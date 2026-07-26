from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from .io import bind_files, canonical_json, load_json, sha256_bytes, utc_now, write_json

_DECISIONS = {"KEEP", "REVERT", "NO_CHANGE"}
_MEMORY_RELATIVE = Path("control/strategy-memory.json")


def _memory_path(workspace: Path) -> Path:
    return workspace.resolve() / _MEMORY_RELATIVE


def _event_payload(event: Dict[str, Any]) -> Dict[str, Any]:
    return {key: value for key, value in event.items() if key not in {"event_hash", "previous_event_hash"}}


def verify_strategy_memory(memory: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    events = memory.get("events")
    if not isinstance(events, list):
        return ["events must be a list"]
    previous = "GENESIS"
    for index, event in enumerate(events, 1):
        if not isinstance(event, dict):
            errors.append("event %d must be an object" % index)
            continue
        if event.get("sequence") != index:
            errors.append("event %d sequence mismatch" % index)
        if event.get("previous_event_hash") != previous:
            errors.append("event %d previous hash mismatch" % index)
        expected = sha256_bytes(previous.encode("utf-8") + canonical_json(_event_payload(event)))
        if event.get("event_hash") != expected:
            errors.append("event %d hash mismatch" % index)
        previous = str(event.get("event_hash", ""))
    if memory.get("head_event_hash", "GENESIS") != previous:
        errors.append("head_event_hash mismatch")
    return errors


def _load_or_initialize(workspace: Path) -> Dict[str, Any]:
    path = _memory_path(workspace)
    if path.is_file():
        memory = load_json(path)
        errors = verify_strategy_memory(memory)
        if errors:
            raise ValueError("strategy memory integrity failed: %s" % "; ".join(errors))
        return memory
    memory = {
        "schema_version": "1.0",
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "head_event_hash": "GENESIS",
        "events": [],
    }
    write_json(path, memory)
    return memory


def _validate_record(record: Dict[str, Any]) -> None:
    required = ("candidate_id", "scope", "mechanism", "decision", "evidence_paths")
    missing = [key for key in required if not record.get(key)]
    if missing:
        raise ValueError("strategy record missing: %s" % ", ".join(missing))
    if record.get("decision") not in _DECISIONS:
        raise ValueError("decision must be KEEP, REVERT or NO_CHANGE")
    ratio = record.get("change_ratio", 0.0)
    if isinstance(ratio, bool) or not isinstance(ratio, (int, float)) or ratio < 0:
        raise ValueError("change_ratio must be a non-negative number")
    if not isinstance(record.get("evidence_paths"), list):
        raise ValueError("evidence_paths must be a non-empty list")


def _recommend(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    if not events:
        return {
            "strategy_status": "START",
            "textual_learning_rate": "small",
            "recommended_mechanism": "highest-evidence-smallest-attributable-change",
            "suppressed_mechanisms": [],
            "oscillation_detected": False,
            "reason": "No prior accepted or rejected edit is recorded.",
        }
    recent = events[-8:]
    failures_by_mechanism: Dict[str, int] = {}
    for event in recent:
        if event["decision"] in {"REVERT", "NO_CHANGE"}:
            mechanism = str(event["mechanism"])
            failures_by_mechanism[mechanism] = failures_by_mechanism.get(mechanism, 0) + 1
    suppressed = sorted(key for key, count in failures_by_mechanism.items() if count >= 2)

    oscillation = False
    if len(recent) >= 4:
        scopes = [str(item["scope"]) for item in recent[-4:]]
        mechanisms = [str(item["mechanism"]) for item in recent[-4:]]
        oscillation = len(set(scopes)) == 1 and mechanisms[0] == mechanisms[2] and mechanisms[1] == mechanisms[3] and mechanisms[0] != mechanisms[1]

    no_progress = [item for item in recent[-3:] if item["decision"] in {"REVERT", "NO_CHANGE"}]
    if len(no_progress) == 3 and len({str(item["mechanism"]) for item in no_progress}) >= 2:
        return {
            "strategy_status": "SATURATED",
            "textual_learning_rate": "stop",
            "recommended_mechanism": "REHEAT_REQUIRED",
            "suppressed_mechanisms": suppressed,
            "oscillation_detected": oscillation,
            "reason": "Three recent bounded attempts across multiple mechanisms produced no retained improvement.",
        }

    last = recent[-1]
    if last["decision"] == "KEEP" and float(last.get("change_ratio", 0.0)) <= 0.20:
        recommended = str(last["mechanism"])
        rate = "small"
        reason = "The latest small attributable change was retained; continue only while marginal benefit remains measurable."
    elif last["decision"] == "REVERT":
        recommended = "alternative-mechanism-outside-rejected-buffer"
        rate = "smaller"
        reason = "The latest edit regressed or failed a gate; reduce edit magnitude and change mechanism family."
    else:
        recommended = "architecture-or-clean-slate-probe" if str(last["mechanism"]) not in suppressed else "new-mechanism-family"
        rate = "medium-probe"
        reason = "No measurable change was found; test a distinct bounded hypothesis rather than repeating the same wording edit."
    if oscillation:
        recommended = "freeze-scope-and-reframe-objective"
        rate = "stop-on-current-scope"
        reason = "Alternating mechanisms on one scope indicate oscillation; freeze the scope and reframe the objective or reheat research."
    return {
        "strategy_status": "CONTINUE",
        "textual_learning_rate": rate,
        "recommended_mechanism": recommended,
        "suppressed_mechanisms": suppressed,
        "oscillation_detected": oscillation,
        "reason": reason,
    }


def update_strategy_memory(workspace: Path, record_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    if not workspace.is_dir():
        raise ValueError("workspace must exist")
    record_path = record_path.resolve()
    if not record_path.is_file() or record_path.is_symlink():
        raise ValueError("record must be a regular file")
    record = load_json(record_path)
    if not isinstance(record, dict):
        raise ValueError("strategy record must be an object")
    _validate_record(record)
    memory = _load_or_initialize(workspace)
    evidence_bindings = bind_files(workspace, record["evidence_paths"], label="strategy evidence")
    sequence = len(memory["events"]) + 1
    previous = str(memory.get("head_event_hash", "GENESIS"))
    event: Dict[str, Any] = {
        "schema_version": "1.0",
        "event_id": "strategy-%s" % uuid.uuid4().hex[:16],
        "sequence": sequence,
        "recorded_at": utc_now(),
        "candidate_id": str(record["candidate_id"]),
        "scope": str(record["scope"]),
        "mechanism": str(record["mechanism"]),
        "decision": str(record["decision"]),
        "change_ratio": float(record.get("change_ratio", 0.0)),
        "metric_delta": record.get("metric_delta", {}),
        "failure_tags": sorted(set(str(item) for item in record.get("failure_tags", []))),
        "cost": record.get("cost", {}),
        "evidence_bindings": evidence_bindings,
        "unknowns": record.get("unknowns", []),
    }
    event["previous_event_hash"] = previous
    event["event_hash"] = sha256_bytes(previous.encode("utf-8") + canonical_json(_event_payload(event)))
    memory["events"].append(event)
    memory["head_event_hash"] = event["event_hash"]
    memory["updated_at"] = utc_now()
    memory["recommendation"] = _recommend(memory["events"])
    write_json(_memory_path(workspace), memory)
    return {
        "status": "PASS",
        "memory_path": str(_memory_path(workspace)),
        "event": event,
        "recommendation": memory["recommendation"],
    }


def inspect_strategy_memory(workspace: Path) -> Dict[str, Any]:
    path = _memory_path(workspace)
    if not path.is_file():
        return {
            "status": "NOT_INITIALIZED",
            "event_count": 0,
            "recommendation": _recommend([]),
            "memory_path": str(path),
        }
    memory = load_json(path)
    errors = verify_strategy_memory(memory)
    return {
        "status": "PASS" if not errors else "FAIL",
        "event_count": len(memory.get("events", [])),
        "head_event_hash": memory.get("head_event_hash"),
        "recommendation": _recommend(memory.get("events", [])) if not errors else None,
        "errors": errors,
        "rejected_edit_buffer": [
            {
                "scope": item.get("scope"),
                "mechanism": item.get("mechanism"),
                "decision": item.get("decision"),
                "failure_tags": item.get("failure_tags", []),
            }
            for item in memory.get("events", [])[-10:]
            if item.get("decision") in {"REVERT", "NO_CHANGE"}
        ],
        "memory_path": str(path),
    }
