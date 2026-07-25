#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import append_jsonl, atomic_write_text, ensure_target, make_id, read_jsonl, target_lock, utc_now

SCOPES = ('facts', 'persona', 'work', 'boundary', 'hypothesis', 'evaluation')
STATUSES = ('active', 'pending', 'rejected', 'resolved', 'superseded')
DEFAULT_SUITES = {
    'facts': ['known', 'fact-preservation'],
    'persona': ['known', 'boundary', 'voice', 'contrast', 'trajectory'],
    'work': ['known', 'contrast', 'trajectory'],
    'boundary': ['boundary', 'fact-preservation'],
    'hypothesis': ['boundary'],
    'evaluation': ['known', 'boundary', 'voice', 'trajectory', 'contrast', 'fact-preservation', 'style-decoy'],
}


def materialize(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    state: dict[str, dict[str, Any]] = {}
    for event in events:
        correction_id = event.get('correction_id')
        if not correction_id:
            continue
        if event.get('event_type') == 'create':
            state[correction_id] = dict(event)
        elif correction_id in state:
            current = state[correction_id]
            if event.get('event_type') in {'status', 'supersede'}:
                current['status'] = event.get('status', current.get('status'))
                current['last_event_id'] = event.get('event_id')
                current['updated_at'] = event.get('timestamp')
                if event.get('rationale'):
                    current['resolution_rationale'] = event.get('rationale')
        if event.get('supersedes') and event.get('status') == 'active':
            prior_id = event['supersedes']
            if prior_id in state:
                state[prior_id]['status'] = 'superseded'
                state[prior_id]['superseded_by'] = correction_id
    return state


def compile_active(target: Path) -> dict[str, Any]:
    events = read_jsonl(target / 'corrections' / 'corrections.jsonl')
    states = materialize(events)
    active = sorted(
        (value for value in states.values() if value.get('status') == 'active'),
        key=lambda item: (item.get('scope', ''), item.get('timestamp', ''), item.get('correction_id', '')),
    )
    lines = [
        '# Active corrections',
        '',
        'Generated from the append-only correction event log. These corrections override lower-confidence patterns but not law, safety, objective facts, or explicit boundaries without evidence.',
        '',
    ]
    if not active:
        lines.append('No active corrections.')
    else:
        for item in active:
            text = ' '.join(str(item.get('text', '')).split())
            lines.extend([
                f'## {item.get("correction_id")} - {item.get("scope")}',
                '',
                f'- Correction: {text}',
                f'- Claim IDs: {", ".join(item.get("claim_ids", [])) or "none"}',
                f'- Source IDs: {", ".join(item.get("source_ids", [])) or "none"}',
                f'- Impacted suites: {", ".join(item.get("impacted_suites", [])) or "none"}',
                f'- Added: {item.get("timestamp")}',
                '',
            ])
    atomic_write_text(target / 'corrections' / 'ACTIVE.md', '\n'.join(lines).rstrip() + '\n', mode=0o600)
    return {'events': len(events), 'active': len(active), 'states': states}


def add_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    meta = ensure_target(target)
    sources = {record.get('source_id') for record in read_jsonl(target / 'evidence' / 'source-ledger.jsonl')}
    claims = {record.get('claim_id') for record in read_jsonl(target / 'evidence' / 'claims.jsonl')}
    missing_sources = set(args.source) - sources
    missing_claims = set(args.claim_id) - claims
    if missing_sources:
        raise ValueError(f'unknown source IDs: {sorted(missing_sources)}')
    if missing_claims:
        raise ValueError(f'unknown Claim IDs: {sorted(missing_claims)}')
    if args.scope == 'facts' and args.status == 'active' and meta.get('subject_origin') in {'public', 'historical'} and not args.source:
        raise ValueError('active factual correction for a public/historical subject requires supporting source IDs; use pending otherwise')

    correction_id = make_id('cor')
    event = {
        'event_id': make_id('evt'),
        'correction_id': correction_id,
        'event_type': 'create',
        'timestamp': utc_now(),
        'text': args.text,
        'scope': args.scope,
        'status': args.status,
        'source_ids': list(dict.fromkeys(args.source)),
        'claim_ids': list(dict.fromkeys(args.claim_id)),
        'rationale': args.rationale,
        'supersedes': args.supersedes,
        'impacted_suites': list(dict.fromkeys(args.impact_suite or DEFAULT_SUITES[args.scope])),
    }
    with target_lock(target):
        append_jsonl(target / 'corrections' / 'corrections.jsonl', event)
        projection = compile_active(target)
    print(json.dumps({'event': event, 'projection': {'active': projection['active']}}, ensure_ascii=False, indent=2))
    return 0


def status_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    events = read_jsonl(target / 'corrections' / 'corrections.jsonl')
    states = materialize(events)
    if args.correction_id not in states:
        raise ValueError(f'unknown correction_id: {args.correction_id}')
    event = {
        'event_id': make_id('evt'),
        'correction_id': args.correction_id,
        'event_type': 'status',
        'timestamp': utc_now(),
        'text': None,
        'scope': states[args.correction_id].get('scope'),
        'status': args.status,
        'source_ids': [],
        'claim_ids': [],
        'rationale': args.rationale,
        'supersedes': None,
        'impacted_suites': states[args.correction_id].get('impacted_suites', []),
    }
    with target_lock(target):
        append_jsonl(target / 'corrections' / 'corrections.jsonl', event)
        projection = compile_active(target)
    print(json.dumps({'event': event, 'projection': {'active': projection['active']}}, ensure_ascii=False, indent=2))
    return 0


def list_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    events = read_jsonl(target / 'corrections' / 'corrections.jsonl')
    states = materialize(events)
    print(json.dumps({'events': len(events), 'corrections': list(states.values())}, ensure_ascii=False, indent=2))
    return 0


def compile_command(args: argparse.Namespace) -> int:
    target = args.target.expanduser().resolve()
    ensure_target(target)
    result = compile_active(target)
    print(json.dumps({'events': result['events'], 'active': result['active']}, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description='Append, resolve, and compile Persona Distiller corrections.')
    sub = parser.add_subparsers(dest='command', required=True)

    add = sub.add_parser('add')
    add.add_argument('target', type=Path)
    add.add_argument('--text', required=True)
    add.add_argument('--scope', choices=SCOPES, required=True)
    add.add_argument('--status', choices=STATUSES, default='active')
    add.add_argument('--source', action='append', default=[])
    add.add_argument('--claim-id', action='append', default=[])
    add.add_argument('--rationale')
    add.add_argument('--supersedes')
    add.add_argument('--impact-suite', action='append', default=[])
    add.set_defaults(func=add_command)

    status = sub.add_parser('status')
    status.add_argument('target', type=Path)
    status.add_argument('--correction-id', required=True)
    status.add_argument('--status', choices=STATUSES, required=True)
    status.add_argument('--rationale')
    status.set_defaults(func=status_command)

    listing = sub.add_parser('list')
    listing.add_argument('target', type=Path)
    listing.set_defaults(func=list_command)

    compile_parser = sub.add_parser('compile')
    compile_parser.add_argument('target', type=Path)
    compile_parser.set_defaults(func=compile_command)

    args = parser.parse_args()
    try:
        return args.func(args)
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
