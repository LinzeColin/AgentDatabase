#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SKILL.md 那道【硬门】的**两条**有没有载体 —— 实测都没有。

为什么要有这份文件
------------------
`persona-distiller/SKILL.md` 从 **v0.0.0.7** 起有一整节标着
**【自 v0.0.0.7 起的硬门】rubric 本身必须被独立核查**，共两条。
2026-08-17 实测（skill 已到 **v0.0.0.154**）：**两条都没有载体。**

**第 1 条**：「rubric 里每一条『须命中』的事实性断言，必须与源账本中的一手条目
一一对应，并记录其 `source_id`。对应不上的断言不得写进 rubric。」

    cases.jsonl 62 份｜带 rubric 的题目 **1432** 道
    rubric 内部出现 source_id / src- 的：**0 / 1432**

★★ 这一条有个**极容易被当成合规**的陷阱：数据里**确实有** `src-` 号，
但它们在 `holdout_source_ids`（1151 道有此字段、200 道非空）——
那回答的是「**哪些源被扣住不给人物看**」，**不是**「这条断言由哪个一手条目支撑」。
**两个不同的问题共用一种号码。**

**第 2 条**：「至少一名评委必须被显式要求『跳出 rubric 独立联网核查其中的事实前提』」

    评委指令模板（references/pipeline/judge_prompts/）  4 份 → 命中 **0**
    各工作区实际发出的评委指令                        30 份 → 命中 **0**
    有 judge_prompts 目录的工作区                    10 个 → 命中 **0**

**那句话在全仓只出现在三处：SKILL.md 和两份 RUNBOOK.md** ——
**全是描述规则的散文，没有一处是执行它的产物。**

⇒ 一整节被称作「硬门」的规则，**147 个版本以来两条都没有任何载体**。
[[a-rule-in-a-doc-has-no-enforcer]]｜[[a-penalty-is-not-a-rule]]｜
[[every-requirement-needs-an-owner]]

## 为什么本件只报数、不改东西

修法只有一条：**把那句要求写进评委指令**。而评委指令是**按人物冻结的尺子** ——
改了它，此前所有分数就不再与新分数可比。「门、席位一概不动」这条约束仍然有效。

⇒ **本件是报告不是门**：把这个洞从「看不见」变成「可复算」，
改不改由 Owner 定。永远 rc=0。

## 还有一件必须一起说的：这条规则可能**本来就执行不了**

本项目已实测记录：**评委没有语料，验不了引文**
（[[judges-cannot-verify-quotes]]）。「独立联网核查」在现有装置里能不能做到，
是个**未验证的前提**。所以 Owner 面对的其实是两个问题，不是一个：

1. 要不要把这句要求写进（今后的）评委指令？
2. 写进去之后，评委**做得到吗**？做不到就只是换一种形式的空转。

**先答第 2 个再答第 1 个** —— 否则会造出一道「永远红不了的绿灯」。
[[a-red-that-can-never-turn-green-is-not-a-signal]]

用法
----
    python3 check_rubric_independent_verification_gate.py --self-test
    python3 check_rubric_independent_verification_gate.py --skill-root <persona-distiller> \\
        --corpora <_corpora>
"""
import argparse
import collections
import json
import pathlib
import re
import sys

# 「跳出 rubric 独立核查」这条要求的各种可能写法。
# ★ 宁可宽 —— 判据要证明的是「一处都没有」，放宽只会让这个结论**更难**成立，
#   而不是更容易。放松只许放在开脱侧。[[loosen-only-the-exonerating-side]]
WANT = re.compile(
    r"跳出\s*rubric|独立(联网)?核查|独立核实|自行核查|"
    r"independently\s+verif|verify\s+the\s+rubric|question\s+the\s+rubric|"
    r"outside\s+the\s+rubric|challenge\s+the\s+rubric",
    re.I,
)


def scan(paths):
    files, hits = 0, []
    for p in paths:
        if not p.is_file():
            continue
        files += 1
        try:
            t = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if WANT.search(t):
            hits.append(p)
    return files, hits


def selftest() -> int:
    bad = []
    ok = ["请跳出 rubric 独立联网核查其中的事实前提",
          "At least one judge must independently verify the factual premises",
          "该席位需自行核查 rubric 里的事实前提"]
    no = ["严格按 rubric 逐条打分", "Score strictly against the rubric.",
          "不得修改候选证据"]
    for s in ok:
        if not WANT.search(s):
            bad.append("应命中却没命中：%r" % s[:40])
    for s in no:
        if WANT.search(s):
            bad.append("★ 不该命中却命中了（正则太宽）：%r" % s[:40])
    print("自测 %d/%d" % (len(ok) + len(no) - len(bad), len(ok) + len(no)))
    for b in bad:
        print("  ✗ " + b)
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skill-root")
    ap.add_argument("--corpora")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not (a.skill_root and a.corpora):
        ap.error("要 --skill-root 与 --corpora，或只跑 --self-test")

    skill = pathlib.Path(a.skill_root).resolve()
    corp = pathlib.Path(a.corpora).resolve()

    tmpl_dir = skill / "references" / "pipeline" / "judge_prompts"
    tmpl = sorted(p for p in tmpl_dir.iterdir() if p.is_file()) if tmpl_dir.is_dir() else []
    ws_dirs = sorted(p for p in corp.rglob("judge_prompts") if p.is_dir())
    ws_files = [f for d in ws_dirs for f in sorted(d.iterdir()) if f.is_file()]

    print("扫描面：")
    print("  规则原文：%s/SKILL.md（【自 v0.0.0.7 起的硬门】第 2 条）" % skill)
    print("  指令模板：%s（%d 份）" % (tmpl_dir, len(tmpl)))
    print("  实发指令：%s 下 %d 个 judge_prompts 目录、%d 份文件"
          % (corp, len(ws_dirs), len(ws_files)))
    if not tmpl and not ws_files:
        print("  ✗ **两个扫描面都是空的 —— 本次结论不成立**（空扫描面不算通过）")
        return 0

    nt, ht = scan(tmpl)
    nw, hw = scan(ws_files)
    ver = (skill / "VERSION")
    print("\n══ 「至少一名评委须跳出 rubric 独立核查」的载体")
    print("   指令模板：**%d / %d** 份带这条要求" % (len(ht), nt))
    print("   实发指令：**%d / %d** 份带这条要求（%d 个工作区）" % (len(hw), nw, len(ws_dirs)))
    for p in (ht + hw)[:10]:
        print("     ✓ %s" % p)
    if not ht and not hw:
        print("   ⇒ **一处都没有。** 规则只存在于描述它的散文里"
              "（SKILL.md 与 RUNBOOK.md）。")
        print("     当前 skill 版本：%s —— 这道「硬门」自 v0.0.0.7 起**未曾有过载体**。"
              % (ver.read_text(encoding="utf-8").strip() if ver.is_file() else "?"))

    # ── 同一节【硬门】的第 1 条 ────────────────────────────────────────
    # 原文：「rubric 里每一条「须命中」的事实性断言，**必须与源账本中的一手条目
    #        一一对应**，并记录其 `source_id`。对应不上的断言不得写进 rubric。」
    #
    # ★★ 这里有个**极容易被当成合规**的陷阱：数据里**确实有** `src-` 号，
    #    但它们在 `holdout_source_ids` 字段里 —— 那回答的是
    #    「**哪些源被扣住不给人物看**」，不是「这条断言由哪个一手条目支撑」。
    #    **两个不同的问题，共用一种号码。** 不分开看就会把「有 src- 号」
    #    误读成「一一对应做到了」。[[two-source-ids-is-not-two-evidences]]
    cases = sorted(corp.rglob("cases.jsonl"))
    total = in_rubric = with_holdout = holdout_nonempty = 0
    fields = collections.Counter()
    for f in cases:
        for line in f.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                d = json.loads(line)
            except ValueError:
                continue
            if d.get("rubric") is None:
                continue
            total += 1
            fields.update(d.keys())
            blob = json.dumps(d.get("rubric"), ensure_ascii=False)
            if "source_id" in blob or "src-" in blob:
                in_rubric += 1
            if "holdout_source_ids" in d:
                with_holdout += 1
                if d["holdout_source_ids"]:
                    holdout_nonempty += 1
    print("\n══ 同一节【硬门】第 1 条：rubric 的断言有没有挂上一手条目的 source_id")
    print("   扫描面：cases.jsonl **%d** 份｜带 rubric 的题目 **%d** 道" % (len(cases), total))
    print("   rubric **内部**出现 source_id / src- 的：**%d / %d**" % (in_rubric, total))
    if total and in_rubric == 0:
        print("   ⇒ **一道都没有。** 这条要求同样没有载体。")
    print("   ★ 易被误读成合规的那个字段：`holdout_source_ids` 存在于 %d 道、非空 %d 道 ——"
          % (with_holdout, holdout_nonempty))
    print("     它回答的是「**哪些源被扣住不给人物看**」，**不是**「这条断言由哪个一手条目支撑」。")
    print("     两个不同的问题共用一种号码，**不分开看就会把它当成已合规**。")

    print("\n   ★ 本件是**报告不是门**（永远 rc=0）：唯一的修法是改评委指令，")
    print("     而评委指令是**按人物冻结的尺子**，改了此前分数就不再可比。")
    print("   ★★ 而且要先答一个更前面的问题：**评委做得到吗？**")
    print("      本项目已实测「评委没有语料，验不了引文」——「独立联网核查」")
    print("      在现有装置里能否执行**尚未验证**。做不到就只是换一种空转，")
    print("      并会造出一道永远红不了的绿灯。**先答这个，再答要不要写。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
