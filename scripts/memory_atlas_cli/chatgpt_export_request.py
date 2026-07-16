"""Official ChatGPT Data Export request connector wrapper."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_request.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_request.v1_2_1_s08_p1_t1.json"
)
CONNECTOR_RELATIVE = Path(
    "apps/memory-atlas/scripts/chatgpt_export_request_connector.cjs"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1"
)
_ERROR_CODE_PATTERN = re.compile(r"^[a-z][a-z0-9_]{0,95}$")

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": "memory_atlas.chatgpt_export_request_contract.v1_2_1_s08_p1_t1",
    "task_id": "S08-P1-T1",
    "acceptance_id": "ACC-MA-V121-S08-P1-T1",
    "source_id": "chatgpt",
    "official_documentation": "https://help.openai.com/en/articles/7260999-how-do-i-export-my-chatgpt-history-and-data",
    "browser_transport": {
        "kind": "existing_chrome_loopback_cdp",
        "existing_session_only": True,
        "requires_explicit_endpoint": True,
        "allowed_schemes": ["http"],
        "allowed_hosts": ["127.0.0.1", "::1"],
        "opens_task_owned_tab": True,
        "closes_task_owned_tab": True,
    },
    "visible_ui": {
        "origin": "https://chatgpt.com",
        "steps": [
            "open_profile_menu",
            "open_settings",
            "open_data_controls",
            "open_export_confirmation",
        ],
        "confirmation_dialog_name": "Request data export - are you sure?",
        "inspect_action": "cancel_before_request",
        "request_action": "confirm_export_once",
    },
    "security": {
        "reads_browser_credentials": False,
        "reads_cookie_store": False,
        "reads_storage_state": False,
        "launches_persistent_profile": False,
        "uses_private_api": False,
        "captures_account_identity": False,
        "captures_page_content": False,
        "submits_request_without_explicit_confirmation": False,
    },
    "cli": {
        "command": "request-chatgpt-export",
        "inspect_flags": ["--dry-run"],
        "request_flags": ["--apply", "--confirm-request"],
        "machine_output": "stdout_json",
        "state_persistence": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": {
        "implements_request_state_machine": False,
        "implements_pending_request_dedupe": False,
        "implements_human_auth_resume": False,
        "downloads_export": False,
        "writes_raw_archive": False,
        "fetches_or_pushes": False,
        "deploys": False,
        "next_task": "S08-P1-T2",
    },
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": "memory_atlas.chatgpt_export_request_model.v1_2_1_s08_p1_t1",
    "task_id": "S08-P1-T1",
    "acceptance_id": "ACC-MA-V121-S08-P1-T1",
    "model_id": "MOD-009",
    "formula_id": "FORM-009",
    "purpose": "Bound one official ChatGPT Data Export request to visible UI in an existing logged-in browser session without reading browser credentials or using a private API.",
    "parameters": {
        "connection_timeout_seconds": 15,
        "navigation_timeout_seconds": 30,
        "action_timeout_seconds": 15,
        "maximum_browser_contexts": 1,
        "maximum_owned_tabs": 1,
        "maximum_confirm_clicks": 1,
        "maximum_machine_output_bytes": 16384,
    },
    "formula": "connector_pass = loopback_cdp AND existing_session AND visible_chatgpt_origin AND unique_visible_steps AND credential_reads=0 AND private_api_calls=0 AND owned_tabs<=1 AND confirm_clicks<=1 AND sanitized_output",
    "parameter_rationale": {
        "connection_timeout_seconds": "A short loopback-only connection budget fails closed when the existing browser is unavailable.",
        "navigation_timeout_seconds": "Thirty seconds covers an authenticated ChatGPT settings load without adding retries.",
        "action_timeout_seconds": "Fifteen seconds bounds each visible UI action and exposes UI drift instead of guessing selectors.",
        "maximum_browser_contexts": "Exactly one existing browser context avoids guessing which signed-in profile owns the request.",
        "maximum_owned_tabs": "The connector creates and closes one task-owned tab while preserving all user tabs.",
        "maximum_confirm_clicks": "One click is the hard upper bound; retry and pending-request suppression belong to S08-P1-T2.",
        "maximum_machine_output_bytes": "A 16 KiB JSON ceiling prevents page content or browser diagnostics from leaking into evidence.",
    },
    "failure_semantics": "Endpoint, context, origin, selector uniqueness, visibility, navigation, explicit confirmation, output schema, or browser action uncertainty fails closed. No automatic retry, credential inspection, private API call, request state persistence, download, raw write, Git remote action, or deployment is allowed.",
    "calibration_boundary": "S08-P1-T1 implements and verifies the request connector only. S08-P1-T2 owns durable REQUESTED-to-terminal state and pending dedupe; S08-P1-T3 owns human-auth pause and resume.",
}


class ChatGPTExportRequestError(RuntimeError):
    """Raised when the request connector cannot proceed safely."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def _read_json(path: Path, error_code: str) -> dict[str, Any]:
    if path.is_symlink() or not path.is_file():
        raise ChatGPTExportRequestError(error_code)
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ChatGPTExportRequestError(error_code) from exc
    if not isinstance(payload, dict):
        raise ChatGPTExportRequestError(error_code)
    return payload


def validate_chatgpt_export_request_contract(payload: object) -> None:
    if payload != EXPECTED_CONTRACT:
        raise ChatGPTExportRequestError("export_request_contract_drift")


def validate_chatgpt_export_request_model_parameters(payload: object) -> None:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTExportRequestError("export_request_model_drift")


def load_chatgpt_export_request_contract(database_dir: Path) -> dict[str, Any]:
    payload = _read_json(
        database_dir.resolve() / CONTRACT_RELATIVE,
        "export_request_contract_unavailable",
    )
    validate_chatgpt_export_request_contract(payload)
    return payload


def load_chatgpt_export_request_model_parameters(database_dir: Path) -> dict[str, Any]:
    payload = _read_json(
        database_dir.resolve() / MODEL_RELATIVE,
        "export_request_model_unavailable",
    )
    validate_chatgpt_export_request_model_parameters(payload)
    return payload


def normalize_loopback_cdp_endpoint(value: object) -> str:
    if not isinstance(value, str) or not value or len(value) > 256:
        raise ChatGPTExportRequestError("cdp_endpoint_invalid")
    parsed = urlsplit(value)
    try:
        port = parsed.port
    except ValueError as exc:
        raise ChatGPTExportRequestError("cdp_endpoint_invalid") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname not in {"127.0.0.1", "::1"}
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
        or parsed.path not in {"", "/"}
        or port is None
    ):
        raise ChatGPTExportRequestError("cdp_endpoint_invalid")
    host = f"[{parsed.hostname}]" if parsed.hostname == "::1" else parsed.hostname
    return f"http://{host}:{port}"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _failure(
    code: str,
    *,
    request_click_count: int = 0,
    owned_tab_closed: bool = False,
) -> dict[str, Any]:
    safe_code = code if _ERROR_CODE_PATTERN.fullmatch(code) else "connector_failed"
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": "S08-P1-T1",
        "acceptance_id": "ACC-MA-V121-S08-P1-T1",
        "error_code": safe_code,
        "request_click_count": request_click_count if request_click_count in {0, 1} else 0,
        "credential_store_access": False,
        "private_api_calls": False,
        "owned_tab_closed": owned_tab_closed,
    }


def _print_payload(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def _parse_connector_result(
    content: str,
    *,
    maximum_bytes: int,
) -> dict[str, Any]:
    encoded = content.encode("utf-8", errors="strict")
    if not encoded or len(encoded) > maximum_bytes:
        raise ChatGPTExportRequestError("connector_output_invalid")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ChatGPTExportRequestError("connector_output_invalid") from exc
    required = {
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
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ChatGPTExportRequestError("connector_output_invalid")
    if payload["schema_version"] != RESULT_SCHEMA_VERSION:
        raise ChatGPTExportRequestError("connector_output_invalid")
    if payload["status"] not in {"READY_TO_REQUEST", "REQUEST_ACTION_DISPATCHED"}:
        raise ChatGPTExportRequestError("connector_output_invalid")
    if type(payload["request_click_count"]) is not int or payload["request_click_count"] not in {0, 1}:
        raise ChatGPTExportRequestError("connector_output_invalid")
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
        raise ChatGPTExportRequestError("connector_output_invalid")
    outcome = (
        payload["status"],
        payload["mode"],
        payload["action"],
        payload["request_click_count"],
    )
    if outcome not in {
        ("READY_TO_REQUEST", "inspect", "CANCELLED_BEFORE_REQUEST", 0),
        ("REQUEST_ACTION_DISPATCHED", "request", "CONFIRM_EXPORT_CLICKED_ONCE", 1),
    }:
        raise ChatGPTExportRequestError("connector_output_invalid")
    return payload


def _parse_connector_failure(
    content: str,
    *,
    maximum_bytes: int,
) -> dict[str, Any]:
    encoded = content.encode("utf-8", errors="strict")
    if not encoded or len(encoded) > maximum_bytes:
        raise ChatGPTExportRequestError("connector_output_invalid")
    try:
        payload = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ChatGPTExportRequestError("connector_output_invalid") from exc
    required = {
        "schema_version",
        "status",
        "error_code",
        "request_click_count",
        "credential_store_access",
        "private_api_calls",
        "owned_tab_closed",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ChatGPTExportRequestError("connector_output_invalid")
    if (
        payload["schema_version"] != RESULT_SCHEMA_VERSION
        or payload["status"] != "FAIL"
        or not isinstance(payload["error_code"], str)
        or not _ERROR_CODE_PATTERN.fullmatch(payload["error_code"])
        or type(payload["request_click_count"]) is not int
        or payload["request_click_count"] not in {0, 1}
        or type(payload["owned_tab_closed"]) is not bool
        or payload["credential_store_access"] is not False
        or payload["private_api_calls"] is not False
    ):
        raise ChatGPTExportRequestError("connector_output_invalid")
    return payload


def run_chatgpt_export_request(args: Any) -> int:
    request_effect_possible = False
    try:
        database_dir = Path(args.database_dir).expanduser().resolve()
        contract = load_chatgpt_export_request_contract(database_dir)
        model = load_chatgpt_export_request_model_parameters(database_dir)
        endpoint = normalize_loopback_cdp_endpoint(args.cdp_endpoint)
        dry_run = bool(args.dry_run)
        apply = bool(args.apply)
        confirm = bool(args.confirm_request)
        if dry_run == apply:
            raise ChatGPTExportRequestError("request_mode_invalid")
        if dry_run and confirm:
            raise ChatGPTExportRequestError("request_confirmation_invalid_for_dry_run")
        if apply and not confirm:
            raise ChatGPTExportRequestError("explicit_request_confirmation_required")

        connector_path = database_dir / CONNECTOR_RELATIVE
        if connector_path.is_symlink() or not connector_path.is_file():
            raise ChatGPTExportRequestError("connector_entrypoint_unavailable")
        mode = "inspect" if dry_run else "request"
        command = [
            "node",
            str(connector_path),
            "--cdp-endpoint",
            endpoint,
            "--mode",
            mode,
        ]
        if apply:
            command.append("--confirm-request")
        child_env = {
            key: os.environ[key]
            for key in ("PATH", "LANG", "LC_ALL")
            if key in os.environ
        }
        request_effect_possible = apply
        completed = subprocess.run(
            command,
            cwd=database_dir / "apps/memory-atlas",
            env=child_env,
            text=True,
            capture_output=True,
            check=False,
            timeout=int(model["parameters"]["navigation_timeout_seconds"])
            + int(model["parameters"]["connection_timeout_seconds"])
            + 30,
        )
        if completed.returncode != 0:
            failure = _parse_connector_failure(
                completed.stdout,
                maximum_bytes=int(model["parameters"]["maximum_machine_output_bytes"]),
            )
            failure.update(
                {
                    "task_id": contract["task_id"],
                    "acceptance_id": contract["acceptance_id"],
                }
            )
            _print_payload(failure)
            return 2
        result = _parse_connector_result(
            completed.stdout,
            maximum_bytes=int(model["parameters"]["maximum_machine_output_bytes"]),
        )
        expected_status = "READY_TO_REQUEST" if dry_run else "REQUEST_ACTION_DISPATCHED"
        expected_clicks = 0 if dry_run else 1
        if result["status"] != expected_status or result["request_click_count"] != expected_clicks:
            raise ChatGPTExportRequestError("connector_outcome_mismatch")
        result.update(
            {
                "task_id": contract["task_id"],
                "acceptance_id": contract["acceptance_id"],
                "contract_sha256": _sha256(database_dir / CONTRACT_RELATIVE),
                "model_parameters_sha256": _sha256(database_dir / MODEL_RELATIVE),
            }
        )
        _print_payload(result)
        return 0
    except ChatGPTExportRequestError as exc:
        _print_payload(
            _failure(exc.code, request_click_count=1 if request_effect_possible else 0)
        )
        return 2
    except (OSError, subprocess.SubprocessError, UnicodeError, ValueError):
        code = (
            "connector_execution_outcome_uncertain"
            if request_effect_possible
            else "connector_execution_failed"
        )
        _print_payload(_failure(code, request_click_count=1 if request_effect_possible else 0))
        return 2


__all__ = (
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "ChatGPTExportRequestError",
    "load_chatgpt_export_request_contract",
    "load_chatgpt_export_request_model_parameters",
    "normalize_loopback_cdp_endpoint",
    "run_chatgpt_export_request",
    "validate_chatgpt_export_request_contract",
    "validate_chatgpt_export_request_model_parameters",
)
