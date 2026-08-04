from __future__ import annotations

import json
import os
import shutil
import socket
import sys
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

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


def _repo_file(*parts: str) -> Path:
    return Path(__file__).resolve().parents[2].joinpath(*parts)


DEFAULT_SOURCE_REGISTRY = (
    Path(__file__).resolve().parents[3] / "ops" / "memory-atlas" / "source-registry.json"
)


def _as_row(item: object) -> dict[str, Any]:
    return item if isinstance(item, dict) else asdict(item)  # type: ignore[arg-type]


def _object_readback_ok(objects: Iterable[object]) -> bool:
    rows = [_as_row(item) for item in objects]
    return bool(rows) and all(
        row.get("readback_verified") is True and row.get("readback_sha256") == row.get("sha256")
        for row in rows
    )


def _authority_tiers(registry_path: Path | None) -> dict[str, dict[str, Any]]:
    """Tier facts live in the registry so availability is data, not a hard-coded guess."""
    path = registry_path or DEFAULT_SOURCE_REGISTRY
    if not Path(path).is_file():
        return {}
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        str(row["source_id"]): row
        for row in payload.get("cloud_native_authorities", [])
        if isinstance(row, dict) and row.get("source_id")
    }


def cloud_native_authorities(
    *,
    objects: Iterable[object],
    normalized_batch_key: str | None,
    private_database_paths: Iterable[str],
    github_release: Mapping[str, Any] | None,
    observed_at: str,
    registry_path: Path | None = None,
) -> list[dict[str, Any]]:
    """Tier A rows, every state derived from something this run actually read.

    `required_for_product` comes from the registry: the GitHub private release is
    a real cloud authority and a real gap when it is missing, but the product can
    still render today's facts without it, so it degrades instead of failing.
    """
    rows = [_as_row(item) for item in objects]
    tiers = _authority_tiers(registry_path)
    paths = list(private_database_paths)
    delta = [row for row in rows if row.get("object_key") == normalized_batch_key] if normalized_batch_key else []

    measured = {
        "r2_primary_objects": (bool(rows), _object_readback_ok(rows), len(rows), sum(int(row.get("size_bytes", 0) or 0) for row in rows)),
        "r2_normalized_events": (bool(delta), _object_readback_ok(delta), len(delta), sum(int(row.get("size_bytes", 0) or 0) for row in delta)),
        "private_database_facts": (bool(paths), bool(paths), len(paths), 0),
        "github_private_release": (
            github_release is not None,
            bool(github_release and github_release.get("files")),
            len((github_release or {}).get("files") or []),
            0,
        ),
    }

    out: list[dict[str, Any]] = []
    for source_id, (present, healthy, count, size) in measured.items():
        spec = tiers.get(source_id, {})
        out.append(
            {
                "source_id": source_id,
                "label_zh": str(spec.get("label_zh", source_id)),
                "tier": "A_CLOUD_NATIVE",
                "required_for_capture": bool(spec.get("required_for_capture", True)),
                "required_for_product": bool(spec.get("required_for_product", True)),
                "state": "READY" if present and healthy else ("FAILED" if present else "MISSING"),
                "object_count": count,
                "size_bytes": size,
                "last_observed_at": observed_at,
            }
        )
    return out


def same_run_evidence_rows(
    *,
    run_id: str,
    trace_id: str,
    r2_readback: bool | None,
    private_database_readback: bool | None,
    ovh_reconcile: bool | None,
    status_projection: bool | None,
    ref: str | None = None,
) -> dict[str, dict[str, Any]]:
    """None means the caller never ran that check — NOT_RUN, never a silent PASS."""

    def row(value: bool | None) -> dict[str, Any]:
        if value is None:
            return {"state": "NOT_RUN", "run_id": None, "trace_id": None, "ref": None}
        return {
            "state": "PASS" if value else "FAIL",
            "run_id": run_id if value else None,
            "trace_id": trace_id if value else None,
            "ref": ref if value else None,
        }

    return {
        "r2_readback": row(r2_readback),
        "private_database_readback": row(private_database_readback),
        "ovh_reconcile": row(ovh_reconcile),
        "status_projection": row(status_projection),
    }


CANONICAL_MANIFEST_KEY = "private-agentdatabase/normalized/canonical/MANIFEST.json"


def load_supersession(object_store, work_dir: Path) -> dict[str, Any]:
    """Which normalized objects were folded into the canonical union, and proof.

    The R2 dedup replaced ten whole-history rollups with one canonical union and
    deleted the originals. Any source manifest written before that still names a
    deleted key, so the reconcile has to be able to tell "superseded" from
    "lost" — and it may only do that from the record written at deletion time,
    never by assuming.
    """
    target = Path(work_dir) / "canonical-supersession.json"
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        object_store.get_file(CANONICAL_MANIFEST_KEY, target)
        value = json.loads(target.read_text(encoding="utf-8"))
    except Exception:
        return {"available": False, "canonical_object": None, "sha256": None, "superseded": set()}
    finally:
        if target.exists():
            target.unlink()
    superseded = {str(row) for row in value.get("supersedes", []) if isinstance(row, str)}
    return {
        "available": bool(superseded and value.get("object") and value.get("sha256")),
        "canonical_object": value.get("object"),
        "sha256": value.get("sha256"),
        "unique_events": value.get("unique_events"),
        "superseded": superseded,
    }


def visual_event(event: Mapping[str, Any]) -> dict[str, Any]:
    """Project a NormalizedEvent onto the fields visual analytics contracts on.

    The repository's event model predates the v0.0.0.32 visual contract and uses
    `activity` where the contract says `activity_type`, and has no `model_tool`
    at all. Mapping explicitly — rather than handing over the whole record —
    also keeps `object_sha256`, `relative_path` and `payload` out of anything
    that can reach a browser.
    """
    row = dict(event)
    effort = row.get("effort_minutes")
    return {
        "event_id": str(row.get("event_id", "")),
        "occurred_at": str(row.get("occurred_at", "")),
        "activity_type": str(row.get("activity") or row.get("activity_type") or "unknown"),
        "outcome_state": str(row.get("outcome_state") or "unknown"),
        # Which agent/tool produced the event is not captured per event today;
        # the source is the closest honest stand-in and is never invented.
        "model_tool": str(row.get("model_tool") or row.get("source_id") or "unknown"),
        "work_time_minutes": float(effort) if isinstance(effort, (int, float)) else None,
        "outcome_evidence": bool(str(row.get("evidence_ref") or "").strip()),
        "verified_at": row.get("verified_at") if isinstance(row.get("verified_at"), str) else None,
    }


def _link_or_copy(src: str, dst: str) -> None:
    """Hardlink when the filesystem allows it, copy when it does not.

    The release tree and the work directory are on different filesystems on the
    production host, and a hardlink cannot cross devices.
    """
    try:
        os.link(src, dst)
    except OSError:
        shutil.copy2(src, dst)


def regenerate_atlas_snapshot(
    events: Iterable[Mapping[str, Any]],
    *,
    database_dir: Path,
    work_dir: Path,
    output: Path,
    runner=None,
) -> dict[str, Any]:
    """Rebuild the ten original views' snapshot from the live event plane.

    `data/processed/codex/*` froze when its local writer stopped on 2026-07-17,
    so the ten views showed 128 sessions ending in mid-July while the capture
    plane held 505 through today. The two files are regenerated from the events
    and the repository's own builder is run over them, unchanged — the graph
    model is not reimplemented, only its stale input is replaced.

    The rest of the data tree is symlinked, not copied: it is ~576 MB and the
    host runs this every fifteen minutes.
    """
    import subprocess

    from .codex_activity_adapter import build_daily_rows, build_session_rows

    sessions = build_session_rows(events)
    daily = build_daily_rows(sessions)
    if not sessions:
        return {"state": "SKIPPED", "reason": "no session events in this run", "session_count": 0}

    # The builder's own safe_repo_path rejects symlinks outright, so the tree it
    # is pointed at must be real files. Hardlinks are indistinguishable from
    # regular files, cost no space and copy instantly. Everything is linked
    # except data/public_raw, which is 433 MB the builder never opens — it needs
    # config/ and the derived trees as well as data/, so an allowlist of two or
    # three directories keeps breaking on the next thing it reads.
    root = Path(work_dir) / "atlas-build"
    if root.exists():
        shutil.rmtree(root)
    root.mkdir(parents=True)
    source = Path(database_dir)
    # Exactly what the builder reads, and nothing else. Linking the whole tree
    # took minutes per run on tens of thousands of files, and this executes
    # every fifteen minutes. If the builder ever needs another path it fails
    # loudly on that path rather than being masked by copying everything.
    for relative in ("config", "data/memory", "data/processed", "data/derived"):
        child = source / relative
        if not child.is_dir():
            continue
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(child, target, copy_function=_link_or_copy, dirs_exist_ok=True)

    def _write(path: Path, rows: list[dict[str, Any]]) -> None:
        # The destination is a hardlink to the repository's own copy; writing
        # through it would rewrite the source. Break the link first.
        path.unlink(missing_ok=True)
        with path.open("w", encoding="utf-8", newline="\n") as handle:
            for row in rows:
                handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")

    codex = root / "data" / "processed" / "codex"
    codex.mkdir(parents=True, exist_ok=True)
    _write(codex / "codex_session_manifest.jsonl", sessions)
    _write(codex / "codex_daily_activity.jsonl", daily)

    builder = Path(database_dir) / "scripts" / "build_memory_atlas_data.py"
    staged = root / "memory_atlas.json"
    command = [sys.executable, "-B", str(builder), "--database-dir", str(root), "--output", str(staged)]
    result = (runner or subprocess.run)(command, capture_output=True, text=True)
    if result.returncode != 0 or not staged.is_file():
        return {
            "state": "FAILED",
            "session_count": len(sessions),
            "reason": (result.stderr or result.stdout or "builder produced no output")[-400:],
        }
    # Only replace the served snapshot once the builder has produced a whole one.
    destination = Path(output)
    write_json_atomic(destination, json.loads(staged.read_text(encoding="utf-8")))
    # nginx runs unprivileged inside the container and reads this through a
    # read-only mount. The pipeline's umask writes 0600, so the container got
    # "Permission denied" and silently fell back to the snapshot baked into the
    # release — the browser kept seeing July while the join was already correct
    # on disk. Only this file is widened; the private analytics beside it stays
    # 0600 and no nginx location serves it.
    os.chmod(destination, 0o644)
    for directory in (destination.parent, destination.parent.parent):
        try:
            os.chmod(directory, os.stat(directory).st_mode | 0o005)
        except OSError:
            pass
    # The staged tree is ~100 MB and this runs every fifteen minutes; leaving it
    # for the next run to delete filled a 38 GB disk twice.
    shutil.rmtree(root, ignore_errors=True)
    return {
        "state": "PUBLISHED",
        "session_count": len(sessions),
        "day_count": len(daily),
        "first_day": daily[0]["date"],
        "last_day": daily[-1]["date"],
    }


def _release_identity() -> dict[str, Any]:
    """What the running process can actually observe about its own release.

    Blank environment means UNVERIFIED, never a fabricated identity: the browser
    cross-checks these against the API headers and would rather show 未验证 than
    a value nobody proved.
    """
    commit = os.environ.get("MEMORY_ATLAS_REPOSITORY_COMMIT", "").strip() or None
    release_id = os.environ.get("MEMORY_ATLAS_RELEASE_ID", "").strip() or None
    digest = os.environ.get("MEMORY_ATLAS_ARTIFACT_DIGEST", "").strip() or None
    revision = os.environ.get("MEMORY_ATLAS_DEPLOYMENT_REVISION", "").strip() or None
    observed = any((commit, release_id, digest, revision))
    return {
        "identity_state": "OBSERVED" if observed else "UNVERIFIED",
        "repository_commit": commit,
        "release_id": release_id,
        "artifact_digest": digest,
        "deployment_revision": revision,
    }


def normalize_live_run_block(
    run: Mapping[str, Any],
    *,
    run_id: str,
    trace_id: str,
    state: str,
    started_at: str | None,
    completed_at: str | None,
    reconciled_at: str | None = None,
) -> dict[str, Any]:
    """The private analytics run block predates LiveSnapshot and lacks its identity fields."""
    block = dict(run)
    block["run_id"] = run_id
    block["trace_id"] = trace_id
    block["state"] = state
    block["source_started_at"] = started_at
    block["source_completed_at"] = completed_at
    block["reconciled_at"] = reconciled_at
    return block


class LiveSnapshotPublisherMixin:
    """Both hosts publish through exactly one adapter and one store.

    The caller supplies the evidence because only the caller knows what it
    actually read. The capture host has no OVH reconcile read-back, so it
    declines here rather than claiming an authority it never touched; the
    reconcile host verified all four and publishes.

    Rollback is flag-off: with MEMORY_ATLAS_LIVE_SNAPSHOT disabled nothing is
    published and every existing path behaves exactly as before.
    """

    def _publish_live_snapshot(
        self,
        private_snapshot: dict[str, Any],
        runtime_evidence: dict[str, Any],
        events: Iterable[Mapping[str, Any]] | None = None,
    ) -> dict[str, Any] | None:
        if os.environ.get("MEMORY_ATLAS_LIVE_SNAPSHOT", "1") == "0":
            self._live_snapshot_error = "feature flag off"
            return None
        schema = _repo_file("schema", "memory_atlas.live_snapshot.v1.schema.json")
        if not schema.is_file():
            self._live_snapshot_error = f"schema not found: {schema}"
            return None
        try:
            from .benchmark_comparator import compare
            from .live_snapshot_adapter import build_live_snapshot
            from .live_snapshot_store import LiveSnapshotStore
            from .visual_analytics import build_visual_analytics

            # build_behavior_analytics deliberately does not retain raw event
            # payloads, so behavior_economics carries none. Reading them from
            # there produced a snapshot whose analysis was over zero events
            # while the run had just counted 122,080 — a zero presented as the
            # current reading, which is the one thing the contract forbids.
            rows = list(events) if events is not None else list(
                private_snapshot.get("behavior_economics", {}).get("events") or []
            )
            declared = int(private_snapshot.get("behavior_economics", {}).get("event_count", 0) or 0)
            if declared and not rows:
                raise PipelineError(
                    f"run reports {declared} events but none were handed to the live snapshot; refusing to publish zeros"
                )
            visual = build_visual_analytics(visual_event(row) for row in rows)
            registry_path = _repo_file("benchmark", "registry.v1.json")
            benchmark = (
                compare({}, json.loads(registry_path.read_text(encoding="utf-8")))
                if registry_path.is_file()
                else {"benchmarks": [], "comparable": False}
            )
            snapshot = build_live_snapshot(
                private_snapshot, visual, runtime_evidence, benchmark, evaluated_at=self.clock()
            )
            store = LiveSnapshotStore(self.config.web_data_dir / "live-snapshot", schema)
            published = store.publish(snapshot)
            self._live_snapshot_error = ""
            return published
        except Exception as exc:  # never let the live snapshot break the existing product
            self._live_snapshot_error = f"{type(exc).__name__}: {exc}"
            return None


class CapturePipeline(LiveSnapshotPublisherMixin):
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
        self._live_snapshot_error = ""
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
            private_snapshot = self._write_web_snapshots(analytics, failure_snapshot, manifest)
            manifest.state = RunState.SUCCEEDED
            manifest.completed_at = self.clock()
            # Same adapter as the OVH reconcile path, with this host's own
            # evidence. The capture host never runs the OVH reconcile, so that
            # row is NOT_RUN and the adapter declines rather than inventing an
            # authority read-back. What is published on OVH is published there.
            live_snapshot = self._publish_live_snapshot(
                {
                    **private_snapshot,
                    "run": normalize_live_run_block(
                        private_snapshot["run"],
                        run_id=manifest.run_id,
                        trace_id=manifest.run_id,
                        state=manifest.state.value,
                        started_at=manifest.started_at,
                        completed_at=manifest.completed_at,
                    ),
                },
                {
                    "schema_version": "memory_atlas.runtime_evidence.v1",
                    "generated_at": self.clock(),
                    "run_id": manifest.run_id,
                    "trace_id": manifest.run_id,
                    "release": _release_identity(),
                    "cloud_native_sources": cloud_native_authorities(
                        objects=manifest.objects,
                        normalized_batch_key=manifest.normalized_batch_key,
                        private_database_paths=manifest.private_database_paths,
                        github_release=manifest.github_private_release_backup,
                        observed_at=manifest.completed_at,
                        registry_path=self.config.source_registry,
                    ),
                    "same_run_evidence": same_run_evidence_rows(
                        run_id=manifest.run_id,
                        trace_id=manifest.run_id,
                        r2_readback=_object_readback_ok(manifest.objects),
                        private_database_readback=None,
                        ovh_reconcile=None,
                        status_projection=None,
                    ),
                },
                events=[asdict(event) for event in all_events],
            )
            result = self._publish_terminal(manifest, events=all_events, message="源端全量对账完成")
            result["live_snapshot"] = live_snapshot or {
                "state": "NOT_PUBLISHED",
                "reason": self._live_snapshot_error or "capture host has no OVH reconcile evidence",
            }
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

    def _write_web_snapshots(
        self,
        analytics: dict[str, Any],
        failure_snapshot: dict[str, Any],
        manifest: RunManifest,
    ) -> dict[str, Any]:
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
        return private_snapshot

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


class RemoteReconcilePipeline(LiveSnapshotPublisherMixin):
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
        self._live_snapshot_error = ""

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
        supersession = load_supersession(self.object_store, self.config.work_dir)
        missing: list[str] = []
        superseded: list[str] = []
        for row in objects:
            if not isinstance(row, dict):
                continue
            key = str(row.get("object_key", ""))
            digest = str(row.get("sha256", ""))
            if key and digest and self.object_store.exists_with_hash(key, digest):
                continue
            # Superseded is not lost — but only when the record written at
            # deletion time says so, and only when the object that replaced it
            # still verifies byte-for-byte.
            if (
                key
                and supersession["available"]
                and key in supersession["superseded"]
                and self.object_store.exists_with_hash(supersession["canonical_object"], supersession["sha256"])
            ):
                superseded.append(key)
                continue
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
        event_source = normalized_key
        live_events: list[dict[str, Any]] = []
        if normalized_key in superseded:
            # The canonical union is a proven superset of every rollup it
            # replaced (122,080 events against a largest single run of 112,036),
            # so reading it loses nothing this manifest referenced.
            event_source = str(supersession["canonical_object"])
        with tempfile.NamedTemporaryFile(prefix="memory-atlas-events-", suffix=".jsonl", delete=False) as handle:
            temporary = Path(handle.name)
        try:
            self.object_store.get_file(event_source, temporary)
            analytics = build_behavior_analytics(_iter_events(temporary), generated_at=self.clock())
            live_events = [asdict(event) for event in _iter_events(temporary)]
            # The ten original views read a snapshot built from
            # data/processed/codex, whose local writer stopped on 2026-07-17.
            # Regenerating it here is what actually joins the two planes.
            try:
                atlas_rebuild = regenerate_atlas_snapshot(
                    live_events,
                    database_dir=Path(__file__).resolve().parents[2],
                    work_dir=self.config.work_dir,
                    output=self.config.web_data_dir / "memory_atlas.json",
                )
            except Exception as exc:
                # A cross-device link error took the whole reconcile down and the
                # deployment auto-rolled back. This run also publishes the live
                # snapshot and the status projection; a failed graph rebuild must
                # degrade to the last good snapshot, never cancel the rest.
                atlas_rebuild = {"state": "FAILED", "reason": f"{type(exc).__name__}: {exc}"[:400]}
        finally:
            temporary.unlink(missing_ok=True)
        event_count = int(analytics["event_count"])
        analytics["normalized_event_batch"] = _normalized_batch_fact(normalized_key, objects)
        if superseded:
            analytics["normalized_event_batch"]["superseded_by_canonical"] = {
                "event_source": event_source,
                "canonical_sha256": supersession["sha256"],
                "superseded_keys": sorted(superseded),
            }
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
        # This host is the one the browser reads from, and it is the only host
        # that can honestly claim all four authority read-backs: it verified
        # every object against R2 above, read the run facts back out of
        # Private-Database, is itself the OVH reconcile, and just wrote the
        # status projection. Same adapter as the capture path.
        run_id = str(latest.get("run_id") or "")
        reconciled_at = self.clock()
        live_snapshot = self._publish_live_snapshot(
            {
                **private_snapshot,
                "run": normalize_live_run_block(
                    private_snapshot["run"],
                    run_id=run_id,
                    trace_id=run_id,
                    state="REBUILT_FROM_AUTHORITIES",
                    started_at=latest.get("started_at"),
                    completed_at=latest.get("completed_at"),
                    reconciled_at=reconciled_at,
                ),
            },
            {
                "schema_version": "memory_atlas.runtime_evidence.v1",
                "generated_at": reconciled_at,
                "run_id": run_id,
                "trace_id": run_id,
                "release": _release_identity(),
                "cloud_native_sources": cloud_native_authorities(
                    objects=objects,
                    normalized_batch_key=normalized_key,
                    private_database_paths=[manifest_path],
                    github_release=manifest.get("github_private_release_backup"),
                    observed_at=str(latest.get("completed_at") or reconciled_at),
                    registry_path=self.config.source_registry,
                ),
                "same_run_evidence": same_run_evidence_rows(
                    run_id=run_id,
                    trace_id=run_id,
                    r2_readback=True,
                    private_database_readback=True,
                    ovh_reconcile=True,
                    status_projection=True,
                    ref=f"private-db://{manifest_path}",
                ),
            },
            events=live_events,
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
            "live_snapshot": live_snapshot
            or {"state": "NOT_PUBLISHED", "reason": self._live_snapshot_error or "live snapshot disabled"},
            "atlas_snapshot": atlas_rebuild,
        }
