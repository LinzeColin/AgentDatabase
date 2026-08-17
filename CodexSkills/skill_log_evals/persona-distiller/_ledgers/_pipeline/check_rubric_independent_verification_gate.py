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

    cases.jsonl **54 个工作区**（62 个文件，8 个工作区有重复副本）｜带 rubric 的题目 **1174** 道
    rubric 内部出现 source_id / src- 的：**0 / 1174**

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

## ★★★ 2026-08-17 补：第 1 条那个洞**第一次有了实测代价**

在此之前本件只能说「规则没载体」，**说不出它值多少**——没有代价的洞排不进优先级。
现在有一件，已量清、可复算：

**Pasteur #106 `lp-voice-01`** 的 rubric 与题面钉着「1881 年 12 月 10 日」。
一手原文（CR t.92, `src-4d783fdbfc30`）写的是 **`Le 10 décembre dernier`**——**相对日期**。
定年靠刊期，而刊期只印在页眉：`C. R., 1881, 1er Semestre. (T. XCII, N° 8.)`
⇒ 1881 年**上半年**刊出的通报说「上一个 12 月」，**只能是 1880-12-10**。

**那个日期错了整一年，而它同时是产物的事实、也是尺子的刻度。**
假如这条断言按第 1 条挂上 `source_id`，就必须有人打开那份源——**一打开就看见 `dernier`**。
它活过了**三轮**判分（评委没有语料，产物与题面同源），错误分布在 **5 个文件**里。
详见 `_ledgers/_Pasteur那个日期错了整一年-而错的一层是事实层不是题面-2026-08-17.md`。

## 为什么本件只报数、不改东西

修法只有一条：**把那句要求写进评委指令**。而评委指令是**按人物冻结的尺子** ——
改了它，此前所有分数就不再与新分数可比。「门、席位一概不动」这条约束仍然有效。

⇒ **本件是报告不是门**：把这个洞从「看不见」变成「可复算」，改不改由 Owner 定。

**退出码**（2026-08-17 修正，原为「永远 rc=0」）：

    0  量到了。**发现的内容永远不拦**——「没有载体」是报告，不是失败。
    4  **未量**：`--skill-root` 下没有 SKILL.md（多半指错根），或两个扫描面都空。
       ★ 原来这两种都返回 0 ⇒ 调用方会把「我没量成」读成 PASS。

★★★ 那个「指错根」不是假想：`skill_log_evals/persona-distiller/` 是**日志目录**，
不是 skill 根，**但它也有一个 `VERSION`**（写着 v0.0.0.46，真根是 v0.0.0.154）。
指过去之后 SKILL.md 不存在、模板面 0 份，而本件照旧印出
「⇒ **一处都没有。** 规则只存在于散文里」并 rc=0 ——
**一个 0 份文件的扫描面被写成了一个测量结论。**
成因是空扫描面的守卫挂在**并集**上，只要另一面非空就混过去了。
现已改成**逐面判**：只有两面都真的量过，才下「一处都没有」这个全称结论。

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
    # ── ★★★ 2026-08-17 新增：`--skill-root` 指错时不许出报告 ──────────────
    #   实跑 main()，不是重实现判断逻辑 —— 上一次我在临时脚本里重实现度量，
    #   结果两边写法不同、结论错了。[[baseline-must-be-the-same-kind-as-what-you-compare]]
    import subprocess as _sp
    import tempfile as _tf
    me = str(pathlib.Path(__file__).resolve())
    here = pathlib.Path(__file__).resolve().parents[1]          # …/_ledgers
    real_skill = here.parents[2] / "registry/codex/persona-distiller"
    real_corp = here.parent / "_corpora"
    n_case = 0

    def case(lbl, args, want_rc, want_in=None, want_not_in=None):
        nonlocal n_case
        n_case += 1
        r = _sp.run([sys.executable, me, *args], capture_output=True, text=True)
        out = r.stdout + r.stderr
        why = []
        if r.returncode != want_rc:
            why.append("rc=%d 期望 %d" % (r.returncode, want_rc))
        if want_in and want_in not in out:
            why.append("输出里没有 %r" % want_in[:30])
        if want_not_in and want_not_in in out:
            why.append("★ 输出里**不该**出现 %r" % want_not_in[:30])
        print(("  ✓ " if not why else "  ✗ ") + lbl)
        if why:
            bad.append("%s —— %s" % (lbl, "；".join(why)))

    with _tf.TemporaryDirectory() as td:
        # 负 ①：根指到没有 SKILL.md 的地方 ⇒ 必须 rc=4，且**不许**下「一处都没有」的结论
        case("★★★ 负：`--skill-root` 指到没有 SKILL.md 的目录 ⇒ rc=4，不出结论",
             ["--skill-root", str(here.parent), "--corpora", str(real_corp)],
             4, want_in="`--skill-root` 多半指错了", want_not_in="⇒ **一处都没有。**")
        # 负 ②：**有 SKILL.md 但两个扫描面都空** ⇒ rc=4（原来是 0，会被调用方读成 PASS）
        #   ★ 必须造出 SKILL.md，否则第一道守卫先触发，测不到第二道 ——
        #     第一版就是直接拿空目录测的，自测当场把我抓住了。
        td2 = pathlib.Path(td) / "fake-skill"
        td2.mkdir()
        (td2 / "SKILL.md").write_text("【自 v0.0.0.7 起的硬门】\n", encoding="utf-8")
        case("★★ 负：有 SKILL.md 但两个扫描面都空 ⇒ rc=4，不是 0",
             ["--skill-root", str(td2), "--corpora", str(td2)], 4,
             want_in="两个扫描面都是空的")
        # 负 ③：**只有一面空** ⇒ 不许下「一处都没有」这个全称结论
        case("★★★ 负：只有模板面空（实发指令面非空）⇒ 不许下「一处都没有」",
             ["--skill-root", str(td2), "--corpora", str(real_corp)], 0,
             want_in="不下「一处都没有」这个结论", want_not_in="⇒ **一处都没有。**")
    # 正 ①：真根 ⇒ rc=0 且下得了结论
    if (real_skill / "SKILL.md").is_file():
        case("★★ 正：真 skill 根 ⇒ rc=0，且印出「一处都没有」这个测量结论",
             ["--skill-root", str(real_skill), "--corpora", str(real_corp)],
             0, want_in="⇒ **一处都没有。**")
        # 正 ②：真根下版本号必须是真根那个（曾把日志目录的 VERSION 当成 skill 版本）
        case("★ 正：印出的版本来自真根的 VERSION（不是日志目录那个）",
             ["--skill-root", str(real_skill), "--corpora", str(real_corp)],
             0, want_in=(real_skill / "VERSION").read_text(encoding="utf-8").strip())
    else:
        print("  ⚠ 找不到真 skill 根 %s —— 两条正例**未跑**（不是通过）" % real_skill)

    print("自测 %d/%d" % (len(ok) + len(no) + n_case - len(bad), len(ok) + len(no) + n_case))
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

    # ★★★ 2026-08-17：`--skill-root` 指错时本件曾**一声不吭地出了一份完整报告**。
    #   把根指到 `skill_log_evals/persona-distiller/`（那是**日志目录**，不是 skill 根，
    #   但它也有一个 VERSION，写着 v0.0.0.46）——SKILL.md 不存在、模板面 0 份，
    #   而下面照旧印「⇒ **一处都没有。** 规则只存在于散文里」，rc=0。
    #   **一个 0 份文件的扫描面，被写成了一个测量结论。**
    #   成因：空扫描面的守卫挂在**并集**上（`not tmpl and not ws_files`），
    #   于是只要另一面非空，空的那一面就混过去了。
    #   ⇒ 改成**逐面判**，并显式核 SKILL.md 在不在。
    #   [[zero-hit-gates-must-prove-they-can-hit]]｜[[a-gates-scan-set-is-smaller-than-reality]]
    skill_md = skill / "SKILL.md"
    print("扫描面：")
    print("  规则原文：%s（【自 v0.0.0.7 起的硬门】第 2 条）%s"
          % (skill_md, "" if skill_md.is_file() else "  ← ✗ **不存在**"))
    print("  指令模板：%s（%d 份）%s"
          % (tmpl_dir, len(tmpl), "" if tmpl else "  ← ✗ **空扫描面**"))
    print("  实发指令：%s 下 %d 个 judge_prompts 目录、%d 份文件%s"
          % (corp, len(ws_dirs), len(ws_files), "" if ws_files else "  ← ✗ **空扫描面**"))
    if not skill_md.is_file():
        print("\n  ✗ **规则原文都不在这个根下 —— `--skill-root` 多半指错了**（本次结论不成立）")
        print("     真根是带 SKILL.md 与 references/pipeline/ 的那个"
              "（本仓：`CodexSkills/registry/codex/persona-distiller`）。")
        print("     ★ 注意 `skill_log_evals/persona-distiller/` **也有 VERSION**"
              "（写着另一个版本号），只看 VERSION 分辨不出根。")
        return 4
    if not tmpl and not ws_files:
        print("  ✗ **两个扫描面都是空的 —— 本次结论不成立**（空扫描面不算通过）")
        return 4

    nt, ht = scan(tmpl)
    nw, hw = scan(ws_files)
    ver = (skill / "VERSION")
    print("\n══ 「至少一名评委须跳出 rubric 独立核查」的载体")
    print("   指令模板：**%d / %d** 份带这条要求%s"
          % (len(ht), nt, "" if nt else "   ← ★ **这一面是空的：未量，不是「没有载体」**"))
    print("   实发指令：**%d / %d** 份带这条要求（%d 个工作区）%s"
          % (len(hw), nw, len(ws_dirs),
             "" if nw else "   ← ★ **这一面是空的：未量**"))
    for p in (ht + hw)[:10]:
        print("     ✓ %s" % p)
    if not ht and not hw:
        # ★ 只有**两面都真的量过**（各自非空）才能下「一处都没有」这个全称结论。
        if nt and nw:
            print("   ⇒ **一处都没有。** 规则只存在于描述它的散文里"
                  "（SKILL.md 与 RUNBOOK.md）。")
            print("     当前 skill 版本：%s —— 这道「硬门」自 v0.0.0.7 起**未曾有过载体**。"
                  % (ver.read_text(encoding="utf-8").strip() if ver.is_file() else "?"))
        else:
            print("   ⇒ ★ **只有 %s 面量过，另一面是空的 —— 不下「一处都没有」这个结论**。"
                  % ("实发指令" if nw else "模板"))

    # ── 同一节【硬门】的第 1 条 ────────────────────────────────────────
    # 原文：「rubric 里每一条「须命中」的事实性断言，**必须与源账本中的一手条目
    #        一一对应**，并记录其 `source_id`。对应不上的断言不得写进 rubric。」
    #
    # ★★ 这里有个**极容易被当成合规**的陷阱：数据里**确实有** `src-` 号，
    #    但它们在 `holdout_source_ids` 字段里 —— 那回答的是
    #    「**哪些源被扣住不给人物看**」，不是「这条断言由哪个一手条目支撑」。
    #    **两个不同的问题，共用一种号码。** 不分开看就会把「有 src- 号」
    #    误读成「一一对应做到了」。[[two-source-ids-is-not-two-evidences]]
    # ★★ **按工作区去重再数。** 2026-08-17：`rglob` 把同一工作区的两份
    #   `cases.jsonl` 都算了进来 —— 全库 **62 个文件只分布在 54 个工作区**，
    #   8 个工作区在 `<wip>/` 与 `evals/` 各有一份**行数完全相同**的副本。
    #   我据此报过「带 rubric 的题目 **1432** 道」，**去重后是 1174**（虚高 18%）。
    #   ★ 结论不变（rubric 内部出现 source_id 的仍是 **0**），**变的是分母**。
    #   [[counts-need-their-cutoff-stated]]｜[[two-source-ids-is-not-two-evidences]]
    _by_ws = {}
    for _f in sorted(corp.rglob("cases.jsonl")):
        _ws = str(_f.relative_to(corp)).split("/")[0]
        # 同工作区多份时取 `evals/`（那是判分产物的位置）
        if _ws not in _by_ws or _f.parent.name == "evals":
            _by_ws[_ws] = _f
    cases = sorted(_by_ws.values())
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

    # ★★★ 2026-08-17 补：这条规则第一次有了**实测代价**。
    #   在此之前本件只能说「规则没载体」，说不出它值多少 —— 而没有代价的洞
    #   在 Owner 那里排不进优先级。现在有一件，且是**已量清、可复算**的。
    print("\n══ 第 1 条那个洞的**实测代价**（2026-08-17 首次量到）")
    print("   Pasteur #106 的 `lp-voice-01`，rubric 与题面钉着「**1881 年 12 月 10 日**」。")
    print("   一手原文（CR t.92, `src-4d783fdbfc30`）写的是「Le 10 décembre **dernier**」——")
    print("   **相对日期**。定年靠刊期，而刊期只印在页眉：`C. R., 1881, 1er Semestre. (T. XCII)`")
    print("   ⇒ 1881 年上半年刊出的通报说「上一个 12 月」，**只能是 1880-12-10**。")
    print("   **那个日期错了整一年，而它同时是产物的事实、也是尺子的刻度。**")
    print("     ★ 假如这条 rubric 断言按【硬门】第 1 条挂上 `source_id`，")
    print("       就必须有人打开那份源 —— **一打开就会看见 `dernier`**。")
    print("     ★ 它活过了**三轮**判分：评委没有语料（见下），产物与题面同源，")
    print("       照错答案答的人得分、答对的人被扣。")
    print("     ★ 未流出（Pasteur 从未出货），但错误在 **5 个文件**里：")
    print("       facts.md / persona.md / work.md / evidence/claims.jsonl / evals/cases.jsonl")
    print("     详见 `_ledgers/_Pasteur那个日期错了整一年-而错的一层是事实层不是题面-2026-08-17.md`")

    print("\n   ★ 本件是**报告不是门**（永远 rc=0）：唯一的修法是改评委指令，")
    print("     而评委指令是**按人物冻结的尺子**，改了此前分数就不再可比。")
    print("   ★★ 而且要先答一个更前面的问题：**评委做得到吗？**")
    print("      本项目已实测「评委没有语料，验不了引文」——「独立联网核查」")
    print("      在现有装置里能否执行**尚未验证**。做不到就只是换一种空转，")
    print("      并会造出一道永远红不了的绿灯。**先答这个，再答要不要写。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
