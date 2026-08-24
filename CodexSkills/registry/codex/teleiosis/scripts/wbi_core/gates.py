from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .evaluation import verify_eval_control, verify_evaluation_summary
from .freshness import reheat_status
from .genesis import verify_genesis
from .io import load_json, sha256_file, sha256_tree, verify_file_bindings
from .ledger import verify_event_chain
from .luban import validate_luban_gates
from .reviews import review_gate
from .security import validate_authority
from .validation import detect_profile, validate_skill
from .workspace import audit_budget, reconcile_state_with_ledger, verify_control_plane, verify_run_seal

TEN_PERSPECTIVES = {
    "requirements-scope-pain", "peers-ecosystem-reuse", "triggering-boundaries", "workflow-failure-branches",
    "security-authority-supply-chain", "architecture-progressive-disclosure", "evaluation-holdout-transfer",
    "runtime-install-release-rollback", "efficiency-maintenance-cost", "live-artifacts-future-blindspots",
}


def _validate_requirement_coverage(workspace: Path, optimizer_root: Path, run: Dict[str, Any]) -> Dict[str, Any]:
    path = workspace / "evidence/validation/requirement-coverage.json"
    errors: List[str] = []
    if not path.is_file():
        return {"status": "BLOCKED", "errors": ["requirement coverage evidence missing"]}
    try:
        value = load_json(path)
    except Exception as exc:
        return {"status": "BLOCKED", "errors": ["invalid requirement coverage evidence: %s" % exc]}
    if value.get("baseline_id") != run.get("genesis", {}).get("baseline_id") or value.get("baseline_hash") != run.get("genesis", {}).get("baseline_hash"):
        errors.append("requirement coverage is not bound to the run Genesis")
    if value.get("valid_as_of") != run.get("valid_as_of"):
        errors.append("requirement coverage valid_as_of differs from frozen run date")
    source = load_json(optimizer_root / "constitution/requirements.json")
    expected = [item.get("id") for item in source.get("requirements", [])]
    records = value.get("requirements")
    if not isinstance(records, list):
        return {"status": "BLOCKED", "errors": errors + ["requirement coverage records must be a list"]}
    ids = [item.get("id") for item in records if isinstance(item, dict)]
    if ids != expected:
        errors.append("requirement coverage IDs are missing, reordered or duplicated")
    blocked: List[str] = []
    for record in records:
        if not isinstance(record, dict):
            errors.append("invalid requirement coverage record")
            continue
        rid = str(record.get("id"))
        if record.get("status") != "PASS":
            blocked.append(rid)
        bindings = record.get("evidence_bindings")
        if not isinstance(bindings, list) or not bindings:
            errors.append("requirement %s lacks hashed evidence bindings" % rid)
            continue
        errors.extend(["%s: %s" % (rid, item) for item in verify_file_bindings(workspace, bindings, label="requirement evidence")])
    if blocked:
        errors.append("Genesis requirements not proven PASS: %s" % blocked)
    return {"status": "PASS" if not errors else "BLOCKED", "errors": errors, "blocked_requirements": blocked}


def _gate_workspace_inner(workspace: Path, as_of: str = "") -> Dict[str, Any]:
    workspace = workspace.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    summary: Dict[str, Any] = {}
    run_path = workspace / "run.json"
    state_path = workspace / "state.json"
    if not run_path.is_file() or not state_path.is_file():
        return {"status": "BLOCKED", "errors": ["run.json/state.json missing"], "warnings": [], "summary": {}}
    run = load_json(run_path)
    state = load_json(state_path)
    if run.get("run_id") != state.get("run_id"):
        errors.append("run/state run_id mismatch")
    errors.extend(verify_event_chain(workspace / "events.jsonl"))
    errors.extend(["RUN_SEAL: %s" % item for item in verify_run_seal(workspace, run)])
    errors.extend(["CONTROL_PLANE: %s" % item for item in verify_control_plane(workspace, run)])
    errors.extend(["STATE_LEDGER: %s" % item for item in reconcile_state_with_ledger(workspace, run, state)])

    baseline = Path(run["target"]["baseline_path"])
    if sha256_tree(baseline, exclude={"MANIFEST.sha256"}) != run["target"]["baseline_tree_hash"]:
        errors.append("frozen baseline changed")
    optimizer_root = Path(run["control_plane"]["optimizer_root"])
    stable_path = Path(run.get("stable", {}).get("path", ""))
    if not stable_path.is_dir() or sha256_tree(stable_path, exclude={"MANIFEST.sha256"}) != run.get("stable", {}).get("tree_hash"):
        errors.append("stable target/optimizer tree changed during run")
    genesis = verify_genesis(optimizer_root, expected_hash=run.get("genesis", {}).get("baseline_hash", ""))
    if genesis.get("status") != "PASS":
        errors.extend(["GENESIS: %s" % item for item in genesis.get("errors", [])])

    freshness_path = workspace / "evidence/research/freshness/freshness-scan.json"
    if not freshness_path.is_file():
        errors.append("freshness scan missing")
    else:
        freshness = load_json(freshness_path)
        if freshness.get("status") != "PASS":
            errors.append("freshness scan did not PASS")
        current = reheat_status(freshness_path, as_of)
        if current["status"] != "CURRENT":
            errors.append("freshness evidence expired or blocked: REHEAT_REQUIRED")
        summary["freshness"] = current

    luban = validate_luban_gates(workspace)
    if luban["status"] != "PASS":
        errors.extend(["LUBAN: %s" % item for item in luban["errors"]])
    warnings.extend(luban.get("warnings", []))
    summary["luban"] = luban["status"]

    security = validate_authority(workspace)
    if security["status"] != "PASS":
        errors.extend(["SECURITY: %s" % item for item in security["errors"]])
    warnings.extend(security.get("warnings", []))
    summary["security"] = security["status"]

    coverage = _validate_requirement_coverage(workspace, optimizer_root, run)
    if coverage["status"] != "PASS":
        errors.extend(["GENESIS_COVERAGE: %s" % item for item in coverage["errors"]])
    summary["genesis_coverage"] = coverage["status"]

    eval_errors = verify_eval_control(workspace)
    errors.extend(["EVAL_CONTROL: %s" % item for item in eval_errors])
    eval_evidence_errors = verify_evaluation_summary(workspace)
    errors.extend(["EVAL_EVIDENCE: %s" % item for item in eval_evidence_errors])
    eval_summary_path = workspace / "evidence/evals/summary/evaluation-summary.json"
    evaluation = None
    if not eval_summary_path.is_file():
        errors.append("evaluation summary missing")
    else:
        evaluation = load_json(eval_summary_path)
        if evaluation.get("status") != "PASS" or not evaluation.get("pareto_frontier"):
            errors.append("no candidate passed multidimensional evaluation/Pareto gate")
        summary["evaluation"] = evaluation.get("status")

    rounds: List[Dict[str, Any]] = []
    for path in sorted((workspace / "rounds").glob("round-*.json")):
        try:
            rounds.append(load_json(path))
        except Exception as exc:
            errors.append("invalid round record %s: %s" % (path.name, exc))
    if len(rounds) < 10:
        errors.append("ten mandatory system-review rounds are incomplete")
    numbers = [item.get("round") for item in rounds]
    if numbers != list(range(1, len(numbers) + 1)):
        errors.append("round numbers are not contiguous")
    if {item.get("perspective") for item in rounds[:10]} != TEN_PERSPECTIVES:
        errors.append("first ten rounds do not cover the ten required system perspectives")
    for item in rounds:
        if item.get("decision") not in {"KEEP", "REVERT", "NO_CHANGE"}:
            errors.append("round %s decision invalid" % item.get("round"))
        if "candidate_comparison" not in item or "residual_risk" not in item:
            errors.append("round %s comparison/risk incomplete" % item.get("round"))
        errors.extend(["ROUND_%s: %s" % (item.get("round"), message) for message in verify_file_bindings(workspace, item.get("evidence_bindings"), label="round evidence")])
    if len(rounds) > int(run["budget"]["max_total_rounds"]):
        errors.append("round budget exceeded")
    summary["rounds"] = len(rounds)
    if int(state.get("rounds_completed", -1)) != len(rounds):
        errors.append("state round counter differs from immutable round records")
    change_records = sorted((workspace / "evidence/changes").glob("*.json"))
    ledger_change_count = sum(int(item.get("change_count", 0)) for item in run.get("target", {}).get("candidates", []))
    if int(state.get("changes_recorded", -1)) != len(change_records) or ledger_change_count != len(change_records):
        errors.append("change counters differ from white-box change records")
    known_candidates = {item.get("candidate_id") for item in run.get("target", {}).get("candidates", [])}
    observed_architecture_resets = 0
    for record_path in change_records:
        try:
            change = load_json(record_path)
        except Exception as exc:
            errors.append("invalid change record %s: %s" % (record_path.name, exc))
            continue
        prefix = "CHANGE_%s" % change.get("change_id", record_path.stem)
        if change.get("run_id") != run.get("run_id") or change.get("candidate_id") not in known_candidates:
            errors.append("%s: run/candidate binding invalid" % prefix)
        if change.get("decision") not in {"KEEP", "REVERT", "NO_CHANGE"}:
            errors.append("%s: decision invalid" % prefix)
        if not isinstance(change.get("architecture_reset", False), bool):
            errors.append("%s: architecture_reset invalid" % prefix)
        elif change.get("architecture_reset"):
            observed_architecture_resets += 1
        errors.extend(["%s: %s" % (prefix, message) for message in verify_file_bindings(workspace, change.get("evidence_bindings"), label="change evidence")])
        raw_bindings = change.get("raw_result_bindings", [])
        if raw_bindings:
            errors.extend(["%s: %s" % (prefix, message) for message in verify_file_bindings(workspace, raw_bindings, label="raw result")])
        errors.extend(["%s: %s" % (prefix, message) for message in verify_file_bindings(workspace, [change.get("exact_diff_binding")], label="exact diff")])
    if observed_architecture_resets != int(state.get("architecture_resets_used", -1)):
        errors.append("architecture reset counter differs from white-box change records")

    budget_audit = audit_budget(workspace)
    if budget_audit["violations"]:
        errors.extend(["BUDGET: %s" % item for item in budget_audit["violations"]])
    summary["budget"] = budget_audit["status"]

    reviews = review_gate(workspace)
    if reviews["status"] != "PASS":
        if reviews["status"] == "INDEPENDENT_REVIEW_UNAVAILABLE":
            errors.append("INDEPENDENT_REVIEW_UNAVAILABLE")
        errors.extend(["REVIEW: %s" % item for item in reviews.get("errors", [])])
    summary["reviews"] = reviews["status"]

    promotion_path = workspace / "release/promotion-selection.json"
    if not promotion_path.is_file():
        errors.append("promotion selection missing")
    else:
        promotion = load_json(promotion_path)
        candidate_id = promotion.get("selected_candidate_id")
        candidate = next((item for item in run["target"]["candidates"] if item["candidate_id"] == candidate_id), None)
        if not candidate:
            errors.append("promotion selects an unknown candidate")
        else:
            current_hash = sha256_tree(Path(candidate["path"]), exclude={"MANIFEST.sha256"})
            if current_hash != candidate["current_tree_hash"] or current_hash != promotion.get("selected_candidate_tree_hash"):
                errors.append("promotion candidate hash mismatch")
            candidate_root = Path(candidate["path"])
            profile = detect_profile(candidate_root, "auto")
            candidate_validation = validate_skill(candidate_root, strict=False, check_manifest=False, expected_genesis_hash=run["genesis"]["baseline_hash"] if profile == "optimizer" else "", profile=profile)
            if candidate_validation["status"] != "PASS":
                errors.extend(["CANDIDATE: %s" % item for item in candidate_validation["errors"]])
            if evaluation:
                if candidate_id not in evaluation.get("pareto_frontier", []):
                    errors.append("promotion candidate is not on the passing Pareto frontier")
                hashes = evaluation.get("aggregates", {}).get(candidate_id, {}).get("system_tree_hashes", [])
                if hashes != [current_hash]:
                    errors.append("promotion candidate differs from the exact tree evaluated across all splits")
            summary["selected_candidate"] = candidate_id
        if promotion.get("optimizer_actor_id") == promotion.get("verifier_actor_id"):
            errors.append("optimizer and final verifier are not separated")
        if promotion.get("verifier_record") != "verifier/final-verdict.json":
            errors.append("promotion does not bind final verifier record")

    return {
        "status": "PASS" if not errors else "BLOCKED", "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)), "summary": summary,
        "claim_boundary": "PASS means this frozen run satisfied available hard evidence; it is not a timeless world-best certificate",
    }


def gate_workspace(workspace: Path, as_of: str = "") -> Dict[str, Any]:
    """Run every promotion gate and fail closed on malformed or hostile evidence."""
    try:
        return _gate_workspace_inner(workspace, as_of)
    except Exception as exc:
        return {
            "status": "BLOCKED",
            "errors": ["promotion gate could not safely evaluate evidence: %s: %s" % (type(exc).__name__, exc)],
            "warnings": [],
            "summary": {},
            "claim_boundary": "Malformed or incomplete evidence is never a PASS; repair the run and evaluate again.",
        }
