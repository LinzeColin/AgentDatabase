#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""`quality_check.py` 拒检整个工作区时，必须自己说「一项都没跑」。

为什么要有这份文件
------------------
`ensure_target()` 拿不到 `meta.json` / `SKILL.md` 就**拒检整个工作区**，
此前只印一条 `target.invalid`。屏幕上「1 条错」看起来像个小毛病，
实际是**零项被检查** —— 同一个坑踩了三次：

  2026-08-14  改完 Leonardo 的九份图版集去看效果，改前改后都是「rc=1、1 条错」，
              差点读成「我的改动什么也没改变」；
  2026-08-14  Churchill 的 13 条 claim 从没被合成门看过一眼，
              而他已经排在判分队列里（`check_scoring_ready.py` 当时就点了名）；
  2026-08-17  拿 32 个未判分工作区跑研究门普查，我发布出「32/32 不通过」——
              其中 **7 个一条检查都没跑**，那个分母是错的。

前两次都只写进了台账。**写进台账的东西没有主人**，于是第三次照犯。
[[a-refusal-to-check-prints-one-error]]｜[[every-requirement-needs-an-owner]]

判据（四条，正反各钉两条）
--------------------------
拒检时：  ① stderr 明说「一项检查都没跑」　② JSON 里 `refused=True` 且 `checks_run=0`
可检时：  ③ 这两个字段**一个都不许出现**　④ 仍照常产出真错误码

★ ③④ 是必须的：只钉正例的话，「永远报拒检」也能全绿。
  [[a-red-that-can-never-turn-green-is-not-a-signal]]
"""
import json
import pathlib
import subprocess
import sys
import unittest

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
QC = ROOT / "scripts" / "quality_check.py"


def _run(target: pathlib.Path):
    p = subprocess.run([sys.executable, str(QC), str(target), "--phase", "research"],
                       capture_output=True, text=True)
    try:
        data = json.loads(p.stdout)
    except Exception:
        data = None
    return p.returncode, p.stderr, data


class RefusalAnnouncesItself(unittest.TestCase):

    def _make(self, tmp: pathlib.Path, *, with_skill: bool):
        """现造工作区，不依赖仓里任何一个真人物 —— 那些会随流程变。"""
        ws = tmp / "somebody"
        ws.mkdir(parents=True)
        (ws / "meta.json").write_text(json.dumps({"slug": "somebody", "profile": "quick"}),
                                      encoding="utf-8")
        if with_skill:
            (ws / "SKILL.md").write_text("---\nname: somebody\n---\n\n正文\n", encoding="utf-8")
        return ws

    def test_refused_target_says_zero_checks_ran(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._make(pathlib.Path(td), with_skill=False)
            rc, err, data = _run(ws)

            self.assertEqual(rc, 1, "缺 SKILL.md 应当拒检并 rc=1")
            self.assertIsNotNone(data, "拒检时仍须产出可解析的 JSON")
            # ① stderr 说人话
            self.assertIn("一项检查都没跑", err,
                          "拒检必须在 stderr 明说零项被检查，否则「1 条错」会被读成小毛病")
            # ② JSON 里机器读得到
            self.assertIs(data.get("refused"), True, "JSON 缺 refused=true")
            self.assertEqual(data.get("checks_run"), 0, "JSON 缺 checks_run=0")
            self.assertIn("SKILL.md", data.get("missing_required") or [],
                          "应当点名缺的是哪个文件，而不是只给一句 Not a target")
            # 形状不许变 —— 两个解析方读的是 passed / errors
            self.assertIs(data.get("passed"), False)
            self.assertTrue(data.get("errors"), "errors 仍须在，形状不许变")

    def test_checkable_target_carries_no_refusal_marks(self):
        """反面：能被检查的工作区，一个拒检标记都不许有。"""
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._make(pathlib.Path(td), with_skill=True)
            rc, err, data = _run(ws)

            self.assertIsNotNone(data, "可检工作区也须产出可解析的 JSON")
            self.assertNotIn("refused", data,
                             "没被拒检却带了 refused 字段 —— 那样这道信号就永远为真")
            self.assertNotIn("checks_run", data)
            self.assertNotIn("一项检查都没跑", err)
            # ④ 它是个空壳工作区，**必须**真跑出错误来；
            #    一个「可检但零错误」的空壳会让 ③ 变得没有意义。
            self.assertTrue(data.get("errors"),
                            "空壳工作区居然 0 错误 —— 说明检查根本没落到实处")


if __name__ == "__main__":
    unittest.main(verbosity=0)
