#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from registry_core import inspect_delivery_zip


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify one Persona Distiller full-delivery ZIP.")
    parser.add_argument("delivery", type=Path)
    args = parser.parse_args()
    try:
        result = inspect_delivery_zip(args.delivery)
    except (OSError, ValueError) as exc:
        print(json.dumps({"passed": False, "error": str(exc)}, ensure_ascii=False, indent=2))
        return 1
    safe = {
        key: str(value) if isinstance(value, Path) else value
        for key, value in result.items()
        if key != "team_card"
    }
    safe["passed"] = True
    print(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
