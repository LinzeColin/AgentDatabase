"""Coalescing local Codex scheduler profile for S07-P3-T2."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import platform
import re
import secrets
import stat
import sys
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from github_backup import find_git_root

from .codex_push_main import (
    ACCEPTANCE_ID as PUSH_MAIN_ACCEPTANCE_ID,
    RESULT_SCHEMA_VERSION as PUSH_MAIN_RESULT_SCHEMA_VERSION,
    TASK_ID as PUSH_MAIN_TASK_ID,
    execute_codex_push_main,
    generated_archive_id,
)
from .codex_source_discovery import build_codex_source_discovery


PROFILE_PATH = Path("config/data_sources/codex_scheduler_profile.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_scheduler_profile.v1_2_1_s07_p3_t2.json"
)
PROFILE_SCHEMA_VERSION = "memory_atlas.codex_scheduler_profile.v1_2_1_s07_p3_t2"
MODEL_SCHEMA_VERSION = "memory_atlas.codex_scheduler_model.v1_2_1_s07_p3_t2"
STATE_SCHEMA_VERSION = "memory_atlas.codex_scheduler_state.v1_2_1_s07_p3_t2"
RESULT_SCHEMA_VERSION = "memory_atlas.codex_scheduler_result.v1_2_1_s07_p3_t2"
TASK_ID = "S07-P3-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P3-T2"
PROFILE_ID = "codex-scheduler"
STATE_FILENAME = "codex_scheduler_state.json"
LOCK_FILENAME = "codex_scheduler.lock"
MAX_PROFILE_BYTES = 128 * 1024
MAX_STATE_BYTES = 64 * 1024
OWNER_RUN_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")
SHA256_PATTERN = re.compile(r"^[a-f0-9]{64}$")

SCHEDULE_INTERVAL_SECONDS = 900
QUIET_PERIOD_SECONDS = 300
MAX_PENDING_SECONDS = 1800
MINIMUM_SUCCESS_INTERVAL_SECONDS = 3600
SAME_METADATA_OBSERVATIONS_REQUIRED = 2
ATTEMPTED_OWNER_RUN_HISTORY_LIMIT = 64

EXPECTED_PROFILE: dict[str, Any] = {
    "schema_version": PROFILE_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "profile_id": PROFILE_ID,
    "source_id": "codex",
    "timezone": "Australia/Sydney",
    "entrypoint": {
        "command": "run --profile codex-scheduler",
        "runner": "scripts/memory_atlas_cli/codex_scheduler.py",
        "push_main_command": "sync codex --push-main",
        "shell": False,
    },
    "schedule": {
        "frequency": "every_15_minutes",
        "interval_seconds": SCHEDULE_INTERVAL_SECONDS,
        "activation": "authorized_local_scheduler_manual_install",
        "installed_by_default": False,
    },
    "coalescing": {
        "quiet_period_seconds": QUIET_PERIOD_SECONDS,
        "max_pending_seconds": MAX_PENDING_SECONDS,
        "minimum_success_interval_seconds": MINIMUM_SUCCESS_INTERVAL_SECONDS,
        "same_metadata_observations_required": SAME_METADATA_OBSERVATIONS_REQUIRED,
        "state_location": "machine_local_outside_repository_and_codex_source",
    },
    "owner_run": {
        "id_strategy": "utc_interval_bucket",
        "sync_invocation_limit": 1,
        "push_attempt_limit": 1,
        "lock_mode": "nonblocking_exclusive",
        "active_attempt_persisted_before_sync": True,
        "duplicate_owner_run": "no_second_invocation",
        "attempted_owner_run_history_limit": ATTEMPTED_OWNER_RUN_HISTORY_LIMIT,
    },
    "state": {
        "schema_version": STATE_SCHEMA_VERSION,
        "filename": STATE_FILENAME,
        "lock_filename": LOCK_FILENAME,
        "contains_source_content": False,
        "contains_absolute_paths": False,
        "file_mode_octal": "0600",
        "atomic_replace_and_directory_fsync": True,
    },
    "safety": {
        "source_metadata_only_before_sync": True,
        "source_mutation": False,
        "automatic_scheduler_install": False,
        "push_main_invocation_limit_per_owner_run": 1,
        "push_attempt_limit_per_owner_run": 1,
        "force": False,
        "fetch": False,
        "branch_creation": False,
        "pull_request": False,
        "merge": False,
        "rebase": False,
        "automatic_retry_after_git_effect": False,
    },
    "phase_boundary": {
        "scheduler_profile_implemented": True,
        "scheduler_not_installed_or_enabled": True,
        "full_restore_proof_not_claimed": True,
        "next_task": "S07-P3-T3",
    },
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-008",
    "formula_id": "FORM-008",
    "purpose": (
        "Merge short-lived Codex source changes into one eligible owner run while "
        "preserving the S07-P3-T1 one-command and one-push-attempt boundary."
    ),
    "parameters": {
        "timezone": "Australia/Sydney",
        "schedule_interval_seconds": SCHEDULE_INTERVAL_SECONDS,
        "quiet_period_seconds": QUIET_PERIOD_SECONDS,
        "max_pending_seconds": MAX_PENDING_SECONDS,
        "minimum_success_interval_seconds": MINIMUM_SUCCESS_INTERVAL_SECONDS,
        "same_metadata_observations_required": SAME_METADATA_OBSERVATIONS_REQUIRED,
        "sync_invocation_limit_per_owner_run": 1,
        "push_attempt_limit_per_owner_run": 1,
        "lock_acquisition_wait_seconds": 0,
        "attempted_owner_run_history_limit": ATTEMPTED_OWNER_RUN_HISTORY_LIMIT,
    },
    "formula": (
        "eligible = source_changed_since_last_success AND "
        "((same_metadata_observations >= 2 AND quiet_elapsed >= 300) OR pending_elapsed >= 1800) AND "
        "success_elapsed >= 3600; sync_invocations_per_owner_run <= 1; "
        "push_attempts_per_owner_run <= 1"
    ),
    "parameter_rationale": {
        "schedule_interval_seconds": "Fifteen-minute observations are responsive without treating each file write as a run.",
        "quiet_period_seconds": "Five minutes merges bursty session and log writes before the expensive validated pipeline.",
        "max_pending_seconds": "Thirty minutes bounds postponement under continuing metadata churn; T1 source-stability gates still stop an unsafe run.",
        "minimum_success_interval_seconds": "One hour prevents repeated small successful pushes across adjacent cadence buckets.",
    },
    "failure_semantics": (
        "Profile, state, path, lock, clock, source or child-result uncertainty fails closed. "
        "An incomplete attempt or any failed child with a Git/remote effect requires manual intervention."
    ),
    "calibration_boundary": (
        "The profile is portable configuration and runtime logic only. It does not install or enable an OS scheduler, "
        "perform a production push in S07-P3-T2, or claim the S07-P3-T3 restore proof."
    ),
}


class CodexSchedulerError(RuntimeError):
    """Path-free fail-closed scheduler error."""

    def __init__(self, code: str, *, remote_effect_possible: bool = False):
        super().__init__(code)
        self.code = code
        self.remote_effect_possible = remote_effect_possible


SourceProbe = Callable[[Path, Path | None], dict[str, Any]]
PushMainRunner = Callable[..., dict[str, Any]]


def isoformat_utc(value: datetime) -> str:
    if value.tzinfo is None:
        raise CodexSchedulerError("scheduler_clock_not_timezone_aware")
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _parse_utc(value: object, code: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise CodexSchedulerError(code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise CodexSchedulerError(code) from exc
    return parsed.astimezone(timezone.utc)


def _canonical_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _read_bounded_regular_json(path: Path, *, max_bytes: int, code: str) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CodexSchedulerError(f"{code}_unreadable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
            raise CodexSchedulerError(f"{code}_not_bounded_regular_file")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            raw = handle.read(max_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(raw) > max_bytes:
        raise CodexSchedulerError(f"{code}_too_large")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexSchedulerError(f"{code}_invalid_json") from exc
    if not isinstance(payload, dict):
        raise CodexSchedulerError(f"{code}_not_object")
    return payload


def validate_codex_scheduler_profile(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_PROFILE:
        raise CodexSchedulerError("scheduler_profile_drift")
    return copy.deepcopy(payload)


def validate_codex_scheduler_model(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise CodexSchedulerError("scheduler_model_drift")
    return copy.deepcopy(payload)


def load_codex_scheduler_profile(database_dir: Path) -> dict[str, Any]:
    return validate_codex_scheduler_profile(
        _read_bounded_regular_json(
            database_dir.resolve() / PROFILE_PATH,
            max_bytes=MAX_PROFILE_BYTES,
            code="scheduler_profile",
        )
    )


def load_codex_scheduler_model(database_dir: Path) -> dict[str, Any]:
    return validate_codex_scheduler_model(
        _read_bounded_regular_json(
            database_dir.resolve() / MODEL_PARAMETERS_PATH,
            max_bytes=MAX_PROFILE_BYTES,
            code="scheduler_model",
        )
    )


def _is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
        return True
    except ValueError:
        return False


def default_scheduler_state_dir(
    *,
    environ: Mapping[str, str] | None = None,
    home: Path | None = None,
) -> Path:
    environment = os.environ if environ is None else environ
    configured = environment.get("MEMORY_ATLAS_CODEX_SCHEDULER_STATE_DIR")
    if configured:
        return Path(configured).expanduser()
    user_home = Path.home() if home is None else home
    if platform.system() == "Darwin":
        return user_home / "Library/Application Support/Memory Atlas/scheduler/codex"
    xdg_state = environment.get("XDG_STATE_HOME")
    root = Path(xdg_state).expanduser() if xdg_state else user_home / ".local/state"
    return root / "memory-atlas/codex-scheduler"


def _codex_source_candidates(codex_home: Path | None) -> list[Path]:
    values: list[Path] = []
    if codex_home is not None:
        values.append(codex_home)
    for name in ("MEMORY_ATLAS_CODEX_HOME", "CODEX_HOME"):
        configured = os.environ.get(name)
        if configured:
            values.append(Path(configured).expanduser())
    values.append(Path.home() / ".codex")
    return values


def _validate_state_dir(
    state_dir: Path,
    database_dir: Path,
    codex_home: Path | None,
) -> Path:
    if not state_dir.is_absolute():
        raise CodexSchedulerError("scheduler_state_path_not_absolute")
    try:
        if state_dir.is_symlink():
            raise CodexSchedulerError("scheduler_state_path_symlink")
        if state_dir.exists() and not state_dir.is_dir():
            raise CodexSchedulerError("scheduler_state_path_not_directory")
        resolved = state_dir.resolve(strict=False)
        database = database_dir.resolve()
    except (OSError, RuntimeError) as exc:
        if isinstance(exc, CodexSchedulerError):
            raise
        raise CodexSchedulerError("scheduler_state_path_invalid") from exc
    if _is_relative_to(resolved, database):
        raise CodexSchedulerError("scheduler_state_inside_database")
    repo_root = find_git_root(database)
    if repo_root is not None and _is_relative_to(resolved, repo_root.resolve()):
        raise CodexSchedulerError("scheduler_state_inside_git_worktree")
    for candidate in _codex_source_candidates(codex_home):
        if not candidate.is_absolute():
            raise CodexSchedulerError("codex_source_path_not_absolute")
        try:
            source_root = candidate.resolve(strict=False)
        except (OSError, RuntimeError):
            continue
        if _is_relative_to(resolved, source_root):
            raise CodexSchedulerError("scheduler_state_inside_codex_source")
    return resolved


def generated_owner_run_id(now: datetime) -> str:
    if now.tzinfo is None:
        raise CodexSchedulerError("scheduler_clock_not_timezone_aware")
    seconds = int(now.astimezone(timezone.utc).timestamp())
    bucket = seconds - (seconds % SCHEDULE_INTERVAL_SECONDS)
    instant = datetime.fromtimestamp(bucket, tz=timezone.utc)
    return f"codex-scheduler-{instant.strftime('%Y%m%dt%H%M%Sz')}"


def _validate_owner_run_id(value: str) -> str:
    if not OWNER_RUN_ID_PATTERN.fullmatch(value):
        raise CodexSchedulerError("owner_run_id_invalid")
    return value


def _initial_state(profile_hash: str) -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "profile_id": PROFILE_ID,
        "profile_sha256": profile_hash,
        "revision": 0,
        "pending": None,
        "last_completed": None,
        "last_attempt": None,
        "active_attempt": None,
        "attempted_owner_run_ids": [],
        "manual_intervention_required": False,
    }


def _validate_digest(value: object, code: str) -> str:
    if not isinstance(value, str) or not SHA256_PATTERN.fullmatch(value):
        raise CodexSchedulerError(code)
    return value


def _validate_pending(value: Any) -> None:
    if value is None:
        return
    keys = {
        "source_metadata_sha256",
        "eligible_file_count",
        "eligible_total_bytes",
        "first_observed_at",
        "last_changed_at",
        "last_observed_at",
        "same_metadata_observation_count",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise CodexSchedulerError("scheduler_state_pending_invalid")
    _validate_digest(value["source_metadata_sha256"], "scheduler_state_pending_invalid")
    for key in ("eligible_file_count", "eligible_total_bytes", "same_metadata_observation_count"):
        if not isinstance(value[key], int) or isinstance(value[key], bool) or value[key] < 0:
            raise CodexSchedulerError("scheduler_state_pending_invalid")
    for key in ("first_observed_at", "last_changed_at", "last_observed_at"):
        _parse_utc(value[key], "scheduler_state_pending_invalid")


def _validate_last_completed(value: Any) -> None:
    if value is None:
        return
    keys = {"source_metadata_sha256", "completed_at", "child_outcome"}
    if not isinstance(value, dict) or set(value) != keys:
        raise CodexSchedulerError("scheduler_state_last_completed_invalid")
    _validate_digest(value["source_metadata_sha256"], "scheduler_state_last_completed_invalid")
    _parse_utc(value["completed_at"], "scheduler_state_last_completed_invalid")
    if not isinstance(value["child_outcome"], str) or not value["child_outcome"]:
        raise CodexSchedulerError("scheduler_state_last_completed_invalid")


def _validate_last_attempt(value: Any) -> None:
    if value is None:
        return
    keys = {
        "owner_run_id",
        "attempted_at",
        "status",
        "child_outcome",
        "push_attempt_count",
        "commit_created",
        "remote_push_attempted",
    }
    if not isinstance(value, dict) or set(value) != keys:
        raise CodexSchedulerError("scheduler_state_last_attempt_invalid")
    _validate_owner_run_id(value["owner_run_id"])
    _parse_utc(value["attempted_at"], "scheduler_state_last_attempt_invalid")
    if value["status"] not in {"PASS", "FAIL_CLOSED"}:
        raise CodexSchedulerError("scheduler_state_last_attempt_invalid")
    if not isinstance(value["child_outcome"], str) or not value["child_outcome"]:
        raise CodexSchedulerError("scheduler_state_last_attempt_invalid")
    if value["push_attempt_count"] not in {0, 1}:
        raise CodexSchedulerError("scheduler_state_last_attempt_invalid")
    if not isinstance(value["commit_created"], bool) or not isinstance(value["remote_push_attempted"], bool):
        raise CodexSchedulerError("scheduler_state_last_attempt_invalid")


def _validate_active_attempt(value: Any) -> None:
    if value is None:
        return
    keys = {"owner_run_id", "started_at", "source_metadata_sha256"}
    if not isinstance(value, dict) or set(value) != keys:
        raise CodexSchedulerError("scheduler_state_active_attempt_invalid")
    _validate_owner_run_id(value["owner_run_id"])
    _parse_utc(value["started_at"], "scheduler_state_active_attempt_invalid")
    _validate_digest(value["source_metadata_sha256"], "scheduler_state_active_attempt_invalid")


def _validate_state(payload: Any, profile_hash: str) -> dict[str, Any]:
    keys = {
        "schema_version",
        "profile_id",
        "profile_sha256",
        "revision",
        "pending",
        "last_completed",
        "last_attempt",
        "active_attempt",
        "attempted_owner_run_ids",
        "manual_intervention_required",
    }
    if not isinstance(payload, dict) or set(payload) != keys:
        raise CodexSchedulerError("scheduler_state_keys_invalid")
    if (
        payload["schema_version"] != STATE_SCHEMA_VERSION
        or payload["profile_id"] != PROFILE_ID
        or payload["profile_sha256"] != profile_hash
    ):
        raise CodexSchedulerError("scheduler_state_identity_invalid")
    if not isinstance(payload["revision"], int) or isinstance(payload["revision"], bool) or payload["revision"] < 0:
        raise CodexSchedulerError("scheduler_state_revision_invalid")
    if not isinstance(payload["manual_intervention_required"], bool):
        raise CodexSchedulerError("scheduler_state_manual_flag_invalid")
    history = payload["attempted_owner_run_ids"]
    if (
        not isinstance(history, list)
        or len(history) > ATTEMPTED_OWNER_RUN_HISTORY_LIMIT
        or len(history) != len(set(history))
    ):
        raise CodexSchedulerError("scheduler_state_owner_run_history_invalid")
    for owner_run_id in history:
        if not isinstance(owner_run_id, str):
            raise CodexSchedulerError("scheduler_state_owner_run_history_invalid")
        _validate_owner_run_id(owner_run_id)
    _validate_pending(payload["pending"])
    _validate_last_completed(payload["last_completed"])
    _validate_last_attempt(payload["last_attempt"])
    _validate_active_attempt(payload["active_attempt"])
    if payload["last_attempt"] and payload["last_attempt"]["owner_run_id"] not in history:
        raise CodexSchedulerError("scheduler_state_owner_run_history_invalid")
    if payload["active_attempt"] and payload["active_attempt"]["owner_run_id"] not in history:
        raise CodexSchedulerError("scheduler_state_owner_run_history_invalid")
    return copy.deepcopy(payload)


def _load_state(state_dir: Path, profile_hash: str) -> dict[str, Any]:
    path = state_dir / STATE_FILENAME
    if not path.exists():
        return _initial_state(profile_hash)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CodexSchedulerError("scheduler_state_unreadable") from exc
    if stat.S_ISLNK(metadata.st_mode):
        raise CodexSchedulerError("scheduler_state_symlink")
    if stat.S_IMODE(metadata.st_mode) & 0o077:
        raise CodexSchedulerError("scheduler_state_permissions_unsafe")
    return _validate_state(
        _read_bounded_regular_json(path, max_bytes=MAX_STATE_BYTES, code="scheduler_state"),
        profile_hash,
    )


def _prepare_state_dir(state_dir: Path) -> None:
    try:
        state_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
        if state_dir.is_symlink() or not state_dir.is_dir():
            raise CodexSchedulerError("scheduler_state_path_invalid")
        os.chmod(state_dir, 0o700)
    except OSError as exc:
        raise CodexSchedulerError("scheduler_state_dir_create_failed") from exc


def _write_state_atomic(state_dir: Path, payload: dict[str, Any]) -> None:
    encoded = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if len(encoded) > MAX_STATE_BYTES:
        raise CodexSchedulerError("scheduler_state_too_large")
    target = state_dir / STATE_FILENAME
    if target.is_symlink():
        raise CodexSchedulerError("scheduler_state_symlink")
    temporary = state_dir / f".{STATE_FILENAME}.{os.getpid()}.{secrets.token_hex(4)}.tmp"
    descriptor = -1
    try:
        descriptor = os.open(
            temporary,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, target)
        os.chmod(target, 0o600)
        directory_fd = os.open(state_dir, os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
    except OSError as exc:
        raise CodexSchedulerError("scheduler_state_write_failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass


class _SchedulerLock:
    def __init__(self, state_dir: Path):
        self.path = state_dir / LOCK_FILENAME
        self.descriptor = -1

    def __enter__(self) -> "_SchedulerLock":
        if self.path.is_symlink():
            raise CodexSchedulerError("scheduler_lock_symlink")
        try:
            self.descriptor = os.open(
                self.path,
                os.O_RDWR | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0),
                0o600,
            )
            metadata = os.fstat(self.descriptor)
            if not stat.S_ISREG(metadata.st_mode):
                raise CodexSchedulerError("scheduler_lock_not_regular")
            os.fchmod(self.descriptor, 0o600)
            fcntl.flock(self.descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            if self.descriptor >= 0:
                os.close(self.descriptor)
                self.descriptor = -1
            raise CodexSchedulerError("scheduler_run_locked") from exc
        except CodexSchedulerError:
            if self.descriptor >= 0:
                os.close(self.descriptor)
                self.descriptor = -1
            raise
        except OSError as exc:
            if self.descriptor >= 0:
                os.close(self.descriptor)
                self.descriptor = -1
            raise CodexSchedulerError("scheduler_lock_failed") from exc
        return self

    def __exit__(self, exc_type, exc, traceback) -> None:
        del exc_type, exc, traceback
        if self.descriptor >= 0:
            try:
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
            finally:
                os.close(self.descriptor)
                self.descriptor = -1


def _observation(source: dict[str, Any]) -> dict[str, Any]:
    digest = _validate_digest(source.get("source_metadata_sha256"), "scheduler_source_observation_invalid")
    count = source.get("eligible_file_count")
    total_bytes = source.get("eligible_total_bytes")
    if (
        not isinstance(count, int)
        or isinstance(count, bool)
        or count <= 0
        or not isinstance(total_bytes, int)
        or isinstance(total_bytes, bool)
        or total_bytes < 0
    ):
        raise CodexSchedulerError("scheduler_source_observation_invalid")
    return {
        "source_metadata_sha256": digest,
        "eligible_file_count": count,
        "eligible_total_bytes": total_bytes,
    }


def _latest_state_time(state: dict[str, Any]) -> datetime | None:
    values: list[datetime] = []
    pending = state["pending"]
    if pending:
        values.extend(
            _parse_utc(pending[key], "scheduler_state_time_invalid")
            for key in ("first_observed_at", "last_changed_at", "last_observed_at")
        )
    completed = state["last_completed"]
    if completed:
        values.append(_parse_utc(completed["completed_at"], "scheduler_state_time_invalid"))
    attempt = state["last_attempt"]
    if attempt:
        values.append(_parse_utc(attempt["attempted_at"], "scheduler_state_time_invalid"))
    active = state["active_attempt"]
    if active:
        values.append(_parse_utc(active["started_at"], "scheduler_state_time_invalid"))
    return max(values) if values else None


def _assert_clock(state: dict[str, Any], now: datetime) -> None:
    latest = _latest_state_time(state)
    if latest is not None and now.astimezone(timezone.utc) < latest:
        raise CodexSchedulerError("scheduler_clock_regression")


def _advance_revision(state: dict[str, Any]) -> None:
    state["revision"] += 1


def _evaluate_observation(
    state: dict[str, Any],
    observed: dict[str, Any],
    now: datetime,
) -> tuple[str, dict[str, Any]]:
    updated = copy.deepcopy(state)
    now_text = isoformat_utc(now)
    digest = observed["source_metadata_sha256"]
    completed = updated["last_completed"]
    if completed and completed["source_metadata_sha256"] == digest:
        changed = updated["pending"] is not None
        updated["pending"] = None
        return "NO_CHANGES", {"state": updated, "state_changed": changed}

    pending = updated["pending"]
    if pending is None:
        updated["pending"] = {
            **observed,
            "first_observed_at": now_text,
            "last_changed_at": now_text,
            "last_observed_at": now_text,
            "same_metadata_observation_count": 1,
        }
        return "COALESCING", {
            "state": updated,
            "state_changed": True,
            "same_metadata_observation_count": 1,
            "quiet_elapsed_seconds": 0,
            "pending_elapsed_seconds": 0,
            "max_pending_window_reached": False,
        }
    if pending["source_metadata_sha256"] != digest:
        pending = {
            **observed,
            "first_observed_at": pending["first_observed_at"],
            "last_changed_at": now_text,
            "last_observed_at": now_text,
            "same_metadata_observation_count": 1,
        }
        updated["pending"] = pending
    else:
        pending["last_observed_at"] = now_text
        pending["same_metadata_observation_count"] += 1
        pending["eligible_file_count"] = observed["eligible_file_count"]
        pending["eligible_total_bytes"] = observed["eligible_total_bytes"]
    quiet_elapsed = int((now - _parse_utc(pending["last_changed_at"], "scheduler_state_time_invalid")).total_seconds())
    pending_elapsed = int((now - _parse_utc(pending["first_observed_at"], "scheduler_state_time_invalid")).total_seconds())
    maximum_reached = pending_elapsed >= MAX_PENDING_SECONDS
    details = {
        "state": updated,
        "state_changed": True,
        "same_metadata_observation_count": pending["same_metadata_observation_count"],
        "quiet_elapsed_seconds": quiet_elapsed,
        "pending_elapsed_seconds": pending_elapsed,
        "max_pending_window_reached": maximum_reached,
    }
    quiet_ready = (
        pending["same_metadata_observation_count"] >= SAME_METADATA_OBSERVATIONS_REQUIRED
        and quiet_elapsed >= QUIET_PERIOD_SECONDS
    )
    if not quiet_ready and not maximum_reached:
        return "COALESCING", details
    if completed:
        success_elapsed = int(
            (now - _parse_utc(completed["completed_at"], "scheduler_state_time_invalid")).total_seconds()
        )
        if success_elapsed < MINIMUM_SUCCESS_INTERVAL_SECONDS:
            details["throttle_remaining_seconds"] = MINIMUM_SUCCESS_INTERVAL_SECONDS - success_elapsed
            return "THROTTLED", details
    return "READY", details


def _validate_push_main_result(payload: Any, *, dry_run: bool) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise CodexSchedulerError("push_main_child_contract_invalid")
    if (
        payload.get("schema_version") != PUSH_MAIN_RESULT_SCHEMA_VERSION
        or payload.get("task_id") != PUSH_MAIN_TASK_ID
        or payload.get("acceptance_id") != PUSH_MAIN_ACCEPTANCE_ID
        or payload.get("command") != "sync codex --push-main"
    ):
        raise CodexSchedulerError(
            "push_main_child_contract_invalid",
            remote_effect_possible=bool(payload.get("remote_push_attempted")),
        )
    push_count = payload.get("push_attempt_count")
    if not isinstance(push_count, int) or isinstance(push_count, bool) or push_count not in {0, 1}:
        raise CodexSchedulerError(
            "push_main_child_contract_invalid",
            remote_effect_possible=bool(payload.get("remote_push_attempted")) or bool(push_count),
        )
    for key in (
        "commit_created",
        "remote_push_attempted",
        "force_push",
        "fetch_executed",
        "branch_created",
        "pull_request_created",
        "merge_executed",
        "rebase_executed",
    ):
        if not isinstance(payload.get(key), bool):
            raise CodexSchedulerError("push_main_child_contract_invalid")
    pushed = payload.get("pushed")
    if (not isinstance(pushed, bool) and pushed is not None) or not isinstance(
        payload.get("remote_verified"), bool
    ):
        raise CodexSchedulerError("push_main_child_contract_invalid")
    if any(
        payload[key]
        for key in (
            "force_push",
            "fetch_executed",
            "branch_created",
            "pull_request_created",
            "merge_executed",
            "rebase_executed",
        )
    ):
        raise CodexSchedulerError("push_main_child_contract_invalid", remote_effect_possible=True)
    if payload.get("status") not in {"PASS", "FAIL_CLOSED"} or not isinstance(payload.get("outcome"), str):
        raise CodexSchedulerError("push_main_child_contract_invalid")
    effect_possible = bool(
        payload["commit_created"]
        or payload["remote_push_attempted"]
        or push_count
        or pushed is True
    )
    if dry_run:
        if (
            payload["status"] == "FAIL_CLOSED"
            and payload["outcome"] == "STOPPED"
            and push_count == 0
            and not payload["commit_created"]
            and not payload["remote_push_attempted"]
            and pushed is False
            and not payload["remote_verified"]
        ):
            raise CodexSchedulerError("push_main_dry_run_not_ready")
        if (
            payload["status"] != "PASS"
            or payload["outcome"] != "DRY_RUN_READY"
            or push_count != 0
            or payload["commit_created"]
            or payload["remote_push_attempted"]
            or pushed is not False
            or not payload["remote_verified"]
        ):
            raise CodexSchedulerError(
                "push_main_dry_run_contract_invalid",
                remote_effect_possible=effect_possible,
            )
    elif payload["status"] == "PASS":
        valid_no_changes = (
            payload["outcome"] == "NO_CHANGES"
            and push_count == 0
            and not payload["commit_created"]
            and not payload["remote_push_attempted"]
            and pushed is False
            and payload["remote_verified"]
        )
        valid_pushed = (
            payload["outcome"] == "PUSHED_MAIN"
            and push_count == 1
            and payload["commit_created"]
            and payload["remote_push_attempted"]
            and pushed is True
            and payload["remote_verified"]
        )
        if not (valid_no_changes or valid_pushed):
            raise CodexSchedulerError(
                "push_main_child_contract_invalid",
                remote_effect_possible=effect_possible,
            )
    elif payload["outcome"] != "STOPPED":
        raise CodexSchedulerError(
            "push_main_child_contract_invalid",
            remote_effect_possible=effect_possible,
        )
    return payload


def _default_source_probe(database_dir: Path, codex_home: Path | None) -> dict[str, Any]:
    payload = build_codex_source_discovery(
        database_dir,
        operator_codex_home=codex_home,
    )
    return {
        "source_metadata_sha256": payload["source_metadata_sha256"],
        "eligible_file_count": payload["eligible_file_count"],
        "eligible_total_bytes": payload["eligible_total_bytes"],
    }


def _default_push_main_runner(
    database_dir: Path,
    archive_id: str,
    *,
    codex_home: Path | None,
    dry_run: bool,
) -> dict[str, Any]:
    return execute_codex_push_main(
        database_dir,
        archive_id,
        codex_home=codex_home,
        dry_run=dry_run,
    )


def _base_result(owner_run_id: str, dry_run: bool) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "profile_id": PROFILE_ID,
        "status": "FAIL_CLOSED",
        "outcome": "NOT_STARTED",
        "owner_run_id": owner_run_id,
        "dry_run": dry_run,
        "writes_state": False,
        "writes_repository": False,
        "sync_invocation_count": 0,
        "push_attempt_count": 0,
        "source_mutation": False,
        "remote_push_attempted": False,
        "automatic_scheduler_install": False,
        "shell": False,
        "next_task": "S07-P3-T3",
    }


def _failure(result: dict[str, Any], error: CodexSchedulerError) -> dict[str, Any]:
    result.update(
        {
            "status": "FAIL_CLOSED",
            "outcome": "STOPPED",
            "reason": error.code,
            "remote_effect_possible": error.remote_effect_possible,
            "recovery": (
                "Inspect machine-local scheduler state and the S07-P3-T1 result. "
                "Do not retry a Git-effectful attempt, force, fetch, merge, rebase, or delete raw evidence."
            ),
        }
    )
    return result


def _attempt_record(owner_run_id: str, now: datetime, child: dict[str, Any]) -> dict[str, Any]:
    return {
        "owner_run_id": owner_run_id,
        "attempted_at": isoformat_utc(now),
        "status": child["status"],
        "child_outcome": child["outcome"],
        "push_attempt_count": child["push_attempt_count"],
        "commit_created": child["commit_created"],
        "remote_push_attempted": child["remote_push_attempted"],
    }


def _write_state_after_child(
    state_dir: Path,
    state: dict[str, Any],
    *,
    remote_effect_possible: bool,
) -> None:
    try:
        _write_state_atomic(state_dir, state)
    except CodexSchedulerError as exc:
        raise CodexSchedulerError(
            "scheduler_state_finalize_failed_after_child",
            remote_effect_possible=remote_effect_possible,
        ) from exc


def execute_codex_scheduler(
    database_dir: Path,
    *,
    state_dir: Path,
    codex_home: Path | None = None,
    owner_run_id: str | None = None,
    dry_run: bool = False,
    now: datetime | None = None,
    source_probe: SourceProbe | None = None,
    push_main_runner: PushMainRunner | None = None,
) -> dict[str, Any]:
    clock = now or datetime.now(timezone.utc)
    provisional_id = owner_run_id or generated_owner_run_id(clock)
    result = _base_result(provisional_id, dry_run)
    try:
        if clock.tzinfo is None:
            raise CodexSchedulerError("scheduler_clock_not_timezone_aware")
        clock = clock.astimezone(timezone.utc)
        owner_id = _validate_owner_run_id(provisional_id)
        result["owner_run_id"] = owner_id
        database = database_dir.resolve()
        profile = load_codex_scheduler_profile(database)
        load_codex_scheduler_model(database)
        profile_hash = _canonical_sha256(profile)
        runtime_dir = _validate_state_dir(state_dir, database, codex_home)
        probe = source_probe or _default_source_probe
        runner = push_main_runner or _default_push_main_runner

        if dry_run:
            state = _load_state(runtime_dir, profile_hash) if runtime_dir.exists() else _initial_state(profile_hash)
            _assert_clock(state, clock)
            if state["active_attempt"] is not None:
                raise CodexSchedulerError("previous_scheduler_attempt_incomplete")
            if state["manual_intervention_required"]:
                raise CodexSchedulerError("scheduler_manual_intervention_required")
            observed = _observation(probe(database, codex_home))
            decision, details = _evaluate_observation(state, observed, clock)
            child_raw = runner(
                database,
                generated_archive_id(lambda: clock),
                codex_home=codex_home,
                dry_run=True,
            )
            if isinstance(child_raw, dict):
                result["push_main_dry_run"] = child_raw
            child = _validate_push_main_result(child_raw, dry_run=True)
            result.update(
                {
                    "status": "PASS",
                    "outcome": "DRY_RUN_READY",
                    "scheduler_decision": decision,
                    "source_observation": observed,
                    "push_main_dry_run": child,
                    "state_would_change": bool(details.get("state_changed")),
                }
            )
            for key in (
                "same_metadata_observation_count",
                "quiet_elapsed_seconds",
                "pending_elapsed_seconds",
                "max_pending_window_reached",
                "throttle_remaining_seconds",
            ):
                if key in details:
                    result[key] = details[key]
            return result

        _prepare_state_dir(runtime_dir)
        with _SchedulerLock(runtime_dir):
            state = _load_state(runtime_dir, profile_hash)
            _assert_clock(state, clock)
            if state["active_attempt"] is not None:
                raise CodexSchedulerError("previous_scheduler_attempt_incomplete")
            if state["manual_intervention_required"]:
                raise CodexSchedulerError("scheduler_manual_intervention_required")
            if owner_id in state["attempted_owner_run_ids"]:
                result.update(
                    {
                        "status": "PASS",
                        "outcome": "OWNER_RUN_ALREADY_ATTEMPTED",
                        "last_child_outcome": state["last_attempt"]["child_outcome"],
                    }
                )
                return result

            observed = _observation(probe(database, codex_home))
            decision, details = _evaluate_observation(state, observed, clock)
            state = details["state"]
            result["source_observation"] = observed
            for key in (
                "same_metadata_observation_count",
                "quiet_elapsed_seconds",
                "pending_elapsed_seconds",
                "max_pending_window_reached",
                "throttle_remaining_seconds",
            ):
                if key in details:
                    result[key] = details[key]

            if decision != "READY":
                if details.get("state_changed"):
                    _advance_revision(state)
                    _write_state_atomic(runtime_dir, state)
                    result["writes_state"] = True
                result.update({"status": "PASS", "outcome": decision})
                return result

            state["active_attempt"] = {
                "owner_run_id": owner_id,
                "started_at": isoformat_utc(clock),
                "source_metadata_sha256": observed["source_metadata_sha256"],
            }
            state["attempted_owner_run_ids"] = (
                state["attempted_owner_run_ids"] + [owner_id]
            )[-ATTEMPTED_OWNER_RUN_HISTORY_LIMIT:]
            _advance_revision(state)
            _write_state_atomic(runtime_dir, state)
            result["writes_state"] = True
            result["sync_invocation_count"] = 1

            child_raw: dict[str, Any]
            try:
                child_raw = runner(
                    database,
                    generated_archive_id(lambda: clock),
                    codex_home=codex_home,
                    dry_run=False,
                )
                child = _validate_push_main_result(child_raw, dry_run=False)
            except CodexSchedulerError as exc:
                state["active_attempt"] = None
                state["manual_intervention_required"] = True
                _advance_revision(state)
                _write_state_after_child(
                    runtime_dir,
                    state,
                    remote_effect_possible=exc.remote_effect_possible,
                )
                result["push_attempt_count"] = (
                    child_raw.get("push_attempt_count", 0)
                    if "child_raw" in locals() and isinstance(child_raw, dict)
                    else 0
                )
                raise exc
            except Exception as exc:
                state["active_attempt"] = None
                state["manual_intervention_required"] = True
                _advance_revision(state)
                _write_state_after_child(
                    runtime_dir,
                    state,
                    remote_effect_possible=True,
                )
                raise CodexSchedulerError(
                    "push_main_child_unexpected_failure",
                    remote_effect_possible=True,
                ) from exc

            result.update(
                {
                    "child_outcome": child["outcome"],
                    "push_attempt_count": child["push_attempt_count"],
                    "remote_push_attempted": child["remote_push_attempted"],
                    "writes_repository": bool(child["commit_created"]),
                }
            )
            state["active_attempt"] = None
            state["last_attempt"] = _attempt_record(owner_id, clock, child)
            if child["status"] == "PASS":
                state["pending"] = None
                state["last_completed"] = {
                    "source_metadata_sha256": observed["source_metadata_sha256"],
                    "completed_at": isoformat_utc(clock),
                    "child_outcome": child["outcome"],
                }
                state["manual_intervention_required"] = False
                _advance_revision(state)
                _write_state_after_child(
                    runtime_dir,
                    state,
                    remote_effect_possible=bool(child["remote_push_attempted"]),
                )
                result.update({"status": "PASS", "outcome": "SYNC_COMPLETED"})
                return result

            effectful = bool(
                child["commit_created"]
                or child["remote_push_attempted"]
                or child["push_attempt_count"]
            )
            state["manual_intervention_required"] = effectful
            _advance_revision(state)
            _write_state_after_child(
                runtime_dir,
                state,
                remote_effect_possible=effectful,
            )
            reason = (
                "push_main_child_failed_after_git_effect"
                if effectful
                else "push_main_child_failed_before_git_effect"
            )
            raise CodexSchedulerError(reason, remote_effect_possible=effectful)
    except CodexSchedulerError as exc:
        return _failure(result, exc)
    except Exception:
        return _failure(result, CodexSchedulerError("unexpected_scheduler_failure"))


def run_codex_scheduler(args: argparse.Namespace) -> int:
    state_dir = getattr(args, "state_dir", None) or default_scheduler_state_dir()
    result = execute_codex_scheduler(
        Path(getattr(args, "database_dir", Path(__file__).resolve().parents[2])),
        state_dir=state_dir,
        codex_home=getattr(args, "codex_home", None),
        owner_run_id=getattr(args, "owner_run_id", None),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = (
    "ACCEPTANCE_ID",
    "EXPECTED_MODEL_PARAMETERS",
    "EXPECTED_PROFILE",
    "LOCK_FILENAME",
    "MODEL_PARAMETERS_PATH",
    "PROFILE_PATH",
    "RESULT_SCHEMA_VERSION",
    "STATE_FILENAME",
    "TASK_ID",
    "default_scheduler_state_dir",
    "execute_codex_scheduler",
    "generated_owner_run_id",
    "isoformat_utc",
    "load_codex_scheduler_model",
    "load_codex_scheduler_profile",
    "run_codex_scheduler",
    "validate_codex_scheduler_model",
    "validate_codex_scheduler_profile",
)
