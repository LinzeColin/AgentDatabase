#!/usr/bin/env python3
"""Validate the Product Reality Lab skill package without external dependencies."""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from pathlib import Path

REQUIRED = (
    "SKILL.md",
    "README.md",
    "LICENSE-NOTICE.md",
    "config/defaults.json",
    "scripts/prl.py",
    "scripts/validate_package.py",
    "tests/test_prl.py",
    "schemas/run_contract.schema.json",
    "schemas/surface_graph.schema.json",
    "schemas/inventory_diff.schema.json",
    "schemas/journey_state_graph.schema.json",
    "schemas/fault_graph.schema.json",
    "schemas/oracle_catalog.schema.json",
    "schemas/test_matrix.schema.json",
    "schemas/coverage_ledger.schema.json",
    "schemas/defect_ledger.schema.json",
    "schemas/competitor_evidence.schema.json",
    "schemas/provenance_ledger.schema.json",
    "schemas/field_experiment.schema.json",
    "schemas/field_feedback.schema.json",
    "schemas/poka_yoke_audit.schema.json",
    "schemas/evidence_index.schema.json",
    "schemas/verifier_intake.schema.json",
    "templates/run_contract.template.json",
    "templates/surface_graph.template.json",
    "templates/inventory_diff.template.json",
    "templates/journey_state_graph.template.json",
    "templates/fault_graph.template.json",
    "templates/oracle_catalog.template.json",
    "templates/test_matrix.template.json",
    "templates/coverage_ledger.template.json",
    "templates/defect_ledger.template.json",
    "templates/competitor_evidence.template.json",
    "templates/provenance_ledger.template.json",
    "templates/field_experiment.template.json",
    "templates/field_feedback.template.json",
    "templates/poka_yoke_audit.template.json",
    "templates/evidence_index.template.json",
    "templates/residual_risk.template.md",
    "references/architecture.md",
    "references/coverage-model.md",
    "references/competitor-intelligence.md",
    "references/poka-yoke.md",
    "references/field-validation.md",
    "references/tool-routing.md",
    "references/risk-controls.md",
    "references/oracle-catalog.md",
    "references/defect-convergence.md",
    "references/verifier-handoff.md",
    "references/scenario-recipes.md",
    "references/runtime-exploration.md",
    "references/user-simulation.md",
    "references/test-data-catalog.md",
)

SECRET_PATTERNS = (
    re.compile(r"(?i)(api[_-]?key|client[_-]?secret|access[_-]?token|password)\s*[:=]\s*['\"][^'\"]{8,}['\"]"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
)


def validate(root: Path) -> list[str]:
    root = root.resolve()
    errors: list[str] = []
    for rel in REQUIRED:
        if not (root / rel).is_file():
            errors.append(f"MISSING:{rel}")

    for path in root.rglob("*"):
        if path.is_symlink():
            errors.append(f"SYMLINK_FORBIDDEN:{path.relative_to(root)}")
        if path.is_file() and path.stat().st_size == 0:
            errors.append(f"EMPTY_FILE:{path.relative_to(root)}")
        if path.is_file() and path.name in {".DS_Store"}:
            errors.append(f"JUNK_FILE:{path.relative_to(root)}")

    for path in root.rglob("*.json"):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001 - validation report must capture all parse errors
            errors.append(f"INVALID_JSON:{path.relative_to(root)}:{exc}")
            continue
        if path.name.endswith(".schema.json"):
            if data.get("$schema") != "https://json-schema.org/draft/2020-12/schema":
                errors.append(f"SCHEMA_DRAFT_MISSING:{path.relative_to(root)}")
        elif isinstance(data, dict) and "schema_version" in data and data.get("schema_version") != "0.1.0":
            errors.append(f"SCHEMA_VERSION_MISMATCH:{path.relative_to(root)}")

    for path in root.rglob("*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            errors.append(f"PYTHON_SYNTAX:{path.relative_to(root)}:{exc}")

    skill_path = root / "SKILL.md"
    if skill_path.is_file():
        skill = skill_path.read_text(encoding="utf-8")
        if not skill.startswith("---\n"):
            errors.append("SKILL_FRONTMATTER_MISSING")
        if "name: product-reality-lab" not in skill:
            errors.append("SKILL_NAME_MISMATCH")
        if "version: 0.0.0.3" not in skill:
            errors.append("SKILL_VERSION_MISMATCH")
        if "READY_FOR_VERIFIER" not in skill:
            errors.append("SKILL_HANDOFF_STATE_MISSING")

    prl_path = root / "scripts/prl.py"
    if prl_path.is_file():
        source = prl_path.read_text(encoding="utf-8")
        forbidden_assignments = (
            re.compile(r"status\s*=\s*['\"]PASS['\"]"),
            re.compile(r"status\s*=\s*['\"]VERIFIED['\"]"),
            re.compile(r"status\s*=\s*['\"]PRODUCTION_READY['\"]"),
        )
        for pattern in forbidden_assignments:
            if pattern.search(source):
                errors.append(f"FORBIDDEN_VERDICT_ASSIGNMENT:{pattern.pattern}")
        if 'READINESS_CALCULATION_VERSION = "0.2.1"' not in source:
            errors.append("READINESS_CALCULATION_VERSION_MISMATCH")
        if "sync-coverage" not in source:
            errors.append("SYNC_COVERAGE_COMMAND_MISSING")

    coverage_template = root / "templates/coverage_ledger.template.json"
    if coverage_template.is_file():
        data = json.loads(coverage_template.read_text(encoding="utf-8"))
        for name, dimension in data.get("dimensions", {}).items():
            if "items" not in dimension:
                errors.append(f"COVERAGE_ITEMS_MISSING:{name}")

    run_template = root / "templates/run_contract.template.json"
    if run_template.is_file():
        data = json.loads(run_template.read_text(encoding="utf-8"))
        if data.get("competitor_research_required") is not True:
            errors.append("COMPETITOR_RESEARCH_DEFAULT_MISSING")

    for path in root.rglob("*"):
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".zip"}:
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                errors.append(f"POSSIBLE_SECRET:{path.relative_to(root)}")

    if prl_path.is_file() and not errors:
        completed = subprocess.run(
            [sys.executable, str(prl_path), "selftest"],
            cwd=root,
            capture_output=True,
            text=True,
            check=False,
            timeout=60,
        )
        if completed.returncode != 0:
            output = (completed.stdout + completed.stderr).strip().replace("\n", " | ")
            errors.append(f"SELFTEST_FAILED:{completed.returncode}:{output[:500]}")

    return sorted(set(errors))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()
    errors = validate(args.root)
    print(json.dumps({"valid": not errors, "errors": errors, "root": str(args.root.resolve())}, ensure_ascii=False, indent=2))
    return 0 if not errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
