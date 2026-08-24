#!/usr/bin/env python3
"""Reconcile an executed command log with an authorized acceptance plan (stdlib only)."""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = "1.0"
SAFE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def load_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ValueError(f"{label} must be strict JSON: {error}") from error
    if not isinstance(value, dict):
        raise ValueError(f"{label} root must be an object")
    return value


def normalize_argv(value: Any, label: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not value:
        raise ValueError(f"{label} must be a non-empty argv array")
    normalized: list[str] = []
    for index, part in enumerate(value):
        if not isinstance(part, str) or not part or "\x00" in part:
            raise ValueError(f"{label}[{index}] must be a non-empty NUL-free string")
        normalized.append(part)
    return tuple(normalized)


def _non_negative_number(value: Any, label: str, errors: list[str]) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        errors.append(f"{label} must be a non-negative number")
        return 0.0
    return float(value)


def evaluate(plan: dict[str, Any], command_log: dict[str, Any], plan_path: str, log_path: str) -> dict[str, Any]:
    errors: list[str] = []
    allowlist = plan.get("command_allowlist")
    if not isinstance(allowlist, list):
        raise ValueError("plan.command_allowlist must be a list")
    policy = plan.get("command_policy") if isinstance(plan.get("command_policy"), dict) else {}
    forbidden = policy.get("forbidden_patterns", [])
    if not isinstance(forbidden, list) or not all(isinstance(item, str) and item for item in forbidden):
        raise ValueError("plan.command_policy.forbidden_patterns must be a string list")

    allowed_by_argv: dict[tuple[str, ...], dict[str, Any]] = {}
    authorized_count = 0
    for index, item in enumerate(allowlist):
        if not isinstance(item, dict):
            errors.append(f"plan.command_allowlist[{index}] must be an object")
            continue
        try:
            argv = normalize_argv(item.get("argv"), f"plan.command_allowlist[{index}].argv")
        except ValueError as error:
            errors.append(str(error))
            continue
        if argv in allowed_by_argv:
            errors.append(f"duplicate command allowlist argv: {list(argv)!r}")
            continue
        allowed_by_argv[argv] = item
        if item.get("authorized") is True:
            authorized_count += 1

    commands = command_log.get("commands")
    if not isinstance(commands, list):
        raise ValueError("COMMAND_LOG.commands must be a list")

    seen_ids: set[str] = set()
    unmatched: list[dict[str, Any]] = []
    forbidden_matches: list[dict[str, Any]] = []
    recorded: list[dict[str, Any]] = []
    total_elapsed = 0.0
    total_output = 0.0
    total_network = 0.0
    total_cost = 0.0

    for index, item in enumerate(commands):
        label = f"COMMAND_LOG.commands[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        command_id = item.get("id")
        if not isinstance(command_id, str) or not SAFE_ID_RE.fullmatch(command_id):
            errors.append(f"{label}.id is invalid")
            command_id = f"INVALID-{index}"
        elif command_id in seen_ids:
            errors.append(f"duplicate command id: {command_id}")
        seen_ids.add(str(command_id))
        try:
            argv = normalize_argv(item.get("argv"), f"{label}.argv")
        except ValueError as error:
            errors.append(str(error))
            continue
        matched = allowed_by_argv.get(argv)
        authorized = bool(matched and matched.get("authorized") is True)
        if not authorized:
            unmatched.append({"id": command_id, "argv": list(argv), "reason": "not on an authorized exact-argv allowlist"})
        joined = " ".join(argv)
        for pattern in forbidden:
            if pattern.casefold() in joined.casefold():
                forbidden_matches.append({"id": command_id, "argv": list(argv), "pattern": pattern})
        elapsed = _non_negative_number(item.get("elapsed_seconds", 0), f"{label}.elapsed_seconds", errors)
        output = _non_negative_number(item.get("output_bytes", 0), f"{label}.output_bytes", errors)
        network = _non_negative_number(item.get("network_requests", 0), f"{label}.network_requests", errors)
        cost = _non_negative_number(item.get("cost", 0), f"{label}.cost", errors)
        total_elapsed += elapsed
        total_output += output
        total_network += network
        total_cost += cost
        recorded.append({
            "id": command_id,
            "argv": list(argv),
            "matched_policy_id": matched.get("policy_id", "") if matched else "",
            "authorized": authorized,
            "returncode": item.get("returncode"),
            "elapsed_seconds": elapsed,
            "output_bytes": int(output),
            "network_requests": int(network),
            "cost": cost,
        })

    budget = plan.get("execution_budget")
    if not isinstance(budget, dict):
        raise ValueError("plan.execution_budget must be an object")
    exceeded: list[dict[str, Any]] = []
    checks = (
        ("max_commands", len(commands)),
        ("max_elapsed_seconds", total_elapsed),
        ("max_output_bytes", total_output),
        ("max_network_requests", total_network),
        ("max_cost", total_cost),
    )
    for key, actual in checks:
        limit = budget.get(key)
        if limit is None:
            continue
        if isinstance(limit, bool) or not isinstance(limit, (int, float)) or limit < 0:
            errors.append(f"plan.execution_budget.{key} must be null or a non-negative number")
            continue
        if actual > float(limit):
            exceeded.append({"metric": key, "limit": limit, "actual": actual})

    filesystem_issues = []
    for key in ("allowed_working_directories", "allowed_network_targets"):
        value = policy.get(key, [])
        if not isinstance(value, list):
            filesystem_issues.append(f"plan.command_policy.{key} must be a list")

    status = "PASS"
    if errors or unmatched or forbidden_matches or exceeded or filesystem_issues:
        status = "BLOCKED"
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "status": status,
        "plan_path": plan_path,
        "command_log_path": log_path,
        "authorized_command_count": authorized_count,
        "executed_command_count": len(commands),
        "unauthorized_execution_count": len(unmatched),
        "budget_exceeded": bool(exceeded),
        "unmatched_commands": unmatched,
        "forbidden_pattern_matches": forbidden_matches,
        "budget_exceeded_details": exceeded,
        "recorded_commands": recorded,
        "validation_errors": errors + filesystem_issues,
        "totals": {
            "elapsed_seconds": total_elapsed,
            "output_bytes": int(total_output),
            "network_requests": int(total_network),
            "cost": total_cost,
        },
        "evidence_paths": [log_path],
        "limitations": [
            "The report reconciles the supplied log; it cannot prove that uninstrumented commands were impossible.",
            "Use a sandbox/audit layer when complete process-level enforcement is required.",
        ],
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--command-log", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        plan = load_object(args.plan, "ACCEPTANCE_PLAN")
        log = load_object(args.command_log, "COMMAND_LOG")
        report = evaluate(plan, log, args.plan.name, args.command_log.name)
    except ValueError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json or not args.output:
        print(text, end="")
    else:
        print(f"COMMAND_POLICY_REPORT: {args.output.resolve()} status={report['status']} executed={report['executed_command_count']}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
