from __future__ import annotations

import datetime as dt
import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .io import canonical_json, load_json, sha256_bytes, sha256_file, sha256_tree, utc_now, write_json

STRENGTH_VALUES = {
    "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT",
    "NOT_PROVEN",
    "REGRESSED",
    "BLOCKED",
    "REHEAT_REQUIRED",
}


def _parse_date(value: str) -> dt.datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def _tool_version(command: List[str]) -> Optional[str]:
    if not command or shutil.which(command[0]) is None:
        return None
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=5, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        text = (completed.stdout or completed.stderr).strip().splitlines()
        return text[0][:300] if completed.returncode == 0 and text else None
    except Exception:
        return None


def _bind_optional(path: Optional[Path], label: str) -> Optional[Dict[str, Any]]:
    if path is None:
        return None
    resolved = path.resolve()
    if not resolved.is_file() or resolved.is_symlink():
        raise ValueError("%s evidence missing or linked" % label)
    return {"path": str(resolved), "sha256": sha256_file(resolved), "bytes": resolved.stat().st_size}


def capture_environment_snapshot(
    target: Path,
    optimizer: Path,
    *,
    valid_as_of: str,
    timezone_name: str = "Australia/Sydney",
    validity_days: int = 30,
    frontier_scan: Optional[Path] = None,
    benchmark_summary: Optional[Path] = None,
    coverage_summary: Optional[Path] = None,
    shadowing_summary: Optional[Path] = None,
    runtime_capabilities: Optional[Path] = None,
    output: Optional[Path] = None,
) -> Dict[str, Any]:
    if validity_days < 1 or validity_days > 365:
        raise ValueError("validity_days must be between 1 and 365")
    valid_dt = _parse_date(valid_as_of)
    target = target.resolve()
    optimizer = optimizer.resolve()
    blockers: List[str] = []
    for label, path in (("target", target), ("optimizer", optimizer)):
        if not path.is_dir() or path.is_symlink():
            blockers.append("%s root missing or linked" % label)
    evidence = {
        "frontier_scan": _bind_optional(frontier_scan, "frontier scan"),
        "benchmark_summary": _bind_optional(benchmark_summary, "benchmark summary"),
        "coverage_summary": _bind_optional(coverage_summary, "coverage summary"),
        "shadowing_summary": _bind_optional(shadowing_summary, "shadowing summary"),
        "runtime_capabilities": _bind_optional(runtime_capabilities, "runtime capabilities"),
    }
    required_evidence = ("frontier_scan", "benchmark_summary", "coverage_summary", "shadowing_summary")
    missing = [name for name in required_evidence if evidence[name] is None]
    expires_at = valid_dt + dt.timedelta(days=validity_days)
    snapshot: Dict[str, Any] = {
        "schema_version": "1.0",
        "snapshot_status": "PASS" if not blockers else "BLOCKED",
        "generated_at": utc_now(),
        "valid_as_of": valid_dt.isoformat(),
        "timezone": timezone_name,
        "validity_days": validity_days,
        "expires_at": expires_at.isoformat(),
        "identity": {
            "target_path": str(target),
            "target_tree_sha256": sha256_tree(target) if target.is_dir() and not target.is_symlink() else None,
            "optimizer_path": str(optimizer),
            "optimizer_tree_sha256": sha256_tree(optimizer) if optimizer.is_dir() and not optimizer.is_symlink() else None,
        },
        "runtime": {
            "python": platform.python_version(),
            "python_implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "machine": platform.machine(),
            "git": _tool_version(["git", "--version"]),
            "network_was_probed": False,
            "subagent_attestation_capability": "UNKNOWN_UNLESS_EXTERNAL_RUNTIME_EVIDENCE_BOUND",
        },
        "evidence": evidence,
        "missing_strength_evidence": missing,
        "blockers": blockers,
        "unknowns": [
            "Closed-source and inaccessible market systems are outside the observed comparison set.",
            "A snapshot records current authorized capabilities; it does not predict every future model or tool.",
        ],
        "reheat_triggers": [
            "evidence lease expired",
            "major model or Agent runtime release",
            "new peer dominates a protected task",
            "Skill behavior coverage falls below contract",
            "library-scale selection or shadowing regression",
            "real-task outcome or safety regression",
            "standard, dependency or security state changed",
            "effective Genesis amendment changed",
        ],
    }
    snapshot["snapshot_sha256"] = sha256_bytes(canonical_json(snapshot))
    if output is not None:
        write_json(output.resolve(), snapshot)
    return snapshot


def _hard_gate_clean(candidate: Dict[str, Any]) -> bool:
    failures = candidate.get("hard_gate_failures", [])
    return isinstance(failures, list) and not failures


def _dominates(a: Dict[str, Any], b: Dict[str, Any], metrics: List[Dict[str, str]]) -> bool:
    better = False
    for spec in metrics:
        name = spec["name"]
        direction = spec.get("direction", "maximize")
        av = a.get("metrics", {}).get(name)
        bv = b.get("metrics", {}).get(name)
        if not isinstance(av, (int, float)) or not isinstance(bv, (int, float)):
            return False
        if direction == "maximize":
            if av < bv:
                return False
            better = better or av > bv
        elif direction == "minimize":
            if av > bv:
                return False
            better = better or av < bv
        else:
            raise ValueError("metric direction must be maximize or minimize")
    return better


def _pareto_ids(candidates: List[Dict[str, Any]], metrics: List[Dict[str, str]]) -> List[str]:
    clean = [item for item in candidates if _hard_gate_clean(item)]
    result: List[str] = []
    for item in clean:
        if not any(other is not item and _dominates(other, item, metrics) for other in clean):
            result.append(str(item.get("candidate_id")))
    return sorted(result)


def attest_environment_strength(
    snapshot_path: Path,
    candidate_set_path: Path,
    *,
    output: Optional[Path] = None,
    checked_at: str = "",
) -> Dict[str, Any]:
    snapshot_path = snapshot_path.resolve()
    candidate_set_path = candidate_set_path.resolve()
    snapshot = load_json(snapshot_path)
    candidate_set = load_json(candidate_set_path)
    errors: List[str] = []
    now = _parse_date(checked_at) if checked_at else dt.datetime.now(dt.timezone.utc)
    expiry = _parse_date(str(snapshot.get("expires_at", "")))
    selected = str(candidate_set.get("selected_candidate", ""))
    candidates = candidate_set.get("candidates")
    metrics = candidate_set.get("metrics")
    if not isinstance(candidates, list) or not candidates:
        errors.append("candidate set is empty")
        candidates = []
    if not isinstance(metrics, list) or not metrics:
        errors.append("metric contract is empty")
        metrics = []
    ids = [str(item.get("candidate_id")) for item in candidates if isinstance(item, dict)]
    if not selected or selected not in ids:
        errors.append("selected candidate is not in the frozen candidate set")
    pareto = _pareto_ids(candidates, metrics) if not errors else []
    selected_row = next((item for item in candidates if str(item.get("candidate_id")) == selected), {})

    required_states = candidate_set.get("required_evidence_states", {})
    expected_states = {
        "frontier": "PASS",
        "benchmark_integrity": "VALID",
        "outcome": "SUPPORTED",
        "coverage": "PASS",
        "shadowing": "PASS",
        "cost_evidence": ("MEASURED", "ESTIMATED"),
        "engineering_release": "INSTALLABLE",
    }
    missing_states: List[str] = []
    for key, expected in expected_states.items():
        observed = required_states.get(key)
        allowed = expected if isinstance(expected, tuple) else (expected,)
        if observed not in allowed:
            missing_states.append("%s=%s (required %s)" % (key, observed, "/".join(allowed)))

    if now > expiry:
        status = "REHEAT_REQUIRED"
        reasons = ["evidence lease expired"]
    elif snapshot.get("snapshot_status") != "PASS" or snapshot.get("blockers"):
        status = "BLOCKED"
        reasons = list(snapshot.get("blockers", [])) or ["environment snapshot did not pass"]
    elif errors:
        status = "BLOCKED"
        reasons = errors
    elif not _hard_gate_clean(selected_row):
        status = "REGRESSED"
        reasons = ["selected candidate has hard-gate failures"]
    elif selected not in pareto:
        status = "REGRESSED"
        reasons = ["selected candidate is dominated within the frozen feasible candidate set"]
    elif missing_states or snapshot.get("missing_strength_evidence"):
        status = "NOT_PROVEN"
        reasons = missing_states + ["missing snapshot evidence: %s" % item for item in snapshot.get("missing_strength_evidence", [])]
    else:
        status = "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT"
        reasons = ["selected candidate is hard-gate-clean and Pareto-undominated within the frozen current-environment comparison set"]

    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "environment_strength_status": status,
        "generated_at": utc_now(),
        "checked_at": now.isoformat(),
        "selected_candidate": selected or None,
        "pareto_frontier": pareto,
        "comparison_set_size": len(candidates),
        "environment_snapshot": {"path": str(snapshot_path), "sha256": sha256_file(snapshot_path)},
        "candidate_set": {"path": str(candidate_set_path), "sha256": sha256_file(candidate_set_path)},
        "evidence_lease": {
            "valid_from": snapshot.get("valid_as_of"),
            "expires_at": snapshot.get("expires_at"),
            "valid_now": now <= expiry and snapshot.get("snapshot_status") == "PASS",
            "reheat_triggers": snapshot.get("reheat_triggers", []),
        },
        "required_evidence_states": required_states,
        "reasons": reasons,
        "unknowns": snapshot.get("unknowns", []),
        "claim_boundary": "This attestation never proves permanent or whole-market supremacy; it only supports a bounded current-environment Pareto claim when every required evidence domain passes.",
    }
    if status not in STRENGTH_VALUES:
        raise ValueError("invalid environment strength status")
    result["attestation_sha256"] = sha256_bytes(canonical_json(result))
    if output is not None:
        write_json(output.resolve(), result)
    return result
