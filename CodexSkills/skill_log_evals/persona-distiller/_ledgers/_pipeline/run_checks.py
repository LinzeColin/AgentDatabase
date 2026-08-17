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

    ★★★ 2026-08-17 第二次扩射程：**上一次只扩了「文件名前缀」，没扩「文件类型」。**
      `_pipeline/` 下还有三个 `.sh`，其中 `verify_handover_bundle.sh` 有 12 条自测
      **却一个调用方都没有** —— 它随移交包发给接手方，而那道「站在交付目录里
      `git bundle verify` 会假红」的缺陷活了三天，正因为没人自动跑它。
      判据的形状 ＝ 我上一次探查的形状。[[one-requirement-two-consumers]]
      [[a-checker-nothing-calls-is-not-a-checker]]｜[[a-gates-scan-set-is-smaller-than-reality]]
      shell 侧的字面事实是 `--self-test)` 这个 case 分支。
    """
    named = set(HERE.glob("check_*.py"))
    capable = set()
    # ★★★ 第三次扩射程（同一天）：**字面标记只是「有没有自测」的代理物。**
    #   只认 `add_argument("--self-test"` 时，另有 **4 件**真有自测却被漏掉——
    #   `assign_lanes.py` 拼的是 `--selftest`（无连字符），
    #   `gen_cases_{brandeis,churchill,dewey}.py` 直接查 `sys.argv` 不走 argparse。
    #   （这 4 件是**用绝对路径真跑一遍**测出来的，不是猜的。）
    #   [[bibliographic-proxy-instead-of-the-measurement]]｜[[one-requirement-two-consumers]]
    PY_MARKERS = ('add_argument("--self-test"', "add_argument('--self-test'",
                  'add_argument("--selftest"', "add_argument('--selftest'",
                  '"--self-test" in sys.argv', "'--self-test' in sys.argv",
                  '"--selftest" in sys.argv', "'--selftest' in sys.argv")
    SH_MARKERS = ("--self-test)", '--self-test")')
    for p in list(HERE.glob("*.py")) + list(HERE.glob("*.sh")):
        if p.name == pathlib.Path(__file__).name:
            continue
        try:
            src = p.read_text(encoding="utf-8")
        except OSError:
            continue
        marks = PY_MARKERS if p.suffix == ".py" else SH_MARKERS
        if any(m in src for m in marks):
            capable.add(p)
    extra = sorted(capable - named)
    if extra:
        print("★ 按能力多收进 %d 件（有 --self-test 但不叫 check_*）：%s"
              % (len(extra), "、".join(p.name for p in extra)))
    # ★ 印出**没被收进来**的，否则「射程够不够」这件事永远没人看得见。
    skipped = sorted(p.name for p in list(HERE.glob("*.py")) + list(HERE.glob("*.sh"))
                     if p not in capable and p not in named
                     and p.name != pathlib.Path(__file__).name)
    if skipped:
        print("   （没有 --self-test、因而不跑的 %d 件：%s）"
              % (len(skipped), "、".join(skipped[:6]) + ("…" if len(skipped) > 6 else "")))
    return sorted(named | capable)


def run_one(p):
    t = time.time()
    # ★ 解释器按后缀选。写死 sys.executable 会让 .sh 一律以 SyntaxError 收场，
    #   而那读起来像「判据坏了」，不像「我用错了解释器」。
    argv = ([sys.executable, str(p)] if p.suffix == ".py" else ["bash", str(p)])
    # ★ 参数拼法也按文件选：`assign_lanes.py` 只认 `--selftest`（无连字符）。
    #   写死一种拼法 ⇒ 它会以 argparse 报错收场，读起来像「判据红了」。
    try:
        _src = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        _src = ""
    flag = ("--selftest" if ("--selftest" in _src and "--self-test" not in _src)
            else "--self-test")
    r = subprocess.run(argv + [flag],
                       # ★★ cwd 固定到仓根：判据的判定不许取决于调用者站在哪。
                       #   （verify_handover_bundle.sh 的那个假红就是 cwd 造成的。）
                       cwd=str(HERE.parents[4]),
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
