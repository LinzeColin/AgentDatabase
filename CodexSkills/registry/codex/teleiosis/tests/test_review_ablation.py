from __future__ import annotations

import copy
import tempfile
import unittest
from pathlib import Path

from wbi_core.review_ablation import evaluate_review_ablation, evaluate_review_ablation_file, validate_review_ablation_study


class ReviewAblationTests(unittest.TestCase):
    def study(self, evidence_class="FIXTURE"):
        reviews = []
        for index in range(1, 14):
            findings = []
            if index <= 12:
                findings.append({"issue_id": "shared", "severity": "HIGH", "supported": True})
                if index in {3, 7, 11}:
                    findings.append({"issue_id": "unique-%d" % index, "severity": "MEDIUM", "supported": True})
            reviews.append({
                "review_id": "review-%02d" % index,
                "actor_id": "actor-%02d" % index,
                "context_id": "context-%02d" % index,
                "provider_run_id": "run-%02d" % index,
                "provider": "provider-%d" % (1 + index % 2),
                "model_family": "family-%d" % (1 + index % 2),
                "verdict": "PASS",
                "findings": findings,
                "tokens": 100,
                "monetary_cost": 0.1,
                "latency_ms": 1000 + index,
                "human_minutes": 1,
                "independent_attestation_status": "PASS" if evidence_class == "REAL_REVIEW" else "DIAGNOSTIC_ONLY",
            })
        return {
            "schema_version": "1.0",
            "evidence_class": evidence_class,
            "packet_index_sha256": "a" * 64,
            "reference_findings": ["shared", "unique-3", "unique-7", "unique-11"],
            "reviews": reviews,
            "cohorts": [
                {"cohort_id": "panel-2", "review_ids": ["review-01", "review-02"]},
                {"cohort_id": "panel-6", "review_ids": ["review-%02d" % i for i in range(1, 7)]},
                {"cohort_id": "panel-12", "review_ids": ["review-%02d" % i for i in range(1, 13)]},
                {"cohort_id": "panel-12-plus-verifier", "review_ids": ["review-%02d" % i for i in range(1, 13)], "verifier_id": "review-13"},
            ],
        }

    def test_fixture_is_valid_but_never_recommends_panel(self):
        result = evaluate_review_ablation(self.study())
        self.assertEqual(result["ablation_integrity_status"], "VALID")
        self.assertEqual(result["engineering_panel_recommendation"], "NOT_PROVEN")
        self.assertTrue(result["formal_2x6_requirement_unchanged"])

    def test_real_review_can_recommend_smallest_stable_panel(self):
        value = self.study("REAL_REVIEW")
        for review in value["reviews"]:
            review["findings"] = [{"issue_id": "shared", "severity": "HIGH", "supported": True}]
        result = evaluate_review_ablation(value)
        self.assertEqual(result["ablation_integrity_status"], "VALID")
        self.assertEqual(result["engineering_panel_recommendation"], "2")

    def test_missing_distinct_verifier_rejected(self):
        value = self.study()
        value["cohorts"][-1]["verifier_id"] = "review-01"
        self.assertTrue(any("distinct verifier" in item for item in validate_review_ablation_study(value)))

    def test_duplicate_provider_run_rejected(self):
        value = self.study()
        value["reviews"][1]["provider_run_id"] = value["reviews"][0]["provider_run_id"]
        self.assertTrue(any("provider_run_id reused" in item for item in validate_review_ablation_study(value)))

    def test_partial_cost_cannot_be_recommended(self):
        value = self.study("REAL_REVIEW")
        value["reviews"][0]["tokens"] = None
        result = evaluate_review_ablation(value)
        self.assertNotEqual(result["engineering_panel_recommendation"], "2")

    def test_panel_decision_not_raw_count_distribution_controls_stability(self):
        value = self.study("REAL_REVIEW")
        for review in value["reviews"]:
            review["findings"] = [{"issue_id": "shared", "severity": "HIGH", "supported": True}]
        result = evaluate_review_ablation(value)
        self.assertEqual(result["cohorts"]["panel-2"]["panel_decision"], "PASS")
        self.assertEqual(result["cohorts"]["panel-12"]["panel_decision"], "PASS")
        self.assertEqual(result["engineering_panel_recommendation"], "2")

    def test_malformed_file_returns_structured_invalid(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "bad.json"
            path.write_text("{not-json", encoding="utf-8")
            result = evaluate_review_ablation_file(path)
        self.assertEqual(result["ablation_integrity_status"], "INVALID")
        self.assertEqual(result["engineering_panel_recommendation"], "NOT_PROVEN")


if __name__ == "__main__":
    unittest.main()
