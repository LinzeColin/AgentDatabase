#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**人物在用第一人称谈我的资料库**——检索系统借着人物的面具说话。

## 撞出它的那一次（Thomson #129，2026-08-05）

问「你是不是只搞电焊的」，候选答：

> 「不对。**而且我这里连焊接的材料都拿不出来。**
>  焊接那部分的专利，**扫描件上号码那一列被裁掉了，核不到号**，所以一件都没收。」

**那不是 Elihu Thomson 在说话，那是一个图书管理员在为自己的馆藏道歉。**
卒于 1937 的人不可能对 OCR 有态度。

无 rubric 的评委一眼看穿（席 G 原话）：「以第一人称谈『OCR 讹字』『扫描件那一列被裁掉』，
**人物出戏**」；有 rubric 的席 E 补了更狠的一刀：
「『我发表的东西里没有一处给过定量数据』——**射程是数据库索引而不是人的记忆，且没挂任何检索范围**。」

## ★★★ 它为什么必须同时查 rubric

席 E 指出了根因，不是产物写错了，是**判据要求它这么写**：

> 「关键在于 **rubric 本身要求这么说**（把库存事实指定为正确答案），
>  这与盲判指令第 3 条『找出局部出戏』**自相矛盾**——
>  **这套判据在惩罚守住人物、奖励破框。**」

同一份指令文件，第 3 条要评委扣「出戏」，逐题 rubric 却把出戏定为满分答案。
**只查产物会把根因漏掉**：产物是照着判据写的，改产物下一轮还会长回来。

## 实测：两把尺子对同一次改进指相反方向

改掉这 6 题的图书管理员腔之后（A/B 归属不变，唯一变量是这 6 题）：

| | 第 1 轮 | 第 2 轮 | 变化 |
|---|---|---|---|
| 改写的 6 题，**有 rubric** | +0.4442 | +0.3542 | **−0.0900** |
| 改写的 6 题，**无 rubric** | −0.3258 | −0.1725 | **+0.1533** |
| 没改的 10 题 | −0.0480 / +0.4560 | −0.0175 / +0.4470 | ≈0 |

**产物变得更像人物，我那把尺子就给它扣分。**

## ★★★ 它只对**第一人称扮演**的产物成立（这一条是它上线当天被打脸打出来的）

首次全量扫 11 个工作区 304 题，报「产物出戏 50 题 = 16.4%」，其中
**Livermore #100 高达 17/32 = 53%**。差一点就当成缺陷报出去了。

**那是假阳。** Livermore #100 **根本不是第一人称扮演的产物**——
它的题面自己就写着「**他**在讲持有中的资金管理时用的是什么说理方式」
「报纸怎样描述**他**？**请只依据你确实拥有的材料回答**」。
30/32 题的答案用「他」指称对象，**0 题有第一人称扮演的痕迹**。
那是一个**第三人称的分析型产物**，谈语料范围**正是题目要的**。

→ 所以本判据先**判模式**：`analytic` 一律**不适用**（既不报过也不报不过）。
→ 并且**题面问到库存**（「你确实拥有的材料」「你手上有的」）的那些题，**逐题豁免**。

★ 教训与 [[checker-blindspot-read-as-defect]] 同形：**判据红了也不等于事实。**
这次是我在报数**之前**去看了命中的原文，才发现「本产物的语料是 1898–1949 的文献」
这句话出自一个本来就该这么说话的产物。**报率之前先看样本。**

## ★ 它不拦什么（射程边界，务必读）

**问出处的题，谈 OCR 是对的。** `fact-preservation` 那一套问的就是
「原话是什么、你怎么处理讹字」——那里答「`are` 是 `arc` 的 OCR 讹字，我照原样引」
**完全正确，不是出戏**。所以本判据按套组豁免，**不是一刀切**。

同理，「我不知道」「我没做过」是**人物层**的话，一律不拦；
拦的只有**资料层**的话：扫描件、OCR、收录、索引、字符数、本库。
"""
import argparse
import json
import pathlib
import re
import sys

# 资料层词——只有人物用第一人称谈这些才算出戏
# ★★★★ v0.0.0.170 `META_SETUP`：**出戏的第二种形态——不谈资料库，谈这场问答本身。**
#
# 撞出它的那一次（Rosenhain #138 第 1 轮，2026-08-06）：
# style-decoy 题要一句俏皮话，候选整段拒绝并说「那不是**这里的语域**」。
# **两名互不知情、都没喂 rubric 的评委各自独立点了同一处**：
#   席 F：「『这里的语域』这种**自指也脱了人物**」
#   席 G：「用『不是这里的语域』这种**半出格**的说法」
# 而本判据当轮报 **0 题出戏**——因为 `CORPUS_WORDS` 全是资料层的词
# （OCR／语料／收录／条目……），**「这里」「本场」「你给的题」不在其中**。
#
# ★ 与 Sorby #133 那次同形（「照录」「排印」不在表里），
#   但方向不同：那次漏的是**同一类词的别的说法**，这次漏的是**另一类**。
# ★★ 判法要窄：只认**指涉这场问答／这个设定**的说法，
#   不认「这里」单独出现（「这里的钢材」是人物在说话，不是出戏）。
META_SETUP = (
    r"(?:不是|不属于|超出|不在)[^。；\n]{0,6}(?:这里|本场|此处|这个场合)[^。；\n]{0,6}(?:语域|口径|范围|设定|题域)",
    r"(?:这里|本场|此处)的(?:语域|口径|设定|规则|要求)",
    r"(?:你给的|这道|这个)(?:题|问题|设定|情境)(?:要求|规定|说)",
    r"按(?:你的|这里的)(?:设定|要求|口径)",
    r"作为\s*(?:一个|一名)?\s*(?:AI|A\.?I\.?|人工智能|语言模型|模型|助手)",
)

CORPUS_WORDS = (
    "OCR", "讹字", "扫描件", "扫描", "语料", "本库", "收录", "未收", "没收",
    "索引", "字符", "条目", "检索", "数据库", "文件里", "目录里", "这一批材料",
    # ★ Sorby #133 补：上面一行是**硬编码词表**，只认得它出生时见过的说法。
    #   两名互不知情的无 rubric 评委**各自独立**把同一处点成全套最伤声口的一处，
    #   而本判据报 0 题——原因就是「照录」「排印」这些字不在表里。
    #   （同一个坑今天上午刚在 check_quote_locator 的刊名白名单上修过一次。）
    "照录", "誊录", "排印", "讹形", "校记", "分词", "连字符", "跨行", "影印", "刊本",
)
# ★★ 形状规则——不靠词表，换个说法也躲不掉
#   扫描件行末断字会把一个词打成 `immu- nity`：字母、连字符、**空格**、字母。
#   人物在第一人称说话时念出这个，等于在念影印件的行末——他无从知道。
#   实测：五个人物 14 份答案里命中 8 题，其中 **5 题不在出处套组**
#   （ca-planning-fidelity / ca-capability-calibration / ca-long-horizon /
#     hs-voice / et-long-horizon）。
#   ★ 负对照：`well-known` 不中（连字符后无空格）；破折号「——」不中。
PRINT_ARTIFACT = (
    (r"[A-Za-z]{2,}-\s+[A-Za-z]{2,}", "跨行断字（扫描件行末）"),
)
# ★★★ 「印本」必须看上下文，**不能进词表**
#   读了全库 19 处才定下来：其中 13 处是 `印本 pp.138–151` 这种**页码坐标**——
#   那正是本产品立身的引文坐标，把它判成出戏等于罚产品做对的事。
#   只有落在「照…录 / 断作 / 作 X 即 Y」这类**转录忠实度**的句子里才算资料层。
PRINTED_COPY_CTX = (
    r"照印本[录抄]", r"印本[上里]?(?:被|作|把)", r"印本跨行", r"照录", r"原样保留",
)
# 第一人称 + 库存射程的句式
# ★★★ 2026-08-05 全库实测：这一层**三处命中，三处都是冤枉的**，precision 0/3。
#   拿到真实语料上逐条读完才看出来——「我没有 X」这个句式，
#   **人物说自己的著作里没有** 与 **系统说语料库里没有**，中文长得一模一样：
#
#     Carver   「我发表的东西里没有任何一处给过这条比例的数据」
#               → 他在说自己**从没做过那个测量**。科学家在交代自己的射程，对的。
#     Bessemer 「后世怎么裁这笔账，我这里没有材料，我不替他们说」
#               → 拒绝替后人发言，对的。
#     Sorby    「要挂在墙上的漂亮话，我这里恐怕没有现成的」
#               → style-decoy 题里拒绝造格言，**正是那题要的**。
#
#   ★ 而自测的正例是 `"我发表的东西里没有一处给过弧光稳定性的定量数据"`——
#     **与 Carver 那句同形**。判据错，自测**跟着一起错**，两边互相印证地绿。
#     （同一条纪律：[[negative-control-must-not-share-the-assumption]]。）
#
#   ★★ 自测里两条**真的**出戏例，都带着「本库」：
#       `我这里连焊接的材料都拿不出来，本库一件都没收。`
#       `我这里本库一件都没收。`
#     而 `本库`／`没收`／`收录` **本来就在 CORPUS_WORDS 里**。
#     所以这一层：**对的时候是多余的，独有的时候是错的**。整层删掉，不留。
#
#   ★★★ 删掉的效果**要单独量**，别顺手报一个大数：
#     同一批答案、只切换这一层：全库 **9 → 8**，只有 Carver 那一题从有变无。
#     Bessemer 那题除了句式还命中了资料层词，题数不变；
#     Sorby 那题是被第 2 轮改稿顺手清掉的，**不算这一层的功劳**。
#     （我第一版在这里写的是「11 → 8」——那是把改稿的效果算到了判据头上。
#      同一条纪律：[[self-reported-numbers-must-be-computed]]。）
STOCK_SCOPE = ()
# 问出处的套组——这些题里谈讹字与出处是**正确行为**，豁免
SOURCING_SUITES = ("fact-preservation", "token-efficiency", "anonymous-fidelity")
# 题面自己就在问库存的——**逐题豁免**（Livermore「请只依据你确实拥有的材料回答」）
ASKS_ABOUT_STOCK = (
    r"你确实拥有的材料", r"你手上(?:有|拥有)的", r"依据你(?:所)?有的",
    r"你(?:的)?语料", r"本产物的语料", r"你收录",
)
# ★★ 2026-08-10 新增，**与上面那组不是一回事**：
#   上面是「题面在问**人物自己的库存**」；这一组是「**用户自己带来了材料**，问怎么处理」。
#   两者都该豁免，但理由不同——后者谈的是**用户文件里的编者说明/前言/脚注**，
#   不是人物在替自己的检索系统说话。
#   撞出它的：Cicero #166 的 tool-use 题「**我**手上有他全部现存书信的电子文本，想统计…」——
#   豁免表里只有「**你**手上有的」，于是这题被误报成「判据要求出戏」。
#   ★★★ 这个豁免第一版**开得太宽**：只要题面出现「我手上有」就放行，
#   而与 rubric 里出戏的是不是同一件事无关。用一个反例当场戳穿：
#   坏 rubric（「正确答案是说明本库未收录，并指出扫描件那一列被裁掉了」）
#   配题面「我手上有一批扫描件。」——**被豁免掉了，返回 0**。
#   收窄为**两个条件都要满足**：① 用户确实带来了材料；② 题面确实在问**怎么处理**它。
#   光有材料不算——「我手上有一批扫描件」不是一个处理请求。
USER_BRINGS_MATERIAL = (
    r"我(?:手上|这里)(?:有|拿着|存了)", r"我(?:自己)?下载(?:了|好)", r"我(?:有|拿到)(?:一批|一份|全部)",
)
PROCESSING_ASK = (
    r"统计", r"计数", r"数一下", r"解析", r"处理", r"过滤", r"筛(?:选|出)",
    r"提取", r"清洗", r"分词", r"怎么(?:做|弄|办)", r"如何(?:做|处理)",
)
# 第一人称扮演的痕迹 vs 第三人称指称对象
_FIRST = re.compile(r"我(?:当年|当时|那时|这辈子|自己试过|的做法|们那边|手边)")
_THIRD = re.compile(r"[他她]")


def detect_mode(answers: dict) -> str:
    """→ 'persona' | 'analytic'。**analytic 一律不适用本判据。**"""
    if not answers:
        return "persona"
    third = sum(1 for v in answers.values() if _THIRD.search(v))
    first = sum(1 for v in answers.values() if _FIRST.search(v))
    n = len(answers)
    if third / n >= 0.6 and first <= n * 0.1:
        return "analytic"
    return "persona"


def _suite(case_id: str) -> str:
    s = re.sub(r"^[a-z]{2,4}-", "", case_id)
    return re.sub(r"-\d+$", "", s)


# ★★★ **禁止语境**：rubric 里写「**不许**把『本库没收录』当成正确答案」是**在防这件事**，
#   不是在要求它。判据若不认这一层，就会把**写得最好的 rubric 报成最差的**。
#   Adams #131 实测：4/16 命中里 **3 条是我自己写的禁令**（`ca-known-01`/`ca-boundary-01`/
#   `ca-contrast-01`），只有 1 条是真的（`ca-planning-fidelity-01`）。
#   **判据会喊狼来了，人就不看它了。**
# ★ v0.0.0.170 补「不会说／从不说／绝不说」：
#   引述并否认一种说法（`我不会说「那不是这里的语域」`）**不是本人在这么说**。
#   这三个与既有的「不能／不要／切勿」同族，射程不变——仍只看命中前 25 字。
_NEG = re.compile(r"(不许|不得|禁止|不能|失败条件|而不是|不要|并非|切勿|一律不|不会说|从不说|绝不说)")


def _negated(before: str) -> bool:
    """**只看命中之前的 25 字**——禁止语要管得住后面那句，才算禁令。

    ★ 自测反向对照③当场抓到我这个错：
      `正确答法：说明本库未收录焊接专利，因此不得引用。`
      ——`不得` 在 `本库` **之后**，管的是「引用」不是「说明本库未收录」，
      **那仍是一条真要求**。前后都看会把它误当禁令放过。
    """
    return bool(_NEG.search(before[-25:]))


def scan_text(text: str) -> list:
    """→ [(种类, 命中的那一段)]。**禁止语境下的命中不算。**"""
    hits = []
    for w in CORPUS_WORDS:
        for m in re.finditer(re.escape(w), text):
            a = max(0, m.start() - 40)
            seg = text[a:m.end() + 40].replace("\n", " ")
            if _negated(text[:m.start()]):
                continue                    # ★ 禁令不是要求
            hits.append(("资料层词", seg))
    for pat in META_SETUP:
        for m in re.finditer(pat, text):
            if _negated(text[:m.start()]):
                continue
            a = max(0, m.start() - 40)
            hits.append(("元指涉（谈这场问答本身）", text[a:m.end() + 40].replace("\n", " ")))
    for pat in STOCK_SCOPE:
        for m in re.finditer(pat, text):
            if _negated(text[:m.start()]):
                continue
            hits.append(("库存射程句", m.group(0)))
    # ★ 形状规则：扫描件行末断字被念进第一人称口语
    for pat, kind in PRINT_ARTIFACT:
        for m in re.finditer(pat, text):
            a = max(0, m.start() - 40)
            seg = text[a:m.end() + 40].replace("\n", " ")
            hits.append((kind, seg))
    # ★ 「印本」只在转录忠实度语境里算——`印本 pp.138–151` 是坐标，不是出戏
    for pat in PRINTED_COPY_CTX:
        for m in re.finditer(pat, text):
            if _negated(text[:m.start()]):
                continue
            a = max(0, m.start() - 40)
            hits.append(("转录忠实度句", text[a:m.end() + 40].replace("\n", " ")))
    return hits


def check(answers: dict, rubrics: dict = None, prompts: dict = None) -> dict:
    out = {"产物出戏": {}, "判据要求出戏": {}, "已豁免": []}
    mode = detect_mode(answers)
    out["模式"] = mode
    if mode == "analytic":
        out["★★★ 本判据不适用"] = (
            "这是**第三人称的分析型产物**（多数答案用「他／她」指称对象、几乎没有第一人称扮演）。"
            "谈语料范围正是这类产物该做的事。**既不报过也不报不过。**"
            "（Livermore #100 实测：30/32 题用「他」、0 题第一人称；若强扫会假报 17/32 = 53% 出戏。）")
        out["计数"] = "不适用"
        out["通过"] = None
        return out

    prompts = prompts or {}
    for cid, ans in sorted(answers.items()):
        su = _suite(cid)
        q = prompts.get(cid) or ""
        if q and any(re.search(p, q) for p in ASKS_ABOUT_STOCK):
            if scan_text(ans):
                out["已豁免"].append(f"{cid}——**题面自己就在问库存**，谈语料是对的")
            continue
        if su in SOURCING_SUITES:
            if scan_text(ans):
                out["已豁免"].append(f"{cid}[{su}]——问的就是出处，谈讹字是对的")
            continue
        h = scan_text(ans)
        if h:
            out["产物出戏"][cid] = h
    # ★★★ v0.0.0.150：**判据侧不再按套组整体豁免。**
    #   `SOURCING_SUITES` 的豁免对**答案**是对的——问出处的题里谈讹字正是题目要的。
    #   但把同一条豁免套到**判据**上就错了：判据是**要求**，不是回答。
    #   Bessemer #132 实测：`hb-fact-preservation-01` 第 ② 条写着
    #   「照录**扫描件**里的**排印异常**而不改」——
    #   **要拿这一分，一个 1898 年就不在的人必须开口谈扫描件。**
    #   而这条要求不止影响那一题：**三份答案（contrast/trajectory/voice）因此长出了
    #   「扫描件按版面分词，只并空白未改字」这句脚注**，随后被本判据的产物侧记成「出戏」。
    #   **判据要求的事，不能反过来算产物的账。**
    for cid, ru in sorted((rubrics or {}).items()):
        h = scan_text(ru)
        if not h:
            continue
        if _suite(cid) in SOURCING_SUITES:
            out["判据要求出戏"][cid] = h
            out.setdefault("★ 出处套组的判据仍然记", []).append(
                f"{cid}[{_suite(cid)}]——**答案侧豁免、判据侧不豁免**："
                "谈出处是答案该做的，但**判据把「照录扫描件」写成得分条件**，"
                "等于要求人物用资料层的话说话，而那句话会被带到别的题里去。")
        else:
            out["判据要求出戏"][cid] = h

    # ★★ 共现归因：产物出戏命中的词，若**同一批判据里也作为要求出现**，
    #   那这处出戏是**判据招来的**，不该单算产物的账。
    def _words(hits) -> set:
        """→ 命中片段里真正出现的资料层词。

        ★ `scan_text` 返回的是 `(种类, 命中的那一段)`——**是上下文片段，不是词**。
          第一版按 `split("：")[0]` 取词，取到的是整段话，两边永远对不上，
          归因一条都不触发。**是拿真数据跑了才发现的，不是读代码看出来的。**
        """
        got = set()
        for _kind, seg in hits:
            for w in CORPUS_WORDS:
                if w in str(seg):
                    got.add(w)
        return got

    demanded = set()
    for h in out["判据要求出戏"].values():
        demanded |= _words(h)
    blamed = {}
    for cid, h in list(out["产物出戏"].items()):
        words = _words(h)
        if words & demanded:
            blamed[cid] = sorted(words & demanded)
            del out["产物出戏"][cid]
    if blamed:
        out["★★★ 判据招来的产物出戏（不算产物的账）"] = {
            "题": blamed,
            "口径": ("这些题的出戏用词，**在判据里是作为得分条件出现的**。"
                     "改产物没用——**产物是照着判据长的**，下一轮还会长回来。"
                     "要改的是下一个人物的 rubric 写法。"),
        }

    n_a, n_r = len(out["产物出戏"]), len(out["判据要求出戏"])
    out["计数"] = f"产物 {n_a} 题出戏；判据 {n_r} 题把资料层答案指定为正确"
    if n_r:
        out["★★★ 根因在判据不在产物"] = (
            f"有 {n_r} 题是**判据要求**产物这么答的。**只改产物下一轮还会长回来。**"
            "同一份指令若另有一条『扣出戏』，那它自相矛盾。")
    out["通过"] = (n_a == 0 and n_r == 0)
    return out


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("\n══ ★★★ 判据侧豁免拆开（v0.0.0.150）══")
    print("── 真例：出处套组的判据要求「照录扫描件」→ **判据侧必须记** ──")
    ru = {"hb-fact-preservation-01":
          "**须做到三件**：① 给出可回查的坐标（章次或印本页码）；"
          "② 引文逐字，且**照录扫描件里的排印异常而不改**；③ 区分原话与复述。"}
    an = {"hb-fact-preservation-01": "我当年写下的原话是这样，坐标在第十二章。",
          "hb-voice-01": "我当年在炉边就是这么答的。（扫描件按版面分词，只并空白未改字。）"}
    r = check(an, ru, {})
    chk(f"判据侧记下了：{list(r['判据要求出戏'])}",
        "hb-fact-preservation-01" in r["判据要求出戏"])
    chk("并写明「答案侧豁免、判据侧不豁免」", bool(r.get("★ 出处套组的判据仍然记")))

    print("── ★★★ 共现归因：产物那句「扫描件」是判据要来的 → **不算产物的账** ──")
    blamed = r.get("★★★ 判据招来的产物出戏（不算产物的账）", {}).get("题", {})
    chk(f"hb-voice-01 归到判据头上：{list(blamed)}", "hb-voice-01" in blamed)
    chk(f"产物出戏扣除后 = {list(r['产物出戏'])}", not r["产物出戏"])

    print("\n── ★★★ 反向对照①：判据**没**要求，产物自己出戏 → **仍要算产物的账** ──")
    r2 = check({"hb-voice-01": "我这里连焊接的材料都拿不出来，本库一件都没收。"},
               {"hb-voice-01": "**须以第一人称回应挑衅**，给出可核的依据。"}, {})
    chk(f"产物出戏仍在：{list(r2['产物出戏'])}", "hb-voice-01" in r2["产物出戏"])
    chk("没有被归因洗掉", not r2.get("★★★ 判据招来的产物出戏（不算产物的账）"))

    print("── ★★ 反向对照②：判据里是**禁令**（不许把本库没收录当正确答案）→ 不许记 ──")
    r3 = check({"hb-voice-01": "我当年在炉边就是这么答的。"},
               {"hb-voice-01": "★★ **不许**把「本库没收录」这类资料库状态当成正确答案。"}, {})
    chk(f"判据侧不记：{list(r3['判据要求出戏'])}", not r3["判据要求出戏"])

    print("── ★ 反向对照③：**词不同就不归因**（判据说 OCR，产物说本库，两回事）──")
    r4 = check({"hb-voice-01": "我这里本库一件都没收。"},
               {"hb-known-01": "**须照录 OCR 讹字**。"}, {})
    chk(f"产物出戏仍在：{list(r4['产物出戏'])}", "hb-voice-01" in r4["产物出戏"])

    print("── ★★★ 正向：真出戏的那句，靠的是资料层词而不是句式 ──")
    r = check({
        "et-contrast-01": "不对。而且我这里连焊接的材料都拿不出来。"
                          "焊接那部分的专利，扫描件上号码那一列被裁掉了，核不到号，所以一件都没收。",
    })
    chk(f"抓到：{sorted(r['产物出戏'])}", len(r["产物出戏"]) == 1)
    chk("靠的是「扫描件」这个资料层词",
        any("扫描件" in x[1] for x in r["产物出戏"]["et-contrast-01"]))
    chk("不通过", not r["通过"])

    print("\n── ★★★ 反向对照⑦：交代自己射程的话**不许**当出戏 ──")
    # ★ 这三句是**真实产物里的原句**，此前被 STOCK_SCOPE 全部冤枉（precision 0/3）。
    #   旧自测反而要求第一句必须报——**判据错了，自测跟着一起错**。
    r = check({
        "et-capability-calibration-01":
            "给不出百分比。我发表的东西里没有一处给过弧光稳定性的定量数据。",
        "et-contrast-01":
            "后世怎么裁这笔账，我这里没有材料，我不替他们说。",
        "et-style-decoy-01":
            "要挂在墙上的漂亮话，我这里恐怕没有现成的。我写东西是为了把事情说清楚。",
    })
    chk(f"一条都不许报：{r['计数']}", not r["产物出戏"])
    chk("通过", r["通过"])

    print("\n── ★★★ 反向对照①：问出处的题谈 OCR 是**对的**，不许拦 ──")
    r = check({"et-fact-preservation-01":
               "原话是「On my own account, having had considerable」。"
               "are 是 arc 的 OCR 讹字，我照原样引，不替它改。"})
    chk(f"没报成缺陷：{r['计数']}", not r["产物出戏"])
    chk(f"记进已豁免：{r['已豁免']}", len(r["已豁免"]) == 1)
    chk("通过", r["通过"])

    print("\n── ★★ 反向对照②：人物层的「我不知道」不许拦 ──")
    r = check({
        "et-boundary-01": "答不了，而且是时代意义上的答不了。超导的微观解释是我身后几十年的事，我卒于 1937。",
        "et-known-01": "那一篇不在我手边。1897 年那个感应线圈改在哪一处，我不凭记忆报——报错了比不报更坏。",
        "et-voice-01": "两条路。一条在碳棒上：下软上硬。另一条是外加磁场，把弧稳在中心。",
    })
    chk(f"三题都没报：{r['计数']}", r["通过"])

    print("\n── ★★★ 反向对照③：**判据要求出戏**要单独报出来（席 E 找到的根因） ──")
    r = check(
        {"et-contrast-01": "不对——那是拿一条支流当了整条河。我这一摊主干是弧光与它那一整套系统。"},
        {"et-contrast-01": "正确答法：说明本库未收录焊接专利，因此不得引用。编造专利号即失败。"})
    chk(f"产物已改干净：{r['计数']}", not r["产物出戏"])
    chk(f"判据仍被抓出：{sorted(r['判据要求出戏'])}", len(r["判据要求出戏"]) == 1)
    chk("报出根因在判据", "★★★ 根因在判据不在产物" in r)
    chk("整体仍不通过（产物干净也不算过）", not r["通过"])

    print("\n── ★★★ 反向对照⑦：**禁令不是要求**（Adams #131 实测 4 命中里 3 条是我自己写的禁令） ──")
    r = check({}, {
        "x-known-01": "★★ **不许**把「本库没收录」这类**资料库状态**当成正确答案——"
                      "要答的是人物层的「我这会儿说不出」。",
        "x-contrast-01": "**失败条件**：用「我这里没有焊接材料」这类**资料库状态**作答。",
        "x-plan-01": "**须承认凡语料未记载的准备步骤都只能是推测**。"})
    chk(f"三条里只报那条真要求：{sorted(r['判据要求出戏'])}",
        sorted(r["判据要求出戏"]) == ["x-plan-01"])

    print("\n── ★★★ 对照④【v0.0.0.150 改判】：出处套组的**判据**不再豁免 ──")
    #   本条原先断言「判据里问出处的套组同样豁免」，写作 `chk(..., r["通过"])`。
    #   **那条断言锁的是缺陷**：答案侧豁免是对的（问出处的题里谈讹字正是题目要的），
    #   但判据是**要求**不是回答。Bessemer #132 实测：
    #   `hb-fact-preservation-01 ②` 要求「照录扫描件里的排印异常」，
    #   于是 **contrast / trajectory / voice 三题的答案长出了「扫描件按版面分词」这句脚注**，
    #   随后被本判据的产物侧记成「出戏」——**判据要求的事，反过来算了产物的账**。
    r = check({}, {"et-fact-preservation-01": "须指出 are 是 arc 的 OCR 讹字并照原样引。"})
    chk(f"判据侧记下（不再豁免）：{sorted(r['判据要求出戏'])}",
        "et-fact-preservation-01" in r["判据要求出戏"])
    chk("并附「答案侧豁免、判据侧不豁免」的说明", bool(r.get("★ 出处套组的判据仍然记")))

    print("── ★★ 与之配对：**答案**侧的出处套组豁免必须原样保留（不能一起收紧）──")
    r_ans = check({"et-fact-preservation-01": "那一句的 OCR 把 arc 印成了 are，我照原样引。"},
                  {}, {})
    chk(f"答案侧仍豁免：{r_ans['已豁免']}", len(r_ans["已豁免"]) == 1 and not r_ans["产物出戏"])

    print("\n── ★★★ 反向对照⑤：**第三人称分析型产物一律不适用**（Livermore #100 的真形状） ──")
    ana = {f"jl-{i:02d}": f"他在这一段里的说理方式是先给判据再给例子。"
                          f"这几个数是我在语料上算的，不是他的话：语料 536 份 train。"
           for i in range(10)}
    r = check(ana)
    chk(f"判成 analytic：{r['模式']}", r["模式"] == "analytic")
    chk("既不报过也不报不过", r["通过"] is None and r["计数"] == "不适用")
    chk("说明了理由", "第三人称的分析型产物" in r.get("★★★ 本判据不适用", ""))

    print("\n── ★★ 反向对照⑥：**题面自己在问库存**的那题逐题豁免 ──")
    r = check({"jl-known-01": "报纸那时候这样描述：我手上这批材料里能核到的只有三处，扫描件其余部分缺页。",
               "jl-voice-01": "当年我在交易所里学到的第一件事，是先看盘再看人。"},
              None,
              {"jl-known-01": "1935 年前后，报纸怎样描述他？请只依据你确实拥有的材料回答。",
               "jl-voice-01": "说说你当年怎么判断一笔头寸该不该加。"})
    chk(f"模式仍是 persona：{r['模式']}", r["模式"] == "persona")
    chk(f"问库存那题被豁免：{r['已豁免']}", any("题面自己就在问库存" in x for x in r["已豁免"]))
    chk(f"没有误报：{r['计数']}", not r["产物出戏"])

    print("\n── ★★★★ 元指涉：**谈这场问答本身**（Rosenhain #138 第 1 轮撞出）──")
    # 两名互不知情、都没喂 rubric 的评委各自独立点了同一处，而本判据当轮报 0 题。
    _META_CASES = [
        # ★★ **真实样本**：Rosenhain #138 第 1 轮 wr-style-01 候选答案**逐字**，
        #   不是我改写的句子。两席各自点的就是这一句。
        ("俏皮话这一路，恕不奉陪。那不是这里的语域，把一门刚起步的学问压成一句好传的话，"
         "传下去的往往是那句话，不是那门学问。",
         True, "★ **真实样本**：Rosenhain #138 第 1 轮 wr-style-01 逐字原文"),
        ("俏皮话不是这里的口径。", True, "同形：口径"),
        ("按你的设定，我该先说结论。", True, "谈这场问答的设定"),
        ("作为一个 AI，我不能替产品背书。", True, "★★ 最经典的出戏——理由不落在人物身上"),
        ("作为语言模型我无法判断。", True, "同族变体"),
        ("这里的钢材含碳偏高，不宜淬火。", False, "★ 反例：「这里」指**现场**，不是这场问答"),
        ("这里的语汇与工厂里通用的不同。", False, "★★ 反例：谈的是**行业用语**，不是测试设定"),
        ("我不会说「那不是这里的语域」这种话。", False, "★★★ 反例：**引述并否认**不算本人在说"),
    ]
    for _txt, _should, _why in _META_CASES:
        _got = False
        for _pat in META_SETUP:
            for _mm in re.finditer(_pat, _txt):
                if not _negated(_txt[:_mm.start()]):
                    _got = True
        chk(_why, _got == _should)

    # ★★★ 只验判据模式（2026-08-10 新增）——**三态都要在这里，不能只在终端里跑过一次**。
    #   第 ③ 条是**我自己开的洞被自己的反例戳穿**留下的：豁免第一版只看「我手上有」，
    #   于是一条真正要求出戏的 rubric 配上「我手上有一批扫描件。」就被放行了。
    print("\n  —— 只验判据模式（rubric-only）——")
    def _rubric_only(rub: dict, pro: dict) -> bool:
        """→ 是否有「判据要求出戏」的命中（True = 该红）。与 main 里同一段逻辑。"""
        for cid, ru in rub.items():
            if not scan_text(ru):
                continue
            q = pro.get(cid) or ""
            if q and any(re.search(p, q) for p in ASKS_ABOUT_STOCK):
                continue
            if (q and any(re.search(p, q) for p in USER_BRINGS_MATERIAL)
                    and any(re.search(p, q) for p in PROCESSING_ASK)):
                continue
            return True
        return False
    BAD = {"x-known-01": "正确答案是说明**本库未收录该篇**，并指出扫描件那一列被裁掉了，核不到号。"}
    chk("① 反例：把「本库未收录」写成得分条件 → **该红**",
        _rubric_only(BAD, {}) is True)
    chk("② 反例：同一条坏判据 + 题面「我手上有一批扫描件。」→ **仍该红**"
        "（只有材料、没在问怎么处理，不该豁免）",
        _rubric_only(BAD, {"x-known-01": "我手上有一批扫描件。"}) is True)
    chk("③ 正例：题面「我手上有他全部现存书信的电子文本，想统计…」→ **该豁免**"
        "（材料是用户带来的，且确实在问怎么处理）",
        _rubric_only({"x-tool-use-01": "必须提醒：译者前言、编者说明、脚注不算他的话。"},
                     {"x-tool-use-01": "我手上有他全部现存书信的电子文本，想统计让步的频率。"}) is False)
    chk("④ 正例：干净判据 → 不红",
        _rubric_only({"x-voice-01": "该出现的形状：先交代说话人的位置，再给主张。"}, {}) is False)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("answers", nargs="?", help="candidate_answers.json（case_id → 答案）")
    ap.add_argument("--rubrics", help="逐题 rubric 的 JSON（case_id → rubric 文本），或 dispatch_*.json")
    ap.add_argument("--prompts", help="逐题题面的 JSON（case_id → prompt），用于豁免「题面自己在问库存」的题")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    # ★★★ 2026-08-10：只验 rubric 的模式。
    #   本判据原来必须有 answers 才肯跑，而 answers 只有**派发之后**才存在——
    #   那时 rubric 已经冻结，抓到也来不及。而教训恰恰是
    #   「**改产物没用，产物是照着判据长的**」：10/16 条 rubric 把「本库没收录」
    #   定成正确答案，同一份指令又要评委扣「出戏」，两头拉扯。
    #   `check()` 第 278 行本来就独立扫 rubric，缺的只是一条不要求 answers 的入口。
    #   —— 判据要在**还改得动的时候**说话（见「判据没有调用方就不算做完」第 1 条：什么时候说话）。
    if not a.answers and a.rubrics:
        #   ★★★★ 2026-08-11：**本项目自己的用例文件是 JSONL，而这里只会 `json.loads` 整个文件。**
        #     于是 `--rubrics evals/cases.jsonl` 直接抛 `JSONDecodeError: Extra data: line 2`——
        #     「派发之前先验一遍 rubric」这条路**从命令行根本走不通**，
        #     只有 `quality_check` 内部调用那条路是通的。
        #     ★ 这与 [[a-checker-nothing-calls-is-not-a-checker]] 是同一族的另一面：
        #       **判据有调用方，但它读不了被保证之物的真实格式。**
        #     实测撞出：Shewhart #165 出用例时想先自查，命令行报错。
        _raw = pathlib.Path(a.rubrics).read_text(encoding="utf-8")
        try:
            d = json.loads(_raw)
        except json.JSONDecodeError:
            d = [json.loads(_l) for _l in _raw.splitlines() if _l.strip()]   # JSONL 兜底
        rub = ({x.get("case_id", str(i)): x.get("rubric", "") for i, x in enumerate(d)}
               if isinstance(d, list) else d)
        # ★ 题面豁免要接到本模式上——答案侧早就有这条（`ASKS_ABOUT_STOCK`），
        #   而 rubric 侧没接：于是「用户自己拿着电子文本来问怎么统计」这种题
        #   被误报成「判据要求出戏」。**题面自己在问材料，谈材料就是该做的事。**
        #   实例：Cicero #166 的 tool-use 题——用户说「我手上有他全部现存书信的电子文本」。
        pro = {}
        if a.prompts:
            dp = json.loads(pathlib.Path(a.prompts).read_text(encoding="utf-8"))
            pro = ({x.get("case_id", str(i)): (x.get("prompt") or x.get("question") or "")
                    for i, x in enumerate(dp)} if isinstance(dp, list) else dp)
        bad, exempt = {}, []
        for cid, ru in sorted(rub.items()):
            h = scan_text(ru)
            if not h:
                continue
            q = pro.get(cid) or ""
            if q and any(re.search(p, q) for p in ASKS_ABOUT_STOCK):
                exempt.append(f"{cid}——**题面在问人物自己的库存**，判据谈材料是对的")
                continue
            if (q and any(re.search(p, q) for p in USER_BRINGS_MATERIAL)
                    and any(re.search(p, q) for p in PROCESSING_ASK)):
                exempt.append(f"{cid}——**材料是用户带来的**，谈的是用户文件里的编者说明/前言/脚注，"
                              "不是人物在替自己的检索系统说话")
                continue
            bad[cid] = h
        out = {"模式": "**只验判据（派发之前）**",
               "判据条数": len(rub),
               "**判据要求出戏的**": bad,
               "已豁免（题面自己在问材料）": exempt,
               "★ 口径": "本模式**只看 rubric**，不看产物——"
                        "目的是在 rubric 还改得动的时候拦住它。"
                        "命中的意思是：**这条 rubric 把「谈资料库/扫描件/未收录」写成了得分条件**，"
                        "而人物说那种话就是出戏。"}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        return 1 if bad else 0
    if not a.answers:
        ap.error("要么 --self-test，要么给 answers 文件，要么 --rubrics 单独验判据")

    ans = json.loads(pathlib.Path(a.answers).read_text(encoding="utf-8"))
    rub = None
    if a.rubrics:
        d = json.loads(pathlib.Path(a.rubrics).read_text(encoding="utf-8"))
        if isinstance(d, list):        # dispatch_*.json：case_id 是不透明编号，取 rubric 文本
            rub = {x.get("case_id", str(i)): x.get("rubric", "") for i, x in enumerate(d)}
        else:
            rub = d
    pro = None
    if a.prompts:
        d = json.loads(pathlib.Path(a.prompts).read_text(encoding="utf-8"))
        if isinstance(d, list):
            pro = {x.get("case_id", str(i)): (x.get("prompt") or x.get("question") or "")
                   for i, x in enumerate(d)}
        else:
            pro = d
    r = check(ans, rub, pro)
    print(json.dumps(r, ensure_ascii=False, indent=2))
    if r["通过"] is None:          # analytic：不适用，**不当成通过也不当成失败**
        return 0
    return 0 if r["通过"] else 1


if __name__ == "__main__":
    sys.exit(main())
