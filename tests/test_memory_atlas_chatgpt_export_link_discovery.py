from __future__ import annotations

import copy
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_link_discovery import (  # noqa: E402
    ACCOUNT_BINDING_FILENAME,
    ACCOUNT_ENVIRONMENT_VARIABLE,
    APPLE_MAIL_DISCOVERY_SCRIPT,
    CONTRACT_RELATIVE,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    LinkDiscoveryError,
    MODEL_RELATIVE,
    PRIVATE_LINK_FILENAME,
    TASK_ID,
    bind_export_account,
    discover_export_link,
    inspect_export_link_discovery,
    load_chatgpt_export_link_discovery_contract,
    load_chatgpt_export_link_discovery_model_parameters,
    load_private_export_link,
    run_chatgpt_export_link_discovery,
    scan_apple_mail_sources,
    validate_chatgpt_export_link_discovery_contract,
    validate_chatgpt_export_link_discovery_model_parameters,
    validate_notification_source,
)
from memory_atlas_cli.chatgpt_export_state import (  # noqa: E402
    CONTRACT_RELATIVE as STATE_CONTRACT_RELATIVE,
    MODEL_RELATIVE as STATE_MODEL_RELATIVE,
    STATE_RELATIVE,
    ChatGPTExportStateError,
    build_initial_export_state,
    load_chatgpt_export_state,
    record_export_request_outcome,
    reserve_export_request,
    write_chatgpt_export_state,
)
import memory_atlas_cli.chatgpt_export_link_discovery as link_module  # noqa: E402
from memory_atlas_cli.chatgpt_notification_connector import (  # noqa: E402
    LOCAL_CONFIG_FILENAME,
)


REQUEST_AT = "2026-07-16T09:00:00Z"
DISPATCHED_AT = "2026-07-16T09:01:00Z"
MESSAGE_AT = "Thu, 16 Jul 2026 10:00:00 +0000"
NOW = datetime(2026, 7, 16, 11, 0, tzinfo=timezone.utc)
ACCOUNT = "owner@example.test"
LINK = "https://download.openai.com/data-export/fixture-token-123"
REQUEST_ID = "1" * 32


def connector_payload() -> dict[str, object]:
    return {
        "schema_version": "memory_atlas.chatgpt_export_request_connector_result.v1_2_1_s08_p1_t1",
        "status": "REQUEST_ACTION_DISPATCHED",
        "mode": "request",
        "action": "CONFIRM_EXPORT_CLICKED_ONCE",
        "visible_ui_only": True,
        "existing_session_reused": True,
        "request_click_count": 1,
        "credential_store_access": False,
        "private_api_calls": False,
        "owned_tab_closed": True,
        "task_id": "S08-P1-T1",
        "acceptance_id": "ACC-MA-V121-S08-P1-T1",
        "contract_sha256": "b" * 64,
        "model_parameters_sha256": "c" * 64,
    }


def notification_source(
    *,
    sender: str = "OpenAI <noreply@tm.openai.com>",
    recipient: str = ACCOUNT,
    subject: str = "Your ChatGPT data export is ready",
    date: str = MESSAGE_AT,
    link: str = LINK,
    second_link: str | None = None,
) -> bytes:
    links = f'<a href="{link}">Download data export</a>'
    if second_link is not None:
        links += f'<a href="{second_link}">Download data export</a>'
    return (
        f"From: {sender}\r\n"
        f"To: {recipient}\r\n"
        f"Date: {date}\r\n"
        f"Subject: {subject}\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "Content-Transfer-Encoding: 8bit\r\n"
        "\r\n"
        f"<html><body><p>Your data export is ready.</p>{links}</body></html>\r\n"
    ).encode("utf-8")


class ChatGPTExportLinkDiscoveryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.repo_root = self.base / "repo"
        self.repo_root.mkdir()
        (self.repo_root / ".git").mkdir()
        self.database_dir = self.repo_root / "OpenAIDatabase"
        for relative in (
            CONTRACT_RELATIVE,
            MODEL_RELATIVE,
            STATE_CONTRACT_RELATIVE,
            STATE_MODEL_RELATIVE,
        ):
            target = self.database_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        write_chatgpt_export_state(self.database_dir, build_initial_export_state())
        self.runtime_dir = self.base / "private-runtime"
        self.runtime_dir.mkdir(mode=0o700)
        self.runtime_dir.chmod(0o700)
        local_config = {
            "adapter_id": "apple-mail-local",
            "credential_policy": "os_keychain_via_apple_mail",
            "read_only": True,
            "schema_version": "memory_atlas.chatgpt_notification_local_config.v1_2_1_s08_p2_t1",
            "stores_credentials": False,
        }
        local_config_path = self.runtime_dir / LOCAL_CONFIG_FILENAME
        local_config_path.write_text(
            json.dumps(local_config, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        local_config_path.chmod(0o600)
        self.mail_app = self.base / "Mail.app"
        self.mail_app.mkdir()
        self.osascript = self.base / "osascript"
        self.osascript.write_text("fixture", encoding="utf-8")
        self.osascript.chmod(0o700)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_waiting(self) -> dict[str, object]:
        state, _ = reserve_export_request(
            build_initial_export_state(),
            request_id=REQUEST_ID,
            occurred_at=REQUEST_AT,
        )
        state, _ = record_export_request_outcome(
            state,
            connector_payload=connector_payload(),
            occurred_at=DISPATCHED_AT,
        )
        write_chatgpt_export_state(self.database_dir, state)
        return state

    def bind(self) -> dict[str, object]:
        return bind_export_account(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            account=ACCOUNT,
            salt_hex="ab" * 16,
        )

    def binding_payload(self) -> dict[str, object]:
        self.bind()
        return json.loads(
            (self.runtime_dir / ACCOUNT_BINDING_FILENAME).read_text(encoding="utf-8")
        )

    def test_contract_and_model_are_exact_and_stop_before_download(self) -> None:
        contract = load_chatgpt_export_link_discovery_contract(self.database_dir)
        model = load_chatgpt_export_link_discovery_model_parameters(self.database_dir)

        self.assertEqual(TASK_ID, "S08-P2-T2")
        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["state_gate"]["required_state"], "WAITING_FOR_EXPORT")
        self.assertEqual(contract["state_gate"]["success_state"], "LINK_READY")
        self.assertEqual(contract["official_source"]["link_validity_seconds"], 86400)
        self.assertFalse(contract["phase_boundary"]["downloads_export"])
        self.assertEqual(contract["phase_boundary"]["next_task"], "S08-P2-T3")

    def test_contract_and_model_drift_fail_closed(self) -> None:
        contract = copy.deepcopy(EXPECTED_CONTRACT)
        contract["security"]["one_time_url_in_repository"] = True
        with self.assertRaises(LinkDiscoveryError) as raised:
            validate_chatgpt_export_link_discovery_contract(contract)
        self.assertEqual(raised.exception.code, "link_discovery_contract_drift")

        model = copy.deepcopy(EXPECTED_MODEL_PARAMETERS)
        model["parameters"]["link_validity_seconds"] = 172800
        with self.assertRaises(LinkDiscoveryError) as raised:
            validate_chatgpt_export_link_discovery_model_parameters(model)
        self.assertEqual(raised.exception.code, "link_discovery_model_drift")

    def test_account_binding_persists_only_salted_digest_with_0600_mode(self) -> None:
        first = self.bind()
        second = bind_export_account(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            account=ACCOUNT.upper(),
        )
        path = self.runtime_dir / ACCOUNT_BINDING_FILENAME
        content = path.read_text(encoding="utf-8")
        payload = json.loads(content)

        self.assertEqual(first["action"], "ACCOUNT_BOUND")
        self.assertEqual(second["action"], "ACCOUNT_ALREADY_BOUND")
        self.assertNotIn(ACCOUNT, content.casefold())
        self.assertEqual(payload["salt_hex"], "ab" * 16)
        self.assertEqual(len(payload["account_digest"]), 64)
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertFalse(first["account_value_emitted"])
        self.assertFalse(first["one_time_url_emitted"])

        with self.assertRaises(LinkDiscoveryError) as raised:
            bind_export_account(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                account="wrong@example.test",
            )
        self.assertEqual(raised.exception.code, "link_discovery_account_binding_conflict")

    def test_mail_scan_uses_fixed_shell_free_script_and_sanitized_environment(self) -> None:
        calls: list[tuple[list[str], dict[str, object]]] = []
        source = notification_source()

        def runner(argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
            calls.append((argv, kwargs))
            return subprocess.CompletedProcess(
                argv,
                0,
                b"SOURCE\n" + source + b"\x1eDONE\n",
                b"private-mail-error",
            )

        sources = scan_apple_mail_sources(
            runner=runner,
            system_name="Darwin",
            application_paths=(self.mail_app,),
            osascript_path=self.osascript,
            environ={
                "HOME": str(self.base / "home"),
                "USER": "fixture-user",
                "PATH": "/private/bin",
                "OPENAI_API_KEY": "must-not-pass",
                "IMAP_PASSWORD": "must-not-pass",
                ACCOUNT_ENVIRONMENT_VARIABLE: ACCOUNT,
            },
        )

        self.assertEqual(sources, [source])
        argv, kwargs = calls[0]
        self.assertEqual(argv[0], str(self.osascript))
        self.assertEqual(tuple(argv[2::2]), APPLE_MAIL_DISCOVERY_SCRIPT)
        self.assertIs(kwargs["shell"], False)
        self.assertEqual(kwargs["timeout"], 15)
        self.assertEqual(kwargs["env"], {"HOME": str(self.base / "home"), "USER": "fixture-user"})
        self.assertNotIn(ACCOUNT, " ".join(argv))
        self.assertNotIn(LINK, " ".join(argv))

    def test_mail_scan_rejects_timeout_unknown_marker_and_private_stderr(self) -> None:
        def timeout_runner(*_args: object, **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            raise subprocess.TimeoutExpired("osascript", 15)

        with self.assertRaises(LinkDiscoveryError) as raised:
            scan_apple_mail_sources(
                runner=timeout_runner,
                system_name="Darwin",
                application_paths=(self.mail_app,),
                osascript_path=self.osascript,
            )
        self.assertEqual(raised.exception.code, "link_discovery_mail_timeout")
        self.assertNotIn("osascript", str(raised.exception))

        def marker_runner(argv: list[str], **_kwargs: object) -> subprocess.CompletedProcess[bytes]:
            return subprocess.CompletedProcess(argv, 0, b"OVERSIZE\x1eDONE\n", b"mail-secret")

        with self.assertRaises(LinkDiscoveryError) as raised:
            scan_apple_mail_sources(
                runner=marker_runner,
                system_name="Darwin",
                application_paths=(self.mail_app,),
                osascript_path=self.osascript,
            )
        self.assertEqual(raised.exception.code, "link_discovery_mail_response_invalid")
        self.assertNotIn("mail-secret", str(raised.exception))

    def test_notification_validation_accepts_only_bound_current_official_link(self) -> None:
        candidate = validate_notification_source(
            notification_source(),
            account_binding=self.binding_payload(),
            request_reserved_at=REQUEST_AT,
            now=NOW,
        )

        self.assertEqual(candidate["url"], LINK)
        self.assertEqual(len(candidate["link_sha256"]), 64)
        self.assertEqual(candidate["received_at"], "2026-07-16T10:00:00Z")
        self.assertEqual(candidate["expires_at"], "2026-07-17T10:00:00Z")

    def test_notification_validation_rejects_wrong_identity_time_status_and_url(self) -> None:
        binding = self.binding_payload()
        cases = (
            (
                notification_source(sender="Attacker <noreply@example.test>"),
                "link_discovery_sender_invalid",
            ),
            (
                notification_source(recipient="wrong@example.test"),
                "link_discovery_account_mismatch",
            ),
            (
                notification_source(subject="Welcome to ChatGPT"),
                "link_discovery_status_invalid",
            ),
            (
                notification_source(date="Thu, 16 Jul 2026 08:59:59 +0000"),
                "link_discovery_message_time_invalid",
            ),
            (
                notification_source(link="https://example.test/data-export/token"),
                "link_discovery_url_invalid",
            ),
            (
                notification_source(
                    second_link="https://chatgpt.com/backend-api/data-export/second-token"
                ),
                "link_discovery_url_ambiguous",
            ),
        )
        for source, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(LinkDiscoveryError) as raised:
                    validate_notification_source(
                        source,
                        account_binding=binding,
                        request_reserved_at=REQUEST_AT,
                        now=NOW,
                    )
                self.assertEqual(raised.exception.code, code)

        with self.assertRaises(LinkDiscoveryError) as raised:
            validate_notification_source(
                notification_source(),
                account_binding=binding,
                request_reserved_at=REQUEST_AT,
                now=datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
            )
        self.assertEqual(raised.exception.code, "link_discovery_link_expired")

    def test_discovery_stores_url_only_outside_repo_and_advances_state(self) -> None:
        self.make_waiting()
        self.bind()
        connector_calls: list[str] = []
        scanner_calls: list[str] = []

        def connector_inspector(*_args: object, **_kwargs: object) -> dict[str, object]:
            connector_calls.append("called")
            return {"real_adapter_ready": True}

        def scanner() -> list[bytes]:
            scanner_calls.append("called")
            return [notification_source()]

        result = discover_export_link(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            scanner=scanner,
            connector_inspector=connector_inspector,
            now=NOW,
        )
        state = load_chatgpt_export_state(self.database_dir)
        private_path = self.runtime_dir / PRIVATE_LINK_FILENAME
        private_content = private_path.read_text(encoding="utf-8")
        state_content = (self.database_dir / STATE_RELATIVE).read_text(encoding="utf-8")
        rendered_result = json.dumps(result, sort_keys=True)

        self.assertEqual(connector_calls, ["called"])
        self.assertEqual(scanner_calls, ["called"])
        self.assertEqual(result["action"], "LINK_STORED")
        self.assertEqual(result["export_state"], "LINK_READY")
        self.assertEqual(state["status"], "LINK_READY")
        self.assertEqual(state["revision"], 3)
        self.assertEqual(state["history"][-1]["reason_code"], "official_export_link_verified")
        self.assertIn(LINK, private_content)
        self.assertEqual(stat.S_IMODE(private_path.stat().st_mode), 0o600)
        self.assertFalse(private_path.is_relative_to(self.repo_root))
        self.assertNotIn(LINK, state_content)
        self.assertNotIn(LINK, rendered_result)
        self.assertNotIn(ACCOUNT, state_content.casefold())
        self.assertNotIn(ACCOUNT, rendered_result.casefold())
        self.assertNotIn("Your data export is ready", state_content)

    def test_idle_state_exits_before_runtime_connector_or_mail_access(self) -> None:
        calls: list[str] = []

        def forbidden(*_args: object, **_kwargs: object) -> object:
            calls.append("called")
            raise AssertionError("must not run")

        with self.assertRaises(LinkDiscoveryError) as raised:
            discover_export_link(
                self.database_dir,
                runtime_dir=self.base / "missing-runtime",
                scanner=forbidden,  # type: ignore[arg-type]
                connector_inspector=forbidden,  # type: ignore[arg-type]
                now=NOW,
            )
        self.assertEqual(raised.exception.code, "link_discovery_state_not_eligible")
        self.assertEqual(calls, [])
        self.assertFalse((self.base / "missing-runtime").exists())

        inspected = inspect_export_link_discovery(
            self.database_dir,
            runtime_dir=self.base / "missing-runtime",
        )
        self.assertEqual(inspected["action"], "STATE_NOT_ELIGIBLE")
        self.assertFalse(inspected["eligible_for_discovery"])
        self.assertEqual(calls, [])

    def test_multiple_valid_notifications_fail_without_link_or_state_write(self) -> None:
        waiting = self.make_waiting()
        self.bind()
        with self.assertRaises(LinkDiscoveryError) as raised:
            discover_export_link(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                scanner=lambda: [notification_source(), notification_source()],
                connector_inspector=lambda *_args, **_kwargs: {"real_adapter_ready": True},
                now=NOW,
            )
        self.assertEqual(raised.exception.code, "link_discovery_notification_ambiguous")
        self.assertEqual(load_chatgpt_export_state(self.database_dir), waiting)
        self.assertFalse((self.runtime_dir / PRIVATE_LINK_FILENAME).exists())

    def test_retry_recovers_when_private_link_precedes_failed_state_write(self) -> None:
        self.make_waiting()
        self.bind()
        kwargs = {
            "runtime_dir": self.runtime_dir,
            "scanner": lambda: [notification_source()],
            "connector_inspector": lambda *_args, **_kwargs: {
                "real_adapter_ready": True
            },
        }
        with mock.patch.object(
            link_module,
            "write_chatgpt_export_state",
            side_effect=ChatGPTExportStateError("export_state_write_failed"),
        ):
            with self.assertRaises(ChatGPTExportStateError):
                discover_export_link(
                    self.database_dir,
                    now=NOW,
                    **kwargs,
                )
        self.assertTrue((self.runtime_dir / PRIVATE_LINK_FILENAME).is_file())
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "WAITING_FOR_EXPORT")

        recovered = discover_export_link(
            self.database_dir,
            now=datetime(2026, 7, 16, 11, 1, tzinfo=timezone.utc),
            **kwargs,
        )
        private_link = load_private_export_link(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            now=NOW,
        )
        self.assertEqual(recovered["action"], "LINK_ALREADY_STORED")
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "LINK_READY")
        self.assertEqual(private_link["url"], LINK)

    def test_cli_uses_env_only_for_binding_and_outputs_sanitized_json(self) -> None:
        bind_args = Namespace(
            database_dir=self.database_dir,
            runtime_dir=self.runtime_dir,
            inspect=False,
            bind_account_from_env=True,
            discover=False,
        )
        output = io.StringIO()
        with mock.patch.dict(os.environ, {ACCOUNT_ENVIRONMENT_VARIABLE: ACCOUNT}, clear=False):
            with redirect_stdout(output):
                code = run_chatgpt_export_link_discovery(bind_args)
        rendered = output.getvalue()
        self.assertEqual(code, 0)
        self.assertNotIn(ACCOUNT, rendered.casefold())
        self.assertNotIn(str(self.runtime_dir), rendered)

        missing_output = io.StringIO()
        with mock.patch.dict(os.environ, {}, clear=True):
            with redirect_stdout(missing_output):
                missing_code = run_chatgpt_export_link_discovery(bind_args)
        failure = json.loads(missing_output.getvalue())
        self.assertEqual(missing_code, 2)
        self.assertEqual(failure["error_code"], "link_discovery_account_environment_missing")
        self.assertFalse(failure["mail_values_emitted"])
        self.assertFalse(failure["one_time_url_emitted"])


if __name__ == "__main__":
    unittest.main()
