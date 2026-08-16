#!/usr/bin/env python3
"""Append one measured run and rebuild calibrated routing telemetry."""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from registry_core import default_registry_root, default_telemetry_path
from team_runtime_common import clamp, read_json, write_json

EXPECTED_SLICES = {
    "single-explanation", "single-diagnosis", "small-product", "small-research",
    "deep-high-risk", "deep-architecture", "swarm-search", "swarm-batch",
    "currentness", "creative", "ood-boundary", "recovery",
}


def calibration_error(runs: list[dict[str, Any]], bins: int = 10) -> float:
    if not runs:
        return 1.0
    grouped: dict[int, list[tuple[float, float]]] = defaultdict(list)
    for run in runs:
        predicted = clamp(float(run.get("predicted_success", 0.5)))
        actual = clamp(float(run.get("actual_success", 0.0)))
        grouped[min(bins - 1, int(predicted * bins))].append((predicted, actual))
    total = len(runs)
    return sum(
        len(rows) / total * abs(sum(p for p, _ in rows) / len(rows) - sum(a for _, a in rows) / len(rows))
        for rows in grouped.values()
    )


def rebuild(runs: list[dict[str, Any]]) -> dict[str, Any]:
    observed_slices = {str(run.get("task_slice")) for run in runs if run.get("task_slice")}
    experts: dict[str, dict[str, Any]] = {}
    raw: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for run in runs:
        for slug in run.get("subject_slugs", []):
            raw[str(slug)].append(run)
    for slug, rows in raw.items():
        domain_values: dict[str, list[float]] = defaultdict(list)
        for row in rows:
            for domain in row.get("task_domains", []):
                domain_values[str(domain)].append(float(row.get("overall_delta", 0.0)))
        experts[slug] = {
            "sample_count": len(rows),
            "overall_delta": round(sum(float(row.get("overall_delta", 0.0)) for row in rows) / len(rows), 4),
            "domain_scores": {
                domain: round(sum(values) / len(values), 4)
                for domain, values in sorted(domain_values.items())
            },
        }
    ece = calibration_error(runs)
    coverage = len(observed_slices & EXPECTED_SLICES) / len(EXPECTED_SLICES)
    return {
        "schema_version": "persona-team.outcome-telemetry.v1",
        "sample_count": len(runs),
        "expected_calibration_error": round(ece, 4),
        "task_slice_coverage": round(coverage, 4),
        "eligible_for_c": len(runs) >= 60 and ece <= 0.12 and coverage >= 0.75,
        "observed_task_slices": sorted(observed_slices),
        "experts": experts,
        "runs": runs,
    }


def append_outcome(telemetry_path: Path, route: dict[str, Any], delta: dict[str, Any], task_slice: str, actual_success: float) -> dict[str, Any]:
    prior = read_json(telemetry_path) if telemetry_path.is_file() else {"runs": []}
    runs = list(prior.get("runs", []))
    members = route.get("members", [])
    routing_scores = [float(row.get("marginal_score", row.get("base_score", 0.5))) for row in members]
    predicted = sum(routing_scores) / len(routing_scores) if routing_scores else 0.5
    profile = route.get("task_graph", {}).get("profile", {})
    run = {
        "run_id": f"RUN-{len(runs) + 1:05d}",
        "task_slice": task_slice,
        "task_domains": profile.get("domains", []),
        "mode": route.get("mode"),
        "strategy": route.get("strategy"),
        "subject_slugs": [row.get("subject_slug") for row in members if row.get("subject_slug")],
        "predicted_success": round(clamp(predicted), 4),
        "actual_success": round(clamp(actual_success), 4),
        "overall_delta": float(delta.get("dimensions", {}).get("overall_delta", 0.0)),
        "minimum_dimension": float(delta.get("minimum_dimension", 0.0)),
        "formal_market_pass": bool(delta.get("formal_market_pass", False)),
    }
    runs.append(run)
    result = rebuild(runs)
    write_json(telemetry_path, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Record one measured team outcome for C-layer calibration.")
    parser.add_argument("--route-plan", type=Path, required=True)
    parser.add_argument("--delta-score", type=Path, required=True)
    parser.add_argument("--task-slice", required=True)
    parser.add_argument("--actual-success", type=float, required=True, help="0..1 observed task success")
    parser.add_argument("--registry-root", type=Path, default=None,
                        help="only used to locate the default telemetry file")
    parser.add_argument("--telemetry", type=Path, default=None,
                        help="defaults to <registry-root>/telemetry/team-outcomes.json "
                             "-- the same path route_team_moe.py reads")
    args = parser.parse_args()

    # ★★ **这条链写的是校准账本 —— 最不能进垃圾。** 2026-08-17 交叉喂测：
    #   `--route-plan` 传一份无关 JSON，本脚本 **rc=0 把记录写进了遥测**。
    #   而 route_team_moe 正是拿这个账本当 C 策略先验 ⇒
    #   一条垃圾记录会**直接污染以后所有路由的排序**，且没有任何地方会报警。
    #   [[empty-default-swallows-unknown]]｜[[a-gates-scan-set-is-smaller-than-reality]]
    _rp = read_json(args.route_plan)
    if not any(k in _rp for k in ("mode", "members", "strategy", "task_graph")):
        print(json.dumps({"status": "blocked", "reason":
              "route-plan 里 mode/members/strategy/task_graph 一个都没有 —— "
              "这不是 route_team_moe 的产物。**不写遥测**：垃圾记录会污染 C 层校准。"},
              ensure_ascii=False))
        return 2
    _ds = read_json(args.delta_score)
    if not any(k in _ds for k in ("dimensions", "formal_market_pass", "minimum_dimension")):
        print(json.dumps({"status": "blocked", "reason":
              "delta-score 里 dimensions/formal_market_pass/minimum_dimension 一个都没有 —— "
              "这不是 score_team_delta 的产物。**不写遥测**。"}, ensure_ascii=False))
        return 2
    if not 0 <= args.actual_success <= 1:
        parser.error("actual-success must be between 0 and 1")
    root = (args.registry_root or default_registry_root()).expanduser().resolve()
    telemetry_path = args.telemetry or default_telemetry_path(root)
    telemetry_path.parent.mkdir(parents=True, exist_ok=True)
    result = append_outcome(telemetry_path, read_json(args.route_plan), read_json(args.delta_score), args.task_slice, args.actual_success)
    print(json.dumps({
        "written": str(telemetry_path),
        "telemetry_path_source": "explicit --telemetry" if args.telemetry else "default (shared with route_team_moe.py)",
        "sample_count": result["sample_count"],
        "expected_calibration_error": result["expected_calibration_error"],
        "task_slice_coverage": result["task_slice_coverage"],
        "eligible_for_c": result["eligible_for_c"],
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
