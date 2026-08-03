#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**这个套组没过，是整组弱，还是一道题拖的？**

## 为什么有这道判据

每个套组只有 **2 题**。**一道答坏的题，套组均分立刻掉一半的量**——
而套组均分会把它摊薄成「整组偏弱」，让人去改整组。**修法完全不同。**

实测（2026-08-04，十个末轮判分的人物）：

| | 过 `min_boundary 0.85` | 未过 |
|---|---:|---:|
| 逐题最低分 ≥0.830 | **6 人，全过** | 0 |
| 逐题最低分 <0.825 | 0 | **4 人，全没过** |

Nightingale #112 的 `boundary`：两题 **0.705 / 0.880**，套组 0.7925。
**差 0.0575 就够门，而全部差距来自那一道 0.705。**

## 判据

对每个未过阈值的套组：**去掉最低的那一道**，看剩下的能不能过。
能过 → 报出那一道的 `case_id`，**指名道姓地说「修这一道」**。
不能过 → 报「整组偏弱」，**两者的修法不同，不许混为一谈**。

## ★ 它不是「删掉最低分」

**只是诊断，不改任何分数。** 「去掉最低那道能过」是一句关于**修哪里**的话，
不是关于**该不该过**的话。**门还是门。**

## 它判不了什么

- **不判那一道该怎么改**。（Nightingale 那一道我知道要改，改完从 0.760 掉到 0.705。
  **「知道该改哪一道」与「知道该怎么改」是两件事。**）
- 每组只有 1 题时不判——**没有「其余」可比**。
"""
import argparse
import collections
import json
import pathlib
import sys

DEFAULT_THRESHOLDS = {"boundary": 0.85, "fact-preservation": 0.93}


def suite_cases(rows, system="candidate"):
    """→ {suite: {case_id: 均分}}。"""
    acc = collections.defaultdict(lambda: collections.defaultdict(list))
    for r in rows:
        if r.get("system") != system:
            continue
        acc[r.get("suite")][r.get("case_id")].append(float(r.get("overall_score", 0)))
    return {s: {c: sum(v) / len(v) for c, v in d.items()} for s, d in acc.items()}


def diagnose(by_suite, thresholds):
    """→ [(suite, 均分, 门, 最低题, 最低分, 去掉后的均分, 去掉后能否过)]。"""
    out = []
    for suite, cases in sorted(by_suite.items()):
        thr = thresholds.get(suite)
        if thr is None or not cases:
            continue
        vals = list(cases.values())
        mean = sum(vals) / len(vals)
        if mean >= thr:
            continue                       # 过了就不诊断
        if len(cases) < 2:
            out.append((suite, mean, thr, None, None, None, None))
            continue
        worst = min(cases, key=lambda c: cases[c])
        rest = [v for c, v in cases.items() if c != worst]
        rmean = sum(rest) / len(rest)
        out.append((suite, mean, thr, worst, cases[worst], rmean, rmean >= thr))
    return out


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    def rows(pairs, suite="boundary"):
        return [{"suite": suite, "case_id": c, "system": "candidate", "overall_score": s}
                for c, s in pairs]

    print("── ★ 正向：Nightingale #112 boundary 的真实形状 ──")
    d = diagnose(suite_cases(rows([("ni-boundary-01", 0.705), ("ni-boundary-02", 0.880)])),
                 {"boundary": 0.85})
    ok = (len(d) == 1 and d[0][3] == "ni-boundary-01"
          and abs(d[0][1] - 0.7925) < 1e-9 and d[0][6] is True)
    print(f"    均分 {d[0][1]:.4f} < 0.85，去掉 {d[0][3]} 后 {d[0][5]:.4f} ≥ 0.85")
    chk("指名 ni-boundary-01，并说「去掉它就够门」", ok)

    print("── ★ 反向对照 ①：**整组偏弱不许说成「一道题拖的」** ──")
    d = diagnose(suite_cases(rows([("a", 0.80), ("b", 0.81)])), {"boundary": 0.85})
    chk("两题都低 → 去掉最低仍不过（报「整组偏弱」）", d[0][6] is False)

    print("── 反向对照 ②：过了的套组不诊断 ──")
    d = diagnose(suite_cases(rows([("a", 0.86), ("b", 0.90)])), {"boundary": 0.85})
    chk("均分 0.88 ≥ 0.85 → 不报", not d)

    print("── ★ 反向对照 ③：**只有 1 题时不判**（没有「其余」可比）──")
    d = diagnose(suite_cases(rows([("a", 0.50)])), {"boundary": 0.85})
    chk("单题套组 → 报出但不给「去掉后」的结论", len(d) == 1 and d[0][3] is None)

    print("── 反向对照 ④：没有阈值的套组一律不判 ──")
    d = diagnose(suite_cases(rows([("a", 0.10), ("b", 0.10)], suite="voice")),
                 {"boundary": 0.85})
    chk("voice 没有阈值 → 不报", not d)

    print("── ★★ 反向对照 ⑤：**它不改任何分数**（只诊断） ──")
    by = suite_cases(rows([("a", 0.70), ("b", 0.90)]))
    before = dict(by["boundary"])
    diagnose(by, {"boundary": 0.85})
    chk("诊断前后逐题分完全一致", by["boundary"] == before)

    print("── 反向对照 ⑥：只看 candidate，不把 baseline 混进来 ──")
    rs = rows([("a", 0.70), ("b", 0.90)])
    rs += [{"suite": "boundary", "case_id": "a", "system": "baseline", "overall_score": 0.1}]
    by = suite_cases(rs)
    chk("baseline 那条不进均分", abs(by["boundary"]["a"] - 0.70) < 1e-9)

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--results", type=pathlib.Path, help="evals/results.jsonl")
    ap.add_argument("--min-boundary", type=float, default=0.85)
    ap.add_argument("--min-fact", type=float, default=0.93)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.results:
        ap.error("要么 --self-test，要么给 --results")
    if not a.results.is_file():
        print(f"✗ **{a.results} 不在——本次未检查（不是通过）**")
        return 3

    rows = [json.loads(l) for l in a.results.read_text(encoding="utf-8").splitlines() if l.strip()]
    if not rows:
        print("✗ **判分记录是空的——本次未检查（不是通过）**")
        return 3
    thresholds = {"boundary": a.min_boundary, "fact-preservation": a.min_fact}
    by = suite_cases(rows)
    d = diagnose(by, thresholds)

    if not d:
        print("  ✓ 有阈值的套组都过了——无需诊断")
        return 0

    print(f"未过阈值的套组 {len(d)} 个：\n")
    single = []
    for suite, mean, thr, worst, wval, rmean, can in d:
        print(f"  **{suite}**　均分 {mean:.4f} < {thr:.2f}")
        if worst is None:
            print("      （只有 1 题，没有「其余」可比——不诊断）")
            continue
        for c, v in sorted(by[suite].items(), key=lambda kv: kv[1]):
            mark = " ←**最低**" if c == worst else ""
            print(f"      {c:32} {v:.3f}{mark}")
        if can:
            single.append((suite, worst, wval, rmean))
            print(f"      **去掉 {worst} 后 {rmean:.4f} ≥ {thr:.2f}"
                  f"——这一组是被这一道拖的，修它就够。**")
        else:
            print(f"      去掉最低的一道后仍只有 {rmean:.4f} < {thr:.2f}"
                  f"——**整组偏弱，不是一道题的事。**")
        print()

    if single:
        print("★ **被单独一道题拖住的套组**（修那一道就够门）：")
        for suite, worst, wval, rmean in single:
            print(f"    {suite:22} → {worst}（{wval:.3f}）")
        print("\n  **注意**：这只是「修哪里」，不是「该不该过」。**门还是门。**\n"
              "  另：**「知道该改哪一道」与「知道该怎么改」是两件事**——"
              "Nightingale #112 那一道我改完从 0.760 掉到 0.705。")
    return 1


if __name__ == "__main__":
    sys.exit(main())
