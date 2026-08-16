#!/usr/bin/env python3
"""Prepare a complete expert-team run directory from one user task."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from audit_persona_fleet_for_team import build_admission
from build_execution_contract import build_contract
from build_team_dossier import build_dossier, route_persona_slugs
from route_team_moe import build_route
from team_runtime_common import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Compile, route, load dossier and emit an execution contract.")
    parser.add_argument("--task", required=True)
    parser.add_argument("--mode", choices=["auto", "single_expert", "small_team", "deep_team", "swarm"], default="auto")
    parser.add_argument("--size", type=int)
    parser.add_argument("--strategy", choices=["auto", "c", "b", "a"], default="auto")
    parser.add_argument("--registry-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--telemetry", type=Path)
    parser.add_argument("--refresh-admission", action="store_true")
    parser.add_argument("--require-artifacts", action="store_true")
    parser.add_argument("--workdir", type=Path, required=True)
    args = parser.parse_args()

    root = args.registry_root.resolve()
    workdir = args.workdir.resolve()
    workdir.mkdir(parents=True, exist_ok=True)

    if args.refresh_admission or not (root / "expert-fleet-admission.json").is_file():
        admission = build_admission(root, args.require_artifacts)
        write_json(root / "expert-fleet-admission.json", admission)
        write_json(workdir / "fleet-admission.json", admission)

    route = build_route(args.task, root, args.mode, args.size, args.strategy, args.telemetry)
    write_json(workdir / "route-plan.json", route)
    if route.get("status") != "ready":
        write_json(workdir / "run-receipt.json", {"status": "blocked", "stage": "routing", "route_status": route.get("status")})
        print(json.dumps({"status": "blocked", "stage": "routing", "workdir": str(workdir)}, ensure_ascii=False))
        return 3

    dossier = build_dossier(root, route_persona_slugs(route), route)
    write_json(workdir / "team-dossier.json", dossier)
    if dossier.get("status") != "ready":
        write_json(workdir / "run-receipt.json", {"status": "blocked", "stage": "dossier", "missing": dossier.get("missing", [])})
        print(json.dumps({"status": "blocked", "stage": "dossier", "workdir": str(workdir)}, ensure_ascii=False))
        return 4

    contract = build_contract(route, dossier)
    write_json(workdir / "execution-contract.json", contract)
    receipt = {
        "schema_version": "persona-team.run-receipt.v1",
        "status": "prepared_for_host_execution",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "task": args.task,
        "mode": route.get("mode"),
        "strategy": route.get("strategy"),
        "persona_expert_count": route.get("persona_expert_count"),
        "control_role_count": route.get("control_role_count"),
        "files": ["route-plan.json", "team-dossier.json", "execution-contract.json"],
        "next_action": "Host agent executes the contract phases and writes result + Team Delta Card.",
    }
    write_json(workdir / "run-receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "workdir": str(workdir), "mode": receipt["mode"], "persona_experts": receipt["persona_expert_count"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
