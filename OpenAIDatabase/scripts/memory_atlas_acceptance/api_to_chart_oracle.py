from __future__ import annotations
"""Compare API LiveSnapshot with values and identities read from the rendered browser DOM."""
import argparse, json, math
from pathlib import Path
from typing import Any, Mapping


def expected(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    analysis = snapshot["analysis"]
    return {
        "event_count": analysis["event_count"],
        "verified_outcome_rate_event": analysis["verified_outcome_rate_event"]["value"],
        "verified_outcome_rate_work_time": analysis["verified_outcome_rate_work_time"]["value"],
        "work_time_coverage_rate": analysis["work_time_coverage_rate"]["value"],
        "outcome_evidence_coverage_rate": analysis["outcome_evidence_coverage_rate"]["value"],
        "verification_debt_proxy_event": analysis["verification_debt_proxy_event"]["value"],
        "top_action_recommendation_id": snapshot["decision"]["top_action"].get("recommendation_id"),
        "freshness_state": snapshot["freshness"]["state"],
        "benchmark_state": snapshot["benchmarks"]["state"],
        "source_completed_at": snapshot["run"]["source_completed_at"],
        "deployment_revision": snapshot["release"]["deployment_revision"],
        "visual_count": len(snapshot["visuals"]),
    }


def same(left: Any, right: Any) -> bool:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return math.isclose(float(left), float(right), rel_tol=0, abs_tol=1e-6)
    return left == right


def evaluate(snapshot: Mapping[str, Any], receipt: Mapping[str, Any]) -> dict[str, Any]:
    checks: list[dict[str, Any]] = []
    identity = {
        "run_id": snapshot["run"]["run_id"],
        "trace_id": snapshot["run"]["trace_id"],
        "release_id": snapshot["release"]["release_id"],
        "deployment_revision": snapshot["release"]["deployment_revision"],
    }
    for field, value in identity.items():
        checks.append({"field": field, "expected": value, "actual": receipt.get(field), "pass": same(value, receipt.get(field))})
        for namespace in ("panel_identity", "api_identity"):
            row = receipt.get(namespace) if isinstance(receipt.get(namespace), Mapping) else {}
            checks.append({"field": f"{namespace}.{field}", "expected": value, "actual": row.get(field), "pass": same(value, row.get(field))})
    values = receipt.get("values") if isinstance(receipt.get("values"), Mapping) else {}
    for field, value in expected(snapshot).items():
        actual = values.get(field)
        checks.append({"field": field, "expected": value, "actual": actual, "pass": same(value, actual)})
    for field, value in (("api_status", 200), ("console_error_count", 0), ("network_error_count", 0)):
        actual = receipt.get(field)
        checks.append({"field": field, "expected": value, "actual": actual, "pass": same(value, actual)})
    cache = str(receipt.get("api_cache_control", ""))
    checks.append({"field": "api_cache_control", "expected": "contains no-store", "actual": cache, "pass": "no-store" in cache.lower()})
    return {
        "schema_version": "memory_atlas.api_to_chart_oracle.v1",
        "verdict": "PASS" if all(row["pass"] for row in checks) else "FAIL",
        "run_id": snapshot["run"]["run_id"],
        "trace_id": snapshot["run"]["trace_id"],
        "release_id": snapshot["release"]["release_id"],
        "deployment_revision": snapshot["release"]["deployment_revision"],
        "mismatch_count": sum(1 for row in checks if not row["pass"]),
        "checks": checks,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--snapshot", type=Path, required=True)
    parser.add_argument("--browser-receipt", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    report = evaluate(json.loads(args.snapshot.read_text()), json.loads(args.browser_receipt.read_text()))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    raise SystemExit(0 if report["verdict"] == "PASS" else 2)


if __name__ == "__main__":
    main()
