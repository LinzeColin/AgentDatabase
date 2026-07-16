from __future__ import annotations

import copy
import hashlib
import io
import json
import stat
import sys
import tempfile
import unittest
import zipfile
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_download import (  # noqa: E402
    CONTRACT_RELATIVE,
    DOWNLOAD_DIRECTORY_NAME,
    DOWNLOAD_METADATA_FILENAME,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    MODEL_RELATIVE,
    TASK_ID,
    ExportDownloadError,
    download_export_zip,
    inspect_export_download,
    load_chatgpt_export_download_contract,
    load_chatgpt_export_download_model_parameters,
    load_private_downloaded_export,
    run_chatgpt_export_download,
    validate_chatgpt_export_download_contract,
    validate_chatgpt_export_download_model_parameters,
    validate_downloaded_zip,
)
import memory_atlas_cli.chatgpt_export_download as download_module  # noqa: E402
from memory_atlas_cli.chatgpt_export_link_discovery import (  # noqa: E402
    ACCOUNT_BINDING_FILENAME,
    CONTRACT_RELATIVE as LINK_CONTRACT_RELATIVE,
    MODEL_RELATIVE as LINK_MODEL_RELATIVE,
    PRIVATE_LINK_FILENAME,
    bind_export_account,
    discover_export_link,
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


def notification_source() -> bytes:
    return (
        "From: OpenAI <noreply@tm.openai.com>\r\n"
        f"To: {ACCOUNT}\r\n"
        f"Date: {MESSAGE_AT}\r\n"
        "Subject: Your ChatGPT data export is ready\r\n"
        "MIME-Version: 1.0\r\n"
        "Content-Type: text/html; charset=utf-8\r\n"
        "\r\n"
        "<html><body><p>Your data export is ready.</p>"
        f'<a href="{LINK}">Download data export</a></body></html>\r\n'
    ).encode("utf-8")


def official_zip_bytes() -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("conversations.json", "[]\n")
        archive.writestr("chat.html", "<!doctype html><title>fixture</title>\n")
    return buffer.getvalue()


class FixtureDownloader:
    def __init__(self, payload: bytes | Exception) -> None:
        self.payload = payload
        self.calls = 0

    def __call__(self, url: str, destination: Path) -> dict[str, object]:
        self.calls += 1
        if isinstance(self.payload, Exception):
            raise self.payload
        destination.write_bytes(self.payload)
        destination.chmod(0o600)
        return {
            "bytes_downloaded": len(self.payload),
            "content_type": "application/zip",
            "final_url_sha256": hashlib.sha256(url.encode("utf-8")).hexdigest(),
            "redirect_count": 0,
        }


class ChatGPTExportDownloadTests(unittest.TestCase):
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
            LINK_CONTRACT_RELATIVE,
            LINK_MODEL_RELATIVE,
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
        config = {
            "adapter_id": "apple-mail-local",
            "credential_policy": "os_keychain_via_apple_mail",
            "read_only": True,
            "schema_version": "memory_atlas.chatgpt_notification_local_config.v1_2_1_s08_p2_t1",
            "stores_credentials": False,
        }
        config_path = self.runtime_dir / LOCAL_CONFIG_FILENAME
        config_path.write_text(
            json.dumps(config, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        config_path.chmod(0o600)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def make_link_ready(self) -> dict[str, object]:
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
        bind_export_account(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            account=ACCOUNT,
            salt_hex="ab" * 16,
        )
        discover_export_link(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            scanner=lambda: [notification_source()],
            connector_inspector=lambda *_args, **_kwargs: {
                "real_adapter_ready": True
            },
            now=NOW,
        )
        return load_chatgpt_export_state(self.database_dir)

    def test_contract_and_model_are_exact_and_stop_before_archive(self) -> None:
        contract = load_chatgpt_export_download_contract(self.database_dir)
        model = load_chatgpt_export_download_model_parameters(self.database_dir)

        self.assertEqual(TASK_ID, "S08-P2-T3")
        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["state_gate"]["required_state"], "LINK_READY")
        self.assertEqual(contract["state_gate"]["success_state"], "DOWNLOADED")
        self.assertTrue(contract["download"]["retryable"])
        self.assertEqual(contract["deduplication"]["identity"], "zip_sha256")
        self.assertFalse(contract["phase_boundary"]["writes_raw_archive"])
        self.assertEqual(contract["phase_boundary"]["next_task"], "S08-P3-T1")

    def test_contract_and_model_drift_fail_closed(self) -> None:
        contract = copy.deepcopy(EXPECTED_CONTRACT)
        contract["security"]["browser_cookie_access"] = True
        with self.assertRaises(ExportDownloadError) as raised:
            validate_chatgpt_export_download_contract(contract)
        self.assertEqual(raised.exception.code, "export_download_contract_drift")

        model = copy.deepcopy(EXPECTED_MODEL_PARAMETERS)
        model["parameters"]["maximum_download_bytes"] *= 2
        with self.assertRaises(ExportDownloadError) as raised:
            validate_chatgpt_export_download_model_parameters(model)
        self.assertEqual(raised.exception.code, "export_download_model_drift")

    def test_idle_state_exits_before_private_runtime_or_network(self) -> None:
        missing_runtime = self.base / "missing-runtime"
        downloader = FixtureDownloader(AssertionError("must not download"))

        inspected = inspect_export_download(
            self.database_dir,
            runtime_dir=missing_runtime,
            now=NOW,
        )
        self.assertEqual(inspected["action"], "STATE_NOT_ELIGIBLE")
        self.assertEqual(inspected["export_state"], "IDLE")
        self.assertFalse(inspected["eligible_for_download"])

        with self.assertRaises(ExportDownloadError) as raised:
            download_export_zip(
                self.database_dir,
                runtime_dir=missing_runtime,
                downloader=downloader,
                now=NOW,
            )
        self.assertEqual(raised.exception.code, "export_download_state_not_eligible")
        self.assertEqual(downloader.calls, 0)
        self.assertFalse(missing_runtime.exists())

    def test_download_validates_zip_stores_private_hash_file_and_advances_state(self) -> None:
        self.make_link_ready()
        payload = official_zip_bytes()
        downloader = FixtureDownloader(payload)

        result = download_export_zip(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            downloader=downloader,
            now=NOW,
        )
        state = load_chatgpt_export_state(self.database_dir)
        digest = hashlib.sha256(payload).hexdigest()
        download_path = (
            self.runtime_dir
            / DOWNLOAD_DIRECTORY_NAME
            / f"chatgpt-export-{digest}.zip"
        )
        metadata_path = self.runtime_dir / DOWNLOAD_METADATA_FILENAME
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        loaded_path, loaded_metadata = load_private_downloaded_export(
            self.database_dir,
            runtime_dir=self.runtime_dir,
        )
        tracked_state = (self.database_dir / STATE_RELATIVE).read_text(encoding="utf-8")
        rendered = json.dumps(result, sort_keys=True)

        self.assertEqual(downloader.calls, 1)
        self.assertEqual(result["action"], "DOWNLOADED")
        self.assertEqual(result["download_sha256"], digest)
        self.assertEqual(result["export_state"], "DOWNLOADED")
        self.assertEqual(state["status"], "DOWNLOADED")
        self.assertEqual(state["history"][-1]["reason_code"], "official_export_zip_downloaded")
        self.assertEqual(download_path.read_bytes(), payload)
        self.assertEqual(stat.S_IMODE(download_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(metadata_path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(download_path.parent.stat().st_mode), 0o700)
        self.assertFalse(download_path.is_relative_to(self.repo_root))
        self.assertEqual(metadata["download_sha256"], digest)
        self.assertEqual(loaded_path, download_path.resolve())
        self.assertEqual(loaded_metadata, metadata)
        self.assertEqual(metadata["relative_path"], f"{DOWNLOAD_DIRECTORY_NAME}/{download_path.name}")
        self.assertNotIn(LINK, tracked_state)
        self.assertNotIn(LINK, rendered)
        self.assertNotIn(ACCOUNT, tracked_state.casefold())
        self.assertNotIn(str(self.runtime_dir), rendered)

    def test_invalid_zip_is_removed_and_retry_succeeds_without_state_poisoning(self) -> None:
        ready = self.make_link_ready()
        failed = FixtureDownloader(b"not-a-zip")

        with self.assertRaises(ExportDownloadError) as raised:
            download_export_zip(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                downloader=failed,
                now=NOW,
            )
        self.assertEqual(raised.exception.code, "export_download_zip_invalid")
        self.assertEqual(load_chatgpt_export_state(self.database_dir), ready)
        self.assertFalse((self.runtime_dir / DOWNLOAD_METADATA_FILENAME).exists())
        download_dir = self.runtime_dir / DOWNLOAD_DIRECTORY_NAME
        self.assertFalse(download_dir.exists() and any(download_dir.iterdir()))

        retry = FixtureDownloader(official_zip_bytes())
        result = download_export_zip(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            downloader=retry,
            now=NOW,
        )
        self.assertEqual(result["action"], "DOWNLOADED")
        self.assertEqual(retry.calls, 1)
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "DOWNLOADED")

    def test_state_write_failure_recovers_existing_hash_without_second_download(self) -> None:
        self.make_link_ready()
        downloader = FixtureDownloader(official_zip_bytes())
        with mock.patch.object(
            download_module,
            "write_chatgpt_export_state",
            side_effect=ChatGPTExportStateError("export_state_write_failed"),
        ):
            with self.assertRaises(ChatGPTExportStateError):
                download_export_zip(
                    self.database_dir,
                    runtime_dir=self.runtime_dir,
                    downloader=downloader,
                    now=NOW,
                )
        self.assertEqual(downloader.calls, 1)
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "LINK_READY")
        self.assertTrue((self.runtime_dir / DOWNLOAD_METADATA_FILENAME).is_file())

        forbidden = FixtureDownloader(AssertionError("must reuse private download"))
        recovered = download_export_zip(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            downloader=forbidden,
            now=datetime(2026, 7, 17, 10, 1, tzinfo=timezone.utc),
        )
        self.assertEqual(recovered["action"], "DOWNLOAD_ALREADY_STORED")
        self.assertEqual(forbidden.calls, 0)
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "DOWNLOADED")
        self.assertEqual(
            len(list((self.runtime_dir / DOWNLOAD_DIRECTORY_NAME).glob("*.zip"))),
            1,
        )

    def test_repeat_download_is_idempotent_and_never_calls_network(self) -> None:
        self.make_link_ready()
        first = FixtureDownloader(official_zip_bytes())
        download_export_zip(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            downloader=first,
            now=NOW,
        )
        forbidden = FixtureDownloader(AssertionError("must not download twice"))

        repeated = download_export_zip(
            self.database_dir,
            runtime_dir=self.runtime_dir,
            downloader=forbidden,
            now=NOW,
        )
        self.assertEqual(repeated["action"], "ALREADY_DOWNLOADED")
        self.assertEqual(forbidden.calls, 0)
        self.assertEqual(
            len(list((self.runtime_dir / DOWNLOAD_DIRECTORY_NAME).glob("*.zip"))),
            1,
        )

    def test_account_mismatch_and_expired_link_fail_before_network(self) -> None:
        self.make_link_ready()
        binding_path = self.runtime_dir / ACCOUNT_BINDING_FILENAME
        binding = json.loads(binding_path.read_text(encoding="utf-8"))
        binding["account_digest"] = "f" * 64
        binding_path.write_text(
            json.dumps(binding, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        binding_path.chmod(0o600)
        forbidden = FixtureDownloader(AssertionError("must not download"))
        with self.assertRaises(ExportDownloadError) as raised:
            download_export_zip(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                downloader=forbidden,
                now=NOW,
            )
        self.assertEqual(raised.exception.code, "export_download_account_mismatch")
        self.assertEqual(forbidden.calls, 0)

        binding["account_digest"] = json.loads(
            (self.runtime_dir / PRIVATE_LINK_FILENAME).read_text(encoding="utf-8")
        )["account_digest"]
        binding_path.write_text(
            json.dumps(binding, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )
        binding_path.chmod(0o600)
        with self.assertRaises(ExportDownloadError) as raised:
            download_export_zip(
                self.database_dir,
                runtime_dir=self.runtime_dir,
                downloader=forbidden,
                now=datetime(2026, 7, 17, 10, 0, tzinfo=timezone.utc),
            )
        self.assertEqual(raised.exception.code, "export_download_link_expired")
        self.assertEqual(forbidden.calls, 0)

    def test_zip_validator_rejects_unsafe_duplicate_and_missing_conversation_members(self) -> None:
        fixtures: list[tuple[str, bytes]] = []

        traversal = io.BytesIO()
        with zipfile.ZipFile(traversal, "w") as archive:
            archive.writestr("../conversations.json", "[]")
        fixtures.append(("export_download_zip_member_unsafe", traversal.getvalue()))

        duplicate = io.BytesIO()
        with zipfile.ZipFile(duplicate, "w") as archive:
            archive.writestr("conversations.json", "[]")
            with mock.patch("warnings.warn"):
                archive.writestr("Conversations.json", "[]")
        fixtures.append(("export_download_zip_member_duplicate", duplicate.getvalue()))

        collapsed = io.BytesIO()
        with zipfile.ZipFile(collapsed, "w") as archive:
            archive.writestr("nested//conversations.json", "[]")
        fixtures.append(("export_download_zip_member_unsafe", collapsed.getvalue()))

        missing = io.BytesIO()
        with zipfile.ZipFile(missing, "w") as archive:
            archive.writestr("chat.html", "fixture")
        fixtures.append(("export_download_conversations_missing", missing.getvalue()))

        for expected_code, payload in fixtures:
            with self.subTest(expected_code=expected_code):
                path = self.base / f"{expected_code}.zip"
                path.write_bytes(payload)
                with self.assertRaises(ExportDownloadError) as raised:
                    validate_downloaded_zip(path)
                self.assertEqual(raised.exception.code, expected_code)

    def test_https_transport_disables_proxy_cookie_and_auth_and_streams_exact_bytes(self) -> None:
        payload = official_zip_bytes()

        class Headers:
            def get_content_type(self) -> str:
                return "application/zip"

            def get(self, name: str) -> str | None:
                return str(len(payload)) if name == "Content-Length" else None

        class Response:
            headers = Headers()

            def __init__(self) -> None:
                self.buffer = io.BytesIO(payload)

            def __enter__(self) -> "Response":
                return self

            def __exit__(self, *_args: object) -> None:
                return None

            def getcode(self) -> int:
                return 200

            def geturl(self) -> str:
                return LINK

            def read(self, size: int) -> bytes:
                return self.buffer.read(size)

        class Opener:
            def __init__(self) -> None:
                self.request: object | None = None
                self.timeout: object | None = None

            def open(self, request: object, *, timeout: object) -> Response:
                self.request = request
                self.timeout = timeout
                return Response()

        opener = Opener()
        handlers: tuple[object, ...] = ()

        def build_opener(*values: object) -> Opener:
            nonlocal handlers
            handlers = values
            return opener

        resolver = lambda *_args, **_kwargs: [  # noqa: E731
            (2, 1, 6, "", ("93.184.216.34", 443))
        ]
        destination = self.base / "transport.zip"
        with mock.patch.object(download_module.urllib_request, "build_opener", build_opener):
            result = download_module._download_https(  # noqa: SLF001
                LINK,
                destination,
                resolver=resolver,
            )

        self.assertEqual(destination.read_bytes(), payload)
        self.assertEqual(result["bytes_downloaded"], len(payload))
        self.assertEqual(opener.timeout, 30)
        self.assertIsNotNone(opener.request)
        request_headers = dict(opener.request.header_items())  # type: ignore[union-attr]
        self.assertNotIn("Authorization", request_headers)
        self.assertNotIn("Cookie", request_headers)
        proxy_handlers = [
            handler
            for handler in handlers
            if isinstance(handler, download_module.urllib_request.ProxyHandler)
        ]
        self.assertEqual(len(proxy_handlers), 1)
        self.assertEqual(proxy_handlers[0].proxies, {})

        with self.assertRaises(ExportDownloadError) as raised:
            download_module._download_https(  # noqa: SLF001
                "https://127.0.0.1/export.zip",
                self.base / "forbidden.zip",
                resolver=resolver,
            )
        self.assertEqual(raised.exception.code, "export_download_redirect_unsafe")

    def test_cli_requires_confirmation_and_emits_no_private_values(self) -> None:
        self.make_link_ready()
        args = Namespace(
            database_dir=self.database_dir,
            runtime_dir=self.runtime_dir,
            inspect=False,
            download=True,
            confirm_download=False,
        )
        output = io.StringIO()
        with redirect_stdout(output):
            code = run_chatgpt_export_download(args)
        failure = json.loads(output.getvalue())
        self.assertEqual(code, 2)
        self.assertEqual(failure["error_code"], "export_download_confirmation_required")
        self.assertNotIn(LINK, output.getvalue())
        self.assertNotIn(ACCOUNT, output.getvalue().casefold())
        self.assertNotIn(str(self.runtime_dir), output.getvalue())


if __name__ == "__main__":
    unittest.main()
