#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import compact_utc, remove_tree

SKILL_NAME = 'persona-distiller'


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(chunk)
    return digest.hexdigest()


def verify_tree(root: Path) -> dict[str, object]:
    checksum_file = root / 'checksums.sha256'
    if not checksum_file.is_file():
        return {'verified': False, 'mode': 'development-workspace', 'files': 0, 'errors': []}
    errors: list[str] = []
    checked = 0
    seen: set[str] = set()
    resolved_root = root.resolve()
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
        path = (root / rel).resolve()
        try:
            path.relative_to(resolved_root)
        except ValueError:
            errors.append(f'path escapes package: {rel}')
            continue
        if not path.is_file():
            errors.append(f'missing file: {rel}')
            continue
        if sha256_file(path) != checksum:
            errors.append(f'checksum mismatch: {rel}')
        checked += 1
    if checked == 0:
        errors.append('checksum manifest contains no payload files')
    return {'verified': not errors, 'mode': 'checksums.sha256', 'files': checked, 'errors': errors}


def destination(args: argparse.Namespace) -> Path:
    home = Path.home()
    project = Path(args.project_dir).expanduser().resolve()
    if args.target == 'path':
        if not args.path:
            raise ValueError('--path is required for --target path')
        return Path(args.path).expanduser().resolve()
    global_roots = {
        'codex': home / '.codex' / 'skills',
        'agents': home / '.agents' / 'skills',
        'claude': home / '.claude' / 'skills',
        'cursor': home / '.cursor' / 'skills',
        'openclaw': home / '.openclaw' / 'workspace' / 'skills',
    }
    project_roots = {
        'codex': project / '.codex' / 'skills',
        'agents': project / '.agents' / 'skills',
        'claude': project / '.claude' / 'skills',
        'cursor': project / '.cursor' / 'skills',
        'openclaw': project / '.openclaw' / 'workspace' / 'skills',
    }
    root = global_roots[args.target] if args.scope == 'global' else project_roots[args.target]
    return root / SKILL_NAME


def conflicting_source(args: argparse.Namespace) -> Path | None:
    if args.target not in {'codex', 'agents'}:
        return None
    home = Path.home()
    project = Path(args.project_dir).expanduser().resolve()
    base = home if args.scope == 'global' else project
    other_root = base / ('.agents' if args.target == 'codex' else '.codex') / 'skills'
    candidate = other_root / SKILL_NAME
    return candidate if candidate.exists() or candidate.is_symlink() else None


def copy_skill(source: Path, dest: Path) -> None:
    ignored = {'.git', '__pycache__', '.pytest_cache', 'workspaces', 'build', 'dist', '_build'}

    def ignore(_directory: str, names: list[str]) -> set[str]:
        return {name for name in names if name in ignored or name.endswith(('.zip', '.pyc', '.pyo'))}

    shutil.copytree(source, dest, ignore=ignore)
    for script in list((dest / 'scripts').glob('*.py')) + list((dest / 'scripts').glob('*.sh')) + [dest / 'install.py', dest / 'install.sh']:
        if script.is_file():
            script.chmod(script.stat().st_mode | 0o111)


def run_post_install_check(dest: Path) -> dict[str, object]:
    completed = subprocess.run(
        [sys.executable, str(dest / 'scripts' / 'self_check.py'), '--skip-tests'],
        cwd=dest, text=True, capture_output=True, timeout=120,
    )
    try:
        payload = json.loads(completed.stdout) if completed.stdout.strip() else {}
    except json.JSONDecodeError:
        payload = {'stdout': completed.stdout[-4000:]}
    return {'passed': completed.returncode == 0, 'payload': payload, 'stderr': completed.stderr[-4000:]}


def install(args: argparse.Namespace) -> int:
    source = Path(__file__).resolve().parents[1]
    source_verification = {'verified': False, 'mode': 'skipped', 'files': 0, 'errors': []} if args.skip_verify else verify_tree(source)
    if not source_verification.get('verified') and source_verification.get('mode') != 'development-workspace':
        raise ValueError('source package verification failed: ' + '; '.join(source_verification.get('errors', [])))
    dest = destination(args)
    conflict = conflicting_source(args)
    if conflict:
        raise ValueError(
            f'conflicting source exists: {conflict}; keep exactly one persona-distiller install '
            'and remove or migrate the other source before installing'
        )
    if source == dest or source in dest.parents:
        raise ValueError('refusing to install inside the source tree')
    backup = None
    if dest.exists() or dest.is_symlink():
        if not args.force:
            raise ValueError(f'destination exists: {dest}; pass --force to back it up and replace')
        backup = dest.with_name(f'{dest.name}.backup-{compact_utc()}')
        suffix = 1
        while backup.exists() or backup.is_symlink():
            backup = dest.with_name(f'{dest.name}.backup-{compact_utc()}-{suffix}')
            suffix += 1
        if args.dry_run:
            print(json.dumps({'action': 'install', 'destination': str(dest), 'backup': str(backup), 'dry_run': True, 'verification': source_verification}, indent=2))
            return 0
        dest.rename(backup)
    elif args.dry_run:
        print(json.dumps({'action': 'install', 'destination': str(dest), 'mode': 'symlink' if args.link else 'copy', 'dry_run': True, 'verification': source_verification}, indent=2))
        return 0
    dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        if args.link:
            dest.symlink_to(source, target_is_directory=True)
        else:
            copy_skill(source, dest)
        installed_verification = verify_tree(dest)
        if installed_verification.get('mode') == 'checksums.sha256' and not installed_verification.get('verified'):
            raise ValueError('installed copy checksum verification failed: ' + '; '.join(installed_verification.get('errors', [])))
        self_check = {'passed': True, 'skipped': True}
        if not args.skip_self_check:
            self_check = run_post_install_check(dest)
            if not self_check.get('passed'):
                raise ValueError(f'post-install self-check failed: {self_check}')
    except Exception:
        if dest.exists() or dest.is_symlink():
            remove_tree(dest)
        if backup and backup.exists():
            backup.rename(dest)
        raise
    print(json.dumps({
        'action': 'install', 'destination': str(dest), 'mode': 'symlink' if args.link else 'copy',
        'backup': str(backup) if backup else None,
        'version': (source / 'VERSION').read_text().strip(),
        'source_verification': source_verification,
        'installed_verification': installed_verification,
        'self_check': self_check,
    }, ensure_ascii=False, indent=2))
    return 0


def status(args: argparse.Namespace) -> int:
    dest = destination(args)
    conflict = conflicting_source(args)
    installed = dest.exists() or dest.is_symlink()
    valid_structure = installed and (dest / 'SKILL.md').is_file() and (dest / 'agents' / 'openai.yaml').is_file()
    version = (dest / 'VERSION').read_text().strip() if (dest / 'VERSION').is_file() else None
    verification = verify_tree(dest) if installed else {'verified': False, 'mode': 'not-installed', 'files': 0, 'errors': []}
    valid = bool(
        valid_structure
        and not conflict
        and (verification.get('verified') or verification.get('mode') == 'development-workspace')
    )
    print(json.dumps({
        'destination': str(dest),
        'installed': installed,
        'valid': valid,
        'version': version,
        'symlink': dest.is_symlink(),
        'conflicting_source': str(conflict) if conflict else None,
        'verification': verification,
    }, ensure_ascii=False, indent=2))
    return 0 if valid else 1


def uninstall(args: argparse.Namespace) -> int:
    dest = destination(args)
    if not (dest.exists() or dest.is_symlink()):
        print(json.dumps({'action': 'uninstall', 'status': 'not-installed', 'destination': str(dest)}, indent=2))
        return 0
    if not args.force:
        raise ValueError('--force is required to uninstall')
    backup = None if args.no_backup else dest.with_name(f'{dest.name}.uninstall-backup-{compact_utc()}')
    if args.dry_run:
        print(json.dumps({'action': 'uninstall', 'destination': str(dest), 'backup': str(backup) if backup else None, 'dry_run': True}, indent=2))
        return 0
    if backup:
        dest.rename(backup)
    else:
        remove_tree(dest)
    print(json.dumps({'action': 'uninstall', 'destination': str(dest), 'backup': str(backup) if backup else None}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Install Persona Distiller into an Agent Skills host.')
    sub = parser.add_subparsers(dest='command')
    for name, func in [('install', install), ('status', status), ('uninstall', uninstall)]:
        child = sub.add_parser(name)
        child.add_argument('--target', choices=['codex', 'agents', 'claude', 'cursor', 'openclaw', 'path'], default='codex')
        child.add_argument('--scope', choices=['global', 'project'], default='global')
        child.add_argument('--project-dir', default='.')
        child.add_argument('--path')
        child.add_argument('--dry-run', action='store_true')
        if name == 'install':
            child.add_argument('--link', action='store_true')
            child.add_argument('--force', action='store_true')
            child.add_argument('--skip-verify', action='store_true', help='Emergency-only: skip source checksum verification.')
            child.add_argument('--skip-self-check', action='store_true')
        if name == 'uninstall':
            child.add_argument('--force', action='store_true')
            child.add_argument('--no-backup', action='store_true')
        child.set_defaults(func=func)
    args = parser.parse_args()
    if not args.command:
        args = parser.parse_args(['install'])
    try:
        return args.func(args)
    except (ValueError, OSError, subprocess.SubprocessError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
