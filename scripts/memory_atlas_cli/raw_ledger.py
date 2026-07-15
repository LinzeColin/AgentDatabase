"""Strict source-stat and append-only raw-ledger primitives for S06-P2-T1."""

from __future__ import annotations

import hashlib
import json
import os
import socket
import stat as stat_module
import time
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterator


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
RAW_LEDGER_CONTRACT_PATH = Path("config/data_sources/raw_ledger.json")
RAW_LEDGER_SCHEMA_VERSION = "memory_atlas.raw_ledger.v1_2_1_s06_p2_t1"
TASK_ID = "S06-P2-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S06-P2-T1"
POLICY_ID = "immutable_raw_ledger"
RAW_ROOT = Path("data/public_raw")
LEDGER_PATH = Path("机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl")
SOURCE_STAT_FIELDS = (
    "device",
    "inode",
    "mode",
    "size_bytes",
    "mtime_ns",
    "ctime_ns",
)
LEDGER_REQUIRED_FIELDS = (
    "source_id",
    "relative_path",
    "sha256",
    "imported_at",
    "size_bytes",
)
LEDGER_IMMUTABLE_FIELDS = (
    "source_id",
    "relative_path",
    "sha256",
    "size_bytes",
)
LOCK_METADATA_FIELDS = (
    "schema_version",
    "pid",
    "hostname",
    "created_at_ns",
    "ledger_identity",
)
LOCK_SCHEMA_VERSION = "memory_atlas.raw_ledger_lock.v1_2_1_s06_p2_t1"
DEFAULT_READ_CHUNK_BYTES = 1024 * 1024


class RawLedgerError(ValueError):
    """Raised when source immutability or raw-ledger integrity cannot be proven."""


class RawLedgerPostWriteError(RawLedgerError):
    """Raised when append-only raw output may exist without a ledger entry."""


@dataclass(frozen=True)
class SourceStat:
    device: int
    inode: int
    mode: int
    size_bytes: int
    mtime_ns: int
    ctime_ns: int

    @classmethod
    def from_os_stat(cls, value: os.stat_result) -> "SourceStat":
        return cls(
            device=int(value.st_dev),
            inode=int(value.st_ino),
            mode=int(value.st_mode),
            size_bytes=int(value.st_size),
            mtime_ns=int(value.st_mtime_ns),
            ctime_ns=int(value.st_ctime_ns),
        )


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise RawLedgerError(f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise RawLedgerError(f"{field} keys do not match the canonical contract")


def load_raw_ledger_contract(
    root: Path = PACKAGE_ROOT,
    path: Path | None = None,
) -> dict[str, Any]:
    contract_path = path or (root.resolve() / RAW_LEDGER_CONTRACT_PATH)
    try:
        payload = json.loads(contract_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RawLedgerError("cannot read the canonical raw-ledger contract") from exc
    contract = _mapping(payload, "raw_ledger")
    _exact_keys(
        contract,
        {
            "schema_version",
            "task_id",
            "acceptance_id",
            "policy",
            "raw_root",
            "source_stat_guard",
            "content_hash",
            "ledger",
            "phase_boundary",
        },
        "raw_ledger",
    )
    if (
        contract.get("schema_version") != RAW_LEDGER_SCHEMA_VERSION
        or contract.get("task_id") != TASK_ID
        or contract.get("acceptance_id") != ACCEPTANCE_ID
        or contract.get("policy") != POLICY_ID
        or contract.get("raw_root") != RAW_ROOT.as_posix()
    ):
        raise RawLedgerError("raw-ledger contract identity is unsupported")

    guard = _mapping(contract.get("source_stat_guard"), "source_stat_guard")
    if guard != {
        "before_after_fields": list(SOURCE_STAT_FIELDS),
        "directory_inventory_must_match": True,
        "reject_symlinks": True,
        "mutation_result": "fail_closed",
    }:
        raise RawLedgerError("source_stat_guard drifted from the fail-closed contract")
    content_hash = _mapping(contract.get("content_hash"), "content_hash")
    if content_hash != {
        "algorithm": "sha256",
        "read_chunk_bytes": DEFAULT_READ_CHUNK_BYTES,
        "hex_length": 64,
    }:
        raise RawLedgerError("content_hash drifted from SHA-256")
    ledger = _mapping(contract.get("ledger"), "ledger")
    if ledger != {
        "path": LEDGER_PATH.as_posix(),
        "format": "jsonl",
        "required_fields": list(LEDGER_REQUIRED_FIELDS),
        "immutable_fields": list(LEDGER_IMMUTABLE_FIELDS),
        "dedupe_key_fields": list(LEDGER_IMMUTABLE_FIELDS),
        "append_only": True,
        "rewrite_existing_bytes": False,
        "exclusive_append_lock": True,
        "lock_metadata_fields": list(LOCK_METADATA_FIELDS),
        "stale_lock_policy": "manual_verify_never_auto_remove",
        "fsync_after_append": True,
        "legacy_rows_compatible": True,
    }:
        raise RawLedgerError("ledger drifted from the append-only contract")
    boundary = _mapping(contract.get("phase_boundary"), "phase_boundary")
    if boundary != {
        "does_not_split_archives": True,
        "does_not_restore_archives": True,
        "does_not_modify_source_bytes": True,
        "does_not_push_remote": True,
        "next_task": "S06-P2-T2",
    }:
        raise RawLedgerError("phase_boundary exceeds S06-P2-T1")
    return contract


def capture_source_stat(path: Path) -> SourceStat:
    try:
        value = os.stat(path, follow_symlinks=False)
    except OSError as exc:
        raise RawLedgerError("source is missing or unreadable") from exc
    if stat_module.S_ISLNK(value.st_mode):
        raise RawLedgerError("source symlinks are not allowed")
    if not stat_module.S_ISREG(value.st_mode):
        raise RawLedgerError("source must be a regular file")
    return SourceStat.from_os_stat(value)


def assert_path_within_root_without_symlinks(path: Path, root: Path) -> Path:
    """Return the lexical relative path after rejecting every symlink component."""

    try:
        relative = path.relative_to(root)
    except ValueError as exc:
        raise RawLedgerError("source path escapes its declared root") from exc
    current = root
    try:
        root_stat = os.stat(current, follow_symlinks=False)
    except OSError as exc:
        raise RawLedgerError("source root is missing or unreadable") from exc
    if stat_module.S_ISLNK(root_stat.st_mode):
        raise RawLedgerError("source root symlinks are not allowed")
    for part in relative.parts:
        current = current / part
        try:
            value = os.stat(current, follow_symlinks=False)
        except OSError as exc:
            raise RawLedgerError("source path component is missing or unreadable") from exc
        if stat_module.S_ISLNK(value.st_mode):
            raise RawLedgerError("source path component symlinks are not allowed")
    return relative


def _source_inventory(
    source: Path,
    directory_globs: tuple[str, ...],
) -> dict[str, SourceStat]:
    try:
        root_stat = os.stat(source, follow_symlinks=False)
    except OSError as exc:
        raise RawLedgerError("source is missing or unreadable") from exc
    if stat_module.S_ISLNK(root_stat.st_mode):
        raise RawLedgerError("source symlinks are not allowed")
    if stat_module.S_ISREG(root_stat.st_mode):
        return {source.name: SourceStat.from_os_stat(root_stat)}
    if not stat_module.S_ISDIR(root_stat.st_mode) or not directory_globs:
        raise RawLedgerError("directory source requires explicit inventory patterns")

    for pattern in directory_globs:
        current = source
        for part in Path(pattern).parts:
            if any(marker in part for marker in ("*", "?", "[")):
                break
            current = current / part
            if os.path.lexists(current):
                assert_path_within_root_without_symlinks(current, source)

    paths: set[Path] = set()
    for pattern in directory_globs:
        paths.update(source.glob(pattern))
    inventory: dict[str, SourceStat] = {}
    for path in sorted(paths, key=lambda item: item.relative_to(source).as_posix()):
        label = assert_path_within_root_without_symlinks(path, source).as_posix()
        inventory[label] = capture_source_stat(path)
    return inventory


@contextmanager
def source_stat_guard(
    source: Path,
    *,
    directory_globs: tuple[str, ...] = (),
    expected: dict[str, SourceStat] | None = None,
) -> Iterator[dict[str, SourceStat]]:
    """Fail when a source file set changes while an adapter is reading it."""

    before = _source_inventory(source, directory_globs)
    if expected is not None and before != expected:
        raise RawLedgerError("source stat changed before sync could commit raw output")
    try:
        yield before
    finally:
        after = _source_inventory(source, directory_globs)
        if before != after or (expected is not None and after != expected):
            raise RawLedgerError("source stat changed while sync was reading input")


def guarded_sha256_file(
    path: Path,
    *,
    chunk_bytes: int = DEFAULT_READ_CHUNK_BYTES,
) -> dict[str, Any]:
    if chunk_bytes <= 0:
        raise RawLedgerError("hash read chunk size must be positive")
    digest = hashlib.sha256()
    with source_stat_guard(path) as inventory:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(chunk_bytes), b""):
                digest.update(chunk)
    source_stat = next(iter(inventory.values()))
    return {
        "sha256": digest.hexdigest(),
        "size_bytes": source_stat.size_bytes,
        "source_stat_verified": True,
    }


def validate_ledger_row(row: Any, label: str) -> dict[str, Any]:
    value = _mapping(row, label)
    if set(value) != set(LEDGER_REQUIRED_FIELDS):
        raise RawLedgerError(f"{label} fields do not match the raw-ledger schema")
    source_id = value.get("source_id")
    relative_path = value.get("relative_path")
    digest = value.get("sha256")
    imported_at = value.get("imported_at")
    size_bytes = value.get("size_bytes")
    if not isinstance(source_id, str) or not source_id:
        raise RawLedgerError(f"{label} contains an invalid source_id")
    if not isinstance(relative_path, str) or not relative_path or "\\" in relative_path:
        raise RawLedgerError(f"{label} contains an invalid relative_path")
    posix_path = PurePosixPath(relative_path)
    windows_path = PureWindowsPath(relative_path)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise RawLedgerError(f"{label} contains an invalid relative_path")
    if not isinstance(digest, str) or len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RawLedgerError(f"{label} contains an invalid sha256")
    if not isinstance(imported_at, str) or not imported_at:
        raise RawLedgerError(f"{label} contains an invalid imported_at")
    if isinstance(size_bytes, bool) or not isinstance(size_bytes, int) or size_bytes < 0:
        raise RawLedgerError(f"{label} contains an invalid size_bytes")
    return value


def ledger_dedupe_key(row: dict[str, Any]) -> str:
    validated = validate_ledger_row(row, "raw-ledger row")
    payload = "\0".join(str(validated[field]) for field in LEDGER_IMMUTABLE_FIELDS)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def raw_ledger_lock_path(path: Path) -> Path:
    return path.with_name(f"{path.name}.lock")


def _source_stat_payload(value: SourceStat) -> dict[str, int]:
    return {field: int(getattr(value, field)) for field in SOURCE_STAT_FIELDS}


def inspect_raw_ledger_lock(path: Path) -> dict[str, Any]:
    """Return bounded stale-lock diagnostics without ever removing the lock."""

    lock_path = raw_ledger_lock_path(path)
    try:
        capture_source_stat(lock_path)
        payload = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, RawLedgerError):
        return {"state": "invalid_metadata", "manual_verification_required": True}
    if not isinstance(payload, dict) or set(payload) != set(LOCK_METADATA_FIELDS):
        return {"state": "invalid_metadata", "manual_verification_required": True}
    pid = payload.get("pid")
    hostname = payload.get("hostname")
    created_at_ns = payload.get("created_at_ns")
    if (
        payload.get("schema_version") != LOCK_SCHEMA_VERSION
        or isinstance(pid, bool)
        or not isinstance(pid, int)
        or pid <= 0
        or not isinstance(hostname, str)
        or not hostname
        or isinstance(created_at_ns, bool)
        or not isinstance(created_at_ns, int)
        or created_at_ns <= 0
        or not isinstance(payload.get("ledger_identity"), (dict, type(None)))
    ):
        return {"state": "invalid_metadata", "manual_verification_required": True}
    state = "foreign_host_manual_verification"
    if hostname == socket.gethostname():
        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            state = "stale_pid_manual_verification"
        except (PermissionError, OSError):
            state = "pid_liveness_unverified"
        else:
            state = "active_pid"
    return {
        "state": state,
        "pid": pid,
        "hostname": hostname,
        "created_at_ns": created_at_ns,
        "ledger_identity": payload.get("ledger_identity"),
        "manual_verification_required": True,
    }


@contextmanager
def raw_ledger_append_lock(path: Path) -> Iterator[None]:
    """Serialize ledger read-check-append cycles with a fail-closed lock."""

    path.parent.mkdir(parents=True, exist_ok=True)
    lock_path = raw_ledger_lock_path(path)
    try:
        descriptor = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        diagnostics = inspect_raw_ledger_lock(path)
        raise RawLedgerError(
            f"raw ledger append lock already exists ({diagnostics['state']}); "
            "manual verification required and automatic removal is forbidden"
        ) from exc
    except OSError as exc:
        raise RawLedgerError("cannot create raw ledger append lock") from exc
    lock_stat: SourceStat | None = None
    try:
        ledger_identity = _source_stat_payload(capture_source_stat(path)) if path.exists() else None
        metadata = {
            "schema_version": LOCK_SCHEMA_VERSION,
            "pid": os.getpid(),
            "hostname": socket.gethostname(),
            "created_at_ns": time.time_ns(),
            "ledger_identity": ledger_identity,
        }
        try:
            with os.fdopen(descriptor, "wb") as handle:
                handle.write((json.dumps(metadata, sort_keys=True) + "\n").encode("utf-8"))
                handle.flush()
                os.fsync(handle.fileno())
        except OSError as exc:
            raise RawLedgerError("cannot durably write raw ledger append lock") from exc
        lock_stat = capture_source_stat(lock_path)
        yield
    finally:
        try:
            current = capture_source_stat(lock_path)
        except RawLedgerError:
            current = None
        if lock_stat is not None and current == lock_stat:
            lock_path.unlink()


def append_jsonl_immutable(
    path: Path,
    rows: list[dict[str, Any]],
    *,
    lock_held: bool = False,
) -> int:
    """Append canonical rows without replacing any existing ledger byte."""

    if not lock_held:
        with raw_ledger_append_lock(path):
            return append_jsonl_immutable(path, rows, lock_held=True)

    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        try:
            try:
                with path.open("xb") as handle:
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as exc:
                raise RawLedgerError("cannot durably create raw ledger") from exc
        except FileExistsError:
            pass
    if not rows:
        return 0
    payload = "".join(
        json.dumps(validate_ledger_row(row, "new raw-ledger row"), ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    ).encode("utf-8")
    before = capture_source_stat(path)
    if before.size_bytes:
        try:
            with path.open("rb") as handle:
                handle.seek(-1, os.SEEK_END)
                if handle.read(1) != b"\n":
                    raise RawLedgerError("raw ledger is not newline terminated")
        except OSError as exc:
            raise RawLedgerError("cannot verify raw ledger termination") from exc
    current = capture_source_stat(path)
    if current != before:
        raise RawLedgerError("raw ledger changed before append")
    try:
        with path.open("ab") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise RawLedgerError("raw ledger append durability verification failed") from exc
    after = capture_source_stat(path)
    if after.device != before.device or after.inode != before.inode:
        raise RawLedgerError("raw ledger identity changed during append")
    if after.size_bytes != before.size_bytes + len(payload):
        raise RawLedgerError("raw ledger append size verification failed")
    return len(payload)


__all__ = (
    "ACCEPTANCE_ID",
    "DEFAULT_READ_CHUNK_BYTES",
    "LEDGER_IMMUTABLE_FIELDS",
    "LEDGER_PATH",
    "LEDGER_REQUIRED_FIELDS",
    "LOCK_METADATA_FIELDS",
    "LOCK_SCHEMA_VERSION",
    "PACKAGE_ROOT",
    "POLICY_ID",
    "RAW_LEDGER_CONTRACT_PATH",
    "RAW_LEDGER_SCHEMA_VERSION",
    "RAW_ROOT",
    "RawLedgerError",
    "RawLedgerPostWriteError",
    "SourceStat",
    "append_jsonl_immutable",
    "assert_path_within_root_without_symlinks",
    "capture_source_stat",
    "guarded_sha256_file",
    "ledger_dedupe_key",
    "load_raw_ledger_contract",
    "inspect_raw_ledger_lock",
    "raw_ledger_append_lock",
    "raw_ledger_lock_path",
    "source_stat_guard",
    "validate_ledger_row",
)
