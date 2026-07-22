#!/usr/bin/env python3
"""Initialize ignored private runtime directories."""

import argparse
import json
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.private_runtime import ensure_private_runtime  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--module-root", type=Path, default=MODULE_ROOT)
    args = parser.parse_args()
    try:
        directories = ensure_private_runtime(args.module_root)
    except (OSError, RuntimeError) as exc:
        print(json.dumps({"status": "BLOCKED", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 2
    print(
        json.dumps(
            {
                "status": "READY",
                "private_runtime_root": str((args.module_root.resolve() / "private_runtime")),
                "directories": [str(path) for path in directories],
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
