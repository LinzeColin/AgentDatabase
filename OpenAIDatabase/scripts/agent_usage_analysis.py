#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_usage_analysis.py —— 从 canonical 事件流出「我到底在用 AI 做什么」的分析

主问题不是「展示趋势」，是 Owner 2026-08-19 提的那一句：
    「三个月了，我依旧不能用它去创造实际的经济价值，去帮我赚钱。」

所以本分析的核心是一个**可证伪的假设**，用他自己的会话数据去验，而不是断言：
    H1：投入集中在建设/修复/文档，面向收入的动作占比极低。
若 H1 成立，钱漏在「做得多、上线少、变现更少」；若不成立，数据会推翻它。

时间切片按 Owner 指定的 9 档：3/7/15/30/45/60/90/180 天 + 全历史。

用法:
  python3 agent_usage_analysis.py --events <目录> [--as-of YYYY-MM-DD] [--format md]
退出码: 0=成功  1=没有可用事件
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path

SLICES = [3, 7, 15, 30, 45, 60, 90, 180]

# 把主题归三类，用来回答「钱漏在哪一步」。
# 分类依据是「这个动作离收入有多远」，不是技术难度。
LADDER = {
    "建设与维护": ["修bug", "文档", "前端界面", "测试验收", "数据", "自动化", "重构简化", "治理"],
    "交付上线": ["部署上线"],
    "面向收入": ["赚钱"],
}


def load(events_dir: Path) -> list:
    rows = []
    for f in sorted(events_dir.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            day = str(d.get("occurred_at", ""))[:10]
            if len(day) != 10 or day < "2020":
                continue          # 缺时间戳的不猜，直接丢，宁可少算不可错算
            rows.append((day, d))
    return sorted(rows, key=lambda r: r[0])   # 只按日期排；同日事件的 dict 不可比


def slice_stats(rows: list, as_of: date, days: int | None) -> dict:
    lo = (as_of - timedelta(days=days)).isoformat() if days else "0000"
    sel = [(d, e) for d, e in rows if d > lo]
    if not sel:
        return {"sessions": 0}
    daycnt = Counter(d for d, _ in sel)
    topics = Counter(t for _, e in sel for t in e.get("topics", []))
    rungs = {k: sum(topics[t] for t in v) for k, v in LADDER.items()}
    turns = sum(e["behavior_metrics"].get("user_turn_count", 0) for _, e in sel)
    tools = sum(e["behavior_metrics"].get("tool_call_count", 0) for _, e in sel)
    errs = sum(e["behavior_metrics"].get("error_mention_count", 0) for _, e in sel)
    return {
        "sessions": len(sel), "active_days": len(daycnt),
        "per_day": round(len(sel) / max(len(daycnt), 1), 1),
        "topics": topics, "rungs": rungs,
        "user_turns": turns, "tool_calls": tools, "errors": errs,
        "sources": Counter(e["source_id"] for _, e in sel),
    }


def render(rows: list, as_of: date) -> str:
    out = ["# 我在用 AI 做什么 —— 基于本机全部 agent 会话", "",
           f"数据：{rows[0][0]} … {rows[-1][0]}，共 **{len(rows)}** 个会话，"
           f"活跃 **{len(set(d for d, _ in rows))}** 天。截止 {as_of}。", ""]

    out += ["## 一、九档时间切片", "",
            "| 切片 | 会话 | 活跃天 | 日均 | 我的发言 | 工具调用 | 报错提及 |",
            "|---|---|---|---|---|---|---|"]
    for d in SLICES + [None]:
        s = slice_stats(rows, as_of, d)
        if not s["sessions"]:
            continue
        name = f"最近 {d} 天" if d else "全历史"
        out.append(f"| {name} | {s['sessions']} | {s['active_days']} | {s['per_day']} | "
                   f"{s['user_turns']} | {s['tool_calls']} | {s['errors']} |")

    full = slice_stats(rows, as_of, None)
    out += ["", "## 二、主题分布（一个会话可含多个主题）", "",
            "| 主题 | 会话数 | 占比 |", "|---|---|---|"]
    for t, c in full["topics"].most_common():
        out.append(f"| {t} | {c} | {c * 100 // full['sessions']}% |")

    out += ["", "## 三、钱漏在哪一步", "",
            "把主题按「离收入有多远」归三档：", "",
            "| 阶梯 | 命中会话 | 占比 |", "|---|---|---|"]
    for k, v in full["rungs"].items():
        out.append(f"| {k} | {v} | {v * 100 // max(sum(full['rungs'].values()), 1)}% |")

    build = full["rungs"]["建设与维护"]
    ship = full["rungs"]["交付上线"]
    money = full["rungs"]["面向收入"]
    out += ["", f"**建设 : 上线 : 收入 = {build} : {ship} : {money}"
                f"（约 {build // max(money, 1)} : {ship // max(money, 1)} : 1）**", ""]

    out += ["## 四、主题趋势（各切片内占比，看什么在升什么在死）", "",
            "| 主题 | 3天 | 7天 | 15天 | 30天 | 全历史 |", "|---|---|---|---|---|---|"]
    cols = [3, 7, 15, 30, None]
    stats = {d: slice_stats(rows, as_of, d) for d in cols}
    for t, _ in full["topics"].most_common():
        cells = []
        for d in cols:
            s = stats[d]
            cells.append(f"{s['topics'][t] * 100 // s['sessions']}%" if s["sessions"] else "-")
        out.append(f"| {t} | " + " | ".join(cells) + " |")

    out += ["", "## 五、工具分布", "",
            "| 来源 | 会话 | 占比 |", "|---|---|---|"]
    for s_, c in full["sources"].most_common():
        out.append(f"| {s_} | {c} | {c * 100 // full['sessions']}% |")

    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--as-of", default=None)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    rows = load(Path(args.events))
    if not rows:
        print("FAIL: 没有可用事件")
        return 1
    as_of = date.fromisoformat(args.as_of) if args.as_of else date.fromisoformat(rows[-1][0])
    body = render(rows, as_of)
    if args.out:
        Path(args.out).write_text(body, encoding="utf-8")
        print(f"已写入 {args.out}（{len(body)} 字符）")
    else:
        print(body)
    return 0


if __name__ == "__main__":
    sys.exit(main())
