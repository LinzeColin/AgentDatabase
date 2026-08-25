#!/usr/bin/env python3
"""Create a deterministic risk-driven acceptance plan from JSON inputs (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

SCHEMA_VERSION = "1.0"
DEPTHS = {"auto", "quick", "standard", "deep"}
SCOPES = {"developer_check", "release_candidate", "staged_release", "post_deploy"}
RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}

TRIGGER_WEIGHTS = {
    "database_migration": (3, "deep"),
    "authentication_or_authorization": (3, "deep"),
    "payment_or_billing": (4, "deep"),
    "secret_or_credential": (4, "deep"),
    "deployment_or_infrastructure": (3, "deep"),
    "ai_or_agent_behavior": (3, "deep"),
    "schema_or_contract": (3, "deep"),
    "message_or_external_side_effect": (3, "deep"),
}

DEFAULT_BUDGETS = {
    "quick": {"max_commands": 20, "max_elapsed_seconds": 900, "max_output_bytes": 25_000_000},
    "standard": {"max_commands": 60, "max_elapsed_seconds": 3600, "max_output_bytes": 100_000_000},
    "deep": {"max_commands": 150, "max_elapsed_seconds": 14_400, "max_output_bytes": 500_000_000},
}


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


def canonical_digest(value: Any) -> str:
    blob = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def get_nested(obj: dict[str, Any], *keys: str, default: Any = None) -> Any:
    value: Any = obj
    for key in keys:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]
    return value


def normalized_profile(request: dict[str, Any], capabilities: dict[str, Any], triggers: list[str]) -> tuple[str, list[str]]:
    requested = str(get_nested(request, "preferences", "profile", default=request.get("profile", "auto"))).strip() or "auto"
    if requested not in DEPTHS:
        raise ValueError(f"unsupported profile: {requested}")
    reasons: list[str] = []
    forced_deep = any(TRIGGER_WEIGHTS.get(trigger, (0, ""))[1] == "deep" for trigger in triggers)
    suggested = str(get_nested(capabilities, "risk", "suggested_profile", default="standard"))
    if requested == "auto":
        profile = "deep" if forced_deep else (suggested if suggested in {"quick", "standard", "deep"} else "standard")
        reasons.append(f"auto selected {profile} from discovered risk signals")
    else:
        profile = requested
        reasons.append(f"Owner requested {requested}")
        if forced_deep and requested != "deep":
            profile = "deep"
            reasons.append("non-waivable risk trigger escalated depth to deep")
    return profile, reasons


def score_risk(request: dict[str, Any], capabilities: dict[str, Any], triggers: list[str], decision_scope: str) -> tuple[str, int, list[str]]:
    score = 0
    reasons: list[str] = []
    for trigger in triggers:
        weight = TRIGGER_WEIGHTS.get(trigger, (2, "standard"))[0]
        score += weight
        reasons.append(f"{trigger}: +{weight}")
    if decision_scope in {"staged_release", "post_deploy"}:
        score += 3
        reasons.append(f"{decision_scope}: +3")
    elif decision_scope == "release_candidate":
        score += 2
        reasons.append("release_candidate: +2")

    allow_prod = bool(get_nested(request, "preferences", "allow_production_write", default=False))
    allow_external = bool(get_nested(request, "preferences", "allow_third_party_write", default=False))
    if allow_prod:
        score += 4
        reasons.append("production write authorization requested: +4")
    elif allow_external:
        score += 2
        reasons.append("third-party write authorization requested: +2")

    if score >= 12:
        level = "critical"
    elif score >= 7:
        level = "high"
    elif score >= 3:
        level = "medium"
    else:
        level = "low"
    if any(trigger in {"payment_or_billing", "secret_or_credential"} for trigger in triggers):
        level = "critical"
        reasons.append("critical direct trigger sets minimum risk=critical")
    elif any(trigger in TRIGGER_WEIGHTS for trigger in triggers) and RISK_ORDER[level] < RISK_ORDER["high"]:
        level = "high"
        reasons.append("non-waivable direct trigger sets minimum risk=high")
    return level, score, reasons


def select_dimensions(triggers: list[str], decision_scope: str) -> list[dict[str, Any]]:
    dimensions: dict[str, dict[str, Any]] = {
        "identity_and_contract": {"required": True, "reason": "all runs"},
        "build_start_health": {"required": True, "reason": "all executable software"},
        "focused_functional": {"required": True, "reason": "all runs"},
        "real_user_or_caller_outcome": {"required": True, "reason": "acceptance requires observable outcome/world state"},
        "changed_scope_regression": {"required": True, "reason": "change-impact traceability"},
        "test_discrimination": {"required": False, "reason": "enable for critical acceptance paths or weak tests"},
        "data_and_migration": {"required": "database_migration" in triggers, "reason": "migration/data trigger"},
        "api_schema_contract": {"required": "schema_or_contract" in triggers, "reason": "schema/contract trigger"},
        "security_and_privacy": {"required": any(t in triggers for t in ("authentication_or_authorization", "secret_or_credential", "payment_or_billing")), "reason": "permission/secret/payment trigger"},
        "external_side_effects": {"required": any(t in triggers for t in ("payment_or_billing", "message_or_external_side_effect")), "reason": "external action trigger"},
        "release_and_recovery": {"required": decision_scope != "developer_check" or "deployment_or_infrastructure" in triggers, "reason": "release scope or deployment trigger"},
        "ai_agent_evaluation": {"required": "ai_or_agent_behavior" in triggers, "reason": "AI/agent behavior trigger"},
        "evidence_privacy": {"required": True, "reason": "all evidence packages"},
        "six_lens_review": {"required": True, "reason": "decision challenge and blind-spot coverage"},
    }
    return [{"dimension": name, **value} for name, value in dimensions.items()]


def command_allowlist(request: dict[str, Any], capabilities: dict[str, Any]) -> list[dict[str, Any]]:
    commands = get_nested(capabilities, "project", "candidate_commands", default=[])
    if not isinstance(commands, list):
        commands = []
    owner_commands = get_nested(request, "command_policy", "allowed_argv", default=[])
    if not isinstance(owner_commands, list):
        owner_commands = []
    authorize_safe = bool(get_nested(request, "preferences", "allow_safe_local_setup", default=True))
    normalized: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()

    def append(argv_value: Any, source: str, authorized: bool, authorization_basis: str) -> None:
        if not isinstance(argv_value, list) or not argv_value or not all(isinstance(part, str) and part and "\x00" not in part for part in argv_value):
            return
        argv = list(argv_value)
        key = tuple(argv)
        if key in seen:
            return
        seen.add(key)
        normalized.append({
            "policy_id": f"CMD-POL-{len(normalized) + 1:03d}",
            "argv": argv,
            "source": source,
            "authorized": authorized,
            "authorization_basis": authorization_basis,
            "side_effect_class": "local_project_execution",
        })

    for item in commands:
        if isinstance(item, dict):
            append(item.get("argv"), str(item.get("source", "discovered")), authorize_safe, "preferences.allow_safe_local_setup")
    for argv in owner_commands:
        append(argv, "owner request command_policy.allowed_argv", True, "explicit owner allowlist")
    return normalized


def build_plan(request: dict[str, Any], capabilities: dict[str, Any]) -> dict[str, Any]:
    if capabilities.get("read_only") is not True:
        raise ValueError("capabilities report must declare read_only=true")
    signals = get_nested(capabilities, "risk", "signals", default=[])
    triggers = sorted({str(item.get("signal")) for item in signals if isinstance(item, dict) and item.get("signal")})
    decision_scope = str(get_nested(request, "preferences", "decision_scope", default=request.get("decision_scope", "release_candidate")))
    if decision_scope not in SCOPES:
        raise ValueError(f"unsupported decision_scope: {decision_scope}")
    profile, profile_reasons = normalized_profile(request, capabilities, triggers)
    risk_level, risk_score, risk_reasons = score_risk(request, capabilities, triggers, decision_scope)
    budget = dict(DEFAULT_BUDGETS[profile])

    request_budget = request.get("execution_budget")
    if isinstance(request_budget, dict):
        for key in budget:
            value = request_budget.get(key)
            if isinstance(value, int) and value > 0:
                budget[key] = min(value, budget[key])

    project_name = str(get_nested(request, "owner_input", "target_project", "name", default=request.get("target_project", "")))
    project_path = str(get_nested(capabilities, "repository", "target_project_path", default="."))
    expected_outcome = str(get_nested(request, "owner_input", "expected_outcome", default=request.get("expected_outcome", "")))

    hard_stops = [
        "subject identity or authorized taskpack/Oracle drifts",
        "target/command/network/data action leaves the allowlist",
        "secret or restricted data would enter ordinary evidence",
        "production health, business invariant, request, cost, concurrency or duration limit is exceeded",
        "unexpected destructive or external side effect occurs",
        "evidence integrity or environment comparability is lost",
    ]

    independence = {
        "minimum_review_roles": 6,
        "critical_positive_requires_distinct_verifier_contexts": risk_level == "critical",
        "same_model_same_context_roles_do_not_count_as_independent": True,
    }

    plan = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "inputs": {
            "request_sha256": canonical_digest(request),
            "capabilities_sha256": canonical_digest(capabilities),
        },
        "target": {
            "project_name": project_name,
            "project_path": project_path,
            "expected_outcome": expected_outcome,
            "single_project": True,
        },
        "decision_scope": decision_scope,
        "profile": {"selected": profile, "reasons": profile_reasons},
        "risk": {"level": risk_level, "score": risk_score, "triggers": triggers, "reasons": risk_reasons},
        "dimensions": select_dimensions(triggers, decision_scope),
        "execution_budget": {
            **budget,
            "max_network_requests": int(get_nested(request, "safety", "max_requests", default=0) or 0),
            "max_cost": get_nested(request, "safety", "max_cost", default=None),
            "budget_exhaustion_action": "STOP_AND_REPORT_PARTIAL",
        },
        "command_allowlist": command_allowlist(request, capabilities),
        "command_policy": {
            "allowed_working_directories": get_nested(request, "command_policy", "allowed_working_directories", default=[]),
            "allowed_network_targets": get_nested(request, "command_policy", "allowed_network_targets", default=[]),
            "forbidden_patterns": get_nested(request, "command_policy", "forbidden_patterns", default=[]),
            "budget_exhaustion_action": get_nested(request, "command_policy", "budget_exhaustion_action", default="STOP_AND_REPORT_PARTIAL"),
        },
        "authorization": {
            "network_read": bool(get_nested(request, "preferences", "allow_network_read", default=True)),
            "third_party_write": bool(get_nested(request, "preferences", "allow_third_party_write", default=False)),
            "production_write": bool(get_nested(request, "preferences", "allow_production_write", default=False)),
            "real_payment_email_sms": bool(get_nested(request, "preferences", "allow_real_payment_email_sms", default=False)),
            "load_test": bool(get_nested(request, "preferences", "load_test_authorized", default=False)),
            "active_security_scan": bool(get_nested(request, "preferences", "active_security_scan_authorized", default=False)),
            "fault_injection": bool(get_nested(request, "preferences", "fault_injection_authorized", default=False)),
            "destructive_data_test": bool(get_nested(request, "preferences", "destructive_data_test_authorized", default=False)),
        },
        "hard_stops": hard_stops,
        "independence": independence,
        "required_artifacts": [
            "CAPABILITY_REPORT.json",
            "ACCEPTANCE_PLAN.json",
            "RUN_MANIFEST.yaml",
            "TRACEABILITY_MATRIX.json",
            "TEST_MATRIX.md",
            "EVIDENCE_PRIVACY_REPORT.json",
            "REVIEW_PANEL.json",
            "VERDICT.md",
            "FINAL_DECISION.json",
            "ACCEPTANCE_ATTESTATION.intoto.json",
            "SHA256SUMS.txt",
        ],
        "unknowns": [],
    }

    if not project_name:
        plan["unknowns"].append({"id": "TARGET_PROJECT_NAME", "blocking": True, "question": "Which single project is the verdict for?"})
    if not expected_outcome:
        plan["unknowns"].append({"id": "EXPECTED_OUTCOME", "blocking": True, "question": "What observable user/caller outcome must be accepted?"})
    if get_nested(capabilities, "repository", "walk_truncated", default=False):
        plan["unknowns"].append({"id": "INVENTORY_TRUNCATED", "blocking": True, "question": "How will the unobserved project inventory be bounded?"})
    if get_nested(capabilities, "repository", "case_collisions", default=[]):
        plan["unknowns"].append({"id": "CASE_COLLISION", "blocking": True, "question": "Resolve portable path collisions before packaging."})
    return plan


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--request", required=True, type=Path)
    parser.add_argument("--capabilities", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        request = load_object(args.request, "request")
        capabilities = load_object(args.capabilities, "capabilities")
        plan = build_plan(request, capabilities)
    except ValueError as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    text = json.dumps(plan, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json or not args.output:
        print(text, end="")
    else:
        print(f"ACCEPTANCE_PLAN: {args.output.resolve()}")
        print(f"risk={plan['risk']['level']} profile={plan['profile']['selected']} unknowns={len(plan['unknowns'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
