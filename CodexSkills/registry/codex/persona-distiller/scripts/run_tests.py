#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""把 `tests/` 下的 15 件测试**真的跑一遍**，并把已知未决与新回归分开。

为什么要有这份文件
------------------
2026-08-17 手工把 `tests/test_*.py` 逐个跑了一遍，发现
`test_group_contract.py` **一直红着**（`failures=1, errors=2`），
而且红在**四个产品从未有过的键**上（`inferred_identity` 在 git 全历史里 0 处）。

追为什么没人发现：**这个目录没有 runner。**
`scripts/` 下没有任何「跑全部测试」的入口，
全仓提到 `tests/` 的文件全部属于不相干的 MemoryAtlas workflow。
⇒ 15 件测试写了、能跑、会红，**而没有任何东西会去跑它们**。
[[a-checker-nothing-calls-is-not-a-checker]] 的又一种形状。

## 为什么默认**不是门**

今天还剩 **2 条真失败**（路由没选中测试点名的人物），
它们是**待 Owner 裁定的契约分歧**，不是可以随手修好的 bug。
把 runner 直接接成硬门，等于**用一个未决问题卡住整条流程** ——
本项目明令「不许因为过不了门而卡住流程」。

⇒ 三档，由调用方选：

    （默认）           只报告，**永远 rc=0**
    --strict          任何一件红 → rc=1
    --strict --allow-known
                      **只有「不在已知名单里的」红才 rc=1** ← 推荐当门用

第三档是唯一既能挡住**新回归**、又不会被两条未决问题卡住的用法。
★ 已知名单写死在本文件里并**逐条附理由**；名单里的项一旦变绿，
本件会**主动报出来**（「已知失败已修复，请把它从名单里删掉」）——
**名单只许缩，不许悄悄长**。

用法
----
    python3 scripts/run_tests.py                     # 报告
    python3 scripts/run_tests.py --strict --allow-known   # 当门用
    python3 scripts/run_tests.py --self-test
"""
import argparse
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TESTS = HERE.parent / "tests"

# ★ 已知未决：**每条都要写清「为什么还红着」与「谁能让它变绿」**。
#   没有理由的条目不许进这个名单 —— 那就成了「把红灯关掉」。
KNOWN = {
    "test_group_contract.py": (
        "2 条真失败（errors 已于 2026-08-17 清零）：软件题期望入选 Simon Willison、"
        "运营题期望入选 Anne Mulcahy／路易斯·郭士纳，而路由未选中。"
        "**五人全部在册**（逐个核过 team-index.json）⇒ 不是人物不存在，是路由没选中。"
        "改期望值＝把测试改成产品现在的样子，属「模式判定/路由该不该改」，**待 Owner 裁定**。"
    ),
}


def discover():
    return sorted(TESTS.glob("test_*.py")) if TESTS.is_dir() else []


def run_one(path):
    r = subprocess.run([sys.executable, str(path)], capture_output=True, text=True)
    tail = [l for l in (r.stdout + r.stderr).strip().splitlines() if l.strip()]
    return r.returncode, (tail[-1][:60] if tail else "")


def selftest() -> int:
    bad = []
    files = discover()
    if not files:
        # ★ 空扫描面不算通过
        print("  ✗ tests/ 下一件 test_*.py 都没有 —— **未检查，不是通过**")
        return 1
    if len(files) < 5:
        bad.append("只发现 %d 件测试，少得可疑（应为十几件）" % len(files))
    # ★ 已知名单里的文件必须真实存在，否则名单会悄悄长草
    for name in KNOWN:
        if not (TESTS / name).is_file():
            bad.append("已知名单里的 %s 不存在 —— **名单陈旧**" % name)
    # ★ 每条已知项都要有理由
    for name, why in KNOWN.items():
        if not why or len(why) < 20:
            bad.append("%s 没有写清为什么还红着" % name)
    for b in bad:
        print("  ✗ " + b)
    print("自测 %d/%d（发现 %d 件测试）" % (3 - len(bad), 3, len(files)))
    return 1 if bad else 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--strict", action="store_true", help="有红就 rc=1")
    ap.add_argument("--allow-known", action="store_true",
                    help="配 --strict：只有**不在已知名单里**的红才 rc=1")
    ap.add_argument("--self-test", "--selftest", dest="selftest", action="store_true")
    a = ap.parse_args()
    if a.selftest:
        return selftest()

    files = discover()
    print("扫描面：%s（**%d 件**）" % (TESTS, len(files)))
    if not files:
        print("✗ 一件都没发现 —— **未检查，不是通过**")
        return 0

    red, green, fixed = [], [], []
    for f in files:
        rc, tail = run_one(f)
        mark = "✓" if rc == 0 else "✗"
        known = f.name in KNOWN
        note = ""
        if rc != 0 and known:
            note = "  ← **已知未决**"
        elif rc != 0:
            note = "  ← **新回归**"
            red.append(f.name)
        elif known:
            note = "  ← **已知失败已修复：请把它从 KNOWN 里删掉**"
            fixed.append(f.name)
        if rc == 0:
            green.append(f.name)
        print("  %s rc=%d  %-38s %-46s%s" % (mark, rc, f.name, tail, note))

    print("\n合计：绿 %d｜红 %d（其中已知未决 %d、**新回归 %d**）"
          % (len(green), len(files) - len(green),
             len(files) - len(green) - len(red), len(red)))
    if KNOWN:
        print("\n已知未决（每条都写明谁能让它变绿）：")
        for n, why in KNOWN.items():
            print("  · %s\n      %s" % (n, why))
    if fixed:
        print("\n★★ **下列已知项已经变绿，名单该缩了**：%s" % "、".join(fixed))
    if red:
        print("\n✗ **新回归 %d 件**：%s" % (len(red), "、".join(red)))

    if a.strict:
        return 1 if (red or (not a.allow_known and len(green) != len(files))) else 0
    return 0          # 默认只报告，永远 rc=0


if __name__ == "__main__":
    sys.exit(main())
