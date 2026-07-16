#!/usr/bin/env python3
"""CLI wrapper for the S07-P3-T3 Codex restore proof."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from memory_atlas_cli.codex_restore_proof import run_codex_restore_proof


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Restore one Codex archive twice and prove deterministic derived rebuilds."
    )
    parser.add_argument("--database-dir", type=Path, required=True)
    parser.add_argument("--archive-id", required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run_codex_restore_proof(parse_args()))
