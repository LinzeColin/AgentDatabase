from __future__ import annotations

import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from .io import load_json, utc_now, write_json

PHASES = {"research", "candidate_generation", "evaluation", "review", "packaging", "installation", "recovery", "other"}
EVIDENCE_STATES = {"MEASURED", "ESTIMATED", "UNKNOWN"}


def _number(value: Any, *, integer: bool = False) -> bool:
    if isinstance(value, bool):
        return False
    return isinstance(value, int) if integer else isinstance(value, (int, float))


def validate_invocation(record: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if not isinstance(record, dict):
        return ["invocation record must be an object"]
    for key in ("invocation_id", "phase", "provider", "model", "runtime", "adapter_version", "started_at", "finished_at"):
        if not isinstance(record.get(key), str) or not str(record.get(key)).strip():
            errors.append("invocation %s missing" % key)
    if record.get("phase") not in PHASES:
        errors.append("invalid invocation phase")
    latency = record.get("latency_ms")
    if not _number(latency) or float(latency) < 0:
        errors.append("latency_ms must be non-negative")
    human = record.get("human_minutes")
    if not _number(human) or float(human) < 0:
        errors.append("human_minutes must be non-negative")
    attempts = record.get("attempt_ids")
    if not isinstance(attempts, list) or not attempts or any(not isinstance(item, str) or not item for item in attempts):
        errors.append("attempt_ids must be a non-empty list")
    elif len(set(attempts)) != len(attempts):
        errors.append("attempt_ids must be unique")
    retries = record.get("retry_count")
    if not _number(retries, integer=True) or int(retries) < 0:
        errors.append("retry_count must be a non-negative integer")
    elif isinstance(attempts, list) and attempts and retries != len(attempts) - 1:
        errors.append("retry_count must equal len(attempt_ids)-1")

    usage_state = record.get("token_evidence_status")
    if usage_state not in EVIDENCE_STATES:
        errors.append("invalid token_evidence_status")
    token_usage = record.get("token_usage")
    if not isinstance(token_usage, dict):
        errors.append("token_usage must be an object")
    else:
        for key in ("input", "output", "cached", "reasoning"):
            value = token_usage.get(key)
            if usage_state == "UNKNOWN":
                if value is not None:
                    errors.append("UNKNOWN token usage must use null for %s, never zero" % key)
            elif value is not None and (not _number(value, integer=True) or int(value) < 0):
                errors.append("token_usage.%s must be null or a non-negative integer" % key)

    cost = record.get("monetary_cost")
    if not isinstance(cost, dict):
        errors.append("monetary_cost must be an object")
    else:
        state = cost.get("status")
        if state not in EVIDENCE_STATES:
            errors.append("invalid monetary cost status")
        amount = cost.get("amount")
        currency = cost.get("currency")
        if state == "UNKNOWN":
            if amount is not None:
                errors.append("UNKNOWN monetary cost must use null, never zero")
        elif not _number(amount) or float(amount) < 0:
            errors.append("known monetary cost must be non-negative")
        if amount is not None and (not isinstance(currency, str) or not currency):
            errors.append("currency required when monetary amount is known")
    return sorted(set(errors))


def _percentile(values: List[float], fraction: float) -> Optional[float]:
    if not values:
        return None
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * fraction
    lower = int(math.floor(index))
    upper = int(math.ceil(index))
    if lower == upper:
        return ordered[lower]
    weight = index - lower
    return ordered[lower] * (1.0 - weight) + ordered[upper] * weight


def _overall_evidence(states: Iterable[str]) -> str:
    values = list(states)
    if not values or all(item == "UNKNOWN" for item in values):
        return "UNKNOWN"
    if all(item == "MEASURED" for item in values):
        return "MEASURED"
    if all(item in {"MEASURED", "ESTIMATED"} for item in values) and any(item == "ESTIMATED" for item in values):
        return "ESTIMATED"
    return "PARTIAL"


def aggregate_invocations(records: List[Dict[str, Any]]) -> Dict[str, Any]:
    errors: List[str] = []
    ids = set()
    attempts = set()
    for index, record in enumerate(records, 1):
        errors.extend("record %d: %s" % (index, item) for item in validate_invocation(record))
        invocation_id = record.get("invocation_id")
        if invocation_id in ids:
            errors.append("duplicate invocation_id: %s" % invocation_id)
        ids.add(invocation_id)
        for attempt in record.get("attempt_ids", []) if isinstance(record.get("attempt_ids"), list) else []:
            if attempt in attempts:
                errors.append("attempt_id reused across invocations: %s" % attempt)
            attempts.add(attempt)
    if errors:
        return {"aggregation_status": "FAIL", "errors": sorted(set(errors))}

    latencies = [float(item["latency_ms"]) for item in records]
    human_minutes = sum(float(item["human_minutes"]) for item in records)
    token_states = [str(item["token_evidence_status"]) for item in records]
    cost_states = [str(item["monetary_cost"]["status"]) for item in records]
    unknown_token_invocations = sum(1 for item in records if item["token_evidence_status"] == "UNKNOWN")
    known_tokens = sum(
        sum(int(value or 0) for value in item["token_usage"].values())
        for item in records if item["token_evidence_status"] != "UNKNOWN"
    )
    currencies = {str(item["monetary_cost"].get("currency")) for item in records if item["monetary_cost"].get("amount") is not None}
    total_cost: Optional[float]
    currency: Optional[str]
    if len(currencies) > 1:
        return {"aggregation_status": "FAIL", "errors": ["cannot aggregate multiple currencies without a frozen conversion contract"]}
    currency = next(iter(currencies)) if currencies else None
    unknown_cost_invocations = sum(1 for item in records if item["monetary_cost"]["status"] == "UNKNOWN")
    known_cost = sum(
        float(item["monetary_cost"].get("amount") or 0.0)
        for item in records if item["monetary_cost"]["status"] != "UNKNOWN"
    )
    # A partial sum is not the total. Preserve the total as unknown whenever any
    # invocation lacks usage/cost evidence, while still exposing the measured subtotal.
    total_cost = None if unknown_cost_invocations else known_cost

    phases: Dict[str, Dict[str, Any]] = {}
    for phase in sorted({str(item["phase"]) for item in records}):
        subset = [item for item in records if item["phase"] == phase]
        phases[phase] = {
            "invocations": len(subset),
            "attempts": sum(len(item["attempt_ids"]) for item in subset),
            "latency_ms": sum(float(item["latency_ms"]) for item in subset),
            "human_minutes": sum(float(item["human_minutes"]) for item in subset),
        }
    return {
        "schema_version": "1.0",
        "aggregation_status": "PASS",
        "generated_at": utc_now(),
        "invocations": len(records),
        "attempts": sum(len(item["attempt_ids"]) for item in records),
        "retries": sum(int(item["retry_count"]) for item in records),
        "latency_ms": {"p50": _percentile(latencies, 0.50), "p95": _percentile(latencies, 0.95), "total": sum(latencies)},
        "human_minutes": human_minutes,
        "token_evidence_status": _overall_evidence(token_states),
        "total_tokens": None if unknown_token_invocations else known_tokens,
        "known_total_tokens": known_tokens,
        "unknown_token_invocations": unknown_token_invocations,
        "cost_evidence_status": _overall_evidence(cost_states),
        "total_monetary_cost": total_cost,
        "known_monetary_cost": known_cost,
        "unknown_cost_invocations": unknown_cost_invocations,
        "currency": currency,
        "phases": phases,
        "errors": [],
    }


def load_invocations(path: Path) -> List[Dict[str, Any]]:
    path = path.resolve()
    if path.suffix == ".jsonl":
        records = []
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                records.append(__import__("json").loads(line))
        return records
    value = load_json(path)
    if isinstance(value, list):
        return value
    if isinstance(value, dict) and isinstance(value.get("invocations"), list):
        return value["invocations"]
    raise ValueError("telemetry input must be a JSON list, {invocations:[...]}, or JSONL")


def aggregate_file(path: Path, output: Optional[Path] = None) -> Dict[str, Any]:
    result = aggregate_invocations(load_invocations(path))
    if output is not None:
        write_json(output.resolve(), result)
    return result
