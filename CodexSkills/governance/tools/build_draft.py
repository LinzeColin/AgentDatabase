#!/usr/bin/env python3
"""Deterministically materialize the non-active Mechanism M0a contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from canonical_json import canonical_digest, canonicalize_object

GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
POLICY_PREFIX = "urn:linzecolin:agentdatabase:skillops:policy:"
PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
DRAFT_STATUS = "DRAFT_NON_ACTIVE"
DRAFT_SRV = "v0.0.0.3"
JSON_SCHEMA = "https://json-schema.org/draft/2020-12/schema"
COMMON_ID = SCHEMA_PREFIX + "common-definitions:v1"
BINDING_ID = SCHEMA_PREFIX + "skill-binding:v1"
EVAL_DIMENSION_CODES = (
    "EFFICIENCY",
    "MAINTAINABILITY",
    "NEGATIVE_CAPABILITY",
    "OUTCOME",
    "RELIABILITY",
    "ROUTING",
    "SAFETY_GOVERNANCE",
)
CORE_HARD_GATE_CODES = (
    "CRITICAL_CORRECTNESS",
    "MAJOR_NOTIFICATION_SENT",
    "OPTIMIZER_EVALUATOR_ISOLATED",
    "PERMISSION_BOUNDARY",
    "PROVENANCE_LICENSE_RESOLVED",
    "PUBLIC_PRIVACY",
    "REPLAYABLE",
    "ROLLBACK_AVAILABLE",
)
ACTOR_ROLE_CODES = (
    "USER",
    "AUTOMATION",
    "SUBAGENT",
    "CLI",
    "UNKNOWN",
)
AUTO_A1A_PUBLIC_DIGEST_FIELDS = (
    "adapter_schema_digest",
    "included_tree_digest",
    "mapping_policy_digest",
    "supersedes_event_digest",
)


def ref(name: str) -> Dict[str, str]:
    return {"$ref": f"{COMMON_ID}#/$defs/{name}"}


def obj(
    properties: Mapping[str, Any],
    required: Sequence[str] = (),
    *,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties),
    }
    if required:
        result["required"] = list(required)
    if description:
        result["description"] = description
    return result


def arr(items: Mapping[str, Any], *, min_items: int = 0, unique: bool = False) -> Dict[str, Any]:
    result: Dict[str, Any] = {"type": "array", "items": dict(items), "minItems": min_items}
    if unique:
        result["uniqueItems"] = True
    return result


def nullable(schema: Mapping[str, Any]) -> Dict[str, Any]:
    return {"anyOf": [dict(schema), {"type": "null"}]}


def schema_id(name: str, version: int = 1) -> str:
    return f"{SCHEMA_PREFIX}{name}:v{version}"


def schema_document(
    name: str,
    version: int,
    title: str,
    body: Mapping[str, Any],
    *,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {
        "$schema": JSON_SCHEMA,
        "$id": schema_id(name, version),
        "title": title,
    }
    if description:
        result["description"] = description
    result.update(body)
    return result


def artifact_properties(sid: str) -> Dict[str, Any]:
    return {
        "schema_version": {"const": sid},
        "protocol_revision": ref("protocol_revision"),
        "bundle_digest": ref("sha256"),
    }


def artifact_schema(
    name: str,
    version: int,
    title: str,
    properties: Mapping[str, Any],
    required: Sequence[str],
    *,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    sid = schema_id(name, version)
    merged = artifact_properties(sid)
    merged.update(properties)
    return schema_document(
        name,
        version,
        title,
        obj(merged, ["schema_version", "protocol_revision", "bundle_digest", *required]),
        description=description,
    )


def common_definitions() -> Dict[str, Any]:
    ulid = "[0-7][0-9A-HJKMNP-TV-Z]{25}"
    typed_uid = rf"^[a-z][a-z0-9]{{1,11}}_{ulid}$"
    prefixes = {
        "skill_identity_uid": "ski",
        "skill_instance_uid": "skinst",
        "skill_version_uid": "skv",
        "eval_profile_uid": "evp",
        "eval_run_uid": "evr",
        "scorecard_uid": "sc",
        "promotion_bundle_uid": "peb",
        "promotion_decision_uid": "prd",
        "iteration_transition_uid": "itr",
        "passport_uid": "spp",
        "graph_uid": "cpg",
        "event_uid": "evt",
        "envelope_uid": "env",
        "invocation_uid": "inv",
        "run_uid": "run",
    }
    defs: Dict[str, Any] = {
        "typed_uid": {"type": "string", "pattern": typed_uid},
        "sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"},
        "git_object_id": {
            "type": "string",
            "pattern": "^(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$",
        },
        "urn_id": {
            "type": "string",
            "pattern": (
                "^urn:linzecolin:agentdatabase:skillops:"
                "(?:schema|policy|protocol):[a-z0-9][a-z0-9-]*"
                "(?::[a-z0-9][a-z0-9-]*)*:v[1-9][0-9]*$"
            ),
            "maxLength": 240,
        },
        "protocol_revision": {"const": PROTOCOL},
        "srv_revision": {
            "type": "string",
            "pattern": "^v0\\.0\\.0\\.[1-9][0-9]*$",
        },
        "utc_z_timestamp": {
            "type": "string",
            "pattern": (
                "^[0-9]{4}-(?:0[1-9]|1[0-2])-"
                "(?:0[1-9]|[12][0-9]|3[01])T"
                "(?:[01][0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]"
                "\\.[0-9]{6}Z$"
            ),
            "format": "utc-z-timestamp-v1",
        },
        "calendar_date": {
            "type": "string",
            "pattern": "^[0-9]{4}-(?:0[1-9]|1[0-2])-(?:0[1-9]|[12][0-9]|3[01])$",
            "format": "calendar-date-v1",
        },
        "repo_relative_posix_path": {
            "type": "string",
            "minLength": 1,
            "maxLength": 4096,
            "format": "repo-relative-posix-path-v1",
        },
        "enum_code": {
            "type": "string",
            "pattern": "^[A-Z][A-Z0-9]*(?:_[A-Z0-9]+)*$",
            "maxLength": 96,
        },
        "nonnegative_count": {
            "type": "integer",
            "minimum": 0,
            "maximum": 9007199254740991,
        },
        "positive_count": {
            "type": "integer",
            "minimum": 1,
            "maximum": 9007199254740991,
        },
        "basis_points": {"type": "integer", "minimum": 0, "maximum": 10000},
        "signed_basis_points": {"type": "integer", "minimum": -10000, "maximum": 10000},
        "recipient_ref": {
            "type": "string",
            "pattern": "^[a-z][a-z0-9-]{2,63}$",
        },
        "lifecycle_status": {
            "enum": [
                "DISCOVERED", "REGISTERED", "QUARANTINED", "EVALUATING",
                "CHALLENGER", "CHAMPION", "DEPRECATED", "REVOKED", "UNKNOWN",
            ]
        },
        "source_class": {"enum": ["AGENTS", "CLAUDE", "CODEX_SYSTEM", "CODEX"]},
        "surface_class": {
            "enum": ["CODEX_DESKTOP", "CODEX_AUTOMATION", "CODEX_CLI", "CLAUDE", "AGENTS"]
        },
        "actor_role": {"enum": list(ACTOR_ROLE_CODES)},
    }
    for name, prefix in prefixes.items():
        defs[name] = {"type": "string", "pattern": rf"^{prefix}_{ulid}$"}
    return schema_document(
        "common-definitions",
        1,
        "SkillOps common definitions",
        {"$defs": defs},
        description="Closed scalar definitions shared by both ownership planes.",
    )


def binding_schema() -> Dict[str, Any]:
    skill_ref = obj(
        {
            "skill_identity_uid": ref("skill_identity_uid"),
            "skill_instance_uid": ref("skill_instance_uid"),
            "skill_version_uid": ref("skill_version_uid"),
            "content_digest": ref("sha256"),
            "tree_digest": ref("sha256"),
            "version_record_digest": ref("sha256"),
            "registry_snapshot_digest": ref("sha256"),
        },
        [
            "skill_identity_uid", "skill_instance_uid", "skill_version_uid",
            "content_digest", "tree_digest", "version_record_digest",
            "registry_snapshot_digest",
        ],
    )
    invocation = obj(
        {
            "invocation_uid": ref("invocation_uid"),
            "invocation_envelope_digest": ref("sha256"),
            "surface_class": {"enum": ["CODEX_CLI", "CODEX_AUTOMATION"]},
            "observed_at": ref("utc_z_timestamp"),
            "evidence_type": {"const": "CONTROLLED_INVOCATION_EXACT_VERSION"},
        },
        [
            "invocation_uid", "invocation_envelope_digest", "surface_class",
            "observed_at", "evidence_type",
        ],
    )
    body = obj(
        {
            "binding_state": {"enum": ["BOUND", "UNKNOWN"]},
            "skill_ref": skill_ref,
            "controlled_invocation": invocation,
            "unknown_reason_code": ref("enum_code"),
        },
        ["binding_state"],
    )
    body["allOf"] = [
        {
            "if": {"properties": {"binding_state": {"const": "BOUND"}}, "required": ["binding_state"]},
            "then": {"required": ["skill_ref", "controlled_invocation"], "not": {"required": ["unknown_reason_code"]}},
        },
        {
            "if": {"properties": {"binding_state": {"const": "UNKNOWN"}}, "required": ["binding_state"]},
            "then": {"required": ["unknown_reason_code"], "not": {"anyOf": [{"required": ["skill_ref"]}, {"required": ["controlled_invocation"]}]}},
        },
    ]
    return schema_document("skill-binding", 1, "Skill binding", body)


def policy_schemas() -> Dict[str, Dict[str, Any]]:
    def policy_base(name: str, version: int) -> Dict[str, Any]:
        return {
            "schema_version": {"const": schema_id(name, version)},
            "protocol_revision": ref("protocol_revision"),
            "policy_id": ref("urn_id"),
        }

    public_value = schema_document(
        "public-value-policy", 1, "Public value policy",
        obj(
            {
                **policy_base("public-value-policy", 1),
                "max_public_string_length": ref("positive_count"),
                "forbidden_field_names": arr({"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}, min_items=1, unique=True),
                "allowed_high_entropy_field_names": arr({"type": "string", "pattern": "^[a-z][a-z0-9_]*$"}, min_items=1, unique=True),
                "detectors": arr(
                    obj(
                        {
                            "code": ref("enum_code"),
                            "kind": {"enum": ["EMAIL", "PHONE_NUMBER", "IP_ADDRESS", "ABSOLUTE_PATH", "SECRET_TOKEN", "PRIVATE_KEY", "URI_CREDENTIAL", "HIGH_ENTROPY_FREE_STRING"]},
                            "action": {"const": "BLOCK"},
                        },
                        ["code", "kind", "action"],
                    ), min_items=1,
                ),
                "recipient_rule": obj(
                    {"public_field": {"const": "recipient_ref"}, "actual_recipient_repo_external": {"const": True}},
                    ["public_field", "actual_recipient_repo_external"],
                ),
            },
            ["schema_version", "protocol_revision", "policy_id", "max_public_string_length", "forbidden_field_names", "allowed_high_entropy_field_names", "detectors", "recipient_rule"],
        ),
    )
    exclusion = obj(
        {
            "rule_id": ref("enum_code"),
            "source_scope": {"enum": ["ALL", "AGENTS", "CLAUDE", "CODEX_SYSTEM", "CODEX"]},
            "pattern": {"type": "string", "minLength": 1, "maxLength": 256},
            "pattern_syntax": {"const": "POSIX_GLOB"},
            "reason_code": {"enum": ["VCS_METADATA", "SOURCE_OVERLAP", "CACHE", "OS_METADATA"]},
        },
        ["rule_id", "source_scope", "pattern", "pattern_syntax", "reason_code"],
    )
    source_material = schema_document(
        "source-material-policy", 1, "Source material policy",
        obj(
            {
                **policy_base("source-material-policy", 1),
                "exclusions": arr(exclusion, min_items=1),
                "other_dotfiles_excluded": {"const": False},
                "size_skip_allowed": {"const": False},
                "silent_skip_allowed": {"const": False},
                "exclusion_accounting_required": {"const": True},
                "excluded_file_count_and_bytes_required": {"const": True},
                "regular_files_only_in_content_digest": {"const": True},
                "symlink_alias_records_separate": {"const": True},
                "symlink_policy": obj(
                    {
                        "lstat_first": {"const": True},
                        "absolute_target_allowed": {"const": False},
                        "same_source_root_required": {"const": True},
                        "raw_target_public": {"const": False},
                        "public_target_field": {"const": "normalized_target_ref"},
                        "cycle_or_race_result": {"const": "INCOMPLETE"},
                    },
                    ["lstat_first", "absolute_target_allowed", "same_source_root_required", "raw_target_public", "public_target_field", "cycle_or_race_result"],
                ),
                "hard_failure_codes": arr(
                    {"enum": ["READ_ERROR", "STAT_ERROR", "PERMISSION_ERROR", "OVERSIZE_NON_POLICY", "SPECIAL_FILE", "SYMLINK_UNSAFE", "INVALID_PATH_ENCODING"]},
                    min_items=1, unique=True,
                ),
                "hard_failure_result": {"const": "INCOMPLETE"},
                "deletion_propagation_when_incomplete": {"const": "BLOCK"},
            },
            ["schema_version", "protocol_revision", "policy_id", "exclusions", "other_dotfiles_excluded", "size_skip_allowed", "silent_skip_allowed", "exclusion_accounting_required", "excluded_file_count_and_bytes_required", "regular_files_only_in_content_digest", "symlink_alias_records_separate", "symlink_policy", "hard_failure_codes", "hard_failure_result", "deletion_propagation_when_incomplete"],
        ),
    )
    retention = schema_document(
        "retention-policy", 2, "Retention policy",
        obj(
            {
                **policy_base("retention-policy", 2),
                "clock_basis": {"const": "UTC_WALL_CLOCK"},
                "persistent_managed_raw_default_enabled": {"const": False},
                "managed_raw_max_hours": {"type": "integer", "const": 72},
                "ttl_enforcement_availability": {"const": "LOCAL_RUNTIME_AVAILABLE_ONLY"},
                "offline_period_hard_guarantee_claimed": {"const": False},
                "offline_resume_first_cycle_receipt_required": {"const": True},
                "offline_gap_receipt_required": {"const": True},
                "offline_breach_code": {"const": "OFFLINE_TTL_BREACH"},
                "protected_root_classes": arr({"enum": ["SKILL_SOURCE", "RUN_SOURCE", "LEGACY_DATA"]}, min_items=3, unique=True),
                "protected_root_delete_allowed": {"const": False},
                "sanitized_public_active_days": {"type": "integer", "const": 365},
                "sanitized_public_full_fidelity": {"const": True},
                "git_history_hard_erasure_claimed": {"const": False},
            },
            ["schema_version", "protocol_revision", "policy_id", "clock_basis", "persistent_managed_raw_default_enabled", "managed_raw_max_hours", "ttl_enforcement_availability", "offline_period_hard_guarantee_claimed", "offline_resume_first_cycle_receipt_required", "offline_gap_receipt_required", "offline_breach_code", "protected_root_classes", "protected_root_delete_allowed", "sanitized_public_active_days", "sanitized_public_full_fidelity", "git_history_hard_erasure_claimed"],
        ),
    )
    notification = schema_document(
        "notification-policy", 1, "Notification policy",
        obj(
            {
                **policy_base("notification-policy", 1),
                "recipient_ref": ref("recipient_ref"),
                "automatic": {"const": True},
                "notification_only": {"const": True},
                "owner_reply_required": {"const": False},
                "owner_approval_required": {"const": False},
                "planned_major_provider_sent_before_write": {"const": True},
                "send_failure_blocks_planned_write": {"const": True},
                "emergency_containment_precedes_notification": {"const": True},
                "actual_recipient_mapping_repo_external": {"const": True},
            },
            ["schema_version", "protocol_revision", "policy_id", "recipient_ref", "automatic", "notification_only", "owner_reply_required", "owner_approval_required", "planned_major_provider_sent_before_write", "send_failure_blocks_planned_write", "emergency_containment_precedes_notification", "actual_recipient_mapping_repo_external"],
        ),
    )
    version = schema_document(
        "version-policy", 2, "Version and schedule policy",
        obj(
            {
                **policy_base("version-policy", 2),
                "srv_pattern": {"const": "^v0\\.0\\.0\\.[1-9][0-9]*$"},
                "srv_release_scopes": arr({"enum": ["MECHANISM", "SCHEMA", "POLICY", "REGISTRY"]}, min_items=4, unique=True),
                "srv_update_mode": {"const": "GLOBAL_ATOMIC_INCREMENT"},
                "srv_reuse_allowed": {"const": False},
                "srv_last_component_bounded": {"const": False},
                "impact_levels": arr({"enum": ["PATCH", "MINOR", "MAJOR"]}, min_items=3, unique=True),
                "major_trigger_codes": arr(ref("enum_code"), min_items=1, unique=True),
                "daily_transaction_uid_separate": {"const": True},
                "transaction_uid_kind": {"const": "AUTO_TRANSACTION_UID"},
                "timezone": {"const": "Australia/Sydney"},
                "daily_schedule_local": {"const": "04:15"},
                "sunday_forced_full": {"const": True},
                "late_start_rejected": {"const": False},
                "manual_uses_same_orchestrator": {"const": True},
                "first_active_requires_exact_bundle_digest": {"const": True},
            },
            ["schema_version", "protocol_revision", "policy_id", "srv_pattern", "srv_release_scopes", "srv_update_mode", "srv_reuse_allowed", "srv_last_component_bounded", "impact_levels", "major_trigger_codes", "daily_transaction_uid_separate", "transaction_uid_kind", "timezone", "daily_schedule_local", "sunday_forced_full", "late_start_rejected", "manual_uses_same_orchestrator", "first_active_requires_exact_bundle_digest"],
        ),
    )
    return {
        "public-value-policy": public_value,
        "source-material-policy": source_material,
        "retention-policy": retention,
        "notification-policy": notification,
        "version-policy": version,
    }


def entity_schemas() -> Dict[str, Dict[str, Any]]:
    provenance = obj(
        {
            "kind": {"enum": ["LOCAL_MANAGED", "UPSTREAM_GIT", "VENDORED", "UNKNOWN"]},
            "upstream_repo": nullable({"type": "string", "pattern": "^https://github\\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(?:\\.git)?$"}),
            "git_object_id": nullable(ref("git_object_id")),
            "license_state": {"enum": ["KNOWN_ALLOWED", "UNKNOWN", "DENIED"]},
            "license_id": nullable({"type": "string", "pattern": "^[A-Za-z0-9.+-]{1,64}$"}),
            "trust_tier": {"enum": ["LOCAL_TRUSTED", "PINNED_UPSTREAM", "UNVERIFIED", "QUARANTINED"]},
        },
        ["kind", "upstream_repo", "git_object_id", "license_state", "license_id", "trust_tier"],
    )
    permissions = obj(
        {
            "network": {"enum": ["NONE", "DECLARED", "UNKNOWN"]},
            "filesystem_write": {"enum": ["NONE", "WORKSPACE_ONLY", "DECLARED_EXTERNAL", "UNKNOWN"]},
            "external_side_effect": {"enum": ["NONE", "DECLARED", "UNKNOWN"]},
            "secrets": {"enum": ["NONE", "REFERENCE_ONLY", "UNKNOWN"]},
        },
        ["network", "filesystem_write", "external_side_effect", "secrets"],
    )
    identity = artifact_schema(
        "skill-identity", 1, "Skill identity",
        {
            "skill_identity_uid": ref("skill_identity_uid"),
            "srv_revision": ref("srv_revision"),
            "canonical_name": {"type": "string", "minLength": 1, "maxLength": 128},
            "summary": {"type": "string", "minLength": 1, "maxLength": 1000},
            "owner_ref": {"type": "string", "pattern": "^[a-z][a-z0-9-]{2,63}$"},
            "lifecycle_status": ref("lifecycle_status"),
            "capability_codes": arr(ref("enum_code"), unique=True),
            "applicability_manifest_digest": ref("sha256"),
            "input_contract_digest": ref("sha256"),
            "output_contract_digest": ref("sha256"),
            "instance_uids": arr(ref("skill_instance_uid"), unique=True),
            "created_at": ref("utc_z_timestamp"),
            "updated_at": ref("utc_z_timestamp"),
            "supersedes_identity_uid": nullable(ref("skill_identity_uid")),
        },
        ["skill_identity_uid", "srv_revision", "canonical_name", "summary", "owner_ref", "lifecycle_status", "capability_codes", "applicability_manifest_digest", "input_contract_digest", "output_contract_digest", "instance_uids", "created_at", "updated_at", "supersedes_identity_uid"],
    )
    instance = artifact_schema(
        "skill-instance", 1, "Skill instance",
        {
            "skill_instance_uid": ref("skill_instance_uid"),
            "skill_identity_uid": ref("skill_identity_uid"),
            "source_class": ref("source_class"),
            "source_relative_path": ref("repo_relative_posix_path"),
            "source_fingerprint_digest": ref("sha256"),
            "provenance": provenance,
            "permissions": permissions,
            "tool_codes": arr(ref("enum_code"), unique=True),
            "data_class_codes": arr(ref("enum_code"), unique=True),
            "first_seen_at": ref("utc_z_timestamp"),
            "last_seen_at": ref("utc_z_timestamp"),
            "parent_instance_uids": arr(ref("skill_instance_uid"), unique=True),
            "moved_from_instance_uid": nullable(ref("skill_instance_uid")),
            "forked_from_instance_uid": nullable(ref("skill_instance_uid")),
            "version_uids": arr(ref("skill_version_uid"), unique=True),
            "lifecycle_status": ref("lifecycle_status"),
        },
        ["skill_instance_uid", "skill_identity_uid", "source_class", "source_relative_path", "source_fingerprint_digest", "provenance", "permissions", "tool_codes", "data_class_codes", "first_seen_at", "last_seen_at", "parent_instance_uids", "moved_from_instance_uid", "forked_from_instance_uid", "version_uids", "lifecycle_status"],
    )
    dependency = obj(
        {
            "dependency_type": {"enum": ["SKILL", "TOOL", "RUNTIME", "DATASET"]},
            "reference": {"type": "string", "minLength": 1, "maxLength": 200},
            "resolved_digest": nullable(ref("sha256")),
            "required": {"type": "boolean"},
        },
        ["dependency_type", "reference", "resolved_digest", "required"],
    )
    version = artifact_schema(
        "skill-version", 1, "Skill version",
        {
            "skill_version_uid": ref("skill_version_uid"),
            "skill_instance_uid": ref("skill_instance_uid"),
            "srv_revision": ref("srv_revision"),
            "content_digest": ref("sha256"),
            "tree_digest": ref("sha256"),
            "metadata_digest": ref("sha256"),
            "dependency_manifest_digest": ref("sha256"),
            "permission_manifest_digest": ref("sha256"),
            "source_material_policy_id": {"const": POLICY_PREFIX + "source-material:v1"},
            "source_material_policy_digest": ref("sha256"),
            "source_observed_at": ref("utc_z_timestamp"),
            "git_object_id": nullable(ref("git_object_id")),
            "dependencies": arr(dependency),
            "permissions": permissions,
            "compatibility_codes": arr(ref("enum_code"), unique=True),
            "trust_tier": {"enum": ["LOCAL_TRUSTED", "PINNED_UPSTREAM", "UNVERIFIED", "QUARANTINED"]},
            "lifecycle_status": ref("lifecycle_status"),
            "eval_profile_uid": nullable(ref("eval_profile_uid")),
            "supersedes_version_uid": nullable(ref("skill_version_uid")),
            "created_at": ref("utc_z_timestamp"),
        },
        ["skill_version_uid", "skill_instance_uid", "srv_revision", "content_digest", "tree_digest", "metadata_digest", "dependency_manifest_digest", "permission_manifest_digest", "source_material_policy_id", "source_material_policy_digest", "source_observed_at", "git_object_id", "dependencies", "permissions", "compatibility_codes", "trust_tier", "lifecycle_status", "eval_profile_uid", "supersedes_version_uid", "created_at"],
    )
    lineage = artifact_schema(
        "identity-lineage-event", 1, "Identity lineage event",
        {
            "event_uid": ref("event_uid"),
            "event_type": {"enum": ["ALIAS_ADDED", "MERGED", "SPLIT", "SUPERSEDED", "QUARANTINED"]},
            "source_identity_uids": arr(ref("skill_identity_uid"), min_items=1, unique=True),
            "target_identity_uids": arr(ref("skill_identity_uid"), min_items=1, unique=True),
            "reason_codes": arr(ref("enum_code"), min_items=1, unique=True),
            "evidence_digests": arr(ref("sha256"), min_items=1, unique=True),
            "actor": {"const": "SKILLOPS_CONTROLLER"},
            "occurred_at": ref("utc_z_timestamp"),
            "event_digest": ref("sha256"),
        },
        ["event_uid", "event_type", "source_identity_uids", "target_identity_uids", "reason_codes", "evidence_digests", "actor", "occurred_at", "event_digest"],
    )
    return {
        "skill-identity": identity,
        "skill-instance": instance,
        "skill-version": version,
        "identity-lineage-event": lineage,
    }


def evaluation_schemas() -> Dict[str, Dict[str, Any]]:
    routing_sets = obj(
        {
            "positive_digest": ref("sha256"),
            "missed_trigger_digest": ref("sha256"),
            "false_trigger_digest": ref("sha256"),
            "conflict_digest": ref("sha256"),
            "abstention_digest": ref("sha256"),
        },
        [
            "positive_digest", "missed_trigger_digest", "false_trigger_digest",
            "conflict_digest", "abstention_digest",
        ],
    )
    freshness_policy = obj(
        {
            "max_age_days": ref("positive_count"),
            "retest_triggers": arr(
                {
                    "enum": [
                        "SKILL_CHANGE", "MODEL_CHANGE", "TOOL_CHANGE",
                        "DEPENDENCY_CHANGE", "INCIDENT", "SCORE_DRIFT",
                        "POLICY_CHANGE", "DATASET_CHANGE", "EVALUATOR_CHANGE",
                    ]
                },
                min_items=1,
                unique=True,
            ),
        },
        ["max_age_days", "retest_triggers"],
    )
    eval_profile = artifact_schema(
        "eval-profile", 1, "Evaluation profile",
        {
            "eval_profile_uid": ref("eval_profile_uid"),
            "skill_identity_uid": ref("skill_identity_uid"),
            "srv_revision": ref("srv_revision"),
            "risk_class": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            "dataset_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "evaluator_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "tool_manifest_digest": ref("sha256"),
            "policy_snapshot_digest": ref("sha256"),
            "routing_sets": routing_sets,
            "deterministic_check_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "confirmed_regression_manifest_digests": arr(ref("sha256"), unique=True),
            "judge_rubric_digest": nullable(ref("sha256")),
            "human_calibration_manifest_digest": nullable(ref("sha256")),
            "sealed_holdout_manifest_digest": ref("sha256"),
            "dimension_weights_bps": arr(
                obj({"dimension_code": {"enum": list(EVAL_DIMENSION_CODES)}, "weight_bps": ref("basis_points")}, ["dimension_code", "weight_bps"]),
                min_items=len(EVAL_DIMENSION_CODES),
            ),
            "hard_gate_codes": arr({"enum": list(CORE_HARD_GATE_CODES)}, min_items=len(CORE_HARD_GATE_CODES), unique=True),
            "minimum_sample_count": ref("positive_count"),
            "sealed_holdout_required": {"const": True},
            "optimizer_may_read_sealed_labels": {"const": False},
            "optimizer_may_mutate_evaluator": {"const": False},
            "optimizer_may_mutate_profile": {"const": False},
            "optimizer_may_mutate_promotion_controller": {"const": False},
            "freshness_policy": freshness_policy,
            "created_at": ref("utc_z_timestamp"),
            "updated_at": ref("utc_z_timestamp"),
            "supersedes_profile_uid": nullable(ref("eval_profile_uid")),
        },
        ["eval_profile_uid", "skill_identity_uid", "srv_revision", "risk_class", "dataset_manifest_digests", "evaluator_manifest_digests", "tool_manifest_digest", "policy_snapshot_digest", "routing_sets", "deterministic_check_manifest_digests", "confirmed_regression_manifest_digests", "judge_rubric_digest", "human_calibration_manifest_digest", "sealed_holdout_manifest_digest", "dimension_weights_bps", "hard_gate_codes", "minimum_sample_count", "sealed_holdout_required", "optimizer_may_read_sealed_labels", "optimizer_may_mutate_evaluator", "optimizer_may_mutate_profile", "optimizer_may_mutate_promotion_controller", "freshness_policy", "created_at", "updated_at", "supersedes_profile_uid"],
    )
    run_ref = obj(
        {"run_uid": ref("run_uid"), "event_digest": ref("sha256"), "event_bundle_digest": ref("sha256")},
        ["run_uid", "event_digest", "event_bundle_digest"],
    )
    model = obj(
        {
            "provider_code": ref("enum_code"),
            "requested_alias": nullable({"type": "string", "maxLength": 120}),
            "resolved_id": {"type": "string", "minLength": 1, "maxLength": 200},
            "observed_at": ref("utc_z_timestamp"),
        },
        ["provider_code", "requested_alias", "resolved_id", "observed_at"],
    )
    eval_run = artifact_schema(
        "eval-run", 1, "Evaluation run",
        {
            "eval_run_uid": ref("eval_run_uid"),
            "skill_version_uid": ref("skill_version_uid"),
            "eval_profile_uid": ref("eval_profile_uid"),
            "skill_version_record_digest": ref("sha256"),
            "eval_profile_digest": ref("sha256"),
            "dataset_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "evaluator_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "rubric_digest": nullable(ref("sha256")),
            "sealed_access_audit_digest": ref("sha256"),
            "tool_manifest_digest": ref("sha256"),
            "policy_snapshot_digest": ref("sha256"),
            "binding_state": {"const": "BOUND"},
            "controlled_invocation_envelope_digest": ref("sha256"),
            "run_event_refs": arr(run_ref, min_items=1),
            "model_snapshot": model,
            "environment_fingerprint_digest": ref("sha256"),
            "started_at": ref("utc_z_timestamp"),
            "finished_at": ref("utc_z_timestamp"),
            "status": {"enum": ["PASS", "FAIL", "INCOMPLETE", "QUARANTINED"]},
            "result_artifact_digests": arr(ref("sha256"), unique=True),
            "eval_run_digest": ref("sha256"),
        },
        ["eval_run_uid", "skill_version_uid", "eval_profile_uid", "skill_version_record_digest", "eval_profile_digest", "dataset_manifest_digests", "evaluator_manifest_digests", "rubric_digest", "sealed_access_audit_digest", "tool_manifest_digest", "policy_snapshot_digest", "binding_state", "controlled_invocation_envelope_digest", "run_event_refs", "model_snapshot", "environment_fingerprint_digest", "started_at", "finished_at", "status", "result_artifact_digests", "eval_run_digest"],
    )
    gate_result = obj(
        {"gate_code": {"enum": list(CORE_HARD_GATE_CODES)}, "passed": {"type": "boolean"}, "evidence_digest": ref("sha256")},
        ["gate_code", "passed", "evidence_digest"],
    )
    dimension = obj(
        {
            "dimension_code": {"enum": list(EVAL_DIMENSION_CODES)},
            "score_bps": ref("basis_points"),
            "sample_count": ref("nonnegative_count"),
            "coverage_bps": ref("basis_points"),
        },
        ["dimension_code", "score_bps", "sample_count", "coverage_bps"],
    )
    routing_result = obj(
        {
            "sample_count": ref("nonnegative_count"),
            "correct_count": ref("nonnegative_count"),
            "score_bps": ref("basis_points"),
        },
        ["sample_count", "correct_count", "score_bps"],
    )
    routing_results = obj(
        {
            "positive": routing_result,
            "missed_trigger": routing_result,
            "false_trigger": routing_result,
            "conflict": routing_result,
            "abstention": routing_result,
        },
        ["positive", "missed_trigger", "false_trigger", "conflict", "abstention"],
    )
    judge_calibration = obj(
        {
            "state": {"enum": ["NOT_USED", "CALIBRATED", "WEAK_ADVISORY_ONLY", "FAILED"]},
            "agreement_bps": nullable(ref("basis_points")),
            "bias_bps": nullable(ref("signed_basis_points")),
            "drift_bps": nullable(ref("basis_points")),
            "evidence_digest": nullable(ref("sha256")),
            "sole_decision_authority": {"const": False},
        },
        ["state", "agreement_bps", "bias_bps", "drift_bps", "evidence_digest", "sole_decision_authority"],
    )
    scorecard = artifact_schema(
        "scorecard", 1, "Skill scorecard",
        {
            "scorecard_uid": ref("scorecard_uid"),
            "skill_version_uid": ref("skill_version_uid"),
            "eval_profile_uid": ref("eval_profile_uid"),
            "eval_run_uid": ref("eval_run_uid"),
            "skill_version_record_digest": ref("sha256"),
            "eval_profile_digest": ref("sha256"),
            "model_snapshot_digest": ref("sha256"),
            "environment_fingerprint_digest": ref("sha256"),
            "dataset_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "evaluator_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "evaluated_at": ref("utc_z_timestamp"),
            "hard_gates": arr(gate_result, min_items=len(CORE_HARD_GATE_CODES)),
            "dimensions": arr(dimension, min_items=len(EVAL_DIMENSION_CODES)),
            "routing_results": routing_results,
            "judge_calibration": judge_calibration,
            "weighted_score_bps": ref("basis_points"),
            "promotion_eligible": {"type": "boolean"},
            "confidence_bps": ref("basis_points"),
            "coverage_bps": ref("basis_points"),
            "freshness_state": {"enum": ["FRESH", "STALE", "UNKNOWN"]},
            "freshness_valid_until": nullable(ref("calendar_date")),
            "critical_incident_count": ref("nonnegative_count"),
            "critical_incident_evidence_digests": arr(ref("sha256"), unique=True),
            "evidence_bundle_digest": ref("sha256"),
            "scorecard_digest": ref("sha256"),
        },
        ["scorecard_uid", "skill_version_uid", "eval_profile_uid", "eval_run_uid", "skill_version_record_digest", "eval_profile_digest", "model_snapshot_digest", "environment_fingerprint_digest", "dataset_manifest_digests", "evaluator_manifest_digests", "evaluated_at", "hard_gates", "dimensions", "routing_results", "judge_calibration", "weighted_score_bps", "promotion_eligible", "confidence_bps", "coverage_bps", "freshness_state", "freshness_valid_until", "critical_incident_count", "critical_incident_evidence_digests", "evidence_bundle_digest", "scorecard_digest"],
    )
    return {"eval-profile": eval_profile, "eval-run": eval_run, "scorecard": scorecard}


def promotion_schemas() -> Dict[str, Dict[str, Any]]:
    evidence_ref = obj(
        {"schema_id": ref("urn_id"), "artifact_uid": ref("typed_uid"), "artifact_digest": ref("sha256")},
        ["schema_id", "artifact_uid", "artifact_digest"],
    )
    matrix_cell = obj(
        {
            "cell": {"enum": ["BASELINE", "MODEL_EFFECT", "SKILL_EFFECT", "INTERACTION"]},
            "skill_version_uid": ref("skill_version_uid"),
            "model_snapshot_digest": ref("sha256"),
            "eval_run_digest": ref("sha256"),
            "status": {"enum": ["PASS", "FAIL", "INCOMPLETE", "QUARANTINED"]},
        },
        ["cell", "skill_version_uid", "model_snapshot_digest", "eval_run_digest", "status"],
    )
    bundle = artifact_schema(
        "promotion-evidence-bundle", 1, "Promotion evidence bundle",
        {
            "promotion_bundle_uid": ref("promotion_bundle_uid"),
            "candidate_skill_version_uid": ref("skill_version_uid"),
            "baseline_skill_version_uid": nullable(ref("skill_version_uid")),
            "scorecard_refs": arr(evidence_ref, min_items=1),
            "eval_run_refs": arr(evidence_ref, min_items=1),
            "candidate_model_snapshot_digest": ref("sha256"),
            "baseline_model_snapshot_digest": ref("sha256"),
            "environment_fingerprint_digest": ref("sha256"),
            "tool_manifest_digest": ref("sha256"),
            "dataset_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "evaluator_manifest_digests": arr(ref("sha256"), min_items=1, unique=True),
            "rubric_digest": ref("sha256"),
            "policy_snapshot_digest": ref("sha256"),
            "causal_matrix": arr(matrix_cell, min_items=4),
            "shadow_evidence_digest": ref("sha256"),
            "canary_evidence_digest": ref("sha256"),
            "hard_gates_passed": {"type": "boolean"},
            "risk_tier": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            "known_risk_codes": arr(ref("enum_code"), unique=True),
            "rollback_target_version_uid": ref("skill_version_uid"),
            "notification_required": {"type": "boolean"},
            "notification_receipt_digest": nullable(ref("sha256")),
            "created_at": ref("utc_z_timestamp"),
            "actor": {"const": "SKILLOPS_PROMOTION_CONTROLLER"},
            "evidence_bundle_digest": ref("sha256"),
        },
        ["promotion_bundle_uid", "candidate_skill_version_uid", "baseline_skill_version_uid", "scorecard_refs", "eval_run_refs", "candidate_model_snapshot_digest", "baseline_model_snapshot_digest", "environment_fingerprint_digest", "tool_manifest_digest", "dataset_manifest_digests", "evaluator_manifest_digests", "rubric_digest", "policy_snapshot_digest", "causal_matrix", "shadow_evidence_digest", "canary_evidence_digest", "hard_gates_passed", "risk_tier", "known_risk_codes", "rollback_target_version_uid", "notification_required", "notification_receipt_digest", "created_at", "actor", "evidence_bundle_digest"],
    )
    decision = artifact_schema(
        "promotion-decision", 1, "Promotion decision",
        {
            "promotion_decision_uid": ref("promotion_decision_uid"),
            "srv_revision": ref("srv_revision"),
            "action": {"enum": ["PROMOTE", "REJECT", "ROLLBACK", "REVOKE"]},
            "stage": {"enum": ["STATIC_PASSED", "OFFLINE_EVAL", "SEALED_HOLDOUT", "SHADOW", "CANARY", "REVIEW_AND_NOTIFY", "CHAMPION", "MONITORING", "BLOCKED", "REJECTED", "ROLLED_BACK", "REVOKED"]},
            "impact": {"enum": ["PATCH", "MINOR", "MAJOR"]},
            "candidate_skill_version_uid": ref("skill_version_uid"),
            "previous_champion_version_uid": nullable(ref("skill_version_uid")),
            "resulting_champion_version_uid": nullable(ref("skill_version_uid")),
            "candidate_model_snapshot_digest": ref("sha256"),
            "baseline_model_snapshot_digest": nullable(ref("sha256")),
            "from_status": ref("lifecycle_status"),
            "to_status": ref("lifecycle_status"),
            "evidence_bundle_digest": ref("sha256"),
            "hard_gates_passed": {"type": "boolean"},
            "known_risk_codes": arr(ref("enum_code"), unique=True),
            "reason_codes": arr(ref("enum_code"), min_items=1, unique=True),
            "actor": {"const": "SKILLOPS_PROMOTION_CONTROLLER"},
            "major_change": {"type": "boolean"},
            "notification_receipt_digest": nullable(ref("sha256")),
            "notification_mode": {"enum": ["NOT_REQUIRED", "PRE_WRITE_SENT", "POST_CONTAINMENT_SENT"]},
            "owner_approval_required": {"const": False},
            "emergency_containment": {"type": "boolean"},
            "rollback_target_version_uid": nullable(ref("skill_version_uid")),
            "decided_at": ref("utc_z_timestamp"),
            "decision_digest": ref("sha256"),
        },
        ["promotion_decision_uid", "srv_revision", "action", "stage", "impact", "candidate_skill_version_uid", "previous_champion_version_uid", "resulting_champion_version_uid", "candidate_model_snapshot_digest", "baseline_model_snapshot_digest", "from_status", "to_status", "evidence_bundle_digest", "hard_gates_passed", "known_risk_codes", "reason_codes", "actor", "major_change", "notification_receipt_digest", "notification_mode", "owner_approval_required", "emergency_containment", "rollback_target_version_uid", "decided_at", "decision_digest"],
    )
    transition = artifact_schema(
        "iteration-transition", 1, "Controlled iteration transition",
        {
            "iteration_transition_uid": ref("iteration_transition_uid"),
            "from_skill_version_uid": ref("skill_version_uid"),
            "to_skill_version_uid": ref("skill_version_uid"),
            "phase": {"enum": ["PROPOSED", "STATIC_PASSED", "OFFLINE_EVAL", "SEALED_HOLDOUT", "SHADOW", "CANARY", "REVIEW_AND_NOTIFY", "CHAMPION", "MONITORING", "BLOCKED", "REJECTED", "ROLLED_BACK", "REVOKED"]},
            "experiment_matrix_digest": ref("sha256"),
            "optimizer_evaluator_isolation_digest": ref("sha256"),
            "side_effect_budget": ref("nonnegative_count"),
            "early_stop_codes": arr(ref("enum_code"), unique=True),
            "rollback_target_version_uid": ref("skill_version_uid"),
            "occurred_at": ref("utc_z_timestamp"),
            "transition_digest": ref("sha256"),
        },
        ["iteration_transition_uid", "from_skill_version_uid", "to_skill_version_uid", "phase", "experiment_matrix_digest", "optimizer_evaluator_isolation_digest", "side_effect_budget", "early_stop_codes", "rollback_target_version_uid", "occurred_at", "transition_digest"],
    )
    return {"promotion-evidence-bundle": bundle, "promotion-decision": decision, "iteration-transition": transition}


def derived_schemas() -> Dict[str, Dict[str, Any]]:
    passport_provenance = obj(
        {
            "source_class": ref("source_class"),
            "source_relative_path": ref("repo_relative_posix_path"),
            "content_digest": ref("sha256"),
            "tree_digest": ref("sha256"),
            "license_state": {"enum": ["KNOWN_ALLOWED", "UNKNOWN", "DENIED"]},
            "trust_tier": {"enum": ["LOCAL_TRUSTED", "PINNED_UPSTREAM", "UNVERIFIED", "QUARANTINED"]},
        },
        ["source_class", "source_relative_path", "content_digest", "tree_digest", "license_state", "trust_tier"],
    )
    passport_permissions = obj(
        {
            "tool_codes": arr(ref("enum_code"), unique=True),
            "network": {"enum": ["NONE", "DECLARED", "UNKNOWN"]},
            "filesystem_write": {"enum": ["NONE", "WORKSPACE_ONLY", "DECLARED_EXTERNAL", "UNKNOWN"]},
            "external_side_effect": {"enum": ["NONE", "DECLARED", "UNKNOWN"]},
            "data_class_codes": arr(ref("enum_code"), unique=True),
        },
        ["tool_codes", "network", "filesystem_write", "external_side_effect", "data_class_codes"],
    )
    passport = artifact_schema(
        "skill-passport", 1, "Skill passport",
        {
            "passport_uid": ref("passport_uid"),
            "skill_identity_uid": ref("skill_identity_uid"),
            "active_skill_version_uid": ref("skill_version_uid"),
            "canonical_name": {"type": "string", "minLength": 1, "maxLength": 128},
            "summary": {"type": "string", "minLength": 1, "maxLength": 1000},
            "owner_ref": {"type": "string", "pattern": "^[a-z][a-z0-9-]{2,63}$"},
            "lifecycle_status": ref("lifecycle_status"),
            "provenance": passport_provenance,
            "permissions": passport_permissions,
            "applicability_codes": arr(ref("enum_code"), unique=True),
            "negative_capability_codes": arr(ref("enum_code"), unique=True),
            "use_when_codes": arr(ref("enum_code"), unique=True),
            "do_not_use_when_codes": arr(ref("enum_code"), unique=True),
            "abstain_when_codes": arr(ref("enum_code"), unique=True),
            "risk_tier": {"enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
            "permission_summary_codes": arr(ref("enum_code"), unique=True),
            "scorecard_uid": ref("scorecard_uid"),
            "scorecard_digest": ref("sha256"),
            "weighted_score_bps": ref("basis_points"),
            "confidence_bps": ref("basis_points"),
            "coverage_bps": ref("basis_points"),
            "freshness_state": {"enum": ["FRESH", "STALE", "UNKNOWN"]},
            "freshness_valid_until": nullable(ref("calendar_date")),
            "last_evaluated_at": ref("utc_z_timestamp"),
            "champion_model_snapshot_digest": ref("sha256"),
            "known_failure_mode_codes": arr(ref("enum_code"), unique=True),
            "rollback_target_version_uid": ref("skill_version_uid"),
            "source_fact_digests": arr(ref("sha256"), min_items=1, unique=True),
            "generated_at": ref("utc_z_timestamp"),
            "passport_digest": ref("sha256"),
        },
        ["passport_uid", "skill_identity_uid", "active_skill_version_uid", "canonical_name", "summary", "owner_ref", "lifecycle_status", "provenance", "permissions", "applicability_codes", "negative_capability_codes", "use_when_codes", "do_not_use_when_codes", "abstain_when_codes", "risk_tier", "permission_summary_codes", "scorecard_uid", "scorecard_digest", "weighted_score_bps", "confidence_bps", "coverage_bps", "freshness_state", "freshness_valid_until", "last_evaluated_at", "champion_model_snapshot_digest", "known_failure_mode_codes", "rollback_target_version_uid", "source_fact_digests", "generated_at", "passport_digest"],
    )
    node = obj(
        {"uid": ref("typed_uid"), "node_type": {"enum": ["SKILL_IDENTITY", "SKILL_INSTANCE", "SKILL_VERSION", "CAPABILITY", "TOOL", "DATA_CLASS", "WRITE_SCOPE", "MODEL", "DATASET", "EVALUATOR"]}, "label_code": ref("enum_code"), "lifecycle_status": nullable(ref("lifecycle_status"))},
        ["uid", "node_type", "label_code", "lifecycle_status"],
    )
    edge = obj(
        {"from_uid": ref("typed_uid"), "to_uid": ref("typed_uid"), "edge_type": {"enum": ["PROVIDES", "DEPENDS_ON", "SUBSTITUTES", "OVERLAPS", "CONFLICTS_WITH", "CALLS", "REQUIRES_TOOL", "READS_DATA_CLASS", "PRODUCES", "CONSUMES", "WRITES_TO"]}, "evidence_digest": ref("sha256"), "confidence_bps": ref("basis_points")},
        ["from_uid", "to_uid", "edge_type", "evidence_digest", "confidence_bps"],
    )
    graph = artifact_schema(
        "capability-graph", 1, "Capability graph",
        {
            "graph_uid": ref("graph_uid"),
            "source_snapshot_digest": ref("sha256"),
            "nodes": arr(node),
            "edges": arr(edge),
            "node_count": ref("nonnegative_count"),
            "edge_count": ref("nonnegative_count"),
            "generated_at": ref("utc_z_timestamp"),
            "graph_digest": ref("sha256"),
        },
        ["graph_uid", "source_snapshot_digest", "nodes", "edges", "node_count", "edge_count", "generated_at", "graph_digest"],
    )
    return {"skill-passport": passport, "capability-graph": graph}


def transport_schemas() -> Dict[str, Dict[str, Any]]:
    envelope = artifact_schema(
        "artifact-envelope", 1, "Immutable artifact envelope",
        {
            "envelope_uid": ref("envelope_uid"),
            "artifact_schema_id": ref("urn_id"),
            "artifact_uid": ref("typed_uid"),
            "artifact_digest": ref("sha256"),
            "artifact_schema_digest": ref("sha256"),
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "immutable": {"const": True},
            "created_at": ref("utc_z_timestamp"),
            "envelope_digest": ref("sha256"),
        },
        ["envelope_uid", "artifact_schema_id", "artifact_uid", "artifact_digest", "artifact_schema_digest", "artifact_repo_path", "immutable", "created_at", "envelope_digest"],
    )
    schema_entry = obj(
        {
            "id": ref("urn_id"),
            "owner_plane": {"enum": ["MECHANISM", "AUTO"]},
            "relative_path": ref("repo_relative_posix_path"),
            "schema_version": ref("urn_id"),
            "schema_sha256": ref("sha256"),
            "compatibility": {"enum": ["EXACT_ONLY", "BACKWARD_COMPATIBLE"]},
            "self_digest_pointer": nullable({"type": "string", "pattern": "^/[a-z][a-z0-9_]*$"}),
        },
        ["id", "owner_plane", "relative_path", "schema_version", "schema_sha256", "compatibility", "self_digest_pointer"],
    )
    policy_entry = obj(
        {
            "id": ref("urn_id"),
            "owner_plane": {"const": "MECHANISM"},
            "relative_path": ref("repo_relative_posix_path"),
            "schema_id": ref("urn_id"),
            "policy_sha256": ref("sha256"),
            "compatibility": {"enum": ["EXACT_ONLY", "BACKWARD_COMPATIBLE"]},
        },
        ["id", "owner_plane", "relative_path", "schema_id", "policy_sha256", "compatibility"],
    )
    canonicalization = obj(
        {
            "scheme": {"const": "RFC8785_JCS"},
            "input_profile": {"const": "I_JSON"},
            "encoding": {"const": "UTF-8"},
            "unicode_normalization": {"const": "NONE"},
            "duplicate_keys": {"const": "REJECT"},
            "self_digest_exclusion": {"const": "EXACT_DECLARED_JSON_POINTER_ONLY"},
        },
        ["scheme", "input_profile", "encoding", "unicode_normalization", "duplicate_keys", "self_digest_exclusion"],
    )
    compatibility = obj(
        {
            "active_bundle_mode": {"const": "EXACT_DIGEST"},
            "accepted_predecessor_bundle_digests": arr(ref("sha256"), unique=True),
            "predecessor_acceptance_expires_at": nullable(ref("utc_z_timestamp")),
        },
        ["active_bundle_mode", "accepted_predecessor_bundle_digests", "predecessor_acceptance_expires_at"],
    )
    sid = schema_id("schema-bundle-manifest", 1)
    manifest = schema_document(
        "schema-bundle-manifest", 1, "Schema bundle manifest",
        obj(
            {
                "schema_version": {"const": sid},
                "protocol_revision": ref("protocol_revision"),
                "srv_revision": ref("srv_revision"),
                "canonicalization": canonicalization,
                "digest_algorithm": {"const": "SHA-256"},
                "test_vectors_digest": ref("sha256"),
                "schemas": arr(schema_entry, min_items=1),
                "schema_count": ref("positive_count"),
                "policies": arr(policy_entry, min_items=1),
                "policy_count": ref("positive_count"),
                "compatibility": compatibility,
                "bundle_digest": ref("sha256"),
            },
            ["schema_version", "protocol_revision", "srv_revision", "canonicalization", "digest_algorithm", "test_vectors_digest", "schemas", "schema_count", "policies", "policy_count", "compatibility", "bundle_digest"],
        ),
    )
    return {"artifact-envelope": envelope, "schema-bundle-manifest": manifest}


def all_schemas() -> Dict[str, Dict[str, Any]]:
    schemas = {
        "common-definitions": common_definitions(),
        "skill-binding": binding_schema(),
    }
    schemas.update(policy_schemas())
    schemas.update(entity_schemas())
    schemas.update(evaluation_schemas())
    schemas.update(promotion_schemas())
    schemas.update(derived_schemas())
    schemas.update(transport_schemas())
    if len(schemas) != 21:
        raise AssertionError(f"expected 21 Mechanism schemas, got {len(schemas)}")
    return schemas


def policy_instances() -> Dict[str, Tuple[str, Dict[str, Any]]]:
    public_id = POLICY_PREFIX + "public-value:v1"
    source_id = POLICY_PREFIX + "source-material:v1"
    retention_id = POLICY_PREFIX + "retention:v2"
    notification_id = POLICY_PREFIX + "notification:v1"
    version_id = POLICY_PREFIX + "version:v2"
    return {
        "public-value-policy.v1": (
            "public-value-policy",
            {
                "schema_version": schema_id("public-value-policy", 1),
                "protocol_revision": PROTOCOL,
                "policy_id": public_id,
                "max_public_string_length": 4096,
                "forbidden_field_names": ["absolute_path", "address", "command", "credential", "email", "full_name", "ip_address", "output", "password", "phone_number", "prompt", "raw", "reasoning", "secret", "stderr", "stdout", "token", "tool_arguments"],
                "allowed_high_entropy_field_names": [
                    "abstention_digest", "accepted_predecessor_bundle_digests",
                    "adapter_schema_digest",
                    "applicability_manifest_digest", "artifact_digest", "artifact_schema_digest",
                    "baseline_model_snapshot_digest", "bundle_digest", "candidate_model_snapshot_digest",
                    "canary_evidence_digest", "content_digest", "decision_digest",
                    "champion_model_snapshot_digest", "conflict_digest",
                    "controlled_invocation_envelope_digest",
                    "critical_incident_evidence_digests", "dataset_manifest_digests",
                    "confirmed_regression_manifest_digests",
                    "dependency_manifest_digest", "deterministic_check_manifest_digests",
                    "envelope_digest", "environment_fingerprint_digest", "evaluator_manifest_digests",
                    "eval_profile_digest", "eval_run_digest", "event_bundle_digest", "event_digest",
                    "evidence_bundle_digest", "evidence_digest", "evidence_digests",
                    "experiment_matrix_digest", "false_trigger_digest", "graph_digest",
                    "human_calibration_manifest_digest", "included_tree_digest",
                    "input_contract_digest", "inventory_digest", "invocation_envelope_digest",
                    "manifest_digest", "mapping_policy_digest",
                    "judge_rubric_digest", "metadata_digest", "missed_trigger_digest",
                    "model_snapshot_digest", "notification_receipt_digest",
                    "optimizer_evaluator_isolation_digest", "output_contract_digest",
                    "passport_digest", "permission_manifest_digest", "policy_sha256",
                    "policy_snapshot_digest", "receipt_digest", "registry_snapshot_digest",
                    "positive_digest",
                    "resolved_digest", "result_artifact_digests", "rubric_digest",
                    "schema_sha256", "scorecard_digest",
                    "sealed_access_audit_digest", "sealed_holdout_manifest_digest", "shadow_evidence_digest",
                    "skill_version_record_digest", "source_fingerprint_digest",
                    "source_fact_digests", "source_material_policy_digest", "source_snapshot_digest",
                    "supersedes_event_digest", "test_vectors_digest", "tool_manifest_digest", "transition_digest",
                    "tree_digest", "version_record_digest",
                ],
                "detectors": [
                    {"code": "PUBLIC_EMAIL_BLOCK", "kind": "EMAIL", "action": "BLOCK"},
                    {"code": "PUBLIC_PHONE_NUMBER_BLOCK", "kind": "PHONE_NUMBER", "action": "BLOCK"},
                    {"code": "PUBLIC_IP_ADDRESS_BLOCK", "kind": "IP_ADDRESS", "action": "BLOCK"},
                    {"code": "PUBLIC_ABSOLUTE_PATH_BLOCK", "kind": "ABSOLUTE_PATH", "action": "BLOCK"},
                    {"code": "PUBLIC_SECRET_TOKEN_BLOCK", "kind": "SECRET_TOKEN", "action": "BLOCK"},
                    {"code": "PUBLIC_PRIVATE_KEY_BLOCK", "kind": "PRIVATE_KEY", "action": "BLOCK"},
                    {"code": "PUBLIC_URI_CREDENTIAL_BLOCK", "kind": "URI_CREDENTIAL", "action": "BLOCK"},
                    {"code": "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK", "kind": "HIGH_ENTROPY_FREE_STRING", "action": "BLOCK"},
                ],
                "recipient_rule": {"public_field": "recipient_ref", "actual_recipient_repo_external": True},
            },
        ),
        "source-material-policy.v1": (
            "source-material-policy",
            {
                "schema_version": schema_id("source-material-policy", 1),
                "protocol_revision": PROTOCOL,
                "policy_id": source_id,
                "exclusions": [
                    {"rule_id": "EXCLUDE_ROOT_GIT_NODE", "source_scope": "ALL", "pattern": ".git", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_ROOT_GIT_CONTENT", "source_scope": "ALL", "pattern": ".git/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_GIT_NODE", "source_scope": "ALL", "pattern": "**/.git", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_GIT_CONTENT", "source_scope": "ALL", "pattern": "**/.git/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_HG_CONTENT", "source_scope": "ALL", "pattern": "**/.hg/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_SVN_CONTENT", "source_scope": "ALL", "pattern": "**/.svn/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "VCS_METADATA"},
                    {"rule_id": "EXCLUDE_CODEX_SYSTEM_OVERLAP", "source_scope": "CODEX", "pattern": ".system/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "SOURCE_OVERLAP"},
                    {"rule_id": "EXCLUDE_PYTHON_CACHE", "source_scope": "ALL", "pattern": "**/__pycache__/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "CACHE"},
                    {"rule_id": "EXCLUDE_PYTEST_CACHE", "source_scope": "ALL", "pattern": "**/.pytest_cache/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "CACHE"},
                    {"rule_id": "EXCLUDE_MYPY_CACHE", "source_scope": "ALL", "pattern": "**/.mypy_cache/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "CACHE"},
                    {"rule_id": "EXCLUDE_VENV", "source_scope": "ALL", "pattern": "**/.venv/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "CACHE"},
                    {"rule_id": "EXCLUDE_NODE_MODULES", "source_scope": "ALL", "pattern": "**/node_modules/**", "pattern_syntax": "POSIX_GLOB", "reason_code": "CACHE"},
                    {"rule_id": "EXCLUDE_DS_STORE", "source_scope": "ALL", "pattern": "**/.DS_Store", "pattern_syntax": "POSIX_GLOB", "reason_code": "OS_METADATA"},
                    {"rule_id": "EXCLUDE_THUMBS_DB", "source_scope": "ALL", "pattern": "**/Thumbs.db", "pattern_syntax": "POSIX_GLOB", "reason_code": "OS_METADATA"},
                ],
                "other_dotfiles_excluded": False,
                "size_skip_allowed": False,
                "silent_skip_allowed": False,
                "exclusion_accounting_required": True,
                "excluded_file_count_and_bytes_required": True,
                "regular_files_only_in_content_digest": True,
                "symlink_alias_records_separate": True,
                "symlink_policy": {
                    "lstat_first": True,
                    "absolute_target_allowed": False,
                    "same_source_root_required": True,
                    "raw_target_public": False,
                    "public_target_field": "normalized_target_ref",
                    "cycle_or_race_result": "INCOMPLETE",
                },
                "hard_failure_codes": ["READ_ERROR", "STAT_ERROR", "PERMISSION_ERROR", "OVERSIZE_NON_POLICY", "SPECIAL_FILE", "SYMLINK_UNSAFE", "INVALID_PATH_ENCODING"],
                "hard_failure_result": "INCOMPLETE",
                "deletion_propagation_when_incomplete": "BLOCK",
            },
        ),
        "retention-policy.v2": (
            "retention-policy",
            {
                "schema_version": schema_id("retention-policy", 2),
                "protocol_revision": PROTOCOL,
                "policy_id": retention_id,
                "clock_basis": "UTC_WALL_CLOCK",
                "persistent_managed_raw_default_enabled": False,
                "managed_raw_max_hours": 72,
                "ttl_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
                "offline_period_hard_guarantee_claimed": False,
                "offline_resume_first_cycle_receipt_required": True,
                "offline_gap_receipt_required": True,
                "offline_breach_code": "OFFLINE_TTL_BREACH",
                "protected_root_classes": ["SKILL_SOURCE", "RUN_SOURCE", "LEGACY_DATA"],
                "protected_root_delete_allowed": False,
                "sanitized_public_active_days": 365,
                "sanitized_public_full_fidelity": True,
                "git_history_hard_erasure_claimed": False,
            },
        ),
        "notification-policy.v1": (
            "notification-policy",
            {
                "schema_version": schema_id("notification-policy", 1),
                "protocol_revision": PROTOCOL,
                "policy_id": notification_id,
                "recipient_ref": "owner-primary",
                "automatic": True,
                "notification_only": True,
                "owner_reply_required": False,
                "owner_approval_required": False,
                "planned_major_provider_sent_before_write": True,
                "send_failure_blocks_planned_write": True,
                "emergency_containment_precedes_notification": True,
                "actual_recipient_mapping_repo_external": True,
            },
        ),
        "version-policy.v2": (
            "version-policy",
            {
                "schema_version": schema_id("version-policy", 2),
                "protocol_revision": PROTOCOL,
                "policy_id": version_id,
                "srv_pattern": "^v0\\.0\\.0\\.[1-9][0-9]*$",
                "srv_release_scopes": ["MECHANISM", "SCHEMA", "POLICY", "REGISTRY"],
                "srv_update_mode": "GLOBAL_ATOMIC_INCREMENT",
                "srv_reuse_allowed": False,
                "srv_last_component_bounded": False,
                "impact_levels": ["PATCH", "MINOR", "MAJOR"],
                "major_trigger_codes": [
                    "ACTIVE_BUNDLE_CHANGE",
                    "CHAMPION_TRANSITION",
                    "MODEL_PROVIDER_CHANGE",
                    "NOTIFICATION_POLICY_CHANGE",
                    "RETENTION_POLICY_CHANGE",
                    "SCHEMA_BREAKING_CHANGE",
                    "SOURCE_LAYOUT_CHANGE",
                ],
                "daily_transaction_uid_separate": True,
                "transaction_uid_kind": "AUTO_TRANSACTION_UID",
                "timezone": "Australia/Sydney",
                "daily_schedule_local": "04:15",
                "sunday_forced_full": True,
                "late_start_rejected": False,
                "manual_uses_same_orchestrator": True,
                "first_active_requires_exact_bundle_digest": True,
            },
        ),
    }


SELF_DIGEST_POINTERS = {
    "identity-lineage-event": "/event_digest",
    "eval-run": "/eval_run_digest",
    "scorecard": "/scorecard_digest",
    "promotion-evidence-bundle": "/evidence_bundle_digest",
    "promotion-decision": "/decision_digest",
    "iteration-transition": "/transition_digest",
    "skill-passport": "/passport_digest",
    "capability-graph": "/graph_digest",
    "artifact-envelope": "/envelope_digest",
    "schema-bundle-manifest": "/bundle_digest",
}


def canonicalization_vectors() -> Dict[str, Any]:
    cases = [
        {
            "id": "KEY_ORDER",
            "input_json": '{"b":1,"a":2}',
            "expected_canonical_json": '{"a":2,"b":1}',
        },
        {
            "id": "RFC_PRIMITIVES",
            "input_json": '{"numbers":[333333333.33333329,1E30,4.50,2e-3,0.000000000000000000000000001],"string":"\\u20ac$\\u000F\\u000aA\'\\u0042\\u0022\\u005c\\\\\\\"\\/","literals":[null,true,false]}',
            "expected_canonical_json": '{"literals":[null,true,false],"numbers":[333333333.3333333,1e+30,4.5,0.002,1e-27],"string":"€$\\u000f\\nA\'B\\\"\\\\\\\\\\\"/"}',
        },
        {
            "id": "UTF16_PROPERTY_ORDER",
            "input_json": '{"€":"Euro Sign","\\r":"Carriage Return","דּ":"Hebrew Letter Dalet With Dagesh","1":"One","😀":"Emoji: Grinning Face","\\u0080":"Control","ö":"Latin Small Letter O With Diaeresis"}',
            "expected_canonical_json": '{"\\r":"Carriage Return","1":"One","":"Control","ö":"Latin Small Letter O With Diaeresis","€":"Euro Sign","😀":"Emoji: Grinning Face","דּ":"Hebrew Letter Dalet With Dagesh"}',
        },
        {
            "id": "NO_UNICODE_NORMALIZATION",
            "input_json": '{"é":1,"é":2}',
            "expected_canonical_json": '{"é":2,"é":1}',
        },
    ]
    for case in cases:
        expected = case["expected_canonical_json"].encode("utf-8")
        case["expected_sha256"] = hashlib.sha256(expected).hexdigest()
    self_material = {"event_digest": "0" * 64, "payload": {"b": 1, "a": 2}}
    expected_material = b'{"payload":{"a":2,"b":1}}'
    negative = [
        {"id": "DUPLICATE_KEY", "input_json": '{"a":1,"a":2}', "error_code": "DUPLICATE_KEY"},
        {"id": "NAN", "input_json": '{"a":NaN}', "error_code": "NON_FINITE_NUMBER"},
        {"id": "INFINITY", "input_json": '{"a":Infinity}', "error_code": "NON_FINITE_NUMBER"},
        {"id": "LONE_SURROGATE", "input_json": '{"a":"\\ud800"}', "error_code": "LONE_SURROGATE"},
    ]
    return {
        "vector_set": "RFC8785_IJSON_V1",
        "cases": cases,
        "self_exclusion": {
            "input": self_material,
            "pointer": "/event_digest",
            "expected_canonical_json": expected_material.decode("utf-8"),
            "expected_sha256": hashlib.sha256(expected_material).hexdigest(),
        },
        "negative_cases": negative,
    }


def provenance() -> Dict[str, Any]:
    return {
        "upstream_repository": "https://github.com/cyberphone/json-canonicalization",
        "upstream_commit": "19d51d7fe467d4706a3ff08adf8a748f29fc21e0",
        "retrieved_date": "2026-07-23",
        "rfc_reference": "RFC 8785 Appendix G",
        "runtime_network_required": False,
        "vendored_files_modified": False,
        "files": [
            {"path": "python3/src/org/webpki/json/Canonicalize.py", "sha256": "644508c81fa4afa50e8f6c7626a8cb6ddbd9515b39128c55484222ad336fad35"},
            {"path": "python3/src/org/webpki/json/NumberToJson.py", "sha256": "b8f78dab5bd7cf32cc620df39db18c8a55c777fa8acb69294d1a4d6702ee7e2a"},
            {"path": "python3/src/org/webpki/json/LICENSE", "sha256": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30"},
            {"path": "python3/src/org/webpki/json/LICENSE.PSF", "sha256": "af99833f38f9849acc41e2ca1de50a3cb266e712713efa6f377bae4befb16482"},
        ],
        "wrapper_path": "CodexSkills/governance/tools/canonical_json.py",
    }


def pretty(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def generated_files() -> Dict[Path, bytes]:
    schemas = all_schemas()
    policies = policy_instances()
    vectors = canonicalization_vectors()
    vectors_digest = hashlib.sha256(canonicalize_object(vectors)).hexdigest()
    outputs: Dict[Path, bytes] = {}
    schema_entries = []
    for name, document in sorted(schemas.items(), key=lambda item: item[1]["$id"].encode("ascii")):
        version = int(document["$id"].rsplit(":v", 1)[1])
        filename = f"{name}.schema.json"
        relative = Path("schemas") / filename
        outputs[relative] = pretty(document)
        schema_entries.append(
            {
                "id": document["$id"],
                "owner_plane": "MECHANISM",
                "relative_path": f"CodexSkills/governance/{relative.as_posix()}",
                "schema_version": document["$id"],
                "schema_sha256": hashlib.sha256(canonicalize_object(document)).hexdigest(),
                "compatibility": "EXACT_ONLY",
                "self_digest_pointer": SELF_DIGEST_POINTERS.get(name),
            }
        )
    policy_entries = []
    for filename, (schema_name, instance) in sorted(policies.items(), key=lambda item: item[1][1]["policy_id"].encode("ascii")):
        relative = Path("policies") / f"{filename}.json"
        outputs[relative] = pretty(instance)
        policy_entries.append(
            {
                "id": instance["policy_id"],
                "owner_plane": "MECHANISM",
                "relative_path": f"CodexSkills/governance/{relative.as_posix()}",
                "schema_id": instance["schema_version"],
                "policy_sha256": hashlib.sha256(canonicalize_object(instance)).hexdigest(),
                "compatibility": "EXACT_ONLY",
            }
        )
    outputs[Path("test_vectors/canonicalization-v1.json")] = pretty(vectors)
    outputs[Path("test_vectors/canonicalization-v1.sha256")] = (vectors_digest + "  canonicalization-v1.json\n").encode("ascii")
    outputs[Path("vendor/json_canonicalization/PROVENANCE.json")] = pretty(provenance())
    auto_public_contracts = [
        {"id": schema_id("source-inventory", 1), "owner_plane": "AUTO", "self_digest_pointer": "/inventory_digest"},
        {"id": schema_id("public-run-event", 2), "owner_plane": "AUTO", "self_digest_pointer": "/event_digest"},
        {"id": schema_id("source-coverage-receipt", 1), "owner_plane": "AUTO", "self_digest_pointer": "/receipt_digest"},
        {"id": schema_id("auto-receipt", 2), "owner_plane": "AUTO", "self_digest_pointer": "/receipt_digest"},
        {"id": schema_id("publication-manifest", 1), "owner_plane": "AUTO", "self_digest_pointer": "/manifest_digest"},
        {"id": schema_id("notification-receipt", 3), "owner_plane": "AUTO", "self_digest_pointer": "/receipt_digest"},
        {"id": schema_id("retention-receipt", 2), "owner_plane": "AUTO", "self_digest_pointer": "/receipt_digest"},
        {"id": schema_id("migration-receipt", 2), "owner_plane": "AUTO", "self_digest_pointer": "/receipt_digest"},
    ]
    auto_public_contracts.sort(key=lambda entry: entry["id"].encode("ascii"))
    auto_public = [entry["id"] for entry in auto_public_contracts]
    auto_private = [
        schema_id("public-queue-envelope", 2), schema_id("watermark", 2),
        schema_id("lock-state", 1), schema_id("raw-segment", 2),
    ]
    interface = {
        "status": DRAFT_STATUS,
        "activation_forbidden": True,
        "target_srv": DRAFT_SRV,
        "task_pack_revision": "v0.0.0.2",
        "protocol_revision": PROTOCOL,
        "canonicalization": {
            "scheme": "RFC8785_JCS",
            "input_profile": "I_JSON",
            "encoding": "UTF-8",
            "unicode_normalization": "NONE",
            "duplicate_keys": "REJECT",
            "self_digest_exclusion": "EXACT_DECLARED_JSON_POINTER_ONLY",
            "test_vectors_digest": vectors_digest,
        },
        "mechanism_schema_entries": schema_entries,
        "mechanism_schema_count": len(schema_entries),
        "mechanism_policy_entries": policy_entries,
        "mechanism_policy_count": len(policy_entries),
        "auto_public_schema_ids_required_for_complete_bundle": sorted(auto_public, key=lambda value: value.encode("ascii")),
        "auto_public_schema_contracts_required_for_complete_bundle": auto_public_contracts,
        "auto_private_schema_ids_excluded_from_shared_bundle": sorted(auto_private, key=lambda value: value.encode("ascii")),
        "compatibility": {
            "v0.0.0.2": "AUDIT_BASELINE_NOT_CANONICALLY_PUBLISHABLE",
            "v0.0.0.3_first_active": "EXACT_PROTOCOL_AND_BUNDLE_DIGEST_ONLY",
            "accepted_predecessor_bundle_digests": [],
        },
        "complete_bundle_contract": {
            "schema_count": len(schema_entries) + len(auto_public_contracts),
            "policy_count": len(policy_entries),
            "extra_schema_ids_allowed": False,
            "auto_private_schemas_included": False,
        },
        "entrypoints": {
            "builder": "CodexSkills/governance/tools/build_draft.py",
            "canonicalization": "CodexSkills/governance/tools/canonical_json.py",
            "validator": "CodexSkills/governance/tools/validate_mechanism.py",
            "schema_set_lint_subcommand": "lint-schema-set",
        },
        "validator_runtime": {
            "python": ">=3.9,<3.14",
            "jsonschema": ">=4.25.1,<5",
            "referencing": ">=0.36.2,<1",
            "dependency_install_during_run": "FORBIDDEN",
            "network_reference_resolution": "FORBIDDEN",
            "unknown_schema_id": "FAIL_CLOSED",
        },
        "trust_bootstrap": {
            "tuple_fields": [
                "verified_git_object_id",
                "expected_bundle_digest",
                "canonical_manifest_path",
                "mode",
            ],
            "canonical_manifest_path": "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json",
            "modes": ["CANDIDATE", "ACTIVE"],
            "repo_self_report_is_trusted": False,
            "missing_external_state": "FAIL_CLOSED_REBOOTSTRAP_REQUIRED",
        },
        "binding_contract": {
            "schema_id": BINDING_ID,
            "run_event_states": ["BOUND", "UNKNOWN"],
            "coverage_only_states": ["UNOBSERVED", "OFFLINE_GAP"],
            "bound_required_objects": ["skill_ref", "controlled_invocation"],
            "bound_eval_eligible_surfaces": ["CODEX_AUTOMATION", "CODEX_CLI"],
            "unknown_forbids": ["skill_ref", "controlled_invocation", "eval_refs", "promotion_refs"],
            "published_event_mutation": "FORBIDDEN_SUPERSEDE_ONLY",
        },
        "actor_role_contract": {
            "allowed_codes": list(ACTOR_ROLE_CODES),
            "unknown_semantics": "OBSERVED_ACTOR_ROLE_NOT_PROVABLE",
            "initial_unknown_surfaces": ["AGENTS", "CLAUDE"],
            "unknown_is_binding_state": False,
            "unknown_legacy_code_allowed": False,
            "legacy_thread_source_missing_treatment": "UNMAPPED",
        },
        "public_value_contract": {
            "approved_auto_public_sha256_fields": list(AUTO_A1A_PUBLIC_DIGEST_FIELDS),
            "approved_value_shape": "LOWERCASE_SHA256_HEX_64",
            "generic_digest_field_substitution_allowed": False,
        },
        "run_surface_baseline_contract": {
            "action": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL",
            "input_count": 577,
            "mapped_count": 559,
            "unmapped_count": 18,
            "policy_excluded_count": 0,
            "quarantined_count": 0,
            "coverage_state": "UNKNOWN",
            "mapped_breakdown": [
                {"surface_class": "CODEX_AUTOMATION", "actor_role": "AUTOMATION", "count": 46},
                {"surface_class": "CODEX_CLI", "actor_role": "CLI", "count": 8},
                {"surface_class": "CODEX_DESKTOP", "actor_role": "SUBAGENT", "count": 329},
                {"surface_class": "CODEX_DESKTOP", "actor_role": "USER", "count": 176},
            ],
            "unmapped_reasons": [
                {"reason_code": "LEGACY_THREAD_SOURCE_MISSING", "count": 18}
            ],
            "historical_public_run_events": 0,
            "private_exact_cursor_required": True,
            "public_safe_watermark_ref_required": True,
            "post_cutover_windows_only": True,
        },
        "coverage_subject_contract": {
            "SKILL_SOURCE": {
                "inventory_ref_required_when_covered": True,
                "source_material_policy_required": True,
            },
            "RUN_SURFACE": {
                "inventory_or_tree_digest_forbidden": True,
                "adapter_identity_and_observation_window_required": True,
                "observed_projected_quarantined_counts_required": True,
            },
        },
        "consumer_first_contract": {
            "target_path": "OpenAIDatabase/data/run_logs/skills_runs/",
            "target_schema_id": schema_id("public-run-event", 2),
            "legacy_sibling_schema": "OpenAIDatabase/config/evaluation/task_run.schema.json",
            "required_change": "ROUTE_SKILLS_RUNS_TO_PUBLIC_RUN_EVENT_V2_WITHOUT_CHANGING_TASK_RUN_SIBLINGS",
            "owner_plane": "MECHANISM",
            "must_land_before_canonical_publish": True,
        },
        "next_phase": "AUTO_A1A",
    }
    outputs[Path("draft-interface.json")] = pretty(interface)
    return outputs


def materialize(check: bool) -> int:
    mismatches: List[str] = []
    for relative, expected in sorted(generated_files().items(), key=lambda item: item[0].as_posix()):
        path = GOVERNANCE_DIR / relative
        if check:
            if not path.is_file() or path.read_bytes() != expected:
                mismatches.append(relative.as_posix())
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)
    if mismatches:
        for mismatch in mismatches:
            print(f"GENERATED_MISMATCH:{mismatch}", file=sys.stderr)
        return 1
    print("DRAFT_GENERATED_OK" if not check else "DRAFT_BYTE_EQUIVALENT")
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    return materialize(check=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
