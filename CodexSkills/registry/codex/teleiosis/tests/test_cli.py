from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, load_json, write_json


class CliTests(unittest.TestCase):
    def run_cli(self, script: Path, *args: str) -> tuple[int, dict, str]:
        env = dict(os.environ)
        env["PYTHONDONTWRITEBYTECODE"] = "1"
        completed = subprocess.run(
            [sys.executable, str(script), *args],
            cwd=str(ROOT), env=env, capture_output=True, text=True, timeout=120, check=False,
        )
        lines = [line for line in completed.stdout.splitlines() if line.strip()]
        self.assertEqual(len(lines), 1, {"stdout": completed.stdout, "stderr": completed.stderr})
        return completed.returncode, json.loads(lines[0]), completed.stderr

    def test_primary_cli_contract(self) -> None:
        code, data, stderr = self.run_cli(ROOT / "scripts/teleiosis.py", "contract")
        self.assertEqual(code, 0)
        self.assertTrue(data["ok"])
        self.assertEqual(data["result"]["total_stages"], 36)
        self.assertEqual(stderr, "")

    def test_start_here_defaults_to_check(self) -> None:
        code, data, _ = self.run_cli(ROOT / "START_HERE.py")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["status"], "PASS")
        self.assertEqual(data["result"]["message_zh"], "当前包完整，可直接安装。")

    def test_invalid_arguments_return_json_without_traceback(self) -> None:
        code, data, stderr = self.run_cli(ROOT / "scripts/teleiosis.py", "not-a-command")
        self.assertEqual(code, 2)
        self.assertFalse(data["ok"])
        self.assertEqual(data["error"]["code"], "ARGUMENT_ERROR")
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("Traceback", json.dumps(data, ensure_ascii=False))

    def test_check_is_strict(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/teleiosis.py", "check")
        self.assertEqual(code, 0)
        self.assertTrue(data["result"]["checks"]["manifest"]["strict"])

    def test_market_alias_exposes_market_capabilities(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/wbi_market.py")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["module"], "S")

    def test_product_alias_exposes_product_capabilities(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/wbi_product.py")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["module"], "P")

    def test_arena_alias_exposes_arena_capabilities(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/wbi_arena.py")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["module"], "A")

    def test_legacy_wbi_alias_uses_same_contract(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/wbi.py", "contract")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["scope_mode"], "FULL_NO_ROUTING")

    def test_teleiosis_run_alias_uses_same_contract(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/teleiosis_run.py", "contract")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["round_sequence"], ["T", "C", "S", "C", "P", "C", "A", "C"])

    def test_install_wrapper_supports_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            code, data, _ = self.run_cli(ROOT / "install.py", "--skills-root", str(Path(tmp) / "skills"), "--dry-run")
            self.assertEqual(code, 0)
            self.assertEqual(data["result"]["status"], "DRY_RUN_READY")

    def test_arena_freeze_cli(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            raw = base / "raw.json"
            frozen = base / "frozen.json"
            write_json(raw, load_json("templates/arena-spec.example.json"))
            code, data, _ = self.run_cli(ROOT / "scripts/arena_lab.py", "freeze", "--spec", str(raw), "--output", str(frozen), "--frozen-at", "2026-08-02T00:00:00Z")
            self.assertEqual(code, 0)
            self.assertEqual(data["result"]["status"], "FROZEN")
            self.assertTrue(frozen.is_file())

    def test_capabilities_reject_unknown_module(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/teleiosis.py", "capabilities", "--module", "X")
        self.assertEqual(code, 2)
        self.assertEqual(data["error"]["code"], "ARGUMENT_ERROR")

    def test_contract_never_issues_formal_pass(self) -> None:
        code, data, _ = self.run_cli(ROOT / "scripts/teleiosis.py", "contract")
        self.assertEqual(code, 0)
        self.assertEqual(data["result"]["formal_pass_authority"], "external independent verifier")


if __name__ == "__main__":
    unittest.main()
