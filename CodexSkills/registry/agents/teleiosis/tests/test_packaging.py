from __future__ import annotations

import os
import stat
import tempfile
import unittest
import warnings
import zipfile
from pathlib import Path

from helpers import ROOT
from teleiosis_core.common import TeleiosisError, sha256_file
from teleiosis_core.integrity import verify_release
from teleiosis_core.packaging import audit_zip, build_deterministic_zip, generate_manifest, safe_extract


class PackagingTests(unittest.TestCase):
    def test_deterministic_zip_is_byte_identical(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            one = base / "one.zip"
            two = base / "two.zip"
            build_deterministic_zip(ROOT, one)
            build_deterministic_zip(ROOT, two)
            self.assertEqual(sha256_file(one), sha256_file(two))

    def test_zip_has_exactly_one_teleiosis_root(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "release.zip"
            build_deterministic_zip(ROOT, archive)
            result = audit_zip(archive)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["root"], "teleiosis")

    def test_cold_extract_passes_strict_release_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive = base / "release.zip"
            build_deterministic_zip(ROOT, archive)
            extracted = safe_extract(archive, base / "extract")
            self.assertEqual(verify_release(extracted, strict=True)["status"], "PASS")

    def test_manifest_regeneration_is_stable(self) -> None:
        before = (ROOT / "MANIFEST.sha256").read_bytes()
        generate_manifest(ROOT)
        middle = (ROOT / "MANIFEST.sha256").read_bytes()
        generate_manifest(ROOT)
        after = (ROOT / "MANIFEST.sha256").read_bytes()
        self.assertEqual(before, middle)
        self.assertEqual(middle, after)

    def test_path_traversal_zip_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("teleiosis/../escape.txt", b"bad")
            with self.assertRaises(TeleiosisError) as ctx:
                audit_zip(archive)
            self.assertEqual(ctx.exception.code, "ZIP_PATH_TRAVERSAL")

    def test_symlink_zip_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            info = zipfile.ZipInfo("teleiosis/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr(info, b"target")
            with self.assertRaises(TeleiosisError) as ctx:
                audit_zip(archive)
            self.assertEqual(ctx.exception.code, "ZIP_SYMLINK")

    def test_duplicate_zip_entry_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                with zipfile.ZipFile(archive, "w") as zf:
                    zf.writestr("teleiosis/file.txt", b"one")
                    zf.writestr("teleiosis/file.txt", b"two")
            with self.assertRaises(TeleiosisError) as ctx:
                audit_zip(archive)
            self.assertEqual(ctx.exception.code, "ZIP_DUPLICATE")

    def test_multiple_roots_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            archive = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(archive, "w") as zf:
                zf.writestr("teleiosis/file.txt", b"one")
                zf.writestr("other/file.txt", b"two")
            with self.assertRaises(TeleiosisError) as ctx:
                audit_zip(archive)
            self.assertEqual(ctx.exception.code, "ZIP_ROOT")

    def test_nonempty_extract_destination_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            archive = base / "release.zip"
            build_deterministic_zip(ROOT, archive)
            destination = base / "extract"
            destination.mkdir()
            (destination / "owner.txt").write_text("keep\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                safe_extract(archive, destination)
            self.assertEqual(ctx.exception.code, "EXTRACT_DEST_NOT_EMPTY")

    def test_wrong_source_root_name_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            wrong = base / "wrong"
            wrong.mkdir()
            (wrong / "file.txt").write_text("x\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                build_deterministic_zip(wrong, base / "bad.zip")
            self.assertEqual(ctx.exception.code, "ZIP_ROOT_NAME")

    def test_zip_output_symlink_is_rejected(self) -> None:
        if not hasattr(os, "symlink"):
            self.skipTest("symlink unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            target = base / "target.zip"
            target.write_bytes(b"x")
            link = base / "link.zip"
            os.symlink(target, link)
            with self.assertRaises(TeleiosisError) as ctx:
                build_deterministic_zip(ROOT, link)
            self.assertEqual(ctx.exception.code, "ZIP_OUTPUT_SYMLINK")


if __name__ == "__main__":
    unittest.main()
