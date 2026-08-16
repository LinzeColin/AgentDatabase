#!/usr/bin/env python3
"""Compile route and dossier records into an executable host-agent contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from team_runtime_common import read_json, write_json


def _member_map(dossier: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {row["subject_slug"]: row for row in dossier.get("members", []) if row.get("subject_slug")}


def build_contract(route: dict[str, Any], dossier: dict[str, Any]) -> dict[str, Any]:
    if route.get("status") != "ready":
        raise ValueError("route plan is not ready")
    if dossier.get("status") != "ready":
        raise ValueError("dossier is not ready; real persona payload is mandatory")
    members = _member_map(dossier)
    routed = {row.get("subject_slug") for row in route.get("members", [])}
    if routed != set(members):
        raise ValueError("route and dossier persona sets differ")

    assignments: dict[str, list[str]] = {slug: [] for slug in members}
    for row in route.get("packet_assignments", []):
        slug = row.get("owner_subject_slug")
        if slug in assignments:
            assignments[slug].append(str(row.get("packet_id")))

    units: list[dict[str, Any]] = [
        {
            "unit_id": "CTRL-HYPOTHESIS",
            "role": "hypothesis-framer",
            "phase": 0,
            "inputs": ["user task", "task profile", "evidence-map packet"],
            "outputs": ["assumption ledger", "falsifiers", "change triggers"],
            "may_read_persona_outputs": False,
        }
    ]
    for position, expert in enumerate(route.get("members", []), start=1):
        slug = expert["subject_slug"]
        payload = members[slug]
        units.append({
            "unit_id": f"PERSONA-{position:03d}",
            "role": "persona-solver",
            "phase": 1,
            "subject_slug": slug,
            "canonical_name": expert.get("canonical_name"),
            "owned_work_packets": assignments.get(slug, []),
            "inputs": ["bounded task packet", "frozen assumptions", "minimal current facts", "persona capsules"],
            "capsules": payload.get("capsules", {}),
            "required_output": {
                "claim": "bounded conclusion",
                "claim_ids": "one or more own claim_ids for every persona-specific assertion",
                "evidence": "dated factual evidence kept separate from persona authority",
                "assumptions": "assumptions relied on",
                "failure_conditions": "conditions that invalidate the result",
                "artifact": "mergeable work product",
            },
            "cannot": ["review own work", "act as judge", "invent unsupported persona views"],
        })

    units.extend([
        {
            "unit_id": "CTRL-ADVERSARY",
            "role": "counterevidence-adversary",
            "phase": 2,
            "inputs": ["sealed persona artifacts", "evidence summaries", "frozen assumptions"],
            "outputs": ["counterevidence", "alternative explanations", "correlated-error risks"],
            "may_read_hidden_reasoning": False,
        },
        {
            "unit_id": "CTRL-REVIEW",
            "role": "independent-reviewer",
            "phase": 3,
            "inputs": ["sealed candidate", "counterevidence", "acceptance rubric"],
            "outputs": ["review findings", "unresolved defects", "artifact completeness"],
            "may_edit_candidate": False,
        },
        {
            "unit_id": "CTRL-JUDGE",
            "role": "decision-judge",
            "phase": 4,
            "inputs": ["candidate options", "evidence", "counterevidence", "review findings", "predeclared rubric"],
            "outputs": ["adjudicated decision", "rejected alternatives", "change triggers"],
            "decision_rule": "evidence and applicability, never majority vote",
        },
        {
            "unit_id": "CTRL-SYNTHESIS",
            "role": "synthesis-lead",
            "phase": 5,
            "inputs": ["judge record", "accepted artifacts", "user output contract"],
            "outputs": ["one coherent final delivery", "Team Delta Card", "remaining unknowns"],
            "may_overrule_judge": False,
        },
    ])

    return {
        "schema_version": "persona-team.execution-contract.v1",
        "status": "ready",
        "mode": route.get("mode"),
        "strategy": route.get("strategy"),
        "persona_expert_count": route.get("persona_expert_count"),
        "control_role_count": route.get("control_role_count"),
        "persona_count_excludes_controls": True,
        "solo_allowed": False,
        "execution_units": units,
        "documented_divergences": dossier.get("divergences", []),
        "stage_gates": [
            {"gate": "G0", "pass_when": "assumptions, falsifiers and evidence gaps are frozen"},
            {"gate": "G1", "pass_when": "each persona artifact is claim-linked and packet-complete"},
            {"gate": "G2", "pass_when": "counterevidence and correlated-error risks are attached"},
            {"gate": "G3", "pass_when": "independent review defects are resolved or visible"},
            {"gate": "G4", "pass_when": "judge chooses one result with change triggers"},
            {"gate": "G5", "pass_when": "one user-ready delivery and Delta Card exist"},
        ],
        "user_output_contract": {
            "show": ["conclusion and next action", "work completed", "material disagreements", "risk and unknowns", "Team Delta Card"],
            "hide_by_default": ["full role transcript", "raw routing scores", "all claim ids", "internal meeting minutes"],
        },
        "target_gates": {
            "overall_delta": 95,
            "user_experience": 95,
            "moe": 95,
            "routing": 95,
            "functionality": 95,
            "quality": 95,
            "minimum_any_dimension": 75,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Create the host execution contract for a routed persona team.")
    parser.add_argument("--route-plan", type=Path, required=True)
    parser.add_argument("--dossier", type=Path, required=True)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        contract = build_contract(read_json(args.route_plan), read_json(args.dossier))
    except ValueError as exc:
        print(json.dumps({"status": "blocked", "reason": str(exc)}, ensure_ascii=False))
        return 3
    if args.output:
        write_json(args.output, contract)
        print(json.dumps({"written": str(args.output), "status": "ready"}, ensure_ascii=False))
    else:
        print(json.dumps(contract, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
