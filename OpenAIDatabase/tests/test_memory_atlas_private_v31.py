from __future__ import annotations

import importlib.util
import hashlib
import json
import os
import re
import shutil
import sqlite3
import subprocess
import threading
import urllib.error
import urllib.request
import weakref
from dataclasses import asdict, replace
from datetime import datetime, timedelta, timezone
from http.server import ThreadingHTTPServer
from pathlib import Path

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from OpenAIDatabase.scripts.memory_atlas_private.access_auth import (
    AccessVerificationError,
    CloudflareAccessVerifier,
)
from OpenAIDatabase.scripts.memory_atlas_private.action_queue import ActionQueue
from OpenAIDatabase.scripts.memory_atlas_private.analytics import (
    build_behavior_analytics,
    build_habit_recommendations,
    compare_with_benchmark,
)
from OpenAIDatabase.scripts.memory_atlas_private.api_server import ApiState, Handler
from OpenAIDatabase.scripts.memory_atlas_private.config import ConfigurationError, RuntimeConfig
from OpenAIDatabase.scripts.memory_atlas_private.failure_compound import (
    FailureCompoundError,
    FailureCompoundStore,
    failure_signature,
)
from OpenAIDatabase.scripts.memory_atlas_private.hashing import sha256_bytes, sha256_file, stable_id
from OpenAIDatabase.scripts.memory_atlas_private.inventory import (
    InventoryError,
    discover_inventory,
    load_source_registry,
)
from OpenAIDatabase.scripts.memory_atlas_private.models import InventoryRecord, NormalizedEvent, SourceState
from OpenAIDatabase.scripts.memory_atlas_private.normalization import normalize_record
from OpenAIDatabase.scripts.memory_atlas_private.object_store import LocalObjectStore
from OpenAIDatabase.scripts.memory_atlas_private.pipeline import CapturePipeline, RemoteReconcilePipeline
from OpenAIDatabase.scripts.memory_atlas_private.private_db import (
    FactOutbox,
    LocalPrivateDatabase,
    PrivateDatabaseError,
)
from OpenAIDatabase.scripts.memory_atlas_private.restore import RestoreError, isolated_restore
from OpenAIDatabase.scripts.memory_atlas_private.sqlite_snapshot import create_consistent_snapshot


FIXED_TIME = "2026-08-02T00:00:00+00:00"


def write_registry(path: Path, sources: list[dict[str, object]]) -> Path:
    path.write_text(json.dumps({"schema_version": "memory_atlas.source_registry.v1", "sources": sources}), encoding="utf-8")
    return path


def make_config(tmp_path: Path, registry: Path) -> RuntimeConfig:
    client = tmp_path / "private_db_client.py"
    client.write_text("print('fixture')\n", encoding="utf-8")
    return RuntimeConfig(
        r2_endpoint="https://fixture.r2.cloudflarestorage.com",
        r2_access_key_id="fixture-access",
        r2_secret_access_key="fixture-secret",
        r2_bucket="existing-owner-bucket",
        r2_primary_prefix="primary-objects/memory-atlas/",
        r2_backup_prefix="backups/private-database/memory-atlas/",
        private_db_client=client,
        runtime_dir=tmp_path / "runtime",
        work_dir=tmp_path / "work",
        web_data_dir=tmp_path / "web",
        source_registry=registry,
        public_atlas_snapshot=None,
        external_origin="https://memoryatlas.example.test",
        source_host_id="fixture-mac",
    )


def write_failure_registry(path: Path, *, generated_at: str = FIXED_TIME) -> Path:
    payload = {
        "schema_version": "memory_atlas.failure_asset_registry.v1",
        "generated_at": generated_at,
        "assets": [{
            "id": "FIXTURE-ONE",
            "component": "memory-atlas-fixture",
            "category": "regression",
            "severity": "P0",
            "error_code": "FIXTURE_ONE",
            "title": "fixture failure",
            "root_cause": "fixture root cause",
            "occurred_at": "2026-08-01T00:00:00Z",
            "evidence_ref": "sha256://red-source",
            "environment": "sealed-taskpack",
            "details": {"source": "frozen"},
            "fixture_path": "taskpack://fixtures/failure_compound_cases.json#FIXTURE-ONE",
            "oracle": "fixture must remain blocked",
            "test_path": "test_fixture_one",
            "red_evidence_ref": "sha256://red",
            "green_evidence_ref": "sha256://green",
            "fixed_by": "git:fixture",
            "fault_injection": {
                "injected_at": generated_at,
                "expected": "PASS",
                "observed": "PASS",
                "evidence_ref": "sha256://green",
            },
        }],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    path.chmod(0o600)
    return path


def env_for_config(tmp_path: Path, registry: Path) -> dict[str, str]:
    client = tmp_path / "client.py"
    client.write_text("print('fixture')\n", encoding="utf-8")
    return {
        "MEMORY_ATLAS_R2_ENDPOINT": "https://fixture.r2.cloudflarestorage.com",
        "MEMORY_ATLAS_R2_ACCESS_KEY_ID": "access",
        "MEMORY_ATLAS_R2_SECRET_ACCESS_KEY": "secret",
        "MEMORY_ATLAS_R2_BUCKET": "exact-existing-bucket",
        "MEMORY_ATLAS_R2_PRIMARY_PREFIX": "primary-objects/memory-atlas",
        "MEMORY_ATLAS_R2_BACKUP_PREFIX": "backups/private-database/memory-atlas",
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT": str(client),
        "MEMORY_ATLAS_RUNTIME_DIR": str(tmp_path / "runtime"),
        "MEMORY_ATLAS_WORK_DIR": str(tmp_path / "work"),
        "MEMORY_ATLAS_WEB_DATA_DIR": str(tmp_path / "web"),
        "MEMORY_ATLAS_SOURCE_REGISTRY": str(registry),
        "MEMORY_ATLAS_EXTERNAL_ORIGIN": "https://memoryatlas.example.test",
        "MEMORY_ATLAS_SOURCE_HOST_ID": "fixture-mac",
    }


def event(index: int, *, outcome: str = "unverified", activity: str = "research_diagnosis", effort: float | None = None) -> NormalizedEvent:
    return NormalizedEvent(
        event_id=f"evt-{index}", source_id="fixture", object_sha256=f"sha-{index}", relative_path=f"p/{index}.json",
        occurred_at=FIXED_TIME, record_type="fixture", project="MemoryAtlas", activity=activity,
        augmentation_mode="augmentation", outcome_state=outcome, effort_minutes=effort,
        evidence_ref=f"fixture://{index}", payload={"index": index},
    )


def verified_payload(outcome_state: str = "deployed_verified") -> dict[str, object]:
    return {
        "project": "MemoryAtlas",
        "activity": "verification_repair",
        "outcome_state": outcome_state,
        "effort_minutes": 30,
        "verification": {
            "schema_version": "memory_atlas.verification.v1",
            "kind": "evidence_adapter_result",
            "status": "PASS",
            "subject_ref": "deployment://memory-atlas/release-fixture",
            "evidence_refs": [{"uri": "probe://run-1", "sha256": "a" * 64}],
            "verifier": "post-promote-probe",
            "oracle": "authenticated-user-path-and-world-state",
        },
    }


def test_hashing_is_stable() -> None:
    assert sha256_bytes(b"abc") == "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    assert stable_id("a", "b") == stable_id("a", "b")
    assert stable_id("a", "b") != stable_id("b", "a")


def test_config_rejects_candidate_default_bucket(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "x", "label_zh": "x", "kind": "file", "required": False}])
    values = env_for_config(tmp_path, registry)
    values["MEMORY_ATLAS_R2_BUCKET"] = "memory-atlas-private"
    with pytest.raises(ConfigurationError, match="禁止使用候选默认名"):
        RuntimeConfig.from_env(values)


def test_config_rejects_wrong_primary_prefix(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "x", "label_zh": "x", "kind": "file", "required": False}])
    values = env_for_config(tmp_path, registry)
    values["MEMORY_ATLAS_R2_PRIMARY_PREFIX"] = "other/memory-atlas"
    with pytest.raises(ConfigurationError, match="primary-objects"):
        RuntimeConfig.from_env(values)


def test_config_rejects_same_prefixes(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "x", "label_zh": "x", "kind": "file", "required": False}])
    values = env_for_config(tmp_path, registry)
    values["MEMORY_ATLAS_R2_BACKUP_PREFIX"] = values["MEMORY_ATLAS_R2_PRIMARY_PREFIX"]
    with pytest.raises(ConfigurationError, match="不同前缀"):
        RuntimeConfig.from_env(values)


def test_config_accepts_exact_existing_scope(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "x", "label_zh": "x", "kind": "file", "required": False}])
    config = RuntimeConfig.from_env(env_for_config(tmp_path, registry))
    assert config.r2_bucket == "exact-existing-bucket"
    assert config.r2_primary_prefix == "primary-objects/memory-atlas/"
    assert config.r2_backup_prefix == "backups/private-database/memory-atlas/"


def test_local_object_store_create_unchanged_and_repair(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    source = tmp_path / "source.bin"
    source.write_bytes(b"canonical")
    digest = sha256_file(source)
    first = store.put_file("a/object", source, digest)
    second = store.put_file("a/object", source, digest)
    (tmp_path / "objects/a/object").write_bytes(b"corrupt")
    third = store.put_file("a/object", source, digest)
    assert [first.operation, second.operation, third.operation] == ["created", "unchanged", "repaired"]
    assert third.readback_verified is True


def test_local_object_preflight_never_creates_bucket(tmp_path: Path) -> None:
    result = LocalObjectStore(tmp_path / "objects").preflight()
    assert result == {"state": "PASS", "readback_equal": True, "bucket_creation_attempted": False}


def test_r2_adapter_source_contains_no_create_bucket() -> None:
    import OpenAIDatabase.scripts.memory_atlas_private.object_store as module
    source = Path(module.__file__).read_text(encoding="utf-8")
    forbidden = "create" + "_bucket"
    assert forbidden not in source


def test_sqlite_snapshot_is_consistent(tmp_path: Path) -> None:
    source = tmp_path / "source.sqlite3"
    with sqlite3.connect(source) as db:
        db.execute("CREATE TABLE sample(id INTEGER PRIMARY KEY, value TEXT)")
        db.executemany("INSERT INTO sample(value) VALUES (?)", [("a",), ("b",)])
        db.commit()
    destination = tmp_path / "snapshot.sqlite3"
    digest, size = create_consistent_snapshot(source, destination)
    assert size > 0 and digest == sha256_file(destination)
    with sqlite3.connect(destination) as db:
        assert db.execute("SELECT COUNT(*) FROM sample").fetchone()[0] == 2


def test_registry_duplicate_source_id_is_rejected(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [
        {"source_id": "x", "label_zh": "x", "kind": "file", "required": False},
        {"source_id": "x", "label_zh": "y", "kind": "file", "required": False},
    ])
    with pytest.raises(InventoryError, match="重复 source_id"):
        load_source_registry(registry, {})


def test_inventory_missing_required_is_explicit(tmp_path: Path) -> None:
    registry = write_registry(tmp_path / "registry.json", [{
        "source_id": "required", "label_zh": "必需", "kind": "file", "required": True, "env_var": "REQUIRED_PATH"
    }])
    resolved = load_source_registry(registry, {})
    records, coverages = discover_inventory(resolved, tmp_path / "snapshots")
    assert records == []
    assert coverages[0].state == SourceState.MISSING_REQUIRED


def test_inventory_materializes_live_file_before_later_mutation(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    live = root / "live.jsonl"
    live.write_text('{"event":1}\n', encoding="utf-8")
    registry = write_registry(tmp_path / "registry.json", [{
        "source_id": "live", "label_zh": "live", "kind": "files", "required": True,
        "env_var": "SOURCE_PATH", "include_globs": ["**/*", "*"],
    }])
    records, coverages = discover_inventory(
        load_source_registry(registry, {"SOURCE_PATH": str(root)}),
        tmp_path / "snapshots",
    )
    assert coverages[0].state == SourceState.READY
    assert len(records) == 1 and records[0].snapshot_created is True
    materialized = Path(records[0].materialized_path)
    live.write_text('{"event":1}\n{"event":2}\n', encoding="utf-8")
    assert materialized.read_text(encoding="utf-8") == '{"event":1}\n'
    assert sha256_file(materialized) == records[0].sha256
    receipt = LocalObjectStore(tmp_path / "objects").put_file(
        "live/object",
        materialized,
        records[0].sha256,
    )
    assert receipt.readback_verified is True


def test_inventory_recursive_glob_includes_root_files_and_skips_only_denied_sibling(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "root.json").write_text('{"safe":1}', encoding="utf-8")
    (root / "token.txt").write_text("excluded configuration secret", encoding="utf-8")
    nested = root / "nested"
    nested.mkdir()
    (nested / "child.json").write_text('{"safe":2}', encoding="utf-8")
    registry = write_registry(tmp_path / "registry.json", [{
        "source_id": "source", "label_zh": "source", "kind": "files", "required": False,
        "env_var": "SOURCE_PATH", "include_globs": ["**/*"],
    }])
    records, coverages = discover_inventory(
        load_source_registry(registry, {"SOURCE_PATH": str(root)}),
        tmp_path / "snapshots",
    )
    assert coverages[0].state == SourceState.UNREADABLE
    assert {row.relative_path for row in records} == {"root.json", "nested/child.json"}
    assert all("token.txt" not in row.relative_path for row in records)


def test_inventory_rejects_standalone_credential_but_not_embedded_text(tmp_path: Path) -> None:
    root = tmp_path / "source"
    root.mkdir()
    (root / "token.txt").write_text("credential", encoding="utf-8")
    (root / "conversation.txt").write_text("user pasted token=abc inside conversation", encoding="utf-8")
    registry = write_registry(tmp_path / "registry.json", [{
        "source_id": "x", "label_zh": "x", "kind": "text", "required": True,
        "env_var": "SOURCE_PATH", "include_globs": ["**/*", "*"],
    }])
    resolved = load_source_registry(registry, {"SOURCE_PATH": str(root)})
    records, coverages = discover_inventory(resolved, tmp_path / "snapshots")
    assert coverages[0].state == SourceState.UNREADABLE
    # Narrowly selecting the conversation proves embedded bytes are preserved.
    registry = write_registry(tmp_path / "registry2.json", [{
        "source_id": "x", "label_zh": "x", "kind": "text", "required": True,
        "env_var": "SOURCE_PATH", "include_globs": ["conversation.txt"],
    }])
    records, coverages = discover_inventory(load_source_registry(registry, {"SOURCE_PATH": str(root)}), tmp_path / "snapshots2")
    assert coverages[0].state == SourceState.READY
    normalized = list(normalize_record(records[0]))
    assert normalized[0].payload["text"] == "user pasted token=abc inside conversation"


def test_normalize_jsonl_emits_each_record(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"
    path.write_text('{"project":"A","outcome_state":"deployed_verified"}\nnot-json\n', encoding="utf-8")
    record = InventoryRecord("src", str(tmp_path), path.name, str(path), "jsonl", path.stat().st_size, path.stat().st_mtime_ns, sha256_file(path), sha256_file(path), False)
    rows = list(normalize_record(record))
    assert len(rows) == 2
    assert rows[0].project == "A"
    assert rows[0].outcome_state == "claimed_deployed"
    assert rows[1].payload == {"text": "not-json"}


def test_normalize_large_binary_emits_metadata_only(tmp_path: Path) -> None:
    path = tmp_path / "image.bin"
    path.write_bytes(b"abc")
    record = InventoryRecord("src", str(tmp_path), path.name, str(path), "binary", 3, path.stat().st_mtime_ns, sha256_file(path), sha256_file(path), False)
    row = list(normalize_record(record))[0]
    assert row.record_type == "object_metadata"
    assert row.payload["content_ref"].startswith("r2://sha256/")


def test_failure_signature_normalizes_variable_numbers() -> None:
    assert failure_signature("backup", "io", "E1", "failed at 123") == failure_signature("backup", "io", "E1", "failed at 456")


def test_incident_deduplicates_and_counts_recurrence(tmp_path: Path) -> None:
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    one = store.record_failure(component="backup", category="automation", severity="P0", error_code="E1", title="stream failed 123", occurred_at="2026-08-01T00:00:00Z", evidence_ref="e://1", environment="mac")
    same_occurrence = store.record_failure(component="backup", category="automation", severity="P0", error_code="E1", title="stream failed 456", occurred_at="2026-08-01T00:00:00Z", evidence_ref="e://1", environment="mac")
    recurrence = store.record_failure(component="backup", category="automation", severity="P0", error_code="E1", title="stream failed 789", occurred_at="2026-08-02T00:00:00Z", evidence_ref="e://2", environment="mac")
    assert one.created is True
    assert same_occurrence.recurrence_count == 1
    assert recurrence.incident_id == one.incident_id and recurrence.recurrence_count == 2


def test_closed_incident_carries_rollback_reference(tmp_path: Path) -> None:
    """AC-015 lists rollback among the elements a closed incident must carry.

    The live ledger had 29/29 closed incidents with evidence, signature, fixture,
    oracle, red proof, green proof, fix reference and monitoring, but 0/29 with a
    rollback reference, because the column did not exist. It is additive with an
    empty default, so this pins both halves: a rollback survives closure, and the
    snapshot counts the ones that still lack one instead of reading as satisfied.
    """
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    with_rb = store.record_failure(component="deploy", category="release", severity="P0", error_code="E9", title="promotion left origin stale", occurred_at=FIXED_TIME, evidence_ref="e://rb", environment="ovh")
    store.promote_regression_asset(
        incident_id=with_rb.incident_id, fixture_path="fixtures/deploy.json", oracle="origin must serve the promoted release",
        test_path="tests/deploy.py", red_evidence_ref="red://rb", green_evidence_ref="green://rb",
        fixed_by="sha:deadbeef", rollback_ref="ops/memory-atlas/rollback.sh#previous-symlink",
    )
    without_rb = store.record_failure(component="ui", category="frontend", severity="P1", error_code="E8", title="theme lost on reload", occurred_at=FIXED_TIME, evidence_ref="e://no", environment="test")
    store.promote_regression_asset(
        incident_id=without_rb.incident_id, fixture_path="fixtures/theme.json", oracle="theme persists",
        test_path="tests/theme.py", red_evidence_ref="red://no", green_evidence_ref="green://no", fixed_by="sha:cafe",
    )

    snapshot = store.export_snapshot(FIXED_TIME)
    rows = {row["incident_id"]: row for row in snapshot["incidents"]}
    assert rows[with_rb.incident_id]["rollback_ref"] == "ops/memory-atlas/rollback.sh#previous-symlink"
    assert rows[without_rb.incident_id]["rollback_ref"] == ""
    metrics = snapshot["metrics"]
    assert metrics["closed_incident_count"] == 2
    assert metrics["closed_incidents_with_rollback"] == 1
    assert metrics["closed_incidents_missing_rollback"] == 1


def test_recurrence_of_a_closed_signature_reopens_and_increments(tmp_path: Path) -> None:
    """The increment path exists in code but has never fired in production: all 29
    live incidents sit at recurrence_count 1. Pin it so a real recurrence cannot
    silently fail to reopen the incident."""
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    first = store.record_failure(component="capture", category="source", severity="P0", error_code="E7", title="upload timed out after 30 seconds", occurred_at="2026-08-01T00:00:00Z", evidence_ref="e://1", environment="mac")
    store.promote_regression_asset(
        incident_id=first.incident_id, fixture_path="fixtures/capture.json", oracle="upload retries",
        test_path="tests/capture.py", red_evidence_ref="red://1", green_evidence_ref="green://1",
        fixed_by="sha:1", rollback_ref="revert sha:1",
    )
    again = store.record_failure(component="capture", category="source", severity="P0", error_code="E7", title="upload timed out after 90 seconds", occurred_at="2026-08-05T00:00:00Z", evidence_ref="e://2", environment="mac")

    assert again.incident_id == first.incident_id, "same normalized signature must reuse the incident"
    assert again.recurrence_count == 2
    row = next(r for r in store.export_snapshot(FIXED_TIME)["incidents"] if r["incident_id"] == first.incident_id)
    assert row["status"] == "REOPENED"
    assert row["rollback_ref"] == "revert sha:1", "reopening must not discard the rollback reference"


def test_failure_store_migrates_live_v1_schema_without_losing_incidents(tmp_path: Path) -> None:
    database = tmp_path / "failure.sqlite3"
    with sqlite3.connect(database) as db:
        db.execute(
            """
            CREATE TABLE incidents (
                incident_id TEXT PRIMARY KEY,
                signature TEXT NOT NULL UNIQUE,
                component TEXT NOT NULL,
                category TEXT NOT NULL,
                severity TEXT NOT NULL,
                title TEXT NOT NULL,
                root_cause TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'OPEN',
                first_seen TEXT NOT NULL,
                last_seen TEXT NOT NULL,
                recurrence_count INTEGER NOT NULL DEFAULT 1,
                regression_asset_id TEXT,
                fixed_by TEXT NOT NULL DEFAULT '',
                closure_evidence_json TEXT NOT NULL DEFAULT '[]'
            )
            """
        )
        db.execute(
            """
            INSERT INTO incidents
            (incident_id, signature, component, category, severity, title, first_seen, last_seen)
            VALUES ('inc_old', 'sig_old', 'legacy', 'runtime', 'P0', 'preserve me', ?, ?)
            """,
            (FIXED_TIME, FIXED_TIME),
        )
    snapshot = FailureCompoundStore(database).export_snapshot(FIXED_TIME)
    assert snapshot["metrics"]["incident_count"] == 1
    assert snapshot["incidents"][0]["incident_id"] == "inc_old"
    assert snapshot["incidents"][0]["error_code"] == ""


def test_regression_asset_requires_red_and_green_evidence(tmp_path: Path) -> None:
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    incident = store.record_failure(component="x", category="y", severity="P1", error_code="E", title="z", occurred_at=FIXED_TIME, evidence_ref="e://1", environment="test")
    with pytest.raises(FailureCompoundError):
        store.promote_regression_asset(incident_id=incident.incident_id, fixture_path="f", oracle="o", test_path="t", red_evidence_ref="", green_evidence_ref="g", fixed_by="commit")


def test_fault_injection_updates_compound_score(tmp_path: Path) -> None:
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    incident = store.record_failure(component="x", category="y", severity="P1", error_code="E", title="z", occurred_at=FIXED_TIME, evidence_ref="e://1", environment="test")
    asset = store.promote_regression_asset(incident_id=incident.incident_id, fixture_path="fixtures/x.json", oracle="must block", test_path="tests/x.py", red_evidence_ref="red://1", green_evidence_ref="green://1", fixed_by="sha:abc")
    assert store.record_fault_injection(asset_id=asset, injected_at=FIXED_TIME, expected="BLOCKED", observed="BLOCKED", evidence_ref="inject://1") == "PASS"
    snapshot = store.export_snapshot(FIXED_TIME)
    assert snapshot["compound_score"] == 100
    assert snapshot["metrics"]["blocked_recurrences"] == 1


def test_fault_injection_and_registry_import_are_idempotent(tmp_path: Path) -> None:
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    registry = write_failure_registry(tmp_path / "failure-assets.json")
    first = store.import_asset_registry(registry)
    second = store.import_asset_registry(registry)
    snapshot = store.export_snapshot(FIXED_TIME)
    assert first["state"] == "PASS" and first["incidents_created"] == 1
    assert second["state"] == "PASS" and second["incidents_created"] == 0
    assert snapshot["metrics"] == {
        "incident_count": 1,
        "active_regression_assets": 1,
        "passing_regression_assets": 1,
        "historical_recurrences": 0,
        "blocked_recurrences": 1,
        "asset_coverage": 1.0,
        "last_pass_rate": 1.0,
        "nonrecurrence_ratio": 1.0,
        # AC-015 rollback coverage: this fixture registry carries no rollback_ref,
        # so the shortfall has to be visible rather than absent.
        "closed_incident_count": 1,
        "closed_incidents_with_rollback": 0,
        "closed_incidents_missing_rollback": 1,
    }
    assert snapshot["incidents"][0]["error_code"] == "FIXTURE_ONE"
    assert snapshot["incidents"][0]["root_cause"] == "fixture root cause"


def test_failure_registry_requires_protected_regular_file(tmp_path: Path) -> None:
    registry = write_failure_registry(tmp_path / "failure-assets.json")
    registry.chmod(0o644)
    with pytest.raises(FailureCompoundError, match="0600"):
        FailureCompoundStore(tmp_path / "failure.sqlite3").import_asset_registry(registry)


def test_failure_registry_validates_every_asset_before_first_write(tmp_path: Path) -> None:
    registry = write_failure_registry(tmp_path / "failure-assets.json")
    payload = json.loads(registry.read_text(encoding="utf-8"))
    bad = dict(payload["assets"][0])
    bad["id"] = "FIXTURE-TWO"
    bad["oracle"] = ""
    payload["assets"].append(bad)
    registry.write_text(json.dumps(payload), encoding="utf-8")
    registry.chmod(0o600)
    store = FailureCompoundStore(tmp_path / "failure.sqlite3")
    with pytest.raises(FailureCompoundError, match="oracle"):
        store.import_asset_registry(registry)
    assert store.export_snapshot(FIXED_TIME)["metrics"]["incident_count"] == 0


def test_raw_success_claim_does_not_enter_verified_outcome_numerator(tmp_path: Path) -> None:
    path = tmp_path / "claim.json"
    path.write_text('{"outcome_state":"deployed_verified","message":"上线成功"}', encoding="utf-8")
    record = InventoryRecord(
        source_id="claim", source_root=str(tmp_path), relative_path="claim.json",
        materialized_path=str(path), kind="json", size_bytes=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns, sha256=sha256_file(path),
        original_sha256=sha256_file(path), snapshot_created=False,
    )
    rows = list(normalize_record(record))
    assert rows[0].outcome_state == "claimed_deployed"
    analytics = build_behavior_analytics(rows, generated_at=FIXED_TIME)
    assert analytics["verified_outcome_rate"]["value"] == 0.0


def test_structured_evidence_adapter_can_verify_outcome(tmp_path: Path) -> None:
    path = tmp_path / "verified.json"
    path.write_text(json.dumps(verified_payload()), encoding="utf-8")
    record = InventoryRecord(
        source_id="verified", source_root=str(tmp_path), relative_path="verified.json",
        materialized_path=str(path), kind="evidence_adapter", size_bytes=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns, sha256=sha256_file(path),
        original_sha256=sha256_file(path), snapshot_created=False,
    )
    rows = list(normalize_record(record))
    assert rows[0].outcome_state == "deployed_verified"
    assert build_behavior_analytics(rows, generated_at=FIXED_TIME)["verified_outcome_rate"]["value"] == 1.0


def test_spoofed_verification_envelope_from_raw_source_is_not_trusted(tmp_path: Path) -> None:
    path = tmp_path / "spoofed.json"
    path.write_text(json.dumps(verified_payload()), encoding="utf-8")
    record = InventoryRecord(
        source_id="raw-conversation", source_root=str(tmp_path), relative_path="spoofed.json",
        materialized_path=str(path), kind="json", size_bytes=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns, sha256=sha256_file(path),
        original_sha256=sha256_file(path), snapshot_created=False,
    )
    rows = list(normalize_record(record))
    assert rows[0].outcome_state == "claimed_deployed"
    assert build_behavior_analytics(rows, generated_at=FIXED_TIME)["verified_outcome_rate"]["value"] == 0.0


def test_evidence_adapter_requires_immutable_hashed_evidence_refs(tmp_path: Path) -> None:
    payload = verified_payload()
    payload["verification"]["evidence_refs"] = [{"uri": "probe://run-1"}]  # type: ignore[index]
    path = tmp_path / "weak-evidence.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    record = InventoryRecord(
        source_id="verified", source_root=str(tmp_path), relative_path="weak-evidence.json",
        materialized_path=str(path), kind="evidence_adapter", size_bytes=path.stat().st_size,
        mtime_ns=path.stat().st_mtime_ns, sha256=sha256_file(path),
        original_sha256=sha256_file(path), snapshot_created=False,
    )
    rows = list(normalize_record(record))
    assert rows[0].outcome_state == "claimed_deployed"


def test_behavior_analytics_uses_effort_when_available() -> None:
    analytics = build_behavior_analytics([
        event(1, outcome="deployed_verified", effort=40),
        event(2, outcome="unverified", effort=60),
    ], generated_at=FIXED_TIME)
    assert analytics["verified_outcome_rate"]["value"] == 0.4
    assert analytics["verified_outcome_rate"]["denominator_type"] == "effort_minutes"


def test_behavior_analytics_falls_back_to_event_count() -> None:
    analytics = build_behavior_analytics([event(1, outcome="restore_verified"), event(2)], generated_at=FIXED_TIME)
    assert analytics["verified_outcome_rate"]["value"] == 0.5
    assert analytics["verified_outcome_rate"]["denominator_type"] == "event_count"


def test_behavior_analytics_does_not_duplicate_normalized_event_payloads() -> None:
    analytics = build_behavior_analytics([
        event(index) for index in range(100)
    ], generated_at=FIXED_TIME)
    assert analytics["event_count"] == 100
    assert "events" not in analytics


def test_behavior_analytics_consumes_events_with_bounded_retention() -> None:
    refs: list[weakref.ReferenceType[NormalizedEvent]] = []

    def rows():
        for index in range(64):
            assert sum(ref() is not None for ref in refs) <= 2
            row = event(index)
            row.payload["blob"] = "x" * 4096
            refs.append(weakref.ref(row))
            yield row

    analytics = build_behavior_analytics(rows(), generated_at=FIXED_TIME)
    assert analytics["event_count"] == 64


def test_remote_reconcile_streams_normalized_event_batch() -> None:
    repo = Path(__file__).resolve().parents[2]
    pipeline = (
        repo / "OpenAIDatabase/scripts/memory_atlas_private/pipeline.py"
    ).read_text(encoding="utf-8")
    assert "def _iter_events(path: Path)" in pipeline
    assert 'with path.open("r", encoding="utf-8") as handle:' in pipeline
    assert "build_behavior_analytics(_iter_events(temporary)" in pipeline
    remote_section = pipeline.split("class RemoteReconcilePipeline:", maxsplit=1)[1]
    assert "_load_events(temporary)" not in remote_section


def test_benchmark_mismatch_never_generates_percentile() -> None:
    personal = {"value": 5, "comparison_contract": {"taxonomy_version": "v1", "unit": "hours", "window_days": 30, "population_scope": "personal"}}
    benchmark = {"distribution": list(range(40)), "comparison_contract": {"taxonomy_version": "v2", "unit": "hours", "window_days": 30, "population_scope": "personal", "sample_size": 40}}
    result = compare_with_benchmark(personal, benchmark)
    assert result["state"] == "DIRECTION_ONLY" and result["percentile"] is None


def test_benchmark_same_contract_can_generate_scoped_percentile() -> None:
    contract = {"taxonomy_version": "v1", "unit": "hours", "window_days": 30, "population_scope": "sample", "sample_size": 40}
    result = compare_with_benchmark({"value": 20, "comparison_contract": contract}, {"distribution": list(range(40)), "comparison_contract": contract})
    assert result["state"] == "COMPARABLE"
    assert 0 <= result["percentile"] <= 100


def test_recommendations_are_evidence_bound_and_capped() -> None:
    analytics = build_behavior_analytics([event(i, activity="research_diagnosis") for i in range(10)], generated_at=FIXED_TIME)
    failure = {"metrics": {"historical_recurrences": 4, "blocked_recurrences": 0}}
    rows = build_habit_recommendations(analytics, failure)
    assert len(rows) <= 3
    assert all(row["fact"] and row["alternative_explanation"] and row["rollback"] for row in rows)


def test_private_database_path_is_confined(tmp_path: Path) -> None:
    db = LocalPrivateDatabase(tmp_path / "private")
    db.put_json("memory-atlas/a.json", {"ok": True}, "test")
    assert db.get_json("memory-atlas/a.json") == {"ok": True}
    with pytest.raises(PrivateDatabaseError):
        db.put_json("other/a.json", {"bad": True}, "test")


class FailOnceDatabase(LocalPrivateDatabase):
    def __init__(self, root: Path):
        super().__init__(root)
        self.calls = 0
    def put_json(self, relpath: str, value: dict[str, object], message: str) -> str:
        self.calls += 1
        if self.calls == 1:
            raise RuntimeError("temporary")
        return super().put_json(relpath, value, message)


def test_fact_outbox_retries_without_losing_payload(tmp_path: Path) -> None:
    outbox = FactOutbox(tmp_path / "outbox.sqlite3")
    backend = FailOnceDatabase(tmp_path / "private")
    outbox.enqueue("memory-atlas/fact.json", {"value": 1}, "test", FIXED_TIME)
    assert outbox.flush(backend, FIXED_TIME)["failed"] == 1
    assert outbox.pending_count() == 1
    assert outbox.flush(backend, FIXED_TIME)["completed"] == 1
    assert backend.get_json("memory-atlas/fact.json")["value"] == 1


def test_fact_outbox_supersedes_stale_pending_payload_for_same_latest_path(tmp_path: Path) -> None:
    outbox = FactOutbox(tmp_path / "outbox.sqlite3")
    backend = LocalPrivateDatabase(tmp_path / "private")
    relpath = "memory-atlas/analytics/latest.json"
    outbox.enqueue(relpath, {"version": 1}, "old", FIXED_TIME)
    outbox.enqueue(relpath, {"version": 2}, "new", "2026-08-02T00:01:00+00:00")
    result = outbox.flush(backend, "2026-08-02T00:01:00+00:00")
    assert result == {"completed": 1, "failed": 0, "remaining": 0}
    assert backend.get_json(relpath)["version"] == 2
    with sqlite3.connect(outbox.path) as db:
        assert db.execute("SELECT COUNT(*) FROM fact_outbox WHERE state='SUPERSEDED'").fetchone()[0] == 1


def test_action_queue_is_idempotent_and_capture_is_not_false_success(tmp_path: Path) -> None:
    queue = ActionQueue(tmp_path / "actions.sqlite3")
    first = queue.enqueue("capture_request", "same", FIXED_TIME)
    second = queue.enqueue("capture_request", "same", FIXED_TIME)
    assert first.request_id == second.request_id
    assert first.state == "WAITING_SOURCE" and first.source_required is True
    assert "尚未完成" in first.message_zh


def test_isolated_restore_verifies_every_hash(tmp_path: Path) -> None:
    store = LocalObjectStore(tmp_path / "objects")
    source = tmp_path / "source"
    source.write_bytes(b"restore-me")
    digest = sha256_file(source)
    receipt = store.put_file("objects/a", source, digest)
    private = LocalPrivateDatabase(tmp_path / "private")
    private.put_json("memory-atlas/runs/manifest.json", {"objects": [asdict(receipt)]}, "manifest")
    result = isolated_restore(manifest_path="memory-atlas/runs/manifest.json", destination=tmp_path / "restore", object_store=store, private_db=private)
    assert result["state"] == "PASS"
    assert result["restored_objects"] == 1 and result["all_hashes_match"] is True


def test_isolated_restore_rejects_nonempty_destination(tmp_path: Path) -> None:
    destination = tmp_path / "restore"
    destination.mkdir()
    (destination / "existing").write_text("x")
    with pytest.raises(RestoreError, match="必须为空"):
        isolated_restore(manifest_path="memory-atlas/x.json", destination=destination, object_store=LocalObjectStore(tmp_path / "objects"), private_db=LocalPrivateDatabase(tmp_path / "private"))


def test_capture_pipeline_waits_when_required_source_is_missing(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "required", "label_zh": "必需", "kind": "file", "required": True, "env_var": "MISSING_REQUIRED_PATH"}])
    monkeypatch.delenv("MISSING_REQUIRED_PATH", raising=False)
    config = make_config(tmp_path, registry)
    result = CapturePipeline(config, LocalObjectStore(tmp_path / "objects"), LocalPrivateDatabase(tmp_path / "private"), clock=lambda: FIXED_TIME).run()
    assert result["state"] == "WAITING_SOURCE"
    assert LocalPrivateDatabase(tmp_path / "private").get_json("memory-atlas/runs/latest.json")["state"] == "WAITING_SOURCE"


def test_capture_and_remote_reconcile_end_to_end(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "event.json").write_text(json.dumps(verified_payload()), encoding="utf-8")
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "source", "label_zh": "来源", "kind": "evidence_adapter", "required": True, "env_var": "SOURCE_PATH", "include_globs": ["*", "**/*"]}])
    monkeypatch.setenv("SOURCE_PATH", str(source))
    config = make_config(tmp_path, registry)
    store = LocalObjectStore(tmp_path / "objects")
    private = LocalPrivateDatabase(tmp_path / "private")
    capture = CapturePipeline(config, store, private, clock=lambda: FIXED_TIME).run()
    assert capture["state"] == "SUCCEEDED" and capture["objects"] >= 2
    analytics = private.get_json("memory-atlas/analytics/latest.json")
    assert analytics["verified_outcome_rate"]["value"] == 1.0
    assert analytics["normalized_event_batch"]["readback_verified"] is True
    assert "events" not in analytics
    rebuilt = RemoteReconcilePipeline(config, store, private, clock=lambda: FIXED_TIME).run()
    assert rebuilt["state"] == "PASS"
    snapshot = json.loads((config.web_data_dir / "memory_atlas_private_analytics.json").read_text(encoding="utf-8"))
    assert snapshot["run"]["state"] == "REBUILT_FROM_AUTHORITIES"
    assert snapshot["run"]["objects"]
    status = json.loads((config.web_data_dir / "memory_atlas_status_projection.json").read_text(encoding="utf-8"))
    assert status["state"] == "PASS"
    assert status["authority"]["this_document"] == "read_only_projection_not_authority"
    assert status["private_content_included"] is False


def test_remote_reconcile_registers_status_and_persists_failure_assets(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "event.json").write_text(json.dumps(verified_payload()), encoding="utf-8")
    source_registry = write_registry(
        tmp_path / "registry.json",
        [{
            "source_id": "source",
            "label_zh": "来源",
            "kind": "evidence_adapter",
            "required": True,
            "env_var": "SOURCE_PATH",
            "include_globs": ["*"],
        }],
    )
    monkeypatch.setenv("SOURCE_PATH", str(source))
    base_config = make_config(tmp_path, source_registry)
    store = LocalObjectStore(tmp_path / "objects")
    private = LocalPrivateDatabase(tmp_path / "private")
    CapturePipeline(base_config, store, private, clock=lambda: FIXED_TIME).run()
    status_dir = tmp_path / "status-data"
    status_dir.mkdir()
    failure_registry = write_failure_registry(tmp_path / "failure-assets.json")
    config = replace(
        base_config,
        failure_asset_registry=failure_registry,
        status_projection_target=status_dir / "memory_atlas_status_projection.json",
    )
    result = RemoteReconcilePipeline(config, store, private, clock=lambda: FIXED_TIME).run()
    assert result["state"] == "PASS"
    assert result["failure_asset_import"]["assets_imported"] == 1
    assert result["failure_outbox"]["failed"] == 0
    assert result["status_registration"]["state"] == "PASS"
    assert result["status_registration"]["readback_verified"] is True
    assert result["status_registration"]["mode"] == "0644"
    assert config.status_projection_target.read_bytes() == (
        config.web_data_dir / "memory_atlas_status_projection.json"
    ).read_bytes()
    persisted = private.get_json("memory-atlas/failure-compound/latest.json")
    assert persisted["metrics"]["incident_count"] == 1
    assert persisted["metrics"]["active_regression_assets"] == 1
    assert persisted["metrics"]["blocked_recurrences"] == 1


def test_status_projection_excludes_raw_private_content() -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.status_projection import build_status_projection

    private_snapshot = {
        "schema_version": "memory_atlas.private_analytics.v1",
        "generated_at": FIXED_TIME,
        "run": {
            "run_id": "run-1",
            "state": "REBUILT_FROM_AUTHORITIES",
            "source_completed_at": FIXED_TIME,
            "source_coverages": [{"source_id": "codex", "state": "COMPLETE"}],
            "objects": [{"object_key": "private/secret", "sha256": "a" * 64}],
        },
        "behavior_economics": {
            "event_count": 1,
            "events": [{"raw_text": "private conversation bytes"}],
            "verified_outcome_rate": {"value": 1.0, "state": "MEASURED"},
            "recommendations": [{"fact": "private fact"}],
        },
        "failure_compound": {
            "compound_score": 82,
            "metrics": {"incident_count": 1, "active_regression_assets": 1, "historical_recurrences": 2, "blocked_recurrences": 3},
            "incidents": [{"title": "private incident title", "details": "secret"}],
        },
    }
    projection = build_status_projection(private_snapshot)
    encoded = json.dumps(projection, ensure_ascii=False, sort_keys=True)
    assert projection["state"] == "PASS"
    assert projection["object_count"] == 1
    assert projection["private_content_included"] is False
    for forbidden in ("private conversation bytes", "private incident title", "private/secret", "raw_text", "sha256"):
        assert forbidden not in encoded


def test_remote_reconcile_fails_closed_on_corrupt_object(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = tmp_path / "source"
    source.mkdir()
    (source / "event.json").write_text(json.dumps(verified_payload("restore_verified")), encoding="utf-8")
    registry = write_registry(tmp_path / "registry.json", [{"source_id": "source", "label_zh": "来源", "kind": "json", "required": True, "env_var": "SOURCE_PATH", "include_globs": ["*"]}])
    monkeypatch.setenv("SOURCE_PATH", str(source))
    config = make_config(tmp_path, registry)
    store = LocalObjectStore(tmp_path / "objects")
    private = LocalPrivateDatabase(tmp_path / "private")
    CapturePipeline(config, store, private, clock=lambda: FIXED_TIME).run()
    target = next(path for path in (tmp_path / "objects").rglob("*") if path.is_file() and "preflight" not in str(path))
    target.write_bytes(b"corrupt")
    result = RemoteReconcilePipeline(config, store, private, clock=lambda: FIXED_TIME).run()
    assert result["state"] == "FAILED"
    assert result["missing_or_corrupt_objects"]


def test_cloudflare_access_verifier_checks_signature_issuer_audience_and_expiry() -> None:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    now = datetime.now(timezone.utc)
    claims = {
        "iss": "https://owner.cloudflareaccess.com",
        "aud": ["memory-atlas-aud"],
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=5)).timestamp()),
        "sub": "fixture-owner",
    }
    token = jwt.encode(claims, private_key, algorithm="RS256", headers={"kid": "fixture"})
    verifier = CloudflareAccessVerifier(
        "owner.cloudflareaccess.com",
        "memory-atlas-aud",
        key_resolver=lambda _: public_key,
    )
    assert verifier.verify(token)["sub"] == "fixture-owner"
    wrong_aud = CloudflareAccessVerifier(
        "owner.cloudflareaccess.com",
        "other-aud",
        key_resolver=lambda _: public_key,
    )
    with pytest.raises(AccessVerificationError):
        wrong_aud.verify(token)
    with pytest.raises(AccessVerificationError):
        verifier.verify(token + "tampered")


class FixtureAccessVerifier:
    def verify(self, token: str) -> dict[str, str]:
        if token != "fixture":
            raise AccessVerificationError("invalid fixture assertion")
        return {"sub": "fixture-owner"}


def test_api_health_and_mutation_auth_boundary(tmp_path: Path) -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    server.state = ApiState(
        tmp_path / "runtime",
        tmp_path / "web",
        "https://memoryatlas.example.test",
        access_verifier=FixtureAccessVerifier(),
    )  # type: ignore[attr-defined]
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = f"http://127.0.0.1:{server.server_address[1]}"
    try:
        with urllib.request.urlopen(base + "/healthz", timeout=5) as response:
            assert json.load(response)["state"] == "PASS"
        with pytest.raises(urllib.error.HTTPError) as private_read_denied:
            urllib.request.urlopen(base + "/api/v31/status", timeout=5)
        assert private_read_denied.value.code == 403
        forged_read = urllib.request.Request(
            base + "/api/v31/status",
            headers={"Cf-Access-Jwt-Assertion": "forged"},
        )
        with pytest.raises(urllib.error.HTTPError) as forged_read_denied:
            urllib.request.urlopen(forged_read, timeout=5)
        assert forged_read_denied.value.code == 403
        valid_read = urllib.request.Request(
            base + "/api/v31/status",
            headers={"Cf-Access-Jwt-Assertion": "fixture"},
        )
        with urllib.request.urlopen(valid_read, timeout=5) as response:
            assert json.load(response)["state"] == "UNKNOWN"
        body = json.dumps({"idempotency_key": "k"}).encode()
        request = urllib.request.Request(base + "/api/v31/actions/capture-request", data=body, method="POST", headers={"Content-Type": "application/json"})
        with pytest.raises(urllib.error.HTTPError) as denied:
            urllib.request.urlopen(request, timeout=5)
        assert denied.value.code == 403
        forged = urllib.request.Request(base + "/api/v31/actions/capture-request", data=body, method="POST", headers={"Content-Type": "application/json", "Origin": "https://memoryatlas.example.test", "Cf-Access-Jwt-Assertion": "forged"})
        with pytest.raises(urllib.error.HTTPError) as forged_denied:
            urllib.request.urlopen(forged, timeout=5)
        assert forged_denied.value.code == 403
        request = urllib.request.Request(base + "/api/v31/actions/capture-request", data=body, method="POST", headers={"Content-Type": "application/json", "Origin": "https://memoryatlas.example.test", "Cf-Access-Jwt-Assertion": "fixture"})
        with urllib.request.urlopen(request, timeout=5) as response:
            result = json.load(response)
        assert response.status == 202 and result["state"] == "WAITING_SOURCE"
    finally:
        server.shutdown(); server.server_close(); thread.join(timeout=5)


def load_lifecycle_module():
    path = Path(__file__).parents[2] / "ops" / "memory-atlas" / "automation_lifecycle.py"
    spec = importlib.util.spec_from_file_location("memory_atlas_automation_lifecycle", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_old_automation_is_archived_verified_then_immediately_paused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_lifecycle_module()
    root = tmp_path / "automations"; old = root / "codex"; old.mkdir(parents=True)
    (old / "automation.toml").write_text('id="codex"\nstatus="ACTIVE"\n', encoding="utf-8")
    (old / "memory.md").write_text("historical failure", encoding="utf-8")
    result = module.diagnose_old(root, tmp_path / "archive", "codex")
    assert result["state"] == "ARCHIVED_VERIFIED_AND_PAUSED"
    assert 'status = "PAUSED"' in (old / "automation.toml").read_text(encoding="utf-8")


def test_new_automation_install_and_retirement_gates(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    module = load_lifecycle_module()
    root = tmp_path / "automations"; old = root / "codex"; old.mkdir(parents=True)
    (old / "automation.toml").write_text('id="codex"\nstatus="PAUSED"\n', encoding="utf-8")
    repo = tmp_path / "repo"; repo.mkdir()
    assert module.install_new(root, repo)["state"] == "PASS"
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"gates": {key: False for key in module.REQUIRED_RETIRE_GATES}}), encoding="utf-8")
    with pytest.raises(module.LifecycleError, match="删除门未满足"):
        module.retire_old(root, "codex", evidence)
    evidence.write_text(json.dumps({"gates": {key: True for key in module.REQUIRED_RETIRE_GATES}}), encoding="utf-8")
    assert module.retire_old(root, "codex", evidence)["old_directory_absent"] is True


def test_systemd_units_use_bounded_runtime_identities() -> None:
    repo = Path(__file__).resolve().parents[2]
    unit_dir = repo / "ops/memory-atlas/systemd"
    application_services = [
        "memory-atlas-api.service",
        "memory-atlas-reconcile.service",
        "memory-atlas-action-worker.service",
    ]
    for name in application_services:
        text = (unit_dir / name).read_text(encoding="utf-8")
        assert "User=ubuntu" in text
        assert "Group=ubuntu" in text
        assert "EnvironmentFile=/srv/linze/secrets/memory-atlas.env" in text
        assert "ExecStart=/srv/linze/venvs/memory-atlas/bin/python -B -m" in text
    selfheal = (unit_dir / "memory-atlas-selfheal.service").read_text(encoding="utf-8")
    assert "User=root" in selfheal and "Group=root" in selfheal
    assert "NoNewPrivileges=true" in selfheal and "ProtectSystem=strict" in selfheal
    assert "ExecStart=/usr/local/bin/memory-atlas-selfheal" in selfheal

    reconcile = (unit_dir / "memory-atlas-reconcile.service").read_text(encoding="utf-8")
    assert "/srv/linze/apps/status/data" in reconcile
    assert "ProtectSystem=strict" in reconcile

    action_worker = (unit_dir / "memory-atlas-action-worker.service").read_text(encoding="utf-8")
    assert "/srv/linze/apps/status/data" in action_worker
    assert "ProtectSystem=strict" in action_worker
    assert "TimeoutStartSec=3600" in action_worker


def test_hardened_systemd_units_bind_gh_config_outside_protected_home() -> None:
    repo = Path(__file__).resolve().parents[2]
    unit_dir = repo / "ops/memory-atlas/systemd"
    gh_config = "Environment=GH_CONFIG_DIR=/srv/linze/state/memory-atlas/gh-config"
    for name in (
        "memory-atlas-api.service",
        "memory-atlas-reconcile.service",
        "memory-atlas-action-worker.service",
        "memory-atlas-selfheal.service",
    ):
        text = (unit_dir / name).read_text(encoding="utf-8")
        assert "ProtectHome=true" in text
        assert gh_config in text
    installer = (repo / "ops/memory-atlas/install-systemd.sh").read_text(encoding="utf-8")
    assert "install -d -m 0700 -o ubuntu -g ubuntu /srv/linze/state/memory-atlas/gh-config" in installer


def test_memory_atlas_uses_dedicated_non_conflicting_api_port() -> None:
    repo = Path(__file__).resolve().parents[2]
    expected = {
        "ops/memory-atlas/systemd/memory-atlas-api.service": "--port 8766",
        "ops/memory-atlas/post-promote-probe.sh": "127.0.0.1:8766",
        "ops/memory-atlas/rollback.sh": "127.0.0.1:8766",
        "ops/memory-atlas/start.sh": "127.0.0.1:8766",
        "ops/memory-atlas/diagnose.sh": "127.0.0.1:8766",
        "ops/memory-atlas/memory-atlas-selfheal": "127.0.0.1:8766",
        "ops/memory-atlas/nginx/default.conf": "host.docker.internal:18766",
    }
    for relative_path, required_fragment in expected.items():
        text = (repo / relative_path).read_text(encoding="utf-8")
        assert required_fragment in text, relative_path
        assert "8765" not in text, relative_path

    unit = (repo / "ops/memory-atlas/systemd/memory-atlas-api.service").read_text(encoding="utf-8")
    unit_section, service_section = unit.split("[Service]", maxsplit=1)
    assert "StartLimitIntervalSec=60" in unit_section
    assert "StartLimitBurst=5" in unit_section
    assert "StartLimitIntervalSec" not in service_section
    assert "StartLimitBurst" not in service_section


def test_memory_atlas_loopback_api_has_bounded_docker_bridge_proxy() -> None:
    repo = Path(__file__).resolve().parents[2]
    unit_dir = repo / "ops/memory-atlas/systemd"
    socket = (unit_dir / "memory-atlas-api-proxy.socket").read_text(encoding="utf-8")
    service = (unit_dir / "memory-atlas-api-proxy.service").read_text(encoding="utf-8")
    assert "ListenStream=10.0.0.1:18766" in socket
    assert "ListenStream=0.0.0.0" not in socket
    assert "ListenStream=18766" not in socket
    assert "After=network-online.target docker.service" in socket
    assert "Wants=network-online.target docker.service" in socket
    assert "User=ubuntu" in service and "Group=ubuntu" in service
    assert "Requires=memory-atlas-api.service" in service
    assert "After=memory-atlas-api.service" in service
    assert "ExecStart=/lib/systemd/systemd-socket-proxyd 127.0.0.1:8766" in service
    assert "NoNewPrivileges=true" in service
    assert "ProtectSystem=strict" in service and "ProtectHome=true" in service

    installer = (repo / "ops/memory-atlas/install-systemd.sh").read_text(encoding="utf-8")
    deploy = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    start = (repo / "ops/memory-atlas/start.sh").read_text(encoding="utf-8")
    stop = (repo / "ops/memory-atlas/stop.sh").read_text(encoding="utf-8")
    rollback = (repo / "ops/memory-atlas/rollback.sh").read_text(encoding="utf-8")
    probe = (repo / "ops/memory-atlas/post-promote-probe.sh").read_text(encoding="utf-8")
    for text in (installer, deploy, start, stop, rollback):
        assert "memory-atlas-api-proxy.socket" in text
    assert "internal_proxy_api_health" in probe
    assert "INTERNAL_PROXY_API_HEALTH_FAIL" in probe
    assert "internal_proxy_private" in probe
    assert "INTERNAL_PROXY_PRIVATE_API_NOT_FAIL_CLOSED" in probe

    assert "sudo systemctl stop memory-atlas-api-proxy.socket memory-atlas-api-proxy.service" in rollback
    assert "sudo systemctl start memory-atlas-api-proxy.socket" in rollback
    assert "sudo systemctl restart memory-atlas-api-proxy.socket" not in rollback


def test_restore_drill_uses_agentdatabase_runtime_not_frontend_release() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/restore-drill.sh").read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_AGENT_CURRENT" in text
    assert "/srv/linze/apps/agentdatabase/current" in text
    assert 'export PYTHONPATH="$AGENT_CURRENT"' in text
    assert 'PYTHONPATH="$CURRENT/AgentDatabase"' not in text


def test_action_worker_calls_keyword_only_restore_contract() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (
        repo / "OpenAIDatabase/scripts/memory_atlas_private/action_worker.py"
    ).read_text(encoding="utf-8")
    restore_call = text.split("receipt = isolated_restore(", maxsplit=1)[1].split(")", maxsplit=1)[0]
    assert "manifest_path=manifest_path" in restore_call
    assert "destination=destination" in restore_call
    assert "object_store=object_store" in restore_call
    assert "private_db=private_db" in restore_call


def test_deploy_preflights_candidate_and_rolls_back_blocking_probe() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    assert 'export PYTHONPATH="$agent_release"' in text
    assert 'MEMORY_ATLAS_PRIVATE_DB_CLIENT="$agent_release/OpenAIDatabase/scripts/private_db_client.py"' in text
    assert 'MEMORY_ATLAS_SOURCE_REGISTRY="$agent_release/ops/memory-atlas/source-registry.json"' in text
    assert 'install-systemd.sh" "$agent_release"' in text
    assert 'POST_PROMOTE_BLOCKED_AND_ROLLED_BACK' in text
    assert 'rollback_promoted_release "$probe_rc" || true' in text
    assert "trap post_promotion_error ERR" in text
    assert text.index("trap post_promotion_error ERR") < text.index("sudo systemctl restart memory-atlas-api.service")
    assert "sudo systemctl restart memory-atlas-reconcile.service memory-atlas-action-worker.service" in text
    assert "sudo systemctl start memory-atlas-reconcile.service memory-atlas-action-worker.service" not in text
    assert text.index("trap - ERR") < text.index('"$agent_release/ops/memory-atlas/post-promote-probe.sh" "$release_id"')
    assert text.index('"$agent_release/ops/memory-atlas/post-promote-probe.sh" "$release_id"') < text.index('case "$probe_rc" in')
    assert "POST_PROMOTION_STEP_FAILED_AND_ROLLED_BACK" in text


def test_deploy_first_release_rolls_back_to_absent_state() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    assert "rollback_first_deploy_to_absent()" in text
    assert "FIRST_DEPLOY_ABSENCE_RESTORED" in text
    assert "systemctl disable --now" in text
    assert 'docker compose -f "$agent_release/ops/memory-atlas/docker-compose.yml" down --remove-orphans' in text
    assert 'remove_symlink_if_target "$APP_ROOT/current" "$release"' in text
    assert 'remove_symlink_if_target "$AGENT_ROOT/current" "$agent_release"' in text
    assert 'remove_symlink_if_target "$APP_ROOT/candidate" "$release"' in text
    assert 'remove_symlink_if_target "$AGENT_ROOT/candidate" "$agent_release"' in text
    assert 'rollback_first_deploy_to_absent "$failed_rc"' in text


def test_deploy_validates_with_locked_memory_atlas_venv() -> None:
    repo = Path(__file__).resolve().parents[2]
    deploy = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    requirements = (
        repo
        / "OpenAIDatabase/scripts/memory_atlas_private/requirements-memory-atlas-private.txt"
    ).read_text(encoding="utf-8")
    assert 'VENV=${MEMORY_ATLAS_VENV:-/srv/linze/venvs/memory-atlas}' in deploy
    assert 'python3 -m venv "$VENV"' in deploy
    assert '"$VENV/bin/python" -m pip install' in deploy
    assert 'requirements-memory-atlas-private.txt' in deploy
    assert '"$VENV/bin/python" -B -m pytest' in deploy
    assert "PYTHONDONTWRITEBYTECODE=1 python3 -B -m pytest" not in deploy
    assert "pytest==9.0.2" in requirements.splitlines()


def test_deploy_prepares_first_release_directories_for_deploy_user() -> None:
    repo = Path(__file__).resolve().parents[2]
    deploy = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    ownership_gate = 'sudo install -d -m 0750 -o "$deploy_user" -g "$deploy_group"'
    assert ownership_gate in deploy
    for path in (
        '"$APP_ROOT"',
        '"$APP_ROOT/releases"',
        '"$APP_ROOT/shared"',
        '"$APP_ROOT/shared/data"',
        '"$APP_ROOT/shared/public-baseline"',
        '"$AGENT_ROOT"',
        '"$AGENT_ROOT/releases"',
    ):
        assert path in deploy
    assert deploy.index(ownership_gate) < deploy.index('release_id="$(date -u')


def test_deploy_uses_current_frozen_candidate_oracles_not_retired_codexproject_validator() -> None:
    repo = Path(__file__).resolve().parents[2]
    deploy = (repo / "ops/memory-atlas/deploy-blue-green.sh").read_text(encoding="utf-8")
    assert "npm --prefix MemoryAtlas run validate:v31" in deploy
    assert "OpenAIDatabase/tests/test_memory_atlas_private_v31.py" in deploy
    executable_lines = [
        line.strip() for line in deploy.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]
    assert all("validate:whole-project" not in line for line in executable_lines)


def test_post_promote_probe_never_claims_full_pass_without_authenticated_path() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/post-promote-probe.sh").read_text(encoding="utf-8")
    assert 'DEPLOYED_INTERNAL_VERIFIED_OWNER_ACCESS_CONFIRMATION_PENDING' in text
    assert 'POST_PROMOTION_AUTHENTICATED_PATH_VERIFIED' in text
    assert '[[ "$state" == "POST_PROMOTION_AUTHENTICATED_PATH_VERIFIED" ]] || exit 5' in text
    assert 'UNAUTHENTICATED_PUBLIC_${name^^}_UNEXPECTEDLY_OPEN' in text
    assert 'INTERNAL_PRIVATE_API_NOT_FAIL_CLOSED' in text
    assert 'STATIC_PRIVATE_SNAPSHOT_EXPOSED' in text
    assert '"$origin/api/v31/status"' in text
    assert 'auth_private' in text


def test_bootstrap_r2_scope_has_no_bucket_creation_path() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/bootstrap_protected_env.py").read_text(encoding="utf-8")
    forbidden = "create" + "_bucket"
    assert forbidden not in text
    assert "len(passed) != 1" in text
    assert "head_bucket" in text and "put_object" in text and "get_object" in text


def test_bootstrap_binds_explicit_github_token_file_without_stdout_secret() -> None:
    repo = Path(__file__).resolve().parents[2]
    bootstrap = (repo / "ops/memory-atlas/bootstrap_protected_env.py").read_text(encoding="utf-8")
    env_example = (repo / "ops/memory-atlas/memory-atlas.env.example").read_text(encoding="utf-8")
    assert 'parser.add_argument("--github-token-file", type=Path)' in bootstrap
    assert "github_token = read_secret_file(args.github_token_file)" in bootstrap
    assert 'f"GH_TOKEN={github_token}\\n"' in bootstrap
    assert '"github_token_bound": bool(github_token)' in bootstrap
    assert "GH_TOKEN=" in env_example
    stdout_payload = bootstrap.split("print(json.dumps({", maxsplit=1)[1].split("}", maxsplit=1)[0]
    assert '"github_token":' not in stdout_payload


def test_private_fact_backup_requires_successful_source_and_readback(tmp_path: Path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.fact_backup import backup_private_facts
    registry = write_registry(tmp_path / "registry.json", [])
    config = make_config(tmp_path, registry)
    private = LocalPrivateDatabase(tmp_path / "private")
    store = LocalObjectStore(tmp_path / "objects")
    waiting = backup_private_facts(config, private, store, generated_at="2026-08-01T00:00:00+00:00")
    assert waiting["state"] == "WAITING_SOURCE"
    manifest_path = "memory-atlas/runs/20260801/run-1/manifest.json"
    private.put_json("memory-atlas/runs/latest.json", {"state": "SUCCEEDED", "run_id": "run-1", "manifest_path": manifest_path}, "x")
    private.put_json(manifest_path, {"run_id": "run-1", "state": "SUCCEEDED", "objects": []}, "x")
    result = backup_private_facts(config, private, store, generated_at="2026-08-01T00:00:00+00:00")
    assert result["state"] == "PASS"
    assert result["receipt"]["readback_verified"] is True
    assert result["github_private_database"]["readback_verified"] is True
    assert private.get_json(result["github_private_database"]["relpath"])["source_run_id"] == "run-1"
    assert private.get_json("memory-atlas/backups/latest.json")["state"] == "PASS"


def test_private_release_archive_is_split_and_restores_exact_bytes(tmp_path: Path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.private_release import (
        _archive_manifest,
        _encrypt_archive,
        _restore_archive,
    )

    age = shutil.which("age") or str(Path.home() / ".local/bin/age")
    age_keygen = shutil.which("age-keygen") or str(Path.home() / ".local/bin/age-keygen")
    assert Path(age).is_file() and Path(age_keygen).is_file(), "age toolchain unavailable"
    generated = subprocess.run(
        [age_keygen], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    identity_match = re.search(rb"AGE-SECRET-KEY-[A-Z0-9]+", generated.stdout)
    recipient_match = re.search(rb"age1[0-9a-z]+", generated.stderr)
    assert identity_match and recipient_match
    identity = bytearray(identity_match.group(0))
    source = tmp_path / "source.bin"
    source.write_bytes(os.urandom(4096))
    record = InventoryRecord(
        source_id="codex_sessions",
        source_root=str(tmp_path),
        relative_path="fixture/source.bin",
        materialized_path=str(source),
        kind="files",
        size_bytes=source.stat().st_size,
        mtime_ns=source.stat().st_mtime_ns,
        sha256=sha256_file(source),
        original_sha256=sha256_file(source),
        snapshot_created=True,
    )
    manifest = _archive_manifest([record], backup_id="fixture-run", created_at=FIXED_TIME)
    encrypted = tmp_path / "encrypted"
    encrypted.mkdir()
    parts = _encrypt_archive(
        records=[record],
        manifest=manifest,
        recipient=recipient_match.group(0).decode("ascii"),
        age=age,
        directory=encrypted,
        max_part_bytes=512,
        max_parts=64,
    )
    assert len(parts) >= 2
    assert all(part.size_bytes <= 512 for part in parts)
    restored = _restore_archive(
        parts=[part.path for part in parts],
        destination=tmp_path / "restore",
        age=age,
        identity=identity,
    )
    assert restored == {
        "state": "PASS",
        "restored_files": 1,
        "restored_bytes": source.stat().st_size,
        "all_hashes_match": True,
    }
    for index in range(len(identity)):
        identity[index] = 0


def test_private_release_workflow_verifies_remote_restore_and_cleans_local_payload(
    tmp_path: Path,
) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.private_release import PrivateReleaseBackup

    age_keygen = shutil.which("age-keygen") or str(Path.home() / ".local/bin/age-keygen")
    assert Path(age_keygen).is_file(), "age toolchain unavailable"
    generated = subprocess.run(
        [age_keygen], stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True
    )
    identity_match = re.search(rb"AGE-SECRET-KEY-[A-Z0-9]+", generated.stdout)
    recipient_match = re.search(rb"age1[0-9a-z]+", generated.stderr)
    assert identity_match and recipient_match
    identity_bytes = identity_match.group(0)
    recipient = recipient_match.group(0).decode("ascii")

    database_dir = Path(__file__).resolve().parents[1]
    private_policy = json.loads(
        (database_dir / "config/storage/private_encrypted_backup_policy.json").read_text()
    )
    public_policy = json.loads(
        (database_dir / "config/storage/public_encrypted_backup_policy.json").read_text()
    )
    public_policy["unified_key"]["public_recipient"] = recipient
    public_policy["unified_key"]["recipient_fingerprint"] = hashlib.sha256(
        recipient.encode("ascii")
    ).hexdigest()
    private_policy_path = tmp_path / "private-policy.json"
    public_policy_path = tmp_path / "public-policy.json"
    private_policy_path.write_text(json.dumps(private_policy), encoding="utf-8")
    public_policy_path.write_text(json.dumps(public_policy), encoding="utf-8")

    class FakeReleaseClient:
        def __init__(self) -> None:
            self.assets: dict[str, bytes] = {}
            self.tag = ""
            self.draft = True

        def assert_private_repository(self) -> None:
            return None

        def create_draft(self, tag: str, title: str) -> None:
            assert title.startswith("Memory Atlas")
            self.tag = tag
            self.draft = True

        def upload(self, tag: str, paths: list[Path]) -> None:
            assert tag == self.tag and self.draft
            self.assets = {path.name: path.read_bytes() for path in paths}

        def download(self, tag: str, destination: Path) -> None:
            assert tag == self.tag
            for name, payload in self.assets.items():
                (destination / name).write_bytes(payload)

        def view(self, tag: str) -> dict[str, object]:
            assert tag == self.tag
            return {
                "tagName": tag,
                "isDraft": self.draft,
                "url": "https://github.example.test/private/release",
                "assets": [
                    {"name": name, "size": len(payload)}
                    for name, payload in self.assets.items()
                ],
            }

        def publish(self, tag: str) -> None:
            assert tag == self.tag
            self.draft = False

        def enforce_retention(self, prefix: str, keep: int) -> list[str]:
            assert prefix == "memory-atlas-auto-backup-" and keep == 3
            return []

    source = tmp_path / "source.jsonl"
    source.write_bytes(os.urandom(8192))
    record = InventoryRecord(
        source_id="codex_sessions",
        source_root=str(tmp_path),
        relative_path="fixture/source.jsonl",
        materialized_path=str(source),
        kind="files",
        size_bytes=source.stat().st_size,
        mtime_ns=source.stat().st_mtime_ns,
        sha256=sha256_file(source),
        original_sha256=sha256_file(source),
        snapshot_created=True,
    )
    fake = FakeReleaseClient()
    backup = PrivateReleaseBackup(
        private_policy_path=private_policy_path,
        public_policy_path=public_policy_path,
        identity_loader=lambda: bytearray(identity_bytes),
        release_client=fake,  # type: ignore[arg-type]
    )
    result = backup.run(
        records=[record],
        logical_source_set=list(private_policy["scope"]["logical_sources"]),
        backup_id="marun_fixture_1234567890",
        created_at=FIXED_TIME,
        work_root=tmp_path,
    )
    assert result["state"] == "PASS"
    assert result["remote_readback_verified"] is True
    assert result["isolated_restore"]["all_hashes_match"] is True
    assert result["local_payload_cleanup"] == {"state": "PASS", "remaining_paths": 0}
    assert not (tmp_path / "private-github-release").exists()


def test_source_capture_entry_only_sweeps_owned_stale_temp_dirs(tmp_path: Path) -> None:
    import OpenAIDatabase.scripts.memory_atlas_source_capture_entry as entry

    old = tmp_path / f"{entry.TEMP_PREFIX}old"
    young = tmp_path / f"{entry.TEMP_PREFIX}young"
    unrelated = tmp_path / "other-task"
    for path in (old, young, unrelated):
        path.mkdir()
        (path / "payload").write_bytes(b"fixture")
    now = 2_000_000.0
    os.utime(old, (now - entry.STALE_SECONDS - 1, now - entry.STALE_SECONDS - 1))
    os.utime(young, (now, now))
    assert entry.cleanup_stale_run_dirs(tmp_path, now=now) == 1
    assert not old.exists()
    assert young.is_dir()
    assert unrelated.is_dir()


def test_source_capture_entry_redacts_unreadable_source_filename() -> None:
    import OpenAIDatabase.scripts.memory_atlas_source_capture_entry as entry

    coverage = entry._public_safe_source_coverage(
        [{
            "source_id": "codex_memories",
            "label_zh": "Codex 记忆",
            "required": False,
            "state": "UNREADABLE",
            "object_count": 3,
            "size_bytes": 10,
            "message_zh": "refused: private-secret-name.json",
        }]
    )
    encoded = json.dumps(coverage, ensure_ascii=False)
    assert "private-secret-name.json" not in encoded
    assert coverage and coverage[0]["reason_code"] == "STANDALONE_CREDENTIAL_LIKE_FILE_EXCLUDED"


def test_private_snapshot_is_only_exposed_through_signed_api() -> None:
    repo = Path(__file__).resolve().parents[2]
    provider = (repo / "MemoryAtlas/src/v31/PrivateAnalyticsProvider.tsx").read_text(encoding="utf-8")
    nginx = (repo / "ops/memory-atlas/nginx/default.conf").read_text(encoding="utf-8")
    compose = (repo / "ops/memory-atlas/docker-compose.yml").read_text(encoding="utf-8")
    assert 'new URL("/api/v31/status"' in provider
    assert "/data/" not in provider
    assert "/memory_atlas_private_analytics.json" not in provider
    assert "location ^~ /data/" in nginx and "return 404;" in nginx
    assert "shared/data:/usr/share/nginx/html/data" not in compose
    assert "proxy_set_header Cf-Access-Jwt-Assertion" in nginx


def test_manual_backup_sources_protected_env_and_current_runtime() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/backup.sh").read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_ENV_FILE" in text
    assert 'source "$ENV_FILE"' in text
    assert "MEMORY_ATLAS_AGENT_CURRENT" in text
    assert 'export PYTHONPATH="$AGENT_CURRENT"' in text
    assert "private_db_client.py" in text and "source-registry.json" in text


def test_source_capture_entry_forces_ephemeral_local_paths(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import OpenAIDatabase.scripts.memory_atlas_source_capture_entry as entry

    env_file = tmp_path / "memory_atlas.env"
    env_file.write_text(
        "MEMORY_ATLAS_RUNTIME_DIR=/srv/linze/state/memory-atlas\n"
        "MEMORY_ATLAS_WORK_DIR=/srv/linze/work/memory-atlas\n"
        "MEMORY_ATLAS_WEB_DATA_DIR=/srv/linze/apps/memory-atlas/shared/data\n",
        encoding="utf-8",
    )
    expected = {
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT": str(tmp_path / "repo" / "private_db_client.py"),
        "MEMORY_ATLAS_SOURCE_REGISTRY": str(tmp_path / "repo" / "source-registry.json"),
        "MEMORY_ATLAS_RUNTIME_DIR": str(tmp_path / "protected" / "runtime"),
        "MEMORY_ATLAS_WORK_DIR": str(tmp_path / "protected" / "work"),
        "MEMORY_ATLAS_WEB_DATA_DIR": str(tmp_path / "protected" / "preview"),
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT": str(tmp_path / "repo" / "memory_atlas.json"),
        "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS": str(tmp_path / "repo" / "data"),
        "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS": str(tmp_path / "protected" / "evidence"),
        "MEMORY_ATLAS_SOURCE_HOST_ID": "verified-local-host",
    }
    monkeypatch.setenv("MEMORY_ATLAS_ENV_FILE", str(env_file))
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr(entry, "find_repo_root", lambda _: tmp_path / "repo")
    observed: dict[str, str] = {}

    def fake_run(command: list[str], *, cwd: Path, env: dict[str, str]):
        assert command[-1] == "capture"
        assert cwd == tmp_path / "repo"
        observed.update(env)
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"state": "SUCCEEDED", "run_id": "fixture-run"}),
            "",
        )

    monkeypatch.setattr(entry, "_run_capture", fake_run)
    with pytest.raises(SystemExit) as exit_info:
        entry.main()
    assert exit_info.value.code == 0
    for key in (
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT",
        "MEMORY_ATLAS_SOURCE_REGISTRY",
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT",
        "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS",
        "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS",
        "MEMORY_ATLAS_SOURCE_HOST_ID",
    ):
        assert observed[key] == expected[key]
    ephemeral = Path(observed["MEMORY_ATLAS_RUNTIME_DIR"]).parent
    assert ephemeral.name.startswith(entry.TEMP_PREFIX)
    assert Path(observed["MEMORY_ATLAS_WORK_DIR"]).parent == ephemeral
    assert Path(observed["MEMORY_ATLAS_WEB_DATA_DIR"]).parent == ephemeral
    assert Path(observed["TMPDIR"]).parent == ephemeral
    assert not ephemeral.exists()
    assert observed["MEMORY_ATLAS_PRIVATE_RELEASE_BACKUP_ENABLED"] == "1"


def test_source_capture_entry_symlink_keeps_evidence_binding_but_uses_ephemeral_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import OpenAIDatabase.scripts.memory_atlas_source_capture_entry as entry

    protected = tmp_path / "protected"
    protected.mkdir()
    protected_env = protected / "memory_atlas.env"
    protected_env.write_text(
        "MEMORY_ATLAS_RUNTIME_DIR=/srv/linze/state/memory-atlas\n"
        "MEMORY_ATLAS_WORK_DIR=/srv/linze/work/memory-atlas\n"
        "MEMORY_ATLAS_WEB_DATA_DIR=/srv/linze/apps/memory-atlas/shared/data\n"
        "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS=/srv/linze/evidence\n",
        encoding="utf-8",
    )
    protected_python = protected / "memory-atlas-venv" / "bin" / "python"
    protected_python.parent.mkdir(parents=True)
    protected_python.write_text("fixture\n", encoding="utf-8")
    env_link = tmp_path / "memory-atlas.env"
    env_link.symlink_to(protected_env)
    local_keys = (
        "MEMORY_ATLAS_RUNTIME_DIR",
        "MEMORY_ATLAS_WORK_DIR",
        "MEMORY_ATLAS_WEB_DATA_DIR",
        "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS",
    )
    monkeypatch.setenv("MEMORY_ATLAS_ENV_FILE", str(env_link))
    for key in local_keys:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(entry, "find_repo_root", lambda _: tmp_path / "repo")
    observed: dict[str, str] = {}

    def fake_run(command: list[str], *, cwd: Path, env: dict[str, str]):
        assert command[0] == str(protected_python)
        observed.update(env)
        return subprocess.CompletedProcess(
            command,
            0,
            json.dumps({"state": "SUCCEEDED", "run_id": "fixture-run"}),
            "",
        )

    monkeypatch.setattr(entry, "_run_capture", fake_run)
    with pytest.raises(SystemExit) as exit_info:
        entry.main()
    assert exit_info.value.code == 0
    ephemeral = Path(observed["MEMORY_ATLAS_RUNTIME_DIR"]).parent
    assert ephemeral.name.startswith(entry.TEMP_PREFIX)
    assert Path(observed["MEMORY_ATLAS_WORK_DIR"]).parent == ephemeral
    assert Path(observed["MEMORY_ATLAS_WEB_DATA_DIR"]).parent == ephemeral
    assert not ephemeral.exists()
    assert observed["MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS"] == str(protected / "memory-atlas-evidence-adapters")


def test_private_database_verify_resolves_release_assets_with_digest(monkeypatch: pytest.MonkeyPatch) -> None:
    import OpenAIDatabase.scripts.private_db_client as client

    digest = "a" * 64
    calls: list[list[str]] = []

    def fake_gh(args: list[str], **_: object) -> bytes:
        calls.append(args)
        return json.dumps({
            "assets": [{
                "name": "archive.tar.gz",
                "state": "uploaded",
                "size": 123,
                "digest": f"sha256:{digest}",
            }],
        }).encode()

    monkeypatch.setattr(client, "_gh", fake_gh)
    record = {
        "object_path": "github-release://LinzeColin/Private-Database/archive-tag/archive.tar.gz",
        "size_bytes": 123,
        "sha256": digest,
    }
    assert client._manifest_object_exists("Private-AgentDatabase", record) is True
    assert calls == [["repos/LinzeColin/Private-Database/releases/tags/archive-tag"]]
    assert client._manifest_object_exists("Private-AgentDatabase", {**record, "sha256": "b" * 64}) is False
    assert client._manifest_object_exists("Private-AgentDatabase", {
        **record,
        "object_path": "https://example.test/archive.tar.gz",
    }) is False


def test_private_database_verify_accepts_legacy_area_qualified_content_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import OpenAIDatabase.scripts.private_db_client as client

    observed: list[str] = []

    def fake_get_meta(path: str) -> dict[str, object]:
        observed.append(path)
        return {"size": 7}

    monkeypatch.setattr(client, "_get_meta", fake_get_meta)
    assert client._manifest_object_exists("Private-AgentDatabase", {
        "object_path": "Private-AgentDatabase/objects/aa/fixture.json",
        "size_bytes": 7,
    }) is True
    assert observed == ["Private-AgentDatabase/objects/aa/fixture.json"]
    assert client._manifest_object_exists("Private-AgentDatabase", {
        "object_path": "Private-KMDatabase/objects/aa/wrong-area.json",
        "size_bytes": 7,
    }) is False


def test_gh_private_database_put_requires_equal_remote_readback(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from subprocess import CompletedProcess
    import OpenAIDatabase.scripts.memory_atlas_private.private_db as private_db_module
    from OpenAIDatabase.scripts.memory_atlas_private.private_db import GhPrivateDatabase

    storage: dict[str, dict[str, object]] = {}
    calls: list[str] = []

    def fake_run(self: GhPrivateDatabase, args: list[str]) -> CompletedProcess[str]:
        calls.append(args[0])
        if args[0] == "put":
            storage[args[2]] = json.loads(Path(args[3]).read_text(encoding="utf-8"))
        elif args[0] == "get":
            Path(args[3]).write_text(json.dumps(storage[args[2]]), encoding="utf-8")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(GhPrivateDatabase, "_run", fake_run)
    backend = GhPrivateDatabase(tmp_path / "client.py")
    value = {"schema_version": "fixture.v1", "state": "PASS"}
    assert backend.put_json("memory-atlas/fixture.json", value, "fixture") == "memory-atlas/fixture.json"
    assert calls == ["put", "get"]

    def corrupt_run(self: GhPrivateDatabase, args: list[str]) -> CompletedProcess[str]:
        if args[0] == "get":
            Path(args[3]).write_text('{"state":"CORRUPT"}', encoding="utf-8")
        return CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(GhPrivateDatabase, "_run", corrupt_run)
    monkeypatch.setattr(private_db_module.time, "sleep", lambda _: None)
    with pytest.raises(PrivateDatabaseError, match="读回不一致"):
        backend.put_json("memory-atlas/fixture.json", value, "fixture")


def load_cloudflare_edge_module():
    path = Path(__file__).parents[2] / "ops" / "memory-atlas" / "configure_cloudflare_edge.py"
    spec = importlib.util.spec_from_file_location("memory_atlas_cloudflare_edge", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_cloudflare_edge_app_resolution_is_unique_and_template_wildcard_safe() -> None:
    module = load_cloudflare_edge_module()
    apps = [
        {"id": "a", "domain": "status.linzezhang.com/admin*"},
        {"id": "b", "domain": "memoryatlas.linzezhang.com"},
    ]
    assert module.find_unique_app(apps, "status.linzezhang.com/admin", template=True)["id"] == "a"
    assert module.find_unique_app(apps, "memoryatlas.linzezhang.com")["id"] == "b"
    with pytest.raises(module.EdgeConfigurationError, match="唯一"):
        module.find_unique_app(apps + [{"id": "c", "domain": "memoryatlas.linzezhang.com"}], "memoryatlas.linzezhang.com")


def test_cloudflare_edge_rejects_bypass_and_public_everyone_policies() -> None:
    module = load_cloudflare_edge_module()
    with pytest.raises(module.EdgeConfigurationError, match="bypass"):
        module.safe_policy_body({"decision": "bypass", "include": [{"email": {"email": "owner@example.test"}}]}, target_name="Memory Atlas")
    with pytest.raises(module.EdgeConfigurationError, match="Everyone"):
        module.safe_policy_body({"decision": "allow", "include": [{"everyone": {}}]}, target_name="Memory Atlas")
    body = module.safe_policy_body({
        "id": "must-not-copy", "name": "Owner", "decision": "allow",
        "include": [{"email": {"email": "owner@example.test"}}], "precedence": 1,
    }, target_name="Memory Atlas")
    assert body["decision"] == "allow" and body["precedence"] == 1
    assert "id" not in body and body["name"].startswith("Memory Atlas")


def test_cloudflare_edge_env_merge_preserves_storage_and_never_persists_api_token(tmp_path: Path) -> None:
    module = load_cloudflare_edge_module()
    env = tmp_path / "memory_atlas.env"
    env.write_text("MEMORY_ATLAS_R2_BUCKET=existing\nMEMORY_ATLAS_CF_ACCESS_AUD=old\n", encoding="utf-8")
    module._write_env_values(env, {
        "MEMORY_ATLAS_CF_ACCESS_TEAM_DOMAIN": "https://owner.cloudflareaccess.com",
        "MEMORY_ATLAS_CF_ACCESS_AUD": "new-aud",
        "MEMORY_ATLAS_CF_ACCESS_APP_ID": "app-id",
    })
    text = env.read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_R2_BUCKET=existing" in text
    assert "MEMORY_ATLAS_CF_ACCESS_AUD=new-aud" in text
    assert "MEMORY_ATLAS_CF_ACCESS_APP_ID=app-id" in text
    assert "API Token" not in text or "without storing API Token" in text
    assert module.stat.S_IMODE(env.stat().st_mode) == 0o600


def test_bootstrap_env_contains_complete_ovh_runtime_defaults() -> None:
    repo = Path(__file__).resolve().parents[2]
    text = (repo / "ops/memory-atlas/bootstrap_protected_env.py").read_text(encoding="utf-8")
    for token in (
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT=/srv/linze/apps/agentdatabase/current/OpenAIDatabase/scripts/private_db_client.py",
        "MEMORY_ATLAS_SOURCE_REGISTRY=/srv/linze/apps/agentdatabase/current/ops/memory-atlas/source-registry.json",
        "MEMORY_ATLAS_RUNTIME_DIR=/srv/linze/state/memory-atlas",
        "MEMORY_ATLAS_WORK_DIR=/srv/linze/work/memory-atlas",
        "MEMORY_ATLAS_WEB_DATA_DIR=/srv/linze/apps/memory-atlas/shared/data",
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT=/srv/linze/apps/memory-atlas/shared/public-baseline/memory_atlas.json",
        "MEMORY_ATLAS_FAILURE_ASSET_REGISTRY=/srv/linze/secrets/memory-atlas-failure-assets.json",
        "MEMORY_ATLAS_STATUS_PROJECTION_TARGET=/srv/linze/apps/status/data/memory_atlas_status_projection.json",
    ):
        assert token in text
