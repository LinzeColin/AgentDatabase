#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第九件检查器：账本里的 split 与磁盘上的物料是否一致。

## 它补的是哪个缺口

前八件检查器的方向是：
- 七件：**产物 → 语料**（引文在不在、实体在不在、有没有残留）
- 一件：**产物 → 现算值**（我的算术对不对）

**没有一件在查「账本说的」与「磁盘上放的」是否一致。**

本轮的实际事故：换 holdout 时我只改了账本的 `split` 字段，没搬物料。结果是

    raw/ 94 份，train 也是 94 条 —— 计数完全正确
    但里面装着已成 holdout 的 three_principles，缺着已回 train 的 design_is_isms

**一进一出，数目恰好抵消。** holdout 的正文因此躺在建模者能读到的目录里，
holdout 隔离在物理上失效，而所有的门都放行。

## 判据

成员级（不是计数级）两向核对：

- `raw/` 与 `references/sources/` 的目录集合，必须**恰好等于** train 源集合
- 缺（train 有而磁盘无）与多（磁盘有而 train 无）**分别报**

只查「有没有缺」会漏掉「多了 holdout」；只查计数则一进一出全看不见。

## 为什么 holdout 那一侧是硬门

train 少一份物料只是下游工具会漏读，可以补。
**holdout 的正文出现在 raw/ 里则是隔离失效**——建模者可能已经读过它，
而 `known` 套组的全部意义就是「用没见过的材料验证」。这一侧一旦破，
这一轮的 known 分数就不可信，必须换 holdout 重来。
"""
import json, os, sys
from pathlib import Path

MATERIAL_DIRS = ("raw", "references/sources")


def check(workspace: str) -> int:
    W = Path(workspace)
    ledger = W / "evidence/source-ledger.jsonl"
    if not ledger.is_file():
        print(f"✗ 找不到账本：{ledger}")
        return 2
    rows = [json.loads(l) for l in ledger.read_text(encoding="utf-8").splitlines() if l.strip()]
    train = {r["source_id"] for r in rows if r.get("split") == "train"}
    hold = {r["source_id"] for r in rows if r.get("split") == "holdout"}
    print(f"账本：{len(rows)} 条（train {len(train)} / holdout {len(hold)}）\n")

    fatal = soft = 0
    for sub in MATERIAL_DIRS:
        d = W / sub
        if not d.is_dir():
            print(f"  ? {sub}/ 不存在——未检查，不等于通过")
            continue
        have = {x for x in os.listdir(d) if x.startswith("src-")}
        missing = sorted(train - have)          # train 有、磁盘无
        leaked = sorted(have & hold)            # 磁盘上出现了 holdout ← 致命
        extra = sorted(have - train - hold)     # 既不在 train 也不在 holdout
        status = "✓" if not (missing or leaked or extra) else "✗"
        print(f"  {status} {sub}/  {len(have)} 份"
              f" | 缺 {len(missing)} | **holdout 泄漏 {len(leaked)}** | 未知 {len(extra)}")
        for s in leaked:
            print(f"       ✗✗ holdout 正文出现在此：{s}  ← 隔离失效，本轮 known 分数不可信")
            fatal += 1
        for s in missing:
            print(f"       ✗  train 缺物料：{s}")
            soft += 1
        for s in extra:
            print(f"       ✗  账本里没有的目录：{s}")
            soft += 1

    print()
    if fatal:
        print(f"结论: 不通过（**{fatal} 处 holdout 泄漏，硬门**）")
        return 2
    if soft:
        print(f"结论: 不通过（{soft} 处成员错配）")
        return 2
    print("结论: 通过")
    return 0


SELF_TEST = [
    # (train, holdout, 磁盘集合, 应否报错, 说明)
    ({"a", "b"}, {"c"}, {"a", "b"}, False, "正常"),
    ({"a", "b"}, {"c"}, {"a", "b", "c"}, True, "holdout 泄漏（致命）"),
    ({"a", "b"}, {"c"}, {"a"}, True, "train 缺物料"),
    ({"a", "b"}, {"c"}, {"a", "c"}, True, "一进一出：**计数相等但成员错**←本轮实际事故"),
    ({"a", "b"}, {"c"}, {"a", "b", "z"}, True, "账本里没有的目录"),
]


def self_test() -> int:
    ok = 0
    for train, hold, have, should, why in SELF_TEST:
        fired = bool((train - have) or (have & hold) or (have - train - hold))
        good = fired == should
        ok += good
        print(f"  {'✓' if good else '✗'} 应报={should!s:<5} 实报={fired!s:<5} {why}")
    print(f"\n自测 {ok}/{len(SELF_TEST)}")
    return 0 if ok == len(SELF_TEST) else 2


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        sys.exit(self_test())
    if len(sys.argv) < 2:
        print("usage: check_material_split.py <workspace> | --self-test")
        sys.exit(2)
    sys.exit(check(sys.argv[1]))
