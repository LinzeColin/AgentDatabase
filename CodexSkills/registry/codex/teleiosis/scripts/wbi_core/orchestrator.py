from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import load_json, sha256_file, sha256_tree, utc_now, write_json

RUN_MODES = {"diagnostic", "engineering", "formal"}
VERIFICATION_LEVELS = {"fast", "release", "deep"}
STEPS = [
    "PREFLIGHT", "CONTRACTS", "RESEARCH", "BENCHMARK", "ITERATION", "SYSTEM_REVIEWS",
    "INDEPENDENT_REVIEW", "PACKAGE", "INSTALL_ROLLBACK", "COMPLETE",
]


def _state_path(workspace: Path) -> Path:
    return workspace.resolve() / "control/orchestration-state.json"


def _status_from_state(state: Dict[str, Any]) -> Dict[str, Any]:
    current = str(state.get("current_step", "PREFLIGHT"))
    index = STEPS.index(current) if current in STEPS else 0
    return {
        "orchestration_status": state.get("orchestration_status", "BLOCKED"),
        "run_id": state.get("run_id"),
        "run_mode": state.get("run_mode"),
        "current_step": current,
        "completed_steps": STEPS[:index],
        "next_action": state.get("next_action"),
        "blocked_reasons": state.get("blocked_reasons", []),
        "identity": state.get("identity", {}),
        "preflight_artifacts": state.get("preflight_artifacts", {}),
        "adaptive_profile": state.get("adaptive_profile", {}),
        "updated_at": state.get("updated_at"),
    }


def init_orchestration(
    target: Path,
    workspace: Path,
    optimizer_root: Path,
    *,
    run_mode: str,
    package_profile: str,
    verification_level: str,
    valid_as_of: str,
    review_contract: Optional[Path] = None,
) -> Dict[str, Any]:
    target, workspace, optimizer_root = target.resolve(), workspace.resolve(), optimizer_root.resolve()
    if run_mode not in RUN_MODES:
        raise ValueError("run_mode must be diagnostic, engineering or formal")
    if verification_level not in VERIFICATION_LEVELS:
        raise ValueError("verification_level must be fast, release or deep")
    if not target.is_dir() or not optimizer_root.is_dir():
        raise ValueError("target and optimizer roots must exist")
    if (
        workspace == target or target in workspace.parents or workspace in target.parents
        or workspace == optimizer_root or optimizer_root in workspace.parents or workspace in optimizer_root.parents
    ):
        raise ValueError("orchestration workspace must be outside and non-overlapping with target and optimizer")
    path = _state_path(workspace)
    if path.exists():
        existing = load_json(path)
        expected = {
            "target_tree_hash": sha256_tree(target, exclude={"MANIFEST.sha256"}),
            "optimizer_tree_hash": sha256_tree(optimizer_root, exclude={"MANIFEST.sha256"}),
        }
        if existing.get("identity", {}).get("target_tree_hash") != expected["target_tree_hash"] or existing.get("identity", {}).get("optimizer_tree_hash") != expected["optimizer_tree_hash"]:
            raise ValueError("existing orchestration identity differs; use a new workspace")
        return _status_from_state(existing)
    workspace.mkdir(parents=True, exist_ok=True)
    review_binding = None
    blocked: List[str] = []
    if review_contract is not None:
        review_contract = review_contract.resolve()
        if not review_contract.is_file():
            blocked.append("review adapter contract path does not exist")
        else:
            review_binding = {"path": str(review_contract), "sha256": sha256_file(review_contract)}
    elif run_mode == "formal":
        blocked.append("formal run requires a frozen external review adapter contract before candidate mutation")
    state = {
        "schema_version": "1.0",
        "run_id": "wbi-orch-%s" % uuid.uuid4().hex[:16],
        "run_mode": run_mode,
        "package_profile": package_profile,
        "verification_level": verification_level,
        "valid_as_of": valid_as_of,
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "current_step": "PREFLIGHT",
        "orchestration_status": "BLOCKED" if blocked else "READY",
        "next_action": "Resolve formal review capability before mutation" if blocked else "Run preflight and freeze contracts",
        "blocked_reasons": blocked,
        "identity": {
            "target_path": str(target),
            "target_tree_hash": sha256_tree(target, exclude={"MANIFEST.sha256"}),
            "optimizer_path": str(optimizer_root),
            "optimizer_tree_hash": sha256_tree(optimizer_root, exclude={"MANIFEST.sha256"}),
        },
        "review_contract": review_binding,
        "step_receipts": {},
    }
    write_json(path, state)
    return _status_from_state(state)


def attach_preflight(workspace: Path, diagnostic_path: Path, plan_path: Path) -> Dict[str, Any]:
    """Bind bounded diagnosis and adaptive plan to one durable run identity.

    The artifacts do not advance PREFLIGHT. They make the next action specific and
    block mutation when diagnosis found a secret/symlink/invalid Skill boundary.
    """
    path = _state_path(workspace)
    if not path.is_file():
        raise ValueError("orchestration is not initialized")
    state = load_json(path)
    diagnostic_path, plan_path = diagnostic_path.resolve(), plan_path.resolve()
    for label, artifact in (("diagnostic", diagnostic_path), ("adaptive plan", plan_path)):
        if not artifact.is_file() or artifact.is_symlink():
            raise ValueError("%s artifact missing or linked" % label)
    diagnostic = load_json(diagnostic_path)
    plan = load_json(plan_path)
    state["preflight_artifacts"] = {
        "diagnostic": {"path": str(diagnostic_path), "sha256": sha256_file(diagnostic_path)},
        "adaptive_plan": {"path": str(plan_path), "sha256": sha256_file(plan_path)},
    }
    state["adaptive_profile"] = plan.get("profile", {})
    blockers = list(state.get("blocked_reasons", []))
    if diagnostic.get("diagnostic_status") == "BLOCKED":
        blockers.extend("diagnostic: %s" % item for item in diagnostic.get("blockers", []))
    if plan.get("plan_status") == "BLOCKED" and not diagnostic.get("blockers"):
        blockers.append("adaptive plan is blocked")
    state["blocked_reasons"] = sorted(set(blockers))
    if state["blocked_reasons"]:
        state["orchestration_status"] = "BLOCKED"
        state["next_action"] = "Resolve preflight blockers before freezing contracts or mutating a candidate"
    else:
        state["orchestration_status"] = "READY"
        state["next_action"] = plan.get("next_action", "Run preflight and freeze contracts")
    state["updated_at"] = utc_now()
    write_json(path, state)
    return _status_from_state(state)


def mark_step(workspace: Path, step: str, receipt_path: Path) -> Dict[str, Any]:
    path = _state_path(workspace)
    state = load_json(path)
    if state.get("orchestration_status") == "BLOCKED":
        return _status_from_state(state)
    if step not in STEPS[:-1]:
        raise ValueError("invalid orchestration step")
    current = str(state.get("current_step"))
    if current != step:
        raise ValueError("cannot mark %s while current step is %s" % (step, current))
    receipt_path = receipt_path.resolve()
    if not receipt_path.is_file() or receipt_path.is_symlink():
        raise ValueError("step receipt missing or linked")
    state["step_receipts"][step] = {"path": str(receipt_path), "sha256": sha256_file(receipt_path)}
    next_index = STEPS.index(step) + 1
    next_step = STEPS[next_index]
    state["current_step"] = next_step
    state["orchestration_status"] = "COMPLETE" if next_step == "COMPLETE" else "READY"
    state["next_action"] = "No further action" if next_step == "COMPLETE" else "Complete %s and record its immutable receipt" % next_step
    state["updated_at"] = utc_now()
    write_json(path, state)
    return _status_from_state(state)


def inspect_orchestration(workspace: Path) -> Dict[str, Any]:
    path = _state_path(workspace)
    if not path.is_file():
        return {"orchestration_status": "NOT_INITIALIZED", "next_action": "Run optimize/preflight", "blocked_reasons": []}
    state = load_json(path)
    errors: List[str] = []
    for step, binding in state.get("step_receipts", {}).items():
        receipt = Path(str(binding.get("path", "")))
        if not receipt.is_file() or receipt.is_symlink():
            errors.append("receipt missing for %s" % step)
        elif sha256_file(receipt) != binding.get("sha256"):
            errors.append("receipt hash drift for %s" % step)
    for label, binding in state.get("preflight_artifacts", {}).items():
        artifact = Path(str(binding.get("path", "")))
        if not artifact.is_file() or artifact.is_symlink():
            errors.append("preflight artifact missing for %s" % label)
        elif sha256_file(artifact) != binding.get("sha256"):
            errors.append("preflight artifact hash drift for %s" % label)
    if errors:
        state["orchestration_status"] = "BLOCKED"
        state["blocked_reasons"] = sorted(set(state.get("blocked_reasons", []) + errors))
        state["next_action"] = "Restore immutable receipts or start a new run; do not overwrite seals"
    return _status_from_state(state)


def explain_block(workspace: Path) -> Dict[str, Any]:
    status = inspect_orchestration(workspace)
    reasons = status.get("blocked_reasons", [])
    return {
        "orchestration_status": status.get("orchestration_status"),
        "blocked_reasons": reasons,
        "explanations": [
            {"reason": reason, "resolution": "Provide the missing external capability or restore the exact frozen evidence; never fabricate PASS."}
            for reason in reasons
        ],
        "next_action": status.get("next_action"),
    }
