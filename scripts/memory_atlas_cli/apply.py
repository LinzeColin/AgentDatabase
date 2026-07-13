from __future__ import annotations

import argparse
import json
import sys

from .constants import (
    DIFF_NARRATOR_BUILDER,
    PROPOSAL_APPLY_BUILDER,
    PROPOSAL_STATE_BUILDER,
    ROOT,
)
from .child_process import StdoutTransform, run_child_command


def _proposal_stdout_transform(dry_run: bool) -> StdoutTransform:
    def transform(stdout: str, returncode: int) -> str:
        if not dry_run or returncode != 0 or not stdout:
            return stdout
        payload = json.loads(stdout)
        payload["command"] = "proposals"
        payload["dry_run"] = True
        payload.setdefault("writes_files", False)
        payload.setdefault("raw_mutation", False)
        payload["phase_status"] = payload.get("status")
        payload["status"] = "PASS"
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    return transform


def run_proposals(args: argparse.Namespace) -> int:
    builder = PROPOSAL_STATE_BUILDER
    if args.view == "diff-narrator":
        builder = DIFF_NARRATOR_BUILDER
    command = [
        sys.executable,
        str(builder),
        "--database-dir",
        str(args.database_dir),
    ]
    if args.dry_run:
        command.append("--dry-run")
    return run_child_command(
        command,
        cwd=ROOT,
        stdout_transform=_proposal_stdout_transform(args.dry_run),
    )


def run_apply(args: argparse.Namespace) -> int:
    command = [
        sys.executable,
        str(PROPOSAL_APPLY_BUILDER),
        "--database-dir",
        str(args.database_dir),
        "--proposal",
        args.proposal,
    ]
    if args.dry_run:
        command.append("--dry-run")
    if args.simulate_validation_failure:
        command.append("--simulate-validation-failure")
    return run_child_command(command, cwd=ROOT)

__all__ = (
    "run_proposals",
    "run_apply",
)
