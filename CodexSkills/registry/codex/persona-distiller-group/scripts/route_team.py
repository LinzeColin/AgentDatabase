#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from registry_core import CATEGORY_BY_FOLDER, default_registry_root

IDENTITY_SIGNALS = {
    "材料建工师": (
        "技术", "工程", "材料", "焊接", "冶金", "管道", "机械", "可靠性", "维护", "摩擦", "腐蚀", "无损检测",
        "material", "welding", "metallurgy", "piping", "mechanical", "maintenance", "reliability", "tribology", "engineering", "technical",
    ),
    "软件开发师": (
        "软件", "开发", "编程", "算法", "代码", "数据", "人工智能", "机器学习", "系统", "架构", "后端", "前端",
        "software", "developer", "programming", "algorithm", "code", "data", "ai", "ml", "backend", "frontend", "devops",
    ),
    "艺术设计师": (
        "设计", "艺术", "产品设计", "平面", "交互", "建筑设计", "美术", "动画", "导演", "摄影", "音乐", "创意",
        "design", "art", "ux", "ui", "creative", "illustration", "animation", "director",
    ),
    "创业经营师": (
        "创业", "经营", "企业", "创始", "高管", "运营", "组织", "增长", "管理", "零售", "门店", "扩张",
        "founder", "business", "startup", "operations", "organization", "management", "growth", "ceo", "retail",
    ),
    "投资资本师": (
        "投资", "估值", "资本", "组合", "基金", "私募", "风投", "交易", "回报",
        "investment", "valuation", "capital", "portfolio", "fund", "returns",
    ),
    "思想教育师": (
        "思想", "教育", "学习", "教学", "写作", "哲学", "训练", "传播", "记者",
        "education", "learning", "teaching", "philosophy", "writing", "coach", "journalist",
    ),
    "政治法律师": (
        "政治", "法律", "政策", "治理", "制度", "诉讼", "律师", "法院", "外交",
        "legal", "law", "policy", "governance", "litigation", "diplomacy",
    ),
    "客户营销师": (
        "营销", "市场", "客户", "品牌", "销售", "广告", "公关", "推广", "电商", "市场分析", "客户画像",
        "marketing", "customer", "brand", "sales", "advertising", "growth", "seo", "crm",
    ),
    "建造采购师": (
        "施工", "建造", "工程管理", "项目管理", "造价", "估算", "招投标", "进度", "采购", "供应链", "物流", "仓储",
        "construction", "project", "estimation", "procurement", "supply chain", "logistics", "tender", "bidding", "bim",
    ),
    "财务合规师": (
        "财务", "会计", "审计", "成本", "税务", "风控", "合规", "内控", "安全", "标准", "规范", "认证",
        "finance", "accounting", "audit", "tax", "risk", "compliance", "safety", "ehs", "regulatory",
    ),
    "医疗护理师": (
        "医疗", "医生", "护理", "护士", "临床", "诊断", "治疗", "药", "公共卫生", "兽医", "康复", "心理",
        "healthcare", "medical", "doctor", "nurse", "clinical", "diagnosis", "therapy", "pharmacy",
    ),
    "农林牧渔师": (
        "农业", "农学", "种植", "养殖", "畜牧", "林业", "渔业", "水产", "园艺", "农机", "食品",
        "agriculture", "farming", "agronomy", "forestry", "livestock", "fishery", "aquaculture", "horticulture",
    ),
}

SCENARIO_SIGNALS = {
    "research-problem-solving": ("研究", "调查", "诊断", "验证", "research", "investigate", "diagnose"),
    "strategy-decision": ("战略", "决策", "选择", "取舍", "strategy", "decision", "choose"),
    "general-agentic-work": ("执行", "完成", "操作", "agent", "execute", "implement"),
    "product-creation": ("产品", "设计", "创作", "开发", "product", "design", "create", "build"),
    "investment-business": ("投资", "估值", "商业", "资本", "investment", "valuation", "business"),
    "leadership-organization": ("领导", "组织", "团队", "管理", "leadership", "organization", "management"),
    "governance-legal": ("法律", "治理", "政策", "诉讼", "legal", "governance", "policy", "litigation"),
    "communication-negotiation": ("沟通", "谈判", "说服", "表达", "communication", "negotiation", "persuasion"),
    "teaching-learning": ("教学", "学习", "培训", "教育", "teaching", "learning", "education"),
    "red-team-risk": ("风险", "反证", "红队", "失败", "risk", "counterevidence", "red team", "failure"),
}

GENERIC_MATCH_TERMS = {
    "研究",
    "调查",
    "诊断",
    "验证",
    "执行",
    "完成",
    "操作",
    "产品",
    "设计",
    "创作",
    "开发",
    "架构",
    "research",
    "investigate",
    "diagnose",
    "agent",
    "execute",
    "implement",
    "product",
    "design",
    "create",
    "build",
    "architecture",
}

CONTROL_ROLES = (
    {
        "role_id": "counterevidence-analyst",
        "role_type": "neutral-control",
        "purpose": "寻找最强反证、替代解释、边界条件和可推翻标准。",
    },
    {
        "role_id": "independent-reviewer",
        "role_type": "neutral-control",
        "purpose": "独立复核证据链、遗漏、可执行性、当前性和硬边界。",
    },
    {
        "role_id": "decision-judge",
        "role_type": "neutral-control",
        "purpose": "依据预先 rubric 对密封候选作最终裁决，不参与原方案生成。",
    },
)
POSITIVE_FILLERS = (
    {
        "role_id": "evidence-researcher",
        "role_type": "neutral-positive",
        "purpose": "补齐当前事实、一手来源、定义和可验证证据。",
    },
    {
        "role_id": "execution-planner",
        "role_type": "neutral-positive",
        "purpose": "把候选方案转成步骤、资源、依赖、验证和停止条件。",
    },
    {
        "role_id": "synthesis-lead",
        "role_type": "neutral-positive",
        "purpose": "合并互补方案并保留实质分歧，形成最终交付骨架。",
    },
)


def occurrences(text: str, signals: tuple[str, ...]) -> int:
    lowered = text.casefold()
    return sum(1 for signal in signals if signal.casefold() in lowered)


def infer_identity(task: str) -> tuple[str, list[dict[str, Any]]]:
    scores = [
        {"identity": identity, "matches": occurrences(task, signals)}
        for identity, signals in IDENTITY_SIGNALS.items()
    ]
    scores.sort(key=lambda item: (-item["matches"], item["identity"]))
    positive = [item for item in scores if item["matches"] > 0]
    if not positive:
        return str(scores[0]["identity"]), scores
    return str(positive[0]["identity"]), scores


def infer_scenario(task: str) -> tuple[str, list[dict[str, Any]]]:
    scores = [
        {"scenario": scenario, "matches": occurrences(task, signals)}
        for scenario, signals in SCENARIO_SIGNALS.items()
    ]
    scores.sort(key=lambda item: (-item["matches"], item["scenario"]))
    if scores[0]["matches"] == 0:
        return "general-agentic-work", scores
    return str(scores[0]["scenario"]), scores


def task_terms(task: str) -> set[str]:
    ascii_terms = set(re.findall(r"[a-z0-9][a-z0-9-]{1,}", task.casefold()))
    chinese_terms = {
        signal
        for signals in (*IDENTITY_SIGNALS.values(), *SCENARIO_SIGNALS.values())
        for signal in signals
        if any("\u4e00" <= character <= "\u9fff" for character in signal)
        and signal in task
    }
    return ascii_terms | chinese_terms


def semantic_matches(values: Any, terms: set[str]) -> int:
    if not isinstance(values, list):
        return 0
    text = " ".join(str(value).casefold() for value in values)
    return sum(1 for term in terms if term.casefold() in text)


def freshness_score(cutoff: Any) -> int:
    if not isinstance(cutoff, str):
        return 0
    match = re.match(r"^(\d{4})", cutoff)
    if not match:
        return 1
    age = max(0, date.today().year - int(match.group(1)))
    return max(0, 5 - age)


def score_candidate(
    candidate: dict[str, Any],
    *,
    identity: str,
    scenario: str,
    terms: set[str],
) -> tuple[int, list[str], str | None]:
    if candidate.get("readiness") != "ready":
        return 0, [], "readiness is not ready"
    identity_score = 0
    if candidate.get("registration_category") == identity:
        identity_score = 25
    scenarios = candidate.get("application_scenarios", [])
    scenario_text = " ".join(str(value).casefold() for value in scenarios)
    exact_scenario = scenario.casefold() in scenario_text
    scenario_score = 25 if exact_scenario else min(20, semantic_matches(scenarios, terms) * 5)
    capability_matches = semantic_matches(candidate.get("key_capabilities"), terms)
    capability_score = min(20, capability_matches * 4)
    if capability_score == 0 and identity_score:
        capability_score = 8
    value_matches = semantic_matches(candidate.get("user_value"), terms)
    value_score = min(15, value_matches * 3)
    if value_score == 0 and scenario_score:
        value_score = 6
    complementarity_score = 10
    freshness = freshness_score(candidate.get("research_cutoff"))
    specific_terms = terms - GENERIC_MATCH_TERMS
    task_specific_matches = sum(
        semantic_matches(candidate.get(field), specific_terms)
        for field in ("application_scenarios", "key_capabilities", "user_value")
    )
    score = identity_score + scenario_score + capability_score + value_score + complementarity_score + freshness
    reasons = [
        f"identity={identity_score}/25",
        f"scenario={scenario_score}/25",
        f"capability={capability_score}/20",
        f"user_value={value_score}/15",
        f"complementarity={complementarity_score}/10",
        f"freshness={freshness}/5",
        f"task_specific_matches={task_specific_matches}",
    ]
    if (
        candidate.get("registration_category") != identity
        and (not exact_scenario or scenario == "general-agentic-work")
        and task_specific_matches == 0
    ):
        return score, reasons, "cross-category candidate has no task-specific semantic match"
    if identity_score == 0 and not exact_scenario and capability_matches < 2:
        return score, reasons, "no material identity, exact-scenario, or capability match"
    if score < 30:
        return score, reasons, "score below 30"
    return score, reasons, None


def main() -> int:
    parser = argparse.ArgumentParser(description="Route a task to a 5–20 role persona expert team.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--size", type=int, default=8)
    parser.add_argument(
        "--identity",
        choices=list(CATEGORY_BY_FOLDER),
        help="Internal test override only; never require this from the caller.",
    )
    parser.add_argument("--registry-root", type=Path, default=default_registry_root())
    args = parser.parse_args()
    if not 5 <= args.size <= 20:
        parser.error("--size must be between 5 and 20")
    root = args.registry_root.expanduser().resolve()
    index = json.loads((root / "team-index.json").read_text(encoding="utf-8"))
    inferred_identity, identity_scores = infer_identity(args.task)
    identity = args.identity or inferred_identity
    scenario, scenario_scores = infer_scenario(args.task)
    terms = task_terms(args.task)
    ranked: list[dict[str, Any]] = []
    excluded: list[dict[str, Any]] = []
    for candidate in index.get("products", []):
        score, reasons, exclusion = score_candidate(
            candidate,
            identity=identity,
            scenario=scenario,
            terms=terms,
        )
        item = {
            "subject_uid": candidate.get("subject_uid"),
            "canonical_name": candidate.get("canonical_name"),
            "registration_category": candidate.get("registration_category"),
            "score": score,
            "score_breakdown": reasons,
            "team_card": candidate.get("team_card"),
            "artifact": candidate.get("latest_artifact"),
        }
        if exclusion:
            item["excluded_because"] = exclusion
            excluded.append(item)
        else:
            ranked.append(item)
    ranked.sort(key=lambda item: (-int(item["score"]), str(item["canonical_name"]).casefold()))
    persona_slots = max(1, args.size - len(CONTROL_ROLES))
    chosen = ranked[:persona_slots]
    selected_roles: list[dict[str, Any]] = [
        {
            **candidate,
            "role_id": f"persona-solver-{index + 1}",
            "role_type": "persona-solver",
            "purpose": "在已证明能力与硬边界内形成独立正向解决方案。",
        }
        for index, candidate in enumerate(chosen)
    ]
    positive_target = args.size - len(CONTROL_ROLES)
    filler_index = 0
    while chosen and len(selected_roles) < positive_target:
        filler = dict(POSITIVE_FILLERS[filler_index % len(POSITIVE_FILLERS)])
        if any(role["role_id"] == filler["role_id"] for role in selected_roles):
            filler["role_id"] = f"{filler['role_id']}-{filler_index + 1}"
        selected_roles.append(filler)
        filler_index += 1
    if chosen:
        selected_roles.extend(dict(role) for role in CONTROL_ROLES)
        status = "ready"
    else:
        status = "insufficient_roster"
    result = {
        "schema_version": "1.0",
        "status": status,
        "task_summary": args.task,
        "inferred_identity": identity,
        "identity_inference": identity_scores,
        "inferred_scenario": scenario,
        "scenario_inference": scenario_scores,
        "requested_size": args.size,
        "actual_size": len(selected_roles),
        "selected_roles": selected_roles,
        "excluded_candidates": excluded,
        "control_roles": [role["role_id"] for role in CONTROL_ROLES],
        "separation_protocol": [
            "persona solvers receive the same task/evidence package and do not review one another",
            "counterevidence runs after candidate generation and cannot edit candidates",
            "independent review receives sealed candidates plus evidence summary",
            "judge receives sealed candidates, counterevidence, review, and a predeclared rubric",
        ],
        "limitations": (
            []
            if chosen
            else [
                "No ready registered persona met the minimum relevance score.",
                "Do not fabricate person experts; expand the registry or use a neutral non-person workflow.",
            ]
        ),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if status == "ready" else 3


if __name__ == "__main__":
    raise SystemExit(main())
