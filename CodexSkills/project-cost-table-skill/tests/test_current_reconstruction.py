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

from project_cost_table.current_reconstruction import (
    CURRENT_BASIS_IDS,
    CURRENT_METRICS,
    CurrentReconstructionError,
    CurrentReconstructionRequest,
    load_current_source_contract,
    metadata_fingerprint,
    run_current_source_reconstruction,
)
from project_cost_table.current_regression import (
    R11_EXPECTED_BLOCKERS,
    publish_expected_block_validation,
    validate_current_expected_block,
    verify_regression_bundle,
)
from project_cost_table.generation import verify_output_index, verify_run_seal
from project_cost_table.inventory import build_private_full_inventory
from project_cost_table.statuses import (
    CalculationStatus,
    ExecutionStatus,
    GenerationStatus,
    InputReadinessStatus,
)


MODULE_ROOT = Path(__file__).resolve().parents[1]


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def digest_bytes(value):
    return hashlib.sha256(value).hexdigest()


def requirement_rows():
    statuses = {
        "CURRENT_INPUT_MANIFEST_V3": "MISSING",
        "PROJECT_IDENTITY_EVIDENCE": "CONFLICT",
        "KINGDEE_READER_PROFILE": "MISSING",
        "ACCOUNTING_BASIS_POLICY": "MISSING",
        "PAYROLL_AND_TIME_SOURCE": "MISSING",
        "FULLY_LOADED_PAYROLL_POLICY": "MISSING",
        "PROJECT_TAX_POLICY_OR_DIRECT_LEDGER": "MISSING",
        "CAPITAL_INTEREST_POLICY": "MISSING",
        "PAYMENT_PROJECT_MAPPING": "CONFLICT",
    }
    return [
        {"requirement_id": key, "observed_status": statuses[key], "evidence_ref": "synthetic:%s" % key}
        for key in sorted(statuses)
    ]


def make_current_case(*, ambient_report=False):
    root = Path(tempfile.mkdtemp(prefix="kmfa-r11-current-"))
    raw = root / "raw"
    raw.mkdir()
    ledger = raw / "ledger.bin"
    ledger.write_bytes(b"synthetic-current-ledger")
    ambient = None
    if ambient_report:
        ambient = raw / "ambient-report.pdf"
        ambient.write_bytes(b"REFERENCE-SENTINEL-MUST-NOT-BE-READ-OR-EMITTED-7719")
    inventory = build_private_full_inventory(raw)
    ledger_entry = next(item for item in inventory if item.relative_path == ledger.name)
    contract = {
        "schema_version": "kmfa.project_cost.current_source_contract.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "contract_id": "r11-synthetic-current",
        "input_root": str(raw),
        "as_of": "2026-05-31",
        "scope": {
            "project_count": 8,
            "requested_metrics": list(CURRENT_METRICS),
            "requested_basis_ids": list(CURRENT_BASIS_IDS),
        },
        "source_snapshot": {
            "metadata_fingerprint": metadata_fingerprint(inventory),
            "entry_count": len(inventory),
            "total_size_bytes": sum(item.identity.size_bytes for item in inventory),
            "unsafe_entry_count": sum(item.status == "UNSAFE" for item in inventory),
            "task_pack_manifest_sha256": "a" * 64,
            "drift_review_sha256": "b" * 64,
            "drift_classification": "OUT_OF_SCOPE_INVENTORY_DRIFT_REVIEWED",
            "snapshot_overwritten": False,
        },
        "selected_sources": [
            {
                "slot_id": "general_ledger",
                "source_id": ledger_entry.source_id,
                "private_relative_path": ledger_entry.relative_path,
                "sha256": ledger_entry.sha256,
            }
        ],
        "evidence_requirements": requirement_rows(),
        "calculate_source_boundary": {
            "baseline_values_allowed": False,
            "report_line_items_allowed": False,
            "replay_adapters_allowed": False,
        },
    }
    contract_path = root / "current_source_contract.private.json"
    contract_data = json_bytes(contract)
    contract_path.write_bytes(contract_data)
    expected = {
        "schema_version": "kmfa.project_cost.expected_block_contract.private.v1",
        "classification": "PRIVATE_RUNTIME_DO_NOT_COMMIT",
        "expectation_id": "r11-synthetic-current-expected-block",
        "current_source_contract_sha256": digest_bytes(contract_data),
        "expected_production_exit_code": 3,
        "expected_status_planes": {
            "execution_status": "NEEDS_USER_INPUT",
            "input_readiness_status": "BLOCKED_NON_WAIVABLE",
            "calculation_status": "BLOCKED_SOURCE",
            "generation_status": "BLOCKED_DIAGNOSTICS_GENERATED",
        },
        "expected_blocker_codes": list(R11_EXPECTED_BLOCKERS),
        "expected_project_count": 8,
        "calculate_source_boundary": {
            "baseline_values_allowed": False,
            "report_line_items_allowed": False,
            "replay_adapters_allowed": False,
        },
        "expectation_frozen_before_production": True,
    }
    expected_path = root / "expected_block_contract.private.json"
    expected_data = json_bytes(expected)
    expected_path.write_bytes(expected_data)
    return {
        "root": root,
        "raw": raw,
        "ledger": ledger,
        "ambient": ambient,
        "contract": contract,
        "contract_path": contract_path,
        "contract_sha": digest_bytes(contract_data),
        "expected_path": expected_path,
        "expected_sha": digest_bytes(expected_data),
    }


def request_for(case, output_name="production"):
    return CurrentReconstructionRequest(
        run_id="r11-synthetic-production",
        as_of="2026-05-31",
        input_root=case["raw"],
        contract_path=case["contract_path"],
        contract_sha256=case["contract_sha"],
        output_dir=case["root"] / output_name,
        module_root=MODULE_ROOT,
    )


class CurrentReconstructionTests(unittest.TestCase):
    def test_production_current_run_is_exactly_blocked_and_sealed(self):
        case = make_current_case()
        request = request_for(case)
        result = run_current_source_reconstruction(request)

        self.assertEqual(result.blocker_codes, R11_EXPECTED_BLOCKERS)
        self.assertEqual(result.generated.status_planes.execution_status, ExecutionStatus.NEEDS_USER_INPUT)
        self.assertEqual(result.generated.status_planes.input_readiness_status, InputReadinessStatus.BLOCKED_NON_WAIVABLE)
        self.assertEqual(result.generated.status_planes.calculation_status, CalculationStatus.BLOCKED_SOURCE)
        self.assertEqual(result.generated.status_planes.generation_status, GenerationStatus.BLOCKED_DIAGNOSTICS_GENERATED)
        self.assertTrue(verify_run_seal(result.generated.output_dir))
        self.assertTrue(verify_output_index(result.generated.output_dir))
        self.assertFalse(any(result.generated.output_dir.glob("*.xlsx")))
        self.assertFalse((result.generated.output_dir / "INTERNAL_PROCESS_HANDOFF.md").exists())
        self.assertIn(str(result.generated.output_dir), result.locator_text())
        diagnostics = json.loads(result.generated.primary_output.read_text(encoding="utf-8"))
        self.assertEqual(diagnostics["blocker_codes"], list(R11_EXPECTED_BLOCKERS))

        contract_schema = json.loads((MODULE_ROOT / "schemas" / "current_source_contract.schema.json").read_text())
        self.assertEqual(
            list(Draft202012Validator(contract_schema, format_checker=FormatChecker()).iter_errors(case["contract"])),
            [],
        )

    def test_harness_passes_only_exact_production_exit_and_blockers(self):
        case = make_current_case()
        request = request_for(case)
        result = run_current_source_reconstruction(request)
        payload = dict(
            validate_current_expected_block(
                production_output_dir=result.generated.output_dir,
                production_exit_code=3,
                input_root=case["raw"],
                source_contract_path=case["contract_path"],
                source_contract_sha256=case["contract_sha"],
                expected_contract_path=case["expected_path"],
                expected_contract_sha256=case["expected_sha"],
            )
        )
        payload.update(
            {
                "production_stdout_sha256": "c" * 64,
                "production_stderr_sha256": "d" * 64,
                "production_command_argument_count": 17,
            }
        )
        self.assertEqual(payload["validation_status"], "PASS")
        self.assertEqual(payload["execution_status"], "EXPECTED_BLOCKED")
        validation_schema = json.loads(
            (MODULE_ROOT / "schemas" / "expected_block_validation.schema.json").read_text()
        )
        self.assertEqual(
            list(Draft202012Validator(validation_schema).iter_errors(payload)),
            [],
        )
        published = publish_expected_block_validation(payload, output_dir=case["root"] / "harness")
        self.assertTrue(published.passed)
        self.assertTrue(verify_regression_bundle(published.output_dir))
        self.assertIn(str(result.generated.output_dir), (published.output_dir / "production_output_locator.md").read_text())

        mismatch = validate_current_expected_block(
            production_output_dir=result.generated.output_dir,
            production_exit_code=0,
            input_root=case["raw"],
            source_contract_path=case["contract_path"],
            source_contract_sha256=case["contract_sha"],
            expected_contract_path=case["expected_path"],
            expected_contract_sha256=case["expected_sha"],
        )
        self.assertEqual(mismatch["validation_status"], "FAIL")
        self.assertIn("PRODUCTION_EXIT_CODE_MISMATCH", mismatch["validation_errors"])

    def test_ambient_report_is_not_selected_opened_or_emitted(self):
        case = make_current_case(ambient_report=True)
        original_open = Path.open

        def guarded_open(path, *args, **kwargs):
            if Path(path).absolute() == case["ambient"].absolute():
                raise AssertionError("calculate attempted to open an ambient report body")
            return original_open(path, *args, **kwargs)

        with patch("pathlib.Path.open", new=guarded_open):
            result = run_current_source_reconstruction(request_for(case))
        public_text = "\n".join(
            path.read_text(encoding="utf-8")
            for path in result.generated.output_dir.iterdir()
            if path.is_file() and path.suffix in {".json", ".md", ".csv", ".sha256"}
        )
        self.assertNotIn("REFERENCE-SENTINEL-MUST-NOT-BE-READ-OR-EMITTED-7719", public_text)
        self.assertNotIn(str(case["ambient"]), public_text)

    def test_contract_rejects_calculate_prohibited_sources(self):
        case = make_current_case()
        raw = json.loads(case["contract_path"].read_text())
        raw["selected_sources"][0]["slot_id"] = "reference_reports"
        raw["selected_sources"][0]["private_relative_path"] = "report.pdf"
        data = json_bytes(raw)
        case["contract_path"].write_bytes(data)
        with self.assertRaises(CurrentReconstructionError) as caught:
            load_current_source_contract(case["contract_path"], digest_bytes(data))
        self.assertEqual(caught.exception.code, "PROHIBITED_CALCULATE_SOURCE")

        second = make_current_case()
        raw = json.loads(second["contract_path"].read_text())
        raw["calculate_source_boundary"]["baseline_values_allowed"] = 0
        data = json_bytes(raw)
        second["contract_path"].write_bytes(data)
        with self.assertRaises(CurrentReconstructionError) as caught:
            load_current_source_contract(second["contract_path"], digest_bytes(data))
        self.assertEqual(caught.exception.code, "CALCULATE_SOURCE_BOUNDARY_RELAXED")

    def test_stale_expected_block_contract_cannot_hide_new_input_readiness(self):
        case = make_current_case()
        raw = json.loads(case["contract_path"].read_text())
        for item in raw["evidence_requirements"]:
            item["observed_status"] = "PRESENT"
        data = json_bytes(raw)
        case["contract_path"].write_bytes(data)
        case["contract_sha"] = digest_bytes(data)
        with self.assertRaises(CurrentReconstructionError) as caught:
            run_current_source_reconstruction(request_for(case))
        self.assertEqual(caught.exception.code, "CURRENT_R11_EXPECTATION_STALE")
        self.assertFalse((case["root"] / "production").exists())

    def test_metadata_or_selected_digest_drift_is_not_silently_accepted(self):
        case = make_current_case()
        (case["raw"] / "new-unselected.bin").write_bytes(b"drift")
        result = run_current_source_reconstruction(request_for(case))
        self.assertIn("CURRENT_SOURCE_METADATA_DRIFT_REVIEW_REQUIRED", result.blocker_codes)
        self.assertFalse(any(result.generated.output_dir.glob("*.xlsx")))

        second = make_current_case()
        before = second["ledger"].stat()
        second["ledger"].write_bytes(b"synthetic-current-ledgef")
        os.utime(second["ledger"], ns=(before.st_atime_ns, before.st_mtime_ns))
        result = run_current_source_reconstruction(request_for(second))
        self.assertIn("CURRENT_SELECTED_SOURCE_HASH_DRIFT", result.blocker_codes)

    def test_production_import_graph_does_not_load_regression_or_replay(self):
        path = MODULE_ROOT / "src" / "project_cost_table" / "current_reconstruction.py"
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imports.extend(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                imports.append(node.module or "")
        self.assertFalse(any("current_regression" in value or "reference_replay" in value for value in imports))

        script_source = (MODULE_ROOT / "scripts" / "run_current_source_reconstruction.py").read_text()
        self.assertNotIn("expected_block_contract", script_source)
        env = dict(os.environ)
        env["PYTHONPATH"] = str(MODULE_ROOT / "src")
        probe = (
            "import sys,types;"
            "a=types.ModuleType('project_cost_table.current_regression');"
            "a.__getattr__=lambda name:(_ for _ in ()).throw(RuntimeError('regression import'));"
            "b=types.ModuleType('project_cost_table.reference_replay');"
            "b.__getattr__=lambda name:(_ for _ in ()).throw(RuntimeError('replay import'));"
            "sys.modules['project_cost_table.current_regression']=a;"
            "sys.modules['project_cost_table.reference_replay']=b;"
            "import project_cost_table.current_reconstruction;"
            "print('current-production-import-pass')"
        )
        completed = subprocess.run(
            [sys.executable, "-c", probe],
            cwd=str(MODULE_ROOT),
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(completed.returncode, 0, completed.stderr)
        self.assertIn("current-production-import-pass", completed.stdout)


if __name__ == "__main__":
    unittest.main()
