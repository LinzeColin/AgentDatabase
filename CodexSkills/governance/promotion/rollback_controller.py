"""Pure append-only rollback/revocation controller for Task Pack M-057.

The controller replays one ordered lifecycle ledger containing promotion,
rejection, rollback, and revocation decisions.  Promotion/rejection steps are
delegated to the M-056 controller against the current derived champion map;
rollback/revocation steps require a bundle-external, explicitly digest-pinned
restore-drill contract.

No function in this module writes Registry state, ledgers, Git, VERSION,
notifications, or public artifacts.  It returns canonical bytes and immutable
derived views only.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.promotion.controller import (
    EVAL_RUN_SCHEMA_ID,
    PROMOTION_DECISION_SCHEMA_ID,
    PROMOTION_EVIDENCE_SCHEMA_ID,
    SCORECARD_SCHEMA_ID,
    PROTOCOL_REVISION,
    PromotionControllerError,
    PromotionRegistryView,
    VersionContext,
    replay_promotion_ledger,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractBundle,
    ContractError,
    build_registry,
    validate_instance,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
ROLLBACK_DRILL_SCHEMA_ID = SCHEMA_PREFIX + "rollback-drill-evidence:v1"
ROLLBACK_DRILL_SELF_POINTER = "/evidence_bundle_digest"
LIFECYCLE_LEDGER_DOMAIN = "SKILLOPS_LIFECYCLE_LEDGER_V1"
UTC_Z_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
REQUIRED_VERIFICATION_KINDS = (
    "REFERENCE_CLOSURE",
    "RESTORE_PLAN",
    "RESTORE_TEST",
    "STATE_SNAPSHOT",
    "TRIGGER",
)


class RollbackControllerError(ValueError):
    """A lifecycle-ledger or restore-drill invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class LifecycleLedgerView:
    """Deterministic derived state for one immutable lifecycle history."""

    actions: Tuple[str, ...]
    decision_uids: Tuple[str, ...]
    decision_digests: Tuple[str, ...]
    evidence_digests: Tuple[str, ...]
    champion_by_scope: Tuple[Tuple[str, str], ...]
    champion_history_by_scope: Tuple[Tuple[str, Tuple[str, ...]], ...]
    lifecycle_overrides: Tuple[Tuple[str, str], ...]
    revoked_version_uids: Tuple[str, ...]
    terminal_candidate_version_uids: Tuple[str, ...]
    last_decided_at: Optional[str]
    ledger_digest: str
    promote_count: int
    reject_count: int
    rollback_count: int
    revoke_count: int


@dataclasses.dataclass(frozen=True)
class RollbackAppendResult:
    """Canonical new event/evidence plus the post-append lifecycle view."""

    canonical_decision_bytes: bytes
    canonical_drill_evidence_bytes: bytes
    decision_digest: str
    evidence_bundle_digest: str
    predecessor_ledger_digest: str
    ledger_view: LifecycleLedgerView


def _fail(code: str) -> None:
    raise RollbackControllerError(code)


def _timestamp(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str):
        _fail(code)
    try:
        return dt.datetime.strptime(value, UTC_Z_FORMAT)
    except ValueError as exc:
        raise RollbackControllerError(code) from exc


def _sorted_unique(values: Any, code: str) -> None:
    if (
        not isinstance(values, list)
        or any(not isinstance(value, str) for value in values)
        or values != sorted(values, key=lambda value: value.encode("utf-8"))
        or len(values) != len(set(values))
    ):
        _fail(code)


def _version_map(
    registry_view: PromotionRegistryView,
) -> Dict[str, VersionContext]:
    return {
        version.skill_version_uid: version
        for version in registry_view.versions
    }


def _validate_candidate_artifact(
    bundle: ContractBundle,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
) -> None:
    try:
        validate_instance(
            bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            public=True,
        )
    except ContractError as exc:
        raise RollbackControllerError(code + ":" + str(exc)) from exc


def _normalize_map(
    values: Mapping[str, Mapping[str, Any]],
    digest_field: str,
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(values, dict):
        _fail(code + "_MAP_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for key, value in values.items():
        if (
            not isinstance(key, str)
            or SHA256_RE.fullmatch(key) is None
            or not isinstance(value, dict)
            or value.get(digest_field) != key
        ):
            _fail(code + "_MAP_ENTRY_INVALID")
        result[key] = value
    return result


def build_rollback_contract(
    candidate_bundle: ContractBundle,
    rollback_drill_schema: Mapping[str, Any],
    expected_schema_digest: str,
) -> ContractBundle:
    """Extend one trusted candidate bundle with an external drill schema."""

    if (
        not isinstance(rollback_drill_schema, dict)
        or rollback_drill_schema.get("$id") != ROLLBACK_DRILL_SCHEMA_ID
        or not isinstance(expected_schema_digest, str)
        or SHA256_RE.fullmatch(expected_schema_digest) is None
        or canonical_digest(rollback_drill_schema)
        != expected_schema_digest
    ):
        _fail("ROLLBACK_DRILL_SCHEMA_TRUST_MISMATCH")
    schemas = dict(candidate_bundle.schemas)
    if ROLLBACK_DRILL_SCHEMA_ID in schemas:
        _fail("ROLLBACK_DRILL_SCHEMA_REBIND_FORBIDDEN")
    schemas[ROLLBACK_DRILL_SCHEMA_ID] = rollback_drill_schema
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise RollbackControllerError(
            "ROLLBACK_DRILL_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    pointers = dict(candidate_bundle.self_digest_pointers)
    pointers[ROLLBACK_DRILL_SCHEMA_ID] = ROLLBACK_DRILL_SELF_POINTER
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=candidate_bundle.policies,
        protocol_revision=candidate_bundle.protocol_revision,
    )


def lifecycle_ledger_digest(
    registry_snapshot_digest: str,
    actions: Sequence[str],
    decision_digests: Sequence[str],
    evidence_digests: Sequence[str],
) -> str:
    """Bind an ordered mixed-action history to one Registry snapshot."""

    if (
        not isinstance(registry_snapshot_digest, str)
        or SHA256_RE.fullmatch(registry_snapshot_digest) is None
        or len(actions) != len(decision_digests)
        or len(actions) != len(evidence_digests)
        or any(
            action
            not in {"PROMOTE", "REJECT", "ROLLBACK", "REVOKE"}
            for action in actions
        )
        or any(
            not isinstance(value, str)
            or SHA256_RE.fullmatch(value) is None
            for value in tuple(decision_digests) + tuple(evidence_digests)
        )
    ):
        _fail("LIFECYCLE_LEDGER_DIGEST_INPUT_INVALID")
    return canonical_digest(
        {
            "domain": LIFECYCLE_LEDGER_DOMAIN,
            "events": [
                {
                    "action": action,
                    "decision_digest": decision_digest,
                    "evidence_bundle_digest": evidence_digest,
                }
                for action, decision_digest, evidence_digest in zip(
                    actions,
                    decision_digests,
                    evidence_digests,
                )
            ],
            "protocol_revision": PROTOCOL_REVISION,
            "registry_snapshot_digest": registry_snapshot_digest,
        }
    )


def _ref_subset(
    refs: Any,
    values: Mapping[str, Mapping[str, Any]],
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(refs, list):
        _fail(code + "_REF_LIST_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for ref in refs:
        if (
            not isinstance(ref, dict)
            or not isinstance(ref.get("artifact_digest"), str)
            or ref["artifact_digest"] not in values
        ):
            _fail(code + "_REFERENCE_CLOSURE_MISMATCH")
        result[ref["artifact_digest"]] = values[ref["artifact_digest"]]
    if len(result) != len(refs):
        _fail(code + "_REFERENCE_REUSED")
    return result


def _validate_drill_semantics(
    drill: Mapping[str, Any],
    decision: Mapping[str, Any],
    *,
    registry_view: PromotionRegistryView,
    versions: Mapping[str, VersionContext],
    champions: Mapping[str, str],
    champion_history: Mapping[str, Sequence[str]],
    champion_provenance: Mapping[Tuple[str, str], Optional[str]],
    revoked_versions: Sequence[str],
    predecessor_ledger_digest: str,
    predecessor_decision_count: int,
) -> Tuple[str, str]:
    current_uid = decision["candidate_skill_version_uid"]
    target_uid = decision["rollback_target_version_uid"]
    current = versions.get(current_uid)
    target = versions.get(target_uid)
    if current is None or target is None:
        _fail("ROLLBACK_VERSION_UNKNOWN")
    scope_uid = current.skill_identity_uid
    if (
        target.skill_identity_uid != scope_uid
        or current_uid == target_uid
        or champions.get(scope_uid) != current_uid
    ):
        _fail("ROLLBACK_SCOPE_OR_CURRENT_CHAMPION_MISMATCH")
    if (
        target_uid not in set(champion_history.get(scope_uid, ()))
        or target_uid in set(revoked_versions)
    ):
        _fail("ROLLBACK_TARGET_NOT_RESTORABLE_PRIOR_CHAMPION")

    current_ref = drill["current_champion_ref"]
    target_ref = drill["rollback_target_ref"]
    if (
        drill["action"] != decision["action"]
        or drill["skill_identity_uid"] != scope_uid
        or drill["registry_snapshot_digest"]
        != registry_view.registry_snapshot_digest
        or current_ref["skill_version_uid"] != current_uid
        or current_ref["version_record_digest"]
        != current.version_record_digest
        or target_ref["skill_version_uid"] != target_uid
        or target_ref["version_record_digest"]
        != target.version_record_digest
        or current_ref["decision_digest"]
        != champion_provenance.get((scope_uid, current_uid))
        or target_ref["decision_digest"]
        != champion_provenance.get((scope_uid, target_uid))
    ):
        _fail("ROLLBACK_DRILL_REFERENCE_CLOSURE_MISMATCH")
    predecessor = drill["predecessor_ledger"]
    if (
        predecessor["artifact_digest"] != predecessor_ledger_digest
        or predecessor["decision_count"] != predecessor_decision_count
    ):
        _fail("ROLLBACK_DRILL_PREDECESSOR_LEDGER_MISMATCH")

    kinds = [
        ref["kind"]
        for ref in drill["verification_evidence_refs"]
        if isinstance(ref, dict) and isinstance(ref.get("kind"), str)
    ]
    if (
        kinds != list(REQUIRED_VERIFICATION_KINDS)
        or len(kinds) != len(drill["verification_evidence_refs"])
        or len(
            {
                ref["artifact_digest"]
                for ref in drill["verification_evidence_refs"]
            }
        )
        != len(REQUIRED_VERIFICATION_KINDS)
    ):
        _fail("ROLLBACK_DRILL_VERIFICATION_CLOSURE_INCOMPLETE")
    _sorted_unique(drill["trigger_codes"], "ROLLBACK_TRIGGER_ORDER_INVALID")
    _sorted_unique(
        drill["known_risk_codes"],
        "ROLLBACK_RISK_ORDER_INVALID",
    )
    if (
        decision["evidence_bundle_digest"]
        != drill["evidence_bundle_digest"]
        or decision["candidate_model_snapshot_digest"]
        != current_ref["model_snapshot_digest"]
        or decision["baseline_model_snapshot_digest"]
        != target_ref["model_snapshot_digest"]
        or decision["known_risk_codes"] != drill["known_risk_codes"]
        or decision["reason_codes"] != drill["trigger_codes"]
        or decision["notification_receipt_digest"]
        != drill["notification_receipt_digest"]
        or decision["notification_mode"] != drill["notification_mode"]
        or decision["srv_revision"] != current.srv_revision
    ):
        _fail("ROLLBACK_DECISION_DRILL_CLAIM_MISMATCH")
    _sorted_unique(
        decision["known_risk_codes"],
        "ROLLBACK_DECISION_RISK_ORDER_INVALID",
    )
    _sorted_unique(
        decision["reason_codes"],
        "ROLLBACK_DECISION_REASON_ORDER_INVALID",
    )
    if (
        decision["impact"] != "MAJOR"
        or not decision["major_change"]
        or not decision["hard_gates_passed"]
        or decision["from_status"] != "CHAMPION"
        or decision["previous_champion_version_uid"] != current_uid
        or decision["resulting_champion_version_uid"] != target_uid
    ):
        _fail("ROLLBACK_DECISION_TRANSITION_INVALID")
    if decision["action"] == "ROLLBACK":
        if (
            decision["stage"] != "ROLLED_BACK"
            or decision["to_status"] != "DEPRECATED"
        ):
            _fail("ROLLBACK_DECISION_TRANSITION_INVALID")
    elif decision["action"] == "REVOKE":
        if (
            decision["stage"] != "REVOKED"
            or decision["to_status"] != "REVOKED"
        ):
            _fail("REVOKE_DECISION_TRANSITION_INVALID")
    else:
        _fail("ROLLBACK_ACTION_UNSUPPORTED")

    if drill["execution_mode"] == "PLANNED_PRE_WRITE":
        if (
            decision["emergency_containment"]
            or drill["state_write_observed"]
            or drill["containment_evidence"] is not None
            or drill["notification_mode"] != "PRE_WRITE_SENT"
        ):
            _fail("ROLLBACK_PLANNED_NOTIFICATION_ORDER_INVALID")
    elif drill["execution_mode"] == "EMERGENCY_POST_CONTAINMENT":
        if (
            not decision["emergency_containment"]
            or not drill["state_write_observed"]
            or not isinstance(drill["containment_evidence"], dict)
            or drill["notification_mode"] != "POST_CONTAINMENT_SENT"
        ):
            _fail("ROLLBACK_EMERGENCY_NOTIFICATION_ORDER_INVALID")
    else:
        _fail("ROLLBACK_EXECUTION_MODE_UNSUPPORTED")
    if _timestamp(
        drill["completed_at"],
        "ROLLBACK_DRILL_TIMESTAMP_INVALID",
    ) > _timestamp(
        decision["decided_at"],
        "ROLLBACK_DECISION_TIMESTAMP_INVALID",
    ):
        _fail("ROLLBACK_DRILL_AFTER_DECISION_FORBIDDEN")
    return scope_uid, target_uid


def replay_lifecycle_ledger(
    candidate_bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    *,
    rollback_drill_schema: Mapping[str, Any],
    expected_rollback_drill_schema_digest: str,
    promotion_evidence_by_digest: Mapping[str, Mapping[str, Any]],
    rollback_drill_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    decisions: Sequence[Mapping[str, Any]],
    expected_bundle_digest: str,
) -> LifecycleLedgerView:
    """Replay a complete mixed lifecycle ledger without mutating inputs."""

    if candidate_bundle.protocol_revision != PROTOCOL_REVISION:
        _fail("ROLLBACK_BUNDLE_PROTOCOL_MISMATCH")
    rollback_bundle = build_rollback_contract(
        candidate_bundle,
        rollback_drill_schema,
        expected_rollback_drill_schema_digest,
    )
    promotions = _normalize_map(
        promotion_evidence_by_digest,
        "evidence_bundle_digest",
        "LIFECYCLE_PROMOTION_EVIDENCE",
    )
    drills = _normalize_map(
        rollback_drill_by_digest,
        "evidence_bundle_digest",
        "LIFECYCLE_ROLLBACK_DRILL",
    )
    scorecards = _normalize_map(
        scorecards_by_digest,
        "scorecard_digest",
        "LIFECYCLE_SCORECARD",
    )
    eval_runs = _normalize_map(
        eval_runs_by_digest,
        "eval_run_digest",
        "LIFECYCLE_EVAL_RUN",
    )
    for value in promotions.values():
        _validate_candidate_artifact(
            candidate_bundle,
            value,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            expected_bundle_digest,
            "LIFECYCLE_PROMOTION_EVIDENCE_INVALID",
        )
    for value in drills.values():
        try:
            validate_instance(
                rollback_bundle,
                value,
                ROLLBACK_DRILL_SCHEMA_ID,
                expected_bundle_digest=expected_bundle_digest,
                public=True,
            )
        except ContractError as exc:
            raise RollbackControllerError(
                "LIFECYCLE_ROLLBACK_DRILL_INVALID:" + str(exc)
            ) from exc

    versions = _version_map(registry_view)
    champions: Dict[str, str] = dict(registry_view.base_champions)
    history: Dict[str, list[str]] = {
        scope_uid: [version_uid]
        for scope_uid, version_uid in registry_view.base_champions
    }
    provenance: Dict[Tuple[str, str], Optional[str]] = {
        (scope_uid, version_uid): None
        for scope_uid, version_uid in registry_view.base_champions
    }
    overrides: Dict[str, str] = {}
    revoked_versions = set()
    terminal_candidates = set()
    actions = []
    decision_uids = []
    decision_digests = []
    evidence_digests = []
    used_promotions = set()
    used_drills = set()
    used_scorecards = set()
    used_eval_runs = set()
    previous_time: Optional[dt.datetime] = None
    last_decided_at: Optional[str] = None
    counts = {
        "PROMOTE": 0,
        "REJECT": 0,
        "ROLLBACK": 0,
        "REVOKE": 0,
    }

    for raw_decision in decisions:
        if not isinstance(raw_decision, dict):
            _fail("LIFECYCLE_DECISION_ROOT_INVALID")
        decision = raw_decision
        _validate_candidate_artifact(
            candidate_bundle,
            decision,
            PROMOTION_DECISION_SCHEMA_ID,
            expected_bundle_digest,
            "LIFECYCLE_DECISION_CONTRACT_INVALID",
        )
        decision_uid = decision["promotion_decision_uid"]
        decision_digest = decision["decision_digest"]
        evidence_digest = decision["evidence_bundle_digest"]
        action = decision["action"]
        if decision_uid in decision_uids:
            _fail("LIFECYCLE_DECISION_UID_DUPLICATE")
        if decision_digest in decision_digests:
            _fail("LIFECYCLE_DECISION_DIGEST_DUPLICATE")
        decided_at = _timestamp(
            decision["decided_at"],
            "LIFECYCLE_DECISION_TIMESTAMP_INVALID",
        )
        if previous_time is not None and decided_at <= previous_time:
            _fail("LIFECYCLE_LEDGER_TIME_ORDER_INVALID")
        predecessor_digest = lifecycle_ledger_digest(
            registry_view.registry_snapshot_digest,
            actions,
            decision_digests,
            evidence_digests,
        )

        if action in {"PROMOTE", "REJECT"}:
            evidence = promotions.get(evidence_digest)
            if evidence is None or evidence_digest in used_promotions:
                _fail("LIFECYCLE_PROMOTION_EVIDENCE_UNKNOWN_OR_REUSED")
            candidate_uid = decision["candidate_skill_version_uid"]
            if (
                candidate_uid in terminal_candidates
                or candidate_uid in revoked_versions
                or overrides.get(candidate_uid)
                in {"DEPRECATED", "QUARANTINED", "REVOKED"}
            ):
                _fail("LIFECYCLE_PROMOTION_CANDIDATE_TERMINAL")
            scorecard_subset = _ref_subset(
                evidence["scorecard_refs"],
                scorecards,
                "LIFECYCLE_SCORECARD",
            )
            eval_subset = _ref_subset(
                evidence["eval_run_refs"],
                eval_runs,
                "LIFECYCLE_EVAL_RUN",
            )
            current_registry = dataclasses.replace(
                registry_view,
                base_champions=tuple(
                    sorted(
                        champions.items(),
                        key=lambda item: item[0].encode("ascii"),
                    )
                ),
            )
            try:
                step = replay_promotion_ledger(
                    candidate_bundle,
                    current_registry,
                    evidence_by_digest={evidence_digest: evidence},
                    scorecards_by_digest=scorecard_subset,
                    eval_runs_by_digest=eval_subset,
                    decisions=[decision],
                    expected_bundle_digest=expected_bundle_digest,
                )
            except PromotionControllerError as exc:
                raise RollbackControllerError(
                    "LIFECYCLE_PROMOTION_STEP_INVALID:" + exc.code
                ) from exc
            candidate = versions[candidate_uid]
            scope_uid = candidate.skill_identity_uid
            previous_champion = champions.get(scope_uid)
            champions = dict(step.champion_by_scope)
            terminal_candidates.add(candidate_uid)
            used_promotions.add(evidence_digest)
            used_scorecards.update(scorecard_subset)
            used_eval_runs.update(eval_subset)
            if action == "PROMOTE":
                if previous_champion is not None:
                    overrides[previous_champion] = "DEPRECATED"
                overrides[candidate_uid] = "CHAMPION"
                history.setdefault(scope_uid, []).append(candidate_uid)
                provenance[(scope_uid, candidate_uid)] = decision_digest
            else:
                overrides[candidate_uid] = "QUARANTINED"
        else:
            drill = drills.get(evidence_digest)
            if drill is None or evidence_digest in used_drills:
                _fail("LIFECYCLE_ROLLBACK_DRILL_UNKNOWN_OR_REUSED")
            scope_uid, target_uid = _validate_drill_semantics(
                drill,
                decision,
                registry_view=registry_view,
                versions=versions,
                champions=champions,
                champion_history=history,
                champion_provenance=provenance,
                revoked_versions=tuple(revoked_versions),
                predecessor_ledger_digest=predecessor_digest,
                predecessor_decision_count=len(decision_digests),
            )
            current_uid = decision["candidate_skill_version_uid"]
            overrides[current_uid] = decision["to_status"]
            if action == "REVOKE":
                revoked_versions.add(current_uid)
            champions[scope_uid] = target_uid
            overrides[target_uid] = "CHAMPION"
            history.setdefault(scope_uid, []).append(target_uid)
            provenance[(scope_uid, target_uid)] = decision_digest
            terminal_candidates.add(current_uid)
            used_drills.add(evidence_digest)

        previous_time = decided_at
        last_decided_at = decision["decided_at"]
        actions.append(action)
        decision_uids.append(decision_uid)
        decision_digests.append(decision_digest)
        evidence_digests.append(evidence_digest)
        counts[action] += 1

    if set(promotions) != used_promotions:
        _fail("LIFECYCLE_UNUSED_PROMOTION_EVIDENCE_FORBIDDEN")
    if set(drills) != used_drills:
        _fail("LIFECYCLE_UNUSED_ROLLBACK_DRILL_FORBIDDEN")
    if set(scorecards) != used_scorecards:
        _fail("LIFECYCLE_UNUSED_SCORECARD_FORBIDDEN")
    if set(eval_runs) != used_eval_runs:
        _fail("LIFECYCLE_UNUSED_EVAL_RUN_FORBIDDEN")
    if len(champions.values()) != len(set(champions.values())):
        _fail("LIFECYCLE_MULTIPLE_CHAMPIONS_PER_SCOPE")

    return LifecycleLedgerView(
        actions=tuple(actions),
        decision_uids=tuple(decision_uids),
        decision_digests=tuple(decision_digests),
        evidence_digests=tuple(evidence_digests),
        champion_by_scope=tuple(
            sorted(
                champions.items(),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        champion_history_by_scope=tuple(
            (
                scope_uid,
                tuple(version_uids),
            )
            for scope_uid, version_uids in sorted(
                history.items(),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        lifecycle_overrides=tuple(
            sorted(
                overrides.items(),
                key=lambda item: item[0].encode("ascii"),
            )
        ),
        revoked_version_uids=tuple(
            sorted(revoked_versions, key=lambda value: value.encode("ascii"))
        ),
        terminal_candidate_version_uids=tuple(
            sorted(
                terminal_candidates,
                key=lambda value: value.encode("ascii"),
            )
        ),
        last_decided_at=last_decided_at,
        ledger_digest=lifecycle_ledger_digest(
            registry_view.registry_snapshot_digest,
            actions,
            decision_digests,
            evidence_digests,
        ),
        promote_count=counts["PROMOTE"],
        reject_count=counts["REJECT"],
        rollback_count=counts["ROLLBACK"],
        revoke_count=counts["REVOKE"],
    )


def append_rollback_decision(
    candidate_bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    *,
    rollback_drill_schema: Mapping[str, Any],
    expected_rollback_drill_schema_digest: str,
    promotion_evidence_by_digest: Mapping[str, Mapping[str, Any]],
    rollback_drill_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    existing_decisions: Sequence[Mapping[str, Any]],
    decision: Mapping[str, Any],
    expected_predecessor_ledger_digest: str,
    expected_bundle_digest: str,
) -> RollbackAppendResult:
    """Validate one new rollback/revoke event and return append material."""

    if not isinstance(decision, dict) or decision.get("action") not in {
        "ROLLBACK",
        "REVOKE",
    }:
        _fail("ROLLBACK_APPEND_ACTION_REQUIRED")
    combined = tuple(existing_decisions) + (decision,)
    view = replay_lifecycle_ledger(
        candidate_bundle,
        registry_view,
        rollback_drill_schema=rollback_drill_schema,
        expected_rollback_drill_schema_digest=(
            expected_rollback_drill_schema_digest
        ),
        promotion_evidence_by_digest=promotion_evidence_by_digest,
        rollback_drill_by_digest=rollback_drill_by_digest,
        scorecards_by_digest=scorecards_by_digest,
        eval_runs_by_digest=eval_runs_by_digest,
        decisions=combined,
        expected_bundle_digest=expected_bundle_digest,
    )
    predecessor_digest = lifecycle_ledger_digest(
        registry_view.registry_snapshot_digest,
        view.actions[:-1],
        view.decision_digests[:-1],
        view.evidence_digests[:-1],
    )
    if (
        not isinstance(expected_predecessor_ledger_digest, str)
        or predecessor_digest != expected_predecessor_ledger_digest
    ):
        _fail("ROLLBACK_PREDECESSOR_LEDGER_DIGEST_MISMATCH")
    drill = rollback_drill_by_digest.get(
        decision["evidence_bundle_digest"]
    )
    if not isinstance(drill, dict):
        _fail("ROLLBACK_APPEND_DRILL_MISSING")
    return RollbackAppendResult(
        canonical_decision_bytes=canonicalize_object(decision),
        canonical_drill_evidence_bytes=canonicalize_object(drill),
        decision_digest=decision["decision_digest"],
        evidence_bundle_digest=drill["evidence_bundle_digest"],
        predecessor_ledger_digest=predecessor_digest,
        ledger_view=view,
    )
