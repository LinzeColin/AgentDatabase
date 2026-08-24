#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**交付里带齐分母了吗——不然一整类债就只能给上界。**

## 为什么有这道判据

2026-08-04 实测：想从产物侧回算「事实密度债」，
门槛是 `min_facts = max(MIN_FLOOR, ceil(usable_train / 5))`，
而 **`usable_train` 从没被写进交付产物**——`source-coverage.json` 只有 `sources_total`。

于是只能拿 total 代入，把 holdout 也算了进去：
**Livermore #100 的 536 份 → 门槛 108，荒谬。**

`quality_check` 一直在算这个数，**只是没人把它交付出去。**

**交付里缺一个分母，一整类债就只能给上界。**

## 判据

交付的 `audit/source-coverage.json` 必须带齐**下游判据回算时要用的每一个分母**。

眼下这份清单是：

| 字段 | 谁要用 | 缺了会怎样 |
|---|---|---|
| `sources_total` | 覆盖率 | — |
| **`sources_usable_train`** | **事实密度门的分母** | **只能拿 total 代入，把 holdout 算进去** |
| `sources_holdout` | holdout 重叠核查 | 不知道该有多少份被留出 |
| `primary_ratio` | 一手占比门 | — |
| `lane_source_counts` | 六条道门 | — |

## ★ 它判的是「带没带」，不是「值对不对」

值对不对由各自的门去判。**这一道只回答：将来想重新回算时，
分母还在不在产物里。**

## ★★ 为什么这件事必须在打包时管

**语料会被清掉**（分档 A–E，BCE 每轮清）。
清掉之后产物就是唯一的证据——**那时候缺的字段补不回来。**
97/100 已入库产物的装饰性引用债量不出来，正是这个道理的另一个形态。

## 它判不了什么

- **判不了这张清单本身全不全。** 将来新增一道用新分母的门，
  **要同时把那个分母加进这张清单**——否则又是一次「回算时才发现」。
- **判不了旧产物。** 已入库的 100 个都缺 `usable_train`，
  **那笔债只能等 #29 重蒸**。
"""
import argparse
import json
import pathlib
import sys

# 下游判据回算时要用的分母。**新增用新分母的门时，同时加进这里。**
REQUIRED = {
    "sources_total": "覆盖率",
    "sources_usable_train": "**事实密度门的分母**",
    "sources_holdout": "holdout 重叠核查",
    "primary_ratio": "一手占比门",
    "lane_source_counts": "六条道门",
}


def audit(doc: dict):
    """→ (缺的, 有但是 None 的)。**None 与「没有这个键」都算缺**。"""
    missing = [k for k in REQUIRED if k not in doc]
    empty = [k for k in REQUIRED if k in doc and doc[k] is None]
    return missing, empty


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    full = {k: (1 if k != "lane_source_counts" else {"writings": 1}) for k in REQUIRED}

    print("── ★ 正向：带齐了就放行 ──")
    m, e = audit(full)
    chk("五项齐全 → 不报", not m and not e)

    print("── ★★ 反向对照 ①：**缺 `usable_train` 必须被抓住**（这次的真事） ──")
    d = dict(full); d.pop("sources_usable_train")
    m, e = audit(d)
    chk("缺 sources_usable_train → 报", m == ["sources_usable_train"])

    print("── ★★ 反向对照 ②：**键在但值是 None，也算缺** ──")
    d = dict(full); d["sources_usable_train"] = None
    m, e = audit(d)
    chk("值为 None → 报（不许「有这个键就算带了」）", e == ["sources_usable_train"])

    print("── ★ 反向对照 ③：0 是合法值，不许当成缺 ──")
    d = dict(full); d["sources_holdout"] = 0
    m, e = audit(d)
    chk("holdout=0 → 不报（真的一份没留也是个数）", not m and not e)

    print("── ★ 反向对照 ④：空字典也是值，不许当成缺 ──")
    d = dict(full); d["lane_source_counts"] = {}
    m, e = audit(d)
    chk("lane_source_counts={} → 不报（该由六条道门去判）", not m and not e)

    print("── ★★ 反向对照 ⑤：**多带字段不算错** ──")
    d = dict(full); d["新加的字段"] = 42
    m, e = audit(d)
    chk("多带一个字段 → 不报", not m and not e)

    print("── ★ 反向对照 ⑥：全空的文档要报出全部五项 ──")
    m, e = audit({})
    chk("{} → 报出 5 项", len(m) == 5)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("coverage", nargs="?", type=pathlib.Path,
                    help="audit/source-coverage.json")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if not a.coverage:
        ap.error("要么 --self-test，要么给 source-coverage.json 的路径")
    if not a.coverage.is_file():
        print(f"✗ **{a.coverage} 不在——本次未检查（不是通过）**")
        return 3
    try:
        doc = json.loads(a.coverage.read_text(encoding="utf-8"))
    except ValueError as exc:
        print(f"✗ **读不了，未检查（不是通过）**：{exc}")
        return 3

    missing, empty = audit(doc)
    if not missing and not empty:
        print(f"  ✓ {len(REQUIRED)} 个分母都带上了")
        return 0
    print("✗ **交付里缺分母——将来想回算这一类，只能给上界**：\n")
    for k in missing:
        print(f"    {k:24} 缺　（{REQUIRED[k]}）")
    for k in empty:
        print(f"    {k:24} **值是 None**　（{REQUIRED[k]}）")
    print("\n  **语料会被清掉，清掉之后产物就是唯一的证据**——"
          "那时候缺的字段补不回来。\n"
          "  实测教训：`usable_train` 没被交付，回算事实密度债时只能拿 "
          "`sources_total` 代入，\n"
          "  把 holdout 也算了进去——**Livermore #100 的 536 份 → 门槛 108，荒谬。**")
    return 1


if __name__ == "__main__":
    sys.exit(main())
