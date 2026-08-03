#!/usr/bin/env python3
"""Validate the private ciphertext-only Codex backup contract without backup I/O."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

try:
    from .validate_public_encrypted_backup_policy import (
        BackupPolicyError,
        validate_policy as validate_public_encrypted_backup_policy,
    )
except ImportError:  # direct script execution
    from validate_public_encrypted_backup_policy import (
        BackupPolicyError,
        validate_policy as validate_public_encrypted_backup_policy,
    )


POLICY_SCHEMA = "openai_database.private_encrypted_backup_policy.v1"
TASK_ID = "TSK.OpenAIDatabase.PEB1.0003"
ACCEPTANCE_ID = "ACC.OpenAIDatabase.PEB1.0003"
DEFAULT_POLICY = Path("config/storage/private_encrypted_backup_policy.json")
DEFAULT_PUBLIC_POLICY = Path("config/storage/public_encrypted_backup_policy.json")
EXPECTED_LOGICAL_SOURCES = [
    "codex_state",
    "codex_memories",
    "codex_sessions",
    "codex_archived_sessions",
    "codex_attachments",
    "codex_automations",
    "codex_tasks",
    "chatgpt_exports",
    "openaidatabase_live_data",
    "verified_evidence_adapters",
]
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


class PrivateBackupPolicyError(RuntimeError):
    """Stable fail-closed error that never includes backup source content."""


def mapping(value: Any, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise PrivateBackupPolicyError(f"{label}_invalid")
    return value


def validate_policy(
    policy: Mapping[str, Any],
    public_policy: Mapping[str, Any],
    *,
    require_ready: bool = False,
) -> dict[str, Any]:
    if (
        policy.get("schema_version") != POLICY_SCHEMA
        or policy.get("task_id") != TASK_ID
        or policy.get("acceptance_id") != ACCEPTANCE_ID
    ):
        raise PrivateBackupPolicyError("policy_identity_invalid")
    if policy.get("status") != "READY":
        raise PrivateBackupPolicyError("policy_status_invalid")
    if (
        policy.get("owner_authorization_ref")
        != "config/storage/raw_material_policy.json#private_encrypted_release_automation_authorization"
    ):
        raise PrivateBackupPolicyError("owner_authorization_ref_invalid")

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
        raise PrivateBackupPolicyError("scope_policy_invalid")
    if (
        release.get("repository") != "LinzeColin/Private-Database"
        or release.get("visibility") != "private"
        or release.get("transport") != "github_release_asset_only"
        or release.get("draft_release_required") is not True
        or release.get("remote_verification_required_before_local_ciphertext_cleanup") is not True
        or not isinstance(release.get("max_ciphertext_part_bytes"), int)
        or int(release["max_ciphertext_part_bytes"]) != 94371840
        or not isinstance(release.get("max_parts"), int)
        or int(release["max_parts"]) != 64
        or release.get("automatic_release_tag_prefix") != "memory-atlas-auto-backup-"
        or release.get("automatic_release_retention_count") != 3
        or release.get("retention_scope")
        != "automatic_releases_with_matching_tag_prefix_only"
        or release.get("manual_or_nonmatching_release_mutation_allowed") is not False
    ):
        raise PrivateBackupPolicyError("release_policy_invalid")
    if (
        encryption.get("algorithm") != "age-x25519-v1"
        or encryption.get("required_tool") != "age"
        or encryption.get("stream_plain_archive") is not True
        or encryption.get("plain_archive_persisted") is not False
        or encryption.get("ciphertext_suffix") != ".age"
        or encryption.get("compression") != "gzip"
    ):
        raise PrivateBackupPolicyError("encryption_policy_invalid")
    if (
        unified_key.get("public_policy_ref")
        != "config/storage/public_encrypted_backup_policy.json#unified_key"
        or unified_key.get("keychain_account") != "memory-atlas"
        or unified_key.get("private_identity_source")
        != "macos_keychain_or_owner_secret_manager"
        or unified_key.get("identity_file_persisted") is not False
        or unified_key.get("key_export_allowed") is not False
        or unified_key.get("rotation_requires_new_key_id") is not True
        or "public_recipient" in unified_key
        or "recipient_fingerprint" in unified_key
    ):
        raise PrivateBackupPolicyError("unified_key_policy_invalid")
    try:
        validate_public_encrypted_backup_policy(public_policy, require_ready=True)
    except BackupPolicyError as exc:
        raise PrivateBackupPolicyError("referenced_public_key_policy_invalid") from exc
    public_key = mapping(public_policy.get("unified_key"), "referenced_public_key")
    if unified_key.get("key_id") != public_key.get("key_id"):
        raise PrivateBackupPolicyError("unified_key_policy_invalid")
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
        raise PrivateBackupPolicyError("manifest_policy_invalid")
    if (
        automation.get("enabled") is not True
        or automation.get("schedule_allowed") is not True
        or any(
            automation.get(key) is not False
            for key in (
                "automatic_retry_allowed",
                "automatic_follow_up_task_allowed",
                "shared_cwd_write_allowed",
                "local_script_creation_allowed",
                "local_persistent_state_allowed",
            )
        )
        or automation.get("system_temporary_directory_only") is not True
        or automation.get("release_creation_requires_all_preflight") is not True
        or automation.get("private_identity_unavailable_action") != "ESCALATE"
        or automation.get("source_snapshot_unstable_action") != "STOP"
        or automation.get("post_upload_remote_hash_mismatch_action") != "STOP"
        or automation.get("required_preflight") != EXPECTED_PREFLIGHT
    ):
        raise PrivateBackupPolicyError("automation_policy_invalid")
    if require_ready and policy.get("status") != "READY":
        raise PrivateBackupPolicyError("backup_policy_not_ready")
    return {
        "status": "PASS",
        "policy_status": "READY",
        "ready_for_upload": True,
        "key_id": unified_key["key_id"],
        "release_repository": release["repository"],
        "release_transport": release["transport"],
        "workspace_isolation": "system_temporary_directory_only",
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--public-policy", type=Path, default=DEFAULT_PUBLIC_POLICY)
    parser.add_argument("--require-ready", action="store_true")
    return parser.parse_args(argv)


def _policy_path(database_dir: Path, candidate: Path) -> Path:
    return candidate if candidate.is_absolute() else database_dir / candidate


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.expanduser().resolve()
    try:
        policy = json.loads(_policy_path(database_dir, args.policy).read_text(encoding="utf-8"))
        public_policy = json.loads(
            _policy_path(database_dir, args.public_policy).read_text(encoding="utf-8")
        )
        result = validate_policy(policy, public_policy, require_ready=args.require_ready)
    except (OSError, json.JSONDecodeError, PrivateBackupPolicyError, BackupPolicyError) as exc:
        result = {"status": "FAIL", "error": str(exc)}
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
