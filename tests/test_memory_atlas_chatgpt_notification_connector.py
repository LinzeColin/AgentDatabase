from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_notification_connector import (  # noqa: E402
    ADAPTER_IDS,
    CONTRACT_RELATIVE,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    LOCAL_CONFIG_FILENAME,
    MODEL_RELATIVE,
    NotificationConnectorError,
    configure_notification_connector,
    inspect_notification_connector,
    load_chatgpt_notification_connector_contract,
    load_chatgpt_notification_connector_model_parameters,
    probe_apple_mail,
    run_chatgpt_notification_connector,
)


class ChatGPTNotificationConnectorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name)
        self.repo_root = self.base / "repo"
        self.repo_root.mkdir()
        (self.repo_root / ".git").mkdir()
        self.database_dir = self.repo_root / "OpenAIDatabase"
        (self.database_dir / CONTRACT_RELATIVE.parent).mkdir(parents=True)
        (self.database_dir / MODEL_RELATIVE.parent).mkdir(parents=True)
        (self.database_dir / CONTRACT_RELATIVE).write_text(
            json.dumps(EXPECTED_CONTRACT, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        (self.database_dir / MODEL_RELATIVE).write_text(
            json.dumps(EXPECTED_MODEL_PARAMETERS, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        self.runtime_dir = self.base / "runtime"
        self.mail_app = self.base / "Mail.app"
        self.mail_app.mkdir()
        self.osascript = self.base / "osascript"
        self.osascript.write_text("fixture", encoding="utf-8")
        self.osascript.chmod(0o700)
        self.calls: list[tuple[list[str], dict[str, object]]] = []

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def ready_runner(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, b"READY\n", b"fixture-secret-stderr")

    def failing_runner(self, argv: list[str], **kwargs: object) -> subprocess.CompletedProcess[bytes]:
        self.calls.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 1, b"", b"private-account-detail")

    def connector_kwargs(self) -> dict[str, object]:
        return {
            "runner": self.ready_runner,
            "system_name": "Darwin",
            "application_paths": (self.mail_app,),
            "osascript_path": self.osascript,
            "environ": {
                "HOME": str(self.base / "home"),
                "USER": "fixture-user",
                "LOGNAME": "fixture-user",
                "LANG": "en_US.UTF-8",
                "PATH": "/private/bin",
                "OPENAI_API_KEY": "must-not-pass",
                "IMAP_PASSWORD": "must-not-pass",
            },
        }

    def test_contract_and_model_are_exact_and_phase_bounded(self) -> None:
        contract = load_chatgpt_notification_connector_contract(self.database_dir)
        model = load_chatgpt_notification_connector_model_parameters(self.database_dir)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(ADAPTER_IDS, ("apple-mail-local",))
        self.assertTrue(contract["connector"]["read_only"])
        self.assertEqual(contract["connector"]["adapter_registry"], list(ADAPTER_IDS))
        self.assertFalse(contract["phase_boundary"]["discovers_export_notifications"])
        self.assertFalse(contract["phase_boundary"]["extracts_download_links"])
        self.assertEqual(contract["phase_boundary"]["next_task"], "S08-P2-T2")

    def test_contract_or_model_drift_fails_closed(self) -> None:
        contract_path = self.database_dir / CONTRACT_RELATIVE
        contract = json.loads(contract_path.read_text(encoding="utf-8"))
        contract["security"]["reads_message_content"] = True
        contract_path.write_text(json.dumps(contract), encoding="utf-8")
        with self.assertRaises(NotificationConnectorError) as raised:
            load_chatgpt_notification_connector_contract(self.database_dir)
        self.assertEqual(raised.exception.code, "notification_connector_contract_drift")

        contract_path.write_text(json.dumps(EXPECTED_CONTRACT), encoding="utf-8")
        model_path = self.database_dir / MODEL_RELATIVE
        model = json.loads(model_path.read_text(encoding="utf-8"))
        model["parameters"]["probe_message_content_reads"] = 1
        model_path.write_text(json.dumps(model), encoding="utf-8")
        with self.assertRaises(NotificationConnectorError) as raised:
            load_chatgpt_notification_connector_model_parameters(self.database_dir)
        self.assertEqual(raised.exception.code, "notification_connector_model_drift")

    def test_apple_mail_probe_is_fixed_read_only_and_env_sanitized(self) -> None:
        result = probe_apple_mail(**self.connector_kwargs())

        self.assertTrue(result["ready"])
        self.assertEqual(result["probe_status"], "READY")
        self.assertTrue(result["application_available"])
        self.assertTrue(result["enabled_account_available"])
        self.assertTrue(result["inbox_readable"])
        self.assertFalse(result["account_identity_read"])
        self.assertFalse(result["message_metadata_read"])
        self.assertFalse(result["message_content_read"])
        self.assertFalse(result["credential_store_access"])
        self.assertEqual(len(self.calls), 1)

        argv, kwargs = self.calls[0]
        self.assertEqual(argv[0], str(self.osascript))
        self.assertFalse(kwargs["shell"])
        self.assertEqual(kwargs["timeout"], 10)
        self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
        self.assertEqual(kwargs["stdout"], subprocess.PIPE)
        self.assertEqual(kwargs["stderr"], subprocess.PIPE)
        self.assertNotIn("OPENAI_API_KEY", kwargs["env"])
        self.assertNotIn("IMAP_PASSWORD", kwargs["env"])
        self.assertNotIn("PATH", kwargs["env"])
        script = "\n".join(argv[1:]).lower()
        self.assertIn("count every account", script)
        self.assertIn("count messages of inbox", script)
        for forbidden in (
            "subject of",
            "sender of",
            "content of",
            "source of",
            "message id of",
            "email addresses",
        ):
            self.assertNotIn(forbidden, script)

    def test_probe_failure_is_path_free_and_does_not_echo_stderr(self) -> None:
        kwargs = self.connector_kwargs()
        kwargs["runner"] = self.failing_runner
        with self.assertRaises(NotificationConnectorError) as raised:
            probe_apple_mail(**kwargs)
        self.assertEqual(raised.exception.code, "apple_mail_probe_failed")
        self.assertNotIn("private-account-detail", str(raised.exception))
        self.assertNotIn(str(self.base), str(raised.exception))

    def test_unknown_probe_output_fails_closed(self) -> None:
        def unknown_runner(
            argv: list[str], **kwargs: object
        ) -> subprocess.CompletedProcess[bytes]:
            self.calls.append((argv, kwargs))
            return subprocess.CompletedProcess(argv, 0, b"account@example.com\n", b"")

        kwargs = self.connector_kwargs()
        kwargs["runner"] = unknown_runner
        with self.assertRaises(NotificationConnectorError) as raised:
            probe_apple_mail(**kwargs)
        self.assertEqual(raised.exception.code, "apple_mail_probe_response_invalid")
        self.assertNotIn("account@example.com", str(raised.exception))

    def test_configure_requires_live_ready_probe_and_writes_only_safe_0600_config(self) -> None:
        result = configure_notification_connector(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            adapter_id="apple-mail-local",
            **self.connector_kwargs(),
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["action"], "CONFIGURED")
        self.assertEqual(result["adapter_id"], "apple-mail-local")
        self.assertTrue(result["real_adapter_ready"])
        self.assertFalse(result["message_content_read"])
        self.assertFalse(result["account_identity_emitted"])
        self.assertFalse(result["configuration_path_emitted"])
        self.assertFalse(result["repository_mutation"])
        config_path = self.runtime_dir / LOCAL_CONFIG_FILENAME
        self.assertTrue(config_path.is_file())
        self.assertEqual(stat.S_IMODE(config_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.runtime_dir.stat().st_mode), 0o700)
        config = json.loads(config_path.read_text(encoding="utf-8"))
        self.assertEqual(
            config,
            {
                "adapter_id": "apple-mail-local",
                "credential_policy": "os_keychain_via_apple_mail",
                "read_only": True,
                "schema_version": "memory_atlas.chatgpt_notification_local_config.v1_2_1_s08_p2_t1",
                "stores_credentials": False,
            },
        )
        serialized = json.dumps(config, sort_keys=True)
        for forbidden in ("password", "token", "secret", "account_id", str(self.base)):
            self.assertNotIn(forbidden, serialized)

    def test_configure_is_idempotent_and_inspect_is_byte_read_only(self) -> None:
        first = configure_notification_connector(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            adapter_id="apple-mail-local",
            **self.connector_kwargs(),
        )
        config_path = self.runtime_dir / LOCAL_CONFIG_FILENAME
        before = config_path.read_bytes()
        before_hash = hashlib.sha256(before).hexdigest()
        before_stat = config_path.stat()

        second = configure_notification_connector(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            adapter_id="apple-mail-local",
            **self.connector_kwargs(),
        )
        inspected = inspect_notification_connector(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            **self.connector_kwargs(),
        )

        self.assertEqual(first["action"], "CONFIGURED")
        self.assertEqual(second["action"], "ALREADY_CONFIGURED")
        self.assertEqual(inspected["action"], "INSPECTED_NO_CHANGES")
        self.assertEqual(hashlib.sha256(config_path.read_bytes()).hexdigest(), before_hash)
        self.assertEqual(config_path.stat().st_mtime_ns, before_stat.st_mtime_ns)

    def test_probe_failure_never_writes_machine_config(self) -> None:
        kwargs = self.connector_kwargs()
        kwargs["runner"] = self.failing_runner
        with self.assertRaises(NotificationConnectorError) as raised:
            configure_notification_connector(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                adapter_id="apple-mail-local",
                **kwargs,
            )
        self.assertEqual(raised.exception.code, "apple_mail_probe_failed")
        self.assertFalse((self.runtime_dir / LOCAL_CONFIG_FILENAME).exists())

    def test_runtime_config_must_be_outside_repo_regular_and_0600(self) -> None:
        with self.assertRaises(NotificationConnectorError) as raised:
            configure_notification_connector(
                self.database_dir,
                runtime_dir=self.database_dir / "runtime",
                adapter_id="apple-mail-local",
                **self.connector_kwargs(),
            )
        self.assertEqual(raised.exception.code, "notification_runtime_inside_repository")

        configure_notification_connector(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            adapter_id="apple-mail-local",
            **self.connector_kwargs(),
        )
        config_path = self.runtime_dir / LOCAL_CONFIG_FILENAME
        config_path.chmod(0o644)
        with self.assertRaises(NotificationConnectorError) as raised:
            inspect_notification_connector(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                **self.connector_kwargs(),
            )
        self.assertEqual(raised.exception.code, "notification_local_config_mode_invalid")

    def test_symlinked_runtime_config_fails_closed(self) -> None:
        self.runtime_dir.mkdir(mode=0o700)
        target = self.base / "target.json"
        target.write_text("{}", encoding="utf-8")
        (self.runtime_dir / LOCAL_CONFIG_FILENAME).symlink_to(target)
        with self.assertRaises(NotificationConnectorError) as raised:
            inspect_notification_connector(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                **self.connector_kwargs(),
            )
        self.assertEqual(raised.exception.code, "notification_local_config_unsafe")

    def test_cli_runner_is_strict_and_output_is_sanitized(self) -> None:
        args = argparse.Namespace(
            command="chatgpt-notification-connector",
            inspect=False,
            configure=True,
            adapter=None,
            runtime_dir=self.runtime_dir,
            database_dir=self.database_dir,
        )
        captured: list[str] = []
        original_print = print

        def capture(*values: object, **kwargs: object) -> None:
            del kwargs
            captured.append(" ".join(str(value) for value in values))

        try:
            import builtins

            builtins.print = capture
            exit_code = run_chatgpt_notification_connector(args)
        finally:
            builtins.print = original_print

        self.assertEqual(exit_code, 2)
        payload = json.loads(captured[-1])
        self.assertEqual(payload["error_code"], "notification_adapter_required")
        serialized = json.dumps(payload, sort_keys=True)
        self.assertNotIn(str(self.base), serialized)
        self.assertNotIn("fixture-user", serialized)
        self.assertNotIn("account", serialized.lower())


if __name__ == "__main__":
    unittest.main()
