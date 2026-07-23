#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, ensure_dir, ensure_target, parse_frontmatter, read_jsonl, scan_secrets, sha256_file, utc_now
from persona_registry import default_registry_root, next_product_version_for

CORE_FILES = [
    'SKILL.md', 'README.md', 'install.py', 'install.sh', 'install.ps1', 'meta.json', 'identity-catalog.json', 'route-manifest.json',
    'facts.md', 'cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md', 'work.md', 'persona.md',
    'boundaries.md', 'hypotheses.md', 'divergence-map.md', 'corrections/ACTIVE.md',
]
CORE_DIRS = ['agents', 'identity-facets', 'scenario-adapters', 'scripts']


def copy_file(src: Path, dst: Path) -> None:
    ensure_dir(dst.parent)
    shutil.copy2(src, dst)


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    ensure_dir(path.parent)
    with path.open('w', encoding='utf-8') as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + '\n')
    os.chmod(path, 0o600)


def package_timestamp(meta: dict[str, Any]) -> str:
    # Rebuilding an unchanged target must produce byte-identical packages.
    return str(meta.get('updated_at') or meta.get('created_at') or '2026-07-23T00:00:00Z')


def sanitized_meta(meta: dict[str, Any], product_version: str) -> dict[str, Any]:
    clean = dict(meta)
    for key in ['consent_authority', 'retention_policy', 'last_rollback']:
        clean.pop(key, None)
    clean['product_version'] = product_version
    clean['runtime_invocation_versioning'] = False
    clean['packaged_at'] = package_timestamp(meta)
    clean['package_mode'] = 'runtime'
    return clean


def sanitized_sources(target: Path) -> list[dict[str, Any]]:
    private = (target / 'meta.json').is_file() and json.loads((target / 'meta.json').read_text()).get('subject_origin') in {'private', 'self'}
    result = []
    for record in read_jsonl(target / 'evidence' / 'source-ledger.jsonl'):
        clean = dict(record)
        for key in ['local_path', 'normalized_path', 'redactions', 'original_name', 'abstract', 'locator']:
            clean.pop(key, None)
        if private:
            clean['url'] = None
        result.append(clean)
    return result


def deterministic_zip(staging: Path, output: Path) -> None:
    ensure_dir(output.parent)
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(p for p in staging.rglob('*') if p.is_file()):
            rel = path.relative_to(staging.parent).as_posix()
            info = zipfile.ZipInfo(rel, date_time=(2026, 7, 23, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix in {'.py', '.sh'} or path.name == 'install.py' else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(description='Build one clean installable target-person Skill ZIP.')
    parser.add_argument('target', type=Path)
    parser.add_argument('--output', type=Path, default=Path('./dist'))
    parser.add_argument('--registry-root', type=Path, default=default_registry_root())
    parser.add_argument('--product-version', help='Optional assertion; must equal the registry-derived next product version.')
    parser.add_argument('--skip-quality', action='store_true')
    parser.add_argument('--include-audit-summary', action='store_true')
    parser.add_argument('--allow-secret-pattern', action='store_true')
    args = parser.parse_args()
    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    fm, _ = parse_frontmatter(target / 'SKILL.md')
    if set(fm) != {'name', 'description'}:
        parser.error('target SKILL.md frontmatter must contain only name and description')
    if fm['name'] != target.name:
        parser.error('target SKILL.md name must match directory')
    if meta.get('status', '').startswith('blocked'):
        parser.error(f'target status blocks release: {meta.get("status")}')
    if not args.skip_quality:
        result = subprocess.run([sys.executable, str(Path(__file__).resolve().parent / 'quality_check.py'), str(target), '--phase', 'release', '--strict'], text=True, capture_output=True)
        if result.returncode != 0:
            print(result.stdout, file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            parser.error('strict release quality gate failed')
    product_version = next_product_version_for(
        str(meta.get('name', '')),
        str(meta.get('subject_origin', '')),
        args.registry_root,
    )
    if args.product_version and args.product_version != product_version:
        parser.error(
            f'--product-version {args.product_version} is not the next available version '
            f'for this person; expected {product_version}'
        )
    with tempfile.TemporaryDirectory(prefix='persona-target-package-') as tmp:
        staging_parent = Path(tmp)
        staging = staging_parent / target.name
        staging.mkdir()
        for rel in CORE_FILES:
            if (target / rel).is_file():
                copy_file(target / rel, staging / rel)
        for rel in CORE_DIRS:
            if (target / rel).is_dir():
                shutil.copytree(target / rel, staging / rel, dirs_exist_ok=True, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
        atomic_write_json(staging / 'meta.json', sanitized_meta(meta, product_version), mode=0o600)
        write_jsonl(staging / 'evidence' / 'claims.jsonl', read_jsonl(target / 'evidence' / 'claims.jsonl'))
        write_jsonl(staging / 'evidence' / 'source-ledger.jsonl', sanitized_sources(target))
        write_jsonl(staging / 'corrections' / 'corrections.jsonl', [])
        write_jsonl(staging / 'memory' / 'episodic.jsonl', [])
        for rel in ['memory/user-overlay.md', 'memory/procedural.md', 'memory/promotion-queue.md']:
            if (target / rel).is_file():
                copy_file(target / rel, staging / rel)
        write_jsonl(staging / 'runtime' / 'invocations.jsonl', [])
        if args.include_audit_summary:
            for rel in ['reports/quality-release.json', 'research/coverage-map.json', 'research/saturation-report.md']:
                if (target / rel).is_file():
                    copy_file(target / rel, staging / 'audit' / Path(rel).name)
        findings = scan_secrets(staging, exclude_dirs={'.git', '__pycache__'})
        if findings and not args.allow_secret_pattern:
            print(json.dumps({'secret_findings': findings}, ensure_ascii=False, indent=2), file=sys.stderr)
            parser.error('secret-like patterns detected')
        # Checksums cover all payload files except the checksum file and package manifest.
        records = []
        for path in sorted(p for p in staging.rglob('*') if p.is_file()):
            if path.name in {'checksums.sha256', 'PACKAGE_MANIFEST.json'}:
                continue
            records.append({'path': path.relative_to(staging).as_posix(), 'sha256': sha256_file(path), 'size': path.stat().st_size})
        checksums = ''.join(f"{item['sha256']}  {item['path']}\n" for item in records)
        (staging / 'checksums.sha256').write_text(checksums, encoding='utf-8')
        manifest = {
            'schema_version': '2.0', 'name': target.name, 'target_name': meta.get('name'),
            'builder': 'persona-distiller', 'builder_version': 'v0.0.0.4',
            'product_version': product_version, 'model_version': meta.get('model_version'),
            'created_at': package_timestamp(meta), 'top_level_count': 1,
            'privacy': {'raw_included': False, 'holdout_included': False, 'private_source_bodies_included': False, 'runtime_history_reset': True},
            'files': records,
        }
        atomic_write_json(staging / 'PACKAGE_MANIFEST.json', manifest)
        output = args.output.expanduser().resolve()
        if output.suffix.lower() != '.zip':
            output.mkdir(parents=True, exist_ok=True)
            output = output / f'{target.name}-persona-skill-v{product_version}.zip'
        deterministic_zip(staging, output)
        checksum = sha256_file(output)
        Path(str(output) + '.sha256').write_text(f'{checksum}  {output.name}\n', encoding='utf-8')
    print(json.dumps({
        'package': str(output),
        'sha256': checksum,
        'top_level': target.name,
        'product_version': product_version,
        'product_version_consumed': False,
        'runtime_records_reset': True,
        'runtime_invocation_versioning': False,
        'registration_required': True,
        'register_command': f'python3 scripts/register_persona.py {output}',
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
