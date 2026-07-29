from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.environment_doctor import run_environment_doctor  # noqa: E402


class EnvironmentDoctorTests(unittest.TestCase):
    def test_engineering_readiness_and_formal_blockers_are_separate(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "doctor.json"
            result = run_environment_doctor(Path(td) / "work", output)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["readiness"]["engineering"], "READY")
            self.assertEqual(result["readiness"]["formal"], "BLOCKED")
            self.assertTrue(result["formal_blockers"])
            self.assertFalse(result["capabilities"]["secret_values_exposed"])
            self.assertTrue(output.is_file())

    def test_presence_of_contracts_is_reported_without_claiming_review_completion(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            review = root / "review.json"; review.write_text("{}", encoding="utf-8")
            personas = root / "team-index.json"; personas.write_text("{}", encoding="utf-8")
            result = run_environment_doctor(root / "work", review_contract=review, persona_index=personas)
            self.assertTrue(result["capabilities"]["external_review_contract_present"])
            self.assertTrue(result["capabilities"]["persona_team_index_present"])

    def test_missing_git_blocks_engineering_readiness(self):
        with tempfile.TemporaryDirectory() as td:
            with patch("wbi_core.environment_doctor.shutil.which", return_value=None):
                result = run_environment_doctor(Path(td) / "work")
            self.assertEqual(result["status"], "BLOCKED")
            self.assertIn("Git is required", result["hard_failures"])


if __name__ == "__main__":
    unittest.main()
