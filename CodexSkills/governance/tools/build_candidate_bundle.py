#!/usr/bin/env python3
"""Materialize the complete non-active SkillOps v0.0.0.3 candidate bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from canonical_json import (
    CanonicalizationError,
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from validate_mechanism import (
    AUTO_PRIVATE_SCHEMA_IDS,
    CANONICAL_MANIFEST_PATH,
    ContractBundle,
    ContractError,
    FINAL_AUTO_PUBLIC_SCHEMA_IDS,
    FINAL_AUTO_V2_SCHEMA_IDS,
    FINAL_BUNDLE_PROFILE,
    FINAL_POLICY_IDS,
    FINAL_SCHEMA_SELF_POINTERS,
    MANIFEST_SCHEMA_ID,
    PROTOCOL,
    build_registry,
    expected_policy_path_prefix,
    expected_schema_path_prefix,
    is_repo_relative_posix_path,
    load_draft_contract,
    load_schema_directories,
    scan_public_value,
    validate_instance,
)


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
AUTO_DIR = REPO_ROOT / "CodexSkills" / "registry" / "auto"
MECHANISM_INTERFACE_PATH = GOVERNANCE_DIR / "draft-interface.json"
AUTO_INTERFACE_PATH = AUTO_DIR / "draft-interface.json"
SEMANTIC_ACCEPTANCE_PATH = (
    GOVERNANCE_DIR / "au040" / "semantic-policy-acceptance.json"
)
PROMOTION_INTERFACE_PATH = (
    AUTO_DIR / "schemas" / "public-v2" / "promotion-interface.json"
)
MANIFEST_PATH = REPO_ROOT / CANONICAL_MANIFEST_PATH
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"

SRV_REVISION = "v0.0.0.3"
MECHANISM_INTERFACE_RAW_SHA256 = (
    "0f4837d9cec37c845cd5e9e799b5f572944cf8fe2457e8b95f696db3b9c03998"
)
AUTO_INTERFACE_RAW_SHA256 = (
    "2c47d6a810a18f878e3935bad9bde42aeb8e7f9c8c51b0ead19acadc48a2b366"
)
SEMANTIC_ACCEPTANCE_RAW_SHA256 = (
    "3385df5975859ef0774d2086a8aa28a0336307e3343e7832eec9e2f024504fda"
)
PROMOTION_INTERFACE_RAW_SHA256 = (
    "65c2e83bb2491d1cb3059767cf1705fc7541bd7e97449f33a51ba17a04f5e595"
)
SEMANTIC_ACCEPTANCE_GIT_OBJECT_ID = (
    "sha1:d4d488ab6f1720f3a837b071caf5c9cf6ac5f8e6"
)
PROMOTION_GIT_OBJECT_ID = (
    "sha1:ab49666bd3343c2abbfc6766478fad63d44163d0"
)
AUTO_BASE_MECHANISM_GIT_OBJECT_ID = (
    "sha1:37d07a47ae87fcf246046d1611d3e00f000d1fa4"
)
REPLACED_SCHEMA_IDS = {
    "urn:linzecolin:agentdatabase:skillops:schema:public-value-policy:v1",
    "urn:linzecolin:agentdatabase:skillops:schema:publication-manifest:v1",
    "urn:linzecolin:agentdatabase:skillops:schema:retention-policy:v2",
    "urn:linzecolin:agentdatabase:skillops:schema:retention-receipt:v2",
}
REPLACED_POLICY_IDS = {
    "urn:linzecolin:agentdatabase:skillops:policy:public-value:v1",
    "urn:linzecolin:agentdatabase:skillops:policy:retention:v2",
}
AUTO_PRIVATE_SELF_POINTERS = {
    "urn:linzecolin:agentdatabase:skillops:schema:lock-state:v1": "/state_digest",
    "urn:linzecolin:agentdatabase:skillops:schema:public-queue-envelope:v2": "/envelope_digest",
    "urn:linzecolin:agentdatabase:skillops:schema:raw-segment:v2": "/segment_digest",
    "urn:linzecolin:agentdatabase:skillops:schema:watermark:v2": "/state_digest",
}


def _load_pinned_interface(
    path: Path,
    expected_raw_sha256: str,
    code: str,
) -> Mapping[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ContractError(f"{code}_READ_FAILED:{exc}") from exc
    observed = hashlib.sha256(raw).hexdigest()
    if observed != expected_raw_sha256:
        raise ContractError(f"{code}_RAW_DIGEST_MISMATCH:{observed}")
    try:
        value = parse_json_bytes(raw)
    except CanonicalizationError as exc:
        raise ContractError(f"{code}_STRICT_JSON_REJECTED:{exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{code}_ROOT_INVALID")
    return value


def _git_blob(object_id: str, relative_path: str, code: str) -> bytes:
    if not object_id.startswith("sha1:") or not is_repo_relative_posix_path(
        relative_path
    ):
        raise ContractError(f"{code}_TRUST_TUPLE_INVALID")
    process = subprocess.run(
        [
            "git",
            "-C",
            str(REPO_ROOT),
            "show",
            f"{object_id.split(':', 1)[1]}:{relative_path}",
        ],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise ContractError(f"{code}_GIT_BLOB_UNAVAILABLE")
    return process.stdout


def _require_external_interface_binding(
    path: Path,
    *,
    object_id: str,
    expected_raw_sha256: str,
    code: str,
) -> Mapping[str, Any]:
    relative_path = path.relative_to(REPO_ROOT).as_posix()
    external = _git_blob(object_id, relative_path, code)
    current = path.read_bytes()
    if external != current:
        raise ContractError(f"{code}_CURRENT_BYTES_DRIFT")
    observed = hashlib.sha256(external).hexdigest()
    if observed != expected_raw_sha256:
        raise ContractError(f"{code}_RAW_DIGEST_MISMATCH:{observed}")
    try:
        value = parse_json_bytes(external)
    except CanonicalizationError as exc:
        raise ContractError(f"{code}_STRICT_JSON_REJECTED:{exc}") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{code}_ROOT_INVALID")
    return value


def _require_non_active_interface(
    interface: Mapping[str, Any],
    code: str,
) -> None:
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("protocol_revision") != PROTOCOL
    ):
        raise ContractError(f"{code}_NON_ACTIVE_CONTRACT_MISMATCH")


def _sorted_entries(entries: Any, code: str) -> List[Dict[str, Any]]:
    if not isinstance(entries, list) or not entries:
        raise ContractError(f"{code}_ENTRIES_INVALID")
    copied: List[Dict[str, Any]] = []
    identifiers: List[str] = []
    paths: List[str] = []
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise ContractError(f"{code}_ENTRY_INVALID:{index}")
        identifier = entry.get("id")
        relative_path = entry.get("relative_path")
        if not isinstance(identifier, str) or not isinstance(relative_path, str):
            raise ContractError(f"{code}_ENTRY_TYPES_INVALID:{index}")
        try:
            identifier.encode("ascii")
        except UnicodeEncodeError as exc:
            raise ContractError(f"{code}_ID_NON_ASCII:{identifier}") from exc
        copied.append(dict(entry))
        identifiers.append(identifier)
        paths.append(relative_path)
    expected_order = sorted(identifiers, key=lambda value: value.encode("ascii"))
    if identifiers != expected_order or len(identifiers) != len(set(identifiers)):
        raise ContractError(f"{code}_ID_ORDER_OR_UNIQUENESS")
    if len(paths) != len(set(paths)):
        raise ContractError(f"{code}_PATH_DUPLICATE")
    return copied


def _validate_schema_entries(
    entries: Sequence[Mapping[str, Any]],
    schemas: Mapping[str, Any],
) -> None:
    if {entry["id"] for entry in entries} != set(FINAL_SCHEMA_SELF_POINTERS):
        raise ContractError("CANDIDATE_SCHEMA_SET_MISMATCH")
    if {entry["id"] for entry in entries}.intersection(AUTO_PRIVATE_SCHEMA_IDS):
        raise ContractError("CANDIDATE_AUTO_PRIVATE_SCHEMA_INCLUDED")
    for entry in entries:
        schema_id = entry["id"]
        expected_owner = (
            "AUTO"
            if schema_id in FINAL_AUTO_PUBLIC_SCHEMA_IDS
            else "MECHANISM"
        )
        expected_prefix = expected_schema_path_prefix(
            FINAL_BUNDLE_PROFILE,
            schema_id,
        )
        if (
            entry.get("owner_plane") != expected_owner
            or entry.get("schema_version") != schema_id
            or entry.get("compatibility") != "EXACT_ONLY"
            or entry.get("self_digest_pointer")
            != FINAL_SCHEMA_SELF_POINTERS[schema_id]
            or not entry["relative_path"].startswith(expected_prefix)
        ):
            raise ContractError(f"CANDIDATE_SCHEMA_ENTRY_MISMATCH:{schema_id}")
        document = schemas.get(schema_id)
        if not isinstance(document, dict) or document.get("$id") != schema_id:
            raise ContractError(f"CANDIDATE_SCHEMA_BINDING_MISMATCH:{schema_id}")
        observed = hashlib.sha256(canonicalize_object(document)).hexdigest()
        if entry.get("schema_sha256") != observed:
            raise ContractError(f"CANDIDATE_SCHEMA_DIGEST_MISMATCH:{schema_id}")


def _normalize_auto_public_entries(
    entries: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for entry in entries:
        schema_id = entry["id"]
        if (
            schema_id not in FINAL_AUTO_PUBLIC_SCHEMA_IDS
            or entry.get("owner_plane") != "AUTO"
        ):
            raise ContractError(f"AUTO_PUBLIC_INTERFACE_ENTRY_MISMATCH:{schema_id}")
        normalized.append(
            {
                "id": schema_id,
                "owner_plane": "AUTO",
                "relative_path": entry["relative_path"],
                "schema_version": schema_id,
                "schema_sha256": entry.get("schema_sha256"),
                "compatibility": "EXACT_ONLY",
                "self_digest_pointer": entry.get("self_digest_pointer"),
            }
        )
    return normalized


def _validate_auto_private_exclusions(interface: Mapping[str, Any]) -> None:
    entries = _sorted_entries(
        interface.get("auto_private_schema_entries"),
        "AUTO_PRIVATE_SCHEMA",
    )
    if (
        interface.get("auto_private_schema_count") != len(entries)
        or len(entries) != 4
        or interface.get("auto_private_schemas_in_shared_bundle") is not False
        or {entry["id"] for entry in entries} != AUTO_PRIVATE_SCHEMA_IDS
    ):
        raise ContractError("AUTO_PRIVATE_INTERFACE_SET_MISMATCH")
    for entry in entries:
        schema_id = entry["id"]
        relative_path = entry["relative_path"]
        if (
            entry.get("owner_plane") != "AUTO"
            or entry.get("visibility") != "PRIVATE"
            or entry.get("self_digest_pointer")
            != AUTO_PRIVATE_SELF_POINTERS[schema_id]
            or not relative_path.startswith("CodexSkills/registry/auto/schemas/private/")
            or not is_repo_relative_posix_path(relative_path)
        ):
            raise ContractError(f"AUTO_PRIVATE_INTERFACE_ENTRY_MISMATCH:{schema_id}")
        path = REPO_ROOT.joinpath(*relative_path.split("/"))
        if not path.is_file() or path.is_symlink():
            raise ContractError(f"AUTO_PRIVATE_SCHEMA_FILE_INVALID:{schema_id}")
        try:
            path.resolve().relative_to(REPO_ROOT.resolve())
        except ValueError as exc:
            raise ContractError(
                f"AUTO_PRIVATE_SCHEMA_PATH_ESCAPES_ROOT:{schema_id}"
            ) from exc
        try:
            document = parse_json_bytes(path.read_bytes())
        except (OSError, CanonicalizationError) as exc:
            raise ContractError(f"AUTO_PRIVATE_SCHEMA_READ_FAILED:{schema_id}:{exc}") from exc
        observed = hashlib.sha256(canonicalize_object(document)).hexdigest()
        if (
            not isinstance(document, dict)
            or document.get("$id") != schema_id
            or entry.get("schema_sha256") != observed
        ):
            raise ContractError(f"AUTO_PRIVATE_SCHEMA_DIGEST_MISMATCH:{schema_id}")


def _validate_policy_entries(
    entries: Sequence[Mapping[str, Any]],
    policies: Mapping[str, Any],
) -> None:
    if {entry["id"] for entry in entries} != FINAL_POLICY_IDS:
        raise ContractError("CANDIDATE_POLICY_SET_MISMATCH")
    for entry in entries:
        policy_id = entry["id"]
        policy = policies.get(policy_id)
        if (
            entry.get("owner_plane") != "MECHANISM"
            or entry.get("compatibility") != "EXACT_ONLY"
            or not entry["relative_path"].startswith(
                expected_policy_path_prefix(
                    FINAL_BUNDLE_PROFILE,
                    policy_id,
                )
            )
            or not isinstance(policy, dict)
            or policy.get("policy_id") != policy_id
            or policy.get("schema_version") != entry.get("schema_id")
        ):
            raise ContractError(f"CANDIDATE_POLICY_ENTRY_MISMATCH:{policy_id}")
        observed = hashlib.sha256(canonicalize_object(policy)).hexdigest()
        if entry.get("policy_sha256") != observed:
            raise ContractError(f"CANDIDATE_POLICY_DIGEST_MISMATCH:{policy_id}")


def candidate_manifest() -> Tuple[Mapping[str, Any], ContractBundle]:
    """Return a validated manifest object without conferring candidate trust."""
    if VERSION_PATH.exists():
        raise ContractError("CANDIDATE_BUILD_ACTIVE_VERSION_FORBIDDEN")

    mechanism_interface = _load_pinned_interface(
        MECHANISM_INTERFACE_PATH,
        MECHANISM_INTERFACE_RAW_SHA256,
        "MECHANISM_INTERFACE",
    )
    auto_interface = _load_pinned_interface(
        AUTO_INTERFACE_PATH,
        AUTO_INTERFACE_RAW_SHA256,
        "AUTO_INTERFACE",
    )
    semantic_acceptance = _require_external_interface_binding(
        SEMANTIC_ACCEPTANCE_PATH,
        object_id=SEMANTIC_ACCEPTANCE_GIT_OBJECT_ID,
        expected_raw_sha256=SEMANTIC_ACCEPTANCE_RAW_SHA256,
        code="SEMANTIC_ACCEPTANCE",
    )
    promotion_interface = _require_external_interface_binding(
        PROMOTION_INTERFACE_PATH,
        object_id=PROMOTION_GIT_OBJECT_ID,
        expected_raw_sha256=PROMOTION_INTERFACE_RAW_SHA256,
        code="SCHEMA_PROMOTION",
    )
    _require_non_active_interface(mechanism_interface, "MECHANISM_INTERFACE")
    _require_non_active_interface(auto_interface, "AUTO_INTERFACE")

    if (
        mechanism_interface.get("target_srv") != SRV_REVISION
        or auto_interface.get("base_mechanism_git_object_id")
        != AUTO_BASE_MECHANISM_GIT_OBJECT_ID
        or auto_interface.get("mechanism_interface_raw_sha256")
        != MECHANISM_INTERFACE_RAW_SHA256
        or auto_interface.get("complete_shared_schema_count_after_m0b") != 29
        or auto_interface.get("auto_public_schema_count") != 8
        or auto_interface.get("next_phase") != "MECHANISM_M0B"
    ):
        raise ContractError("CANDIDATE_INPUT_INTERFACE_CONTRACT_MISMATCH")
    _validate_auto_private_exclusions(auto_interface)
    if (
        semantic_acceptance.get("status")
        != "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED"
        or semantic_acceptance.get("repository_bound") is not False
        or semantic_acceptance.get("bundle_materialization_forbidden")
        is not True
        or semantic_acceptance.get("canonical_publication_permitted")
        is not False
        or semantic_acceptance.get("protocol_revision") != PROTOCOL
        or semantic_acceptance.get("next_phase")
        != "AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS"
    ):
        raise ContractError("SEMANTIC_ACCEPTANCE_STATE_MISMATCH")
    promotion_acceptance = promotion_interface.get(
        "mechanism_semantic_policy_acceptance",
        {},
    )
    if (
        promotion_interface.get("status")
        != "DRAFT_NON_ACTIVE_SCHEMA_PROMOTED"
        or promotion_interface.get("exact_byte_promotion_complete") is not True
        or promotion_interface.get("promotion_requirement_satisfied") is not True
        or promotion_interface.get("repository_bound") is not False
        or promotion_interface.get("bundle_materialization_performed") is not False
        or promotion_interface.get("runtime_integration_performed") is not False
        or promotion_interface.get("canonical_publication_permitted") is not False
        or promotion_interface.get("activation_forbidden") is not True
        or promotion_interface.get("protocol_revision") != PROTOCOL
        or promotion_interface.get("next_phase")
        != "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL"
        or promotion_acceptance.get("interface_raw_sha256")
        != SEMANTIC_ACCEPTANCE_RAW_SHA256
        or promotion_acceptance.get("verified_git_object_id")
        != SEMANTIC_ACCEPTANCE_GIT_OBJECT_ID
    ):
        raise ContractError("SCHEMA_PROMOTION_STATE_MISMATCH")

    # The current generated manifest may be stale precisely because this
    # builder is replacing a non-active predecessor candidate.
    mechanism_bundle = load_draft_contract(lint_candidate_manifest=False)
    all_schemas = load_schema_directories(
        [
            GOVERNANCE_DIR / "schemas",
            GOVERNANCE_DIR / "schemas-v2",
            AUTO_DIR / "schemas" / "public",
            AUTO_DIR / "schemas" / "public-v2",
        ]
    )
    schemas = {
        schema_id: document
        for schema_id, document in all_schemas.items()
        if schema_id in FINAL_SCHEMA_SELF_POINTERS
    }
    if set(schemas) != set(FINAL_SCHEMA_SELF_POINTERS):
        raise ContractError("CANDIDATE_COMPLETE_SCHEMA_SET_MISMATCH")
    registry, checker = build_registry(schemas)
    policies = dict(mechanism_bundle.policies)
    for policy_id in REPLACED_POLICY_IDS:
        policies.pop(policy_id, None)
    replacement_policy_entries = _sorted_entries(
        semantic_acceptance.get("mechanism_policy_entries"),
        "MECHANISM_REPLACEMENT_POLICY",
    )
    for entry in replacement_policy_entries:
        policy = parse_json_bytes(
            REPO_ROOT.joinpath(*entry["relative_path"].split("/")).read_bytes()
        )
        if not isinstance(policy, dict):
            raise ContractError(
                f"CANDIDATE_REPLACEMENT_POLICY_ROOT_INVALID:{entry['id']}"
            )
        policies[entry["id"]] = policy
    if set(policies) != FINAL_POLICY_IDS:
        raise ContractError("CANDIDATE_COMPLETE_POLICY_SET_MISMATCH")
    bundle = ContractBundle(
        schemas,
        registry,
        checker,
        FINAL_SCHEMA_SELF_POINTERS,
        policies,
        PROTOCOL,
    )

    legacy_mechanism_schema_entries = _sorted_entries(
        mechanism_interface.get("mechanism_schema_entries"),
        "MECHANISM_SCHEMA",
    )
    replacement_mechanism_schema_entries = _sorted_entries(
        semantic_acceptance.get("mechanism_policy_schema_entries"),
        "MECHANISM_REPLACEMENT_SCHEMA",
    )
    mechanism_schema_entries = [
        entry
        for entry in legacy_mechanism_schema_entries
        if entry["id"] not in REPLACED_SCHEMA_IDS
    ]
    mechanism_schema_entries.extend(
        {
            "id": entry["id"],
            "owner_plane": "MECHANISM",
            "relative_path": entry["relative_path"],
            "schema_version": entry["id"],
            "schema_sha256": entry["schema_sha256"],
            "compatibility": "EXACT_ONLY",
            "self_digest_pointer": entry["self_digest_pointer"],
        }
        for entry in replacement_mechanism_schema_entries
    )
    legacy_auto_schema_entries = [
        entry
        for entry in _sorted_entries(
            auto_interface.get("auto_public_schema_entries"),
            "AUTO_PUBLIC_SCHEMA",
        )
        if entry["id"] not in REPLACED_SCHEMA_IDS
    ]
    promoted_raw = promotion_interface.get("promoted_schema_entries")
    if not isinstance(promoted_raw, list) or len(promoted_raw) != 4:
        raise ContractError("AUTO_PROMOTED_SCHEMA_ENTRIES_INVALID")
    promoted_schema_entries = sorted(
        [dict(entry) for entry in promoted_raw if isinstance(entry, dict)],
        key=lambda entry: str(entry.get("id", "")).encode("ascii"),
    )
    if (
        len(promoted_schema_entries) != 4
        or [entry.get("id") for entry in promoted_schema_entries]
        != [entry.get("id") for entry in promoted_raw]
        or len(
            {
                entry.get("canonical_relative_path")
                for entry in promoted_schema_entries
            }
        )
        != 4
    ):
        raise ContractError("AUTO_PROMOTED_SCHEMA_ORDER_OR_PATH_INVALID")
    for entry in promoted_schema_entries:
        schema_id = entry.get("id")
        canonical_path = entry.get("canonical_relative_path")
        draft_path = entry.get("draft_relative_path")
        if (
            schema_id not in FINAL_AUTO_V2_SCHEMA_IDS
            or not isinstance(canonical_path, str)
            or not canonical_path.startswith(
                "CodexSkills/registry/auto/schemas/public-v2/"
            )
            or not isinstance(draft_path, str)
            or entry.get("exact_bytes_equal") is not True
        ):
            raise ContractError(
                f"AUTO_PROMOTED_SCHEMA_CONTRACT_INVALID:{schema_id}"
            )
        canonical_raw = REPO_ROOT.joinpath(*canonical_path.split("/")).read_bytes()
        draft_raw = REPO_ROOT.joinpath(*draft_path.split("/")).read_bytes()
        external_raw = _git_blob(
            PROMOTION_GIT_OBJECT_ID,
            canonical_path,
            "AUTO_PROMOTED_SCHEMA",
        )
        if (
            canonical_raw != draft_raw
            or canonical_raw != external_raw
            or hashlib.sha256(canonical_raw).hexdigest()
            != entry.get("raw_sha256")
        ):
            raise ContractError(
                f"AUTO_PROMOTED_SCHEMA_EXACT_BYTES_MISMATCH:{schema_id}"
            )
    if (
        promotion_acceptance.get("mechanism_policy_entries")
        != semantic_acceptance.get("mechanism_policy_entries")
        or promotion_acceptance.get("mechanism_policy_schema_entries")
        != semantic_acceptance.get("mechanism_policy_schema_entries")
        or promotion_acceptance.get(
            "production_semantic_guard_codes_acknowledged"
        )
        != semantic_acceptance.get("production_semantic_guard_codes_required")
    ):
        raise ContractError("SCHEMA_PROMOTION_ACCEPTANCE_ACK_MISMATCH")
    auto_schema_entries = _normalize_auto_public_entries(
        [
            *legacy_auto_schema_entries,
            *(
                {
                    "id": entry["id"],
                    "owner_plane": "AUTO",
                    "relative_path": entry["canonical_relative_path"],
                    "schema_sha256": entry["schema_sha256"],
                    "self_digest_pointer": entry["self_digest_pointer"],
                }
                for entry in promoted_schema_entries
            ),
        ]
    )
    schema_entries = sorted(
        [*mechanism_schema_entries, *auto_schema_entries],
        key=lambda entry: entry["id"].encode("ascii"),
    )
    policy_entries = [
        entry
        for entry in _sorted_entries(
            mechanism_interface.get("mechanism_policy_entries"),
            "MECHANISM_POLICY",
        )
        if entry["id"] not in REPLACED_POLICY_IDS
    ]
    policy_entries.extend(
        {
            "id": entry["id"],
            "owner_plane": "MECHANISM",
            "relative_path": entry["relative_path"],
            "schema_id": entry["schema_id"],
            "policy_sha256": entry["policy_sha256"],
            "compatibility": "EXACT_ONLY",
        }
        for entry in replacement_policy_entries
    )
    policy_entries.sort(key=lambda entry: entry["id"].encode("ascii"))
    if (
        len(mechanism_schema_entries) != 21
        or len(auto_schema_entries) != 10
        or len(schema_entries) != 31
        or len(policy_entries) != 5
    ):
        raise ContractError("CANDIDATE_MEMBER_COUNT_MISMATCH")
    _validate_schema_entries(schema_entries, schemas)
    _validate_policy_entries(policy_entries, policies)
    for entry in policy_entries:
        validate_instance(
            bundle,
            policies[entry["id"]],
            entry["schema_id"],
            verify_digest=False,
        )

    canonicalization = mechanism_interface.get("canonicalization")
    if not isinstance(canonicalization, dict):
        raise ContractError("CANDIDATE_CANONICALIZATION_CONTRACT_MISSING")
    expected_canonicalization = {
        "scheme": "RFC8785_JCS",
        "input_profile": "I_JSON",
        "encoding": "UTF-8",
        "unicode_normalization": "NONE",
        "duplicate_keys": "REJECT",
        "self_digest_exclusion": "EXACT_DECLARED_JSON_POINTER_ONLY",
    }
    if {
        key: canonicalization.get(key)
        for key in expected_canonicalization
    } != expected_canonicalization:
        raise ContractError("CANDIDATE_CANONICALIZATION_CONTRACT_MISMATCH")
    test_vectors_digest = canonicalization.get("test_vectors_digest")
    if not isinstance(test_vectors_digest, str):
        raise ContractError("CANDIDATE_TEST_VECTOR_DIGEST_MISSING")

    manifest: Dict[str, Any] = {
        "schema_version": MANIFEST_SCHEMA_ID,
        "protocol_revision": PROTOCOL,
        "srv_revision": SRV_REVISION,
        "canonicalization": expected_canonicalization,
        "digest_algorithm": "SHA-256",
        "test_vectors_digest": test_vectors_digest,
        "schemas": schema_entries,
        "schema_count": len(schema_entries),
        "policies": policy_entries,
        "policy_count": len(policy_entries),
        "compatibility": {
            "active_bundle_mode": "EXACT_DIGEST",
            "accepted_predecessor_bundle_digests": [],
            "predecessor_acceptance_expires_at": None,
        },
        "bundle_digest": "0" * 64,
    }
    manifest["bundle_digest"] = canonical_digest(manifest, "/bundle_digest")
    validate_instance(
        bundle,
        manifest,
        MANIFEST_SCHEMA_ID,
        expected_bundle_digest=manifest["bundle_digest"],
    )
    scan_public_value(manifest, policies)
    return manifest, bundle


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def materialize(check: bool) -> int:
    manifest, _ = candidate_manifest()
    expected = _pretty(manifest)
    if check:
        try:
            observed = MANIFEST_PATH.read_bytes()
        except OSError as exc:
            raise ContractError(f"CANDIDATE_MANIFEST_READ_FAILED:{exc}") from exc
        if observed != expected:
            print("CANDIDATE_BUNDLE_GENERATED_MISMATCH", file=sys.stderr)
            return 1
        action = "CANDIDATE_BUNDLE_BYTE_EQUIVALENT"
    else:
        MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
        MANIFEST_PATH.write_bytes(expected)
        action = "CANDIDATE_BUNDLE_GENERATED_OK"
    print(
        f"{action} bundle_digest={manifest['bundle_digest']} "
        f"schemas={manifest['schema_count']} policies={manifest['policy_count']}"
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
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
