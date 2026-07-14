#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Sequence


MAP_PATH = Path("config/memory_atlas_legacy_command_migrations.json")
PACKAGE_PATH = Path("apps/memory-atlas/package.json")
PROFILE_PATH = Path("config/memory_atlas_validator_profiles.json")
SCHEMA_VERSION = "memory_atlas.legacy_command_migrations.v1_2_1_s04_p3_t3"
TASK_ID = "S04-P3-T3"
SOURCE_COMMIT = "f22f2d336e3b5154a68fbabeec33b13be646a56c"
SOURCE_PACKAGE_SHA256 = "06268d65a3db20919a94860a7f2a41c3408204e8aa5276d83f25ca8c8ce29c01"
SOURCE_ALIAS_MANIFEST_SHA256 = "aa3134c05c436f2645052dc6dc8866521df4906a9996dc25fe20b1d2bfcc0689"
PUBLIC_PROFILES = ("fast", "sync", "ui", "release")
PUBLIC_ALIASES = {f"validate:{profile}" for profile in PUBLIC_PROFILES}
EXPECTED_PUBLIC_SCRIPTS = {
    f"validate:{profile}": (
        f"python3 ../../scripts/memory_atlas_validator_profiles.py --profile {profile}"
    )
    for profile in PUBLIC_PROFILES
}
REQUIRED_POLICY = {
    "mode": "lookup_only",
    "execution_supported": False,
    "shell_invocation_allowed": False,
    "introduced_version": "v1.2.1",
    "removal_version": "v1.2.2",
    "maximum_supported_releases": 1,
    "removal_required": True,
}
REQUIRED_ROW_KEYS = {
    "legacy_alias",
    "legacy_command",
    "previous_package_command",
    "target_script",
    "target_state",
    "replacement_profile",
    "replacement_command",
    "compatibility_mode",
    "execution_supported",
    "migration_reason",
}
REQUIRED_MIGRATED_CALLERS = {
    "apps/memory-atlas/scripts/validate_inspector_proposal.mjs": [
        "validate:inspector-proposal"
    ],
    "apps/memory-atlas/scripts/validate_memory_atlas_stage6.mjs": [
        "validate:shared-state",
        "validate:inspector-proposal",
        "validate:stage6",
    ],
    "apps/memory-atlas/scripts/validate_memory_atlas_stage7.mjs": [
        "validate:stage7-visual",
        "validate:stage7-performance",
        "validate:stage7-privacy-accessibility",
        "validate:stage7",
    ],
    "apps/memory-atlas/scripts/validate_memory_atlas_stage8.cjs": [
        "validate:stage8-local-app",
        "validate:stage8-release-safety",
        "validate:stage8",
    ],
    "apps/memory-atlas/scripts/validate_memory_atlas_stage9.cjs": [
        "validate:stage9-obsidian",
        "validate:stage9-visual-semantics",
        "validate:stage9",
    ],
    "apps/memory-atlas/scripts/validate_memory_river_evidence_layers.mjs": [
        "validate:memory-river-evidence"
    ],
    "apps/memory-atlas/scripts/validate_memory_river_interaction.mjs": [
        "validate:memory-river-interaction"
    ],
    "apps/memory-atlas/scripts/validate_memory_river_rendering.mjs": [
        "validate:memory-river-rendering"
    ],
    "apps/memory-atlas/scripts/validate_memory_river_stage5.mjs": [
        "validate:memory-river-rendering",
        "validate:memory-river-interaction",
        "validate:memory-river-evidence",
        "validate:memory-river-stage5",
    ],
    "apps/memory-atlas/scripts/validate_shared_state_store.mjs": [
        "validate:shared-state"
    ],
}


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return payload


def load_migration_map(database_dir: Path) -> dict[str, Any]:
    return _read_json(database_dir.resolve() / MAP_PATH)


def _manifest_hash(rows: list[dict[str, Any]]) -> str:
    aliases = {
        row["legacy_alias"]: row["previous_package_command"]
        for row in rows
        if isinstance(row, dict)
        and isinstance(row.get("legacy_alias"), str)
        and isinstance(row.get("previous_package_command"), str)
    }
    encoded = json.dumps(
        aliases,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _current_package_errors(database_dir: Path) -> list[str]:
    errors: list[str] = []
    package = _read_json(database_dir / PACKAGE_PATH)
    scripts = package.get("scripts")
    if not isinstance(scripts, dict):
        return ["current package scripts must be an object"]
    validate_scripts = {
        name: command
        for name, command in scripts.items()
        if str(name).startswith("validate:")
    }
    if validate_scripts != EXPECTED_PUBLIC_SCRIPTS:
        errors.append(
            "current package must expose the exact four audited validator profile commands"
        )
    if len(scripts) != 8:
        errors.append("current package script count must remain 8")
    return errors


def _legacy_package_dependency_errors(database_dir: Path) -> list[str]:
    errors: list[str] = []
    script_dir = database_dir / "apps/memory-atlas/scripts"
    patterns = (
        re.compile(r"packageSource\.includes\([\s\S]{0,240}?[\"']validate:"),
        re.compile(r"hasAll\(packageSource,[\s\S]{0,640}?[\"']validate:"),
    )
    for path in sorted(script_dir.glob("validate_*.cjs")) + sorted(
        script_dir.glob("validate_*.mjs")
    ):
        source = path.read_text(encoding="utf-8")
        if any(pattern.search(source) for pattern in patterns):
            errors.append(
                f"retained validator still requires a legacy package alias: {path.relative_to(database_dir)}"
            )
    return errors


def validate_migration_map(payload: dict[str, Any], database_dir: Path) -> list[str]:
    errors: list[str] = []
    database_dir = database_dir.resolve()
    if payload.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version mismatch")
    if payload.get("task_id") != TASK_ID:
        errors.append("task_id mismatch")

    source = payload.get("source")
    expected_source = {
        "git_commit": SOURCE_COMMIT,
        "package_path": "OpenAIDatabase/apps/memory-atlas/package.json",
        "package_json_sha256": SOURCE_PACKAGE_SHA256,
        "validate_alias_count": 178,
        "validate_alias_manifest_sha256": SOURCE_ALIAS_MANIFEST_SHA256,
    }
    if source != expected_source:
        errors.append("historical source identity mismatch")
    if payload.get("compatibility_policy") != REQUIRED_POLICY:
        errors.append("compatibility policy must be lookup-only and expire in v1.2.2")
    if payload.get("public_profiles") != list(PUBLIC_PROFILES):
        errors.append("public profile list mismatch")

    try:
        profile_config = _read_json(database_dir / PROFILE_PATH)
        valid_profiles = set(profile_config.get("public_profiles") or [])
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
        valid_profiles = set()

    rows = payload.get("migrations")
    if not isinstance(rows, list):
        errors.append("migrations must be a list")
        rows = []
    if len(rows) != 178:
        errors.append("migration count must be exactly 178")

    aliases: set[str] = set()
    profile_counts = {profile: 0 for profile in PUBLIC_PROFILES}
    target_state_counts = {
        "retained_internal": 0,
        "deleted_in_s04_p3_t2": 0,
    }
    for index, row in enumerate(rows):
        label = f"migration[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        if set(row) != REQUIRED_ROW_KEYS:
            errors.append(f"{label} field set mismatch")
        alias = row.get("legacy_alias")
        if not isinstance(alias, str) or not alias.startswith("validate:"):
            errors.append(f"{label} legacy_alias is invalid")
            continue
        if alias in aliases:
            errors.append(f"duplicate legacy alias: {alias}")
        aliases.add(alias)
        if row.get("legacy_command") != f"npm run {alias}":
            errors.append(f"{alias} legacy command mismatch")
        if not isinstance(row.get("previous_package_command"), str) or not row.get(
            "previous_package_command"
        ):
            errors.append(f"{alias} previous package command is missing")
        target_script = row.get("target_script")
        target_path = Path(target_script) if isinstance(target_script, str) else None
        if (
            target_path is None
            or target_path.is_absolute()
            or ".." in target_path.parts
            or "\\" in target_script
            or target_path.as_posix() != target_script
            or not target_script.startswith("scripts/")
        ):
            errors.append(f"{alias} target script is invalid")
            target_exists = False
        else:
            target_exists = (database_dir / "apps/memory-atlas" / target_script).is_file()
        expected_state = "retained_internal" if target_exists else "deleted_in_s04_p3_t2"
        if row.get("target_state") != expected_state:
            errors.append(f"{alias} target state mismatch")
        elif expected_state in target_state_counts:
            target_state_counts[expected_state] += 1
        profile = row.get("replacement_profile")
        if profile not in valid_profiles:
            errors.append(f"{alias} replacement profile is invalid")
        elif profile in profile_counts:
            profile_counts[profile] += 1
        if row.get("replacement_command") != f"npm run validate:{profile}":
            errors.append(f"{alias} replacement command mismatch")
        if row.get("compatibility_mode") != "lookup_only":
            errors.append(f"{alias} compatibility mode mismatch")
        if row.get("execution_supported") is not False:
            errors.append(f"{alias} must not support execution")
        if not isinstance(row.get("migration_reason"), str) or not row.get("migration_reason"):
            errors.append(f"{alias} migration reason is missing")

    if _manifest_hash(rows) != SOURCE_ALIAS_MANIFEST_SHA256:
        errors.append("legacy alias manifest SHA-256 mismatch")

    summary = payload.get("summary")
    expected_summary = {
        "migration_count": 178,
        "profile_counts": profile_counts,
        "target_state_counts": target_state_counts,
        "migrated_caller_count": 10,
    }
    if summary != expected_summary:
        errors.append("migration summary mismatch")

    migrated_callers = payload.get("migrated_callers")
    expected_callers = [
        {
            "path": path,
            "legacy_aliases": caller_aliases,
            "validation_mode": "legacy_map_lookup",
        }
        for path, caller_aliases in sorted(REQUIRED_MIGRATED_CALLERS.items())
    ]
    if migrated_callers != expected_callers:
        errors.append("migrated caller inventory must match the exact 10-path contract")
    else:
        for row in migrated_callers:
            path = row.get("path")
            if not (database_dir / path).is_file():
                errors.append(f"migrated caller path is missing: {path}")
            if not set(row["legacy_aliases"]).issubset(aliases):
                errors.append(f"migrated caller has unknown aliases: {path}")

    safety = payload.get("safety")
    if safety != {
        "restores_legacy_package_aliases": False,
        "executes_legacy_commands": False,
        "product_behavior_change": False,
        "raw_or_derived_mutation": False,
        "push_or_deploy": False,
    }:
        errors.append("safety boundary mismatch")

    try:
        errors.extend(_current_package_errors(database_dir))
        errors.extend(_legacy_package_dependency_errors(database_dir))
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors.append(str(exc))
    return errors


def _lookup(payload: dict[str, Any], alias: str) -> dict[str, Any] | None:
    for row in payload.get("migrations") or []:
        if isinstance(row, dict) and row.get("legacy_alias") == alias:
            return row
    return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Audit or look up the temporary Memory Atlas legacy validator command map."
    )
    parser.add_argument("--database-dir", type=Path, default=Path.cwd())
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--audit", action="store_true")
    action.add_argument("--lookup", metavar="LEGACY_ALIAS")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    database_dir = args.database_dir.resolve()
    try:
        payload = load_migration_map(database_dir)
        errors = validate_migration_map(payload, database_dir)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        errors = [str(exc)]
        payload = {}

    if args.audit:
        result = {
            "schema_version": "memory_atlas.legacy_command_audit_result.v1_2_1_s04_p3_t3",
            "task_id": TASK_ID,
            "status": "PASS" if not errors else "FAIL",
            "migration_count": len(payload.get("migrations") or []),
            "errors": errors,
        }
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return 0 if not errors else 1

    if errors:
        print(
            json.dumps(
                {"status": "INVALID_MAP", "legacy_alias": args.lookup, "errors": errors},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 1
    row = _lookup(payload, args.lookup)
    if row is None:
        print(
            json.dumps(
                {"status": "NOT_FOUND", "legacy_alias": args.lookup},
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 2
    result = {
        "status": "FOUND",
        "legacy_alias": row["legacy_alias"],
        "legacy_command": row["legacy_command"],
        "replacement_command": row["replacement_command"],
        "target_state": row["target_state"],
        "execution_supported": False,
        "removal_version": payload["compatibility_policy"]["removal_version"],
    }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
