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
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_state import (  # noqa: E402
    CONTRACT_RELATIVE,
    EXPORT_STATES,
    HUMAN_AUTH_STATE,
    MODEL_RELATIVE,
    PENDING_STATES,
    STATE_RELATIVE,
    ChatGPTExportStateError,
    apply_export_transition,
    build_initial_export_state,
    execute_stateful_chatgpt_export_request,
    export_state_lock,
    load_chatgpt_export_state,
    load_chatgpt_export_state_contract,
    load_chatgpt_export_state_model_parameters,
    record_export_request_outcome,
    reserve_export_request,
    run_chatgpt_export_state,
    validate_chatgpt_export_state,
    validate_chatgpt_export_state_contract,
    validate_chatgpt_export_state_model_parameters,
    write_chatgpt_export_state,
)
import memory_atlas_cli.chatgpt_export_state as state_module  # noqa: E402
from memory_atlas_cli.chatgpt_export_human_auth import (  # noqa: E402
    CONTRACT_RELATIVE as AUTH_CONTRACT_RELATIVE,
    MODEL_RELATIVE as AUTH_MODEL_RELATIVE,
)


NOW = "2026-07-16T18:00:00Z"
LATER = "2026-07-16T18:01:00Z"
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
        "owned_tab_closed": False,
    }


def emitting_connector(payload: dict, calls: list[str]):
    def runner(_args: Namespace) -> int:
        calls.append("called")
        print(json.dumps(payload, sort_keys=True, separators=(",", ":")))
        return 0 if payload["status"] == "REQUEST_ACTION_DISPATCHED" else 2

    return runner


class ExportStateFixture:
    def __init__(self, root: Path):
        self.root = root
        for relative in (
            CONTRACT_RELATIVE,
            MODEL_RELATIVE,
            AUTH_CONTRACT_RELATIVE,
            AUTH_MODEL_RELATIVE,
        ):
            target = root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        write_chatgpt_export_state(root, build_initial_export_state())

    @property
    def state_path(self) -> Path:
        return self.root / STATE_RELATIVE

    def args(self) -> Namespace:
        return Namespace(
            database_dir=self.root,
            cdp_endpoint="http://127.0.0.1:9222",
            dry_run=False,
            apply=True,
            confirm_request=True,
        )


class ChatGPTExportStateTests(unittest.TestCase):
    def test_contract_model_and_idle_baseline_freeze_taskpack_states(self) -> None:
        contract = load_chatgpt_export_state_contract(ROOT)
        model = load_chatgpt_export_state_model_parameters(ROOT)
        state = load_chatgpt_export_state(ROOT)

        self.assertEqual(
            EXPORT_STATES,
            (
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
            ),
        )
        self.assertEqual(PENDING_STATES, frozenset({"REQUESTED", "WAITING_FOR_EXPORT", "LINK_READY"}))
        self.assertEqual(
            contract["no_duplicate_request_while"],
            ["REQUESTED", "WAITING_FOR_EXPORT", "LINK_READY"],
        )
        self.assertFalse(contract["phase_boundary"]["implements_human_auth_resume"])
        self.assertEqual(model["parameters"]["maximum_request_clicks"], 1)
        self.assertEqual(state, build_initial_export_state())
        self.assertEqual(state["status"], "IDLE")
        self.assertEqual(state["revision"], 0)
        self.assertIsNone(state["request"])

        mutated = copy.deepcopy(contract)
        mutated["no_duplicate_request_while"] = ["REQUESTED"]
        with self.assertRaises(ChatGPTExportStateError):
            validate_chatgpt_export_state_contract(mutated)
        changed_model = copy.deepcopy(model)
        changed_model["parameters"]["maximum_request_clicks"] = 2
        with self.assertRaises(ChatGPTExportStateError):
            validate_chatgpt_export_state_model_parameters(changed_model)

    def test_complete_normal_chain_is_valid_and_duplicate_event_is_idempotent(self) -> None:
        state, changed = reserve_export_request(
            build_initial_export_state(),
            request_id="1" * 32,
            occurred_at=NOW,
        )
        self.assertTrue(changed)
        state, changed = record_export_request_outcome(
            state,
            connector_payload=connector_payload(status="PASS", clicks=1),
            occurred_at=LATER,
        )
        self.assertTrue(changed)
        self.assertEqual(state["status"], "WAITING_FOR_EXPORT")

        for index, target in enumerate(
            ("LINK_READY", "DOWNLOADED", "ARCHIVED", "PARSED", "VALIDATED", "COMMITTED", "PUSHED"),
            start=1,
        ):
            expected_revision = state["revision"]
            event_id = f"event-{index}"
            state, changed = apply_export_transition(
                state,
                to_state=target,
                event_id=event_id,
                reason_code="verified_external_step",
                evidence_sha256=EVIDENCE,
                occurred_at=LATER,
                expected_revision=expected_revision,
            )
            self.assertTrue(changed)
            repeated, repeated_changed = apply_export_transition(
                state,
                to_state=target,
                event_id=event_id,
                reason_code="verified_external_step",
                evidence_sha256=EVIDENCE,
                occurred_at=LATER,
                expected_revision=expected_revision,
            )
            self.assertFalse(repeated_changed)
            self.assertEqual(repeated, state)
        self.assertEqual(state["status"], "PUSHED")
        validate_chatgpt_export_state(state)

    def test_successful_request_enters_waiting_and_second_request_is_suppressed(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            calls: list[str] = []
            runner = emitting_connector(connector_payload(status="PASS", clicks=1), calls)

            code, first = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=runner,
                clock=lambda: NOW,
                request_id_factory=lambda: "2" * 32,
            )
            state_bytes = fixture.state_path.read_bytes()
            code_again, second = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=runner,
                clock=lambda: LATER,
                request_id_factory=lambda: "3" * 32,
            )

            self.assertEqual(code, 0)
            self.assertEqual(first["export_state"], "WAITING_FOR_EXPORT")
            self.assertEqual(first["state_revision"], 2)
            self.assertEqual(code_again, 2)
            self.assertEqual(second["error_code"], "export_request_pending")
            self.assertEqual(second["request_click_count"], 0)
            self.assertEqual(calls, ["called"])
            self.assertEqual(fixture.state_path.read_bytes(), state_bytes)

    def test_zero_click_failure_is_retryable_but_uncertain_click_stays_pending(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            zero_calls: list[str] = []
            code, failed = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(
                    connector_payload(status="FAIL", clicks=0),
                    zero_calls,
                ),
                clock=lambda: NOW,
                request_id_factory=lambda: "4" * 32,
            )
            self.assertEqual(code, 2)
            self.assertEqual(failed["export_state"], "FAILED_RETRYABLE")

            success_calls: list[str] = []
            code, retried = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(
                    connector_payload(status="PASS", clicks=1),
                    success_calls,
                ),
                clock=lambda: LATER,
                request_id_factory=lambda: "5" * 32,
            )
            self.assertEqual(code, 0)
            self.assertEqual(retried["export_state"], "WAITING_FOR_EXPORT")
            self.assertEqual(success_calls, ["called"])

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            uncertain_calls: list[str] = []
            code, uncertain = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(
                    connector_payload(
                        status="FAIL",
                        clicks=1,
                        error_code="confirm_click_outcome_uncertain",
                    ),
                    uncertain_calls,
                ),
                clock=lambda: NOW,
                request_id_factory=lambda: "6" * 32,
            )
            second_calls: list[str] = []
            second_code, blocked = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(
                    connector_payload(status="PASS", clicks=1),
                    second_calls,
                ),
                clock=lambda: LATER,
                request_id_factory=lambda: "7" * 32,
            )
            self.assertEqual(code, 2)
            self.assertEqual(uncertain["export_state"], "REQUESTED")
            self.assertEqual(uncertain["request_click_count"], 1)
            self.assertEqual(second_code, 2)
            self.assertEqual(blocked["error_code"], "export_request_pending")
            self.assertEqual(second_calls, [])

    def test_lock_corruption_and_symlink_fail_before_connector(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            calls: list[str] = []
            with export_state_lock(fixture.root):
                code, payload = execute_stateful_chatgpt_export_request(
                    fixture.args(),
                    connector_runner=emitting_connector(
                        connector_payload(status="PASS", clicks=1),
                        calls,
                    ),
                    clock=lambda: NOW,
                    request_id_factory=lambda: "8" * 32,
                )
            self.assertEqual(code, 2)
            self.assertEqual(payload["error_code"], "export_state_lock_busy")
            self.assertEqual(calls, [])

            fixture.state_path.write_text("not-json", encoding="utf-8")
            code, payload = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(
                    connector_payload(status="PASS", clicks=1),
                    calls,
                ),
                clock=lambda: NOW,
                request_id_factory=lambda: "9" * 32,
            )
            self.assertEqual(code, 2)
            self.assertEqual(payload["error_code"], "export_state_unreadable")
            self.assertEqual(calls, [])

        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            outside = fixture.root / "outside.json"
            outside.write_text("{}", encoding="utf-8")
            fixture.state_path.unlink()
            fixture.state_path.symlink_to(outside)
            with self.assertRaisesRegex(ChatGPTExportStateError, "export_state_target_unsafe"):
                load_chatgpt_export_state(fixture.root)

    def test_revision_and_illegal_transition_fail_without_state_write(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            before = fixture.state_path.read_bytes()
            for expected_revision, target, expected_code in (
                (1, "REQUESTED", "export_state_revision_conflict"),
                (0, "PUSHED", "export_state_transition_invalid"),
            ):
                args = Namespace(
                    database_dir=fixture.root,
                    inspect=False,
                    apply=True,
                    to_state=target,
                    expected_revision=expected_revision,
                    event_id="operator-event",
                    reason_code="verified_external_step",
                    evidence_sha256=EVIDENCE,
                )
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    code = run_chatgpt_export_state(args)
                self.assertEqual(code, 2)
                self.assertEqual(json.loads(stdout.getvalue())["error_code"], expected_code)
                self.assertEqual(fixture.state_path.read_bytes(), before)

    def test_cli_event_replay_is_idempotent_across_different_wall_times(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            state, _ = reserve_export_request(
                build_initial_export_state(),
                request_id="b" * 32,
                occurred_at=NOW,
            )
            state, _ = record_export_request_outcome(
                state,
                connector_payload=connector_payload(status="PASS", clicks=1),
                occurred_at=NOW,
            )
            write_chatgpt_export_state(fixture.root, state)
            args = Namespace(
                database_dir=fixture.root,
                inspect=False,
                apply=True,
                to_state="LINK_READY",
                expected_revision=state["revision"],
                event_id="notification-link-ready",
                reason_code="verified_external_step",
                evidence_sha256=EVIDENCE,
            )

            outputs: list[dict] = []
            for observed_at in (NOW, LATER):
                stdout = io.StringIO()
                with mock.patch.object(state_module, "_now_utc", return_value=observed_at):
                    with redirect_stdout(stdout):
                        code = run_chatgpt_export_state(args)
                self.assertEqual(code, 0)
                outputs.append(json.loads(stdout.getvalue()))
            self.assertEqual(outputs[0]["action"], "TRANSITION_APPLIED")
            self.assertEqual(outputs[1]["action"], "NO_CHANGES")

    def test_connector_output_with_extra_account_content_is_rejected_and_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            fixture = ExportStateFixture(Path(tmpdir))
            unsafe = connector_payload(status="PASS", clicks=1)
            unsafe["account_email"] = "owner@example.test"
            calls: list[str] = []
            code, payload = execute_stateful_chatgpt_export_request(
                fixture.args(),
                connector_runner=emitting_connector(unsafe, calls),
                clock=lambda: NOW,
                request_id_factory=lambda: "c" * 32,
            )
            self.assertEqual(code, 2)
            self.assertEqual(payload["error_code"], "connector_output_invalid")
            self.assertEqual(payload["export_state"], "REQUESTED")
            self.assertNotIn("account_email", payload)
            self.assertNotIn("example.test", json.dumps(payload))

    def test_human_auth_state_is_recordable_but_resume_is_deferred_to_t3(self) -> None:
        state, _ = reserve_export_request(
            build_initial_export_state(),
            request_id="a" * 32,
            occurred_at=NOW,
        )
        state, _ = apply_export_transition(
            state,
            to_state=HUMAN_AUTH_STATE,
            event_id="auth-required",
            reason_code="human_auth_required",
            evidence_sha256=EVIDENCE,
            occurred_at=LATER,
            expected_revision=state["revision"],
        )
        self.assertEqual(state["status"], HUMAN_AUTH_STATE)
        with self.assertRaisesRegex(ChatGPTExportStateError, "human_auth_resume_deferred"):
            apply_export_transition(
                state,
                to_state="REQUESTED",
                event_id="resume-auth",
                reason_code="human_auth_completed",
                evidence_sha256=EVIDENCE,
                occurred_at=LATER,
                expected_revision=state["revision"],
            )

    def test_state_payload_rejects_credentials_and_unbounded_history(self) -> None:
        state = build_initial_export_state()
        state["unexpected_secret"] = "token"
        with self.assertRaises(ChatGPTExportStateError):
            validate_chatgpt_export_state(state)

        valid = build_initial_export_state()
        valid["history"] = [
            {
                "event_id": f"event-{index}",
                "from_state": "IDLE",
                "to_state": "IDLE",
                "reason_code": "test",
                "evidence_sha256": EVIDENCE,
                "occurred_at": NOW,
            }
            for index in range(129)
        ]
        with self.assertRaisesRegex(ChatGPTExportStateError, "export_state_history_invalid"):
            validate_chatgpt_export_state(valid)

        tampered, _ = reserve_export_request(
            build_initial_export_state(),
            request_id="d" * 32,
            occurred_at=NOW,
        )
        tampered["history"][0]["to_state"] = "PUSHED"
        tampered["status"] = "PUSHED"
        with self.assertRaisesRegex(ChatGPTExportStateError, "export_state_history_invalid"):
            validate_chatgpt_export_state(tampered)


if __name__ == "__main__":
    unittest.main()
