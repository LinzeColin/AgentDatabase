from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .io import canonical_json, load_json, sha256_bytes, sha256_file, utc_now, write_json


def _rows(path: Path) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("trajectory line %d must be an object" % number)
        result.append(value)
    return result


def evaluate_skill_coverage(
    constraints_path: Path,
    trajectories_path: Path,
    *,
    output: Optional[Path] = None,
    minimum_overall_coverage: float = 0.80,
    minimum_hard_coverage: float = 1.0,
) -> Dict[str, Any]:
    constraints_path = constraints_path.resolve()
    trajectories_path = trajectories_path.resolve()
    contract = load_json(constraints_path)
    constraints = contract.get("constraints")
    if not isinstance(constraints, list) or not constraints:
        raise ValueError("constraints must be a non-empty list")
    ids: List[str] = []
    severity: Dict[str, str] = {}
    family: Dict[str, str] = {}
    for row in constraints:
        cid = str(row.get("constraint_id", ""))
        if not cid or cid in ids:
            raise ValueError("constraint IDs must be unique and non-empty")
        ids.append(cid)
        severity[cid] = str(row.get("severity", "NORMAL"))
        family[cid] = str(row.get("family", "unclassified"))
    known = set(ids)
    exercised: Set[str] = set()
    satisfied: Set[str] = set()
    failed: Set[str] = set()
    unknown_refs: Set[str] = set()
    task_count = 0
    family_tasks: Counter[str] = Counter()
    for row in _rows(trajectories_path):
        task_count += 1
        family_tasks[str(row.get("task_family", "unclassified"))] += 1
        for key, destination in (("satisfied_constraints", satisfied), ("failed_constraints", failed), ("exercised_constraints", exercised)):
            values = row.get(key, [])
            if not isinstance(values, list):
                raise ValueError("%s must be a list" % key)
            for cid in values:
                token = str(cid)
                if token in known:
                    destination.add(token)
                    exercised.add(token)
                else:
                    unknown_refs.add(token)
    hard = {cid for cid in ids if severity[cid] in {"HARD", "HARD_NON_COMPENSABLE", "CRITICAL"}}
    overall = len(exercised) / len(ids)
    hard_coverage = len(exercised & hard) / len(hard) if hard else 1.0
    uncovered = [cid for cid in ids if cid not in exercised]
    hard_uncovered = [cid for cid in uncovered if cid in hard]
    status = "PASS" if overall >= minimum_overall_coverage and hard_coverage >= minimum_hard_coverage and not hard_uncovered and not unknown_refs else "INCOMPLETE"
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "coverage_status": status,
        "generated_at": utc_now(),
        "constraints": {"path": str(constraints_path), "sha256": sha256_file(constraints_path), "count": len(ids)},
        "trajectories": {"path": str(trajectories_path), "sha256": sha256_file(trajectories_path), "count": task_count},
        "metrics": {
            "overall_behavior_coverage": round(overall, 6),
            "hard_behavior_coverage": round(hard_coverage, 6),
            "exercised_constraints": len(exercised),
            "satisfied_constraints": len(satisfied),
            "failed_constraints": len(failed),
            "uncovered_constraints": len(uncovered),
        },
        "thresholds": {"minimum_overall_coverage": minimum_overall_coverage, "minimum_hard_coverage": minimum_hard_coverage},
        "uncovered": uncovered,
        "hard_uncovered": hard_uncovered,
        "failed": sorted(failed),
        "unknown_constraint_references": sorted(unknown_refs),
        "task_family_counts": dict(sorted(family_tasks.items())),
        "constraint_family_coverage": {
            name: {
                "total": len([cid for cid in ids if family[cid] == name]),
                "exercised": len([cid for cid in exercised if family[cid] == name]),
            }
            for name in sorted(set(family.values()))
        },
        "next_actions": [
            "Add probes that exercise uncovered hard constraints before making an outcome or current-environment-strength claim."
        ] if uncovered else [],
        "claim_boundary": "Coverage measures which declared Skill behaviors were exercised by recorded trajectories; it does not by itself prove correctness or quality.",
    }
    result["coverage_sha256"] = sha256_bytes(canonical_json(result))
    if output is not None:
        write_json(output.resolve(), result)
    return result
