"""Deterministic SkillOps revision, impact, precedence, and Handoff gates.

This module defines Mechanism semantics only.  It never writes VERSION, state,
Git, notifications, or public artifacts.  A separately authorized executor
must persist the returned revision ledger atomically and must still satisfy the
activation settlement contract.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import re
from dataclasses import dataclass
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
)


PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
REVISION_LEDGER_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:revision-allocation-ledger:v1"
)
RELEASE_HANDOFF_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:release-handoff:v1"
)
FOUNDATION_INTERFACE_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:release-foundation-interface:v1"
)
VERSION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
)
VERSION_POLICY_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:version-policy:v2"
)
BOOTSTRAP_SRV = "v0.0.0.2"

SRV_RE = re.compile(r"^v0\.0\.0\.([1-9][0-9]*)$")
GIT_OBJECT_RE = re.compile(
    r"^(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
TYPED_UID_RE = re.compile(
    r"^[a-z][a-z0-9]{1,11}_[0-7][0-9A-HJKMNP-TV-Z]{25}$"
)
ENUM_CODE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
PHASE_RE = re.compile(r"^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$")
SOURCE_REF_RE = re.compile(r"^[A-Z][A-Z0-9_.:-]{0,95}$")
POLICY_FIELD_PATH_RE = re.compile(
    r"^/[a-z][a-z0-9_-]*(?:/[a-z][a-z0-9_-]*)*$"
)
UTC_Z_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])"
    r"T(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]\.[0-9]{6}Z$"
)

IMPACT_TRANSLATION = {
    "ROUTINE": "PATCH",
    "MATERIAL": "MINOR",
    "MAJOR": "MAJOR",
}
ROUTINE_TRIGGER_CODES = frozenset(
    {
        "DERIVED_VIEW_REBUILD",
        "NON_BEHAVIORAL_DOCUMENTATION",
    }
)
MATERIAL_TRIGGER_CODES = frozenset(
    {
        "COMPATIBLE_SCHEMA_ADDITION",
        "DATASET_EXTENSION",
        "EVALUATOR_EXTENSION",
    }
)
LOCKED_MAJOR_TRIGGER_CODES = frozenset(
    {
        "ACTIVE_BUNDLE_CHANGE",
        "AUTOMATIC_SIDE_EFFECT_CHANGE",
        "CHAMPION_TRANSITION",
        "EVALUATOR_OR_HOLDOUT_CHANGE",
        "HARD_GATE_CHANGE",
        "MIGRATION_OR_DELETE_SEMANTICS_CHANGE",
        "MODEL_PROVIDER_CHANGE",
        "NETWORK_OR_PERMISSION_CHANGE",
        "NOTIFICATION_POLICY_CHANGE",
        "PRIVACY_POLICY_CHANGE",
        "RETENTION_POLICY_CHANGE",
        "SCHEMA_BREAKING_CHANGE",
        "SOURCE_LAYOUT_CHANGE",
    }
)
KNOWN_TRIGGER_CODES = (
    ROUTINE_TRIGGER_CODES
    | MATERIAL_TRIGGER_CODES
    | LOCKED_MAJOR_TRIGGER_CODES
)

POLICY_PRECEDENCE = {
    "OWNER_LOCK": 1,
    "VALIDATED_CONFIG": 2,
    "NUMBERED_SPEC": 3,
    "TASK_ACCEPTANCE": 4,
    "EXAMPLE_OR_PDF": 5,
}
REQUIRED_RELEASE_GATES = (
    "BASELINE",
    "NOTIFICATION",
    "PATH",
    "PRIVACY",
    "REMOTE_HEAD",
    "ROLLBACK",
    "TESTS",
)
MAJOR_POLICY_FIELD_TOKENS = (
    "champion",
    "delete",
    "evaluator",
    "hard_gate",
    "holdout",
    "major_trigger",
    "migration",
    "network",
    "notification",
    "permission",
    "privacy",
    "retention",
    "schema",
    "side_effect",
    "source_layout",
)


class ReleaseContractError(ValueError):
    """A release-governance invariant failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class ImpactDecision:
    canonical_level: str
    taskpack_level: str
    trigger_codes: Tuple[str, ...]
    policy_coverage_complete: bool
    missing_policy_major_trigger_codes: Tuple[str, ...]


@dataclass(frozen=True)
class PolicyClaim:
    field_path: str
    source_class: str
    source_ref: str
    value: Any


def _strict_keys(
    value: Mapping[str, Any],
    expected: Iterable[str],
    code: str,
) -> None:
    if not isinstance(value, dict) or set(value) != set(expected):
        raise ReleaseContractError(code)


def _strict_utc(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str) or not UTC_Z_RE.fullmatch(value):
        raise ReleaseContractError(code)
    try:
        parsed = dt.datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
    except ValueError as exc:
        raise ReleaseContractError(code) from exc
    return parsed.replace(tzinfo=dt.timezone.utc)


def _safe_code(value: Any, code: str) -> str:
    if (
        not isinstance(value, str)
        or len(value) > 96
        or not ENUM_CODE_RE.fullmatch(value)
    ):
        raise ReleaseContractError(code)
    return value


def _safe_ref(value: Any, code: str) -> str:
    if not isinstance(value, str) or not SOURCE_REF_RE.fullmatch(value):
        raise ReleaseContractError(code)
    return value


def _self_digest(value: Mapping[str, Any], pointer: str) -> str:
    return canonical_digest(value, pointer)


def _with_digest(value: Mapping[str, Any], field: str) -> Dict[str, Any]:
    result = copy.deepcopy(dict(value))
    result[field] = "0" * 64
    result[field] = _self_digest(result, "/" + field)
    return result


def parse_srv(value: Any) -> int:
    """Parse the non-SemVer global SkillOps Revision Version."""

    if not isinstance(value, str):
        raise ReleaseContractError("SRV_TYPE_INVALID")
    match = SRV_RE.fullmatch(value)
    if not match:
        raise ReleaseContractError("SRV_FORMAT_INVALID")
    return int(match.group(1))


def format_srv(counter: int) -> str:
    if not isinstance(counter, int) or isinstance(counter, bool) or counter < 1:
        raise ReleaseContractError("SRV_COUNTER_INVALID")
    return "v0.0.0." + str(counter)


def compare_srv(left: str, right: str) -> int:
    left_value = parse_srv(left)
    right_value = parse_srv(right)
    return (left_value > right_value) - (left_value < right_value)


def increment_srv(value: str) -> str:
    return format_srv(parse_srv(value) + 1)


def validate_version_policy(
    policy: Mapping[str, Any],
) -> Tuple[str, ...]:
    """Validate the frozen v2 core and return uncovered locked MAJOR codes."""

    if (
        not isinstance(policy, dict)
        or policy.get("policy_id") != VERSION_POLICY_ID
        or policy.get("schema_version") != VERSION_POLICY_SCHEMA_ID
        or policy.get("protocol_revision") != PROTOCOL_REVISION
        or policy.get("srv_pattern") != r"^v0\.0\.0\.[1-9][0-9]*$"
        or policy.get("srv_update_mode") != "GLOBAL_ATOMIC_INCREMENT"
        or policy.get("srv_reuse_allowed") is not False
        or policy.get("srv_last_component_bounded") is not False
        or policy.get("daily_transaction_uid_separate") is not True
        or policy.get("transaction_uid_kind") != "AUTO_TRANSACTION_UID"
        or policy.get("impact_levels") != ["PATCH", "MINOR", "MAJOR"]
    ):
        raise ReleaseContractError("VERSION_POLICY_CORE_MISMATCH")
    codes = policy.get("major_trigger_codes")
    if (
        not isinstance(codes, list)
        or any(not isinstance(code, str) for code in codes)
        or codes != sorted(set(codes))
    ):
        raise ReleaseContractError("VERSION_POLICY_MAJOR_TRIGGER_SET_INVALID")
    return tuple(sorted(LOCKED_MAJOR_TRIGGER_CODES.difference(codes)))


def classify_impact(
    trigger_codes: Sequence[str],
    version_policy: Mapping[str, Any],
) -> ImpactDecision:
    """Classify from the locked vocabulary; unknown change codes never soften."""

    if (
        not isinstance(trigger_codes, (list, tuple))
        or not trigger_codes
        or any(not isinstance(code, str) for code in trigger_codes)
    ):
        raise ReleaseContractError("IMPACT_TRIGGER_SET_INVALID")
    normalized = tuple(sorted(trigger_codes))
    if len(set(normalized)) != len(normalized):
        raise ReleaseContractError("IMPACT_TRIGGER_DUPLICATE")
    unknown = set(normalized).difference(KNOWN_TRIGGER_CODES)
    if unknown:
        raise ReleaseContractError("IMPACT_TRIGGER_UNKNOWN")
    missing = validate_version_policy(version_policy)
    canonical_level = _canonical_impact_for_triggers(normalized)
    taskpack_level = {
        "PATCH": "ROUTINE",
        "MINOR": "MATERIAL",
        "MAJOR": "MAJOR",
    }[canonical_level]
    return ImpactDecision(
        canonical_level,
        taskpack_level,
        normalized,
        not missing,
        missing,
    )


def assert_impact_policy_coverage(policy: Mapping[str, Any]) -> None:
    if validate_version_policy(policy):
        raise ReleaseContractError(
            "VERSION_POLICY_MAJOR_TRIGGER_COVERAGE_INCOMPLETE"
        )


def _canonical_impact_for_triggers(
    trigger_codes: Sequence[str],
) -> str:
    trigger_set = set(trigger_codes)
    if trigger_set.intersection(LOCKED_MAJOR_TRIGGER_CODES):
        return "MAJOR"
    if trigger_set.intersection(MATERIAL_TRIGGER_CODES):
        return "MINOR"
    return "PATCH"


def _claim_digest(value: Any) -> str:
    return hashlib.sha256(canonicalize_object(value)).hexdigest()


def _public_field_ref(field_path: str) -> str:
    return "_".join(
        part.replace("-", "_").upper()
        for part in field_path.strip("/").split("/")
    )


def detect_policy_conflicts(
    claims: Sequence[PolicyClaim],
) -> Tuple[Mapping[str, Any], ...]:
    """Return sanitized conflicts; never copy raw claim values into evidence."""

    if not isinstance(claims, (list, tuple)):
        raise ReleaseContractError("POLICY_CLAIMS_INVALID")
    grouped: Dict[str, list] = {}
    seen = set()
    for claim in claims:
        if not isinstance(claim, PolicyClaim):
            raise ReleaseContractError("POLICY_CLAIM_TYPE_INVALID")
        if (
            not isinstance(claim.field_path, str)
            or not POLICY_FIELD_PATH_RE.fullmatch(claim.field_path)
        ):
            raise ReleaseContractError("POLICY_CLAIM_FIELD_INVALID")
        if claim.source_class not in POLICY_PRECEDENCE:
            raise ReleaseContractError("POLICY_CLAIM_SOURCE_CLASS_INVALID")
        _safe_ref(claim.source_ref, "POLICY_CLAIM_SOURCE_REF_INVALID")
        identity = (
            claim.field_path,
            claim.source_class,
            claim.source_ref,
        )
        if identity in seen:
            raise ReleaseContractError("POLICY_CLAIM_DUPLICATE_SOURCE")
        seen.add(identity)
        grouped.setdefault(claim.field_path, []).append(
            {
                "source_class": claim.source_class,
                "source_ref": claim.source_ref,
                "value_digest": _claim_digest(claim.value),
            }
        )

    conflicts = []
    for field_path, rows in grouped.items():
        if len({row["value_digest"] for row in rows}) < 2:
            continue
        ordered = sorted(
            rows,
            key=lambda row: (
                POLICY_PRECEDENCE[row["source_class"]],
                row["source_ref"],
            ),
        )
        best_rank = POLICY_PRECEDENCE[ordered[0]["source_class"]]
        best = [
            row
            for row in ordered
            if POLICY_PRECEDENCE[row["source_class"]] == best_rank
        ]
        unique_best_values = {row["value_digest"] for row in best}
        unambiguous = len(unique_best_values) == 1
        lower = field_path.casefold()
        impact = (
            "MAJOR"
            if any(token in lower for token in MAJOR_POLICY_FIELD_TOKENS)
            else "MINOR"
        )
        conflicts.append(
            {
                "field_ref": _public_field_ref(field_path),
                "impact": impact,
                "authoritative_source_class": (
                    best[0]["source_class"] if unambiguous else None
                ),
                "authoritative_source_refs": sorted(
                    row["source_ref"] for row in best
                ),
                "claims": sorted(
                    (
                        {
                            "source_class": row["source_class"],
                            "source_ref": row["source_ref"],
                            "evidence_digest": row["value_digest"],
                        }
                        for row in rows
                    ),
                    key=lambda row: (
                        POLICY_PRECEDENCE[row["source_class"]],
                        row["source_ref"],
                    ),
                ),
                "resolution_code": (
                    "STOP_WRITE_RECONCILE_TO_HIGHER_PRECEDENCE"
                    if unambiguous
                    else "STOP_WRITE_OWNER_DISAMBIGUATION_REQUIRED"
                ),
                "srv_increment_required": True,
                "write_permitted": False,
            }
        )
    return tuple(sorted(conflicts, key=lambda row: row["field_ref"]))


def assert_no_policy_conflicts(claims: Sequence[PolicyClaim]) -> None:
    if detect_policy_conflicts(claims):
        raise ReleaseContractError("POLICY_PRECEDENCE_CONFLICT")


def new_revision_ledger(
    observed_current_srv: Optional[str],
) -> Mapping[str, Any]:
    if observed_current_srv is None:
        floor = BOOTSTRAP_SRV
        committed = None
        version_file_present = False
    else:
        if compare_srv(observed_current_srv, BOOTSTRAP_SRV) < 0:
            raise ReleaseContractError("SRV_ROLLBACK_DETECTED")
        floor = observed_current_srv
        committed = observed_current_srv
        version_file_present = True
    return _with_digest(
        {
            "schema_version": REVISION_LEDGER_SCHEMA_ID,
            "protocol_revision": PROTOCOL_REVISION,
            "bootstrap_srv": BOOTSTRAP_SRV,
            "version_file_present": version_file_present,
            "allocation_floor_srv": floor,
            "committed_srv": committed,
            "allocations": [],
        },
        "ledger_digest",
    )


def _validate_allocation_record(
    record: Mapping[str, Any],
) -> None:
    _strict_keys(
        record,
        {
            "transaction_uid",
            "target_srv",
            "expected_remote_head",
            "impact",
            "trigger_codes",
            "status",
            "reserved_at",
            "settled_at",
            "remote_readback_head",
            "abandon_reason_code",
        },
        "REVISION_ALLOCATION_SHAPE_INVALID",
    )
    if not TYPED_UID_RE.fullmatch(str(record["transaction_uid"])):
        raise ReleaseContractError("REVISION_TRANSACTION_UID_INVALID")
    parse_srv(record["target_srv"])
    if not GIT_OBJECT_RE.fullmatch(str(record["expected_remote_head"])):
        raise ReleaseContractError("REVISION_EXPECTED_HEAD_INVALID")
    if record["impact"] not in {"PATCH", "MINOR", "MAJOR"}:
        raise ReleaseContractError("REVISION_IMPACT_INVALID")
    codes = record["trigger_codes"]
    if (
        not isinstance(codes, list)
        or not codes
        or codes != sorted(set(codes))
        or any(code not in KNOWN_TRIGGER_CODES for code in codes)
    ):
        raise ReleaseContractError("REVISION_TRIGGER_CODES_INVALID")
    if record["impact"] != _canonical_impact_for_triggers(codes):
        raise ReleaseContractError("REVISION_IMPACT_TRIGGER_MISMATCH")
    reserved_at = _strict_utc(
        record["reserved_at"],
        "REVISION_RESERVED_AT_INVALID",
    )
    status = record["status"]
    if status == "RESERVED":
        if any(
            record[field] is not None
            for field in (
                "settled_at",
                "remote_readback_head",
                "abandon_reason_code",
            )
        ):
            raise ReleaseContractError("REVISION_RESERVED_STATE_INVALID")
    elif status == "SETTLED":
        settled_at = _strict_utc(
            record["settled_at"],
            "REVISION_SETTLED_AT_INVALID",
        )
        if (
            settled_at < reserved_at
            or not GIT_OBJECT_RE.fullmatch(
                str(record["remote_readback_head"])
            )
            or record["remote_readback_head"]
            == record["expected_remote_head"]
            or record["abandon_reason_code"] is not None
        ):
            raise ReleaseContractError("REVISION_SETTLED_STATE_INVALID")
    elif status == "ABANDONED":
        if (
            record["settled_at"] is not None
            or record["remote_readback_head"] is not None
        ):
            raise ReleaseContractError("REVISION_ABANDONED_STATE_INVALID")
        _safe_code(
            record["abandon_reason_code"],
            "REVISION_ABANDON_REASON_INVALID",
        )
    else:
        raise ReleaseContractError("REVISION_STATUS_INVALID")


def validate_revision_ledger(
    ledger: Mapping[str, Any],
) -> Mapping[str, Any]:
    _strict_keys(
        ledger,
        {
            "schema_version",
            "protocol_revision",
            "bootstrap_srv",
            "version_file_present",
            "allocation_floor_srv",
            "committed_srv",
            "allocations",
            "ledger_digest",
        },
        "REVISION_LEDGER_SHAPE_INVALID",
    )
    if (
        ledger["schema_version"] != REVISION_LEDGER_SCHEMA_ID
        or ledger["protocol_revision"] != PROTOCOL_REVISION
        or ledger["bootstrap_srv"] != BOOTSTRAP_SRV
        or not isinstance(ledger["version_file_present"], bool)
        or not SHA256_RE.fullmatch(str(ledger["ledger_digest"]))
    ):
        raise ReleaseContractError("REVISION_LEDGER_CONTEXT_INVALID")
    floor = parse_srv(ledger["allocation_floor_srv"])
    if floor < parse_srv(BOOTSTRAP_SRV):
        raise ReleaseContractError("REVISION_LEDGER_FLOOR_INVALID")
    committed_raw = ledger["committed_srv"]
    committed = parse_srv(committed_raw) if committed_raw is not None else None
    if (
        ledger["version_file_present"] is True
        and committed is None
    ) or (
        ledger["version_file_present"] is False
        and committed is not None
    ):
        raise ReleaseContractError("REVISION_LEDGER_VERSION_STATE_INVALID")
    allocations = ledger["allocations"]
    if not isinstance(allocations, list):
        raise ReleaseContractError("REVISION_ALLOCATIONS_INVALID")
    expected_target = floor + 1
    transaction_uids = set()
    settled_targets = []
    reserved_indexes = []
    for index, record in enumerate(allocations):
        if not isinstance(record, dict):
            raise ReleaseContractError("REVISION_ALLOCATION_SHAPE_INVALID")
        _validate_allocation_record(record)
        if parse_srv(record["target_srv"]) != expected_target:
            raise ReleaseContractError("REVISION_TARGET_SEQUENCE_INVALID")
        expected_target += 1
        if record["transaction_uid"] in transaction_uids:
            raise ReleaseContractError("REVISION_TRANSACTION_REUSED")
        transaction_uids.add(record["transaction_uid"])
        if record["status"] == "SETTLED":
            settled_targets.append(parse_srv(record["target_srv"]))
        elif record["status"] == "RESERVED":
            reserved_indexes.append(index)
    if len(reserved_indexes) > 1 or (
        reserved_indexes and reserved_indexes[0] != len(allocations) - 1
    ):
        raise ReleaseContractError("REVISION_SINGLE_FLIGHT_INVALID")
    expected_committed = (
        max(settled_targets)
        if settled_targets
        else (floor if ledger["version_file_present"] else None)
    )
    if committed != expected_committed:
        raise ReleaseContractError("REVISION_COMMITTED_SRV_INVALID")
    if ledger["ledger_digest"] != _self_digest(
        ledger,
        "/ledger_digest",
    ):
        raise ReleaseContractError("REVISION_LEDGER_DIGEST_MISMATCH")
    return ledger


def reserve_revision(
    ledger: Mapping[str, Any],
    *,
    transaction_uid: str,
    expected_remote_head: str,
    impact: str,
    trigger_codes: Sequence[str],
    reserved_at: str,
) -> Mapping[str, Any]:
    validate_revision_ledger(ledger)
    if not TYPED_UID_RE.fullmatch(transaction_uid):
        raise ReleaseContractError("REVISION_TRANSACTION_UID_INVALID")
    if not GIT_OBJECT_RE.fullmatch(expected_remote_head):
        raise ReleaseContractError("REVISION_EXPECTED_HEAD_INVALID")
    if any(
        row["transaction_uid"] == transaction_uid
        for row in ledger["allocations"]
    ):
        raise ReleaseContractError("REVISION_TRANSACTION_REUSED")
    if any(row["status"] == "RESERVED" for row in ledger["allocations"]):
        raise ReleaseContractError("REVISION_RESERVATION_ALREADY_OPEN")
    _strict_utc(reserved_at, "REVISION_RESERVED_AT_INVALID")
    decision_codes = tuple(sorted(trigger_codes))
    if impact not in {"PATCH", "MINOR", "MAJOR"}:
        raise ReleaseContractError("REVISION_IMPACT_INVALID")
    if (
        not decision_codes
        or len(set(decision_codes)) != len(decision_codes)
        or any(code not in KNOWN_TRIGGER_CODES for code in decision_codes)
    ):
        raise ReleaseContractError("REVISION_TRIGGER_CODES_INVALID")
    if impact != _canonical_impact_for_triggers(decision_codes):
        raise ReleaseContractError("REVISION_IMPACT_TRIGGER_MISMATCH")
    highest = parse_srv(ledger["allocation_floor_srv"])
    for row in ledger["allocations"]:
        highest = max(highest, parse_srv(row["target_srv"]))
    result = copy.deepcopy(dict(ledger))
    result["allocations"].append(
        {
            "transaction_uid": transaction_uid,
            "target_srv": format_srv(highest + 1),
            "expected_remote_head": expected_remote_head,
            "impact": impact,
            "trigger_codes": list(decision_codes),
            "status": "RESERVED",
            "reserved_at": reserved_at,
            "settled_at": None,
            "remote_readback_head": None,
            "abandon_reason_code": None,
        }
    )
    result["ledger_digest"] = "0" * 64
    result["ledger_digest"] = _self_digest(result, "/ledger_digest")
    return validate_revision_ledger(result)


def settle_revision(
    ledger: Mapping[str, Any],
    *,
    transaction_uid: str,
    version_payload: bytes,
    artifact_srv_revisions: Sequence[str],
    remote_readback_head: str,
    settled_at: str,
) -> Mapping[str, Any]:
    validate_revision_ledger(ledger)
    if not GIT_OBJECT_RE.fullmatch(remote_readback_head):
        raise ReleaseContractError("REVISION_REMOTE_READBACK_HEAD_INVALID")
    _strict_utc(settled_at, "REVISION_SETTLED_AT_INVALID")
    matches = [
        (index, row)
        for index, row in enumerate(ledger["allocations"])
        if row["transaction_uid"] == transaction_uid
    ]
    if len(matches) != 1 or matches[0][1]["status"] != "RESERVED":
        raise ReleaseContractError("REVISION_RESERVATION_NOT_OPEN")
    index, record = matches[0]
    target = record["target_srv"]
    if (
        not isinstance(version_payload, bytes)
        or version_payload != (target + "\n").encode("ascii")
    ):
        raise ReleaseContractError("REVISION_VERSION_PAYLOAD_MISMATCH")
    if (
        not isinstance(artifact_srv_revisions, (list, tuple))
        or not artifact_srv_revisions
        or any(value != target for value in artifact_srv_revisions)
    ):
        raise ReleaseContractError("REVISION_ARTIFACT_SRV_MISMATCH")
    if remote_readback_head == record["expected_remote_head"]:
        raise ReleaseContractError("REVISION_REMOTE_HEAD_NOT_ADVANCED")
    result = copy.deepcopy(dict(ledger))
    updated = result["allocations"][index]
    updated["status"] = "SETTLED"
    updated["settled_at"] = settled_at
    updated["remote_readback_head"] = remote_readback_head
    result["committed_srv"] = target
    result["version_file_present"] = True
    result["ledger_digest"] = "0" * 64
    result["ledger_digest"] = _self_digest(result, "/ledger_digest")
    return validate_revision_ledger(result)


def abandon_revision(
    ledger: Mapping[str, Any],
    *,
    transaction_uid: str,
    reason_code: str,
) -> Mapping[str, Any]:
    validate_revision_ledger(ledger)
    _safe_code(reason_code, "REVISION_ABANDON_REASON_INVALID")
    matches = [
        (index, row)
        for index, row in enumerate(ledger["allocations"])
        if row["transaction_uid"] == transaction_uid
    ]
    if len(matches) != 1 or matches[0][1]["status"] != "RESERVED":
        raise ReleaseContractError("REVISION_RESERVATION_NOT_OPEN")
    result = copy.deepcopy(dict(ledger))
    updated = result["allocations"][matches[0][0]]
    updated["status"] = "ABANDONED"
    updated["abandon_reason_code"] = reason_code
    result["ledger_digest"] = "0" * 64
    result["ledger_digest"] = _self_digest(result, "/ledger_digest")
    return validate_revision_ledger(result)


def build_release_handoff(
    *,
    status: str,
    phase: str,
    srv_revision: str,
    bundle_digest: str,
    expected_remote_head: str,
    impact: str,
    trigger_codes: Sequence[str],
    policy_conflict_count: int,
    version_policy_major_trigger_coverage_complete: bool,
    external_runtime_readiness: str,
    schedule_authority_resolved: bool,
    gates: Sequence[Mapping[str, Any]],
    residual_risk_codes: Sequence[str],
    next_phase: str,
    updated_at: str,
) -> Mapping[str, Any]:
    value = {
        "schema_version": RELEASE_HANDOFF_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": status,
        "phase": phase,
        "srv_revision": srv_revision,
        "bundle_digest": bundle_digest,
        "expected_remote_head": expected_remote_head,
        "impact": impact,
        "trigger_codes": list(trigger_codes),
        "policy_conflict_count": policy_conflict_count,
        "version_policy_major_trigger_coverage_complete": (
            version_policy_major_trigger_coverage_complete
        ),
        "external_runtime_readiness": external_runtime_readiness,
        "schedule_authority_resolved": schedule_authority_resolved,
        "gates": [dict(gate) for gate in gates],
        "residual_risk_codes": list(residual_risk_codes),
        "next_phase": next_phase,
        "activation_forbidden": status != "READY_FOR_ACTIVATION",
    }
    value["updated_at"] = updated_at
    value["artifact_digest"] = "0" * 64
    value["artifact_digest"] = _self_digest(value, "/artifact_digest")
    return validate_release_handoff(value)


def validate_release_handoff(
    handoff: Optional[Mapping[str, Any]],
    *,
    expected_srv_revision: Optional[str] = None,
    expected_bundle_digest: Optional[str] = None,
    expected_remote_head: Optional[str] = None,
) -> Mapping[str, Any]:
    if handoff is None:
        raise ReleaseContractError("RELEASE_HANDOFF_MISSING")
    _strict_keys(
        handoff,
        {
            "schema_version",
            "protocol_revision",
            "status",
            "phase",
            "srv_revision",
            "bundle_digest",
            "expected_remote_head",
            "impact",
            "trigger_codes",
            "policy_conflict_count",
            "version_policy_major_trigger_coverage_complete",
            "external_runtime_readiness",
            "schedule_authority_resolved",
            "gates",
            "residual_risk_codes",
            "next_phase",
            "activation_forbidden",
            "updated_at",
            "artifact_digest",
        },
        "RELEASE_HANDOFF_SHAPE_INVALID",
    )
    if (
        handoff["schema_version"] != RELEASE_HANDOFF_SCHEMA_ID
        or handoff["protocol_revision"] != PROTOCOL_REVISION
        or handoff["status"]
        not in {"DRAFT_NON_ACTIVE", "BLOCKED", "READY_FOR_ACTIVATION"}
        or handoff["impact"] not in {"PATCH", "MINOR", "MAJOR"}
        or not isinstance(handoff["policy_conflict_count"], int)
        or isinstance(handoff["policy_conflict_count"], bool)
        or handoff["policy_conflict_count"] < 0
        or not isinstance(
            handoff["version_policy_major_trigger_coverage_complete"],
            bool,
        )
        or handoff["external_runtime_readiness"]
        not in {"READY", "NOT_READY", "UNKNOWN"}
        or not isinstance(handoff["schedule_authority_resolved"], bool)
        or not isinstance(handoff["activation_forbidden"], bool)
        or not SHA256_RE.fullmatch(str(handoff["artifact_digest"]))
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_CONTEXT_INVALID")
    if (
        not PHASE_RE.fullmatch(str(handoff["phase"]))
        or len(str(handoff["phase"])) > 96
        or not PHASE_RE.fullmatch(str(handoff["next_phase"]))
        or len(str(handoff["next_phase"])) > 96
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_PHASE_INVALID")
    parse_srv(handoff["srv_revision"])
    if not SHA256_RE.fullmatch(str(handoff["bundle_digest"])):
        raise ReleaseContractError("RELEASE_HANDOFF_BUNDLE_INVALID")
    if not GIT_OBJECT_RE.fullmatch(str(handoff["expected_remote_head"])):
        raise ReleaseContractError("RELEASE_HANDOFF_EXPECTED_HEAD_INVALID")
    _strict_utc(handoff["updated_at"], "RELEASE_HANDOFF_TIME_INVALID")
    trigger_codes = handoff["trigger_codes"]
    risks = handoff["residual_risk_codes"]
    if (
        not isinstance(trigger_codes, list)
        or not trigger_codes
        or trigger_codes != sorted(set(trigger_codes))
        or any(code not in KNOWN_TRIGGER_CODES for code in trigger_codes)
        or not isinstance(risks, list)
        or risks != sorted(set(risks))
        or any(not ENUM_CODE_RE.fullmatch(str(code)) for code in risks)
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_CODES_INVALID")
    gates = handoff["gates"]
    if not isinstance(gates, list):
        raise ReleaseContractError("RELEASE_HANDOFF_GATES_INVALID")
    observed_gate_codes = []
    all_pass = True
    for gate in gates:
        _strict_keys(
            gate,
            {"gate_code", "status", "evidence_digest", "reason_code"},
            "RELEASE_HANDOFF_GATE_SHAPE_INVALID",
        )
        gate_code = _safe_code(
            gate["gate_code"],
            "RELEASE_HANDOFF_GATE_CODE_INVALID",
        )
        observed_gate_codes.append(gate_code)
        if gate["status"] == "PASS":
            if (
                not SHA256_RE.fullmatch(str(gate["evidence_digest"]))
                or gate["reason_code"] is not None
            ):
                raise ReleaseContractError(
                    "RELEASE_HANDOFF_PASS_EVIDENCE_INVALID"
                )
        elif gate["status"] in {"FAIL", "UNKNOWN"}:
            all_pass = False
            if gate["evidence_digest"] is not None:
                if not SHA256_RE.fullmatch(str(gate["evidence_digest"])):
                    raise ReleaseContractError(
                        "RELEASE_HANDOFF_FAILURE_EVIDENCE_INVALID"
                    )
            _safe_code(
                gate["reason_code"],
                "RELEASE_HANDOFF_GATE_REASON_INVALID",
            )
        else:
            raise ReleaseContractError("RELEASE_HANDOFF_GATE_STATUS_INVALID")
    if tuple(observed_gate_codes) != REQUIRED_RELEASE_GATES:
        raise ReleaseContractError("RELEASE_HANDOFF_GATE_SET_INVALID")
    ready = (
        all_pass
        and handoff["policy_conflict_count"] == 0
        and handoff["version_policy_major_trigger_coverage_complete"] is True
        and handoff["external_runtime_readiness"] == "READY"
        and handoff["schedule_authority_resolved"] is True
        and not risks
    )
    if (
        handoff["status"] == "READY_FOR_ACTIVATION"
    ) != ready or handoff["activation_forbidden"] == ready:
        raise ReleaseContractError("RELEASE_HANDOFF_READINESS_MISMATCH")
    if expected_srv_revision is not None and (
        handoff["srv_revision"] != expected_srv_revision
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_SRV_STALE")
    if expected_bundle_digest is not None and (
        handoff["bundle_digest"] != expected_bundle_digest
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_BUNDLE_STALE")
    if expected_remote_head is not None and (
        handoff["expected_remote_head"] != expected_remote_head
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_EXPECTED_HEAD_STALE")
    if handoff["artifact_digest"] != _self_digest(
        handoff,
        "/artifact_digest",
    ):
        raise ReleaseContractError("RELEASE_HANDOFF_DIGEST_MISMATCH")
    return handoff
