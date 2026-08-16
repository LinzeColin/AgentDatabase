#!/usr/bin/env python3
"""Create the concise user-facing Team Delta Card."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from team_runtime_common import read_json, write_json


def build_card(route: dict[str, Any], result: dict[str, Any], score: dict[str, Any]) -> dict[str, Any]:
    contributions = result.get("member_contributions", [])
    material = [row for row in contributions if float(row.get("decision_influence", 0)) > 0 or row.get("artifact_owned")]
    return {
        "schema_version": "persona-team.delta-card.v1",
        "mode": route.get("mode"),
        "persona_expert_count": route.get("persona_expert_count"),
        "why_this_mode": route.get("task_graph", {}).get("mode_reasons", []),
        "work_completed": result.get("work_completed", []),
        "material_expert_contributions": material,
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
    card = build_card(read_json(args.route_plan), read_json(args.result), read_json(args.delta_score))
    write_json(args.output, card)
    print(json.dumps({"written": str(args.output), "target_status": card["target_status"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
