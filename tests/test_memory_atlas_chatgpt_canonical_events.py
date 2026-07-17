from __future__ import annotations

import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_canonical_events import (  # noqa: E402
    EVENTS_RELATIVE,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    ChatGPTCanonicalEventError,
    build_chatgpt_canonical_event,
    commit_chatgpt_canonical_events,
    load_chatgpt_canonical_event_contract,
    load_chatgpt_canonical_event_model_parameters,
    plan_chatgpt_canonical_events,
    validate_chatgpt_canonical_event_contract,
    validate_chatgpt_canonical_event_model_parameters,
)


SYNC_SCRIPT = SCRIPTS / "sync_chatgpt_memory_data.py"
ATLASCTL_SCRIPT = SCRIPTS / "atlasctl.py"


def normalized_conversation(
    text: str,
    *,
    conversation_id: str = "conversation-source-1",
    message_id: str = "message-source-1",
    updated_at: str = "2026-07-17T00:01:00Z",
) -> dict[str, object]:
    return {
        "schema_version": "memory_atlas_public_raw_chatgpt.v1",
        "source_id": "chatgpt",
        "conversation_id": conversation_id,
        "title": "Stable identity fixture",
        "created_at": "2026-07-17T00:00:00Z",
        "updated_at": updated_at,
        "message_count": 1,
        "messages": [
            {
                "message_id": message_id,
                "role": "user",
                "created_at": "2026-07-17T00:00:30Z",
                "text": text,
                "attachments": [],
                "source_extensions": {"future_message_field": "preserved"},
                "author_extensions": {"name": "fixture"},
                "content_extensions": {"content_type": "text"},
            }
        ],
        "source_extensions": {"future_conversation_field": "preserved"},
        "parser_provenance": {
            "source_ref": "conversations.json",
            "item_index": 0,
        },
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": "official_export_fallback",
        "redact_for_public_backup": False,
        "redaction_counts": {},
        "content_sha256": "f" * 64,
    }


def export_payload(text: str, *, update_time: int = 1_760_000_060) -> list[dict[str, object]]:
    return [
        {
            "id": "conv-stable",
            "title": "Versioned conversation",
            "create_time": 1_760_000_000,
            "update_time": update_time,
            "mapping": {
                "message-node": {
                    "id": "message-node",
                    "message": {
                        "id": "msg-stable",
                        "author": {"role": "user"},
                        "create_time": 1_760_000_001,
                        "content": {"content_type": "text", "parts": [text]},
                    },
                }
            },
        }
    ]


def install_raw_ledger_contract(database: Path) -> None:
    source = ROOT / "config/data_sources/raw_ledger.json"
    target = database / "config/data_sources/raw_ledger.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(source.read_bytes())


def run_sync(
    database: Path,
    export_path: Path,
    *,
    expect_success: bool = True,
) -> dict[str, object]:
    result = subprocess.run(
        [
            sys.executable,
            str(SYNC_SCRIPT),
            "--database-dir",
            str(database),
            "--official-export",
            str(export_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if expect_success and result.returncode != 0:
        raise AssertionError(f"sync failed\nstdout={result.stdout}\nstderr={result.stderr}")
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"sync unexpectedly passed\nstdout={result.stdout}")
    return json.loads(result.stdout[result.stdout.find("{") :])


class ChatGPTCanonicalEventContractTests(unittest.TestCase):
    def test_contract_and_model_are_strict_and_task_bounded(self) -> None:
        contract = load_chatgpt_canonical_event_contract(ROOT)
        model = load_chatgpt_canonical_event_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["task_id"], "S09-P1-T2")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S09-P1-T2")
        self.assertEqual(
            contract["outputs"]["canonical_events"],
            "data/processed/conversations/chatgpt_canonical_events.jsonl",
        )
        self.assertIs(contract["append_only"]["raw_never_overwritten"], True)
        self.assertIs(contract["phase_boundary"]["implements_derived_facets"], False)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S09-P1-T3")

    def test_contract_and_model_drift_fail_closed(self) -> None:
        contract = copy.deepcopy(EXPECTED_CONTRACT)
        contract["append_only"]["raw_never_overwritten"] = False
        with self.assertRaises(ChatGPTCanonicalEventError):
            validate_chatgpt_canonical_event_contract(contract)

        model = copy.deepcopy(EXPECTED_MODEL_PARAMETERS)
        model["formulas"]["conversation_version_id"] = "mutable"
        with self.assertRaises(ChatGPTCanonicalEventError):
            validate_chatgpt_canonical_event_model_parameters(model)

    def test_atlasctl_dry_run_exposes_canonical_output_without_writes(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ATLASCTL_SCRIPT),
                "sync",
                "--source",
                "chatgpt",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(
            payload["canonical_events"]["events_path"],
            "data/processed/conversations/chatgpt_canonical_events.jsonl",
        )
        self.assertIs(payload["canonical_events"]["writes_files"], False)


class ChatGPTCanonicalIdentityTests(unittest.TestCase):
    def test_content_change_keeps_stable_ids_and_creates_new_hashes(self) -> None:
        first = build_chatgpt_canonical_event(
            normalized_conversation("first text"),
            raw_ref="data/public_raw/chatgpt/conv.first.json",
            export_sha256="a" * 64,
            observed_at="2026-07-17T01:00:00Z",
        )
        second = build_chatgpt_canonical_event(
            normalized_conversation(
                "edited text",
                updated_at="2026-07-17T00:02:00Z",
            ),
            raw_ref="data/public_raw/chatgpt/conv.second.json",
            export_sha256="b" * 64,
            observed_at="2026-07-17T02:00:00Z",
        )

        self.assertEqual(first["conversation_id"], second["conversation_id"])
        self.assertEqual(
            first["conversation"]["messages"][0]["message_id"],
            second["conversation"]["messages"][0]["message_id"],
        )
        self.assertNotEqual(
            first["conversation"]["messages"][0]["message_sha256"],
            second["conversation"]["messages"][0]["message_sha256"],
        )
        self.assertNotEqual(first["version_id"], second["version_id"])
        self.assertNotEqual(first["version_sha256"], second["version_sha256"])

    def test_transport_provenance_does_not_change_version_identity(self) -> None:
        row = normalized_conversation("same text")
        first = build_chatgpt_canonical_event(
            row,
            raw_ref="data/public_raw/chatgpt/first.json",
            export_sha256="a" * 64,
            observed_at="2026-07-17T01:00:00Z",
        )
        second = build_chatgpt_canonical_event(
            row,
            raw_ref="data/public_raw/chatgpt/second.json",
            export_sha256="b" * 64,
            observed_at="2026-07-17T02:00:00Z",
        )
        self.assertEqual(first["version_id"], second["version_id"])
        self.assertEqual(first["version_sha256"], second["version_sha256"])

    def test_duplicate_message_identity_fails_closed(self) -> None:
        row = normalized_conversation("first")
        duplicate = copy.deepcopy(row["messages"][0])
        duplicate["text"] = "second"
        row["messages"].append(duplicate)
        row["message_count"] = 2
        with self.assertRaises(ChatGPTCanonicalEventError):
            build_chatgpt_canonical_event(
                row,
                raw_ref="data/public_raw/chatgpt/duplicate.json",
                export_sha256="a" * 64,
                observed_at="2026-07-17T01:00:00Z",
            )


class ChatGPTCanonicalIncrementalTests(unittest.TestCase):
    def test_plan_commit_replay_and_new_version_form_append_only_chain(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            first_row = normalized_conversation("first")
            first_plan = plan_chatgpt_canonical_events(
                database,
                [first_row],
                [Path("data/public_raw/chatgpt/first.json")],
                export_sha256="a" * 64,
                observed_at="2026-07-17T01:00:00Z",
            )
            first_result = commit_chatgpt_canonical_events(database, first_plan)
            self.assertEqual(first_result["appended_version_count"], 1)
            ledger = database / EVENTS_RELATIVE
            first_bytes = ledger.read_bytes()

            replay_plan = plan_chatgpt_canonical_events(
                database,
                [first_row],
                [Path("data/public_raw/chatgpt/first.json")],
                export_sha256="b" * 64,
                observed_at="2026-07-17T02:00:00Z",
            )
            replay_result = commit_chatgpt_canonical_events(database, replay_plan)
            self.assertEqual(replay_result["appended_version_count"], 0)
            self.assertEqual(ledger.read_bytes(), first_bytes)

            second_plan = plan_chatgpt_canonical_events(
                database,
                [normalized_conversation("edited")],
                [Path("data/public_raw/chatgpt/second.json")],
                export_sha256="c" * 64,
                observed_at="2026-07-17T03:00:00Z",
            )
            second_result = commit_chatgpt_canonical_events(database, second_plan)
            self.assertEqual(second_result["appended_version_count"], 1)
            rows = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual([row["version_number"] for row in rows], [1, 2])
            self.assertIsNone(rows[0]["previous_version_id"])
            self.assertEqual(rows[1]["previous_version_id"], rows[0]["version_id"])
            self.assertTrue(ledger.read_bytes().startswith(first_bytes))

    def test_changed_export_preserves_old_raw_and_replay_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            export_path = database / "conversations.json"
            install_raw_ledger_contract(database)
            export_path.write_text(json.dumps(export_payload("first")), encoding="utf-8")
            source_before = export_path.read_bytes()

            first = run_sync(database, export_path)
            first_raw = database / str(first["raw_paths"][0])
            first_raw_bytes = first_raw.read_bytes()
            self.assertEqual(first["canonical_events"]["appended_version_count"], 1)
            self.assertEqual(export_path.read_bytes(), source_before)

            export_path.write_text(
                json.dumps(export_payload("edited", update_time=1_760_000_120)),
                encoding="utf-8",
            )
            second = run_sync(database, export_path)
            second_raw = database / str(second["raw_paths"][0])
            self.assertNotEqual(first_raw, second_raw)
            self.assertTrue(first_raw.exists())
            self.assertEqual(first_raw.read_bytes(), first_raw_bytes)
            self.assertEqual(second["canonical_events"]["appended_version_count"], 1)

            ledger = database / EVENTS_RELATIVE
            rows = [json.loads(line) for line in ledger.read_text().splitlines()]
            self.assertEqual(len(rows), 2)
            self.assertEqual(rows[0]["conversation_id"], rows[1]["conversation_id"])
            self.assertEqual(
                rows[0]["conversation"]["messages"][0]["message_id"],
                rows[1]["conversation"]["messages"][0]["message_id"],
            )
            ledger_before_replay = ledger.read_bytes()
            replay = run_sync(database, export_path)
            self.assertEqual(replay["canonical_events"]["appended_version_count"], 0)
            self.assertEqual(ledger.read_bytes(), ledger_before_replay)
            self.assertEqual(len(list((database / "data/public_raw/chatgpt").glob("conv-stable.*.json"))), 2)
            self.assertFalse((database / "data/derived/chatgpt/chatgpt_facets.jsonl").exists())
            self.assertFalse((database / "data/derived/chatgpt/chatgpt_universe_state_input.json").exists())

    def test_invalid_existing_ledger_fails_before_raw_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            export_path = database / "conversations.json"
            export_path.write_text(json.dumps(export_payload("first")), encoding="utf-8")
            install_raw_ledger_contract(database)
            ledger = database / EVENTS_RELATIVE
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text("not-json\n", encoding="utf-8")

            result = run_sync(database, export_path, expect_success=False)
            self.assertEqual(result["reason"], "canonical_event_violation")
            self.assertFalse((database / "data/public_raw/chatgpt").exists())
            self.assertEqual(ledger.read_text(encoding="utf-8"), "not-json\n")


if __name__ == "__main__":
    unittest.main()
