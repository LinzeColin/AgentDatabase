from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.dashboard import render_dashboard, render_dashboard_file  # noqa: E402


class DashboardTests(unittest.TestCase):
    def test_render_is_static_dependency_free_and_escaped(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "dashboard.html"
            result = render_dashboard({
                "title": "<script>alert(1)</script>", "version": "v1",
                "status_domains": {"formal_promotion": "BLOCKED"},
                "improvements": ["<b>unsafe</b>"], "blockers": [], "next_actions": [],
            }, output)
            html = output.read_text(encoding="utf-8")
            self.assertEqual(result["external_dependencies"], 0)
            self.assertNotIn("<script>alert(1)</script>", html)
            self.assertIn("&lt;script&gt;", html)
            self.assertNotIn("src=", html.lower())
            self.assertIn("BLOCKED", html)

    def test_template_dashboard_renders(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "dashboard.html"
            result = render_dashboard_file(ROOT / "templates/dashboard-data.json", output)
            self.assertEqual(result["status"], "PASS")
            self.assertGreater(result["bytes"], 1000)
            self.assertEqual(len(result["input_sha256"]), 64)

    def test_metrics_accept_only_object_rows(self):
        with tempfile.TemporaryDirectory() as td:
            output = Path(td) / "dashboard.html"
            render_dashboard({"title": "x", "version": "v", "status_domains": {}, "metrics": ["ignored", {"name": "n", "value": "v", "evidence": "e"}]}, output)
            html = output.read_text(encoding="utf-8")
            self.assertIn("<td>n</td>", html)
            self.assertNotIn("ignored", html)


if __name__ == "__main__":
    unittest.main()
