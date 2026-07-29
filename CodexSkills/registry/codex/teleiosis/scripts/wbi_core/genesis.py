from __future__ import annotations

import difflib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import canonical_json, load_json, sha256_bytes, sha256_file

SOURCE_REL = "constitution/GENESIS_SOURCE.v0.0.0.1.zh-CN.md"
LOCKED_REL = "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
LOCK_REL = "constitution/genesis-lock.json"
REQUIREMENTS_REL = "constitution/requirements.json"
EFFECTIVE_LOCK_REL = "constitution/effective-genesis-lock.v0.0.0.2.json"
EFFECTIVE_REQUIREMENTS_REL = "constitution/effective-requirements.v0.0.0.2.json"


def _verify_base(root: Path, expected_hash: Optional[str]) -> Dict[str, Any]:
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
        "requirements_sha256": requirements_hash,
        "requirement_count": len(ids),
        "requirement_ids": ids,
        "errors": errors,
        "warnings": warnings,
    }


def verify_effective_genesis(root: Path, expected_hash: Optional[str] = None) -> Dict[str, Any]:
    """Verify the append-only effective Genesis without changing the base anchor.

    The base v0.0.0.1 files remain byte-preserved and independently verifiable. The
    effective hash binds their hashes, every authorized amendment, and the ordered
    effective requirement IDs. This keeps implementation/version details out of the
    immutable base while still making user-authorized additions fail closed.
    """
    root = root.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    lock_path = root / EFFECTIVE_LOCK_REL
    projection_path = root / EFFECTIVE_REQUIREMENTS_REL
    if not lock_path.is_file() or not projection_path.is_file():
        return {
            "status": "NOT_CONFIGURED",
            "effective_requirement_count": 0,
            "effective_composite_sha256": None,
            "errors": [],
            "warnings": ["effective Genesis amendment set not configured"],
        }
    try:
        lock = load_json(lock_path)
        projection = load_json(projection_path)
    except Exception as exc:
        return {"status": "FAIL", "errors": ["invalid effective Genesis JSON: %s" % exc], "warnings": []}

    base_locked = sha256_file(root / LOCKED_REL) if (root / LOCKED_REL).is_file() else ""
    base_requirements = sha256_file(root / REQUIREMENTS_REL) if (root / REQUIREMENTS_REL).is_file() else ""
    if lock.get("base_locked_sha256") != base_locked or projection.get("base_locked_sha256") != base_locked:
        errors.append("effective Genesis does not bind the byte-preserved base locked hash")
    if lock.get("base_requirements_sha256") != base_requirements or projection.get("base_requirements_sha256") != base_requirements:
        errors.append("effective Genesis does not bind the base requirements projection hash")

    amendment_rows = lock.get("amendment_files")
    if not isinstance(amendment_rows, list) or not amendment_rows:
        errors.append("effective Genesis amendment list missing")
        amendment_rows = []
    observed_amendments: List[Dict[str, Any]] = []
    seen_ids = set()
    for row in amendment_rows:
        if not isinstance(row, dict):
            errors.append("invalid amendment lock row")
            continue
        amendment_id = str(row.get("amendment_id", ""))
        relative = str(row.get("path", ""))
        if not amendment_id or amendment_id in seen_ids:
            errors.append("missing or duplicate amendment_id: %s" % amendment_id)
        seen_ids.add(amendment_id)
        path = root / relative
        if path.is_absolute() and root not in path.resolve().parents:
            errors.append("amendment path escaped root: %s" % relative)
            continue
        if not path.is_file() or path.is_symlink():
            errors.append("amendment missing or linked: %s" % relative)
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            errors.append("amendment hash mismatch: %s" % relative)
        observed_amendments.append(dict(row))

    projection_hash = sha256_file(projection_path)
    projection_lock = lock.get("effective_projection", {})
    if projection_lock.get("sha256") != projection_hash:
        errors.append("effective requirements projection hash mismatch")
    if projection_lock.get("path") != EFFECTIVE_REQUIREMENTS_REL:
        errors.append("effective requirements projection path mismatch")

    requirements = projection.get("requirements")
    ids = [item.get("id") for item in requirements] if isinstance(requirements, list) else []
    expected_ids = ["WBI-GB-%03d" % number for number in range(1, 29)]
    if ids != expected_ids or projection_lock.get("requirement_ids") != expected_ids:
        errors.append("effective Genesis Requirement IDs changed, missing, or reordered")
    if len(ids) >= 28:
        requirement_28 = requirements[27]
        if requirement_28.get("source_amendment") != "WBI-GB-AMENDMENT-001":
            errors.append("WBI-GB-028 is not bound to its authorized amendment")
        if requirement_28.get("severity") != "HARD_NON_COMPENSABLE":
            errors.append("WBI-GB-028 severity was weakened")

    composite = sha256_bytes(canonical_json({
        "base_locked_sha256": base_locked,
        "base_requirements_sha256": base_requirements,
        "amendments": observed_amendments,
        "requirement_ids": ids,
    }))
    if composite != lock.get("effective_composite_sha256") or composite != projection.get("effective_composite_sha256"):
        errors.append("effective Genesis composite hash mismatch")

    anchor = expected_hash or os.environ.get("WBI_EXPECTED_EFFECTIVE_GENESIS_SHA256")
    if anchor:
        if anchor != composite:
            errors.append("external effective Genesis anchor mismatch")
    else:
        warnings.append("no external effective Genesis anchor supplied")

    return {
        "status": "PASS" if not errors else "FAIL",
        "effective_baseline_id": lock.get("effective_baseline_id"),
        "effective_version": lock.get("effective_version"),
        "base_locked_sha256": base_locked,
        "effective_projection_sha256": projection_hash,
        "effective_composite_sha256": composite,
        "effective_requirement_count": len(ids),
        "effective_requirement_ids": ids,
        "amendment_count": len(observed_amendments),
        "errors": errors,
        "warnings": warnings,
    }


def verify_genesis(root: Path, expected_hash: Optional[str] = None, expected_effective_hash: Optional[str] = None) -> Dict[str, Any]:
    root = root.resolve()
    base = _verify_base(root, expected_hash)
    effective = verify_effective_genesis(root, expected_effective_hash)
    errors = list(base.get("errors", []))
    warnings = list(base.get("warnings", []))
    if effective.get("status") == "FAIL":
        errors.extend(effective.get("errors", []))
    warnings.extend(effective.get("warnings", []))
    result = dict(base)
    result.update({
        "status": "PASS" if not errors else "FAIL",
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
        "effective_genesis_status": effective.get("status"),
        "effective_baseline_id": effective.get("effective_baseline_id"),
        "effective_version": effective.get("effective_version"),
        "effective_composite_sha256": effective.get("effective_composite_sha256"),
        "effective_requirement_count": effective.get("effective_requirement_count", 0),
        "amendment_count": effective.get("amendment_count", 0),
    })
    return result
