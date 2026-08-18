#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""卡片把「筛掉了几条贡献」说出来 —— 否则 `[]` 与「团队没有实质贡献」不可区分。

## 它守的那件事（2026-08-18 实测 @v0.0.0.45）

`build_team_delta_card.build_card` 里：

    material = [row for row in contributions
                if float(row.get("decision_influence", 0)) > 0 or row.get("artifact_owned")]

而 `decision_influence` / `artifact_owned` 在 **SKILL.md 与 references/*.md 里出现 0 次**
（`member_contributions` 本身写在 SKILL.md:200）。
⇒ **文档叫你填 A，代码按你没听说过的 B 来筛。**

实测：喂两条只有 `canonical_name` + `contribution` 的贡献 ⇒ **两条全被静默丢掉**
⇒ 卡片 `material_expert_contributions: []`。

★ **筛选规则一个字没改**（改它会改变卡片的判断）。改的是**把丢掉的说出来**：
  丢行时多一条 `material_expert_contributions_note`。静默 → 披露。
  [[empty-default-swallows-unknown]]｜[[the-comment-states-the-rule-the-code-narrows-it]]

★★ 这是同一形状的**第四处**：前三处（result 传错／delta-score 传错／六区段全缺）
  本文件都精心守住了；这一处「文档传对了但每行少字段」此前**没有守卫**。
"""
import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

ROUTE = {"mode": "small_team", "persona_expert_count": 9, "task_graph": {"mode_reasons": ["x"]}}
SCORE = {"dimensions": {"overall_delta": 1.0}, "benefit_deltas": {}, "efficiency_deltas": {},
         "status": "CANDIDATE_REJECTED_BELOW_FLOOR"}


def _result(rows):
    return {"work_completed": ["a"], "member_contributions": rows,
            "decision_changing_disagreements": [], "audit_trace": ["t"],
            "next_action": "n", "remaining_unknowns": []}


class DeltaCardDisclosesDroppedContributions(unittest.TestCase):

    def _card(self, rows):
        from build_team_delta_card import build_card
        return build_card(ROUTE, _result(rows), SCORE)

    def test_rows_missing_both_fields_are_disclosed(self):
        """★★★ 正是本件抓的那一幕：两条实打实的贡献被静默丢掉。"""
        card = self._card([{"canonical_name": "A", "contribution": "..."},
                           {"canonical_name": "B", "contribution": "..."}])
        self.assertEqual(card["material_expert_contributions"], [])
        note = card.get("material_expert_contributions_note")
        self.assertIsNotNone(note, "丢了 2 条却没有任何披露 ⇒ `[]` 会被读成「没有实质贡献」")
        self.assertIn("2 / 2", note)
        for field in ("decision_influence", "artifact_owned"):
            self.assertIn(field, note, "披露必须点名缺的是哪个字段，否则修不了")
        self.assertIn("A", note)
        self.assertIn("B", note)

    def test_rows_with_the_fields_are_kept_and_no_note(self):
        """★ 反对照：字段齐全时**不许**加噪声。"""
        card = self._card([{"canonical_name": "A", "decision_influence": 0.4},
                           {"canonical_name": "B", "artifact_owned": "plan.md"}])
        self.assertEqual(len(card["material_expert_contributions"]), 2)
        self.assertNotIn("material_expert_contributions_note", card)

    def test_partial_drop_is_disclosed_too(self):
        """★★ 只丢一部分也要说 —— 「筛掉一半」比「全筛掉」更容易被忽略。"""
        card = self._card([{"canonical_name": "A", "decision_influence": 0.4},
                           {"canonical_name": "B", "contribution": "..."}])
        self.assertEqual(len(card["material_expert_contributions"]), 1)
        self.assertIn("1 / 2", card.get("material_expert_contributions_note", ""))

    def test_no_contributions_at_all_adds_no_note(self):
        """★ 一条都没给 ⇒ 没什么可丢的，不加披露（否则每张卡都带一句废话）。"""
        card = self._card([])
        self.assertNotIn("material_expert_contributions_note", card)

    def test_the_two_fields_are_now_documented(self):
        """★★★ 本件的根因是「文档里 0 次」—— 补完之后要钉住它别再消失。"""
        skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
        for field in ("decision_influence", "artifact_owned"):
            self.assertIn(field, skill,
                          "`%s` 又从 SKILL.md 里消失了 ⇒ 宿主没法知道该填什么" % field)


if __name__ == "__main__":
    unittest.main(verbosity=2)
