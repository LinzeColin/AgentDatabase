#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_pinned_year_from_relative_date.py —— **断言钉了年份，而它引的原文写的是「上一个」**

## 抓到它的那一次（2026-08-17，Pasteur #106）

产物的 `facts.md` / `persona.md` / `work.md` / `claims.jsonl` / `cases.jsonl`
**五处**都写：

    **1881 年 12 月 10 日**，Lannelongue 医生……患儿次日 10 时 40 分死亡。**记到分钟。**
    confidence 0.95｜status fact

而它自己引的一手原文（CR t.92，`src-4d783fdbfc30`）写的是：

    « Le 10 décembre **dernier**, M. le D r Lannelongue, … »

**`dernier` = 上一个／去年的。** 年份不在这句话里，在**刊期**里 ——
而原刊页眉印着 `C. R., 1881, 1er Semestre. (T. XCII, N° 8.)`：
一篇 1881 年**上半年**刊出的通报说「上一个 12 月」，**不可能是 1881 年 12 月**
（那时还没到），只能是 **1880-12-10**。

**错了整整一年。** 更糟的是它是**事实层**错，`cases.jsonl` 的题面是从
`facts.md` 抄的 ⇒ **尺子与被测物同源**，三轮盲判都测不出来。

## 本件切在哪：**只切「引文里带相对日期词，而断言钉了年份」**

    断言文本里有 `18XX 年 M 月 D 日`（或 `M 月 D 日` + 邻近的四位年）
    且**同一条断言引用的原文片段**里出现相对日期词
      dernier / dernière / passé(e)  ·  last
    （`past` 与 `ult./ultimo` **按语料实测删掉了**，理由见 REL_WORDS 上方注释）
    ⇒ 报出来，人工核刊期

**为什么不切得更宽**：全库一手原文里这类相对日期词有 **12,712 处、339 个源**
（2026-08-17 实测）。按「源里含相对词」去报，会把 339 个源牵连的所有断言全报一遍，
绝大多数与年份无关。⇒ **只报「相对词被抄进了断言自己的引文」那一档**，
精度接近 100%，代价是**看不见没抄引文的那些**——本件把这个射程印出来，不假装覆盖全部。
[[zero-hit-gates-must-prove-they-can-hit]]｜[[a-gates-scan-set-is-smaller-than-reality]]

## ★ `may` / `last` 两义必须排除

英语 `may`（五月／情态动词）与 `last`（上一个／持续）**双双两义**：
「employment of these means **may last** …」不是五月。
实测这一类占原始命中的 **6,221 / 18,933**。本件**整类剔除**，宁可少报。
[[a-signal-that-both-overfires-and-underfires]]｜[[regex-must-clear-the-corpus-language]]

退出码：0＝没有新的（已知的那条照旧印出）；1＝有新的；4＝读不到语料树（未量）。
"""
import argparse
import json
import pathlib
import re
import sys

# ── 相对日期词（`may`/`last may` 由 MODAL_TRAP 剔除）────────────────────
# ★★★ 词表按**语料实测**收紧，不按「听起来像」加：
#   · `ult.` / `ultimo`：英语「上月」义在本语料 **0 例**；命中的全是拉丁语
#     `ultimo`（ultimus 的夺格，与日期无关）与法语 `ultérieurement` 的编码误配 ⇒ **删**
#   · `past`：唯一的「月份 + past」是 `the past march`（进展，**不是三月**）⇒ **删**
#   · `passé` 留下：`juin passé` 实测 12 例，是真的
#   [[a-signal-that-both-overfires-and-underfires]]｜[[read-the-hits-before-reporting-the-rate]]
REL_WORDS = r"(?:dernier|derni[eè]re|pass[ée]e?|last)"
MONTHS = (r"(?:janvier|f[ée]vrier|mars|avril|mai|juin|juillet|ao[ûu]t|septembre|"
          r"octobre|novembre|d[ée]cembre|January|February|March|April|May|June|"
          r"July|August|September|October|November|December)")
REL_DATE = re.compile(r"(\b%s\b\s+\b%s\b|\b%s\b\s+\b%s\b)" % (MONTHS, REL_WORDS, REL_WORDS, MONTHS),
                      re.IGNORECASE)
# ★ 两义陷阱：may（五月/情态动词）× last（上一个/持续）——无上下文判不了，整类剔除
MODAL_TRAP = re.compile(r"^\s*(?:may\s+last|last\s+may)\s*$", re.IGNORECASE)
# 断言里钉死的年月日（中文产物的写法）
PINNED = re.compile(r"1[5-9]\d{2}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日")

# ── 已知且已记台账的（不重复报红）──────────────────────────────────
#   ★ 每条都要带「为什么不修」，否则它就是一个永远红不了的绿灯。
KNOWN = {
    ("wip-pasteur-106", "décembre dernier"):
        "Pasteur #106：正解 1880-12-10（原刊页眉 T. XCII = 1881 上半年）。"
        "`evals/results.jsonl` 128 行非空 ⇒ ㊵ 冻结，本轮不改；"
        "见 `_Pasteur那个日期错了整一年-…-2026-08-17.md`",
}


def relative_dates(text: str) -> list[str]:
    """→ 文本里的相对日期词组（已剔除 may/last 两义）。纯函数。"""
    out = []
    for m in REL_DATE.finditer(text or ""):
        g = re.sub(r"\s+", " ", m.group(0)).strip()
        if MODAL_TRAP.match(g):
            continue
        out.append(g)
    return out


def suspicious(text: str) -> list[str]:
    """→ 同一段文本里**既钉了年月日、又带相对日期词**的那些词组。纯函数。

    ★ 两个条件必须**同段共存**才算 —— 只有相对词（原文常态）或只有年份
    （产物常态）都不算，否则会把 339 个源牵连的一切都报进来。
    """
    if not PINNED.search(text or ""):
        return []
    return relative_dates(text)


def self_test() -> int:
    bad, n = [], [0]

    def chk(lbl, ok):
        n[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    PAST = ("**1881 年 12 月 10 日**，Lannelongue 医生……原文："
            "「Le 10 décembre dernier, M. le D r Lannelongue」")
    chk("★★★ 正例：钉了年月日 + 引文带 `décembre dernier` ⇒ 报出来",
        suspicious(PAST) == ["décembre dernier"])
    chk("★★ 负例：只有相对日期词、没钉年月日（一手原文的常态）⇒ 不报",
        suspicious("« Le 10 décembre dernier, M. le Dr Lannelongue »") == [])
    chk("★★ 负例：钉了年月日但引文没有相对词（产物的常态）⇒ 不报",
        suspicious("**1859 年 11 月 24 日**《物种起源》出版。原文：`On the Origin`") == [])
    chk("★★★ 负例：`may last` 是情态动词+动词，不是五月 ⇒ 不报",
        suspicious("**1888 年 3 月 4 日**……原文：`these means may last`") == [])
    chk("★★★ 负例：`last may` 同上 ⇒ 不报",
        suspicious("**1888 年 3 月 4 日**……原文：`it will last may be longer`") == [])
    chk("★ 正例：英语 `June last` 也要认",
        suspicious("**1889 年 6 月 19 日**……原文：`died on the 19th of June last`")
        == ["June last"])
    chk("★★★ 负例（**实测到的假阳**）：`the past march` 是「进展」不是三月 ⇒ 不报",
        suspicious("**1890 年 5 月 2 日**……原文：`advances made in the past march`") == [])
    chk("★★ 负例：拉丁语 `ultimo`（ultimus 夺格）不是日期 ⇒ 不报",
        suspicious("**1590 年 3 月 1 日**……原文：`ad principale tametsi ultimo positum`") == [])
    chk("★ 正例：法语 `juin passé` 要认（语料实测 12 例）",
        suspicious("**1889 年 6 月 3 日**……原文：`au mois de juin passé`") == ["juin passé"])
    chk("★★ 多个相对词全部报出",
        len(suspicious("**1881 年 12 月 10 日** `décembre dernier` … `June last`")) == 2)
    chk("★ 空文本不炸", suspicious("") == [] and suspicious(None) == [])
    chk("★★ `relative_dates` 单独可用，且剔掉两义那一类",
        relative_dates("may last / décembre dernier") == ["décembre dernier"])
    print("\n自测 %d 项，不符 %d 项" % (n[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--corpora", default=None, help="_corpora 目录")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    # ★★ **本目录上一级也有一个 `_corpora`**（`_ledgers/_corpora/livermore-100/`，
    #   5 份 .txt 且已进 git，含一份 HOLDOUT 章节）——**同名两棵树**。
    #   默认必须指 `parents[2]`（persona-distiller/_corpora，75 个工作区），
    #   指错时不会报错，只会扫出 0 个产物文件。本件第一次跑就踩了，
    #   靠「空扫描面 ⇒ rc=4 未量」这道守卫接住的 —— 若按 0 命中报绿就是假绿。
    #   [[a-gates-scan-set-is-smaller-than-reality]]｜[[zero-hit-gates-must-prove-they-can-hit]]
    corp = pathlib.Path(a.corpora or (pathlib.Path(__file__).resolve().parents[2] / "_corpora"))
    if not corp.is_dir():
        print("★ **未量，不是通过**（rc=4）—— 读不到语料树：%s" % corp)
        return 4

    files = []
    for pat in ("facts.md", "persona.md", "work.md", "claims.jsonl", "cases.jsonl"):
        files += list(corp.rglob(pat))
    if not files:
        print("★ **未量，不是通过**（rc=4）—— 扫描面是空的（%s 下 0 个产物文件）" % corp)
        return 4

    hits, ws_seen = [], set()
    for f in sorted(files):
        ws = f.relative_to(corp).parts[0]
        ws_seen.add(ws)
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        for i, line in enumerate(text.splitlines(), 1):
            for g in suspicious(line):
                hits.append((ws, f.relative_to(corp), i, g))

    print("扫描面：**%d** 个文件 / **%d** 个工作区"
          "（facts.md / persona.md / work.md / claims.jsonl / cases.jsonl）"
          % (len(files), len(ws_seen)))
    print("★ 射程：只看得见**相对日期词被抄进断言自己的引文**那一档。")
    print("  一手原文里这类词有 **12,712 处 / 339 个源**（2026-08-17 实测），")
    print("  读了却没抄引文的，本件一处也看不见 —— **这是射程，不是「全库干净」**。")

    fresh = []
    print("\n逐条：")
    for ws, rel, ln, g in hits:
        note = KNOWN.get((ws, g))
        print("  %s %-22s %-46s L%-5d 「%s」"
              % ("·" if note else "✗", ws, str(rel)[:46], ln, g))
        if note:
            print("      已知：%s" % note)
        else:
            fresh.append((ws, rel, ln, g))
    if not hits:
        print("  （0 条）")

    print("\n合计命中 **%d** 条｜其中已知已记台账 **%d**｜**新出现 %d**"
          % (len(hits), len(hits) - len(fresh), len(fresh)))
    if fresh:
        print("\n✗ **有新的**：断言钉死了年月日，而它引的原文写的是「上一个」。")
        print("  ★ 处置：**去找刊期**（卷、期号、semestre、宣读日）——")
        print("    年份不在那句话里。原刊页眉常常就印着，OCR 会把它混进正文，别当噪声跳过。")
        print("  ★★ 改之前先数副本：Pasteur 那次同一句话在 **5 个文件**里。")
        return 1
    print("\n✓ 没有新的（已知的那条按台账处置，不重复报红）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
