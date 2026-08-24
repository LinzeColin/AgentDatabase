from __future__ import annotations

from pathlib import Path
import json
import tempfile
import unittest
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from wbi_core.io import load_json, write_json
from wbi_core.strategy import inspect_strategy_memory, update_strategy_memory


class StrategyMemoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.workspace = Path(self.tmp.name) / "workspace"
        (self.workspace / "evidence").mkdir(parents=True)
        (self.workspace / "evidence/result.json").write_text("{}\n", encoding="utf-8")
        self.counter = 0

    def tearDown(self):
        self.tmp.cleanup()

    def add(self, mechanism: str, decision: str, scope: str = "SKILL.md", change_ratio: float = 0.1):
        self.counter += 1
        record = Path(self.tmp.name) / ("record-%d.json" % self.counter)
        write_json(record, {
            "candidate_id": "candidate-%d" % self.counter,
            "scope": scope,
            "mechanism": mechanism,
            "decision": decision,
            "change_ratio": change_ratio,
            "metric_delta": {},
            "failure_tags": ["no_gain"] if decision != "KEEP" else [],
            "evidence_paths": ["evidence/result.json"],
        })
        return update_strategy_memory(self.workspace, record)

    def test_repeated_failed_mechanism_enters_rejected_buffer(self):
        self.add("wording", "REVERT")
        result = self.add("wording", "NO_CHANGE")
        self.assertIn("wording", result["recommendation"]["suppressed_mechanisms"])
        inspected = inspect_strategy_memory(self.workspace)
        self.assertEqual(inspected["status"], "PASS")
        self.assertEqual(inspected["event_count"], 2)

    def test_three_cross_mechanism_failures_saturate(self):
        self.add("wording", "REVERT")
        self.add("structure", "NO_CHANGE")
        result = self.add("architecture", "REVERT")
        self.assertEqual(result["recommendation"]["strategy_status"], "SATURATED")
        self.assertEqual(result["recommendation"]["recommended_mechanism"], "REHEAT_REQUIRED")

    def test_oscillation_is_detected(self):
        self.add("a", "KEEP", scope="same")
        self.add("b", "KEEP", scope="same")
        self.add("a", "KEEP", scope="same")
        result = self.add("b", "KEEP", scope="same")
        self.assertTrue(result["recommendation"]["oscillation_detected"])
        self.assertEqual(result["recommendation"]["recommended_mechanism"], "freeze-scope-and-reframe-objective")

    def test_tamper_breaks_hash_chain(self):
        self.add("wording", "KEEP")
        path = self.workspace / "control/strategy-memory.json"
        memory = load_json(path)
        memory["events"][0]["mechanism"] = "tampered"
        write_json(path, memory)
        inspected = inspect_strategy_memory(self.workspace)
        self.assertEqual(inspected["status"], "FAIL")
        self.assertTrue(any("hash mismatch" in item for item in inspected["errors"]))


if __name__ == "__main__":
    unittest.main()
