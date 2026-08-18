#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`check_team_size_ladder_has_no_hole.py` 的**调用方**。

`test_all_selftests_have_a_runner.py` 只跑 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.39）

只靠推断（不给 `--size` / `--mode`），`persona_expert_target` 取得到的是
**{1, 9, 10, 11, 21, 22}**（纯长度扫 1–240 词）／**{10,11,12,24,25,28}**（72 道 oracle）。
**2–8 这一整段，两种样本上一次都没出现过。**

成因可从公式推：`single_expert` 恰好 1；`small_team` 是
`min(15, max(5, round(5 + 6c + 3r + |domains|)))`，而进门要 `c ≥ 0.38`
⇒ 门一过、各分量落地板就已经是 **9**。

出口存在但自相矛盾：`--size 5..8` 只在**推断出的模式已经是 small_team** 时被接受；
任务短到 `single_expert` 时 `--size 6` 被拒 ⇒ **想要 6 人，得先把任务写到够拿 9 人**。

★ 本件**不补那个洞**（改公式/改门会移动每一道任务的人数 ⇒ Task #134），
  只钉「推断可达的档位不许再少」＋ 钉住成因公式与出口行为还在。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_team_size_ladder_has_no_hole.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class TeamSizeLadderHasNoHole(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_ladder_did_not_lose_a_rung(self):
        r = _run()
        self.assertNotEqual(r.returncode, 4, "**未量不是通过**：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_prints_the_hole_and_the_cause(self):
        """★ 空扫描面报红：可达集合、空洞、成因公式三样都得印出来。"""
        r = _run()
        self.assertIn("取得到的人数", r.stdout)
        self.assertIn("一次都没出现", r.stdout)
        self.assertIn("成因", r.stdout)

    def test_floor_can_actually_fire(self):
        """★★★ 一道永远红不了的门不是门。"""
        r = _run("--baseline-reachable", "99")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_the_contract_still_declares_five(self):
        """★★ 「合同说 5、实际最少 9」是本件的全部张力 —— 合同那个 5 被改了就要重写。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        import compile_task_graph as C
        self.assertEqual(C.MODE_LIMITS["small_team"][0], 5)
        self.assertEqual(C.MODE_LIMITS["single_expert"], (1, 1))

    def test_the_escape_hatch_still_requires_what_it_escapes(self):
        """★★★ 出口的自相矛盾本身要钉住：small_team 下 --size 6 收，
        single_expert 下 --size 6 拒。任一边变了，SKILL.md 那行就该改。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        import compile_task_graph as C
        from check_team_size_ladder_has_no_hole import gibberish
        g = C.compile_graph(gibberish(32), "auto", 6)
        self.assertEqual(g["persona_expert_target"], 6, "small_team 下 --size 6 该被接受")
        with self.assertRaises(Exception, msg="single_expert 下 --size 6 该被拒"):
            C.compile_graph(gibberish(10), "auto", 6)


if __name__ == "__main__":
    unittest.main(verbosity=2)
