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
        for name in ("r2_readback", "private_database_readback", "ovh_reconcile"):
            row = evidence[name]
            if row["state"] != "PASS" or row["run_id"] != run["run_id"] or row["trace_id"] != run["trace_id"]:
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
        if history.exists() and history.read_bytes() != data:
            raise SnapshotStoreError("immutable history conflict")
        current = self.read_current()
        if current and _time(snapshot) < _time(current):
            raise SnapshotStoreError("time regression refused")
        if not history.exists():
            _atomic(history, data)
        digest = hashlib.sha256(data).hexdigest()
        if current and current["run"]["run_id"] == identity["run_id"]:
            if _canonical(current) != data:
                raise SnapshotStoreError("same run changed after publication")
            return {"state": "NO_CHANGE", **identity, "sha256": digest}
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
