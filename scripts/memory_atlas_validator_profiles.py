#!/usr/bin/env python3
"""Run the four stable Memory Atlas validation profiles."""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import stat
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "memory_atlas.validator_profiles.v1_2_1_s04_p3_t1"
RESULT_SCHEMA_VERSION = "memory_atlas.validator_profile_result.v1_2_1_s04_p3_t1"
PROFILE_IDS = ("fast", "sync", "ui", "release")
DEFAULT_CONFIG_RELATIVE_PATH = Path("config/memory_atlas_validator_profiles.json")
MAX_CONFIG_BYTES = 64 * 1024
MAX_OUTPUT_CHARS_LIMIT = 64 * 1024
MAX_STEP_TIMEOUT_SECONDS = 7200
_CONFIG_KEYS = {
    "schema_version",
    "result_schema_version",
    "public_profiles",
    "max_output_chars_per_stream",
    "profiles",
}
_PROFILE_KEYS = {"description_zh", "steps"}
_STEP_KEYS = {"id", "command", "cwd", "timeout_seconds", "critical"}
_CWD_IDS = {"worktree", "database", "app"}
_STEP_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,63}$")
_AUDITED_STEP_POLICIES: dict[tuple[str, str], tuple[str, tuple[str, ...]]] = {
    ("fast", "python_core"): (
        "database",
        (
            "@python",
            "-B",
            "-m",
            "unittest",
            "tests.test_memory_atlas_validator_profiles",
            "tests.test_atlasctl_modular_cli",
            "tests.test_atlasctl_runtime_core",
            "tests.test_atlasctl_script_consolidation",
            "tests.test_memory_atlas_test_value_audit",
            "tests.test_memory_atlas_legacy_command_migrations",
            "tests.test_memory_atlas_raw_isolation",
            "tests.test_memory_atlas_push_size_guard",
            "-q",
        ),
    ),
    ("fast", "raw_isolation"): (
        "database",
        ("@python", "scripts/atlasctl.py", "audit", "--check", "raw-isolation"),
    ),
    ("fast", "push_size_guard"): (
        "database",
        ("@python", "scripts/atlasctl.py", "audit", "--check", "push-size", "--push-scope", "staged"),
    ),
    ("fast", "frontend_typecheck"): ("app", ("npm", "run", "lint")),
    ("fast", "feature_structure"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_1_s04_p1_t1_structure.mjs"),
    ),
    ("fast", "mounted_paths"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_1_s04_p1_t2_mounts.mjs"),
    ),
    ("sync", "sync_unit_tests"): (
        "database",
        (
            "@python",
            "-B",
            "-m",
            "unittest",
            "tests.test_s03p3_raw_manifest",
            "tests.test_s04p1_chatgpt_sync",
            "tests.test_s04p2_codex_agent_sync",
            "tests.test_s04p3_github_backup",
            "tests.test_memory_atlas_credential_exclusion",
            "tests.test_memory_atlas_r7_public_raw",
            "tests.test_memory_atlas_r7_raw_integrity",
            "tests.test_memory_atlas_source_registry",
            "tests.test_memory_atlas_codex_source_discovery",
            "tests.test_memory_atlas_codex_public_raw_archive",
            "tests.test_memory_atlas_codex_sync_state",
            "tests.test_memory_atlas_codex_derived",
            "tests.test_memory_atlas_codex_push_main",
            "tests.test_memory_atlas_public_raw_layout",
            "tests.test_memory_atlas_raw_ledger",
            "tests.test_memory_atlas_archive_chunking",
            "tests.test_memory_atlas_archive_restore",
            "tests.test_memory_atlas_raw_contract_fixtures",
            "-q",
        ),
    ),
    ("sync", "public_raw_layout"): (
        "database",
        ("@python", "scripts/atlasctl.py", "audit", "--check", "public-raw-layout"),
    ),
    ("sync", "sync_chatgpt_dry_run"): (
        "database",
        ("@python", "scripts/atlasctl.py", "sync", "--source", "chatgpt", "--dry-run"),
    ),
    ("sync", "sync_codex_dry_run"): (
        "database",
        ("@python", "scripts/atlasctl.py", "sync", "--source", "codex", "--dry-run"),
    ),
    ("sync", "sync_future_agent_dry_run"): (
        "database",
        ("@python", "scripts/atlasctl.py", "sync", "--source", "future-agent", "--dry-run"),
    ),
    ("sync", "codex_public_raw_archive"): (
        "database",
        (
            "@python",
            "scripts/atlasctl.py",
            "audit",
            "--check",
            "codex-public-raw-archive",
            "--archive-id",
            "codex-public-raw-20260715t1300z",
        ),
    ),
    ("sync", "codex_sync_state"): (
        "database",
        (
            "@python",
            "scripts/atlasctl.py",
            "audit",
            "--check",
            "codex-sync-state",
            "--archive-id",
            "codex-incremental-20260715t180600z",
        ),
    ),
    ("sync", "codex_derived"): (
        "database",
        (
            "@python",
            "scripts/atlasctl.py",
            "analyze",
            "--stage",
            "codex-derived",
            "--dry-run",
        ),
    ),
    ("sync", "raw_append_only"): (
        "database",
        ("@python", "scripts/raw_archive_manifest.py", "audit", "--database-dir", "."),
    ),
    ("sync", "credential_scan"): (
        "database",
        ("@python", "scripts/privacy_guard.py", "--database-dir", ".", "--scan-only"),
    ),
    ("ui", "frontend_build"): ("app", ("npm", "run", "build")),
    ("ui", "public_raw_build_isolation"): (
        "database",
        (
            "@python",
            "scripts/atlasctl.py",
            "audit",
            "--check",
            "raw-isolation",
            "--require-built-dist",
        ),
    ),
    ("ui", "semantic_readability"): (
        "database",
        ("@python", "scripts/atlasctl.py", "audit", "--check", "chinese-ux"),
    ),
    ("ui", "home_multiviewport"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_home_multiviewport.cjs"),
    ),
    ("ui", "visual_models"): (
        "app",
        (
            "node",
            "--experimental-strip-types",
            "scripts/validate_memory_atlas_v1_2_visual_models.mjs",
        ),
    ),
    ("ui", "visual_workflows"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_visual_workflows.cjs"),
    ),
    ("ui", "command_workflows"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_command_workflows.cjs"),
    ),
    ("ui", "proposal_e2e"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_proposal_e2e.cjs"),
    ),
    ("ui", "owner_daily_e2e"): (
        "app",
        ("node", "scripts/validate_memory_atlas_v1_2_owner_daily_e2e.cjs"),
    ),
    ("ui", "canvas_visual"): (
        "app",
        ("node", "scripts/validate_stage7_visual_acceptance.cjs"),
    ),
    ("ui", "canvas_performance"): (
        "app",
        ("node", "scripts/validate_stage7_performance_acceptance.cjs"),
    ),
    ("ui", "privacy_accessibility"): (
        "app",
        ("node", "scripts/validate_stage7_privacy_accessibility.cjs"),
    ),
    ("ui", "obsidian_graph"): (
        "app",
        ("node", "scripts/validate_stage9_obsidian_iteration.cjs"),
    ),
    ("ui", "visual_semantics"): (
        "app",
        ("node", "scripts/validate_stage9_visual_semantics.cjs"),
    ),
    ("release", "final_audit"): (
        "database",
        ("@python", "scripts/atlasctl.py", "audit"),
    ),
}


class ValidatorProfileConfigError(ValueError):
    """Raised when the validation profile contract cannot be trusted."""


@dataclass(frozen=True)
class ValidatorStep:
    step_id: str
    command: tuple[str, ...]
    cwd: str
    timeout_seconds: int
    critical: bool


@dataclass(frozen=True)
class ValidatorProfile:
    profile_id: str
    description_zh: str
    steps: tuple[ValidatorStep, ...]


@dataclass(frozen=True)
class ValidatorProfileConfig:
    schema_version: str
    result_schema_version: str
    public_profiles: tuple[str, ...]
    max_output_chars_per_stream: int
    profiles: dict[str, ValidatorProfile]
    source_path: Path
    commands_audited: bool = False

    @classmethod
    def from_mapping(cls, payload: object, source_path: Path) -> "ValidatorProfileConfig":
        if not isinstance(payload, dict) or set(payload) != _CONFIG_KEYS:
            raise ValidatorProfileConfigError("validator profile config keys do not match the schema")
        if payload["schema_version"] != SCHEMA_VERSION:
            raise ValidatorProfileConfigError("validator profile schema version is unsupported")
        if payload["result_schema_version"] != RESULT_SCHEMA_VERSION:
            raise ValidatorProfileConfigError("validator profile result schema version is unsupported")
        if payload["public_profiles"] != list(PROFILE_IDS):
            raise ValidatorProfileConfigError("public profile order must be fast, sync, ui, release")
        max_output_chars = payload["max_output_chars_per_stream"]
        if type(max_output_chars) is not int or not 1 <= max_output_chars <= MAX_OUTPUT_CHARS_LIMIT:
            raise ValidatorProfileConfigError("max_output_chars_per_stream is outside the supported range")
        profiles_payload = payload["profiles"]
        if not isinstance(profiles_payload, dict) or tuple(profiles_payload) != PROFILE_IDS:
            raise ValidatorProfileConfigError("profiles must contain fast, sync, ui and release in order")

        profiles: dict[str, ValidatorProfile] = {}
        all_step_ids: set[str] = set()
        for profile_id in PROFILE_IDS:
            profile_payload = profiles_payload[profile_id]
            if not isinstance(profile_payload, dict) or set(profile_payload) != _PROFILE_KEYS:
                raise ValidatorProfileConfigError(f"profile {profile_id} keys do not match the schema")
            description = profile_payload["description_zh"]
            if not isinstance(description, str) or not description.strip() or len(description) > 240:
                raise ValidatorProfileConfigError(f"profile {profile_id} description_zh is invalid")
            steps_payload = profile_payload["steps"]
            if not isinstance(steps_payload, list) or not 1 <= len(steps_payload) <= 32:
                raise ValidatorProfileConfigError(f"profile {profile_id} steps are invalid")
            steps: list[ValidatorStep] = []
            for step_payload in steps_payload:
                if not isinstance(step_payload, dict) or set(step_payload) != _STEP_KEYS:
                    raise ValidatorProfileConfigError(f"profile {profile_id} step keys do not match the schema")
                step_id = step_payload["id"]
                if not isinstance(step_id, str) or not _STEP_ID_PATTERN.fullmatch(step_id):
                    raise ValidatorProfileConfigError(f"profile {profile_id} step id is invalid")
                if step_id in all_step_ids:
                    raise ValidatorProfileConfigError(f"validator step id is duplicated: {step_id}")
                all_step_ids.add(step_id)
                command = step_payload["command"]
                if (
                    not isinstance(command, list)
                    or not 1 <= len(command) <= 64
                    or not all(isinstance(value, str) and 0 < len(value) <= 2048 for value in command)
                ):
                    raise ValidatorProfileConfigError(f"profile {profile_id} step {step_id} command is invalid")
                if command[0].startswith("@") and command[0] != "@python":
                    raise ValidatorProfileConfigError(f"profile {profile_id} step {step_id} command token is unsupported")
                cwd = step_payload["cwd"]
                if cwd not in _CWD_IDS:
                    raise ValidatorProfileConfigError(f"profile {profile_id} step {step_id} cwd is unsupported")
                timeout = step_payload["timeout_seconds"]
                if type(timeout) is not int or not 1 <= timeout <= MAX_STEP_TIMEOUT_SECONDS:
                    raise ValidatorProfileConfigError(f"profile {profile_id} step {step_id} timeout is invalid")
                if step_payload["critical"] is not True:
                    raise ValidatorProfileConfigError(f"profile {profile_id} step {step_id} must remain critical")
                steps.append(
                    ValidatorStep(
                        step_id=step_id,
                        command=tuple(command),
                        cwd=cwd,
                        timeout_seconds=timeout,
                        critical=True,
                    )
                )
            profiles[profile_id] = ValidatorProfile(
                profile_id=profile_id,
                description_zh=description,
                steps=tuple(steps),
            )
        return cls(
            schema_version=SCHEMA_VERSION,
            result_schema_version=RESULT_SCHEMA_VERSION,
            public_profiles=PROFILE_IDS,
            max_output_chars_per_stream=max_output_chars,
            profiles=profiles,
            source_path=source_path,
        )


def _validate_audited_step_policies(config: ValidatorProfileConfig) -> None:
    actual = {
        (profile_id, step.step_id): (step.cwd, step.command)
        for profile_id, profile in config.profiles.items()
        for step in profile.steps
    }
    if actual != _AUDITED_STEP_POLICIES:
        raise ValidatorProfileConfigError(
            "validator profile commands do not match the audited safety policy"
        )


def _read_config_bytes(path: Path) -> bytes:
    if path.is_symlink():
        raise ValidatorProfileConfigError("validator profile config cannot be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValidatorProfileConfigError("validator profile config is unavailable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValidatorProfileConfigError("validator profile config must be a regular file")
        if metadata.st_size > MAX_CONFIG_BYTES:
            raise ValidatorProfileConfigError("validator profile config exceeds the size limit")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(MAX_CONFIG_BYTES + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > MAX_CONFIG_BYTES:
        raise ValidatorProfileConfigError("validator profile config exceeds the size limit")
    return content


def load_validator_profile_config(
    database_dir: Path,
    path: Path | str | None = None,
) -> ValidatorProfileConfig:
    database_dir = database_dir.expanduser().resolve()
    source_path = (
        Path(path).expanduser().absolute()
        if path is not None
        else database_dir / DEFAULT_CONFIG_RELATIVE_PATH
    )
    try:
        payload = json.loads(_read_config_bytes(source_path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidatorProfileConfigError("validator profile config is not valid UTF-8 JSON") from exc
    config = ValidatorProfileConfig.from_mapping(payload, source_path)
    _validate_audited_step_policies(config)
    return replace(config, commands_audited=True)


def _working_directories(database_dir: Path) -> dict[str, Path]:
    database = database_dir.expanduser().resolve()
    roots = {
        "worktree": database.parent,
        "database": database,
        "app": database / "apps/memory-atlas",
    }
    for cwd_id, path in roots.items():
        if path.is_symlink() or not path.is_dir():
            raise ValidatorProfileConfigError(f"validator working directory is unavailable: {cwd_id}")
    return roots


def _resolved_command(command: tuple[str, ...]) -> list[str]:
    values = list(command)
    if values[0] == "@python":
        values[0] = sys.executable
    return values


def build_profile_plan(
    config: ValidatorProfileConfig,
    profile_name: str,
    database_dir: Path,
) -> list[dict[str, Any]]:
    if profile_name not in config.public_profiles:
        raise ValidatorProfileConfigError("unknown profile; expected fast, sync, ui or release")
    roots = _working_directories(database_dir)
    profile = config.profiles[profile_name]
    return [
        {
            "id": step.step_id,
            "command": _resolved_command(step.command),
            "cwd": str(roots[step.cwd]),
            "cwd_id": step.cwd,
            "timeout_seconds": step.timeout_seconds,
            "critical": step.critical,
        }
        for step in profile.steps
    ]


class _BoundedByteTail:
    """Thread-safe UTF-8 tail that never retains a child's full output."""

    def __init__(self, max_chars: int) -> None:
        self._max_chars = max_chars
        self._max_bytes = max(1, max_chars * 4)
        self._buffer = bytearray()
        self._lock = threading.Lock()

    @property
    def buffered_bytes(self) -> int:
        with self._lock:
            return len(self._buffer)

    def append(self, chunk: bytes) -> None:
        if not chunk:
            return
        with self._lock:
            if len(chunk) >= self._max_bytes:
                self._buffer[:] = chunk[-self._max_bytes :]
                return
            self._buffer.extend(chunk)
            overflow = len(self._buffer) - self._max_bytes
            if overflow > 0:
                del self._buffer[:overflow]

    def text(self) -> str:
        with self._lock:
            value = bytes(self._buffer)
        return value.decode("utf-8", errors="replace")[-self._max_chars :]


def _drain_stream(stream: Any, tail: _BoundedByteTail) -> None:
    try:
        while True:
            chunk = stream.read(8192)
            if not chunk:
                return
            tail.append(chunk)
    except (OSError, ValueError):
        return
    finally:
        try:
            stream.close()
        except (OSError, ValueError):
            pass


@dataclass
class _ChildOutputCapture:
    stdout_tail: _BoundedByteTail
    stderr_tail: _BoundedByteTail
    streams: tuple[Any, Any]
    threads: tuple[threading.Thread, threading.Thread]

    def finish(self) -> tuple[str, str]:
        for thread in self.threads:
            thread.join(timeout=5)
        if any(thread.is_alive() for thread in self.threads):
            for stream in self.streams:
                try:
                    stream.close()
                except (OSError, ValueError):
                    pass
            for thread in self.threads:
                thread.join(timeout=1)
        return self.stdout_tail.text(), self.stderr_tail.text()


def _start_output_capture(
    process: subprocess.Popen[bytes],
    max_chars: int,
) -> _ChildOutputCapture:
    if process.stdout is None or process.stderr is None:
        raise RuntimeError("validator child output pipes are unavailable")
    stdout_tail = _BoundedByteTail(max_chars)
    stderr_tail = _BoundedByteTail(max_chars)
    streams = (process.stdout, process.stderr)
    threads = (
        threading.Thread(
            target=_drain_stream,
            args=(process.stdout, stdout_tail),
            daemon=True,
            name=f"validator-stdout-{process.pid}",
        ),
        threading.Thread(
            target=_drain_stream,
            args=(process.stderr, stderr_tail),
            daemon=True,
            name=f"validator-stderr-{process.pid}",
        ),
    )
    for thread in threads:
        thread.start()
    return _ChildOutputCapture(stdout_tail, stderr_tail, streams, threads)


def _start_child(command: list[str], cwd: str) -> subprocess.Popen[bytes]:
    creationflags = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0) if os.name == "nt" else 0
    return subprocess.Popen(
        command,
        cwd=cwd,
        text=False,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        start_new_session=os.name == "posix",
        creationflags=creationflags,
    )


def _record_cleanup_error(errors: list[str], exc: OSError) -> None:
    if isinstance(exc, ProcessLookupError):
        return
    error_name = type(exc).__name__
    if error_name not in errors:
        errors.append(error_name)


def _signal_parent(process: subprocess.Popen[bytes], errors: list[str], *, kill: bool) -> None:
    try:
        process.kill() if kill else process.terminate()
    except OSError as exc:
        _record_cleanup_error(errors, exc)


def _terminate_process_tree(process: subprocess.Popen[bytes]) -> str:
    errors: list[str] = []
    if os.name == "posix":
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except OSError as exc:
            _record_cleanup_error(errors, exc)
            _signal_parent(process, errors, kill=False)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        except OSError as exc:
            _record_cleanup_error(errors, exc)
        process_group_exists = False
        try:
            os.killpg(process.pid, 0)
            process_group_exists = True
        except OSError as exc:
            _record_cleanup_error(errors, exc)
        if process_group_exists:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError as exc:
                _record_cleanup_error(errors, exc)
                _signal_parent(process, errors, kill=True)
        elif process.poll() is None:
            _signal_parent(process, errors, kill=True)
    elif os.name == "nt":
        try:
            completed = subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                text=True,
                capture_output=True,
                check=False,
                shell=False,
                timeout=5,
            )
            if completed.returncode != 0:
                _signal_parent(process, errors, kill=True)
        except subprocess.TimeoutExpired:
            errors.append("CleanupTimeout")
            _signal_parent(process, errors, kill=True)
        except OSError as exc:
            _record_cleanup_error(errors, exc)
            _signal_parent(process, errors, kill=True)
    else:
        _signal_parent(process, errors, kill=True)
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        errors.append("CleanupTimeout")
        _signal_parent(process, errors, kill=True)
        try:
            process.wait(timeout=1)
        except subprocess.TimeoutExpired:
            pass
        except OSError as exc:
            _record_cleanup_error(errors, exc)
    except OSError as exc:
        _record_cleanup_error(errors, exc)
    return ",".join(dict.fromkeys(errors))


def _with_cleanup_warning(stderr: str, warning: str, limit: int) -> str:
    if not warning:
        return stderr
    separator = "\n" if stderr and not stderr.endswith("\n") else ""
    return f"{stderr}{separator}process cleanup warning: {warning}"[-limit:]


def _base_result(
    config: ValidatorProfileConfig,
    profile_name: str,
    *,
    status: str,
    step_count: int,
    duration_ms: int,
) -> dict[str, Any]:
    return {
        "schema_version": config.result_schema_version,
        "profile": profile_name,
        "status": status,
        "step_count": step_count,
        "duration_ms": duration_ms,
        "safety": {
            "shell": False,
            "commands_audited": config.commands_audited,
            "remote_push": False if config.commands_audited else None,
            "raw_mutation": False if config.commands_audited else None,
        },
    }


def run_validator_profile(
    config: ValidatorProfileConfig,
    profile_name: str,
    database_dir: Path,
    *,
    plan_only: bool = False,
) -> dict[str, Any]:
    started = time.monotonic()
    plan = build_profile_plan(config, profile_name, database_dir)
    if plan_only:
        result = _base_result(
            config,
            profile_name,
            status="PLAN",
            step_count=len(plan),
            duration_ms=int((time.monotonic() - started) * 1000),
        )
        result.update(
            {
                "planned_count": len(plan),
                "completed_count": 0,
                "failed_count": 0,
                "skipped_critical_count": 0,
                "steps": [
                    {
                        "id": step["id"],
                        "status": "PLANNED",
                        "cwd": step["cwd_id"],
                        "timeout_seconds": step["timeout_seconds"],
                        "critical": True,
                    }
                    for step in plan
                ],
            }
        )
        return result

    executed: list[dict[str, Any]] = []
    completed_count = 0
    failed_count = 0
    for index, step in enumerate(plan):
        step_started = time.monotonic()
        try:
            child = _start_child(step["command"], step["cwd"])
        except OSError as exc:
            executed.append(
                {
                    "id": step["id"],
                    "status": "LAUNCH_ERROR",
                    "exit_code": None,
                    "duration_ms": int((time.monotonic() - step_started) * 1000),
                    "stderr_tail": f"{type(exc).__name__}: configured command could not be started",
                }
            )
            failed_count = 1
            skipped_count = len(plan) - index - 1
            break
        capture = _start_output_capture(child, config.max_output_chars_per_stream)
        try:
            child.wait(timeout=step["timeout_seconds"])
        except subprocess.TimeoutExpired:
            cleanup_warning = _terminate_process_tree(child)
            stdout, stderr = capture.finish()
            stderr = _with_cleanup_warning(
                stderr,
                cleanup_warning,
                config.max_output_chars_per_stream,
            )
            executed.append(
                {
                    "id": step["id"],
                    "status": "TIMEOUT",
                    "exit_code": None,
                    "duration_ms": int((time.monotonic() - step_started) * 1000),
                    "stdout_tail": stdout,
                    "stderr_tail": stderr,
                }
            )
            failed_count = 1
            skipped_count = len(plan) - index - 1
            break
        stdout, stderr = capture.finish()
        if child.returncode == 0:
            completed_count += 1
            executed.append(
                {
                    "id": step["id"],
                    "status": "PASS",
                    "exit_code": 0,
                    "duration_ms": int((time.monotonic() - step_started) * 1000),
                }
            )
            continue
        executed.append(
            {
                "id": step["id"],
                "status": "FAIL",
                "exit_code": child.returncode,
                "duration_ms": int((time.monotonic() - step_started) * 1000),
                "stdout_tail": stdout,
                "stderr_tail": stderr,
            }
        )
        failed_count = 1
        skipped_count = len(plan) - index - 1
        break
    else:
        skipped_count = 0

    status = "PASS" if failed_count == 0 else "FAIL"
    result = _base_result(
        config,
        profile_name,
        status=status,
        step_count=len(plan),
        duration_ms=int((time.monotonic() - started) * 1000),
    )
    result.update(
        {
            "completed_count": completed_count,
            "failed_count": failed_count,
            "skipped_critical_count": skipped_count,
            "steps": executed,
        }
    )
    return result


def _rejected_result(reason: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "REJECTED",
        "error_code": "VALIDATOR_PROFILE_INVALID",
        "reason": reason,
    }


def _write_diagnostics(result: dict[str, Any]) -> None:
    profile = result.get("profile", "unparsed")
    for step in result.get("steps", []):
        status = step.get("status", "UNKNOWN")
        step_id = step.get("id", "unknown")
        duration = step.get("duration_ms", 0)
        print(f"[{profile}:{step_id}] {status} ({duration} ms)", file=sys.stderr)
        if status in {"FAIL", "TIMEOUT", "LAUNCH_ERROR"}:
            if step.get("stdout_tail"):
                print(step["stdout_tail"], file=sys.stderr, end="" if step["stdout_tail"].endswith("\n") else "\n")
            if step.get("stderr_tail"):
                print(step["stderr_tail"], file=sys.stderr, end="" if step["stderr_tail"].endswith("\n") else "\n")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a stable Memory Atlas validator profile.")
    parser.add_argument("--profile", required=True)
    parser.add_argument("--plan", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = Path(__file__).resolve().parents[1]
    try:
        config = load_validator_profile_config(database_dir)
        result = run_validator_profile(
            config,
            args.profile,
            database_dir,
            plan_only=args.plan,
        )
    except ValidatorProfileConfigError as exc:
        print(json.dumps(_rejected_result(str(exc)), ensure_ascii=False, sort_keys=True))
        return 2
    _write_diagnostics(result)
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] in {"PASS", "PLAN"} else 1


if __name__ == "__main__":
    raise SystemExit(main())


__all__ = (
    "PROFILE_IDS",
    "RESULT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "ValidatorProfileConfig",
    "ValidatorProfileConfigError",
    "build_profile_plan",
    "load_validator_profile_config",
    "main",
    "run_validator_profile",
)
