"""Metadata-only discovery for approved local Codex source files."""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import os
import stat
from collections import Counter
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from .credential_exclusion import (
    CREDENTIAL_CONTRACT_PATH,
    CredentialExclusionError,
    forbidden_public_raw_path_match,
    load_credential_exclusion_contract,
)
from .source_registry import (
    CODEX_DISCOVERY_CONTRACT_PATH,
    REGISTRY_PATH,
    SourceRegistryError,
    load_source_registry,
    sync_source_map,
)


SCHEMA_VERSION = "memory_atlas.codex_source_discovery.v1_2_1_s07_p1_t1"
TASK_ID = "S07-P1-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P1-T1"
MAX_CONTRACT_BYTES = 128 * 1024
SERIALIZED_ROOT = "[CODEX_HOME]"

EXPECTED_DISCOVERY = {
    "strategy": "source_registry_ordered_candidates",
    "explicit_candidate_failure": "fail_closed",
    "default_missing_result": "not_found",
    "root_symlink_policy": "reject",
    "eligible_path_symlink_policy": "reject",
    "serialized_root": SERIALIZED_ROOT,
}
EXPECTED_ELIGIBLE_SOURCES = [
    {
        "source_kind": "session_index",
        "path_kind": "file",
        "paths": ["session_index.jsonl"],
        "suffixes": [],
        "recursive": False,
    },
    {
        "source_kind": "active_sessions",
        "path_kind": "tree",
        "paths": ["sessions"],
        "suffixes": [".jsonl"],
        "recursive": True,
    },
    {
        "source_kind": "archived_sessions",
        "path_kind": "tree",
        "paths": ["archived_sessions"],
        "suffixes": [".jsonl"],
        "recursive": True,
    },
    {
        "source_kind": "history",
        "path_kind": "file",
        "paths": ["history.jsonl", "transcription-history.jsonl"],
        "suffixes": [],
        "recursive": False,
    },
    {
        "source_kind": "jsonl_logs",
        "path_kind": "tree",
        "paths": ["log", "logs"],
        "suffixes": [".jsonl"],
        "recursive": True,
    },
    {
        "source_kind": "sqlite_logs",
        "path_kind": "file",
        "paths": ["logs_2.sqlite", "sqlite/logs_2.sqlite"],
        "suffixes": [],
        "recursive": False,
    },
]
EXPECTED_CREDENTIAL_EXCLUSIONS = {
    "policy": "credentials_not_transcript",
    "allowlist_only": True,
    "blocked_name_patterns": [
        ".env",
        ".env.*",
        ".netrc",
        ".npmrc",
        ".pypirc",
        "auth.json",
        "config.toml",
        "config.toml.*",
        "installation_id",
        "cookies",
        "cookies.*",
        "login data",
        "login data.*",
        "web data",
        "web data.*",
        "credentials",
        "credentials.*",
        "id_rsa",
        "id_ed25519",
        "*.pem",
        "*.key",
        "*.p12",
        "*.pfx",
    ],
    "blocked_path_segments": ["private_keys", "mcp-oauth-locks", "browser"],
    "source_content_read": False,
    "credential_value_echo": False,
}
EXPECTED_SAFETY = {
    "metadata_only": True,
    "source_content_read": False,
    "source_mutation": False,
    "network_access": False,
    "remote_git_write": False,
    "local_absolute_path_in_output": False,
}
EXPECTED_PHASE_BOUNDARY = {
    "does_not_archive_raw": True,
    "does_not_write_sync_state": True,
    "does_not_build_derived": True,
    "does_not_commit_or_push": True,
    "next_task": "S07-P1-T2",
}
EXPECTED_REGISTRY_CANDIDATES = [
    {"kind": "operator_argument", "value": "--codex-home"},
    {
        "kind": "environment_variable",
        "value": "MEMORY_ATLAS_CODEX_HOME",
        "target_argument": "--codex-home",
    },
    {
        "kind": "environment_variable",
        "value": "CODEX_HOME",
        "target_argument": "--codex-home",
    },
    {"kind": "home_relative", "value": ".codex", "target_argument": "--codex-home"},
]
EXPECTED_REGISTRY_RAW_PATHS = [
    "session_index.jsonl",
    "sessions/**/*.jsonl",
    "archived_sessions/**/*.jsonl",
    "history.jsonl",
    "transcription-history.jsonl",
    "log/**/*.jsonl",
    "logs/**/*.jsonl",
    "logs_2.sqlite",
    "sqlite/logs_2.sqlite",
]


class CodexSourceDiscoveryError(ValueError):
    """Raised with a path-free reason code when discovery cannot be trusted."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class CodexRootSelection:
    path: Path
    candidate_kind: str
    candidate_name: str


@dataclass(frozen=True)
class CodexSourceFile:
    source_kind: str
    relative_path: str
    path: Path
    device: int
    inode: int
    mode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True)
class CodexSourceInventory:
    root: CodexRootSelection
    files: tuple[CodexSourceFile, ...]
    components: tuple[dict[str, Any], ...]
    credential_rule_counts: tuple[tuple[str, int], ...]


def _load_json_regular_file(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CodexSourceDiscoveryError("discovery_contract_unreadable") from exc
    try:
        try:
            metadata = os.fstat(descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise CodexSourceDiscoveryError("discovery_contract_not_regular")
            if metadata.st_size > MAX_CONTRACT_BYTES:
                raise CodexSourceDiscoveryError("discovery_contract_too_large")
            payload = os.read(descriptor, MAX_CONTRACT_BYTES + 1)
        except OSError as exc:
            raise CodexSourceDiscoveryError("discovery_contract_unreadable") from exc
    finally:
        os.close(descriptor)
    try:
        loaded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSourceDiscoveryError("discovery_contract_invalid_json") from exc
    if not isinstance(loaded, dict):
        raise CodexSourceDiscoveryError("discovery_contract_not_object")
    return loaded


def _safe_relative_path(value: object) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CodexSourceDiscoveryError("discovery_contract_path_invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or value.startswith("//") or ".." in path.parts or "." in path.parts:
        raise CodexSourceDiscoveryError("discovery_contract_path_invalid")
    return value


def validate_codex_source_discovery_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CodexSourceDiscoveryError("discovery_contract_not_object")
    expected_keys = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "source_registry_ref",
        "credential_exclusion_ref",
        "discovery",
        "eligible_sources",
        "credential_exclusions",
        "safety",
        "phase_boundary",
    }
    if set(payload) != expected_keys:
        raise CodexSourceDiscoveryError("discovery_contract_keys_mismatch")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != "codex"
    ):
        raise CodexSourceDiscoveryError("discovery_contract_identity_mismatch")
    if _safe_relative_path(payload.get("source_registry_ref")) != REGISTRY_PATH.as_posix():
        raise CodexSourceDiscoveryError("discovery_contract_registry_ref_mismatch")
    if _safe_relative_path(payload.get("credential_exclusion_ref")) != CREDENTIAL_CONTRACT_PATH.as_posix():
        raise CodexSourceDiscoveryError("discovery_contract_credential_ref_mismatch")
    if payload.get("discovery") != EXPECTED_DISCOVERY:
        raise CodexSourceDiscoveryError("discovery_contract_strategy_mismatch")
    if payload.get("eligible_sources") != EXPECTED_ELIGIBLE_SOURCES:
        raise CodexSourceDiscoveryError("discovery_contract_allowlist_mismatch")
    if payload.get("credential_exclusions") != EXPECTED_CREDENTIAL_EXCLUSIONS:
        raise CodexSourceDiscoveryError("discovery_contract_exclusions_mismatch")
    if payload.get("safety") != EXPECTED_SAFETY:
        raise CodexSourceDiscoveryError("discovery_contract_safety_mismatch")
    if payload.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY:
        raise CodexSourceDiscoveryError("discovery_contract_phase_boundary_mismatch")
    return payload


def load_codex_source_discovery_contract(
    database_dir: Path,
    path: Path | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    target = path if path is not None else database_dir / CODEX_DISCOVERY_CONTRACT_PATH
    contract = validate_codex_source_discovery_contract(_load_json_regular_file(target))
    try:
        load_credential_exclusion_contract(
            database_dir,
            database_dir / str(contract["credential_exclusion_ref"]),
        )
    except CredentialExclusionError as exc:
        raise CodexSourceDiscoveryError("credential_exclusion_contract_invalid") from exc
    return contract


def _registered_codex_source(database_dir: Path) -> dict[str, Any]:
    try:
        source = sync_source_map(load_source_registry(database_dir))["codex"]
    except (KeyError, SourceRegistryError) as exc:
        raise CodexSourceDiscoveryError("source_registry_invalid") from exc
    discovery = source.get("discovery")
    if not isinstance(discovery, dict):
        raise CodexSourceDiscoveryError("source_registry_discovery_invalid")
    if discovery.get("contract_ref") != CODEX_DISCOVERY_CONTRACT_PATH.as_posix():
        raise CodexSourceDiscoveryError("source_registry_discovery_ref_mismatch")
    if discovery.get("candidates") != EXPECTED_REGISTRY_CANDIDATES:
        raise CodexSourceDiscoveryError("source_registry_candidate_order_mismatch")
    if source.get("raw_paths") != EXPECTED_REGISTRY_RAW_PATHS:
        raise CodexSourceDiscoveryError("source_registry_raw_paths_mismatch")
    return source


def _expand_home(value: str, home: Path) -> Path:
    if value == "~":
        return home
    if value.startswith("~/"):
        return home / value[2:]
    if value.startswith("~"):
        raise CodexSourceDiscoveryError("codex_home_user_expansion_unsupported")
    return Path(value)


def _validate_selected_root(path: Path, *, explicit: bool) -> Path | None:
    if not path.is_absolute():
        raise CodexSourceDiscoveryError("codex_home_must_be_absolute")
    try:
        metadata = path.lstat()
    except FileNotFoundError:
        if explicit:
            raise CodexSourceDiscoveryError("configured_codex_home_missing")
        return None
    except (OSError, ValueError) as exc:
        raise CodexSourceDiscoveryError("codex_home_stat_failed") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise CodexSourceDiscoveryError("codex_home_symlink_rejected")
    if not stat.S_ISDIR(metadata.st_mode):
        raise CodexSourceDiscoveryError("codex_home_not_directory")
    try:
        return path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise CodexSourceDiscoveryError("codex_home_resolve_failed") from exc


def resolve_codex_home(
    registered_source: dict[str, Any],
    *,
    operator_codex_home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> CodexRootSelection | None:
    environment = os.environ if environ is None else environ
    resolved_home = Path.home() if home is None else home
    if not resolved_home.is_absolute():
        raise CodexSourceDiscoveryError("home_must_be_absolute")

    for candidate in registered_source["discovery"]["candidates"]:
        kind = str(candidate["kind"])
        name = str(candidate["value"])
        explicit = kind in {"operator_argument", "environment_variable"}
        if kind == "operator_argument":
            if operator_codex_home is None:
                continue
            path = _expand_home(str(operator_codex_home), resolved_home)
        elif kind == "environment_variable":
            value = str(environment.get(name, "")).strip()
            if not value:
                continue
            path = _expand_home(value, resolved_home)
        elif kind == "home_relative":
            path = resolved_home / _safe_relative_path(name)
            explicit = False
        else:  # pragma: no cover - source registry validation owns the kinds.
            raise CodexSourceDiscoveryError("source_registry_candidate_kind_unsupported")
        selected = _validate_selected_root(path, explicit=explicit)
        if selected is not None:
            return CodexRootSelection(selected, kind, name)
    return None


def _credential_rule(
    relative: PurePosixPath,
    contract: dict[str, Any],
    credential_contract: dict[str, Any],
) -> str | None:
    exclusions = contract["credential_exclusions"]
    lowered_parts = [part.casefold() for part in relative.parts]
    blocked_segments = {str(value).casefold() for value in exclusions["blocked_path_segments"]}
    for part in lowered_parts:
        if part in blocked_segments:
            return f"segment:{part}"
    name = relative.name.casefold()
    for pattern in exclusions["blocked_name_patterns"]:
        if fnmatch.fnmatchcase(name, str(pattern).casefold()):
            return f"name:{pattern}"
    canonical_match = forbidden_public_raw_path_match(relative.as_posix(), credential_contract)
    if canonical_match:
        return f"credential_contract:{canonical_match}"
    return None


def _lstat_below_root(root: Path, relative: PurePosixPath) -> os.stat_result | None:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            return None
        except OSError as exc:
            raise CodexSourceDiscoveryError("eligible_source_stat_failed") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise CodexSourceDiscoveryError("eligible_source_symlink_rejected")
    return metadata


def _source_file(source_kind: str, root: Path, relative: PurePosixPath, metadata: os.stat_result) -> CodexSourceFile:
    if not stat.S_ISREG(metadata.st_mode):
        raise CodexSourceDiscoveryError("eligible_source_not_regular")
    return CodexSourceFile(
        source_kind=source_kind,
        relative_path=relative.as_posix(),
        path=root / relative,
        device=metadata.st_dev,
        inode=metadata.st_ino,
        mode=metadata.st_mode,
        size_bytes=metadata.st_size,
        mtime_ns=metadata.st_mtime_ns,
        ctime_ns=metadata.st_ctime_ns,
    )


def _scan_tree(
    root: Path,
    relative_root: PurePosixPath,
    source_kind: str,
    suffixes: tuple[str, ...],
    recursive: bool,
    contract: dict[str, Any],
    credential_contract: dict[str, Any],
    rule_counts: Counter[str],
) -> list[CodexSourceFile]:
    records: list[CodexSourceFile] = []

    def visit(relative_directory: PurePosixPath) -> None:
        directory = root / relative_directory
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: entry.name)
        except OSError as exc:
            raise CodexSourceDiscoveryError("eligible_tree_scan_failed") from exc
        for entry in entries:
            relative = relative_directory / entry.name
            rule = _credential_rule(relative, contract, credential_contract)
            if rule is not None:
                rule_counts[rule] += 1
                continue
            try:
                if entry.is_symlink():
                    raise CodexSourceDiscoveryError("eligible_source_symlink_rejected")
                if entry.is_dir(follow_symlinks=False):
                    if recursive:
                        visit(relative)
                    continue
                if not entry.is_file(follow_symlinks=False):
                    continue
                if suffixes and Path(entry.name).suffix.casefold() not in suffixes:
                    continue
                metadata = entry.stat(follow_symlinks=False)
            except FileNotFoundError as exc:
                raise CodexSourceDiscoveryError("source_changed_during_discovery") from exc
            except OSError as exc:
                raise CodexSourceDiscoveryError("eligible_source_stat_failed") from exc
            records.append(_source_file(source_kind, root, relative, metadata))

    visit(relative_root)
    return records


def discover_codex_sources(
    root: CodexRootSelection,
    contract: dict[str, Any],
    credential_contract: dict[str, Any],
) -> CodexSourceInventory:
    files: list[CodexSourceFile] = []
    components: list[dict[str, Any]] = []
    rule_counts: Counter[str] = Counter()

    try:
        root_entries = sorted(os.scandir(root.path), key=lambda entry: entry.name)
    except OSError as exc:
        raise CodexSourceDiscoveryError("codex_home_scan_failed") from exc
    for entry in root_entries:
        rule = _credential_rule(PurePosixPath(entry.name), contract, credential_contract)
        if rule is not None:
            rule_counts[rule] += 1

    for source_spec in contract["eligible_sources"]:
        source_kind = str(source_spec["source_kind"])
        path_kind = str(source_spec["path_kind"])
        suffixes = tuple(str(value).casefold() for value in source_spec["suffixes"])
        component_files: list[CodexSourceFile] = []
        existing_path_count = 0
        for configured_path in source_spec["paths"]:
            relative = PurePosixPath(_safe_relative_path(configured_path))
            metadata = _lstat_below_root(root.path, relative)
            if metadata is None:
                continue
            existing_path_count += 1
            rule = _credential_rule(relative, contract, credential_contract)
            if rule is not None:
                rule_counts[rule] += 1
                continue
            if path_kind == "file":
                component_files.append(_source_file(source_kind, root.path, relative, metadata))
            elif path_kind == "tree":
                if not stat.S_ISDIR(metadata.st_mode):
                    raise CodexSourceDiscoveryError("eligible_tree_not_directory")
                component_files.extend(
                    _scan_tree(
                        root.path,
                        relative,
                        source_kind,
                        suffixes,
                        bool(source_spec["recursive"]),
                        contract,
                        credential_contract,
                        rule_counts,
                    )
                )
            else:  # pragma: no cover - exact contract validation owns this value.
                raise CodexSourceDiscoveryError("eligible_path_kind_unsupported")
        component_files.sort(key=lambda item: item.relative_path)
        files.extend(component_files)
        components.append(
            {
                "source_kind": source_kind,
                "configured_path_count": len(source_spec["paths"]),
                "existing_path_count": existing_path_count,
                "eligible_file_count": len(component_files),
                "eligible_total_bytes": sum(item.size_bytes for item in component_files),
            }
        )

    files.sort(key=lambda item: (item.source_kind, item.relative_path))
    identities: dict[tuple[int, int], str] = {}
    for item in files:
        identity = (item.device, item.inode)
        if identity in identities and identities[identity] != item.relative_path:
            raise CodexSourceDiscoveryError("duplicate_source_identity")
        identities[identity] = item.relative_path
    return CodexSourceInventory(
        root=root,
        files=tuple(files),
        components=tuple(components),
        credential_rule_counts=tuple(sorted(rule_counts.items())),
    )


def _metadata_digest(files: tuple[CodexSourceFile, ...]) -> str:
    digest = hashlib.sha256()
    for item in files:
        row = (
            item.source_kind,
            item.relative_path,
            str(item.device),
            str(item.inode),
            str(item.mode),
            str(item.size_bytes),
            str(item.mtime_ns),
            str(item.ctime_ns),
        )
        digest.update("\0".join(row).encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def build_codex_source_discovery(
    database_dir: Path,
    *,
    operator_codex_home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    contract = load_codex_source_discovery_contract(database_dir)
    registered_source = _registered_codex_source(database_dir)
    root = resolve_codex_home(
        registered_source,
        operator_codex_home=operator_codex_home,
        environ=environ,
        home=home,
    )
    if root is None:
        raise CodexSourceDiscoveryError("codex_home_not_found")
    credential_contract = load_credential_exclusion_contract(database_dir)
    inventory = discover_codex_sources(root, contract, credential_contract)
    if not inventory.files:
        raise CodexSourceDiscoveryError("eligible_codex_sources_not_found")
    rule_counts = [
        {"rule_id": rule_id, "match_count": count}
        for rule_id, count in inventory.credential_rule_counts
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": "PASS",
        "check": "codex-source-discovery",
        "source_id": "codex",
        "source_root": SERIALIZED_ROOT,
        "root_candidate": {
            "kind": inventory.root.candidate_kind,
            "name": inventory.root.candidate_name,
        },
        "eligible_source_kind_count": sum(
            int(component["eligible_file_count"] > 0) for component in inventory.components
        ),
        "eligible_file_count": len(inventory.files),
        "eligible_total_bytes": sum(item.size_bytes for item in inventory.files),
        "source_metadata_sha256": _metadata_digest(inventory.files),
        "components": list(inventory.components),
        "credential_exclusions": {
            "policy": contract["credential_exclusions"]["policy"],
            "allowlist_only": True,
            "configured_name_rule_count": len(contract["credential_exclusions"]["blocked_name_patterns"]),
            "configured_segment_rule_count": len(contract["credential_exclusions"]["blocked_path_segments"]),
            "existing_excluded_entry_count": sum(row["match_count"] for row in rule_counts),
            "matched_rules": rule_counts,
            "credential_value_echo": False,
        },
        "safety": {
            **contract["safety"],
            "writes_files": False,
        },
        "phase_boundary": contract["phase_boundary"],
    }


def run_codex_source_discovery_audit(args: argparse.Namespace) -> int:
    try:
        result = build_codex_source_discovery(
            args.database_dir,
            operator_codex_home=getattr(args, "codex_home", None),
        )
    except (CodexSourceDiscoveryError, CredentialExclusionError, SourceRegistryError) as exc:
        reason = exc.code if isinstance(exc, CodexSourceDiscoveryError) else "discovery_dependency_invalid"
        result = {
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "status": "FAIL_CLOSED",
            "check": "codex-source-discovery",
            "source_id": "codex",
            "source_root": SERIALIZED_ROOT,
            "reason": reason,
            "safety": {**EXPECTED_SAFETY, "writes_files": False},
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = (
    "ACCEPTANCE_ID",
    "CODEX_DISCOVERY_CONTRACT_PATH",
    "CodexRootSelection",
    "CodexSourceDiscoveryError",
    "CodexSourceFile",
    "CodexSourceInventory",
    "EXPECTED_REGISTRY_CANDIDATES",
    "EXPECTED_REGISTRY_RAW_PATHS",
    "SCHEMA_VERSION",
    "TASK_ID",
    "build_codex_source_discovery",
    "discover_codex_sources",
    "load_codex_source_discovery_contract",
    "resolve_codex_home",
    "run_codex_source_discovery_audit",
    "validate_codex_source_discovery_contract",
)
