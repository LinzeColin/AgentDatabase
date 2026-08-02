from __future__ import annotations

import json
import os
import socket
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .analytics import build_behavior_analytics, build_habit_recommendations
from .config import RuntimeConfig
from .failure_compound import FailureCompoundStore
from .hashing import sha256_file, stable_id
from .inventory import cleanup_snapshots, discover_inventory, load_source_registry
from .manifest import manifest_digest, run_fact_paths, utc_now, write_json_atomic
from .models import NormalizedEvent, RunManifest, RunState, SourceState
from .normalization import normalize_record
from .object_store import ObjectStore, R2ObjectStore
from .private_db import FactOutbox, GhPrivateDatabase, PrivateDatabase
from .status_projection import build_status_projection


class PipelineError(RuntimeError):
    pass


def _run_id(started_at: str, host_id: str) -> str:
    return stable_id(started_at, host_id, str(os.getpid()), prefix="marun")


def _object_key(sha256: str) -> str:
    return f"private-agentdatabase/sha256/{sha256[:2]}/{sha256}"


def _normalized_key(run_id: str) -> str:
    return f"private-agentdatabase/normalized/{run_id}/events.jsonl"


def _write_jsonl(path: Path, events: Iterable[NormalizedEvent]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for event in events:
            handle.write(json.dumps(asdict(event), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")
            count += 1
    return count


def _iter_events(path: Path) -> Iterable[NormalizedEvent]:
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            value = json.loads(line)
            yield NormalizedEvent(**value)


def _normalized_batch_fact(normalized_key: str | None, objects: Iterable[object]) -> dict[str, object]:
    if not normalized_key:
        raise PipelineError("manifest 缺少规范化事件批次")
    for item in objects:
        row = item if isinstance(item, dict) else asdict(item)
        if row.get("object_key") != normalized_key:
            continue
        if row.get("readback_verified") is not True or row.get("readback_sha256") != row.get("sha256"):
            raise PipelineError("规范化事件批次缺少完整读回证明")
        return {
            "schema_version": "memory_atlas.normalized_event_batch_ref.v1",
            "object_key": normalized_key,
            "sha256": row.get("sha256"),
            "size_bytes": row.get("size_bytes"),
            "readback_sha256": row.get("readback_sha256"),
            "readback_verified": True,
        }
    raise PipelineError("manifest 对象清单中缺少规范化事件批次")


class CapturePipeline:
    """Source-side lossless capture.

    This component is designed for the Mac/Codex Automation because the sources
    are local to that host. It has no deployment or Git write responsibilities.
    """

    def __init__(
        self,
        config: RuntimeConfig,
        object_store: ObjectStore | None = None,
        private_db: PrivateDatabase | None = None,
        clock=utc_now,
    ):
        self.config = config
        self.config.ensure_runtime_dirs()
        self.object_store = object_store or R2ObjectStore(config)
        self.private_db = private_db or GhPrivateDatabase(config.private_db_client)
        self.clock = clock
        self.outbox = FactOutbox(config.runtime_dir / "fact-outbox.sqlite3")
        self.failures = FailureCompoundStore(config.runtime_dir / "failure-compound.sqlite3")

    def run(self) -> dict[str, Any]:
        started_at = self.clock()
        run_id = _run_id(started_at, self.config.source_host_id)
        work = self.config.work_dir / run_id
        snapshots = work / "snapshots"
        work.mkdir(parents=True, exist_ok=False)
        manifest = RunManifest(
            schema_version="memory_atlas.capture_run.v1",
            run_id=run_id,
            started_at=started_at,
            completed_at=None,
            state=RunState.DISCOVERING,
            source_capture_host=self.config.source_host_id,
        )
        try:
            preflight = self.object_store.preflight()
            if preflight.get("state") != "PASS" or preflight.get("bucket_creation_attempted") is not False:
                raise PipelineError("R2 精确范围 preflight 未通过")
            registry = load_source_registry(self.config.source_registry)
            records, coverages = discover_inventory(registry, snapshots)
            manifest.source_coverages = coverages
            manifest.bytes_discovered = sum(item.size_bytes for item in records)
            required_bad = [
                item for item in coverages
                if item.required and item.state in {SourceState.MISSING_REQUIRED, SourceState.UNREADABLE}
            ]
            if required_bad:
                manifest.state = RunState.WAITING_SOURCE
                manifest.completed_at = self.clock()
                return self._publish_terminal(manifest, events=[], message="必需来源缺失，未伪报全量成功")
            manifest.state = RunState.CAPTURING
            all_events: list[NormalizedEvent] = []
            for record in records:
                receipt = self.object_store.put_file(_object_key(record.sha256), Path(record.materialized_path), record.sha256)
                manifest.objects.append(receipt)
                manifest.bytes_uploaded += receipt.size_bytes if receipt.operation in {"created", "repaired"} else 0
                manifest.objects_new += 1 if receipt.operation == "created" else 0
                manifest.objects_repaired += 1 if receipt.operation == "repaired" else 0
                manifest.objects_unchanged += 1 if receipt.operation == "unchanged" else 0
                all_events.extend(normalize_record(record))
            normalized_path = work / "events.jsonl"
            event_count = _write_jsonl(normalized_path, all_events)
            normalized_sha = sha256_file(normalized_path)
            normalized_receipt = self.object_store.put_file(_normalized_key(run_id), normalized_path, normalized_sha)
            manifest.objects.append(normalized_receipt)
            manifest.normalized_batch_key = normalized_receipt.object_key
            manifest.state = RunState.VERIFYING_OBJECTS
            if not all(item.readback_verified and item.readback_sha256 == item.sha256 for item in manifest.objects):
                raise PipelineError("至少一个对象缺少完整读回证明")
            manifest.state = RunState.PUBLISHING_FACTS
            analytics = build_behavior_analytics(all_events, generated_at=self.clock())
            analytics["normalized_event_batch"] = _normalized_batch_fact(
                manifest.normalized_batch_key,
                manifest.objects,
            )
            failure_snapshot = self.failures.export_snapshot(self.clock())
            analytics["recommendations"] = build_habit_recommendations(analytics, failure_snapshot)
            manifest.state = RunState.REFRESHING_ATLAS
            self._write_web_snapshots(analytics, failure_snapshot, manifest)
            manifest.state = RunState.SUCCEEDED
            manifest.completed_at = self.clock()
            result = self._publish_terminal(manifest, events=all_events, message="源端全量对账完成")
            result["event_count"] = event_count
            return result
        except Exception as exc:
            manifest.state = RunState.FAILED
            manifest.completed_at = self.clock()
            incident = self.failures.record_failure(
                component="memory-atlas-source-capture",
                category="automation_failure",
                severity="P0",
                error_code=exc.__class__.__name__,
                title=str(exc),
                occurred_at=manifest.completed_at,
                evidence_ref=f"runtime://capture/{run_id}",
                environment=self.config.source_host_id,
                details={"run_id": run_id},
            )
            manifest.error_signatures.append(incident.signature)
            try:
                self._publish_terminal(manifest, events=[], message="源端采集失败；已转为 Incident")
            except Exception:
                pass
            raise
        finally:
            cleanup_snapshots(snapshots)

    def _write_web_snapshots(
        self,
        analytics: dict[str, Any],
        failure_snapshot: dict[str, Any],
        manifest: RunManifest,
    ) -> None:
        private_snapshot = {
            "schema_version": "memory_atlas.private_analytics.v1",
            "generated_at": self.clock(),
            "source_contract": {
                "mode": "private_full_fidelity_read_only_analytics",
                "writeback": "proposal_only",
                "direct_stable_memory_mutation": False,
            },
            "run": {
                "run_id": manifest.run_id,
                "state": manifest.state.value,
                "started_at": manifest.started_at,
                "source_coverages": [
                    {**asdict(item), "state": item.state.value}
                    for item in manifest.source_coverages
                ],
                "objects": [asdict(item) for item in manifest.objects],
            },
            "behavior_economics": analytics,
            "failure_compound": failure_snapshot,
        }
        write_json_atomic(self.config.web_data_dir / "memory_atlas_private_analytics.json", private_snapshot)
        write_json_atomic(
            self.config.web_data_dir / "memory_atlas_status_projection.json",
            build_status_projection(private_snapshot),
        )
        if self.config.public_atlas_snapshot and self.config.public_atlas_snapshot.is_file():
            public = json.loads(self.config.public_atlas_snapshot.read_text(encoding="utf-8"))
            if not isinstance(public, dict):
                raise PipelineError("现有 Memory Atlas 快照不是 JSON object")
            private_atlas = dict(public)
            source_contract = dict(private_atlas.get("source_contract") or {})
            source_contract["mode"] = "private_full_fidelity_read_only_analytics"
            source_contract["private_analytics_snapshot"] = "/memory_atlas_private_analytics.json"
            private_atlas["source_contract"] = source_contract
            write_json_atomic(self.config.web_data_dir / "memory_atlas.json", private_atlas)

    def _publish_terminal(
        self,
        manifest: RunManifest,
        events: list[NormalizedEvent],
        message: str,
    ) -> dict[str, Any]:
        paths = run_fact_paths(manifest.run_id, manifest.started_at)
        manifest.private_database_paths = [
            paths["run"], paths["latest"], paths["catalog"], paths["analytics"],
            paths["failure_compound"], paths["runtime"],
        ]
        manifest_payload = manifest.to_dict()
        digest = manifest_digest(manifest)
        latest = {
            "schema_version": "memory_atlas.latest_run.v1",
            "run_id": manifest.run_id,
            "state": manifest.state.value,
            "started_at": manifest.started_at,
            "completed_at": manifest.completed_at,
            "manifest_path": paths["run"],
            "manifest_sha256": digest,
            "message_zh": message,
        }
        catalog = {
            "schema_version": "memory_atlas.object_catalog.v1",
            "run_id": manifest.run_id,
            "objects": [asdict(item) for item in manifest.objects],
            "normalized_batch_key": manifest.normalized_batch_key,
            "event_count": len(events),
        }
        runtime = {
            "schema_version": "memory_atlas.runtime_projection.v1",
            "run_id": manifest.run_id,
            "state": manifest.state.value,
            "source_host": manifest.source_capture_host,
            "generated_at": self.clock(),
            "facts_authority": "Private-Database",
            "object_authority": "Cloudflare R2 primary-objects/",
            "runtime_journal": "local SQLite, rebuildable",
        }
        now = self.clock()
        for relpath, payload, title in (
            (paths["run"], manifest_payload, f"memory-atlas: capture run {manifest.run_id}"),
            (paths["latest"], latest, "memory-atlas: update latest capture"),
            (paths["catalog"], catalog, f"memory-atlas: object catalog {manifest.run_id}"),
            (paths["runtime"], runtime, "memory-atlas: update runtime projection"),
        ):
            self.outbox.enqueue(relpath, payload, title, now)
        failure_snapshot = self.failures.export_snapshot(now)
        analytics = build_behavior_analytics(events, generated_at=now)
        if manifest.normalized_batch_key:
            analytics["normalized_event_batch"] = _normalized_batch_fact(
                manifest.normalized_batch_key,
                manifest.objects,
            )
        analytics["recommendations"] = build_habit_recommendations(analytics, failure_snapshot)
        self.outbox.enqueue(paths["analytics"], analytics, "memory-atlas: update behavior analytics", now)
        self.outbox.enqueue(paths["failure_compound"], failure_snapshot, "memory-atlas: update failure compound", now)
        flush = self.outbox.flush(self.private_db, now)
        if manifest.state == RunState.SUCCEEDED and flush["failed"]:
            raise PipelineError("对象已保存，但完成态事实尚未进入 Private-Database")
        return {
            "schema_version": "memory_atlas.capture_result.v1",
            "run_id": manifest.run_id,
            "state": manifest.state.value,
            "manifest_sha256": digest,
            "outbox": flush,
            "source_coverage": [
                {**asdict(item), "state": item.state.value}
                for item in manifest.source_coverages
            ],
            "objects": len(manifest.objects),
            "readback_verified_objects": sum(1 for item in manifest.objects if item.readback_verified),
            "bytes_discovered": manifest.bytes_discovered,
            "bytes_uploaded": manifest.bytes_uploaded,
        }


class RemoteReconcilePipeline:
    """OVH-side rebuild and verification. It never scans Mac source paths."""

    def __init__(
        self,
        config: RuntimeConfig,
        object_store: ObjectStore | None = None,
        private_db: PrivateDatabase | None = None,
        clock=utc_now,
    ):
        self.config = config
        self.config.ensure_runtime_dirs()
        self.object_store = object_store or R2ObjectStore(config)
        self.private_db = private_db or GhPrivateDatabase(config.private_db_client)
        self.clock = clock
        self.failures = FailureCompoundStore(config.runtime_dir / "failure-compound.sqlite3")

    def run(self) -> dict[str, Any]:
        latest = self.private_db.get_json("memory-atlas/runs/latest.json")
        if latest.get("state") != RunState.SUCCEEDED.value:
            return {
                "schema_version": "memory_atlas.remote_reconcile.v1",
                "state": "WAITING_SOURCE",
                "source_state": latest.get("state", "UNKNOWN"),
                "run_id": latest.get("run_id"),
                "message_zh": "最近源端运行未成功；OVH 不会伪造新鲜快照。",
            }
        manifest_path = str(latest["manifest_path"])
        manifest = self.private_db.get_json(manifest_path)
        objects = manifest.get("objects", [])
        missing: list[str] = []
        for row in objects:
            if not isinstance(row, dict):
                continue
            key = str(row.get("object_key", ""))
            digest = str(row.get("sha256", ""))
            if not key or not digest or not self.object_store.exists_with_hash(key, digest):
                missing.append(key or "<missing-key>")
        if missing:
            incident = self.failures.record_failure(
                component="memory-atlas-remote-reconcile",
                category="data_integrity",
                severity="P0",
                error_code="OBJECT_READBACK_MISMATCH",
                title="远端对象清单与 R2 字节不一致",
                occurred_at=self.clock(),
                evidence_ref=f"private-db://{manifest_path}",
                environment=socket.gethostname(),
                details={"missing": missing[:100]},
            )
            return {
                "schema_version": "memory_atlas.remote_reconcile.v1",
                "state": "FAILED",
                "run_id": latest.get("run_id"),
                "missing_or_corrupt_objects": missing,
                "incident_id": incident.incident_id,
            }
        normalized_key = manifest.get("normalized_batch_key")
        if not isinstance(normalized_key, str) or not normalized_key:
            raise PipelineError("源端 manifest 缺少 normalized_batch_key")
        with tempfile.NamedTemporaryFile(prefix="memory-atlas-events-", suffix=".jsonl", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            self.object_store.get_file(normalized_key, temporary)
            analytics = build_behavior_analytics(_iter_events(temporary), generated_at=self.clock())
        finally:
            temporary.unlink(missing_ok=True)
        event_count = int(analytics["event_count"])
        analytics["normalized_event_batch"] = _normalized_batch_fact(normalized_key, objects)
        failure_snapshot = self.failures.export_snapshot(self.clock())
        analytics["recommendations"] = build_habit_recommendations(analytics, failure_snapshot)
        private_snapshot = {
            "schema_version": "memory_atlas.private_analytics.v1",
            "generated_at": self.clock(),
            "source_contract": {
                "mode": "private_full_fidelity_read_only_analytics",
                "writeback": "proposal_only",
                "direct_stable_memory_mutation": False,
            },
            "run": {
                "run_id": latest.get("run_id"),
                "state": "REBUILT_FROM_AUTHORITIES",
                "source_completed_at": latest.get("completed_at"),
                "source_coverages": manifest.get("source_coverages", []),
                "objects": objects,
            },
            "behavior_economics": analytics,
            "failure_compound": failure_snapshot,
        }
        write_json_atomic(self.config.web_data_dir / "memory_atlas_private_analytics.json", private_snapshot)
        status_path = self.config.web_data_dir / "memory_atlas_status_projection.json"
        write_json_atomic(status_path, build_status_projection(private_snapshot))
        return {
            "schema_version": "memory_atlas.remote_reconcile.v1",
            "state": "PASS",
            "run_id": latest.get("run_id"),
            "verified_objects": len(objects),
            "events": event_count,
            "snapshot": str(self.config.web_data_dir / "memory_atlas_private_analytics.json"),
            "status_projection": str(status_path),
        }
