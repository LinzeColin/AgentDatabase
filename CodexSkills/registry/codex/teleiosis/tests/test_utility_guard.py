from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.utility_guard import evaluate_utility_contract, evaluate_utility_file  # noqa: E402


class UtilityGuardTests(unittest.TestCase):
    def base_contract(self):
        return {
            "schema_version": "1.0", "minimum_material_gain": 0.05,
            "metrics": [
                {"metric_id": "quality", "direction": "higher", "baseline": 10, "candidate": 11, "hard": True},
                {"metric_id": "operator_steps", "direction": "lower", "baseline": 5, "candidate": 4, "hard": False},
            ],
            "protected_checks": [{"check_id": "genesis", "baseline_pass": True, "candidate_pass": True}],
        }

    def test_keeps_candidate_only_with_material_gain_and_no_hard_regression(self):
        result = evaluate_utility_contract(self.base_contract())
        self.assertEqual(result["decision"], "KEEP_CANDIDATE")
        self.assertEqual(result["hard_regression_count"], 0)
        self.assertGreater(result["material_gain_count"], 0)

    def test_reverts_hard_metric_regression_even_when_soft_metric_improves(self):
        contract = self.base_contract()
        contract["metrics"][0]["candidate"] = 9
        contract["metrics"][1]["candidate"] = 1
        result = evaluate_utility_contract(contract)
        self.assertEqual(result["decision"], "REVERT")
        self.assertGreater(result["hard_regression_count"], 0)

    def test_reverts_protected_check_regression(self):
        contract = self.base_contract()
        contract["protected_checks"][0]["candidate_pass"] = False
        self.assertEqual(evaluate_utility_contract(contract)["decision"], "REVERT")

    def test_no_material_gain_falls_back_to_baseline(self):
        contract = self.base_contract()
        contract["metrics"][0]["candidate"] = 10.01
        contract["metrics"][1]["candidate"] = 5
        result = evaluate_utility_contract(contract)
        self.assertEqual(result["decision"], "KEEP_BASELINE")

    def test_unknown_or_non_finite_values_are_not_silently_zeroed(self):
        for value in (None, True, float("inf"), float("nan")):
            contract = self.base_contract()
            contract["metrics"][0]["candidate"] = value
            with self.assertRaises(ValueError):
                evaluate_utility_contract(contract)

    def test_file_evaluation_binds_contract_hash(self):
        with tempfile.TemporaryDirectory() as td:
            source = Path(td) / "contract.json"
            source.write_text(json.dumps(self.base_contract()), encoding="utf-8")
            output = Path(td) / "result.json"
            result = evaluate_utility_file(source, output)
            self.assertTrue(output.is_file())
            self.assertEqual(len(result["contract_sha256"]), 64)
            self.assertEqual(len(result["result_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
