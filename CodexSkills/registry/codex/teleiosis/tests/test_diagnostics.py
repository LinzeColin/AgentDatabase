from __future__ import annotations

from pathlib import Path
import os
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.diagnostics import diagnose_target


class DiagnosticTests(unittest.TestCase):
    def make_skill(self, root: Path) -> Path:
        skill = root / "sample-skill"
        skill.mkdir()
        (skill / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Helps with one bounded task.\n---\n\n# Workflow\n\nDo the task.\n",
            encoding="utf-8",
        )
        (skill / "README.md").write_text("# Sample\n", encoding="utf-8")
        (skill / "LICENSE").write_text("MIT\n", encoding="utf-8")
        return skill

    def test_text_skill_is_classified_without_execution(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            result = diagnose_target(skill, valid_as_of="2026-07-26")
            self.assertIn(result["diagnostic_status"], {"PASS", "WARN"})
            self.assertEqual(result["classification"]["target_class"], "text-and-reasoning")
            self.assertEqual(result["target"]["name"], "sample-skill")
            self.assertEqual(result["claim_boundary"].split()[0], "This")

    def test_tool_and_artifact_profile(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            (skill / "scripts").mkdir()
            (skill / "scripts/run.py").write_text("print('ok')\n", encoding="utf-8")
            (skill / "assets").mkdir()
            (skill / "assets/index.html").write_text("<p>demo</p>\n", encoding="utf-8")
            result = diagnose_target(skill, valid_as_of="2026-07-26")
            self.assertEqual(result["classification"]["target_class"], "tool-and-artifact")
            self.assertEqual(result["classification"]["suggested_verification_level"], "release")

    def test_possible_secret_blocks(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            (skill / "notes.txt").write_text("api_" + "key = '" + "ABCDEFGHIJKLMNOPQRSTUVWX" + "'\n", encoding="utf-8")
            result = diagnose_target(skill, valid_as_of="2026-07-26")
            self.assertEqual(result["diagnostic_status"], "BLOCKED")
            self.assertIn("notes.txt", result["bounded_scan"]["possible_secret_paths"])

    @unittest.skipIf(os.name == "nt", "symlink setup is platform-dependent")
    def test_symlink_blocks_packaging_profile(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            (skill / "real.txt").write_text("real\n", encoding="utf-8")
            (skill / "linked.txt").symlink_to(skill / "real.txt")
            result = diagnose_target(skill, valid_as_of="2026-07-26")
            self.assertEqual(result["diagnostic_status"], "BLOCKED")
            self.assertIn("linked.txt", result["bounded_scan"]["symlinks"])

    def test_bounded_scan_discloses_partial_evidence(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            for index in range(10):
                (skill / ("f%02d.txt" % index)).write_text("x" * 200, encoding="utf-8")
            result = diagnose_target(skill, valid_as_of="2026-07-26", max_files=2, max_text_bytes=1000)
            self.assertEqual(result["classification"]["evidence_completeness"], "PARTIAL")
            self.assertTrue(result["bounded_scan"]["truncated"])

    def test_nested_showcase_and_install_docs_are_detected(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            (skill / "assets").mkdir()
            (skill / "assets/showcase.html").write_text("<p>evidence</p>\n", encoding="utf-8")
            (skill / "delivery").mkdir()
            (skill / "delivery/INSTALL.md").write_text("# Install\n", encoding="utf-8")
            (skill / "delivery/ROLLBACK.md").write_text("# Rollback\n", encoding="utf-8")
            result = diagnose_target(skill, valid_as_of="2026-07-26")
            self.assertTrue(result["capabilities"]["has_showcase"])
            self.assertTrue(result["capabilities"]["has_install_docs"])
            self.assertTrue(result["capabilities"]["has_rollback_docs"])


if __name__ == "__main__":
    unittest.main()
