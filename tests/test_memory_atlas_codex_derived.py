from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from memory_atlas_cli.codex_derived import (  # noqa: E402
    CONTRACT_PATH,
    EXPECTED_OUTPUTS,
    EXPECTED_PHASE_BOUNDARY,
    CodexDerivedError,
    _derived_lock,
    _validate_output_privacy,
    build_codex_derived,
    load_codex_derived_contract,
    validate_codex_derived_contract,
)
from memory_atlas_cli.codex_public_raw_archive import (  # noqa: E402
    ARCHIVE_ROOT,
    build_codex_public_raw_archive,
)
from memory_atlas_cli.codex_sync_state import sync_codex_public_raw_incremental  # noqa: E402
from test_memory_atlas_codex_public_raw_archive import (  # noqa: E402
    SYNTHETIC_VALUE,
    make_codex_fixture,
    make_database_fixture,
    tree_evidence,
    write_jsonl,
)


def add_session(codex_home: Path, relative: str, session_id: str, timestamp: str, text: str) -> Path:
    path = codex_home / relative
    write_jsonl(
        path,
        [
            {
                "timestamp": timestamp,
                "type": "session_meta",
                "payload": {
                    "id": session_id,
                    "timestamp": timestamp,
                    "cwd": "/Users/example/private/project",
                    "originator": "codex_cli_rs",
                    "cli_version": "1.2.3",
                },
            },
            {
                "timestamp": timestamp,
                "type": "response_item",
                "payload": {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": text}],
                },
            },
            {
                "timestamp": timestamp,
                "type": "response_item",
                "payload": {
                    "type": "function_call",
                    "name": "exec_command",
                    "arguments": "{}",
                },
            },
            {
                "timestamp": timestamp,
                "type": "event_msg",
                "payload": {"type": "turn_aborted"},
            },
        ],
    )
    old_timestamp = time.time() - 600
    os.utime(path, (old_timestamp, old_timestamp))
    return path


def make_derived_fixture(parent: Path) -> tuple[Path, Path]:
    database = make_database_fixture(parent)
    model_target = database / "机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json"
    model_target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(
        ROOT / "机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json",
        model_target,
    )
    codex_home = make_codex_fixture(parent)
    base_session = add_session(
        codex_home,
        "archived_sessions/base-session.jsonl",
        "session-base",
        "2026-07-14T01:00:00Z",
        "构建 Memory Atlas validator 并验证 GitHub backup",
    )
    write_jsonl(
        codex_home / "session_index.jsonl",
        [{"id": "session-base", "thread_name": "Memory Atlas baseline"}],
    )
    source_before = tree_evidence(codex_home)
    build_codex_public_raw_archive(
        database,
        "baseline",
        operator_codex_home=codex_home,
        environ={},
    )
    assert tree_evidence(codex_home) == source_before
    sync_codex_public_raw_incremental(
        database,
        "bootstrap-noop",
        operator_codex_home=codex_home,
        environ={},
    )

    add_session(
        codex_home,
        "archived_sessions/delta-session.jsonl",
        "session-delta",
        "2026-07-15T02:00:00Z",
        "复审 Codex 数据治理和 secret 安全边界",
    )
    write_jsonl(
        codex_home / "session_index.jsonl",
        [
            {"id": "session-base", "thread_name": "Memory Atlas baseline"},
            {"id": "session-delta", "thread_name": "Codex governance delta"},
        ],
    )
    sync_codex_public_raw_incremental(
        database,
        "delta-one",
        operator_codex_home=codex_home,
        environ={},
    )
    self_check = base_session.read_text(encoding="utf-8")
    assert "Memory Atlas" in self_check
    return database, codex_home


def output_evidence(database: Path) -> dict[str, tuple[int, int, str]]:
    evidence: dict[str, tuple[int, int, str]] = {}
    for relative in EXPECTED_OUTPUTS.values():
        path = database / relative
        metadata = path.stat()
        evidence[relative] = (
            metadata.st_size,
            metadata.st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return evidence


def immutable_raw_evidence(database: Path) -> dict[str, dict[str, tuple[int, int, str]]]:
    return {
        "archives": tree_evidence(database / ARCHIVE_ROOT),
        "public": tree_evidence(database / "data/public_raw/codex"),
        "ledger": tree_evidence(database / "机器治理/证据与日志/raw_archive_manifests"),
    }


def read_jsonl(path: Path) -> list[dict[str, object]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]


class CodexDerivedTests(unittest.TestCase):
    def test_contract_freezes_archive_provenance_outputs_and_t1_boundary(self) -> None:
        contract = load_codex_derived_contract(ROOT)

        self.assertEqual(contract["task_id"], "S07-P2-T1")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S07-P2-T1")
        self.assertEqual(contract["outputs"], EXPECTED_OUTPUTS)
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        self.assertIs(contract["inputs"]["source_read_only"], True)
        self.assertEqual(
            contract["incremental"]["session_identity"], "source_relative_path"
        )
        self.assertEqual(
            contract["concurrency"],
            {
                "lock": "process_scoped_advisory_lock",
                "scope": "resolved_database_dir",
                "busy_policy": "fail_closed",
                "registration_change_policy": "fail_before_output_write",
            },
        )
        self.assertEqual(
            contract["provenance"]["required_refs"],
            [
                "public_index_ref",
                "archive_manifest_ref",
                "archive_manifest_sha256",
                "source_manifest_member",
                "archive_member",
                "archive_member_sha256",
                "source_relative_path",
                "source_sha256",
            ],
        )

        mutated = copy.deepcopy(contract)
        mutated["phase_boundary"]["does_not_update_atlas_snapshot"] = False
        with self.assertRaises(CodexDerivedError):
            validate_codex_derived_contract(mutated)

    def test_builds_events_facets_summary_universe_input_with_raw_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _codex_home = make_derived_fixture(Path(temp_dir))
            raw_before = immutable_raw_evidence(database)

            result = build_codex_derived(database)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "BUILT_FROM_IMMUTABLE_RAW")
            self.assertEqual(result["input_archive_count"], 2)
            self.assertEqual(result["parsed_archive_count"], 2)
            self.assertGreaterEqual(result["event_count"], 2)
            self.assertIs(result["raw_mutation"], False)
            self.assertIs(result["atlas_snapshot_updated"], False)
            self.assertEqual(immutable_raw_evidence(database), raw_before)

            events = read_jsonl(database / EXPECTED_OUTPUTS["events"])
            facets = read_jsonl(database / EXPECTED_OUTPUTS["facets"])
            self.assertEqual(len(events), len(facets))
            delta = next(row for row in events if row["record_id"] == "session-delta")
            provenance = delta["provenance"]
            self.assertEqual(provenance["archive_id"], "delta-one")
            self.assertEqual(provenance["source_relative_path"], "archived_sessions/delta-session.jsonl")
            for field in load_codex_derived_contract(ROOT)["provenance"]["required_refs"]:
                self.assertTrue(provenance[field])
            self.assertEqual(delta["backup_policy"], "derived_summary_not_full_raw_backup")

            delta_facet = next(row for row in facets if row["record_id"] == "session-delta")
            self.assertEqual(delta_facet["source"], "codex")
            self.assertEqual(delta_facet["task_type"], "governance")
            self.assertEqual(delta_facet["manifest_ref"], provenance["archive_manifest_ref"])
            self.assertEqual(
                {ref["ref_type"] for ref in delta_facet["evidence_refs"]},
                {"archive_manifest", "archive_member"},
            )

            behavior = json.loads(
                (database / EXPECTED_OUTPUTS["behavior_summary"]).read_text(encoding="utf-8")
            )
            universe = json.loads(
                (database / EXPECTED_OUTPUTS["universe_state_input"]).read_text(encoding="utf-8")
            )
            state = json.loads(
                (database / EXPECTED_OUTPUTS["state"]).read_text(encoding="utf-8")
            )
            self.assertEqual(behavior["session_count"], len(events))
            self.assertIs(behavior["source_truth"]["full_raw_backup"], False)
            self.assertEqual(universe["schema_version"], "memory_atlas_universe_state_fixture.v1")
            self.assertEqual(universe["source_scope"], "codex")
            self.assertEqual(
                universe["source_safety"],
                {
                    "raw_private_data_included": False,
                    "plaintext_secrets_included": False,
                    "local_absolute_paths_included": False,
                    "writeback_allowed": False,
                },
            )
            self.assertEqual(len(state["input_archives"]), 2)

            all_output = "".join(
                (database / relative).read_text(encoding="utf-8")
                for relative in EXPECTED_OUTPUTS.values()
            )
            self.assertNotIn("/Users/", all_output)
            self.assertNotIn(SYNTHETIC_VALUE, all_output)
            self.assertFalse(
                (database / "data/processed/codex/codex_session_manifest.jsonl").exists()
            )
            self.assertFalse(
                (database / "data/derived/codex/codex_agent_recommendations.json").exists()
            )

    def test_exact_repeat_verifies_inputs_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _codex_home = make_derived_fixture(Path(temp_dir))
            build_codex_derived(database)
            before = output_evidence(database)

            result = build_codex_derived(database)

            self.assertEqual(result["outcome"], "NO_CHANGES")
            self.assertIs(result["writes_files"], False)
            self.assertEqual(result["parsed_archive_count"], 0)
            self.assertEqual(output_evidence(database), before)

    def test_model_parameter_change_forces_full_rebuild_and_updates_hash(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _codex_home = make_derived_fixture(Path(temp_dir))
            first = build_codex_derived(database)
            state_path = database / EXPECTED_OUTPUTS["state"]
            first_state = json.loads(state_path.read_text(encoding="utf-8"))
            model_path = (
                database
                / "机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json"
            )
            model = json.loads(model_path.read_text(encoding="utf-8"))
            model["session_activity_formula"]["coefficients"]["user_message_count"] = 5
            model_path.write_text(
                json.dumps(model, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            second = build_codex_derived(database)
            second_state = json.loads(state_path.read_text(encoding="utf-8"))

            self.assertEqual(first["outcome"], "BUILT_FROM_IMMUTABLE_RAW")
            self.assertEqual(second["outcome"], "REBUILT_FROM_IMMUTABLE_RAW")
            self.assertEqual(second["parsed_archive_count"], 2)
            self.assertNotEqual(
                first_state["model_parameters_sha256"],
                second_state["model_parameters_sha256"],
            )

    def test_concurrent_build_fails_closed_before_read_or_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir) / "OpenAIDatabase"
            database.mkdir()
            with _derived_lock(database):
                with self.assertRaises(CodexDerivedError) as captured:
                    build_codex_derived(database)
            self.assertEqual(captured.exception.code, "codex_derived_lock_busy")

    def test_output_privacy_uses_canonical_credential_and_path_rules(self) -> None:
        with self.assertRaises(CodexDerivedError) as credential:
            _validate_output_privacy(
                {"fixture.json": b'{"token":"ghp_1234567890abcdefghijklmnopqrst"}'}
            )
        self.assertEqual(credential.exception.code, "codex_derived_output_credential")
        with self.assertRaises(CodexDerivedError) as absolute_path:
            _validate_output_privacy(
                {"fixture.json": b'{"path":"C:\\\\Users\\\\private\\\\secret"}'}
            )
        self.assertEqual(
            absolute_path.exception.code,
            "codex_derived_output_absolute_path",
        )

    def test_symlinked_output_parent_fails_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, _codex_home = make_derived_fixture(parent)
            outside = parent / "outside-derived"
            outside.mkdir()
            derived = database / "data/derived"
            derived.symlink_to(outside, target_is_directory=True)

            with self.assertRaises(CodexDerivedError) as captured:
                build_codex_derived(database)

            self.assertEqual(
                captured.exception.code,
                "codex_derived_output_parent_unsafe",
            )
            self.assertEqual(list(outside.iterdir()), [])

    def test_new_registered_archive_is_the_only_increment_parsed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, codex_home = make_derived_fixture(Path(temp_dir))
            first = build_codex_derived(database)
            add_session(
                codex_home,
                "archived_sessions/delta-two.jsonl",
                "session-delta-two",
                "2026-07-16T03:00:00Z",
                "调研 Memory Atlas automation data",
            )
            sync_codex_public_raw_incremental(
                database,
                "delta-two",
                operator_codex_home=codex_home,
                environ={},
            )

            second = build_codex_derived(database)

            self.assertEqual(second["outcome"], "INCREMENTAL_BUILD")
            self.assertEqual(second["input_archive_count"], 3)
            self.assertEqual(second["parsed_archive_count"], 1)
            self.assertEqual(second["event_count"], first["event_count"] + 1)
            events = read_jsonl(database / EXPECTED_OUTPUTS["events"])
            latest = next(row for row in events if row["record_id"] == "session-delta-two")
            self.assertEqual(latest["provenance"]["archive_id"], "delta-two")

    def test_archive_or_registration_tamper_fails_before_derived_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _codex_home = make_derived_fixture(Path(temp_dir))
            build_codex_derived(database)
            outputs_before = output_evidence(database)
            part = next((database / ARCHIVE_ROOT / "delta-one/parts").iterdir())
            payload = bytearray(part.read_bytes())
            payload[len(payload) // 2] ^= 1
            part.write_bytes(payload)

            with self.assertRaises(CodexDerivedError):
                build_codex_derived(database)
            self.assertEqual(output_evidence(database), outputs_before)

        with tempfile.TemporaryDirectory() as temp_dir:
            database, _codex_home = make_derived_fixture(Path(temp_dir))
            build_codex_derived(database)
            outputs_before = output_evidence(database)
            index = next(
                (database / "data/public_raw/codex").glob("codex_incremental_archive.delta-one.*.json")
            )
            index.unlink()

            with self.assertRaises(CodexDerivedError):
                build_codex_derived(database)
            self.assertEqual(output_evidence(database), outputs_before)


if __name__ == "__main__":
    unittest.main()
