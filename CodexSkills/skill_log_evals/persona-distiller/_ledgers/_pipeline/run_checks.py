#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `_pipeline/` 下每一件判据的 `--self-test` **真的跑一遍**。

为什么要有这份文件
------------------
2026-08-17 数了一遍：`_pipeline/` 有 **28 件判据，全部支持 `--self-test`**，
**却没有任何统一入口** —— 只有 RUNBOOK.md 提到它们的名字。
当天新加的 `check_example_knuth_mirror.py` 更是 **0 处提及**：
一件谁也不调的判据，等于没做完。[[a-checker-nothing-calls-is-not-a-checker]]

## 它验的是什么、不验什么

**验**：每件判据**自己的判定逻辑**还站得住（自测通常带正反对照）。
**不验**：判据跑在真语料上的结论 —— 那要各自的 `--corpora` / `--skill-root`，
参数各不相同，本件不代跑。**别把「自测全绿」读成「全库没问题」。**

★ 与两个 skill 的 `run_tests.py` 同一形状：并行、逐件计时、
  空扫描面报红（「一件都没发现」不是通过）。

用法
----
    python3 run_checks.py            # 有红就 rc=1
    python3 run_checks.py --report   # 只报告，永远 rc=0
"""
import argparse
import concurrent.futures
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent


def discover():
    """★ **按能力发现，不按文件名前缀。**

    原写法是 `HERE.glob("check_*.py")` —— 于是 2026-08-17 新建的
    `sweep_phase_gate.py`（有 `--self-test`、9 条断言）**一条也不会被跑到**，
    只因为它不叫 `check_*`。判据扫的集合比实况小，是本仓记过十二种的老病。
    [[a-gates-scan-set-is-smaller-than-reality]]

    改为：`_pipeline/*.py` 里**凡是把 `--self-test` 注册成命令行参数的**，都跑。
    判据用的是 `add_argument("--self-test"` 这个字面事实，不是文档里提没提。
    """
    named = set(HERE.glob("check_*.py"))
    capable = set()
    marker = 'add_argument("--self-test"'
    marker2 = "add_argument('--self-test'"
    for p in HERE.glob("*.py"):
        if p.name == pathlib.Path(__file__).name:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except OSError:
            continue
        if marker in src or marker2 in src:
            capable.add(p)
    extra = sorted(capable - named)
    if extra:
        print("★ 按能力多收进 %d 件（有 --self-test 但不叫 check_*）：%s"
              % (len(extra), "、".join(p.name for p in extra)))
    return sorted(named | capable)


def run_one(p):
    t = time.time()
    r = subprocess.run([sys.executable, str(p), "--self-test"],
                       capture_output=True, text=True)
    tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    return r.returncode, (tail[-1][:56] if tail else ""), time.time() - t


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="只报告，永远 rc=0")
    a = ap.parse_args()

    files = discover()
    print("扫描面：%s（**%d 件**判据的 --self-test）" % (HERE, len(files)))
    if not files:
        print("✗ **一件都没发现 —— 未检查，不是通过**")
        return 0 if a.report else 1

    t0 = time.time()
    res = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(8, len(files))) as ex:
        futs = {ex.submit(run_one, f): f for f in files}
        for fut in concurrent.futures.as_completed(futs):
            res[futs[fut]] = fut.result()

    red = []
    for f in files:
        rc, tail, secs = res[f]
        if rc != 0:
            red.append(f.name)
        print("  %s rc=%d %5.1fs  %-50s %s"
              % ("✓" if rc == 0 else "✗", rc, secs, f.name, tail))
    print("\n合计：绿 %d｜**红 %d**%s｜墙钟 %.1fs"
          % (len(files) - len(red), len(red),
             ("：" + "、".join(red)) if red else "", time.time() - t0))
    print("★ 本件只验**判据自己的逻辑**，不代跑真语料 —— "
          "**别把「自测全绿」读成「全库没问题」**。")
    return 0 if a.report else (1 if red else 0)


if __name__ == "__main__":
    sys.exit(main())
