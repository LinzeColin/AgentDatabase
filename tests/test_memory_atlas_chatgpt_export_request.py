from __future__ import annotations

import copy
import io
import json
import subprocess
import sys
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_request import (  # noqa: E402
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    ChatGPTExportRequestError,
    load_chatgpt_export_request_contract,
    load_chatgpt_export_request_model_parameters,
    normalize_loopback_cdp_endpoint,
    run_chatgpt_export_request,
    validate_chatgpt_export_request_contract,
    validate_chatgpt_export_request_model_parameters,
)


class ChatGPTExportRequestTests(unittest.TestCase):
    def test_contract_and_model_freeze_visible_ui_and_no_credential_boundary(self) -> None:
        contract = load_chatgpt_export_request_contract(ROOT)
        model = load_chatgpt_export_request_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["task_id"], "S08-P1-T1")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S08-P1-T1")
        self.assertTrue(contract["browser_transport"]["existing_session_only"])
        self.assertFalse(contract["security"]["reads_browser_credentials"])
        self.assertFalse(contract["security"]["uses_private_api"])
        self.assertFalse(contract["security"]["launches_persistent_profile"])
        self.assertEqual(model["parameters"]["maximum_confirm_clicks"], 1)

        mutated_contract = copy.deepcopy(contract)
        mutated_contract["security"]["reads_browser_credentials"] = True
        with self.assertRaises(ChatGPTExportRequestError):
            validate_chatgpt_export_request_contract(mutated_contract)

        mutated_model = copy.deepcopy(model)
        mutated_model["parameters"]["maximum_confirm_clicks"] = 2
        with self.assertRaises(ChatGPTExportRequestError):
            validate_chatgpt_export_request_model_parameters(mutated_model)

    def test_cdp_endpoint_must_be_plain_loopback_without_embedded_secret(self) -> None:
        self.assertEqual(
            normalize_loopback_cdp_endpoint("http://127.0.0.1:9222"),
            "http://127.0.0.1:9222",
        )
        self.assertEqual(
            normalize_loopback_cdp_endpoint("http://[::1]:9444"),
            "http://[::1]:9444",
        )
        for value in (
            "https://127.0.0.1:9222",
            "http://localhost:9222",
            "http://192.168.1.20:9222",
            "http://user:secret@127.0.0.1:9222",
            "http://127.0.0.1:9222/devtools/browser/abc",
            "http://127.0.0.1:9222?access_token=secret",
            "http://127.0.0.1",
            "http://127.0.0.1:not-a-port",
        ):
            with self.subTest(value=value), self.assertRaises(ChatGPTExportRequestError):
                normalize_loopback_cdp_endpoint(value)

    def test_dry_run_delegates_to_inspect_mode_and_emits_sanitized_result(self) -> None:
        connector_payload = {
            "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
            "status": "READY_TO_REQUEST",
            "mode": "inspect",
            "action": "CANCELLED_BEFORE_REQUEST",
            "visible_ui_only": True,
            "existing_session_reused": True,
            "request_click_count": 0,
            "credential_store_access": False,
            "private_api_calls": False,
            "owned_tab_closed": True,
        }
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(connector_payload) + "\n",
            stderr="",
        )
        stdout = io.StringIO()
        with mock.patch("memory_atlas_cli.chatgpt_export_request.subprocess.run", return_value=completed) as runner:
            with redirect_stdout(stdout):
                exit_code = run_chatgpt_export_request(
                    Namespace(
                        database_dir=ROOT,
                        cdp_endpoint="http://127.0.0.1:9222",
                        dry_run=True,
                        apply=False,
                        confirm_request=False,
                    )
                )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["status"], "READY_TO_REQUEST")
        self.assertEqual(payload["action"], "CANCELLED_BEFORE_REQUEST")
        command = runner.call_args.args[0]
        self.assertEqual(command[0], "node")
        self.assertIn("--mode", command)
        self.assertEqual(command[command.index("--mode") + 1], "inspect")
        self.assertNotIn("--confirm-request", command)
        self.assertNotIn("secret", json.dumps(payload).lower())

    def test_success_payload_requires_the_exact_mode_action_pair(self) -> None:
        connector_payload = {
            "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
            "status": "READY_TO_REQUEST",
            "mode": "inspect",
            "action": "CONFIRM_EXPORT_CLICKED_ONCE",
            "visible_ui_only": True,
            "existing_session_reused": True,
            "request_click_count": 0,
            "credential_store_access": False,
            "private_api_calls": False,
            "owned_tab_closed": True,
        }
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=0,
            stdout=json.dumps(connector_payload) + "\n",
            stderr="",
        )
        stdout = io.StringIO()
        with mock.patch(
            "memory_atlas_cli.chatgpt_export_request.subprocess.run",
            return_value=completed,
        ):
            with redirect_stdout(stdout):
                exit_code = run_chatgpt_export_request(
                    Namespace(
                        database_dir=ROOT,
                        cdp_endpoint="http://127.0.0.1:9222",
                        dry_run=True,
                        apply=False,
                        confirm_request=False,
                    )
                )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error_code"], "connector_output_invalid")
        self.assertEqual(payload["request_click_count"], 0)

    def test_apply_requires_explicit_confirmation_before_browser_process(self) -> None:
        stdout = io.StringIO()
        with mock.patch("memory_atlas_cli.chatgpt_export_request.subprocess.run") as runner:
            with redirect_stdout(stdout):
                exit_code = run_chatgpt_export_request(
                    Namespace(
                        database_dir=ROOT,
                        cdp_endpoint="http://127.0.0.1:9222",
                        dry_run=False,
                        apply=True,
                        confirm_request=False,
                    )
                )

        self.assertEqual(exit_code, 2)
        self.assertFalse(runner.called)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error_code"], "explicit_request_confirmation_required")
        self.assertEqual(payload["request_click_count"], 0)

    def test_browser_failure_preserves_a_confirm_click_attempt(self) -> None:
        connector_payload = {
            "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
            "status": "FAIL",
            "error_code": "owned_tab_cleanup_failed",
            "request_click_count": 1,
            "credential_store_access": False,
            "private_api_calls": False,
            "owned_tab_closed": False,
        }
        completed = subprocess.CompletedProcess(
            args=[],
            returncode=2,
            stdout=json.dumps(connector_payload) + "\n",
            stderr="ignored browser diagnostic",
        )
        stdout = io.StringIO()
        with mock.patch("memory_atlas_cli.chatgpt_export_request.subprocess.run", return_value=completed):
            with redirect_stdout(stdout):
                exit_code = run_chatgpt_export_request(
                    Namespace(
                        database_dir=ROOT,
                        cdp_endpoint="http://127.0.0.1:9222",
                        dry_run=False,
                        apply=True,
                        confirm_request=True,
                    )
                )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error_code"], "owned_tab_cleanup_failed")
        self.assertEqual(payload["request_click_count"], 1)
        self.assertFalse(payload["owned_tab_closed"])
        self.assertNotIn("browser diagnostic", stdout.getvalue())

    def test_apply_timeout_reports_the_conservative_click_upper_bound(self) -> None:
        stdout = io.StringIO()
        timeout = subprocess.TimeoutExpired(cmd=["node", "connector.cjs"], timeout=75)
        with mock.patch(
            "memory_atlas_cli.chatgpt_export_request.subprocess.run",
            side_effect=timeout,
        ):
            with redirect_stdout(stdout):
                exit_code = run_chatgpt_export_request(
                    Namespace(
                        database_dir=ROOT,
                        cdp_endpoint="http://127.0.0.1:9222",
                        dry_run=False,
                        apply=True,
                        confirm_request=True,
                    )
                )

        self.assertEqual(exit_code, 2)
        payload = json.loads(stdout.getvalue())
        self.assertEqual(payload["error_code"], "connector_execution_outcome_uncertain")
        self.assertEqual(payload["request_click_count"], 1)

    def test_real_browser_fixture_covers_inspect_submit_and_fail_closed_paths(self) -> None:
        result = subprocess.run(
            ["node", "tests/chatgpt_export_request_connector.test.cjs"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
            timeout=120,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["scenario_count"], 10)
        self.assertEqual(
            payload["human_auth_challenges"],
            {
                "login": "login_required",
                "two-factor": "two_factor_required",
                "captcha": "captcha_required",
                "account-confirmation": "account_confirmation_required",
            },
        )
        self.assertEqual(
            payload["official_auth_url_checks"],
            {
                "https://auth.openai.com/u/login": "login_required",
                "https://auth.openai.com/u/login/mfa": "two_factor_required",
                "https://auth.openai.com/captcha": "captcha_required",
                "https://auth.openai.com/u/verify": "account_confirmation_required",
            },
        )
        self.assertEqual(payload["request_clicks"], {"inspect": 0, "request": 1})


if __name__ == "__main__":
    unittest.main()
