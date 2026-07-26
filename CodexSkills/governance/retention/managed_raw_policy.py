"""Pure M-061 managed-raw clock, action-plan, and receipt policy.

The policy consumes only candidates already selected by the M-060 protected
root guard.  It validates the exact private ``raw-segment:v2`` marker, applies
UTC elapsed-time stages, emits public-safe observation/plan evidence, and
validates an externally produced ``retention-receipt:v3``.  It never reads a
physical path, creates a receipt, or mutates a segment.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import re
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.retention.root_lifecycle import (
    RAW_SEGMENT_SCHEMA_ID,
    REPORT_SCHEMA_ID as ROOT_REPORT_SCHEMA_ID,
    RootLifecycleError,
    raw_ownership_marker,
    validate_selection_report,
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
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
OBSERVATION_SCHEMA_ID = (
    SCHEMA_PREFIX + "managed-raw-clock-observation:v1"
)
PLAN_SCHEMA_ID = SCHEMA_PREFIX + "managed-raw-retention-plan:v1"
RETENTION_RECEIPT_SCHEMA_ID = SCHEMA_PREFIX + "retention-receipt:v3"
RETENTION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
)
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
PLAN_SELF_POINTER = "/evidence_bundle_digest"

MAX_AGE_HOURS = 72
MAX_AGE_SECONDS = MAX_AGE_HOURS * 60 * 60
MAX_AGE_MICROSECONDS = MAX_AGE_SECONDS * 1_000_000
STAGE_THRESHOLDS = (
    ("PROJECT_IMMEDIATELY", 0),
    ("WARNING_24H", 24 * 60 * 60 * 1_000_000),
    ("CRITICAL_48H", 48 * 60 * 60 * 1_000_000),
    ("EMERGENCY_CATCH_UP_60H", 60 * 60 * 60 * 1_000_000),
    ("HARD_EXPIRY_72H", MAX_AGE_MICROSECONDS),
)
KEEP_DECISION = "KEEP"
EXPIRE_DECISION = "EXPIRE"
UTC_Z_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:"
    r"[0-5][0-9]\.[0-9]{6}Z$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

BASE_EXPIRE_ACTION_ORDER = (
    "REPROJECT_PUBLIC_SAFE",
    "RECORD_RAW_EXPIRED_GAP_IF_REPROJECTION_FAILED",
    "DELETE_OWNED_SEGMENT",
    "EMIT_RETENTION_RECEIPT",
)
BREACH_EXPIRE_ACTION_ORDER = (
    "RECORD_OFFLINE_TTL_BREACH",
) + BASE_EXPIRE_ACTION_ORDER


class ManagedRawPolicyError(ValueError):
    """The M-061 clock, evidence, or receipt contract failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclasses.dataclass(frozen=True)
class ManagedRawPolicyResult:
    """Canonical public-safe observation and action-plan bytes."""

    canonical_observation_bytes: bytes
    observation_digest: str
    canonical_plan_bytes: bytes
    plan_digest: str
    keep_candidate_refs: Tuple[str, ...]
    expire_candidate_refs: Tuple[str, ...]


def _fail(code: str) -> None:
    raise ManagedRawPolicyError(code)


def _strict_utc(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str) or UTC_Z_RE.fullmatch(value) is None:
        _fail(code)
    try:
        parsed = dt.datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
    except ValueError as exc:
        raise ManagedRawPolicyError(code) from exc
    return parsed.replace(tzinfo=dt.timezone.utc)


def _elapsed_microseconds(delta: dt.timedelta) -> int:
    return (
        (delta.days * 86400 + delta.seconds) * 1_000_000
        + delta.microseconds
    )


def _stage_for_elapsed(elapsed_microseconds: int) -> str:
    stage = STAGE_THRESHOLDS[0][0]
    for candidate, threshold in STAGE_THRESHOLDS:
        if elapsed_microseconds < threshold:
            break
        stage = candidate
    return stage


def build_managed_raw_policy_contract(
    m060_bundle: ContractBundle,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    plan_schema: Mapping[str, Any],
    expected_plan_schema_digest: str,
) -> ContractBundle:
    """Add exact bundle-external M-061 observation and plan schemas."""

    schemas = dict(m060_bundle.schemas)
    pointers = dict(m060_bundle.self_digest_pointers)
    additions = (
        (
            OBSERVATION_SCHEMA_ID,
            observation_schema,
            expected_observation_schema_digest,
            OBSERVATION_SELF_POINTER,
        ),
        (
            PLAN_SCHEMA_ID,
            plan_schema,
            expected_plan_schema_digest,
            PLAN_SELF_POINTER,
        ),
    )
    for schema_id, document, expected_digest, pointer in additions:
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or not isinstance(expected_digest, str)
            or SHA256_RE.fullmatch(expected_digest) is None
            or canonical_digest(document) != expected_digest
        ):
            _fail("MANAGED_RAW_SCHEMA_TRUST_MISMATCH")
        if schema_id in schemas:
            _fail("MANAGED_RAW_SCHEMA_REBIND_FORBIDDEN")
        schemas[schema_id] = document
        pointers[schema_id] = pointer
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise ManagedRawPolicyError(
            "MANAGED_RAW_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=m060_bundle.policies,
        protocol_revision=m060_bundle.protocol_revision,
    )


def _validate_artifact(
    bundle: ContractBundle,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
    *,
    public: bool,
) -> None:
    try:
        validate_instance(
            bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            verify_digest=True,
            public=public,
        )
    except ContractError as exc:
        raise ManagedRawPolicyError(code + ":" + str(exc)) from exc


def _validate_metadata(
    bundle: ContractBundle,
    metadata: Mapping[str, Any],
    expected_bundle_digest: str,
) -> Tuple[dt.datetime, dt.datetime, dt.datetime]:
    if not isinstance(metadata, dict):
        _fail("MANAGED_RAW_METADATA_ROOT_INVALID")
    _validate_artifact(
        bundle,
        metadata,
        RAW_SEGMENT_SCHEMA_ID,
        expected_bundle_digest,
        "MANAGED_RAW_METADATA_CONTRACT_INVALID",
        public=False,
    )
    if (
        metadata.get("bundle_digest") != expected_bundle_digest
        or metadata.get("managed_owned") is not True
        or metadata.get("protected_or_legacy") is not False
    ):
        _fail("MANAGED_RAW_OWNERSHIP_CONTRACT_INVALID")
    if metadata.get("ownership_marker_digest") != raw_ownership_marker(
        metadata
    ):
        _fail("MANAGED_RAW_OWNERSHIP_MARKER_INVALID")
    if metadata.get("persistence_mode") != "TEST_ONLY":
        _fail("MANAGED_RAW_PRODUCTION_CERTIFICATION_NOT_GRANTED")
    created_at = _strict_utc(
        metadata.get("created_at"),
        "MANAGED_RAW_CREATED_AT_INVALID",
    )
    sealed_at = _strict_utc(
        metadata.get("sealed_at"),
        "MANAGED_RAW_SEALED_AT_INVALID",
    )
    expires_at = _strict_utc(
        metadata.get("expires_at"),
        "MANAGED_RAW_EXPIRES_AT_INVALID",
    )
    if not (created_at <= sealed_at <= expires_at):
        _fail("MANAGED_RAW_SEGMENT_TIME_ORDER_INVALID")
    if expires_at != created_at + dt.timedelta(hours=MAX_AGE_HOURS):
        _fail("MANAGED_RAW_EXPIRES_NOT_CREATED_PLUS_72H")
    return created_at, sealed_at, expires_at


def _candidate_observation(
    bundle: ContractBundle,
    candidate_ref: str,
    metadata: Mapping[str, Any],
    observed: dt.datetime,
    *,
    expected_bundle_digest: str,
    recovery_cycle: bool,
    last_runtime_available: Optional[dt.datetime],
) -> Mapping[str, Any]:
    created_at, sealed_at, expires_at = _validate_metadata(
        bundle,
        metadata,
        expected_bundle_digest,
    )
    if observed < created_at:
        _fail("MANAGED_RAW_OBSERVED_BEFORE_CREATED")
    elapsed = _elapsed_microseconds(observed - created_at)
    remaining = max(0, MAX_AGE_MICROSECONDS - elapsed)
    overdue = max(0, elapsed - MAX_AGE_MICROSECONDS)
    if overdue:
        if (
            not recovery_cycle
            or last_runtime_available is None
            or last_runtime_available > expires_at
        ):
            _fail("MANAGED_RAW_OVERDUE_REQUIRES_OFFLINE_GAP_EVIDENCE")
        ttl_breach = True
    else:
        ttl_breach = False
    return {
        "candidate_ref": candidate_ref,
        "created_at": metadata["created_at"],
        "sealed_at": metadata["sealed_at"],
        "expires_at": metadata["expires_at"],
        "persistence_mode": "TEST_ONLY",
        "byte_count": metadata["byte_count"],
        "elapsed_microseconds": elapsed,
        "remaining_microseconds": remaining,
        "overdue_microseconds": overdue,
        "metadata_contract_valid": True,
        "stage": _stage_for_elapsed(elapsed),
        "ttl_breach": ttl_breach,
    }


def _validate_observation_semantics(
    observation: Mapping[str, Any],
) -> None:
    observed = _strict_utc(
        observation["observed_at"],
        "MANAGED_RAW_OBSERVED_AT_INVALID",
    )
    recovery_cycle = observation["recovery_cycle"]
    last_value = observation["last_runtime_available_at"]
    if recovery_cycle:
        if last_value is None:
            _fail("MANAGED_RAW_RECOVERY_LAST_AVAILABLE_REQUIRED")
        last_runtime = _strict_utc(
            last_value,
            "MANAGED_RAW_LAST_AVAILABLE_INVALID",
        )
        if last_runtime >= observed:
            _fail("MANAGED_RAW_RECOVERY_INTERVAL_INVALID")
        offline_microseconds = _elapsed_microseconds(
            observed - last_runtime
        )
        offline_seconds = offline_microseconds // 1_000_000
        if offline_seconds <= 0:
            _fail("MANAGED_RAW_OFFLINE_DURATION_UNREPRESENTABLE")
    else:
        if last_value is not None:
            _fail("MANAGED_RAW_LAST_AVAILABLE_WITHOUT_RECOVERY")
        last_runtime = None
        offline_seconds = 0
    if observation["offline_duration_seconds"] != offline_seconds:
        _fail("MANAGED_RAW_OFFLINE_DURATION_MISMATCH")
    rows = observation["candidate_observations"]
    refs = [row["candidate_ref"] for row in rows]
    if refs != sorted(refs) or len(refs) != len(set(refs)):
        _fail("MANAGED_RAW_CANDIDATE_ORDER_OR_DUPLICATE")
    for row in rows:
        created = _strict_utc(
            row["created_at"],
            "MANAGED_RAW_CREATED_AT_INVALID",
        )
        sealed = _strict_utc(
            row["sealed_at"],
            "MANAGED_RAW_SEALED_AT_INVALID",
        )
        expires = _strict_utc(
            row["expires_at"],
            "MANAGED_RAW_EXPIRES_AT_INVALID",
        )
        if (
            not (created <= sealed <= expires)
            or expires != created + dt.timedelta(hours=MAX_AGE_HOURS)
            or observed < created
        ):
            _fail("MANAGED_RAW_OBSERVATION_TIME_CONTRACT_INVALID")
        elapsed = _elapsed_microseconds(observed - created)
        remaining = max(0, MAX_AGE_MICROSECONDS - elapsed)
        overdue = max(0, elapsed - MAX_AGE_MICROSECONDS)
        expected_breach = overdue > 0
        if expected_breach and (
            not recovery_cycle
            or last_runtime is None
            or last_runtime > expires
        ):
            _fail("MANAGED_RAW_OVERDUE_REQUIRES_OFFLINE_GAP_EVIDENCE")
        if (
            row["persistence_mode"] != "TEST_ONLY"
            or row["metadata_contract_valid"] is not True
            or row["elapsed_microseconds"] != elapsed
            or row["remaining_microseconds"] != remaining
            or row["overdue_microseconds"] != overdue
            or row["stage"] != _stage_for_elapsed(elapsed)
            or row["ttl_breach"] is not expected_breach
        ):
            _fail("MANAGED_RAW_OBSERVATION_RECOMPUTATION_MISMATCH")
    if (
        observation["input_count"] != len(rows)
        or observation["protected_candidate_count"] != 0
        or observation["legacy_candidate_count"] != 0
        or observation["public_queue_candidate_count"] != 0
        or observation["persistent_managed_raw_default_enabled"] is not False
        or observation["clock_basis"] != "UTC_WALL_CLOCK"
        or observation["ttl_enforcement_availability"]
        != "LOCAL_RUNTIME_AVAILABLE_ONLY"
        or observation["offline_period_hard_guarantee_claimed"] is not False
        or observation["time_evaluation_performed"] is not True
        or observation["destructive_action_performed"] is not False
    ):
        _fail("MANAGED_RAW_OBSERVATION_POLICY_MISMATCH")


def _validate_m060_scope_binding(
    bundle: ContractBundle,
    m060_observation: Mapping[str, Any],
    m060_report: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
    managed_observation: Optional[Mapping[str, Any]] = None,
) -> Tuple[str, ...]:
    try:
        validate_selection_report(
            bundle,
            m060_observation,
            m060_report,
            expected_bundle_digest=expected_bundle_digest,
        )
    except RootLifecycleError as exc:
        raise ManagedRawPolicyError(
            "MANAGED_RAW_M060_SELECTION_INVALID:" + str(exc)
        ) from exc
    if (
        m060_report.get("schema_version") != ROOT_REPORT_SCHEMA_ID
        or m060_report.get("scope_authorization")
        != "M061_TIME_EVALUATION_ONLY"
        or m060_report.get("protected_selected_count") != 0
        or m060_report.get("legacy_selected_count") != 0
        or m060_report.get("public_queue_selected_count") != 0
    ):
        _fail("MANAGED_RAW_M060_SCOPE_AUTHORIZATION_INVALID")
    selected_refs = tuple(m060_report["selected_candidate_refs"])
    if managed_observation is not None:
        observed_refs = tuple(
            row["candidate_ref"]
            for row in managed_observation["candidate_observations"]
        )
        if (
            managed_observation["m060_selection_report_ref"][
                "artifact_digest"
            ]
            != m060_report["evidence_bundle_digest"]
            or observed_refs != selected_refs
        ):
            _fail("MANAGED_RAW_M060_OBSERVATION_BINDING_MISMATCH")
    return selected_refs


def recompute_retention_plan(
    bundle: ContractBundle,
    observation: Mapping[str, Any],
    *,
    plan_uid: str,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Recompute a non-mutating action plan from a valid observation."""

    if not isinstance(observation, dict):
        _fail("MANAGED_RAW_OBSERVATION_ROOT_INVALID")
    _validate_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "MANAGED_RAW_OBSERVATION_INVALID",
        public=True,
    )
    _validate_observation_semantics(observation)
    actions = []
    keep_count = 0
    expire_count = 0
    breach_count = 0
    for row in observation["candidate_observations"]:
        expired = row["elapsed_microseconds"] >= MAX_AGE_MICROSECONDS
        if expired:
            decision = EXPIRE_DECISION
            expire_count += 1
            if row["ttl_breach"]:
                breach_count += 1
                action_order: Sequence[str] = (
                    BREACH_EXPIRE_ACTION_ORDER
                )
            else:
                action_order = BASE_EXPIRE_ACTION_ORDER
        else:
            decision = KEEP_DECISION
            keep_count += 1
            action_order = ()
        actions.append(
            {
                "candidate_ref": row["candidate_ref"],
                "stage": row["stage"],
                "decision": decision,
                "ttl_breach": row["ttl_breach"],
                "projection_required": expired,
                "offline_gap_receipt_required": row["ttl_breach"],
                "unpublished_gap_required_if_reprojection_fails": (
                    expired
                ),
                "execution_receipt_required": expired,
                "action_order": list(action_order),
                "delete_authority_granted": False,
                "destructive_action_performed": False,
            }
        )
    plan: Dict[str, Any] = {
        "schema_version": PLAN_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "plan_uid": plan_uid,
        "observation_ref": {
            "artifact_digest": observation["evidence_bundle_digest"],
        },
        "generated_at": observation["observed_at"],
        "clock_basis": "UTC_WALL_CLOCK",
        "max_age_seconds": MAX_AGE_SECONDS,
        "boundary_rule": "ELAPSED_LT_72H_KEEP_ELAPSED_GTE_72H_EXPIRE",
        "retention_policy_id": RETENTION_POLICY_ID,
        "retention_receipt_schema_id": RETENTION_RECEIPT_SCHEMA_ID,
        "actions": actions,
        "input_count": len(actions),
        "keep_count": keep_count,
        "expire_count": expire_count,
        "ttl_breach_count": breach_count,
        "protected_candidate_count": 0,
        "legacy_candidate_count": 0,
        "public_queue_candidate_count": 0,
        "real_execution_permitted": False,
        "receipt_emitted": False,
        "canonical_publication_permitted": False,
        "actor": "SKILLOPS_MANAGED_RAW_POLICY_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    plan["evidence_bundle_digest"] = canonical_digest(
        plan,
        PLAN_SELF_POINTER,
    )
    _validate_artifact(
        bundle,
        plan,
        PLAN_SCHEMA_ID,
        expected_bundle_digest,
        "MANAGED_RAW_PLAN_INVALID",
        public=True,
    )
    return plan


def validate_retention_plan(
    bundle: ContractBundle,
    observation: Mapping[str, Any],
    plan: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> None:
    """Reject a supplied plan unless it equals deterministic recomputation."""

    if not isinstance(plan, dict):
        _fail("MANAGED_RAW_PLAN_ROOT_INVALID")
    expected = recompute_retention_plan(
        bundle,
        observation,
        plan_uid=plan.get("plan_uid", ""),
        expected_bundle_digest=expected_bundle_digest,
    )
    if canonicalize_object(expected) != canonicalize_object(plan):
        _fail("MANAGED_RAW_PLAN_RECOMPUTATION_MISMATCH")


def evaluate_managed_raw_policy(
    bundle: ContractBundle,
    *,
    m060_observation: Mapping[str, Any],
    m060_report: Mapping[str, Any],
    metadata_by_candidate_ref: Mapping[str, Mapping[str, Any]],
    observation_uid: str,
    plan_uid: str,
    observed_at: str,
    expected_bundle_digest: str,
    recovery_cycle: bool = False,
    last_runtime_available_at: Optional[str] = None,
) -> ManagedRawPolicyResult:
    """Evaluate UTC stages without creating a receipt or mutating raw data."""

    selected_refs = _validate_m060_scope_binding(
        bundle,
        m060_observation,
        m060_report,
        expected_bundle_digest=expected_bundle_digest,
    )
    if (
        tuple(sorted(metadata_by_candidate_ref)) != selected_refs
        or len(metadata_by_candidate_ref) != len(selected_refs)
    ):
        _fail("MANAGED_RAW_METADATA_SELECTION_SET_MISMATCH")
    observed = _strict_utc(
        observed_at,
        "MANAGED_RAW_OBSERVED_AT_INVALID",
    )
    if recovery_cycle:
        if last_runtime_available_at is None:
            _fail("MANAGED_RAW_RECOVERY_LAST_AVAILABLE_REQUIRED")
        last_runtime = _strict_utc(
            last_runtime_available_at,
            "MANAGED_RAW_LAST_AVAILABLE_INVALID",
        )
        if last_runtime >= observed:
            _fail("MANAGED_RAW_RECOVERY_INTERVAL_INVALID")
        offline_microseconds = _elapsed_microseconds(
            observed - last_runtime
        )
        offline_seconds = offline_microseconds // 1_000_000
        if offline_seconds <= 0:
            _fail("MANAGED_RAW_OFFLINE_DURATION_UNREPRESENTABLE")
    else:
        if last_runtime_available_at is not None:
            _fail("MANAGED_RAW_LAST_AVAILABLE_WITHOUT_RECOVERY")
        last_runtime = None
        offline_seconds = 0

    rows = [
        _candidate_observation(
            bundle,
            candidate_ref,
            metadata_by_candidate_ref[candidate_ref],
            observed,
            expected_bundle_digest=expected_bundle_digest,
            recovery_cycle=recovery_cycle,
            last_runtime_available=last_runtime,
        )
        for candidate_ref in selected_refs
    ]

    observation: Dict[str, Any] = {
        "schema_version": OBSERVATION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "observation_uid": observation_uid,
        "m060_selection_report_ref": {
            "artifact_digest": m060_report["evidence_bundle_digest"],
        },
        "observed_at": observed_at,
        "clock_basis": "UTC_WALL_CLOCK",
        "recovery_cycle": recovery_cycle,
        "last_runtime_available_at": last_runtime_available_at,
        "offline_duration_seconds": offline_seconds,
        "ttl_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
        "offline_period_hard_guarantee_claimed": False,
        "persistent_managed_raw_default_enabled": False,
        "candidate_observations": rows,
        "input_count": len(rows),
        "protected_candidate_count": 0,
        "legacy_candidate_count": 0,
        "public_queue_candidate_count": 0,
        "time_evaluation_performed": True,
        "destructive_action_performed": False,
        "actor": "SKILLOPS_MANAGED_RAW_POLICY_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    observation["evidence_bundle_digest"] = canonical_digest(
        observation,
        OBSERVATION_SELF_POINTER,
    )
    _validate_artifact(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "MANAGED_RAW_OBSERVATION_INVALID",
        public=True,
    )
    _validate_observation_semantics(observation)
    plan = recompute_retention_plan(
        bundle,
        observation,
        plan_uid=plan_uid,
        expected_bundle_digest=expected_bundle_digest,
    )
    keep_refs = tuple(
        row["candidate_ref"]
        for row in plan["actions"]
        if row["decision"] == KEEP_DECISION
    )
    expire_refs = tuple(
        row["candidate_ref"]
        for row in plan["actions"]
        if row["decision"] == EXPIRE_DECISION
    )
    return ManagedRawPolicyResult(
        canonical_observation_bytes=canonicalize_object(observation),
        observation_digest=observation["evidence_bundle_digest"],
        canonical_plan_bytes=canonicalize_object(plan),
        plan_digest=plan["evidence_bundle_digest"],
        keep_candidate_refs=keep_refs,
        expire_candidate_refs=expire_refs,
    )


def receipt_evidence(
    observation: Mapping[str, Any],
    plan: Mapping[str, Any],
    candidate_ref: str,
) -> Mapping[str, Any]:
    """Return the exact public-safe evidence material bound by a receipt."""

    observed_rows = {
        row["candidate_ref"]: row
        for row in observation["candidate_observations"]
    }
    planned_rows = {
        row["candidate_ref"]: row for row in plan["actions"]
    }
    observed = observed_rows.get(candidate_ref)
    planned = planned_rows.get(candidate_ref)
    if observed is None or planned is None:
        _fail("MANAGED_RAW_RECEIPT_CANDIDATE_UNKNOWN")
    return {
        "domain": "SKILLOPS_MANAGED_RAW_RETENTION_RECEIPT_EVIDENCE_V1",
        "candidate_ref": candidate_ref,
        "observation_ref": {
            "artifact_digest": observation["evidence_bundle_digest"],
        },
        "plan_ref": {
            "artifact_digest": plan["evidence_bundle_digest"],
        },
        "expires_at": observed["expires_at"],
        "selected_bytes": observed["byte_count"],
        "decision": planned["decision"],
        "ttl_breach": planned["ttl_breach"],
    }


def validate_execution_receipt(
    bundle: ContractBundle,
    m060_observation: Mapping[str, Any],
    m060_report: Mapping[str, Any],
    observation: Mapping[str, Any],
    plan: Mapping[str, Any],
    candidate_ref: str,
    receipt: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> None:
    """Validate one externally executed expiry receipt against the plan."""

    _validate_m060_scope_binding(
        bundle,
        m060_observation,
        m060_report,
        expected_bundle_digest=expected_bundle_digest,
        managed_observation=observation,
    )
    validate_retention_plan(
        bundle,
        observation,
        plan,
        expected_bundle_digest=expected_bundle_digest,
    )
    if not isinstance(receipt, dict):
        _fail("MANAGED_RAW_RECEIPT_ROOT_INVALID")
    _validate_artifact(
        bundle,
        receipt,
        RETENTION_RECEIPT_SCHEMA_ID,
        expected_bundle_digest,
        "MANAGED_RAW_RECEIPT_INVALID",
        public=True,
    )
    observed_rows = {
        row["candidate_ref"]: row
        for row in observation["candidate_observations"]
    }
    planned_rows = {
        row["candidate_ref"]: row for row in plan["actions"]
    }
    observed = observed_rows.get(candidate_ref)
    planned = planned_rows.get(candidate_ref)
    if observed is None or planned is None:
        _fail("MANAGED_RAW_RECEIPT_CANDIDATE_UNKNOWN")
    if planned["decision"] != EXPIRE_DECISION:
        _fail("MANAGED_RAW_KEEP_RECEIPT_FORBIDDEN")
    policy = bundle.policies.get(RETENTION_POLICY_ID)
    if not isinstance(policy, dict):
        _fail("MANAGED_RAW_RETENTION_POLICY_MISSING")
    expected_evidence_digest = canonical_digest(
        receipt_evidence(
            observation,
            plan,
            candidate_ref,
        )
    )
    selected_bytes = observed["byte_count"]
    if (
        receipt["scope"] != "MANAGED_RAW"
        or receipt["retention_policy_id"] != RETENTION_POLICY_ID
        or receipt["policy_snapshot_digest"] != canonical_digest(policy)
        or receipt["executed_at"] != observation["observed_at"]
        or receipt["cutoff_at"] != observed["expires_at"]
        or receipt["selected_count"] != 1
        or receipt["selected_bytes"] != selected_bytes
        or receipt["affected_count"] != 1
        or receipt["affected_bytes"] != selected_bytes
        or receipt["protected_candidate_count"] != 0
        or receipt["legacy_candidate_count"] != 0
        or receipt["history_rewrite_performed"] is not False
        or receipt["hard_delete_claimed"] is not False
        or receipt["evidence_digest"] != expected_evidence_digest
    ):
        _fail("MANAGED_RAW_RECEIPT_PLAN_BINDING_MISMATCH")
    if planned["ttl_breach"]:
        if (
            receipt["action"] != "OFFLINE_TTL_BREACH_CLEANUP"
            or receipt.get("gap_code") != "OFFLINE_TTL_BREACH"
            or receipt["ttl_breach"] is not True
            or receipt["offline_duration_seconds"]
            != observation["offline_duration_seconds"]
            or receipt["reprojection_status"]
            not in {"SUCCEEDED", "FAILED_GAP_RECORDED"}
        ):
            _fail("MANAGED_RAW_BREACH_RECEIPT_INVALID")
    else:
        if (
            receipt["action"] != "DELETE_OWNED_SEGMENT"
            or receipt["ttl_breach"] is not False
            or receipt["offline_duration_seconds"] != 0
        ):
            _fail("MANAGED_RAW_EXPIRY_RECEIPT_INVALID")
        reprojection = receipt["reprojection_status"]
        gap_code = receipt.get("gap_code")
        if (
            reprojection == "SUCCEEDED"
            and gap_code is not None
        ) or (
            reprojection == "FAILED_GAP_RECORDED"
            and gap_code != "RAW_EXPIRED_UNPUBLISHED"
        ) or reprojection not in {
            "SUCCEEDED",
            "FAILED_GAP_RECORDED",
        }:
            _fail("MANAGED_RAW_EXPIRY_REPROJECTION_EVIDENCE_INVALID")
