from __future__ import annotations

import contextlib
import copy
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import archive_chunking as chunking  # noqa: E402
from memory_atlas_cli.raw_ledger import RawLedgerError, capture_source_stat  # noqa: E402
import raw_archive_manifest as raw_archive_manifest_cli  # noqa: E402


def install_contract(database: Path) -> None:
    source = ROOT / chunking.CONTRACT_PATH
    target = database / chunking.CONTRACT_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")


def create_sparse_package(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("wb") as handle:
        handle.truncate(size)
        if size >= 16:
            handle.seek(0)
            handle.write(b"memory-atlas")
            handle.seek(size - 4)
            handle.write(b"tail")


def identity(path: Path) -> tuple[int, int, int, int]:
    metadata = path.stat()
    return (
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
    )


class MemoryAtlasArchiveChunkingTests(unittest.TestCase):
    def test_canonical_contract_fixes_45_mib_and_task_boundary(self) -> None:
        contract = chunking.load_archive_chunking_contract(ROOT)

        self.assertEqual(contract["task_id"], "S06-P2-T2")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S06-P2-T2")
        self.assertEqual(contract["threshold"]["max_part_bytes"], 45 * 1024 * 1024)
        self.assertLess(
            contract["threshold"]["max_part_bytes"],
            contract["threshold"]["github_warning_bytes"],
        )
        self.assertIs(contract["phase_boundary"]["does_not_restore_archives"], True)
        self.assertIs(contract["phase_boundary"]["does_not_rewrite_legacy_archives"], True)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S06-P2-T3")
        self.assertIs(contract["publication"]["exclusive_output_reservation"], True)
        self.assertIs(contract["publication"]["normal_failure_cleanup_requires_identity"], True)

        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            target = root / chunking.CONTRACT_PATH
            target.parent.mkdir(parents=True)
            broken = copy.deepcopy(contract)
            broken["threshold"]["max_part_bytes"] += 1
            target.write_text(json.dumps(broken), encoding="utf-8")
            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.load_archive_chunking_contract(root, target)

    def test_package_at_exact_threshold_is_not_split_or_copied(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            package = root / "exact-threshold.bin"
            database.mkdir()
            install_contract(database)
            create_sparse_package(package, chunking.MAX_PART_BYTES)
            before = capture_source_stat(package)

            result = chunking.chunk_archive_package(
                database,
                package,
                "fixture-source",
                "exact-threshold",
            )

            self.assertEqual(result["status"], "PASS")
            self.assertIs(result["chunking_required"], False)
            self.assertEqual(result["part_count"], 0)
            self.assertIsNone(result["archive_path"])
            self.assertFalse((database / chunking.ARCHIVE_ROOT).exists())
            self.assertEqual(capture_source_stat(package), before)

            existing = (
                database
                / chunking.ARCHIVE_ROOT
                / "fixture-source"
                / "exact-threshold"
            )
            existing.mkdir(parents=True)
            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "exact-threshold",
                )

    def test_real_45_mib_split_is_deterministic_idempotent_and_below_warning(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            package = root / "large-package.bin"
            database_a = root / "database-a"
            database_b = root / "database-b"
            database_a.mkdir()
            database_b.mkdir()
            install_contract(database_a)
            install_contract(database_b)
            create_sparse_package(package, chunking.MAX_PART_BYTES + 123)
            before_source = capture_source_stat(package)

            first = chunking.chunk_archive_package(
                database_a,
                package,
                "fixture-source",
                "deterministic-run",
            )
            second = chunking.chunk_archive_package(
                database_b,
                package,
                "fixture-source",
                "deterministic-run",
            )

            archive_a = database_a / str(first["archive_path"])
            archive_b = database_b / str(second["archive_path"])
            manifest_a = archive_a / chunking.MANIFEST_FILENAME
            manifest_b = archive_b / chunking.MANIFEST_FILENAME
            self.assertEqual(manifest_a.read_bytes(), manifest_b.read_bytes())
            self.assertEqual(first["part_count"], 2)
            self.assertEqual(first["parts"][0]["byte_size"], chunking.MAX_PART_BYTES)
            self.assertEqual(first["parts"][1]["byte_size"], 123)
            self.assertLess(first["largest_part_bytes"], chunking.GITHUB_WARNING_BYTES)
            self.assertLess(first["largest_part_bytes"], chunking.GITHUB_HARD_LIMIT_BYTES)
            self.assertEqual(first["package"]["byte_size"], chunking.MAX_PART_BYTES + 123)
            self.assertEqual(capture_source_stat(package), before_source)

            manifest_text = manifest_a.read_text(encoding="utf-8")
            self.assertNotIn(str(root), manifest_text)
            self.assertNotIn("created_at", manifest_text)
            self.assertNotIn("restore", manifest_text)
            manifest = json.loads(manifest_text)
            chunking.validate_chunk_manifest(manifest)
            for part in manifest["parts"]:
                path_a = archive_a / part["filename"]
                path_b = archive_b / part["filename"]
                self.assertEqual(path_a.read_bytes(), path_b.read_bytes())
                self.assertEqual(hashlib.sha256(path_a.read_bytes()).hexdigest(), part["sha256"])

            tracked_paths = [manifest_a, *(archive_a / part["filename"] for part in manifest["parts"])]
            identities_before = {path: identity(path) for path in tracked_paths}
            replay = chunking.chunk_archive_package(
                database_a,
                package,
                "fixture-source",
                "deterministic-run",
            )
            identities_after = {path: identity(path) for path in tracked_paths}
            self.assertIs(replay["idempotent"], True)
            self.assertEqual(identities_after, identities_before)
            self.assertEqual(capture_source_stat(package), before_source)

            first_part = archive_a / manifest["parts"][0]["filename"]
            with first_part.open("r+b") as handle:
                handle.seek(0)
                handle.write(b"conflict")
            conflict_identity = identity(first_part)
            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.chunk_archive_package(
                    database_a,
                    package,
                    "fixture-source",
                    "deterministic-run",
                )
            self.assertEqual(identity(first_part), conflict_identity)

    def test_manifest_rejects_nonsequential_oversized_and_nonportable_values(self) -> None:
        digest = "0" * 64
        payload = {
            "schema_version": chunking.MANIFEST_SCHEMA_VERSION,
            "task_id": "S06-P2-T2",
            "acceptance_id": "ACC-MA-V121-S06-P2-T2",
            "source_id": "fixture-source",
            "archive_id": "fixture-archive",
            "archive_path": "data/raw_archives/fixture-source/fixture-archive",
            "package": {
                "filename": "package.bin",
                "byte_size": chunking.MAX_PART_BYTES + 1,
                "sha256": digest,
            },
            "split": {
                "method": "fixed_bytes",
                "max_part_bytes": chunking.MAX_PART_BYTES,
                "github_warning_bytes": chunking.GITHUB_WARNING_BYTES,
                "part_count": 2,
                "part_index_width": chunking.PART_INDEX_WIDTH,
                "deterministic": True,
            },
            "parts": [
                {
                    "index": 0,
                    "filename": "parts/fixture-archive.part-000000",
                    "byte_size": chunking.MAX_PART_BYTES,
                    "sha256": digest,
                },
                {
                    "index": 1,
                    "filename": "parts/fixture-archive.part-000001",
                    "byte_size": 1,
                    "sha256": digest,
                },
            ],
        }
        self.assertEqual(chunking.validate_chunk_manifest(payload), payload)

        mutations = {
            "nonsequential": lambda item: item["parts"][1].update({"index": 2}),
            "oversized": lambda item: item["parts"][0].update(
                {"byte_size": chunking.GITHUB_WARNING_BYTES}
            ),
            "absolute": lambda item: item.update({"archive_path": "/tmp/archive"}),
            "nonportable": lambda item: item.update({"source_id": "../fixture"}),
            "timestamp": lambda item: item.update({"created_at": "2026-07-15T00:00:00Z"}),
        }
        for label, mutate in mutations.items():
            with self.subTest(label=label):
                broken = copy.deepcopy(payload)
                mutate(broken)
                with self.assertRaises(chunking.ArchiveChunkError):
                    chunking.validate_chunk_manifest(broken)

    def test_source_and_output_symlinks_fail_before_archive_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            package_link = root / "package-link.bin"
            package_link.symlink_to(package)

            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.chunk_archive_package(
                    database,
                    package_link,
                    "fixture-source",
                    "source-symlink",
                )

            archive_parent = database / chunking.ARCHIVE_ROOT / "fixture-source"
            archive_parent.mkdir(parents=True)
            outside = root / "outside"
            outside.mkdir()
            (archive_parent / "output-symlink").symlink_to(outside, target_is_directory=True)
            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "output-symlink",
                )
            self.assertEqual(list(outside.iterdir()), [])

    def test_archive_root_symlink_fails_without_writing_outside_database(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            outside = root / "outside"
            outside.mkdir()
            (database / "data").symlink_to(outside, target_is_directory=True)

            with self.assertRaises(chunking.ArchiveChunkError):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "root-symlink",
                )

            self.assertEqual(list(outside.iterdir()), [])

    def test_existing_lock_fails_closed_and_is_never_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            archive_path = (
                database / chunking.ARCHIVE_ROOT / "fixture-source" / "locked-run"
            )
            archive_path.parent.mkdir(parents=True)
            lock_path = chunking.archive_chunk_lock_path(archive_path)
            lock_payload = {
                "schema_version": chunking.LOCK_SCHEMA_VERSION,
                "pid": 999_999_999,
                "hostname": chunking.socket.gethostname(),
                "created_at_ns": 1,
                "archive_id": "locked-run",
            }
            lock_path.write_text(json.dumps(lock_payload) + "\n", encoding="utf-8")
            before = lock_path.read_bytes()

            with self.assertRaisesRegex(chunking.ArchiveChunkError, "manual verification"):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "locked-run",
                )

            self.assertEqual(lock_path.read_bytes(), before)
            self.assertEqual(
                chunking.inspect_archive_chunk_lock(archive_path)["state"],
                "stale_pid_manual_verification",
            )

    def test_lock_identity_change_fails_closed_and_preserves_foreign_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            archive_parent = Path(temp_dir).resolve()
            archive_path = archive_parent / "swapped-lock-run"
            lock_path = chunking.archive_chunk_lock_path(archive_path)

            with self.assertRaises(chunking.ArchiveChunkPartialWriteError):
                with chunking.archive_chunk_lock(archive_path):
                    lock_path.unlink()
                    lock_path.write_text("foreign replacement\n", encoding="utf-8")

            self.assertEqual(lock_path.read_text(encoding="utf-8"), "foreign replacement\n")

    def test_source_stat_change_during_small_fixture_split_fails(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            package = root / "package.bin"
            parts = root / "parts"
            package.write_bytes(b"abcdefghi")
            parts.mkdir()
            expected = capture_source_stat(package)
            original_guard = chunking.source_stat_guard

            @contextlib.contextmanager
            def mutate_after_read(*args, **kwargs):
                with original_guard(*args, **kwargs) as inventory:
                    yield inventory
                    package.write_bytes(b"abcdefgXy")

            with (
                mock.patch.object(chunking, "MAX_PART_BYTES", 4),
                mock.patch.object(chunking, "READ_CHUNK_BYTES", 2),
                mock.patch.object(chunking, "source_stat_guard", mutate_after_read),
                self.assertRaises(chunking.ArchiveChunkError),
            ):
                parts_fd = os.open(parts, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    chunking._scan_package(package, "fixture", expected, parts_fd)
                finally:
                    os.close(parts_fd)

    def test_normal_failure_removes_only_owned_reserved_output_and_lock(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            archive_parent = database / chunking.ARCHIVE_ROOT / "fixture-source"

            with (
                mock.patch.object(
                    chunking,
                    "_scan_package",
                    side_effect=chunking.ArchiveChunkError("injected write failure"),
                ),
                self.assertRaisesRegex(chunking.ArchiveChunkError, "injected"),
            ):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "failed-run",
                )

            self.assertFalse((archive_parent / "failed-run").exists())
            self.assertFalse(chunking.archive_chunk_lock_path(archive_parent / "failed-run").exists())

    def test_cleanup_refuses_replaced_output_and_preserves_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            archive_parent = database / chunking.ARCHIVE_ROOT / "fixture-source"
            archive_path = archive_parent / "swapped-run"
            moved_path = archive_parent / "moved-owned-output"

            def swap_output_then_fail(*_args, **_kwargs):
                archive_path.rename(moved_path)
                archive_path.mkdir()
                (archive_path / "sentinel").write_text("do not delete", encoding="utf-8")
                raise chunking.ArchiveChunkError("injected post-swap failure")

            with (
                mock.patch.object(chunking, "_scan_package", side_effect=swap_output_then_fail),
                self.assertRaises(chunking.ArchiveChunkPartialWriteError),
            ):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "swapped-run",
                )

            self.assertEqual((archive_path / "sentinel").read_text(encoding="utf-8"), "do not delete")
            self.assertTrue((moved_path / chunking.PARTS_DIRECTORY).is_dir())
            self.assertFalse(chunking.archive_chunk_lock_path(archive_path).exists())

    def test_cleanup_refuses_replaced_part_and_preserves_replacement(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            archive_path = (
                database
                / chunking.ARCHIVE_ROOT
                / "fixture-source"
                / "swapped-part-run"
            )
            first_part = (
                archive_path
                / chunking.PARTS_DIRECTORY
                / "swapped-part-run.part-000000"
            )

            def replace_part_then_fail(*_args, **_kwargs):
                first_part.unlink()
                first_part.write_bytes(b"foreign replacement")
                raise chunking.ArchiveChunkError("injected post-swap failure")

            with (
                mock.patch.object(chunking, "_build_manifest", side_effect=replace_part_then_fail),
                self.assertRaises(chunking.ArchiveChunkPartialWriteError),
            ):
                chunking.chunk_archive_package(
                    database,
                    package,
                    "fixture-source",
                    "swapped-part-run",
                )

            self.assertEqual(first_part.read_bytes(), b"foreign replacement")
            self.assertTrue(archive_path.is_dir())
            self.assertFalse(chunking.archive_chunk_lock_path(archive_path).exists())

    def test_cli_reports_parent_fsync_failure_as_maybe_published(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            install_contract(database)
            package = root / "package.bin"
            create_sparse_package(package, chunking.MAX_PART_BYTES + 1)
            original_fsync = chunking._fsync_directory_fd

            def fail_parent_fsync(descriptor: int, label: str) -> None:
                if label == "archive parent":
                    raise chunking.ArchiveChunkError("injected parent fsync failure")
                original_fsync(descriptor, label)

            output = io.StringIO()
            with (
                mock.patch.object(chunking, "_fsync_directory_fd", side_effect=fail_parent_fsync),
                contextlib.redirect_stdout(output),
            ):
                return_code = raw_archive_manifest_cli.main(
                    [
                        "chunk",
                        "--database-dir",
                        str(database),
                        "--package",
                        str(package),
                        "--source-id",
                        "fixture-source",
                        "--archive-id",
                        "post-publish-run",
                    ]
                )

            payload = json.loads(output.getvalue())
            self.assertEqual(return_code, 1)
            self.assertIs(payload["published_archive_may_exist"], True)
            self.assertIs(payload["incomplete_archive_may_exist"], False)
            archive_path = (
                database
                / chunking.ARCHIVE_ROOT
                / "fixture-source"
                / "post-publish-run"
            )
            manifest = json.loads(
                (archive_path / chunking.MANIFEST_FILENAME).read_text(encoding="utf-8")
            )
            self.assertEqual(chunking.validate_chunk_manifest(manifest), manifest)

    def test_cli_uses_target_database_contract_and_never_pushes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "database"
            database.mkdir()
            package = root / "small.bin"
            package.write_bytes(b"small package")
            command = [
                sys.executable,
                str(ROOT / "scripts/raw_archive_manifest.py"),
                "chunk",
                "--database-dir",
                str(database),
                "--package",
                str(package),
                "--source-id",
                "fixture-source",
                "--archive-id",
                "cli-run",
            ]

            missing = subprocess.run(command, text=True, capture_output=True, check=False)
            self.assertEqual(missing.returncode, 1, missing.stderr)
            self.assertEqual(json.loads(missing.stdout)["status"], "FAIL")
            install_contract(database)
            result = subprocess.run(command, text=True, capture_output=True, check=False)

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertIs(payload["chunking_required"], False)
            self.assertIs(payload["remote_push"], False)
            self.assertFalse((database / chunking.ARCHIVE_ROOT).exists())


if __name__ == "__main__":
    unittest.main()
