#!/usr/bin/env python3
"""Ingest a registry-bound external plugin envelope through host-owned gates."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from memory_atlas_cli.generic_agent_plugin import (
    ACCEPTANCE_ID,
    TASK_ID,
    GenericAgentPluginError,
    run_generic_agent_plugin,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--source-id", required=True)
    parser.add_argument("--agent-id", required=True)
    parser.add_argument("--plugin-id", required=True)
    parser.add_argument("--plugin-envelope", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.agent_id != args.source_id:
        result = {
            "status": "FAIL_CLOSED",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "reason": "plugin_agent_source_identity_mismatch",
            "writes_files": False,
            "production_database_mutation": False,
            "remote_push": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    try:
        result = run_generic_agent_plugin(
            package_root=Path(__file__).resolve().parents[1],
            database_dir=args.database_dir,
            source_id=args.source_id,
            plugin_id=args.plugin_id,
            envelope_path=args.plugin_envelope,
            dry_run=args.dry_run,
        )
    except GenericAgentPluginError as exc:
        result = {
            "status": "FAIL_CLOSED",
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": args.source_id,
            "reason": str(exc),
            "writes_files": False,
            "production_database_mutation": False,
            "remote_push": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
