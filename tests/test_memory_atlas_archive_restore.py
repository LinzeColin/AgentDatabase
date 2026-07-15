from __future__ import annotations

import hashlib
import io
import json
import os
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import archive_restore as restore  # noqa: E402
from memory_atlas_cli.archive_chunking import (  # noqa: E402
    CONTRACT_PATH as CHUNK_CONTRACT_PATH,
    MAX_PART_BYTES,
    chunk_archive_package,
)
from memory_atlas_cli.raw_ledger import SourceStat  # noqa: E402
import raw_archive_manifest as raw_archive_manifest_cli  # noqa: E402


def install_contracts(database: Path) -> None:
    for relative in (CHUNK_CONTRACT_PATH, restore.CONTRACT_PATH):
        target = database / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / relative).read_bytes())


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> SourceStat:
    return SourceStat.from_os_stat(path.stat(follow_symlinks=False))


def archive_identity(archive: Path) -> dict[str, SourceStat]:
    return {
        path.relative_to(archive).as_posix(): file_identity(path)
        for path in sorted(archive.rglob("*"))
    }


def write_large_package(path: Path) -> None:
    block = bytes(range(256)) * 4096
    remaining = MAX_PART_BYTES + 123
    with path.open("wb") as handle:
        while remaining:
            payload = block[: min(len(block), remaining)]
            handle.write(payload)
            remaining -= len(payload)


def legacy_manifest(
    database: Path,
    source_id: str,
    archive_id: str,
    schema_version: str,
    payload: bytes = b"legacy archive fixture\n",
) -> tuple[Path, dict]:
    archive = database / "data/raw_archives" / source_id / archive_id
    parts = archive / "parts"
    parts.mkdir(parents=True)
    suffix = "zip" if schema_version == restore.CHATGPT_LEGACY_SCHEMA else "bundle"
    package_name = f"fixture.{suffix}"
    part_name = f"parts/fixture.{suffix}.part-000"
    (archive / part_name).write_bytes(payload)
    (archive / "README.md").write_text("# Fixture\n", encoding="utf-8")
    (archive / "restore.sh").write_text("#!/bin/sh\nexit 99\n", encoding="utf-8")
    package = {
        "filename": package_name,
        "byte_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }
    part_rows = [
        {
            "index": 0,
            "filename": part_name,
            "byte_size": len(payload),
            "sha256": hashlib.sha256(payload).hexdigest(),
        }
    ]
    archive_path = (Path(database.name) / "data/raw_archives" / source_id / archive_id).as_posix()
    if schema_version == restore.CHATGPT_LEGACY_SCHEMA:
        manifest = {
            "schema_version": schema_version,
            "archive_id": "legacy-chatgpt-fixture",
            "source": "ChatGPT official data export",
            "visibility": "public_github_repository",
            "repository": "fixture/repository",
            "path": archive_path,
            "recorded_at_utc": "2026-07-08T04:55:00Z",
            "user_confirmation": {
                "confirmed_public_raw_upload": True,
                "selected_option": "2",
                "note": "fixture",
            },
            "original_file": {
                **package,
                "local_source_path_at_upload_time": "/historical/source/fixture.zip",
            },
            "split": {
                "method": "split -b 90m -a 3 -d",
                "part_prefix": "parts/fixture.zip.part-",
                "part_count": 1,
                "max_part_bytes": restore.LEGACY_PART_BYTES,
                "restore_command": "touch must-not-run",
            },
            "parts": part_rows,
        }
    else:
        manifest = {
            "archive_id": "legacy-branch-fixture",
            "branch_count": 0,
            "branches": [],
            "bundle": {**package, "verify_command": "touch must-not-run"},
            "created_at_utc": "2026-07-08T09:12:57Z",
            "delete_remote_branches_after_archive": True,
            "main_ref_at_archive_time": "0" * 40,
            "parts": part_rows,
            "path": archive_path,
            "purpose": "fixture",
            "repository": "fixture/repository",
            "schema_version": schema_version,
            "split": {
                "max_part_bytes": restore.LEGACY_PART_BYTES,
                "method": "split -b 90m -a 3 -d",
                "part_count": 1,
                "restore_command": "touch must-not-run",
            },
        }
    (archive / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return archive, manifest


class MemoryAtlasArchiveRestoreTests(unittest.TestCase):
    def test_contract_is_strict_and_closes_t3_boundary(self) -> None:
        contract = restore.load_archive_restore_contract(ROOT)

        self.assertEqual(contract["task_id"], "S06-P2-T3")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S06-P2-T3")
        self.assertEqual(
            contract["supported_manifest_schemas"]["legacy_read_only"],
            [restore.CHATGPT_LEGACY_SCHEMA, restore.BRANCH_LEGACY_SCHEMA],
        )
        self.assertIs(contract["verification"]["manifest_commands_are_metadata_only"], True)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S06-P3-T1")

        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "archive_restore.json"
            payload = json.loads((ROOT / restore.CONTRACT_PATH).read_text(encoding="utf-8"))
            payload["restore"]["existing_output_policy"] = "overwrite"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(restore.ArchiveRestoreError):
                restore.load_archive_restore_contract(Path(temp_dir), path)

    def test_real_45_mib_chunk_restore_round_trip_is_exact_and_idempotent(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            package = root / "fixture.bin"
            write_large_package(package)
            package_before = file_identity(package)
            package_sha256 = sha256_file(package)

            chunked = chunk_archive_package(database, package, "fixture-source", "roundtrip")
            archive = database / chunked["archive_path"]
            archive_before = archive_identity(archive)
            verified = restore.verify_archive(database, "fixture-source", "roundtrip")
            output = root / "restored.bin"
            restored = restore.restore_archive(
                database,
                "fixture-source",
                "roundtrip",
                output,
            )
            output_before = file_identity(output)
            replay = restore.restore_archive(
                database,
                "fixture-source",
                "roundtrip",
                output,
            )

            self.assertEqual(verified["verified_part_count"], 2)
            self.assertEqual(verified["package"]["byte_size"], MAX_PART_BYTES + 123)
            self.assertEqual(verified["package"]["sha256"], package_sha256)
            self.assertEqual(restored["package_verification"], "PASS")
            self.assertFalse(restored["idempotent"])
            self.assertTrue(replay["idempotent"])
            self.assertEqual(output.stat().st_size, MAX_PART_BYTES + 123)
            self.assertEqual(sha256_file(output), package_sha256)
            self.assertEqual(file_identity(output), output_before)
            self.assertEqual(file_identity(package), package_before)
            self.assertEqual(archive_identity(archive), archive_before)
            self.assertFalse(list(root.glob(".*.restore-*.tmp")))

    def test_both_registered_legacy_manifests_verify_and_restore_without_running_commands(self) -> None:
        for schema_version, source_id in (
            (restore.CHATGPT_LEGACY_SCHEMA, "chatgpt"),
            (restore.BRANCH_LEGACY_SCHEMA, "git-remote-branches"),
        ):
            with self.subTest(schema_version=schema_version), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                database = root / "OpenAIDatabase"
                database.mkdir()
                install_contracts(database)
                archive, manifest = legacy_manifest(
                    database,
                    source_id,
                    "2026-07-08",
                    schema_version,
                )
                before = archive_identity(archive)
                verified = restore.verify_archive(database, source_id, "2026-07-08")
                output = root / f"restored-{source_id}.bin"
                restored = restore.restore_archive(database, source_id, "2026-07-08", output)

                package = manifest.get("original_file", manifest.get("bundle"))
                self.assertEqual(verified["manifest_schema_version"], schema_version)
                self.assertTrue(verified["legacy_read_only"])
                self.assertEqual(restored["package"]["sha256"], package["sha256"])
                self.assertEqual(output.read_bytes(), b"legacy archive fixture\n")
                self.assertFalse((root / "must-not-run").exists())
                self.assertEqual(archive_identity(archive), before)

    def test_tampered_missing_extra_and_symlink_parts_fail_closed(self) -> None:
        cases = ("tampered", "missing", "extra", "symlink")
        for case in cases:
            with self.subTest(case=case), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                database = root / "OpenAIDatabase"
                database.mkdir()
                install_contracts(database)
                archive, _ = legacy_manifest(
                    database,
                    "chatgpt",
                    "2026-07-08",
                    restore.CHATGPT_LEGACY_SCHEMA,
                )
                part = next((archive / "parts").iterdir())
                if case == "tampered":
                    part.write_bytes(b"tampered bytes\n")
                elif case == "missing":
                    part.unlink()
                elif case == "extra":
                    (archive / "parts/extra.part").write_bytes(b"extra")
                else:
                    target = root / "outside.bin"
                    target.write_bytes(part.read_bytes())
                    part.unlink()
                    part.symlink_to(target)

                with self.assertRaises(restore.ArchiveRestoreError):
                    restore.verify_archive(database, "chatgpt", "2026-07-08")

    def test_manifest_order_path_and_schema_fail_closed(self) -> None:
        mutators = (
            lambda payload: payload["parts"][0].update(index=1),
            lambda payload: payload["parts"][0].update(filename="../escape.part"),
            lambda payload: payload.update(schema_version="unknown.v1"),
            lambda payload: payload.update(path="OpenAIDatabase/data/raw_archives/other/run"),
        )
        for index, mutate in enumerate(mutators):
            with self.subTest(index=index), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                database = root / "OpenAIDatabase"
                database.mkdir()
                install_contracts(database)
                archive, payload = legacy_manifest(
                    database,
                    "chatgpt",
                    "2026-07-08",
                    restore.CHATGPT_LEGACY_SCHEMA,
                )
                mutate(payload)
                (archive / "manifest.json").write_text(json.dumps(payload), encoding="utf-8")

                with self.assertRaises(restore.ArchiveRestoreError):
                    restore.verify_archive(database, "chatgpt", "2026-07-08")

    def test_existing_conflict_and_archive_local_output_are_never_overwritten(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            archive, _ = legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            conflict = root / "existing.bin"
            conflict.write_bytes(b"keep me")
            before = file_identity(conflict)

            with self.assertRaisesRegex(restore.ArchiveRestoreError, "conflicts"):
                restore.restore_archive(database, "chatgpt", "2026-07-08", conflict)
            with self.assertRaisesRegex(restore.ArchiveRestoreError, "outside"):
                restore.restore_archive(
                    database,
                    "chatgpt",
                    "2026-07-08",
                    archive / "restored.zip",
                )

            self.assertEqual(conflict.read_bytes(), b"keep me")
            self.assertEqual(file_identity(conflict), before)
            self.assertFalse((archive / "restored.zip").exists())

    def test_failed_restore_cleans_only_its_owned_temporary_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "failed.bin"

            with (
                mock.patch.object(
                    restore,
                    "_stream_and_verify",
                    side_effect=restore.ArchiveRestoreError("injected stream failure"),
                ),
                self.assertRaisesRegex(restore.ArchiveRestoreError, "injected"),
            ):
                restore.restore_archive(database, "chatgpt", "2026-07-08", output)

            self.assertFalse(output.exists())
            self.assertFalse(list(root.glob(".*.restore-*.tmp")))

    def test_post_read_part_or_manifest_mutation_is_detected_before_pass(self) -> None:
        for target in ("part", "manifest"):
            with self.subTest(target=target), tempfile.TemporaryDirectory() as temp_dir:
                root = Path(temp_dir).resolve()
                database = root / "OpenAIDatabase"
                database.mkdir()
                install_contracts(database)
                archive, _ = legacy_manifest(
                    database,
                    "chatgpt",
                    "2026-07-08",
                    restore.CHATGPT_LEGACY_SCHEMA,
                )
                real_stream = restore._stream_and_verify

                def mutate_after_read(loaded, output_fd):
                    proof = real_stream(loaded, output_fd)
                    path = (
                        next((archive / "parts").iterdir())
                        if target == "part"
                        else archive / "manifest.json"
                    )
                    payload = path.read_bytes()
                    path.write_bytes(bytes([payload[0] ^ 1]) + payload[1:])
                    return proof

                with (
                    mock.patch.object(restore, "_stream_and_verify", side_effect=mutate_after_read),
                    self.assertRaises(restore.ArchiveRestoreError),
                ):
                    restore.verify_archive(database, "chatgpt", "2026-07-08")

    def test_existing_identical_output_mutation_during_verify_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "existing.bin"
            output.write_bytes(b"legacy archive fixture\n")
            real_stream = restore._stream_and_verify

            def mutate_output_after_archive_read(loaded, output_fd):
                proof = real_stream(loaded, output_fd)
                output.write_bytes(b"x" * len(output.read_bytes()))
                return proof

            with (
                mock.patch.object(
                    restore,
                    "_stream_and_verify",
                    side_effect=mutate_output_after_archive_read,
                ),
                self.assertRaisesRegex(restore.ArchiveRestoreError, "existing restore output changed"),
            ):
                restore.restore_archive(database, "chatgpt", "2026-07-08", output)

    def test_newly_published_output_mutation_before_final_pass_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "published-then-mutated.bin"
            real_finish = restore._finish_archive_verification

            def mutate_after_archive_finish(opened, loaded, proof):
                real_finish(opened, loaded, proof)
                output.write_bytes(b"x" * len(output.read_bytes()))

            with (
                mock.patch.object(
                    restore,
                    "_finish_archive_verification",
                    side_effect=mutate_after_archive_finish,
                ),
                self.assertRaises(restore.ArchiveRestorePartialWriteError) as raised,
            ):
                restore.restore_archive(database, "chatgpt", "2026-07-08", output)

            self.assertTrue(raised.exception.output_may_exist)
            self.assertFalse(raised.exception.output_complete)
            self.assertTrue(output.exists())

    def test_parent_fsync_failure_reports_complete_published_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "published.bin"
            real_fsync = restore.os.fsync
            calls = 0

            def fail_parent_fsync(descriptor: int) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("injected parent fsync failure")
                real_fsync(descriptor)

            with (
                mock.patch.object(restore.os, "fsync", side_effect=fail_parent_fsync),
                self.assertRaises(restore.ArchiveRestorePostPublishError),
            ):
                restore.restore_archive(database, "chatgpt", "2026-07-08", output)

            self.assertEqual(output.read_bytes(), b"legacy archive fixture\n")
            self.assertFalse(list(root.glob(".*.restore-*.tmp")))

    def test_parent_fsync_failure_with_concurrent_mutation_reports_incomplete_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "published-mutated-before-fsync.bin"
            real_fsync = restore.os.fsync
            calls = 0

            def mutate_then_fail_parent_fsync(descriptor: int) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    output.write_bytes(b"x" * len(output.read_bytes()))
                    raise OSError("injected parent fsync failure")
                real_fsync(descriptor)

            with (
                mock.patch.object(
                    restore.os,
                    "fsync",
                    side_effect=mutate_then_fail_parent_fsync,
                ),
                self.assertRaises(restore.ArchiveRestorePartialWriteError) as raised,
            ):
                restore.restore_archive(database, "chatgpt", "2026-07-08", output)

            self.assertTrue(raised.exception.output_may_exist)
            self.assertFalse(raised.exception.output_complete)
            self.assertFalse(raised.exception.temporary_output_may_exist)

    def test_cli_verify_restore_and_failure_results_are_truthful(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contracts(database)
            legacy_manifest(
                database,
                "chatgpt",
                "2026-07-08",
                restore.CHATGPT_LEGACY_SCHEMA,
            )
            output = root / "cli.bin"

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                verify_return_code = raw_archive_manifest_cli.main(
                    [
                        "verify",
                        "--database-dir",
                        str(database),
                        "--source-id",
                        "chatgpt",
                        "--archive-id",
                        "2026-07-08",
                    ]
                )
            self.assertEqual(verify_return_code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["operation"], "verify")

            stdout = io.StringIO()
            with redirect_stdout(stdout):
                restore_return_code = raw_archive_manifest_cli.main(
                    [
                        "restore",
                        "--database-dir",
                        str(database),
                        "--source-id",
                        "chatgpt",
                        "--archive-id",
                        "2026-07-08",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(restore_return_code, 0)
            self.assertEqual(json.loads(stdout.getvalue())["operation"], "restore")
            output.write_bytes(b"conflict")
            stdout = io.StringIO()
            with redirect_stdout(stdout):
                conflict_return_code = raw_archive_manifest_cli.main(
                    [
                        "restore",
                        "--database-dir",
                        str(database),
                        "--source-id",
                        "chatgpt",
                        "--archive-id",
                        "2026-07-08",
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(conflict_return_code, 1)
            conflict = json.loads(stdout.getvalue())
            self.assertTrue(conflict["output_may_exist"])
            self.assertIn("conflicts", conflict["reason"])


if __name__ == "__main__":
    unittest.main()
