from __future__ import annotations

import json
import math
import re
import shutil
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence

from .io import canonical_json, load_json, sha256_bytes, sha256_file, utc_now, write_json

REQUIRED_DIMENSIONS = {
    "trigger_accuracy", "task_effectiveness", "safety", "evidence_truthfulness", "cost",
    "latency", "installability", "compatibility", "cross_model_transfer", "maintainability", "future_adaptability",
}
SPLITS = {"dev", "validation", "sealed-holdout", "adversarial"}
SYSTEM_ROLES = {"no-skill", "baseline", "candidate"}
HASH_RE = re.compile(r"^[a-f0-9]{64}$")


def _chmod_read_only(path: Path) -> None:
    try:
        path.chmod(0o444)
    except OSError:
        pass


def _system_map(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("system_id")): item for item in contract.get("systems", []) if isinstance(item, dict) and item.get("system_id")}


def _dataset_map(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item.get("dataset_id")): item for item in contract.get("datasets", []) if isinstance(item, dict) and item.get("dataset_id")}


def validate_eval_contract(contract: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    for key in ("contract_id", "created_before_first_change", "systems", "metrics", "hard_gates", "datasets", "protected_task_families", "judge_policy"):
        if key not in contract:
            errors.append("eval contract missing %s" % key)
    if contract.get("created_before_first_change") is not True:
        errors.append("eval contract must be frozen before first candidate change")
    systems = contract.get("systems", [])
    ids = [item.get("system_id") for item in systems if isinstance(item, dict)]
    if not ids or len(ids) != len(set(ids)):
        errors.append("eval system IDs must be non-empty and unique")
    roles = [item.get("role") for item in systems if isinstance(item, dict)]
    if roles.count("baseline") != 1 or "candidate" not in roles:
        errors.append("eval contract requires exactly one baseline and at least one candidate")
    for item in systems:
        if not isinstance(item, dict) or item.get("role") not in SYSTEM_ROLES:
            errors.append("eval system role invalid")
            continue
        policy = item.get("tree_hash_policy", "fixed")
        tree_hash = item.get("tree_hash")
        if policy not in {"fixed", "result-bound", "none"}:
            errors.append("system tree_hash_policy invalid")
        if policy == "fixed" and not HASH_RE.fullmatch(str(tree_hash or "")):
            errors.append("fixed system requires a 64-hex tree_hash")
        if item.get("role") in {"baseline", "candidate"} and policy == "none":
            errors.append("baseline/candidate system cannot use an unbound tree hash")
    metrics = contract.get("metrics", {})
    if not isinstance(metrics, dict) or not REQUIRED_DIMENSIONS.issubset(metrics):
        errors.append("eval contract lacks all Genesis evaluation dimensions")
    else:
        for name, definition in metrics.items():
            if not isinstance(definition, dict):
                errors.append("metric %s definition invalid" % name)
                continue
            if definition.get("direction") not in {"maximize", "minimize"}:
                errors.append("metric %s direction invalid" % name)
            if not isinstance(definition.get("regression_tolerance"), (int, float)):
                errors.append("metric %s regression_tolerance missing" % name)
    datasets = contract.get("datasets", [])
    dataset_ids = [item.get("dataset_id") for item in datasets if isinstance(item, dict)]
    if not dataset_ids or len(dataset_ids) != len(set(dataset_ids)):
        errors.append("dataset IDs must be non-empty and unique")
    for dataset in datasets:
        if not isinstance(dataset, dict) or dataset.get("split") not in SPLITS:
            errors.append("dataset split invalid")
            continue
        if not dataset.get("dataset_id") or not HASH_RE.fullmatch(str(dataset.get("dataset_hash", ""))):
            errors.append("dataset identity/64-hex hash missing")
        if dataset.get("split") == "sealed-holdout":
            forbidden = set(dataset) & {"prompts", "cases", "content", "local_content_path", "examples"}
            if forbidden:
                errors.append("sealed holdout content leaked into contract: %s" % sorted(forbidden))
    policy = contract.get("judge_policy", {})
    if not policy.get("modifier_cannot_be_final_judge"):
        errors.append("modifier/final-judge separation missing")
    if not policy.get("blind_identity"):
        errors.append("blind identity policy missing")
    return errors


def seal_eval_contract(workspace: Path, contract_source: Path, actor_id: str) -> Dict[str, Any]:
    workspace = workspace.resolve()
    state = load_json(workspace / "state.json")
    if int(state.get("changes_recorded", 0)) > 0:
        raise ValueError("eval contract must be sealed before the first candidate change")
    contract = load_json(contract_source)
    errors = validate_eval_contract(contract)
    if errors:
        return {"status": "BLOCKED", "errors": errors}
    control = workspace / "control/evals"
    control.mkdir(parents=True, exist_ok=True)
    destination = control / "evaluation-contract.json"
    write_json(destination, contract)
    seal = {
        "schema_version": "1.0", "contract_id": contract["contract_id"], "sealed_at": utc_now(), "actor_id": actor_id,
        "contract_sha256": sha256_file(destination), "candidate_change_count_at_seal": 0,
        "sealed_holdout_dataset_ids": [item["dataset_id"] for item in contract["datasets"] if item.get("split") == "sealed-holdout"],
        "status": "SEALED",
    }
    write_json(control / "evaluation-contract.seal.json", seal)
    _chmod_read_only(destination)
    _chmod_read_only(control / "evaluation-contract.seal.json")
    return seal


def verify_eval_control(workspace: Path) -> List[str]:
    workspace = workspace.resolve()
    errors: List[str] = []
    contract_path = workspace / "control/evals/evaluation-contract.json"
    seal_path = workspace / "control/evals/evaluation-contract.seal.json"
    if not contract_path.is_file() or not seal_path.is_file():
        return ["evaluation contract/seal missing"]
    contract = load_json(contract_path)
    seal = load_json(seal_path)
    errors.extend(validate_eval_contract(contract))
    if sha256_file(contract_path) != seal.get("contract_sha256"):
        errors.append("evaluation contract changed after sealing")
    if seal.get("candidate_change_count_at_seal") != 0 or seal.get("status") != "SEALED":
        errors.append("evaluation contract seal invalid")
    return errors


def _parse_utc(value: Any, label: str, errors: List[str]) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        errors.append("%s timestamp is missing" % label)
        return None
    text = value.strip()
    try:
        parsed = datetime.fromisoformat(text[:-1] + "+00:00" if text.endswith("Z") else text)
    except ValueError:
        errors.append("%s timestamp is not ISO-8601" % label)
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        errors.append("%s timestamp must include a timezone" % label)
        return None
    return parsed.astimezone(timezone.utc)


def _verify_bound_file(workspace: Path, relative: Any, expected_hash: Any, label: str, errors: List[str]) -> None:
    if not isinstance(relative, str) or not relative.strip():
        errors.append("%s path missing" % label)
        return
    if not HASH_RE.fullmatch(str(expected_hash or "")):
        errors.append("%s sha256 missing or invalid" % label)
        return
    path = (workspace / relative).resolve()
    if workspace != path and workspace not in path.parents:
        errors.append("%s path escapes workspace" % label)
    elif not path.is_file():
        errors.append("%s file missing" % label)
    elif sha256_file(path) != expected_hash:
        errors.append("%s hash mismatch" % label)


def result_cell(row: Dict[str, Any]) -> tuple:
    """Return the frozen comparison cell independent of system identity."""
    return (
        str(row.get("dataset_id", "")), str(row.get("split", "")), str(row.get("task_id", "")),
        str(row.get("task_family", "")), str(row.get("trial_id", "")),
        str(row.get("model", "")), str(row.get("runtime", "")),
    )


def validate_result(row: Dict[str, Any], contract: Dict[str, Any], workspace: Path) -> List[str]:
    # Resolve the workspace once before comparing child paths.  On macOS,
    # tempfile paths can be spelled through /var while resolved children use
    # /private/var; comparing mixed spellings falsely rejects safe evidence.
    workspace = workspace.resolve()
    errors: List[str] = []
    if not isinstance(row, dict):
        return ["evaluation result must be an object"]
    required = (
        "result_id", "task_id", "task_family", "dataset_id", "dataset_hash", "split", "system_id", "system_role",
        "system_tree_hash", "trial_id", "model", "runtime", "metrics", "hard_gates", "raw_result_path",
        "raw_result_sha256", "process_trace_path", "process_trace_sha256", "actor_id", "started_at", "finished_at",
    )
    for key in required:
        if key not in row:
            errors.append("missing %s" % key)
    for key in ("result_id", "task_id", "task_family", "dataset_id", "system_id", "trial_id", "model", "runtime", "actor_id"):
        if key in row and (not isinstance(row.get(key), str) or not row.get(key).strip()):
            errors.append("%s must be a non-empty string" % key)
    systems = _system_map(contract)
    system = systems.get(str(row.get("system_id")))
    if not system:
        errors.append("result system_id is not frozen in the eval contract")
    elif row.get("system_role") != system.get("role"):
        errors.append("result system role does not match eval contract")
    tree_hash = str(row.get("system_tree_hash", ""))
    if not HASH_RE.fullmatch(tree_hash):
        errors.append("result lacks a 64-hex system_tree_hash")
    elif system and system.get("tree_hash_policy", "fixed") == "fixed" and tree_hash != system.get("tree_hash"):
        errors.append("result tree hash does not match fixed eval system")
    datasets = _dataset_map(contract)
    dataset = datasets.get(str(row.get("dataset_id")))
    if not dataset:
        errors.append("result dataset_id is not frozen in the eval contract")
    elif row.get("dataset_hash") != dataset.get("dataset_hash") or row.get("split") != dataset.get("split"):
        errors.append("result dataset hash/split does not match eval contract")
    if row.get("split") not in SPLITS:
        errors.append("invalid split")
    if row.get("system_role") not in SYSTEM_ROLES:
        errors.append("invalid system role")
    metric_names = set(contract.get("metrics", {}))
    metrics = row.get("metrics", {})
    if not isinstance(metrics, dict) or set(metrics) != metric_names:
        errors.append("result metrics must exactly match the frozen metric set")
    else:
        for name in metric_names:
            value = metrics.get(name)
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not math.isfinite(float(value)):
                errors.append("metric %s is not finite numeric" % name)
    gates = row.get("hard_gates", {})
    if not isinstance(gates, dict) or not set(contract.get("hard_gates", [])).issubset(gates):
        errors.append("hard gate results incomplete")
    elif any(not isinstance(value, bool) for value in gates.values()):
        errors.append("hard gate results must be boolean")
    _verify_bound_file(workspace, row.get("raw_result_path"), row.get("raw_result_sha256"), "raw result", errors)
    _verify_bound_file(workspace, row.get("process_trace_path"), row.get("process_trace_sha256"), "process trace", errors)
    started = _parse_utc(row.get("started_at"), "started_at", errors)
    finished = _parse_utc(row.get("finished_at"), "finished_at", errors)
    if started and finished and finished < started:
        errors.append("finished_at precedes started_at")
    return errors


def load_results(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            rows.append(json.loads(raw))
        except Exception as exc:
            raise ValueError("invalid JSONL line %d: %s" % (number, exc))
    return rows


def _median(values: Sequence[float]) -> float:
    return float(statistics.median(values)) if values else float("nan")


def aggregate_results(rows: List[Dict[str, Any]], contract: Dict[str, Any]) -> Dict[str, Any]:
    groups: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        system_id = str(row["system_id"])
        group = groups.setdefault(system_id, {
            "system_id": system_id, "system_role": row["system_role"], "metrics": {}, "hard_gate_failures": [],
            "task_families": {}, "models": set(), "splits": set(), "dataset_ids": set(), "tree_hashes": set(), "trials": 0,
        })
        group["models"].add(row["model"])
        group["splits"].add(row["split"])
        group["dataset_ids"].add(row["dataset_id"])
        group["tree_hashes"].add(row["system_tree_hash"])
        group["trials"] += 1
        for name, value in row["metrics"].items():
            group["metrics"].setdefault(name, []).append(float(value))
        for gate, passed in row["hard_gates"].items():
            if passed is not True:
                group["hard_gate_failures"].append({"result_id": row["result_id"], "gate": gate})
        family = group["task_families"].setdefault(row["task_family"], {})
        for name, value in row["metrics"].items():
            family.setdefault(name, []).append(float(value))
    normalized: Dict[str, Any] = {}
    for system_id, group in groups.items():
        normalized[system_id] = {
            "system_id": system_id, "system_role": group["system_role"], "trials": group["trials"],
            "models": sorted(group["models"]), "splits": sorted(group["splits"]), "dataset_ids": sorted(group["dataset_ids"]),
            "system_tree_hashes": sorted(group["tree_hashes"]),
            "metrics": {name: {"median": _median(values), "min": min(values), "max": max(values), "n": len(values)} for name, values in group["metrics"].items()},
            "task_families": {family: {name: _median(values) for name, values in metrics.items()} for family, metrics in group["task_families"].items()},
            "hard_gate_failures": group["hard_gate_failures"],
        }
    return normalized


def _delta(candidate: float, baseline: float, direction: str) -> float:
    return candidate - baseline if direction == "maximize" else baseline - candidate


def compare_systems(aggregates: Dict[str, Any], contract: Dict[str, Any]) -> Dict[str, Any]:
    baselines = [item for item in aggregates.values() if item["system_role"] == "baseline"]
    candidates = [item for item in aggregates.values() if item["system_role"] == "candidate"]
    if len(baselines) != 1:
        return {"status": "BLOCKED", "errors": ["exactly one baseline aggregate required"], "candidates": {}}
    baseline = baselines[0]
    if len(baseline.get("system_tree_hashes", [])) != 1:
        return {"status": "BLOCKED", "errors": ["baseline evidence is not bound to one exact tree hash"], "candidates": {}}
    # A broken stable version is a legitimate starting point for evolution. Its
    # hard-gate failures are baseline defects, not evidence-integrity failures.
    # Blocking here would make it impossible to promote a candidate that fixes
    # an unsafe or otherwise non-compliant baseline. Candidate hard-gate
    # failures remain non-compensatory below.
    baseline_hard_gate_failures = list(baseline.get("hard_gate_failures", []))
    results: Dict[str, Any] = {}
    for candidate in candidates:
        errors: List[str] = []
        regressions: List[Dict[str, Any]] = []
        improvements: List[Dict[str, Any]] = []
        if candidate["hard_gate_failures"]:
            errors.append("candidate has hard-gate failures")
        if len(candidate.get("system_tree_hashes", [])) != 1:
            errors.append("candidate results are not bound to one exact tree hash")
        for name, definition in contract["metrics"].items():
            if name not in baseline["metrics"] or name not in candidate["metrics"]:
                errors.append("missing comparable metric %s" % name)
                continue
            base = baseline["metrics"][name]["median"]
            cand = candidate["metrics"][name]["median"]
            delta = _delta(cand, base, definition["direction"])
            tolerance = float(definition.get("regression_tolerance", 0.0))
            entry = {"metric": name, "baseline": base, "candidate": cand, "benefit_delta": delta, "tolerance": tolerance}
            if delta < -tolerance:
                regressions.append(entry)
            elif delta > 0:
                improvements.append(entry)
        protected = set(contract.get("protected_task_families", []))
        family_regressions: List[Dict[str, Any]] = []
        for family in protected:
            base_family = baseline["task_families"].get(family)
            cand_family = candidate["task_families"].get(family)
            if not base_family or not cand_family:
                family_regressions.append({"task_family": family, "reason": "missing protected family evidence"})
                continue
            for name, definition in contract["metrics"].items():
                if name not in base_family or name not in cand_family:
                    continue
                delta = _delta(cand_family[name], base_family[name], definition["direction"])
                if delta < -float(definition.get("regression_tolerance", 0.0)):
                    family_regressions.append({"task_family": family, "metric": name, "benefit_delta": delta})
        if regressions:
            errors.append("aggregate metric regression")
        if family_regressions:
            errors.append("protected task-family negative transfer")
        if not improvements:
            errors.append("no measured improvement over baseline")
        results[candidate["system_id"]] = {
            "status": "PASS" if not errors else "FAIL", "errors": errors, "regressions": regressions,
            "improvements": improvements, "protected_family_regressions": family_regressions,
        }
    passing = [key for key, value in results.items() if value["status"] == "PASS"]
    return {
        "status": "PASS" if passing else "FAIL",
        "baseline_system_id": baseline["system_id"],
        "baseline_hard_gate_failures": baseline_hard_gate_failures,
        "candidates": results,
        "passing_candidates": passing,
    }


def pareto_frontier(aggregates: Dict[str, Any], contract: Dict[str, Any], system_ids: Iterable[str]) -> List[str]:
    ids = [item for item in system_ids if item in aggregates]
    frontier: List[str] = []
    for candidate_id in ids:
        candidate = aggregates[candidate_id]
        dominated = False
        for other_id in ids:
            if other_id == candidate_id:
                continue
            other = aggregates[other_id]
            no_worse = True
            strictly_better = False
            for name, definition in contract["metrics"].items():
                c = candidate["metrics"].get(name, {}).get("median")
                o = other["metrics"].get(name, {}).get("median")
                if c is None or o is None:
                    no_worse = False
                    break
                benefit = _delta(o, c, definition["direction"])
                if benefit < 0:
                    no_worse = False
                    break
                if benefit > 0:
                    strictly_better = True
            if no_worse and strictly_better:
                dominated = True
                break
        if not dominated:
            frontier.append(candidate_id)
    return sorted(frontier)


def _validate_result_matrix(rows: List[Dict[str, Any]], contract: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    systems = _system_map(contract)
    required_dataset_ids = set(_dataset_map(contract))
    required_models = set(contract.get("cross_model_matrix", []))
    cells_by_system: Dict[str, set] = {}
    for system_id in systems:
        system_rows = [row for row in rows if str(row.get("system_id")) == system_id]
        if not system_rows:
            errors.append("contracted system has no results: %s" % system_id)
            continue
        datasets = {str(row.get("dataset_id")) for row in system_rows}
        if datasets != required_dataset_ids:
            errors.append("system %s does not cover exactly every contracted dataset" % system_id)
        models = {str(row.get("model")) for row in system_rows}
        if required_models and not required_models.issubset(models):
            errors.append("system %s does not cover every required model" % system_id)
        cells = [result_cell(row) for row in system_rows]
        if len(cells) != len(set(cells)):
            errors.append("system %s contains duplicate comparison cells" % system_id)
        cells_by_system[system_id] = set(cells)
    baseline_ids = [system_id for system_id, item in systems.items() if item.get("role") == "baseline"]
    if len(baseline_ids) == 1 and baseline_ids[0] in cells_by_system:
        baseline_cells = cells_by_system[baseline_ids[0]]
        for system_id, cells in cells_by_system.items():
            if cells != baseline_cells:
                errors.append("system %s comparison cells differ from baseline" % system_id)
    return errors


def _compute_summary(workspace: Path, contract_path: Path, results_file: Path) -> Dict[str, Any]:
    contract = load_json(contract_path)
    rows = load_results(results_file)
    errors: List[str] = []
    seen_ids = set()
    for row in rows:
        result_id = row.get("result_id") if isinstance(row, dict) else None
        if result_id in seen_ids:
            errors.append("duplicate result_id: %s" % result_id)
        seen_ids.add(result_id)
        errors.extend(["%s: %s" % (result_id, item) for item in validate_result(row, contract, workspace)])
    errors.extend(_validate_result_matrix(rows, contract))
    if errors:
        return {"status": "BLOCKED", "errors": sorted(set(errors)), "result_count": len(rows)}
    aggregates = aggregate_results(rows, contract)
    comparison = compare_systems(aggregates, contract)
    frontier = pareto_frontier(aggregates, contract, comparison.get("passing_candidates", []))
    cell_payload = sorted([list(result_cell(row)) for row in rows if row.get("system_role") == "baseline"])
    return {
        "schema_version": "3.0", "status": comparison["status"],
        "contract_sha256": sha256_file(contract_path), "results_sha256": sha256_file(results_file),
        "comparison_cells_sha256": sha256_bytes(canonical_json(cell_payload)),
        "result_count": len(rows), "aggregates": aggregates, "comparison": comparison,
        "pareto_frontier": frontier,
        "selection_policy": "hard-gates -> one exact system tree -> identical dataset/task/trial/model/runtime cells -> no protected regression -> Pareto; no scalar score may compensate a hard regression",
    }


def evaluate_workspace(workspace: Path, results_path: Optional[Path] = None) -> Dict[str, Any]:
    workspace = workspace.resolve()
    control_errors = verify_eval_control(workspace)
    contract_path = workspace / "control/evals/evaluation-contract.json"
    if control_errors or not contract_path.is_file():
        return {"status": "BLOCKED", "errors": control_errors or ["missing eval contract"]}
    canonical_results = workspace / "evidence/evals/raw/results.jsonl"
    if results_path:
        source = results_path.resolve()
        if not source.is_file():
            return {"status": "BLOCKED", "errors": ["missing evaluation results JSONL"]}
        canonical_results.parent.mkdir(parents=True, exist_ok=True)
        if source != canonical_results.resolve():
            shutil.copyfile(source, canonical_results)
    results_file = canonical_results
    if not results_file.is_file():
        return {"status": "BLOCKED", "errors": ["missing evaluation results JSONL"]}
    try:
        summary = _compute_summary(workspace, contract_path, results_file)
    except Exception as exc:
        return {"status": "BLOCKED", "errors": ["evaluation could not safely parse evidence: %s: %s" % (type(exc).__name__, exc)]}
    if summary.get("status") == "BLOCKED":
        return summary
    summary["generated_at"] = utc_now()
    summary_dir = workspace / "evidence/evals/summary"
    summary_dir.mkdir(parents=True, exist_ok=True)
    write_json(summary_dir / "evaluation-summary.json", summary)
    return summary


def verify_evaluation_summary(workspace: Path) -> List[str]:
    """Recompute the decision from raw bound evidence; never trust a stored green summary."""
    workspace = workspace.resolve()
    errors = verify_eval_control(workspace)
    contract_path = workspace / "control/evals/evaluation-contract.json"
    results_file = workspace / "evidence/evals/raw/results.jsonl"
    summary_path = workspace / "evidence/evals/summary/evaluation-summary.json"
    if not results_file.is_file() or not summary_path.is_file():
        return errors + ["evaluation raw results or summary missing"]
    try:
        stored = load_json(summary_path)
        recomputed = _compute_summary(workspace, contract_path, results_file)
    except Exception as exc:
        return errors + ["evaluation evidence could not be recomputed: %s: %s" % (type(exc).__name__, exc)]
    if recomputed.get("status") == "BLOCKED":
        return errors + ["recomputed evaluation is blocked: %s" % message for message in recomputed.get("errors", [])]
    comparable = dict(stored)
    comparable.pop("generated_at", None)
    if comparable != recomputed:
        errors.append("stored evaluation summary differs from recomputed raw evidence")
    return errors
