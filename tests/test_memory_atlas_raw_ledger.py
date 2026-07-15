from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import sys
import tempfile
import unittest
from unittest import mock
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.raw_ledger import (  # noqa: E402
    RAW_LEDGER_CONTRACT_PATH,
    RawLedgerError,
    append_jsonl_immutable,
    guarded_sha256_file,
    inspect_raw_ledger_lock,
    load_raw_ledger_contract,
    raw_ledger_append_lock,
    source_stat_guard,
)
from memory_atlas_cli import raw_ledger as raw_ledger_module  # noqa: E402


def load_manifest_module(name: str):
    path = SCRIPTS / "raw_archive_manifest.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def write_raw(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"text": text}, sort_keys=True) + "\n", encoding="utf-8")


def install_raw_ledger_contract(database: Path) -> None:
    target = database / RAW_LEDGER_CONTRACT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / RAW_LEDGER_CONTRACT_PATH).read_bytes())


class RawLedgerContractTests(unittest.TestCase):
    def test_canonical_contract_is_strict_and_stops_before_split_restore(self) -> None:
        contract = load_raw_ledger_contract()

        self.assertEqual(contract["task_id"], "S06-P2-T1")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S06-P2-T1")
        self.assertEqual(contract["content_hash"]["algorithm"], "sha256")
        self.assertIs(contract["ledger"]["append_only"], True)
        self.assertIs(contract["ledger"]["rewrite_existing_bytes"], False)
        self.assertIs(contract["phase_boundary"]["does_not_split_archives"], True)
        self.assertIs(contract["phase_boundary"]["does_not_restore_archives"], True)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S06-P2-T2")

    def test_contract_drift_fails_closed(self) -> None:
        canonical = json.loads((ROOT / RAW_LEDGER_CONTRACT_PATH).read_text(encoding="utf-8"))
        mutations = {
            "weak hash": lambda value: value["content_hash"].update({"algorithm": "md5"}),
            "ledger rewrite": lambda value: value["ledger"].update({"rewrite_existing_bytes": True}),
            "restore scope": lambda value: value["phase_boundary"].update({"does_not_restore_archives": False}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temp_dir:
                payload = copy.deepcopy(canonical)
                mutate(payload)
                path = Path(temp_dir) / "raw_ledger.json"
                path.write_text(json.dumps(payload), encoding="utf-8")
                with self.assertRaises(RawLedgerError):
                    load_raw_ledger_contract(Path(temp_dir), path)

    def test_source_stat_guard_detects_same_size_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.jsonl"
            source.write_bytes(b"aaaa\n")
            before = source.stat()

            with self.assertRaises(RawLedgerError):
                with source_stat_guard(source):
                    source.write_bytes(b"bbbb\n")
                    os.utime(
                        source,
                        ns=(before.st_atime_ns, before.st_mtime_ns + 1_000_000),
                    )

    def test_source_symlink_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "source.jsonl"
            source.write_text("{}\n", encoding="utf-8")
            link = root / "source-link.jsonl"
            link.symlink_to(source)

            with self.assertRaises(RawLedgerError):
                guarded_sha256_file(link)

    def test_guarded_sha256_preserves_source_bytes_size_and_mtime(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "source.jsonl"
            source_bytes = b"immutable source\n"
            source.write_bytes(source_bytes)
            before = source.stat()

            result = guarded_sha256_file(source)
            after = source.stat()

        self.assertEqual(result["sha256"], hashlib.sha256(source_bytes).hexdigest())
        self.assertEqual(result["size_bytes"], len(source_bytes))
        self.assertTrue(result["source_stat_verified"])
        self.assertEqual(after.st_size, before.st_size)
        self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)

    def test_directory_inventory_guard_rejects_added_source_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "conversations.json").write_text("[]\n", encoding="utf-8")
            with self.assertRaises(RawLedgerError):
                with source_stat_guard(source, directory_globs=("**/conversations*.json",)):
                    (source / "conversations-new.json").write_text("[]\n", encoding="utf-8")

    def test_chatgpt_adapter_source_mutation_fails_before_any_database_write(self) -> None:
        module_path = SCRIPTS / "sync_chatgpt_memory_data.py"
        spec = importlib.util.spec_from_file_location("s06_p2_t1_chatgpt_mutation", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "conversations.json"
            source.write_bytes(b"aaaa\n")
            database = root / "database"

            def mutate_source(_path: Path) -> list[dict[str, object]]:
                source.write_bytes(b"bbbb\n")
                return []

            with mock.patch.object(module, "load_official_export", side_effect=mutate_source):
                with self.assertRaises(RawLedgerError):
                    module.sync_official_export(database, source, dry_run=True)
            self.assertFalse(database.exists())

    def test_codex_summary_source_mutation_fails_before_any_database_write(self) -> None:
        module_path = SCRIPTS / "sync_codex_memory_data.py"
        spec = importlib.util.spec_from_file_location("s06_p2_t1_codex_mutation", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / ".codex"
            source = codex_home / "sessions/2026/07/15/session.jsonl"
            source.parent.mkdir(parents=True)
            source.write_bytes(b"aaaa\n")
            database = root / "database"

            def mutate_source(*_args: object) -> None:
                source.write_bytes(b"bbbb\n")
                return None

            with mock.patch.object(module, "parse_session_file", side_effect=mutate_source):
                with self.assertRaises(RawLedgerError):
                    module.sync_codex_data(
                        database,
                        codex_home,
                        build_atlas=False,
                        commit=False,
                        push=False,
                        force_full_scan=True,
                        dry_run=True,
                    )
            self.assertFalse(database.exists())

    def test_codex_parent_directory_symlink_is_rejected(self) -> None:
        module_path = SCRIPTS / "sync_codex_memory_data.py"
        spec = importlib.util.spec_from_file_location("s06_p2_t1_codex_symlink", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            codex_home = root / ".codex"
            outside = root / "outside"
            source = outside / "2026/07/15/session.jsonl"
            source.parent.mkdir(parents=True)
            source.write_text("{}\n", encoding="utf-8")
            codex_home.mkdir()
            (codex_home / "sessions").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(RawLedgerError):
                module.sync_codex_data(
                    root / "database",
                    codex_home,
                    build_atlas=False,
                    commit=False,
                    push=False,
                    force_full_scan=True,
                    dry_run=True,
                )

    def test_chatgpt_mutation_after_parse_fails_before_raw_commit(self) -> None:
        module_path = SCRIPTS / "sync_chatgpt_memory_data.py"
        spec = importlib.util.spec_from_file_location("s06_p2_t1_chatgpt_post_parse", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "conversations.json"
            source.write_text("[]\n", encoding="utf-8")
            database = root / "database"
            original_prepare = module.prepare_public_conversation
            conversation = {
                "id": "fixture",
                "title": "fixture",
                "create_time": 1,
                "update_time": 1,
                "mapping": {},
            }

            def mutate_after_parse(*args: object, **kwargs: object):
                source.write_bytes(b"[ ]")
                return original_prepare(*args, **kwargs)

            with mock.patch.object(module, "load_official_export", return_value=[conversation]):
                with mock.patch.object(module, "prepare_public_conversation", side_effect=mutate_after_parse):
                    with self.assertRaises(RawLedgerError):
                        module.sync_official_export(database, source, dry_run=False)
            self.assertFalse((database / "data/public_raw").exists())


class RawLedgerBehaviorTests(unittest.TestCase):
    def test_target_database_contract_is_required(self) -> None:
        module = load_manifest_module("s06_p2_t1_target_contract")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            write_raw(database / "data/public_raw/chatgpt/first.json", "first")

            with self.assertRaises(RawLedgerError):
                module.record_raw_ledger(database, "2026-07-15T00:00:00Z")

            self.assertFalse(module.hash_ledger_path(database).exists())

    def test_preflight_rejects_existing_raw_without_ledger(self) -> None:
        module = load_manifest_module("s06_p2_t1_missing_ledger")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            install_raw_ledger_contract(database)
            write_raw(database / "data/public_raw/chatgpt/first.json", "first")

            with self.assertRaises(RawLedgerError):
                module.preflight_raw_ledger(database)

            self.assertFalse(module.hash_ledger_path(database).exists())

    def test_ledger_appends_new_rows_and_idempotent_replay_changes_no_byte_or_stat(self) -> None:
        module = load_manifest_module("s06_p2_t1_append_only")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            install_raw_ledger_contract(database)
            first_raw = database / "data/public_raw/chatgpt/first.json"
            write_raw(first_raw, "first")
            raw_before = first_raw.read_bytes()
            raw_stat_before = first_raw.stat()

            first = module.record_raw_ledger(database, "2026-07-15T00:00:00Z")
            ledger = database / first["hash_ledger_path"]
            first_bytes = ledger.read_bytes()
            first_stat = ledger.stat()

            replay = module.record_raw_ledger(database, "2026-07-15T00:01:00Z")
            replay_stat = ledger.stat()
            self.assertTrue(replay["idempotent"])
            self.assertEqual(replay["ledger_appended_count"], 0)
            self.assertEqual(ledger.read_bytes(), first_bytes)
            self.assertEqual(replay_stat.st_ino, first_stat.st_ino)
            self.assertEqual(replay_stat.st_mtime_ns, first_stat.st_mtime_ns)

            write_raw(database / "data/public_raw/codex/second.json", "second")
            extended = module.record_raw_ledger(database, "2026-07-15T00:02:00Z")
            extended_bytes = ledger.read_bytes()
            extended_stat = ledger.stat()

            self.assertEqual(first["ledger_appended_count"], 1)
            self.assertEqual(first["source_stat_verified_count"], 1)
            self.assertEqual(extended["ledger_appended_count"], 1)
            self.assertEqual(extended["ledger_entry_count"], 2)
            self.assertTrue(extended_bytes.startswith(first_bytes))
            self.assertEqual(extended_stat.st_ino, first_stat.st_ino)
            self.assertEqual(first_raw.read_bytes(), raw_before)
            self.assertEqual(first_raw.stat().st_size, raw_stat_before.st_size)
            self.assertEqual(first_raw.stat().st_mtime_ns, raw_stat_before.st_mtime_ns)

    def test_drift_delete_and_unledgered_file_fail_without_changing_ledger(self) -> None:
        module = load_manifest_module("s06_p2_t1_fail_closed")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            install_raw_ledger_contract(database)
            raw = database / "data/public_raw/chatgpt/first.json"
            write_raw(raw, "first")
            result = module.record_raw_ledger(database, "2026-07-15T00:00:00Z")
            ledger = database / result["hash_ledger_path"]
            ledger_bytes = ledger.read_bytes()

            write_raw(raw, "drift")
            with self.assertRaises(module.ManifestConflict):
                module.record_raw_ledger(database, "2026-07-15T00:01:00Z")
            self.assertEqual(ledger.read_bytes(), ledger_bytes)

            raw.unlink()
            with self.assertRaises(module.ManifestConflict):
                module.record_raw_ledger(database, "2026-07-15T00:02:00Z")
            self.assertEqual(ledger.read_bytes(), ledger_bytes)

            write_raw(raw, "first")
            write_raw(database / "data/public_raw/codex/unledgered.json", "new")
            audit = module.audit_raw_append_only(database)

        self.assertEqual(audit["status"], "FAIL")
        self.assertEqual(audit["unledgered_raw_file_count"], 1)
        self.assertEqual(audit["source_stat_verified_count"], 2)

    def test_existing_append_lock_fails_closed_without_changing_ledger(self) -> None:
        module = load_manifest_module("s06_p2_t1_lock")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            install_raw_ledger_contract(database)
            write_raw(database / "data/public_raw/chatgpt/first.json", "first")
            result = module.record_raw_ledger(database, "2026-07-15T00:00:00Z")
            ledger = database / result["hash_ledger_path"]
            before = ledger.read_bytes()
            lock_path = ledger.with_name(f"{ledger.name}.lock")
            lock_path.write_text("pid=fixture\n", encoding="utf-8")

            with self.assertRaises(RawLedgerError):
                module.record_raw_ledger(database, "2026-07-15T00:01:00Z")

            self.assertEqual(ledger.read_bytes(), before)

    def test_lock_metadata_supports_active_pid_diagnostics_without_auto_removal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "raw_hash_ledger.jsonl"
            ledger.write_bytes(b"")

            with raw_ledger_append_lock(ledger):
                diagnostics = inspect_raw_ledger_lock(ledger)
                self.assertEqual(diagnostics["state"], "active_pid")
                self.assertTrue(diagnostics["manual_verification_required"])
                self.assertEqual(diagnostics["pid"], os.getpid())

            self.assertFalse(ledger.with_name(f"{ledger.name}.lock").exists())

    def test_append_fsync_failure_is_wrapped_as_raw_ledger_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            ledger = Path(temp_dir) / "raw_hash_ledger.jsonl"
            ledger.write_bytes(b"")
            row = {
                "source_id": "chatgpt",
                "relative_path": "chatgpt/first.json",
                "sha256": "a" * 64,
                "imported_at": "2026-07-15T00:00:00Z",
                "size_bytes": 1,
            }
            call_count = 0
            real_fsync = raw_ledger_module.os.fsync

            def fail_append_fsync(fd: int) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 2:
                    raise OSError("fixture fsync failure")
                real_fsync(fd)

            with mock.patch.object(raw_ledger_module.os, "fsync", side_effect=fail_append_fsync):
                with self.assertRaises(RawLedgerError):
                    append_jsonl_immutable(ledger, [row])

            self.assertIn(b'"relative_path": "chatgpt/first.json"', ledger.read_bytes())

    def test_adapter_reports_post_write_truth_when_ledger_fsync_fails(self) -> None:
        module_path = SCRIPTS / "sync_chatgpt_memory_data.py"
        spec = importlib.util.spec_from_file_location("s06_p2_t1_chatgpt_fsync", module_path)
        module = importlib.util.module_from_spec(spec)
        assert spec and spec.loader
        sys.modules[spec.name] = module
        spec.loader.exec_module(module)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database"
            install_raw_ledger_contract(database)
            ledger = database / "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
            ledger.parent.mkdir(parents=True)
            ledger.write_bytes(b"")
            source = root / "conversations.json"
            source.write_text("[]\n", encoding="utf-8")
            conversation = {
                "id": "fixture",
                "title": "fixture",
                "create_time": 1,
                "update_time": 1,
                "mapping": {},
            }
            call_count = 0
            real_fsync = raw_ledger_module.os.fsync

            def fail_ledger_append_fsync(fd: int) -> None:
                nonlocal call_count
                call_count += 1
                if call_count == 3:
                    raise OSError("fixture ledger fsync failure")
                real_fsync(fd)

            with mock.patch.object(module, "load_official_export", return_value=[conversation]):
                with mock.patch.object(raw_ledger_module.os, "fsync", side_effect=fail_ledger_append_fsync):
                    with self.assertRaises(module.RawLedgerPostWriteError):
                        module.sync_official_export(database, source, dry_run=False)

            self.assertTrue((database / "data/public_raw/chatgpt").is_dir())
            self.assertFalse((database / module.PROCESSED_MANIFEST).exists())

    def test_audit_rejects_non_hash_immutable_ledger_drift(self) -> None:
        module = load_manifest_module("s06_p2_t1_immutable_drift")
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir)
            install_raw_ledger_contract(database)
            write_raw(database / "data/public_raw/chatgpt/first.json", "first")
            result = module.record_raw_ledger(database, "2026-07-15T00:00:00Z")
            ledger = database / result["hash_ledger_path"]
            row = json.loads(ledger.read_text(encoding="utf-8"))
            row["size_bytes"] += 1
            ledger.write_text(json.dumps(row, sort_keys=True) + "\n", encoding="utf-8")

            audit = module.audit_raw_append_only(database)

        self.assertEqual(audit["status"], "FAIL")
        self.assertEqual(audit["immutable_drift_count"], 1)
        self.assertEqual(audit["hash_drift_count"], 0)


if __name__ == "__main__":
    unittest.main()
