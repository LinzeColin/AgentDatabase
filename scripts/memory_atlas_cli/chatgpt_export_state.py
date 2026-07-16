"""Durable ChatGPT export state machine and pending-request guard."""

from __future__ import annotations

import errno
import fcntl
import hashlib
import io
import json
import os
import re
import secrets
import stat
import tempfile
from contextlib import contextmanager, redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterator

from .chatgpt_export_request import run_chatgpt_export_request


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_state.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_state.v1_2_1_s08_p1_t2.json"
)
STATE_RELATIVE = Path("data/sync_state/chatgpt.json")
TASK_ID = "S08-P1-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P1-T2"
SOURCE_ID = "chatgpt"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_state_contract.v1_2_1_s08_p1_t2"
)
MODEL_SCHEMA_VERSION = "memory_atlas.chatgpt_export_state_model.v1_2_1_s08_p1_t2"
STATE_SCHEMA_VERSION = "memory_atlas.chatgpt_export_state.v1_2_1_s08_p1_t2"
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_state_result.v1_2_1_s08_p1_t2"
)
CONNECTOR_RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1"
)
CONNECTOR_TASK_ID = "S08-P1-T1"
CONNECTOR_ACCEPTANCE_ID = "ACC-MA-V121-S08-P1-T1"

EXPORT_STATES = (
    "IDLE",
    "REQUESTED",
    "WAITING_FOR_EXPORT",
    "LINK_READY",
    "DOWNLOADED",
    "ARCHIVED",
    "PARSED",
    "VALIDATED",
    "COMMITTED",
    "PUSHED",
    "FAILED_NEEDS_HUMAN_AUTH",
    "FAILED_RETRYABLE",
)
NORMAL_TRANSITIONS = (
    ("IDLE", "REQUESTED"),
    ("REQUESTED", "WAITING_FOR_EXPORT"),
    ("WAITING_FOR_EXPORT", "LINK_READY"),
    ("LINK_READY", "DOWNLOADED"),
    ("DOWNLOADED", "ARCHIVED"),
    ("ARCHIVED", "PARSED"),
    ("PARSED", "VALIDATED"),
    ("VALIDATED", "COMMITTED"),
    ("COMMITTED", "PUSHED"),
)
PENDING_STATES = frozenset({"REQUESTED", "WAITING_FOR_EXPORT", "LINK_READY"})
HUMAN_AUTH_STATE = "FAILED_NEEDS_HUMAN_AUTH"
RETRYABLE_STATE = "FAILED_RETRYABLE"
FAILURE_STATES = frozenset({HUMAN_AUTH_STATE, RETRYABLE_STATE})
FAILURE_SOURCES = frozenset(EXPORT_STATES) - {"PUSHED", *FAILURE_STATES}
MAX_STATE_BYTES = 64 * 1024
MAX_HISTORY_ENTRIES = 128
MAX_CONNECTOR_OUTPUT_BYTES = 16 * 1024
MAX_EVENT_ID_CHARS = 96
MAX_REASON_CODE_CHARS = 96
PHASE_BOUNDARY = {
    "implements_human_auth_resume": False,
    "discovers_notifications": False,
    "downloads_export": False,
    "writes_raw_archive": False,
    "commits_or_pushes": False,
    "deploys": False,
    "next_task": "S08-P1-T3",
}
_CODE_RE = re.compile(r"^[a-z][a-z0-9_]{0,95}$")
_EVENT_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,95}$")
_REQUEST_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "state_path": STATE_RELATIVE.as_posix(),
    "states": list(EXPORT_STATES),
    "normal_transitions": [list(row) for row in NORMAL_TRANSITIONS],
    "failure_transitions": {
        "allowed_from": [state for state in EXPORT_STATES if state in FAILURE_SOURCES],
        "targets": [HUMAN_AUTH_STATE, RETRYABLE_STATE],
        "retryable_resume": "explicit_transition_or_new_confirmed_request_after_zero_click",
        "human_auth_resume": "deferred_to_s08_p1_t3",
    },
    "no_duplicate_request_while": [
        "REQUESTED",
        "WAITING_FOR_EXPORT",
        "LINK_READY",
    ],
    "request_coupling": {
        "pre_effect_state": "REQUESTED",
        "pre_effect_write": "atomic_before_connector_dispatch",
        "success_state": "WAITING_FOR_EXPORT",
        "zero_click_failure_state": RETRYABLE_STATE,
        "uncertain_click_state": "REQUESTED",
        "maximum_request_clicks": 1,
        "lock_scope": "state_check_reservation_connector_and_finalize",
    },
    "state_integrity": {
        "write": "exclusive_temp_fsync_atomic_replace_directory_fsync",
        "lock": "nonblocking_process_advisory_lock",
        "optimistic_revision_required": True,
        "event_id_idempotency": True,
        "maximum_state_bytes": MAX_STATE_BYTES,
        "maximum_history_entries": MAX_HISTORY_ENTRIES,
        "symlinks_allowed": False,
    },
    "cli": {
        "request_command": "request-chatgpt-export",
        "state_command": "chatgpt-export-state",
        "inspect_is_read_only": True,
        "state_apply_requires": [
            "--to-state",
            "--expected-revision",
            "--event-id",
            "--reason-code",
            "--evidence-sha256",
        ],
        "request_state_requires_connector": True,
    },
    "security": {
        "credentials_in_state": False,
        "cookies_in_state": False,
        "download_links_in_state": False,
        "account_identity_in_state": False,
        "private_api_calls": False,
        "raw_mutation": False,
        "remote_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-009",
    "formula_id": "FORM-009",
    "purpose": "Persist the official ChatGPT export lifecycle and suppress every duplicate request while a prior request can still be pending.",
    "parameters": {
        "maximum_state_bytes": MAX_STATE_BYTES,
        "maximum_transition_history_entries": MAX_HISTORY_ENTRIES,
        "maximum_connector_output_bytes": MAX_CONNECTOR_OUTPUT_BYTES,
        "maximum_event_id_characters": MAX_EVENT_ID_CHARS,
        "maximum_reason_code_characters": MAX_REASON_CODE_CHARS,
        "maximum_request_clicks": 1,
        "lock_wait_seconds": 0,
    },
    "formula": "request_permitted = explicit_apply_confirmation AND lock_acquired AND state_valid AND state_not_in{REQUESTED,WAITING_FOR_EXPORT,LINK_READY} AND (state=IDLE OR safe_zero_click_retry); reservation_persisted_before_connector = true",
    "parameter_rationale": {
        "maximum_state_bytes": "A 64 KiB ceiling is ample for one bounded lifecycle journal and prevents arbitrary payload capture.",
        "maximum_transition_history_entries": "One export requires fewer than twelve normal transitions; 128 entries retain retries without unbounded growth.",
        "maximum_connector_output_bytes": "The state wrapper accepts only the same bounded sanitized machine payload as the visible-UI connector.",
        "maximum_event_id_characters": "Short portable event identifiers remain reviewable and path-independent.",
        "maximum_reason_code_characters": "Reason codes are bounded enums, never free-form account or notification content.",
        "maximum_request_clicks": "One explicit connector dispatch is the hard limit for each reservation.",
        "lock_wait_seconds": "A nonblocking lock fails closed instead of queueing a second possible request.",
    },
    "failure_semantics": "Missing, malformed, oversized, symlinked, stale-revision or concurrently locked state fails before connector execution. A reservation is atomically durable before any request click. Zero-click failure is retryable; one-click or unknown outcome remains pending. Human-auth resume is forbidden until S08-P1-T3.",
    "calibration_boundary": "S08-P1-T2 implements state persistence, transitions, idempotency and pending-request suppression only. S08-P1-T3 owns human-auth pause/resume behavior; S08-P2/P3 own notification, download, archive and push effects.",
}


class ChatGPTExportStateError(RuntimeError):
    """Path-free state-machine failure."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _canonical_json_bytes(payload: object) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _sha256_payload(payload: object) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(canonical).hexdigest()


def _now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _validate_utc(value: object, code: str) -> str:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ChatGPTExportStateError(code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ChatGPTExportStateError(code) from exc
    if parsed.tzinfo is None or parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ChatGPTExportStateError(code)
    return value


def _validate_code(value: object, code: str) -> str:
    if not isinstance(value, str) or not _CODE_RE.fullmatch(value):
        raise ChatGPTExportStateError(code)
    return value


def _validate_event_id(value: object) -> str:
    if not isinstance(value, str) or not _EVENT_ID_RE.fullmatch(value):
        raise ChatGPTExportStateError("export_state_event_id_invalid")
    return value


def _validate_sha256(value: object, code: str) -> str:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value):
        raise ChatGPTExportStateError(code)
    return value


def _database_root(database_dir: Path) -> Path:
    path = Path(database_dir).expanduser()
    if path.is_symlink() or not path.is_dir():
        raise ChatGPTExportStateError("export_state_database_invalid")
    return path.resolve()


def _read_json(path: Path, *, maximum_bytes: int, code: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ChatGPTExportStateError(code) from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ChatGPTExportStateError(code)
    if metadata.st_size <= 0 or metadata.st_size > maximum_bytes:
        raise ChatGPTExportStateError(code)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChatGPTExportStateError(code) from exc
    if not isinstance(value, dict):
        raise ChatGPTExportStateError(code)
    return value


def validate_chatgpt_export_state_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise ChatGPTExportStateError("export_state_contract_drift")
    return dict(payload)


def validate_chatgpt_export_state_model_parameters(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTExportStateError("export_state_model_drift")
    return dict(payload)


def load_chatgpt_export_state_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_state_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_STATE_BYTES,
            code="export_state_contract_unreadable",
        )
    )


def load_chatgpt_export_state_model_parameters(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_state_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_STATE_BYTES,
            code="export_state_model_unreadable",
        )
    )


def build_initial_export_state() -> dict[str, Any]:
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "state_path": STATE_RELATIVE.as_posix(),
        "revision": 0,
        "status": "IDLE",
        "updated_at": None,
        "request": None,
        "retry_from": None,
        "last_error_code": None,
        "history": [],
        "phase_boundary": PHASE_BOUNDARY,
    }


def _validate_request(value: object) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != {
        "request_id",
        "origin_state",
        "reserved_at",
        "dispatch_status",
        "request_click_count",
        "connector_error_code",
        "connector_result_sha256",
    }:
        raise ChatGPTExportStateError("export_state_request_invalid")
    if not isinstance(value["request_id"], str) or not _REQUEST_ID_RE.fullmatch(
        value["request_id"]
    ):
        raise ChatGPTExportStateError("export_state_request_invalid")
    if value["origin_state"] != "IDLE":
        raise ChatGPTExportStateError("export_state_request_invalid")
    _validate_utc(value["reserved_at"], "export_state_request_invalid")
    if value["dispatch_status"] not in {
        "RESERVED",
        "DISPATCHED",
        "FAILED_BEFORE_CLICK",
        "OUTCOME_UNCERTAIN",
    }:
        raise ChatGPTExportStateError("export_state_request_invalid")
    if type(value["request_click_count"]) is not int or value[
        "request_click_count"
    ] not in {0, 1}:
        raise ChatGPTExportStateError("export_state_request_invalid")
    error = value["connector_error_code"]
    if error is not None:
        _validate_code(error, "export_state_request_invalid")
    result_hash = value["connector_result_sha256"]
    if result_hash is not None:
        _validate_sha256(result_hash, "export_state_request_invalid")
    return dict(value)


def _validate_history(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list) or len(value) > MAX_HISTORY_ENTRIES:
        raise ChatGPTExportStateError("export_state_history_invalid")
    result: list[dict[str, Any]] = []
    seen: set[str] = set()
    previous_to = "IDLE"
    for index, row in enumerate(value):
        if not isinstance(row, dict) or set(row) != {
            "event_id",
            "from_state",
            "to_state",
            "reason_code",
            "evidence_sha256",
            "occurred_at",
        }:
            raise ChatGPTExportStateError("export_state_history_invalid")
        event_id = _validate_event_id(row["event_id"])
        if event_id in seen:
            raise ChatGPTExportStateError("export_state_history_invalid")
        seen.add(event_id)
        if row["from_state"] not in EXPORT_STATES or row["to_state"] not in EXPORT_STATES:
            raise ChatGPTExportStateError("export_state_history_invalid")
        if index == 0 and row["from_state"] != "IDLE":
            raise ChatGPTExportStateError("export_state_history_invalid")
        if index > 0 and row["from_state"] != previous_to:
            raise ChatGPTExportStateError("export_state_history_invalid")
        reason_code = _validate_code(
            row["reason_code"], "export_state_history_invalid"
        )
        _validate_sha256(row["evidence_sha256"], "export_state_history_invalid")
        _validate_utc(row["occurred_at"], "export_state_history_invalid")
        source = row["from_state"]
        target = row["to_state"]
        coupled_transition = {
            "request_reserved_before_connector": (
                source in {"IDLE", RETRYABLE_STATE} and target == "REQUESTED"
            ),
            "request_dispatched_waiting_for_export": (
                source == "REQUESTED" and target == "WAITING_FOR_EXPORT"
            ),
            "request_failed_before_click": (
                source == "REQUESTED" and target == RETRYABLE_STATE
            ),
            "request_click_outcome_uncertain": (
                source == "REQUESTED" and target == "REQUESTED"
            ),
        }
        if reason_code in coupled_transition:
            transition_valid = coupled_transition[reason_code]
        else:
            transition_valid = (source, target) in NORMAL_TRANSITIONS
            if target in FAILURE_STATES and source in FAILURE_SOURCES:
                transition_valid = True
            if source == RETRYABLE_STATE and result:
                failed_transition = result[-1]
                if (
                    failed_transition["to_state"] == RETRYABLE_STATE
                    and target == failed_transition["from_state"]
                ):
                    transition_valid = True
        if not transition_valid:
            raise ChatGPTExportStateError("export_state_history_invalid")
        previous_to = row["to_state"]
        result.append(dict(row))
    return result


def validate_chatgpt_export_state(payload: object) -> dict[str, Any]:
    required = {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "state_path",
        "revision",
        "status",
        "updated_at",
        "request",
        "retry_from",
        "last_error_code",
        "history",
        "phase_boundary",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ChatGPTExportStateError("export_state_shape_invalid")
    if (
        payload["schema_version"] != STATE_SCHEMA_VERSION
        or payload["task_id"] != TASK_ID
        or payload["acceptance_id"] != ACCEPTANCE_ID
        or payload["source_id"] != SOURCE_ID
        or payload["state_path"] != STATE_RELATIVE.as_posix()
        or payload["phase_boundary"] != PHASE_BOUNDARY
    ):
        raise ChatGPTExportStateError("export_state_identity_invalid")
    if payload["status"] not in EXPORT_STATES:
        raise ChatGPTExportStateError("export_state_status_invalid")
    history = _validate_history(payload["history"])
    if type(payload["revision"]) is not int or payload["revision"] != len(history):
        raise ChatGPTExportStateError("export_state_revision_invalid")
    if history:
        if payload["status"] != history[-1]["to_state"]:
            raise ChatGPTExportStateError("export_state_history_status_mismatch")
        if payload["updated_at"] != history[-1]["occurred_at"]:
            raise ChatGPTExportStateError("export_state_updated_at_invalid")
    elif payload["updated_at"] is not None or payload["status"] != "IDLE":
        raise ChatGPTExportStateError("export_state_updated_at_invalid")
    request = payload["request"]
    if request is not None:
        request = _validate_request(request)
    if payload["status"] == "IDLE" and request is not None:
        raise ChatGPTExportStateError("export_state_request_invalid")
    if payload["status"] in {
        "REQUESTED",
        "WAITING_FOR_EXPORT",
        "LINK_READY",
        "DOWNLOADED",
        "ARCHIVED",
        "PARSED",
        "VALIDATED",
        "COMMITTED",
        "PUSHED",
    } and request is None:
        raise ChatGPTExportStateError("export_state_request_missing")
    retry_from = payload["retry_from"]
    if payload["status"] == RETRYABLE_STATE:
        if retry_from not in FAILURE_SOURCES:
            raise ChatGPTExportStateError("export_state_retry_invalid")
    elif retry_from is not None:
        raise ChatGPTExportStateError("export_state_retry_invalid")
    error = payload["last_error_code"]
    if error is not None:
        _validate_code(error, "export_state_error_code_invalid")
    if payload["status"] in FAILURE_STATES and error is None:
        raise ChatGPTExportStateError("export_state_error_code_invalid")
    return dict(payload)


def load_chatgpt_export_state(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    path = root / STATE_RELATIVE
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ChatGPTExportStateError("export_state_unavailable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
        raise ChatGPTExportStateError("export_state_target_unsafe")
    return validate_chatgpt_export_state(
        _read_json(
            path,
            maximum_bytes=MAX_STATE_BYTES,
            code="export_state_unreadable",
        )
    )


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def write_chatgpt_export_state(database_dir: Path, payload: dict[str, Any]) -> None:
    state = validate_chatgpt_export_state(payload)
    root = _database_root(database_dir)
    path = root / STATE_RELATIVE
    parent = path.parent
    parent.mkdir(parents=True, exist_ok=True)
    if parent.is_symlink() or not parent.is_dir() or root not in parent.resolve().parents:
        raise ChatGPTExportStateError("export_state_parent_unsafe")
    if os.path.lexists(path):
        metadata = path.lstat()
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise ChatGPTExportStateError("export_state_target_unsafe")
    temporary = parent / f".{path.name}.{os.getpid()}.{secrets.token_hex(6)}.tmp"
    descriptor: int | None = None
    try:
        descriptor = os.open(
            temporary,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY,
            0o600,
        )
        content = _canonical_json_bytes(state)
        if len(content) > MAX_STATE_BYTES:
            raise ChatGPTExportStateError("export_state_oversized")
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = None
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        _fsync_directory(parent)
    except ChatGPTExportStateError:
        raise
    except OSError as exc:
        raise ChatGPTExportStateError("export_state_write_failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if os.path.lexists(temporary):
            temporary.unlink()


@contextmanager
def export_state_lock(database_dir: Path) -> Iterator[None]:
    root = _database_root(database_dir)
    identity = hashlib.sha256(str(root).encode("utf-8")).hexdigest()[:24]
    path = Path(tempfile.gettempdir()) / f"memory-atlas-chatgpt-export-{identity}.lock"
    flags = os.O_CREAT | os.O_RDWR
    flags |= getattr(os, "O_CLOEXEC", 0)
    flags |= getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
    except OSError as exc:
        if exc.errno in {errno.ELOOP, errno.EMLINK}:
            raise ChatGPTExportStateError("export_state_lock_unsafe") from exc
        raise ChatGPTExportStateError("export_state_lock_unavailable") from exc
    try:
        if not stat.S_ISREG(os.fstat(descriptor).st_mode):
            raise ChatGPTExportStateError("export_state_lock_unsafe")
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ChatGPTExportStateError("export_state_lock_busy") from exc
        try:
            yield
        finally:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
    finally:
        os.close(descriptor)


def _append_history(
    state: dict[str, Any],
    *,
    to_state: str,
    event_id: str,
    reason_code: str,
    evidence_sha256: str,
    occurred_at: str,
) -> dict[str, Any]:
    if len(state["history"]) >= MAX_HISTORY_ENTRIES:
        raise ChatGPTExportStateError("export_state_history_full")
    updated = json.loads(json.dumps(state))
    updated["history"].append(
        {
            "event_id": _validate_event_id(event_id),
            "from_state": state["status"],
            "to_state": to_state,
            "reason_code": _validate_code(
                reason_code, "export_state_reason_code_invalid"
            ),
            "evidence_sha256": _validate_sha256(
                evidence_sha256, "export_state_evidence_invalid"
            ),
            "occurred_at": _validate_utc(
                occurred_at, "export_state_occurred_at_invalid"
            ),
        }
    )
    updated["revision"] += 1
    updated["status"] = to_state
    updated["updated_at"] = occurred_at
    return updated


def reserve_export_request(
    state: dict[str, Any],
    *,
    request_id: str,
    occurred_at: str,
) -> tuple[dict[str, Any], bool]:
    current = validate_chatgpt_export_state(state)
    if current["status"] in PENDING_STATES:
        raise ChatGPTExportStateError("export_request_pending")
    retry_allowed = (
        current["status"] == RETRYABLE_STATE
        and current["retry_from"] == "IDLE"
        and isinstance(current["request"], dict)
        and current["request"]["request_click_count"] == 0
    )
    if current["status"] != "IDLE" and not retry_allowed:
        raise ChatGPTExportStateError("export_request_state_invalid")
    if not isinstance(request_id, str) or not _REQUEST_ID_RE.fullmatch(request_id):
        raise ChatGPTExportStateError("export_request_id_invalid")
    _validate_utc(occurred_at, "export_state_occurred_at_invalid")
    request = {
        "request_id": request_id,
        "origin_state": "IDLE",
        "reserved_at": occurred_at,
        "dispatch_status": "RESERVED",
        "request_click_count": 0,
        "connector_error_code": None,
        "connector_result_sha256": None,
    }
    updated = _append_history(
        current,
        to_state="REQUESTED",
        event_id=f"request-reserved-{request_id}",
        reason_code="request_reserved_before_connector",
        evidence_sha256=_sha256_payload(request),
        occurred_at=occurred_at,
    )
    updated["request"] = request
    updated["retry_from"] = None
    updated["last_error_code"] = None
    return validate_chatgpt_export_state(updated), True


def _connector_failure_payload(code: str, clicks: int) -> dict[str, Any]:
    safe_code = code if _CODE_RE.fullmatch(code) else "connector_output_invalid"
    return {
        "schema_version": CONNECTOR_RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": CONNECTOR_TASK_ID,
        "acceptance_id": CONNECTOR_ACCEPTANCE_ID,
        "error_code": safe_code,
        "request_click_count": clicks if clicks in {0, 1} else 1,
        "credential_store_access": False,
        "private_api_calls": False,
        "owned_tab_closed": False,
    }


def _validate_connector_payload(
    payload: object, *, apply: bool
) -> dict[str, Any]:
    success_fields = {
        "schema_version",
        "status",
        "mode",
        "action",
        "visible_ui_only",
        "existing_session_reused",
        "request_click_count",
        "credential_store_access",
        "private_api_calls",
        "owned_tab_closed",
        "task_id",
        "acceptance_id",
        "contract_sha256",
        "model_parameters_sha256",
    }
    failure_fields = {
        "schema_version",
        "status",
        "task_id",
        "acceptance_id",
        "error_code",
        "request_click_count",
        "credential_store_access",
        "private_api_calls",
        "owned_tab_closed",
    }
    if not isinstance(payload, dict):
        raise ChatGPTExportStateError("connector_output_invalid")
    payload_fields = set(payload)
    if payload_fields != success_fields and payload_fields != failure_fields:
        raise ChatGPTExportStateError("connector_output_invalid")
    if (
        payload["schema_version"] != CONNECTOR_RESULT_SCHEMA_VERSION
        or payload["task_id"] != CONNECTOR_TASK_ID
        or payload["acceptance_id"] != CONNECTOR_ACCEPTANCE_ID
    ):
        raise ChatGPTExportStateError("connector_output_invalid")
    clicks = payload.get("request_click_count")
    if type(clicks) is not int or clicks not in {0, 1}:
        raise ChatGPTExportStateError("connector_output_invalid")
    if payload.get("credential_store_access") is not False:
        raise ChatGPTExportStateError("connector_output_invalid")
    if payload.get("private_api_calls") is not False:
        raise ChatGPTExportStateError("connector_output_invalid")
    status = payload["status"]
    if payload_fields == success_fields:
        if any(
            payload[key] is not expected
            for key, expected in {
                "visible_ui_only": True,
                "existing_session_reused": True,
                "credential_store_access": False,
                "private_api_calls": False,
                "owned_tab_closed": True,
            }.items()
        ):
            raise ChatGPTExportStateError("connector_output_invalid")
        _validate_sha256(payload["contract_sha256"], "connector_output_invalid")
        _validate_sha256(
            payload["model_parameters_sha256"], "connector_output_invalid"
        )
        expected = (
            (
                "REQUEST_ACTION_DISPATCHED",
                "request",
                "CONFIRM_EXPORT_CLICKED_ONCE",
                1,
            )
            if apply
            else ("READY_TO_REQUEST", "inspect", "CANCELLED_BEFORE_REQUEST", 0)
        )
        observed = (status, payload["mode"], payload["action"], clicks)
        if observed != expected:
            raise ChatGPTExportStateError("connector_output_invalid")
    elif payload_fields == failure_fields and status == "FAIL":
        _validate_code(payload.get("error_code"), "connector_output_invalid")
        if type(payload["owned_tab_closed"]) is not bool:
            raise ChatGPTExportStateError("connector_output_invalid")
    else:
        raise ChatGPTExportStateError("connector_output_invalid")
    return dict(payload)


def record_export_request_outcome(
    state: dict[str, Any],
    *,
    connector_payload: dict[str, Any],
    occurred_at: str,
) -> tuple[dict[str, Any], bool]:
    current = validate_chatgpt_export_state(state)
    payload = _validate_connector_payload(connector_payload, apply=True)
    if current["status"] != "REQUESTED" or not isinstance(
        current["request"], dict
    ):
        raise ChatGPTExportStateError("export_request_reservation_missing")
    result_hash = _sha256_payload(payload)
    request = current["request"]
    if request["dispatch_status"] != "RESERVED":
        if request["connector_result_sha256"] == result_hash:
            return current, False
        raise ChatGPTExportStateError("export_request_outcome_conflict")
    clicks = payload["request_click_count"]
    error_code = payload.get("error_code") if payload["status"] == "FAIL" else None
    if payload["status"] == "REQUEST_ACTION_DISPATCHED":
        target = "WAITING_FOR_EXPORT"
        dispatch_status = "DISPATCHED"
        reason = "request_dispatched_waiting_for_export"
    elif clicks == 0:
        target = RETRYABLE_STATE
        dispatch_status = "FAILED_BEFORE_CLICK"
        reason = "request_failed_before_click"
    else:
        target = "REQUESTED"
        dispatch_status = "OUTCOME_UNCERTAIN"
        reason = "request_click_outcome_uncertain"
    updated = _append_history(
        current,
        to_state=target,
        event_id=f"request-outcome-{request['request_id']}",
        reason_code=reason,
        evidence_sha256=result_hash,
        occurred_at=occurred_at,
    )
    updated["request"]["dispatch_status"] = dispatch_status
    updated["request"]["request_click_count"] = clicks
    updated["request"]["connector_error_code"] = error_code
    updated["request"]["connector_result_sha256"] = result_hash
    updated["retry_from"] = "IDLE" if target == RETRYABLE_STATE else None
    updated["last_error_code"] = error_code
    return validate_chatgpt_export_state(updated), True


def apply_export_transition(
    state: dict[str, Any],
    *,
    to_state: str,
    event_id: str,
    reason_code: str,
    evidence_sha256: str,
    occurred_at: str,
    expected_revision: int,
) -> tuple[dict[str, Any], bool]:
    current = validate_chatgpt_export_state(state)
    event_id = _validate_event_id(event_id)
    reason_code = _validate_code(reason_code, "export_state_reason_code_invalid")
    evidence_sha256 = _validate_sha256(
        evidence_sha256, "export_state_evidence_invalid"
    )
    occurred_at = _validate_utc(occurred_at, "export_state_occurred_at_invalid")
    existing = next(
        (row for row in current["history"] if row["event_id"] == event_id),
        None,
    )
    if existing is not None:
        same_event = (
            existing["to_state"] == to_state
            and existing["reason_code"] == reason_code
            and existing["evidence_sha256"] == evidence_sha256
        )
        if same_event and current["status"] == to_state:
            return current, False
        raise ChatGPTExportStateError("export_state_event_conflict")
    if type(expected_revision) is not int or expected_revision != current["revision"]:
        raise ChatGPTExportStateError("export_state_revision_conflict")
    if to_state not in EXPORT_STATES:
        raise ChatGPTExportStateError("export_state_target_invalid")
    if current["status"] == HUMAN_AUTH_STATE:
        raise ChatGPTExportStateError("human_auth_resume_deferred")
    if to_state == "REQUESTED":
        raise ChatGPTExportStateError("export_state_transition_invalid")
    if current["status"] == RETRYABLE_STATE:
        allowed = to_state == current["retry_from"]
    else:
        allowed = (current["status"], to_state) in NORMAL_TRANSITIONS
    if to_state in FAILURE_STATES and current["status"] in FAILURE_SOURCES:
        allowed = True
    if not allowed:
        raise ChatGPTExportStateError("export_state_transition_invalid")
    updated = _append_history(
        current,
        to_state=to_state,
        event_id=event_id,
        reason_code=reason_code,
        evidence_sha256=evidence_sha256,
        occurred_at=occurred_at,
    )
    if to_state == RETRYABLE_STATE:
        updated["retry_from"] = current["status"]
        updated["last_error_code"] = reason_code
    elif to_state == HUMAN_AUTH_STATE:
        updated["retry_from"] = None
        updated["last_error_code"] = reason_code
    else:
        updated["retry_from"] = None
        updated["last_error_code"] = None
        if to_state == "IDLE":
            updated["request"] = None
    return validate_chatgpt_export_state(updated), True


def _capture_connector(
    args: Any,
    connector_runner: Callable[[Any], int],
) -> tuple[int, dict[str, Any]]:
    stream = io.StringIO()
    apply = bool(getattr(args, "apply", False))
    uncertain_clicks = 1 if apply else 0
    try:
        with redirect_stdout(stream):
            exit_code = connector_runner(args)
    except Exception:
        return 2, _connector_failure_payload(
            "connector_execution_outcome_uncertain", uncertain_clicks
        )
    content = stream.getvalue()
    if not content or len(content.encode("utf-8")) > MAX_CONNECTOR_OUTPUT_BYTES:
        return 2, _connector_failure_payload(
            "connector_output_invalid", uncertain_clicks
        )
    try:
        payload = json.loads(content)
        payload = _validate_connector_payload(payload, apply=apply)
        normalized_exit = int(exit_code)
        if normalized_exit not in {0, 2} or (
            (payload["status"] == "FAIL") == (normalized_exit == 0)
        ):
            raise ChatGPTExportStateError("connector_output_invalid")
    except (ChatGPTExportStateError, json.JSONDecodeError, ValueError, TypeError):
        return 2, _connector_failure_payload(
            "connector_output_invalid", uncertain_clicks
        )
    return normalized_exit, payload


def _failure_payload(
    code: str,
    *,
    state: dict[str, Any] | None = None,
    request_click_count: int = 0,
    pending_request_suppressed: bool = False,
) -> dict[str, Any]:
    safe_code = code if _CODE_RE.fullmatch(code) else "export_state_failed"
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "error_code": safe_code,
        "export_state": state["status"] if state else "UNKNOWN",
        "state_revision": state["revision"] if state else None,
        "request_click_count": request_click_count
        if request_click_count in {0, 1}
        else 1,
        "pending_request_suppressed": pending_request_suppressed,
        "credential_store_access": False,
        "private_api_calls": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def _augment_connector_payload(
    payload: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    result = dict(payload)
    result.update(
        {
            "state_task_id": TASK_ID,
            "state_acceptance_id": ACCEPTANCE_ID,
            "export_state": state["status"],
            "state_revision": state["revision"],
            "pending_request_suppressed": False,
            "raw_mutation": False,
            "remote_actions": False,
        }
    )
    return result


def execute_stateful_chatgpt_export_request(
    args: Any,
    *,
    connector_runner: Callable[[Any], int] = run_chatgpt_export_request,
    clock: Callable[[], str] = _now_utc,
    request_id_factory: Callable[[], str] = lambda: secrets.token_hex(16),
) -> tuple[int, dict[str, Any]]:
    state: dict[str, Any] | None = None
    request_dispatched = False
    try:
        database_dir = _database_root(Path(args.database_dir))
        load_chatgpt_export_state_contract(database_dir)
        load_chatgpt_export_state_model_parameters(database_dir)
        if bool(getattr(args, "dry_run", False)):
            state = load_chatgpt_export_state(database_dir)
            exit_code, payload = _capture_connector(args, connector_runner)
            return exit_code, _augment_connector_payload(payload, state)
        if not bool(getattr(args, "apply", False)) or not bool(
            getattr(args, "confirm_request", False)
        ):
            raise ChatGPTExportStateError("explicit_request_confirmation_required")
        with export_state_lock(database_dir):
            state = load_chatgpt_export_state(database_dir)
            if state["status"] in PENDING_STATES:
                return 2, _failure_payload(
                    "export_request_pending",
                    state=state,
                    pending_request_suppressed=True,
                )
            reserved, _ = reserve_export_request(
                state,
                request_id=request_id_factory(),
                occurred_at=clock(),
            )
            write_chatgpt_export_state(database_dir, reserved)
            state = reserved
            request_dispatched = True
            exit_code, connector_payload = _capture_connector(args, connector_runner)
            finalized, _ = record_export_request_outcome(
                state,
                connector_payload=connector_payload,
                occurred_at=clock(),
            )
            write_chatgpt_export_state(database_dir, finalized)
            state = finalized
            return exit_code, _augment_connector_payload(connector_payload, state)
    except ChatGPTExportStateError as exc:
        return 2, _failure_payload(
            exc.code,
            state=state,
            request_click_count=1 if request_dispatched else 0,
        )
    except (OSError, UnicodeError, ValueError):
        return 2, _failure_payload(
            "export_state_execution_failed",
            state=state,
            request_click_count=1 if request_dispatched else 0,
        )


def run_stateful_chatgpt_export_request(args: Any) -> int:
    exit_code, payload = execute_stateful_chatgpt_export_request(args)
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return exit_code


def _state_summary(state: dict[str, Any]) -> dict[str, Any]:
    request = state["request"] if isinstance(state["request"], dict) else None
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "export_state": state["status"],
        "state_revision": state["revision"],
        "pending_request": state["status"] in PENDING_STATES,
        "request_id": request["request_id"] if request else None,
        "request_dispatch_status": request["dispatch_status"] if request else None,
        "state_sha256": _sha256_payload(state),
        "raw_mutation": False,
        "remote_actions": False,
    }


def run_chatgpt_export_state(args: Any) -> int:
    state: dict[str, Any] | None = None
    try:
        database_dir = _database_root(Path(args.database_dir))
        load_chatgpt_export_state_contract(database_dir)
        load_chatgpt_export_state_model_parameters(database_dir)
        inspect = bool(getattr(args, "inspect", False))
        apply = bool(getattr(args, "apply", False))
        if inspect == apply:
            raise ChatGPTExportStateError("export_state_mode_invalid")
        with export_state_lock(database_dir):
            state = load_chatgpt_export_state(database_dir)
            if inspect:
                payload = _state_summary(state)
                payload["action"] = "INSPECTED_NO_CHANGES"
                print(
                    json.dumps(
                        payload,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                )
                return 0
            required = {
                "to_state": getattr(args, "to_state", None),
                "expected_revision": getattr(args, "expected_revision", None),
                "event_id": getattr(args, "event_id", None),
                "reason_code": getattr(args, "reason_code", None),
                "evidence_sha256": getattr(args, "evidence_sha256", None),
            }
            if any(value is None for value in required.values()):
                raise ChatGPTExportStateError("export_state_apply_arguments_required")
            updated, changed = apply_export_transition(
                state,
                to_state=required["to_state"],
                event_id=required["event_id"],
                reason_code=required["reason_code"],
                evidence_sha256=required["evidence_sha256"],
                occurred_at=_now_utc(),
                expected_revision=required["expected_revision"],
            )
            if changed:
                write_chatgpt_export_state(database_dir, updated)
            payload = _state_summary(updated)
            payload["action"] = "TRANSITION_APPLIED" if changed else "NO_CHANGES"
            print(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
            )
            return 0
    except ChatGPTExportStateError as exc:
        print(
            json.dumps(
                _failure_payload(exc.code, state=state),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    except (OSError, UnicodeError, ValueError):
        print(
            json.dumps(
                _failure_payload("export_state_execution_failed", state=state),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2


__all__ = (
    "CONTRACT_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "EXPORT_STATES",
    "HUMAN_AUTH_STATE",
    "MODEL_RELATIVE",
    "PENDING_STATES",
    "STATE_RELATIVE",
    "ChatGPTExportStateError",
    "apply_export_transition",
    "build_initial_export_state",
    "execute_stateful_chatgpt_export_request",
    "export_state_lock",
    "load_chatgpt_export_state",
    "load_chatgpt_export_state_contract",
    "load_chatgpt_export_state_model_parameters",
    "record_export_request_outcome",
    "reserve_export_request",
    "run_chatgpt_export_state",
    "run_stateful_chatgpt_export_request",
    "validate_chatgpt_export_state",
    "validate_chatgpt_export_state_contract",
    "validate_chatgpt_export_state_model_parameters",
    "write_chatgpt_export_state",
)
