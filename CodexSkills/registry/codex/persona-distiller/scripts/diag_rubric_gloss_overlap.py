#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""诊断（**不接线、不改门**）：判据与候选答案之间的**中文对中文**重合。

## 为什么这个角度可能有用

`check_rubric_copies_answer` 找的是**长字面串**，报 Adams 0/16。
而两席评委各自数出 7–9 题，举的例子是：

    判据「取决于制造与使用两侧的许多细节」
    ← 候选答案里那句英文引文 `depends upon avery great many details not only of manufacture but`

看上去是「跨语言，抓不到」。**但漏了一件事**：候选答案在引完英文之后，
自己也用中文把它复述了一遍（「制造这一侧和使用这一侧的细节都算数」）。
**于是判据的中文与答案的中文之间，是有字面重合的**——只是短，且被 `MIN_RUN=24` 滤掉了。

所以本诊断量的是：**判据与答案共有的中文串（≥6 字），且该串不在题面里**。
减去题面是关键——题面里本来就会出现的词（人物名、题目关键词）不算抄。

## ★★★ 为什么叫 `diag_` 而不是 `check_`

本项目的元判据 `check_checkers` 会普查「每件 `check_*.py` 有没有生产调用方」，
**没有调用方就报硬失败**——这是对的，今天刚靠它抓出 `check_material_split`
（45 份 holdout 里 18 份从未隔离）。

而本件**故意不接线**（理由见下）。若仍叫 `check_*`，它会让那道普查**长期挂一条红**，
而**一条永远变不绿的红不是信号**——看久了人就不看它了。

**所以按它的真实身份命名：它是诊断，不是门。**
将来若裁定 ⑳ 决定把它变成门，再改名并接线。

## ★★ 它**故意没有被接进任何门**，这不是遗漏

要不要把「抄答案」这道判据加固到能看中文重合，**是待裁定 ⑳ 的内容**。
在裁定之前把它接成门，等于我自己替用户把那个决定做了。
**所以它现在只是一件可手跑的诊断，只报形状。**

★ 但它已经在 4 个人物上跑过（≥2 次同逻辑复用），
按本项目的规矩就**必须从临时脚本变成带自测的共享件**——
否则它会和历次那些「每人一份、不进任何门、没有自测」的脚本一样，
**算出唯一的成绩单，却没有人验过它对不对**。

## 实测（2026-08-05）

| 工作区 | 中文重合题 | |
|---|---|---|
| comfort-avery-adams | **2/16 = 12%** | 四人里最干净（第一批按 v2 规则写的 rubric） |
| george-washington-carver | 5/16 = 31% | 已入库 |
| gregor-mendel | **7/16 = 44%** | **此前从未被任何判据量过这一项** |
| elihu-thomson | **7/16 = 44%** | **同上** |

抽样核过 Mendel 命中最多的一条，判据把答案那半句**连破折号一起**写了进去，
而题面里没有那句话——**是真命中，不是用词碰巧相近**。

★★★ **但要知道它的上限**：Adams 上两席评委各自点名 8 题与 5 题，
本件只找到 **2 题**。**加固字符串检测能从 0 走到 2，走不到 8。**
剩下的是真正的语义对应（英文引文 → 判据里的中译），没有便宜的字符串办法。
"""
import json
import pathlib
import re
import sys

CJK = re.compile(r"[一-鿿]")
MIN_RUN = 6


def cjk_runs(a: str, b: str, minlen: int = MIN_RUN) -> list:
    """→ a 与 b 共有的、长度 ≥minlen 的**纯中文**子串（去掉被包含的）。"""
    a_c = re.sub(r"[^一-鿿]+", "\n", a)
    b_c = re.sub(r"[^一-鿿]+", "\n", b)
    bset = set()
    for seg in b_c.split("\n"):
        for i in range(len(seg) - minlen + 1):
            bset.add(seg[i:i + minlen])
    out = []
    for seg in a_c.split("\n"):
        i = 0
        while i <= len(seg) - minlen:
            if seg[i:i + minlen] in bset:
                j = i + minlen
                while j < len(seg) and seg[i:j + 1] in b_c:
                    j += 1
                out.append(seg[i:j])
                i = j - minlen + 1
            else:
                i += 1
    out.sort(key=len, reverse=True)
    kept = []
    for s in out:
        if not any(s in k for k in kept):
            kept.append(s)
    return kept


def run(ws: pathlib.Path) -> dict:
    cases = {}
    f = ws / "evals/cases.jsonl"
    if not f.is_file():
        return {}
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip():
            r = json.loads(line)
            cases[r["case_id"]] = r
    ap = ws / "evals/candidate_answers.json"
    if not ap.is_file():
        return {}
    ans = json.loads(ap.read_text(encoding="utf-8"))
    hits, total_chars = {}, 0
    for cid, c in cases.items():
        ru = str(c.get("rubric") or "")
        an = str(ans.get(cid) or "")
        prompt = str(c.get("prompt") or "")
        if not ru or not an:
            continue
        runs = [r for r in cjk_runs(ru, an) if r not in prompt]
        # 再逐条剔掉「整串都能在题面里找到」的
        runs = [r for r in runs if r not in re.sub(r"[^一-鿿]+", "", prompt)]
        if runs:
            hits[cid] = runs[:4]
            total_chars += sum(len(r) for r in runs)
    return {"题数": len(cases), "命中题数": len(hits), "共有中文字符": total_chars, "逐题": hits}


def self_test() -> int:
    ok = True

    def chk(m, c):
        nonlocal ok
        ok = ok and bool(c)
        print(("  ✓ " if c else "  ✗ ") + m)

    print("── ★★★ 正向：Mendel 的真实形态（判据把答案半句连破折号一起抄了）──")
    ru = "须答那封信，并明确说「我没有说它导致了后来的实验」——两处只是同一种警觉。"
    an = "我不说那件事导致了后来的实验——两处只是同一种警觉：外观会骗人。"
    runs = [r for r in cjk_runs(ru, an) if r not in "1854 年你在做什么"]
    chk(f"抓到共有中文串：{runs[:2]}", any("两处只是同一种警觉" in r for r in runs))

    print("\n── ★★ 反向对照①：**题面里本来就有的词不算抄** ──")
    prompt = "你怎么看绕线式感应电动机的取代"
    ru2, an2 = "须谈绕线式感应电动机的取代", "绕线式感应电动机的取代是身后的事"
    runs2 = [r for r in cjk_runs(ru2, an2)
             if r not in re.sub(r"[^一-鿿]+", "", prompt)]
    chk(f"题面里的词被剔掉，剩 {runs2}", not runs2)

    print("\n── ★★ 反向对照②：判据只写要求、不写答案措辞 → 不许报 ──")
    ru3 = "须说明自己此刻拿不出该篇内容，且不补构造。"
    an3 = "那一份我说不出来。能说的是我那些年关心什么。"
    chk(f"没报：{cjk_runs(ru3, an3)}", not cjk_runs(ru3, an3))

    print("\n── ★ 反向对照③：短于门槛的共有串不算（否则「须答」两字就报） ──")
    chk("两字不报", not cjk_runs("须答甲乙", "须答甲乙"[:4], minlen=6))

    print("\n" + ("✓ 自测全过" if ok else "✗ 自测未过"))
    return 0 if ok else 2


def main() -> int:
    if "--self-test" in sys.argv[1:]:
        return self_test()
    root = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(".")
    rows = []
    for f in sorted(root.rglob("evals/cases.jsonl")):
        ws = f.parent.parent
        r = run(ws)
        if r:
            rows.append((ws.name, r))
    print(f"{'工作区':30}{'题数':>6}{'中文重合题':>12}{'占比':>8}{'共有汉字':>10}")
    for name, r in rows:
        pct = r["命中题数"] / max(r["题数"], 1)
        print(f"{name:30}{r['题数']:>6}{r['命中题数']:>12}{pct:>7.0%}{r['共有中文字符']:>10}")
    print("\n── 命中最多的三个工作区，各举两条 ──")
    for name, r in sorted(rows, key=lambda x: -x[1]["命中题数"])[:3]:
        print(f"\n{name}")
        for cid, runs in list(r["逐题"].items())[:2]:
            print(f"  {cid}")
            for s in runs[:2]:
                print(f"    「{s}」")
    return 0


if __name__ == "__main__":
    sys.exit(main())
