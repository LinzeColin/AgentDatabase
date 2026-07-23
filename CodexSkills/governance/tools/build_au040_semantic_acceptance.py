#!/usr/bin/env python3
"""Build the non-active Mechanism acceptance for the Auto AU-040 draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
AUTO_DRAFT_DIR = (
    REPO_ROOT / "CodexSkills" / "registry" / "auto" / "transport-draft"
)
AUTO_DRAFT_INTERFACE_PATH = AUTO_DRAFT_DIR / "draft-interface.json"
OUTPUT_INTERFACE = (
    GOVERNANCE_DIR / "au040" / "semantic-policy-acceptance.json"
)
SCHEMA_V2_DIR = GOVERNANCE_DIR / "schemas-v2"
POLICY_V2_DIR = GOVERNANCE_DIR / "policies-v2"
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

sys.path.insert(0, str(GOVERNANCE_DIR / "tools"))

from canonical_json import (  # noqa: E402
    canonicalize_object,
    parse_json_bytes,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
POLICY_PREFIX = "urn:linzecolin:agentdatabase:skillops:policy:"

PUBLIC_VALUE_SCHEMA_V1 = SCHEMA_PREFIX + "public-value-policy:v1"
PUBLIC_VALUE_SCHEMA_V2 = SCHEMA_PREFIX + "public-value-policy:v2"
RETENTION_SCHEMA_V2 = SCHEMA_PREFIX + "retention-policy:v2"
RETENTION_SCHEMA_V3 = SCHEMA_PREFIX + "retention-policy:v3"
PUBLIC_VALUE_POLICY_V1 = POLICY_PREFIX + "public-value:v1"
PUBLIC_VALUE_POLICY_V2 = POLICY_PREFIX + "public-value:v2"
RETENTION_POLICY_V2 = POLICY_PREFIX + "retention:v2"
RETENTION_POLICY_V3 = POLICY_PREFIX + "retention:v3"

CURRENT_CANDIDATE_GIT_OBJECT = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
CURRENT_CANDIDATE_BUNDLE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
CURRENT_CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
AUTO_DRAFT_GIT_OBJECT = (
    "sha1:3a133ee8a812bac6a577e93102df9981240659e1"
)
AUTO_DRAFT_INTERFACE_RAW_SHA256 = (
    "aa4d1b174d45b87424b81f0896c7a594e72f24bfdc16e4128c133ed543fb3831"
)
AUTO_DRAFT_INTERFACE_RELATIVE_PATH = (
    "CodexSkills/registry/auto/transport-draft/draft-interface.json"
)

AUTO_SCHEMA_CONTRACTS = (
    (
        SCHEMA_PREFIX + "daily-run-shard-manifest:v1",
        "e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337",
        "/manifest_digest",
    ),
    (
        SCHEMA_PREFIX + "publication-manifest:v2",
        "e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346",
        "/manifest_digest",
    ),
    (
        SCHEMA_PREFIX + "retention-receipt:v3",
        "81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45",
        "/receipt_digest",
    ),
    (
        SCHEMA_PREFIX + "run-event-index-entry:v1",
        "27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433",
        "/index_entry_digest",
    ),
)

PUBLIC_VALUE_ALLOWLIST_ADDITIONS = (
    "first_event_digest",
    "index_digest",
    "index_entry_digest",
    "last_event_digest",
    "previous_manifest_digest",
    "prior_artifact_digest",
    "prior_daily_manifest_digest",
    "retained_index_digest",
    "retention_receipt_digest",
    "shard_digest",
)


def _ref(name: str) -> Dict[str, str]:
    return {
        "$ref": (
            SCHEMA_PREFIX
            + "common-definitions:v1#/$defs/"
            + name
        )
    }


def _closed_object(
    properties: Mapping[str, Any],
    required: Sequence[str],
) -> Dict[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required),
        "type": "object",
    }


def _policy_schema(
    schema_id: str,
    title: str,
    properties: Mapping[str, Any],
    required: Sequence[str],
) -> Dict[str, Any]:
    return {
        "$id": schema_id,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": title,
        **_closed_object(properties, required),
    }


def public_value_policy_schema_v2() -> Dict[str, Any]:
    detector = _closed_object(
        {
            "action": {"const": "BLOCK"},
            "code": _ref("enum_code"),
            "kind": {
                "enum": [
                    "ABSOLUTE_PATH",
                    "EMAIL",
                    "HIGH_ENTROPY_FREE_STRING",
                    "IP_ADDRESS",
                    "PHONE_NUMBER",
                    "PRIVATE_KEY",
                    "SECRET_TOKEN",
                    "URI_CREDENTIAL",
                ]
            },
        },
        ["code", "kind", "action"],
    )
    recipient = _closed_object(
        {
            "actual_recipient_repo_external": {"const": True},
            "public_field": {"const": "recipient_ref"},
        },
        ["public_field", "actual_recipient_repo_external"],
    )
    field_names = {
        "items": {
            "pattern": "^[a-z][a-z0-9_]*$",
            "type": "string",
        },
        "minItems": 1,
        "type": "array",
        "uniqueItems": True,
    }
    return _policy_schema(
        PUBLIC_VALUE_SCHEMA_V2,
        "Public value policy v2 with exact digest-field allowlisting",
        {
            "allowed_high_entropy_field_names": field_names,
            "approved_digest_value_pattern": {
                "const": "LOWERCASE_SHA256_HEX_64"
            },
            "detectors": {
                "items": detector,
                "minItems": 8,
                "type": "array",
            },
            "field_name_allowlist_exact_match_required": {"const": True},
            "forbidden_field_names": field_names,
            "generic_digest_field_substitution_allowed": {"const": False},
            "low_entropy_sensitive_value_hash_publication_allowed": {
                "const": False
            },
            "max_public_string_length": _ref("positive_count"),
            "policy_id": {"const": PUBLIC_VALUE_POLICY_V2},
            "protocol_revision": _ref("protocol_revision"),
            "recipient_rule": recipient,
            "schema_version": {"const": PUBLIC_VALUE_SCHEMA_V2},
        },
        [
            "schema_version",
            "protocol_revision",
            "policy_id",
            "max_public_string_length",
            "forbidden_field_names",
            "allowed_high_entropy_field_names",
            "detectors",
            "recipient_rule",
            "approved_digest_value_pattern",
            "field_name_allowlist_exact_match_required",
            "generic_digest_field_substitution_allowed",
            "low_entropy_sensitive_value_hash_publication_allowed",
        ],
    )


def retention_policy_schema_v3() -> Dict[str, Any]:
    required_index_fields = {
        "items": {
            "enum": [
                "event_digest",
                "event_type",
                "event_uid",
                "first_published_at",
                "index_entry_digest",
                "line_number",
                "occurred_at",
                "part_number",
                "supersedes_event_digest",
                "supersedes_event_uid",
            ]
        },
        "minItems": 10,
        "maxItems": 10,
        "type": "array",
        "uniqueItems": True,
    }
    return _policy_schema(
        RETENTION_SCHEMA_V3,
        "Retention policy v3 for AU-040 active-tree evidence",
        {
            "boundary_at_retention_not_before_retained": {"const": True},
            "clock_basis": {"const": "UTC_WALL_CLOCK"},
            "current_tree_prune_exact_affected_artifacts_required": {
                "const": True
            },
            "current_tree_prune_receipt_required": {"const": True},
            "current_tree_prune_scope": {"const": "ACTIVE_TREE_ONLY"},
            "git_history_hard_erasure_claimed": {"const": False},
            "history_rewrite_allowed": {"const": False},
            "immutable_daily_shards": {"const": True},
            "managed_raw_max_hours": {"const": 72, "type": "integer"},
            "manifest_revision_reuse_allowed": {"const": False},
            "manifest_revisions_append_only": {"const": True},
            "offline_breach_code": {"const": "OFFLINE_TTL_BREACH"},
            "offline_gap_receipt_required": {"const": True},
            "offline_period_hard_guarantee_claimed": {"const": False},
            "offline_resume_first_cycle_receipt_required": {"const": True},
            "part_number_reuse_allowed": {"const": False},
            "persistent_managed_raw_default_enabled": {"const": False},
            "policy_id": {"const": RETENTION_POLICY_V3},
            "protected_root_classes": {
                "items": {
                    "enum": ["LEGACY_DATA", "RUN_SOURCE", "SKILL_SOURCE"]
                },
                "minItems": 3,
                "maxItems": 3,
                "type": "array",
                "uniqueItems": True,
            },
            "protected_root_delete_allowed": {"const": False},
            "protocol_revision": _ref("protocol_revision"),
            "prune_deadline_breach_code": {
                "const": "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
            },
            "prune_deadline_equal_is_on_time": {"const": True},
            "prune_deadline_hard_guarantee_claimed": {"const": False},
            "prune_deadline_hours_after_eligibility": {
                "const": 24,
                "type": "integer",
            },
            "prune_deadline_late_breach_receipt_required": {"const": True},
            "prune_enforcement_availability": {
                "const": "LOCAL_RUNTIME_AVAILABLE_ONLY"
            },
            "retained_index_full_event_payload_allowed": {"const": False},
            "retained_index_required_after_shard_prune": {"const": True},
            "retained_index_required_fields": required_index_fields,
            "retention_anchor_rule": {
                "const": "FIRST_PUBLISHED_AT_PLUS_365_ELAPSED_DAYS"
            },
            "retention_clock_schedule_independent": {"const": True},
            "retention_eligibility_condition": {
                "const": "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
            },
            "sanitized_public_active_days": {
                "const": 365,
                "type": "integer",
            },
            "sanitized_public_elapsed_seconds": {
                "const": 31536000,
                "type": "integer",
            },
            "sanitized_public_full_fidelity": {"const": True},
            "schema_version": {"const": RETENTION_SCHEMA_V3},
            "shard_calendar_timezone": {"const": "Australia/Sydney"},
            "ttl_enforcement_availability": {
                "const": "LOCAL_RUNTIME_AVAILABLE_ONLY"
            },
        },
        [
            "schema_version",
            "protocol_revision",
            "policy_id",
            "clock_basis",
            "persistent_managed_raw_default_enabled",
            "managed_raw_max_hours",
            "ttl_enforcement_availability",
            "offline_period_hard_guarantee_claimed",
            "offline_resume_first_cycle_receipt_required",
            "offline_gap_receipt_required",
            "offline_breach_code",
            "protected_root_classes",
            "protected_root_delete_allowed",
            "sanitized_public_active_days",
            "sanitized_public_elapsed_seconds",
            "sanitized_public_full_fidelity",
            "retention_anchor_rule",
            "retention_eligibility_condition",
            "boundary_at_retention_not_before_retained",
            "prune_deadline_hours_after_eligibility",
            "prune_deadline_equal_is_on_time",
            "prune_deadline_late_breach_receipt_required",
            "prune_deadline_breach_code",
            "prune_deadline_hard_guarantee_claimed",
            "prune_enforcement_availability",
            "current_tree_prune_scope",
            "current_tree_prune_receipt_required",
            "current_tree_prune_exact_affected_artifacts_required",
            "git_history_hard_erasure_claimed",
            "history_rewrite_allowed",
            "immutable_daily_shards",
            "part_number_reuse_allowed",
            "manifest_revisions_append_only",
            "manifest_revision_reuse_allowed",
            "retained_index_required_after_shard_prune",
            "retained_index_full_event_payload_allowed",
            "retained_index_required_fields",
            "shard_calendar_timezone",
            "retention_clock_schedule_independent",
        ],
    )


def _load_json(path: Path) -> Mapping[str, Any]:
    value = parse_json_bytes(path.read_bytes())
    if not isinstance(value, dict):
        raise ValueError(f"JSON_ROOT_NOT_OBJECT:{path}")
    return value


def _current_public_value_policy() -> Mapping[str, Any]:
    return _load_json(
        GOVERNANCE_DIR / "policies" / "public-value-policy.v1.json"
    )


def public_value_policy_v2() -> Dict[str, Any]:
    current = _current_public_value_policy()
    allowed = sorted(
        set(current["allowed_high_entropy_field_names"]).union(
            PUBLIC_VALUE_ALLOWLIST_ADDITIONS
        )
    )
    return {
        **current,
        "allowed_high_entropy_field_names": allowed,
        "approved_digest_value_pattern": "LOWERCASE_SHA256_HEX_64",
        "field_name_allowlist_exact_match_required": True,
        "generic_digest_field_substitution_allowed": False,
        "low_entropy_sensitive_value_hash_publication_allowed": False,
        "policy_id": PUBLIC_VALUE_POLICY_V2,
        "schema_version": PUBLIC_VALUE_SCHEMA_V2,
    }


def retention_policy_v3() -> Dict[str, Any]:
    return {
        "boundary_at_retention_not_before_retained": True,
        "clock_basis": "UTC_WALL_CLOCK",
        "current_tree_prune_exact_affected_artifacts_required": True,
        "current_tree_prune_receipt_required": True,
        "current_tree_prune_scope": "ACTIVE_TREE_ONLY",
        "git_history_hard_erasure_claimed": False,
        "history_rewrite_allowed": False,
        "immutable_daily_shards": True,
        "managed_raw_max_hours": 72,
        "manifest_revision_reuse_allowed": False,
        "manifest_revisions_append_only": True,
        "offline_breach_code": "OFFLINE_TTL_BREACH",
        "offline_gap_receipt_required": True,
        "offline_period_hard_guarantee_claimed": False,
        "offline_resume_first_cycle_receipt_required": True,
        "part_number_reuse_allowed": False,
        "persistent_managed_raw_default_enabled": False,
        "policy_id": RETENTION_POLICY_V3,
        "protected_root_classes": [
            "LEGACY_DATA",
            "RUN_SOURCE",
            "SKILL_SOURCE",
        ],
        "protected_root_delete_allowed": False,
        "protocol_revision": PROTOCOL,
        "prune_deadline_breach_code": (
            "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
        ),
        "prune_deadline_equal_is_on_time": True,
        "prune_deadline_hard_guarantee_claimed": False,
        "prune_deadline_hours_after_eligibility": 24,
        "prune_deadline_late_breach_receipt_required": True,
        "prune_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
        "retained_index_full_event_payload_allowed": False,
        "retained_index_required_after_shard_prune": True,
        "retained_index_required_fields": [
            "event_digest",
            "event_type",
            "event_uid",
            "first_published_at",
            "index_entry_digest",
            "line_number",
            "occurred_at",
            "part_number",
            "supersedes_event_digest",
            "supersedes_event_uid",
        ],
        "retention_anchor_rule": (
            "FIRST_PUBLISHED_AT_PLUS_365_ELAPSED_DAYS"
        ),
        "retention_clock_schedule_independent": True,
        "retention_eligibility_condition": (
            "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
        ),
        "sanitized_public_active_days": 365,
        "sanitized_public_elapsed_seconds": 31536000,
        "sanitized_public_full_fidelity": True,
        "schema_version": RETENTION_SCHEMA_V3,
        "shard_calendar_timezone": "Australia/Sydney",
        "ttl_enforcement_availability": "LOCAL_RUNTIME_AVAILABLE_ONLY",
    }


def _sha256(value: Mapping[str, Any]) -> str:
    return hashlib.sha256(canonicalize_object(value)).hexdigest()


def _validate_auto_draft_interface() -> Mapping[str, Any]:
    raw = AUTO_DRAFT_INTERFACE_PATH.read_bytes()
    observed = hashlib.sha256(raw).hexdigest()
    if observed != AUTO_DRAFT_INTERFACE_RAW_SHA256:
        raise ValueError(
            "AUTO_DRAFT_INTERFACE_RAW_DIGEST_MISMATCH:" + observed
        )
    interface = parse_json_bytes(raw)
    if not isinstance(interface, dict):
        raise ValueError("AUTO_DRAFT_INTERFACE_ROOT_INVALID")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("repository_bound") is not False
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("draft_paths_forbidden_in_candidate_manifest")
        is not True
        or interface.get("promotion_required_before_candidate_materialization")
        is not True
        or interface.get("required_mechanism_public_value_allowlist_additions")
        != list(PUBLIC_VALUE_ALLOWLIST_ADDITIONS)
    ):
        raise ValueError("AUTO_DRAFT_INTERFACE_CONTRACT_MISMATCH")
    observed_entries = {
        (
            entry.get("id"),
            entry.get("schema_sha256"),
            entry.get("self_digest_pointer"),
        )
        for entry in interface.get("draft_schema_entries", [])
    }
    if observed_entries != set(AUTO_SCHEMA_CONTRACTS):
        raise ValueError("AUTO_DRAFT_SCHEMA_SET_MISMATCH")
    for entry in interface["draft_schema_entries"]:
        relative = entry["draft_relative_path"]
        if (
            not relative.startswith(
                "CodexSkills/registry/auto/transport-draft/schemas/public/"
            )
            or ".." in relative.split("/")
        ):
            raise ValueError("AUTO_DRAFT_SCHEMA_PATH_INVALID:" + relative)
        path = REPO_ROOT.joinpath(*relative.split("/"))
        if not path.is_file() or path.is_symlink():
            raise ValueError("AUTO_DRAFT_SCHEMA_FILE_INVALID:" + relative)
        document = _load_json(path)
        if (
            document.get("$id") != entry["id"]
            or _sha256(document) != entry["schema_sha256"]
        ):
            raise ValueError(
                "AUTO_DRAFT_SCHEMA_PHYSICAL_DIGEST_MISMATCH:" + entry["id"]
            )
    current = interface.get("current_trusted_candidate", {})
    if (
        current.get("git_object_id") != CURRENT_CANDIDATE_GIT_OBJECT
        or current.get("bundle_digest") != CURRENT_CANDIDATE_BUNDLE_DIGEST
        or current.get("schema_count") != 29
        or current.get("policy_count") != 5
        or current.get("unchanged_by_this_draft") is not True
    ):
        raise ValueError("AUTO_DRAFT_CURRENT_CANDIDATE_MISMATCH")
    return interface


def semantic_policy_acceptance() -> Dict[str, Any]:
    auto_interface = _validate_auto_draft_interface()
    public_schema = public_value_policy_schema_v2()
    retention_schema = retention_policy_schema_v3()
    public_policy = public_value_policy_v2()
    retention_policy = retention_policy_v3()
    accepted_auto = []
    entries_by_id = {
        entry["id"]: entry
        for entry in auto_interface["draft_schema_entries"]
    }
    for schema_id, digest, pointer in sorted(AUTO_SCHEMA_CONTRACTS):
        source = entries_by_id[schema_id]
        accepted_auto.append(
            {
                "draft_relative_path": source["draft_relative_path"],
                "id": schema_id,
                "proposed_canonical_relative_path": (
                    source["proposed_canonical_relative_path"]
                ),
                "schema_sha256": digest,
                "self_digest_pointer": pointer,
            }
        )
    mechanism_schemas = [
        {
            "id": PUBLIC_VALUE_SCHEMA_V2,
            "relative_path": (
                "CodexSkills/governance/schemas-v2/"
                "public-value-policy.schema.json"
            ),
            "replaces_schema_id": PUBLIC_VALUE_SCHEMA_V1,
            "schema_sha256": _sha256(public_schema),
            "self_digest_pointer": None,
        },
        {
            "id": RETENTION_SCHEMA_V3,
            "relative_path": (
                "CodexSkills/governance/schemas-v2/"
                "retention-policy.schema.json"
            ),
            "replaces_schema_id": RETENTION_SCHEMA_V2,
            "schema_sha256": _sha256(retention_schema),
            "self_digest_pointer": None,
        },
    ]
    policies = [
        {
            "id": PUBLIC_VALUE_POLICY_V2,
            "policy_sha256": _sha256(public_policy),
            "relative_path": (
                "CodexSkills/governance/policies-v2/"
                "public-value-policy.v2.json"
            ),
            "replaces_policy_id": PUBLIC_VALUE_POLICY_V1,
            "schema_id": PUBLIC_VALUE_SCHEMA_V2,
        },
        {
            "id": RETENTION_POLICY_V3,
            "policy_sha256": _sha256(retention_policy),
            "relative_path": (
                "CodexSkills/governance/policies-v2/"
                "retention-policy.v3.json"
            ),
            "replaces_policy_id": RETENTION_POLICY_V2,
            "schema_id": RETENTION_SCHEMA_V3,
        },
    ]
    return {
        "accepted_auto_transport_schemas": accepted_auto,
        "activation_forbidden": True,
        "auto_draft_semantic_validator_production_eligible": False,
        "bundle_materialization_forbidden": True,
        "canonical_publication_permitted": False,
        "cross_artifact_semantic_gates": [
            {
                "code": "CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE",
            },
            {
                "code": "INDEX_EVENT_MANIFEST_CLOSURE",
            },
            {
                "code": "MANIFEST_PART_IMMUTABILITY",
            },
            {
                "code": "MANIFEST_PREDECESSOR_EXACT_CHAIN",
            },
            {
                "code": "PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE",
            },
            {
                "code": "RETENTION_ANCHOR_EXACT_365D",
            },
            {
                "code": "SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE",
            },
        ],
        "current_candidate": {
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "canonical_manifest_path": CURRENT_CANDIDATE_MANIFEST_PATH,
            "git_object_id": CURRENT_CANDIDATE_GIT_OBJECT,
            "policy_count": 5,
            "schema_count": 29,
            "unchanged_by_this_phase": True,
        },
        "mechanism_policy_entries": policies,
        "mechanism_policy_schema_entries": mechanism_schemas,
        "next_phase": "AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS",
        "owner_plane": "MECHANISM",
        "production_semantic_guard_codes_required": [
            "CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE",
            "INDEX_EVENT_MANIFEST_CLOSURE",
            "MANIFEST_PART_IMMUTABILITY",
            "MANIFEST_PREDECESSOR_EXACT_CHAIN",
            "PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE",
            "RETENTION_ANCHOR_EXACT_365D",
            "SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE",
        ],
        "promotion_contract": {
            "auto_schema_bytes_may_change_during_promotion": False,
            "draft_paths_forbidden_in_candidate_manifest": True,
            "exact_byte_auto_schema_promotion_permitted": True,
            "final_auto_schema_path": (
                "CodexSkills/registry/auto/schemas/public-v2"
            ),
            "mechanism_semantic_guard_consumption_required_before_"
            "runtime_integration": True,
        },
        "protocol_revision": PROTOCOL,
        "public_value_contract": {
            "approved_value_shape": "LOWERCASE_SHA256_HEX_64",
            "generic_digest_field_substitution_allowed": False,
            "low_entropy_sensitive_value_hash_publication_allowed": False,
            "required_allowlist_additions": list(
                PUBLIC_VALUE_ALLOWLIST_ADDITIONS
            ),
            "replacement_policy_id": PUBLIC_VALUE_POLICY_V2,
        },
        "repository_bound": False,
        "retention_contract": {
            "active_tree_days": 365,
            "active_tree_elapsed_seconds": 31536000,
            "boundary_is_retained": True,
            "deadline_equality_is_on_time": True,
            "hard_deadline_guarantee_claimed": False,
            "prune_deadline_hours": 24,
            "prune_eligibility": (
                "NOW_STRICTLY_GREATER_THAN_RETENTION_NOT_BEFORE"
            ),
            "receipt_path": (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "YYYY/MM/DD/retention-receipt-NNNN.json"
            ),
            "replacement_policy_id": RETENTION_POLICY_V3,
            "schedule_independent": True,
            "timezone": "Australia/Sydney",
        },
        "schema_version": (
            "urn:linzecolin:agentdatabase:skillops:"
            "interface:au040-semantic-policy-acceptance:v1"
        ),
        "source_auto_draft_trust": {
            "canonical_interface_path": AUTO_DRAFT_INTERFACE_RELATIVE_PATH,
            "expected_interface_object_id": (
                "sha256:" + AUTO_DRAFT_INTERFACE_RAW_SHA256
            ),
            "mode": "DRAFT_NON_ACTIVE",
            "verified_git_object_id": AUTO_DRAFT_GIT_OBJECT,
        },
        "status": "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED",
        "target_shared_set": {
            "added_schema_ids": [
                SCHEMA_PREFIX + "daily-run-shard-manifest:v1",
                SCHEMA_PREFIX + "run-event-index-entry:v1",
            ],
            "current_policy_count": 5,
            "current_schema_count": 29,
            "replaced_policy_ids": [
                PUBLIC_VALUE_POLICY_V1,
                RETENTION_POLICY_V2,
            ],
            "replaced_schema_ids": [
                SCHEMA_PREFIX + "publication-manifest:v1",
                PUBLIC_VALUE_SCHEMA_V1,
                SCHEMA_PREFIX + "retention-receipt:v2",
                RETENTION_SCHEMA_V2,
            ],
            "replacement_policy_ids": [
                PUBLIC_VALUE_POLICY_V2,
                RETENTION_POLICY_V3,
            ],
            "replacement_schema_ids": [
                SCHEMA_PREFIX + "publication-manifest:v2",
                PUBLIC_VALUE_SCHEMA_V2,
                SCHEMA_PREFIX + "retention-receipt:v3",
                RETENTION_SCHEMA_V3,
            ],
            "target_policy_count": 5,
            "target_schema_count": 31,
        },
    }


def outputs() -> Mapping[Path, Mapping[str, Any]]:
    _validate_auto_draft_interface()
    return {
        SCHEMA_V2_DIR / "public-value-policy.schema.json": (
            public_value_policy_schema_v2()
        ),
        SCHEMA_V2_DIR / "retention-policy.schema.json": (
            retention_policy_schema_v3()
        ),
        POLICY_V2_DIR / "public-value-policy.v2.json": (
            public_value_policy_v2()
        ),
        POLICY_V2_DIR / "retention-policy.v3.json": retention_policy_v3(),
        OUTPUT_INTERFACE: semantic_policy_acceptance(),
    }


def pretty_bytes(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def materialize(*, check: bool) -> None:
    if VERSION_PATH.exists():
        raise ValueError("AU040_ACCEPTANCE_ACTIVE_VERSION_FORBIDDEN")
    for path, value in outputs().items():
        expected = pretty_bytes(value)
        if check:
            if not path.is_file() or path.is_symlink():
                raise ValueError(f"AU040_ACCEPTANCE_OUTPUT_MISSING:{path}")
            if path.read_bytes() != expected:
                raise ValueError(f"AU040_ACCEPTANCE_OUTPUT_DRIFT:{path}")
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(expected)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    materialize(check=args.check)
    mode = "CHECKED" if args.check else "BUILT"
    print(
        "MECHANISM_AU040_SEMANTIC_ACCEPTANCE_"
        + mode
        + " current=29/5 target=31/5 active=false"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
