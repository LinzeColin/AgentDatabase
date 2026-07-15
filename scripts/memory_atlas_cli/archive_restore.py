"""Manifest-bound archive verification and restoration for S06-P2-T3."""

from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import stat as stat_module
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any, Iterator

from memory_atlas_cli.archive_chunking import (
    ARCHIVE_ROOT,
    MANIFEST_FILENAME,
    MANIFEST_SCHEMA_VERSION,
    PARTS_DIRECTORY,
    ArchiveChunkError,
    validate_chunk_manifest,
)
from memory_atlas_cli.raw_ledger import SourceStat


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("config/data_sources/archive_restore.json")
CONTRACT_SCHEMA_VERSION = "memory_atlas.archive_restore.v1_2_1_s06_p2_t3"
RESULT_SCHEMA_VERSION = "memory_atlas.archive_restore_result.v1_2_1_s06_p2_t3"
ERROR_SCHEMA_VERSION = "memory_atlas.archive_restore_error.v1_2_1_s06_p2_t3"
TASK_ID = "S06-P2-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S06-P2-T3"
POLICY_ID = "manifest_bound_restore_verify"
CHATGPT_LEGACY_SCHEMA = "memory_atlas_raw_archive_manifest.v1"
BRANCH_LEGACY_SCHEMA = "codexproject_remote_branch_archive_manifest.v1"
SUPPORTED_MANIFEST_SCHEMAS = (
    MANIFEST_SCHEMA_VERSION,
    CHATGPT_LEGACY_SCHEMA,
    BRANCH_LEGACY_SCHEMA,
)
READ_CHUNK_BYTES = 1024 * 1024
MAX_CONTRACT_BYTES = 64 * 1024
MAX_MANIFEST_BYTES = 4 * 1024 * 1024
LEGACY_PART_BYTES = 90 * 1024 * 1024
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
_WINDOWS_RESERVED_ID_RE = re.compile(
    r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$",
    re.IGNORECASE,
)


class ArchiveRestoreError(ValueError):
    """Raised when archive integrity or safe restoration cannot be proven."""


class ArchiveRestorePostPublishError(ArchiveRestoreError):
    """Raised when a complete output exists but parent durability is unverified."""


class ArchiveRestoreOutputConflictError(ArchiveRestoreError):
    """Raised when the requested output path already exists but is not reusable."""


class ArchiveRestorePartialWriteError(ArchiveRestoreError):
    """Raised when an owned temporary output cannot be safely cleaned up."""

    def __init__(
        self,
        message: str,
        *,
        output_may_exist: bool = False,
        output_complete: bool = False,
        temporary_output_may_exist: bool = True,
    ) -> None:
        super().__init__(message)
        self.output_may_exist = output_may_exist
        self.output_complete = output_complete
        self.temporary_output_may_exist = temporary_output_may_exist


@dataclass(frozen=True)
class PartSpec:
    index: int
    filename: str
    basename: str
    byte_size: int
    sha256: str


@dataclass(frozen=True)
class ArchiveSpec:
    manifest_schema_version: str
    package_filename: str
    package_byte_size: int
    package_sha256: str
    parts: tuple[PartSpec, ...]
    expected_root_entries: frozenset[str]
    legacy_read_only: bool


@dataclass(frozen=True)
class OpenArchive:
    archive_path: Path
    archive_fd: int
    chain: tuple[tuple[int, str, int, SourceStat], ...]


@dataclass(frozen=True)
class LoadedArchive:
    spec: ArchiveSpec
    manifest_sha256: str
    manifest_bytes: int
    archive_stat: SourceStat
    parts_fd: int
    parts_stat: SourceStat
    control_stats: dict[str, SourceStat]


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ArchiveRestoreError(f"{field} must be an object")
    return value


def _exact_keys(value: dict[str, Any], expected: set[str], field: str) -> None:
    if set(value) != expected:
        raise ArchiveRestoreError(f"{field} keys do not match the supported manifest contract")


def _valid_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _portable_id(value: Any, field: str, *, max_length: int) -> str:
    if not isinstance(value, str) or not value or value != value.strip():
        raise ArchiveRestoreError(f"{field} must be a non-empty portable identifier")
    if len(value) > max_length or not _PORTABLE_ID_RE.fullmatch(value):
        raise ArchiveRestoreError(f"{field} is not a portable identifier")
    if _WINDOWS_RESERVED_ID_RE.fullmatch(value):
        raise ArchiveRestoreError(f"{field} is a reserved Windows path component")
    return value


def _safe_basename(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value in {".", ".."}:
        raise ArchiveRestoreError(f"{field} is invalid")
    if "\n" in value or "\r" in value or "/" in value or "\\" in value:
        raise ArchiveRestoreError(f"{field} must be a basename")
    if PurePosixPath(value).name != value or PureWindowsPath(value).name != value:
        raise ArchiveRestoreError(f"{field} must be portable")
    return value


def _safe_part_path(value: Any, field: str) -> tuple[str, str]:
    if not isinstance(value, str) or "\\" in value:
        raise ArchiveRestoreError(f"{field} must be a portable parts path")
    path = PurePosixPath(value)
    if path.is_absolute() or len(path.parts) != 2 or path.parts[0] != PARTS_DIRECTORY:
        raise ArchiveRestoreError(f"{field} must be directly under {PARTS_DIRECTORY}/")
    basename = _safe_basename(path.parts[1], field)
    if path.as_posix() != value:
        raise ArchiveRestoreError(f"{field} is not canonical")
    return value, basename


def _positive_int(value: Any, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ArchiveRestoreError(f"{field} must be a positive integer")
    return value


def _read_regular_bytes(path: Path, *, max_bytes: int, label: str) -> bytes:
    descriptor = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        before = SourceStat.from_os_stat(os.fstat(descriptor))
        if not stat_module.S_ISREG(before.mode) or before.size_bytes > max_bytes:
            raise ArchiveRestoreError(f"{label} must be a bounded regular file")
        payload = _read_exact_fd(descriptor, before.size_bytes, label)
        if SourceStat.from_os_stat(os.fstat(descriptor)) != before:
            raise ArchiveRestoreError(f"{label} changed while it was read")
        return payload
    except ArchiveRestoreError:
        raise
    except OSError as exc:
        raise ArchiveRestoreError(f"{label} is missing or unreadable") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def load_archive_restore_contract(
    root: Path = PACKAGE_ROOT,
    path: Path | None = None,
) -> dict[str, Any]:
    contract_path = path or (root.resolve() / CONTRACT_PATH)
    try:
        payload = json.loads(
            _read_regular_bytes(
                contract_path,
                max_bytes=MAX_CONTRACT_BYTES,
                label="archive-restore contract",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveRestoreError("cannot read the canonical archive-restore contract") from exc
    contract = _mapping(payload, "archive_restore")
    _exact_keys(
        contract,
        {
            "schema_version",
            "task_id",
            "acceptance_id",
            "policy",
            "archive_root",
            "supported_manifest_schemas",
            "verification",
            "restore",
            "phase_boundary",
        },
        "archive_restore",
    )
    if (
        contract.get("schema_version") != CONTRACT_SCHEMA_VERSION
        or contract.get("task_id") != TASK_ID
        or contract.get("acceptance_id") != ACCEPTANCE_ID
        or contract.get("policy") != POLICY_ID
        or contract.get("archive_root") != ARCHIVE_ROOT.as_posix()
    ):
        raise ArchiveRestoreError("archive-restore contract identity is unsupported")
    if _mapping(contract.get("supported_manifest_schemas"), "supported_manifest_schemas") != {
        "canonical": MANIFEST_SCHEMA_VERSION,
        "legacy_read_only": [CHATGPT_LEGACY_SCHEMA, BRANCH_LEGACY_SCHEMA],
    }:
        raise ArchiveRestoreError("supported archive manifest schemas drifted")
    if _mapping(contract.get("verification"), "verification") != {
        "manifest_filename": MANIFEST_FILENAME,
        "parts_directory": PARTS_DIRECTORY,
        "hash_algorithm": "sha256",
        "read_chunk_bytes": READ_CHUNK_BYTES,
        "ordered_indices_required": True,
        "exact_part_inventory_required": True,
        "per_part_bytes_and_hash_required": True,
        "package_bytes_and_hash_required": True,
        "symlinks_forbidden": True,
        "source_identity_guard": True,
        "manifest_commands_are_metadata_only": True,
    }:
        raise ArchiveRestoreError("archive verification rules drifted")
    if _mapping(contract.get("restore"), "restore") != {
        "explicit_output_required": True,
        "output_must_be_outside_archive": True,
        "output_parent_must_exist": True,
        "exclusive_temp_reservation": True,
        "hard_link_publish_no_replace": True,
        "existing_output_policy": "verify_identical_never_rewrite",
        "fsync_output_and_parent": True,
        "failure_cleanup_requires_identity": True,
        "partial_or_post_publish_state_reported": True,
    }:
        raise ArchiveRestoreError("archive restore publication rules drifted")
    if _mapping(contract.get("phase_boundary"), "phase_boundary") != {
        "does_not_modify_archive_or_parts": True,
        "does_not_modify_public_raw_or_ledger": True,
        "does_not_rewrite_legacy_archives": True,
        "does_not_execute_manifest_commands": True,
        "does_not_push_remote": True,
        "next_task": "S06-P3-T1",
    }:
        raise ArchiveRestoreError("phase_boundary exceeds S06-P2-T3")
    return contract


def _read_exact_fd(descriptor: int, byte_size: int, label: str) -> bytes:
    chunks: list[bytes] = []
    remaining = byte_size
    while remaining:
        chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
        if not chunk:
            raise ArchiveRestoreError(f"{label} ended before its recorded size")
        chunks.append(chunk)
        remaining -= len(chunk)
    if os.read(descriptor, 1):
        raise ArchiveRestoreError(f"{label} grew while it was read")
    return b"".join(chunks)


def _part_specs(parts_value: Any, *, max_part_bytes: int) -> tuple[PartSpec, ...]:
    if not isinstance(parts_value, list) or not parts_value:
        raise ArchiveRestoreError("manifest parts must be a non-empty ordered list")
    parts: list[PartSpec] = []
    seen: set[str] = set()
    for expected_index, value in enumerate(parts_value):
        part = _mapping(value, f"parts[{expected_index}]")
        _exact_keys(part, {"index", "filename", "byte_size", "sha256"}, f"parts[{expected_index}]")
        if part.get("index") != expected_index:
            raise ArchiveRestoreError("manifest part indices are not contiguous and ordered")
        filename, basename = _safe_part_path(part.get("filename"), f"parts[{expected_index}].filename")
        if basename in seen:
            raise ArchiveRestoreError("manifest contains duplicate part filenames")
        seen.add(basename)
        byte_size = _positive_int(part.get("byte_size"), f"parts[{expected_index}].byte_size")
        if byte_size > max_part_bytes:
            raise ArchiveRestoreError("manifest part exceeds its declared size boundary")
        if expected_index < len(parts_value) - 1 and byte_size != max_part_bytes:
            raise ArchiveRestoreError("only the final archive part may be shorter")
        sha256 = part.get("sha256")
        if not _valid_sha256(sha256):
            raise ArchiveRestoreError(f"parts[{expected_index}].sha256 is invalid")
        parts.append(PartSpec(expected_index, filename, basename, byte_size, sha256))
    return tuple(parts)


def _package_fields(value: Any, field: str, expected_keys: set[str]) -> tuple[str, int, str]:
    package = _mapping(value, field)
    _exact_keys(package, expected_keys, field)
    filename = _safe_basename(package.get("filename"), f"{field}.filename")
    byte_size = _positive_int(package.get("byte_size"), f"{field}.byte_size")
    sha256 = package.get("sha256")
    if not _valid_sha256(sha256):
        raise ArchiveRestoreError(f"{field}.sha256 is invalid")
    return filename, byte_size, sha256


def _assert_total_bytes(parts: tuple[PartSpec, ...], package_bytes: int) -> None:
    if sum(part.byte_size for part in parts) != package_bytes:
        raise ArchiveRestoreError("manifest part bytes do not equal package bytes")


def _validate_legacy_part_names(parts: tuple[PartSpec, ...], prefix: Any) -> None:
    if not isinstance(prefix, str) or not prefix.startswith(f"{PARTS_DIRECTORY}/"):
        raise ArchiveRestoreError("legacy part prefix is invalid")
    for part in parts:
        if part.filename != f"{prefix}{part.index:03d}":
            raise ArchiveRestoreError("legacy part filename does not match its declared prefix")


def _normalize_canonical_manifest(
    payload: dict[str, Any],
    source_id: str,
    archive_id: str,
) -> ArchiveSpec:
    try:
        manifest = validate_chunk_manifest(payload)
    except ArchiveChunkError as exc:
        raise ArchiveRestoreError(str(exc)) from exc
    if manifest["source_id"] != source_id or manifest["archive_id"] != archive_id:
        raise ArchiveRestoreError("canonical manifest does not match the requested archive")
    package = manifest["package"]
    parts = _part_specs(manifest["parts"], max_part_bytes=manifest["split"]["max_part_bytes"])
    _assert_total_bytes(parts, package["byte_size"])
    return ArchiveSpec(
        manifest_schema_version=MANIFEST_SCHEMA_VERSION,
        package_filename=package["filename"],
        package_byte_size=package["byte_size"],
        package_sha256=package["sha256"],
        parts=parts,
        expected_root_entries=frozenset({MANIFEST_FILENAME, PARTS_DIRECTORY}),
        legacy_read_only=False,
    )


def _expected_legacy_path(database_dir: Path, source_id: str, archive_id: str) -> str:
    return (Path(database_dir.name) / ARCHIVE_ROOT / source_id / archive_id).as_posix()


def _normalize_chatgpt_legacy_manifest(
    payload: dict[str, Any],
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> ArchiveSpec:
    _exact_keys(
        payload,
        {
            "schema_version",
            "archive_id",
            "source",
            "visibility",
            "repository",
            "path",
            "recorded_at_utc",
            "user_confirmation",
            "original_file",
            "split",
            "parts",
        },
        "legacy ChatGPT manifest",
    )
    if payload.get("path") != _expected_legacy_path(database_dir, source_id, archive_id):
        raise ArchiveRestoreError("legacy ChatGPT manifest path does not match the requested archive")
    filename, package_bytes, package_sha256 = _package_fields(
        payload.get("original_file"),
        "original_file",
        {"filename", "byte_size", "sha256", "local_source_path_at_upload_time"},
    )
    split = _mapping(payload.get("split"), "split")
    _exact_keys(
        split,
        {"method", "part_prefix", "part_count", "max_part_bytes", "restore_command"},
        "split",
    )
    if (
        split.get("method") != "split -b 90m -a 3 -d"
        or split.get("max_part_bytes") != LEGACY_PART_BYTES
        or not isinstance(split.get("restore_command"), str)
        or not split.get("restore_command")
    ):
        raise ArchiveRestoreError("legacy ChatGPT split contract is unsupported")
    parts = _part_specs(payload.get("parts"), max_part_bytes=LEGACY_PART_BYTES)
    _validate_legacy_part_names(parts, split.get("part_prefix"))
    if split.get("part_count") != len(parts):
        raise ArchiveRestoreError("legacy ChatGPT part_count does not match parts")
    _assert_total_bytes(parts, package_bytes)
    return ArchiveSpec(
        CHATGPT_LEGACY_SCHEMA,
        filename,
        package_bytes,
        package_sha256,
        parts,
        frozenset({MANIFEST_FILENAME, PARTS_DIRECTORY, "README.md", "restore.sh"}),
        True,
    )


def _normalize_branch_legacy_manifest(
    payload: dict[str, Any],
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> ArchiveSpec:
    _exact_keys(
        payload,
        {
            "archive_id",
            "branch_count",
            "branches",
            "bundle",
            "created_at_utc",
            "delete_remote_branches_after_archive",
            "main_ref_at_archive_time",
            "parts",
            "path",
            "purpose",
            "repository",
            "schema_version",
            "split",
        },
        "legacy branch manifest",
    )
    if payload.get("path") != _expected_legacy_path(database_dir, source_id, archive_id):
        raise ArchiveRestoreError("legacy branch manifest path does not match the requested archive")
    filename, package_bytes, package_sha256 = _package_fields(
        payload.get("bundle"),
        "bundle",
        {"filename", "byte_size", "sha256", "verify_command"},
    )
    if not isinstance(payload["bundle"].get("verify_command"), str) or not payload["bundle"].get(
        "verify_command"
    ):
        raise ArchiveRestoreError("legacy bundle verify_command must remain metadata text")
    split = _mapping(payload.get("split"), "split")
    _exact_keys(
        split,
        {"method", "part_count", "max_part_bytes", "restore_command"},
        "split",
    )
    if (
        split.get("method") != "split -b 90m -a 3 -d"
        or split.get("max_part_bytes") != LEGACY_PART_BYTES
        or not isinstance(split.get("restore_command"), str)
        or not split.get("restore_command")
    ):
        raise ArchiveRestoreError("legacy branch split contract is unsupported")
    parts = _part_specs(payload.get("parts"), max_part_bytes=LEGACY_PART_BYTES)
    _validate_legacy_part_names(parts, f"{PARTS_DIRECTORY}/{filename}.part-")
    if split.get("part_count") != len(parts):
        raise ArchiveRestoreError("legacy branch part_count does not match parts")
    _assert_total_bytes(parts, package_bytes)
    return ArchiveSpec(
        BRANCH_LEGACY_SCHEMA,
        filename,
        package_bytes,
        package_sha256,
        parts,
        frozenset({MANIFEST_FILENAME, PARTS_DIRECTORY, "README.md", "restore.sh"}),
        True,
    )


def _normalize_manifest(
    payload: Any,
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> ArchiveSpec:
    manifest = _mapping(payload, "archive manifest")
    schema_version = manifest.get("schema_version")
    if schema_version == MANIFEST_SCHEMA_VERSION:
        return _normalize_canonical_manifest(manifest, source_id, archive_id)
    if schema_version == CHATGPT_LEGACY_SCHEMA:
        return _normalize_chatgpt_legacy_manifest(manifest, database_dir, source_id, archive_id)
    if schema_version == BRANCH_LEGACY_SCHEMA:
        return _normalize_branch_legacy_manifest(manifest, database_dir, source_id, archive_id)
    raise ArchiveRestoreError("archive manifest schema_version is unsupported")


def _canonical_database_dir(database_dir: Path) -> Path:
    lexical = Path(os.path.abspath(os.fspath(database_dir)))
    try:
        resolved = database_dir.resolve(strict=True)
    except OSError as exc:
        raise ArchiveRestoreError("database directory is missing or unreadable") from exc
    if lexical != resolved or not resolved.is_dir():
        raise ArchiveRestoreError("database directory must not contain symlink components")
    return resolved


def _open_directory_at(parent_fd: int, name: str, label: str) -> int:
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except OSError as exc:
        raise ArchiveRestoreError(f"{label} must be a non-symlink directory") from exc
    if not stat_module.S_ISDIR(os.fstat(descriptor).st_mode):
        os.close(descriptor)
        raise ArchiveRestoreError(f"{label} must be a directory")
    return descriptor


def _same_identity(left: SourceStat, right: SourceStat) -> bool:
    return left.device == right.device and left.inode == right.inode and left.mode == right.mode


def _assert_chain_identity(open_archive: OpenArchive) -> None:
    for parent_fd, name, child_fd, expected in open_archive.chain:
        current = SourceStat.from_os_stat(os.fstat(child_fd))
        try:
            named = SourceStat.from_os_stat(
                os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
            )
        except OSError as exc:
            raise ArchiveRestoreError("archive path identity changed during verification") from exc
        if not _same_identity(current, expected) or not _same_identity(named, expected):
            raise ArchiveRestoreError("archive path identity changed during verification")


@contextmanager
def _open_archive(
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> Iterator[OpenArchive]:
    source_id = _portable_id(source_id, "source_id", max_length=64)
    archive_id = _portable_id(archive_id, "archive_id", max_length=128)
    database_dir = _canonical_database_dir(database_dir)
    opened: list[int] = []
    chain: list[tuple[int, str, int, SourceStat]] = []
    try:
        root_fd = os.open(
            database_dir,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        opened.append(root_fd)
        current_fd = root_fd
        for component in (*ARCHIVE_ROOT.parts, source_id, archive_id):
            child_fd = _open_directory_at(current_fd, component, "canonical archive path")
            opened.append(child_fd)
            child_stat = SourceStat.from_os_stat(os.fstat(child_fd))
            chain.append((current_fd, component, child_fd, child_stat))
            current_fd = child_fd
        opened_archive = OpenArchive(
            database_dir / ARCHIVE_ROOT / source_id / archive_id,
            current_fd,
            tuple(chain),
        )
        yield opened_archive
        _assert_chain_identity(opened_archive)
    except ArchiveRestoreError:
        raise
    except OSError as exc:
        raise ArchiveRestoreError("cannot safely open the requested archive") from exc
    finally:
        for descriptor in reversed(opened):
            os.close(descriptor)


def _read_regular_file_at(
    directory_fd: int,
    name: str,
    label: str,
    *,
    max_bytes: int,
) -> bytes:
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=directory_fd,
        )
        before = SourceStat.from_os_stat(os.fstat(descriptor))
        if not stat_module.S_ISREG(before.mode) or before.size_bytes > max_bytes:
            raise ArchiveRestoreError(f"{label} must be a bounded regular file")
        payload = _read_exact_fd(descriptor, before.size_bytes, label)
        if SourceStat.from_os_stat(os.fstat(descriptor)) != before:
            raise ArchiveRestoreError(f"{label} changed while it was read")
        return payload
    except ArchiveRestoreError:
        raise
    except OSError as exc:
        raise ArchiveRestoreError(f"cannot read {label}") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _validate_control_entries(
    archive_fd: int,
    expected_entries: frozenset[str],
) -> dict[str, SourceStat]:
    if set(os.listdir(archive_fd)) != set(expected_entries):
        raise ArchiveRestoreError("archive root inventory does not match its manifest schema")
    control_stats: dict[str, SourceStat] = {}
    for name in expected_entries - {PARTS_DIRECTORY}:
        try:
            metadata = SourceStat.from_os_stat(
                os.stat(name, dir_fd=archive_fd, follow_symlinks=False)
            )
        except OSError as exc:
            raise ArchiveRestoreError(f"archive control file is unreadable: {name}") from exc
        if not stat_module.S_ISREG(metadata.mode):
            raise ArchiveRestoreError(f"archive control file must be regular: {name}")
        control_stats[name] = metadata
    return control_stats


def _load_open_archive(
    open_archive: OpenArchive,
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> LoadedArchive:
    archive_stat = SourceStat.from_os_stat(os.fstat(open_archive.archive_fd))
    manifest_bytes = _read_regular_file_at(
        open_archive.archive_fd,
        MANIFEST_FILENAME,
        "archive manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    try:
        payload = json.loads(manifest_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ArchiveRestoreError("archive manifest is not strict UTF-8 JSON") from exc
    spec = _normalize_manifest(payload, database_dir, source_id, archive_id)
    control_stats = _validate_control_entries(
        open_archive.archive_fd,
        spec.expected_root_entries,
    )
    parts_fd = _open_directory_at(open_archive.archive_fd, PARTS_DIRECTORY, "archive parts")
    expected_names = {part.basename for part in spec.parts}
    if set(os.listdir(parts_fd)) != expected_names:
        os.close(parts_fd)
        raise ArchiveRestoreError("archive part inventory does not match the manifest")
    return LoadedArchive(
        spec=spec,
        manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest(),
        manifest_bytes=len(manifest_bytes),
        archive_stat=archive_stat,
        parts_fd=parts_fd,
        parts_stat=SourceStat.from_os_stat(os.fstat(parts_fd)),
        control_stats=control_stats,
    )


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise ArchiveRestoreError("restored output write made no progress")
        offset += written


def _stream_and_verify(loaded: LoadedArchive, output_fd: int | None) -> dict[str, Any]:
    package_digest = hashlib.sha256()
    total_bytes = 0
    part_stats: dict[str, SourceStat] = {}
    for part in loaded.spec.parts:
        descriptor = None
        try:
            descriptor = os.open(
                part.basename,
                os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=loaded.parts_fd,
            )
            before = SourceStat.from_os_stat(os.fstat(descriptor))
            if not stat_module.S_ISREG(before.mode) or before.size_bytes != part.byte_size:
                raise ArchiveRestoreError(f"archive part byte_size mismatch: {part.filename}")
            part_digest = hashlib.sha256()
            remaining = part.byte_size
            while remaining:
                chunk = os.read(descriptor, min(READ_CHUNK_BYTES, remaining))
                if not chunk:
                    raise ArchiveRestoreError(f"archive part ended early: {part.filename}")
                part_digest.update(chunk)
                package_digest.update(chunk)
                if output_fd is not None:
                    _write_all(output_fd, chunk)
                total_bytes += len(chunk)
                remaining -= len(chunk)
            if os.read(descriptor, 1):
                raise ArchiveRestoreError(f"archive part grew while it was read: {part.filename}")
            if SourceStat.from_os_stat(os.fstat(descriptor)) != before:
                raise ArchiveRestoreError(f"archive part changed while it was read: {part.filename}")
            if part_digest.hexdigest() != part.sha256:
                raise ArchiveRestoreError(f"archive part SHA-256 mismatch: {part.filename}")
            part_stats[part.basename] = before
        except ArchiveRestoreError:
            raise
        except OSError as exc:
            raise ArchiveRestoreError(f"cannot read archive part: {part.filename}") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
    if total_bytes != loaded.spec.package_byte_size:
        raise ArchiveRestoreError("restored package byte_size does not match the manifest")
    package_sha256 = package_digest.hexdigest()
    if package_sha256 != loaded.spec.package_sha256:
        raise ArchiveRestoreError("restored package SHA-256 does not match the manifest")
    return {
        "byte_size": total_bytes,
        "sha256": package_sha256,
        "part_stats": part_stats,
    }


def _finish_archive_verification(
    open_archive: OpenArchive,
    loaded: LoadedArchive,
    proof: dict[str, Any],
) -> None:
    if set(os.listdir(loaded.parts_fd)) != {part.basename for part in loaded.spec.parts}:
        raise ArchiveRestoreError("archive part inventory changed during verification")
    if SourceStat.from_os_stat(os.fstat(loaded.parts_fd)) != loaded.parts_stat:
        raise ArchiveRestoreError("archive parts directory changed during verification")
    for name, expected in proof["part_stats"].items():
        try:
            current = SourceStat.from_os_stat(
                os.stat(name, dir_fd=loaded.parts_fd, follow_symlinks=False)
            )
        except OSError as exc:
            raise ArchiveRestoreError("archive part identity changed after verification") from exc
        if current != expected or not stat_module.S_ISREG(current.mode):
            raise ArchiveRestoreError("archive part changed after it was verified")
    current_control_stats = _validate_control_entries(
        open_archive.archive_fd,
        loaded.spec.expected_root_entries,
    )
    if current_control_stats != loaded.control_stats:
        raise ArchiveRestoreError("archive control files changed during verification")
    manifest_bytes = _read_regular_file_at(
        open_archive.archive_fd,
        MANIFEST_FILENAME,
        "archive manifest",
        max_bytes=MAX_MANIFEST_BYTES,
    )
    if (
        len(manifest_bytes) != loaded.manifest_bytes
        or hashlib.sha256(manifest_bytes).hexdigest() != loaded.manifest_sha256
    ):
        raise ArchiveRestoreError("archive manifest changed during verification")
    if SourceStat.from_os_stat(os.fstat(open_archive.archive_fd)) != loaded.archive_stat:
        raise ArchiveRestoreError("archive directory changed during verification")
    _assert_chain_identity(open_archive)


def _result(
    *,
    operation: str,
    source_id: str,
    archive_id: str,
    loaded: LoadedArchive,
    proof: dict[str, Any],
    output_path: Path | None,
    idempotent: bool,
) -> dict[str, Any]:
    return {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "operation": operation,
        "source_id": source_id,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / source_id / archive_id).as_posix(),
        "manifest_schema_version": loaded.spec.manifest_schema_version,
        "manifest_sha256": loaded.manifest_sha256,
        "manifest_bytes": loaded.manifest_bytes,
        "legacy_read_only": loaded.spec.legacy_read_only,
        "package": {
            "filename": loaded.spec.package_filename,
            "byte_size": proof["byte_size"],
            "sha256": proof["sha256"],
        },
        "part_count": len(loaded.spec.parts),
        "verified_part_count": len(loaded.spec.parts),
        "part_verification": "PASS",
        "package_verification": "PASS",
        "output_path": output_path.as_posix() if output_path is not None else None,
        "output_published": output_path is not None,
        "idempotent": idempotent,
        "archive_mutation": False,
        "public_raw_or_ledger_mutation": False,
        "manifest_command_executed": False,
        "remote_push": False,
    }


def verify_archive(
    database_dir: Path,
    source_id: str,
    archive_id: str,
) -> dict[str, Any]:
    """Verify ordered parts and the reconstructed package without writing output."""

    database_dir = _canonical_database_dir(database_dir)
    load_archive_restore_contract(database_dir, database_dir / CONTRACT_PATH)
    with _open_archive(database_dir, source_id, archive_id) as opened:
        loaded = _load_open_archive(opened, database_dir, source_id, archive_id)
        try:
            proof = _stream_and_verify(loaded, None)
            _finish_archive_verification(opened, loaded, proof)
            return _result(
                operation="verify",
                source_id=source_id,
                archive_id=archive_id,
                loaded=loaded,
                proof=proof,
                output_path=None,
                idempotent=True,
            )
        finally:
            os.close(loaded.parts_fd)


def _canonical_output(
    output_path: Path,
    archive_path: Path,
) -> tuple[Path, int, str, SourceStat]:
    if not output_path.name:
        raise ArchiveRestoreError("restore output must name a file")
    name = _safe_basename(output_path.name, "restore output")
    lexical_parent = Path(os.path.abspath(os.fspath(output_path.parent)))
    try:
        parent = output_path.parent.resolve(strict=True)
    except OSError as exc:
        raise ArchiveRestoreError("restore output parent is missing or unreadable") from exc
    if lexical_parent != parent or not parent.is_dir():
        raise ArchiveRestoreError("restore output parent must not contain symlink components")
    canonical = parent / name
    if canonical == archive_path or archive_path in canonical.parents:
        raise ArchiveRestoreError("restore output must be outside the archive directory")
    try:
        parent_fd = os.open(
            parent,
            os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise ArchiveRestoreError("cannot safely open restore output parent") from exc
    return canonical, parent_fd, name, SourceStat.from_os_stat(os.fstat(parent_fd))


def _assert_output_parent_identity(
    parent_fd: int,
    parent_path: Path,
    expected: SourceStat,
) -> None:
    current = SourceStat.from_os_stat(os.fstat(parent_fd))
    try:
        named = SourceStat.from_os_stat(parent_path.stat(follow_symlinks=False))
    except OSError as exc:
        raise ArchiveRestoreError("restore output parent identity changed") from exc
    if not _same_identity(current, expected) or not _same_identity(named, expected):
        raise ArchiveRestoreError("restore output parent identity changed")


def _fingerprint_output_at(parent_fd: int, name: str) -> dict[str, Any] | None:
    descriptor = None
    try:
        descriptor = os.open(
            name,
            os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=parent_fd,
        )
    except FileNotFoundError:
        return None
    except OSError as exc:
        raise ArchiveRestoreOutputConflictError(
            "existing restore output is unsafe or unreadable"
        ) from exc
    try:
        before = SourceStat.from_os_stat(os.fstat(descriptor))
        if not stat_module.S_ISREG(before.mode):
            raise ArchiveRestoreOutputConflictError(
                "existing restore output must be a regular file"
            )
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(descriptor, READ_CHUNK_BYTES)
            if not chunk:
                break
            digest.update(chunk)
            total += len(chunk)
        if SourceStat.from_os_stat(os.fstat(descriptor)) != before:
            raise ArchiveRestoreOutputConflictError(
                "existing restore output changed while it was verified"
            )
        return {
            "byte_size": total,
            "sha256": digest.hexdigest(),
            "stat": before,
        }
    finally:
        os.close(descriptor)


def _matching_existing_output(
    parent_fd: int,
    name: str,
    spec: ArchiveSpec,
) -> dict[str, Any] | None:
    fingerprint = _fingerprint_output_at(parent_fd, name)
    if fingerprint is None:
        return None
    if (
        fingerprint["byte_size"] != spec.package_byte_size
        or fingerprint["sha256"] != spec.package_sha256
    ):
        raise ArchiveRestoreOutputConflictError(
            "existing restore output conflicts with the manifest"
        )
    return fingerprint


def _assert_existing_output_unchanged(
    parent_fd: int,
    name: str,
    expected: dict[str, Any],
) -> None:
    try:
        current = SourceStat.from_os_stat(
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        )
    except OSError as exc:
        raise ArchiveRestoreOutputConflictError(
            "existing restore output identity changed"
        ) from exc
    if current != expected["stat"] or not stat_module.S_ISREG(current.mode):
        raise ArchiveRestoreOutputConflictError(
            "existing restore output changed during archive verification"
        )


def _remove_owned_temp(parent_fd: int, name: str, expected: SourceStat) -> bool:
    try:
        current = SourceStat.from_os_stat(
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        )
    except FileNotFoundError:
        return True
    except OSError:
        return False
    if not stat_module.S_ISREG(current.mode) or not _same_identity(current, expected):
        return False
    try:
        os.unlink(name, dir_fd=parent_fd)
    except OSError:
        return False
    return True


def _assert_published_identity(parent_fd: int, name: str, expected: SourceStat) -> None:
    try:
        current = SourceStat.from_os_stat(
            os.stat(name, dir_fd=parent_fd, follow_symlinks=False)
        )
    except OSError as exc:
        raise ArchiveRestoreError("published restore output disappeared") from exc
    if not stat_module.S_ISREG(current.mode) or not _same_identity(current, expected):
        raise ArchiveRestoreError("published restore output identity changed")


def _verify_published_output(
    parent_fd: int,
    name: str,
    spec: ArchiveSpec,
    expected_identity: SourceStat,
) -> SourceStat:
    fingerprint = _fingerprint_output_at(parent_fd, name)
    if fingerprint is None:
        raise ArchiveRestoreError("published restore output disappeared")
    if (
        fingerprint["byte_size"] != spec.package_byte_size
        or fingerprint["sha256"] != spec.package_sha256
        or not _same_identity(fingerprint["stat"], expected_identity)
    ):
        raise ArchiveRestoreError("published restore output conflicts with the manifest")
    return fingerprint["stat"]


def restore_archive(
    database_dir: Path,
    source_id: str,
    archive_id: str,
    output_path: Path,
) -> dict[str, Any]:
    """Restore an archive to an explicit no-overwrite output and verify all bytes."""

    database_dir = _canonical_database_dir(database_dir)
    load_archive_restore_contract(database_dir, database_dir / CONTRACT_PATH)
    with _open_archive(database_dir, source_id, archive_id) as opened:
        loaded = _load_open_archive(opened, database_dir, source_id, archive_id)
        output_fd = None
        parent_fd = None
        temp_name = ""
        temp_stat: SourceStat | None = None
        published = False
        published_identity_verified = False
        published_content_verified = False
        canonical_output: Path | None = None
        output_parent_stat: SourceStat | None = None
        try:
            canonical_output, parent_fd, output_name, output_parent_stat = _canonical_output(
                output_path,
                opened.archive_path,
            )
            existing_output = _matching_existing_output(parent_fd, output_name, loaded.spec)
            if existing_output is not None:
                proof = _stream_and_verify(loaded, None)
                _finish_archive_verification(opened, loaded, proof)
                _assert_existing_output_unchanged(parent_fd, output_name, existing_output)
                _assert_output_parent_identity(
                    parent_fd,
                    canonical_output.parent,
                    output_parent_stat,
                )
                return _result(
                    operation="restore",
                    source_id=source_id,
                    archive_id=archive_id,
                    loaded=loaded,
                    proof=proof,
                    output_path=canonical_output,
                    idempotent=True,
                )

            temp_name = f".{output_name}.restore-{os.getpid()}-{secrets.token_hex(8)}.tmp"
            try:
                output_fd = os.open(
                    temp_name,
                    os.O_CREAT
                    | os.O_EXCL
                    | os.O_WRONLY
                    | getattr(os, "O_NOFOLLOW", 0),
                    0o600,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                raise ArchiveRestoreError("cannot reserve restore temporary output") from exc
            temp_stat = SourceStat.from_os_stat(os.fstat(output_fd))
            try:
                proof = _stream_and_verify(loaded, output_fd)
                os.fsync(output_fd)
            except ArchiveRestoreError:
                raise
            except OSError as exc:
                raise ArchiveRestoreError("cannot durably write restored output") from exc
            final_stat = SourceStat.from_os_stat(os.fstat(output_fd))
            if (
                not _same_identity(final_stat, temp_stat)
                or final_stat.size_bytes != loaded.spec.package_byte_size
            ):
                raise ArchiveRestoreError("restored temporary output identity or size changed")
            os.close(output_fd)
            output_fd = None
            try:
                os.link(
                    temp_name,
                    output_name,
                    src_dir_fd=parent_fd,
                    dst_dir_fd=parent_fd,
                    follow_symlinks=False,
                )
            except FileExistsError:
                if not _remove_owned_temp(parent_fd, temp_name, final_stat):
                    raise ArchiveRestorePartialWriteError(
                        "restore output appeared and owned temporary output could not be removed",
                        output_may_exist=True,
                    )
                temp_name = ""
                temp_stat = None
                existing_output = _matching_existing_output(parent_fd, output_name, loaded.spec)
                if existing_output is None:
                    raise ArchiveRestoreError("restore output appeared but could not be verified")
                _finish_archive_verification(opened, loaded, proof)
                _assert_existing_output_unchanged(parent_fd, output_name, existing_output)
                _assert_output_parent_identity(
                    parent_fd,
                    canonical_output.parent,
                    output_parent_stat,
                )
                return _result(
                    operation="restore",
                    source_id=source_id,
                    archive_id=archive_id,
                    loaded=loaded,
                    proof=proof,
                    output_path=canonical_output,
                    idempotent=True,
                )
            except OSError as exc:
                raise ArchiveRestoreError("cannot publish restored output without overwrite") from exc
            published = True
            _assert_published_identity(parent_fd, output_name, final_stat)
            published_identity_verified = True
            try:
                os.unlink(temp_name, dir_fd=parent_fd)
            except OSError as exc:
                raise ArchiveRestorePartialWriteError(
                    "restored output is complete but temporary link cleanup failed",
                    output_may_exist=True,
                    output_complete=True,
                    temporary_output_may_exist=True,
                ) from exc
            temp_name = ""
            temp_stat = None
            _verify_published_output(
                parent_fd,
                output_name,
                loaded.spec,
                final_stat,
            )
            published_content_verified = True
            try:
                os.fsync(parent_fd)
            except OSError as exc:
                try:
                    _verify_published_output(
                        parent_fd,
                        output_name,
                        loaded.spec,
                        final_stat,
                    )
                except ArchiveRestoreError as verify_exc:
                    raise ArchiveRestorePartialWriteError(
                        "parent-directory durability failed and published output changed",
                        output_may_exist=True,
                        output_complete=False,
                        temporary_output_may_exist=False,
                    ) from verify_exc
                raise ArchiveRestorePostPublishError(
                    "restored output is complete but parent-directory durability is unverified"
                ) from exc
            _assert_published_identity(parent_fd, output_name, final_stat)
            _finish_archive_verification(opened, loaded, proof)
            published_content_verified = False
            _verify_published_output(
                parent_fd,
                output_name,
                loaded.spec,
                final_stat,
            )
            published_content_verified = True
            _assert_output_parent_identity(
                parent_fd,
                canonical_output.parent,
                output_parent_stat,
            )
            return _result(
                operation="restore",
                source_id=source_id,
                archive_id=archive_id,
                loaded=loaded,
                proof=proof,
                output_path=canonical_output,
                idempotent=False,
            )
        except (ArchiveRestorePostPublishError, ArchiveRestorePartialWriteError):
            raise
        except Exception as exc:
            if output_fd is not None:
                os.close(output_fd)
                output_fd = None
            if published:
                temporary_output_may_exist = bool(temp_name)
                if (
                    temp_name
                    and temp_stat is not None
                    and parent_fd is not None
                    and _remove_owned_temp(parent_fd, temp_name, temp_stat)
                ):
                    temporary_output_may_exist = False
                raise ArchiveRestorePartialWriteError(
                    "restore output may be published but final state requires manual verification",
                    output_may_exist=True,
                    output_complete=published_identity_verified and published_content_verified,
                    temporary_output_may_exist=temporary_output_may_exist,
                ) from exc
            if temp_name and temp_stat is not None and parent_fd is not None:
                if not _remove_owned_temp(parent_fd, temp_name, temp_stat):
                    raise ArchiveRestorePartialWriteError(
                        "restore failed and temporary output ownership changed; manual verification required",
                        output_may_exist=published,
                        output_complete=published,
                    ) from exc
            raise
        finally:
            if output_fd is not None:
                os.close(output_fd)
            if parent_fd is not None:
                os.close(parent_fd)
            os.close(loaded.parts_fd)


__all__ = (
    "ACCEPTANCE_ID",
    "ArchiveRestoreError",
    "ArchiveRestoreOutputConflictError",
    "ArchiveRestorePartialWriteError",
    "ArchiveRestorePostPublishError",
    "BRANCH_LEGACY_SCHEMA",
    "CHATGPT_LEGACY_SCHEMA",
    "CONTRACT_PATH",
    "CONTRACT_SCHEMA_VERSION",
    "ERROR_SCHEMA_VERSION",
    "RESULT_SCHEMA_VERSION",
    "SUPPORTED_MANIFEST_SCHEMAS",
    "TASK_ID",
    "load_archive_restore_contract",
    "restore_archive",
    "verify_archive",
)
