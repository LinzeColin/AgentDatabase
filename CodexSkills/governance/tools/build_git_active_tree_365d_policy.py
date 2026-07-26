#!/usr/bin/env python3
"""Build/check non-active Mechanism M-063 active-tree retention evidence."""

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

from CodexSkills.governance.retention.git_active_tree_policy import (  # noqa: E402
    JSONL_SERIALIZATION,
    MAX_OBJECT_BYTES,
    MAX_PART_BYTES,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    PLAN_SCHEMA_ID,
    PLAN_SELF_POINTER,
    PROTOCOL_REVISION,
    PRUNE_ACTION_ORDER,
    KEEP_ACTION_ORDER,
    RETENTION_MICROSECONDS,
    RETENTION_POLICY_ID,
    RETENTION_POLICY_SHA256,
    RUN_LOG_ROOT,
    build_git_active_tree_contract,
)
from CodexSkills.governance.tools import (  # noqa: E402
    build_public_safe_queue_lifecycle as m062_builder,
)
from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (  # noqa: E402
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (  # noqa: E402
    ContractBundle,
    ContractError,
    build_registry,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = REPO_ROOT / "CodexSkills" / "governance"
RETENTION_DIR = GOVERNANCE_DIR / "retention"
SCHEMA_DIR = RETENTION_DIR / "schemas"
COMPONENT_PATH = RETENTION_DIR / "git_active_tree_policy.py"
OUTPUT_PATH = RETENTION_DIR / "git-active-tree-365d-readiness.json"
OBSERVATION_SCHEMA_PATH = (
    SCHEMA_DIR / "git-active-tree-retention-observation.schema.json"
)
PLAN_SCHEMA_PATH = SCHEMA_DIR / "git-active-tree-prune-plan.schema.json"
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "git-active-tree-365d-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:git-active-tree-365d-readiness:v1"
)
NEXT_PHASE = "MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE"

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

M062_GIT_OBJECT = (
    "sha1:72fd98353fa7065e520067c221e8689435dffd4c"
)
M062_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "public-safe-queue-lifecycle-readiness.json"
)
M062_READINESS_RAW_SHA256 = (
    "cf7193aa6057647ad48dd7c74ce133faaa138a49311322d13599f8329525712f"
)
M062_READINESS_SELF_DIGEST = (
    "96f9ba8496f3e6496924c5c7cfb2536c3aeb694eacef202758365046d2093373"
)
M062_COMPONENT_PATH = (
    "CodexSkills/governance/retention/public_safe_queue.py"
)
M062_COMPONENT_RAW_SHA256 = (
    "920c086674753d3e3226e1cb1ff2a2c1317e0a8049ead1819daf6e6552e0e20f"
)
M062_SCHEMA_CONTRACTS = (
    (
        "CodexSkills/governance/retention/schemas/"
        "public-safe-queue-observation.schema.json",
        "65aae782d197b2bfcf837194583ae4a57fbdf7d8272d48b99d3e0ea1536940bd",
        "62b2eaa0e8e977850f05b97c437f09a22436fa7b9aebf2d64c458ff6c2eb9fa2",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "public-safe-queue-remote-readback.schema.json",
        "89d364bbf7119351570743e57ebd7c955975830f636e606c477358e3ae950364",
        "0963016596308548aadfe69ffbc230521e05b3bcd7171dfb40693799dd6b86f8",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "public-safe-queue-lifecycle-plan.schema.json",
        "7f8b28588bb014d0e78d2866f2f8b76859bd0e92484cc6cd28175426df930e89",
        "5643a4881b5dfb19967a7ade5b46f60c19b6d7f850c5051aefd1ea8a3adb6c34",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "public-safe-queue-lifecycle-readiness.schema.json",
        "23eac7f36c02c3965bb3ebef4a824d94187856f871141aa8bc241dbdfa33c1d7",
        "7b301a22ce6095e3108aaabe955d17082f47c6cc29276315d2e971aed070f42c",
    ),
)

DAILY_MANIFEST_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:daily-run-shard-manifest:v1"
)
INDEX_ENTRY_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:run-event-index-entry:v1"
)
RETENTION_RECEIPT_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:retention-receipt:v3"
)
PUBLICATION_MANIFEST_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:publication-manifest:v2"
)
DAILY_MANIFEST_SCHEMA_SHA256 = (
    "e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337"
)
INDEX_ENTRY_SCHEMA_SHA256 = (
    "27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433"
)
RETENTION_RECEIPT_SCHEMA_SHA256 = (
    "81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45"
)
PUBLICATION_MANIFEST_SCHEMA_SHA256 = (
    "e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346"
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class GitActiveTreePolicyBuildError(ValueError):
    """M-063 material cannot be reproduced without weakening a gate."""


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
        raise GitActiveTreePolicyBuildError(code) from exc
    if not isinstance(value, dict):
        raise GitActiveTreePolicyBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise GitActiveTreePolicyBuildError("M063_GIT_OBJECT_INVALID")
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
        raise GitActiveTreePolicyBuildError(
            "M063_GIT_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise GitActiveTreePolicyBuildError(
            "M063_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _ref(name: str) -> Dict[str, str]:
    return {"$ref": REF + name}


def _nullable_sha256() -> Mapping[str, Any]:
    return {
        "anyOf": [
            {"type": "null"},
            _ref("sha256"),
        ]
    }


def _manifest_ref_schema() -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": {
            "artifact_repo_path": _ref("repo_relative_posix_path"),
            "manifest_uid": {
                "pattern": "^drm_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
                "type": "string",
            },
            "manifest_digest": _ref("sha256"),
            "manifest_revision": _ref("positive_count"),
            "local_date": _ref("calendar_date"),
            "previous_manifest_digest": _nullable_sha256(),
        },
        "required": [
            "artifact_repo_path",
            "manifest_uid",
            "manifest_digest",
            "manifest_revision",
            "local_date",
            "previous_manifest_digest",
        ],
        "type": "object",
    }


def build_observation_schema() -> Mapping[str, Any]:
    part = {
        "additionalProperties": False,
        "allOf": [
            {
                "if": {
                    "properties": {"state": {"const": "PRUNED"}},
                    "required": ["state"],
                },
                "then": {"required": ["pruned_at"]},
                "else": {"not": {"required": ["pruned_at"]}},
            }
        ],
        "properties": {
            "part_number": _ref("positive_count"),
            "state": {"enum": ["ACTIVE", "PRUNED"]},
            "shard_path": _ref("repo_relative_posix_path"),
            "index_path": _ref("repo_relative_posix_path"),
            "shard_digest": _ref("sha256"),
            "shard_bytes": _ref("positive_count"),
            "record_count": _ref("positive_count"),
            "index_digest": _ref("sha256"),
            "index_bytes": _ref("positive_count"),
            "index_record_count": _ref("positive_count"),
            "first_published_at": _ref("utc_z_timestamp"),
            "retention_not_before": _ref("utc_z_timestamp"),
            "elapsed_microseconds": _ref("nonnegative_count"),
            "retention_state": {
                "enum": [
                    "RETAIN_BEFORE_BOUNDARY",
                    "RETAIN_AT_BOUNDARY",
                    "ELIGIBLE_AFTER_BOUNDARY",
                    "ALREADY_PRUNED",
                ]
            },
            "active_shard_present": {"type": "boolean"},
            "retained_index_present": {"const": True},
            "full_fidelity_verified": {"type": "boolean"},
            "pruned_at": _ref("utc_z_timestamp"),
        },
        "required": [
            "part_number",
            "state",
            "shard_path",
            "index_path",
            "shard_digest",
            "shard_bytes",
            "record_count",
            "index_digest",
            "index_bytes",
            "index_record_count",
            "first_published_at",
            "retention_not_before",
            "elapsed_microseconds",
            "retention_state",
            "active_shard_present",
            "retained_index_present",
            "full_fidelity_verified",
        ],
        "type": "object",
    }
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": OBSERVATION_SCHEMA_ID},
            "protocol_revision": _ref("protocol_revision"),
            "bundle_digest": _ref("sha256"),
            "observation_uid": {
                "pattern": "^atr_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
                "type": "string",
            },
            "observed_at": _ref("utc_z_timestamp"),
            "scope": {"const": "GIT_CURRENT_TREE"},
            "clock_basis": {"const": "UTC_WALL_CLOCK"},
            "retention_policy_id": {"const": RETENTION_POLICY_ID},
            "policy_snapshot_digest": _ref("sha256"),
            "source_manifest": _manifest_ref_schema(),
            "manifest_history_count": _ref("positive_count"),
            "part_observations": {
                "items": part,
                "minItems": 1,
                "type": "array",
            },
            "active_part_count": _ref("nonnegative_count"),
            "keep_part_count": _ref("nonnegative_count"),
            "eligible_part_count": _ref("nonnegative_count"),
            "pruned_part_count": _ref("nonnegative_count"),
            "active_shard_bytes": _ref("nonnegative_count"),
            "retained_index_bytes": _ref("positive_count"),
            "full_fidelity_aggregation_substitution_performed": {
                "const": False
            },
            "history_rewrite_performed": {"const": False},
            "hard_delete_claimed": {"const": False},
            "state_mutation_performed": {"const": False},
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "observation_uid",
            "observed_at",
            "scope",
            "clock_basis",
            "retention_policy_id",
            "policy_snapshot_digest",
            "source_manifest",
            "manifest_history_count",
            "part_observations",
            "active_part_count",
            "keep_part_count",
            "eligible_part_count",
            "pruned_part_count",
            "active_shard_bytes",
            "retained_index_bytes",
            "full_fidelity_aggregation_substitution_performed",
            "history_rewrite_performed",
            "hard_delete_claimed",
            "state_mutation_performed",
            "evidence_bundle_digest",
        ],
        "title": "Mechanism M-063 Git active-tree retention observation",
        "type": "object",
    }


def build_plan_schema() -> Mapping[str, Any]:
    candidate = {
        "additionalProperties": False,
        "properties": {
            "part_number": _ref("positive_count"),
            "artifact_repo_path": _ref("repo_relative_posix_path"),
            "prior_artifact_digest": _ref("sha256"),
            "prior_artifact_bytes": _ref("positive_count"),
            "prior_record_count": _ref("positive_count"),
            "first_published_at": _ref("utc_z_timestamp"),
            "retention_not_before": _ref("utc_z_timestamp"),
            "prune_deadline_at": _ref("utc_z_timestamp"),
            "retained_index_path": _ref("repo_relative_posix_path"),
            "retained_index_digest": _ref("sha256"),
            "prior_daily_manifest_digest": _ref("sha256"),
            "deadline_status": {
                "enum": ["ON_TIME_WINDOW", "DEADLINE_BREACHED"]
            },
            "required_gap_code": {
                "anyOf": [
                    {"type": "null"},
                    {
                        "const": (
                            "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
                        )
                    },
                ]
            },
        },
        "required": [
            "part_number",
            "artifact_repo_path",
            "prior_artifact_digest",
            "prior_artifact_bytes",
            "prior_record_count",
            "first_published_at",
            "retention_not_before",
            "prune_deadline_at",
            "retained_index_path",
            "retained_index_digest",
            "prior_daily_manifest_digest",
            "deadline_status",
            "required_gap_code",
        ],
        "type": "object",
    }
    return {
        "$id": PLAN_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": PLAN_SCHEMA_ID},
            "protocol_revision": _ref("protocol_revision"),
            "bundle_digest": _ref("sha256"),
            "plan_uid": {
                "pattern": "^atp_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
                "type": "string",
            },
            "generated_at": _ref("utc_z_timestamp"),
            "observation_ref": {
                "additionalProperties": False,
                "properties": {
                    "observation_uid": {
                        "pattern": (
                            "^atr_[0-7][0-9A-HJKMNP-TV-Z]{25}$"
                        ),
                        "type": "string",
                    },
                    "evidence_bundle_digest": _ref("sha256"),
                },
                "required": [
                    "observation_uid",
                    "evidence_bundle_digest",
                ],
                "type": "object",
            },
            "source_manifest_ref": _manifest_ref_schema(),
            "decision": {
                "enum": [
                    "KEEP_ACTIVE_TREE",
                    "PLAN_CURRENT_TREE_PRUNE",
                ]
            },
            "selected_count": _ref("nonnegative_count"),
            "selected_bytes": _ref("nonnegative_count"),
            "candidates": {"items": candidate, "type": "array"},
            "action_order": {
                "items": {
                    "enum": sorted(
                        set(KEEP_ACTION_ORDER + PRUNE_ACTION_ORDER)
                    )
                },
                "minItems": 1,
                "type": "array",
            },
            "current_tree_prune_only": {"const": True},
            "retained_index_required": {"const": True},
            "full_fidelity_aggregation_substitution_permitted": {
                "const": False
            },
            "history_rewrite_performed": {"const": False},
            "hard_delete_claimed": {"const": False},
            "delete_authority_granted": {"const": False},
            "real_execution_permitted": {"const": False},
            "auto_executor_integration_status": {"const": "NOT_BOUND"},
            "state_mutation_performed": {"const": False},
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "plan_uid",
            "generated_at",
            "observation_ref",
            "source_manifest_ref",
            "decision",
            "selected_count",
            "selected_bytes",
            "candidates",
            "action_order",
            "current_tree_prune_only",
            "retained_index_required",
            "full_fidelity_aggregation_substitution_permitted",
            "history_rewrite_performed",
            "hard_delete_claimed",
            "delete_authority_granted",
            "real_execution_permitted",
            "auto_executor_integration_status",
            "state_mutation_performed",
            "evidence_bundle_digest",
        ],
        "title": "Mechanism M-063 non-mutating Git active-tree prune plan",
        "type": "object",
    }


def _descriptor(
    *,
    schema_id: str,
    path: str,
    raw_digest: str,
    schema_digest: str,
    self_pointer: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "artifact_digest": raw_digest,
        "schema_sha256": schema_digest,
        "self_digest_pointer": self_pointer,
    }


def _validate_predecessor() -> Mapping[str, Any]:
    readiness_raw = _git_blob(
        M062_GIT_OBJECT,
        M062_READINESS_PATH,
    )
    readiness = _load_bytes(
        readiness_raw,
        "M063_M062_READINESS_JSON_INVALID",
    )
    component_raw = _git_blob(
        M062_GIT_OBJECT,
        M062_COMPONENT_PATH,
    )
    if (
        _sha256(readiness_raw) != M062_READINESS_RAW_SHA256
        or readiness.get("artifact_digest")
        != M062_READINESS_SELF_DIGEST
        or canonical_digest(readiness, "/artifact_digest")
        != M062_READINESS_SELF_DIGEST
        or readiness.get("status")
        != "DRAFT_NON_ACTIVE_PUBLIC_SAFE_QUEUE_LIFECYCLE_READY"
        or readiness.get("next_phase")
        != "MECHANISM_GIT_ACTIVE_TREE_365D_POLICY"
        or _sha256(component_raw) != M062_COMPONENT_RAW_SHA256
    ):
        raise GitActiveTreePolicyBuildError(
            "M063_M062_PREDECESSOR_TRUST_MISMATCH"
        )
    exact_pairs = (
        (M062_READINESS_PATH, readiness_raw),
        (M062_COMPONENT_PATH, component_raw),
    )
    for path, expected_raw, expected_canonical in M062_SCHEMA_CONTRACTS:
        raw = _git_blob(M062_GIT_OBJECT, path)
        value = _load_bytes(raw, "M063_M062_SCHEMA_JSON_INVALID")
        if (
            _sha256(raw) != expected_raw
            or canonical_digest(value) != expected_canonical
        ):
            raise GitActiveTreePolicyBuildError(
                "M063_M062_SCHEMA_TRUST_MISMATCH:" + path
            )
        exact_pairs += ((path, raw),)
    for relative_path, expected in exact_pairs:
        if (
            REPO_ROOT.joinpath(*relative_path.split("/")).read_bytes()
            != expected
        ):
            raise GitActiveTreePolicyBuildError(
                "M063_M062_WORKING_TREE_DRIFT:" + relative_path
            )
    m062_builder._check()
    return readiness


def trusted_context():
    """Return the exact 31/5 AU-040 contract plus M-063 evidence schemas."""

    _validate_predecessor()
    acceptance = load_au040_acceptance()
    observation_schema = build_observation_schema()
    plan_schema = build_plan_schema()
    return build_git_active_tree_contract(
        acceptance,
        observation_schema=observation_schema,
        expected_observation_schema_digest=canonical_digest(
            observation_schema
        ),
        plan_schema=plan_schema,
        expected_plan_schema_digest=canonical_digest(plan_schema),
    )


def build_readiness() -> Mapping[str, Any]:
    predecessor = _validate_predecessor()
    acceptance = load_au040_acceptance()
    observation_schema = build_observation_schema()
    plan_schema = build_plan_schema()
    context = build_git_active_tree_contract(
        acceptance,
        observation_schema=observation_schema,
        expected_observation_schema_digest=canonical_digest(
            observation_schema
        ),
        plan_schema=plan_schema,
        expected_plan_schema_digest=canonical_digest(plan_schema),
    )
    component_digest = _sha256(COMPONENT_PATH.read_bytes())
    readiness: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": "DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY",
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
            "m062_predecessor": {
                "verified_git_object_id": M062_GIT_OBJECT,
                "readiness": {
                    "canonical_path": M062_READINESS_PATH,
                    "content_digest": M062_READINESS_RAW_SHA256,
                    "artifact_digest": M062_READINESS_SELF_DIGEST,
                },
                "component": {
                    "component_path": M062_COMPONENT_PATH,
                    "content_digest": M062_COMPONENT_RAW_SHA256,
                },
                "status": predecessor["status"],
                "done_gate": predecessor["task_contract"]["done_gate"],
            },
            "retention_policy": {
                "policy_id": RETENTION_POLICY_ID,
                "policy_snapshot_digest": RETENTION_POLICY_SHA256,
                "bundle_member": True,
            },
            "daily_manifest_schema": {
                "schema_version": DAILY_MANIFEST_SCHEMA_ID,
                "schema_sha256": DAILY_MANIFEST_SCHEMA_SHA256,
                "self_digest_pointer": "/manifest_digest",
                "bundle_member": True,
            },
            "index_entry_schema": {
                "schema_version": INDEX_ENTRY_SCHEMA_ID,
                "schema_sha256": INDEX_ENTRY_SCHEMA_SHA256,
                "self_digest_pointer": "/index_entry_digest",
                "bundle_member": True,
            },
            "retention_receipt_schema": {
                "schema_version": RETENTION_RECEIPT_SCHEMA_ID,
                "schema_sha256": RETENTION_RECEIPT_SCHEMA_SHA256,
                "self_digest_pointer": "/receipt_digest",
                "bundle_member": True,
            },
            "publication_manifest_schema": {
                "schema_version": PUBLICATION_MANIFEST_SCHEMA_ID,
                "schema_sha256": PUBLICATION_MANIFEST_SCHEMA_SHA256,
                "self_digest_pointer": "/manifest_digest",
                "bundle_member": True,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "active_tree_contract": {
            "component_path": (
                "CodexSkills/governance/retention/"
                "git_active_tree_policy.py"
            ),
            "content_digest": component_digest,
            "scope": "GIT_CURRENT_TREE",
            "run_log_root": {"canonical_path": RUN_LOG_ROOT},
            "clock_basis": "UTC_WALL_CLOCK",
            "retention_elapsed_seconds": (
                RETENTION_MICROSECONDS // 1_000_000
            ),
            "boundary_at_365_days_retained": True,
            "eligibility_condition": (
                "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
            ),
            "day_364_action": "KEEP_FULL_FIDELITY",
            "day_365_boundary_action": "KEEP_FULL_FIDELITY",
            "after_day_365_action": "ELIGIBLE_FOR_CURRENT_TREE_PRUNE",
            "prune_deadline_hours": 24,
            "prune_deadline_equality_is_on_time": True,
            "prune_deadline_hard_guarantee_claimed": False,
            "prune_enforcement_availability": (
                "LOCAL_RUNTIME_AVAILABLE_ONLY"
            ),
            "full_fidelity_aggregation_substitution_permitted": False,
            "manifest_history_required": "REVISION_1_THROUGH_LATEST",
            "manifest_revisions_append_only": True,
            "part_number_reuse_permitted": False,
            "retained_index_required_after_prune": True,
            "retained_index_full_event_payload_permitted": False,
            "prune_receipt_required": True,
            "prune_receipt_prior_manifest_binding_required": True,
            "prune_transaction_exact_artifact_set_required": True,
            "jsonl_serialization": JSONL_SERIALIZATION,
            "max_part_bytes": MAX_PART_BYTES,
            "max_object_bytes": MAX_OBJECT_BYTES,
            "history_rewrite_permitted": False,
            "hard_delete_claimed": False,
            "real_execution_permitted": False,
            "auto_executor_integration_status": "NOT_BOUND",
            "observation_schema": _descriptor(
                schema_id=OBSERVATION_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "git-active-tree-retention-observation.schema.json"
                ),
                raw_digest=_sha256(_render(observation_schema)),
                schema_digest=canonical_digest(observation_schema),
                self_pointer=OBSERVATION_SELF_POINTER,
            ),
            "prune_plan_schema": _descriptor(
                schema_id=PLAN_SCHEMA_ID,
                path=(
                    "CodexSkills/governance/retention/schemas/"
                    "git-active-tree-prune-plan.schema.json"
                ),
                raw_digest=_sha256(_render(plan_schema)),
                schema_digest=canonical_digest(plan_schema),
                self_pointer=PLAN_SELF_POINTER,
            ),
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "candidate_bundle_unchanged": True,
            "retention_policy_unchanged": True,
            "run_log_artifact_instance_created": False,
            "retention_receipt_instance_created": False,
            "git_current_tree_mutation_performed": False,
            "git_history_rewrite_performed": False,
            "state_write_permitted": False,
            "watermark_advance_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-062"],
            "completed_task_ids": ["M-063"],
            "pending_task_ids": ["M-064"],
            "required_output": "DAILY_SHARDS_INDEX_PRUNE_RECEIPTS",
            "done_gate": "DAY_364_AND_365_RETAINED_AFTER_365_ELIGIBLE",
        },
        "schema_closure_count": len(context.evidence_bundle.schemas),
        "policy_count": len(context.evidence_bundle.policies),
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
    scan_public_value(readiness, context.evidence_bundle.policies)
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
        "title": "Mechanism M-063 Git active-tree 365-day readiness",
        "type": "object",
    }


def _contract_with_readiness(
    base: ContractBundle,
    schema: Mapping[str, Any],
) -> ContractBundle:
    schemas = dict(base.schemas)
    pointers = dict(base.self_digest_pointers)
    if READINESS_SCHEMA_ID in schemas:
        raise GitActiveTreePolicyBuildError(
            "M063_READINESS_SCHEMA_REBIND_FORBIDDEN"
        )
    schemas[READINESS_SCHEMA_ID] = schema
    pointers[READINESS_SCHEMA_ID] = "/artifact_digest"
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise GitActiveTreePolicyBuildError(
            "M063_READINESS_SCHEMA_CLOSURE_INVALID:" + str(exc)
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
    context = trusted_context()
    readiness = build_readiness()
    readiness_schema = build_readiness_schema(readiness)
    final_contract = _contract_with_readiness(
        context.evidence_bundle,
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
        raise GitActiveTreePolicyBuildError(
            "M063_READINESS_INVALID:" + str(exc)
        ) from exc
    return {
        OBSERVATION_SCHEMA_PATH: build_observation_schema(),
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
            raise GitActiveTreePolicyBuildError(
                "M063_ARTIFACT_NOT_BYTE_EQUIVALENT:"
                + str(path.relative_to(REPO_ROOT))
            )
    if VERSION_PATH.exists():
        raise GitActiveTreePolicyBuildError(
            "M063_ACTIVE_VERSION_FORBIDDEN"
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
        "GIT_ACTIVE_TREE_365D_POLICY_OK "
        "day_364=KEEP day_365=KEEP after_day_365=ELIGIBLE "
        "history_rewrite=false real_execution=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (
        ContractError,
        GitActiveTreePolicyBuildError,
    ) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
