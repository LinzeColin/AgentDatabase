#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""check_generators_respect_freeze.py —— **`gen_cases_*.py` 会无条件重写用例**

## 抓到它的那一次（2026-08-17）

我在探测「哪些脚本有 `--self-test`」时，写了个探针：**拿参数跑一遍，看它印什么**。
`gen_cases_brandeis.py --self-test` 印了 `✓ 写出 32 题 …` —— 我的探针把那个 `✓`
读成「自测通过」，实际上它**根本不看 argv，直接把用例文件重写了一遍**。
brandeis / churchill / dewey 三份 `cases.jsonl` 的 mtime 全部变成那一刻。

**损害为零，但那是运气**：三份都在 git 里、生成是确定性的、逐字节与 HEAD 一致，
且三人 `results.jsonl` 都是 0 行（未判分，不触 ㊵）。
换成一个已判分的人，就是**无声覆盖冻结的评测材料**。
[[i-create-the-leak-channels-myself]]：**探测本身就是执行**——
「跑一遍看它印什么」不能用来探测能力。

## 本件判什么

对每个 `gen_cases_*.py`：

1. 解出它的目标工作区 —— **解不出就 rc=1「未量」**，不许当成没问题；
2. 目标的 `results.jsonl` 非空 ⇒ **rc=1**：跑一下它就违反
   ㊵「已判分即冻结」，而**脚本自己一行守卫都没有**。

## ★★ 它不是守卫，是探测器（必须一起念）

本件**拦不住**任何人手敲 `python3 gen_cases_X.py`。真正的守卫要写在那 12 个脚本里，
而它们写法各异（有的 `OUT.write_text`、有的函数内 `p.write_text`、
有的把整条路径写成一个字符串）。本件先把**风险可见**并钉住不许恶化。
[[a-rule-in-a-doc-has-no-enforcer]]｜[[a-penalty-is-not-a-rule]]

## ★ 抽取为什么要泛化

第一版要求 `"wip-xxx"` **整个被引号包住**，于是 churchill / dewey / lincoln
三件（把 `_corpora/wip-…/workspaces/…` 写成**一整条路径字符串**）全部「抽不出」。
判据的形状 ＝ 我上一次探查的形状。改成**在全文里找子串**。
[[a-gates-scan-set-is-smaller-than-reality]]｜[[one-requirement-two-consumers]]

退出码：0＝全部解得出且都未判分；1＝有解不出的或有已判分的；4＝一件都没扫到（未量）。
"""
import argparse
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
SKILL = HERE.parent.parent                      # …/persona-distiller
CORPORA = SKILL / "_corpora"


def known_names(corpora: pathlib.Path):
    """→ (wip 目录名集合, 工作区 slug 集合)。目录不在就返回两个空集。"""
    if not corpora.is_dir():
        return set(), set()
    wips = {p.name for p in corpora.glob("wip-*") if p.is_dir()}
    slugs = {q.name for q in corpora.glob("wip-*/workspaces/*") if q.is_dir()}
    return wips, slugs


def target(src: str, wips: set, slugs: set):
    """→ (wip, slug)；任一解不出或有歧义则该项为 None。**纯函数。**

    ★ 用**子串**匹配，不要求被引号单独包住 —— 三件把整条路径写成一个字符串。
    """
    w = sorted(x for x in wips if x in src)
    g = sorted(x for x in slugs if x in src)
    # 同名前缀会互相命中（wip-kant-179 与 wip-kant-179b），取最长的那个；
    # 长度相同却有多个 ⇒ 真歧义，报 None。
    def pick(c):
        if not c:
            return None
        m = max(len(x) for x in c)
        top = [x for x in c if len(x) == m]
        return top[0] if len(top) == 1 else None
    return pick(w), pick(g)


def scored_lines(ws: pathlib.Path) -> int:
    """→ `evals/results.jsonl` 的**非空行数**；文件不在算 0。"""
    r = ws / "evals" / "results.jsonl"
    if not r.is_file():
        return 0
    return sum(1 for l in r.read_text(encoding="utf-8", errors="replace").splitlines()
               if l.strip())


def self_test() -> int:
    bad = []
    tot = [0]                       # ★ 总数**现算**：手写的「8 项」当场就漂成了 9。
    #                                 [[self-reported-numbers-must-be-computed.md]]

    def chk(lbl, ok):
        tot[0] += 1
        print(("  ✓ " if ok else "  ✗ ") + lbl)
        if not ok:
            bad.append(lbl)

    W = {"wip-brandeis-172", "wip-churchill-191"}
    G = {"louis-brandeis", "winston-churchill"}
    chk("★★ **分段引号**那种写得出（brandeis 形状）",
        target('W = HERE / "_corpora" / "wip-brandeis-172" / "workspaces" / "louis-brandeis"',
               W, G) == ("wip-brandeis-172", "louis-brandeis"))
    chk("★★★ **整条路径写成一个字符串**那种也写得出（churchill 形状）—— "
        "第一版就是在这里漏掉三件",
        target('OUT = (p / "_corpora/wip-churchill-191/workspaces/winston-churchill/evals/cases.jsonl")',
               W, G) == ("wip-churchill-191", "winston-churchill"))
    chk("★★ 抽不出 → **(None, None)**，不是随便挑一个",
        target("这个文件里什么路径都没有", W, G) == (None, None))
    chk("★★ 同长度多个候选 ⇒ **报歧义**，不许挑第一个",
        target("wip-a-1 wip-b-1", {"wip-a-1", "wip-b-1"}, set())[0] is None)
    chk("★ 前缀互相命中时取**最长**的那个",
        target("wip-kant-179b", {"wip-kant-179", "wip-kant-179b"}, set())[0] == "wip-kant-179b")

    import tempfile
    with tempfile.TemporaryDirectory() as td:
        ws = pathlib.Path(td) / "w"
        (ws / "evals").mkdir(parents=True)
        chk("★★ results.jsonl **不存在** ⇒ 0（未判分）", scored_lines(ws) == 0)
        (ws / "evals" / "results.jsonl").write_text("\n\n  \n", encoding="utf-8")
        chk("★★★ **只有空行的 results.jsonl 算未判分**（0），"
            "不是「文件在就算判过」", scored_lines(ws) == 0)
        (ws / "evals" / "results.jsonl").write_text('{"a":1}\n{"b":2}\n', encoding="utf-8")
        chk("★ 两行真结果 ⇒ 2", scored_lines(ws) == 2)

    # ★★★ 正对照：真语料上**解得出至少 10 件**，否则上面那些 None 断言是恒真。
    wips, slugs = known_names(CORPORA)
    gens = sorted(HERE.glob("gen_cases_*.py"))
    if not gens or not wips:
        chk("★★★ 正对照**未判**：本机没有 gen_cases_* 或没有 _corpora —— 未量，不是通过", False)
    else:
        okn = sum(1 for p in gens
                  if all(target(p.read_text(encoding="utf-8", errors="replace"), wips, slugs)))
        chk("★★★ 正对照：真语料上 **%d/%d** 件解得出目标（要求 ≥10，否则上面的 None "
            "断言在「恒解不出」时也全过）" % (okn, len(gens)), okn >= 10)
    print("\n自测 %d 项，不符 %d 项" % (tot[0], len(bad)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return self_test()

    gens = sorted(HERE.glob("gen_cases_*.py"))
    wips, slugs = known_names(CORPORA)
    print("扫描面：`gen_cases_*.py` **%d** 件｜已知 wip 目录 %d 个｜已知工作区 %d 个"
          % (len(gens), len(wips), len(slugs)))
    if not gens or not wips:
        print("★ **未量，不是通过**（rc=4）—— 扫描面是空的："
              "gen_cases_* %d 件、wip 目录 %d 个" % (len(gens), len(wips)))
        return 4

    unresolved, frozen, clean = [], [], []
    for p in gens:
        w, g = target(p.read_text(encoding="utf-8", errors="replace"), wips, slugs)
        if not (w and g):
            unresolved.append((p.name, w, g))
            continue
        n = scored_lines(CORPORA / w / "workspaces" / g)
        (frozen if n else clean).append((p.name, w, g, n))

    print("\n%-27s %-24s %-25s %s" % ("生成器", "wip 目录", "工作区", "results.jsonl"))
    for n_, w, g, k in sorted(clean):
        print("%-27s %-24s %-25s %d" % (n_, w, g, k))
    for n_, w, g, k in sorted(frozen):
        print("%-27s %-24s %-25s **%d ← 已判分**" % (n_, w, g, k))
    for n_, w, g in unresolved:
        print("%-27s %-24s %-25s —" % (n_, w or "**抽不出**", g or "**抽不出**"))

    print("\n合计：解得出且未判分 **%d**｜**已判分 %d**｜**抽不出 %d**"
          % (len(clean), len(frozen), len(unresolved)))
    if frozen:
        print("\n✗ **跑一下就违反 ㊵** —— 上面这些生成器指着已判分的工作区，"
              "而它们**一行守卫都没有**，会无条件重写 `cases.jsonl`。")
        return 1
    if unresolved:
        print("\n✗ **未量，不是通过** —— 有 %d 件解不出目标，"
              "本件说不出它们会不会覆盖冻结材料。" % len(unresolved))
        return 1
    print("\n✓ %d 件生成器的目标**全部未判分** —— 今天跑它们不会覆盖冻结材料。" % len(clean))
    print("  ★ 但本件是**探测器不是守卫**：拦不住手敲。真守卫要写进那 12 个脚本里。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
