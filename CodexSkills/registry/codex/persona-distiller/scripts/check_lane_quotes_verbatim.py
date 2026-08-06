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
_MARKUP = re.compile(r"\*\*|\*|__|</?[A-Za-z][^>]*>|[«»“”\"]")
# 显式省略号 = 作者声明「这里略去了」，与 `[版口：…]` 同类，按分段各自命中验
_ELISION = re.compile(r"\s*(?:\.\.\.|…)\s*")


# ★★ 印本的**折行连字**与**破折号**在不同扫本里形态不同，比对前一律归一。
#   Lister 实测：同一段话在三份来源里分别印成
#     `same—namely` / `same — namely`，`circum- stances` / `circum¬ stances` / `ac¬ cordance`
#   **这是扫本的差别，不是引文改了字**——与「悄悄改讹字」不是一类。
_HYPHEN_BREAK = re.compile(r"[-¬­]\s+")          # 行末折行连字（含 OCR 的 ¬ 与软连字）
_DASHES = re.compile(r"[—–−]")


def _norm(s: str) -> str:
    s = _MARKUP.sub("", s)
    s = _HYPHEN_BREAK.sub("", s)                 # `circum- stances` → `circumstances`
    s = _DASHES.sub("-", s)                      # 各种破折号归一
    # ★ 这里**不要**再把 ` - ` 缩成 `-`：那是我随手加的一条、没配自测，
    #   当场把 Roberts-Austen 从 0 条对不上打成 2 条
    #   （`[April 20, 1891. — In the course…` → `1891.-In`，
    #     `chronological sequence : —` → `sequence : -`）。
    #   **每加一条归一，就得同时问「它会不会把本来对得上的打散」。**
    return " ".join(s.split())


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
