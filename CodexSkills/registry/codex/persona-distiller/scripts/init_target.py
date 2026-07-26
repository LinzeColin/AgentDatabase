#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import atomic_write_json, atomic_write_text, ensure_dir, make_id, read_json, slugify, utc_now, valid_skill_name
from identity import load_registry, parse_identity_spec
from namesake_gate import normalize_name
from persona_registry import category_for_identity, subject_uid
from route_engine import build_route, source_universe


def render(text: str, values: dict[str, str]) -> str:
    for key, value in values.items():
        text = text.replace('{{' + key + '}}', value)
    return text


def load_namesake_gate(path: Path, target_name: str) -> dict[str, object]:
    gate = read_json(path.expanduser().resolve())
    if not isinstance(gate, dict) or gate.get('schema_version') != '1.0':
        raise ValueError('namesake gate must be a schema 1.0 object')
    if gate.get('normalized_name') != normalize_name(target_name):
        raise ValueError('namesake gate target name does not match --name')
    candidates = gate.get('candidates')
    count = gate.get('candidate_count')
    if not isinstance(candidates, list) or count != len(candidates):
        raise ValueError('namesake gate candidate_count does not match candidates')
    if gate.get('status') == 'blocked' or gate.get('resolution') == 'multiple' or count > 1:
        raise ValueError('BLOCKED_NAMESAKE_SELECTION: choose one candidate before initialization')
    if gate.get('status') != 'ready' or gate.get('resolution') not in {'none', 'single'}:
        raise ValueError('namesake gate is not ready')
    if count == 1 and gate.get('selected_subject_uid') != candidates[0].get('subject_uid'):
        raise ValueError('namesake gate selected_subject_uid does not match its candidate')
    cards = gate.get('candidate_cards')
    if not isinstance(cards, list) or len(cards) != count:
        raise ValueError('namesake gate candidate_cards does not match candidates')
    return gate


def main() -> int:
    parser = argparse.ArgumentParser(description='Create a target-person executable Agent Skill workspace.')
    parser.add_argument('--name', required=True, help='Target person name.')
    parser.add_argument('--identity', required=True, help='single primary identity, 1-12 or name, e.g. 1 or 材料建工师.')
    parser.add_argument('--namesake-gate', required=True, type=Path, help='Ready schema-1 namesake gate produced before initialization.')
    parser.add_argument('--scenario', help='Optional primary scenario. Runtime still routes other scenarios.')
    parser.add_argument('--slug')
    parser.add_argument('--workspace', default='./workspaces')
    parser.add_argument('--profile', choices=['quick', 'standard', 'deep'], default='deep')
    parser.add_argument('--subject-origin', choices=['auto', 'public', 'private', 'self', 'fictional', 'historical'], default='auto')
    parser.add_argument('--consent-authority')
    parser.add_argument('--retention-policy')
    parser.add_argument('--language', default='zh-CN')
    parser.add_argument('--time-scope', default='all available periods, separated by role and material drift')
    parser.add_argument('--enable-existential-hypotheses', action='store_true')
    parser.add_argument('--force', action='store_true')
    args = parser.parse_args()

    try:
        # This is intentionally before identity parsing, workspace creation, or --force deletion.
        namesake_gate = load_namesake_gate(args.namesake_gate, args.name)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))

    try:
        selection = parse_identity_spec(args.identity)
    except (ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))
    slug = args.slug or slugify(args.name)
    if not valid_skill_name(slug):
        parser.error('slug must be lowercase ASCII letters/numbers/hyphens and <=64 chars')
    workspace = Path(args.workspace).expanduser().resolve()
    target = workspace / slug
    if target.exists():
        if not args.force:
            parser.error(f'target exists: {target}')
        if any(target.iterdir()) and not (target / 'meta.json').is_file():
            parser.error('--force refused: existing directory is not a generated target')
        shutil.rmtree(target)

    origin = args.subject_origin
    origin_review_required = origin == 'auto'
    effective_origin = 'public' if origin == 'auto' else origin
    # 多重身份已移除：所有 origin 都使用单一主身份。private/self 仍需 consent 授权。
    status = 'blocked-consent' if effective_origin in {'private', 'self'} and not args.consent_authority else 'draft'
    now = utc_now()
    target_id = make_id('tgt')
    route = build_route(args.name, args.identity, args.scenario, effective_origin)
    universe = source_universe(route)
    registry = load_registry()
    scenario_display = args.scenario or '未指定；每次任务自动推断'
    meta = {
        'schema_version': '2.0',
        'target_id': target_id,
        'name': args.name,
        'slug': slug,
        'identity_selection': selection,
        'namesake_gate': {
            'schema_version': namesake_gate.get('schema_version'),
            'normalized_name': namesake_gate.get('normalized_name'),
            'resolution': namesake_gate.get('resolution'),
            'candidate_count': namesake_gate.get('candidate_count'),
            'chosen_subject_uid': namesake_gate.get('selected_subject_uid'),
            'chosen_candidate': (namesake_gate.get('candidates') or [None])[0] if namesake_gate.get('resolution') == 'single' else None,
        },
        'chosen_subject_uid': namesake_gate.get('selected_subject_uid'),
        'normalized_name': namesake_gate.get('normalized_name'),
        'subject_origin': effective_origin,
        'origin_review_required': origin_review_required,
        'profile': args.profile,
        'status': status,
        'scenario': args.scenario,
        'scenario_policy': 'optional-build-hint; infer-per-runtime-task',
        'language': args.language,
        'time_scope': args.time_scope,
        'consent_authority': args.consent_authority,
        'retention_policy': args.retention_policy,
        'prohibited_uses': [
            'identity authentication or deceptive impersonation',
            'invented endorsement, signature, consent, private memory or current opinion',
            'unsupported psychological diagnosis',
            'replacement of accountable high-stakes professional judgment',
        ],
        'existential_hypotheses_enabled': bool(args.enable_existential_hypotheses),
        'builder_version': 'v0.0.0.5',
        'model_version': '0.1.0-draft',
        'product_version': None,
        'product_version_policy': 'per-canonical-person; 0.0.0.1..0.0.0.999; consumed-on-successful-registration',
        'runtime_invocation_versioning': False,
        'created_at': now,
        'updated_at': now,
        'current_version': None,
    }
    values = {
        'TARGET_NAME': args.name,
        'TARGET_NAME_YAML': json.dumps(args.name, ensure_ascii=False),
        'SLUG': slug,
        'PROFILE': args.profile,
        'SUBJECT_ORIGIN': effective_origin,
        'IDENTITY_DISPLAY': selection['display'],
        'IDENTITY_CANONICAL': selection['canonical'],
        'SCENARIO_DISPLAY': scenario_display,
        'LANGUAGE': args.language,
        'TIME_SCOPE': args.time_scope,
        'TARGET_ID': target_id,
        'SUBJECT_UID': subject_uid(args.name, effective_origin),
        'REGISTRATION_IDENTITY_FAMILY_ID': category_for_identity(selection)['identity_family_id'],
        'CREATED_AT': now,
        'IDENTITY_CATALOG_JSON': json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True),
        'ROUTE_MANIFEST_JSON': json.dumps(route, ensure_ascii=False, indent=2, sort_keys=True),
        'SOURCE_UNIVERSE_JSON': json.dumps(universe, ensure_ascii=False, indent=2, sort_keys=True),
    }
    template_root = Path(__file__).resolve().parents[1] / 'templates' / 'target'
    target.mkdir(parents=True)
    for source in sorted(template_root.rglob('*')):
        rel = source.relative_to(template_root)
        if '__pycache__' in rel.parts or source.suffix in {'.pyc', '.pyo'}:
            continue
        if source.is_dir():
            ensure_dir(target / rel)
            continue
        output_rel = Path(str(rel)[:-5]) if str(rel).endswith('.tmpl') else rel
        output = target / output_rel
        ensure_dir(output.parent)
        text = render(source.read_text(encoding='utf-8'), values)
        atomic_write_text(output, text, mode=0o600 if output.suffix in {'.json', '.jsonl'} else None)
        if output.suffix in {'.py', '.sh'} or output.name == 'install.py':
            output.chmod(output.stat().st_mode | 0o111)
    atomic_write_json(target / 'meta.json', meta, mode=0o600)
    atomic_write_json(target / 'route-manifest.json', route, mode=0o600)
    atomic_write_json(target / 'research' / 'source-universe.json', universe, mode=0o600)

    result = {
        'target': str(target),
        'slug': slug,
        'status': status,
        'identity': selection,
        'scenario': args.scenario,
        'subject_origin': effective_origin,
        'origin_review_required': origin_review_required,
        'next': [
            f'python3 scripts/ingest.py {target} INPUT...',
            f'python3 scripts/quality_check.py {target} --phase research --write-report',
            f'python3 scripts/package_target.py {target} --output dist/',
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    if status.startswith('blocked'):
        print('BLOCKED: record consent/authority before private research or packaging.', file=sys.stderr)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
