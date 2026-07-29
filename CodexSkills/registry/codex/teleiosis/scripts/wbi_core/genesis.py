from __future__ import annotations

import difflib
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .io import canonical_json, load_json, sha256_bytes, sha256_file

SOURCE_REL = "constitution/GENESIS_SOURCE.v0.0.0.1.zh-CN.md"
LOCKED_REL = "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
LOCK_REL = "constitution/genesis-lock.json"
REQUIREMENTS_REL = "constitution/requirements.json"
_EFFECTIVE_LOCK_RE = re.compile(r"effective-genesis-lock\.v(\d+)\.(\d+)\.(\d+)\.(\d+)\.json$")


def _version_key(path: Path) -> Tuple[int, int, int, int]:
    m = _EFFECTIVE_LOCK_RE.fullmatch(path.name)
    return tuple(int(x) for x in m.groups()) if m else (-1, -1, -1, -1)


def discover_effective_paths(root: Path) -> Tuple[Optional[Path], Optional[Path]]:
    """Return the latest effective lock/projection pair available in the installed tree.

    This removes the old v0.0.0.2 filename coupling. Discovery is local and
    deterministic; explicit external anchors remain supported as a stronger trust
    signal but are not required merely to install or verify the Skill.
    """
    candidates = sorted((root / "constitution").glob("effective-genesis-lock.v*.json"), key=_version_key)
    for lock_path in reversed(candidates):
        lock = load_json(lock_path)
        projection_rel = str((lock.get("effective_projection") or {}).get("path") or "")
        if projection_rel:
            projection = root / projection_rel
        else:
            version = lock_path.name[len("effective-genesis-lock."):-len(".json")]
            projection = root / f"constitution/effective-requirements.{version}.json"
        if projection.is_file():
            return lock_path, projection
    return None, None


def discover_internal_anchors(root: Path) -> Dict[str, str]:
    """Discover self-contained anchors for compatibility-oriented local checks.

    These values are derived from the lock files and then independently checked
    against the actual files. They do not pretend to be an external trust anchor.
    """
    base = ""
    lock_path = root / LOCK_REL
    if lock_path.is_file():
        lock = load_json(lock_path)
        base = str((lock.get("locked_genesis") or {}).get("sha256") or "")
    effective = ""
    effective_lock, _ = discover_effective_paths(root)
    if effective_lock:
        effective = str(load_json(effective_lock).get("effective_composite_sha256") or "")
    return {"base": base, "effective": effective}


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
        anchor_mode = "EXTERNAL"
    else:
        declared = str(lock.get("locked_genesis", {}).get("sha256") or "")
        if declared != locked_hash:
            errors.append("self-contained Genesis lock mismatch")
        warnings.append("external Genesis anchor not supplied; verified with the bundled lock and transport manifest")
        anchor_mode = "SELF_CONTAINED"

    return {
        "status": "PASS" if not errors else "FAIL",
        "baseline_id": lock.get("baseline_id"),
        "baseline_version": lock.get("baseline_version"),
        "locked_sha256": locked_hash,
        "source_sha256": source_hash,
        "requirements_sha256": requirements_hash,
        "requirement_count": len(ids),
        "requirement_ids": ids,
        "anchor_mode": anchor_mode,
        "errors": errors,
        "warnings": warnings,
    }


def _compute_effective_v10(root: Path, lock: Dict[str, Any], projection: Dict[str, Any]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    errors: List[str] = []
    observed: List[Dict[str, Any]] = []
    base_locked = sha256_file(root / LOCKED_REL) if (root / LOCKED_REL).is_file() else ""
    base_requirements = sha256_file(root / REQUIREMENTS_REL) if (root / REQUIREMENTS_REL).is_file() else ""
    amendment_rows = lock.get("amendment_files") or projection.get("amendments") or []
    for row in amendment_rows:
        if not isinstance(row, dict):
            errors.append("invalid amendment lock row")
            continue
        relative = str(row.get("path") or "")
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append("amendment missing or linked: %s" % relative)
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            errors.append("amendment hash mismatch: %s" % relative)
        observed.append(dict(row))
    ids = [item.get("id") for item in projection.get("requirements", [])]
    composite = sha256_bytes(canonical_json({
        "base_locked_sha256": base_locked,
        "base_requirements_sha256": base_requirements,
        "amendments": observed,
        "requirement_ids": ids,
    }))
    return composite, errors, observed


def _compute_effective_v11(root: Path, lock: Dict[str, Any], projection: Dict[str, Any]) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    errors: List[str] = []
    observed: List[Dict[str, Any]] = []
    for row in lock.get("amendment_files", []):
        if not isinstance(row, dict):
            errors.append("invalid amendment lock row")
            continue
        relative = str(row.get("path") or "")
        path = root / relative
        if not path.is_file() or path.is_symlink():
            errors.append("amendment missing or linked: %s" % relative)
            continue
        actual = sha256_file(path)
        if actual != row.get("sha256"):
            errors.append("amendment hash mismatch: %s" % relative)
        observed.append({
            "amendment_id": row.get("amendment_id"),
            "path": relative,
            "sha256": actual,
            "requirements": row.get("requirements", []),
        })
    ids = [item.get("id") for item in projection.get("requirements", [])]
    composite = sha256_bytes(canonical_json({
        "base_locked_sha256": lock.get("base_locked_sha256"),
        "base_requirements_sha256": lock.get("base_requirements_sha256"),
        "prior_effective_composite_sha256": lock.get("prior_effective_composite_sha256"),
        "amendments": observed,
        "requirement_ids": ids,
    }))
    return composite, errors, observed


def verify_effective_genesis(root: Path, expected_hash: Optional[str] = None) -> Dict[str, Any]:
    root = root.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    lock_path, projection_path = discover_effective_paths(root)
    if not lock_path or not projection_path:
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
    if lock.get("base_requirements_sha256") and lock.get("base_requirements_sha256") != base_requirements:
        errors.append("effective Genesis lock does not bind the base requirements projection hash")
    if projection.get("base_requirements_sha256") != base_requirements:
        errors.append("effective Genesis projection does not bind the base requirements projection hash")

    projection_lock = lock.get("effective_projection", {})
    if projection_lock.get("path") != projection_path.relative_to(root).as_posix():
        errors.append("effective requirements projection path mismatch")
    if projection_lock.get("sha256") != sha256_file(projection_path):
        errors.append("effective requirements projection hash mismatch")

    ids = [item.get("id") for item in projection.get("requirements", [])]
    expected_ids = ["WBI-GB-%03d" % number for number in range(1, len(ids) + 1)]
    if ids != expected_ids or projection_lock.get("requirement_ids") != expected_ids:
        errors.append("effective Genesis Requirement IDs changed, missing, or reordered")
    for item in projection.get("requirements", [])[27:]:
        if item.get("severity") != "HARD_NON_COMPENSABLE":
            errors.append("effective amendment severity was weakened: %s" % item.get("id"))

    schema = str(lock.get("schema_version") or "1.0")
    if schema == "1.1":
        composite, compute_errors, observed = _compute_effective_v11(root, lock, projection)
    else:
        composite, compute_errors, observed = _compute_effective_v10(root, lock, projection)
    errors.extend(compute_errors)
    if composite != lock.get("effective_composite_sha256") or composite != projection.get("effective_composite_sha256"):
        errors.append("effective Genesis composite hash mismatch")

    anchor = expected_hash or os.environ.get("WBI_EXPECTED_EFFECTIVE_GENESIS_SHA256")
    if anchor:
        if anchor != composite:
            errors.append("external effective Genesis anchor mismatch")
        anchor_mode = "EXTERNAL"
    else:
        warnings.append("external effective Genesis anchor not supplied; verified with the latest bundled effective lock")
        anchor_mode = "SELF_CONTAINED"

    return {
        "status": "PASS" if not errors else "FAIL",
        "effective_baseline_id": lock.get("effective_baseline_id"),
        "effective_version": lock.get("effective_version"),
        "effective_lock_path": lock_path.relative_to(root).as_posix(),
        "effective_projection_path": projection_path.relative_to(root).as_posix(),
        "base_locked_sha256": base_locked,
        "effective_projection_sha256": sha256_file(projection_path),
        "effective_composite_sha256": composite,
        "effective_requirement_count": len(ids),
        "effective_requirement_ids": ids,
        "amendment_count": len(observed),
        "anchor_mode": anchor_mode,
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
        "effective_lock_path": effective.get("effective_lock_path"),
        "effective_projection_path": effective.get("effective_projection_path"),
        "effective_composite_sha256": effective.get("effective_composite_sha256"),
        "effective_requirement_count": effective.get("effective_requirement_count", 0),
        "amendment_count": effective.get("amendment_count", 0),
        "anchor_mode": {
            "base": base.get("anchor_mode"),
            "effective": effective.get("anchor_mode"),
        },
    })
    return result
