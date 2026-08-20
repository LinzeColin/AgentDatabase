#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""aei.py —— 对标 Anthropic Economic Index 的分析。

AEI 报告的核心是四件事，这里逐项给出本机数据能回答的版本：

  1. 协作模式  自动化(指派 / 反馈环) vs 增强(迭代 / 学习 / 校验)
     —— AEI 的五分法，不是「自动化 vs 协作」两分。上一版只有四个粗桶，
        分不出「我在学」和「我在校验」，那正是 AEI 最有信息量的一刀。
  2. 任务分布  每类任务的份额，以及**每类任务各自的自动化率**
     —— AEI 真正的看点不是总自动化率，是「哪类活已经能交出去、哪类还得盯着」。
  3. 技能呈现  用到了哪些能力（读 / 写 / 执行 / 检索 / 联网）
     —— AEI 用 O*NET 技能，这里用工具调用作为可观测代理。
  4. 深度与广度 + 集中度

全部为确定性统计，运行期不调用任何模型。判不出来的写「未归类」，不硬塞。
"""
from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

# —— 语言标记：这两类靠说了什么判，不靠结构判 ——
LEARNING = re.compile(
    r"为什么|怎么理解|什么是|解释一下|原理|讲讲|讲一下|教我|区别是|有什么不同|"
    r"能不能说明|科普|why does|how does|what is|explain", re.I)
VALIDATION = re.compile(
    r"检查|复核|复审|核对|确认一下|对不对|是否正确|验证|审一下|查一下有没有|"
    r"帮我看看有没有问题|double.?check|verify|review the", re.I)

# —— 结构阈值 ——
DIRECTIVE_TOOLS = 8      # 保留给「重指派」的标注，不再作为归类门槛
FEEDBACK_TOOLS = 15      # 轮次很少但工具极多，且提到过报错 = 它自己在跟环境较劲
ITERATION_TURNS = 5      # 来回这么多次 = 协作迭代

MODES = {
    "指派":   {"group": "自动化", "desc": "一句话丢过去，机器自己干完一长串，中途你没再插手"},
    "反馈环": {"group": "自动化", "desc": "你几乎没说话，但它反复撞报错再自己修 —— 跟环境较劲，不是跟你"},
    "迭代":   {"group": "增强",   "desc": "来回五次以上打磨出来的"},
    "学习":   {"group": "增强",   "desc": "你在问「为什么 / 是什么 / 怎么理解」"},
    "校验":   {"group": "增强",   "desc": "你在让它检查、复核、确认"},
    "未归类": {"group": "未归类", "desc": "既没有足够轮次也没有明确语言标记，如实留空"},
}

# —— 工具 → 能力。AEI 用 O*NET 技能，这里用工具调用当可观测代理 ——
SKILL_MAP = [
    (re.compile(r"read|view|cat|open|glob|ls", re.I),            "读取"),
    (re.compile(r"write|edit|patch|apply|create|str_replace", re.I), "写入"),
    (re.compile(r"bash|shell|exec|run|command|terminal", re.I),  "执行"),
    (re.compile(r"grep|search|find|ripgrep", re.I),              "检索"),
    (re.compile(r"web|fetch|http|browser|url", re.I),            "联网"),
    (re.compile(r"task|agent|spawn|subagent", re.I),             "派生子任务"),
    (re.compile(r"todo|plan|think", re.I),                       "规划"),
]


def classify_mode(s: dict) -> str:
    turns = s.get("turns", 0)
    tools = s.get("tools", 0)
    errs = s.get("errors", 0)
    text = "\n".join(s.get("prompts") or [])

    # 语言标记优先：一场会话里「你在问为什么」比「你说了几次」更能说明它是什么
    if text and VALIDATION.search(text):
        return "校验"
    if text and LEARNING.search(text):
        return "学习"
    if turns >= ITERATION_TURNS:
        return "迭代"
    if turns <= 3 and tools >= FEEDBACK_TOOLS and errs > 0:
        return "反馈环"
    if turns >= 2:
        return "迭代"
    if turns == 1:
        # AEI 的 directive 就是「完整委派、几乎没有往返」—— 一问一答本身就属于这一类，
        # 不管它调没调工具。上一版要求 ≥8 次工具，把 38% 的会话推进了「未归类」，
        # 那不是谨慎，那是把能判的判成判不了。
        return "指派"
    # 真正判不出来的只剩：一句人话都没有的会话。如实留空。
    return "未归类"


def skills_of(s: dict) -> Counter:
    out = Counter()
    for name, n in (s.get("tool_names") or {}).items():
        for pat, skill in SKILL_MAP:
            if pat.search(name):
                out[skill] += n
                break
        else:
            out["其他"] += n
    return out


def hhi(counts) -> float | None:
    tot = sum(counts.values())
    if not tot:
        return None
    return round(sum((v / tot) ** 2 for v in counts.values()), 4)


def build(sessions: list) -> dict:
    hum = [s for s in sessions if s.get("kind") == "human"]
    n = max(1, len(hum))

    modes = Counter()
    by_topic_mode = defaultdict(Counter)
    by_week_mode = defaultdict(Counter)
    skills = Counter()
    by_topic_skill = defaultdict(Counter)
    proj_topics = defaultdict(set)
    proj_sessions = Counter()

    for s in hum:
        m = classify_mode(s)
        s["_mode"] = m
        modes[m] += 1
        for t in (s.get("topics") or []):
            by_topic_mode[t][m] += 1
        day = s.get("day") or s.get("start", "")[:10]
        if day:
            y, mo, d = (int(x) for x in day.split("-"))
            import datetime
            iy, iw, _ = datetime.date(y, mo, d).isocalendar()
            by_week_mode[f"{iy}-W{iw:02d}"][m] += 1
        sk = skills_of(s)
        skills.update(sk)
        for t in (s.get("topics") or []):
            by_topic_skill[t].update(sk)
        p = s.get("project") or "未标注"
        proj_topics[p].update(s.get("topics") or [])
        proj_sessions[p] += 1

    def group_share(c: Counter) -> dict:
        g = Counter()
        for k, v in c.items():
            g[MODES[k]["group"]] += v
        tot = sum(g.values()) or 1
        return {k: round(v / tot, 4) for k, v in g.items()}

    # 每类任务各自的自动化率 —— AEI 真正的看点
    task_rows = []
    for t, c in by_topic_mode.items():
        tot = sum(c.values())
        auto = sum(v for k, v in c.items() if MODES[k]["group"] == "自动化")
        aug = sum(v for k, v in c.items() if MODES[k]["group"] == "增强")
        denom = auto + aug
        task_rows.append({
            "task": t, "n": tot,
            "automation": round(auto / denom, 4) if denom else None,
            "augmentation": round(aug / denom, 4) if denom else None,
            "modes": dict(c),
            "skills": dict(by_topic_skill[t].most_common(5)),
            "unclassified": c.get("未归类", 0),
        })
    task_rows.sort(key=lambda r: -r["n"])

    # 深度 vs 广度：一个项目碰了多少类活（广），每类平均开了多少场（深）
    depth_rows = sorted(
        [{"project": p, "breadth": len(ts), "sessions": proj_sessions[p],
          "depth": round(proj_sessions[p] / max(1, len(ts)), 2), "topics": sorted(ts)}
         for p, ts in proj_topics.items() if proj_sessions[p] >= 3],
        key=lambda r: -r["sessions"])[:24]

    week_rows = []
    for w in sorted(by_week_mode):
        c = by_week_mode[w]
        week_rows.append({"w": w, "n": sum(c.values()), "modes": dict(c), "share": group_share(c)})

    tot_skill = sum(skills.values()) or 1
    return {
        "framework": "Anthropic Economic Index 的五种协作模式：自动化（指派／反馈环）与增强（迭代／学习／校验）。"
                     "判不出来的写「未归类」，不硬塞进任何一类。",
        "mode_defs": {k: {"group": v["group"], "desc": v["desc"]} for k, v in MODES.items()},
        "modes": dict(modes),
        "mode_share": {k: round(v / n, 4) for k, v in modes.items()},
        "group_share": group_share(modes),
        "headline": {
            "automation": group_share(modes).get("自动化", 0),
            "augmentation": group_share(modes).get("增强", 0),
            "unclassified_n": modes.get("未归类", 0),
        },
        "by_task": task_rows,
        "by_week": week_rows,
        "skills": [{"skill": k, "n": v, "share": round(v / tot_skill, 4)} for k, v in skills.most_common()],
        "skills_note": "AEI 用 O*NET 技能；本机没有那份映射，改用**工具调用**作为可观测代理 —— "
                       "读取／写入／执行／检索／联网／派生子任务／规划。这是代理指标，不是 O*NET 本身。",
        "depth_breadth": depth_rows,
        "concentration": {
            "task_hhi": hhi(Counter({r["task"]: r["n"] for r in task_rows})),
            "project_hhi": hhi(proj_sessions),
            "mode_hhi": hhi(modes),
            "note": "赫芬达尔指数：0 = 完全摊开，1 = 全压在一件事上。",
        },
        "sessions_classified": n - modes.get("未归类", 0),
        "sessions_total": n,
    }
