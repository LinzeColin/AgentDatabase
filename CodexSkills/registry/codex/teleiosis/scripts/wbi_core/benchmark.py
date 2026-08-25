from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from .io import canonical_json, ensure_external, load_json, sha256_bytes, sha256_file, utc_now, write_json

TRACKS = {"A_OPTIMIZATION", "B_PRODUCTIZATION", "C_ASSURANCE"}
TARGET_TYPES = {"text-reasoning", "tool-artifact", "high-risk-reversible"}
SPLITS = {"dev", "validation", "sealed_holdout", "adversarial", "protected"}
REQUIRED_METRICS = {
    "trigger_precision", "trigger_recall", "task_success", "safety_success", "truthfulness",
    "protected_task_success", "latency_ms", "model_tokens", "human_minutes", "evidence_completeness",
}


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _non_negative(value: Any) -> bool:
    return not isinstance(value, bool) and isinstance(value, (int, float)) and value >= 0


def validate_benchmark_contract(contract: Dict[str, Any], *, production: bool = True) -> List[str]:
    errors: List[str] = []
    if not isinstance(contract, dict):
        return ["benchmark contract must be an object"]
    if contract.get("schema_version") != "1.0":
        errors.append("benchmark contract schema_version must be 1.0")
    if contract.get("evidence_class") not in {"REAL_TASK", "FIXTURE"}:
        errors.append("benchmark evidence_class must be REAL_TASK or FIXTURE")
    if production and contract.get("evidence_class") != "REAL_TASK":
        errors.append("production outcome benchmark requires REAL_TASK evidence")
    for key in ("benchmark_id", "valid_as_of", "created_at", "judge_oracle_id", "normalization_policy", "blind_randomization_policy"):
        if not isinstance(contract.get(key), str) or not str(contract.get(key)).strip():
            errors.append("benchmark contract %s missing" % key)
    tracks = contract.get("tracks")
    if not isinstance(tracks, list) or set(tracks) != TRACKS:
        errors.append("benchmark tracks must contain exactly A_OPTIMIZATION, B_PRODUCTIZATION and C_ASSURANCE")
    systems = contract.get("systems")
    if not isinstance(systems, list) or len(systems) < 2:
        errors.append("benchmark requires at least baseline and one candidate system")
        systems = []
    system_ids = set()
    for index, system in enumerate(systems, 1):
        if not isinstance(system, dict):
            errors.append("system %d must be an object" % index)
            continue
        sid = system.get("system_id")
        if not isinstance(sid, str) or not sid:
            errors.append("system %d id missing" % index)
        elif sid in system_ids:
            errors.append("duplicate system_id: %s" % sid)
        system_ids.add(sid)
        if system.get("role") not in {"baseline", "candidate", "comparator"}:
            errors.append("invalid system role: %s" % system.get("role"))
        if not _is_hash(system.get("tree_hash")):
            errors.append("system tree_hash invalid: %s" % sid)
    if sum(1 for item in systems if isinstance(item, dict) and item.get("role") == "baseline") != 1:
        errors.append("benchmark requires exactly one baseline system")
    if not any(isinstance(item, dict) and item.get("role") == "candidate" for item in systems):
        errors.append("benchmark requires at least one candidate system")

    targets = contract.get("targets")
    minimum = int(contract.get("minimum_targets", 6)) if isinstance(contract.get("minimum_targets", 6), int) else 6
    if not isinstance(targets, list) or len(targets) < minimum:
        errors.append("benchmark requires at least %d targets" % minimum)
        targets = []
    target_ids = set()
    type_counts = {key: 0 for key in TARGET_TYPES}
    for index, target in enumerate(targets, 1):
        if not isinstance(target, dict):
            errors.append("target %d must be an object" % index)
            continue
        tid = target.get("target_id")
        if not isinstance(tid, str) or not tid:
            errors.append("target %d id missing" % index)
        elif tid in target_ids:
            errors.append("duplicate target_id: %s" % tid)
        target_ids.add(tid)
        kind = target.get("target_type")
        if kind not in TARGET_TYPES:
            errors.append("invalid target_type for %s" % tid)
        else:
            type_counts[kind] += 1
        if not _is_hash(target.get("baseline_tree_hash")):
            errors.append("target baseline_tree_hash invalid: %s" % tid)
        datasets = target.get("datasets")
        if not isinstance(datasets, dict):
            errors.append("target datasets missing: %s" % tid)
            continue
        for split in SPLITS:
            descriptor = datasets.get(split)
            if not isinstance(descriptor, dict):
                errors.append("target %s missing split %s" % (tid, split))
                continue
            for key in ("dataset_id", "dataset_hash"):
                if not isinstance(descriptor.get(key), str) or not descriptor.get(key):
                    errors.append("target %s %s.%s missing" % (tid, split, key))
            if not _is_hash(descriptor.get("dataset_hash")):
                errors.append("target %s %s dataset_hash invalid" % (tid, split))
            forbidden = {"content", "prompts", "items", "examples", "questions"}.intersection(descriptor)
            if forbidden:
                errors.append("sealed benchmark descriptor leaks content keys for %s/%s: %s" % (tid, split, sorted(forbidden)))
            if split == "sealed_holdout":
                if not isinstance(descriptor.get("external_pointer"), str) or not Path(str(descriptor.get("external_pointer"))).is_absolute():
                    errors.append("sealed holdout pointer must be absolute and external for %s" % tid)
                if production and int(descriptor.get("item_count", 0)) < 20:
                    errors.append("sealed holdout requires at least 20 items for %s" % tid)
    if production:
        for kind, count in type_counts.items():
            if count < 2:
                errors.append("production benchmark requires at least two %s targets" % kind)

    execution = contract.get("execution")
    if not isinstance(execution, dict):
        errors.append("benchmark execution contract missing")
    else:
        if production and int(execution.get("trials_per_cell", 0)) < 3:
            errors.append("production benchmark requires at least three stochastic trials per cell")
        for key in ("runtime", "model", "tool_permissions", "context_window", "sampling"):
            if key not in execution:
                errors.append("execution.%s missing" % key)
    budget = contract.get("budget")
    if not isinstance(budget, dict):
        errors.append("benchmark budget missing")
    else:
        token_limit = budget.get("max_model_tokens")
        if token_limit is None:
            if production:
                errors.append("production budget.max_model_tokens must be measured and non-negative")
        elif not _non_negative(token_limit):
            errors.append("budget.max_model_tokens must be null or non-negative")
        for key in ("max_calls", "max_wall_seconds", "max_human_minutes"):
            if not _non_negative(budget.get(key)):
                errors.append("budget.%s must be non-negative" % key)
        cost = budget.get("max_monetary_cost")
        if cost is not None and not _non_negative(cost):
            errors.append("budget.max_monetary_cost must be null or non-negative")
    acceptance = contract.get("acceptance")
    if not isinstance(acceptance, dict):
        errors.append("benchmark acceptance rules missing")
    else:
        if not _non_negative(acceptance.get("minimum_task_success_delta")):
            errors.append("acceptance.minimum_task_success_delta must be non-negative")
        if not _non_negative(acceptance.get("maximum_protected_regression")):
            errors.append("acceptance.maximum_protected_regression must be non-negative")
        if acceptance.get("hard_gate_compensation_allowed") is not False:
            errors.append("hard gate compensation must be false")
    if contract.get("candidate_can_read_holdout") is not False:
        errors.append("candidate_can_read_holdout must be false")
    return sorted(set(errors))


def seal_benchmark_contract(workspace: Path, source: Path, actor_id: str, optimizer_root: Optional[Path] = None) -> Dict[str, Any]:
    workspace = workspace.resolve()
    source = source.resolve()
    contract = load_json(source)
    errors = validate_benchmark_contract(contract, production=bool(contract.get("production", True)))
    if errors:
        return {"seal_status": "FAIL", "errors": errors}
    if optimizer_root is not None:
        ensure_external(workspace, [optimizer_root.resolve()], "benchmark workspace")
    destination = workspace / "control/contracts/benchmark-contract.json"
    if destination.exists():
        existing = load_json(destination)
        if sha256_bytes(canonical_json(existing)) != sha256_bytes(canonical_json(contract)):
            return {"seal_status": "FAIL", "errors": ["benchmark contract already sealed with different content"]}
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)
        write_json(destination, contract)
        try:
            destination.chmod(0o444)
        except OSError:
            pass
    receipt = {
        "schema_version": "1.0",
        "seal_status": "SEALED",
        "actor_id": actor_id,
        "sealed_at": utc_now(),
        "contract_path": str(destination),
        "contract_sha256": sha256_file(destination),
        "canonical_sha256": sha256_bytes(canonical_json(contract)),
    }
    write_json(workspace / "control/contracts/benchmark-seal.json", receipt)
    return receipt


def _load_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows = []
    for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("benchmark result line %d is not an object" % number)
        rows.append(value)
    return rows


def _system_map(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item["system_id"]): item for item in contract.get("systems", []) if isinstance(item, dict) and item.get("system_id")}


def _target_map(contract: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    return {str(item["target_id"]): item for item in contract.get("targets", []) if isinstance(item, dict) and item.get("target_id")}


def validate_benchmark_result(row: Dict[str, Any], contract: Dict[str, Any], workspace: Path) -> List[str]:
    errors: List[str] = []
    systems, targets = _system_map(contract), _target_map(contract)
    for key in ("result_id", "system_id", "target_id", "track", "split", "trial", "runtime", "model", "started_at", "finished_at"):
        if key not in row:
            errors.append("result %s missing" % key)
    sid, tid = row.get("system_id"), row.get("target_id")
    if sid not in systems:
        errors.append("unknown benchmark system_id: %s" % sid)
    elif row.get("system_tree_hash") != systems[sid].get("tree_hash"):
        errors.append("benchmark result system tree hash mismatch")
    if tid not in targets:
        errors.append("unknown benchmark target_id: %s" % tid)
    elif row.get("target_tree_hash") != targets[tid].get("baseline_tree_hash"):
        errors.append("benchmark result target tree hash mismatch")
    if row.get("track") not in TRACKS:
        errors.append("invalid benchmark track")
    if row.get("split") not in SPLITS:
        errors.append("invalid benchmark split")
    if not isinstance(row.get("trial"), int) or isinstance(row.get("trial"), bool) or int(row.get("trial", 0)) < 1:
        errors.append("benchmark trial must be a positive integer")
    execution = contract.get("execution", {})
    if row.get("runtime") != execution.get("runtime") or row.get("model") != execution.get("model"):
        errors.append("benchmark result runtime/model differs from frozen execution contract")
    metrics = row.get("metrics")
    if not isinstance(metrics, dict):
        errors.append("benchmark metrics missing")
    else:
        for key in REQUIRED_METRICS:
            if key not in metrics:
                errors.append("benchmark metric missing or invalid: %s" % key)
            elif key == "model_tokens":
                if metrics.get(key) is not None and not _non_negative(metrics.get(key)):
                    errors.append("benchmark metric missing or invalid: %s" % key)
            elif not _non_negative(metrics.get(key)):
                errors.append("benchmark metric missing or invalid: %s" % key)
        for key in ("trigger_precision", "trigger_recall", "task_success", "safety_success", "truthfulness", "protected_task_success", "evidence_completeness"):
            if _non_negative(metrics.get(key)) and float(metrics[key]) > 1.0:
                errors.append("benchmark metric %s must be within 0..1" % key)
    hard_gates = row.get("hard_gates")
    if not isinstance(hard_gates, dict) or not hard_gates:
        errors.append("benchmark hard_gates missing")
    elif any(value not in {"PASS", "FAIL"} for value in hard_gates.values()):
        errors.append("benchmark hard_gates must be PASS or FAIL")
    budget = row.get("budget")
    if not isinstance(budget, dict):
        errors.append("benchmark budget evidence missing")
    else:
        token_state = budget.get("token_evidence_status")
        if token_state not in {"MEASURED", "ESTIMATED", "UNKNOWN"}:
            errors.append("benchmark token_evidence_status invalid")
        model_tokens = budget.get("model_tokens")
        if token_state == "UNKNOWN":
            if model_tokens is not None:
                errors.append("UNKNOWN benchmark token usage must use null, never zero")
        elif not _non_negative(model_tokens):
            errors.append("benchmark budget.model_tokens invalid")
        for key in ("calls", "wall_seconds", "human_minutes"):
            if not _non_negative(budget.get(key)):
                errors.append("benchmark budget.%s invalid" % key)
        cost_state = budget.get("monetary_cost_status")
        if cost_state not in {"MEASURED", "ESTIMATED", "UNKNOWN"}:
            errors.append("benchmark monetary_cost_status invalid")
        monetary_cost = budget.get("monetary_cost")
        if cost_state == "UNKNOWN":
            if monetary_cost is not None:
                errors.append("UNKNOWN benchmark monetary cost must use null, never zero")
        elif not _non_negative(monetary_cost):
            errors.append("benchmark monetary cost invalid")
        if isinstance(metrics, dict):
            metric_tokens = metrics.get("model_tokens")
            if token_state == "UNKNOWN" and metric_tokens is not None:
                errors.append("benchmark metrics.model_tokens must be null when token usage is UNKNOWN")
            elif token_state != "UNKNOWN" and metric_tokens != model_tokens:
                errors.append("benchmark metric and budget model_tokens differ")
    for prefix in ("raw_result", "process_trace"):
        relative = row.get(prefix + "_path")
        digest = row.get(prefix + "_sha256")
        if not isinstance(relative, str) or Path(relative).is_absolute() or ".." in Path(relative).parts:
            errors.append("unsafe or missing %s path" % prefix)
            continue
        path = (workspace / relative).resolve()
        if workspace not in path.parents or not path.is_file() or path.is_symlink():
            errors.append("%s file missing or outside workspace" % prefix)
        elif not _is_hash(digest) or sha256_file(path) != digest:
            errors.append("%s hash mismatch" % prefix)
    return sorted(set(errors))


def _mean(values: Sequence[float]) -> float:
    return sum(values) / float(len(values)) if values else 0.0


def _group(rows: Iterable[Dict[str, Any]]) -> Dict[Tuple[str, str, str, str], List[Dict[str, Any]]]:
    groups: Dict[Tuple[str, str, str, str], List[Dict[str, Any]]] = {}
    for row in rows:
        key = (str(row["system_id"]), str(row["target_id"]), str(row["track"]), str(row["split"]))
        groups.setdefault(key, []).append(row)
    return groups


def evaluate_benchmark(workspace: Path, results_file: Path) -> Dict[str, Any]:
    workspace, results_file = workspace.resolve(), results_file.resolve()
    contract_path = workspace / "control/contracts/benchmark-contract.json"
    if not contract_path.is_file():
        return {"benchmark_integrity_status": "INVALID", "outcome_status": "UNKNOWN", "errors": ["sealed benchmark contract missing"]}
    contract = load_json(contract_path)
    errors = validate_benchmark_contract(contract, production=bool(contract.get("production", True)))
    rows = _load_jsonl(results_file)
    result_ids = set()
    for index, row in enumerate(rows, 1):
        errors.extend("row %d: %s" % (index, item) for item in validate_benchmark_result(row, contract, workspace))
        rid = row.get("result_id")
        if rid in result_ids:
            errors.append("duplicate benchmark result_id: %s" % rid)
        result_ids.add(rid)

    groups = _group(rows)
    trials = int(contract.get("execution", {}).get("trials_per_cell", 1))
    systems, targets = _system_map(contract), _target_map(contract)
    required_splits = {"sealed_holdout", "adversarial", "protected"}
    missing = []
    for sid in systems:
        for tid in targets:
            for track in TRACKS:
                for split in required_splits:
                    count = len(groups.get((sid, tid, track, split), []))
                    if count < trials:
                        missing.append("%s/%s/%s/%s=%d<%d" % (sid, tid, track, split, count, trials))
    if missing:
        errors.append("benchmark matrix incomplete: %s" % ", ".join(missing[:20]))

    budget_limit = contract.get("budget", {})
    budget_violations = []
    per_system_budget: Dict[str, Dict[str, Any]] = {}
    for sid in systems:
        subset = [row for row in rows if row.get("system_id") == sid]
        token_values = [row["budget"].get("model_tokens") for row in subset]
        unknown_tokens = sum(1 for value in token_values if value is None)
        known_tokens = sum(float(value) for value in token_values if value is not None)
        monetary_values = [row["budget"].get("monetary_cost") for row in subset]
        unknown_monetary = sum(1 for value in monetary_values if value is None)
        known_monetary = sum(float(value) for value in monetary_values if value is not None)
        totals = {
            "model_tokens": None if unknown_tokens else known_tokens,
            "known_model_tokens": known_tokens,
            "unknown_token_results": unknown_tokens,
            "calls": sum(float(row["budget"]["calls"]) for row in subset),
            "wall_seconds": sum(float(row["budget"]["wall_seconds"]) for row in subset),
            "human_minutes": sum(float(row["budget"]["human_minutes"]) for row in subset),
            "monetary_cost": None if unknown_monetary else known_monetary,
            "known_monetary_cost": known_monetary,
            "unknown_monetary_cost_results": unknown_monetary,
        }
        per_system_budget[sid] = totals
        mapping = {
            "model_tokens": "max_model_tokens", "calls": "max_calls", "wall_seconds": "max_wall_seconds",
            "human_minutes": "max_human_minutes", "monetary_cost": "max_monetary_cost",
        }
        for field, limit_field in mapping.items():
            limit = budget_limit.get(limit_field)
            if field in {"model_tokens", "monetary_cost"} and limit is not None and totals[field] is None:
                budget_violations.append("%s has unknown %s under a finite %s" % (sid, field, limit_field))
            elif limit is not None and totals[field] is not None and totals[field] > float(limit):
                budget_violations.append("%s exceeds %s" % (sid, limit_field))
    errors.extend("BUDGET_VIOLATION: %s" % item for item in budget_violations)
    budget_evidence_gaps = [
        "%s has unknown model token usage; equal-budget outcome is not proven" % sid
        for sid, totals in per_system_budget.items() if totals.get("unknown_token_results", 0) > 0
    ]

    aggregates: Dict[str, Any] = {}
    for sid in systems:
        subset = [row for row in rows if row.get("system_id") == sid and row.get("split") in required_splits]
        aggregates[sid] = {}
        for metric in sorted(REQUIRED_METRICS):
            metric_values = [row["metrics"].get(metric) for row in subset]
            known_values = [float(value) for value in metric_values if value is not None]
            aggregates[sid][metric] = (
                None if not subset or (metric == "model_tokens" and len(known_values) != len(metric_values))
                else _mean(known_values)
            )
        aggregates[sid]["all_hard_gates_pass"] = bool(subset) and all(all(value == "PASS" for value in row["hard_gates"].values()) for row in subset)
        aggregates[sid]["budget"] = per_system_budget.get(sid, {})

    baseline_ids = [sid for sid, system in systems.items() if system.get("role") == "baseline"]
    candidate_ids = [sid for sid, system in systems.items() if system.get("role") == "candidate"]
    outcome = "NOT_PROVEN"
    selected = None
    claim_reasons: List[str] = []
    if not errors and baseline_ids and candidate_ids:
        baseline_id = baseline_ids[0]
        baseline = aggregates[baseline_id]
        acceptance = contract["acceptance"]
        minimum_delta = float(acceptance["minimum_task_success_delta"])
        maximum_regression = float(acceptance["maximum_protected_regression"])
        qualifying = []
        for sid in candidate_ids:
            candidate = aggregates[sid]
            if not candidate["all_hard_gates_pass"]:
                claim_reasons.append("%s has a hard-gate failure" % sid)
                continue
            task_delta = float(candidate["task_success"]) - float(baseline["task_success"])
            protected_delta = float(candidate["protected_task_success"]) - float(baseline["protected_task_success"])
            if task_delta < minimum_delta:
                claim_reasons.append("%s task delta %.6f below %.6f" % (sid, task_delta, minimum_delta))
                continue
            if protected_delta < -maximum_regression:
                claim_reasons.append("%s protected regression %.6f exceeds %.6f" % (sid, protected_delta, maximum_regression))
                continue
            qualifying.append((sid, task_delta, protected_delta))
        if qualifying:
            qualifying.sort(key=lambda item: (-item[1], -item[2], item[0]))
            selected = qualifying[0][0]
            outcome = "SUPPORTED"
        else:
            all_regressed = all(
                float(aggregates[sid]["task_success"]) < float(baseline["task_success"]) for sid in candidate_ids
            ) if candidate_ids else False
            outcome = "REGRESSED" if all_regressed else "NOT_PROVEN"
    diagnostic_selected = selected
    if contract.get("evidence_class") == "FIXTURE":
        if outcome == "SUPPORTED":
            claim_reasons.append("deterministic fixture validates the runner, not real-task outcome superiority")
        outcome = "NOT_PROVEN"
        selected = None
    integrity = "VALID" if not errors else ("INCOMPLETE" if any("matrix incomplete" in item for item in errors) else "INVALID")
    if integrity == "VALID" and budget_evidence_gaps:
        integrity = "INCOMPLETE"
        claim_reasons.extend(budget_evidence_gaps)
    if integrity != "VALID" and outcome == "SUPPORTED":
        outcome = "NOT_PROVEN"
        selected = None
    if outcome != "SUPPORTED":
        selected = None
    summary = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "benchmark_integrity_status": integrity,
        "outcome_status": outcome,
        "outcome_claim_allowed": outcome == "SUPPORTED" and integrity == "VALID" and contract.get("evidence_class") == "REAL_TASK",
        "selected_candidate": selected,
        "diagnostic_selected_candidate": diagnostic_selected,
        "contract_sha256": sha256_file(contract_path),
        "results_sha256": sha256_file(results_file),
        "aggregates": aggregates,
        "budget_violations": budget_violations,
        "budget_evidence_gaps": budget_evidence_gaps,
        "claim_reasons": claim_reasons,
        "errors": sorted(set(errors)),
    }
    output = workspace / "evidence/benchmark/benchmark-summary.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, summary)
    return summary
