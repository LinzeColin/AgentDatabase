#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**文档里写的门槛数，与代码里真正在用的那套，是不是同一套。**

## 起因：我把 deep 的门槛当成了通用门槛，连报三处

`RUNBOOK.md` 原先写着一行：

    **必须 0 错 0 警**。阈值：总分≥0.80、delta≥0.07、边界≥0.85、事实保持≥0.93。

那四个数**是 deep 那一档的**，而这行字里**没有「deep」两个字**。
于是我把 `delta ≥ 0.07` 当成了通用门槛，写进了三处记录：

| 人物 | 实际 profile | 真门槛 | 我写的 |
|---|---|---|---|
| Barton #117 | deep | 0.07 | 0.07 ✓ |
| **Thomson #129** | **quick** | **0.03** | 0.07 ✗ |
| Adams #131（本轮） | quick | 0.03 | 差点又按 0.07 判 |

★ Thomson 的结论没被改变（−0.0859 对 0.03 也过不了），
**但「按错的门槛去判一个人过没过」这件事本身，只是这一次刚好不影响结论。**

## 它查什么

`PROFILE_THRESHOLDS` 是**唯一真源**。本件把它与 `RUNBOOK.md` 里那张表逐格比对：
文档少写一档、多写一档、或某一格数字不一致，都报。

★ **只认带 profile 名的表格行**。散文里出现「0.07」不算——
那正是原来的写法，而**问题恰恰是它没说自己是哪一档**：
所以本件的口径是「**门槛必须写在带档位名的行里**」，
散文式的孤零零一个数字**一律视为没写**。

## 只报不拦？不——**硬门**

文档与代码不一致，代价不是「文档旧了」，是**读文档的人会按错的数下判断**，
而这条流水线里读文档的人主要是我自己。
"""
import argparse
import importlib.util
import pathlib
import re
import sys

KEYS = (("min_overall_score", "总分"), ("min_baseline_delta", "delta"),
        ("min_boundary_score", "边界"), ("min_fact_score", "事实保持"))
HERE = pathlib.Path(__file__).resolve().parent


def load_thresholds(qc: pathlib.Path) -> dict:
    spec = importlib.util.spec_from_file_location("_pd_qc", qc)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.PROFILE_THRESHOLDS


def doc_rows(text: str) -> dict:
    """→ {profile: [数字...]}，只认**以档位名开头的表格行**。"""
    out = {}
    for prof in ("quick", "standard", "deep"):
        m = re.search(rf"^\s*\|\s*{prof}\s*\|(.+?)\|\s*$", text, re.M)
        if m:
            out[prof] = [float(x) for x in re.findall(r"\d*\.\d+", m.group(1))]
    return out


def check(qc: pathlib.Path, doc: pathlib.Path) -> int:
    want = load_thresholds(qc)
    got = doc_rows(doc.read_text(encoding="utf-8"))
    bad = []
    print(f"代码真源：{qc.name}　文档：{doc.name}")
    for prof in ("quick", "standard", "deep"):
        w = [want[prof][k] for k, _ in KEYS]
        g = got.get(prof)
        if g is None:
            bad.append(f"✗ **文档里找不到 `{prof}` 那一行**（散文里的孤零零一个数字不算——"
                       f"原来的写法就是那样，问题正是它没说自己是哪一档）")
            print(f"  {prof:9} 文档 **缺**　代码 {w}")
            continue
        if g != w:
            bad.append(f"✗ **`{prof}` 对不上**：文档 {g}　代码 {w}")
        print(f"  {prof:9} 文档 {g}　代码 {w}　{'✓' if g == w else '✗'}")
    for b in bad:
        print("  " + b)
    if bad:
        print("\n✗ **门槛表与代码不一致——改文档去迁就代码，不许反过来。**")
        return 1
    print("\n✓ 门槛表与代码逐格一致")
    return 0


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    good = ("| profile | 总分 | delta | 边界 | 事实保持 |\n"
            "|---|---|---|---|---|\n"
            "| quick    | ≥0.65 | ≥0.03 | ≥0.70 | ≥0.80 |\n"
            "| standard | ≥0.72 | ≥0.05 | ≥0.78 | ≥0.88 |\n"
            "| deep     | ≥0.80 | ≥0.07 | ≥0.85 | ≥0.93 |\n")
    r = doc_rows(good)
    chk(f"三档都读到：{sorted(r)}", sorted(r) == ["deep", "quick", "standard"])
    chk(f"quick 那行读成 {r['quick']}", r["quick"] == [0.65, 0.03, 0.70, 0.80])

    print("\n── ★★★ 反向对照①：**原来那句散文，必须读成「没写」** ──")
    prose = "**必须 0 错 0 警**。阈值：总分≥0.80、delta≥0.07、边界≥0.85、事实保持≥0.93。\n"
    r2 = doc_rows(prose)
    chk(f"散文里的四个数一档也不算：{r2}", r2 == {})

    print("\n── ★★ 反向对照②：某一格数字被改动 → 必须报出来 ──")
    tampered = good.replace("≥0.03", "≥0.07")
    r3 = doc_rows(tampered)
    chk(f"quick 的 delta 变成 0.07 被读出来：{r3['quick']}", r3["quick"][1] == 0.07)
    chk("与真值 0.03 不同", r3["quick"][1] != 0.03)

    print("\n── ★ 反向对照③：少写一档 → 那一档要判成「缺」 ──")
    missing = "\n".join(l for l in good.splitlines() if "standard" not in l)
    chk("standard 读不到", "standard" not in doc_rows(missing))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--quality-check", type=pathlib.Path,
                    default=HERE / "quality_check.py")
    ap.add_argument("--doc", type=pathlib.Path,
                    default=HERE.parent / "references/pipeline/RUNBOOK.md")
    ap.add_argument("--self-test", action="store_true")
    a = ap.parse_args()
    if a.self_test:
        return self_test()
    if not a.quality_check.is_file():
        print(f"✗ 找不到代码真源：{a.quality_check}——**未核，不是通过**")
        return 3
    if not a.doc.is_file():
        print(f"✗ 找不到文档：{a.doc}——**未核，不是通过**")
        return 3
    return check(a.quality_check, a.doc)


if __name__ == "__main__":
    sys.exit(main())
