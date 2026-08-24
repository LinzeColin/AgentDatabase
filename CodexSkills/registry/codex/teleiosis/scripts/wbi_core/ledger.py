from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .io import canonical_json, load_json, sha256_bytes, utc_now, write_json


def read_events(path: Path) -> tuple:
    """Return parsed events plus tamper-evidence errors without trusting state.json."""
    if not path.is_file():
        return [], ["event ledger missing"]
    events: List[Dict[str, Any]] = []
    errors: List[str] = []
    previous = "GENESIS"
    expected_sequence = 1
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = __import__("json").loads(line)
        except Exception as exc:
            errors.append("invalid event JSON at line %d: %s" % (line_number, exc))
            continue
        if not isinstance(event, dict):
            errors.append("event at line %d must be an object" % line_number)
            continue
        if event.get("sequence") != expected_sequence:
            errors.append("event sequence mismatch at line %d" % line_number)
        if event.get("prev_hash") != previous:
            errors.append("event previous hash mismatch at line %d" % line_number)
        supplied = event.get("event_hash")
        payload = dict(event)
        payload.pop("event_hash", None)
        calculated = sha256_bytes(canonical_json(payload))
        if supplied != calculated:
            errors.append("event hash mismatch at line %d" % line_number)
        previous = str(supplied)
        expected_sequence += 1
        events.append(event)
    if not events:
        errors.append("event ledger is empty")
    return events, errors


def verify_event_chain(path: Path) -> List[str]:
    return read_events(path)[1]


def append_event(path: Path, event: Dict[str, Any]) -> Dict[str, Any]:
    errors = verify_event_chain(path) if path.exists() else []
    if errors:
        raise ValueError("cannot append to a tampered ledger: %s" % errors)
    previous = "GENESIS"
    sequence = 1
    if path.exists():
        rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
        if rows:
            last = __import__("json").loads(rows[-1])
            previous = last["event_hash"]
            sequence = int(last["sequence"]) + 1
    payload = dict(event)
    payload.setdefault("timestamp", utc_now())
    payload["sequence"] = sequence
    payload["prev_hash"] = previous
    payload["event_hash"] = sha256_bytes(canonical_json(payload))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(__import__("json").dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
        handle.flush()
        __import__("os").fsync(handle.fileno())
    return payload
