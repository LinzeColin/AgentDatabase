#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_registry import default_registry_root, validate_registry, write_index


def main() -> int:
    parser = argparse.ArgumentParser(description='Validate unique target-person registration across all seven categories.')
    parser.add_argument('--registry-root', type=Path, default=default_registry_root())
    parser.add_argument('--rebuild-index', action='store_true')
    args = parser.parse_args()
    try:
        if args.rebuild_index:
            write_index(args.registry_root.expanduser().resolve())
        result = validate_registry(args.registry_root)
    except (OSError, ValueError) as exc:
        print(json.dumps({'passed': False, 'errors': [str(exc)]}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['passed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
