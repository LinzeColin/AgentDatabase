#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_lessons_build.py —— 从会话事件提炼「给后续 agent 看的经验」

目标是降低后续 agent 的开发阻碍与 token 消耗，所以有两条硬约束：

1. **有上限**（默认 ≤200 条 / ≤8KB）。它会被每个 session 读；超了就是新的
   token 负担，不是减负。这和 kit 的 check_doc_budget 是同一个道理。
2. **每条带出处**（会话 id + 日期）。没出处的「经验」一个月后没人敢信，
   会变成又一份没人读的文档 —— 本仓的 AGENT_CONTEXT.md 就是活教训：
   产出了，但 9 个仓里 8 个的 AGENTS.md 没指向它，全局 CLAUDE.md 一字未提。

零 agent 零 token：纯正则与统计，运行期不调模型。
提炼的是**信号**不是**结论**——脚本不会假装自己懂业务，只把高频/高痛的
模式排出来，让人和 agent 自己判断。

用法:
  python3 agent_lessons_build.py --events <目录> --out <文件> [--max-items 200]
退出码: 0=成功  1=无事件
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# 纠偏信号：用户说这些词，说明上一步 agent 做错了。
# 这是整份沉淀里最值钱的部分 —— 它记录的是「本工作间特有的错法」。
CORRECTION = re.compile(
    r"(不对|错了|不是这个|我要的是|重来|回滚|revert|撤销|你没有|漏了|遗漏|"
    r"别再|不要再|又犯|再一次|第二次|说过了)")
# 痛点信号
PAIN = re.compile(r"(卡住|卡了|一直|反复|又|还是不行|依旧|仍然|老是|总是)")
# 决定信号
DECIDE = re.compile(r"(定了|就这样|按这个|采用|决定|以后都|一律|永远|禁止|必须)")


def load(d: Path) -> list:
    rows = []
    for f in sorted(d.glob("*.events.jsonl")):
        for line in f.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.strip():
                try:
                    rows.append(json.loads(line))
                except ValueError:
                    continue
    return rows


def sentences(text: str) -> list:
    return [s.strip() for s in re.split(r"[。；\n!?！？]+", text) if 8 <= len(s.strip()) <= 120]


def build(rows: list, max_items: int, max_bytes: int) -> str:
    corr, pain, dec = [], [], []
    topic_pain = Counter()
    for e in rows:
        day = str(e.get("occurred_at", ""))[:10]
        rid = e.get("record_id", "?")
        for s in sentences(e.get("summary", "")):
            if CORRECTION.search(s):
                corr.append((day, rid, s))
            elif DECIDE.search(s):
                dec.append((day, rid, s))
            elif PAIN.search(s):
                pain.append((day, rid, s))
        if e["behavior_metrics"].get("error_mention_count", 0) > 30:
            for t in e.get("topics", []):
                topic_pain[t] += 1

    def dedupe(items):
        seen, out = set(), []
        for day, rid, s in sorted(items, key=lambda x: x[0], reverse=True):
            k = re.sub(r"[^\w一-鿿]", "", s)[:24]
            if k and k not in seen:
                seen.add(k)
                out.append((day, rid, s))
        return out

    corr, pain, dec = dedupe(corr), dedupe(pain), dedupe(dec)
    quota = max(max_items // 3, 1)
    out = ["<!-- 本文件由 OpenAIDatabase/scripts/agent_lessons_build.py 生成。请勿手写。 -->",
           "", "# 本工作间的既有教训（给 agent 看）", "",
           f"来自 {len(rows)} 个真实会话。**每条带出处**，不可追溯的不收。",
           "有上限，因为它每个 session 都要被读一遍。", ""]

    out += ["## 一、高痛主题（报错提及 >30 次的会话里，什么主题最常出现）", ""]
    for t, c in topic_pain.most_common(8):
        out.append(f"- **{t}** —— {c} 个高报错会话")

    for title, items, note in (
        ("二、我被纠偏的地方（Owner 说「不对/错了/漏了」）", corr,
         "这些是本工作间特有的错法，不是通用最佳实践能覆盖的。"),
        ("三、拍过的板", dec, "说过「一律/必须/禁止/以后都」的，按定论处理。"),
        ("四、反复卡住的地方", pain, "出现「又/还是/一直/反复」，说明前一次没修根因。"),
    ):
        out += ["", f"## {title}", "", f"> {note}", ""]
        for day, rid, s in items[:quota]:
            out.append(f"- {s}  <sub>`{day} {rid}`</sub>")

    body = "\n".join(out) + "\n"
    if len(body.encode("utf-8")) > max_bytes:
        # 超预算就砍，不是调大上限 —— 和 check_doc_budget 同一立场
        keep = []
        size = 0
        for line in body.splitlines(True):
            size += len(line.encode("utf-8"))
            if size > max_bytes - 120:
                keep.append(f"\n> ⚠️ 已达 {max_bytes} 字节预算上限，其余条目未展示。"
                            f"要看更多请精简高频重复项，**不要调大上限**。\n")
                break
            keep.append(line)
        body = "".join(keep)
    return body


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--events", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--max-items", type=int, default=200)
    ap.add_argument("--max-bytes", type=int, default=8192)
    args = ap.parse_args()
    rows = load(Path(args.events))
    if not rows:
        print("FAIL: 无事件")
        return 1
    body = build(rows, args.max_items, args.max_bytes)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(body, encoding="utf-8")
    n = len(body.encode("utf-8"))
    print(f"已写入 {args.out}  {n} 字节 / 上限 {args.max_bytes}"
          f"  ≈{n // 4} tokens")
    return 0


if __name__ == "__main__":
    sys.exit(main())
