"""Shared configuration, state, error, and machine-log runtime for atlasctl."""

from __future__ import annotations

import json
import os
import re
import stat
import sys
import time
import uuid
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, TextIO

from .constants import ROOT


RUNTIME_CONFIG_SCHEMA_VERSION = "memory_atlas_cli_runtime_config.v1_2_1_s04_p2_t2"
RUNTIME_EVENT_SCHEMA_VERSION = "memory_atlas_cli_runtime_event.v1_2_1_s04_p2_t2"
RUNTIME_CONFIG_ENV = "MEMORY_ATLAS_RUNTIME_CONFIG"
DEFAULT_RUNTIME_CONFIG_PATH = ROOT / "config/atlasctl_runtime.json"
MAX_RUNTIME_CONFIG_BYTES = 16 * 1024

KNOWN_COMMANDS = frozenset(
    {
        "run",
        "sync",
        "request-chatgpt-export",
        "build-atlas",
        "analyze",
        "audit",
        "push",
        "generate-personalization-prompt",
        "chatgpt-deep-explore",
        "deep-explore",
        "proposals",
        "apply",
    }
)
_CONFIG_KEYS = frozenset(
    {
        "schema_version",
        "machine_log_destination",
        "emit_started_event",
        "exception_detail",
    }
)
_EXCEPTION_TYPE_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]{0,127}$")


class RuntimeConfigError(ValueError):
    """Raised when the runtime configuration cannot be trusted."""


class RuntimeStateError(RuntimeError):
    """Raised when a runtime state transition is illegal."""


class RuntimeErrorCode(str, Enum):
    OK = "MA_OK"
    ARGUMENT_INVALID = "MA_ARGUMENT_INVALID"
    CONFIG_INVALID = "MA_CONFIG_INVALID"
    FAIL_CLOSED = "MA_FAIL_CLOSED"
    COMMAND_FAILED = "MA_COMMAND_FAILED"
    UNHANDLED_EXCEPTION = "MA_UNHANDLED_EXCEPTION"


class RunStatus(str, Enum):
    CREATED = "CREATED"
    RUNNING = "RUNNING"
    SUCCEEDED = "SUCCEEDED"
    FAIL_CLOSED = "FAIL_CLOSED"
    FAILED = "FAILED"
    REJECTED = "REJECTED"


_ALLOWED_TRANSITIONS = {
    RunStatus.CREATED: frozenset({RunStatus.RUNNING, RunStatus.REJECTED}),
    RunStatus.RUNNING: frozenset(
        {RunStatus.SUCCEEDED, RunStatus.FAIL_CLOSED, RunStatus.FAILED}
    ),
}


@dataclass(frozen=True)
class RuntimeConfig:
    schema_version: str
    machine_log_destination: str
    emit_started_event: bool
    exception_detail: str
    source_path: Path

    @classmethod
    def from_mapping(cls, payload: object, source_path: Path) -> "RuntimeConfig":
        if not isinstance(payload, dict):
            raise RuntimeConfigError("runtime config must be a JSON object")
        if set(payload) != _CONFIG_KEYS:
            raise RuntimeConfigError("runtime config keys do not match the schema")
        if payload["schema_version"] != RUNTIME_CONFIG_SCHEMA_VERSION:
            raise RuntimeConfigError("runtime config schema version is unsupported")
        if payload["machine_log_destination"] not in {"stderr", "off"}:
            raise RuntimeConfigError("machine log destination is unsupported")
        if type(payload["emit_started_event"]) is not bool:
            raise RuntimeConfigError("emit_started_event must be a boolean")
        if payload["exception_detail"] != "type_only":
            raise RuntimeConfigError("exception detail must remain type_only")
        return cls(
            schema_version=RUNTIME_CONFIG_SCHEMA_VERSION,
            machine_log_destination=str(payload["machine_log_destination"]),
            emit_started_event=payload["emit_started_event"],
            exception_detail="type_only",
            source_path=source_path,
        )


@dataclass
class RuntimeState:
    run_id: str
    command: str
    dry_run: bool
    status: RunStatus = RunStatus.CREATED

    def transition(self, next_status: RunStatus) -> None:
        allowed = _ALLOWED_TRANSITIONS.get(self.status, frozenset())
        if next_status not in allowed:
            raise RuntimeStateError(
                f"illegal runtime transition: {self.status.value} -> {next_status.value}"
            )
        self.status = next_status


def _config_path(path: Path | str | None, env: Mapping[str, str] | None) -> Path:
    if path is not None:
        candidate = Path(path)
    else:
        values = os.environ if env is None else env
        override = values.get(RUNTIME_CONFIG_ENV)
        if override == "":
            raise RuntimeConfigError("runtime config override cannot be empty")
        candidate = Path(override) if override is not None else DEFAULT_RUNTIME_CONFIG_PATH
    return candidate.expanduser().absolute()


def _read_config_bytes(path: Path) -> bytes:
    if path.is_symlink():
        raise RuntimeConfigError("runtime config cannot be a symlink")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except (FileNotFoundError, OSError) as exc:
        raise RuntimeConfigError("runtime config is unavailable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise RuntimeConfigError("runtime config must be a regular file")
        if metadata.st_size > MAX_RUNTIME_CONFIG_BYTES:
            raise RuntimeConfigError("runtime config exceeds the size limit")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(MAX_RUNTIME_CONFIG_BYTES + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > MAX_RUNTIME_CONFIG_BYTES:
        raise RuntimeConfigError("runtime config exceeds the size limit")
    return content


def load_runtime_config(
    path: Path | str | None = None,
    *,
    env: Mapping[str, str] | None = None,
) -> RuntimeConfig:
    source_path = _config_path(path, env)
    try:
        payload = json.loads(_read_config_bytes(source_path).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RuntimeConfigError("runtime config is not valid UTF-8 JSON") from exc
    return RuntimeConfig.from_mapping(payload, source_path)


def _utc_timestamp(clock: Callable[[], datetime]) -> str:
    value = clock()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_command(command: object) -> str:
    return command if isinstance(command, str) and command in KNOWN_COMMANDS else "unparsed"


def command_from_argv(argv: list[str] | None = None) -> str:
    values = sys.argv[1:] if argv is None else argv
    return _safe_command(values[0] if values else None)


def _safe_exception_type(exc: Exception) -> str:
    name = type(exc).__name__
    return name if _EXCEPTION_TYPE_PATTERN.fullmatch(name) else "Exception"


@dataclass
class _MachineLogger:
    config: RuntimeConfig
    stream: TextIO
    clock: Callable[[], datetime]
    transport_available: bool = True

    def emit(self, payload: Mapping[str, Any]) -> None:
        if self.config.machine_log_destination == "off" or not self.transport_available:
            return
        event = {
            "schema_version": RUNTIME_EVENT_SCHEMA_VERSION,
            "timestamp": _utc_timestamp(self.clock),
            **payload,
        }
        serialized = json.dumps(
            event, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        ) + "\n"
        try:
            self.stream.write(serialized)
            self.stream.flush()
        except (OSError, ValueError):
            # Machine telemetry must never replace the runner's stdout, exit, or exception.
            self.transport_available = False


def _base_event(
    state: RuntimeState,
    *,
    event: str,
    level: str,
    error_code: RuntimeErrorCode,
    exit_code: int | None,
) -> dict[str, Any]:
    return {
        "run_id": state.run_id,
        "command": state.command,
        "event": event,
        "level": level,
        "status": state.status.value,
        "error_code": error_code.value,
        "exit_code": exit_code,
        "dry_run": state.dry_run,
    }


def execute_with_runtime(
    args: Any,
    runner: Callable[[Any], int],
    *,
    config: RuntimeConfig | None = None,
    machine_stream: TextIO | None = None,
    env: Mapping[str, str] | None = None,
    clock: Callable[[], datetime] | None = None,
    monotonic: Callable[[], float] | None = None,
    run_id_factory: Callable[[], str] | None = None,
) -> int:
    resolved_config = config if config is not None else load_runtime_config(env=env)
    resolved_clock = clock or (lambda: datetime.now(timezone.utc))
    resolved_monotonic = monotonic or time.monotonic
    resolved_run_id = run_id_factory or (lambda: uuid.uuid4().hex)
    logger = _MachineLogger(
        resolved_config,
        machine_stream if machine_stream is not None else sys.stderr,
        resolved_clock,
    )
    state = RuntimeState(
        run_id=str(resolved_run_id()),
        command=_safe_command(getattr(args, "command", None)),
        dry_run=bool(getattr(args, "dry_run", False)),
    )
    state.transition(RunStatus.RUNNING)
    started_at = resolved_monotonic()
    if resolved_config.emit_started_event:
        logger.emit(
            _base_event(
                state,
                event="run_started",
                level="INFO",
                error_code=RuntimeErrorCode.OK,
                exit_code=None,
            )
        )
    try:
        exit_code = runner(args)
        if type(exit_code) is not int:
            raise TypeError("atlasctl runners must return an integer exit code")
    except Exception as exc:
        state.transition(RunStatus.FAILED)
        payload = _base_event(
            state,
            event="run_failed",
            level="ERROR",
            error_code=RuntimeErrorCode.UNHANDLED_EXCEPTION,
            exit_code=1,
        )
        payload["duration_ms"] = max(0, int((resolved_monotonic() - started_at) * 1000))
        payload["exception_type"] = _safe_exception_type(exc)
        logger.emit(payload)
        raise

    if exit_code == 0:
        status = RunStatus.SUCCEEDED
        error_code = RuntimeErrorCode.OK
        level = "INFO"
    elif exit_code == 2:
        status = RunStatus.FAIL_CLOSED
        error_code = RuntimeErrorCode.FAIL_CLOSED
        level = "WARNING"
    else:
        status = RunStatus.FAILED
        error_code = RuntimeErrorCode.COMMAND_FAILED
        level = "ERROR"
    state.transition(status)
    payload = _base_event(
        state,
        event="run_finished",
        level=level,
        error_code=error_code,
        exit_code=exit_code,
    )
    payload["duration_ms"] = max(0, int((resolved_monotonic() - started_at) * 1000))
    logger.emit(payload)
    return exit_code


def emit_bootstrap_rejection(
    error_code: RuntimeErrorCode,
    *,
    command: str = "unparsed",
    exit_code: int = 2,
    machine_stream: TextIO | None = None,
    clock: Callable[[], datetime] | None = None,
    run_id_factory: Callable[[], str] | None = None,
) -> None:
    fallback_config = RuntimeConfig.from_mapping(
        {
            "schema_version": RUNTIME_CONFIG_SCHEMA_VERSION,
            "machine_log_destination": "stderr",
            "emit_started_event": False,
            "exception_detail": "type_only",
        },
        DEFAULT_RUNTIME_CONFIG_PATH,
    )
    resolved_clock = clock or (lambda: datetime.now(timezone.utc))
    resolved_run_id = run_id_factory or (lambda: uuid.uuid4().hex)
    logger = _MachineLogger(
        fallback_config,
        machine_stream if machine_stream is not None else sys.stderr,
        resolved_clock,
    )
    state = RuntimeState(
        run_id=str(resolved_run_id()),
        command=_safe_command(command),
        dry_run=False,
    )
    state.transition(RunStatus.REJECTED)
    logger.emit(
        _base_event(
            state,
            event="run_rejected",
            level="ERROR",
            error_code=error_code,
            exit_code=exit_code,
        )
    )


__all__ = (
    "DEFAULT_RUNTIME_CONFIG_PATH",
    "KNOWN_COMMANDS",
    "MAX_RUNTIME_CONFIG_BYTES",
    "RUNTIME_CONFIG_ENV",
    "RUNTIME_CONFIG_SCHEMA_VERSION",
    "RUNTIME_EVENT_SCHEMA_VERSION",
    "RunStatus",
    "RuntimeConfig",
    "RuntimeConfigError",
    "RuntimeErrorCode",
    "RuntimeState",
    "RuntimeStateError",
    "command_from_argv",
    "emit_bootstrap_rejection",
    "execute_with_runtime",
    "load_runtime_config",
)
