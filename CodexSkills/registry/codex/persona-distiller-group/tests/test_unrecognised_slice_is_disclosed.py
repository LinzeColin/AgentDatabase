#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**词表外的 `--task-slice` 不许静默变成 0。**

## 抓到它的那一次（2026-08-17）

照 SKILL.md 的六步走第 5 步，随手写了 `--task-slice retail-expansion`：

    rc=0｜sample_count 1｜task_slice_coverage **0.0**

而 `coverage = |观测 ∩ EXPECTED_SLICES| / |EXPECTED_SLICES|` —— 那是一张
**12 个词的固定表**，只活在 `record_team_outcome.py` 的常量里：
`--task-slice` **没有 `choices=`、没有 help**，SKILL.md 写的是 `<slice>`，
一个字都没提有词表。

⇒ 使用者写一个表外的名字，会得到一条**看起来正常**的遥测记录，
coverage 永远是 0，而**C 层启用看的正是 coverage**
（`eligible_for_c = runs>=60 and ece<=0.12 and coverage>=0.75`）。
**不认识的值静默变成 0，和分数被算成常数是同一个病。**

## 为什么不用 `choices=` 硬拒

硬拒会卡住真实流程（本项目规矩：「不许因为过不了门而卡住流程」）。
改成**收下 + 披露**：词表进 `--help`，表外的名字进遥测的
`unrecognised_task_slices` 与 `task_slice_coverage_note`。
**证据要留在仓里，不是终端里。**
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / "scripts"
sys.path.insert(0, str(S))


class UnrecognisedSliceIsDisclosed(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        from record_team_outcome import EXPECTED_SLICES
        cls.expected = set(EXPECTED_SLICES)
        cls.route = {"mode": "small_team", "members": [{"subject_slug": "x"}],
                     "strategy": "B", "task_graph": {}}
        cls.delta = {"dimensions": {"overall_delta": 80.0, "quality": 80.0},
                     "minimum_dimension": 80.0, "formal_market_pass": False}

    def _record(self, slice_name, td):
        td = pathlib.Path(td)
        rp, ds, tl = td / "rp.json", td / "ds.json", td / "tl.json"
        rp.write_text(json.dumps(self.route), encoding="utf-8")
        ds.write_text(json.dumps(self.delta), encoding="utf-8")
        r = subprocess.run([sys.executable, str(S / "record_team_outcome.py"),
                            "--route-plan", str(rp), "--delta-score", str(ds),
                            "--task-slice", slice_name, "--actual-success", "0.8",
                            "--telemetry", str(tl)], capture_output=True, text=True)
        got = json.loads(tl.read_text(encoding="utf-8")) if tl.is_file() else {}
        return r, got

    # ── 负例：表外的名字必须被标出来 ──────────────────────────────
    def test_unknown_slice_is_flagged_in_the_artifact(self):
        with tempfile.TemporaryDirectory() as td:
            r, got = self._record("retail-expansion", td)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)   # 收下，不硬拒
            self.assertEqual(got.get("unrecognised_task_slices"), ["retail-expansion"])
            self.assertIn("⚠", got.get("task_slice_coverage_note", ""))
            self.assertEqual(got.get("task_slice_coverage"), 0.0)

    def test_the_expected_vocabulary_ships_in_the_artifact(self):
        """★ 光标出「不认识」不够——**得告诉他认识哪些**，否则他改不对。"""
        with tempfile.TemporaryDirectory() as td:
            _, got = self._record("retail-expansion", td)
            self.assertEqual(set(got.get("expected_task_slices", [])), self.expected)

    def test_help_names_the_vocabulary(self):
        """★★ 词表原来只活在常量里。`--help` 是用户唯一够得着的地方。"""
        r = subprocess.run([sys.executable, str(S / "record_team_outcome.py"), "--help"],
                           capture_output=True, text=True)
        for w in ("small-product", "swarm-search", "ood-boundary"):
            self.assertIn(w, r.stdout, "--help 里没有 %s" % w)

    # ── 正例：表内的名字不许被误标 ────────────────────────────────
    def test_known_slice_is_not_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            r, got = self._record("small-product", td)
            self.assertEqual(r.returncode, 0)
            self.assertEqual(got.get("unrecognised_task_slices"), [])
            self.assertNotIn("⚠", got.get("task_slice_coverage_note", ""))
            self.assertGreater(got.get("task_slice_coverage", 0), 0)

    def test_every_expected_slice_is_accepted_without_flag(self):
        """★★★ 逐个跑全部 12 个 —— 只测一个会漏掉词表里拼错的那个。

        （本项目实测过：一张 92 词的关键词表召回只有 42%，
        「匹配不上」的结论必须先量匹配器自己。）
        """
        with tempfile.TemporaryDirectory() as td:
            for s in sorted(self.expected):
                with self.subTest(slice=s):
                    d = pathlib.Path(td) / s      # 每个 slice 一个干净目录，遥测不串
                    d.mkdir()
                    _, got = self._record(s, d)
                    self.assertEqual(got.get("unrecognised_task_slices"), [], s)
                    self.assertGreater(got.get("task_slice_coverage", 0), 0, s)


if __name__ == "__main__":
    unittest.main(verbosity=2)
