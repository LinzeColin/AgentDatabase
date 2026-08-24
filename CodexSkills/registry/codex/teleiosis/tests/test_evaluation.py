from __future__ import annotations

import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.evaluation import (  # noqa: E402
    aggregate_results, compare_systems, evaluate_workspace, pareto_frontier, seal_eval_contract,
    validate_eval_contract, validate_result, verify_evaluation_summary,
)
from wbi_core.io import sha256_file, write_json  # noqa: E402


def contract():
    metrics = {}
    for name in ("trigger_accuracy", "task_effectiveness", "safety", "evidence_truthfulness", "cost", "latency", "installability", "compatibility", "cross_model_transfer", "maintainability", "future_adaptability"):
        metrics[name] = {"direction": "minimize" if name in {"cost", "latency"} else "maximize", "regression_tolerance": 0.0}
    return {
        "contract_id": "c", "created_before_first_change": True,
        "systems": [
            {"system_id": "b", "role": "baseline", "tree_hash": "1" * 64, "tree_hash_policy": "fixed"},
            {"system_id": "c1", "role": "candidate", "tree_hash": None, "tree_hash_policy": "result-bound"},
            {"system_id": "c2", "role": "candidate", "tree_hash": None, "tree_hash_policy": "result-bound"},
        ],
        "metrics": metrics, "hard_gates": ["genesis", "safety"],
        "datasets": [
            {"dataset_id": "d", "dataset_hash": "a" * 64, "split": "dev"},
            {"dataset_id": "h", "dataset_hash": "b" * 64, "split": "sealed-holdout"},
        ],
        "protected_task_families": ["core"],
        "judge_policy": {"modifier_cannot_be_final_judge": True, "blind_identity": True},
        "cross_model_matrix": [],
    }


def row(system_id, role, task, quality_delta=0.0, hard=True):
    metrics = {}
    for name, definition in contract()["metrics"].items():
        base = 1.0 if definition["direction"] == "maximize" else 10.0
        metrics[name] = base + quality_delta if definition["direction"] == "maximize" else base - quality_delta
    return {
        "result_id": "%s-%s" % (system_id, task), "task_id": task, "task_family": "core",
        "dataset_id": "d", "dataset_hash": "a" * 64, "split": "dev",
        "system_id": system_id, "system_role": role, "system_tree_hash": "1" * 64 if role == "baseline" else ("2" * 64 if system_id == "c1" else "3" * 64),
        "trial_id": "1", "model": "m", "runtime": "r",
        "metrics": metrics, "hard_gates": {"genesis": hard, "safety": hard},
    }


class EvaluationTests(unittest.TestCase):
    def test_holdout_content_cannot_enter_contract(self):
        value = contract()
        value["datasets"][1]["prompts"] = ["secret"]
        self.assertTrue(any("leaked" in error for error in validate_eval_contract(value)))

    def test_candidate_hard_failure_cannot_be_compensated(self):
        rows = [row("b", "baseline", "t1"), row("c1", "candidate", "t1", quality_delta=10.0, hard=False)]
        aggregates = aggregate_results(rows, contract())
        result = compare_systems(aggregates, contract())
        self.assertEqual(result["status"], "FAIL")

    def test_candidate_can_fix_a_baseline_hard_gate_failure(self):
        rows = [
            row("b", "baseline", "t1", hard=False),
            row("c1", "candidate", "t1", quality_delta=0.1, hard=True),
        ]
        aggregates = aggregate_results(rows, contract())
        result = compare_systems(aggregates, contract())
        self.assertEqual(result["status"], "PASS", result)
        self.assertTrue(result["baseline_hard_gate_failures"])
        self.assertEqual(result["candidates"]["c1"]["status"], "PASS")

    def test_protected_family_regression_is_not_hidden_by_average(self):
        rows = [row("b", "baseline", "t1"), row("c1", "candidate", "t1", quality_delta=-0.1)]
        aggregates = aggregate_results(rows, contract())
        result = compare_systems(aggregates, contract())
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["candidates"]["c1"]["protected_family_regressions"])

    def test_result_must_bind_contract_system_dataset_and_tree_hash(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            raw = ws / "raw.json"
            raw.write_text("{}", encoding="utf-8")
            value = row("c1", "candidate", "t1", quality_delta=0.1)
            value.update({
                "raw_result_path": "raw.json", "raw_result_sha256": sha256_file(raw),
                "process_trace_path": "trace.json", "process_trace_sha256": "",
                "actor_id": "evaluator", "started_at": "2026-07-26T00:00:00Z", "finished_at": "2026-07-26T00:00:01Z",
            })
            trace = ws / "trace.json"
            trace.write_text("{}", encoding="utf-8")
            value["process_trace_sha256"] = sha256_file(trace)
            self.assertEqual(validate_result(value, contract(), ws), [])
            value["system_id"] = "not-in-contract"
            self.assertTrue(any("not frozen" in item for item in validate_result(value, contract(), ws)))

    def test_one_candidate_cannot_mix_multiple_tree_hashes_across_splits(self):
        rows = [row("b", "baseline", "t1"), row("c1", "candidate", "t1", quality_delta=0.1)]
        second = row("c1", "candidate", "t2", quality_delta=0.1)
        second["system_tree_hash"] = "9" * 64
        rows.append(second)
        result = compare_systems(aggregate_results(rows, contract()), contract())
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("one exact tree hash", " ".join(result["candidates"]["c1"]["errors"]))


    def _formal_contract(self):
        value = contract()
        value["systems"] = value["systems"][:2]
        return value

    def _materialize(self, workspace, system_id, role, dataset, model="m", quality=0.0):
        task = "%s-%s" % (dataset["dataset_id"], model)
        value = row(system_id, role, task, quality_delta=quality)
        value.update({
            "result_id": "%s-%s" % (system_id, task),
            "dataset_id": dataset["dataset_id"], "dataset_hash": dataset["dataset_hash"], "split": dataset["split"],
            "model": model, "runtime": "runtime-1", "trial_id": "trial-1",
            "raw_result_path": "evidence/evals/raw/items/%s.json" % ("%s-%s" % (system_id, task)),
            "process_trace_path": "evidence/evals/raw/traces/%s.json" % ("%s-%s" % (system_id, task)),
            "actor_id": "evaluator", "started_at": "2026-07-26T00:00:00Z", "finished_at": "2026-07-26T00:00:01Z",
        })
        raw = workspace / value["raw_result_path"]
        trace = workspace / value["process_trace_path"]
        raw.parent.mkdir(parents=True, exist_ok=True)
        trace.parent.mkdir(parents=True, exist_ok=True)
        write_json(raw, {"result_id": value["result_id"], "outcome": "recorded"})
        write_json(trace, {"result_id": value["result_id"], "steps": ["invoke", "observe", "score"]})
        value["raw_result_sha256"] = sha256_file(raw)
        value["process_trace_sha256"] = sha256_file(trace)
        return value

    def _seal_and_write(self, workspace, value, rows):
        workspace.mkdir(parents=True, exist_ok=True)
        write_json(workspace / "state.json", {"changes_recorded": 0})
        source = workspace / "contract-source.json"
        write_json(source, value)
        seal = seal_eval_contract(workspace, source, "contract-owner")
        self.assertEqual(seal.get("status"), "SEALED", seal)
        results = workspace / "evidence/evals/raw/results.jsonl"
        results.parent.mkdir(parents=True, exist_ok=True)
        results.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in rows), encoding="utf-8")

    def test_evaluation_requires_identical_cells_and_models_per_system(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            value = self._formal_contract()
            value["cross_model_matrix"] = ["m1", "m2"]
            rows = []
            for dataset in value["datasets"]:
                rows.append(self._materialize(ws, "b", "baseline", dataset, "m1"))
                rows.append(self._materialize(ws, "b", "baseline", dataset, "m2"))
                rows.append(self._materialize(ws, "c1", "candidate", dataset, "m1", quality=0.1))
            self._seal_and_write(ws, value, rows)
            result = evaluate_workspace(ws)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertTrue(any("required model" in item or "comparison cells" in item for item in result["errors"]))

    def test_forged_summary_is_detected_by_recomputation(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            value = self._formal_contract()
            rows = []
            for dataset in value["datasets"]:
                rows.append(self._materialize(ws, "b", "baseline", dataset))
                rows.append(self._materialize(ws, "c1", "candidate", dataset, quality=0.1))
            self._seal_and_write(ws, value, rows)
            summary = evaluate_workspace(ws)
            self.assertEqual(summary["status"], "PASS", summary)
            self.assertEqual(verify_evaluation_summary(ws), [])
            summary_path = ws / "evidence/evals/summary/evaluation-summary.json"
            forged = json.loads(summary_path.read_text())
            forged["pareto_frontier"] = []
            write_json(summary_path, forged)
            self.assertTrue(any("differs from recomputed" in item for item in verify_evaluation_summary(ws)))

    def test_trace_and_timestamp_are_content_bound(self):
        with tempfile.TemporaryDirectory() as td:
            ws = Path(td)
            value = self._formal_contract()
            result = self._materialize(ws, "c1", "candidate", value["datasets"][0], quality=0.1)
            self.assertEqual(validate_result(result, value, ws), [])
            trace = ws / result["process_trace_path"]
            write_json(trace, {"tampered": True})
            errors = validate_result(result, value, ws)
            self.assertTrue(any("process trace hash mismatch" in item for item in errors))
            result["process_trace_sha256"] = sha256_file(trace)
            result["finished_at"] = "2026-07-25T23:59:59Z"
            self.assertTrue(any("precedes" in item for item in validate_result(result, value, ws)))

    def test_pareto_frontier_avoids_single_weighted_score(self):
        c = contract()
        rows = [row("b", "baseline", "t"), row("c1", "candidate", "t", quality_delta=0.1), row("c2", "candidate", "t", quality_delta=0.2)]
        aggregates = aggregate_results(rows, c)
        frontier = pareto_frontier(aggregates, c, ["c1", "c2"])
        self.assertEqual(frontier, ["c2"])


if __name__ == "__main__":
    unittest.main()
