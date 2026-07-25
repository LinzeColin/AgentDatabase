#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[1] / 'registries' / 'identity-families.json'


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    families = data.get('families')
    if not isinstance(families, list) or len(families) != 12:
        raise ValueError('identity registry must contain exactly twelve families')
    return data


def _alias_map(registry: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for family in registry['families']:
        values = [str(family['number']), family['id'], family['zh'], *family.get('aliases', [])]
        for value in values:
            key = str(value).strip().casefold().replace('_', '-').replace(' ', '')
            if key in mapping and mapping[key] != family['id']:
                raise ValueError(f'ambiguous identity alias: {value}')
            mapping[key] = family['id']
    return mapping


def resolve_identity(value: str, registry: dict[str, Any] | None = None) -> str:
    registry = registry or load_registry()
    key = value.strip().casefold().replace('_', '-').replace(' ', '')
    mapping = _alias_map(registry)
    if key not in mapping:
        options = '、'.join(f"{f['number']} {f['zh']}" for f in registry['families'])
        raise ValueError(f'unknown identity {value!r}; choose {options}')
    return mapping[key]


def parse_identity_spec(spec: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_registry()
    raw = spec.strip()
    if not raw:
        raise ValueError('identity selection is required')
    # 多重身份已移除：每个人物只归属 1–12 中的单一主身份。拒绝加权/复合选择。
    if raw.startswith('{') or any(sep in raw for sep in [':', '=', '+', ',', '，', ';', '；']):
        raise ValueError('多重身份已移除；请从 1–12 中选择单一主身份，例如 “2” 或 “软件开发师”')
    identity_id = resolve_identity(raw, registry)
    return {
        'mode': 'single',
        'primary': identity_id,
        'weights': {identity_id: 1.0},
        'canonical': identity_id,
        'display': next(f['zh'] for f in registry['families'] if f['id'] == identity_id),
    }


def menu(compact: bool = True, registry: dict[str, Any] | None = None) -> str:
    registry = registry or load_registry()
    if compact:
        return '｜'.join(f"{f['number']} {f['zh']}" for f in registry['families'])
    return '\n'.join(f"{f['number']}. {f['zh']}（{'、'.join(f.get('merged_from', []))}）" for f in registry['families'])


def main() -> int:
    parser = argparse.ArgumentParser(description='Parse Persona Distiller identity selections.')
    sub = parser.add_subparsers(dest='command', required=True)
    p_menu = sub.add_parser('menu')
    p_menu.add_argument('--long', action='store_true')
    p_parse = sub.add_parser('parse')
    p_parse.add_argument('--spec', required=True)
    args = parser.parse_args()
    try:
        if args.command == 'menu':
            print(menu(compact=not args.long))
        else:
            print(json.dumps(parse_identity_spec(args.spec), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
