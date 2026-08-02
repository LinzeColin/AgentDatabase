from __future__ import annotations

import json
import os
import platform
import shutil
import sys
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .common import (
    PACKAGE_ROOT,
    TeleiosisError,
    atomic_write_json,
    atomic_write_text,
    canonical_json_hash,
    copy_tree_secure,
    ensure_not_nested,
    ensure_plain_directory,
    iter_tree_files,
    is_relative_to,
    read_json,
    remove_tree,
    sha256_file,
    tree_digest,
)

MODULE_ORDER = ["T", "S", "P", "A"]
ROUNDS_PER_GROUP = 3
GROUPS_PER_RUN = 3
TOTAL_ROUNDS = ROUNDS_PER_GROUP * GROUPS_PER_RUN
TOTAL_STAGES = TOTAL_ROUNDS * len(MODULE_ORDER)
ALLOWED_CAPABILITY_STATUSES = {"EXECUTED", "NOT_APPLICABLE_WITH_REASON", "NOT_RUN", "BLOCKED"}
ALLOWED_DECISIONS = {"KEEP", "REVERT", "NO_CHANGE", "BLOCKED"}
ROOT_PUBLIC_FILES = {"candidate", ".teleiosis", "RUN_STATE.json", "RUN_STATUS.json", "SUMMARY.md", "NEXT_STAGE.json", "RESULT.json"}


def build_sequence() -> List[Dict[str, Any]]:
    sequence: List[Dict[str, Any]] = []
    stage_index = 0
    for group in range(1, GROUPS_PER_RUN + 1):
        for round_in_group in range(1, ROUNDS_PER_GROUP + 1):
            global_round = (group - 1) * ROUNDS_PER_GROUP + round_in_group
            for module in MODULE_ORDER:
                sequence.append({
                    "stage_index": stage_index,
                    "group": group,
                    "round_in_group": round_in_group,
                    "global_round": global_round,
                    "module": module,
                    "candidate_checkpoint": "C%04d" % (stage_index + 1),
                    "internal_passes": [
                        "baseline_and_discovery",
                        "adversarial_experiment_and_stress",
                        "adjudicate_stabilize_and_bind",
                    ],
                })
                stage_index += 1
    return sequence


def _module_manifest(module: str) -> Dict[str, Any]:
    path_map = {
        "T": "modules/raw_teleiosis/CAPABILITIES.json",
        "S": "modules/skill_market_lab/CAPABILITIES.json",
        "P": "modules/product_reality_lab/CAPABILITIES.json",
        "A": "modules/arena_lab/CAPABILITIES.json",
    }
    return read_json(PACKAGE_ROOT / path_map[module])


def _environment_snapshot() -> Dict[str, Any]:
    return {
        "schema_version": "teleiosis.environment_snapshot.v1",
        "python": platform.python_version(),
        "implementation": platform.python_implementation(),
        "platform": platform.platform(),
        "machine": platform.machine(),
        "network": "runtime-dependent-not-assumed",
        "credentials": "not-recorded",
        "valid_as_of": "runtime",
    }


def _new_run_id(explicit: Optional[str] = None) -> str:
    if explicit:
        if not explicit.replace("-", "").replace("_", "").isalnum() or len(explicit) > 96:
            raise TeleiosisError("RUN_ID_INVALID", "run_id 仅允许字母、数字、连字符和下划线，长度不超过 96。")
        return explicit
    return "RUN-" + uuid.uuid4().hex[:20]


def _workspace_paths(workspace: Path) -> Dict[str, Path]:
    return {
        "candidate": workspace / "candidate",
        "private": workspace / ".teleiosis",
        "state": workspace / "RUN_STATE.json",
        "status": workspace / "RUN_STATUS.json",
        "summary": workspace / "SUMMARY.md",
        "next": workspace / "NEXT_STAGE.json",
        "result": workspace / "RESULT.json",
    }


def _assert_workspace_shape(workspace: Path) -> None:
    names = {item.name for item in workspace.iterdir()}
    extra = sorted(names - ROOT_PUBLIC_FILES)
    if extra:
        raise TeleiosisError("WORKSPACE_POLLUTION", "Workspace 根目录包含未授权文件。", {"extra": extra})
    for item in workspace.iterdir():
        if item.is_symlink():
            raise TeleiosisError("SYMLINK_REFUSED", "Workspace 根目录含符号链接。", {"path": str(item)})


def _candidate_identity(state: Dict[str, Any]) -> Dict[str, Any]:
    current = state["current_candidate"]
    return {
        "subject_id": state["subject_id"],
        "run_id": state["run_id"],
        "candidate_id": state["candidate_id"],
        "revision_id": current["revision_id"],
        "parent_revision_id": current.get("parent_revision_id"),
        "baseline_hash": state["baseline_hash"],
        "candidate_hash": current["tree_hash"],
        "acceptance_hash": state["acceptance_hash"],
        "environment_hash": state["environment_hash"],
    }


def _result_template(state: Dict[str, Any]) -> Dict[str, Any]:
    index = state["next_stage_index"]
    if index >= TOTAL_STAGES:
        return {
            "schema_version": "teleiosis.capability_result.v5",
            "run_id": state["run_id"],
            "stage_index": TOTAL_STAGES,
            "module": "COMPLETE",
            "candidate_revision_id": state["current_candidate"]["revision_id"],
            "decision": "NO_CHANGE",
            "summary": "完整 Run 已结束；此文件只读。",
            "capabilities": [],
            "evidence_files": [],
        }
    stage = state["sequence"][index]
    manifest = _module_manifest(stage["module"])
    return {
        "schema_version": "teleiosis.capability_result.v5",
        "run_id": state["run_id"],
        "stage_index": index,
        "module": stage["module"],
        "candidate_revision_id": state["current_candidate"]["revision_id"],
        "decision": "NO_CHANGE",
        "summary": "",
        "developer_burden_delta": {
            "closed_unknowns": [],
            "closed_p0_p1": [],
            "generated_executable_artifacts": [],
            "builder_tasks_removed": [],
        },
        "capabilities": [
            {"id": cap["id"], "status": "", "reason": "", "evidence_refs": []}
            for cap in manifest["capabilities"]
        ],
        "evidence_files": [],
        "arena_result": None,
    }


def _public_status(state: Dict[str, Any]) -> Dict[str, Any]:
    next_index = state["next_stage_index"]
    next_stage = state["sequence"][next_index] if next_index < TOTAL_STAGES else None
    return {
        "schema_version": "teleiosis.run_status.v5",
        "run_id": state["run_id"],
        "status": state["status"],
        "completed_stages": next_index,
        "total_stages": TOTAL_STAGES,
        "completed_rounds": next_index // 4,
        "total_rounds": TOTAL_ROUNDS,
        "next_stage": next_stage,
        "candidate_identity": _candidate_identity(state),
        "external_verifier_required": True,
        "formal_pass": "NOT_ISSUED_INTERNALLY",
    }


def _summary_text(state: Dict[str, Any]) -> str:
    status = _public_status(state)
    next_stage = status["next_stage"]
    next_text = "完整 Run 已结束，等待外部 Verifier。" if next_stage is None else (
        "下一阶段：第 {stage_index} 阶段，Group {group} / Round {global_round} / Module {module}。".format(**next_stage)
    )
    return """# Teleiosis Run 摘要

- Run ID：`{run_id}`
- 状态：`{status}`
- 已完成：`{completed_stages}/{total_stages}` 个阶段
- 当前 Candidate：`{revision}`
- 当前 tree digest：`{digest}`
- {next_text}
- 正式 PASS：仅由外部独立 Verifier 产生
""".format(
        run_id=state["run_id"], status=state["status"], completed_stages=status["completed_stages"],
        total_stages=TOTAL_STAGES, revision=state["current_candidate"]["revision_id"],
        digest=state["current_candidate"]["tree_hash"], next_text=next_text,
    )


def _refresh_public(workspace: Path, state: Dict[str, Any], result: Optional[Dict[str, Any]] = None) -> None:
    paths = _workspace_paths(workspace)
    atomic_write_json(paths["state"], state)
    atomic_write_json(paths["status"], _public_status(state))
    atomic_write_text(paths["summary"], _summary_text(state))
    atomic_write_json(paths["next"], _result_template(state))
    if result is None:
        result = {"schema_version": "teleiosis.last_result.v5", "status": "INITIALIZED", "run_id": state["run_id"]}
    atomic_write_json(paths["result"], result)
    _assert_workspace_shape(workspace)


def init_run(subject: Path, workspace: Path, run_id: Optional[str] = None) -> Dict[str, Any]:
    subject = ensure_plain_directory(subject)
    workspace_raw = workspace.expanduser().absolute()
    ensure_not_nested(subject, workspace_raw)
    if workspace_raw.exists() and any(workspace_raw.iterdir()):
        raise TeleiosisError("WORKSPACE_NOT_EMPTY", "Workspace 必须不存在或为空。", {"path": str(workspace_raw)})
    if workspace_raw.exists() and workspace_raw.is_symlink():
        raise TeleiosisError("SYMLINK_REFUSED", "Workspace 不能是符号链接。")
    # Validate the subject before creating any workspace side effect.
    baseline_hash = tree_digest(subject)
    run = _new_run_id(run_id)
    acceptance_hash = sha256_file(PACKAGE_ROOT / "ACCEPTANCE_CONTRACT.json")
    environment = _environment_snapshot()
    environment_hash = canonical_json_hash(environment)
    subject_id = "SUBJECT-" + canonical_json_hash({"path": str(subject), "baseline_hash": baseline_hash})[:20]
    candidate_id = "CANDIDATE-" + run.replace("RUN-", "")
    paths = _workspace_paths(workspace_raw)
    workspace_raw.mkdir(parents=True, exist_ok=True)
    try:
        copy_tree_secure(subject, paths["candidate"])
        private = paths["private"]
        (private / "snapshots").mkdir(parents=True)
        (private / "revisions").mkdir(parents=True)
        (private / "evidence").mkdir(parents=True)
        (private / "rejected").mkdir(parents=True)
        copy_tree_secure(paths["candidate"], private / "snapshots/C0000")
        atomic_write_json(private / "environment.json", environment)
        initial_revision = {
            "revision_id": "C0000", "parent_revision_id": None, "tree_hash": baseline_hash,
            "decision": "BASELINE", "snapshot_ref": ".teleiosis/snapshots/C0000", "changed_files": [],
        }
        atomic_write_json(private / "revisions/C0000.json", initial_revision)
        state = {
            "schema_version": "teleiosis.run_state.v5",
            "run_id": run,
            "subject": str(subject),
            "subject_id": subject_id,
            "candidate_id": candidate_id,
            "workspace": str(workspace_raw),
            "status": "RUNNING",
            "scope_mode": "FULL_NO_ROUTING",
            "baseline_hash": baseline_hash,
            "acceptance_hash": acceptance_hash,
            "environment_hash": environment_hash,
            "sequence": build_sequence(),
            "next_stage_index": 0,
            "current_candidate": initial_revision,
            "events": [],
            "hash_chain_head": "0" * 64,
            "external_verifier_required": True,
        }
        event = {
            "event_index": 0,
            "event_type": "RUN_INITIALIZED",
            "run_id": run,
            "candidate_revision_id": "C0000",
            "candidate_hash": baseline_hash,
            "previous_event_hash": state["hash_chain_head"],
        }
        event["event_hash"] = canonical_json_hash(event)
        state["events"].append(event)
        state["hash_chain_head"] = event["event_hash"]
        _refresh_public(workspace_raw, state)
        return {"status": "INITIALIZED", "run_id": run, "workspace": str(workspace_raw), "candidate_identity": _candidate_identity(state), "next_stage": state["sequence"][0]}
    except Exception:
        if workspace_raw.exists():
            shutil.rmtree(str(workspace_raw), ignore_errors=True)
        raise


def _load_state(workspace: Path) -> Tuple[Path, Dict[str, Any]]:
    workspace = ensure_plain_directory(workspace)
    _assert_workspace_shape(workspace)
    state = read_json(workspace / "RUN_STATE.json")
    if state.get("schema_version") != "teleiosis.run_state.v5":
        raise TeleiosisError("RUN_STATE_VERSION", "Run state 版本不受支持。")
    if Path(state.get("workspace", "")).resolve() != workspace:
        raise TeleiosisError("WORKSPACE_IDENTITY", "Run state 与当前 Workspace 不匹配。")
    if state.get("sequence") != build_sequence():
        raise TeleiosisError("SEQUENCE_TAMPERED", "固定 T/S/P/A 序列被修改。")
    candidate = workspace / "candidate"
    ensure_plain_directory(candidate)
    return workspace, state


def _validate_result(state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
    allowed_keys = {"schema_version", "run_id", "stage_index", "module", "candidate_revision_id", "decision", "summary", "developer_burden_delta", "capabilities", "evidence_files", "arena_result"}
    unknown = sorted(set(result) - allowed_keys)
    if unknown:
        raise TeleiosisError("RESULT_UNKNOWN_FIELDS", "阶段结果包含未知字段。", {"unknown": unknown})
    if result.get("schema_version") != "teleiosis.capability_result.v5":
        raise TeleiosisError("RESULT_SCHEMA", "阶段结果 Schema 版本错误。")
    index = state["next_stage_index"]
    if index >= TOTAL_STAGES:
        raise TeleiosisError("RUN_ALREADY_COMPLETE", "完整 Run 已结束。")
    stage = state["sequence"][index]
    expected = {
        "run_id": state["run_id"], "stage_index": index, "module": stage["module"],
        "candidate_revision_id": state["current_candidate"]["revision_id"],
    }
    for key, value in expected.items():
        if result.get(key) != value:
            raise TeleiosisError("RESULT_IDENTITY", "阶段结果身份或顺序不匹配。", {"field": key, "expected": value, "actual": result.get(key)})
    if result.get("decision") not in ALLOWED_DECISIONS:
        raise TeleiosisError("DECISION_INVALID", "阶段决定不合法。", {"decision": result.get("decision")})
    if not isinstance(result.get("summary"), str) or not result.get("summary", "").strip():
        raise TeleiosisError("SUMMARY_REQUIRED", "阶段结果必须提供实质摘要。")
    manifest = _module_manifest(stage["module"])
    expected_caps = [cap["id"] for cap in manifest["capabilities"]]
    submitted = result.get("capabilities")
    if not isinstance(submitted, list):
        raise TeleiosisError("CAPABILITY_RESULTS_REQUIRED", "缺少能力结果。")
    submitted_ids = [item.get("id") for item in submitted if isinstance(item, dict)]
    if submitted_ids != expected_caps:
        raise TeleiosisError("CAPABILITY_RESULTS_INCOMPLETE", "能力结果必须完整、按固定顺序且不得缩减。", {"expected": expected_caps, "actual": submitted_ids})
    blocked = False
    evidence_union: Set[str] = set()
    for item in submitted:
        if set(item) - {"id", "status", "reason", "evidence_refs"}:
            raise TeleiosisError("CAPABILITY_RESULT_UNKNOWN_FIELDS", "单项能力结果包含未知字段。", {"id": item.get("id")})
        status = item.get("status")
        reason = item.get("reason")
        refs = item.get("evidence_refs")
        if status not in ALLOWED_CAPABILITY_STATUSES:
            raise TeleiosisError("CAPABILITY_STATUS_INVALID", "能力状态不合法或尚未填写。", {"id": item.get("id"), "status": status})
        if not isinstance(reason, str):
            raise TeleiosisError("CAPABILITY_REASON_INVALID", "能力 reason 必须是字符串。", {"id": item.get("id")})
        if not isinstance(refs, list) or any(not isinstance(ref, str) for ref in refs):
            raise TeleiosisError("CAPABILITY_EVIDENCE_INVALID", "evidence_refs 必须是字符串数组。", {"id": item.get("id")})
        if status == "EXECUTED" and not refs:
            raise TeleiosisError("EXECUTED_WITHOUT_EVIDENCE", "EXECUTED 必须至少引用一个证据文件。", {"id": item.get("id")})
        if status == "NOT_APPLICABLE_WITH_REASON" and len(reason.strip()) < 8:
            raise TeleiosisError("NA_REASON_TOO_WEAK", "N/A 必须给出具体适用性判断。", {"id": item.get("id")})
        if status in {"NOT_RUN", "BLOCKED"}:
            blocked = True
            if len(reason.strip()) < 8:
                raise TeleiosisError("BLOCK_REASON_REQUIRED", "NOT_RUN/BLOCKED 必须说明阻塞原因。", {"id": item.get("id")})
        evidence_union.update(refs)
    top_files = result.get("evidence_files")
    if not isinstance(top_files, list) or any(not isinstance(ref, str) for ref in top_files):
        raise TeleiosisError("EVIDENCE_FILES_INVALID", "evidence_files 必须是字符串数组。")
    if not evidence_union.issubset(set(top_files)):
        raise TeleiosisError("EVIDENCE_REFERENCE_NOT_DECLARED", "能力引用的证据必须出现在 evidence_files。", {"missing": sorted(evidence_union - set(top_files))})
    if blocked and result.get("decision") != "BLOCKED":
        raise TeleiosisError("BLOCKED_CAPABILITY_DECISION", "存在 NOT_RUN/BLOCKED 时决定必须为 BLOCKED。")
    if not blocked and result.get("decision") == "BLOCKED":
        blocked = True
    result = dict(result)
    result["_blocked"] = blocked
    return result


def _capture_evidence(workspace: Path, state: Dict[str, Any], result: Dict[str, Any]) -> List[Dict[str, Any]]:
    stage_index = state["next_stage_index"]
    dest_root = workspace / ".teleiosis/evidence" / ("stage-%02d" % stage_index)
    sources: List[Path] = []
    for ref in result.get("evidence_files", []):
        path = Path(ref).expanduser()
        if not path.is_absolute():
            path = workspace / path
        if not path.exists() or path.is_symlink() or not path.is_file():
            raise TeleiosisError("EVIDENCE_FILE_INVALID", "证据必须是存在的普通文件。", {"path": str(path)})
        if path.stat().st_size > 64 * 1024 * 1024:
            raise TeleiosisError("EVIDENCE_TOO_LARGE", "单个证据文件超过 64 MiB。", {"path": str(path)})
        sources.append(path.resolve())
    staging = workspace / ".teleiosis/evidence" / (".stage-%02d-staging-%s" % (stage_index, uuid.uuid4().hex))
    staging.mkdir(parents=True)
    captured: List[Dict[str, Any]] = []
    try:
        for idx, path in enumerate(sources):
            target = staging / ("%03d-%s" % (idx, path.name))
            shutil.copy2(str(path), str(target), follow_symlinks=False)
            captured.append({
                "source": str(path),
                "stored_path": str((dest_root / target.name).relative_to(workspace)),
                "sha256": sha256_file(target),
                "size": target.stat().st_size,
            })
        if dest_root.exists():
            remove_tree(dest_root)
        os.replace(str(staging), str(dest_root))
    except Exception:
        if staging.exists():
            shutil.rmtree(str(staging), ignore_errors=True)
        raise
    return captured


def _changed_files(before_snapshot: Path, candidate: Path) -> List[Dict[str, Any]]:
    before = {entry["path"]: entry for entry in _manifest_allow_empty(before_snapshot)}
    after = {entry["path"]: entry for entry in _manifest_allow_empty(candidate)}
    changes = []
    for path in sorted(set(before) | set(after)):
        b = before.get(path)
        a = after.get(path)
        if b == a:
            continue
        if b is None:
            state = "added"
        elif a is None:
            state = "deleted"
        else:
            state = "modified"
        changes.append({"path": path, "state": state, "before_sha256": b and b["sha256"], "after_sha256": a and a["sha256"]})
    return changes


def _manifest_allow_empty(root: Path) -> List[Dict[str, Any]]:
    entries = []
    for rel, path in iter_tree_files(root, include_manifest=True):
        entries.append({"path": rel.as_posix(), "sha256": sha256_file(path), "size": path.stat().st_size})
    return entries


def _restore_snapshot(snapshot: Path, candidate: Path) -> None:
    if candidate.exists():
        remove_tree(candidate)
    copy_tree_secure(snapshot, candidate)


def submit_stage(workspace: Path, result_path: Path) -> Dict[str, Any]:
    workspace, state = _load_state(workspace)
    result_path = result_path.expanduser()
    if not result_path.is_absolute():
        result_path = workspace / result_path
    result = read_json(result_path)
    validated = _validate_result(state, result)
    index = state["next_stage_index"]
    stage = state["sequence"][index]
    candidate = workspace / "candidate"
    before_revision = state["current_candidate"]
    before_snapshot = workspace / before_revision["snapshot_ref"]
    before_hash = before_revision["tree_hash"]
    current_hash = tree_digest(candidate)
    delta = current_hash != before_hash
    decision = validated["decision"]
    if decision == "NO_CHANGE" and delta:
        raise TeleiosisError("NO_CHANGE_DELTA_CONFLICT", "Candidate 已变化，不能提交 NO_CHANGE。", {"before": before_hash, "after": current_hash})
    if decision == "KEEP" and not delta:
        decision = "NO_CHANGE"
    captured = _capture_evidence(workspace, state, validated)
    changed = _changed_files(before_snapshot, candidate) if delta else []
    next_revision_id = "C%04d" % (index + 1)
    rejected_ref = None
    if decision == "REVERT":
        if delta:
            rejected = workspace / ".teleiosis/rejected" / next_revision_id
            if rejected.exists():
                remove_tree(rejected)
            copy_tree_secure(candidate, rejected)
            rejected_ref = str(rejected.relative_to(workspace))
        _restore_snapshot(before_snapshot, candidate)
        current_hash = tree_digest(candidate)
        delta = False
    if validated["_blocked"] or decision == "BLOCKED":
        state["status"] = "BLOCKED"
        event = {
            "event_index": len(state["events"]), "event_type": "STAGE_BLOCKED", "stage_index": index,
            "module": stage["module"], "candidate_revision_id": before_revision["revision_id"],
            "candidate_hash": current_hash, "evidence": captured, "previous_event_hash": state["hash_chain_head"],
        }
        event["event_hash"] = canonical_json_hash(event)
        state["events"].append(event)
        state["hash_chain_head"] = event["event_hash"]
        output = {"schema_version": "teleiosis.last_result.v5", "status": "BLOCKED", "stage": stage, "reason": validated["summary"], "candidate_hash": current_hash}
        _refresh_public(workspace, state, output)
        return output
    # Stage is accepted and advances.
    if decision == "KEEP" and delta:
        snapshot = workspace / ".teleiosis/snapshots" / next_revision_id
        copy_tree_secure(candidate, snapshot)
        snapshot_ref = str(snapshot.relative_to(workspace))
    else:
        snapshot_ref = before_revision["snapshot_ref"]
    revision = {
        "revision_id": next_revision_id,
        "parent_revision_id": before_revision["revision_id"],
        "tree_hash": current_hash,
        "decision": decision,
        "snapshot_ref": snapshot_ref,
        "changed_files": changed,
        "rejected_ref": rejected_ref,
        "stage_index": index,
        "module": stage["module"],
        "summary": validated["summary"],
        "developer_burden_delta": validated.get("developer_burden_delta", {}),
        "evidence": captured,
        "arena_result": validated.get("arena_result"),
    }
    atomic_write_json(workspace / ".teleiosis/revisions" / (next_revision_id + ".json"), revision)
    event = {
        "event_index": len(state["events"]), "event_type": "STAGE_COMMITTED", "stage_index": index,
        "module": stage["module"], "decision": decision, "parent_revision_id": before_revision["revision_id"],
        "candidate_revision_id": next_revision_id, "candidate_hash": current_hash,
        "changed_files": changed, "evidence": captured, "previous_event_hash": state["hash_chain_head"],
    }
    event["event_hash"] = canonical_json_hash(event)
    state["events"].append(event)
    state["hash_chain_head"] = event["event_hash"]
    state["current_candidate"] = revision
    state["next_stage_index"] = index + 1
    state["status"] = "READY_FOR_EXTERNAL_VERIFIER" if state["next_stage_index"] == TOTAL_STAGES else "RUNNING"
    output = {
        "schema_version": "teleiosis.last_result.v5", "status": "STAGE_COMMITTED", "stage": stage,
        "decision": decision, "candidate_identity": _candidate_identity(state), "completed_stages": state["next_stage_index"],
        "run_status": state["status"],
    }
    _refresh_public(workspace, state, output)
    return output


def status_run(workspace: Path) -> Dict[str, Any]:
    workspace, state = _load_state(workspace)
    return _public_status(state)


def validate_run(workspace: Path, require_complete: bool = False) -> Dict[str, Any]:
    workspace, state = _load_state(workspace)
    errors: List[str] = []
    if len(state["sequence"]) != TOTAL_STAGES:
        errors.append("sequence_length")
    if state["next_stage_index"] != len([event for event in state["events"] if event.get("event_type") == "STAGE_COMMITTED"]):
        errors.append("committed_event_count")
    if tree_digest(workspace / "candidate") != state["current_candidate"]["tree_hash"]:
        errors.append("candidate_hash")
    previous = "0" * 64
    for event in state["events"]:
        if event.get("previous_event_hash") != previous:
            errors.append("hash_chain_previous")
            break
        event_copy = dict(event)
        stored_hash = event_copy.pop("event_hash", None)
        if canonical_json_hash(event_copy) != stored_hash:
            errors.append("hash_chain_event")
            break
        previous = stored_hash
    if state.get("hash_chain_head") != previous:
        errors.append("hash_chain_head")
    if require_complete and (state["next_stage_index"] != TOTAL_STAGES or state["status"] != "READY_FOR_EXTERNAL_VERIFIER"):
        errors.append("run_not_complete")
    if errors:
        raise TeleiosisError("RUN_VALIDATION_FAILED", "Run 验证失败。", {"errors": errors})
    return {"status": "PASS", "run_id": state["run_id"], "completed_stages": state["next_stage_index"], "complete": state["next_stage_index"] == TOTAL_STAGES, "candidate_identity": _candidate_identity(state)}


def create_handoff(workspace: Path, output: Path) -> Dict[str, Any]:
    workspace, state = _load_state(workspace)
    validate_run(workspace, require_complete=True)
    evidence_manifest = []
    evidence_root = workspace / ".teleiosis/evidence"
    if evidence_root.exists():
        for rel, path in iter_tree_files(evidence_root, include_manifest=True):
            evidence_manifest.append({"path": str(Path(".teleiosis/evidence") / rel), "sha256": sha256_file(path), "size": path.stat().st_size})
    arena_results = [rev.get("arena_result") for rev in _load_revisions(workspace) if rev.get("module") == "A" and rev.get("arena_result")]
    packet = {
        "schema_version": "teleiosis.external_verifier_handoff.v1",
        "candidate_identity": _candidate_identity(state),
        "acceptance_contract": str((PACKAGE_ROOT / "ACCEPTANCE_CONTRACT.json").resolve()),
        "evidence_manifest": evidence_manifest,
        "arena_result": arena_results[-1] if arena_results else None,
        "formal_decision_requested": "FORMAL_PASS_OR_FAIL",
        "builder_self_assessment_accepted": False,
        "run_hash_chain_head": state["hash_chain_head"],
        "rollback_snapshot": state["current_candidate"]["snapshot_ref"],
        "truth_boundary": "T/S/P/A 只产内部证据；本文件不构成 formal PASS。",
    }
    output = output.expanduser()
    if not output.is_absolute():
        output = workspace / output
    if is_relative_to(output.resolve(), PACKAGE_ROOT.resolve()):
        raise TeleiosisError("OUTPUT_INSIDE_PACKAGE", "运行结果不得写入安装包。")
    atomic_write_json(output, packet)
    return {"status": "HANDOFF_READY", "output": str(output), "candidate_identity": packet["candidate_identity"]}


def _load_revisions(workspace: Path) -> List[Dict[str, Any]]:
    revisions = []
    for path in sorted((workspace / ".teleiosis/revisions").glob("C*.json")):
        revisions.append(read_json(path))
    return revisions


def contract() -> Dict[str, Any]:
    return {
        "schema_version": "teleiosis.full_run_contract.v5",
        "scope_mode": "FULL_NO_ROUTING",
        "round_sequence": ["T", "C", "S", "C", "P", "C", "A", "C"],
        "modules": MODULE_ORDER,
        "rounds_per_group": ROUNDS_PER_GROUP,
        "groups_per_run": GROUPS_PER_RUN,
        "total_rounds": TOTAL_ROUNDS,
        "total_stages": TOTAL_STAGES,
        "sequence": build_sequence(),
        "formal_pass_authority": "external independent verifier",
    }
