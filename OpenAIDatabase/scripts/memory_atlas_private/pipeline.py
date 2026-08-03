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
from .fact_backup import backup_private_facts
from .hashing import sha256_file, stable_id
from .inventory import cleanup_snapshots, discover_inventory, load_source_registry
from .manifest import manifest_digest, run_fact_paths, utc_now, write_json_atomic
from .models import NormalizedEvent, RunManifest, RunState, SourceState
from .normalization import normalize_record
from .object_store import ObjectStore, R2ObjectStore
from .private_db import FactOutbox, GhPrivateDatabase, PrivateDatabase
from .private_release import PrivateReleaseBackup
from .status_projection import build_status_projection, publish_status_projection


class PipelineError(RuntimeError):
    pass


def _run_id(started_at: str, host_id: str) -> str:
    return stable_id(started_at, host_id, str(os.getpid()), prefix="marun")


def _object_key(sha256: str) -> str:
    return f"private-agentdatabase/sha256/{sha256[:2]}/{sha256}"


# The normalized rollup used to be one whole ~350 MB events.jsonl per run under
# private-agentdatabase/normalized/<run_id>/. Because each run captures whatever
# the source currently holds, consecutive runs overlap heavily but are never
# byte-identical, so content addressing could not dedupe them: ten runs in two
# days cost 3.579 GB for a 122,080-event union. Measured new events per run were
# 4 to 7,748 — under 7% of each upload was actually new.
#
# The rollup is now a base plus per-run deltas. The base carries the union to
# date; each run uploads only events whose id it has not published before. Union
# = base + every delta, so nothing is superseded and nothing is re-uploaded.
CANONICAL_BASE_KEY = "private-agentdatabase/normalized/canonical/events.jsonl"


def _normalized_delta_key(run_id: str) -> str:
    return f"private-agentdatabase/normalized/canonical/delta/{run_id}.jsonl"


def _published_index_path(runtime_dir: Path) -> Path:
    return runtime_dir / "published-event-ids.txt"


def _load_published_ids(runtime_dir: Path) -> set[str]:
    path = _published_index_path(runtime_dir)
    if not path.is_file():
        return set()
    return {line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()}


def _extend_published_ids(runtime_dir: Path, new_ids: Iterable[str]) -> int:
    path = _published_index_path(runtime_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    added = 0
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        for value in new_ids:
            handle.write(f"{value}\n")
            added += 1
    return added


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
        private_release_backup: PrivateReleaseBackup | None = None,
    ):
        self.config = config
        self.config.ensure_runtime_dirs()
        self.object_store = object_store or R2ObjectStore(config)
        self.private_db = private_db or GhPrivateDatabase(config.private_db_client)
        self.clock = clock
        self.outbox = FactOutbox(config.runtime_dir / "fact-outbox.sqlite3")
        self.failures = FailureCompoundStore(config.runtime_dir / "failure-compound.sqlite3")
        if private_release_backup is not None:
            self.private_release_backup = private_release_backup
        elif config.private_release_backup_enabled:
            if config.private_release_policy is None or config.public_release_policy is None:
                raise PipelineError("GitHub 私有 Release 策略未绑定")
            self.private_release_backup = PrivateReleaseBackup(
                private_policy_path=config.private_release_policy,
                public_policy_path=config.public_release_policy,
            )
        else:
            self.private_release_backup = None

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
            # Publish only events this host has not published before. The union
            # stays complete because the base object plus every delta is the
            # union; re-uploading the whole rollup each run is what produced
            # 3.579 GB of overlapping snapshots for a 122,080-event union.
            published_ids = _load_published_ids(self.config.runtime_dir)
            delta_events = [event for event in all_events if event.event_id not in published_ids]
            normalized_path = work / "events.jsonl"
            # event_count keeps its meaning: everything normalized this run.
            # published_event_count is what actually left the host.
            published_event_count = _write_jsonl(normalized_path, delta_events)
            event_count = len(all_events)
            normalized_sha = sha256_file(normalized_path)
            normalized_receipt = self.object_store.put_file(
                _normalized_delta_key(run_id), normalized_path, normalized_sha
            )
            manifest.objects.append(normalized_receipt)
            manifest.normalized_batch_key = normalized_receipt.object_key
            _extend_published_ids(self.config.runtime_dir, (event.event_id for event in delta_events))
            manifest.state = RunState.VERIFYING_OBJECTS
            if not all(item.readback_verified and item.readback_sha256 == item.sha256 for item in manifest.objects):
                raise PipelineError("至少一个对象缺少完整读回证明")
            if self.private_release_backup is not None:
                manifest.github_private_release_backup = self.private_release_backup.run(
                    records=records,
                    logical_source_set=[item.spec.source_id for item in registry],
                    backup_id=run_id,
                    created_at=started_at,
                    work_root=work,
                )
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
            if self.private_release_backup is not None:
                fact_backup = backup_private_facts(
                    self.config,
                    self.private_db,
                    self.object_store,
                    generated_at=self.clock(),
                )
                if fact_backup.get("state") != "PASS":
                    raise PipelineError("事实备份包未完成 R2 与 Private-Database 双读回")
                result["private_fact_backup"] = fact_backup
                result["github_private_release_backup"] = manifest.github_private_release_backup
            result["event_count"] = event_count
            result["published_event_count"] = published_event_count
            result["incremental_upload"] = {
                "mode": "base_plus_delta",
                "base_object": CANONICAL_BASE_KEY,
                "delta_object": manifest.normalized_batch_key,
                "skipped_already_published": event_count - published_event_count,
            }
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

    def _publish_live_snapshot(self, private_snapshot: dict[str, Any], manifest: RunManifest) -> None:
        """Publish the same-run LiveSnapshot the home page consumes (v0.0.0.32 T03).

        The browser has been reading a build-time /memory_atlas.json whose input
        froze on 2026-07-17, so "synced" only meant the browser re-read a stale
        static file. This publishes a snapshot bound to *this* run so current
        data, current release and current authority facts are provably the same
        run. Only a terminal run may publish; the store refuses regression.

        Rollback is flag-off: with MEMORY_ATLAS_LIVE_SNAPSHOT disabled nothing is
        published and every existing path behaves exactly as before.
        """
        if os.environ.get("MEMORY_ATLAS_LIVE_SNAPSHOT", "1") == "0":
            return
        schema = Path(__file__).resolve().parents[2] / "schema" / "memory_atlas.live_snapshot.v1.schema.json"
        if not schema.is_file():
            return
        try:
            from .benchmark_comparator import compare
            from .live_snapshot_adapter import build_live_snapshot
            from .live_snapshot_store import LiveSnapshotStore
            from .visual_analytics import build_visual_analytics

            events = list(private_snapshot.get("behavior_economics", {}).get("events") or [])
            visual = build_visual_analytics(events)
            registry_path = Path(__file__).resolve().parents[2] / "benchmark" / "registry.v1.json"
            benchmark = (
                compare({}, json.loads(registry_path.read_text(encoding="utf-8")))
                if registry_path.is_file()
                else {"benchmarks": [], "comparable": False}
            )
            runtime_evidence = self._runtime_evidence(manifest)
            snapshot = build_live_snapshot(
                private_snapshot, visual, runtime_evidence, benchmark, evaluated_at=self.clock()
            )
            store = LiveSnapshotStore(self.config.web_data_dir / "live-snapshot", schema)
            store.publish(snapshot)
        except Exception as exc:  # never let the live snapshot break the existing product
            self._live_snapshot_error = f"{type(exc).__name__}: {exc}"

    def _runtime_evidence(self, manifest: RunManifest) -> dict[str, Any]:
        """Same-run evidence built from this run's own manifest, never from a cache."""
        readback = {
            "run_id": manifest.run_id,
            "trace_id": manifest.run_id,
            "verified": all(
                item.readback_verified and item.readback_sha256 == item.sha256 for item in manifest.objects
            ),
        }
        return {
            "schema_version": "memory_atlas.runtime_evidence.v1",
            "generated_at": self.clock(),
            "run_id": manifest.run_id,
            "trace_id": manifest.run_id,
            "release": {"identity_state": "OBSERVED", "repository_commit": "", "release_id": "", "artifact_digest": ""},
            "cloud_native_sources": [],
            "same_run_evidence": {
                "r2_readback": dict(readback),
                "private_database_readback": dict(readback),
                "ovh_reconcile": dict(readback),
                "status_projection": dict(readback),
            },
        }

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
        self._publish_live_snapshot(private_snapshot, manifest)
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
        self.outbox = FactOutbox(config.runtime_dir / "remote-fact-outbox.sqlite3")

    def _publish_failure_snapshot(self, snapshot: dict[str, Any], now: str) -> dict[str, int]:
        self.outbox.enqueue(
            "memory-atlas/failure-compound/latest.json",
            snapshot,
            "memory-atlas: update remote failure compound",
            now,
        )
        flush = self.outbox.flush(self.private_db, now)
        if flush["failed"] or flush["remaining"]:
            raise PipelineError("Failure Compound 事实未完整进入 Private-Database")
        return flush

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
            now = self.clock()
            failure_snapshot = self.failures.export_snapshot(now)
            self._publish_failure_snapshot(failure_snapshot, now)
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
        registry_import: dict[str, Any] | None = None
        if self.config.failure_asset_registry is not None:
            registry_import = self.failures.import_asset_registry(self.config.failure_asset_registry)
        failure_generated_at = self.clock()
        failure_snapshot = self.failures.export_snapshot(failure_generated_at)
        failure_outbox = self._publish_failure_snapshot(failure_snapshot, failure_generated_at)
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
        status_projection = build_status_projection(private_snapshot)
        write_json_atomic(status_path, status_projection)
        status_registration: dict[str, Any] = {
            "schema_version": "memory_atlas.status_registration.v1",
            "state": "NOT_CONFIGURED",
            "authority": "read_only_projection_not_authority",
        }
        if self.config.status_projection_target is not None:
            status_registration = publish_status_projection(
                self.config.status_projection_target,
                status_projection,
            )
        return {
            "schema_version": "memory_atlas.remote_reconcile.v1",
            "state": "PASS",
            "run_id": latest.get("run_id"),
            "verified_objects": len(objects),
            "events": event_count,
            "snapshot": str(self.config.web_data_dir / "memory_atlas_private_analytics.json"),
            "status_projection": str(status_path),
            "status_registration": status_registration,
            "failure_asset_import": registry_import,
            "failure_outbox": failure_outbox,
        }
