"""Stable, append-only ChatGPT conversation version events for S09-P1-T2."""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_canonical_events.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_canonical_events.v1_2_1_s09_p1_t2.json"
)
EVENTS_RELATIVE = Path(
    "data/processed/conversations/chatgpt_canonical_events.jsonl"
)

TASK_ID = "S09-P1-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P1-T2"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_canonical_event_contract.v1_2_1_s09_p1_t2"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_canonical_event_model.v1_2_1_s09_p1_t2"
)
EVENT_SCHEMA_VERSION = "memory_atlas.chatgpt_canonical_event.v1_2_1_s09_p1_t2"
CONVERSATION_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_canonical_conversation.v1_2_1_s09_p1_t2"
)
MESSAGE_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_canonical_message.v1_2_1_s09_p1_t2"
)
PLAN_SCHEMA_VERSION = "memory_atlas.chatgpt_canonical_event_plan.v1_2_1_s09_p1_t2"

MAXIMUM_LEDGER_BYTES = 512 * 1024 * 1024
MAXIMUM_LEDGER_EVENTS = 2_000_000
MAXIMUM_MESSAGES_PER_CONVERSATION = 500_000
MAXIMUM_CONTRACT_BYTES = 128 * 1024

_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

PHASE_BOUNDARY = {
    "implements_stable_ids": True,
    "implements_version_history": True,
    "implements_incremental_deduplication": True,
    "implements_derived_facets": False,
    "implements_topics_or_activity": False,
    "mutates_source": False,
    "next_task": "S09-P1-T3",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "inputs": {
        "normalized_conversation_schema": "memory_atlas_public_raw_chatgpt.v1",
        "parser_task": "S09-P1-T1",
        "raw_root": "data/public_raw/chatgpt",
    },
    "outputs": {
        "canonical_events": EVENTS_RELATIVE.as_posix(),
        "event_type": "conversation_version",
        "one_row_per_unseen_version": True,
    },
    "identity": {
        "conversation_id": "sha256(source_id + stable source conversation identity)",
        "message_id": "sha256(canonical conversation id + stable source message identity)",
        "message_sha256": "sha256(canonical normalized message payload)",
        "version_id": "sha256(canonical normalized conversation payload)",
        "transport_provenance_excluded_from_version_hash": True,
    },
    "append_only": {
        "ledger_prefix_preserved": True,
        "replay_appends_zero_rows": True,
        "modified_conversation_appends_new_version": True,
        "raw_never_overwritten": True,
        "previous_version_chain_required": True,
    },
    "security": {
        "source_read_only": True,
        "repository_relative_raw_refs": True,
        "remote_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S09-P1-T2",
    "formula_id": "FORM-MA-V121-S09-P1-T2",
    "purpose": "Create stable ChatGPT conversation/message identities and append one immutable event for each unseen conversation version.",
    "limits": {
        "maximum_ledger_bytes": MAXIMUM_LEDGER_BYTES,
        "maximum_ledger_events": MAXIMUM_LEDGER_EVENTS,
        "maximum_messages_per_conversation": MAXIMUM_MESSAGES_PER_CONVERSATION,
        "maximum_contract_bytes": MAXIMUM_CONTRACT_BYTES,
    },
    "formulas": {
        "canonical_json": "utf8(json(value, sort_keys=true, separators=(',', ':'), ensure_ascii=false))",
        "conversation_id": "chatgpt-conversation- + sha256(canonical_json({source_id, source_conversation_id}))[0:32]",
        "message_id": "chatgpt-message- + sha256(canonical_json({conversation_id, source_message_id}))[0:32]",
        "message_sha256": "sha256(canonical_json(message_without_message_sha256))",
        "conversation_version_id": "chatgpt-version- + sha256(canonical_json(canonical_conversation))[0:32]",
        "incremental_decision": "append iff version_id is absent from validated existing ledger",
    },
    "invariants": [
        "conversation and message IDs do not depend on mutable content",
        "export hash, observed time, raw ref and parser provenance do not affect version identity",
        "existing canonical event bytes remain an exact prefix after append",
        "a replay of an existing version writes no canonical event bytes",
        "a changed conversation writes a new raw content-addressed file and a chained canonical version without replacing old raw",
        "facets, topics, activity and Universe State inputs remain outside this task",
    ],
    "phase_boundary": PHASE_BOUNDARY,
}


class ChatGPTCanonicalEventError(ValueError):
    """Fail-closed canonical identity or append-only ledger error."""

    def __init__(self, code: str, *, writes_files: bool = False) -> None:
        super().__init__(code)
        self.code = code
        self.writes_files = writes_files


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_payload_invalid") from exc


def _sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _stable_id(kind: str, value: Any) -> str:
    return f"chatgpt-{kind}-{_sha256(value)[:32]}"


def _database_root(database_dir: Path) -> Path:
    root = Path(database_dir).expanduser().absolute()
    if root.exists():
        if root.is_symlink() or not root.is_dir():
            raise ChatGPTCanonicalEventError("chatgpt_canonical_database_invalid")
        return root.resolve()
    parent = root.parent
    if not parent.is_dir() or parent.is_symlink():
        raise ChatGPTCanonicalEventError("chatgpt_canonical_database_invalid")
    return root.resolve(strict=False)


def _read_regular_bytes(path: Path, *, maximum_bytes: int, code: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ChatGPTCanonicalEventError(code) from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ChatGPTCanonicalEventError(code)
    if metadata.st_size > maximum_bytes:
        raise ChatGPTCanonicalEventError(code)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ChatGPTCanonicalEventError(code) from exc
    if len(payload) > maximum_bytes:
        raise ChatGPTCanonicalEventError(code)
    return payload


def _read_contract_json(path: Path, *, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            _read_regular_bytes(
                path,
                maximum_bytes=MAXIMUM_CONTRACT_BYTES,
                code=code,
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChatGPTCanonicalEventError(code) from exc
    if not isinstance(payload, dict):
        raise ChatGPTCanonicalEventError(code)
    return payload


def validate_chatgpt_canonical_event_contract(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_CONTRACT:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_contract_drift")
    return dict(payload)


def validate_chatgpt_canonical_event_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_model_drift")
    return dict(payload)


def load_chatgpt_canonical_event_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_canonical_event_contract(
        _read_contract_json(
            root / CONTRACT_RELATIVE,
            code="chatgpt_canonical_contract_invalid",
        )
    )


def load_chatgpt_canonical_event_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_canonical_event_model_parameters(
        _read_contract_json(
            root / MODEL_RELATIVE,
            code="chatgpt_canonical_model_invalid",
        )
    )


def _clean_source_id(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _first_message_anchor(conversation: dict[str, Any]) -> str:
    mapping = conversation.get("mapping")
    if isinstance(mapping, dict):
        for mapping_key, node in mapping.items():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            if not isinstance(message, dict):
                continue
            anchor = _clean_source_id(message.get("id"))
            if anchor:
                return f"message:{anchor}"
            node_anchor = _clean_source_id(node.get("id")) or str(mapping_key)
            if node_anchor:
                return f"mapping:{node_anchor}"
    messages = conversation.get("messages")
    if isinstance(messages, list):
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            anchor = _clean_source_id(message.get("id"))
            if anchor:
                return f"message:{anchor}"
            created_at = _clean_source_id(
                message.get("create_time") or message.get("created_at")
            )
            role = _clean_source_id(message.get("role"))
            if created_at or role:
                return f"direct:{index}:{created_at}:{role}"
    return ""


def stable_source_conversation_id(conversation: dict[str, Any]) -> str:
    """Return source ID or a content-independent parser-position fallback."""

    source_id = _clean_source_id(
        conversation.get("id") or conversation.get("conversation_id")
    )
    if source_id:
        return source_id
    provenance = conversation.get("_memory_atlas_parser")
    provenance = provenance if isinstance(provenance, dict) else {}
    seed = {
        "source_id": "chatgpt",
        "source_ref": _clean_source_id(provenance.get("source_ref")),
        "item_index": provenance.get("item_index"),
        "created_at": _clean_source_id(
            conversation.get("create_time") or conversation.get("created_at")
        ),
        "first_message_anchor": _first_message_anchor(conversation),
    }
    return f"derived-{_sha256(seed)[:32]}"


def _mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ChatGPTCanonicalEventError(code)
    return value


def _list(value: Any, code: str) -> list[Any]:
    if not isinstance(value, list):
        raise ChatGPTCanonicalEventError(code)
    return value


def _repository_relative_raw_ref(value: Any) -> str:
    raw_ref = _clean_source_id(value)
    path = PurePosixPath(raw_ref)
    if (
        not raw_ref.startswith("data/public_raw/chatgpt/")
        or path.is_absolute()
        or ".." in path.parts
        or path.as_posix() != raw_ref
    ):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_raw_ref_invalid")
    return raw_ref


def _require_sha256(value: Any, code: str) -> str:
    text = _clean_source_id(value)
    if not _SHA256_RE.fullmatch(text):
        raise ChatGPTCanonicalEventError(code)
    return text


def _canonical_message(
    conversation_id: str,
    message: dict[str, Any],
) -> dict[str, Any]:
    source_message_id = _clean_source_id(message.get("message_id"))
    if not source_message_id:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_message_identity_missing")
    message_id = _stable_id(
        "message",
        {
            "conversation_id": conversation_id,
            "source_message_id": source_message_id,
        },
    )
    canonical = {
        "schema_version": MESSAGE_SCHEMA_VERSION,
        "message_id": message_id,
        "source_message_id": source_message_id,
        "role": _clean_source_id(message.get("role")) or "unknown",
        "created_at": _clean_source_id(message.get("created_at")),
        "text": str(message.get("text") or ""),
        "attachments": copy.deepcopy(_list(message.get("attachments"), "chatgpt_canonical_attachments_invalid")),
        "source_extensions": copy.deepcopy(
            _mapping(
                message.get("source_extensions"),
                "chatgpt_canonical_message_extensions_invalid",
            )
        ),
        "author_extensions": copy.deepcopy(
            _mapping(
                message.get("author_extensions"),
                "chatgpt_canonical_author_extensions_invalid",
            )
        ),
        "content_extensions": copy.deepcopy(
            _mapping(
                message.get("content_extensions"),
                "chatgpt_canonical_content_extensions_invalid",
            )
        ),
    }
    canonical["message_sha256"] = _sha256(canonical)
    return canonical


def build_chatgpt_canonical_event(
    row: dict[str, Any],
    *,
    raw_ref: str,
    export_sha256: str,
    observed_at: str,
) -> dict[str, Any]:
    if not isinstance(row, dict) or row.get("source_id") != "chatgpt":
        raise ChatGPTCanonicalEventError("chatgpt_canonical_conversation_invalid")
    source_conversation_id = _clean_source_id(row.get("conversation_id"))
    if not source_conversation_id:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_conversation_identity_missing")
    conversation_id = _stable_id(
        "conversation",
        {
            "source_id": "chatgpt",
            "source_conversation_id": source_conversation_id,
        },
    )
    source_messages = _list(
        row.get("messages"),
        "chatgpt_canonical_messages_invalid",
    )
    if len(source_messages) > MAXIMUM_MESSAGES_PER_CONVERSATION:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_message_limit_exceeded")
    messages = [
        _canonical_message(
            conversation_id,
            _mapping(message, "chatgpt_canonical_message_invalid"),
        )
        for message in source_messages
    ]
    message_ids = [message["message_id"] for message in messages]
    if len(message_ids) != len(set(message_ids)):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_message_identity_duplicate")
    if int(row.get("message_count") or 0) != len(messages):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_message_count_invalid")

    conversation = {
        "schema_version": CONVERSATION_SCHEMA_VERSION,
        "source_id": "chatgpt",
        "conversation_id": conversation_id,
        "source_conversation_id": source_conversation_id,
        "title": str(row.get("title") or "Untitled ChatGPT conversation"),
        "created_at": _clean_source_id(row.get("created_at")),
        "updated_at": _clean_source_id(row.get("updated_at")),
        "message_count": len(messages),
        "messages": messages,
        "source_extensions": copy.deepcopy(
            _mapping(
                row.get("source_extensions"),
                "chatgpt_canonical_conversation_extensions_invalid",
            )
        ),
        "redact_for_public_backup": bool(row.get("redact_for_public_backup")),
        "redaction_counts": copy.deepcopy(
            _mapping(
                row.get("redaction_counts"),
                "chatgpt_canonical_redaction_counts_invalid",
            )
        ),
    }
    version_sha256 = _sha256(conversation)
    version_id = f"chatgpt-version-{version_sha256[:32]}"
    return {
        "schema_version": EVENT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": "chatgpt",
        "event_type": "conversation_version",
        "event_id": f"chatgpt-event-{version_sha256[:32]}",
        "conversation_id": conversation_id,
        "source_conversation_id": source_conversation_id,
        "version_id": version_id,
        "version_number": 0,
        "version_sha256": version_sha256,
        "previous_version_id": None,
        "raw_ref": _repository_relative_raw_ref(raw_ref),
        "raw_content_sha256": _require_sha256(
            row.get("content_sha256"),
            "chatgpt_canonical_raw_hash_invalid",
        ),
        "export_sha256": _require_sha256(
            export_sha256,
            "chatgpt_canonical_export_hash_invalid",
        ),
        "observed_at": _clean_source_id(observed_at),
        "parser_provenance": copy.deepcopy(
            _mapping(
                row.get("parser_provenance"),
                "chatgpt_canonical_parser_provenance_invalid",
            )
        ),
        "conversation": conversation,
    }


_EVENT_FIELDS = {
    "schema_version",
    "task_id",
    "acceptance_id",
    "source_id",
    "event_type",
    "event_id",
    "conversation_id",
    "source_conversation_id",
    "version_id",
    "version_number",
    "version_sha256",
    "previous_version_id",
    "raw_ref",
    "raw_content_sha256",
    "export_sha256",
    "observed_at",
    "parser_provenance",
    "conversation",
}


def _validate_message(message: Any, conversation_id: str) -> dict[str, Any]:
    payload = _mapping(message, "chatgpt_canonical_ledger_message_invalid")
    expected_fields = {
        "schema_version",
        "message_id",
        "source_message_id",
        "role",
        "created_at",
        "text",
        "attachments",
        "source_extensions",
        "author_extensions",
        "content_extensions",
        "message_sha256",
    }
    if set(payload) != expected_fields or payload.get("schema_version") != MESSAGE_SCHEMA_VERSION:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_message_invalid")
    expected_id = _stable_id(
        "message",
        {
            "conversation_id": conversation_id,
            "source_message_id": _clean_source_id(payload.get("source_message_id")),
        },
    )
    if payload.get("message_id") != expected_id:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_message_identity_invalid")
    content = dict(payload)
    message_sha256 = _require_sha256(
        content.pop("message_sha256"),
        "chatgpt_canonical_ledger_message_hash_invalid",
    )
    if _sha256(content) != message_sha256:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_message_hash_invalid")
    return payload


def _validate_event(event: Any) -> dict[str, Any]:
    payload = _mapping(event, "chatgpt_canonical_ledger_event_invalid")
    if set(payload) != _EVENT_FIELDS:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_event_invalid")
    if (
        payload.get("schema_version") != EVENT_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != "chatgpt"
        or payload.get("event_type") != "conversation_version"
    ):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_event_invalid")
    source_conversation_id = _clean_source_id(payload.get("source_conversation_id"))
    conversation_id = _stable_id(
        "conversation",
        {
            "source_id": "chatgpt",
            "source_conversation_id": source_conversation_id,
        },
    )
    if payload.get("conversation_id") != conversation_id:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_conversation_identity_invalid")
    conversation = _mapping(
        payload.get("conversation"),
        "chatgpt_canonical_ledger_conversation_invalid",
    )
    expected_conversation_fields = {
        "schema_version",
        "source_id",
        "conversation_id",
        "source_conversation_id",
        "title",
        "created_at",
        "updated_at",
        "message_count",
        "messages",
        "source_extensions",
        "redact_for_public_backup",
        "redaction_counts",
    }
    if (
        set(conversation) != expected_conversation_fields
        or conversation.get("schema_version") != CONVERSATION_SCHEMA_VERSION
        or conversation.get("source_id") != "chatgpt"
        or conversation.get("conversation_id") != conversation_id
        or conversation.get("source_conversation_id") != source_conversation_id
    ):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_conversation_invalid")
    messages = _list(
        conversation.get("messages"),
        "chatgpt_canonical_ledger_messages_invalid",
    )
    validated_messages = [_validate_message(message, conversation_id) for message in messages]
    message_ids = [message["message_id"] for message in validated_messages]
    if (
        len(messages) > MAXIMUM_MESSAGES_PER_CONVERSATION
        or int(conversation.get("message_count") or 0) != len(messages)
        or len(message_ids) != len(set(message_ids))
    ):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_messages_invalid")
    version_sha256 = _require_sha256(
        payload.get("version_sha256"),
        "chatgpt_canonical_ledger_version_hash_invalid",
    )
    if _sha256(conversation) != version_sha256:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_version_hash_invalid")
    if payload.get("version_id") != f"chatgpt-version-{version_sha256[:32]}":
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_version_identity_invalid")
    if payload.get("event_id") != f"chatgpt-event-{version_sha256[:32]}":
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_event_identity_invalid")
    if not isinstance(payload.get("version_number"), int) or payload["version_number"] < 1:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_version_number_invalid")
    previous = payload.get("previous_version_id")
    if previous is not None and not isinstance(previous, str):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_previous_version_invalid")
    _repository_relative_raw_ref(payload.get("raw_ref"))
    _require_sha256(
        payload.get("raw_content_sha256"),
        "chatgpt_canonical_ledger_raw_hash_invalid",
    )
    _require_sha256(
        payload.get("export_sha256"),
        "chatgpt_canonical_ledger_export_hash_invalid",
    )
    if not _clean_source_id(payload.get("observed_at")):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_observed_at_invalid")
    _mapping(
        payload.get("parser_provenance"),
        "chatgpt_canonical_ledger_parser_provenance_invalid",
    )
    return payload


def _read_ledger(database_dir: Path) -> tuple[bytes, list[dict[str, Any]]]:
    path = database_dir / EVENTS_RELATIVE
    if not path.exists():
        return b"", []
    raw = _read_regular_bytes(
        path,
        maximum_bytes=MAXIMUM_LEDGER_BYTES,
        code="chatgpt_canonical_ledger_invalid",
    )
    if raw and not raw.endswith(b"\n"):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_invalid")
    events: list[dict[str, Any]] = []
    for line in raw.splitlines():
        try:
            decoded = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_invalid") from exc
        events.append(_validate_event(decoded))
        if len(events) > MAXIMUM_LEDGER_EVENTS:
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_event_limit_exceeded")

    histories: dict[str, list[dict[str, Any]]] = {}
    version_ids: set[str] = set()
    event_ids: set[str] = set()
    for event in events:
        version_id = str(event["version_id"])
        event_id = str(event["event_id"])
        if version_id in version_ids or event_id in event_ids:
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_identity_duplicate")
        version_ids.add(version_id)
        event_ids.add(event_id)
        history = histories.setdefault(str(event["conversation_id"]), [])
        expected_number = len(history) + 1
        expected_previous = history[-1]["version_id"] if history else None
        if (
            event["version_number"] != expected_number
            or event["previous_version_id"] != expected_previous
        ):
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_chain_invalid")
        history.append(event)
    return raw, events


def plan_chatgpt_canonical_events(
    database_dir: Path,
    rows: Iterable[dict[str, Any]],
    raw_paths: Iterable[Path],
    *,
    export_sha256: str,
    observed_at: str,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    normalized_rows = list(rows)
    normalized_paths = [Path(path) for path in raw_paths]
    if len(normalized_rows) != len(normalized_paths):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_input_alignment_invalid")
    existing_bytes, existing_events = _read_ledger(root)
    histories: dict[str, list[dict[str, Any]]] = {}
    versions: dict[str, dict[str, Any]] = {}
    for event in existing_events:
        histories.setdefault(str(event["conversation_id"]), []).append(event)
        versions[str(event["version_id"])] = event

    append_events: list[dict[str, Any]] = []
    unchanged_version_count = 0
    for row, raw_path in zip(normalized_rows, normalized_paths):
        event = build_chatgpt_canonical_event(
            row,
            raw_ref=raw_path.as_posix(),
            export_sha256=export_sha256,
            observed_at=observed_at,
        )
        version_id = str(event["version_id"])
        existing = versions.get(version_id)
        if existing is not None:
            if existing["conversation_id"] != event["conversation_id"]:
                raise ChatGPTCanonicalEventError("chatgpt_canonical_version_identity_conflict")
            unchanged_version_count += 1
            continue
        history = histories.setdefault(str(event["conversation_id"]), [])
        event["version_number"] = len(history) + 1
        event["previous_version_id"] = history[-1]["version_id"] if history else None
        validated = _validate_event(event)
        history.append(validated)
        versions[version_id] = validated
        append_events.append(validated)
        if len(existing_events) + len(append_events) > MAXIMUM_LEDGER_EVENTS:
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_event_limit_exceeded")

    return {
        "schema_version": PLAN_SCHEMA_VERSION,
        "events_path": EVENTS_RELATIVE.as_posix(),
        "existing_ledger_sha256": _sha256(existing_bytes),
        "existing_event_count": len(existing_events),
        "appended_version_count": len(append_events),
        "unchanged_version_count": unchanged_version_count,
        "event_count_after": len(existing_events) + len(append_events),
        "append_events": append_events,
    }


def _current_ledger_bytes(root: Path) -> bytes:
    raw, _ = _read_ledger(root)
    return raw


def _safe_output_path(root: Path) -> Path:
    target = root / EVENTS_RELATIVE
    target.parent.mkdir(parents=True, exist_ok=True)
    resolved_parent = target.parent.resolve()
    if root != resolved_parent and root not in resolved_parent.parents:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_output_path_invalid")
    if target.exists() and target.is_symlink():
        raise ChatGPTCanonicalEventError("chatgpt_canonical_output_path_invalid")
    return target


def commit_chatgpt_canonical_events(
    database_dir: Path,
    plan: dict[str, Any],
) -> dict[str, Any]:
    root = _database_root(database_dir)
    if not isinstance(plan, dict) or plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_plan_invalid")
    append_events = plan.get("append_events")
    if not isinstance(append_events, list):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_plan_invalid")
    current_bytes = _current_ledger_bytes(root)
    if _sha256(current_bytes) != plan.get("existing_ledger_sha256"):
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_changed")
    if not append_events:
        return {
            "status": "NO_CHANGES",
            "events_path": EVENTS_RELATIVE.as_posix(),
            "appended_version_count": 0,
            "unchanged_version_count": int(plan.get("unchanged_version_count") or 0),
            "event_count": int(plan.get("existing_event_count") or 0),
            "writes_files": False,
            "append_only": True,
        }

    serialized = b"".join(_canonical_bytes(_validate_event(event)) + b"\n" for event in append_events)
    output = current_bytes + serialized
    if len(output) > MAXIMUM_LEDGER_BYTES:
        raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_size_exceeded")
    target = _safe_output_path(root)
    temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
    try:
        with temp.open("xb") as handle:
            handle.write(output)
            handle.flush()
            os.fsync(handle.fileno())
        if _current_ledger_bytes(root) != current_bytes:
            raise ChatGPTCanonicalEventError("chatgpt_canonical_ledger_changed")
        os.replace(temp, target)
    except ChatGPTCanonicalEventError:
        raise
    except OSError as exc:
        raise ChatGPTCanonicalEventError(
            "chatgpt_canonical_ledger_write_failed",
            writes_files=target.exists(),
        ) from exc
    finally:
        if temp.exists():
            temp.unlink()
    return {
        "status": "APPENDED",
        "events_path": EVENTS_RELATIVE.as_posix(),
        "appended_version_count": len(append_events),
        "unchanged_version_count": int(plan.get("unchanged_version_count") or 0),
        "event_count": int(plan.get("event_count_after") or 0),
        "writes_files": True,
        "append_only": True,
    }


def canonical_plan_result(plan: dict[str, Any], *, dry_run: bool) -> dict[str, Any]:
    return {
        "status": "PLANNED" if plan["appended_version_count"] else "NO_CHANGES",
        "events_path": EVENTS_RELATIVE.as_posix(),
        "appended_version_count": int(plan["appended_version_count"]),
        "unchanged_version_count": int(plan["unchanged_version_count"]),
        "event_count": int(plan["event_count_after"]),
        "writes_files": False,
        "append_only": True,
        "dry_run": dry_run,
    }


__all__ = [
    "EVENTS_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "ChatGPTCanonicalEventError",
    "build_chatgpt_canonical_event",
    "canonical_plan_result",
    "commit_chatgpt_canonical_events",
    "load_chatgpt_canonical_event_contract",
    "load_chatgpt_canonical_event_model_parameters",
    "plan_chatgpt_canonical_events",
    "stable_source_conversation_id",
    "validate_chatgpt_canonical_event_contract",
    "validate_chatgpt_canonical_event_model_parameters",
]
