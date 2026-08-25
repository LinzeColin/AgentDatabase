from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT
from teleiosis_core.common import TeleiosisError
from teleiosis_core.regression import validate_corpus


class V5RegressionTests(unittest.TestCase):
    def test_regression_corpus(self) -> None:
        result = validate_corpus(ROOT / "fixtures/regression/teleiosis-v5-regression.jsonl")
        metadata = json.loads((ROOT / "fixtures/regression/METADATA.json").read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["records"], 8192)
        self.assertEqual(result["sha256"], metadata["sha256"])
        self.assertEqual(set(result["engines"]), {"T", "S", "P", "A"})
        self.assertEqual(len(result["splits"]), 6)
        self.assertGreater(result["hard_gate_cases"], 0)

    def test_regression_tamper_is_detected(self) -> None:
        first = (ROOT / "fixtures/regression/teleiosis-v5-regression.jsonl").read_text(encoding="utf-8").splitlines()[0]
        record = json.loads(first)
        record["expected_status"] = "BLOCKED" if record["expected_status"] != "BLOCKED" else "EXECUTED"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tampered.jsonl"
            path.write_text(json.dumps(record, ensure_ascii=False) + "\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                validate_corpus(path, expected_count=1)
            self.assertEqual(ctx.exception.code, "REGRESSION_CHECKSUM")

    def test_regression_truncation_is_detected(self) -> None:
        first = (ROOT / "fixtures/regression/teleiosis-v5-regression.jsonl").read_text(encoding="utf-8").splitlines()[0]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "short.jsonl"
            path.write_text(first + "\n", encoding="utf-8")
            with self.assertRaises(TeleiosisError) as ctx:
                validate_corpus(path)
            self.assertEqual(ctx.exception.code, "REGRESSION_COUNT")


if __name__ == "__main__":
    unittest.main()
