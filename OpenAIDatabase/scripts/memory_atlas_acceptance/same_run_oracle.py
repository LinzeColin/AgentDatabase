from __future__ import annotations
"""Reject evidence stitched from different runs, traces, releases or deployments."""
import argparse, json
from pathlib import Path
from typing import Any, Mapping

CORE = ("r2_readback", "private_database_readback", "ovh_reconcile", "api_snapshot", "browser_receipt", "status_projection")
STABLE = CORE + ("restore_receipt",)
DEPLOYMENT_LAYERS = {"api_snapshot", "browser_receipt", "status_projection", "restore_receipt"}


def evaluate(snapshot: Mapping[str, Any], receipts: Mapping[str, Any], *, mode: str = "stable") -> dict[str, Any]:
    run = snapshot["run"]
    release = snapshot["release"]
    rows = receipts.get("receipts") if isinstance(receipts.get("receipts"), Mapping) else {}
    required = STABLE if mode == "stable" else CORE
    checks = []
    for name in required:
        row = rows.get(name) if isinstance(rows.get(name), Mapping) else {}
        passed = row.get("state") == "PASS" and row.get("run_id") == run["run_id"] and row.get("trace_id") == run["trace_id"]
        if name in DEPLOYMENT_LAYERS:
            if release.get("release_id") is not None:
                passed = passed and row.get("release_id") == release["release_id"]
            if release.get("deployment_revision") is not None:
                passed = passed and row.get("deployment_revision") == release["deployment_revision"]
        checks.append({
            "component": name,
            "pass": bool(passed),
            "actual": {
                "state": row.get("state"), "run_id": row.get("run_id"), "trace_id": row.get("trace_id"),
                "release_id": row.get("release_id"), "deployment_revision": row.get("deployment_revision"),
            },
        })
    return {
        "schema_version": "memory_atlas.same_run_oracle.v1",
        "mode": mode,
        "verdict": "PASS" if all(row["pass"] for row in checks) else "FAIL",
        "run_id": run["run_id"], "trace_id": run["trace_id"],
        "release_id": release.get("release_id"), "deployment_revision": release.get("deployment_revision"),
        "mismatch_count": sum(1 for row in checks if not row["pass"]), "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--receipts", type=Path, required=True)
    parser.add_argument("--mode", choices=("core", "stable"), default="stable")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.snapshot.read_text()), json.loads(args.receipts.read_text()), mode=args.mode)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    raise SystemExit(0 if report["verdict"] == "PASS" else 2)


if __name__ == "__main__":
    main()
