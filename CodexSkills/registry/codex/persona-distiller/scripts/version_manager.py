#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (
    atomic_write_bytes,
    atomic_write_json,
    compact_utc,
    ensure_dir,
    ensure_target,
    iter_tracked_files,
    read_json,
    save_meta,
    sha256_file,
    target_lock,
    utc_now,
)

STATUSES = ('candidate', 'accepted', 'rejected', 'release', 'backup')


def manifest_digest(files: list[dict[str, Any]]) -> str:
    canonical = json.dumps(files, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode('utf-8')
    return hashlib.sha256(canonical).hexdigest()


def current_file_records(target: Path, include_sources: bool = False) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in iter_tracked_files(target, include_sources=include_sources):
        if path.is_symlink():
            raise ValueError(f'symlinks are not snapshot-safe: {path}')
        rel = path.relative_to(target).as_posix()
        records.append({'path': rel, 'sha256': sha256_file(path), 'size': path.stat().st_size})
    return records


def snapshot_locked(
    target: Path,
    reason: str,
    status: str = 'candidate',
    include_sources: bool = False,
    update_current: bool = True,
) -> dict[str, Any]:
    meta = ensure_target(target)
    versions = ensure_dir(target / 'versions')
    files = current_file_records(target, include_sources=include_sources)
    digest = manifest_digest(files)
    version_id = f'v{compact_utc()}-{digest[:8]}'
    final_dir = versions / version_id
    if final_dir.exists():
        manifest = read_json(final_dir / 'manifest.json')
        if update_current:
            meta['current_version'] = version_id
            save_meta(target, meta)
        return manifest

    temp_dir = Path(tempfile.mkdtemp(prefix='.snapshot-', dir=str(versions)))
    try:
        payload_root = temp_dir / 'files'
        for record in files:
            src = target / record['path']
            dst = payload_root / record['path']
            ensure_dir(dst.parent)
            shutil.copy2(src, dst)
        manifest = {
            'schema_version': '1.0',
            'version_id': version_id,
            'created_at': utc_now(),
            'reason': reason,
            'parent_version': meta.get('current_version'),
            'status': status,
            'include_sources': include_sources,
            'files': files,
            'digest': digest,
        }
        atomic_write_json(temp_dir / 'manifest.json', manifest, mode=0o600)
        os.replace(temp_dir, final_dir)
    finally:
        if temp_dir.exists():
            shutil.rmtree(temp_dir)
    if update_current:
        meta['current_version'] = version_id
        save_meta(target, meta)
    return manifest


def snapshot_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    with target_lock(target):
        manifest = snapshot_locked(target, args.reason, args.status, args.include_sources)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def load_manifest(target: Path, version_id: str) -> dict[str, Any]:
    path = target / 'versions' / version_id / 'manifest.json'
    manifest = read_json(path)
    if not isinstance(manifest, dict):
        raise ValueError(f'unknown or invalid version: {version_id}')
    return manifest


def verify_manifest(target: Path, version_id: str) -> dict[str, Any]:
    manifest = load_manifest(target, version_id)
    errors: list[str] = []
    files = manifest.get('files', [])
    if manifest_digest(files) != manifest.get('digest'):
        errors.append('manifest digest mismatch')
    payload_root = target / 'versions' / version_id / 'files'
    for record in files:
        rel = Path(record.get('path', ''))
        if rel.is_absolute() or '..' in rel.parts:
            errors.append(f'unsafe path in manifest: {rel}')
            continue
        path = payload_root / rel
        if not path.is_file():
            errors.append(f'missing snapshot file: {rel.as_posix()}')
            continue
        if path.stat().st_size != record.get('size'):
            errors.append(f'size mismatch: {rel.as_posix()}')
        if sha256_file(path) != record.get('sha256'):
            errors.append(f'hash mismatch: {rel.as_posix()}')
    return {'ok': not errors, 'version_id': version_id, 'files': len(files), 'errors': errors}


def verify_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    result = verify_manifest(target, args.version)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['ok'] else 1


def list_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    pins = read_json(target / 'versions' / 'pins.json', default={}) or {}
    versions: list[dict[str, Any]] = []
    versions_root = target / 'versions'
    if versions_root.exists():
        for path in sorted(versions_root.iterdir(), reverse=True):
            if not path.is_dir() or path.name.startswith('.'):
                continue
            manifest = read_json(path / 'manifest.json')
            if isinstance(manifest, dict):
                versions.append({
                    'version_id': manifest.get('version_id'),
                    'created_at': manifest.get('created_at'),
                    'reason': manifest.get('reason'),
                    'status': manifest.get('status'),
                    'parent_version': manifest.get('parent_version'),
                    'files': len(manifest.get('files', [])),
                    'pinned': bool(pins.get(path.name)),
                    'current': path.name == meta.get('current_version'),
                })
    print(json.dumps({'current_version': meta.get('current_version'), 'versions': versions}, ensure_ascii=False, indent=2))
    return 0


def resolve_state(target: Path, value: str, include_sources: bool = False) -> tuple[str, dict[str, str]]:
    if value == 'current':
        records = current_file_records(target, include_sources=include_sources)
        return 'current', {record['path']: record['sha256'] for record in records}
    manifest = load_manifest(target, value)
    return value, {record['path']: record['sha256'] for record in manifest.get('files', [])}


def diff_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    from_name, left = resolve_state(target, args.from_version, args.include_sources)
    to_name, right = resolve_state(target, args.to_version, args.include_sources)
    left_keys = set(left)
    right_keys = set(right)
    result = {
        'from': from_name,
        'to': to_name,
        'added': sorted(right_keys - left_keys),
        'removed': sorted(left_keys - right_keys),
        'modified': sorted(path for path in left_keys & right_keys if left[path] != right[path]),
        'unchanged': sum(1 for path in left_keys & right_keys if left[path] == right[path]),
    }
    result['changed'] = len(result['added']) + len(result['removed']) + len(result['modified'])
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def rollback_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    verification = verify_manifest(target, args.version)
    if not verification['ok']:
        print(json.dumps(verification, ensure_ascii=False, indent=2), file=sys.stderr)
        return 1

    manifest = load_manifest(target, args.version)
    payload_root = target / 'versions' / args.version / 'files'
    with target_lock(target):
        backup_manifest = None
        if not args.no_backup:
            backup_manifest = snapshot_locked(
                target,
                reason=f'pre-rollback backup before restoring {args.version}',
                status='backup',
                include_sources=bool(manifest.get('include_sources')),
                update_current=True,
            )
        snapshot_paths = {record['path'] for record in manifest.get('files', [])}
        current_paths = {record['path'] for record in current_file_records(target, include_sources=bool(manifest.get('include_sources')))}
        for rel in sorted(current_paths - snapshot_paths, reverse=True):
            path = target / rel
            if path.exists() and not path.is_symlink():
                path.unlink()
        for record in manifest.get('files', []):
            rel = Path(record['path'])
            if rel.is_absolute() or '..' in rel.parts:
                raise ValueError(f'unsafe snapshot path: {rel}')
            src = payload_root / rel
            dst = target / rel
            atomic_write_bytes(dst, src.read_bytes(), mode=src.stat().st_mode & 0o777)
        meta = ensure_target(target)
        meta['current_version'] = args.version
        meta['last_rollback'] = {'at': utc_now(), 'from_backup': backup_manifest.get('version_id') if backup_manifest else None}
        save_meta(target, meta)
    result = {
        'ok': True,
        'restored': args.version,
        'pre_rollback_backup': backup_manifest.get('version_id') if backup_manifest else None,
        'files': len(manifest.get('files', [])),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def pin_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    load_manifest(target, args.version)
    pins_path = target / 'versions' / 'pins.json'
    pins = read_json(pins_path, default={}) or {}
    if args.command == 'pin':
        pins[args.version] = {'pinned_at': utc_now(), 'reason': args.reason}
    else:
        pins.pop(args.version, None)
    atomic_write_json(pins_path, pins, mode=0o600)
    print(json.dumps({'version': args.version, 'pinned': args.command == 'pin'}, ensure_ascii=False))
    return 0


def prune_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    versions_root = target / 'versions'
    pins = read_json(versions_root / 'pins.json', default={}) or {}
    manifests: list[tuple[str, dict[str, Any]]] = []
    if versions_root.exists():
        for path in versions_root.iterdir():
            if path.is_dir() and (path / 'manifest.json').exists():
                manifest = read_json(path / 'manifest.json')
                if isinstance(manifest, dict):
                    manifests.append((path.name, manifest))
    manifests.sort(key=lambda item: item[1].get('created_at', ''), reverse=True)
    protected = set(list(pins.keys()) + [meta.get('current_version')])
    removed: list[str] = []
    kept_unprotected = 0
    for version_id, manifest in manifests:
        if version_id in protected or manifest.get('status') == 'release':
            continue
        kept_unprotected += 1
        if kept_unprotected > args.keep:
            if not args.dry_run:
                shutil.rmtree(versions_root / version_id)
            removed.append(version_id)
    print(json.dumps({'dry_run': args.dry_run, 'removed': removed, 'protected': sorted(v for v in protected if v)}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Immutable snapshots, diffs, verified rollback, and retention.')
    sub = parser.add_subparsers(dest='command', required=True)

    snapshot = sub.add_parser('snapshot')
    snapshot.add_argument('target', type=Path)
    snapshot.add_argument('--reason', required=True)
    snapshot.add_argument('--status', choices=STATUSES, default='candidate')
    snapshot.add_argument('--include-sources', action='store_true')
    snapshot.set_defaults(func=snapshot_command)

    listing = sub.add_parser('list')
    listing.add_argument('target', type=Path)
    listing.set_defaults(func=list_command)

    verify = sub.add_parser('verify')
    verify.add_argument('target', type=Path)
    verify.add_argument('--version', required=True)
    verify.set_defaults(func=verify_command)

    diff = sub.add_parser('diff')
    diff.add_argument('target', type=Path)
    diff.add_argument('--from', dest='from_version', default='current')
    diff.add_argument('--to', dest='to_version', required=True)
    diff.add_argument('--include-sources', action='store_true')
    diff.set_defaults(func=diff_command)

    rollback = sub.add_parser('rollback')
    rollback.add_argument('target', type=Path)
    rollback.add_argument('--version', required=True)
    rollback.add_argument('--no-backup', action='store_true')
    rollback.set_defaults(func=rollback_command)

    for command in ('pin', 'unpin'):
        pin = sub.add_parser(command)
        pin.add_argument('target', type=Path)
        pin.add_argument('--version', required=True)
        pin.add_argument('--reason')
        pin.set_defaults(func=pin_command)

    prune = sub.add_parser('prune')
    prune.add_argument('target', type=Path)
    prune.add_argument('--keep', type=int, default=20, help='Keep this many newest unprotected snapshots.')
    prune.add_argument('--dry-run', action='store_true')
    prune.set_defaults(func=prune_command)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
