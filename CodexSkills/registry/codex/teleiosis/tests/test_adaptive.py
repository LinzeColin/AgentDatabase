from __future__ import annotations

from pathlib import Path
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.adaptive import build_adaptive_plan


def diagnostic(target_class: str, risk: str = "low", status: str = "PASS"):
    return {
        "diagnostic_status": status,
        "blockers": ["blocked"] if status == "BLOCKED" else [],
        "classification": {
            "target_class": target_class,
            "risk_level": risk,
            "suggested_verification_level": "release",
            "evidence_completeness": "COMPLETE",
        },
        "target": {"path": "/tmp/target", "tree_sha256": "a" * 64, "file_count": 25},
    }


class AdaptivePlanTests(unittest.TestCase):
    def test_text_profile_prioritizes_trigger_and_clarity(self):
        result = build_adaptive_plan(diagnostic("text-and-reasoning"), run_mode="engineering")
        self.assertEqual(result["plan_status"], "READY")
        self.assertEqual(result["candidate_portfolio"][0]["candidate_id"], "trigger-and-clarity")
        self.assertIn("trigger_precision", result["optimization_objectives"])

    def test_high_risk_profile_is_deep_and_omits_clean_slate_default(self):
        result = build_adaptive_plan(diagnostic("high-risk-or-side-effecting", "high"), run_mode="formal")
        self.assertEqual(result["profile"]["verification_level"], "deep")
        self.assertNotIn("clean-slate", [item["candidate_id"] for item in result["candidate_portfolio"]])
        self.assertIn("external-signed-2x6-plus-distinct-read-only-verifier", result["required_gates"])

    def test_blocked_diagnostic_blocks_plan(self):
        result = build_adaptive_plan(diagnostic("text-and-reasoning", status="BLOCKED"), run_mode="engineering")
        self.assertEqual(result["plan_status"], "BLOCKED")
        self.assertEqual(result["blockers"], ["blocked"])

    def test_diagnostic_mode_has_zero_mutation_budget(self):
        result = build_adaptive_plan(diagnostic("tool-execution"), run_mode="diagnostic")
        self.assertEqual(result["budget"]["max_iteration_rounds"], 0)
        self.assertEqual(result["budget"]["max_changed_lines_per_candidate"], 0)


if __name__ == "__main__":
    unittest.main()
