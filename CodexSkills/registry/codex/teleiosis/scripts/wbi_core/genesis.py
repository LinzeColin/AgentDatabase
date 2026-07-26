from __future__ import annotations

import difflib
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import load_json, sha256_file

SOURCE_REL = "constitution/GENESIS_SOURCE.v0.0.0.1.zh-CN.md"
LOCKED_REL = "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
LOCK_REL = "constitution/genesis-lock.json"
REQUIREMENTS_REL = "constitution/requirements.json"


def verify_genesis(root: Path, expected_hash: Optional[str] = None) -> Dict[str, Any]:
    root = root.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    paths = {name: root / relative for name, relative in {
        "source": SOURCE_REL,
        "locked": LOCKED_REL,
        "lock": LOCK_REL,
        "requirements": REQUIREMENTS_REL,
    }.items()}
    for name, path in paths.items():
        if not path.is_file():
            errors.append("missing Genesis %s: %s" % (name, path.relative_to(root)))
    if errors:
        return {"status": "FAIL", "errors": errors, "warnings": warnings}

    lock = load_json(paths["lock"])
    requirements = load_json(paths["requirements"])
    source_hash = sha256_file(paths["source"])
    locked_hash = sha256_file(paths["locked"])
    requirements_hash = sha256_file(paths["requirements"])

    if source_hash != lock.get("source_candidate", {}).get("sha256"):
        errors.append("Genesis source hash mismatch")
    if locked_hash != lock.get("locked_genesis", {}).get("sha256"):
        errors.append("locked Genesis hash mismatch")
    if requirements_hash != lock.get("requirements", {}).get("sha256"):
        errors.append("requirements projection hash mismatch")
    if requirements.get("source_sha256") != source_hash or requirements.get("locked_sha256") != locked_hash:
        errors.append("requirements projection does not bind Genesis hashes")

    ids = [item.get("id") for item in requirements.get("requirements", [])]
    expected_ids = ["WBI-GB-%03d" % number for number in range(1, 28)]
    if ids != expected_ids or lock.get("requirements", {}).get("ids") != expected_ids:
        errors.append("Genesis Requirement IDs changed, missing, or reordered")

    source_lines = paths["source"].read_text(encoding="utf-8").splitlines()
    locked_lines = paths["locked"].read_text(encoding="utf-8").splitlines()
    changed = list(difflib.unified_diff(source_lines, locked_lines, lineterm=""))
    removals = [line[1:].rstrip() for line in changed if line.startswith("-") and not line.startswith("---")]
    additions = [line[1:].rstrip() for line in changed if line.startswith("+") and not line.startswith("+++")]
    if removals != ["**状态：** `BASELINE_CANDIDATE`"] or additions != ["**状态：** `LOCKED_GENESIS`"]:
        errors.append("locked Genesis differs from source beyond the authorized one-line status transition")

    anchor = expected_hash or os.environ.get("WBI_EXPECTED_GENESIS_SHA256")
    if anchor:
        if anchor != locked_hash:
            errors.append("external Genesis anchor mismatch")
    else:
        warnings.append("no external Genesis anchor supplied; internal consistency cannot detect a coordinated rewrite")

    return {
        "status": "PASS" if not errors else "FAIL",
        "baseline_id": lock.get("baseline_id"),
        "baseline_version": lock.get("baseline_version"),
        "locked_sha256": locked_hash,
        "source_sha256": source_hash,
        "requirement_count": len(ids),
        "errors": errors,
        "warnings": warnings,
    }
