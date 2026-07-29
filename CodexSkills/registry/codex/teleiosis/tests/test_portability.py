from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from wbi_core.io import sha256_file, write_json
from wbi_core.portability import evaluate_portability, evaluate_portability_file, validate_portability_contract


class PortabilityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.workspace = self.root / "workspace"; self.workspace.mkdir()
        self.contract_path = self.root / "contract.json"
        self.results_path = self.root / "results.jsonl"

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self, evidence_class="FIXTURE"):
        return {
            "schema_version": "1.0",
            "evidence_class": evidence_class,
            "candidate_tree_hash": "a" * 64,
            "required_runtimes": ["runtime-a", "runtime-b"],
            "required_model_families": ["model-x", "model-y"],
            "no_subagent_runtime": "runtime-a",
        }

    def write_matrix(self, contract, omit=None, mutate=None):
        rows = []
        for runtime in contract["required_runtimes"]:
            for model in contract["required_model_families"]:
                if omit == (runtime, model):
                    continue
                evidence = self.workspace / (runtime + "-" + model + ".json")
                write_json(evidence, {"runtime": runtime, "model": model, "result": "PASS"})
                row = {
                    "runtime": runtime,
                    "model_family": model,
                    "candidate_tree_hash": contract["candidate_tree_hash"],
                    "status": "PASS",
                    "formal_promotion_status": "BLOCKED" if runtime == contract["no_subagent_runtime"] else "PASS",
                    "metrics": {
                        "trigger_success": 1.0,
                        "task_success": 1.0,
                        "install_pass": True,
                        "rollback_pass": True,
                        "truthful_blocked_behavior": runtime == contract["no_subagent_runtime"],
                    },
                    "raw_evidence_path": evidence.relative_to(self.workspace).as_posix(),
                    "raw_evidence_sha256": sha256_file(evidence),
                }
                if mutate:
                    mutate(row)
                rows.append(row)
        self.results_path.write_text("\n".join(json.dumps(row, sort_keys=True) for row in rows) + "\n", encoding="utf-8")

    def test_fixture_matrix_valid_but_never_supports_platform_neutral_claim(self):
        contract = self.contract(); write_json(self.contract_path, contract); self.write_matrix(contract)
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "VALID")
        self.assertFalse(result["platform_neutral_claim_supported"])

    def test_real_complete_matrix_can_support_scoped_claim(self):
        contract = self.contract("REAL_RUNTIME"); write_json(self.contract_path, contract); self.write_matrix(contract)
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertTrue(result["platform_neutral_claim_supported"])

    def test_missing_matrix_cell_is_incomplete(self):
        contract = self.contract(); write_json(self.contract_path, contract); self.write_matrix(contract, omit=("runtime-b", "model-y"))
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "INCOMPLETE")
        self.assertFalse(result["platform_neutral_claim_supported"])

    def test_wrong_candidate_tree_fails(self):
        contract = self.contract(); write_json(self.contract_path, contract)
        self.write_matrix(contract, mutate=lambda row: row.update({"candidate_tree_hash": "b" * 64}))
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "INVALID")

    def test_no_subagent_runtime_must_block_formal_promotion(self):
        contract = self.contract(); write_json(self.contract_path, contract)
        def mutate(row):
            if row["runtime"] == "runtime-a":
                row["formal_promotion_status"] = "PASS"
        self.write_matrix(contract, mutate=mutate)
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "INVALID")

    def test_unsafe_raw_evidence_path_rejected(self):
        contract = self.contract(); write_json(self.contract_path, contract)
        self.write_matrix(contract, mutate=lambda row: row.update({"raw_evidence_path": "../outside.json"}))
        result = evaluate_portability(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "INVALID")

    def test_contract_requires_two_runtime_and_model_families(self):
        contract = self.contract(); contract["required_runtimes"] = ["one"]
        self.assertTrue(any("at least two named runtimes" in item for item in validate_portability_contract(contract)))

    def test_malformed_results_return_structured_invalid(self):
        contract = self.contract(); write_json(self.contract_path, contract)
        self.results_path.write_text("{not-json\n", encoding="utf-8")
        result = evaluate_portability_file(self.workspace, self.contract_path, self.results_path)
        self.assertEqual(result["portability_integrity_status"], "INVALID")
        self.assertFalse(result["platform_neutral_claim_supported"])


if __name__ == "__main__":
    unittest.main()
