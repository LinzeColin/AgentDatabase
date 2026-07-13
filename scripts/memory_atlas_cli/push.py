from __future__ import annotations

import argparse
import sys

from .constants import (
    GITHUB_BACKUP,
    ROOT,
)
from .child_process import run_child_command


def run_push(args: argparse.Namespace) -> int:
    command = [sys.executable, str(GITHUB_BACKUP), "--database-dir", str(args.database_dir)]
    if args.dry_run:
        command.append("--dry-run")
    if args.apply:
        command.extend(["--apply", "--message", args.message])
    return run_child_command(command, cwd=ROOT)

__all__ = (
    "run_push",
)
