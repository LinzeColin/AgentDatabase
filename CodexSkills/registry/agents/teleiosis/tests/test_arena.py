from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import ROOT, load_json, write_json
from teleiosis_core.arena import execute_command_adapter, freeze_spec, score_arena, validate_spec
from teleiosis_core.common import TeleiosisError


def load_rows() -> list[dict]:
    return [json.loads(line) for line in (ROOT / "templates/arena-observations.example.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]


def write_rows(path: Path, rows: list[dict]) -> None:
    path.write_text("".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


class ArenaTests(unittest.TestCase):
    def prepare(self, base: Path, mutate_spec=None, mutate_rows=None) -> tuple[Path, Path, Path]:
        spec = load_json("templates/arena-spec.example.json")
        rows = load_rows()
        if mutate_spec:
            mutate_spec(spec)
        if mutate_rows:
            mutate_rows(rows)
        raw = base / "arena.json"
        frozen = base / "arena.frozen.json"
        observations = base / "observations.jsonl"
        write_json(raw, spec)
        freeze_spec(raw, frozen, "2026-08-02T00:00:00Z")
        write_rows(observations, rows)
        return raw, frozen, observations

    def test_example_development_candidate_improves(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base)
            output = base / "result.json"
            result = score_arena(frozen, observations, output)
            self.assertEqual(result["status"], "IMPROVED")
            data = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(data["empirical_leaderboard"][0]["participant_id"], "candidate")
            self.assertEqual(data["effective_evidence_level"], "L2")

    def test_sealed_arena_only_emits_evidence_ready(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, lambda spec: spec.__setitem__("mode", "sealed"))
            output = base / "result.json"
            result = score_arena(frozen, observations, output)
            self.assertEqual(result["status"], "ARENA_EVIDENCE_READY")
            self.assertNotIn("PASS", result["status"])

    def test_candidate_hard_failure_blocks_sealed_arena(self) -> None:
        def mutate(rows: list[dict]) -> None:
            next(row for row in rows if row["participant_id"] == "candidate")["hard_failures"] = ["safety"]
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, lambda spec: spec.__setitem__("mode", "sealed"), mutate)
            result = score_arena(frozen, observations, base / "result.json")
            self.assertEqual(result["status"], "BLOCKED")

    def test_candidate_hard_failure_degrades_development_arena(self) -> None:
        def mutate(rows: list[dict]) -> None:
            next(row for row in rows if row["participant_id"] == "candidate")["hard_failures"] = ["truthfulness"]
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            result = score_arena(frozen, observations, base / "result.json")
            self.assertEqual(result["status"], "DEGRADED")

    def test_protocol_tampering_is_detected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base)
            spec = json.loads(frozen.read_text(encoding="utf-8"))
            spec["protocol"]["bootstrap_seed"] += 1
            write_json(frozen, spec)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_PROTOCOL_TAMPERED")

    def test_budget_mismatch_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            row = next(row for row in rows if row["participant_id"] == "candidate")
            row["cost"]["candidate_evaluations"] = 1
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_BUDGET_MISMATCH")

    def test_budget_ceiling_is_enforced(self) -> None:
        def mutate(spec: dict) -> None:
            spec["protocol"]["budget"]["ceiling_per_participant"] = 15
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_spec=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_BUDGET_EXCEEDED")

    def test_task_set_mismatch_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            for index, row in enumerate(rows):
                if row["participant_id"] == "candidate":
                    rows.pop(index)
                    return
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_TASK_SET_MISMATCH")

    def test_missing_required_split_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            rows[:] = [row for row in rows if row["split"] != "redteam"]
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_SPLIT_MISSING")

    def test_duplicate_observation_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            rows.append(dict(rows[0]))
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_DUPLICATE_OBSERVATION")

    def test_unknown_participant_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            rows[0]["participant_id"] = "intruder"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_UNKNOWN_PARTICIPANT")

    def test_metric_out_of_range_is_rejected(self) -> None:
        def mutate(rows: list[dict]) -> None:
            rows[0]["metrics"]["quality"] = 1.1
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            with self.assertRaises(TeleiosisError) as ctx:
                score_arena(frozen, observations, base / "result.json")
            self.assertEqual(ctx.exception.code, "ARENA_METRIC_RANGE")

    def test_invalid_weights_are_rejected_before_freeze(self) -> None:
        spec = load_json("templates/arena-spec.example.json")
        spec["protocol"]["dimensions"][0]["weight"] = 0.31
        with self.assertRaises(TeleiosisError) as ctx:
            validate_spec(spec)
        self.assertEqual(ctx.exception.code, "ARENA_WEIGHTS")

    def test_non_native_declared_l3_is_capped_at_l2(self) -> None:
        def mutate(spec: dict) -> None:
            spec["declared_evidence_level"] = "L3"
            spec["participants"][1]["adapter"]["native_execution"] = False
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_spec=mutate)
            score_arena(frozen, observations, base / "result.json")
            data = json.loads((base / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(data["effective_evidence_level"], "L2")

    def test_l4_without_authorized_production_is_capped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, lambda spec: spec.__setitem__("declared_evidence_level", "L4"))
            score_arena(frozen, observations, base / "result.json")
            data = json.loads((base / "result.json").read_text(encoding="utf-8"))
            self.assertEqual(data["effective_evidence_level"], "L3")

    def test_governance_board_does_not_change_empirical_score(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base)
            score_arena(frozen, observations, base / "one.json")
            score_one = json.loads((base / "one.json").read_text(encoding="utf-8"))["empirical_leaderboard"][0]["score"]
            spec = json.loads(frozen.read_text(encoding="utf-8"))
            spec.pop("freeze")
            spec["participants"][1]["governance_capabilities"] = []
            raw2 = base / "two.raw.json"
            frozen2 = base / "two.frozen.json"
            write_json(raw2, spec)
            freeze_spec(raw2, frozen2, "2026-08-02T00:00:00Z")
            score_arena(frozen2, observations, base / "two.json")
            two = json.loads((base / "two.json").read_text(encoding="utf-8"))
            score_two = two["empirical_leaderboard"][0]["score"]
            self.assertAlmostEqual(score_one, score_two)
            candidate_governance = next(row for row in two["governance_board"] if row["participant_id"] == "candidate")
            self.assertEqual(candidate_governance["coverage"], 0.0)

    def test_pareto_front_is_reported_separately(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base)
            score_arena(frozen, observations, base / "result.json")
            data = json.loads((base / "result.json").read_text(encoding="utf-8"))
            self.assertIn("candidate", data["pareto_front"])
            self.assertNotEqual(data["pareto_front"], data["governance_board"])

    def test_no_baseline_role_yields_insufficient_evidence(self) -> None:
        def mutate(spec: dict) -> None:
            spec["participants"][0]["role"] = "competitor"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_spec=mutate)
            result = score_arena(frozen, observations, base / "result.json")
            self.assertEqual(result["status"], "INSUFFICIENT_EVIDENCE")

    def test_equal_scores_require_reheat(self) -> None:
        def mutate(rows: list[dict]) -> None:
            baseline = {(row["task_id"], row["split"], row["slice"], row["repetition"]): row for row in rows if row["participant_id"] == "baseline"}
            for row in rows:
                if row["participant_id"] == "candidate":
                    source = baseline[(row["task_id"], row["split"], row["slice"], row["repetition"])]
                    row["metrics"] = dict(source["metrics"])
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base, mutate_rows=mutate)
            result = score_arena(frozen, observations, base / "result.json")
            self.assertEqual(result["status"], "REHEAT_REQUIRED")

    def test_markdown_report_is_created(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            _, frozen, observations = self.prepare(base)
            output = base / "result.json"
            score_arena(frozen, observations, output)
            report = output.with_suffix(".md")
            self.assertIn("经验效果主榜", report.read_text(encoding="utf-8"))

    def test_command_adapter_uses_explicit_argument_vector(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            spec = load_json("templates/arena-spec.example.json")
            script = base / "adapter.py"
            script.write_text(
                "import json, os\nfrom pathlib import Path\n"
                "Path(os.environ['TELEIOSIS_ARENA_OUTPUT']).write_text(json.dumps({'ok': True})+'\\n', encoding='utf-8')\n",
                encoding="utf-8",
            )
            spec["participants"][1]["adapter"] = {
                "kind": "command",
                "native_execution": True,
                "official_implementation": True,
                "command": [sys.executable, str(script)],
                "timeout_seconds": 30,
            }
            raw = base / "raw.json"
            frozen = base / "frozen.json"
            write_json(raw, spec)
            freeze_spec(raw, frozen, "2026-08-02T00:00:00Z")
            input_path = base / "input.json"
            write_json(input_path, {"task": "x"})
            result = execute_command_adapter(frozen, "candidate", input_path, base / "out.json", base / "receipt.json")
            self.assertEqual(result["status"], "ADAPTER_COMPLETED")
            self.assertTrue((base / "out.json").is_file())

    def test_shell_string_adapter_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            spec = load_json("templates/arena-spec.example.json")
            spec["participants"][1]["adapter"] = {
                "kind": "command",
                "native_execution": True,
                "official_implementation": True,
                "command": "echo unsafe",
            }
            raw = base / "raw.json"
            frozen = base / "frozen.json"
            write_json(raw, spec)
            freeze_spec(raw, frozen, "2026-08-02T00:00:00Z")
            input_path = base / "input.json"
            write_json(input_path, {"task": "x"})
            with self.assertRaises(TeleiosisError) as ctx:
                execute_command_adapter(frozen, "candidate", input_path, base / "out.json", base / "receipt.json")
            self.assertEqual(ctx.exception.code, "ADAPTER_COMMAND")


if __name__ == "__main__":
    unittest.main()
