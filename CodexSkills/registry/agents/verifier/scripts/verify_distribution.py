#!/usr/bin/env python3
"""Build or verify deterministic Verifier skill manifests and checksums (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

SCHEMA_VERSION = "1.0"
MANIFEST_NAME = "MANIFEST.json"
CHECKSUMS_NAME = "SHA256SUMS.txt"
IGNORED_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
IGNORED_SUFFIXES = {".pyc", ".pyo"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_cache_path(relative: Path) -> bool:
    return bool(set(relative.parts) & IGNORED_DIRS) or relative.suffix in IGNORED_SUFFIXES


def collect_files(root: Path, mode: str, excludes: set[str]) -> tuple[list[Path], list[str]]:
    files: list[Path] = []
    errors: list[str] = []
    lowered: dict[str, str] = {}
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix().casefold()):
        relative = path.relative_to(root)
        rel = relative.as_posix()
        if rel in excludes:
            continue
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
        if is_cache_path(relative):
            if mode == "distribution":
                errors.append(f"cache/compiled artifact forbidden in distribution: {rel}")
            continue
        if any(part in {".", ".."} for part in relative.parts) or "\\" in rel or "\x00" in rel:
            errors.append(f"non-portable path: {rel!r}")
        key = rel.casefold()
        if key in lowered and lowered[key] != rel:
            errors.append(f"case-colliding paths: {lowered[key]} / {rel}")
        lowered[key] = rel
        files.append(path)
    return files, errors


def manifest_entries(root: Path, files: Iterable[Path]) -> list[dict[str, Any]]:
    return [
        {
            "path": path.relative_to(root).as_posix(),
            "size": path.stat().st_size,
            "sha256": sha256_file(path),
        }
        for path in files
    ]


def canonical_manifest(entries: list[dict[str, Any]], version: str) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "skill": "verifier",
        "skill_version": version,
        "generated_at": "deterministic-build",
        "hash_algorithm": "sha256",
        "excludes": [MANIFEST_NAME, CHECKSUMS_NAME, "runtime caches"],
        "entries": entries,
    }


def read_version(root: Path) -> str:
    version_path = root / "VERSION"
    if not version_path.is_file():
        raise ValueError("VERSION missing")
    version = version_path.read_text(encoding="utf-8").strip()
    if not version:
        raise ValueError("VERSION empty")
    return version


def build(root: Path) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    files, errors = collect_files(root, "distribution", {MANIFEST_NAME, CHECKSUMS_NAME})
    if errors:
        raise ValueError("; ".join(errors))
    entries = manifest_entries(root, files)
    manifest = canonical_manifest(entries, read_version(root))
    (root / MANIFEST_NAME).write_text(json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    checksum_files, checksum_errors = collect_files(root, "distribution", {CHECKSUMS_NAME})
    if checksum_errors:
        raise ValueError("; ".join(checksum_errors))
    lines = [f"{sha256_file(path)}  {path.relative_to(root).as_posix()}" for path in checksum_files]
    (root / CHECKSUMS_NAME).write_text("\n".join(lines) + "\n", encoding="utf-8")
    return {
        "ok": True,
        "root": str(root),
        "skill_version": manifest["skill_version"],
        "manifest_entry_count": len(entries),
        "checksum_entry_count": len(lines),
        "built_at": utc_now(),
    }


def load_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"invalid {MANIFEST_NAME}: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{MANIFEST_NAME} root must be object")
    return value


def parse_checksums(path: Path) -> tuple[dict[str, str], list[str]]:
    entries: dict[str, str] = {}
    errors: list[str] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return {}, [f"cannot read {CHECKSUMS_NAME}: {error}"]
    for number, line in enumerate(lines, 1):
        if not line:
            continue
        if "  " not in line:
            errors.append(f"{CHECKSUMS_NAME}:{number}: invalid format")
            continue
        digest, rel = line.split("  ", 1)
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            errors.append(f"{CHECKSUMS_NAME}:{number}: invalid digest")
            continue
        if rel in entries:
            errors.append(f"{CHECKSUMS_NAME}:{number}: duplicate path {rel}")
        entries[rel] = digest
    return entries, errors


def verify(root: Path, mode: str) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    errors: list[str] = []
    manifest_path = root / MANIFEST_NAME
    checksums_path = root / CHECKSUMS_NAME
    if not manifest_path.is_file():
        errors.append(f"missing {MANIFEST_NAME}")
    if not checksums_path.is_file():
        errors.append(f"missing {CHECKSUMS_NAME}")
    if errors:
        return {"ok": False, "root": str(root), "mode": mode, "errors": errors}

    try:
        manifest = load_manifest(manifest_path)
    except ValueError as error:
        errors.append(str(error))
        manifest = {}
    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"{MANIFEST_NAME} schema_version must be {SCHEMA_VERSION}")
    if manifest.get("skill") != "verifier":
        errors.append(f"{MANIFEST_NAME} skill must be verifier")
    try:
        version = read_version(root)
    except ValueError as error:
        errors.append(str(error))
        version = ""
    if manifest.get("skill_version") != version:
        errors.append("MANIFEST skill_version does not match VERSION")

    actual_files, tree_errors = collect_files(root, mode, {MANIFEST_NAME, CHECKSUMS_NAME})
    errors.extend(tree_errors)
    actual_entries = {item["path"]: item for item in manifest_entries(root, actual_files)}
    expected_list = manifest.get("entries")
    expected_entries: dict[str, dict[str, Any]] = {}
    if not isinstance(expected_list, list):
        errors.append("MANIFEST entries must be a list")
    else:
        for item in expected_list:
            if not isinstance(item, dict) or not isinstance(item.get("path"), str):
                errors.append("MANIFEST contains invalid entry")
                continue
            rel = item["path"]
            if rel in expected_entries:
                errors.append(f"MANIFEST duplicate entry: {rel}")
            expected_entries[rel] = item

    for rel in sorted(set(expected_entries) - set(actual_entries)):
        errors.append(f"manifest file missing: {rel}")
    for rel in sorted(set(actual_entries) - set(expected_entries)):
        errors.append(f"unmanifested file: {rel}")
    for rel in sorted(set(actual_entries) & set(expected_entries)):
        expected = expected_entries[rel]
        actual = actual_entries[rel]
        if expected.get("size") != actual["size"]:
            errors.append(f"size mismatch: {rel}")
        if expected.get("sha256") != actual["sha256"]:
            errors.append(f"sha256 mismatch: {rel}")

    expected_checksums, checksum_parse_errors = parse_checksums(checksums_path)
    errors.extend(checksum_parse_errors)
    checksum_files, checksum_tree_errors = collect_files(root, mode, {CHECKSUMS_NAME})
    errors.extend(checksum_tree_errors)
    actual_checksums = {path.relative_to(root).as_posix(): sha256_file(path) for path in checksum_files}
    for rel in sorted(set(expected_checksums) - set(actual_checksums)):
        errors.append(f"checksummed file missing: {rel}")
    for rel in sorted(set(actual_checksums) - set(expected_checksums)):
        errors.append(f"file missing from {CHECKSUMS_NAME}: {rel}")
    for rel in sorted(set(actual_checksums) & set(expected_checksums)):
        if expected_checksums[rel] != actual_checksums[rel]:
            errors.append(f"checksum mismatch: {rel}")

    return {
        "ok": not errors,
        "root": str(root),
        "mode": mode,
        "skill_version": version,
        "manifest_entry_count": len(expected_entries),
        "checksum_entry_count": len(expected_checksums),
        "errors": errors,
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build_parser = sub.add_parser("build")
    build_parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    build_parser.add_argument("--json", action="store_true")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("root", nargs="?", type=Path, default=Path(__file__).resolve().parent.parent)
    verify_parser.add_argument("--mode", choices=("distribution", "installed"), default="installed")
    verify_parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = build(args.root) if args.command == "build" else verify(args.root, args.mode)
    except (OSError, ValueError) as error:
        result = {"ok": False, "error": str(error)}
    if args.json or not result.get("ok"):
        stream = sys.stdout if result.get("ok") else sys.stderr
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True), file=stream)
    else:
        print(f"VALID DISTRIBUTION: {result['root']} version={result['skill_version']} mode={result.get('mode', 'build')}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
