"""Append-only, recoverable public Codex raw archive for S07-P1-T2."""

from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import os
import re
import shutil
import sqlite3
import stat as stat_module
import tarfile
import tempfile
import time
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, Iterator, Mapping

from privacy_guard import (
    LOCAL_ABSOLUTE_PATH_RE,
    credential_exclusion_hits,
)
from public_raw_sanitizer import sanitize_public_text, sanitize_public_value
from raw_archive_manifest import generate_raw_manifest, preflight_raw_ledger

from .archive_chunking import MAX_PART_BYTES
from .codex_source_discovery import (
    CodexRootSelection,
    CodexSourceDiscoveryError,
    CodexSourceFile,
    CodexSourceInventory,
    discover_codex_sources,
    load_codex_source_discovery_contract,
    resolve_codex_home,
)
from .credential_exclusion import (
    CredentialExclusionError,
    load_credential_exclusion_contract,
)
from .raw_ledger import (
    SOURCE_STAT_FIELDS,
    RawLedgerError,
    SourceStat,
    capture_source_stat,
    guarded_sha256_file,
    source_stat_guard,
)
from .source_registry import (
    SourceRegistryError,
    load_source_registry,
    sync_source_map,
)


CONTRACT_PATH = Path("config/data_sources/codex_public_raw_archive.json")
SCHEMA_VERSION = "memory_atlas.codex_public_raw_archive.v1_2_1_s07_p1_t2"
SOURCE_MANIFEST_SCHEMA_VERSION = (
    "memory_atlas.codex_public_raw_source_manifest.v1_2_1_s07_p1_t2"
)
ARCHIVE_MANIFEST_SCHEMA_VERSION = (
    "memory_atlas.codex_public_raw_archive_manifest.v1_2_1_s07_p1_t2"
)
PUBLIC_INDEX_SCHEMA_VERSION = (
    "memory_atlas.codex_public_raw_archive_index.v1_2_1_s07_p1_t2"
)
RESULT_SCHEMA_VERSION = "memory_atlas.codex_public_raw_archive_result.v1_2_1_s07_p1_t2"
TASK_ID = "S07-P1-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P1-T2"
SOURCE_ID = "codex"
ARCHIVE_ROOT = Path("data/raw_archives/codex")
PUBLIC_INDEX_ROOT = Path("data/public_raw/codex")
RAW_MANIFEST_ROOT = Path("机器治理/证据与日志/raw_archive_manifests")
PARTS_DIRECTORY = "parts"
MANIFEST_FILENAME = "manifest.json"
README_FILENAME = "README.md"
RESTORE_FILENAME = "restore.sh"
PACKAGE_MEMBER_ROOT = "codex"
SOURCE_MANIFEST_MEMBER = "codex/_memory_atlas/source_manifest.json"
PACKAGE_FORMAT = "tar_gzip"
GZIP_COMPRESSLEVEL = 1
GZIP_MTIME = 0
PART_INDEX_WIDTH = 6
INFLIGHT_GRACE_SECONDS = 300
READ_CHUNK_BYTES = 1024 * 1024
MAX_CONTRACT_BYTES = 128 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
SPOOL_BYTES = 8 * 1024 * 1024
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
_WINDOWS_RESERVED_ID_RE = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)

EXPECTED_ARCHIVE = {
    "root": ARCHIVE_ROOT.as_posix(),
    "public_index_root": PUBLIC_INDEX_ROOT.as_posix(),
    "package_format": PACKAGE_FORMAT,
    "package_member_root": PACKAGE_MEMBER_ROOT,
    "gzip_compresslevel": GZIP_COMPRESSLEVEL,
    "gzip_mtime": GZIP_MTIME,
    "max_part_bytes": MAX_PART_BYTES,
    "part_index_width": PART_INDEX_WIDTH,
    "manifest_filename": MANIFEST_FILENAME,
    "readme_filename": README_FILENAME,
    "restore_filename": RESTORE_FILENAME,
}
EXPECTED_PUBLIC_CONTENT = {
    "policy": "recoverable_sanitized_raw_package",
    "jsonl": "canonical_jsonl_preserve_order",
    "sqlite": "schema_and_rows_rebuilt_as_sqlite",
    "credential_values": "replace_with_[REDACTED_CREDENTIAL]",
    "local_absolute_paths": "replace_with_[REDACTED_LOCAL_PATH]",
    "non_text_blob": "replace_with_hash_and_size_marker",
    "ordinary_transcript_allowed": True,
    "source_bytes_mutated": False,
}
EXPECTED_SOURCE_PROOF = {
    "hash_algorithm": "sha256",
    "stat_fields": list(SOURCE_STAT_FIELDS),
    "inventory_before_after_equal": True,
    "hash_before_after_equal": True,
    "initial_quiescence_attempts": 3,
    "initial_quiescence_delay_ms": 250,
    "publish_only_after_source_proof": True,
}
EXPECTED_INFLIGHT_SOURCES = {
    "source_kinds": ["active_sessions"],
    "recent_mtime_grace_seconds": INFLIGHT_GRACE_SECONDS,
    "policy": "defer_from_archive_and_record_in_manifest",
    "hash_stat_claim": False,
    "writes_cursor_or_resume_state": False,
}
EXPECTED_APPEND_ONLY = {
    "explicit_archive_id_required": True,
    "existing_archive_policy": "fail_closed_no_overwrite",
    "manifest_publish_last": True,
    "public_index_append_only": True,
    "public_index_ledger_required": True,
    "exclusive_archive_lock": True,
    "stale_lock_policy": "manual_verify_never_auto_remove",
}
EXPECTED_RESTORE = {
    "ordered_part_hashes_required": True,
    "package_hash_required": True,
    "safe_relative_members_required": True,
    "source_manifest_in_package": SOURCE_MANIFEST_MEMBER,
    "restore_output_no_overwrite": True,
}
EXPECTED_PHASE_BOUNDARY = {
    "does_not_write_cursor": True,
    "does_not_deduplicate_by_content": True,
    "does_not_resume_interrupted_runs": True,
    "does_not_build_derived": True,
    "does_not_commit_or_push": True,
    "next_task": "S07-P1-T3",
}


class CodexPublicRawArchiveError(ValueError):
    """Path-free fail-closed result for the T2 archive connector."""

    def __init__(
        self,
        code: str,
        *,
        writes_files: bool = False,
        archive_may_exist: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.writes_files = writes_files
        self.archive_may_exist = archive_may_exist


@dataclass(frozen=True)
class SourceProof:
    source_kind: str
    relative_path: str
    stat: SourceStat
    sha256: str


def _now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _read_regular_bytes(path: Path, *, max_bytes: int, code: str) -> bytes:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        metadata = os.fstat(descriptor)
        if not stat_module.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            raise CodexPublicRawArchiveError(code)
        chunks: list[bytes] = []
        remaining = metadata.st_size
        while remaining:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                raise CodexPublicRawArchiveError(code)
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise CodexPublicRawArchiveError(code)
        return b"".join(chunks)
    except CodexPublicRawArchiveError:
        raise
    except OSError as exc:
        raise CodexPublicRawArchiveError(code) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _safe_repo_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise CodexPublicRawArchiveError("archive_contract_path_invalid")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or any(part in {"", ".", ".."} for part in posix.parts)
    ):
        raise CodexPublicRawArchiveError("archive_contract_path_invalid")
    return value


def _portable_archive_id(value: Any) -> str:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or not value
        or len(value) > 128
        or not _PORTABLE_ID_RE.fullmatch(value)
        or _WINDOWS_RESERVED_ID_RE.fullmatch(value)
    ):
        raise CodexPublicRawArchiveError("archive_id_invalid")
    return value


def _raw_manifest_run_id(archive_id: str) -> str:
    return f"s07_p1_t2_{archive_id}"


def validate_codex_public_raw_archive_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CodexPublicRawArchiveError("archive_contract_not_object")
    expected_keys = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "source_discovery_ref",
        "credential_exclusion_ref",
        "raw_ledger_ref",
        "archive",
        "public_content",
        "source_proof",
        "inflight_sources",
        "append_only",
        "restore",
        "phase_boundary",
    }
    if set(payload) != expected_keys:
        raise CodexPublicRawArchiveError("archive_contract_keys_mismatch")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != SOURCE_ID
    ):
        raise CodexPublicRawArchiveError("archive_contract_identity_mismatch")
    if _safe_repo_relative(payload.get("source_discovery_ref")) != (
        "config/data_sources/codex_source_discovery.json"
    ):
        raise CodexPublicRawArchiveError("archive_contract_discovery_ref_mismatch")
    if _safe_repo_relative(payload.get("credential_exclusion_ref")) != (
        "config/data_sources/credential_exclusion.json"
    ):
        raise CodexPublicRawArchiveError("archive_contract_credential_ref_mismatch")
    if _safe_repo_relative(payload.get("raw_ledger_ref")) != (
        "config/data_sources/raw_ledger.json"
    ):
        raise CodexPublicRawArchiveError("archive_contract_ledger_ref_mismatch")
    expected_sections = (
        ("archive", EXPECTED_ARCHIVE),
        ("public_content", EXPECTED_PUBLIC_CONTENT),
        ("source_proof", EXPECTED_SOURCE_PROOF),
        ("inflight_sources", EXPECTED_INFLIGHT_SOURCES),
        ("append_only", EXPECTED_APPEND_ONLY),
        ("restore", EXPECTED_RESTORE),
        ("phase_boundary", EXPECTED_PHASE_BOUNDARY),
    )
    for name, expected in expected_sections:
        if payload.get(name) != expected:
            raise CodexPublicRawArchiveError(f"archive_contract_{name}_mismatch")
    return payload


def load_codex_public_raw_archive_contract(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    path = database_dir / CONTRACT_PATH
    try:
        payload = json.loads(
            _read_regular_bytes(
                path,
                max_bytes=MAX_CONTRACT_BYTES,
                code="archive_contract_unreadable",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexPublicRawArchiveError("archive_contract_invalid_json") from exc
    contract = validate_codex_public_raw_archive_contract(payload)
    try:
        load_codex_source_discovery_contract(database_dir)
        load_credential_exclusion_contract(database_dir)
    except (CredentialExclusionError, SourceRegistryError, ValueError) as exc:
        raise CodexPublicRawArchiveError("archive_contract_dependency_invalid") from exc
    return contract


def _registered_codex_source(database_dir: Path) -> dict[str, Any]:
    try:
        return sync_source_map(load_source_registry(database_dir))[SOURCE_ID]
    except (KeyError, SourceRegistryError) as exc:
        raise CodexPublicRawArchiveError("source_registry_invalid") from exc


def _resolve_inventory(
    database_dir: Path,
    *,
    operator_codex_home: Path | None,
    environ: Mapping[str, str] | None,
    home: Path | None,
) -> tuple[dict[str, Any], dict[str, Any], CodexSourceInventory]:
    try:
        discovery_contract = load_codex_source_discovery_contract(database_dir)
        credential_contract = load_credential_exclusion_contract(database_dir)
        root = resolve_codex_home(
            _registered_codex_source(database_dir),
            operator_codex_home=operator_codex_home,
            environ=environ,
            home=home,
        )
        if root is None:
            raise CodexPublicRawArchiveError("codex_home_not_found")
        inventory = discover_codex_sources(root, discovery_contract, credential_contract)
    except CodexPublicRawArchiveError:
        raise
    except (CodexSourceDiscoveryError, CredentialExclusionError, SourceRegistryError) as exc:
        code = exc.code if isinstance(exc, CodexSourceDiscoveryError) else "archive_dependency_invalid"
        raise CodexPublicRawArchiveError(code) from exc
    if not inventory.files:
        raise CodexPublicRawArchiveError("eligible_codex_sources_not_found")
    return discovery_contract, credential_contract, inventory


def _source_stat(item: CodexSourceFile) -> SourceStat:
    return SourceStat(
        device=item.device,
        inode=item.inode,
        mode=item.mode,
        size_bytes=item.size_bytes,
        mtime_ns=item.mtime_ns,
        ctime_ns=item.ctime_ns,
    )


def _filter_inventory(
    inventory: CodexSourceInventory,
    excluded_paths: frozenset[str],
) -> CodexSourceInventory:
    return CodexSourceInventory(
        root=inventory.root,
        files=tuple(
            item for item in inventory.files if item.relative_path not in excluded_paths
        ),
        components=inventory.components,
        credential_rule_counts=inventory.credential_rule_counts,
    )


def _partition_inflight_sources(
    inventory: CodexSourceInventory,
    *,
    observed_at_ns: int | None = None,
) -> tuple[CodexSourceInventory, tuple[dict[str, Any], ...]]:
    now_ns = time.time_ns() if observed_at_ns is None else observed_at_ns
    grace_ns = INFLIGHT_GRACE_SECONDS * 1_000_000_000
    deferred: list[dict[str, Any]] = []
    excluded: set[str] = set()
    for item in inventory.files:
        _safe_public_text(item.relative_path)
        if item.source_kind != "active_sessions":
            continue
        age_ns = now_ns - item.mtime_ns
        if age_ns >= grace_ns:
            continue
        excluded.add(item.relative_path)
        deferred.append(
            {
                "source_kind": item.source_kind,
                "relative_path": item.relative_path,
                "stat": {
                    field: int(getattr(_source_stat(item), field))
                    for field in SOURCE_STAT_FIELDS
                },
                "reason": "inflight_recent_active_session",
                "hash_stat_claim": False,
            }
        )
    selected = _filter_inventory(inventory, frozenset(excluded))
    if not selected.files:
        raise CodexPublicRawArchiveError("stable_codex_sources_not_found")
    original_kinds = {item.source_kind for item in inventory.files}
    selected_kinds = {item.source_kind for item in selected.files}
    missing_kinds = original_kinds - selected_kinds
    if missing_kinds - {"active_sessions"}:
        raise CodexPublicRawArchiveError("stable_source_kind_missing")
    return selected, tuple(deferred)


def _capture_proofs(inventory: CodexSourceInventory) -> tuple[SourceProof, ...]:
    proofs: list[SourceProof] = []
    for item in inventory.files:
        expected = _source_stat(item)
        try:
            if capture_source_stat(item.path) != expected:
                raise CodexPublicRawArchiveError("source_stat_changed")
            fingerprint = guarded_sha256_file(item.path)
            if capture_source_stat(item.path) != expected:
                raise CodexPublicRawArchiveError("source_stat_changed")
        except CodexPublicRawArchiveError:
            raise
        except RawLedgerError as exc:
            code = (
                "source_stat_changed"
                if "source stat changed" in str(exc)
                else "source_hash_unverified"
            )
            raise CodexPublicRawArchiveError(code) from exc
        if (
            int(fingerprint["size_bytes"]) != expected.size_bytes
        ):
            raise CodexPublicRawArchiveError("source_stat_changed")
        proofs.append(
            SourceProof(
                source_kind=item.source_kind,
                relative_path=item.relative_path,
                stat=expected,
                sha256=str(fingerprint["sha256"]),
            )
        )
    return tuple(proofs)


def _capture_quiescent_proofs(
    inventory: CodexSourceInventory,
    discovery_contract: dict[str, Any],
    credential_contract: dict[str, Any],
    deferred_inflight: tuple[dict[str, Any], ...],
) -> tuple[
    CodexSourceInventory,
    tuple[SourceProof, ...],
    tuple[dict[str, Any], ...],
]:
    current = inventory
    current_deferred = deferred_inflight
    for attempt in range(3):
        try:
            return current, _capture_proofs(current), current_deferred
        except CodexPublicRawArchiveError as exc:
            if exc.code != "source_stat_changed" or attempt == 2:
                raise
            time.sleep(0.25)
            rediscovered = discover_codex_sources(
                inventory.root,
                discovery_contract,
                credential_contract,
            )
            current, current_deferred = _partition_inflight_sources(rediscovered)
    raise CodexPublicRawArchiveError("source_stat_changed")


def _proof_payload(proof: SourceProof) -> dict[str, Any]:
    return {
        "source_kind": proof.source_kind,
        "relative_path": proof.relative_path,
        "sha256": proof.sha256,
        "stat": {
            field: int(getattr(proof.stat, field)) for field in SOURCE_STAT_FIELDS
        },
    }


def _proof_digest(proofs: tuple[SourceProof, ...]) -> str:
    digest = hashlib.sha256()
    for proof in proofs:
        digest.update(
            json.dumps(
                _proof_payload(proof),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ).encode("utf-8")
        )
        digest.update(b"\n")
    return digest.hexdigest()


def _compare_proofs(
    before: tuple[SourceProof, ...],
    after: tuple[SourceProof, ...],
) -> None:
    if before != after:
        raise CodexPublicRawArchiveError("source_hash_or_stat_changed")


def _verify_final_inventory_stat(
    inventory: CodexSourceInventory,
    discovery_contract: dict[str, Any],
    credential_contract: dict[str, Any],
    expected: tuple[SourceProof, ...],
    excluded_paths: frozenset[str],
) -> None:
    current = discover_codex_sources(
        inventory.root,
        discovery_contract,
        credential_contract,
    )
    current = _filter_inventory(current, excluded_paths)
    observed = tuple(
        (
            item.source_kind,
            item.relative_path,
            _source_stat(item),
        )
        for item in current.files
    )
    expected_stat = tuple(
        (proof.source_kind, proof.relative_path, proof.stat) for proof in expected
    )
    if observed != expected_stat:
        raise CodexPublicRawArchiveError("source_inventory_changed")


def _safe_public_text(value: str) -> None:
    if credential_exclusion_hits(value, source="codex_public_raw_archive"):
        raise CodexPublicRawArchiveError("sanitized_output_contains_credential")
    if LOCAL_ABSOLUTE_PATH_RE.search(value):
        raise CodexPublicRawArchiveError("sanitized_output_contains_local_path")


def _safe_public_value(value: Any) -> None:
    if isinstance(value, str):
        _safe_public_text(value)
    elif isinstance(value, list):
        for item in value:
            _safe_public_value(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            if isinstance(key, str):
                _safe_public_text(key)
            _safe_public_value(item)


def _merge_counts(target: Counter[str], values: Mapping[str, int]) -> None:
    for key, value in values.items():
        target[str(key)] += int(value)


def _write_and_hash(handle: BinaryIO, digest: Any, payload: bytes) -> None:
    handle.write(payload)
    digest.update(payload)


def _sanitize_jsonl(
    item: CodexSourceFile,
    expected_stat: SourceStat,
    output: BinaryIO,
) -> dict[str, Any]:
    digest = hashlib.sha256()
    counts: Counter[str] = Counter()
    line_count = 0
    invalid_json_count = 0
    try:
        with source_stat_guard(
            item.path,
            expected={item.path.name: expected_stat},
        ):
            with item.path.open("rb") as source:
                for raw_line in source:
                    line_count += 1
                    try:
                        text = raw_line.decode("utf-8", errors="strict")
                    except UnicodeDecodeError as exc:
                        raise CodexPublicRawArchiveError(
                            "eligible_jsonl_not_utf8"
                        ) from exc
                    line_ending = "\n" if text.endswith(("\n", "\r")) else ""
                    body = text.rstrip("\r\n")
                    if not body:
                        payload = line_ending.encode("utf-8")
                        _write_and_hash(output, digest, payload)
                        continue
                    try:
                        value = json.loads(body)
                    except json.JSONDecodeError:
                        invalid_json_count += 1
                        invalid_json = True
                        sanitized, redactions = sanitize_public_text(body)
                        _safe_public_text(sanitized)
                    else:
                        invalid_json = False
                        sanitized, redactions = sanitize_public_value(value)
                        _safe_public_value(sanitized)
                    _merge_counts(counts, redactions)
                    if isinstance(sanitized, str) and invalid_json:
                        serialized = sanitized
                    else:
                        serialized = json.dumps(
                            sanitized,
                            ensure_ascii=False,
                            sort_keys=True,
                            separators=(",", ":"),
                        )
                    payload = (serialized + line_ending).encode("utf-8")
                    _write_and_hash(output, digest, payload)
    except RawLedgerError as exc:
        raise CodexPublicRawArchiveError("source_stat_changed") from exc
    return {
        "archive_sha256": digest.hexdigest(),
        "archive_size_bytes": int(output.tell()),
        "record_count": line_count,
        "invalid_json_count": invalid_json_count,
        "redaction_counts": dict(sorted(counts.items())),
        "transformation": "canonical_jsonl_sanitized",
    }


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _blob_marker(value: bytes) -> bytes:
    return (
        f"[REDACTED_BINARY sha256={hashlib.sha256(value).hexdigest()} "
        f"bytes={len(value)} reason=non_text_binary_not_transcript]"
    ).encode("utf-8")


def _sanitize_sqlite_value(value: Any, counts: Counter[str]) -> Any:
    if isinstance(value, str):
        sanitized, redactions = sanitize_public_text(value)
        _merge_counts(counts, redactions)
        _safe_public_text(sanitized)
        return sanitized
    if isinstance(value, bytes):
        try:
            text = value.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            counts["binary_omission"] += 1
            return _blob_marker(value)
        sanitized, redactions = sanitize_public_text(text)
        _merge_counts(counts, redactions)
        _safe_public_text(sanitized)
        return sanitized.encode("utf-8")
    if value is None or isinstance(value, (int, float)):
        return value
    raise CodexPublicRawArchiveError("sqlite_value_type_unsupported")


def _sqlite_uri(path: Path) -> str:
    return path.as_uri() + "?mode=ro&immutable=1"


def _sqlite_table_columns(connection: sqlite3.Connection, table: str) -> list[tuple[Any, ...]]:
    return list(connection.execute(f"PRAGMA table_xinfo({_quote_identifier(table)})"))


def _rebuild_sqlite(
    item: CodexSourceFile,
    expected_stat: SourceStat,
    output_path: Path,
) -> dict[str, Any]:
    counts: Counter[str] = Counter()
    table_counts: dict[str, int] = {}
    source: sqlite3.Connection | None = None
    target: sqlite3.Connection | None = None
    try:
        with source_stat_guard(
            item.path,
            expected={item.path.name: expected_stat},
        ):
            source = sqlite3.connect(_sqlite_uri(item.path), uri=True, timeout=0)
            source.execute("PRAGMA query_only=ON")
            quick_check = source.execute("PRAGMA quick_check").fetchone()
            if quick_check != ("ok",):
                raise CodexPublicRawArchiveError("sqlite_source_integrity_failed")
            user_version = int(source.execute("PRAGMA user_version").fetchone()[0])
            application_id = int(source.execute("PRAGMA application_id").fetchone()[0])
            objects = list(
                source.execute(
                    "SELECT type, name, tbl_name, sql FROM sqlite_master "
                    "WHERE sql IS NOT NULL AND name NOT LIKE 'sqlite_%' "
                    "ORDER BY CASE type WHEN 'table' THEN 0 WHEN 'index' THEN 1 "
                    "WHEN 'view' THEN 2 WHEN 'trigger' THEN 3 ELSE 4 END, name"
                )
            )
            if not objects:
                raise CodexPublicRawArchiveError("sqlite_source_schema_empty")
            output_path.parent.mkdir(parents=True, exist_ok=True)
            target = sqlite3.connect(output_path)
            target.execute("PRAGMA journal_mode=OFF")
            target.execute("PRAGMA synchronous=OFF")
            target.execute("PRAGMA temp_store=MEMORY")

            for object_type, _name, _table_name, sql in objects:
                if object_type != "table":
                    continue
                sanitized_sql, redactions = sanitize_public_text(str(sql))
                _merge_counts(counts, redactions)
                _safe_public_text(sanitized_sql)
                if sanitized_sql != sql:
                    raise CodexPublicRawArchiveError("sqlite_schema_not_public_safe")
                target.execute(str(sql))

            for object_type, name, _table_name, _sql in objects:
                if object_type != "table":
                    continue
                columns = _sqlite_table_columns(source, str(name))
                writable = [row for row in columns if int(row[6]) == 0]
                column_names = [str(row[1]) for row in writable]
                if not column_names:
                    table_counts[str(name)] = 0
                    continue
                quoted_columns = ", ".join(_quote_identifier(value) for value in column_names)
                primary = [
                    (int(row[5]), str(row[1]))
                    for row in writable
                    if int(row[5]) > 0
                ]
                if primary:
                    order = ", ".join(
                        _quote_identifier(value)
                        for _index, value in sorted(primary)
                    )
                else:
                    order = "rowid"
                select_sql = (
                    f"SELECT {quoted_columns} FROM {_quote_identifier(str(name))} "
                    f"ORDER BY {order}"
                )
                try:
                    cursor = source.execute(select_sql)
                except sqlite3.OperationalError:
                    cursor = source.execute(
                        f"SELECT {quoted_columns} FROM {_quote_identifier(str(name))}"
                    )
                insert_sql = (
                    f"INSERT INTO {_quote_identifier(str(name))} ({quoted_columns}) "
                    f"VALUES ({', '.join('?' for _ in column_names)})"
                )
                row_count = 0
                while True:
                    rows = cursor.fetchmany(512)
                    if not rows:
                        break
                    sanitized_rows = [
                        tuple(_sanitize_sqlite_value(value, counts) for value in row)
                        for row in rows
                    ]
                    target.executemany(insert_sql, sanitized_rows)
                    row_count += len(rows)
                table_counts[str(name)] = row_count

            for object_type, _name, _table_name, sql in objects:
                if object_type == "table":
                    continue
                sanitized_sql, redactions = sanitize_public_text(str(sql))
                _merge_counts(counts, redactions)
                _safe_public_text(sanitized_sql)
                if sanitized_sql != sql:
                    raise CodexPublicRawArchiveError("sqlite_schema_not_public_safe")
                target.execute(str(sql))
            target.execute(f"PRAGMA user_version={user_version}")
            target.execute(f"PRAGMA application_id={application_id}")
            target.commit()
            target.execute("VACUUM")
            target.close()
            target = None
            source.close()
            source = None
    except sqlite3.Error as exc:
        raise CodexPublicRawArchiveError("sqlite_rebuild_failed") from exc
    except RawLedgerError as exc:
        raise CodexPublicRawArchiveError("source_stat_changed") from exc
    finally:
        if target is not None:
            target.close()
        if source is not None:
            source.close()

    verify = sqlite3.connect(_sqlite_uri(output_path), uri=True)
    try:
        if verify.execute("PRAGMA quick_check").fetchone() != ("ok",):
            raise CodexPublicRawArchiveError("sqlite_archive_integrity_failed")
        for table, expected_count in table_counts.items():
            actual = int(
                verify.execute(
                    f"SELECT COUNT(*) FROM {_quote_identifier(table)}"
                ).fetchone()[0]
            )
            if actual != expected_count:
                raise CodexPublicRawArchiveError("sqlite_archive_row_count_mismatch")
    finally:
        verify.close()
    fingerprint = guarded_sha256_file(output_path)
    return {
        "archive_sha256": str(fingerprint["sha256"]),
        "archive_size_bytes": int(fingerprint["size_bytes"]),
        "record_count": sum(table_counts.values()),
        "table_counts": dict(sorted(table_counts.items())),
        "redaction_counts": dict(sorted(counts.items())),
        "transformation": "sqlite_schema_and_rows_rebuilt_sanitized",
    }


class _ChunkedPackageWriter:
    def __init__(self, parts_dir: Path, archive_id: str) -> None:
        self.parts_dir = parts_dir
        self.archive_id = archive_id
        self.package_digest = hashlib.sha256()
        self.package_bytes = 0
        self.parts: list[dict[str, Any]] = []
        self._handle: BinaryIO | None = None
        self._part_digest: Any | None = None
        self._part_bytes = 0
        self._part_name = ""

    def tell(self) -> int:
        return self.package_bytes

    def writable(self) -> bool:
        return True

    def _open_part(self) -> None:
        index = len(self.parts)
        self._part_name = (
            f"{self.archive_id}.tar.gz.part-{index:0{PART_INDEX_WIDTH}d}"
        )
        path = self.parts_dir / self._part_name
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        self._handle = os.fdopen(descriptor, "wb")
        self._part_digest = hashlib.sha256()
        self._part_bytes = 0

    def _close_part(self) -> None:
        if self._handle is None or self._part_digest is None:
            return
        self._handle.flush()
        os.fsync(self._handle.fileno())
        self._handle.close()
        index = len(self.parts)
        self.parts.append(
            {
                "index": index,
                "filename": f"{PARTS_DIRECTORY}/{self._part_name}",
                "byte_size": self._part_bytes,
                "sha256": self._part_digest.hexdigest(),
            }
        )
        self._handle = None
        self._part_digest = None
        self._part_bytes = 0

    def write(self, payload: bytes | bytearray | memoryview) -> int:
        view = memoryview(payload)
        total = len(view)
        cursor = 0
        while cursor < total:
            if self._handle is None:
                self._open_part()
            available = MAX_PART_BYTES - self._part_bytes
            chunk = view[cursor : cursor + available]
            written = self._handle.write(chunk)  # type: ignore[union-attr]
            if written != len(chunk):
                raise CodexPublicRawArchiveError("archive_part_short_write")
            data = chunk[:written]
            self.package_digest.update(data)
            self._part_digest.update(data)  # type: ignore[union-attr]
            self.package_bytes += written
            self._part_bytes += written
            cursor += written
            if self._part_bytes == MAX_PART_BYTES:
                self._close_part()
        return total

    def flush(self) -> None:
        if self._handle is not None:
            self._handle.flush()

    def finish(self) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        self._close_part()
        if not self.parts or self.package_bytes <= 0:
            raise CodexPublicRawArchiveError("archive_package_empty")
        return (
            {
                "filename": f"{self.archive_id}.tar.gz",
                "format": PACKAGE_FORMAT,
                "byte_size": self.package_bytes,
                "sha256": self.package_digest.hexdigest(),
            },
            self.parts,
        )


def _tar_info(name: str, size: int, *, mode: int = 0o600) -> tarfile.TarInfo:
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CodexPublicRawArchiveError("archive_member_path_invalid")
    info = tarfile.TarInfo(name=name)
    info.size = size
    info.mode = mode
    info.mtime = 0
    info.uid = 0
    info.gid = 0
    info.uname = ""
    info.gname = ""
    return info


def _add_bytes_member(
    archive: tarfile.TarFile,
    name: str,
    payload: bytes,
    *,
    mode: int = 0o600,
) -> None:
    with tempfile.SpooledTemporaryFile(max_size=SPOOL_BYTES, mode="w+b") as handle:
        handle.write(payload)
        handle.seek(0)
        archive.addfile(_tar_info(name, len(payload), mode=mode), handle)


def _build_source_manifest(
    archive_id: str,
    before: tuple[SourceProof, ...],
    after: tuple[SourceProof, ...],
    archived_files: list[dict[str, Any]],
    deferred_inflight: tuple[dict[str, Any], ...],
) -> dict[str, Any]:
    deferred_bytes = sum(int(item["stat"]["size_bytes"]) for item in deferred_inflight)
    return {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "content_policy": EXPECTED_PUBLIC_CONTENT,
        "source_proof": {
            "hash_algorithm": "sha256",
            "stat_fields": list(SOURCE_STAT_FIELDS),
            "file_count": len(before),
            "source_total_bytes": sum(proof.stat.size_bytes for proof in before),
            "discovered_file_count": len(before) + len(deferred_inflight),
            "discovered_total_bytes": (
                sum(proof.stat.size_bytes for proof in before) + deferred_bytes
            ),
            "deferred_inflight_file_count": len(deferred_inflight),
            "before_sha256": _proof_digest(before),
            "after_sha256": _proof_digest(after),
            "inventory_equal": before == after,
            "hash_stat_equal": before == after,
            "source_mutation": False,
        },
        "files": archived_files,
        "deferred_inflight_sources": list(deferred_inflight),
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _build_package(
    staging: Path,
    archive_id: str,
    inventory: CodexSourceInventory,
    discovery_contract: dict[str, Any],
    credential_contract: dict[str, Any],
    before: tuple[SourceProof, ...],
    deferred_inflight: tuple[dict[str, Any], ...],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    excluded_paths = frozenset(
        str(item["relative_path"]) for item in deferred_inflight
    )
    proof_by_path = {proof.relative_path: proof for proof in before}
    parts_dir = staging / PARTS_DIRECTORY
    work_dir = staging / ".work"
    parts_dir.mkdir(mode=0o700)
    work_dir.mkdir(mode=0o700)
    writer = _ChunkedPackageWriter(parts_dir, archive_id)
    archived_files: list[dict[str, Any]] = []
    aggregate_redactions: Counter[str] = Counter()
    after: tuple[SourceProof, ...] | None = None
    try:
        with gzip.GzipFile(
            filename="",
            mode="wb",
            compresslevel=GZIP_COMPRESSLEVEL,
            fileobj=writer,
            mtime=GZIP_MTIME,
        ) as compressed:
            with tarfile.open(
                fileobj=compressed,
                mode="w|",
                format=tarfile.PAX_FORMAT,
            ) as archive:
                for index, item in enumerate(inventory.files):
                    proof = proof_by_path[item.relative_path]
                    member_name = f"{PACKAGE_MEMBER_ROOT}/{item.relative_path}"
                    if item.source_kind == "sqlite_logs":
                        sqlite_output = work_dir / f"sqlite-{index:06d}.sqlite"
                        transformed = _rebuild_sqlite(item, proof.stat, sqlite_output)
                        with sqlite_output.open("rb") as handle:
                            archive.addfile(
                                _tar_info(
                                    member_name,
                                    int(transformed["archive_size_bytes"]),
                                ),
                                handle,
                            )
                        sqlite_output.unlink()
                    else:
                        with tempfile.SpooledTemporaryFile(
                            max_size=SPOOL_BYTES,
                            mode="w+b",
                            dir=work_dir,
                        ) as handle:
                            transformed = _sanitize_jsonl(item, proof.stat, handle)
                            handle.seek(0)
                            archive.addfile(
                                _tar_info(
                                    member_name,
                                    int(transformed["archive_size_bytes"]),
                                ),
                                handle,
                            )
                    _merge_counts(
                        aggregate_redactions,
                        transformed.get("redaction_counts", {}),
                    )
                    archived_files.append(
                        {
                            "source_kind": proof.source_kind,
                            "source_relative_path": proof.relative_path,
                            "source_sha256": proof.sha256,
                            "source_size_bytes": proof.stat.size_bytes,
                            "source_stat": {
                                field: int(getattr(proof.stat, field))
                                for field in SOURCE_STAT_FIELDS
                            },
                            "archive_member": member_name,
                            **transformed,
                        }
                    )

                after_inventory = discover_codex_sources(
                    inventory.root,
                    discovery_contract,
                    credential_contract,
                )
                after_inventory = _filter_inventory(after_inventory, excluded_paths)
                after = _capture_proofs(after_inventory)
                _compare_proofs(before, after)
                source_manifest = _build_source_manifest(
                    archive_id,
                    before,
                    after,
                    archived_files,
                    deferred_inflight,
                )
                _add_bytes_member(
                    archive,
                    SOURCE_MANIFEST_MEMBER,
                    _canonical_json_bytes(source_manifest),
                )
                _add_bytes_member(
                    archive,
                    "codex/_memory_atlas/README.md",
                    (
                        "# Codex Public Raw Package\n\n"
                        "This package preserves every S07-P1-T1 eligible Codex source in a "
                        "recoverable public form. Credential values and local absolute paths "
                        "are deterministically replaced; source files are never modified.\n"
                    ).encode("utf-8"),
                    mode=0o644,
                )
        package, parts = writer.finish()
    except Exception:
        if writer._handle is not None:
            writer._handle.close()
        raise
    finally:
        shutil.rmtree(work_dir, ignore_errors=True)
    if after is None:
        raise CodexPublicRawArchiveError("source_post_proof_missing")
    _verify_final_inventory_stat(
        inventory,
        discovery_contract,
        credential_contract,
        after,
        excluded_paths,
    )
    deferred_bytes = sum(int(item["stat"]["size_bytes"]) for item in deferred_inflight)
    package_summary = {
        **package,
        "member_count": len(archived_files) + 2,
        "source_file_count": len(before),
        "source_total_bytes": sum(proof.stat.size_bytes for proof in before),
        "discovered_file_count": len(before) + len(deferred_inflight),
        "discovered_total_bytes": (
            sum(proof.stat.size_bytes for proof in before) + deferred_bytes
        ),
        "deferred_inflight_file_count": len(deferred_inflight),
        "source_before_sha256": _proof_digest(before),
        "source_after_sha256": _proof_digest(after),
        "source_hash_stat_equal": before == after,
        "redaction_counts": dict(sorted(aggregate_redactions.items())),
    }
    return package_summary, parts, source_manifest


def _archive_manifest(
    archive_id: str,
    package: dict[str, Any],
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": ARCHIVE_MANIFEST_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / archive_id).as_posix(),
        "recorded_at_utc": _now_utc(),
        "visibility": "public_github_repository",
        "authorization": {
            "basis": "v1.2.1 TaskPack S07-P1-T2",
            "credential_values_public": False,
            "local_absolute_paths_public": False,
        },
        "content_policy": EXPECTED_PUBLIC_CONTENT,
        "source_proof": {
            "file_count": package["source_file_count"],
            "source_total_bytes": package["source_total_bytes"],
            "discovered_file_count": package["discovered_file_count"],
            "discovered_total_bytes": package["discovered_total_bytes"],
            "deferred_inflight_file_count": package[
                "deferred_inflight_file_count"
            ],
            "before_sha256": package["source_before_sha256"],
            "after_sha256": package["source_after_sha256"],
            "hash_stat_equal": package["source_hash_stat_equal"],
            "source_mutation": False,
        },
        "package": {
            key: package[key]
            for key in (
                "filename",
                "format",
                "byte_size",
                "sha256",
                "member_count",
            )
        },
        "split": {
            "method": "fixed_bytes",
            "max_part_bytes": MAX_PART_BYTES,
            "part_index_width": PART_INDEX_WIDTH,
            "part_count": len(parts),
        },
        "parts": parts,
        "redaction_counts": package["redaction_counts"],
        "restore": {
            "script": RESTORE_FILENAME,
            "output_no_overwrite": True,
            "source_manifest_member": SOURCE_MANIFEST_MEMBER,
        },
        "public_index": {
            "root": PUBLIC_INDEX_ROOT.as_posix(),
            "append_only": True,
            "raw_ledger_required": True,
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _restore_script(
    archive_id: str,
    package_sha256: str,
    member_count: int,
) -> bytes:
    return f"""#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: ./restore.sh OUTPUT_DIRECTORY" >&2
  exit 2
fi

script_dir="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
output="$1"
if [[ -e "$output" || -L "$output" ]]; then
  echo "restore output already exists" >&2
  exit 3
fi
staging="${{output}}.restore-{archive_id}-$$"
if [[ -e "$staging" || -L "$staging" ]]; then
  echo "restore staging path already exists" >&2
  exit 3
fi
mkdir "$staging"
cleanup() {{ rm -rf "$staging"; }}
trap cleanup EXIT
package="$staging/.{archive_id}.tar.gz"
cat "$script_dir"/parts/{archive_id}.tar.gz.part-* > "$package"
actual="$(shasum -a 256 "$package" | awk '{{print $1}}')"
if [[ "$actual" != "{package_sha256}" ]]; then
  echo "restored package SHA-256 mismatch" >&2
  exit 4
fi
python3 - "$package" "$staging" <<'PY'
import os
import sys
import tarfile

package, output = sys.argv[1:]
output = os.path.realpath(output)
with tarfile.open(package, "r:gz") as archive:
    members = archive.getmembers()
    names = []
    for member in members:
        name = member.name
        parts = name.split("/")
        if (
            not name
            or "\\\\" in name
            or "\\x00" in name
            or parts[0] != "codex"
            or any(part in {{"", ".", ".."}} for part in parts)
            or not member.isfile()
        ):
            raise SystemExit("unsafe archive member")
        target = os.path.realpath(os.path.join(output, *parts))
        if os.path.commonpath([output, target]) != output:
            raise SystemExit("unsafe archive member")
        names.append(name)
    if (
        len(members) != {member_count}
        or len(names) != len(set(names))
        or "{SOURCE_MANIFEST_MEMBER}" not in names
    ):
        raise SystemExit("archive member inventory mismatch")
    archive.extractall(output, members=members)
PY
rm "$package"
mv "$staging" "$output"
trap - EXIT
echo "PASS {package_sha256}"
""".encode("utf-8")


def _readme(archive_id: str, manifest: dict[str, Any]) -> bytes:
    return (
        "# Codex Public Raw Archive\n\n"
        f"Archive ID: `{archive_id}`\n\n"
        f"Source files: `{manifest['source_proof']['file_count']}`\n\n"
        f"Source bytes: `{manifest['source_proof']['source_total_bytes']}`\n\n"
        f"Package SHA-256: `{manifest['package']['sha256']}`\n\n"
        f"Parts: `{manifest['split']['part_count']}` at no more than "
        f"`{MAX_PART_BYTES}` bytes each.\n\n"
        "The source remained byte/stat identical during the run. The public package "
        "retains ordinary transcript content while replacing credential values and "
        "local absolute paths. It does not contain cursor, dedupe, resume or derived data.\n\n"
        "Restore into a new directory:\n\n"
        "```bash\n./restore.sh OUTPUT_DIRECTORY\n```\n"
    ).encode("utf-8")


def _write_exclusive(path: Path, payload: bytes, *, mode: int = 0o600) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            mode,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise CodexPublicRawArchiveError("archive_metadata_write_failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _fsync_directory(path: Path) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        os.fsync(descriptor)
    except OSError as exc:
        raise CodexPublicRawArchiveError("archive_directory_fsync_failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def _archive_lock(parent: Path, archive_id: str) -> Iterator[None]:
    lock_path = parent / f".{archive_id}.archive.lock"
    descriptor: int | None = None
    identity: tuple[int, int] | None = None
    try:
        try:
            descriptor = os.open(
                lock_path,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
        except FileExistsError as exc:
            raise CodexPublicRawArchiveError("archive_lock_exists") from exc
        metadata = os.fstat(descriptor)
        identity = (metadata.st_dev, metadata.st_ino)
        payload = _canonical_json_bytes(
            {
                "schema_version": SCHEMA_VERSION,
                "archive_id": archive_id,
                "pid": os.getpid(),
                "created_at_ns": time.time_ns(),
            }
        )
        os.write(descriptor, payload)
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        yield
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if identity is not None:
            try:
                current = os.stat(lock_path, follow_symlinks=False)
            except OSError:
                current = None
            if current is not None and (current.st_dev, current.st_ino) == identity:
                lock_path.unlink()
                _fsync_directory(parent)


def _ensure_archive_parent(database_dir: Path) -> Path:
    parent = database_dir / ARCHIVE_ROOT
    current = database_dir
    for part in ARCHIVE_ROOT.parts:
        current = current / part
        try:
            current.mkdir(mode=0o700)
        except FileExistsError:
            pass
        metadata = current.lstat()
        if stat_module.S_ISLNK(metadata.st_mode) or not stat_module.S_ISDIR(metadata.st_mode):
            raise CodexPublicRawArchiveError("archive_parent_unsafe")
    return parent


def _prepare_staging(
    staging: Path,
    archive_id: str,
    package: dict[str, Any],
    parts: list[dict[str, Any]],
) -> tuple[dict[str, Any], bytes]:
    manifest = _archive_manifest(archive_id, package, parts)
    manifest_bytes = _canonical_json_bytes(manifest)
    _write_exclusive(staging / README_FILENAME, _readme(archive_id, manifest), mode=0o644)
    _write_exclusive(
        staging / RESTORE_FILENAME,
        _restore_script(
            archive_id,
            str(package["sha256"]),
            int(package["member_count"]),
        ),
        mode=0o700,
    )
    _write_exclusive(staging / MANIFEST_FILENAME, manifest_bytes, mode=0o600)
    _fsync_directory(staging / PARTS_DIRECTORY)
    _fsync_directory(staging)
    return manifest, manifest_bytes


def _publish_staging(staging: Path, final: Path) -> None:
    created_final = False
    try:
        final.mkdir(mode=0o700)
        created_final = True
        os.rename(staging / PARTS_DIRECTORY, final / PARTS_DIRECTORY)
        os.rename(staging / README_FILENAME, final / README_FILENAME)
        os.rename(staging / RESTORE_FILENAME, final / RESTORE_FILENAME)
        os.rename(staging / MANIFEST_FILENAME, final / MANIFEST_FILENAME)
        _fsync_directory(final)
        _fsync_directory(final.parent)
    except FileExistsError as exc:
        raise CodexPublicRawArchiveError("archive_id_exists") from exc
    except Exception as exc:
        manifest_exists = (final / MANIFEST_FILENAME).exists() if created_final else False
        if created_final and not manifest_exists:
            shutil.rmtree(final, ignore_errors=True)
        if isinstance(exc, CodexPublicRawArchiveError):
            if manifest_exists:
                raise CodexPublicRawArchiveError(
                    exc.code,
                    writes_files=True,
                    archive_may_exist=True,
                ) from exc
            raise
        raise CodexPublicRawArchiveError(
            "archive_publish_failed",
            writes_files=created_final,
            archive_may_exist=manifest_exists,
        ) from exc


def _safe_manifest_path(path: str) -> None:
    _safe_repo_relative(path)
    if "/Users/" in path or path.startswith("/home/"):
        raise CodexPublicRawArchiveError("archive_manifest_path_invalid")


def verify_codex_public_raw_archive(
    database_dir: Path,
    archive_id: str,
    *,
    require_public_registration: bool = True,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    archive_id = _portable_archive_id(archive_id)
    archive_path = database_dir / ARCHIVE_ROOT / archive_id
    try:
        if archive_path.is_symlink() or not archive_path.is_dir():
            raise CodexPublicRawArchiveError("archive_missing")
        expected_root = {
            PARTS_DIRECTORY,
            MANIFEST_FILENAME,
            README_FILENAME,
            RESTORE_FILENAME,
        }
        if {path.name for path in archive_path.iterdir()} != expected_root:
            raise CodexPublicRawArchiveError("archive_root_inventory_mismatch")
        manifest_bytes = _read_regular_bytes(
            archive_path / MANIFEST_FILENAME,
            max_bytes=MAX_MANIFEST_BYTES,
            code="archive_manifest_unreadable",
        )
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexPublicRawArchiveError("archive_manifest_invalid_json") from exc
    if not isinstance(manifest, dict):
        raise CodexPublicRawArchiveError("archive_manifest_not_object")
    expected_manifest_keys = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "archive_id",
        "recorded_at_utc",
        "visibility",
        "archive_path",
        "authorization",
        "content_policy",
        "source_proof",
        "package",
        "split",
        "parts",
        "redaction_counts",
        "restore",
        "public_index",
        "phase_boundary",
    }
    if (
        set(manifest) != expected_manifest_keys
        or
        manifest.get("schema_version") != ARCHIVE_MANIFEST_SCHEMA_VERSION
        or manifest.get("task_id") != TASK_ID
        or manifest.get("acceptance_id") != ACCEPTANCE_ID
        or manifest.get("source_id") != SOURCE_ID
        or manifest.get("archive_id") != archive_id
        or manifest.get("archive_path") != (ARCHIVE_ROOT / archive_id).as_posix()
        or manifest.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
        or manifest.get("visibility") != "public_github_repository"
        or manifest.get("authorization")
        != {
            "basis": "v1.2.1 TaskPack S07-P1-T2",
            "credential_values_public": False,
            "local_absolute_paths_public": False,
        }
        or manifest.get("content_policy") != EXPECTED_PUBLIC_CONTENT
        or manifest.get("restore")
        != {
            "script": RESTORE_FILENAME,
            "output_no_overwrite": True,
            "source_manifest_member": SOURCE_MANIFEST_MEMBER,
        }
        or manifest.get("public_index")
        != {
            "root": PUBLIC_INDEX_ROOT.as_posix(),
            "append_only": True,
            "raw_ledger_required": True,
        }
    ):
        raise CodexPublicRawArchiveError("archive_manifest_identity_mismatch")
    recorded_at = manifest.get("recorded_at_utc")
    try:
        parsed_recorded_at = datetime.fromisoformat(str(recorded_at).replace("Z", "+00:00"))
    except ValueError as exc:
        raise CodexPublicRawArchiveError("archive_manifest_time_invalid") from exc
    if (
        not isinstance(recorded_at, str)
        or not recorded_at.endswith("Z")
        or parsed_recorded_at.tzinfo is None
        or parsed_recorded_at.utcoffset() != timezone.utc.utcoffset(parsed_recorded_at)
    ):
        raise CodexPublicRawArchiveError("archive_manifest_time_invalid")
    redaction_counts = manifest.get("redaction_counts")
    if (
        not isinstance(redaction_counts, dict)
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for key, value in redaction_counts.items()
        )
    ):
        raise CodexPublicRawArchiveError("archive_redaction_counts_invalid")
    _safe_manifest_path(str(manifest["archive_path"]))
    source_proof = manifest.get("source_proof")
    if (
        not isinstance(source_proof, dict)
        or source_proof.get("before_sha256") != source_proof.get("after_sha256")
        or source_proof.get("hash_stat_equal") is not True
        or source_proof.get("source_mutation") is not False
    ):
        raise CodexPublicRawArchiveError("archive_source_proof_invalid")
    package = manifest.get("package")
    split = manifest.get("split")
    parts = manifest.get("parts")
    if not isinstance(package, dict) or not isinstance(split, dict) or not isinstance(parts, list):
        raise CodexPublicRawArchiveError("archive_manifest_structure_invalid")
    if (
        split.get("max_part_bytes") != MAX_PART_BYTES
        or split.get("part_index_width") != PART_INDEX_WIDTH
        or split.get("part_count") != len(parts)
        or not parts
    ):
        raise CodexPublicRawArchiveError("archive_split_contract_mismatch")
    parts_dir = archive_path / PARTS_DIRECTORY
    expected_names: set[str] = set()
    package_digest = hashlib.sha256()
    package_bytes = 0
    for index, part in enumerate(parts):
        if not isinstance(part, dict):
            raise CodexPublicRawArchiveError("archive_part_manifest_invalid")
        name = f"{archive_id}.tar.gz.part-{index:0{PART_INDEX_WIDTH}d}"
        relative = f"{PARTS_DIRECTORY}/{name}"
        if part.get("index") != index or part.get("filename") != relative:
            raise CodexPublicRawArchiveError("archive_part_order_invalid")
        expected_names.add(name)
        part_path = parts_dir / name
        if part_path.is_symlink() or not part_path.is_file():
            raise CodexPublicRawArchiveError("archive_part_missing")
        digest = hashlib.sha256()
        size = 0
        with part_path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(READ_CHUNK_BYTES), b""):
                digest.update(chunk)
                package_digest.update(chunk)
                size += len(chunk)
                package_bytes += len(chunk)
        if (
            size != part.get("byte_size")
            or digest.hexdigest() != part.get("sha256")
            or size <= 0
            or size > MAX_PART_BYTES
        ):
            raise CodexPublicRawArchiveError("archive_part_hash_or_size_mismatch")
    if {path.name for path in parts_dir.iterdir()} != expected_names:
        raise CodexPublicRawArchiveError("archive_part_inventory_mismatch")
    if (
        package_bytes != package.get("byte_size")
        or package_digest.hexdigest() != package.get("sha256")
        or package.get("format") != PACKAGE_FORMAT
        or not isinstance(package.get("member_count"), int)
        or package.get("member_count") <= 0
    ):
        raise CodexPublicRawArchiveError("archive_package_hash_or_size_mismatch")
    expected_readme = _readme(archive_id, manifest)
    expected_restore = _restore_script(
        archive_id,
        str(package["sha256"]),
        int(package["member_count"]),
    )
    if _read_regular_bytes(
        archive_path / README_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="archive_readme_unreadable",
    ) != expected_readme:
        raise CodexPublicRawArchiveError("archive_readme_mismatch")
    if _read_regular_bytes(
        archive_path / RESTORE_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="archive_restore_script_unreadable",
    ) != expected_restore:
        raise CodexPublicRawArchiveError("archive_restore_script_mismatch")
    result = {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / archive_id).as_posix(),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "package_sha256": package_digest.hexdigest(),
        "package_bytes": package_bytes,
        "part_count": len(parts),
        "source_file_count": source_proof["file_count"],
        "source_total_bytes": source_proof["source_total_bytes"],
        "discovered_file_count": source_proof["discovered_file_count"],
        "discovered_total_bytes": source_proof["discovered_total_bytes"],
        "deferred_inflight_file_count": source_proof[
            "deferred_inflight_file_count"
        ],
        "source_hash_stat_equal": source_proof["hash_stat_equal"],
        "source_mutation": False,
        "archive_mutation": False,
        "remote_push": False,
    }
    if require_public_registration:
        result.update(
            _verify_public_registration(
                database_dir,
                archive_id,
                result,
                manifest,
            )
        )
    return result


def _public_index_payload(
    archive_id: str,
    verification: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_INDEX_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": verification["archive_path"],
        "archive_manifest_sha256": verification["manifest_sha256"],
        "package_sha256": verification["package_sha256"],
        "package_bytes": verification["package_bytes"],
        "part_count": verification["part_count"],
        "source_file_count": verification["source_file_count"],
        "source_total_bytes": verification["source_total_bytes"],
        "discovered_file_count": verification["discovered_file_count"],
        "discovered_total_bytes": verification["discovered_total_bytes"],
        "deferred_inflight_file_count": verification[
            "deferred_inflight_file_count"
        ],
        "source_before_sha256": manifest["source_proof"]["before_sha256"],
        "source_after_sha256": manifest["source_proof"]["after_sha256"],
        "source_hash_stat_equal": verification["source_hash_stat_equal"],
        "content_policy": EXPECTED_PUBLIC_CONTENT["policy"],
        "credential_values_public": False,
        "local_absolute_paths_public": False,
        "raw_ledger_required": True,
        "source_mutation": False,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _verify_public_registration(
    database_dir: Path,
    archive_id: str,
    verification: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    suffix = str(verification["manifest_sha256"])[:12]
    relative = PUBLIC_INDEX_ROOT / f"codex_raw_archive.{archive_id}.{suffix}.json"
    path = database_dir / relative
    try:
        payload_bytes = _read_regular_bytes(
            path,
            max_bytes=MAX_CONTRACT_BYTES,
            code="archive_public_index_missing",
        )
        payload = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexPublicRawArchiveError("archive_public_index_invalid") from exc
    expected = _public_index_payload(archive_id, verification, manifest)
    if payload != expected:
        raise CodexPublicRawArchiveError("archive_public_index_mismatch")
    raw_manifest_relative = (
        RAW_MANIFEST_ROOT / f"raw_manifest.{_raw_manifest_run_id(archive_id)}.jsonl"
    )
    raw_ledger_relative = RAW_MANIFEST_ROOT / "raw_hash_ledger.jsonl"
    raw_manifest_bytes = _read_regular_bytes(
        database_dir / raw_manifest_relative,
        max_bytes=MAX_MANIFEST_BYTES,
        code="archive_raw_manifest_missing",
    )
    raw_ledger_bytes = _read_regular_bytes(
        database_dir / raw_ledger_relative,
        max_bytes=MAX_MANIFEST_BYTES,
        code="archive_public_ledger_invalid",
    )
    if not raw_ledger_bytes.startswith(raw_manifest_bytes) or (
        raw_manifest_bytes and not raw_manifest_bytes.endswith(b"\n")
    ):
        raise CodexPublicRawArchiveError("archive_raw_manifest_ledger_mismatch")
    try:
        ledger = preflight_raw_ledger(database_dir)
    except RawLedgerError as exc:
        raise CodexPublicRawArchiveError(
            "archive_public_ledger_invalid"
        ) from exc
    return {
        "public_index_path": relative.as_posix(),
        "public_index_sha256": hashlib.sha256(payload_bytes).hexdigest(),
        "raw_manifest_path": raw_manifest_relative.as_posix(),
        "raw_manifest_sha256": hashlib.sha256(raw_manifest_bytes).hexdigest(),
        "raw_manifest_is_ledger_prefix": True,
        "raw_ledger_verified": True,
        "public_raw_file_count": int(ledger["raw_file_count"]),
    }


def _write_public_index(
    database_dir: Path,
    archive_id: str,
    verification: dict[str, Any],
    manifest: dict[str, Any],
) -> Path:
    root = database_dir / PUBLIC_INDEX_ROOT
    root.mkdir(parents=True, exist_ok=True)
    payload = _canonical_json_bytes(
        _public_index_payload(archive_id, verification, manifest)
    )
    suffix = str(verification["manifest_sha256"])[:12]
    path = root / f"codex_raw_archive.{archive_id}.{suffix}.json"
    _write_exclusive(path, payload, mode=0o600)
    _fsync_directory(root)
    return path


def build_codex_public_raw_archive(
    database_dir: Path,
    archive_id: str,
    *,
    operator_codex_home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    archive_id = _portable_archive_id(archive_id)
    load_codex_public_raw_archive_contract(database_dir)
    if not dry_run:
        try:
            preflight_raw_ledger(database_dir)
        except RawLedgerError as exc:
            raise CodexPublicRawArchiveError("public_raw_ledger_preflight_failed") from exc
    discovery_contract, credential_contract, inventory = _resolve_inventory(
        database_dir,
        operator_codex_home=operator_codex_home,
        environ=environ,
        home=home,
    )
    discovered_inventory = inventory
    inventory, deferred_inflight = _partition_inflight_sources(inventory)
    final_relative = ARCHIVE_ROOT / archive_id
    final = database_dir / final_relative
    if os.path.lexists(final):
        raise CodexPublicRawArchiveError("archive_id_exists")
    if dry_run:
        return {
            "status": "PASS",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "archive_id": archive_id,
            "dry_run": True,
            "eligible_file_count": len(discovered_inventory.files),
            "eligible_total_bytes": sum(
                item.size_bytes for item in discovered_inventory.files
            ),
            "stable_file_count": len(inventory.files),
            "deferred_inflight_file_count": len(deferred_inflight),
            "source_root": "[CODEX_HOME]",
            "would_write_archive_path": final_relative.as_posix(),
            "would_write_public_index_root": PUBLIC_INDEX_ROOT.as_posix(),
            "source_content_read": False,
            "source_mutation": False,
            "writes_files": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }

    parent = _ensure_archive_parent(database_dir)
    with _archive_lock(parent, archive_id):
        if os.path.lexists(final):
            raise CodexPublicRawArchiveError("archive_id_exists")
        staging = Path(
            tempfile.mkdtemp(prefix=f".{archive_id}.staging-", dir=parent)
        )
        published = False
        try:
            inventory, before, deferred_inflight = _capture_quiescent_proofs(
                inventory,
                discovery_contract,
                credential_contract,
                deferred_inflight,
            )
            package, parts, _source_manifest = _build_package(
                staging,
                archive_id,
                inventory,
                discovery_contract,
                credential_contract,
                before,
                deferred_inflight,
            )
            manifest, _manifest_bytes = _prepare_staging(
                staging,
                archive_id,
                package,
                parts,
            )
            _publish_staging(staging, final)
            published = True
        except CodexPublicRawArchiveError:
            raise
        except Exception as exc:
            raise CodexPublicRawArchiveError("archive_build_failed") from exc
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)
        if not published:
            raise CodexPublicRawArchiveError("archive_not_published")

    verification = verify_codex_public_raw_archive(
        database_dir,
        archive_id,
        require_public_registration=False,
    )
    try:
        public_index = _write_public_index(
            database_dir,
            archive_id,
            verification,
            manifest,
        )
        ledger = generate_raw_manifest(
            database_dir,
            _raw_manifest_run_id(archive_id),
            imported_at=manifest["recorded_at_utc"],
            require_non_empty=False,
        )
    except (RawLedgerError, CodexPublicRawArchiveError) as exc:
        raise CodexPublicRawArchiveError(
            "archive_public_index_or_ledger_failed",
            writes_files=True,
            archive_may_exist=True,
        ) from exc
    verification = verify_codex_public_raw_archive(database_dir, archive_id)
    return {
        **verification,
        "dry_run": False,
        "writes_files": True,
        "public_index_path": public_index.relative_to(database_dir).as_posix(),
        "raw_ledger": ledger,
        "redaction_counts": manifest["redaction_counts"],
        "source_before_sha256": manifest["source_proof"]["before_sha256"],
        "source_after_sha256": manifest["source_proof"]["after_sha256"],
        "credential_values_public": False,
        "local_absolute_paths_public": False,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def run_codex_public_raw_archive(args: argparse.Namespace) -> int:
    archive_id = getattr(args, "archive_id", None)
    if not archive_id:
        result = {
            "status": "FAIL_CLOSED",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "reason": "archive_id_required",
            "writes_files": False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    try:
        result = build_codex_public_raw_archive(
            getattr(args, "database_dir", Path(__file__).resolve().parents[2]),
            archive_id,
            operator_codex_home=getattr(args, "codex_home", None),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    except (
        CodexPublicRawArchiveError,
        CredentialExclusionError,
        RawLedgerError,
        SourceRegistryError,
    ) as exc:
        error = exc if isinstance(exc, CodexPublicRawArchiveError) else None
        result = {
            "status": "FAIL_CLOSED",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "archive_id": archive_id,
            "reason": error.code if error else "archive_dependency_invalid",
            "writes_files": error.writes_files if error else False,
            "archive_may_exist": error.archive_may_exist if error else False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


def run_codex_public_raw_archive_audit(args: argparse.Namespace) -> int:
    archive_id = getattr(args, "archive_id", None)
    try:
        if not archive_id:
            raise CodexPublicRawArchiveError("archive_id_required")
        result = verify_codex_public_raw_archive(args.database_dir, archive_id)
        result["check"] = "codex-public-raw-archive"
        result["writes_files"] = False
    except CodexPublicRawArchiveError as exc:
        result = {
            "status": "FAIL_CLOSED",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "check": "codex-public-raw-archive",
            "source_id": SOURCE_ID,
            "archive_id": archive_id,
            "reason": exc.code,
            "writes_files": False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = (
    "ACCEPTANCE_ID",
    "ARCHIVE_MANIFEST_SCHEMA_VERSION",
    "ARCHIVE_ROOT",
    "CONTRACT_PATH",
    "CodexPublicRawArchiveError",
    "EXPECTED_PHASE_BOUNDARY",
    "MAX_PART_BYTES",
    "PUBLIC_INDEX_ROOT",
    "RESULT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "SOURCE_MANIFEST_SCHEMA_VERSION",
    "TASK_ID",
    "build_codex_public_raw_archive",
    "load_codex_public_raw_archive_contract",
    "run_codex_public_raw_archive",
    "run_codex_public_raw_archive_audit",
    "validate_codex_public_raw_archive_contract",
    "verify_codex_public_raw_archive",
)
