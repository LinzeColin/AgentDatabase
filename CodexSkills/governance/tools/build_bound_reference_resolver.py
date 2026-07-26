#!/usr/bin/env python3
"""Build/check the registered, non-binding Mechanism Registry materialization.

The builder reads current Skill material only from the immutable Auto
source-content-sync Git object.  It does not trust the working tree, the
compatibility index, or source names as identity evidence.  The four current
catalogs and global snapshot are materialized both as a governance draft and
at their registered paths.  Registration makes the exact snapshot tuple
loadable; it does not make any quarantined version binding eligible.
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import posixpath
import re
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import yaml
from jsonschema import Draft202012Validator

from canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (
    ContractError,
    PROTOCOL,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
REGISTRY_DRAFT_DIR = GOVERNANCE_DIR / "registry"
SCHEMA_DIR = REGISTRY_DRAFT_DIR / "schemas"
MATERIALIZED_DIR = REGISTRY_DRAFT_DIR / "materialized"
INTERFACE_PATH = REGISTRY_DRAFT_DIR / "resolver-interface.json"

SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
COMMON_ID = SCHEMA_PREFIX + "common-definitions:v1"
IDENTITY_ID = SCHEMA_PREFIX + "skill-identity:v1"
INSTANCE_ID = SCHEMA_PREFIX + "skill-instance:v1"
VERSION_ID = SCHEMA_PREFIX + "skill-version:v1"
BINDING_ID = SCHEMA_PREFIX + "skill-binding:v1"
CATALOG_ID = SCHEMA_PREFIX + "registry-source-catalog:v1"
SNAPSHOT_ID = SCHEMA_PREFIX + "registry-snapshot:v1"
REQUEST_ID = SCHEMA_PREFIX + "bound-reference-request:v1"
DRIFT_ID = (
    SCHEMA_PREFIX + "registry-source-drift-reconciliation:v1"
)

CATALOG_SCHEMA_PATH = SCHEMA_DIR / "registry-source-catalog.schema.json"
SNAPSHOT_SCHEMA_PATH = SCHEMA_DIR / "registry-snapshot.schema.json"
REQUEST_SCHEMA_PATH = SCHEMA_DIR / "bound-reference-request.schema.json"
DRIFT_SCHEMA_PATH = (
    SCHEMA_DIR / "registry-source-drift-reconciliation.schema.json"
)
SNAPSHOT_PATH = (
    MATERIALIZED_DIR / "_global" / "registry-snapshot.v1.json"
)
DRIFT_PATH = (
    REGISTRY_DRAFT_DIR / "source-drift-reconciliation.v1.json"
)

CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_GIT_OBJECT_ID = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
SOURCE_MATERIAL_GIT_OBJECT_ID = (
    "sha1:dc653654603f5bfee3bd41890b49cfad700cf541"
)
SOURCE_MATERIAL_COMMIT = SOURCE_MATERIAL_GIT_OBJECT_ID.split(":", 1)[1]
SOURCE_OBSERVED_AT = "2026-07-26T00:49:03.000000Z"
HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT_ID = (
    "sha1:44a38890ec38ceb24ccae1ec6f5b1fc8e93aefa1"
)
HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID = (
    "sha1:5db5beecf3de7ac916020ca988f6e875891e19b1"
)
HISTORICAL_MATERIALIZATION_COMMIT = (
    HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID.split(":", 1)[1]
)
HISTORICAL_SNAPSHOT_RAW_SHA256 = (
    "d07b4d921534eabc065e2b4e7a509e5dd7e42ef3c678698958cbc3f74ef268b4"
)
HISTORICAL_SNAPSHOT_DIGEST = (
    "31f49c8ffa3bd2d268feec49b2869f409d61a5bfbb0b03f382bc562996b7fa76"
)
AUTO_SOURCE_SYNC_GIT_OBJECT_ID = (
    "sha1:dc653654603f5bfee3bd41890b49cfad700cf541"
)
AUTO_SOURCE_SYNC_COMMIT = AUTO_SOURCE_SYNC_GIT_OBJECT_ID.split(":", 1)[1]
AUTO_SOURCE_SYNC_INTERFACE_PATH = (
    "CodexSkills/registry/auto/runtime-interface.json"
)
AUTO_SOURCE_SYNC_INTERFACE_RAW_SHA256 = (
    "7f2e335b682ec98c15f2e21e74bc0c2af24768cda7e5ed1ddc1b5e341449ac84"
)
AUTO_SOURCE_SYNC_MODULE_COUNT = 27
AUTO_SOURCE_SYNC_ALIAS_SET_DIGEST = (
    "75f6db86e5a18cc000985dc32a719ac7e0bc15b22b2e3f20c0d32d3138f27387"
)
AUTO_SOURCE_SYNC_EXECUTOR_DIGEST = (
    "1fd015a043dfe48034df03d8a821cda5793c90694191a8b629672efaf33283ac"
)
AUTO_SOURCE_SYNC_PARENT_COMMIT = (
    "5db5beecf3de7ac916020ca988f6e875891e19b1"
)
AUTO_SOURCE_SYNC_CURRENT_COUNTS = {
    "agents": 24,
    "claude": 3,
    "codex": 55,
    "codex-system": 6,
}
AUTO_SOURCE_SYNC_CURRENT_SKILL_COUNT = 88
AUTO_SOURCE_SYNC_MISSING_ROOTS = ("codex/context-kernel",)
AUTO_SOURCE_SYNC_CLOSED_CONTENT_DRIFT = (
    "codex/graphify",
    "codex/persona-distiller-group",
    "codex/verifier",
)
AUTO_SOURCE_SYNC_REMOVED_PATHS = (
    "CodexSkills/registry/codex/context-kernel/MANIFEST.json",
    "CodexSkills/registry/codex/context-kernel/SKILL.md",
    "CodexSkills/registry/codex/context-kernel/scripts/context_kernel.py",
)
AUTO_SOURCE_SYNC_RESERVED_PATHS = (
    "CodexSkills/registry/agents/_catalog/",
    "CodexSkills/registry/claude/_catalog/",
    "CodexSkills/registry/codex/_catalog/",
    "CodexSkills/registry/codex-system/_catalog/",
    "CodexSkills/registry/_global/",
)
SRV_REVISION = "v0.0.0.3"
SOURCE_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1"
)
SYNC_EXECUTOR_PATH = "CodexSkills/sync_skills.py"
RESOLVER_RUNTIME_PATH = (
    "CodexSkills/governance/tools/resolve_skill_binding.py"
)
BUILDER_PATH = (
    "CodexSkills/governance/tools/build_bound_reference_resolver.py"
)

SOURCE_NAMES = ("agents", "claude", "codex", "codex-system")
SOURCE_CLASSES = {
    "agents": "AGENTS",
    "claude": "CLAUDE",
    "codex": "CODEX",
    "codex-system": "CODEX_SYSTEM",
}
EXPECTED_SOURCE_SKILL_COUNTS = {
    "agents": 24,
    "claude": 3,
    "codex": 55,
    "codex-system": 6,
}
EXPECTED_TOTAL_SKILLS = 88
EXPECTED_INVALID_METADATA: set[str] = set()
FROZEN_EXTERNAL_ALIAS_COUNT = 20

DRAFT_CATALOG_PATHS = {
    source: (
        MATERIALIZED_DIR / "sources" / source / "catalog.v1.json"
    )
    for source in SOURCE_NAMES
}
REGISTERED_CANDIDATE_DIR = MATERIALIZED_DIR / "registered"
REGISTERED_CANDIDATE_SNAPSHOT_PATH = (
    REGISTERED_CANDIDATE_DIR / "_global" / "registry-snapshot.v1.json"
)
REGISTERED_CANDIDATE_CATALOG_PATHS = {
    source: (
        REGISTERED_CANDIDATE_DIR
        / "sources"
        / source
        / "catalog.v1.json"
    )
    for source in SOURCE_NAMES
}
FINAL_SNAPSHOT_REPO_PATH = (
    "CodexSkills/registry/_global/registry-snapshot.v1.json"
)
FINAL_CATALOG_REPO_PATHS = {
    source: f"CodexSkills/registry/{source}/_catalog/catalog.v1.json"
    for source in SOURCE_NAMES
}
FINAL_SNAPSHOT_PATH = REPO_ROOT / FINAL_SNAPSHOT_REPO_PATH
FINAL_CATALOG_PATHS = {
    source: REPO_ROOT / relative_path
    for source, relative_path in FINAL_CATALOG_REPO_PATHS.items()
}

UID_ALPHABET = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
GIT_TREE_RE = re.compile(
    rb"^(100644|100755|120000) blob ([0-9a-f]{40})\t(.+)$"
)


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n"
    ).encode("utf-8")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _object_digest(value: Any) -> str:
    return _sha(canonicalize_object(value))


def _with_self_digest(value: Mapping[str, Any], field: str) -> Dict[str, Any]:
    result = dict(value)
    result[field] = "0" * 64
    result[field] = canonical_digest(result, "/" + field)
    return result


def _git(args: Sequence[str], *, binary: bool = False) -> Any:
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
        text=not binary,
    )
    if process.returncode != 0:
        stderr = (
            process.stderr.decode("utf-8", "replace")
            if binary
            else process.stderr
        )
        raise ContractError(
            f"REGISTRY_GIT_READ_FAILED:{' '.join(args)}:{stderr.strip()}"
        )
    return process.stdout


def _git_blob(object_id: str, relative_path: str) -> bytes:
    return _git(
        ["show", f"{object_id}:{relative_path}"],
        binary=True,
    )


def _tagged_commit_exists(tagged_object_id: str) -> None:
    algorithm, commit = tagged_object_id.split(":", 1)
    observed = _git(["rev-parse", "--show-object-format"]).strip()
    if algorithm != observed:
        raise ContractError("REGISTRY_SOURCE_GIT_ALGORITHM_MISMATCH")
    _git(["cat-file", "-e", f"{commit}^{{commit}}"])


def _uid(prefix: str, seed: str) -> str:
    value = int.from_bytes(
        hashlib.sha256(seed.encode("utf-8")).digest()[:16],
        "big",
    )
    encoded = []
    for _ in range(26):
        encoded.append(UID_ALPHABET[value & 31])
        value >>= 5
    return prefix + "_" + "".join(reversed(encoded))


def _schema_ref(schema_id: str, pointer: str = "") -> Dict[str, str]:
    return {"$ref": schema_id + pointer}


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


def registry_source_catalog_schema() -> Dict[str, Any]:
    ref_state = _closed_object(
        {
            "artifact_digest": {
                "anyOf": [
                    _schema_ref(COMMON_ID, "#/$defs/sha256"),
                    {"type": "null"},
                ]
            },
            "reason_code": {
                "anyOf": [
                    _schema_ref(COMMON_ID, "#/$defs/enum_code"),
                    {"type": "null"},
                ]
            },
            "state": {"enum": ["AVAILABLE", "UNAVAILABLE"]},
            "uid": {
                "anyOf": [
                    {"minLength": 1, "maxLength": 64, "type": "string"},
                    {"type": "null"},
                ]
            },
        },
        ["state", "uid", "artifact_digest", "reason_code"],
    )
    ref_state["allOf"] = [
        {
            "if": {
                "properties": {"state": {"const": "AVAILABLE"}},
                "required": ["state"],
            },
            "then": {
                "properties": {
                    "artifact_digest": _schema_ref(
                        COMMON_ID, "#/$defs/sha256"
                    ),
                    "reason_code": {"type": "null"},
                    "uid": {
                        "minLength": 1,
                        "maxLength": 64,
                        "type": "string",
                    },
                }
            },
        },
        {
            "if": {
                "properties": {"state": {"const": "UNAVAILABLE"}},
                "required": ["state"],
            },
            "then": {
                "properties": {
                    "artifact_digest": {"type": "null"},
                    "reason_code": _schema_ref(
                        COMMON_ID, "#/$defs/enum_code"
                    ),
                    "uid": {"type": "null"},
                }
            },
        },
    ]
    identity_ref = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "skill_identity_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_identity_uid"
            ),
        },
        ["skill_identity_uid", "artifact_digest"],
    )
    instance_ref = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "skill_instance_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_instance_uid"
            ),
        },
        ["skill_instance_uid", "artifact_digest"],
    )
    version_ref = _closed_object(
        {
            "skill_version_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_version_uid"
            ),
            "version_record_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
        },
        ["skill_version_uid", "version_record_digest"],
    )
    material = _closed_object(
        {
            "byte_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "content_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "metadata_state": {"enum": ["VALID", "INVALID"]},
            "regular_file_count": _schema_ref(
                COMMON_ID, "#/$defs/positive_count"
            ),
            "symlink_alias_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "tree_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
        },
        [
            "content_digest",
            "tree_digest",
            "regular_file_count",
            "symlink_alias_count",
            "byte_count",
            "metadata_state",
        ],
    )
    entry = _closed_object(
        {
            "canonical_name": {
                "minLength": 1,
                "maxLength": 128,
                "type": "string",
            },
            "eval_profile_ref": ref_state,
            "identity_ref": identity_ref,
            "instance_ref": instance_ref,
            "material": material,
            "promotion_decision_ref": ref_state,
            "source_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
            "version_ref": version_ref,
        },
        [
            "source_relative_path",
            "canonical_name",
            "identity_ref",
            "instance_ref",
            "version_ref",
            "eval_profile_ref",
            "promotion_decision_ref",
            "material",
        ],
    )
    exclusion = _closed_object(
        {
            "byte_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "file_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "reason_code": {
                "enum": [
                    "CACHE",
                    "OS_METADATA",
                    "SOURCE_OVERLAP",
                    "VCS_METADATA",
                ]
            },
        },
        ["reason_code", "file_count", "byte_count"],
    )
    return {
        "$id": CATALOG_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "bundle_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "entry_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "entries": {"items": entry, "type": "array"},
            "exclusions": {"items": exclusion, "type": "array"},
            "metadata_invalid_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "protocol_revision": _schema_ref(
                COMMON_ID, "#/$defs/protocol_revision"
            ),
            "schema_version": {"const": CATALOG_ID},
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
            "source_material_git_object_id": _schema_ref(
                COMMON_ID, "#/$defs/git_object_id"
            ),
            "source_material_policy_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "source_material_policy_id": {"const": SOURCE_POLICY_ID},
            "source_root_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
            "status": {"enum": ["DRAFT_NON_ACTIVE", "REGISTERED"]},
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "status",
            "source_class",
            "source_root_path",
            "source_material_git_object_id",
            "source_material_policy_id",
            "source_material_policy_digest",
            "entry_count",
            "metadata_invalid_count",
            "exclusions",
            "entries",
            "artifact_digest",
        ],
        "title": "Mechanism Registry source catalog",
        "type": "object",
    }


def registry_snapshot_schema() -> Dict[str, Any]:
    identity_assignment = _closed_object(
        {
            "first_seen_at": _schema_ref(
                COMMON_ID, "#/$defs/utc_z_timestamp"
            ),
            "identity_assignment_reason": {
                "const": "INITIAL_SOURCE_PATH_ANCHOR"
            },
            "skill_identity_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_identity_uid"
            ),
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
            "source_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
        },
        [
            "source_class",
            "source_relative_path",
            "skill_identity_uid",
            "first_seen_at",
            "identity_assignment_reason",
        ],
    )
    identity_record = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "record": _schema_ref(IDENTITY_ID),
        },
        ["artifact_digest", "record"],
    )
    instance_record = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "record": _schema_ref(INSTANCE_ID),
        },
        ["artifact_digest", "record"],
    )
    version_record = _closed_object(
        {
            "record": _schema_ref(VERSION_ID),
            "version_record_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
        },
        ["version_record_digest", "record"],
    )
    catalog_ref = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "draft_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
            "entry_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "proposed_final_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
        },
        [
            "source_class",
            "draft_relative_path",
            "proposed_final_relative_path",
            "entry_count",
            "artifact_digest",
        ],
    )
    merge_candidate = _closed_object(
        {
            "canonical_name": {
                "minLength": 1,
                "maxLength": 128,
                "type": "string",
            },
            "identity_uids": {
                "items": _schema_ref(
                    COMMON_ID, "#/$defs/skill_identity_uid"
                ),
                "minItems": 2,
                "type": "array",
                "uniqueItems": True,
            },
            "reason_code": {"const": "OWNER_REVIEW_REQUIRED"},
        },
        ["canonical_name", "identity_uids", "reason_code"],
    )
    counts = _closed_object(
        {
            "binding_eligible_version_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "identity_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "instance_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "metadata_invalid_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "quarantined_version_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "source_catalog_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "source_skill_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "tracked_symlink_alias_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "version_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
        },
        [
            "source_catalog_count",
            "source_skill_count",
            "identity_count",
            "instance_count",
            "version_count",
            "binding_eligible_version_count",
            "quarantined_version_count",
            "metadata_invalid_count",
            "tracked_symlink_alias_count",
        ],
    )
    parity = _closed_object(
        {
            "binding_eligible": {"type": "boolean"},
            "expected_external_symlink_alias_count": {
                "$ref": (
                    COMMON_ID + "#/$defs/nonnegative_count"
                )
            },
            "reason_codes": {
                "items": {
                    "enum": [
                        "SOURCE_MIRROR_SYMLINK_ALIAS_LOSS",
                        "SOURCE_SCAN_INCOMPLETE",
                    ]
                },
                "type": "array",
                "uniqueItems": True,
            },
            "status": {"enum": ["COMPLETE", "INCOMPLETE"]},
            "tracked_symlink_alias_count": {
                "$ref": (
                    COMMON_ID + "#/$defs/nonnegative_count"
                )
            },
        },
        [
            "status",
            "binding_eligible",
            "tracked_symlink_alias_count",
            "expected_external_symlink_alias_count",
            "reason_codes",
        ],
    )
    parity["allOf"] = [
        {
            "if": {
                "properties": {"status": {"const": "COMPLETE"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "binding_eligible": {"const": True},
                    "reason_codes": {"const": []},
                }
            },
        },
        {
            "if": {
                "properties": {"status": {"const": "INCOMPLETE"}},
                "required": ["status"],
            },
            "then": {
                "properties": {
                    "binding_eligible": {"const": False},
                    "reason_codes": {"minItems": 1},
                }
            },
        },
    ]
    return {
        "$id": SNAPSHOT_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "baseline_policy": {
                "const": "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"
            },
            "bundle_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "counts": counts,
            "identities": {"items": identity_record, "type": "array"},
            "identity_assignments": {
                "items": identity_assignment,
                "type": "array",
            },
            "identity_merge_candidates": {
                "items": merge_candidate,
                "type": "array",
            },
            "instances": {"items": instance_record, "type": "array"},
            "protocol_revision": _schema_ref(
                COMMON_ID, "#/$defs/protocol_revision"
            ),
            "registry_compatibility_index_is_not_snapshot_truth": {
                "const": True
            },
            "registry_snapshot_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "same_name_auto_merge_permitted": {"const": False},
            "schema_version": {"const": SNAPSHOT_ID},
            "snapshot_observed_at": _schema_ref(
                COMMON_ID, "#/$defs/utc_z_timestamp"
            ),
            "source_catalogs": {
                "items": catalog_ref,
                "minItems": 4,
                "maxItems": 4,
                "type": "array",
            },
            "source_material_git_object_id": _schema_ref(
                COMMON_ID, "#/$defs/git_object_id"
            ),
            "source_material_policy_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "source_material_policy_id": {"const": SOURCE_POLICY_ID},
            "source_mirror_parity": parity,
            "srv_revision": _schema_ref(
                COMMON_ID, "#/$defs/srv_revision"
            ),
            "status": {"enum": ["DRAFT_NON_ACTIVE", "REGISTERED"]},
            "versions": {"items": version_record, "type": "array"},
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "srv_revision",
            "status",
            "source_material_git_object_id",
            "source_material_policy_id",
            "source_material_policy_digest",
            "snapshot_observed_at",
            "baseline_policy",
            "registry_compatibility_index_is_not_snapshot_truth",
            "same_name_auto_merge_permitted",
            "source_mirror_parity",
            "counts",
            "identity_assignments",
            "identities",
            "instances",
            "versions",
            "identity_merge_candidates",
            "source_catalogs",
            "registry_snapshot_digest",
        ],
        "title": "Mechanism immutable Registry snapshot",
        "type": "object",
    }


def bound_reference_request_schema() -> Dict[str, Any]:
    return {
        "$id": REQUEST_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "additionalProperties": False,
        "properties": {
            "bundle_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "controlled_invocation": _schema_ref(
                BINDING_ID, "#/properties/controlled_invocation"
            ),
            "envelope_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "content_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "tree_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "protocol_revision": _schema_ref(
                COMMON_ID, "#/$defs/protocol_revision"
            ),
            "schema_version": {"const": REQUEST_ID},
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
            "source_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
        },
        "required": [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "source_class",
            "source_relative_path",
            "content_digest",
            "tree_digest",
            "controlled_invocation",
            "envelope_digest",
        ],
        "title": "Mechanism BOUND reference request",
        "type": "object",
    }


def source_drift_reconciliation_schema() -> Dict[str, Any]:
    auto_evidence = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "phase": {
                "const": "AUTO_REGISTRY_CATALOG_PATH_RESERVATION"
            },
            "relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
            "verified_git_object_id": _schema_ref(
                COMMON_ID, "#/$defs/git_object_id"
            ),
        },
        [
            "phase",
            "verified_git_object_id",
            "relative_path",
            "artifact_digest",
        ],
    )
    source_count = _closed_object(
        {
            "skill_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
        },
        ["source_class", "skill_count"],
    )
    source_observation = _closed_object(
        {
            "alias_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "completeness_status": {
                "const": "COMPLETE_AFTER_POLICY_EXCLUSIONS"
            },
            "included_file_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "included_tree_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "source_class": _schema_ref(
                COMMON_ID, "#/$defs/source_class"
            ),
            "source_snapshot_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
        },
        [
            "source_class",
            "alias_count",
            "included_file_count",
            "included_tree_digest",
            "source_snapshot_digest",
            "completeness_status",
        ],
    )
    current_mirror = _closed_object(
        {
            "evidence_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "mirror_alias_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "mirror_alias_parity_satisfied": {"const": True},
            "mirror_skill_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "source_alias_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "source_alias_parity_satisfied": {"const": True},
            "source_counts": {
                "items": source_count,
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
            },
            "source_observations": {
                "items": source_observation,
                "maxItems": 4,
                "minItems": 4,
                "type": "array",
            },
            "source_root_parity_satisfied": {"const": False},
            "whole_source_parity_satisfied": {"const": False},
        },
        [
            "source_counts",
            "mirror_skill_count",
            "source_alias_count",
            "mirror_alias_count",
            "source_alias_parity_satisfied",
            "mirror_alias_parity_satisfied",
            "source_root_parity_satisfied",
            "whole_source_parity_satisfied",
            "evidence_digest",
            "source_observations",
        ],
    )
    disposition = _closed_object(
        {
            "binding_eligible": {"const": False},
            "current_catalog_entry_present": {"const": False},
            "historical_registry_records_retained": {"const": True},
            "lifecycle_transition_permitted": {"const": False},
            "missing_root_observation_state": {
                "const": "UNOBSERVED"
            },
            "promotion_permitted": {"const": False},
            "reason_codes": {
                "const": [
                    "HISTORICAL_RECORD_RETENTION_REQUIRED",
                    "SOURCE_CONTENT_DRIFT_PENDING_AUTO_SYNC",
                    "SOURCE_ROOT_ABSENT_CURRENT_OBSERVATION",
                ]
            },
        },
        [
            "missing_root_observation_state",
            "current_catalog_entry_present",
            "historical_registry_records_retained",
            "lifecycle_transition_permitted",
            "binding_eligible",
            "promotion_permitted",
            "reason_codes",
        ],
    )
    identity_ref = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "skill_identity_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_identity_uid"
            ),
        },
        ["skill_identity_uid", "artifact_digest"],
    )
    instance_ref = _closed_object(
        {
            "artifact_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "skill_instance_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_instance_uid"
            ),
        },
        ["skill_instance_uid", "artifact_digest"],
    )
    version_ref = _closed_object(
        {
            "skill_version_uid": _schema_ref(
                COMMON_ID, "#/$defs/skill_version_uid"
            ),
            "version_record_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
        },
        ["skill_version_uid", "version_record_digest"],
    )
    historical_entry = _closed_object(
        {
            "identity_ref": identity_ref,
            "instance_ref": instance_ref,
            "source_relative_path": {
                "const": "codex/context-kernel"
            },
            "version_ref": version_ref,
        },
        [
            "source_relative_path",
            "identity_ref",
            "instance_ref",
            "version_ref",
        ],
    )
    historical_registry = _closed_object(
        {
            "historical_catalog_entry": historical_entry,
            "registry_snapshot_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "source_material_git_object_id": _schema_ref(
                COMMON_ID, "#/$defs/git_object_id"
            ),
            "source_skill_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
        },
        [
            "source_material_git_object_id",
            "source_skill_count",
            "registry_snapshot_digest",
            "historical_catalog_entry",
        ],
    )
    removed_artifact = _closed_object(
        {
            "byte_count": _schema_ref(
                COMMON_ID, "#/$defs/nonnegative_count"
            ),
            "content_digest": _schema_ref(
                COMMON_ID, "#/$defs/sha256"
            ),
            "relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
        },
        ["relative_path", "byte_count", "content_digest"],
    )
    pending_drift = _closed_object(
        {
            "action_owner": {"const": "AUTO"},
            "required_action": {"const": "EXACT_CONTENT_SYNC"},
            "source_relative_path": _schema_ref(
                COMMON_ID, "#/$defs/repo_relative_posix_path"
            ),
        },
        ["source_relative_path", "action_owner", "required_action"],
    )
    return {
        "$id": DRIFT_ID,
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        **_closed_object(
            {
                "artifact_digest": _schema_ref(
                    COMMON_ID, "#/$defs/sha256"
                ),
                "auto_evidence": auto_evidence,
                "bundle_digest": _schema_ref(
                    COMMON_ID, "#/$defs/sha256"
                ),
                "current_mirror": current_mirror,
                "disposition": disposition,
                "historical_registry": historical_registry,
                "mirror_removal_artifacts": {
                    "items": removed_artifact,
                    "maxItems": 3,
                    "minItems": 3,
                    "type": "array",
                },
                "next_phase": {
                    "const": "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
                },
                "pending_content_drift": {
                    "items": pending_drift,
                    "maxItems": 3,
                    "minItems": 3,
                    "type": "array",
                },
                "protocol_revision": _schema_ref(
                    COMMON_ID, "#/$defs/protocol_revision"
                ),
                "schema_version": {"const": DRIFT_ID},
                "status": {
                    "const": (
                        "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
                    )
                },
            },
            [
                "schema_version",
                "protocol_revision",
                "bundle_digest",
                "status",
                "auto_evidence",
                "historical_registry",
                "current_mirror",
                "mirror_removal_artifacts",
                "pending_content_drift",
                "disposition",
                "next_phase",
                "artifact_digest",
            ],
        ),
        "title": "Mechanism Registry source drift reconciliation",
    }


def _tree_entries(
    commit: str = SOURCE_MATERIAL_COMMIT,
) -> List[Tuple[str, str, str]]:
    paths = [
        f"CodexSkills/registry/{source}"
        for source in SOURCE_NAMES
    ]
    raw = _git(
        [
            "ls-tree",
            "-rz",
            "--full-tree",
            commit,
            "--",
            *paths,
        ],
        binary=True,
    )
    entries: List[Tuple[str, str, str]] = []
    for row in raw.split(b"\0"):
        if not row:
            continue
        match = GIT_TREE_RE.fullmatch(row)
        if match is None:
            raise ContractError("REGISTRY_SOURCE_TREE_ENTRY_INVALID")
        try:
            path = match.group(3).decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise ContractError(
                "REGISTRY_SOURCE_PATH_ENCODING_INVALID"
            ) from exc
        entries.append(
            (
                match.group(1).decode("ascii"),
                match.group(2).decode("ascii"),
                path,
            )
        )
    if not entries:
        raise ContractError("REGISTRY_SOURCE_TREE_EMPTY")
    return entries


def _read_blobs(object_ids: Iterable[str]) -> Dict[str, bytes]:
    ordered = sorted(set(object_ids))
    process = subprocess.Popen(
        ["git", "-C", str(REPO_ROOT), "cat-file", "--batch"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
    )
    assert process.stdin is not None
    assert process.stdout is not None
    result: Dict[str, bytes] = {}
    try:
        for object_id in ordered:
            process.stdin.write((object_id + "\n").encode("ascii"))
            process.stdin.flush()
            header = process.stdout.readline().rstrip(b"\n")
            parts = header.split(b" ")
            if (
                len(parts) != 3
                or parts[0].decode("ascii") != object_id
                or parts[1] != b"blob"
            ):
                raise ContractError("REGISTRY_SOURCE_BLOB_HEADER_INVALID")
            size = int(parts[2])
            payload = process.stdout.read(size)
            terminator = process.stdout.read(1)
            if len(payload) != size or terminator != b"\n":
                raise ContractError("REGISTRY_SOURCE_BLOB_READ_TRUNCATED")
            result[object_id] = payload
        process.stdin.close()
        try:
            return_code = process.wait(timeout=30)
        except subprocess.TimeoutExpired as exc:
            raise ContractError(
                "REGISTRY_SOURCE_BLOB_BATCH_TIMEOUT"
            ) from exc
        if return_code != 0:
            raise ContractError("REGISTRY_SOURCE_BLOB_BATCH_FAILED")
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
        if process.stdin is not None and not process.stdin.closed:
            process.stdin.close()
        if process.stdout is not None and not process.stdout.closed:
            process.stdout.close()
    return result


def _exclusion_reason(
    source_class: str,
    source_relative_file: str,
    policy: Mapping[str, Any],
) -> Optional[str]:
    for rule in policy["exclusions"]:
        if rule["source_scope"] not in {"ALL", source_class}:
            continue
        pattern = rule["pattern"]
        if fnmatch.fnmatchcase(source_relative_file, pattern):
            return rule["reason_code"]
        if PurePosixPath(source_relative_file).match(pattern):
            return rule["reason_code"]
    return None


def _normalize_alias_target(
    *,
    source: str,
    skill: str,
    alias_relative_path: str,
    raw: bytes,
    source_paths: Iterable[str],
) -> str:
    try:
        target = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise ContractError("REGISTRY_SYMLINK_TARGET_ENCODING_INVALID") from exc
    if (
        not target
        or target.startswith("/")
        or "\\" in target
        or any(ord(char) < 0x20 for char in target)
    ):
        raise ContractError("REGISTRY_SYMLINK_TARGET_INVALID")
    source_relative_alias = posixpath.join(skill, alias_relative_path)
    normalized = posixpath.normpath(
        posixpath.join(posixpath.dirname(source_relative_alias), target)
    )
    if normalized in {"", ".", ".."} or normalized.startswith("../"):
        raise ContractError("REGISTRY_SYMLINK_TARGET_ESCAPES_SOURCE")
    available = set(source_paths)
    if normalized not in available and not any(
        candidate.startswith(normalized.rstrip("/") + "/")
        for candidate in available
    ):
        raise ContractError("REGISTRY_SYMLINK_TARGET_MISSING")
    return normalized


def _frontmatter_state(raw: bytes) -> str:
    try:
        text = raw.decode("utf-8", errors="strict")
        if not text.startswith("---\n"):
            return "INVALID"
        end = text.find("\n---\n", 4)
        if end < 0:
            return "INVALID"
        parsed = yaml.safe_load(text[4:end])
        if (
            not isinstance(parsed, dict)
            or not isinstance(parsed.get("name"), str)
            or not isinstance(parsed.get("description"), str)
        ):
            return "INVALID"
    except (UnicodeError, yaml.YAMLError):
        return "INVALID"
    return "VALID"


def _source_material(
    source_policy: Mapping[str, Any],
) -> Tuple[
    Dict[str, List[Mapping[str, Any]]],
    int,
]:
    entries = _tree_entries()
    blobs = _read_blobs(item[1] for item in entries)
    grouped: Dict[str, Dict[str, List[Tuple[str, str, bytes]]]] = {
        source: {} for source in SOURCE_NAMES
    }
    source_paths: Dict[str, List[str]] = {
        source: [] for source in SOURCE_NAMES
    }
    for mode, object_id, repo_path in entries:
        parts = PurePosixPath(repo_path).parts
        if (
            len(parts) < 5
            or parts[:2] != ("CodexSkills", "registry")
            or parts[2] not in SOURCE_NAMES
        ):
            raise ContractError("REGISTRY_SOURCE_PATH_SHAPE_INVALID")
        source = parts[2]
        skill = parts[3]
        if skill == "_catalog":
            raise ContractError("REGISTRY_SOURCE_OBJECT_CONTAINS_CATALOG")
        relative = PurePosixPath(*parts[4:]).as_posix()
        grouped[source].setdefault(skill, []).append(
            (mode, relative, blobs[object_id])
        )
        source_paths[source].append(
            PurePosixPath(*parts[3:]).as_posix()
        )
    for source, expected in EXPECTED_SOURCE_SKILL_COUNTS.items():
        if len(grouped[source]) != expected:
            raise ContractError(
                f"REGISTRY_SOURCE_SKILL_COUNT_MISMATCH:{source}"
            )
    material: Dict[str, List[Mapping[str, Any]]] = {
        source: [] for source in SOURCE_NAMES
    }
    tracked_alias_count = 0
    for source in SOURCE_NAMES:
        source_class = SOURCE_CLASSES[source]
        included_source_files: Dict[str, Mapping[str, Any]] = {}
        for source_skill, source_rows in grouped[source].items():
            for mode, relative, payload in source_rows:
                if mode not in {"100644", "100755"}:
                    continue
                source_relative_file = f"{source_skill}/{relative}"
                if (
                    _exclusion_reason(
                        source_class,
                        source_relative_file,
                        source_policy,
                    )
                    is None
                ):
                    included_source_files[source_relative_file] = {
                        "byte_count": len(payload),
                        "content_digest": _sha(payload),
                    }
        for skill in sorted(
            grouped[source], key=lambda value: value.encode("utf-8")
        ):
            rows = grouped[source][skill]
            if not any(relative == "SKILL.md" for _, relative, _ in rows):
                raise ContractError(
                    f"REGISTRY_SKILL_ENTRYPOINT_MISSING:{source}/{skill}"
                )
            regular = []
            aliases = []
            exclusions: Dict[str, List[int]] = {}
            metadata_state = "INVALID"
            for mode, relative, payload in sorted(
                rows, key=lambda value: value[1].encode("utf-8")
            ):
                source_relative_file = f"{skill}/{relative}"
                reason = _exclusion_reason(
                    source_class,
                    source_relative_file,
                    source_policy,
                )
                if reason is not None:
                    aggregate = exclusions.setdefault(reason, [0, 0])
                    aggregate[0] += 1
                    aggregate[1] += len(payload)
                    continue
                if mode in {"100644", "100755"}:
                    regular.append(
                        {
                            "byte_count": len(payload),
                            "content_digest": _sha(payload),
                            "relative_path": relative,
                        }
                    )
                    if relative == "SKILL.md":
                        metadata_state = _frontmatter_state(payload)
                elif mode == "120000":
                    target_ref = _normalize_alias_target(
                        source=source,
                        skill=skill,
                        alias_relative_path=relative,
                        raw=payload,
                        source_paths=source_paths[source],
                    )
                    target_file = included_source_files.get(target_ref)
                    if target_file is not None:
                        alias_content_digest = target_file[
                            "content_digest"
                        ]
                        target_type = "REGULAR_FILE"
                    else:
                        prefix = target_ref.rstrip("/") + "/"
                        target_files = [
                            {
                                "byte_count": evidence["byte_count"],
                                "content_digest": evidence[
                                    "content_digest"
                                ],
                                "relative_path": path[len(prefix) :],
                            }
                            for path, evidence in sorted(
                                included_source_files.items(),
                                key=lambda item: item[0].encode("utf-8"),
                            )
                            if path.startswith(prefix)
                        ]
                        if not target_files:
                            raise ContractError(
                                "REGISTRY_SYMLINK_TARGET_INCLUDED_SET_EMPTY"
                            )
                        alias_content_digest = _object_digest(
                            {
                                "domain": (
                                    "SKILLOPS_ALIAS_DIRECTORY_CONTENT_V1"
                                ),
                                "files": target_files,
                                "target_ref": target_ref,
                            }
                        )
                        target_type = "DIRECTORY"
                    aliases.append(
                        {
                            "alias_path": relative,
                            "metadata_digest": _object_digest(
                                {
                                    "alias_path": relative,
                                    "normalized_target_ref": target_ref,
                                    "target_type": target_type,
                                }
                            ),
                            "normalized_target_ref": target_ref,
                            "content_digest": alias_content_digest,
                        }
                    )
                    tracked_alias_count += 1
                else:  # pragma: no cover - tree parser rejects first.
                    raise ContractError("REGISTRY_SOURCE_MODE_UNSUPPORTED")
            if not regular:
                raise ContractError(
                    f"REGISTRY_SKILL_REGULAR_FILE_SET_EMPTY:{source}/{skill}"
                )
            content_material = {
                "domain": "SKILLOPS_SKILL_CONTENT_V1",
                "files": regular,
            }
            tree_files = [
                {
                    **entry,
                    "relative_path": f"{skill}/{entry['relative_path']}",
                }
                for entry in regular
            ]
            tree_aliases = [
                {
                    **entry,
                    "alias_path": f"{skill}/{entry['alias_path']}",
                }
                for entry in aliases
            ]
            tree_material = {
                "aliases": tree_aliases,
                "domain": "SKILLOPS_SOURCE_TREE_V1",
                "files": tree_files,
                "source_class": source_class,
                "source_material_policy_digest": _object_digest(
                    source_policy
                ),
            }
            material[source].append(
                {
                    "byte_count": sum(
                        entry["byte_count"] for entry in regular
                    ),
                    "canonical_name": skill,
                    "content_digest": _object_digest(content_material),
                    "exclusions": [
                        {
                            "byte_count": values[1],
                            "file_count": values[0],
                            "reason_code": reason,
                        }
                        for reason, values in sorted(exclusions.items())
                    ],
                    "metadata_digest": _sha(
                        next(
                            payload
                            for mode, relative, payload in rows
                            if relative == "SKILL.md"
                        )
                    ),
                    "metadata_state": metadata_state,
                    "regular_file_count": len(regular),
                    "source_class": source_class,
                    "source_relative_path": f"{source}/{skill}",
                    "symlink_alias_count": len(aliases),
                    "tree_digest": _object_digest(tree_material),
                }
            )
    if sum(len(rows) for rows in material.values()) != EXPECTED_TOTAL_SKILLS:
        raise ContractError("REGISTRY_TOTAL_SKILL_COUNT_MISMATCH")
    return material, tracked_alias_count


def _historical_registry_records() -> Mapping[str, Any]:
    """Load the immutable 89-root baseline used only for lineage evidence."""

    snapshot_raw = _git_blob(
        HISTORICAL_MATERIALIZATION_COMMIT,
        SNAPSHOT_PATH.relative_to(REPO_ROOT).as_posix(),
    )
    if _sha(snapshot_raw) != HISTORICAL_SNAPSHOT_RAW_SHA256:
        raise ContractError(
            "REGISTRY_HISTORICAL_SNAPSHOT_RAW_DIGEST_MISMATCH"
        )
    snapshot = parse_json_bytes(snapshot_raw)
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("registry_snapshot_digest")
        != HISTORICAL_SNAPSHOT_DIGEST
        or canonical_digest(snapshot, "/registry_snapshot_digest")
        != HISTORICAL_SNAPSHOT_DIGEST
        or snapshot.get("source_material_git_object_id")
        != HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT_ID
        or snapshot.get("counts", {}).get("source_skill_count") != 89
        or snapshot.get("counts", {}).get("identity_count") != 89
        or snapshot.get("counts", {}).get("instance_count") != 89
        or snapshot.get("counts", {}).get("version_count") != 89
    ):
        raise ContractError(
            "REGISTRY_HISTORICAL_SNAPSHOT_CONTRACT_MISMATCH"
        )
    identities = {
        row["record"]["skill_identity_uid"]: row
        for row in snapshot["identities"]
    }
    instances = {
        row["record"]["skill_instance_uid"]: row
        for row in snapshot["instances"]
    }
    versions = {
        row["record"]["skill_version_uid"]: row
        for row in snapshot["versions"]
    }
    assignments = {
        (
            row["source_class"],
            row["source_relative_path"],
        ): row["skill_identity_uid"]
        for row in snapshot["identity_assignments"]
    }
    catalog_entries: Dict[Tuple[str, str], Mapping[str, Any]] = {}
    for source in SOURCE_NAMES:
        catalog = parse_json_bytes(
            _git_blob(
                HISTORICAL_MATERIALIZATION_COMMIT,
                DRAFT_CATALOG_PATHS[source]
                .relative_to(REPO_ROOT)
                .as_posix(),
            )
        )
        if (
            not isinstance(catalog, dict)
            or catalog.get("source_class") != SOURCE_CLASSES[source]
            or catalog.get("source_material_git_object_id")
            != HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT_ID
            or catalog.get("entry_count") != len(catalog.get("entries", []))
        ):
            raise ContractError(
                "REGISTRY_HISTORICAL_CATALOG_CONTRACT_MISMATCH"
            )
        for entry in catalog["entries"]:
            key = (catalog["source_class"], entry["source_relative_path"])
            if key in catalog_entries:
                raise ContractError(
                    "REGISTRY_HISTORICAL_CATALOG_ENTRY_DUPLICATE"
                )
            catalog_entries[key] = entry
    if (
        len(identities) != 89
        or len(instances) != 89
        or len(versions) != 89
        or len(assignments) != 89
        or len(catalog_entries) != 89
    ):
        raise ContractError("REGISTRY_HISTORICAL_RECORD_COUNT_MISMATCH")
    context_key = ("CODEX", "codex/context-kernel")
    if context_key not in assignments or context_key not in catalog_entries:
        raise ContractError(
            "REGISTRY_HISTORICAL_CONTEXT_KERNEL_REFERENCE_MISSING"
        )
    return {
        "assignments": assignments,
        "catalog_entries": catalog_entries,
        "identities": identities,
        "instances": instances,
        "snapshot": snapshot,
        "versions": versions,
    }


def _records_and_catalogs(
    source_material: Mapping[str, Sequence[Mapping[str, Any]]],
    source_policy_digest: str,
) -> Tuple[
    List[Mapping[str, Any]],
    List[Mapping[str, Any]],
    List[Mapping[str, Any]],
    List[Mapping[str, Any]],
    Dict[str, Mapping[str, Any]],
    List[Mapping[str, Any]],
]:
    historical = _historical_registry_records()
    identity_assignments = []
    identity_records = []
    instance_records = []
    version_records = []
    catalog_entries: Dict[str, List[Mapping[str, Any]]] = {
        source: [] for source in SOURCE_NAMES
    }
    unknown_contract_digest = _object_digest(
        {"reason_code": "NOT_MATERIALIZED", "state": "UNKNOWN"}
    )
    unknown_permissions = {
        "external_side_effect": "UNKNOWN",
        "filesystem_write": "UNKNOWN",
        "network": "UNKNOWN",
        "secrets": "UNKNOWN",
    }
    permission_digest = _object_digest(unknown_permissions)
    dependency_digest = _object_digest([])
    names: Dict[str, List[str]] = {}
    for source in SOURCE_NAMES:
        for skill in source_material[source]:
            source_path = skill["source_relative_path"]
            identity_uid = _uid(
                "ski", "SKILLOPS_IDENTITY_PATH_V1\0" + source_path
            )
            source_fingerprint = _object_digest(
                {
                    "domain": "SKILLOPS_SOURCE_INSTANCE_V1",
                    "provenance_kind": "VENDORED",
                    "source_class": skill["source_class"],
                    "source_relative_path": source_path,
                }
            )
            instance_uid = _uid(
                "skinst",
                "SKILLOPS_INSTANCE_V1\0"
                + identity_uid
                + "\0"
                + source_fingerprint,
            )
            version_uid = _uid(
                "skv",
                "SKILLOPS_VERSION_V1\0"
                + instance_uid
                + "\0"
                + skill["content_digest"]
                + "\0"
                + skill["tree_digest"]
                + "\0"
                + skill["metadata_digest"]
                + "\0"
                + dependency_digest
                + "\0"
                + permission_digest,
            )
            key = (skill["source_class"], source_path)
            historical_identity_uid = historical["assignments"].get(key)
            historical_entry = historical["catalog_entries"].get(key)
            if historical_identity_uid is None or historical_entry is None:
                raise ContractError(
                    "REGISTRY_CURRENT_ROOT_HISTORICAL_REFERENCE_MISSING:"
                    + source_path
                )
            historical_identity_row = historical["identities"].get(
                historical_identity_uid
            )
            historical_instance_uid = historical_entry["instance_ref"][
                "skill_instance_uid"
            ]
            historical_instance_row = historical["instances"].get(
                historical_instance_uid
            )
            historical_version_uid = historical_entry["version_ref"][
                "skill_version_uid"
            ]
            historical_version_row = historical["versions"].get(
                historical_version_uid
            )
            if (
                historical_identity_uid != identity_uid
                or historical_instance_uid != instance_uid
                or historical_identity_row is None
                or historical_instance_row is None
                or historical_version_row is None
            ):
                raise ContractError(
                    "REGISTRY_CURRENT_ROOT_HISTORICAL_LINEAGE_MISMATCH:"
                    + source_path
                )
            historical_identity = historical_identity_row["record"]
            historical_instance = historical_instance_row["record"]
            historical_version = historical_version_row["record"]
            identity = {
                "applicability_manifest_digest": unknown_contract_digest,
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "canonical_name": skill["canonical_name"],
                "capability_codes": [],
                "created_at": historical_identity["created_at"],
                "input_contract_digest": unknown_contract_digest,
                "instance_uids": [instance_uid],
                "lifecycle_status": "QUARANTINED",
                "output_contract_digest": unknown_contract_digest,
                "owner_ref": "owner-primary",
                "protocol_revision": PROTOCOL,
                "schema_version": IDENTITY_ID,
                "skill_identity_uid": identity_uid,
                "srv_revision": SRV_REVISION,
                "summary": (
                    "Unverified Registry baseline for " + source_path + "."
                ),
                "supersedes_identity_uid": None,
                "updated_at": SOURCE_OBSERVED_AT,
            }
            instance = {
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "data_class_codes": [],
                "first_seen_at": historical_instance["first_seen_at"],
                "forked_from_instance_uid": None,
                "last_seen_at": SOURCE_OBSERVED_AT,
                "lifecycle_status": "QUARANTINED",
                "moved_from_instance_uid": None,
                "parent_instance_uids": [],
                "permissions": unknown_permissions,
                "protocol_revision": PROTOCOL,
                "provenance": {
                    "git_object_id": SOURCE_MATERIAL_GIT_OBJECT_ID,
                    "kind": "VENDORED",
                    "license_id": None,
                    "license_state": "UNKNOWN",
                    "trust_tier": "UNVERIFIED",
                    "upstream_repo": None,
                },
                "schema_version": INSTANCE_ID,
                "skill_identity_uid": identity_uid,
                "skill_instance_uid": instance_uid,
                "source_class": skill["source_class"],
                "source_fingerprint_digest": source_fingerprint,
                "source_relative_path": source_path,
                "tool_codes": [],
                "version_uids": [version_uid],
            }
            version = {
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "compatibility_codes": [],
                "content_digest": skill["content_digest"],
                "created_at": SOURCE_OBSERVED_AT,
                "dependencies": [],
                "dependency_manifest_digest": dependency_digest,
                "eval_profile_uid": None,
                "git_object_id": SOURCE_MATERIAL_GIT_OBJECT_ID,
                "lifecycle_status": "QUARANTINED",
                "metadata_digest": skill["metadata_digest"],
                "permission_manifest_digest": permission_digest,
                "permissions": unknown_permissions,
                "protocol_revision": PROTOCOL,
                "schema_version": VERSION_ID,
                "skill_instance_uid": instance_uid,
                "skill_version_uid": version_uid,
                "source_material_policy_digest": source_policy_digest,
                "source_material_policy_id": SOURCE_POLICY_ID,
                "source_observed_at": SOURCE_OBSERVED_AT,
                "srv_revision": SRV_REVISION,
                "supersedes_version_uid": None,
                "tree_digest": skill["tree_digest"],
                "trust_tier": "UNVERIFIED",
            }
            if version_uid == historical_version_uid:
                if (
                    version["content_digest"]
                    != historical_version["content_digest"]
                    or version["tree_digest"]
                    != historical_version["tree_digest"]
                    or version["metadata_digest"]
                    != historical_version["metadata_digest"]
                    or version["dependency_manifest_digest"]
                    != historical_version["dependency_manifest_digest"]
                    or version["permission_manifest_digest"]
                    != historical_version["permission_manifest_digest"]
                ):
                    raise ContractError(
                        "REGISTRY_IMMUTABLE_VERSION_UID_COLLISION:"
                        + source_path
                    )
                version = dict(historical_version)
            else:
                version["supersedes_version_uid"] = historical_version_uid
            identity_digest = _object_digest(identity)
            instance_digest = _object_digest(instance)
            version_digest = _object_digest(version)
            identity_assignments.append(
                {
                    "first_seen_at": SOURCE_OBSERVED_AT,
                    "identity_assignment_reason": (
                        "INITIAL_SOURCE_PATH_ANCHOR"
                    ),
                    "skill_identity_uid": identity_uid,
                    "source_class": skill["source_class"],
                    "source_relative_path": source_path,
                }
            )
            identity_records.append(
                {"artifact_digest": identity_digest, "record": identity}
            )
            instance_records.append(
                {"artifact_digest": instance_digest, "record": instance}
            )
            version_records.append(
                {
                    "record": version,
                    "version_record_digest": version_digest,
                }
            )
            unavailable = {
                "artifact_digest": None,
                "reason_code": "NOT_MATERIALIZED",
                "state": "UNAVAILABLE",
                "uid": None,
            }
            catalog_entries[source].append(
                {
                    "canonical_name": skill["canonical_name"],
                    "eval_profile_ref": unavailable,
                    "identity_ref": {
                        "artifact_digest": identity_digest,
                        "skill_identity_uid": identity_uid,
                    },
                    "instance_ref": {
                        "artifact_digest": instance_digest,
                        "skill_instance_uid": instance_uid,
                    },
                    "material": {
                        "byte_count": skill["byte_count"],
                        "content_digest": skill["content_digest"],
                        "metadata_state": skill["metadata_state"],
                        "regular_file_count": skill["regular_file_count"],
                        "symlink_alias_count": skill[
                            "symlink_alias_count"
                        ],
                        "tree_digest": skill["tree_digest"],
                    },
                    "promotion_decision_ref": unavailable,
                    "source_relative_path": source_path,
                    "version_ref": {
                        "skill_version_uid": version_uid,
                        "version_record_digest": version_digest,
                    },
                }
            )
            names.setdefault(skill["canonical_name"], []).append(identity_uid)
    identity_assignments.sort(
        key=lambda item: item["source_relative_path"].encode("utf-8")
    )
    identity_records.sort(
        key=lambda item: item["record"]["skill_identity_uid"]
    )
    instance_records.sort(
        key=lambda item: item["record"]["skill_instance_uid"]
    )
    version_records.sort(
        key=lambda item: item["record"]["skill_version_uid"]
    )
    merge_candidates = [
        {
            "canonical_name": name,
            "identity_uids": sorted(uids),
            "reason_code": "OWNER_REVIEW_REQUIRED",
        }
        for name, uids in sorted(names.items())
        if len(uids) > 1
    ]
    return (
        identity_assignments,
        identity_records,
        instance_records,
        version_records,
        {
            source: tuple(
                sorted(
                    catalog_entries[source],
                    key=lambda item: item[
                        "source_relative_path"
                    ].encode("utf-8"),
                )
            )
            for source in SOURCE_NAMES
        },
        merge_candidates,
    )


def _materialized_contracts(
    schemas: Mapping[str, Mapping[str, Any]],
) -> Tuple[
    Mapping[Path, bytes],
    Mapping[str, Any],
    Mapping[str, Any],
]:
    candidate = load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            CANDIDATE_GIT_OBJECT_ID,
            CANDIDATE_BUNDLE_DIGEST,
            CANDIDATE_MANIFEST_PATH,
            "CANDIDATE",
        ),
    )
    source_policy = candidate.policies[SOURCE_POLICY_ID]
    policy_digest = _object_digest(source_policy)
    source_material, tracked_alias_count = _source_material(source_policy)
    (
        assignments,
        identities,
        instances,
        versions,
        catalog_entries,
        merge_candidates,
    ) = _records_and_catalogs(source_material, policy_digest)

    invalid_paths = {
        entry["source_relative_path"]
        for entries in source_material.values()
        for entry in entries
        if entry["metadata_state"] == "INVALID"
    }
    if invalid_paths != EXPECTED_INVALID_METADATA:
        raise ContractError("REGISTRY_METADATA_INVALID_SET_MISMATCH")
    if tracked_alias_count != FROZEN_EXTERNAL_ALIAS_COUNT:
        raise ContractError("REGISTRY_TRACKED_ALIAS_COUNT_MISMATCH")

    exclusions_by_source: Dict[str, List[Mapping[str, Any]]] = {}
    for source in SOURCE_NAMES:
        exclusions: Dict[str, List[int]] = {}
        for material in source_material[source]:
            for row in material["exclusions"]:
                aggregate = exclusions.setdefault(
                    row["reason_code"], [0, 0]
                )
                aggregate[0] += row["file_count"]
                aggregate[1] += row["byte_count"]
        exclusions_by_source[source] = [
            {
                "byte_count": values[1],
                "file_count": values[0],
                "reason_code": reason,
            }
            for reason, values in sorted(exclusions.items())
        ]

    def build_catalogs(status: str) -> Dict[str, Mapping[str, Any]]:
        catalogs: Dict[str, Mapping[str, Any]] = {}
        for source in SOURCE_NAMES:
            catalogs[source] = _with_self_digest(
                {
                    "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                    "entries": list(catalog_entries[source]),
                    "entry_count": len(catalog_entries[source]),
                    "exclusions": exclusions_by_source[source],
                    "metadata_invalid_count": sum(
                        entry["material"]["metadata_state"] == "INVALID"
                        for entry in catalog_entries[source]
                    ),
                    "protocol_revision": PROTOCOL,
                    "schema_version": CATALOG_ID,
                    "source_class": SOURCE_CLASSES[source],
                    "source_material_git_object_id": (
                        SOURCE_MATERIAL_GIT_OBJECT_ID
                    ),
                    "source_material_policy_digest": policy_digest,
                    "source_material_policy_id": SOURCE_POLICY_ID,
                    "source_root_path": f"CodexSkills/registry/{source}",
                    "status": status,
                },
                "artifact_digest",
            )
        return catalogs

    draft_catalogs = build_catalogs("DRAFT_NON_ACTIVE")
    registered_catalogs = build_catalogs("REGISTERED")

    def build_snapshot(
        status: str,
        catalogs: Mapping[str, Mapping[str, Any]],
    ) -> Mapping[str, Any]:
        return _with_self_digest(
            {
                "baseline_policy": (
                    "BASELINE_ESTABLISHED_NO_HISTORICAL_BACKFILL"
                ),
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "counts": {
                    "binding_eligible_version_count": 0,
                    "identity_count": len(identities),
                    "instance_count": len(instances),
                    "metadata_invalid_count": len(invalid_paths),
                    "quarantined_version_count": len(versions),
                    "source_catalog_count": len(catalogs),
                    "source_skill_count": len(assignments),
                    "tracked_symlink_alias_count": tracked_alias_count,
                    "version_count": len(versions),
                },
                "identities": identities,
                "identity_assignments": assignments,
                "identity_merge_candidates": merge_candidates,
                "instances": instances,
                "protocol_revision": PROTOCOL,
                "registry_compatibility_index_is_not_snapshot_truth": True,
                "same_name_auto_merge_permitted": False,
                "schema_version": SNAPSHOT_ID,
                "snapshot_observed_at": SOURCE_OBSERVED_AT,
                "source_catalogs": [
                    {
                        "artifact_digest": catalogs[source][
                            "artifact_digest"
                        ],
                        "draft_relative_path": DRAFT_CATALOG_PATHS[
                            source
                        ].relative_to(REPO_ROOT).as_posix(),
                        "entry_count": catalogs[source]["entry_count"],
                        "proposed_final_relative_path": (
                            FINAL_CATALOG_REPO_PATHS[source]
                        ),
                        "source_class": SOURCE_CLASSES[source],
                    }
                    for source in SOURCE_NAMES
                ],
                "source_material_git_object_id": (
                    SOURCE_MATERIAL_GIT_OBJECT_ID
                ),
                "source_material_policy_digest": policy_digest,
                "source_material_policy_id": SOURCE_POLICY_ID,
                "source_mirror_parity": {
                    "binding_eligible": True,
                    "expected_external_symlink_alias_count": (
                        FROZEN_EXTERNAL_ALIAS_COUNT
                    ),
                    "reason_codes": [],
                    "status": "COMPLETE",
                    "tracked_symlink_alias_count": tracked_alias_count,
                },
                "srv_revision": SRV_REVISION,
                "status": status,
                "versions": versions,
            },
            "registry_snapshot_digest",
        )

    draft_snapshot = build_snapshot(
        "DRAFT_NON_ACTIVE",
        draft_catalogs,
    )
    registered_snapshot = build_snapshot(
        "REGISTERED",
        registered_catalogs,
    )
    outputs: Dict[Path, bytes] = {}
    for source in SOURCE_NAMES:
        outputs[DRAFT_CATALOG_PATHS[source]] = _pretty(
            draft_catalogs[source]
        )
        outputs[REGISTERED_CANDIDATE_CATALOG_PATHS[source]] = _pretty(
            registered_catalogs[source]
        )
        outputs[FINAL_CATALOG_PATHS[source]] = _pretty(
            registered_catalogs[source]
        )
    outputs[SNAPSHOT_PATH] = _pretty(draft_snapshot)
    outputs[REGISTERED_CANDIDATE_SNAPSHOT_PATH] = _pretty(
        registered_snapshot
    )
    outputs[FINAL_SNAPSHOT_PATH] = _pretty(registered_snapshot)
    if (
        outputs[REGISTERED_CANDIDATE_SNAPSHOT_PATH]
        != outputs[FINAL_SNAPSHOT_PATH]
        or any(
            outputs[REGISTERED_CANDIDATE_CATALOG_PATHS[source]]
            != outputs[FINAL_CATALOG_PATHS[source]]
            for source in SOURCE_NAMES
        )
    ):
        raise ContractError("REGISTRY_EXACT_BYTE_PROMOTION_MISMATCH")

    all_schemas = {**candidate.schemas, **schemas}
    registry, checker = build_registry(all_schemas)
    for mode, catalogs in (
        ("DRAFT_NON_ACTIVE", draft_catalogs),
        ("REGISTERED", registered_catalogs),
    ):
        for source in SOURCE_NAMES:
            errors = list(
                Draft202012Validator(
                    schemas[CATALOG_ID],
                    registry=registry,
                    format_checker=checker,
                ).iter_errors(catalogs[source])
            )
            if errors:
                raise ContractError(
                    "REGISTRY_CATALOG_SCHEMA_INVALID:"
                    + mode
                    + ":"
                    + source
                    + ":"
                    + errors[0].message
                )
            scan_public_value(catalogs[source], candidate.policies)
    for mode, snapshot in (
        ("DRAFT_NON_ACTIVE", draft_snapshot),
        ("REGISTERED", registered_snapshot),
    ):
        errors = list(
            Draft202012Validator(
                schemas[SNAPSHOT_ID],
                registry=registry,
                format_checker=checker,
            ).iter_errors(snapshot)
        )
        if errors:
            raise ContractError(
                "REGISTRY_SNAPSHOT_SCHEMA_INVALID:"
                + mode
                + ":"
                + errors[0].message
            )
        scan_public_value(snapshot, candidate.policies)
    for entry in identities:
        validate_instance(
            candidate,
            entry["record"],
            IDENTITY_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            public=True,
        )
        if _object_digest(entry["record"]) != entry["artifact_digest"]:
            raise ContractError("REGISTRY_IDENTITY_DIGEST_MISMATCH")
    for entry in instances:
        validate_instance(
            candidate,
            entry["record"],
            INSTANCE_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            public=True,
        )
        if _object_digest(entry["record"]) != entry["artifact_digest"]:
            raise ContractError("REGISTRY_INSTANCE_DIGEST_MISMATCH")
    for entry in versions:
        validate_instance(
            candidate,
            entry["record"],
            VERSION_ID,
            expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
            public=True,
        )
        if (
            _object_digest(entry["record"])
            != entry["version_record_digest"]
        ):
            raise ContractError("REGISTRY_VERSION_DIGEST_MISMATCH")
    return outputs, registered_snapshot, draft_snapshot


def _verified_auto_source_sync() -> Mapping[str, Any]:
    """Verify immutable Auto source-sync evidence from its Git object.

    The current checkout may contain a legitimate successor Auto interface.
    Historical source-sync evidence therefore cannot be coupled to current
    Auto bytes; current Auto runtime closure is verified separately by the
    activation-control builder.
    """

    _tagged_commit_exists(AUTO_SOURCE_SYNC_GIT_OBJECT_ID)
    parent = _git(
        ["rev-parse", f"{AUTO_SOURCE_SYNC_COMMIT}^"]
    ).strip()
    if parent != AUTO_SOURCE_SYNC_PARENT_COMMIT:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_PARENT_MISMATCH")
    raw = _git_blob(
        AUTO_SOURCE_SYNC_COMMIT,
        AUTO_SOURCE_SYNC_INTERFACE_PATH,
    )
    if _sha(raw) != AUTO_SOURCE_SYNC_INTERFACE_RAW_SHA256:
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_INTERFACE_DIGEST_MISMATCH"
        )
    interface = parse_json_bytes(raw)
    reservation = interface.get(
        "catalog_reservation_materialization_snapshot", {}
    )
    source_sync = interface.get(
        "source_content_sync_materialization_snapshot", {}
    )
    predecessor = interface.get(
        "source_content_sync_predecessor_observation", {}
    )
    if (
        not isinstance(interface, dict)
        or interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("candidate_bundle_digest")
        != CANDIDATE_BUNDLE_DIGEST
        or interface.get("candidate_git_object_id")
        != CANDIDATE_GIT_OBJECT_ID
        or interface.get("module_count") != AUTO_SOURCE_SYNC_MODULE_COUNT
        or interface.get("catalog_path_reservation_complete") is not True
        or interface.get("registry_source_content_sync_complete") is not True
        or interface.get("registry_source_alias_parity_satisfied") is not True
        or interface.get("registry_mirror_alias_parity_satisfied") is not True
        or interface.get("registry_source_mirror_parity_satisfied") is not True
        or interface.get("registry_source_root_parity_satisfied") is not False
        or interface.get("registry_whole_source_parity_satisfied") is not False
        or interface.get("registry_alias_set_digest")
        != AUTO_SOURCE_SYNC_ALIAS_SET_DIGEST
        or interface.get(
            "bound_reference_resolver_implementation_complete"
        )
        is not True
        or interface.get(
            "bound_reference_resolver_auto_integration_complete"
        )
        is not False
        or interface.get("bound_reference_resolver_gate_satisfied") is not False
        or interface.get("runtime_state_write_permitted") is not False
        or interface.get("repository_bound") is not False
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("au_040_complete") is not False
        or interface.get("au_040_daily_jsonl_shard_complete") is not False
        or interface.get("external_gmail_ready_gate_satisfied") is not False
        or interface.get("m0c_b_permitted") is not False
        or interface.get("schedule_authority_resolved") is not False
        or interface.get("schedule_complete") is not False
        or interface.get("au_040_authority_ruling_status")
        != "REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING"
        or interface.get("next_phase")
        != "MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION"
    ):
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_INTERFACE_CONTRACT_MISMATCH"
        )
    if (
        not isinstance(source_sync, dict)
        or source_sync.get("as_of_phase")
        != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
        or source_sync.get("semantic_scope")
        != "INTERFACE_MATERIALIZATION_ONLY"
        or source_sync.get("predecessor_control_git_object_id")
        != HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID
        or source_sync.get("source_content_sync_complete") is not True
        or source_sync.get("source_mirror_parity_satisfied") is not True
        or source_sync.get("source_root_parity_satisfied") is not False
        or source_sync.get("whole_source_parity_satisfied") is not False
        or source_sync.get("remaining_content_drift_paths") != []
        or source_sync.get("exact_synchronized_paths")
        != list(AUTO_SOURCE_SYNC_CLOSED_CONTENT_DRIFT)
        or source_sync.get("missing_source_skill_roots")
        != list(AUTO_SOURCE_SYNC_MISSING_ROOTS)
        or source_sync.get("reserved_registry_namespaces_preserved") is not True
        or source_sync.get("catalog_or_snapshot_artifacts_generated") is not False
        or source_sync.get(
            "bound_reference_resolver_auto_integration_complete"
        )
        is not False
        or source_sync.get("bound_reference_resolver_gate_satisfied") is not False
        or source_sync.get("runtime_state_write_permitted") is not False
        or source_sync.get("repository_bound") is not False
        or source_sync.get("canonical_publication_permitted") is not False
        or source_sync.get("next_phase")
        != "MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION"
    ):
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_SNAPSHOT_CONTRACT_MISMATCH"
        )
    synchronized = source_sync.get("synchronized_entries")
    expected_sync = {
        "codex/graphify": (
            695,
            13_373_911,
            "816bfb795d8998983a3df2b8786a2d1c691e9e2280dd7be2bdc07acd47775587",
        ),
        "codex/persona-distiller-group": (
            35,
            1_064_137,
            "eaf8f8e32b1ade683387346adec8a21b241541567e910609247426ec3626b921",
        ),
        "codex/verifier": (
            61,
            525_884,
            "7727bcfb4d03bcc97fafeedea1f8e773945e6be70f0351e8ca32525ff1e8d556",
        ),
    }
    if (
        not isinstance(synchronized, list)
        or [row.get("source_relative_path") for row in synchronized]
        != list(AUTO_SOURCE_SYNC_CLOSED_CONTENT_DRIFT)
    ):
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ENTRY_SET_MISMATCH")
    for row in synchronized:
        expected = expected_sync[row["source_relative_path"]]
        if (
            row.get("regular_file_count") != expected[0]
            or row.get("byte_count") != expected[1]
            or row.get("alias_count") != 0
            or row.get("content_digest") != expected[2]
            or row.get("source_content_digest") != expected[2]
            or row.get("mirror_content_digest") != expected[2]
            or row.get("exact_source_mirror_content_equal") is not True
        ):
            raise ContractError(
                "REGISTRY_AUTO_SOURCE_SYNC_ENTRY_CONTRACT_MISMATCH:"
                + row["source_relative_path"]
            )
    if (
        not isinstance(predecessor, dict)
        or predecessor.get("verified_git_object_id")
        != HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID
        or predecessor.get("control_interface_raw_sha256")
        != "a31751bf1258f646412aba84e0b5c46f84f09b77e33156caea372873b819ff36"
        or predecessor.get("resolver_interface_raw_sha256")
        != "38c7952ae712e6d4543bb4f4c1f3e5f8a98b00b36780c99bfce6944a722eabf0"
        or predecessor.get("reconciliation_artifact_digest")
        != "24d02db5182463912074c109f2b5be350126d62340f58e6463755edbad1b799c"
        or predecessor.get("pending_content_drift_paths")
        != list(AUTO_SOURCE_SYNC_CLOSED_CONTENT_DRIFT)
        or predecessor.get("next_phase_at_observation")
        != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
    ):
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_PREDECESSOR_MISMATCH"
        )
    if (
        not isinstance(reservation, dict)
        or reservation.get("as_of_phase")
        != "AUTO_REGISTRY_CATALOG_PATH_RESERVATION"
        or reservation.get("reserved_registry_paths")
        != list(AUTO_SOURCE_SYNC_RESERVED_PATHS)
        or reservation.get("current_source_skill_count")
        != AUTO_SOURCE_SYNC_CURRENT_SKILL_COUNT
        or reservation.get("current_source_skill_counts")
        != AUTO_SOURCE_SYNC_CURRENT_COUNTS
        or reservation.get("mirror_skill_count")
        != AUTO_SOURCE_SYNC_CURRENT_SKILL_COUNT
        or reservation.get("mirror_skill_counts")
        != AUTO_SOURCE_SYNC_CURRENT_COUNTS
        or reservation.get("historical_source_skill_count") != 89
        or reservation.get("source_skill_count_delta") != -1
        or reservation.get("source_alias_count") != FROZEN_EXTERNAL_ALIAS_COUNT
        or reservation.get("mirror_alias_count") != FROZEN_EXTERNAL_ALIAS_COUNT
        or reservation.get("source_alias_parity_satisfied") is not True
        or reservation.get("mirror_alias_parity_satisfied") is not True
        or reservation.get("source_root_parity_satisfied") is not False
        or reservation.get("whole_source_parity_satisfied") is not False
        or reservation.get("missing_source_skill_roots")
        != list(AUTO_SOURCE_SYNC_MISSING_ROOTS)
        or reservation.get("mirror_removed_skill_roots")
        != list(AUTO_SOURCE_SYNC_MISSING_ROOTS)
        or reservation.get("mirror_removal_performed") is not True
        or reservation.get("non_alias_content_drift_observed_paths")
        != list(AUTO_SOURCE_SYNC_CLOSED_CONTENT_DRIFT)
        or reservation.get("alias_set_digest")
        != AUTO_SOURCE_SYNC_ALIAS_SET_DIGEST
    ):
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_RESERVATION_MISMATCH"
        )

    module_artifacts = interface.get("module_artifacts")
    if (
        not isinstance(module_artifacts, list)
        or len(module_artifacts) != AUTO_SOURCE_SYNC_MODULE_COUNT
    ):
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_MODULE_SET_MISMATCH")
    module_paths = []
    for artifact in module_artifacts:
        if (
            not isinstance(artifact, dict)
            or set(artifact) != {"artifact_digest", "relative_path"}
            or not isinstance(artifact.get("relative_path"), str)
            or not artifact["relative_path"].startswith(
                "CodexSkills/registry/auto/"
            )
            or "\\" in artifact["relative_path"]
            or ".." in PurePosixPath(artifact["relative_path"]).parts
            or not re.fullmatch(
                r"[0-9a-f]{64}",
                str(artifact.get("artifact_digest", "")),
            )
        ):
            raise ContractError(
                "REGISTRY_AUTO_SOURCE_SYNC_MODULE_ENTRY_INVALID"
            )
        module_paths.append(artifact["relative_path"])
        pinned = _git_blob(
            AUTO_SOURCE_SYNC_COMMIT,
            artifact["relative_path"],
        )
        if _sha(pinned) != artifact["artifact_digest"]:
            raise ContractError(
                "REGISTRY_AUTO_SOURCE_SYNC_MODULE_DIGEST_MISMATCH"
            )
    if (
        module_paths != sorted(module_paths)
        or len(module_paths) != len(set(module_paths))
    ):
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_MODULE_SET_MISMATCH")

    entries = _tree_entries(AUTO_SOURCE_SYNC_COMMIT)
    tree = {repo_path: (mode, object_id) for mode, object_id, repo_path in entries}
    aliases = reservation.get("alias_contract_entries")
    if not isinstance(aliases, list) or len(aliases) != FROZEN_EXTERNAL_ALIAS_COUNT:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ALIAS_SET_MISMATCH")
    if _object_digest(
        {
            "aliases": [
                {
                    key: row[key]
                    for key in (
                        "alias_path",
                        "normalized_target_ref",
                        "raw_target",
                        "source_namespace",
                        "target_type",
                    )
                }
                for row in aliases
            ],
            "domain": "SKILLOPS_REGISTRY_ALIAS_SET_V1",
        }
    ) != AUTO_SOURCE_SYNC_ALIAS_SET_DIGEST:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ALIAS_DIGEST_MISMATCH")
    observed_alias_paths = set()
    for alias in aliases:
        repo_path = (
            "CodexSkills/registry/"
            + alias["source_namespace"]
            + "/"
            + alias["alias_path"]
        )
        if repo_path in observed_alias_paths:
            raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ALIAS_DUPLICATE")
        observed_alias_paths.add(repo_path)
        if tree.get(repo_path, (None,))[0] != "120000":
            raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ALIAS_MODE_MISMATCH")
        if _git_blob(AUTO_SOURCE_SYNC_COMMIT, repo_path) != alias[
            "raw_target"
        ].encode("utf-8"):
            raise ContractError(
                "REGISTRY_AUTO_SOURCE_SYNC_ALIAS_TARGET_MISMATCH"
            )
    if sum(mode == "120000" for mode, _, _ in entries) != 20:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ALIAS_COUNT_MISMATCH")

    observed_roots = {source: set() for source in SOURCE_NAMES}
    for repo_path in tree:
        parts = PurePosixPath(repo_path).parts
        if (
            len(parts) >= 4
            and parts[:2] == ("CodexSkills", "registry")
            and parts[2] in SOURCE_NAMES
            and parts[3] != "_catalog"
        ):
            observed_roots[parts[2]].add(parts[3])
    observed_counts = {
        source: len(observed_roots[source])
        for source in SOURCE_NAMES
    }
    if observed_counts != AUTO_SOURCE_SYNC_CURRENT_COUNTS:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_ROOT_COUNT_MISMATCH")
    if "context-kernel" in observed_roots["codex"]:
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_REMOVED_ROOT_PRESENT")
    if any(
        repo_path.startswith(prefix)
        for repo_path in tree
        for prefix in AUTO_SOURCE_SYNC_RESERVED_PATHS
    ):
        raise ContractError(
            "REGISTRY_AUTO_SOURCE_SYNC_GENERATED_ARTIFACT_FORBIDDEN"
        )
    for removal_path in AUTO_SOURCE_SYNC_REMOVED_PATHS:
        if removal_path in tree:
            raise ContractError(
                "REGISTRY_AUTO_SOURCE_SYNC_REMOVAL_NOT_APPLIED"
            )
    sync_artifact = reservation.get("sync_executor_artifact", {})
    if (
        sync_artifact.get("relative_path") != SYNC_EXECUTOR_PATH
        or sync_artifact.get("artifact_digest")
        != AUTO_SOURCE_SYNC_EXECUTOR_DIGEST
        or _sha(_git_blob(AUTO_SOURCE_SYNC_COMMIT, SYNC_EXECUTOR_PATH))
        != AUTO_SOURCE_SYNC_EXECUTOR_DIGEST
    ):
        raise ContractError("REGISTRY_AUTO_SOURCE_SYNC_EXECUTOR_MISMATCH")
    return interface


def _historical_source_drift_reconciliation() -> Tuple[bytes, Mapping[str, Any]]:
    """Read the immutable context-kernel reconciliation from its Git object."""

    relative_path = DRIFT_PATH.relative_to(REPO_ROOT).as_posix()
    raw = _git_blob(HISTORICAL_MATERIALIZATION_COMMIT, relative_path)
    reconciliation = parse_json_bytes(raw)
    if (
        not isinstance(reconciliation, dict)
        or reconciliation.get("artifact_digest")
        != canonical_digest(reconciliation, "/artifact_digest")
        or reconciliation.get("artifact_digest")
        != "24d02db5182463912074c109f2b5be350126d62340f58e6463755edbad1b799c"
        or reconciliation.get("schema_version") != DRIFT_ID
        or reconciliation.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
        or reconciliation.get("historical_registry", {}).get(
            "registry_snapshot_digest"
        )
        != HISTORICAL_SNAPSHOT_DIGEST
        or reconciliation.get("historical_registry", {}).get(
            "source_material_git_object_id"
        )
        != HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT_ID
        or reconciliation.get("historical_registry", {}).get(
            "source_skill_count"
        )
        != 89
        or reconciliation.get("historical_registry", {}).get(
            "historical_catalog_entry", {}
        ).get("source_relative_path")
        != "codex/context-kernel"
        or reconciliation.get("disposition", {}).get(
            "current_catalog_entry_present"
        )
        is not False
        or reconciliation.get("disposition", {}).get(
            "historical_registry_records_retained"
        )
        is not True
        or reconciliation.get("disposition", {}).get(
            "missing_root_observation_state"
        )
        != "UNOBSERVED"
        or reconciliation.get("disposition", {}).get(
            "lifecycle_transition_permitted"
        )
        is not False
        or reconciliation.get("disposition", {}).get("promotion_permitted")
        is not False
    ):
        raise ContractError(
            "REGISTRY_HISTORICAL_RECONCILIATION_CONTRACT_MISMATCH"
        )
    return raw, reconciliation


def _schema_entries(
    schemas: Mapping[str, Mapping[str, Any]],
) -> List[Mapping[str, Any]]:
    paths = {
        CATALOG_ID: CATALOG_SCHEMA_PATH,
        DRIFT_ID: DRIFT_SCHEMA_PATH,
        REQUEST_ID: REQUEST_SCHEMA_PATH,
        SNAPSHOT_ID: SNAPSHOT_SCHEMA_PATH,
    }
    pointers = {
        CATALOG_ID: "/artifact_digest",
        DRIFT_ID: "/artifact_digest",
        REQUEST_ID: "/envelope_digest",
        SNAPSHOT_ID: "/registry_snapshot_digest",
    }
    return [
        {
            "id": schema_id,
            "relative_path": paths[schema_id]
            .relative_to(REPO_ROOT)
            .as_posix(),
            "schema_sha256": _object_digest(schemas[schema_id]),
            "self_digest_pointer": pointers[schema_id],
        }
        for schema_id in sorted(schemas, key=lambda value: value.encode("ascii"))
    ]


def _interface(
    schemas: Mapping[str, Mapping[str, Any]],
    registered_snapshot: Mapping[str, Any],
    draft_snapshot: Mapping[str, Any],
    outputs: Mapping[Path, bytes],
    reconciliation: Mapping[str, Any],
) -> Mapping[str, Any]:
    sync_raw = _git_blob(
        AUTO_SOURCE_SYNC_COMMIT,
        SYNC_EXECUTOR_PATH,
    )
    runtime_raw = (REPO_ROOT / RESOLVER_RUNTIME_PATH).read_bytes()
    builder_raw = (REPO_ROOT / BUILDER_PATH).read_bytes()
    return _with_self_digest(
        {
            "activation_forbidden": True,
            "auto_integration_complete": False,
            "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
            "candidate_git_object_id": CANDIDATE_GIT_OBJECT_ID,
            "candidate_manifest_path": CANDIDATE_MANIFEST_PATH,
            "candidate_trust_mode": "CANDIDATE",
            "canonical_publication_permitted": False,
            "catalog_count": 4,
            "catalog_path_reservation_complete": True,
            "catalog_path_reservation_required": False,
            "current_materialization_path": (
                REGISTERED_CANDIDATE_DIR.relative_to(REPO_ROOT).as_posix()
            ),
            "current_materialization_promotable": True,
            "current_materialization_structurally_promoted": True,
            "current_sync_executor_contract": {
                "artifact_digest": _sha(sync_raw),
                "deletes_unreserved_source_directories": True,
                "enumerates_unreserved_source_directories_as_skills": True,
                "relative_path": SYNC_EXECUTOR_PATH,
                "reserved_registry_paths_excluded_from_deletion": True,
                "reserved_registry_paths_excluded_from_skill_enumeration": (
                    True
                ),
                "verified_git_object_id": (
                    AUTO_SOURCE_SYNC_GIT_OBJECT_ID
                ),
            },
            "exact_byte_promotion_complete": True,
            "exact_byte_promotion_required": True,
            "exact_byte_promotion_scope": (
                "POST_SOURCE_CONTENT_SYNC_PARITY_COMPLETE_"
                "SUCCESSOR_MATERIALIZATION"
            ),
            "external_trust_tuple_required_fields": [
                "canonical_snapshot_digest",
                "canonical_snapshot_path",
                "canonical_snapshot_schema_id",
                "mode",
                "verified_git_object_id",
            ],
            "final_catalog_entries": [
                {
                    "artifact_digest": parse_json_bytes(
                        outputs[FINAL_CATALOG_PATHS[source]]
                    )["artifact_digest"],
                    "candidate_relative_path": (
                        REGISTERED_CANDIDATE_CATALOG_PATHS[source]
                        .relative_to(REPO_ROOT)
                        .as_posix()
                    ),
                    "draft_relative_path": DRAFT_CATALOG_PATHS[source]
                    .relative_to(REPO_ROOT)
                    .as_posix(),
                    "relative_path": FINAL_CATALOG_REPO_PATHS[source],
                    "source_class": SOURCE_CLASSES[source],
                    "status": "REGISTERED",
                }
                for source in SOURCE_NAMES
            ],
            "final_snapshot_path": FINAL_SNAPSHOT_REPO_PATH,
            "next_phase": "AUTO_BOUND_REFERENCE_RESOLVER_INTEGRATION",
            "production_trust_permitted": False,
            "post_reservation_rebuild_required": False,
            "post_source_content_sync_rebuild_required": False,
            "protocol_revision": PROTOCOL,
            "registry_compatibility_index_is_not_snapshot_truth": True,
            "registry_snapshot": {
                "binding_eligible_version_count": registered_snapshot[
                    "counts"
                ][
                    "binding_eligible_version_count"
                ],
                "current_identity_count": registered_snapshot["counts"][
                    "identity_count"
                ],
                "current_instance_count": registered_snapshot["counts"][
                    "instance_count"
                ],
                "current_source_skill_count": registered_snapshot["counts"][
                    "source_skill_count"
                ],
                "current_version_count": registered_snapshot["counts"][
                    "version_count"
                ],
                "draft_snapshot": {
                    "artifact_digest": draft_snapshot[
                        "registry_snapshot_digest"
                    ],
                    "relative_path": SNAPSHOT_PATH.relative_to(
                        REPO_ROOT
                    ).as_posix(),
                    "status": "DRAFT_NON_ACTIVE",
                },
                "registered_candidate": {
                    "artifact_digest": registered_snapshot[
                        "registry_snapshot_digest"
                    ],
                    "relative_path": (
                        REGISTERED_CANDIDATE_SNAPSHOT_PATH
                        .relative_to(REPO_ROOT)
                        .as_posix()
                    ),
                    "status": "REGISTERED",
                },
                "draft_relative_path": SNAPSHOT_PATH.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "proposed_final_relative_path": (
                    FINAL_SNAPSHOT_REPO_PATH
                ),
                "registry_snapshot_digest": registered_snapshot[
                    "registry_snapshot_digest"
                ],
                "schema_id": SNAPSHOT_ID,
                "source_material_git_object_id": (
                    SOURCE_MATERIAL_GIT_OBJECT_ID
                ),
                "source_mirror_parity_satisfied": True,
                "status": "REGISTERED",
                "tracked_symlink_alias_count": registered_snapshot[
                    "counts"
                ]["tracked_symlink_alias_count"],
            },
            "registered_snapshot_external_trust_contract": {
                "registry_snapshot_digest": registered_snapshot[
                    "registry_snapshot_digest"
                ],
                "canonical_snapshot_path": FINAL_SNAPSHOT_REPO_PATH,
                "canonical_snapshot_schema_id": SNAPSHOT_ID,
                "mode": "REGISTERED",
                "verified_git_object_id_source": (
                    "REPO_EXTERNAL_MECHANISM_SUCCESSOR_COMMIT"
                ),
            },
            "source_content_sync_required": False,
            "resolver_contract": {
                "approved_surfaces": [
                    "CODEX_AUTOMATION",
                    "CODEX_CLI",
                ],
                "bound_output_schema_id": BINDING_ID,
                "candidate_bundle_required": True,
                "controlled_invocation_digest_contract": {
                    "self_digest_pointer": (
                        "/invocation_envelope_digest"
                    )
                },
                "current_snapshot_can_emit_bound": False,
                "fail_closed_unknown_reason_code": (
                    "MAPPING_NOT_PROVABLE"
                ),
                "full_seven_field_skill_ref_required": True,
                "implementation_status": (
                    "REGISTERED_NON_BINDING_MATERIALIZED"
                ),
                "request_schema_id": REQUEST_ID,
                "source_path_name_match_is_not_identity_evidence": True,
                "version_closure": (
                    "IDENTITY_TO_INSTANCE_TO_VERSION_"
                    "UNIQUE_AND_DIGEST_EXACT"
                ),
            },
            "source_drift_reconciliation": {
                "artifact_digest": reconciliation["artifact_digest"],
                "auto_evidence": {
                    "artifact_digest": (
                        AUTO_SOURCE_SYNC_INTERFACE_RAW_SHA256
                    ),
                    "verified_git_object_id": (
                        AUTO_SOURCE_SYNC_GIT_OBJECT_ID
                    ),
                },
                "current_source_alias_count": FROZEN_EXTERNAL_ALIAS_COUNT,
                "current_source_skill_count": EXPECTED_TOTAL_SKILLS,
                "historical_reconciliation_verified_git_object_id": (
                    HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID
                ),
                "historical_registry_records_retained": True,
                "missing_source_skill_roots": list(
                    AUTO_SOURCE_SYNC_MISSING_ROOTS
                ),
                "pending_content_drift_paths": [],
                "relative_path": DRIFT_PATH.relative_to(
                    REPO_ROOT
                ).as_posix(),
                "schema_id": DRIFT_ID,
                "source_alias_parity_satisfied": True,
                "source_content_sync_complete": True,
                "source_drift_reconciliation_complete": True,
                "source_mirror_parity_satisfied": True,
                "source_root_parity_satisfied": False,
                "status": (
                    "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
                ),
                "whole_source_parity_satisfied": False,
            },
            "source_digest_contract": {
                "alias_metadata_fields": [
                    "alias_path",
                    "normalized_target_ref",
                    "target_type",
                ],
                "canonicalization": "RFC8785_JCS_UTF8",
                "content_material_domain": (
                    "SKILLOPS_SKILL_CONTENT_V1"
                ),
                "content_material_fields": ["domain", "files"],
                "file_fields": [
                    "byte_count",
                    "content_digest",
                    "relative_path",
                ],
                "tree_material_domain": "SKILLOPS_SOURCE_TREE_V1",
                "tree_material_fields": [
                    "aliases",
                    "domain",
                    "files",
                    "source_class",
                    "source_material_policy_digest",
                ],
                "tree_paths_are_source_root_relative": True,
            },
            "runtime_artifacts": [
                {
                    "artifact_digest": _sha(builder_raw),
                    "relative_path": BUILDER_PATH,
                },
                {
                    "artifact_digest": _sha(runtime_raw),
                    "relative_path": RESOLVER_RUNTIME_PATH,
                },
            ],
            "schema_entries": _schema_entries(schemas),
            "schema_entry_count": len(schemas),
            "source_drift_reconciliation_complete": True,
            "source_mirror_parity_satisfied": True,
            "source_root_parity_satisfied": False,
            "status": (
                "DRAFT_NON_ACTIVE_PARITY_COMPLETE_MATERIALIZED"
            ),
            "whole_source_parity_satisfied": False,
        },
        "artifact_digest",
    )


def expected_outputs() -> Mapping[Path, bytes]:
    _tagged_commit_exists(CANDIDATE_GIT_OBJECT_ID)
    _tagged_commit_exists(SOURCE_MATERIAL_GIT_OBJECT_ID)
    _tagged_commit_exists(HISTORICAL_MATERIALIZATION_GIT_OBJECT_ID)
    _tagged_commit_exists(AUTO_SOURCE_SYNC_GIT_OBJECT_ID)
    schemas = {
        CATALOG_ID: registry_source_catalog_schema(),
        DRIFT_ID: source_drift_reconciliation_schema(),
        SNAPSHOT_ID: registry_snapshot_schema(),
        REQUEST_ID: bound_reference_request_schema(),
    }
    _verified_auto_source_sync()
    materialized, registered_snapshot, draft_snapshot = (
        _materialized_contracts(schemas)
    )
    outputs: Dict[Path, bytes] = {
        CATALOG_SCHEMA_PATH: _pretty(schemas[CATALOG_ID]),
        DRIFT_SCHEMA_PATH: _pretty(schemas[DRIFT_ID]),
        SNAPSHOT_SCHEMA_PATH: _pretty(schemas[SNAPSHOT_ID]),
        REQUEST_SCHEMA_PATH: _pretty(schemas[REQUEST_ID]),
        **materialized,
    }
    reconciliation_raw, reconciliation = (
        _historical_source_drift_reconciliation()
    )
    candidate = load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            CANDIDATE_GIT_OBJECT_ID,
            CANDIDATE_BUNDLE_DIGEST,
            CANDIDATE_MANIFEST_PATH,
            "CANDIDATE",
        ),
    )
    registry, checker = build_registry(
        {**candidate.schemas, **schemas}
    )
    errors = list(
        Draft202012Validator(
            schemas[DRIFT_ID],
            registry=registry,
            format_checker=checker,
        ).iter_errors(reconciliation)
    )
    if errors:
        raise ContractError(
            "REGISTRY_SOURCE_DRIFT_RECONCILIATION_SCHEMA_INVALID:"
            + errors[0].message
        )
    scan_public_value(reconciliation, candidate.policies)
    outputs[DRIFT_PATH] = reconciliation_raw
    interface = _interface(
        schemas,
        registered_snapshot,
        draft_snapshot,
        outputs,
        reconciliation,
    )
    scan_public_value(interface, candidate.policies)
    outputs[INTERFACE_PATH] = _pretty(interface)
    return outputs


def materialize(*, check: bool) -> int:
    outputs = expected_outputs()
    if check:
        mismatches = [
            path.relative_to(REPO_ROOT).as_posix()
            for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        if mismatches:
            print(
                "BOUND_REFERENCE_RESOLVER_MISMATCH:"
                + ",".join(mismatches),
                file=sys.stderr,
            )
            return 1
        action = "BOUND_REFERENCE_RESOLVER_BYTE_EQUIVALENT"
    else:
        for path, payload in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        action = "BOUND_REFERENCE_RESOLVER_GENERATED_OK"
    interface = parse_json_bytes(outputs[INTERFACE_PATH])
    snapshot = parse_json_bytes(outputs[FINAL_SNAPSHOT_PATH])
    print(
        f"{action} skills={snapshot['counts']['source_skill_count']} "
        f"catalogs={interface['catalog_count']} "
        f"binding_eligible="
        f"{snapshot['counts']['binding_eligible_version_count']} "
        f"source_drift="
        f"{interface['source_drift_reconciliation_complete']} "
        f"snapshot_digest={snapshot['registry_snapshot_digest']} "
        f"interface_raw_sha256={_sha(outputs[INTERFACE_PATH])}"
    )
    return 0


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    try:
        return materialize(check=args.check)
    except (ContractError, OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
