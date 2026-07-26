from __future__ import annotations

import ast
import json
from pathlib import Path
import sys
import tempfile
from typing import Any, Dict

from .io import copy_clean
from .process import run_bounded
from .validation import validate_skill


def _parse_python_and_json(root: Path) -> Dict[str, Any]:
    python_files = 0
    json_files = 0
    errors = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or any(part in {".git", "__pycache__"} for part in path.relative_to(root).parts):
            continue
        relative = path.relative_to(root).as_posix()
        try:
            if path.suffix == ".py":
                ast.parse(path.read_text(encoding="utf-8"), filename=relative, feature_version=(3, 9))
                python_files += 1
            elif path.suffix == ".json":
                json.loads(path.read_text(encoding="utf-8"))
                json_files += 1
        except Exception as exc:
            errors.append("%s: %s" % (relative, exc))
    return {"status": "PASS" if not errors else "FAIL", "python_files": python_files, "json_files": json_files, "errors": errors}


def _cli_surface(root: Path) -> Dict[str, Any]:
    command = [sys.executable, str(root / "scripts/wbi.py"), "--help"]
    result = run_bounded(command, cwd=root, timeout_seconds=20, max_output_bytes=256 * 1024)
    required = {
        "verify-self", "release-smoke", "self-test", "init-run", "competitors", "freshness-scan",
        "seal-research", "seal-eval", "evaluate", "review-plan", "review-gate", "gate", "package",
        "install", "install-status", "recover-install", "rollback-install", "release-receipt",
    }
    missing = sorted(item for item in required if item not in result["stdout"])
    return {
        "status": "PASS" if result["returncode"] == 0 and not result["timed_out"] and not missing else "FAIL",
        "returncode": result["returncode"], "timed_out": result["timed_out"], "missing_commands": missing,
    }


def _generic_release_primitives() -> Dict[str, Any]:
    # Imported lazily so the smoke check itself stays acyclic and transparent.
    from .install import install_archive, rollback_install
    from .package import package_skill

    with tempfile.TemporaryDirectory(prefix="wbi-release-smoke-") as td:
        base = Path(td)
        source = base / "smoke-skill"
        source.mkdir()
        (source / "SKILL.md").write_text(
            "---\nname: smoke-skill\ndescription: Minimal install transaction smoke target.\n---\n\n# Use\n\nRun only for the release smoke.\n",
            encoding="utf-8",
        )
        archive = base / "smoke.zip"
        packaged = package_skill(source, archive, profile="generic", verification_level="structural")
        if packaged.get("status") != "PASS":
            return {"status": "FAIL", "stage": "package", "detail": packaged}
        skills_root = base / "skills"
        first = install_archive(archive, skills_root, profile="generic", verification_level="structural")
        if first.get("status") != "PASS":
            return {"status": "FAIL", "stage": "first-install", "detail": first}
        sentinel = skills_root / "smoke-skill" / "old-sentinel.txt"
        sentinel.write_text("old", encoding="utf-8")
        second = install_archive(archive, skills_root, replace=True, profile="generic", verification_level="structural")
        if second.get("status") != "PASS" or not second.get("backup"):
            return {"status": "FAIL", "stage": "replace", "detail": second}
        rolled = rollback_install(skills_root / "smoke-skill", Path(second["backup"]))
        if rolled.get("status") != "PASS" or not sentinel.is_file():
            return {"status": "FAIL", "stage": "rollback", "detail": rolled}
        return {
            "status": "PASS", "archive_sha256": packaged.get("archive_sha256"),
            "transaction_receipt": second.get("transaction_receipt"),
        }


def run_release_smoke(root: Path, expected_genesis_hash: str) -> Dict[str, Any]:
    """Run a bounded, non-recursive installation-safe verification profile.

    This deliberately does not execute the full unit suite. Full regression is a
    release-build concern; installers use this smoke before and after the atomic
    switch so they cannot recursively test their own installer.
    """
    root = root.resolve()
    validation = validate_skill(root, strict=True, expected_genesis_hash=expected_genesis_hash, profile="optimizer")
    syntax = _parse_python_and_json(root)
    cli = _cli_surface(root)
    primitives = _generic_release_primitives()
    checks = {
        "strict_validation": validation.get("status"),
        "python_ast": syntax.get("status"),
        "json_documents": syntax.get("status"),
        "cli_surface": cli.get("status"),
        "generic_package_install_rollback": primitives.get("status"),
    }
    errors = []
    if validation.get("status") != "PASS":
        errors.extend(validation.get("errors", []))
    errors.extend(syntax.get("errors", []))
    if cli.get("status") != "PASS":
        errors.append("CLI surface failed or commands missing: %s" % cli.get("missing_commands"))
    if primitives.get("status") != "PASS":
        errors.append("generic package/install/rollback smoke failed at %s" % primitives.get("stage"))
    return {
        "status": "PASS" if not errors else "FAIL",
        "profile": "optimizer",
        "recursive_full_suite": False,
        "checks": checks,
        "details": {"validation": validation, "syntax": syntax, "cli": cli, "release_primitives": primitives},
        "errors": errors,
    }
