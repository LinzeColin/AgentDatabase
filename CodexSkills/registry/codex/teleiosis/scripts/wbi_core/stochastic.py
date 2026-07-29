from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .io import canonical_json, sha256_bytes, sha256_file, utc_now, write_json


def _wilson(successes: int, total: int, z: float = 1.96) -> Tuple[float, float]:
    if total <= 0:
        return (0.0, 1.0)
    p = successes / total
    denominator = 1 + z * z / total
    center = (p + z * z / (2 * total)) / denominator
    margin = z * math.sqrt((p * (1 - p) + z * z / (4 * total)) / total) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def compare_stochastic_results(
    results_path: Path,
    *,
    baseline_id: str,
    candidate_id: str,
    minimum_trials: int = 20,
    minimum_effect: float = 0.0,
    output: Optional[Path] = None,
) -> Dict[str, Any]:
    results_path = results_path.resolve()
    groups: Dict[str, List[bool]] = {baseline_id: [], candidate_id: []}
    for number, line in enumerate(results_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        row = json.loads(line)
        system = str(row.get("system_id", ""))
        if system not in groups:
            continue
        value = row.get("success")
        if not isinstance(value, bool):
            raise ValueError("line %d success must be boolean" % number)
        groups[system].append(value)
    stats: Dict[str, Any] = {}
    for system, values in groups.items():
        successes = sum(values)
        low, high = _wilson(successes, len(values))
        stats[system] = {
            "trials": len(values),
            "successes": successes,
            "success_rate": successes / len(values) if values else None,
            "confidence_interval_95": [low, high],
        }
    b, c = stats[baseline_id], stats[candidate_id]
    reasons: List[str] = []
    if b["trials"] < minimum_trials or c["trials"] < minimum_trials:
        decision = "INCONCLUSIVE"
        reasons.append("minimum trial count not reached")
    else:
        b_low, b_high = b["confidence_interval_95"]
        c_low, c_high = c["confidence_interval_95"]
        delta = float(c["success_rate"]) - float(b["success_rate"])
        if c_low > b_high and delta > minimum_effect:
            decision = "SUPPORTED"
            reasons.append("candidate confidence interval is above baseline")
        elif c_high < b_low or delta < -abs(minimum_effect):
            decision = "REGRESSED"
            reasons.append("candidate is lower than baseline under the frozen sequential rule")
        else:
            decision = "INCONCLUSIVE"
            reasons.append("intervals overlap or effect is below threshold")
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "stochastic_decision": decision,
        "generated_at": utc_now(),
        "results": {"path": str(results_path), "sha256": sha256_file(results_path)},
        "baseline_id": baseline_id,
        "candidate_id": candidate_id,
        "minimum_trials": minimum_trials,
        "minimum_effect": minimum_effect,
        "statistics": stats,
        "reasons": reasons,
        "claim_boundary": "A stochastic result remains INCONCLUSIVE until the predeclared trial and interval rule is met; repeated runs cannot be cherry-picked.",
    }
    result["comparison_sha256"] = sha256_bytes(canonical_json(result))
    if output is not None:
        write_json(output.resolve(), result)
    return result
