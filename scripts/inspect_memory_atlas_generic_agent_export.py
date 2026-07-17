#!/usr/bin/env python3
"""Inspect a standard Agent export through the S09-P2-T1 read-only adapter."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from memory_atlas_cli.generic_agent_read_adapter import (
    GenericAgentReadError,
    read_generic_agent_export,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Inspect a standard Agent export read-only.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--input", type=Path, required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        result = read_generic_agent_export(
            args.database_dir.resolve(),
            args.input.expanduser().absolute(),
        )
    except GenericAgentReadError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "task_id": "S09-P2-T1",
            "reason": exc.code,
            "source_read_only": True,
            "writes_files": False,
            "network_access": False,
            "remote_push": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result.public_summary(), ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
