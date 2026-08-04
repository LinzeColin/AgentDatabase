from __future__ import annotations

"""Schema-validated immutable history with atomic current/previous promotion."""

import hashlib, json, os, tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping
import jsonschema


class SnapshotStoreError(ValueError):
    pass


def _canonical(value: Mapping[str, Any]) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def _atomic(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def _time(snapshot: Mapping[str, Any]) -> datetime:
    return datetime.fromisoformat(str(snapshot["run"]["source_completed_at"]).replace("Z", "+00:00"))


# Re-reconciling the same source run is normal: the timer fires every fifteen
# minutes and the capture host may not have produced a newer run. What may never
# happen is the same run reporting a different conclusion. These keys move on
# every reconcile without changing any conclusion, so they are excluded from the
# comparison; everything else about the analysis is included.
_VOLATILE_KEYS = frozenset(
    {"generated_at", "evaluated_at", "reconciled_at", "observed_at", "last_observed_at", "captured_at"}
)
# The failure compound is a live incident ledger, not something the run derived
# from its events: recording any new incident changes it. Including it made the
# ledger growing look identical to a run rewriting its own history, which is the
# one thing this comparison exists to catch.
_LEDGER_KEYS = frozenset({"failure_compound"})
_CONCLUSION_KEYS = ("analysis", "visuals", "decision", "benchmarks")
_RUN_IDENTITY_KEYS = ("run_id", "trace_id", "source_state", "source_completed_at")


def _strip_volatile(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            key: _strip_volatile(child)
            for key, child in value.items()
            if key not in _VOLATILE_KEYS and key not in _LEDGER_KEYS
        }
    if isinstance(value, list):
        return [_strip_volatile(child) for child in value]
    return value


def _conclusion_parts(snapshot: Mapping[str, Any]) -> dict[str, str]:
    """Per-part digests, so a conflict can name what actually differs."""
    run = snapshot.get("run") or {}
    core: dict[str, Any] = {key: run.get(key) for key in _RUN_IDENTITY_KEYS}
    for key in _CONCLUSION_KEYS:
        core[key] = snapshot.get(key)
    return {
        key: hashlib.sha256(_canonical({key: _strip_volatile(value)})).hexdigest()
        for key, value in core.items()
    }


def _conclusion_fingerprint(snapshot: Mapping[str, Any]) -> str:
    """What this run concluded from its events, independent of when it was read."""
    return hashlib.sha256(_canonical(_conclusion_parts(snapshot))).hexdigest()


def _conclusion_diff(left: Mapping[str, Any], right: Mapping[str, Any]) -> str:
    """Name the differing parts, descending one level so the report is usable."""
    a, b = _conclusion_parts(left), _conclusion_parts(right)
    out: list[str] = []
    for key in sorted(key for key in a if a[key] != b.get(key)):
        one, two = left.get(key), right.get(key)
        if isinstance(one, Mapping) and isinstance(two, Mapping):
            children = sorted(
                child for child in set(one) | set(two)
                if _canonical({child: _strip_volatile(one.get(child))})
                != _canonical({child: _strip_volatile(two.get(child))})
            )
            out.extend(f"{key}.{child}" for child in children) if children else out.append(key)
        else:
            out.append(key)
    return ",".join(out) or "<none>"


def _identity(snapshot: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "run_id": snapshot["run"]["run_id"],
        "trace_id": snapshot["run"]["trace_id"],
        "release_id": snapshot["release"].get("release_id"),
        "deployment_revision": snapshot["release"].get("deployment_revision"),
    }


class LiveSnapshotStore:
    def __init__(self, root: Path, schema_path: Path):
        self.root = Path(root)
        self.schema = json.loads(Path(schema_path).read_text(encoding="utf-8"))
        self.validator = jsonschema.Draft202012Validator(self.schema, format_checker=jsonschema.FormatChecker())
        self.current = self.root / "current.json"
        self.previous = self.root / "previous.json"
        self.history = self.root / "history"

    def validate(self, snapshot: Mapping[str, Any]) -> None:
        errors = sorted(self.validator.iter_errors(snapshot), key=lambda error: list(error.path))
        if errors:
            raise SnapshotStoreError(errors[0].message)
        run = snapshot["run"]
        evidence = snapshot["truth"]["same_run_evidence"]

        def same_run(name: str) -> bool:
            row = evidence.get(name)
            if not isinstance(row, Mapping):
                return False
            return (
                row.get("state") == "PASS"
                and row.get("run_id") == run["run_id"]
                and row.get("trace_id") == run["trace_id"]
            )

        # Which side stored the event bytes is a fact about storage; that this
        # run hashed them against a declared digest is the fact that matters.
        # After the 2026-08-04 migration R2 is drained and honestly NOT_RUN.
        if not any(same_run(name) for name in ("canonical_source_readback", "r2_readback")):
            raise SnapshotStoreError("authority evidence mismatch: canonical_source_readback/r2_readback")
        for name in ("private_database_readback", "ovh_reconcile"):
            if not same_run(name):
                raise SnapshotStoreError(f"authority evidence mismatch: {name}")

    def read_current(self) -> dict[str, Any] | None:
        if not self.current.exists():
            return None
        value = json.loads(self.current.read_text(encoding="utf-8"))
        self.validate(value)
        return value

    def publish(self, snapshot: Mapping[str, Any]) -> dict[str, Any]:
        self.validate(snapshot)
        data = _canonical(snapshot)
        identity = _identity(snapshot)
        history = self.history / f"{identity['run_id']}.json"
        if history.exists():
            # The byte comparison this replaced made every re-reconcile of an
            # unchanged source run a conflict, so `current.json` stopped being
            # updated and the page served a snapshot that aged all day while
            # the reconcile reported PASS. The guarantee worth keeping is that a
            # run cannot silently change what it concluded.
            stored = json.loads(history.read_text(encoding="utf-8"))
            if _conclusion_fingerprint(stored) != _conclusion_fingerprint(snapshot):
                raise SnapshotStoreError(
                    f"immutable history conflict: {_conclusion_diff(stored, snapshot)}"
                )
        current = self.read_current()
        if current and _time(snapshot) < _time(current):
            raise SnapshotStoreError("time regression refused")
        if not history.exists():
            _atomic(history, data)
        digest = hashlib.sha256(data).hexdigest()
        if current and current["run"]["run_id"] == identity["run_id"]:
            if _conclusion_fingerprint(current) != _conclusion_fingerprint(snapshot):
                raise SnapshotStoreError(
                    f"same run changed after publication: {_conclusion_diff(current, snapshot)}"
                )
            if _canonical(current) == data:
                return {"state": "NO_CHANGE", **identity, "sha256": digest}
            # Same conclusions, newer reading: freshness, release identity and
            # which authority served the bytes all move without the run having
            # changed its mind. Refusing this is what froze the served page.
            _atomic(self.previous, _canonical(current))
            _atomic(self.current, data)
            return {"state": "REFRESHED", **identity, "sha256": digest, "previous_run_id": identity["run_id"]}
        if current:
            _atomic(self.previous, _canonical(current))
        _atomic(self.current, data)
        return {"state": "PUBLISHED", **identity, "sha256": digest, "previous_run_id": current["run"]["run_id"] if current else None}

    def recover_previous_if_current_invalid(self) -> dict[str, Any]:
        try:
            current = self.read_current()
            if current is not None:
                return {"state": "NO_ACTION", **_identity(current)}
        except Exception:
            pass
        if not self.previous.exists():
            raise SnapshotStoreError("no valid current and no previous snapshot")
        previous = json.loads(self.previous.read_text(encoding="utf-8"))
        self.validate(previous)
        _atomic(self.current, _canonical(previous))
        return {"state": "RECOVERED", **_identity(previous)}
