"""S06-P1-T3 credential exclusion contract and public-raw path guard."""

from __future__ import annotations

import json
from fnmatch import fnmatchcase
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


CREDENTIAL_CONTRACT_PATH = Path("config/data_sources/credential_exclusion.json")
CREDENTIAL_SCHEMA_VERSION = "memory_atlas.credential_exclusion.v1_2_1_s06_p1_t3"
TASK_ID = "S06-P1-T3"
POLICY_ID = "credentials_not_transcript"
SOURCE_REGISTRY_REF = "config/data_sources/source_registry.json"
BLOCKED_ACCOUNT_CONTROL_CATEGORIES = (
    "api_keys",
    "cookies",
    "session_tokens",
    "passwords",
    "private_keys",
    "oauth_tokens",
    "browser_credential_store",
)
ALLOWED_NON_CREDENTIAL_CONTENT = (
    "email_addresses",
    "phone_numbers",
    "personal_and_business_transcript",
    "credential_discussion_without_secret_values",
    "safe_placeholder_values",
)
PUBLIC_RAW_FORBIDDEN_PATH_PATTERNS = (
    ".env",
    ".env.*",
    ".netrc",
    ".npmrc",
    ".pypirc",
    "cookies",
    "cookies.*",
    "login data",
    "login data.*",
    "web data",
    "web data.*",
    "keychain",
    "keychain.*",
    "credentials",
    "credentials.*",
    "id_rsa",
    "id_ed25519",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
)
PUBLIC_RAW_POLICY = {
    "plaintext_transcript_allowed": True,
    "ordinary_transcript_blocked": False,
    "broad_privacy_redaction": False,
    "allowed_non_credential_content": list(ALLOWED_NON_CREDENTIAL_CONTENT),
    "repository_portability_boundary": {
        "local_absolute_paths_allowed": False,
        "treatment": "replace_with_[REDACTED_LOCAL_PATH]",
        "credential_category": False,
    },
}
ENFORCEMENT = {
    "source_bytes_mutated": False,
    "credential_value_echo": False,
    "prewrite_actions": ["fail_closed", "replace_exact_credential_match"],
    "replacement_marker": "[REDACTED_CREDENTIAL]",
    "existing_public_raw_audit": "fail_closed",
    "staged_diff_audit": "fail_closed",
}
_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "policy_id",
    "source_registry_ref",
    "public_raw_policy",
    "blocked_account_control_categories",
    "public_raw_forbidden_path_patterns",
    "enforcement",
}


class CredentialExclusionError(ValueError):
    """Raised when the account-control exclusion contract cannot be trusted."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise CredentialExclusionError(f"{field} must be an object")
    return value


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise CredentialExclusionError(f"{field} must be a canonical repository-relative path")
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or value.startswith("//")
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise CredentialExclusionError(f"{field} must be a safe repository-relative path")
    return value


def validate_credential_exclusion_contract(payload: Any) -> dict[str, Any]:
    contract = _mapping(payload, "credential_exclusion")
    if set(contract) != _CONTRACT_KEYS:
        raise CredentialExclusionError("credential_exclusion keys do not match the canonical contract")
    if contract.get("schema_version") != CREDENTIAL_SCHEMA_VERSION or contract.get("task_id") != TASK_ID:
        raise CredentialExclusionError("credential_exclusion identity is unsupported")
    if contract.get("policy_id") != POLICY_ID:
        raise CredentialExclusionError("credential_exclusion policy_id must be credentials_not_transcript")
    if _safe_relative_path(contract.get("source_registry_ref"), "source_registry_ref") != SOURCE_REGISTRY_REF:
        raise CredentialExclusionError("source_registry_ref must use the canonical registry")
    if _mapping(contract.get("public_raw_policy"), "public_raw_policy") != PUBLIC_RAW_POLICY:
        raise CredentialExclusionError("public_raw_policy must allow ordinary plaintext transcript without broad redaction")
    if contract.get("blocked_account_control_categories") != list(BLOCKED_ACCOUNT_CONTROL_CATEGORIES):
        raise CredentialExclusionError("blocked_account_control_categories drifted from the account-control boundary")
    if contract.get("public_raw_forbidden_path_patterns") != list(PUBLIC_RAW_FORBIDDEN_PATH_PATTERNS):
        raise CredentialExclusionError("public_raw_forbidden_path_patterns drifted from the account-control boundary")
    if _mapping(contract.get("enforcement"), "enforcement") != ENFORCEMENT:
        raise CredentialExclusionError("credential enforcement actions are unsupported")
    return contract


def load_credential_exclusion_contract(database_dir: Path, path: Path | None = None) -> dict[str, Any]:
    target = path or database_dir.resolve() / CREDENTIAL_CONTRACT_PATH
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CredentialExclusionError("cannot read canonical credential exclusion contract") from exc
    return validate_credential_exclusion_contract(payload)


def forbidden_public_raw_path_match(
    relative_path: Path | PurePosixPath | str,
    contract: dict[str, Any],
) -> str | None:
    normalized = str(relative_path).replace("\\", "/")
    path = PurePosixPath(normalized)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CredentialExclusionError("public-raw path must be safe and relative")
    patterns = contract["public_raw_forbidden_path_patterns"]
    for part in path.parts:
        folded = part.casefold()
        for pattern in patterns:
            if fnmatchcase(folded, str(pattern).casefold()):
                return str(pattern)
    return None


__all__ = (
    "ALLOWED_NON_CREDENTIAL_CONTENT",
    "BLOCKED_ACCOUNT_CONTROL_CATEGORIES",
    "CREDENTIAL_CONTRACT_PATH",
    "CREDENTIAL_SCHEMA_VERSION",
    "CredentialExclusionError",
    "ENFORCEMENT",
    "POLICY_ID",
    "PUBLIC_RAW_FORBIDDEN_PATH_PATTERNS",
    "PUBLIC_RAW_POLICY",
    "SOURCE_REGISTRY_REF",
    "TASK_ID",
    "forbidden_public_raw_path_match",
    "load_credential_exclusion_contract",
    "validate_credential_exclusion_contract",
)
