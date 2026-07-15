from __future__ import annotations

import hashlib
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

from memory_atlas_cli import archive_chunking as chunking  # noqa: E402
from memory_atlas_cli import archive_restore as restore  # noqa: E402
from memory_atlas_cli.credential_exclusion import CREDENTIAL_CONTRACT_PATH  # noqa: E402
from memory_atlas_cli.raw_ledger import RAW_LEDGER_CONTRACT_PATH  # noqa: E402
from privacy_guard import scan_repo_privacy  # noqa: E402
import raw_archive_manifest  # noqa: E402


TASK_ID = "S06-P3-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S06-P3-T3"
FIXTURE_MATRIX = (
    {"scenario": "append", "contract": "raw_ledger", "input": "synthetic_transcript"},
    {"scenario": "duplicate", "contract": "raw_ledger", "input": "synthetic_transcript"},
    {"scenario": "tamper", "contract": "raw_ledger", "input": "synthetic_transcript"},
    {"scenario": "chunk", "contract": "archive_chunking", "input": "synthetic_package"},
    {"scenario": "restore", "contract": "archive_restore", "input": "synthetic_package"},
    {"scenario": "credential_block", "contract": "credential_exclusion", "input": "synthetic_secret"},
)
FIXTURE_BOUNDARY = {
    "real_private_credentials": False,
    "real_public_raw_read": False,
    "real_public_raw_write": False,
    "network_access": False,
    "remote_git_write": False,
}


def install_contract(database: Path, relative: Path) -> None:
    target = database / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes((ROOT / relative).read_bytes())


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while chunk := handle.read(1024 * 1024):
            digest.update(chunk)
    return digest.hexdigest()


def file_identity(path: Path) -> tuple[int, int, int, int]:
    metadata = path.stat(follow_symlinks=False)
    return metadata.st_ino, metadata.st_size, metadata.st_mtime_ns, metadata.st_ctime_ns


def create_minimal_split_package(path: Path) -> None:
    size = chunking.MAX_PART_BYTES + 17
    with path.open("wb") as handle:
        handle.truncate(size)
        handle.seek(0)
        handle.write(b"memory-atlas-fixture")
        handle.seek(size - 4)
        handle.write(b"tail")


class MemoryAtlasRawContractFixtureTests(unittest.TestCase):
    def test_fixture_matrix_is_complete_and_non_private(self) -> None:
        self.assertEqual(TASK_ID, "S06-P3-T3")
        self.assertEqual(ACCEPTANCE_ID, "ACC-MA-V121-S06-P3-T3")
        self.assertEqual(
            {row["scenario"] for row in FIXTURE_MATRIX},
            {"append", "duplicate", "tamper", "chunk", "restore", "credential_block"},
        )
        self.assertEqual(len(FIXTURE_MATRIX), 6)
        self.assertTrue(all(row["input"].startswith("synthetic_") for row in FIXTURE_MATRIX))
        self.assertEqual(set(FIXTURE_BOUNDARY.values()), {False})

    def test_small_raw_fixture_append_duplicate_and_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir).resolve() / "OpenAIDatabase"
            database.mkdir()
            install_contract(database, RAW_LEDGER_CONTRACT_PATH)
            raw = database / "data/public_raw/agents/fixture/session.fixture.jsonl"
            raw.parent.mkdir(parents=True)
            original = b'{"text":"fixture alpha"}\n'
            raw.write_bytes(original)
            raw_identity = file_identity(raw)

            first = raw_archive_manifest.record_raw_ledger(
                database,
                "2026-07-15T00:00:00Z",
            )
            ledger = database / first["hash_ledger_path"]
            ledger_bytes = ledger.read_bytes()
            ledger_identity = file_identity(ledger)
            replay = raw_archive_manifest.record_raw_ledger(
                database,
                "2026-07-15T00:01:00Z",
            )

            self.assertEqual(first["ledger_appended_count"], 1)
            self.assertEqual(first["ledger_entry_count"], 1)
            self.assertIs(replay["idempotent"], True)
            self.assertEqual(replay["ledger_appended_count"], 0)
            self.assertEqual(ledger.read_bytes(), ledger_bytes)
            self.assertEqual(file_identity(ledger), ledger_identity)
            self.assertEqual(raw.read_bytes(), original)
            self.assertEqual(file_identity(raw), raw_identity)

            tampered = original.replace(b"alpha", b"bravo")
            self.assertEqual(len(tampered), len(original))
            raw.write_bytes(tampered)
            tampered_identity = file_identity(raw)
            with self.assertRaises(raw_archive_manifest.ManifestConflict):
                raw_archive_manifest.record_raw_ledger(
                    database,
                    "2026-07-15T00:02:00Z",
                )

            self.assertEqual(raw.read_bytes(), tampered)
            self.assertEqual(file_identity(raw), tampered_identity)
            self.assertEqual(ledger.read_bytes(), ledger_bytes)
            self.assertEqual(file_identity(ledger), ledger_identity)

    def test_minimal_45_mib_chunk_restore_and_manifest_tamper(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir).resolve()
            database = root / "OpenAIDatabase"
            database.mkdir()
            install_contract(database, chunking.CONTRACT_PATH)
            install_contract(database, restore.CONTRACT_PATH)
            package = root / "fixture.bin"
            create_minimal_split_package(package)
            package_identity = file_identity(package)
            package_sha256 = file_sha256(package)

            chunked = chunking.chunk_archive_package(
                database,
                package,
                "fixture-source",
                "raw-contract-fixture",
            )
            archive = database / chunked["archive_path"]
            manifest_path = archive / chunking.MANIFEST_FILENAME
            verified = restore.verify_archive(
                database,
                "fixture-source",
                "raw-contract-fixture",
            )
            output = root / "restored.bin"
            restored = restore.restore_archive(
                database,
                "fixture-source",
                "raw-contract-fixture",
                output,
            )
            output_identity = file_identity(output)
            replay = restore.restore_archive(
                database,
                "fixture-source",
                "raw-contract-fixture",
                output,
            )

            self.assertEqual(chunked["part_count"], 2)
            self.assertEqual(chunked["parts"][0]["byte_size"], chunking.MAX_PART_BYTES)
            self.assertEqual(chunked["parts"][1]["byte_size"], 17)
            self.assertLess(chunked["largest_part_bytes"], chunking.GITHUB_WARNING_BYTES)
            self.assertEqual(verified["verified_part_count"], 2)
            self.assertEqual(verified["package"]["sha256"], package_sha256)
            self.assertEqual(restored["package_verification"], "PASS")
            self.assertIs(restored["idempotent"], False)
            self.assertIs(replay["idempotent"], True)
            self.assertEqual(file_identity(output), output_identity)
            self.assertEqual(file_sha256(output), package_sha256)
            self.assertEqual(file_identity(package), package_identity)

            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            manifest["parts"][0]["sha256"] = "f" * 64
            manifest_path.write_text(
                json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            with self.assertRaises(restore.ArchiveRestoreError):
                restore.verify_archive(
                    database,
                    "fixture-source",
                    "raw-contract-fixture",
                )
            with self.assertRaises(restore.ArchiveRestoreError):
                restore.restore_archive(
                    database,
                    "fixture-source",
                    "raw-contract-fixture",
                    output,
                )

            self.assertEqual(file_identity(output), output_identity)
            self.assertEqual(file_sha256(output), package_sha256)
            self.assertEqual(file_identity(package), package_identity)

    def test_synthetic_credential_is_blocked_and_safe_transcript_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database = Path(temp_dir).resolve() / "OpenAIDatabase"
            database.mkdir()
            install_contract(database, CREDENTIAL_CONTRACT_PATH)
            gitignore = database / ".gitignore"
            gitignore.write_text(
                "*.zip\ndata/raw/\ndata/raw_encrypted/\ndata/private_imports/\n",
                encoding="utf-8",
            )
            safe_path = database / "data/public_raw/agents/fixture/session.safe.jsonl"
            safe_path.parent.mkdir(parents=True)
            safe_bytes = (
                json.dumps(
                    {"text": "Discuss token budgets and cookie recipes; your_token=redacted."},
                    sort_keys=True,
                )
                + "\n"
            ).encode("utf-8")
            safe_path.write_bytes(safe_bytes)

            subprocess.run(["git", "init", "-q"], cwd=database, check=True)
            subprocess.run(
                [
                    "git",
                    "add",
                    "-f",
                    ".gitignore",
                    CREDENTIAL_CONTRACT_PATH.as_posix(),
                    safe_path.relative_to(database).as_posix(),
                ],
                cwd=database,
                check=True,
            )
            safe_scan = scan_repo_privacy(database)

            self.assertEqual(safe_scan["status"], "PASS")
            self.assertEqual(safe_scan["high_risk_secret_hit_count"], 0)
            self.assertEqual(safe_path.read_bytes(), safe_bytes)

            secret_value = "".join(("Fixture", "Session", "Value", "123456789"))
            credential_label = "_".join(("session", "token"))
            blocked_path = database / "data/public_raw/agents/fixture/session.blocked.jsonl"
            blocked_bytes = (
                json.dumps({"text": f"{credential_label}={secret_value}"}, sort_keys=True) + "\n"
            ).encode("utf-8")
            blocked_path.write_bytes(blocked_bytes)
            subprocess.run(
                ["git", "add", "-f", blocked_path.relative_to(database).as_posix()],
                cwd=database,
                check=True,
            )
            blocked_scan = scan_repo_privacy(database)
            serialized_scan = json.dumps(blocked_scan, ensure_ascii=False, sort_keys=True)

            self.assertEqual(blocked_scan["status"], "FAIL")
            self.assertEqual(blocked_scan["credential_like_path_hit_count"], 0)
            self.assertEqual(
                blocked_scan["high_risk_secret_hits"],
                [
                    {
                        "path": "data/public_raw/agents/fixture/session.blocked.jsonl",
                        "pattern": "session_tokens",
                    }
                ],
            )
            self.assertNotIn(secret_value, serialized_scan)
            self.assertEqual(blocked_path.read_bytes(), blocked_bytes)
            self.assertEqual(safe_path.read_bytes(), safe_bytes)


if __name__ == "__main__":
    unittest.main()
