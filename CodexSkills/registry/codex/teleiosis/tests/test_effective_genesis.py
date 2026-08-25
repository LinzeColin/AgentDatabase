from __future__ import annotations

from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.genesis import verify_genesis, verify_effective_genesis


class EffectiveGenesisTests(unittest.TestCase):
    def test_base_is_unchanged_and_effective_requirement_is_added(self):
        result = verify_genesis(ROOT)
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["requirement_count"], 27)
        self.assertEqual(result["effective_requirement_count"], 28)
        self.assertEqual(result["effective_genesis_status"], "PASS")
        self.assertEqual(result["effective_composite_sha256"], "fe80c467f8ecbe8343ef0c09ef5e6f9fd9683803c8260c9188998c7e3dfca0a2")

    def test_external_effective_anchor_detects_wrong_hash(self):
        result = verify_effective_genesis(ROOT, expected_hash="0" * 64)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("external effective Genesis anchor mismatch", result["errors"])

    def test_amendment_mutation_is_detected(self):
        with tempfile.TemporaryDirectory() as td:
            copy = Path(td) / "teleiosis"
            shutil.copytree(ROOT, copy, ignore=shutil.ignore_patterns(".git", "__pycache__", "MANIFEST.sha256"))
            path = copy / "constitution/amendments/WBI-GB-AMENDMENT-001-v0.0.0.2.zh-CN.md"
            path.write_text(path.read_text(encoding="utf-8") + "\nmutation\n", encoding="utf-8")
            self.assertEqual(verify_effective_genesis(copy)["status"], "FAIL")

    def test_base_locked_file_is_still_exact(self):
        result = verify_genesis(ROOT, expected_hash="14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086")
        self.assertEqual(result["status"], "PASS", result)
        self.assertEqual(result["locked_sha256"], "14ab08b9053db4ca87140e59a49f1de8105a718a87ec2d55590c6487c1a77086")


if __name__ == "__main__":
    unittest.main()
