"""Bounded read-only adapter for standard local Agent exports."""

from __future__ import annotations

import hashlib
import json
import math
import os
import sqlite3
import stat
from collections import Counter
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping


SCHEMA_VERSION = "memory_atlas.generic_agent_read_adapter.v1_2_1_s09_p2_t1"
TASK_ID = "S09-P2-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P2-T1"
CONTRACT_PATH = Path("config/data_sources/generic_agent_read_adapter.json")
MODEL_PATH = Path("机器治理/参数与公式/generic_agent_read_adapter.v1_2_1_s09_p2_t1.json")
ENTRYPOINT_PATH = Path("scripts/inspect_memory_atlas_generic_agent_export.py")
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
MAX_CONTRACT_BYTES = 128 * 1024
READ_CHUNK_BYTES = 1024 * 1024

EXPECTED_SOURCE_SHAPES = ["file", "directory"]
EXPECTED_FORMATS = ["json", "jsonl", "sqlite"]
EXPECTED_SUFFIXES = {
    "json": [".json"],
    "jsonl": [".jsonl"],
    "sqlite": [".db", ".sqlite", ".sqlite3"],
}
EXPECTED_DIRECTORY = {
    "recursive": True,
    "follow_symlinks": False,
    "unsupported_regular_files": "skip_without_read",
    "symlink_or_special_file": "fail_closed",
    "ordering": "relative_path_utf8_lexical",
    "snapshot_scope": "all_entries_and_supported_file_hashes",
}
EXPECTED_JSON = {
    "encoding": "utf-8-sig-strict",
    "top_level": ["object", "non_empty_object_list", "events_object_list"],
    "jsonl_blank_lines": "ignore",
    "non_object_record": "fail_closed",
    "non_finite_number": "fail_closed",
}
EXPECTED_SQLITE = {
    "open_mode": "mode=ro&immutable=1",
    "query_only": True,
    "self_contained_export_required": True,
    "rejected_sidecars": ["-journal", "-shm", "-wal"],
    "table_scope": "user_tables_only",
    "record_json_column": "allowed_only_as_single_column_object_payload",
    "direct_columns": "json_scalar_values_only",
    "blob_policy": "fail_closed",
    "record_order": "canonical_json_utf8_lexical_per_table",
}
EXPECTED_LIMITS = {
    "max_tree_entries": 4096,
    "max_source_files": 1024,
    "max_file_bytes": 64 * 1024 * 1024,
    "max_total_bytes": 512 * 1024 * 1024,
    "max_records": 200_000,
    "max_sqlite_tables": 128,
    "max_sqlite_columns": 256,
    "max_scalar_utf8_bytes": 1024 * 1024,
    "max_json_depth": 64,
}
EXPECTED_SAFETY = {
    "source_read_only": True,
    "writes_files": False,
    "network_access": False,
    "remote_git_write": False,
    "source_content_in_cli_output": False,
    "local_absolute_path_in_output": False,
    "verify_before_and_after_downstream_commit": True,
}
EXPECTED_PHASE_BOUNDARY = {
    "future_agent_fixture_implemented": False,
    "raw_archive_implemented": False,
    "derived_pipeline_implemented": False,
    "restore_proof_implemented": False,
    "plugin_contract_implemented": False,
    "remote_push": False,
    "next_task": "S09-P2-T2",
}


class GenericAgentReadError(ValueError):
    """Path-free fail-closed reason for untrusted Agent source input."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


@dataclass(frozen=True)
class AdapterLimits:
    max_tree_entries: int = EXPECTED_LIMITS["max_tree_entries"]
    max_source_files: int = EXPECTED_LIMITS["max_source_files"]
    max_file_bytes: int = EXPECTED_LIMITS["max_file_bytes"]
    max_total_bytes: int = EXPECTED_LIMITS["max_total_bytes"]
    max_records: int = EXPECTED_LIMITS["max_records"]
    max_sqlite_tables: int = EXPECTED_LIMITS["max_sqlite_tables"]
    max_sqlite_columns: int = EXPECTED_LIMITS["max_sqlite_columns"]
    max_scalar_utf8_bytes: int = EXPECTED_LIMITS["max_scalar_utf8_bytes"]
    max_json_depth: int = EXPECTED_LIMITS["max_json_depth"]

    @classmethod
    def from_mapping(cls, value: Mapping[str, Any]) -> "AdapterLimits":
        if set(value) != set(EXPECTED_LIMITS):
            raise GenericAgentReadError("adapter_limit_keys_mismatch")
        if any(not isinstance(item, int) or isinstance(item, bool) or item <= 0 for item in value.values()):
            raise GenericAgentReadError("adapter_limit_invalid")
        return cls(**{field: int(value[field]) for field in EXPECTED_LIMITS})

    def assert_within(self, maximum: "AdapterLimits") -> None:
        for field in EXPECTED_LIMITS:
            if getattr(self, field) <= 0 or getattr(self, field) > getattr(maximum, field):
                raise GenericAgentReadError("adapter_limits_exceed_contract")


@dataclass(frozen=True)
class TreeEntrySnapshot:
    relative_path: str
    entry_kind: str
    device: int
    inode: int
    mode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int


@dataclass(frozen=True)
class GenericAgentSourceFile:
    path: Path
    relative_path: str
    source_format: str
    size_bytes: int
    sha256: str


@dataclass(frozen=True)
class GenericAgentSourceRecord:
    payload: dict[str, Any]
    source_format: str
    relative_path_sha256: str
    ordinal: int
    sqlite_table_sha256: str | None = None


@dataclass(frozen=True)
class GenericAgentReadResult:
    source_path: Path
    source_kind: str
    limits: AdapterLimits
    tree_snapshot: tuple[TreeEntrySnapshot, ...]
    files: tuple[GenericAgentSourceFile, ...]
    records: tuple[GenericAgentSourceRecord, ...]
    skipped_file_count: int
    source_sha256: str

    @property
    def source_file_count(self) -> int:
        return len(self.files)

    @property
    def format_counts(self) -> dict[str, int]:
        counts = Counter(record.source_format for record in self.records)
        return dict(sorted(counts.items()))

    def public_summary(self) -> dict[str, Any]:
        return {
            "status": "PASS",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "adapter_contract": CONTRACT_PATH.as_posix(),
            "source_kind": self.source_kind,
            "source_file_count": self.source_file_count,
            "skipped_file_count": self.skipped_file_count,
            "record_count": len(self.records),
            "source_formats": sorted(self.format_counts),
            "format_counts": self.format_counts,
            "source_sha256": self.source_sha256,
            "source_read_only": True,
            "writes_files": False,
            "network_access": False,
            "remote_push": False,
            "source_content_in_output": False,
            "local_absolute_path_in_output": False,
            "sqlite_open_mode": EXPECTED_SQLITE["open_mode"],
        }


def _load_contract_json(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise GenericAgentReadError("adapter_contract_unreadable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise GenericAgentReadError("adapter_contract_not_regular")
        if metadata.st_size > MAX_CONTRACT_BYTES:
            raise GenericAgentReadError("adapter_contract_too_large")
        payload = os.read(descriptor, MAX_CONTRACT_BYTES + 1)
    except OSError as exc:
        raise GenericAgentReadError("adapter_contract_unreadable") from exc
    finally:
        os.close(descriptor)
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenericAgentReadError("adapter_contract_invalid_json") from exc
    if not isinstance(value, dict):
        raise GenericAgentReadError("adapter_contract_not_object")
    return value


def validate_generic_agent_read_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise GenericAgentReadError("adapter_contract_not_object")
    expected_keys = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "entrypoint",
        "model_ref",
        "source_shapes",
        "formats",
        "suffixes",
        "directory",
        "json",
        "sqlite",
        "limits",
        "safety",
        "phase_boundary",
    }
    if set(payload) != expected_keys:
        raise GenericAgentReadError("adapter_contract_keys_mismatch")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("entrypoint") != ENTRYPOINT_PATH.as_posix()
        or payload.get("model_ref") != MODEL_PATH.as_posix()
    ):
        raise GenericAgentReadError("adapter_contract_identity_mismatch")
    expected_sections = {
        "source_shapes": EXPECTED_SOURCE_SHAPES,
        "formats": EXPECTED_FORMATS,
        "suffixes": EXPECTED_SUFFIXES,
        "directory": EXPECTED_DIRECTORY,
        "json": EXPECTED_JSON,
        "sqlite": EXPECTED_SQLITE,
        "limits": EXPECTED_LIMITS,
        "safety": EXPECTED_SAFETY,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    for field, expected in expected_sections.items():
        if payload.get(field) != expected:
            raise GenericAgentReadError(f"adapter_contract_{field}_mismatch")
    AdapterLimits.from_mapping(payload["limits"])
    return payload


def load_generic_agent_read_contract(database_dir: Path) -> dict[str, Any]:
    requested_root = database_dir.resolve()
    root = requested_root if (requested_root / CONTRACT_PATH).is_file() else PACKAGE_ROOT
    contract = validate_generic_agent_read_contract(_load_contract_json(root / CONTRACT_PATH))
    for field, relative in (("entrypoint", ENTRYPOINT_PATH), ("model_ref", MODEL_PATH)):
        target = root / relative
        try:
            metadata = target.lstat()
        except OSError as exc:
            raise GenericAgentReadError(f"adapter_{field}_missing") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise GenericAgentReadError(f"adapter_{field}_not_regular")
    return contract


def _snapshot_entry(relative_path: str, entry_kind: str, metadata: os.stat_result) -> TreeEntrySnapshot:
    return TreeEntrySnapshot(
        relative_path=relative_path,
        entry_kind=entry_kind,
        device=int(metadata.st_dev),
        inode=int(metadata.st_ino),
        mode=int(metadata.st_mode),
        size_bytes=int(metadata.st_size),
        mtime_ns=int(metadata.st_mtime_ns),
        ctime_ns=int(metadata.st_ctime_ns),
    )


def _capture_tree(source: Path, limits: AdapterLimits) -> tuple[str, tuple[TreeEntrySnapshot, ...]]:
    try:
        root_metadata = source.lstat()
    except OSError as exc:
        raise GenericAgentReadError("source_missing_or_unreadable") from exc
    if stat.S_ISLNK(root_metadata.st_mode):
        raise GenericAgentReadError("source_symlink_rejected")
    if stat.S_ISREG(root_metadata.st_mode):
        return "file", (_snapshot_entry(".", "file", root_metadata),)
    if not stat.S_ISDIR(root_metadata.st_mode):
        raise GenericAgentReadError("source_special_file_rejected")

    snapshots = [_snapshot_entry(".", "directory", root_metadata)]
    stack = [source]
    while stack:
        directory = stack.pop()
        try:
            entries = sorted(os.scandir(directory), key=lambda entry: os.fsencode(entry.name))
        except OSError as exc:
            raise GenericAgentReadError("source_directory_unreadable") from exc
        child_directories: list[Path] = []
        for entry in entries:
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise GenericAgentReadError("tree_entry_unreadable") from exc
            path = Path(entry.path)
            try:
                relative_path = path.relative_to(source).as_posix()
            except ValueError as exc:
                raise GenericAgentReadError("tree_entry_escape") from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise GenericAgentReadError("tree_symlink_rejected")
            if stat.S_ISDIR(metadata.st_mode):
                snapshots.append(_snapshot_entry(relative_path, "directory", metadata))
                child_directories.append(path)
            elif stat.S_ISREG(metadata.st_mode):
                snapshots.append(_snapshot_entry(relative_path, "file", metadata))
            else:
                raise GenericAgentReadError("tree_special_file_rejected")
            if len(snapshots) - 1 > limits.max_tree_entries:
                raise GenericAgentReadError("tree_entry_limit_exceeded")
        stack.extend(reversed(child_directories))
    snapshots.sort(key=lambda item: os.fsencode(item.relative_path))
    return "directory", tuple(snapshots)


def _format_for_path(path: Path) -> str | None:
    suffix = path.suffix.lower()
    for source_format, suffixes in EXPECTED_SUFFIXES.items():
        if suffix in suffixes:
            return source_format
    return None


def _open_regular(path: Path) -> tuple[int, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        metadata = os.fstat(descriptor)
    except OSError as exc:
        raise GenericAgentReadError("source_file_unreadable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        os.close(descriptor)
        raise GenericAgentReadError("source_file_not_regular")
    return descriptor, metadata


def _read_regular_bytes(path: Path, max_bytes: int) -> tuple[bytes, str]:
    descriptor, before = _open_regular(path)
    try:
        if before.st_size > max_bytes:
            raise GenericAgentReadError("source_file_size_limit_exceeded")
        chunks: list[bytes] = []
        total = 0
        digest = hashlib.sha256()
        while True:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise GenericAgentReadError("source_file_size_limit_exceeded")
            chunks.append(chunk)
            digest.update(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise GenericAgentReadError("source_file_unreadable") from exc
    finally:
        os.close(descriptor)
    if _stat_identity(before) != _stat_identity(after) or total != int(after.st_size):
        raise GenericAgentReadError("source_snapshot_changed")
    return b"".join(chunks), digest.hexdigest()


def _hash_regular_file(path: Path, max_bytes: int) -> str:
    descriptor, before = _open_regular(path)
    try:
        if before.st_size > max_bytes:
            raise GenericAgentReadError("source_file_size_limit_exceeded")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, READ_CHUNK_BYTES)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise GenericAgentReadError("source_file_size_limit_exceeded")
            digest.update(chunk)
        after = os.fstat(descriptor)
    except OSError as exc:
        raise GenericAgentReadError("source_file_unreadable") from exc
    finally:
        os.close(descriptor)
    if _stat_identity(before) != _stat_identity(after) or total != int(after.st_size):
        raise GenericAgentReadError("source_snapshot_changed")
    return digest.hexdigest()


def _stat_identity(value: os.stat_result) -> tuple[int, int, int, int, int, int]:
    return (
        int(value.st_dev),
        int(value.st_ino),
        int(value.st_mode),
        int(value.st_size),
        int(value.st_mtime_ns),
        int(value.st_ctime_ns),
    )


def _reject_json_constant(_value: str) -> None:
    raise GenericAgentReadError("json_non_finite_number")


def _json_loads(text: str, code: str) -> Any:
    try:
        return json.loads(text, parse_constant=_reject_json_constant)
    except GenericAgentReadError:
        raise
    except json.JSONDecodeError as exc:
        raise GenericAgentReadError(code) from exc


def _validate_json_value(value: Any, limits: AdapterLimits, depth: int = 0) -> None:
    if depth > limits.max_json_depth:
        raise GenericAgentReadError("json_depth_limit_exceeded")
    if value is None or isinstance(value, bool) or isinstance(value, int):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise GenericAgentReadError("json_non_finite_number")
        return
    if isinstance(value, str):
        if len(value.encode("utf-8")) > limits.max_scalar_utf8_bytes:
            raise GenericAgentReadError("scalar_size_limit_exceeded")
        return
    if isinstance(value, list):
        for item in value:
            _validate_json_value(item, limits, depth + 1)
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise GenericAgentReadError("json_key_not_string")
            _validate_json_value(key, limits, depth + 1)
            _validate_json_value(item, limits, depth + 1)
        return
    raise GenericAgentReadError("json_value_type_unsupported")


def _object_records(value: Any, limits: AdapterLimits, *, prefix: str) -> list[dict[str, Any]]:
    if isinstance(value, dict):
        events = value.get("events")
        if isinstance(events, list):
            value = events
        else:
            value = [value]
    if not isinstance(value, list) or not value:
        raise GenericAgentReadError(f"{prefix}_record_missing")
    if not all(isinstance(item, dict) for item in value):
        raise GenericAgentReadError(f"{prefix}_record_not_object")
    records = list(value)
    for record in records:
        _validate_json_value(record, limits)
    return records


def _read_json(data: bytes, limits: AdapterLimits) -> list[dict[str, Any]]:
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise GenericAgentReadError("json_encoding_invalid") from exc
    return _object_records(_json_loads(text, "json_invalid"), limits, prefix="json")


def _read_jsonl(data: bytes, limits: AdapterLimits) -> list[dict[str, Any]]:
    try:
        text = data.decode("utf-8-sig", errors="strict")
    except UnicodeDecodeError as exc:
        raise GenericAgentReadError("jsonl_encoding_invalid") from exc
    records: list[dict[str, Any]] = []
    for line in text.splitlines():
        if not line.strip():
            continue
        value = _json_loads(line, "jsonl_invalid")
        if not isinstance(value, dict):
            raise GenericAgentReadError("jsonl_record_not_object")
        _validate_json_value(value, limits)
        records.append(value)
        if len(records) > limits.max_records:
            raise GenericAgentReadError("record_limit_exceeded")
    if not records:
        raise GenericAgentReadError("jsonl_record_missing")
    return records


def _quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sqlite_sidecars(path: Path) -> tuple[Path, ...]:
    return tuple(Path(f"{path}{suffix}") for suffix in EXPECTED_SQLITE["rejected_sidecars"])


def _assert_sqlite_self_contained(path: Path) -> None:
    for sidecar in _sqlite_sidecars(path):
        if os.path.lexists(sidecar):
            raise GenericAgentReadError("sqlite_sidecar_present")


def _sqlite_value(value: Any, limits: AdapterLimits) -> Any:
    if isinstance(value, bytes):
        raise GenericAgentReadError("sqlite_blob_unsupported")
    _validate_json_value(value, limits)
    return value


def _read_sqlite(path: Path, limits: AdapterLimits, remaining: int) -> list[tuple[dict[str, Any], str]]:
    _assert_sqlite_self_contained(path)
    uri = f"{path.resolve(strict=True).as_uri()}?mode=ro&immutable=1"
    connection: sqlite3.Connection | None = None
    records: list[tuple[dict[str, Any], str]] = []
    try:
        connection = sqlite3.connect(uri, uri=True, timeout=0)
        connection.execute("PRAGMA query_only=ON")
        query_only = connection.execute("PRAGMA query_only").fetchone()
        if query_only != (1,):
            raise GenericAgentReadError("sqlite_query_only_unproven")
        quick_check = connection.execute("PRAGMA quick_check").fetchone()
        if quick_check != ("ok",):
            raise GenericAgentReadError("sqlite_integrity_failed")
        tables = [
            str(row[0])
            for row in connection.execute(
                "SELECT name FROM sqlite_schema "
                "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        if not tables:
            raise GenericAgentReadError("sqlite_user_table_missing")
        if len(tables) > limits.max_sqlite_tables:
            raise GenericAgentReadError("sqlite_table_limit_exceeded")
        for table in tables:
            quoted = _quote_identifier(table)
            columns = [str(row[1]) for row in connection.execute(f"PRAGMA table_info({quoted})")]
            if not columns or len(columns) > limits.max_sqlite_columns:
                raise GenericAgentReadError("sqlite_column_limit_exceeded")
            if "record_json" in columns and columns != ["record_json"]:
                raise GenericAgentReadError("sqlite_record_json_schema_invalid")
            available = remaining - len(records)
            if available <= 0:
                raise GenericAgentReadError("record_limit_exceeded")
            rows = connection.execute(f"SELECT * FROM {quoted} LIMIT ?", (available + 1,)).fetchall()
            if len(rows) > available:
                raise GenericAgentReadError("record_limit_exceeded")
            table_records: list[dict[str, Any]] = []
            for row in rows:
                if columns == ["record_json"]:
                    if not isinstance(row[0], str):
                        raise GenericAgentReadError("sqlite_record_json_invalid")
                    value = _json_loads(row[0], "sqlite_record_json_invalid")
                    if not isinstance(value, dict):
                        raise GenericAgentReadError("sqlite_record_json_not_object")
                    record = value
                else:
                    record = {
                        column: _sqlite_value(value, limits)
                        for column, value in zip(columns, row, strict=True)
                    }
                _validate_json_value(record, limits)
                table_records.append(record)
            table_records.sort(
                key=lambda value: json.dumps(
                    value,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ).encode("utf-8")
            )
            table_sha256 = hashlib.sha256(table.encode("utf-8")).hexdigest()
            records.extend((record, table_sha256) for record in table_records)
    except GenericAgentReadError:
        raise
    except (OSError, sqlite3.Error, ValueError) as exc:
        raise GenericAgentReadError("sqlite_read_failed") from exc
    finally:
        if connection is not None:
            connection.close()
    _assert_sqlite_self_contained(path)
    if not records:
        raise GenericAgentReadError("sqlite_record_missing")
    return records


def _source_manifest_sha256(files: list[GenericAgentSourceFile], source_kind: str) -> str:
    manifest = {
        "source_kind": source_kind,
        "files": [
            {
                "relative_path": item.relative_path,
                "format": item.source_format,
                "size_bytes": item.size_bytes,
                "sha256": item.sha256,
            }
            for item in files
        ],
    }
    payload = json.dumps(manifest, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def read_generic_agent_export(
    database_dir: Path,
    source_path: Path,
    *,
    limits: AdapterLimits | None = None,
) -> GenericAgentReadResult:
    contract = load_generic_agent_read_contract(database_dir)
    maximum = AdapterLimits.from_mapping(contract["limits"])
    active_limits = limits or maximum
    active_limits.assert_within(maximum)

    try:
        source_lstat = source_path.lstat()
    except OSError as exc:
        raise GenericAgentReadError("source_missing_or_unreadable") from exc
    if stat.S_ISLNK(source_lstat.st_mode):
        raise GenericAgentReadError("source_symlink_rejected")
    try:
        source = source_path.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise GenericAgentReadError("source_resolve_failed") from exc
    source_kind, tree_snapshot = _capture_tree(source, active_limits)

    candidate_entries = [item for item in tree_snapshot if item.entry_kind == "file"]
    supported: list[tuple[TreeEntrySnapshot, Path, str]] = []
    skipped_file_count = 0
    for entry in candidate_entries:
        path = source if source_kind == "file" else source / entry.relative_path
        source_format = _format_for_path(path)
        if source_format is None:
            if source_kind == "file":
                raise GenericAgentReadError("source_format_unsupported")
            skipped_file_count += 1
            continue
        supported.append((entry, path, source_format))
    if not supported:
        raise GenericAgentReadError("supported_source_file_missing")
    if len(supported) > active_limits.max_source_files:
        raise GenericAgentReadError("source_file_limit_exceeded")
    if any(entry.size_bytes > active_limits.max_file_bytes for entry, _path, _format in supported):
        raise GenericAgentReadError("source_file_size_limit_exceeded")
    if sum(entry.size_bytes for entry, _path, _format in supported) > active_limits.max_total_bytes:
        raise GenericAgentReadError("source_total_size_limit_exceeded")

    files: list[GenericAgentSourceFile] = []
    records: list[GenericAgentSourceRecord] = []
    for entry, path, source_format in supported:
        if source_format == "sqlite":
            source_sha256 = _hash_regular_file(path, active_limits.max_file_bytes)
            loaded = _read_sqlite(path, active_limits, active_limits.max_records - len(records))
        else:
            data, source_sha256 = _read_regular_bytes(path, active_limits.max_file_bytes)
            plain_records = (
                _read_json(data, active_limits)
                if source_format == "json"
                else _read_jsonl(data, active_limits)
            )
            loaded = [(record, None) for record in plain_records]
        if len(records) + len(loaded) > active_limits.max_records:
            raise GenericAgentReadError("record_limit_exceeded")
        relative_path = "." if source_kind == "file" else entry.relative_path
        relative_path_sha256 = hashlib.sha256(relative_path.encode("utf-8")).hexdigest()
        files.append(
            GenericAgentSourceFile(
                path=path,
                relative_path=relative_path,
                source_format=source_format,
                size_bytes=entry.size_bytes,
                sha256=source_sha256,
            )
        )
        records.extend(
            GenericAgentSourceRecord(
                payload=payload,
                source_format=source_format,
                relative_path_sha256=relative_path_sha256,
                ordinal=ordinal,
                sqlite_table_sha256=table_sha256,
            )
            for ordinal, (payload, table_sha256) in enumerate(loaded, start=1)
        )

    result = GenericAgentReadResult(
        source_path=source,
        source_kind=source_kind,
        limits=active_limits,
        tree_snapshot=tree_snapshot,
        files=tuple(files),
        records=tuple(records),
        skipped_file_count=skipped_file_count,
        source_sha256=_source_manifest_sha256(files, source_kind),
    )
    verify_generic_agent_export_unchanged(result)
    return result


def verify_generic_agent_export_unchanged(result: GenericAgentReadResult) -> None:
    try:
        source_kind, current_tree = _capture_tree(result.source_path, result.limits)
        if source_kind != result.source_kind or current_tree != result.tree_snapshot:
            raise GenericAgentReadError("source_snapshot_changed")
        for source_file in result.files:
            if _hash_regular_file(source_file.path, result.limits.max_file_bytes) != source_file.sha256:
                raise GenericAgentReadError("source_snapshot_changed")
            if source_file.source_format == "sqlite":
                _assert_sqlite_self_contained(source_file.path)
    except GenericAgentReadError as exc:
        if exc.code == "source_snapshot_changed":
            raise
        raise GenericAgentReadError("source_snapshot_changed") from exc


@contextmanager
def generic_agent_export_guard(result: GenericAgentReadResult) -> Iterator[None]:
    verify_generic_agent_export_unchanged(result)
    try:
        yield
    finally:
        verify_generic_agent_export_unchanged(result)


__all__ = (
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "ENTRYPOINT_PATH",
    "MODEL_PATH",
    "SCHEMA_VERSION",
    "TASK_ID",
    "AdapterLimits",
    "GenericAgentReadError",
    "GenericAgentReadResult",
    "GenericAgentSourceFile",
    "GenericAgentSourceRecord",
    "generic_agent_export_guard",
    "load_generic_agent_read_contract",
    "read_generic_agent_export",
    "validate_generic_agent_read_contract",
    "verify_generic_agent_export_unchanged",
)
