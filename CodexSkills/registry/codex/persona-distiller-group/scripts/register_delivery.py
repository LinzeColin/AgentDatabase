#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from registry_core import default_registry_root, register_product, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(description="Uniquely register one full persona delivery ZIP.")
    parser.add_argument("delivery", type=Path)
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    args = parser.parse_args()
    try:
        result = register_product(args.delivery, args.registry_root)
        validation = validate_registry(args.registry_root)
    except (OSError, ValueError) as exc:
        print(json.dumps({"registered": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    result["registry_validation"] = validation
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if validation["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
