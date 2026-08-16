#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `tests/` 下的每一件**真的跑一遍**。默认就是门（本 skill 目前全绿）。

为什么要有这份文件
------------------
2026-08-17 在上游 `persona-distiller` 发现 `test_group_contract.py` 对着**四个从未
存在过的键**红了很久。
★★ **订正**：我当时写「没有任何 runner」是错的 —— 上游 `self_check.py` **本来就跑整套**
（`unittest discover`，失败即 rc=1）。**它不是没人跑，是跑了没人修**，而且 `self_check`
只给一个**聚合**的 pass/fail，说不出哪一件红、红了多久、是新回归还是待裁定。
按「先数出口个数」回头查本 skill —— **同一个缺口，而且是我自己造的**：
本目录 6 件测试里 **4 件是 2026-08-17 当天我写的**
（disclosures-reach-the-contract／domain-classifier-language／
restricted-is-measured-only／telemetry-roundtrip），
**写了测试却没给它一个逐件可见的入口**（上游 `self_check` 那种聚合 pass/fail
在本 skill 这边**根本没有对应物** —— 团队 skill 没有 self_check）。
★ 措辞要准：上游是「跑了没人修」，本 skill 是「**真的没有入口**」——
**两处的缺口不同，别用同一句话概括。**

## 这套测试到底有多大力气——2026-08-17 变异实测

「8 件全绿」本身不说明任何事。**把核心函数逐个打坏，看有没有人喊**：

| 打坏的东西 | 察觉 |
|---|---|
| `compile_task_graph._signal_hits` 恒 False（任务信号全丢） | **5/8** |
| `build_team_dossier` 输出空档案 | 3/8 |
| `score_team_delta` 的 win_rate 恒 50 | 2/8 |
| `build_execution_contract` 丢掉 `separation_protocol` | 1/8 |
| `route_team_moe` 的打分恒 0.5（排序坍成常数） | 1/8 |

★★ 最后一行是这次的起点：**当时是 0/7 —— 七件测试无一察觉**。
整套测试查的是披露、合同、拒答、遥测往返，没有一件在看「排序还成不成立」，
而路由正是 Owner 评分里点名的那一项。已补 `test_routing_actually_discriminates.py`。

⇒ 现状：**五项破坏各有至少一件测试察觉，核心函数打不成哑的**。
★ 这张表是**实测**不是估计；重做的方法就是逐个插一行再跑本 runner。

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
