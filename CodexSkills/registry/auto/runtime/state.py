"""Crash-safe private state, single-flight, and verified lane watermarks."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Mapping, Optional

from CodexSkills.registry.auto.tools.validate_auto import AutoContract, validate_auto_instance

from .core import (
    AutoRuntimeError,
    Clock,
    PROTOCOL,
    SCHEMA_PREFIX,
    atomic_write_json,
    canonical_with_digest,
    format_utc,
    new_uid,
    parse_utc,
    read_json,
)
from CodexSkills.governance.tools.canonical_json import canonicalize_object


LOCK_SCHEMA = SCHEMA_PREFIX + "lock-state:v1"
WATERMARK_SCHEMA = SCHEMA_PREFIX + "watermark:v2"
LANES = ("REGISTRY", "RUN_LOG")


def _mkdir_private(path: Path) -> None:
    try:
        path.mkdir(mode=0o700, parents=False, exist_ok=True)
        info = os.lstat(str(path))
    except OSError as exc:
        raise AutoRuntimeError("STATE_DIRECTORY_CREATE_FAILED") from exc
    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
        raise AutoRuntimeError("STATE_DIRECTORY_NOT_REAL")
    if stat.S_IMODE(info.st_mode) & 0o077:
        raise AutoRuntimeError("STATE_DIRECTORY_PERMISSIONS_TOO_BROAD")


@dataclass(frozen=True)
class StateLayout:
    root: Path
    locks: Path
    lock_history: Path
    watermarks: Path
    queue: Path
    outbox: Path
    staging: Path
    managed_raw: Path
    private: Path
    notification_private: Path

    @classmethod
    def create(cls, root: Path) -> "StateLayout":
        names = (
            "locks",
            "lock-history",
            "watermarks",
            "queue",
            "outbox",
            "staging",
            "managed-raw",
            "private",
        )
        for name in names:
            _mkdir_private(root / name)
        notification_private = root / "private" / "notification"
        _mkdir_private(notification_private)
        return cls(
            root,
            *(root / name for name in names),
            notification_private,
        )


class JSONStateStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def _path(self, relative: str) -> Path:
        parsed = PurePosixPath(relative)
        if parsed.is_absolute() or not parsed.parts or any(part in {"", ".", ".."} for part in parsed.parts):
            raise AutoRuntimeError("STATE_RELATIVE_PATH_INVALID")
        target = self.root.joinpath(*parsed.parts)
        if target.parent.resolve(strict=True) != target.parent:
            raise AutoRuntimeError("STATE_PATH_PARENT_REBOUND")
        return target

    def write(self, relative: str, value: Mapping[str, object], failpoint=None) -> None:
        atomic_write_json(self._path(relative), dict(value), failpoint=failpoint)

    def read(self, relative: str):
        return read_json(self._path(relative))


@dataclass(frozen=True)
class LockResult:
    status: str
    state: Optional[Mapping[str, object]]


class SingleFlightLock:
    """Directory claim lock; expired claims are never stolen implicitly."""

    def __init__(
        self,
        layout: StateLayout,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
    ) -> None:
        self.layout = layout
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock
        self.claim = layout.locks / "global-publisher.claim"
        self.state_path = self.claim / "state.json"

    def _validate(self, state: Mapping[str, object]) -> None:
        validate_auto_instance(
            self.contract,
            state,
            LOCK_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )

    def _read_existing(self) -> Mapping[str, object]:
        try:
            info = os.lstat(str(self.claim))
        except OSError as exc:
            raise AutoRuntimeError("LOCK_CLAIM_LSTAT_FAILED") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise AutoRuntimeError("LOCK_CLAIM_NOT_REAL_DIRECTORY")
        state = read_json(self.state_path)
        if not isinstance(state, dict):
            raise AutoRuntimeError("LOCK_STATE_ROOT_INVALID")
        self._validate(state)
        return state

    def acquire(
        self,
        owner_run_uid: str,
        *,
        lease_seconds: int = 120,
        generation: int = 1,
        entropy: Optional[bytes] = None,
    ) -> LockResult:
        now = self.clock.now()
        try:
            self.claim.mkdir(mode=0o700)
        except FileExistsError:
            try:
                state = self._read_existing()
            except AutoRuntimeError:
                return LockResult("CORRUPT_REQUIRES_RECONCILIATION", None)
            if state["status"] == "HELD" and parse_utc(str(state["lease_expires_at"])) <= now:
                return LockResult("STALE_REQUIRES_RECONCILIATION", state)
            return LockResult("BUSY", state)
        except OSError as exc:
            raise AutoRuntimeError("LOCK_CLAIM_CREATE_FAILED") from exc

        state = canonical_with_digest(
            {
                "schema_version": LOCK_SCHEMA,
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "lock_uid": new_uid("lck", now, entropy),
                "owner_run_uid": owner_run_uid,
                "generation": generation,
                "status": "HELD",
                "acquired_at": format_utc(now),
                "heartbeat_at": format_utc(now),
                "lease_expires_at": format_utc(now + dt.timedelta(seconds=lease_seconds)),
                "state_digest": "0" * 64,
            },
            "state_digest",
        )
        try:
            self._validate(state)
            atomic_write_json(self.state_path, state)
        except Exception:
            try:
                self.claim.rmdir()
            except OSError:
                pass
            raise
        return LockResult("ACQUIRED", state)

    def heartbeat(self, owner_run_uid: str, expected_digest: str, lease_seconds: int = 120) -> Mapping[str, object]:
        state = dict(self._read_existing())
        if state["owner_run_uid"] != owner_run_uid or state["state_digest"] != expected_digest:
            raise AutoRuntimeError("LOCK_OWNERSHIP_MISMATCH")
        if state["status"] != "HELD":
            raise AutoRuntimeError("LOCK_NOT_HELD")
        now = self.clock.now()
        state["heartbeat_at"] = format_utc(now)
        state["lease_expires_at"] = format_utc(now + dt.timedelta(seconds=lease_seconds))
        state = canonical_with_digest(state, "state_digest")
        self._validate(state)
        atomic_write_json(self.state_path, state)
        return state

    def assert_owned(
        self,
        owner_run_uid: str,
        expected_digest: str,
    ) -> Mapping[str, object]:
        """Prove a live exact lock claim without extending or mutating it."""

        state = self._read_existing()
        if (
            state["owner_run_uid"] != owner_run_uid
            or state["state_digest"] != expected_digest
        ):
            raise AutoRuntimeError("LOCK_OWNERSHIP_MISMATCH")
        if state["status"] != "HELD":
            raise AutoRuntimeError("LOCK_NOT_HELD")
        if parse_utc(str(state["lease_expires_at"])) <= self.clock.now():
            raise AutoRuntimeError("LOCK_LEASE_EXPIRED")
        return state

    def release(self, owner_run_uid: str, expected_digest: str) -> Mapping[str, object]:
        state = dict(self._read_existing())
        if state["owner_run_uid"] != owner_run_uid or state["state_digest"] != expected_digest:
            raise AutoRuntimeError("LOCK_OWNERSHIP_MISMATCH")
        now = self.clock.now()
        state["status"] = "RELEASED"
        state["released_at"] = format_utc(now)
        state["state_digest"] = "0" * 64
        state = canonical_with_digest(state, "state_digest")
        self._validate(state)
        atomic_write_json(self.state_path, state)
        destination = self.layout.lock_history / f"released-{state['lock_uid']}"
        try:
            os.rename(str(self.claim), str(destination))
        except OSError as exc:
            raise AutoRuntimeError("LOCK_RELEASE_ARCHIVE_FAILED") from exc
        return state

    def recover_stale(
        self,
        expected_digest: str,
        owner_probe: Callable[[str], bool],
    ) -> int:
        state = self._read_existing()
        if state["state_digest"] != expected_digest:
            raise AutoRuntimeError("LOCK_STALE_DIGEST_MISMATCH")
        if state["status"] != "HELD" or parse_utc(str(state["lease_expires_at"])) > self.clock.now():
            raise AutoRuntimeError("LOCK_NOT_STALE")
        if owner_probe(str(state["owner_run_uid"])):
            raise AutoRuntimeError("LOCK_OWNER_STILL_ACTIVE")
        destination = self.layout.lock_history / f"stale-{state['lock_uid']}"
        try:
            os.rename(str(self.claim), str(destination))
        except OSError as exc:
            raise AutoRuntimeError("LOCK_STALE_ARCHIVE_FAILED") from exc
        return int(state["generation"]) + 1

    def corrupt_claim_evidence(self) -> Mapping[str, object]:
        try:
            self._read_existing()
        except AutoRuntimeError:
            pass
        else:
            raise AutoRuntimeError("LOCK_CLAIM_NOT_CORRUPT")
        try:
            info = os.lstat(str(self.claim))
        except OSError as exc:
            raise AutoRuntimeError("LOCK_CLAIM_LSTAT_FAILED") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise AutoRuntimeError("LOCK_CLAIM_NOT_REAL_DIRECTORY")
        material = {
            "domain": "SKILLOPS_CORRUPT_LOCK_CLAIM_V1",
            "device": info.st_dev,
            "inode": info.st_ino,
            "modified_ns": info.st_mtime_ns,
        }
        return {
            "claim_fingerprint": hashlib.sha256(canonicalize_object(material)).hexdigest(),
            "age_seconds": max(0, int(self.clock.now().timestamp() - info.st_mtime)),
        }

    def recover_corrupt(
        self,
        expected_fingerprint: str,
        authorize: Callable[[Mapping[str, object]], bool],
        *,
        minimum_age_seconds: int = 120,
    ) -> None:
        evidence = self.corrupt_claim_evidence()
        if evidence["claim_fingerprint"] != expected_fingerprint:
            raise AutoRuntimeError("LOCK_CORRUPT_FINGERPRINT_MISMATCH")
        if evidence["age_seconds"] < minimum_age_seconds:
            raise AutoRuntimeError("LOCK_CORRUPT_RECOVERY_GRACE_REQUIRED")
        if not authorize(evidence):
            raise AutoRuntimeError("LOCK_CORRUPT_RECOVERY_NOT_AUTHORIZED")
        destination = self.layout.lock_history / (
            "corrupt-" + str(evidence["claim_fingerprint"])[:24]
        )
        try:
            os.rename(str(self.claim), str(destination))
        except OSError as exc:
            raise AutoRuntimeError("LOCK_CORRUPT_ARCHIVE_FAILED") from exc


@dataclass(frozen=True)
class RemoteSettlementEvidence:
    lane: str
    manifest_digest: str
    remote_head: str
    readback_verified: bool


class WatermarkStore:
    def __init__(
        self,
        path: Path,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
    ) -> None:
        self.path = path
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock

    def initialize(
        self,
        source_generations: Mapping[str, str],
        cursors: Mapping[str, str],
        *,
        entropy: Optional[bytes] = None,
    ) -> Mapping[str, object]:
        if self.path.exists():
            raise AutoRuntimeError("WATERMARK_ALREADY_EXISTS")
        now = self.clock.now()
        lanes = []
        for lane in LANES:
            lanes.append(
                {
                    "lane": lane,
                    "source_generation_uid": source_generations[lane],
                    "cursor_token": cursors[lane],
                    "public_watermark_ref": f"{lane.lower().replace('_', '-')}-initial",
                    "last_settled_manifest_digest": None,
                    "last_settled_remote_head": None,
                }
            )
        state = canonical_with_digest(
            {
                "schema_version": WATERMARK_SCHEMA,
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "watermark_uid": new_uid("wm", now, entropy),
                "updated_at": format_utc(now),
                "baseline_established": False,
                "lane_states": lanes,
                "state_digest": "0" * 64,
            },
            "state_digest",
        )
        self._validate(state)
        atomic_write_json(self.path, state)
        return state

    def _validate(self, state: Mapping[str, object]) -> None:
        validate_auto_instance(
            self.contract,
            state,
            WATERMARK_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )

    def read(self) -> Mapping[str, object]:
        state = read_json(self.path)
        if not isinstance(state, dict):
            raise AutoRuntimeError("WATERMARK_ROOT_INVALID")
        self._validate(state)
        return state

    def settle(self, evidence: RemoteSettlementEvidence, new_cursor: str) -> Mapping[str, object]:
        if evidence.lane not in LANES:
            raise AutoRuntimeError("WATERMARK_LANE_UNKNOWN")
        if not evidence.readback_verified:
            raise AutoRuntimeError("WATERMARK_REMOTE_READBACK_REQUIRED")
        state = dict(self.read())
        lane_states = [dict(item) for item in state["lane_states"]]
        selected = next(item for item in lane_states if item["lane"] == evidence.lane)
        selected["cursor_token"] = new_cursor
        selected["last_settled_manifest_digest"] = evidence.manifest_digest
        selected["last_settled_remote_head"] = evidence.remote_head
        state["lane_states"] = lane_states
        state["updated_at"] = format_utc(self.clock.now())
        state["state_digest"] = "0" * 64
        state = canonical_with_digest(state, "state_digest")
        self._validate(state)
        atomic_write_json(self.path, state)
        return state
