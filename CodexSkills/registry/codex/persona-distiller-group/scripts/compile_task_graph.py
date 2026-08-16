#!/usr/bin/env python3
"""Compile a natural-language request into a deterministic work-packet DAG.

The compiler never chooses a zero-expert path.  Low-complexity requests become
Single Expert; larger requests become Small, Deep, or Swarm according to the
owner-frozen ranges. Mandatory control-plane stages are present in every mode.
"""
from __future__ import annotations

import re

import argparse
import json
import math
from pathlib import Path
from typing import Any

from team_runtime_common import (
    MODE_LIMITS,
    clamp,
    normalized_count,
    required_control_plane,
    tokens,
    valid_mode_size,
    write_json,
)

# ★★★ 2026-08-16 扩表 —— **原表 92 个词要给 12 个专业族分类，实测召回 42%。**
#
#   实测链条（判据 `_ledgers/_pipeline/measure_routing_discrimination.py`）：
#     撞不上 → `infer_domains` 返回 ["general-decision"]
#     而 general-decision **不在任何一个族的 CATEGORY_DOMAINS 里**
#     ⇒ `domain_match` 对全部 101 个候选**在数学上恒为 0**
#     ⇒ 排序落到 `currentness`（人物年代新旧）⇒ **−1.7 pp，低于随机抽人**
#   实测兜底率 **13/24 = 54%**；有领域信号的那 9 题是 **+5.3 pp**。
#
#   漏的是最普通的词：`software-ai` 14 个词里**没有「测试」**（于是纯软件测试题上
#   34 个软件开发师全部 domain_match=0）；`finance` 里没有「定价」；
#   `engineering` 里没有「钢桥」。**词表瞎了，而系统把账记在「没有合适的人」上。**
#   [[blamed-the-channel-my-own-wordlist-was-blind]]
#
#   ★ 扩表**只加词、不删词、不改任何权重与阈值**，也不碰模式/人数/控制面/95-75 门。
#   ★ 只加**单义**的行业词；刻意不加「方案」「优化」「流程」这类跨域通用词 ——
#     它们会把所有任务都点亮，等于另一种失效。
#   ★ 改完必须用同一把尺子跑 24 题对比前后，**变差就回退**（负对照见台账）。
DOMAIN_SIGNALS: dict[str, tuple[str, ...]] = {
    "software-ai": (
        "软件", "代码", "架构", "api", "agent", "llm", "ai", "codex", "python", "数据库",
        "前端", "后端", "部署", "debug",
        # ↓ 2026-08-16 补
        "测试", "单元测试", "ci", "cd", "流水线", "重构", "接口", "sdk", "函数", "命名",
        "版本", "发布", "回滚", "微服务", "服务拆分", "缓存", "并发", "性能", "延迟",
        "日志", "监控", "告警", "bug", "缺陷", "编译", "构建", "仓库", "分支", "评审",
        "code review", "test", "deploy", "rollback", "microservice", "latency", "sdk",
    ),
    "finance-investment": (
        "财务", "会计", "税", "现金流", "估值", "投资", "股票", "债券", "组合", "审计",
        "finance", "valuation",
        # ↓ 2026-08-16 补
        "定价", "计费", "订阅", "客单价", "毛利", "成本", "预算", "回本", "回报", "回撤",
        "收入确认", "对冲", "汇率", "利率", "股权", "融资", "摊销", "折旧", "资产", "负债",
        "roi", "pricing", "revenue", "margin", "hedge", "budget", "payback",
    ),
    "legal-policy": (
        "法律", "合同", "诉讼", "监管", "政策", "合规", "legal", "regulation", "governance",
        # ↓ 2026-08-16 补
        "条款", "解约", "违约", "仲裁", "复议", "规章", "越权", "授权", "责任", "赔偿",
        "知识产权", "专利", "商标", "隐私", "反垄断", "听证", "判例", "管辖",
        "contract", "arbitration", "liability", "patent", "privacy", "antitrust",
    ),
    # ★★★ `operations-product` **有意不扩**。实测：它出现在 **12 个族里的 7 个**
    #   （创业经营／客户营销／建造采购／思想教育／投资资本／政治法律／艺术设计），
    #   往它加词 = 把 7/12 的人一起点亮 = **稀释**，不是分辨。
    #   第一版扩表时我给它加了 24 个词，`factory-layout` 当场从 **+10.4 → −3.0**
    #   （最大的一处回退）。回退这一族之后重测（见台账）。
    #   ⇒ **加词之前先看这个 domain 被几个族共用**：共用越多，加词越像噪声。
    #   [[merging-two-signals-cancels-both]]｜[[loosen-only-the-exonerating-side]]
    "operations-product": (
        "运营", "产品", "用户", "市场", "战略", "组织", "流程", "供应链", "采购",
        "product", "operations", "strategy",
    ),
    "engineering-industry": (
        "工程", "机械", "材料", "焊接", "设备", "制造", "可靠性", "施工", "industrial",
        "engineering",
        # ↓ 2026-08-16 补
        "钢", "桥", "钢桥", "焊缝", "裂纹", "疲劳", "腐蚀", "热处理", "硬度", "合金",
        "铸造", "锻造", "管道", "压力容器", "阀门", "检测", "探伤", "延寿", "判废",
        "公差", "装配", "车间", "厂房", "自动化", "分拣",
        "weld", "fatigue", "corrosion", "alloy", "pipeline", "inspection",
    ),
    "research-education": (
        "研究", "论文", "教学", "课程", "证据", "benchmark", "实验", "research", "study",
        "education",
        # ↓ 2026-08-16 补
        "教材", "年级", "学生", "教师", "学习", "认知", "评估", "考试", "科学课",
        "课堂", "培养", "探究", "教研",
        "curriculum", "pedagogy", "classroom", "assessment",
    ),
    "creative-design": (
        "设计", "视觉", "文案", "视频", "品牌", "创意", "ui", "ux", "creative", "design",
        # ↓ 2026-08-16 补
        "排版", "字号", "字体", "行距", "配色", "版式", "图标", "插画", "海报",
        "规范", "组件库", "样式", "可读性", "美学",
        "typography", "font", "layout", "palette", "icon", "readability",
    ),
    "healthcare": (
        "医疗", "护理", "药", "诊断", "治疗", "健康", "medical", "health",
        # ↓ 2026-08-16 补
        "护士", "医生", "病人", "患者", "分诊", "急诊", "门诊", "住院", "病房",
        "诊所", "医院", "临床", "疫苗", "手术", "康复", "流行病",
        "nurse", "clinic", "hospital", "triage", "clinical", "patient",
    ),
    "agriculture": (
        "农业", "种植", "养殖", "食品", "农场", "agriculture", "farming",
        # ↓ 2026-08-16 补
        "果园", "作物", "土壤", "施肥", "灌溉", "病害", "虫害", "砧木", "育种",
        "农地", "耕地", "收成", "牲畜", "饲料", "烂根",
        "crop", "soil", "irrigation", "orchard", "livestock", "harvest",
    ),
}

HIGH_RISK = (
    "法律", "医疗", "财务", "税", "投资", "安全", "合规", "生产", "人身", "监管", "诉讼",
    "legal", "medical", "financial", "compliance", "safety", "production", "regulated",
)
CURRENTNESS = ("最新", "当前", "今天", "本周", "现在", "价格", "法规", "版本", "latest", "current", "today", "price", "version")
PARALLEL = ("全网", "批量", "所有", "多文件", "多平台", "竞品", "矩阵", "并行", "遍历", "global", "batch", "all", "parallel", "competitor")
DEPENDENCY = ("迁移", "修复", "重构", "兼容", "部署", "数据库", "状态", "依赖", "migration", "refactor", "debug", "deploy", "dependency")
DELIVERABLE = ("压缩包", "zip", "报告", "任务包", "代码", "文件", "页面", "系统", "方案", "benchmark", "交付")


_ASCII_WORD = re.compile(r"^[a-z0-9][a-z0-9+.#/_-]*$")
_BOUNDARY_CACHE: dict[str, re.Pattern[str]] = {}


def _signal_hits(signal: str, low: str) -> bool:
    """Does this domain keyword occur in the (already case-folded) task text?

    Matching rule is **per script**, because one rule cannot serve both:

    * **ASCII keywords -> word-boundary match.** Plain substring matching made
      ``ci`` (continuous integration) fire on "de*ci*de" and ``ai`` fire on
      "av*ai*lable" / "cert*ai*n" / "det*ai*l". Measured 2026-08-17: the task
      "Decide whether to proceed." -- which contains no technical vocabulary at
      all -- was classified ``software-ai`` and handed 34 domain-matched
      candidates. Two-letter keywords make substring matching untenable.

    * **Non-ASCII (CJK) keywords -> substring match.** ``\b`` is defined
      against ``\w``, and CJK characters *are* ``\w``, so ``\b软件\b`` never
      matches inside "的软件架构并" -- both neighbours are word characters, so
      there is no boundary to find. Chinese is written without spaces; applying
      the ASCII rule to it silently drops **every** Chinese keyword.

    Both halves cost a real error before this function existed: the ASCII half
    let a keyword-free English sentence claim a domain, and the CJK half made a
    check of mine report 12 correctly-classified Chinese tasks as false hits.
    A regex has to clear the language of the corpus it runs on.
    """
    if _ASCII_WORD.match(signal):
        pat = _BOUNDARY_CACHE.get(signal)
        if pat is None:
            pat = _BOUNDARY_CACHE[signal] = re.compile(
                r"(?<![a-z0-9])%s(?![a-z0-9])" % re.escape(signal))
        return bool(pat.search(low))
    return signal in low


def infer_domains(task: str) -> list[str]:
    low = task.casefold()
    scored = []
    for domain, signals in DOMAIN_SIGNALS.items():
        count = sum(1 for signal in signals if _signal_hits(signal, low))
        if count:
            scored.append((count, domain))
    scored.sort(key=lambda item: (-item[0], item[1]))
    return [domain for _, domain in scored] or ["general-decision"]


def task_profile(task: str) -> dict[str, Any]:
    word_count = max(1, len(tokens(task)))
    domains = infer_domains(task)
    conjunctions = sum(task.count(x) for x in ("，", "、", ";", "；", "以及", "并且", "同时", " and "))
    complexity = clamp(
        0.14
        + min(word_count, 120) / 170
        + min(conjunctions, 14) / 35
        + min(len(domains), 6) / 18
        + normalized_count(task, DELIVERABLE, 5) * 0.16
    )
    risk = clamp(0.08 + normalized_count(task, HIGH_RISK, 4) * 0.76)
    currentness = clamp(normalized_count(task, CURRENTNESS, 3))
    parallel = clamp(0.08 + normalized_count(task, PARALLEL, 4) * 0.78)
    coupling = clamp(0.12 + normalized_count(task, DEPENDENCY, 4) * 0.74)
    return {
        "complexity": round(complexity, 4),
        "risk": round(risk, 4),
        "currentness": round(currentness, 4),
        "parallelizability": round(parallel, 4),
        "coupling": round(coupling, 4),
        "domains": domains,
        "token_count_proxy": word_count,
    }


def choose_mode(profile: dict[str, Any], requested: str = "auto", requested_size: int | None = None) -> tuple[str, int, list[str]]:
    reasons: list[str] = []
    if requested != "auto":
        mode = requested
        if requested_size is None:
            requested_size = MODE_LIMITS[mode][0]
        if not valid_mode_size(mode, requested_size):
            low, high = MODE_LIMITS[mode]
            span = f">={low}" if high is None else f"{low}-{high}"
            raise ValueError(f"{mode} requires {span} persona experts")
        return mode, requested_size, ["explicit owner/runtime override"]

    complexity = float(profile["complexity"])
    risk = float(profile["risk"])
    parallel = float(profile["parallelizability"])
    coupling = float(profile["coupling"])
    domains = len(profile["domains"])

    estimated_packets = max(1, math.ceil(2 + 20 * parallel + 8 * complexity + 2 * domains))
    if parallel >= 0.72 and estimated_packets >= 25 and coupling < 0.72:
        mode = "swarm"
        size = max(25, min(60, estimated_packets))
        reasons.append("highly parallel work has at least 25 useful shards")
    elif complexity >= 0.76 or risk >= 0.72 or domains >= 5:
        mode = "deep_team"
        size = min(30, max(10, round(10 + 12 * complexity + 8 * risk + domains)))
        reasons.append("high depth, risk, or cross-domain load")
    elif complexity >= 0.38 or risk >= 0.36 or domains >= 2:
        mode = "small_team"
        size = min(15, max(5, round(5 + 6 * complexity + 3 * risk + domains)))
        reasons.append("multi-capability task with bounded coordination")
    else:
        mode = "single_expert"
        size = 1
        reasons.append("one persona expert is sufficient; mandatory controls still execute")

    if requested_size is not None:
        if not valid_mode_size(mode, requested_size):
            raise ValueError(f"requested size {requested_size} is invalid for inferred mode {mode}")
        size = requested_size
        reasons.append("explicit size accepted inside inferred mode")
    return mode, size, reasons


def _packet(packet_id: str, kind: str, objective: str, domains: list[str], dependencies: list[str], *, parallel_group: str | None = None) -> dict[str, Any]:
    return {
        "packet_id": packet_id,
        "kind": kind,
        "objective": objective,
        "domains": domains,
        "dependencies": dependencies,
        "parallel_group": parallel_group,
        "required_output": {
            "conclusion": "bounded conclusion",
            "evidence": "claim/source references",
            "assumptions": "explicit assumptions",
            "failure_conditions": "conditions that invalidate the output",
            "next_action": "one executable next action",
        },
    }


def compile_graph(task: str, requested_mode: str = "auto", requested_size: int | None = None) -> dict[str, Any]:
    profile = task_profile(task)
    mode, size, mode_reasons = choose_mode(profile, requested_mode, requested_size)
    domains = profile["domains"]

    packets: list[dict[str, Any]] = [
        _packet("WP-001", "problem-framing", "把用户目标编译为交付物、约束、成功条件和停止条件。", domains, []),
        _packet("WP-002", "evidence-map", "建立事实、来源、未知、当前性和证据缺口地图。", domains, ["WP-001"]),
        _packet("WP-003", "solution-analysis", "在人物能力与边界内形成可执行解决方案。", domains, ["WP-001", "WP-002"]),
        _packet("WP-004", "artifact-plan", "把解决方案转成用户所需的最终制品或行动包。", domains, ["WP-003"]),
    ]

    # Large teams need enough independent ownership units; these are real work shards,
    # not duplicated requests for opinions.
    target_packets = {
        "single_expert": 4,
        "small_team": max(6, min(15, size)),
        "deep_team": max(12, min(30, size)),
        "swarm": max(25, size),
    }[mode]
    while len(packets) < target_packets:
        idx = len(packets) + 1
        domain = domains[(idx - 1) % len(domains)]
        packets.append(_packet(
            f"WP-{idx:03d}",
            "independent-shard",
            f"独立处理第 {idx - 4} 个证据／方案／对象分片，并提交可合并的结构化产物。",
            [domain],
            ["WP-001"],
            parallel_group="DISCOVERY-A",
        ))

    control_stages = [
        {"stage": "G0", "role": "hypothesis-framer", "after": ["WP-001"], "gate": "assumptions and falsifiers frozen"},
        {"stage": "G1", "role": "counterevidence-adversary", "after": [p["packet_id"] for p in packets], "gate": "counterevidence attached"},
        {"stage": "G2", "role": "independent-reviewer", "after": ["G1"], "gate": "review findings resolved or surfaced"},
        {"stage": "G3", "role": "decision-judge", "after": ["G2"], "gate": "one adjudicated decision with change triggers"},
        {"stage": "G4", "role": "synthesis-lead", "after": ["G3"], "gate": "single coherent delivery produced"},
    ]

    return {
        "schema_version": "persona-team.task-graph.v2",
        "task": task,
        "profile": profile,
        "mode": mode,
        "persona_expert_target": size,
        "mode_reasons": mode_reasons,
        "persona_count_contract": {
            "single_expert": "exactly 1 persona expert",
            "small_team": "5-15 persona experts",
            "deep_team": "10-30 persona experts",
            "swarm": "25+ persona experts",
            "controls_excluded_from_persona_count": True,
            "solo_allowed": False,
        },
        "control_plane": required_control_plane(),
        "work_packets": packets,
        "control_stages": control_stages,
        "merge_contract": {
            "unit": "structured artifact, not free-form opinion",
            "conflict_rule": "compare assumptions, evidence, predictions, failure conditions and applicability; no majority vote",
            "final_owner": "synthesis-lead after decision-judge",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile an expert-team work-packet DAG.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["auto", *MODE_LIMITS], default="auto")
    parser.add_argument("--size", type=int)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        graph = compile_graph(args.task, args.mode, args.size)
    except ValueError as exc:
        parser.error(str(exc))
    if args.output:
        write_json(args.output, graph)
        print(json.dumps({"written": str(args.output), "mode": graph["mode"], "persona_expert_target": graph["persona_expert_target"]}, ensure_ascii=False))
    else:
        print(json.dumps(graph, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
