#!/usr/bin/env python3
"""Build/check the non-active two-stage SkillOps activation control contract."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence

from canonical_json import canonicalize_object, parse_json_bytes
from validate_mechanism import (
    ContractError,
    PROTOCOL,
    TrustTuple,
    build_registry,
    load_trusted_bundle,
    scan_public_value,
)


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
ACTIVATION_DIR = GOVERNANCE_DIR / "activation"
SCHEMA_DIR = ACTIVATION_DIR / "schemas"
CONTROL_INTERFACE_PATH = ACTIVATION_DIR / "control-interface.json"
CONTROL_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/activation/control-interface.json"
)
VERSION_PATH = REPO_ROOT / "CodexSkills" / "VERSION"
CANDIDATE_MANIFEST_PATH = (
    REPO_ROOT
    / "CodexSkills"
    / "governance"
    / "bundles"
    / "schema-bundle-manifest.v1.json"
)
AUTO_RUNTIME_INTERFACE_PATH = (
    REPO_ROOT / "CodexSkills" / "registry" / "auto" / "runtime-interface.json"
)
AUTO_PROMOTION_INTERFACE_REPO_PATH = (
    "CodexSkills/registry/auto/schemas/public-v2/promotion-interface.json"
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
COMMON_SCHEMA_PATH = GOVERNANCE_DIR / "schemas" / "common-definitions.schema.json"

PROTOCOL_REVISION = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_BUNDLE_GIT_OBJECT_ID = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
AUTO_RUNTIME_GIT_OBJECT_ID = (
    "sha1:7ed9e761921f557887440803d1fc7327f3e986a9"
)
AUTO_RUNTIME_INTERFACE_RAW_SHA256 = (
    "09af0c00273825e90a489f413a2f0bb6995042e5b4eea17973ce7582eab66340"
)
AUTO_RUNTIME_MODULE_COUNT = 21
AUTO_SOURCE_CONTROL_GIT_OBJECT_ID = (
    "sha1:66d5bafadca508cad825b4ce49a42e81e8b66ef7"
)
AUTO_SOURCE_CONTROL_INTERFACE_RAW_SHA256 = (
    "86e4d625bdab87261a39c949883d410822e25e0222dbab6a333d171ce420c614"
)
AUTO_PROMOTION_GIT_OBJECT_ID = (
    "sha1:ab49666bd3343c2abbfc6766478fad63d44163d0"
)
AUTO_PROMOTION_INTERFACE_RAW_SHA256 = (
    "65c2e83bb2491d1cb3059767cf1705fc7541bd7e97449f33a51ba17a04f5e595"
)
SOURCE_AUTO_CANDIDATE_BUNDLE_DIGEST = (
    "2704ed797c843f969965db600747abcdcd217550522e6479aab6817ef5a86ef5"
)
SOURCE_AUTO_CANDIDATE_GIT_OBJECT_ID = (
    "sha1:899a4374bc02f5e18444fea7404864df7b118adf"
)
CONSUMER_INTERFACE_RAW_SHA256 = (
    "189a47300fc1aa6012e87feb6184833cb717cdbe2b9dc9be6db89197f579939c"
)
CONSUMER_GIT_OBJECT_ID = "sha1:91a12e48351be3ee05ec23ef61aec81056b02014"
TARGET_SRV_REVISION = "v0.0.0.3"
CANDIDATE_MANIFEST_REPO_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CANDIDATE_MANIFEST_RAW_SHA256 = (
    "66ad125629cab71739ff2bc266219f995f7a45998936ca720c6db678ee77e65a"
)

COMMON_ID = "urn:linzecolin:agentdatabase:skillops:schema:common-definitions:v1"
INTENT_ID = "urn:linzecolin:agentdatabase:skillops:schema:activation-intent:v1"
SETTLEMENT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:activation-settlement:v1"
)
NOTIFICATION_RECEIPT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:notification-receipt:v3"
)

INTENT_SCHEMA_PATH = SCHEMA_DIR / "activation-intent.schema.json"
SETTLEMENT_SCHEMA_PATH = SCHEMA_DIR / "activation-settlement.schema.json"

PLANNED_ARTIFACT_ROLES = (
    "ACTIVE_VERSION_MARKER",
    "ACTIVATION_INTENT",
    "ACTIVATION_SETTLEMENT",
    "MECHANISM_HANDOFF",
    "NOTIFICATION_RECEIPT",
)
DIGEST_AVAILABILITY = (
    "BOUND_IN_INTENT",
    "DERIVED_AFTER_PROVIDER_SENT",
    "SELF_DIGESTED_INTENT",
)
SETTLEMENT_ARTIFACT_ROLES = (
    "ACTIVE_VERSION_MARKER",
    "ACTIVATION_INTENT",
    "MECHANISM_HANDOFF",
    "NOTIFICATION_RECEIPT",
)
NOTIFICATION_AFFECTED_PATH_REFS = (
    "CodexSkills/VERSION",
    "CodexSkills/governance",
)


def ref(name: str) -> Dict[str, str]:
    return {"$ref": f"{COMMON_ID}#/$defs/{name}"}


def closed_object(
    properties: Mapping[str, Any],
    required: Sequence[str],
    *,
    title: Optional[str] = None,
) -> Dict[str, Any]:
    value: Dict[str, Any] = {
        "type": "object",
        "additionalProperties": False,
        "properties": dict(properties),
        "required": list(required),
    }
    if title is not None:
        value["title"] = title
    return value


def activation_intent_schema() -> Dict[str, Any]:
    artifact = closed_object(
        {
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "artifact_role": {"enum": list(PLANNED_ARTIFACT_ROLES)},
            "digest_availability": {"enum": list(DIGEST_AVAILABILITY)},
            "artifact_digest": ref("sha256"),
        },
        [
            "artifact_repo_path",
            "artifact_role",
            "digest_availability",
        ],
    )
    artifact["allOf"] = [
        {
            "if": {
                "properties": {
                    "digest_availability": {"const": "BOUND_IN_INTENT"}
                },
                "required": ["digest_availability"],
            },
            "then": {"required": ["artifact_digest"]},
            "else": {"not": {"required": ["artifact_digest"]}},
        }
    ]
    schema = closed_object(
        {
            "schema_version": {"const": INTENT_ID},
            "protocol_revision": ref("protocol_revision"),
            "bundle_digest": ref("sha256"),
            "activation_uid": {
                "type": "string",
                "pattern": "^act_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
            },
            "envelope_uid": ref("envelope_uid"),
            "notification_uid": {
                "type": "string",
                "pattern": "^ntf_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
            },
            "auto_transaction_uid": {
                "type": "string",
                "pattern": "^atx_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
            },
            "bundle_git_object_id": ref("git_object_id"),
            "expected_remote_head": ref("git_object_id"),
            "candidate_manifest_path": {
                "const": CANDIDATE_MANIFEST_REPO_PATH
            },
            "target_srv_revision": ref("srv_revision"),
            "impact": {"const": "MAJOR"},
            "change_code": {"const": "ACTIVE_BUNDLE_CHANGE"},
            "planned_action": {"const": "ACTIVATE"},
            "notification_timing": {"const": "PRE_WRITE"},
            "recipient_ref": ref("recipient_ref"),
            "rollback_target_ref": ref("git_object_id"),
            "notification_affected_path_refs": {
                "const": list(NOTIFICATION_AFFECTED_PATH_REFS)
            },
            "planned_artifacts": {
                "type": "array",
                "minItems": 5,
                "maxItems": 16,
                "uniqueItems": True,
                "items": artifact,
            },
            "created_at": ref("utc_z_timestamp"),
            "envelope_digest": ref("sha256"),
        },
        [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "activation_uid",
            "envelope_uid",
            "notification_uid",
            "auto_transaction_uid",
            "bundle_git_object_id",
            "expected_remote_head",
            "candidate_manifest_path",
            "target_srv_revision",
            "impact",
            "change_code",
            "planned_action",
            "notification_timing",
            "recipient_ref",
            "rollback_target_ref",
            "notification_affected_path_refs",
            "planned_artifacts",
            "created_at",
            "envelope_digest",
        ],
        title="Pre-notification coordinated activation intent",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = INTENT_ID
    return schema


def activation_settlement_schema() -> Dict[str, Any]:
    evidence = closed_object(
        {
            "evidence_type": {
                "enum": ["ACTIVATION_INTENT", "NOTIFICATION_RECEIPT"]
            },
            "evidence_uid": ref("typed_uid"),
            "evidence_digest": ref("sha256"),
            "artifact_repo_path": ref("repo_relative_posix_path"),
        },
        [
            "evidence_type",
            "evidence_uid",
            "evidence_digest",
            "artifact_repo_path",
        ],
    )
    artifact = closed_object(
        {
            "artifact_uid": ref("typed_uid"),
            "artifact_role": {"enum": list(SETTLEMENT_ARTIFACT_ROLES)},
            "artifact_repo_path": ref("repo_relative_posix_path"),
            "artifact_digest": ref("sha256"),
            "artifact_schema_id": ref("urn_id"),
        },
        [
            "artifact_uid",
            "artifact_role",
            "artifact_repo_path",
            "artifact_digest",
        ],
    )
    schema = closed_object(
        {
            "schema_version": {"const": SETTLEMENT_ID},
            "protocol_revision": ref("protocol_revision"),
            "bundle_digest": ref("sha256"),
            "activation_uid": {
                "type": "string",
                "pattern": "^act_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
            },
            "envelope_uid": ref("envelope_uid"),
            "auto_transaction_uid": {
                "type": "string",
                "pattern": "^atx_[0-7][0-9A-HJKMNP-TV-Z]{25}$",
            },
            "expected_remote_head": ref("git_object_id"),
            "target_srv_revision": ref("srv_revision"),
            "notification_provider_status": {"const": "SENT"},
            "notification_timing": {"const": "PRE_WRITE"},
            "recipient_ref": ref("recipient_ref"),
            "evidence_refs": {
                "type": "array",
                "minItems": 2,
                "maxItems": 2,
                "uniqueItems": True,
                "items": evidence,
            },
            "artifacts": {
                "type": "array",
                "minItems": 4,
                "maxItems": 15,
                "uniqueItems": True,
                "items": artifact,
            },
            "created_at": ref("utc_z_timestamp"),
            "envelope_digest": ref("sha256"),
        },
        [
            "schema_version",
            "protocol_revision",
            "bundle_digest",
            "activation_uid",
            "envelope_uid",
            "auto_transaction_uid",
            "expected_remote_head",
            "target_srv_revision",
            "notification_provider_status",
            "notification_timing",
            "recipient_ref",
            "evidence_refs",
            "artifacts",
            "created_at",
            "envelope_digest",
        ],
        title="Post-provider coordinated activation settlement",
    )
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = SETTLEMENT_ID
    return schema


def _pretty(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _strict_object(path: Path, code: str) -> Mapping[str, Any]:
    try:
        value = parse_json_bytes(path.read_bytes())
    except Exception as exc:
        raise ContractError(f"{code}_READ_OR_PARSE_FAILED") from exc
    if not isinstance(value, dict):
        raise ContractError(f"{code}_ROOT_INVALID")
    return value


def _git_blob(object_id: str, relative_path: str) -> bytes:
    raw_object_id = object_id.split(":", 1)[-1]
    process = subprocess.run(
        ["git", "-C", str(REPO_ROOT), "show", f"{raw_object_id}:{relative_path}"],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=30,
        check=False,
    )
    if process.returncode != 0:
        raise ContractError("ACTIVATION_PINNED_GIT_BLOB_UNAVAILABLE")
    return process.stdout


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _verify_auto_module_artifacts(
    auto_interface: Mapping[str, Any],
    *,
    require_current_auto: bool,
) -> None:
    artifacts = auto_interface.get("module_artifacts")
    if (
        not isinstance(artifacts, list)
        or auto_interface.get("module_count") != AUTO_RUNTIME_MODULE_COUNT
        or len(artifacts) != AUTO_RUNTIME_MODULE_COUNT
    ):
        raise ContractError("ACTIVATION_AUTO_MODULE_SET_INVALID")

    observed_paths = []
    for entry in artifacts:
        if not isinstance(entry, dict):
            raise ContractError("ACTIVATION_AUTO_MODULE_ENTRY_INVALID")
        relative_path = entry.get("relative_path")
        artifact_digest = entry.get("artifact_digest")
        if (
            not isinstance(relative_path, str)
            or not relative_path.startswith("CodexSkills/registry/auto/")
            or "\\" in relative_path
            or ".." in PurePosixPath(relative_path).parts
            or not _is_sha256(artifact_digest)
        ):
            raise ContractError("ACTIVATION_AUTO_MODULE_ENTRY_INVALID")
        observed_paths.append(relative_path)
        pinned_raw = _git_blob(AUTO_RUNTIME_GIT_OBJECT_ID, relative_path)
        if hashlib.sha256(pinned_raw).hexdigest() != artifact_digest:
            raise ContractError("ACTIVATION_AUTO_MODULE_DIGEST_MISMATCH")
        if require_current_auto:
            try:
                local_raw = REPO_ROOT.joinpath(
                    *relative_path.split("/")
                ).read_bytes()
            except OSError as exc:
                raise ContractError(
                    "ACTIVATION_AUTO_MODULE_READ_FAILED"
                ) from exc
            if local_raw != pinned_raw:
                raise ContractError(
                    "ACTIVATION_AUTO_MODULE_CURRENT_DRIFT"
                )
    if (
        observed_paths != sorted(observed_paths)
        or len(observed_paths) != len(set(observed_paths))
    ):
        raise ContractError("ACTIVATION_AUTO_MODULE_SET_INVALID")


def _preflight_inputs(
    *,
    require_non_active: bool,
    require_current_auto: bool,
) -> None:
    if PROTOCOL != PROTOCOL_REVISION:
        raise ContractError("ACTIVATION_PROTOCOL_CONSTANT_MISMATCH")
    if require_non_active and VERSION_PATH.exists():
        raise ContractError("ACTIVATION_CONTROL_ACTIVE_VERSION_FORBIDDEN")
    manifest_raw = _git_blob(
        CANDIDATE_BUNDLE_GIT_OBJECT_ID,
        CANDIDATE_MANIFEST_REPO_PATH,
    )
    if require_non_active:
        try:
            current_manifest_raw = CANDIDATE_MANIFEST_PATH.read_bytes()
        except OSError as exc:
            raise ContractError(
                "ACTIVATION_CANDIDATE_MANIFEST_READ_FAILED"
            ) from exc
        if current_manifest_raw != manifest_raw:
            raise ContractError(
                "ACTIVATION_CANDIDATE_MANIFEST_CURRENT_DRIFT"
            )
    manifest = parse_json_bytes(manifest_raw)
    if (
        hashlib.sha256(manifest_raw).hexdigest()
        != CANDIDATE_MANIFEST_RAW_SHA256
        or not isinstance(manifest, dict)
        or manifest.get("bundle_digest") != CANDIDATE_BUNDLE_DIGEST
        or manifest.get("srv_revision") != TARGET_SRV_REVISION
        or manifest.get("schema_count") != 31
        or manifest.get("policy_count") != 5
    ):
        raise ContractError("ACTIVATION_CANDIDATE_MANIFEST_MISMATCH")
    auto_raw = _git_blob(
        AUTO_RUNTIME_GIT_OBJECT_ID,
        "CodexSkills/registry/auto/runtime-interface.json",
    )
    if hashlib.sha256(auto_raw).hexdigest() != AUTO_RUNTIME_INTERFACE_RAW_SHA256:
        raise ContractError("ACTIVATION_AUTO_INTERFACE_RAW_DIGEST_MISMATCH")
    if require_current_auto:
        try:
            current_auto_raw = AUTO_RUNTIME_INTERFACE_PATH.read_bytes()
        except OSError as exc:
            raise ContractError("ACTIVATION_AUTO_INTERFACE_READ_FAILED") from exc
        if current_auto_raw != auto_raw:
            raise ContractError("ACTIVATION_AUTO_INTERFACE_CURRENT_DRIFT")
    auto_interface = parse_json_bytes(auto_raw)
    promotion_raw = _git_blob(
        AUTO_PROMOTION_GIT_OBJECT_ID,
        AUTO_PROMOTION_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(promotion_raw).hexdigest()
        != AUTO_PROMOTION_INTERFACE_RAW_SHA256
    ):
        raise ContractError(
            "ACTIVATION_AUTO_PROMOTION_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    promotion_interface = parse_json_bytes(promotion_raw)
    transport = (
        auto_interface.get("au_040_transport_contract", {})
        if isinstance(auto_interface, dict)
        else {}
    )
    if (
        not isinstance(auto_interface, dict)
        or auto_interface.get("status") != "DRAFT_NON_ACTIVE"
        or auto_interface.get("auto_exact_bundle_integration_complete")
        is not True
        or auto_interface.get("candidate_bundle_digest")
        != CANDIDATE_BUNDLE_DIGEST
        or auto_interface.get("candidate_git_object_id")
        != CANDIDATE_BUNDLE_GIT_OBJECT_ID
        or auto_interface.get("candidate_manifest_raw_sha256")
        != CANDIDATE_MANIFEST_RAW_SHA256
        or auto_interface.get("shared_bundle_schema_count") != 31
        or auto_interface.get("shared_policy_count") != 5
        or auto_interface.get("consumer_first_gate_satisfied") is not True
        or auto_interface.get("consumer_first_verified_git_object_id")
        != CONSUMER_GIT_OBJECT_ID
        or auto_interface.get("consumer_first_interface_raw_sha256")
        != CONSUMER_INTERFACE_RAW_SHA256
        or auto_interface.get("activation_control_baseline_git_object_id")
        != AUTO_SOURCE_CONTROL_GIT_OBJECT_ID
        or auto_interface.get(
            "activation_control_baseline_interface_raw_sha256"
        )
        != AUTO_SOURCE_CONTROL_INTERFACE_RAW_SHA256
        or auto_interface.get("activation_control_mode")
        != "DRAFT_NON_ACTIVE_CONTROL"
        or auto_interface.get("activation_control_observed_root_status")
        != "DRAFT_NON_ACTIVE"
        or auto_interface.get("dual_external_trust_tuples_required")
        is not True
        or auto_interface.get("control_sync_required_before_state_write")
        is not True
        or auto_interface.get(
            "control_observed_auto_runtime_integration_complete"
        )
        is not False
        or auto_interface.get("runtime_preflight_shadow_permitted")
        is not True
        or auto_interface.get("runtime_state_write_permitted") is not False
        or auto_interface.get("au_040_schema_promotion_complete") is not True
        or auto_interface.get(
            "au_040_retention_policy_v3_repository_accepted"
        )
        is not True
        or auto_interface.get("au_040_retention_policy_v3_present")
        is not True
        or auto_interface.get("au_040_manifest_contract_resolved") is not True
        or auto_interface.get(
            "au_040_consumer_manifest_path_contract_present"
        )
        is not True
        or auto_interface.get("au_040_daily_jsonl_shard_complete") is not False
        or auto_interface.get("canonical_publication_permitted") is not False
        or auto_interface.get("schedule_authority_resolved") is not False
        or auto_interface.get("schedule_complete") is not False
        or auto_interface.get("external_gmail_ready_gate_satisfied") is not False
        or auto_interface.get("m0c_b_permitted") is not False
        or auto_interface.get("notification_production_transport")
        != "GMAIL_API_V1"
        or auto_interface.get("notification_provider_readback_required") is not True
        or auto_interface.get("notification_test_transport_production_forbidden")
        is not True
        or auto_interface.get("next_phase")
        != "MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC"
        or not isinstance(transport, dict)
        or transport.get("current_candidate_schema_count") != 31
        or transport.get("final_candidate_materialization_complete")
        is not True
        or transport.get("runtime_shard_writer_integration_complete")
        is not False
        or transport.get("publisher_v2_runtime_integration_complete")
        is not False
        or transport.get("repository_bound") is not False
        or transport.get("schema_promotion_interface_raw_sha256")
        != AUTO_PROMOTION_INTERFACE_RAW_SHA256
        or transport.get("schema_promotion_evidence_git_object_id")
        != AUTO_PROMOTION_GIT_OBJECT_ID
        or not isinstance(promotion_interface, dict)
        or promotion_interface.get("status")
        != "DRAFT_NON_ACTIVE_SCHEMA_PROMOTED"
        or promotion_interface.get("repository_bound") is not False
        or promotion_interface.get("runtime_integration_performed") is not False
    ):
        raise ContractError("ACTIVATION_AUTO_INTERFACE_CONTRACT_MISMATCH")
    _verify_auto_module_artifacts(
        auto_interface,
        require_current_auto=require_current_auto,
    )

    consumer_raw = _git_blob(
        CONSUMER_GIT_OBJECT_ID,
        CONSUMER_INTERFACE_REPO_PATH,
    )
    if hashlib.sha256(consumer_raw).hexdigest() != CONSUMER_INTERFACE_RAW_SHA256:
        raise ContractError("ACTIVATION_CONSUMER_INTERFACE_RAW_DIGEST_MISMATCH")
    if require_current_auto:
        try:
            current_consumer_raw = CONSUMER_INTERFACE_PATH.read_bytes()
        except OSError as exc:
            raise ContractError(
                "ACTIVATION_CONSUMER_INTERFACE_READ_FAILED"
            ) from exc
        if current_consumer_raw != consumer_raw:
            raise ContractError("ACTIVATION_CONSUMER_INTERFACE_CURRENT_DRIFT")
    consumer = parse_json_bytes(consumer_raw)
    candidate_trust = (
        consumer.get("candidate_trust", {})
        if isinstance(consumer, dict)
        else {}
    )
    gate = (
        consumer.get("publication_gate", {})
        if isinstance(consumer, dict)
        else {}
    )
    if (
        not isinstance(consumer, dict)
        or consumer.get("schema_version")
        != "openai_database.skill_run_consumer.v2"
        or consumer.get("status") != "DRAFT_NON_ACTIVE_CONSUMER_READY"
        or candidate_trust.get("verified_git_object_id")
        != CANDIDATE_BUNDLE_GIT_OBJECT_ID
        or candidate_trust.get("expected_bundle_digest")
        != CANDIDATE_BUNDLE_DIGEST
        or candidate_trust.get("canonical_manifest_path")
        != CANDIDATE_MANIFEST_REPO_PATH
        or candidate_trust.get("mode") != "CANDIDATE"
        or gate.get("canonical_publication_permitted") is not False
        or gate.get("repository_shards_permitted") is not False
    ):
        raise ContractError("ACTIVATION_CONSUMER_INTERFACE_CONTRACT_MISMATCH")


def control_interface(schemas: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    entries = []
    paths = {
        INTENT_ID: INTENT_SCHEMA_PATH,
        SETTLEMENT_ID: SETTLEMENT_SCHEMA_PATH,
    }
    for schema_id in sorted(schemas, key=lambda value: value.encode("ascii")):
        entries.append(
            {
                "id": schema_id,
                "relative_path": paths[schema_id]
                .relative_to(REPO_ROOT)
                .as_posix(),
                "schema_sha256": hashlib.sha256(
                    canonicalize_object(schemas[schema_id])
                ).hexdigest(),
                "self_digest_pointer": "/envelope_digest",
            }
        )
    return {
        "activation_forbidden": True,
        "base_auto_git_object_id": AUTO_RUNTIME_GIT_OBJECT_ID,
        "bootstrap_schema_entries": entries,
        "bootstrap_schema_count": len(entries),
        "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
        "candidate_bundle_git_object_id": CANDIDATE_BUNDLE_GIT_OBJECT_ID,
        "candidate_manifest_path": CANDIDATE_MANIFEST_REPO_PATH,
        "candidate_policy_count": 5,
        "candidate_schema_count": 31,
        "candidate_trust_mode": "CANDIDATE",
        "consumer_contract": {
            "artifact_digest": CONSUMER_INTERFACE_RAW_SHA256,
            "canonical_publication_permitted": False,
            "contract_revision": "V2",
            "relative_path": CONSUMER_INTERFACE_REPO_PATH,
            "repository_shards_permitted": False,
            "verified_git_object_id": CONSUMER_GIT_OBJECT_ID,
        },
        "control_trust_contract": {
            "canonical_path": CONTROL_INTERFACE_REPO_PATH,
            "expected_mode": "DRAFT_NON_ACTIVE_CONTROL",
            "external_expected_raw_sha256_required": True,
            "external_verified_git_object_required": True,
            "repository_self_report_is_not_trust_root": True,
        },
        "notification_contract": {
            "actual_recipient_repo_external": True,
            "affected_path_refs": list(NOTIFICATION_AFFECTED_PATH_REFS),
            "affected_path_refs_are_conservative_public_scope": True,
            "exact_write_set_bound_by_intent_digest": True,
            "fake_transport_forbidden": True,
            "provider_readback_required": True,
            "provider_status_required": "SENT",
            "timing": "PRE_WRITE",
            "transport": "GMAIL_API_V1",
        },
        "next_phase": "AUTO_AU040_RUNTIME_WRITER_INTEGRATION",
        "protocol_revision": PROTOCOL_REVISION,
        "publication_contract": {
            "caller_boolean_is_not_trust_root": True,
            "final_request_paths_equal_settlement_plus_self": True,
            "json_artifacts_are_jcs_utf8_without_bom_or_trailing_newline": True,
            "physical_artifact_digests_recomputed": True,
            "remote_readback_required_before_active_trust": True,
            "settlement_excludes_self_from_artifacts": True,
        },
        "sequence": [
            "INTENT_VERIFIED",
            "PROVIDER_SENT_READBACK",
            "SETTLEMENT_VERIFIED",
            "EXPECTED_HEAD_FF_PUBLISH",
            "REMOTE_BYTE_READBACK",
            "ACTIVE_TRUST_BOOTSTRAP",
        ],
        "status": "DRAFT_NON_ACTIVE",
        "target_srv_revision": TARGET_SRV_REVISION,
        "transition_contract": {
            "au_040_complete": False,
            "au_040_daily_jsonl_shard_complete": False,
            "auto_runtime_integrated_candidate": {
                "bundle_digest": CANDIDATE_BUNDLE_DIGEST,
                "policy_count": 5,
                "schema_count": 31,
                "verified_git_object_id": CANDIDATE_BUNDLE_GIT_OBJECT_ID,
            },
            "auto_runtime_integration_complete": True,
            "auto_runtime_source_candidate": {
                "bundle_digest": SOURCE_AUTO_CANDIDATE_BUNDLE_DIGEST,
                "policy_count": 5,
                "schema_count": 29,
                "verified_git_object_id": SOURCE_AUTO_CANDIDATE_GIT_OBJECT_ID,
            },
            "canonical_publication_permitted": False,
            "external_gmail_ready": False,
            "external_state_ready": False,
            "final_candidate_integration_required": False,
            "m0c_b_permitted": False,
            "promotion_evidence": {
                "artifact_digest": AUTO_PROMOTION_INTERFACE_RAW_SHA256,
                "relative_path": AUTO_PROMOTION_INTERFACE_REPO_PATH,
                "verified_git_object_id": AUTO_PROMOTION_GIT_OBJECT_ID,
            },
            "publisher_v2_runtime_integration_complete": False,
            "repository_bound": False,
            "runtime_preflight_shadow_permitted": True,
            "runtime_shard_writer_integration_complete": False,
            "runtime_state_instance_created": False,
            "runtime_state_write_permitted": True,
            "schedule_authority_resolved": False,
            "schedule_complete": False,
        },
        "transport_runtime_interface": {
            "artifact_digest": AUTO_RUNTIME_INTERFACE_RAW_SHA256,
            "integration_state": "FINAL_31_5_INTEGRATED_CONTROL_SYNCED",
            "module_count": AUTO_RUNTIME_MODULE_COUNT,
            "relative_path": "CodexSkills/registry/auto/runtime-interface.json",
            "verified_git_object_id": AUTO_RUNTIME_GIT_OBJECT_ID,
        },
        "validator_contract": {
            "artifact_reads": "DESCRIPTOR_RELATIVE_O_NOFOLLOW",
            "intent_repo_path_argument": "--intent-repo-path",
            "settlement_repo_path_argument": "--settlement-repo-path",
        },
        "write_set_contract": {
            "digest_availability": list(DIGEST_AVAILABILITY),
            "planned_artifact_roles": list(PLANNED_ARTIFACT_ROLES),
            "settlement_artifact_roles": list(SETTLEMENT_ARTIFACT_ROLES),
            "settlement_path_is_distinguished_control_artifact": True,
        },
    }


def expected_outputs(
    *,
    require_non_active: bool = False,
    require_current_auto: bool = False,
) -> Dict[Path, bytes]:
    _preflight_inputs(
        require_non_active=require_non_active,
        require_current_auto=require_current_auto,
    )
    schemas = {
        INTENT_ID: activation_intent_schema(),
        SETTLEMENT_ID: activation_settlement_schema(),
    }
    common = _strict_object(COMMON_SCHEMA_PATH, "ACTIVATION_COMMON_SCHEMA")
    build_registry({COMMON_ID: common, **schemas})
    interface = control_interface(schemas)
    trusted = load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            CANDIDATE_BUNDLE_GIT_OBJECT_ID,
            CANDIDATE_BUNDLE_DIGEST,
            CANDIDATE_MANIFEST_REPO_PATH,
            "CANDIDATE",
        ),
    )
    scan_public_value(interface, trusted.policies)
    return {
        INTENT_SCHEMA_PATH: _pretty(schemas[INTENT_ID]),
        SETTLEMENT_SCHEMA_PATH: _pretty(schemas[SETTLEMENT_ID]),
        CONTROL_INTERFACE_PATH: _pretty(interface),
    }


def materialize(*, check: bool) -> int:
    outputs = expected_outputs(
        require_non_active=not check,
        require_current_auto=not check,
    )
    if check:
        mismatches = [
            path.relative_to(REPO_ROOT).as_posix()
            for path, expected in outputs.items()
            if not path.is_file() or path.read_bytes() != expected
        ]
        if mismatches:
            print(
                "ACTIVATION_CONTROL_MISMATCH:" + ",".join(mismatches),
                file=sys.stderr,
            )
            return 1
        action = "ACTIVATION_CONTROL_BYTE_EQUIVALENT"
    else:
        for path, payload in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
        action = "ACTIVATION_CONTROL_GENERATED_OK"
    interface = parse_json_bytes(outputs[CONTROL_INTERFACE_PATH])
    print(
        f"{action} schemas={interface['bootstrap_schema_count']} "
        f"bundle_digest={interface['bundle_digest']} "
        f"interface_raw_sha256="
        f"{hashlib.sha256(outputs[CONTROL_INTERFACE_PATH]).hexdigest()}"
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
