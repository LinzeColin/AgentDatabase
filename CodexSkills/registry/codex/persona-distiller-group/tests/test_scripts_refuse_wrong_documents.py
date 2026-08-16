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


if __name__ == "__main__":
    unittest.main(verbosity=0)
