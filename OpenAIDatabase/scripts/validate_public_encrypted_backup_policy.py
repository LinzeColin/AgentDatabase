#!/usr/bin/env python3
"""Validate the public ciphertext-only backup contract without touching backup data."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping


POLICY_SCHEMA = "openai_database.public_encrypted_backup_policy.v1"
TASK_ID = "TSK.OpenAIDatabase.PEB1.0001"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PEB1.0001"
DEFAULT_POLICY = Path("config/storage/public_encrypted_backup_policy.json")
EXPECTED_LOGICAL_SOURCES = ["codex_memories", "codex_sessions", "codex_attachments"]
EXPECTED_PREFLIGHT = [
    "age_binary_available",
    "unified_recipient_provisioned",
    "private_identity_accessible",
    "source_integrity_verified",
    "remote_release_upload_verified",
]
EXPECTED_MANIFEST_FIELDS = [
    "backup_id",
    "created_at",
    "key_id",
    "recipient_fingerprint",
    "ciphertext_sha256",
    "ciphertext_size_bytes",
    "part_number",
    "part_count",
    "logical_source_set",
    "schema_version",
]


class BackupPolicyError(RuntimeError):
    """Stable fail-closed error that never includes backup source content."""


def mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise BackupPolicyError(f"{label}_invalid")
    return value


def validate_policy(policy: Mapping[str, Any], *, require_ready: bool = False) -> dict[str, Any]:
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("task_id") != TASK_ID
        or policy.get("acceptance_id") != ACCEPTANCE_ID
    ):
        raise BackupPolicyError("policy_identity_invalid")

    status = policy.get("status")
    if status not in {"UNPROVISIONED", "READY"}:
        raise BackupPolicyError("policy_status_invalid")
    scope = mapping(policy.get("scope"), "scope")
    release = mapping(policy.get("release"), "release")
    encryption = mapping(policy.get("encryption"), "encryption")
    unified_key = mapping(policy.get("unified_key"), "unified_key")
    manifest = mapping(policy.get("manifest"), "manifest")
    automation = mapping(policy.get("automation"), "automation")

    if (
        scope.get("logical_sources") != EXPECTED_LOGICAL_SOURCES
        or scope.get("full_recovery_intended") is not True
        or any(
            scope.get(key) is not False
            for key in (
                "plaintext_publication_allowed",
                "git_tracked_ciphertext_allowed",
                "automatic_source_deletion_allowed",
            )
        )
    ):
        raise BackupPolicyError("scope_policy_invalid")
    if (
        release.get("repository") != "LinzeColin/AgentDatabase"
        or release.get("visibility") != "public"
        or release.get("transport") != "github_release_asset_only"
        or release.get("r8_required_before_upload") is not False
        or release.get("remote_verification_required_before_local_ciphertext_cleanup") is not True
        or not isinstance(release.get("max_ciphertext_part_bytes"), int)
        or not 0 < int(release["max_ciphertext_part_bytes"]) <= 1073741824
    ):
        raise BackupPolicyError("release_policy_invalid")
    historical_gate_override = mapping(
        release.get("historical_product_gate_override"), "historical_product_gate_override"
    )
    if (
        historical_gate_override.get("gate_id")
        != "R8_OVERALL_ACCEPTANCE_AND_SINGLE_FINAL_DELIVERY"
        or historical_gate_override.get("applicable_to")
        != "Memory Atlas v1.2 product release"
        or historical_gate_override.get("applicable_to_this_backup") is not False
        or not isinstance(historical_gate_override.get("owner_authorized_at"), str)
        or not historical_gate_override.get("owner_authorized_at")
        or historical_gate_override.get("scope")
        != "public ciphertext-only Codex backup Release assets only"
        or historical_gate_override.get("does_not_override")
        != [
            "age encryption",
            "unified recipient and fingerprint validation",
            "GitHub Release asset-only transport",
            "remote ciphertext hash verification",
            "no automatic source deletion",
        ]
    ):
        raise BackupPolicyError("historical_product_gate_override_invalid")
    if (
        encryption.get("algorithm") != "age-x25519-v1"
        or encryption.get("required_tool") != "age"
        or encryption.get("stream_plain_archive") is not True
        or encryption.get("plain_archive_persisted") is not False
        or encryption.get("ciphertext_suffix") != ".age"
        or encryption.get("compression") != "gzip"
    ):
        raise BackupPolicyError("encryption_policy_invalid")
    if (
        unified_key.get("key_id") != "agentdatabase-public-backup-v1"
        or unified_key.get("private_identity_source")
        != "macos_keychain_or_owner_secret_manager"
        or unified_key.get("identity_file_persisted") is not False
        or unified_key.get("key_export_allowed") is not False
        or unified_key.get("rotation_requires_new_key_id") is not True
    ):
        raise BackupPolicyError("unified_key_policy_invalid")
    if status == "UNPROVISIONED":
        if (
            unified_key.get("recipient_provisioning_status") != "UNPROVISIONED"
            or unified_key.get("public_recipient") is not None
            or unified_key.get("recipient_fingerprint") is not None
        ):
            raise BackupPolicyError("unprovisioned_key_state_invalid")
    else:
        recipient = unified_key.get("public_recipient")
        fingerprint = unified_key.get("recipient_fingerprint")
        if (
            unified_key.get("recipient_provisioning_status") != "READY"
            or not isinstance(recipient, str)
            or not recipient.startswith("age1")
            or not isinstance(fingerprint, str)
            or len(fingerprint) != 64
        ):
            raise BackupPolicyError("ready_key_state_invalid")
    if (
        manifest.get("allowed_fields") != EXPECTED_MANIFEST_FIELDS
        or any(
            manifest.get(key) is not False
            for key in (
                "source_absolute_path_allowed",
                "source_file_name_allowed",
                "plaintext_content_allowed",
                "credential_or_key_material_allowed",
            )
        )
    ):
        raise BackupPolicyError("manifest_policy_invalid")
    if (
        automation.get("default_enabled") is not False
        or automation.get("required_preflight") != EXPECTED_PREFLIGHT
    ):
        raise BackupPolicyError("automation_policy_invalid")
    if require_ready and status != "READY":
        raise BackupPolicyError("backup_key_not_provisioned")
    return {
        "status": "PASS",
        "policy_status": status,
        "ready_for_upload": status == "READY",
        "key_id": unified_key["key_id"],
        "release_transport": release["transport"],
        "plaintext_publication_allowed": False,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    policy_path = args.policy if args.policy.is_absolute() else database_dir / args.policy
    try:
        policy = json.loads(policy_path.read_text(encoding="utf-8"))
        result = validate_policy(policy, require_ready=args.require_ready)
    except (OSError, json.JSONDecodeError, BackupPolicyError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
