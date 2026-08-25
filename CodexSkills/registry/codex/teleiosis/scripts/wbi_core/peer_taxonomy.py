from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .io import sha256_file, utc_now, write_json

SCOPES = {
    "direct-competitor",
    "adjacent-competitor",
    "method-reference",
    "engineering-analogy",
    "out-of-scope",
}
MARKET_ELIGIBLE_SCOPES = {"direct-competitor", "adjacent-competitor", "method-reference"}

_OPTIMIZATION_TERMS = (
    "skill optimizer", "skill optimisation", "skill optimization", "skill evolution",
    "self-evol", "self evol", "refin", "darwin-skill", "luban-skill", "skillopt",
)
_SKILL_TERMS = ("agent skill", "agentskills", "skill creator", "skill registry", "skill publish")
_METHOD_TERMS = (
    "llm", "language model", "prompt", "agent", "benchmark", "evaluation", "autoresearch",
    "multi-objective", "coevolution", "skillmoo", "skilllens", "metaskill",
)


def _text(metadata: Dict[str, Any]) -> str:
    values: List[str] = []
    for key in ("name", "description", "topics", "full_name", "slug", "peer_id", "source_url"):
        value = metadata.get(key)
        if isinstance(value, list):
            values.extend(str(item) for item in value)
        elif value is not None:
            values.append(str(value))
    return " ".join(values).lower().replace("_", " ").replace("-", " ")


def classify_comparison_scope(metadata: Dict[str, Any], inspection: Optional[Dict[str, Any]] = None) -> Tuple[str, float, List[str]]:
    """Classify *why* a repository is being compared, separately from peer category.

    This prevents an unrelated but well-engineered repository from satisfying the
    five-market-peer gate merely because its name overlaps with a Skill name.
    """
    explicit = str(metadata.get("comparison_scope") or "").strip()
    if explicit:
        if explicit not in SCOPES:
            return "out-of-scope", 0.0, ["invalid explicit comparison_scope=%s" % explicit]
        return explicit, float(metadata.get("scope_confidence", 1.0) or 1.0), ["caller supplied explicit comparison_scope"]

    text = _text(metadata)
    signals = (inspection or {}).get("signals", {}) if isinstance(inspection, dict) else {}
    has_skill = bool(signals.get("has_skill"))
    evidence: List[str] = []
    if has_skill:
        evidence.append("repository contains SKILL.md")
    optimization_match = any(term in text for term in _OPTIMIZATION_TERMS)
    skill_match = any(term in text for term in _SKILL_TERMS)
    method_match = any(term in text for term in _METHOD_TERMS)

    if has_skill and optimization_match:
        return "direct-competitor", 0.94, evidence + ["Skill-evolution intent observed"]
    if has_skill or skill_match:
        return "adjacent-competitor", 0.86, evidence + ["Agent Skill craft/tooling intent observed"]
    if method_match and any(term in text for term in ("optim", "evol", "evaluat", "research", "benchmark")):
        return "method-reference", 0.76, evidence + ["transferable AI optimization/evaluation method observed"]
    if inspection and any(bool(signals.get(key)) for key in ("has_readme", "has_tests", "has_scripts", "has_ci")):
        return "engineering-analogy", 0.72, evidence + ["engineered repository without Agent Skill identity"]
    if metadata.get("source_url") or metadata.get("slug"):
        return "engineering-analogy", 0.58, evidence + ["non-Skill repository; analogy only until stronger evidence"]
    return "out-of-scope", 0.30, evidence + ["insufficient comparable evidence"]


def normalized_scope(row: Dict[str, Any]) -> str:
    explicit = str(row.get("comparison_scope") or "").strip()
    if explicit in SCOPES:
        return explicit
    # Backward-compatible mapping for v0.0.0.2 records. New datasets always
    # persist comparison_scope explicitly.
    category = str(row.get("category") or "")
    if category == "direct":
        return "direct-competitor"
    if category == "craft":
        return "adjacent-competitor"
    if category == "indirect":
        return "method-reference"
    return "out-of-scope"


def market_peer_eligible(row: Dict[str, Any]) -> bool:
    return normalized_scope(row) in MARKET_ELIGIBLE_SCOPES


def audit_records(rows: Iterable[Dict[str, Any]]) -> Dict[str, Any]:
    audited: List[Dict[str, Any]] = []
    counts = {scope: 0 for scope in sorted(SCOPES)}
    errors: List[str] = []
    seen = set()
    for index, original in enumerate(rows):
        if not isinstance(original, dict):
            errors.append("row %d is not an object" % index)
            continue
        row = dict(original)
        identity = str(row.get("peer_id") or row.get("slug") or row.get("source_url") or "row:%d" % index)
        if identity in seen:
            errors.append("duplicate peer identity: %s" % identity)
            continue
        seen.add(identity)
        scope, confidence, evidence = classify_comparison_scope(row, row.get("inspection") if isinstance(row.get("inspection"), dict) else None)
        row["comparison_scope"] = scope
        row["scope_confidence"] = confidence
        row["scope_evidence"] = evidence
        row["market_scope_eligible"] = scope in MARKET_ELIGIBLE_SCOPES
        # Classification alone never proves a production peer. A caller may set
        # production_eligible only after the separate provenance/evidence gate.
        row["market_peer_eligible"] = row["market_scope_eligible"] and row.get("production_eligible") is True
        if str(original.get("comparison_scope") or "").strip() and str(original.get("comparison_scope")) not in SCOPES:
            errors.append("invalid comparison_scope for %s" % identity)
        counts[scope] += 1
        audited.append(row)
    scope_candidates = [row for row in audited if row["market_scope_eligible"]]
    eligible = [row for row in audited if row["market_peer_eligible"]]
    analogies = [row for row in audited if row["comparison_scope"] == "engineering-analogy"]
    return {
        "schema_version": "1.0",
        "status": "PASS" if not errors else "FAIL",
        "generated_at": utc_now(),
        "row_count": len(audited),
        "market_scope_candidate_count": len(scope_candidates),
        "production_qualified_peer_count": len(eligible),
        "engineering_analogy_count": len(analogies),
        "counts": counts,
        "market_scope_candidate_ids": [str(row.get("peer_id") or row.get("slug") or row.get("source_url")) for row in scope_candidates],
        "market_peer_ids": [str(row.get("peer_id") or row.get("slug") or row.get("source_url")) for row in eligible],
        "engineering_analogy_ids": [str(row.get("peer_id") or row.get("slug") or row.get("source_url")) for row in analogies],
        "records": audited,
        "errors": errors,
        "policy": {
            "market_gate_accepts": sorted(MARKET_ELIGIBLE_SCOPES),
            "engineering_analogy_can_supply_mechanisms": True,
            "engineering_analogy_can_satisfy_market_peer_minimum": False,
            "classification_alone_can_satisfy_production_peer_gate": False,
        },
    }


def audit_file(input_path: Path, output_path: Optional[Path] = None) -> Dict[str, Any]:
    rows: List[Dict[str, Any]] = []
    text = input_path.read_text(encoding="utf-8")
    if input_path.suffix.lower() == ".jsonl":
        for number, raw in enumerate(text.splitlines(), 1):
            if raw.strip():
                value = json.loads(raw)
                if not isinstance(value, dict):
                    raise ValueError("JSONL line %d must be an object" % number)
                rows.append(value)
    else:
        value = json.loads(text)
        if isinstance(value, dict) and isinstance(value.get("records"), list):
            rows = value["records"]
        elif isinstance(value, list):
            rows = value
        else:
            raise ValueError("peer audit input must be a JSON array, records object, or JSONL")
    result = audit_records(rows)
    result["input_path"] = str(input_path.resolve())
    result["input_sha256"] = sha256_file(input_path)
    if output_path:
        write_json(output_path, result)
    return result
