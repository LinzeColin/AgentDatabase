"""v0.0.0.32 T03/T06 — the publish path actually publishes, and tiers are data.

The T03 slice wired `_publish_live_snapshot` into the pipeline but never ran it
end to end. It could not have worked: the run block carried no `trace_id` and no
`source_completed_at`, the state was still `REFRESHING_ATLAS` when the adapter
demands a terminal state, `cloud_native_sources` was empty, and the same-run
evidence rows carried `verified` instead of `state`. Each of those raises inside
`build_live_snapshot`, and the exception was swallowed into
`_live_snapshot_error`. These tests pin the shape end to end so a silent
regression cannot come back.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from OpenAIDatabase.scripts.memory_atlas_private.live_snapshot_adapter import (
    LiveSnapshotError,
    build_live_snapshot,
)
from OpenAIDatabase.scripts.memory_atlas_private.pipeline import (
    cloud_native_authorities,
    normalize_live_run_block,
    same_run_evidence_rows,
)

REPO = Path(__file__).resolve().parents[2]
FIXTURES = REPO / "OpenAIDatabase" / "fixtures"
SCHEMA = REPO / "OpenAIDatabase" / "schema" / "memory_atlas.live_snapshot.v1.schema.json"
REGISTRY = REPO / "ops" / "memory-atlas" / "source-registry.json"

VERIFIED_OBJECT = {
    "sha256": "a" * 64,
    "object_key": "primary-objects/memory-atlas/x",
    "size_bytes": 1024,
    "operation": "CREATED",
    "readback_sha256": "a" * 64,
    "readback_verified": True,
    "provider_version": "r2",
}
BROKEN_OBJECT = {**VERIFIED_OBJECT, "readback_sha256": "b" * 64, "readback_verified": False}
# Since the 2026-08-04 migration the event authority is the canonical union in
# the private repository's releases, not R2.
CANONICAL_READY = {
    "state": "READY",
    "provider": "github_private_release",
    "canonical_object": "primary-objects/memory-atlas/x/canonical/events.jsonl",
    "sha256": "c" * 64,
    "bytes": 389413637,
    "unique_events": 122080,
    "release_tag": "memory-atlas-canonical-20260804",
    "release_published_at": "2026-08-04T08:02:40Z",
    "superseded_count": 10,
    "reason": None,
}
CANONICAL_LOST = {**CANONICAL_READY, "state": "UNAVAILABLE", "reason": "no_canonical_release_published"}
# The shape PrivateReleaseBackup actually writes. The old fixture used a `files`
# key it has never written, which is the defect these tests now pin.
RELEASE_BACKUP_PASS = {
    "schema_version": "memory_atlas.encrypted_archive_manifest.v1",
    "state": "PASS",
    "ciphertext_part_count": 8,
    "ciphertext_size_bytes": 698130810,
    "remote_readback_verified": True,
    "parts": [{"part_number": n} for n in range(1, 9)],
    "isolated_restore": {"state": "PASS", "all_hashes_match": True, "restored_files": 2301},
}


def _visual() -> dict:
    return json.loads((FIXTURES / "visual_analytics.synthetic.json").read_text(encoding="utf-8"))


def _private() -> dict:
    return json.loads((FIXTURES / "private_analytics.synthetic.json").read_text(encoding="utf-8"))


def _benchmark() -> dict:
    return json.loads((FIXTURES / "benchmark_result.synthetic.json").read_text(encoding="utf-8"))


def _evidence(**overrides) -> dict:
    base = {
        "schema_version": "memory_atlas.runtime_evidence.v1",
        "generated_at": "2026-08-03T10:20:00Z",
        "run_id": "marun-20260803T101500Z-a1b2c3",
        "trace_id": "marun-20260803T101500Z-a1b2c3",
        "release": {"identity_state": "OBSERVED", "repository_commit": None, "release_id": None, "artifact_digest": None, "deployment_revision": None},
        "cloud_native_sources": cloud_native_authorities(
            objects=[VERIFIED_OBJECT],
            normalized_batch_key=VERIFIED_OBJECT["object_key"],
            private_database_paths=["memory-atlas/runs/latest.json"],
            github_release=RELEASE_BACKUP_PASS,
            observed_at="2026-08-03T10:15:00Z",
            registry_path=REGISTRY,
            canonical=CANONICAL_READY,
        ),
        "same_run_evidence": same_run_evidence_rows(
            run_id="marun-20260803T101500Z-a1b2c3",
            trace_id="marun-20260803T101500Z-a1b2c3",
            r2_readback=True,
            private_database_readback=True,
            ovh_reconcile=True,
            status_projection=True,
            ref="private-db://memory-atlas/runs/latest.json",
            canonical_source_readback=True,
        ),
    }
    base.update(overrides)
    return base


def _run_block(state: str = "REBUILT_FROM_AUTHORITIES") -> dict:
    return normalize_live_run_block(
        {"run_id": "marun-20260803T101500Z-a1b2c3", "state": "REFRESHING_ATLAS", "source_coverages": []},
        run_id="marun-20260803T101500Z-a1b2c3",
        trace_id="marun-20260803T101500Z-a1b2c3",
        state=state,
        started_at="2026-08-03T10:00:00Z",
        completed_at="2026-08-03T10:15:00Z",
    )


def _snapshot(**overrides):
    private = _private()
    private["run"] = _run_block()
    private.update(overrides)
    return build_live_snapshot(private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z")


def test_pipeline_shaped_inputs_actually_produce_a_snapshot() -> None:
    # The regression this file exists for: before the fix every one of these
    # fields was wrong and the adapter refused on the first of them.
    snapshot = _snapshot()
    assert snapshot["schema_version"] == "memory_atlas.live_snapshot.v1"
    assert snapshot["run"]["run_id"] == "marun-20260803T101500Z-a1b2c3" and snapshot["run"]["trace_id"] == "marun-20260803T101500Z-a1b2c3"
    assert snapshot["run"]["source_completed_at"] == "2026-08-03T10:15:00Z"
    assert snapshot["run"]["source_state"] == "REBUILT_FROM_AUTHORITIES"
    assert len(snapshot["visuals"]) == 3


def test_published_snapshot_validates_against_the_frozen_schema() -> None:
    import jsonschema

    schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).validate(_snapshot())


def test_a_non_terminal_run_is_refused() -> None:
    private = _private()
    private["run"] = _run_block(state="REFRESHING_ATLAS")
    with pytest.raises(LiveSnapshotError, match="non-terminal"):
        build_live_snapshot(private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z")


def test_source_host_without_ovh_reconcile_cannot_publish() -> None:
    # The capture host uploads objects; only the OVH reconcile has reconcile
    # evidence. Publishing there would claim an authority the host never read.
    evidence = _evidence(
        same_run_evidence=same_run_evidence_rows(
            run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3", r2_readback=True,
            private_database_readback=True, ovh_reconcile=None, status_projection=None,
        )
    )
    private = _private()
    private["run"] = _run_block()
    with pytest.raises(LiveSnapshotError, match="ovh_reconcile"):
        build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")


def test_failed_object_readback_is_reported_as_failed_not_ready() -> None:
    rows = cloud_native_authorities(
        objects=[BROKEN_OBJECT], normalized_batch_key=BROKEN_OBJECT["object_key"],
        private_database_paths=["memory-atlas/runs/latest.json"], github_release=None,
        observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY,
    )
    by_id = {row["source_id"]: row for row in rows}
    assert by_id["r2_primary_objects"]["state"] == "FAILED"
    assert same_run_evidence_rows(
        run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3", r2_readback=False, private_database_readback=True,
        ovh_reconcile=True, status_projection=True,
    )["r2_readback"]["state"] == "FAIL"


def test_tier_a_failure_never_reports_fresh_or_pass() -> None:
    evidence = _evidence(
        cloud_native_sources=cloud_native_authorities(
            objects=[BROKEN_OBJECT], normalized_batch_key=BROKEN_OBJECT["object_key"],
            private_database_paths=[], github_release=None,
            observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY,
            canonical=CANONICAL_LOST,
        )
    )
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    assert snapshot["coverage"]["product_state"] == "FAILED"
    assert snapshot["freshness"]["state"] != "FRESH"


def test_optional_cloud_source_missing_does_not_fail_the_product() -> None:
    # The GitHub private release is the long-term backup. Losing it is a real
    # gap, but the product can still render today's facts, so it must degrade
    # rather than report FAILED.
    evidence = _evidence(
        cloud_native_sources=cloud_native_authorities(
            objects=[VERIFIED_OBJECT], normalized_batch_key=VERIFIED_OBJECT["object_key"],
            private_database_paths=["memory-atlas/runs/latest.json"], github_release=None,
            observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY,
        )
    )
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    rows = {row["source_id"]: row for row in snapshot["coverage"]["sources"]}
    assert rows["github_private_release"]["required_for_product"] is False
    assert rows["github_private_release"]["state"] == "MISSING"
    assert snapshot["coverage"]["product_state"] == "DEGRADED"
    assert snapshot["freshness"]["state"] != "FRESH"


def test_local_tier_b_gap_makes_metrics_stale_without_blocking_the_product() -> None:
    """MA-LIVE-AC-009: "Tier B 本机来源缺失只使相关指标陈旧；Tier A 权威缺失禁止
    宣称 fresh/pass". This used to degrade the whole product for any Tier B gap,
    which is stricter than the contract and made DEGRADED permanent — the Owner
    has no ChatGPT exports, so that row can never become READY.

    The gap is never hidden: the row keeps its real state and the reason names
    it. What changed is that it no longer blocks the product."""
    private = _private()
    run = _run_block()
    run["source_coverages"] = [
        {"source_id": "codex_state", "label_zh": "Codex 状态数据库", "required": True, "state": "READY"},
        {"source_id": "chatgpt_exports", "label_zh": "ChatGPT 导出", "required": False, "state": "MISSING_OPTIONAL"},
    ]
    private["run"] = run
    snapshot = build_live_snapshot(private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    rows = {row["source_id"]: row for row in snapshot["coverage"]["sources"]}
    assert rows["chatgpt_exports"]["required_for_product"] is False
    assert rows["chatgpt_exports"]["tier"] == "B_LOCAL_OPTIONAL"
    assert snapshot["coverage"]["product_state"] == "PASS"


def test_a_tier_b_source_that_broke_is_named_even_though_it_does_not_block() -> None:
    private = _private()
    run = _run_block()
    run["source_coverages"] = [
        {"source_id": "codex_memories", "label_zh": "Codex 记忆", "required": False, "state": "UNREADABLE"},
    ]
    private["run"] = run
    snapshot = build_live_snapshot(private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    assert snapshot["coverage"]["product_state"] == "PASS"
    # Not blocking is not the same as not reporting.
    assert "Codex 记忆" in snapshot["freshness"]["reason_zh"]
    assert "相关指标按陈旧处理" in snapshot["freshness"]["reason_zh"]
    assert next(r for r in snapshot["coverage"]["sources"] if r["source_id"] == "codex_memories")["state"] == "FAILED"


def test_a_tier_a_authority_that_is_not_ready_still_blocks_fresh() -> None:
    """The other half of AC-009, which must not move: a cloud authority that is
    not ready forbids claiming fresh, whether or not it is required."""
    evidence = _evidence(
        cloud_native_sources=cloud_native_authorities(
            objects=[BROKEN_OBJECT], normalized_batch_key=BROKEN_OBJECT["object_key"],
            private_database_paths=["memory-atlas/runs/latest.json"], github_release=None,
            observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY, canonical=CANONICAL_READY,
        )
    )
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    assert snapshot["coverage"]["product_state"] == "DEGRADED"
    assert snapshot["freshness"]["state"] != "FRESH"


def test_registry_declares_the_tier_of_every_source() -> None:
    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    for row in registry["sources"]:
        assert row["availability_tier"] == "B_LOCAL_OPTIONAL", row["source_id"]
        assert row["required_for_product"] is False, row["source_id"]
    ids = {row["source_id"] for row in registry["cloud_native_authorities"]}
    assert ids == {
        "r2_primary_objects", "r2_normalized_events", "private_database_facts",
        "github_canonical_events", "github_private_release",
    }
    # After the 2026-08-04 migration the data pressure sits on the GitHub
    # private repository. R2 may be empty without failing the product; the
    # canonical event stream may not.
    required = {row["source_id"] for row in registry["cloud_native_authorities"] if row["required_for_product"]}
    assert required == {"private_database_facts", "github_canonical_events"}
    assert registry["primary_data_authority"]["state"] == "GITHUB_PRIVATE_REPOSITORY"
    assert registry["primary_data_authority"]["repository"] == "LinzeColin/Private-Database"


def test_a_stale_but_healthy_run_is_stale_not_failed() -> None:
    # Everything read back fine; the data is simply older than the target. That
    # is a freshness fact, not an availability failure, and last-good stays.
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(
        private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T12:00:00Z"
    )
    assert snapshot["freshness"]["state"] == "STALE"
    assert snapshot["coverage"]["product_state"] == "DEGRADED"
    assert snapshot["freshness"]["age_seconds"] == 6300


def test_recovery_returns_to_fresh_and_pass() -> None:
    # The same inputs that failed above, once the authority reads succeed again.
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(
        private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z"
    )
    assert snapshot["coverage"]["product_state"] == "PASS"
    assert snapshot["freshness"]["state"] == "FRESH"


def test_degraded_reason_names_the_source_instead_of_a_generic_sentence() -> None:
    evidence = _evidence(
        cloud_native_sources=cloud_native_authorities(
            objects=[VERIFIED_OBJECT], normalized_batch_key=VERIFIED_OBJECT["object_key"],
            private_database_paths=["memory-atlas/runs/latest.json"], github_release=None,
            observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY,
            canonical=CANONICAL_LOST,
        )
    )
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    assert "GitHub 私有仓全量事件流" in snapshot["freshness"]["reason_zh"]


def _walk(value, path="$"):
    if isinstance(value, dict):
        for key, child in value.items():
            yield f"{path}.{key}", key, child
            yield from _walk(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield f"{path}[{index}]", "", child
            yield from _walk(child, f"{path}[{index}]")


def test_snapshot_never_carries_object_keys_paths_or_digests() -> None:
    snapshot = _snapshot()
    # `privacy.object_keys_included` is the declaration, not a leak, so keys and
    # values are checked separately rather than grepping the serialized blob.
    for where, key, child in _walk(snapshot):
        assert key not in {"object_key", "sha256", "readback_sha256", "relative_path", "payload"}, where
        if isinstance(child, str):
            for forbidden in ("primary-objects/", "private-agentdatabase/", "/srv/linze", "$HOME", "a" * 64):
                assert forbidden not in child, f"{where}: {forbidden}"


class _FakeStore:
    """Only the two calls the supersession path makes."""

    def __init__(self, present: dict[str, str], manifest: dict | None):
        self.present = present
        self.manifest = manifest

    def exists_with_hash(self, key: str, digest: str) -> bool:
        return self.present.get(key) == digest

    def get_file(self, key: str, target) -> None:
        from pathlib import Path as _P

        if key == "private-agentdatabase/normalized/canonical/MANIFEST.json" and self.manifest is not None:
            _P(target).write_text(json.dumps(self.manifest), encoding="utf-8")
            return
        raise FileNotFoundError(key)


CANONICAL = "primary-objects/memory-atlas/private-agentdatabase/normalized/canonical/events.jsonl"
DELETED = "primary-objects/memory-atlas/private-agentdatabase/normalized/marun_x/events.jsonl"
CANONICAL_SHA = "7b" + "0" * 62


def _manifest() -> dict:
    return {"object": CANONICAL, "sha256": CANONICAL_SHA, "unique_events": 122080, "supersedes": [DELETED]}


def test_supersession_record_is_read_from_the_deletion_time_manifest(tmp_path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import load_supersession

    record = load_supersession(_FakeStore({}, _manifest()), tmp_path)
    assert record["available"] is True
    assert record["canonical_object"] == CANONICAL
    assert DELETED in record["superseded"]


def test_a_missing_manifest_never_excuses_a_missing_object(tmp_path) -> None:
    # No record means no permission to treat a deletion as intentional.
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import load_supersession

    record = load_supersession(_FakeStore({}, None), tmp_path)
    assert record["available"] is False
    assert record["superseded"] == set()


def test_supersession_requires_the_replacement_to_still_verify(tmp_path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import load_supersession

    store = _FakeStore({}, _manifest())
    record = load_supersession(store, tmp_path)
    # The canonical object is absent from the store, so the guard the reconcile
    # applies — exists_with_hash on the replacement — is what refuses it.
    assert store.exists_with_hash(record["canonical_object"], record["sha256"]) is False


def test_reconcile_treats_superseded_and_lost_differently() -> None:
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    assert "if key and canonical.covers(key):" in source
    assert 'missing.append(key or "<missing-key>")' in source
    assert '"superseded_by_canonical"' in source
    canonical = (
        Path(__file__).resolve().parents[1] / "scripts" / "memory_atlas_private" / "canonical_source.py"
    ).read_text(encoding="utf-8")
    # `covers` may only answer yes off a resolution that verified its digest.
    assert "return self.available and (object_key in self.superseded or object_key == self.canonical_object)" in canonical


def test_publisher_refuses_to_publish_zeros_when_the_run_counted_events() -> None:
    """Production published a snapshot whose analysis was over 0 events while the
    run had just counted 122,080, because behavior_economics deliberately keeps
    no raw payloads and the publisher read them from there. A zero presented as
    the current reading is the one thing the failure contract forbids."""
    source = (
        Path(__file__).resolve().parents[1] / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    assert "refusing to publish zeros" in source
    assert "if declared and not rows:" in source
    # Both callers must hand over the events they actually have.
    assert "events=live_events," in source
    assert "events=[asdict(event) for event in all_events]," in source


def test_normalized_events_are_projected_onto_the_visual_contract() -> None:
    """The first attempt at real events raised `event[0].activity_type is
    required`: this repository's event model says `activity`, the v0.0.0.32
    visual contract says `activity_type`, and `model_tool` does not exist at
    all. Handing raw records over also carried object_sha256, relative_path and
    payload toward the browser."""
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import visual_event
    from OpenAIDatabase.scripts.memory_atlas_private.visual_analytics import build_visual_analytics

    raw = {
        "event_id": "e1",
        "occurred_at": "2026-08-03T10:00:00Z",
        "activity": "development_deployment",
        "outcome_state": "deployed",
        "source_id": "codex_sessions",
        "effort_minutes": 30.0,
        "evidence_ref": "private-db://memory-atlas/runs/x.json",
        "object_sha256": "a" * 64,
        "relative_path": "/Users/someone/.codex/sessions/s.jsonl",
        "payload": {"prompt": "raw text"},
    }
    projected = visual_event(raw)
    assert projected["activity_type"] == "development_deployment"
    assert projected["model_tool"] == "codex_sessions"
    assert projected["work_time_minutes"] == 30.0
    assert projected["outcome_evidence"] is True
    assert set(projected) == {
        "event_id", "occurred_at", "activity_type", "outcome_state",
        "model_tool", "work_time_minutes", "outcome_evidence", "verified_at",
    }
    serialized = json.dumps(build_visual_analytics([projected]), ensure_ascii=False)
    for forbidden in ("a" * 64, "/Users/", "raw text", "prompt"):
        assert forbidden not in serialized, forbidden


def test_an_event_missing_its_activity_still_produces_a_usable_row() -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import visual_event

    projected = visual_event({"event_id": "e", "occurred_at": "2026-08-03T10:00:00Z", "outcome_state": "unknown"})
    assert projected["activity_type"] == "unknown"
    assert projected["model_tool"] == "unknown"
    assert projected["work_time_minutes"] is None
    assert projected["outcome_evidence"] is False


def test_canonical_readback_alone_satisfies_the_object_authority_gate() -> None:
    """After the migration R2 is drained, so `r2_readback` is honestly NOT_RUN.
    The gate is about whether the event bytes were hashed against a declared
    digest, not about which company stored them."""
    evidence = _evidence(
        same_run_evidence=same_run_evidence_rows(
            run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3",
            r2_readback=None, private_database_readback=True, ovh_reconcile=True,
            status_projection=True, canonical_source_readback=True,
            ref="private-db://memory-atlas/runs/latest.json",
        )
    )
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")
    assert snapshot["truth"]["same_run_evidence"]["canonical_source_readback"]["state"] == "PASS"
    assert snapshot["truth"]["same_run_evidence"]["r2_readback"]["state"] == "NOT_RUN"


def test_no_object_authority_readback_at_all_is_refused() -> None:
    # Weakening the gate to "R2 is optional now" must not weaken it to nothing.
    evidence = _evidence(
        same_run_evidence=same_run_evidence_rows(
            run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3",
            r2_readback=None, private_database_readback=True, ovh_reconcile=True,
            status_projection=True, canonical_source_readback=None,
        )
    )
    private = _private()
    private["run"] = _run_block()
    with pytest.raises(LiveSnapshotError, match="no object authority readback passed"):
        build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")


def test_a_failed_canonical_readback_is_not_quietly_treated_as_absent() -> None:
    evidence = _evidence(
        same_run_evidence=same_run_evidence_rows(
            run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3",
            r2_readback=None, private_database_readback=True, ovh_reconcile=True,
            status_projection=True, canonical_source_readback=False,
        )
    )
    private = _private()
    private["run"] = _run_block()
    with pytest.raises(LiveSnapshotError, match="no object authority readback passed"):
        build_live_snapshot(private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z")


def test_the_store_gate_matches_the_adapter_gate() -> None:
    """The adapter and the store both gate on authority evidence. When only the
    adapter was made provider-neutral the reconcile passed and then refused to
    publish with `authority evidence mismatch: r2_readback`, which is the exact
    shape of a half-migration: green upstream, silently stale downstream."""
    from OpenAIDatabase.scripts.memory_atlas_private.live_snapshot_store import (
        LiveSnapshotStore,
        SnapshotStoreError,
    )

    snapshot = _snapshot(
        run=normalize_live_run_block(
            {"run_id": "marun-20260803T101500Z-a1b2c3", "state": "REFRESHING_ATLAS", "source_coverages": []},
            run_id="marun-20260803T101500Z-a1b2c3", trace_id="marun-20260803T101500Z-a1b2c3",
            state="REBUILT_FROM_AUTHORITIES", started_at="2026-08-03T10:00:00Z",
            completed_at="2026-08-03T10:15:00Z",
        )
    )
    store = LiveSnapshotStore.__new__(LiveSnapshotStore)
    store.schema = json.loads(SCHEMA.read_text(encoding="utf-8"))
    import jsonschema

    store.validator = jsonschema.Draft202012Validator(store.schema, format_checker=jsonschema.FormatChecker())

    drained = json.loads(json.dumps(snapshot))
    drained["truth"]["same_run_evidence"]["r2_readback"] = {
        "state": "NOT_RUN", "run_id": None, "trace_id": None, "ref": None
    }
    store.validate(drained)  # canonical readback carries it

    blind = json.loads(json.dumps(drained))
    blind["truth"]["same_run_evidence"]["canonical_source_readback"] = {
        "state": "NOT_RUN", "run_id": None, "trace_id": None, "ref": None
    }
    with pytest.raises(SnapshotStoreError, match="canonical_source_readback/r2_readback"):
        store.validate(blind)

    borrowed = json.loads(json.dumps(drained))
    borrowed["truth"]["same_run_evidence"]["canonical_source_readback"]["run_id"] = "marun-someone-else"
    with pytest.raises(SnapshotStoreError, match="canonical_source_readback/r2_readback"):
        store.validate(borrowed)


def _store(tmp_path):
    from OpenAIDatabase.scripts.memory_atlas_private.live_snapshot_store import LiveSnapshotStore

    return LiveSnapshotStore(tmp_path, SCHEMA)


def test_re_reconciling_an_unchanged_run_keeps_the_page_current(tmp_path) -> None:
    """The defect this pins: history was compared byte-for-byte, so the second
    reconcile of the same source run raised `immutable history conflict` and
    `current.json` stopped moving. The reconcile still reported PASS, so the
    page served a snapshot that aged all day — 27,753 seconds by the time the
    golden transaction read it — with nothing anywhere reporting a failure."""
    store = _store(tmp_path)
    first = _snapshot()
    store.publish(first)
    later = json.loads(json.dumps(first))
    later["freshness"]["age_seconds"] = first["freshness"]["age_seconds"] + 3600
    later["run"]["reconciled_at"] = "2026-08-03T11:20:00Z"
    store.publish(later)
    current = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert current["freshness"]["age_seconds"] == later["freshness"]["age_seconds"]
    # History still holds what the run first said, untouched.
    history = json.loads((tmp_path / "history" / f"{first['run']['run_id']}.json").read_text(encoding="utf-8"))
    assert history["freshness"]["age_seconds"] == first["freshness"]["age_seconds"]


def test_the_same_run_may_not_change_what_it_concluded(tmp_path) -> None:
    # The property the byte comparison was protecting, kept exactly.
    store = _store(tmp_path)
    store.publish(_snapshot())
    rewritten = json.loads(json.dumps(_snapshot()))
    rewritten["analysis"]["event_count"] = rewritten["analysis"]["event_count"] + 1
    with pytest.raises(Exception, match="immutable history conflict"):
        store.publish(rewritten)


def test_a_changed_visual_is_also_a_conflict(tmp_path) -> None:
    store = _store(tmp_path)
    store.publish(_snapshot())
    rewritten = json.loads(json.dumps(_snapshot()))
    rewritten["visuals"][0]["rows"] = []
    with pytest.raises(Exception, match="immutable history conflict"):
        store.publish(rewritten)


def test_storage_provider_changing_is_not_a_conclusion_change(tmp_path) -> None:
    """Reading the same events from GitHub instead of R2 does not change what
    the run concluded, so it must not look like history being rewritten."""
    store = _store(tmp_path)
    store.publish(_snapshot())
    migrated = json.loads(json.dumps(_snapshot()))
    migrated["truth"]["same_run_evidence"]["r2_readback"] = {
        "state": "NOT_RUN", "run_id": None, "trace_id": None, "ref": None
    }
    store.publish(migrated)
    current = json.loads((tmp_path / "current.json").read_text(encoding="utf-8"))
    assert current["truth"]["same_run_evidence"]["r2_readback"]["state"] == "NOT_RUN"


def test_a_growing_incident_ledger_is_not_a_rewritten_history(tmp_path) -> None:
    """`analysis.failure_compound` is the live incident ledger. Recording an
    incident — which is what a healthy system does when something breaks — made
    the next reconcile of the same run raise `immutable history conflict`, so
    the page stopped updating precisely when there was something to report."""
    store = _store(tmp_path)
    first = _snapshot()
    store.publish(first)
    later = json.loads(json.dumps(first))
    ledger = later["analysis"]["failure_compound"]
    ledger["incident_count"] = int(ledger.get("incident_count") or 0) + 1
    later["freshness"]["age_seconds"] = first["freshness"]["age_seconds"] + 900
    assert store.publish(later)["state"] == "REFRESHED"


def test_a_conflict_names_the_part_that_differs(tmp_path) -> None:
    # "immutable history conflict" with no subject cost a diagnosis cycle.
    store = _store(tmp_path)
    store.publish(_snapshot())
    rewritten = json.loads(json.dumps(_snapshot()))
    rewritten["analysis"]["event_count"] = 999
    with pytest.raises(Exception, match=r"immutable history conflict: analysis\.event_count"):
        store.publish(rewritten)


# --- Two labels that made "unusable" a permanent state ------------------------

def test_freshness_target_comes_from_the_declared_capture_cadence() -> None:
    """1800 seconds against a once-a-day capture meant STALE ~98% of the time,
    so the freshness signal carried no information at all."""
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import capture_freshness_target

    registry = json.loads(REGISTRY.read_text(encoding="utf-8"))
    cadence = registry["source_capture_cadence"]
    assert cadence["rrule"] == "FREQ=DAILY;BYHOUR=3;BYMINUTE=0"
    assert cadence["cadence_seconds"] == 86400
    assert cadence["freshness_target_seconds"] == cadence["cadence_seconds"] + cadence["grace_seconds"]
    assert capture_freshness_target(REGISTRY) == cadence["freshness_target_seconds"]
    # A missing or malformed declaration must not silently widen the window.
    assert capture_freshness_target(Path("/does/not/exist.json")) == 1800


def test_a_capture_that_missed_its_slot_is_still_stale() -> None:
    """The widened target is not a licence. Two missed daily runs must still
    read as STALE — that is the whole point of the signal."""
    private = _private()
    private["run"] = _run_block()
    two_days_late = build_live_snapshot(
        private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-05T12:00:00Z",
        freshness_target_seconds=97_200,
    )
    assert two_days_late["freshness"]["state"] == "STALE"
    assert two_days_late["coverage"]["product_state"] == "DEGRADED"
    on_time = build_live_snapshot(
        private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-04T02:00:00Z",
        freshness_target_seconds=97_200,
    )
    assert on_time["freshness"]["state"] == "FRESH"
    assert on_time["coverage"]["product_state"] == "PASS"


MIGRATION_PROVEN = {
    "manifest_object_count": 2302,
    "canonical_covered_objects": 1,
    "migrated_to_github_objects": 2301,
    "github_backup_coverage": {"state": "COVERED"},
}


def _migrated_authorities(**overrides):
    return cloud_native_authorities(
        objects=[BROKEN_OBJECT], normalized_batch_key=BROKEN_OBJECT["object_key"],
        private_database_paths=["memory-atlas/runs/latest.json"],
        github_release=RELEASE_BACKUP_PASS,
        observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY, canonical=CANONICAL_READY,
        migration={**MIGRATION_PROVEN, **overrides},
    )


def _row(rows, source_id):
    return next(row for row in rows if row["source_id"] == source_id)


def test_a_drained_bucket_with_proof_is_migrated_not_failed() -> None:
    """R2 was drained on purpose. Reporting it FAILED forever made the product
    permanently DEGRADED for a state that is exactly as designed."""
    rows = _migrated_authorities()
    assert _row(rows, "r2_primary_objects")["state"] == "MIGRATED"
    assert _row(rows, "r2_normalized_events")["state"] == "MIGRATED"
    # The authority that actually holds the bytes is unaffected.
    assert _row(rows, "github_canonical_events")["state"] == "READY"


@pytest.mark.parametrize(
    "broken",
    [
        {"migrated_to_github_objects": 0},                      # nothing was covered
        {"manifest_object_count": 9000},                        # the count does not add up
        {"github_backup_coverage": {"state": "ABSENT"}},        # the archive is gone
        {"github_backup_coverage": {"state": "INSUFFICIENT"}},  # the archive is short
    ],
)
def test_without_per_object_proof_a_drained_bucket_is_still_failed(broken: dict) -> None:
    """"We moved it" has to be shown. Otherwise it becomes an excuse for data
    that simply vanished — which is the exact failure this path must catch."""
    rows = _migrated_authorities(**broken)
    assert _row(rows, "r2_primary_objects")["state"] == "FAILED"


def test_migrated_sources_do_not_degrade_the_product() -> None:
    evidence = _evidence(cloud_native_sources=_migrated_authorities())
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(
        private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z",
        freshness_target_seconds=97_200,
    )
    assert snapshot["coverage"]["product_state"] == "PASS"
    assert snapshot["coverage"]["tier_a_cloud_native"]["migrated"] == 2
    assert snapshot["coverage"]["tier_a_cloud_native"]["failed"] == 0
    assert {row["state"] for row in snapshot["coverage"]["sources"] if row["source_id"].startswith("r2_")} == {"MIGRATED"}


def test_a_genuinely_failed_source_still_degrades() -> None:
    # The migration path must not become a blanket amnesty.
    evidence = _evidence(cloud_native_sources=_migrated_authorities(migrated_to_github_objects=0))
    private = _private()
    private["run"] = _run_block()
    snapshot = build_live_snapshot(
        private, _visual(), evidence, _benchmark(), evaluated_at="2026-08-03T10:20:00Z",
        freshness_target_seconds=97_200,
    )
    assert snapshot["coverage"]["product_state"] == "DEGRADED"


def _with_backup(record):
    return cloud_native_authorities(
        objects=[VERIFIED_OBJECT], normalized_batch_key=VERIFIED_OBJECT["object_key"],
        private_database_paths=["memory-atlas/runs/latest.json"], github_release=record,
        observed_at="2026-08-03T10:15:00Z", registry_path=REGISTRY, canonical=CANONICAL_READY,
    )


def test_the_backup_row_reads_the_fields_its_producer_writes() -> None:
    """`PrivateReleaseBackup` writes `parts`, `state`, `remote_readback_verified`
    and `isolated_restore`. The row looked for `files`, which it has never
    written — so a backup that passed its own contract reported FAILED with 0
    objects and degraded the product permanently."""
    row = _row(_with_backup(RELEASE_BACKUP_PASS), "github_private_release")
    assert row["state"] == "READY"
    assert row["object_count"] == 8
    assert row["size_bytes"] == 698130810


@pytest.mark.parametrize(
    "broken",
    [
        {"state": "FAILED"},
        {"remote_readback_verified": False},
        {"isolated_restore": {"state": "FAILED", "all_hashes_match": True}},
        {"isolated_restore": {"state": "PASS", "all_hashes_match": False}},
    ],
)
def test_a_backup_that_did_not_pass_still_reports_failed(broken: dict) -> None:
    row = _row(_with_backup({**RELEASE_BACKUP_PASS, **broken}), "github_private_release")
    assert row["state"] == "FAILED"


def test_no_backup_record_at_all_is_missing() -> None:
    assert _row(_with_backup(None), "github_private_release")["state"] == "MISSING"


def _tier_b(*states):
    return [
        {"source_id": f"src_{i}", "label_zh": f"来源{i}", "availability_tier": "B_LOCAL_OPTIONAL",
         "required": False, "required_for_product": False, "state": state, "object_count": 0}
        for i, state in enumerate(states)
    ]


def _snapshot_with_tier_b(*states):
    private = _private()
    private["run"] = _run_block()
    private["run"]["source_coverages"] = _tier_b(*states)
    return build_live_snapshot(
        private, _visual(), _evidence(), _benchmark(), evaluated_at="2026-08-03T10:20:00Z",
        freshness_target_seconds=97_200,
    )


def test_an_optional_source_the_capture_calls_missing_optional_is_not_a_gap() -> None:
    """The capture already distinguishes "declared optional and absent" from
    "should be here and is not". Collapsing both into MISSING made five sources
    the Owner simply does not have degrade the product forever."""
    snapshot = _snapshot_with_tier_b("MISSING_OPTIONAL", "MISSING_OPTIONAL")
    assert snapshot["coverage"]["product_state"] == "PASS"
    assert snapshot["coverage"]["tier_b_local_optional"]["missing_optional"] == 2
    # Still visible, not hidden.
    assert {row["state"] for row in snapshot["coverage"]["sources"] if row["source_id"].startswith("src_")} == {"MISSING_OPTIONAL"}


def test_an_unreadable_tier_b_source_is_named_but_does_not_block() -> None:
    """UNREADABLE means something was there and could not be read — a real gap,
    and the reason must name it. Per MA-LIVE-AC-009 a Tier B gap only makes the
    related metrics stale, so it is reported without blocking the product.

    The state itself is not softened: the row still reads FAILED."""
    snapshot = _snapshot_with_tier_b("MISSING_OPTIONAL", "UNREADABLE")
    assert snapshot["coverage"]["product_state"] == "PASS"
    assert "来源1" in snapshot["freshness"]["reason_zh"]
    # A source that is optional and absent is not a gap and is not named.
    assert "来源0" not in snapshot["freshness"]["reason_zh"]
    states = {row["source_id"]: row["state"] for row in snapshot["coverage"]["sources"]}
    assert states["src_1"] == "FAILED" and states["src_0"] == "MISSING_OPTIONAL"


def test_a_plain_missing_tier_b_source_is_named_but_does_not_block() -> None:
    snapshot = _snapshot_with_tier_b("MISSING")
    assert snapshot["coverage"]["product_state"] == "PASS"
    assert "来源0" in snapshot["freshness"]["reason_zh"]
    assert snapshot["coverage"]["tier_b_local_optional"]["missing"] == 1


def test_a_code_fix_may_change_what_a_run_concludes(tmp_path) -> None:
    """The rule is "the same run under the same code may not change its
    conclusions". Without the commit in the fingerprint it read as "may never
    change", and it blocked a correction: fixing the truncated event union made
    run marun_d8019f8 legitimately conclude 127,712 instead of 114,024, and the
    store refused to publish the fix."""
    store = _store(tmp_path)
    before = _snapshot()
    store.publish(before)
    after = json.loads(json.dumps(before))
    after["analysis"]["event_count"] = before["analysis"]["event_count"] + 13_688
    after["release"]["repository_commit"] = "d0c50b50" + "0" * 32
    assert store.publish(after)["state"] == "REFRESHED"


def test_the_same_run_under_the_same_code_still_may_not_change(tmp_path) -> None:
    # The guarantee this protects, unchanged.
    store = _store(tmp_path)
    store.publish(_snapshot())
    rewritten = json.loads(json.dumps(_snapshot()))
    rewritten["analysis"]["event_count"] += 1
    with pytest.raises(Exception, match="immutable history conflict"):
        store.publish(rewritten)


def test_the_first_derivation_of_a_run_stays_on_the_record(tmp_path) -> None:
    """A re-derivation must not overwrite what the run first concluded — that is
    the whole point of immutable history. It gets its own object instead."""
    store = _store(tmp_path)
    before = _snapshot()
    store.publish(before)
    after = json.loads(json.dumps(before))
    after["analysis"]["event_count"] = 127_712
    after["release"]["repository_commit"] = "d0c50b50" + "0" * 32
    store.publish(after)

    history = sorted(p.name for p in (tmp_path / "history").glob("*.json"))
    run_id = before["run"]["run_id"]
    assert history == [f"{run_id}.d0c50b500000.json", f"{run_id}.json"]
    first = json.loads((tmp_path / "history" / f"{run_id}.json").read_text(encoding="utf-8"))
    assert first["analysis"]["event_count"] == before["analysis"]["event_count"]
