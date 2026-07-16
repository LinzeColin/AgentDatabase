from __future__ import annotations

import copy
import hashlib
import io
import json
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
from argparse import Namespace
from contextlib import redirect_stdout
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_archive import (  # noqa: E402
    CONTRACT_RELATIVE,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    MODEL_RELATIVE,
    TASK_ID,
    ChatGPTExportArchiveError,
    archive_export,
    inspect_export_archive,
    load_chatgpt_export_archive_contract,
    load_chatgpt_export_archive_model_parameters,
    run_chatgpt_export_archive,
    validate_chatgpt_export_archive_contract,
    validate_chatgpt_export_archive_model_parameters,
)
import memory_atlas_cli.chatgpt_export_archive as archive_module  # noqa: E402
from memory_atlas_cli.archive_chunking import (  # noqa: E402
    CONTRACT_PATH as CHUNK_CONTRACT_RELATIVE,
    MAX_PART_BYTES,
)
from memory_atlas_cli.archive_restore import (  # noqa: E402
    CONTRACT_PATH as RESTORE_CONTRACT_RELATIVE,
    restore_archive,
    verify_archive,
)
from memory_atlas_cli.chatgpt_export_state import (  # noqa: E402
    CONTRACT_RELATIVE as STATE_CONTRACT_RELATIVE,
    MODEL_RELATIVE as STATE_MODEL_RELATIVE,
    apply_export_transition,
    build_initial_export_state,
    load_chatgpt_export_state,
    record_export_request_outcome,
    reserve_export_request,
    write_chatgpt_export_state,
)
from memory_atlas_cli.raw_ledger import (  # noqa: E402
    RAW_LEDGER_CONTRACT_PATH as RAW_LEDGER_CONTRACT_RELATIVE,
)


REQUEST_AT = "2026-07-16T09:00:00Z"
DISPATCHED_AT = "2026-07-16T09:01:00Z"
LINK_AT = "2026-07-16T10:00:00Z"
DOWNLOADED_AT = "2026-07-16T10:10:00Z"
ARCHIVED_AT = datetime(2026, 7, 16, 10, 20, tzinfo=timezone.utc)
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


def downloaded_state(request_id: str = REQUEST_ID) -> dict[str, object]:
    state, _ = reserve_export_request(
        build_initial_export_state(),
        request_id=request_id,
        occurred_at=REQUEST_AT,
    )
    state, _ = record_export_request_outcome(
        state,
        connector_payload=connector_payload(),
        occurred_at=DISPATCHED_AT,
    )
    state, _ = apply_export_transition(
        state,
        to_state="LINK_READY",
        event_id=f"link-{request_id}",
        reason_code="official_export_link_ready",
        evidence_sha256="d" * 64,
        occurred_at=LINK_AT,
        expected_revision=state["revision"],
    )
    state, _ = apply_export_transition(
        state,
        to_state="DOWNLOADED",
        event_id=f"downloaded-{request_id}",
        reason_code="official_export_zip_downloaded",
        evidence_sha256="e" * 64,
        occurred_at=DOWNLOADED_AT,
        expected_revision=state["revision"],
    )
    return state


def write_export_zip(path: Path, *, minimum_bytes: int = 0) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_STORED, allowZip64=True) as archive:
        archive.writestr("conversations.json", "[]\n")
        if minimum_bytes:
            with archive.open("large-fixture.bin", "w", force_zip64=True) as handle:
                remaining = minimum_bytes
                block = b"x" * (1024 * 1024)
                while remaining:
                    payload = block[: min(len(block), remaining)]
                    handle.write(payload)
                    remaining -= len(payload)
    path.chmod(0o600)


def private_metadata(path: Path, request_id: str = REQUEST_ID) -> dict[str, object]:
    payload = path.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        members = archive.infolist()
        uncompressed = sum(member.file_size for member in members)
    return {
        "schema_version": "memory_atlas.chatgpt_export_private_download.v1_2_1_s08_p2_t3",
        "task_id": "S08-P2-T3",
        "request_id": request_id,
        "link_sha256": "f" * 64,
        "account_digest": "a" * 64,
        "download_sha256": digest,
        "bytes_downloaded": len(payload),
        "downloaded_at": DOWNLOADED_AT,
        "relative_path": f"chatgpt_exports/chatgpt-export-{digest}.zip",
        "zip_member_count": len(members),
        "conversations_member_count": 1,
        "uncompressed_bytes": uncompressed,
        "transport": {
            "content_type": "application/zip",
            "final_url_sha256": "9" * 64,
            "redirect_count": 0,
        },
    }


class ChatGPTExportArchiveTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve()
        self.repo_root = self.base / "repo"
        self.repo_root.mkdir()
        (self.repo_root / ".git").mkdir()
        self.database_dir = self.repo_root / "OpenAIDatabase"
        for relative in (
            CONTRACT_RELATIVE,
            MODEL_RELATIVE,
            CHUNK_CONTRACT_RELATIVE,
            RESTORE_CONTRACT_RELATIVE,
            RAW_LEDGER_CONTRACT_RELATIVE,
            STATE_CONTRACT_RELATIVE,
            STATE_MODEL_RELATIVE,
        ):
            target = self.database_dir / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes((ROOT / relative).read_bytes())
        write_chatgpt_export_state(self.database_dir, build_initial_export_state())
        self.private_zip = self.base / "chatgpt-export.zip"
        write_export_zip(self.private_zip)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def loader(self, request_id: str = REQUEST_ID):
        metadata = private_metadata(self.private_zip, request_id=request_id)
        return lambda *_args, **_kwargs: (self.private_zip, metadata)

    def test_contract_and_model_are_exact_and_preserve_phase_boundary(self) -> None:
        contract = load_chatgpt_export_archive_contract(self.database_dir)
        model = load_chatgpt_export_archive_model_parameters(self.database_dir)

        self.assertEqual(TASK_ID, "S08-P3-T1")
        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["state_gate"]["required_state"], "DOWNLOADED")
        self.assertEqual(contract["state_gate"]["success_state"], "ARCHIVED")
        self.assertEqual(contract["append_only"]["archive_identity"], "download_sha256")
        self.assertTrue(contract["append_only"]["raw_ledger_required"])
        self.assertFalse(contract["phase_boundary"]["parses_export"])
        self.assertEqual(contract["phase_boundary"]["next_task"], "S08-P3-T2")

    def test_contract_and_model_drift_fail_closed(self) -> None:
        contract = copy.deepcopy(EXPECTED_CONTRACT)
        contract["archive"]["maximum_part_bytes"] += 1
        with self.assertRaises(ChatGPTExportArchiveError) as raised:
            validate_chatgpt_export_archive_contract(contract)
        self.assertEqual(raised.exception.code, "export_archive_contract_drift")

        model = copy.deepcopy(EXPECTED_MODEL_PARAMETERS)
        model["parameters"]["maximum_part_bytes"] += 1
        with self.assertRaises(ChatGPTExportArchiveError) as raised:
            validate_chatgpt_export_archive_model_parameters(model)
        self.assertEqual(raised.exception.code, "export_archive_model_drift")

    def test_idle_inspect_stops_before_private_or_raw_access(self) -> None:
        private_loader = mock.Mock(side_effect=AssertionError("private access"))
        with mock.patch.object(
            archive_module,
            "preflight_raw_ledger",
            side_effect=AssertionError("raw access"),
        ):
            result = inspect_export_archive(
                self.database_dir,
                runtime_dir=self.base / "missing-private-runtime",
                private_loader=private_loader,
            )

        self.assertEqual(result["action"], "STATE_NOT_ELIGIBLE")
        self.assertEqual(result["export_state"], "IDLE")
        self.assertFalse(result["eligible_for_archive"])
        self.assertEqual(result["private_runtime_reads"], 0)
        self.assertEqual(result["raw_archive_reads"], 0)
        private_loader.assert_not_called()

    def test_archive_publishes_single_part_index_ledger_and_state(self) -> None:
        write_chatgpt_export_state(self.database_dir, downloaded_state())

        result = archive_export(
            self.database_dir,
            runtime_dir=self.base / "private-runtime",
            private_loader=self.loader(),
            clock=lambda: ARCHIVED_AT,
        )

        self.assertEqual(result["action"], "ARCHIVED")
        self.assertEqual(result["export_state"], "ARCHIVED")
        self.assertEqual(result["part_count"], 1)
        self.assertFalse(result["private_path_emitted"])
        self.assertFalse(result["account_or_link_value_emitted"])
        verification = verify_archive(
            self.database_dir,
            "chatgpt",
            result["archive_id"],
        )
        self.assertEqual(verification["package_verification"], "PASS")
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "ARCHIVED")
        self.assertTrue((self.database_dir / result["public_index_path"]).is_file())
        self.assertTrue((self.database_dir / result["raw_manifest_path"]).is_file())
        public_index = json.loads(
            (self.database_dir / result["public_index_path"]).read_text(
                encoding="utf-8"
            )
        )
        serialized_index = json.dumps(public_index, ensure_ascii=False)
        self.assertNotIn(str(self.private_zip), serialized_index)
        self.assertNotIn("relative_path", public_index["download_metadata"])
        self.assertEqual(public_index["request_metadata"]["origin_state"], "IDLE")

        no_private = mock.Mock(side_effect=AssertionError("private access"))
        replay = archive_export(
            self.database_dir,
            runtime_dir=self.base / "missing-private-runtime",
            private_loader=no_private,
            clock=lambda: ARCHIVED_AT,
        )
        self.assertEqual(replay["action"], "ALREADY_ARCHIVED")
        self.assertEqual(replay["part_count"], 1)
        self.assertGreater(replay["largest_part_bytes"], 0)
        no_private.assert_not_called()
        self.assertEqual(
            len(list((self.database_dir / "data/raw_archives/chatgpt").iterdir())),
            1,
        )

    def test_large_export_uses_45_mib_parts_and_restores_exactly(self) -> None:
        write_export_zip(self.private_zip, minimum_bytes=MAX_PART_BYTES + 123)
        write_chatgpt_export_state(self.database_dir, downloaded_state())

        result = archive_export(
            self.database_dir,
            runtime_dir=self.base / "private-runtime",
            private_loader=self.loader(),
            clock=lambda: ARCHIVED_AT,
        )

        self.assertEqual(result["part_count"], 2)
        self.assertLessEqual(result["largest_part_bytes"], MAX_PART_BYTES)
        restored = self.base / "restored.zip"
        restored_result = restore_archive(
            self.database_dir,
            "chatgpt",
            result["archive_id"],
            restored,
        )
        self.assertEqual(restored_result["package_verification"], "PASS")
        self.assertEqual(restored.read_bytes(), self.private_zip.read_bytes())

    def test_state_write_failure_recovers_without_duplicate_archive_or_index(self) -> None:
        write_chatgpt_export_state(self.database_dir, downloaded_state())

        def fail_state_write(_root: Path, _payload: dict[str, object]) -> None:
            raise OSError("fixture state failure")

        with self.assertRaises(ChatGPTExportArchiveError) as raised:
            archive_export(
                self.database_dir,
                runtime_dir=self.base / "private-runtime",
                private_loader=self.loader(),
                state_writer=fail_state_write,
                clock=lambda: ARCHIVED_AT,
            )
        self.assertEqual(raised.exception.code, "export_archive_state_write_failed")
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "DOWNLOADED")

        recovered = archive_export(
            self.database_dir,
            runtime_dir=self.base / "private-runtime",
            private_loader=self.loader(),
            clock=lambda: ARCHIVED_AT,
        )
        self.assertEqual(recovered["action"], "ARCHIVED")
        self.assertTrue(recovered["archive_idempotent"])
        self.assertTrue(recovered["public_index_idempotent"])
        self.assertEqual(
            len(list((self.database_dir / "data/raw_archives/chatgpt").iterdir())),
            1,
        )
        self.assertEqual(
            len(list((self.database_dir / "data/public_raw/chatgpt").glob("chatgpt_raw_archive.*.json"))),
            1,
        )

    def test_same_hash_new_request_reuses_archive_and_appends_provenance(self) -> None:
        write_chatgpt_export_state(self.database_dir, downloaded_state())
        first = archive_export(
            self.database_dir,
            runtime_dir=self.base / "private-runtime",
            private_loader=self.loader(),
            clock=lambda: ARCHIVED_AT,
        )
        second_request = "2" * 32
        write_chatgpt_export_state(self.database_dir, downloaded_state(second_request))

        second = archive_export(
            self.database_dir,
            runtime_dir=self.base / "private-runtime",
            private_loader=self.loader(second_request),
            clock=lambda: ARCHIVED_AT,
        )

        self.assertEqual(second["archive_id"], first["archive_id"])
        self.assertTrue(second["archive_idempotent"])
        self.assertNotEqual(second["public_index_path"], first["public_index_path"])
        self.assertEqual(
            len(list((self.database_dir / "data/raw_archives/chatgpt").iterdir())),
            1,
        )
        self.assertEqual(
            len(list((self.database_dir / "data/public_raw/chatgpt").glob("chatgpt_raw_archive.*.json"))),
            2,
        )

    def test_request_mismatch_fails_before_raw_write(self) -> None:
        write_chatgpt_export_state(self.database_dir, downloaded_state())

        with self.assertRaises(ChatGPTExportArchiveError) as raised:
            archive_export(
                self.database_dir,
                runtime_dir=self.base / "private-runtime",
                private_loader=self.loader("2" * 32),
                clock=lambda: ARCHIVED_AT,
            )

        self.assertEqual(raised.exception.code, "export_archive_request_mismatch")
        self.assertFalse((self.database_dir / "data/raw_archives").exists())
        self.assertEqual(load_chatgpt_export_state(self.database_dir)["status"], "DOWNLOADED")

    def test_cli_requires_confirmation_and_never_emits_private_values(self) -> None:
        stream = io.StringIO()
        with redirect_stdout(stream):
            exit_code = run_chatgpt_export_archive(
                Namespace(
                    inspect=False,
                    archive=True,
                    confirm_archive=False,
                    database_dir=self.database_dir,
                    runtime_dir=self.base / "private-runtime",
                )
            )
        payload = json.loads(stream.getvalue())

        self.assertEqual(exit_code, 2)
        self.assertEqual(payload["error_code"], "export_archive_confirmation_required")
        self.assertFalse(payload["private_path_emitted"])
        self.assertFalse(payload["account_or_link_value_emitted"])


if __name__ == "__main__":
    unittest.main()
