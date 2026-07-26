#!/usr/bin/env python3
"""Build/check deterministic Auto activation-handshake interface evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from pathlib import Path

SCRIPT_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(SCRIPT_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(SCRIPT_REPO_ROOT))

from CodexSkills.registry.auto.runtime.catalog_reservation import (
    EXPECTED_SOURCE_ALIASES,
    EXPECTED_SOURCE_ALIAS_COUNT,
    EXPECTED_SOURCE_ALIAS_SET_DIGEST,
    HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT,
    HISTORICAL_SOURCE_SKILL_COUNT,
    HISTORICAL_SOURCE_SKILL_COUNTS,
    SOURCE_NAMESPACES,
    alias_set_digest,
    assert_exact_alias_set,
    reserved_registry_paths,
)


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
OUTPUT = AUTO_DIR / "runtime-interface.json"
HISTORICAL_CANDIDATE_GIT_OBJECT = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
HISTORICAL_CANDIDATE_BUNDLE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
FINAL_CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
FINAL_CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_MANIFEST_PATH = "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
EXPECTED_FINAL_CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995"
    "f7a45998936ca720c6db678ee77e65a"
)
CONSUMER_FIRST_EVIDENCE_GIT_OBJECT = (
    "sha1:91a12e48351be3ee05ec23ef61aec81056b02014"
)
CONSUMER_INTERFACE_PATH = (
    REPO_ROOT
    / "OpenAIDatabase"
    / "config"
    / "evaluation"
    / "skill_run_consumer.json"
)
CONSUMER_INTERFACE_REPO_PATH = (
    "OpenAIDatabase/config/evaluation/skill_run_consumer.json"
)
EXPECTED_CONSUMER_INTERFACE_RAW_SHA256 = (
    "189a47300fc1aa6012e87feb6184833cb"
    "717cdbe2b9dc9be6db89197f579939c"
)
CONTROL_INTERFACE_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "governance"
    / "activation"
    / "control-interface.json"
)
CONTROL_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/activation/control-interface.json"
)
CONTROL_EVIDENCE_GIT_OBJECT = (
    "sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea"
)
EXPECTED_CONTROL_INTERFACE_RAW_SHA256 = (
    "28a35148cc18362de4fc53b508754f263"
    "a015cf33e4cd187314cf48c767b6920"
)
CONTROL_BOUND_AUTO_GIT_OBJECT = (
    "sha1:85edc67df48d4e5bc783f89ed3f3371f25f288e1"
)
CONTROL_BOUND_AUTO_RUNTIME_INTERFACE_RAW_SHA256 = (
    "ce3aae7a22419c3a01455e8e83cc67b2"
    "3eeb2ada3f3c17e57590a890c0fdef31"
)
CONTROL_BOUND_AUTO_MODULE_COUNT = 25
PUBLISHER_MATERIALIZATION_CONTROL_GIT_OBJECT = (
    "sha1:fb9b99c36cb870b04f34b5ed3bcb75aeae52c296"
)
CATALOG_RESERVATION_CONTROL_GIT_OBJECT = (
    "sha1:488321c83b2a669ea964873e22a94b8e65429350"
)
EXPECTED_CATALOG_RESERVATION_CONTROL_RAW_SHA256 = (
    "6f7a2bdedfc7c388c4b6e1c2345855e"
    "110305b7ed906874676a5ba6daf7779f2"
)
RESOLVER_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/registry/resolver-interface.json"
)
EXPECTED_RESOLVER_INTERFACE_RAW_SHA256 = (
    "0fe26ab55d92a1c6f5628e2a8d27bec"
    "bdcc839ccfd73372150a2339ffe7eb4cb"
)
SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT = (
    "sha1:5db5beecf3de7ac916020ca988f6e875891e19b1"
)
EXPECTED_SOURCE_CONTENT_SYNC_CONTROL_RAW_SHA256 = (
    "a31751bf1258f646412aba84e0b5c46f"
    "84f09b77e33156caea372873b819ff36"
)
EXPECTED_SOURCE_CONTENT_SYNC_RESOLVER_RAW_SHA256 = (
    "38c7952ae712e6d4543bb4f4c1f3e5f8"
    "a98b00b36780c99bfce6944a722eabf0"
)
SOURCE_DRIFT_RECONCILIATION_REPO_PATH = (
    "CodexSkills/governance/registry/"
    "source-drift-reconciliation.v1.json"
)
EXPECTED_SOURCE_DRIFT_RECONCILIATION_RAW_SHA256 = (
    "f36f20f8ee8551eae155c5b58ba0d776"
    "cc4fdd2b9f08d3186519ce052a297120"
)
EXPECTED_SOURCE_DRIFT_RECONCILIATION_SELF_DIGEST = (
    "24d02db5182463912074c109f2b5be350"
    "126d62340f58e6463755edbad1b799c"
)
SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT = (
    "sha1:b5a32c817e4016f595fa33caed6bce1d51199e63"
)
SOURCE_CONTENT_SYNC_BOUND_AUTO_INTERFACE_RAW_SHA256 = (
    "e88ec8c711434619756ee8f91c451e94"
    "1501764e30e4a7fff310d8685b02140a"
)
SOURCE_CONTENT_SYNC_BOUND_AUTO_MODULE_COUNT = 27
SOURCE_CONTENT_SYNC_NEXT_PHASE = (
    "MECHANISM_REGISTRY_PARITY_COMPLETE_MATERIALIZATION"
)
SOURCE_CONTENT_SYNC_ENTRIES = [
    {
        "alias_count": 0,
        "byte_count": 13373911,
        "content_digest": (
            "816bfb795d8998983a3df2b8786a2d1c"
            "691e9e2280dd7be2bdc07acd47775587"
        ),
        "regular_file_count": 695,
        "source_relative_path": "codex/graphify",
    },
    {
        "alias_count": 0,
        "byte_count": 1064137,
        "content_digest": (
            "eaf8f8e32b1ade683387346adec8a21b"
            "241541567e910609247426ec3626b921"
        ),
        "regular_file_count": 35,
        "source_relative_path": "codex/persona-distiller-group",
    },
    {
        "alias_count": 0,
        "byte_count": 525884,
        "content_digest": (
            "7727bcfb4d03bcc97fafeedea1f8e773"
            "945e6be70f0351e8ca32525ff1e8d556"
        ),
        "regular_file_count": 61,
        "source_relative_path": "codex/verifier",
    },
]
INCOMPLETE_REGISTRY_SNAPSHOT_DIGEST = (
    "31f49c8ffa3bd2d268feec49b2869f40"
    "9d61a5bfbb0b03f382bc562996b7fa76"
)
CATALOG_RESERVATION_BOUND_AUTO_GIT_OBJECT = (
    "sha1:49ac09dbd9c8a2e18d5a199088a910dc77e7d365"
)
CATALOG_RESERVATION_BOUND_AUTO_INTERFACE_RAW_SHA256 = (
    "c7af9d1406fe2ed084d5a30fab6cded3"
    "897a83c1602e6c40587cf28c75a2c75c"
)
CATALOG_RESERVATION_BOUND_AUTO_MODULE_COUNT = 26
CURRENT_SOURCE_SKILL_COUNTS = {
    "agents": 24,
    "claude": 3,
    "codex": 55,
    "codex-system": 6,
}
CURRENT_SOURCE_SKILL_COUNT = 88
MISSING_SOURCE_SKILL_ROOTS = ["codex/context-kernel"]
NON_ALIAS_CONTENT_DRIFT_OBSERVED_PATHS = [
    "codex/graphify",
    "codex/persona-distiller-group",
    "codex/verifier",
]
SOURCE_SCAN_OBSERVATIONS = [
    {
        "alias_count": 0,
        "completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "included_file_count": 350,
        "included_tree_digest": (
            "93af33c94c38f910df35a08dfd294a95"
            "5b137d74bec6eebb4e083825014c7a64"
        ),
        "source_namespace": "agents",
        "source_snapshot_digest": (
            "9cc710e9dc8d6bf011f19e4576d4e558"
            "dd6cdd72f0814e519b23d7aa08de47c5"
        ),
    },
    {
        "alias_count": 0,
        "completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "included_file_count": 191,
        "included_tree_digest": (
            "03d37e741ace0feffc19a4dac1f3550b"
            "8ffccb0d6d66c95cb84fe6cf250e8e2b"
        ),
        "source_namespace": "claude",
        "source_snapshot_digest": (
            "b7c44c9118f1385ffb82c7a4c32e6e5"
            "db00d74d5aab43e9066259bc375459dc4"
        ),
    },
    {
        "alias_count": 20,
        "completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "included_file_count": 3091,
        "included_tree_digest": (
            "746b945b967502edd30872a69a713cd67"
            "9432ef89059856cbe819fa74e06cab5"
        ),
        "source_namespace": "codex",
        "source_snapshot_digest": (
            "1f41a69acd5de4a0017ae596bf80ce706"
            "32369ddf2377eb4fe659fc00f7905b4"
        ),
    },
    {
        "alias_count": 0,
        "completeness_status": "COMPLETE_AFTER_POLICY_EXCLUSIONS",
        "included_file_count": 54,
        "included_tree_digest": (
            "cbd66243b0c52fabe69284386316350ee"
            "5ef6e7308bdd9e629c2abffefd9b378"
        ),
        "source_namespace": "codex-system",
        "source_snapshot_digest": (
            "33163f9473ca2865e5bf159eff9140105"
            "83a842842c1bcc8aa4d567db9b70a36"
        ),
    },
]
REMOVED_SOURCE_SKILL_PATHS = [
    "CodexSkills/registry/codex/context-kernel/MANIFEST.json",
    "CodexSkills/registry/codex/context-kernel/SKILL.md",
    "CodexSkills/registry/codex/context-kernel/scripts/context_kernel.py",
]
ALIAS_CONTENT_DIGESTS = {
    "DIRECTORY": (
        "6fce6f28999e3684c13505d67201175c"
        "e50e08d9867fc61931b9036c05e8f255"
    ),
    "REGULAR_FILE": (
        "1900bd27da156a2048919a652980b2c4"
        "7a44b6f1e8b85f1b32cc5b31e26a6e0e"
    ),
}
EXPECTED_CONSUMER_REQUIRED_GATES = [
    "ACTIVE_EXTERNAL_TRUST",
    "AU_040_DAILY_JSONL_SHARD_MANIFEST",
    "BOUND_REFERENCE_RESOLVER",
]
TRANSPORT_DRAFT_INTERFACE_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "registry"
    / "auto"
    / "transport-draft"
    / "draft-interface.json"
)
TRANSPORT_DRAFT_INTERFACE_REPO_PATH = (
    "CodexSkills/registry/auto/transport-draft/draft-interface.json"
)
EXPECTED_TRANSPORT_DRAFT_INTERFACE_RAW_SHA256 = (
    "aa4d1b174d45b87424b81f0896c7a594"
    "e72f24bfdc16e4128c133ed543fb3831"
)
EXPECTED_TRANSPORT_ALLOWLIST_DELTA = [
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
SCHEMA_PROMOTION_INTERFACE_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "registry"
    / "auto"
    / "schemas"
    / "public-v2"
    / "promotion-interface.json"
)
SCHEMA_PROMOTION_INTERFACE_REPO_PATH = (
    "CodexSkills/registry/auto/schemas/public-v2/promotion-interface.json"
)
EXPECTED_SCHEMA_PROMOTION_INTERFACE_RAW_SHA256 = (
    "65c2e83bb2491d1cb3059767cf1705fc"
    "7541bd7e97449f33a51ba17a04f5e595"
)
AU040_ACCEPTANCE_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/au040/semantic-policy-acceptance.json"
)
EXPECTED_AU040_ACCEPTANCE_INTERFACE_RAW_SHA256 = (
    "3385df5975859ef0774d2086a8aa28a0"
    "336307e3343e7832eec9e2f024504fda"
)
AU040_ACCEPTANCE_VERIFIED_GIT_OBJECT = (
    "sha1:d4d488ab6f1720f3a837b071caf5c9cf6ac5f8e6"
)
EXPECTED_AU040_GUARD_CODES = [
    "CANONICAL_BYTES_PHYSICAL_DIGEST_CLOSURE",
    "INDEX_EVENT_MANIFEST_CLOSURE",
    "MANIFEST_PART_IMMUTABILITY",
    "MANIFEST_PREDECESSOR_EXACT_CHAIN",
    "PRUNE_TRANSACTION_ARTIFACT_SET_CLOSURE",
    "RETENTION_ANCHOR_EXACT_365D",
    "SHARD_TRANSACTION_ARTIFACT_SET_CLOSURE",
]
EXPECTED_PROMOTED_SCHEMA_IDS = [
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:daily-run-shard-manifest:v1",
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:publication-manifest:v2",
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:retention-receipt:v3",
    "urn:linzecolin:agentdatabase:skillops:"
    "schema:run-event-index-entry:v1",
]
SCHEMA_PROMOTION_EVIDENCE_GIT_OBJECT = (
    "sha1:ab49666bd3343c2abbfc6766478fad63d44163d0"
)
HISTORICAL_CANDIDATE_MANIFEST_RAW_SHA256 = (
    "0d2600fd54fcb1fb5dd0901d9acc31b43b5cae0be8ee599f5c3c7ca0b01f9109"
)


def _strict_object(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("AUTO_CONSUMER_INTERFACE_DUPLICATE_KEY")
        value[key] = item
    return value


def _git_blob(object_id, relative_path):
    if (
        not object_id.startswith("sha1:")
        or len(object_id) != len("sha1:") + 40
    ):
        raise ValueError("AUTO_RUNTIME_INTERFACE_GIT_OBJECT_ID_INVALID")
    try:
        result = subprocess.run(
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
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(
            "AUTO_RUNTIME_INTERFACE_HISTORICAL_BLOB_READ_FAILED"
        ) from exc
    if result.returncode != 0:
        raise ValueError(
            "AUTO_RUNTIME_INTERFACE_HISTORICAL_BLOB_READ_FAILED"
        )
    return result.stdout


def _consumer_first_evidence(path=CONSUMER_INTERFACE_PATH):
    raw = path.read_bytes()
    observed_raw_digest = hashlib.sha256(raw).hexdigest()
    if observed_raw_digest != EXPECTED_CONSUMER_INTERFACE_RAW_SHA256:
        raise ValueError("AUTO_CONSUMER_INTERFACE_RAW_DIGEST_MISMATCH")
    try:
        interface = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AUTO_CONSUMER_INTERFACE_JSON_INVALID") from exc
    expected_trust = {
        "canonical_manifest_path": CANDIDATE_MANIFEST_PATH,
        "expected_bundle_digest": FINAL_CANDIDATE_BUNDLE_DIGEST,
        "mode": "CANDIDATE",
        "verified_git_object_id": FINAL_CANDIDATE_GIT_OBJECT,
    }
    expected_gate = {
        "canonical_publication_permitted": False,
        "repository_shards_permitted": False,
        "required_before_enable": EXPECTED_CONSUMER_REQUIRED_GATES,
    }
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE_CONSUMER_READY"
        or interface.get("schema_version")
        != "openai_database.skill_run_consumer.v2"
        or interface.get("consumer_owner_plane") != "MECHANISM"
        or interface.get("candidate_trust") != expected_trust
        or interface.get("publication_gate") != expected_gate
        or set(interface.get("artifact_contracts", {}))
        != {"daily_manifest", "index", "part", "retention_receipt"}
    ):
        raise ValueError("AUTO_CONSUMER_INTERFACE_CONTRACT_MISMATCH")
    if (
        _git_blob(
            CONSUMER_FIRST_EVIDENCE_GIT_OBJECT,
            CONSUMER_INTERFACE_REPO_PATH,
        )
        != raw
    ):
        raise ValueError("AUTO_CONSUMER_INTERFACE_GIT_BLOB_DRIFT")
    return {
        "canonical_publication_permitted": False,
        "contract_revision": "V2",
        "expected_bundle_digest": FINAL_CANDIDATE_BUNDLE_DIGEST,
        "required_before_enable": list(EXPECTED_CONSUMER_REQUIRED_GATES),
        "repository_shards_permitted": False,
        "status": "DRAFT_NON_ACTIVE_CONSUMER_READY",
        "verified_git_object_id": FINAL_CANDIDATE_GIT_OBJECT,
    }


def _transport_draft_evidence(path=TRANSPORT_DRAFT_INTERFACE_PATH):
    raw = path.read_bytes()
    observed_raw_digest = hashlib.sha256(raw).hexdigest()
    if observed_raw_digest != EXPECTED_TRANSPORT_DRAFT_INTERFACE_RAW_SHA256:
        raise ValueError("AUTO_TRANSPORT_DRAFT_INTERFACE_RAW_DIGEST_MISMATCH")
    try:
        interface = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AUTO_TRANSPORT_DRAFT_INTERFACE_JSON_INVALID") from exc
    current = interface.get("current_trusted_candidate")
    target = interface.get("proposed_active_shared_set")
    loader = interface.get("loader_isolation_invariant")
    validation_context = interface.get("draft_validation_context")
    entries = interface.get("draft_schema_entries")
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
        or interface.get("required_mechanism_public_value_allowlist_additions")
        != EXPECTED_TRANSPORT_ALLOWLIST_DELTA
        or not isinstance(current, dict)
        or current.get("git_object_id")
        != HISTORICAL_CANDIDATE_GIT_OBJECT
        or current.get("bundle_digest")
        != HISTORICAL_CANDIDATE_BUNDLE_DIGEST
        or current.get("schema_count") != 29
        or current.get("policy_count") != 5
        or current.get("unchanged_by_this_draft") is not True
        or not isinstance(target, dict)
        or target.get("target_schema_count") != 31
        or target.get("policy_count") != 5
        or not isinstance(loader, dict)
        or loader.get("current_candidate_recursive_loader_root")
        != "CodexSkills/registry/auto/schemas/public/"
        or loader.get("proposed_canonical_root")
        != "CodexSkills/registry/auto/schemas/public-v2/"
        or loader.get("proposed_paths_visible_to_current_loader") is not False
        or not isinstance(validation_context, dict)
        or validation_context.get("retention_policy_v3_present") is not False
        or validation_context.get("mechanism_policy_acceptance_required")
        is not True
        or not isinstance(entries, list)
        or len(entries) != 4
        or any(
            "/transport-draft/" not in entry.get("draft_relative_path", "")
            or not entry.get("proposed_canonical_relative_path", "").startswith(
                "CodexSkills/registry/auto/schemas/public-v2/"
            )
            for entry in entries
        )
    ):
        raise ValueError("AUTO_TRANSPORT_DRAFT_INTERFACE_CONTRACT_MISMATCH")
    return {
        "allowlist_delta": list(EXPECTED_TRANSPORT_ALLOWLIST_DELTA),
        "current_schema_count": 29,
        "draft_schema_count": 4,
        "next_phase": interface["next_phase"],
        "policy_count": 5,
        "retention_policy_v3_present": False,
        "target_schema_count": 31,
    }


def _schema_promotion_evidence(path=SCHEMA_PROMOTION_INTERFACE_PATH):
    raw = path.read_bytes()
    observed_raw_digest = hashlib.sha256(raw).hexdigest()
    if (
        observed_raw_digest
        != EXPECTED_SCHEMA_PROMOTION_INTERFACE_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    try:
        interface = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_INTERFACE_JSON_INVALID"
        ) from exc
    current = interface.get("current_trusted_candidate")
    acceptance = interface.get("mechanism_semantic_policy_acceptance")
    isolation = interface.get("loader_isolation_invariant")
    target = interface.get("target_shared_set")
    entries = interface.get("promoted_schema_entries")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE_SCHEMA_PROMOTED"
        or interface.get("owner_plane") != "AUTO"
        or interface.get("activation_forbidden") is not True
        or interface.get("repository_bound") is not False
        or interface.get("au_040_complete") is not False
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("bundle_materialization_performed") is not False
        or interface.get("runtime_integration_performed") is not False
        or interface.get("exact_byte_promotion_complete") is not True
        or interface.get("promotion_requirement_satisfied") is not True
        or interface.get("draft_paths_forbidden_in_candidate_manifest")
        is not True
        or interface.get("next_phase")
        != "MECHANISM_FINAL_31_5_CANDIDATE_CONSUMER_CONTROL"
        or not isinstance(current, dict)
        or current.get("git_object_id")
        != HISTORICAL_CANDIDATE_GIT_OBJECT
        or current.get("bundle_digest")
        != HISTORICAL_CANDIDATE_BUNDLE_DIGEST
        or current.get("schema_count") != 29
        or current.get("policy_count") != 5
        or current.get("canonical_manifest_path")
        != CANDIDATE_MANIFEST_PATH
        or current.get("mode") != "CANDIDATE"
        or current.get("unchanged_by_this_promotion") is not True
        or not isinstance(acceptance, dict)
        or acceptance.get("interface_path")
        != AU040_ACCEPTANCE_INTERFACE_REPO_PATH
        or acceptance.get("interface_raw_sha256")
        != EXPECTED_AU040_ACCEPTANCE_INTERFACE_RAW_SHA256
        or acceptance.get("verified_git_object_id")
        != AU040_ACCEPTANCE_VERIFIED_GIT_OBJECT
        or acceptance.get("status")
        != "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED"
        or acceptance.get(
            "production_semantic_guard_codes_acknowledged"
        )
        != EXPECTED_AU040_GUARD_CODES
        or not isinstance(isolation, dict)
        or isolation.get("current_candidate_recursive_loader_root")
        != "CodexSkills/registry/auto/schemas/public/"
        or isolation.get("promoted_canonical_root")
        != "CodexSkills/registry/auto/schemas/public-v2/"
        or isolation.get("promoted_paths_visible_to_current_loader")
        is not False
        or not isinstance(target, dict)
        or target.get("target_schema_count") != 31
        or target.get("target_policy_count") != 5
        or not isinstance(entries, list)
        or interface.get("promoted_schema_count") != 4
        or [entry.get("id") for entry in entries]
        != EXPECTED_PROMOTED_SCHEMA_IDS
    ):
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_INTERFACE_CONTRACT_MISMATCH"
        )
    for entry in entries:
        canonical = entry.get("canonical_relative_path")
        draft = entry.get("draft_relative_path")
        if (
            entry.get("exact_bytes_equal") is not True
            or not isinstance(canonical, str)
            or not canonical.startswith(
                "CodexSkills/registry/auto/schemas/public-v2/"
            )
            or "draft" in canonical.split("/")
            or not isinstance(draft, str)
            or "/transport-draft/" not in draft
        ):
            raise ValueError(
                "AUTO_SCHEMA_PROMOTION_INTERFACE_PATH_MISMATCH"
            )
        canonical_raw = (REPO_ROOT / canonical).read_bytes()
        draft_raw = (REPO_ROOT / draft).read_bytes()
        if (
            canonical_raw != draft_raw
            or hashlib.sha256(canonical_raw).hexdigest()
            != entry.get("raw_sha256")
        ):
            raise ValueError(
                "AUTO_SCHEMA_PROMOTION_INTERFACE_BYTES_MISMATCH"
            )
    historical_manifest_raw = _git_blob(
        current["git_object_id"],
        current["canonical_manifest_path"],
    )
    promotion_manifest_raw = _git_blob(
        SCHEMA_PROMOTION_EVIDENCE_GIT_OBJECT,
        current["canonical_manifest_path"],
    )
    if historical_manifest_raw != promotion_manifest_raw:
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_HISTORICAL_MANIFEST_BLOB_DRIFT"
        )
    if (
        hashlib.sha256(historical_manifest_raw).hexdigest()
        != HISTORICAL_CANDIDATE_MANIFEST_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_HISTORICAL_MANIFEST_DIGEST_MISMATCH"
        )
    try:
        historical_manifest = json.loads(
            historical_manifest_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_HISTORICAL_MANIFEST_INVALID"
        ) from exc
    if (
        historical_manifest.get("bundle_digest")
        != HISTORICAL_CANDIDATE_BUNDLE_DIGEST
        or historical_manifest.get("schema_count") != 29
        or historical_manifest.get("policy_count") != 5
        or any(
            not isinstance(entry, dict)
            or not isinstance(entry.get("relative_path"), str)
            or "/transport-draft/" in entry["relative_path"]
            or entry["relative_path"].startswith(
                "CodexSkills/registry/auto/schemas/public-v2/"
            )
            for entry in historical_manifest.get("schemas", [])
        )
    ):
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_HISTORICAL_MANIFEST_CONTRACT_MISMATCH"
        )
    if (
        _git_blob(
            SCHEMA_PROMOTION_EVIDENCE_GIT_OBJECT,
            SCHEMA_PROMOTION_INTERFACE_REPO_PATH,
        )
        != raw
    ):
        raise ValueError(
            "AUTO_SCHEMA_PROMOTION_HISTORICAL_INTERFACE_BLOB_DRIFT"
        )
    return {
        "acceptance_interface_path": (
            AU040_ACCEPTANCE_INTERFACE_REPO_PATH
        ),
        "acceptance_interface_raw_sha256": (
            EXPECTED_AU040_ACCEPTANCE_INTERFACE_RAW_SHA256
        ),
        "guard_codes": list(EXPECTED_AU040_GUARD_CODES),
        "historical_candidate_manifest_exact_blob_verified": True,
        "historical_candidate_manifest_raw_sha256": (
            HISTORICAL_CANDIDATE_MANIFEST_RAW_SHA256
        ),
        "next_phase": interface["next_phase"],
        "promoted_schema_count": 4,
        "promotion_interface_path": (
            SCHEMA_PROMOTION_INTERFACE_REPO_PATH
        ),
        "promotion_interface_raw_sha256": (
            EXPECTED_SCHEMA_PROMOTION_INTERFACE_RAW_SHA256
        ),
        "schema_promotion_evidence_git_object_id": (
            SCHEMA_PROMOTION_EVIDENCE_GIT_OBJECT
        ),
        "target_policy_count": 5,
        "target_schema_count": 31,
        "working_tree_manifest_assumed_historical_candidate": False,
    }


def _final_candidate_evidence():
    raw = _git_blob(
        FINAL_CANDIDATE_GIT_OBJECT,
        CANDIDATE_MANIFEST_PATH,
    )
    local = REPO_ROOT.joinpath(
        *CANDIDATE_MANIFEST_PATH.split("/")
    ).read_bytes()
    if raw != local:
        raise ValueError("AUTO_FINAL_CANDIDATE_MANIFEST_LOCAL_DRIFT")
    if (
        hashlib.sha256(raw).hexdigest()
        != EXPECTED_FINAL_CANDIDATE_MANIFEST_RAW_SHA256
    ):
        raise ValueError("AUTO_FINAL_CANDIDATE_MANIFEST_RAW_DIGEST_MISMATCH")
    try:
        manifest = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AUTO_FINAL_CANDIDATE_MANIFEST_INVALID") from exc
    schema_ids = {
        entry.get("id")
        for entry in manifest.get("schemas", [])
        if isinstance(entry, dict)
    }
    policy_ids = {
        entry.get("id")
        for entry in manifest.get("policies", [])
        if isinstance(entry, dict)
    }
    required_v2_schemas = {
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:daily-run-shard-manifest:v1",
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:publication-manifest:v2",
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:retention-receipt:v3",
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:run-event-index-entry:v1",
    }
    forbidden_legacy = {
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:publication-manifest:v1",
        "urn:linzecolin:agentdatabase:skillops:"
        "schema:retention-receipt:v2",
    }
    if (
        manifest.get("bundle_digest")
        != FINAL_CANDIDATE_BUNDLE_DIGEST
        or manifest.get("schema_count") != 31
        or manifest.get("policy_count") != 5
        or not required_v2_schemas.issubset(schema_ids)
        or forbidden_legacy.intersection(schema_ids)
        or "urn:linzecolin:agentdatabase:skillops:policy:public-value:v2"
        not in policy_ids
        or "urn:linzecolin:agentdatabase:skillops:policy:retention:v3"
        not in policy_ids
    ):
        raise ValueError("AUTO_FINAL_CANDIDATE_MANIFEST_CONTRACT_MISMATCH")
    return {
        "bundle_digest": FINAL_CANDIDATE_BUNDLE_DIGEST,
        "manifest_raw_sha256": (
            EXPECTED_FINAL_CANDIDATE_MANIFEST_RAW_SHA256
        ),
        "policy_count": 5,
        "schema_count": 31,
        "verified_git_object_id": FINAL_CANDIDATE_GIT_OBJECT,
    }


def _historical_control_observation():
    raw = _git_blob(
        CONTROL_EVIDENCE_GIT_OBJECT,
        CONTROL_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(raw).hexdigest()
        != EXPECTED_CONTROL_INTERFACE_RAW_SHA256
    ):
        raise ValueError("AUTO_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH")
    try:
        interface = json.loads(
            raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError("AUTO_CONTROL_INTERFACE_JSON_INVALID") from exc
    consumer = interface.get("consumer_contract")
    transition = interface.get("transition_contract")
    source = interface.get("transport_runtime_interface")
    promotion = (
        transition.get("promotion_evidence")
        if isinstance(transition, dict)
        else None
    )
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("base_auto_git_object_id")
        != CONTROL_BOUND_AUTO_GIT_OBJECT
        or interface.get("candidate_bundle_git_object_id")
        != FINAL_CANDIDATE_GIT_OBJECT
        or interface.get("bundle_digest")
        != FINAL_CANDIDATE_BUNDLE_DIGEST
        or interface.get("candidate_manifest_path")
        != CANDIDATE_MANIFEST_PATH
        or interface.get("candidate_trust_mode") != "CANDIDATE"
        or interface.get("candidate_schema_count") != 31
        or interface.get("candidate_policy_count") != 5
        or interface.get("next_phase")
        != "AUTO_AU040_REPOSITORY_BINDING"
        or not isinstance(consumer, dict)
        or consumer.get("verified_git_object_id")
        != CONSUMER_FIRST_EVIDENCE_GIT_OBJECT
        or consumer.get("artifact_digest")
        != EXPECTED_CONSUMER_INTERFACE_RAW_SHA256
        or consumer.get("contract_revision") != "V2"
        or consumer.get("canonical_publication_permitted") is not False
        or consumer.get("repository_shards_permitted") is not False
        or not isinstance(source, dict)
        or source.get("verified_git_object_id")
        != CONTROL_BOUND_AUTO_GIT_OBJECT
        or source.get("artifact_digest")
        != CONTROL_BOUND_AUTO_RUNTIME_INTERFACE_RAW_SHA256
        or source.get("integration_state")
        != "AU040_PUBLISHER_V2_SYNCED"
        or source.get("module_count") != CONTROL_BOUND_AUTO_MODULE_COUNT
        or not isinstance(transition, dict)
        or transition.get("auto_runtime_integration_complete") is not True
        or transition.get("au_040_complete") is not False
        or transition.get("au_040_daily_jsonl_shard_complete") is not False
        or transition.get("canonical_publication_permitted") is not False
        or transition.get("external_gmail_ready") is not False
        or transition.get("external_state_ready") is not False
        or transition.get("final_candidate_integration_required") is not False
        or transition.get("m0c_b_permitted") is not False
        or transition.get("publisher_v2_runtime_integration_complete")
        is not True
        or transition.get("repository_bound") is not False
        or transition.get("runtime_preflight_shadow_permitted") is not True
        or transition.get("runtime_shard_writer_integration_complete")
        is not True
        or transition.get("runtime_state_instance_created") is not False
        or transition.get("runtime_state_write_permitted") is not True
        or transition.get("schedule_authority_resolved") is not False
        or transition.get("schedule_complete") is not False
        or not isinstance(promotion, dict)
        or promotion.get("verified_git_object_id")
        != SCHEMA_PROMOTION_EVIDENCE_GIT_OBJECT
        or promotion.get("artifact_digest")
        != EXPECTED_SCHEMA_PROMOTION_INTERFACE_RAW_SHA256
    ):
        raise ValueError("AUTO_CONTROL_INTERFACE_CONTRACT_MISMATCH")
    historical_runtime_artifacts = []
    for relative_path in (
        "CodexSkills/governance/tools/build_activation_control.py",
        "CodexSkills/governance/tools/canonical_json.py",
        "CodexSkills/governance/tools/validate_activation.py",
        "CodexSkills/governance/tools/validate_mechanism.py",
    ):
        historical_raw = _git_blob(
            CONTROL_EVIDENCE_GIT_OBJECT,
            relative_path,
        )
        historical_runtime_artifacts.append(
            {
                "artifact_digest": hashlib.sha256(
                    historical_raw
                ).hexdigest(),
                "relative_path": relative_path,
            }
        )
    return {
        "auto_runtime_integration_complete": True,
        "bound_auto_git_object_id": CONTROL_BOUND_AUTO_GIT_OBJECT,
        "bound_auto_module_count": CONTROL_BOUND_AUTO_MODULE_COUNT,
        "bound_auto_runtime_interface_raw_sha256": (
            CONTROL_BOUND_AUTO_RUNTIME_INTERFACE_RAW_SHA256
        ),
        "interface_raw_sha256": (
            EXPECTED_CONTROL_INTERFACE_RAW_SHA256
        ),
        "mode": "DRAFT_NON_ACTIVE_CONTROL",
        "next_phase": interface["next_phase"],
        "publisher_v2_runtime_integration_complete": True,
        "repository_bound": False,
        "runtime_state_write_permitted": True,
        "status": interface["status"],
        "historical_runtime_artifacts": historical_runtime_artifacts,
        "verified_git_object_id": CONTROL_EVIDENCE_GIT_OBJECT,
    }


def _catalog_reservation_predecessor_observation():
    control_raw = _git_blob(
        CATALOG_RESERVATION_CONTROL_GIT_OBJECT,
        CONTROL_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(control_raw).hexdigest()
        != EXPECTED_CATALOG_RESERVATION_CONTROL_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_CATALOG_RESERVATION_CONTROL_RAW_DIGEST_MISMATCH"
        )
    resolver_raw = _git_blob(
        CATALOG_RESERVATION_CONTROL_GIT_OBJECT,
        RESOLVER_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(resolver_raw).hexdigest()
        != EXPECTED_RESOLVER_INTERFACE_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_CATALOG_RESERVATION_RESOLVER_RAW_DIGEST_MISMATCH"
        )
    try:
        control = json.loads(
            control_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
        resolver = json.loads(
            resolver_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "AUTO_CATALOG_RESERVATION_PREDECESSOR_JSON_INVALID"
        ) from exc
    transition = control.get("transition_contract")
    transport = control.get("transport_runtime_interface")
    bound_resolver = control.get("bound_reference_resolver_contract")
    sync_contract = resolver.get("current_sync_executor_contract")
    snapshot = resolver.get("registry_snapshot")
    resolver_contract = resolver.get("resolver_contract")
    expected_catalogs = [
        {
            "relative_path": (
                f"CodexSkills/registry/{namespace}/"
                "_catalog/catalog.v1.json"
            ),
            "source_class": {
                "agents": "AGENTS",
                "claude": "CLAUDE",
                "codex": "CODEX",
                "codex-system": "CODEX_SYSTEM",
            }[namespace],
        }
        for namespace in SOURCE_NAMESPACES
    ]
    if (
        control.get("status") != "DRAFT_NON_ACTIVE"
        or control.get("activation_forbidden") is not True
        or control.get("base_auto_git_object_id")
        != CATALOG_RESERVATION_BOUND_AUTO_GIT_OBJECT
        or control.get("next_phase")
        != "AUTO_REGISTRY_CATALOG_PATH_RESERVATION"
        or not isinstance(transport, dict)
        or transport.get("verified_git_object_id")
        != CATALOG_RESERVATION_BOUND_AUTO_GIT_OBJECT
        or transport.get("artifact_digest")
        != CATALOG_RESERVATION_BOUND_AUTO_INTERFACE_RAW_SHA256
        or transport.get("module_count")
        != CATALOG_RESERVATION_BOUND_AUTO_MODULE_COUNT
        or not isinstance(transition, dict)
        or transition.get("bound_reference_resolver_implementation_complete")
        is not True
        or transition.get("bound_reference_resolver_auto_integration_complete")
        is not False
        or transition.get("bound_reference_resolver_gate_satisfied")
        is not False
        or transition.get("canonical_publication_permitted") is not False
        or transition.get("effective_runtime_state_write_permitted")
        is not False
        or transition.get("external_gmail_ready") is not False
        or transition.get("external_state_ready") is not False
        or transition.get("m0c_b_permitted") is not False
        or transition.get("runtime_state_instance_created") is not False
        or transition.get("schedule_authority_resolved") is not False
        or transition.get("schedule_complete") is not False
        or not isinstance(bound_resolver, dict)
        or bound_resolver.get("artifact_digest")
        != EXPECTED_RESOLVER_INTERFACE_RAW_SHA256
        or bound_resolver.get("catalog_path_reservation_required")
        is not True
        or bound_resolver.get("current_snapshot_promotable") is not False
        or bound_resolver.get("gate_satisfied") is not False
        or bound_resolver.get("implementation_complete") is not True
        or bound_resolver.get("production_trust_permitted") is not False
        or resolver.get("status")
        != "DRAFT_NON_ACTIVE_RESOLVER_IMPLEMENTED"
        or resolver.get("activation_forbidden") is not True
        or resolver.get("auto_integration_complete") is not False
        or resolver.get("canonical_publication_permitted") is not False
        or resolver.get("catalog_path_reservation_required") is not True
        or resolver.get("current_materialization_promotable") is not False
        or resolver.get("production_trust_permitted") is not False
        or resolver.get("next_phase")
        != "AUTO_REGISTRY_CATALOG_PATH_RESERVATION"
        or resolver.get("final_catalog_entries") != expected_catalogs
        or resolver.get("final_snapshot_path")
        != "CodexSkills/registry/_global/registry-snapshot.v1.json"
        or not isinstance(sync_contract, dict)
        or sync_contract.get("verified_git_object_id")
        != HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT
        or sync_contract.get("deletes_unreserved_source_directories")
        is not True
        or sync_contract.get("enumerates_unreserved_source_directories_as_skills")
        is not True
        or not isinstance(snapshot, dict)
        or snapshot.get("source_material_git_object_id")
        != HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT
        or snapshot.get("registry_snapshot_digest")
        != INCOMPLETE_REGISTRY_SNAPSHOT_DIGEST
        or snapshot.get("source_mirror_parity_satisfied") is not False
        or not isinstance(resolver_contract, dict)
        or resolver_contract.get("current_snapshot_can_emit_bound")
        is not False
    ):
        raise ValueError(
            "AUTO_CATALOG_RESERVATION_PREDECESSOR_CONTRACT_MISMATCH"
        )
    for artifact in resolver.get("runtime_artifacts", []):
        if (
            not isinstance(artifact, dict)
            or hashlib.sha256(
                _git_blob(
                    CATALOG_RESERVATION_CONTROL_GIT_OBJECT,
                    artifact.get("relative_path", ""),
                )
            ).hexdigest()
            != artifact.get("artifact_digest")
        ):
            raise ValueError(
                "AUTO_CATALOG_RESERVATION_RESOLVER_RUNTIME_DRIFT"
            )
    return {
        "bound_auto_git_object_id": (
            CATALOG_RESERVATION_BOUND_AUTO_GIT_OBJECT
        ),
        "bound_auto_module_count": (
            CATALOG_RESERVATION_BOUND_AUTO_MODULE_COUNT
        ),
        "bound_auto_runtime_interface_raw_sha256": (
            CATALOG_RESERVATION_BOUND_AUTO_INTERFACE_RAW_SHA256
        ),
        "control_interface_raw_sha256": (
            EXPECTED_CATALOG_RESERVATION_CONTROL_RAW_SHA256
        ),
        "control_root_status": control["status"],
        "external_control_mode": "DRAFT_NON_ACTIVE_CONTROL",
        "next_phase_at_observation": control["next_phase"],
        "resolver_interface_raw_sha256": (
            EXPECTED_RESOLVER_INTERFACE_RAW_SHA256
        ),
        "resolver_status": resolver["status"],
        "verified_git_object_id": (
            CATALOG_RESERVATION_CONTROL_GIT_OBJECT
        ),
    }


def _source_content_sync_predecessor_observation():
    control_raw = _git_blob(
        SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT,
        CONTROL_INTERFACE_REPO_PATH,
    )
    resolver_raw = _git_blob(
        SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT,
        RESOLVER_INTERFACE_REPO_PATH,
    )
    reconciliation_raw = _git_blob(
        SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT,
        SOURCE_DRIFT_RECONCILIATION_REPO_PATH,
    )
    if (
        hashlib.sha256(control_raw).hexdigest()
        != EXPECTED_SOURCE_CONTENT_SYNC_CONTROL_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_SOURCE_CONTENT_SYNC_CONTROL_RAW_DIGEST_MISMATCH"
        )
    if (
        hashlib.sha256(resolver_raw).hexdigest()
        != EXPECTED_SOURCE_CONTENT_SYNC_RESOLVER_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_SOURCE_CONTENT_SYNC_RESOLVER_RAW_DIGEST_MISMATCH"
        )
    if (
        hashlib.sha256(reconciliation_raw).hexdigest()
        != EXPECTED_SOURCE_DRIFT_RECONCILIATION_RAW_SHA256
    ):
        raise ValueError(
            "AUTO_SOURCE_CONTENT_SYNC_RECONCILIATION_RAW_DIGEST_MISMATCH"
        )
    try:
        control = json.loads(
            control_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
        resolver = json.loads(
            resolver_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
        reconciliation = json.loads(
            reconciliation_raw.decode("utf-8"),
            object_pairs_hook=_strict_object,
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(
            "AUTO_SOURCE_CONTENT_SYNC_PREDECESSOR_JSON_INVALID"
        ) from exc

    pending_paths = [
        entry["source_relative_path"]
        for entry in SOURCE_CONTENT_SYNC_ENTRIES
    ]
    transport = control.get("transport_runtime_interface")
    transition = control.get("transition_contract")
    bound_resolver = control.get("bound_reference_resolver_contract")
    control_reconciliation = (
        bound_resolver.get("source_drift_reconciliation")
        if isinstance(bound_resolver, dict)
        else None
    )
    resolver_reconciliation = resolver.get("source_drift_reconciliation")
    resolver_snapshot = resolver.get("registry_snapshot")
    resolver_sync = resolver.get("current_sync_executor_contract")
    disposition = reconciliation.get("disposition")
    auto_evidence = reconciliation.get("auto_evidence")
    if (
        control.get("status") != "DRAFT_NON_ACTIVE"
        or control.get("activation_forbidden") is not True
        or control.get("base_auto_git_object_id")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT
        or control.get("next_phase") != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
        or not isinstance(transport, dict)
        or transport.get("verified_git_object_id")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT
        or transport.get("artifact_digest")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_INTERFACE_RAW_SHA256
        or transport.get("module_count")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_MODULE_COUNT
        or transport.get("integration_state")
        != "REGISTRY_CATALOG_RESERVED_SOURCE_CONTENT_SYNC_PENDING"
        or not isinstance(transition, dict)
        or transition.get("bound_reference_resolver_auto_integration_complete")
        is not False
        or transition.get("bound_reference_resolver_gate_satisfied")
        is not False
        or transition.get("bound_reference_resolver_implementation_complete")
        is not True
        or transition.get("canonical_publication_permitted") is not False
        or transition.get("catalog_path_reservation_complete") is not True
        or transition.get("effective_runtime_state_write_permitted")
        is not False
        or transition.get("external_gmail_ready") is not False
        or transition.get("external_state_ready") is not False
        or transition.get("m0c_b_permitted") is not False
        or transition.get("repository_bound") is not True
        or transition.get("runtime_state_instance_created") is not False
        or transition.get("runtime_state_write_gate_status")
        != "BOUND_REFERENCE_RESOLVER_SOURCE_CONTENT_SYNC_PENDING"
        or transition.get("runtime_state_write_permitted") is not True
        or transition.get("schedule_authority_resolved") is not False
        or transition.get("schedule_complete") is not False
        or transition.get("source_content_sync_required") is not True
        or transition.get("source_drift_reconciliation_complete") is not True
        or not isinstance(bound_resolver, dict)
        or bound_resolver.get("artifact_digest")
        != EXPECTED_SOURCE_CONTENT_SYNC_RESOLVER_RAW_SHA256
        or bound_resolver.get("auto_integration_complete") is not False
        or bound_resolver.get("gate_satisfied") is not False
        or bound_resolver.get("implementation_complete") is not True
        or bound_resolver.get("post_source_content_sync_rebuild_required")
        is not True
        or bound_resolver.get("production_trust_permitted") is not False
        or bound_resolver.get("source_content_sync_required") is not True
        or bound_resolver.get("source_mirror_parity_satisfied") is not False
        or not isinstance(control_reconciliation, dict)
        or control_reconciliation.get("artifact_digest")
        != EXPECTED_SOURCE_DRIFT_RECONCILIATION_SELF_DIGEST
        or control_reconciliation.get("missing_source_skill_roots")
        != MISSING_SOURCE_SKILL_ROOTS
        or control_reconciliation.get("pending_content_drift_paths")
        != pending_paths
        or control_reconciliation.get("source_drift_reconciliation_complete")
        is not True
        or resolver.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
        or resolver.get("activation_forbidden") is not True
        or resolver.get("auto_integration_complete") is not False
        or resolver.get("canonical_publication_permitted") is not False
        or resolver.get("current_materialization_promotable") is not False
        or resolver.get("next_phase") != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
        or resolver.get("post_source_content_sync_rebuild_required")
        is not True
        or resolver.get("production_trust_permitted") is not False
        or resolver.get("source_content_sync_required") is not True
        or resolver.get("source_drift_reconciliation_complete") is not True
        or not isinstance(resolver_reconciliation, dict)
        or resolver_reconciliation.get("artifact_digest")
        != EXPECTED_SOURCE_DRIFT_RECONCILIATION_SELF_DIGEST
        or resolver_reconciliation.get("missing_source_skill_roots")
        != MISSING_SOURCE_SKILL_ROOTS
        or resolver_reconciliation.get("pending_content_drift_paths")
        != pending_paths
        or not isinstance(resolver_snapshot, dict)
        or resolver_snapshot.get("source_mirror_parity_satisfied")
        is not False
        or not isinstance(resolver_sync, dict)
        or resolver_sync.get("verified_git_object_id")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT
        or resolver_sync.get("artifact_digest")
        != hashlib.sha256(
            _git_blob(
                SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT,
                "CodexSkills/sync_skills.py",
            )
        ).hexdigest()
        or resolver_sync.get("reserved_registry_paths_excluded_from_deletion")
        is not True
        or resolver_sync.get(
            "reserved_registry_paths_excluded_from_skill_enumeration"
        )
        is not True
        or reconciliation.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
        or reconciliation.get("artifact_digest")
        != EXPECTED_SOURCE_DRIFT_RECONCILIATION_SELF_DIGEST
        or reconciliation.get("next_phase")
        != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
        or not isinstance(auto_evidence, dict)
        or auto_evidence.get("verified_git_object_id")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT
        or auto_evidence.get("artifact_digest")
        != SOURCE_CONTENT_SYNC_BOUND_AUTO_INTERFACE_RAW_SHA256
        or reconciliation.get("pending_content_drift")
        != [
            {
                "action_owner": "AUTO",
                "required_action": "EXACT_CONTENT_SYNC",
                "source_relative_path": path,
            }
            for path in pending_paths
        ]
        or not isinstance(disposition, dict)
        or disposition.get("historical_registry_records_retained")
        is not True
        or disposition.get("lifecycle_transition_permitted") is not False
        or disposition.get("missing_root_observation_state") != "UNOBSERVED"
        or disposition.get("promotion_permitted") is not False
    ):
        raise ValueError(
            "AUTO_SOURCE_CONTENT_SYNC_PREDECESSOR_CONTRACT_MISMATCH"
        )
    for artifact in resolver.get("runtime_artifacts", []):
        if (
            not isinstance(artifact, dict)
            or hashlib.sha256(
                _git_blob(
                    SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT,
                    artifact.get("relative_path", ""),
                )
            ).hexdigest()
            != artifact.get("artifact_digest")
        ):
            raise ValueError(
                "AUTO_SOURCE_CONTENT_SYNC_RESOLVER_RUNTIME_DRIFT"
            )
    return {
        "bound_auto_git_object_id": (
            SOURCE_CONTENT_SYNC_BOUND_AUTO_GIT_OBJECT
        ),
        "bound_auto_module_count": SOURCE_CONTENT_SYNC_BOUND_AUTO_MODULE_COUNT,
        "bound_auto_runtime_interface_raw_sha256": (
            SOURCE_CONTENT_SYNC_BOUND_AUTO_INTERFACE_RAW_SHA256
        ),
        "canonical_control_path": CONTROL_INTERFACE_REPO_PATH,
        "control_interface_raw_sha256": (
            EXPECTED_SOURCE_CONTENT_SYNC_CONTROL_RAW_SHA256
        ),
        "control_root_status": control["status"],
        "external_control_mode": "DRAFT_NON_ACTIVE_CONTROL",
        "next_phase_at_observation": control["next_phase"],
        "pending_content_drift_paths": pending_paths,
        "reconciliation_artifact_digest": (
            EXPECTED_SOURCE_DRIFT_RECONCILIATION_SELF_DIGEST
        ),
        "reconciliation_interface_raw_sha256": (
            EXPECTED_SOURCE_DRIFT_RECONCILIATION_RAW_SHA256
        ),
        "reconciliation_status": reconciliation["status"],
        "resolver_interface_raw_sha256": (
            EXPECTED_SOURCE_CONTENT_SYNC_RESOLVER_RAW_SHA256
        ),
        "resolver_status": resolver["status"],
        "verified_git_object_id": SOURCE_CONTENT_SYNC_CONTROL_GIT_OBJECT,
    }


def _source_content_sync_materialization():
    from CodexSkills import sync_skills

    mirror_root = REPO_ROOT / "CodexSkills" / "registry"
    for relative_path in reserved_registry_paths():
        target = REPO_ROOT.joinpath(*relative_path.rstrip("/").split("/"))
        if os.path.lexists(target):
            raise ValueError(
                "AUTO_SOURCE_CONTENT_SYNC_RESERVED_PAYLOAD_PRESENT"
            )
    if os.path.lexists(mirror_root / "codex" / "context-kernel"):
        raise ValueError("AUTO_SOURCE_CONTENT_SYNC_ABSENT_ROOT_RESTORED")

    entries = []
    for expected in SOURCE_CONTENT_SYNC_ENTRIES:
        source_namespace, slug = expected[
            "source_relative_path"
        ].split("/", 1)
        root = mirror_root / source_namespace / slug
        rows = tuple(
            sync_skills.walk_entries(
                root,
                source_namespace=source_namespace,
                source_root=mirror_root / source_namespace,
            )
        )
        regular_rows = [row for row in rows if row[2] == "REGULAR_FILE"]
        alias_rows = [row for row in rows if row[2] != "REGULAR_FILE"]
        byte_count = sum(os.lstat(row[1]).st_size for row in regular_rows)
        content_digest = sync_skills.skill_digest(
            root,
            sync_skills.repo_owned_files(source_namespace, slug),
            source_namespace=source_namespace,
            source_root=mirror_root / source_namespace,
        )
        if (
            len(regular_rows) != expected["regular_file_count"]
            or len(alias_rows) != expected["alias_count"]
            or byte_count != expected["byte_count"]
            or content_digest != expected["content_digest"]
        ):
            raise ValueError(
                "AUTO_SOURCE_CONTENT_SYNC_MIRROR_CONTENT_DRIFT"
            )
        expected_paths = {
            (
                f"CodexSkills/registry/{source_namespace}/{slug}/"
                f"{row[0].replace(os.sep, '/')}"
            )
            for row in rows
        }
        tracked = subprocess.run(
            [
                "git",
                "ls-files",
                "-z",
                "--",
                f"CodexSkills/registry/{source_namespace}/{slug}",
            ],
            cwd=REPO_ROOT,
            check=True,
            stdout=subprocess.PIPE,
        ).stdout
        tracked_paths = {
            item.decode("utf-8")
            for item in tracked.split(b"\0")
            if item
        }
        if tracked_paths != expected_paths:
            raise ValueError(
                "AUTO_SOURCE_CONTENT_SYNC_GIT_TRACKED_CLOSURE_MISMATCH"
            )
        entries.append(
            {
                **expected,
                "exact_source_mirror_content_equal": True,
                "mirror_content_digest": content_digest,
                "source_content_digest": expected["content_digest"],
            }
        )
    return {
        "bound_reference_resolver_auto_integration_complete": False,
        "bound_reference_resolver_gate_satisfied": False,
        "canonical_publication_permitted": False,
        "catalog_or_snapshot_artifacts_generated": False,
        "current_auto_runtime_control_bound": False,
        "exact_synchronized_paths": [
            entry["source_relative_path"] for entry in entries
        ],
        "external_source_dry_run_required": True,
        "git_tracked_exact_closure_verified": True,
        "missing_source_skill_roots": list(MISSING_SOURCE_SKILL_ROOTS),
        "next_phase": SOURCE_CONTENT_SYNC_NEXT_PHASE,
        "remaining_content_drift_paths": [],
        "repository_bound": False,
        "reserved_registry_namespaces_preserved": True,
        "runtime_state_write_permitted": False,
        "source_content_sync_complete": True,
        "source_mirror_parity_satisfied": True,
        "source_root_parity_satisfied": False,
        "synchronized_entries": entries,
        "whole_source_parity_satisfied": False,
    }


def _catalog_reservation_materialization():
    mirror_roots = {
        namespace: REPO_ROOT / "CodexSkills" / "registry" / namespace
        for namespace in SOURCE_NAMESPACES
    }
    observed_aliases = assert_exact_alias_set(mirror_roots)
    if (
        len(observed_aliases) != EXPECTED_SOURCE_ALIAS_COUNT
        or alias_set_digest(observed_aliases)
        != EXPECTED_SOURCE_ALIAS_SET_DIGEST
    ):
        raise ValueError("AUTO_REGISTRY_MIRROR_ALIAS_SET_DRIFT")
    mirror_counts = {}
    for namespace, root in mirror_roots.items():
        try:
            root_info = os.lstat(root)
        except OSError as exc:
            raise ValueError(
                "AUTO_REGISTRY_SOURCE_NAMESPACE_MISSING"
            ) from exc
        if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(
            root_info.st_mode
        ):
            raise ValueError(
                "AUTO_REGISTRY_SOURCE_NAMESPACE_NOT_REAL_DIRECTORY"
            )
        count = 0
        try:
            with os.scandir(root) as iterator:
                entries = sorted(
                    iterator,
                    key=lambda item: item.name.encode("utf-8"),
                )
        except (OSError, UnicodeError) as exc:
            raise ValueError(
                "AUTO_REGISTRY_SOURCE_NAMESPACE_ENUMERATION_FAILED"
            ) from exc
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ValueError(
                    "AUTO_REGISTRY_SOURCE_ROOT_LSTAT_FAILED"
                ) from exc
            if entry.name == "_catalog":
                if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(
                    info.st_mode
                ):
                    raise ValueError(
                        "AUTO_REGISTRY_RESERVED_CATALOG_NOT_REAL_DIRECTORY"
                    )
                continue
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                raise ValueError(
                    "AUTO_REGISTRY_SOURCE_ROOT_TYPE_INVALID"
                )
            count += 1
        mirror_counts[namespace] = count
    if mirror_counts != CURRENT_SOURCE_SKILL_COUNTS:
        raise ValueError("AUTO_REGISTRY_MIRROR_SKILL_COUNT_DRIFT")

    removed_artifacts = []
    for relative_path in REMOVED_SOURCE_SKILL_PATHS:
        local = REPO_ROOT.joinpath(*relative_path.split("/"))
        if os.path.lexists(local):
            raise ValueError("AUTO_REGISTRY_REMOVED_SKILL_PATH_PRESENT")
        historical_raw = _git_blob(
            CATALOG_RESERVATION_CONTROL_GIT_OBJECT,
            relative_path,
        )
        removed_artifacts.append(
            {
                "historical_byte_count": len(historical_raw),
                "historical_raw_sha256": hashlib.sha256(
                    historical_raw
                ).hexdigest(),
                "relative_path": relative_path,
            }
        )
    root_index = json.loads(
        (REPO_ROOT / "CodexSkills" / "index.json").read_text(
            encoding="utf-8"
        ),
        object_pairs_hook=_strict_object,
    )
    if (
        root_index.get("skill_instance_count") != CURRENT_SOURCE_SKILL_COUNT
        or any(
            item.get("source") == "codex"
            and item.get("slug") == "context-kernel"
            for item in root_index.get("skills", [])
            if isinstance(item, dict)
        )
    ):
        raise ValueError("AUTO_REGISTRY_COMPATIBILITY_INDEX_DRIFT")
    sync_path = REPO_ROOT / "CodexSkills" / "sync_skills.py"
    return {
        "alias_contract_entries": [
            {
                **item.as_dict(),
                "content_digest": ALIAS_CONTENT_DIGESTS[
                    item.target_type
                ],
                "metadata_digest": item.metadata_digest(),
            }
            for item in EXPECTED_SOURCE_ALIASES
        ],
        "alias_set_digest": EXPECTED_SOURCE_ALIAS_SET_DIGEST,
        "catalog_or_snapshot_artifacts_generated": False,
        "catalog_path_reservation_complete": True,
        "current_source_skill_count": CURRENT_SOURCE_SKILL_COUNT,
        "current_source_skill_counts": dict(CURRENT_SOURCE_SKILL_COUNTS),
        "existing_incomplete_materialization_promotable": False,
        "global_snapshot_namespace_reserved": True,
        "historical_source_material_git_object_id": (
            HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT
        ),
        "historical_source_skill_count": HISTORICAL_SOURCE_SKILL_COUNT,
        "historical_source_skill_counts": dict(
            HISTORICAL_SOURCE_SKILL_COUNTS
        ),
        "mirror_alias_count": len(observed_aliases),
        "mirror_alias_parity_satisfied": True,
        "mirror_removal_artifacts": removed_artifacts,
        "mirror_removal_performed": True,
        "mirror_removed_skill_roots": list(MISSING_SOURCE_SKILL_ROOTS),
        "mirror_skill_count": sum(mirror_counts.values()),
        "mirror_skill_counts": mirror_counts,
        "missing_source_skill_roots": list(MISSING_SOURCE_SKILL_ROOTS),
        "non_alias_content_drift_observed_paths": list(
            NON_ALIAS_CONTENT_DRIFT_OBSERVED_PATHS
        ),
        "reserved_registry_paths": list(reserved_registry_paths()),
        "source_alias_count": EXPECTED_SOURCE_ALIAS_COUNT,
        "source_alias_parity_satisfied": True,
        "source_root_parity_satisfied": False,
        "source_scan_observations": list(SOURCE_SCAN_OBSERVATIONS),
        "source_skill_count_delta": (
            CURRENT_SOURCE_SKILL_COUNT - HISTORICAL_SOURCE_SKILL_COUNT
        ),
        "sync_executor_artifact": {
            "artifact_digest": hashlib.sha256(
                sync_path.read_bytes()
            ).hexdigest(),
            "relative_path": "CodexSkills/sync_skills.py",
        },
        "whole_source_parity_satisfied": False,
    }


def _files():
    paths = sorted((AUTO_DIR / "runtime").glob("*.py"))
    paths.extend(
        [
            AUTO_DIR / "tools" / "activation_handshake_cli.py",
            AUTO_DIR / "tools" / "build_runtime_interface.py",
            AUTO_DIR / "tools" / "notification_transport_cli.py",
            AUTO_DIR / "tools" / "run_fault_suite.py",
            AUTO_DIR / "tools" / "runtime_preflight.py",
            AUTO_DIR / "tools" / "validate_au040_publisher.py",
            AUTO_DIR / "tools" / "validate_au040_writer.py",
            AUTO_DIR / "tools" / "validate_auto.py",
        ]
    )
    return sorted(paths, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def build():
    consumer = _consumer_first_evidence()
    transport = _transport_draft_evidence()
    promotion = _schema_promotion_evidence()
    final_candidate = _final_candidate_evidence()
    control = _historical_control_observation()
    reservation_control = _catalog_reservation_predecessor_observation()
    source_sync_control = _source_content_sync_predecessor_observation()
    catalog_reservation = _catalog_reservation_materialization()
    source_content_sync = _source_content_sync_materialization()
    artifacts = []
    for path in _files():
        relative = path.relative_to(REPO_ROOT).as_posix()
        artifacts.append(
            {
                "artifact_digest": hashlib.sha256(path.read_bytes()).hexdigest(),
                "relative_path": relative,
            }
        )
    return {
        "activation_caller_assertions_forbidden": [
            "activation_artifact_digests",
            "activation_envelope_verified",
            "notification_provider_status",
            "shared_gate_status_map",
        ],
        "activation_control_interface_path": (
            "CodexSkills/governance/activation/control-interface.json"
        ),
        "activation_control_mode": "DRAFT_NON_ACTIVE_CONTROL",
        "activation_control_trust_tuple_repo_external_only": True,
        "auto_exact_bundle_integration_complete": True,
        "control_sync_required_before_state_write": True,
        "dual_external_trust_tuples_required": True,
        "activation_forbidden_without_coordinated_m0c": True,
        "activation_handshake_entrypoint": (
            "CodexSkills/registry/auto/tools/activation_handshake_cli.py"
        ),
        "activation_instance_created": False,
        "activation_settlement_recomputed_before_publish": True,
        "au_040_authority_ruling_status": (
            "REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING"
        ),
        "au_040_complete": False,
        "au_040_consumer_manifest_path_contract_present": True,
        "au_040_daily_jsonl_shard_complete": False,
        "au_040_manifest_contract_resolved": True,
        "au_040_retention_policy_v3_present": True,
        "au_040_retention_policy_v3_repository_accepted": True,
        "au_040_schema_promotion_complete": True,
        "au_040_semantic_policy_acceptance_complete": True,
        "au_040_transport_schema_draft_complete": True,
        "au_040_transport_contract": {
            "acceptance_interface_path": promotion[
                "acceptance_interface_path"
            ],
            "acceptance_interface_raw_sha256": promotion[
                "acceptance_interface_raw_sha256"
            ],
            "daily_manifest_path_pattern": (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "YYYY/MM/DD/manifest-NNNN.json"
            ),
            "daily_manifest_schema_id": (
                "urn:linzecolin:agentdatabase:skillops:"
                "schema:daily-run-shard-manifest:v1"
            ),
            "manifest_entry_numbers_contiguous": True,
            "historical_candidate_manifest_exact_blob_verified": promotion[
                "historical_candidate_manifest_exact_blob_verified"
            ],
            "historical_candidate_manifest_raw_sha256": promotion[
                "historical_candidate_manifest_raw_sha256"
            ],
            "current_candidate_schema_count": final_candidate[
                "schema_count"
            ],
            "historical_candidate_schema_count": transport[
                "current_schema_count"
            ],
            "draft_interface_path": TRANSPORT_DRAFT_INTERFACE_REPO_PATH,
            "draft_interface_raw_sha256": (
                EXPECTED_TRANSPORT_DRAFT_INTERFACE_RAW_SHA256
            ),
            "draft_paths_forbidden_in_candidate_manifest": True,
            "draft_schema_count": transport["draft_schema_count"],
            "loader_isolation_root": (
                "CodexSkills/registry/auto/schemas/public-v2/"
            ),
            "part_numbers_reused": False,
            "physical_part_gaps_after_prune_permitted": True,
            "publisher_serialization_discriminator_required": True,
            "publisher_v2_control_sync_required_before_canonical_write": (
                True
            ),
            "publisher_v2_delete_prior_bytes_revalidated": True,
            "publisher_v2_jsonl_per_line_validation": True,
            "publisher_v2_manifest_recomputed_from_physical_descriptors": (
                True
            ),
            "publisher_v2_runtime_integration_complete": True,
            "repository_binding_integration_complete": True,
            "repository_bound": False,
            "promotion_required_before_candidate_materialization": True,
            "promotion_requirement_satisfied": True,
            "proposed_active_policy_count": transport["policy_count"],
            "proposed_active_policy_contract_complete": True,
            "proposed_active_schema_count": promotion[
                "target_schema_count"
            ],
            "promoted_schema_count": promotion[
                "promoted_schema_count"
            ],
            "final_candidate_materialization_complete": True,
            "runtime_shard_writer_integration_complete": True,
            "production_semantic_guard_codes_acknowledged": promotion[
                "guard_codes"
            ],
            "required_mechanism_public_value_allowlist_additions": (
                transport["allowlist_delta"]
            ),
            "retention_exact_affected_records_required": True,
            "retention_index_readiness_required": True,
            "schema_promotion_interface_path": promotion[
                "promotion_interface_path"
            ],
            "schema_promotion_interface_raw_sha256": promotion[
                "promotion_interface_raw_sha256"
            ],
            "schema_promotion_evidence_git_object_id": promotion[
                "schema_promotion_evidence_git_object_id"
            ],
            "transaction_manifest_v1_role": "TRANSACTION_SETTLEMENT_ONLY",
            "working_tree_manifest_assumed_historical_candidate": promotion[
                "working_tree_manifest_assumed_historical_candidate"
            ],
        },
        "candidate_bundle_digest": final_candidate["bundle_digest"],
        "candidate_git_object_id": final_candidate[
            "verified_git_object_id"
        ],
        "candidate_manifest_raw_sha256": final_candidate[
            "manifest_raw_sha256"
        ],
        "candidate_manifest_path": CANDIDATE_MANIFEST_PATH,
        "canonical_publication_permitted": False,
        "catalog_path_reservation_complete": True,
        "registry_alias_set_digest": (
            catalog_reservation["alias_set_digest"]
        ),
        "registry_mirror_alias_parity_satisfied": True,
        "registry_source_alias_parity_satisfied": True,
        "registry_source_content_sync_complete": True,
        "registry_source_mirror_parity_satisfied": True,
        "registry_source_root_parity_satisfied": False,
        "registry_whole_source_parity_satisfied": False,
        "catalog_reservation_materialization_snapshot": {
            "as_of_phase": "AUTO_REGISTRY_CATALOG_PATH_RESERVATION",
            "bound_reference_resolver_auto_integration_complete": False,
            "bound_reference_resolver_gate_satisfied": False,
            "canonical_publication_permitted": False,
            "current_auto_runtime_control_bound": False,
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
            **catalog_reservation,
        },
        "catalog_reservation_predecessor_observation": {
            "bound_auto_git_object_id": reservation_control[
                "bound_auto_git_object_id"
            ],
            "bound_auto_module_count": reservation_control[
                "bound_auto_module_count"
            ],
            "bound_auto_runtime_interface_raw_sha256": reservation_control[
                "bound_auto_runtime_interface_raw_sha256"
            ],
            "canonical_control_path": CONTROL_INTERFACE_REPO_PATH,
            "control_interface_raw_sha256": reservation_control[
                "control_interface_raw_sha256"
            ],
            "control_root_status": reservation_control[
                "control_root_status"
            ],
            "external_control_mode": reservation_control[
                "external_control_mode"
            ],
            "next_phase_at_observation": reservation_control[
                "next_phase_at_observation"
            ],
            "resolver_interface_path": RESOLVER_INTERFACE_REPO_PATH,
            "resolver_interface_raw_sha256": reservation_control[
                "resolver_interface_raw_sha256"
            ],
            "resolver_status": reservation_control["resolver_status"],
            "verified_git_object_id": reservation_control[
                "verified_git_object_id"
            ],
            "working_tree_control_is_not_historical_trust_evidence": True,
            "working_tree_resolver_is_not_historical_trust_evidence": True,
        },
        "source_content_sync_materialization_snapshot": {
            "as_of_phase": "AUTO_REGISTRY_SOURCE_CONTENT_SYNC",
            "predecessor_control_git_object_id": source_sync_control[
                "verified_git_object_id"
            ],
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
            **source_content_sync,
        },
        "source_content_sync_predecessor_observation": {
            **source_sync_control,
            "reconciliation_interface_path": (
                SOURCE_DRIFT_RECONCILIATION_REPO_PATH
            ),
            "resolver_interface_path": RESOLVER_INTERFACE_REPO_PATH,
            "working_tree_control_is_not_historical_trust_evidence": True,
            "working_tree_reconciliation_is_not_historical_trust_evidence": (
                True
            ),
            "working_tree_resolver_is_not_historical_trust_evidence": True,
        },
        "capability_gate_precedes_state_write": True,
        "current_auto_runtime_control_bound": False,
        "consumer_first_canonical_publication_permitted": consumer[
            "canonical_publication_permitted"
        ],
        "consumer_first_gate_satisfied": True,
        "consumer_first_interface_path": CONSUMER_INTERFACE_REPO_PATH,
        "consumer_first_interface_raw_sha256": (
            EXPECTED_CONSUMER_INTERFACE_RAW_SHA256
        ),
        "consumer_first_observed_bundle_digest": consumer[
            "expected_bundle_digest"
        ],
        "consumer_first_observed_candidate_git_object_id": consumer[
            "verified_git_object_id"
        ],
        "consumer_first_observed_status": consumer["status"],
        "consumer_first_owner_plane": "MECHANISM",
        "consumer_first_repository_shards_permitted": consumer[
            "repository_shards_permitted"
        ],
        "consumer_first_required_before_enable": consumer[
            "required_before_enable"
        ],
        "consumer_first_required_bundle_digest": (
            FINAL_CANDIDATE_BUNDLE_DIGEST
        ),
        "consumer_first_required_candidate_git_object_id": (
            FINAL_CANDIDATE_GIT_OBJECT
        ),
        "consumer_first_trust_tuple_drift_detected": False,
        "consumer_first_verified_git_object_id": (
            CONSUMER_FIRST_EVIDENCE_GIT_OBJECT
        ),
        "external_gmail_ready_gate_satisfied": False,
        "fault_test_rounds_required": 2,
        "historical_control_observation": {
            "bound_auto_git_object_id": control[
                "bound_auto_git_object_id"
            ],
            "bound_auto_module_count": control[
                "bound_auto_module_count"
            ],
            "bound_auto_runtime_interface_raw_sha256": control[
                "bound_auto_runtime_interface_raw_sha256"
            ],
            "canonical_path": CONTROL_INTERFACE_REPO_PATH,
            "external_mode": control["mode"],
            "historical_mechanism_runtime_artifacts": control[
                "historical_runtime_artifacts"
            ],
            "interface_raw_sha256": control["interface_raw_sha256"],
            "next_phase_at_observation": control["next_phase"],
            "observed_auto_runtime_integration_complete": control[
                "auto_runtime_integration_complete"
            ],
            "observed_runtime_state_write_permitted": control[
                "runtime_state_write_permitted"
            ],
            "observed_publisher_v2_runtime_integration_complete": control[
                "publisher_v2_runtime_integration_complete"
            ],
            "observed_repository_bound": control[
                "repository_bound"
            ],
            "root_status": control["status"],
            "verified_git_object_id": control["verified_git_object_id"],
            "working_tree_control_is_not_historical_trust_evidence": True,
            "working_tree_mechanism_runtime_is_not_historical_trust_evidence": (
                True
            ),
        },
        "manual_and_scheduled_same_orchestrator": True,
        "module_artifacts": artifacts,
        "module_count": len(artifacts),
        "m0c_b_permitted": False,
        "next_phase": SOURCE_CONTENT_SYNC_NEXT_PHASE,
        "notification_actual_recipient_repo_external": True,
        "notification_credentials_repo_external": True,
        "notification_external_path_contract": {
            "gmail_config_ref": (
                "state-root/private/notification/gmail-api.v1.json"
            ),
            "recipient_mapping_ref": (
                "state-root/private/notification/recipient-mapping.v1.json"
            ),
        },
        "notification_production_transport": "GMAIL_API_V1",
        "notification_preflight_cannot_claim_metadata_readback": True,
        "notification_preflight_query": {
            "endpoint": "users.messages.list",
            "max_results": 1,
            "query": (
                "in:sent rfc822msgid:"
                "<skillops-query-capability-v1@"
                "notification.skillops.invalid>"
            ),
            "send_performed": False,
        },
        "notification_preflight_query_endpoint_implemented": True,
        "notification_preflight_query_endpoint_runtime_verified": False,
        "notification_provider_lookup": (
            "RFC822_MESSAGE_ID_AND_PRIVATE_PAYLOAD_DIGEST"
        ),
        "notification_provider_readback_required": True,
        "notification_public_recipient_ref_only": True,
        "notification_real_message_metadata_readback_verified": False,
        "notification_real_message_metadata_readback_with_send_only": True,
        "notification_send_entrypoint": (
            "CodexSkills/registry/auto/tools/activation_handshake_cli.py"
        ),
        "notification_test_transport_production_forbidden": True,
        "os_local_scheduler_or_daemon_used": False,
        "persistent_managed_raw_default_enabled": False,
        "protocol_revision": "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1",
        "remote_readback_precedes_watermark": True,
        "runtime_preflight_shadow_permitted": True,
        "runtime_interface_materialization_snapshot": {
            "as_of_phase": "AUTO_AU040_RUNTIME_WRITER_INTEGRATION",
            "control_sync_required_before_state_write": True,
            "current_auto_runtime_control_bound": False,
            "historical_control_git_object_id": (
                "sha1:00c4a52d177898b1999b87b29ddb480e89908729"
            ),
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        },
        "publisher_v2_runtime_materialization_snapshot": {
            "as_of_phase": (
                "AUTO_AU040_PUBLISHER_V2_RUNTIME_INTEGRATION"
            ),
            "canonical_publication_permitted": False,
            "control_sync_required_before_state_write": True,
            "current_auto_runtime_control_bound": False,
            "predecessor_control_git_object_id": (
                PUBLISHER_MATERIALIZATION_CONTROL_GIT_OBJECT
            ),
            "repository_bound": False,
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        },
        "repository_binding_contract": {
            "artifact_closure": [
                {
                    "artifact_kind": "INDEX",
                    "artifact_operation": "PUT",
                    "max_bytes": 20971520,
                    "path_pattern": (
                        "OpenAIDatabase/data/run_logs/skills_runs/"
                        "YYYY/MM/DD/index-NNNN.jsonl"
                    ),
                    "schema_id": (
                        "urn:linzecolin:agentdatabase:skillops:"
                        "schema:run-event-index-entry:v1"
                    ),
                    "serialization": "RFC8785_JCS_PER_LINE_LF",
                },
                {
                    "artifact_kind": "PART",
                    "artifact_operation": "PUT|DELETE",
                    "max_bytes": 20971520,
                    "path_pattern": (
                        "OpenAIDatabase/data/run_logs/skills_runs/"
                        "YYYY/MM/DD/part-NNNN.jsonl"
                    ),
                    "schema_id": (
                        "urn:linzecolin:agentdatabase:skillops:"
                        "schema:public-run-event:v2"
                    ),
                    "serialization": "RFC8785_JCS_PER_LINE_LF",
                },
                {
                    "artifact_kind": "DAILY_MANIFEST",
                    "artifact_operation": "PUT",
                    "max_bytes": 1048576,
                    "path_pattern": (
                        "OpenAIDatabase/data/run_logs/skills_runs/"
                        "YYYY/MM/DD/manifest-NNNN.json"
                    ),
                    "schema_id": (
                        "urn:linzecolin:agentdatabase:skillops:"
                        "schema:daily-run-shard-manifest:v1"
                    ),
                    "serialization": "RFC8785_JCS_OBJECT",
                },
                {
                    "artifact_kind": "RETENTION_RECEIPT",
                    "artifact_operation": "PUT",
                    "max_bytes": 1048576,
                    "path_pattern": (
                        "OpenAIDatabase/data/run_logs/skills_runs/"
                        "YYYY/MM/DD/retention-receipt-NNNN.json"
                    ),
                    "schema_id": (
                        "urn:linzecolin:agentdatabase:skillops:"
                        "schema:retention-receipt:v3"
                    ),
                    "serialization": "RFC8785_JCS_OBJECT",
                },
            ],
            "bound_reference_resolver_owner_plane": "MECHANISM",
            "bound_reference_resolver_required_before_mutable_git": True,
            "branch": "main",
            "canonical_run_log_root": (
                "OpenAIDatabase/data/run_logs/skills_runs/"
            ),
            "changed_path_exact_closure_required": True,
            "expected_fetch_url": (
                "git@github.com:LinzeColin/AgentDatabase.git"
            ),
            "expected_push_url": (
                "git@github.com:LinzeColin/AgentDatabase.git"
            ),
            "expected_remote_head_repo_external_per_transaction": True,
            "ff_only": True,
            "logical_numbering": (
                "0001_TO_9999_GAPLESS_MANIFEST_ENTRIES"
            ),
            "object_format": "sha1",
            "push_refspec": "HEAD:main",
            "reference_main_clean_required": True,
            "remote_name": "origin",
            "remote_readback_precedes_watermark": True,
            "remote_ref": "refs/heads/main",
            "repository_id": "github.com/LinzeColin/AgentDatabase",
            "repository_self_report_is_not_trust_root": True,
            "scratch_and_state_repo_external_nonoverlapping": True,
            "sydney_calendar_date_required": True,
        },
        "repository_binding_integration_complete": True,
        "repository_binding_materialization_snapshot": {
            "as_of_phase": "AUTO_AU040_REPOSITORY_BINDING",
            "bound_reference_resolver_gate_satisfied": False,
            "canonical_publication_permitted": False,
            "current_auto_runtime_control_bound": False,
            "predecessor_control_git_object_id": control[
                "verified_git_object_id"
            ],
            "repository_binding_integration_complete": True,
            "repository_bound": False,
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        },
        "repository_binding_readonly_preflight_verified": False,
        "bound_reference_resolver_auto_integration_complete": False,
        "bound_reference_resolver_implementation_complete": True,
        "bound_reference_resolver_dependency_contract": {
            "adapter_may_generate_or_authenticate_resolver": False,
            "approved_surfaces": [
                "CODEX_AUTOMATION",
                "CODEX_CLI",
            ],
            "current_registry_compatibility_index_is_not_snapshot_truth": (
                True
            ),
            "gate_owner_plane": "MECHANISM",
            "controlled_invocation_required_fields": [
                "evidence_type",
                "invocation_envelope_digest",
                "invocation_uid",
                "observed_at",
                "surface_class",
            ],
            "event_inputs_required": [
                "CANONICAL_PUBLIC_RUN_EVENT_V2_BYTES_AND_SELF_DIGEST",
                "CONTROLLED_INVOCATION_AND_RAW_ENVELOPE",
                "EXTERNAL_CANDIDATE_PROTOCOL_AND_BUNDLE",
                "FULL_SEVEN_FIELD_SKILL_REF",
                "MECHANISM_IMMUTABLE_REGISTRY_SNAPSHOT_TUPLE",
            ],
            "missing_current_artifacts": [
                "FOUR_SOURCE_IDENTITY_INSTANCE_VERSION_CATALOGS",
                "GLOBAL_SKILL_IDENTITY_RECORDS",
                "PROMOTABLE_VERSIONED_REGISTRY_SNAPSHOT",
            ],
            "must_precede": [
                "GMAIL_CLIENT",
                "GIT_LS_REMOTE",
                "GIT_MUTABLE_BACKEND",
                "LOCK",
                "NOTIFICATION_OUTBOX",
                "PUBLISHER",
                "STATE_ROOT",
                "WATERMARK",
                "WORKTREE",
            ],
            "nonpublishable_states": [
                "QUARANTINED",
                "REVOKED",
                "UNKNOWN_WITHOUT_EXPLICIT_PUBLISHABLE_STATUS",
            ],
            "pinned_git_object_reads_before_gate_permitted": True,
            "registry_snapshot_tuple_required_fields": [
                "canonical_snapshot_digest",
                "canonical_snapshot_path",
                "canonical_snapshot_schema_id",
                "verified_git_object_id",
            ],
            "skill_ref_required_fields": [
                "content_digest",
                "registry_snapshot_digest",
                "skill_identity_uid",
                "skill_instance_uid",
                "skill_version_uid",
                "tree_digest",
                "version_record_digest",
            ],
            "version_closure_required": (
                "IDENTITY_TO_INSTANCE_TO_VERSION_UNIQUE_AND_DIGEST_EXACT"
            ),
            "unprovable_binding_action": (
                "PROJECT_UNKNOWN_AND_BLOCK_CANONICAL_PUBLICATION"
            ),
            "unknown_reason_codes": [
                "ADAPTER_NOT_APPROVED",
                "BUNDLE_DIGEST_MISMATCH",
                "CONTROLLED_INVOCATION_INVALID",
                "IDENTITY_REFERENCE_INCOMPLETE",
                "MAPPING_NOT_PROVABLE",
                "REGISTRY_SNAPSHOT_MISMATCH",
                "SURFACE_NOT_BINDING_ELIGIBLE",
                "VERSION_DIGEST_MISMATCH",
            ],
        },
        "runtime_shard_writer_integration_complete": True,
        "runtime_state_write_permitted": False,
        "runtime_writer_shadow_returns_bootstrap_context": False,
        "runtime_writer_shadow_state_access_permitted": False,
        "runtime_writer_shadow_status": (
            "UNBOUND_REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING"
        ),
        "runtime_writer_shadow_validator_kind": (
            "DEVELOPMENT_ONLY_UNBOUND"
        ),
        "runtime_writer_shadow_validator_path": (
            "CodexSkills/registry/auto/tools/validate_au040_writer.py"
        ),
        "runtime_publisher_shadow_returns_bootstrap_context": False,
        "runtime_publisher_shadow_state_access_permitted": False,
        "runtime_publisher_shadow_status": (
            "UNBOUND_REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING"
        ),
        "runtime_publisher_shadow_validator_kind": (
            "DEVELOPMENT_ONLY_UNBOUND"
        ),
        "runtime_publisher_shadow_validator_path": (
            "CodexSkills/registry/auto/tools/"
            "validate_au040_publisher.py"
        ),
        "runtime_repository_binding_shadow_returns_bootstrap_context": (
            False
        ),
        "runtime_repository_binding_shadow_state_access_permitted": (
            False
        ),
        "runtime_repository_binding_shadow_status": (
            "UNBOUND_REGISTRY_SOURCE_CONTENT_SYNCED_CONTROL_PENDING"
        ),
        "runtime_repository_binding_shadow_validator_kind": (
            "DEVELOPMENT_ONLY_UNBOUND"
        ),
        "runtime_repository_binding_shadow_validator_path": (
            "CodexSkills/registry/auto/tools/"
            "validate_au040_publisher.py"
        ),
        "publisher_v2_runtime_integration_complete": True,
        "bound_reference_resolver_gate_satisfied": False,
        "repository_bound": False,
        "schedule": {
            "daily_local_time": "04:15",
            "late_start_rejected": False,
            "sunday_forced_full": True,
            "timezone": "Australia/Sydney",
        },
        "schedule_authority_conflict_detected": True,
        "schedule_authority_resolved": False,
        "schedule_complete": False,
        "shared_bundle_schema_count": 31,
        "shared_policy_count": 5,
        "state_root_repo_external": True,
        "status": "DRAFT_NON_ACTIVE",
        "trust_tuple_repo_external_only": True,
    }


def render(value) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--write", action="store_true")
    modes.add_argument("--check", action="store_true")
    args = parser.parse_args()
    expected = render(build())
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print("AUTO_RUNTIME_INTERFACE_MISMATCH")
            return 2
        print(
            "AUTO_RUNTIME_INTERFACE_BYTE_EQUIVALENT "
            f"raw_sha256={hashlib.sha256(expected).hexdigest()}"
        )
        return 0
    OUTPUT.write_bytes(expected)
    print(
        "AUTO_RUNTIME_INTERFACE_GENERATED_OK "
        f"raw_sha256={hashlib.sha256(expected).hexdigest()}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
