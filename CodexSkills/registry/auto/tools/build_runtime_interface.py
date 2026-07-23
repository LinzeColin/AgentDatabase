#!/usr/bin/env python3
"""Build/check deterministic Auto activation-handshake interface evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path


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
    "sha1:66d5bafadca508cad825b4ce49a42e81e8b66ef7"
)
EXPECTED_CONTROL_INTERFACE_RAW_SHA256 = (
    "86e4d625bdab87261a39c949883d4108"
    "22e25e0222dbab6a333d171ce420c614"
)
SOURCE_AUTO_GIT_OBJECT = (
    "sha1:d16273c26b859379578ea9ec04e1473f175d14f6"
)
SOURCE_AUTO_RUNTIME_INTERFACE_RAW_SHA256 = (
    "e8d8af9b74908e56a86550492f4cf26"
    "a100bfd674cf858c61e72e3193b3d8a24"
)
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


def _control_evidence(path=CONTROL_INTERFACE_PATH):
    raw = path.read_bytes()
    if (
        hashlib.sha256(raw).hexdigest()
        != EXPECTED_CONTROL_INTERFACE_RAW_SHA256
    ):
        raise ValueError("AUTO_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH")
    if (
        _git_blob(
            CONTROL_EVIDENCE_GIT_OBJECT,
            CONTROL_INTERFACE_REPO_PATH,
        )
        != raw
    ):
        raise ValueError("AUTO_CONTROL_INTERFACE_GIT_BLOB_DRIFT")
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
        != SOURCE_AUTO_GIT_OBJECT
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
        != "AUTO_EXACT_BUNDLE_INTEGRATION"
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
        != SOURCE_AUTO_GIT_OBJECT
        or source.get("artifact_digest")
        != SOURCE_AUTO_RUNTIME_INTERFACE_RAW_SHA256
        or source.get("integration_state")
        != "SOURCE_CANDIDATE_NOT_FINAL"
        or not isinstance(transition, dict)
        or transition.get("auto_runtime_integration_complete") is not False
        or transition.get("au_040_complete") is not False
        or transition.get("canonical_publication_permitted") is not False
        or transition.get("external_gmail_ready") is not False
        or transition.get("m0c_b_permitted") is not False
        or transition.get("repository_bound") is not False
        or transition.get("schedule_authority_resolved") is not False
        or transition.get("schedule_complete") is not False
        or not isinstance(promotion, dict)
        or promotion.get("verified_git_object_id")
        != SOURCE_AUTO_GIT_OBJECT
        or promotion.get("artifact_digest")
        != EXPECTED_SCHEMA_PROMOTION_INTERFACE_RAW_SHA256
    ):
        raise ValueError("AUTO_CONTROL_INTERFACE_CONTRACT_MISMATCH")
    for relative_path in (
        "CodexSkills/governance/tools/build_activation_control.py",
        "CodexSkills/governance/tools/canonical_json.py",
        "CodexSkills/governance/tools/validate_activation.py",
        "CodexSkills/governance/tools/validate_mechanism.py",
    ):
        if (
            REPO_ROOT.joinpath(*relative_path.split("/")).read_bytes()
            != _git_blob(CONTROL_EVIDENCE_GIT_OBJECT, relative_path)
        ):
            raise ValueError("AUTO_CONTROL_RUNTIME_LOCAL_DRIFT")
    return {
        "auto_runtime_integration_complete": False,
        "interface_raw_sha256": (
            EXPECTED_CONTROL_INTERFACE_RAW_SHA256
        ),
        "mode": "DRAFT_NON_ACTIVE_CONTROL",
        "next_phase": interface["next_phase"],
        "status": interface["status"],
        "verified_git_object_id": CONTROL_EVIDENCE_GIT_OBJECT,
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
            AUTO_DIR / "tools" / "validate_auto.py",
        ]
    )
    return sorted(paths, key=lambda path: path.relative_to(REPO_ROOT).as_posix())


def build():
    consumer = _consumer_first_evidence()
    transport = _transport_draft_evidence()
    promotion = _schema_promotion_evidence()
    final_candidate = _final_candidate_evidence()
    control = _control_evidence()
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
        "activation_control_baseline_git_object_id": (
            control["verified_git_object_id"]
        ),
        "activation_control_baseline_interface_raw_sha256": (
            control["interface_raw_sha256"]
        ),
        "activation_control_interface_path": (
            "CodexSkills/governance/activation/control-interface.json"
        ),
        "activation_control_mode": "DRAFT_NON_ACTIVE_CONTROL",
        "activation_control_trust_tuple_repo_external_only": True,
        "activation_control_observed_root_status": control["status"],
        "auto_exact_bundle_integration_complete": True,
        "control_observed_auto_runtime_integration_complete": control[
            "auto_runtime_integration_complete"
        ],
        "control_sync_required_before_state_write": True,
        "dual_external_trust_tuples_required": True,
        "activation_forbidden_without_coordinated_m0c": True,
        "activation_handshake_entrypoint": (
            "CodexSkills/registry/auto/tools/activation_handshake_cli.py"
        ),
        "activation_instance_created": False,
        "activation_settlement_recomputed_before_publish": True,
        "au_040_authority_ruling_status": (
            "FINAL_31_5_INTEGRATED_RUNTIME_WRITER_PENDING"
        ),
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
            "publisher_v2_runtime_integration_complete": False,
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
            "runtime_shard_writer_integration_complete": False,
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
        "capability_gate_precedes_state_write": True,
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
        "manual_and_scheduled_same_orchestrator": True,
        "module_artifacts": artifacts,
        "module_count": len(artifacts),
        "m0c_b_permitted": False,
        "next_phase": "MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC",
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
        "runtime_state_write_permitted": False,
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
