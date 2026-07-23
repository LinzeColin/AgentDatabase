#!/usr/bin/env python3
"""Build/check the non-active AU-040 exact-byte schema promotion."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))

from CodexSkills.governance.tools.canonical_json import (  # noqa: E402
    canonicalize_object,
    parse_json_bytes,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
POLICY_PREFIX = "urn:linzecolin:agentdatabase:skillops:policy:"

CURRENT_CANDIDATE_GIT_OBJECT = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
CURRENT_CANDIDATE_BUNDLE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
CURRENT_CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)

DRAFT_INTERFACE_REPO_PATH = (
    "CodexSkills/registry/auto/transport-draft/draft-interface.json"
)
DRAFT_INTERFACE_PATH = REPO_ROOT / DRAFT_INTERFACE_REPO_PATH
DRAFT_INTERFACE_RAW_SHA256 = (
    "aa4d1b174d45b87424b81f0896c7a594e72f24bfdc16e4128c133ed543fb3831"
)
DRAFT_INTERFACE_GIT_OBJECT = (
    "sha1:3a133ee8a812bac6a577e93102df9981240659e1"
)

ACCEPTANCE_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/au040/semantic-policy-acceptance.json"
)
ACCEPTANCE_INTERFACE_PATH = REPO_ROOT / ACCEPTANCE_INTERFACE_REPO_PATH
ACCEPTANCE_INTERFACE_RAW_SHA256 = (
    "3385df5975859ef0774d2086a8aa28a0336307e3343e7832eec9e2f024504fda"
)
ACCEPTANCE_INTERFACE_GIT_OBJECT = (
    "sha1:d4d488ab6f1720f3a837b071caf5c9cf6ac5f8e6"
)

PROMOTED_SCHEMA_DIR = AUTO_DIR / "schemas" / "public-v2"
PROMOTION_INTERFACE_PATH = PROMOTED_SCHEMA_DIR / "promotion-interface.json"
PROMOTION_INTERFACE_REPO_PATH = (
    "CodexSkills/registry/auto/schemas/public-v2/promotion-interface.json"
)

PRODUCTION_SEMANTIC_GUARD_CODES = (
    "CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE",
    "INDEX_EVENT_MANIFEST_CLOSURE",
    "MANIFEST_PART_IMMUTABILITY",
    "MANIFEST_PREDECESSOR_EXACT_CHAIN",
    "PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE",
    "RETENTION_ANCHOR_EXACT_365D",
    "SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE",
)

SCHEMA_CONTRACTS: Mapping[str, Mapping[str, Any]] = {
    SCHEMA_PREFIX + "daily-run-shard-manifest:v1": {
        "draft_relative_path": (
            "CodexSkills/registry/auto/transport-draft/schemas/public/"
            "daily-run-shard-manifest.schema.json"
        ),
        "canonical_relative_path": (
            "CodexSkills/registry/auto/schemas/public-v2/"
            "daily-run-shard-manifest.schema.json"
        ),
        "schema_sha256": (
            "e9214388da78376da47770934454d65a57659d1dde33fa0cb4e36b79e4665337"
        ),
        "self_digest_pointer": "/manifest_digest",
        "relationship": {"kind": "ADDS"},
    },
    SCHEMA_PREFIX + "publication-manifest:v2": {
        "draft_relative_path": (
            "CodexSkills/registry/auto/transport-draft/schemas/public/"
            "publication-manifest-v2.schema.json"
        ),
        "canonical_relative_path": (
            "CodexSkills/registry/auto/schemas/public-v2/"
            "publication-manifest-v2.schema.json"
        ),
        "schema_sha256": (
            "e7f8c4dd623379052829a21e3fcae77a98f14b3da1d79bb8f1d416f828063346"
        ),
        "self_digest_pointer": "/manifest_digest",
        "relationship": {
            "kind": "REPLACES",
            "replaces_schema_id": SCHEMA_PREFIX + "publication-manifest:v1",
        },
    },
    SCHEMA_PREFIX + "retention-receipt:v3": {
        "draft_relative_path": (
            "CodexSkills/registry/auto/transport-draft/schemas/public/"
            "retention-receipt-v3.schema.json"
        ),
        "canonical_relative_path": (
            "CodexSkills/registry/auto/schemas/public-v2/"
            "retention-receipt-v3.schema.json"
        ),
        "schema_sha256": (
            "81435881fbc5e1ced14975edbedee63ca6555674db36f906bdfdee20eb317c45"
        ),
        "self_digest_pointer": "/receipt_digest",
        "relationship": {
            "kind": "REPLACES",
            "replaces_schema_id": SCHEMA_PREFIX + "retention-receipt:v2",
        },
    },
    SCHEMA_PREFIX + "run-event-index-entry:v1": {
        "draft_relative_path": (
            "CodexSkills/registry/auto/transport-draft/schemas/public/"
            "run-event-index-entry.schema.json"
        ),
        "canonical_relative_path": (
            "CodexSkills/registry/auto/schemas/public-v2/"
            "run-event-index-entry.schema.json"
        ),
        "schema_sha256": (
            "27663e9da3d9511cf9a03d1fe6f4b3779b1bbdab8f2f8adb94a274b8653a1433"
        ),
        "self_digest_pointer": "/index_entry_digest",
        "relationship": {"kind": "ADDS"},
    },
}

EXPECTED_POLICY_MATERIAL = {
    POLICY_PREFIX + "public-value:v2": (
        "CodexSkills/governance/policies-v2/public-value-policy.v2.json",
        "cff871b00dec9d33ba6bd879e02b7039cef57d11e35bdc4c57a80d4d3ea519d4",
        SCHEMA_PREFIX + "public-value-policy:v2",
    ),
    POLICY_PREFIX + "retention:v3": (
        "CodexSkills/governance/policies-v2/retention-policy.v3.json",
        "bcad1e50a847e040d1350ca2fd977503b4ae642deabd727266e9dbbd26acb7ce",
        SCHEMA_PREFIX + "retention-policy:v3",
    ),
}
EXPECTED_POLICY_SCHEMA_MATERIAL = {
    SCHEMA_PREFIX + "public-value-policy:v2": (
        "CodexSkills/governance/schemas-v2/public-value-policy.schema.json",
        "16a233cab9f403b25da933414156f0f776a76c06518b792a0ff9691d813793aa",
    ),
    SCHEMA_PREFIX + "retention-policy:v3": (
        "CodexSkills/governance/schemas-v2/retention-policy.schema.json",
        "ad5637fad9600941db02ce3cc5f3078d9cc96730603407ff0c019588a32d0ea3",
    ),
}


@dataclasses.dataclass(frozen=True)
class PromotionSources:
    draft_interface: Mapping[str, Any]
    acceptance_interface: Mapping[str, Any]
    promoted_schema_entries: Tuple[Mapping[str, Any], ...]
    schema_bytes: Mapping[str, bytes]


def _strict_object(pairs: Sequence[Tuple[str, Any]]) -> Dict[str, Any]:
    value: Dict[str, Any] = {}
    for key, item in pairs:
        if key in value:
            raise ValueError(f"AUTO_SCHEMA_PROMOTION_DUPLICATE_KEY:{key}")
        value[key] = item
    return value


def _load_interface(
    path: Path,
    expected_raw_sha256: str,
    code: str,
) -> Mapping[str, Any]:
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise ValueError(f"{code}_READ_FAILED") from exc
    if hashlib.sha256(raw).hexdigest() != expected_raw_sha256:
        raise ValueError(f"{code}_RAW_DIGEST_MISMATCH")
    try:
        value = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"{code}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{code}_ROOT_INVALID")
    return value


def _validate_draft_interface(interface: Mapping[str, Any]) -> None:
    current = interface.get("current_trusted_candidate")
    target = interface.get("proposed_active_shared_set")
    loader = interface.get("loader_isolation_invariant")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("repository_bound") is not False
        or interface.get("au_040_complete") is not False
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("promotion_required_before_candidate_materialization")
        is not True
        or interface.get("draft_paths_forbidden_in_candidate_manifest")
        is not True
        or interface.get("next_phase")
        != "MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE"
        or not isinstance(current, dict)
        or current.get("git_object_id") != CURRENT_CANDIDATE_GIT_OBJECT
        or current.get("bundle_digest") != CURRENT_CANDIDATE_BUNDLE_DIGEST
        or current.get("schema_count") != 29
        or current.get("policy_count") != 5
        or not isinstance(target, dict)
        or target.get("target_schema_count") != 31
        or target.get("policy_count") != 5
        or not isinstance(loader, dict)
        or loader.get("current_candidate_recursive_loader_root")
        != "CodexSkills/registry/auto/schemas/public/"
        or loader.get("proposed_canonical_root")
        != "CodexSkills/registry/auto/schemas/public-v2/"
        or loader.get("proposed_paths_visible_to_current_loader") is not False
    ):
        raise ValueError("AUTO_SCHEMA_PROMOTION_DRAFT_CONTRACT_MISMATCH")


def _validate_policy_material(interface: Mapping[str, Any]) -> None:
    observed_policies = {
        entry.get("id"): (
            entry.get("relative_path"),
            entry.get("policy_sha256"),
            entry.get("schema_id"),
        )
        for entry in interface.get("mechanism_policy_entries", [])
        if isinstance(entry, dict)
    }
    observed_schemas = {
        entry.get("id"): (
            entry.get("relative_path"),
            entry.get("schema_sha256"),
        )
        for entry in interface.get("mechanism_policy_schema_entries", [])
        if isinstance(entry, dict)
    }
    if (
        observed_policies != EXPECTED_POLICY_MATERIAL
        or observed_schemas != EXPECTED_POLICY_SCHEMA_MATERIAL
    ):
        raise ValueError("AUTO_SCHEMA_PROMOTION_POLICY_MATERIAL_MISMATCH")


def _validate_acceptance_interface(interface: Mapping[str, Any]) -> None:
    source = interface.get("source_auto_draft_trust")
    current = interface.get("current_candidate")
    target = interface.get("target_shared_set")
    promotion = interface.get("promotion_contract")
    guards = interface.get("production_semantic_guard_codes_required")
    if (
        interface.get("status")
        != "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED"
        or interface.get("owner_plane") != "MECHANISM"
        or interface.get("repository_bound") is not False
        or interface.get("bundle_materialization_forbidden") is not True
        or interface.get("activation_forbidden") is not True
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("protocol_revision") != PROTOCOL
        or interface.get("next_phase")
        != "AUTO_SCHEMA_PROMOTION_TO_FINAL_PATHS"
        or not isinstance(source, dict)
        or source.get("canonical_interface_path")
        != DRAFT_INTERFACE_REPO_PATH
        or source.get("expected_interface_object_id")
        != "sha256:" + DRAFT_INTERFACE_RAW_SHA256
        or source.get("verified_git_object_id")
        != DRAFT_INTERFACE_GIT_OBJECT
        or source.get("mode") != "DRAFT_NON_ACTIVE"
        or not isinstance(current, dict)
        or current.get("git_object_id") != CURRENT_CANDIDATE_GIT_OBJECT
        or current.get("bundle_digest") != CURRENT_CANDIDATE_BUNDLE_DIGEST
        or current.get("schema_count") != 29
        or current.get("policy_count") != 5
        or not isinstance(target, dict)
        or target.get("target_schema_count") != 31
        or target.get("target_policy_count") != 5
        or not isinstance(promotion, dict)
        or promotion.get("auto_schema_bytes_may_change_during_promotion")
        is not False
        or promotion.get("draft_paths_forbidden_in_candidate_manifest")
        is not True
        or promotion.get("exact_byte_auto_schema_promotion_permitted")
        is not True
        or promotion.get("final_auto_schema_path")
        != "CodexSkills/registry/auto/schemas/public-v2"
        or promotion.get(
            "mechanism_semantic_guard_consumption_required_before_runtime_integration"
        )
        is not True
        or guards != list(PRODUCTION_SEMANTIC_GUARD_CODES)
        or interface.get("cross_artifact_semantic_gates")
        != [{"code": code} for code in PRODUCTION_SEMANTIC_GUARD_CODES]
    ):
        raise ValueError("AUTO_SCHEMA_PROMOTION_ACCEPTANCE_CONTRACT_MISMATCH")
    _validate_policy_material(interface)


def _schema_entry_map(
    entries: Any,
    *,
    code: str,
) -> Mapping[str, Mapping[str, Any]]:
    if not isinstance(entries, list):
        raise ValueError(f"{code}_ENTRIES_INVALID")
    identifiers = [
        entry.get("id")
        for entry in entries
        if isinstance(entry, dict)
    ]
    expected_ids = list(SCHEMA_CONTRACTS)
    if identifiers != expected_ids or len(identifiers) != len(entries):
        raise ValueError(f"{code}_ENTRY_ORDER_OR_SET_MISMATCH")
    return {entry["id"]: entry for entry in entries}


def load_sources(
    draft_interface_path: Path = DRAFT_INTERFACE_PATH,
    acceptance_interface_path: Path = ACCEPTANCE_INTERFACE_PATH,
) -> PromotionSources:
    draft = _load_interface(
        draft_interface_path,
        DRAFT_INTERFACE_RAW_SHA256,
        "AUTO_SCHEMA_PROMOTION_DRAFT_INTERFACE",
    )
    acceptance = _load_interface(
        acceptance_interface_path,
        ACCEPTANCE_INTERFACE_RAW_SHA256,
        "AUTO_SCHEMA_PROMOTION_ACCEPTANCE_INTERFACE",
    )
    _validate_draft_interface(draft)
    _validate_acceptance_interface(acceptance)
    draft_entries = _schema_entry_map(
        draft.get("draft_schema_entries"),
        code="AUTO_SCHEMA_PROMOTION_DRAFT",
    )
    accepted_entries = _schema_entry_map(
        acceptance.get("accepted_auto_transport_schemas"),
        code="AUTO_SCHEMA_PROMOTION_ACCEPTED",
    )

    promoted_entries = []
    schema_bytes: Dict[str, bytes] = {}
    for schema_id, expected in SCHEMA_CONTRACTS.items():
        draft_entry = draft_entries[schema_id]
        accepted_entry = accepted_entries[schema_id]
        expected_accepted = {
            "draft_relative_path": expected["draft_relative_path"],
            "id": schema_id,
            "proposed_canonical_relative_path": expected[
                "canonical_relative_path"
            ],
            "schema_sha256": expected["schema_sha256"],
            "self_digest_pointer": expected["self_digest_pointer"],
        }
        if accepted_entry != expected_accepted:
            raise ValueError(
                f"AUTO_SCHEMA_PROMOTION_ACCEPTED_SCHEMA_MISMATCH:{schema_id}"
            )
        if (
            draft_entry.get("draft_relative_path")
            != expected["draft_relative_path"]
            or draft_entry.get("proposed_canonical_relative_path")
            != expected["canonical_relative_path"]
            or draft_entry.get("schema_sha256") != expected["schema_sha256"]
            or draft_entry.get("self_digest_pointer")
            != expected["self_digest_pointer"]
            or draft_entry.get("relationship") != expected["relationship"]
            or draft_entry.get("owner_plane") != "AUTO"
            or draft_entry.get("visibility") != "PUBLIC"
        ):
            raise ValueError(
                f"AUTO_SCHEMA_PROMOTION_DRAFT_SCHEMA_MISMATCH:{schema_id}"
            )
        canonical_parts = Path(expected["canonical_relative_path"]).parts
        if (
            canonical_parts[:5]
            != (
                "CodexSkills",
                "registry",
                "auto",
                "schemas",
                "public-v2",
            )
            or "draft" in canonical_parts
        ):
            raise ValueError(
                f"AUTO_SCHEMA_PROMOTION_CANONICAL_PATH_INVALID:{schema_id}"
            )
        source_path = REPO_ROOT / expected["draft_relative_path"]
        try:
            raw = source_path.read_bytes()
        except OSError as exc:
            raise ValueError(
                f"AUTO_SCHEMA_PROMOTION_SOURCE_READ_FAILED:{schema_id}"
            ) from exc
        schema = parse_json_bytes(raw)
        if (
            not isinstance(schema, dict)
            or schema.get("$id") != schema_id
            or hashlib.sha256(canonicalize_object(schema)).hexdigest()
            != expected["schema_sha256"]
        ):
            raise ValueError(
                f"AUTO_SCHEMA_PROMOTION_SOURCE_SCHEMA_INVALID:{schema_id}"
            )
        raw_sha256 = hashlib.sha256(raw).hexdigest()
        schema_bytes[schema_id] = raw
        promoted_entries.append(
            {
                "canonical_relative_path": expected[
                    "canonical_relative_path"
                ],
                "draft_relative_path": expected["draft_relative_path"],
                "exact_bytes_equal": True,
                "id": schema_id,
                "raw_sha256": raw_sha256,
                "relationship": copy.deepcopy(expected["relationship"]),
                "schema_sha256": expected["schema_sha256"],
                "self_digest_pointer": expected["self_digest_pointer"],
            }
        )
    return PromotionSources(
        draft_interface=draft,
        acceptance_interface=acceptance,
        promoted_schema_entries=tuple(promoted_entries),
        schema_bytes=schema_bytes,
    )


def promotion_interface(sources: PromotionSources) -> Dict[str, Any]:
    acceptance = sources.acceptance_interface
    return {
        "activation_forbidden": True,
        "au_040_complete": False,
        "bundle_materialization_owner_plane": "MECHANISM",
        "bundle_materialization_performed": False,
        "canonical_publication_permitted": False,
        "current_trusted_candidate": {
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "canonical_manifest_path": CURRENT_CANDIDATE_MANIFEST_PATH,
            "git_object_id": CURRENT_CANDIDATE_GIT_OBJECT,
            "mode": "CANDIDATE",
            "policy_count": 5,
            "schema_count": 29,
            "unchanged_by_this_promotion": True,
        },
        "draft_paths_forbidden_in_candidate_manifest": True,
        "exact_byte_promotion_complete": True,
        "loader_isolation_invariant": {
            "current_candidate_recursive_loader_glob": "**/*.schema.json",
            "current_candidate_recursive_loader_root": (
                "CodexSkills/registry/auto/schemas/public/"
            ),
            "current_candidate_set_remains_exact": True,
            "promoted_canonical_root": (
                "CodexSkills/registry/auto/schemas/public-v2/"
            ),
            "promoted_paths_visible_to_current_loader": False,
        },
        "mechanism_semantic_policy_acceptance": {
            "interface_path": ACCEPTANCE_INTERFACE_REPO_PATH,
            "interface_raw_sha256": ACCEPTANCE_INTERFACE_RAW_SHA256,
            "mechanism_policy_entries": copy.deepcopy(
                acceptance["mechanism_policy_entries"]
            ),
            "mechanism_policy_schema_entries": copy.deepcopy(
                acceptance["mechanism_policy_schema_entries"]
            ),
            "production_semantic_guard_codes_acknowledged": list(
                PRODUCTION_SEMANTIC_GUARD_CODES
            ),
            "status": acceptance["status"],
            "verified_git_object_id": ACCEPTANCE_INTERFACE_GIT_OBJECT,
        },
        "next_phase": "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL",
        "owner_plane": "AUTO",
        "promoted_schema_count": len(sources.promoted_schema_entries),
        "promoted_schema_entries": [
            copy.deepcopy(entry)
            for entry in sources.promoted_schema_entries
        ],
        "promotion_required_before_candidate_materialization": True,
        "promotion_requirement_satisfied": True,
        "protocol_revision": PROTOCOL,
        "repository_bound": False,
        "runtime_integration_performed": False,
        "schema_version": (
            "urn:linzecolin:agentdatabase:skillops:"
            "interface:auto-schema-promotion:v1"
        ),
        "source_auto_draft_trust": {
            "canonical_interface_path": DRAFT_INTERFACE_REPO_PATH,
            "expected_interface_object_id": (
                "sha256:" + DRAFT_INTERFACE_RAW_SHA256
            ),
            "mode": "DRAFT_NON_ACTIVE",
            "verified_git_object_id": DRAFT_INTERFACE_GIT_OBJECT,
        },
        "target_shared_set": copy.deepcopy(
            acceptance["target_shared_set"]
        ),
        "status": "DRAFT_NON_ACTIVE_SCHEMA_PROMOTED",
    }


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def generated_files(
    sources: Optional[PromotionSources] = None,
) -> Mapping[Path, bytes]:
    observed = sources or load_sources()
    files: Dict[Path, bytes] = {}
    for entry in observed.promoted_schema_entries:
        files[REPO_ROOT / entry["canonical_relative_path"]] = (
            observed.schema_bytes[entry["id"]]
        )
    files[PROMOTION_INTERFACE_PATH] = _pretty(
        promotion_interface(observed)
    )
    return files


def materialize(check: bool) -> int:
    files = generated_files()
    mismatches = []
    for output_path, expected in files.items():
        if check:
            if (
                not output_path.is_file()
                or output_path.read_bytes() != expected
            ):
                mismatches.append(
                    output_path.relative_to(REPO_ROOT).as_posix()
                )
        else:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(expected)
    if mismatches:
        print(
            "AUTO_SCHEMA_PROMOTION_MISMATCH:"
            + ",".join(sorted(mismatches))
        )
        return 2
    interface_raw = files[PROMOTION_INTERFACE_PATH]
    print(
        "AUTO_SCHEMA_PROMOTION_BYTE_EQUIVALENT"
        if check
        else "AUTO_SCHEMA_PROMOTION_GENERATED_OK",
        f"interface_raw_sha256={hashlib.sha256(interface_raw).hexdigest()}",
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
