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
    r"(?:不计入|不列入)本道",
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
            rec = {"文件": f.name, "行": line, "命中": m.group(0), "整行": whole[:160]}
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
            print("\n✓ 没有字面提及，也没有内容重叠")
            print("  ★ 但**这不等于没泄题**：本件抓不到「不提 holdout 也不抄它、"
                  "却把题目描述出来」的写法（见文件头射程）。")
        for k in ("★ 本工作区没有 holdout", "★★ holdout 正文读不到"):
            if k in r:
                print(f"\n⚠ {k}：{r[k]}")
    return 1 if (r.get("**字面提及**") or r.get("**与 holdout 独有内容的 8 词片重叠**")) else 0


if __name__ == "__main__":
    raise SystemExit(main())
