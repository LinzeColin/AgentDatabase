from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from wbi_core.io import write_json
from wbi_core.orchestrator import init_orchestration, inspect_orchestration, mark_step


class OrchestratorTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.target = self.root / "target"; self.target.mkdir(); (self.target / "a.txt").write_text("a", encoding="utf-8")
        self.optimizer = self.root / "optimizer"; self.optimizer.mkdir(); (self.optimizer / "b.txt").write_text("b", encoding="utf-8")
        self.workspace = self.root / "workspace"

    def tearDown(self):
        self.tmp.cleanup()

    def test_engineering_cold_start(self):
        result = init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")
        self.assertEqual(result["orchestration_status"], "READY")
        self.assertEqual(result["current_step"], "PREFLIGHT")

    def test_formal_without_external_adapter_blocks_before_mutation(self):
        result = init_orchestration(self.target, self.workspace, self.optimizer, run_mode="formal", package_profile="optimizer", verification_level="deep", valid_as_of="2026-07-26")
        self.assertEqual(result["orchestration_status"], "BLOCKED")
        self.assertTrue(any("formal run requires" in item for item in result["blocked_reasons"]))

    def test_resume_preserves_identity(self):
        first = init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")
        second = inspect_orchestration(self.workspace)
        self.assertEqual(first["run_id"], second["run_id"])

    def test_receipt_hash_drift_blocks(self):
        init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")
        receipt = self.root / "receipt.json"; write_json(receipt, {"status": "PASS"})
        result = mark_step(self.workspace, "PREFLIGHT", receipt)
        self.assertEqual(result["current_step"], "CONTRACTS")
        write_json(receipt, {"status": "CHANGED"})
        status = inspect_orchestration(self.workspace)
        self.assertEqual(status["orchestration_status"], "BLOCKED")

    def test_out_of_order_step_rejected(self):
        init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")
        receipt = self.root / "receipt.json"; write_json(receipt, {"status": "PASS"})
        with self.assertRaises(ValueError):
            mark_step(self.workspace, "RESEARCH", receipt)

    def test_changed_target_requires_new_workspace(self):
        init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")
        (self.target / "a.txt").write_text("changed", encoding="utf-8")
        with self.assertRaises(ValueError):
            init_orchestration(self.target, self.workspace, self.optimizer, run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26")


    def test_workspace_inside_target_rejected(self):
        with self.assertRaises(ValueError):
            init_orchestration(
                self.target, self.target / "workspace", self.optimizer,
                run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26"
            )

    def test_workspace_parent_of_target_rejected(self):
        parent = self.root / "shared"
        parent.mkdir()
        target = parent / "target"; target.mkdir(); (target / "a.txt").write_text("a", encoding="utf-8")
        optimizer = self.root / "separate-optimizer"; optimizer.mkdir(); (optimizer / "b.txt").write_text("b", encoding="utf-8")
        with self.assertRaises(ValueError):
            init_orchestration(
                target, parent, optimizer,
                run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26"
            )

    def test_workspace_parent_of_optimizer_rejected(self):
        parent = self.root / "optimizer-parent"
        parent.mkdir()
        optimizer = parent / "optimizer"; optimizer.mkdir(); (optimizer / "b.txt").write_text("b", encoding="utf-8")
        target = self.root / "separate-target"; target.mkdir(); (target / "a.txt").write_text("a", encoding="utf-8")
        with self.assertRaises(ValueError):
            init_orchestration(
                target, parent, optimizer,
                run_mode="engineering", package_profile="optimizer", verification_level="release", valid_as_of="2026-07-26"
            )



if __name__ == "__main__":
    unittest.main()
