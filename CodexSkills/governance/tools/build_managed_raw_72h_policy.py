#!/usr/bin/env python3
"""Build/check non-active Mechanism M-061 managed-raw policy evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.retention.managed_raw_policy import (  # noqa: E402
    BASE_EXPIRE_ACTION_ORDER,
    BREACH_EXPIRE_ACTION_ORDER,
    MAX_AGE_SECONDS,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    PLAN_SCHEMA_ID,
    PLAN_SELF_POINTER,
    PROTOCOL_REVISION,
    RETENTION_POLICY_ID,
    RETENTION_RECEIPT_SCHEMA_ID,
    STAGE_THRESHOLDS,
    build_managed_raw_policy_contract,
)
from CodexSkills.governance.retention.root_lifecycle import (  # noqa: E402
    OBSERVATION_SCHEMA_ID as M060_OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER as M060_OBSERVATION_SELF_POINTER,
    RAW_SEGMENT_SCHEMA_ID,
    REPORT_SCHEMA_ID as M060_REPORT_SCHEMA_ID,
    REPORT_SELF_POINTER as M060_REPORT_SELF_POINTER,
    build_root_lifecycle_contract,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RETENTION_DIR = GOVERNANCE_DIR / "retention"
SCHEMA_DIR = RETENTION_DIR / "schemas"
COMPONENT_PATH = RETENTION_DIR / "managed_raw_policy.py"
OUTPUT_PATH = RETENTION_DIR / "managed-raw-72h-readiness.json"
OBSERVATION_SCHEMA_PATH = (
    SCHEMA_DIR / "managed-raw-clock-observation.schema.json"
)
PLAN_SCHEMA_PATH = (
    SCHEMA_DIR / "managed-raw-retention-plan.schema.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "managed-raw-72h-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:managed-raw-72h-readiness:v1"
)
NEXT_PHASE = "MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE"

CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

M060_GIT_OBJECT = (
    "sha1:21235d49fca818b74677172711cfe279d2da68a6"
)
M060_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "protected-local-managed-raw-readiness.json"
)
M060_READINESS_RAW_SHA256 = (
    "6376e6776b6f23cf45080f5d3a9191fcdf0238168032b14356da8b88dd45bef4"
)
M060_READINESS_SELF_DIGEST = (
    "b7c1ba479d0a47b97cb00b0556b2bf5db5b035bc156c9ae4e3bdc71337707080"
)
M060_COMPONENT_PATH = (
    "CodexSkills/governance/retention/root_lifecycle.py"
)
M060_COMPONENT_RAW_SHA256 = (
    "0b2436b889c7ff386f0468c2bfb7012159706784c830daa0ef1c19df4c663bf2"
)
M060_OBSERVATION_SCHEMA_PATH = (
    "CodexSkills/governance/retention/schemas/"
    "root-lifecycle-observation.schema.json"
)
M060_OBSERVATION_SCHEMA_RAW_SHA256 = (
    "4fc70bca0530e2a584ad6261bc413397725221aca24c110decc7ec67c0c0a135"
)
M060_OBSERVATION_SCHEMA_SHA256 = (
    "333c91ababd47048e809dd18b5589efabda7c44cc53a9827cc576be0d14959ca"
)
M060_REPORT_SCHEMA_PATH = (
    "CodexSkills/governance/retention/schemas/"
    "root-lifecycle-selection-report.schema.json"
)
M060_REPORT_SCHEMA_RAW_SHA256 = (
    "1a5b19cf291de745bcf09c894652cf178fcf86887316b06ef2ff1644961434e7"
)
M060_REPORT_SCHEMA_SHA256 = (
    "45120d6472a3fd2bb2206fa6047cba53e0918beb6cd80acf139efa693e68081b"
)

RAW_SEGMENT_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/private/raw-segment.schema.json"
)
RAW_SEGMENT_SCHEMA_RAW_SHA256 = (
    "238f3861bafd257c3ed0a5525383b357a17c65ef68049d8fbc519045982c584f"
)
RAW_SEGMENT_SCHEMA_SHA256 = (
    "032bdfb38c704a031e6c6f9c2f84dfbc82c9cc13af89e01723d8f439dff47dd5"
)
RETENTION_RECEIPT_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/public-v2/"
    "retention-receipt-v3.schema.json"
)
RETENTION_RECEIPT_SCHEMA_RAW_SHA256 = (
    "ddb464fe6a381580af486df25a85c4750b1743289cb631732f77d36944c8b215"
)
RETENTION_RECEIPT_SCHEMA_SHA256 = (
    "81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45"
)
RETENTION_POLICY_SHA256 = (
    "bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce"
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class ManagedRawPolicyBuildError(ValueError):
    """M-061 material cannot be reproduced without weakening a gate."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _load_bytes(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise ManagedRawPolicyBuildError(code) from exc
    if not isinstance(value, dict):
        raise ManagedRawPolicyBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise ManagedRawPolicyBuildError("M061_GIT_OBJECT_INVALID")
    _, object_id = tagged_object.split(":", 1)
    try:
        process = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "show",
                object_id + ":" + relative_path,
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=20,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ManagedRawPolicyBuildError(
            "M061_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise ManagedRawPolicyBuildError(
            "M061_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _ref(name: str) -> Dict[str, str]:
    return {"$ref": REF + name}


def _nullable_utc() -> Mapping[str, Any]:
    return {
        "anyOf": [
            {"type": "null"},
            _ref("utc_z_timestamp"),
        ]
    }


def build_observation_schema() -> Mapping[str, Any]:
    candidate_properties = {
        "candidate_ref": {
            "pattern": "^[a-z][a-z0-9-]{2,63}$",
            "type": "string",
        },
        "created_at": _ref("utc_z_timestamp"),
        "sealed_at": _ref("utc_z_timestamp"),
        "expires_at": _ref("utc_z_timestamp"),
        "persistence_mode": {"const": "TEST_ONLY"},
        "byte_count": _ref("nonnegative_count"),
        "elapsed_microseconds": _ref("nonnegative_count"),
        "remaining_microseconds": _ref("nonnegative_count"),
        "overdue_microseconds": _ref("nonnegative_count"),
        "metadata_contract_valid": {"const": True},
        "stage": {
            "enum": [row[0] for row in STAGE_THRESHOLDS],
        },
        "ttl_breach": {"type": "boolean"},
    }
    properties = {
        "schema_version": {"const": OBSERVATION_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "observation_uid": _ref("typed_uid"),
        "m060_selection_report_ref": {
            "additionalProperties": False,
            "properties": {
                "artifact_digest": _ref("sha256"),
            },
            "required": ["artifact_digest"],
            "type": "object",
        },
        "observed_at": _ref("utc_z_timestamp"),
        "clock_basis": {"const": "UTC_WALL_CLOCK"},
        "recovery_cycle": {"type": "boolean"},
        "last_runtime_available_at": _nullable_utc(),
        "offline_duration_seconds": _ref("nonnegative_count"),
        "ttl_enforcement_availability": {
            "const": "LOCAL_RUNTIME_AVAILABLE_ONLY"
        },
        "offline_period_hard_guarantee_claimed": {"const": False},
        "persistent_managed_raw_default_enabled": {"const": False},
        "candidate_observations": {
            "items": {
                "additionalProperties": False,
                "properties": candidate_properties,
                "required": list(candidate_properties),
                "type": "object",
            },
            "type": "array",
            "uniqueItems": True,
        },
        "input_count": _ref("nonnegative_count"),
        "protected_candidate_count": {"const": 0},
        "legacy_candidate_count": {"const": 0},
        "public_queue_candidate_count": {"const": 0},
        "time_evaluation_performed": {"const": True},
        "destructive_action_performed": {"const": False},
        "actor": {"const": "SKILLOPS_MANAGED_RAW_POLICY_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "M-061 managed raw UTC clock observation",
        "type": "object",
    }


def build_plan_schema() -> Mapping[str, Any]:
    action_codes = sorted(
        set(BASE_EXPIRE_ACTION_ORDER).union(
            BREACH_EXPIRE_ACTION_ORDER
        )
    )
    action_properties = {
        "candidate_ref": {
            "pattern": "^[a-z][a-z0-9-]{2,63}$",
            "type": "string",
        },
        "stage": {
            "enum": [row[0] for row in STAGE_THRESHOLDS],
        },
        "decision": {"enum": ["EXPIRE", "KEEP"]},
        "ttl_breach": {"type": "boolean"},
        "projection_required": {"type": "boolean"},
        "offline_gap_receipt_required": {"type": "boolean"},
        "unpublished_gap_required_if_reprojection_fails": {
            "type": "boolean"
        },
        "execution_receipt_required": {"type": "boolean"},
        "action_order": {
            "items": {"enum": action_codes},
            "maxItems": len(BREACH_EXPIRE_ACTION_ORDER),
            "type": "array",
            "uniqueItems": True,
        },
        "delete_authority_granted": {"const": False},
        "destructive_action_performed": {"const": False},
    }
    properties = {
        "schema_version": {"const": PLAN_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "plan_uid": _ref("typed_uid"),
        "observation_ref": {
            "additionalProperties": False,
            "properties": {
                "artifact_digest": _ref("sha256"),
            },
            "required": ["artifact_digest"],
            "type": "object",
        },
        "generated_at": _ref("utc_z_timestamp"),
        "clock_basis": {"const": "UTC_WALL_CLOCK"},
        "max_age_seconds": {"const": MAX_AGE_SECONDS},
        "boundary_rule": {
            "const": "ELAPSED_LT_72H_KEEP_ELAPSED_GTE_72H_EXPIRE"
        },
        "retention_policy_id": {"const": RETENTION_POLICY_ID},
        "retention_receipt_schema_id": {
            "const": RETENTION_RECEIPT_SCHEMA_ID
        },
        "actions": {
            "items": {
                "additionalProperties": False,
                "properties": action_properties,
                "required": list(action_properties),
                "type": "object",
            },
            "type": "array",
            "uniqueItems": True,
        },
        "input_count": _ref("nonnegative_count"),
        "keep_count": _ref("nonnegative_count"),
        "expire_count": _ref("nonnegative_count"),
        "ttl_breach_count": _ref("nonnegative_count"),
        "protected_candidate_count": {"const": 0},
        "legacy_candidate_count": {"const": 0},
        "public_queue_candidate_count": {"const": 0},
        "real_execution_permitted": {"const": False},
        "receipt_emitted": {"const": False},
        "canonical_publication_permitted": {"const": False},
        "actor": {"const": "SKILLOPS_MANAGED_RAW_POLICY_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": PLAN_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "M-061 managed raw non-mutating retention plan",
        "type": "object",
    }


def _descriptor(
    *,
    schema_id: str,
    path: str,
    raw_digest: str,
    canonical_digest_value: str,
    self_pointer: Optional[str],
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "artifact_digest": raw_digest,
        "schema_sha256": canonical_digest_value,
        "self_digest_pointer": self_pointer,
    }


def _trusted_candidate() -> ContractBundle:
    raw = _git_blob(CANDIDATE_GIT_OBJECT, CANDIDATE_MANIFEST_PATH)
    if _sha256(raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise ManagedRawPolicyBuildError(
            "M061_CANDIDATE_MANIFEST_RAW_MISMATCH"
        )
    return load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            verified_git_object_id=CANDIDATE_GIT_OBJECT,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            canonical_manifest_path=CANDIDATE_MANIFEST_PATH,
            mode="CANDIDATE",
        ),
    )


def _trusted_document(
    object_id: str,
    path: str,
    raw_digest: str,
    canonical_digest_value: str,
    expected_id: str,
    code: str,
) -> Mapping[str, Any]:
    raw = _git_blob(object_id, path)
    value = _load_bytes(raw, code + "_JSON_INVALID")
    if (
        _sha256(raw) != raw_digest
        or canonical_digest(value) != canonical_digest_value
        or value.get("$id") != expected_id
    ):
        raise ManagedRawPolicyBuildError(code + "_TRUST_MISMATCH")
    return value


def _trusted_m060_bundle() -> ContractBundle:
    candidate = _trusted_candidate()
    raw_schema = _trusted_document(
        CANDIDATE_GIT_OBJECT,
        RAW_SEGMENT_SCHEMA_PATH,
        RAW_SEGMENT_SCHEMA_RAW_SHA256,
        RAW_SEGMENT_SCHEMA_SHA256,
        RAW_SEGMENT_SCHEMA_ID,
        "M061_RAW_SEGMENT_SCHEMA",
    )
    m060_observation = _trusted_document(
        M060_GIT_OBJECT,
        M060_OBSERVATION_SCHEMA_PATH,
        M060_OBSERVATION_SCHEMA_RAW_SHA256,
        M060_OBSERVATION_SCHEMA_SHA256,
        M060_OBSERVATION_SCHEMA_ID,
        "M061_M060_OBSERVATION_SCHEMA",
    )
    m060_report = _trusted_document(
        M060_GIT_OBJECT,
        M060_REPORT_SCHEMA_PATH,
        M060_REPORT_SCHEMA_RAW_SHA256,
        M060_REPORT_SCHEMA_SHA256,
        M060_REPORT_SCHEMA_ID,
        "M061_M060_REPORT_SCHEMA",
    )
    return build_root_lifecycle_contract(
        candidate,
        raw_schema,
        RAW_SEGMENT_SCHEMA_SHA256,
        m060_observation,
        M060_OBSERVATION_SCHEMA_SHA256,
        m060_report,
        M060_REPORT_SCHEMA_SHA256,
    )


def _validate_predecessor_and_candidate(
    bundle: ContractBundle,
) -> Mapping[str, Any]:
    readiness_raw = _git_blob(M060_GIT_OBJECT, M060_READINESS_PATH)
    readiness = _load_bytes(
        readiness_raw,
        "M061_M060_READINESS_JSON_INVALID",
    )
    component_raw = _git_blob(M060_GIT_OBJECT, M060_COMPONENT_PATH)
    if (
        _sha256(readiness_raw) != M060_READINESS_RAW_SHA256
        or readiness.get("artifact_digest")
        != M060_READINESS_SELF_DIGEST
        or canonical_digest(readiness, "/artifact_digest")
        != M060_READINESS_SELF_DIGEST
        or readiness.get("status")
        != "DRAFT_NON_ACTIVE_PROTECTED_LOCAL_MANAGED_RAW_BOUNDARY_READY"
        or readiness.get("next_phase")
        != "MECHANISM_MANAGED_RAW_72H_POLICY"
        or _sha256(component_raw) != M060_COMPONENT_RAW_SHA256
    ):
        raise ManagedRawPolicyBuildError(
            "M061_M060_PREDECESSOR_TRUST_MISMATCH"
        )
    current_pairs = (
        (REPO_ROOT / M060_READINESS_PATH, readiness_raw),
        (REPO_ROOT / M060_COMPONENT_PATH, component_raw),
        (
            REPO_ROOT / M060_OBSERVATION_SCHEMA_PATH,
            _git_blob(M060_GIT_OBJECT, M060_OBSERVATION_SCHEMA_PATH),
        ),
        (
            REPO_ROOT / M060_REPORT_SCHEMA_PATH,
            _git_blob(M060_GIT_OBJECT, M060_REPORT_SCHEMA_PATH),
        ),
    )
    if any(path.read_bytes() != expected for path, expected in current_pairs):
        raise ManagedRawPolicyBuildError(
            "M061_M060_WORKING_TREE_DRIFT"
        )
    policy = bundle.policies.get(RETENTION_POLICY_ID)
    receipt = bundle.schemas.get(RETENTION_RECEIPT_SCHEMA_ID)
    if (
        not isinstance(policy, dict)
        or canonical_digest(policy) != RETENTION_POLICY_SHA256
        or policy.get("clock_basis") != "UTC_WALL_CLOCK"
        or policy.get("managed_raw_max_hours") != 72
        or policy.get("persistent_managed_raw_default_enabled")
        is not False
        or policy.get("protected_root_delete_allowed") is not False
        or policy.get("ttl_enforcement_availability")
        != "LOCAL_RUNTIME_AVAILABLE_ONLY"
        or policy.get("offline_period_hard_guarantee_claimed")
        is not False
        or policy.get("offline_resume_first_cycle_receipt_required")
        is not True
        or policy.get("offline_gap_receipt_required") is not True
        or policy.get("offline_breach_code") != "OFFLINE_TTL_BREACH"
    ):
        raise ManagedRawPolicyBuildError(
            "M061_RETENTION_POLICY_CONTRACT_MISMATCH"
        )
    receipt_raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        RETENTION_RECEIPT_SCHEMA_PATH,
    )
    if (
        not isinstance(receipt, dict)
        or _sha256(receipt_raw) != RETENTION_RECEIPT_SCHEMA_RAW_SHA256
        or canonical_digest(receipt) != RETENTION_RECEIPT_SCHEMA_SHA256
        or receipt.get("$id") != RETENTION_RECEIPT_SCHEMA_ID
        or bundle.self_digest_pointers.get(
            RETENTION_RECEIPT_SCHEMA_ID
        )
        != "/receipt_digest"
    ):
        raise ManagedRawPolicyBuildError(
            "M061_RETENTION_RECEIPT_CONTRACT_MISMATCH"
        )
    if VERSION_PATH.exists():
        raise ManagedRawPolicyBuildError(
            "M061_ACTIVE_VERSION_FORBIDDEN"
        )
    return readiness


def build_readiness() -> Mapping[str, Any]:
    m060_bundle = _trusted_m060_bundle()
    m060_readiness = _validate_predecessor_and_candidate(m060_bundle)
    observation_schema = build_observation_schema()
    plan_schema = build_plan_schema()
    observation_schema_digest = canonical_digest(observation_schema)
    plan_schema_digest = canonical_digest(plan_schema)
    contract = build_managed_raw_policy_contract(
        m060_bundle,
        observation_schema,
        observation_schema_digest,
        plan_schema,
        plan_schema_digest,
    )
    component_digest = _sha256(COMPONENT_PATH.read_bytes())
    readiness: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": "DRAFT_NON_ACTIVE_MANAGED_RAW_72H_POLICY_READY",
        "owner_plane": "MECHANISM",
        "source_trust": {
            "candidate_bundle": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "canonical_path": CANDIDATE_MANIFEST_PATH,
                "artifact_digest": CANDIDATE_MANIFEST_RAW_SHA256,
                "expected_mode": "CANDIDATE",
                "schema_count": 31,
                "policy_count": 5,
            },
            "m060_predecessor": {
                "verified_git_object_id": M060_GIT_OBJECT,
                "readiness": {
                    "canonical_path": M060_READINESS_PATH,
                    "content_digest": M060_READINESS_RAW_SHA256,
                    "artifact_digest": M060_READINESS_SELF_DIGEST,
                },
                "component": {
                    "component_path": M060_COMPONENT_PATH,
                    "content_digest": M060_COMPONENT_RAW_SHA256,
                },
                "status": m060_readiness["status"],
                "done_gate": m060_readiness["task_contract"][
                    "done_gate"
                ],
            },
            "raw_segment_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": RAW_SEGMENT_SCHEMA_PATH,
                "artifact_digest": RAW_SEGMENT_SCHEMA_RAW_SHA256,
                "schema_version": RAW_SEGMENT_SCHEMA_ID,
                "schema_sha256": RAW_SEGMENT_SCHEMA_SHA256,
                "self_digest_pointer": "/segment_digest",
                "private_schema": True,
                "bundle_member": False,
            },
            "retention_policy": {
                "policy_id": RETENTION_POLICY_ID,
                "policy_sha256": RETENTION_POLICY_SHA256,
                "bundle_member": True,
            },
            "retention_receipt_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": RETENTION_RECEIPT_SCHEMA_PATH,
                "artifact_digest": RETENTION_RECEIPT_SCHEMA_RAW_SHA256,
                "schema_version": RETENTION_RECEIPT_SCHEMA_ID,
                "schema_sha256": RETENTION_RECEIPT_SCHEMA_SHA256,
                "self_digest_pointer": "/receipt_digest",
                "bundle_member": True,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "managed_raw_policy_contract": {
            "component_path": (
                "CodexSkills/governance/retention/"
                "managed_raw_policy.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": component_digest,
            "clock_basis": "UTC_WALL_CLOCK",
            "clock_anchor": "CREATED_AT_PLUS_72_ELAPSED_HOURS",
            "sealed_at_may_extend_ttl": False,
            "max_age_seconds": MAX_AGE_SECONDS,
            "stage_thresholds": [
                {
                    "stage": stage,
                    "elapsed_seconds": threshold // 1_000_000,
                }
                for stage, threshold in STAGE_THRESHOLDS
            ],
            "boundary_rule": (
                "ELAPSED_LT_72H_KEEP_ELAPSED_GTE_72H_EXPIRE"
            ),
            "keep_boundary_seconds": MAX_AGE_SECONDS - 1,
            "expire_boundary_seconds": MAX_AGE_SECONDS,
            "expiry_action_order": list(BASE_EXPIRE_ACTION_ORDER),
            "offline_breach_action_order": list(
                BREACH_EXPIRE_ACTION_ORDER
            ),
            "offline_overdue_requires_gap_evidence": True,
            "offline_breach_code": "OFFLINE_TTL_BREACH",
            "unpublished_gap_code": "RAW_EXPIRED_UNPUBLISHED",
            "receipt_evidence_domain": (
                "SKILLOPS_MANAGED_RAW_RETENTION_RECEIPT_EVIDENCE_V1"
            ),
            "receipt_schema_semantics_validated": True,
            "receipt_created_by_mechanism": False,
            "physical_path_consumed": False,
            "delete_authority_granted_by_plan": False,
            "persistent_managed_raw_default_enabled": False,
            "production_certification_status": "NOT_GRANTED",
            "auto_executor_integration_status": "NOT_BOUND",
            "real_execution_permitted": False,
            "observation_schema": _descriptor(
                schema_id=OBSERVATION_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "managed-raw-clock-observation.schema.json"
                ),
                raw_digest=_sha256(_render(observation_schema)),
                canonical_digest_value=observation_schema_digest,
                self_pointer=OBSERVATION_SELF_POINTER,
            ),
            "plan_schema": _descriptor(
                schema_id=PLAN_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "managed-raw-retention-plan.schema.json"
                ),
                raw_digest=_sha256(_render(plan_schema)),
                canonical_digest_value=plan_schema_digest,
                self_pointer=PLAN_SELF_POINTER,
            ),
        },
        "offline_contract": {
            "ttl_enforcement_availability": (
                "LOCAL_RUNTIME_AVAILABLE_ONLY"
            ),
            "offline_period_hard_guarantee_claimed": False,
            "first_recovery_cycle_receipt_required": True,
            "offline_gap_evidence_required_for_overdue": True,
            "offline_breach_code": "OFFLINE_TTL_BREACH",
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "retention_policy_unchanged": True,
            "retention_receipt_schema_unchanged": True,
            "state_write_permitted": False,
            "raw_segment_write_permitted": False,
            "raw_expiry_delete_permitted": False,
            "receipt_write_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-060"],
            "completed_task_ids": ["M-061"],
            "pending_task_ids": ["M-062"],
            "required_output": "SEGMENT_MARKERS_RECEIPTS_CLOCK_TESTS",
            "done_gate": (
                "71_59_59_KEEP_AND_72_00_00_EXPIRE"
            ),
        },
        "real_execution_permitted": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    scan_public_value(readiness, contract.policies)
    return readiness


def build_readiness_schema(
    readiness: Mapping[str, Any],
) -> Mapping[str, Any]:
    properties: Dict[str, Any] = {
        key: {"const": value}
        for key, value in readiness.items()
        if key != "artifact_digest"
    }
    properties["artifact_digest"] = _ref("sha256")
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(readiness),
        "title": "Mechanism M-061 managed raw 72-hour readiness",
        "type": "object",
    }


def _contract_with_readiness(
    base: ContractBundle,
    schema: Mapping[str, Any],
) -> ContractBundle:
    schemas = dict(base.schemas)
    pointers = dict(base.self_digest_pointers)
    if READINESS_SCHEMA_ID in schemas:
        raise ManagedRawPolicyBuildError(
            "M061_READINESS_SCHEMA_REBIND_FORBIDDEN"
        )
    schemas[READINESS_SCHEMA_ID] = schema
    pointers[READINESS_SCHEMA_ID] = "/artifact_digest"
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise ManagedRawPolicyBuildError(
            "M061_READINESS_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _documents() -> Mapping[Path, Mapping[str, Any]]:
    m060_bundle = _trusted_m060_bundle()
    _validate_predecessor_and_candidate(m060_bundle)
    observation_schema = build_observation_schema()
    plan_schema = build_plan_schema()
    contract = build_managed_raw_policy_contract(
        m060_bundle,
        observation_schema,
        canonical_digest(observation_schema),
        plan_schema,
        canonical_digest(plan_schema),
    )
    readiness = build_readiness()
    readiness_schema = build_readiness_schema(readiness)
    final_contract = _contract_with_readiness(
        contract,
        readiness_schema,
    )
    try:
        validate_instance(
            final_contract,
            readiness,
            READINESS_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
    except ContractError as exc:
        raise ManagedRawPolicyBuildError(
            "M061_READINESS_INVALID:" + str(exc)
        ) from exc
    return {
        OBSERVATION_SCHEMA_PATH: observation_schema,
        PLAN_SCHEMA_PATH: plan_schema,
        READINESS_SCHEMA_PATH: readiness_schema,
        OUTPUT_PATH: readiness,
    }


def _write() -> None:
    documents = _documents()
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for path, value in documents.items():
        path.write_bytes(_render(value))


def _check() -> None:
    documents = _documents()
    for path, expected in documents.items():
        if not path.exists() or path.read_bytes() != _render(expected):
            raise ManagedRawPolicyBuildError(
                "M061_ARTIFACT_NOT_BYTE_EQUIVALENT:" + str(
                    path.relative_to(REPO_ROOT)
                )
            )


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--write", action="store_true")
    group.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    if args.write:
        _write()
    else:
        _check()
    print(
        "MANAGED_RAW_72H_POLICY_OK "
        "keep_boundary=71:59:59 expire_boundary=72:00:00 "
        "persistent_default=false real_execution=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (
        ContractError,
        ManagedRawPolicyBuildError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
