#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""路由必须**真的在区分**——排序坍成常数时要有人报。

为什么要有这份文件
------------------
2026-08-17 做了一次广谱破坏：把 `route_team_moe.score_candidate` 的打分改成
恒定 `0.5`（排序信息全丢），然后跑本 skill 当时的 **7 件测试** ——

    **7 件无一察觉，全部 rc=0。**

整套测试查的是披露、合同、拒答、遥测往返，**没有一件在看「排序还成不成立」**。
而路由正是 Owner 评分里点名的那一项。一个功能被彻底打坏而测试全绿，
那不是测试通过，是测试看不见。
[[a-red-that-can-never-turn-green-is-not-a-signal]]｜[[zero-hit-gates-must-prove-they-can-hit]]

## 本件**不预设路由该选谁**

「软件题该不该选 Simon Willison」是**待 Owner 裁定**的契约分歧
（上游 `test_group_contract.py` 至今为此红着）。本件刻意避开那个问题，
只钉两条**无论裁定结果如何都必须成立**的性质：

1. **题内可分**：同一题落座的人，分数不能全都一样。
2. **跨题可分**：两道明显不同的题，名单不能完全相同。

实测基线（2026-08-17）：软件题头名 `linus-torvalds`、金融题头名 `warren-buffett`，
两题各 10 席、重合 4 人；软件题前四名分数 0.3071／0.2647／0.2447／0.2027。

★ 读的是 `base_score` —— 我第一次写这个探针时读的是 `score`，
  那个键**根本不存在**，于是「分数互不相同 1/10」是假的。
  **报数之前先确认那个键在。**[[the-field-was-filled-with-the-filename]]
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
ROUTE = ROOT / "scripts" / "route_team_moe.py"
SOFT = "把一个 Python 单体服务拆成微服务，并设计灰度发布"
FIN = "为一支价值型股票组合设计再平衡与风险敞口规则"


def route(task: str, out: pathlib.Path) -> dict:
    r = subprocess.run([sys.executable, str(ROUTE), "--task", task,
                        "--registry-root", str(ROOT), "--output", str(out)],
                       capture_output=True, text=True)
    if r.returncode != 0 or not out.exists():
        raise AssertionError("路由失败 rc=%d：%s" % (r.returncode, (r.stderr or "")[:300]))
    return json.loads(out.read_text(encoding="utf-8"))


def seats(plan: dict) -> list:
    return [m for m in (plan.get("members") or plan.get("selected") or [])
            if isinstance(m, dict)]


class RoutingDiscriminatesTests(unittest.TestCase):
    def test_scores_are_not_degenerate_and_tasks_differ(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            td = pathlib.Path(td)
            soft = route(SOFT, td / "soft.json")
            fin = route(FIN, td / "fin.json")

        s_seats, f_seats = seats(soft), seats(fin)
        # ★ 空扫描面不算通过
        self.assertGreaterEqual(len(s_seats), 3, "软件题只落座 %d 人，样本太小" % len(s_seats))
        self.assertGreaterEqual(len(f_seats), 3, "金融题只落座 %d 人，样本太小" % len(f_seats))

        for name, rows in (("软件题", s_seats), ("金融题", f_seats)):
            self.assertTrue(all("base_score" in m for m in rows),
                            "%s 有席位不带 `base_score` —— 键名变了就先改本件，别让它空转" % name)
            scores = {round(float(m["base_score"]), 6) for m in rows}
            print("  %s：%d 席，分数互不相同 **%d** 个" % (name, len(rows), len(scores)))
            self.assertGreater(
                len(scores), 1,
                "%s 的 %d 个席位分数**完全一样**（%r）—— 排序已坍成常数，"
                "这正是 2026-08-17 那次广谱破坏的形状" % (name, len(rows), scores))

        s_slugs = [m.get("subject_slug") for m in s_seats]
        f_slugs = [m.get("subject_slug") for m in f_seats]
        print("  两题名单重合 %d 人（%d／%d）"
              % (len(set(s_slugs) & set(f_slugs)), len(s_slugs), len(f_slugs)))
        self.assertNotEqual(
            set(s_slugs), set(f_slugs),
            "两道明显不同的题选出**完全相同**的名单 —— 路由没有在区分任务")


if __name__ == "__main__":
    unittest.main(verbosity=0)
