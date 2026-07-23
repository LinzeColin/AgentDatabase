#!/usr/bin/env python3
"""Run A1b fault/privacy tests in a deterministic seed-shuffled order."""

from __future__ import annotations

import argparse
import json
import random
import sys
import unittest
from pathlib import Path


AUTO_DIR = Path(__file__).resolve().parents[1]
TEST_DIR = AUTO_DIR / "tests"
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(TEST_DIR))


def flatten(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from flatten(item)
        else:
            yield item


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, required=True)
    args = parser.parse_args()
    discovered = unittest.defaultTestLoader.discover(
        str(TEST_DIR), pattern="test_runtime_*.py"
    )
    tests = list(flatten(discovered))
    random.Random(args.seed).shuffle(tests)
    result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(
        unittest.TestSuite(tests)
    )
    evidence = {
        "errors": len(result.errors),
        "failures": len(result.failures),
        "seed": args.seed,
        "skipped": len(result.skipped),
        "successful": result.wasSuccessful(),
        "test_count": result.testsRun,
    }
    print(json.dumps(evidence, sort_keys=True, separators=(",", ":")))
    return 0 if result.wasSuccessful() else 2


if __name__ == "__main__":
    raise SystemExit(main())
