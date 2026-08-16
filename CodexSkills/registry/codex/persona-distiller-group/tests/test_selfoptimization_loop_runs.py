#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自优化回路必须**真的能跑通**，而且样本不够时必须**拒绝校准**。

为什么要有这份文件
------------------
2026-08-17 实测 `telemetry/team-outcomes.json` **0 条记录**。
「0 条」有两种可能，此前从未区分：**回路坏了**，还是**没人跑过**。
当天在 scratchpad 端到端跑了一遍，答案是**没人跑过** ——

    route_team_moe → score_team_delta → record_team_outcome  三步 rc 全 0
    写出的遥测：sample_count=1｜runs=1｜experts=10｜ECE=0.5796｜切片=['software']
    **eligible_for_c=False**
    把遥测喂回路由：`telemetry_prior=0.0`、`reason='not C'` —— **先验正确地没生效**

**回路是通的，拒绝也是对的**（C 策略准入要 ≥60 outcomes、ECE≤0.12、切片覆盖≥0.75）。
但那是一次性手跑 —— **回路哪天坏了没人会知道**。本件把它固定下来。

★ 本件**不断言任何绩效**：判分输入是合法形状的占位数值，
  只用来验「三步跑得通 + 样本不够时不校准」。
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
S = ROOT / "scripts"
TASK = "把一个 Python 单体服务拆成微服务，并设计灰度发布"
RESULT_INPUT = {
    "absolute": {"quality": 80, "task_completion": 78},
    "candidate": {"quality": 8, "task_completion": 7, "risk_reduction": 6,
                  "evidence_coverage": 7, "time_saved": 5, "user_action_reduction": 4},
    "baseline": {"quality": 5, "task_completion": 5, "risk_reduction": 4,
                 "evidence_coverage": 4, "time_saved": 3, "user_action_reduction": 3},
    "paired": {"win_rate": 72, "noninferiority_rate": 80,
               "catastrophic_error_free_rate": 96},
}


def run(*cmd) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable] + [str(x) for x in cmd],
                          capture_output=True, text=True)


class SelfOptimizationLoopTests(unittest.TestCase):
    def test_loop_runs_and_refuses_to_calibrate_on_one_sample(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            w = pathlib.Path(td)
            r1 = run(S / "route_team_moe.py", "--task", TASK,
                     "--registry-root", ROOT, "--output", w / "route.json")
            self.assertEqual(r1.returncode, 0, "① 路由失败：%s" % r1.stderr[:300])

            (w / "ri.json").write_text(json.dumps(RESULT_INPUT), encoding="utf-8")
            r2 = run(S / "score_team_delta.py", "--result", w / "ri.json",
                     "--output", w / "ds.json")
            # score 的 rc：0=过 floor75、3=未过，都算「跑通了」；2 才是拒答
            self.assertIn(r2.returncode, (0, 3), "② 判分异常：%s" % r2.stderr[:300])
            self.assertTrue((w / "ds.json").is_file(), "② 没写出 delta-score")

            r3 = run(S / "record_team_outcome.py", "--route-plan", w / "route.json",
                     "--delta-score", w / "ds.json", "--task-slice", "software",
                     "--actual-success", "0.8", "--telemetry", w / "tel.json")
            self.assertEqual(r3.returncode, 0, "③ 记遥测失败：%s" % r3.stderr[:300])

            tel = json.loads((w / "tel.json").read_text(encoding="utf-8"))
            print("  遥测：sample_count=%s｜eligible_for_c=%s｜experts=%d"
                  % (tel.get("sample_count"), tel.get("eligible_for_c"),
                     len(tel.get("experts") or {})))
            self.assertEqual(tel.get("sample_count"), 1, "遥测没记上这一条")
            # ★ 最要紧的一条：**1 条样本不许启用 C 策略**
            self.assertIs(tel.get("eligible_for_c"), False,
                          "只有 1 条样本却 eligible_for_c=True —— 校准门形同虚设")

            r4 = run(S / "route_team_moe.py", "--task", TASK, "--registry-root", ROOT,
                     "--telemetry", w / "tel.json", "--output", w / "route2.json")
            self.assertEqual(r4.returncode, 0, "④ 带遥测路由失败：%s" % r4.stderr[:300])
            seats = json.loads((w / "route2.json").read_text(encoding="utf-8")).get("members") or []
            self.assertTrue(seats, "④ 带遥测后一个席位都没有")
            priors = {round(float((m.get("score_breakdown") or {}).get("telemetry_prior") or 0), 6)
                      for m in seats}
            print("  带遥测后的 telemetry_prior 取值集合：%s" % priors)
            self.assertEqual(priors, {0.0},
                             "样本不够却把先验用上了：%s" % priors)


if __name__ == "__main__":
    unittest.main(verbosity=0)
