"""UTC wall-clock retention restricted to explicitly owned managed data."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Mapping, Optional, Sequence, Tuple

from CodexSkills.auto.tools.validate_auto import (
    AutoContract,
    ContractError,
    validate_auto_instance,
)
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from .core import (
    AutoRuntimeError,
    Clock,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
    format_utc,
    new_uid,
    parse_utc,
    read_json,
    sha256_bytes,
)
from .roots import RootRegistry


RAW_SCHEMA = SCHEMA_PREFIX + "raw-segment:v2"
RETENTION_SCHEMA = SCHEMA_PREFIX + "retention-receipt:v2"
RETENTION_POLICY_ID = "urn:linzecolin:agentdatabase:skillops:policy:retention:v2"


@dataclass(frozen=True)
class RawCandidate:
    metadata_path: Path
    payload_path: Path
    metadata: Mapping[str, object]
    ttl_breach: bool
    offline_duration_seconds: int


@dataclass(frozen=True)
class RawExecution:
    action: str
    reprojection_status: str
    gap_code: Optional[str]
    affected_count: int
    affected_bytes: int


class RetentionExecutor:
    def __init__(
        self,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
        roots: RootRegistry,
    ) -> None:
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock
        self.roots = roots
        policy = contract.shared.policies.get(RETENTION_POLICY_ID)
        if not isinstance(policy, dict):
            raise AutoRuntimeError("RETENTION_POLICY_NOT_TRUSTED")
        if (
            policy.get("clock_basis") != "UTC_WALL_CLOCK"
            or policy.get("persistent_managed_raw_default_enabled") is not False
            or policy.get("protected_root_delete_allowed") is not False
            or policy.get("managed_raw_max_hours") != 72
        ):
            raise AutoRuntimeError("RETENTION_POLICY_CONTRACT_MISMATCH")
        self.policy = policy
        self.policy_digest = sha256_bytes(canonicalize_object(policy))

    def select_raw(
        self,
        metadata_paths: Sequence[Path],
        *,
        last_runtime_available_at: Optional[dt.datetime] = None,
        allow_test_only: bool = False,
    ) -> Tuple[RawCandidate, ...]:
        now = self.clock.now()
        candidates = []
        for metadata_path in metadata_paths:
            try:
                info = os.lstat(str(metadata_path))
            except OSError:
                continue
            if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                continue
            try:
                metadata = read_json(metadata_path)
                validate_auto_instance(
                    self.contract,
                    metadata,
                    RAW_SCHEMA,
                    expected_bundle_digest=self.bundle_digest,
                )
            except (AutoRuntimeError, ContractError):
                continue
            mode = metadata["persistence_mode"]
            if mode == "DISABLED":
                continue
            if mode == "TEST_ONLY" and not allow_test_only:
                continue
            if mode == "ENABLED_AFTER_CERTIFICATION":
                raise AutoRuntimeError("RAW_PERSISTENCE_NOT_CERTIFIED")
            expires = parse_utc(str(metadata["expires_at"]))
            if now < expires:
                continue
            payload_path = metadata_path.with_suffix(".payload")
            if metadata["ownership_marker_digest"] != raw_ownership_marker(metadata):
                raise AutoRuntimeError("RAW_OWNERSHIP_MARKER_INVALID")
            try:
                payload_info = os.lstat(str(payload_path))
                if stat.S_ISLNK(payload_info.st_mode) or not stat.S_ISREG(payload_info.st_mode):
                    raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
                if payload_info.st_size != metadata["byte_count"]:
                    raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
                payload_digest = _regular_file_digest(payload_path, payload_info)
            except AutoRuntimeError:
                raise
            except OSError as exc:
                raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID") from exc
            if payload_digest != metadata["payload_digest"]:
                raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
            offline_seconds = 0
            if last_runtime_available_at is not None:
                if (
                    last_runtime_available_at.tzinfo is None
                    or last_runtime_available_at.utcoffset() != dt.timedelta(0)
                ):
                    raise AutoRuntimeError("RETENTION_LAST_AVAILABLE_MUST_BE_UTC")
                offline_seconds = max(
                    0,
                    int((now - last_runtime_available_at.astimezone(dt.timezone.utc)).total_seconds()),
                )
            candidates.append(
                RawCandidate(
                    metadata_path,
                    payload_path,
                    metadata,
                    now > expires,
                    offline_seconds,
                )
            )
        return tuple(sorted(candidates, key=lambda item: str(item.metadata_path)))

    def execute_raw(
        self,
        candidate: RawCandidate,
        *,
        reproject: Callable[[RawCandidate], bool],
        record_gap: Callable[[RawCandidate, str], bool],
    ) -> RawExecution:
        self.roots.assert_mutation("DELETE", candidate.metadata_path)
        self.roots.assert_mutation("DELETE", candidate.payload_path)
        current_metadata = read_json(candidate.metadata_path)
        if (
            not isinstance(current_metadata, dict)
            or current_metadata.get("segment_digest")
            != candidate.metadata.get("segment_digest")
        ):
            raise AutoRuntimeError("RAW_CANDIDATE_CHANGED_BEFORE_DELETE")
        try:
            payload_info = os.lstat(str(candidate.payload_path))
            current_payload_digest = _regular_file_digest(candidate.payload_path, payload_info)
        except OSError as exc:
            raise AutoRuntimeError("RAW_CANDIDATE_CHANGED_BEFORE_DELETE") from exc
        if current_payload_digest != candidate.metadata["payload_digest"]:
            raise AutoRuntimeError("RAW_CANDIDATE_CHANGED_BEFORE_DELETE")
        if candidate.ttl_breach and not record_gap(candidate, "OFFLINE_TTL_BREACH"):
            raise AutoRuntimeError("OFFLINE_TTL_BREACH_RECEIPT_REQUIRED_BEFORE_DELETE")
        projected = reproject(candidate)
        gap_code = None
        if projected:
            reprojection_status = "SUCCEEDED"
        else:
            gap_code = "RAW_EXPIRED_UNPUBLISHED"
            if not record_gap(candidate, gap_code):
                raise AutoRuntimeError("RAW_GAP_RECEIPT_REQUIRED_BEFORE_DELETE")
            reprojection_status = "FAILED_GAP_RECORDED"
        affected_bytes = int(candidate.metadata.get("byte_count", 0))
        try:
            if candidate.payload_path.exists():
                candidate.payload_path.unlink()
            candidate.metadata_path.unlink()
            directory_fd = os.open(str(candidate.metadata_path.parent), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        except OSError as exc:
            raise AutoRuntimeError("RAW_OWNED_SEGMENT_DELETE_FAILED") from exc
        action = "OFFLINE_TTL_BREACH_CLEANUP" if candidate.ttl_breach else "DELETE_OWNED_SEGMENT"
        if candidate.ttl_breach:
            gap_code = "OFFLINE_TTL_BREACH"
        return RawExecution(action, reprojection_status, gap_code, 1, affected_bytes)

    @staticmethod
    def git_current_tree_eligible(now: dt.datetime, retention_not_before: dt.datetime) -> bool:
        return now.astimezone(dt.timezone.utc) > retention_not_before.astimezone(dt.timezone.utc)

    def build_receipt(
        self,
        *,
        auto_transaction_uid: str,
        scope: str,
        execution: RawExecution,
        selected_count: int,
        selected_bytes: int,
        cutoff_at: dt.datetime,
        protected_candidate_count: int = 0,
        legacy_candidate_count: int = 0,
        offline_duration_seconds: int = 0,
        evidence: Mapping[str, object],
        entropy: Optional[bytes] = None,
    ) -> Mapping[str, object]:
        now = self.clock.now()
        receipt = {
            "schema_version": RETENTION_SCHEMA,
            "protocol_revision": PROTOCOL,
            "bundle_digest": self.bundle_digest,
            "receipt_uid": new_uid("rtr", now, entropy),
            "retention_action_uid": new_uid("rta", now, entropy),
            "auto_transaction_uid": auto_transaction_uid,
            "executed_at": format_utc(now),
            "cutoff_at": format_utc(cutoff_at),
            "clock_basis": "UTC_WALL_CLOCK",
            "scope": scope,
            "action": execution.action,
            "retention_policy_id": RETENTION_POLICY_ID,
            "policy_snapshot_digest": self.policy_digest,
            "selected_count": selected_count,
            "selected_bytes": selected_bytes,
            "affected_count": execution.affected_count,
            "affected_bytes": execution.affected_bytes,
            "protected_candidate_count": protected_candidate_count,
            "legacy_candidate_count": legacy_candidate_count,
            "reprojection_status": execution.reprojection_status,
            "offline_duration_seconds": offline_duration_seconds,
            "ttl_breach": execution.action == "OFFLINE_TTL_BREACH_CLEANUP",
            "history_rewrite_performed": False,
            "hard_delete_claimed": False,
            "evidence_digest": sha256_bytes(canonicalize_object(evidence)),
            "receipt_digest": "0" * 64,
        }
        if execution.gap_code is not None:
            receipt["gap_code"] = execution.gap_code
        receipt = canonical_with_digest(receipt, "receipt_digest")
        validate_auto_instance(
            self.contract,
            receipt,
            RETENTION_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )
        return receipt


def raw_ownership_marker(metadata: Mapping[str, object]) -> str:
    return sha256_bytes(
        canonicalize_object(
            {
                "domain": "SKILLOPS_MANAGED_RAW_OWNERSHIP_V1",
                "segment_uid": metadata["segment_uid"],
                "source_generation_uid": metadata["source_generation_uid"],
                "payload_digest": metadata["payload_digest"],
                "created_at": metadata["created_at"],
                "managed_owned": metadata["managed_owned"],
                "protected_or_legacy": metadata["protected_or_legacy"],
            }
        )
    )


def _regular_file_digest(path: Path, expected: os.stat_result) -> str:
    if stat.S_ISLNK(expected.st_mode) or not stat.S_ISREG(expected.st_mode):
        raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
    descriptor = None
    digest = hashlib.sha256()
    try:
        descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        opened = os.fstat(descriptor)
        identity = lambda value: (
            value.st_dev,
            value.st_ino,
            value.st_mode,
            value.st_size,
            value.st_mtime_ns,
        )
        if identity(opened) != identity(expected):
            raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
        while True:
            block = os.read(descriptor, 1024 * 1024)
            if not block:
                break
            digest.update(block)
        if identity(os.lstat(str(path))) != identity(expected):
            raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID")
    except AutoRuntimeError:
        raise
    except OSError as exc:
        raise AutoRuntimeError("RAW_PAYLOAD_EVIDENCE_INVALID") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return digest.hexdigest()
