#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""归因塌成一个提交时，`--apply` 必须停手 —— 一个统一而错误的出处比没有出处更坏。

## 它守的那件事（2026-08-18 实测 @v0.0.0.48）

`backfill_distilled_with.py` 从 **git 首次落盘提交处的 VERSION** 推断 `distilled_with`。
方法本身是对的。但在**本仓**实测：

    registration.json 102 / 102 = **100%** 被 git 判成同一个提交 bfe16379a（2026-08-14）新增

那不是「它们同一天被蒸出来」，是**整棵树那天才进的 git**（本仓有两个根提交）。
⇒ `--apply` 会把 **97 份**记录一律盖成 `v0.0.0.154`，
并配上听起来很权威的 `source: git-first-commit`。

**一个统一而错误的出处，比没有出处更坏** —— 后者是「不知道」，前者是「知道错了」。

★ 不硬拒（「不许因为过不了门而卡住流程」）：印出归因分布，`--apply` 要 `--anyway '<理由>'`。
★★ 本件必须有**正对照**：一棵**归因不退化**的树，`--apply` 必须照常写盘 ——
   否则这道守卫会把所有人都拦住，那就成了另一个毛病。
"""
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))


def _git(*args, cwd):
    return subprocess.run(["git", *args], cwd=str(cwd), capture_output=True, text=True)


def _record(n):
    return {"subject_slug": f"p{n}", "versions": [{"version": "0.0.0.1"}]}


def _build_tree(root: pathlib.Path, per_commit: int, total: int) -> pathlib.Path:
    """造一棵 git 树：每 `per_commit` 个人物一个提交，每个提交把 VERSION 往前推一格。"""
    root.mkdir(parents=True, exist_ok=True)
    _git("init", "-q", cwd=root)
    _git("config", "user.email", "t@t", cwd=root)
    _git("config", "user.name", "t", cwd=root)
    reg = root / "CodexSkills" / "registry" / "codex" / "persona-distiller"
    reg.mkdir(parents=True)
    group = root / "CodexSkills" / "registry" / "codex" / "persona-distiller-group"
    made = 0
    while made < total:
        (reg / "VERSION").write_text("v0.0.0.%d\n" % (100 + made), encoding="utf-8")
        for _ in range(per_commit):
            if made >= total:
                break
            d = group / "族" / ("p%d" % made)
            d.mkdir(parents=True, exist_ok=True)
            (d / "registration.json").write_text(json.dumps(_record(made), ensure_ascii=False),
                                                 encoding="utf-8")
            made += 1
        _git("add", "-A", cwd=root)
        _git("commit", "-q", "-m", "batch %d" % made, cwd=root)
    return group


class BackfillRefusesDegenerateAttribution(unittest.TestCase):

    def test_degenerate_tree_blocks_apply_and_writes_nothing(self):
        """★★★ 一次提交加进全部记录 ⇒ --apply 必须 blocked，且盘上一个字节不动。"""
        from backfill_distilled_with import run
        with tempfile.TemporaryDirectory() as td:
            group = _build_tree(pathlib.Path(td) / "r", per_commit=6, total=6)
            before = {p: p.read_bytes() for p in group.rglob("registration.json")}
            out = run(group, apply_changes=True)
            self.assertEqual(out.get("status"), "blocked", out)
            self.assertTrue(out["degeneracy"]["degenerate"])
            self.assertEqual(out["degeneracy"]["top_commit_share"], 1.0)
            for p, raw in before.items():
                self.assertEqual(p.read_bytes(), raw, "被拦下了却仍然写了盘")

    def test_non_degenerate_tree_still_applies(self):
        """★★ 正对照：每次提交只加 1 个人 ⇒ 归因不退化 ⇒ --apply 必须照常写盘。"""
        from backfill_distilled_with import run
        with tempfile.TemporaryDirectory() as td:
            group = _build_tree(pathlib.Path(td) / "r", per_commit=1, total=6)
            out = run(group, apply_changes=True)
            self.assertNotEqual(out.get("status"), "blocked", out)
            self.assertTrue(out["applied"])
            self.assertFalse(out["degeneracy"]["degenerate"], out["degeneracy"])
            self.assertGreater(out["degeneracy"]["distinct_first_commits"], 1)
            one = json.loads(next(group.rglob("registration.json")).read_text(encoding="utf-8"))
            self.assertIn("distilled_with", one["versions"][0])

    def test_anyway_lets_a_degenerate_tree_through_and_records_the_reason(self):
        """★ 不硬拒：给了理由就放行，且理由必须落进输出（不许只在终端里）。"""
        from backfill_distilled_with import run
        with tempfile.TemporaryDirectory() as td:
            group = _build_tree(pathlib.Path(td) / "r", per_commit=6, total=6)
            out = run(group, apply_changes=True, anyway="迁移期一次性对齐，已写进 CHANGELOG")
            self.assertTrue(out["applied"])
            self.assertIn("anyway", out)

    def test_dry_run_always_reports_the_distribution(self):
        """★ 读 dry-run 的人正是要据此决定要不要写 —— 分布每次都得给。"""
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "backfill_distilled_with.py")],
                           capture_output=True, text=True)
        self.assertIn("归因分布", r.stdout)
        self.assertIn("不同的首次落盘提交", r.stdout)


if __name__ == "__main__":
    unittest.main(verbosity=2)
