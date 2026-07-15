"""Incremental, content-deduplicated Codex raw sync state for S07-P1-T3."""

from __future__ import annotations

import argparse
import fcntl
import gzip
import hashlib
import io
import json
import os
import re
import shutil
import stat
import tarfile
import tempfile
from collections import Counter
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, BinaryIO, Callable, Iterator, Mapping

from raw_archive_manifest import generate_raw_manifest, preflight_raw_ledger, read_jsonl

from .archive_chunking import MAX_PART_BYTES
from .codex_public_raw_archive import (
    ARCHIVE_ROOT,
    GZIP_COMPRESSLEVEL,
    GZIP_MTIME,
    MANIFEST_FILENAME,
    MAX_CONTRACT_BYTES,
    MAX_MANIFEST_BYTES,
    PACKAGE_MEMBER_ROOT,
    PART_INDEX_WIDTH,
    PARTS_DIRECTORY,
    PACKAGE_FORMAT,
    PUBLIC_INDEX_ROOT,
    READ_CHUNK_BYTES,
    README_FILENAME,
    RESTORE_FILENAME,
    SOURCE_MANIFEST_MEMBER,
    SPOOL_BYTES,
    CodexPublicRawArchiveError,
    SourceProof,
    _ChunkedPackageWriter,
    _add_bytes_member,
    _archive_lock,
    _canonical_json_bytes,
    _capture_proofs,
    _capture_quiescent_proofs,
    _compare_proofs,
    _ensure_archive_parent,
    _filter_inventory,
    _fsync_directory,
    _merge_counts,
    _partition_inflight_sources,
    _portable_archive_id as _t2_portable_archive_id,
    _proof_digest,
    _publish_staging,
    _read_regular_bytes as _t2_read_regular_bytes,
    _rebuild_sqlite,
    _resolve_inventory,
    _safe_public_text,
    _sanitize_jsonl,
    _tar_info,
    _verify_final_inventory_stat,
    _write_exclusive,
    verify_codex_public_raw_archive,
)
from .codex_source_discovery import CodexSourceInventory, discover_codex_sources
from .raw_ledger import SOURCE_STAT_FIELDS, RawLedgerError


CONTRACT_PATH = Path("config/data_sources/codex_sync_state.json")
STATE_PATH = Path("data/sync_state/codex.json")
SCHEMA_VERSION = "memory_atlas.codex_sync_state.v1_2_1_s07_p1_t3"
CONTRACT_SCHEMA_VERSION = "memory_atlas.codex_sync_state_contract.v1_2_1_s07_p1_t3"
ARCHIVE_MANIFEST_SCHEMA_VERSION = (
    "memory_atlas.codex_incremental_archive_manifest.v1_2_1_s07_p1_t3"
)
SOURCE_MANIFEST_SCHEMA_VERSION = (
    "memory_atlas.codex_incremental_source_manifest.v1_2_1_s07_p1_t3"
)
PUBLIC_INDEX_SCHEMA_VERSION = (
    "memory_atlas.codex_incremental_archive_index.v1_2_1_s07_p1_t3"
)
RESULT_SCHEMA_VERSION = "memory_atlas.codex_sync_state_result.v1_2_1_s07_p1_t3"
TASK_ID = "S07-P1-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P1-T3"
SOURCE_ID = "codex"
MAX_STATE_BYTES = 32 * 1024 * 1024
MAX_SOURCE_MANIFEST_BYTES = 16 * 1024 * 1024
SYNC_PHASES = (
    "PLANNED",
    "ARCHIVE_PUBLISHED",
    "PUBLIC_INDEX_PUBLISHED",
    "LEDGER_RECORDED",
)
EXPECTED_PHASE_BOUNDARY = {
    "does_not_build_derived": True,
    "does_not_commit_or_push": True,
    "does_not_deploy": True,
    "next_task": "S07-P2-T1",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_CONTRACT = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "state_path": STATE_PATH.as_posix(),
    "bootstrap": {
        "source_task_id": "S07-P1-T2",
        "strategy": "latest_verified_public_raw_archive",
        "requires_public_registration_before_first_incremental_write": True,
    },
    "cursor": {
        "identity_fields": ["source_kind", "relative_path"],
        "content_hash_algorithm": "sha256",
        "source_stat_fields": list(SOURCE_STAT_FIELDS),
        "inventory_digest_algorithm": "sha256",
        "portable_paths_only": True,
    },
    "deduplication": {
        "key": "source_sha256",
        "scope": "all_completed_codex_archives",
        "one_package_member_per_unique_content_hash": True,
        "path_aliases_restored_from_source_manifest": True,
        "no_archive_when_no_new_content_hash": True,
    },
    "resume": {
        "state_write": "atomic_replace_and_directory_fsync",
        "lock": "process_scoped_advisory_lock",
        "phases": list(SYNC_PHASES),
        "same_archive_id_required": True,
        "published_archive_reused_not_rewritten": True,
        "incomplete_staging_policy": "verify_marker_then_rebuild",
        "source_drift_policy": "fail_closed_keep_journal",
    },
    "append_only": {
        "archive_root": ARCHIVE_ROOT.as_posix(),
        "public_index_root": PUBLIC_INDEX_ROOT.as_posix(),
        "raw_ledger_required": True,
        "existing_archive_policy": "verify_or_fail_never_overwrite",
        "historical_state_content_index_retained": True,
    },
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}


class CodexSyncStateError(ValueError):
    """Path-free fail-closed error for the incremental state machine."""

    def __init__(
        self,
        code: str,
        *,
        writes_files: bool = False,
        archive_may_exist: bool = False,
        state_may_exist: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.writes_files = writes_files
        self.archive_may_exist = archive_may_exist
        self.state_may_exist = state_may_exist


def _now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _portable_archive_id(value: Any) -> str:
    try:
        return _t2_portable_archive_id(value)
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError(exc.code) from exc


def _read_regular_bytes(path: Path, *, max_bytes: int, code: str) -> bytes:
    try:
        return _t2_read_regular_bytes(path, max_bytes=max_bytes, code=code)
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError(code) from exc


def _safe_relative_path(value: Any, *, prefix: str | None = None) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or "\\" in value
        or "\x00" in value
    ):
        raise CodexSyncStateError("state_path_invalid")
    posix = PurePosixPath(value)
    windows = PureWindowsPath(value)
    if (
        posix.is_absolute()
        or windows.is_absolute()
        or bool(windows.drive)
        or value.startswith("//")
        or any(part in {"", ".", ".."} for part in posix.parts)
    ):
        raise CodexSyncStateError("state_path_invalid")
    if prefix is not None and not value.startswith(prefix):
        raise CodexSyncStateError("state_path_outside_scope")
    _safe_public_text(value)
    return value


def _require_sha256(value: Any) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise CodexSyncStateError("state_sha256_invalid")
    return value


def _read_json_file(path: Path, *, max_bytes: int, code: str) -> dict[str, Any]:
    try:
        payload = _read_regular_bytes(path, max_bytes=max_bytes, code=code)
        value = json.loads(payload.decode("utf-8"))
    except (CodexPublicRawArchiveError, OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSyncStateError(code) from exc
    if not isinstance(value, dict):
        raise CodexSyncStateError(code)
    return value


def validate_codex_sync_state_contract(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise CodexSyncStateError("sync_state_contract_drift")
    return dict(payload)


def load_codex_sync_state_contract(database_dir: Path) -> dict[str, Any]:
    payload = _read_json_file(
        database_dir.resolve() / CONTRACT_PATH,
        max_bytes=MAX_CONTRACT_BYTES,
        code="sync_state_contract_unreadable",
    )
    return validate_codex_sync_state_contract(payload)


def _validate_source_stat(value: Any) -> dict[str, int]:
    if not isinstance(value, dict) or set(value) != set(SOURCE_STAT_FIELDS):
        raise CodexSyncStateError("state_source_stat_invalid")
    result: dict[str, int] = {}
    for field in SOURCE_STAT_FIELDS:
        item = value.get(field)
        if not isinstance(item, int) or item < 0:
            raise CodexSyncStateError("state_source_stat_invalid")
        result[field] = item
    return result


def _validate_content_ref(content_hash: str, value: Any) -> dict[str, Any]:
    _require_sha256(content_hash)
    if not isinstance(value, dict):
        raise CodexSyncStateError("state_content_index_invalid")
    required = {
        "archive_id",
        "archive_member",
        "first_seen_path",
        "source_kind",
        "source_size_bytes",
    }
    if set(value) != required:
        raise CodexSyncStateError("state_content_index_invalid")
    _portable_archive_id(value.get("archive_id"))
    _safe_relative_path(value.get("archive_member"), prefix="codex/")
    _safe_relative_path(value.get("first_seen_path"))
    if not isinstance(value.get("source_kind"), str) or not value["source_kind"]:
        raise CodexSyncStateError("state_content_index_invalid")
    if not isinstance(value.get("source_size_bytes"), int) or value["source_size_bytes"] < 0:
        raise CodexSyncStateError("state_content_index_invalid")
    return dict(value)


def _validate_cursor_path(
    relative_path: str,
    value: Any,
    content_index: dict[str, Any],
) -> dict[str, Any]:
    _safe_relative_path(relative_path)
    if not isinstance(value, dict) or set(value) != {
        "archive_id",
        "archive_member",
        "source_kind",
        "source_sha256",
        "source_size_bytes",
        "source_stat",
    }:
        raise CodexSyncStateError("state_cursor_path_invalid")
    content_hash = _require_sha256(value.get("source_sha256"))
    if content_hash not in content_index:
        raise CodexSyncStateError("state_cursor_content_missing")
    _portable_archive_id(value.get("archive_id"))
    _safe_relative_path(value.get("archive_member"), prefix="codex/")
    if not isinstance(value.get("source_kind"), str) or not value["source_kind"]:
        raise CodexSyncStateError("state_cursor_path_invalid")
    if not isinstance(value.get("source_size_bytes"), int) or value["source_size_bytes"] < 0:
        raise CodexSyncStateError("state_cursor_path_invalid")
    _validate_source_stat(value.get("source_stat"))
    reference = content_index[content_hash]
    if (
        value["archive_id"] != reference["archive_id"]
        or value["archive_member"] != reference["archive_member"]
        or value["source_size_bytes"] != reference["source_size_bytes"]
    ):
        raise CodexSyncStateError("state_cursor_reference_mismatch")
    return dict(value)


def _validate_deferred(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        raise CodexSyncStateError("state_deferred_invalid")
    result: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, dict) or set(item) != {
            "hash_stat_claim",
            "reason",
            "relative_path",
            "source_kind",
            "stat",
        }:
            raise CodexSyncStateError("state_deferred_invalid")
        _safe_relative_path(item.get("relative_path"))
        _validate_source_stat(item.get("stat"))
        if item.get("hash_stat_claim") is not False:
            raise CodexSyncStateError("state_deferred_invalid")
        result.append(dict(item))
    return result


def validate_codex_sync_state(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "state_path",
        "revision",
        "bootstrap",
        "cursor",
        "content_index",
        "active_run",
        "last_result",
        "phase_boundary",
    }:
        raise CodexSyncStateError("sync_state_shape_invalid")
    if (
        payload.get("schema_version") != SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != SOURCE_ID
        or payload.get("state_path") != STATE_PATH.as_posix()
        or payload.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
    ):
        raise CodexSyncStateError("sync_state_identity_invalid")
    if not isinstance(payload.get("revision"), int) or payload["revision"] < 0:
        raise CodexSyncStateError("sync_state_revision_invalid")
    bootstrap = payload.get("bootstrap")
    if not isinstance(bootstrap, dict) or set(bootstrap) != {
        "archive_id",
        "archive_manifest_sha256",
        "content_count",
        "source_file_count",
        "source_inventory_sha256",
    }:
        raise CodexSyncStateError("sync_state_bootstrap_invalid")
    _portable_archive_id(bootstrap.get("archive_id"))
    _require_sha256(bootstrap.get("archive_manifest_sha256"))
    _require_sha256(bootstrap.get("source_inventory_sha256"))
    if any(not isinstance(bootstrap.get(key), int) or bootstrap[key] < 0 for key in ("content_count", "source_file_count")):
        raise CodexSyncStateError("sync_state_bootstrap_invalid")

    content_index = payload.get("content_index")
    if not isinstance(content_index, dict):
        raise CodexSyncStateError("state_content_index_invalid")
    for content_hash, reference in content_index.items():
        _validate_content_ref(content_hash, reference)

    cursor = payload.get("cursor")
    if not isinstance(cursor, dict) or set(cursor) != {
        "sequence",
        "inventory_sha256",
        "stable_file_count",
        "source_total_bytes",
        "deferred_inflight_sources",
        "paths",
    }:
        raise CodexSyncStateError("state_cursor_invalid")
    if not isinstance(cursor.get("sequence"), int) or cursor["sequence"] < 0:
        raise CodexSyncStateError("state_cursor_invalid")
    _require_sha256(cursor.get("inventory_sha256"))
    if any(not isinstance(cursor.get(key), int) or cursor[key] < 0 for key in ("stable_file_count", "source_total_bytes")):
        raise CodexSyncStateError("state_cursor_invalid")
    _validate_deferred(cursor.get("deferred_inflight_sources"))
    paths = cursor.get("paths")
    if not isinstance(paths, dict) or len(paths) != cursor["stable_file_count"]:
        raise CodexSyncStateError("state_cursor_path_count_invalid")
    for relative_path, value in paths.items():
        _validate_cursor_path(relative_path, value, content_index)

    active = payload.get("active_run")
    if active is not None:
        if not isinstance(active, dict) or active.get("phase") not in SYNC_PHASES:
            raise CodexSyncStateError("state_active_run_invalid")
        _portable_archive_id(active.get("archive_id"))
        _require_sha256(active.get("inventory_sha256"))
        if not isinstance(active.get("inventory"), list) or not active["inventory"]:
            raise CodexSyncStateError("state_active_run_invalid")
        if not isinstance(active.get("objects"), dict) or not active["objects"]:
            raise CodexSyncStateError("state_active_run_invalid")
        _validate_deferred(active.get("deferred_inflight_sources"))
    if payload.get("last_result") is not None and not isinstance(payload["last_result"], dict):
        raise CodexSyncStateError("state_last_result_invalid")
    return payload


def _load_state(database_dir: Path) -> dict[str, Any] | None:
    path = database_dir / STATE_PATH
    if not os.path.lexists(path):
        return None
    payload = _read_json_file(path, max_bytes=MAX_STATE_BYTES, code="sync_state_unreadable")
    return validate_codex_sync_state(payload)


def _atomic_write_state(database_dir: Path, state_payload: dict[str, Any]) -> None:
    validate_codex_sync_state(state_payload)
    path = database_dir / STATE_PATH
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir():
        raise CodexSyncStateError("sync_state_parent_unsafe")
    if os.path.lexists(path):
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise CodexSyncStateError("sync_state_target_unsafe")
    temp_path = parent / f".{path.name}.{os.getpid()}.{os.urandom(6).hex()}.tmp"
    try:
        _write_exclusive(temp_path, _canonical_json_bytes(state_payload), mode=0o600)
        os.replace(temp_path, path)
        _fsync_directory(parent)
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError("sync_state_write_failed", writes_files=True, state_may_exist=True) from exc
    finally:
        if temp_path.exists():
            temp_path.unlink()


@contextmanager
def _sync_lock(database_dir: Path) -> Iterator[None]:
    identity = hashlib.sha256(str(database_dir.resolve()).encode("utf-8")).hexdigest()[:24]
    lock_path = Path(tempfile.gettempdir()) / f"memory-atlas-codex-sync-{identity}.lock"
    handle = lock_path.open("a+b")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CodexSyncStateError("sync_state_lock_busy") from exc
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


class _MultipartReader(io.RawIOBase):
    def __init__(self, paths: list[Path]) -> None:
        super().__init__()
        self._paths = paths
        self._index = 0
        self._handle: BinaryIO | None = None

    def readable(self) -> bool:
        return True

    def readinto(self, buffer: bytearray | memoryview) -> int:
        view = memoryview(buffer)
        total = 0
        while total < len(view):
            if self._handle is None:
                if self._index >= len(self._paths):
                    break
                self._handle = self._paths[self._index].open("rb")
                self._index += 1
            count = self._handle.readinto(view[total:])
            if count:
                total += count
                continue
            self._handle.close()
            self._handle = None
        return total

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None
        super().close()


def _part_paths(database_dir: Path, archive_id: str, manifest: dict[str, Any]) -> list[Path]:
    parts = manifest.get("parts")
    if not isinstance(parts, list) or not parts:
        raise CodexSyncStateError("incremental_archive_parts_invalid")
    result: list[Path] = []
    for index, item in enumerate(parts):
        if not isinstance(item, dict) or set(item) != {"index", "filename", "byte_size", "sha256"}:
            raise CodexSyncStateError("incremental_archive_parts_invalid")
        expected_name = f"{PARTS_DIRECTORY}/{archive_id}.tar.gz.part-{index:0{PART_INDEX_WIDTH}d}"
        if item.get("index") != index or item.get("filename") != expected_name:
            raise CodexSyncStateError("incremental_archive_parts_invalid")
        _require_sha256(item.get("sha256"))
        if not isinstance(item.get("byte_size"), int) or item["byte_size"] <= 0:
            raise CodexSyncStateError("incremental_archive_parts_invalid")
        result.append(database_dir / ARCHIVE_ROOT / archive_id / expected_name)
    return result


def _read_package_source_manifest(
    database_dir: Path,
    archive_id: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    paths = _part_paths(database_dir, archive_id, manifest)
    try:
        with _MultipartReader(paths) as reader:
            with tarfile.open(fileobj=reader, mode="r|gz") as archive:
                for member in archive:
                    if member.name != SOURCE_MANIFEST_MEMBER:
                        continue
                    if not member.isfile() or member.size > MAX_SOURCE_MANIFEST_BYTES:
                        raise CodexSyncStateError("source_manifest_invalid")
                    handle = archive.extractfile(member)
                    if handle is None:
                        raise CodexSyncStateError("source_manifest_invalid")
                    payload = handle.read(MAX_SOURCE_MANIFEST_BYTES + 1)
                    if len(payload) != member.size:
                        raise CodexSyncStateError("source_manifest_invalid")
                    value = json.loads(payload.decode("utf-8"))
                    if not isinstance(value, dict):
                        raise CodexSyncStateError("source_manifest_invalid")
                    return value
    except (OSError, tarfile.TarError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSyncStateError("source_manifest_unreadable") from exc
    raise CodexSyncStateError("source_manifest_missing")


def _bootstrap_state(database_dir: Path) -> dict[str, Any]:
    archive_root = database_dir / ARCHIVE_ROOT
    candidates: list[tuple[str, str, dict[str, Any]]] = []
    if archive_root.is_dir() and not archive_root.is_symlink():
        for path in archive_root.iterdir():
            manifest_path = path / MANIFEST_FILENAME
            if path.is_symlink() or not path.is_dir() or not manifest_path.is_file():
                continue
            try:
                manifest = _read_json_file(
                    manifest_path,
                    max_bytes=MAX_MANIFEST_BYTES,
                    code="bootstrap_manifest_unreadable",
                )
            except CodexSyncStateError:
                continue
            if manifest.get("task_id") == "S07-P1-T2" and manifest.get("source_id") == SOURCE_ID:
                candidates.append((str(manifest.get("recorded_at_utc") or ""), path.name, manifest))
    if not candidates:
        raise CodexSyncStateError("bootstrap_archive_not_found")
    _recorded_at, archive_id, manifest = max(candidates)
    try:
        verification = verify_codex_public_raw_archive(database_dir, archive_id)
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError("bootstrap_archive_not_verified") from exc
    source_manifest = _read_package_source_manifest(database_dir, archive_id, manifest)
    if (
        source_manifest.get("task_id") != "S07-P1-T2"
        or source_manifest.get("source_id") != SOURCE_ID
        or source_manifest.get("archive_id") != archive_id
        or not isinstance(source_manifest.get("files"), list)
    ):
        raise CodexSyncStateError("bootstrap_source_manifest_invalid")

    content_index: dict[str, dict[str, Any]] = {}
    source_rows: list[dict[str, Any]] = []
    for item in source_manifest["files"]:
        if not isinstance(item, dict):
            raise CodexSyncStateError("bootstrap_source_manifest_invalid")
        relative_path = _safe_relative_path(item.get("source_relative_path"))
        source_hash = _require_sha256(item.get("source_sha256"))
        archive_member = _safe_relative_path(item.get("archive_member"), prefix="codex/")
        source_stat = _validate_source_stat(item.get("source_stat"))
        source_kind = str(item.get("source_kind") or "")
        source_size = item.get("source_size_bytes")
        if not source_kind or not isinstance(source_size, int) or source_size < 0:
            raise CodexSyncStateError("bootstrap_source_manifest_invalid")
        content_index.setdefault(
            source_hash,
            {
                "archive_id": archive_id,
                "archive_member": archive_member,
                "first_seen_path": relative_path,
                "source_kind": source_kind,
                "source_size_bytes": source_size,
            },
        )
        source_rows.append(
            {
                "relative_path": relative_path,
                "source_kind": source_kind,
                "source_sha256": source_hash,
                "source_size_bytes": source_size,
                "source_stat": source_stat,
            }
        )
    source_rows.sort(key=lambda row: str(row["relative_path"]))
    paths = _cursor_paths(source_rows, content_index)
    proof = source_manifest.get("source_proof")
    if not isinstance(proof, dict):
        raise CodexSyncStateError("bootstrap_source_manifest_invalid")
    inventory_sha256 = _require_sha256(proof.get("before_sha256"))
    deferred = _validate_deferred(source_manifest.get("deferred_inflight_sources"))
    state_payload = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "state_path": STATE_PATH.as_posix(),
        "revision": 0,
        "bootstrap": {
            "archive_id": archive_id,
            "archive_manifest_sha256": verification["manifest_sha256"],
            "content_count": len(content_index),
            "source_file_count": len(source_rows),
            "source_inventory_sha256": inventory_sha256,
        },
        "cursor": {
            "sequence": 0,
            "inventory_sha256": inventory_sha256,
            "stable_file_count": len(source_rows),
            "source_total_bytes": sum(int(row["source_size_bytes"]) for row in source_rows),
            "deferred_inflight_sources": deferred,
            "paths": paths,
        },
        "content_index": content_index,
        "active_run": None,
        "last_result": None,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    return validate_codex_sync_state(state_payload)


def _proof_record(proof: SourceProof) -> dict[str, Any]:
    return {
        "relative_path": proof.relative_path,
        "source_kind": proof.source_kind,
        "source_sha256": proof.sha256,
        "source_size_bytes": proof.stat.size_bytes,
        "source_stat": {
            field: int(getattr(proof.stat, field)) for field in SOURCE_STAT_FIELDS
        },
    }


def _cursor_paths(
    source_rows: list[dict[str, Any]],
    content_index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for row in source_rows:
        content_hash = str(row["source_sha256"])
        reference = content_index.get(content_hash)
        if reference is None:
            raise CodexSyncStateError("cursor_content_reference_missing")
        result[str(row["relative_path"])] = {
            "archive_id": reference["archive_id"],
            "archive_member": reference["archive_member"],
            "source_kind": row["source_kind"],
            "source_sha256": content_hash,
            "source_size_bytes": row["source_size_bytes"],
            "source_stat": row["source_stat"],
        }
    return dict(sorted(result.items()))


def _current_inventory(
    database_dir: Path,
    *,
    operator_codex_home: Path | None,
    environ: Mapping[str, str] | None,
    home: Path | None,
) -> tuple[
    dict[str, Any],
    dict[str, Any],
    CodexSourceInventory,
    tuple[SourceProof, ...],
    tuple[dict[str, Any], ...],
    int,
    int,
]:
    discovery, credential, discovered = _resolve_inventory(
        database_dir,
        operator_codex_home=operator_codex_home,
        environ=environ,
        home=home,
    )
    discovered_count = len(discovered.files)
    discovered_bytes = sum(item.size_bytes for item in discovered.files)
    stable, deferred = _partition_inflight_sources(discovered)
    stable, proofs, deferred = _capture_quiescent_proofs(
        stable,
        discovery,
        credential,
        deferred,
    )
    return discovery, credential, stable, proofs, deferred, discovered_count, discovered_bytes


def _deferred_payload(deferred: tuple[dict[str, Any], ...]) -> list[dict[str, Any]]:
    return [dict(item) for item in deferred]


def _cursor_matches(
    state_payload: dict[str, Any],
    inventory_sha256: str,
    deferred: list[dict[str, Any]],
) -> bool:
    cursor = state_payload["cursor"]
    return (
        cursor["inventory_sha256"] == inventory_sha256
        and cursor["deferred_inflight_sources"] == deferred
    )


def _objects_for_new_content(
    source_rows: list[dict[str, Any]],
    content_index: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in source_rows:
        content_hash = str(row["source_sha256"])
        if content_hash not in content_index:
            grouped.setdefault(content_hash, []).append(row)
    result: dict[str, dict[str, Any]] = {}
    for content_hash, rows in sorted(grouped.items()):
        ordered = sorted(rows, key=lambda item: str(item["relative_path"]))
        canonical = ordered[0]
        result[content_hash] = {
            "canonical_path": canonical["relative_path"],
            "source_kind": canonical["source_kind"],
            "source_size_bytes": canonical["source_size_bytes"],
            "source_stat": canonical["source_stat"],
            "paths": [row["relative_path"] for row in ordered],
        }
    return result


def _checkpoint(
    database_dir: Path,
    state_payload: dict[str, Any],
    phase: str,
    updates: dict[str, Any] | None,
    hook: Callable[[str], None] | None,
) -> None:
    active = state_payload["active_run"]
    if not isinstance(active, dict):
        raise CodexSyncStateError("active_run_missing")
    active["phase"] = phase
    if updates:
        active.update(updates)
    state_payload["revision"] += 1
    _atomic_write_state(database_dir, state_payload)
    if hook is not None:
        hook(phase)


def _source_manifest_payload(
    active: dict[str, Any],
    archive_objects: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    files: list[dict[str, Any]] = []
    inventory_by_path = {str(item["relative_path"]): item for item in active["inventory"]}
    for content_hash, planned in sorted(active["objects"].items()):
        archive_object = archive_objects[content_hash]
        for relative_path in planned["paths"]:
            source = inventory_by_path[str(relative_path)]
            files.append(
                {
                    "source_kind": source["source_kind"],
                    "source_relative_path": relative_path,
                    "source_sha256": content_hash,
                    "source_size_bytes": source["source_size_bytes"],
                    "source_stat": source["source_stat"],
                    "archive_member": archive_object["archive_member"],
                }
            )
    return {
        "schema_version": SOURCE_MANIFEST_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": active["archive_id"],
        "source_proof": {
            "hash_algorithm": "sha256",
            "stat_fields": list(SOURCE_STAT_FIELDS),
            "stable_file_count": len(active["inventory"]),
            "source_total_bytes": sum(int(row["source_size_bytes"]) for row in active["inventory"]),
            "before_sha256": active["inventory_sha256"],
            "after_sha256": active["inventory_sha256"],
            "hash_stat_equal": True,
            "source_mutation": False,
        },
        "deduplication": {
            "new_path_count": sum(len(item["paths"]) for item in active["objects"].values()),
            "unique_content_count": len(active["objects"]),
            "key": "source_sha256",
        },
        "objects": archive_objects,
        "files": sorted(files, key=lambda item: str(item["source_relative_path"])),
        "deferred_inflight_sources": active["deferred_inflight_sources"],
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _build_incremental_package(
    staging: Path,
    active: dict[str, Any],
    inventory: CodexSourceInventory,
    discovery_contract: dict[str, Any],
    credential_contract: dict[str, Any],
    before: tuple[SourceProof, ...],
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any]]:
    archive_id = str(active["archive_id"])
    item_by_path = {item.relative_path: item for item in inventory.files}
    proof_by_path = {proof.relative_path: proof for proof in before}
    parts_dir = staging / PARTS_DIRECTORY
    work_dir = staging / ".work"
    parts_dir.mkdir(mode=0o700)
    work_dir.mkdir(mode=0o700)
    writer = _ChunkedPackageWriter(parts_dir, archive_id)
    archive_objects: dict[str, dict[str, Any]] = {}
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
            with tarfile.open(fileobj=compressed, mode="w|", format=tarfile.PAX_FORMAT) as archive:
                for index, (content_hash, planned) in enumerate(sorted(active["objects"].items())):
                    relative_path = str(planned["canonical_path"])
                    item = item_by_path.get(relative_path)
                    proof = proof_by_path.get(relative_path)
                    if item is None or proof is None or proof.sha256 != content_hash:
                        raise CodexSyncStateError("active_run_source_changed")
                    member_name = f"{PACKAGE_MEMBER_ROOT}/{relative_path}"
                    if item.source_kind == "sqlite_logs":
                        output = work_dir / f"sqlite-{index:06d}.sqlite"
                        transformed = _rebuild_sqlite(item, proof.stat, output)
                        with output.open("rb") as handle:
                            archive.addfile(_tar_info(member_name, int(transformed["archive_size_bytes"])), handle)
                        output.unlink()
                    else:
                        with tempfile.SpooledTemporaryFile(
                            max_size=SPOOL_BYTES,
                            mode="w+b",
                            dir=work_dir,
                        ) as handle:
                            transformed = _sanitize_jsonl(item, proof.stat, handle)
                            handle.seek(0)
                            archive.addfile(_tar_info(member_name, int(transformed["archive_size_bytes"])), handle)
                    _merge_counts(aggregate_redactions, transformed.get("redaction_counts", {}))
                    archive_objects[content_hash] = {
                        "archive_member": member_name,
                        "archive_sha256": transformed["archive_sha256"],
                        "archive_size_bytes": transformed["archive_size_bytes"],
                        "canonical_path": relative_path,
                        "record_count": transformed["record_count"],
                        "source_kind": proof.source_kind,
                        "source_sha256": proof.sha256,
                        "source_size_bytes": proof.stat.size_bytes,
                        "transformation": transformed["transformation"],
                    }

                rediscovered = discover_codex_sources(
                    inventory.root,
                    discovery_contract,
                    credential_contract,
                )
                excluded = frozenset(
                    str(item["relative_path"])
                    for item in active["deferred_inflight_sources"]
                )
                rediscovered = _filter_inventory(rediscovered, excluded)
                after = _capture_proofs(rediscovered)
                _compare_proofs(before, after)
                source_manifest = _source_manifest_payload(active, archive_objects)
                _add_bytes_member(archive, SOURCE_MANIFEST_MEMBER, _canonical_json_bytes(source_manifest))
                _add_bytes_member(
                    archive,
                    "codex/_memory_atlas/README.md",
                    (
                        "# Codex Incremental Public Raw Package\n\n"
                        "Content is keyed by source SHA-256. Path aliases are listed in "
                        "source_manifest.json and restored without duplicate package members.\n"
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
        raise CodexSyncStateError("source_post_proof_missing")
    excluded = frozenset(
        str(item["relative_path"]) for item in active["deferred_inflight_sources"]
    )
    _verify_final_inventory_stat(
        inventory,
        discovery_contract,
        credential_contract,
        after,
        excluded,
    )
    package.update(
        {
            "member_count": len(archive_objects) + 2,
            "redaction_counts": dict(sorted(aggregate_redactions.items())),
        }
    )
    return package, parts, source_manifest


def _archive_manifest(
    active: dict[str, Any],
    package: dict[str, Any],
    parts: list[dict[str, Any]],
    source_manifest: dict[str, Any],
) -> dict[str, Any]:
    archive_id = str(active["archive_id"])
    return {
        "schema_version": ARCHIVE_MANIFEST_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / archive_id).as_posix(),
        "recorded_at_utc": active["started_at_utc"],
        "source_proof": source_manifest["source_proof"],
        "deduplication": source_manifest["deduplication"],
        "objects": source_manifest["objects"],
        "package": {
            key: package[key]
            for key in ("filename", "format", "byte_size", "sha256", "member_count")
        },
        "split": {
            "method": "fixed_bytes",
            "max_part_bytes": 45 * 1024 * 1024,
            "part_index_width": PART_INDEX_WIDTH,
            "part_count": len(parts),
        },
        "parts": parts,
        "redaction_counts": package["redaction_counts"],
        "restore": {
            "script": RESTORE_FILENAME,
            "output_no_overwrite": True,
            "source_manifest_member": SOURCE_MANIFEST_MEMBER,
            "path_aliases_restored": True,
        },
        "public_index": {
            "root": PUBLIC_INDEX_ROOT.as_posix(),
            "append_only": True,
            "raw_ledger_required": True,
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _readme(archive_id: str, manifest: dict[str, Any]) -> bytes:
    return (
        "# Codex Incremental Public Raw Archive\n\n"
        f"Archive ID: `{archive_id}`\n\n"
        f"New paths: `{manifest['deduplication']['new_path_count']}`\n\n"
        f"Unique content objects: `{manifest['deduplication']['unique_content_count']}`\n"
    ).encode("utf-8")


def _restore_script(archive_id: str, package_sha256: str, member_count: int) -> bytes:
    return f'''#!/usr/bin/env bash
set -euo pipefail
if [[ $# -ne 1 ]]; then echo "usage: ./restore.sh OUTPUT_DIRECTORY" >&2; exit 2; fi
script_dir="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
output="$1"
if [[ -e "$output" || -L "$output" ]]; then echo "restore output already exists" >&2; exit 3; fi
staging="${{output}}.restore-{archive_id}-$$"
if [[ -e "$staging" || -L "$staging" ]]; then echo "restore staging path already exists" >&2; exit 3; fi
mkdir "$staging"
cleanup() {{ rm -rf "$staging"; }}
trap cleanup EXIT
package="$staging/.{archive_id}.tar.gz"
cat "$script_dir"/parts/{archive_id}.tar.gz.part-* > "$package"
actual="$(shasum -a 256 "$package" | awk '{{print $1}}')"
if [[ "$actual" != "{package_sha256}" ]]; then echo "restored package SHA-256 mismatch" >&2; exit 4; fi
python3 - "$package" "$staging" <<'PY'
import json
import os
import shutil
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
        if (not name or "\\\\" in name or "\\x00" in name or parts[0] != "codex"
                or any(part in {{"", ".", ".."}} for part in parts) or not member.isfile()):
            raise SystemExit("unsafe archive member")
        target = os.path.realpath(os.path.join(output, *parts))
        if os.path.commonpath([output, target]) != output:
            raise SystemExit("unsafe archive member")
        names.append(name)
    if len(members) != {member_count} or len(names) != len(set(names)) or "{SOURCE_MANIFEST_MEMBER}" not in names:
        raise SystemExit("archive member inventory mismatch")
    archive.extractall(output, members=members)
manifest_path = os.path.join(output, *"{SOURCE_MANIFEST_MEMBER}".split("/"))
with open(manifest_path, "r", encoding="utf-8") as handle:
    manifest = json.load(handle)
for item in manifest.get("files", []):
    relative = item.get("source_relative_path", "")
    member = item.get("archive_member", "")
    relative_parts = relative.split("/")
    member_parts = member.split("/")
    if (not relative or not member or any(part in {{"", ".", ".."}} for part in relative_parts)
            or any(part in {{"", ".", ".."}} for part in member_parts) or member_parts[0] != "codex"):
        raise SystemExit("unsafe source alias")
    target = os.path.realpath(os.path.join(output, "codex", *relative_parts))
    source = os.path.realpath(os.path.join(output, *member_parts))
    if os.path.commonpath([output, target]) != output or os.path.commonpath([output, source]) != output:
        raise SystemExit("unsafe source alias")
    if target == source:
        continue
    if os.path.lexists(target):
        raise SystemExit("source alias conflict")
    os.makedirs(os.path.dirname(target), exist_ok=True)
    try:
        os.link(source, target)
    except OSError:
        shutil.copyfile(source, target)
PY
rm "$package"
mv "$staging" "$output"
trap - EXIT
echo "PASS {package_sha256}"
'''.encode("utf-8")


def _prepare_staging(
    staging: Path,
    active: dict[str, Any],
    package: dict[str, Any],
    parts: list[dict[str, Any]],
    source_manifest: dict[str, Any],
) -> dict[str, Any]:
    manifest = _archive_manifest(active, package, parts, source_manifest)
    archive_id = str(active["archive_id"])
    _write_exclusive(
        staging / README_FILENAME,
        _readme(archive_id, manifest),
        mode=0o644,
    )
    _write_exclusive(
        staging / RESTORE_FILENAME,
        _restore_script(archive_id, str(package["sha256"]), int(package["member_count"])),
        mode=0o700,
    )
    _write_exclusive(staging / MANIFEST_FILENAME, _canonical_json_bytes(manifest), mode=0o600)
    _fsync_directory(staging / PARTS_DIRECTORY)
    _fsync_directory(staging)
    return manifest


def _staging_path(parent: Path, archive_id: str) -> Path:
    return parent / f".{archive_id}.t3-staging"


def _prepare_clean_staging(parent: Path, active: dict[str, Any]) -> Path:
    archive_id = str(active["archive_id"])
    staging = _staging_path(parent, archive_id)
    marker_name = ".t3-staging.json"
    if os.path.lexists(staging):
        if staging.is_symlink() or not staging.is_dir():
            raise CodexSyncStateError("incremental_staging_unsafe")
        marker = _read_json_file(
            staging / marker_name,
            max_bytes=MAX_CONTRACT_BYTES,
            code="incremental_staging_marker_invalid",
        )
        if marker != {
            "archive_id": archive_id,
            "inventory_sha256": active["inventory_sha256"],
            "task_id": TASK_ID,
        }:
            raise CodexSyncStateError("incremental_staging_marker_invalid")
        shutil.rmtree(staging)
    staging.mkdir(mode=0o700)
    _write_exclusive(
        staging / marker_name,
        _canonical_json_bytes(
            {
                "archive_id": archive_id,
                "inventory_sha256": active["inventory_sha256"],
                "task_id": TASK_ID,
            }
        ),
    )
    return staging


def _public_index_payload(manifest: dict[str, Any], manifest_sha256: str) -> dict[str, Any]:
    return {
        "schema_version": PUBLIC_INDEX_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": manifest["archive_id"],
        "archive_path": manifest["archive_path"],
        "archive_manifest_sha256": manifest_sha256,
        "package_sha256": manifest["package"]["sha256"],
        "package_bytes": manifest["package"]["byte_size"],
        "part_count": manifest["split"]["part_count"],
        "new_path_count": manifest["deduplication"]["new_path_count"],
        "unique_content_count": manifest["deduplication"]["unique_content_count"],
        "source_before_sha256": manifest["source_proof"]["before_sha256"],
        "source_after_sha256": manifest["source_proof"]["after_sha256"],
        "source_hash_stat_equal": manifest["source_proof"]["hash_stat_equal"],
        "dedupe_key": "source_sha256",
        "credential_values_public": False,
        "local_absolute_paths_public": False,
        "raw_ledger_required": True,
        "source_mutation": False,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _public_index_relative(archive_id: str, manifest_sha256: str) -> Path:
    return PUBLIC_INDEX_ROOT / f"codex_incremental_archive.{archive_id}.{manifest_sha256[:12]}.json"


def _write_or_verify_public_index(
    database_dir: Path,
    manifest: dict[str, Any],
    manifest_sha256: str,
) -> Path:
    relative = _public_index_relative(str(manifest["archive_id"]), manifest_sha256)
    path = database_dir / relative
    payload = _canonical_json_bytes(_public_index_payload(manifest, manifest_sha256))
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        existing = _read_regular_bytes(
            path,
            max_bytes=MAX_CONTRACT_BYTES,
            code="incremental_public_index_unreadable",
        )
        if existing != payload:
            raise CodexSyncStateError("incremental_public_index_conflict")
        return relative
    try:
        _write_exclusive(path, payload, mode=0o600)
        _fsync_directory(path.parent)
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError("incremental_public_index_write_failed", writes_files=True, archive_may_exist=True) from exc
    return relative


def _manifest_is_ledger_prefix(manifest_bytes: bytes, ledger_bytes: bytes) -> bool:
    return ledger_bytes.startswith(manifest_bytes) and (
        not manifest_bytes or manifest_bytes.endswith(b"\n")
    )


def verify_codex_incremental_archive(
    database_dir: Path,
    archive_id: str,
    *,
    require_public_registration: bool = True,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    archive_id = _portable_archive_id(archive_id)
    archive_path = database_dir / ARCHIVE_ROOT / archive_id
    if archive_path.is_symlink() or not archive_path.is_dir():
        raise CodexSyncStateError("incremental_archive_missing")
    expected_root = {PARTS_DIRECTORY, MANIFEST_FILENAME, README_FILENAME, RESTORE_FILENAME}
    if {path.name for path in archive_path.iterdir()} != expected_root:
        raise CodexSyncStateError("incremental_archive_root_inventory_mismatch")
    manifest_bytes = _read_regular_bytes(
        archive_path / MANIFEST_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="incremental_archive_manifest_unreadable",
    )
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSyncStateError("incremental_archive_manifest_invalid") from exc
    expected_manifest_keys = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "archive_id",
        "archive_path",
        "recorded_at_utc",
        "source_proof",
        "deduplication",
        "objects",
        "package",
        "split",
        "parts",
        "redaction_counts",
        "restore",
        "public_index",
        "phase_boundary",
    }
    if (
        not isinstance(manifest, dict)
        or set(manifest) != expected_manifest_keys
        or manifest.get("schema_version") != ARCHIVE_MANIFEST_SCHEMA_VERSION
        or manifest.get("task_id") != TASK_ID
        or manifest.get("acceptance_id") != ACCEPTANCE_ID
        or manifest.get("source_id") != SOURCE_ID
        or manifest.get("archive_id") != archive_id
        or manifest.get("archive_path") != (ARCHIVE_ROOT / archive_id).as_posix()
        or manifest.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
        or manifest.get("restore")
        != {
            "script": RESTORE_FILENAME,
            "output_no_overwrite": True,
            "source_manifest_member": SOURCE_MANIFEST_MEMBER,
            "path_aliases_restored": True,
        }
        or manifest.get("public_index")
        != {
            "root": PUBLIC_INDEX_ROOT.as_posix(),
            "append_only": True,
            "raw_ledger_required": True,
        }
    ):
        raise CodexSyncStateError("incremental_archive_manifest_identity_invalid")
    manifest_sha256 = _sha256_bytes(manifest_bytes)
    parts_dir = archive_path / PARTS_DIRECTORY
    if parts_dir.is_symlink() or not parts_dir.is_dir():
        raise CodexSyncStateError("incremental_archive_parts_unsafe")
    part_paths = _part_paths(database_dir, archive_id, manifest)
    split = manifest.get("split")
    if split != {
        "method": "fixed_bytes",
        "max_part_bytes": MAX_PART_BYTES,
        "part_index_width": PART_INDEX_WIDTH,
        "part_count": len(part_paths),
    }:
        raise CodexSyncStateError("incremental_archive_split_invalid")
    if {path.name for path in parts_dir.iterdir()} != {path.name for path in part_paths}:
        raise CodexSyncStateError("incremental_archive_part_inventory_mismatch")
    package_digest = hashlib.sha256()
    package_bytes = 0
    for path, expected in zip(part_paths, manifest["parts"], strict=True):
        if path.is_symlink() or not path.is_file():
            raise CodexSyncStateError("incremental_archive_part_unsafe")
        try:
            fingerprint = hashlib.sha256()
            size = 0
            with path.open("rb") as handle:
                while chunk := handle.read(READ_CHUNK_BYTES):
                    fingerprint.update(chunk)
                    package_digest.update(chunk)
                    size += len(chunk)
                    package_bytes += len(chunk)
        except OSError as exc:
            raise CodexSyncStateError("incremental_archive_part_unreadable") from exc
        if (
            size != expected["byte_size"]
            or fingerprint.hexdigest() != expected["sha256"]
            or size > MAX_PART_BYTES
        ):
            raise CodexSyncStateError("incremental_archive_part_hash_or_size_mismatch")
    package = manifest.get("package")
    if (
        not isinstance(package, dict)
        or set(package) != {"filename", "format", "byte_size", "sha256", "member_count"}
        or package.get("filename") != f"{archive_id}.tar.gz"
        or package.get("format") != PACKAGE_FORMAT
        or package.get("sha256") != package_digest.hexdigest()
        or package.get("byte_size") != package_bytes
        or package.get("member_count") != len(manifest.get("objects", {})) + 2
    ):
        raise CodexSyncStateError("incremental_archive_package_mismatch")

    objects = manifest.get("objects")
    if not isinstance(objects, dict) or not objects:
        raise CodexSyncStateError("incremental_archive_objects_invalid")
    deduplication = manifest.get("deduplication")
    if (
        not isinstance(deduplication, dict)
        or set(deduplication) != {"new_path_count", "unique_content_count", "key"}
        or deduplication.get("key") != "source_sha256"
        or deduplication.get("unique_content_count") != len(objects)
        or not isinstance(deduplication.get("new_path_count"), int)
        or deduplication["new_path_count"] < len(objects)
    ):
        raise CodexSyncStateError("incremental_archive_deduplication_invalid")
    redaction_counts = manifest.get("redaction_counts")
    if (
        not isinstance(redaction_counts, dict)
        or any(not isinstance(key, str) or not key for key in redaction_counts)
        or any(not isinstance(value, int) or value < 0 for value in redaction_counts.values())
    ):
        raise CodexSyncStateError("incremental_archive_redaction_counts_invalid")
    expected_members: dict[str, dict[str, Any]] = {}
    for content_hash, item in objects.items():
        _require_sha256(content_hash)
        if (
            not isinstance(item, dict)
            or set(item)
            != {
                "archive_member",
                "archive_sha256",
                "archive_size_bytes",
                "canonical_path",
                "record_count",
                "source_kind",
                "source_sha256",
                "source_size_bytes",
                "transformation",
            }
            or item.get("source_sha256") != content_hash
        ):
            raise CodexSyncStateError("incremental_archive_objects_invalid")
        member_name = _safe_relative_path(item.get("archive_member"), prefix="codex/")
        canonical_path = _safe_relative_path(item.get("canonical_path"))
        _require_sha256(item.get("archive_sha256"))
        if (
            member_name != f"{PACKAGE_MEMBER_ROOT}/{canonical_path}"
            or member_name in expected_members
            or not isinstance(item.get("archive_size_bytes"), int)
            or item["archive_size_bytes"] < 0
            or not isinstance(item.get("record_count"), int)
            or item["record_count"] < 0
            or not isinstance(item.get("source_size_bytes"), int)
            or item["source_size_bytes"] < 0
            or not isinstance(item.get("source_kind"), str)
            or not item["source_kind"]
            or not isinstance(item.get("transformation"), str)
            or not item["transformation"]
        ):
            raise CodexSyncStateError("incremental_archive_objects_invalid")
        expected_members[member_name] = item
    seen: set[str] = set()
    source_manifest_bytes: bytes | None = None
    try:
        with _MultipartReader(part_paths) as reader:
            with tarfile.open(fileobj=reader, mode="r|gz") as archive:
                for member in archive:
                    name = _safe_relative_path(member.name, prefix="codex/")
                    if not member.isfile() or name in seen:
                        raise CodexSyncStateError("incremental_archive_member_invalid")
                    seen.add(name)
                    handle = archive.extractfile(member)
                    if handle is None:
                        raise CodexSyncStateError("incremental_archive_member_invalid")
                    digest = hashlib.sha256()
                    size = 0
                    chunks: list[bytes] | None = [] if name == SOURCE_MANIFEST_MEMBER else None
                    while chunk := handle.read(1024 * 1024):
                        digest.update(chunk)
                        size += len(chunk)
                        if chunks is not None:
                            chunks.append(chunk)
                            if size > MAX_SOURCE_MANIFEST_BYTES:
                                raise CodexSyncStateError("source_manifest_invalid")
                    if name in expected_members:
                        expected = expected_members[name]
                        if size != expected["archive_size_bytes"] or digest.hexdigest() != expected["archive_sha256"]:
                            raise CodexSyncStateError("incremental_archive_object_mismatch")
                    elif name == SOURCE_MANIFEST_MEMBER:
                        source_manifest_bytes = b"".join(chunks or [])
                    elif name != "codex/_memory_atlas/README.md":
                        raise CodexSyncStateError("incremental_archive_member_unregistered")
    except (OSError, tarfile.TarError) as exc:
        raise CodexSyncStateError("incremental_archive_package_unreadable") from exc
    if seen != {*expected_members, SOURCE_MANIFEST_MEMBER, "codex/_memory_atlas/README.md"}:
        raise CodexSyncStateError("incremental_archive_member_inventory_mismatch")
    if source_manifest_bytes is None:
        raise CodexSyncStateError("source_manifest_missing")
    try:
        source_manifest = json.loads(source_manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSyncStateError("source_manifest_invalid") from exc
    if (
        not isinstance(source_manifest, dict)
        or set(source_manifest)
        != {
            "schema_version",
            "task_id",
            "acceptance_id",
            "source_id",
            "archive_id",
            "source_proof",
            "deduplication",
            "objects",
            "files",
            "deferred_inflight_sources",
            "phase_boundary",
        }
        or source_manifest.get("schema_version") != SOURCE_MANIFEST_SCHEMA_VERSION
        or source_manifest.get("task_id") != TASK_ID
        or source_manifest.get("acceptance_id") != ACCEPTANCE_ID
        or source_manifest.get("source_id") != SOURCE_ID
        or source_manifest.get("archive_id") != archive_id
        or source_manifest.get("source_proof") != manifest.get("source_proof")
        or source_manifest.get("deduplication") != deduplication
        or source_manifest.get("objects") != objects
        or source_manifest.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
    ):
        raise CodexSyncStateError("source_manifest_invalid")
    files = source_manifest.get("files")
    if not isinstance(files, list) or len(files) != deduplication["new_path_count"]:
        raise CodexSyncStateError("source_manifest_invalid")
    seen_paths: set[str] = set()
    for item in files:
        if (
            not isinstance(item, dict)
            or set(item)
            != {
                "source_kind",
                "source_relative_path",
                "source_sha256",
                "source_size_bytes",
                "source_stat",
                "archive_member",
            }
        ):
            raise CodexSyncStateError("source_manifest_invalid")
        relative_path = _safe_relative_path(item.get("source_relative_path"))
        content_hash = _require_sha256(item.get("source_sha256"))
        archive_member = _safe_relative_path(item.get("archive_member"), prefix="codex/")
        if (
            relative_path in seen_paths
            or content_hash not in objects
            or archive_member != objects[content_hash]["archive_member"]
            or item.get("source_kind") != objects[content_hash]["source_kind"]
            or item.get("source_size_bytes") != objects[content_hash]["source_size_bytes"]
        ):
            raise CodexSyncStateError("source_manifest_invalid")
        _validate_source_stat(item.get("source_stat"))
        seen_paths.add(relative_path)
    _validate_deferred(source_manifest.get("deferred_inflight_sources"))
    if _read_regular_bytes(
        archive_path / README_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="incremental_archive_readme_unreadable",
    ) != _readme(archive_id, manifest):
        raise CodexSyncStateError("incremental_archive_readme_mismatch")
    expected_restore = _restore_script(
        archive_id,
        str(package["sha256"]),
        int(package["member_count"]),
    )
    if _read_regular_bytes(
        archive_path / RESTORE_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="incremental_archive_restore_script_unreadable",
    ) != expected_restore:
        raise CodexSyncStateError("incremental_archive_restore_script_mismatch")

    result = {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / archive_id).as_posix(),
        "manifest_sha256": manifest_sha256,
        "package_sha256": package["sha256"],
        "package_bytes": package_bytes,
        "part_count": len(part_paths),
        "new_path_count": manifest["deduplication"]["new_path_count"],
        "unique_content_count": manifest["deduplication"]["unique_content_count"],
        "source_hash_stat_equal": manifest["source_proof"]["hash_stat_equal"],
        "source_mutation": False,
        "archive_mutation": False,
        "remote_push": False,
    }
    if require_public_registration:
        index_relative = _public_index_relative(archive_id, manifest_sha256)
        index_bytes = _read_regular_bytes(
            database_dir / index_relative,
            max_bytes=MAX_CONTRACT_BYTES,
            code="incremental_public_index_missing",
        )
        if index_bytes != _canonical_json_bytes(_public_index_payload(manifest, manifest_sha256)):
            raise CodexSyncStateError("incremental_public_index_mismatch")
        ledger_path = database_dir / "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
        raw_manifest_path = database_dir / (
            f"机器治理/证据与日志/raw_archive_manifests/"
            f"raw_manifest.s07_p1_t3_{archive_id}.jsonl"
        )
        ledger_bytes = _read_regular_bytes(
            ledger_path,
            max_bytes=MAX_MANIFEST_BYTES,
            code="incremental_raw_ledger_missing",
        )
        raw_manifest_bytes = _read_regular_bytes(
            raw_manifest_path,
            max_bytes=MAX_MANIFEST_BYTES,
            code="incremental_raw_manifest_missing",
        )
        if not _manifest_is_ledger_prefix(raw_manifest_bytes, ledger_bytes):
            raise CodexSyncStateError("incremental_raw_manifest_ledger_mismatch")
        expected_relative = index_relative.relative_to(Path("data/public_raw")).as_posix()
        expected_hash = _sha256_bytes(index_bytes)
        rows = read_jsonl(ledger_path)
        matching = [row for row in rows if row.get("relative_path") == expected_relative]
        if len(matching) != 1 or matching[0].get("sha256") != expected_hash or matching[0].get("size_bytes") != len(index_bytes):
            raise CodexSyncStateError("incremental_public_index_not_ledgered")
        result.update(
            {
                "public_index_path": index_relative.as_posix(),
                "raw_manifest_path": raw_manifest_path.relative_to(database_dir).as_posix(),
                "raw_manifest_is_ledger_prefix": True,
                "raw_ledger_verified": True,
                "public_raw_file_count": len(rows),
            }
        )
    return result


def _verify_active_inventory(
    active: dict[str, Any],
    proofs: tuple[SourceProof, ...],
    deferred: list[dict[str, Any]],
) -> None:
    observed = [_proof_record(proof) for proof in proofs]
    if (
        _proof_digest(proofs) != active["inventory_sha256"]
        or observed != active["inventory"]
        or deferred != active["deferred_inflight_sources"]
    ):
        raise CodexSyncStateError(
            "active_run_source_changed",
            state_may_exist=True,
        )


def _finalize_state(
    database_dir: Path,
    state_payload: dict[str, Any],
    verification: dict[str, Any],
    *,
    resumed: bool,
) -> dict[str, Any]:
    active = state_payload["active_run"]
    if not isinstance(active, dict):
        raise CodexSyncStateError("active_run_missing")
    manifest = _read_json_file(
        database_dir / ARCHIVE_ROOT / active["archive_id"] / MANIFEST_FILENAME,
        max_bytes=MAX_MANIFEST_BYTES,
        code="incremental_archive_manifest_unreadable",
    )
    content_index = dict(state_payload["content_index"])
    for content_hash, item in manifest["objects"].items():
        content_index[content_hash] = {
            "archive_id": active["archive_id"],
            "archive_member": item["archive_member"],
            "first_seen_path": item["canonical_path"],
            "source_kind": item["source_kind"],
            "source_size_bytes": item["source_size_bytes"],
        }
    source_rows = list(active["inventory"])
    completed_at = _now_utc()
    state_payload["content_index"] = content_index
    state_payload["cursor"] = {
        "sequence": int(state_payload["cursor"]["sequence"]) + 1,
        "inventory_sha256": active["inventory_sha256"],
        "stable_file_count": len(source_rows),
        "source_total_bytes": sum(int(row["source_size_bytes"]) for row in source_rows),
        "deferred_inflight_sources": active["deferred_inflight_sources"],
        "paths": _cursor_paths(source_rows, content_index),
    }
    state_payload["active_run"] = None
    state_payload["last_result"] = {
        "archive_id": active["archive_id"],
        "completed_at_utc": completed_at,
        "inventory_sha256": active["inventory_sha256"],
        "new_content_count": len(active["objects"]),
        "new_path_count": sum(len(item["paths"]) for item in active["objects"].values()),
        "outcome": "ARCHIVED_NEW_CONTENT",
    }
    state_payload["revision"] += 1
    _atomic_write_state(database_dir, state_payload)
    return {
        **verification,
        "outcome": "ARCHIVED_NEW_CONTENT",
        "resumed": resumed,
        "idempotent": False,
        "writes_files": True,
        "state_path": STATE_PATH.as_posix(),
        "state_revision": state_payload["revision"],
        "cursor_sequence": state_payload["cursor"]["sequence"],
        "content_index_count": len(content_index),
        "new_path_count": state_payload["last_result"]["new_path_count"],
        "new_content_count": state_payload["last_result"]["new_content_count"],
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _resume_active(
    database_dir: Path,
    state_payload: dict[str, Any],
    discovery_contract: dict[str, Any],
    credential_contract: dict[str, Any],
    inventory: CodexSourceInventory,
    proofs: tuple[SourceProof, ...],
    *,
    resumed: bool,
    checkpoint_hook: Callable[[str], None] | None,
) -> dict[str, Any]:
    active = state_payload["active_run"]
    if not isinstance(active, dict):
        raise CodexSyncStateError("active_run_missing")
    archive_id = str(active["archive_id"])
    parent = _ensure_archive_parent(database_dir)
    final = database_dir / ARCHIVE_ROOT / archive_id

    if active["phase"] == "PLANNED":
        with _archive_lock(parent, archive_id):
            if not final.exists():
                staging = _prepare_clean_staging(parent, active)
                try:
                    package, parts, source_manifest = _build_incremental_package(
                        staging,
                        active,
                        inventory,
                        discovery_contract,
                        credential_contract,
                        proofs,
                    )
                    _prepare_staging(staging, active, package, parts, source_manifest)
                    marker = staging / ".t3-staging.json"
                    marker.unlink()
                    _fsync_directory(staging)
                    _publish_staging(staging, final)
                    if staging.exists():
                        staging.rmdir()
                except Exception:
                    if staging.exists():
                        shutil.rmtree(staging, ignore_errors=True)
                    raise
            verification = verify_codex_incremental_archive(
                database_dir,
                archive_id,
                require_public_registration=False,
            )
        _checkpoint(
            database_dir,
            state_payload,
            "ARCHIVE_PUBLISHED",
            {
                "archive_manifest_sha256": verification["manifest_sha256"],
                "package_sha256": verification["package_sha256"],
            },
            checkpoint_hook,
        )

    active = state_payload["active_run"]
    if active["phase"] == "ARCHIVE_PUBLISHED":
        verification = verify_codex_incremental_archive(
            database_dir,
            archive_id,
            require_public_registration=False,
        )
        manifest = _read_json_file(
            final / MANIFEST_FILENAME,
            max_bytes=MAX_MANIFEST_BYTES,
            code="incremental_archive_manifest_unreadable",
        )
        public_index = _write_or_verify_public_index(
            database_dir,
            manifest,
            verification["manifest_sha256"],
        )
        _checkpoint(
            database_dir,
            state_payload,
            "PUBLIC_INDEX_PUBLISHED",
            {"public_index_path": public_index.as_posix()},
            checkpoint_hook,
        )

    active = state_payload["active_run"]
    if active["phase"] == "PUBLIC_INDEX_PUBLISHED":
        try:
            ledger = generate_raw_manifest(
                database_dir,
                f"s07_p1_t3_{archive_id}",
                imported_at=active["started_at_utc"],
                require_non_empty=False,
            )
        except RawLedgerError as exc:
            raise CodexSyncStateError(
                "incremental_raw_ledger_failed",
                writes_files=True,
                archive_may_exist=True,
                state_may_exist=True,
            ) from exc
        _checkpoint(
            database_dir,
            state_payload,
            "LEDGER_RECORDED",
            {
                "raw_manifest_path": ledger["manifest_path"],
                "raw_manifest_sha256": ledger["manifest_sha256"],
            },
            checkpoint_hook,
        )

    verification = verify_codex_incremental_archive(database_dir, archive_id)
    return _finalize_state(database_dir, state_payload, verification, resumed=resumed)


def _no_content_update(
    database_dir: Path,
    state_payload: dict[str, Any],
    source_rows: list[dict[str, Any]],
    inventory_sha256: str,
    deferred: list[dict[str, Any]],
    archive_id: str,
    *,
    initial_state: bool,
) -> dict[str, Any]:
    state_payload["cursor"] = {
        "sequence": int(state_payload["cursor"]["sequence"]) + 1,
        "inventory_sha256": inventory_sha256,
        "stable_file_count": len(source_rows),
        "source_total_bytes": sum(int(row["source_size_bytes"]) for row in source_rows),
        "deferred_inflight_sources": deferred,
        "paths": _cursor_paths(source_rows, state_payload["content_index"]),
    }
    outcome = (
        "CURSOR_INITIALIZED_NO_NEW_CONTENT"
        if initial_state
        else "CURSOR_UPDATED_NO_NEW_CONTENT"
    )
    state_payload["last_result"] = {
        "archive_id": archive_id,
        "completed_at_utc": _now_utc(),
        "inventory_sha256": inventory_sha256,
        "new_content_count": 0,
        "new_path_count": 0,
        "outcome": outcome,
    }
    state_payload["revision"] += 1
    _atomic_write_state(database_dir, state_payload)
    return {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "outcome": outcome,
        "resumed": False,
        "idempotent": False,
        "writes_files": True,
        "archive_created": False,
        "state_path": STATE_PATH.as_posix(),
        "state_revision": state_payload["revision"],
        "cursor_sequence": state_payload["cursor"]["sequence"],
        "stable_file_count": len(source_rows),
        "new_path_count": 0,
        "new_content_count": 0,
        "content_index_count": len(state_payload["content_index"]),
        "source_mutation": False,
        "remote_push": False,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _sync_impl(
    database_dir: Path,
    archive_id: str,
    *,
    operator_codex_home: Path | None,
    environ: Mapping[str, str] | None,
    home: Path | None,
    dry_run: bool,
    checkpoint_hook: Callable[[str], None] | None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    archive_id = _portable_archive_id(archive_id)
    load_codex_sync_state_contract(database_dir)

    def execute() -> dict[str, Any]:
        state_payload = _load_state(database_dir)
        initial_state = state_payload is None
        if state_payload is None:
            state_payload = _bootstrap_state(database_dir)
        active_before = state_payload["active_run"] is not None
        if active_before and state_payload["active_run"]["archive_id"] != archive_id:
            raise CodexSyncStateError("active_run_archive_id_mismatch", state_may_exist=True)
        if not active_before:
            try:
                preflight_raw_ledger(database_dir)
            except RawLedgerError as exc:
                raise CodexSyncStateError("public_raw_ledger_preflight_failed") from exc

        (
            discovery,
            credential,
            inventory,
            proofs,
            deferred_tuple,
            discovered_count,
            discovered_bytes,
        ) = _current_inventory(
            database_dir,
            operator_codex_home=operator_codex_home,
            environ=environ,
            home=home,
        )
        inventory_sha256 = _proof_digest(proofs)
        source_rows = [_proof_record(proof) for proof in proofs]
        deferred = _deferred_payload(deferred_tuple)

        if active_before:
            _verify_active_inventory(state_payload["active_run"], proofs, deferred)
            if dry_run:
                return {
                    "status": "PASS",
                    "schema_version": RESULT_SCHEMA_VERSION,
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "source_id": SOURCE_ID,
                    "archive_id": archive_id,
                    "dry_run": True,
                    "outcome": "WOULD_RESUME",
                    "resume_phase": state_payload["active_run"]["phase"],
                    "new_path_count": sum(len(item["paths"]) for item in state_payload["active_run"]["objects"].values()),
                    "new_content_count": len(state_payload["active_run"]["objects"]),
                    "writes_files": False,
                    "source_mutation": False,
                    "remote_push": False,
                    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
                }
            return _resume_active(
                database_dir,
                state_payload,
                discovery,
                credential,
                inventory,
                proofs,
                resumed=True,
                checkpoint_hook=checkpoint_hook,
            )

        objects = _objects_for_new_content(source_rows, state_payload["content_index"])
        new_path_count = sum(len(item["paths"]) for item in objects.values())
        if dry_run:
            return {
                "status": "PASS",
                "schema_version": RESULT_SCHEMA_VERSION,
                "task_id": TASK_ID,
                "acceptance_id": ACCEPTANCE_ID,
                "source_id": SOURCE_ID,
                "archive_id": archive_id,
                "dry_run": True,
                "outcome": "WOULD_ARCHIVE_NEW_CONTENT" if objects else "WOULD_UPDATE_CURSOR_ONLY",
                "eligible_file_count": discovered_count,
                "eligible_total_bytes": discovered_bytes,
                "stable_file_count": len(proofs),
                "deferred_inflight_file_count": len(deferred),
                "new_path_count": new_path_count,
                "new_content_count": len(objects),
                "source_root": "[CODEX_HOME]",
                "writes_files": False,
                "source_mutation": False,
                "remote_push": False,
                "phase_boundary": EXPECTED_PHASE_BOUNDARY,
            }
        if not objects:
            if not initial_state and _cursor_matches(state_payload, inventory_sha256, deferred):
                return {
                    "status": "PASS",
                    "schema_version": RESULT_SCHEMA_VERSION,
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "source_id": SOURCE_ID,
                    "archive_id": archive_id,
                    "outcome": "NO_CHANGES",
                    "resumed": False,
                    "idempotent": True,
                    "writes_files": False,
                    "archive_created": False,
                    "state_path": STATE_PATH.as_posix(),
                    "state_revision": state_payload["revision"],
                    "cursor_sequence": state_payload["cursor"]["sequence"],
                    "stable_file_count": len(proofs),
                    "new_path_count": 0,
                    "new_content_count": 0,
                    "content_index_count": len(state_payload["content_index"]),
                    "source_mutation": False,
                    "remote_push": False,
                    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
                }
            return _no_content_update(
                database_dir,
                state_payload,
                source_rows,
                inventory_sha256,
                deferred,
                archive_id,
                initial_state=initial_state,
            )

        final = database_dir / ARCHIVE_ROOT / archive_id
        if os.path.lexists(final):
            raise CodexSyncStateError("archive_id_exists")
        active = {
            "archive_id": archive_id,
            "phase": "PLANNED",
            "started_at_utc": _now_utc(),
            "inventory_sha256": inventory_sha256,
            "inventory": source_rows,
            "deferred_inflight_sources": deferred,
            "objects": objects,
        }
        state_payload["active_run"] = active
        state_payload["revision"] += 1
        _atomic_write_state(database_dir, state_payload)
        if checkpoint_hook is not None:
            checkpoint_hook("PLANNED")
        return _resume_active(
            database_dir,
            state_payload,
            discovery,
            credential,
            inventory,
            proofs,
            resumed=False,
            checkpoint_hook=checkpoint_hook,
        )

    if dry_run:
        return execute()
    with _sync_lock(database_dir):
        return execute()


def sync_codex_public_raw_incremental(
    database_dir: Path,
    archive_id: str,
    *,
    operator_codex_home: Path | None = None,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
    dry_run: bool = False,
    checkpoint_hook: Callable[[str], None] | None = None,
) -> dict[str, Any]:
    try:
        return _sync_impl(
            database_dir,
            archive_id,
            operator_codex_home=operator_codex_home,
            environ=environ,
            home=home,
            dry_run=dry_run,
            checkpoint_hook=checkpoint_hook,
        )
    except CodexSyncStateError:
        raise
    except CodexPublicRawArchiveError as exc:
        raise CodexSyncStateError(
            exc.code,
            writes_files=exc.writes_files,
            archive_may_exist=exc.archive_may_exist,
            state_may_exist=True,
        ) from exc


def run_codex_sync_state(args: argparse.Namespace) -> int:
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
        result = sync_codex_public_raw_incremental(
            getattr(args, "database_dir", Path(__file__).resolve().parents[2]),
            archive_id,
            operator_codex_home=getattr(args, "codex_home", None),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    except (CodexSyncStateError, RawLedgerError) as exc:
        error = exc if isinstance(exc, CodexSyncStateError) else None
        result = {
            "status": "FAIL_CLOSED",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "archive_id": archive_id,
            "reason": error.code if error else "sync_state_dependency_invalid",
            "writes_files": error.writes_files if error else False,
            "archive_may_exist": error.archive_may_exist if error else False,
            "state_may_exist": error.state_may_exist if error else False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


def run_codex_sync_state_audit(args: argparse.Namespace) -> int:
    database_dir = getattr(args, "database_dir", Path(__file__).resolve().parents[2])
    archive_id = getattr(args, "archive_id", None)
    try:
        load_codex_sync_state_contract(database_dir)
        state_payload = _load_state(database_dir.resolve())
        if state_payload is None:
            raise CodexSyncStateError("sync_state_missing")
        if state_payload["active_run"] is not None:
            raise CodexSyncStateError("sync_state_active_run_incomplete", state_may_exist=True)
        result: dict[str, Any] = {
            "status": "PASS",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "state_path": STATE_PATH.as_posix(),
            "state_revision": state_payload["revision"],
            "cursor_sequence": state_payload["cursor"]["sequence"],
            "stable_file_count": state_payload["cursor"]["stable_file_count"],
            "content_index_count": len(state_payload["content_index"]),
            "active_run": False,
            "writes_files": False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
        if archive_id:
            result["archive"] = verify_codex_incremental_archive(database_dir, archive_id)
    except (CodexSyncStateError, RawLedgerError) as exc:
        error = exc if isinstance(exc, CodexSyncStateError) else None
        result = {
            "status": "FAIL_CLOSED",
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "reason": error.code if error else "sync_state_dependency_invalid",
            "writes_files": False,
            "source_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = [
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "EXPECTED_PHASE_BOUNDARY",
    "SCHEMA_VERSION",
    "STATE_PATH",
    "TASK_ID",
    "CodexSyncStateError",
    "load_codex_sync_state_contract",
    "run_codex_sync_state",
    "run_codex_sync_state_audit",
    "sync_codex_public_raw_incremental",
    "validate_codex_sync_state",
    "validate_codex_sync_state_contract",
    "verify_codex_incremental_archive",
]
