from __future__ import annotations

import csv
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JSON_PATH = ROOT / "research" / "comparison_matrix.json"
CSV_PATH = ROOT / "research" / "comparison_matrix.csv"
SCORING_PATH = ROOT / "research" / "scoring_method.json"


class ResearchMatrixTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.matrix = json.loads(JSON_PATH.read_text(encoding="utf-8"))
        cls.method = json.loads(SCORING_PATH.read_text(encoding="utf-8"))
        with CSV_PATH.open(encoding="utf-8-sig", newline="") as handle:
            cls.csv_rows = list(csv.DictReader(handle))

    def test_goal_fit_weights_sum_to_100(self):
        weights = self.method["goal_fit_weights_percent"]
        self.assertEqual(sum(weights.values()), 100)
        self.assertEqual(set(weights), set(self.matrix["method"]["goal_fit_weights_percent"]))

    def test_weighted_scores_recompute(self):
        weights = self.matrix["method"]["goal_fit_weights_percent"]
        for row in self.matrix["candidates"]:
            calculated = sum(float(row[name]) * weight for name, weight in weights.items()) / 100
            self.assertAlmostEqual(calculated, row["weighted_goal_fit_percent"], places=1, msg=row["candidate"])
            self.assertTrue(0 <= row["evidence_confidence_percent"] <= 100)
            self.assertTrue(row["license_note"].strip())

    def test_json_and_csv_match_and_are_sorted(self):
        json_pairs = [(row["candidate"], row["weighted_goal_fit_percent"]) for row in self.matrix["candidates"]]
        csv_pairs = [(row["candidate"], float(row["weighted_goal_fit_percent"])) for row in self.csv_rows]
        self.assertEqual(json_pairs, csv_pairs)
        scores = [score for _, score in json_pairs]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_integrated_candidate_keeps_external_evidence_separate(self):
        candidate = self.matrix["candidates"][0]
        self.assertEqual(candidate["candidate"], "Video Prompt Compiler v0.0.0.2")
        self.assertEqual(candidate["native_model_validation_status"], "NOT_RUN")
        self.assertEqual(candidate["independent_acceptance_status"], "NOT_RUN")
        self.assertLess(candidate["evidence_confidence_percent"], candidate["weighted_goal_fit_percent"])


if __name__ == "__main__":
    unittest.main()
