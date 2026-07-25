#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from persona_registry import default_registry_root, register_product, validate_registry


def main() -> int:
    parser = argparse.ArgumentParser(
        description='Register one released target-person Skill ZIP in exactly one identity category.',
    )
    parser.add_argument('package', type=Path)
    parser.add_argument('--registry-root', type=Path, default=default_registry_root())
    args = parser.parse_args()
    try:
        result = register_product(args.package, args.registry_root)
        validation = validate_registry(args.registry_root)
        if not validation['passed']:
            raise ValueError('post-registration validation failed: ' + '; '.join(validation['errors']))
    except (OSError, ValueError, zipfile.BadZipFile) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2
    print(json.dumps({'registration': result, 'validation': validation}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
