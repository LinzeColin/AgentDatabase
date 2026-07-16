"""Human-only pause and resume boundary for ChatGPT export authentication."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .chatgpt_export_state import (
    AUTH_CHALLENGE_CODES,
    HUMAN_AUTH_STATE,
    MAX_STATE_BYTES,
    ChatGPTExportStateError,
    _database_root,
    _now_utc,
    _read_json,
    _sha256_payload,
    export_state_lock,
    human_auth_resume_target,
    load_chatgpt_export_state,
    load_chatgpt_export_state_contract,
    load_chatgpt_export_state_model_parameters,
    pause_export_for_human_auth,
    resume_export_after_human_auth,
    write_chatgpt_export_state,
)


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_human_auth.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_human_auth.v1_2_1_s08_p1_t3.json"
)
TASK_ID = "S08-P1-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P1-T3"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_human_auth_contract.v1_2_1_s08_p1_t3"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_human_auth_model.v1_2_1_s08_p1_t3"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_human_auth_result.v1_2_1_s08_p1_t3"
)
PHASE_BOUNDARY = {
    "implements_human_auth_resume": True,
    "discovers_notifications": False,
    "downloads_export": False,
    "writes_raw_archive": False,
    "commits_or_pushes": False,
    "deploys": False,
    "next_task": "S08-P2-T1",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "state_path": "data/sync_state/chatgpt.json",
    "challenge_detection": {
        "codes": list(AUTH_CHALLENGE_CODES),
        "visible_exact_markers_only": True,
        "official_auth_url_classification": True,
        "captures_account_content": False,
    },
    "pause": {
        "target_state": HUMAN_AUTH_STATE,
        "request_click_count_required": 0,
        "automatic_auth_action": False,
    },
    "resume": {
        "explicit_human_confirmation_required": True,
        "evidence_sha256_required": True,
        "optimistic_revision_required": True,
        "request_origin_target": "FAILED_RETRYABLE",
        "nonrequest_origin_target": "pre_auth_state",
        "automatic_retry": False,
    },
    "cli": {
        "command": "chatgpt-export-auth",
        "modes": ["--inspect", "--pause", "--resume"],
        "pause_requires": [
            "--challenge",
            "--expected-revision",
            "--event-id",
            "--evidence-sha256",
        ],
        "resume_requires": [
            "--confirm-human-auth-complete",
            "--expected-revision",
            "--event-id",
            "--evidence-sha256",
        ],
        "inspect_is_read_only": True,
    },
    "security": {
        "automates_authentication": False,
        "bypasses_login_2fa_captcha": False,
        "reads_credentials": False,
        "stores_credentials_or_account_content": False,
        "uses_private_api": False,
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
    "purpose": "Pause on an exact authentication challenge and resume only after explicit human completion without automating or bypassing platform security.",
    "parameters": {
        "challenge_type_count": 4,
        "maximum_evidence_sha256_characters": 64,
        "automatic_auth_attempts": 0,
        "automatic_resume_attempts": 0,
        "automatic_request_retries_after_resume": 0,
        "lock_wait_seconds": 0,
    },
    "formula": "resume_permitted = state=FAILED_NEEDS_HUMAN_AUTH AND explicit_human_confirmation AND revision_match AND evidence_sha256_valid AND last_pause_valid; automatic_auth_actions=0; automatic_request_retries=0",
    "parameter_rationale": {
        "challenge_type_count": "Only login, two-factor, CAPTCHA and account-confirmation challenges are recognized.",
        "maximum_evidence_sha256_characters": "Evidence is represented only by a fixed SHA-256 digest, never by account or challenge content.",
        "automatic_auth_attempts": "Authentication remains a human-only action.",
        "automatic_resume_attempts": "Resume requires one explicit operator command after human completion.",
        "automatic_request_retries_after_resume": "A pre-click request pause resumes to a retryable state and requires a new explicit request.",
        "lock_wait_seconds": "A nonblocking lock fails closed under concurrent access.",
    },
    "failure_semantics": "Unknown challenges, missing confirmation, malformed evidence, stale revision, invalid pause history and concurrent access fail closed without browser or remote action.",
    "calibration_boundary": "S08-P1-T3 owns human-auth pause and explicit resume only. S08-P2/P3 own notification, download, archive and push effects.",
}


def validate_chatgpt_export_human_auth_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise ChatGPTExportStateError("human_auth_contract_drift")
    return dict(payload)


def validate_chatgpt_export_human_auth_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTExportStateError("human_auth_model_drift")
    return dict(payload)


def load_chatgpt_export_human_auth_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_human_auth_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_STATE_BYTES,
            code="human_auth_contract_unreadable",
        )
    )


def load_chatgpt_export_human_auth_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_human_auth_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_STATE_BYTES,
            code="human_auth_model_unreadable",
        )
    )


def _result_payload(state: dict[str, Any], action: str) -> dict[str, Any]:
    required = state["status"] == HUMAN_AUTH_STATE
    challenge = state["last_error_code"] if required else None
    resume_target = human_auth_resume_target(state) if required else None
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "action": action,
        "export_state": state["status"],
        "state_revision": state["revision"],
        "state_sha256": _sha256_payload(state),
        "human_auth_required": required,
        "human_auth_challenge": challenge,
        "human_auth_resume_target": resume_target,
        "automatic_auth_action": False,
        "automatic_retry": False,
        "credential_store_access": False,
        "private_api_calls": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def _failure_payload(
    code: str, state: dict[str, Any] | None = None
) -> dict[str, Any]:
    required = bool(state and state["status"] == HUMAN_AUTH_STATE)
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "error_code": code,
        "export_state": state["status"] if state else "UNKNOWN",
        "state_revision": state["revision"] if state else None,
        "human_auth_required": required,
        "human_auth_challenge": state["last_error_code"] if required else None,
        "automatic_auth_action": False,
        "automatic_retry": False,
        "credential_store_access": False,
        "private_api_calls": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def run_chatgpt_export_human_auth(args: Any) -> int:
    state: dict[str, Any] | None = None
    try:
        database_dir = _database_root(Path(args.database_dir))
        load_chatgpt_export_state_contract(database_dir)
        load_chatgpt_export_state_model_parameters(database_dir)
        load_chatgpt_export_human_auth_contract(database_dir)
        load_chatgpt_export_human_auth_model_parameters(database_dir)
        modes = [
            bool(getattr(args, "inspect", False)),
            bool(getattr(args, "pause", False)),
            bool(getattr(args, "resume", False)),
        ]
        if sum(modes) != 1:
            raise ChatGPTExportStateError("human_auth_mode_invalid")
        with export_state_lock(database_dir):
            state = load_chatgpt_export_state(database_dir)
            if modes[0]:
                if any(
                    (
                        getattr(args, "challenge", None) is not None,
                        getattr(args, "expected_revision", None) is not None,
                        getattr(args, "event_id", None) is not None,
                        getattr(args, "evidence_sha256", None) is not None,
                        bool(getattr(args, "confirm_human_auth_complete", False)),
                    )
                ):
                    raise ChatGPTExportStateError(
                        "human_auth_inspect_arguments_forbidden"
                    )
                payload = _result_payload(state, "INSPECTED_NO_CHANGES")
            else:
                required = {
                    "expected_revision": getattr(args, "expected_revision", None),
                    "event_id": getattr(args, "event_id", None),
                    "evidence_sha256": getattr(args, "evidence_sha256", None),
                }
                if any(value is None for value in required.values()):
                    raise ChatGPTExportStateError(
                        "human_auth_transition_arguments_required"
                    )
                if modes[1]:
                    challenge = getattr(args, "challenge", None)
                    if challenge is None or bool(
                        getattr(args, "confirm_human_auth_complete", False)
                    ):
                        raise ChatGPTExportStateError(
                            "human_auth_transition_arguments_required"
                        )
                    updated, changed = pause_export_for_human_auth(
                        state,
                        challenge=challenge,
                        event_id=required["event_id"],
                        evidence_sha256=required["evidence_sha256"],
                        occurred_at=_now_utc(),
                        expected_revision=required["expected_revision"],
                    )
                    action = "PAUSED_FOR_HUMAN_AUTH" if changed else "NO_CHANGES"
                else:
                    if getattr(args, "challenge", None) is not None:
                        raise ChatGPTExportStateError(
                            "human_auth_resume_arguments_invalid"
                        )
                    updated, changed = resume_export_after_human_auth(
                        state,
                        event_id=required["event_id"],
                        evidence_sha256=required["evidence_sha256"],
                        occurred_at=_now_utc(),
                        expected_revision=required["expected_revision"],
                        explicit_confirmation=bool(
                            getattr(args, "confirm_human_auth_complete", False)
                        ),
                    )
                    action = "RESUMED_AFTER_HUMAN_AUTH" if changed else "NO_CHANGES"
                if changed:
                    write_chatgpt_export_state(database_dir, updated)
                state = updated
                payload = _result_payload(state, action)
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except ChatGPTExportStateError as exc:
        print(
            json.dumps(
                _failure_payload(exc.code, state),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    except (OSError, UnicodeError, ValueError):
        print(
            json.dumps(
                _failure_payload("human_auth_execution_failed", state),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2


__all__ = (
    "AUTH_CHALLENGE_CODES",
    "CONTRACT_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "MODEL_RELATIVE",
    "load_chatgpt_export_human_auth_contract",
    "load_chatgpt_export_human_auth_model_parameters",
    "run_chatgpt_export_human_auth",
    "validate_chatgpt_export_human_auth_contract",
    "validate_chatgpt_export_human_auth_model_parameters",
)
