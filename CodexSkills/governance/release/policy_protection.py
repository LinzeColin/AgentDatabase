"""Pure evaluator/release-policy protection gate for Task Pack M-059.

The guard recomputes protected-surface differences, classifies every detected
change through the exact version-policy v3 MAJOR vocabulary, and validates a
complete optimizer access-denial audit.  A protected change is never allowed
to ride the Skill promotion path: optimizer-originated changes are blocked and
independently originated changes are isolated to a separate MAJOR release.

This module never writes Registry, state, Git, VERSION, notifications, or
public artifacts.  An unchanged protected snapshot may delegate only through
the immutable M-058 monitor, which in turn delegates to M-056.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from typing import Any, Dict, Mapping, Sequence, Tuple

from CodexSkills.governance.monitoring.freshness_drift import (
    MonitoredPromotionAppendResult,
    FreshnessDriftError,
    append_monitored_promotion_decision,
)
from CodexSkills.governance.promotion.controller import (
    PROMOTION_DECISION_SCHEMA_ID,
    PROMOTION_EVIDENCE_SCHEMA_ID,
    PROTOCOL_REVISION,
    SCORECARD_SCHEMA_ID,
)
from CodexSkills.governance.release.version_policy_v3.contract import (
    VERSION_POLICY_V3_ID,
    VersionPolicyV3Error,
    classify_v3_impact,
    validate_version_policy_v3,
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
EVAL_PROFILE_SCHEMA_ID = SCHEMA_PREFIX + "eval-profile:v1"
OBSERVATION_SCHEMA_ID = (
    SCHEMA_PREFIX + "evaluator-release-change-observation:v1"
)
REPORT_SCHEMA_ID = (
    SCHEMA_PREFIX + "evaluator-release-protection-report:v1"
)
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
REPORT_SELF_POINTER = "/evidence_bundle_digest"
AUTHORIZATION_DIGEST_DOMAIN = "SKILLOPS_RELEASE_PROTECTED_PROMOTION_V1"
UTC_Z_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

POLICY_CODES = (
    "NOTIFICATION",
    "PUBLIC_VALUE",
    "RETENTION",
    "SOURCE_MATERIAL",
    "VERSION",
)
POLICY_CHANGE_MAP = {
    "NOTIFICATION": (
        "RELEASE_NOTIFICATION_POLICY_CHANGE",
        "NOTIFICATION_POLICY_CHANGE",
    ),
    "PUBLIC_VALUE": (
        "RELEASE_PRIVACY_POLICY_CHANGE",
        "PRIVACY_POLICY_CHANGE",
    ),
    "RETENTION": (
        "RELEASE_RETENTION_POLICY_CHANGE",
        "RETENTION_POLICY_CHANGE",
    ),
    "SOURCE_MATERIAL": (
        "RELEASE_SOURCE_POLICY_CHANGE",
        "SOURCE_LAYOUT_CHANGE",
    ),
    "VERSION": (
        "RELEASE_VERSION_POLICY_CHANGE",
        "HARD_GATE_CHANGE",
    ),
}
AUDIT_REQUIREMENTS = (
    (
        "OPTIMIZER_READ_SEALED_LABELS",
        "SEALED_LABELS",
        "READ",
    ),
    (
        "OPTIMIZER_WRITE_EVALUATOR",
        "EVALUATOR",
        "WRITE",
    ),
    (
        "OPTIMIZER_WRITE_EVAL_PROFILE",
        "EVAL_PROFILE",
        "WRITE",
    ),
    (
        "OPTIMIZER_WRITE_HARD_GATES",
        "HARD_GATES",
        "WRITE",
    ),
    (
        "OPTIMIZER_WRITE_PROMOTION_CONTROLLER",
        "PROMOTION_CONTROLLER",
        "WRITE",
    ),
    (
        "OPTIMIZER_WRITE_RELEASE_POLICY",
        "RELEASE_POLICY",
        "WRITE",
    ),
    (
        "OPTIMIZER_WRITE_RUBRIC",
        "RUBRIC",
        "WRITE",
    ),
)
SOURCE_ROLE_ACTOR_FIELD = {
    "INDEPENDENT_EVALUATOR": "evaluator_actor_ref",
    "OPTIMIZER": "optimizer_actor_ref",
    "RELEASE_AUTHORIZER": "release_actor_ref",
}
PROFILE_CHANGE_GROUPS = (
    (
        "EVALUATOR_MANIFEST_CHANGE",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        ("evaluator_manifest_digests",),
    ),
    (
        "SEALED_HOLDOUT_CHANGE",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        ("sealed_holdout_manifest_digest",),
    ),
    (
        "JUDGE_RUBRIC_CHANGE",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        ("judge_rubric_digest",),
    ),
    (
        "JUDGE_CALIBRATION_CHANGE",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        ("human_calibration_manifest_digest",),
    ),
    (
        "EVALUATION_DATA_CHANGE",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        (
            "dataset_manifest_digests",
            "routing_sets",
            "deterministic_check_manifest_digests",
            "confirmed_regression_manifest_digests",
        ),
    ),
    (
        "JUDGE_WEIGHT_CHANGE",
        "HARD_GATE_CHANGE",
        ("dimension_weights_bps",),
    ),
    (
        "HARD_GATE_SET_CHANGE",
        "HARD_GATE_CHANGE",
        ("hard_gate_codes",),
    ),
    (
        "EVALUATION_POLICY_CHANGE",
        "HARD_GATE_CHANGE",
        (
            "policy_snapshot_digest",
            "risk_class",
            "minimum_sample_count",
            "freshness_policy",
            "tool_manifest_digest",
        ),
    ),
)


class EvaluatorReleaseProtectionError(ValueError):
    """A protected-change or promotion invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class ReleaseProtectedPromotionAppendResult:
    """Canonical M-059 evidence plus the delegated M-058/M-056 result."""

    monitored_result: MonitoredPromotionAppendResult
    canonical_protection_report_bytes: bytes
    protection_report_digest: str
    authorization_digest: str


def _fail(code: str) -> None:
    raise EvaluatorReleaseProtectionError(code)


def _timestamp(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str):
        _fail(code)
    try:
        return dt.datetime.strptime(value, UTC_Z_FORMAT)
    except ValueError as exc:
        raise EvaluatorReleaseProtectionError(code) from exc


def _validate_artifact(
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
        raise EvaluatorReleaseProtectionError(code + ":" + str(exc)) from exc


def build_protection_contract(
    monitor_bundle: ContractBundle,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    report_schema: Mapping[str, Any],
    expected_report_schema_digest: str,
) -> ContractBundle:
    """Extend an M-058 contract with two exact bundle-external schemas."""

    additions = (
        (
            OBSERVATION_SCHEMA_ID,
            observation_schema,
            expected_observation_schema_digest,
            OBSERVATION_SELF_POINTER,
        ),
        (
            REPORT_SCHEMA_ID,
            report_schema,
            expected_report_schema_digest,
            REPORT_SELF_POINTER,
        ),
    )
    schemas = dict(monitor_bundle.schemas)
    pointers = dict(monitor_bundle.self_digest_pointers)
    for schema_id, document, expected_digest, pointer in additions:
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or not isinstance(expected_digest, str)
            or SHA256_RE.fullmatch(expected_digest) is None
            or canonical_digest(document) != expected_digest
        ):
            _fail("EVALUATOR_RELEASE_SCHEMA_TRUST_MISMATCH")
        if schema_id in schemas:
            _fail("EVALUATOR_RELEASE_SCHEMA_REBIND_FORBIDDEN")
        schemas[schema_id] = document
        pointers[schema_id] = pointer
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise EvaluatorReleaseProtectionError(
            "EVALUATOR_RELEASE_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=monitor_bundle.policies,
        protocol_revision=monitor_bundle.protocol_revision,
    )


def _profile_map(
    bundle: ContractBundle,
    profiles: Any,
    expected_bundle_digest: str,
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(profiles, list) or not profiles:
        _fail(code + "_SET_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    sort_keys = []
    for profile in profiles:
        if not isinstance(profile, dict):
            _fail(code + "_ENTRY_INVALID")
        _validate_artifact(
            bundle,
            profile,
            EVAL_PROFILE_SCHEMA_ID,
            expected_bundle_digest,
            code + "_ENTRY_INVALID",
        )
        if profile.get("bundle_digest") != expected_bundle_digest:
            _fail(code + "_BUNDLE_MISMATCH")
        identity_uid = profile["skill_identity_uid"]
        if identity_uid in result:
            _fail(code + "_IDENTITY_DUPLICATE")
        result[identity_uid] = profile
        sort_keys.append(
            (
                identity_uid,
                profile["eval_profile_uid"],
                canonical_digest(profile),
            )
        )
    if sort_keys != sorted(sort_keys):
        _fail(code + "_ORDER_INVALID")
    return result


def _validate_policy_descriptors(
    snapshot: Mapping[str, Any],
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    descriptors = snapshot.get("policy_descriptors")
    if (
        not isinstance(descriptors, list)
        or [entry.get("policy_code") for entry in descriptors]
        != list(POLICY_CODES)
    ):
        _fail(code + "_POLICY_SET_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for entry in descriptors:
        policy_code = entry["policy_code"]
        if policy_code in result:
            _fail(code + "_POLICY_DUPLICATE")
        result[policy_code] = entry
    return result


def _validate_isolation_audit(
    observation: Mapping[str, Any],
) -> str:
    audit = observation["isolation_audit"]
    if (
        audit["optimizer_actor_ref"] == audit["evaluator_actor_ref"]
        or audit["optimizer_actor_ref"] == audit["release_actor_ref"]
        or audit["evaluator_actor_ref"] == audit["release_actor_ref"]
        or audit["roles_distinct"] is not True
    ):
        _fail("EVALUATOR_RELEASE_ACTOR_SEPARATION_INVALID")
    source_role = observation["change_origin"]["source_role"]
    actor_field = SOURCE_ROLE_ACTOR_FIELD[source_role]
    if (
        observation["change_origin"]["actor_ref"]
        != audit[actor_field]
    ):
        _fail("EVALUATOR_RELEASE_CHANGE_ORIGIN_ACTOR_MISMATCH")
    attempts = audit["attempts"]
    observed_requirements = tuple(
        (
            entry["attempt_code"],
            entry["resource_code"],
            entry["operation"],
        )
        for entry in attempts
    )
    if observed_requirements != AUDIT_REQUIREMENTS:
        _fail("EVALUATOR_RELEASE_AUDIT_COVERAGE_INVALID")
    if any(entry["outcome"] != "DENIED" for entry in attempts):
        _fail("EVALUATOR_RELEASE_FORBIDDEN_ACCESS_NOT_DENIED")
    evidence_digests = [entry["evidence_digest"] for entry in attempts]
    if len(evidence_digests) != len(set(evidence_digests)):
        _fail("EVALUATOR_RELEASE_AUDIT_EVIDENCE_REUSED")
    if (
        audit["forbidden_attempt_count"] != len(AUDIT_REQUIREMENTS)
        or audit["denied_attempt_count"] != len(AUDIT_REQUIREMENTS)
        or audit["allowed_forbidden_attempt_count"] != 0
    ):
        _fail("EVALUATOR_RELEASE_AUDIT_COUNT_MISMATCH")
    if _timestamp(
        audit["completed_at"],
        "EVALUATOR_RELEASE_AUDIT_TIME_INVALID",
    ) > _timestamp(
        observation["observed_at"],
        "EVALUATOR_RELEASE_OBSERVED_AT_INVALID",
    ):
        _fail("EVALUATOR_RELEASE_AUDIT_AFTER_OBSERVATION")
    digest = canonical_digest(audit)
    if observation["optimizer_evaluator_isolation_digest"] != digest:
        _fail("EVALUATOR_RELEASE_ISOLATION_DIGEST_MISMATCH")
    return digest


def _add_change(
    changes: Dict[str, Dict[str, Any]],
    *,
    change_code: str,
    trigger_code: str,
    subject_code: str,
) -> None:
    existing = changes.get(change_code)
    if existing is None:
        changes[change_code] = {
            "change_code": change_code,
            "major_trigger_code": trigger_code,
            "subject_codes": {subject_code},
        }
        return
    if existing["major_trigger_code"] != trigger_code:
        _fail("EVALUATOR_RELEASE_CHANGE_CLASSIFIER_CONFLICT")
    existing["subject_codes"].add(subject_code)


def _profile_changes(
    baseline: Mapping[str, Mapping[str, Any]],
    proposed: Mapping[str, Mapping[str, Any]],
    changes: Dict[str, Dict[str, Any]],
) -> None:
    identities = sorted(set(baseline).union(proposed))
    for identity_uid in identities:
        before = baseline.get(identity_uid)
        after = proposed.get(identity_uid)
        if before is None or after is None:
            _add_change(
                changes,
                change_code="EVAL_PROFILE_SET_CHANGE",
                trigger_code="EVALUATOR_OR_HOLDOUT_CHANGE",
                subject_code="EVAL_PROFILE",
            )
            continue
        any_specific = False
        for change_code, trigger_code, fields in PROFILE_CHANGE_GROUPS:
            if any(before[field] != after[field] for field in fields):
                any_specific = True
                _add_change(
                    changes,
                    change_code=change_code,
                    trigger_code=trigger_code,
                    subject_code="EVAL_PROFILE",
                )
        if (
            canonicalize_object(before) != canonicalize_object(after)
            and not any_specific
        ):
            _add_change(
                changes,
                change_code="EVAL_PROFILE_RECORD_CHANGE",
                trigger_code="EVALUATOR_OR_HOLDOUT_CHANGE",
                subject_code="EVAL_PROFILE",
            )


def _release_changes(
    baseline: Mapping[str, Any],
    proposed: Mapping[str, Any],
    changes: Dict[str, Dict[str, Any]],
) -> None:
    before_policies = _validate_policy_descriptors(
        baseline,
        "EVALUATOR_RELEASE_BASELINE",
    )
    after_policies = _validate_policy_descriptors(
        proposed,
        "EVALUATOR_RELEASE_PROPOSED",
    )
    for policy_code in POLICY_CODES:
        if (
            canonicalize_object(before_policies[policy_code])
            != canonicalize_object(after_policies[policy_code])
        ):
            change_code, trigger_code = POLICY_CHANGE_MAP[policy_code]
            _add_change(
                changes,
                change_code=change_code,
                trigger_code=trigger_code,
                subject_code="POLICY_" + policy_code,
            )
    if (
        baseline["policy_snapshot_digest"]
        != proposed["policy_snapshot_digest"]
        and not any(
            code.startswith("RELEASE_")
            for code in changes
        )
    ):
        _add_change(
            changes,
            change_code="RELEASE_POLICY_SNAPSHOT_CHANGE",
            trigger_code="HARD_GATE_CHANGE",
            subject_code="POLICY_SNAPSHOT",
        )
    if (
        canonicalize_object(baseline["promotion_controller"])
        != canonicalize_object(proposed["promotion_controller"])
    ):
        _add_change(
            changes,
            change_code="PROMOTION_CONTROLLER_CHANGE",
            trigger_code="HARD_GATE_CHANGE",
            subject_code="PROMOTION_CONTROLLER",
        )


def _profile_refs(
    profiles: Mapping[str, Mapping[str, Any]],
) -> list[Dict[str, str]]:
    return [
        {
            "skill_identity_uid": identity_uid,
            "eval_profile_uid": profile["eval_profile_uid"],
            "artifact_digest": canonical_digest(profile),
        }
        for identity_uid, profile in sorted(profiles.items())
    ]


def _validate_reference_closure(
    bundle: ContractBundle,
    *,
    observation: Mapping[str, Any],
    promotion_evidence: Mapping[str, Any],
    decision: Mapping[str, Any],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    baseline_profiles: Mapping[str, Mapping[str, Any]],
    proposed_profiles: Mapping[str, Mapping[str, Any]],
    expected_bundle_digest: str,
    expected_promotion_controller_path: str,
    expected_promotion_controller_digest: str,
) -> None:
    _validate_artifact(
        bundle,
        promotion_evidence,
        PROMOTION_EVIDENCE_SCHEMA_ID,
        expected_bundle_digest,
        "EVALUATOR_RELEASE_PROMOTION_EVIDENCE_INVALID",
    )
    _validate_artifact(
        bundle,
        decision,
        PROMOTION_DECISION_SCHEMA_ID,
        expected_bundle_digest,
        "EVALUATOR_RELEASE_DECISION_INVALID",
    )
    if (
        decision.get("action") != "PROMOTE"
        or observation["promotion_decision_ref"]["decision_digest"]
        != decision.get("decision_digest")
        or observation["promotion_evidence_ref"]["artifact_digest"]
        != promotion_evidence.get("evidence_bundle_digest")
        or decision.get("evidence_bundle_digest")
        != promotion_evidence.get("evidence_bundle_digest")
    ):
        _fail("EVALUATOR_RELEASE_DECISION_EVIDENCE_CLOSURE_MISMATCH")
    if not isinstance(scorecards_by_digest, dict):
        _fail("EVALUATOR_RELEASE_SCORECARD_MAP_INVALID")
    referenced = {
        ref["artifact_digest"]
        for ref in promotion_evidence["scorecard_refs"]
    }
    if referenced != set(scorecards_by_digest):
        _fail("EVALUATOR_RELEASE_SCORECARD_REFERENCE_SET_MISMATCH")
    used_profile_digests = set()
    used_identity_uids = set()
    for digest in sorted(referenced):
        scorecard = scorecards_by_digest[digest]
        if (
            not isinstance(scorecard, dict)
            or scorecard.get("scorecard_digest") != digest
        ):
            _fail("EVALUATOR_RELEASE_SCORECARD_MAP_ENTRY_INVALID")
        _validate_artifact(
            bundle,
            scorecard,
            SCORECARD_SCHEMA_ID,
            expected_bundle_digest,
            "EVALUATOR_RELEASE_SCORECARD_INVALID",
        )
        profile_digest = scorecard["eval_profile_digest"]
        matches = [
            (identity_uid, profile)
            for identity_uid, profile in baseline_profiles.items()
            if canonical_digest(profile) == profile_digest
        ]
        if len(matches) != 1:
            _fail("EVALUATOR_RELEASE_BASELINE_PROFILE_REFERENCE_MISSING")
        identity_uid, _ = matches[0]
        used_profile_digests.add(profile_digest)
        used_identity_uids.add(identity_uid)
    if (
        used_profile_digests
        != {canonical_digest(value) for value in baseline_profiles.values()}
        or used_identity_uids != set(baseline_profiles)
        or set(proposed_profiles) != set(baseline_profiles)
    ):
        _fail("EVALUATOR_RELEASE_PROFILE_CLOSURE_MISMATCH")
    baseline_snapshot = observation["baseline_release_snapshot"]
    proposed_snapshot = observation["proposed_release_snapshot"]
    if (
        baseline_snapshot["policy_snapshot_digest"]
        != promotion_evidence["policy_snapshot_digest"]
        or any(
            profile["policy_snapshot_digest"]
            != baseline_snapshot["policy_snapshot_digest"]
            for profile in baseline_profiles.values()
        )
        or any(
            profile["policy_snapshot_digest"]
            != proposed_snapshot["policy_snapshot_digest"]
            for profile in proposed_profiles.values()
        )
        or baseline_snapshot["promotion_controller"]
        != {
            "canonical_path": expected_promotion_controller_path,
            "artifact_digest": expected_promotion_controller_digest,
        }
    ):
        _fail("EVALUATOR_RELEASE_PROTECTED_SNAPSHOT_CLOSURE_MISMATCH")
    if _timestamp(
        observation["observed_at"],
        "EVALUATOR_RELEASE_OBSERVED_AT_INVALID",
    ) > _timestamp(
        decision["decided_at"],
        "EVALUATOR_RELEASE_DECISION_TIME_INVALID",
    ):
        _fail("EVALUATOR_RELEASE_OBSERVATION_AFTER_DECISION")


def evaluate_evaluator_release_protection(
    bundle: ContractBundle,
    *,
    observation: Mapping[str, Any],
    promotion_evidence: Mapping[str, Any],
    decision: Mapping[str, Any],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    report_uid: str,
    version_policy: Mapping[str, Any],
    expected_version_policy_sha256: str,
    expected_promotion_controller_path: str,
    expected_promotion_controller_digest: str,
    expected_bundle_digest: str,
) -> Dict[str, Any]:
    """Build the only canonical protection report for one promotion attempt."""

    _validate_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "EVALUATOR_RELEASE_OBSERVATION_INVALID",
    )
    baseline_profiles = _profile_map(
        bundle,
        observation["baseline_eval_profiles"],
        expected_bundle_digest,
        "EVALUATOR_RELEASE_BASELINE_PROFILE",
    )
    proposed_profiles = _profile_map(
        bundle,
        observation["proposed_eval_profiles"],
        expected_bundle_digest,
        "EVALUATOR_RELEASE_PROPOSED_PROFILE",
    )
    isolation_digest = _validate_isolation_audit(observation)
    _validate_reference_closure(
        bundle,
        observation=observation,
        promotion_evidence=promotion_evidence,
        decision=decision,
        scorecards_by_digest=scorecards_by_digest,
        baseline_profiles=baseline_profiles,
        proposed_profiles=proposed_profiles,
        expected_bundle_digest=expected_bundle_digest,
        expected_promotion_controller_path=(
            expected_promotion_controller_path
        ),
        expected_promotion_controller_digest=(
            expected_promotion_controller_digest
        ),
    )
    try:
        validate_version_policy_v3(version_policy)
    except VersionPolicyV3Error as exc:
        raise EvaluatorReleaseProtectionError(
            "EVALUATOR_RELEASE_VERSION_POLICY_INVALID:" + exc.code
        ) from exc
    policy_sha256 = canonical_digest(version_policy)
    if (
        not isinstance(expected_version_policy_sha256, str)
        or policy_sha256 != expected_version_policy_sha256
    ):
        _fail("EVALUATOR_RELEASE_VERSION_POLICY_TRUST_MISMATCH")

    changes: Dict[str, Dict[str, Any]] = {}
    _profile_changes(baseline_profiles, proposed_profiles, changes)
    _release_changes(
        observation["baseline_release_snapshot"],
        observation["proposed_release_snapshot"],
        changes,
    )
    trigger_codes = sorted(
        {value["major_trigger_code"] for value in changes.values()}
    )
    if trigger_codes:
        try:
            impact = classify_v3_impact(trigger_codes, version_policy)
        except VersionPolicyV3Error as exc:
            raise EvaluatorReleaseProtectionError(
                "EVALUATOR_RELEASE_IMPACT_CLASSIFICATION_FAILED:"
                + exc.code
            ) from exc
        if impact != "MAJOR":
            _fail("EVALUATOR_RELEASE_PROTECTED_CHANGE_NOT_MAJOR")
    else:
        impact = "NONE"

    origin_role = observation["change_origin"]["source_role"]
    if not changes:
        reason_code = "PROTECTED_SURFACES_UNCHANGED"
    elif origin_role == "OPTIMIZER":
        reason_code = "OPTIMIZER_PROTECTED_CHANGE_BLOCKED"
    else:
        reason_code = "INDEPENDENT_MAJOR_RELEASE_REQUIRED"
    pass_gate = not changes
    observation_digest = observation["evidence_bundle_digest"]
    detected_changes = []
    for change_code, value in sorted(changes.items()):
        detected_changes.append(
            {
                "change_code": change_code,
                "major_trigger_code": value["major_trigger_code"],
                "subject_codes": sorted(value["subject_codes"]),
                "evidence_digest": observation_digest,
            }
        )
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "report_uid": report_uid,
        "promotion_decision_ref": {
            "decision_digest": decision["decision_digest"],
        },
        "promotion_evidence_ref": {
            "artifact_digest": promotion_evidence[
                "evidence_bundle_digest"
            ],
        },
        "observation_ref": {
            "artifact_digest": observation_digest,
        },
        "baseline_eval_profile_refs": _profile_refs(baseline_profiles),
        "proposed_eval_profile_refs": _profile_refs(proposed_profiles),
        "detected_changes": detected_changes,
        "major_trigger_codes": trigger_codes,
        "impact": impact,
        "classification": {
            "policy_id": VERSION_POLICY_V3_ID,
            "policy_sha256": policy_sha256,
            "impact_downgrade_allowed": False,
            "unknown_trigger_action": "FAIL_CLOSED",
        },
        "isolation_gate": {
            "status": "PASS",
            "optimizer_evaluator_isolation_digest": isolation_digest,
            "roles_distinct": True,
            "forbidden_attempt_count": len(AUDIT_REQUIREMENTS),
            "denied_attempt_count": len(AUDIT_REQUIREMENTS),
            "all_forbidden_attempts_denied": True,
        },
        "promotion_gate": {
            "status": "PASS" if pass_gate else "BLOCKED",
            "reason_code": reason_code,
            "optimizer_self_improvement_permitted": False,
            "protected_release_write_permitted": False,
            "separate_major_release_required": bool(changes),
            "m058_delegation_permitted": pass_gate,
        },
        "generated_at": observation["observed_at"],
        "actor": "SKILLOPS_EVALUATOR_RELEASE_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    report["evidence_bundle_digest"] = canonical_digest(
        report,
        REPORT_SELF_POINTER,
    )
    _validate_artifact(
        bundle,
        report,
        REPORT_SCHEMA_ID,
        expected_bundle_digest,
        "EVALUATOR_RELEASE_REPORT_INVALID",
    )
    return report


def validate_evaluator_release_protection_report(
    bundle: ContractBundle,
    *,
    observation: Mapping[str, Any],
    promotion_evidence: Mapping[str, Any],
    decision: Mapping[str, Any],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    report: Mapping[str, Any],
    version_policy: Mapping[str, Any],
    expected_version_policy_sha256: str,
    expected_promotion_controller_path: str,
    expected_promotion_controller_digest: str,
    expected_bundle_digest: str,
) -> None:
    """Require a supplied report to equal deterministic recomputation."""

    if not isinstance(report, dict):
        _fail("EVALUATOR_RELEASE_REPORT_ROOT_INVALID")
    _validate_artifact(
        bundle,
        report,
        REPORT_SCHEMA_ID,
        expected_bundle_digest,
        "EVALUATOR_RELEASE_REPORT_INVALID",
    )
    expected = evaluate_evaluator_release_protection(
        bundle,
        observation=observation,
        promotion_evidence=promotion_evidence,
        decision=decision,
        scorecards_by_digest=scorecards_by_digest,
        report_uid=report["report_uid"],
        version_policy=version_policy,
        expected_version_policy_sha256=expected_version_policy_sha256,
        expected_promotion_controller_path=(
            expected_promotion_controller_path
        ),
        expected_promotion_controller_digest=(
            expected_promotion_controller_digest
        ),
        expected_bundle_digest=expected_bundle_digest,
    )
    if canonicalize_object(report) != canonicalize_object(expected):
        _fail("EVALUATOR_RELEASE_REPORT_RECOMPUTATION_MISMATCH")


def _artifact_map(
    values: Mapping[str, Mapping[str, Any]],
    digest_field: str,
    code: str,
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(values, dict):
        _fail(code + "_MAP_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for digest, value in values.items():
        if (
            not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            or not isinstance(value, dict)
            or value.get(digest_field) != digest
        ):
            _fail(code + "_MAP_ENTRY_INVALID")
        result[digest] = value
    return result


def _canonical_profile_map(
    values: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Mapping[str, Any]]:
    if not isinstance(values, dict):
        _fail("EVALUATOR_RELEASE_EVAL_PROFILE_MAP_INVALID")
    result: Dict[str, Mapping[str, Any]] = {}
    for digest, value in values.items():
        if (
            not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            or not isinstance(value, dict)
            or canonical_digest(value) != digest
        ):
            _fail("EVALUATOR_RELEASE_EVAL_PROFILE_MAP_ENTRY_INVALID")
        result[digest] = value
    return result


def append_release_protected_promotion_decision(
    bundle: ContractBundle,
    registry_view: Any,
    *,
    eval_profiles_by_digest: Mapping[str, Mapping[str, Any]],
    freshness_observations_by_digest: Mapping[str, Mapping[str, Any]],
    freshness_reports_by_digest: Mapping[str, Mapping[str, Any]],
    protection_observations_by_digest: Mapping[str, Mapping[str, Any]],
    protection_reports_by_digest: Mapping[str, Mapping[str, Any]],
    evidence_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    existing_decisions: Sequence[Mapping[str, Any]],
    decision: Mapping[str, Any],
    version_policy: Mapping[str, Any],
    expected_version_policy_sha256: str,
    expected_promotion_controller_path: str,
    expected_promotion_controller_digest: str,
    expected_predecessor_ledger_digest: str,
    expected_bundle_digest: str,
) -> ReleaseProtectedPromotionAppendResult:
    """Delegate through M-058 only after one exact M-059 PASS report."""

    profiles = _canonical_profile_map(eval_profiles_by_digest)
    evidences = _artifact_map(
        evidence_by_digest,
        "evidence_bundle_digest",
        "EVALUATOR_RELEASE_PROMOTION_EVIDENCE",
    )
    scorecards = _artifact_map(
        scorecards_by_digest,
        "scorecard_digest",
        "EVALUATOR_RELEASE_SCORECARD",
    )
    observations = _artifact_map(
        protection_observations_by_digest,
        "evidence_bundle_digest",
        "EVALUATOR_RELEASE_OBSERVATION",
    )
    reports = _artifact_map(
        protection_reports_by_digest,
        "evidence_bundle_digest",
        "EVALUATOR_RELEASE_REPORT",
    )
    action = decision.get("action") if isinstance(decision, dict) else None
    if action == "PROMOTE":
        if len(observations) != 1 or len(reports) != 1:
            _fail("EVALUATOR_RELEASE_PROTECTION_CLOSURE_REQUIRED")
        evidence = evidences.get(decision.get("evidence_bundle_digest"))
        if not isinstance(evidence, dict):
            _fail("EVALUATOR_RELEASE_PROMOTION_EVIDENCE_MISSING")
        observation = next(iter(observations.values()))
        report = next(iter(reports.values()))
        validate_evaluator_release_protection_report(
            bundle,
            observation=observation,
            promotion_evidence=evidence,
            decision=decision,
            scorecards_by_digest=scorecards,
            report=report,
            version_policy=version_policy,
            expected_version_policy_sha256=(
                expected_version_policy_sha256
            ),
            expected_promotion_controller_path=(
                expected_promotion_controller_path
            ),
            expected_promotion_controller_digest=(
                expected_promotion_controller_digest
            ),
            expected_bundle_digest=expected_bundle_digest,
        )
        baseline = {
            canonical_digest(profile): profile
            for profile in observation["baseline_eval_profiles"]
        }
        if (
            baseline != profiles
            or report["promotion_gate"]["status"] != "PASS"
            or report["promotion_gate"][
                "optimizer_self_improvement_permitted"
            ]
            is not False
            or report["promotion_gate"][
                "protected_release_write_permitted"
            ]
            is not False
            or report["promotion_gate"]["m058_delegation_permitted"]
            is not True
            or report["impact"] != "NONE"
            or report["detected_changes"]
            or report["major_trigger_codes"]
        ):
            _fail("EVALUATOR_RELEASE_PROMOTION_GATE_BLOCKED")
        if _timestamp(
            report["generated_at"],
            "EVALUATOR_RELEASE_REPORT_TIME_INVALID",
        ) > _timestamp(
            decision["decided_at"],
            "EVALUATOR_RELEASE_DECISION_TIME_INVALID",
        ):
            _fail("EVALUATOR_RELEASE_REPORT_AFTER_DECISION")
    elif action == "REJECT":
        if observations or reports:
            _fail("EVALUATOR_RELEASE_REJECT_PROTECTION_ARTIFACT_FORBIDDEN")
        report = None
    else:
        _fail("EVALUATOR_RELEASE_PROMOTE_OR_REJECT_REQUIRED")

    try:
        monitored_result = append_monitored_promotion_decision(
            bundle,
            registry_view,
            eval_profiles_by_digest=profiles,
            observations_by_digest=freshness_observations_by_digest,
            reports_by_digest=freshness_reports_by_digest,
            evidence_by_digest=evidences,
            scorecards_by_digest=scorecards,
            eval_runs_by_digest=eval_runs_by_digest,
            existing_decisions=existing_decisions,
            decision=decision,
            expected_predecessor_ledger_digest=(
                expected_predecessor_ledger_digest
            ),
            expected_bundle_digest=expected_bundle_digest,
        )
    except FreshnessDriftError as exc:
        raise EvaluatorReleaseProtectionError(
            "EVALUATOR_RELEASE_M058_DELEGATION_FAILED:" + str(exc)
        ) from exc

    if report is None:
        canonical_report = b""
        report_digest = "0" * 64
    else:
        canonical_report = canonicalize_object(report)
        report_digest = report["evidence_bundle_digest"]
    authorization_digest = canonical_digest(
        {
            "bundle_digest": expected_bundle_digest,
            "decision_digest": (
                monitored_result.promotion_result.decision_digest
            ),
            "domain": AUTHORIZATION_DIGEST_DOMAIN,
            "m058_authorization_digest": (
                monitored_result.authorization_digest
            ),
            "protection_report_digest": report_digest,
            "protocol_revision": PROTOCOL_REVISION,
        }
    )
    return ReleaseProtectedPromotionAppendResult(
        monitored_result=monitored_result,
        canonical_protection_report_bytes=canonical_report,
        protection_report_digest=report_digest,
        authorization_digest=authorization_digest,
    )
