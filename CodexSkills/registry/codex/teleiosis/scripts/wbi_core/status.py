from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import load_json, utc_now, write_json

STATUS_VALUES = {
    "control_plane_status": {"PASS", "FAIL", "BLOCKED"},
    "benchmark_integrity_status": {"VALID", "INVALID", "INCOMPLETE", "BLOCKED"},
    "outcome_status": {"SUPPORTED", "NOT_PROVEN", "REGRESSED", "UNKNOWN"},
    "cost_evidence_status": {"MEASURED", "PARTIAL", "ESTIMATED", "UNKNOWN"},
    "independent_review_status": {"PASS", "BLOCKED", "UNAVAILABLE", "FAIL"},
    "engineering_release_status": {"INSTALLABLE", "NOT_INSTALLABLE"},
    "formal_promotion_status": {"PASS", "BLOCKED", "FAIL"},
    "current_environment_strength_status": {
        "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT", "NOT_PROVEN",
        "REGRESSED", "BLOCKED", "REHEAT_REQUIRED"
    },
}


class StatusSemanticError(ValueError):
    pass


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _non_negative_number(value: Any, *, integer: bool = False) -> bool:
    if isinstance(value, bool):
        return False
    if integer:
        return isinstance(value, int) and value >= 0
    return isinstance(value, (int, float)) and value >= 0


def _reasons(value: Any, label: str, errors: List[str]) -> None:
    if not isinstance(value, list) or not value or any(not isinstance(item, str) or not item.strip() for item in value):
        errors.append("%s reasons must be a non-empty list of strings" % label)


def _validate_cost_evidence(cost: Any, cost_status: Optional[str]) -> List[str]:
    errors: List[str] = []
    if not isinstance(cost, dict):
        return ["cost_evidence object missing"]

    required = (
        "total_tokens",
        "known_total_tokens",
        "unknown_token_invocations",
        "total_monetary_cost",
        "known_monetary_cost",
        "unknown_cost_invocations",
        "currency",
    )
    for key in required:
        if key not in cost:
            errors.append("cost_evidence.%s missing" % key)

    total_tokens = cost.get("total_tokens")
    known_tokens = cost.get("known_total_tokens")
    unknown_tokens = cost.get("unknown_token_invocations")
    total_cost = cost.get("total_monetary_cost")
    known_cost = cost.get("known_monetary_cost")
    unknown_cost = cost.get("unknown_cost_invocations")
    currency = cost.get("currency")

    if total_tokens is not None and not _non_negative_number(total_tokens, integer=True):
        errors.append("total_tokens must be null or a non-negative integer")
    if not _non_negative_number(known_tokens, integer=True):
        errors.append("known_total_tokens must be a non-negative integer")
    if not _non_negative_number(unknown_tokens, integer=True):
        errors.append("unknown_token_invocations must be a non-negative integer")
    if total_cost is not None and not _non_negative_number(total_cost):
        errors.append("total_monetary_cost must be null or non-negative")
    if not _non_negative_number(known_cost):
        errors.append("known_monetary_cost must be non-negative")
    if not _non_negative_number(unknown_cost, integer=True):
        errors.append("unknown_cost_invocations must be a non-negative integer")
    if currency is not None and (not isinstance(currency, str) or not currency.strip()):
        errors.append("currency must be null or a non-empty string")

    if isinstance(unknown_tokens, int) and unknown_tokens > 0 and total_tokens is not None:
        errors.append("unknown token invocations require total_tokens=null; a known subtotal is not the total")
    if isinstance(unknown_cost, int) and unknown_cost > 0 and total_cost is not None:
        errors.append("unknown cost invocations require total_monetary_cost=null; a known subtotal is not the total")
    if total_tokens is not None and isinstance(known_tokens, int) and total_tokens != known_tokens:
        errors.append("total_tokens must equal known_total_tokens when no token usage is unknown")
    if total_cost is not None and _non_negative_number(known_cost) and abs(float(total_cost) - float(known_cost)) > 1e-9:
        errors.append("total_monetary_cost must equal known_monetary_cost when no cost is unknown")
    if (_non_negative_number(known_cost) and float(known_cost) > 0) or total_cost is not None:
        if not isinstance(currency, str) or not currency.strip():
            errors.append("currency is required when any monetary amount is known")

    if cost_status == "UNKNOWN":
        if total_tokens is not None or total_cost is not None:
            errors.append("UNKNOWN cost evidence must use null totals, never zero or a fabricated value")
        if _non_negative_number(known_tokens, integer=True) and int(known_tokens) != 0:
            errors.append("UNKNOWN cost evidence cannot contain a known token subtotal; use PARTIAL")
        if _non_negative_number(known_cost) and float(known_cost) != 0.0:
            errors.append("UNKNOWN cost evidence cannot contain a known monetary subtotal; use PARTIAL")
    elif cost_status == "PARTIAL":
        token_unknown = isinstance(unknown_tokens, int) and unknown_tokens > 0
        cost_unknown = isinstance(unknown_cost, int) and unknown_cost > 0
        if not token_unknown and not cost_unknown:
            errors.append("PARTIAL cost evidence requires at least one unknown invocation count")
        if total_tokens is not None or total_cost is not None:
            errors.append("PARTIAL cost evidence must keep incomplete totals null")
    elif cost_status in {"MEASURED", "ESTIMATED"}:
        if unknown_tokens != 0 or unknown_cost != 0:
            errors.append("%s cost evidence cannot contain unknown invocation counts" % cost_status)
        if total_tokens is None or total_cost is None:
            errors.append("%s cost evidence requires non-null token and monetary totals" % cost_status)
        if cost_status == "ESTIMATED":
            methods = cost.get("estimation_methods")
            if not isinstance(methods, list) or not methods or any(not isinstance(item, str) or not item.strip() for item in methods):
                errors.append("ESTIMATED cost evidence requires non-empty estimation_methods")
    return errors


def validate_status_summary(value: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, dict):
        return ["status summary must be an object"]
    if value.get("schema_version") != "1.0":
        errors.append("status summary schema_version must be 1.0")
    identity = value.get("identity")
    if not isinstance(identity, dict):
        errors.append("status identity missing")
    else:
        for key in ("run_id", "candidate_id", "valid_as_of"):
            if not isinstance(identity.get(key), str) or not str(identity.get(key)).strip():
                errors.append("status identity.%s missing" % key)
        if not _is_hash(identity.get("candidate_tree_hash")):
            errors.append("status identity.candidate_tree_hash must be a lowercase 64-character SHA-256")
    domains = value.get("domains")
    if not isinstance(domains, dict):
        return errors + ["status domains missing"]
    for name, allowed in STATUS_VALUES.items():
        domain = domains.get(name)
        if not isinstance(domain, dict):
            errors.append("missing status domain: %s" % name)
            continue
        state = domain.get("value")
        if state not in allowed:
            errors.append("invalid %s: %s" % (name, state))
        _reasons(domain.get("reasons"), name, errors)
        evidence = domain.get("evidence")
        if not isinstance(evidence, list) or any(not isinstance(item, str) or not item.strip() for item in evidence):
            errors.append("%s evidence must be a list of non-empty strings" % name)

    def state(name: str) -> Optional[str]:
        item = domains.get(name)
        return str(item.get("value")) if isinstance(item, dict) and item.get("value") is not None else None

    formal = state("formal_promotion_status")
    if formal == "PASS":
        required = {
            "control_plane_status": "PASS",
            "benchmark_integrity_status": "VALID",
            "outcome_status": "SUPPORTED",
            "independent_review_status": "PASS",
            "engineering_release_status": "INSTALLABLE",
            "current_environment_strength_status": "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT",
        }
        for name, expected in required.items():
            if state(name) != expected:
                errors.append("formal promotion PASS requires %s=%s" % (name, expected))
        if state("cost_evidence_status") not in {"MEASURED", "ESTIMATED"}:
            errors.append("formal promotion PASS requires complete MEASURED or ESTIMATED cost evidence")
    if state("independent_review_status") in {"BLOCKED", "UNAVAILABLE"} and formal == "PASS":
        errors.append("unavailable or blocked independent review must block formal promotion")
    if state("benchmark_integrity_status") in {"INVALID", "INCOMPLETE", "BLOCKED"} and state("outcome_status") == "SUPPORTED":
        errors.append("outcome SUPPORTED requires benchmark integrity VALID")
    if state("outcome_status") == "REGRESSED" and formal != "FAIL":
        errors.append("outcome REGRESSED requires formal promotion FAIL")
    if state("engineering_release_status") == "NOT_INSTALLABLE" and formal == "PASS":
        errors.append("non-installable engineering release cannot formally promote")
    strength = state("current_environment_strength_status")
    if strength == "REGRESSED" and formal != "FAIL":
        errors.append("current environment strength REGRESSED requires formal promotion FAIL")
    if strength in {"NOT_PROVEN", "BLOCKED", "REHEAT_REQUIRED"} and formal == "PASS":
        errors.append("unproven, blocked or expired current environment strength must block formal promotion")

    errors.extend(_validate_cost_evidence(value.get("cost_evidence"), state("cost_evidence_status")))

    if "status" in value and value.get("status") in {"PASS", "FAIL"}:
        errors.append("ambiguous top-level PASS/FAIL is forbidden; use the evidence status domains")
    return sorted(set(errors))


def build_status_summary(
    run_id: str,
    candidate_id: str,
    candidate_tree_hash: str,
    valid_as_of: str,
    domains: Dict[str, str],
    reasons: Dict[str, List[str]],
    evidence: Optional[Dict[str, List[str]]] = None,
    cost_evidence: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    domain_payload: Dict[str, Any] = {}
    evidence = evidence or {}
    for name in STATUS_VALUES:
        domain_payload[name] = {
            "value": domains.get(name, "UNKNOWN" if name in {"outcome_status", "cost_evidence_status"} else "BLOCKED"),
            "reasons": reasons.get(name) or ["No reason supplied; fail-closed default applied"],
            "evidence": evidence.get(name, []),
        }
    value = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "identity": {
            "run_id": run_id,
            "candidate_id": candidate_id,
            "candidate_tree_hash": candidate_tree_hash,
            "valid_as_of": valid_as_of,
        },
        "domains": domain_payload,
        "cost_evidence": cost_evidence or {
            "total_tokens": None,
            "known_total_tokens": 0,
            "unknown_token_invocations": 0,
            "total_monetary_cost": None,
            "known_monetary_cost": 0.0,
            "unknown_cost_invocations": 0,
            "currency": None,
        },
    }
    errors = validate_status_summary(value)
    if errors:
        raise StatusSemanticError("; ".join(errors))
    return value


def validate_status_file(path: Path, output: Optional[Path] = None) -> Dict[str, Any]:
    value = load_json(path.resolve())
    errors = validate_status_summary(value)
    result = {"validation_status": "PASS" if not errors else "FAIL", "errors": errors, "summary": value}
    if output is not None:
        write_json(output.resolve(), result)
    return result
