#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`check_c_layer_is_reachable_for_a_working_product.py` 的**调用方**。

`test_all_selftests_have_a_runner.py` 只跑 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.44）

C 层（自优化）启用要 `sample_count≥60` 且 `ECE≤0.12` 且 `coverage≥0.75`。
而 `record_team_outcome` 存进遥测的 `predicted_success` 是
**队伍 `marginal_score` 均值** —— 一个**排序分，不是概率**。

    72 道 oracle 的 12 个题面 ⇒ predicted 0.1559–0.2552 ⇒ 窗口 0.04–0.38
    名册标签 12 条（默认样本）⇒ predicted 0.2155–0.5160 ⇒ 窗口 **0.10–0.64**

取对产品**最有利**的那份来说：真实成功率 70%/80%/90% ⇒ ECE 0.1840/0.2840/0.3840
⇒ 三档**全部 False**。**自优化层被绑在「产品表现得差」这个条件上。**

★ 整条回路**实跑过**（临时遥测文件，默认路径一字节未碰）：
  60 条 + actual 匹配排序分 ⇒ ECE 0.0000 ⇒ strategy **C**；
  60 条 + actual 0.85 ⇒ ECE 0.6091 ⇒ strategy **B**。
  **机制是通的，坏的是预测量选错了对象。**

★★ 本件**不改任何门**（改 `predicted_success` 或 ECE 阈值会改变每次路由的策略层 ⇒ Task #137），
  只钉「窗口上沿不许再往下掉」＋ 钉住那两处源码事实还在。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_c_layer_is_reachable_for_a_working_product.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class CLayerIsReachableForAWorkingProduct(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_window_did_not_narrow(self):
        r = _run()
        self.assertNotEqual(r.returncode, 4, "**未量不是通过**（正对照没过）：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_prints_the_window_and_the_working_rates(self):
        """★ 空扫描面报红：窗口区间和三档「能用的产品」都必须印出来。"""
        r = _run()
        self.assertIn("真实成功率必须落在", r.stdout)
        for pct in ("70%", "80%", "90%"):
            self.assertIn(pct, r.stdout)

    def test_floor_can_actually_fire(self):
        """★★★ 一道永远红不了的门不是门。"""
        r = _run("--baseline-window-hi", "0.99")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_the_two_source_facts_it_rests_on(self):
        """★★ 本件的全部前提是这两处源码事实 —— 任一被改，结论要重写。"""
        route = (ROOT / "scripts" / "route_team_moe.py").read_text(encoding="utf-8")
        writer = (ROOT / "scripts" / "record_team_outcome.py").read_text(encoding="utf-8")
        self.assertIn("<= 0.12", route, "ECE 阈值变了 ⇒ 窗口要重算")
        self.assertIn('row.get("marginal_score", row.get("base_score"', writer,
                      "预测量不再取自排序分 ⇒ 本件的结论可能已不成立，去重测")

    def test_it_never_writes_the_default_telemetry(self):
        """★★★ 本件会造遥测 —— **必须只写临时文件**。默认路径被写脏会污染所有后续路由。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        import route_team_moe as R
        default = R.default_telemetry_path(R.default_registry_root())
        before = default.exists()
        _run()
        self.assertEqual(default.exists(), before,
                         "判据跑完之后默认遥测文件的存在性变了 ⇒ 它写了不该写的地方")
        src = CHECKER.read_text(encoding="utf-8")
        self.assertIn("tempfile", src, "它应当只在临时目录里造遥测")


if __name__ == "__main__":
    unittest.main(verbosity=2)
