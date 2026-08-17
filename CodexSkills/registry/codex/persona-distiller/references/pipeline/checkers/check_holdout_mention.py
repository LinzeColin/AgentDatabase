#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**建模者能读到的文件里，一个字都不许提 holdout**——2026-08-07 被子代理抓出来的。

## 撞出它的那一次

Whitworth #152 第 1 轮，候选方（一个隔离的子代理）**主动上报**：

> `hypotheses.md` 第 2 条写明「他对『别人的产品』有一套稳定的评价方式。
> **证据只有 holdout 里那一条，train 侧没有第二处**」——这句话把 holdout 那条的
> 主题直接说了出来，而它恰好对应那道锁的题。也就是说，**在我读题之前，
> 允许读的产物正文已经告诉我这道题考的是什么、以及 train 侧取不到证据。**

★★ 那句话是我写的，而且是我**在说明「我已经把 holdout 的内容删干净了」的语境里**写的。
同一天里第三次「堵漏的那段话本身成了新的漏」——
前两次是门抓到的（`corpus.holdout-leak` / `research.invalid-source`），
**这一次两道门全绿**。

## 为什么那两道门抓不到

- `corpus.holdout-leak`（`check_material_split`）查的是**同一份正文有没有同时躺在
  train 与 holdout 两个目录里**——文件挪对了它就绿。
- `research.invalid-source` 查的是研究文档里有没有引用**非 train 的 source_id**——
  我把 id 删了它就绿。

**两道门都只认「id 与文件」，不认「有这么一份、它考什么」。**
而对答题方来说，知道「存在一份取不到的材料、它关于某某」已经足够定位那道题。

## 本件判什么

对**建模者能读到的每一个文件**（十份产物正文 + `references/research/*.md`
+ `evidence/claims.jsonl`）：

### 层一：字面提及 —— 硬错

出现 `holdout` / `保留集` / `已划为` 一类词，或「train 侧没有／不含」这种表述。
**这一层是确定的**：这些词在建模者读的文件里没有任何正当用途。

### 层二：与 holdout 正文的 8 词片重叠 —— 硬错

抓「不说 holdout 三个字，但把它的内容抄了过来」。

## ★ 射程（必须一起说）

- **层二只能抓到同语种的近似复述。** 本人物的 holdout 是英文语料，
  而产物正文是中文——**中文转述英文 holdout 的主题，层二一个字也看不见**。
  今天那次泄漏正是靠层一（字面 `holdout`）抓到的，**如果我当时换个说法就漏了**。
- **本件抓不到「不提 holdout 也不抄它，却把题目描述出来」的写法。**
  例如「他评价别人产品的材料我们取不到」——没有关键词、没有重叠、照样泄题。
  **那一类只能靠人读，或者靠答题方像今天这样主动上报。**
- 因此本件的正确读法是：**它把最粗的那一档堵上，不是把这条路封死。**

退出码：0 = 没有提及也没有重叠；1 = 有；3 = 用法错误。
"""
from __future__ import annotations

import argparse
import itertools
import json
import pathlib
import re
import sys

# 层一：这些词在建模者读的文件里没有正当用途
MENTION = re.compile(
    r"holdout|hold-out|保留集|留出集|"
    r"已划为[^\n]{0,6}(?:保留|留出)|"
    r"train\s*侧(?:没有|不含|取不到)|"
    r"(?:不计入|不列入)本道|"
    # ★★★ 2026-08-11 补：**中文平白说法**。此前词表只有 `holdout` 一族，
    #   于是「不入训练」这种等价说法**门一个都不认识**。
    #   全库实测 10 处，其中 **6 处附近 160 字符内没有任何原词表词 → 门完全看不见**：
    #     · lister-108 `## 传记（S2，其中一份不入训练）src-6448ba81d2d2 等 4 份。` → **四选一**
    #     · koch-107   `## 传记（皆 S2，其中一份不入训练）src-b58f8581c014（Cohn 回忆录…` → 同型
    #     · pasteur-106 先点书名与译本，再说「其一个译本不入训练」
    #   与 [[a-gate-that-says-independent-may-not-be]] 同类：**门报 0，而它要挡的就在那儿。**
    #   ★ 收紧不放宽：这些词只是进入「提及」层，是否算**点名**仍由 `names_the_work` 判，
    #     所以「本道无不入训练的材料」这种否定句照旧只算泛提。
    r"不入训练|不进训练|未入训练|不参与训练|不在训练侧|"
    r"排除在训练之外|不作训练用|训练侧(?:没有|不含|取不到)",
    re.I)
SHINGLE_N = 8
_WORD = re.compile(r"[a-z0-9]+")

# 建模者能读到的文件（与 quality_check.RENDER_FILES 对齐 + 研究道 + 断言）
# ★★★★ 2026-08-10：这张表**只列了十份产物正文，漏掉了工作区根目录里的其它 .md**。
#   Nasmyth #153 实测：抓源勘察报告被拷进工作区根，叫 `00-勘察记录.md`，
#   里面有 holdout 那一篇的**完整标题、卷期页码与日期**——
#   `"On some peculiar Features in the Structure of Lunar Volcanic Craters" | MNRAS 14(5):158–159 | 1854-03-10`。
#   **本件当时报「✓ 没有字面提及，也没有内容重叠」**，因为那个文件根本不在扫描清单里。
#   ★ 抓到它的不是判据，是我事后手打的一条 grep。[[checker-blindspot-read-as-defect]] 的反面：
#     **这一次不是判据的盲区被误当成缺陷，是判据的盲区里真有缺陷。**
#   ★★ 改法：十份产物**逐个点名**（它们必须存在），**再加上工作区根目录下的所有 .md**
#     （勘察记录、检查点、抓取清单这类会随手拷进来的东西）。
#     **建模者能打开的就要扫，不能只扫我记得的那十份。**
_RENDER = (
    "facts.md", "cognitive-os.md", "decision-policy.md", "strategy.md", "capabilities.md",
    "persona.md", "work.md", "boundaries.md", "hypotheses.md", "divergence-map.md",
)
BUILDER_READABLE = _RENDER


# ★★★ 2026-08-10：**「提到 holdout」与「说出它是哪一份」后果差很远，而本件把它们混成一个数。**
#   全库实测 25 行命中里：**23 行是泛泛提及**（「本路不引 holdout」，不说哪一份，无害），
#   **只有 3 行点名**（Adams 的 `work.md` 1 行 + Virchow 的研究道 2 行）。
#   只报总数会让人以为有 25 处泄题，或反过来把 3 处真的淹掉。
#
#   ★ 我第一次手写「点名」判据时**漏了 Adams**：只认书名号／`.txt`／`src-`，
#     而他写的是「1904 年那篇排斥式电动机的会后书面补充（**卷 XXIII pp.63–76**）划为 holdout」——
#     **用卷次页码点名，不带书名号。** 所以坐标形式必须一起认。
NAMES_THE_WORK = (
    r"《[^》]{2,60}》",                       # 书名号
    r"\.txt\b",                              # 文件名
    r"src-[a-f0-9]{12}",                      # 源 id
    r"卷\s*[IVXLC\d]+",                       # 卷 XXIII / 卷 12
    r"\bvol\.?\s*[IVXLC\d]+",                # vol. XXIII
    r"pp?\.\s*\d+",                          # p.63 / pp.63–76
    r"第\s*\d+\s*[卷期页]",                   # 第 23 卷
    r"(?<!\d)1[5-9]\d\d(?!\d)\s*年[^\n]{0,12}(?:那篇|这篇|的[^\n]{0,8}[篇文书报])",  # 1877 年的《…》/1904 年那篇
)
_NAMES_RE = re.compile("|".join(NAMES_THE_WORK))


def naming_window(text: str, pos: int) -> str:
    """→ 判「点名」时该看的那一段：**提及所在行 + 其后至多 3 个非空行**。

    ## 为什么不能只看一行（2026-08-11 实测）

    真实语料里点名**就在下面两行**，中间隔一个空行：

        ## 传记（S2，其中一份不入训练）
        <空行>
        `src-6448ba81d2d2` 等 4 份。            ← lister-108，**四选一**

        ## 传记（皆 S2，其中一份不入训练）
        <空行>
        `src-b58f8581c014`（Cohn 回忆录…）等 7 份。  ← koch-107，**七选一**

    按行判时两处都报「不点名」。★★ 而我给这两条写的第一版自测夹具
    **把它们压成了一行**——[[fixtures-cleaner-than-the-real-thing]]，
    于是自测绿、真语料漏。现在自测用的是**逐字取自语料的多行原文**。

    ★ 窗口在遇到新的 `#` 标题时截断：跨节的 id 与本次提及无关。
    """
    a = max(text.rfind("\n", 0, pos) + 1, 0)
    out, n, i = [text[a:text.find("\n", pos) if text.find("\n", pos) > 0 else len(text)]], 0, None
    i = text.find("\n", pos)
    while i > 0 and n < 3:
        j = text.find("\n", i + 1)
        ln = text[i + 1:j if j > 0 else len(text)]
        if ln.lstrip().startswith("#"):
            break
        if ln.strip():
            out.append(ln)
            n += 1
        i = j
        if i <= 0:
            break
    return "\n".join(out)


def names_the_work(line: str) -> bool:
    """→ 这一行是不是**说出了 holdout 是哪一份**（而不只是提到有个 holdout）。"""
    return bool(_NAMES_RE.search(line))


def builder_readable_files(target) -> list:
    """十份产物 + **工作区根目录下的一切 `.md`**
    + **`references/research/` 下的六份研究道文档** + **`evidence/claims.jsonl`**。

    ★ `SKILL.md`／`README.md` 也在内——它们同样是建模者打得开的。

    ★★★★ 2026-08-10：**研究道文档此前不在清单里，而它们恰是建模者读得最多的一类。**
      发现它的不是本判据，是 Nasmyth #153 候选侧答题子代理**自己在 `__incident__` 里报**
      「六份研究道文档各有一节标题写着 Proposed Holdout cases」。

      全库现算（18 个有研究道的工作区，65 份带该节）：
        · **53 份是空节**——与出厂模板逐字相同，走模板豁免，不算问题；
        · **12 份非空**，其中
            - **Mendel #125 的 3 份把 holdout 的书名直接写了出来**（16 处）
              （`Focke 1881《Die Pflanzen-Mischlinge》、Bateson`）；
            - Carver #127 的 3 份写了件数与所在道（「本道有 3 件 holdout」）；
            - Roberts-Austen #135 的 6 份只写「本轮未提名」，**不泄任何东西**。

      ★★★ **2026-08-10 逐条读完命中之后的更正：按处数排的档次是错的。**
        我先按「处数」排，得出「Mendel 最重」；**读完原文，第一档有三个人**：

        | 泄的信息 | 谁 | 原文 |
        |---|---|---|
        | **作品名／主题** | Mendel（16 处）、**Pasteur**（3）、**Rosenhain**（2） | Pasteur：`其英译本《Louis Pasteur, his life and labours》留作 holdout`；Rosenhain：`1910 年论轻合金（holdout，此处连 source_id 都不写）` |
        | 只有件数 | Blackwell（6 处／件数 6）、Carver（7 处／件数 3）、Koch（1）、Lister（1） | 「holdout 的 6 份**不列在此**」 |
        | 什么也没泄 | Roberts-Austen（2 处） | 「（本轮未提名。）」 |

        ★ Rosenhain 那条最说明问题：**同一段的下一行写着**
          「判据说得对：写下 id 本身就是引用，holdout 一旦在研究文档里露面就不再是盲的」——
          **我在写下这句话的同一处，把作品说了出来。**
          写「我不写 id」和「不泄漏」是两件事：**id 不是唯一的指针，标题也是。**

        ★★★★ **这些处数本身我报错过一次**：并清单那天 `scan()` 里还留着旧的
          「再加一遍研究道与 claims」三行，同一批文件进了两次，
          **研究道那几类的处数全部虚高 2 倍**（我据此报过 Mendel 32／Carver 14／Blackwell 12）。
          上表是修掉重复之后的真值。
          ★ **分档结论没有因此改变**——分档是读原文得出的，不是按处数排的。
            **这一次「先读命中再报率」把我从一个计数 bug 里捞了出来。**
        ★★ **所以本件不能只数处数**。处数多的可能是六份文档同一句样板（Blackwell），
          处数少的可能一句就点了名（Rosenhain 两行）。**报率之前先读命中。**

      ★ 也就是说：本判据一直报 ✓，**而它从来没有看过泄得最狠的那一类文件**。
        这与「判据没有调用方就不算做完」是同一族——
        **清单不含被保证之物，等于这道保证从未存在过。**[[a-checker-nothing-calls-is-not-a-checker]]

      ★★★ **模板那一节要不要改掉——查过了，结论是不改。**
        `## Proposed Holdout cases` 这个节标题出现在 65 份研究道里（53 份空节）。
        看着像泄题，**实际上什么也没多泄**：派发给建模者的指令里本来就写着
        「`references/holdout/` 与 `references/holdout-notes/` 明令禁止读」——
        **它早就知道 holdout 存在了，是我自己告诉它的。**
        改掉节标题只是让它看不到一个它已经知道的事实，属于**做样子**。
        ★ 真正的泄漏是**人物特定的补写**（Mendel 写出书名、Carver 写出件数与所在道），
          那一类扩清单之后本件能抓到。**分清「模板样板」与「人写上去的」，是这道门的全部要点。**
        ★★ 真要根治，得让 holdout 材料**根本不落在建模者可见的工作区根下**——
          那是结构改动，不是改一个标题。**记在这里，别再重新推一遍。**

      ★★ 为什么不顺手把 `references/holdout-notes/` 也扫进来：
        那个目录**本来就是记 holdout 的地方**，且明令禁止建模者打开。
        把它算成「建模者可读」会让判据对着自己的档案报红——**红得毫无信息**。
        清单要跟着「实际发给建模者的是什么」走，不是跟着「目录里有什么」走。
    """
    import pathlib as _p
    root = _p.Path(target)
    out = [root / n for n in _RENDER]
    out += sorted(p for p in root.glob("*.md") if p.name not in _RENDER)
    out += sorted((root / "references" / "research").glob("*.md"))
    out.append(root / "evidence" / "claims.jsonl")   # 断言层同样发给建模者
    return [p for p in out if p.is_file()]


def shingles(text: str, n: int = SHINGLE_N) -> set:
    w = _WORD.findall(text.lower())
    return {" ".join(w[i:i + n]) for i in range(max(len(w) - n + 1, 0))}


def scan(target: pathlib.Path) -> dict:
    led = target / "evidence/source-ledger.jsonl"
    if not led.is_file():
        return {"状态": f"没有 {led}，**未核（不是通过）**"}
    rows = [json.loads(l) for l in led.read_text(encoding="utf-8").splitlines() if l.strip()]
    hold = [r for r in rows if r.get("split") == "holdout"]

    # ★★★★ 2026-08-10：这里原本在 `builder_readable_files()` **之外又加了一遍**
    #   研究道与 `claims.jsonl`。此前那两项不在清单里，所以补在这儿是对的；
    #   而我当天把它们并进了 `builder_readable_files()`，**却忘了把这三行删掉**——
    #   于是同一批文件进了两次，**那几类命中全部被数了两倍**。
    #   ★ 后果不是「多打印几行」：我据此报出过 Mendel 32／Carver 14／Blackwell 12，
    #     **真值是它们的一半**，而且这些数已经写进了提交信息与任务台账。
    #   ★★ 抓到它的不是自测（自测只考正则与清单函数，不考 `scan()` 有没有重复喂），
    #     是我回头读自己刚改过的那段代码。**「改了 A 处、忘了删 B 处」是加清单这类改动的固定形状。**
    #   现在**只走一处真源**，谁该被扫由 `builder_readable_files()` 独家决定。
    files = builder_readable_files(target)
    assert len(files) == len(set(files)), "同一个文件被喂了两次——**又是重复计数**"

    # ★★ 2026-08-07：**与出厂模板逐字相同的行要豁免，但必须报出豁免了几条。**
    #   首跑在 Whitworth 上报出 4 处，逐条读命中才发现是脚手架原文：
    #     `## Proposed Holdout cases` 与
    #     `IDs only; research Agents must not inspect Holdout bodies.`
    #   它们逐字来自 `templates/target/references/research/*.md`，
    #   **全库 71 个文件都带着**，不含任何本人物信息。
    #   ★ 豁免的依据是「这一行在出厂模板里就有」，**不是把它写进白名单**——
    #     同样的词若出现在人物特定的句子里，照报。
    tmpl_lines = set()
    tmpl_root = pathlib.Path(__file__).resolve().parent.parent / "templates" / "target"
    if tmpl_root.is_dir():
        for tf in tmpl_root.rglob("*.md"):
            for ln in tf.read_text(encoding="utf-8", errors="replace").splitlines():
                if ln.strip():
                    tmpl_lines.add(ln.strip())

    mentions, exempted, overlaps = [], [], []
    # ★★★★ 2026-08-07：**层二必须减掉 train，只比 holdout 独有的部分。**
    #   首版直接拿「产物 ∩ holdout」当泄漏，全库回扫报出 17 处重叠。
    #   去量 `holdout ∩ train` 才发现那是个巨大的共有第三方：
    #       Koch #107 **84.7%**、Nightingale #112 **44.8%**、Barton #117 6.3%、Lister #108 5.7%
    #   也就是说，**holdout 的正文大半本来就在 train 里**（同一部作品被收进两侧、
    #   或文集与单篇的关系），产物引用 train 就会「与 holdout 重叠」——**根本没有泄漏**。
    #   ★ 这是同一天里第三次要减共有的第三方
    #     （前两次：判据里的题面回声、我自己写进语料的表头）。
    #     [[overlap-metrics-need-a-shared-baseline-subtracted]]
    hold_raw, train_sh = set(), set()
    for r in hold:
        p = target / str(r.get("normalized_path") or r.get("local_path") or "")
        if p.is_file():
            hold_raw |= shingles(p.read_text(encoding="utf-8", errors="replace"))
    for r in rows:
        if r.get("split") != "train":
            continue
        p = target / str(r.get("normalized_path") or r.get("local_path") or "")
        if p.is_file():
            train_sh |= shingles(p.read_text(encoding="utf-8", errors="replace"))
    hold_sh = hold_raw - train_sh          # ← holdout **独有**的部分

    for f in files:
        if not f.is_file():
            continue
        t = f.read_text(encoding="utf-8", errors="replace")
        for m in MENTION.finditer(t):
            line = t[:m.start()].count("\n") + 1
            a = max(t.rfind("\n", 0, m.start()) + 1, 0)
            e = t.find("\n", m.end())
            whole = t[a:e if e > 0 else None]
            rec = {"文件": f.name, "行": line, "命中": m.group(0), "整行": whole[:160],
                   # ★ 判「点名」看窗口不看单行——真实语料里点名在下面两行，见 naming_window
                   "★ 点名了是哪一份": names_the_work(naming_window(t, m.start()))}
            (exempted if whole.strip() in tmpl_lines else mentions).append(rec)
        if hold_sh:
            common = shingles(t) & hold_sh
            if common:
                overlaps.append({"文件": f.name, "共有 8 词片": len(common),
                                 "样本": sorted(common)[:3]})

    out = {
        "holdout 份数": len(hold),
        "扫过的建模者可读文件": len(files),
        "**字面提及**": mentions,
        # ★ 分档：泛泛提到「有个 holdout」无害；**说出它是哪一份才是泄题**。
        "**其中点名了是哪一份的**": [x for x in mentions if x["★ 点名了是哪一份"]],
        # ★★★ 2026-08-12 加的射程说明：上面这个「点名」是
        #   **窗口里出现了作品名／source_id** —— 它**不保证那就是 holdout 那一份**。
        #   实测三例：Koch「传记（皆 S2，其中一份不入训练）… `src-b58f8581c014` 等 7 份」，
        #   窗口里那个 id 是**代表性的 train 源**，真正泄的是「holdout 是 7 份传记之一」。
        #   而 Pasteur 是**真点名**：「`src-…`《La Vie de Pasteur》…**其一个译本**不入训练」。
        #   ⇒ **这一栏要逐条读原文再定性**，别把三例并成「都点名了」。
        #     [[read-the-hits-before-reporting-the-rate]]
        "★ 「点名」这一栏的射程": (
            "判的是**窗口里有没有出现作品名/source_id**，"
            "**不保证那个 id 就是 holdout 那一份**——可能是同节里的 train 源。"
            "逐条读原文，区分「真点名」与「缩小到 N 份之一」。"),
        "★ 只是泛泛提及（不说哪一份）": sum(1 for x in mentions if not x["★ 点名了是哪一份"]),
        "★ 与出厂模板逐字相同、已豁免的": exempted,
        "**与 holdout 独有内容的 8 词片重叠**": overlaps,
        "★ holdout 词片": len(hold_raw),
        "★ 其中与 train 共有（已扣除）": len(hold_raw & train_sh),
        "★ 扣除后剩下（层二真正比的）": len(hold_sh),
    }
    if not hold:
        # ★ 没有 holdout 时，层二无从谈起——**不当成通过**
        out["★ 本工作区没有 holdout"] = "层二（内容重叠）无从判定，本次只做了层一"
    if hold and not hold_sh:
        out["★★ holdout 正文读不到"] = "层二**未核（不是通过）**——路径字段指的文件不在盘上"
    return out


def self_test() -> int:
    ok = True

    def chk(msg, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print(("  ✓ " if cond else "  ✗ ") + msg)

    print("\n══ ★★★★ 逐字真实样本：Whitworth #152 —— 我自己写的那句泄漏 ══")
    #   下面这段是 `hypotheses.md` 里**原样**的第 2 条，2026-08-07 被候选子代理主动上报。
    #   ★ 它是我在「说明我已经把 holdout 内容删干净了」的语境里写下的。
    REAL = ("2. **他对「别人的产品」有一套稳定的评价方式。**\n"
            "   证据只有 holdout 里那一条，**train 侧没有第二处**，因此只能是假说不能是模式。\n")
    hits = list(MENTION.finditer(REAL))
    chk(f"抓到 {len(hits)} 处：{[h.group(0) for h in hits]}", len(hits) >= 2)
    chk("★ 两处分别是字面 `holdout` 与「train 侧没有」——**两种写法都得认**",
        any(h.group(0).lower() == "holdout" for h in hits)
        and any("train" in h.group(0).lower() for h in hits))

    #   同一天的第二处（较轻）：研究道文档说「有一份 holdout、用于 known 那道题」
    REAL2 = ("**train 侧 2 份来源、6 条发言**；另有 1 份 1 条**划为 holdout**（见第五节）。\n"
             "本节只保留一个事实：**train 侧不含该份内容**，它的用处是 `known` 那道题。\n")
    chk(f"研究道那两处也抓到（{len(list(MENTION.finditer(REAL2)))} 处）",
        len(list(MENTION.finditer(REAL2))) >= 2)

    print("\n── 反向对照：改写之后的版本不许再报 ──")
    FIXED = ("2. **他区分「我的经历」与「可复现的试验」。**\n"
             "   证据：1875 年那句 he believed nine-tenths of it was common air 与同段的实数并置。\n"
             "   **缺的**：只有这一处，一条线画不出模式，故列为假说。\n")
    chk(f"改写版 0 处命中：{[h.group(0) for h in MENTION.finditer(FIXED)]}",
        not list(MENTION.finditer(FIXED)))

    print("\n── 反向对照：正常正文不许被误伤 ──")
    for txt in ("他把「准」当成工序问题，三块面互相研磨。",
                "本道 2 份来源、6 条发言。",
                "The method hitherto adopted in getting up plane surfaces has been to grind them together."):
        chk(f"不报：{txt[:26]}…", not list(MENTION.finditer(txt)))

    print("\n══ ★★★★ 扫的是哪些文件（2026-08-10 —— 缺陷不在检测，在清单）══")
    #   ★ 上面那些用例全在考 `MENTION` 正则，**而正则从来没错过**。
    #     真实缺陷是 `builder_readable_files()` 不含 `references/research/`：
    #     检测再准，没送进去的文件一个也查不到。**所以这一条必须考清单本身。**
    import tempfile as _tf, os as _os
    with _tf.TemporaryDirectory() as _td:
        _r = pathlib.Path(_td)
        (_r / "references" / "research").mkdir(parents=True)
        (_r / "references" / "holdout-notes").mkdir(parents=True)
        (_r / "evidence").mkdir()
        (_r / "facts.md").write_text("# Facts\n", encoding="utf-8")
        (_r / "references" / "research" / "01-writings.md").write_text(
            "★ 本轮 holdout 3 件（Focke 1881），train 17 件。\n", encoding="utf-8")
        (_r / "references" / "holdout-notes" / "00-勘察记录.md").write_text(
            "holdout 定为 Focke 1881《Die Pflanzen-Mischlinge》。\n", encoding="utf-8")
        (_r / "evidence" / "claims.jsonl").write_text("{}\n", encoding="utf-8")
        names = [p.name for p in builder_readable_files(_r)]
        chk(f"★ 正例：研究道文档在清单里（{'01-writings.md' in names}）",
            "01-writings.md" in names)
        chk("★ 断言层也在清单里", "claims.jsonl" in names)
        # ★★ 反例：**记 holdout 的档案本来就该谈 holdout，扫它只会红得没有信息**
        chk(f"★ 反例：`references/holdout-notes/` 不在清单里（{'00-勘察记录.md' not in names}）",
            "00-勘察记录.md" not in names)
        # ★★★ 再加一层反例：**旧清单必须真的抓不到这条**——
        #     否则「修好了」这个结论是靠不住的（改坏它，红要真的红）。
        _old = [_r / n for n in _RENDER] + sorted(
            p for p in _r.glob("*.md") if p.name not in _RENDER)
        chk("★★ 反向验证：按**旧清单**扫，研究道那份确实扫不到（说明这道口子真存在过）",
            "01-writings.md" not in [p.name for p in _old if p.is_file()])

    print("\n── ★ 层二：不提 holdout 但抄了它的内容 ──")
    hold_txt = ("Mr. Whitworth said he had much pleasure in bearing testimony to the great value "
                "of Mr. Chubb's locks he used them almost invariably in his establishment")
    doc_ok = "他谈判据的可复现性，与量法的判读方式。"
    doc_bad = ("他曾说过 he had much pleasure in bearing testimony to the great value of "
               "Mr. Chubb's locks he used them almost invariably in his establishment")
    hs = shingles(hold_txt)
    chk(f"干净正文与 holdout 无重叠：{len(shingles(doc_ok) & hs)}", not (shingles(doc_ok) & hs))
    chk(f"抄了 holdout 的正文被抓到：{len(shingles(doc_bad) & hs)} 个 8 词片",
        len(shingles(doc_bad) & hs) >= 5)

    print("\n── ★★ 豁免：与出厂模板逐字相同的行 ──")
    #   首跑在 Whitworth 上报出 4 处，读命中才发现是脚手架原文，全库 71 个文件都有。
    #   ★ 豁免的依据是「这一行在出厂模板里就有」，**不是把它写进白名单**。
    TMPL = "IDs only; research Agents must not inspect Holdout bodies."
    chk(f"模板原句本身会被层一命中：{bool(MENTION.search(TMPL))}", bool(MENTION.search(TMPL)))
    _t = pathlib.Path(__file__).resolve().parent.parent / "templates" / "target"
    _lines = set()
    if _t.is_dir():
        for tf in _t.rglob("*.md"):
            _lines |= {l.strip() for l in tf.read_text(encoding="utf-8", errors="replace").splitlines() if l.strip()}
    chk(f"而它确实逐字在模板里（模板共 {len(_lines)} 行）", TMPL in _lines)
    PERSON = "他评价别人产品那一条在 holdout 里，train 侧没有。"
    chk("★ 同样的词出现在**人物特定**的句子里则不在模板中 → 照报",
        bool(MENTION.search(PERSON)) and PERSON not in _lines)

    print("\n★ 射程（本件抓不到的）：**不提 holdout 也不抄它，却把题目描述出来**——")
    print("  例如「他评价别人产品的材料我们取不到」：没有关键词、没有重叠、照样泄题。")
    print("  今天那次是靠层一抓到的；**我当时若换个说法就漏了**。")
    print("  层二只能抓同语种的近似复述——**中文转述英文 holdout 的主题，它一个字看不见**。")

    # ★★★ 2026-08-10 新增：**「泛提」与「点名」必须分开**（全库 25 行里只有 3 行是点名）

    print("\n  —— 点名判定（泛提 vs 说出是哪一份）——")

    for _line, _exp, _why in (

        ("> **1877 年的《Sectionstechnik》故意留作 holdout，本路不引它。**", True,

         "Virchow 实例：书名号 + 年份 → **点名**"),

        ("1904 年那篇排斥式电动机的会后书面补充（卷 XXIII pp.63–76）**划为 holdout**，", True,

         "★ Adams 实例：**卷次页码点名、不带书名号** —— 我第一版正则漏的就是它"),

        ("该篇留作 holdout（notes-on-nursing-1860.txt）", True, "文件名 → 点名"),

        ("holdout 见 src-1a59d21f7eab", True, "源 id → 点名"),

        ("本路不引 holdout。", False, "泛提 → **不算点名**"),

        ("> 留出集一旦被引用，known 套组就不可信。", False, "泛提 → **不算点名**"),

        ("本道无**不入训练**的材料。", False,
         "★ 否定句 → 只算泛提，**不点名**（收紧不许误伤这种）"),

        ("本道 **36 件 train**（另有几件不入训练）", False,
         "★ 只说件数不说是哪几件 → 泛提"),

    ):

        chk(f"{_why}", names_the_work(_line) == _exp)

    print("\n══ ★★ 点名在下面两行：**夹具必须是多行的**（2026-08-11）══")
    #   逐字取自语料，**含空行**。第一版我把它们压成一行 → 自测绿而真语料漏。
    _LISTER = ("## 传记（S2，其中一份不入训练）\n"
               "\n"
               "`src-6448ba81d2d2` 等 4 份。\n")
    _KOCH = ("## 传记（皆 S2，其中一份不入训练）\n"
             "\n"
             "`src-b58f8581c014`（Cohn 回忆录，**Fraktur OCR 报废 2.3%**）等 7 份。\n")
    _CLEAN = ("## 传记（S2，其中一份不入训练）\n"
              "\n"
              "共 4 份，此处不列它们的编号。\n")
    _CROSS = ("## 传记（S2，其中一份不入训练）\n"
              "\n"
              "## 另一节\n"
              "\n"
              "`src-6448ba81d2d2` 等 4 份。\n")
    for _lbl, _txt, _exp in (
            ("★★ lister-108 真实多行原文 → **点名**（四选一）", _LISTER, True),
            ("★★ koch-107 真实多行原文 → **点名**（七选一）", _KOCH, True),
            ("★ 反对照：同样的提及，下文**不给编号** → 不点名", _CLEAN, False),
            ("★ 反对照：编号在**另一节**里 → 窗口应在标题处截断，不点名", _CROSS, False)):
        _m = MENTION.search(_txt)
        _got = names_the_work(naming_window(_txt, _m.start())) if _m else None
        chk(_lbl, _got == _exp)
    chk("★ 只看单行时 lister 那条会漏（证明窗口是必须的）",
        names_the_work(_LISTER.splitlines()[0]) is False)

    # ══════════════════════════════════════════════════════════════════
    # ⑧ `scan()` 本身——**2026-08-12 之前它一次也没被自测进入过**
    # ══════════════════════════════════════════════════════════════════
    #
    # 上面全部在考 `MENTION` 正则、`naming_window`、`names_the_work`、
    # `builder_readable_files`、`shingles`——**都是配料**。
    # `scan()` 才是把它们合起来出判决的那一段。
    #
    # ★ 这不是猜的：本文件第 249–257 行的注解**自己写着**
    #   「抓到它的不是自测（自测只考正则与清单函数，**不考 `scan()` 有没有重复喂**），
    #     是我回头读自己刚改过的那段代码」。
    #   那次的后果是**同一批文件进了两次、命中被数了两倍**，
    #   我据此报出过 Mendel 32／Carver 14／Blackwell 12，**真值是它们的一半**，
    #   而且这些数已经写进了提交信息与任务台账。
    #
    # ⑧a 就是那次的回归：**同一个文件不许被喂两次。**
    import tempfile as _tf
    # ★★★ 夹具必须**带上共有的第三方**，否则 ⑧e 那条负对照是假的。
    #   我第一版写成 holdout 全是 `holdoutword*`、train 全是 `trainword*`——两边不相交，
    #   于是「减不减 train」结果一样，**变异 M2（去掉减法）打不红**。
    #   真实情况恰恰相反：Koch #107 的 holdout 正文 **84.7% 本来就在 train 里**
    #   （同一部作品被收进两侧），Nightingale #112 是 44.8%。
    #   ⇒ [[fixtures-cleaner-than-the-real-thing]]：夹具比原文干净就等于没测。
    _shared = " ".join(f"sharedword{i:03d}" for i in range(120))   # holdout 与 train 共有
    _hold_only = " ".join(f"holdoutword{i:03d}" for i in range(120))
    _train_only = " ".join(f"trainword{i:03d}" for i in range(120))
    _hold_body = _shared + " " + _hold_only
    _train_body = _shared + " " + _train_only

    def _mk(td, product_text, *, with_holdout=True, hold_on_disk=True):
        ws = pathlib.Path(td)
        (ws / "evidence").mkdir(parents=True, exist_ok=True)
        (ws / "references/research").mkdir(parents=True, exist_ok=True)
        (ws / "raw").mkdir(parents=True, exist_ok=True)
        rows = [{"source_id": "t1", "split": "train", "local_path": "raw/t1.txt"}]
        if with_holdout:
            rows.append({"source_id": "h1", "split": "holdout", "local_path": "raw/h1.txt"})
        (ws / "evidence/source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) + "\n",
            encoding="utf-8")
        (ws / "raw/t1.txt").write_text(_train_body, encoding="utf-8")
        if with_holdout and hold_on_disk:
            (ws / "raw/h1.txt").write_text(_hold_body, encoding="utf-8")
        (ws / "references/research/01-writings.md").write_text(product_text, encoding="utf-8")
        return ws

    with _tf.TemporaryDirectory() as _td:
        ws = _mk(_td + "/a", "本道有 3 件 holdout，不在此列。\n")
        r = scan(ws)
        chk(f"⑧a **同一个文件不许被喂两次**（扫过 {r['扫过的建模者可读文件']} 份，"
            f"字面提及 {len(r['**字面提及**'])} 处）",
            len(r["**字面提及**"]) == 1)
        chk("⑧a′ 泛泛提及**不算点名**", len(r["**其中点名了是哪一份的**"]) == 0)

    with _tf.TemporaryDirectory() as _td:
        ws = _mk(_td + "/b",
                 "留作 holdout 的是《Die Pflanzen-Mischlinge》。\n见 `src-000000000001`。\n")
        r = scan(ws)
        chk("⑧b 点名作品 → **进「点名了是哪一份」那一栏**",
            len(r["**其中点名了是哪一份的**"]) >= 1)

    with _tf.TemporaryDirectory() as _td:
        ws = _mk(_td + "/c", "本人物的写作以清晰见长。\n")
        r = scan(ws)
        chk("⑧c 没有任何提及 → 两栏都空", not r["**字面提及**"] and not r["**其中点名了是哪一份的**"])

    with _tf.TemporaryDirectory() as _td:
        # ★★ 层二：产物抄了 holdout **独有**的正文 → 必须报重叠
        ws = _mk(_td + "/d", _hold_only[:600] + "\n")
        r = scan(ws)
        chk(f"⑧d 产物含 holdout **独有**正文 → 报重叠"
            f"（{len(r['**与 holdout 独有内容的 8 词片重叠**'])} 处）",
            len(r["**与 holdout 独有内容的 8 词片重叠**"]) >= 1)

    with _tf.TemporaryDirectory() as _td:
        # ★★★ 反向：产物抄的是 **holdout 与 train 共有**的那一段 → **不许**报重叠。
        #   这一条是 [[overlap-metrics-need-a-shared-baseline-subtracted]] 的守卫：
        #   首版没减 train，全库回扫误报 17 处——Koch 的 holdout 正文 84.7% 本就在 train 里，
        #   产物引 train 就会「与 holdout 重叠」，**而那根本不是泄漏**。
        ws = _mk(_td + "/e", _shared[:600] + "\n")
        r = scan(ws)
        chk(f"⑧e 产物抄的是 **holdout 与 train 共有**的段 → **不许**报重叠"
            f"（扣除前共有 {r['★ 其中与 train 共有（已扣除）']} 片、扣除后剩 {r['★ 扣除后剩下（层二真正比的）']} 片）",
            not r["**与 holdout 独有内容的 8 词片重叠**"])
        chk("⑧e′ 且**共有的第三方确实存在**（否则上一条是空过的假绿）",
            r["★ 其中与 train 共有（已扣除）"] > 0)

    with _tf.TemporaryDirectory() as _td:
        ws = _mk(_td + "/f", "干净正文。\n", with_holdout=False)
        r = scan(ws)
        chk("⑧f 没有 holdout → **明写「无从判定」，不是通过**",
            "★ 本工作区没有 holdout" in r)

    with _tf.TemporaryDirectory() as _td:
        ws = _mk(_td + "/g", "干净正文。\n", hold_on_disk=False)
        r = scan(ws)
        chk("⑧g holdout 正文读不到 → **明写「未核」，不是通过** [[empty-default-swallows-unknown]]",
            "★★ holdout 正文读不到" in r)

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("target", nargs="?", help="工作区目录")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.target:
        print("✗ 需要工作区目录（或只给 --self-test）", file=sys.stderr)
        return 3
    r = scan(pathlib.Path(a.target))
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        if "状态" in r:
            print("⚠", r["状态"])
            return 3
        print(f"holdout {r['holdout 份数']} 份；扫过建模者可读文件 {r['扫过的建模者可读文件']} 个")
        n1 = len(r["**字面提及**"])
        n2 = len(r["**与 holdout 独有内容的 8 词片重叠**"])
        if n1:
            print(f"\n✗ **字面提及 {n1} 处**——建模者读得到的文件里不许出现：")
            for m in r["**字面提及**"][:8]:
                print(f"    {m['文件']}:{m['行']}  「{m['命中']}」")
                print(f"        {m['整行']}")
        if n2:
            print(f"\n✗ **与 holdout 正文重叠 {n2} 处**：")
            for o in r["**与 holdout 独有内容的 8 词片重叠**"][:5]:
                print(f"    {o['文件']}：{o['共有 8 词片']} 个片段，如 {o['样本'][:1]}")
        ex = r.get("★ 与出厂模板逐字相同、已豁免的") or []
        if ex:
            # ★ **豁免不许静默**——今天一整天抓的就是「0 被读成通过」这个形状。
            print(f"\n★ 与出厂模板**逐字相同**因而豁免的 {len(ex)} 处"
                  f"（依据是这一行在 templates/target/ 里就有，不是白名单）：")
            for m in ex[:6]:
                print(f"    {m['文件']}:{m['行']}  {m['整行'][:70]}")
        if not n1 and not n2:
            # ★★★ 2026-08-17 第二轮：**层二没跑过就不许说「也没有内容重叠」**。
            #   下面几行确实会印「本工作区没有 holdout：层二无从判定」——
            #   但那是在这句肯定句**之后**，而肯定句本身已经把话说满了。
            #   实测（空工作区）：holdout 0 份，照印「也没有内容重叠」。
            #   [[zero-hit-gates-must-prove-they-can-hit]]
            if "★ 本工作区没有 holdout" in r:
                print("\n⚠ **只做了层一（字面提及）：没有字面提及。**")
                print("   层二（内容重叠）**未核，不是通过** —— 本工作区没有 holdout。")
            else:
                print("\n✓ 没有字面提及，也没有内容重叠")
            print("  ★ 但**这不等于没泄题**：本件抓不到「不提 holdout 也不抄它、"
                  "却把题目描述出来」的写法（见文件头射程）。")
        for k in ("★ 本工作区没有 holdout", "★★ holdout 正文读不到"):
            if k in r:
                print(f"\n⚠ {k}：{r[k]}")
    return 1 if (r.get("**字面提及**") or r.get("**与 holdout 独有内容的 8 词片重叠**")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
