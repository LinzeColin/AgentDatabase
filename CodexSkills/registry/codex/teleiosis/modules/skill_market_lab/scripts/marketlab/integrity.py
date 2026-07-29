from __future__ import annotations

import fnmatch
import os
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence

from .common import ValidationError, file_sha256, object_sha256, read_json, utc_now, write_json

DEFAULT_EXCLUDES = (
    ".DS_Store",
    "__pycache__/*",
    "*.pyc",
    ".pytest_cache/*",
    ".git/*",
)


def _is_excluded(relative: str, excludes: Sequence[str]) -> bool:
    return any(fnmatch.fnmatch(relative, pattern) or fnmatch.fnmatch(Path(relative).name, pattern) for pattern in excludes)


def inventory_tree(root: Path, excludes: Sequence[str] = DEFAULT_EXCLUDES) -> List[Dict[str, Any]]:
    root = root.resolve()
    if not root.is_dir():
        raise ValidationError(f"不是目录: {root}")
    entries: List[Dict[str, Any]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if _is_excluded(relative, excludes):
            continue
        if path.is_symlink():
            raise ValidationError(f"拒绝封存符号链接: {relative}")
        if path.is_dir():
            continue
        stat = path.stat()
        entries.append(
            {
                "path": relative,
                "size": stat.st_size,
                "mode": oct(stat.st_mode & 0o777),
                "sha256": file_sha256(path),
            }
        )
    return entries


def seal_tree(
    root: Path,
    manifest_path: Path,
    excludes: Sequence[str] = DEFAULT_EXCLUDES,
) -> Dict[str, Any]:
    root = root.resolve()
    manifest_path = manifest_path.resolve()
    effective_excludes = list(excludes)
    if root == manifest_path.parent or root in manifest_path.parents:
        effective_excludes.append(manifest_path.relative_to(root).as_posix())
    entries = inventory_tree(root, effective_excludes)
    manifest = {
        "schema_version": "1.0",
        "root_name": root.name,
        "created_at": utc_now(),
        "entry_count": len(entries),
        "entries": entries,
        "tree_digest": object_sha256(entries),
    }
    write_json(manifest_path, manifest)
    return manifest


def verify_tree(root: Path, manifest: Mapping[str, Any]) -> Dict[str, Any]:
    root = root.resolve()
    if not isinstance(manifest, dict) or not isinstance(manifest.get("entries"), list):
        raise ValidationError("封存清单无效")
    expected = {item["path"]: item for item in manifest["entries"]}
    actual_entries = inventory_tree(root, excludes=DEFAULT_EXCLUDES)
    # Allow the manifest file itself and top-level package checksums to exist outside its own entry set.
    actual = {item["path"]: item for item in actual_entries if item["path"] in expected}
    missing = sorted(set(expected) - set(actual))
    changed = sorted(
        path
        for path in set(expected) & set(actual)
        if expected[path].get("sha256") != actual[path].get("sha256")
        or expected[path].get("size") != actual[path].get("size")
    )
    unexpected = sorted(
        path
        for path in set(item["path"] for item in actual_entries) - set(expected)
        if Path(path).name not in {"TREE_MANIFEST.json", "MANIFEST.json", "checksums.sha256"}
    )
    calculated_tree_digest = object_sha256([expected[path] for path in sorted(expected)])
    digest_matches = calculated_tree_digest == manifest.get("tree_digest")
    valid = not missing and not changed and not unexpected and digest_matches
    return {
        "valid": valid,
        "missing": missing,
        "changed": changed,
        "unexpected": unexpected,
        "manifest_tree_digest": manifest.get("tree_digest"),
        "calculated_tree_digest": calculated_tree_digest,
        "digest_matches": digest_matches,
    }


def load_and_verify_tree(root: Path, manifest_path: Path) -> Dict[str, Any]:
    return verify_tree(root, read_json(manifest_path))
