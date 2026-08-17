#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""流水线脚本吃到**错文档**时，不许 rc=0 还照样产出。

为什么要有这份文件
------------------
2026-08-17 交叉喂测：把一份毫不相干的 JSON 交给每个吃文档的入参，
6 个入参里 **4 个 rc=0 还照样产出**：

    score_team_delta      --result       印出 overall_delta 17.5
                                         （那是「所有 delta 都缺 ⇒ 都当 0」的常数）
    build_team_delta_card --result       写出 audit_trace/next_action 全 null 的
                                         **用户卡片**，还带一句 CANDIDATE_REJECTED_BELOW_FLOOR
    build_team_delta_card --delta-score   同上
    record_team_outcome   --route-plan   **rc=0 把垃圾写进遥测账本** ——
                                         而 route_team_moe 正拿它当 C 策略先验，
                                         一条垃圾记录会污染以后所有路由的排序

四处都补了拒答。**但那次是手工扫的** —— 手工扫出来的东西没有主人，
下一个新脚本照样会再犯。本件把那套扫法固定下来。
[[empty-default-swallows-unknown]]｜[[every-requirement-needs-an-owner]]

判据：喂错文档 ⇒ **要么 rc≠0，要么不产出**。两样都不占就是假绿。

★ 本件印出实跑了几组，并对扫描面过小自己报红。
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / "scripts"


def cases(td: pathlib.Path):
    junk = td / "junk.json"
    junk.write_text(json.dumps({"totally": "unrelated", "n": 1}), encoding="utf-8")
    rp = td / "rp.json"
    rp.write_text(json.dumps({"mode": "small_team", "selected": [
        {"subject_slug": "a", "display_name": "A"}]}), encoding="utf-8")
    narr = td / "narr.json"
    narr.write_text(json.dumps({"work_completed": "x", "member_contributions": [],
                                "decision_changing_disagreements": [], "audit_trace": [],
                                "next_action": "y", "remaining_unknowns": []}),
                    encoding="utf-8")
    ds = td / "ds.json"
    ds.write_text(json.dumps({"dimensions": {}, "benefit_deltas": {}, "status": "x",
                              "formal_market_pass": False, "minimum_dimension": 0}),
                  encoding="utf-8")
    out = td / "out.json"
    return junk, rp, narr, ds, out, [
        ("score_team_delta --result",
         [S / "score_team_delta.py", "--result", junk, "--output", out]),
        ("build_team_delta_card --result",
         [S / "build_team_delta_card.py", "--route-plan", rp, "--result", junk,
          "--delta-score", ds, "--output", out]),
        ("build_team_delta_card --delta-score",
         [S / "build_team_delta_card.py", "--route-plan", rp, "--result", narr,
          "--delta-score", junk, "--output", out]),
        ("record_team_outcome --route-plan",
         [S / "record_team_outcome.py", "--route-plan", junk, "--delta-score", ds,
          "--task-slice", "x", "--actual-success", "0.8", "--telemetry", out]),
        ("record_team_outcome --delta-score",
         [S / "record_team_outcome.py", "--route-plan", rp, "--delta-score", junk,
          "--task-slice", "x", "--actual-success", "0.8", "--telemetry", out]),
        ("build_team_dossier --route-plan",
         [S / "build_team_dossier.py", "--route-plan", junk, "--registry-root", ROOT,
          "--output", out]),
        ("build_execution_contract --route-plan",
         [S / "build_execution_contract.py", "--route-plan", junk, "--dossier", junk,
          "--output", out]),
        ("route_team_moe --telemetry",
         [S / "route_team_moe.py", "--registry-root", ROOT, "--telemetry", junk,
          "--output", out]),
    ]


class WrongDocumentTests(unittest.TestCase):
    def test_wrong_document_never_yields_output_with_rc_zero(self):
        bad, ran = [], 0
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            _, _, _, _, out, rows = cases(td)
            for name, cmd in rows:
                if out.exists():
                    out.unlink()
                r = subprocess.run([sys.executable] + [str(x) for x in cmd],
                                   capture_output=True, text=True)
                ran += 1
                produced = out.exists() and out.stat().st_size > 0
                if r.returncode == 0 and produced:
                    bad.append((name, (r.stdout or "").strip()[:70]))
        print("扫描面：**%d** 组「入参 × 错文档」" % ran)
        self.assertGreaterEqual(ran, 8, "扫描面太小，本次不构成通过")
        for n, t in bad:
            print("  ✗ %-38s rc=0 且产出了：%s" % (n, t))
        self.assertEqual(bad, [], "有脚本吃了错文档还 rc=0 产出：%s"
                         % [n for n, _ in bad])


class UnrecognisedFieldsAreRefusedNotScored(unittest.TestCase):
    """★★★ 四个区段都在、**字段名一个都不认识** ⇒ 必须拒答，不许出成绩单。

    2026-08-17 实测（修前）：`overall_delta` **恒为 17.5**——小值、大值
    （baseline=-999）、只填一个区段，三种输入同一个数。因为路径完全相同：
    全部读成 0。而 status 印 `CANDIDATE_REJECTED_BELOW_FLOOR`，
    **把「我读不懂你的输入」报成了「你的团队不合格」**——
    使用者会去返工团队，而真因是字段名拼错。

    原守卫只查「四个区段空不空」（容器），坏的是「字段认不认识」（键）。
    """

    S = pathlib.Path(__file__).resolve().parents[1] / "scripts"

    def _run(self, doc, td):
        src, out = pathlib.Path(td) / "in.json", pathlib.Path(td) / "out.json"
        src.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
        r = subprocess.run([sys.executable, str(self.S / "score_team_delta.py"),
                            "--result", str(src), "--output", str(out)],
                           capture_output=True, text=True)
        return r, out

    def test_bogus_field_names_are_refused(self):
        with tempfile.TemporaryDirectory() as td:
            r, out = self._run({"absolute": {"aaa": 1}, "candidate": {"bbb": 1},
                                "baseline": {"bbb": 1}, "paired": {"ccc": 0.1}}, td)
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertIn("blocked", r.stdout)
            self.assertFalse(out.exists() and out.stat().st_size > 0,
                             "拒答却仍写出了成绩单")

    def test_refusal_names_the_expected_fields(self):
        """★ 报错要当模板用——仓里没有 result-input.json 的样例。"""
        with tempfile.TemporaryDirectory() as td:
            r, _ = self._run({"absolute": {"aaa": 1}}, td)
            for k in ("user_experience", "task_completion", "win_rate"):
                self.assertIn(k, r.stdout, "报错里没印出字段名 %s" % k)

    def test_the_constant_is_never_emitted_as_a_score(self):
        """★★ 17.5 这个常数不许再作为**分数**出现在任何一种瞎猜输入上。

        ★★★ 本件第一版断的是 `assertNotIn("17.5", r.stdout)` —— **当场被自己打中**：
        拒答文案里为了解释成因写了「常数（17.5）」。
        **判据别扫说明层**，要断在**产物**上。
        [[my-checkers-are-mis-cut-six-times-in-one-day]]
        """
        with tempfile.TemporaryDirectory() as td:
            for doc in ({"absolute": {"x": 1}},
                        {"candidate": {"y": 999}, "baseline": {"y": -999}},
                        {"paired": {"z": 0.99}}):
                r, out = self._run(doc, td)
                self.assertEqual(r.returncode, 2, "%s 没被拒答" % doc)
                # 断在产物：拒答就不许写出成绩单；万一写了，里面也不许有 overall_delta
                if out.exists() and out.stat().st_size > 0:
                    got = json.loads(out.read_text(encoding="utf-8"))
                    self.assertNotIn("overall_delta", got.get("dimensions", {}),
                                     "拒答却仍写出了 overall_delta：%s" % got)

    # ── ★ 正例：不许误伤「部分填写」的合法输入 ──────────────────────
    def test_one_real_field_still_scores(self):
        with tempfile.TemporaryDirectory() as td:
            r, out = self._run({"absolute": {"quality": 90}, "candidate": {},
                                "baseline": {}, "paired": {}}, td)
            self.assertNotEqual(r.returncode, 2, "只填一个真字段被误伤了：" + r.stdout)
            self.assertTrue(out.exists() and out.stat().st_size > 0)

    def test_one_real_field_in_each_section_still_scores(self):
        with tempfile.TemporaryDirectory() as td:
            for doc in ({"absolute": {"routing": 80}},
                        {"candidate": {"cost": 1}},
                        {"baseline": {"latency": 2}},
                        {"paired": {"win_rate": 0.8}}):
                r, out = self._run(doc, td)
                self.assertNotEqual(r.returncode, 2, "%s 被误伤：%s" % (doc, r.stdout))


if __name__ == "__main__":
    unittest.main(verbosity=0)
