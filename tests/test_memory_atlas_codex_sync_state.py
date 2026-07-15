from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
TESTS = Path(__file__).resolve().parent
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))
if str(TESTS) not in sys.path:
    sys.path.insert(0, str(TESTS))

from memory_atlas_cli.codex_public_raw_archive import (  # noqa: E402
    ARCHIVE_ROOT,
    build_codex_public_raw_archive,
    verify_codex_public_raw_archive,
)
from memory_atlas_cli.codex_sync_state import (  # noqa: E402
    CONTRACT_PATH,
    EXPECTED_PHASE_BOUNDARY,
    STATE_PATH,
    CodexSyncStateError,
    load_codex_sync_state_contract,
    run_codex_sync_state,
    sync_codex_public_raw_incremental,
    validate_codex_sync_state_contract,
    verify_codex_incremental_archive,
)
from memory_atlas_cli.parser import parse_args  # noqa: E402
from test_memory_atlas_codex_public_raw_archive import (  # noqa: E402
    make_codex_fixture,
    make_database_fixture,
    tree_evidence,
    write_jsonl,
)


def archive_ids(database: Path) -> list[str]:
    root = database / ARCHIVE_ROOT
    return sorted(path.name for path in root.iterdir() if path.is_dir())


def public_indexes(database: Path) -> list[Path]:
    return sorted((database / "data/public_raw/codex").glob("codex_*archive.*.json"))


def prepare_baseline(parent: Path) -> tuple[Path, Path]:
    database = make_database_fixture(parent)
    codex_home = make_codex_fixture(parent)
    build_codex_public_raw_archive(
        database,
        "baseline",
        operator_codex_home=codex_home,
        environ={},
    )
    return database, codex_home


def add_stable_jsonl(codex_home: Path, relative: str, rows: list[object]) -> Path:
    path = codex_home / relative
    write_jsonl(path, rows)
    old_timestamp = time.time() - 600
    os.utime(path, (old_timestamp, old_timestamp))
    return path


class CodexSyncStateTests(unittest.TestCase):
    def test_contract_freezes_cursor_dedupe_resume_and_t3_boundary(self) -> None:
        contract = load_codex_sync_state_contract(ROOT)

        self.assertEqual(contract["task_id"], "S07-P1-T3")
        self.assertEqual(contract["state_path"], STATE_PATH.as_posix())
        self.assertEqual(contract["cursor"]["content_hash_algorithm"], "sha256")
        self.assertEqual(contract["deduplication"]["key"], "source_sha256")
        self.assertEqual(
            contract["resume"]["phases"],
            [
                "PLANNED",
                "ARCHIVE_PUBLISHED",
                "PUBLIC_INDEX_PUBLISHED",
                "LEDGER_RECORDED",
            ],
        )
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        registry = json.loads(
            (ROOT / "config/data_sources/source_registry.json").read_text(encoding="utf-8")
        )
        codex = next(
            source for source in registry["sync_sources"] if source["source_id"] == "codex"
        )
        self.assertEqual(
            codex["parser"]["sync_state_contract_ref"],
            CONTRACT_PATH.as_posix(),
        )
        self.assertEqual(
            codex["parser"]["sync_state_entrypoint"],
            "scripts/memory_atlas_cli/codex_sync_state.py",
        )

        mutated = copy.deepcopy(contract)
        mutated["deduplication"]["key"] = "relative_path"
        with self.assertRaises(CodexSyncStateError):
            validate_codex_sync_state_contract(mutated)

    def test_bootstrap_and_exact_repeat_create_state_without_duplicate_archive(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            source_before = tree_evidence(codex_home)

            first = sync_codex_public_raw_incremental(
                database,
                "noop-run",
                operator_codex_home=codex_home,
                environ={},
            )
            state_path = database / STATE_PATH
            state_bytes = state_path.read_bytes()
            second = sync_codex_public_raw_incremental(
                database,
                "noop-run",
                operator_codex_home=codex_home,
                environ={},
            )

            self.assertEqual(first["outcome"], "CURSOR_INITIALIZED_NO_NEW_CONTENT")
            self.assertEqual(second["outcome"], "NO_CHANGES")
            self.assertIs(second["idempotent"], True)
            self.assertIs(second["writes_files"], False)
            self.assertEqual(state_path.read_bytes(), state_bytes)
            self.assertEqual(archive_ids(database), ["baseline"])
            self.assertEqual(len(public_indexes(database)), 1)
            self.assertEqual(tree_evidence(codex_home), source_before)

    def test_new_content_archives_once_and_repeat_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            add_stable_jsonl(
                codex_home,
                "archived_sessions/new-session.jsonl",
                [{"type": "message", "payload": {"text": "new public transcript"}}],
            )
            source_before = tree_evidence(codex_home)

            first = sync_codex_public_raw_incremental(
                database,
                "delta-one",
                operator_codex_home=codex_home,
                environ={},
            )
            state_path = database / STATE_PATH
            state_bytes = state_path.read_bytes()
            verified = verify_codex_incremental_archive(database, "delta-one")
            second = sync_codex_public_raw_incremental(
                database,
                "delta-one",
                operator_codex_home=codex_home,
                environ={},
            )

            self.assertEqual(first["outcome"], "ARCHIVED_NEW_CONTENT")
            self.assertEqual(first["new_path_count"], 1)
            self.assertEqual(first["new_content_count"], 1)
            self.assertEqual(verified["status"], "PASS")
            self.assertEqual(verified["unique_content_count"], 1)
            self.assertEqual(second["outcome"], "NO_CHANGES")
            self.assertEqual(state_path.read_bytes(), state_bytes)
            self.assertEqual(archive_ids(database), ["baseline", "delta-one"])
            self.assertEqual(len(public_indexes(database)), 2)
            self.assertEqual(tree_evidence(codex_home), source_before)

    def test_identical_new_paths_store_one_member_and_restore_alias(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            rows = [{"type": "message", "payload": {"text": "same bytes"}}]
            add_stable_jsonl(codex_home, "archived_sessions/alias-a.jsonl", rows)
            add_stable_jsonl(codex_home, "archived_sessions/alias-b.jsonl", rows)

            result = sync_codex_public_raw_incremental(
                database,
                "delta-alias",
                operator_codex_home=codex_home,
                environ={},
            )
            verified = verify_codex_incremental_archive(database, "delta-alias")
            output = parent / "restored-alias"
            restore = subprocess.run(
                [
                    str(database / ARCHIVE_ROOT / "delta-alias/restore.sh"),
                    str(output),
                ],
                cwd=database / ARCHIVE_ROOT / "delta-alias",
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result["new_path_count"], 2)
            self.assertEqual(result["new_content_count"], 1)
            self.assertEqual(verified["unique_content_count"], 1)
            self.assertEqual(restore.returncode, 0, restore.stderr)
            first = output / "codex/archived_sessions/alias-a.jsonl"
            second = output / "codex/archived_sessions/alias-b.jsonl"
            self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_resume_after_public_index_checkpoint_does_not_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            add_stable_jsonl(
                codex_home,
                "archived_sessions/interrupted.jsonl",
                [{"text": "resume me"}],
            )

            def interrupt(phase: str) -> None:
                if phase == "PUBLIC_INDEX_PUBLISHED":
                    raise RuntimeError("simulated interruption")

            with self.assertRaisesRegex(RuntimeError, "simulated interruption"):
                sync_codex_public_raw_incremental(
                    database,
                    "delta-resume",
                    operator_codex_home=codex_home,
                    environ={},
                    checkpoint_hook=interrupt,
                )
            interrupted = json.loads((database / STATE_PATH).read_text(encoding="utf-8"))
            self.assertEqual(interrupted["active_run"]["phase"], "PUBLIC_INDEX_PUBLISHED")

            resumed = sync_codex_public_raw_incremental(
                database,
                "delta-resume",
                operator_codex_home=codex_home,
                environ={},
            )
            final_state = json.loads((database / STATE_PATH).read_text(encoding="utf-8"))

            self.assertEqual(resumed["outcome"], "ARCHIVED_NEW_CONTENT")
            self.assertIs(resumed["resumed"], True)
            self.assertIsNone(final_state["active_run"])
            self.assertEqual(archive_ids(database).count("delta-resume"), 1)
            self.assertEqual(
                len(list((database / "data/public_raw/codex").glob("*delta-resume*.json"))),
                1,
            )

    def test_resume_fails_closed_when_planned_source_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            source = add_stable_jsonl(
                codex_home,
                "archived_sessions/drift.jsonl",
                [{"text": "before"}],
            )

            def interrupt(phase: str) -> None:
                if phase == "PLANNED":
                    raise RuntimeError("planned")

            with self.assertRaises(RuntimeError):
                sync_codex_public_raw_incremental(
                    database,
                    "delta-drift",
                    operator_codex_home=codex_home,
                    environ={},
                    checkpoint_hook=interrupt,
                )
            write_jsonl(source, [{"text": "after"}])
            old_timestamp = time.time() - 600
            os.utime(source, (old_timestamp, old_timestamp))

            with self.assertRaises(CodexSyncStateError) as raised:
                sync_codex_public_raw_incremental(
                    database,
                    "delta-drift",
                    operator_codex_home=codex_home,
                    environ={},
                )
            self.assertEqual(raised.exception.code, "active_run_source_changed")
            self.assertFalse((database / ARCHIVE_ROOT / "delta-drift").exists())

    def test_t2_registration_manifest_remains_valid_append_only_prefix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            add_stable_jsonl(
                codex_home,
                "archived_sessions/prefix.jsonl",
                [{"text": "append ledger"}],
            )
            sync_codex_public_raw_incremental(
                database,
                "delta-prefix",
                operator_codex_home=codex_home,
                environ={},
            )

            verified = verify_codex_public_raw_archive(database, "baseline")

            self.assertIs(verified["raw_ledger_verified"], True)
            self.assertIs(verified["raw_manifest_is_ledger_prefix"], True)
            self.assertGreater(verified["public_raw_file_count"], 1)

    def test_runner_and_parser_are_path_free_and_expose_incremental_mode(self) -> None:
        parsed = parse_args(
            [
                "sync",
                "--source",
                "codex",
                "--raw-archive",
                "--incremental",
                "--archive-id",
                "fixture",
                "--dry-run",
            ]
        )
        self.assertIs(parsed.incremental, True)

        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            args = Namespace(
                database_dir=database,
                archive_id="runner-dry",
                codex_home=codex_home,
                dry_run=True,
            )
            with mock.patch("sys.stdout") as stdout:
                exit_code = run_codex_sync_state(args)
            output = "".join(
                str(call.args[0]) for call in stdout.write.call_args_list if call.args
            )

            self.assertEqual(exit_code, 0)
            self.assertNotIn(temp_dir, output)
            self.assertNotIn("Traceback", output)
            self.assertFalse((database / STATE_PATH).exists())

    def test_missing_public_index_uses_t3_fail_closed_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            add_stable_jsonl(
                codex_home,
                "archived_sessions/missing-index.jsonl",
                [{"text": "registered then removed"}],
            )
            result = sync_codex_public_raw_incremental(
                database,
                "delta-missing-index",
                operator_codex_home=codex_home,
                environ={},
            )
            (database / result["public_index_path"]).unlink()

            with self.assertRaises(CodexSyncStateError) as raised:
                verify_codex_incremental_archive(database, "delta-missing-index")
            self.assertEqual(raised.exception.code, "incremental_public_index_missing")

    def test_verifier_rejects_restore_tamper_and_symlinked_part(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database, codex_home = prepare_baseline(parent)
            sync_codex_public_raw_incremental(
                database,
                "bootstrap-noop",
                operator_codex_home=codex_home,
                environ={},
            )
            add_stable_jsonl(
                codex_home,
                "archived_sessions/verifier-hardening.jsonl",
                [{"text": "verify published helper and part types"}],
            )
            sync_codex_public_raw_incremental(
                database,
                "delta-hardening",
                operator_codex_home=codex_home,
                environ={},
            )
            archive = database / ARCHIVE_ROOT / "delta-hardening"
            restore = archive / "restore.sh"
            restore_bytes = restore.read_bytes()
            restore.write_text("#!/usr/bin/env bash\necho unsafe\n", encoding="utf-8")
            with self.assertRaises(CodexSyncStateError) as raised:
                verify_codex_incremental_archive(database, "delta-hardening")
            self.assertEqual(
                raised.exception.code,
                "incremental_archive_restore_script_mismatch",
            )
            restore.write_bytes(restore_bytes)

            part = next((archive / "parts").iterdir())
            part_copy = parent / "part-copy"
            shutil.copyfile(part, part_copy)
            part.unlink()
            part.symlink_to(part_copy)
            with self.assertRaises(CodexSyncStateError) as raised:
                verify_codex_incremental_archive(database, "delta-hardening")
            self.assertEqual(raised.exception.code, "incremental_archive_part_unsafe")


if __name__ == "__main__":
    unittest.main()
