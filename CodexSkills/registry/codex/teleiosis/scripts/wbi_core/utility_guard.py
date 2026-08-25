from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import canonical_json, load_json, sha256_bytes, sha256_file, utc_now, write_json

DIRECTIONS = {"higher", "lower", "equal"}


def _number(value: Any, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise ValueError("%s must be a finite number" % label)
    return float(value)


def _improvement(direction: str, baseline: float, candidate: float) -> float:
    if abs(baseline) < 1e-12:
        if candidate == baseline:
            return 0.0
        if direction == "higher":
            return 1.0 if candidate > baseline else -1.0
        if direction == "lower":
            return 1.0 if candidate < baseline else -1.0
        return -1.0
    scale = abs(baseline)
    if direction == "higher":
        return (candidate - baseline) / scale
    if direction == "lower":
        return (baseline - candidate) / scale
    return -abs(candidate - baseline) / scale


def evaluate_utility_contract(contract: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(contract, dict):
        raise ValueError("utility contract must be an object")
    minimum_gain = _number(contract.get("minimum_material_gain", 0.01), "minimum_material_gain")
    if minimum_gain < 0:
        raise ValueError("minimum_material_gain cannot be negative")
    metrics = contract.get("metrics")
    if not isinstance(metrics, list) or not metrics:
        raise ValueError("metrics must be a non-empty array")
    checks = contract.get("protected_checks", [])
    if not isinstance(checks, list):
        raise ValueError("protected_checks must be an array")

    hard_regressions: List[Dict[str, Any]] = []
    material_gains: List[Dict[str, Any]] = []
    metric_results: List[Dict[str, Any]] = []
    seen = set()
    for index, metric in enumerate(metrics):
        if not isinstance(metric, dict):
            raise ValueError("metric %d must be an object" % index)
        metric_id = str(metric.get("metric_id") or "").strip()
        if not metric_id or metric_id in seen:
            raise ValueError("metric_id must be non-empty and unique")
        seen.add(metric_id)
        direction = str(metric.get("direction") or "")
        if direction not in DIRECTIONS:
            raise ValueError("metric %s has invalid direction" % metric_id)
        baseline = _number(metric.get("baseline"), "%s.baseline" % metric_id)
        candidate = _number(metric.get("candidate"), "%s.candidate" % metric_id)
        tolerance = _number(metric.get("regression_tolerance", 0.0), "%s.regression_tolerance" % metric_id)
        if tolerance < 0:
            raise ValueError("regression_tolerance cannot be negative")
        improvement = _improvement(direction, baseline, candidate)
        hard = bool(metric.get("hard", False))
        result = {
            "metric_id": metric_id,
            "direction": direction,
            "baseline": baseline,
            "candidate": candidate,
            "relative_improvement": improvement,
            "absolute_delta": candidate - baseline,
            "hard": hard,
            "regression_tolerance": tolerance,
            "material_gain": improvement >= minimum_gain,
            "regression": improvement < -tolerance,
            "evidence_ref": metric.get("evidence_ref"),
        }
        metric_results.append(result)
        if result["material_gain"]:
            material_gains.append(result)
        if hard and result["regression"]:
            hard_regressions.append(result)

    protected_results: List[Dict[str, Any]] = []
    for index, check in enumerate(checks):
        if not isinstance(check, dict):
            raise ValueError("protected check %d must be an object" % index)
        check_id = str(check.get("check_id") or "").strip()
        if not check_id:
            raise ValueError("protected check id cannot be empty")
        baseline_pass = check.get("baseline_pass") is True
        candidate_pass = check.get("candidate_pass") is True
        result = {
            "check_id": check_id,
            "baseline_pass": baseline_pass,
            "candidate_pass": candidate_pass,
            "regression": baseline_pass and not candidate_pass,
            "evidence_ref": check.get("evidence_ref"),
        }
        protected_results.append(result)
        if result["regression"]:
            hard_regressions.append(result)

    if hard_regressions:
        decision = "REVERT"
        reason = "candidate regressed at least one protected or hard dimension"
    elif material_gains:
        decision = "KEEP_CANDIDATE"
        reason = "candidate has a material measured gain and no hard regression"
    else:
        decision = "KEEP_BASELINE"
        reason = "candidate has no material measured gain; avoid complexity/burden expansion"

    payload = {
        "schema_version": "1.0",
        "status": "PASS",
        "evaluated_at": utc_now(),
        "decision": decision,
        "reason": reason,
        "minimum_material_gain": minimum_gain,
        "hard_regression_count": len(hard_regressions),
        "material_gain_count": len(material_gains),
        "metric_results": metric_results,
        "protected_check_results": protected_results,
        "hard_regressions": hard_regressions,
        "material_gains": material_gains,
        "policy": {
            "hard_gates_are_non_compensatory": True,
            "no_material_gain_falls_back_to_baseline": True,
            "unknown_values_are_not_zero": True,
        },
    }
    payload["result_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def evaluate_utility_file(contract_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    contract = load_json(contract_path)
    result = evaluate_utility_contract(contract)
    result["contract_path"] = str(contract_path.resolve())
    result["contract_sha256"] = sha256_file(contract_path)
    if output_path:
        write_json(output_path, result)
    return result
