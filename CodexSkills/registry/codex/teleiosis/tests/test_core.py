from __future__ import annotations

import ast
import json
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.genesis import verify_genesis
from wbi_core.io import copy_clean, deterministic_zip, generate_manifest, safe_extract_zip, sha256_file
from wbi_core.package import package_skill
from wbi_core.validation import validate_skill


class CoreTests(unittest.TestCase):
    def test_locked_genesis_is_valid(self):
        result = verify_genesis(ROOT)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["requirement_count"], 27)

    def test_source_is_exact_uploaded_baseline(self):
        self.assertEqual(
            sha256_file(ROOT / "constitution/GENESIS_SOURCE.v0.0.0.1.zh-CN.md"),
            "bcf4c4b4d2238bda91caf45aea6bd0001b857024ba0be0e4e241c6b37aabc12a",
        )

    def test_external_anchor_detects_coordinated_or_wrong_hash(self):
        result = verify_genesis(ROOT, expected_hash="0" * 64)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("external Genesis anchor mismatch", result["errors"])

    def test_genesis_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "teleiosis"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            path = copy / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
            self.assertEqual(verify_genesis(copy)["status"], "FAIL")

    def test_version_is_not_permanently_fixed_by_validator(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "teleiosis"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            (copy / "VERSION").write_text("v0.0.0.2\n", encoding="utf-8")
            skill = (copy / "SKILL.md").read_text(encoding="utf-8").replace('version: "v0.0.0.1"', 'version: "v0.0.0.2"')
            (copy / "SKILL.md").write_text(skill, encoding="utf-8")
            release = json.loads((copy / "metadata/release.json").read_text(encoding="utf-8"))
            release["version"] = "v0.0.0.2"
            (copy / "metadata/release.json").write_text(json.dumps(release, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            result = validate_skill(copy, check_manifest=False)
            self.assertEqual(result["status"], "PASS", result)

    def test_name_and_chinese_display_name(self):
        result = validate_skill(ROOT, check_manifest=False)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["skill"], "teleiosis")

    def test_python39_compatible_syntax(self):
        for path in (ROOT / "scripts").rglob("*.py"):
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path), feature_version=(3, 9))

    def test_manifest_detects_tamper(self):
        with tempfile.TemporaryDirectory() as temp:
            copy = Path(temp) / "teleiosis"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            generate_manifest(copy)
            self.assertEqual(validate_skill(copy, strict=True)["status"], "PASS")
            (copy / "README.md").write_text("tampered", encoding="utf-8")
            self.assertEqual(validate_skill(copy, strict=True)["status"], "FAIL")

    def test_deterministic_zip(self):
        with tempfile.TemporaryDirectory() as temp:
            parent = Path(temp)
            source = parent / "teleiosis"
            shutil.copytree(ROOT, source, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            generate_manifest(source)
            a, b = parent / "a.zip", parent / "b.zip"
            deterministic_zip(source, a)
            deterministic_zip(source, b)
            self.assertEqual(sha256_file(a), sha256_file(b))

    def test_package_post_extract_validation(self):
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "final.zip"
            result = package_skill(ROOT, output, "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086")
            self.assertEqual(result["status"], "PASS", result)
            extracted = Path(temp) / "extract"
            safe_extract_zip(output, extracted)
            self.assertTrue((extracted / "teleiosis/SKILL.md").is_file())

    def test_zip_traversal_is_rejected(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            bad = Path(temp) / "bad.zip"
            with zipfile.ZipFile(bad, "w") as archive:
                archive.writestr("../escape", "bad")
            with self.assertRaises(ValueError):
                safe_extract_zip(bad, Path(temp) / "out")

    def test_copy_clean_rejects_symlink_instead_of_dereferencing_external_data(self):
        import os
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "source"
            source.mkdir()
            outside = base / "outside-secret.txt"
            outside.write_text("secret", encoding="utf-8")
            try:
                os.symlink(str(outside), str(source / "linked.txt"))
            except (OSError, NotImplementedError):
                self.skipTest("symlinks unavailable")
            with self.assertRaises(ValueError):
                copy_clean(source, base / "copy")

    def test_zip_duplicate_case_collision_and_special_file_are_rejected(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            duplicate = base / "duplicate.zip"
            with zipfile.ZipFile(duplicate, "w") as archive:
                archive.writestr("skill/a.txt", "one")
                archive.writestr("skill/A.txt", "two")
            with self.assertRaises(ValueError):
                safe_extract_zip(duplicate, base / "duplicate-out")
            special = base / "special.zip"
            info = zipfile.ZipInfo("skill/fifo")
            info.create_system = 3
            info.external_attr = (0o010000 | 0o644) << 16
            with zipfile.ZipFile(special, "w") as archive:
                archive.writestr(info, b"x")
            with self.assertRaises(ValueError):
                safe_extract_zip(special, base / "special-out")

    def test_archive_hash_does_not_depend_on_source_execute_bits(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "skill"
            (source / "scripts").mkdir(parents=True)
            (source / "scripts/run.py").write_text("print('ok')\n", encoding="utf-8")
            (source / "README.md").write_text("hello\n", encoding="utf-8")
            a, b = base / "a.zip", base / "b.zip"
            (source / "scripts/run.py").chmod(0o600)
            deterministic_zip(source, a)
            (source / "scripts/run.py").chmod(0o777)
            deterministic_zip(source, b)
            self.assertEqual(sha256_file(a), sha256_file(b))

    def test_copy_clean_rejects_both_overlap_directions(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = base / "parent/source"
            source.mkdir(parents=True)
            (source / "x.txt").write_text("x", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "overlap"):
                copy_clean(source, source / "nested")
            with self.assertRaisesRegex(ValueError, "overlap"):
                copy_clean(source, base / "parent")

    def test_zip_backslash_and_exact_duplicate_are_rejected(self):
        import zipfile
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            bad = base / "backslash.zip"
            with zipfile.ZipFile(bad, "w") as archive:
                archive.writestr("skill\\..\\escape.txt", "x")
            with self.assertRaises(ValueError):
                safe_extract_zip(bad, base / "out-a")
            duplicate = base / "duplicate.zip"
            with zipfile.ZipFile(duplicate, "w") as archive:
                archive.writestr("skill/a.txt", "one")
                archive.writestr("skill/a.txt", "two")
            with self.assertRaises(ValueError):
                safe_extract_zip(duplicate, base / "out-b")


if __name__ == "__main__":
    unittest.main()
