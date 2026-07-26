"""Pure M-062 public-safe RUN_LOG queue lifecycle policy.

The Auto plane owns physical queue files and publication.  This module only
validates an exact ``public-queue-envelope:v2`` plus its canonical
``public-run-event:v2`` payload, emits public-safe evidence, and decides
whether the entry must remain queued.  A READY entry becomes settlement
eligible only after a repository-external reader resolves ``origin/main`` to
an advanced Git object and returns that object's exact JSONL blob.  Caller
booleans, local repository self-reporting, and digest maps are never trust
roots.

No method in this module receives a queue root, state path, lock, watermark,
Git worktree, or mutable publisher.  It performs no filesystem, network, or
state mutation.
"""

from __future__ import annotations

import dataclasses
import datetime as dt
import hashlib
import re
import sys
from pathlib import Path
from typing import Any, Mapping, Optional, Protocol, Tuple
from zoneinfo import ZoneInfo

_TOOLS_DIR = Path(__file__).resolve().parents[1] / "tools"
if str(_TOOLS_DIR) not in sys.path:
    sys.path.insert(0, str(_TOOLS_DIR))

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractBundle,
    ContractError,
    build_registry,
    validate_instance,
)
from CodexSkills.governance.tools.validate_public_run_event import (
    PUBLIC_RUN_EVENT_SCHEMA_ID,
    parse_canonical_public_run_event,
)


SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
PROTOCOL_REVISION = (
    "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
)
QUEUE_ENVELOPE_SCHEMA_ID = (
    SCHEMA_PREFIX + "public-queue-envelope:v2"
)
OBSERVATION_SCHEMA_ID = (
    SCHEMA_PREFIX + "public-safe-queue-observation:v1"
)
READBACK_SCHEMA_ID = (
    SCHEMA_PREFIX + "public-safe-queue-remote-readback:v1"
)
PLAN_SCHEMA_ID = (
    SCHEMA_PREFIX + "public-safe-queue-lifecycle-plan:v1"
)
QUEUE_ENVELOPE_SELF_POINTER = "/envelope_digest"
OBSERVATION_SELF_POINTER = "/evidence_bundle_digest"
READBACK_SELF_POINTER = "/evidence_bundle_digest"
PLAN_SELF_POINTER = "/evidence_bundle_digest"

REMOTE_NAME = "origin"
REMOTE_REF = "refs/heads/main"
RUN_LOG_ROOT = "OpenAIDatabase/data/run_logs/skills_runs"
JSONL_SERIALIZATION = "RFC8785_JCS_PER_LINE_LF"
MAX_SHARD_BYTES = 20 * 1024 * 1024
SYDNEY = ZoneInfo("Australia/Sydney")

GIT_OBJECT_RE = re.compile(
    r"^(?:sha1:[0-9a-f]{40}|sha256:[0-9a-f]{64})$"
)
PART_PATH_RE = re.compile(
    r"^OpenAIDatabase/data/run_logs/skills_runs/"
    r"(?P<year>[0-9]{4})/"
    r"(?P<month>0[1-9]|1[0-2])/"
    r"(?P<day>0[1-9]|[12][0-9]|3[01])/"
    r"part-(?P<part>[0-9]{4})\.jsonl$"
)
UTC_Z_RE = re.compile(
    r"^[0-9]{4}-(?:0[1-9]|1[0-2])-"
    r"(?:0[1-9]|[12][0-9]|3[01])T"
    r"(?:[01][0-9]|2[0-3]):[0-5][0-9]:"
    r"[0-5][0-9]\.[0-9]{6}Z$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class PublicSafeQueueError(ValueError):
    """The M-062 queue, payload, or remote proof failed closed."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class RemoteRunLogReader(Protocol):
    """Repository-external, read-only capability required for settlement."""

    def resolve_remote_head(
        self,
        remote_name: str,
        remote_ref: str,
    ) -> str:
        """Resolve the current remote ref to a tagged Git object."""
        ...

    def read_blob(
        self,
        verified_git_object_id: str,
        artifact_repo_path: str,
    ) -> bytes:
        """Read exact bytes from the already resolved Git object."""
        ...


@dataclasses.dataclass(frozen=True)
class QueueLifecycleResult:
    """Canonical public-safe evidence and a non-mutating lifecycle decision."""

    canonical_observation_bytes: bytes
    observation_digest: str
    canonical_readback_bytes: Optional[bytes]
    readback_digest: Optional[str]
    canonical_plan_bytes: bytes
    plan_digest: str
    next_queue_state: str
    queue_retention_required: bool


def _fail(code: str) -> None:
    raise PublicSafeQueueError(code)


def _strict_utc(value: Any, code: str) -> dt.datetime:
    if not isinstance(value, str) or UTC_Z_RE.fullmatch(value) is None:
        _fail(code)
    try:
        parsed = dt.datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%S.%fZ",
        )
    except ValueError as exc:
        raise PublicSafeQueueError(code) from exc
    return parsed.replace(tzinfo=dt.timezone.utc)


def _strict_git_object(value: Any, code: str) -> str:
    if not isinstance(value, str) or GIT_OBJECT_RE.fullmatch(value) is None:
        _fail(code)
    return value


def _validate_part_path(
    value: Any,
    event_occurred_at: str,
) -> str:
    if not isinstance(value, str):
        _fail("PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_INVALID")
    match = PART_PATH_RE.fullmatch(value)
    if match is None:
        _fail("PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_INVALID")
    try:
        local_date = dt.date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_DATE_INVALID"
        ) from exc
    occurred = _strict_utc(
        event_occurred_at,
        "PUBLIC_SAFE_QUEUE_EVENT_OCCURRED_AT_INVALID",
    )
    if occurred.astimezone(SYDNEY).date() != local_date:
        _fail("PUBLIC_SAFE_QUEUE_LOCAL_DATE_MISMATCH")
    if int(match.group("part")) < 1:
        _fail("PUBLIC_SAFE_QUEUE_PART_NUMBER_INVALID")
    return value


def _validate_part_path_shape(value: Any) -> str:
    if not isinstance(value, str):
        _fail("PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_INVALID")
    match = PART_PATH_RE.fullmatch(value)
    if match is None:
        _fail("PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_INVALID")
    try:
        dt.date(
            int(match.group("year")),
            int(match.group("month")),
            int(match.group("day")),
        )
    except ValueError as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_ARTIFACT_PATH_DATE_INVALID"
        ) from exc
    if int(match.group("part")) < 1:
        _fail("PUBLIC_SAFE_QUEUE_PART_NUMBER_INVALID")
    return value


def _add_schema(
    schemas: dict[str, Any],
    pointers: dict[str, Optional[str]],
    *,
    schema_id: str,
    document: Mapping[str, Any],
    expected_digest: str,
    self_pointer: str,
) -> None:
    if (
        not isinstance(document, dict)
        or document.get("$id") != schema_id
        or not isinstance(expected_digest, str)
        or SHA256_RE.fullmatch(expected_digest) is None
        or canonical_digest(document) != expected_digest
    ):
        _fail("PUBLIC_SAFE_QUEUE_SCHEMA_TRUST_MISMATCH")
    if schema_id in schemas:
        _fail("PUBLIC_SAFE_QUEUE_SCHEMA_REBIND_FORBIDDEN")
    schemas[schema_id] = document
    pointers[schema_id] = self_pointer


def build_public_safe_queue_contract(
    candidate: ContractBundle,
    *,
    queue_envelope_schema: Mapping[str, Any],
    expected_queue_envelope_schema_digest: str,
    observation_schema: Mapping[str, Any],
    expected_observation_schema_digest: str,
    readback_schema: Mapping[str, Any],
    expected_readback_schema_digest: str,
    plan_schema: Mapping[str, Any],
    expected_plan_schema_digest: str,
) -> ContractBundle:
    """Add the exact private queue schema and M-062 evidence schemas."""

    if (
        PUBLIC_RUN_EVENT_SCHEMA_ID not in candidate.schemas
        or candidate.self_digest_pointers.get(
            PUBLIC_RUN_EVENT_SCHEMA_ID
        )
        != "/event_digest"
    ):
        _fail("PUBLIC_SAFE_QUEUE_RUN_EVENT_CONTRACT_MISSING")
    schemas = dict(candidate.schemas)
    pointers = dict(candidate.self_digest_pointers)
    additions = (
        (
            QUEUE_ENVELOPE_SCHEMA_ID,
            queue_envelope_schema,
            expected_queue_envelope_schema_digest,
            QUEUE_ENVELOPE_SELF_POINTER,
        ),
        (
            OBSERVATION_SCHEMA_ID,
            observation_schema,
            expected_observation_schema_digest,
            OBSERVATION_SELF_POINTER,
        ),
        (
            READBACK_SCHEMA_ID,
            readback_schema,
            expected_readback_schema_digest,
            READBACK_SELF_POINTER,
        ),
        (
            PLAN_SCHEMA_ID,
            plan_schema,
            expected_plan_schema_digest,
            PLAN_SELF_POINTER,
        ),
    )
    for schema_id, document, expected_digest, pointer in additions:
        _add_schema(
            schemas,
            pointers,
            schema_id=schema_id,
            document=document,
            expected_digest=expected_digest,
            self_pointer=pointer,
        )
    try:
        registry, format_checker = build_registry(schemas)
    except ContractError as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_SCHEMA_CLOSURE_INVALID:" + str(exc)
        ) from exc
    return ContractBundle(
        schemas=schemas,
        registry=registry,
        format_checker=format_checker,
        self_digest_pointers=pointers,
        policies=candidate.policies,
        protocol_revision=candidate.protocol_revision,
    )


def _validate_instance(
    bundle: ContractBundle,
    value: Mapping[str, Any],
    schema_id: str,
    expected_bundle_digest: str,
    code: str,
    *,
    public: bool,
) -> None:
    try:
        validate_instance(
            bundle,
            value,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
            verify_digest=True,
            public=public,
        )
    except ContractError as exc:
        raise PublicSafeQueueError(code + ":" + str(exc)) from exc


def validate_queue_observation(
    bundle: ContractBundle,
    observation: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate one emitted observation, including non-schema semantics."""

    if not isinstance(observation, dict):
        _fail("PUBLIC_SAFE_QUEUE_OBSERVATION_ROOT_INVALID")
    _validate_instance(
        bundle,
        observation,
        OBSERVATION_SCHEMA_ID,
        expected_bundle_digest,
        "PUBLIC_SAFE_QUEUE_OBSERVATION_INVALID",
        public=True,
    )
    _strict_utc(
        observation["observed_at"],
        "PUBLIC_SAFE_QUEUE_OBSERVED_AT_INVALID",
    )
    _validate_part_path_shape(observation["artifact_repo_path"])
    if (
        observation["artifact_ref"]["artifact_schema_id"]
        != PUBLIC_RUN_EVENT_SCHEMA_ID
        or observation["lane"] != "RUN_LOG"
        or observation["raw_or_private_field_count"] != 0
        or observation["physical_queue_path_consumed"] is not False
        or observation["state_mutation_performed"] is not False
    ):
        _fail("PUBLIC_SAFE_QUEUE_OBSERVATION_SEMANTIC_MISMATCH")
    return observation


def validate_remote_readback_evidence(
    bundle: ContractBundle,
    readback: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
) -> Mapping[str, Any]:
    """Validate emitted readback evidence without treating it as a trust root."""

    if not isinstance(readback, dict):
        _fail("PUBLIC_SAFE_QUEUE_READBACK_ROOT_INVALID")
    _validate_instance(
        bundle,
        readback,
        READBACK_SCHEMA_ID,
        expected_bundle_digest,
        "PUBLIC_SAFE_QUEUE_READBACK_INVALID",
        public=True,
    )
    _strict_utc(
        readback["readback_at"],
        "PUBLIC_SAFE_QUEUE_READBACK_AT_INVALID",
    )
    expected_head = _strict_git_object(
        readback["expected_remote_head"],
        "PUBLIC_SAFE_QUEUE_EXPECTED_REMOTE_HEAD_INVALID",
    )
    observed_head = _strict_git_object(
        readback["observed_remote_head"],
        "PUBLIC_SAFE_QUEUE_OBSERVED_REMOTE_HEAD_INVALID",
    )
    if expected_head.split(":", 1)[0] != observed_head.split(":", 1)[0]:
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_OBJECT_ALGORITHM_MISMATCH")
    if expected_head == observed_head:
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_HEAD_NOT_ADVANCED")
    _validate_part_path_shape(readback["artifact_repo_path"])
    if (
        readback["remote_name"] != REMOTE_NAME
        or readback["remote_ref"] != REMOTE_REF
        or readback["artifact_schema_id"]
        != PUBLIC_RUN_EVENT_SCHEMA_ID
        or readback["line_number"] > readback["record_count"]
        or readback["remote_head_advanced"] is not True
        or readback["caller_boolean_trusted"] is not False
        or readback["state_mutation_performed"] is not False
    ):
        _fail("PUBLIC_SAFE_QUEUE_READBACK_SEMANTIC_MISMATCH")
    return readback


def validate_lifecycle_plan(
    bundle: ContractBundle,
    plan: Mapping[str, Any],
    *,
    expected_bundle_digest: str,
    expected_observation_digest: Optional[str] = None,
    expected_readback_digest: Optional[str] = None,
) -> Mapping[str, Any]:
    """Validate the retain/settle state machine and exact evidence links."""

    if not isinstance(plan, dict):
        _fail("PUBLIC_SAFE_QUEUE_PLAN_ROOT_INVALID")
    _validate_instance(
        bundle,
        plan,
        PLAN_SCHEMA_ID,
        expected_bundle_digest,
        "PUBLIC_SAFE_QUEUE_PLAN_INVALID",
        public=True,
    )
    _strict_utc(
        plan["generated_at"],
        "PUBLIC_SAFE_QUEUE_PLAN_TIME_INVALID",
    )
    observation_digest = plan["observation_ref"][
        "evidence_bundle_digest"
    ]
    if (
        expected_observation_digest is not None
        and observation_digest != expected_observation_digest
    ):
        _fail("PUBLIC_SAFE_QUEUE_PLAN_OBSERVATION_REF_MISMATCH")
    source_state = plan["source_queue_state"]
    readback_ref = plan["remote_readback_ref"]
    if readback_ref is None:
        expected = {
            "QUARANTINED": (
                "RETAIN_QUARANTINED",
                "QUARANTINED",
            ),
            "READY": ("RETAIN_READY", "READY"),
        }.get(source_state)
        if (
            expected is None
            or plan["decision"] != expected[0]
            or plan["next_queue_state"] != expected[1]
            or plan["queue_retention_required"] is not True
            or plan["settlement_eligible"] is not False
            or plan["action_order"]
            != [
                "RETAIN_QUEUE_ENTRY",
                "RETRY_REMOTE_VERIFICATION",
            ]
            or expected_readback_digest is not None
        ):
            _fail("PUBLIC_SAFE_QUEUE_RETAIN_PLAN_INVALID")
    else:
        readback_digest = readback_ref["evidence_bundle_digest"]
        expected_decision = {
            "READY": "ELIGIBLE_TO_MARK_SETTLED",
            "SETTLED": "CONFIRM_SETTLED",
        }.get(source_state)
        if (
            expected_decision is None
            or plan["decision"] != expected_decision
            or plan["next_queue_state"] != "SETTLED"
            or plan["queue_retention_required"] is not False
            or plan["settlement_eligible"] is not True
            or plan["action_order"]
            != [
                "BIND_REMOTE_READBACK_EVIDENCE",
                "MARK_QUEUE_ENTRY_SETTLED",
            ]
            or expected_readback_digest is None
            or readback_digest != expected_readback_digest
        ):
            _fail("PUBLIC_SAFE_QUEUE_SETTLEMENT_PLAN_INVALID")
    if (
        plan["queue_content_delete_authority_granted"] is not False
        or plan["watermark_advance_authority_granted"] is not False
        or plan["state_mutation_performed"] is not False
        or plan["auto_executor_integration_status"] != "NOT_BOUND"
    ):
        _fail("PUBLIC_SAFE_QUEUE_PLAN_AUTHORITY_MISMATCH")
    return plan


def _validate_queue_and_event(
    bundle: ContractBundle,
    envelope: Mapping[str, Any],
    artifact_bytes: bytes,
    expected_bundle_digest: str,
) -> tuple[Mapping[str, Any], str]:
    if not isinstance(envelope, dict):
        _fail("PUBLIC_SAFE_QUEUE_ENVELOPE_ROOT_INVALID")
    _validate_instance(
        bundle,
        envelope,
        QUEUE_ENVELOPE_SCHEMA_ID,
        expected_bundle_digest,
        "PUBLIC_SAFE_QUEUE_ENVELOPE_INVALID",
        public=True,
    )
    if not isinstance(artifact_bytes, bytes):
        _fail("PUBLIC_SAFE_QUEUE_ARTIFACT_BYTES_INVALID")
    try:
        event = parse_canonical_public_run_event(
            bundle,
            artifact_bytes,
            expected_bundle_digest=expected_bundle_digest,
        )
    except ValueError as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_EVENT_INVALID:" + str(exc)
        ) from exc
    if (
        envelope.get("bundle_digest") != expected_bundle_digest
        or envelope.get("lane") != "RUN_LOG"
        or envelope.get("artifact_schema_id")
        != PUBLIC_RUN_EVENT_SCHEMA_ID
        or envelope.get("artifact_uid") != event.get("event_uid")
        or envelope.get("artifact_digest")
        != event.get("event_digest")
    ):
        _fail("PUBLIC_SAFE_QUEUE_ENVELOPE_EVENT_BINDING_MISMATCH")
    artifact_path = _validate_part_path(
        envelope.get("artifact_repo_path"),
        str(event["occurred_at"]),
    )
    if _strict_utc(
        envelope.get("sealed_at"),
        "PUBLIC_SAFE_QUEUE_SEALED_AT_INVALID",
    ) < _strict_utc(
        event.get("occurred_at"),
        "PUBLIC_SAFE_QUEUE_EVENT_OCCURRED_AT_INVALID",
    ):
        _fail("PUBLIC_SAFE_QUEUE_SEALED_BEFORE_EVENT")
    return event, artifact_path


def _observation(
    *,
    expected_bundle_digest: str,
    observation_uid: str,
    observed_at: str,
    envelope: Mapping[str, Any],
    artifact_bytes: bytes,
    artifact_path: str,
) -> Mapping[str, Any]:
    value = {
        "schema_version": OBSERVATION_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "observation_uid": observation_uid,
        "observed_at": observed_at,
        "queue_envelope_ref": {
            "envelope_uid": envelope["envelope_uid"],
            "envelope_digest": envelope["envelope_digest"],
        },
        "artifact_ref": {
            "artifact_schema_id": envelope["artifact_schema_id"],
            "artifact_uid": envelope["artifact_uid"],
            "artifact_digest": envelope["artifact_digest"],
        },
        "lane": "RUN_LOG",
        "source_queue_state": envelope["queue_state"],
        "artifact_repo_path": artifact_path,
        "artifact_serialization": "RFC8785_JCS_OBJECT",
        "artifact_bytes": len(artifact_bytes),
        "public_schema_valid": True,
        "semantic_event_valid": True,
        "post_serialization_scan_passed": True,
        "raw_or_private_field_count": 0,
        "physical_queue_path_consumed": False,
        "state_mutation_performed": False,
        "actor": "SKILLOPS_PUBLIC_SAFE_QUEUE_GUARD",
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        OBSERVATION_SELF_POINTER,
    )
    return value


def _readback(
    bundle: ContractBundle,
    *,
    reader: RemoteRunLogReader,
    expected_bundle_digest: str,
    readback_uid: str,
    readback_at: str,
    expected_remote_head: str,
    envelope: Mapping[str, Any],
    artifact_bytes: bytes,
    artifact_path: str,
) -> Mapping[str, Any]:
    expected_head = _strict_git_object(
        expected_remote_head,
        "PUBLIC_SAFE_QUEUE_EXPECTED_REMOTE_HEAD_INVALID",
    )
    try:
        observed_raw = reader.resolve_remote_head(
            REMOTE_NAME,
            REMOTE_REF,
        )
    except Exception as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_REMOTE_REF_READ_FAILED"
        ) from exc
    observed_head = _strict_git_object(
        observed_raw,
        "PUBLIC_SAFE_QUEUE_OBSERVED_REMOTE_HEAD_INVALID",
    )
    if observed_head.split(":", 1)[0] != expected_head.split(":", 1)[0]:
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_OBJECT_ALGORITHM_MISMATCH")
    if observed_head == expected_head:
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_HEAD_NOT_ADVANCED")
    try:
        shard_bytes = reader.read_blob(
            observed_head,
            artifact_path,
        )
    except Exception as exc:
        raise PublicSafeQueueError(
            "PUBLIC_SAFE_QUEUE_REMOTE_BLOB_READ_FAILED"
        ) from exc
    if (
        not isinstance(shard_bytes, bytes)
        or not shard_bytes
        or len(shard_bytes) > MAX_SHARD_BYTES
        or shard_bytes.startswith(b"\xef\xbb\xbf")
        or b"\r" in shard_bytes
        or not shard_bytes.endswith(b"\n")
    ):
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_JSONL_FRAMING_INVALID")
    records = shard_bytes[:-1].split(b"\n")
    if not records or any(not record for record in records):
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_JSONL_FRAMING_INVALID")

    event_uids: set[str] = set()
    event_digests: set[str] = set()
    target_lines = []
    for line_number, record in enumerate(records, 1):
        try:
            parsed = parse_canonical_public_run_event(
                bundle,
                record,
                expected_bundle_digest=expected_bundle_digest,
            )
        except ValueError as exc:
            raise PublicSafeQueueError(
                "PUBLIC_SAFE_QUEUE_REMOTE_RECORD_INVALID:" + str(exc)
            ) from exc
        event_uid = str(parsed["event_uid"])
        event_digest = str(parsed["event_digest"])
        if event_uid in event_uids or event_digest in event_digests:
            _fail("PUBLIC_SAFE_QUEUE_REMOTE_RECORD_DUPLICATE")
        event_uids.add(event_uid)
        event_digests.add(event_digest)
        if event_uid == envelope["artifact_uid"]:
            if (
                event_digest != envelope["artifact_digest"]
                or record != artifact_bytes
            ):
                _fail("PUBLIC_SAFE_QUEUE_REMOTE_ARTIFACT_BYTES_MISMATCH")
            target_lines.append(line_number)
    if len(target_lines) != 1:
        _fail("PUBLIC_SAFE_QUEUE_REMOTE_ARTIFACT_NOT_UNIQUE")

    value = {
        "schema_version": READBACK_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "readback_uid": readback_uid,
        "readback_at": readback_at,
        "queue_envelope_ref": {
            "envelope_uid": envelope["envelope_uid"],
            "envelope_digest": envelope["envelope_digest"],
        },
        "remote_name": REMOTE_NAME,
        "remote_ref": REMOTE_REF,
        "expected_remote_head": expected_head,
        "observed_remote_head": observed_head,
        "artifact_repo_path": artifact_path,
        "artifact_schema_id": PUBLIC_RUN_EVENT_SCHEMA_ID,
        "artifact_uid": envelope["artifact_uid"],
        "artifact_digest": envelope["artifact_digest"],
        "artifact_serialization": JSONL_SERIALIZATION,
        "record_count": len(records),
        "line_number": target_lines[0],
        "shard_digest": hashlib.sha256(shard_bytes).hexdigest(),
        "remote_head_advanced": True,
        "caller_boolean_trusted": False,
        "state_mutation_performed": False,
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        READBACK_SELF_POINTER,
    )
    return value


def _plan(
    *,
    expected_bundle_digest: str,
    plan_uid: str,
    generated_at: str,
    envelope: Mapping[str, Any],
    observation_digest: str,
    readback_digest: Optional[str],
) -> Mapping[str, Any]:
    source_state = str(envelope["queue_state"])
    if readback_digest is None:
        if source_state == "SETTLED":
            _fail("PUBLIC_SAFE_QUEUE_SETTLED_REQUIRES_REMOTE_PROOF")
        decision = (
            "RETAIN_QUARANTINED"
            if source_state == "QUARANTINED"
            else "RETAIN_READY"
        )
        next_state = source_state
        retention_required = True
        settlement_eligible = False
        action_order = [
            "RETAIN_QUEUE_ENTRY",
            "RETRY_REMOTE_VERIFICATION",
        ]
        readback_ref = None
    else:
        if source_state == "QUARANTINED":
            _fail("PUBLIC_SAFE_QUEUE_QUARANTINED_NOT_SETTLEABLE")
        decision = (
            "CONFIRM_SETTLED"
            if source_state == "SETTLED"
            else "ELIGIBLE_TO_MARK_SETTLED"
        )
        next_state = "SETTLED"
        retention_required = False
        settlement_eligible = True
        action_order = [
            "BIND_REMOTE_READBACK_EVIDENCE",
            "MARK_QUEUE_ENTRY_SETTLED",
        ]
        readback_ref = {
            "evidence_bundle_digest": readback_digest,
        }
    value = {
        "schema_version": PLAN_SCHEMA_ID,
        "protocol_revision": PROTOCOL_REVISION,
        "bundle_digest": expected_bundle_digest,
        "plan_uid": plan_uid,
        "generated_at": generated_at,
        "observation_ref": {
            "evidence_bundle_digest": observation_digest,
        },
        "remote_readback_ref": readback_ref,
        "source_queue_state": source_state,
        "decision": decision,
        "next_queue_state": next_state,
        "queue_retention_required": retention_required,
        "settlement_eligible": settlement_eligible,
        "action_order": action_order,
        "queue_content_delete_authority_granted": False,
        "watermark_advance_authority_granted": False,
        "state_mutation_performed": False,
        "auto_executor_integration_status": "NOT_BOUND",
        "evidence_bundle_digest": "0" * 64,
    }
    value["evidence_bundle_digest"] = canonical_digest(
        value,
        PLAN_SELF_POINTER,
    )
    return value


def evaluate_public_safe_queue(
    bundle: ContractBundle,
    *,
    envelope: Mapping[str, Any],
    artifact_bytes: bytes,
    observation_uid: str,
    plan_uid: str,
    observed_at: str,
    expected_bundle_digest: str,
    remote_reader: Optional[RemoteRunLogReader] = None,
    expected_remote_head: Optional[str] = None,
    readback_uid: Optional[str] = None,
    readback_at: Optional[str] = None,
) -> QueueLifecycleResult:
    """Validate one queue entry and decide retain/settle without mutation."""

    observed = _strict_utc(
        observed_at,
        "PUBLIC_SAFE_QUEUE_OBSERVED_AT_INVALID",
    )
    _event, artifact_path = _validate_queue_and_event(
        bundle,
        envelope,
        artifact_bytes,
        expected_bundle_digest,
    )
    sealed = _strict_utc(
        envelope["sealed_at"],
        "PUBLIC_SAFE_QUEUE_SEALED_AT_INVALID",
    )
    if observed < sealed:
        _fail("PUBLIC_SAFE_QUEUE_OBSERVED_BEFORE_SEALED")
    observation = _observation(
        expected_bundle_digest=expected_bundle_digest,
        observation_uid=observation_uid,
        observed_at=observed_at,
        envelope=envelope,
        artifact_bytes=artifact_bytes,
        artifact_path=artifact_path,
    )
    validate_queue_observation(
        bundle,
        observation,
        expected_bundle_digest=expected_bundle_digest,
    )

    readback = None
    readback_digest = None
    remote_arguments = (
        expected_remote_head,
        readback_uid,
        readback_at,
    )
    if remote_reader is None:
        if any(value is not None for value in remote_arguments):
            _fail("PUBLIC_SAFE_QUEUE_REMOTE_ARGUMENTS_WITHOUT_READER")
    else:
        if any(value is None for value in remote_arguments):
            _fail("PUBLIC_SAFE_QUEUE_REMOTE_ARGUMENTS_INCOMPLETE")
        assert expected_remote_head is not None
        assert readback_uid is not None
        assert readback_at is not None
        readback_time = _strict_utc(
            readback_at,
            "PUBLIC_SAFE_QUEUE_READBACK_AT_INVALID",
        )
        if readback_time < sealed or readback_time > observed:
            _fail("PUBLIC_SAFE_QUEUE_READBACK_TIME_INVALID")
        readback = _readback(
            bundle,
            reader=remote_reader,
            expected_bundle_digest=expected_bundle_digest,
            readback_uid=readback_uid,
            readback_at=readback_at,
            expected_remote_head=expected_remote_head,
            envelope=envelope,
            artifact_bytes=artifact_bytes,
            artifact_path=artifact_path,
        )
        validate_remote_readback_evidence(
            bundle,
            readback,
            expected_bundle_digest=expected_bundle_digest,
        )
        readback_digest = str(readback["evidence_bundle_digest"])

    plan = _plan(
        expected_bundle_digest=expected_bundle_digest,
        plan_uid=plan_uid,
        generated_at=observed_at,
        envelope=envelope,
        observation_digest=str(
            observation["evidence_bundle_digest"]
        ),
        readback_digest=readback_digest,
    )
    validate_lifecycle_plan(
        bundle,
        plan,
        expected_bundle_digest=expected_bundle_digest,
        expected_observation_digest=str(
            observation["evidence_bundle_digest"]
        ),
        expected_readback_digest=readback_digest,
    )
    return QueueLifecycleResult(
        canonical_observation_bytes=canonicalize_object(observation),
        observation_digest=str(
            observation["evidence_bundle_digest"]
        ),
        canonical_readback_bytes=(
            canonicalize_object(readback)
            if readback is not None
            else None
        ),
        readback_digest=readback_digest,
        canonical_plan_bytes=canonicalize_object(plan),
        plan_digest=str(plan["evidence_bundle_digest"]),
        next_queue_state=str(plan["next_queue_state"]),
        queue_retention_required=bool(
            plan["queue_retention_required"]
        ),
    )
