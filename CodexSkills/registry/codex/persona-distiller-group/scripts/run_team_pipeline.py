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
    parser.add_argument("--telemetry", type=Path, default=None,
                        help="defaults to <registry-root>/telemetry/team-outcomes.json "
                             "-- the same path record_team_outcome.py writes")
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
    # ★★★ 2026-08-18：收据**此前不带生成它的 skill 版本**。
    #   实测：一次真实运行产出的四份文件（route-plan / team-dossier /
    #   execution-contract / run-receipt）里，**没有一份**能回答「这是哪个版本跑的」
    #   （文中出现的 `v0.0.0.1` 是**人物交付包**的版本，不是本 skill 的）。
    #   而仓内产物是有的：`team-index.json:generator_version`、
    #   `expert-fleet-admission.json:source_generator_version`。
    #   ⇒ **仓内产物有出身，运行产物没有** —— 而运行产物才是宿主真去执行、
    #     用户出了问题会拿来对质的那一份。收据存在的全部意义就是「这次跑了什么」。
    #   [[evidence-must-carry-what-it-measured]]｜[[a-checkers-verdict-must-not-depend-on-cwd]]
    try:
        _gen = (root / "VERSION").read_text(encoding="utf-8").strip() or None
    except OSError:
        _gen = None
    receipt = {
        "schema_version": "persona-team.run-receipt.v1",
        # ★ 读不到就写 None，**不写 "unknown"** —— `unknown` 会让下游一致性比对恒等成立。
        "generator_version": _gen,
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
