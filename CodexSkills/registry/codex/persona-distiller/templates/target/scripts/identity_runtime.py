#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]


def registry() -> dict[str, Any]:
    return json.loads((ROOT / 'identity-catalog.json').read_text(encoding='utf-8'))


def alias_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for family in registry()['families']:
        for item in [str(family['number']), family['id'], family['zh'], *family.get('aliases', [])]:
            result[str(item).strip().casefold().replace('_', '-').replace(' ', '')] = family['id']
    return result


def resolve(value: str) -> str:
    key = value.strip().casefold().replace('_', '-').replace(' ', '')
    mapping = alias_map()
    if key not in mapping:
        raise ValueError(f'未知身份：{value}')
    return mapping[key]


def parse(spec: str) -> dict[str, Any]:
    raw = spec.strip()
    if not raw:
        raise ValueError('必须选择身份或权重')
    if raw in {'沿用上次身份', 'reuse-last', 'last'}:
        state = json.loads((ROOT / 'runtime' / 'state.json').read_text(encoding='utf-8'))
        last = state.get('last_identity_selection')
        if not last:
            raise ValueError('没有可沿用的上次身份')
        return last
    if raw.startswith('{'):
        parts = json.loads(raw)
        if not isinstance(parts, dict):
            raise ValueError('身份 JSON 必须是对象')
    elif any(x in raw for x in ['+', ',', '，', ';', '；']):
        parts = {}
        for part in re.split(r'[+,，;；]', raw):
            match = re.fullmatch(r'(.+?)\s*[:=]\s*([0-9.]+%?)', part.strip())
            if not match:
                raise ValueError(f'权重格式错误：{part}')
            parts[match.group(1)] = match.group(2)
    elif ':' in raw or '=' in raw:
        match = re.fullmatch(r'(.+?)\s*[:=]\s*([0-9.]+%?)', raw)
        if not match:
            raise ValueError('权重格式错误')
        parts = {match.group(1): match.group(2)}
    else:
        identity_id = resolve(raw)
        if identity_id == 'multi-identity':
            raise ValueError('多重身份需要至少两个具体身份权重')
        return {'mode': 'single', 'primary': identity_id, 'weights': {identity_id: 1.0}, 'canonical': identity_id}
    weights: dict[str, float] = {}
    for key, raw_value in parts.items():
        identity_id = resolve(str(key))
        if identity_id == 'multi-identity':
            raise ValueError('权重项不能是“多重身份”')
        text = str(raw_value).strip()
        percent = text.endswith('%')
        if percent:
            text = text[:-1]
        value = float(text)
        if percent or value > 1:
            value /= 100
        if not math.isfinite(value) or value <= 0:
            raise ValueError('权重必须大于 0')
        weights[identity_id] = weights.get(identity_id, 0.0) + value
    if len(weights) < 2:
        raise ValueError('多重身份至少需要两个不同主身份')
    total = sum(weights.values())
    normalized = {key: round(value / total, 6) for key, value in weights.items()}
    drift = round(1 - sum(normalized.values()), 6)
    if drift:
        largest = max(normalized, key=normalized.get)
        normalized[largest] = round(normalized[largest] + drift, 6)
    primary = max(normalized, key=normalized.get)
    return {'mode': 'multi', 'primary': primary, 'weights': normalized, 'canonical': '+'.join(f'{k}:{normalized[k]:.6f}' for k in sorted(normalized))}


def menu() -> str:
    return '请选择本次身份：' + '｜'.join(f"{f['number']} {f['zh']}" for f in registry()['families']) + '；多重示例 1:70+4:30。'
