from __future__ import annotations

import copy
import io
import json
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_human_auth import (  # noqa: E402
    AUTH_CHALLENGE_CODES,
    CONTRACT_RELATIVE as AUTH_CONTRACT_RELATIVE,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    MODEL_RELATIVE as AUTH_MODEL_RELATIVE,
    load_chatgpt_export_human_auth_contract,
    load_chatgpt_export_human_auth_model_parameters,
    run_chatgpt_export_human_auth,
    validate_chatgpt_export_human_auth_contract,
    validate_chatgpt_export_human_auth_model_parameters,
)
from memory_atlas_cli.chatgpt_export_state import (  # noqa: E402
    CONTRACT_RELATIVE as STATE_CONTRACT_RELATIVE,
    HUMAN_AUTH_STATE,
    MODEL_RELATIVE as STATE_MODEL_RELATIVE,
    ChatGPTExportStateError,
    apply_export_transition,
    build_initial_export_state,
    execute_stateful_chatgpt_export_request,
    load_chatgpt_export_state,
    pause_export_for_human_auth,
    record_export_request_outcome,
    reserve_export_request,
    resume_export_after_human_auth,
    write_chatgpt_export_state,
)


NOW = "2026-07-17T00:00:00Z"
LATER = "2026-07-17T00:01:00Z"
EVIDENCE = "a" * 64


def connector_payload(*, status: str, clicks: int, error_code: str | None = None) -> dict:
    if status == "PASS":
        return {
            "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
            "status": "REQUEST_ACTION_DISPATCHED",
            "mode": "request",
            "action": "CONFIRM_EXPORT_CLICKED_ONCE",
            "visible_ui_only": True,
            "existing_session_reused": True,
            "request_click_count": clicks,
            "credential_store_access": False,
            "private_api_calls": False,
            "owned_tab_closed": True,
            "task_id": "S08-P1-T1",
            "acceptance_id": "ACC-MA-V121-S08-P1-T1",
            "contract_sha256": "b" * 64,
            "model_parameters_sha256": "c" * 64,
        }
    return {
        "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
        "status": "FAIL",
        "task_id": "S08-P1-T1",
        "acceptance_id": "ACC-MA-V121-S08-P1-T1",
        "error_code": error_code or "browser_connection_failed",
        "request_click_count": clicks,
        "credential_store_access": False,
        "private_api_calls": False,
        "owned_tab_closed": True,
    }


class HumanAuthFixture:
    def __init__(self, root: Path):
        self.root = root
        for relative in (
            STATE_CONTRACT_RELATIVE,
            STATE_MODEL_RELATIVE,
            AUTH_CONTRACT_RELATIVE,
            AUTH_MODEL_RELATIVE,
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        write_chatgpt_export_state(root, build_initial_export_state())

    @property
    def state_path(self) -> Path:
        return self.root / "data/sync_state/chatgpt.json"


class ChatGPTExportHumanAuthTests(unittest.TestCase):
    def test_contract_and_model_freeze_human_only_security_boundary(self) -> None:
        contract = load_chatgpt_export_human_auth_contract(ROOT)
        model = load_chatgpt_export_human_auth_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(
            AUTH_CHALLENGE_CODES,
            (
                "login_required",
                "two_factor_required",
                "captcha_required",
                "account_confirmation_required",
            ),
        )
        self.assertTrue(contract["resume"]["explicit_human_confirmation_required"])
        self.assertFalse(contract["resume"]["automatic_retry"])
        self.assertFalse(contract["security"]["automates_authentication"])
        self.assertFalse(contract["security"]["reads_credentials"])
        self.assertEqual(model["parameters"]["automatic_auth_attempts"], 0)
        self.assertEqual(model["parameters"]["automatic_resume_attempts"], 0)

        mutated = copy.deepcopy(contract)
        mutated["security"]["automates_authentication"] = True
        with self.assertRaises(ChatGPTExportStateError):
            validate_chatgpt_export_human_auth_contract(mutated)
        changed_model = copy.deepcopy(model)
        changed_model["parameters"]["automatic_auth_attempts"] = 1
        with self.assertRaises(ChatGPTExportStateError):
            validate_chatgpt_export_human_auth_model_parameters(changed_model)

    def test_exact_connector_challenges_pause_a_zero_click_request(self) -> None:
        for challenge in AUTH_CHALLENGE_CODES:
            with self.subTest(challenge=challenge):
                state, _ = reserve_export_request(
                    build_initial_export_state(),
                    request_id=(str(AUTH_CHALLENGE_CODES.index(challenge) + 1) * 32),
                    occurred_at=NOW,
                )
                paused, changed = record_export_request_outcome(
                    state,
                    connector_payload=connector_payload(
                        status="FAIL", clicks=0, error_code=challenge
                    ),
                    occurred_at=LATER,
                )
                self.assertTrue(changed)
                self.assertEqual(paused["status"], HUMAN_AUTH_STATE)
                self.assertEqual(paused["last_error_code"], challenge)
                self.assertIsNone(paused["retry_from"])
                self.assertEqual(paused["request"]["dispatch_status"], "HUMAN_AUTH_REQUIRED")
                self.assertEqual(paused["request"]["request_click_count"], 0)

    def test_unknown_or_post_click_failure_never_becomes_human_auth_pause(self) -> None:
        state, _ = reserve_export_request(
            build_initial_export_state(), request_id="5" * 32, occurred_at=NOW
        )
        retryable, _ = record_export_request_outcome(
            state,
            connector_payload=connector_payload(
                status="FAIL", clicks=0, error_code="profile_menu_unavailable"
            ),
            occurred_at=LATER,
        )
        self.assertEqual(retryable["status"], "FAILED_RETRYABLE")

        state, _ = reserve_export_request(
            build_initial_export_state(), request_id="6" * 32, occurred_at=NOW
        )
        uncertain, _ = record_export_request_outcome(
            state,
            connector_payload=connector_payload(
                status="FAIL", clicks=1, error_code="login_required"
            ),
            occurred_at=LATER,
        )
        self.assertEqual(uncertain["status"], "REQUESTED")
        self.assertEqual(uncertain["request"]["dispatch_status"], "OUTCOME_UNCERTAIN")

    def test_stateful_connector_challenge_persists_pause_and_surfaces_human_action(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = HumanAuthFixture(Path(tmpdir))
            calls: list[str] = []

            def connector(_args: Namespace) -> int:
                calls.append("called")
                print(
                    json.dumps(
                        connector_payload(
                            status="FAIL", clicks=0, error_code="login_required"
                        )
                    )
                )
                return 2

            code, payload = execute_stateful_chatgpt_export_request(
                Namespace(
                    database_dir=fixture.root,
                    cdp_endpoint="http://127.0.0.1:9222",
                    dry_run=False,
                    apply=True,
                    confirm_request=True,
                ),
                connector_runner=connector,
                clock=lambda: NOW,
                request_id_factory=lambda: "f" * 32,
            )
            persisted = load_chatgpt_export_state(fixture.root)
            self.assertEqual(code, 2)
            self.assertEqual(calls, ["called"])
            self.assertEqual(payload["export_state"], HUMAN_AUTH_STATE)
            self.assertTrue(payload["human_auth_required"])
            self.assertEqual(payload["human_auth_challenge"], "login_required")
            self.assertEqual(persisted["status"], HUMAN_AUTH_STATE)
            self.assertEqual(persisted["request"]["dispatch_status"], "HUMAN_AUTH_REQUIRED")

    def test_request_execution_is_suppressed_while_human_action_is_required(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = HumanAuthFixture(Path(tmpdir))
            paused, _ = pause_export_for_human_auth(
                build_initial_export_state(),
                challenge="login_required",
                event_id="auth-login-required",
                evidence_sha256=EVIDENCE,
                occurred_at=NOW,
                expected_revision=0,
            )
            write_chatgpt_export_state(fixture.root, paused)
            calls: list[str] = []

            def connector(_args: Namespace) -> int:
                calls.append("called")
                return 0

            code, payload = execute_stateful_chatgpt_export_request(
                Namespace(
                    database_dir=fixture.root,
                    cdp_endpoint="http://127.0.0.1:9222",
                    dry_run=False,
                    apply=True,
                    confirm_request=True,
                ),
                connector_runner=connector,
                clock=lambda: LATER,
                request_id_factory=lambda: "7" * 32,
            )
            self.assertEqual(code, 2)
            self.assertEqual(payload["error_code"], "human_auth_required")
            self.assertTrue(payload["human_auth_required"])
            self.assertEqual(payload["human_auth_challenge"], "login_required")
            self.assertTrue(payload["pending_request_suppressed"])
            self.assertEqual(calls, [])

            dry_run_args = Namespace(
                database_dir=fixture.root,
                cdp_endpoint="http://127.0.0.1:9222",
                dry_run=True,
                apply=False,
                confirm_request=False,
            )
            dry_code, dry_payload = execute_stateful_chatgpt_export_request(
                dry_run_args,
                connector_runner=connector,
                clock=lambda: LATER,
                request_id_factory=lambda: "7" * 32,
            )
            self.assertEqual(dry_code, 2)
            self.assertEqual(dry_payload["error_code"], "human_auth_required")
            self.assertEqual(calls, [])

    def test_resume_returns_to_prior_nonrequest_state_only_after_confirmation(self) -> None:
        state, _ = reserve_export_request(
            build_initial_export_state(), request_id="8" * 32, occurred_at=NOW
        )
        waiting, _ = record_export_request_outcome(
            state,
            connector_payload=connector_payload(status="PASS", clicks=1),
            occurred_at=NOW,
        )
        paused, _ = pause_export_for_human_auth(
            waiting,
            challenge="two_factor_required",
            event_id="auth-2fa-required",
            evidence_sha256=EVIDENCE,
            occurred_at=NOW,
            expected_revision=waiting["revision"],
        )
        with self.assertRaisesRegex(
            ChatGPTExportStateError, "explicit_human_auth_confirmation_required"
        ):
            resume_export_after_human_auth(
                paused,
                event_id="auth-2fa-complete",
                evidence_sha256=EVIDENCE,
                occurred_at=LATER,
                expected_revision=paused["revision"],
                explicit_confirmation=False,
            )

        resumed, changed = resume_export_after_human_auth(
            paused,
            event_id="auth-2fa-complete",
            evidence_sha256=EVIDENCE,
            occurred_at=LATER,
            expected_revision=paused["revision"],
            explicit_confirmation=True,
        )
        self.assertTrue(changed)
        self.assertEqual(resumed["status"], "WAITING_FOR_EXPORT")
        self.assertIsNone(resumed["last_error_code"])
        repeated, repeated_changed = resume_export_after_human_auth(
            resumed,
            event_id="auth-2fa-complete",
            evidence_sha256=EVIDENCE,
            occurred_at=LATER,
            expected_revision=paused["revision"],
            explicit_confirmation=True,
        )
        self.assertFalse(repeated_changed)
        self.assertEqual(repeated, resumed)

    def test_request_resume_requires_a_new_explicit_request_and_generic_api_stays_closed(self) -> None:
        state, _ = reserve_export_request(
            build_initial_export_state(), request_id="9" * 32, occurred_at=NOW
        )
        paused, _ = record_export_request_outcome(
            state,
            connector_payload=connector_payload(
                status="FAIL", clicks=0, error_code="captcha_required"
            ),
            occurred_at=NOW,
        )
        with self.assertRaisesRegex(ChatGPTExportStateError, "human_auth_resume_deferred"):
            apply_export_transition(
                paused,
                to_state="FAILED_RETRYABLE",
                event_id="generic-resume",
                reason_code="human_auth_completed",
                evidence_sha256=EVIDENCE,
                occurred_at=LATER,
                expected_revision=paused["revision"],
            )

        resumed, _ = resume_export_after_human_auth(
            paused,
            event_id="captcha-complete",
            evidence_sha256=EVIDENCE,
            occurred_at=LATER,
            expected_revision=paused["revision"],
            explicit_confirmation=True,
        )
        self.assertEqual(resumed["status"], "FAILED_RETRYABLE")
        self.assertEqual(resumed["retry_from"], "IDLE")
        self.assertEqual(resumed["last_error_code"], "human_auth_resume_requires_new_request")
        self.assertEqual(resumed["request"]["dispatch_status"], "FAILED_BEFORE_CLICK")
        self.assertEqual(resumed["request"]["request_click_count"], 0)

    def test_cli_inspect_is_read_only_and_resume_requires_explicit_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = HumanAuthFixture(Path(tmpdir))
            before = fixture.state_path.read_bytes()
            inspect_args = Namespace(
                database_dir=fixture.root,
                inspect=True,
                pause=False,
                resume=False,
                challenge=None,
                expected_revision=None,
                event_id=None,
                evidence_sha256=None,
                confirm_human_auth_complete=False,
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = run_chatgpt_export_human_auth(inspect_args)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 0)
            self.assertEqual(payload["action"], "INSPECTED_NO_CHANGES")
            self.assertFalse(payload["human_auth_required"])
            self.assertFalse(payload["automatic_auth_action"])
            self.assertEqual(fixture.state_path.read_bytes(), before)

            invalid_inspect = copy.copy(inspect_args)
            invalid_inspect.confirm_human_auth_complete = True
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = run_chatgpt_export_human_auth(invalid_inspect)
            self.assertEqual(code, 2)
            self.assertEqual(
                json.loads(stdout.getvalue())["error_code"],
                "human_auth_inspect_arguments_forbidden",
            )
            self.assertEqual(fixture.state_path.read_bytes(), before)

            pause_args = Namespace(
                database_dir=fixture.root,
                inspect=False,
                pause=True,
                resume=False,
                challenge="account_confirmation_required",
                expected_revision=0,
                event_id="account-confirmation-required",
                evidence_sha256=EVIDENCE,
                confirm_human_auth_complete=False,
            )
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = run_chatgpt_export_human_auth(pause_args)
            self.assertEqual(code, 0)

            resume_args = copy.copy(pause_args)
            resume_args.pause = False
            resume_args.resume = True
            resume_args.challenge = None
            resume_args.expected_revision = 1
            resume_args.event_id = "account-confirmation-complete"
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                code = run_chatgpt_export_human_auth(resume_args)
            payload = json.loads(stdout.getvalue())
            self.assertEqual(code, 2)
            self.assertEqual(
                payload["error_code"], "explicit_human_auth_confirmation_required"
            )


if __name__ == "__main__":
    unittest.main()
