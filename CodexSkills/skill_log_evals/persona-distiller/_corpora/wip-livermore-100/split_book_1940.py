#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 1940 年那本书按**作者**切开，再入库。

## 为什么必须切

《How to Trade in Stocks》(1940) 的前言 **不是 Livermore 写的**，
署名 `EDWARD JEROME DIES`（第 123 行）。前言里是 Dies 用第三人称谈他：

    Each move was touched with singular genius, buttressed by
    endless research and the dogged patience of Griselda.

整本以 `--tier P1 --author "Jesse L. Livermore"` 灌进去，
**这句会变成「他自己的话」**——而它是别人对他的溢美。
这正是 Steinhardt #98 那次的失败模式，只是这次发生在**一个文件内部**
（那次是刊物按页切片后一律冠上人物前缀）。

`check_authorship.py` 在这里帮不上忙：它按**整份文件**判归属，
而这份文件确实有 Livermore 的署名页。**按文件判的门，看不见文件内部的换人。**

## 切法（按行号，来自实测）

| 段 | 行 | 归谁 | 处置 |
|---|---|---|---|
| 版权页 / 题献 | 0–34 | 出版社 | **不入库**（无内容价值） |
| **PREFACE** | 35–133 | **Edward Jerome Dies** | 入库为 `S1`，作者写 Dies，**只作 external 路用** |
| CONTENTS | 134–159 | — | **不入库** |
| 正文 I–IX | 160–末 | **Jesse L. Livermore** | 入库为 `P1` |

行号写死是有意的：**它必须可复核**。跑 `--verify` 会打印每段的首尾各两行，
切错了一眼就能看出来。
"""
import argparse
import pathlib
import sys

PREFACE_START = 35
# 123 = `EDWARD JEROME DIES` 署名行。第一次写成 133，`--verify` 立刻显示
# 该段尾部混进了目录的 `VIII.` / `IX.` 两行——**边界打印就是为了看这个**。
PREFACE_END = 123
BODY_START = 160

# ★ `body_livermore` = **扉页 + 正文**，中间挖掉 Dies 的前言与目录。
#   带上扉页是有意的：那里有 `COPYRIGHT, 1040, BY / JESSE 1. LIVERMORE`，
#   是这份文件**自带的归属证据**（v0.0.0.18 的 A-copyright 判据认它）。
#   切掉扉页会让一份货真价实的亲笔著作变成「无据」——
#   **归属证据在扉页上，而要防的东西在前言里，两者不能一刀切掉。**
SEGMENTS = [
    ("preface_dies", [(PREFACE_START, PREFACE_END + 1)], "Edward Jerome Dies", "S1"),
    ("body_livermore", [(0, PREFACE_START), (BODY_START, None)], "Jesse L. Livermore", "P1"),
]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=pathlib.Path)
    ap.add_argument("--outdir", type=pathlib.Path, required=True)
    ap.add_argument("--verify", action="store_true", help="只打印每段边界，不写文件")
    a = ap.parse_args()

    lines = a.source.read_text(encoding="utf-8", errors="replace").splitlines()
    a.outdir.mkdir(parents=True, exist_ok=True)

    for name, ranges, author, tier in SEGMENTS:
        chunk: list = []
        for start, end in ranges:
            chunk.extend(lines[start:end] if end is not None else lines[start:])
        body = [l for l in chunk if l.strip()]
        if a.verify:
            spans = " + ".join(f"{s}..{(e - 1) if e else len(lines) - 1}" for s, e in ranges)
            print(f"\n=== {name}  行 {spans}  "
                  f"作者={author}  tier={tier}  非空行={len(body)}")
            for l in body[:2]:
                print(f"    首| {l.strip()[:80]}")
            for l in body[-2:]:
                print(f"    尾| {l.strip()[:80]}")
            continue
        if author is None:
            continue
        out = a.outdir / f"jl_1940_HowToTradeInStocks_{name}.txt"
        out.write_text("\n".join(chunk).strip() + "\n", encoding="utf-8")
        print(f"{out.name}\t{len(body)} 非空行\tauthor={author}\ttier={tier}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
