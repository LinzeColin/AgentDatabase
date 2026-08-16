#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""任务包自带的 48+24 道基准题，**真的跑一遍**，看模式判对没有。

为什么要有这份文件
------------------
TaskPack `V0.0.0.1` 里带了两个基准集，每一行都有 **`expected_mode`** 这个 oracle：

    benchmarks/tasks/development-48.jsonl   48 条
    benchmarks/tasks/regression-24.jsonl    24 条

而任务包自己的验收 `tools/run_taskpack_acceptance.py` 对它们只做两件事：

    required = [..., "benchmarks/tasks/development-48.jsonl", ...]   # 检查**文件存在**
    if development_count != 48 or regression_count != 24:            # 检查**行数**
        failures.append("benchmark task counts differ from 48/24 contract")

**它从来没有把任何一道题跑进路由器。** 每一行的 `expected_mode` 从未被评估过 ——
基准被「数了行数」，没有被「跑过」。
[[a-checker-nothing-calls-is-not-a-checker]]｜[[zero-hit-gates-must-prove-they-can-hit]]

而且这两个 jsonl **没有随 overlay 落进仓里**（overlay 只装 scripts/references/tests），
所以仓里也没有任何东西引用 `expected_mode`。本目录下那两份是**从任务包原样复制**的，
sha256 前 16 位：`bb554b325f85d037` / `e3340b594a18567e`。

## 首次真跑的结果（2026-08-16，路由 v0.0.0.15）

    development-48：命中 **16 / 48 = 33%**

    期望 → 实得                 条数
    single_expert → small_team   12   （要 1 人，给了 5–15）
    small_team    → deep_team     8   （超配）
    small_team    → small_team    8   ✓
    deep_team     → deep_team     8   ✓
    swarm         → small_team    8   （要 25+，给了 5–15）
    deep_team     → small_team    4   （欠配）

★ **`swarm` 一次都没被选中（0/8）。**
★ 两个方向都错：12 条超配、12 条欠配、24 条对。
★ **与词表扩容无关** —— 92 词版与 290 词版实测都是 16/48
  （这些题是通用模板，没有领域词汇，两版都落 `general-decision`）。

## 它答不了什么

1. **不判最终答案对不对**，只判模式选得对不对。
2. `expected_mode` 是**任务包作者写的**，不是我标的 —— 这正是它的价值
   （外部 oracle），但若那些标注本身有争议，本件的结论随之动摇。
3. 本件**不改任何阈值**。模式判定的公式在
   `persona-distiller-group/scripts/compile_task_graph.py` 的 `decide_mode` 一带，
   属 TaskPack 冻结项 D-005，**不动**。

用法
----
    python3 check_benchmark_mode_accuracy.py --self-test
    python3 check_benchmark_mode_accuracy.py --registry-root <group 目录>
    python3 check_benchmark_mode_accuracy.py --registry-root <...> --set regression-24
"""
import argparse
import collections
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
BENCH = HERE / "benchmarks"
MODES = ("single_expert", "small_team", "deep_team", "swarm")


def load_tasks(name):
    p = BENCH / (name + ".jsonl")
    if not p.is_file():
        raise SystemExit("✗ 找不到基准集 %s —— 它随任务包来，不在 overlay 里" % p)
    return [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l.strip()]


def route_mode(registry_root, task):
    out = subprocess.run(
        [sys.executable, str(pathlib.Path(registry_root) / "scripts" / "route_team_moe.py"),
         "--task", task, "--registry-root", str(registry_root)],
        capture_output=True, text=True)
    if out.returncode != 0:
        return None
    return json.loads(out.stdout[out.stdout.find("{"):]).get("mode")


def selftest():
    bad = []
    for name, want in (("development-48", 48), ("regression-24", 24)):
        try:
            n = len(load_tasks(name))
        except SystemExit as e:
            bad.append(str(e)); continue
        if n != want:
            bad.append("%s 应有 %d 条，实得 %d" % (name, want, n))
    # 每行都要带 oracle —— 没有 oracle 的基准题**不算基准题**
    for name in ("development-48", "regression-24"):
        try:
            rows = load_tasks(name)
        except SystemExit:
            continue
        miss = [r.get("task_id") for r in rows if r.get("expected_mode") not in MODES]
        if miss:
            bad.append("%s 有 %d 行的 expected_mode 缺失或不在四种模式内：%s"
                       % (name, len(miss), miss[:5]))
    # ★ 负对照：一个不存在的集合必须报错，不许静默返回空
    try:
        load_tasks("no-such-set")
        bad.append("★ 不存在的集合应当报错，实际静默通过")
    except SystemExit:
        pass
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d" % (5 - len(bad), 5))
    return 1 if bad else 0


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--registry-root")
    ap.add_argument("--set", dest="which", default="development-48",
                    choices=["development-48", "regression-24", "both"])
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()
    if not a.registry_root:
        ap.error("要 --registry-root（persona-distiller-group 目录），或只跑 --self-test")

    root = pathlib.Path(a.registry_root).resolve()
    sets = ["development-48", "regression-24"] if a.which == "both" else [a.which]
    for name in sets:
        rows = load_tasks(name)
        pairs = collections.Counter()
        unresolved = 0
        for r in rows:
            got = route_mode(root, r["task"])
            if got is None:
                unresolved += 1
                continue
            pairs[(r["expected_mode"], got)] += 1
        hit = sum(n for (e, g), n in pairs.items() if e == g)
        total = sum(pairs.values())
        print("\n══ %s：%d 条%s" % (name, len(rows),
              ("｜**路由跑不出来的 %d 条**" % unresolved) if unresolved else ""))
        print("   模式命中 **%d / %d = %.0f%%**" % (hit, total, 100 * hit / max(total, 1)))
        print("   %-16s %-16s %s" % ("期望", "实得", "条数"))
        for (e, g), n in pairs.most_common():
            print("   %-16s %-16s %3d %s" % (e, g, n, "✓" if e == g else ""))
        # ★ 逐模式召回：整体命中率会被条数多的模式带偏
        print("   —— 逐模式召回（**整体率会被条数多的模式带偏，必须分开看**）——")
        for m in MODES:
            want = sum(n for (e, _), n in pairs.items() if e == m)
            got = sum(n for (e, g), n in pairs.items() if e == m and g == m)
            if want:
                print("     %-16s %d/%d = %3.0f%% %s"
                      % (m, got, want, 100 * got / want, "**一次都没选中**" if got == 0 else ""))
    # 只报数，不设阈值 —— 阈值要 Owner 定；本件永远 rc=0
    return 0


if __name__ == "__main__":
    sys.exit(main())
