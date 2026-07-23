"""Atomic public-safe queue; raw values are structurally impossible here."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Optional

from CodexSkills.registry.auto.tools.validate_auto import AutoContract, validate_auto_instance
from CodexSkills.governance.tools.canonical_json import canonicalize_object

from .core import (
    AutoRuntimeError,
    Clock,
    PROTOCOL,
    SCHEMA_PREFIX,
    atomic_write_bytes,
    canonical_with_digest,
    format_utc,
    new_uid,
    read_json,
)
from .privacy import validate_public_serialization


QUEUE_SCHEMA = SCHEMA_PREFIX + "public-queue-envelope:v2"


@dataclass(frozen=True)
class QueueResult:
    status: str
    envelope: Mapping[str, object]


class PublicSafeQueue:
    def __init__(
        self,
        root: Path,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
    ) -> None:
        self.root = root
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock

    def _artifact_digest(self, schema_id: str, artifact: Mapping[str, object]) -> str:
        pointer = self.contract.shared.self_digest_pointers.get(schema_id)
        if not pointer or pointer.count("/") != 1:
            raise AutoRuntimeError("QUEUE_ARTIFACT_SELF_POINTER_INVALID")
        field = pointer[1:]
        value = artifact.get(field)
        if not isinstance(value, str):
            raise AutoRuntimeError("QUEUE_ARTIFACT_DIGEST_MISSING")
        return value

    def enqueue(
        self,
        *,
        auto_transaction_uid: str,
        lane: str,
        artifact_schema_id: str,
        artifact_uid: str,
        artifact_repo_path: str,
        artifact: Mapping[str, object],
        entropy: Optional[bytes] = None,
    ) -> QueueResult:
        raw = canonicalize_object(artifact)
        validated = validate_public_serialization(
            raw,
            self.contract,
            artifact_schema_id,
            self.bundle_digest,
        )
        artifact_digest = self._artifact_digest(artifact_schema_id, validated)
        now = self.clock.now()
        envelope_uid = new_uid("env", now, entropy)
        envelope = canonical_with_digest(
            {
                "schema_version": QUEUE_SCHEMA,
                "protocol_revision": PROTOCOL,
                "bundle_digest": self.bundle_digest,
                "envelope_uid": envelope_uid,
                "auto_transaction_uid": auto_transaction_uid,
                "lane": lane,
                "artifact_schema_id": artifact_schema_id,
                "artifact_uid": artifact_uid,
                "artifact_digest": artifact_digest,
                "artifact_repo_path": artifact_repo_path,
                "queue_state": "READY",
                "sealed_at": format_utc(now),
                "retry_count": 0,
                "envelope_digest": "0" * 64,
            },
            "envelope_digest",
        )
        validate_auto_instance(
            self.contract,
            envelope,
            QUEUE_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )
        final = self.root / envelope_uid
        temporary = self.root / f".{envelope_uid}.tmp"
        if final.exists():
            observed = read_json(final / "envelope.json")
            if (
                observed.get("artifact_uid") == artifact_uid
                and observed.get("artifact_digest") == artifact_digest
            ):
                return QueueResult("IDEMPOTENT", observed)
            raise AutoRuntimeError("QUEUE_UID_DIGEST_CORRUPTION")
        try:
            temporary.mkdir(mode=0o700)
            atomic_write_bytes(temporary / "artifact.json", raw)
            atomic_write_bytes(temporary / "envelope.json", canonicalize_object(envelope))
            directory_fd = os.open(str(temporary), os.O_RDONLY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
            os.rename(str(temporary), str(final))
            parent_fd = os.open(str(self.root), os.O_RDONLY)
            try:
                os.fsync(parent_fd)
            finally:
                os.close(parent_fd)
        except FileExistsError:
            raise AutoRuntimeError("QUEUE_CONCURRENT_UID_COLLISION")
        except OSError as exc:
            raise AutoRuntimeError("QUEUE_ATOMIC_COMMIT_FAILED") from exc
        return QueueResult("ENQUEUED", envelope)

    def mark_settled(
        self,
        envelope_uid: str,
        *,
        remote_head: str,
        observed_artifact_digest: str,
        remote_readback_verified: bool,
    ) -> Mapping[str, object]:
        if not remote_readback_verified:
            raise AutoRuntimeError("QUEUE_SETTLEMENT_REMOTE_READBACK_REQUIRED")
        if not re.fullmatch(r"(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})", remote_head):
            raise AutoRuntimeError("QUEUE_SETTLEMENT_REMOTE_HEAD_INVALID")
        directory = self.root / envelope_uid
        try:
            info = os.lstat(str(directory))
        except OSError as exc:
            raise AutoRuntimeError("QUEUE_ENTRY_MISSING") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise AutoRuntimeError("QUEUE_ENTRY_NOT_REAL_DIRECTORY")
        envelope = dict(read_json(directory / "envelope.json"))
        if observed_artifact_digest != envelope["artifact_digest"]:
            raise AutoRuntimeError("QUEUE_SETTLEMENT_ARTIFACT_DIGEST_MISMATCH")
        envelope["queue_state"] = "SETTLED"
        envelope["retry_count"] = 0
        envelope["envelope_digest"] = "0" * 64
        envelope = canonical_with_digest(envelope, "envelope_digest")
        validate_auto_instance(
            self.contract,
            envelope,
            QUEUE_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )
        atomic_write_bytes(directory / "envelope.json", canonicalize_object(envelope))
        return envelope
