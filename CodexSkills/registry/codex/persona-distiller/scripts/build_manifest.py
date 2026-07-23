#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, atomic_write_text, sha256_file

ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    '.git', '.mypy_cache', '.pytest_cache', '.ruff_cache', '__pycache__',
    '_build', 'build', 'dist', 'workspaces',
}
MUTABLE_REGISTRY_STATIC_FILES = {'README.md', '_category.json'}


def included(path: Path) -> bool:
    relative = path.relative_to(ROOT)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.suffix in {'.pyc', '.pyo', '.zip'}:
        return False
    if relative.as_posix() in {'PACKAGE_MANIFEST.json', 'checksums.sha256'}:
        return False
    if relative.parts and relative.parts[0] == '产物登记':
        return path.name in MUTABLE_REGISTRY_STATIC_FILES
    return True


def main() -> int:
    manifest_path = ROOT / 'PACKAGE_MANIFEST.json'
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    files = sorted(path for path in ROOT.rglob('*') if path.is_file() and included(path))
    records = [
        {
            'path': path.relative_to(ROOT).as_posix(),
            'sha256': sha256_file(path),
            'size_bytes': path.stat().st_size,
        }
        for path in files
    ]
    manifest['files'] = records
    manifest['distribution'] = {
        'kind': 'repository-customized-v0.0.0.3',
        'source_archive_sha256': 'e891912d98d14afb7677ac935a19be329d97d206f4ae74a644892f46b17f6748',
    }
    manifest['mutable_paths'] = {
        'excluded_from_release_checksums': [
            '产物登记/index.json',
            '产物登记/<分类>/<人物>/registration.json',
            '产物登记/<分类>/<人物>/versions/<model_version>/*.zip',
        ],
        'validation': 'python3 scripts/validate_persona_registry.py',
    }
    atomic_write_json(manifest_path, manifest)
    checksum_paths = files + [manifest_path]
    lines = ''.join(
        f'{sha256_file(path)}  {path.relative_to(ROOT).as_posix()}\n'
        for path in sorted(checksum_paths)
    )
    atomic_write_text(ROOT / 'checksums.sha256', lines)
    print(json.dumps({
        'package_manifest_files': len(records),
        'checksum_files': len(checksum_paths),
        'mutable_registry_files_excluded': True,
    }, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
