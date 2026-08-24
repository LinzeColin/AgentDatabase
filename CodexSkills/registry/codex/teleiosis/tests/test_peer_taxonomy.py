from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.competitors import qualify_peer, select_peers  # noqa: E402
from wbi_core.peer_taxonomy import audit_file, audit_records, classify_comparison_scope  # noqa: E402


class PeerTaxonomyTests(unittest.TestCase):
    def test_exact_user_links_are_engineering_analogies_not_market_peers(self):
        rows = json.loads((ROOT / "templates/peer-audit-records.json").read_text(encoding="utf-8"))
        result = audit_records(rows)
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["engineering_analogy_count"], 2)
        self.assertIn("github:Curzibn/Luban", result["engineering_analogy_ids"])
        self.assertIn("github:EasyDarwin/EasyDarwin", result["engineering_analogy_ids"])
        self.assertNotIn("github:Curzibn/Luban", result["market_scope_candidate_ids"])
        self.assertEqual(result["production_qualified_peer_count"], 0)
        self.assertEqual(result["market_peer_ids"], [])

    def test_non_skill_engineered_repository_defaults_to_analogy(self):
        scope, confidence, evidence = classify_comparison_scope(
            {"slug": "org/media-server", "description": "cross-platform streaming server"},
            {"signals": {"has_skill": False, "has_readme": True, "has_tests": True, "has_scripts": True}},
        )
        self.assertEqual(scope, "engineering-analogy")
        self.assertGreater(confidence, 0.5)
        self.assertTrue(evidence)

    def test_skill_optimizer_is_direct_competitor(self):
        scope, _, _ = classify_comparison_scope(
            {"slug": "org/darwin-skill", "description": "Agent Skill optimizer and evolution"},
            {"signals": {"has_skill": True}},
        )
        self.assertEqual(scope, "direct-competitor")

    def test_engineering_analogy_is_rejected_by_peer_gate_even_with_live_evidence(self):
        row = {
            "peer_id": "analogy", "source_url": "https://example.com/a", "category": "indirect",
            "comparison_scope": "engineering-analogy", "evidence_mode": "product-live",
            "captured_at": "2026-07-26T00:00:00+00:00", "license_status": "terms-observed",
            "observed_artifacts": ["output"], "reproduction_or_observation": ["open", "run"],
            "third_party_code_executed": False,
        }
        passed, reasons = qualify_peer(row)
        self.assertFalse(passed)
        self.assertIn("cannot satisfy", " ".join(reasons))

    def test_selection_ignores_analogies_and_requires_five_real_market_peers(self):
        rows = []
        categories = ["direct", "direct", "indirect", "craft"]
        scopes = ["direct-competitor", "direct-competitor", "method-reference", "adjacent-competitor"]
        for index, (category, scope) in enumerate(zip(categories, scopes)):
            rows.append({
                "peer_id": "peer-%d" % index, "source_url": "https://example.com/%d" % index,
                "category": category, "comparison_scope": scope, "evidence_mode": "product-live",
                "captured_at": "2026-07-26T00:00:00+00:00", "license_status": "terms-observed",
                "observed_artifacts": ["output"], "reproduction_or_observation": ["observe"],
                "third_party_code_executed": False, "relevance_score": 1.0 - index * 0.01,
            })
        rows.append({
            "peer_id": "analogy", "source_url": "https://example.com/analogy", "category": "indirect",
            "comparison_scope": "engineering-analogy", "evidence_mode": "product-live",
            "captured_at": "2026-07-26T00:00:00+00:00", "license_status": "terms-observed",
            "observed_artifacts": ["output"], "reproduction_or_observation": ["observe"],
            "third_party_code_executed": False, "relevance_score": 0.99,
        })
        result = select_peers(rows, minimum=5, min_remote_github=0)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["eligible_count"], 4)

    def test_audit_file_supports_jsonl_and_rejects_duplicate_identity(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "peers.jsonl"
            source.write_text(
                json.dumps({"peer_id": "x", "comparison_scope": "direct-competitor"}) + "\n" +
                json.dumps({"peer_id": "x", "comparison_scope": "engineering-analogy"}) + "\n",
                encoding="utf-8",
            )
            output = Path(td) / "audit.json"
            result = audit_file(source, output)
            self.assertEqual(result["status"], "FAIL")
            self.assertTrue(output.is_file())
            self.assertIn("duplicate", " ".join(result["errors"]))


if __name__ == "__main__":
    unittest.main()
