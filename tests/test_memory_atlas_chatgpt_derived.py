from __future__ import annotations

import copy
import hashlib
import json
import shutil
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
    commit_chatgpt_canonical_events,
    plan_chatgpt_canonical_events,
)
from memory_atlas_cli.chatgpt_derived import (  # noqa: E402
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    EXPECTED_OUTPUTS,
    EXPECTED_PHASE_BOUNDARY,
    ChatGPTDerivedError,
    build_chatgpt_derived,
    load_chatgpt_derived_contract,
    load_chatgpt_derived_model_parameters,
    validate_chatgpt_derived_contract,
    validate_chatgpt_derived_model_parameters,
)


ATLASCTL = SCRIPTS / "atlasctl.py"
SYNC_SCRIPT = SCRIPTS / "sync_chatgpt_memory_data.py"
BUILDER = SCRIPTS / "build_memory_atlas_chatgpt_derived.py"
CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_derived.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_derived.v1_2_1_s09_p1_t3.json"
)


def stable_hash(value: object) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized_conversation(
    text: str,
    *,
    title: str = "Memory Atlas validator build",
    updated_at: str = "2026-07-17T00:01:00Z",
) -> dict[str, object]:
    payload: dict[str, object] = {
        "schema_version": "memory_atlas_public_raw_chatgpt.v1",
        "source_id": "chatgpt",
        "conversation_id": "conversation-source-1",
        "title": title,
        "created_at": "2026-07-17T00:00:00Z",
        "updated_at": updated_at,
        "message_count": 2,
        "messages": [
            {
                "message_id": "message-source-1",
                "role": "user",
                "created_at": "2026-07-17T00:00:30Z",
                "text": text,
                "attachments": [],
                "source_extensions": {},
                "author_extensions": {},
                "content_extensions": {"content_type": "text"},
            },
            {
                "message_id": "message-source-2",
                "role": "assistant",
                "created_at": "2026-07-17T00:00:40Z",
                "text": "Acknowledged.",
                "attachments": [],
                "source_extensions": {},
                "author_extensions": {},
                "content_extensions": {"content_type": "text"},
            },
        ],
        "source_extensions": {},
        "parser_provenance": {
            "source_ref": "conversations.json",
            "item_index": 0,
        },
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": "official_export_fallback",
        "redact_for_public_backup": False,
        "redaction_counts": {},
    }
    payload["content_sha256"] = stable_hash(payload)
    return payload


def official_export(text: str) -> list[dict[str, object]]:
    return [
        {
            "id": "conversation-source-1",
            "title": "Memory Atlas validator build",
            "create_time": 1_760_000_000,
            "update_time": 1_760_000_060,
            "mapping": {
                "message-source-1": {
                    "id": "message-source-1",
                    "message": {
                        "id": "message-source-1",
                        "author": {"role": "user"},
                        "create_time": 1_760_000_001,
                        "content": {"content_type": "text", "parts": [text]},
                    },
                }
            },
        }
    ]


def install_contracts(database: Path, *, include_raw_ledger: bool = False) -> None:
    for relative in (CONTRACT_RELATIVE, MODEL_RELATIVE):
        target = database / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)
    if include_raw_ledger:
        relative = Path("config/data_sources/raw_ledger.json")
        target = database / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / relative, target)


def append_conversation(
    database: Path,
    row: dict[str, object],
    *,
    raw_name: str,
    export_sha256: str,
    observed_at: str,
) -> Path:
    raw_relative = Path("data/public_raw/chatgpt") / raw_name
    raw_path = database / raw_relative
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    raw_path.write_text(
        json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    plan = plan_chatgpt_canonical_events(
        database,
        [row],
        [raw_relative],
        export_sha256=export_sha256,
        observed_at=observed_at,
    )
    commit_chatgpt_canonical_events(database, plan)
    return raw_path


def make_fixture(parent: Path) -> tuple[Path, Path]:
    database = parent / "OpenAIDatabase"
    database.mkdir()
    install_contracts(database)
    raw_path = append_conversation(
        database,
        normalized_conversation("source-only message body must not be persisted"),
        raw_name="conversation-source-1.first.json",
        export_sha256="a" * 64,
        observed_at="2026-07-17T01:00:00Z",
    )
    return database, raw_path


def read_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line
    ]


def file_evidence(paths: list[Path]) -> dict[str, tuple[int, int, str]]:
    return {
        str(path): (
            path.stat().st_size,
            path.stat().st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
        for path in paths
    }


def output_evidence(database: Path) -> dict[str, tuple[int, int, str]]:
    return file_evidence([database / relative for relative in EXPECTED_OUTPUTS.values()])


def assert_direct_evidence(
    case: unittest.TestCase,
    row: dict[str, object],
) -> None:
    refs = row.get("evidence_refs")
    case.assertIsInstance(refs, list)
    case.assertEqual(
        {ref["ref_type"] for ref in refs},
        {"raw", "canonical_event"},
    )
    raw_ref = next(ref for ref in refs if ref["ref_type"] == "raw")
    canonical_ref = next(
        ref for ref in refs if ref["ref_type"] == "canonical_event"
    )
    case.assertTrue(str(raw_ref["path"]).startswith("data/public_raw/chatgpt/"))
    case.assertRegex(str(raw_ref["file_sha256"]), r"^[0-9a-f]{64}$")
    case.assertEqual(
        canonical_ref["path"],
        "data/processed/conversations/chatgpt_canonical_events.jsonl",
    )
    case.assertRegex(str(canonical_ref["version_sha256"]), r"^[0-9a-f]{64}$")


class ChatGPTDerivedTests(unittest.TestCase):
    def test_contract_and_model_are_strict_and_task_bounded(self) -> None:
        contract = load_chatgpt_derived_contract(ROOT)
        model = load_chatgpt_derived_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["task_id"], "S09-P1-T3")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S09-P1-T3")
        self.assertEqual(contract["outputs"], EXPECTED_OUTPUTS)
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        self.assertEqual(
            contract["derivation"]["facet_scope"],
            "latest_canonical_version_per_conversation",
        )
        self.assertEqual(
            contract["derivation"]["activity_scope"],
            "all_canonical_version_events",
        )

        drifted_contract = copy.deepcopy(contract)
        drifted_contract["raw_evidence"]["required"] = False
        with self.assertRaises(ChatGPTDerivedError):
            validate_chatgpt_derived_contract(drifted_contract)

        drifted_model = copy.deepcopy(model)
        drifted_model["activity_formula"]["coefficients"]["user_message_count"] = 99
        with self.assertRaises(ChatGPTDerivedError):
            validate_chatgpt_derived_model_parameters(drifted_model)

    def test_builds_facets_topics_activity_and_universe_with_direct_raw_refs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, raw_path = make_fixture(Path(temp_dir))
            ledger = database / EVENTS_RELATIVE
            inputs_before = file_evidence([raw_path, ledger])

            result = build_chatgpt_derived(database)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "BUILT_FROM_CANONICAL_EVENTS")
            self.assertEqual(result["canonical_event_count"], 1)
            self.assertEqual(result["facet_count"], 1)
            self.assertEqual(result["topic_count"], 1)
            self.assertEqual(result["activity_count"], 1)
            self.assertIs(result["raw_mutation"], False)
            self.assertIs(result["canonical_mutation"], False)
            self.assertEqual(file_evidence([raw_path, ledger]), inputs_before)

            facets = read_jsonl(database / EXPECTED_OUTPUTS["facets"])
            topics = read_json(database / EXPECTED_OUTPUTS["topics"])["topics"]
            activity = read_jsonl(database / EXPECTED_OUTPUTS["activity"])
            universe = read_json(
                database / EXPECTED_OUTPUTS["universe_state_input"]
            )
            state = read_json(database / EXPECTED_OUTPUTS["state"])

            self.assertEqual(len(facets), 1)
            self.assertEqual(facets[0]["source"], "chatgpt")
            self.assertEqual(facets[0]["task_type"], "engineering")
            self.assertEqual(facets[0]["record_id"], facets[0]["conversation_id"])
            self.assertEqual(len(topics), 1)
            self.assertEqual(topics[0]["conversation_count"], 1)
            self.assertEqual(len(activity), 1)
            self.assertEqual(activity[0]["version_number"], 1)
            self.assertEqual(
                universe["schema_version"],
                "memory_atlas_universe_state_fixture.v1",
            )
            self.assertEqual(universe["source_scope"], "chatgpt")
            self.assertEqual(len(universe["clusters"]), 1)
            self.assertEqual(state["canonical_event_count"], 1)
            for row in [facets[0], topics[0], activity[0], universe["clusters"][0]]:
                assert_direct_evidence(self, row)

            all_output = "".join(
                (database / relative).read_text(encoding="utf-8")
                for relative in EXPECTED_OUTPUTS.values()
            )
            self.assertNotIn("source-only message body must not be persisted", all_output)
            self.assertNotIn("/Users/", all_output)

    def test_exact_replay_verifies_inputs_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _raw_path = make_fixture(Path(temp_dir))
            build_chatgpt_derived(database)
            before = output_evidence(database)

            result = build_chatgpt_derived(database)

            self.assertEqual(result["outcome"], "NO_CHANGES")
            self.assertIs(result["writes_files"], False)
            self.assertEqual(output_evidence(database), before)

    def test_new_canonical_version_replaces_current_facets_but_keeps_activity_history(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, first_raw = make_fixture(Path(temp_dir))
            build_chatgpt_derived(database)
            ledger = database / EVENTS_RELATIVE
            ledger_prefix = ledger.read_bytes()
            first_raw_bytes = first_raw.read_bytes()

            second_raw = append_conversation(
                database,
                normalized_conversation(
                    "edited source body",
                    updated_at="2026-07-17T00:02:00Z",
                ),
                raw_name="conversation-source-1.second.json",
                export_sha256="b" * 64,
                observed_at="2026-07-17T02:00:00Z",
            )
            inputs_before = file_evidence([first_raw, second_raw, ledger])
            result = build_chatgpt_derived(database)

            self.assertEqual(result["outcome"], "REBUILT_FROM_CANONICAL_EVENTS")
            self.assertEqual(result["canonical_event_count"], 2)
            self.assertEqual(result["facet_count"], 1)
            self.assertEqual(result["activity_count"], 2)
            self.assertTrue(ledger.read_bytes().startswith(ledger_prefix))
            self.assertEqual(first_raw.read_bytes(), first_raw_bytes)
            self.assertEqual(file_evidence([first_raw, second_raw, ledger]), inputs_before)
            facets = read_jsonl(database / EXPECTED_OUTPUTS["facets"])
            activity = read_jsonl(database / EXPECTED_OUTPUTS["activity"])
            self.assertEqual(facets[0]["version_number"], 2)
            self.assertEqual([row["version_number"] for row in activity], [1, 2])

    def test_missing_or_tampered_raw_fails_before_replacing_outputs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, raw_path = make_fixture(Path(temp_dir))
            build_chatgpt_derived(database)
            outputs_before = output_evidence(database)
            raw_path.unlink()

            with self.assertRaises(ChatGPTDerivedError) as missing:
                build_chatgpt_derived(database)
            self.assertEqual(missing.exception.code, "chatgpt_derived_raw_missing")
            self.assertEqual(output_evidence(database), outputs_before)

        with tempfile.TemporaryDirectory() as temp_dir:
            database, raw_path = make_fixture(Path(temp_dir))
            build_chatgpt_derived(database)
            outputs_before = output_evidence(database)
            payload = read_json(raw_path)
            payload["title"] = "tampered title"
            payload_without_hash = dict(payload)
            payload_without_hash.pop("content_sha256")
            payload["content_sha256"] = stable_hash(payload_without_hash)
            raw_path.write_text(json.dumps(payload), encoding="utf-8")

            with self.assertRaises(ChatGPTDerivedError) as tampered:
                build_chatgpt_derived(database)
            self.assertEqual(
                tampered.exception.code,
                "chatgpt_derived_raw_canonical_mismatch",
            )
            self.assertEqual(output_evidence(database), outputs_before)

    def test_invalid_canonical_ledger_fails_before_any_derived_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            ledger = database / EVENTS_RELATIVE
            ledger.parent.mkdir(parents=True, exist_ok=True)
            ledger.write_text("not-json\n", encoding="utf-8")

            with self.assertRaises(ChatGPTDerivedError) as captured:
                build_chatgpt_derived(database)
            self.assertEqual(
                captured.exception.code,
                "chatgpt_derived_canonical_ledger_invalid",
            )
            self.assertFalse((database / "data/derived/chatgpt").exists())

    def test_cli_and_atlasctl_dry_run_are_write_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _raw_path = make_fixture(Path(temp_dir))
            commands = (
                [
                    sys.executable,
                    str(BUILDER),
                    "--database-dir",
                    str(database),
                    "--dry-run",
                ],
                [
                    sys.executable,
                    str(ATLASCTL),
                    "analyze",
                    "--stage",
                    "chatgpt-derived",
                    "--database-dir",
                    str(database),
                    "--dry-run",
                ],
            )
            for command in commands:
                with self.subTest(command=command):
                    result = subprocess.run(
                        command,
                        cwd=ROOT,
                        text=True,
                        capture_output=True,
                        check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    payload = json.loads(result.stdout)
                    self.assertEqual(payload["status"], "PASS")
                    self.assertIs(payload["writes_files"], False)
            self.assertFalse((database / "data/derived/chatgpt").exists())

    def test_normal_chatgpt_sync_builds_derived_inputs_and_replay_is_noop(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database, include_raw_ledger=True)
            export_path = database / "conversations.json"
            export_path.write_text(
                json.dumps(official_export("sync integration fixture")),
                encoding="utf-8",
            )

            first = subprocess.run(
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
            self.assertEqual(first.returncode, 0, first.stderr)
            first_payload = json.loads(first.stdout[first.stdout.find("{") :])
            self.assertEqual(
                first_payload["derived_inputs"]["outcome"],
                "BUILT_FROM_CANONICAL_EVENTS",
            )
            for relative in EXPECTED_OUTPUTS.values():
                self.assertTrue((database / relative).is_file(), relative)
            derived_before = output_evidence(database)

            second = subprocess.run(
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
            self.assertEqual(second.returncode, 0, second.stderr)
            second_payload = json.loads(second.stdout[second.stdout.find("{") :])
            self.assertEqual(second_payload["derived_inputs"]["outcome"], "NO_CHANGES")
            self.assertIs(second_payload["derived_inputs"]["writes_files"], False)
            self.assertEqual(output_evidence(database), derived_before)

    def test_symlinked_output_parent_fails_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, _raw_path = make_fixture(parent)
            outside = parent / "outside"
            outside.mkdir()
            derived = database / "data/derived"
            derived.parent.mkdir(parents=True, exist_ok=True)
            derived.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(ChatGPTDerivedError) as captured:
                build_chatgpt_derived(database)

            self.assertEqual(
                captured.exception.code,
                "chatgpt_derived_output_parent_unsafe",
            )
            self.assertEqual(list(outside.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
