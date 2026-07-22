"""Single-flight orchestrator shell shared by scheduled and manual runs."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.tools.validate_mechanism import TrustTuple

from .bootstrap import BootstrapContext, bootstrap_runtime
from .core import AutoRuntimeError, Clock
from .roots import RootEntry, RootRegistry, prepare_state_root
from .schedule import SchedulePolicy
from .state import SingleFlightLock, StateLayout


SHARED_GATE_CODES = {
    "BUNDLE_DIGEST",
    "EXPECTED_REMOTE_HEAD",
    "LOCK_OWNERSHIP",
    "PATH_BOUNDARY",
    "POLICY_DIGEST",
    "PRIVACY",
}


@dataclass(frozen=True)
class LaneOutcome:
    lane: str
    status: str
    input_count: int = 0
    output_count: int = 0
    quarantined_count: int = 0
    reason_code: Optional[str] = None


@dataclass(frozen=True)
class RunOutcome:
    overall_status: str
    final_action: str
    lane_outcomes: Tuple[LaneOutcome, ...]
    forced_full: bool
    reason_codes: Tuple[str, ...]


BootstrapFunction = Callable[[Path, TrustTuple], BootstrapContext]
LaneExecutor = Callable[[BootstrapContext, bool], LaneOutcome]


class SkillOpsOrchestrator:
    """Preflight-first orchestration; it never waits or retries a busy lock."""

    def __init__(
        self,
        *,
        repo_root: Path,
        state_root: Path,
        protected_roots: Sequence[RootEntry],
        trust: TrustTuple,
        clock: Clock,
        bootstrap: BootstrapFunction = bootstrap_runtime,
    ) -> None:
        self.repo_root = repo_root
        self.state_root = state_root
        self.protected_roots = tuple(protected_roots)
        self.trust = trust
        self.clock = clock
        self.bootstrap = bootstrap
        self.schedule = SchedulePolicy()

    def run(
        self,
        *,
        owner_run_uid: str,
        trigger_kind: str,
        last_full_local_date,
        lane_executors: Mapping[str, LaneExecutor],
        shared_gates: Optional[Mapping[str, bool]] = None,
        lock_entropy: Optional[bytes] = None,
    ) -> RunOutcome:
        # P0 ordering: nothing under state_root exists before this returns.
        context = self.bootstrap(self.repo_root, self.trust)
        self.schedule.validate_trusted_policy(
            context.contract.shared.policies[
                "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
            ]
        )
        prepared = prepare_state_root(
            self.state_root,
            repo_root=self.repo_root,
            protected_roots=[entry.path for entry in self.protected_roots],
        )
        layout = StateLayout.create(prepared)
        RootRegistry(
            (
                *self.protected_roots,
                RootEntry("runtime-state", "STATE", prepared),
                RootEntry("runtime-queue", "PUBLIC_QUEUE", layout.queue),
                RootEntry("runtime-outbox", "OUTBOX", layout.outbox),
                RootEntry("runtime-staging", "STAGING", layout.staging),
            )
        )
        lock = SingleFlightLock(
            layout,
            context.contract,
            self.trust.expected_bundle_digest,
            self.clock,
        )
        acquired = lock.acquire(owner_run_uid, entropy=lock_entropy)
        if acquired.status != "ACQUIRED":
            status = (
                "DEFERRED_SINGLE_FLIGHT"
                if acquired.status == "BUSY"
                else "FAILED"
            )
            return RunOutcome(
                status,
                "DEFER" if status == "DEFERRED_SINGLE_FLIGHT" else "STOP",
                (),
                False,
                ("LOCK_BUSY" if status == "DEFERRED_SINGLE_FLIGHT" else acquired.status,),
            )

        state = acquired.state
        assert state is not None
        try:
            cadence = self.schedule.classify(
                trigger_kind,
                self.clock.now(),
                last_full_local_date=last_full_local_date,
            )
            lanes = []
            for lane in ("REGISTRY", "RUN_LOG"):
                executor = lane_executors.get(lane)
                if executor is None:
                    lanes.append(LaneOutcome(lane, "NO_CHANGE"))
                    continue
                try:
                    outcome = executor(context, cadence.forced_full)
                    if outcome.lane != lane:
                        raise AutoRuntimeError("LANE_EXECUTOR_IDENTITY_MISMATCH")
                    if outcome.status not in {
                        "NO_CHANGE",
                        "READY",
                        "SHADOW_VALIDATED",
                        "QUARANTINED",
                        "FAILED",
                    }:
                        raise AutoRuntimeError("LANE_EXECUTOR_STATUS_INVALID")
                    lanes.append(outcome)
                except Exception:
                    lanes.append(
                        LaneOutcome(
                            lane,
                            "QUARANTINED",
                            quarantined_count=1,
                            reason_code="LANE_LOCAL_FAILURE",
                        )
                    )

            if shared_gates is None or set(shared_gates) != SHARED_GATE_CODES:
                failed_shared = ("SHARED_GATE_SET_INCOMPLETE",)
            else:
                failed_shared = tuple(
                    sorted(code for code, passed in shared_gates.items() if not passed)
                )
            if failed_shared:
                return RunOutcome(
                    "FAILED",
                    "STOP",
                    tuple(lanes),
                    cadence.forced_full,
                    failed_shared,
                )
            if self.trust.mode == "CANDIDATE":
                lane_reasons = tuple(
                    sorted(
                        {
                            lane.reason_code
                            for lane in lanes
                            if lane.reason_code is not None
                        }
                    )
                )
                return RunOutcome(
                    "PARTIAL" if lane_reasons else "SUCCESS",
                    "NONE",
                    tuple(lanes),
                    cadence.forced_full,
                    ("CANDIDATE_NON_ACTIVE", *lane_reasons),
                )
            return RunOutcome(
                "FAILED",
                "STOP",
                tuple(lanes),
                cadence.forced_full,
                ("ACTIVE_CUTOVER_NOT_CONFIGURED",),
            )
        finally:
            lock.release(owner_run_uid, str(state["state_digest"]))
