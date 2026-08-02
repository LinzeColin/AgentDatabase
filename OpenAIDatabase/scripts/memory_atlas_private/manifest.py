from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .hashing import sha256_bytes
from .models import RunManifest


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_fact_paths(run_id: str, started_at: str) -> dict[str, str]:
    day = started_at[:10].replace("-", "/")
    return {
        "run": f"memory-atlas/runs/{day}/{run_id}/manifest.json",
        "latest": "memory-atlas/runs/latest.json",
        "catalog": f"memory-atlas/catalog/{day}/{run_id}.json",
        "analytics": "memory-atlas/analytics/latest.json",
        "failure_compound": "memory-atlas/failure-compound/latest.json",
        "runtime": "memory-atlas/runtime/latest.json",
    }


def manifest_digest(manifest: RunManifest) -> str:
    payload = json.dumps(manifest.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return sha256_bytes(payload)


def write_json_atomic(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n"
    temporary = path.with_suffix(path.suffix + ".partial")
    temporary.write_bytes(payload)
    temporary.replace(path)
