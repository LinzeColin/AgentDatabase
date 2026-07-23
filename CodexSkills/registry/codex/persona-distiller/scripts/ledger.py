#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import LANES, append_jsonl, ensure_target, make_id, read_jsonl, sha256_bytes, target_lock, utc_now

CLAIM_CATEGORIES = (
    'fact', 'mental-model', 'heuristic', 'value', 'epistemic', 'expression', 'lineage',
    'blind-spot', 'contradiction', 'work-method', 'boundary', 'soul-hypothesis',
)
CLAIM_STATUSES = ('fact', 'pattern', 'hypothesis', 'unknown', 'superseded')


def source_add_url(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    ledger = target / 'evidence' / 'source-ledger.jsonl'
    existing = read_jsonl(ledger)
    locator_checksum = args.content_checksum or sha256_bytes(('URL:' + args.url).encode('utf-8'))
    if len(locator_checksum) != 64 or any(c not in '0123456789abcdefABCDEF' for c in locator_checksum):
        raise ValueError('--content-checksum must be a 64-character SHA-256 hex digest')
    locator_checksum = locator_checksum.lower()
    source_id = f'src-{locator_checksum[:12]}'
    for record in existing:
        if record.get('source_id') == source_id or record.get('url') == args.url:
            print(json.dumps({'status': 'duplicate-skipped', 'source_id': record.get('source_id')}, ensure_ascii=False))
            return 0
    record = {
        'source_id': source_id,
        'title': args.title,
        'author': args.author,
        'published_at': args.published_at,
        'accessed_at': utc_now(),
        'url': args.url,
        'local_path': None,
        'normalized_path': None,
        'source_type': args.source_type,
        'tier': args.tier,
        'rights': args.rights,
        'language': args.language,
        'split': 'holdout' if args.holdout else 'train',
        'checksum': locator_checksum,
        'checksum_basis': 'content' if args.content_checksum else 'url-locator-only',
        'normalized_checksum': None,
        'dimensions': list(dict.fromkeys(args.dimension)),
        'derived_from': list(dict.fromkeys(args.derived_from)),
        'extraction_status': 'needs_agent_read',
        'abstract': args.abstract,
        'locator': args.locator,
        'created_at': utc_now(),
    }
    with target_lock(target):
        append_jsonl(ledger, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def claim_add(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    source_records = read_jsonl(target / 'evidence' / 'source-ledger.jsonl')
    sources = {record.get('source_id'): record for record in source_records}
    for source_id in args.source + args.counter_source:
        if source_id not in sources:
            raise ValueError(f'unknown source_id: {source_id}')
    leaked = [source_id for source_id in args.source if sources[source_id].get('split') == 'holdout']
    if leaked:
        raise ValueError(f'Holdout sources cannot support Claims: {", ".join(leaked)}')
    if args.status in {'fact', 'pattern', 'hypothesis'} and not args.source:
        raise ValueError(f'{args.status} Claim requires at least one supporting source')
    if args.category == 'soul-hypothesis' and args.status != 'hypothesis':
        raise ValueError('soul-hypothesis category must use hypothesis status')
    if args.confidence < 0 or args.confidence > 1:
        raise ValueError('confidence must be between 0 and 1')

    claim_id = make_id('clm')
    record = {
        'claim_id': claim_id,
        'claim': args.claim,
        'category': args.category,
        'status': args.status,
        'source_ids': list(dict.fromkeys(args.source)),
        'counter_source_ids': list(dict.fromkeys(args.counter_source)),
        'contexts': list(dict.fromkeys(args.context)),
        'evidence_clusters': list(dict.fromkeys(args.cluster or args.source)),
        'confidence': args.confidence,
        'time_scope': args.time_scope,
        'applicability': args.applicability,
        'falsifiers': list(dict.fromkeys(args.falsifier)),
        'alternative_explanations': list(dict.fromkeys(args.alternative)),
        'supersedes': args.supersedes,
        'author_role': args.author_role,
        'created_at': utc_now(),
        'updated_at': utc_now(),
    }
    with target_lock(target):
        append_jsonl(target / 'evidence' / 'claims.jsonl', record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


def list_records(path: Path, kind: str) -> int:
    records = read_jsonl(path)
    print(json.dumps({'kind': kind, 'count': len(records), 'records': records}, ensure_ascii=False, indent=2))
    return 0


def validate_target(target: Path) -> tuple[list[str], list[str], dict[str, int]]:
    ensure_target(target)
    errors: list[str] = []
    warnings: list[str] = []
    sources = read_jsonl(target / 'evidence' / 'source-ledger.jsonl')
    claims = read_jsonl(target / 'evidence' / 'claims.jsonl')
    source_ids: set[str] = set()
    checksums: dict[str, dict] = {}
    for index, record in enumerate(sources, 1):
        source_id = record.get('source_id')
        if not source_id:
            errors.append(f'source record {index} missing source_id')
            continue
        if source_id in source_ids:
            errors.append(f'duplicate source_id: {source_id}')
        source_ids.add(source_id)
        checksum = record.get('checksum')
        if checksum in checksums and checksums[checksum].get('split') != record.get('split'):
            errors.append(f'checksum appears in both train and Holdout: {checksum}')
        if checksum:
            checksums[checksum] = record
        if record.get('tier') not in {'P1', 'P2', 'S1', 'S2', 'U'}:
            errors.append(f'{source_id} has invalid tier')
        if record.get('split') not in {'train', 'holdout'}:
            errors.append(f'{source_id} has invalid split')
        unknown_lanes = set(record.get('dimensions', [])) - set(LANES)
        if unknown_lanes:
            errors.append(f'{source_id} has unknown dimensions: {sorted(unknown_lanes)}')
        if record.get('checksum_basis') == 'url-locator-only':
            warnings.append(f'{source_id} checksum is locator-only; capture content hash before release')

    source_map = {record.get('source_id'): record for record in sources}
    claim_ids: set[str] = set()
    for index, record in enumerate(claims, 1):
        claim_id = record.get('claim_id')
        if not claim_id:
            errors.append(f'claim record {index} missing claim_id')
            continue
        if claim_id in claim_ids:
            errors.append(f'duplicate claim_id: {claim_id}')
        claim_ids.add(claim_id)
        if record.get('status') not in CLAIM_STATUSES:
            errors.append(f'{claim_id} has invalid status')
        if record.get('category') not in CLAIM_CATEGORIES:
            errors.append(f'{claim_id} has invalid category')
        confidence = record.get('confidence')
        if not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
            errors.append(f'{claim_id} confidence must be 0..1')
        for source_id in record.get('source_ids', []) + record.get('counter_source_ids', []):
            if source_id not in source_map:
                errors.append(f'{claim_id} references missing source {source_id}')
        for source_id in record.get('source_ids', []):
            if source_map.get(source_id, {}).get('split') == 'holdout':
                errors.append(f'{claim_id} leaks Holdout source {source_id}')
        if record.get('status') in {'fact', 'pattern', 'hypothesis'} and not record.get('source_ids'):
            errors.append(f'{claim_id} active conclusion has no support')
        if record.get('category') == 'soul-hypothesis':
            if record.get('status') != 'hypothesis':
                errors.append(f'{claim_id} soul-hypothesis must be hypothesis')
            if not record.get('alternative_explanations'):
                errors.append(f'{claim_id} soul-hypothesis lacks alternative explanations')
            if not record.get('falsifiers'):
                errors.append(f'{claim_id} soul-hypothesis lacks falsifiers')
        supersedes = record.get('supersedes')
        if supersedes and supersedes not in claim_ids:
            # It may refer to a later line, so defer with a warning and final check below.
            warnings.append(f'{claim_id} supersedes unresolved Claim {supersedes}')
    for record in claims:
        supersedes = record.get('supersedes')
        if supersedes and supersedes not in claim_ids:
            errors.append(f'{record.get("claim_id")} supersedes missing Claim {supersedes}')

    return errors, sorted(set(warnings)), {'sources': len(sources), 'claims': len(claims)}


def validate_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    errors, warnings, counts = validate_target(target)
    result = {'ok': not errors, 'counts': counts, 'errors': errors, 'warnings': warnings}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if errors or (args.strict and warnings) else 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage Persona Distiller source and Claim ledgers.')
    sub = parser.add_subparsers(dest='command', required=True)

    source_url = sub.add_parser('source-add-url', help='Register a remote source without downloading it.')
    source_url.add_argument('target', type=Path)
    source_url.add_argument('--title', required=True)
    source_url.add_argument('--url', required=True)
    source_url.add_argument('--content-checksum')
    source_url.add_argument('--source-type', default='web')
    source_url.add_argument('--tier', choices=['P1', 'P2', 'S1', 'S2', 'U'], default='U')
    source_url.add_argument('--rights', default='publicly-accessible-for-analysis; redistribution-not-assumed')
    source_url.add_argument('--author')
    source_url.add_argument('--published-at')
    source_url.add_argument('--language')
    source_url.add_argument('--dimension', action='append', choices=LANES, default=[])
    source_url.add_argument('--derived-from', action='append', default=[])
    source_url.add_argument('--holdout', action='store_true')
    source_url.add_argument('--abstract')
    source_url.add_argument('--locator')
    source_url.set_defaults(func=source_add_url)

    claim = sub.add_parser('claim-add', help='Append an atomic Claim.')
    claim.add_argument('target', type=Path)
    claim.add_argument('--claim', required=True)
    claim.add_argument('--category', choices=CLAIM_CATEGORIES, required=True)
    claim.add_argument('--status', choices=CLAIM_STATUSES, required=True)
    claim.add_argument('--source', action='append', default=[])
    claim.add_argument('--counter-source', action='append', default=[])
    claim.add_argument('--context', action='append', default=[])
    claim.add_argument('--cluster', action='append', default=[])
    claim.add_argument('--confidence', type=float, default=0.5)
    claim.add_argument('--time-scope')
    claim.add_argument('--applicability')
    claim.add_argument('--falsifier', action='append', default=[])
    claim.add_argument('--alternative', action='append', default=[])
    claim.add_argument('--supersedes')
    claim.add_argument('--author-role', default='agent')
    claim.set_defaults(func=claim_add)

    source_list = sub.add_parser('source-list')
    source_list.add_argument('target', type=Path)
    source_list.set_defaults(func=lambda a: list_records(a.target / 'evidence/source-ledger.jsonl', 'sources'))

    claim_list = sub.add_parser('claim-list')
    claim_list.add_argument('target', type=Path)
    claim_list.set_defaults(func=lambda a: list_records(a.target / 'evidence/claims.jsonl', 'claims'))

    validate = sub.add_parser('validate')
    validate.add_argument('target', type=Path)
    validate.add_argument('--strict', action='store_true')
    validate.set_defaults(func=validate_command)
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, OSError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
