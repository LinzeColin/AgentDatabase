from __future__ import annotations

import json
import tempfile
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import RuntimeConfig
from .hashing import sha256_file
from .object_store import LocalObjectStore, ObjectStoreError, R2ObjectStore
from .private_db import PrivateDatabase


KNOWN_FACTS = (
    "memory-atlas/runs/latest.json",
    "memory-atlas/analytics/latest.json",
    "memory-atlas/failure-compound/latest.json",
    "memory-atlas/runtime/latest.json",
)


def _safe_backup_key(value: str) -> str:
    clean = value.strip("/")
    if not clean or any(part in {"", ".", ".."} for part in clean.split("/")):
        raise ValueError("backup key 不安全")
    return clean


def _put_backup(store: object, config: RuntimeConfig, key: str, source: Path, digest: str) -> dict[str, Any]:
    clean = _safe_backup_key(key)
    if isinstance(store, LocalObjectStore):
        receipt = store.put_file(f"backups/private-database/{clean}", source, digest)
        return asdict(receipt)
    if not isinstance(store, R2ObjectStore):
        raise ObjectStoreError("不支持的 backup object store")
    full_key = config.r2_backup_prefix + clean
    with source.open("rb") as stream:
        store.client.upload_fileobj(
            stream,
            config.r2_bucket,
            full_key,
            ExtraArgs={"Metadata": {"sha256": digest}, "ContentType": "application/json"},
            Config=store._transfer_config,
        )
    observed = store._download_and_hash(full_key)
    if observed != digest:
        raise ObjectStoreError("Private-Database fact bundle R2 读回哈希不一致")
    return {
        "sha256": digest,
        "object_key": full_key,
        "size_bytes": source.stat().st_size,
        "operation": "created_or_replaced",
        "readback_sha256": observed,
        "readback_verified": True,
        "provider_version": "cloudflare-r2-s3-v1",
    }


def backup_private_facts(
    config: RuntimeConfig,
    private_db: PrivateDatabase,
    object_store: object,
    *,
    generated_at: str,
) -> dict[str, Any]:
    facts: dict[str, dict[str, object]] = {}
    missing: list[str] = []
    for relpath in KNOWN_FACTS:
        try:
            facts[relpath] = private_db.get_json(relpath)
        except Exception:
            missing.append(relpath)
    latest = facts.get("memory-atlas/runs/latest.json")
    if not latest or latest.get("state") != "SUCCEEDED":
        return {
            "schema_version": "memory_atlas.private_fact_backup.v1",
            "state": "WAITING_SOURCE",
            "generated_at": generated_at,
            "missing": missing,
        }
    manifest_path = str(latest.get("manifest_path", ""))
    if not manifest_path.startswith("memory-atlas/runs/"):
        raise ValueError("latest run 缺少安全 manifest_path")
    facts[manifest_path] = private_db.get_json(manifest_path)
    bundle = {
        "schema_version": "memory_atlas.private_fact_bundle.v1",
        "generated_at": generated_at,
        "source_run_id": latest.get("run_id"),
        "facts": facts,
        "missing_optional": missing,
    }
    with tempfile.NamedTemporaryFile(prefix="memory-atlas-facts-", suffix=".json", delete=False) as handle:
        path = Path(handle.name)
        handle.write(json.dumps(bundle, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")
    try:
        digest = sha256_file(path)
        day = generated_at[:10].replace("-", "")
        run_id = str(latest.get("run_id", "unknown"))
        key = f"{day}/{run_id}/private-facts-{digest[:16]}.json"
        receipt = _put_backup(object_store, config, key, path, digest)
    finally:
        path.unlink(missing_ok=True)
    result = {
        "schema_version": "memory_atlas.private_fact_backup.v1",
        "state": "PASS",
        "generated_at": generated_at,
        "source_run_id": latest.get("run_id"),
        "fact_count": len(facts),
        "missing_optional": missing,
        "receipt": receipt,
    }
    private_db.put_json("memory-atlas/backups/latest.json", result, "memory-atlas: record private fact backup")
    return result
