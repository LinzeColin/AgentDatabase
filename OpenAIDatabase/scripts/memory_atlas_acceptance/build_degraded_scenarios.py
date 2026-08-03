from __future__ import annotations

"""v0.0.0.32 T06 — build the degraded-path scenarios with the real adapter.

Hand-edited JSON would only prove that hand-edited JSON renders. Every scenario
here goes through `build_live_snapshot`, so what the browser is shown is what
the production adapter would actually emit for that failure.
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from OpenAIDatabase.scripts.memory_atlas_private.live_snapshot_adapter import (  # noqa: E402
    build_live_snapshot,
)
from OpenAIDatabase.scripts.memory_atlas_private.pipeline import (  # noqa: E402
    cloud_native_authorities,
    normalize_live_run_block,
    same_run_evidence_rows,
)

FIXTURES = REPO / "OpenAIDatabase" / "fixtures"
REGISTRY = REPO / "ops" / "memory-atlas" / "source-registry.json"
RUN_ID = "marun-20260803T101500Z-scenario"
COMPLETED_AT = "2026-08-03T10:15:00Z"
FRESH_AT = "2026-08-03T10:20:00Z"
STALE_AT = "2026-08-03T12:00:00Z"

GOOD_OBJECT = {
    "sha256": "a" * 64, "object_key": "primary-objects/memory-atlas/x", "size_bytes": 4096,
    "operation": "CREATED", "readback_sha256": "a" * 64, "readback_verified": True, "provider_version": "r2",
}
BROKEN_OBJECT = {**GOOD_OBJECT, "readback_sha256": "b" * 64, "readback_verified": False}
HEALTHY_LOCAL = [
    {"source_id": "codex_state", "label_zh": "Codex 状态数据库", "required": True, "state": "READY", "object_count": 1},
    {"source_id": "codex_sessions", "label_zh": "Codex 活跃会话", "required": True, "state": "READY", "object_count": 42},
]
DEGRADED_LOCAL = HEALTHY_LOCAL + [
    {"source_id": "chatgpt_exports", "label_zh": "ChatGPT 导出", "required": False, "state": "MISSING_OPTIONAL", "object_count": 0},
]


def _fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text(encoding="utf-8"))


def _build(*, objects, github_release, local_sources, evaluated_at) -> dict:
    private = _fixture("private_analytics.synthetic.json")
    run = normalize_live_run_block(
        {"run_id": RUN_ID, "state": "REFRESHING_ATLAS", "source_coverages": local_sources},
        run_id=RUN_ID, trace_id=RUN_ID, state="REBUILT_FROM_AUTHORITIES",
        started_at="2026-08-03T10:00:00Z", completed_at=COMPLETED_AT, reconciled_at=evaluated_at,
    )
    private["run"] = run
    evidence = {
        "schema_version": "memory_atlas.runtime_evidence.v1",
        "generated_at": evaluated_at,
        "run_id": RUN_ID,
        "trace_id": RUN_ID,
        "release": {"identity_state": "OBSERVED", "repository_commit": None, "release_id": "20260803T101000Z-scenario", "artifact_digest": None, "deployment_revision": "memory-atlas-blue-scenario"},
        "cloud_native_sources": cloud_native_authorities(
            objects=objects, normalized_batch_key=objects[0]["object_key"] if objects else None,
            private_database_paths=["memory-atlas/runs/latest.json"], github_release=github_release,
            observed_at=COMPLETED_AT, registry_path=REGISTRY,
        ),
        "same_run_evidence": same_run_evidence_rows(
            run_id=RUN_ID, trace_id=RUN_ID, r2_readback=True, private_database_readback=True,
            ovh_reconcile=True, status_projection=True, ref=f"private-db://memory-atlas/runs/{RUN_ID}.json",
        ),
    }
    return build_live_snapshot(
        private, _fixture("visual_analytics.synthetic.json"), evidence,
        _fixture("benchmark_result.synthetic.json"), evaluated_at=evaluated_at,
    )


SCENARIOS = {
    # name: (expected product_state, expected freshness state, builder kwargs)
    "01-healthy": ("PASS", "FRESH", dict(objects=[GOOD_OBJECT], github_release={"files": [{}]}, local_sources=HEALTHY_LOCAL, evaluated_at=FRESH_AT)),
    "02-tier-b-local-source-missing": ("DEGRADED", "DEGRADED", dict(objects=[GOOD_OBJECT], github_release={"files": [{}]}, local_sources=DEGRADED_LOCAL, evaluated_at=FRESH_AT)),
    "03-optional-cloud-backup-missing": ("DEGRADED", "DEGRADED", dict(objects=[GOOD_OBJECT], github_release=None, local_sources=HEALTHY_LOCAL, evaluated_at=FRESH_AT)),
    "04-stale-but-healthy": ("DEGRADED", "STALE", dict(objects=[GOOD_OBJECT], github_release={"files": [{}]}, local_sources=HEALTHY_LOCAL, evaluated_at=STALE_AT)),
    "05-required-cloud-authority-failed": ("FAILED", "DEGRADED", dict(objects=[BROKEN_OBJECT], github_release={"files": [{}]}, local_sources=HEALTHY_LOCAL, evaluated_at=FRESH_AT)),
    "06-recovered": ("PASS", "FRESH", dict(objects=[GOOD_OBJECT], github_release={"files": [{}]}, local_sources=HEALTHY_LOCAL, evaluated_at=FRESH_AT)),
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    index = []
    for name, (product, freshness, kwargs) in SCENARIOS.items():
        snapshot = _build(**kwargs)
        assert snapshot["coverage"]["product_state"] == product, (name, snapshot["coverage"]["product_state"])
        assert snapshot["freshness"]["state"] == freshness, (name, snapshot["freshness"]["state"])
        path = args.output_dir / f"{name}.json"
        path.write_text(json.dumps(snapshot, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
        index.append({
            "scenario": name,
            "file": path.name,
            "expected_product_state": product,
            "expected_freshness_state": freshness,
            "reason_zh": snapshot["freshness"]["reason_zh"],
        })
    (args.output_dir / "index.json").write_text(json.dumps({"schema_version": "memory_atlas.degraded_scenarios.v1", "scenarios": index}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(index, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
