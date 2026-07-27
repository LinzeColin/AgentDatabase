#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""JSONL 字段一致性体检 —— 抓订正脚本留下的字段污染。

## 为什么需要它

Jesse Vincent #94：我的订正脚本里有个 `patch(obj)` 无差别地给对象设了 `candidate`，
于是**产物的 `evals/cases.jsonl` 里有 1 条带了 `candidate` 字段，另外 31 条没有**。
`quality_check.py` 忽略多余字段，三个门全绿；**它会就这么打进 ZIP 入库。**

这类污染的特征是**只影响一部分记录**——正因为不是全体，肉眼看首行看不出来。
所以判据不是「有没有这个字段」，而是「**这个字段是不是所有记录都有**」。

## 判据

对每个 JSONL 文件统计字段出现频次：
- 出现在**全部**记录里 → 正常
- 出现在**部分**记录里 → 报出来，人工确认是「合法可选字段」还是「污染」

合法可选的例子：`holdout_source_ids` 只有 known 套组的用例才有。
所以**只列不判**，但必须列——不列就等于放行。
"""
import argparse, collections, json, pathlib, sys


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path)
    ap.add_argument("--expect", nargs="*", default=[],
                    help="已知的合法可选字段，形如 cases.jsonl:holdout_source_ids")
    a = ap.parse_args()

    known = collections.defaultdict(set)
    for e in a.expect:
        fn, _, k = e.partition(":")
        known[fn].add(k)

    flagged = 0
    for f in sorted(a.workspace.rglob("*.jsonl")):
        try:
            rows = [json.loads(l) for l in f.read_text(encoding="utf-8").splitlines() if l.strip()]
        except (json.JSONDecodeError, ValueError) as e:
            print(f"  ✗ {f.name}: 解析失败 {e}")
            flagged += 1
            continue
        if not rows:
            continue
        cnt = collections.Counter(k for r in rows for k in r)
        partial = {k: v for k, v in cnt.items() if v < len(rows)}
        if partial:
            print(f"── {f.relative_to(a.workspace)}（{len(rows)} 条）")
            for k, v in sorted(partial.items(), key=lambda x: x[1]):
                tag = "已知合法" if k in known.get(f.name, set()) else "**须确认**"
                print(f"   {k}: {v}/{len(rows)}  {tag}")
                flagged += k not in known.get(f.name, set())
    print(f"\n{'✓ 无字段漂移' if not flagged else f'⚠ {flagged} 处须确认——只列不判'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
