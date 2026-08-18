#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`marginal_select` 的多样性权重把「对口的人」换掉了多少 —— 判据的调用方。

判据本体：`scripts/check_diversity_does_not_outweigh_fit.py`。
`test_all_selftests_have_a_runner.py` 只跑它的 `--self-task`，跑不到 `main()`。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测）

`marginal_select()` 对同族惩罚极重：同族第 2 人要胜过一个**新族**候选，
`base_score` 需领先 **(0.08+0.025)/0.76 = 0.1382**。实测一道软件评审题：
Chip Huyen 领先 Joel Salatin **0.1250 < 0.1382** ⇒ **农场主第 5、Huyen 第 10**，
14 人里只有 3 个软件开发师。

**换手率**（按 base 排前 K 里没能进最终名单的人 / K）实测中位 **36%**。

★ 本件**不要求它变小** —— 「多样性该不该压过对口度」是设计取舍，要 Owner 定（#123 ⑩）。
  它钉的是「**不许比现在更严重**」，外加钉住那四个常数的形状（变了则推导作废）。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_diversity_does_not_outweigh_fit.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class DiversityDoesNotOutweighFit(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_churn_has_not_worsened(self):
        """rc=1 更严重；**rc=4 是未量，同样不算通过**。"""
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未量不是通过** —— 公式形状变了或取不到样本：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_reports_the_churn_and_the_tipping_points(self):
        """★ 空扫描面报红：没印出换手率与临界点就不算跑过。"""
        r = _run()
        self.assertIn("换手率", r.stdout)
        self.assertIn("0.1382", r.stdout, "同族第 2 人的临界点没印出来")

    def test_floor_can_actually_fire(self):
        """★★★ 一道永远红不了的门不是门 —— 压低地板它必须判红。"""
        r = _run("--baseline-churn", "0.01")
        self.assertEqual(r.returncode, 1,
                         "地板压到 1% 都不红 ⇒ 这道门够不到：\n" + r.stdout)

    def test_formula_shape_is_pinned(self):
        """★★ 那四个常数一变，本件印的所有临界点就作废 —— 必须判未量而不是照印。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_diversity_does_not_outweigh_fit import (
            BASELINE_CHURN, formula_intact, tipping_point)
        intact, bad = formula_intact()
        self.assertTrue(intact, "`marginal_select` 的公式形状变了：%s" % bad)
        self.assertAlmostEqual(tipping_point(2), 0.105 / 0.76, places=12)
        self.assertLess(tipping_point(2), tipping_point(3))
        self.assertGreater(BASELINE_CHURN, 0.0)
        self.assertLess(BASELINE_CHURN, 1.0, "地板 1.0 ⇒ 永远红不了")


if __name__ == "__main__":
    unittest.main(verbosity=2)
