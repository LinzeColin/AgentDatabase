#!/usr/bin/env python3
"""Resolve the active Memory Atlas frontend after the repository split.

The active product layout is::

    AgentDatabase/
      OpenAIDatabase/
      MemoryAtlas/

Older recovery fixtures may still contain ``OpenAIDatabase/apps/memory-atlas``.
Those fixtures remain supported as a fallback, but operational commands must
prefer the split top-level application whenever it is present.
"""

from __future__ import annotations

import os
from pathlib import Path


SPLIT_FRONTEND_NAME = "MemoryAtlas"
LEGACY_FRONTEND_RELATIVE = Path("apps/memory-atlas")


class MemoryAtlasPathError(RuntimeError):
    """No usable Memory Atlas frontend exists for the supplied database root."""


def is_frontend_root(path: Path) -> bool:
    """Return whether *path* has the minimum tracked frontend shape."""

    return (path / "package.json").is_file() and (path / "src").is_dir()


def frontend_candidates(database_dir: Path) -> tuple[Path, Path]:
    """Return canonical split and compatibility frontend candidates in priority order."""

    database_dir = Path(database_dir).expanduser().resolve()
    return (
        database_dir.parent / SPLIT_FRONTEND_NAME,
        database_dir / LEGACY_FRONTEND_RELATIVE,
    )


def resolve_frontend_root(database_dir: Path, *, require_exists: bool = True) -> Path:
    """Resolve the active frontend, preferring the top-level split project.

    ``require_exists=False`` is for command-plan construction only. Runtime
    readers and builders should keep the default fail-closed behavior.
    """

    canonical, legacy = frontend_candidates(database_dir)
    for candidate in (canonical, legacy):
        if is_frontend_root(candidate):
            return candidate

    if not require_exists:
        return canonical

    expected = ", ".join(path.as_posix() for path in (canonical, legacy))
    raise MemoryAtlasPathError(
        "Memory Atlas frontend is missing or incomplete; expected one of: " + expected
    )


def frontend_relative_to_database(database_dir: Path, frontend_root: Path | None = None) -> str:
    """Return a portable frontend path relative to the OpenAIDatabase root."""

    database_dir = Path(database_dir).expanduser().resolve()
    frontend_root = (frontend_root or resolve_frontend_root(database_dir)).resolve()
    return Path(os.path.relpath(frontend_root, database_dir)).as_posix()


def default_publish_dir(database_dir: Path) -> Path:
    """Return the split-aware default Vite output directory."""

    return resolve_frontend_root(database_dir) / "dist"
