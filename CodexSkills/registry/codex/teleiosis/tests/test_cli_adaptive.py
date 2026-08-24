from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "scripts/wbi.py"


class AdaptiveCliTests(unittest.TestCase):
    def run_cli(self, *args: str):
        completed = subprocess.run(
            [sys.executable, str(CLI), *args],
            text=True,
            capture_output=True,
            timeout=30,
        )
        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            self.fail("CLI did not emit JSON: %s\nstdout=%s\nstderr=%s" % (exc, completed.stdout, completed.stderr))
        return completed, payload

    def make_skill(self, base: Path) -> Path:
        target = base / "sample-skill"
        target.mkdir()
        (target / "SKILL.md").write_text(
            "---\nname: sample-skill\ndescription: Bounded sample.\n---\n\n# Workflow\n\nDo one task.\n",
            encoding="utf-8",
        )
        (target / "README.md").write_text("# Sample\n", encoding="utf-8")
        (target / "LICENSE").write_text("MIT\n", encoding="utf-8")
        return target

    def test_doctor_and_adaptive_plan_cli(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = self.make_skill(base)
            diagnostic = base / "diagnostic.json"
            plan = base / "plan.json"
            completed, payload = self.run_cli(
                "doctor", str(target), "--valid-as-of", "2026-07-26", "--output", str(diagnostic)
            )
            self.assertEqual(completed.returncode, 0, payload)
            self.assertTrue(diagnostic.is_file())
            completed, payload = self.run_cli(
                "adaptive-plan", "--diagnostic", str(diagnostic), "--run-mode", "engineering", "--output", str(plan)
            )
            self.assertEqual(completed.returncode, 0, payload)
            self.assertEqual(payload["plan_status"], "READY")
            self.assertTrue(plan.is_file())

    def test_optimize_auto_preflight_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = self.make_skill(base)
            workspace = base / "workspace"
            args = (
                "optimize", str(target), "--workspace", str(workspace),
                "--run-mode", "engineering", "--valid-as-of", "2026-07-26",
            )
            first, first_payload = self.run_cli(*args)
            second, second_payload = self.run_cli(*args)
            self.assertEqual(first.returncode, 0, first_payload)
            self.assertEqual(second.returncode, 0, second_payload)
            self.assertEqual(first_payload["run_id"], second_payload["run_id"])
            self.assertTrue((workspace / "control/target-diagnostic.json").is_file())
            self.assertTrue((workspace / "control/adaptive-plan.json").is_file())

    def test_strategy_and_showcase_cli(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            workspace = base / "workspace"
            (workspace / "evidence").mkdir(parents=True)
            (workspace / "evidence/result.json").write_text("{}\n", encoding="utf-8")
            record = base / "record.json"
            record.write_text(json.dumps({
                "candidate_id": "c1", "scope": "SKILL.md", "mechanism": "wording",
                "decision": "NO_CHANGE", "change_ratio": 0.01, "metric_delta": {},
                "failure_tags": ["no_gain"], "cost": {"tokens": None},
                "evidence_paths": ["evidence/result.json"], "unknowns": ["usage unavailable"],
            }) + "\n", encoding="utf-8")
            completed, payload = self.run_cli("strategy-update", str(workspace), "--record", str(record))
            self.assertEqual(completed.returncode, 0, payload)
            completed, payload = self.run_cli("strategy-next", str(workspace))
            self.assertEqual(completed.returncode, 0, payload)
            self.assertEqual(payload["event_count"], 1)

            status = base / "status.json"
            status.write_text(json.dumps({"domains": {
                "outcome": "NOT_PROVEN", "independent_review": "UNAVAILABLE", "formal_promotion": "BLOCKED"
            }}) + "\n", encoding="utf-8")
            card = base / "card.html"
            completed, payload = self.run_cli("showcase", "--status", str(status), "--output", str(card))
            self.assertEqual(completed.returncode, 0, payload)
            self.assertIn("MARKET LEADERSHIP NOT PROVEN", card.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
