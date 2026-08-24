from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Sequence, Tuple

SCHEMA_VERSION = "2.0"
SEQUENCE: Tuple[Tuple[str, str], ...] = (
    ("T1", "raw_teleiosis"),
    ("M1", "market_evidence"),
    ("T2", "raw_teleiosis"),
    ("M2", "market_evidence"),
    ("T3", "raw_teleiosis"),
)
ROUND_MODES = {1: "diagnose", 2: "adversarial_challenge", 3: "adjudicate_and_stabilize"}
ALLOWED_OUTCOMES = {
    "KEEP",
    "REVERT",
    "NO_CHANGE",
    "EVIDENCE_READY_FOR_TELEIOSIS",
    "REHEAT_REQUIRED",
    "BLOCKED",
}
IGNORED_NAMES = {"__pycache__", ".DS_Store", ".git", ".pytest_cache", ".mypy_cache"}


class CycleError(RuntimeError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def tree_manifest(root: Path) -> List[Dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise CycleError(f"制品目录不存在: {root}")
    rows: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        if any(part in IGNORED_NAMES for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise CycleError(f"拒绝符号链接: {path}")
        if not path.is_file():
            continue
        rows.append(
            {
                "path": path.relative_to(root).as_posix(),
                "sha256": file_sha256(path),
                "size": path.stat().st_size,
            }
        )
    return rows


def tree_sha256(root: Path) -> str:
    return object_sha256(tree_manifest(root))


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def read_json(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CycleError(f"缺少文件: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CycleError(f"JSON 无效: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise CycleError(f"JSON 根节点必须为 object: {path}")
    return value


@contextmanager
def workspace_lock(workspace: Path) -> Iterator[None]:
    lock = workspace / ".cycle.lock"
    workspace.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as exc:
        raise CycleError(f"工作区已有活动锁: {lock}") from exc
    try:
        os.write(fd, f"pid={os.getpid()}\n".encode("utf-8"))
        os.close(fd)
        yield
    finally:
        try:
            lock.unlink()
        except FileNotFoundError:
            pass


def _event_payload(event: Mapping[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in event.items() if key != "event_hash"}


def load_events(workspace: Path) -> List[Dict[str, Any]]:
    path = workspace / "events.jsonl"
    if not path.exists():
        return []
    rows: List[Dict[str, Any]] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise CycleError(f"事件账本第 {line_no} 行无效: {exc}") from exc
        if not isinstance(row, dict):
            raise CycleError(f"事件账本第 {line_no} 行不是 object")
        rows.append(row)
    return rows


def append_event(workspace: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    events = load_events(workspace)
    event = dict(event)
    event["event_index"] = len(events)
    event["recorded_at"] = utc_now()
    event["previous_event_hash"] = events[-1]["event_hash"] if events else None
    event["event_hash"] = object_sha256(_event_payload(event))
    path = workspace / "events.jsonl"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(canonical_json(event) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    return event


def expected_position(state: Mapping[str, Any]) -> Tuple[str | None, int | None, str | None]:
    if state.get("complete"):
        return None, None, None
    stage_index = int(state["stage_index"])
    if stage_index >= len(SEQUENCE):
        return None, None, None
    stage, profile = SEQUENCE[stage_index]
    return stage, int(state["next_round"]), profile


def initialize_workspace(workspace: Path, subject_name: str, subject_version: str, subject_digest: str, force: bool = False) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if workspace.exists() and any(workspace.iterdir()) and not force:
        raise CycleError(f"工作区非空，拒绝覆盖: {workspace}")
    workspace.mkdir(parents=True, exist_ok=True)
    for child in list(workspace.iterdir()):
        if force and child.is_file():
            child.unlink()
        elif force and child.is_dir():
            import shutil
            shutil.rmtree(child)
    contract = {
        "schema_version": SCHEMA_VERSION,
        "version": "v0.0.0.2",
        "subject": {
            "name": subject_name,
            "version": subject_version,
            "initial_digest": subject_digest,
        },
        "sequence": [
            {
                "stage": stage,
                "profile": profile,
                "required_consecutive_subruns": 3,
                "round_modes": [ROUND_MODES[i] for i in (1, 2, 3)],
                "mutation_after_subrun": 3,
            }
            for stage, profile in SEQUENCE
        ],
        "authority": {
            "final_promotion_authority": "teleiosis",
            "market_kernel_authority": "evidence_only",
            "raw_profile_can_call_market_kernel": False,
            "market_kernel_can_mutate_official_candidate": False,
        },
        "mutation_contract": {
            "round_3_must_bind_staged_candidate_digest": True,
            "commit_is_atomic_and_content_preserving": True,
            "post_approval_content_change_forbidden": True,
        },
    }
    state = {
        "schema_version": SCHEMA_VERSION,
        "stage_index": 0,
        "next_round": 1,
        "awaiting_mutation": False,
        "pending_stage": None,
        "approved_candidate_digest": None,
        "current_subject_digest": subject_digest,
        "completed_stages": [],
        "complete": False,
        "last_event_hash": None,
    }
    atomic_write_json(workspace / "cycle_contract.json", contract)
    atomic_write_json(workspace / "state.json", state)
    (workspace / "events.jsonl").write_text("", encoding="utf-8")
    return {"contract": contract, "state": state, "workspace": str(workspace)}


def load_state(workspace: Path) -> Dict[str, Any]:
    return read_json(workspace / "state.json")


def _save_state(workspace: Path, state: Dict[str, Any], event: Mapping[str, Any]) -> None:
    state = dict(state)
    state["last_event_hash"] = event["event_hash"]
    atomic_write_json(workspace / "state.json", state)


def record_subrun(
    workspace: Path,
    stage: str,
    round_number: int,
    subject_digest: str,
    evidence_digest: str,
    outcome: str,
    staged_candidate_digest: str | None = None,
    notes: str = "",
) -> Dict[str, Any]:
    if outcome not in ALLOWED_OUTCOMES:
        raise CycleError(f"不支持的 outcome: {outcome}")
    state = load_state(workspace)
    if state.get("awaiting_mutation"):
        raise CycleError("上一调用已完成三轮，必须先提交其已批准 Candidate")
    expected_stage, expected_round, profile = expected_position(state)
    if (stage, round_number) != (expected_stage, expected_round):
        raise CycleError(
            f"调用顺序错误：期望 {expected_stage}/R{expected_round}，收到 {stage}/R{round_number}"
        )
    if subject_digest != state["current_subject_digest"]:
        raise CycleError("本次 subject_digest 与当前正式 Candidate 不一致")
    if not re_full_sha(evidence_digest):
        raise CycleError("evidence_digest 必须是 64 位 SHA-256")
    if round_number < 3 and staged_candidate_digest is not None:
        raise CycleError("只有第三轮可以批准 staged Candidate")
    if round_number == 3:
        if not staged_candidate_digest or not re_full_sha(staged_candidate_digest):
            raise CycleError("第三轮必须绑定已评测 staged_candidate_digest")
    event = append_event(
        workspace,
        {
            "type": "subrun",
            "stage": stage,
            "profile": profile,
            "round": round_number,
            "mode": ROUND_MODES[round_number],
            "subject_digest": subject_digest,
            "evidence_digest": evidence_digest,
            "staged_candidate_digest": staged_candidate_digest,
            "outcome": outcome,
            "notes": notes,
        },
    )
    state["next_round"] = round_number + 1
    if round_number == 3:
        state["awaiting_mutation"] = True
        state["pending_stage"] = stage
        state["approved_candidate_digest"] = staged_candidate_digest
        state["next_round"] = None
    _save_state(workspace, state, event)
    return {"event": event, "state": state}


def re_full_sha(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdef" for char in value.lower())


def commit_mutation(workspace: Path, stage: str, artifact_path: Path) -> Dict[str, Any]:
    state = load_state(workspace)
    if not state.get("awaiting_mutation"):
        raise CycleError("当前没有待提交的已批准 Candidate")
    if stage != state.get("pending_stage"):
        raise CycleError(f"待提交阶段为 {state.get('pending_stage')}，不是 {stage}")
    actual_digest = tree_sha256(artifact_path)
    approved = state.get("approved_candidate_digest")
    if actual_digest != approved:
        raise CycleError(
            "提交制品与第三轮批准哈希不一致；提交节点不得产生新内容 "
            f"(approved={approved}, actual={actual_digest})"
        )
    event = append_event(
        workspace,
        {
            "type": "mutation_commit",
            "stage": stage,
            "approved_candidate_digest": approved,
            "actual_candidate_digest": actual_digest,
            "artifact_manifest_digest": object_sha256(tree_manifest(artifact_path)),
            "atomic_content_preserving": True,
        },
    )
    stage_index = int(state["stage_index"])
    expected_stage, _profile = SEQUENCE[stage_index]
    if expected_stage != stage:
        raise CycleError("内部状态与序列不一致")
    state["current_subject_digest"] = actual_digest
    state["completed_stages"] = list(state.get("completed_stages", [])) + [stage]
    state["stage_index"] = stage_index + 1
    state["awaiting_mutation"] = False
    state["pending_stage"] = None
    state["approved_candidate_digest"] = None
    if state["stage_index"] >= len(SEQUENCE):
        state["complete"] = True
        state["next_round"] = None
    else:
        state["next_round"] = 1
    _save_state(workspace, state, event)
    return {"event": event, "state": state, "committed_digest": actual_digest}


def validate_workspace(workspace: Path, require_complete: bool = False) -> Dict[str, Any]:
    contract = read_json(workspace / "cycle_contract.json")
    state = load_state(workspace)
    events = load_events(workspace)
    errors: List[str] = []
    previous: str | None = None
    expected_stage_index = 0
    expected_round = 1
    awaiting_mutation = False
    approved_digest: str | None = None
    current_digest = contract.get("subject", {}).get("initial_digest")
    seen_subruns = 0
    seen_mutations = 0

    for index, event in enumerate(events):
        if event.get("event_index") != index:
            errors.append(f"event_index 不连续: {index}")
        if event.get("previous_event_hash") != previous:
            errors.append(f"previous_event_hash 断链: {index}")
        calculated = object_sha256(_event_payload(event))
        if event.get("event_hash") != calculated:
            errors.append(f"event_hash 被篡改: {index}")
        previous = event.get("event_hash")
        if expected_stage_index >= len(SEQUENCE):
            errors.append(f"完成后出现额外事件: {index}")
            continue
        stage, profile = SEQUENCE[expected_stage_index]
        if event.get("type") == "subrun":
            seen_subruns += 1
            if awaiting_mutation:
                errors.append(f"未提交 mutation 就开始下一 subrun: {index}")
            if event.get("stage") != stage or event.get("profile") != profile:
                errors.append(f"stage/profile 顺序错误: {index}")
            if event.get("round") != expected_round:
                errors.append(f"round 顺序错误: {index}")
            if event.get("mode") != ROUND_MODES.get(expected_round):
                errors.append(f"round mode 错误: {index}")
            if event.get("subject_digest") != current_digest:
                errors.append(f"subject digest 串用: {index}")
            if expected_round < 3 and event.get("staged_candidate_digest") is not None:
                errors.append(f"第三轮前出现批准哈希: {index}")
            if expected_round == 3:
                approved_digest = event.get("staged_candidate_digest")
                if not isinstance(approved_digest, str) or not re_full_sha(approved_digest):
                    errors.append(f"第三轮缺少批准哈希: {index}")
                awaiting_mutation = True
            expected_round += 1
        elif event.get("type") == "mutation_commit":
            seen_mutations += 1
            if not awaiting_mutation or expected_round != 4:
                errors.append(f"mutation 未在连续三轮后发生: {index}")
            if event.get("stage") != stage:
                errors.append(f"mutation stage 错误: {index}")
            if event.get("approved_candidate_digest") != approved_digest:
                errors.append(f"mutation 未绑定第三轮批准哈希: {index}")
            if event.get("actual_candidate_digest") != approved_digest:
                errors.append(f"mutation 在批准后改变了内容: {index}")
            if event.get("atomic_content_preserving") is not True:
                errors.append(f"mutation 未声明原子、内容保持: {index}")
            current_digest = approved_digest
            expected_stage_index += 1
            expected_round = 1
            awaiting_mutation = False
            approved_digest = None
        else:
            errors.append(f"未知事件类型: {index}")

    expected_complete = expected_stage_index == len(SEQUENCE) and not awaiting_mutation
    if require_complete and not expected_complete:
        errors.append("宏循环未完成：必须是 5 次调用 × 每次连续 3 轮 × 5 次已批准 mutation")
    if bool(state.get("complete")) != expected_complete:
        errors.append("state.complete 与事件账本不一致")
    if state.get("last_event_hash") != previous:
        errors.append("state.last_event_hash 与账本尾部不一致")
    if state.get("current_subject_digest") != current_digest:
        errors.append("state.current_subject_digest 与账本投影不一致")
    if require_complete and (seen_subruns != 15 or seen_mutations != 5):
        errors.append(f"完整运行必须为 15 subruns + 5 mutations，实际 {seen_subruns}+{seen_mutations}")
    return {
        "valid": not errors,
        "complete": expected_complete,
        "errors": errors,
        "events": len(events),
        "subruns": seen_subruns,
        "mutations": seen_mutations,
        "final_subject_digest": current_digest,
        "last_event_hash": previous,
        "contract_digest": object_sha256(contract),
    }
