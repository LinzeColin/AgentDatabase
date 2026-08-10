#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】十份渲染文档。每人复制一份，只改 M（映射）与 DOCS（正文）。

## claim → 文档的映射必须从 claims.jsonl 派生，不许硬编码顺序

Vincent 一轮我在生成器里手写了一个 `_ORDER` 列表，后来往 claims.jsonl 中间插了一条，
列表没跟着改，**所有后续 claim 的锚点整体错位一格**。
官方门只查计数与孤儿——计数没变、也没有孤儿，门全绿。是评委逐条比对才发现的。

所以映射键用 **category + 关键词**，从实际 claims.jsonl 读出来匹配：
插入新 claim 不会导致错位；匹配不上的**在生成时报错**，而不是静默漏掉。

## 十份文档
persona / facts / capabilities / boundaries / decision-policy /
cognitive-os / strategy / work / divergence-map / hypotheses
每份 ≥500 字；每条 claim 至少被渲染一次，不得有孤儿、不得有幽灵锚点。
"""
import collections, json, pathlib, re, sys

W = pathlib.Path(__file__).resolve().parent / "ws-XXXX/XXXX"          # ← 改
CL = [json.loads(l) for l in (W / "evidence/claims.jsonl").read_text(encoding="utf-8").splitlines()]


def find(cat, kw):
    hits = [c for c in CL if c["category"] == cat and kw in c["applicability"][0]]
    if len(hits) != 1:
        raise SystemExit(f"✗ 映射不唯一：({cat}, {kw}) 命中 {len(hits)} 条 —— "
                         f"claims.jsonl 改过就必须同步改这里，不能靠位置")
    return hits[0]["claim_id"]


M = {k: find(*v) for k, v in {}.items()}      # ← 每人填 别名 → (category, 关键词)


def a(k):
    return f"<!-- claim:{M[k]} -->"


DOCS = {}                                     # ← 每人填 文件名 → 正文


def main() -> int:
    used = collections.Counter()
    for name, text in DOCS.items():
        (W / name).write_text(text, encoding="utf-8")
        for cid in re.findall(r"<!-- claim:(clm-[0-9a-f]{12}) -->", text):
            used[cid] += 1
        print(f"  ✓ {name:<22} {len(text):>6} 字")
    ids = {c["claim_id"] for c in CL}
    orphan, ghost = sorted(ids - set(used)), sorted(set(used) - ids)
    short = [n for n, t in DOCS.items() if len(t) < 500]
    bad = False
    for label, items in (("孤儿 claim", orphan), ("幽灵锚点", ghost), ("文档过短", short)):
        if items:
            print(f"\n✗ {label} {len(items)}: {items[:6]}")
            bad = True
    if bad:
        return 2
    print(f"\n✓ {len(DOCS)} 份文档；{len(ids)} 条 claim 全部有锚点，无孤儿、无幽灵")
    return 0


if __name__ == "__main__":
    sys.exit(main())
