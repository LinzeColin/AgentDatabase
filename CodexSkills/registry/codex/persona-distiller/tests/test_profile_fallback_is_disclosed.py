#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""profile 缺席时两件判据回退到不同档 —— 本测钉住「至少要说出来」。

★★★ 2026-08-17 订正：**第一版是个脚本，不是测试模块。**
  它在**模块级**跑断言并以 `sys.exit(...)` 结束，于是
  `python3 -m unittest discover` 一 import 就抛 `SystemExit`：

      ERROR: test_profile_fallback_is_disclosed (unittest.loader._FailedTest)
      ImportError: Failed to import test module … SystemExit: 0

  单跑它是 `自测 6/6`、rc=0 —— **我只验了这一步，没走过套件那条链**。
  而 README 教的第一条命令 `self_check.py` 正是跑这个套件，于是它 rc=1。
  [[verifying-single-commands-is-not-verifying-the-chain]]
  [[my-verification-loop-never-opened-the-files]]

  现在是标准 `unittest.TestCase`：模块级只做 import 与常量，
  一切断言都在测试方法里；直跑本文件仍然可用（走 `unittest.main()`）。
"""
import json
import pathlib
import subprocess
import sys
import unittest

_r = subprocess.run(["git", "-C", str(pathlib.Path(__file__).resolve().parent),
                     "rev-parse", "--show-toplevel"], capture_output=True, text=True)
REPO = pathlib.Path(_r.stdout.strip()) if _r.returncode == 0 else pathlib.Path(".").resolve()
PD = REPO / "CodexSkills/registry/codex/persona-distiller"
QC = PD / "scripts/quality_check.py"
sys.path.insert(0, str(PD / "scripts"))
sys.path.insert(0, str(REPO / "CodexSkills/skill_log_evals/persona-distiller/_ledgers/_pipeline"))


def _fallback_note(ws):
    """→ (profile_fallback 提示, 实际用的档)。跑真 quality_check，不模拟。"""
    r = subprocess.run([sys.executable, str(QC), str(ws), "--phase", "research"],
                       capture_output=True, text=True, timeout=900)
    o = r.stdout + r.stderr
    d = json.loads(o[o.find("{"):]) if "{" in o else {}
    return d.get("metrics", {}).get("profile_fallback"), d.get("profile")


class ProfileFallbackIsDisclosed(unittest.TestCase):
    """缺 `meta.profile` 时两件工具按 3 倍不同的门槛判 —— 至少要印出来。"""

    @classmethod
    def setUpClass(cls):
        from common import PROFILE_THRESHOLDS
        from workspace_roots import iter_workspaces, CORPORA
        cls.TH = PROFILE_THRESHOLDS
        cls.by = {w.name: w for w in iter_workspaces(CORPORA)}
        # ★ 两次真跑很贵（各自要几十秒），整类只跑一遍。
        cls.note_missing = _fallback_note(cls.by["winston-churchill"])
        cls.note_declared = _fallback_note(cls.by["robert-koch"])

    def test_quality_check_falls_back_to_standard(self):
        src = (PD / "scripts/quality_check.py").read_text(encoding="utf-8")
        self.assertIn("meta.get('profile')", src)
        self.assertIn("or 'standard'", src)

    def test_corpus_feasibility_falls_back_to_quick(self):
        src = (PD / "scripts/check_corpus_feasibility.py").read_text(encoding="utf-8")
        self.assertIn("profile = 'quick'", src)

    def test_the_two_defaults_really_differ(self):
        """★ 本测存在的理由：两个默认档的 `min_sources` 必须真的不同。"""
        self.assertNotEqual(self.TH["standard"]["min_sources"],
                            self.TH["quick"]["min_sources"])

    def test_missing_profile_prints_a_fallback_note(self):
        note, profile = self.note_missing
        self.assertTrue(note, "缺 profile 的工作区应当印出回退提示")
        self.assertEqual(profile, "standard")

    def test_the_note_names_both_thresholds(self):
        """★ 只说「回退了」没用 —— 读者要看得出两档差多少。"""
        note, _ = self.note_missing
        self.assertTrue(note)
        for token in (str(self.TH["standard"]["min_sources"]),
                      str(self.TH["quick"]["min_sources"]), "quick"):
            self.assertIn(token, note)

    def test_declared_profile_prints_no_note(self):
        """★★ 反对照：`meta` 里写了 profile 的**不许**印回退提示（koch=deep）。"""
        note, profile = self.note_declared
        self.assertIsNone(note)
        self.assertEqual(profile, "deep")


if __name__ == "__main__":
    unittest.main(verbosity=2)
