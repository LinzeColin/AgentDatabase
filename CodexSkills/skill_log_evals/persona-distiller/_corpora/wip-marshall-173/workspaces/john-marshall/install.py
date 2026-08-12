#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SOURCE = Path(__file__).resolve().parent
NAME = SOURCE.name


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_payload(root: Path = SOURCE) -> dict[str, object]:
    checksum_file = root / 'checksums.sha256'
    if not checksum_file.is_file():
        # Development workspaces are installable before packaging; packaged releases must contain it.
        return {'verified': False, 'mode': 'development-workspace', 'files': 0}
    checked = 0
    errors: list[str] = []
    seen: set[str] = set()
    for line_number, line in enumerate(checksum_file.read_text(encoding='utf-8').splitlines(), 1):
        if not line.strip():
            continue
        checksum, sep, rel = line.partition('  ')
        if not sep or len(checksum) != 64:
            errors.append(f'invalid checksum line {line_number}')
            continue
        if rel in seen:
            errors.append(f'duplicate checksum path: {rel}')
            continue
        seen.add(rel)
        candidate = (root / rel).resolve()
        try:
            candidate.relative_to(root.resolve())
        except ValueError:
            errors.append(f'path escapes package: {rel}')
            continue
        if not candidate.is_file():
            errors.append(f'missing payload: {rel}')
            continue
        actual = sha256_file(candidate)
        if actual != checksum:
            errors.append(f'checksum mismatch: {rel}')
        checked += 1
    if checked == 0:
        errors.append('checksum manifest contains no payload files')
    if errors:
        raise ValueError('; '.join(errors))
    return {'verified': True, 'mode': 'checksums.sha256', 'files': checked}


def main() -> int:
    parser = argparse.ArgumentParser(description='Install this target-person Skill.')
    parser.add_argument('--root', type=Path, default=Path.home() / '.codex' / 'skills')
    parser.add_argument('--force', action='store_true')
    parser.add_argument('--link', action='store_true')
    parser.add_argument('--skip-verify', action='store_true', help='Emergency-only: skip release payload checksum verification.')
    args = parser.parse_args()
    try:
        verification = {'verified': False, 'mode': 'skipped', 'files': 0} if args.skip_verify else verify_payload()
    except (ValueError, OSError) as exc:
        print(f'ERROR: package verification failed: {exc}', file=sys.stderr)
        return 2
    destination = args.root.expanduser().resolve() / NAME
    if destination == SOURCE:
        print(json.dumps({'installed': True, 'destination': str(destination), 'mode': 'already-in-place', 'verification': verification, 'source_verification': verification, 'installed_verification': verification}, ensure_ascii=False, indent=2))
        return 0
    backup = None
    if destination.exists() or destination.is_symlink():
        if not args.force:
            print(f'ERROR: destination exists: {destination}; use --force', file=sys.stderr)
            return 2
        stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        backup = destination.with_name(f'{NAME}.backup-{stamp}')
        if backup.exists():
            suffix = 1
            while backup.with_name(f'{backup.name}-{suffix}').exists():
                suffix += 1
            backup = backup.with_name(f'{backup.name}-{suffix}')
        destination.rename(backup)
    destination.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.link:
            destination.symlink_to(SOURCE, target_is_directory=True)
        else:
            shutil.copytree(SOURCE, destination, ignore=shutil.ignore_patterns('__pycache__', '*.pyc', '.DS_Store'))
        installed_verification = verify_payload(destination) if verification.get('mode') == 'checksums.sha256' else {'verified': False, 'mode': 'development-workspace', 'files': 0}
    except Exception:
        if destination.exists() or destination.is_symlink():
            if destination.is_symlink() or destination.is_file():
                destination.unlink()
            else:
                shutil.rmtree(destination)
        if backup and backup.exists():
            backup.rename(destination)
        raise
    print(json.dumps({'installed': True, 'destination': str(destination), 'backup': str(backup) if backup else None, 'mode': 'link' if args.link else 'copy', 'verification': verification, 'source_verification': verification, 'installed_verification': installed_verification}, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
