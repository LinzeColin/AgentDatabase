from __future__ import annotations

import json
import sqlite3
import subprocess
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .hashing import sha256_bytes, stable_id


class PrivateDatabaseError(RuntimeError):
    pass


class PrivateDatabase(Protocol):
    def put_json(self, relpath: str, value: dict[str, object], message: str) -> str: ...
    def get_json(self, relpath: str) -> dict[str, object]: ...
    def verify(self) -> dict[str, object]: ...


def _safe_relpath(relpath: str) -> str:
    clean = relpath.strip("/")
    if not clean or any(part in {"", ".", ".."} for part in clean.split("/")):
        raise PrivateDatabaseError(f"Private-Database 路径不安全：{relpath}")
    if not clean.startswith("memory-atlas/"):
        raise PrivateDatabaseError("Memory Atlas 只能写 Private-AgentDatabase/memory-atlas/ 范围")
    return clean


@dataclass
class LocalPrivateDatabase:
    root: Path

    def _target(self, relpath: str) -> Path:
        target = (self.root / _safe_relpath(relpath)).resolve()
        target.relative_to(self.root.resolve())
        return target

    def put_json(self, relpath: str, value: dict[str, object], message: str) -> str:
        target = self._target(relpath)
        target.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        if target.exists() and target.read_bytes() == payload:
            return relpath
        temporary = target.with_suffix(target.suffix + ".partial")
        temporary.write_bytes(payload)
        temporary.replace(target)
        return relpath

    def get_json(self, relpath: str) -> dict[str, object]:
        target = self._target(relpath)
        if not target.is_file():
            raise PrivateDatabaseError(f"事实不存在：{relpath}")
        value = json.loads(target.read_text(encoding="utf-8"))
        if not isinstance(value, dict):
            raise PrivateDatabaseError(f"事实不是 JSON object：{relpath}")
        return value

    def verify(self) -> dict[str, object]:
        files = sorted(path for path in self.root.rglob("*") if path.is_file())
        return {"state": "PASS", "file_count": len(files), "backend": "local-test"}


@dataclass
class GhPrivateDatabase:
    client_path: Path
    area: str = "Private-AgentDatabase"

    def _run(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        command = ["python3", "-B", str(self.client_path), *args]
        completed = subprocess.run(command, text=True, capture_output=True, timeout=180)
        if completed.returncode != 0:
            raise PrivateDatabaseError(
                f"Private-Database client 失败：{' '.join(args[:3])}: {completed.stderr.strip() or completed.stdout.strip()}"
            )
        return completed

    def put_json(self, relpath: str, value: dict[str, object], message: str) -> str:
        clean = _safe_relpath(relpath)
        payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
        with tempfile.NamedTemporaryFile(prefix="memory-atlas-fact-", suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
            handle.write(payload)
        try:
            self._run(["put", self.area, clean, str(temporary)])
        finally:
            temporary.unlink(missing_ok=True)
        last_error = ""
        for attempt in range(6):
            try:
                observed = self.get_json(clean)
            except Exception as exc:
                last_error = str(exc)
            else:
                if observed == value:
                    return clean
                last_error = "JSON 内容不一致"
            if attempt < 5:
                time.sleep(min(0.5 * (2 ** attempt), 2.0))
        raise PrivateDatabaseError(f"Private-Database 提交后读回不一致：{clean}: {last_error[:500]}")

    def get_json(self, relpath: str) -> dict[str, object]:
        clean = _safe_relpath(relpath)
        with tempfile.NamedTemporaryFile(prefix="memory-atlas-get-", suffix=".json", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            self._run(["get", self.area, clean, str(temporary)])
            value = json.loads(temporary.read_text(encoding="utf-8"))
        finally:
            temporary.unlink(missing_ok=True)
        if not isinstance(value, dict):
            raise PrivateDatabaseError(f"远端事实不是 JSON object：{clean}")
        return value

    def verify(self) -> dict[str, object]:
        completed = self._run(["verify", self.area])
        text = completed.stdout.strip()
        return {"state": "PASS", "backend": "github-rest", "client_output": text[-2000:]}


class FactOutbox:
    """Rebuildable runtime outbox. Completed facts remain authoritative remotely."""

    def __init__(self, sqlite_path: Path):
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = sqlite_path
        with self._connect() as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS fact_outbox (
                    outbox_id TEXT PRIMARY KEY,
                    relpath TEXT NOT NULL,
                    payload_json TEXT NOT NULL,
                    payload_sha256 TEXT NOT NULL,
                    message TEXT NOT NULL,
                    state TEXT NOT NULL DEFAULT 'PENDING',
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL,
                    completed_at TEXT
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_fact_outbox_path_hash
                    ON fact_outbox(relpath, payload_sha256);
                """
            )

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def enqueue(self, relpath: str, payload: dict[str, object], message: str, now: str) -> str:
        clean = _safe_relpath(relpath)
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest = sha256_bytes(encoded.encode("utf-8"))
        outbox_id = stable_id(clean, digest, prefix="outbox")
        with self._connect() as db:
            db.execute(
                """
                UPDATE fact_outbox
                SET state='SUPERSEDED', completed_at=?, last_error='superseded by newer payload for same path'
                WHERE relpath=? AND payload_sha256!=? AND state IN ('PENDING', 'RETRY')
                """,
                (now, clean, digest),
            )
            db.execute(
                """
                INSERT OR IGNORE INTO fact_outbox
                (outbox_id, relpath, payload_json, payload_sha256, message, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (outbox_id, clean, encoded, digest, message, now),
            )
            db.commit()
        return outbox_id

    def flush(self, backend: PrivateDatabase, now: str, limit: int = 100) -> dict[str, int]:
        completed = failed = 0
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM fact_outbox WHERE state IN ('PENDING', 'RETRY') ORDER BY created_at LIMIT ?",
                (limit,),
            ).fetchall()
        for row in rows:
            try:
                backend.put_json(row["relpath"], json.loads(row["payload_json"]), row["message"])
            except Exception as exc:
                failed += 1
                with self._connect() as db:
                    db.execute(
                        "UPDATE fact_outbox SET attempts=attempts+1, state='RETRY', last_error=? WHERE outbox_id=?",
                        (str(exc)[:1000], row["outbox_id"]),
                    )
                    db.commit()
            else:
                completed += 1
                with self._connect() as db:
                    db.execute(
                        "UPDATE fact_outbox SET attempts=attempts+1, state='COMPLETED', completed_at=?, last_error='' WHERE outbox_id=?",
                        (now, row["outbox_id"]),
                    )
                    db.commit()
        return {"completed": completed, "failed": failed, "remaining": self.pending_count()}

    def pending_count(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COUNT(*) FROM fact_outbox WHERE state IN ('PENDING', 'RETRY')").fetchone()
            return int(row[0])
