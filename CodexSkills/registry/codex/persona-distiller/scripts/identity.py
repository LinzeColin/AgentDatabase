#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from typing import Any

REGISTRY_PATH = Path(__file__).resolve().parents[1] / 'registries' / 'identity-families.json'


def load_registry(path: Path = REGISTRY_PATH) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding='utf-8'))
    families = data.get('families')
    if not isinstance(families, list) or len(families) != 7:
        raise ValueError('identity registry must contain exactly seven families')
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


def _parse_weight_number(raw: Any) -> float:
    if isinstance(raw, bool):
        raise ValueError('boolean is not a valid weight')
    text = str(raw).strip()
    percent = text.endswith('%')
    if percent:
        text = text[:-1]
    try:
        value = float(text)
    except ValueError as exc:
        raise ValueError(f'invalid weight {raw!r}') from exc
    if percent or value > 1:
        value /= 100.0
    if not math.isfinite(value) or value <= 0:
        raise ValueError('weights must be finite and > 0')
    return value


def parse_identity_spec(spec: str, registry: dict[str, Any] | None = None) -> dict[str, Any]:
    registry = registry or load_registry()
    raw = spec.strip()
    if not raw:
        raise ValueError('identity selection is required')

    weights_raw: dict[str, Any] = {}
    if raw.startswith('{'):
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError('JSON identity selection must be an object')
        weights_raw = {str(k): v for k, v in value.items()}
    elif any(sep in raw for sep in [':', '=']) and any(sep in raw for sep in ['+', ',', '，', ';', '；']):
        for part in re.split(r'[+,，;；]', raw):
            part = part.strip()
            if not part:
                continue
            match = re.fullmatch(r'(.+?)\s*[:=]\s*([0-9.]+%?)', part)
            if not match:
                raise ValueError(f'invalid weighted identity component: {part!r}')
            weights_raw[match.group(1).strip()] = match.group(2)
    elif ':' in raw or '=' in raw:
        match = re.fullmatch(r'(.+?)\s*[:=]\s*([0-9.]+%?)', raw)
        if not match:
            raise ValueError(f'invalid weighted identity selection: {raw!r}')
        weights_raw[match.group(1).strip()] = match.group(2)
    else:
        identity_id = resolve_identity(raw, registry)
        if identity_id == 'multi-identity':
            raise ValueError('多重身份必须给至少两个身份及权重，例如 1:60+5:40')
        return {
            'mode': 'single',
            'primary': identity_id,
            'weights': {identity_id: 1.0},
            'canonical': identity_id,
            'display': next(f['zh'] for f in registry['families'] if f['id'] == identity_id),
        }

    merged: dict[str, float] = {}
    for key, raw_weight in weights_raw.items():
        identity_id = resolve_identity(key, registry)
        if identity_id == 'multi-identity':
            raise ValueError('权重项不能使用“多重身份”本身；请列出具体主身份')
        merged[identity_id] = merged.get(identity_id, 0.0) + _parse_weight_number(raw_weight)
    if len(merged) < 2:
        raise ValueError('多重身份必须至少包含两个不同主身份')
    total = sum(merged.values())
    normalized = {key: round(value / total, 6) for key, value in merged.items()}
    # Correct rounding drift on the largest component.
    drift = round(1.0 - sum(normalized.values()), 6)
    if drift:
        largest = max(normalized, key=normalized.get)
        normalized[largest] = round(normalized[largest] + drift, 6)
    primary = max(normalized, key=normalized.get)
    by_id = {f['id']: f for f in registry['families']}
    canonical = '+'.join(f'{key}:{normalized[key]:.6f}' for key in sorted(normalized))
    display = ' + '.join(f"{by_id[key]['zh']} {normalized[key] * 100:.1f}%" for key in sorted(normalized, key=normalized.get, reverse=True))
    return {'mode': 'multi', 'primary': primary, 'weights': normalized, 'canonical': canonical, 'display': display}


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
