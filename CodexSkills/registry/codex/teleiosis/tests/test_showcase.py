from __future__ import annotations

from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import write_json
from wbi_core.showcase import generate_showcase


class ShowcaseTests(unittest.TestCase):
    def test_unproven_comparison_withholds_winner(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            status = base / "status.json"
            comparison = base / "comparison.json"
            output = base / "card.html"
            write_json(status, {"domains": {
                "control_plane": "PASS",
                "outcome": "NOT_PROVEN",
                "independent_review": "UNAVAILABLE",
                "formal_promotion": "BLOCKED",
            }})
            write_json(comparison, {"evidence_status": "PARTIAL", "claim_scope": "fixture", "winner": "Teleiosis"})
            result = generate_showcase(status, output, comparison_path=comparison)
            text = output.read_text(encoding="utf-8")
            self.assertEqual(result["status"], "PASS")
            self.assertIn("MARKET LEADERSHIP NOT PROVEN", text)
            self.assertIn("WITHHELD", text)
            self.assertNotIn("<span>Teleiosis</span>", text)
            receipt = Path(result["receipt"])
            self.assertTrue(receipt.is_file())
            receipt_payload = __import__("json").loads(receipt.read_text(encoding="utf-8"))
            self.assertEqual(receipt_payload["output"], "card.html")
            self.assertEqual(receipt_payload["path_base"], "receipt_parent")
            self.assertFalse(Path(receipt_payload["output"]).is_absolute())

    def test_html_is_escaped(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            status = base / "status.json"
            output = base / "card.html"
            write_json(status, {"domains": {"outcome": "<script>alert(1)</script>"}})
            generate_showcase(status, output, title="<b>unsafe</b>")
            text = output.read_text(encoding="utf-8")
            self.assertNotIn("<script>alert", text)
            self.assertIn("&lt;script&gt;", text)
            self.assertIn("&lt;b&gt;unsafe&lt;/b&gt;", text)

    def test_nested_domain_status_can_support_scoped_formal_label(self):
        with tempfile.TemporaryDirectory() as td:
            base = Path(td)
            status = base / "status.json"
            comparison = base / "comparison.json"
            output = base / "card.html"
            write_json(status, {"domains": {
                "outcome": {"status": "PROVEN", "evidence": "sealed benchmark"},
                "independent_review": {"status": "PASS", "evidence": "external attestation"},
                "formal_promotion": {"status": "PASS", "evidence": "frozen scope"},
            }})
            write_json(comparison, {"evidence_status": "PROVEN", "claim_scope": "frozen benchmark", "winner": "Teleiosis"})
            generate_showcase(status, output, comparison_path=comparison)
            text = output.read_text(encoding="utf-8")
            self.assertIn("EVIDENCE-BOUNDED LEADER", text)
            self.assertIn("<span>Teleiosis</span>", text)


if __name__ == "__main__":
    unittest.main()
