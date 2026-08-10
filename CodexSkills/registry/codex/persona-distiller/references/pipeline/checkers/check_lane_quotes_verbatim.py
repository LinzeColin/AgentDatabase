#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**六道研究稿里的每一条逐字引文，都要能在语料里原样找到。**

## 为什么要它（Roberts-Austen #135 实测，2026-08-06）

六道写完、逐条都标了 `source_id`，看上去无懈可击。
写这个脚本回原文比对，**31 条里 2 条对不上**：

| 道 | 我们写的 | 语料原文 |
|---|---|---|
| 01-writings | `re-stated on the first page` | `re-stated on' the first page`（撇号是 OCR 讹形，**被抹平了**） |
| 02-conversations | `Prof. Barrett's` | `Prof. Barrett’s`（弯撇号被改成直撇号） |
| 05-decisions | `communicated to the Royal Society, and` | `communicated to the Koyal` **`Feb. 1897. ALLOTS RESEARCH. 57`** `Society, and` |

★★★ **第三条是最难查的一种**：`Koyal` 被悄悄改回 `Royal`，
而且**句子中间横着一道版口，被抹掉之后两半缝成了一句连续的引文**。
**缝合处不留任何痕迹，引文读起来完全通顺。**

这与 [[verbatim-is-not-understood]] 记的是同一件事的另一半：
逐字抄 OCR 是对的，**而改了讹字再当逐字引文用**，一天里出过两次、
两个工作区、**都不是门抓到的**。现在它是门抓的了。

## 判法

引文 = markdown 里 `>` 引用块中**反引号包起来**的段落。

三条要害，缺一不可：

1. **在 `——` 归属行处切开。** 一个 `>` 块里常有「引文＋出处＋下一条引文」，
   不切就会把两条粘成一条，**制造假的「对不上」**（第一版就这样报了 3 条假失败）。
2. **只取以 ASCII 为主的段落。** 中文散文里的 `字段名`／`source_id` 不是引文；
   第二版按「所有反引号」取，**97 条里 88 条是噪声**。
3. ★★★ **`[版口：…]` 标记要按「分段各自命中」验，不许只验前缀。**
   写这条的时候我一度让它只比对前半句就算过——
   **那等于给自己开了一道永远绿的门。**

## 只报不拦？**不。**

引文对不上就是引文对不上。**退出码非零**——
「照录」是这个项目的立身之本，不是风格问题。
"""

import argparse
import json
import pathlib
import re
import sys

_PAGE_FURNITURE = re.compile(r"\[版口：([^\]]*)\]")

# ★★★ 引文里**允许**的三类排版记号，比对前一律剥掉。
#   这三类是全库回扫撞出来的（Lister 6/6、Pasteur 4/4 全红，去读才知道不是缺陷）：
#     · markdown 着重号：`**antiseptic principle**`——道稿作者给引文里的词加粗；
#     · 行内 HTML：`D<sup>r</sup> Lannelongue`——把 `Dr` 排成上标；
#     · 法/俄式引号 `« »`、弯引号——包在引文外面。
#   ★ 它们与「悄悄改讹字」**不是一类**：加粗是**看得见的**编辑记号，
#     而 `Koyal`→`Royal` 不留痕迹。**看得见的允许，不留痕迹的不允许。**
# ★★★★ 2026-08-07：`</?[A-Za-z][^>]*>` 这一支**吃掉了 46% 的语料**。
#   Whitworth #152 的 `in.ernet.dli.2015.43651`（泰晤士报讣告重印本）实测：
#
#       全文 983,190 字符 → `_MARKUP` 之后 531,425 字符
#       「标签」匹配 **156 处，删掉 450,343 字符（45.8%）**，最长一处一口吃掉 **46,006 字符**
#       而真正该删的引号类只有 **1,424** 个
#
#   起因：OCR 里有孤立的 `<`（`<lied` 是 `plied` 的讹形），`[^>]*` **不禁换行**，
#   于是从那个 `<` 一路吃到几万字符之外的下一个 `>`，中间全是正常散文。
#   后果方向是**假阴**——真引文被报成「对不上」，不会造成假过；
#   但「0 条对不上」是在**残缺语料**上得出的，落在被删区间里的引文一律冤枉。
#   ★ 抓到它的是 Whitworth 的 Hampson 那句：`Hampson` 在归一副本里明明有 2 处，
#     而 `load_corpus` 交给比对的文本里是 **0 处**。
#
#   修法：真 HTML 标签**既短又不跨行**。加 `\n` 排除 + 长度上限 120。
#   ★ 上限不是拍的：本文件里最长的**真**标签是 0 个（这批语料根本没有 HTML），
#     而误吃的 156 处最短的一处也有 74 字符——120 这个界把两侧分开还有余量。
_MARKUP = re.compile(r"\*\*|\*|__|</?[A-Za-z][^>\n]{0,120}>|[«»“”\"]")
# 显式省略号 = 作者声明「这里略去了」，与 `[版口：…]` 同类，按分段各自命中验
_ELISION = re.compile(r"\s*(?:\.\.\.|…)\s*")


# ★★ 印本的**折行连字**与**破折号**在不同扫本里形态不同，比对前一律归一。
#   Lister 实测：同一段话在三份来源里分别印成
#     `same—namely` / `same — namely`，`circum- stances` / `circum¬ stances` / `ac¬ cordance`
#   **这是扫本的差别，不是引文改了字**——与「悄悄改讹字」不是一类。
_HYPHEN_BREAK = re.compile(r"[-¬­]\s+")          # 行末折行连字（含 OCR 的 ¬ 与软连字）
_DASHES = re.compile(r"[—–−]")
# 标点前的空白（OCR 版面产物，尤以德文/法文排印为多）
# 撇号的各种排印形态——OCR 与手打之间必然不一致，**归一不动字母**
_APOSTROPHE = re.compile(r"[\u2018\u2019\u201b\u02bc\u00b4`]")
_SPACE_BEFORE_PUNCT = re.compile(r"\s+([,.;:!?)\]])")
# 中日韩标点：出现即说明这是我写的散文，不是英文逐字引文
# ★★★★ **`—` 与 `…` 有意不在这个集合里。**
#   第一版把它们放进来了，结果全库引文总数 **390 → 358**，一次静默吃掉 32 条**本来对得上**的引文：
#     · `—` 是英文 OCR 里极常见的破折号，真引文天天带它；
#     · `…` **是本判据自己的省略号语法**（`_ELISION` 要按它分段验），
#       把带 `…` 的引文整条滤掉，等于把省略号那条功能拆了。
#   ★ 抓到它的是**分母**：我把「引文总数」和「对不上数」一起打印，
#     才看见「变绿」其实是分母掉了 32。[[ratio-gates-can-be-passed-by-shrinking]]
_CJK_PUNCT = re.compile(r"[《》「」『』，、。；：？！（）【】]")


def _norm(s: str) -> str:
    s = _MARKUP.sub("", s)
    s = _HYPHEN_BREAK.sub("", s)                 # `circum- stances` → `circumstances`
    s = _DASHES.sub("-", s)                      # 各种破折号归一
    # ★★★★ 2026-08-10：**扫描分栏留下的竖线 `|` 按空白处理。**
    #   Nasmyth #153 实测：报刊与议会卷是双栏扫描，OCR 把栏界打成 `|`，
    #   于是同一句话里会出现 `he attended | the first session … of the| School of Arts`。
    #   **12 条「对不上」在只去掉 `|` 与压平空白之后，12/12 全部逐字对上**——
    #   也就是说那 12 条的差异**纯粹是版面，不是内容**。
    #
    #   ★ 为什么这一条可以加，而「把 eycy 改成 eye」不可以：
    #     去 `|` 是**版面归一**——统一、可声明、可验证，且 `|` 不可能是英文引文的一部分；
    #     改 `eycy` 是**改内容**——那正是本件要抓的「改了 OCR 错字再当逐字引文用」。
    #     **两者的分界是「动没动字母」。**
    #
    #   ★★ 按上一条注释的纪律，加归一必须同时问「它会不会把本来对得上的打散」：
    #     `|` 变空白只会让更多东西对上，**不会拆散已经对上的**（空白最后统一压平）。
    #     自测里配了正例与反例各一。
    s = s.replace("|", " ")
    # ★★★★ 2026-08-10：**标点前的空白按版面处理。**
    #   Mendel #125 实测：13 条对不上里 **7 条是同一件事**——
    #   OCR 在德文标点前留了空格：
    #       `Brünn : Gestern`、`( 54 Mm . in`、`Menge , dass`、`gesetzt . Der`
    #   我写研究道时把它们按正常排印收紧了，于是「逐字」对不上。
    #
    #   ★ 与「把 eycy 改成 eye」的分界仍然是**动没动字母**：
    #     去掉标点前的空格不动任何字母，且**两侧同时归一**，
    #     所以它只可能让更多东西对上，**不可能拆散已经对上的**。
    #   ★★ 但它确实放宽了判据：`a , b` 与 `a, b` 从此视为同一句。
    #     **这是有意的**——那是排印差异，不是内容差异。
    #     自测里配了反例：**字母一改，照样对不上。**
    s = _APOSTROPHE.sub("'", s)
    s = _SPACE_BEFORE_PUNCT.sub(r"\1", s)
    # ★ 这里**不要**再把 ` - ` 缩成 `-`：那是我随手加的一条、没配自测，
    #   当场把 Roberts-Austen 从 0 条对不上打成 2 条
    #   （`[April 20, 1891. — In the course…` → `1891.-In`，
    #     `chronological sequence : —` → `sequence : -`）。
    #   **每加一条归一，就得同时问「它会不会把本来对得上的打散」。**
    s = " ".join(s.split())
    # ★★★★ 2026-08-10：**引文断在跨行连字符上时，末尾那个连字符要去掉。**
    #   `_HYPHEN_BREAK` 只处理 `连字符 + 空白`（`circum- stances` → `circumstances`），
    #   而引文如果**正好断在半个词上**，连字符后面什么都没有，它就留在末尾：
    #       Thomson #129 实测：`1 have tried that with considerable suc-`
    #                          `It is my privilege, as … a young, vigorous and grow-`
    #       语料里是 `suc- cess` → `success`、`grow- ing` → `growing`。
    #   ★ 去掉末尾连字符后 `…considerable suc` 就是 `…considerable success` 的前缀，能对上。
    #   ★★ **这确实放宽了一点**：截断的词只比到词干。
    #     但整条引文本身很长，靠前面几十个词已经锁死了位置；
    #     而**不去掉的话，凡是断在半个词上的引文一条都验不了**——那是更大的盲区。
    return s[:-1] if s.endswith("-") else s


def load_corpus(ws: pathlib.Path):
    """→ {source_id: 归一化后的全文}。读不到的**记下来**，不当成没问题。"""
    led = ws / "evidence" / "source-ledger.jsonl"
    if not led.is_file():
        return None, [f"没有 {led}"]
    corp, unread = {}, []
    for line in led.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        r = json.loads(line)
        p = ws / str(r.get("normalized_path") or r.get("local_path") or "")
        if p.is_file():
            corp[r.get("source_id")] = _norm(
                p.read_text(encoding="utf-8", errors="replace"))
        else:
            unread.append(r.get("source_id"))
    return corp, unread


def extract_quotes(md: str):
    """从 markdown 里取出逐字引文。见文件头「判法」三条。"""
    blocks = []
    for blk in re.findall(r"((?:^>.*\n)+)", md, re.M):
        seg = []
        for ln in blk.split("\n"):
            s = ln.lstrip(">").strip()
            if s.startswith("——"):                 # ← 要害 1：归属行处切开
                if seg:
                    blocks.append(" ".join(seg))
                seg = []
            elif s:
                seg.append(s)
        if seg:
            blocks.append(" ".join(seg))
    # ★★★★ 2026-08-10：**段落内的反引号引文此前一条都没验过。**
    #   本件原来只从 `>` 引用块里取引文。Nasmyth #153 实测：
    #     引用块内 33 条（判据验的就是这些，全绿）
    #     **段落内反引号 30 条 —— 从来没进过判据，其中 14 条对不上**
    #   而那 14 条里**有两份是 `[sketch]`／`[Schneider]` 这种我自己补的方括号编造**
    #   （在 `04-external.md` 与 `05-decisions.md`）。
    #   我当天已经修过 `06-timeline.md` 里的同一处，**以为改完了**——
    #   本件报 0 条对不上，于是「改完了」这个结论看着还有判据背书。
    #   [[fixed-the-symptom-kept-the-root-cause]] ＋ 清单缺口，两个一起犯。
    #
    #   ★ 抓到它的不是本件，是 `check_quote_speaker` 扩清单进研究道之后
    #     报出「在语料里定位不到 14 条」。**两件判据互为对照才看得见。**
    #   ★★ 只取**引用块之外**的反引号，块内的已经由上面那条路走过了，
    #     否则同一条会被数两次——同一天刚在 `check_holdout_mention` 上犯过重复计数。
    nonblk = "\n".join(l for l in md.split("\n") if not l.lstrip().startswith(">"))
    for inline in re.findall(r"`([^`\n]{25,400})`", nonblk):
        blocks.append(inline)

    out = []
    for b in blocks:
        for m in (re.findall(r"`([^`]+)`", b) or [b]):
            t = " ".join(m.split()).strip(" …")
            if len(t) < 25:
                continue
            # ★ 文件名／标识符不是引文（Carver 的 `proceedingsofiow07iowa.txt`
            #   被上一版当成引文报了失败）。引文总有空格与句读。
            if " " not in t or re.fullmatch(r"[\w.\-/]+", t):
                continue
            # ← 要害 2：中文散文里的 `字段名` 不是引文。
            #   ★ 但**不能按 ASCII 判**——Pasteur 的道稿引的是法语原文
            #     （`à`/`é`/`ô`），按 ASCII 会把一整个人物的引文全漏掉。
            #   改判「CJK 占比」：有汉字的是我们写的散文，没有的是引文。
            if sum('\u4e00' <= c <= '\u9fff' for c in t) / len(t) > 0.05:
                continue
            # ★★★★ 2026-08-10：**中日韩标点也算「这是我写的散文」**，与汉字同论。
            #   上面那条只数**汉字**，于是这几种漏了过去（全库实测 4 条）：
            #       `《The Times》1878-01「A Billion Dissected」，落款`   ← 我的著录标签
            #       `P1 Elizabeth Blackwell Papers: Poetry（`            ← 我的引证标签
            #   它们汉字极少甚至没有，却带着 `《》「」，（`——**一句真的英文逐字引文
            #   永远不会含这些符号**，所以这一条不会误伤引文，只会滤掉我的散文。
            #   ★ 反过来说：**中文语料的引文早就被上面那条汉字比例挡住了**，这里不冲突。
            if _CJK_PUNCT.search(t):
                continue
            out.append(t)
    return out


def verify(quote: str, corpus: dict):
    """→ (命中的 source_id, 或 None)。

    ★★★ 要害 3：带 `[版口：…]` 的引文，**按标记切成数段，要求同一份来源里
      每一段都在，且顺序不乱**——不许只验前缀。
    """
    # `[版口：…]` 与显式省略号都是「作者声明此处有断」，按分段各自命中验
    parts = []
    for p in _PAGE_FURNITURE.split(quote):
        parts.extend(_ELISION.split(p))
    segs = [_norm(p) for p in parts if len(_norm(p)) >= 4]
    if not segs:
        return None
    for sid, text in corpus.items():
        pos, ok = 0, True
        for s in segs:
            i = text.find(s, pos)
            if i < 0:
                ok = False
                break
            pos = i + len(s)
        if ok:
            return sid
    return None


def check(ws: pathlib.Path):
    corp, unread = load_corpus(ws)
    if corp is None:
        return 2, {"错": unread}
    res, bad = {}, 0
    for f in sorted((ws / "references" / "research").glob("0*.md")):
        qs = extract_quotes(f.read_text(encoding="utf-8"))
        miss = [q for q in qs if verify(q, corp) is None]
        bad += len(miss)
        res[f.name] = {"引文数": len(qs), "核过": len(qs) - len(miss),
                       "**对不上**": [q[:140] for q in miss]}
    return (0 if bad == 0 else 1), {
        "逐道": res,
        "合计": f"{sum(v['引文数'] for v in res.values())} 条引文，对不上 {bad} 条",
        "读不到正文的来源": unread,      # ★ 读不到就说读不到
        "通过": bad == 0 and not unread,
    }


def self_test():
    bad = []

    def chk(lbl, ok):
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    print("\n══ ★ 引文断在跨行连字符上（Thomson #129 实测两条）══")
    chk("`…considerable suc-` 能对上语料的 `suc- cess`",
        _norm("1 have tried that with considerable suc-")
        in _norm("Pror. Tmomson:-1 have tried that with considerable suc- cess in a case"))
    chk("`…vigorous and grow-` 能对上 `grow- ing`",
        _norm("as the chief officer of a young, vigorous and grow-")
        in _norm("It is my privilege, as the chief officer of a young, vigorous and grow- ing body"))
    chk("★ 而词干不同仍然对不上（`suc-` vs `sur- vey`）",
        _norm("with considerable suc-") not in _norm("with considerable sur- vey"))

    print("\n══ ★ 撇号排印变体（Thomson #129 实测）══")
    chk("弯撇号与直撇号视为同一个",
        _norm("I think that Prof. Anthony's remarks are very apt")
        in _norm("Pror. Taomson:-I think that Prof. Anthony\u2019s remarks are very apt indeed"))
    chk("★ 而改了字母仍然对不上（`Anthony` → `Anthonys`）",
        _norm("Prof. Anthonys remarks") not in _norm("Prof. Anthony\u2019s remarks"))

    print("\n══ ★ 带中日韩标点的不是引文（2026-08-10 全库实测 4 条）══")
    for s_ in ("《The Times》1878-01「A Billion Dissected」，落款",
               "P1 Elizabeth Blackwell Papers: Poetry（",
               "1841 论文 ¶491（他自己写的）"):
        chk(f"不取：{s_[:34]}", not extract_quotes("正文里 `" + s_ + "` 这样写。\n"))
    chk("★ 而纯英文逐字引文照取",
        bool(extract_quotes("他写道 `to him we are certainly indebted for the slide rest` 。\n")))

    chk("★★ 而 `—`（英文破折号）不算——真引文天天带它",
        bool(extract_quotes("他写道 `the tool is held by an iron hand—firmly and truly` 。\n")))
    chk("★★★ `…` 更不算——**那是本判据自己的省略号语法**",
        bool(extract_quotes("他写道 `Hitherto, so far as I am aware … has not received that attention` 。\n")))

    print("\n══ ★★★★ 标点前的空白（Mendel #125，13 条里 7 条是这一件事）══")
    _DE_REAL = ("Herr Abt Mendel schreibt uns aus Brünn : Gestern am 29. Juni um 7 Uhr Abends "
                "entlud sich über unsere Stadt ein Gewitter mit Hagelschlag und wolkenbruchartigem "
                "Gussregen ( 54 Mm . in kaum mehr als einer halben Stunde ) .")
    _DE_MINE = ("Herr Abt Mendel schreibt uns aus Brünn: Gestern am 29. Juni um 7 Uhr Abends entlud")
    chk("标点前空白归一后，德文那句对得上", _norm(_DE_MINE) in _norm(_DE_REAL))
    chk("同段的括号与句点也对得上",
        _norm("54 Mm. in kaum mehr als einer halben Stunde") in _norm(_DE_REAL))
    # ★★ 反例：**改了字母仍然必须对不上**——这道门存在的理由不许被顺手削掉
    chk("而把 `eultivirten` 改成 `cultivirten` 仍然对不上",
        _norm("in grossen Mengen cultivirten Pflanzenbastarde")
        not in _norm("in grossen Mengen eultivirten Pflanzenbastarde"))
    chk("★ 删掉 OCR 垃圾字也仍然对不上（`P. oO Sa Gresor` → `P. Gresor`）",
        _norm("Vereinsmiteliedes P. Gresor Mendel")
        not in _norm("Vereinsmiteliedes P. oO Sa Gresor Mendel"))
    # ★★★ 反例：**词序改了照样对不上**（Mendel 第 7 条就是我把语序调了）
    chk("★★ 调换词序仍然对不上（`referiren über einen Delinquenten` vs 原文语序）",
        _norm("referiren über einen Delinquenten")
        not in _norm("Ich erlaube mir über einen Delinquenten zu referiren"))

    print("\n══ ★★★★ 段落内反引号引文（2026-08-10 —— 此前一条都没进过判据）══")
    # ★ 夹具照真实研究道的排法写：中文引导句在**块外**，块内只有引文本身。
    #   第一版我把引导句写进了块里，整块 CJK 占比超阈值被过滤——
    #   **红的是夹具不是代码**，而我差点去改代码。
    MD = ("正文里这样写：`a very great loss of time to the master in giving necessary instructions`（代价）。\n"
          "\n引用块里的这条：\n"
          "\n> the correctness of his eycy had we entirely to depend for accuracy\n")
    qs = extract_quotes(MD)
    chk(f"段落内那条被取到了（共 {len(qs)} 条）",
        any("loss of time to the master" in q for q in qs))
    chk("引用块那条也还在", any("correctness of his eycy" in q for q in qs))
    # ★ 反例①：**同一条不许被数两次**——块内的反引号引文只能出现一次
    MD2 = "> 块里带反引号：`the correctness of his eycy had we entirely to depend for accuracy`\n"
    q2 = extract_quotes(MD2)
    chk(f"块内的反引号引文只出现一次（{len(q2)} 条）", len(q2) == 1)
    # ★ 反例②：URL／标识符不是引文（同一个坑在 check_quote_speaker 上也踩过）
    MD3 = "见 `https://archive.org/details/practicalessays00nasmgoog` 与 `proceedingsofiow07iowa.txt`。\n"
    chk(f"URL 与文件名不算引文（{extract_quotes(MD3)}）", not extract_quotes(MD3))

    # ══ ★★★★ 真实样本：**分栏竖线**（Nasmyth #153，2026-08-10）══
    #   议会卷与报刊是双栏扫描，OCR 把栏界打成 `|`。
    _PIPE_REAL = ("Along with Leonard Horner, he attended | the first session in the winter "
                  "of 1821 of the| School of Arts")
    _PIPE_MINE = ("Along with Leonard Horner, he attended the first session in the winter "
                  "of 1821 of the School of Arts")
    chk("分栏竖线按空白处理后，同一句逐字对上", _norm(_PIPE_MINE) in _norm(_PIPE_REAL))
    # ★★ 反例：**改了字母就必须仍然对不上**——这是本件存在的理由，不许被上面那条顺手削掉
    chk("而把 `eycy` 改成 `eye` 仍然对不上（去竖线没有把这道门剥掉）",
        _norm("the correctness of his eye") not in _norm("the correctness of his eycy"))

    # ══ ★★★★ 逐字真实样本：`_MARKUP` 的「标签」支吃掉 46% 的语料（2026-08-07）══
    #   下面这段是 Whitworth #152 的 `in.ernet.dli.2015.43651`（泰晤士报讣告 1893 重印本）
    #   里的**原文**，连 OCR 讹形（`<lied` 是 `plied`、`ho liad` 是 he had、`j^laced`）一起。
    #   ★ 要害在开头那个孤立的 `<`：旧正则 `[^>]*` **不禁换行**，
    #     于是从它一路吃到几万字符之外的下一个 `>`。
    print("\n══ ★★★★ 逐字真实样本：孤立的 `<` 不许吃掉整段散文 ══")
    _REAL = ("<lied to satisfy a fastidious\ntaste, but he was generally well worth hearing,\n"
             "for his knowledge was wide and various.\n"
             "workroom and j^laced next to his best workman, one Hampson.\n"
             "After ^the day’s labour was over ho liad always employment at\n"
             "home, and it was in this way that he completed the true plane,\n"
             "exhibiting it one night with pride to Hampson, whose sole\n"
             "comment was You’ve done it.” From Maudslay’s, Whitworth\n"
             "went to Holtzapfrd’s and then to Clements’, where Hr.\n")
    _n = _norm(_REAL)
    chk(f"`Hampson` 还在（{_n.count('Hampson')} 处，旧口径是 0）", _n.count("Hampson") == 2)
    chk(f"删掉的字符 {len(_REAL) - len(_MARKUP.sub('', _REAL))} 个"
        f"（只该删两个弯引号）", len(_REAL) - len(_MARKUP.sub("", _REAL)) <= 4)
    chk("那句真引文能核到", verify(
        "After ^the day’s labour was over ho liad always employment at\n"
        "home, and it was in this way that he completed the true plane,\n"
        "exhibiting it one night with pride to Hampson, whose sole\n"
        "comment was You’ve done it.", {"src-x": _n}) == "src-x")
    #   ★ 反向：**真的 HTML 标签仍要剥掉**，否则修过头。
    chk("真标签仍剥掉：`<b>` / `</span>` / `<span class=\"x\">`",
        _norm("a <b>bold</b> and <span class=\"x\">tagged</span> line")
        == "a bold and tagged line")
    #   ★★ 全库实测（2026-08-07）：旧口径删 **132,987,151** 字符，新口径 **1,076,997**；
    #     574 份语料文件被误删 >500 字符，跨 21 个工作区（Koch 4000 万、Virchow 2940 万）。
    #     **而已实现的损害只有 2 条冤枉报错**（归档里 Pasteur 1 条 + Whitworth 1 条）——
    #     多数引文恰好落在没被删的部分。两件事都要说，不许只说其中一件。
    #   ★★★ **方向只会假阴**：删除让判据更容易报「对不上」，
    #     所以过去那些「0 条对不上」不但仍然成立，而且是在**更苛刻**的条件下取得的。
    print("  ★ 全库实测：旧口径删 132,987,151 字符 / 新 1,076,997；"
          "574 份文件受影响，**而冤枉报错只有 2 条**——机制严重、已实现损害小，两件都要说。")


    # ★★★ 自测的语料**必须与生产同口径**——`load_corpus` 会 `_norm`，
    #   而我第一版把生地 dict 直接喂给 `verify`，**测的是另一条路**：
    #   折行连字那四条当场全红，红的却是自测自己。
    def _C(d):
        return {k: _norm(v) for k, v in d.items()}

    corpus = _C({"src-a": "and the results have recently been communicated to the "
                       "Koyal Feb. 1897. ALLOTS RESEARCH. 57 Society, and formed the "
                       "subject of the Bakerian Lecture for the past year.",
              "src-b": "he was re-stated on' the first page of this paper."})

    print("── ★★★★ **真实样本**：Rosenhain #138 JISI 1912 讨论纪要（逐字，含真实换行与 OCR 讹形）──")

    # 2026-08-06 我在 04-external.md 里引这句时**把 OCR 讹字改对了**（`I)r. llosenhain` → `Dr. Rosenhain`），

    # 本判据当场报「语料里没有」。**它说得对。**

    # 下面两条把这个区分钉死：**照录该过，改对了不该过。**

    _real = _C({"src-jisi": "t a \nlittle practical help was worth a world of advice. I)r. llosenhain and \n"

                            "his somewhat slavish adherence to equilibrium curves did not appeal \n"

                            "to the authors, since as practical men their faith in such curves fell \n"

                            "far short of that of Dr. Rose"})

    chk("★ **照录 OCR 讹形**（`I)r. llosenhain and his somewhat slavish`）→ 命中",

        verify("I)r. llosenhain and his somewhat slavish adherence to equilibrium curves",

               _real) == "src-jisi")

    chk("★★ **把讹字改对了**（`Dr. Rosenhain and his somewhat slavish`）→ **不该命中**",

        verify("Dr. Rosenhain and his somewhat slavish adherence to equilibrium curves",

               _real) is None)

    chk("★★★ 跨行处照样命中（`did not appeal \\n to the authors`）",

        verify("did not appeal to the authors, since as practical men", _real) == "src-jisi")


    print("── 正例 ──")
    chk("整段命中", verify("communicated to the Koyal", corpus) == "src-a")
    chk("标出版口后，分段都在 → 过",
        verify("communicated to the Koyal [版口：Feb. 1897. ALLOTS RESEARCH. 57] "
               "Society, and formed the", corpus) == "src-a")
    chk("OCR 讹形照录 → 过", verify("re-stated on' the first page", corpus) == "src-b")

    print("\n── ★★★ 反例：抹平讹字／抹掉版口，一条都不许过 ──")
    chk("抹平撇号 → 拒", verify("re-stated on the first page", corpus) is None)
    chk("抹掉版口把两半缝起来 → 拒",
        verify("communicated to the Royal Society, and formed the", corpus) is None)
    chk("**只改讹字不动版口** → 拒",
        verify("communicated to the Royal [版口：Feb. 1897. ALLOTS RESEARCH. 57] "
               "Society, and formed the", corpus) is None)
    # ★★★ 这一条防的是我自己：写的时候一度让带版口的引文「只验前缀」就算过
    chk("**版口后半句是编的** → 拒（不许只验前缀）",
        verify("communicated to the Koyal [版口：Feb. 1897. ALLOTS RESEARCH. 57] "
               "Society, and was never published", corpus) is None)
    chk("版口内容本身是编的 → 拒",
        verify("communicated to the Koyal [版口：Jan. 1899. WRONG HEADER] "
               "Society, and formed the", corpus) is None)

    print("\n── ★★ 允许的排版记号（全库回扫撞出来的，去读才知道不是缺陷）──")
    c2 = _C({"src-c": "It is based, like the treatment of compound fracture, on the "
                   "antiseptic principle, and the paste should be changed daily ; and, "
                   "in order to prevent mischief, a piece of rag dipped in the solution.",
          "src-d": "Le 10 décembre dernier, M. le Dr Lannelongue, chirurgien de "
                   "l'hôpital Sainte-Eugénie, vint me voir."})
    chk("引文里加粗 → 过（加粗是看得见的记号）",
        verify("on the **antiseptic principle**, and the paste should be changed "
               "**daily**", c2) == "src-c")
    chk("行内 HTML 上标 → 过",
        verify("M. le D<sup>r</sup> Lannelongue, chirurgien de l'hôpital", c2) == "src-d")
    chk("法语弯引号包起来 → 过",
        verify("«Le 10 décembre dernier, M. le Dr Lannelongue»", c2) == "src-d")
    chk("显式省略号 → 按分段各自命中",
        verify("the paste should be changed daily ; ... a piece of rag dipped in "
               "the solution", c2) == "src-c")

    print("\n── ★★★ 负对照：剥掉记号**不许**把改过的正文放过去 ──")
    #   这是本件最要紧的一条：`_MARKUP` 剥得越多，越容易把真缺陷一起剥掉。
    chk("剥了加粗，但词被换了 → 仍拒",
        verify("on the **aseptic principle**, and the paste should be changed", c2) is None)
    chk("剥了 HTML，但人名被换了 → 仍拒",
        verify("M. le D<sup>r</sup> Lannelongue, chirurgien de l'hôpital Saint-Louis",
               c2) is None)
    chk("省略号两侧顺序颠倒 → 拒",
        verify("a piece of rag dipped in the solution ... the paste should be "
               "changed daily", c2) is None)
    chk("★ 法语引文不许被「按 ASCII 取引文」漏掉",
        any("décembre" in q for q in extract_quotes(
            "> `Le 10 décembre dernier, M. le Dr Lannelongue, vint me voir.`\n")))

    print("\n── ★★ 折行连字：印本差别放过，改字不放过 ──")
    c3 = _C({"src-e": "in accordance with the difference of the circum- stances. "
                   "It was a matter of co- operation between them.",
          "src-f": "in accordance with the difference of the circum¬ stances."})
    chk("`circum- stances` ←→ `circumstances`", verify("of the circumstances", c3) == "src-e")
    chk("OCR 的 `¬` 折行同样归一", verify("difference of the circumstances", c3) is not None)
    # ★★★ 负对照：归一折行连字**不许**把别的词放过去
    chk("`circumference` → 拒", verify("of the circumference and so on here", c3) is None)
    chk("`cooperation` 与 `co- operation` 同 → 过",
        verify("a matter of cooperation between them", c3) == "src-e")
    chk("`corporation` → 拒", verify("a matter of corporation between them", c3) is None)

    print("\n── 取引文的两条要害 ──")
    md = ("> `first quote here that is long enough to count ok`\n"
          "> —— `src-x`（1891）\n"
          "> `second quote here that is also long enough yes`\n")
    qs = extract_quotes(md)
    chk(f"归属行处切开 → 取到 2 条（{len(qs)}）", len(qs) == 2)
    md2 = "> 这一段是中文散文，里面提到 `dimensions` 这个字段名，不该被当成引文。\n"
    chk(f"中文散文里的字段名不算引文（{len(extract_quotes(md2))}）",
        not extract_quotes(md2))

    if bad:
        print("\n未过：")
        for b in bad:
            print("  · " + b)
        return 2
    print("\n✓ 自测全过（3 正 + 5 反 + 2 条取法）")
    return 0


def main():
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("workspace", nargs="?", help="人物工作区（含 evidence/ 与 references/research/）")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.workspace:
        ap.error("要么 --self-test，要么给工作区")
    code, rep = check(pathlib.Path(a.workspace))
    print(json.dumps(rep, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    sys.exit(main())
