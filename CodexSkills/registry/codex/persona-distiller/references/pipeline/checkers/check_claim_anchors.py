#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""claim 标记锚点体检：文段与它标注的断言，谈的是不是同一件事。

## 为什么官方门看不见这个

官方门查两件事：**每条断言都被渲染了吗**、**有没有孤儿标记**。
两条都是**计数**层面的——而 claim 标记错挂**不改变任何计数**。

Jesse Vincent #94 实测：三个标记发生了**循环错位**（A 段标了 B 的号、
B 段标了 C 的号、C 段标了 A 的号）。数量对得上、无孤儿、每条断言都被渲染，
**三个门全绿**。后果是读者顺着标记去查证据，会落到另一条断言上——
**引用链断了，而且断得看不出来。**

## 判据

取标记前约 450 字作为「被标注的文段」，与断言正文求关键词重合
（英文实体 ≥5 字符、中文 4–8 字串）。重合 < 2 即报出。

## 已知误报：中文文段 + 英文引文断言

断言正文常常主体是英文引文，而渲染文段是中文转述，**字面重合天然为 0**。
Vincent 那轮 4 处命中里有 1 处是这种情况
（中文「五个月内发生过一次实质推翻」↔ 英文「Over the past 5 months」）。

**所以只列不判。** 它的价值不在于自动判错，在于**把 33 个标记压缩成 3–4 个要看的**。
"""
import argparse, json, pathlib, re, sys

EN = re.compile(r"[A-Za-z][A-Za-z0-9./\-]{4,}")
CN = re.compile(r"[一-鿿]{4,8}")
WIN = 450
MIN_OVERLAP = 2


def keys(s: str) -> set:
    return {k.lower() for k in EN.findall(s)} | set(CN.findall(s))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path)
    a = ap.parse_args()

    cl = a.workspace / "evidence" / "claims.jsonl"
    claims = {}
    for line in cl.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            claims[r["claim_id"]] = r["claim"]

    total, flagged = 0, []
    for f in sorted(a.workspace.rglob("*.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        for m in re.finditer(r"<!-- claim:(clm-[0-9a-f]+) -->", t):
            total += 1
            cid = m.group(1)
            if cid not in claims:
                flagged.append((f.name, cid, "断言不存在", ""))
                continue
            seg = t[max(0, m.start() - WIN):m.start()]
            ov = keys(seg) & keys(claims[cid])
            if len(ov) < MIN_OVERLAP:
                flagged.append((f.name, cid, f"重合 {len(ov)}", claims[cid][:70]))

    print(f"claim 标记 {total} 个，须人工看 {len(flagged)} 个")
    for fn, cid, why, txt in flagged:
        print(f"  ⚠ {fn} {cid}（{why}）\n      {txt}")
    print("\n✓ 全部对上" if not flagged
          else "\n⚠ 只列不判——中文文段配英文引文断言会天然重合为 0，逐条人工确认")
    return 0


if __name__ == "__main__":
    sys.exit(main())
