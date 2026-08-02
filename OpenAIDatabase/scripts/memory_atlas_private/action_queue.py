from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import stable_id
from .models import ActionRequest


ALLOWED_ACTIONS = {"capture_request", "diagnose", "restore_drill"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


class ActionQueue:
    def __init__(self, sqlite_path: Path):
        sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self.path = sqlite_path
        with sqlite3.connect(self.path) as db:
            db.executescript(
                """
                PRAGMA journal_mode=WAL;
                CREATE TABLE IF NOT EXISTS action_requests (
                    request_id TEXT PRIMARY KEY,
                    action TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    idempotency_key TEXT NOT NULL UNIQUE,
                    state TEXT NOT NULL,
                    source_required INTEGER NOT NULL,
                    message_zh TEXT NOT NULL,
                    result_json TEXT,
                    updated_at TEXT NOT NULL
                );
                """
            )

    def enqueue(self, action: str, idempotency_key: str, now: str | None = None) -> ActionRequest:
        if action not in ALLOWED_ACTIONS:
            raise ValueError(f"不支持的动作：{action}")
        if not idempotency_key.strip():
            raise ValueError("idempotency_key 不能为空")
        timestamp = now or utc_now()
        request_id = stable_id(action, idempotency_key, prefix="cmd")
        source_required = action == "capture_request"
        state = "WAITING_SOURCE" if source_required else "QUEUED"
        message = "等待本机源端采集；尚未完成备份。" if source_required else "动作已进入有界运行队列。"
        with sqlite3.connect(self.path) as db:
            db.execute(
                """
                INSERT OR IGNORE INTO action_requests
                (request_id, action, requested_at, idempotency_key, state, source_required, message_zh, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (request_id, action, timestamp, idempotency_key, state, int(source_required), message, timestamp),
            )
            row = db.execute(
                "SELECT request_id, action, requested_at, idempotency_key, state, source_required, message_zh "
                "FROM action_requests WHERE idempotency_key=?",
                (idempotency_key,),
            ).fetchone()
            db.commit()
        return ActionRequest(
            request_id=str(row[0]),
            action=str(row[1]),
            requested_at=str(row[2]),
            idempotency_key=str(row[3]),
            state=str(row[4]),
            source_required=bool(row[5]),
            message_zh=str(row[6]),
        )

    def update(self, request_id: str, state: str, result: dict[str, Any], now: str | None = None) -> None:
        timestamp = now or utc_now()
        with sqlite3.connect(self.path) as db:
            changed = db.execute(
                "UPDATE action_requests SET state=?, result_json=?, updated_at=? WHERE request_id=?",
                (state, json.dumps(result, ensure_ascii=False, sort_keys=True), timestamp, request_id),
            ).rowcount
            db.commit()
        if changed != 1:
            raise KeyError(request_id)

    def status(self, request_id: str) -> dict[str, Any]:
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            row = db.execute("SELECT * FROM action_requests WHERE request_id=?", (request_id,)).fetchone()
        if row is None:
            raise KeyError(request_id)
        value = dict(row)
        if value.get("result_json"):
            value["result"] = json.loads(value.pop("result_json"))
        else:
            value.pop("result_json", None)
        value["source_required"] = bool(value["source_required"])
        return value

    def pending(self, states: tuple[str, ...] = ("QUEUED", "WAITING_SOURCE"), limit: int = 20) -> list[dict[str, Any]]:
        if not states:
            return []
        placeholders = ",".join("?" for _ in states)
        with sqlite3.connect(self.path) as db:
            db.row_factory = sqlite3.Row
            rows = db.execute(
                f"SELECT * FROM action_requests WHERE state IN ({placeholders}) ORDER BY requested_at LIMIT ?",
                (*states, limit),
            ).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            value = dict(row)
            if value.get("result_json"):
                value["result"] = json.loads(value.pop("result_json"))
            else:
                value.pop("result_json", None)
            value["source_required"] = bool(value["source_required"])
            result.append(value)
        return result
