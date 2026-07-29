from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("prl", ROOT / "scripts" / "prl.py")
assert SPEC and SPEC.loader
prl = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(prl)


class ProductRealityLabTests(unittest.TestCase):
    def make_workspace(self, *, field_required: bool = False) -> Path:
        self.temp = tempfile.TemporaryDirectory(prefix="prl-test-")
        self.addCleanup(self.temp.cleanup)
        workspace = Path(self.temp.name) / "run"
        prl.initialize_workspace(
            workspace,
            "demo-subject",
            "commit-abc123",
            owner="test-owner",
            field_required=field_required,
        )
        return workspace

    def test_init_creates_required_workspace_and_is_not_ready(self) -> None:
        workspace = self.make_workspace()
        for rel in prl.REQUIRED_WORKSPACE_FILES:
            self.assertTrue((workspace / rel).is_file(), rel)
        errors, warnings = prl.validate_workspace(workspace)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertTrue(any("critical inventory is empty" in gap for gap in result["gaps"]))

    def test_ready_workspace_creates_non_adjudicative_handoff(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "READY_FOR_VERIFIER")
        output = prl.create_handoff(workspace)
        intake = json.loads(output.read_text(encoding="utf-8"))
        self.assertEqual(intake["status"], "READY_FOR_VERIFIER")
        self.assertEqual(intake["open_p0"], 0)
        self.assertEqual(intake["open_p1"], 0)
        self.assertNotIn("PASS", intake.values())

    def test_field_required_yields_field_pending_after_lab_gates_close(self) -> None:
        workspace = self.make_workspace(field_required=True)
        prl.populate_selftest_ready_workspace(workspace)
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "FIELD_VALIDATION_PENDING")
        self.assertIn("field:required validation is incomplete", result["gaps"])

    def test_open_high_severity_defect_blocks_readiness(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        evidence_id = json.loads((workspace / "evidence/index.json").read_text())["artifacts"][0]["evidence_id"]
        defect_path = workspace / "defect_ledger.json"
        defects = json.loads(defect_path.read_text())
        defects["defects"].append({
            "defect_id": "DEF-001",
            "title": "Critical demo defect",
            "severity": "P1",
            "status": "OPEN",
            "expectation_source": "selftest invariant",
            "source_method": "unit",
            "minimal_reproduction": ["run selftest"],
            "expected": "success",
            "actual": "failure",
            "impact": "blocks task",
            "environment": "test",
            "subject_ref": "commit-abc123",
            "root_cause": "unknown",
            "root_cause_confidence": 0.1,
            "owner": "test-owner",
            "fix_ref": "",
            "regression_oracle": "",
            "evidence_refs": [evidence_id],
            "duplicate_of": None,
            "evidence_class": "SYNTHETIC",
        })
        defect_path.write_text(json.dumps(defects, indent=2) + "\n")
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["gates"]["open_p1"] = 1
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertEqual(errors, [])
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertTrue(any("open_p1" in gap for gap in result["gaps"]))

    def test_coverage_overcount_is_blocked(self) -> None:
        workspace = self.make_workspace()
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["dimensions"]["surface"]["critical_total"] = 1
        coverage["dimensions"]["surface"]["critical_covered"] = 2
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("COVERAGE_OVERCOUNT" in error for error in result["errors"]))

    def test_manual_full_coverage_counters_without_items_are_blocked(self) -> None:
        workspace = self.make_workspace()
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        for dimension in coverage["dimensions"].values():
            dimension["critical_total"] = 1
            dimension["critical_covered"] = 1
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("COVERAGE_DERIVED_COUNT_MISMATCH" in error for error in result["errors"]))

    def test_catalog_item_cannot_disappear_from_coverage_inventory(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["dimensions"]["surface"]["items"] = []
        prl.recalculate_dimension(coverage["dimensions"]["surface"])
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("COVERAGE_INVENTORY_MISSING:surface" in error for error in errors))

    def test_field_completion_boolean_cannot_be_spoofed(self) -> None:
        workspace = self.make_workspace(field_required=True)
        prl.populate_selftest_ready_workspace(workspace)
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["gates"]["field_validation_complete"] = True
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("FIELD_COMPLETE_DERIVATION_MISMATCH" in error for error in errors))

    def test_real_field_evidence_can_close_required_field_gate(self) -> None:
        workspace = self.make_workspace(field_required=True)
        prl.populate_selftest_ready_workspace(workspace)
        field_file = workspace / "evidence" / "field-observed.txt"
        field_file.write_text("Observed representative user completed the task.\n", encoding="utf-8")
        index = prl.index_evidence(workspace, "FIELD_OBSERVED", "controlled-field-fixture")
        field_ref = next(
            item["evidence_id"] for item in index["artifacts"] if item["path"].endswith("field-observed.txt")
        )
        field_path = workspace / "field_experiment.json"
        field = json.loads(field_path.read_text())
        field["experiments"] = [{
            "experiment_id": "FIELD-1",
            "stage": "CLOSED_BETA",
            "hypothesis": "Representative users complete the critical task without assistance",
            "segment": "selftest users",
            "feature_flag": "selftest",
            "primary_metric": "task success",
            "guardrail_metrics": ["error rate"],
            "minimum_evidence_rule": "one observed fixture for selftest",
            "rollback_trigger": "any unexpected side effect",
            "privacy_masking": "no personal data",
            "evidence_class": "FIELD_OBSERVED",
            "status": "COMPLETED",
            "results": {"task_success": 1},
            "evidence_refs": [field_ref],
        }]
        field_path.write_text(json.dumps(field, indent=2) + "\n")
        feedback_path = workspace / "field_feedback.json"
        feedback = json.loads(feedback_path.read_text())
        feedback["evidence_class"] = "FIELD_OBSERVED"
        feedback["observations"] = [{"observation": "task completed"}]
        feedback["metrics"] = {"task_success": 1}
        feedback["decision"] = "field gate closed for selftest"
        feedback["evidence_refs"] = [field_ref]
        feedback_path.write_text(json.dumps(feedback, indent=2) + "\n")
        prl.sync_coverage_inventory(workspace, auto_cover_evidenced=True)
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["gates"]["field_validation_complete"] = True
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "READY_FOR_VERIFIER", result)

    def test_negative_control_is_a_readiness_gate(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        matrix_path = workspace / "test_matrix.json"
        matrix = json.loads(matrix_path.read_text())
        matrix["tests"][0]["negative_control_effective"] = False
        matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertTrue(any("negative control" in gap for gap in result["gaps"]))

    def test_graph_reference_drift_is_blocked(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        journey_path = workspace / "journey_state_graph.json"
        journey = json.loads(journey_path.read_text())
        journey["transitions"][0]["to"] = "STATE-MISSING"
        journey_path.write_text(json.dumps(journey, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertTrue(any("JOURNEY_TRANSITION_UNKNOWN_TO" in error for error in result["errors"]))

    def test_nested_pass_verdict_is_forbidden(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        matrix_path = workspace / "test_matrix.json"
        matrix = json.loads(matrix_path.read_text())
        matrix["tests"][0]["status"] = "PASS"
        matrix_path.write_text(json.dumps(matrix, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("FORBIDDEN_NESTED_VERDICT" in error for error in errors))

    def test_expired_waiver_is_invalid(self) -> None:
        workspace = self.make_workspace()
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        expiry = (date.today() - timedelta(days=1)).isoformat()
        coverage["waivers"].append({
            "id": "W-001",
            "scope": "surface:one",
            "reason": "test",
            "owner": "test-owner",
            "expires_at": expiry,
            "compensating_control": "none",
            "evidence_refs": [],
        })
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("WAIVER_EXPIRED" in error for error in errors))

    def test_evidence_hash_tampering_is_detected(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        (workspace / "evidence/selftest.txt").write_text("tampered\n", encoding="utf-8")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("EVIDENCE_HASH_MISMATCH" in error for error in errors))

    def test_duplicate_content_at_different_paths_gets_distinct_evidence_ids(self) -> None:
        workspace = self.make_workspace()
        (workspace / "evidence/a.txt").write_text("same content\n", encoding="utf-8")
        (workspace / "evidence/b.txt").write_text("same content\n", encoding="utf-8")
        index = prl.index_evidence(workspace, "SYNTHETIC", "duplicate-fixture")
        ids = [item["evidence_id"] for item in index["artifacts"]]
        self.assertEqual(len(ids), 2)
        self.assertEqual(len(set(ids)), 2)

    def test_sync_coverage_merges_new_catalog_evidence(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        (workspace / "evidence/new-trace.txt").write_text("new trace\n", encoding="utf-8")
        index = prl.index_evidence(workspace, "SYNTHETIC", "new-trace-tool")
        new_ref = next(
            item["evidence_id"] for item in index["artifacts"] if item["path"].endswith("new-trace.txt")
        )
        graph_path = workspace / "surface_graph.json"
        graph = json.loads(graph_path.read_text())
        graph["nodes"][0]["evidence_refs"].append(new_ref)
        graph_path.write_text(json.dumps(graph, indent=2) + "\n")
        prl.sync_coverage_inventory(workspace, auto_cover_evidenced=True)
        coverage = json.loads((workspace / "coverage_ledger.json").read_text())
        surface_item = coverage["dimensions"]["surface"]["items"][0]
        self.assertIn(new_ref, surface_item["evidence_refs"])
        evidence_sources = {
            item["source_ref"] for item in coverage["dimensions"]["evidence"]["items"]
        }
        self.assertIn(new_ref, evidence_sources)
        errors, _ = prl.validate_workspace(workspace)
        self.assertEqual(errors, [])

    def test_field_observed_claim_rejects_synthetic_artifact(self) -> None:
        workspace = self.make_workspace(field_required=True)
        prl.populate_selftest_ready_workspace(workspace)
        synthetic_ref = json.loads((workspace / "evidence/index.json").read_text())["artifacts"][0]["evidence_id"]
        field_path = workspace / "field_experiment.json"
        field = json.loads(field_path.read_text())
        field["experiments"] = [{
            "experiment_id": "FIELD-BAD-CLASS",
            "stage": "CLOSED_BETA",
            "hypothesis": "synthetic evidence must not close field gate",
            "segment": "selftest",
            "feature_flag": "selftest",
            "primary_metric": "task success",
            "guardrail_metrics": ["error rate"],
            "minimum_evidence_rule": "one field artifact",
            "rollback_trigger": "any error",
            "privacy_masking": "none needed",
            "evidence_class": "FIELD_OBSERVED",
            "status": "COMPLETED",
            "results": {"task_success": 1},
            "evidence_refs": [synthetic_ref],
        }]
        field_path.write_text(json.dumps(field, indent=2) + "\n")
        feedback_path = workspace / "field_feedback.json"
        feedback = json.loads(feedback_path.read_text())
        feedback["evidence_class"] = "FIELD_OBSERVED"
        feedback["decision"] = "invalid fixture"
        feedback["evidence_refs"] = [synthetic_ref]
        feedback_path.write_text(json.dumps(feedback, indent=2) + "\n")
        coverage_path = workspace / "coverage_ledger.json"
        coverage = json.loads(coverage_path.read_text())
        coverage["gates"]["field_validation_complete"] = True
        coverage_path.write_text(json.dumps(coverage, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("FIELD_EXPERIMENT_EVIDENCE_CLASS_MISMATCH" in error for error in errors))
        self.assertTrue(any("FIELD_FEEDBACK_EVIDENCE_CLASS_MISMATCH" in error for error in errors))

    def test_competitor_source_without_evidence_is_blocked(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        path = workspace / "competitor_evidence.json"
        competitor = json.loads(path.read_text())
        competitor["references"][0]["sources"][0].pop("evidence_ref")
        path.write_text(json.dumps(competitor, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("COMPETITOR_SOURCE_WITHOUT_EVIDENCE" in error for error in errors))

    def test_pending_provenance_blocks_readiness(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        path = workspace / "provenance_ledger.json"
        provenance = json.loads(path.read_text())
        provenance["items"][0]["review_status"] = "PENDING"
        provenance["items"][0].pop("reviewer", None)
        provenance["items"][0].pop("reviewed_at", None)
        path.write_text(json.dumps(provenance, indent=2) + "\n")
        result = prl.evaluate_readiness(workspace)
        self.assertEqual(result["status"], "MORE_EVIDENCE_REQUIRED")
        self.assertTrue(any("provenance:pending reviews" in gap for gap in result["gaps"]))

    def test_approved_provenance_requires_auditable_review(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        path = workspace / "provenance_ledger.json"
        provenance = json.loads(path.read_text())
        provenance["items"][0].pop("allowed_use_basis", None)
        provenance["items"][0].pop("reviewer", None)
        provenance["items"][0].pop("reviewed_at", None)
        path.write_text(json.dumps(provenance, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("PROVENANCE_APPROVED_MISSING_FIELD" in error for error in errors))

    def test_unfinalized_owner_is_blocked(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="prl-test-owner-")
        self.addCleanup(self.temp.cleanup)
        workspace = Path(self.temp.name) / "run"
        prl.initialize_workspace(workspace, "demo", "abc")
        errors, _ = prl.validate_workspace(workspace)
        self.assertIn("RUN_CONTRACT:authorization.owner is not finalized", errors)

    def test_evidence_subject_ref_mismatch_is_blocked(self) -> None:
        workspace = self.make_workspace()
        prl.populate_selftest_ready_workspace(workspace)
        index_path = workspace / "evidence/index.json"
        index = json.loads(index_path.read_text())
        index["artifacts"][0]["subject_ref"] = "different-subject"
        index_path.write_text(json.dumps(index, indent=2) + "\n")
        errors, _ = prl.validate_workspace(workspace)
        self.assertTrue(any("EVIDENCE_SUBJECT_REF_MISMATCH" in error for error in errors))

    def test_package_validator_passes(self) -> None:
        completed = subprocess.run(
            [sys.executable, str(ROOT / "scripts/validate_package.py"), str(ROOT)],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)


if __name__ == "__main__":
    unittest.main()
