#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 **72 道 TaskPack oracle** 导成一份 json，喂给各判据的 `--tasks` 插座。

## 为什么要有这份文件

2026-08-18 用这 72 条把三条头条结论翻了两条（`check_mode_ladder_reachable`：
`single_expert` 从「名册标签 53/60」变成「真任务 **0/72**」；`deep_team` 从「结构性不可达」
变成 **18/72**）。**而我当时是把它导到会话临时目录里跑的** ——
那个路径**随会话消失**，台账里的「可复算」只剩一段散文里的 python。

⇒ **本件把那一步落成可执行的、进版本控制的一条命令。**
  [[evidence-must-live-in-the-repo-not-the-terminal]]｜[[counts-need-their-cutoff-stated]]

## 样本是什么、不是什么

来源：`_pipeline/benchmarks/development-48.jsonl` + `regression-24.jsonl`
（**TaskPack 原样复制，不是我编的**；`check_benchmark_mode_accuracy.py` 每次会印两份的 sha256）。

★★★ **这 72 条不是真实用户提问，而且远比看上去薄**（2026-08-18 本件自测抓出来的）：

    development-48   48 条 ⇒ **独立题面 12 个**（每个 ×4）
    regression-24    24 条 ⇒ **独立题面 12 个**（每个 ×2）
    两份合计 72 条  ⇒ **独立题面仍是 12 个**（每个 ×6）

  ★ 也就是说 **两份题集共用同一批 12 个题面** —— `regression-24` **不是独立的第二份样本**，
    它是同一批题面的另一组变体。凡把两份当「两个样本」互相印证的说法，**都要收窄**。
  ★★ 我此前反复写「每题 3 个变体、独立题面 24 个」——**两个数都错**，是本件自测抓到的。
  `--dedup` 只导那 12 个独立题面。
  **真实提问的分布仍然没有量过** —— 引用本件的读数时要连这句一起引。

用法：

    python3 export_benchmark_tasks.py                 # 打到 stdout
    python3 export_benchmark_tasks.py -o /tmp/b72.json
    python3 export_benchmark_tasks.py --dedup         # 只导独立题面（24 条）
    python3 export_benchmark_tasks.py --self-test
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
BENCH = HERE / "benchmarks"
SETS = ("development-48", "regression-24")

#: 机械变体的尾巴：「 变体 1：要求证据可追溯…」
VARIANT = re.compile(r"\s*变体\s*\d+\s*[：:].*$", re.S)


def load(dedup: bool = False) -> tuple[list[str], list[str]]:
    """→ `(任务列表, 说明行)`。取不到就返回空列表，**由调用方判未量**。"""
    notes, tasks = [], []
    for name in SETS:
        p = BENCH / (name + ".jsonl")
        if not p.is_file():
            notes.append("★ 缺 %s —— **未量，不是空**" % p.name)
            continue
        n = 0
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                t = json.loads(line).get("task")
            except ValueError:
                continue
            if isinstance(t, str) and t.strip():
                tasks.append(t.strip())
                n += 1
        notes.append("%s：%d 条" % (p.name, n))
    if dedup:
        seen, out = set(), []
        for t in tasks:
            k = VARIANT.sub("", t).strip()
            if k in seen:
                continue
            seen.add(k)
            out.append(t)
        notes.append("★ 去掉机械变体后：**%d** 条独立题面（原 %d）" % (len(out), len(tasks)))
        tasks = out
    return tasks, notes


def self_test() -> int:
    ok = True

    def chk(name, cond):
        nonlocal ok
        ok = ok and bool(cond)
        print("  %s %s" % ("✓" if cond else "**✗**", name))

    print("自测：")
    full, notes = load()
    chk("① 两份题集都读得到（%s）" % "｜".join(notes), len(notes) == 2 and all("缺" not in n for n in notes))
    chk("② 导出 **72** 条（实得 %d）" % len(full), len(full) == 72)
    chk("③ 每条都是非空字符串", all(isinstance(t, str) and t.strip() for t in full))

    ded, notes2 = load(dedup=True)
    chk("④ ★★ 去变体后是 **12** 条（实得 %d）—— 72 条＝12 个题面 × 6 个变体" % len(ded), len(ded) == 12)
    dev, _ = load()   # 再单独核「两份共用同一批题面」
    import re as _re
    stem = lambda xs: {VARIANT.sub("", x).strip() for x in xs}
    d48 = [json.loads(l)["task"] for l in (BENCH/"development-48.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    r24 = [json.loads(l)["task"] for l in (BENCH/"regression-24.jsonl").read_text(encoding="utf-8").splitlines() if l.strip()]
    chk("④b ★★★ 两份题集**共用同一批 12 个题面**（regression-24 不是独立的第二份样本）",
        stem(d48) == stem(r24) and len(stem(d48)) == 12)
    chk("⑤ ★ 负对照：去变体只减不增", len(ded) < len(full))
    chk("⑥ ★★ 变体正则**只吃尾巴**：去掉后题面仍非空",
        all(VARIANT.sub("", t).strip() for t in full))
    # ★ 负对照：一条没有「变体」的题不该被改动
    plain = "诊断一个单一领域问题，列出假设、证据缺口、结论和改判条件。"
    chk("⑦ ★ 负对照：不含「变体」的题面**一个字都不许动**",
        VARIANT.sub("", plain) == plain)
    print("自测：%s" % ("**全过**" if ok else "**有失败**"))
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--output", default=None, metavar="文件")
    ap.add_argument("--dedup", action="store_true", help="只导独立题面（去掉机械变体）")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args(argv)
    if a.selftest:
        return self_test()

    tasks, notes = load(a.dedup)
    for n in notes:
        print("# " + n, file=sys.stderr)
    if not tasks:
        print("★ **未量，不是通过**（rc=4）—— 一条题都取不到", file=sys.stderr)
        return 4
    print("# ★★★ 这 72 条**不是真实用户提问**，而且**远比看上去薄**：", file=sys.stderr)
    print("#     72 条 = **12 个独立题面 × 6 个变体**；且 development-48 与 regression-24"
          " **共用同一批 12 个题面**", file=sys.stderr)
    print("#     ⇒ `regression-24` **不是独立的第二份样本**。引用本件的读数时要连这句一起引。",
          file=sys.stderr)
    blob = json.dumps(tasks, ensure_ascii=False, indent=0)
    if a.output:
        pathlib.Path(a.output).write_text(blob, encoding="utf-8")
        print("# 已写入 %s（%d 条）" % (a.output, len(tasks)), file=sys.stderr)
    else:
        print(blob)
    return 0


if __name__ == "__main__":
    sys.exit(main())
