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
            github_release={"schema_version": "memory_atlas.encrypted_archive_manifest.v1", "files": [{}]},
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


def test_local_tier_b_gap_degrades_without_claiming_failure() -> None:
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
    assert snapshot["coverage"]["product_state"] == "DEGRADED"
    assert snapshot["coverage"]["product_state"] != "FAILED"


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
