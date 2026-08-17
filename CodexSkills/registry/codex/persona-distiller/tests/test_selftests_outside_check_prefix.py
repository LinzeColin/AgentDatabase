#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`scripts/` 里**不叫 `check_*` 却带 `--self-test`** 的脚本，也得真跑一遍。

为什么要有这份文件
------------------
`check_checkers.py` 是判据的看门人，但它的扫描面是 `directory.glob("check_*.py")`
（第 125／265／426 行三处）。于是 2026-08-17 数出来：

    scripts/ 里带 `--self-test` 的共 **107** 件
      · 叫 check_* 的 **91** 件 —— `check_checkers.py` 管着
      · **不叫 check_* 的 16 件 —— 没有任何东西跑它们的自测**

`tests/test_skill_contract.py` 只按名字点了 4 件（contract_drift／ocr_homoglyphs／
baseline_provenance／distillation_freshness），其余靠运气。

同一天在 `_ledgers/_pipeline/run_checks.py` 上撞到完全同型的一处：
它也只 glob `check_*.py`，**按能力重扫当场多收进 12 件**（28 → 40）。
两处都是「**判据扫的集合比实况小**」，而这一族本仓已记过十二种机制。
[[a-gates-scan-set-is-smaller-than-reality]]｜[[every-requirement-needs-an-owner]]

★ 落这件的时候 16 件**全部 rc=0** —— 也就是说它抓的不是当下的红，
  是「**这 16 件此前谁红了都不会有人知道**」。

射程（写清楚，免得被当成更大的保证）
------------------------------------
* 本件**只**管 `scripts/` 下**不以 `check_` 开头**的 `*.py`；
  `check_*` 那 91 件归 `check_checkers.py`，不在这里重复跑。
* 判据是「**声明了 `--self-test` 就必须 rc=0**」，不是「必须有自测」——
  没声明的脚本本件一个字都不说。
* 空扫描面不算通过：一件都没扫到就报红。
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
        src = p.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    return any(m in src for m in MARKERS)


class SelfTestsOutsideCheckPrefix(unittest.TestCase):

    def test_every_declared_selftest_passes(self):
        targets = sorted(p for p in SCRIPTS.glob("*.py")
                         if not p.name.startswith("check_") and declares_selftest(p))
        # ★ 印出扫描面本身 —— 「跑了 0 件」的全绿正是本件要抓的病
        print("扫描面：scripts/ 下**不叫 check_\\* 且声明了 --self-test** 的脚本"
              "｜**实跑 %d 件**" % len(targets))
        self.assertGreaterEqual(
            len(targets), 10,
            "只扫到 %d 件 —— 扫描面太小，本次不构成通过（2026-08-17 实测 16 件）"
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
                #   [[code-that-only-ever-ran-with-n-equals-one]]
                bad.append((p.name, rc, (tail[-1][:120] if tail else "（无输出）")))
        for n, rc, t in bad:
            print("  ✗ %-34s rc=%s  %s" % (n, rc, t))
        self.assertEqual(bad, [],
                         "有脚本声明了 --self-test 却跑不过：%s"
                         % [n for n, _, _ in bad])

    def test_scan_surface_is_disjoint_from_check_checkers(self):
        """反面：本件的扫描面**不许**与 `check_checkers.py` 的重叠。

        重叠了就是把同一批人跑两遍 —— 既慢，又会让「本件全绿」
        被读成对 `check_*` 也有保证。
        """
        mine = {p.name for p in SCRIPTS.glob("*.py")
                if not p.name.startswith("check_") and declares_selftest(p)}
        theirs = {p.name for p in SCRIPTS.glob("check_*.py")}
        self.assertEqual(mine & theirs, set(),
                         "两个扫描面重叠了：%s" % sorted(mine & theirs))
        # 并集必须覆盖「所有声明了自测的脚本」，否则还有第三块没人管
        declared = {p.name for p in SCRIPTS.glob("*.py") if declares_selftest(p)}
        uncovered = declared - mine - theirs
        self.assertEqual(uncovered, set(),
                         "既不归本件也不归 check_checkers 的：%s" % sorted(uncovered))


if __name__ == "__main__":
    unittest.main(verbosity=0)
