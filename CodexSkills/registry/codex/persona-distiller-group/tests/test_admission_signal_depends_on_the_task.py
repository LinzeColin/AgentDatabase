#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""准入门那句注释的**执行点** —— `check_admission_signal_depends_on_the_task.py` 的调用方。

`test_all_selftests_have_a_runner.py` 只跑它的 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.35）

`route_team_moe.py` 写着：

    # Expert Choice: the expert declines tasks outside its demonstrated competence.
    if max(task_similarity, packet_similarity, capabilities, scenarios, domain_match) < accept_threshold:

`max(...)` ⇒ 任一项过线即可。而 `packet_similarity` 比的是候选人卡片与
`work_packets` 的 `objective`，那些 objective 是**固定套话**：五道内容毫不相干的题
（微服务重构／农场轮作／医院灭菌／供应商谈判／一串无意义词）编出来的 14 条 objective
**sha256 完全相同** ⇒ **102/102 人的读数跨题一个都不动**。

实测规模（24 条样本、策略 B、门 0.17）：过准入的人里，**其余四项全部低于门、
唯一靠这条任务无关通道过线**的 —— 均值 **62.8%**，最坏一题 **97.6%**（41/42 人）。

★ 本件**不要求它变绿**：变绿要改 `packet_similarity` 的定义或把它移出 `max(...)`，
  会移动每一道真实任务选出的人 ⇒ 属「门、席位一概不动」，要 Owner 定（Task #135）。
  本件钉的是「**不许比现在更依赖那条通道**」，外加钉住那句注释还在。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_admission_signal_depends_on_the_task.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class AdmissionSignalDependsOnTheTask(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_the_pinned_comment_still_exists(self):
        """★★ 那句注释被删掉，判据就无的放矢 —— 单独钉住它。"""
        text = (ROOT / "scripts" / "route_team_moe.py").read_text(encoding="utf-8")
        self.assertIn(
            "Expert Choice: the expert declines tasks outside its demonstrated competence.",
            text)

    def test_not_more_dependent_on_the_task_blind_lane(self):
        """rc=1 更依赖了；**rc=4 是未量，同样不算通过**。"""
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未量不是通过** —— 正对照没过或取不到样本：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_reports_both_the_mechanism_and_the_scale(self):
        """★ 空扫描面报红：机制（指纹）和规模（占比）两段都必须印出来。"""
        r = _run()
        self.assertIn("objective 指纹", r.stdout)
        self.assertIn("与任务无关", r.stdout)
        self.assertIn("唯一靠", r.stdout)

    def test_floor_can_actually_fire(self):
        """★★★ **一道永远红不了的门不是门** —— 把地板压到 1%，它必须判红。"""
        r = _run("--baseline-sole-share", "0.01")
        self.assertEqual(r.returncode, 1,
                         "地板压到 1% 都不判红 ⇒ 这道门够不到，等于没有：\n" + r.stdout)

    def test_changing_the_sample_without_a_new_floor_is_unmeasured(self):
        """★★★ 基线只对它自己那份样本成立 —— 换样本量却不给新地板，必须 rc=4。"""
        r = _run("--limit", "8")
        self.assertEqual(r.returncode, 4, r.stdout)
        self.assertIn("未量", r.stdout)

    def test_constants_are_reachable_not_pinned_at_the_ends(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_admission_signal_depends_on_the_task import (
            BASELINE_LIMIT, BASELINE_SOLE_SHARE, MIN_CANDIDATES, MIN_TASKS)
        self.assertGreater(BASELINE_SOLE_SHARE, 0.0, "地板 0 ⇒ 永远绿")
        self.assertLess(BASELINE_SOLE_SHARE, 1.0, "地板 1.00 ⇒ 永远红不了")
        self.assertGreater(BASELINE_LIMIT, 0, "基线必须记着它自己的样本量")
        self.assertGreaterEqual(MIN_CANDIDATES, 10)
        self.assertGreaterEqual(MIN_TASKS, 4)

    def test_component_keys_match_the_products_own_dict(self):
        """★★★ 我第一版把键写成 `capabilities`/`scenarios` —— 产品存的是
        `capability_match`/`scenario_match` ⇒ 那两项恒读 0.0，会**多算**占比。
        这里直接对着产品的 `values` 字典钉键名。[[the-field-was-filled-with-the-filename]]
        """
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_admission_signal_depends_on_the_task import COMPONENTS
        src = (ROOT / "scripts" / "route_team_moe.py").read_text(encoding="utf-8")
        for key in COMPONENTS:
            self.assertIn('"%s":' % key, src,
                          "`%s` 不是 route_team_moe 里 values 的键 ⇒ 会恒读 0.0" % key)


if __name__ == "__main__":
    unittest.main(verbosity=2)
