from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .action_queue import ActionQueue
from .config import RuntimeConfig
from .object_store import R2ObjectStore
from .pipeline import RemoteReconcilePipeline
from .private_db import GhPrivateDatabase
from .restore import isolated_restore


def _parse_time(value: object) -> datetime | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def process_actions(config: RuntimeConfig, limit: int = 20) -> dict[str, Any]:
    queue = ActionQueue(config.runtime_dir / "action-queue.sqlite3")
    private_db = GhPrivateDatabase(config.private_db_client)
    object_store = R2ObjectStore(config)
    processed: list[dict[str, object]] = []
    for row in queue.pending(limit=limit):
        request_id = str(row["request_id"])
        action = str(row["action"])
        try:
            if action == "capture_request":
                request_fact = {
                    "schema_version": "memory_atlas.capture_request.v1",
                    "request_id": request_id,
                    "requested_at": row["requested_at"],
                    "state": "WAITING_SOURCE",
                    "message_zh": "等待 Mac/Codex 源端采集；尚未完成备份。",
                }
                private_db.put_json(
                    f"memory-atlas/actions/{request_id}.json",
                    request_fact,
                    f"memory-atlas: source capture request {request_id}",
                )
                latest = private_db.get_json("memory-atlas/runs/latest.json")
                requested_at = _parse_time(row.get("requested_at"))
                completed_at = _parse_time(latest.get("completed_at"))
                if (
                    latest.get("state") == "SUCCEEDED"
                    and requested_at is not None
                    and completed_at is not None
                    and completed_at >= requested_at
                ):
                    result = {
                        "state": "SUCCEEDED",
                        "run_id": latest.get("run_id"),
                        "completed_at": latest.get("completed_at"),
                        "message_zh": "源端采集、远端对象保存和完成态事实提交已发生在请求之后。",
                    }
                    queue.update(request_id, "SUCCEEDED", result)
                    private_db.put_json(
                        f"memory-atlas/actions/{request_id}.json",
                        {**request_fact, **result},
                        f"memory-atlas: close source capture request {request_id}",
                    )
                    processed.append({"request_id": request_id, "state": "SUCCEEDED"})
                else:
                    processed.append({"request_id": request_id, "state": "WAITING_SOURCE"})
                continue

            if action == "diagnose":
                result = {
                    "schema_version": "memory_atlas.diagnose_result.v1",
                    "r2": object_store.preflight(),
                    "private_database": private_db.verify(),
                    "reconcile": RemoteReconcilePipeline(config, object_store, private_db).run(),
                }
                state = "SUCCEEDED" if result["r2"].get("state") == "PASS" and result["private_database"].get("state") == "PASS" else "FAILED"
                queue.update(request_id, state, result)
                processed.append({"request_id": request_id, "state": state})
                continue

            if action == "restore_drill":
                latest = private_db.get_json("memory-atlas/runs/latest.json")
                manifest_path = str(latest.get("manifest_path", ""))
                if not manifest_path:
                    raise RuntimeError("最新运行缺少 manifest_path")
                destination = config.runtime_dir / "restore-drills" / request_id
                if destination.exists():
                    shutil.rmtree(destination)
                receipt = isolated_restore(manifest_path, destination, object_store, private_db)
                receipt_path = config.runtime_dir / "restore-receipts" / f"{request_id}.json"
                receipt_path.parent.mkdir(parents=True, exist_ok=True)
                receipt_path.write_text(json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
                shutil.rmtree(destination, ignore_errors=True)
                queue.update(request_id, "SUCCEEDED", receipt)
                processed.append({"request_id": request_id, "state": "SUCCEEDED"})
                continue

            queue.update(request_id, "FAILED", {"message_zh": f"未知动作：{action}"})
            processed.append({"request_id": request_id, "state": "FAILED"})
        except Exception as exc:
            queue.update(request_id, "FAILED", {"error_type": exc.__class__.__name__, "message_zh": str(exc)[:1000]})
            processed.append({"request_id": request_id, "state": "FAILED"})
    return {"schema_version": "memory_atlas.action_worker.v1", "processed": processed, "count": len(processed)}


def main() -> None:
    print(json.dumps(process_actions(RuntimeConfig.from_env()), ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
