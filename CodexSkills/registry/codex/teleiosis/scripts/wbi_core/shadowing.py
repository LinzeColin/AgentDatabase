from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import canonical_json, sha256_bytes, sha256_file, utc_now, write_json


def evaluate_skill_shadowing(
    records_path: Path,
    *,
    output: Optional[Path] = None,
    minimum_top1_accuracy: float = 0.90,
    maximum_false_activation_rate: float = 0.05,
    maximum_outcome_drop: float = 0.02,
) -> Dict[str, Any]:
    records_path = records_path.resolve()
    rows: List[Dict[str, Any]] = []
    for number, line in enumerate(records_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("record line %d must be an object" % number)
        rows.append(value)
    if not rows:
        raise ValueError("shadowing records are empty")
    top1 = 0
    topk = 0
    false_activation = 0
    eligible_negative = 0
    confusion: Counter[str] = Counter()
    deltas: List[float] = []
    unknowns: List[str] = []
    for row in rows:
        intended = row.get("intended_skill")
        selected = row.get("selected_skill")
        ranked = row.get("ranked_skills", [])
        if intended is None:
            eligible_negative += 1
            if selected not in {None, "", "NO_SKILL"}:
                false_activation += 1
                confusion["NO_SKILL->%s" % selected] += 1
        else:
            intended = str(intended)
            if selected == intended:
                top1 += 1
            else:
                confusion["%s->%s" % (intended, selected)] += 1
            if isinstance(ranked, list) and intended in [str(item) for item in ranked]:
                topk += 1
        single = row.get("single_skill_outcome")
        library = row.get("library_outcome")
        if isinstance(single, (int, float)) and isinstance(library, (int, float)):
            deltas.append(float(library) - float(single))
        else:
            unknowns.append("outcome delta unavailable for query %s" % row.get("query_id", "UNKNOWN"))
    positives = len(rows) - eligible_negative
    top1_accuracy = top1 / positives if positives else 1.0
    topk_recall = topk / positives if positives else 1.0
    false_rate = false_activation / eligible_negative if eligible_negative else 0.0
    mean_delta = sum(deltas) / len(deltas) if deltas else None
    blockers: List[str] = []
    if top1_accuracy < minimum_top1_accuracy:
        blockers.append("top-1 skill selection accuracy below threshold")
    if false_rate > maximum_false_activation_rate:
        blockers.append("false activation rate above threshold")
    if mean_delta is None:
        blockers.append("library-vs-single-skill outcome delta is unknown")
    elif mean_delta < -maximum_outcome_drop:
        blockers.append("skill library causes material outcome degradation")
    status = "PASS" if not blockers else "SHADOWING_RISK"
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "shadowing_status": status,
        "generated_at": utc_now(),
        "records": {"path": str(records_path), "sha256": sha256_file(records_path), "count": len(rows)},
        "metrics": {
            "top1_selection_accuracy": round(top1_accuracy, 6),
            "topk_recall": round(topk_recall, 6),
            "false_activation_rate": round(false_rate, 6),
            "mean_library_outcome_delta": round(mean_delta, 6) if mean_delta is not None else None,
            "outcome_delta_observations": len(deltas),
        },
        "thresholds": {
            "minimum_top1_accuracy": minimum_top1_accuracy,
            "maximum_false_activation_rate": maximum_false_activation_rate,
            "maximum_outcome_drop": maximum_outcome_drop,
        },
        "confusion_pairs": [{"pair": key, "count": count} for key, count in confusion.most_common()],
        "blockers": blockers,
        "unknowns": sorted(set(unknowns)),
        "claim_boundary": "A Skill that works alone can still fail in a large library because retrieval and activation selection change; current-environment claims require this domain when a library is in scope.",
    }
    result["shadowing_sha256"] = sha256_bytes(canonical_json(result))
    if output is not None:
        write_json(output.resolve(), result)
    return result
