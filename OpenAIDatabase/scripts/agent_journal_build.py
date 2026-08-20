#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_journal_build.py —— 从 canonical 事件流出日记 / 日历 / 时间线

三者不是三份数据，是同一份事件流的三个视图：
    日记   按天聚合：这天做了什么、卡在哪、开了几个会话
    日历   热力图：哪天忙、忙什么主题
    时间线 项目泳道：同时并行着几条线

零 agent 零 token：纯统计与字符串拼接，运行期不调任何模型。

用法:
  python3 agent_journal_build.py --events <目录> --out <目录>
退出码: 0=成功  1=无事件
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from datetime import date, timedelta
from pathlib import Path

BLOCK = " ▁▂▃▄▅▆▇█"          # 热力图字符，0..8 级


def load(d: Path) -> list:
    rows = []
    for f in sorted(d.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if not line.strip():
                continue
            try:
                e = json.loads(line)
            except ValueError:
                continue
            day = str(e.get("occurred_at", ""))[:10]
            if len(day) == 10 and day >= "2020":
                rows.append((day, e))
    return sorted(rows, key=lambda r: r[0])


def build_journal(rows: list) -> str:
    byday = defaultdict(list)
    for d, e in rows:
        byday[d].append(e)
    out = ["# 日记 —— 每天做了什么", "",
           "由 `agent_journal_build.py` 从会话事件生成。请勿手写。", ""]
    for d in sorted(byday, reverse=True):
        evs = byday[d]
        topics = Counter(t for e in evs for t in e.get("topics", []))
        turns = sum(e["behavior_metrics"].get("user_turn_count", 0) for e in evs)
        errs = sum(e["behavior_metrics"].get("error_mention_count", 0) for e in evs)
        srcs = Counter(e["source_id"] for e in evs)
        titles = [e["title"] for e in evs if e.get("title") and not e["title"].endswith("会话")]
        out += [f"## {d}", "",
                f"- **{len(evs)} 个会话**，我说了 {turns} 次，报错提及 {errs} 次",
                f"- 工具：" + "、".join(f"{k} {v}" for k, v in srcs.most_common()),
                f"- 主题：" + ("、".join(f"{k}({v})" for k, v in topics.most_common(5)) or "未识别")]
        if titles:
            out.append("- 那天开头几句：")
            for t in titles[:3]:
                out.append(f"  - {t[:100]}")
        out.append("")
    return "\n".join(out)


def build_calendar(rows: list) -> str:
    byday = Counter(d for d, _ in rows)
    if not byday:
        return "# 日历\n\n无数据。\n"
    lo, hi = date.fromisoformat(min(byday)), date.fromisoformat(max(byday))
    peak = max(byday.values())
    out = ["# 日历 —— 哪天忙", "",
           f"{lo} … {hi}，峰值 {peak} 会话/天。字符越满越忙。", "",
           "```"]
    # 按周排：每行一周，周一起
    cur = lo - timedelta(days=lo.weekday())
    while cur <= hi:
        cells = []
        for i in range(7):
            d = (cur + timedelta(days=i)).isoformat()
            n = byday.get(d, 0)
            lvl = 0 if n == 0 else min(8, 1 + int(n * 7 / max(peak, 1)))
            cells.append(BLOCK[lvl])
        wk = sum(byday.get((cur + timedelta(days=i)).isoformat(), 0) for i in range(7))
        out.append(f"{cur.isoformat()}  {''.join(cells)}  共 {wk}")
        cur += timedelta(days=7)
    out += ["```", "", "（一格一天，周一起。每周一行。）", ""]
    return "\n".join(out)


def build_timeline(rows: list) -> str:
    """项目泳道：每个项目从第一次到最后一次出现，看并行了多少条线。"""
    span = defaultdict(lambda: [None, None, 0])
    for d, e in rows:
        for p in e.get("project_refs", []) or ["(未标注)"]:
            s = span[p]
            s[0] = d if s[0] is None else min(s[0], d)
            s[1] = d if s[1] is None else max(s[1], d)
            s[2] += 1
    if not span:
        return "# 时间线\n\n无数据。\n"
    lo = min(v[0] for v in span.values())
    hi = max(v[1] for v in span.values())
    total = (date.fromisoformat(hi) - date.fromisoformat(lo)).days + 1
    W = 48
    out = ["# 时间线 —— 项目泳道", "",
           f"{lo} … {hi}（{total} 天）。每条是一个项目的存活期。", "",
           "| 项目 | 起 | 止 | 天 | 会话 | 泳道 |", "|---|---|---|---|---|---|"]
    for p, (s, e_, n) in sorted(span.items(), key=lambda kv: -kv[1][2])[:25]:
        a = (date.fromisoformat(s) - date.fromisoformat(lo)).days
        b = (date.fromisoformat(e_) - date.fromisoformat(lo)).days
        x0 = int(a * W / max(total, 1))
        x1 = max(x0 + 1, int((b + 1) * W / max(total, 1)))
        bar = " " * x0 + "█" * (x1 - x0) + " " * (W - x1)
        days = (date.fromisoformat(e_) - date.fromisoformat(s)).days + 1
        out.append(f"| `{p[:34]}` | {s[5:]} | {e_[5:]} | {days} | {n} | `{bar}` |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = load(Path(args.events))
    if not rows:
        print("FAIL: 无事件")
        return 1
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    for name, body in (("日记.md", build_journal(rows)),
                       ("日历.md", build_calendar(rows)),
                       ("时间线.md", build_timeline(rows))):
        (out / name).write_text(body, encoding="utf-8")
        print(f"  {name}  {len(body)} 字符")
    return 0


if __name__ == "__main__":
    sys.exit(main())
