#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**事实密度门**：语料有多大，`fact` 类断言就得有多少条——而且每条要带可核的东西。

## 这条是 Galen #101 被拒发之后倒推出来的

Galen 有 59 条可用训练源、244 万词希腊文一手语料。两轮真基线盲测：

```
第 1 轮  产物 0.6514 / 裸模型 0.8458 → 真 delta -0.1944
第 2 轮  产物 0.7380 / 裸模型 0.8639 → 真 delta -0.1259
```

**第 2 轮我改的是答案，delta 从 -0.19 拉到 -0.13 就到顶了。** 因为天花板在上游：

> 席 D 两轮同一判断：弱的那侧「**用它偏好的更抽象的问题替换了被问的问题**」。
> 裸模型给的是 Athenaeus 1.1e、Thessalus 六个月之夸、
> 伊本·纳菲斯 → 塞尔维特 → 科隆博 → 哈维。
> **产物手里有 244 万词，输出的是格言。**

29 条断言里 `fact` 类只有 **5** 条。**这个比例对整个名册成立**——
Livermore 的 541 份报纸语料也只蒸出 5 条事实。

**「他重视 X」不是事实断言，是格言。** 格言可以从零语料生成，
所以一个满是格言的产物，**在盲测里和裸模型的差别只剩文风**。

## 判据两条

### 一、数量：`fact` 类条数须与可用语料规模挂钩

`min_facts = ceil(usable_train / FACTS_PER_SOURCES)`，下限 `MIN_FLOOR`。
默认 `FACTS_PER_SOURCES = 5`——即**每五条可用源至少要蒸出一条事实断言**。
这个比例不是理论推的，是从「59 条源只蒸出 5 条事实」这个实测缺口反推的下界：
59 / 5 ≈ 12，而实际只有 5。

### 二、质量：每条 `fact` 必须带**可核的东西**

至少命中一项：
- **专名**：连续大写词、书名号内容、希腊／拉丁文斜体术语；
- **数字**：年份、数量、金额、页码、编号。

**只有形容词和动词的「事实」不是事实。**

## 射程（必须一起说）

- 它数的是**形态**，不是**真伪**。写一条带年份的假事实照样过。
  **它挡的是「压根没写具体的」，不是「写错了」。** 真伪由盲判席与引文门负责。
- `FACTS_PER_SOURCES` 是一个**约定**，不是从理论推出来的常数。
  它的作用是把「事实密度」变成一个每次都会被看见的数，而不是一个凭感觉的印象。

退出码：0 = 通过；1 = 不达标；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import json
import math
import pathlib
import re
import sys

FACTS_PER_SOURCES = 5
MIN_FLOOR = 5

# 可核标记：专名或数字
PROPER = re.compile(
    r"《[^》]{2,}》"                       # 书名号
    r"|[A-Z][A-Za-zÀ-ɏ.'\-]{2,}"  # 拉丁字母专名
    r"|[Ͱ-Ͽ]{3,}"                # 希腊文
)
NUMERIC = re.compile(r"\d")


def has_checkable(claim: str) -> tuple[bool, str]:
    if PROPER.search(claim) and NUMERIC.search(claim):
        return True, "专名+数字"
    if PROPER.search(claim):
        return True, "专名"
    if NUMERIC.search(claim):
        return True, "数字"
    return False, "**只有形容词与动词**"


def evaluate(claims: list[dict], usable_train: int,
             per: int = FACTS_PER_SOURCES, floor: int = MIN_FLOOR) -> tuple[list[str], dict]:
    active = [c for c in claims if c.get("status") not in {"superseded"}]
    facts = [c for c in active if c.get("category") == "fact"]
    need = max(floor, math.ceil(usable_train / per)) if usable_train else floor
    problems, thin = [], []
    for c in facts:
        ok, why = has_checkable(str(c.get("claim", "")))
        if not ok:
            thin.append(f'{c.get("claim_id")} {why}')
    solid = len(facts) - len(thin)
    info = {
        "usable_train": usable_train, "fact 类条数": len(facts),
        "其中带可核专名或数字": solid, "要求": need,
        "口径": f"每 {per} 条可用源至少 1 条事实断言，下限 {floor}；每条须带专名或数字",
    }
    if thin:
        info["**无可核内容的 fact**"] = thin[:8]
        problems.append(
            f"{len(thin)} 条 `fact` 断言没有任何可核的专名或数字："
            f"{', '.join(t.split()[0] for t in thin[:6])}"
            f"{' …' if len(thin) > 6 else ''} —— **「他重视 X」不是事实断言，是格言**")
    if solid < need:
        problems.append(
            f"可核 `fact` 断言 {solid} 条 < 要求 {need} 条"
            f"（{usable_train} 条可用源 ÷ {per}）"
            f" —— **语料里可核的具体事实没有进入断言层**；"
            f"这正是 Galen #101 真 delta −0.1259 的根因")
    return problems, info


# ── 负对照 ────────────────────────────────────────────────────────────
# ★ 真实样本：下面两条直接取自 Galen #101 的实际断言层（2026-08-02 实测）。
REAL_SOLID = ("他为自己编纂过真作目录：《De libris propriis》与"
              "《De ordine librorum suorum ad Eugenianum》，明确用于把真作与市面冒名伪托本分开。")
REAL_THIN = "**「知道」必须以「你自己能重做一遍」为标准。** 他反对靠背诵获得的医学知识。"


def self_test() -> int:
    fails = []
    F = lambda i, t: {"claim_id": f"clm-{i:012x}", "category": "fact", "claim": t}

    # ★ 真实样本对照
    ok, why = has_checkable(REAL_SOLID)
    if not ok:
        fails.append(f"真实样本被误杀：带书名的事实断言判为 {why}")
    ok, _ = has_checkable(REAL_THIN)
    if ok:
        fails.append("真实样本未抓出：纯格言（无专名无数字）被判为有可核内容")

    # 负对照 1：条数不足
    p, i = evaluate([F(n, REAL_SOLID) for n in range(5)], usable_train=59)
    if not any("< 要求" in x for x in p):
        fails.append(f"负对照 1 未抓出：59 源只有 5 条 fact（要求 12），实得 {i}")

    # 负对照 2：条数够但全是格言
    p, _ = evaluate([F(n, REAL_THIN) for n in range(20)], usable_train=59)
    if not any("没有任何可核" in x for x in p):
        fails.append("负对照 2 未抓出：20 条全是格言")
    if not any("< 要求" in x for x in p):
        fails.append("负对照 2 未抓出：格言不计入可核条数，应同时报条数不足")

    # 正对照 1：条数够且都可核
    p, _ = evaluate([F(n, f"{REAL_SOLID}（第 {n} 条）") for n in range(12)], usable_train=59)
    if p:
        fails.append(f"正对照 1 被误杀：12 条可核事实 / 59 源，却报 {p}")

    # 正对照 2：小语料走下限，不按比例
    p, i = evaluate([F(n, REAL_SOLID) for n in range(5)], usable_train=10)
    if p:
        fails.append(f"正对照 2 被误杀：10 源 5 条应走下限 5，实得 {i}")

    # 边界：只有数字没有专名 → 仍算可核
    ok, why = has_checkable("1923-12-21 他在参议院宣誓作证，自报获利 9,916。")
    if not ok:
        fails.append(f"边界失败：纯数字事实被判为 {why}")

    # 边界：只有专名没有数字 → 仍算可核
    ok, _ = has_checkable("《Deipnosophistae》里提到他。")
    if not ok:
        fails.append("边界失败：纯专名事实被误杀")

    # 边界：superseded 不计入
    rows = [F(n, REAL_SOLID) for n in range(12)]
    rows[0]["status"] = "superseded"
    p, i = evaluate(rows, usable_train=59)
    if i["fact 类条数"] != 11:
        fails.append(f"边界失败：superseded 未被排除，实得 {i['fact 类条数']}")

    for f in fails:
        print(f"✗ {f}")
    if fails:
        print(f"负对照未通过：{len(fails)} 项")
        return 1
    print("负对照通过：**两条真实样本各自判对**（带书名的事实未误杀、纯格言被抓出）；"
          "条数不足与「够数但全是格言」两类坏样本全抓出；"
          "足量可核、小语料走下限两类正对照未误杀；"
          "纯数字与纯专名均算可核；superseded 不计入")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="事实密度门：语料有多大，fact 类断言就得有多少条")
    ap.add_argument("target", nargs="?", type=pathlib.Path, help="工作区目录")
    ap.add_argument("--per", type=int, default=FACTS_PER_SOURCES)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    if a.self_test:
        return self_test()
    if not a.target:
        print("用法错误：需要工作区路径（或 --self-test）", file=sys.stderr)
        return 3
    cp = a.target / "evidence/claims.jsonl"
    sp = a.target / "evidence/source-ledger.jsonl"
    if not cp.is_file():
        print(f"用法错误：{cp} 不存在", file=sys.stderr)
        return 3
    claims = [json.loads(l) for l in cp.read_text(encoding="utf-8").splitlines() if l.strip()]
    usable = 0
    if sp.is_file():
        for l in sp.read_text(encoding="utf-8").splitlines():
            if not l.strip():
                continue
            r = json.loads(l)
            if r.get("split") == "train" and r.get("tier") != "U":
                usable += 1
    problems, info = evaluate(claims, usable, per=a.per)

    if a.json:
        print(json.dumps({"problems": problems, "metrics": info}, ensure_ascii=False, indent=1))
        return 1 if problems else 0
    if not problems:
        print("✓ 事实密度达标：", json.dumps(info, ensure_ascii=False))
        return 0
    print(f"\n✗ 事实密度 {len(problems)} 条问题：\n")
    for x in problems:
        print(f"  - {x}")
    print("\n  ↑ **格言可以从零语料生成。** 一个满是格言的产物，"
          "在盲测里和裸模型的差别只剩文风——Galen #101 实测 −0.1259。")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
