from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import load_json, sha256_bytes, canonical_json, utc_now, write_json


def _candidate_portfolio(target_class: str, risk_level: str) -> List[Dict[str, Any]]:
    incremental = {
        "candidate_id": "incremental",
        "purpose": "repair the highest-evidence bottleneck with the smallest attributable patch",
        "change_budget": "small",
        "max_candidate_growth_ratio": 1.20,
    }
    architecture = {
        "candidate_id": "architecture",
        "purpose": "move repeated policy into scripts, contracts or progressive references",
        "change_budget": "medium",
        "max_candidate_growth_ratio": 1.50,
    }
    clean_slate = {
        "candidate_id": "clean-slate",
        "purpose": "escape local optimum while preserving the frozen baseline as fallback",
        "change_budget": "large-but-bounded",
        "max_candidate_growth_ratio": 1.50,
    }
    trigger = {
        "candidate_id": "trigger-and-clarity",
        "purpose": "improve activation precision, workflow clarity and failure branches without product sprawl",
        "change_budget": "small",
        "max_candidate_growth_ratio": 1.15,
    }
    product = {
        "candidate_id": "productization",
        "purpose": "improve installability, reproducible showcase and real-artifact reconciliation",
        "change_budget": "medium",
        "max_candidate_growth_ratio": 1.40,
    }
    prune_substitute = {
        "candidate_id": "prune-and-substitute",
        "purpose": "remove low-value or conflicting instructions and replace them with higher-evidence mechanisms under a frozen utility contract",
        "change_budget": "medium",
        "max_candidate_growth_ratio": 1.10,
    }
    coverage_repair = {
        "candidate_id": "coverage-repair",
        "purpose": "strengthen uncovered or failed declared Skill behaviors identified from trajectories without overfitting to prompt text",
        "change_budget": "medium",
        "max_candidate_growth_ratio": 1.25,
    }
    retrieval_routing = {
        "candidate_id": "retrieval-and-routing",
        "purpose": "reduce false activation, selection confusion and library-scale Skill shadowing",
        "change_budget": "small",
        "max_candidate_growth_ratio": 1.15,
    }
    bilevel = {
        "candidate_id": "structure-content-bilevel",
        "purpose": "optimize Skill structure and content in separate attributable stages while preserving a rollback path",
        "change_budget": "large-but-bounded",
        "max_candidate_growth_ratio": 1.40,
    }
    if target_class == "text-and-reasoning":
        return [trigger, retrieval_routing, coverage_repair, incremental, prune_substitute, clean_slate]
    if target_class == "artifact-productization":
        return [incremental, product, coverage_repair, prune_substitute, architecture]
    if target_class == "high-risk-or-side-effecting" or risk_level == "high":
        # High-risk targets can still explore architecture, but clean-slate candidates
        # are not the default because broad rewrites weaken attribution and review.
        return [incremental, coverage_repair, architecture]
    return [incremental, retrieval_routing, coverage_repair, prune_substitute, architecture, bilevel, clean_slate]


def _metric_focus(target_class: str) -> List[str]:
    common = ["task_success", "instruction_compliance", "behavior_coverage", "skill_selection_accuracy", "negative_transfer", "token_cost", "human_minutes"]
    if target_class == "text-and-reasoning":
        return ["trigger_precision", "trigger_recall", "task_quality"] + common
    if target_class == "artifact-productization":
        return ["artifact_correctness", "install_success", "showcase_reproducibility"] + common
    if target_class == "high-risk-or-side-effecting":
        return ["safety_gate_pass", "reversibility", "least_privilege", "auditability"] + common
    return ["runtime_portability", "artifact_correctness", "recovery_success"] + common


def _budget(file_count: int, risk_level: str, run_mode: str) -> Dict[str, Any]:
    if file_count <= 40:
        scale = "small"
        rounds, branches, patch_lines = 6, 3, 240
    elif file_count <= 500:
        scale = "medium"
        rounds, branches, patch_lines = 10, 3, 600
    else:
        scale = "large"
        rounds, branches, patch_lines = 12, 4, 1200
    if risk_level == "high":
        patch_lines = min(patch_lines, 500)
    if run_mode == "diagnostic":
        rounds = 0
        branches = 0
        patch_lines = 0
    return {
        "scale": scale,
        "max_iteration_rounds": rounds,
        "max_parallel_candidates": branches,
        "max_changed_lines_per_candidate": patch_lines,
        "max_repeated_failed_mechanism": 2,
        "max_no_change_rounds_before_saturation": 3,
        "equal_budget_required_for_outcome_claim": True,
        "unknown_usage_is_zero": False,
    }


def build_adaptive_plan(
    diagnostic: Dict[str, Any],
    *,
    run_mode: str = "engineering",
    output: Optional[Path] = None,
) -> Dict[str, Any]:
    if run_mode not in {"diagnostic", "engineering", "formal"}:
        raise ValueError("run_mode must be diagnostic, engineering or formal")
    if not isinstance(diagnostic, dict) or "classification" not in diagnostic or "target" not in diagnostic:
        raise ValueError("diagnostic must be a Teleiosis target-diagnostic object")
    classification = diagnostic["classification"]
    target = diagnostic["target"]
    target_class = str(classification.get("target_class", "text-and-reasoning"))
    risk_level = str(classification.get("risk_level", "low"))
    diagnostic_status = str(diagnostic.get("diagnostic_status", "BLOCKED"))
    blockers = list(diagnostic.get("blockers", []))
    portfolio = _candidate_portfolio(target_class, risk_level)
    budget = _budget(int(target.get("file_count", 0)), risk_level, run_mode)

    required_gates = [
        "frozen-baseline-and-candidate-only-edits",
        "premise-challenge-and-at-least-five-real-peers",
        "research-benchmark-holdout-budget-and-review-seals-before-mutation",
        "track-A-outcome-track-B-productization-track-C-assurance-kept-separate",
        "mandatory-metric-negative-transfer-blocks-promotion",
        "deterministic-package-install-recovery-and-rollback",
    ]
    if risk_level == "high":
        required_gates.extend(["least-privilege-action-review", "deep-verification-before-switch"])
    if run_mode == "formal":
        required_gates.append("external-signed-2x6-plus-distinct-read-only-verifier")

    plan_status = "BLOCKED" if diagnostic_status == "BLOCKED" else "READY"
    if run_mode == "diagnostic":
        next_action = "Review diagnosis and frozen evidence; diagnostic mode performs no candidate mutation."
    elif plan_status == "BLOCKED":
        next_action = "Resolve diagnosis blockers before freezing contracts or mutating a candidate."
    else:
        next_action = "Freeze contracts, establish real peers and benchmark, then start the smallest attributable candidate."

    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "plan_status": plan_status,
        "generated_at": utc_now(),
        "run_mode": run_mode,
        "target_binding": {
            "path": target.get("path"),
            "tree_sha256": target.get("tree_sha256"),
            "diagnostic_sha256": sha256_bytes(canonical_json(diagnostic)),
        },
        "profile": {
            "target_class": target_class,
            "risk_level": risk_level,
            "verification_level": "deep" if risk_level == "high" else classification.get("suggested_verification_level", "release"),
            "evidence_completeness": classification.get("evidence_completeness", "UNKNOWN"),
        },
        "optimization_objectives": _metric_focus(target_class),
        "candidate_portfolio": portfolio,
        "budget": budget,
        "required_gates": required_gates + [
            "declared-skill-behavior-coverage-measured",
            "library-scale-trigger-selection-and-shadowing-evaluated-when-in-scope",
            "stochastic-trials-use-predeclared-inconclusive-supported-regressed-semantics",
            "final-output-carries-current-environment-evidence-lease",
        ],
        "negative_optimization_guard": {
            "rule": "KEEP only when mandatory metrics and hard gates do not regress under the frozen equal-budget contract.",
            "fallback": "REVERT to the frozen baseline or last independently verified candidate.",
            "size_rule": "Growth beyond the candidate-specific ratio requires measured outcome or maintainability benefit; prose volume is not benefit.",
            "unknown_rule": "UNKNOWN, NOT_RUN and PARTIAL evidence never become PASS or zero cost.",
        },
        "strategy_memory_policy": {
            "record_rejected_edits": True,
            "suppress_repeated_failed_mechanism_after": 2,
            "detect_scope_oscillation": True,
            "reheat_after_saturation_or_frontier_change": True,
            "retain_cross_session_decision_history": True,
            "track_behavior_coverage_and_shadowing": True,
        },
        "reading_order": [
            "references/ADAPTIVE_OPTIMIZATION.md",
            "references/WORKFLOW.md",
            "references/BENCHMARK_PROTOCOL.md",
            "references/STRATEGY_MEMORY.md",
            "references/TRUTHFUL_SHOWCASE.md",
        ],
        "blockers": blockers,
        "next_action": next_action,
        "claim_boundary": "This plan selects a process profile; it does not prove that any candidate improves real task outcomes.",
    }
    if output is not None:
        write_json(output.resolve(), result)
    return result


def build_adaptive_plan_file(diagnostic_path: Path, *, run_mode: str, output: Optional[Path] = None) -> Dict[str, Any]:
    return build_adaptive_plan(load_json(diagnostic_path.resolve()), run_mode=run_mode, output=output)
