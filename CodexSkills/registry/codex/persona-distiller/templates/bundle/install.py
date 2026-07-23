#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path, PurePosixPath

BUNDLE_VERSION = "v0.0.0.5"
SKILL_NAMES = ("persona-distiller", "persona-distiller-group")
SOURCE = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_relative(value: str) -> Path:
    posix = PurePosixPath(value)
    if (
        posix.is_absolute()
        or not posix.parts
        or ".." in posix.parts
        or "\\" in value
        or "\x00" in value
    ):
        raise ValueError(f"unsafe checksum path: {value!r}")
    return Path(*posix.parts)


def verify_bundle() -> dict[str, object]:
    checksum_path = SOURCE / "checksums.sha256"
    if not checksum_path.is_file():
        raise ValueError("checksums.sha256 is missing")
    expected: dict[str, str] = {}
    for line_number, raw in enumerate(
        checksum_path.read_text(encoding="utf-8").splitlines(),
        start=1,
    ):
        if not raw.strip():
            continue
        try:
            digest, relative = raw.split("  ", 1)
        except ValueError as exc:
            raise ValueError(f"invalid checksum line {line_number}") from exc
        if len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError(f"invalid SHA-256 on checksum line {line_number}")
        safe_relative(relative)
        if relative in expected:
            raise ValueError(f"duplicate checksum path: {relative}")
        expected[relative] = digest
    actual = {
        path.relative_to(SOURCE).as_posix()
        for path in SOURCE.rglob("*")
        if path.is_file() and path != checksum_path
    }
    if not actual:
        raise ValueError("bundle contains no payload files")
    missing = sorted(actual - set(expected))
    extra = sorted(set(expected) - actual)
    if missing or extra:
        raise ValueError(
            f"checksum coverage mismatch; missing={missing[:10]}; extra={extra[:10]}"
        )
    mismatches = [
        relative
        for relative, digest in sorted(expected.items())
        if sha256_file(SOURCE / safe_relative(relative)) != digest
    ]
    if mismatches:
        raise ValueError(f"checksum mismatch: {mismatches[:10]}")
    for skill_name in SKILL_NAMES:
        skill_root = SOURCE / skill_name
        if not (skill_root / "SKILL.md").is_file():
            raise ValueError(f"missing bundled Skill: {skill_name}")
        if (skill_root / "VERSION").read_text(encoding="utf-8").strip() != BUNDLE_VERSION:
            raise ValueError(f"bundled Skill version mismatch: {skill_name}")
    return {"verified": True, "files": len(expected)}


def run_validation(staging_root: Path) -> dict[str, object]:
    group = subprocess.run(
        [
            sys.executable,
            str(staging_root / "persona-distiller-group" / "scripts" / "validate_group.py"),
        ],
        cwd=staging_root / "persona-distiller-group",
        text=True,
        capture_output=True,
    )
    if group.returncode != 0:
        raise ValueError(
            "persona-distiller-group validation failed: "
            + (group.stderr.strip() or group.stdout.strip())
        )
    builder = subprocess.run(
        [
            sys.executable,
            str(staging_root / "persona-distiller" / "scripts" / "self_check.py"),
            "--skip-tests",
        ],
        cwd=staging_root / "persona-distiller",
        text=True,
        capture_output=True,
    )
    if builder.returncode != 0:
        raise ValueError(
            "persona-distiller validation failed: "
            + (builder.stderr.strip() or builder.stdout.strip())
        )
    return {
        "group": json.loads(group.stdout),
        "builder": json.loads(builder.stdout),
    }


def move_to_backup(path: Path, backup_root: Path, label: str) -> Path:
    destination = backup_root / label
    destination.parent.mkdir(parents=True, exist_ok=True)
    os.replace(path, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Atomically install Persona Distiller and its canonical expert-team registry."
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.home() / ".codex" / "skills",
        help="Skill root; defaults to ~/.codex/skills",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="replace existing copies of the two bundled Skills",
    )
    parser.add_argument(
        "--remove-conflicts",
        action="store_true",
        help="remove duplicate copies from ~/.agents/skills after the new install validates",
    )
    args = parser.parse_args()
    install_root = args.root.expanduser().resolve()
    default_root = (Path.home() / ".codex" / "skills").resolve()
    legacy_root = (Path.home() / ".agents" / "skills").resolve()
    destinations = {name: install_root / name for name in SKILL_NAMES}
    conflicts = {
        name: legacy_root / name
        for name in SKILL_NAMES
        if install_root == default_root and (legacy_root / name).exists()
    }
    try:
        source_verification = verify_bundle()
        existing = [name for name, path in destinations.items() if path.exists()]
        if existing and not args.force:
            raise ValueError(
                "existing Skill copies require --force: " + ", ".join(existing)
            )
        if conflicts and not args.remove_conflicts:
            raise ValueError(
                "duplicate sources exist under ~/.agents/skills; rerun with "
                "--remove-conflicts: " + ", ".join(sorted(conflicts))
            )
        install_root.parent.mkdir(parents=True, exist_ok=True)
        install_root.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(
            prefix=".persona-distiller-install-",
            dir=install_root.parent,
        ) as temporary:
            transaction = Path(temporary)
            staging_root = transaction / "staging"
            backup_root = transaction / "backup"
            staging_root.mkdir()
            for name in SKILL_NAMES:
                shutil.copytree(
                    SOURCE / name,
                    staging_root / name,
                    symlinks=False,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"),
                )
            staged_validation = run_validation(staging_root)
            moved: list[tuple[Path, Path]] = []
            installed: list[Path] = []
            try:
                for name, destination in destinations.items():
                    if destination.exists():
                        backup = move_to_backup(
                            destination,
                            backup_root,
                            f"codex/{name}",
                        )
                        moved.append((backup, destination))
                for name, conflict in conflicts.items():
                    backup = move_to_backup(
                        conflict,
                        backup_root,
                        f"agents/{name}",
                    )
                    moved.append((backup, conflict))
                for name, destination in destinations.items():
                    os.replace(staging_root / name, destination)
                    installed.append(destination)
                installed_validation = run_validation(install_root)
            except Exception:
                for destination in reversed(installed):
                    if destination.exists():
                        shutil.rmtree(destination)
                for backup, original in reversed(moved):
                    if backup.exists():
                        original.parent.mkdir(parents=True, exist_ok=True)
                        os.replace(backup, original)
                raise
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "installed": True,
                "version": BUNDLE_VERSION,
                "root": str(install_root),
                "skills": list(SKILL_NAMES),
                "removed_conflicts": sorted(conflicts),
                "bundle_verification": source_verification,
                "staged_validation": {
                    "builder_passed": bool(staged_validation["builder"].get("passed")),
                    "group_passed": bool(staged_validation["group"].get("passed")),
                },
                "installed_validation": {
                    "builder_passed": bool(installed_validation["builder"].get("passed")),
                    "group_passed": bool(installed_validation["group"].get("passed")),
                },
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
