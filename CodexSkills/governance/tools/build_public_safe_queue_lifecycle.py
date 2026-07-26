#!/usr/bin/env python3
"""Build/check non-active Mechanism M-062 queue lifecycle evidence."""

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

from CodexSkills.governance.retention.public_safe_queue import (  # noqa: E402
    JSONL_SERIALIZATION,
    MAX_SHARD_BYTES,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    PLAN_SCHEMA_ID,
    PLAN_SELF_POINTER,
    PROTOCOL_REVISION,
    PUBLIC_RUN_EVENT_SCHEMA_ID,
    QUEUE_ENVELOPE_SCHEMA_ID,
    QUEUE_ENVELOPE_SELF_POINTER,
    READBACK_SCHEMA_ID,
    READBACK_SELF_POINTER,
    REMOTE_NAME,
    REMOTE_REF,
    RUN_LOG_ROOT,
    build_public_safe_queue_contract,
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
COMPONENT_PATH = RETENTION_DIR / "public_safe_queue.py"
OUTPUT_PATH = (
    RETENTION_DIR / "public-safe-queue-lifecycle-readiness.json"
)
OBSERVATION_SCHEMA_PATH = (
    SCHEMA_DIR / "public-safe-queue-observation.schema.json"
)
READBACK_SCHEMA_PATH = (
    SCHEMA_DIR / "public-safe-queue-remote-readback.schema.json"
)
PLAN_SCHEMA_PATH = (
    SCHEMA_DIR / "public-safe-queue-lifecycle-plan.schema.json"
)
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "public-safe-queue-lifecycle-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:public-safe-queue-lifecycle-readiness:v1"
)
NEXT_PHASE = "MECHANISM_GIT_ACTIVE_TREE_365D_POLICY"

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

M061_GIT_OBJECT = (
    "sha1:b023ac71c5c7852a95f4b87a56981fe7a42c32d9"
)
M061_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "managed-raw-72h-readiness.json"
)
M061_READINESS_RAW_SHA256 = (
    "d60a71554ffbe4bde30fbd639e723086598df22b69b4ceee04b070dd4ddb6e0f"
)
M061_READINESS_SELF_DIGEST = (
    "dad952d9df1523bb63765dc028a4f3609251834dcb52dfa06a085341f555f774"
)
M061_COMPONENT_PATH = (
    "CodexSkills/governance/retention/managed_raw_policy.py"
)
M061_COMPONENT_RAW_SHA256 = (
    "d18da577b0530c319579ca95c77d6126cee0e56de9552a13965c2fbd2eadaf66"
)

QUEUE_ENVELOPE_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/private/"
    "public-queue-envelope.schema.json"
)
QUEUE_ENVELOPE_SCHEMA_RAW_SHA256 = (
    "c802243b23641822eed6a708435c7df363b4c57a3b8a02dc73ce0c1ac16e29b1"
)
QUEUE_ENVELOPE_SCHEMA_SHA256 = (
    "4bc05ac0b883a85e7efd1a1393772f0596714b9df76f8d9277fa62ebbd741d35"
)
PUBLIC_RUN_EVENT_SCHEMA_PATH = (
    "CodexSkills/registry/auto/schemas/public/"
    "public-run-event.schema.json"
)
PUBLIC_RUN_EVENT_SCHEMA_RAW_SHA256 = (
    "c11fa25cbc292869e788f0639361eef8dcfdadf4019a13e4d88e0eb301ae0557"
)
PUBLIC_RUN_EVENT_SCHEMA_SHA256 = (
    "c2b494baf284ba53f6c0101e0ab29b228de68964e4ab823710bcc3461555e523"
)
PUBLIC_VALUE_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:public-value:v2"
)
PUBLIC_VALUE_POLICY_SHA256 = (
    "cff871b00dec9d33ba6bd879e02b7039cef57d11e35bdc4c57a80d4d3ea519d4"
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class PublicSafeQueueBuildError(ValueError):
    """M-062 material cannot be reproduced without weakening a gate."""


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
        raise PublicSafeQueueBuildError(code) from exc
    if not isinstance(value, dict):
        raise PublicSafeQueueBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise PublicSafeQueueBuildError("M062_GIT_OBJECT_INVALID")
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
        raise PublicSafeQueueBuildError(
            "M062_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise PublicSafeQueueBuildError(
            "M062_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _ref(name: str) -> Dict[str, str]:
    return {"$ref": REF + name}


def _digest_ref() -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": ["evidence_bundle_digest"],
        "type": "object",
    }


def _nullable_digest_ref() -> Mapping[str, Any]:
    return {
        "anyOf": [
            {"type": "null"},
            _digest_ref(),
        ]
    }


def _queue_envelope_ref() -> Mapping[str, Any]:
    properties = {
        "envelope_uid": _ref("envelope_uid"),
        "envelope_digest": _ref("sha256"),
    }
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "type": "object",
    }


def _artifact_ref() -> Mapping[str, Any]:
    properties = {
        "artifact_schema_id": {
            "const": PUBLIC_RUN_EVENT_SCHEMA_ID,
        },
        "artifact_uid": _ref("event_uid"),
        "artifact_digest": _ref("sha256"),
    }
    return {
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "type": "object",
    }


def build_observation_schema() -> Mapping[str, Any]:
    properties = {
        "schema_version": {"const": OBSERVATION_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "observation_uid": _ref("typed_uid"),
        "observed_at": _ref("utc_z_timestamp"),
        "queue_envelope_ref": _queue_envelope_ref(),
        "artifact_ref": _artifact_ref(),
        "lane": {"const": "RUN_LOG"},
        "source_queue_state": {
            "enum": ["QUARANTINED", "READY", "SETTLED"],
        },
        "artifact_repo_path": _ref("repo_relative_posix_path"),
        "artifact_serialization": {
            "const": "RFC8785_JCS_OBJECT",
        },
        "artifact_bytes": _ref("positive_count"),
        "public_schema_valid": {"const": True},
        "semantic_event_valid": {"const": True},
        "post_serialization_scan_passed": {"const": True},
        "raw_or_private_field_count": {"const": 0},
        "physical_queue_path_consumed": {"const": False},
        "state_mutation_performed": {"const": False},
        "actor": {
            "const": "SKILLOPS_PUBLIC_SAFE_QUEUE_GUARD",
        },
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "M-062 public-safe queue observation",
        "type": "object",
    }


def build_readback_schema() -> Mapping[str, Any]:
    properties = {
        "schema_version": {"const": READBACK_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "readback_uid": _ref("typed_uid"),
        "readback_at": _ref("utc_z_timestamp"),
        "queue_envelope_ref": _queue_envelope_ref(),
        "remote_name": {"const": REMOTE_NAME},
        "remote_ref": {"const": REMOTE_REF},
        "expected_remote_head": _ref("git_object_id"),
        "observed_remote_head": _ref("git_object_id"),
        "artifact_repo_path": _ref("repo_relative_posix_path"),
        "artifact_schema_id": {
            "const": PUBLIC_RUN_EVENT_SCHEMA_ID,
        },
        "artifact_uid": _ref("event_uid"),
        "artifact_digest": _ref("sha256"),
        "artifact_serialization": {
            "const": JSONL_SERIALIZATION,
        },
        "record_count": _ref("positive_count"),
        "line_number": _ref("positive_count"),
        "shard_digest": _ref("sha256"),
        "remote_head_advanced": {"const": True},
        "caller_boolean_trusted": {"const": False},
        "state_mutation_performed": {"const": False},
        "evidence_bundle_digest": _ref("sha256"),
    }
    return {
        "$id": READBACK_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": properties,
        "required": list(properties),
        "title": "M-062 public-safe queue remote readback",
        "type": "object",
    }


def build_plan_schema() -> Mapping[str, Any]:
    action_codes = (
        "BIND_REMOTE_READBACK_EVIDENCE",
        "MARK_QUEUE_ENTRY_SETTLED",
        "RETAIN_QUEUE_ENTRY",
        "RETRY_REMOTE_VERIFICATION",
    )
    properties = {
        "schema_version": {"const": PLAN_SCHEMA_ID},
        "protocol_revision": _ref("protocol_revision"),
        "bundle_digest": _ref("sha256"),
        "plan_uid": _ref("typed_uid"),
        "generated_at": _ref("utc_z_timestamp"),
        "observation_ref": {
            "additionalProperties": False,
            "properties": {
                "evidence_bundle_digest": _ref("sha256"),
            },
            "required": ["evidence_bundle_digest"],
            "type": "object",
        },
        "remote_readback_ref": _nullable_digest_ref(),
        "source_queue_state": {
            "enum": ["QUARANTINED", "READY", "SETTLED"],
        },
        "decision": {
            "enum": [
                "CONFIRM_SETTLED",
                "ELIGIBLE_TO_MARK_SETTLED",
                "RETAIN_QUARANTINED",
                "RETAIN_READY",
            ]
        },
        "next_queue_state": {
            "enum": ["QUARANTINED", "READY", "SETTLED"],
        },
        "queue_retention_required": {"type": "boolean"},
        "settlement_eligible": {"type": "boolean"},
        "action_order": {
            "items": {"enum": list(action_codes)},
            "maxItems": 2,
            "minItems": 2,
            "type": "array",
            "uniqueItems": True,
        },
        "queue_content_delete_authority_granted": {
            "const": False,
        },
        "watermark_advance_authority_granted": {
            "const": False,
        },
        "state_mutation_performed": {"const": False},
        "auto_executor_integration_status": {"const": "NOT_BOUND"},
        "evidence_bundle_digest": _ref("sha256"),
    }
    retain_actions = [
        "RETAIN_QUEUE_ENTRY",
        "RETRY_REMOTE_VERIFICATION",
    ]
    settle_actions = [
        "BIND_REMOTE_READBACK_EVIDENCE",
        "MARK_QUEUE_ENTRY_SETTLED",
    ]
    state_branches = (
        (
            "RETAIN_QUARANTINED",
            "QUARANTINED",
            "QUARANTINED",
            True,
            False,
            {"type": "null"},
            retain_actions,
        ),
        (
            "RETAIN_READY",
            "READY",
            "READY",
            True,
            False,
            {"type": "null"},
            retain_actions,
        ),
        (
            "ELIGIBLE_TO_MARK_SETTLED",
            "READY",
            "SETTLED",
            False,
            True,
            _digest_ref(),
            settle_actions,
        ),
        (
            "CONFIRM_SETTLED",
            "SETTLED",
            "SETTLED",
            False,
            True,
            _digest_ref(),
            settle_actions,
        ),
    )
    all_of = []
    for (
        decision,
        source_state,
        next_state,
        retain,
        eligible,
        readback_shape,
        actions,
    ) in state_branches:
        all_of.append(
            {
                "if": {
                    "properties": {
                        "decision": {"const": decision},
                    },
                    "required": ["decision"],
                },
                "then": {
                    "properties": {
                        "source_queue_state": {
                            "const": source_state,
                        },
                        "next_queue_state": {
                            "const": next_state,
                        },
                        "queue_retention_required": {
                            "const": retain,
                        },
                        "settlement_eligible": {
                            "const": eligible,
                        },
                        "remote_readback_ref": readback_shape,
                        "action_order": {"const": actions},
                    }
                },
            }
        )
    return {
        "$id": PLAN_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "allOf": all_of,
        "properties": properties,
        "required": list(properties),
        "title": "M-062 public-safe queue lifecycle plan",
        "type": "object",
    }


def _descriptor(
    *,
    schema_id: str,
    path: str,
    raw_digest: str,
    canonical_digest_value: str,
    self_pointer: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "artifact_digest": raw_digest,
        "schema_sha256": canonical_digest_value,
        "self_digest_pointer": self_pointer,
    }


def _trusted_candidate() -> ContractBundle:
    raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        CANDIDATE_MANIFEST_PATH,
    )
    if _sha256(raw) != CANDIDATE_MANIFEST_RAW_SHA256:
        raise PublicSafeQueueBuildError(
            "M062_CANDIDATE_MANIFEST_RAW_MISMATCH"
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


def _trusted_queue_schema() -> Mapping[str, Any]:
    raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        QUEUE_ENVELOPE_SCHEMA_PATH,
    )
    value = _load_bytes(
        raw,
        "M062_QUEUE_ENVELOPE_SCHEMA_JSON_INVALID",
    )
    if (
        _sha256(raw) != QUEUE_ENVELOPE_SCHEMA_RAW_SHA256
        or canonical_digest(value) != QUEUE_ENVELOPE_SCHEMA_SHA256
        or value.get("$id") != QUEUE_ENVELOPE_SCHEMA_ID
    ):
        raise PublicSafeQueueBuildError(
            "M062_QUEUE_ENVELOPE_SCHEMA_TRUST_MISMATCH"
        )
    return value


def _validate_predecessor_and_candidate(
    candidate: ContractBundle,
) -> Mapping[str, Any]:
    readiness_raw = _git_blob(
        M061_GIT_OBJECT,
        M061_READINESS_PATH,
    )
    readiness = _load_bytes(
        readiness_raw,
        "M062_M061_READINESS_JSON_INVALID",
    )
    component_raw = _git_blob(
        M061_GIT_OBJECT,
        M061_COMPONENT_PATH,
    )
    if (
        _sha256(readiness_raw) != M061_READINESS_RAW_SHA256
        or readiness.get("artifact_digest")
        != M061_READINESS_SELF_DIGEST
        or canonical_digest(readiness, "/artifact_digest")
        != M061_READINESS_SELF_DIGEST
        or readiness.get("status")
        != "DRAFT_NON_ACTIVE_MANAGED_RAW_72H_POLICY_READY"
        or readiness.get("next_phase")
        != "MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE"
        or _sha256(component_raw) != M061_COMPONENT_RAW_SHA256
    ):
        raise PublicSafeQueueBuildError(
            "M062_M061_PREDECESSOR_TRUST_MISMATCH"
        )
    current_pairs = (
        (REPO_ROOT / M061_READINESS_PATH, readiness_raw),
        (REPO_ROOT / M061_COMPONENT_PATH, component_raw),
    )
    if any(path.read_bytes() != expected for path, expected in current_pairs):
        raise PublicSafeQueueBuildError(
            "M062_M061_WORKING_TREE_DRIFT"
        )

    event = candidate.schemas.get(PUBLIC_RUN_EVENT_SCHEMA_ID)
    event_raw = _git_blob(
        CANDIDATE_GIT_OBJECT,
        PUBLIC_RUN_EVENT_SCHEMA_PATH,
    )
    if (
        not isinstance(event, dict)
        or _sha256(event_raw)
        != PUBLIC_RUN_EVENT_SCHEMA_RAW_SHA256
        or canonical_digest(event)
        != PUBLIC_RUN_EVENT_SCHEMA_SHA256
        or candidate.self_digest_pointers.get(
            PUBLIC_RUN_EVENT_SCHEMA_ID
        )
        != "/event_digest"
    ):
        raise PublicSafeQueueBuildError(
            "M062_PUBLIC_RUN_EVENT_CONTRACT_MISMATCH"
        )
    public_value_policy = candidate.policies.get(
        PUBLIC_VALUE_POLICY_ID
    )
    if (
        not isinstance(public_value_policy, dict)
        or canonical_digest(public_value_policy)
        != PUBLIC_VALUE_POLICY_SHA256
        or public_value_policy.get(
            "field_name_allowlist_exact_match_required"
        )
        is not True
        or public_value_policy.get(
            "generic_digest_field_substitution_allowed"
        )
        is not False
    ):
        raise PublicSafeQueueBuildError(
            "M062_PUBLIC_VALUE_POLICY_CONTRACT_MISMATCH"
        )
    if VERSION_PATH.exists():
        raise PublicSafeQueueBuildError(
            "M062_ACTIVE_VERSION_FORBIDDEN"
        )
    return readiness


def _contract(
    candidate: ContractBundle,
    queue_schema: Mapping[str, Any],
) -> ContractBundle:
    observation_schema = build_observation_schema()
    readback_schema = build_readback_schema()
    plan_schema = build_plan_schema()
    return build_public_safe_queue_contract(
        candidate,
        queue_envelope_schema=queue_schema,
        expected_queue_envelope_schema_digest=(
            QUEUE_ENVELOPE_SCHEMA_SHA256
        ),
        observation_schema=observation_schema,
        expected_observation_schema_digest=canonical_digest(
            observation_schema
        ),
        readback_schema=readback_schema,
        expected_readback_schema_digest=canonical_digest(
            readback_schema
        ),
        plan_schema=plan_schema,
        expected_plan_schema_digest=canonical_digest(plan_schema),
    )


def trusted_contract() -> ContractBundle:
    """Return the exact candidate + private queue + M-062 schema closure."""

    candidate = _trusted_candidate()
    _validate_predecessor_and_candidate(candidate)
    return _contract(candidate, _trusted_queue_schema())


def build_readiness() -> Mapping[str, Any]:
    candidate = _trusted_candidate()
    m061_readiness = _validate_predecessor_and_candidate(candidate)
    queue_schema = _trusted_queue_schema()
    contract = _contract(candidate, queue_schema)
    observation_schema = build_observation_schema()
    readback_schema = build_readback_schema()
    plan_schema = build_plan_schema()
    component_digest = _sha256(COMPONENT_PATH.read_bytes())
    readiness: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_PUBLIC_SAFE_QUEUE_LIFECYCLE_READY"
        ),
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
            "m061_predecessor": {
                "verified_git_object_id": M061_GIT_OBJECT,
                "readiness": {
                    "canonical_path": M061_READINESS_PATH,
                    "content_digest": M061_READINESS_RAW_SHA256,
                    "artifact_digest": M061_READINESS_SELF_DIGEST,
                },
                "component": {
                    "component_path": M061_COMPONENT_PATH,
                    "content_digest": M061_COMPONENT_RAW_SHA256,
                },
                "status": m061_readiness["status"],
                "done_gate": m061_readiness["task_contract"][
                    "done_gate"
                ],
            },
            "public_run_event_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": PUBLIC_RUN_EVENT_SCHEMA_PATH,
                "artifact_digest": (
                    PUBLIC_RUN_EVENT_SCHEMA_RAW_SHA256
                ),
                "schema_version": PUBLIC_RUN_EVENT_SCHEMA_ID,
                "schema_sha256": PUBLIC_RUN_EVENT_SCHEMA_SHA256,
                "self_digest_pointer": "/event_digest",
                "bundle_member": True,
            },
            "queue_envelope_schema": {
                "verified_git_object_id": CANDIDATE_GIT_OBJECT,
                "canonical_path": QUEUE_ENVELOPE_SCHEMA_PATH,
                "artifact_digest": (
                    QUEUE_ENVELOPE_SCHEMA_RAW_SHA256
                ),
                "schema_version": QUEUE_ENVELOPE_SCHEMA_ID,
                "schema_sha256": QUEUE_ENVELOPE_SCHEMA_SHA256,
                "self_digest_pointer": (
                    QUEUE_ENVELOPE_SELF_POINTER
                ),
                "private_schema": True,
                "bundle_member": False,
            },
            "public_value_policy": {
                "policy_id": PUBLIC_VALUE_POLICY_ID,
                "policy_sha256": PUBLIC_VALUE_POLICY_SHA256,
                "bundle_member": True,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "public_safe_queue_contract": {
            "component_path": (
                "CodexSkills/governance/retention/"
                "public_safe_queue.py"
            ),
            "component_source_binding_mode": (
                "SUCCESSOR_EXTERNAL_TUPLE_REQUIRED"
            ),
            "content_digest": component_digest,
            "queue_owner_plane": "AUTO",
            "policy_owner_plane": "MECHANISM",
            "lane": "RUN_LOG",
            "queue_storage_class": "PRIVATE_LOCAL_PUBLIC_SAFE",
            "payload_schema_id": PUBLIC_RUN_EVENT_SCHEMA_ID,
            "queue_envelope_schema_id": QUEUE_ENVELOPE_SCHEMA_ID,
            "artifact_path_contract": (
                "SYDNEY_DAILY_PART_JSONL_V1"
            ),
            "run_log_root": {
                "canonical_path": RUN_LOG_ROOT,
            },
            "sydney_local_date_required": True,
            "payload_contains_raw_or_private_fields": False,
            "post_serialization_scan_required": True,
            "max_remote_shard_bytes": MAX_SHARD_BYTES,
            "remote_name": REMOTE_NAME,
            "remote_ref": REMOTE_REF,
            "remote_verification_sequence": [
                "RESOLVE_REMOTE_REF",
                "REQUIRE_ADVANCED_REMOTE_OBJECT",
                "READ_EXACT_OBJECT_BLOB",
                "VALIDATE_ALL_JSONL_RECORDS",
                "REQUIRE_UNIQUE_UID_DIGEST_BYTES_MATCH",
                "EMIT_READBACK_EVIDENCE",
            ],
            "caller_boolean_trusted": False,
            "caller_digest_map_trusted": False,
            "ready_without_readback_action": "RETAIN",
            "quarantined_without_readback_action": "RETAIN",
            "settled_without_readback_action": "FAIL_CLOSED",
            "settled_after_exact_readback_action": "CONFIRM",
            "queue_content_delete_authority_granted": False,
            "watermark_advance_authority_granted": False,
            "remote_reader_integration_status": "NOT_BOUND",
            "auto_executor_integration_status": "NOT_BOUND",
            "real_queue_settlement_permitted": False,
            "m063_daily_manifest_index_contract_deferred": True,
            "observation_schema": _descriptor(
                schema_id=OBSERVATION_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "public-safe-queue-observation.schema.json"
                ),
                raw_digest=_sha256(_render(observation_schema)),
                canonical_digest_value=canonical_digest(
                    observation_schema
                ),
                self_pointer=OBSERVATION_SELF_POINTER,
            ),
            "remote_readback_schema": _descriptor(
                schema_id=READBACK_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "public-safe-queue-remote-readback.schema.json"
                ),
                raw_digest=_sha256(_render(readback_schema)),
                canonical_digest_value=canonical_digest(
                    readback_schema
                ),
                self_pointer=READBACK_SELF_POINTER,
            ),
            "lifecycle_plan_schema": _descriptor(
                schema_id=PLAN_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "public-safe-queue-lifecycle-plan.schema.json"
                ),
                raw_digest=_sha256(_render(plan_schema)),
                canonical_digest_value=canonical_digest(
                    plan_schema
                ),
                self_pointer=PLAN_SELF_POINTER,
            ),
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "public_value_policy_unchanged": True,
            "queue_instance_created": False,
            "queue_envelope_mutation_permitted": False,
            "queue_content_delete_permitted": False,
            "remote_network_call_performed": False,
            "git_worktree_created_by_policy": False,
            "state_write_permitted": False,
            "watermark_advance_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-031", "M-061"],
            "completed_task_ids": ["M-062"],
            "pending_task_ids": ["M-063"],
            "required_output": "QUEUE_UNTIL_REMOTE_VERIFICATION",
            "done_gate": "CONTAINS_NO_RAW_OR_PRIVATE_FIELDS",
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
        "title": "Mechanism M-062 public-safe queue readiness",
        "type": "object",
    }


def _contract_with_readiness(
    base: ContractBundle,
    schema: Mapping[str, Any],
) -> ContractBundle:
    schemas = dict(base.schemas)
    pointers = dict(base.self_digest_pointers)
    if READINESS_SCHEMA_ID in schemas:
        raise PublicSafeQueueBuildError(
            "M062_READINESS_SCHEMA_REBIND_FORBIDDEN"
        )
    schemas[READINESS_SCHEMA_ID] = schema
    pointers[READINESS_SCHEMA_ID] = "/artifact_digest"
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise PublicSafeQueueBuildError(
            "M062_READINESS_SCHEMA_CLOSURE_INVALID:" + str(exc)
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
    contract = trusted_contract()
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
        raise PublicSafeQueueBuildError(
            "M062_READINESS_INVALID:" + str(exc)
        ) from exc
    return {
        OBSERVATION_SCHEMA_PATH: build_observation_schema(),
        READBACK_SCHEMA_PATH: build_readback_schema(),
        PLAN_SCHEMA_PATH: build_plan_schema(),
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
            raise PublicSafeQueueBuildError(
                "M062_ARTIFACT_NOT_BYTE_EQUIVALENT:"
                + str(path.relative_to(REPO_ROOT))
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
        "PUBLIC_SAFE_QUEUE_LIFECYCLE_OK "
        "lane=RUN_LOG raw_private_fields=0 "
        "caller_boolean_trusted=false real_execution=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (
        ContractError,
        PublicSafeQueueBuildError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
