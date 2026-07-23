#!/usr/bin/env python3
"""Validate the Verifier v2.1 Product-Design-aligned skill payload using stdlib only."""

from __future__ import annotations

import argparse
import ast
import json
import re
import stat
import sys
from pathlib import Path
from typing import Any, Optional


EXPECTED_FILES = {
    "SKILL.md",
    "agents/openai.yaml",
    "references/acceptance-contract.md",
    "references/ai-system-acceptance.md",
    "references/coverage-model.md",
    "references/evidence-integrity.md",
    "references/execution-playbook.md",
    "references/human-acceptance.md",
    "references/product-design-taskpack-contract.md",
    "references/release-assurance.md",
    "references/safety-policy.md",
    "references/tool-routing.md",
    "references/verdict-and-reporting.md",
    "scripts/finalize_acceptance_run.py",
    "scripts/ingest_taskpack.py",
    "scripts/init_acceptance_run.py",
    "scripts/make_gallery.py",
    "scripts/package_review_taskpack.py",
    "scripts/validate_pack.py",
    "templates/ACCEPTANCE_REQUEST.yaml",
    "templates/AI_EVAL_MATRIX.md",
    "templates/DEFECT_REPORT.md",
    "templates/GALLERY_PAIRS.csv",
    "templates/HUMAN_JOURNEY.md",
    "templates/MODIFICATION_REPORT.md",
    "templates/RELEASE_ASSURANCE.md",
    "templates/RUN_MANIFEST.yaml",
    "templates/TEST_MATRIX.md",
    "templates/TRACEABILITY_MATRIX.json",
    "templates/VERDICT_TEMPLATE.md",
    "tests/test_tools.py",
}
FRONTMATTER_RE = re.compile(r"\A---\n(?P<body>.*?)\n---\n", re.DOTALL)
LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
FORBIDDEN_IMPORTS = {"yaml", "requests", "pandas", "numpy", "PIL"}
ALLOWED_TASKPACK_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}


def _read_text(path: Path, errors: list[str]) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        errors.append(f"cannot read {path.name}: {error}")
        return ""


def require_terms(path: Path, terms: tuple[str, ...], errors: list[str]) -> None:
    if not path.is_file():
        return
    content = _read_text(path, errors)
    for term in terms:
        if term not in content:
            errors.append(f"{path.relative_to(path.parents[1])} missing required contract term: {term}")


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


def _validate_portable_tree(payload: Path, errors: list[str]) -> None:
    actual_files: set[str] = set()
    for path in payload.rglob("*"):
        relative = path.relative_to(payload)
        relative_text = relative.as_posix()
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            errors.append(f"cannot stat payload entry {relative_text}: {error}")
            continue
        if stat.S_ISLNK(mode):
            errors.append(f"symlink forbidden in portable payload: {relative_text}")
            continue
        if stat.S_ISREG(mode):
            actual_files.add(relative_text)
        elif not stat.S_ISDIR(mode):
            errors.append(f"non-regular payload entry forbidden: {relative_text}")
        if "__pycache__" in relative.parts or path.suffix in {".pyc", ".pyo"}:
            errors.append(f"compiled/cache artifact forbidden: {relative_text}")
        if any(part in {".", ".."} for part in relative.parts):
            errors.append(f"non-portable path forbidden: {relative_text}")
        if "\\" in relative_text or "\x00" in relative_text:
            errors.append(f"non-portable filename forbidden: {relative_text!r}")

    missing = sorted(EXPECTED_FILES - actual_files)
    extra = sorted(actual_files - EXPECTED_FILES)
    for relative in missing:
        errors.append(f"missing required file: {relative}")
    for relative in extra:
        errors.append(f"unexpected payload file: {relative}")

    lowered: dict[str, str] = {}
    for relative in sorted(actual_files):
        key = relative.casefold()
        prior = lowered.get(key)
        if prior is not None and prior != relative:
            errors.append(f"case-colliding payload paths: {prior} / {relative}")
        lowered[key] = relative


def _validate_frontmatter(skill_path: Path, errors: list[str]) -> None:
    content = _read_text(skill_path, errors)
    match = FRONTMATTER_RE.match(content)
    if match is None:
        errors.append("SKILL.md has no valid YAML frontmatter block")
        return
    frontmatter = match.group("body")
    if not re.search(r"(?m)^name:\s*verifier\s*$", frontmatter):
        errors.append("SKILL.md frontmatter name must be verifier")
    description_match = re.search(r"(?m)^description:\s*(.+)$", frontmatter)
    if description_match is None or len(description_match.group(1).strip()) < 180:
        errors.append("SKILL.md description is missing or too vague")
    if "Skill 1" not in frontmatter or "Never alter" not in frontmatter:
        errors.append("SKILL.md frontmatter must preserve the Skill 1 read-only boundary")


def _validate_links(payload: Path, skill_path: Path, errors: list[str]) -> None:
    content = _read_text(skill_path, errors)
    for target in LINK_RE.findall(content):
        if "://" in target or target.startswith("#"):
            continue
        clean = target.split("#", 1)[0]
        linked = (skill_path.parent / clean).resolve()
        try:
            linked.relative_to(payload)
        except ValueError:
            errors.append(f"SKILL.md link escapes payload: {target}")
            continue
        if not linked.is_file():
            errors.append(f"SKILL.md link target missing or non-file: {target}")


def _expect_object(parent: dict[str, Any], key: str, label: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{label} missing object: {key}")
        return {}
    return value


def _expect_list(parent: dict[str, Any], key: str, label: str, errors: list[str]) -> list[Any]:
    value = parent.get(key)
    if not isinstance(value, list):
        errors.append(f"{label} missing list: {key}")
        return []
    return value


def _validate_manifest_template(path: Path, errors: list[str]) -> None:
    manifest = _load_json(path, "RUN_MANIFEST.yaml", errors)
    if manifest is None:
        return
    if manifest.get("schema_version") != "2.1":
        errors.append("RUN_MANIFEST schema_version must be 2.1")

    objects: dict[str, dict[str, Any]] = {}
    for key in (
        "run",
        "scope",
        "taskpack",
        "traceability",
        "subject",
        "baseline",
        "environment",
        "release",
        "operations",
        "ai_system",
        "evidence",
        "verdict",
    ):
        objects[key] = _expect_object(manifest, key, "RUN_MANIFEST", errors)
    for key in ("tools", "commands", "inputs", "results", "findings", "waivers", "abort_or_incidents"):
        _expect_list(manifest, key, "RUN_MANIFEST", errors)

    scope = objects["scope"]
    if scope.get("mode") != "single-project":
        errors.append("RUN_MANIFEST scope.mode must be single-project")
    if scope.get("verdict_scope") != "target-project-only":
        errors.append("RUN_MANIFEST scope.verdict_scope must be target-project-only")

    run = objects["run"]
    _expect_list(run, "independent_pass_records", "RUN_MANIFEST.run", errors)

    taskpack = objects["taskpack"]
    for key in (
        "files",
        "acceptance_ids",
        "task_ids",
        "drift_items",
        "authorization_evidence_paths",
        "integrity_evidence_paths",
        "compatibility_evidence_paths",
        "drift_evidence_paths",
        "evidence_paths",
    ):
        _expect_list(taskpack, key, "RUN_MANIFEST.taskpack", errors)
    for key in ("integrity_status", "compatibility_status", "drift_status"):
        if taskpack.get(key) not in ALLOWED_TASKPACK_STATUSES:
            errors.append(f"RUN_MANIFEST taskpack.{key} has invalid default status")
    for key in (
        "authorization_reference",
        "source_snapshot_path",
        "source_snapshot_sha256",
        "source_snapshot_size",
        "source_file_count",
        "pack_digest_sha256",
        "contract_digest_sha256",
        "authorized_pack_digest_sha256",
        "reason_if_absent",
    ):
        if key not in taskpack:
            errors.append(f"RUN_MANIFEST missing field: taskpack.{key}")
    if not isinstance(taskpack.get("source_snapshot_size"), int):
        errors.append("RUN_MANIFEST taskpack.source_snapshot_size must default to an integer")
    if not isinstance(taskpack.get("source_file_count"), int):
        errors.append("RUN_MANIFEST taskpack.source_file_count must default to an integer")

    traceability = objects["traceability"]
    for key in ("matrix_path", "status", "reason"):
        if key not in traceability:
            errors.append(f"RUN_MANIFEST missing field: traceability.{key}")
    _expect_list(traceability, "evidence_paths", "RUN_MANIFEST.traceability", errors)
    if traceability.get("matrix_path") != "TRACEABILITY_MATRIX.json":
        errors.append("RUN_MANIFEST traceability.matrix_path must be TRACEABILITY_MATRIX.json")

    subject = objects["subject"]
    for key in (
        "source_snapshot_sha256",
        "source_snapshot_evidence_paths",
        "source_to_artifact_mapping_evidence",
        "deployment_mapping_evidence_paths",
        "artifact_sha256",
        "image_digest",
        "deployment_identity",
    ):
        if key not in subject:
            errors.append(f"RUN_MANIFEST missing field: subject.{key}")
    for key in (
        "source_snapshot_evidence_paths",
        "source_to_artifact_mapping_evidence",
        "deployment_mapping_evidence_paths",
    ):
        _expect_list(subject, key, "RUN_MANIFEST.subject", errors)

    release = objects["release"]
    if "candidate_identity" not in release:
        errors.append("RUN_MANIFEST missing field: release.candidate_identity")
    _expect_object(release, "rollback_or_rollforward", "RUN_MANIFEST.release", errors)
    _expect_object(release, "bake", "RUN_MANIFEST.release", errors)
    _expect_object(release, "post_deploy", "RUN_MANIFEST.release", errors)

    ai = objects["ai_system"]
    for key in (
        "trial_records",
        "success_threshold",
        "observed_pass_rate",
        "safety_gate_status",
        "safety_evidence_paths",
        "evaluator_independence",
    ):
        if key not in ai:
            errors.append(f"RUN_MANIFEST missing field: ai_system.{key}")
    _expect_list(ai, "trial_records", "RUN_MANIFEST.ai_system", errors)
    _expect_list(ai, "safety_evidence_paths", "RUN_MANIFEST.ai_system", errors)
    independence = _expect_object(ai, "evaluator_independence", "RUN_MANIFEST.ai_system", errors)
    for key in (
        "primary_grader_type",
        "generator_is_sole_judge",
        "cross_model_review",
        "blind_evaluation",
        "independent_evaluator_ids",
        "disagreement_policy",
        "evidence_paths",
    ):
        if key not in independence:
            errors.append(f"RUN_MANIFEST missing field: ai_system.evaluator_independence.{key}")
    if independence.get("generator_is_sole_judge") is not False:
        errors.append("RUN_MANIFEST AI template must default generator_is_sole_judge to false")
    _expect_list(independence, "independent_evaluator_ids", "RUN_MANIFEST.ai_system.evaluator_independence", errors)
    _expect_list(independence, "evidence_paths", "RUN_MANIFEST.ai_system.evaluator_independence", errors)


def _validate_traceability_template(path: Path, errors: list[str]) -> None:
    matrix = _load_json(path, "TRACEABILITY_MATRIX.json", errors)
    if matrix is None:
        return
    if matrix.get("schema_version") != "2.1":
        errors.append("TRACEABILITY_MATRIX schema_version must be 2.1")
    for key in ("target_project_name", "subject_identity", "taskpack_digest_sha256"):
        if key not in matrix:
            errors.append(f"TRACEABILITY_MATRIX missing field: {key}")
    _expect_list(matrix, "rows", "TRACEABILITY_MATRIX", errors)
    _expect_list(matrix, "change_impact", "TRACEABILITY_MATRIX", errors)
    note = matrix.get("_format_note", "")
    for term in ("Acceptance ID", "Task Graph", "RUN_MANIFEST.results", "change_impact"):
        if term not in note:
            errors.append(f"TRACEABILITY_MATRIX format note missing: {term}")


def _validate_python(path: Path, errors: list[str]) -> None:
    try:
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        tree = ast.parse(source, filename=str(path))
    except (OSError, UnicodeError, SyntaxError) as error:
        errors.append(f"invalid Python {path.name}: {error}")
        return
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = {alias.name.split(".", 1)[0] for alias in node.names}
        elif isinstance(node, ast.ImportFrom):
            names = {str(node.module).split(".", 1)[0]} if node.module else set()
        else:
            continue
        bad = names & FORBIDDEN_IMPORTS
        if bad:
            errors.append(f"{path.name} imports non-stdlib dependency: {sorted(bad)}")


def validate(payload: Path) -> list[str]:
    payload = payload.expanduser().resolve()
    errors: list[str] = []
    if not payload.is_dir():
        return [f"payload directory not found: {payload}"]

    _validate_portable_tree(payload, errors)

    skill_path = payload / "SKILL.md"
    if skill_path.is_file():
        _validate_frontmatter(skill_path, errors)
        _validate_links(payload, skill_path, errors)
        require_terms(
            skill_path,
            (
                "一次只裁决一个",
                "最小验收闭包",
                "Product-Design-Taskpack",
                "只读",
                "七个语义角色",
                "完整任务包",
                "TASKPACK_SOURCE_SNAPSHOT.zip",
                "pack_digest_sha256",
                "contract_digest_sha256",
                "--authorized-pack-digest",
                "Acceptance/Task IDs",
                "integrity_evidence_paths",
                "compatibility_evidence_paths",
                "drift_evidence_paths",
                "source snapshot → build → artifact/image → deployment",
                "TRACEABILITY_MATRIX.json",
                "locked Task IDs",
                "change_impact",
                "release_candidate",
                "post_deploy",
                "generator_is_sole_judge",
                "cross-model review",
                "blind evaluation",
                "finalize_acceptance_run.py",
                "EVIDENCE_INDEX.json",
                "ACCEPTANCE_ATTESTATION.intoto.json",
                "package_review_taskpack.py",
                "唯一默认文件交付物",
                "acceptance_review_taskpack.zip",
                "AI/Agent",
                "不可豁免",
                "DELIVERY_CONTENT_MISMATCH",
                "ACTION: ESCALATE",
                "NOT_RUN",
                "load",
                "stress",
                "spike",
                "soak",
                "breakpoint",
            ),
            errors,
        )

    openai_yaml = payload / "agents/openai.yaml"
    require_terms(
        openai_yaml,
        (
            "interface:",
            "display_name:",
            "short_description:",
            "default_prompt:",
            "exactly one target project",
            "without altering Skill 1",
            "Product-Design-Taskpack read-only",
            "complete relevant taskpack",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
            "normalized full-pack digest",
            "separate seven-role contract digest",
            "Acceptance IDs and Task IDs",
            "integrity, compatibility and drift evidence",
            "change_impact",
            "exact Subject",
            "cross-model blind AI grading",
            "in-toto attestation",
            "exactly one *_acceptance_review_taskpack.zip",
            "link only that single ZIP",
        ),
        errors,
    )

    require_terms(
        payload / "references/product-design-taskpack-contract.md",
        (
            "只读接入契约",
            "完整包与七角色双锁",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
            "pack_digest_sha256",
            "contract_digest_sha256",
            "source_archive_sha256",
            "--authorized-pack-digest",
            "Acceptance/Task IDs",
            "integrity_evidence_paths",
            "compatibility_evidence_paths",
            "drift_evidence_paths",
            "哈希一致只说明 bytes 一致",
            "Task ID 必须存在于锁定 Task Graph",
            "change_impact",
            "DELIVERY_CONTENT_MISMATCH",
        ),
        errors,
    )
    require_terms(
        payload / "references/ai-system-acceptance.md",
        (
            "generator_is_sole_judge=false",
            "cross_model_review=true",
            "blind_evaluation=true",
            "至少一个 evaluator 与生成模型不同",
            "每个声明任务切片至少3个独立trial",
            "不能用总体平均掩盖关键切片失败",
            "真实世界 Oracle",
        ),
        errors,
    )
    require_terms(
        payload / "references/evidence-integrity.md",
        (
            "source snapshot",
            "artifact",
            "deployment",
            "attestation",
            "签名",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
            "pack_digest_sha256",
            "contract_digest_sha256",
        ),
        errors,
    )
    require_terms(
        payload / "references/release-assurance.md",
        ("candidate", "control", "bake", "abort", "rollback", "post_deploy"),
        errors,
    )

    request = payload / "templates/ACCEPTANCE_REQUEST.yaml"
    require_terms(
        request,
        (
            'schema_version: "2.1"',
            "owner_input:",
            "product_design_taskpack:",
            "authorized_pack_digest_sha256:",
            "pack_digest_sha256:",
            "contract_digest_sha256:",
            "source_snapshot_sha256:",
            "source_file_count:",
            "target_project:",
            "decision_scope:",
            "verifier_discovered:",
            "acceptance_closure:",
            "acceptance_ids:",
            "task_ids:",
            "change_impact_count:",
            "ai_system:",
            "independent_evaluator_preference:",
        ),
        errors,
    )

    manifest_path = payload / "templates/RUN_MANIFEST.yaml"
    _validate_manifest_template(manifest_path, errors)
    _validate_traceability_template(payload / "templates/TRACEABILITY_MATRIX.json", errors)

    require_terms(
        payload / "templates/VERDICT_TEMPLATE.md",
        (
            "你只需要先看这里",
            "结论适用范围",
            "证据封存",
            "release_candidate PASS",
            "Taskpack",
            "Traceability",
            "full-pack SHA-256",
            "seven-role contract SHA-256",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
        ),
        errors,
    )
    require_terms(
        payload / "templates/DEFECT_REPORT.md",
        ("直接交给开发线程的任务", "最少复验闭包", "自动扩大复验", "Non-waivable", "Taskpack / Oracle drift"),
        errors,
    )
    require_terms(
        payload / "templates/RELEASE_ASSURANCE.md",
        ("身份链", "运营就绪", "渐进发布", "Post-deploy", "Taskpack / release contract drift"),
        errors,
    )
    require_terms(
        payload / "templates/AI_EVAL_MATRIX.md",
        (
            "Task × Trial",
            "Outcome / world-state grader",
            "Generator is sole judge",
            "Independent evaluator IDs",
            "Cross-model review",
            "Blind evaluation",
            "每个声明切片至少3个独立trial",
            "总体平均不得掩盖切片失败",
            "Prompt injection",
            "world state",
        ),
        errors,
    )
    require_terms(
        payload / "templates/TEST_MATRIX.md",
        (
            "Acceptance",
            "Task IDs",
            "Subject",
            "Change impact",
            "Evidence",
            "full-pack digest",
            "contract digest",
            "source snapshot",
        ),
        errors,
    )

    scripts_dir = payload / "scripts"
    if scripts_dir.is_dir():
        for script in sorted(scripts_dir.glob("*.py")):
            _validate_python(script, errors)

    require_terms(
        payload / "scripts/init_acceptance_run.py",
        ("TRACEABILITY_MATRIX.json", "AI_EVAL_MATRIX.md", "RELEASE_ASSURANCE.md", "RUN_MANIFEST.yaml", "taskpack"),
        errors,
    )
    require_terms(
        payload / "scripts/ingest_taskpack.py",
        (
            "authorized-pack-digest",
            "acceptance_ids",
            "task_ids",
            "ROLE_ALIASES",
            "role-stable",
            "duplicate/case-colliding ZIP member",
            "encrypted",
            "symlink",
            "path traversal",
            "taskpack-lock.json",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
            "source_files",
            "source_snapshot_sha256",
            "contract_digest_sha256",
            "_source_tree_digest",
        ),
        errors,
    )
    require_terms(
        payload / "scripts/finalize_acceptance_run.py",
        (
            "EVIDENCE_INDEX.json",
            "FINAL_DECISION.json",
            "ACCEPTANCE_ATTESTATION.intoto.json",
            "NON_WAIVABLE_CATEGORIES",
            "DELIVERY_CONTENT_MISMATCH",
            "TASKPACK_INTEGRITY",
            "ACCEPTANCE_ORACLE_DRIFT",
            "TRACEABILITY_GAP",
            "PASS_WITH_RISKS",
            "candidate_identity",
            "source_snapshot_sha256",
            "independent_pass_records",
            "trial_records",
            "success_threshold",
            "generator_is_sole_judge",
            "cross_model_review",
            "blind_evaluation",
            "independent_evaluator_ids",
            "AI task slice",
            "compatibility_evidence_paths",
            "drift_evidence_paths",
            "change_impact",
            "TASKPACK_SOURCE_SNAPSHOT.zip",
            "source_files",
            "contract_digest_sha256",
            "_canonical_source_tree_digest",
            "taskpack_source_snapshot_sha256",
        ),
        errors,
    )
    require_terms(
        payload / "scripts/package_review_taskpack.py",
        (
            "FINALIZER.verify",
            "README_FIRST.md",
            "acceptance_review_taskpack.zip",
            "FINAL_DECISION.json",
            "ACCEPTANCE_ATTESTATION.intoto.json",
            "SHA256SUMS.txt",
            "refusing to overwrite",
            "symlink forbidden",
            "evidence_root_sha256",
        ),
        errors,
    )

    return errors


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("payload", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    errors = validate(args.payload)
    result = {"ok": not errors, "payload": str(args.payload.resolve()), "errors": errors}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif errors:
        print("INVALID")
        for error in errors:
            print(f"- {error}")
    else:
        print("VALID: verifier v2.1 Product-Design-aligned payload")
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
