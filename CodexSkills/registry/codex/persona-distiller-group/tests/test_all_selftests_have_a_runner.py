#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""本 skill 的 `--self-test` **一件都没人跑过** —— 本件就是那个跑的人。

为什么要有这份文件
------------------
2026-08-17 把「谁在跑自测」这个问题挨着三棵树问了一遍：

    persona-distiller/scripts/     107 件带 --self-test
                                   · check_* 的 91 件 → check_checkers.py 管着
                                   · 另外 **16 件没人跑**（已落 test_selftests_outside_check_prefix.py）
    _ledgers/_pipeline/            run_checks.py 只 glob check_*.py
                                   · 改成按能力发现后**多收进 12 件**（28 → 40）
    persona-distiller-group/       4 件带 --self-test
                                   · **一件都没人跑** ←—— 本件补的就是这块

本 skill 的 `tests/` 下 9 件测试里，**没有一处**执行过
`check_group_version_binding` / `check_roster_independence` /
`check_team_attribution` 的 `--self-test`；`scripts/run_tests.py` 也只跑
`tests/` 目录，不碰 `scripts/` 下的自测。

★ 落这件时**三件全部 rc=0**。所以它抓的不是当下的红，是
「**这三件此前谁红了都不会有人知道**」——没有主人的判据不算做完。
[[a-gates-scan-set-is-smaller-than-reality]]｜[[every-requirement-needs-an-owner]]

★★ 为什么这件事在团队 skill 上更要紧：那三件里
`check_roster_independence` 与 `check_team_attribution` 都是**负对照型**判据
（自测里放一份「克隆名册」「宣称三人实际一人」的坏样本，要求判据抓出来）。
**负对照本身不跑，等于判据的「全绿」不构成任何证据。**

射程
----
* 只管 `scripts/` 下声明了 `--self-test` 的脚本；没声明的一个字都不说。
* 空扫描面报红：一件都没扫到不算通过。
  [[zero-hit-gates-must-prove-they-can-hit]]
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"
MARKERS = ('add_argument("--self-test"', "add_argument('--self-test'")


def declares_selftest(p: pathlib.Path) -> bool:
    try:
        return any(m in p.read_text(encoding="utf-8", errors="replace") for m in MARKERS)
    except OSError:
        return False


class EverySelfTestHasARunner(unittest.TestCase):

    def test_all_declared_selftests_pass(self):
        targets = sorted(p for p in SCRIPTS.glob("*.py") if declares_selftest(p))
        print("扫描面：%s 下声明了 --self-test 的脚本｜**实跑 %d 件**"
              % (SCRIPTS.name, len(targets)))
        self.assertGreaterEqual(
            len(targets), 3,
            "只扫到 %d 件 —— 扫描面太小，本次不构成通过（2026-08-17 实测 4 件）"
            % len(targets))

        bad = []
        for p in targets:
            try:
                r = subprocess.run([sys.executable, str(p), "--self-test"],
                                   capture_output=True, text=True, timeout=300)
                rc, out = r.returncode, (r.stdout + r.stderr)
            except subprocess.TimeoutExpired:
                rc, out = "超时", ""
            if rc != 0:
                tail = [l.strip() for l in out.strip().splitlines() if l.strip()]
                # ★ 报别人失败必须附上别人的 stderr
                bad.append((p.name, rc, (tail[-1][:120] if tail else "（无输出）")))
        for n, rc, t in bad:
            print("  ✗ %-36s rc=%s  %s" % (n, rc, t))
        self.assertEqual(bad, [],
                         "有脚本声明了 --self-test 却跑不过：%s"
                         % [n for n, _, _ in bad])

    def test_the_three_negative_control_checkers_are_covered(self):
        """反面：三件**负对照型**判据必须真的在扫描面里，不许被改名溜走。

        它们的自测放的是坏样本（克隆名册／宣称三人实际一人），
        **负对照不跑，判据的全绿就不构成证据**。
        """
        must = {"check_group_version_binding.py",
                "check_roster_independence.py",
                "check_team_attribution.py"}
        found = {p.name for p in SCRIPTS.glob("*.py") if declares_selftest(p)}
        missing = must - found
        self.assertEqual(missing, set(),
                         "这几件不在扫描面里了（改名？删了？丢了 --self-test？）：%s"
                         % sorted(missing))


if __name__ == "__main__":
    unittest.main(verbosity=0)
