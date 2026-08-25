#!/usr/bin/env python3
"""Install Video Prompt Compiler into Codex, Claude Code, or a custom skill directory."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent
SKILL_NAME = "video-prompt-compiler"
INCLUDE = [
    "SKILL.md", "README.md", "README_FIRST.md", "QUICKSTART.md", "INSTALL.md", "VERSION",
    "LICENSE", "NOTICE.md", "manifest.json", ".ramify", "references", "research", "presets", "schemas", "scripts", "bridges", "examples", "tests", "taskpack"
]


def targets(kind: str) -> list[Path]:
    home = Path.home()
    if kind == "codex":
        return [home / ".codex" / "skills" / SKILL_NAME]
    if kind == "claude":
        return [home / ".claude" / "skills" / SKILL_NAME]
    if kind == "both":
        return [home / ".codex" / "skills" / SKILL_NAME, home / ".claude" / "skills" / SKILL_NAME]
    raise ValueError(kind)


def copy_item(src: Path, dst: Path) -> None:
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)


def install(dest: Path, force: bool, dry_run: bool) -> None:
    if dest.exists() and not force:
        raise FileExistsError(f"destination exists: {dest}; use --force to replace/update")
    if dry_run:
        print(f"DRY_RUN target={dest}")
        for rel in INCLUDE:
            print(f"  {rel}")
        return
    if dest.exists() and force:
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    for rel in INCLUDE:
        src = PACKAGE_ROOT / rel
        if not src.exists():
            raise FileNotFoundError(f"required package item missing: {src}")
        copy_item(src, dest / rel)
    print(f"INSTALLED {dest}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Install Video Prompt Compiler Agent Skill.")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--target", choices=["codex", "claude", "both"])
    group.add_argument("--target-path", type=Path, help="Parent skills directory; skill folder is created below it")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    destinations = targets(args.target) if args.target else [args.target_path.expanduser().resolve() / SKILL_NAME]
    try:
        for dest in destinations:
            install(dest, args.force, args.dry_run)
        return 0
    except (OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
