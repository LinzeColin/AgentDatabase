#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `tests/` 下的每一件**真的跑一遍**。默认就是门（本 skill 目前全绿）。

为什么要有这份文件
------------------
2026-08-17 在上游 `persona-distiller` 发现：`tests/` 下 14 件测试**没有任何 runner**，
于是 `test_group_contract.py` 对着**四个从未存在过的键**红了很久而无人发现。
按「先数出口个数」回头查本 skill —— **同一个缺口，而且是我自己造的**：
本目录 6 件测试里 **4 件是 2026-08-17 当天我写的**
（disclosures-reach-the-contract／domain-classifier-language／
restricted-is-measured-only／telemetry-roundtrip），
**写了测试却没给它一个会被调用的入口**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 与上游那个 runner 的区别：**这边默认就是门**

上游有 1 件待 Owner 裁定的红，所以那边默认只报告。
本 skill 6 件**当前全绿**，没有「用未决问题卡流程」的风险 ⇒ **默认 rc≠0 即失败**。
`--report` 可退回只报告。

★ 顺带一条本 skill 特有的：`tests/run_functional_acceptance.py` 不叫 `test_*`，
  只按 `test_*.py` 找会**漏掉它**（它恰恰是最重要的那件）。
  **列文件时别只认一种命名。**

用法
----
    python3 scripts/run_tests.py            # 当门用：有红就 rc=1
    python3 scripts/run_tests.py --report   # 只报告，永远 rc=0
    python3 scripts/run_tests.py --self-test
"""
import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TESTS = HERE.parent / "tests"


def discover():
    """★ `test_*.py` **加** `run_*.py` —— 本目录最重要的那件叫 run_functional_acceptance.py。"""
    if not TESTS.is_dir():
        return []
    seen = {}
    for pat in ("test_*.py", "run_*.py"):
        for p in TESTS.glob(pat):
            seen[p.name] = p
    return [seen[k] for k in sorted(seen)]


def selftest() -> int:
    bad = []
    files = discover()
    if not files:
        print("  ✗ tests/ 下一件都没发现 —— **未检查，不是通过**")
        return 1
    names = {f.name for f in files}
    if "run_functional_acceptance.py" not in names:
        bad.append("★ 漏掉了 run_functional_acceptance.py —— **只认 test_* 就会漏它**")
    if len(files) < 3:
        bad.append("只发现 %d 件，少得可疑" % len(files))
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d（发现 %d 件：%s）"
          % (2 - len(bad), 2, len(files), "、".join(sorted(names))))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--report", action="store_true", help="只报告，永远 rc=0")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    files = discover()
    print("扫描面：%s（**%d 件**，`test_*.py` ＋ `run_*.py`）" % (TESTS, len(files)))
    if not files:
        print("✗ 一件都没发现 —— **未检查，不是通过**")
        return 0 if a.report else 1

    red = []
    for f in files:
        r = subprocess.run([sys.executable, str(f)], capture_output=True, text=True)
        tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
        print("  %s rc=%d  %-42s %s"
              % ("✓" if r.returncode == 0 else "✗", r.returncode, f.name,
                 (tail[-1][:52] if tail else "")))
        if r.returncode != 0:
            red.append(f.name)

    print("\n合计：绿 %d｜**红 %d**%s"
          % (len(files) - len(red), len(red), ("：" + "、".join(red)) if red else ""))
    return 0 if a.report else (1 if red else 0)


if __name__ == "__main__":
    sys.exit(main())
