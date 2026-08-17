#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「门没能判」不许说成「门判了不合格」** —— 本件管两种形状。

形状一：`quality_check.py` 拒检整个工作区时，必须自己说「一项都没跑」。
形状二：holdout 门跑起来了但定位不到正文时，不许报成「有内容重合」。

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


class UnverifiableIsNotAViolation(unittest.TestCase):
    """holdout 门定位不到正文时，报「未核」，不许报「有重合」。

    `check_holdout_overlap.py` 自己分得很清楚 —— 定位不到正文时它印
    「✗ 找不到正文的源 N 条 …… **无法判定，不算通过**」并 rc=2。
    而 `quality_check` 此前把**所有** ✗ 一律计进 `hard`，再报成
    「holdout 与 train 有内容重合（N 条硬失败）—— **现在换源还来得及**」。

    Rousseau #178 实测：唯一那条 ✗ 是「找不到正文的源 **103** 条」
    （语料正文本来就不进 git），**零条真重合**，而门印的是「有内容重合」
    并劝人换源 —— 换源修不了「文件不在这台机器上」。
    全库 25 个被检查的未判分工作区里，**22 个撞的都是这一条**。

    正反各钉一条：**语料缺 → unverifiable**；**真重合 → overlap**。
    只钉一头的话，「永远报未核」或「永远报重合」都能全绿。
    """

    def _ws(self, tmp: pathlib.Path, contaminated: bool):
        ws = tmp / "contam"
        (ws / "evidence").mkdir(parents=True)
        (ws / "raw").mkdir()
        (ws / "meta.json").write_text(
            json.dumps({"slug": "contam", "profile": "quick", "name": "Test Person"}),
            encoding="utf-8")
        (ws / "SKILL.md").write_text("---\nname: contam\n---\n\n正文\n", encoding="utf-8")
        body = (" ".join(
            "the quick brown fox jumps over the lazy dog near a silent river bank at dawn "
            "while distant bells ring across the valley and the miller counts his sacks "
            "of grain before the market opens".split()) + " ") * 6
        led = [{"source_id": "t1", "split": "train", "local_path": "raw/t1.txt"},
               {"source_id": "h1", "split": "holdout", "local_path": "raw/h1.txt"}]
        (ws / "evidence/source-ledger.jsonl").write_text(
            "\n".join(json.dumps(r) for r in led) + "\n", encoding="utf-8")
        (ws / "raw/t1.txt").write_text(body + "\n", encoding="utf-8")
        if contaminated:
            # holdout 逐字含 train 的一大段 —— **真重合**
            (ws / "raw/h1.txt").write_text("preamble words here " + body
                                           + " trailing words here\n", encoding="utf-8")
        # contaminated=False 时故意不落 h1.txt ⇒ 定位不到正文 ⇒ **未核**
        return ws

    def _holdout(self, ws):
        rc, err, data = _run(ws)
        self.assertIsNotNone(data, "须产出可解析 JSON")
        codes = [e["code"] for e in data.get("errors", [])
                 if e["code"].startswith("corpus.holdout")]
        return codes, data.get("metrics", {}).get("holdout_overlap", {}), data

    def test_missing_body_reports_unverifiable_not_overlap(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(pathlib.Path(td), contaminated=False)
            codes, h, data = self._holdout(ws)
            self.assertIn("corpus.holdout-unverifiable", codes)
            self.assertNotIn("corpus.holdout-overlap", codes,
                             "定位不到正文却报「有内容重合」—— 未核被说成了违规")
            self.assertEqual(h.get("其中·真重合"), 0)
            self.assertGreaterEqual(h.get("其中·无法判定") or 0, 1)
            self.assertFalse(any("换源" in e["message"] for e in data.get("errors", [])),
                             "**换源修不了「文件不在这台机器上」**，不许这么劝")

    def test_real_overlap_still_reports_overlap(self):
        import tempfile
        with tempfile.TemporaryDirectory() as td:
            ws = self._ws(pathlib.Path(td), contaminated=True)
            codes, h, _ = self._holdout(ws)
            self.assertIn("corpus.holdout-overlap", codes,
                          "真重合必须照报 —— 否则上一条测试靠「永远报未核」就能过")
            self.assertNotIn("corpus.holdout-unverifiable", codes)
            self.assertGreaterEqual(h.get("其中·真重合") or 0, 1)
            self.assertEqual(h.get("其中·无法判定"), 0)


if __name__ == "__main__":
    unittest.main(verbosity=0)
