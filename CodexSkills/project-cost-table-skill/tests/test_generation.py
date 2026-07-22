import json
import os
import tempfile
import unittest
import zipfile
from dataclasses import replace
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.generation import (
    GenerationError,
    ReviewQueueItem,
    RunGenerationRequest,
    generate_run_artifacts,
    verify_output_index,
    verify_run_seal,
)
from project_cost_table.security import SecurityProfile
from project_cost_table.statuses import CalculationStatus, GenerationStatus
from project_cost_table.workbook import ArtifactToolRuntime, EXPECTED_SHEETS

from r9_helpers import CONFIG_HASH, REQUEST_HASH, blocked_report, cost_actual_batch, lineage, sufficient_report


MODULE_ROOT = Path(__file__).resolve().parents[1]


def runtime_from_environment():
    if not os.environ.get("CODEX_SPREADSHEET_NODE") or not os.environ.get("CODEX_SPREADSHEET_NODE_MODULES"):
        return None
    return ArtifactToolRuntime.from_environment()


def request_for(
    output_dir: Path,
    *,
    blocked: bool = False,
    runtime=None,
    run_id: str = "r9-synthetic",
    review_tasks=(),
) -> RunGenerationRequest:
    batch, facts = cost_actual_batch()
    report = blocked_report(output_dir, run_id=run_id) if blocked else sufficient_report(output_dir, run_id=run_id)
    return RunGenerationRequest(
        run_id=run_id,
        request_hash=REQUEST_HASH,
        mode="calculate",
        as_of="2026-05-31",
        output_dir=output_dir,
        input_report=report,
        metric_batch=None if blocked else batch,
        facts=() if blocked else facts,
        source_lineage=() if blocked else lineage(),
        review_tasks=tuple(review_tasks),
        security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
        workbook_runtime=runtime,
        code_version="0.2.0",
        config_hash=CONFIG_HASH,
    )


class GenerationTests(unittest.TestCase):
    def test_insufficient_input_generates_prompt_and_diagnostics_only(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-blocked-"))
        output = root / "run"
        result = generate_run_artifacts(request_for(output, blocked=True, run_id="r9-blocked"))
        self.assertEqual(result.status_planes.generation_status, GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED)
        self.assertEqual(result.status_planes.calculation_status, CalculationStatus.BLOCKED_SOURCE)
        self.assertTrue((output / "missing_input_prompt.md").is_file())
        self.assertTrue((output / "blocked_diagnostics.json").is_file())
        self.assertFalse(any(output.glob("*.xlsx")))
        self.assertFalse((output / "INTERNAL_PROCESS_HANDOFF.md").exists())
        self.assertTrue(verify_run_seal(output))
        self.assertTrue(verify_output_index(output))
        locator = result.locator_text()
        self.assertIn(str(output), locator)
        self.assertIn(str(output / "OUTPUT_INDEX.md"), locator)
        prompt = (output / "missing_input_prompt.md").read_text(encoding="utf-8")
        self.assertIn("未回复不构成授权", prompt)
        self.assertIn("补充输入", prompt)
        self.assertIn("保持 BLOCKED，停止正式计算并保留诊断", prompt)

    def test_input_incomplete_run_cannot_carry_precalculated_metrics(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-no-early-calc-"))
        request = request_for(root / "run", blocked=True, run_id="r9-blocked")
        batch, facts = cost_actual_batch()
        with self.assertRaises(GenerationError):
            replace(request, metric_batch=batch, facts=facts).validate()

    def test_missing_workbook_runtime_is_an_explicit_nonfinal_block(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-runtime-block-"))
        output = root / "run"
        result = generate_run_artifacts(request_for(output, runtime=None))
        diagnostics = json.loads((output / "blocked_diagnostics.json").read_text(encoding="utf-8"))
        self.assertIn("WORKBOOK_RUNTIME_INPUT_REQUIRED", diagnostics["blocker_codes"])
        self.assertFalse(any(output.glob("*.xlsx")))
        self.assertTrue((output / "missing_input_prompt.md").is_file())
        self.assertEqual(result.primary_output, output / "blocked_diagnostics.json")

    def test_output_directory_is_non_overwriting(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-no-overwrite-"))
        output = root / "run"
        request = request_for(output, blocked=True, run_id="r9-blocked")
        generate_run_artifacts(request)
        before = (output / "run_seal.sha256").read_bytes()
        with self.assertRaises(GenerationError):
            generate_run_artifacts(request)
        self.assertEqual((output / "run_seal.sha256").read_bytes(), before)

    def test_restatement_requires_a_new_bound_superseding_run(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-restate-"))
        base = request_for(root / "run", blocked=True, run_id="r9-blocked")
        restate_report = replace(base.input_report, mode="restate")
        with self.assertRaises(GenerationError):
            replace(base, mode="restate", input_report=restate_report).validate()
        replace(
            base,
            mode="restate",
            input_report=restate_report,
            supersedes_run_id="prior-run-001",
        ).validate()

    def test_final_request_binds_input_coverage_and_exact_detail_facts(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-bindings-"))
        request = request_for(root / "run", runtime=None)
        incomplete_report = replace(request.input_report, requested_basis_ids=("JOB_COST_INCURRED",))
        with self.assertRaises(GenerationError):
            replace(request, input_report=incomplete_report).validate()
        with self.assertRaises(GenerationError):
            replace(request, facts=request.facts[:-1]).validate()

    @unittest.skipUnless(runtime_from_environment() is not None, "bundled spreadsheet runtime not injected")
    def test_renderer_failure_is_atomic_and_still_has_an_absolute_diagnostic_locator(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-render-failure-"))
        output = root / "run"
        injected = runtime_from_environment()
        failing_runtime = ArtifactToolRuntime(Path("/usr/bin/false"), injected.node_modules_dir)
        result = generate_run_artifacts(request_for(output, runtime=failing_runtime))
        self.assertEqual(result.status_planes.generation_status, GenerationStatus.FAILED)
        self.assertTrue((output / "generation_failure.json").is_file())
        self.assertFalse(any(output.glob("*.xlsx")))
        self.assertTrue(verify_run_seal(output))
        self.assertTrue(verify_output_index(output))
        self.assertIn(str(output / "generation_failure.json"), result.locator_text())

    @unittest.skipUnless(runtime_from_environment() is not None, "bundled spreadsheet runtime not injected")
    def test_validated_run_generates_safe_final_without_approval_state(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r9-final-"))
        output = root / "run"
        review = ReviewQueueItem(
            task_id="review-safe-text",
            severity="P2",
            blocker_code="NON_BLOCKING_NOTE",
            metric_id="COST_POSTED_ACTUAL",
            description="=SUM(A1:A2)",
            required_action="记录说明",
            blocking=False,
        )
        result = generate_run_artifacts(request_for(output, runtime=runtime_from_environment(), review_tasks=(review,)))
        self.assertEqual(result.status_planes.generation_status, GenerationStatus.FINAL_GENERATED)
        self.assertTrue(result.primary_output.is_file())
        self.assertTrue(result.internal_process_handoff.is_file())
        self.assertFalse((output / "blocked_diagnostics.json").exists())
        self.assertFalse((output / "missing_input_prompt.md").exists())
        self.assertTrue(verify_run_seal(output))
        self.assertTrue(verify_output_index(output))

        with zipfile.ZipFile(result.primary_output) as archive:
            workbook_xml = archive.read("xl/workbook.xml").decode("utf-8")
            self.assertTrue(all(name in workbook_xml for name in EXPECTED_SHEETS))
            self.assertFalse(any(name.casefold().startswith("xl/externallinks/") for name in archive.namelist()))
            self.assertFalse(any(b"<f" in archive.read(name) for name in archive.namelist() if name.startswith("xl/worksheets/") and name.endswith(".xml")))

        manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
        index = json.loads((output / "output_index.json").read_text(encoding="utf-8"))
        batch = json.loads((output / "metric_snapshots.json").read_text(encoding="utf-8"))
        facts_payload = json.loads((output / "metric_facts.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["generation_status"], "FINAL_GENERATED")
        self.assertNotIn("run_manifest.json", manifest["output_hashes"])
        self.assertNotIn("output_index.json", manifest["output_hashes"])
        self.assertTrue(all(Path(item["path"]).is_absolute() for item in index["files"]))
        self.assertNotIn("output_index.json", {Path(item["path"]).name for item in index["files"]})
        self.assertNotIn("run_seal.sha256", {Path(item["path"]).name for item in index["files"]})
        self.assertEqual(
            {tuple(item) for item in batch["required_pairs"]},
            {
                ("COST_POSTED_ACTUAL", "JOB_COST_INCURRED"),
                ("COST_POSTED_ACTUAL", "GL_RECOGNIZED_COGS"),
            },
        )
        self.assertTrue(all(item["channel_signed_delta_minor"] == 0 for item in batch["snapshots"]))
        self.assertTrue(all(item["channel_absolute_delta_minor"] == 0 for item in batch["snapshots"]))

        schema_pairs = (
            (manifest, "run_manifest.schema.json"),
            (index, "output_index.schema.json"),
        )
        for payload, schema_name in schema_pairs:
            schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)), [])
        snapshot_schema = json.loads((MODULE_ROOT / "schemas" / "metric_snapshot.schema.json").read_text(encoding="utf-8"))
        for item in batch["snapshots"]:
            self.assertEqual(list(Draft202012Validator(snapshot_schema, format_checker=FormatChecker()).iter_errors(item)), [])
        fact_schema = json.loads((MODULE_ROOT / "schemas" / "metric_fact.schema.json").read_text(encoding="utf-8"))
        for item in facts_payload["facts"]:
            self.assertEqual(list(Draft202012Validator(fact_schema, format_checker=FormatChecker()).iter_errors(item)), [])

        handoff = result.internal_process_handoff.read_text(encoding="utf-8")
        self.assertIn("Skill 不设置财务负责人或授权人", handoff)
        self.assertIn("Skill 外", handoff)
        self.assertNotIn("finance_owner", manifest)
        self.assertNotIn("approver", manifest)
        review_csv = (output / "review_tasks.csv").read_text(encoding="utf-8")
        self.assertIn("'=SUM(A1:A2)", review_csv)
        self.assertIn(str(output), result.locator_text())


if __name__ == "__main__":
    unittest.main()
