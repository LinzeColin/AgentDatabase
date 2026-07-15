#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Any


SCHEMA_VERSION = "memory_atlas.test_value_review.v1_2_1_s04_p3_t2"
BASELINE_COMMIT = "31e217c9c"
CONFIG_PATH = Path("config/memory_atlas_test_value_review.json")
MAX_CONFIG_BYTES = 2 * 1024 * 1024
TOP_LEVEL_KEYS = {
    "schema_version",
    "task_id",
    "source_package",
    "policy",
    "baseline",
    "summary",
    "profile_commands",
    "added_paths",
    "candidates",
    "retained",
}
CANDIDATE_KEYS = {
    "path",
    "category",
    "references",
    "runtime_dependency",
    "replacement_source",
    "reason",
    "restore_method",
    "batch",
    "validation",
    "approval",
}
RETAINED_KEYS = {"path", "risk_bindings", "reason", "current_dependency"}
RISK_BINDINGS = {"user_journey", "data_integrity", "release_risk", "runner_contract"}
PROFILE_COMMANDS = {
    "fast": "npm run validate:fast",
    "sync": "npm run validate:sync",
    "ui": "npm run validate:ui",
    "release": "npm run validate:release",
}
SOURCE_PACKAGE = {
    "name": "v1.2.1_四线16Stage质量收敛升级_TaskPack.zip",
    "sha256": "db59f4db3ac02845fb3cde346a301cba64146c81c7ba19168f52c27e82ddd0f1",
}
POLICY = {
    "audit_before_delete": True,
    "delete_only_approved_candidates": True,
    "all_current_callers_migrated": True,
    "behavior_risk_replacement_required": True,
    "historical_recovery_via_git": True,
    "raw_mutation": False,
    "remote_push": False,
    "deployment": False,
    "branch_or_pr": False,
    "cache_cleanup": False,
}
BASELINE = {
    "validator_count": 177,
    "python_test_count": 51,
    "validator_bytes": 2_902_666,
}
SUMMARY = {
    "deleted_validator_count": 139,
    "deleted_python_test_count": 2,
    "retained_validator_count": 39,
    "retained_baseline_python_test_count": 49,
    "added_python_test_count": 15,
    "current_python_test_count": 64,
}
ADDED_PATHS = [
    "tests/test_memory_atlas_test_value_audit.py",
    "tests/test_memory_atlas_legacy_command_migrations.py",
    "tests/test_memory_atlas_human_plane.py",
    "tests/test_memory_atlas_zh_cn_copy_source.py",
    "apps/memory-atlas/scripts/validate_memory_atlas_semantic_readability.mjs",
    "tests/test_memory_atlas_semantic_readability.py",
    "tests/test_memory_atlas_source_registry.py",
    "tests/test_memory_atlas_codex_source_discovery.py",
    "tests/test_memory_atlas_public_raw_layout.py",
    "tests/test_memory_atlas_credential_exclusion.py",
    "tests/test_memory_atlas_raw_ledger.py",
    "tests/test_memory_atlas_archive_chunking.py",
    "tests/test_memory_atlas_archive_restore.py",
    "tests/test_memory_atlas_raw_isolation.py",
    "tests/test_memory_atlas_push_size_guard.py",
    "tests/test_memory_atlas_raw_contract_fixtures.py",
]
DELETED_TEST_REPLACEMENTS = {
    "tests/test_memory_atlas_v1_2_product_identity_contract.py": "npm run validate:ui",
    "tests/test_memory_atlas_visual_acceptance.py": (
        "python3 -m unittest tests.test_memory_atlas_acceptance_audit -q"
    ),
}
CANDIDATE_VALIDATION = [
    "python3 -m unittest tests.test_memory_atlas_test_value_audit -q",
    "python3 -m unittest discover -s OpenAIDatabase/tests -q",
]
EXECUTABLE_SUFFIXES = {".py", ".cjs", ".mjs", ".js", ".sh", ".yaml", ".yml", ".toml"}
IGNORED_REFERENCE_PATHS = {
    "scripts/audit_memory_atlas_test_value.py",
    "tests/test_memory_atlas_test_value_audit.py",
}


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value or "\\" in value:
        return None
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != value:
        return None
    return value


def _load_json_regular_file(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode):
            raise ValueError(f"review config is not a regular file: {path}")
        if metadata.st_size > MAX_CONFIG_BYTES:
            raise ValueError(f"review config exceeds {MAX_CONFIG_BYTES} bytes")
        payload = os.read(fd, MAX_CONFIG_BYTES + 1)
    finally:
        os.close(fd)
    try:
        loaded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"review config is not strict UTF-8 JSON: {exc}") from exc
    if not isinstance(loaded, dict):
        raise ValueError("review config root must be an object")
    return loaded


def load_test_value_review(database_dir: Path, path: Path | None = None) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    target = path if path is not None else database_dir / CONFIG_PATH
    return _load_json_regular_file(target)


def _current_validator_paths(database_dir: Path) -> set[str]:
    root = database_dir / "apps/memory-atlas/scripts"
    return {
        path.relative_to(database_dir).as_posix()
        for path in root.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and path.name.startswith("validate_")
        and path.suffix in {".cjs", ".mjs"}
    }


def _current_test_paths(database_dir: Path) -> set[str]:
    root = database_dir / "tests"
    return {
        path.relative_to(database_dir).as_posix()
        for path in root.iterdir()
        if path.is_file()
        and not path.is_symlink()
        and path.name.startswith("test_")
        and path.suffix == ".py"
    }


def _executable_files(database_dir: Path) -> list[Path]:
    files: set[Path] = set()
    for root in (database_dir / "scripts", database_dir / "tests", database_dir / "apps/memory-atlas/scripts"):
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if path.is_file() and not path.is_symlink() and path.suffix in EXECUTABLE_SUFFIXES:
                files.add(path)
    for relative in (
        "apps/memory-atlas/package.json",
        "config/memory_atlas_validator_profiles.json",
    ):
        path = database_dir / relative
        if path.is_file() and not path.is_symlink():
            files.add(path)
    return sorted(files)


def find_executable_references(database_dir: Path, deleted_basenames: set[str]) -> dict[str, list[str]]:
    database_dir = database_dir.resolve()
    references: dict[str, list[str]] = {}
    for path in _executable_files(database_dir):
        relative = path.relative_to(database_dir).as_posix()
        if relative in IGNORED_REFERENCE_PATHS:
            continue
        try:
            source = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        for basename in sorted(deleted_basenames):
            if basename in source:
                references.setdefault(basename, []).append(relative)
    return references


def _baseline_asset_inventory(database_dir: Path) -> dict[str, int]:
    repo_root = database_dir.resolve().parent
    result = subprocess.run(
        [
            "git",
            "ls-tree",
            "-r",
            "-l",
            BASELINE_COMMIT,
            "--",
            "OpenAIDatabase/apps/memory-atlas/scripts",
            "OpenAIDatabase/tests",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        detail = result.stderr.strip() or "unknown git ls-tree failure"
        raise ValueError(f"cannot verify baseline commit {BASELINE_COMMIT}: {detail}")
    assets: dict[str, int] = {}
    prefix = "OpenAIDatabase/"
    for line in result.stdout.splitlines():
        metadata, path = line.split("\t", 1)
        size = int(metadata.rsplit(" ", 1)[1])
        if not path.startswith(prefix):
            continue
        relative = path[len(prefix) :]
        candidate = Path(relative)
        is_validator = (
            candidate.parent.as_posix() == "apps/memory-atlas/scripts"
            and candidate.name.startswith("validate_")
            and candidate.suffix in {".cjs", ".mjs"}
        )
        is_test = (
            candidate.parent.as_posix() == "tests"
            and candidate.name.startswith("test_")
            and candidate.suffix == ".py"
        )
        if is_validator or is_test:
            assets[relative] = size
    return assets


def _validate_candidate(item: object, index: int, errors: list[str]) -> str | None:
    if not isinstance(item, dict):
        errors.append(f"candidate {index} must be an object")
        return None
    if set(item) != CANDIDATE_KEYS:
        errors.append(f"candidate keys mismatch at index {index}")
    relative = _safe_relative_path(item.get("path"))
    label = relative or f"index {index}"
    if relative is None:
        errors.append(f"candidate path is invalid: {label}")
    if item.get("category") != "delete" or item.get("approval") != "approved":
        errors.append(f"candidate {label} is not an approved deletion")
    for key in ("runtime_dependency", "replacement_source", "reason", "restore_method", "batch"):
        if not isinstance(item.get(key), str) or not item.get(key, "").strip():
            errors.append(f"candidate {label} requires {key}")
    for key in ("references", "validation"):
        value = item.get(key)
        if not isinstance(value, list) or not value or not all(isinstance(row, str) and row for row in value):
            errors.append(f"candidate {label} requires non-empty {key}")
    if relative is not None:
        git_reference = f"git:{BASELINE_COMMIT}:{relative}"
        restore_method = (
            f"git restore --source={BASELINE_COMMIT} -- OpenAIDatabase/{relative}"
        )
        if relative.startswith("apps/memory-atlas/scripts/validate_") and relative.endswith(
            (".cjs", ".mjs")
        ):
            expected_references = [git_reference, "config/atlasctl_script_migrations.json"]
            expected_replacement = "npm run validate:release"
            expected_batch = "s04_p3_t2_historical_validators"
        elif relative in DELETED_TEST_REPLACEMENTS:
            expected_references = [git_reference, "tests/test_memory_atlas_test_value_audit.py"]
            expected_replacement = DELETED_TEST_REPLACEMENTS[relative]
            expected_batch = "s04_p3_t2_source_marker_tests"
        else:
            expected_references = []
            expected_replacement = ""
            expected_batch = ""
            errors.append(f"candidate path is outside the approved asset classes: {relative}")
        if item.get("references") != expected_references:
            errors.append(f"candidate {relative} references do not bind the baseline path")
        if item.get("restore_method") != restore_method:
            errors.append(f"candidate {relative} restore_method mismatch")
        if item.get("replacement_source") != expected_replacement:
            errors.append(f"candidate {relative} replacement_source mismatch")
        if item.get("batch") != expected_batch:
            errors.append(f"candidate {relative} batch mismatch")
        if item.get("validation") != CANDIDATE_VALIDATION:
            errors.append(f"candidate {relative} validation mismatch")
    return relative


def _validate_retained(item: object, index: int, database_dir: Path, errors: list[str]) -> str | None:
    if not isinstance(item, dict):
        errors.append(f"retained {index} must be an object")
        return None
    if set(item) != RETAINED_KEYS:
        errors.append(f"retained keys mismatch at index {index}")
    relative = _safe_relative_path(item.get("path"))
    label = relative or f"index {index}"
    if relative is None:
        errors.append(f"retained path is invalid: {label}")
        return None
    bindings = item.get("risk_bindings")
    if (
        not isinstance(bindings, list)
        or not bindings
        or not all(isinstance(row, str) and row in RISK_BINDINGS for row in bindings)
    ):
        errors.append(f"retained {label} requires valid risk_bindings")
    for key in ("reason", "current_dependency"):
        if not isinstance(item.get(key), str) or not item.get(key, "").strip():
            errors.append(f"retained {label} requires {key}")
    path = database_dir / relative
    if path.is_symlink() or not path.is_file():
        errors.append(f"retained path is missing or symlinked: {label}")
    return relative


def audit_test_value_review(payload: dict[str, Any], database_dir: Path) -> list[str]:
    database_dir = database_dir.resolve()
    errors: list[str] = []
    if set(payload) != TOP_LEVEL_KEYS:
        errors.append("review top-level keys mismatch")
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("review schema_version mismatch")
    if payload.get("task_id") != "S04-P3-T2":
        errors.append("review task_id mismatch")
    if payload.get("source_package") != SOURCE_PACKAGE:
        errors.append("source package identity mismatch")
    if payload.get("policy") != POLICY:
        errors.append("deletion policy must match the fail-closed Task boundary")
    if payload.get("baseline") != BASELINE:
        errors.append("baseline mismatch")
    if payload.get("summary") != SUMMARY:
        errors.append("summary mismatch")
    if payload.get("profile_commands") != PROFILE_COMMANDS:
        errors.append("profile command set mismatch")
    if payload.get("added_paths") != ADDED_PATHS:
        errors.append("added path set mismatch")

    candidates = payload.get("candidates")
    if not isinstance(candidates, list):
        errors.append("candidates must be a list")
        candidates = []
    candidate_paths = [_validate_candidate(item, index, errors) for index, item in enumerate(candidates)]
    candidate_paths = [path for path in candidate_paths if path is not None]
    if len(candidate_paths) != len(set(candidate_paths)):
        errors.append("candidate paths are duplicated")
    deleted_validators = {path for path in candidate_paths if path.startswith("apps/memory-atlas/scripts/")}
    deleted_tests = {path for path in candidate_paths if path.startswith("tests/")}
    if len(deleted_validators) != SUMMARY["deleted_validator_count"]:
        errors.append("deleted validator count mismatch")
    if len(deleted_tests) != SUMMARY["deleted_python_test_count"]:
        errors.append("deleted Python test count mismatch")
    for relative in candidate_paths:
        path = database_dir / relative
        if path.exists() or path.is_symlink():
            errors.append(f"approved deletion still exists: {relative}")

    retained = payload.get("retained")
    if not isinstance(retained, list):
        errors.append("retained must be a list")
        retained = []
    retained_paths = [_validate_retained(item, index, database_dir, errors) for index, item in enumerate(retained)]
    retained_paths = [path for path in retained_paths if path is not None]
    if len(retained_paths) != len(set(retained_paths)):
        errors.append("retained paths are duplicated")
    actual_validators = _current_validator_paths(database_dir)
    actual_tests = _current_test_paths(database_dir)
    actual_paths = actual_validators | actual_tests
    if set(retained_paths) != actual_paths:
        errors.append("retained set does not equal current validator/test files")
    if len(actual_validators) != SUMMARY["retained_validator_count"]:
        errors.append("current validator count mismatch")
    if len(actual_tests) != SUMMARY["current_python_test_count"]:
        errors.append("current Python test count mismatch")
    baseline_test_paths = set(retained_paths) - set(ADDED_PATHS)
    if len([path for path in baseline_test_paths if path.startswith("tests/")]) != SUMMARY["retained_baseline_python_test_count"]:
        errors.append("retained baseline Python test count mismatch")
    if len(candidate_paths) + len(baseline_test_paths) != BASELINE["validator_count"] + BASELINE["python_test_count"]:
        errors.append("baseline candidate/retained partition mismatch")
    baseline_assets = _baseline_asset_inventory(database_dir)
    reviewed_baseline_paths = set(candidate_paths) | baseline_test_paths
    if reviewed_baseline_paths != set(baseline_assets):
        errors.append("reviewed baseline paths do not equal the Git baseline asset set")
    baseline_validator_bytes = sum(
        size
        for path, size in baseline_assets.items()
        if path.startswith("apps/memory-atlas/scripts/")
    )
    if baseline_validator_bytes != BASELINE["validator_bytes"]:
        errors.append("Git baseline validator byte count mismatch")

    references = find_executable_references(database_dir, {Path(path).name for path in candidate_paths})
    for basename, callers in references.items():
        errors.append(f"deleted path still has executable references: {basename}: {callers}")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit Memory Atlas validator/test value review")
    parser.add_argument("--database-dir", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--config", type=Path)
    args = parser.parse_args()
    try:
        payload = load_test_value_review(args.database_dir, args.config)
        errors = audit_test_value_review(payload, args.database_dir)
    except (OSError, ValueError) as exc:
        errors = [str(exc)]
    result = {
        "schema_version": "memory_atlas.test_value_audit_result.v1_2_1_s04_p3_t2",
        "task_id": "S04-P3-T2",
        "status": "PASS" if not errors else "FAIL",
        "errors": errors,
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    sys.exit(main())
