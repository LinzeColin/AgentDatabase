#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**换一种语言问同一件事，不许换域** —— 而域决定的是「谁进候选池」。

## 与本目录已有两件的分工（**不是第二把尺子**）

| 文件 | 断言的是 | 形式 |
|---|---|---|
| `test_domain_classifier_language.py` | 单题 → **应得的域**（`ci` 不许在 decide 里发火…） | 绝对标准 |
| `test_generic_verbs_do_not_claim_a_domain.py` | `设计`/`design`/`仓库` 三个**具体词** | 绝对标准 |
| **本件** | 同一内容的**中英两版必须落进同一组域** | **关系** |

前两件都要求「这道题的正确答案是 X」——那要人来定，所以只能一题一题写。
本件断的是**关系**，不需要标准答案：谁对谁错都行，**但两版必须一致**。
所以它能覆盖前两件写不到的题，也不会与它们抢同一个判定。
[[i-built-a-second-ruler-while-the-authoritative-one-sat-in-scripts]]

## 为什么这件事重要到要单独一件

`domain_match` 不是排序项，是**准入项**。实测 2026-08-18（`score_candidate`，
strategy=B，accept_threshold 0.17，102 份产物）：

    英文软件题 合格 91 人 —— **83 人**靠 domain_match 进来；
                             task_similarity 只抬了 3 人、scenario 1、capability **0**
    中文同一题 合格 58 人 —— domain_match 34、packet_similarity 24

⇒ 域判错，后面所有分数都是**在错的池子里排序**。

## 首跑就是红的，所以它是**回归地板**不是门

平价 **3/6**（`诊断`→healthcare、`评审`→software-ai、英文那题一个信号都不命中）。
一道从建成起就红、要改代码才转绿的门不是信号
（[[a-red-that-can-never-turn-green-is-not-a-signal]]），
所以本件钉的是「**不许比现在更差**」，修好一对就把 `BASELINE` 抬一档。

★ 判据本体在 `scripts/check_domain_inference_language_parity.py`；
  本件是它的**调用方** —— `test_all_selftests_have_a_runner.py` 只跑它的 `--self-test`，
  跑不到 `main()`，那样平价回归了也没人喊。
  [[a-checker-nothing-calls-is-not-a-checker]]
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_domain_inference_language_parity.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class DomainInferenceIsLanguageNeutral(unittest.TestCase):

    def test_checker_exists(self):
        self.assertTrue(CHECKER.is_file(), "判据本体不在：%s" % CHECKER)

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_parity_has_not_regressed(self):
        """rc=0 平价 ≥ 基线；rc=1 变差了；**rc=4 是未量，同样不算通过**。"""
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未量不是通过** —— 非退化门没过或装不进：\n" + r.stdout)
        self.assertEqual(r.returncode, 0,
                         "换语言换域的对数变多了（回归）：\n" + r.stdout)

    def test_it_actually_reports_a_parity_number(self):
        """★ 空扫描面报红：没印出平价数就不算跑过。"""
        r = _run()
        self.assertIn("平价", r.stdout)
        self.assertIn("/6", r.stdout, r.stdout)

    def test_baseline_is_not_zero(self):
        """★★ 地板压到 0 等于把这件事关掉 —— 那样任何回归都过得去。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_domain_inference_language_parity import BASELINE, PAIRS
        self.assertGreater(BASELINE, 0, "基线 0 等于没有地板")
        self.assertLessEqual(BASELINE, len(PAIRS))
        self.assertGreaterEqual(len(PAIRS), 4, "对数太少，平价数没有分辨力")


if __name__ == "__main__":
    unittest.main(verbosity=2)
