from __future__ import annotations

import argparse
import json
import subprocess
import sys

from .constants import (
    DIFF_NARRATOR_BUILDER,
    PROPOSAL_APPLY_BUILDER,
    PROPOSAL_STATE_BUILDER,
    ROOT,
)


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
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if args.dry_run and result.returncode == 0 and result.stdout:
        payload = json.loads(result.stdout)
        payload["command"] = "proposals"
        payload["dry_run"] = True
        payload.setdefault("writes_files", False)
        payload.setdefault("raw_mutation", False)
        payload["phase_status"] = payload.get("status")
        payload["status"] = "PASS"
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    elif result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


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
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode

__all__ = (
    "run_proposals",
    "run_apply",
)
