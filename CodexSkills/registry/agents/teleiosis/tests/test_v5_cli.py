from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT


class V5CliTests(unittest.TestCase):
    def run_cli(self, *args: str, timeout: int = 180) -> tuple[int, dict, str]:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/teleiosis.py"), *args],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=timeout, check=False,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, {"stdout": completed.stdout, "stderr": completed.stderr})
        return completed.returncode, json.loads(lines[0]), completed.stderr

    def test_doctor_and_install_v5(self) -> None:
        code, data, stderr = self.run_cli("doctor")
        self.assertEqual(code, 0, data)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["status"], "PASS")
        self.assertEqual(data["result"]["next_command"], "python3 START_HERE.py install")
        self.assertEqual(stderr, "")

    def test_new_governance_commands(self) -> None:
        for command in ("skill-audit", "review", "regression"):
            with self.subTest(command=command):
                code, data, _ = self.run_cli(command)
                self.assertEqual(code, 0, data)
                self.assertEqual(data["result"]["status"], "PASS")
        code, data, _ = self.run_cli("taskpack", "validate")
        self.assertEqual(code, 0, data)
        self.assertEqual(data["result"]["status"], "PASS")
        code, data, _ = self.run_cli("taskpack", "fresh-builder")
        self.assertEqual(code, 0, data)
        self.assertEqual(data["result"]["status"], "ACCEPTANCE_PASS")

    def test_semantic_reconcile_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            repo.mkdir()
            (repo / "SKILL.md").write_text("semantic reconcile moving main\n", encoding="utf-8")
            output = Path(tmp) / "report.json"
            code, data, _ = self.run_cli(
                "semantic-reconcile", "--repository", str(repo),
                "--spec", str(ROOT / "templates/semantic-reconcile-spec.example.json"),
                "--output", str(output),
            )
            self.assertEqual(code, 0, data)
            self.assertIn(data["result"]["status"], {"READY", "BLOCKED"})
            self.assertTrue(output.is_file())

    def test_verifier_handoff_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handoff.zip"
            code, data, _ = self.run_cli("verifier-handoff", "build", "--output", str(path))
            self.assertEqual(code, 0, data)
            self.assertEqual(data["result"]["formal_pass"], "NOT_ISSUED")
            code, data, _ = self.run_cli("verifier-handoff", "validate", "--zip", str(path))
            self.assertEqual(code, 0, data)
            self.assertEqual(data["result"]["status"], "PASS")


if __name__ == "__main__":
    unittest.main()
