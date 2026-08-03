#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这个数是 0% 或 100%——先去核工具，别先去信它。**

## 为什么有这道判据

2026-08-04 一天之内，同一形状的错犯了三次：

| 何时 | 错法 | 当时看到的数 |
|---|---|---|
| v0.0.0.71 | `roster()` 报工作区、`scan()` 报容器——**两套标识符空间相减** | 「**少扫 11 个**」（而 15 = 15） |
| #15 范围统计 | `charles-becht-iv` 的 `iv` 是 `l-iv-ermore` 的子串 | 4 人（真值 3） |
| 锚点全量审计 | **只读外层 zip，核心产物在嵌套 zip 里** | 「**98/100 零锚点**」（真值 4/100） |

**共同点：拿到一个看起来完整的数，而它答的是另一个问题。**
而且三次里两次的结论是**极端值**——「一片绿」或「一片红」。

再往前还有四次「判据绿了却指错了文件」，**表征全是一片绿**。

## 判据

一次扫描的结果落在 **0%／100%** 这两端时，**先报可疑，而不是先报结论**。

它不否定那个数——**0% 与 100% 当然可能是真的**。
它要求的是：**在把这个数写进任何册子之前，先说清工具的射程对不对。**

## ★★ 方向：它只在极端值上说话

中间值一律不管。**一个 43% 不值得怀疑工具**——
射程写错时你几乎总会得到 0% 或 100%，
**因为「一个都没看见」和「看见的都一样」正是射程为空／射程错位的表征。**

## ★★ 它抓得住三次里的两次，第三次归别人管

**诚实地记下射程：**

| 那次的错 | 当时的数 | 这道判据 |
|---|---|---|
| 首创声明第一版 | 0 处 / 10 人 | **抓得住**（命中为 0） |
| 锚点全量审计 | 98/100 单位内部为空 | **抓得住**（逐个单位都空） |
| 语料射程 collapse | 1 个工作区 / 1 | **抓不住**——它不是比例，是**扫过的单位数与名册对不上**，
  那归 `check_scan_reach` 管 |

**一道判据抓不住的那一类，要写清楚归谁管，而不是含糊过去。**

## 它判不了什么

- **判不了那个数到底对不对。** 它只举手，不裁决。
- **判不了非比例型的结论**（如「均分 0.7925」）。
  那类由 `check_suite_single_drag` 一类的判据管。
- **不是门。** 它是提示，且必须能被一句「已核过射程：<怎么核的>」关掉——
  否则它会变成一个逼人把真实的 100% 改写成别的东西的机器。
"""
import argparse
import json
import pathlib
import sys

RULES = [
    ("命中数为 0",
     lambda hit, tot: tot > 0 and hit == 0,
     "**「一个都没看见」正是射程为空的表征**——先确认扫的是不是该扫的东西"),
    ("命中数 = 全体",
     lambda hit, tot: tot > 0 and hit == tot and tot >= 3,
     "**「看见的都一样」正是射程错位的表征**——先确认单位切得对不对"),
]


# ★★ 第三条规则，为锚点审计那次补的。
#   那次的真实信号**不是比例极端**（98/100 既不是 0 也不是全体），
#   而是「**100 个单位里有 98 个单位内部命中为 0**」——
#   即**逐个单位都空**。这正是「每个单位里都没打开该打开的东西」的表征。
ZERO_UNIT_RATIO = 0.80
MIN_UNITS = 5


def suspect(hit: int, total: int, verified: str = "",
            zero_units: int = None, units: int = None):
    """→ [(规则名, 说明)]；`verified` 非空即视为已核过射程，直接放行。"""
    if verified.strip():
        return []
    out = [(name, why) for name, pred, why in RULES if pred(hit, total)]
    if (units and units >= MIN_UNITS and zero_units is not None
            and zero_units / units >= ZERO_UNIT_RATIO):
        out.append((
            f"{zero_units}/{units} 个单位内部命中为 0",
            "**逐个单位都空**——先确认每个单位里该打开的东西打开了没有"
            "（锚点审计那次：核心产物在**嵌套 zip** 里，只读了外层）"))
    return out


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★ 正向：0/100 要举手（锚点审计那次的真实数字） ──")
    s = suspect(0, 100)
    print(f"    {s[0][1] if s else '—'}")
    chk("命中 0 / 全体 100 → 报可疑", len(s) == 1)

    print("── ★ 正向：100/100 也要举手 ──")
    chk("命中 = 全体 → 报可疑", len(suspect(100, 100)) == 1)

    print("── ★★ 反向对照 ①：**中间值一律不管** ──")
    chk("43/100 → 不报", not suspect(43, 100))
    chk("1/100 → 不报（不是 0，就不是极端）", not suspect(1, 100))
    chk("99/100 → 不报", not suspect(99, 100))

    print("── ★★ 反向对照 ②：**样本太小时「全中」不算极端** ──")
    chk("2/2 → 不报（两个全中太常见）", not suspect(2, 2))
    chk("3/3 → 报（到 3 个才开始说话）", len(suspect(3, 3)) == 1)

    print("── ★★ 反向对照 ③：**空集合不许被当成「命中 0」** ──")
    chk("0/0 → 不报（没有全体，谈不上比例）", not suspect(0, 0))

    print("── ★★ 反向对照 ④：**核过射程就必须能关掉它** ──")
    s = suspect(0, 100, verified="已递归进嵌套 zip，逐个确认 runtime/*.zip 被打开")
    chk("给了核验说明 → 不报", not s)
    chk("空白说明关不掉", len(suspect(0, 100, verified="   ")) == 1)

    print("── ★★ 反向对照 ⑥：**逐个单位都空要举手**（锚点审计那次） ──")
    s = suspect(98, 100, zero_units=98, units=100)
    names = [n for n, _ in s]
    print(f"    {s[-1][1][:52] if s else '—'}")
    chk("98/100 个单位内部命中 0 → 报（虽然 98/100 不是比例极端）",
        any("单位内部命中为 0" in n for n in names))

    print("── ★★ 反向对照 ⑦：**修好之后的真值不许再报** ──")
    chk("0 个单位为空（100 个都有锚点）→ 不报",
        not suspect(4, 100, zero_units=0, units=100))

    print("── ★★ 反向对照 ⑧：**单位数太少不说话** ──")
    chk("3/3 个单位为空但只有 3 个单位 → 这条规则不报",
        not any("单位内部命中为 0" in n
                for n, _ in suspect(1, 9, zero_units=3, units=3)))

    print("── ★ 反向对照 ⑨：**没给单位数时这条规则一律不动** ──")
    chk("只给 hit/total → 只有原来两条规则", len(suspect(0, 100)) == 1)

    print("── ★ 反向对照 ⑤：**它不改任何数** ──")
    before = (0, 100)
    suspect(*before)
    chk("调用前后输入不变", before == (0, 100))

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--hit", type=int, help="命中／异常的单位数")
    ap.add_argument("--total", type=int, help="扫过的单位总数")
    ap.add_argument("--zero-units", type=int, help="内部命中为 0 的单位数")
    ap.add_argument("--units", type=int, help="单位总数")
    ap.add_argument("--verified", default="",
                    help="已核过射程的话，写清**怎么核的**；写了就放行")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return selftest()
    if a.hit is None or a.total is None:
        ap.error("要么 --self-test，要么给 --hit 与 --total")

    s = suspect(a.hit, a.total, a.verified, a.zero_units, a.units)
    pct = (a.hit / a.total * 100) if a.total else 0
    print(f"命中 **{a.hit}** / 全体 **{a.total}**（{pct:.0f}%）\n")
    if not s:
        if a.verified.strip():
            print(f"  ✓ 已核过射程：{a.verified}")
        else:
            print("  ✓ 不是极端值——这道判据不说话")
        return 0
    for name, why in s:
        print(f"⚠ **{name}**\n    {why}")
    print("\n  **它不否定这个数**——0% 与 100% 当然可能是真的。\n"
          "  它要求的是：**写进册子之前，先说清工具的射程对不对。**\n"
          "  核过了就用 `--verified '<怎么核的>'` 关掉它。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
