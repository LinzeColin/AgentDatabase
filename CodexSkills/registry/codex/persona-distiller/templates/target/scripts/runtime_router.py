#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]

SCENARIOS = {
    'research-problem-solving': ['研究', '实验', '假设', '证伪', 'debug', '故障', '架构', '算法', '代码', '技术'],
    'strategy-decision': ['战略', '选择', '决策', '取舍', '路线', '优先级', '资源配置'],
    'product-creation': ['产品', '设计', '创作', '写作', '编辑', '审美', '体验', '开发'],
    'investment-business': ['投资', '估值', '公司', '商业', '股票', '组合', '风险收益', '资本'],
    'leadership-organization': ['组织', '招聘', '管理', '绩效', '文化', '团队', '领导', '经营'],
    'teaching-learning': ['学习', '教学', '课程', '训练', '导师', '解释', '掌握', '思想'],
    'communication-negotiation': ['沟通', '谈判', '说服', '演讲', '回复', '辩论', '冲突', '采访'],
    'governance-legal': ['法律', '政策', '制度', '监管', '判决', '治理', '合规', '政治'],
    'red-team-risk': ['风险', '审计', '红队', '反驳', '失败', '盲点', '攻击面', '复盘'],
}

IDENTITY_SCENARIO_PRIORS = {
    'technical-engineer': ['research-problem-solving', 'red-team-risk'],
    'entrepreneur-operator': ['strategy-decision', 'leadership-organization'],
    'investor-capital-allocator': ['investment-business', 'red-team-risk'],
    'developer-designer': ['product-creation', 'strategy-decision'],
    'thinker-educator': ['teaching-learning', 'communication-negotiation'],
    'political-legal': ['governance-legal', 'strategy-decision'],
}


def keyword_scores(task: str) -> list[tuple[int, str]]:
    lowered = task.casefold()
    scored: list[tuple[int, str]] = []
    for scenario, keywords in SCENARIOS.items():
        score = sum(1 for keyword in keywords if keyword.casefold() in lowered)
        if score:
            scored.append((score, scenario))
    return sorted(scored, key=lambda item: (-item[0], item[1]))


def load_distilled_selection(root: Path = ROOT) -> dict[str, Any]:
    route = json.loads((root / 'route-manifest.json').read_text(encoding='utf-8'))
    selection = route.get('identity_selection')
    if not isinstance(selection, dict):
        raise ValueError('route-manifest identity_selection must be an object')
    weights = selection.get('weights')
    if not isinstance(weights, dict) or not weights:
        raise ValueError('route-manifest identity weights are missing')
    normalized: dict[str, float] = {}
    for identity_id, raw_weight in weights.items():
        if identity_id not in IDENTITY_SCENARIO_PRIORS:
            raise ValueError(f'unsupported distilled identity: {identity_id}')
        weight = float(raw_weight)
        if weight <= 0:
            raise ValueError(f'distilled identity weight must be positive: {identity_id}')
        normalized[str(identity_id)] = weight
    total = sum(normalized.values())
    normalized = {key: value / total for key, value in normalized.items()}
    return {
        'mode': 'multi' if len(normalized) > 1 else 'single',
        'primary': max(normalized, key=normalized.get),
        'weights': normalized,
        'source': 'distilled-route-manifest',
        'user_selection_required': False,
    }


def route_identity(task: str, scenarios: list[str], selection: dict[str, Any]) -> dict[str, Any]:
    weights = dict(selection['weights'])
    if task.strip() and scenarios:
        scores: dict[str, float] = {}
        for identity_id, base_weight in weights.items():
            matches = sum(1 for scenario in scenarios if scenario in IDENTITY_SCENARIO_PRIORS.get(identity_id, []))
            scores[identity_id] = float(base_weight) * (1.0 + matches)
        total = sum(scores.values())
        weights = {identity_id: score / total for identity_id, score in scores.items()}
    rounded = {identity_id: round(weight, 6) for identity_id, weight in weights.items()}
    correction = 1.0 - sum(rounded.values())
    primary = max(rounded, key=rounded.get)
    rounded[primary] = round(rounded[primary] + correction, 6)
    return {
        'mode': 'multi' if len(rounded) > 1 else 'single',
        'primary': primary,
        'weights': rounded,
        'source': selection['source'],
        'strategy': 'automatic-task-routing',
        'user_selection_required': False,
    }


def infer(task: str, selection: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    scored = keyword_scores(task)
    selected = [scenario for _, scenario in scored[:2]]
    basis: dict[str, Any] = {
        'task_keyword_scores': {scenario: score for score, scenario in scored},
        'internal_identity_priors_used': [],
        'user_identity_input': False,
    }
    identities = sorted(selection['weights'], key=selection['weights'].get, reverse=True)
    priors: list[str] = []
    for identity_id in identities:
        for scenario in IDENTITY_SCENARIO_PRIORS.get(identity_id, []):
            if scenario not in priors:
                priors.append(scenario)
    for scenario in priors:
        if len(selected) >= 2:
            break
        if scenario not in selected:
            selected.append(scenario)
            basis['internal_identity_priors_used'].append(scenario)
    if not selected:
        selected = ['general-agentic-work']
        basis['internal_identity_priors_used'] = ['general-agentic-work']
    basis['primary_basis'] = 'task-keywords' if scored else 'distilled-identity-prior'
    return selected[:2], basis


def plan(task: str, root: Path = ROOT) -> dict[str, Any]:
    distilled = load_distilled_selection(root)
    scenarios, basis = infer(task, distilled)
    identity_route = route_identity(task, scenarios, distilled)
    files = ['boundaries.md', 'corrections/ACTIVE.md', 'facts.md']
    for identity_id in sorted(identity_route['weights'], key=identity_route['weights'].get, reverse=True):
        files.append(f'identity-facets/{identity_id}.md')
    files.extend(['cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md', 'work.md', 'persona.md'])
    for scenario in scenarios:
        candidate = f'scenario-adapters/{scenario}.md'
        files.append(candidate if (root / candidate).is_file() else 'scenario-adapters/auto.md')
    files.append('divergence-map.md')
    return {
        'identity_route': identity_route,
        'scenarios': scenarios,
        'route_basis': basis,
        'load_files': list(dict.fromkeys(files)),
        'execution_loop': [
            'model-task', 'retrieve-minimum', 'plan-as-target', 'act-with-host-tools',
            'verify-facts-results-and-risks', 'deliver', 'optionally-record-unnumbered-audit',
        ],
        'output_contract': {
            'invocation_version': None,
            'chat_version_label': False,
            'versioned_file_names': False,
            'audit': 'optional unnumbered runtime/invocations.jsonl record',
        },
        'warning': 'Do not load source bodies, all research files, unavailable identity facets, or full runtime history unless an evidence audit explicitly requires them.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Token-efficient automatic internal identity and scenario router.')
    parser.add_argument('command', choices=['plan'])
    parser.add_argument('--task', default='')
    args = parser.parse_args()
    try:
        print(json.dumps(plan(args.task), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, json.JSONDecodeError, TypeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
