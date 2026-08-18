#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""合同那句「人工关键词不得成为冠军路由的主要证据」的**执行点** —— 判据的调用方。

判据本体：`scripts/check_keyword_table_is_not_the_main_driver.py`。
`test_all_selftests_have_a_runner.py` 只跑它的 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.31）

`references/moe-routing-contract.md` A 层写着这条规则，**此前没有任何执行点** ——
写在文档里就等于没有。实测：**8/12 条任务上冠军驱动就是 `domain_match`**，
而它的任务那一侧来自 `DOMAIN_SIGNALS`（手工维护的关键词表）。
[[a-rule-in-a-doc-has-no-enforcer]]

★ 本件**不要求它变绿** —— 变绿要改词表或权重，那会移动每一道真实任务选出的人，
  属「门、席位一概不动」，要 Owner 定（Task #123 ③）。
  本件钉的是「**不许比现在更依赖那张词表**」，外加钉住合同那句话本身还在。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_keyword_table_is_not_the_main_driver.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class KeywordTableIsNotTheMainDriver(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_contract_line_still_exists(self):
        """★★ 合同那句话被删掉，判据就无的放矢 —— 单独钉住它。"""
        text = (ROOT / "references" / "moe-routing-contract.md").read_text(encoding="utf-8")
        self.assertIn("人工关键词不得成为冠军路由的主要证据", text)

    def test_not_more_keyword_dependent_than_baseline(self):
        """rc=1 更依赖词表了；**rc=4 是未量，同样不算通过**。

        ★ **不许传 `--limit`** —— 基线 0.67 是在默认样本量上测的，
          换了样本量它就不适用（我第一版传了 `--limit 8`，8 条上是 6/8=75%，误报回归）。
        """
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未量不是通过** —— 非退化守卫没过或取不到样本：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_reports_the_top_driver_rate(self):
        """★ 空扫描面报红：没印出「当第一驱动」的占比就不算跑过。"""
        r = _run()
        self.assertIn("当第一驱动", r.stdout)
        self.assertIn("份额", r.stdout)

    def test_floor_can_actually_fire(self):
        """★★★ **一道永远红不了的门不是门** —— 把地板压低，它必须判红。"""
        r = _run("--baseline-top-rate", "0.01")
        self.assertEqual(r.returncode, 1,
                         "地板压到 1% 都不判红 ⇒ 这道门够不到，等于没有：\n" + r.stdout)

    def test_changing_the_sample_without_a_new_floor_is_unmeasured(self):
        """★★★ 基线只对它自己那份样本成立 —— 换了样本量却不给新地板，必须判 **rc=4 未量**。"""
        r = _run("--limit", "8")
        self.assertEqual(r.returncode, 4,
                         "换了样本量还照旧判，等于拿不适用的地板判人：\n" + r.stdout)
        self.assertIn("未量", r.stdout)

    def test_baseline_is_reachable_not_pinned_at_one(self):
        """★★ 地板设成 1.00 会让它永远红不了；设成 0 会让它永远绿。两头都不许。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_keyword_table_is_not_the_main_driver import (
            BASELINE_LIMIT, BASELINE_TOP_RATE, MIN_CANDIDATES, MIN_NONZERO_SIGMA)
        self.assertGreater(BASELINE_LIMIT, 0, "基线必须记着它自己的样本量")
        self.assertGreater(BASELINE_TOP_RATE, 0.0)
        self.assertLess(BASELINE_TOP_RATE, 1.0, "地板 1.00 ⇒ 永远红不了")
        self.assertGreaterEqual(MIN_NONZERO_SIGMA, 2)
        self.assertGreaterEqual(MIN_CANDIDATES, 10)


if __name__ == "__main__":
    unittest.main(verbosity=2)
