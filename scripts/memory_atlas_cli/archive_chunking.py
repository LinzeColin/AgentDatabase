"""Deterministic fixed-size archive chunking primitives for S06-P2-T2."""

from __future__ import annotations

import hashlib
import json
import os
import re
import socket
import stat as stat_module
import time
from contextlib import contextmanager
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterator

from memory_atlas_cli.raw_ledger import (
    RawLedgerError,
    SourceStat,
    capture_source_stat,
    guarded_sha256_file,
    source_stat_guard,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("config/data_sources/archive_chunking.json")
ARCHIVE_ROOT = Path("data/raw_archives")
CONTRACT_SCHEMA_VERSION = "memory_atlas.archive_chunking.v1_2_1_s06_p2_t2"
MANIFEST_SCHEMA_VERSION = "memory_atlas.archive_chunk_manifest.v1_2_1_s06_p2_t2"
RESULT_SCHEMA_VERSION = "memory_atlas.archive_chunk_result.v1_2_1_s06_p2_t2"
LOCK_SCHEMA_VERSION = "memory_atlas.archive_chunk_lock.v1_2_1_s06_p2_t2"
TASK_ID = "S06-P2-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S06-P2-T2"
POLICY_ID = "deterministic_fixed_size_chunks"
MAX_PART_BYTES = 45 * 1024 * 1024
GITHUB_WARNING_BYTES = 50 * 1024 * 1024
GITHUB_HARD_LIMIT_BYTES = 100 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024
PART_INDEX_WIDTH = 6
PARTS_DIRECTORY = "parts"
MANIFEST_FILENAME = "manifest.json"
PACKAGE_FIELDS = ("filename", "byte_size", "sha256")
PART_FIELDS = ("index", "filename", "byte_size", "sha256")
LOCK_FIELDS = ("schema_version", "pid", "hostname", "created_at_ns", "archive_id")
MAX_CONTRACT_BYTES = 64 * 1024
MAX_LOCK_BYTES = 16 * 1024
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
_WINDOWS_RESERVED_ID_RE = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


class ArchiveChunkError(ValueError):
    """Raised when deterministic chunking or publication cannot be proven."""


class ArchiveChunkPostPublishError(ArchiveChunkError):
    """Raised when a valid archive may exist but parent-directory fsync failed."""


class ArchiveChunkPartialWriteError(ArchiveChunkError):
    """Raised when an incomplete reserved archive cannot be safely cleaned up."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArchiveChunkError(f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ArchiveChunkError(f"{field} keys do not match the canonical contract")


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_portable_id(value: Any, field: str, *, max_length: int) -> str:
    if not isinstance(value, str) or value != value.strip() or not value:
        raise ArchiveChunkError(f"{field} must be a non-empty portable identifier")
    if len(value) > max_length or not _PORTABLE_ID_RE.fullmatch(value):
        raise ArchiveChunkError(f"{field} is not a portable identifier")
    if _WINDOWS_RESERVED_ID_RE.fullmatch(value):
        raise ArchiveChunkError(f"{field} is a reserved Windows path component")
    return value


def _read_regular_bytes(path: Path, *, max_bytes: int, label: str) -> bytes:
    if path.is_symlink():
        raise ArchiveChunkError(f"{label} cannot be a symlink")
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        metadata = os.fstat(descriptor)
        if not stat_module.S_ISREG(metadata.st_mode):
            raise ArchiveChunkError(f"{label} must be a regular file")
        if metadata.st_size > max_bytes:
            raise ArchiveChunkError(f"{label} exceeds its size limit")
        payload = os.read(descriptor, max_bytes + 1)
    except ArchiveChunkError:
        raise
    except OSError as exc:
        raise ArchiveChunkError(f"{label} is missing or unreadable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    if len(payload) > max_bytes:
        raise ArchiveChunkError(f"{label} exceeds its size limit")
    return payload


def load_archive_chunking_contract(
    root: Path = PACKAGE_ROOT,
    path: Path | None = None,
) -> dict[str, Any]:
    contract_path = path or (root.resolve() / CONTRACT_PATH)
    try:
        payload = json.loads(
            _read_regular_bytes(
                contract_path,
                max_bytes=MAX_CONTRACT_BYTES,
                label="archive-chunking contract",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveChunkError("cannot read the canonical archive-chunking contract") from exc
    contract = _mapping(payload, "archive_chunking")
    _exact_keys(
        contract,
        {
            "schema_version",
            "task_id",
            "acceptance_id",
            "policy",
            "archive_root",
            "threshold",
            "hashing",
            "naming",
            "manifest",
            "publication",
            "phase_boundary",
        },
        "archive_chunking",
    )
    if (
        contract.get("schema_version") != CONTRACT_SCHEMA_VERSION
        or contract.get("task_id") != TASK_ID
        or contract.get("acceptance_id") != ACCEPTANCE_ID
        or contract.get("policy") != POLICY_ID
        or contract.get("archive_root") != ARCHIVE_ROOT.as_posix()
    ):
        raise ArchiveChunkError("archive-chunking contract identity is unsupported")
    if _mapping(contract.get("threshold"), "threshold") != {
        "max_part_bytes": MAX_PART_BYTES,
        "github_warning_bytes": GITHUB_WARNING_BYTES,
        "github_hard_limit_bytes": GITHUB_HARD_LIMIT_BYTES,
        "part_bytes_below_warning": True,
    }:
        raise ArchiveChunkError("archive threshold drifted from the 45 MiB contract")
    if _mapping(contract.get("hashing"), "hashing") != {
        "algorithm": "sha256",
        "read_chunk_bytes": READ_CHUNK_BYTES,
        "hex_length": 64,
    }:
        raise ArchiveChunkError("archive hashing drifted from SHA-256")
    if _mapping(contract.get("naming"), "naming") != {
        "parts_directory": PARTS_DIRECTORY,
        "manifest_filename": MANIFEST_FILENAME,
        "part_index_width": PART_INDEX_WIDTH,
        "part_filename_template": "{archive_id}.part-{index:06d}",
    }:
        raise ArchiveChunkError("archive part naming drifted from the deterministic contract")
    if _mapping(contract.get("manifest"), "manifest") != {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "deterministic_json": True,
        "package_fields": list(PACKAGE_FIELDS),
        "part_fields": list(PART_FIELDS),
        "ordered_parts": True,
        "absolute_paths_forbidden": True,
        "timestamps_forbidden": True,
    }:
        raise ArchiveChunkError("archive manifest drifted from the deterministic contract")
    if _mapping(contract.get("publication"), "publication") != {
        "output_path_template": "data/raw_archives/{source_id}/{archive_id}",
        "exclusive_lock": True,
        "exclusive_output_reservation": True,
        "no_overwrite": True,
        "idempotent_replay": True,
        "manifest_publish_last": True,
        "incomplete_output_invalid_without_manifest": True,
        "normal_failure_cleanup_requires_identity": True,
        "fsync_parts_and_manifest": True,
        "stale_lock_policy": "manual_verify_never_auto_remove",
    }:
        raise ArchiveChunkError("archive publication drifted from the no-overwrite contract")
    if _mapping(contract.get("phase_boundary"), "phase_boundary") != {
        "does_not_restore_archives": True,
        "does_not_modify_source_bytes": True,
        "does_not_modify_public_raw_or_ledger": True,
        "does_not_rewrite_legacy_archives": True,
        "does_not_push_remote": True,
        "production_activation_requires": "S06-P2-T3",
        "next_task": "S06-P2-T3",
    }:
        raise ArchiveChunkError("phase_boundary exceeds S06-P2-T2")
    if not MAX_PART_BYTES < GITHUB_WARNING_BYTES < GITHUB_HARD_LIMIT_BYTES:
        raise ArchiveChunkError("archive size boundaries are internally inconsistent")
    return contract


def _canonical_regular_file(path: Path) -> tuple[Path, SourceStat]:
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ArchiveChunkError("archive package is missing or unreadable") from exc
    if lexical != resolved:
        raise ArchiveChunkError("archive package path contains a symlink component")
    try:
        metadata = capture_source_stat(resolved)
    except RawLedgerError as exc:
        raise ArchiveChunkError(str(exc)) from exc
    return resolved, metadata


def _safe_package_filename(value: Any) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ArchiveChunkError("package.filename is invalid")
    if "\n" in value or "\r" in value or "/" in value or "\\" in value:
        raise ArchiveChunkError("package.filename must be a basename")
    if PurePosixPath(value).name != value or PureWindowsPath(value).name != value:
        raise ArchiveChunkError("package.filename must be portable")
    return value


def _part_relative_path(archive_id: str, index: int) -> str:
    return f"{PARTS_DIRECTORY}/{archive_id}.part-{index:0{PART_INDEX_WIDTH}d}"


def _manifest_bytes(payload: dict[str, Any]) -> bytes:
    validate_chunk_manifest(payload)
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def validate_chunk_manifest(payload: Any) -> dict[str, Any]:
    manifest = _mapping(payload, "chunk manifest")
    _exact_keys(
        manifest,
        {
            "schema_version",
            "task_id",
            "acceptance_id",
            "source_id",
            "archive_id",
            "archive_path",
            "package",
            "split",
            "parts",
        },
        "chunk manifest",
    )
    if (
        manifest.get("schema_version") != MANIFEST_SCHEMA_VERSION
        or manifest.get("task_id") != TASK_ID
        or manifest.get("acceptance_id") != ACCEPTANCE_ID
    ):
        raise ArchiveChunkError("chunk manifest identity is unsupported")
    source_id = _validate_portable_id(manifest.get("source_id"), "source_id", max_length=64)
    archive_id = _validate_portable_id(manifest.get("archive_id"), "archive_id", max_length=128)
    expected_archive_path = (ARCHIVE_ROOT / source_id / archive_id).as_posix()
    if manifest.get("archive_path") != expected_archive_path:
        raise ArchiveChunkError("chunk manifest archive_path is not canonical")

    package = _mapping(manifest.get("package"), "package")
    _exact_keys(package, set(PACKAGE_FIELDS), "package")
    _safe_package_filename(package.get("filename"))
    package_bytes = package.get("byte_size")
    if isinstance(package_bytes, bool) or not isinstance(package_bytes, int) or package_bytes <= MAX_PART_BYTES:
        raise ArchiveChunkError("chunk manifest package must exceed 45 MiB")
    if not _valid_sha256(package.get("sha256")):
        raise ArchiveChunkError("package.sha256 is invalid")

    split = _mapping(manifest.get("split"), "split")
    if set(split) != {
        "method",
        "max_part_bytes",
        "github_warning_bytes",
        "part_count",
        "part_index_width",
        "deterministic",
    }:
        raise ArchiveChunkError("split keys do not match the chunk manifest contract")
    parts = manifest.get("parts")
    if not isinstance(parts, list) or len(parts) < 2:
        raise ArchiveChunkError("chunk manifest must contain at least two ordered parts")
    if split != {
        "method": "fixed_bytes",
        "max_part_bytes": MAX_PART_BYTES,
        "github_warning_bytes": GITHUB_WARNING_BYTES,
        "part_count": len(parts),
        "part_index_width": PART_INDEX_WIDTH,
        "deterministic": True,
    }:
        raise ArchiveChunkError("split metadata drifted from the 45 MiB contract")

    total_bytes = 0
    seen_filenames: set[str] = set()
    for expected_index, item in enumerate(parts):
        part = _mapping(item, f"parts[{expected_index}]")
        _exact_keys(part, set(PART_FIELDS), f"parts[{expected_index}]")
        expected_filename = _part_relative_path(archive_id, expected_index)
        if part.get("index") != expected_index or part.get("filename") != expected_filename:
            raise ArchiveChunkError("chunk manifest part order or filename is not deterministic")
        part_bytes = part.get("byte_size")
        if isinstance(part_bytes, bool) or not isinstance(part_bytes, int) or not 0 < part_bytes <= MAX_PART_BYTES:
            raise ArchiveChunkError("chunk manifest part byte_size exceeds the 45 MiB limit")
        if part_bytes >= GITHUB_WARNING_BYTES:
            raise ArchiveChunkError("chunk manifest part reaches the GitHub warning line")
        if expected_index < len(parts) - 1 and part_bytes != MAX_PART_BYTES:
            raise ArchiveChunkError("only the final archive part may be shorter than 45 MiB")
        if not _valid_sha256(part.get("sha256")):
            raise ArchiveChunkError("chunk manifest part sha256 is invalid")
        if expected_filename in seen_filenames:
            raise ArchiveChunkError("chunk manifest contains duplicate part filenames")
        seen_filenames.add(expected_filename)
        total_bytes += part_bytes
    if total_bytes != package_bytes:
        raise ArchiveChunkError("chunk manifest part bytes do not equal package bytes")
    return manifest


def _scan_package(
    package_path: Path,
    archive_id: str,
    expected_stat: SourceStat,
    parts_dir_fd: int | None,
    created_part_stats: dict[str, SourceStat] | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    package_digest = hashlib.sha256()
    parts: list[dict[str, Any]] = []
    total_bytes = 0
    expected_inventory = {package_path.name: expected_stat}
    try:
        with source_stat_guard(package_path, expected=expected_inventory):
            with package_path.open("rb") as source:
                index = 0
                while True:
                    first_chunk = source.read(min(READ_CHUNK_BYTES, MAX_PART_BYTES))
                    if not first_chunk:
                        break
                    part_relative = _part_relative_path(archive_id, index)
                    part_name = Path(part_relative).name
                    part_digest = hashlib.sha256()
                    part_bytes = 0
                    part_handle = None
                    try:
                        if parts_dir_fd is not None:
                            descriptor = os.open(
                                part_name,
                                os.O_CREAT
                                | os.O_EXCL
                                | os.O_WRONLY
                                | getattr(os, "O_NOFOLLOW", 0),
                                0o600,
                                dir_fd=parts_dir_fd,
                            )
                            if created_part_stats is not None:
                                if part_name in created_part_stats:
                                    os.close(descriptor)
                                    raise ArchiveChunkError(
                                        "archive part identity was registered more than once"
                                    )
                                created_part_stats[part_name] = SourceStat.from_os_stat(
                                    os.fstat(descriptor)
                                )
                            try:
                                part_handle = os.fdopen(descriptor, "wb")
                            except OSError:
                                os.close(descriptor)
                                raise
                        chunk = first_chunk
                        while chunk:
                            package_digest.update(chunk)
                            part_digest.update(chunk)
                            part_bytes += len(chunk)
                            total_bytes += len(chunk)
                            if part_handle is not None:
                                part_handle.write(chunk)
                            if part_bytes == MAX_PART_BYTES:
                                break
                            chunk = source.read(min(READ_CHUNK_BYTES, MAX_PART_BYTES - part_bytes))
                        if part_handle is not None:
                            part_handle.flush()
                            os.fsync(part_handle.fileno())
                    except OSError as exc:
                        raise ArchiveChunkError("cannot durably write an archive part") from exc
                    finally:
                        if part_handle is not None:
                            part_handle.close()
                    parts.append(
                        {
                            "index": index,
                            "filename": part_relative,
                            "byte_size": part_bytes,
                            "sha256": part_digest.hexdigest(),
                        }
                    )
                    index += 1
    except RawLedgerError as exc:
        raise ArchiveChunkError(str(exc)) from exc
    if total_bytes != expected_stat.size_bytes:
        raise ArchiveChunkError("archive package bytes changed while chunking")
    package = {
        "filename": package_path.name,
        "byte_size": total_bytes,
        "sha256": package_digest.hexdigest(),
    }
    return package, parts


def _build_manifest(
    source_id: str,
    archive_id: str,
    package: dict[str, Any],
    parts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = {
        "schema_version": MANIFEST_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": source_id,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / source_id / archive_id).as_posix(),
        "package": package,
        "split": {
            "method": "fixed_bytes",
            "max_part_bytes": MAX_PART_BYTES,
            "github_warning_bytes": GITHUB_WARNING_BYTES,
            "part_count": len(parts),
            "part_index_width": PART_INDEX_WIDTH,
            "deterministic": True,
        },
        "parts": parts,
    }
    return validate_chunk_manifest(payload)


def _source_stat_from_fd(descriptor: int) -> SourceStat:
    return SourceStat.from_os_stat(os.fstat(descriptor))


def _open_directory_at(parent_fd: int, name: str, label: str) -> int:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise ArchiveChunkError(f"{label} must be a non-symlink directory") from exc
    if not stat_module.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ArchiveChunkError(f"{label} must be a directory")
    return descriptor


@contextmanager
def _open_archive_parent(database_dir: Path, source_id: str) -> Iterator[tuple[Path, int]]:
    try:
        current_fd = os.open(
            database_dir,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ArchiveChunkError("database directory cannot be opened safely") from exc
    opened = [current_fd]
    try:
        for part in (*ARCHIVE_ROOT.parts, source_id):
            try:
                os.mkdir(part, mode=0o700, dir_fd=current_fd)
            except FileExistsError:
                pass
            except OSError as exc:
                raise ArchiveChunkError("cannot create canonical archive parent safely") from exc
            next_fd = _open_directory_at(current_fd, part, "canonical archive parent")
            opened.append(next_fd)
            current_fd = next_fd
        yield database_dir / ARCHIVE_ROOT / source_id, current_fd
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _write_durable_file_at(directory_fd: int, name: str, payload: bytes) -> None:
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_CREAT
            | os.O_EXCL
            | os.O_WRONLY
            | getattr(os, "O_NOFOLLOW", 0),
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(descriptor, "wb") as handle:
            descriptor = None
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
    except OSError as exc:
        raise ArchiveChunkError(f"cannot durably write {name}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _fsync_directory_fd(directory_fd: int, label: str) -> None:
    try:
        os.fsync(directory_fd)
    except OSError as exc:
        raise ArchiveChunkError(f"cannot durably sync directory: {label}") from exc


def _read_regular_file_at(
    directory_fd: int,
    name: str,
    label: str,
    *,
    max_bytes: int | None = None,
) -> bytes:
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        before = _source_stat_from_fd(descriptor)
        if not stat_module.S_ISREG(before.mode):
            raise ArchiveChunkError(f"{label} must be a regular file")
        if max_bytes is not None and before.size_bytes > max_bytes:
            raise ArchiveChunkError(f"{label} exceeds its size limit")
        chunks: list[bytes] = []
        remaining = before.size_bytes
        while remaining:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
            if not chunk:
                raise ArchiveChunkError(f"{label} ended before its recorded size")
            chunks.append(chunk)
            remaining -= len(chunk)
        if os.read(descriptor, 1):
            raise ArchiveChunkError(f"{label} grew while it was read")
        if _source_stat_from_fd(descriptor) != before:
            raise ArchiveChunkError(f"{label} changed while it was read")
        return b"".join(chunks)
    except ArchiveChunkError:
        raise
    except OSError as exc:
        raise ArchiveChunkError(f"cannot read {label}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _fingerprint_regular_file_at(directory_fd: int, name: str, label: str) -> dict[str, Any]:
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        before = _source_stat_from_fd(descriptor)
        if not stat_module.S_ISREG(before.mode):
            raise ArchiveChunkError(f"{label} must be a regular file")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, READ_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
        if _source_stat_from_fd(descriptor) != before or total != before.size_bytes:
            raise ArchiveChunkError(f"{label} changed while it was hashed")
        return {"sha256": digest.hexdigest(), "size_bytes": total}
    except ArchiveChunkError:
        raise
    except OSError as exc:
        raise ArchiveChunkError(f"cannot hash {label}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _assert_archive_name_identity(parent_fd: int, archive_id: str, archive_fd: int) -> None:
    try:
        named = SourceStat.from_os_stat(
            os.stat(archive_id, dir_fd=parent_fd, follow_symlinks=False)
        )
    except OSError as exc:
        raise ArchiveChunkError("archive output name disappeared during publication") from exc
    opened = _source_stat_from_fd(archive_fd)
    if (
        named.device != opened.device
        or named.inode != opened.inode
        or not stat_module.S_ISDIR(named.mode)
    ):
        raise ArchiveChunkError("archive output name changed during publication")


def _verify_archive_fd(archive_fd: int, expected_manifest: dict[str, Any]) -> dict[str, Any]:
    before = _source_stat_from_fd(archive_fd)
    expected_bytes = _manifest_bytes(expected_manifest)
    expected_root_entries = {MANIFEST_FILENAME, PARTS_DIRECTORY}
    if set(os.listdir(archive_fd)) != expected_root_entries:
        raise ArchiveChunkError("archive output root inventory conflicts with the manifest")
    parts_fd = _open_directory_at(archive_fd, PARTS_DIRECTORY, "archive parts")
    try:
        expected_part_names = {Path(str(part["filename"])).name for part in expected_manifest["parts"]}
        if set(os.listdir(parts_fd)) != expected_part_names:
            raise ArchiveChunkError("archive part inventory conflicts with the manifest")
        if _read_regular_file_at(
            archive_fd,
            MANIFEST_FILENAME,
            "archive manifest",
        ) != expected_bytes:
            raise ArchiveChunkError("existing archive manifest is not byte-identical")
        for part in expected_manifest["parts"]:
            name = Path(str(part["filename"])).name
            fingerprint = _fingerprint_regular_file_at(parts_fd, name, f"archive part {name}")
            if (
                fingerprint["size_bytes"] != part["byte_size"]
                or fingerprint["sha256"] != part["sha256"]
            ):
                raise ArchiveChunkError("existing archive part conflicts with the manifest")
    finally:
        os.close(parts_fd)
    if _source_stat_from_fd(archive_fd) != before:
        raise ArchiveChunkError("archive output changed during verification")
    return {
        "manifest_sha256": hashlib.sha256(expected_bytes).hexdigest(),
        "manifest_bytes": len(expected_bytes),
    }


def _try_open_archive_at(parent_fd: int, archive_id: str) -> int | None:
    try:
        return os.open(
            archive_id,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ArchiveChunkError("existing archive path is not a non-symlink directory") from exc


def _same_node_identity(current: SourceStat, expected: SourceStat) -> bool:
    return (
        current.device == expected.device
        and current.inode == expected.inode
        and current.mode == expected.mode
    )


def _cleanup_owned_archive(
    parent_fd: int,
    archive_id: str,
    archive_fd: int,
    created_part_stats: dict[str, SourceStat],
) -> bool:
    """Remove only the reserved directory still proven to be owned by this run."""

    parts_fd = None
    try:
        _assert_archive_name_identity(parent_fd, archive_id, archive_fd)
        root_entries = set(os.listdir(archive_fd))
        if not root_entries <= {MANIFEST_FILENAME, PARTS_DIRECTORY}:
            return False

        part_names: list[str] = []
        if PARTS_DIRECTORY in root_entries:
            parts_fd = _open_directory_at(archive_fd, PARTS_DIRECTORY, "reserved archive parts")
            part_names = sorted(os.listdir(parts_fd))
            expected_name = re.compile(
                rf"^{re.escape(archive_id)}\.part-\d{{{PART_INDEX_WIDTH}}}$"
            )
            if set(part_names) != set(created_part_stats):
                return False
            for name in part_names:
                if not expected_name.fullmatch(name):
                    return False
                current = SourceStat.from_os_stat(
                    os.stat(name, dir_fd=parts_fd, follow_symlinks=False)
                )
                if (
                    not stat_module.S_ISREG(current.mode)
                    or not _same_node_identity(current, created_part_stats[name])
                ):
                    return False

        if MANIFEST_FILENAME in root_entries:
            metadata = os.stat(
                MANIFEST_FILENAME,
                dir_fd=archive_fd,
                follow_symlinks=False,
            )
            if not stat_module.S_ISREG(metadata.st_mode):
                return False

        if MANIFEST_FILENAME in root_entries:
            os.unlink(MANIFEST_FILENAME, dir_fd=archive_fd)
        if parts_fd is not None:
            for name in part_names:
                current = SourceStat.from_os_stat(
                    os.stat(name, dir_fd=parts_fd, follow_symlinks=False)
                )
                if not _same_node_identity(current, created_part_stats[name]):
                    return False
                os.unlink(name, dir_fd=parts_fd)
            _fsync_directory_fd(parts_fd, "reserved archive parts cleanup")
            parts_identity = _source_stat_from_fd(parts_fd)
            named_parts = SourceStat.from_os_stat(
                os.stat(PARTS_DIRECTORY, dir_fd=archive_fd, follow_symlinks=False)
            )
            if (
                named_parts.device != parts_identity.device
                or named_parts.inode != parts_identity.inode
                or not stat_module.S_ISDIR(named_parts.mode)
            ):
                return False
            os.rmdir(PARTS_DIRECTORY, dir_fd=archive_fd)
        _fsync_directory_fd(archive_fd, "reserved archive cleanup")
        if os.listdir(archive_fd):
            return False
        _assert_archive_name_identity(parent_fd, archive_id, archive_fd)
        os.rmdir(archive_id, dir_fd=parent_fd)
        _fsync_directory_fd(parent_fd, "archive parent cleanup")
        return True
    except (ArchiveChunkError, OSError):
        return False
    finally:
        if parts_fd is not None:
            os.close(parts_fd)


def archive_chunk_lock_path(archive_path: Path) -> Path:
    return archive_path.parent / f".{archive_path.name}.chunk.lock"


def _inspect_archive_chunk_lock_at(parent_fd: int, expected_archive_id: str) -> dict[str, Any]:
    lock_name = f".{expected_archive_id}.chunk.lock"
    try:
        payload = json.loads(
            _read_regular_file_at(
                parent_fd,
                lock_name,
                "archive chunk lock",
                max_bytes=MAX_LOCK_BYTES,
            ).decode("utf-8")
        )
    except (ArchiveChunkError, UnicodeDecodeError, json.JSONDecodeError):
        return {"state": "invalid_metadata", "manual_verification_required": True}
    if not isinstance(payload, dict) or set(payload) != set(LOCK_FIELDS):
        return {"state": "invalid_metadata", "manual_verification_required": True}
    pid = payload.get("pid")
    hostname = payload.get("hostname")
    created_at_ns = payload.get("created_at_ns")
    archive_id = payload.get("archive_id")
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
        or archive_id != expected_archive_id
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
        "archive_id": archive_id,
        "manual_verification_required": True,
    }


def inspect_archive_chunk_lock(archive_path: Path) -> dict[str, Any]:
    descriptor = None
    try:
        descriptor = os.open(
            archive_path.parent,
            os.O_RDONLY
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        return _inspect_archive_chunk_lock_at(descriptor, archive_path.name)
    except OSError:
        return {"state": "invalid_metadata", "manual_verification_required": True}
    finally:
        if descriptor is not None:
            os.close(descriptor)


@contextmanager
def archive_chunk_lock(archive_path: Path, *, parent_fd: int | None = None) -> Iterator[None]:
    owned_parent_fd = None
    try:
        if parent_fd is None:
            try:
                owned_parent_fd = os.open(
                    archive_path.parent,
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
            except OSError as exc:
                raise ArchiveChunkError("archive chunk lock parent is unsafe") from exc
            parent_fd = owned_parent_fd
        lock_name = f".{archive_path.name}.chunk.lock"
        try:
            descriptor = os.open(
                lock_name,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                0o600,
                dir_fd=parent_fd,
            )
        except FileExistsError as exc:
            diagnostics = _inspect_archive_chunk_lock_at(parent_fd, archive_path.name)
            raise ArchiveChunkError(
                f"archive chunk lock already exists ({diagnostics['state']}); "
                "manual verification required and automatic removal is forbidden"
            ) from exc
        except OSError as exc:
            raise ArchiveChunkError("cannot create archive chunk lock") from exc
        created = SourceStat.from_os_stat(os.fstat(descriptor))
        lock_stat: SourceStat | None = None
        descriptor_open = True
        try:
            metadata = {
                "schema_version": LOCK_SCHEMA_VERSION,
                "pid": os.getpid(),
                "hostname": socket.gethostname(),
                "created_at_ns": time.time_ns(),
                "archive_id": archive_path.name,
            }
            try:
                with os.fdopen(descriptor, "wb") as handle:
                    descriptor_open = False
                    handle.write((json.dumps(metadata, sort_keys=True) + "\n").encode("utf-8"))
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as exc:
                raise ArchiveChunkError("cannot durably write archive chunk lock") from exc
            lock_stat = SourceStat.from_os_stat(
                os.stat(lock_name, dir_fd=parent_fd, follow_symlinks=False)
            )
            yield
        finally:
            if descriptor_open:
                os.close(descriptor)
            try:
                current = SourceStat.from_os_stat(
                    os.stat(lock_name, dir_fd=parent_fd, follow_symlinks=False)
                )
            except OSError:
                current = None
            if lock_stat is not None and current == lock_stat:
                try:
                    os.unlink(lock_name, dir_fd=parent_fd)
                except OSError as exc:
                    raise ArchiveChunkPartialWriteError(
                        "archive chunk lock cleanup failed; manual verification required"
                    ) from exc
            elif lock_stat is not None:
                raise ArchiveChunkPartialWriteError(
                    "archive chunk lock ownership changed; foreign lock was preserved"
                )
            elif (
                lock_stat is None
                and current is not None
                and current.device == created.device
                and current.inode == created.inode
            ):
                try:
                    os.unlink(lock_name, dir_fd=parent_fd)
                except OSError:
                    pass
    finally:
        if owned_parent_fd is not None:
            os.close(owned_parent_fd)


def _result(
    *,
    source_id: str,
    archive_id: str,
    package: dict[str, Any],
    archive_path: Path | None,
    manifest_proof: dict[str, Any] | None,
    parts: list[dict[str, Any]],
    idempotent: bool,
) -> dict[str, Any]:
    return {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": source_id,
        "archive_id": archive_id,
        "chunking_required": package["byte_size"] > MAX_PART_BYTES,
        "archive_path": archive_path.as_posix() if archive_path is not None else None,
        "manifest_path": (
            (archive_path / MANIFEST_FILENAME).as_posix() if archive_path is not None else None
        ),
        "package": package,
        "part_count": len(parts),
        "parts": parts,
        "max_part_bytes": MAX_PART_BYTES,
        "largest_part_bytes": max((int(part["byte_size"]) for part in parts), default=0),
        "manifest_sha256": manifest_proof["manifest_sha256"] if manifest_proof else None,
        "manifest_bytes": manifest_proof["manifest_bytes"] if manifest_proof else 0,
        "idempotent": idempotent,
        "source_mutation": False,
        "existing_archive_rewritten": False,
        "restore_implemented": False,
        "remote_push": False,
    }


def chunk_archive_package(
    database_dir: Path,
    package_path: Path,
    source_id: str,
    archive_id: str,
) -> dict[str, Any]:
    """Split a package above 45 MiB and publish a deterministic archive directory."""

    source_id = _validate_portable_id(source_id, "source_id", max_length=64)
    archive_id = _validate_portable_id(archive_id, "archive_id", max_length=128)
    try:
        database_dir = database_dir.resolve(strict=True)
    except OSError as exc:
        raise ArchiveChunkError("database directory is missing or unreadable") from exc
    if not database_dir.is_dir():
        raise ArchiveChunkError("database directory must be a directory")
    load_archive_chunking_contract(database_dir, database_dir / CONTRACT_PATH)
    package_path, package_stat = _canonical_regular_file(package_path)
    candidate_archive_path = database_dir / ARCHIVE_ROOT / source_id / archive_id

    if package_stat.size_bytes <= MAX_PART_BYTES:
        if os.path.lexists(candidate_archive_path):
            raise ArchiveChunkError(
                "archive id already exists even though this package does not require chunking"
            )
        try:
            fingerprint = guarded_sha256_file(package_path)
        except RawLedgerError as exc:
            raise ArchiveChunkError(str(exc)) from exc
        package = {
            "filename": _safe_package_filename(package_path.name),
            "byte_size": fingerprint["size_bytes"],
            "sha256": fingerprint["sha256"],
        }
        return _result(
            source_id=source_id,
            archive_id=archive_id,
            package=package,
            archive_path=None,
            manifest_proof=None,
            parts=[],
            idempotent=True,
        )

    if candidate_archive_path == package_path or candidate_archive_path in package_path.parents:
        raise ArchiveChunkError("archive package cannot be inside its output directory")

    with _open_archive_parent(database_dir, source_id) as (archive_parent, parent_fd):
        archive_path = archive_parent / archive_id
        with archive_chunk_lock(archive_path, parent_fd=parent_fd):
            existing_fd = _try_open_archive_at(parent_fd, archive_id)
            if existing_fd is not None:
                try:
                    package, parts = _scan_package(package_path, archive_id, package_stat, None)
                    manifest = _build_manifest(source_id, archive_id, package, parts)
                    proof = _verify_archive_fd(existing_fd, manifest)
                    _assert_archive_name_identity(parent_fd, archive_id, existing_fd)
                finally:
                    os.close(existing_fd)
                return _result(
                    source_id=source_id,
                    archive_id=archive_id,
                    package=package,
                    archive_path=ARCHIVE_ROOT / source_id / archive_id,
                    manifest_proof=proof,
                    parts=parts,
                    idempotent=True,
                )

            try:
                os.mkdir(archive_id, mode=0o700, dir_fd=parent_fd)
            except FileExistsError as exc:
                raise ArchiveChunkError(
                    "archive output appeared during exclusive reservation; overwrite is forbidden"
                ) from exc
            except OSError as exc:
                raise ArchiveChunkError("cannot reserve archive output directory") from exc

            archive_fd = None
            created_part_stats: dict[str, SourceStat] = {}
            try:
                archive_fd = _open_directory_at(parent_fd, archive_id, "reserved archive output")
                _assert_archive_name_identity(parent_fd, archive_id, archive_fd)
                try:
                    os.mkdir(PARTS_DIRECTORY, mode=0o700, dir_fd=archive_fd)
                except OSError as exc:
                    raise ArchiveChunkError("cannot create reserved archive parts directory") from exc
                parts_fd = _open_directory_at(archive_fd, PARTS_DIRECTORY, "reserved archive parts")
                try:
                    package, parts = _scan_package(
                        package_path,
                        archive_id,
                        package_stat,
                        parts_fd,
                        created_part_stats,
                    )
                    _fsync_directory_fd(parts_fd, "archive parts")
                finally:
                    os.close(parts_fd)
                manifest = _build_manifest(source_id, archive_id, package, parts)
                _write_durable_file_at(archive_fd, MANIFEST_FILENAME, _manifest_bytes(manifest))
                _fsync_directory_fd(archive_fd, "archive output")
                proof = _verify_archive_fd(archive_fd, manifest)
                _assert_archive_name_identity(parent_fd, archive_id, archive_fd)
                try:
                    _fsync_directory_fd(parent_fd, "archive parent")
                except ArchiveChunkError as exc:
                    raise ArchiveChunkPostPublishError(
                        "archive chunks were published but parent-directory durability is unverified"
                    ) from exc
                _assert_archive_name_identity(parent_fd, archive_id, archive_fd)
            except ArchiveChunkPostPublishError:
                raise
            except Exception as exc:
                if archive_fd is None or not _cleanup_owned_archive(
                    parent_fd,
                    archive_id,
                    archive_fd,
                    created_part_stats,
                ):
                    raise ArchiveChunkPartialWriteError(
                        "reserved archive may be incomplete; ownership changed or cleanup durability "
                        "could not be proven"
                    ) from exc
                raise
            finally:
                if archive_fd is not None:
                    os.close(archive_fd)
            return _result(
                source_id=source_id,
                archive_id=archive_id,
                package=package,
                archive_path=ARCHIVE_ROOT / source_id / archive_id,
                manifest_proof=proof,
                parts=parts,
                idempotent=False,
            )


__all__ = (
    "ACCEPTANCE_ID",
    "ARCHIVE_ROOT",
    "ArchiveChunkError",
    "ArchiveChunkPartialWriteError",
    "ArchiveChunkPostPublishError",
    "CONTRACT_PATH",
    "CONTRACT_SCHEMA_VERSION",
    "GITHUB_HARD_LIMIT_BYTES",
    "GITHUB_WARNING_BYTES",
    "MANIFEST_FILENAME",
    "MANIFEST_SCHEMA_VERSION",
    "MAX_PART_BYTES",
    "PART_INDEX_WIDTH",
    "PARTS_DIRECTORY",
    "RESULT_SCHEMA_VERSION",
    "TASK_ID",
    "archive_chunk_lock",
    "archive_chunk_lock_path",
    "chunk_archive_package",
    "inspect_archive_chunk_lock",
    "load_archive_chunking_contract",
    "validate_chunk_manifest",
)
