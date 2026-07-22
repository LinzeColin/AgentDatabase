"""Transactional notification outbox with repo-external recipient mapping."""

from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable, Dict, Mapping, Optional

from CodexSkills.auto.tools.validate_auto import AutoContract, validate_auto_instance
from CodexSkills.governance.tools.canonical_json import canonicalize_object, parse_json_bytes
from CodexSkills.governance.tools.validate_mechanism import scan_public_value

from .core import (
    AutoRuntimeError,
    Clock,
    PROTOCOL,
    SCHEMA_PREFIX,
    atomic_write_json,
    canonical_with_digest,
    format_utc,
    new_uid,
    read_json,
    sha256_bytes,
)


NOTIFICATION_SCHEMA = SCHEMA_PREFIX + "notification-receipt:v3"
NOTIFICATION_POLICY_ID = "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
EMAIL_RE = re.compile(r"^[^@\s]{1,64}@[^@\s]{1,190}$")


@dataclass(frozen=True)
class RecipientMapping:
    recipient_ref: str
    provider_target: str

    @classmethod
    def load(cls, path: Path, recipient_ref: str) -> "RecipientMapping":
        try:
            info = os.lstat(str(path))
        except OSError as exc:
            raise AutoRuntimeError("RECIPIENT_MAPPING_UNAVAILABLE") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AutoRuntimeError("RECIPIENT_MAPPING_NOT_PRIVATE_FILE")
        if stat.S_IMODE(info.st_mode) & 0o077:
            raise AutoRuntimeError("RECIPIENT_MAPPING_PERMISSIONS_TOO_BROAD")
        try:
            document = parse_json_bytes(path.read_bytes())
        except Exception as exc:
            raise AutoRuntimeError("RECIPIENT_MAPPING_INVALID") from exc
        if not isinstance(document, dict) or set(document) != {"schema_version", "mappings"}:
            raise AutoRuntimeError("RECIPIENT_MAPPING_SHAPE_INVALID")
        if document["schema_version"] != "skillops.private-recipient-mapping.v1":
            raise AutoRuntimeError("RECIPIENT_MAPPING_VERSION_INVALID")
        rows = document["mappings"]
        if not isinstance(rows, list):
            raise AutoRuntimeError("RECIPIENT_MAPPING_ROWS_INVALID")
        selected = []
        for row in rows:
            if not isinstance(row, dict) or set(row) != {"recipient_ref", "provider_target"}:
                raise AutoRuntimeError("RECIPIENT_MAPPING_ROW_INVALID")
            if row["recipient_ref"] == recipient_ref:
                selected.append(row)
        if len(selected) != 1:
            raise AutoRuntimeError("RECIPIENT_MAPPING_NOT_UNIQUE")
        target = selected[0]["provider_target"]
        if not isinstance(target, str) or not EMAIL_RE.fullmatch(target):
            raise AutoRuntimeError("RECIPIENT_PROVIDER_TARGET_INVALID")
        return cls(recipient_ref, target)


@dataclass(frozen=True)
class ProviderResult:
    status: str
    provider_receipt_ref: Optional[str] = None
    failure_code: Optional[str] = None


class NotificationTransport:
    """Provider interface; credentials and targets never enter public receipts."""

    def lookup(self, idempotency_key: str) -> ProviderResult:
        raise NotImplementedError

    def send(
        self,
        *,
        idempotency_key: str,
        provider_target: str,
        subject: str,
        body: str,
    ) -> ProviderResult:
        raise NotImplementedError


class FakeNotificationTransport(NotificationTransport):
    def __init__(self, fail_code: Optional[str] = None) -> None:
        self.fail_code = fail_code
        self.sent: Dict[str, ProviderResult] = {}
        self.send_count = 0

    def lookup(self, idempotency_key: str) -> ProviderResult:
        return self.sent.get(idempotency_key, ProviderResult("UNKNOWN", failure_code="RECEIPT_UNVERIFIED"))

    def send(
        self,
        *,
        idempotency_key: str,
        provider_target: str,
        subject: str,
        body: str,
    ) -> ProviderResult:
        self.send_count += 1
        existing = self.sent.get(idempotency_key)
        if existing is not None:
            return existing
        if self.fail_code is not None:
            return ProviderResult("FAILED", failure_code=self.fail_code)
        receipt_ref = "msg-" + hashlib.sha256(idempotency_key.encode("ascii")).hexdigest()[:24]
        result = ProviderResult("SENT", provider_receipt_ref=receipt_ref)
        self.sent[idempotency_key] = result
        return result


@dataclass(frozen=True)
class NotificationOutcome:
    receipt: Mapping[str, object]
    planned_write_allowed: bool


class TransactionalNotifier:
    def __init__(
        self,
        outbox_root: Path,
        contract: AutoContract,
        bundle_digest: str,
        clock: Clock,
        transport: NotificationTransport,
    ) -> None:
        self.outbox_root = outbox_root
        self.contract = contract
        self.bundle_digest = bundle_digest
        self.clock = clock
        self.transport = transport
        policy = contract.shared.policies.get(NOTIFICATION_POLICY_ID)
        if not isinstance(policy, dict):
            raise AutoRuntimeError("NOTIFICATION_POLICY_NOT_TRUSTED")
        if (
            policy.get("automatic") is not True
            or policy.get("owner_approval_required") is not False
            or policy.get("owner_reply_required") is not False
            or policy.get("actual_recipient_mapping_repo_external") is not True
        ):
            raise AutoRuntimeError("NOTIFICATION_POLICY_CONTRACT_MISMATCH")
        self.policy = policy
        self.policy_digest = sha256_bytes(canonicalize_object(policy))

    def _validate_public_metadata(self, value: Mapping[str, object]) -> None:
        allowed = {
            "impact",
            "change_code",
            "planned_action",
            "affected_path_refs",
            "evidence_digests",
            "rollback_target_ref",
        }
        if not {"impact", "change_code", "planned_action", "affected_path_refs", "evidence_digests"}.issubset(value):
            raise AutoRuntimeError("NOTIFICATION_PUBLIC_METADATA_REQUIRED_FIELD_MISSING")
        if set(value).difference(allowed):
            raise AutoRuntimeError("NOTIFICATION_PUBLIC_METADATA_FIELD_FORBIDDEN")
        version_policy = self.contract.shared.policies.get(
            "urn:linzecolin:agentdatabase:skillops:policy:version:v2"
        )
        if (
            value["impact"] != "MAJOR"
            or value["change_code"] not in version_policy["major_trigger_codes"]
            or value["planned_action"] not in {"ACTIVATE", "CUTOVER", "ROLLBACK", "STOP"}
        ):
            raise AutoRuntimeError("NOTIFICATION_PUBLIC_METADATA_ENUM_INVALID")
        paths = value["affected_path_refs"]
        if (
            not isinstance(paths, list)
            or not paths
            or any(not isinstance(path, str) for path in paths)
            or paths != sorted(set(paths))
        ):
            raise AutoRuntimeError("NOTIFICATION_AFFECTED_PATHS_INVALID")
        for path in paths:
            parsed = PurePosixPath(path) if isinstance(path, str) else None
            if (
                parsed is None
                or parsed.is_absolute()
                or not parsed.parts
                or any(part in {"", ".", ".."} for part in parsed.parts)
                or "\\" in path
            ):
                raise AutoRuntimeError("NOTIFICATION_AFFECTED_PATH_INVALID")
        digests = value["evidence_digests"]
        if (
            not isinstance(digests, list)
            or any(not isinstance(item, str) for item in digests)
            or digests != sorted(set(digests))
            or any(not re.fullmatch(r"[0-9a-f]{64}", item) for item in digests)
        ):
            raise AutoRuntimeError("NOTIFICATION_EVIDENCE_DIGESTS_INVALID")
        rollback = value.get("rollback_target_ref")
        if rollback is not None and (
            not isinstance(rollback, str)
            or not re.fullmatch(r"(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64}|[a-z][a-z0-9-]{2,63})", rollback)
        ):
            raise AutoRuntimeError("NOTIFICATION_ROLLBACK_REF_INVALID")
        try:
            scan_public_value(value, self.contract.shared.policies)
        except Exception as exc:
            raise AutoRuntimeError(f"NOTIFICATION_PUBLIC_METADATA_PRIVACY_FAILED:{exc}") from exc

    def _entry_path(self, notification_uid: str) -> Path:
        return self.outbox_root / f"{notification_uid}.json"

    def _public_receipt(
        self,
        *,
        notification_uid: str,
        auto_transaction_uid: str,
        impact: str,
        timing: str,
        metadata_digest: str,
        result: ProviderResult,
        recipient_ref: str,
        entropy: Optional[bytes],
    ) -> Mapping[str, object]:
        now = self.clock.now()
        receipt = {
            "schema_version": NOTIFICATION_SCHEMA,
            "protocol_revision": PROTOCOL,
            "bundle_digest": self.bundle_digest,
            "receipt_uid": new_uid("nrc", now, entropy),
            "notification_uid": notification_uid,
            "auto_transaction_uid": auto_transaction_uid,
            "impact": impact,
            "notification_mode": "AUTOMATIC_NOTIFICATION_ONLY",
            "timing": timing,
            "provider_code": "EMAIL_PROVIDER",
            "provider_status": result.status,
            "recipient_ref": recipient_ref,
            "notification_policy_id": NOTIFICATION_POLICY_ID,
            "policy_snapshot_digest": self.policy_digest,
            "metadata_digest": metadata_digest,
            "created_at": format_utc(now),
            "approval_required": False,
            "owner_reply_required": False,
            "receipt_digest": "0" * 64,
        }
        if result.status == "SENT":
            receipt["provider_receipt_ref"] = result.provider_receipt_ref
            receipt["sent_at"] = format_utc(now)
        elif result.status in {"FAILED", "UNKNOWN"}:
            receipt["failure_code"] = result.failure_code or "RECEIPT_UNVERIFIED"
        else:
            raise AutoRuntimeError("NOTIFICATION_PROVIDER_STATUS_INVALID")
        receipt = canonical_with_digest(receipt, "receipt_digest")
        validate_auto_instance(
            self.contract,
            receipt,
            NOTIFICATION_SCHEMA,
            expected_bundle_digest=self.bundle_digest,
        )
        return receipt

    def notify_major(
        self,
        *,
        notification_uid: str,
        auto_transaction_uid: str,
        timing: str,
        mapping: RecipientMapping,
        subject: str,
        body: str,
        public_metadata: Mapping[str, object],
        entropy: Optional[bytes] = None,
        failpoint: Optional[Callable[[str], None]] = None,
    ) -> NotificationOutcome:
        if timing not in {"PRE_WRITE", "POST_CONTAINMENT"}:
            raise AutoRuntimeError("NOTIFICATION_TIMING_INVALID")
        if mapping.recipient_ref != self.policy.get("recipient_ref"):
            raise AutoRuntimeError("NOTIFICATION_RECIPIENT_REF_MISMATCH")
        self._validate_public_metadata(public_metadata)
        metadata_digest = sha256_bytes(canonicalize_object(public_metadata))
        private_payload_digest = sha256_bytes(
            canonicalize_object(
                {
                    "provider_target": mapping.provider_target,
                    "subject": subject,
                    "body": body,
                }
            )
        )
        idempotency_key = f"{notification_uid}:{private_payload_digest}"
        path = self._entry_path(notification_uid)
        entry = None
        if path.exists():
            entry = read_json(path)
            if (
                not isinstance(entry, dict)
                or entry.get("private_payload_digest") != private_payload_digest
                or entry.get("idempotency_key") != idempotency_key
            ):
                raise AutoRuntimeError("NOTIFICATION_UID_PAYLOAD_CORRUPTION")
            if entry.get("status") == "SENT":
                result = ProviderResult("SENT", provider_receipt_ref=entry["provider_receipt_ref"])
                receipt = self._public_receipt(
                    notification_uid=notification_uid,
                    auto_transaction_uid=auto_transaction_uid,
                    impact="MAJOR",
                    timing=timing,
                    metadata_digest=metadata_digest,
                    result=result,
                    recipient_ref=mapping.recipient_ref,
                    entropy=entropy,
                )
                return NotificationOutcome(receipt, True)
        else:
            entry = {
                "schema_version": "skillops.private-notification-outbox.v1",
                "notification_uid": notification_uid,
                "auto_transaction_uid": auto_transaction_uid,
                "recipient_ref": mapping.recipient_ref,
                "provider_target": mapping.provider_target,
                "subject": subject,
                "body": body,
                "private_payload_digest": private_payload_digest,
                "idempotency_key": idempotency_key,
                "status": "PENDING",
                "created_at": format_utc(self.clock.now()),
            }
            atomic_write_json(path, entry)

        observed = self.transport.lookup(idempotency_key)
        result = observed if observed.status == "SENT" else self.transport.send(
            idempotency_key=idempotency_key,
            provider_target=mapping.provider_target,
            subject=subject,
            body=body,
        )
        if failpoint is not None:
            failpoint("AFTER_PROVIDER_SEND")
        updated = dict(entry)
        updated["status"] = result.status
        if result.provider_receipt_ref is not None:
            updated["provider_receipt_ref"] = result.provider_receipt_ref
        if result.failure_code is not None:
            updated["failure_code"] = result.failure_code
        updated["updated_at"] = format_utc(self.clock.now())
        atomic_write_json(path, updated)
        receipt = self._public_receipt(
            notification_uid=notification_uid,
            auto_transaction_uid=auto_transaction_uid,
            impact="MAJOR",
            timing=timing,
            metadata_digest=metadata_digest,
            result=result,
            recipient_ref=mapping.recipient_ref,
            entropy=entropy,
        )
        allowed = result.status == "SENT" or timing == "POST_CONTAINMENT"
        return NotificationOutcome(receipt, allowed)
