#!/usr/bin/env python3
"""Build/check non-active Mechanism M-060 lifecycle-boundary evidence."""

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

from CodexSkills.governance.retention.root_lifecycle import (  # noqa: E402
    ELIGIBLE_DECISION,
    EXCLUDED_DECISION,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    PROTECTED_ROOT_CLASSES,
    PROTOCOL_REVISION,
    RAW_SEGMENT_SCHEMA_ID,
    REPORT_SCHEMA_ID,
    REPORT_SELF_POINTER,
    ROOT_CLASS_LIFECYCLE,
    build_root_lifecycle_contract,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RETENTION_DIR = GOVERNANCE_DIR / "retention"
SCHEMA_DIR = RETENTION_DIR / "schemas"
ROOT_LIFECYCLE_PATH = RETENTION_DIR / "root_lifecycle.py"
OUTPUT_PATH = (
    RETENTION_DIR / "protected-local-managed-raw-readiness.json"
)
OBSERVATION_SCHEMA_PATH = (
    SCHEMA_DIR / "root-lifecycle-observation.schema.json"
)
REPORT_SCHEMA_PATH = (
    SCHEMA_DIR / "root-lifecycle-selection-report.schema.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "protected-local-managed-raw-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:protected-local-managed-raw-readiness:v1"
)
RETENTION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
)
PUBLIC_RUN_EVENT_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2"
)
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
RAW_SEGMENT_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/private/raw-segment.schema.json"
)
RAW_SEGMENT_SCHEMA_RAW_SHA256 = (
    "238f3861bafd257c3ed0a5525383b357a17c65ef68049d8fbc519045982c584f"
)
RAW_SEGMENT_SCHEMA_SHA256 = (
    "032bdfb38c704a031e6c6f9c2f84dfbc82c9cc13af89e01723d8f439dff47dd5"
)
RETENTION_POLICY_SHA256 = (
    "bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce"
)
PUBLIC_RUN_EVENT_SCHEMA_SHA256 = (
    "c2b494baf284ba53f6c0101e0ab29b228de68964e4ab823710bcc3461555e523"
)
NEXT_PHASE = "MECHANISM_MANAGED_RAW_72H_POLICY"

ROOT_CLASS_ROWS = (
    (
        "LEGACY_DATA",
        "PROTECTED_LOCAL_DATA",
        False,
        "READ_ONLY_NO_DELETE_MOVE_TRUNCATE",
    ),
    (
        "PUBLIC_QUEUE",
        "PUBLIC_SAFE_PUBLICATION_QUEUE",
        False,
        "RETAIN_UNTIL_REMOTE_VERIFIED",
    ),
    (
        "RUN_SOURCE",
        "PROTECTED_LOCAL_DATA",
        False,
        "READ_ONLY_NO_DELETE_MOVE_TRUNCATE",
    ),
    (
        "SKILL_SOURCE",
        "PROTECTED_LOCAL_DATA",
        False,
        "READ_ONLY_NO_DELETE_MOVE_TRUNCATE",
    ),
    (
        "STAGING",
        "MANAGED_RAW_SPOOL",
        True,
        "M061_TIME_EVALUATION_ONLY",
    ),
)
EXCLUSION_REASONS = (
    "PERSISTENCE_DISABLED",
    "PROTECTED_LOCAL_TTL_FORBIDDEN",
    "PUBLIC_SAFE_QUEUE_NOT_RAW_SPOOL",
    "TEST_ONLY_NOT_AUTHORIZED",
)
PUBLIC_RUN_FORBIDDEN_FIELD_NAMES = {
    "absolute_path",
    "command",
    "credential",
    "email",
    "output",
    "password",
    "phone_number",
    "prompt",
    "raw",
    "reasoning",
    "secret",
    "stderr",
    "stdout",
    "tool_arguments",
}


class ProtectedLocalRawBoundaryBuildError(ValueError):
    """M-060 material cannot be reproduced without weakening a gate."""


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
        raise ProtectedLocalRawBoundaryBuildError(code) from exc
    if not isinstance(value, dict):
        raise ProtectedLocalRawBoundaryBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_GIT_OBJECT_INVALID"
        )
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
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _schema_property_names(value: Any) -> set:
    names = set()
    if isinstance(value, dict):
        properties = value.get("properties")
        if isinstance(properties, dict):
            names.update(properties)
        for child in value.values():
            names.update(_schema_property_names(child))
    elif isinstance(value, list):
        for child in value:
            names.update(_schema_property_names(child))
    return names


def _ref(name: str) -> Dict[str, str]:
    return {
        "$ref": (
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:common-definitions:v1#/$defs/"
            + name
        )
    }


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required or properties),
        "type": "object",
    }


def build_observation_schema() -> Mapping[str, Any]:
    root_binding = _closed(
        {
            "root_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "root_class": {
                "enum": [row[0] for row in ROOT_CLASS_ROWS]
            },
            "lifecycle_class": {
                "enum": sorted(set(ROOT_CLASS_LIFECYCLE.values()))
            },
            "private_path_serialized": {"const": False},
            "ttl_selection_allowed": {"type": "boolean"},
            "lifecycle_action": {
                "enum": sorted({row[3] for row in ROOT_CLASS_ROWS})
            },
        }
    )
    evaluation = _closed(
        {
            "candidate_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "root_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "root_class": {
                "enum": [row[0] for row in ROOT_CLASS_ROWS]
            },
            "lifecycle_class": {
                "enum": sorted(set(ROOT_CLASS_LIFECYCLE.values()))
            },
            "decision": {
                "enum": [ELIGIBLE_DECISION, EXCLUDED_DECISION]
            },
            "reason_code": {
                "enum": [
                    ELIGIBLE_DECISION,
                    *EXCLUSION_REASONS,
                ]
            },
            "metadata_read": {"type": "boolean"},
            "raw_schema_valid": {"type": "boolean"},
            "ownership_marker_verified": {"type": "boolean"},
            "payload_integrity_verified": {"type": "boolean"},
        }
    )
    properties = {
        "schema_version": {"const": OBSERVATION_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "observation_uid": _ref("typed_uid"),
        "observed_at": _ref("utc_z_timestamp"),
        "root_bindings": {
            "items": root_binding,
            "minItems": 1,
            "type": "array",
            "uniqueItems": True,
        },
        "candidate_evaluations": {
            "items": evaluation,
            "type": "array",
        },
        "persistent_managed_raw_default_enabled": {"const": False},
        "ttl_enforcement_availability": {
            "const": "LOCAL_RUNTIME_AVAILABLE_ONLY"
        },
        "offline_period_hard_guarantee_claimed": {"const": False},
        "offline_resume_first_cycle_receipt_required": {"const": True},
        "offline_gap_receipt_required": {"const": True},
        "time_evaluation_performed": {"const": False},
        "destructive_action_performed": {"const": False},
        "actor": {"const": "SKILLOPS_ROOT_LIFECYCLE_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Protected-local and managed-raw lifecycle observation",
        "type": "object",
    }


def build_report_schema() -> Mapping[str, Any]:
    excluded = _closed(
        {
            "candidate_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "reason_code": {"enum": list(EXCLUSION_REASONS)},
        }
    )
    properties = {
        "schema_version": {"const": REPORT_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "report_uid": _ref("typed_uid"),
        "observation_ref": _closed(
            {"artifact_digest": _ref("sha256")}
        ),
        "selection_state": {"const": "PASS"},
        "scope_authorization": {
            "const": "M061_TIME_EVALUATION_ONLY"
        },
        "selected_candidate_refs": {
            "items": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "type": "array",
            "uniqueItems": True,
        },
        "excluded_candidates": {
            "items": excluded,
            "type": "array",
            "uniqueItems": True,
        },
        "root_count": _ref("positive_count"),
        "input_count": _ref("nonnegative_count"),
        "selected_count": _ref("nonnegative_count"),
        "protected_input_count": _ref("nonnegative_count"),
        "legacy_input_count": _ref("nonnegative_count"),
        "public_queue_input_count": _ref("nonnegative_count"),
        "protected_selected_count": {"const": 0},
        "legacy_selected_count": {"const": 0},
        "public_queue_selected_count": {"const": 0},
        "protected_delete_budget": {"const": 0},
        "time_evaluation_performed": {"const": False},
        "destructive_action_performed": {"const": False},
        "public_artifact_write_performed": {"const": False},
        "generated_at": _ref("utc_z_timestamp"),
        "actor": {"const": "SKILLOPS_ROOT_LIFECYCLE_GUARD"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": REPORT_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Protected-local and managed-raw selection report",
        "type": "object",
    }


def _schema_descriptor(
    *,
    path: str,
    schema_id: str,
    schema: Mapping[str, Any],
    pointer: str,
) -> Dict[str, Any]:
    return {
        "artifact_digest": _sha256(_render(schema)),
        "canonical_path": path,
        "schema_sha256": canonical_digest(schema),
        "schema_version": schema_id,
        "self_digest_pointer": pointer,
    }


def _trust_descriptor(
    *,
    artifact_digest: str,
    canonical_path: str,
    expected_mode: str,
    verified_git_object_id: str,
) -> Dict[str, Any]:
    return {
        "artifact_digest": artifact_digest,
        "canonical_path": canonical_path,
        "expected_mode": expected_mode,
        "verified_git_object_id": verified_git_object_id,
    }


def build_readiness_schema() -> Mapping[str, Any]:
    trust = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "expected_mode": _ref("enum_code"),
            "verified_git_object_id": _ref("git_object_id"),
        }
    )
    schema_descriptor = _closed(
        {
            "artifact_digest": _ref("sha256"),
            "canonical_path": _ref("repo_relative_posix_path"),
            "schema_sha256": _ref("sha256"),
            "schema_version": _ref("urn_id"),
            "self_digest_pointer": {
                "const": "/evidence_bundle_digest"
            },
        }
    )
    source_trust = _closed(
        {
            "candidate_bundle": _closed(
                {
                    **trust["properties"],
                    "bundle_digest": _ref("sha256"),
                    "schema_count": {"const": 31},
                    "policy_count": {"const": 5},
                }
            ),
            "raw_segment_schema": _closed(
                {
                    **trust["properties"],
                    "schema_version": {"const": RAW_SEGMENT_SCHEMA_ID},
                    "schema_sha256": _ref("sha256"),
                    "self_digest_pointer": {
                        "const": "/segment_digest"
                    },
                    "bundle_member": {"const": False},
                    "private_schema": {"const": True},
                }
            ),
            "retention_policy": _closed(
                {
                    "policy_id": {"const": RETENTION_POLICY_ID},
                    "policy_sha256": _ref("sha256"),
                    "bundle_member": {"const": True},
                }
            ),
            "public_run_event_schema": _closed(
                {
                    "schema_version": {
                        "const": PUBLIC_RUN_EVENT_SCHEMA_ID
                    },
                    "schema_sha256": _ref("sha256"),
                    "self_digest_pointer": {"const": "/event_digest"},
                    "bundle_member": {"const": True},
                }
            ),
            "repository_self_report_is_not_trust_root": {"const": True},
        }
    )
    m003 = _closed(
        {
            "lstat_first": {"const": True},
            "realpath_containment_required": {"const": True},
            "root_symlink_allowed": {"const": False},
            "candidate_symlink_allowed": {"const": False},
            "sibling_prefix_match_allowed": {"const": False},
            "root_overlap_allowed": {"const": False},
            "special_file_allowed": {"const": False},
            "private_root_path_serialized": {"const": False},
        }
    )
    m031 = _closed(
        {
            "public_run_event_schema_id": {
                "const": PUBLIC_RUN_EVENT_SCHEMA_ID
            },
            "private_raw_schema_id": {"const": RAW_SEGMENT_SCHEMA_ID},
            "public_queue_contains_raw": {"const": False},
            "raw_private_fields_structurally_impossible": {"const": True},
            "private_schema_bundle_member": {"const": False},
        }
    )
    lifecycle = _closed(
        {
            "component_path": {
                "const": (
                    "CodexSkills/governance/retention/"
                    "root_lifecycle.py"
                )
            },
            "component_source_binding_mode": {
                "const": "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            },
            "content_digest": _ref("sha256"),
            "root_class_mapping": {
                "const": [
                    {
                        "root_class": row[0],
                        "lifecycle_class": row[1],
                        "ttl_selection_allowed": row[2],
                        "lifecycle_action": row[3],
                    }
                    for row in ROOT_CLASS_ROWS
                ]
            },
            "protected_root_classes": {
                "const": list(PROTECTED_ROOT_CLASSES)
            },
            "managed_raw_root_class": {"const": "STAGING"},
            "public_queue_root_class": {"const": "PUBLIC_QUEUE"},
            "only_managed_raw_may_reach_m061": {"const": True},
            "protected_or_queue_selected_count": {"const": 0},
            "protected_delete_budget": {"const": 0},
            "raw_ownership_marker_recomputed": {"const": True},
            "raw_payload_digest_recomputed": {"const": True},
            "persistent_managed_raw_default_enabled": {"const": False},
            "production_certification_status": {
                "const": "PENDING_M061"
            },
            "time_evaluation_performed": {"const": False},
            "destructive_action_permitted": {"const": False},
            "observation_schema": schema_descriptor,
            "report_schema": schema_descriptor,
            "report_recomputation_required": {"const": True},
        }
    )
    offline = _closed(
        {
            "clock_basis": {"const": "UTC_WALL_CLOCK"},
            "ttl_enforcement_availability": {
                "const": "LOCAL_RUNTIME_AVAILABLE_ONLY"
            },
            "offline_period_hard_guarantee_claimed": {"const": False},
            "offline_resume_first_cycle_receipt_required": {"const": True},
            "offline_gap_receipt_required": {"const": True},
            "offline_breach_code": {"const": "OFFLINE_TTL_BREACH"},
        }
    )
    nonmutation = _closed(
        {
            "activation_forbidden": {"const": True},
            "auto_plane_unchanged": {"const": True},
            "candidate_bundle_unchanged": {"const": True},
            "canonical_publication_permitted": {"const": False},
            "state_write_permitted": {"const": False},
            "raw_expiry_action_permitted": {"const": False},
            "version_file_created": {"const": False},
        }
    )
    task = _closed(
        {
            "dependency_task_ids": {"const": ["M-003", "M-031"]},
            "completed_task_ids": {"const": ["M-060"]},
            "pending_task_ids": {"const": ["M-061"]},
            "required_output": {
                "const": "ROOT_TYPING_AND_LIFECYCLE_CONTRACT"
            },
            "done_gate": {
                "const": (
                    "LEGACY_LOCAL_SOURCE_NEVER_SELECTED_BY_72H_JOB"
                )
            },
        }
    )
    properties = {
        "artifact_digest": _ref("sha256"),
        "schema_version": {"const": READINESS_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "status": {
            "const": (
                "DRAFT_NON_ACTIVE_PROTECTED_LOCAL_MANAGED_RAW_"
                "BOUNDARY_READY"
            )
        },
        "owner_plane": {"const": "MECHANISM"},
        "digest_algorithm": {"const": "SHA-256"},
        "source_trust": source_trust,
        "m003_dependency_contract": m003,
        "m031_dependency_contract": m031,
        "root_lifecycle_contract": lifecycle,
        "offline_contract": offline,
        "real_execution_permitted": {"const": False},
        "nonmutation": nonmutation,
        "task_contract": task,
        "next_phase": {"const": NEXT_PHASE},
        "self_digest_pointer": {"const": "/artifact_digest"},
        "task_pack_revision": {"const": "v0.0.0.2"},
    }
    return {
        "$id": READINESS_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "Mechanism M-060 protected-local managed-raw readiness",
        "type": "object",
    }


def _trusted_candidate() -> ContractBundle:
    raw = _git_blob(CANDIDATE_GIT_OBJECT, CANDIDATE_MANIFEST_PATH)
    if _sha256(raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_CANDIDATE_MANIFEST_RAW_MISMATCH"
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


def _trusted_raw_schema() -> Mapping[str, Any]:
    raw = _git_blob(CANDIDATE_GIT_OBJECT, RAW_SEGMENT_SCHEMA_PATH)
    schema = _load_bytes(raw, "M060_RAW_SEGMENT_SCHEMA_JSON_INVALID")
    if (
        _sha256(raw) != RAW_SEGMENT_SCHEMA_RAW_SHA256
        or canonical_digest(schema) != RAW_SEGMENT_SCHEMA_SHA256
        or schema.get("$id") != RAW_SEGMENT_SCHEMA_ID
    ):
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_RAW_SEGMENT_SCHEMA_TRUST_MISMATCH"
        )
    return schema


def build_readiness() -> Mapping[str, Any]:
    candidate = _trusted_candidate()
    raw_schema = _trusted_raw_schema()
    observation_schema = build_observation_schema()
    report_schema = build_report_schema()
    contract = build_root_lifecycle_contract(
        candidate,
        raw_schema,
        RAW_SEGMENT_SCHEMA_SHA256,
        observation_schema,
        canonical_digest(observation_schema),
        report_schema,
        canonical_digest(report_schema),
    )
    retention_policy = candidate.policies.get(RETENTION_POLICY_ID)
    public_run_schema = candidate.schemas.get(PUBLIC_RUN_EVENT_SCHEMA_ID)
    if (
        not isinstance(retention_policy, dict)
        or canonical_digest(retention_policy) != RETENTION_POLICY_SHA256
        or retention_policy.get("managed_raw_max_hours") != 72
        or retention_policy.get(
            "persistent_managed_raw_default_enabled"
        )
        is not False
        or retention_policy.get("protected_root_delete_allowed") is not False
        or retention_policy.get("clock_basis") != "UTC_WALL_CLOCK"
        or retention_policy.get("ttl_enforcement_availability")
        != "LOCAL_RUNTIME_AVAILABLE_ONLY"
        or retention_policy.get("offline_period_hard_guarantee_claimed")
        is not False
        or retention_policy.get(
            "offline_resume_first_cycle_receipt_required"
        )
        is not True
        or retention_policy.get("offline_gap_receipt_required") is not True
        or retention_policy.get("offline_breach_code")
        != "OFFLINE_TTL_BREACH"
    ):
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_RETENTION_POLICY_CONTRACT_MISMATCH"
        )
    if (
        not isinstance(public_run_schema, dict)
        or canonical_digest(public_run_schema)
        != PUBLIC_RUN_EVENT_SCHEMA_SHA256
        or public_run_schema.get("$id") != PUBLIC_RUN_EVENT_SCHEMA_ID
        or candidate.self_digest_pointers.get(PUBLIC_RUN_EVENT_SCHEMA_ID)
        != "/event_digest"
        or PUBLIC_RUN_FORBIDDEN_FIELD_NAMES.intersection(
            _schema_property_names(public_run_schema)
        )
    ):
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_PUBLIC_RUN_EVENT_CONTRACT_MISMATCH"
        )
    if VERSION_PATH.exists():
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_ACTIVE_VERSION_FORBIDDEN"
        )

    observation_descriptor = _schema_descriptor(
        path=(
            "CodexSkills/governance/retention/schemas/"
            "root-lifecycle-observation.schema.json"
        ),
        schema_id=OBSERVATION_SCHEMA_ID,
        schema=observation_schema,
        pointer=OBSERVATION_SELF_POINTER,
    )
    report_descriptor = _schema_descriptor(
        path=(
            "CodexSkills/governance/retention/schemas/"
            "root-lifecycle-selection-report.schema.json"
        ),
        schema_id=REPORT_SCHEMA_ID,
        schema=report_schema,
        pointer=REPORT_SELF_POINTER,
    )
    readiness: Dict[str, Any] = {
        "artifact_digest": "0" * 64,
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_PROTECTED_LOCAL_MANAGED_RAW_BOUNDARY_READY"
        ),
        "owner_plane": "MECHANISM",
        "digest_algorithm": "SHA-256",
        "source_trust": {
            "candidate_bundle": {
                **_trust_descriptor(
                    artifact_digest=CANDIDATE_MANIFEST_RAW_SHA256,
                    canonical_path=CANDIDATE_MANIFEST_PATH,
                    expected_mode="CANDIDATE",
                    verified_git_object_id=CANDIDATE_GIT_OBJECT,
                ),
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "schema_count": len(candidate.schemas),
                "policy_count": len(candidate.policies),
            },
            "raw_segment_schema": {
                **_trust_descriptor(
                    artifact_digest=RAW_SEGMENT_SCHEMA_RAW_SHA256,
                    canonical_path=RAW_SEGMENT_SCHEMA_PATH,
                    expected_mode="AUTO_PRIVATE_SCHEMA_EXTERNAL",
                    verified_git_object_id=CANDIDATE_GIT_OBJECT,
                ),
                "schema_version": RAW_SEGMENT_SCHEMA_ID,
                "schema_sha256": RAW_SEGMENT_SCHEMA_SHA256,
                "self_digest_pointer": "/segment_digest",
                "bundle_member": False,
                "private_schema": True,
            },
            "retention_policy": {
                "policy_id": RETENTION_POLICY_ID,
                "policy_sha256": RETENTION_POLICY_SHA256,
                "bundle_member": True,
            },
            "public_run_event_schema": {
                "schema_version": PUBLIC_RUN_EVENT_SCHEMA_ID,
                "schema_sha256": PUBLIC_RUN_EVENT_SCHEMA_SHA256,
                "self_digest_pointer": "/event_digest",
                "bundle_member": True,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "m003_dependency_contract": {
            "lstat_first": True,
            "realpath_containment_required": True,
            "root_symlink_allowed": False,
            "candidate_symlink_allowed": False,
            "sibling_prefix_match_allowed": False,
            "root_overlap_allowed": False,
            "special_file_allowed": False,
            "private_root_path_serialized": False,
        },
        "m031_dependency_contract": {
            "public_run_event_schema_id": PUBLIC_RUN_EVENT_SCHEMA_ID,
            "private_raw_schema_id": RAW_SEGMENT_SCHEMA_ID,
            "public_queue_contains_raw": False,
            "raw_private_fields_structurally_impossible": True,
            "private_schema_bundle_member": False,
        },
        "root_lifecycle_contract": {
            "component_path": (
                "CodexSkills/governance/retention/root_lifecycle.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": _sha256(ROOT_LIFECYCLE_PATH.read_bytes()),
            "root_class_mapping": [
                {
                    "root_class": row[0],
                    "lifecycle_class": row[1],
                    "ttl_selection_allowed": row[2],
                    "lifecycle_action": row[3],
                }
                for row in ROOT_CLASS_ROWS
            ],
            "protected_root_classes": list(PROTECTED_ROOT_CLASSES),
            "managed_raw_root_class": "STAGING",
            "public_queue_root_class": "PUBLIC_QUEUE",
            "only_managed_raw_may_reach_m061": True,
            "protected_or_queue_selected_count": 0,
            "protected_delete_budget": 0,
            "raw_ownership_marker_recomputed": True,
            "raw_payload_digest_recomputed": True,
            "persistent_managed_raw_default_enabled": False,
            "production_certification_status": "PENDING_M061",
            "time_evaluation_performed": False,
            "destructive_action_permitted": False,
            "observation_schema": observation_descriptor,
            "report_schema": report_descriptor,
            "report_recomputation_required": True,
        },
        "offline_contract": {
            "clock_basis": "UTC_WALL_CLOCK",
            "ttl_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
            "offline_period_hard_guarantee_claimed": False,
            "offline_resume_first_cycle_receipt_required": True,
            "offline_gap_receipt_required": True,
            "offline_breach_code": "OFFLINE_TTL_BREACH",
        },
        "real_execution_permitted": False,
        "nonmutation": {
            "activation_forbidden": True,
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "canonical_publication_permitted": False,
            "state_write_permitted": False,
            "raw_expiry_action_permitted": False,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-003", "M-031"],
            "completed_task_ids": ["M-060"],
            "pending_task_ids": ["M-061"],
            "required_output": "ROOT_TYPING_AND_LIFECYCLE_CONTRACT",
            "done_gate": (
                "LEGACY_LOCAL_SOURCE_NEVER_SELECTED_BY_72H_JOB"
            ),
        },
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
    }
    readiness["artifact_digest"] = canonical_digest(
        readiness,
        "/artifact_digest",
    )
    readiness_schema = build_readiness_schema()
    schemas = dict(contract.schemas)
    if READINESS_SCHEMA_ID in schemas:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_READINESS_SCHEMA_REBIND"
        )
    schemas[READINESS_SCHEMA_ID] = readiness_schema
    try:
        registry, format_checker = build_registry(schemas)
        readiness_bundle = ContractBundle(
            schemas=schemas,
            registry=registry,
            format_checker=format_checker,
            self_digest_pointers={
                **contract.self_digest_pointers,
                READINESS_SCHEMA_ID: "/artifact_digest",
            },
            policies=contract.policies,
            protocol_revision=contract.protocol_revision,
        )
        validate_instance(
            readiness_bundle,
            readiness,
            READINESS_SCHEMA_ID,
            verify_digest=True,
            public=True,
        )
        scan_public_value(readiness, candidate.policies)
    except Exception as exc:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_READINESS_INVALID:" + str(exc)
        ) from exc
    return readiness


def render_observation_schema() -> bytes:
    return _render(build_observation_schema())


def render_report_schema() -> bytes:
    return _render(build_report_schema())


def render_readiness_schema() -> bytes:
    return _render(build_readiness_schema())


def render_readiness() -> bytes:
    return _render(build_readiness())


def _write() -> None:
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    OBSERVATION_SCHEMA_PATH.write_bytes(render_observation_schema())
    REPORT_SCHEMA_PATH.write_bytes(render_report_schema())
    READINESS_SCHEMA_PATH.write_bytes(render_readiness_schema())
    OUTPUT_PATH.write_bytes(render_readiness())


def _check() -> None:
    expected = {
        OBSERVATION_SCHEMA_PATH: render_observation_schema(),
        REPORT_SCHEMA_PATH: render_report_schema(),
        READINESS_SCHEMA_PATH: render_readiness_schema(),
        OUTPUT_PATH: render_readiness(),
    }
    drift = [
        path.as_posix()
        for path, raw in expected.items()
        if not path.exists() or path.read_bytes() != raw
    ]
    if drift:
        raise ProtectedLocalRawBoundaryBuildError(
            "M060_BYTE_DRIFT:" + ",".join(drift)
        )


def main() -> int:
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--check", action="store_true")
    mode.add_argument("--write", action="store_true")
    args = parser.parse_args()
    if args.write:
        _write()
    else:
        _check()
    print(
        "PROTECTED_LOCAL_MANAGED_RAW_BOUNDARY_OK "
        "protected_classes=3 managed_raw_classes=1 "
        "protected_selected=0 real_execution=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
