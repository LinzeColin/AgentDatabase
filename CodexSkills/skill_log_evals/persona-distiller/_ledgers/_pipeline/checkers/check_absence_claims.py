#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""绝对化／不在场断言体检 —— 产物文档专用（RUNBOOK 第十六种的第二个工具）。

## 为什么单独做一个

评委只看 evals，**产物文档没有评委**。Jesse Vincent #94 里同一个 star 错误有三个落点，
其中两个在产物文档（`boundaries.md`、`references/research/04-external.md`），
分别在第一轮和第二轮才被翻出来——而 `case-boundary-1` 第一轮就被评委抓到了。

## 它查什么

「完全没有」「从未」「无任何」「只有」这类断言**本身不是错**，
错的是**下断言时没有说明检索方式**。本脚本把它们全部列出来，
由人逐条确认：**这一条的依据在哪，检索范围是什么。**

**不做自动判定**——判定不在场需要看语料，脚本看不了。它只保证「一条都不漏看」。
"""
import argparse, pathlib, re, sys

PAT = re.compile(r"[^。\n]{0,60}(完全没有|从未|从没|从来没|毫无|一次也没|无任何|没有任何|"
                 r"绝无|全部都是|一律是|只有|唯一|均未|皆无)[^。\n]{0,60}")
# 依据词：同句/邻近出现即视为已给检索方式
GROUND = re.compile(r"(全文检索|逐条查|命中\s*0|0\s*次|份来源|份书面|检索过|逐字|原话|原文|"
                    r"其本人|一手|有日期|可逐字核)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path)
    ap.add_argument("--context", type=int, default=160, help="判定依据的邻近窗口")
    a = ap.parse_args()

    n_all = n_bare = 0
    for f in sorted(a.workspace.rglob("*.md")):
        t = f.read_text(encoding="utf-8", errors="replace")
        rows = []
        for m in PAT.finditer(t):
            n_all += 1
            ctx = t[max(0, m.start() - a.context):m.end() + a.context]
            ok = bool(GROUND.search(ctx))
            if not ok:
                n_bare += 1
            rows.append((ok, re.sub(r"\s+", " ", m.group(0)).strip()))
        if rows:
            print(f"\n── {f.relative_to(a.workspace)}")
            for ok, s in rows:
                print(f"   {'✓' if ok else '⚠'} {s[:110]}")

    print(f"\n合计 {n_all} 条绝对化断言，其中 {n_bare} 条邻近未见检索依据")
    print("⚠ 标记的须人工确认依据；本脚本不做自动判定" if n_bare else "✓ 全部带依据")
    return 0


if __name__ == "__main__":
    sys.exit(main())
