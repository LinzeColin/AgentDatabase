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
# v0.0.0.36：**暂定值，无实测支持。** 有实据的只是「四个人恒为 1 条」这个事实，
# 以及那四个恒负套组每人 8 道题。取 3 是因为它明确高于 1、又远低于 8——
# 不至于逼人为凑数编方法（Galen 那 5 条账本事实就是被凑数逼出来的）。
# **只报不拦**：已入库 100 人没回扫过，硬拦会把整个名册一起拦下。
METHOD_FLOOR = 3

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

# ── v0.0.0.36：`work-method` 密度 ───────────────────────────────────────
# 四人合并实测（Galen/Vesalius/Harvey/Jenner，各自末轮，共 260 逐对）：
# **四个套组在四个人身上无一例外为负**——planning-fidelity −0.0508、
# task-completion −0.0675、tool-use −0.0783、token-efficiency −0.0867（均 0/4 人为正）。
# 这四组问的都是「给我一套做法／从哪开始／你怎么做到的／一句话说清方法」。
# 而稳定为正的三组问的是「你写过什么／那件事的细节／你不知道的东西」。
#
# ★ 根因不在答案，在断言层：**四个人的 `work-method` 断言恰好都是 1 条**
#   （fact 则是 15/23/24/16）。因为密度门只数 `fact`，我每轮补的就都是 `fact`。
#   **判据把我推向了 fact，而输掉的四组要的是 work-method。**
#
# 与 v0.0.0.29（账本事实 ≠ 人物事实）同一形态：类别没分开，力气就流错方向。
METHOD_STEPS = re.compile(
    r"→|->|—[^—]{2,20}—"                       # 箭头或破折号串起的步骤
    r"|先[^，。]{2,30}[，。]?\s*(?:再|然后|接着)"   # 先…再…
    r"|第\s*[一二三四五六七八九1-9]\s*步"
    # ★ v0.0.0.44：认圈码与序号列表。Virchow #109 实测撞出——
    #   四条 work-method 里三条用 `① ② ③` 编号，判据一条都不认，
    #   把它们全判成「复述式」。**`①②③` 本来就是步骤标记，是正则漏了，
    #   不是那三条写得不好。** 加它并不放松分界：
    #   分界在**判据**那一半（METHOD_CRITERION），步骤这一半只管「有没有分步」。
    r"|[①②③④⑤⑥⑦⑧⑨].{2,80}?[②③④⑤⑥⑦⑧⑨]"      # ① … ② …（至少两步）
    r"|\b1[\.、)].{2,80}?\b2[\.、)]")            # 1. … 2. …（至少两步）
# 验证／弃置判据——**这是可复用与复述的分界**：
# 一套做法若没有「怎么知道这步做对了／什么时候丢掉」，用户照着做也不知道自己做错没有。
METHOD_CRITERION = re.compile(
    r"对不上|不算数|就丢|丢掉|排除|再验|复核|反证|归谬|证伪|判据|标准是"
    r"|才(?:下结论|算|能说)|否则|若[^，。]{1,20}则|压到二值|交叉比|两三张嘴|缺口写在")


def classify_method(claim: str) -> tuple[str, str]:
    """→ (`reusable` / `retrospective`, 理由)。**只有 `reusable` 计入方法密度。**

    分界不是「有没有步骤」——四条真实断言全都有步骤。
    分界是**有没有判据**：怎么知道这一步做对了、什么时候把结果丢掉。
    裸模型在 tool-use 上赢的那一段给了判据（「同一件事让两三张嘴说，对不上就丢」），
    我的产物给的是处境（「我住在这儿，我知道谁在哪」）——**处境不可复用。**
    """
    has_step = bool(METHOD_STEPS.search(claim))
    has_crit = bool(METHOD_CRITERION.search(claim))
    if has_step and has_crit:
        return "reusable", "有步骤且有验证/弃置判据"
    if has_step:
        return "retrospective", "**只有步骤没有判据**：照着做的人不知道自己做错没有"
    return "retrospective", "**连步骤都没有**：是一句概括不是一套做法"


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

    # ── v0.0.0.36：方法密度（**只报不拦**，见下）────────────────────────
    # ★ 射程边界：只在断言层**成型**时才判。判据是「类别数 ≥ 3」——
    #   真实工作区有 9–10 个类别（fact / heuristic / mental-model / boundary / …），
    #   而只有 fact 的输入是事实密度的夹具，不是方法密度的判对象。
    #   接线当场撞出来的：不设边界会把本门自己的两条正对照误杀。
    #   **判据拦下了不该拦的东西时，默认是射程写错了**（v0.0.0.34 同一条）。
    if len({c.get("category") for c in active}) < 3:
        info["方法密度"] = "**未判**（断言层类别 < 3，不像成型的断言层）——不是通过"
        return problems, info
    methods = [c for c in active if c.get("category") == "work-method"]
    reusable, retro = [], []
    for c in methods:
        kind, why = classify_method(str(c.get("claim", "")))
        (reusable if kind == "reusable" else retro).append(f'{c.get("claim_id")} {why}')
    info["work-method 条数"] = len(methods)
    info["**可复用做法**（计入）"] = len(reusable)
    info["复述式（不计入）"] = len(retro)
    info["方法口径"] = (f"至少 {METHOD_FLOOR} 条**可复用做法**；"
                        f"可复用 = 有步骤**且**有验证/弃置判据。"
                        f"**这个数是暂定的，尚无实测支持**——有实据的只是「四人恒为 1」这个事实")
    if retro:
        info["**复述式 work-method**"] = retro[:6]
    if len(reusable) < METHOD_FLOOR:
        problems.append(
            f"可复用 `work-method` 断言 {len(reusable)} 条 < 暂定 {METHOD_FLOOR} 条"
            f"（另有 {len(retro)} 条是复述式）—— "
            f"**四人合并实测：planning-fidelity / task-completion / tool-use / token-efficiency "
            f"四组在四个人身上无一例外为负（0/4），而这四人的 `work-method` 恰好都只有 1 条**；"
            f"密度门只数 `fact`，力气就全流去了 `fact`（15/23/24/16）")
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

    # ── v0.0.0.36：方法密度 ──────────────────────────────────────────
    # ★ 真实夹具：下面四条**逐字取自四个人实际的 `work-method` 断言**（各自唯一的那一条）。
    #   两条有验证判据、两条没有——真实数据自带双侧夹具，不必构造。
    M = lambda i, t: {"claim_id": f"clm-m{i:011x}", "category": "work-method", "claim": t}
    REAL_M_GALEN = "工作方式是**写—编号—互引—编目**：先写成篇，再在正文中互相指引，最后为全部作品编目并规定阅读次序。"
    REAL_M_VESALIUS = "**做法是：亲手切 → 与旧文本逐条比 → 记下分歧积成大卷 → 换物种再验（有尾与无尾的猿）→ 才下结论。**"
    REAL_M_HARVEY = ("**做法是：先在活体与尸体上反复演示 → 把判据压到二值 → "
                     "直接观察不到的那一环用量级归谬补 → 缺口写在结论旁边 → 发表后不与骂你的人辩。**")
    REAL_M_JENNER = "**先攒既往观察，再做一次前瞻接种，最后自费把两者一起发出去。**"
    print("\n── 方法密度（v0.0.0.36）：四条真实 work-method 断言 ──")
    for text, want, who in ((REAL_M_VESALIUS, "reusable", "Vesalius"),
                            (REAL_M_HARVEY, "reusable", "Harvey"),
                            (REAL_M_GALEN, "retrospective", "Galen"),
                            (REAL_M_JENNER, "retrospective", "Jenner")):
        got, why = classify_method(text)
        mark = "✓" if got == want else "✗"
        print(f"  {mark} {who:<9} 判为 {got:<14}（应为 {want}）—— {why}")
        if got != want:
            fails.append(f"方法夹具失败：{who} 判为 {got}，应为 {want}")

    # 成型断言层的骨架：凑够 3 个类别，否则射程边界会跳过方法判定
    SHAPE = [{"claim_id": "clm-h1", "category": "heuristic", "claim": "凡事先看证据"},
             {"claim_id": "clm-b1", "category": "boundary", "claim": "机理我给不出"}]

    # 坏样本：四条全是复述式 → 必须报出
    p, i = evaluate([F(n, REAL_SOLID) for n in range(12)] + SHAPE
                    + [M(n, REAL_M_JENNER) for n in range(4)], usable_train=59)
    if not any("work-method" in x for x in p):
        fails.append("方法失败：4 条全复述式未被报出")
    if i["**可复用做法**（计入）"] != 0:
        fails.append(f"方法失败：复述式被计入，实得 {i['**可复用做法**（计入）']}")

    # 正对照：三条可复用 → 不得报出
    p, i = evaluate([F(n, REAL_SOLID) for n in range(12)] + SHAPE
                    + [M(n, REAL_M_HARVEY) for n in range(3)], usable_train=59)
    if any("work-method" in x for x in p):
        fails.append("方法失败：3 条可复用被误报")

    # ★ 射程边界：只有 fact 的输入（本门自己的事实密度夹具）**一条方法问题都不许报**
    p, i = evaluate([F(n, REAL_SOLID) for n in range(12)], usable_train=59)
    if any("work-method" in x for x in p):
        fails.append("方法射程失败：纯 fact 输入被判方法密度")
    if "未判" not in str(i.get("方法密度", "")):
        fails.append("方法射程失败：纯 fact 输入未标为「未判」")
    else:
        print("  ✓ 射程边界：纯 fact 输入标为「未判（不是通过）」，不报方法问题")

    # ★ 反向对照：关掉「判据」这一条，可复用的两条必须转为复述式
    #   ——证明放行靠的是判据判据本身，不是步骤箭头
    _saved = globals()["METHOD_CRITERION"]
    globals()["METHOD_CRITERION"] = re.compile(r"___IMPOSSIBLE_SENTINEL___")
    rev = [classify_method(t)[0] for t in (REAL_M_VESALIUS, REAL_M_HARVEY)]
    globals()["METHOD_CRITERION"] = _saved
    if any(k == "reusable" for k in rev):
        fails.append("方法反向对照失败：关掉判据后仍判为可复用——放行靠的不是判据")
    else:
        print("  ✓ 反向对照：关掉验证判据后，两条可复用样本全部转为复述式")

    # ★ v0.0.0.44 新增：圈码步骤须被认出，且**只加步骤不足以判可复用**。
    CIRCLED_OK = ("引自己旧作时先确认引的是哪一版。步骤：① 翻扉页，不看文件名；"
                  "② 版次与年份一并记下；③ 若不同版本措辞有别，把差别写出来。"
                  "**弃置判据：扉页看不到版次的，就不要断言它是哪一版。**")
    CIRCLED_NO = ("引自己旧作时先确认引的是哪一版。步骤：① 翻扉页，不看文件名；"
                  "② 版次与年份一并记下；③ 若不同版本措辞有别，把差别写出来。")
    k1, _ = classify_method(CIRCLED_OK)
    k2, why2 = classify_method(CIRCLED_NO)
    ok1 = k1 == "reusable"
    ok2 = k2 == "retrospective"
    print(f"  {'✓' if ok1 else '✗'} 圈码 ①②③ 的步骤被认出（带弃置判据 → reusable）")
    print(f"  {'✓' if ok2 else '✗'} **同一段去掉弃置判据 → 仍判复述式**"
          f"（证明扩步骤正则没有放松分界）")
    if not ok1:
        fails.append("圈码 ①②③ 的步骤未被认出——三条真实 work-method 会被误判为复述式")
    if not ok2:
        fails.append("去掉弃置判据后仍判可复用——**扩步骤正则放松了分界**")

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
          "纯数字与纯专名均算可核；superseded 不计入；"
          "**方法密度另有 4 条真实 work-method 夹具（两侧各二）+ 1 条反向对照**")
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
