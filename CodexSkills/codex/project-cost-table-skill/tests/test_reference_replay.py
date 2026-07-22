import ast
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.generation import RunGenerationRequest, generate_run_artifacts
from project_cost_table.reference_replay import (
    ReferenceReplayRequest,
    run_reference_replay,
    verify_replay_output_index,
    verify_replay_run_seal,
)
from project_cost_table.security import SecurityProfile
from project_cost_table.statuses import (
    CalculationStatus,
    ExecutionStatus,
    GenerationStatus,
    InputReadinessStatus,
    ReplayFidelityStatus,
    SourceQualityStatus,
)
from r9_helpers import CONFIG_HASH, REQUEST_HASH, cost_actual_batch, lineage, sufficient_report


MODULE_ROOT = Path(__file__).resolve().parents[1]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_pdf(path: Path, *, active: bool = False) -> None:
    marker = b"/OpenAction << >>\n" if active else b""
    path.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog >>\nendobj\n"
        + marker
        + b"%%EOF\n"
    )


def baseline_payload(pdf_hashes, *, line_delta: bool = False):
    projects = []
    for index, pdf_hash in enumerate(pdf_hashes, 1):
        cost = 101 if line_delta and index == 1 else 100
        source_profit = 110 if index == 1 else 100
        expected_delta = 10 if index == 1 else 0
        projects.append(
            {
                "project_code": "SYNTHETIC-%d" % index,
                "project_name": "Synthetic Project %d" % index,
                "reference_pdf": "reference-%d.pdf" % index,
                "reference_pdf_sha256": pdf_hash,
                "source_revenue_cents": 200,
                "source_total_cost_cents": cost,
                "source_profit_cents": source_profit,
                "source_profit_rate_text": None if index == 2 else "source display",
                "line_items": [
                    {
                        "category": "labor",
                        "label": "Synthetic",
                        "amount_cents": 100,
                    }
                ],
                "expected_source_profit_delta_cents": expected_delta,
                "expected_kingdee_5001_cents_current_snapshot": 0,
            }
        )
    return {
        "schema_version": "kmfa.project_cost.reference_expected.private.v1",
        "classification": "PRIVATE_FINANCIAL_REFERENCE_DO_NOT_COMMIT_PUBLICLY",
        "generated_from_snapshot": "synthetic",
        "projects": projects,
    }


def make_case(*, project_count: int = 2, line_delta: bool = False, active_pdf: bool = False):
    root = Path(tempfile.mkdtemp(prefix="kmfa-r10-reference-"))
    raw = root / "raw"
    baseline_root = root / "baseline"
    raw.mkdir()
    baseline_root.mkdir()
    hashes = []
    for index in range(1, project_count + 1):
        pdf = raw / ("reference-%d.pdf" % index)
        write_pdf(pdf, active=active_pdf and index == 1)
        hashes.append(digest(pdf))
    baseline = baseline_root / "reference.json"
    baseline.write_text(
        json.dumps(baseline_payload(hashes, line_delta=line_delta), ensure_ascii=False),
        encoding="utf-8",
    )
    return root, raw, baseline_root, baseline


def request_for(
    root: Path,
    raw: Path,
    baseline_root: Path,
    baseline: Path,
    *,
    baseline_sha256=None,
    run_id="r10-synthetic",
    expected_project_count=2,
):
    return ReferenceReplayRequest(
        run_id=run_id,
        as_of="2026-05-31",
        input_root=raw,
        baseline_root=baseline_root,
        baseline_relative_path=baseline.name,
        baseline_sha256=baseline_sha256 or digest(baseline),
        output_dir=root / "output",
        expected_project_count=expected_project_count,
        security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
        code_version="0.2.0",
        config_hash="a" * 64,
    )


class ReferenceReplayTests(unittest.TestCase):
    def test_reference_calculate_isolation(self) -> None:
        root = Path(tempfile.mkdtemp(prefix="kmfa-r10-data-flow-"))
        ambient_baseline = root / "private_runtime" / "reference_baseline"
        ambient_baseline.mkdir(parents=True)
        sentinel = "REFERENCE-SENTINEL-MUST-NEVER-ENTER-CALCULATE-9381"
        (ambient_baseline / "ambient-reference.json").write_text(
            json.dumps({"private_reference_value": sentinel}),
            encoding="utf-8",
        )

        output = root / "calculate-output"
        batch, facts = cost_actual_batch()
        request = RunGenerationRequest(
            run_id="r10-calculate-isolation",
            request_hash=REQUEST_HASH,
            mode="calculate",
            as_of="2026-05-31",
            output_dir=output,
            input_report=sufficient_report(output, run_id="r10-calculate-isolation"),
            metric_batch=batch,
            facts=facts,
            source_lineage=lineage(),
            review_tasks=(),
            security_profile=SecurityProfile.from_yaml(MODULE_ROOT / "config" / "security_limits.yml"),
            workbook_runtime=None,
            code_version="0.2.0",
            config_hash=CONFIG_HASH,
        )
        field_names = set(RunGenerationRequest.__dataclass_fields__)
        self.assertFalse(any(token in name for name in field_names for token in ("reference", "baseline", "replay")))

        result = generate_run_artifacts(request)
        self.assertEqual(result.status_planes.calculation_status, CalculationStatus.BLOCKED_SECURITY)
        self.assertEqual(result.status_planes.generation_status, GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED)
        public_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in output.iterdir()
            if path.is_file() and path.suffix in {".json", ".md", ".csv", ".sha256"}
        )
        self.assertNotIn(sentinel, public_text)
        self.assertNotIn(str(ambient_baseline), public_text)

    def test_exact_replay_preserves_source_arithmetic_difference_without_calculation(self) -> None:
        root, raw, baseline_root, baseline = make_case()
        before = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in raw.iterdir()}
        result = run_reference_replay(request_for(root, raw, baseline_root, baseline))

        self.assertEqual(result.replay_fidelity_status, ReplayFidelityStatus.EXACT)
        self.assertEqual(result.source_quality_status, SourceQualityStatus.SOURCE_ARITHMETIC_DIFFERENCE)
        self.assertEqual(result.status_planes.execution_status, ExecutionStatus.SUCCEEDED)
        self.assertEqual(result.status_planes.input_readiness_status, InputReadinessStatus.SUFFICIENT)
        self.assertEqual(result.status_planes.calculation_status, CalculationStatus.NOT_EVALUATED)
        self.assertEqual(result.status_planes.generation_status, GenerationStatus.NOT_GENERATED)
        self.assertTrue(verify_replay_run_seal(result.output_dir))
        self.assertTrue(verify_replay_output_index(result.output_dir))
        self.assertFalse(any(result.output_dir.glob("*.xlsx")))
        self.assertFalse((result.output_dir / "INTERNAL_PROCESS_HANDOFF.md").exists())

        payload = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(payload["project_count"], 2)
        self.assertEqual(payload["exact_count"], 2)
        self.assertEqual(payload["source_arithmetic_difference_count"], 1)
        self.assertEqual(payload["projects"][0]["source_profit_delta_cents"], 10)
        self.assertEqual(payload["projects"][0]["replay_fidelity_status"], "EXACT")
        self.assertEqual(payload["projects"][1]["source_profit_rate_text"], None)
        self.assertNotIn("note", payload["projects"][0]["line_items"][0])
        self.assertTrue(
            all(
                item["reference_line_values_sha256"] == item["replayed_line_values_sha256"]
                for item in payload["projects"]
            )
        )
        after = {path.name: (path.read_bytes(), path.stat().st_mtime_ns) for path in raw.iterdir()}
        self.assertEqual(before, after)
        self.assertIn(str(result.output_dir), result.locator_text())
        self.assertIn(str(result.output_index_md), result.locator_text())

        for payload_value, schema_name in (
            (payload, "reference_replay_result.schema.json"),
            (
                json.loads((result.output_dir / "run_manifest.json").read_text(encoding="utf-8")),
                "run_manifest.schema.json",
            ),
            (
                json.loads((result.output_dir / "output_index.json").read_text(encoding="utf-8")),
                "output_index.schema.json",
            ),
        ):
            schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            errors = list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload_value))
            self.assertEqual(errors, [])

    def test_baseline_hash_drift_blocks_before_invalid_json_is_parsed(self) -> None:
        root, raw, baseline_root, baseline = make_case()
        baseline.write_text("{not-json", encoding="utf-8")
        result = run_reference_replay(
            request_for(root, raw, baseline_root, baseline, baseline_sha256="0" * 64)
        )
        diagnostics = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(result.replay_fidelity_status, ReplayFidelityStatus.BLOCKED_HASH)
        self.assertEqual(diagnostics["blocker_codes"], ["REFERENCE_BASELINE_HASH_DRIFT"])
        self.assertFalse((result.output_dir / "reference_replay_results.json").exists())
        self.assertTrue(verify_replay_run_seal(result.output_dir))

    def test_pdf_hash_drift_blocks_all_reference_values(self) -> None:
        root, raw, baseline_root, baseline = make_case()
        payload = json.loads(baseline.read_text(encoding="utf-8"))
        payload["projects"][0]["reference_pdf_sha256"] = "f" * 64
        baseline.write_text(json.dumps(payload), encoding="utf-8")
        result = run_reference_replay(request_for(root, raw, baseline_root, baseline))
        diagnostics = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(result.replay_fidelity_status, ReplayFidelityStatus.BLOCKED_HASH)
        self.assertEqual(diagnostics["blocker_codes"], ["REFERENCE_PDF_HASH_DRIFT"])
        self.assertFalse((result.output_dir / "reference_replay_results.json").exists())

    def test_line_sum_drift_is_distinct_from_source_arithmetic_difference(self) -> None:
        root, raw, baseline_root, baseline = make_case(line_delta=True)
        result = run_reference_replay(request_for(root, raw, baseline_root, baseline))
        diagnostics = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(result.replay_fidelity_status, ReplayFidelityStatus.BLOCKED_LINE_DELTA)
        self.assertEqual(result.status_planes.execution_status, ExecutionStatus.EXPECTED_BLOCKED)
        self.assertEqual(result.status_planes.input_readiness_status, InputReadinessStatus.SUFFICIENT)
        self.assertEqual(diagnostics["blocker_codes"], ["REFERENCE_LINE_SUM_DELTA"])

    def test_active_pdf_is_blocked_by_security_preflight(self) -> None:
        root, raw, baseline_root, baseline = make_case(active_pdf=True)
        result = run_reference_replay(request_for(root, raw, baseline_root, baseline))
        diagnostics = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["blocker_codes"], ["PDF_ACTIVE_CONTENT"])
        self.assertEqual(diagnostics["reference_values_replayed"], False)

    def test_atomic_output_never_overwrites_existing_run(self) -> None:
        root, raw, baseline_root, baseline = make_case()
        request = request_for(root, raw, baseline_root, baseline)
        result = run_reference_replay(request)
        before = result.run_seal.read_bytes()
        with self.assertRaises(Exception):
            run_reference_replay(request)
        self.assertEqual(result.run_seal.read_bytes(), before)

    def test_private_baseline_schema_rejects_float_money(self) -> None:
        root, raw, baseline_root, baseline = make_case()
        payload = json.loads(baseline.read_text(encoding="utf-8"))
        payload["projects"][0]["line_items"][0]["amount_cents"] = 100.0
        baseline.write_text(json.dumps(payload), encoding="utf-8")
        result = run_reference_replay(request_for(root, raw, baseline_root, baseline))
        diagnostics = json.loads(result.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["blocker_codes"], ["REFERENCE_BASELINE_MONEY"])
        self.assertEqual(result.status_planes.calculation_status, CalculationStatus.NOT_EVALUATED)

    def test_import_manifest_schema_accepts_minimal_private_binding(self) -> None:
        schema = json.loads(
            (MODULE_ROOT / "schemas" / "reference_baseline_import.schema.json").read_text(encoding="utf-8")
        )
        payload = {
            "schema_version": "kmfa.project_cost.reference_baseline_import.private.v1",
            "classification": "PRIVATE_RUNTIME",
            "baseline_file": "reference_expected.private.json",
            "baseline_sha256": "a" * 64,
            "expected_project_count": 8,
            "task_pack_version": "synthetic",
            "source_package_manifest_sha256": "b" * 64,
        }
        errors = list(Draft202012Validator(schema).iter_errors(payload))
        self.assertEqual(errors, [])

    def test_unexpected_partial_write_is_replaced_by_atomic_failure_evidence(self) -> None:
        root, raw, baseline_root, baseline = make_case()

        def fail_after_partial(directory, *_args, **_kwargs):
            (directory / "partial.tmp").write_text("partial", encoding="utf-8")
            raise RuntimeError("synthetic writer failure")

        with patch("project_cost_table.reference_replay._write_success", side_effect=fail_after_partial):
            result = run_reference_replay(request_for(root, raw, baseline_root, baseline))

        self.assertEqual(result.status_planes.execution_status, ExecutionStatus.FAILED)
        self.assertEqual(result.replay_fidelity_status, ReplayFidelityStatus.NOT_EVALUATED)
        self.assertEqual(result.primary_output.name, "generation_failure.json")
        self.assertFalse((result.output_dir / "partial.tmp").exists())
        self.assertTrue(verify_replay_run_seal(result.output_dir))
        self.assertTrue(verify_replay_output_index(result.output_dir))
        self.assertIn("generation_failure.json", result.locator_text())
        self.assertNotIn("blocked_diagnostics.json", result.locator_text())

    def test_reference_and_calculate_import_graphs_are_isolated(self) -> None:
        calculate_modules = (
            "accounting_basis.py",
            "adjustments.py",
            "formulas.py",
            "generation.py",
            "metrics.py",
            "payroll.py",
            "reconciliation.py",
        )
        for name in calculate_modules:
            source = (MODULE_ROOT / "src" / "project_cost_table" / name).read_text(encoding="utf-8")
            tree = ast.parse(source)
            imports = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    imports.extend(alias.name for alias in node.names)
                elif isinstance(node, ast.ImportFrom):
                    imports.append(node.module or "")
            self.assertFalse(any("reference_replay" in value for value in imports), name)

        replay_source = (MODULE_ROOT / "src" / "project_cost_table" / "reference_replay.py").read_text(encoding="utf-8")
        replay_tree = ast.parse(replay_source)
        replay_imports = []
        for node in ast.walk(replay_tree):
            if isinstance(node, ast.Import):
                replay_imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                replay_imports.append(node.module or "")
        for forbidden in ("generation", "metrics", "accounting_basis", "formulas", "payroll", "adjustments"):
            self.assertFalse(any(value == forbidden or value.endswith("." + forbidden) for value in replay_imports))

        env = dict(os.environ)
        env["PYTHONPATH"] = str(MODULE_ROOT / "src")
        probe = (
            "import sys,types;"
            "m=types.ModuleType('project_cost_table.reference_replay');"
            "m.__getattr__=lambda name:(_ for _ in ()).throw(RuntimeError('replay import'));"
            "sys.modules['project_cost_table.reference_replay']=m;"
            "import project_cost_table.generation,project_cost_table.metrics,project_cost_table.accounting_basis;"
            "print('calculate-import-pass')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(MODULE_ROOT),
            env=env,
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("calculate-import-pass", completed.stdout)

        cli_source = (MODULE_ROOT / "scripts" / "run_reference_regression.py").read_text(encoding="utf-8")
        self.assertIn("project_cost_table.reference_replay", cli_source)
        for forbidden in (
            "project_cost_table.generation",
            "project_cost_table.metrics",
            "project_cost_table.accounting_basis",
        ):
            self.assertNotIn(forbidden, cli_source)


if __name__ == "__main__":
    unittest.main()
