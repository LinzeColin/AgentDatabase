#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**文档里的「怎么重跑」不能指向包外的脚本** —— 判据的调用方。

判据本体：`scripts/check_cited_scripts_ship_with_the_package.py`。
`test_all_selftests_have_a_runner.py` 只跑它的 `--self-test`，**跑不到 `main()`** ——
那样「有人往 SKILL.md 里新写了一个包外脚本名」不会有任何人喊。
[[a-checker-nothing-calls-is-not-a-checker]]

## 它守的那件事（2026-08-18 实测）

`SKILL.md` 的「已测量的边界」表八行，每行一列「怎么重跑」。逐个查：
**四个脚本不在本包里**（在 `_ledgers/_pipeline/` 开发台账树），
装了这个 skill 的人照着敲会得到 `can't open file`。
[[green-in-the-repo-dead-in-the-package]]

★ 本件同时钉住**披露本身**：SKILL.md 里那段「有四个脚本不在你装的包里」如果被删掉，
  判据仍会绿（它只查明码表），所以**披露要由本件单独钉**。
  [[a-comment-claiming-a-guard-is-not-a-guard]]
"""
import pathlib
import subprocess
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECKER = ROOT / "scripts" / "check_cited_scripts_ship_with_the_package.py"


def _run(*args):
    return subprocess.run([sys.executable, str(CHECKER), *args],
                          capture_output=True, text=True)


class CitedScriptsShipWithThePackage(unittest.TestCase):

    def test_checker_self_test_passes(self):
        r = _run("--self-test")
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)

    def test_no_undisclosed_out_of_package_script(self):
        """rc=1 有未披露的包外脚本；**rc=4 是未核，同样不算通过**。"""
        r = _run()
        self.assertNotEqual(r.returncode, 4,
                            "**未核不是通过** —— 一个脚本名都没扫到：\n" + r.stdout)
        self.assertEqual(r.returncode, 0, r.stdout)

    def test_it_actually_scanned_something(self):
        """★ 空扫描面报红：没印出被点名的个数就不算跑过。"""
        r = _run()
        self.assertIn("被点名", r.stdout)
        self.assertIn("包内", r.stdout)

    def test_skill_md_carries_the_disclosure(self):
        """★★ 判据只查明码表，**查不到披露在不在**。这一条单独钉住那段文字。"""
        text = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        self.assertIn("不在你装的这个包里", text,
                      "SKILL.md 里那段「四个脚本不在本包」的披露不见了")
        for name in ("measure_routing_discrimination.py",
                     "check_benchmark_mode_accuracy.py",
                     "check_registered_products_have_delta_evidence.py",
                     "report_expert_team_state.py"):
            with self.subTest(script=name):
                self.assertIn(name, text, "披露里没点名 %s" % name)

    def test_acknowledged_list_is_not_a_blanket(self):
        """★★★ 明码表不许变成万能豁免：里面每一条都必须**真的不在包内**。"""
        sys.path.insert(0, str(ROOT / "scripts"))
        from check_cited_scripts_ship_with_the_package import (
            OUT_OF_PACKAGE_ACKNOWLEDGED, in_package)
        for name, where in OUT_OF_PACKAGE_ACKNOWLEDGED.items():
            with self.subTest(script=name):
                self.assertFalse(in_package(name, ROOT),
                                 "%s 其实在包内，不该出现在「已披露包外」名单里" % name)
                self.assertTrue(str(where).strip(), "%s 没写它在哪" % name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
