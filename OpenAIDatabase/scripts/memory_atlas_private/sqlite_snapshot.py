from __future__ import annotations

import sqlite3
from pathlib import Path

from .hashing import sha256_file


class SQLiteSnapshotError(RuntimeError):
    pass


def create_consistent_snapshot(source: Path, destination: Path) -> tuple[str, int]:
    """Create an online-consistent SQLite snapshot using the SQLite backup API."""
    if not source.is_file():
        raise SQLiteSnapshotError(f"SQLite 源不存在：{source}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(destination.suffix + ".partial")
    temporary.unlink(missing_ok=True)
    try:
        source_uri = f"file:{source}?mode=ro"
        with sqlite3.connect(source_uri, uri=True, timeout=10) as src:
            with sqlite3.connect(temporary, timeout=10) as dst:
                src.backup(dst, pages=256, sleep=0.01)
                result = dst.execute("PRAGMA integrity_check").fetchone()
                if not result or result[0] != "ok":
                    raise SQLiteSnapshotError(f"SQLite snapshot integrity_check 失败：{result}")
        temporary.replace(destination)
    except Exception:
        temporary.unlink(missing_ok=True)
        raise
    return sha256_file(destination), destination.stat().st_size
