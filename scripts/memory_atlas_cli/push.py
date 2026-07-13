from __future__ import annotations

import argparse
import subprocess
import sys

from .constants import (
    GITHUB_BACKUP,
    ROOT,
)


def run_push(args: argparse.Namespace) -> int:
    command = [sys.executable, str(GITHUB_BACKUP), "--database-dir", str(args.database_dir)]
    if args.dry_run:
        command.append("--dry-run")
    if args.apply:
        command.extend(["--apply", "--message", args.message])
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode

__all__ = (
    "run_push",
)
