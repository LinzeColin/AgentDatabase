from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
import time
import uuid
import zipfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

SKILL_ROOT = Path(__file__).resolve().parents[2]
STATE_NAME = "RUN_STATE.json"
STATUS_NAME = "RUN_STATUS.json"
SUMMARY_NAME = "SUMMARY.md"
NEXT_NAME = "NEXT_STAGE.json"
RESULT_NAME = "RESULT.json"
CONTROL_NAME = ".teleiosis"
IGNORED = {".git", CONTROL_NAME, "__pycache__", ".pytest_cache", ".mypy_cache", ".DS_Store"}
PUBLIC_ALLOWED = {"candidate", CONTROL_NAME, STATE_NAME, STATUS_NAME, SUMMARY_NAME, NEXT_NAME, RESULT_NAME}
MODULES = ("T", "S", "P")
MODULE_SLUGS = {"T": "raw_teleiosis", "S": "skill_market_lab", "P": "product_reality_lab"}
RESULTS = {"EXECUTED", "NOT_APPLICABLE_WITH_REASON", "NOT_RUN", "BLOCKED"}
DECISIONS = {"KEEP", "NO_CHANGE", "REVERT"}
DEFAULT_LIMITS = {
    "candidate_max_files": 100_000,
    "candidate_max_total_bytes": 10 * 1024 * 1024 * 1024,
    "candidate_max_single_file_bytes": 2 * 1024 * 1024 * 1024,
    "input_max_bytes": 8 * 1024 * 1024,
    "evidence_max_bytes": 256 * 1024 * 1024,
}
_SECRET_KEY = re.compile(r"(?i)(?:^|[_-])(token|secret|password|passwd|api[_-]?key|private[_-]?key|authorization|cookie|session)(?:$|[_-])")
_SECRET_VALUE = re.compile(
    r"(?i)(?:github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|"
    r"bearer\s+[A-Za-z0-9._~+/-]{16,}|https?://[^\s/@:]+:[^\s/@]+@)"
)


class RunError(ValueError):
    """A fail-closed, user-correctable Run contract error."""


def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp, path)
    finally:
        try:
            os.unlink(temp)
        except FileNotFoundError:
            pass


def atomic_json(path: Path, obj: Any) -> None:
    atomic_write(path, json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n")


def atomic_text(path: Path, text: str) -> None:
    atomic_write(path, text.encode("utf-8"))


def load_json(path: Path, *, max_bytes: Optional[int] = None) -> Any:
    if not path.is_file() or path.is_symlink():
        raise RunError(f"JSON 文件不存在或不是普通文件: {path}")
    if max_bytes is not None and path.stat().st_size > max_bytes:
        raise RunError(f"JSON 文件超过上限: {path.name}")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise RunError(f"JSON 无效: {path.name}: {exc}") from exc


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def _assert_disjoint(subject: Path, workspace: Path) -> None:
    if subject == workspace or _is_relative_to(workspace, subject) or _is_relative_to(subject, workspace):
        raise RunError("subject 与 workspace 必须彼此独立，不能互相嵌套")


def _scan_sensitive(value: Any, trail: str = "$") -> None:
    if isinstance(value, dict):
        for key, item in value.items():
            key_text = str(key)
            if _SECRET_KEY.search(key_text):
                raise RunError(f"输入包含敏感字段，已拒绝: {trail}.{key_text}")
            _scan_sensitive(item, f"{trail}.{key_text}")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            _scan_sensitive(item, f"{trail}[{index}]")
    elif isinstance(value, str) and _SECRET_VALUE.search(value):
        raise RunError(f"输入疑似包含凭证，已拒绝: {trail}")


def _scan_sensitive_text(text: str, label: str) -> None:
    if _SECRET_VALUE.search(text):
        raise RunError(f"{label} 疑似包含凭证，已拒绝")


def iter_files(root: Path, *, limits: Optional[Mapping[str, int]] = None) -> Iterable[Path]:
    if root.is_symlink() or not root.is_dir():
        raise RunError(f"必须是真实目录: {root}")
    max_files = int((limits or DEFAULT_LIMITS)["candidate_max_files"])
    max_total = int((limits or DEFAULT_LIMITS)["candidate_max_total_bytes"])
    max_single = int((limits or DEFAULT_LIMITS)["candidate_max_single_file_bytes"])
    count = 0
    total = 0
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root)
        if any(part in IGNORED for part in rel.parts):
            continue
        if path.is_symlink():
            raise RunError(f"Candidate 拒绝符号链接: {rel.as_posix()}")
        if path.is_file():
            size = path.stat().st_size
            count += 1
            total += size
            if count > max_files:
                raise RunError(f"Candidate 文件数超过上限 {max_files}")
            if size > max_single:
                raise RunError(f"Candidate 单文件超过上限: {rel.as_posix()}")
            if total > max_total:
                raise RunError("Candidate 总容量超过上限")
            yield path


def manifest(root: Path, *, limits: Optional[Mapping[str, int]] = None) -> Dict[str, Dict[str, Any]]:
    return {
        p.relative_to(root).as_posix(): {"sha256": sha256_file(p), "size_bytes": p.stat().st_size}
        for p in iter_files(root, limits=limits)
    }


def fingerprint(rows: Mapping[str, Any]) -> str:
    return sha256_bytes(json.dumps(rows, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def diff_manifests(before: Mapping[str, Any], after: Mapping[str, Any]) -> Dict[str, List[str]]:
    before_keys, after_keys = set(before), set(after)
    return {
        "added": sorted(after_keys - before_keys),
        "removed": sorted(before_keys - after_keys),
        "modified": sorted(k for k in before_keys & after_keys if before[k] != after[k]),
    }


def _has_delta(delta: Mapping[str, Sequence[str]]) -> bool:
    return any(delta.get(key) for key in ("added", "removed", "modified"))


def build_contract() -> Dict[str, Any]:
    stages: List[Dict[str, Any]] = []
    global_stage = 0
    revision = 0
    for group in range(1, 4):
        for round_number in range(1, 4):
            for module in MODULES:
                global_stage += 1
                revision += 1
                local_c = MODULES.index(module) + 1
                stages.append({
                    "global_stage": global_stage,
                    "group": group,
                    "round": round_number,
                    "module": module,
                    "module_name": MODULE_SLUGS[module],
                    "stage_label": f"G{group}R{round_number}-{module}1",
                    "candidate_label": f"G{group}R{round_number}-C{local_c}",
                    "global_candidate_revision": revision,
                })
    return {
        "schema_version": "teleiosis.full_run_contract.v3",
        "execution_mode": "FULL_NO_ROUTING",
        "round_sequence": ["T", "C", "S", "C", "P", "C"],
        "groups": 3,
        "rounds_per_group": 3,
        "module_stages": 27,
        "candidate_revisions": 27,
        "candidate_semantics": "C_IS_ITERATION_OBJECT_REVISION_NOT_SHA_CHECKPOINT",
        "fixed_sha_precondition": False,
        "fingerprint_role": "POST_STAGE_AUDIT_ONLY",
        "revision_store_role": "ROLLBACK_STORAGE_NOT_MERGE_PRECONDITION",
        "stages": stages,
    }


def _capabilities(module: str) -> List[Dict[str, Any]]:
    path = SKILL_ROOT / "modules" / MODULE_SLUGS[module] / "CAPABILITIES.json"
    doc = load_json(path)
    rows = doc.get("capabilities") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        raise RunError(f"内置模块能力清单无效: {module}")
    return list(rows)


def _control(workspace: Path) -> Path:
    return workspace / CONTROL_NAME


def _manifest_path(workspace: Path, revision_number: int) -> Path:
    return _control(workspace) / "manifests" / f"C{revision_number:03d}.json"


def _relative(workspace: Path, path: Path) -> str:
    return path.resolve().relative_to(workspace.resolve()).as_posix()


def _load_revision_manifest(workspace: Path, revision: Mapping[str, Any], limits: Mapping[str, int]) -> Dict[str, Any]:
    rel = str(revision.get("manifest_path") or "")
    path = workspace / rel
    doc = load_json(path, max_bytes=max(64 * 1024 * 1024, int(limits["input_max_bytes"])))
    if not isinstance(doc, dict):
        raise RunError(f"revision manifest 无效: {rel}")
    return doc


def _write_template(workspace: Path, expected: Mapping[str, Any]) -> Path:
    rows = [{"id": x["id"], "status": "NOT_RUN", "reason": "", "evidence_refs": []} for x in _capabilities(str(expected["module"]))]
    path = workspace / NEXT_NAME
    atomic_json(path, {
        "schema_version": "teleiosis.capability_results.v1",
        "module": expected["module"],
        "global_stage": expected["global_stage"],
        "results": rows,
    })
    return path


def _public_status(state: Mapping[str, Any]) -> Dict[str, Any]:
    index = int(state.get("next_stage_index", 0))
    stages = state["contract"]["stages"]
    return {
        "schema_version": "teleiosis.run_status.v3",
        "status": state.get("status"),
        "run_id": state.get("run_id"),
        "candidate_id": state.get("candidate_id"),
        "completed_stages": index,
        "required_stages": len(stages),
        "candidate_revisions": len(state.get("revisions", [])),
        "next": stages[index] if index < len(stages) and state.get("status") == "ACTIVE" else None,
        "execution_mode": "FULL_NO_ROUTING",
        "fixed_sha_precondition": False,
        "updated_at": state.get("updated_at"),
    }


def _summary_text(state: Mapping[str, Any]) -> str:
    status = _public_status(state)
    next_stage = status.get("next") or {}
    next_text = "无（已完成或已阻断）" if not next_stage else f"G{next_stage['group']} R{next_stage['round']} / {next_stage['module']}"
    return (
        "# Teleiosis Run\n\n"
        f"- 状态：`{status['status']}`\n"
        f"- 进度：`{status['completed_stages']}/{status['required_stages']}`\n"
        f"- 下一阶段：`{next_text}`\n"
        "- 路径：`T1 -> C1 -> S1 -> C2 -> P1 -> C3`，三轮一组、三组一次 Run\n"
        "- C：迭代对象本身的连续 Candidate revision，不是固定 SHA 前置条件\n"
    )


def _refresh_public(workspace: Path, state: Mapping[str, Any], result: Optional[Mapping[str, Any]] = None) -> None:
    atomic_json(workspace / STATUS_NAME, _public_status(state))
    atomic_text(workspace / SUMMARY_NAME, _summary_text(state))
    if result is not None:
        atomic_json(workspace / RESULT_NAME, result)


def _assert_clean_public_workspace(workspace: Path) -> List[str]:
    extras = sorted(path.name for path in workspace.iterdir() if path.name not in PUBLIC_ALLOWED)
    return extras


def _git_base(workspace: Path) -> List[str]:
    repo = _control(workspace) / "revision-store"
    candidate = workspace / "candidate"
    return ["git", f"--git-dir={repo / '.git'}", f"--work-tree={candidate}"]


def _run(command: Sequence[str], *, cwd: Optional[Path] = None, timeout: int = 180, check: bool = True) -> subprocess.CompletedProcess[str]:
    env = {
        **os.environ,
        "PYTHONDONTWRITEBYTECODE": "1",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_CONFIG_NOSYSTEM": "1",
        "TERM": "dumb",
    }
    cp = subprocess.run(list(command), cwd=cwd, env=env, text=True, capture_output=True, timeout=timeout)
    if check and cp.returncode != 0:
        raise RunError(f"命令失败: {' '.join(command[:4])}: {cp.stderr[-1000:].strip()}")
    return cp


def _git(workspace: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    return _run([*_git_base(workspace), *args], cwd=workspace, check=check)


def _init_revision_store(workspace: Path) -> str:
    control = _control(workspace)
    repo = control / "revision-store"
    hooks = control / "empty-hooks"
    hooks.mkdir(parents=True, exist_ok=True)
    _run(["git", "init", "-b", "main", str(repo)], cwd=workspace)
    _git(workspace, "config", "user.name", "Teleiosis Revision Store")
    _git(workspace, "config", "user.email", "teleiosis@local.invalid")
    _git(workspace, "config", "commit.gpgsign", "false")
    _git(workspace, "config", "core.autocrlf", "false")
    _git(workspace, "config", "core.hooksPath", str(hooks))
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "--allow-empty", "-m", "C000 baseline")
    _git(workspace, "tag", "C000")
    return _git(workspace, "rev-parse", "HEAD").stdout.strip()


def _commit_revision(workspace: Path, ref: str, message: str) -> str:
    _git(workspace, "add", "-A")
    _git(workspace, "commit", "--allow-empty", "-m", message)
    _git(workspace, "tag", ref)
    return _git(workspace, "rev-parse", "HEAD").stdout.strip()


def _rollback_revision_store(workspace: Path, commit: str, ref: str = "") -> None:
    _git(workspace, "update-ref", "refs/heads/main", commit)
    if ref:
        _git(workspace, "tag", "-d", ref, check=False)


def _safe_extract_tar(tar_path: Path, destination: Path) -> None:
    """Extract only regular files/directories without tarfile.extractall side effects."""
    destination.mkdir(parents=True, exist_ok=False)
    root = destination.resolve()
    with tarfile.open(tar_path, "r") as archive:
        for member in archive.getmembers():
            target = (destination / member.name).resolve()
            if target != root and not _is_relative_to(target, root):
                raise RunError("revision archive 包含路径穿越")
            if member.issym() or member.islnk() or member.isdev():
                raise RunError("revision archive 包含不安全条目")
            if member.isdir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            if not member.isfile():
                raise RunError("revision archive 包含非普通文件")
            target.parent.mkdir(parents=True, exist_ok=True)
            source = archive.extractfile(member)
            if source is None:
                raise RunError("revision archive 文件不可读取")
            with source, target.open("wb") as handle:
                shutil.copyfileobj(source, handle, length=1024 * 1024)
            os.chmod(target, 0o755 if (member.mode & 0o111) else 0o644)


def _tree_from_ref(workspace: Path, ref: str, destination: Path) -> None:
    tar_path = _control(workspace) / "transactions" / f"archive-{uuid.uuid4().hex}.tar"
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        _git(workspace, "archive", "--format=tar", f"--output={tar_path}", ref)
        _safe_extract_tar(tar_path, destination)
    finally:
        tar_path.unlink(missing_ok=True)


def _zip_tree(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(destination, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in iter_files(source):
            rel = path.relative_to(source).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())


def _copy_input(source: Path, destination: Path, max_bytes: int, *, scan_text: bool = True) -> Dict[str, Any]:
    source = source.resolve()
    if not source.is_file() or source.is_symlink():
        raise RunError(f"输入文件不存在或不是普通文件: {source}")
    size = source.stat().st_size
    if size > max_bytes:
        raise RunError(f"输入文件超过容量上限: {source.name}")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)
    if scan_text and source.suffix.lower() in {".json", ".jsonl", ".txt", ".md", ".csv", ".yaml", ".yml"}:
        text = destination.read_text(encoding="utf-8", errors="strict")
        _scan_sensitive_text(text, source.name)
    return {"path": destination, "sha256": sha256_file(destination), "size_bytes": size}


def _cleanup_consumed_input(path: Path, workspace: Path) -> None:
    try:
        rel = path.resolve().relative_to(workspace.resolve())
    except ValueError:
        return
    if len(rel.parts) == 1 and rel.name not in {STATE_NAME, STATUS_NAME, SUMMARY_NAME, NEXT_NAME, RESULT_NAME}:
        path.unlink(missing_ok=True)


def init_run(
    subject: Path,
    workspace: Path,
    *,
    candidate_id: str = "",
    copy_subject: bool = True,
    limits: Optional[Mapping[str, int]] = None,
) -> Dict[str, Any]:
    subject, workspace = subject.expanduser().resolve(), workspace.expanduser().resolve()
    _assert_disjoint(subject, workspace)
    if not subject.is_dir() or subject.is_symlink():
        raise RunError(f"subject 必须是真实目录: {subject}")
    effective_limits = {**DEFAULT_LIMITS, **{k: int(v) for k, v in (limits or {}).items()}}
    if any(value <= 0 for value in effective_limits.values()):
        raise RunError("容量限制必须为正数")
    # Validate the source before creating any output.
    source_manifest = manifest(subject, limits=effective_limits)
    if workspace.exists() and any(workspace.iterdir()):
        state_path = workspace / STATE_NAME
        if state_path.is_file() and load_json(state_path).get("status") == "ACTIVE":
            raise RunError("拒绝嵌套或重复 Run：workspace 已处于 ACTIVE")
        raise RunError("workspace 必须不存在或为空目录")
    workspace.mkdir(parents=True, exist_ok=True)
    candidate_path = workspace / "candidate"
    try:
        if copy_subject:
            shutil.copytree(subject, candidate_path, symlinks=False, ignore=shutil.ignore_patterns(*IGNORED))
        else:
            raise RunError("v0.0.0.3 只允许在 workspace 内复制 Candidate，禁止直接改写 subject")
        candidate_manifest = manifest(candidate_path, limits=effective_limits)
        if candidate_manifest != source_manifest:
            raise RunError("Candidate 初始化复制不完整")
        control = _control(workspace)
        (control / "manifests").mkdir(parents=True)
        (control / "evidence").mkdir()
        (control / "rejected").mkdir()
        (control / "transactions").mkdir()
        initial_manifest_path = _manifest_path(workspace, 0)
        atomic_json(initial_manifest_path, candidate_manifest)
        revision_commit = _init_revision_store(workspace)
        cid = candidate_id.strip() or f"candidate-{uuid.uuid4().hex[:12]}"
        if not re.fullmatch(r"[A-Za-z0-9._-]{3,80}", cid):
            raise RunError("candidate-id 仅允许 3-80 位字母、数字、点、下划线和连字符")
        contract = build_contract()
        now = utc_now()
        state = {
            "schema_version": "teleiosis.full_run_state.v3.1",
            "run_id": f"teleiosis-{uuid.uuid4().hex}",
            "status": "ACTIVE",
            "nested_run_guard": True,
            "execution_mode": "FULL_NO_ROUTING",
            "candidate_semantics": contract["candidate_semantics"],
            "candidate_id": cid,
            "subject": {"name": subject.name, "initial_fingerprint": fingerprint(source_manifest)},
            "candidate_path": "candidate",
            "created_at": now,
            "updated_at": now,
            "next_stage_index": 0,
            "limits": effective_limits,
            "initial_revision": {
                "revision_id": f"{cid}:C000",
                "revision_number": 0,
                "parent_revision_id": None,
                "candidate_path": "candidate",
                "revision_store_ref": "C000",
                "revision_store_commit": revision_commit,
                "revision_store_role": "ROLLBACK_STORAGE_NOT_MERGE_PRECONDITION",
                "manifest_path": _relative(workspace, initial_manifest_path),
                "content_fingerprint": fingerprint(candidate_manifest),
            },
            "revisions": [],
            "events": [],
            "contract": contract,
        }
        atomic_json(workspace / STATE_NAME, state)
        _write_template(workspace, contract["stages"][0])
        result = {
            "status": "INITIALIZED",
            "run_id": state["run_id"],
            "workspace": str(workspace),
            "candidate_path": str(candidate_path),
            "candidate_id": cid,
            "next": contract["stages"][0],
            "public_files": sorted(PUBLIC_ALLOWED),
        }
        _refresh_public(workspace, state, result)
        return result
    except Exception:
        shutil.rmtree(workspace, ignore_errors=True)
        raise


def _validate_capability_results(
    module: str,
    expected_stage: int,
    path: Path,
    *,
    max_bytes: int,
) -> Tuple[List[Dict[str, Any]], List[str], str]:
    doc = load_json(path, max_bytes=max_bytes)
    _scan_sensitive(doc)
    errors: List[str] = []
    if not isinstance(doc, dict):
        raise RunError("capability result 必须是 JSON object")
    allowed_top = {"schema_version", "module", "global_stage", "results"}
    extra_top = sorted(set(doc) - allowed_top)
    if extra_top:
        errors.append(f"capability result 含未声明字段: {extra_top}")
    if doc.get("schema_version") != "teleiosis.capability_results.v1":
        errors.append("capability result schema_version 不匹配")
    if doc.get("module") != module:
        errors.append("capability result module 与当前阶段不匹配")
    if doc.get("global_stage") != expected_stage:
        errors.append("capability result global_stage 与当前阶段不匹配")
    expected = [str(x["id"]) for x in _capabilities(module)]
    raw_rows = doc.get("results")
    if not isinstance(raw_rows, list):
        errors.append("capability result results 必须是 list")
        raw_rows = []
    rows: List[Dict[str, Any]] = []
    observed: List[str] = []
    allowed_row = {"id", "status", "reason", "evidence_refs"}
    for index, raw in enumerate(raw_rows):
        if not isinstance(raw, dict):
            errors.append(f"capability row {index} 必须是 object")
            continue
        extra = sorted(set(raw) - allowed_row)
        if extra:
            errors.append(f"capability row {index} 含未声明字段: {extra}")
        row = {
            "id": str(raw.get("id") or ""),
            "status": str(raw.get("status") or ""),
            "reason": str(raw.get("reason") or ""),
            "evidence_refs": raw.get("evidence_refs") if isinstance(raw.get("evidence_refs"), list) else [],
        }
        observed.append(row["id"])
        if row["status"] not in RESULTS:
            errors.append(f"invalid capability status for {row['id']}: {row['status']}")
        if row["status"] == "NOT_APPLICABLE_WITH_REASON" and not row["reason"].strip():
            errors.append(f"N/A capability requires reason: {row['id']}")
        if row["status"] == "EXECUTED" and not row["evidence_refs"]:
            errors.append(f"executed capability requires evidence_refs: {row['id']}")
        if not all(isinstance(ref, str) and 0 < len(ref) <= 500 for ref in row["evidence_refs"]):
            errors.append(f"evidence_refs 必须是非空短字符串: {row['id']}")
        rows.append(row)
    if observed != expected:
        errors.append("capability results 必须按原顺序完整覆盖 Capability Manifest")
    statuses = {row["status"] for row in rows}
    if "BLOCKED" in statuses:
        derived = "BLOCKED"
    elif "NOT_RUN" in statuses:
        derived = "NOT_RUN"
    elif statuses and statuses <= {"NOT_APPLICABLE_WITH_REASON"}:
        derived = "NOT_APPLICABLE_WITH_REASON"
    else:
        derived = "EXECUTED"
    return rows, errors, derived


def _replace_candidate_with_ref(workspace: Path, ref: str, transaction: Path) -> Path:
    candidate = workspace / "candidate"
    original = transaction / "candidate-before-revert"
    restored = transaction / "candidate-restored"
    os.replace(candidate, original)
    try:
        _tree_from_ref(workspace, ref, restored)
        os.replace(restored, candidate)
        return original
    except Exception:
        shutil.rmtree(restored, ignore_errors=True)
        if not candidate.exists() and original.exists():
            os.replace(original, candidate)
        raise


def _restore_original_candidate(workspace: Path, original: Path) -> None:
    candidate = workspace / "candidate"
    shutil.rmtree(candidate, ignore_errors=True)
    if original.exists():
        os.replace(original, candidate)


def record_stage(
    workspace: Path,
    module: str,
    result: str,
    capability_results: Path,
    *,
    evidence: Optional[Path] = None,
    decision: str = "KEEP",
    rollback_pointer: str = "",
    note: str = "",
) -> Dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    state_path = workspace / STATE_NAME
    state = load_json(state_path)
    if state.get("status") != "ACTIVE":
        raise RunError(f"Run 不是 ACTIVE: {state.get('status')}")
    extras = _assert_clean_public_workspace(workspace)
    allowed_transient = {Path(capability_results).name}
    if evidence:
        allowed_transient.add(Path(evidence).name)
    extras = [name for name in extras if name not in allowed_transient]
    if extras:
        raise RunError(f"workspace 根目录含未知文件，先清理: {extras}")
    index = int(state.get("next_stage_index", 0))
    stages = state["contract"]["stages"]
    if index >= len(stages):
        raise RunError("Run 已包含全部阶段")
    expected = stages[index]
    module = module.upper()
    if module != expected["module"]:
        raise RunError(f"wrong module order: expected {expected['module']} got {module}")
    result = result.upper()
    if result == "AUTO":
        pass
    elif result not in RESULTS:
        raise RunError(f"invalid stage result: {result}")
    decision = decision.upper()
    if decision not in DECISIONS:
        raise RunError(f"decision 必须是 {sorted(DECISIONS)}")
    _scan_sensitive_text(note, "note")
    limits = state.get("limits") or DEFAULT_LIMITS
    capability_results = capability_results.expanduser().resolve()
    rows, errors, derived_result = _validate_capability_results(
        module,
        int(expected["global_stage"]),
        capability_results,
        max_bytes=int(limits["input_max_bytes"]),
    )
    if errors:
        raise RunError("; ".join(errors))
    if result != "AUTO" and result != derived_result:
        raise RunError(f"stage result 与 Capability Manifest 不一致: supplied={result}, derived={derived_result}")
    result = derived_result
    candidate_path = workspace / str(state.get("candidate_path") or "candidate")
    if not candidate_path.is_dir() or candidate_path.is_symlink():
        raise RunError("candidate path missing or unsafe")
    current_manifest = manifest(candidate_path, limits=limits)
    parent = state["revisions"][-1] if state["revisions"] else state["initial_revision"]
    parent_manifest = _load_revision_manifest(workspace, parent, limits)
    delta_before_decision = diff_manifests(parent_manifest, current_manifest)
    has_delta = _has_delta(delta_before_decision)
    if decision == "NO_CHANGE" and has_delta:
        raise RunError("NO_CHANGE 与 Candidate 实际变化冲突；修改被保留，请选择 KEEP 或 REVERT")
    if decision == "REVERT" and not has_delta:
        raise RunError("REVERT 但 Candidate 没有变化；请使用 NO_CHANGE")
    normalized_from = None
    if decision == "KEEP" and not has_delta:
        normalized_from = "KEEP"
        decision = "NO_CHANGE"
    revision_number = index + 1
    revision_ref = f"C{revision_number:03d}"
    revision_id = f"{state['candidate_id']}:{revision_ref}"
    control = _control(workspace)
    transaction = control / "transactions" / f"stage-{revision_ref}-{uuid.uuid4().hex}"
    evidence_final = control / "evidence" / revision_ref
    rejected_final = control / "rejected" / revision_ref
    transaction.mkdir(parents=True, exist_ok=False)
    original_candidate: Optional[Path] = None
    parent_commit = str(parent.get("revision_store_commit") or _git(workspace, "rev-parse", "HEAD").stdout.strip())
    commit_created = False
    try:
        capability_copy = _copy_input(
            capability_results,
            transaction / "evidence" / "capabilities.json",
            int(limits["input_max_bytes"]),
        )
        evidence_copy: Optional[Dict[str, Any]] = None
        if evidence:
            evidence_copy = _copy_input(
                evidence.expanduser().resolve(),
                transaction / "evidence" / f"evidence{evidence.suffix.lower() or '.bin'}",
                int(limits["evidence_max_bytes"]),
            )
        rejected_archive_rel = ""
        if decision == "REVERT":
            rejected_zip = transaction / "rejected" / "candidate-before-revert.zip"
            _zip_tree(candidate_path, rejected_zip)
            atomic_json(transaction / "rejected" / "rejected-delta.json", {
                "decision": "REVERT",
                "delta": delta_before_decision,
                "content_fingerprint": fingerprint(current_manifest),
                "created_at": utc_now(),
            })
            original_candidate = _replace_candidate_with_ref(workspace, str(parent["revision_store_ref"]), transaction)
            current_manifest = manifest(candidate_path, limits=limits)
            if current_manifest != parent_manifest:
                raise RunError("REVERT 后 Candidate 与父 revision 不一致")
            rejected_archive_rel = f"{CONTROL_NAME}/rejected/{revision_ref}/candidate-before-revert.zip"
        final_delta = diff_manifests(parent_manifest, current_manifest)
        manifest_pending = transaction / "manifest.json"
        atomic_json(manifest_pending, current_manifest)
        revision_commit = _commit_revision(
            workspace,
            revision_ref,
            f"{revision_ref} G{expected['group']}R{expected['round']} {module} {decision}",
        )
        commit_created = True
        capability_rel = f"{CONTROL_NAME}/evidence/{revision_ref}/capabilities.json"
        evidence_rel = ""
        if evidence_copy:
            evidence_rel = f"{CONTROL_NAME}/evidence/{revision_ref}/{Path(evidence_copy['path']).name}"
        revision = {
            "revision_id": revision_id,
            "revision_number": revision_number,
            "parent_revision_id": parent["revision_id"],
            "candidate_id": state["candidate_id"],
            "candidate_path": "candidate",
            "revision_store_ref": revision_ref,
            "revision_store_commit": revision_commit,
            "revision_store_role": "ROLLBACK_STORAGE_NOT_MERGE_PRECONDITION",
            "module": module,
            "module_name": MODULE_SLUGS[module],
            "group": expected["group"],
            "round": expected["round"],
            "stage_label": expected["stage_label"],
            "candidate_label": expected["candidate_label"],
            "result": result,
            "decision": decision,
            "decision_normalized_from": normalized_from,
            "changed_files_before_decision": delta_before_decision,
            "changed_files": final_delta,
            "content_fingerprint": fingerprint(current_manifest),
            "fingerprint_role": "POST_STAGE_AUDIT_ONLY",
            "fixed_sha_precondition": False,
            "manifest_path": f"{CONTROL_NAME}/manifests/{revision_ref}.json",
            "capability_results_path": capability_rel,
            "capability_results_sha256": capability_copy["sha256"],
            "capability_results": rows,
            "evidence_path": evidence_rel or None,
            "evidence_sha256": evidence_copy["sha256"] if evidence_copy else None,
            "rollback_pointer": rollback_pointer.strip() or str(parent["revision_store_ref"]),
            "rejected_candidate_archive": rejected_archive_rel or None,
            "note": note,
            "recorded_at": utc_now(),
        }
        record_pending = transaction / "evidence" / "record.json"
        atomic_json(record_pending, {k: v for k, v in revision.items() if k != "capability_results"})
        new_state = copy.deepcopy(state)
        new_state["revisions"].append(revision)
        new_state["events"].append({
            "event": "CANDIDATE_REVISION_RECORDED",
            "revision_id": revision_id,
            "module": module,
            "decision": decision,
            "content_fingerprint": revision["content_fingerprint"],
            "fixed_sha_precondition": False,
            "at": revision["recorded_at"],
        })
        new_state["next_stage_index"] = index + 1
        new_state["updated_at"] = utc_now()
        if result in {"BLOCKED", "NOT_RUN"}:
            new_state["status"] = "BLOCKED"
        elif new_state["next_stage_index"] == len(stages):
            new_state["status"] = "COMPLETE_PENDING_VALIDATION"
        # All pending artifacts are complete before they become visible.
        manifest_final = _manifest_path(workspace, revision_number)
        if manifest_final.exists() or evidence_final.exists() or rejected_final.exists():
            raise RunError(f"revision output already exists: {revision_ref}")
        os.replace(manifest_pending, manifest_final)
        os.replace(transaction / "evidence", evidence_final)
        if (transaction / "rejected").exists():
            os.replace(transaction / "rejected", rejected_final)
        atomic_json(state_path, new_state)
        state = new_state
        if state["status"] == "ACTIVE":
            _write_template(workspace, stages[state["next_stage_index"]])
        else:
            (workspace / NEXT_NAME).unlink(missing_ok=True)
        result_doc = {
            "status": "RECORDED",
            "revision": revision,
            "run_status": state["status"],
            "next": stages[state["next_stage_index"]] if state["status"] == "ACTIVE" else None,
        }
        _refresh_public(workspace, state, result_doc)
        _cleanup_consumed_input(capability_results, workspace)
        if evidence:
            _cleanup_consumed_input(evidence.expanduser().resolve(), workspace)
        if original_candidate and original_candidate.exists():
            shutil.rmtree(original_candidate, ignore_errors=True)
        shutil.rmtree(transaction, ignore_errors=True)
        return result_doc
    except Exception:
        if commit_created:
            _rollback_revision_store(workspace, parent_commit, revision_ref)
        if original_candidate is not None:
            _restore_original_candidate(workspace, original_candidate)
        shutil.rmtree(evidence_final, ignore_errors=True)
        shutil.rmtree(rejected_final, ignore_errors=True)
        _manifest_path(workspace, revision_number).unlink(missing_ok=True)
        shutil.rmtree(transaction, ignore_errors=True)
        raise


def run_status(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    state = load_json(workspace / STATE_NAME)
    return _public_status(state)


def _verify_revision_artifacts(workspace: Path, revision: Mapping[str, Any], errors: List[str]) -> None:
    manifest_path = workspace / str(revision.get("manifest_path") or "")
    if not manifest_path.is_file():
        errors.append(f"revision {revision.get('revision_number')} manifest missing")
    else:
        try:
            doc = load_json(manifest_path)
            if fingerprint(doc) != revision.get("content_fingerprint"):
                errors.append(f"revision {revision.get('revision_number')} manifest fingerprint mismatch")
        except Exception as exc:
            errors.append(f"revision {revision.get('revision_number')} manifest invalid: {exc}")
    capability_path = workspace / str(revision.get("capability_results_path") or "")
    if not capability_path.is_file() or sha256_file(capability_path) != revision.get("capability_results_sha256"):
        errors.append(f"revision {revision.get('revision_number')} capability evidence mismatch")
    evidence_rel = revision.get("evidence_path")
    if evidence_rel:
        evidence_path = workspace / str(evidence_rel)
        if not evidence_path.is_file() or sha256_file(evidence_path) != revision.get("evidence_sha256"):
            errors.append(f"revision {revision.get('revision_number')} evidence mismatch")
    ref = str(revision.get("revision_store_ref") or "")
    cp = _git(workspace, "rev-parse", "--verify", ref, check=False)
    if cp.returncode != 0 or cp.stdout.strip() != revision.get("revision_store_commit"):
        errors.append(f"revision {revision.get('revision_number')} revision-store ref mismatch")


def validate_run(workspace: Path, *, require_complete: bool = False) -> Dict[str, Any]:
    workspace = workspace.expanduser().resolve()
    state = load_json(workspace / STATE_NAME)
    errors: List[str] = []
    contract = build_contract()
    if state.get("candidate_semantics") != contract["candidate_semantics"]:
        errors.append("candidate semantics mismatch")
    if state.get("execution_mode") != "FULL_NO_ROUTING":
        errors.append("execution mode is not FULL_NO_ROUTING")
    extras = _assert_clean_public_workspace(workspace)
    if extras:
        errors.append(f"workspace root contains unexpected entries: {extras}")
    revisions = list(state.get("revisions") or [])
    for idx, revision in enumerate(revisions):
        if idx >= len(contract["stages"]):
            errors.append(f"unexpected extra revision {idx + 1}")
            break
        expected = contract["stages"][idx]
        if revision.get("module") != expected["module"]:
            errors.append(f"stage {idx+1} module order mismatch")
        expected_parent = state["initial_revision"]["revision_id"] if idx == 0 else revisions[idx - 1]["revision_id"]
        if revision.get("parent_revision_id") != expected_parent:
            errors.append(f"stage {idx+1} parent revision mismatch")
        if revision.get("fixed_sha_precondition") is not False:
            errors.append(f"stage {idx+1} contains a fixed SHA precondition")
        if not revision.get("rollback_pointer"):
            errors.append(f"stage {idx+1} missing rollback pointer")
        rows = revision.get("capability_results") or []
        if len(rows) != len(_capabilities(expected["module"])):
            errors.append(f"stage {idx+1} capability manifest incomplete")
        if any(row.get("status") in {"NOT_RUN", "BLOCKED"} for row in rows):
            errors.append(f"stage {idx+1} has NOT_RUN/BLOCKED capability")
        if revision.get("result") in {"NOT_RUN", "BLOCKED"}:
            errors.append(f"stage {idx+1} result is not complete")
        _verify_revision_artifacts(workspace, revision, errors)
    fsck = _git(workspace, "fsck", "--no-dangling", check=False)
    if fsck.returncode != 0:
        errors.append("revision store fsck failed")
    if require_complete and len(revisions) != 27:
        errors.append(f"complete Run requires 27 revisions, observed {len(revisions)}")
    if revisions:
        try:
            current = manifest(workspace / "candidate", limits=state.get("limits") or DEFAULT_LIMITS)
            if fingerprint(current) != revisions[-1].get("content_fingerprint"):
                errors.append("current Candidate does not match latest recorded revision")
        except Exception as exc:
            errors.append(f"current Candidate validation failed: {exc}")
    final_status = "PASS" if not errors and (not require_complete or len(revisions) == 27) else "FAIL"
    if final_status == "PASS" and require_complete:
        state["status"] = "COMPLETE"
        state["completed_at"] = utc_now()
        state["updated_at"] = state["completed_at"]
        atomic_json(workspace / STATE_NAME, state)
        (workspace / NEXT_NAME).unlink(missing_ok=True)
    result = {
        "status": final_status,
        "run_status": state.get("status"),
        "revision_count": len(revisions),
        "required_revision_count": 27,
        "module_counts": {m: sum(1 for row in revisions if row.get("module") == m) for m in MODULES},
        "fixed_sha_preconditions": 0,
        "workspace_clean": not extras,
        "errors": errors,
    }
    _refresh_public(workspace, state, result)
    return result


def simulate_run(subject: Path, workspace: Path) -> Dict[str, Any]:
    init_run(subject, workspace)
    control = _control(workspace)
    simulation = control / "simulation-input"
    simulation.mkdir(parents=True, exist_ok=True)
    for idx, expected in enumerate(build_contract()["stages"], 1):
        cap = workspace / NEXT_NAME
        doc = load_json(cap)
        doc["results"] = [
            {
                "id": row["id"],
                "status": "EXECUTED",
                "reason": "synthetic controller compatibility fixture",
                "evidence_refs": [f"synthetic://stage/{idx}/{row['id']}"],
            }
            for row in _capabilities(expected["module"])
        ]
        atomic_json(cap, doc)
        evidence = simulation / f"evidence-{idx:03d}.json"
        atomic_json(evidence, {
            "evidence_class": "SYNTHETIC",
            "stage": idx,
            "module": expected["module"],
            "real_market_evidence": "NOT_CLAIMED",
        })
        record_stage(
            workspace,
            expected["module"],
            "AUTO",
            cap,
            evidence=evidence,
            decision="NO_CHANGE",
            note="synthetic controller compatibility fixture",
        )
    shutil.rmtree(simulation, ignore_errors=True)
    return validate_run(workspace, require_complete=True)
