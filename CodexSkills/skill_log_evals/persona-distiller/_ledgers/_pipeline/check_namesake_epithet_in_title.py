#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_namesake_epithet_in_title.py —— **编目已经把两个同名人分开了，抓源没读那个字**

## 抓到它的那一次

2026-08-14，给 Michelangelo #185 的八条 claim 找第二处证据。八条里六条报「0 部」，
只有一条报回候选 —— 打开一读，是一首**喜剧韵文**（人物叫 Calandrin、Gambasso）。
去查它的台账：

    title   Opere varie in versi ed in prosa di Michelangelo Buonarroti **il giovane**
    tier    P1        attribution  HIS-OWN
    authorship_evidence  ['ia-creator-field']        ← **只有这一条**

**「il giovane」＝ 年轻的那个**：Michelangelo Buonarroti il giovane（1568–1646），
雕塑家（1475–1564）的曾侄孙、剧作家。**三份印本 513,208 词**（train 的 14.6%、
一手的 17.1%）以「他的一手」的身份躺在语料里，唯一依据是 archive.org 的 creator 字段。

★★ 差一点它就成了「第二处证据」：那条 claim 讲「不内行就请第三方估价」，
   候选命中的是**别人诗里**的 `resto gabbato`。**不打开读就写进去了。**

## 既有的同名护栏为什么没拦住

`check_namesake_separability.py` 当场印的是

    · 同名可分性 **跳过（不适用，不是通过）**：找不到同名候选名单

它要一份**人工写的同名候选名单**，Michelangelo 没有 ⇒ 整道门跳过。
[[every-requirement-needs-an-owner]]：护栏挂在一个没人认领的输入上，就等于没有护栏。
而这一次 —— **区分符就印在题名里**。本件不要任何人工名单。

## 判什么

题名里出现「区分同名者的称谓」就报出来，**报了不等于错**：

- `il giovane`／`the younger`／`der Jüngere`／`le jeune` ⇒ 多半**不是本人**（后辈）
- `il vecchio`／`the elder`／`der Ältere`／`l'ancien` ⇒ 多半**就是本人**（长辈）

**两种都要报**：这些词的存在本身就说明**编目在区分两个人**，
而抓源只按姓名匹配，两边都可能拿错。谁是谁要人去定。

## 两条已知的射程（**都是实测出来的，不是推的**）

1. **同一部书的不同印本，题名不一定都带那个词。** Michelangelo 那部有三份印本，
   其中 `src-d89e65b8002f` 的编目题名被截成「Opere varie in versi ed in prosa」，
   **区分符没了**。⇒ 报出一份之后，**必须顺着同作品归并把兄弟印本一起看**
   （`measure_distinct_works.py` 能做这件事）。只修报出来的那两份 = 漏一份。
2. **不要用 `II`／`Jr.`／`Sr.` 当判据。** 第一版把它们写进正则，
   报回 12 行里 8 行是**卷次**（`The River War Vol Ii`、`Bismarck-Briefe: I. … II. …`、
   `A primer of forestry : part II`）。删掉它们之后 4 行全对。
   [[read-the-hits-before-reporting-the-rate]]

## ★ 另一条路：我试过并且**被负对照打掉了**

我先写的是另一件判据：数「正文里的年份落在 `[生年, 卒年]` 之间的占比」，
低于 10% 就报。在 Michelangelo 身上分得极漂亮 ——
il giovane 的三份都是 **0.0%**，他自己最低的一份 26.7%，书信集 93–98%。

**全库一跑就塌了**：15 份命中里，`john-dewey / Leibniz's New Essays…`（Dewey 自己
1888 年写的莱布尼茨评注）、`immanuel-kant / Fundamental principles…`（康德自己的书）、
`johann-pestalozzi / Sämmtliche Schriften`（他自己的全集）都被报了 ——
**写更早时代的人，正文里的年份自然不在自己生前。** 这不是误标，是这个量本身有混杂。
逐人中位数也印证：Comenius 32.7%、Leonardo 42.8%、Machiavelli 52.8% ——
**这些人的语料整体不带年份，尺子在他们身上分不开。**

⇒ 那条路**没有落成判据**，只留在这段注释里。
[[my-checkers-are-mis-cut-six-times-in-one-day]]、
[[baseline-must-be-the-same-kind-as-what-you-compare]]。
**在一个人身上分得漂亮的量，要拿全库当负对照。**

## 用法

    python3 check_namesake_epithet_in_title.py
    python3 check_namesake_epithet_in_title.py --self-test

退出码恒 0：报出来的**不一定是错的**，要人读。
"""
import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from workspace_roots import iter_workspaces  # noqa: E402

CORPORA = HERE.parent.parent / "_corpora"

# 「后辈」与「长辈」两组。**不含 II／Jr.／Sr.** —— 它们在这个语料里几乎全是卷次。
# ★ 德语的属格与 Ae 二合写法要一起收：实测题名写的是「des **Aelteren**」，
#   我第一版只写了 `der Ältere`，自测当场判红——**自测里放真实题名，不放我编的**。
YOUNGER = (r"il giovane|il giovine|the younger|d(?:er|es) j[üu]ngere?n?|"
           r"le jeune|de jonge|el joven")
ELDER = (r"il vecchio|the elder|d(?:er|es) (?:[ÄA]e?lter)e?n?|"
         r"l'ancien|de oude|el viejo")
EPITHET = re.compile(rf"\b({YOUNGER}|{ELDER})\b", re.I)
IS_YOUNGER = re.compile(YOUNGER, re.I)


def classify(title: str):
    """→ (命中的词, '后辈'|'长辈') 或 (None, None)。**纯函数**。"""
    m = EPITHET.search(title or "")
    if not m:
        return None, None
    return m.group(), ("后辈（多半不是本人）" if IS_YOUNGER.search(m.group())
                       else "长辈（多半就是本人）")


def self_test() -> int:
    ok = t = 0

    def chk(d, c):
        nonlocal ok, t
        t += 1
        ok += 1 if c else 0
        print(f"  {'✓' if c else '✗'} {d}")

    # ★★ 正对照：真实那两行题名
    g = classify("Opere varie in versi ed in prosa di Michelangelo Buonarroti il giovane, "
                 "alcune delle quali non mai stampate")
    chk(f"★★ **正对照：`il giovane` 判成后辈**（实得 {g}）", g[0] == "il giovane" and "后辈" in g[1])
    e = classify("Rime di Michelagnolo Buonarroti il vecchio, col comento di G. Biagioli")
    chk(f"★★ **`il vecchio` 判成长辈**（实得 {e}）", e[0] == "il vecchio" and "长辈" in e[1])
    chk("★ 德语 der Jüngere", classify("Cranach der Jüngere")[1].startswith("后辈"))
    chk("★ 德语 des Aelteren（Michelangelo 那两份德文诗集的写法）",
        classify("Michel Angelo Buonarrotti des Aelteren sämmtliche Gedichte")[0] is not None)
    # ★★ 反例：卷次不许命中 —— 第一版正是栽在这里
    for bad in ("The River War Vol Ii", "Bismarck-Briefe: I. Familien-Briefe ; II. Politische",
                "A primer of forestry : part II : practical forestry",
                "0063-conv-1904-repulsion-motor-jr.txt"):
        chk(f"★★ **反例：卷次/文件名不许命中** —— 「{bad[:44]}」", classify(bad)[0] is None)
    # ★★ 那份被截掉区分符的题名：本件**看不见**它 —— 射程要自己说出来
    chk("★★ **已知漏检：区分符被编目截掉的那份，本件看不见**"
        "（`Opere varie in versi ed in prosa`）",
        classify("Opere varie in versi ed in prosa")[0] is None)
    print(f"\n{'✓ 全过' if ok == t else f'✗ {t - ok}/{t} 项不符'}")
    return 0 if ok == t else 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    if ap.parse_args().self_test:
        return self_test()

    wss = list(iter_workspaces(CORPORA))
    rows, scanned, own = [], 0, 0
    for ws in wss:
        led = ws / "evidence/source-ledger.jsonl"
        if not led.is_file():
            continue
        for line in led.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            r = json.loads(line)
            scanned += 1
            a = str(r.get("attribution") or "")
            if a == "HIS-OWN":
                own += 1
            # ★★ **扫全部行，不只 HIS-OWN**：处置过的行（已改成 OTHER／U）
            #   要是从输出里消失，这道门就再也演示不了自己抓到过什么，
            #   而下一个人只会看到一片空白。已处置的照印，只是不打 ❗。
            w, kind = classify(str(r.get("title") or ""))
            if w:
                rows.append((ws.name, r["source_id"], r.get("tier"), r.get("split"),
                             a or "（缺失）", w, kind, str(r.get("title") or "")[:70]))

    print(f"★★ **分母**：台账 **{scanned:,} 行全扫**（不按 attribution 过滤——"
          f"过滤会让已处置的行整个消失，这道门就再也演示不了自己抓到过什么。"
          f"[[filters-make-rows-vanish]]）；其中 `attribution=HIS-OWN` 的 {own:,} 行")
    print(f"⇒ 题名里带「区分同名者」称谓的：**{len(rows)} 行**\n")
    open_n = 0
    for n, sid, tier, sp, attr, w, kind, ti in sorted(rows):
        # ❗ 只给「还挂在他名下的后辈」；已处置的（attribution 不是 HIS-OWN）只是照印
        younger = "后辈" in kind
        hot = younger and attr == "HIS-OWN"
        open_n += 1 if hot else 0
        tail = ("" if hot else
                "　（**已处置**，照印以证明本件抓得到）" if younger else
                "　（长辈＝本人，不用动）")
        print(f"  {'❗' if hot else '·'} {n} / {sid}  tier={tier} split={sp} attribution={attr}"
              f"  **{w}** → {kind}{tail}\n     {ti}")
    print(f"\n⇒ 其中**仍挂在他名下的「后辈」：{open_n} 行**（要处置的就是这些）")
    if not rows:
        print("  ✅ 一行也没有")
    print("\n★ **报了不等于错**：「长辈」那一组多半就是本人。谁是谁要人去定。")
    print("★★ 射程：**同一部书的别的印本，题名不一定带那个词**"
          "（实测有一份被编目截掉了）⇒ 处置任何一行之前，"
          "先用 `measure_distinct_works.py` 把它的兄弟印本一起捞出来。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
