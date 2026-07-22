from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yaml
from jsonschema import Draft202012Validator

MODULE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = MODULE_ROOT.parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.input_gate import (
    InputGateError,
    InputRequirements,
    MetricCatalog,
    OperationRequest,
    evaluate_input_sufficiency,
    publish_input_gate_outputs,
    render_missing_input_prompt,
    resolve_operation_output_dir,
    verify_detached_seal,
)
from project_cost_table.inventory import scan_inventory_metadata
from project_cost_table.manifest import load_input_manifest
from project_cost_table.resolutions import input_resolution_from_mapping
from r3_helpers import manifest_mapping, operation_request_mapping, write_manifest, write_source


REQUIREMENTS = InputRequirements.from_yaml(MODULE_ROOT / "config" / "input_requirements.yml")
CATALOG = MetricCatalog.from_yaml(MODULE_ROOT / "config" / "metric_catalog.yml")


def resolution_mapping(
    *,
    resulting_request: OperationRequest,
    manifest_sha256: str,
    requirement_id: str,
    resolution: str,
    affected_metrics: list[str],
    classification: str = "NON_WAIVABLE",
    evidence_refs: list[str] | None = None,
) -> dict[str, object]:
    return {
        "schema_version": "kmfa.project_cost.input_resolution.v1",
        "resolution_id": "resolution_" + "6" * 32,
        "run_id": resulting_request.run_id,
        "recorded_at": "2000-01-01T00:00:00+00:00",
        "bound_request_hash": "7" * 64,
        "resulting_request_hash": resulting_request.binding_hash(),
        "bound_manifest_sha256": manifest_sha256,
        "bound_requirements_sha256": REQUIREMENTS.content_sha256,
        "items": [
            {
                "requirement_id": requirement_id,
                "classification": classification,
                "resolution": resolution,
                "user_instruction": "apply the synthetic explicit handling",
                "user_instruction_ref": "instruction:synthetic-r3",
                "affected_metrics": affected_metrics,
                "effect_on_scope_or_metrics": "only the named synthetic Metric scope is affected",
                "evidence_refs": list(evidence_refs or []),
            }
        ],
    }


class InputGateTests(unittest.TestCase):
    @staticmethod
    def _copy_standalone_markers(destination: Path) -> None:
        required_files = (
            "SKILL.md",
            "VERSION",
            "config/input_requirements.yml",
            "config/metric_catalog.yml",
            "config/security_limits.yml",
            "src/project_cost_table/__init__.py",
            "scripts/run_input_preflight.py",
        )
        for relative in required_files:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(MODULE_ROOT / relative, target)

    @staticmethod
    def _run_repo_less_preflight(
        *, request_path: Path, module_root: Path, cwd: Path, codex_home: Path
    ) -> subprocess.CompletedProcess[str]:
        environment = dict(os.environ)
        environment["PATH"] = ""
        environment["CODEX_HOME"] = str(codex_home)
        return subprocess.run(
            [
                sys.executable,
                str(MODULE_ROOT / "scripts" / "run_input_preflight.py"),
                "--request",
                str(request_path),
                "--module-root",
                str(module_root),
            ],
            cwd=str(cwd),
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def _sufficient_cost_paid(self, root: Path) -> tuple[OperationRequest, object, tuple, Path]:
        raw = root / "raw"
        raw.mkdir()
        write_source(raw, "identity.dat")
        write_source(raw, "payment.dat")
        mapping = manifest_mapping(raw, {"project_identity": "identity.dat", "cash_out": "payment.dat"})
        manifest_path = write_manifest(root / "manifest.yml", mapping)
        output_dir = root / "private-output"
        request = OperationRequest.from_mapping(
            operation_request_mapping(
                run_id="RUN-R3-SUFFICIENT",
                mode="calculate",
                output_dir=output_dir,
                raw_root=raw,
                manifest_path=manifest_path,
                metrics=["COST_PAID"],
                basis_ids=["CASH_VERIFIED"],
                policy_refs={"verified_payment_status_and_mapping": "policy:synthetic-v1"},
            )
        )
        manifest = load_input_manifest(manifest_path)
        return request, manifest, scan_inventory_metadata(raw), output_dir

    def test_missing_inputs_create_one_compact_matrix_and_no_waiver_option(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request = OperationRequest.from_mapping(
                operation_request_mapping(
                    run_id="RUN-R3-MISSING",
                    mode="calculate",
                    output_dir=root / "outputs",
                    metrics=["COST_POSTED_ACTUAL"],
                    basis_ids=["JOB_COST_INCURRED"],
                )
            )
            report = evaluate_input_sufficiency(
                request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=root / "outputs",
                manifest=None,
                inventory_entries=(),
                security_capability_present=True,
            )
            prompt = render_missing_input_prompt(report)
            self.assertEqual(report.overall_status, "NEEDS_SUPPLEMENT")
            self.assertTrue(report.user_action_required)
            self.assertEqual(prompt.count("# 输入不足"), 1)
            self.assertIn("`RAW_ROOT_AND_MANIFEST`", prompt)
            self.assertIn("`1,3,2,5`", prompt)
            self.assertIn("保持 BLOCKED，停止正式计算并保留诊断", prompt)
            self.assertTrue(REQUIREMENTS.no_response_is_permission is False)
            metric_item = next(item for item in report.items if item.requirement_id == "METRIC_AND_BASIS")
            self.assertEqual(metric_item.observed_status, "MISSING")

    def test_input_policy_cannot_relax_authorization_payroll_or_required_modes(self) -> None:
        original = yaml.safe_load((MODULE_ROOT / "config" / "input_requirements.yml").read_text(encoding="utf-8"))
        cases = []
        no_response = yaml.safe_load(yaml.safe_dump(original))
        no_response["resolution_policy"]["no_response_is_permission"] = True
        cases.append((no_response, "INPUT_RESOLUTION_POLICY_RELAXED"))
        payroll = yaml.safe_load(yaml.safe_dump(original))
        payroll["payroll_model"]["model_id"] = "RELAXED_PAYROLL"
        cases.append((payroll, "PAYROLL_INPUT_CONTRACT_RELAXED"))
        modes = yaml.safe_load(yaml.safe_dump(original))
        del modes["mode_dependencies"]["restate"]
        cases.append((modes, "INPUT_DEPENDENCIES_INVALID"))
        omission = yaml.safe_load(yaml.safe_dump(original))
        omission["global_requirements"][0]["allowed_resolutions"].append("OMIT_OPTIONAL_PRESENTATION")
        cases.append((omission, "INPUT_REQUIREMENTS_RULE"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for index, (payload, code) in enumerate(cases):
                path = root / ("requirements-%d.yml" % index)
                path.write_text(yaml.safe_dump(payload, sort_keys=False), encoding="utf-8")
                with self.subTest(code=code):
                    with self.assertRaises(InputGateError) as caught:
                        InputRequirements.from_yaml(path)
                    self.assertEqual(caught.exception.code, code)

    def test_sufficient_gate_uses_metadata_only_and_does_not_prompt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            with mock.patch.object(Path, "open", side_effect=AssertionError("source body opened before gate")):
                report = evaluate_input_sufficiency(
                    request,
                    requirements=REQUIREMENTS,
                    metric_catalog=CATALOG,
                    output_dir=output_dir,
                    manifest=manifest,
                    inventory_entries=entries,
                    security_capability_present=True,
                )
            self.assertEqual(report.overall_status, "SUFFICIENT")
            self.assertFalse(report.user_action_required)
            self.assertIsNone(render_missing_input_prompt(report))

    def test_schema_lock_and_current_security_profile_are_required_before_sufficiency(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            profile_report = evaluate_input_sufficiency(
                request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=output_dir,
                manifest=manifest,
                inventory_entries=entries,
                security_capability_present=True,
                security_profile_id="DIFFERENT-PROFILE",
            )
            security_item = next(item for item in profile_report.items if item.requirement_id == "SAFE_READ_AND_DIGEST")
            self.assertEqual(security_item.observed_status, "CONFLICT")

            manifest_raw = manifest_mapping(
                Path(request.input_root),
                {"project_identity": "identity.dat", "cash_out": "payment.dat"},
            )
            manifest_raw["slots"]["cash_out"]["expected_schema_fingerprint"] = None
            unlocked_manifest = load_input_manifest(write_manifest(root / "unlocked.yml", manifest_raw))
            unlocked_report = evaluate_input_sufficiency(
                request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=output_dir,
                manifest=unlocked_manifest,
                inventory_entries=entries,
                security_capability_present=True,
            )
            cash_slot = next(item for item in unlocked_report.items if item.requirement_id == "SLOT:cash_out")
            self.assertEqual(cash_slot.observed_status, "MISSING")

    def test_report_matches_schema_and_atomic_outputs_have_absolute_locator_and_seal(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            report = evaluate_input_sufficiency(
                request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=output_dir,
                manifest=manifest,
                inventory_entries=entries,
                security_capability_present=True,
            )
            schema = json.loads(
                (MODULE_ROOT / "schemas" / "input_sufficiency_report.schema.json").read_text(encoding="utf-8")
            )
            self.assertEqual(list(Draft202012Validator(schema).iter_errors(report.as_dict())), [])
            outputs = publish_input_gate_outputs(report)
            self.assertTrue(verify_detached_seal(outputs.output_dir))
            index = json.loads(outputs.output_index_json.read_text(encoding="utf-8"))
            self.assertTrue(Path(index["output_dir"]).is_absolute())
            self.assertFalse(index["final_financial_workbook_generated"])
            self.assertFalse(any(path.suffix == ".xlsx" for path in outputs.output_dir.iterdir()))
            outputs.primary_output.write_text("tampered", encoding="utf-8")
            self.assertFalse(verify_detached_seal(outputs.output_dir))

    def test_output_directory_rejects_raw_overlap_and_tracked_tree(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            repo = root / "repo"
            runtime = repo / "module" / "private_runtime"
            raw = root / "raw"
            repo.mkdir()
            runtime.mkdir(parents=True)
            raw.mkdir()
            overlap = OperationRequest.from_mapping(
                operation_request_mapping(
                    run_id="RUN-RAW-OVERLAP",
                    mode="inventory",
                    output_dir=raw / "outputs",
                    raw_root=raw,
                )
            )
            with self.assertRaises(InputGateError) as caught:
                resolve_operation_output_dir(overlap, private_runtime_root=runtime, repo_root=repo)
            self.assertEqual(caught.exception.code, "OUTPUT_OVERLAPS_RAW")
            tracked = OperationRequest.from_mapping(
                operation_request_mapping(
                    run_id="RUN-TRACKED",
                    mode="review",
                    output_dir=repo / "public-output",
                )
            )
            with self.assertRaises(InputGateError) as caught:
                resolve_operation_output_dir(tracked, private_runtime_root=runtime, repo_root=repo)
            self.assertEqual(caught.exception.code, "OUTPUT_INSIDE_TRACKED_TREE")

    def test_scope_reduction_is_machine_recorded_and_only_passes_after_metric_removed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            resolution = input_resolution_from_mapping(
                resolution_mapping(
                    resulting_request=request,
                    manifest_sha256=manifest.content_sha256,
                    requirement_id="SLOT:cash_in",
                    resolution="SCOPE_REDUCED",
                    affected_metrics=["MARGIN_CASH"],
                )
            )
            report = evaluate_input_sufficiency(
                request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=output_dir,
                manifest=manifest,
                inventory_entries=entries,
                security_capability_present=True,
                resolution=resolution,
                prior_request_hash=resolution.bound_request_hash,
            )
            self.assertEqual(report.overall_status, "SUFFICIENT_WITH_DOCUMENTED_SCOPE")
            scope_item = next(item for item in report.items if item.requirement_id == "SLOT:cash_in")
            self.assertEqual(scope_item.observed_status, "NOT_IN_SCOPE")
            self.assertEqual(scope_item.selected_resolution, "SCOPE_REDUCED")
            outputs = publish_input_gate_outputs(report, resolution=resolution)
            self.assertTrue(verify_detached_seal(outputs.output_dir))
            self.assertEqual(
                json.loads(outputs.resolution_path.read_text(encoding="utf-8")),
                resolution.as_dict(),
            )
            self.assertIn(str(outputs.resolution_path), outputs.output_index_md.read_text(encoding="utf-8"))

    def test_claimed_alternate_stays_unresolved_until_present_on_rescan(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            missing_policy_mapping = operation_request_mapping(
                run_id=request.run_id,
                mode="calculate",
                output_dir=output_dir,
                raw_root=Path(request.input_root),
                manifest_path=Path(request.manifest_path),
                metrics=["COST_PAID"],
                basis_ids=["CASH_VERIFIED"],
                policy_refs={},
            )
            missing_request = OperationRequest.from_mapping(missing_policy_mapping)
            resolution = input_resolution_from_mapping(
                resolution_mapping(
                    resulting_request=missing_request,
                    manifest_sha256=manifest.content_sha256,
                    requirement_id="POLICY:verified_payment_status_and_mapping",
                    resolution="QUALIFIED_ALTERNATE_EVIDENCE",
                    affected_metrics=["COST_PAID"],
                    evidence_refs=["evidence:synthetic-alternate"],
                )
            )
            report = evaluate_input_sufficiency(
                missing_request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=output_dir,
                manifest=manifest,
                inventory_entries=entries,
                security_capability_present=True,
                resolution=resolution,
                prior_request_hash=resolution.bound_request_hash,
            )
            self.assertEqual(report.overall_status, "NEEDS_SUPPLEMENT")
            policy_item = next(item for item in report.items if item.requirement_id.startswith("POLICY:"))
            self.assertEqual(policy_item.selected_resolution, "QUALIFIED_ALTERNATE_EVIDENCE")
            self.assertEqual(policy_item.observed_status, "MISSING")

    def test_resolution_without_prior_report_binding_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, output_dir = self._sufficient_cost_paid(root)
            resolution = input_resolution_from_mapping(
                resolution_mapping(
                    resulting_request=request,
                    manifest_sha256=manifest.content_sha256,
                    requirement_id="SLOT:cash_in",
                    resolution="SCOPE_REDUCED",
                    affected_metrics=["MARGIN_CASH"],
                )
            )
            with self.assertRaises(InputGateError) as caught:
                evaluate_input_sufficiency(
                    request,
                    requirements=REQUIREMENTS,
                    metric_catalog=CATALOG,
                    output_dir=output_dir,
                    manifest=manifest,
                    inventory_entries=entries,
                    security_capability_present=True,
                    resolution=resolution,
                )
            self.assertEqual(caught.exception.code, "RESOLUTION_PRIOR_REPORT_REQUIRED")

    def test_script_missing_run_returns_two_and_prints_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            output_dir = root / "diagnostic-output"
            request_path = root / "request.json"
            request = operation_request_mapping(
                run_id="RUN-R3-SCRIPT-MISSING",
                mode="calculate",
                output_dir=output_dir,
                metrics=["COST_PAID"],
                basis_ids=["CASH_VERIFIED"],
            )
            request_path.write_text(json.dumps(request), encoding="utf-8")
            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_ROOT / "scripts" / "run_input_preflight.py"),
                    "--request",
                    str(request_path),
                    "--module-root",
                    str(MODULE_ROOT),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn("RESULT_STATUS: NEEDS_USER_INPUT", result.stdout)
            canonical_output = Path(os.path.realpath(str(output_dir)))
            self.assertIn("OUTPUT_DIR: %s" % canonical_output, result.stdout)
            self.assertTrue((canonical_output / "input_sufficiency_report.json").is_file())
            self.assertTrue(verify_detached_seal(canonical_output))

    def test_script_missing_run_is_portable_without_git_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex-home"
            standalone_module = codex_home / "skills" / "project-cost-table-skill"
            self._copy_standalone_markers(standalone_module)
            output_dir = root / "standalone-diagnostic-output"
            request_path = root / "request.json"
            request_path.write_text(
                json.dumps(
                    operation_request_mapping(
                        run_id="RUN-R3-STANDALONE-MISSING",
                        mode="calculate",
                        output_dir=output_dir,
                        metrics=["COST_PAID"],
                        basis_ids=["CASH_VERIFIED"],
                    )
                ),
                encoding="utf-8",
            )
            result = self._run_repo_less_preflight(
                request_path=request_path,
                module_root=standalone_module,
                cwd=root,
                codex_home=codex_home,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            canonical_output = Path(os.path.realpath(str(output_dir)))
            self.assertIn("RESULT_STATUS: NEEDS_USER_INPUT", result.stdout)
            self.assertIn("OUTPUT_DIR: %s" % canonical_output, result.stdout)
            self.assertTrue((canonical_output / "input_sufficiency_report.json").is_file())
            self.assertTrue(verify_detached_seal(canonical_output))

    def test_script_rejects_repo_less_copy_outside_codex_skills(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            standalone_module = root / "unregistered-copy" / "project-cost-table-skill"
            self._copy_standalone_markers(standalone_module)
            request_path = root / "request.json"
            request_path.write_text(
                json.dumps(
                    operation_request_mapping(
                        run_id="RUN-R3-UNREGISTERED-STANDALONE",
                        mode="calculate",
                        output_dir=root / "must-not-exist",
                        metrics=["COST_PAID"],
                        basis_ids=["CASH_VERIFIED"],
                    )
                ),
                encoding="utf-8",
            )
            result = self._run_repo_less_preflight(
                request_path=request_path,
                module_root=standalone_module,
                cwd=root,
                codex_home=root / "codex-home",
            )
            self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
            self.assertIn("STANDALONE_MODULE_ROOT_INVALID", result.stdout)
            self.assertFalse((standalone_module / "private_runtime").exists())

    def test_script_rejects_incomplete_standalone_module_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            codex_home = root / "codex-home"
            fake_module = codex_home / "skills" / "project-cost-table-skill"
            fake_module.mkdir(parents=True)
            request_path = root / "request.json"
            request_path.write_text(
                json.dumps(
                    operation_request_mapping(
                        run_id="RUN-R3-INCOMPLETE-STANDALONE",
                        mode="calculate",
                        output_dir=root / "must-not-exist",
                        metrics=["COST_PAID"],
                        basis_ids=["CASH_VERIFIED"],
                    )
                ),
                encoding="utf-8",
            )
            result = self._run_repo_less_preflight(
                request_path=request_path,
                module_root=fake_module,
                cwd=root,
                codex_home=codex_home,
            )
            self.assertEqual(result.returncode, 4, result.stdout + result.stderr)
            self.assertIn("STANDALONE_MODULE_ROOT_INVALID", result.stdout)
            self.assertFalse((fake_module / "private_runtime").exists())

    def test_script_accepts_only_resolution_bound_to_sealed_prior_incomplete_report(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            request, manifest, entries, _ = self._sufficient_cost_paid(root)
            prior_request = OperationRequest.from_mapping(
                operation_request_mapping(
                    run_id=request.run_id,
                    mode="calculate",
                    output_dir=root / "prior-output",
                    raw_root=Path(request.input_root),
                    manifest_path=Path(request.manifest_path),
                    metrics=["COST_PAID"],
                    basis_ids=["CASH_VERIFIED"],
                    policy_refs={},
                )
            )
            prior_report = evaluate_input_sufficiency(
                prior_request,
                requirements=REQUIREMENTS,
                metric_catalog=CATALOG,
                output_dir=root / "prior-output",
                manifest=manifest,
                inventory_entries=entries,
                security_capability_present=True,
            )
            self.assertTrue(prior_report.user_action_required)
            prior_outputs = publish_input_gate_outputs(prior_report)

            current_mapping = operation_request_mapping(
                run_id=request.run_id,
                mode="calculate",
                output_dir=root / "current-output",
                raw_root=Path(request.input_root),
                manifest_path=Path(request.manifest_path),
                metrics=["COST_PAID"],
                basis_ids=["CASH_VERIFIED"],
                policy_refs={"verified_payment_status_and_mapping": "policy:synthetic-v1"},
            )
            current_request = OperationRequest.from_mapping(current_mapping)
            resolution_raw = resolution_mapping(
                resulting_request=current_request,
                manifest_sha256=manifest.content_sha256,
                requirement_id="POLICY:verified_payment_status_and_mapping",
                resolution="SUPPLIED",
                affected_metrics=["COST_PAID"],
                evidence_refs=["evidence:synthetic-supply"],
            )
            resolution_raw["bound_request_hash"] = prior_report.request_hash
            resolution_path = root / "resolution.json"
            resolution_path.write_text(json.dumps(resolution_raw), encoding="utf-8")
            current_mapping["resolution_path"] = str(resolution_path)
            current_mapping["prior_sufficiency_report_path"] = str(prior_outputs.primary_output)
            request_path = root / "current-request.json"
            request_path.write_text(json.dumps(current_mapping), encoding="utf-8")

            original_seal = prior_outputs.run_seal.read_text(encoding="ascii")
            prior_outputs.run_seal.write_text(
                "\n".join(
                    line for line in original_seal.splitlines() if not line.endswith("  input_sufficiency_report.json")
                )
                + "\n",
                encoding="ascii",
            )
            invalid = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_ROOT / "scripts" / "run_input_preflight.py"),
                    "--request",
                    str(request_path),
                    "--module-root",
                    str(MODULE_ROOT),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(invalid.returncode, 4, invalid.stdout + invalid.stderr)
            self.assertIn("PRIOR_REPORT_SEAL_INVALID", invalid.stdout)
            prior_outputs.run_seal.write_text(original_seal, encoding="ascii")

            result = subprocess.run(
                [
                    sys.executable,
                    str(MODULE_ROOT / "scripts" / "run_input_preflight.py"),
                    "--request",
                    str(request_path),
                    "--module-root",
                    str(MODULE_ROOT),
                ],
                cwd=str(REPO_ROOT),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            current_output = Path(os.path.realpath(str(root / "current-output")))
            self.assertIn("RESULT_STATUS: INPUT_SUFFICIENT", result.stdout)
            self.assertIn("OUTPUT_DIR: %s" % current_output, result.stdout)
            self.assertTrue((current_output / "input_resolution.json").is_file())
            self.assertTrue(verify_detached_seal(current_output))


if __name__ == "__main__":
    unittest.main()
