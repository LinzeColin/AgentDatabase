"""Deterministic lstat-first Skill source inventory and integrity audit."""

from __future__ import annotations

import collections
import hashlib
import os
import posixpath
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from CodexSkills.registry.auto.tools.validate_auto import AutoContract, validate_auto_instance
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from .core import (
    AutoRuntimeError,
    Clock,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    format_utc,
    new_uid,
    sha256_bytes,
)


SOURCE_POLICY_ID = "urn:linzecolin:agentdatabase:skillops:policy:source-material:v1"
VCS_COMPONENTS = {".git", ".hg", ".svn"}
CACHE_COMPONENTS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".venv", "node_modules"}
OS_METADATA_FILES = {".DS_Store", "Thumbs.db"}
ERROR_CODES = {
    "INVALID_PATH_ENCODING",
    "OVERSIZE_NON_POLICY",
    "PERMISSION_ERROR",
    "READ_ERROR",
    "SPECIAL_FILE",
    "STAT_ERROR",
    "SYMLINK_UNSAFE",
}


@dataclass(frozen=True)
class FileEvidence:
    relative_path: str
    byte_count: int
    content_digest: str


@dataclass(frozen=True)
class AliasEvidence:
    alias_path: str
    normalized_target_ref: str
    metadata_digest: str
    content_digest: str


@dataclass(frozen=True)
class ExclusionEvidence:
    reason_code: str
    node_count: int
    file_count: int
    byte_count: int


@dataclass(frozen=True)
class ErrorEvidence:
    reason_code: str
    count: int


@dataclass(frozen=True)
class SourceScanReport:
    source_class: str
    source_root_ref: str
    completeness_status: str
    included_files: Tuple[FileEvidence, ...]
    included_file_count: int
    included_bytes: int
    included_tree_digest: str
    exclusions: Tuple[ExclusionEvidence, ...]
    excluded_node_count: int
    excluded_file_count: int
    excluded_bytes: int
    aliases: Tuple[AliasEvidence, ...]
    oversize_blocked_count: int
    errors: Tuple[ErrorEvidence, ...]
    source_snapshot_digest: str


@dataclass(frozen=True)
class SourceInventoryObservation:
    report: SourceScanReport
    inventory: Mapping[str, object]
    coverage_receipt: Mapping[str, object]


@dataclass(frozen=True)
class _PendingAlias:
    alias_path: str
    target_ref: str
    target_path: Path
    target_is_directory: bool


def _safe_text(value: str) -> bool:
    return not any(0xD800 <= ord(char) <= 0xDFFF for char in value)


def _same_lstat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
    )


def _within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


class SourceScanner:
    def __init__(
        self,
        source_policy: Mapping[str, object],
        *,
        max_file_bytes: int = 95 * 1024 * 1024,
        chunk_bytes: int = 1024 * 1024,
    ) -> None:
        if source_policy.get("policy_id") != SOURCE_POLICY_ID:
            raise AutoRuntimeError("SOURCE_POLICY_ID_MISMATCH")
        if source_policy.get("silent_skip_allowed") is not False:
            raise AutoRuntimeError("SOURCE_POLICY_SILENT_SKIP_MUST_BE_FALSE")
        if max_file_bytes <= 0 or chunk_bytes <= 0:
            raise AutoRuntimeError("SOURCE_SCAN_LIMIT_INVALID")
        self.policy = source_policy
        self.policy_digest = sha256_bytes(canonicalize_object(source_policy))
        self.max_file_bytes = max_file_bytes
        self.chunk_bytes = chunk_bytes

    @staticmethod
    def _exclusion_reason(source_class: str, relative: PurePosixPath, is_dir: bool) -> Optional[str]:
        parts = relative.parts
        if any(part in VCS_COMPONENTS for part in parts):
            return "VCS_METADATA"
        if source_class == "CODEX" and parts and parts[0] == ".system":
            return "SOURCE_OVERLAP"
        if any(part in CACHE_COMPONENTS for part in parts):
            return "CACHE"
        if not is_dir and parts and parts[-1] in OS_METADATA_FILES:
            return "OS_METADATA"
        return None

    def _read_regular(self, path: Path, expected: os.stat_result) -> str:
        if expected.st_size > self.max_file_bytes:
            raise AutoRuntimeError("OVERSIZE_NON_POLICY")
        descriptor: Optional[int] = None
        digest = hashlib.sha256()
        try:
            descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            opened = os.fstat(descriptor)
            if not _same_lstat(expected, opened):
                raise AutoRuntimeError("STAT_ERROR")
            while True:
                block = os.read(descriptor, self.chunk_bytes)
                if not block:
                    break
                digest.update(block)
            observed = os.lstat(str(path))
            if not _same_lstat(expected, observed):
                raise AutoRuntimeError("STAT_ERROR")
        except PermissionError as exc:
            raise AutoRuntimeError("PERMISSION_ERROR") from exc
        except AutoRuntimeError:
            raise
        except OSError as exc:
            raise AutoRuntimeError("READ_ERROR") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
        return digest.hexdigest()

    def _aggregate_excluded(
        self,
        path: Path,
        first: os.stat_result,
    ) -> Tuple[int, int, int]:
        nodes = 1
        files = 1 if stat.S_ISREG(first.st_mode) else 0
        bytes_count = first.st_size if stat.S_ISREG(first.st_mode) else 0
        if not stat.S_ISDIR(first.st_mode):
            return nodes, files, bytes_count
        descriptor = None
        try:
            descriptor = os.open(
                str(path),
                os.O_RDONLY | getattr(os, "O_DIRECTORY", 0) | getattr(os, "O_NOFOLLOW", 0),
            )
            if not _same_lstat(first, os.fstat(descriptor)):
                raise AutoRuntimeError("STAT_ERROR")
            with os.scandir(descriptor) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.encode("utf-8"))
            for entry in entries:
                try:
                    info = entry.stat(follow_symlinks=False)
                except PermissionError as exc:
                    raise AutoRuntimeError("PERMISSION_ERROR") from exc
                except OSError as exc:
                    raise AutoRuntimeError("STAT_ERROR") from exc
                child_nodes, child_files, child_bytes = self._aggregate_excluded(
                    path / entry.name, info
                )
                nodes += child_nodes
                files += child_files
                bytes_count += child_bytes
            if not _same_lstat(first, os.lstat(str(path))):
                raise AutoRuntimeError("STAT_ERROR")
        except AutoRuntimeError:
            raise
        except PermissionError as exc:
            raise AutoRuntimeError("PERMISSION_ERROR") from exc
        except (OSError, UnicodeError) as exc:
            raise AutoRuntimeError("STAT_ERROR") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
        return nodes, files, bytes_count

    def _resolve_alias(self, root: Path, alias: Path, visited: Optional[set] = None) -> Tuple[Path, bool]:
        chain = set() if visited is None else set(visited)
        candidate = Path(os.path.normpath(str(alias)))
        while True:
            if not _within(root, candidate):
                raise AutoRuntimeError("SYMLINK_UNSAFE")
            try:
                parts = candidate.relative_to(root).parts
            except ValueError as exc:
                raise AutoRuntimeError("SYMLINK_UNSAFE") from exc
            current = root
            restarted = False
            final_info = None
            for index, part in enumerate(parts):
                current = current / part
                try:
                    before = os.lstat(str(current))
                except OSError as exc:
                    raise AutoRuntimeError("SYMLINK_UNSAFE") from exc
                if stat.S_ISLNK(before.st_mode):
                    key = str(current)
                    if key in chain:
                        raise AutoRuntimeError("SYMLINK_UNSAFE")
                    chain.add(key)
                    try:
                        raw = os.readlink(str(current))
                        after = os.lstat(str(current))
                    except OSError as exc:
                        raise AutoRuntimeError("SYMLINK_UNSAFE") from exc
                    if not _same_lstat(before, after) or os.path.isabs(raw):
                        raise AutoRuntimeError("SYMLINK_UNSAFE")
                    remaining = parts[index + 1 :]
                    candidate = Path(
                        os.path.normpath(str(current.parent.joinpath(raw, *remaining)))
                    )
                    restarted = True
                    break
                if index < len(parts) - 1 and not stat.S_ISDIR(before.st_mode):
                    raise AutoRuntimeError("SYMLINK_UNSAFE")
                final_info = before
            if restarted:
                continue
            if final_info is not None and stat.S_ISREG(final_info.st_mode):
                return candidate, False
            if final_info is not None and stat.S_ISDIR(final_info.st_mode):
                return candidate, True
            raise AutoRuntimeError("SYMLINK_UNSAFE")

    def scan(self, root: Path, source_class: str, source_root_ref: str) -> SourceScanReport:
        if source_class not in {"CODEX", "CODEX_SYSTEM", "CLAUDE", "AGENTS"}:
            raise AutoRuntimeError("SOURCE_CLASS_UNKNOWN")
        if not re.fullmatch(r"[a-z][a-z0-9-]{2,63}", source_root_ref):
            raise AutoRuntimeError("SOURCE_ROOT_REF_INVALID")
        try:
            root_lstat = os.lstat(str(root))
        except FileNotFoundError as exc:
            raise AutoRuntimeError("SOURCE_ROOT_MISSING") from exc
        except OSError as exc:
            raise AutoRuntimeError("SOURCE_ROOT_STAT_FAILED") from exc
        if stat.S_ISLNK(root_lstat.st_mode) or not stat.S_ISDIR(root_lstat.st_mode):
            raise AutoRuntimeError("SOURCE_ROOT_NOT_REAL_DIRECTORY")
        root_real = root.resolve(strict=True)

        files: List[FileEvidence] = []
        pending_aliases: List[_PendingAlias] = []
        exclusions: Dict[str, List[int]] = collections.defaultdict(lambda: [0, 0, 0])
        errors: Dict[str, int] = collections.Counter()

        def record_error(code: str) -> None:
            if code not in ERROR_CODES:
                code = "READ_ERROR"
            errors[code] += 1

        def walk(
            directory: Path,
            relative_dir: PurePosixPath,
            expected_directory: os.stat_result,
        ) -> None:
            descriptor = None
            try:
                descriptor = os.open(
                    str(directory),
                    os.O_RDONLY
                    | getattr(os, "O_DIRECTORY", 0)
                    | getattr(os, "O_NOFOLLOW", 0),
                )
                if not _same_lstat(expected_directory, os.fstat(descriptor)):
                    record_error("STAT_ERROR")
                    return
                with os.scandir(descriptor) as iterator:
                    entries = sorted(iterator, key=lambda item: item.name.encode("utf-8"))
                observed_entries = []
                for entry in entries:
                    try:
                        info = entry.stat(follow_symlinks=False)
                    except PermissionError:
                        record_error("PERMISSION_ERROR")
                        continue
                    except OSError:
                        record_error("STAT_ERROR")
                        continue
                    observed_entries.append((entry.name, info))
            except PermissionError:
                record_error("PERMISSION_ERROR")
                return
            except (OSError, UnicodeError):
                record_error("READ_ERROR")
                return
            finally:
                if descriptor is not None:
                    os.close(descriptor)
            for entry_name, info in observed_entries:
                relative = relative_dir / entry_name if relative_dir.parts else PurePosixPath(entry_name)
                relative_text = relative.as_posix()
                if not _safe_text(relative_text):
                    record_error("INVALID_PATH_ENCODING")
                    continue
                is_dir = stat.S_ISDIR(info.st_mode)
                reason = self._exclusion_reason(source_class, relative, is_dir)
                path = directory / entry_name
                if reason is not None:
                    try:
                        aggregate = self._aggregate_excluded(path, info)
                    except AutoRuntimeError as exc:
                        record_error(exc.code)
                        continue
                    for index, value in enumerate(aggregate):
                        exclusions[reason][index] += value
                    continue
                if stat.S_ISDIR(info.st_mode):
                    walk(path, relative, info)
                elif stat.S_ISREG(info.st_mode):
                    try:
                        digest = self._read_regular(path, info)
                    except AutoRuntimeError as exc:
                        record_error(exc.code)
                        continue
                    files.append(FileEvidence(relative_text, info.st_size, digest))
                elif stat.S_ISLNK(info.st_mode):
                    try:
                        if not _same_lstat(info, os.lstat(str(path))):
                            raise AutoRuntimeError("SYMLINK_UNSAFE")
                        target, target_is_directory = self._resolve_alias(root_real, path)
                        target_ref = target.relative_to(root_real).as_posix()
                    except (AutoRuntimeError, ValueError):
                        record_error("SYMLINK_UNSAFE")
                        continue
                    pending_aliases.append(
                        _PendingAlias(relative_text, target_ref, target, target_is_directory)
                    )
                else:
                    record_error("SPECIAL_FILE")
            try:
                if not _same_lstat(expected_directory, os.lstat(str(directory))):
                    record_error("STAT_ERROR")
            except OSError:
                record_error("STAT_ERROR")

        walk(root_real, PurePosixPath(), root_lstat)
        ordered_files = tuple(sorted(files, key=lambda item: item.relative_path.encode("utf-8")))
        file_by_path = {item.relative_path: item for item in ordered_files}
        aliases: List[AliasEvidence] = []
        for pending in sorted(pending_aliases, key=lambda item: item.alias_path.encode("utf-8")):
            if pending.target_is_directory:
                prefix = pending.target_ref.rstrip("/") + "/"
                target_files = [item for item in ordered_files if item.relative_path.startswith(prefix)]
                content_material = {
                    "domain": "SKILLOPS_ALIAS_DIRECTORY_CONTENT_V1",
                    "target_ref": pending.target_ref,
                    "files": [
                        {
                            "relative_path": item.relative_path[len(prefix) :],
                            "byte_count": item.byte_count,
                            "content_digest": item.content_digest,
                        }
                        for item in target_files
                    ],
                }
                content_digest = sha256_bytes(canonicalize_object(content_material))
                target_type = "DIRECTORY"
            else:
                target_file = file_by_path.get(pending.target_ref)
                if target_file is None:
                    errors["SYMLINK_UNSAFE"] += 1
                    continue
                content_digest = target_file.content_digest
                target_type = "REGULAR_FILE"
            metadata_digest = sha256_bytes(
                canonicalize_object(
                    {
                        "alias_path": pending.alias_path,
                        "normalized_target_ref": pending.target_ref,
                        "target_type": target_type,
                    }
                )
            )
            aliases.append(
                AliasEvidence(
                    pending.alias_path,
                    pending.target_ref,
                    metadata_digest,
                    content_digest,
                )
            )

        ordered_aliases = tuple(aliases)
        exclusion_rows = tuple(
            ExclusionEvidence(reason, values[0], values[1], values[2])
            for reason, values in sorted(exclusions.items())
        )
        error_rows = tuple(ErrorEvidence(code, count) for code, count in sorted(errors.items()))
        tree_material = {
            "domain": "SKILLOPS_SOURCE_TREE_V1",
            "source_class": source_class,
            "source_material_policy_digest": self.policy_digest,
            "files": [
                {
                    "relative_path": item.relative_path,
                    "byte_count": item.byte_count,
                    "content_digest": item.content_digest,
                }
                for item in ordered_files
            ],
            "aliases": [
                {
                    "alias_path": item.alias_path,
                    "normalized_target_ref": item.normalized_target_ref,
                    "metadata_digest": item.metadata_digest,
                    "content_digest": item.content_digest,
                }
                for item in ordered_aliases
            ],
        }
        tree_digest = sha256_bytes(canonicalize_object(tree_material))
        snapshot_material = {
            "tree_digest": tree_digest,
            "exclusions": [item.__dict__ for item in exclusion_rows],
            "errors": [item.__dict__ for item in error_rows],
        }
        included_bytes = sum(item.byte_count for item in ordered_files)
        return SourceScanReport(
            source_class=source_class,
            source_root_ref=source_root_ref,
            completeness_status=(
                "COMPLETE_AFTER_POLICY_EXCLUSIONS" if not error_rows else "INCOMPLETE"
            ),
            included_files=ordered_files,
            included_file_count=len(ordered_files),
            included_bytes=included_bytes,
            included_tree_digest=tree_digest,
            exclusions=exclusion_rows,
            excluded_node_count=sum(item.node_count for item in exclusion_rows),
            excluded_file_count=sum(item.file_count for item in exclusion_rows),
            excluded_bytes=sum(item.byte_count for item in exclusion_rows),
            aliases=ordered_aliases,
            oversize_blocked_count=errors.get("OVERSIZE_NON_POLICY", 0),
            errors=error_rows,
            source_snapshot_digest=sha256_bytes(canonicalize_object(snapshot_material)),
        )


def assert_source_unchanged(before: SourceScanReport, after: SourceScanReport) -> None:
    if before.source_snapshot_digest != after.source_snapshot_digest:
        raise AutoRuntimeError("SOURCE_MUTATED_DURING_RUN")


class SourceInventoryAdapter:
    """Project a deterministic scan into the frozen public inventory contract."""

    adapter_id = "skill-source-inventory"
    adapter_version = "1.0.0"
    adapter_scope = "all-skill-sources"

    def __init__(
        self,
        scanner: SourceScanner,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
    ) -> None:
        self.scanner = scanner
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock
        self.adapter_schema_digest = sha256_bytes(
            canonicalize_object(
                {
                    "adapter_id": self.adapter_id,
                    "adapter_version": self.adapter_version,
                    "projection": "SOURCE_INVENTORY_V1",
                    "path_disclosure": "ROOT_REF_ONLY",
                    "symlink": "LSTAT_FIRST_SAME_ROOT_ALIAS",
                }
            )
        )

    def observe(
        self,
        root: Path,
        source_class: str,
        source_root_ref: str,
        *,
        entropy: Optional[bytes] = None,
    ) -> SourceInventoryObservation:
        started = self.clock.now()
        report = self.scanner.scan(root, source_class, source_root_ref)
        finished = self.clock.now()
        inventory = canonical_with_digest(
            {
                "schema_version": SCHEMA_PREFIX + "source-inventory:v1",
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "inventory_uid": new_uid("sinv", started, entropy),
                "source_class": source_class,
                "source_root_ref": source_root_ref,
                "observed_started_at": format_utc(started),
                "observed_finished_at": format_utc(finished),
                "adapter_id": self.adapter_id,
                "adapter_version": self.adapter_version,
                "adapter_schema_digest": self.adapter_schema_digest,
                "source_material_policy_id": SOURCE_POLICY_ID,
                "source_material_policy_digest": self.scanner.policy_digest,
                "completeness_status": report.completeness_status,
                "included_file_count": report.included_file_count,
                "included_bytes": report.included_bytes,
                "included_tree_digest": report.included_tree_digest,
                "excluded_node_count": report.excluded_node_count,
                "excluded_file_count": report.excluded_file_count,
                "excluded_bytes": report.excluded_bytes,
                "exclusions": [
                    {
                        "reason_code": item.reason_code,
                        "node_count": item.node_count,
                        "file_count": item.file_count,
                        "byte_count": item.byte_count,
                    }
                    for item in report.exclusions
                ],
                "symlink_alias_count": len(report.aliases),
                "symlink_aliases": [
                    {
                        "alias_path": item.alias_path,
                        "normalized_target_ref": item.normalized_target_ref,
                        "metadata_digest": item.metadata_digest,
                        "content_digest": item.content_digest,
                    }
                    for item in report.aliases
                ],
                "oversize_blocked_count": report.oversize_blocked_count,
                "scan_error_counts": [
                    {"reason_code": item.reason_code, "count": item.count}
                    for item in report.errors
                ],
                "inventory_digest": "0" * 64,
            },
            "inventory_digest",
        )
        validate_auto_instance(
            self.contract,
            inventory,
            SCHEMA_PREFIX + "source-inventory:v1",
            expected_bundle_digest=self.bundle_digest,
        )
        coverage = canonical_with_digest(
            {
                "schema_version": SCHEMA_PREFIX + "source-coverage-receipt:v1",
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "receipt_uid": new_uid("cov", finished, entropy),
                "coverage_subject": "SKILL_SOURCE",
                "coverage_state": (
                    "COVERED"
                    if report.completeness_status == "COMPLETE_AFTER_POLICY_EXCLUSIONS"
                    else "UNKNOWN"
                ),
                "adapter_scope": self.adapter_scope,
                "adapter_id": self.adapter_id,
                "adapter_version": self.adapter_version,
                "adapter_schema_digest": self.adapter_schema_digest,
                "observation_window_started_at": format_utc(started),
                "observation_window_finished_at": format_utc(finished),
                "heartbeat_at": format_utc(finished),
                "reason_codes": (
                    []
                    if report.completeness_status == "COMPLETE_AFTER_POLICY_EXCLUSIONS"
                    else ["INVENTORY_INCOMPLETE"]
                ),
                "source_class": source_class,
                "inventory_uid": inventory["inventory_uid"],
                "inventory_digest": inventory["inventory_digest"],
                "inventory_completeness_status": report.completeness_status,
                "source_material_policy_id": SOURCE_POLICY_ID,
                "source_material_policy_digest": self.scanner.policy_digest,
                "receipt_digest": "0" * 64,
            },
            "receipt_digest",
        )
        validate_auto_instance(
            self.contract,
            coverage,
            SCHEMA_PREFIX + "source-coverage-receipt:v1",
            expected_bundle_digest=self.bundle_digest,
        )
        return SourceInventoryObservation(report, inventory, coverage)
