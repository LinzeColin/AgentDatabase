#!/usr/bin/env python3
"""Run the S09-P2-T2 standard Agent fixture in an ephemeral workspace."""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path

from memory_atlas_cli.generic_agent_fixture import (
    FixtureAcceptanceError,
    run_generic_agent_fixture,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        with tempfile.TemporaryDirectory(prefix="memory-atlas-s09-p2-t2-") as temp_dir:
            result = run_generic_agent_fixture(
                args.database_dir.resolve(),
                Path(temp_dir),
            )
            result["workspace_persisted"] = False
    except FixtureAcceptanceError as exc:
        result = {
            "status": "FAIL_CLOSED",
            "task_id": "S09-P2-T2",
            "acceptance_id": "ACC-MA-V121-S09-P2-T2",
            "reason": str(exc),
            "workspace_persisted": False,
            "production_database_mutation": False,
            "remote_push": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
