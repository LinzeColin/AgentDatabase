#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, utc_now
from identity import load_registry, parse_identity_spec


def build_route(name: str, identity_spec: str, scenario: str | None = None, subject_origin: str = 'auto') -> dict[str, Any]:
    registry = load_registry()
    selection = parse_identity_spec(identity_spec, registry)
    by_id = {f['id']: f for f in registry['families']}
    primary = by_id[selection['primary']]
    depth: dict[str, str] = {}
    readiness: dict[str, str] = {}
    for family in registry['families'][:6]:
        weight = selection['weights'].get(family['id'], 0.0)
        if weight > 0:
            depth[family['id']] = 'deep'
            readiness[family['id']] = 'building'
        elif family['id'] == selection['primary']:
            depth[family['id']] = 'deep'
            readiness[family['id']] = 'building'
        else:
            depth[family['id']] = 'screening'
            readiness[family['id']] = 'provisional-until-evidenced'
    source_priorities: list[str] = []
    for identity_id, weight in sorted(selection['weights'].items(), key=lambda item: item[1], reverse=True):
        for source in by_id[identity_id].get('source_priorities', []):
            if source not in source_priorities:
                source_priorities.append(source)
    if not source_priorities:
        source_priorities = list(primary.get('source_priorities', []))
    scenario_priors: list[str] = []
    for identity_id in selection['weights']:
        for item in by_id[identity_id].get('scenario_priors', []):
            if item not in scenario_priors:
                scenario_priors.append(item)
    return {
        'schema_version': '1.0',
        'target_name': name,
        'generated_at': utc_now(),
        'identity_selection': selection,
        'subject_origin': subject_origin,
        'provided_scenario': scenario,
        'scenario_policy': 'user-provided-primary' if scenario else 'infer-per-task',
        'build_depth': depth,
        'runtime_readiness': readiness,
        'runtime_identity_gate': {
            'required_each_substantive_invocation': True,
            'selection_may_be_in_same_request': True,
            'reuse_requires_explicit_phrase': '沿用上次身份',
            'aborted_gate_consumes_version': False,
        },
        'research': {
            'base_lanes': ['writings', 'conversations', 'expression', 'external', 'decisions', 'timeline'],
            'primary_identity_focus': primary['research_focus'],
            'source_priorities': source_priorities,
            'scenario_priors': scenario_priors,
            'completeness_method': ['source-universe', 'coverage-cube', 'origin-clustering', 'gap-expansion', 'two-round-saturation'],
        },
        'runtime_model_load_order': [
            'boundaries.md', 'corrections/ACTIVE.md', 'facts.md', 'identity-facets/<selection>.md',
            'cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md',
            'work.md', 'persona.md', 'scenario-adapters/<inferred>.md', 'divergence-map.md'
        ],
        'runtime_versioning': {
            'format': '0.0.0.N',
            'allocate_after_identity_selection': True,
            'failed_runs_consume_serial': True,
            'serial_reuse_forbidden': True,
            'override_requires_explicit_user_instruction': True,
        },
    }


def source_universe(route: dict[str, Any]) -> dict[str, Any]:
    return {
        'schema_version': '1.0',
        'target_name': route['target_name'],
        'generated_at': route['generated_at'],
        'families': [
            {'id': 'first-party-systematic', 'examples': ['books', 'papers', 'official essays', 'courses', 'code', 'patents', 'formal documents'], 'priority': 'highest'},
            {'id': 'dialogue-pressure', 'examples': ['long interviews', 'debates', 'hearings', 'Q&A', 'press conferences', 'conflict records'], 'priority': 'high'},
            {'id': 'decisions-actions-outcomes', 'examples': ['investments', 'products', 'votes', 'judgments', 'experiments', 'matches', 'failures', 'exits'], 'priority': 'highest'},
            {'id': 'external-triangulation', 'examples': ['colleagues', 'partners', 'competitors', 'biographies', 'criticism', 'peer review'], 'priority': 'high'},
            {'id': 'context-constraints', 'examples': ['information available at the time', 'resources', 'incentives', 'organization', 'market', 'law'], 'priority': 'high'},
            {'id': 'multimodal', 'examples': ['audio', 'video', 'images', 'design drafts', 'code', 'game data', 'manuscripts'], 'priority': 'medium'},
            {'id': 'authorized-private', 'examples': ['local mail exports', 'chat exports', 'meeting notes', 'user corrections'], 'priority': 'conditional'},
        ],
        'identity_priorities': route['research']['source_priorities'],
        'coverage_axes': ['identity', 'role', 'period', 'research-lane', 'source-family', 'language', 'decision-context', 'success/failure', 'public/private'],
        'stop_rule': 'Stop only after two consecutive gap-driven rounds add no high-impact Claim and all critical coverage cells are either evidenced or explicitly unresolved.',
        'non_claim': 'This protocol targets evidence saturation, not a logically impossible guarantee that every public or private source has been found.'
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Generate adaptive build and runtime route plans.')
    parser.add_argument('--name', required=True)
    parser.add_argument('--identity', required=True)
    parser.add_argument('--scenario')
    parser.add_argument('--subject-origin', default='auto')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    try:
        route = build_route(args.name, args.identity, args.scenario, args.subject_origin)
        payload = {'route': route, 'source_universe': source_universe(route)}
        if args.output:
            args.output.mkdir(parents=True, exist_ok=True)
            atomic_write_json(args.output / 'route-plan.json', route)
            atomic_write_json(args.output / 'source-universe.json', payload['source_universe'])
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
