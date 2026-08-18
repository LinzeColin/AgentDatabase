#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`check_divergence_pairs_survive_extraction.py` 的**调用方**。

`test_all_selftests_have_a_runner.py` 只跑 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.37）

`divergences: []` 在下游读起来像「专家一致」，实际只意味着「**没有检出**」。
检出链条有三处会静默断掉：段落被切碎到 <40 字／`canonical_name` 写法改了／
重打的包里没有 `divergence-map.md`。**三种都会让它恒为 `[]`。**

现算基线：102 人名册 ⇒ 5151 个配对，可互相点名的 **24 个**，
**全部同族**（investor-capital-allocator 17、software-developer 7），跨族 **0**。

★ 与之相邻但**本件不判**的一件事（只在 SKILL.md 披露）：
  72 道 oracle 上路由选出的队伍含可检出对的是 **0/72**，
  而同样大小的随机队伍中位 **22/72（30.6%）**、200 次重抽里 **0 次** ≤0
  ⇒ 多样性配重（同族第 2 人要 base 领先 0.1382）与分歧检出**结构性冲突**。
  改配重会移动每一道任务选出的人 ⇒ 属「门、席位一概不动」。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_divergence_pairs_survive_extraction.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class DivergencePairsSurviveExtraction(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_pairs_did_not_drop(self):
        """rc=1 检出掉了；**rc=4 是未量，同样不算通过**。"""
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未量不是通过** —— 扫描面塌了或名册规模变了：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_reports_the_scan_surface_before_the_count(self):
        """★ 报「N 个」之前必须先报「我扫了多少」—— 否则 0 分不清「没有」和「没看见」。"""
        r = _run()
        self.assertIn("非空", r.stdout)
        self.assertIn("配对", r.stdout)
        self.assertIn("同族", r.stdout)

    def test_floor_can_actually_fire(self):
        """★★★ 一道永远红不了的门不是门 —— 把地板抬高，它必须判红。"""
        r = _run("--baseline-pairs", "999")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_extract_divergences_still_pops_its_input(self):
        """★★ 判据传的是**副本** —— 因为 `extract_divergences` 会 `pop` 掉
        `divergence_text`。这行为若变了，判据里那句注释就该跟着改。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from build_team_dossier import extract_divergences
        m = [{"subject_slug": "a", "canonical_name": "A", "divergence_text": "x" * 60},
             {"subject_slug": "b", "canonical_name": "B", "divergence_text": "y" * 60}]
        extract_divergences(m)
        self.assertNotIn("divergence_text", m[0],
                         "它不再 pop 了 ⇒ 判据可以不传副本，注释要更新")

    def test_constants_are_bound_to_their_roster(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_divergence_pairs_survive_extraction import (
            BASELINE_PAIRS, BASELINE_ROSTER, MIN_NONEMPTY_RATE)
        self.assertGreater(BASELINE_PAIRS, 0, "地板 0 ⇒ 永远绿")
        self.assertGreater(BASELINE_ROSTER, 0, "基线必须记着它自己的名册规模")
        self.assertGreater(MIN_NONEMPTY_RATE, 0.5)
        self.assertLessEqual(MIN_NONEMPTY_RATE, 1.0)


if __name__ == "__main__":
    unittest.main(verbosity=2)
