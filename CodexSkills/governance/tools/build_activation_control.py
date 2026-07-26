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
RESOLVER_INTERFACE_PATH = (
    GOVERNANCE_DIR / "registry" / "resolver-interface.json"
)
RESOLVER_INTERFACE_REPO_PATH = (
    "CodexSkills/governance/registry/resolver-interface.json"
)
RESOLVER_BUILDER_PATH = (
    GOVERNANCE_DIR / "tools" / "build_bound_reference_resolver.py"
)
RESOLVER_SNAPSHOT_DRAFT_REPO_PATH = (
    "CodexSkills/governance/registry/materialized/_global/"
    "registry-snapshot.v1.json"
)
RESOLVER_SNAPSHOT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:registry-snapshot:v1"
)
RESOLVER_REQUEST_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "bound-reference-request:v1"
)
RESOLVER_DRIFT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:"
    "registry-source-drift-reconciliation:v1"
)
RESOLVER_BINDING_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:skill-binding:v1"
)
RESOLVER_DRIFT_REPO_PATH = (
    "CodexSkills/governance/registry/"
    "source-drift-reconciliation.v1.json"
)

PROTOCOL_REVISION = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CANDIDATE_BUNDLE_GIT_OBJECT_ID = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
AUTO_RUNTIME_GIT_OBJECT_ID = (
    "sha1:b5a32c817e4016f595fa33caed6bce1d51199e63"
)
AUTO_RUNTIME_INTERFACE_RAW_SHA256 = (
    "e88ec8c711434619756ee8f91c451e941501764e30e4a7fff310d8685b02140a"
)
AUTO_RUNTIME_MODULE_COUNT = 27
AUTO_SOURCE_CONTROL_GIT_OBJECT_ID = (
    "sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea"
)
AUTO_SOURCE_CONTROL_INTERFACE_RAW_SHA256 = (
    "28a35148cc18362de4fc53b508754f263a015cf33e4cd187314cf48c767b6920"
)
AUTO_SOURCE_RUNTIME_GIT_OBJECT_ID = (
    "sha1:85edc67df48d4e5bc783f89ed3f3371f25f288e1"
)
AUTO_SOURCE_RUNTIME_INTERFACE_RAW_SHA256 = (
    "ce3aae7a22419c3a01455e8e83cc67b23eeb2ada3f3c17e57590a890c0fdef31"
)
AUTO_SOURCE_RUNTIME_MODULE_COUNT = 25
AUTO_PUBLISHER_SOURCE_CONTROL_GIT_OBJECT_ID = (
    "sha1:fb9b99c36cb870b04f34b5ed3bcb75aeae52c296"
)
AUTO_WRITER_SOURCE_CONTROL_GIT_OBJECT_ID = (
    "sha1:00c4a52d177898b1999b87b29ddb480e89908729"
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
HISTORICAL_MECHANISM_RUNTIME_PATHS = (
    "CodexSkills/governance/tools/build_activation_control.py",
    "CodexSkills/governance/tools/canonical_json.py",
    "CodexSkills/governance/tools/validate_activation.py",
    "CodexSkills/governance/tools/validate_mechanism.py",
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


def _verify_auto_historical_control(
    auto_interface: Mapping[str, Any],
) -> None:
    observation = auto_interface.get("historical_control_observation")
    writer_snapshot = auto_interface.get(
        "runtime_interface_materialization_snapshot"
    )
    publisher_snapshot = auto_interface.get(
        "publisher_v2_runtime_materialization_snapshot"
    )
    repository_snapshot = auto_interface.get(
        "repository_binding_materialization_snapshot"
    )
    if (
        not isinstance(observation, dict)
        or writer_snapshot
        != {
            "as_of_phase": "AUTO_AU040_RUNTIME_WRITER_INTEGRATION",
            "control_sync_required_before_state_write": True,
            "current_auto_runtime_control_bound": False,
            "historical_control_git_object_id": (
                AUTO_WRITER_SOURCE_CONTROL_GIT_OBJECT_ID
            ),
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        }
        or publisher_snapshot
        != {
            "as_of_phase": "AUTO_AU040_PUBLISHER_V2_RUNTIME_INTEGRATION",
            "canonical_publication_permitted": False,
            "control_sync_required_before_state_write": True,
            "current_auto_runtime_control_bound": False,
            "predecessor_control_git_object_id": (
                AUTO_PUBLISHER_SOURCE_CONTROL_GIT_OBJECT_ID
            ),
            "repository_bound": False,
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        }
        or repository_snapshot
        != {
            "as_of_phase": "AUTO_AU040_REPOSITORY_BINDING",
            "bound_reference_resolver_gate_satisfied": False,
            "canonical_publication_permitted": False,
            "current_auto_runtime_control_bound": False,
            "predecessor_control_git_object_id": (
                AUTO_SOURCE_CONTROL_GIT_OBJECT_ID
            ),
            "repository_binding_integration_complete": True,
            "repository_bound": False,
            "runtime_state_write_permitted": False,
            "semantic_scope": "INTERFACE_MATERIALIZATION_ONLY",
        }
    ):
        raise ContractError("ACTIVATION_AUTO_CONTROL_SNAPSHOT_INVALID")

    source_control_raw = _git_blob(
        AUTO_SOURCE_CONTROL_GIT_OBJECT_ID,
        CONTROL_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(source_control_raw).hexdigest()
        != AUTO_SOURCE_CONTROL_INTERFACE_RAW_SHA256
    ):
        raise ContractError(
            "ACTIVATION_AUTO_HISTORICAL_CONTROL_DIGEST_MISMATCH"
        )
    source_control = parse_json_bytes(source_control_raw)
    source_transport = (
        source_control.get("transport_runtime_interface", {})
        if isinstance(source_control, dict)
        else {}
    )
    source_transition = (
        source_control.get("transition_contract", {})
        if isinstance(source_control, dict)
        else {}
    )
    if (
        not isinstance(source_control, dict)
        or source_control.get("status") != "DRAFT_NON_ACTIVE"
        or source_control.get("activation_forbidden") is not True
        or source_control.get("base_auto_git_object_id")
        != AUTO_SOURCE_RUNTIME_GIT_OBJECT_ID
        or source_control.get("next_phase")
        != "AUTO_AU040_REPOSITORY_BINDING"
        or not isinstance(source_transport, dict)
        or source_transport.get("verified_git_object_id")
        != AUTO_SOURCE_RUNTIME_GIT_OBJECT_ID
        or source_transport.get("artifact_digest")
        != AUTO_SOURCE_RUNTIME_INTERFACE_RAW_SHA256
        or source_transport.get("module_count")
        != AUTO_SOURCE_RUNTIME_MODULE_COUNT
        or source_transport.get("integration_state")
        != "AU040_PUBLISHER_V2_SYNCED"
        or not isinstance(source_transition, dict)
        or source_transition.get("auto_runtime_integration_complete")
        is not True
        or source_transition.get("runtime_state_write_permitted")
        is not True
        or source_transition.get("runtime_shard_writer_integration_complete")
        is not True
        or source_transition.get("publisher_v2_runtime_integration_complete")
        is not True
        or source_transition.get("repository_bound") is not False
        or source_transition.get("canonical_publication_permitted")
        is not False
        or source_transition.get("au_040_complete") is not False
        or source_transition.get("au_040_daily_jsonl_shard_complete")
        is not False
        or source_transition.get("external_state_ready") is not False
        or source_transition.get("external_gmail_ready") is not False
    ):
        raise ContractError(
            "ACTIVATION_AUTO_HISTORICAL_CONTROL_CONTRACT_MISMATCH"
        )

    if any(
        observation.get(key) != value
        for key, value in {
            "bound_auto_git_object_id": AUTO_SOURCE_RUNTIME_GIT_OBJECT_ID,
            "bound_auto_module_count": AUTO_SOURCE_RUNTIME_MODULE_COUNT,
            "bound_auto_runtime_interface_raw_sha256": (
                AUTO_SOURCE_RUNTIME_INTERFACE_RAW_SHA256
            ),
            "canonical_path": CONTROL_INTERFACE_REPO_PATH,
            "external_mode": "DRAFT_NON_ACTIVE_CONTROL",
            "interface_raw_sha256": (
                AUTO_SOURCE_CONTROL_INTERFACE_RAW_SHA256
            ),
            "next_phase_at_observation": (
                "AUTO_AU040_REPOSITORY_BINDING"
            ),
            "observed_auto_runtime_integration_complete": True,
            "observed_publisher_v2_runtime_integration_complete": True,
            "observed_repository_bound": False,
            "observed_runtime_state_write_permitted": True,
            "root_status": "DRAFT_NON_ACTIVE",
            "verified_git_object_id": AUTO_SOURCE_CONTROL_GIT_OBJECT_ID,
            "working_tree_control_is_not_historical_trust_evidence": True,
            "working_tree_mechanism_runtime_is_not_historical_trust_evidence": (
                True
            ),
        }.items()
    ):
        raise ContractError(
            "ACTIVATION_AUTO_HISTORICAL_CONTROL_OBSERVATION_MISMATCH"
        )

    runtime_artifacts = observation.get(
        "historical_mechanism_runtime_artifacts"
    )
    if (
        not isinstance(runtime_artifacts, list)
        or [
            entry.get("relative_path")
            for entry in runtime_artifacts
            if isinstance(entry, dict)
        ]
        != list(HISTORICAL_MECHANISM_RUNTIME_PATHS)
    ):
        raise ContractError(
            "ACTIVATION_AUTO_HISTORICAL_RUNTIME_SET_INVALID"
        )
    for entry in runtime_artifacts:
        if (
            not isinstance(entry, dict)
            or not _is_sha256(entry.get("artifact_digest"))
            or hashlib.sha256(
                _git_blob(
                    AUTO_SOURCE_CONTROL_GIT_OBJECT_ID,
                    entry["relative_path"],
                )
            ).hexdigest()
            != entry["artifact_digest"]
        ):
            raise ContractError(
                "ACTIVATION_AUTO_HISTORICAL_RUNTIME_DIGEST_MISMATCH"
            )


def _verified_resolver_interface() -> tuple[bytes, Mapping[str, Any]]:
    try:
        process = subprocess.run(
            [
                "/usr/bin/python3",
                "-B",
                str(RESOLVER_BUILDER_PATH),
                "--check",
            ],
            cwd=REPO_ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ContractError(
            "ACTIVATION_BOUND_RESOLVER_BUILDER_UNAVAILABLE"
        ) from exc
    if process.returncode != 0:
        raise ContractError(
            "ACTIVATION_BOUND_RESOLVER_GENERATED_DRIFT:"
            + process.stderr.strip()
        )
    try:
        current = RESOLVER_INTERFACE_PATH.read_bytes()
    except OSError as exc:
        raise ContractError(
            "ACTIVATION_BOUND_RESOLVER_INTERFACE_READ_FAILED"
        ) from exc
    interface = parse_json_bytes(current)
    if (
        not isinstance(interface, dict)
        or interface.get("artifact_digest")
        != canonical_digest(interface, "/artifact_digest")
        or interface.get("protocol_revision") != PROTOCOL_REVISION
        or interface.get("bundle_digest") != CANDIDATE_BUNDLE_DIGEST
        or interface.get("candidate_git_object_id")
        != CANDIDATE_BUNDLE_GIT_OBJECT_ID
        or interface.get("candidate_manifest_path")
        != CANDIDATE_MANIFEST_REPO_PATH
        or interface.get("candidate_trust_mode") != "CANDIDATE"
        or interface.get("catalog_count") != 4
        or interface.get("catalog_path_reservation_complete") is not True
        or interface.get("catalog_path_reservation_required") is not False
        or interface.get("current_materialization_promotable") is not False
        or interface.get("exact_byte_promotion_required") is not True
        or interface.get("exact_byte_promotion_scope")
        != (
            "POST_SOURCE_CONTENT_SYNC_PARITY_COMPLETE_"
            "SUCCESSOR_MATERIALIZATION"
        )
        or interface.get("post_reservation_rebuild_required") is not True
        or interface.get("post_source_content_sync_rebuild_required")
        is not True
        or interface.get("source_drift_reconciliation_complete")
        is not True
        or interface.get("source_content_sync_required") is not True
        or interface.get("auto_integration_complete") is not False
        or interface.get("production_trust_permitted") is not False
        or interface.get("canonical_publication_permitted") is not False
        or interface.get("activation_forbidden") is not True
        or interface.get("next_phase")
        != "AUTO_REGISTRY_SOURCE_CONTENT_SYNC"
        or interface.get("schema_entry_count") != 4
        or interface.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
    ):
        raise ContractError(
            "ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH"
        )
    snapshot = interface.get("registry_snapshot", {})
    contract = interface.get("resolver_contract", {})
    reconciliation = interface.get(
        "source_drift_reconciliation", {}
    )
    if (
        not isinstance(snapshot, dict)
        or snapshot.get("binding_eligible_version_count") != 0
        or snapshot.get("source_mirror_parity_satisfied") is not False
        or snapshot.get("schema_id") != RESOLVER_SNAPSHOT_ID
        or snapshot.get("draft_relative_path")
        != RESOLVER_SNAPSHOT_DRAFT_REPO_PATH
        or not isinstance(
            snapshot.get("registry_snapshot_digest"),
            str,
        )
        or not isinstance(contract, dict)
        or contract.get("implementation_status")
        != "DRAFT_NON_ACTIVE_IMPLEMENTED"
        or contract.get("current_snapshot_can_emit_bound") is not False
        or contract.get("bound_output_schema_id")
        != RESOLVER_BINDING_ID
        or contract.get("request_schema_id")
        != RESOLVER_REQUEST_ID
        or contract.get("fail_closed_unknown_reason_code")
        != "MAPPING_NOT_PROVABLE"
        or not isinstance(reconciliation, dict)
        or reconciliation.get("schema_id") != RESOLVER_DRIFT_ID
        or reconciliation.get("relative_path")
        != RESOLVER_DRIFT_REPO_PATH
        or reconciliation.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
        or reconciliation.get(
            "source_drift_reconciliation_complete"
        )
        is not True
        or reconciliation.get("historical_registry_records_retained")
        is not True
        or reconciliation.get("current_source_skill_count") != 88
        or reconciliation.get("current_source_alias_count") != 20
        or reconciliation.get("source_alias_parity_satisfied") is not True
        or reconciliation.get("source_root_parity_satisfied") is not False
        or reconciliation.get("whole_source_parity_satisfied") is not False
        or reconciliation.get("missing_source_skill_roots")
        != ["codex/context-kernel"]
        or reconciliation.get("pending_content_drift_paths")
        != [
            "codex/graphify",
            "codex/persona-distiller-group",
            "codex/verifier",
        ]
        or reconciliation.get("auto_evidence")
        != {
            "artifact_digest": AUTO_RUNTIME_INTERFACE_RAW_SHA256,
            "verified_git_object_id": AUTO_RUNTIME_GIT_OBJECT_ID,
        }
    ):
        raise ContractError(
            "ACTIVATION_BOUND_RESOLVER_INTERFACE_CONTRACT_MISMATCH"
        )
    try:
        reconciliation_raw = REPO_ROOT.joinpath(
            *RESOLVER_DRIFT_REPO_PATH.split("/")
        ).read_bytes()
    except OSError as exc:
        raise ContractError(
            "ACTIVATION_SOURCE_DRIFT_RECONCILIATION_READ_FAILED"
        ) from exc
    reconciliation_artifact = parse_json_bytes(reconciliation_raw)
    if (
        not isinstance(reconciliation_artifact, dict)
        or reconciliation_artifact.get("schema_version")
        != RESOLVER_DRIFT_ID
        or reconciliation_artifact.get("status")
        != "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
        or reconciliation_artifact.get("artifact_digest")
        != canonical_digest(
            reconciliation_artifact,
            "/artifact_digest",
        )
        or reconciliation_artifact.get("artifact_digest")
        != reconciliation.get("artifact_digest")
    ):
        raise ContractError(
            "ACTIVATION_SOURCE_DRIFT_RECONCILIATION_MISMATCH"
        )
    return current, interface


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
    if not isinstance(auto_interface, dict):
        raise ContractError("ACTIVATION_AUTO_INTERFACE_CONTRACT_MISMATCH")
    _verify_auto_historical_control(auto_interface)
    transport = auto_interface.get("au_040_transport_contract", {})
    repository_contract = auto_interface.get(
        "repository_binding_contract", {}
    )
    resolver_contract = auto_interface.get(
        "bound_reference_resolver_dependency_contract", {}
    )
    reservation = auto_interface.get(
        "catalog_reservation_materialization_snapshot", {}
    )
    if (
        auto_interface.get("status") != "DRAFT_NON_ACTIVE"
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
        or auto_interface.get("activation_control_mode")
        != "DRAFT_NON_ACTIVE_CONTROL"
        or auto_interface.get(
            "activation_control_trust_tuple_repo_external_only"
        )
        is not True
        or auto_interface.get("trust_tuple_repo_external_only") is not True
        or auto_interface.get("dual_external_trust_tuples_required")
        is not True
        or auto_interface.get("control_sync_required_before_state_write")
        is not True
        or auto_interface.get("runtime_preflight_shadow_permitted")
        is not True
        or auto_interface.get("runtime_state_write_permitted") is not False
        or auto_interface.get("runtime_shard_writer_integration_complete")
        is not True
        or auto_interface.get("publisher_v2_runtime_integration_complete")
        is not True
        or auto_interface.get("repository_binding_integration_complete")
        is not True
        or auto_interface.get(
            "repository_binding_readonly_preflight_verified"
        )
        is not False
        or auto_interface.get("repository_bound") is not False
        or auto_interface.get("bound_reference_resolver_gate_satisfied")
        is not False
        or auto_interface.get("catalog_path_reservation_complete")
        is not True
        or auto_interface.get("registry_source_alias_parity_satisfied")
        is not True
        or auto_interface.get("registry_mirror_alias_parity_satisfied")
        is not True
        or auto_interface.get("registry_source_root_parity_satisfied")
        is not False
        or auto_interface.get("registry_whole_source_parity_satisfied")
        is not False
        or auto_interface.get("registry_alias_set_digest")
        != (
            "75f6db86e5a18cc000985dc32a719ac7e0bc15b22b2e3f20"
            "c0d32d3138f27387"
        )
        or auto_interface.get("au_040_complete") is not False
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
        or auto_interface.get("activation_instance_created") is not False
        or auto_interface.get("runtime_writer_shadow_status")
        != "UNBOUND_REPOSITORY_CONTROL_SYNC_PENDING"
        or auto_interface.get("runtime_writer_shadow_validator_kind")
        != "DEVELOPMENT_ONLY_UNBOUND"
        or auto_interface.get("runtime_writer_shadow_returns_bootstrap_context")
        is not False
        or auto_interface.get("runtime_writer_shadow_state_access_permitted")
        is not False
        or auto_interface.get("runtime_publisher_shadow_status")
        != "UNBOUND_REPOSITORY_CONTROL_SYNC_PENDING"
        or auto_interface.get("runtime_publisher_shadow_validator_kind")
        != "DEVELOPMENT_ONLY_UNBOUND"
        or auto_interface.get(
            "runtime_publisher_shadow_returns_bootstrap_context"
        )
        is not False
        or auto_interface.get(
            "runtime_publisher_shadow_state_access_permitted"
        )
        is not False
        or auto_interface.get("runtime_publisher_shadow_validator_path")
        != "CodexSkills/registry/auto/tools/validate_au040_publisher.py"
        or auto_interface.get("runtime_repository_binding_shadow_status")
        != "UNBOUND_REPOSITORY_CONTROL_SYNC_PENDING"
        or auto_interface.get(
            "runtime_repository_binding_shadow_validator_kind"
        )
        != "DEVELOPMENT_ONLY_UNBOUND"
        or auto_interface.get(
            "runtime_repository_binding_shadow_returns_bootstrap_context"
        )
        is not False
        or auto_interface.get(
            "runtime_repository_binding_shadow_state_access_permitted"
        )
        is not False
        or auto_interface.get(
            "runtime_repository_binding_shadow_validator_path"
        )
        != "CodexSkills/registry/auto/tools/validate_au040_publisher.py"
        or auto_interface.get("au_040_authority_ruling_status")
        != "REGISTRY_CATALOG_RESERVED_SOURCE_DRIFT_PENDING"
        or auto_interface.get("notification_production_transport")
        != "GMAIL_API_V1"
        or auto_interface.get("notification_provider_readback_required") is not True
        or auto_interface.get("notification_test_transport_production_forbidden")
        is not True
        or auto_interface.get("next_phase")
        != "MECHANISM_REGISTRY_SOURCE_DRIFT_RECONCILIATION"
        or not isinstance(transport, dict)
        or transport.get("current_candidate_schema_count") != 31
        or transport.get("final_candidate_materialization_complete")
        is not True
        or transport.get("runtime_shard_writer_integration_complete")
        is not True
        or transport.get("publisher_v2_runtime_integration_complete")
        is not True
        or transport.get("repository_binding_integration_complete")
        is not True
        or transport.get(
            "publisher_v2_control_sync_required_before_canonical_write"
        )
        is not True
        or transport.get("publisher_v2_delete_prior_bytes_revalidated")
        is not True
        or transport.get("publisher_v2_jsonl_per_line_validation")
        is not True
        or transport.get(
            "publisher_v2_manifest_recomputed_from_physical_descriptors"
        )
        is not True
        or transport.get("publisher_serialization_discriminator_required")
        is not True
        or transport.get("repository_bound") is not False
        or not isinstance(repository_contract, dict)
        or repository_contract.get("repository_id")
        != "github.com/LinzeColin/AgentDatabase"
        or repository_contract.get("remote_name") != "origin"
        or repository_contract.get("branch") != "main"
        or repository_contract.get("remote_ref") != "refs/heads/main"
        or repository_contract.get("push_refspec") != "HEAD:main"
        or repository_contract.get("object_format") != "sha1"
        or repository_contract.get("expected_fetch_url")
        != "git@github.com:LinzeColin/AgentDatabase.git"
        or repository_contract.get("expected_push_url")
        != "git@github.com:LinzeColin/AgentDatabase.git"
        or repository_contract.get("canonical_run_log_root")
        != "OpenAIDatabase/data/run_logs/skills_runs/"
        or repository_contract.get("reference_main_clean_required")
        is not True
        or repository_contract.get("changed_path_exact_closure_required")
        is not True
        or repository_contract.get(
            "bound_reference_resolver_required_before_mutable_git"
        )
        is not True
        or repository_contract.get("bound_reference_resolver_owner_plane")
        != "MECHANISM"
        or not isinstance(resolver_contract, dict)
        or resolver_contract.get("gate_owner_plane") != "MECHANISM"
        or resolver_contract.get(
            "adapter_may_generate_or_authenticate_resolver"
        )
        is not False
        or resolver_contract.get(
            "current_registry_compatibility_index_is_not_snapshot_truth"
        )
        is not True
        or resolver_contract.get(
            "pinned_git_object_reads_before_gate_permitted"
        )
        is not True
        or resolver_contract.get("unprovable_binding_action")
        != "PROJECT_UNKNOWN_AND_BLOCK_CANONICAL_PUBLICATION"
        or resolver_contract.get("must_precede")
        != [
            "GMAIL_CLIENT",
            "GIT_LS_REMOTE",
            "GIT_MUTABLE_BACKEND",
            "LOCK",
            "NOTIFICATION_OUTBOX",
            "PUBLISHER",
            "STATE_ROOT",
            "WATERMARK",
            "WORKTREE",
        ]
        or resolver_contract.get("missing_current_artifacts")
        != [
            "FOUR_SOURCE_IDENTITY_INSTANCE_VERSION_CATALOGS",
            "GLOBAL_SKILL_IDENTITY_RECORDS",
            "PROMOTABLE_VERSIONED_REGISTRY_SNAPSHOT",
        ]
        or not isinstance(reservation, dict)
        or reservation.get("as_of_phase")
        != "AUTO_REGISTRY_CATALOG_PATH_RESERVATION"
        or reservation.get("catalog_path_reservation_complete")
        is not True
        or reservation.get("catalog_or_snapshot_artifacts_generated")
        is not False
        or reservation.get("current_source_skill_count") != 88
        or reservation.get("historical_source_skill_count") != 89
        or reservation.get("source_alias_count") != 20
        or reservation.get("mirror_alias_count") != 20
        or reservation.get("source_alias_parity_satisfied") is not True
        or reservation.get("mirror_alias_parity_satisfied") is not True
        or reservation.get("source_root_parity_satisfied") is not False
        or reservation.get("whole_source_parity_satisfied") is not False
        or reservation.get("missing_source_skill_roots")
        != ["codex/context-kernel"]
        or reservation.get("non_alias_content_drift_observed_paths")
        != [
            "codex/graphify",
            "codex/persona-distiller-group",
            "codex/verifier",
        ]
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
    _verified_resolver_interface()


def control_interface(schemas: Mapping[str, Mapping[str, Any]]) -> Dict[str, Any]:
    entries = []
    resolver_raw = RESOLVER_INTERFACE_PATH.read_bytes()
    resolver_interface = parse_json_bytes(resolver_raw)
    resolver_snapshot = resolver_interface["registry_snapshot"]
    source_drift = resolver_interface[
        "source_drift_reconciliation"
    ]
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
        "bound_reference_resolver_contract": {
            "artifact_digest": hashlib.sha256(
                resolver_raw
            ).hexdigest(),
            "auto_integration_complete": False,
            "binding_eligible_version_count": resolver_snapshot[
                "binding_eligible_version_count"
            ],
            "catalog_path_reservation_complete": True,
            "catalog_path_reservation_required": False,
            "current_snapshot_can_emit_bound": False,
            "current_snapshot_promotable": False,
            "gate_satisfied": False,
            "implementation_complete": True,
            "production_trust_permitted": False,
            "post_reservation_rebuild_required": True,
            "post_source_content_sync_rebuild_required": True,
            "registry_snapshot_digest": resolver_snapshot[
                "registry_snapshot_digest"
            ],
            "registry_snapshot_draft_relative_path": resolver_snapshot[
                "draft_relative_path"
            ],
            "registry_snapshot_schema_id": resolver_snapshot["schema_id"],
            "relative_path": RESOLVER_INTERFACE_REPO_PATH,
            "source_mirror_parity_satisfied": False,
            "source_content_sync_required": True,
            "source_drift_reconciliation": {
                "artifact_digest": source_drift["artifact_digest"],
                "historical_registry_records_retained": True,
                "missing_source_skill_roots": source_drift[
                    "missing_source_skill_roots"
                ],
                "pending_content_drift_paths": source_drift[
                    "pending_content_drift_paths"
                ],
                "relative_path": source_drift["relative_path"],
                "schema_id": source_drift["schema_id"],
                "source_alias_parity_satisfied": True,
                "source_drift_reconciliation_complete": True,
                "source_root_parity_satisfied": False,
                "whole_source_parity_satisfied": False,
            },
            "status": (
                "DRAFT_NON_ACTIVE_SOURCE_DRIFT_RECONCILED"
            ),
        },
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
        "next_phase": "AUTO_REGISTRY_SOURCE_CONTENT_SYNC",
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
            "bound_reference_resolver_auto_integration_complete": False,
            "bound_reference_resolver_implementation_complete": True,
            "catalog_path_reservation_complete": True,
            "auto_runtime_source_candidate": {
                "bundle_digest": SOURCE_AUTO_CANDIDATE_BUNDLE_DIGEST,
                "policy_count": 5,
                "schema_count": 29,
                "verified_git_object_id": SOURCE_AUTO_CANDIDATE_GIT_OBJECT_ID,
            },
            "canonical_publication_permitted": False,
            "effective_runtime_state_write_permitted": False,
            "external_gmail_ready": False,
            "external_state_ready": False,
            "final_candidate_integration_required": False,
            "m0c_b_permitted": False,
            "promotion_evidence": {
                "artifact_digest": AUTO_PROMOTION_INTERFACE_RAW_SHA256,
                "relative_path": AUTO_PROMOTION_INTERFACE_REPO_PATH,
                "verified_git_object_id": AUTO_PROMOTION_GIT_OBJECT_ID,
            },
            "publisher_v2_runtime_integration_complete": True,
            "repository_binding_integration_complete": True,
            "repository_bound": True,
            "bound_reference_resolver_gate_satisfied": False,
            "runtime_preflight_shadow_permitted": True,
            "runtime_shard_writer_integration_complete": True,
            "runtime_state_instance_created": False,
            "runtime_state_write_gate_status": (
                "BOUND_REFERENCE_RESOLVER_SOURCE_CONTENT_SYNC_PENDING"
            ),
            "runtime_state_write_permitted": True,
            "schedule_authority_resolved": False,
            "schedule_complete": False,
            "source_content_sync_required": True,
            "source_drift_reconciliation_complete": True,
        },
        "transport_runtime_interface": {
            "artifact_digest": AUTO_RUNTIME_INTERFACE_RAW_SHA256,
            "integration_state": (
                "REGISTRY_CATALOG_RESERVED_SOURCE_CONTENT_SYNC_PENDING"
            ),
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
