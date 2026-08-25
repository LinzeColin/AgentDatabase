#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""三轮盲判是不是三次**独立**的盲判——查 A/B 分配有没有跨轮重新随机。

## 实测（2026-08-04，全量）

```
9 人 × 32 题 × 3 轮，（人物, 题）组合 **290 个全部在 ≥2 轮里出现**
其中跨轮换过边的：**0 个**
```

**每一道题的候选侧从第一轮固定到第三轮，一次都没重新随机过。**

★★ **这不是疏漏，是有意的设计。** `build_blind_payload.py` 里写着：

> `# 轮次之间 A/B 映射必须一致，否则各轮不可比`

而且有一道**硬门**在拦：映射与第 1 轮不一致就中止（`return 3`）。
分配是 `sha256(case_id) % 2`，**与轮次无关**，正是为了满足那道门。

**所以本判据不是在报 bug，是在把这个设计的代价写出来**——
那句注释只写了收益（各轮可比），没写代价。

## 为什么这要紧

它本身**不是泄题**——评委仍然不知道哪边是候选。
但它让**三轮不是三次独立的复现**：

- 已实测两席能靠**格式**认出候选侧（Barton 100%、四人合计 116/128 = 91%）
- 也能靠**长度**认出（席 D：「长的一侧在 32/32 全部命中同一个系统」）
- **一旦在第 1 轮认出某道题的候选在 A 侧，这个认定在第 2、3 轮原样有效**

所以「三轮 delta 逐轮向零」这类跨轮趋势，**不能当作三个独立样本读**。

★ 这**不推翻**任何已记录的 delta——那些数是真的。
  它推翻的是「三轮 = 三次独立测量」这个读法。

## 判据

给两份及以上的同人物 blind key，算**翻转率** = 换过边的题 / 在多轮中都出现的题。

- 翻转率 **0%** → 报出**代价**（三轮在这一根轴上不独立）
- 翻转率显著低于 50% → 报出（重随机做了，但不够）
- **只有一轮 → 报「未核」，不报「通过」**

★ **报出 ≠ 应当改掉。** 固定映射有它的理由（各轮逐题可比），
重随机也有它的理由（三轮真独立）。**两者不能兼得，这是权衡不是缺陷**，
该由用户裁定（已记入 `_待用户裁定.md` ⑦）。本判据只保证这个代价不再是隐性的。

## 它不做什么

- **不判 delta 对不对。** 那是 `assemble_judge_results` 的事。
- **不判泄题。** 那是 `check_answer_surface_leak`。本件只问「三轮独不独立」。
"""
import argparse
import collections
import json
import pathlib
import re
import sys

LOW = 0.30      # 翻转率低于这个数就报——理想是 ~0.50


def load_key(obj):
    """认三种历史形态 → {case_id: 候选在哪一侧}。**认不出就抛，不静默返回空。**"""
    if not isinstance(obj, dict):
        raise ValueError("顶层不是 dict")
    out = {}
    for k, v in obj.items():
        if isinstance(v, dict) and "A" in v and "B" in v:
            out[v.get("case_id", k)] = "A" if v["A"] == "candidate" else "B"
    if not out:
        raise ValueError("认不出 A/B —— 可能是「值直接是 candidate/baseline」那种旧形态")
    return out


def flip_rate(rounds):
    """rounds: [{case_id: 侧}, ...] → 计量。**分母只算在 ≥2 轮里都出现的题。**"""
    seen = collections.defaultdict(dict)
    for i, r in enumerate(rounds):
        for cid, s in r.items():
            seen[cid][i] = s
    multi = {c: v for c, v in seen.items() if len(v) >= 2}
    flipped = {c for c, v in multi.items() if len(set(v.values())) > 1}
    return {"轮数": len(rounds), "题数合计": len(seen),
            "**在 ≥2 轮里都出现的**": len(multi),
            "其中换过边的": len(flipped),
            "翻转率": (len(flipped) / len(multi)) if multi else None}


def verdict(info):
    """→ 问题列表。**只有一轮时报「未核」，不报「通过」。**"""
    if info["轮数"] < 2:
        return ["**只有一轮，未核**——三轮独立性无从判断，这不是通过"]
    if not info["**在 ≥2 轮里都出现的**"]:
        return ["**没有一道题在两轮里都出现**——两轮题面不同，独立性无从判断，不是通过"]
    r = info["翻转率"]
    if r == 0.0:
        return [f"★★ **翻转率 0%**——{info['**在 ≥2 轮里都出现的**']} 道题的候选侧"
                f"**从第一轮固定到最后一轮**。这是 build_blind_payload 的**有意设计**"
                f"（注释：「轮次之间 A/B 映射必须一致，否则各轮不可比」，并有硬门拦不一致）。"
                f"**代价**：三轮在这根轴上不独立——第 1 轮认出的边，后两轮原样有效；"
                f"跨轮趋势不宜当三个独立样本读。**这是权衡不是缺陷，待裁定 ⑦**"]
    if r < LOW:
        return [f"翻转率 {r:.0%}，低于 {LOW:.0%}——重随机做了但不够，"
                f"跨轮趋势仍不宜当独立样本读"]
    return []


# ══════════════════ 自测 ══════════════════

def selftest() -> int:
    fails = []

    def chk(label, cond):
        print(("  ✓ " if cond else "  ✗ ") + label)
        if not cond:
            fails.append(label)

    print("── ★★ 正向：真数据那一幕——三轮完全固定 → 报出 ──")
    same = {"c1": "A", "c2": "B", "c3": "A"}
    info = flip_rate([same, dict(same), dict(same)])
    chk(f"翻转率 {info['翻转率']:.0%} → 报出", verdict(info) and "翻转率 0%" in verdict(info)[0])

    print("── ★★ 反向对照 ①：真的重随机了 → **不报** ──")
    info2 = flip_rate([{"c1": "A", "c2": "B", "c3": "A", "c4": "B"},
                       {"c1": "B", "c2": "A", "c3": "A", "c4": "A"}])
    chk(f"翻转率 {info2['翻转率']:.0%}（3/4）→ 不报", not verdict(info2))

    print("── ★ 反向对照 ②：只翻了一点点也要报 ──")
    r = flip_rate([{f"c{i}": "A" for i in range(10)},
                   dict({f"c{i}": "A" for i in range(10)}, c0="B")])
    chk(f"翻转率 {r['翻转率']:.0%} → 报「不够」", any("不够" in p for p in verdict(r)))

    print("── ★★★ 反向对照 ③：只有一轮 → 报「未核」，**不报「通过」** ──")
    one = flip_rate([same])
    chk("报出「未核」", any("未核" in p for p in verdict(one)))

    print("── ★★ 反向对照 ④：两轮题面完全不同 → 分母 0，报「无从判断」不报「通过」 ──")
    dif = flip_rate([{"a": "A"}, {"b": "B"}])
    chk(f"分母 {dif['**在 ≥2 轮里都出现的**']} → 报出",
        any("无从判断" in p for p in verdict(dif)))

    print("── ★ 反向对照 ⑤：分母只算在 ≥2 轮里都出现的题 ──")
    m = flip_rate([{"a": "A", "only1": "A"}, {"a": "B", "only2": "B"}])
    chk(f"题数合计 {m['题数合计']}、**多轮的只有 {m['**在 ≥2 轮里都出现的**']}**",
        m["题数合计"] == 3 and m["**在 ≥2 轮里都出现的**"] == 1)

    print("── ★★ 反向对照 ⑥：认不出的 key 形态要抛，不许静默返回空 ──")
    try:
        load_key({"q-01": "candidate"})
        raised = False
    except ValueError:
        raised = True
    chk("旧形态（值是字符串）→ 抛 ValueError", raised)
    chk("新形态两种都认得",
        load_key({"q-01": {"A": "candidate", "B": "baseline", "case_id": "x"}}) == {"x": "A"}
        and load_key({"y": {"A": "baseline", "B": "candidate"}}) == {"y": "B"})

    print(f"\n{'✓ 自测全过' if not fails else f'✗ **{len(fails)} 项未过**'}")
    return 0 if not fails else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--keys", nargs="*", help="同一人物各轮的 blind key，按轮次顺序给")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return selftest()
    if not a.keys:
        print("✗ **什么都没核**——没给 --keys。这不是通过。")
        return 2

    rounds, bad = [], []
    for f in a.keys:
        try:
            rounds.append(load_key(json.loads(pathlib.Path(f).read_text(encoding="utf-8"))))
        except Exception as exc:                                # noqa: BLE001
            bad.append(f"{f}：{exc}")
    for b in bad:
        print(f"  ✗ 读不了：{b}")
    if not rounds:
        print("✗ **一份都没读成**——这不是通过。")
        return 2
    info = flip_rate(rounds)
    for k, v in info.items():
        print(f"  {k}: {v if not isinstance(v, float) else f'{v:.0%}'}")
    problems = verdict(info)
    for p in problems:
        print(f"  · {p}")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
