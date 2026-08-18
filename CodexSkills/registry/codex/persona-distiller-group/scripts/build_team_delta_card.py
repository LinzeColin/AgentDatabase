#!/usr/bin/env python3
"""Create the concise user-facing Team Delta Card."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from team_runtime_common import read_json, write_json


# 运行叙述文档该有的区段。**用途是「一个都没有就拒答」，不是逐条必填。**
_NARRATIVE_SECTIONS = ("work_completed", "member_contributions",
                       "decision_changing_disagreements", "audit_trace",
                       "next_action", "remaining_unknowns")


def build_card(route: dict[str, Any], result: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    # ★★ **兄弟链上的同一个洞，而且更糟。** 2026-08-17 先在 score_team_delta 修了
    #   「错文档也给分」，按「并列的兄弟链有同样的洞」回头查这一条：
    #   把**判分输入**喂给本函数，它 **rc=0 照样写出一张卡** ——
    #   audit_trace / next_action / persona_expert_count 全是 null，
    #   material_expert_contributions 空，却带着一句像模像样的
    #   `CANDIDATE_REJECTED_BELOW_FLOOR`。**这正是用户看到的那张卡**，
    #   而 rc=0 意味着流水线会若无其事地继续。
    #   [[empty-default-swallows-unknown]]｜[[fixed-the-symptom-kept-the-root-cause]]
    #   ★ 只在**六个区段一个都没有**时拒答 —— 放宽只放在开脱侧，
    #     部分填写的合法叙述一个都不会被误伤。
    if not any(k in result for k in _NARRATIVE_SECTIONS):
        raise ValueError(
            "result 文档里 %s 六个区段一个都没有 —— 这看起来是给 score_team_delta 的"
            "判分输入（absolute/candidate/baseline/paired），不是运行叙述。"
            "两个脚本的参数都叫 --result 但要的是不同文档："
            "build_team_delta_card 要 team-result.json，score_team_delta 要 result-input.json。"
            "**不产卡片** —— 全 null 的卡片会冒充一次真实交付。"
            % "/".join(_NARRATIVE_SECTIONS))
    # ★ 同一形状的第三处：`--delta-score` 传错时它 **rc=0 照样出卡**。
    #   判分产物该有 dimensions/benefit_deltas/efficiency_deltas/status，一个都没有
    #   就不是判分产物。同样只在**全缺**时开火。
    if not any(k in score for k in ("dimensions", "benefit_deltas",
                                    "efficiency_deltas", "status")):
        raise ValueError(
            "delta-score 文档里 dimensions/benefit_deltas/efficiency_deltas/status "
            "一个都没有 —— 这不是 score_team_delta 的产物。**不产卡片**："
            "分数区全空的卡片会把「没测过」显示成「测了但很差」。")
    # ★★★ 2026-08-18：**同一形状的第四处，而它此前没有守卫** ——
    #   前三处守的都是「文档传错了」；这一处是「文档传对了，但每行少了两个
    #   **SKILL.md 从没提过**的字段」。实测：`member_contributions` 给两条实打实的贡献
    #   （只有 canonical_name + contribution）⇒ 两条**全部被静默丢掉**
    #   ⇒ 卡片上 `material_expert_contributions: []`，与「这支队伍没做出实质贡献」
    #   **一模一样**。而 `decision_influence` / `artifact_owned` 在 SKILL.md 与
    #   references/*.md 里出现 **0 次**（`member_contributions` 本身写在 SKILL.md:200）。
    #   ⇒ 文档叫你填 A，代码按你没听说过的 B 来筛。**不改筛选规则**（那会改变卡片的判断），
    #      改成**把丢掉的说出来**：静默 → 披露。
    #   [[empty-default-swallows-unknown]]｜[[the-comment-states-the-rule-the-code-narrows-it]]
    contributions = result.get("member_contributions", [])
    material = [row for row in contributions if float(row.get("decision_influence", 0)) > 0 or row.get("artifact_owned")]
    dropped = [row for row in contributions if row not in material]
    dropped_note = None
    if dropped:
        dropped_note = (
            "**%d / %d 条 `member_contributions` 未计入**：每行需要 "
            "`decision_influence > 0` 或 `artifact_owned`，这两个字段这些行都没有。"
            "⇒ 上面的 `material_expert_contributions` **不能读成「团队没有实质贡献」**。"
            "被丢掉的：%s"
            % (len(dropped), len(contributions),
               "、".join(str(r.get("canonical_name") or "?") for r in dropped[:6])))
    return {
        "schema_version": "persona-team.delta-card.v1",
        "mode": route.get("mode"),
        "persona_expert_count": route.get("persona_expert_count"),
        "why_this_mode": route.get("task_graph", {}).get("mode_reasons", []),
        "work_completed": result.get("work_completed", []),
        "material_expert_contributions": material,
        # ★ 只有真丢了行才出现这个键 —— 没丢时不加噪声。
        **({"material_expert_contributions_note": dropped_note} if dropped_note else {}),
        "decision_changing_disagreements": result.get("decision_changing_disagreements", []),
        "relative_to_baseline": {
            "overall_delta": score.get("dimensions", {}).get("overall_delta"),
            "benefit_deltas": score.get("benefit_deltas", {}),
            "efficiency_deltas": score.get("efficiency_deltas", {}),
        },
        "target_status": score.get("status"),
        "remaining_unknowns": result.get("remaining_unknowns", []),
        "next_action": result.get("next_action"),
        "audit_trace": result.get("audit_trace"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a user-facing Team Delta Card.")
    parser.add_argument("--route-plan", type=Path, required=True)
    parser.add_argument("--result", type=Path, required=True)
    parser.add_argument("--delta-score", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        card = build_card(read_json(args.route_plan), read_json(args.result),
                          read_json(args.delta_score))
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 2
    write_json(args.output, card)
    print(json.dumps({"written": str(args.output), "target_status": card["target_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
