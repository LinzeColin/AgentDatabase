#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`check_execution_contract_fits_a_context.py` 的**调用方**。

`test_all_selftests_have_a_runner.py` 只跑 `--self-test`，**跑不到 `main()`**。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测 @v0.0.0.41）

整条链现跑（route→dossier→contract，**读盘上字节**）：

    single_expert  1 人  contract   38 KB
    small_team     9 人  contract  233 KB
    deep_team     28 人  contract  **776 KB**（dossier 更是 1796 KB）

合同 98% 是 `execution_units`（每位专家一段）⇒ **随人数近似线性长**。

★★ 与档位阶梯并排读：**32 个无意义词就能拿到 deep_team**
⇒ 一个稍长的请求就能产出宿主可能装不下的合同。

★ 本件**不判「太大了」**（多大算大取决于宿主），只判
「**每位专家占的字节不许比基线更胖**」—— 那才是这个包控制得了的。
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_execution_contract_fits_a_context.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class ExecutionContractFitsAContext(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_per_expert_bytes_did_not_grow(self):
        r = _run()
        self.assertNotEqual(r.returncode, 4, "**未量不是通过**：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_prints_bytes_before_tokens(self):
        """★ 字节是实测、token 是估算 —— 两者必须分开印，且 token 要给区间。"""
        r = _run()
        self.assertIn("盘上字节", r.stdout)
        self.assertIn("除数是我选的", r.stdout)
        self.assertIn("区间", r.stdout)
        self.assertNotIn("%%", r.stdout, "百分号写成了 `%%`，会原样印给用户")

    def test_floor_can_actually_fire(self):
        """★★★ 一道永远红不了的门不是门。"""
        r = _run("--baseline-kb-per-expert", "1")
        self.assertEqual(r.returncode, 1, r.stdout)

    def test_the_whole_chain_is_what_gets_run(self):
        """★★ 本件的价值在于**跑整条链**（我一直在验单步）—— 三步都要出现。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        src = CHECKER.read_text(encoding="utf-8")
        for step in ("route_team_moe.py", "build_team_dossier.py", "build_execution_contract.py"):
            self.assertIn(step, src, "少了 %s ⇒ 就不是整条链了" % step)

    def test_constants_are_reachable(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_execution_contract_fits_a_context import (
            BASELINE_KB_PER_EXPERT, DIVISORS, MIN_MODES)
        self.assertGreater(BASELINE_KB_PER_EXPERT, 0.0, "地板 0 ⇒ 永远红")
        self.assertGreaterEqual(MIN_MODES, 2)
        self.assertGreaterEqual(len(DIVISORS), 2, "token 必须给区间，不许只给一个除数")


if __name__ == "__main__":
    unittest.main(verbosity=2)
