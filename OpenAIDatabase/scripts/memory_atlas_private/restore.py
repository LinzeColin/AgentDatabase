from __future__ import annotations

import json
import tempfile
from pathlib import Path
from typing import Any

from .hashing import sha256_file
from .object_store import ObjectStore
from .private_db import PrivateDatabase


class RestoreError(RuntimeError):
    pass


def _safe_destination(root: Path, relative: str) -> Path:
    if not relative or any(part in {"", ".", ".."} for part in relative.replace("\\", "/").split("/")):
        raise RestoreError(f"恢复路径不安全：{relative}")
    target = (root / relative).resolve()
    target.relative_to(root.resolve())
    return target


def isolated_restore(
    *,
    manifest_path: str,
    destination: Path,
    object_store: ObjectStore,
    private_db: PrivateDatabase,
) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=True)
    if any(destination.iterdir()):
        raise RestoreError("隔离恢复目录必须为空")
    manifest = private_db.get_json(manifest_path)
    restored: list[dict[str, Any]] = []
    for index, row in enumerate(manifest.get("objects", [])):
        if not isinstance(row, dict):
            continue
        key = str(row.get("object_key", ""))
        digest = str(row.get("sha256", ""))
        if not key or not digest:
            raise RestoreError("manifest object 缺少 key 或 sha256")
        target = _safe_destination(destination, f"objects/{index:06d}-{digest}")
        object_store.get_file(key, target)
        observed = sha256_file(target)
        if observed != digest:
            raise RestoreError(f"恢复对象哈希不一致：{key}")
        restored.append({"object_key": key, "sha256": digest, "path": str(target)})
    receipt = {
        "schema_version": "memory_atlas.restore_receipt.v1",
        "manifest_path": manifest_path,
        "restored_objects": len(restored),
        "all_hashes_match": True,
        "destination": str(destination),
        "objects": restored,
    }
    (destination / "RESTORE_RECEIPT.json").write_text(
        json.dumps(receipt, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return receipt
