"""Pure freshness/drift monitor and promotion gate for Task Pack M-058.

The monitor validates bundle-external observation/report contracts against an
externally trusted candidate bundle.  It deterministically recomputes stale,
behavior, latency, context, incident, and EvalProfile trigger-gap alerts.

The module never reads or writes state, Registry, Git, VERSION, notifications,
or public artifacts.  Promotion remains delegated to the immutable M-056
controller only after an exact, recomputed ``PROMOTION_GATE`` report passes.
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
    PROTOCOL_REVISION,
    SCORECARD_SCHEMA_ID,
    PromotionAppendResult,
    PromotionControllerError,
    PromotionRegistryView,
    append_promotion_decision,
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
OBSERVATION_SCHEMA_ID = SCHEMA_PREFIX + "freshness-drift-observation:v1"
REPORT_SCHEMA_ID = SCHEMA_PREFIX + "freshness-drift-report:v1"
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
REPORT_SELF_POINTER = "/evidence_bundle_digest"
AUTHORIZATION_DIGEST_DOMAIN = "SKILLOPS_MONITORED_PROMOTION_V1"
UTC_Z_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

DIMENSION_CODES = (
    "EFFICIENCY",
    "MAINTAINABILITY",
    "NEGATIVE_CAPABILITY",
    "OUTCOME",
    "RELIABILITY",
    "ROUTING",
    "SAFETY_GOVERNANCE",
)
RETEST_TRIGGER_CODES = (
    "DATASET_CHANGE",
    "DEPENDENCY_CHANGE",
    "EVALUATOR_CHANGE",
    "INCIDENT",
    "MODEL_CHANGE",
    "POLICY_CHANGE",
    "SCORE_DRIFT",
    "SKILL_CHANGE",
    "TOOL_CHANGE",
)


class FreshnessDriftError(ValueError):
    """A monitoring or monitored-promotion invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class MonitoredPromotionAppendResult:
    """Canonical monitor evidence plus the delegated M-056 append result."""

    promotion_result: PromotionAppendResult
    canonical_report_bytes: Tuple[bytes, ...]
    report_digests: Tuple[str, ...]
    authorization_digest: str


def _fail(code: str) -> None:
    raise FreshnessDriftError(code)


def _timestamp(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str):
        _fail(code)
    try:
        return dt.datetime.strptime(value, UTC_Z_FORMAT)
    except ValueError as exc:
        raise FreshnessDriftError(code) from exc


def _calendar_date(value: Any, code: str) -> dt.date:
    if not isinstance(value, str):
        _fail(code)
    try:
        return dt.date.fromisoformat(value)
    except ValueError as exc:
        raise FreshnessDriftError(code) from exc


def _sorted_unique(values: Any, code: str) -> None:
    if (
        not isinstance(values, list)
        or any(not isinstance(value, str) for value in values)
        or values != sorted(values, key=lambda value: value.encode("ascii"))
        or len(values) != len(set(values))
    ):
        _fail(code)


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
        raise FreshnessDriftError(code + ":" + str(exc)) from exc


def build_monitor_contract(
    candidate_bundle: ContractBundle,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    report_schema: Mapping[str, Any],
    expected_report_schema_digest: str,
) -> ContractBundle:
    """Extend one trusted candidate with two explicitly pinned schemas."""

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
    schemas = dict(candidate_bundle.schemas)
    pointers = dict(candidate_bundle.self_digest_pointers)
    for schema_id, document, expected_digest, pointer in additions:
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or not isinstance(expected_digest, str)
            or SHA256_RE.fullmatch(expected_digest) is None
            or canonical_digest(document) != expected_digest
        ):
            _fail("FRESHNESS_DRIFT_SCHEMA_TRUST_MISMATCH")
        if schema_id in schemas:
            _fail("FRESHNESS_DRIFT_SCHEMA_REBIND_FORBIDDEN")
        schemas[schema_id] = document
        pointers[schema_id] = pointer
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise FreshnessDriftError(
            "FRESHNESS_DRIFT_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=candidate_bundle.policies,
        protocol_revision=candidate_bundle.protocol_revision,
    )


def _validate_inputs(
    bundle: ContractBundle,
    *,
    eval_profile: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    observation: Mapping[str, Any],
    expected_bundle_digest: str,
) -> Tuple[str, str]:
    _validate_artifact(
        bundle,
        eval_profile,
        EVAL_PROFILE_SCHEMA_ID,
        expected_bundle_digest,
        "FRESHNESS_DRIFT_EVAL_PROFILE_INVALID",
    )
    _validate_artifact(
        bundle,
        scorecard,
        SCORECARD_SCHEMA_ID,
        expected_bundle_digest,
        "FRESHNESS_DRIFT_SCORECARD_INVALID",
    )
    _validate_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "FRESHNESS_DRIFT_OBSERVATION_INVALID",
    )
    profile_digest = canonical_digest(eval_profile)
    scorecard_digest = scorecard["scorecard_digest"]
    if (
        observation["scorecard_ref"]["scorecard_uid"]
        != scorecard["scorecard_uid"]
        or observation["scorecard_ref"]["artifact_digest"]
        != scorecard_digest
        or observation["eval_profile_ref"]["eval_profile_uid"]
        != eval_profile["eval_profile_uid"]
        or observation["eval_profile_ref"]["artifact_digest"]
        != profile_digest
        or scorecard["eval_profile_uid"] != eval_profile["eval_profile_uid"]
        or scorecard["eval_profile_digest"] != profile_digest
    ):
        _fail("FRESHNESS_DRIFT_REFERENCE_CLOSURE_MISMATCH")

    behavior = observation["behavior_metrics"]
    if (
        [entry["dimension_code"] for entry in behavior]
        != list(DIMENSION_CODES)
    ):
        _fail("FRESHNESS_DRIFT_BEHAVIOR_DIMENSION_SET_INVALID")
    score_dimensions = scorecard["dimensions"]
    if (
        [entry["dimension_code"] for entry in score_dimensions]
        != list(DIMENSION_CODES)
    ):
        _fail("FRESHNESS_DRIFT_SCORECARD_DIMENSION_SET_INVALID")

    for field in (
        "dataset_manifest_digests",
        "evaluator_manifest_digests",
    ):
        _sorted_unique(
            observation["context"][field],
            "FRESHNESS_DRIFT_CONTEXT_ORDER_INVALID",
        )
    _sorted_unique(
        observation["critical_incident_evidence_digests"],
        "FRESHNESS_DRIFT_INCIDENT_EVIDENCE_ORDER_INVALID",
    )
    if (
        observation["critical_incident_count"]
        != len(observation["critical_incident_evidence_digests"])
    ):
        _fail("FRESHNESS_DRIFT_INCIDENT_EVIDENCE_COUNT_MISMATCH")
    for name in ("baseline", "current"):
        summary = observation["latency"][name]
        if not (
            summary["p50_milliseconds"]
            <= summary["p95_milliseconds"]
            <= summary["max_milliseconds"]
        ):
            _fail("FRESHNESS_DRIFT_LATENCY_ORDER_INVALID")
    observed_at = _timestamp(
        observation["observed_at"],
        "FRESHNESS_DRIFT_OBSERVED_AT_INVALID",
    )
    evaluated_at = _timestamp(
        scorecard["evaluated_at"],
        "FRESHNESS_DRIFT_EVALUATED_AT_INVALID",
    )
    if observed_at < evaluated_at:
        _fail("FRESHNESS_DRIFT_TIME_ORDER_INVALID")
    return profile_digest, scorecard_digest


def _alert(
    *,
    category: str,
    code: str,
    severity: str,
    subjects: Sequence[str],
    evidence_digest: str,
    action_code: str = "REEVALUATE",
) -> Dict[str, Any]:
    return {
        "action_code": action_code,
        "category": category,
        "code": code,
        "evidence_digest": evidence_digest,
        "severity": severity,
        "subject_codes": sorted(
            subjects,
            key=lambda value: value.encode("ascii"),
        ),
    }


def _alert_sort_key(value: Mapping[str, Any]) -> Tuple[Any, ...]:
    return (
        value["category"],
        value["code"],
        tuple(value["subject_codes"]),
        value["evidence_digest"],
    )


def evaluate_freshness_drift(
    bundle: ContractBundle,
    *,
    eval_profile: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    observation: Mapping[str, Any],
    report_uid: str,
    mode: str,
    promotion_decision_digest: Optional[str],
    expected_bundle_digest: str,
) -> Dict[str, Any]:
    """Build the only canonical report for one observation and scorecard."""

    profile_digest, scorecard_digest = _validate_inputs(
        bundle,
        eval_profile=eval_profile,
        scorecard=scorecard,
        observation=observation,
        expected_bundle_digest=expected_bundle_digest,
    )
    if mode not in {"MONITOR_ONLY", "PROMOTION_GATE"}:
        _fail("FRESHNESS_DRIFT_REPORT_MODE_INVALID")
    if mode == "PROMOTION_GATE":
        if (
            not isinstance(promotion_decision_digest, str)
            or SHA256_RE.fullmatch(promotion_decision_digest) is None
        ):
            _fail("FRESHNESS_DRIFT_PROMOTION_DECISION_DIGEST_REQUIRED")
    elif promotion_decision_digest is not None:
        _fail("FRESHNESS_DRIFT_MONITOR_ONLY_DECISION_FORBIDDEN")

    observed_at = _timestamp(
        observation["observed_at"],
        "FRESHNESS_DRIFT_OBSERVED_AT_INVALID",
    )
    evaluated_at = _timestamp(
        scorecard["evaluated_at"],
        "FRESHNESS_DRIFT_EVALUATED_AT_INVALID",
    )
    max_age_days = eval_profile["freshness_policy"]["max_age_days"]
    deadline_at = evaluated_at + dt.timedelta(days=max_age_days)
    elapsed = observed_at - evaluated_at
    age_microseconds = (
        elapsed.days * 86_400_000_000
        + elapsed.seconds * 1_000_000
        + elapsed.microseconds
    )
    observation_digest = observation["evidence_bundle_digest"]
    alerts = []
    trigger_codes = set()

    freshness_state = scorecard["freshness_state"]
    if freshness_state == "STALE":
        alerts.append(
            _alert(
                category="STALE",
                code="SCORECARD_STATE_STALE",
                severity="CRITICAL",
                subjects=["SCORECARD"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SCORE_DRIFT")
    elif freshness_state == "UNKNOWN":
        alerts.append(
            _alert(
                category="STALE",
                code="SCORECARD_STATE_UNKNOWN",
                severity="CRITICAL",
                subjects=["SCORECARD"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SCORE_DRIFT")

    if observed_at > deadline_at:
        freshness_state = "STALE"
        alerts.append(
            _alert(
                category="STALE",
                code="SCORECARD_MAX_AGE_EXCEEDED",
                severity="CRITICAL",
                subjects=["MAX_AGE_DAYS"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SCORE_DRIFT")
    valid_until = scorecard["freshness_valid_until"]
    if (
        valid_until is not None
        and observed_at.date()
        > _calendar_date(
            valid_until,
            "FRESHNESS_DRIFT_VALID_UNTIL_INVALID",
        )
    ):
        freshness_state = "STALE"
        alerts.append(
            _alert(
                category="STALE",
                code="SCORECARD_VALIDITY_EXPIRED",
                severity="CRITICAL",
                subjects=["FRESHNESS_VALID_UNTIL"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SCORE_DRIFT")

    if (
        observation["skill_version_uid"] != scorecard["skill_version_uid"]
        or observation["skill_version_record_digest"]
        != scorecard["skill_version_record_digest"]
    ):
        alerts.append(
            _alert(
                category="CONTEXT",
                code="SKILL_CHANGE",
                severity="CRITICAL",
                subjects=["SKILL_VERSION"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SKILL_CHANGE")

    score_by_dimension = {
        entry["dimension_code"]: entry["score_bps"]
        for entry in scorecard["dimensions"]
    }
    changed_dimensions = [
        entry["dimension_code"]
        for entry in observation["behavior_metrics"]
        if entry["score_bps"]
        != score_by_dimension[entry["dimension_code"]]
    ]
    if changed_dimensions:
        alerts.append(
            _alert(
                category="BEHAVIOR",
                code="BEHAVIOR_SCORE_CHANGE",
                severity="CRITICAL",
                subjects=changed_dimensions,
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("SCORE_DRIFT")

    context = observation["context"]
    comparisons = (
        (
            "MODEL_CHANGE",
            context["model_snapshot_digest"],
            scorecard["model_snapshot_digest"],
            "MODEL",
        ),
        (
            "TOOL_CHANGE",
            context["tool_manifest_digest"],
            eval_profile["tool_manifest_digest"],
            "TOOL",
        ),
        (
            "DATASET_CHANGE",
            context["dataset_manifest_digests"],
            sorted(
                eval_profile["dataset_manifest_digests"],
                key=lambda value: value.encode("ascii"),
            ),
            "DATASET",
        ),
        (
            "EVALUATOR_CHANGE",
            context["evaluator_manifest_digests"],
            sorted(
                eval_profile["evaluator_manifest_digests"],
                key=lambda value: value.encode("ascii"),
            ),
            "EVALUATOR",
        ),
        (
            "POLICY_CHANGE",
            context["policy_snapshot_digest"],
            eval_profile["policy_snapshot_digest"],
            "POLICY",
        ),
    )
    for code, current, baseline, subject in comparisons:
        if current != baseline:
            alerts.append(
                _alert(
                    category="CONTEXT",
                    code=code,
                    severity="CRITICAL",
                    subjects=[subject],
                    evidence_digest=observation_digest,
                )
            )
            trigger_codes.add(code)
    if (
        context["environment_fingerprint_digest"]
        != scorecard["environment_fingerprint_digest"]
    ):
        alerts.append(
            _alert(
                category="CONTEXT",
                code="ENVIRONMENT_CHANGE",
                severity="CRITICAL",
                subjects=["ENVIRONMENT"],
                evidence_digest=observation_digest,
            )
        )
        # EvalProfile v1 has no ENVIRONMENT_CHANGE code.  TOOL_CHANGE is the
        # conservative supported trigger for runtime/tool environment drift.
        trigger_codes.add("TOOL_CHANGE")
    dependency = observation["dependency_context"]
    if (
        dependency["baseline"]["dependency_manifest_digest"]
        != dependency["current"]["dependency_manifest_digest"]
    ):
        alerts.append(
            _alert(
                category="CONTEXT",
                code="DEPENDENCY_CHANGE",
                severity="CRITICAL",
                subjects=["DEPENDENCY"],
                evidence_digest=observation_digest,
            )
        )
        trigger_codes.add("DEPENDENCY_CHANGE")

    latency = observation["latency"]
    insufficient_latency_samples = [
        name.upper() + "_SAMPLE_COUNT"
        for name in ("baseline", "current")
        if latency[name]["sample_count"]
        < eval_profile["minimum_sample_count"]
    ]
    if insufficient_latency_samples:
        alerts.append(
            _alert(
                category="LATENCY",
                code="LATENCY_SAMPLE_INSUFFICIENT",
                severity="CRITICAL",
                subjects=insufficient_latency_samples,
                evidence_digest=latency["current"]["evidence_digest"],
            )
        )
        trigger_codes.add("SCORE_DRIFT")
    if (
        latency["current"]["p95_milliseconds"]
        > latency["baseline"]["p95_milliseconds"]
    ):
        alerts.append(
            _alert(
                category="LATENCY",
                code="LATENCY_P95_REGRESSION",
                severity="WARNING",
                subjects=["P95_MILLISECONDS"],
                evidence_digest=latency["current"]["evidence_digest"],
            )
        )
        trigger_codes.add("SCORE_DRIFT")

    if (
        observation["critical_incident_count"] > 0
        or scorecard["critical_incident_count"] > 0
    ):
        alerts.append(
            _alert(
                category="INCIDENT",
                code="INCIDENT_OBSERVED",
                severity="CRITICAL",
                subjects=["CRITICAL_INCIDENT"],
                evidence_digest=observation_digest,
                action_code="INVESTIGATE",
            )
        )
        trigger_codes.add("INCIDENT")

    declared_triggers = set(
        eval_profile["freshness_policy"]["retest_triggers"]
    )
    missing_triggers = sorted(
        trigger_codes.difference(declared_triggers),
        key=lambda value: value.encode("ascii"),
    )
    if missing_triggers:
        alerts.append(
            _alert(
                category="POLICY_GAP",
                code="PROFILE_RETEST_TRIGGER_GAP",
                severity="CRITICAL",
                subjects=missing_triggers,
                evidence_digest=profile_digest,
            )
        )

    alerts.sort(key=_alert_sort_key)
    effective_eligible = (
        scorecard["promotion_eligible"]
        and freshness_state == "FRESH"
        and not alerts
    )
    if mode == "MONITOR_ONLY":
        promotion_status = "NOT_EVALUATED"
    else:
        promotion_status = "PASS" if effective_eligible else "BLOCKED"
    report: Dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "report_uid": report_uid,
        "mode": mode,
        "skill_version_uid": observation["skill_version_uid"],
        "scorecard_ref": {
            "scorecard_uid": scorecard["scorecard_uid"],
            "artifact_digest": scorecard_digest,
        },
        "eval_profile_ref": {
            "eval_profile_uid": eval_profile["eval_profile_uid"],
            "artifact_digest": profile_digest,
        },
        "observation_ref": {
            "artifact_digest": observation_digest,
        },
        "promotion_decision_ref": (
            {"decision_digest": promotion_decision_digest}
            if promotion_decision_digest is not None
            else None
        ),
        "generated_at": observation["observed_at"],
        "freshness": {
            "state": freshness_state,
            "evaluated_at": scorecard["evaluated_at"],
            "deadline_at": deadline_at.strftime(UTC_Z_FORMAT),
            "freshness_valid_until": valid_until,
            "age_microseconds": age_microseconds,
            "max_age_days": max_age_days,
        },
        "alerts": alerts,
        "retest_trigger_codes": sorted(
            trigger_codes,
            key=lambda value: value.encode("ascii"),
        ),
        "missing_profile_trigger_codes": missing_triggers,
        "promotion_gate": {
            "status": promotion_status,
            "scorecard_effective_promotion_eligible": effective_eligible,
            "stale_score_independent_promotion_permitted": False,
            "re_evaluation_required": bool(alerts),
        },
        "actor": "SKILLOPS_FRESHNESS_DRIFT_MONITOR",
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
        "FRESHNESS_DRIFT_REPORT_INVALID",
    )
    return report


def validate_freshness_drift_report(
    bundle: ContractBundle,
    *,
    eval_profile: Mapping[str, Any],
    scorecard: Mapping[str, Any],
    observation: Mapping[str, Any],
    report: Mapping[str, Any],
    expected_bundle_digest: str,
) -> None:
    """Require the supplied report to equal the deterministic recomputation."""

    if not isinstance(report, dict):
        _fail("FRESHNESS_DRIFT_REPORT_ROOT_INVALID")
    _validate_artifact(
        bundle,
        report,
        REPORT_SCHEMA_ID,
        expected_bundle_digest,
        "FRESHNESS_DRIFT_REPORT_INVALID",
    )
    decision_ref = report["promotion_decision_ref"]
    expected = evaluate_freshness_drift(
        bundle,
        eval_profile=eval_profile,
        scorecard=scorecard,
        observation=observation,
        report_uid=report["report_uid"],
        mode=report["mode"],
        promotion_decision_digest=(
            decision_ref["decision_digest"]
            if decision_ref is not None
            else None
        ),
        expected_bundle_digest=expected_bundle_digest,
    )
    if canonicalize_object(report) != canonicalize_object(expected):
        _fail("FRESHNESS_DRIFT_REPORT_RECOMPUTATION_MISMATCH")


def append_monitored_promotion_decision(
    bundle: ContractBundle,
    registry_view: PromotionRegistryView,
    *,
    eval_profiles_by_digest: Mapping[str, Mapping[str, Any]],
    observations_by_digest: Mapping[str, Mapping[str, Any]],
    reports_by_digest: Mapping[str, Mapping[str, Any]],
    evidence_by_digest: Mapping[str, Mapping[str, Any]],
    scorecards_by_digest: Mapping[str, Mapping[str, Any]],
    eval_runs_by_digest: Mapping[str, Mapping[str, Any]],
    existing_decisions: Sequence[Mapping[str, Any]],
    decision: Mapping[str, Any],
    expected_predecessor_ledger_digest: str,
    expected_bundle_digest: str,
) -> MonitoredPromotionAppendResult:
    """Delegate to M-056 only after exact report closure passes."""

    if not isinstance(decision, dict):
        _fail("FRESHNESS_DRIFT_DECISION_ROOT_INVALID")
    _validate_artifact(
        bundle,
        decision,
        PROMOTION_DECISION_SCHEMA_ID,
        expected_bundle_digest,
        "FRESHNESS_DRIFT_DECISION_INVALID",
    )
    evidences = _artifact_map(
        evidence_by_digest,
        "evidence_bundle_digest",
        "FRESHNESS_DRIFT_PROMOTION_EVIDENCE",
    )
    scorecards = _artifact_map(
        scorecards_by_digest,
        "scorecard_digest",
        "FRESHNESS_DRIFT_SCORECARD",
    )
    # EvalProfile v1 has no self-digest field.  The caller map is normalized
    # separately so a field cannot be confused with a schema property.
    profiles: Dict[str, Mapping[str, Any]] = {}
    if not isinstance(eval_profiles_by_digest, dict):
        _fail("FRESHNESS_DRIFT_EVAL_PROFILE_MAP_INVALID")
    for digest, profile in eval_profiles_by_digest.items():
        if (
            not isinstance(digest, str)
            or SHA256_RE.fullmatch(digest) is None
            or not isinstance(profile, dict)
            or canonical_digest(profile) != digest
        ):
            _fail("FRESHNESS_DRIFT_EVAL_PROFILE_MAP_ENTRY_INVALID")
        profiles[digest] = profile
    observations = _artifact_map(
        observations_by_digest,
        "evidence_bundle_digest",
        "FRESHNESS_DRIFT_OBSERVATION",
    )
    reports = _artifact_map(
        reports_by_digest,
        "evidence_bundle_digest",
        "FRESHNESS_DRIFT_REPORT",
    )

    report_digests = []
    canonical_reports = []
    if decision.get("action") == "PROMOTE":
        evidence = evidences.get(
            decision.get("evidence_bundle_digest")
        )
        if not isinstance(evidence, dict):
            _fail("FRESHNESS_DRIFT_PROMOTION_EVIDENCE_MISSING")
        _validate_artifact(
            bundle,
            evidence,
            PROMOTION_EVIDENCE_SCHEMA_ID,
            expected_bundle_digest,
            "FRESHNESS_DRIFT_PROMOTION_EVIDENCE_INVALID",
        )
        referenced_scorecards = {
            ref["artifact_digest"]
            for ref in evidence.get("scorecard_refs", [])
            if isinstance(ref, dict)
        }
        if referenced_scorecards != set(scorecards):
            _fail("FRESHNESS_DRIFT_SCORECARD_REFERENCE_SET_MISMATCH")
        reports_by_scorecard: Dict[str, Mapping[str, Any]] = {}
        for report in reports.values():
            scorecard_digest = report["scorecard_ref"]["artifact_digest"]
            if scorecard_digest in reports_by_scorecard:
                _fail("FRESHNESS_DRIFT_REPORT_SCORECARD_DUPLICATE")
            reports_by_scorecard[scorecard_digest] = report
        if set(reports_by_scorecard) != referenced_scorecards:
            _fail("FRESHNESS_DRIFT_REPORT_SCORECARD_CLOSURE_MISMATCH")

        used_profiles = set()
        used_observations = set()
        for scorecard_digest in sorted(referenced_scorecards):
            scorecard = scorecards[scorecard_digest]
            report = reports_by_scorecard[scorecard_digest]
            profile_digest = scorecard["eval_profile_digest"]
            profile = profiles.get(profile_digest)
            observation_digest = report["observation_ref"][
                "artifact_digest"
            ]
            observation = observations.get(observation_digest)
            if profile is None or observation is None:
                _fail("FRESHNESS_DRIFT_MONITOR_REFERENCE_MISSING")
            validate_freshness_drift_report(
                bundle,
                eval_profile=profile,
                scorecard=scorecard,
                observation=observation,
                report=report,
                expected_bundle_digest=expected_bundle_digest,
            )
            decision_ref = report["promotion_decision_ref"]
            if (
                report["mode"] != "PROMOTION_GATE"
                or decision_ref is None
                or decision_ref["decision_digest"]
                != decision.get("decision_digest")
                or report["skill_version_uid"]
                != decision.get("candidate_skill_version_uid")
                or _timestamp(
                    report["generated_at"],
                    "FRESHNESS_DRIFT_REPORT_TIME_INVALID",
                )
                > _timestamp(
                    decision.get("decided_at"),
                    "FRESHNESS_DRIFT_DECISION_TIME_INVALID",
                )
                or report["promotion_gate"]["status"] != "PASS"
                or report["promotion_gate"][
                    "scorecard_effective_promotion_eligible"
                ]
                is not True
                or report["promotion_gate"][
                    "stale_score_independent_promotion_permitted"
                ]
                is not False
            ):
                _fail("FRESHNESS_DRIFT_PROMOTION_GATE_BLOCKED")
            used_profiles.add(profile_digest)
            used_observations.add(observation_digest)
            report_digests.append(report["evidence_bundle_digest"])
            canonical_reports.append(canonicalize_object(report))
        if set(profiles) != used_profiles or set(observations) != used_observations:
            _fail("FRESHNESS_DRIFT_UNUSED_MONITOR_ARTIFACT_FORBIDDEN")
    elif decision.get("action") == "REJECT":
        if profiles or observations or reports:
            _fail("FRESHNESS_DRIFT_REJECT_MONITOR_ARTIFACT_FORBIDDEN")
    else:
        _fail("FRESHNESS_DRIFT_PROMOTE_OR_REJECT_REQUIRED")

    try:
        promotion_result = append_promotion_decision(
            bundle,
            registry_view,
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
    except PromotionControllerError as exc:
        raise FreshnessDriftError(
            "FRESHNESS_DRIFT_M056_DELEGATION_FAILED:" + str(exc)
        ) from exc

    report_digests_tuple = tuple(report_digests)
    authorization_digest = canonical_digest(
        {
            "bundle_digest": expected_bundle_digest,
            "decision_digest": promotion_result.decision_digest,
            "domain": AUTHORIZATION_DIGEST_DOMAIN,
            "predecessor_ledger_digest": (
                promotion_result.predecessor_ledger_digest
            ),
            "protocol_revision": PROTOCOL_REVISION,
            "evidence_digests": list(report_digests_tuple),
        }
    )
    return MonitoredPromotionAppendResult(
        promotion_result=promotion_result,
        canonical_report_bytes=tuple(canonical_reports),
        report_digests=report_digests_tuple,
        authorization_digest=authorization_digest,
    )
