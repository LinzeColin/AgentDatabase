#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from registry_core import default_registry_root, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate the canonical persona expert-team registry.")
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    args = parser.parse_args()
    result = validate_registry(args.registry_root)
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
