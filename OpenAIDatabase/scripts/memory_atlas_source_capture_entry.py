#!/usr/bin/env python3
from __future__ import annotations

import argparse
import fcntl
import json
import os
import shutil
import signal
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


TEMP_PREFIX = "memory-atlas-daily-"
MAX_RUN_SECONDS = 6 * 60 * 60
STALE_SECONDS = 24 * 60 * 60


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "OpenAIDatabase" / "AGENTS.md").is_file() and (candidate / "MemoryAtlas").is_dir():
            return candidate
    raise RuntimeError("无法定位 AgentDatabase 仓库根目录")


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def protected_incremental_state_dir(env_path: Path) -> Path:
    """Return the only durable local state: a protected deduplication journal.

    Raw snapshots, release payloads, and web projections remain in the per-run
    temporary directory. The journal is committed only after a completed run,
    so losing it can cause extra work but cannot cause data to be skipped.
    """
    state_dir = env_path.resolve().parent / "memory-atlas-state"
    try:
        if state_dir.exists():
            if state_dir.is_symlink() or not state_dir.is_dir():
                raise RuntimeError("protected_incremental_state_invalid")
        else:
            state_dir.mkdir(mode=0o700)
        state_dir.chmod(0o700)
    except OSError as exc:
        raise RuntimeError("protected_incremental_state_unavailable") from exc
    return state_dir


def acquire_capture_lock(state_dir: Path) -> Any:
    """Hold one host-local lock so scheduled captures never overlap."""
    handle = (state_dir / "capture.lock").open("a+", encoding="utf-8")
    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError as exc:
        handle.close()
        raise RuntimeError("concurrent_capture_active") from exc
    except OSError as exc:
        handle.close()
        raise RuntimeError("protected_incremental_lock_unavailable") from exc
    return handle


def _is_owned_temp(path: Path, temporary_root: Path) -> bool:
    try:
        return (
            not path.is_symlink()
            and path.name.startswith(TEMP_PREFIX)
            and path.resolve().parent == temporary_root.resolve()
            and path.stat().st_uid == os.getuid()
        )
    except OSError:
        return False


def cleanup_stale_run_dirs(temporary_root: Path, *, now: float | None = None) -> int:
    observed_now = time.time() if now is None else now
    cleaned = 0
    for candidate in temporary_root.glob(f"{TEMP_PREFIX}*"):
        if not _is_owned_temp(candidate, temporary_root):
            continue
        try:
            age_seconds = observed_now - candidate.stat().st_mtime
        except OSError:
            continue
        if age_seconds < STALE_SECONDS:
            continue
        try:
            shutil.rmtree(candidate)
        except OSError:
            continue
        else:
            cleaned += 1
    return cleaned


def _run_capture(command: list[str], *, cwd: Path, env: dict[str, str]) -> subprocess.CompletedProcess[str]:
    process = subprocess.Popen(
        command,
        cwd=cwd,
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=MAX_RUN_SECONDS)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGTERM)
        try:
            stdout, stderr = process.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(command, 124, stdout, stderr)
    return subprocess.CompletedProcess(command, process.returncode, stdout, stderr)


def _child_payload(stdout: str) -> dict[str, Any]:
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError("capture_result_json_missing") from exc
    if not isinstance(value, dict):
        raise RuntimeError("capture_result_json_invalid")
    return value


def _safe_child_failure_code(returncode: int, stderr: str) -> str:
    """Expose a stable diagnosis without publishing child stderr or paths."""
    if returncode == 124:
        return "CHILD_CAPTURE_TIMEOUT"
    if "No module named 'boto3'" in stderr:
        return "MISSING_BOTO3_DEPENDENCY"
    if "Read-only file system" in stderr:
        return "RUNTIME_DIRECTORY_UNWRITABLE"
    if "logical_source_contract_mismatch" in stderr:
        return "PRIVATE_BACKUP_SOURCE_CONTRACT_MISMATCH"
    if "scope_policy_invalid" in stderr:
        return "PRIVATE_BACKUP_SCOPE_POLICY_INVALID"
    if "private_identity_unavailable" in stderr:
        return "PRIVATE_BACKUP_IDENTITY_UNAVAILABLE"
    if "github_release_command_failed" in stderr:
        return "GITHUB_RELEASE_COMMAND_FAILED"
    if "No module named" in stderr:
        return "PYTHON_DEPENDENCY_MISSING"
    if returncode != 0:
        return "CHILD_EXITED_BEFORE_STRUCTURED_RESULT"
    return "CHILD_STRUCTURED_RESULT_MISSING"


def _parse_args(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Run one Memory Atlas source capture with temporary payloads and a protected incremental journal."
    )
    parser.parse_args(argv)


def _public_safe_source_coverage(value: object) -> list[dict[str, Any]] | None:
    if not isinstance(value, list):
        return None
    safe: list[dict[str, Any]] = []
    for raw in value:
        if not isinstance(raw, dict):
            continue
        state = str(raw.get("state", "UNKNOWN"))
        row = {
            key: raw.get(key)
            for key in (
                "source_id",
                "label_zh",
                "required",
                "state",
                "object_count",
                "size_bytes",
            )
        }
        row["reason_code"] = {
            "READY": "READY",
            "UNREADABLE": "STANDALONE_CREDENTIAL_LIKE_FILE_EXCLUDED",
            "MISSING_OPTIONAL": "OPTIONAL_SOURCE_NOT_CONFIGURED_OR_VISIBLE",
            "MISSING_REQUIRED": "REQUIRED_SOURCE_NOT_CONFIGURED_OR_VISIBLE",
            "EMPTY": "VISIBLE_SOURCE_EMPTY",
        }.get(state, "UNKNOWN")
        safe.append(row)
    return safe


def main(argv: list[str] | None = None) -> None:
    _parse_args([] if argv is None else argv)
    repo = find_repo_root(Path(__file__).resolve())
    env_path = Path(os.environ.get(
        "MEMORY_ATLAS_ENV_FILE",
        str(Path.home() / ".codex" / "memory-atlas" / "memory-atlas.env"),
    )).expanduser()
    if not env_path.is_file():
        print(json.dumps({
            "state": "BLOCKED",
            "message_zh": "缺少已验证的 Memory Atlas 受保护环境文件。先运行 bootstrap-protected-env。",
            "expected_path": str(env_path),
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    values = load_env_file(env_path)
    process_env = os.environ
    linked_protected_root = env_path.resolve().parent if env_path.is_symlink() else None
    try:
        incremental_state_dir = protected_incremental_state_dir(env_path)
        capture_lock = acquire_capture_lock(incremental_state_dir)
    except RuntimeError as exc:
        print(json.dumps({
            "state": "BLOCKED",
            "failure_code": str(exc),
            "message_zh": "受保护的增量备份状态目录不可用；未启动采集。",
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2) from exc
    values.update({
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT": process_env.get(
            "MEMORY_ATLAS_PRIVATE_DB_CLIENT",
            str(repo / "OpenAIDatabase" / "scripts" / "private_db_client.py"),
        ),
        "MEMORY_ATLAS_SOURCE_REGISTRY": process_env.get(
            "MEMORY_ATLAS_SOURCE_REGISTRY",
            str(repo / "ops" / "memory-atlas" / "source-registry.json"),
        ),
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT": process_env.get(
            "MEMORY_ATLAS_PUBLIC_SNAPSHOT",
            str(repo / "MemoryAtlas" / "public" / "memory_atlas.json"),
        ),
        "MEMORY_ATLAS_EXTERNAL_ORIGIN": process_env.get(
            "MEMORY_ATLAS_EXTERNAL_ORIGIN",
            values.get("MEMORY_ATLAS_EXTERNAL_ORIGIN", "https://memoryatlas.linzezhang.com"),
        ),
        "MEMORY_ATLAS_SOURCE_HOST_ID": process_env.get(
            "MEMORY_ATLAS_SOURCE_HOST_ID",
            values.get("MEMORY_ATLAS_SOURCE_HOST_ID", "mac-codex-source"),
        ),
        "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS": process_env.get(
            "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS",
            str(repo / "OpenAIDatabase" / "data"),
        ),
        "MEMORY_ATLAS_PRIVATE_RELEASE_BACKUP_ENABLED": "1",
        "MEMORY_ATLAS_CAPTURE_STORAGE_MODE": "GITHUB_RELEASE_ONLY",
        "MEMORY_ATLAS_PRIVATE_RELEASE_POLICY": str(
            repo / "OpenAIDatabase" / "config" / "storage" / "private_encrypted_backup_policy.json"
        ),
        "MEMORY_ATLAS_PUBLIC_RELEASE_POLICY": str(
            repo / "OpenAIDatabase" / "config" / "storage" / "public_encrypted_backup_policy.json"
        ),
    })
    if linked_protected_root:
        values["MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS"] = process_env.get(
            "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS",
            str(linked_protected_root / "memory-atlas-evidence-adapters"),
        )
    protected_python = env_path.resolve().parent / "memory-atlas-venv" / "bin" / "python"
    configured_python = process_env.get("MEMORY_ATLAS_SOURCE_PYTHON", "").strip()
    python_executable = configured_python or (str(protected_python) if protected_python.is_file() else sys.executable)
    command = [python_executable, "-B", "-m", "OpenAIDatabase.scripts.memory_atlas_private", "capture"]
    temporary_root = Path(tempfile.gettempdir()).resolve()
    stale_cleaned = cleanup_stale_run_dirs(temporary_root)
    run_root = Path(tempfile.mkdtemp(prefix=TEMP_PREFIX, dir=temporary_root))
    run_root.chmod(0o700)
    (run_root / "tmp").mkdir(mode=0o700)
    env = values.copy()
    env.update(process_env)
    env.update({
        "TMPDIR": str(run_root / "tmp"),
        "MEMORY_ATLAS_RUNTIME_DIR": str(incremental_state_dir),
        "MEMORY_ATLAS_WORK_DIR": str(run_root / "work"),
        "MEMORY_ATLAS_WEB_DATA_DIR": str(run_root / "web"),
        "MEMORY_ATLAS_PRIVATE_RELEASE_BACKUP_ENABLED": "1",
        "MEMORY_ATLAS_CAPTURE_STORAGE_MODE": "GITHUB_RELEASE_ONLY",
        "MEMORY_ATLAS_PRIVATE_RELEASE_POLICY": str(
            repo / "OpenAIDatabase" / "config" / "storage" / "private_encrypted_backup_policy.json"
        ),
        "MEMORY_ATLAS_PUBLIC_RELEASE_POLICY": str(
            repo / "OpenAIDatabase" / "config" / "storage" / "public_encrypted_backup_policy.json"
        ),
    })
    child: dict[str, Any] = {}
    returncode = 1
    failure_code = "capture_not_started"
    child_stderr = ""
    child_failure_code = ""
    try:
        completed = _run_capture(command, cwd=repo, env=env)
        returncode = completed.returncode
        child_stderr = completed.stderr
        child = _child_payload(completed.stdout)
        failure_code = "" if returncode == 0 else "capture_command_failed"
    except Exception as exc:
        failure_code = (
            str(exc)
            if str(exc) in {"capture_result_json_missing", "capture_result_json_invalid"}
            else f"entrypoint_exception_{exc.__class__.__name__}"
        )
        if failure_code == "capture_result_json_missing":
            child_failure_code = _safe_child_failure_code(returncode, child_stderr)
    finally:
        cleanup_error = False
        if _is_owned_temp(run_root, temporary_root):
            try:
                shutil.rmtree(run_root)
            except OSError:
                cleanup_error = True
        capture_lock.close()
        cleanup_pass = not cleanup_error and not run_root.exists()
    state = str(child.get("state", "FAILED"))
    succeeded = returncode == 0 and state == "SUCCEEDED" and cleanup_pass
    result = {
        "schema_version": "memory_atlas.daily_backup_entry_result.v1",
        "state": "SUCCEEDED" if succeeded else "FAILED",
        "child_returncode": returncode,
        "run_id": child.get("run_id"),
        "bytes_discovered": child.get("bytes_discovered"),
        "bytes_uploaded": child.get("bytes_uploaded"),
        "objects": child.get("objects"),
        "readback_verified_objects": child.get("readback_verified_objects"),
        "outbox": child.get("outbox"),
        "source_coverage": _public_safe_source_coverage(child.get("source_coverage")),
        "github_private_release_backup": child.get("github_private_release_backup"),
        "private_fact_backup": child.get("private_fact_backup"),
        "github_canonical_backup": child.get("github_canonical_backup"),
        "r2": child.get("r2"),
        "local_cleanup": {
            "state": "PASS" if cleanup_pass else "FAIL",
            "current_run_temp_removed": cleanup_pass,
            "current_run_remaining_paths": 0 if cleanup_pass else 1,
            "stale_owned_run_dirs_cleaned": stale_cleaned,
        },
    }
    if not succeeded:
        result["failure_code"] = failure_code or f"child_state_{state.lower()}"
    if child_failure_code:
        result["child_failure_code"] = child_failure_code
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))
    raise SystemExit(0 if succeeded else 1)


if __name__ == "__main__":
    main(sys.argv[1:])
