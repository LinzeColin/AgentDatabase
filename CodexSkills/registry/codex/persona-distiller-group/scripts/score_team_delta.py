#!/usr/bin/env python3
"""Score expert-team quality, experience and net Delta against a strong baseline."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from team_runtime_common import clamp, read_json, write_json

ABSOLUTE_DIMENSIONS = ("user_experience", "moe", "routing", "functionality", "quality")
BENEFIT_DIMENSIONS = ("quality", "task_completion", "evidence_coverage", "risk_reduction", "time_saved", "user_action_reduction")
COST_DIMENSIONS = ("cost", "latency", "coordination_tax", "correlated_error_risk")


def _number(data: dict[str, Any], key: str, default: float = 0.0) -> float:
    value = data.get(key, default)
    if not isinstance(value, (int, float)):
        raise ValueError(f"metric {key} must be numeric")
    return float(value)


def score_result(data: dict[str, Any]) -> dict[str, Any]:
    absolute = data.get("absolute", {})
    candidate = data.get("candidate", {})
    baseline = data.get("baseline", {})
    paired = data.get("paired", {})

    absolute_scores = {key: _number(absolute, key) for key in ABSOLUTE_DIMENSIONS}
    benefit_deltas = {key: _number(candidate, key) - _number(baseline, key) for key in BENEFIT_DIMENSIONS}
    # Lower is better for these metrics.
    cost_deltas = {key: _number(baseline, key) - _number(candidate, key) for key in COST_DIMENSIONS}

    win_rate = _number(paired, "win_rate")
    noninferiority_rate = _number(paired, "noninferiority_rate", win_rate)
    catastrophic_error_free_rate = _number(paired, "catastrophic_error_free_rate", 0)
    average_benefit = sum(clamp(50 + 2.5 * value, 0, 100) for value in benefit_deltas.values()) / len(benefit_deltas)
    efficiency = sum(clamp(50 + 2.5 * value, 0, 100) for value in cost_deltas.values()) / len(cost_deltas)
    overall_delta = (
        0.35 * win_rate
        + 0.15 * noninferiority_rate
        + 0.15 * catastrophic_error_free_rate
        + 0.25 * average_benefit
        + 0.10 * efficiency
    )

    dimensions = {**absolute_scores, "overall_delta": round(overall_delta, 2)}
    minimum_dimension = min(dimensions.values())
    target95 = all(dimensions[key] >= 95 for key in ("overall_delta", *ABSOLUTE_DIMENSIONS))
    floor75 = minimum_dimension >= 75

    evidence = data.get("evidence", {})
    evidence_level = str(evidence.get("level", "L1"))
    external_verifier = bool(evidence.get("external_verifier_passed", False))
    production_tasks = int(evidence.get("production_blind_tasks", 0))
    native_competitors = int(evidence.get("native_competitors_run", 0))
    formal_market_pass = target95 and floor75 and evidence_level == "L4" and external_verifier and production_tasks >= 20 and native_competitors >= 2

    if formal_market_pass:
        status = "MARKET_LEADER_PASS"
    elif target95 and floor75:
        status = "TARGET_METRICS_MET_EVIDENCE_INCOMPLETE"
    elif floor75:
        status = "FLOOR_PASS_TARGET_NOT_MET"
    else:
        status = "CANDIDATE_REJECTED_BELOW_FLOOR"

    return {
        "schema_version": "persona-team.delta-score.v1",
        "status": status,
        "dimensions": dimensions,
        "benefit_deltas": {key: round(value, 2) for key, value in benefit_deltas.items()},
        "efficiency_deltas": {key: round(value, 2) for key, value in cost_deltas.items()},
        "minimum_dimension": round(minimum_dimension, 2),
        "target95_pass": target95,
        "floor75_pass": floor75,
        "formal_market_pass": formal_market_pass,
        "evidence": {
            "level": evidence_level,
            "external_verifier_passed": external_verifier,
            "production_blind_tasks": production_tasks,
            "native_competitors_run": native_competitors,
        },
        "interpretation": [
            "95 is a measured acceptance gate, never a design-time promise.",
            "Every reported template/framework/model/task slice must also remain at or above 75.",
            "Formal market leadership additionally requires L4 production evidence and an external verifier.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Score expert-team net Delta and 95/75 acceptance gates.")
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        result = score_result(read_json(args.result))
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    if args.output:
        write_json(args.output, result)
        print(json.dumps({"written": str(args.output), "status": result["status"]}, ensure_ascii=False))
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["floor75_pass"] else 3


if __name__ == "__main__":
    raise SystemExit(main())
