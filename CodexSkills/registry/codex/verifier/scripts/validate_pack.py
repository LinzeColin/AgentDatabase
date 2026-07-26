#!/usr/bin/env python3
"""Validate the Verifier v0.0.2.2 skill payload and portability contract (stdlib only)."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any, Optional

SKILL_VERSION = "0.0.2.2"
EVIDENCE_SCHEMA_VERSION = "2.1"
EXPECTED_FILES = {
    "SKILL.md",
    "VERSION",
    "MANIFEST.json",
    "SHA256SUMS.txt",
    "agents/openai.yaml",
    "references/acceptance-contract.md",
    "references/adapters-and-portability.md",
    "references/ai-system-acceptance.md",
    "references/coverage-model.md",
    "references/evidence-integrity.md",
    "references/evidence-privacy-retention.md",
    "references/execution-playbook.md",
    "references/flaky-and-test-effectiveness.md",
    "references/human-acceptance.md",
    "references/product-design-taskpack-contract.md",
    "references/release-assurance.md",
    "references/review-panel-protocol.md",
    "references/risk-and-test-planning.md",
    "references/safety-policy.md",
    "references/threat-model-and-command-safety.md",
    "references/tool-routing.md",
    "references/verdict-and-reporting.md",
    "scripts/command_guard.py",
    "scripts/doctor.py",
    "scripts/evidence_guard.py",
    "scripts/finalize_acceptance_run.py",
    "scripts/ingest_taskpack.py",
    "scripts/init_acceptance_run.py",
    "scripts/make_gallery.py",
    "scripts/normalize_adapter_result.py",
    "scripts/package_review_taskpack.py",
    "scripts/plan_acceptance.py",
    "scripts/review_panel.py",
    "scripts/run_selftest.py",
    "scripts/validate_pack.py",
    "scripts/verify_distribution.py",
    "templates/ACCEPTANCE_PLAN.json",
    "templates/ADAPTER_CONTRACT.json",
    "templates/ADAPTER_RESULT.json",
    "templates/ACCEPTANCE_REQUEST.json",
    "templates/ACCEPTANCE_REQUEST.yaml",
    "templates/AI_EVAL_MATRIX.md",
    "templates/CAPABILITY_REPORT.json",
    "templates/COMMAND_LOG.json",
    "templates/COMMAND_POLICY_REPORT.json",
    "templates/DEFECT_REPORT.md",
    "templates/EVIDENCE_POLICY.json",
    "templates/EVIDENCE_PRIVACY_REPORT.json",
    "templates/GALLERY_PAIRS.csv",
    "templates/HUMAN_JOURNEY.md",
    "templates/MODIFICATION_REPORT.md",
    "templates/RELEASE_ASSURANCE.md",
    "templates/REVIEW_PANEL.json",
    "templates/RUN_MANIFEST.yaml",
    "templates/TEST_MATRIX.md",
    "templates/TRACEABILITY_MATRIX.json",
    "templates/VERDICT_TEMPLATE.md",
    "templates/WAIVER_TEMPLATE.json",
    "tests/test_adapter_contract.py",
    "tests/test_tools.py",
    "tests/test_v0022_tools.py",
}
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_IMPORTS = {"yaml", "requests", "pandas", "numpy", "PIL"}
CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_SUFFIXES = {".pyc", ".pyo"}


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read {path}: {error}")
        return ""


def _load_json(path: Path, label: str, errors: list[str]) -> Optional[dict[str, Any]]:
    if not path.is_file():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        errors.append(f"{label} must be strict JSON: {error}")
        return None
    if not isinstance(value, dict):
        errors.append(f"{label} root must be an object")
        return None
    return value


def _is_cache(relative: Path) -> bool:
    return bool(set(relative.parts) & CACHE_DIRS) or relative.suffix in CACHE_SUFFIXES


def _portable_tree(payload: Path, errors: list[str], mode: str) -> set[str]:
    actual: set[str] = set()
    folded: dict[str, str] = {}
    for path in payload.rglob("*"):
        relative = path.relative_to(payload)
        rel = relative.as_posix()
        try:
            mode_bits = path.lstat().st_mode
        except OSError as error:
            errors.append(f"cannot stat {rel}: {error}")
            continue
        if stat.S_ISLNK(mode_bits):
            errors.append(f"symlink forbidden: {rel}")
            continue
        if stat.S_ISDIR(mode_bits):
            continue
        if not stat.S_ISREG(mode_bits):
            errors.append(f"non-regular entry forbidden: {rel}")
            continue
        if _is_cache(relative):
            if mode == "distribution":
                errors.append(f"compiled/cache artifact forbidden in distribution: {rel}")
            continue
        actual.add(rel)
        if any(part in {".", ".."} for part in relative.parts) or "\\" in rel or "\x00" in rel:
            errors.append(f"non-portable path: {rel!r}")
        key = rel.casefold()
        if key in folded and folded[key] != rel:
            errors.append(f"case-colliding paths: {folded[key]} / {rel}")
        folded[key] = rel
    for rel in sorted(EXPECTED_FILES - actual):
        errors.append(f"missing required file: {rel}")
    for rel in sorted(actual - EXPECTED_FILES):
        errors.append(f"unexpected payload file: {rel}")
    return actual


def _frontmatter(payload: Path, errors: list[str]) -> None:
    path = payload / "SKILL.md"
    content = _read_text(path, errors)
    match = FRONTMATTER_RE.match(content)
    if match is None:
        errors.append("SKILL.md has no valid YAML frontmatter")
        return
    body = match.group("body")
    if not re.search(r"(?m)^name:\s*verifier\s*$", body):
        errors.append("SKILL.md name must be verifier")
    description_match = re.search(r"(?m)^description:\s*(.+)$", body)
    if description_match is None:
        errors.append("SKILL.md description missing")
    else:
        description = description_match.group(1).strip()
        if len(description) < 180:
            errors.append("SKILL.md description is too vague")
        if len(description) > 1024:
            errors.append("SKILL.md description exceeds 1024 characters")
    if len(content.splitlines()) > 500:
        errors.append("SKILL.md exceeds 500 lines; move detail into references")
    required = (
        "一次只裁决一个",
        "Product-Design-Taskpack",
        "TASKPACK_SOURCE_SNAPSHOT.zip",
        "pack_digest_sha256",
        "contract_digest_sha256",
        "source snapshot → build → artifact/image → deployment",
        "Requirement → Acceptance → Oracle",
        "change_impact",
        "真实用户结果",
        "generator_is_sole_judge=false",
        "role_separated_same_model",
        "ACTION: ESCALATE",
        "NOT_RUN",
        "PASS_WITH_RISKS",
        "acceptance_review_taskpack.zip",
        "Token 与上下文纪律",
    )
    for term in required:
        if term not in content:
            errors.append(f"SKILL.md missing required contract term: {term}")

    for target in LINK_RE.findall(content):
        if "://" in target or target.startswith("#"):
            continue
        clean = target.split("#", 1)[0]
        linked = (payload / clean).resolve()
        try:
            linked.relative_to(payload)
        except ValueError:
            errors.append(f"SKILL.md link escapes payload: {target}")
            continue
        if not linked.is_file():
            errors.append(f"SKILL.md link target missing: {target}")


def _version(payload: Path, errors: list[str]) -> None:
    value = _read_text(payload / "VERSION", errors).strip()
    if value != SKILL_VERSION:
        errors.append(f"VERSION must be {SKILL_VERSION}")
    skill = _read_text(payload / "SKILL.md", errors)
    if f"Skill release: `{SKILL_VERSION}`" not in skill:
        errors.append("SKILL.md release version does not match VERSION")


def _python_files(payload: Path, errors: list[str]) -> None:
    for path in sorted((payload / "scripts").glob("*.py")) + sorted((payload / "tests").glob("*.py")):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
            tree = ast.parse(source, filename=str(path))
        except (OSError, UnicodeError, SyntaxError) as error:
            errors.append(f"invalid Python {path.relative_to(payload)}: {error}")
            continue
        for node in ast.walk(tree):
            names: set[str] = set()
            if isinstance(node, ast.Import):
                names = {alias.name.split(".", 1)[0] for alias in node.names}
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = {node.module.split(".", 1)[0]}
            bad = names & FORBIDDEN_IMPORTS
            if bad:
                errors.append(f"{path.relative_to(payload)} imports non-stdlib dependency: {sorted(bad)}")
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                for keyword in node.keywords:
                    if keyword.arg == "shell" and isinstance(keyword.value, ast.Constant) and keyword.value.value is True:
                        errors.append(f"{path.relative_to(payload)} uses forbidden shell execution")


def _strict_templates(payload: Path, errors: list[str]) -> None:
    manifest = _load_json(payload / "templates/RUN_MANIFEST.yaml", "RUN_MANIFEST.yaml", errors)
    if manifest is not None:
        if manifest.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            errors.append("RUN_MANIFEST evidence schema must remain 2.1 for compatibility")
        for key in ("run", "scope", "taskpack", "traceability", "subject", "environment", "release", "ai_system", "evidence", "assurance_v22", "verdict"):
            if not isinstance(manifest.get(key), dict):
                errors.append(f"RUN_MANIFEST missing object: {key}")
        for key in ("tools", "commands", "inputs", "results", "findings", "waivers", "abort_or_incidents"):
            if not isinstance(manifest.get(key), list):
                errors.append(f"RUN_MANIFEST missing list: {key}")
        if manifest.get("scope", {}).get("mode") != "single-project":
            errors.append("RUN_MANIFEST scope.mode must be single-project")
        if manifest.get("scope", {}).get("verdict_scope") != "target-project-only":
            errors.append("RUN_MANIFEST scope.verdict_scope must be target-project-only")
        independence = manifest.get("ai_system", {}).get("evaluator_independence", {})
        if independence.get("generator_is_sole_judge") is not False:
            errors.append("RUN_MANIFEST must default generator_is_sole_judge=false")
        assurance = manifest.get("assurance_v22", {})
        if assurance.get("skill_version") != SKILL_VERSION or assurance.get("enforced") is not True:
            errors.append("RUN_MANIFEST assurance_v22 must be enabled for skill 0.0.2.2")
        for key in ("capability_report", "acceptance_plan", "command_policy", "evidence_privacy", "review_panel"):
            if not isinstance(assurance.get(key), dict):
                errors.append(f"RUN_MANIFEST assurance_v22 missing object: {key}")

    traceability = _load_json(payload / "templates/TRACEABILITY_MATRIX.json", "TRACEABILITY_MATRIX.json", errors)
    if traceability is not None:
        if traceability.get("schema_version") != EVIDENCE_SCHEMA_VERSION:
            errors.append("TRACEABILITY_MATRIX evidence schema must remain 2.1")
        if not isinstance(traceability.get("rows"), list) or not isinstance(traceability.get("change_impact"), list):
            errors.append("TRACEABILITY_MATRIX rows/change_impact must be lists")

    template_expectations = {
        "ADAPTER_CONTRACT.json": ("schema_version", "allowed_adapter_types", "decision_authority", "normalized_statuses"),
        "ADAPTER_RESULT.json": ("schema_version", "adapter_type", "adapter", "subject_identity", "execution", "status_mapping", "raw_evidence", "claims"),
        "ACCEPTANCE_REQUEST.json": ("schema_version", "owner_input", "preferences", "command_policy", "review_panel"),
        "CAPABILITY_REPORT.json": ("schema_version", "read_only", "repository", "risk"),
        "ACCEPTANCE_PLAN.json": ("schema_version", "target", "risk", "execution_budget", "hard_stops", "command_policy"),
        "COMMAND_LOG.json": ("schema_version", "commands"),
        "COMMAND_POLICY_REPORT.json": ("schema_version", "status", "unauthorized_execution_count", "budget_exceeded"),
        "EVIDENCE_PRIVACY_REPORT.json": ("schema_version", "status", "blocking_findings", "filesystem_issues"),
        "REVIEW_PANEL.json": ("schema_version", "rounds", "independence_claim", "open_findings"),
        "EVIDENCE_POLICY.json": ("schema_version", "classification", "retention_days", "forbidden_in_public_bundle"),
        "WAIVER_TEMPLATE.json": ("schema_version", "waiver_id", "expires_at", "non_waivable_check"),
    }
    for filename, keys in template_expectations.items():
        value = _load_json(payload / "templates" / filename, filename, errors)
        if value is not None:
            for key in keys:
                if key not in value:
                    errors.append(f"{filename} missing field: {key}")


def _interface_and_references(payload: Path, errors: list[str]) -> None:
    interface = _read_text(payload / "agents/openai.yaml", errors)
    for term in ("display_name:", "short_description:", "default_prompt:", "exactly one target project/version", "untrusted data", "exactly one *_acceptance_review_taskpack.zip"):
        if term not in interface:
            errors.append(f"agents/openai.yaml missing: {term}")

    required_by_file = {
        "references/risk-and-test-planning.md": ("风险评分不是 verdict", "变更影响选择", "预算耗尽", "停止条件"),
        "references/threat-model-and-command-safety.md": ("Instruction injection", "shell=True", "两阶段门", "Fail-closed"),
        "references/flaky-and-test-effectiveness.md": ("重试洗绿", "Test discrimination", "surviving mutant", "干净状态"),
        "references/evidence-privacy-retention.md": ("restricted", "redaction", "保留与销毁", "private key"),
        "references/review-panel-protocol.md": ("六个固定角色", "role_separated_same_model", "blocker", "不证明六个独立"),
        "references/adapters-and-portability.md": ("Adapter 不能直接写 verdict", "argv", "跨平台", "Offline"),
    }
    for rel, terms in required_by_file.items():
        content = _read_text(payload / rel, errors)
        for term in terms:
            if term not in content:
                errors.append(f"{rel} missing: {term}")


def _manifest_shape(payload: Path, errors: list[str]) -> None:
    manifest = _load_json(payload / "MANIFEST.json", "MANIFEST.json", errors)
    if manifest is not None:
        if manifest.get("skill") != "verifier" or manifest.get("skill_version") != SKILL_VERSION:
            errors.append("MANIFEST skill/version mismatch")
        entries = manifest.get("entries")
        if not isinstance(entries, list):
            errors.append("MANIFEST entries must be a list")
        else:
            paths: set[str] = set()
            for item in entries:
                if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                    errors.append("MANIFEST invalid entry")
                    continue
                if item["path"] in paths:
                    errors.append(f"MANIFEST duplicate path: {item['path']}")
                paths.add(item["path"])
                if not isinstance(item.get("size"), int) or not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
                    errors.append(f"MANIFEST invalid size/hash: {item['path']}")
    sums = _read_text(payload / "SHA256SUMS.txt", errors)
    for number, line in enumerate(sums.splitlines(), 1):
        if not re.fullmatch(r"[0-9a-f]{64}  .+", line):
            errors.append(f"SHA256SUMS.txt:{number}: invalid format")


def validate(payload: Path, mode: str = "installed") -> list[str]:
    if mode not in {"distribution", "installed"}:
        return [f"invalid mode: {mode}"]
    payload = payload.expanduser().resolve()
    errors: list[str] = []
    if not payload.is_dir():
        return [f"payload directory not found: {payload}"]
    _portable_tree(payload, errors, mode)
    if (payload / "SKILL.md").is_file():
        _frontmatter(payload, errors)
    _version(payload, errors)
    _python_files(payload, errors)
    _strict_templates(payload, errors)
    _interface_and_references(payload, errors)
    _manifest_shape(payload, errors)
    return errors


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--mode", choices=("distribution", "installed"), default="installed")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    errors = validate(args.payload, args.mode)
    result = {"ok": not errors, "payload": str(args.payload.resolve()), "mode": args.mode, "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    elif errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
    else:
        print(f"VALID: verifier {SKILL_VERSION} ({args.mode})")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
