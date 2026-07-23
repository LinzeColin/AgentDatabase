#!/usr/bin/env python3
"""Validate the public R12 Skill package and optional working/staged boundary."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, Mapping

import yaml
from jsonschema import Draft202012Validator


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table.artifact_boundary import (  # noqa: E402
    ArtifactBoundaryPolicy,
    PolicyError,
    scan_staged,
    scan_working_tree,
)
from project_cost_table.release import PerformanceBudget, ReleaseError  # noqa: E402


EXPECTED_RELEASE_FAMILIES = {
    "adversarial",
    "property",
    "metamorphic",
    "package_governance",
    "workbook_runtime",
    "private_reference_replay",
    "private_current_source",
    "performance",
}


def _read_yaml(path: Path, findings: list[Dict[str, str]]) -> Mapping[str, Any]:
    try:
        value = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, yaml.YAMLError):
        findings.append({"code": "YAML_UNREADABLE", "path": path.relative_to(MODULE_ROOT).as_posix()})
        return {}
    if not isinstance(value, dict):
        findings.append({"code": "YAML_ROOT_INVALID", "path": path.relative_to(MODULE_ROOT).as_posix()})
        return {}
    return value


def _add(findings: list[Dict[str, str]], condition: bool, code: str, path: str) -> None:
    if not condition:
        findings.append({"code": code, "path": path})


def _validate_schemas(findings: list[Dict[str, str]]) -> None:
    required = {
        "performance_budget.schema.json",
        "performance_summary.schema.json",
        "input_sufficiency_report.schema.json",
        "run_manifest.schema.json",
        "output_index.schema.json",
    }
    for name in sorted(required):
        path = MODULE_ROOT / "schemas" / name
        try:
            schema = json.loads(path.read_text(encoding="utf-8"))
            Draft202012Validator.check_schema(schema)
        except Exception:
            findings.append({"code": "SCHEMA_INVALID", "path": "schemas/%s" % name})


def _validate_test_matrix(findings: list[Dict[str, str]]) -> None:
    path = MODULE_ROOT / "config" / "release_test_matrix.yml"
    value = _read_yaml(path, findings)
    _add(findings, value.get("schema_version") == "kmfa.project_cost.release_test_matrix.v1", "TEST_MATRIX_VERSION", "config/release_test_matrix.yml")
    _add(findings, value.get("release_id") == "KMFA-PROJECT-COST-0.2.0-R12", "TEST_MATRIX_RELEASE", "config/release_test_matrix.yml")
    families = value.get("families")
    _add(findings, isinstance(families, dict) and set(families) == EXPECTED_RELEASE_FAMILIES, "TEST_MATRIX_FAMILIES", "config/release_test_matrix.yml")
    if not isinstance(families, dict):
        return
    for family, targets in families.items():
        if not isinstance(targets, list) or not targets or not all(isinstance(item, str) for item in targets):
            findings.append({"code": "TEST_MATRIX_TARGETS", "path": "config/release_test_matrix.yml:%s" % family})
            continue
        for target in targets:
            if target.startswith("/") or ".." in Path(target).parts or not (MODULE_ROOT / target).is_file():
                findings.append({"code": "TEST_MATRIX_TARGET_MISSING", "path": target})


def validate_package(*, working_tree: bool, staged: bool, repo_root: Path | None, module_relative_root: str) -> Dict[str, Any]:
    findings: list[Dict[str, str]] = []
    try:
        version = (MODULE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        version = ""
    governance = _read_yaml(MODULE_ROOT / "governance.yaml", findings)
    models = _read_yaml(MODULE_ROOT / "model_registry.yaml", findings)
    formulas = _read_yaml(MODULE_ROOT / "formula_registry.yaml", findings)
    _add(findings, version == "0.2.0", "RELEASE_VERSION", "VERSION")
    _add(findings, governance.get("task_pack_version") == "1.2.0", "TASK_PACK_VERSION", "governance.yaml")
    _add(findings, governance.get("product_version") == version, "GOVERNANCE_VERSION", "governance.yaml")
    run_status = governance.get("run_status")
    _add(
        findings,
        isinstance(run_status, dict) and all(run_status.get("R%d" % number) == "COMPLETE" for number in range(13)),
        "RUN_STATUS_INCOMPLETE",
        "governance.yaml",
    )
    _add(
        findings,
        isinstance(run_status, dict) and run_status.get("GLOBAL_INSTALL") == "MACHINE_LOCAL_EXTERNAL",
        "GLOBAL_INSTALL_BOUNDARY",
        "governance.yaml",
    )
    model_rows = models.get("models")
    _add(findings, isinstance(model_rows, list) and bool(model_rows), "MODEL_REGISTRY_EMPTY", "model_registry.yaml")
    if isinstance(model_rows, list):
        for row in model_rows:
            if not isinstance(row, dict):
                findings.append({"code": "MODEL_ROW_INVALID", "path": "model_registry.yaml"})
                continue
            model_id = str(row.get("model_id") or "UNKNOWN")
            _add(findings, row.get("product_version") == version, "MODEL_VERSION_DRIFT", "model_registry.yaml:%s" % model_id)
            status = row.get("status")
            _add(findings, isinstance(status, str) and "NOT_RELEASED" not in status and "PARTIAL_IMPLEMENTATION" not in status, "MODEL_NOT_RELEASED", "model_registry.yaml:%s" % model_id)
            if "internal_company_approval_managed" in row:
                _add(findings, row.get("internal_company_approval_managed") is False, "APPROVAL_BOUNDARY_RELAXED", "model_registry.yaml:%s" % model_id)
            if "finance_owner_or_authorized_person_managed" in row:
                _add(findings, row.get("finance_owner_or_authorized_person_managed") is False, "FINANCE_ROLE_BOUNDARY_RELAXED", "model_registry.yaml:%s" % model_id)
        primary = next((row for row in model_rows if isinstance(row, dict) and row.get("model_id") == governance.get("model_id")), None)
        _add(findings, isinstance(primary, dict) and primary.get("status") == "RELEASED_R12_FAIL_CLOSED_CURRENT_INPUT_GATED", "PRIMARY_MODEL_RELEASE_STATUS", "model_registry.yaml")
    formula_rows = formulas.get("formulas")
    _add(findings, isinstance(formula_rows, list) and len(formula_rows) == 8, "FORMULA_REGISTRY_COUNT", "formula_registry.yaml")
    if isinstance(formula_rows, list):
        for row in formula_rows:
            status = row.get("status") if isinstance(row, dict) else None
            _add(findings, isinstance(status, str) and status.startswith("IMPLEMENTED"), "FORMULA_NOT_IMPLEMENTED", "formula_registry.yaml")
    traceability_path = MODULE_ROOT / "TRACEABILITY_MATRIX.csv"
    try:
        with traceability_path.open(encoding="utf-8", newline="") as handle:
            traceability = list(csv.DictReader(handle))
    except (OSError, UnicodeError, csv.Error):
        traceability = []
    _add(findings, {row.get("requirement_id") for row in traceability} == {"REQ-%03d" % number for number in range(1, 20)}, "TRACEABILITY_SET", "TRACEABILITY_MATRIX.csv")
    for row in traceability:
        _add(findings, str(row.get("status") or "").startswith("IMPLEMENTED"), "TRACEABILITY_NOT_IMPLEMENTED", "TRACEABILITY_MATRIX.csv:%s" % row.get("requirement_id"))
    req17 = next((row for row in traceability if row.get("requirement_id") == "REQ-017"), {})
    _add(findings, req17.get("run_id") == "R12" and req17.get("status") == "IMPLEMENTED_R12", "PERFORMANCE_TRACEABILITY", "TRACEABILITY_MATRIX.csv:REQ-017")
    skill_text = (MODULE_ROOT / "SKILL.md").read_text(encoding="utf-8")
    for token, code in (
        ("RELEASED_0_2_0_FAIL_CLOSED", "SKILL_RELEASE_STATUS"),
        ("输入充分性", "SKILL_INPUT_PREFLIGHT"),
        ("绝对", "SKILL_OUTPUT_LOCATOR"),
        ("不设置财务负责人或授权人", "SKILL_ROLE_BOUNDARY"),
        ("不管理公司内部审批", "SKILL_APPROVAL_BOUNDARY"),
    ):
        _add(findings, token in skill_text, code, "SKILL.md")
    handoff_text = (MODULE_ROOT / "HANDOFF.md").read_text(encoding="utf-8")
    for token, code in (
        ("product `0.2.0`", "HANDOFF_RELEASE_VERSION"),
        ("R0–R12", "HANDOFF_RUN_STATUS"),
        ("global installation is `MACHINE_LOCAL_EXTERNAL`", "HANDOFF_GLOBAL_INSTALL_BOUNDARY"),
        ("BLOCKED_SOURCE", "HANDOFF_CURRENT_BLOCK"),
    ):
        _add(findings, token in handoff_text, code, "HANDOFF.md")
    feature_text = (MODULE_ROOT / "FEATURE_CATALOG.md").read_text(encoding="utf-8")
    _add(findings, "product `0.2.0` after R12" in feature_text, "FEATURE_RELEASE_VERSION", "FEATURE_CATALOG.md")
    model_text = (MODULE_ROOT / "MODEL_SPEC.md").read_text(encoding="utf-8")
    _add(findings, "RELEASED_R12_FAIL_CLOSED_CURRENT_INPUT_GATED" in model_text, "MODEL_SPEC_RELEASE_STATUS", "MODEL_SPEC.md")
    try:
        budget = PerformanceBudget.from_yaml(MODULE_ROOT / "config" / "performance_budgets.yml")
        _add(findings, budget.candidate_pair_budget_max == 1_000_000, "PERFORMANCE_BUDGET_DRIFT", "config/performance_budgets.yml")
    except ReleaseError as exc:
        findings.append({"code": exc.code, "path": "config/performance_budgets.yml"})
    _validate_schemas(findings)
    _validate_test_matrix(findings)
    policy_path = MODULE_ROOT / "config" / "artifact_classification.yml"
    try:
        policy = ArtifactBoundaryPolicy.from_yaml(policy_path)
        if working_tree:
            findings.extend(
                {"code": item.code, "path": item.path}
                for item in scan_working_tree(MODULE_ROOT, policy)
            )
        if staged:
            if repo_root is None:
                findings.append({"code": "REPO_ROOT_REQUIRED", "path": "--repo-root"})
            else:
                findings.extend(
                    {"code": item.code, "path": item.path}
                    for item in scan_staged(repo_root, module_relative_root, policy)
                )
    except PolicyError:
        findings.append({"code": "ARTIFACT_POLICY_INVALID", "path": "config/artifact_classification.yml"})
    ordered = sorted(findings, key=lambda item: (item["code"], item["path"]))
    return {
        "schema_version": "kmfa.project_cost.package_validation.v1",
        "status": "PASS" if not ordered else "FAILED",
        "product_version": version,
        "task_pack_version": governance.get("task_pack_version"),
        "r12_status": run_status.get("R12") if isinstance(run_status, dict) else None,
        "global_install_status": run_status.get("GLOBAL_INSTALL") if isinstance(run_status, dict) else None,
        "working_tree_scan_performed": working_tree,
        "staged_scan_performed": staged,
        "finding_count": len(ordered),
        "findings": ordered,
        "module_root": str(MODULE_ROOT),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate the R12 public Skill package and print its output location.")
    parser.add_argument("--working-tree", action="store_true")
    parser.add_argument("--staged", action="store_true")
    parser.add_argument("--repo-root")
    parser.add_argument("--module-relative-root", default="KMFA/project-cost-table-skill")
    parser.add_argument("--output", help="new absolute JSON evidence path")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output = Path(args.output).expanduser().absolute() if args.output else None
    if output is not None and (output.exists() or not output.parent.is_dir()):
        print(json.dumps({"status": "FAILED", "error_code": "OUTPUT_PATH_INVALID", "output": str(output)}, sort_keys=True))
        return 4
    result = validate_package(
        working_tree=args.working_tree,
        staged=args.staged,
        repo_root=Path(args.repo_root).expanduser() if args.repo_root else None,
        module_relative_root=args.module_relative_root,
    )
    encoded = (json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")
    if output is not None:
        with output.open("xb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    print("OUTPUT_FILE: %s" % (str(output) if output is not None else "STDOUT_ONLY"))
    return 0 if result["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
