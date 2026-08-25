from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.benchmark import evaluate_benchmark, seal_benchmark_contract, validate_benchmark_contract
from wbi_core.io import sha256_file, write_json

HASH_A = "a" * 64
HASH_B = "b" * 64
TRACKS = ["A_OPTIMIZATION", "B_PRODUCTIZATION", "C_ASSURANCE"]
SPLITS = ["dev", "validation", "sealed_holdout", "adversarial", "protected"]
KINDS = ["text-reasoning", "text-reasoning", "tool-artifact", "tool-artifact", "high-risk-reversible", "high-risk-reversible"]


def contract(root: Path, production=True):
    targets = []
    for index, kind in enumerate(KINDS, 1):
        datasets = {}
        for split in SPLITS:
            datasets[split] = {
                "dataset_id": "t%d-%s" % (index, split),
                "dataset_hash": ("%x" % (index % 16)) * 64,
                "item_count": 20 if split == "sealed_holdout" else 3,
            }
            if split == "sealed_holdout":
                datasets[split]["external_pointer"] = str(root / "holdout" / ("t%d.jsonl" % index))
        targets.append({"target_id": "t%d" % index, "target_type": kind, "baseline_tree_hash": HASH_A, "datasets": datasets})
    return {
        "schema_version": "1.0", "benchmark_id": "bench-1", "valid_as_of": "2026-07-26", "created_at": "2026-07-26T00:00:00Z",
        "production": production, "evidence_class": "REAL_TASK", "minimum_targets": 6 if production else 1, "tracks": TRACKS,
        "systems": [
            {"system_id": "baseline", "role": "baseline", "tree_hash": HASH_A},
            {"system_id": "candidate", "role": "candidate", "tree_hash": HASH_B},
        ],
        "targets": targets if production else targets[:1],
        "execution": {"trials_per_cell": 3 if production else 1, "runtime": "fixture", "model": "deterministic", "tool_permissions": [], "context_window": 1000, "sampling": {"temperature": 0}},
        "budget": {"max_model_tokens": 1000000, "max_calls": 100000, "max_wall_seconds": 100000, "max_human_minutes": 100000, "max_monetary_cost": 100000},
        "judge_oracle_id": "oracle-v1", "normalization_policy": "frozen", "blind_randomization_policy": "frozen",
        "acceptance": {"minimum_task_success_delta": 0.01, "maximum_protected_regression": 0.0, "hard_gate_compensation_allowed": False},
        "candidate_can_read_holdout": False,
    }


def result(workspace: Path, sid: str, tid: str, track: str, split: str, trial: int, success: float):
    raw = workspace / "raw" / ("%s-%s-%s-%s-%d.json" % (sid, tid, track, split, trial))
    trace = workspace / "trace" / ("%s-%s-%s-%s-%d.json" % (sid, tid, track, split, trial))
    write_json(raw, {"success": success})
    write_json(trace, {"steps": ["fixture"]})
    return {
        "result_id": raw.stem,
        "system_id": sid, "system_tree_hash": HASH_A if sid == "baseline" else HASH_B,
        "target_id": tid, "target_tree_hash": HASH_A, "track": track, "split": split, "trial": trial,
        "runtime": "fixture", "model": "deterministic", "started_at": "2026-07-26T00:00:00Z", "finished_at": "2026-07-26T00:00:01Z",
        "metrics": {
            "trigger_precision": success, "trigger_recall": success, "task_success": success,
            "safety_success": 1.0, "truthfulness": 1.0, "protected_task_success": 1.0,
            "latency_ms": 10, "model_tokens": 1, "human_minutes": 0, "evidence_completeness": 1.0,
        },
        "hard_gates": {"safety": "PASS", "authority": "PASS"},
        "budget": {
            "token_evidence_status": "MEASURED", "model_tokens": 1,
            "calls": 1, "wall_seconds": 0.01, "human_minutes": 0,
            "monetary_cost_status": "MEASURED", "monetary_cost": 0
        },
        "raw_result_path": raw.relative_to(workspace).as_posix(), "raw_result_sha256": sha256_file(raw),
        "process_trace_path": trace.relative_to(workspace).as_posix(), "process_trace_sha256": sha256_file(trace),
    }


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "holdout").mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_valid_production_contract(self):
        self.assertEqual(validate_benchmark_contract(contract(self.root)), [])

    def test_requires_six_targets_and_type_balance(self):
        value = contract(self.root); value["targets"] = value["targets"][:5]
        errors = validate_benchmark_contract(value)
        self.assertTrue(any("at least 6 targets" in item for item in errors))
        self.assertTrue(any("two high-risk" in item for item in errors))

    def test_holdout_content_leak_rejected(self):
        value = contract(self.root); value["targets"][0]["datasets"]["sealed_holdout"]["items"] = ["secret"]
        self.assertTrue(any("leaks content" in item for item in validate_benchmark_contract(value)))

    def test_minimum_three_trials(self):
        value = contract(self.root); value["execution"]["trials_per_cell"] = 1
        self.assertTrue(any("three stochastic trials" in item for item in validate_benchmark_contract(value)))

    def test_hard_gate_compensation_forbidden(self):
        value = contract(self.root); value["acceptance"]["hard_gate_compensation_allowed"] = True
        self.assertTrue(any("compensation" in item for item in validate_benchmark_contract(value)))

    def test_seal_is_immutable(self):
        ws = self.root / "ws"; ws.mkdir()
        source = self.root / "contract.json"; write_json(source, contract(self.root))
        first = seal_benchmark_contract(ws, source, "actor")
        self.assertEqual(first["seal_status"], "SEALED")
        changed = contract(self.root); changed["benchmark_id"] = "different"; write_json(source, changed)
        second = seal_benchmark_contract(ws, source, "actor")
        self.assertEqual(second["seal_status"], "FAIL")

    def _write_complete(self, workspace: Path, candidate_success=0.8, baseline_success=0.6, hard_fail=False):
        value = contract(self.root, production=False)
        write_json(self.root / "contract.json", value)
        self.assertEqual(seal_benchmark_contract(workspace, self.root / "contract.json", "actor")["seal_status"], "SEALED")
        rows = []
        for sid, success in (("baseline", baseline_success), ("candidate", candidate_success)):
            for track in TRACKS:
                for split in ("sealed_holdout", "adversarial", "protected"):
                    row = result(workspace, sid, "t1", track, split, 1, success)
                    if hard_fail and sid == "candidate" and split == "sealed_holdout":
                        row["hard_gates"]["safety"] = "FAIL"
                    rows.append(row)
        path = workspace / "results.jsonl"
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        return path

    def test_complete_equal_budget_fixture_supports_outcome(self):
        ws = self.root / "ws"; ws.mkdir()
        summary = evaluate_benchmark(ws, self._write_complete(ws))
        self.assertEqual(summary["benchmark_integrity_status"], "VALID")
        self.assertEqual(summary["outcome_status"], "SUPPORTED")

    def test_fixture_can_validate_runner_but_not_support_market_outcome(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        cpath = ws / "control/contracts/benchmark-contract.json"
        cpath.chmod(0o644)
        value = json.loads(cpath.read_text(encoding="utf-8")); value["evidence_class"] = "FIXTURE"
        write_json(cpath, value)
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "VALID")
        self.assertEqual(summary["outcome_status"], "NOT_PROVEN")
        self.assertIsNone(summary["selected_candidate"])
        self.assertEqual(summary["diagnostic_selected_candidate"], "candidate")
        self.assertFalse(summary["outcome_claim_allowed"])
        self.assertTrue(any("fixture" in item for item in summary["claim_reasons"]))

    def test_candidate_hard_failure_cannot_be_compensated(self):
        ws = self.root / "ws"; ws.mkdir()
        summary = evaluate_benchmark(ws, self._write_complete(ws, candidate_success=1.0, baseline_success=0.1, hard_fail=True))
        self.assertEqual(summary["outcome_status"], "NOT_PROVEN")

    def test_incomplete_matrix_not_supported(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        rows = path.read_text(encoding="utf-8").splitlines()[:-1]
        path.write_text("\n".join(rows) + "\n", encoding="utf-8")
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "INCOMPLETE")
        self.assertNotEqual(summary["outcome_status"], "SUPPORTED")

    def test_result_tree_hash_drift_rejected(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["system_tree_hash"] = "0" * 64
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "INVALID")

    def test_budget_violation_invalidates_claim(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        cpath = ws / "control/contracts/benchmark-contract.json"
        cpath.chmod(0o644)
        value = json.loads(cpath.read_text(encoding="utf-8")); value["budget"]["max_calls"] = 1
        write_json(cpath, value)
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "INVALID")
        self.assertTrue(summary["budget_violations"])

    def test_failed_trials_are_not_deleted(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        rows = path.read_text(encoding="utf-8").splitlines()
        self.assertEqual(len(rows), 18)
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(len(rows), 18)
        self.assertEqual(summary["benchmark_integrity_status"], "VALID")


    def test_unknown_monetary_cost_is_not_reported_as_zero_total(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        cpath = ws / "control/contracts/benchmark-contract.json"
        cpath.chmod(0o644)
        value = json.loads(cpath.read_text(encoding="utf-8")); value["budget"]["max_monetary_cost"] = None
        write_json(cpath, value)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["budget"]["monetary_cost_status"] = "UNKNOWN"
        rows[0]["budget"]["monetary_cost"] = None
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "VALID")
        budget = summary["aggregates"]["baseline"]["budget"]
        self.assertIsNone(budget["monetary_cost"])
        self.assertEqual(budget["known_monetary_cost"], 0.0)
        self.assertEqual(budget["unknown_monetary_cost_results"], 1)



    def test_unknown_token_usage_is_not_reported_as_zero_total(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        cpath = ws / "control/contracts/benchmark-contract.json"
        cpath.chmod(0o644)
        value = json.loads(cpath.read_text(encoding="utf-8")); value["budget"]["max_model_tokens"] = None
        write_json(cpath, value)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["budget"]["token_evidence_status"] = "UNKNOWN"
        rows[0]["budget"]["model_tokens"] = None
        rows[0]["metrics"]["model_tokens"] = None
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "INCOMPLETE")
        self.assertEqual(summary["outcome_status"], "NOT_PROVEN")
        self.assertIsNone(summary["selected_candidate"])
        budget = summary["aggregates"]["baseline"]["budget"]
        self.assertIsNone(budget["model_tokens"])
        self.assertGreater(budget["known_model_tokens"], 0)
        self.assertEqual(budget["unknown_token_results"], 1)
        self.assertIsNone(summary["aggregates"]["baseline"]["model_tokens"])

    def test_unknown_token_usage_under_finite_budget_invalidates_claim(self):
        ws = self.root / "ws"; ws.mkdir()
        path = self._write_complete(ws)
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
        rows[0]["budget"]["token_evidence_status"] = "UNKNOWN"
        rows[0]["budget"]["model_tokens"] = None
        rows[0]["metrics"]["model_tokens"] = None
        path.write_text("\n".join(json.dumps(row) for row in rows) + "\n", encoding="utf-8")
        summary = evaluate_benchmark(ws, path)
        self.assertEqual(summary["benchmark_integrity_status"], "INVALID")
        self.assertTrue(any("unknown model_tokens" in item for item in summary["budget_violations"]))



if __name__ == "__main__":
    unittest.main()
