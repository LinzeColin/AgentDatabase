#!/usr/bin/env python3
"""Fail-closed validator for the one-file dynamic profile contract."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from update_dynamic_profile import validate_profile_file


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    errors = validate_profile_file(args.profile)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: dynamic profile contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
