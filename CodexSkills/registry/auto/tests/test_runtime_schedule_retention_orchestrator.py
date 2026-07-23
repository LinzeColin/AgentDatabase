from __future__ import annotations

import contextlib
import datetime as dt
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from CodexSkills.registry.auto.runtime.core import (
    AutoRuntimeError,
    PROTOCOL,
    SCHEMA_PREFIX,
    atomic_write_json,
    canonical_with_digest,
    format_utc,
)
from CodexSkills.registry.auto.runtime.orchestrator import LaneOutcome, SkillOpsOrchestrator
from CodexSkills.registry.auto.runtime.retention import RetentionExecutor, raw_ownership_marker
from CodexSkills.registry.auto.runtime.roots import RootEntry, RootRegistry, prepare_state_root
from CodexSkills.registry.auto.runtime.schedule import SchedulePolicy
from CodexSkills.registry.auto.runtime.state import SingleFlightLock, StateLayout

from runtime_helpers import (
    CANDIDATE_DIGEST,
    FIXED_NOW,
    REPO_ROOT,
    clock,
    context,
    control_synced_context,
    control_trust,
    trust,
    uid,
)


def all_shared_gates(value=True):
    return {
        "BUNDLE_DIGEST": value,
        "EXPECTED_REMOTE_HEAD": value,
        "LOCK_OWNERSHIP": value,
        "PATH_BOUNDARY": value,
        "POLICY_DIGEST": value,
        "PRIVACY": value,
    }


class RuntimeScheduleRetentionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.protected = self.base / "protected"
        self.protected.mkdir()
        self.state = self.base / "state"
        prepared = prepare_state_root(
            self.state,
            repo_root=REPO_ROOT,
            protected_roots=[self.protected],
        )
        self.layout = StateLayout.create(prepared)
        self.roots = RootRegistry(
            (
                RootEntry("protected", "LEGACY_DATA", self.protected),
                RootEntry("state", "STATE", prepared),
            )
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def executor(self, fake=None):
        return RetentionExecutor(
            context().contract,
            CANDIDATE_DIGEST,
            fake or clock(),
            self.roots,
        )

    def raw_segment(self, *, age_seconds: int, mode="TEST_ONLY", number=1):
        now = FIXED_NOW
        sealed = now - dt.timedelta(seconds=age_seconds)
        payload = b"synthetic raw"
        metadata = {
                "schema_version": SCHEMA_PREFIX + "raw-segment:v2",
                "protocol_revision": PROTOCOL,
                "bundle_digest": CANDIDATE_DIGEST,
                "segment_uid": uid("raw", number),
                "source_generation_uid": uid("gen", number),
                "adapter_id": "synthetic-adapter",
                "adapter_version": "1.0.0",
                "persistence_mode": mode,
                "managed_owned": True,
                "protected_or_legacy": False,
                "ownership_marker_digest": "0" * 64,
                "payload_digest": __import__("hashlib").sha256(payload).hexdigest(),
                "record_count": 1,
                "byte_count": len(payload),
                "created_at": format_utc(sealed),
                "sealed_at": format_utc(sealed),
                "expires_at": format_utc(sealed + dt.timedelta(hours=72)),
                "segment_digest": "0" * 64,
            }
        metadata["ownership_marker_digest"] = raw_ownership_marker(metadata)
        metadata = canonical_with_digest(
            metadata,
            "segment_digest",
        )
        path = self.layout.managed_raw / f"segment-{number}.json"
        atomic_write_json(path, metadata)
        path.with_suffix(".payload").write_bytes(payload)
        return path

    def test_raw_persistence_is_disabled_by_default(self) -> None:
        path = self.raw_segment(age_seconds=72 * 3600)
        self.assertEqual(self.executor().select_raw([path]), ())

    def test_raw_ttl_boundary_is_utc_elapsed_time(self) -> None:
        before = self.raw_segment(age_seconds=72 * 3600 - 1, number=1)
        exact = self.raw_segment(age_seconds=72 * 3600, number=2)
        selected = self.executor().select_raw([before, exact], allow_test_only=True)
        self.assertEqual([item.metadata_path for item in selected], [exact])
        self.assertFalse(selected[0].ttl_breach)

    def test_uncertified_persistent_raw_fails_closed(self) -> None:
        path = self.raw_segment(
            age_seconds=72 * 3600,
            mode="ENABLED_AFTER_CERTIFICATION",
        )
        with self.assertRaisesRegex(AutoRuntimeError, "RAW_PERSISTENCE_NOT_CERTIFIED"):
            self.executor().select_raw([path], allow_test_only=True)

    def test_raw_ownership_marker_and_payload_are_content_bound(self) -> None:
        marker_path = self.raw_segment(age_seconds=72 * 3600, number=1)
        marker = __import__("json").loads(marker_path.read_text(encoding="utf-8"))
        marker["ownership_marker_digest"] = "f" * 64
        marker = canonical_with_digest(marker, "segment_digest")
        atomic_write_json(marker_path, marker)
        with self.assertRaisesRegex(AutoRuntimeError, "RAW_OWNERSHIP_MARKER_INVALID"):
            self.executor().select_raw([marker_path], allow_test_only=True)

        payload_path = self.raw_segment(age_seconds=72 * 3600, number=2)
        payload_path.with_suffix(".payload").write_bytes(b"tampered")
        with self.assertRaisesRegex(AutoRuntimeError, "RAW_PAYLOAD_EVIDENCE_INVALID"):
            self.executor().select_raw([payload_path], allow_test_only=True)

    def test_legacy_or_malformed_file_is_never_selected(self) -> None:
        legacy = self.layout.managed_raw / "legacy.json"
        legacy.write_text('{"created_at":"old"}', encoding="utf-8")
        self.assertEqual(
            self.executor().select_raw([legacy], allow_test_only=True),
            (),
        )

    def test_owned_expired_segment_deletes_only_after_projection_or_gap(self) -> None:
        path = self.raw_segment(age_seconds=72 * 3600)
        candidate = self.executor().select_raw([path], allow_test_only=True)[0]
        execution = self.executor().execute_raw(
            candidate,
            reproject=lambda _candidate: True,
            record_gap=lambda _candidate, _code: False,
        )
        self.assertEqual(execution.action, "DELETE_OWNED_SEGMENT")
        self.assertFalse(path.exists())
        self.assertTrue(self.protected.exists())

    def test_failed_projection_without_durable_gap_never_deletes(self) -> None:
        path = self.raw_segment(age_seconds=72 * 3600)
        candidate = self.executor().select_raw([path], allow_test_only=True)[0]
        with self.assertRaisesRegex(AutoRuntimeError, "RAW_GAP_RECEIPT_REQUIRED_BEFORE_DELETE"):
            self.executor().execute_raw(
                candidate,
                reproject=lambda _candidate: False,
                record_gap=lambda _candidate, _code: False,
            )
        self.assertTrue(path.exists())
        self.assertTrue(path.with_suffix(".payload").exists())

    def test_offline_ttl_breach_requires_gap_before_cleanup(self) -> None:
        path = self.raw_segment(age_seconds=72 * 3600 + 1)
        candidate = self.executor().select_raw(
            [path],
            allow_test_only=True,
            last_runtime_available_at=FIXED_NOW - dt.timedelta(hours=80),
        )[0]
        self.assertTrue(candidate.ttl_breach)
        codes = []
        execution = self.executor().execute_raw(
            candidate,
            reproject=lambda _candidate: True,
            record_gap=lambda _candidate, code: codes.append(code) is None,
        )
        self.assertEqual(codes, ["OFFLINE_TTL_BREACH"])
        self.assertEqual(execution.action, "OFFLINE_TTL_BREACH_CLEANUP")

    def test_git_active_tree_boundary_is_strictly_after_365_days(self) -> None:
        boundary = FIXED_NOW
        self.assertFalse(RetentionExecutor.git_current_tree_eligible(boundary, boundary))
        self.assertTrue(
            RetentionExecutor.git_current_tree_eligible(
                boundary + dt.timedelta(microseconds=1), boundary
            )
        )

    def test_sydney_schedule_survives_both_dst_transitions(self) -> None:
        policy = SchedulePolicy()
        autumn_before = policy.scheduled_instant(dt.date(2026, 4, 4))
        autumn_after = policy.scheduled_instant(dt.date(2026, 4, 5))
        spring_before = policy.scheduled_instant(dt.date(2026, 10, 3))
        spring_after = policy.scheduled_instant(dt.date(2026, 10, 4))
        self.assertEqual(autumn_after - autumn_before, dt.timedelta(hours=25))
        self.assertEqual(spring_after - spring_before, dt.timedelta(hours=23))

    def test_manual_has_no_late_window_and_uses_overdue_sunday_full(self) -> None:
        policy = SchedulePolicy()
        result = policy.classify(
            "MANUAL",
            FIXED_NOW,
            last_full_local_date=dt.date(2026, 7, 12),
        )
        self.assertFalse(result.late_rejected)
        self.assertTrue(result.forced_full)


class RuntimeOrchestratorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.source = self.base / "source"
        self.source.mkdir()
        self.state = self.base / "state"

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def orchestrator(self):
        return SkillOpsOrchestrator(
            repo_root=REPO_ROOT,
            state_root=self.state,
            protected_roots=(RootEntry("source", "SKILL_SOURCE", self.source),),
            trust=trust(),
            control_trust=control_trust(),
            clock=clock(),
            bootstrap=lambda _repo, _trust, _control: (
                control_synced_context()
            ),
        )

    def test_current_control_blocks_before_state_write(self) -> None:
        runner = SkillOpsOrchestrator(
            repo_root=REPO_ROOT,
            state_root=self.state,
            protected_roots=(
                RootEntry("source", "SKILL_SOURCE", self.source),
            ),
            trust=trust(),
            control_trust=control_trust(),
            clock=clock(),
        )
        with contextlib.ExitStack() as stack:
            state_preparer = stack.enter_context(
                mock.patch(
                    "CodexSkills.registry.auto.runtime.orchestrator."
                    "prepare_state_root"
                )
            )
            layout = stack.enter_context(
                mock.patch(
                    "CodexSkills.registry.auto.runtime.orchestrator."
                    "StateLayout"
                )
            )
            registry = stack.enter_context(
                mock.patch(
                    "CodexSkills.registry.auto.runtime.orchestrator."
                    "RootRegistry"
                )
            )
            lock = stack.enter_context(
                mock.patch(
                    "CodexSkills.registry.auto.runtime.orchestrator."
                    "SingleFlightLock"
                )
            )
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "RUNTIME_CONTROL_SYNC_REQUIRED_BEFORE_STATE_WRITE",
            ):
                runner.run(
                    owner_run_uid=uid("run", 9),
                    trigger_kind="MANUAL",
                    last_full_local_date=None,
                    lane_executors={},
                )
            state_preparer.assert_not_called()
            layout.assert_not_called()
            registry.assert_not_called()
            lock.assert_not_called()
        self.assertFalse(self.state.exists())

    def test_candidate_run_uses_both_lanes_but_cannot_publish(self) -> None:
        def registry(_context, forced):
            return LaneOutcome("REGISTRY", "SHADOW_VALIDATED", input_count=1, output_count=1)

        def broken(_context, _forced):
            raise RuntimeError("lane local")

        outcome = self.orchestrator().run(
            owner_run_uid=uid("run", 10),
            trigger_kind="MANUAL",
            last_full_local_date=dt.date(2026, 7, 19),
            lane_executors={"REGISTRY": registry, "RUN_LOG": broken},
            shared_gates=all_shared_gates(),
            lock_entropy=(10).to_bytes(10, "big"),
        )
        self.assertEqual(outcome.final_action, "NONE")
        self.assertEqual(
            outcome.reason_codes,
            ("CANDIDATE_NON_ACTIVE", "LANE_LOCAL_FAILURE"),
        )
        self.assertEqual(outcome.overall_status, "PARTIAL")
        self.assertEqual(outcome.lane_outcomes[0].status, "SHADOW_VALIDATED")
        self.assertEqual(outcome.lane_outcomes[1].status, "QUARANTINED")

    def test_shared_gate_failure_blocks_candidate_settlement(self) -> None:
        outcome = self.orchestrator().run(
            owner_run_uid=uid("run", 11),
            trigger_kind="SCHEDULED",
            last_full_local_date=dt.date(2026, 7, 19),
            lane_executors={},
            shared_gates={**all_shared_gates(), "PRIVACY": False},
            lock_entropy=(11).to_bytes(10, "big"),
        )
        self.assertEqual(outcome.final_action, "STOP")
        self.assertEqual(outcome.reason_codes, ("PRIVACY",))

    def test_busy_lock_defers_immediately_without_retry(self) -> None:
        prepared = prepare_state_root(
            self.state,
            repo_root=REPO_ROOT,
            protected_roots=[self.source],
        )
        layout = StateLayout.create(prepared)
        held = SingleFlightLock(layout, context().contract, CANDIDATE_DIGEST, clock())
        held.acquire(uid("run", 12), entropy=(12).to_bytes(10, "big"))
        outcome = self.orchestrator().run(
            owner_run_uid=uid("run", 13),
            trigger_kind="MANUAL",
            last_full_local_date=dt.date(2026, 7, 19),
            lane_executors={},
            shared_gates=all_shared_gates(),
        )
        self.assertEqual(outcome.overall_status, "DEFERRED_SINGLE_FLIGHT")
        self.assertEqual(outcome.final_action, "DEFER")
        self.assertEqual(outcome.reason_codes, ("LOCK_BUSY",))

    def test_manual_and_scheduled_share_same_business_path(self) -> None:
        def execute(trigger):
            state = self.base / f"state-{trigger.lower()}"
            runner = SkillOpsOrchestrator(
                repo_root=REPO_ROOT,
                state_root=state,
                protected_roots=(RootEntry("source", "SKILL_SOURCE", self.source),),
                trust=trust(),
                control_trust=control_trust(),
                clock=clock(),
                bootstrap=lambda _repo, _trust, _control: (
                    control_synced_context()
                ),
            )
            return runner.run(
                owner_run_uid=uid("run", 20 if trigger == "MANUAL" else 21),
                trigger_kind=trigger,
                last_full_local_date=dt.date(2026, 7, 19),
                lane_executors={},
                shared_gates=all_shared_gates(),
                lock_entropy=(20 if trigger == "MANUAL" else 21).to_bytes(10, "big"),
            )

        manual = execute("MANUAL")
        scheduled = execute("SCHEDULED")
        self.assertEqual(manual.final_action, scheduled.final_action)
        self.assertEqual(manual.lane_outcomes, scheduled.lane_outcomes)
        self.assertEqual(manual.forced_full, scheduled.forced_full)


if __name__ == "__main__":
    unittest.main()
