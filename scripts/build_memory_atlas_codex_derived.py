#!/usr/bin/env python3
"""CLI wrapper for the S07-P2-T1 Codex archive-derived builder."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_atlas_cli.codex_derived import run_codex_derived


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build Codex derived outputs from registered immutable raw archives."
    )
    parser.add_argument("--database-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run_codex_derived(parse_args()))
