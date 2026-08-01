#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**名册独立性**：这 100 个人物到底是 100 份认知，还是一份认知的 100 个说法。

## 触发本检查器的实例

用户 2026-08-02 评分：

> 如果所有人物都由同一个基础模型、同一个上下文和相似资料生成，
> 它们主要提供的是**「结构化视角差异」，不是 97 份真正独立的认知与判断**。
> 人物之间还可能产生**相关性错误、共同幻觉和伪共识**。
> 真正独立性：**40%**。

## 本检查器测什么、不测什么

**测**：名册**静态层面**的同质化——不同人物写下来的
「可蒸馏特点 / 关键能力 / 硬边界」在措辞与概念上有多少重叠。

**不测**：同一个问题过 k 个人物时答案会不会趋同（那是**动态伪共识**，
需要真的把 k 个人物跑起来，本检查器做不到）。
**两者不可互相替代**，本文件里的数**不足以回答用户的问题**，只能给出下界证据：
**如果静态层面就已经高度重叠，动态层面不可能独立。**

## 判据

对每一对人物，取其 `distillation_traits + key_capabilities + hard_boundaries`
的**中文双字词 + 英文词**集合，算 Jaccard 相似度。然后比较两个分布：

| 量 | 含义 |
|---|---|
| `within_family` | **同族**人物两两相似度均值 |
| `cross_family` | **跨族**人物两两相似度均值 |
| `ratio` | `cross_family ÷ within_family` |

**`ratio` 越接近 1，说明「分族」这个结构没有产生差异化**——
一个软件开发师和一个医疗护理师，写出来的东西跟两个软件开发师之间一样像。
那正是「结构化视角差异而非独立认知」的可测量形态。

**不设阈值。** 一个名册的合理相似度是多少，需要与外部对照（如真人专家问卷）比，
本项目没有那个对照。**现在拍的任何阈值都是编的。**

退出码：恒为 0（只报不判）；`--self-test` 失败时为 1。
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import re
import sys

TOKEN = re.compile(r"[a-zA-Z]{3,}|[一-鿿]{2}")
FIELDS = ("distillation_traits", "key_capabilities", "hard_boundaries")


def tokens(item: dict) -> set:
    text = " ".join(
        str(x) for f in FIELDS for x in (item.get(f) or [])
    )
    return set(TOKEN.findall(text.lower()))


def jaccard(a: set, b: set) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def analyse(products: list) -> dict:
    toks = [(p.get("registration_category"), tokens(p)) for p in products]
    toks = [(f, t) for f, t in toks if t]
    within, cross = [], []
    for (fa, ta), (fb, tb) in itertools.combinations(toks, 2):
        (within if fa == fb else cross).append(jaccard(ta, tb))
    mw = sum(within) / len(within) if within else 0.0
    mc = sum(cross) / len(cross) if cross else 0.0
    top = sorted(cross, reverse=True)[:5]
    return {
        "personas": len(toks),
        "within_family_pairs": len(within),
        "cross_family_pairs": len(cross),
        "within_family_mean": round(mw, 4),
        "cross_family_mean": round(mc, 4),
        "ratio_cross_over_within": round(mc / mw, 4) if mw else None,
        "cross_family_top5": [round(x, 4) for x in top],
        "口径": ("Jaccard over 中文双字词 + 英文词，取自 distillation_traits / "
                 "key_capabilities / hard_boundaries。**只测静态措辞重叠**，"
                 "测不了「同一问题过 k 个人物会不会趋同」那种动态伪共识。"
                 "**不设阈值**——没有外部对照可比。"),
    }


def self_test() -> int:
    fails = []

    def P(fam, *lines):
        return {"registration_category": fam, "distillation_traits": list(lines),
                "key_capabilities": [], "hard_boundaries": []}

    # 负对照 1：全员克隆 → 相似度应接近 1，且跨族/同族之比接近 1
    clones = [P(f"族{i%3}", "把浮盈当作判断正确的证据", "先认第一笔小亏") for i in range(6)]
    r = analyse(clones)
    if r["within_family_mean"] < 0.95 or r["cross_family_mean"] < 0.95:
        fails.append(f"负对照未抓出：全员克隆，实得 {r}")
    if r["ratio_cross_over_within"] is None or abs(r["ratio_cross_over_within"] - 1) > 0.05:
        fails.append(f"负对照未抓出：克隆名册的跨族/同族之比应≈1，实得 {r['ratio_cross_over_within']}")

    # 正对照：同族内相似、跨族不相似 → ratio 应明显小于 1
    varied = [
        P("软件", "先写测试再写实现", "把复杂度当成本"),
        P("软件", "先写测试再写实现", "把耦合当负债"),
        P("医疗", "先排除最坏诊断", "把病史当主证据"),
        P("医疗", "先排除最坏诊断", "把体征当次证据"),
    ]
    r = analyse(varied)
    if r["ratio_cross_over_within"] is None or r["ratio_cross_over_within"] > 0.6:
        fails.append(f"正对照失败：分化良好的名册 ratio 应明显 <1，实得 {r['ratio_cross_over_within']}")

    # 反向对照：**空字段不得被算成「高度独立」**
    empties = [{"registration_category": "族A"}, {"registration_category": "族B"}]
    r = analyse(empties)
    if r["personas"] != 0:
        fails.append("反向对照失败：全空字段的人物不该计入统计（会伪装成 0 相似度）")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：克隆名册被判为高度重叠且跨族/同族之比≈1，"
          "分化良好的名册 ratio 明显 <1，空字段不被伪装成独立")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="名册独立性：静态措辞重叠的下界证据")
    ap.add_argument("--registry-root", type=pathlib.Path)
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    root = a.registry_root or pathlib.Path(__file__).resolve().parents[1]
    index = json.loads((root / "team-index.json").read_text(encoding="utf-8"))
    r = analyse(index.get("products") or [])
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
