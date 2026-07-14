"""Validation for the tracked Memory Atlas script migration map."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path, PurePosixPath
from typing import Any


MIGRATION_MAP_PATH = Path("config/atlasctl_script_migrations.json")
SCHEMA_VERSION = "memory_atlas.script_migrations.v1_2_1_s04_p2_t3"
TASK_ID = "S04-P2-T3"
EXPECTED_FAMILIES = {"build", "sync", "audit", "validator"}
EXPECTED_ROOTS = ("scripts", "apps/memory-atlas/scripts")
EXPECTED_KEYWORDS = ("build", "sync", "audit", "validate")
EXPECTED_SUFFIXES = (".py", ".cjs", ".mjs", ".js", ".sh")
EXPECTED_FAMILY_KEYWORDS = (
    ("build", "build"),
    ("sync", "sync"),
    ("audit", "audit"),
    ("validator", "validate"),
)
BASELINE_SCOPED_SCRIPT_COUNT = 208
BASELINE_PATH_MANIFEST_SHA256 = "1d59897596ab7f74be2afd3478015b8533a7f6b6fb69d054e4006fb9e0ea2cd4"
CONSOLIDATED_MODULES = (
    "scripts/memory_atlas_cli/analyze.py",
    "scripts/memory_atlas_cli/apply.py",
    "scripts/memory_atlas_cli/build.py",
    "scripts/memory_atlas_cli/push.py",
    "scripts/memory_atlas_cli/sync.py",
)
RETAINED_STATUSES = {
    "retained_unique_implementation",
    "retained_partial_cli_coverage",
    "retained_no_equivalent_command",
    "profiled_in_s04_p3_t1",
}
REQUIRED_PROFILE_CONSOLIDATION = {
    "task_id": "S04-P3-T1",
    "status": "completed_local_only",
    "public_profile_count": 4,
    "public_profiles": ["fast", "sync", "ui", "release"],
}
REQUIRED_DELETION_POLICY = {
    "task_only_files_may_be_deleted_now": True,
    "shared_or_active_files_deferred_until_full_project_cleanup": True,
    "equivalent_command_required": True,
    "equivalence_test_required": True,
    "all_callers_migrated_required": True,
    "behavior_parity_or_approved_low_value_retirement_required": True,
}
REQUIRED_SAFETY = {
    "raw_mutation": False,
    "remote_push": False,
    "deployment": False,
    "branch_or_pr": False,
    "cache_cleanup": False,
}
REQUIRED_RETIREMENT_ASSERTIONS = {
    "approved_deletion_schema",
    "baseline_asset_identity",
    "all_current_callers_migrated",
    "risk_replacement",
}
LOW_VALUE_RETIREMENT_REVIEW = "config/memory_atlas_test_value_review.json"
RETAINED_DEFAULT_DELETION_BLOCKER = "equivalent_command_callers_and_behavior_parity_not_all_proven"


class ScriptMigrationError(RuntimeError):
    pass


def load_script_migration_map(database_dir: Path) -> dict[str, Any]:
    path = database_dir.resolve() / MIGRATION_MAP_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ScriptMigrationError(f"cannot load script migration map: {path}") from exc
    if not isinstance(payload, dict):
        raise ScriptMigrationError("script migration map must be a JSON object")
    return payload


def _safe_relative_path(value: object) -> str | None:
    if not isinstance(value, str) or not value:
        return None
    path = PurePosixPath(value)
    if path.is_absolute() or ".." in path.parts:
        return None
    return path.as_posix()


def _inside_roots(relative: str, roots: tuple[str, ...]) -> bool:
    return any(relative.startswith(f"{root}/") for root in roots)


def _matched_families(relative: str) -> list[str]:
    name = PurePosixPath(relative).name
    return [family for family, keyword in EXPECTED_FAMILY_KEYWORDS if keyword in name]


def _is_scoped_script(relative: str) -> bool:
    path = PurePosixPath(relative)
    return _inside_roots(relative, EXPECTED_ROOTS) and path.suffix in EXPECTED_SUFFIXES and bool(
        _matched_families(relative)
    )


def _path_manifest_sha256(paths: set[str]) -> str:
    manifest = "".join(f"{path}\n" for path in sorted(paths))
    return hashlib.sha256(manifest.encode("utf-8")).hexdigest()


def _scoped_inventory(database_dir: Path) -> tuple[list[Path], int, list[str]]:
    errors: list[str] = []
    files: list[Path] = []
    for relative_root in EXPECTED_ROOTS:
        root = database_dir / relative_root
        if root.is_symlink() or not root.is_dir():
            errors.append(f"inventory root is missing or symlinked: {relative_root}")
            continue
        for path in root.iterdir():
            if path.is_symlink():
                if path.suffix in EXPECTED_SUFFIXES and any(keyword in path.name for keyword in EXPECTED_KEYWORDS):
                    errors.append(f"inventory script cannot be a symlink: {path.relative_to(database_dir).as_posix()}")
                continue
            if path.is_file() and path.suffix in EXPECTED_SUFFIXES and any(
                keyword in path.name for keyword in EXPECTED_KEYWORDS
            ):
                files.append(path)
    hashes: dict[str, list[str]] = defaultdict(list)
    for path in files:
        hashes[hashlib.sha256(path.read_bytes()).hexdigest()].append(path.name)
    duplicate_groups = sum(1 for paths in hashes.values() if len(paths) > 1)
    return sorted(files), duplicate_groups, errors


def _validate_inventory(payload: dict[str, Any], database_dir: Path, errors: list[str]) -> int:
    inventory = payload.get("inventory")
    if not isinstance(inventory, dict):
        errors.append("inventory must be an object")
        return 0
    if inventory.get("recursive") is not False:
        errors.append("inventory recursive must be false")
    if inventory.get("roots") != list(EXPECTED_ROOTS):
        errors.append("inventory roots mismatch")
    if inventory.get("filename_keywords") != list(EXPECTED_KEYWORDS):
        errors.append("inventory filename_keywords mismatch")
    if inventory.get("suffixes") != list(EXPECTED_SUFFIXES):
        errors.append("inventory suffixes mismatch")
    if inventory.get("unlisted_scoped_script_policy") != "retain_deletion_forbidden_until_mapped":
        errors.append("inventory unlisted_scoped_script_policy mismatch")
    if inventory.get("retained_default_deletion_blocker") != RETAINED_DEFAULT_DELETION_BLOCKER:
        errors.append("inventory retained_default_deletion_blocker mismatch")
    files, duplicate_groups, inventory_errors = _scoped_inventory(database_dir)
    errors.extend(inventory_errors)
    if inventory.get("scanned_script_count") != len(files):
        errors.append("inventory scanned_script_count mismatch")
    if inventory.get("exact_sha256_duplicate_group_count") != duplicate_groups:
        errors.append("inventory exact_sha256_duplicate_group_count mismatch")
    if duplicate_groups:
        errors.append("inventory contains exact SHA-256 duplicate groups")

    if inventory.get("baseline_scoped_script_count") != BASELINE_SCOPED_SCRIPT_COUNT:
        errors.append("inventory baseline_scoped_script_count mismatch")
    if inventory.get("baseline_path_manifest_sha256") != BASELINE_PATH_MANIFEST_SHA256:
        errors.append("inventory baseline_path_manifest_sha256 mismatch")

    rows = inventory.get("scoped_scripts")
    if not isinstance(rows, list):
        errors.append("inventory scoped_scripts must be a list")
        return 0
    mapped: dict[str, dict[str, Any]] = {}
    baseline_paths: set[str] = set()
    retained_paths: set[str] = set()
    mapped_deleted_paths: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("scoped script mapping entry must be an object")
            continue
        relative = _safe_relative_path(row.get("path"))
        label = relative or "<invalid-path>"
        if relative is None or not _is_scoped_script(relative):
            errors.append(f"scoped script mapping path is outside inventory scope: {label}")
            continue
        if relative in mapped:
            errors.append(f"scoped script mapping path is duplicated: {relative}")
            continue
        mapped[relative] = row
        if not isinstance(row.get("baseline"), bool):
            errors.append(f"scoped script mapping baseline flag is invalid: {relative}")
        elif row["baseline"]:
            baseline_paths.add(relative)
        digest = row.get("sha256")
        if (
            not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            errors.append(f"scoped script mapping SHA-256 is invalid: {relative}")
        if row.get("matched_families") != _matched_families(relative):
            errors.append(f"scoped script mapping family mismatch: {relative}")
        disposition = row.get("disposition")
        if disposition == "retained":
            retained_paths.add(relative)
        elif disposition == "deleted":
            mapped_deleted_paths.add(relative)
        else:
            errors.append(f"scoped script mapping disposition is invalid: {relative}")

    if len(baseline_paths) != BASELINE_SCOPED_SCRIPT_COUNT:
        errors.append("inventory baseline scoped script mapping count mismatch")
    if _path_manifest_sha256(baseline_paths) != BASELINE_PATH_MANIFEST_SHA256:
        errors.append("inventory baseline scoped script path manifest mismatch")
    if len(mapped) < BASELINE_SCOPED_SCRIPT_COUNT:
        errors.append("inventory scoped script mapping cannot shrink below baseline")

    current_paths = {path.relative_to(database_dir).as_posix(): path for path in files}
    if retained_paths != set(current_paths):
        missing = sorted(set(current_paths) - retained_paths)
        absent = sorted(retained_paths - set(current_paths))
        errors.append(
            "scoped script mapping mismatch: "
            f"unmapped_current={missing[:5]} absent_retained={absent[:5]}"
        )
    declared_deleted_paths = {
        relative
        for item in payload.get("deleted_scripts", [])
        if isinstance(item, dict)
        for relative in [_safe_relative_path(item.get("path"))]
        if relative is not None
    }
    if mapped_deleted_paths != declared_deleted_paths:
        errors.append("scoped script mapping deleted disposition does not match deleted_scripts")
    for relative, path in current_paths.items():
        row = mapped.get(relative)
        if row is None:
            continue
        actual_digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if row.get("sha256") != actual_digest:
            errors.append(f"scoped script mapping SHA-256 mismatch: {relative}")
    return len(mapped)


def _validate_equivalence_tests(
    rows: object,
    database_dir: Path,
    errors: list[str],
) -> set[str]:
    if not isinstance(rows, list):
        errors.append("equivalence_tests must be a list")
        return set()
    registered: set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            errors.append("equivalence test entry must be an object")
            continue
        test_id = row.get("test_id")
        label = test_id if isinstance(test_id, str) and test_id else "<invalid-test-id>"
        valid = True
        if not isinstance(test_id, str) or not test_id or test_id in registered:
            errors.append(f"equivalence test {label} requires a unique test_id")
            valid = False
        if not isinstance(row.get("test_command"), str) or not row.get("test_command", "").strip():
            errors.append(f"equivalence test {label} requires test_command")
            valid = False
        test_file = _safe_relative_path(row.get("test_file"))
        if test_file is None or not test_file.startswith("tests/"):
            errors.append(f"equivalence test {label} requires test_file under tests/")
            valid = False
            test_path = None
        else:
            test_path = database_dir / test_file
            if test_path.is_symlink() or not test_path.is_file():
                errors.append(f"equivalence test {label} test_file is missing or symlinked")
                valid = False
        test_case = row.get("test_case")
        if not isinstance(test_case, str) or not test_case:
            errors.append(f"equivalence test {label} requires test_case")
            valid = False
        elif test_path is not None and test_path.is_file() and test_case not in test_path.read_text(encoding="utf-8"):
            errors.append(f"equivalence test {label} test_case is absent from test_file")
            valid = False
        assertions = row.get("asserts")
        if (
            not isinstance(assertions, list)
            or not all(isinstance(assertion, str) for assertion in assertions)
            or not REQUIRED_RETIREMENT_ASSERTIONS.issubset(set(assertions))
        ):
            errors.append(f"equivalence test {label} must assert approved retirement evidence")
            valid = False
        if valid:
            registered.add(test_id)
    return registered


def validate_script_migration_map(payload: dict[str, Any], database_dir: Path) -> list[str]:
    errors: list[str] = []
    database_dir = database_dir.resolve()
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if payload.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")
    if payload.get("canonical_entrypoint") != "python3 scripts/atlasctl.py":
        errors.append("canonical_entrypoint mismatch")
    mapped_scoped_script_count = _validate_inventory(payload, database_dir, errors)
    if payload.get("deletion_policy") != REQUIRED_DELETION_POLICY:
        errors.append("deletion_policy mismatch")
    if payload.get("safety") != REQUIRED_SAFETY:
        errors.append("safety contract mismatch")
    if payload.get("profile_consolidation") != REQUIRED_PROFILE_CONSOLIDATION:
        errors.append("profile consolidation contract mismatch")
    command_migration = payload.get("command_migration")
    if (
        not isinstance(command_migration, dict)
        or command_migration.get("task_id") != "S04-P3-T3"
        or command_migration.get("status") != "completed_local_only"
        or command_migration.get("migration_map")
        != "config/memory_atlas_legacy_command_migrations.json"
        or command_migration.get("compatibility_mode") != "lookup_only"
        or command_migration.get("removal_version") != "v1.2.2"
        or command_migration.get("public_aliases_restored") is not False
    ):
        errors.append("S04-P3-T3 command migration contract mismatch")

    families = payload.get("families")
    if not isinstance(families, list):
        errors.append("families must be a list")
        families = []
    family_names = [
        row.get("family")
        for row in families
        if isinstance(row, dict) and isinstance(row.get("family"), str)
    ]
    if set(family_names) != EXPECTED_FAMILIES or len(family_names) != len(EXPECTED_FAMILIES):
        errors.append("families must cover build, sync, audit and validator exactly once")

    retained_paths: set[str] = set()
    retained_count = 0
    for family in families:
        if not isinstance(family, dict):
            errors.append("family entry must be an object")
            continue
        family_name = str(family.get("family") or "unknown")
        if not isinstance(family.get("scope"), str) or not family.get("scope"):
            errors.append(f"family {family_name} requires scope")
        if not isinstance(family.get("disposition"), str) or not family.get("disposition"):
            errors.append(f"family {family_name} requires disposition")
        scripts = family.get("scripts")
        if not isinstance(scripts, list):
            errors.append(f"family {family_name} scripts must be a list")
            continue
        for item in scripts:
            retained_count += 1
            if not isinstance(item, dict):
                errors.append(f"family {family_name} script entry must be an object")
                continue
            relative = _safe_relative_path(item.get("path"))
            if relative is None or not _inside_roots(relative or "", EXPECTED_ROOTS):
                errors.append(f"family {family_name} retained path is outside audited script roots")
                continue
            if relative in retained_paths:
                errors.append(f"retained script is mapped more than once: {relative}")
            retained_paths.add(relative)
            if item.get("status") not in RETAINED_STATUSES:
                errors.append(f"retained script {relative} has invalid status")
            blockers = item.get("deletion_blockers")
            if not isinstance(blockers, list) or not blockers or not all(isinstance(row, str) and row for row in blockers):
                errors.append(f"retained script {relative} requires deletion_blockers")
            candidate = database_dir / relative
            if candidate.is_symlink() or not candidate.is_file():
                errors.append(f"retained script is missing or symlinked: {relative}")

    registered_test_ids = _validate_equivalence_tests(payload.get("equivalence_tests"), database_dir, errors)
    deleted = payload.get("deleted_scripts")
    if not isinstance(deleted, list):
        errors.append("deleted_scripts must be a list")
        deleted = []
    deleted_paths: set[str] = set()
    for item in deleted:
        if not isinstance(item, dict):
            errors.append("deleted script entry must be an object")
            continue
        relative = _safe_relative_path(item.get("path"))
        label = relative or "<invalid-path>"
        if relative is None or not _inside_roots(relative or "", EXPECTED_ROOTS):
            errors.append(f"deleted script {label} path is outside the audited script roots")
        else:
            if relative in deleted_paths:
                errors.append(f"deleted script is mapped more than once: {relative}")
            deleted_paths.add(relative)
            candidate = database_dir / relative
            if candidate.exists() or candidate.is_symlink():
                errors.append(f"deleted script path still exists: {relative}")
            if relative in retained_paths:
                errors.append(f"deleted script remains in retained map: {relative}")
        if not isinstance(item.get("equivalent_command"), str) or not item.get("equivalent_command", "").strip():
            errors.append(f"deleted script {label} requires equivalent_command")
        test_ids = item.get("equivalence_test_ids")
        if not isinstance(test_ids, list) or not test_ids or not all(isinstance(row, str) and row for row in test_ids):
            errors.append(f"deleted script {label} requires equivalence_test_ids")
        else:
            for test_id in test_ids:
                if test_id not in registered_test_ids:
                    errors.append(f"deleted script {label} has unregistered equivalence test: {test_id}")
        if item.get("callers_migrated") is not True:
            errors.append(f"deleted script {label} requires callers_migrated=true")
        behavior_parity = item.get("behavior_parity_verified") is True
        approved_retirement = (
            item.get("approved_low_value_retirement") is True
            and item.get("retirement_review") == LOW_VALUE_RETIREMENT_REVIEW
            and item.get("replacement_risk_coverage_verified") is True
        )
        if not behavior_parity and not approved_retirement:
            errors.append(
                f"deleted script {label} requires behavior parity or approved low-value retirement"
            )

    summary = payload.get("summary")
    if not isinstance(summary, dict):
        errors.append("summary must be an object")
    else:
        if summary.get("deleted_script_count") != len(deleted):
            errors.append("summary deleted_script_count does not match deleted_scripts")
        if summary.get("retained_representative_script_count") != retained_count:
            errors.append("summary retained_representative_script_count mismatch")
        if summary.get("mapped_scoped_script_count") != mapped_scoped_script_count:
            errors.append("summary mapped_scoped_script_count mismatch")
        call_counts = []
        for relative in CONSOLIDATED_MODULES:
            source = (database_dir / relative).read_text(encoding="utf-8")
            if "subprocess.run(" in source or "import subprocess" in source:
                errors.append(f"consolidated module still owns subprocess execution: {relative}")
            call_counts.append(source.count("run_child_command("))
        if summary.get("consolidated_execution_module_count") != sum(count > 0 for count in call_counts):
            errors.append("summary consolidated_execution_module_count mismatch")
        if summary.get("consolidated_execution_block_count") != sum(call_counts):
            errors.append("summary consolidated_execution_block_count mismatch")
        if summary.get("validator_profile_count_created") != 4:
            errors.append("summary validator_profile_count_created must equal 4")
    return errors


__all__ = (
    "EXPECTED_FAMILIES",
    "MIGRATION_MAP_PATH",
    "SCHEMA_VERSION",
    "TASK_ID",
    "ScriptMigrationError",
    "load_script_migration_map",
    "validate_script_migration_map",
)
