"""Private full inventory and public aggregate-only inventory views."""

from __future__ import annotations

import fnmatch
import hashlib
import stat
import unicodedata
from collections import Counter
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .paths import PathSafetyError, resolve_input_file


class InventoryError(RuntimeError):
    """Fail-closed inventory error that never exposes a raw relative path."""

    def __init__(self, code: str, message: str, *, source_id: Optional[str] = None) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.source_id = source_id

    def as_dict(self) -> Dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.source_id:
            result["source_ref"] = self.source_id
        return result


@dataclass(frozen=True)
class FileIdentity:
    device: int
    inode: int
    size_bytes: int
    mtime_ns: int
    link_count: int


@dataclass(frozen=True)
class InventoryEntry:
    """Private-only file inventory record; relative_path must never enter public output."""

    source_id: str
    relative_path: str
    entry_kind: str
    status: str
    identity: FileIdentity
    sha256: Optional[str] = None
    error_code: Optional[str] = None

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "source_id": self.source_id,
            "relative_path": self.relative_path,
            "entry_kind": self.entry_kind,
            "status": self.status,
            "identity": {
                "device": self.identity.device,
                "inode": self.identity.inode,
                "size_bytes": self.identity.size_bytes,
                "mtime_ns": self.identity.mtime_ns,
                "link_count": self.identity.link_count,
            },
            "sha256": self.sha256,
            "error_code": self.error_code,
        }


@dataclass(frozen=True)
class VerifiedSource:
    source_id: str
    relative_path: str
    sha256: str
    identity: FileIdentity


def _identity(metadata: Any) -> FileIdentity:
    return FileIdentity(
        device=int(metadata.st_dev),
        inode=int(metadata.st_ino),
        size_bytes=int(metadata.st_size),
        mtime_ns=int(metadata.st_mtime_ns),
        link_count=int(metadata.st_nlink),
    )


def _normalized_relative_path(relative_path: str) -> str:
    return unicodedata.normalize("NFC", relative_path)


def source_id_for_relative_path(relative_path: str) -> str:
    normalized = _normalized_relative_path(relative_path)
    digest = hashlib.sha256(("kmfa-source-id-v1\0" + normalized).encode("utf-8")).hexdigest()
    return "src_" + digest[:32]


def _resolve_inventory_root(root: Path) -> Path:
    value = Path(root)
    if value.is_symlink():
        raise InventoryError("ROOT_SYMLINK", "inventory root must not be a symbolic link")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise InventoryError("ROOT_UNAVAILABLE", "inventory root does not exist") from exc
    if not resolved.is_dir():
        raise InventoryError("ROOT_NOT_DIRECTORY", "inventory root must be a directory")
    return resolved


def scan_inventory_metadata(root: Path) -> Tuple[InventoryEntry, ...]:
    """Enumerate metadata only; this function never opens a source file body."""

    resolved_root = _resolve_inventory_root(root)
    entries = []
    seen_ids: Dict[str, str] = {}
    try:
        paths = sorted(resolved_root.rglob("*"), key=lambda item: item.relative_to(resolved_root).as_posix())
    except OSError as exc:
        raise InventoryError("INVENTORY_ENUMERATION_FAILED", "source metadata cannot be enumerated") from exc
    for path in paths:
        relative = path.relative_to(resolved_root).as_posix()
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise InventoryError("INVENTORY_LSTAT_FAILED", "source metadata cannot be inspected") from exc
        mode = metadata.st_mode
        if stat.S_ISDIR(mode):
            continue
        source_id = source_id_for_relative_path(relative)
        previous = seen_ids.get(source_id)
        if previous is not None and previous != relative:
            raise InventoryError("SOURCE_ID_COLLISION", "normalized source identifiers collide", source_id=source_id)
        seen_ids[source_id] = relative
        if stat.S_ISLNK(mode):
            kind, status, error_code = "SYMLINK", "UNSAFE", "INPUT_SYMLINK"
        elif stat.S_ISREG(mode) and metadata.st_nlink != 1:
            kind, status, error_code = "REGULAR_FILE", "UNSAFE", "INPUT_HARDLINK"
        elif stat.S_ISREG(mode):
            kind, status, error_code = "REGULAR_FILE", "SAFE_METADATA", None
        else:
            kind, status, error_code = "SPECIAL", "UNSAFE", "INPUT_NOT_REGULAR"
        entries.append(
            InventoryEntry(
                source_id=source_id,
                relative_path=relative,
                entry_kind=kind,
                status=status,
                identity=_identity(metadata),
                error_code=error_code,
            )
        )
    return tuple(entries)


def _matches(relative_path: str, pattern: str) -> bool:
    if fnmatch.fnmatchcase(relative_path, pattern):
        return True
    if pattern.startswith("**/"):
        return fnmatch.fnmatchcase(relative_path, pattern[3:])
    return False


def match_inventory_entries(
    entries: Sequence[InventoryEntry],
    patterns: Sequence[str],
) -> Tuple[InventoryEntry, ...]:
    matched = {
        entry.source_id: entry
        for entry in entries
        if any(_matches(entry.relative_path, pattern) for pattern in patterns)
    }
    return tuple(sorted(matched.values(), key=lambda item: item.source_id))


def verify_source_file(root: Path, entry: InventoryEntry) -> VerifiedSource:
    """Re-open and fully hash a selected source; cached inventory digests are ignored."""

    if entry.status not in {"SAFE_METADATA", "VERIFIED"}:
        raise InventoryError(
            entry.error_code or "UNSAFE_SOURCE",
            "selected source failed the metadata safety gate",
            source_id=entry.source_id,
        )
    try:
        path = resolve_input_file(root, entry.relative_path)
    except PathSafetyError as exc:
        raise InventoryError(exc.code, exc.message, source_id=entry.source_id) from exc
    try:
        before = _identity(path.stat())
        digest = hashlib.sha256()
        with path.open("rb") as handle:
            for block in iter(lambda: handle.read(1024 * 1024), b""):
                digest.update(block)
        after = _identity(path.stat())
    except OSError as exc:
        raise InventoryError("SOURCE_UNREADABLE", "selected source cannot be fully hashed", source_id=entry.source_id) from exc
    if before != after:
        raise InventoryError(
            "SOURCE_CHANGED_DURING_DIGEST",
            "selected source identity changed during full digest verification",
            source_id=entry.source_id,
        )
    if source_id_for_relative_path(entry.relative_path) != entry.source_id:
        raise InventoryError("SOURCE_ID_MISMATCH", "source identifier no longer matches its private locator")
    return VerifiedSource(
        source_id=entry.source_id,
        relative_path=entry.relative_path,
        sha256=digest.hexdigest(),
        identity=after,
    )


def build_private_full_inventory(root: Path) -> Tuple[InventoryEntry, ...]:
    """Hash every safe regular source for a private-only inventory payload."""

    entries = scan_inventory_metadata(root)
    completed = []
    for entry in entries:
        if entry.status != "SAFE_METADATA":
            completed.append(entry)
            continue
        try:
            verified = verify_source_file(root, entry)
        except InventoryError as exc:
            completed.append(replace(entry, status="UNSAFE", error_code=exc.code, sha256=None))
            continue
        completed.append(
            replace(
                entry,
                status="VERIFIED",
                identity=verified.identity,
                sha256=verified.sha256,
                error_code=None,
            )
        )
    return tuple(completed)


def private_inventory_payload(entries: Iterable[InventoryEntry]) -> Dict[str, Any]:
    ordered = sorted(entries, key=lambda item: item.source_id)
    return {
        "schema_version": "kmfa.project_cost.private_inventory.v1",
        "entries": [entry.as_private_dict() for entry in ordered],
    }


def public_inventory_summary(entries: Iterable[InventoryEntry]) -> Dict[str, Any]:
    """Return aggregate status/counts only: no path, name, source ID, hash, or value."""

    ordered = tuple(entries)
    statuses = Counter(entry.status for entry in ordered)
    return {
        "schema_version": "kmfa.project_cost.public_inventory_summary.v1",
        "entry_count": len(ordered),
        "verified_file_count": statuses.get("VERIFIED", 0),
        "metadata_only_file_count": statuses.get("SAFE_METADATA", 0),
        "unsafe_entry_count": statuses.get("UNSAFE", 0),
        "status_counts": {key: statuses[key] for key in sorted(statuses)},
        "contains_private_locators": False,
        "contains_source_hashes": False,
        "contains_business_values": False,
    }
