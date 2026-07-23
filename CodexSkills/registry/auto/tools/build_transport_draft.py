#!/usr/bin/env python3
"""Build/check the non-active Auto AU-040 transport schema draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.tools.canonical_json import canonicalize_object
from CodexSkills.registry.auto.tools.build_schemas import (
    POLICY_PREFIX,
    PROTOCOL,
    SCHEMA_PREFIX,
    arr,
    artifact_schema,
    forbid,
    nullable,
    obj,
    ref,
    uid,
)


DRAFT_DIR = AUTO_DIR / "transport-draft"
SCHEMA_DIR = DRAFT_DIR / "schemas" / "public"
OUTPUT_INTERFACE = DRAFT_DIR / "draft-interface.json"

CURRENT_CANDIDATE_GIT_OBJECT = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
CURRENT_CANDIDATE_BUNDLE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
CURRENT_CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)

DAILY_MANIFEST_ID = SCHEMA_PREFIX + "daily-run-shard-manifest:v1"
INDEX_ENTRY_ID = SCHEMA_PREFIX + "run-event-index-entry:v1"
PUBLICATION_V2_ID = SCHEMA_PREFIX + "publication-manifest:v2"
RETENTION_V3_ID = SCHEMA_PREFIX + "retention-receipt:v3"
PUBLIC_RUN_EVENT_ID = SCHEMA_PREFIX + "public-run-event:v2"
PUBLICATION_V1_ID = SCHEMA_PREFIX + "publication-manifest:v1"
RETENTION_V2_ID = SCHEMA_PREFIX + "retention-receipt:v2"

SELF_POINTERS = {
    DAILY_MANIFEST_ID: "/manifest_digest",
    INDEX_ENTRY_ID: "/index_entry_digest",
    PUBLICATION_V2_ID: "/manifest_digest",
    RETENTION_V3_ID: "/receipt_digest",
}

SCHEMA_FILENAMES = {
    DAILY_MANIFEST_ID: "daily-run-shard-manifest.schema.json",
    INDEX_ENTRY_ID: "run-event-index-entry.schema.json",
    PUBLICATION_V2_ID: "publication-manifest-v2.schema.json",
    RETENTION_V3_ID: "retention-receipt-v3.schema.json",
}

REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS = [
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
]

MAX_PART_BYTES = 20 * 1024 * 1024
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs/"
OBJECT_SERIALIZATION = "RFC8785_JCS_OBJECT"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"


def _daily_part_schema() -> Dict[str, Any]:
    receipt_fields = (
        "retention_receipt_path",
        "retention_receipt_uid",
        "retention_receipt_digest",
        "pruned_at",
    )
    part = obj(
        {
            "part_number": ref("positive_count"),
            "shard_name": {
                "type": "string",
                "pattern": "^part-[0-9]{4}\\.jsonl$",
            },
            "state": {"enum": ["ACTIVE", "PRUNED"]},
            "shard_digest": ref("sha256"),
            "shard_bytes": {
                "type": "integer",
                "minimum": 1,
                "maximum": MAX_PART_BYTES,
            },
            "record_count": ref("positive_count"),
            "index_name": {
                "type": "string",
                "pattern": "^index-[0-9]{4}\\.jsonl$",
            },
            "index_digest": ref("sha256"),
            "index_bytes": ref("positive_count"),
            "index_record_count": ref("positive_count"),
            "first_event_uid": ref("event_uid"),
            "first_event_digest": ref("sha256"),
            "first_occurred_at": ref("utc_z_timestamp"),
            "last_event_uid": ref("event_uid"),
            "last_event_digest": ref("sha256"),
            "last_occurred_at": ref("utc_z_timestamp"),
            "first_published_at": ref("utc_z_timestamp"),
            "retention_not_before": ref("utc_z_timestamp"),
            "retention_receipt_path": ref("repo_relative_posix_path"),
            "retention_receipt_uid": uid("rtr"),
            "retention_receipt_digest": ref("sha256"),
            "pruned_at": ref("utc_z_timestamp"),
        },
        [
            "part_number",
            "shard_name",
            "state",
            "shard_digest",
            "shard_bytes",
            "record_count",
            "index_name",
            "index_digest",
            "index_bytes",
            "index_record_count",
            "first_event_uid",
            "first_event_digest",
            "first_occurred_at",
            "last_event_uid",
            "last_event_digest",
            "last_occurred_at",
            "first_published_at",
            "retention_not_before",
        ],
    )
    part["allOf"] = [
        {
            "if": {
                "properties": {"state": {"const": "ACTIVE"}},
                "required": ["state"],
            },
            "then": forbid(*receipt_fields),
        },
        {
            "if": {
                "properties": {"state": {"const": "PRUNED"}},
                "required": ["state"],
            },
            "then": {"required": list(receipt_fields)},
        },
    ]
    return part


def daily_manifest_schema() -> Dict[str, Any]:
    schema = artifact_schema(
        "daily-run-shard-manifest",
        1,
        "Append-only daily run shard manifest revision",
        {
            "manifest_uid": uid("drm"),
            "local_date": ref("calendar_date"),
            "timezone": {"const": "Australia/Sydney"},
            "record_schema_id": {"const": PUBLIC_RUN_EVENT_ID},
            "artifact_serialization": {"const": JSONL_SERIALIZATION},
            "max_part_bytes": {"const": MAX_PART_BYTES},
            "manifest_revision": ref("positive_count"),
            "previous_manifest_digest": nullable(ref("sha256")),
            "auto_transaction_uid": uid("atx"),
            "publication_transaction_at": ref("utc_z_timestamp"),
            "max_part_number": ref("positive_count"),
            "total_part_count": ref("positive_count"),
            "active_part_count": ref("nonnegative_count"),
            "pruned_part_count": ref("nonnegative_count"),
            "active_shard_bytes": ref("nonnegative_count"),
            "active_record_count": ref("nonnegative_count"),
            "retained_index_bytes": ref("positive_count"),
            "retained_index_record_count": ref("positive_count"),
            "parts": arr(_daily_part_schema(), min_items=1),
            "manifest_digest": ref("sha256"),
        },
        [
            "manifest_uid",
            "local_date",
            "timezone",
            "record_schema_id",
            "artifact_serialization",
            "max_part_bytes",
            "manifest_revision",
            "previous_manifest_digest",
            "auto_transaction_uid",
            "publication_transaction_at",
            "max_part_number",
            "total_part_count",
            "active_part_count",
            "pruned_part_count",
            "active_shard_bytes",
            "active_record_count",
            "retained_index_bytes",
            "retained_index_record_count",
            "parts",
            "manifest_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {
                "properties": {"manifest_revision": {"const": 1}},
                "required": ["manifest_revision"],
            },
            "then": {
                "properties": {"previous_manifest_digest": {"type": "null"}}
            },
        },
        {
            "if": {
                "properties": {"manifest_revision": {"minimum": 2}},
                "required": ["manifest_revision"],
            },
            "then": {
                "properties": {
                    "previous_manifest_digest": ref("sha256"),
                }
            },
        },
    ]
    return schema


def index_entry_schema() -> Dict[str, Any]:
    schema = artifact_schema(
        "run-event-index-entry",
        1,
        "Persistent public-safe run event index entry",
        {
            "event_uid": ref("event_uid"),
            "event_digest": ref("sha256"),
            "event_type": {"enum": ["BINDING_CORRECTION", "RUN_OBSERVED"]},
            "occurred_at": ref("utc_z_timestamp"),
            "part_number": ref("positive_count"),
            "line_number": ref("positive_count"),
            "first_published_at": ref("utc_z_timestamp"),
            "supersedes_event_uid": ref("event_uid"),
            "supersedes_event_digest": ref("sha256"),
            "index_entry_digest": ref("sha256"),
        },
        [
            "event_uid",
            "event_digest",
            "event_type",
            "occurred_at",
            "part_number",
            "line_number",
            "first_published_at",
            "index_entry_digest",
        ],
    )
    schema["allOf"] = [
        {
            "if": {
                "properties": {"event_type": {"const": "BINDING_CORRECTION"}},
                "required": ["event_type"],
            },
            "then": {
                "required": [
                    "supersedes_event_uid",
                    "supersedes_event_digest",
                ]
            },
        },
        {
            "if": {
                "properties": {"event_type": {"const": "RUN_OBSERVED"}},
                "required": ["event_type"],
            },
            "then": forbid(
                "supersedes_event_uid",
                "supersedes_event_digest",
            ),
        },
    ]
    return schema


def _publication_artifact_schema() -> Dict[str, Any]:
    new_fields = (
        "artifact_serialization",
        "artifact_digest",
        "artifact_bytes",
        "artifact_record_count",
    )
    prior_fields = (
        "prior_artifact_serialization",
        "prior_artifact_digest",
        "prior_artifact_bytes",
        "prior_artifact_record_count",
    )
    artifact = obj(
        {
            "artifact_uid": ref("typed_uid"),
            "artifact_operation": {"enum": ["DELETE", "PUT"]},
            "artifact_schema_id": ref("urn_id"),
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "artifact_serialization": {
                "enum": [OBJECT_SERIALIZATION, JSONL_SERIALIZATION]
            },
            "artifact_digest": ref("sha256"),
            "artifact_bytes": ref("positive_count"),
            "artifact_record_count": ref("positive_count"),
            "prior_artifact_serialization": {
                "enum": [OBJECT_SERIALIZATION, JSONL_SERIALIZATION]
            },
            "prior_artifact_digest": ref("sha256"),
            "prior_artifact_bytes": ref("positive_count"),
            "prior_artifact_record_count": ref("positive_count"),
        },
        [
            "artifact_uid",
            "artifact_operation",
            "artifact_schema_id",
            "artifact_repo_path",
        ],
    )
    artifact["allOf"] = [
        {
            "if": {
                "properties": {"artifact_operation": {"const": "PUT"}},
                "required": ["artifact_operation"],
            },
            "then": {
                "required": list(new_fields),
                **forbid(*prior_fields),
            },
        },
        {
            "if": {
                "properties": {"artifact_operation": {"const": "DELETE"}},
                "required": ["artifact_operation"],
            },
            "then": {
                "required": list(prior_fields),
                **forbid(*new_fields),
            },
        },
    ]
    return artifact


def publication_manifest_v2_schema() -> Dict[str, Any]:
    lane = obj(
        {
            "lane": {"enum": ["REGISTRY", "RUN_LOG"]},
            "lane_transaction_uid": uid("ltx"),
            "source_watermark_ref": {
                "type": "string",
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
            },
            "artifact_count": ref("nonnegative_count"),
            "artifacts": arr(
                _publication_artifact_schema(),
                min_items=1,
                unique=True,
            ),
        },
        [
            "lane",
            "lane_transaction_uid",
            "source_watermark_ref",
            "artifact_count",
            "artifacts",
        ],
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
        2,
        "Canonical publication transaction manifest with operation framing",
        {
            "manifest_uid": uid("pub"),
            "auto_transaction_uid": uid("atx"),
            "trigger_kind": {"enum": ["MANUAL", "SCHEDULED"]},
            "created_at": ref("utc_z_timestamp"),
            "mechanism_srv_revision": ref("srv_revision"),
            "expected_remote_head": ref("git_object_id"),
            "settled_lanes": arr(
                {"enum": ["REGISTRY", "RUN_LOG"]},
                min_items=1,
                unique=True,
            ),
            "lane_manifests": arr(
                lane,
                min_items=1,
                max_items=2,
                unique=True,
            ),
            "shared_gates": arr(
                gate,
                min_items=6,
                max_items=6,
                unique=True,
            ),
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


def _retention_affected_artifact_schema() -> Dict[str, Any]:
    return obj(
        {
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "artifact_schema_id": {"const": PUBLIC_RUN_EVENT_ID},
            "artifact_serialization": {"const": JSONL_SERIALIZATION},
            "prior_artifact_digest": ref("sha256"),
            "prior_artifact_bytes": ref("positive_count"),
            "prior_record_count": ref("positive_count"),
            "first_published_at": ref("utc_z_timestamp"),
            "retention_not_before": ref("utc_z_timestamp"),
            "prune_deadline_at": ref("utc_z_timestamp"),
            "retained_index_path": ref("repo_relative_posix_path"),
            "retained_index_digest": ref("sha256"),
            "prior_daily_manifest_digest": ref("sha256"),
        },
        [
            "artifact_repo_path",
            "artifact_schema_id",
            "artifact_serialization",
            "prior_artifact_digest",
            "prior_artifact_bytes",
            "prior_record_count",
            "first_published_at",
            "retention_not_before",
            "prune_deadline_at",
            "retained_index_path",
            "retained_index_digest",
            "prior_daily_manifest_digest",
        ],
    )


def retention_receipt_v3_schema() -> Dict[str, Any]:
    schema = artifact_schema(
        "retention-receipt",
        3,
        "Retention receipt with exact active-tree prune evidence",
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
            "retention_policy_id": {
                "const": POLICY_PREFIX + "retention:v3"
            },
            "policy_snapshot_digest": ref("sha256"),
            "selected_count": ref("nonnegative_count"),
            "selected_bytes": ref("nonnegative_count"),
            "affected_count": ref("nonnegative_count"),
            "affected_bytes": ref("nonnegative_count"),
            "affected_public_artifacts": arr(
                _retention_affected_artifact_schema(),
                min_items=1,
                unique=True,
            ),
            "prune_deadline_breached": {"type": "boolean"},
            "protected_candidate_count": {"const": 0},
            "legacy_candidate_count": {"const": 0},
            "reprojection_status": {
                "enum": [
                    "FAILED_GAP_RECORDED",
                    "NOT_APPLICABLE",
                    "SUCCEEDED",
                ]
            },
            "gap_code": {
                "enum": [
                    "OFFLINE_TTL_BREACH",
                    "RAW_EXPIRED_UNPUBLISHED",
                    "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH",
                ]
            },
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
    schema["allOf"] = [
        {
            "if": {
                "properties": {
                    "scope": {"const": "GIT_CURRENT_TREE"},
                    "action": {"const": "PRUNE_CURRENT_TREE"},
                },
                "required": ["scope", "action"],
            },
            "then": {
                "required": [
                    "affected_public_artifacts",
                    "prune_deadline_breached",
                ]
            },
            "else": forbid(
                "affected_public_artifacts",
                "prune_deadline_breached",
            ),
        },
        {
            "if": {
                "properties": {
                    "scope": {"const": "GIT_CURRENT_TREE"},
                    "action": {"const": "PRUNE_CURRENT_TREE"},
                    "prune_deadline_breached": {"const": True},
                },
                "required": [
                    "scope",
                    "action",
                    "prune_deadline_breached",
                ],
            },
            "then": {
                "required": ["gap_code"],
                "properties": {
                    "gap_code": {
                        "const": "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
                    }
                },
            },
        },
        {
            "if": {
                "properties": {
                    "scope": {"const": "GIT_CURRENT_TREE"},
                    "action": {"const": "PRUNE_CURRENT_TREE"},
                    "prune_deadline_breached": {"const": False},
                },
                "required": [
                    "scope",
                    "action",
                    "prune_deadline_breached",
                ],
            },
            "then": forbid("gap_code"),
        },
        {
            "if": {
                "properties": {"scope": {"const": "GIT_CURRENT_TREE"}},
                "required": ["scope"],
            },
            "then": {
                "properties": {
                    "action": {
                        "enum": [
                            "KEEP",
                            "NO_CANDIDATE",
                            "PRUNE_CURRENT_TREE",
                        ]
                    }
                }
            },
        },
        {
            "if": {
                "properties": {"scope": {"const": "MANAGED_RAW"}},
                "required": ["scope"],
            },
            "then": {
                "properties": {
                    "action": {
                        "enum": [
                            "DELETE_OWNED_SEGMENT",
                            "KEEP",
                            "NO_CANDIDATE",
                            "OFFLINE_TTL_BREACH_CLEANUP",
                        ]
                    },
                    "gap_code": {
                        "enum": [
                            "OFFLINE_TTL_BREACH",
                            "RAW_EXPIRED_UNPUBLISHED",
                        ]
                    },
                },
                **forbid("affected_public_artifacts"),
            },
        },
    ]
    return schema


def schemas() -> Dict[str, Dict[str, Any]]:
    return {
        DAILY_MANIFEST_ID: daily_manifest_schema(),
        INDEX_ENTRY_ID: index_entry_schema(),
        PUBLICATION_V2_ID: publication_manifest_v2_schema(),
        RETENTION_V3_ID: retention_receipt_v3_schema(),
    }


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _schema_entry(schema_id: str, document: Mapping[str, Any]) -> Dict[str, Any]:
    draft_path = SCHEMA_DIR / SCHEMA_FILENAMES[schema_id]
    canonical_path = (
        AUTO_DIR / "schemas" / "public-v2" / SCHEMA_FILENAMES[schema_id]
    )
    relationship: Dict[str, Any]
    if schema_id == PUBLICATION_V2_ID:
        relationship = {
            "kind": "REPLACES",
            "replaces_schema_id": PUBLICATION_V1_ID,
        }
    elif schema_id == RETENTION_V3_ID:
        relationship = {
            "kind": "REPLACES",
            "replaces_schema_id": RETENTION_V2_ID,
        }
    else:
        relationship = {"kind": "ADDS"}
    dependencies = {
        DAILY_MANIFEST_ID: [
            "MECHANISM_CONSUMER_DAILY_MANIFEST_V1",
            "MECHANISM_RETENTION_POLICY_V3",
            "PUBLICATION_MANIFEST_V2_STREAMING",
        ],
        INDEX_ENTRY_ID: [
            "BOUND_REFERENCE_RESOLVER",
            "MECHANISM_LONG_LIVED_DEDUPE_AND_CORRECTION_INDEX",
            "MECHANISM_RETENTION_POLICY_V3",
        ],
        PUBLICATION_V2_ID: [
            "BOUNDED_STREAMING_PUBLIC_JSONL_VALIDATOR",
            "MECHANISM_CONSUMER_PATH_OPERATION_ROUTING",
            "MECHANISM_PUBLIC_VALUE_ALLOWLIST_DELTA",
        ],
        RETENTION_V3_ID: [
            "DAILY_RUN_SHARD_MANIFEST_V1",
            "MECHANISM_RETENTION_POLICY_V3",
            "PUBLICATION_MANIFEST_V2_DELETE",
        ],
    }
    return {
        "consumer_and_policy_dependencies": dependencies[schema_id],
        "draft_relative_path": draft_path.relative_to(REPO_ROOT).as_posix(),
        "id": schema_id,
        "owner_plane": "AUTO",
        "proposed_canonical_relative_path": canonical_path.relative_to(
            REPO_ROOT
        ).as_posix(),
        "relationship": relationship,
        "schema_sha256": hashlib.sha256(
            canonicalize_object(document)
        ).hexdigest(),
        "self_digest_pointer": SELF_POINTERS[schema_id],
        "visibility": "PUBLIC",
    }


def interface(schema_documents: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    entries = [
        _schema_entry(schema_id, document)
        for schema_id, document in schema_documents.items()
    ]
    entries.sort(key=lambda item: item["id"].encode("utf-8"))
    return {
        "activation_forbidden": True,
        "au_040_complete": False,
        "canonical_publication_permitted": False,
        "current_trusted_candidate": {
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "canonical_manifest_path": CURRENT_CANDIDATE_MANIFEST_PATH,
            "git_object_id": CURRENT_CANDIDATE_GIT_OBJECT,
            "mode": "CANDIDATE",
            "schema_count": 29,
            "policy_count": 5,
            "unchanged_by_this_draft": True,
        },
        "draft_schema_count": len(entries),
        "draft_schema_entries": entries,
        "draft_validation_context": {
            "current_candidate_bundle_digest": (
                CURRENT_CANDIDATE_BUNDLE_DIGEST
            ),
            "current_policy_set_used_for_schema_validation_only": True,
            "mechanism_policy_acceptance_required": True,
            "retention_policy_v3_present": False,
        },
        "future_mechanism_retention_policy_v3_required": {
            "active_tree_only": True,
            "boundary_is_retained": True,
            "index_and_dedupe_aggregate_retained": True,
            "prune_deadline_hours": 24,
            "strict_now_greater_than_anchor": True,
        },
        "loader_isolation_invariant": {
            "current_candidate_recursive_loader_glob": "**/*.schema.json",
            "current_candidate_recursive_loader_root": (
                "CodexSkills/registry/auto/schemas/public/"
            ),
            "current_candidate_set_must_remain_exact": True,
            "proposed_canonical_root": (
                "CodexSkills/registry/auto/schemas/public-v2/"
            ),
            "proposed_paths_visible_to_current_loader": False,
        },
        "next_phase": "MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE",
        "ownership_safe_sequence": [
            "AUTO_TRANSPORT_SCHEMA_DRAFT",
            "MECHANISM_SEMANTIC_POLICY_ACCEPTANCE_NO_BUNDLE",
            "AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS",
            "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL",
            "AUTO_EXACT_BUNDLE_INTEGRATION",
        ],
        "promotion_required_before_candidate_materialization": True,
        "proposed_active_shared_set": {
            "current_schema_count": 29,
            "policy_count": 5,
            "replaced_policy_ids": [
                POLICY_PREFIX + "retention:v2",
            ],
            "replacement_policy_ids": [
                POLICY_PREFIX + "retention:v3",
            ],
            "replaced_schema_ids": [
                PUBLICATION_V1_ID,
                RETENTION_V2_ID,
            ],
            "replacement_schema_ids": [
                PUBLICATION_V2_ID,
                RETENTION_V3_ID,
            ],
            "added_schema_ids": [
                DAILY_MANIFEST_ID,
                INDEX_ENTRY_ID,
            ],
            "target_schema_count": 31,
        },
        "protocol_revision": PROTOCOL,
        "draft_paths_forbidden_in_candidate_manifest": True,
        "repository_bound": False,
        "required_mechanism_public_value_allowlist_additions": (
            REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS
        ),
        "runtime_integration_performed": False,
        "status": "DRAFT_NON_ACTIVE",
        "transport_contract": {
            "daily_manifest_path_pattern": (
                RUN_LOG_ROOT + "YYYY/MM/DD/manifest-NNNN.json"
            ),
            "empty_date_manifest_forbidden": True,
            "event_order": "OCCURRED_AT_THEN_EVENT_UID",
            "first_published_at_definition": (
                "FIRST_CANONICAL_PUBLICATION_CONTROLLED_UTC_TRANSACTION_"
                "TIMESTAMP_EFFECTIVE_AFTER_REMOTE_READBACK"
            ),
            "index_path_pattern": (
                RUN_LOG_ROOT + "YYYY/MM/DD/index-NNNN.jsonl"
            ),
            "part_path_pattern": (
                RUN_LOG_ROOT + "YYYY/MM/DD/part-NNNN.jsonl"
            ),
            "index_persistent_after_shard_prune": True,
            "manifest_revisions_append_only": True,
            "manifest_revision_numbers_reused": False,
            "manifest_result_commit_sha_embedded": False,
            "max_part_bytes": MAX_PART_BYTES,
            "part_numbers_reused": False,
            "physical_shard_required_only_when_active": True,
            "prune_deadline_boundary_is_breach": False,
            "prune_deadline_breach_gap_code": (
                "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
            ),
            "prune_deadline_hours_after_retention_anchor": 24,
            "record_framing": JSONL_SERIALIZATION,
            "retained_index_required_for_all_part_states": True,
            "timezone": "Australia/Sydney",
        },
    }


def generated_files() -> Dict[Path, bytes]:
    schema_documents = schemas()
    files: Dict[Path, bytes] = {}
    for schema_id, document in schema_documents.items():
        files[SCHEMA_DIR / SCHEMA_FILENAMES[schema_id]] = _pretty(document)
    files[OUTPUT_INTERFACE] = _pretty(interface(schema_documents))
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
        print(
            "AUTO_TRANSPORT_DRAFT_MISMATCH:" + ",".join(sorted(mismatches))
        )
        return 2
    interface_raw = generated_files()[OUTPUT_INTERFACE]
    digest = hashlib.sha256(interface_raw).hexdigest()
    print(
        "AUTO_TRANSPORT_DRAFT_BYTE_EQUIVALENT"
        if check
        else "AUTO_TRANSPORT_DRAFT_GENERATED_OK",
        f"interface_raw_sha256={digest}",
    )
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
