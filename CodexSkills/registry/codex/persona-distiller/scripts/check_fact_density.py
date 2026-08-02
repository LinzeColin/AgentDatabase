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

## v0.0.0.29：**「关于语料的数」不算「关于人物的事」**

v0.0.0.28 只查「有没有专名或数字」。Galen 第 3 轮实测暴露了这道口子：

> 我按这道门把 `fact` 从 5 条补到 15 条，**真 delta 从 −0.1259 退到 −0.1456**。
> 15 条里 **6 条是语料统计**——「他的注疏合计 578,737 词」「真作 89 部合计 244 万词」。
> **那是我的账本，不是他的知识。用户拿不走这个数。**

这与 Livermore #100 席 E 的原话是同一条：
「真正空转的是 `own_voice_ratio`、536 份、词频 47 次这类**内部遥测：用户拿不走**。」
**同一条诊断第二次出现，而第二次我是把它当解药用的。**

因此 `fact` 分两类，**只有后者计入密度**：

| 类 | 长什么样 | 计入？ |
|---|---|---|
| **账本事实**（ledger） | 「89 部合计 2,442,576 词」「541 份语料」「占比 3.1%」「本工作区口径」 | **不计入** |
| **人物事实**（subject） | 「他在某卷驳 Thessalus」「Athenaeus 1.1e 记他赴宴」「1923-12-21 宣誓作证自报 $9,916」 | 计入 |

判别靠**语料计量词**：条目里若出现「词／部／份／条源／占比／`usable_train`／本工作区口径」
这类**只描述我这份材料有多大**的表述，且**没有**同时出现人物侧的可核锚点
（人名、地名、机构名、书名 + 具体内容、日期），判为账本事实。

**账本事实不是错的，只是不该拿它充数。** 它们仍可留在断言层供审计，
只是不计入「这个产物到底知道多少关于他的事」。

## 射程（必须一起说）

- 它数的是**形态**，不是**真伪**。写一条带年份的假事实照样过。
  **它挡的是「压根没写具体的」，不是「写错了」。** 真伪由盲判席与引文门负责。
- 账本／人物的判别同样是**形态判别**：一条精心措辞的账本事实可以骗过它。
  **它挡的是「拿语料统计充数」这个默认动作，不是有意的伪装。**
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

# ★ v0.0.0.29 账本计量词：只描述「我这份材料有多大」的表述
LEDGER_UNIT = re.compile(
    r"\d[\d,]*\s*(?:词|字|部|份|卷页|条源)"
    r"|\d+(?:\.\d+)?\s*%"
    r"|占比|合计\s*\d|本工作区(?:口径|解出)|usable_train|primary_ratio|own_voice_ratio")
# 人物侧锚点：日期、书名+内容、以及非语料计量的专名
SUBJECT_ANCHOR = re.compile(
    r"\d{3,4}\s*[-–—年]\s*\d{0,2}"        # 年份／日期
    r"|\d{1,2}\s*月\s*\d{1,2}\s*日"
    r"|第\s*[一二三四五六七八九十百\d]+\s*(?:卷|节|号)"   # 卷次编号
    r"|[A-Z][A-Za-zÀ-ɏ.'\-]{2,}\s*[0-9.]+")      # Athenaeus 1.1e 式定位

# ★ v0.0.0.31：**逐字引文本身就是可核标记**。
#   Vesalius #102 实测暴露：四条带拉丁原文引文的人物事实被判 thin——
#   「per tres et ultra septimanas」「quantumvis interim haec nobis sit obscurissima」
#   「quos ter jam praelegerat studiosis」，全是小写起首、无数字，
#   于是 PROPER（要求首字母大写）与 NUMERIC 都不命中。
#   **而逐字引文是所有可核形态里最硬的一种**——可以直接回语料 grep。
#   要求它首字母大写是纯粹的形态偶然。
QUOTED = re.compile(
    r"[「\"“]\s*[A-Za-zÀ-ɏ]{2,}(?:[\s,;.\-]+[A-Za-zÀ-ɏ]{2,}){2,}"   # 引号内 ≥3 个拉丁词
    r"|[「\"“]\s*[Ͱ-Ͽ]{2,}(?:[\s,;.\-]+[Ͱ-Ͽ]{2,}){2,}")            # 或 ≥3 个希腊词

# 可核标记：专名或数字
PROPER = re.compile(
    r"《[^》]{2,}》"                       # 书名号
    r"|[A-Z][A-Za-zÀ-ɏ.'\-]{2,}"  # 拉丁字母专名
    r"|[Ͱ-Ͽ]{3,}"                # 希腊文
)
NUMERIC = re.compile(r"\d")


def classify(claim: str) -> tuple[str, str]:
    """→ (`subject` / `ledger` / `thin`, 理由)。**只有 `subject` 计入密度。**"""
    if QUOTED.search(claim):
        return "subject", "逐字引文（最硬的可核形态：可直接回语料 grep）"
    if not (PROPER.search(claim) or NUMERIC.search(claim)):
        return "thin", "**只有形容词与动词**"
    if LEDGER_UNIT.search(claim) and not SUBJECT_ANCHOR.search(claim):
        return "ledger", "**账本事实：只说了我这份材料有多大**"
    if PROPER.search(claim) and NUMERIC.search(claim):
        return "subject", "专名+数字"
    return "subject", "专名" if PROPER.search(claim) else "数字"


def has_checkable(claim: str) -> tuple[bool, str]:
    """兼容旧调用：`subject` 才算可核。"""
    kind, why = classify(claim)
    return kind == "subject", why


def evaluate(claims: list[dict], usable_train: int,
             per: int = FACTS_PER_SOURCES, floor: int = MIN_FLOOR) -> tuple[list[str], dict]:
    active = [c for c in claims if c.get("status") not in {"superseded"}]
    facts = [c for c in active if c.get("category") == "fact"]
    need = max(floor, math.ceil(usable_train / per)) if usable_train else floor
    problems, thin, ledger = [], [], []
    for c in facts:
        kind, why = classify(str(c.get("claim", "")))
        if kind == "thin":
            thin.append(f'{c.get("claim_id")} {why}')
        elif kind == "ledger":
            ledger.append(f'{c.get("claim_id")} {why}')
    solid = len(facts) - len(thin) - len(ledger)
    info = {
        "usable_train": usable_train, "fact 类条数": len(facts),
        "**人物事实**（计入）": solid, "账本事实（不计入）": len(ledger),
        "无可核内容": len(thin), "要求": need,
        "口径": (f"每 {per} 条可用源至少 1 条**人物事实**，下限 {floor}；"
                 f"每条须带专名或数字；**只说语料有多大的不算**"),
    }
    if thin:
        info["**无可核内容的 fact**"] = thin[:6]
        problems.append(
            f"{len(thin)} 条 `fact` 断言没有任何可核的专名或数字 —— "
            f"**「他重视 X」不是事实断言，是格言**")
    if ledger:
        info["**账本事实**"] = ledger[:6]
        problems.append(
            f"{len(ledger)} 条 `fact` 是**账本事实**（只说了我这份材料有多大），不计入密度 —— "
            f"**那是我的账本不是他的知识，用户拿不走这个数**；"
            f"Galen #101 实测：补 6 条这类事实，真 delta 从 −0.1259 **退到** −0.1456")
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
# ★ 真实样本：Galen 第 3 轮我实际写下的账本事实——形态上过关，内容上是遥测。
REAL_LEDGER = ("他为希波克拉底文本写过 **11 部注疏，合计 578,737 词**，"
               "注疏量约占其存世希腊文著作的四分之一。")
REAL_SUBJECT = ("1923-12-21 他在美国参议院公共土地委员会宣誓作证，"
                "亲口报出该役「realized a profit of only $9,916 on the total transaction」。")
# ★ 真实样本：Vesalius #102 实写的四条之一——**小写起首的拉丁引文，无数字无大写专名**。
#   v0.0.0.30 判它 thin，那是判据错不是断言错。
REAL_QUOTE_ONLY = ("他把绞刑犯或掘出的尸体带回自己房间，留在那里"
                   "「per tres et ultra septimanas」——三周以上。")


def self_test() -> int:
    fails = []
    F = lambda i, t: {"claim_id": f"clm-{i:012x}", "category": "fact", "claim": t}

    # ★ 真实样本对照（四条，全部取自实际断言层）
    for text, want, label in ((REAL_SOLID, "subject", "带书名的人物事实"),
                              (REAL_THIN, "thin", "纯格言"),
                              (REAL_LEDGER, "ledger", "账本事实（Galen 第 3 轮实写）"),
                              (REAL_SUBJECT, "subject", "带日期与金额的人物事实"),
                              (REAL_QUOTE_ONLY, "subject", "**只有小写拉丁引文**的人物事实（v0.0.0.31 修）")):
        kind, why = classify(text)
        if kind != want:
            fails.append(f"真实样本判错：{label} 应为 {want}，实得 {kind}（{why}）")

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

    # ★ 负对照 3（v0.0.0.29 核心）：条数够、形态也过关，但全是账本事实
    p, i = evaluate([F(n, f"{REAL_LEDGER}（第 {n} 部）") for n in range(20)], usable_train=59)
    if not any("账本事实" in x for x in p):
        fails.append(f"负对照 3 未抓出：20 条全是账本事实，实得 {i}")
    if not any("< 要求" in x for x in p):
        fails.append("负对照 3 未抓出：账本事实不计入密度，应同时报条数不足")

    # 正对照 4：账本与人物混合，只按人物条数算
    rows = [F(n, REAL_LEDGER) for n in range(6)] + [F(100 + n, f"{REAL_SUBJECT}（{n}）") for n in range(12)]
    p, i = evaluate(rows, usable_train=59)
    if i["**人物事实**（计入）"] != 12 or i["账本事实（不计入）"] != 6:
        fails.append(f"混合样本计数错：实得 {i}")
    if any("< 要求" in x for x in p):
        fails.append("混合样本被误杀：12 条人物事实已达要求 12")

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
    print("负对照通过：**四条真实样本各自判对**"
          "（带书名的人物事实、纯格言、**账本事实**、带日期与金额的人物事实、"
          "**只有小写拉丁引文的人物事实**）；"
          "条数不足／全是格言／**全是账本事实**三类坏样本全抓出；"
          "足量可核、小语料走下限、账本与人物混合三类正对照未误杀；"
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
