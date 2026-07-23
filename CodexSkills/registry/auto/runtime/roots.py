"""Realpath-aware root registry and destructive-operation guard."""

from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Tuple

from .core import AutoRuntimeError


PROTECTED_CLASSES = {"SKILL_SOURCE", "RUN_SOURCE", "LEGACY_DATA"}
MANAGED_CLASSES = {"STATE", "STAGING", "PUBLIC_QUEUE", "OUTBOX"}
TARGET_CLASS = "TARGET_WORKTREE"
MUTATION_OPERATIONS = {"WRITE", "DELETE", "MOVE", "TRUNCATE", "CHMOD"}


def _contains(root: Path, target: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(target))) == str(root)
    except ValueError:
        return False


def _existing_real(path: Path) -> Path:
    try:
        info = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError("ROOT_LSTAT_FAILED") from exc
    if stat.S_ISLNK(info.st_mode):
        raise AutoRuntimeError("ROOT_SYMLINK_FORBIDDEN")
    try:
        return path.resolve(strict=True)
    except OSError as exc:
        raise AutoRuntimeError("ROOT_REALPATH_FAILED") from exc


@dataclass(frozen=True)
class RootEntry:
    root_ref: str
    root_class: str
    path: Path


class RootRegistry:
    def __init__(self, entries: Iterable[RootEntry]) -> None:
        normalized = []
        seen_refs = set()
        for entry in entries:
            if entry.root_ref in seen_refs:
                raise AutoRuntimeError("ROOT_REF_DUPLICATE")
            if entry.root_class not in PROTECTED_CLASSES | MANAGED_CLASSES | {TARGET_CLASS}:
                raise AutoRuntimeError("ROOT_CLASS_UNKNOWN")
            real = _existing_real(entry.path)
            seen_refs.add(entry.root_ref)
            normalized.append(RootEntry(entry.root_ref, entry.root_class, real))
        self._entries: Tuple[RootEntry, ...] = tuple(
            sorted(normalized, key=lambda item: (-len(str(item.path)), item.root_ref))
        )
        self._validate_overlaps()

    @property
    def entries(self) -> Tuple[RootEntry, ...]:
        return self._entries

    def _validate_overlaps(self) -> None:
        for index, left in enumerate(self._entries):
            for right in self._entries[index + 1 :]:
                overlap = _contains(left.path, right.path) or _contains(right.path, left.path)
                if not overlap:
                    continue
                classes = {left.root_class, right.root_class}
                if classes.issubset(PROTECTED_CLASSES) or classes.issubset(MANAGED_CLASSES):
                    continue
                raise AutoRuntimeError("ROOT_CLASS_OVERLAP_FORBIDDEN")

    def classify(self, path: Path) -> RootEntry:
        resolved = path.resolve(strict=False)
        for entry in self._entries:
            if _contains(entry.path, resolved):
                return entry
        raise AutoRuntimeError("PATH_OUTSIDE_DECLARED_ROOTS")

    def assert_mutation(
        self,
        operation: str,
        path: Path,
        *,
        target_mutation_allowed: bool = False,
    ) -> RootEntry:
        if operation not in MUTATION_OPERATIONS:
            raise AutoRuntimeError("MUTATION_OPERATION_UNKNOWN")
        entry = self.classify(path)
        if entry.root_class in PROTECTED_CLASSES:
            raise AutoRuntimeError(f"PROTECTED_ROOT_MUTATION_FORBIDDEN:{entry.root_class}")
        if entry.root_class == TARGET_CLASS and not target_mutation_allowed:
            raise AutoRuntimeError("TARGET_MUTATION_REQUIRES_EXPLICIT_TRANSACTION")
        return entry


def prepare_state_root(
    requested: Path,
    *,
    repo_root: Path,
    protected_roots: Iterable[Path],
) -> Path:
    """Create an owner-only repo-external state root after bootstrap succeeds."""

    if not requested.is_absolute():
        raise AutoRuntimeError("STATE_ROOT_MUST_BE_ABSOLUTE")
    repo = repo_root.resolve(strict=True)
    real_protected = tuple(root.resolve(strict=True) for root in protected_roots)
    parent = requested.parent.resolve(strict=True)
    candidate = parent / requested.name
    if _contains(repo, candidate) or _contains(candidate, repo):
        raise AutoRuntimeError("STATE_ROOT_REPOSITORY_OVERLAP")
    for protected in real_protected:
        if _contains(protected, candidate) or _contains(candidate, protected):
            raise AutoRuntimeError("STATE_ROOT_PROTECTED_OVERLAP")
    try:
        candidate.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = os.lstat(str(candidate))
    except OSError as exc:
        raise AutoRuntimeError("STATE_ROOT_CREATE_FAILED") from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise AutoRuntimeError("STATE_ROOT_NOT_REAL_DIRECTORY")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise AutoRuntimeError("STATE_ROOT_PERMISSIONS_TOO_BROAD")
    return candidate.resolve(strict=True)
