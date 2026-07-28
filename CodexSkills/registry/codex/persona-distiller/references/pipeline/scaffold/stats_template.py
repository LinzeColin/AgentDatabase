#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""【脚手架】人物产物里所有计数的**唯一真源**。每人复制一份，只改 CORPUS_DIR 与 FACTS。

## 为什么每个人物都要有这个文件

Maeda 一轮出过一个真错：产物里写「38 篇动手笔记里 22 篇（58%）标题含年份」，
而真值是 11 篇 29%。错因是统计代码在**完整文件名**上匹配年份，
而文件名前缀 `jm_YYYY_` 是我自己加的——**它数的是我写进文件名的年份**。

自查时改用 `f[8:]` 跳过前缀，得到 6 篇（16%），**这次也错**——slug 在 46 字符处截断，
「in November 2024」这类长标题的年份被截掉。**两次都错，方向相反。**

一个错误的数字散在 6 处生成器 / 5 处产物（RUNBOOK 第十六种）。

**定则：凡是会出现在产物里的计数，一律在这里现算，生成器只许引用、不许手写。**
手写的数字会在语料变动、口径变动或我数错时静默失效，而所有的门都查不出来
——门查的是格式与引用，不查我的算术。

## 三条口径纪律

0. **引文里的数字关系，要另外核一遍算得通不算得通**（Robertson #97，RUNBOOK 第六十一种）。
   他清盘信里写「the 8.8 million had grown to 21 billion, and increase of over 259,000%」——
   **210 亿 ÷ 880 万 = 2,386 倍 = +238,536%，不是 259,000%**，缺口 8.6%，就在同一句话里。
   我漏掉它是因为那半句是**引文**：引文完整性检查回答的是「他说没说过」，
   **回答不了「他说的对不对」**，而我又因为它是引文默认它内部自洽。

   所以每人物的 stats 里应该有一段这样的自检：

   ```python
   def cross_check():
       """产物里引用的数字关系，逐条算一遍。算不通的**写进产物**，不要抹平。"""
       checks = [("规模倍数", 21e9 / 8.8e6, 2590, "他写 over 259,000% 即 2590 倍")]
       for name, got, want, note in checks:
           if abs(got - want) / want > 0.02:
               print(f"  ⚠ {name}: 算得 {got:,.0f}，声称 {want:,.0f}（{note}）")
   ```

   **一手件的作者也会算错、会取整、会把两个时点的数写进同一句。**

1. **分子分母必须同口径。** Maeda 一轮查出 divergence-map 用净化前 118 篇做分母，
   而同一行的分子是在净化后 97 篇上验证的。
2. **train / 全量必须声明。** 门报的是 train-only；产物若不写明口径，读者无从判断哪个对。
"""
import functools, json, os, re

HERE = os.path.dirname(os.path.abspath(__file__))
CORPUS_DIR = os.path.join(HERE, "core_XXXX")          # ← 每人改这一行
LEDGER = os.path.join(HERE, "ws-XXXX/XXXX/evidence/source-ledger.jsonl")  # ← 与这一行
TITLE_RE = re.compile(r"\s*(.{4,120}?)\s*\|\s*", re.S)                    # ← 站点标题分隔符


def files():
    return sorted(f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt"))


@functools.lru_cache(maxsize=None)
def read(f):
    return open(os.path.join(CORPUS_DIR, f), encoding="utf-8").read()


def title(f):
    """**从正文取标题，不要用文件名代替**——文件名带我加的前缀且会被截断。"""
    m = TITLE_RE.match(read(f))
    return (m.group(1) if m else read(f).split("\n")[0][:90]).replace("\n", " ").strip()


def rate(pattern, corpus=None):
    """返回 (命中篇数, 总篇数, 百分比串)。**分母永远是同一个 files()**。"""
    fs = corpus or files()
    n = sum(1 for f in fs if re.search(pattern, read(f), re.I))
    return n, len(fs), f"{n / len(fs):.0%}" if fs else "0%"


def rate_robust(patterns, corpus=None):
    """**同一结论在宽窄不同的检索式下是否都成立**（RUNBOOK 第三十七种）。

    Maeda 一轮评委复现不出我的「65/81」，因为产物只给了数字没给判据。
    改正后发现：绝对数随词表从 36 跳到 147（4 倍），而**集中度纹丝不动 80–83%**。
    绝对数是词表的产物，比例才是语料的性质。**产物里要引比例并附这张表。**
    """
    return {name: rate(p, corpus) for name, p in patterns.items()}


def lane_counts(split="train"):
    import collections
    c = collections.Counter()
    for line in open(LEDGER, encoding="utf-8"):
        r = json.loads(line)
        if split and r.get("split") != split:
            continue
        for d in r.get("dimensions", []):
            c[d] += 1
    return dict(c)


def primary_ratio(split="train"):
    rows = [json.loads(l) for l in open(LEDGER, encoding="utf-8")]
    if split:
        rows = [r for r in rows if r.get("split") == split]
    return round(sum(1 for r in rows if r.get("tier") in ("P1", "P2")) / len(rows), 4)


def corpus_size():
    fs = files()
    return len(fs), sum(len(read(f)) for f in fs)


_n, _c = corpus_size()
FACTS = {                                   # ← 每人在这里加本人物特有的计数
    "corpus_n": _n,
    "corpus_chars": f"{_c:,}",
    "corpus_wan": f"{_c/10000:.1f}",
    "lanes_train": lane_counts("train"),
    "primary_train": primary_ratio("train"),
}

if __name__ == "__main__":
    for k, v in FACTS.items():
        print(f"  {k:<18} {v}")
