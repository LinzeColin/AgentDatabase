#!/usr/bin/env python3
"""Build/check non-active Mechanism M-065 migration/cutover evidence."""

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

from CodexSkills.governance.migration.read_only_cutover import (  # noqa: E402
    AUDIT_COUNTER_FIELDS,
    OBSERVATION_SCHEMA_ID,
    OBSERVATION_SELF_POINTER,
    PLAN_SCHEMA_ID,
    PLAN_SELF_POINTER,
    PROTOCOL_REVISION,
    SOURCE_CLASSES,
    build_observation,
    derive_cutover_plan,
    validate_cutover_plan,
    validate_observation,
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
MIGRATION_DIR = GOVERNANCE_DIR / "migration"
SCHEMA_DIR = MIGRATION_DIR / "schemas"
COMPONENT_PATH = MIGRATION_DIR / "read_only_cutover.py"
OBSERVATION_PATH = MIGRATION_DIR / "read-only-migration-observation.json"
PLAN_PATH = MIGRATION_DIR / "read-only-cutover-plan.json"
READINESS_PATH = MIGRATION_DIR / "read-only-migration-cutover-readiness.json"
OBSERVATION_SCHEMA_PATH = (
    SCHEMA_DIR / "read-only-migration-observation.schema.json"
)
PLAN_SCHEMA_PATH = SCHEMA_DIR / "read-only-cutover-plan.schema.json"
READINESS_SCHEMA_PATH = (
    SCHEMA_DIR / "read-only-migration-cutover-readiness.schema.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

READINESS_SCHEMA_ID = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:read-only-migration-cutover-readiness:v1"
)
NEXT_PHASE = "MECHANISM_PERFORMANCE_CAPACITY_BUDGETS"
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

M064_GIT_OBJECT = (
    "sha1:9b8f20f3ab97a7ec06aedfbe53670569ac036f9b"
)
M064_READINESS_PATH = (
    "CodexSkills/governance/retention/"
    "git-history-persistence-readiness.json"
)
M064_READINESS_RAW_SHA256 = (
    "3cb7f9b6c5528f6c7415fa45c53da1fd38f2dbb7561f8d123b56769e96db567f"
)
M064_READINESS_SELF_DIGEST = (
    "b94cfab93ad5383dda32b45506f267cf126c7400925fd4d371278bde392a007e"
)
M064_COMPONENT_PATH = (
    "CodexSkills/governance/retention/git_history_disclosure.py"
)
M064_COMPONENT_RAW_SHA256 = (
    "f45d8fd67fa52a8eac0305af0e6f47c47fd91a2052fa9915eb82a7128754c792"
)
M064_SCHEMA_CONTRACTS = (
    (
        "CodexSkills/governance/retention/schemas/"
        "git-history-persistence-disclosure.schema.json",
        "a038b9dfc34ed419b6cdd7b67917a6f7a7699e937d0c603e81b677f924b1d30e",
        "7afb8cfa3f4039d91b272307f5d92a162e0d85ed972589bba1289c01fc74d440",
    ),
    (
        "CodexSkills/governance/retention/schemas/"
        "git-history-persistence-readiness.schema.json",
        "7c27b1b04c36293df917aecbe74c19c889a6293e8a1810be1e2a92272aa7d598",
        "247053b03b42750fd2bdf76732ee311967850661b97fe9181b722a8b5d677351",
    ),
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
M060_READINESS_SCHEMA_PATH = (
    "CodexSkills/governance/retention/schemas/"
    "protected-local-managed-raw-readiness.schema.json"
)
M060_READINESS_SCHEMA_RAW_SHA256 = (
    "22a8fd3946bdd37059000b49b77c102de653884c2c909b27193a45b619e56935"
)
M060_READINESS_SCHEMA_SHA256 = (
    "a4bf03f6cf1c244952a5f99b33f37d61fe71d840b661f340db0b64dffeb8479b"
)

HISTORICAL_MIGRATION_GIT_OBJECT = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
HISTORICAL_PREDECESSOR_GIT_OBJECT = (
    "sha1:60c7311989e8931b0a701d7620260bb4d31313a1"
)
HISTORICAL_PATH_ROWS = (
    (
        "AGENTS",
        "sha1:012f7d3759bb4f54ebe8d029d50f45b4a0092e51",
        "sha1:012f7d3759bb4f54ebe8d029d50f45b4a0092e51",
        True,
    ),
    (
        "CLAUDE",
        "sha1:5a01abd56c36c8a3fc682e35b866f8847327d3d2",
        "sha1:5a01abd56c36c8a3fc682e35b866f8847327d3d2",
        True,
    ),
    (
        "CODEX",
        "sha1:3a9cbdd2b0b8dd353e90c466e6f6aee8df3fe7a7",
        "sha1:2b4204d4a755f18ab910f3e3228291f76c67c00c",
        False,
    ),
    (
        "CODEX_SYSTEM",
        "sha1:2ce698d64a137a3319f314df0010d98d70cb9625",
        "sha1:2ce698d64a137a3319f314df0010d98d70cb9625",
        True,
    ),
)
HISTORICAL_SOURCE_PATHS = {
    "AGENTS": "CodexSkills/agents",
    "CLAUDE": "CodexSkills/claude",
    "CODEX": "CodexSkills/codex",
    "CODEX_SYSTEM": "CodexSkills/codex-system",
}
HISTORICAL_TARGET_PATHS = {
    "AGENTS": "CodexSkills/registry/agents",
    "CLAUDE": "CodexSkills/registry/claude",
    "CODEX": "CodexSkills/registry/codex",
    "CODEX_SYSTEM": "CodexSkills/registry/codex-system",
}

RESOLVER_GIT_OBJECT = (
    "sha1:98e193e74991346d266bdd94ae720c32f25dfb47"
)
RESOLVER_PATH = "CodexSkills/governance/registry/resolver-interface.json"
RESOLVER_RAW_SHA256 = (
    "f83032d5cb8c9dda9c6e903bb9dc5bf4f2a5de8bd687beeb010047f9e6b3ba2a"
)
RESOLVER_SELF_DIGEST = (
    "d75e9b1d112b95d7ce0c5b9579140e78847ebc228b7347df7340e211522c0077"
)
REGISTERED_SNAPSHOT_PATH = (
    "CodexSkills/registry/_global/registry-snapshot.v1.json"
)
REGISTERED_SNAPSHOT_RAW_SHA256 = (
    "ed5fb74fa88a2f1115a716be5e63f683d206c10d3d0a2005230d4c33d4c12c98"
)
REGISTERED_SNAPSHOT_SELF_DIGEST = (
    "7b5a74bd459a4737299444b68439c1799ba8a2159032636a24a987113eee9d12"
)

CURRENT_DEPENDENCY_BLOCKERS = (
    "M014_SOURCE_MIGRATION_RECEIPT_MISSING",
    "M015_COMPLETE_SOURCE_TARGET_PARITY_MISSING",
    "RESOLVER_PRODUCTION_TRUST_NOT_PERMITTED",
    "RESOLVER_SOURCE_ROOT_PARITY_NOT_PROVEN",
    "RESOLVER_WHOLE_SOURCE_PARITY_NOT_PROVEN",
)

REF = (
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:common-definitions:v1#/$defs/"
)


class ReadOnlyMigrationBuildError(ValueError):
    """M-065 evidence cannot be reproduced without weakening a gate."""


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _render(value: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _load(raw: bytes, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(raw)
    except Exception as exc:
        raise ReadOnlyMigrationBuildError(code) from exc
    if not isinstance(value, dict):
        raise ReadOnlyMigrationBuildError(code)
    return value


def _git_blob(tagged_object: str, relative_path: str) -> bytes:
    if tagged_object.count(":") != 1:
        raise ReadOnlyMigrationBuildError("M065_GIT_OBJECT_INVALID")
    algorithm, object_id = tagged_object.split(":", 1)
    if algorithm != "sha1" or len(object_id) != 40:
        raise ReadOnlyMigrationBuildError("M065_GIT_OBJECT_INVALID")
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", object_id + ":" + relative_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if process.returncode != 0:
        raise ReadOnlyMigrationBuildError(
            "M065_GIT_BLOB_UNAVAILABLE:" + relative_path
        )
    return process.stdout


def _git_tree(tagged_object: str, relative_path: str) -> str:
    _, object_id = tagged_object.split(":", 1)
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "rev-parse", object_id + ":" + relative_path],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if process.returncode != 0:
        raise ReadOnlyMigrationBuildError(
            "M065_GIT_TREE_UNAVAILABLE:" + relative_path
        )
    value = process.stdout.decode("ascii", errors="strict").strip()
    if len(value) != 40:
        raise ReadOnlyMigrationBuildError(
            "M065_GIT_TREE_INVALID:" + relative_path
        )
    return "sha1:" + value


def _current(relative_path: str) -> bytes:
    path = REPO_ROOT.joinpath(*relative_path.split("/"))
    if not path.is_file() or path.is_symlink():
        raise ReadOnlyMigrationBuildError(
            "M065_CURRENT_FILE_INVALID:" + relative_path
        )
    return path.read_bytes()


def _validate_pinned_file(
    tagged_object: str,
    relative_path: str,
    raw_digest: str,
    *,
    schema_digest: Optional[str] = None,
) -> Mapping[str, Any]:
    historical = _git_blob(tagged_object, relative_path)
    if _sha256(historical) != raw_digest:
        raise ReadOnlyMigrationBuildError(
            "M065_HISTORICAL_RAW_DRIFT:" + relative_path
        )
    if _current(relative_path) != historical:
        raise ReadOnlyMigrationBuildError(
            "M065_CURRENT_RAW_DRIFT:" + relative_path
        )
    value = _load(historical, "M065_JSON_INVALID:" + relative_path)
    if schema_digest is not None and canonical_digest(value) != schema_digest:
        raise ReadOnlyMigrationBuildError(
            "M065_SCHEMA_DIGEST_DRIFT:" + relative_path
        )
    return value


def _validate_predecessors() -> Mapping[str, Any]:
    m064 = _validate_pinned_file(
        M064_GIT_OBJECT,
        M064_READINESS_PATH,
        M064_READINESS_RAW_SHA256,
    )
    if (
        m064.get("artifact_digest") != M064_READINESS_SELF_DIGEST
        or m064.get("artifact_digest")
        != canonical_digest(m064, "/artifact_digest")
        or m064.get("status")
        != "DRAFT_NON_ACTIVE_GIT_HISTORY_PERSISTENCE_DISCLOSURE_READY"
        or m064.get("next_phase") != "MECHANISM_READ_ONLY_MIGRATION_CUTOVER"
        or m064.get("task_contract", {}).get("completed_task_ids")
        != ["M-064"]
    ):
        raise ReadOnlyMigrationBuildError("M065_M064_CONTRACT_INVALID")
    if _sha256(_git_blob(M064_GIT_OBJECT, M064_COMPONENT_PATH)) != (
        M064_COMPONENT_RAW_SHA256
    ):
        raise ReadOnlyMigrationBuildError("M065_M064_COMPONENT_DRIFT")
    if _current(M064_COMPONENT_PATH) != _git_blob(
        M064_GIT_OBJECT, M064_COMPONENT_PATH
    ):
        raise ReadOnlyMigrationBuildError("M065_M064_COMPONENT_CURRENT_DRIFT")
    for path, raw_digest, schema_digest in M064_SCHEMA_CONTRACTS:
        _validate_pinned_file(
            M064_GIT_OBJECT,
            path,
            raw_digest,
            schema_digest=schema_digest,
        )

    m060 = _validate_pinned_file(
        M060_GIT_OBJECT,
        M060_READINESS_PATH,
        M060_READINESS_RAW_SHA256,
    )
    if (
        m060.get("artifact_digest") != M060_READINESS_SELF_DIGEST
        or m060.get("artifact_digest")
        != canonical_digest(m060, "/artifact_digest")
        or m060.get("task_contract", {}).get("completed_task_ids")
        != ["M-060"]
        or m060.get("root_lifecycle_contract", {}).get(
            "protected_delete_budget"
        )
        != 0
    ):
        raise ReadOnlyMigrationBuildError("M065_M060_CONTRACT_INVALID")
    if _sha256(_git_blob(M060_GIT_OBJECT, M060_COMPONENT_PATH)) != (
        M060_COMPONENT_RAW_SHA256
    ):
        raise ReadOnlyMigrationBuildError("M065_M060_COMPONENT_DRIFT")
    if _current(M060_COMPONENT_PATH) != _git_blob(
        M060_GIT_OBJECT, M060_COMPONENT_PATH
    ):
        raise ReadOnlyMigrationBuildError("M065_M060_COMPONENT_CURRENT_DRIFT")
    _validate_pinned_file(
        M060_GIT_OBJECT,
        M060_READINESS_SCHEMA_PATH,
        M060_READINESS_SCHEMA_RAW_SHA256,
        schema_digest=M060_READINESS_SCHEMA_SHA256,
    )
    return {"m060": m060, "m064": m064}


def _validate_historical_path_evidence() -> list[Mapping[str, Any]]:
    actual_parent = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "rev-parse",
            HISTORICAL_MIGRATION_GIT_OBJECT.split(":", 1)[1] + "^",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=20,
        check=False,
    )
    if (
        actual_parent.returncode != 0
        or actual_parent.stdout.decode("ascii", errors="strict").strip()
        != HISTORICAL_PREDECESSOR_GIT_OBJECT.split(":", 1)[1]
    ):
        raise ReadOnlyMigrationBuildError(
            "M065_HISTORICAL_MIGRATION_PARENT_DRIFT"
        )
    rows = []
    for source_class, source_tree, target_tree, equal in HISTORICAL_PATH_ROWS:
        observed_source = _git_tree(
            HISTORICAL_PREDECESSOR_GIT_OBJECT,
            HISTORICAL_SOURCE_PATHS[source_class],
        )
        observed_target = _git_tree(
            HISTORICAL_MIGRATION_GIT_OBJECT,
            HISTORICAL_TARGET_PATHS[source_class],
        )
        if observed_source != source_tree or observed_target != target_tree:
            raise ReadOnlyMigrationBuildError(
                "M065_HISTORICAL_TREE_DRIFT:" + source_class
            )
        rows.append(
            {
                "source_class": source_class,
                "predecessor_git_object_id": (
                    HISTORICAL_PREDECESSOR_GIT_OBJECT
                ),
                "source_tree_git_object_id": source_tree,
                "target_tree_git_object_id": target_tree,
                "target_path_present": True,
                "tree_object_equal": equal,
            }
        )
    return rows


def _validate_registry_evidence() -> Mapping[str, Any]:
    resolver = _validate_pinned_file(
        RESOLVER_GIT_OBJECT,
        RESOLVER_PATH,
        RESOLVER_RAW_SHA256,
    )
    if (
        resolver.get("artifact_digest") != RESOLVER_SELF_DIGEST
        or resolver.get("artifact_digest")
        != canonical_digest(resolver, "/artifact_digest")
        or resolver.get("source_root_parity_satisfied") is not False
        or resolver.get("source_drift_reconciliation", {}).get(
            "whole_source_parity_satisfied"
        )
        is not False
        or resolver.get("production_trust_permitted") is not False
    ):
        raise ReadOnlyMigrationBuildError(
            "M065_RESOLVER_BLOCKING_FACTS_DRIFT"
        )
    snapshot_raw = _current(REGISTERED_SNAPSHOT_PATH)
    if _sha256(snapshot_raw) != REGISTERED_SNAPSHOT_RAW_SHA256:
        raise ReadOnlyMigrationBuildError("M065_REGISTRY_SNAPSHOT_RAW_DRIFT")
    snapshot = _load(snapshot_raw, "M065_REGISTRY_SNAPSHOT_INVALID")
    if (
        snapshot.get("registry_snapshot_digest")
        != REGISTERED_SNAPSHOT_SELF_DIGEST
        or snapshot.get("registry_snapshot_digest")
        != canonical_digest(snapshot, "/registry_snapshot_digest")
        or snapshot.get("status") != "REGISTERED"
    ):
        raise ReadOnlyMigrationBuildError(
            "M065_REGISTRY_SNAPSHOT_CONTRACT_INVALID"
        )
    return {"resolver": resolver, "snapshot": snapshot}


def _ref(name: str) -> Mapping[str, str]:
    return {"$ref": REF + name}


def _closed(
    properties: Mapping[str, Any],
    required: Optional[Sequence[str]] = None,
) -> Mapping[str, Any]:
    return {
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required or properties),
        "type": "object",
    }


def _snapshot_schema() -> Mapping[str, Any]:
    return _closed(
        {
            "file_count": _ref("nonnegative_count"),
            "byte_count": _ref("nonnegative_count"),
            "regular_file_count": _ref("nonnegative_count"),
            "symlink_count": _ref("nonnegative_count"),
            "tree_digest": _ref("sha256"),
            "link_digest": _ref("sha256"),
        }
    )


def build_observation_schema() -> Mapping[str, Any]:
    source = _closed(
        {
            "source_class": {"enum": list(SOURCE_CLASSES)},
            "source_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "state": {"enum": ["COMPLETE", "EMPTY", "ERROR", "MISSING"]},
            "reason_code": _ref("enum_code"),
            "pre_snapshot": _snapshot_schema(),
            "post_snapshot": _snapshot_schema(),
            "target_snapshot": _snapshot_schema(),
        },
        ("source_class", "source_ref", "state"),
    )
    history = _closed(
        {
            "source_class": {"enum": list(SOURCE_CLASSES)},
            "predecessor_git_object_id": _ref("git_object_id"),
            "source_tree_git_object_id": _ref("git_object_id"),
            "target_tree_git_object_id": _ref("git_object_id"),
            "target_path_present": {"type": "boolean"},
            "tree_object_equal": {"type": "boolean"},
        }
    )
    view = _closed(
        {
            "record_count": _ref("nonnegative_count"),
            "evidence_digest": _ref("sha256"),
        }
    )
    query = _closed(
        {
            "query_ref": {
                "pattern": "^[a-z][a-z0-9-]{2,63}$",
                "type": "string",
            },
            "state": {"enum": ["COMPLETE", "ERROR", "MISSING"]},
            "reason_code": _ref("enum_code"),
            "old_view": view,
            "new_view": view,
        },
        ("query_ref", "state"),
    )
    audit_properties: Dict[str, Any] = {
        "mode": {
            "enum": [
                "CONTROLLED_SYSCALL_AND_COMMAND_AUDIT",
                "STATIC_CAPABILITY_AUDIT",
            ]
        },
        "forbidden_command_observed": {"type": "boolean"},
        "audit_complete": {"type": "boolean"},
    }
    for field in AUDIT_COUNTER_FIELDS:
        audit_properties[field] = _ref("nonnegative_count")
    return {
        "$id": OBSERVATION_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": OBSERVATION_SCHEMA_ID},
            "protocol_revision": {"const": PROTOCOL_REVISION},
            "bundle_digest": {"const": CANDIDATE_BUNDLE_DIGEST},
            "observation_uid": _ref("typed_uid"),
            "owner_plane": {"const": "MECHANISM"},
            "status": {"const": "DRAFT_NON_ACTIVE"},
            "baseline_git_object_id": _ref("git_object_id"),
            "sources": {
                "items": source,
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
            },
            "historical_path_parity": {
                "items": history,
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
            },
            "dual_read_queries": {
                "items": query,
                "type": "array",
            },
            "mutation_audit": _closed(audit_properties),
            "delete_budget": _ref("nonnegative_count"),
            "local_data_mutation_performed": {"type": "boolean"},
            "derived_blocker_codes": {
                "items": _ref("enum_code"),
                "type": "array",
                "uniqueItems": True,
            },
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "observation_uid",
            "owner_plane",
            "status",
            "baseline_git_object_id",
            "sources",
            "historical_path_parity",
            "dual_read_queries",
            "mutation_audit",
            "delete_budget",
            "local_data_mutation_performed",
            "derived_blocker_codes",
            "evidence_bundle_digest",
        ],
        "title": "Mechanism M-065 read-only migration observation",
        "type": "object",
    }


def build_plan_schema() -> Mapping[str, Any]:
    return {
        "$id": PLAN_SCHEMA_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "schema_version": {"const": PLAN_SCHEMA_ID},
            "protocol_revision": {"const": PROTOCOL_REVISION},
            "bundle_digest": {"const": CANDIDATE_BUNDLE_DIGEST},
            "plan_uid": _ref("typed_uid"),
            "owner_plane": {"const": "MECHANISM"},
            "status": {"const": "DRAFT_NON_ACTIVE"},
            "observation_ref": _closed(
                {
                    "observation_uid": _ref("typed_uid"),
                    "evidence_digest": _ref("sha256"),
                }
            ),
            "decision": {"enum": ["BLOCKED", "CUTOVER_ELIGIBLE"]},
            "cutover_mode": {"const": "SHADOW_ONLY"},
            "parity_complete": {"type": "boolean"},
            "dual_read_complete": {"type": "boolean"},
            "zero_local_mutation_verified": {"type": "boolean"},
            "delete_budget": {"const": 0},
            "current_cutover_permitted": {"const": False},
            "blocker_codes": {
                "items": _ref("enum_code"),
                "type": "array",
                "uniqueItems": True,
            },
            "rollback_contract": {
                "const": {
                    "mode": "NEW_COMMIT_ONLY",
                    "baseline_git_object_required": True,
                    "previous_read_route_retained": True,
                    "path_map_retained": True,
                    "source_evidence_retained": True,
                    "receipt_evidence_retained": True,
                    "watermark_state_backup_required": True,
                    "local_source_deletion_permitted": False,
                    "history_rewrite_permitted": False,
                    "rebase_permitted": False,
                    "force_push_permitted": False,
                }
            },
            "evidence_bundle_digest": _ref("sha256"),
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "plan_uid",
            "owner_plane",
            "status",
            "observation_ref",
            "decision",
            "cutover_mode",
            "parity_complete",
            "dual_read_complete",
            "zero_local_mutation_verified",
            "delete_budget",
            "current_cutover_permitted",
            "blocker_codes",
            "rollback_contract",
            "evidence_bundle_digest",
        ],
        "title": "Mechanism M-065 read-only cutover plan",
        "type": "object",
    }


def _extend_bundle(
    base: ContractBundle,
    additions: Mapping[str, Mapping[str, Any]],
    pointers: Mapping[str, str],
) -> ContractBundle:
    schemas = dict(base.schemas)
    self_pointers = dict(base.self_digest_pointers)
    for schema_id, schema in additions.items():
        if schema_id in schemas:
            raise ReadOnlyMigrationBuildError(
                "M065_SCHEMA_REBIND_FORBIDDEN:" + schema_id
            )
        schemas[schema_id] = schema
        self_pointers[schema_id] = pointers[schema_id]
    try:
        registry, checker = build_registry(schemas)
    except ContractError as exc:
        raise ReadOnlyMigrationBuildError(
            "M065_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=checker,
        self_digest_pointers=self_pointers,
        policies=base.policies,
        protocol_revision=base.protocol_revision,
    )


def _descriptor(
    *,
    schema_id: str,
    path: str,
    raw: bytes,
    schema_digest: str,
    self_pointer: str,
) -> Mapping[str, Any]:
    return {
        "schema_version": schema_id,
        "canonical_path": path,
        "content_digest": _sha256(raw),
        "schema_sha256": schema_digest,
        "self_digest_pointer": self_pointer,
    }


def _current_observation() -> Mapping[str, Any]:
    sources = [
        {
            "source_class": source_class,
            "source_ref": source_class.lower().replace("_", "-") + "-source",
            "state": "MISSING",
            "reason_code": "M014_SOURCE_SNAPSHOT_NOT_MATERIALIZED",
        }
        for source_class in SOURCE_CLASSES
    ]
    audit: Dict[str, Any] = {
        "mode": "STATIC_CAPABILITY_AUDIT",
        "forbidden_command_observed": False,
        "audit_complete": True,
    }
    audit.update({field: 0 for field in AUDIT_COUNTER_FIELDS})
    return build_observation(
        observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FAV",
        baseline_git_object_id=M064_GIT_OBJECT,
        sources=sources,
        historical_path_parity=_validate_historical_path_evidence(),
        dual_read_queries=(),
        mutation_audit=audit,
        delete_budget=0,
    )


def _build_readiness(
    *,
    observation: Mapping[str, Any],
    plan: Mapping[str, Any],
    observation_schema: Mapping[str, Any],
    plan_schema: Mapping[str, Any],
    predecessors: Mapping[str, Any],
    registry: Mapping[str, Any],
) -> Mapping[str, Any]:
    observation_raw = _render(observation)
    plan_raw = _render(plan)
    observation_schema_raw = _render(observation_schema)
    plan_schema_raw = _render(plan_schema)
    value: Dict[str, Any] = {
        "schema_version": READINESS_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "status": (
            "DRAFT_NON_ACTIVE_READ_ONLY_MIGRATION_CUTOVER_IMPLEMENTED_BLOCKED"
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
            "m064_predecessor": {
                "verified_git_object_id": M064_GIT_OBJECT,
                "canonical_path": M064_READINESS_PATH,
                "content_digest": M064_READINESS_RAW_SHA256,
                "artifact_digest": M064_READINESS_SELF_DIGEST,
                "status": predecessors["m064"]["status"],
            },
            "m060_protected_local_boundary": {
                "verified_git_object_id": M060_GIT_OBJECT,
                "canonical_path": M060_READINESS_PATH,
                "content_digest": M060_READINESS_RAW_SHA256,
                "artifact_digest": M060_READINESS_SELF_DIGEST,
                "protected_delete_budget": 0,
            },
            "historical_repo_path_consolidation": {
                "verified_git_object_id": HISTORICAL_MIGRATION_GIT_OBJECT,
                "predecessor_git_object_id": (
                    HISTORICAL_PREDECESSOR_GIT_OBJECT
                ),
                "tree_parity_complete": False,
                "old_repo_paths_retained_after_commit": False,
                "local_source_mutation_proven": False,
            },
            "registered_snapshot": {
                "canonical_path": REGISTERED_SNAPSHOT_PATH,
                "content_digest": REGISTERED_SNAPSHOT_RAW_SHA256,
                "registry_snapshot_digest": (
                    REGISTERED_SNAPSHOT_SELF_DIGEST
                ),
                "status": registry["snapshot"]["status"],
            },
            "resolver_interface": {
                "verified_git_object_id": RESOLVER_GIT_OBJECT,
                "canonical_path": RESOLVER_PATH,
                "content_digest": RESOLVER_RAW_SHA256,
                "artifact_digest": RESOLVER_SELF_DIGEST,
                "source_mirror_parity_satisfied": True,
                "source_root_parity_satisfied": False,
                "whole_source_parity_satisfied": False,
                "production_trust_permitted": False,
            },
            "repository_self_report_is_not_trust_root": True,
        },
        "implementation_contract": {
            "component_path": (
                "CodexSkills/governance/migration/read_only_cutover.py"
            ),
            "content_digest": _sha256(COMPONENT_PATH.read_bytes()),
            "capability_mode": "PURE_IMMUTABLE_OBJECTS_ONLY",
            "source_classes": list(SOURCE_CLASSES),
            "observation": {
                **_descriptor(
                    schema_id=OBSERVATION_SCHEMA_ID,
                    path=(
                        "CodexSkills/governance/migration/schemas/"
                        "read-only-migration-observation.schema.json"
                    ),
                    raw=observation_schema_raw,
                    schema_digest=canonical_digest(observation_schema),
                    self_pointer=OBSERVATION_SELF_POINTER,
                ),
                "instance": {
                    "canonical_path": (
                        "CodexSkills/governance/migration/"
                        "read-only-migration-observation.json"
                    ),
                    "content_digest": _sha256(observation_raw),
                    "evidence_digest": (
                        observation["evidence_bundle_digest"]
                    ),
                },
            },
            "plan": {
                **_descriptor(
                    schema_id=PLAN_SCHEMA_ID,
                    path=(
                        "CodexSkills/governance/migration/schemas/"
                        "read-only-cutover-plan.schema.json"
                    ),
                    raw=plan_schema_raw,
                    schema_digest=canonical_digest(plan_schema),
                    self_pointer=PLAN_SELF_POINTER,
                ),
                "instance": {
                    "canonical_path": (
                        "CodexSkills/governance/migration/"
                        "read-only-cutover-plan.json"
                    ),
                    "content_digest": _sha256(plan_raw),
                    "evidence_digest": plan["evidence_bundle_digest"],
                },
            },
            "required_evidence": [
                "FOUR_SOURCE_PRE_POST_SNAPSHOT",
                "FILE_TYPE_DIGEST_LINK_PARITY",
                "DUAL_READ_RESULT_EQUIVALENCE",
                "ZERO_MUTATION_COMMAND_SYSCALL_AUDIT",
                "NEW_COMMIT_ONLY_ROLLBACK_CLOSURE",
            ],
            "caller_cutover_boolean_is_not_trust_root": True,
            "private_absolute_paths_serialized": False,
            "filesystem_capability_present": False,
            "git_capability_present": False,
            "network_capability_present": False,
            "state_capability_present": False,
            "mutation_capability_present": False,
        },
        "current_evidence": {
            "decision": plan["decision"],
            "cutover_mode": plan["cutover_mode"],
            "blocker_codes": plan["blocker_codes"],
            "delete_budget": plan["delete_budget"],
            "local_data_mutation_performed": (
                observation["local_data_mutation_performed"]
            ),
            "current_cutover_permitted": plan["current_cutover_permitted"],
            "real_migration_executed": False,
            "real_dual_read_executed": False,
            "real_rollback_executed": False,
        },
        "dependency_evidence": {
            "m014_status": "MISSING_DISTINCT_SOURCE_MIGRATION_RECEIPT",
            "m015_status": (
                "PARTIAL_HISTORICAL_REPO_PATH_PARITY_ONLY"
            ),
            "m060_status": "VERIFIED_PROTECTED_LOCAL_ZERO_DELETE_BUDGET",
            "dependency_completion_claimed": False,
            "incomplete_dependency_never_grandfathered": True,
        },
        "nonmutation": {
            "auto_plane_unchanged": True,
            "openai_database_unchanged": True,
            "candidate_bundle_unchanged": True,
            "local_source_write_permitted": False,
            "local_source_delete_permitted": False,
            "local_run_data_write_permitted": False,
            "legacy_data_write_permitted": False,
            "state_write_permitted": False,
            "watermark_advance_permitted": False,
            "canonical_publication_permitted": False,
            "activation_forbidden": True,
            "version_file_created": False,
        },
        "task_contract": {
            "dependency_task_ids": ["M-014", "M-015", "M-060"],
            "implemented_task_ids": ["M-065"],
            "production_dependency_status": "BLOCKED_FAIL_CLOSED",
            "pending_task_ids": ["M-066"],
            "required_output": "DUAL_READ_PARITY_CUTOVER_ROLLBACK",
            "done_gate": "NO_LOCAL_DATA_MUTATION_DELETE_BUDGET_ZERO",
            "acceptance_criteria": ["AC-07", "AC-08", "AC-09", "AC-15"],
        },
        "schema_closure_count": 34,
        "policy_count": 5,
        "real_execution_permitted": False,
        "next_phase": NEXT_PHASE,
        "self_digest_pointer": "/artifact_digest",
        "task_pack_revision": "v0.0.0.2",
        "artifact_digest": "0" * 64,
    }
    value["artifact_digest"] = canonical_digest(value, "/artifact_digest")
    return value


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
        "title": "Mechanism M-065 read-only migration/cutover readiness",
        "type": "object",
    }


def _documents() -> Mapping[Path, bytes]:
    predecessors = _validate_predecessors()
    registry_evidence = _validate_registry_evidence()
    acceptance = load_au040_acceptance()
    if (
        len(acceptance.bundle.schemas) != 31
        or len(acceptance.bundle.policies) != 5
        or acceptance.bundle.protocol_revision != PROTOCOL_REVISION
    ):
        raise ReadOnlyMigrationBuildError("M065_CANDIDATE_CONTRACT_INVALID")
    observation = _current_observation()
    plan = derive_cutover_plan(
        observation,
        plan_uid="cut_01ARZ3NDEKTSV4RRFFQ69G5FAW",
        dependency_blocker_codes=CURRENT_DEPENDENCY_BLOCKERS,
    )
    validate_observation(observation)
    validate_cutover_plan(plan, observation)
    observation_schema = build_observation_schema()
    plan_schema = build_plan_schema()
    contract = _extend_bundle(
        acceptance.bundle,
        {
            OBSERVATION_SCHEMA_ID: observation_schema,
            PLAN_SCHEMA_ID: plan_schema,
        },
        {
            OBSERVATION_SCHEMA_ID: OBSERVATION_SELF_POINTER,
            PLAN_SCHEMA_ID: PLAN_SELF_POINTER,
        },
    )
    for instance, schema_id in (
        (observation, OBSERVATION_SCHEMA_ID),
        (plan, PLAN_SCHEMA_ID),
    ):
        try:
            validate_instance(
                contract,
                instance,
                schema_id,
                expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
                verify_digest=True,
                public=True,
            )
            scan_public_value(instance, contract.policies)
        except ContractError as exc:
            raise ReadOnlyMigrationBuildError(
                "M065_INSTANCE_INVALID:" + str(exc)
            ) from exc
    readiness = _build_readiness(
        observation=observation,
        plan=plan,
        observation_schema=observation_schema,
        plan_schema=plan_schema,
        predecessors=predecessors,
        registry=registry_evidence,
    )
    readiness_schema = build_readiness_schema(readiness)
    final_contract = _extend_bundle(
        contract,
        {READINESS_SCHEMA_ID: readiness_schema},
        {READINESS_SCHEMA_ID: "/artifact_digest"},
    )
    if len(final_contract.schemas) != 34:
        raise ReadOnlyMigrationBuildError("M065_SCHEMA_CLOSURE_COUNT_INVALID")
    try:
        validate_instance(
            final_contract,
            readiness,
            READINESS_SCHEMA_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            verify_digest=True,
            public=True,
        )
        scan_public_value(readiness, final_contract.policies)
    except ContractError as exc:
        raise ReadOnlyMigrationBuildError(
            "M065_READINESS_INVALID:" + str(exc)
        ) from exc
    return {
        OBSERVATION_PATH: _render(observation),
        PLAN_PATH: _render(plan),
        READINESS_PATH: _render(readiness),
        OBSERVATION_SCHEMA_PATH: _render(observation_schema),
        PLAN_SCHEMA_PATH: _render(plan_schema),
        READINESS_SCHEMA_PATH: _render(readiness_schema),
    }


def _write() -> None:
    documents = _documents()
    SCHEMA_DIR.mkdir(parents=True, exist_ok=True)
    for path, raw in documents.items():
        path.write_bytes(raw)


def _check() -> None:
    for path, expected in _documents().items():
        if not path.is_file() or path.is_symlink():
            raise ReadOnlyMigrationBuildError(
                "M065_ARTIFACT_FILE_INVALID:" + str(path.relative_to(REPO_ROOT))
            )
        if path.read_bytes() != expected:
            raise ReadOnlyMigrationBuildError(
                "M065_ARTIFACT_NOT_BYTE_EQUIVALENT:"
                + str(path.relative_to(REPO_ROOT))
            )
    if VERSION_PATH.exists():
        raise ReadOnlyMigrationBuildError("M065_ACTIVE_VERSION_FORBIDDEN")


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
        "READ_ONLY_MIGRATION_CUTOVER_OK "
        "implementation=true current_decision=BLOCKED delete_budget=0 "
        "local_mutation=false cutover=false"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except (ContractError, ReadOnlyMigrationBuildError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
