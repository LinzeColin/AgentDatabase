#!/usr/bin/env python3
"""CLI wrapper for the S09-P1-T3 ChatGPT derived-input builder."""

from __future__ import annotations

import argparse
from pathlib import Path

from memory_atlas_cli.chatgpt_derived import run_chatgpt_derived


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build ChatGPT derived inputs from canonical events and public raw."
    )
    parser.add_argument("--database-dir", type=Path, required=True)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


if __name__ == "__main__":
    raise SystemExit(run_chatgpt_derived(parse_args()))
