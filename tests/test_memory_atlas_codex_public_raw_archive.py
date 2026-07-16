from __future__ import annotations

import copy
import hashlib
import io
import json
import os
import shutil
import sqlite3
import subprocess
import sys
import tarfile
import tempfile
import time
import unittest
import uuid
from argparse import Namespace
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.codex_public_raw_archive import (  # noqa: E402
    ARCHIVE_ROOT,
    CONTRACT_PATH,
    EXPECTED_PHASE_BOUNDARY,
    PUBLIC_INDEX_ROOT,
    SCHEMA_VERSION,
    CodexPublicRawArchiveError,
    build_codex_public_raw_archive,
    load_codex_public_raw_archive_contract,
    run_codex_public_raw_archive,
    validate_codex_public_raw_archive_contract,
    verify_codex_public_raw_archive,
)


SYNTHETIC_VALUE = str().join(("s", "k", "-", "ABCDEFGHIJKLMNOPQRSTUVWX"))
LOCAL_PATH = "/Users/example/private/project/file.txt"


def write_jsonl(path: Path, rows: list[object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n"
            for row in rows
        ),
        encoding="utf-8",
    )


def make_codex_fixture(parent: Path) -> Path:
    root = parent / "codex-home"
    root.mkdir()
    write_jsonl(root / "session_index.jsonl", [{"id": "session-a", "name": "Index"}])
    active_session = root / "sessions/2026/active.jsonl"
    write_jsonl(
        active_session,
        [
            {
                "type": "message",
                "payload": {
                    "text": (
                        f"ordinary transcript key={SYNTHETIC_VALUE} path={LOCAL_PATH}"
                        "\nitems:\n- preserve this list"
                    ),
                    "password": "StrongPassword123",
                },
            }
        ],
    )
    old_timestamp = time.time() - 600
    os.utime(active_session, (old_timestamp, old_timestamp))
    write_jsonl(
        root / "archived_sessions/archived.jsonl",
        [{"text": "ordinary contact owner@example.com +61 400 000 000"}],
    )
    write_jsonl(root / "history.jsonl", [{"session_id": "session-a", "text": "history"}])
    write_jsonl(root / "log/client.jsonl", [{"level": "INFO", "message": "client log"}])

    database = root / "logs_2.sqlite"
    connection = sqlite3.connect(database)
    connection.executescript(
        """
        CREATE TABLE logs (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          level TEXT NOT NULL,
          feedback_log_body TEXT,
          file TEXT
        );
        CREATE INDEX idx_logs_level ON logs(level);
        """
    )
    connection.execute(
        "INSERT INTO logs(level, feedback_log_body, file) VALUES (?, ?, ?)",
        ("INFO", f"token={SYNTHETIC_VALUE}", LOCAL_PATH),
    )
    connection.commit()
    connection.close()

    (root / "auth.json").write_text(SYNTHETIC_VALUE, encoding="utf-8")
    (root / "config.toml").write_text(
        f"api_key={SYNTHETIC_VALUE}\n",
        encoding="utf-8",
    )
    (root / "private_keys").mkdir()
    (root / "private_keys/key.pem").write_text("PRIVATE", encoding="utf-8")
    return root


def make_database_fixture(parent: Path) -> Path:
    database = parent / "OpenAIDatabase"
    (database / "config").mkdir(parents=True)
    shutil.copytree(ROOT / "config/data_sources", database / "config/data_sources")
    scripts = database / "scripts"
    scripts.mkdir()
    for name in (
        "sync_chatgpt_memory_data.py",
        "sync_codex_memory_data.py",
        "sync_future_agent_data.py",
    ):
        (scripts / name).write_text("# fixture\n", encoding="utf-8")
    raw_archive_entrypoint = scripts / "memory_atlas_cli/codex_public_raw_archive.py"
    raw_archive_entrypoint.parent.mkdir()
    raw_archive_entrypoint.write_text("# fixture\n", encoding="utf-8")
    (raw_archive_entrypoint.parent / "chatgpt_export_archive.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (raw_archive_entrypoint.parent / "codex_sync_state.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (raw_archive_entrypoint.parent / "codex_legacy_summary.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (raw_archive_entrypoint.parent / "codex_push_main.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (raw_archive_entrypoint.parent / "codex_scheduler.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    (scripts / "build_memory_atlas_codex_derived.py").write_text(
        "# fixture\n",
        encoding="utf-8",
    )
    return database


def tree_evidence(root: Path) -> dict[str, tuple[int, int, str]]:
    evidence: dict[str, tuple[int, int, str]] = {}
    for path in sorted(candidate for candidate in root.rglob("*") if candidate.is_file()):
        metadata = path.stat()
        evidence[path.relative_to(root).as_posix()] = (
            metadata.st_size,
            metadata.st_mtime_ns,
            hashlib.sha256(path.read_bytes()).hexdigest(),
        )
    return evidence


def extract_archive(database: Path, archive_id: str, output: Path) -> subprocess.CompletedProcess[str]:
    archive = database / ARCHIVE_ROOT / archive_id
    return subprocess.run(
        [str(archive / "restore.sh"), str(output)],
        cwd=archive,
        text=True,
        capture_output=True,
        check=False,
    )


class CodexPublicRawArchiveTests(unittest.TestCase):
    def test_contract_freezes_t2_without_cursor_dedupe_resume_or_derived(self) -> None:
        contract = load_codex_public_raw_archive_contract(ROOT)

        self.assertEqual(contract["schema_version"], SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], "S07-P1-T2")
        self.assertEqual(contract["archive"]["root"], ARCHIVE_ROOT.as_posix())
        self.assertEqual(
            contract["archive"]["public_index_root"],
            PUBLIC_INDEX_ROOT.as_posix(),
        )
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        self.assertIs(contract["phase_boundary"]["does_not_write_cursor"], True)
        self.assertIs(contract["phase_boundary"]["does_not_deduplicate_by_content"], True)
        self.assertIs(contract["phase_boundary"]["does_not_resume_interrupted_runs"], True)
        self.assertEqual(
            contract["inflight_sources"]["recent_mtime_grace_seconds"], 300
        )
        self.assertIs(
            contract["inflight_sources"]["writes_cursor_or_resume_state"], False
        )
        registry = json.loads((ROOT / "config/data_sources/source_registry.json").read_text())
        codex = next(
            source for source in registry["sync_sources"] if source["source_id"] == "codex"
        )
        self.assertEqual(
            codex["parser"]["raw_archive_contract_ref"], CONTRACT_PATH.as_posix()
        )
        self.assertEqual(
            codex["parser"]["complete_archive_root"], ARCHIVE_ROOT.as_posix()
        )

        mutated = copy.deepcopy(contract)
        mutated["phase_boundary"]["does_not_write_cursor"] = False
        with self.assertRaises(CodexPublicRawArchiveError):
            validate_codex_public_raw_archive_contract(mutated)

    def test_archive_is_recoverable_sanitized_complete_and_source_immutable(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            before = tree_evidence(codex_home)

            result = build_codex_public_raw_archive(
                database,
                "fixture-archive",
                operator_codex_home=codex_home,
                environ={},
            )
            after = tree_evidence(codex_home)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(before, after)
            self.assertEqual(result["source_before_sha256"], result["source_after_sha256"])
            self.assertIs(result["source_hash_stat_equal"], True)
            self.assertIs(result["source_mutation"], False)
            self.assertEqual(result["source_file_count"], 6)
            self.assertGreater(result["redaction_counts"].get("api_keys", 0), 0)
            self.assertGreater(result["redaction_counts"].get("local_absolute_path", 0), 0)
            self.assertEqual(result["raw_ledger"]["ledger_appended_count"], 1)

            restored = parent / "restored"
            restore = extract_archive(database, "fixture-archive", restored)
            self.assertEqual(restore.returncode, 0, restore.stderr)
            restored_root = restored / "codex"
            self.assertTrue((restored_root / "sessions/2026/active.jsonl").is_file())
            self.assertTrue((restored_root / "logs_2.sqlite").is_file())
            self.assertFalse((restored_root / "auth.json").exists())
            self.assertFalse((restored_root / "config.toml").exists())
            self.assertFalse((restored_root / "private_keys").exists())

            restored_text = "".join(
                path.read_text(encoding="utf-8")
                for path in restored_root.rglob("*.jsonl")
            )
            self.assertNotIn(SYNTHETIC_VALUE, restored_text)
            self.assertNotIn(LOCAL_PATH, restored_text)
            self.assertIn("[REDACTED_CREDENTIAL]", restored_text)
            self.assertIn("[REDACTED_LOCAL_PATH]", restored_text)
            self.assertIn("owner@example.com", restored_text)
            self.assertIn("preserve this list", restored_text)

            connection = sqlite3.connect(restored_root / "logs_2.sqlite")
            row = connection.execute(
                "SELECT feedback_log_body, file FROM logs ORDER BY id"
            ).fetchone()
            quick_check = connection.execute("PRAGMA quick_check").fetchone()
            connection.close()
            self.assertEqual(quick_check, ("ok",))
            self.assertEqual(row, ("token=[REDACTED_CREDENTIAL]", "[REDACTED_LOCAL_PATH]"))

            source_manifest = restored_root / "_memory_atlas/source_manifest.json"
            source_payload = json.loads(source_manifest.read_text(encoding="utf-8"))
            self.assertEqual(source_payload["source_proof"]["file_count"], 6)
            self.assertIs(source_payload["source_proof"]["hash_stat_equal"], True)
            self.assertEqual(len(source_payload["files"]), 6)

    def test_same_archive_id_fails_closed_without_content_dedupe_or_rewrite(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            build_codex_public_raw_archive(
                database,
                "append-only",
                operator_codex_home=codex_home,
                environ={},
            )
            archive = database / ARCHIVE_ROOT / "append-only"
            before = tree_evidence(archive)

            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                build_codex_public_raw_archive(
                    database,
                    "append-only",
                    operator_codex_home=codex_home,
                    environ={},
                )

            self.assertEqual(raised.exception.code, "archive_id_exists")
            self.assertEqual(before, tree_evidence(archive))

    def test_recent_active_session_is_deferred_and_recorded_without_hash_claim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            recent = codex_home / "sessions/recent-inflight.jsonl"
            write_jsonl(recent, [{"text": "still running"}])

            result = build_codex_public_raw_archive(
                database,
                "deferred-inflight",
                operator_codex_home=codex_home,
                environ={},
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["discovered_file_count"], 7)
            self.assertEqual(result["source_file_count"], 6)
            self.assertEqual(result["deferred_inflight_file_count"], 1)
            restored = parent / "deferred-restored"
            self.assertEqual(
                extract_archive(database, "deferred-inflight", restored).returncode,
                0,
            )
            self.assertFalse((restored / "codex/sessions/recent-inflight.jsonl").exists())
            source_manifest = json.loads(
                (restored / "codex/_memory_atlas/source_manifest.json").read_text(
                    encoding="utf-8"
                )
            )
            deferred = source_manifest["deferred_inflight_sources"]
            self.assertEqual(len(deferred), 1)
            self.assertEqual(
                deferred[0]["relative_path"], "sessions/recent-inflight.jsonl"
            )
            self.assertIs(deferred[0]["hash_stat_claim"], False)

    def test_quiescence_retry_reclassifies_new_recent_active_session(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            from memory_atlas_cli import codex_public_raw_archive as module

            discovery, credentials, discovered = module._resolve_inventory(
                database,
                operator_codex_home=codex_home,
                environ={},
                home=None,
            )
            stable, deferred = module._partition_inflight_sources(discovered)
            original_capture = module._capture_proofs
            call_count = 0

            def drift_once(current):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    write_jsonl(
                        codex_home / "sessions/new-inflight.jsonl",
                        [{"text": "new active session"}],
                    )
                    raise CodexPublicRawArchiveError("source_stat_changed")
                return original_capture(current)

            with (
                mock.patch.object(module, "_capture_proofs", side_effect=drift_once),
                mock.patch.object(module.time, "sleep"),
            ):
                selected, proofs, current_deferred = module._capture_quiescent_proofs(
                    stable,
                    discovery,
                    credentials,
                    deferred,
                )

            self.assertEqual(len(proofs), len(selected.files))
            self.assertNotIn(
                "sessions/new-inflight.jsonl",
                {item.relative_path for item in selected.files},
            )
            self.assertIn(
                "sessions/new-inflight.jsonl",
                {str(item["relative_path"]) for item in current_deferred},
            )

    def test_source_change_aborts_before_archive_or_public_index_publish(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            from memory_atlas_cli import codex_public_raw_archive as module

            original = module._sanitize_jsonl
            mutated = False

            def mutate_after_read(item, expected_stat, output):
                nonlocal mutated
                result = original(item, expected_stat, output)
                if not mutated:
                    item.path.write_bytes(item.path.read_bytes() + b"{}\n")
                    mutated = True
                return result

            with (
                mock.patch.object(module, "_sanitize_jsonl", side_effect=mutate_after_read),
                self.assertRaises(CodexPublicRawArchiveError),
            ):
                build_codex_public_raw_archive(
                    database,
                    "source-change",
                    operator_codex_home=codex_home,
                    environ={},
                )

            self.assertFalse((database / ARCHIVE_ROOT / "source-change").exists())
            self.assertFalse(list((database / PUBLIC_INDEX_ROOT).glob("*source-change*")))

    def test_part_tamper_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            result = build_codex_public_raw_archive(
                database,
                "tamper",
                operator_codex_home=codex_home,
                environ={},
            )
            self.assertEqual(
                verify_codex_public_raw_archive(database, "tamper")["status"],
                "PASS",
            )
            archive = database / ARCHIVE_ROOT / "tamper"
            manifest = json.loads((archive / "manifest.json").read_text(encoding="utf-8"))
            part = archive / manifest["parts"][0]["filename"]
            with part.open("r+b") as handle:
                first = handle.read(1)
                handle.seek(0)
                handle.write(bytes([first[0] ^ 0xFF]))

            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                verify_codex_public_raw_archive(database, "tamper")
            self.assertEqual(raised.exception.code, "archive_part_hash_or_size_mismatch")
            self.assertGreater(result["package_bytes"], 0)

    def test_archive_audit_requires_public_index_and_raw_ledger_registration(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            result = build_codex_public_raw_archive(
                database,
                "registration",
                operator_codex_home=codex_home,
                environ={},
            )

            verified = verify_codex_public_raw_archive(database, "registration")
            self.assertIs(verified["raw_ledger_verified"], True)
            self.assertEqual(verified["public_index_path"], result["public_index_path"])
            public_index = database / result["public_index_path"]
            public_index_bytes = public_index.read_bytes()
            public_index.unlink()

            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                verify_codex_public_raw_archive(database, "registration")
            self.assertEqual(raised.exception.code, "archive_public_index_missing")

            public_index.write_bytes(public_index_bytes)
            raw_manifest = database / verified["raw_manifest_path"]
            raw_manifest_bytes = raw_manifest.read_bytes()
            raw_manifest.unlink()
            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                verify_codex_public_raw_archive(database, "registration")
            self.assertEqual(raised.exception.code, "archive_raw_manifest_missing")

            raw_manifest.write_bytes(raw_manifest_bytes)
            ledger = (
                database
                / "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
            )
            ledger.write_text("", encoding="utf-8")
            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                verify_codex_public_raw_archive(database, "registration")
            self.assertEqual(
                raised.exception.code,
                "archive_raw_manifest_ledger_mismatch",
            )

    def test_archive_audit_rejects_manifest_authorization_drift(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            build_codex_public_raw_archive(
                database,
                "manifest-drift",
                operator_codex_home=codex_home,
                environ={},
            )
            manifest_path = database / ARCHIVE_ROOT / "manifest-drift/manifest.json"
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["authorization"]["basis"] = "unreviewed"
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )

            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                verify_codex_public_raw_archive(
                    database,
                    "manifest-drift",
                    require_public_registration=False,
                )
            self.assertEqual(raised.exception.code, "archive_manifest_identity_mismatch")

    def test_restore_rejects_unsafe_tar_member_without_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            archive = parent / "unsafe"
            parts = archive / "parts"
            parts.mkdir(parents=True)
            package = io.BytesIO()
            with tarfile.open(fileobj=package, mode="w:gz") as handle:
                for name, payload in (
                    ("codex/_memory_atlas/source_manifest.json", b"{}\n"),
                    ("../escape.txt", b"unsafe\n"),
                ):
                    info = tarfile.TarInfo(name)
                    info.size = len(payload)
                    handle.addfile(info, io.BytesIO(payload))
            package_bytes = package.getvalue()
            package_sha256 = hashlib.sha256(package_bytes).hexdigest()
            (parts / "unsafe.tar.gz.part-000000").write_bytes(package_bytes)
            from memory_atlas_cli import codex_public_raw_archive as module

            script = archive / "restore.sh"
            script.write_bytes(module._restore_script("unsafe", package_sha256, 2))
            script.chmod(0o700)
            output = parent / "restored"
            result = subprocess.run(
                [str(script), str(output)],
                cwd=archive,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(output.exists())
            self.assertFalse((parent / "escape.txt").exists())

    def test_non_utf8_jsonl_fails_before_publication(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            invalid = codex_home / "sessions/non-utf8.jsonl"
            invalid.write_bytes(b"\xff\xfe\n")
            old_timestamp = time.time() - 600
            os.utime(invalid, (old_timestamp, old_timestamp))

            with self.assertRaises(CodexPublicRawArchiveError) as raised:
                build_codex_public_raw_archive(
                    database,
                    "non-utf8",
                    operator_codex_home=codex_home,
                    environ={},
                )

            self.assertEqual(raised.exception.code, "eligible_jsonl_not_utf8")
            self.assertFalse((database / ARCHIVE_ROOT / "non-utf8").exists())

    def test_dry_run_reads_metadata_only_and_writes_nothing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            codex_home = make_codex_fixture(parent)
            before = tree_evidence(parent)

            result = build_codex_public_raw_archive(
                database,
                "dry-run",
                operator_codex_home=codex_home,
                environ={},
                dry_run=True,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertIs(result["dry_run"], True)
            self.assertIs(result["source_content_read"], False)
            self.assertIs(result["writes_files"], False)
            self.assertEqual(before, tree_evidence(parent))

    def test_runner_error_is_path_free_and_does_not_echo_source_body(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            database = make_database_fixture(parent)
            missing = parent / "missing-codex"
            args = Namespace(
                database_dir=database,
                archive_id="runner-error",
                codex_home=missing,
                dry_run=False,
            )
            with mock.patch("sys.stdout") as stdout:
                exit_code = run_codex_public_raw_archive(args)
            output = "".join(
                str(call.args[0]) for call in stdout.write.call_args_list if call.args
            )

            self.assertEqual(exit_code, 2)
            self.assertNotIn(temp_dir, output)
            self.assertNotIn(SYNTHETIC_VALUE, output)
            self.assertNotIn("Traceback", output)

    def test_atlasctl_raw_archive_dry_run_is_wired_and_path_free(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            parent = Path(temp_dir)
            codex_home = make_codex_fixture(parent)
            archive_id = f"cli-dry-{uuid.uuid4().hex[:12]}"
            before = tree_evidence(codex_home)
            result = subprocess.run(
                [
                    sys.executable,
                    str(SCRIPTS / "atlasctl.py"),
                    "sync",
                    "--source",
                    "codex",
                    "--raw-archive",
                    "--archive-id",
                    archive_id,
                    "--codex-home",
                    str(codex_home),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(payload["status"], "PASS")
            self.assertIs(payload["dry_run"], True)
            self.assertIs(payload["writes_files"], False)
            self.assertEqual(before, tree_evidence(codex_home))
            self.assertNotIn(temp_dir, result.stdout + result.stderr)
            self.assertNotIn(SYNTHETIC_VALUE, result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
