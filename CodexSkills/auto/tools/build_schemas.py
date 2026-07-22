#!/usr/bin/env python3
"""Deterministically materialize the non-active SkillOps Auto A1a schemas."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[1]
GOVERNANCE_TOOLS = REPO_ROOT / "CodexSkills" / "governance" / "tools"
sys.path.insert(0, str(GOVERNANCE_TOOLS))

from canonical_json import canonicalize_object  # noqa: E402


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
POLICY_PREFIX = "urn:linzecolin:agentdatabase:skillops:policy:"
PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
JSON_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
COMMON_ID = SCHEMA_PREFIX + "common-definitions:v1"
BINDING_ID = SCHEMA_PREFIX + "skill-binding:v1"
BASE_MECHANISM_GIT_OBJECT_ID = "sha1:37d07a47ae87fcf246046d1611d3e00f000d1fa4"
MECHANISM_INTERFACE_RAW_SHA256 = (
    "0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998"
)

PUBLIC_SELF_POINTERS = {
    "auto-receipt:v2": "/receipt_digest",
    "migration-receipt:v2": "/receipt_digest",
    "notification-receipt:v3": "/receipt_digest",
    "public-run-event:v2": "/event_digest",
    "publication-manifest:v1": "/manifest_digest",
    "retention-receipt:v2": "/receipt_digest",
    "source-coverage-receipt:v1": "/receipt_digest",
    "source-inventory:v1": "/inventory_digest",
}
PRIVATE_SELF_POINTERS = {
    "lock-state:v1": "/state_digest",
    "public-queue-envelope:v2": "/envelope_digest",
    "raw-segment:v2": "/segment_digest",
    "watermark:v2": "/state_digest",
}


def schema_id(name: str, version: int) -> str:
    return f"{SCHEMA_PREFIX}{name}:v{version}"


def ref(name: str) -> Dict[str, str]:
    return {"$ref": f"{COMMON_ID}#/$defs/{name}"}


def schema_ref(schema: str, pointer: str) -> Dict[str, str]:
    return {"$ref": f"{schema}#{pointer}"}


def obj(
    properties: Mapping[str, Any],
    required: Sequence[str] = (),
    *,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties),
    }
    if required:
        value["required"] = list(required)
    if description:
        value["description"] = description
    return value


def arr(
    items: Mapping[str, Any],
    *,
    min_items: int = 0,
    max_items: Optional[int] = None,
    unique: bool = False,
) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "type": "array",
        "items": dict(items),
        "minItems": min_items,
    }
    if max_items is not None:
        value["maxItems"] = max_items
    if unique:
        value["uniqueItems"] = True
    return value


def nullable(schema: Mapping[str, Any]) -> Dict[str, Any]:
    return {"anyOf": [dict(schema), {"type": "null"}]}


def uid(prefix: str) -> Dict[str, Any]:
    return {
        "type": "string",
        "pattern": rf"^{prefix}_[0-7][0-9A-HJKMNP-TV-Z]{{25}}$",
    }


def safe_ref() -> Dict[str, Any]:
    return {"type": "string", "pattern": "^[a-z][a-z0-9-]{2,63}$"}


def adapter_id() -> Dict[str, Any]:
    return {"type": "string", "pattern": "^[a-z][a-z0-9-]{2,63}$"}


def adapter_version() -> Dict[str, Any]:
    return {
        "type": "string",
        "maxLength": 64,
        "pattern": "^v?[0-9]+\\.[0-9]+\\.[0-9]+(?:-[a-z0-9]+(?:[.-][a-z0-9]+)*)?$",
    }


def forbid(*fields: str) -> Dict[str, Any]:
    return {"not": {"anyOf": [{"required": [field]} for field in fields]}}


def artifact_schema(
    name: str,
    version: int,
    title: str,
    properties: Mapping[str, Any],
    required: Sequence[str],
) -> Dict[str, Any]:
    sid = schema_id(name, version)
    merged = {
        "schema_version": {"const": sid},
        "protocol_revision": ref("protocol_revision"),
        "bundle_digest": ref("sha256"),
        **properties,
    }
    return {
        "$schema": JSON_SCHEMA,
        "$id": sid,
        "title": title,
        **obj(
            merged,
            ["schema_version", "protocol_revision", "bundle_digest", *required],
        ),
    }


def source_inventory_schema() -> Dict[str, Any]:
    exclusion = obj(
        {
            "reason_code": {
                "enum": ["CACHE", "OS_METADATA", "SOURCE_OVERLAP", "VCS_METADATA"]
            },
            "node_count": ref("nonnegative_count"),
            "file_count": ref("nonnegative_count"),
            "byte_count": ref("nonnegative_count"),
        },
        ["reason_code", "node_count", "file_count", "byte_count"],
    )
    scan_error = obj(
        {
            "reason_code": {
                "enum": [
                    "INVALID_PATH_ENCODING",
                    "OVERSIZE_NON_POLICY",
                    "PERMISSION_ERROR",
                    "READ_ERROR",
                    "SPECIAL_FILE",
                    "STAT_ERROR",
                    "SYMLINK_UNSAFE",
                ]
            },
            "count": ref("positive_count"),
        },
        ["reason_code", "count"],
    )
    alias = obj(
        {
            "alias_path": ref("repo_relative_posix_path"),
            "normalized_target_ref": ref("repo_relative_posix_path"),
            "metadata_digest": ref("sha256"),
            "content_digest": ref("sha256"),
        },
        ["alias_path", "normalized_target_ref", "metadata_digest", "content_digest"],
        description="Public alias evidence; raw readlink text is private and forbidden here.",
    )
    return artifact_schema(
        "source-inventory",
        1,
        "Public source inventory",
        {
            "inventory_uid": uid("sinv"),
            "source_class": ref("source_class"),
            "source_root_ref": safe_ref(),
            "observed_started_at": ref("utc_z_timestamp"),
            "observed_finished_at": ref("utc_z_timestamp"),
            "adapter_id": adapter_id(),
            "adapter_version": adapter_version(),
            "adapter_schema_digest": ref("sha256"),
            "source_material_policy_id": {
                "const": POLICY_PREFIX + "source-material:v1"
            },
            "source_material_policy_digest": ref("sha256"),
            "completeness_status": {
                "enum": ["COMPLETE_AFTER_POLICY_EXCLUSIONS", "INCOMPLETE", "UNKNOWN"]
            },
            "included_file_count": ref("nonnegative_count"),
            "included_bytes": ref("nonnegative_count"),
            "included_tree_digest": ref("sha256"),
            "excluded_node_count": ref("nonnegative_count"),
            "excluded_file_count": ref("nonnegative_count"),
            "excluded_bytes": ref("nonnegative_count"),
            "exclusions": arr(exclusion, unique=True),
            "symlink_alias_count": ref("nonnegative_count"),
            "symlink_aliases": arr(alias, unique=True),
            "oversize_blocked_count": ref("nonnegative_count"),
            "scan_error_counts": arr(scan_error, unique=True),
            "inventory_digest": ref("sha256"),
        },
        [
            "inventory_uid",
            "source_class",
            "source_root_ref",
            "observed_started_at",
            "observed_finished_at",
            "adapter_id",
            "adapter_version",
            "adapter_schema_digest",
            "source_material_policy_id",
            "source_material_policy_digest",
            "completeness_status",
            "included_file_count",
            "included_bytes",
            "included_tree_digest",
            "excluded_node_count",
            "excluded_file_count",
            "excluded_bytes",
            "exclusions",
            "symlink_alias_count",
            "symlink_aliases",
            "oversize_blocked_count",
            "scan_error_counts",
            "inventory_digest",
        ],
    )


def public_run_event_schema() -> Dict[str, Any]:
    skill_ref = schema_ref(BINDING_ID, "/properties/skill_ref")
    controlled_invocation = schema_ref(BINDING_ID, "/properties/controlled_invocation")
    metrics = obj(
        {
            "duration_ms": nullable(ref("nonnegative_count")),
            "tool_call_count": ref("nonnegative_count"),
            "input_tokens": nullable(ref("nonnegative_count")),
            "output_tokens": nullable(ref("nonnegative_count")),
            "token_usage_status": {"enum": ["MEASURED", "UNAVAILABLE", "UNKNOWN"]},
        },
        [
            "duration_ms",
            "tool_call_count",
            "input_tokens",
            "output_tokens",
            "token_usage_status",
        ],
    )
    redaction = obj(
        {
            "policy_snapshot_digest": ref("sha256"),
            "unknown_fields_dropped": ref("nonnegative_count"),
            "omitted_category_codes": arr(
                {
                    "enum": [
                        "ABSOLUTE_PATH",
                        "COMMAND_ARGUMENTS",
                        "ENVIRONMENT_RAW",
                        "FILE_BODY",
                        "IDENTITY",
                        "OUTPUT",
                        "PROMPT",
                        "RAW_SOURCE",
                        "REASONING",
                        "SECRET",
                        "STDERR",
                        "STDOUT",
                        "TOOL_ARGUMENTS",
                    ]
                },
                unique=True,
            ),
            "post_serialization_scan_passed": {"const": True},
        },
        [
            "policy_snapshot_digest",
            "unknown_fields_dropped",
            "omitted_category_codes",
            "post_serialization_scan_passed",
        ],
    )
    schema = artifact_schema(
        "public-run-event",
        2,
        "Public observed run event",
        {
            "event_uid": ref("event_uid"),
            "run_uid": ref("run_uid"),
            "event_type": {"enum": ["BINDING_CORRECTION", "RUN_OBSERVED"]},
            "occurred_at": ref("utc_z_timestamp"),
            "surface_class": ref("surface_class"),
            "actor_role": ref("actor_role"),
            "adapter_id": adapter_id(),
            "adapter_version": adapter_version(),
            "adapter_schema_digest": ref("sha256"),
            "mapping_policy_id": ref("urn_id"),
            "mapping_policy_digest": ref("sha256"),
            "trigger_kind": {"enum": ["MANUAL", "SCHEDULED"]},
            "run_status": {
                "enum": ["ABORTED", "BLOCKED", "FAILED", "PARTIAL", "SUCCESS", "UNKNOWN"]
            },
            "model_ref": nullable(safe_ref()),
            "reasoning_effort": nullable(
                {"enum": ["HIGH", "LOW", "MAX", "MEDIUM", "ULTRA", "UNKNOWN", "XHIGH"]}
            ),
            "metrics": metrics,
            "binding_state": {"enum": ["BOUND", "UNKNOWN"]},
            "skill_ref": skill_ref,
            "controlled_invocation": controlled_invocation,
            "unknown_reason_code": {
                "enum": [
                    "ADAPTER_NOT_APPROVED",
                    "BUNDLE_DIGEST_MISMATCH",
                    "CONTROLLED_INVOCATION_INVALID",
                    "IDENTITY_REFERENCE_INCOMPLETE",
                    "MAPPING_NOT_PROVABLE",
                    "REGISTRY_SNAPSHOT_MISMATCH",
                    "SURFACE_NOT_BINDING_ELIGIBLE",
                    "VERSION_DIGEST_MISMATCH",
                ]
            },
            "supersedes_event_uid": ref("event_uid"),
            "supersedes_event_digest": ref("sha256"),
            "redaction": redaction,
            "immutable": {"const": True},
            "event_digest": ref("sha256"),
        },
        [
            "event_uid",
            "run_uid",
            "event_type",
            "occurred_at",
            "surface_class",
            "actor_role",
            "adapter_id",
            "adapter_version",
            "adapter_schema_digest",
            "mapping_policy_id",
            "mapping_policy_digest",
            "trigger_kind",
            "run_status",
            "model_ref",
            "reasoning_effort",
            "metrics",
            "binding_state",
            "redaction",
            "immutable",
            "event_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {"properties": {"binding_state": {"const": "BOUND"}}, "required": ["binding_state"]},
            "then": {
                "required": ["skill_ref", "controlled_invocation"],
                "properties": {
                    "surface_class": {"enum": ["CODEX_AUTOMATION", "CODEX_CLI"]}
                },
                **forbid("unknown_reason_code"),
            },
        },
        {
            "if": {"properties": {"binding_state": {"const": "UNKNOWN"}}, "required": ["binding_state"]},
            "then": {"required": ["unknown_reason_code"], **forbid("skill_ref", "controlled_invocation")},
        },
        {
            "if": {"properties": {"event_type": {"const": "BINDING_CORRECTION"}}, "required": ["event_type"]},
            "then": {"required": ["supersedes_event_uid", "supersedes_event_digest"]},
        },
        {
            "if": {"properties": {"event_type": {"const": "RUN_OBSERVED"}}, "required": ["event_type"]},
            "then": forbid("supersedes_event_uid", "supersedes_event_digest"),
        },
        {
            "if": {"properties": {"surface_class": {"const": "CODEX_DESKTOP"}}, "required": ["surface_class"]},
            "then": {"properties": {"actor_role": {"enum": ["SUBAGENT", "USER"]}}},
        },
        {
            "if": {"properties": {"surface_class": {"const": "CODEX_AUTOMATION"}}, "required": ["surface_class"]},
            "then": {"properties": {"actor_role": {"const": "AUTOMATION"}}},
        },
        {
            "if": {"properties": {"surface_class": {"const": "CODEX_CLI"}}, "required": ["surface_class"]},
            "then": {"properties": {"actor_role": {"const": "CLI"}}},
        },
        {
            "if": {"properties": {"surface_class": {"enum": ["AGENTS", "CLAUDE"]}}, "required": ["surface_class"]},
            "then": {"properties": {"actor_role": {"const": "UNKNOWN"}}},
        },
    ]
    return schema


def source_coverage_receipt_schema() -> Dict[str, Any]:
    breakdown = obj(
        {
            "surface_class": ref("surface_class"),
            "actor_role": ref("actor_role"),
            "count": ref("nonnegative_count"),
        },
        ["surface_class", "actor_role", "count"],
    )
    unmapped = obj(
        {
            "reason_code": {
                "enum": [
                    "ACTOR_ROLE_NOT_PROVABLE",
                    "LEGACY_THREAD_SOURCE_MISSING",
                    "MAPPING_POLICY_NO_MATCH",
                    "SOURCE_RECORD_INCOMPLETE",
                ]
            },
            "count": ref("positive_count"),
        },
        ["reason_code", "count"],
    )
    source_fields = (
        "source_class",
        "inventory_uid",
        "inventory_digest",
        "inventory_completeness_status",
        "source_material_policy_id",
        "source_material_policy_digest",
    )
    run_fields = (
        "mapping_policy_id",
        "mapping_policy_digest",
        "input_record_count",
        "mapped_input_record_count",
        "unmapped_record_count",
        "policy_excluded_record_count",
        "quarantined_input_record_count",
        "observed_run_count",
        "projected_bound_run_count",
        "projected_unknown_run_count",
        "quarantined_run_count",
        "projected_event_count",
        "surface_breakdown",
        "unmapped_reasons",
        "baseline_action_code",
        "cutover_at",
        "public_safe_watermark_ref",
        "historical_public_run_event_count",
    )
    schema = artifact_schema(
        "source-coverage-receipt",
        1,
        "Source and runtime coverage receipt",
        {
            "receipt_uid": uid("cov"),
            "coverage_subject": {"enum": ["RUN_SURFACE", "SKILL_SOURCE"]},
            "coverage_state": {"enum": ["COVERED", "OFFLINE_GAP", "UNKNOWN", "UNOBSERVED"]},
            "adapter_scope": safe_ref(),
            "adapter_id": adapter_id(),
            "adapter_version": adapter_version(),
            "adapter_schema_digest": ref("sha256"),
            "observation_window_started_at": ref("utc_z_timestamp"),
            "observation_window_finished_at": ref("utc_z_timestamp"),
            "heartbeat_at": ref("utc_z_timestamp"),
            "reason_codes": arr(
                {
                    "enum": [
                        "ADAPTER_UNAVAILABLE",
                        "BASELINE_ONLY",
                        "CONTINUITY_GAP",
                        "INVENTORY_INCOMPLETE",
                        "OFFLINE_TTL_BREACH",
                        "QUARANTINED_RECORDS",
                        "SOURCE_UNOBSERVED",
                        "UNMAPPED_RECORDS",
                    ]
                },
                unique=True,
            ),
            "source_class": ref("source_class"),
            "inventory_uid": uid("sinv"),
            "inventory_digest": ref("sha256"),
            "inventory_completeness_status": {
                "enum": ["COMPLETE_AFTER_POLICY_EXCLUSIONS", "INCOMPLETE", "UNKNOWN"]
            },
            "source_material_policy_id": {"const": POLICY_PREFIX + "source-material:v1"},
            "source_material_policy_digest": ref("sha256"),
            "mapping_policy_id": ref("urn_id"),
            "mapping_policy_digest": ref("sha256"),
            "input_record_count": ref("nonnegative_count"),
            "mapped_input_record_count": ref("nonnegative_count"),
            "unmapped_record_count": ref("nonnegative_count"),
            "policy_excluded_record_count": ref("nonnegative_count"),
            "quarantined_input_record_count": ref("nonnegative_count"),
            "observed_run_count": ref("nonnegative_count"),
            "projected_bound_run_count": ref("nonnegative_count"),
            "projected_unknown_run_count": ref("nonnegative_count"),
            "quarantined_run_count": ref("nonnegative_count"),
            "projected_event_count": ref("nonnegative_count"),
            "surface_breakdown": arr(breakdown, unique=True),
            "unmapped_reasons": arr(unmapped, unique=True),
            "baseline_action_code": {"const": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"},
            "cutover_at": ref("utc_z_timestamp"),
            "public_safe_watermark_ref": safe_ref(),
            "historical_public_run_event_count": {"const": 0},
            "receipt_digest": ref("sha256"),
        },
        [
            "receipt_uid",
            "coverage_subject",
            "coverage_state",
            "adapter_scope",
            "adapter_id",
            "adapter_version",
            "adapter_schema_digest",
            "observation_window_started_at",
            "observation_window_finished_at",
            "heartbeat_at",
            "reason_codes",
            "receipt_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {"properties": {"coverage_subject": {"const": "SKILL_SOURCE"}}, "required": ["coverage_subject"]},
            "then": {"required": ["source_class"], **forbid(*run_fields)},
        },
        {
            "if": {"properties": {"coverage_subject": {"const": "RUN_SURFACE"}}, "required": ["coverage_subject"]},
            "then": {
                "required": [
                    "mapping_policy_id",
                    "mapping_policy_digest",
                    "input_record_count",
                    "mapped_input_record_count",
                    "unmapped_record_count",
                    "policy_excluded_record_count",
                    "quarantined_input_record_count",
                    "observed_run_count",
                    "projected_bound_run_count",
                    "projected_unknown_run_count",
                    "quarantined_run_count",
                    "projected_event_count",
                    "surface_breakdown",
                    "unmapped_reasons",
                ],
                **forbid(*source_fields),
            },
        },
        {
            "if": {
                "properties": {
                    "coverage_subject": {"const": "SKILL_SOURCE"},
                    "coverage_state": {"const": "COVERED"},
                },
                "required": ["coverage_subject", "coverage_state"],
            },
            "then": {
                "required": [
                    "inventory_uid",
                    "inventory_digest",
                    "inventory_completeness_status",
                    "source_material_policy_id",
                    "source_material_policy_digest",
                ],
                "properties": {
                    "inventory_completeness_status": {
                        "const": "COMPLETE_AFTER_POLICY_EXCLUSIONS"
                    }
                },
            },
        },
        {
            "if": {
                "properties": {
                    "coverage_subject": {"const": "SKILL_SOURCE"},
                    "coverage_state": {"enum": ["OFFLINE_GAP", "UNOBSERVED"]},
                },
                "required": ["coverage_subject", "coverage_state"],
            },
            "then": forbid(
                "inventory_uid",
                "inventory_digest",
                "inventory_completeness_status",
                "source_material_policy_id",
                "source_material_policy_digest",
            ),
        },
        {
            "if": {"required": ["baseline_action_code"]},
            "then": {
                "required": [
                    "cutover_at",
                    "public_safe_watermark_ref",
                    "historical_public_run_event_count",
                ],
                "properties": {
                    "coverage_subject": {"const": "RUN_SURFACE"},
                    "coverage_state": {"const": "UNKNOWN"},
                },
            },
        },
    ]
    return schema


def auto_receipt_schema() -> Dict[str, Any]:
    lane_result = obj(
        {
            "lane": {"enum": ["REGISTRY", "RUN_LOG"]},
            "status": {"enum": ["DEFERRED", "FAILED", "NO_CHANGE", "QUARANTINED", "SETTLED"]},
            "input_count": ref("nonnegative_count"),
            "published_count": ref("nonnegative_count"),
            "quarantined_count": ref("nonnegative_count"),
        },
        ["lane", "status", "input_count", "published_count", "quarantined_count"],
    )
    publication = obj(
        {
            "manifest_digest": ref("sha256"),
            "observed_remote_head": ref("git_object_id"),
        },
        ["manifest_digest", "observed_remote_head"],
    )
    schema = artifact_schema(
        "auto-receipt",
        2,
        "Auto execution receipt",
        {
            "receipt_uid": uid("ar"),
            "auto_transaction_uid": uid("atx"),
            "trigger_kind": {"enum": ["MANUAL", "SCHEDULED"]},
            "started_at": ref("utc_z_timestamp"),
            "finished_at": ref("utc_z_timestamp"),
            "execution_profile": obj(
                {
                    "model_ref": safe_ref(),
                    "reasoning_effort": {
                        "enum": ["HIGH", "LOW", "MAX", "MEDIUM", "ULTRA", "XHIGH"]
                    },
                },
                ["model_ref", "reasoning_effort"],
            ),
            "final_action": {"enum": ["DEFER", "NONE", "PUBLISH", "STOP"]},
            "overall_status": {
                "enum": [
                    "COALESCED_WITH_ACTIVE_RUN",
                    "DEFERRED_SINGLE_FLIGHT",
                    "FAILED",
                    "NO_CHANGE",
                    "PARTIAL",
                    "SUCCESS",
                ]
            },
            "settled_lanes": arr({"enum": ["REGISTRY", "RUN_LOG"]}, unique=True),
            "lane_results": arr(lane_result, min_items=2, max_items=2, unique=True),
            "publication": publication,
            "notification_receipt_digest": ref("sha256"),
            "reason_codes": arr(
                {
                    "enum": [
                        "BUNDLE_MISMATCH",
                        "CAPABILITY_GATE_FAILED",
                        "LOCK_BUSY",
                        "NO_CHANGES",
                        "NOTIFICATION_FAILED",
                        "PRIVACY_GATE_FAILED",
                        "REMOTE_HEAD_CHANGED",
                        "REMOTE_READBACK_FAILED",
                        "SOURCE_INCOMPLETE",
                    ]
                },
                unique=True,
            ),
            "receipt_digest": ref("sha256"),
        },
        [
            "receipt_uid",
            "auto_transaction_uid",
            "trigger_kind",
            "started_at",
            "finished_at",
            "execution_profile",
            "final_action",
            "overall_status",
            "settled_lanes",
            "lane_results",
            "reason_codes",
            "receipt_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {"properties": {"final_action": {"const": "PUBLISH"}}, "required": ["final_action"]},
            "then": {"required": ["publication"], "properties": {"settled_lanes": {"minItems": 1}}},
        },
        {
            "if": {
                "properties": {
                    "overall_status": {
                        "enum": ["COALESCED_WITH_ACTIVE_RUN", "DEFERRED_SINGLE_FLIGHT"]
                    }
                },
                "required": ["overall_status"],
            },
            "then": {"properties": {"final_action": {"const": "DEFER"}}, **forbid("publication")},
        },
        {
            "if": {"properties": {"overall_status": {"const": "NO_CHANGE"}}, "required": ["overall_status"]},
            "then": {"properties": {"final_action": {"const": "NONE"}}, **forbid("publication")},
        },
    ]
    return schema


def publication_manifest_schema() -> Dict[str, Any]:
    artifact = obj(
        {
            "artifact_uid": ref("typed_uid"),
            "artifact_schema_id": ref("urn_id"),
            "artifact_digest": ref("sha256"),
            "artifact_repo_path": ref("repo_relative_posix_path"),
        },
        ["artifact_uid", "artifact_schema_id", "artifact_digest", "artifact_repo_path"],
    )
    lane = obj(
        {
            "lane": {"enum": ["REGISTRY", "RUN_LOG"]},
            "lane_transaction_uid": uid("ltx"),
            "source_watermark_ref": safe_ref(),
            "artifact_count": ref("nonnegative_count"),
            "artifacts": arr(artifact, unique=True),
        },
        ["lane", "lane_transaction_uid", "source_watermark_ref", "artifact_count", "artifacts"],
    )
    gate = obj(
        {
            "gate_code": {
                "enum": [
                    "BUNDLE_DIGEST",
                    "EXPECTED_REMOTE_HEAD",
                    "LOCK_OWNERSHIP",
                    "PATH_BOUNDARY",
                    "POLICY_DIGEST",
                    "PRIVACY",
                ]
            },
            "status": {"const": "PASS"},
            "evidence_digest": ref("sha256"),
        },
        ["gate_code", "status", "evidence_digest"],
    )
    return artifact_schema(
        "publication-manifest",
        1,
        "Canonical publication transaction manifest",
        {
            "manifest_uid": uid("pub"),
            "auto_transaction_uid": uid("atx"),
            "trigger_kind": {"enum": ["MANUAL", "SCHEDULED"]},
            "created_at": ref("utc_z_timestamp"),
            "mechanism_srv_revision": ref("srv_revision"),
            "expected_remote_head": ref("git_object_id"),
            "settled_lanes": arr({"enum": ["REGISTRY", "RUN_LOG"]}, min_items=1, unique=True),
            "lane_manifests": arr(lane, min_items=1, max_items=2, unique=True),
            "shared_gates": arr(gate, min_items=6, max_items=6, unique=True),
            "manifest_digest": ref("sha256"),
        },
        [
            "manifest_uid",
            "auto_transaction_uid",
            "trigger_kind",
            "created_at",
            "mechanism_srv_revision",
            "expected_remote_head",
            "settled_lanes",
            "lane_manifests",
            "shared_gates",
            "manifest_digest",
        ],
    )


def notification_receipt_schema() -> Dict[str, Any]:
    schema = artifact_schema(
        "notification-receipt",
        3,
        "Public-safe notification receipt",
        {
            "receipt_uid": uid("nrc"),
            "notification_uid": uid("ntf"),
            "auto_transaction_uid": uid("atx"),
            "impact": {"enum": ["MAJOR", "MATERIAL", "ROUTINE"]},
            "notification_mode": {"const": "AUTOMATIC_NOTIFICATION_ONLY"},
            "timing": {"enum": ["NOT_REQUIRED", "POST_CONTAINMENT", "PRE_WRITE"]},
            "provider_code": {"enum": ["EMAIL_PROVIDER", "NONE"]},
            "provider_status": {"enum": ["FAILED", "NOT_REQUIRED", "SENT", "UNKNOWN"]},
            "recipient_ref": ref("recipient_ref"),
            "provider_receipt_ref": safe_ref(),
            "notification_policy_id": {"const": POLICY_PREFIX + "notification:v1"},
            "policy_snapshot_digest": ref("sha256"),
            "metadata_digest": ref("sha256"),
            "created_at": ref("utc_z_timestamp"),
            "sent_at": ref("utc_z_timestamp"),
            "failure_code": {
                "enum": [
                    "CREDENTIAL_UNAVAILABLE",
                    "PROVIDER_REJECTED",
                    "PROVIDER_TIMEOUT",
                    "RECEIPT_UNVERIFIED",
                ]
            },
            "approval_required": {"const": False},
            "owner_reply_required": {"const": False},
            "receipt_digest": ref("sha256"),
        },
        [
            "receipt_uid",
            "notification_uid",
            "auto_transaction_uid",
            "impact",
            "notification_mode",
            "timing",
            "provider_code",
            "provider_status",
            "recipient_ref",
            "notification_policy_id",
            "policy_snapshot_digest",
            "metadata_digest",
            "created_at",
            "approval_required",
            "owner_reply_required",
            "receipt_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {"properties": {"provider_status": {"const": "SENT"}}, "required": ["provider_status"]},
            "then": {
                "required": ["provider_receipt_ref", "sent_at"],
                "properties": {"provider_code": {"const": "EMAIL_PROVIDER"}},
                **forbid("failure_code"),
            },
        },
        {
            "if": {"properties": {"provider_status": {"const": "FAILED"}}, "required": ["provider_status"]},
            "then": {
                "required": ["failure_code"],
                "properties": {"provider_code": {"const": "EMAIL_PROVIDER"}},
                **forbid("provider_receipt_ref", "sent_at"),
            },
        },
        {
            "if": {"properties": {"provider_status": {"const": "UNKNOWN"}}, "required": ["provider_status"]},
            "then": {
                "required": ["failure_code"],
                "properties": {
                    "provider_code": {"const": "EMAIL_PROVIDER"},
                    "failure_code": {"const": "RECEIPT_UNVERIFIED"},
                },
                **forbid("provider_receipt_ref", "sent_at"),
            },
        },
        {
            "if": {"properties": {"provider_status": {"const": "NOT_REQUIRED"}}, "required": ["provider_status"]},
            "then": {
                "properties": {
                    "timing": {"const": "NOT_REQUIRED"},
                    "provider_code": {"const": "NONE"},
                },
                **forbid("provider_receipt_ref", "sent_at", "failure_code"),
            },
        },
        {
            "if": {
                "properties": {"timing": {"enum": ["POST_CONTAINMENT", "PRE_WRITE"]}},
                "required": ["timing"],
            },
            "then": {"properties": {"provider_code": {"const": "EMAIL_PROVIDER"}}},
        },
    ]
    return schema


def retention_receipt_schema() -> Dict[str, Any]:
    return artifact_schema(
        "retention-receipt",
        2,
        "Truthful retention execution receipt",
        {
            "receipt_uid": uid("rtr"),
            "retention_action_uid": uid("rta"),
            "auto_transaction_uid": uid("atx"),
            "executed_at": ref("utc_z_timestamp"),
            "cutoff_at": ref("utc_z_timestamp"),
            "clock_basis": {"const": "UTC_WALL_CLOCK"},
            "scope": {"enum": ["GIT_CURRENT_TREE", "MANAGED_RAW"]},
            "action": {
                "enum": [
                    "DELETE_OWNED_SEGMENT",
                    "KEEP",
                    "NO_CANDIDATE",
                    "OFFLINE_TTL_BREACH_CLEANUP",
                    "PRUNE_CURRENT_TREE",
                ]
            },
            "retention_policy_id": {"const": POLICY_PREFIX + "retention:v2"},
            "policy_snapshot_digest": ref("sha256"),
            "selected_count": ref("nonnegative_count"),
            "selected_bytes": ref("nonnegative_count"),
            "affected_count": ref("nonnegative_count"),
            "affected_bytes": ref("nonnegative_count"),
            "protected_candidate_count": {"const": 0},
            "legacy_candidate_count": {"const": 0},
            "reprojection_status": {
                "enum": ["FAILED_GAP_RECORDED", "NOT_APPLICABLE", "SUCCEEDED"]
            },
            "gap_code": {"enum": ["OFFLINE_TTL_BREACH", "RAW_EXPIRED_UNPUBLISHED"]},
            "offline_duration_seconds": ref("nonnegative_count"),
            "ttl_breach": {"type": "boolean"},
            "history_rewrite_performed": {"const": False},
            "hard_delete_claimed": {"const": False},
            "evidence_digest": ref("sha256"),
            "receipt_digest": ref("sha256"),
        },
        [
            "receipt_uid",
            "retention_action_uid",
            "auto_transaction_uid",
            "executed_at",
            "cutoff_at",
            "clock_basis",
            "scope",
            "action",
            "retention_policy_id",
            "policy_snapshot_digest",
            "selected_count",
            "selected_bytes",
            "affected_count",
            "affected_bytes",
            "protected_candidate_count",
            "legacy_candidate_count",
            "reprojection_status",
            "offline_duration_seconds",
            "ttl_breach",
            "history_rewrite_performed",
            "hard_delete_claimed",
            "evidence_digest",
            "receipt_digest",
        ],
    )


def migration_receipt_schema() -> Dict[str, Any]:
    breakdown = obj(
        {
            "surface_class": ref("surface_class"),
            "actor_role": ref("actor_role"),
            "count": ref("nonnegative_count"),
        },
        ["surface_class", "actor_role", "count"],
    )
    reason = obj(
        {
            "reason_code": {"const": "LEGACY_THREAD_SOURCE_MISSING"},
            "count": ref("positive_count"),
        },
        ["reason_code", "count"],
    )
    return artifact_schema(
        "migration-receipt",
        2,
        "No-historical-backfill baseline receipt",
        {
            "receipt_uid": uid("mgr"),
            "migration_uid": uid("mig"),
            "source_generation_uid": uid("gen"),
            "adapter_scope": safe_ref(),
            "adapter_id": adapter_id(),
            "adapter_version": adapter_version(),
            "adapter_schema_digest": ref("sha256"),
            "mapping_policy_id": ref("urn_id"),
            "mapping_policy_digest": ref("sha256"),
            "baseline_action_code": {"const": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"},
            "coverage_state": {"const": "UNKNOWN"},
            "cutover_at": ref("utc_z_timestamp"),
            "public_safe_watermark_ref": safe_ref(),
            "private_exact_cursor_stored": {"const": True},
            "input_record_count": {"const": 577},
            "mapped_input_record_count": {"const": 559},
            "unmapped_record_count": {"const": 18},
            "policy_excluded_record_count": {"const": 0},
            "quarantined_input_record_count": {"const": 0},
            "surface_breakdown": arr(breakdown, min_items=4, max_items=4, unique=True),
            "unmapped_reasons": arr(reason, min_items=1, max_items=1, unique=True),
            "historical_public_run_event_count": {"const": 0},
            "legacy_local_mutation_performed": {"const": False},
            "evidence_digest": ref("sha256"),
            "receipt_digest": ref("sha256"),
        },
        [
            "receipt_uid",
            "migration_uid",
            "source_generation_uid",
            "adapter_scope",
            "adapter_id",
            "adapter_version",
            "adapter_schema_digest",
            "mapping_policy_id",
            "mapping_policy_digest",
            "baseline_action_code",
            "coverage_state",
            "cutover_at",
            "public_safe_watermark_ref",
            "private_exact_cursor_stored",
            "input_record_count",
            "mapped_input_record_count",
            "unmapped_record_count",
            "policy_excluded_record_count",
            "quarantined_input_record_count",
            "surface_breakdown",
            "unmapped_reasons",
            "historical_public_run_event_count",
            "legacy_local_mutation_performed",
            "evidence_digest",
            "receipt_digest",
        ],
    )


def public_queue_envelope_schema() -> Dict[str, Any]:
    return artifact_schema(
        "public-queue-envelope",
        2,
        "Private public-safe queue envelope",
        {
            "envelope_uid": ref("envelope_uid"),
            "auto_transaction_uid": uid("atx"),
            "lane": {"enum": ["REGISTRY", "RUN_LOG"]},
            "artifact_schema_id": ref("urn_id"),
            "artifact_uid": ref("typed_uid"),
            "artifact_digest": ref("sha256"),
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "queue_state": {"enum": ["QUARANTINED", "READY", "SETTLED"]},
            "sealed_at": ref("utc_z_timestamp"),
            "retry_count": ref("nonnegative_count"),
            "envelope_digest": ref("sha256"),
        },
        [
            "envelope_uid",
            "auto_transaction_uid",
            "lane",
            "artifact_schema_id",
            "artifact_uid",
            "artifact_digest",
            "artifact_repo_path",
            "queue_state",
            "sealed_at",
            "retry_count",
            "envelope_digest",
        ],
    )


def watermark_schema() -> Dict[str, Any]:
    lane = obj(
        {
            "lane": {"enum": ["REGISTRY", "RUN_LOG"]},
            "source_generation_uid": uid("gen"),
            "cursor_token": {"type": "string", "minLength": 1, "maxLength": 4096},
            "public_watermark_ref": safe_ref(),
            "last_settled_manifest_digest": nullable(ref("sha256")),
            "last_settled_remote_head": nullable(ref("git_object_id")),
        },
        [
            "lane",
            "source_generation_uid",
            "cursor_token",
            "public_watermark_ref",
            "last_settled_manifest_digest",
            "last_settled_remote_head",
        ],
    )
    return artifact_schema(
        "watermark",
        2,
        "Private lane watermark state",
        {
            "watermark_uid": uid("wm"),
            "updated_at": ref("utc_z_timestamp"),
            "baseline_established": {"type": "boolean"},
            "lane_states": arr(lane, min_items=2, max_items=2, unique=True),
            "state_digest": ref("sha256"),
        },
        ["watermark_uid", "updated_at", "baseline_established", "lane_states", "state_digest"],
    )


def lock_state_schema() -> Dict[str, Any]:
    return artifact_schema(
        "lock-state",
        1,
        "Private global publisher lock state",
        {
            "lock_uid": uid("lck"),
            "owner_run_uid": ref("run_uid"),
            "generation": ref("positive_count"),
            "status": {"enum": ["HELD", "RELEASED"]},
            "acquired_at": ref("utc_z_timestamp"),
            "heartbeat_at": ref("utc_z_timestamp"),
            "lease_expires_at": ref("utc_z_timestamp"),
            "released_at": ref("utc_z_timestamp"),
            "state_digest": ref("sha256"),
        },
        [
            "lock_uid",
            "owner_run_uid",
            "generation",
            "status",
            "acquired_at",
            "heartbeat_at",
            "lease_expires_at",
            "state_digest",
        ],
    )


def raw_segment_schema() -> Dict[str, Any]:
    return artifact_schema(
        "raw-segment",
        2,
        "Private managed raw segment metadata",
        {
            "segment_uid": uid("raw"),
            "source_generation_uid": uid("gen"),
            "adapter_id": adapter_id(),
            "adapter_version": adapter_version(),
            "persistence_mode": {"enum": ["DISABLED", "ENABLED_AFTER_CERTIFICATION", "TEST_ONLY"]},
            "managed_owned": {"const": True},
            "protected_or_legacy": {"const": False},
            "ownership_marker_digest": ref("sha256"),
            "payload_digest": ref("sha256"),
            "record_count": ref("nonnegative_count"),
            "byte_count": ref("nonnegative_count"),
            "created_at": ref("utc_z_timestamp"),
            "sealed_at": ref("utc_z_timestamp"),
            "expires_at": ref("utc_z_timestamp"),
            "segment_digest": ref("sha256"),
        },
        [
            "segment_uid",
            "source_generation_uid",
            "adapter_id",
            "adapter_version",
            "persistence_mode",
            "managed_owned",
            "protected_or_legacy",
            "ownership_marker_digest",
            "payload_digest",
            "record_count",
            "byte_count",
            "created_at",
            "sealed_at",
            "expires_at",
            "segment_digest",
        ],
    )


def public_schemas() -> Dict[str, Dict[str, Any]]:
    return {
        "auto-receipt.schema.json": auto_receipt_schema(),
        "migration-receipt.schema.json": migration_receipt_schema(),
        "notification-receipt.schema.json": notification_receipt_schema(),
        "public-run-event.schema.json": public_run_event_schema(),
        "publication-manifest.schema.json": publication_manifest_schema(),
        "retention-receipt.schema.json": retention_receipt_schema(),
        "source-coverage-receipt.schema.json": source_coverage_receipt_schema(),
        "source-inventory.schema.json": source_inventory_schema(),
    }


def private_schemas() -> Dict[str, Dict[str, Any]]:
    return {
        "lock-state.schema.json": lock_state_schema(),
        "public-queue-envelope.schema.json": public_queue_envelope_schema(),
        "raw-segment.schema.json": raw_segment_schema(),
        "watermark.schema.json": watermark_schema(),
    }


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def schema_entry(path: Path, document: Mapping[str, Any], pointer: str, visibility: str) -> Dict[str, Any]:
    return {
        "id": document["$id"],
        "owner_plane": "AUTO",
        "visibility": visibility,
        "relative_path": path.relative_to(REPO_ROOT).as_posix(),
        "schema_sha256": hashlib.sha256(canonicalize_object(document)).hexdigest(),
        "self_digest_pointer": pointer,
    }


def generated_files() -> Dict[Path, bytes]:
    files: Dict[Path, bytes] = {}
    public_entries = []
    private_entries = []
    public = public_schemas()
    private = private_schemas()
    for filename, document in public.items():
        path = AUTO_DIR / "schemas" / "public" / filename
        files[path] = pretty(document)
        short = document["$id"][len(SCHEMA_PREFIX):]
        public_entries.append(schema_entry(path, document, PUBLIC_SELF_POINTERS[short], "PUBLIC"))
    for filename, document in private.items():
        path = AUTO_DIR / "schemas" / "private" / filename
        files[path] = pretty(document)
        short = document["$id"][len(SCHEMA_PREFIX):]
        private_entries.append(schema_entry(path, document, PRIVATE_SELF_POINTERS[short], "PRIVATE"))
    public_entries.sort(key=lambda entry: entry["id"].encode("ascii"))
    private_entries.sort(key=lambda entry: entry["id"].encode("ascii"))
    interface = {
        "status": "DRAFT_NON_ACTIVE",
        "activation_forbidden": True,
        "protocol_revision": PROTOCOL,
        "base_mechanism_git_object_id": BASE_MECHANISM_GIT_OBJECT_ID,
        "mechanism_interface_raw_sha256": MECHANISM_INTERFACE_RAW_SHA256,
        "auto_public_schema_count": len(public_entries),
        "auto_public_schema_entries": public_entries,
        "auto_private_schema_count": len(private_entries),
        "auto_private_schema_entries": private_entries,
        "complete_shared_schema_count_after_m0b": 29,
        "auto_private_schemas_in_shared_bundle": False,
        "canonicalization_entrypoint": "CodexSkills/governance/tools/canonical_json.py",
        "offline_validator_entrypoint": "CodexSkills/auto/tools/validate_auto.py",
        "next_phase": "MECHANISM_M0B",
    }
    files[AUTO_DIR / "draft-interface.json"] = pretty(interface)
    return files


def materialize(check: bool) -> int:
    mismatches = []
    for path, expected in generated_files().items():
        if check:
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(path.relative_to(REPO_ROOT).as_posix())
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(expected)
    if mismatches:
        print("AUTO_DRAFT_MISMATCH:" + ",".join(sorted(mismatches)), file=sys.stderr)
        return 2
    print("AUTO_DRAFT_BYTE_EQUIVALENT" if check else "AUTO_DRAFT_GENERATED_OK")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    return materialize(args.check)


if __name__ == "__main__":
    raise SystemExit(main())
