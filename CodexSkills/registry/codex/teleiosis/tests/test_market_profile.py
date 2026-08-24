from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.market_profile import build_market_profile  # noqa: E402


class MarketProfileTests(unittest.TestCase):
    def test_agent_skill_profile_inherits_luban_and_verifier_lanes(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "alpha-skill"
            root.mkdir()
            (root / "SKILL.md").write_text("---\nname: alpha-skill\ndescription: Does one thing.\n---\n\n# Use\n", encoding="utf-8")
            (root / "README.md").write_text("# alpha\n", encoding="utf-8")
            result = build_market_profile(root, valid_as_of="2026-07-26")
            self.assertEqual(result["profile_status"], "PASS", result)
            self.assertEqual(result["target_class"], "agent-skill")
            lanes = {lane["lane_id"] for lane in result["adoption_lanes"]}
            self.assertIn("luban-no-negative-optimization", lanes)
            self.assertIn("verifier-exact-subject-identity", lanes)

    def test_runtime_service_profile_adopts_operations_control_plane(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td) / "rtsp-service"
            for rel in ["configs", "deploy", "web", "cmd/server"]:
                (root / rel).mkdir(parents=True, exist_ok=True)
            (root / "Dockerfile").write_text("FROM scratch\n", encoding="utf-8")
            (root / "Makefile").write_text("build:\n\t@echo ok\n", encoding="utf-8")
            (root / "go.mod").write_text("module example.com/rtsp\n", encoding="utf-8")
            (root / "README.md").write_text("# service\n", encoding="utf-8")
            result = build_market_profile(root)
            self.assertEqual(result["target_class"], "runtime-service")
            lanes = {lane["lane_id"]: lane for lane in result["adoption_lanes"]}
            self.assertTrue(lanes["easydarwin-operations-control-plane"]["mandatory"])

    def test_cli_writes_profile_json(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            target = base / "simple-skill"
            target.mkdir()
            (target / "SKILL.md").write_text("---\nname: simple-skill\ndescription: Does one thing.\n---\n\n# Use\n", encoding="utf-8")
            output = base / "profile.json"
            completed = subprocess.run(
                [sys.executable, str(ROOT / "scripts/wbi.py"), "market-profile", str(target), "--output", str(output)],
                text=True, capture_output=True, timeout=20,
            )
            self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
            self.assertTrue(output.is_file())
            payload = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(payload["profile_status"], "PASS")

    def test_missing_target_fails_closed(self):
        result = build_market_profile(Path("/path/that/does/not/exist"))
        self.assertEqual(result["profile_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
