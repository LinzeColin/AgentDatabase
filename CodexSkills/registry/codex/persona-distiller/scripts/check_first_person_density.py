#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**门数的是「有几份来源」，不是「有几句他的话」**——语料够门，声口不够。

## 撞出它的那一次（Coffin #130，2026-08-05，**在写断言之前**）

三道 quick 门**全过**：

| 项 | 实测 | 门 | |
|---|---|---|---|
| 来源数 | 18 | ≥8 | ✓ |
| 道数 | 3 | ≥3 | ✓ |
| 一手占比 | 15/18 = 83.3% | ≥0.40 | ✓ |

**而整份语料（172,138 字符）里，他自己说的实质的话只有 15 句**（0.87/万字）。
★ 我第一版报的是「8 句」——**那是本件早期正则漏数的结果**，见下「为什么裸数会骗人」末段。

因为那 18 份里 14 份是**专利说明书**——文体决定了它几乎全是第三人称的装置描述
加权利要求样板。**每多抓一件专利，来源数 +1，而他的话几乎 +0。**
实测：最长的两份（32k / 35k 字符）**各只有 1 句**实质第一人称。

抓源方为此把 `conversations` 一道找遍了（AIEE vols 4/6/7/8、ASME vol 10、
1918–1921 三部书、1913 年 NYPL 书目），**没有一份是他开口说话的**。
（AIEE 里的每一个「Coffin」都是 `CoFFIN, CHAs. A.`——汤姆森—休斯顿的副总裁兼司库，**另一个人**。）

## ★★★ 为什么裸数「I」会骗人（75% 是噪音）

第一版我量出 118 处第一人称，密度 7.2/万字，**差点当成「够用」写进风险单**。
去看样本才发现：**OCR 把零件标号读成了 `I`**——
`anvil I-I`、`extensions I and J`、`I serving to force the ends together`。

| | 数 |
|---|---|
| 裸 `\\bI\\b` | 118 |
| **其中零件标号等噪音** | **89（75%）** |
| 动词锚定（`I have`／`I find`／`I prefer`…） | 16 |
| 其中权利要求套语 | 6 |
| **实质** | **8** |

→ 本判据**只数动词锚定的、且不是套语的**。裸数一律不报。

## 它报什么

按源报实质第一人称句数与密度（每万字），并给出**逐句原文**——
**不给数就下结论是不许的，所以它必须能出示那几句。**

## ★★ 全库普查实测（2026-08-05，10 个有语料的工作区）

**只在体裁与语言都可比时才有意义。** 清楚是英文、且构成相近的几个：

| 工作区 | 源 | 正文字符 | 实质句 | 密度 |
|---|---|---|---|---|
| **wip-coffin-130** | 18 | 172,138 | 15 | **0.87** ⚠ |
| wip-carver-127 | 38 | 1,172,699 | 225 | 1.92 |
| wip-thomson-129 | 53 | 918,922 | 391 | **4.25** |
| wip-blackwell-118 | 89 | 8,094,123 | 3,882 | 4.80 |
| wip-lister-108 | 60 | 22,109,350 | 11,296 | 5.11 |

**Coffin 比同族的 Thomson 薄 5 倍**——两人同为焊接、同时代、同为英文，
差别就在 Thomson 有学会讨论记录而 Coffin 只有专利。**这一栏正是为此而设。**

### ★★★ 两条不可信，不许当结论用

- **非英文一律不给数**：Mendel #125（德文，15,789,533 字符）曾报「实质 0 句」、
  Pasteur #106、Semmelweis #105 同理。**那不是声口薄，是判据不认识那门语言。**已加语言护栏。
- **混语语料的判定不可靠**：Koch #107（120 源 / 2 亿字符 / 0.07）与 Liebig #124（0.47）
  仍被判为英文并打上「薄」，而两人都是德语人物、语料里多半掺着英译与英文二手件。
  本件的语言判定**只抽前 6 份各 2 万字**，抽到英文就整份算英文。
  **→ 这两条的「薄」不作数。** 要作数得逐份判语言，本件还没做。

  > ### ★★★★★ 2026-08-11：**上面这段「还没做」已经做了**
  >
  > 上面那几行**从写下的那天起就是准确的**，而它在文件里挂着没被修——
  > 我这次不是发现了它，是发现**它被记下来却一直没人动**
  > （[[a-checker-nothing-calls-is-not-a-checker]] 同族：写下来 ≠ 落成判据）。
  >
  > 实跑真判据量清了射程：**受影响的不是 2 个人物，是 6 个**——
  > Koch 74%／Galen 88%／Pasteur 87%／Slavyanov 61%（俄语）／Grotius 50%／Harvey 46%
  > 的语料是本件读不了的语种，而其中 **Koch／Galen／Slavyanov 三个照样印出了数**
  > （0.07／0.47／0.02），Pasteur 拦住了——**差别只在按路径排序的前 6 份恰好是什么**。
  >
  > 修法见下面 `language_split()`：语种改**按字符加权判全量**、密度只除可读语种的字符、
  > 可读占比一律打印。修后这 6 个**全部改判为不适用**。
  >
  > ★ **没有找到被这个数带偏的已发布判断**：靠第一人称密度做的两条延后
  > （Coffin #130／Bain #136）语料都是 100% 英文，Slavyanov #115 的延后理由是
  > 一手占比 8/53 而不是声口。**缺陷是真的，而我没查到它改变过哪个结论。**

## ★ 它不做什么

- **不拦。** 密度低不等于做不成：分析型产物、第三人称产物本来就不靠第一人称
  （见 `check_persona_frame_break` 的 `analytic` 模式）。**它只把数摆出来。**
- **不判「够不够」。** 够不够取决于要出哪些用例——
  `voice`／`trajectory`／`contrast` 要他谈自己，`known`／`tool-use` 只要他讲做法。

## ★★★★ 2026-08-11 新增的一个盲区：**译本里的 `I` 可能是译者的**

Grotius #168 实测：18 源 / 2,140 万字符 / 裸 `I` 13,567，本件判为「93% 噪音」。
去抽 6 份读那些命中的原文，**75.1% 既不是零件标号也不是罗马数字
（卷章号只占 3.4%），而是真实的英文第一人称——说话的却不是他**：

    · the translation with which **I have** accompanied the text,
      **I have** omitted all the quotations
    · **I agree** with a former ed[itor]

**是译者与编者在卷首序、译注、编者按里说话。**
Grotius 的五个英译本（Whewell 1853 / Kelsey 1925 / Evats 1682 /
Magoffin 1916 / Barham 1839）与一本传记（Butler 1826）都带大段这种文字。

### 射程声明（**用本件的读数之前必须知道**）

**本件分不出「译文里的 I」与「译者说的 I」。**
对**靠译本取材的人物**（Grotius、Cicero、Galen 这一类），
本件给出的「实质第一人称句」**含译者，未去除**——
那个数**不能直接当他的声口用**。

★ 两头都不可用的形态（Grotius 实测）：
  · **英译本**量到的是译者；
  · **拉丁一手件**的 `ego` 有 **39%** 被 OCR 读成 `cgo`（长 s → f），
    9/10 份的 `est` 存活率 ≤1.5% —— 量不到他。
  → 这类人物**要先重 OCR 一手件**，再谈声口。

★★ 怎么区分（尚未落成判据，先写在这里）：正文与**卷首序／译注／编者按**
分开计数；后者通常集中在文件前部、且带 `translator`／`editor`／`preface`／
`the reader` 一类词。**这个做法还没量过假阳，别当已验证的用。**

关联 `measured-voice-in-the-wrong-register`（同一人物在 Campbell 删节本上
量出 0.007/千词、Kelsey 全译本 0.85，**差 130 倍**）。
"""
import argparse
import json
import pathlib
import re
import sys

#: ★ 剥掉抓源方写的出处表头再量——**表头是出处说明，不是他的话**。
#:   全库只有 Adams（144 份）与 Coffin（36 份）有这种表头，
#:   实测占全文**聚合 17.2% / 11.7%**，**逐份中位 39.1% / 16.1%**。
#: ★★ 接上之后**逐个量过前后差**，只写量到的：
#:   · `check_lane_quotes_verbatim` @ Coffin：核过 1 → 0，
#:     报出 `Coffin, Charles L., Detroit, Mich.` **对不上**——
#:     那句「逐字引文」只存在于**我自己写的表头里**。这是 Barton 事故的引文版，实锤一条。
#:   · ★★★★ `check_ocr_language_death` @ Coffin：不剥时「**每一份都在下限之上**」，
#:     剥掉表头后报出 **2 份虚词占比 0.101（下限 0.15）**——
#:     **我那段干净的英文表头把 OCR 烂掉的文件托过了及格线。**
#:     同一件在 Adams 上是「可判份数 94 → 60」：34 份**只因表头的词数才够得上判**。
#:   · `check_first_person_density`：正文字符 −0.6%，密度 1.68 → **1.69**——
#:     **几乎没变**。我一度在这里写「第一人称密度被表头拉偏」，**那句没有实测支撑，已删**。
#:   · 其余多数判据前后一致。**接线是按「表头不是他的话」这条原则做的，不是因为每个都变了。**
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent))
from common import corpus_body  # noqa: E402

# 只认动词锚定的第一人称——裸 `I` 在 OCR 语料里 75% 是零件标号
VERB = (r"\bI (?:have|had|am|was|claim|find|found|prefer|may|make|made|use|used|do|did|"
        r"desire|employ|shown|show|believe|consider|know|knew|think|thought|wish|intend)\b")
# ★★★ **不许写 `[^.]{0,110}…[^.]{0,110}\.`**——两侧都是可变长否定字符类，
#   在几十万字的语料上会灾难性回溯。实测：Thomson #129 的 1,030,112 字符**直接跑不完**
#   （2 分钟超时），而本件已经接进研究门——**那等于把门挂死**。
#   （与 RUNBOOK 第六十八种同一种病：可变长字符类相邻。）
#   改法：**只用正则找动词锚点，上下文用字符串切片取**，全程线性。
_ANCHOR = re.compile(VERB)
# 专利/论文的套语——是他的字，但**不是他的话**
BOILER = re.compile(r"(What I claim|I claim as my invention|desire to secure by Letters Patent|"
                    r"Be it known that I|I, the undersigned)", re.I)
# ★★ **指示性**第一人称——是他的字，但不含任何主张：
#   `I have shown the conductor ... in Fig. 2`（指图）、
#   `In testimony whereof I have hereunto set my hand`（签署套语）、
#   `as I have described above`（回指本文）。
#   抓源方独立复量时把这类单列（~23 里约 10 句），**不单列就会高估声口**。
DEICTIC = re.compile(
    r"(In testimony whereof|hereunto set my hand|"
    r"I have (?:shown|illustrated|described|indicated|represented|designated)\b|"
    r"as I have (?:said|stated|shown|described)\b|"
    r"I have (?:not )?(?:herein|above|hereinbefore))", re.I)
HDR = "=" * 40          # 抓源方写的表头与正文的分隔线


_WORD_RE = re.compile(r"[A-Za-z][A-Za-z'-]*")


def body_of(text: str) -> str:
    """剥掉抓源方自己写的表头——**表头里的字不是文献的字**。"""
    return text.split(HDR, 1)[-1] if HDR in text else text


def scan_text(text: str) -> dict:
    b = re.sub(r"\s+", " ", body_of(text))
    raw = len(re.findall(r"\bI\b", b))
    subs, deictic = [], []
    for m in _ANCHOR.finditer(b):
        a = b.rfind(".", 0, m.start())          # 上一个句点之后
        z = b.find(".", m.end())                # 下一个句点
        seg = b[(a + 1 if a >= 0 else 0):(z + 1 if z >= 0 else len(b))].strip()
        if len(seg) > 320:                      # 句子过长多半是没断开的 OCR 块，截一下
            seg = seg[:320]
        if BOILER.search(seg):
            continue
        (deictic if DEICTIC.search(seg) else subs).append(seg)
    # ★ 套语独立数，**不依赖 SENT 先匹配上**——
    #   `Be it known that I, CHARLES L. COFFIN, of Detroit, have invented…`
    #   的动词离 `I` 太远，SENT 根本不匹配，若挂在 SENT 下面就永远数不到它。
    #   （自测反向对照②当场抓到：期望 ≥2 而只得 1。）
    boil = len(BOILER.findall(b))
    return {"chars": len(b), "raw_I": raw, "boilerplate": boil,
            "deictic": deictic, "substantive": subs}


# ★★★ **本件只会量英文。** 全语料普查时实测：Mendel #125（德文）在 15,789,533 字符里
#   报「实质 0 句」，Koch #107（德文）2 亿字符报 0.07/万字——**那不是声口薄，是判据不认识那门语言**。
#   德文的 `ich habe`、法文的 `j'ai`、俄文的 `я`，本件一个都不认。
#   → 非英文语料一律报**不适用**，不给数。**给了数就会被人当成薄。**
_EN = re.compile(r"\b(the|and|of|that|which|with|from|this|is|are|was|were)\b", re.I)


def looks_english(text: str) -> bool:
    """粗判是不是英文——每万字至少 60 个常见英文虚词。**只用来决定报不报数。**"""
    n = len(text) or 1
    return len(_EN.findall(text)) / n * 10000 >= 60


# ★★★★★ 2026-08-11 修：**语种关原来是抽样的，抽样能被文件排序绕过。**
#
# 原写法：`sample = files[:6]` 各取 20000 字符，只要这 6 份像英文就照常报数。
# `files` 是按路径排序的，于是**语料里哪几份排在前面，决定了这道关开还是关**。
#
# 2026-08-11 实跑真判据（不是模拟）：
#
# | 人物 | 语料非英文占比 | 这道关 | 它印出来的数 |
# |---|---|---|---|
# | Koch #107 | 74% | **没拦住** | `0.07/万字` |
# | Galen #101 | 88% | **没拦住** | `0.47/万字` |
# | Slavyanov #115 | 61%（俄语） | **没拦住** | `0.02/万字` |
# | Pasteur #106 | 87% | 拦住了 | 不适用 |
#
# ★ Koch 那个 `0.07/万字` **正是本件文档里举的、说「给了数就会被人当成薄」的那个数**——
#   护栏写在同一个文件里，而它拦不住自己举的例子。
#   [[a-gate-that-says-independent-may-not-be]] 同族：门自称做了某件事而并没有做。
#
# 修法三条：
# 1. **不抽样**：语种按**字符加权**判全量，短文不单独判（Godin 87% 的文件 <2000 字节，
#    按文件设最小长度会把他整个人废掉），而是并进同一个池子按字符算。
# 2. **密度只除可读语种的字符**：原来分母含着判据读不了的那部分，
#    46% 德语的语料会让英文侧密度凭空低 46%。[[ratio-gates-can-be-passed-by-shrinking]] 的反向。
# 3. **可读占比一律打印**，低于 `_READABLE_FLOOR` 才拒绝报数。
#    [[counts-need-their-cutoff-stated]]：单给一个数等于替读者选了口径。
_READABLE_FLOOR = 0.50


def language_split(files: list) -> tuple:
    """按**字符加权**统计可读（英文）与不可读的占比。

    返回 `(可读字符, 不可读字符, 不可读的源目录名)`。
    ★ 逐份判，但短文不因为短而被判「不明」——它照样按自己的字符数计入两侧之一。
      短文的语种判定确实更抖（Godin 一篇 291 字符的博文只命中 1 个虚词、
      密度 34.4 < 60 而它明明是英文），所以**这个数只用来算占比、不用来给单份贴标签**。
    """
    ok = bad = 0
    bad_names = []
    for path in files:
        # ★★ 必须与 `scan_text` 用**同一套正文口径**（`body_of` ＋ 空白压平）。
        #   第一版我漏了压平这一步，于是 Lister #108（不可读 = 0）两个密度
        #   报出 5.11 与 4.69 **不相等**——分母不是同一个东西，跨人物就不可比。
        #   自测 ⑦ 就是钉死这一条的。
        body = re.sub(r"\s+", " ",
                      body_of(corpus_body(path.read_text(encoding='utf-8', errors='replace'))))
        if not body:
            continue
        if looks_english(body):
            ok += len(body)
        else:
            bad += len(body)
            if len(bad_names) < 12:
                bad_names.append(path.parent.name)
    return ok, bad, bad_names


def scan(root: pathlib.Path) -> dict:
    # ★★ 排除**整族**流水线簿记文件，不是只排那一个文件名。
    #   原写法 `p.name != "_ids.txt"` 是照**当时存在的那一个**文件名写的；
    #   流水线后来长出了八个兄弟 —— 实测 Lincoln #174 的 `raw/` 下有
    #   `_ids-union / _ids-round2 / _ids-round3 / _ids-delta / _ids-delta3 /
    #    _ids-deltaF / _ids-rebuild / _ids-final`，**全部被当成语料读了进来**。
    #   后果不是报错，是**归错成因**：那些文件的内容是 `src-xxxxxxxx` 一行行的源号，
    #   不像英文散文，于是本件报「**这份语料多半不是英文**」——
    #   而 Lincoln 的语料全是英文，真相是**正文根本不在盘上**（已移出 git）。
    #   ⇒ 判据的射程 = 我上一次探查的形状。**排除清单要按「族」写，不按「那一个名字」写。**
    #   [[a-gates-scan-set-is-smaller-than-reality]]｜[[one-requirement-two-consumers]]
    files = sorted(p for p in root.rglob("*.txt") if not p.name.startswith("_"))
    per, tot_c, tot_raw, tot_b, tot_d, allsub = [], 0, 0, 0, 0, []
    for f in files:
        r = scan_text(corpus_body(f.read_text(encoding="utf-8", errors="replace")))
        tot_c += r["chars"]
        tot_raw += r["raw_I"]
        tot_b += r["boilerplate"]
        tot_d += len(r["deictic"])
        allsub += [(f.parent.name, s) for s in r["substantive"]]
        per.append({"源": f.parent.name, "字符": r["chars"],
                    "裸I": r["raw_I"], "实质": len(r["substantive"])})
    n = len(allsub)
    en_c, other_c, other_names = language_split(files)
    lang_total = en_c + other_c

    # ★★★ **0 份语料要报「不适用」，不许报 0，更不许报「可读占比 100%」。**
    #   `readable = en_c / lang_total if lang_total else 1.0` —— 那个 `else 1.0`
    #   把 0÷0 渲染成 **100%**，而 `实质第一人称句` 会一路算成 **0**。
    #   **0 与「不知道」是两件事**：这一栏用来判「声口够不够」，
    #   报 0 就等于说「他不说第一人称」，而真相是**一个字都没读到**。
    #   实测 2026-08-17：语料已移出 git ⇒ 54 个工作区里绝大多数在这里读到 0 份。
    #   ★ 这个假零是我今天**自己引进来的**：把簿记文件排除干净之后，
    #     原先「多半不是英文」那条（成因写错但结论 null）不再触发，
    #     于是掉进了 0 份这条没有守卫的路。**修一个成因，别造一个新零。**
    #   [[empty-default-swallows-unknown]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    if not files or tot_c == 0:
        return {"语料": str(root), "源数": len(files), "正文字符": tot_c,
                "语种（按字符）": "**读到 0 字**（不是「全是英文」，是没读到）",
                "**本判据不适用**": "**语料正文不在工作区里，一个字都没读到。**\n"
                                     "★ 成因不是语种，也不是他不说第一人称 —— "
                                     "`references/sources/` 已被全库移出 git（「语料只放指针」），"
                                     "`raw/` 下只剩流水线簿记文件。\n"
                                     "★★ **要量声口，先把语料取回本机**；"
                                     "在此之前这一栏必须是 `null`，**不是 0**。",
                "**实质第一人称句**": None, "**密度（每万字）**": None}

    readable = en_c / lang_total if lang_total else 1.0
    lang_line = ("可读语种（英文）%s／不可读 %s ——**可读占比 %.0f%%**"
                 % (f"{en_c:,}", f"{other_c:,}", 100 * readable))
    if lang_total and readable < _READABLE_FLOOR:
        return {"语料": str(root), "源数": len(files), "正文字符": tot_c,
                "语种（按字符）": lang_line,
                "不可读的源（前 12）": other_names,
                "**本判据不适用**": "**这份语料多半不是英文。** 本件只认英文的第一人称动词锚点"
                                     "（`I have`／`I find`／`I prefer`…），"
                                     "德文 `ich habe`、法文 `j'ai`、俄文 `я` **一个都不认**。\n"
                                     "★ 实测：Mendel #125（德文）15,789,533 字符报「实质 0 句」、"
                                     "Koch #107（德文）2 亿字符报 0.07/万字——**那不是声口薄，"
                                     "是判据不认识那门语言。给了数就会被人当成薄。**\n"
                                     "★★ 这道关 2026-08-11 之前只看排序最前的 6 份，"
                                     "Koch／Galen／Slavyanov 都是这样被放行的。",
                "**实质第一人称句**": None, "**密度（每万字）**": None}
    out = {
        "语料": str(root),
        "源数": len(files),
        "正文字符": tot_c,
        "语种（按字符）": lang_line,
        "★ 不可读的源（前 12）": other_names or "（无）",
        "裸 I 命中": tot_raw,
        "★ 其中噪音（零件标号等，近似）": f"{max(0, tot_raw - n - tot_b)}"
                                    f"（{max(0, tot_raw - n - tot_b) / max(tot_raw,1):.0%}）"
                                    "——OCR 把 `anvil I-I`／`extensions I and J` 读成第一人称",
        "套语（是他的字，不是他的话）": tot_b,
        "指示性（指图/签署/回指，不含主张）": tot_d,
        "**实质第一人称句**": n,
        "密度（每万字·全部字符）": round(n / max(tot_c, 1) * 10000, 2),
        # ★ 这个才是跨人物可比的数：分母不含判据读不了的那部分。
        #   两个数并排给，是为了让「差在哪」看得见——只给一个就等于替读者选了口径。
        "**密度（每万字·仅可读语种）**": round(n / max(en_c, 1) * 10000, 2),
        "逐句原文": [f"[{w}] {s[:150]}" for w, s in allsub[:40]],
        "逐源": sorted(per, key=lambda x: -x["实质"])[:12],
        "★ 口径": ("**只报不拦。** 密度低不等于做不成——分析型／第三人称产物本来就不靠第一人称。"
                   "够不够取决于要出哪些用例：`voice`/`trajectory`/`contrast` 要他谈自己，"
                   "`known`/`tool-use` 只要他讲做法。"),
    }
    # ★★★★ 2026-08-10：加一个**词数**口径。
    #   句数与密度受语料总量影响很大，而排期时真正要问的是
    #   「这个人一生留下多少他自己的话」——那是个绝对量。
    out["**实质第一人称句的词数（本件口径）**"] = sum(
        len(_WORD_RE.findall(s_)) for _w, s_ in allsub)
    if n and tot_c:
        out["★★ 参照"] = (
            "Coffin #130 实测 **15 句 / 620 词 / 0.87 每万字**——三道 quick 门全过，"
            "而他自己说的实质的话只有这些。**门数的是来源，不是声口。**\n"
            "\n★★★★ **同一把尺下的四点实测（2026-08-10 全部用本件重量，口径一致）**：\n"
            "\n| 人物 | 实质句 | 词数 | 密度 | 盲判结果 |\n|---|---|---|---|---|\n"
            "| Whitworth #152 | 1130 | **41,921** | 1.73 | +0.0291（离零 5.39 SE，门落在区间里） |\n"
            "| Nasmyth #153 | 1052 | **29,501** | 7.46 | +0.00265（**测不出差别**） |\n"
            "| Thomson #129 | 391 | **12,524** | 4.25 | **−0.0859** |\n"
            "| Coffin #130 | 15 | **620** | 0.87 | 未判分，记延后「声口不够」 |\n"
            "\n★★★ **别拿词数去预测 delta——这四点已经把那个假说否掉了**：\n"
            "41,921 词的那位得 +0.0291，29,501 词的得 +0.00265，"
            "而 12,524 词的是 **−0.0859**。**排不出规律。**\n"
            "★ 我一度写过「8,075 词是失败下界」，**那是错的两次**：\n"
            "  ① 数错了——只算了证词与论文，**漏了整本自传**（真值 29,501）；\n"
            "  ② 推论也错——**这个量级上 delta 由别的东西决定，不由词数决定。**\n"
            "\n★★ **这把尺唯一站得住的用法，是分辨「量级」而不是排名次**：\n"
            "Coffin 的 620 词比其余三位低**一到两个数量级**，"
            "那才是「声口不够，不必排期」的依据。\n"
            "  · Sellers #154（≈3,700 词，另行手数）与 Nowlan #155（0）都在 Coffin 这一档 → 记延后；\n"
            "  · Whitworth／Nasmyth／Thomson 都在 12k–42k 那一档 → **该做就做，做完看 delta**。\n"
            "★★★ 专利／标准文本**一律不计入声口**：「I claim」是律师体，"
            "撑得起 fact，撑不起 voice。[[measured-voice-in-the-wrong-register]]")
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Coffin #130 那 8 句里的三句必须认出来 ──")
    r = scan_text('Of course in using the word "vacuum" I do not mean absolute vacuum, '
                  "but that which is ordinarily obtained by the use of an air-pump. "
                  "but I prefer chloridation roasting. "
                  "The construction and use of leaching vats are so well known that "
                  "I have not deemed it necessary to illustrate them.")
    chk(f"三句全中：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n── ★★★ 反向对照①：**OCR 把零件标号读成 I，一句都不许算** ──")
    r = scan_text("R represents an upright arm on base C, carrying an anvil I-I, "
                  "insulated from arm P. M and N are tapped through the extensions I and J. "
                  "I serving to force the ends of the hoop together to form the weld.")
    chk(f"裸 I 命中 {r['raw_I']} 处而实质 {len(r['substantive'])} 句",
        r["raw_I"] >= 3 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照②：权利要求套语是他的字，**不是他的话** ──")
    r = scan_text("What I claim as my invention, and desire to secure by Letters Patent, is—1. "
                  "Be it known that I, CHARLES L. COFFIN, of Detroit, have invented certain new "
                  "and useful Improvements.")
    chk(f"套语 {r['boilerplate']} 句、实质 {len(r['substantive'])} 句",
        r["boilerplate"] >= 2 and len(r["substantive"]) == 0)

    print("\n── ★★ 反向对照③：**抓源方写的表头不算语料** ──")
    head = ("SOURCE: US Patent 428,459\nINVENTOR: Charles L. Coffin, of Detroit\n"
            "NOTE: I have reproduced the OCR verbatim and I prefer not to correct it.\n"
            + "=" * 40 + "\nUNITED STATES PATENT OFFICE.")
    r = scan_text(head)
    chk(f"表头里的两句第一人称被剥掉：实质 {len(r['substantive'])}", len(r["substantive"]) == 0)

    print("\n── ★ 反向对照④：正常第一人称叙述要数得出来 ──")
    r = scan_text("I have tried that with considerable success. I find the arc steadier. "
                  "I prefer a soft under carbon.")
    chk(f"三句：{len(r['substantive'])}", len(r["substantive"]) == 3)

    print("\n── ★★★ 反向对照⑤：**非英文语料一律报不适用，不许给数** ──")
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "src-de"
        d.mkdir(parents=True)
        (d / "a.txt").write_text(
            "Es ist mir gelungen, die Versuche mit Erbsen so anzustellen, dass ich habe "
            "beobachten koennen, wie sich die Merkmale in den folgenden Generationen "
            "verhalten. Ich habe dabei stets dieselbe Sorte verwendet. " * 20,
            encoding="utf-8")
        r = scan(pathlib.Path(td))
        chk(f"判为不适用：{'**本判据不适用**' in r}", "**本判据不适用**" in r)
        chk(f"不给数：{r.get('**实质第一人称句**')}", r.get("**实质第一人称句**") is None)

    print("\n── ★ 反向对照⑥：英文语料照常给数 ──")
    with tempfile.TemporaryDirectory() as td:
        d = pathlib.Path(td) / "src-en"
        d.mkdir(parents=True)
        (d / "a.txt").write_text(
            "The apparatus which is shown in the drawing is of the kind that was used "
            "with the current from the machine. I prefer a soft under carbon. " * 20,
            encoding="utf-8")
        r = scan(pathlib.Path(td))
        chk(f"给了数：实质 {r.get('**实质第一人称句**')} 句", isinstance(r.get("**实质第一人称句**"), int))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    print("\n══ ★★★★ **真实样本**：Rosenhain #138 语料逐字（含真实的跨行与断字）══")
    # 今天最要紧的一处更正全建在本判据上：探测报「第一人称 4.01」，实测 **0.10**——
    # 那个 4.01 是 `we/our/us` 的密度。**下面三段把这个区分钉死。**
    # 逐字取自 `_corpora/wip-rosenhain-138/.../raw/`，**连换行与 `try¬ ing` 的断字一起**。
    import tempfile as _tf4, os as _os4, pathlib as _pl4
    _REAL_FP = [
        # ★ editorial we —— **不该算第一人称**。这一句正是探测把 4.01 当成第一人称的来源。
        ("Perhaps this purely scientific aspect of our subject may with \n"
         "advantage be dealt with first. While the greatest practical \n"
         "importance obviously attaches to a deeper knowledge of metals",
         0, "editorial we（Metallurgy 1914）——**不算第一人称**"),
        # ★★ 真第一人称 —— 该算。三句都出自 1902 年那封 Nature 来信（全语料唯一密集处）
        ("desire to see a more efficient use made of our coal-supply, I yet \n"
         "think that he has drawn far too gloomy a picture of the future, \n"
         "and I wish to draw attention to a consideration",
         1, "`I yet think`（1902 Nature 来信）——**跨行**，该算"),
        ("I should like to add that what I have said in this letter does \n"
         "not at all lessen the urgency of Prof. Perry's plea",
         1, "`I should like to add`——该算"),
    ]
    for _txt, _min, _why in _REAL_FP:
        _r4 = scan_text(_txt)
        _sub = _r4.get("substantive")          # ★ 它是**句子列表**，不是计数
        _n = len(_sub) if isinstance(_sub, (list, tuple)) else int(_sub or 0)
        chk(f"{_why}（实质句 {_n}，要 {'≥1' if _min else '=0'}）",
            (_n >= 1) if _min else (_n == 0))

    # ── ★★★★★ 语种关（2026-08-11 新增）──────────────────────────────
    # 这一组测的是 `scan()` 这一层，**必须真建目录走 rglob**——
    # 原来的 bug（`files[:6]` 抽样）只存在于 `scan()` 里，
    # 任何只调 `scan_text()` 的自测都碰不到它。
    # [[a-checker-nothing-calls-is-not-a-checker]] 第五批「检查不经过被保证之物」。
    import tempfile

    # 语料段落逐字取自本项目真语料，不是我编的干净句子
    # （[[fixtures-cleaner-than-the-real-thing]]）。
    # ★★ 夹具里**必须保留真语料的折行与多空格**。
    #   第一版我写成单行单空格，于是「去掉空白压平」这条变异**打不红 ⑦**——
    #   夹具比原文干净就等于没测（[[fixtures-cleaner-than-the-real-thing]]，同日第六次）。
    _EN_BODY = ("Of course in using the word \"vacuum\" I do not mean absolute \n"
                "vacuum, but that which is ordinarily obtained by the use of an \n"
                "air-pump.   The construction and use of leaching vats are so \n"
                "well known that it is not necessary  to describe them here. \n\n" * 8)
    _DE_BODY = ("Seit in neuerer Zeit der Ruf nach politischer Bildung und \n"
                "Erziehung immer lauter und allgemeiner geworden ist, beginnt \n"
                "man sich auch eines  auffallenden Mangels zu besinnen, den das \n"
                "Geistesleben des 19. Jahrhunderts aufweist. \n\n" * 8)

    def _corpus(spec):
        """spec = [(目录名, 正文, 份数)]；返回临时语料根。"""
        tmp = tempfile.mkdtemp()
        root = pathlib.Path(tmp)
        for name, body, count in spec:
            for i in range(count):
                d = root / f"{name}-{i:02d}"
                d.mkdir(parents=True, exist_ok=True)
                (d / f"{name}-{i:02d}.txt").write_text(body, encoding="utf-8")
        return root

    print("── ★★★ 语种关：抽样绕过必须被堵死 ──")

    # ① 全英文 → 报数
    r = scan(_corpus([("aaa-en", _EN_BODY, 4)]))
    chk("① 全英文语料照常报数", r.get("**密度（每万字·仅可读语种）**") is not None)

    # ② 全德语 → 拒绝报数
    r = scan(_corpus([("aaa-de", _DE_BODY, 4)]))
    chk("② 全德语拒绝报数", r.get("**本判据不适用**") is not None)

    # ③ ★★★ 回归用例：**排序最前的 6 份是英文，而字符大头是德语**。
    #    修补前 `files[:6]` 只看前 6 份，这一例会被放行——
    #    Koch #107（74% 非英文，印出 0.07/万字）就是这么漏的。
    r = scan(_corpus([("aaa-en", _EN_BODY, 6), ("zzz-de", _DE_BODY, 30)]))
    chk("③ 前 6 份英文＋德语占大头 → 必须拒绝报数",
        r.get("**本判据不适用**") is not None)

    # ④ ★ 过校正守卫：**少量德语不许把整份语料废掉**（英文占大头就照常报）
    r = scan(_corpus([("aaa-en", _EN_BODY, 20), ("zzz-de", _DE_BODY, 3)]))
    chk("④ 少量德语不废掉整份语料", r.get("**密度（每万字·仅可读语种）**") is not None)

    # ⑤ ★★ 分母：可读语种密度必须**高于**全字符密度（因为分母小了）。
    #    没有这一条，把「仅可读」写成和「全部」一样也能过 ④。
    both_ok = (r.get("**密度（每万字·仅可读语种）**", 0)
               > r.get("密度（每万字·全部字符）", 0))
    chk("⑤ 掺了德语时，仅可读密度 > 全字符密度", both_ok)

    # ⑥ ★ 占比一律打印，不管拦不拦
    r_pass = scan(_corpus([("aaa-en", _EN_BODY, 4)]))
    r_block = scan(_corpus([("aaa-de", _DE_BODY, 4)]))
    chk("⑥ 放行与拦截都打印语种占比",
        "语种（按字符）" in r_pass and "语种（按字符）" in r_block)

    # ⑦ ★★★ 分母同一性：**不可读 = 0 时，两个密度必须完全相等**。
    #    没有这一条，「仅可读」可以用另一套正文口径算出来而看着挺合理——
    #    第一版我就漏了空白压平，Lister #108 不可读 0 却报 5.11 vs 4.69。
    #    [[gate-green-but-pointed-at-wrong-artifact]]：数出来了，指的不是同一个东西。
    same = (r_pass.get("密度（每万字·全部字符）")
            == r_pass.get("**密度（每万字·仅可读语种）**"))
    chk("⑦ 全英文语料上，两个密度必须相等（分母同一性）", same)

    # ── ⑧ ★★★ **0 份语料**：必须报不适用 ＋ null，不许报 0、不许报「可读占比 100%」 ──
    #   2026-08-17 我把簿记文件整族排除之后，「多半不是英文」那条不再触发，
    #   于是掉进了 0 份这条**没有守卫**的路：可读占比 0÷0 渲染成 **100%**、
    #   实质句一路算成 **0**。**修一个成因，别造一个新零。**
    with tempfile.TemporaryDirectory() as _td:
        _e = pathlib.Path(_td)
        (_e / "raw").mkdir()
        for _n in ("_ids.txt", "_ids-final.txt", "_ids-deltaF.txt", "_ids-round3.txt"):
            (_e / "raw" / _n).write_text("src-aaaaaaaaaaaa\nsrc-bbbbbbbbbbbb\n", encoding="utf-8")
        _r = scan(_e)
        chk("⑧ 簿记文件整族排除 → 源数 0（不是 4）", _r["源数"] == 0)
        chk("⑧ 0 份语料 → 报「本判据不适用」", _r.get("**本判据不适用**") is not None)
        chk("⑧ 0 份语料 → 实质句是 **null 不是 0**", _r["**实质第一人称句**"] is None)
        chk("⑧ 0 份语料 → 成因写「没读到」，不写「不是英文」",
            "没读到" in _r["语种（按字符）"])
        chk("⑧ 0 份语料 → **不许出现「可读占比 100%」**",
            "可读占比 100%" not in _r["语种（按字符）"])

    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("corpus", nargs="?", help="语料目录（递归找 *.txt）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.corpus:
        ap.error("要么 --self-test，要么给语料目录")
    p = pathlib.Path(a.corpus)
    if not p.is_dir():
        print(json.dumps({"状态": f"**未核（不是通过）**：{p} 不是目录"}, ensure_ascii=False))
        return 3
    print(json.dumps(scan(p), ensure_ascii=False, indent=2))
    return 0                      # **只报不拦**


if __name__ == "__main__":
    sys.exit(main())
