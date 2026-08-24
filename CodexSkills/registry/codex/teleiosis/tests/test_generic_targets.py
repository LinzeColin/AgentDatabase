from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import generate_manifest, read_frontmatter  # noqa: E402
from wbi_core.validation import validate_skill  # noqa: E402


class GenericTargetTests(unittest.TestCase):
    def make_skill(self, base: Path, name: str = "simple-skill", multiline: bool = False) -> Path:
        root = base / name
        root.mkdir(parents=True)
        description = "description: |\n  Helps with one real task.\n  Keeps the package small." if multiline else "description: Helps with one real task."
        (root / "SKILL.md").write_text(
            "---\nname: %s\n%s\nmetadata:\n  version: 2.1.0\n---\n\n# Use\n\nDo the task.\n" % (name, description),
            encoding="utf-8",
        )
        return root

    def test_generic_skill_is_not_forced_into_teleiosis_layout(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            result = validate_skill(skill, check_manifest=False)
            self.assertEqual(result["status"], "PASS", result)
            self.assertEqual(result["profile"], "generic")
            self.assertEqual(result["version"], "UNKNOWN")

    def test_generic_strict_profile_only_adds_integrity_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            self.assertEqual(validate_skill(skill, strict=True)["status"], "FAIL")
            generate_manifest(skill)
            result = validate_skill(skill, strict=True)
            self.assertEqual(result["status"], "PASS", result)

    def test_multiline_description_frontmatter_is_supported(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td), multiline=True)
            frontmatter, _ = read_frontmatter(skill / "SKILL.md")
            self.assertIn("Helps with one real task", frontmatter["description"])
            self.assertEqual(validate_skill(skill, check_manifest=False)["status"], "PASS")

    def test_explicit_optimizer_profile_rejects_generic_target(self):
        with tempfile.TemporaryDirectory() as td:
            skill = self.make_skill(Path(td))
            result = validate_skill(skill, check_manifest=False, profile="optimizer")
            self.assertEqual(result["status"], "FAIL")
            self.assertIn("missing required file: VERSION", result["errors"])


if __name__ == "__main__":
    unittest.main()
