#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from identity_runtime import menu, parse

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


def infer(task: str, selection: dict[str, Any]) -> tuple[list[str], dict[str, Any]]:
    scored = keyword_scores(task)
    selected = [scenario for _, scenario in scored[:2]]
    basis: dict[str, Any] = {'task_keyword_scores': {scenario: score for score, scenario in scored}, 'identity_priors_used': []}
    identities = sorted(selection['weights'], key=selection['weights'].get, reverse=True)
    priors: list[str] = []
    for identity_id in identities:
        for scenario in IDENTITY_SCENARIO_PRIORS.get(identity_id, []):
            if scenario not in priors:
                priors.append(scenario)
    # Scenario is never required. Identity priors provide a deterministic fallback and may fill a second route.
    for scenario in priors:
        if len(selected) >= 2:
            break
        if scenario not in selected:
            selected.append(scenario)
            basis['identity_priors_used'].append(scenario)
    if not selected:
        selected = ['general-agentic-work']
        basis['identity_priors_used'] = ['general-agentic-work']
    basis['primary_basis'] = 'task-keywords' if scored else 'identity-prior'
    return selected[:2], basis


def plan(identity: str, task: str) -> dict[str, Any]:
    selection = parse(identity)
    scenarios, basis = infer(task, selection)
    files = ['boundaries.md', 'corrections/ACTIVE.md', 'facts.md']
    for identity_id in sorted(selection['weights'], key=selection['weights'].get, reverse=True):
        files.append(f'identity-facets/{identity_id}.md')
    files.extend(['cognitive-os.md', 'decision-policy.md', 'strategy.md', 'capabilities.md', 'work.md', 'persona.md'])
    for scenario in scenarios:
        candidate = f'scenario-adapters/{scenario}.md'
        files.append(candidate if (ROOT / candidate).is_file() else 'scenario-adapters/auto.md')
    files.append('divergence-map.md')
    files = list(dict.fromkeys(files))
    return {
        'identity_selection': selection,
        'scenarios': scenarios,
        'route_basis': basis,
        'load_files': files,
        'execution_loop': [
            'model-task', 'retrieve-minimum', 'plan-as-target', 'act-with-host-tools',
            'verify-facts-results-and-risks', 'deliver-with-artifact-version', 'record',
        ],
        'output_contract': {
            'chat_label': '运行版本：0.0.0.N',
            'file_naming': '<artifact-name>-v0.0.0.N.<ext>',
            'manifest': 'runtime/runs/0.0.0.N/artifact-manifest.json',
        },
        'warning': 'Do not load source bodies, all research files, other identity facets, or full run history unless an evidence audit explicitly requires them.',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Token-efficient runtime identity and scenario router.')
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('menu')
    p = sub.add_parser('plan')
    p.add_argument('--identity', required=True)
    p.add_argument('--task', default='')
    args = parser.parse_args()
    try:
        if args.command == 'menu':
            print(menu())
        else:
            print(json.dumps(plan(args.identity, args.task), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        print(f'ERROR: {exc}', file=sys.stderr)
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
