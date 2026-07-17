"""Read-only, loss-aware parser for ChatGPT export JSON variants."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_parser.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_parser.v1_2_1_s09_p1_t1.json"
)
QUARANTINE_RELATIVE = Path(
    "data/processed/conversations/chatgpt_parse_quarantine.jsonl"
)

TASK_ID = "S09-P1-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P1-T1"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_parser_contract.v1_2_1_s09_p1_t1"
)
MODEL_SCHEMA_VERSION = "memory_atlas.chatgpt_export_parser_model.v1_2_1_s09_p1_t1"
REPORT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_parser_report.v1_2_1_s09_p1_t1"
)

MAXIMUM_JSON_FILES = 10_000
MAXIMUM_JSON_BYTES = 512 * 1024 * 1024
MAXIMUM_TOTAL_JSON_BYTES = 4 * 1024 * 1024 * 1024
MAXIMUM_CONVERSATIONS = 2_000_000
MAXIMUM_CONTRACT_BYTES = 128 * 1024
READ_CHUNK_BYTES = 1024 * 1024

_NUMBERED_JSON_RE = re.compile(r"^(?:conversation[_-]?)?\d+\.json$", re.I)
_METADATA_JSON_RE = re.compile(
    r"^(?:metadata|export_metadata|attachments)(?:[_-].*)?\.json$", re.I
)
_ATTACHMENT_KEYS = {
    "asset_pointer",
    "attachment_id",
    "file_id",
    "file_name",
    "mime_type",
    "size_bytes",
}

PHASE_BOUNDARY = {
    "implements_incremental_ids": False,
    "implements_version_history": False,
    "implements_derived_facets": False,
    "mutates_source": False,
    "next_task": "S09-P1-T2",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "inputs": {
        "supported": ["json_file", "json_directory", "zip_archive"],
        "canonical_names": ["conversations*.json"],
        "numbered_names": ["<number>.json", "conversation_<number>.json"],
        "future_container_keys": ["data", "items"],
        "metadata_names": ["metadata*.json", "export_metadata*.json", "attachments*.json"],
    },
    "unknown_fields": {
        "preserve": True,
        "conversation_payload_preserved": True,
        "message_payload_preserved": True,
        "attachment_payload_preserved": True,
        "metadata_payload_preserved": True,
    },
    "quarantine": {
        "path": QUARANTINE_RELATIVE.as_posix(),
        "every_unparseable_item_required": True,
        "raw_payload_forbidden": True,
        "payload_sha256_required": True,
        "field_names_allowed": True,
    },
    "security": {
        "source_read_only": True,
        "source_symlinks_allowed": False,
        "zip_path_traversal_allowed": False,
        "quarantine_copies_private_values": False,
        "remote_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S09-P1-T1",
    "formula_id": "FORM-MA-V121-S09-P1-T1",
    "purpose": "Parse recognizable ChatGPT export variants without silently dropping unknown fields or malformed items.",
    "limits": {
        "maximum_json_files": MAXIMUM_JSON_FILES,
        "maximum_json_bytes": MAXIMUM_JSON_BYTES,
        "maximum_total_json_bytes": MAXIMUM_TOTAL_JSON_BYTES,
        "maximum_conversations": MAXIMUM_CONVERSATIONS,
        "maximum_contract_bytes": MAXIMUM_CONTRACT_BYTES,
        "read_chunk_bytes": READ_CHUNK_BYTES,
    },
    "formulas": {
        "payload_identity": "sha256(canonical_json_or_source_bytes)",
        "attachment_count": "sum(recognized_dict_parts_in_message_content)",
        "status": "PASS if conversation_count>0 and quarantine_count=0 else PASS_WITH_QUARANTINE if conversation_count>0 else QUARANTINED if quarantine_count>0 else NO_CONVERSATIONS",
    },
    "invariants": [
        "source bytes are never modified",
        "recognized payloads retain unknown fields",
        "every rejected JSON file, conversation item, mapping node, or message has one sanitized quarantine record",
        "quarantine records never contain raw payload values",
        "stable IDs, version history, deduplication, and derived facets remain outside this task",
    ],
    "phase_boundary": PHASE_BOUNDARY,
}


class ChatGPTExportParserError(ValueError):
    """Raised when parser inputs or canonical contracts fail closed."""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _payload_sha256(value: Any) -> str:
    payload = value if isinstance(value, bytes) else _canonical_bytes(value)
    return hashlib.sha256(payload).hexdigest()


def _database_root(database_dir: Path) -> Path:
    root = Path(database_dir).expanduser()
    if root.is_symlink() or not root.is_dir():
        raise ChatGPTExportParserError("chatgpt_parser_database_invalid")
    return root.resolve()


def _read_regular_bytes(path: Path, *, maximum_bytes: int, code: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ChatGPTExportParserError(code) from exc
    if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
        raise ChatGPTExportParserError(code)
    if metadata.st_size > maximum_bytes:
        raise ChatGPTExportParserError(code)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise ChatGPTExportParserError(code) from exc
    if len(payload) > maximum_bytes:
        raise ChatGPTExportParserError(code)
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
        raise ChatGPTExportParserError(code) from exc
    if not isinstance(payload, dict):
        raise ChatGPTExportParserError(code)
    return payload


def validate_chatgpt_export_parser_contract(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_CONTRACT:
        raise ChatGPTExportParserError("chatgpt_parser_contract_drift")
    return dict(payload)


def validate_chatgpt_export_parser_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTExportParserError("chatgpt_parser_model_drift")
    return dict(payload)


def load_chatgpt_export_parser_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_parser_contract(
        _read_contract_json(
            root / CONTRACT_RELATIVE,
            code="chatgpt_parser_contract_invalid",
        )
    )


def load_chatgpt_export_parser_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_parser_model_parameters(
        _read_contract_json(
            root / MODEL_RELATIVE,
            code="chatgpt_parser_model_invalid",
        )
    )


def _field_names(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    return sorted(str(key) for key in value)


def _quarantine_row(
    *,
    source_ref: str,
    reason_code: str,
    value: Any,
    item_index: int | None = None,
    location: str = "",
) -> dict[str, Any]:
    row: dict[str, Any] = {
        "schema_version": REPORT_SCHEMA_VERSION,
        "source_ref": source_ref,
        "reason_code": reason_code,
        "value_type": type(value).__name__,
        "field_names": _field_names(value),
        "payload_sha256": _payload_sha256(value),
    }
    if item_index is not None:
        row["item_index"] = item_index
    if location:
        row["location"] = location
    return row


def _looks_like_conversation(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    return isinstance(value.get("mapping"), dict) or isinstance(
        value.get("messages"), list
    )


def _is_attachment_part(value: Any) -> bool:
    if not isinstance(value, dict):
        return False
    content_type = str(value.get("content_type") or "").lower()
    return bool(
        _ATTACHMENT_KEYS.intersection(value)
        or any(marker in content_type for marker in ("asset", "image", "file", "audio", "video"))
    )


def _conversation_attachment_count(conversation: dict[str, Any]) -> int:
    messages: list[dict[str, Any]] = []
    mapping = conversation.get("mapping")
    if isinstance(mapping, dict):
        for node in mapping.values():
            if isinstance(node, dict) and isinstance(node.get("message"), dict):
                messages.append(node["message"])
    direct_messages = conversation.get("messages")
    if isinstance(direct_messages, list):
        messages.extend(row for row in direct_messages if isinstance(row, dict))

    count = 0
    for message in messages:
        content = message.get("content")
        if not isinstance(content, dict):
            continue
        parts = content.get("parts")
        if isinstance(parts, list):
            count += sum(1 for part in parts if _is_attachment_part(part))
    return count


def _message_shape_quarantine(
    conversation: dict[str, Any],
    *,
    source_ref: str,
    item_index: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mapping = conversation.get("mapping")
    if isinstance(mapping, dict):
        for mapping_index, node in enumerate(mapping.values()):
            if not isinstance(node, dict):
                rows.append(
                    _quarantine_row(
                        source_ref=source_ref,
                        reason_code="mapping_node_not_object",
                        value=node,
                        item_index=item_index,
                        location=f"mapping[{mapping_index}]",
                    )
                )
                continue
            message = node.get("message")
            if message is not None and not isinstance(message, dict):
                rows.append(
                    _quarantine_row(
                        source_ref=source_ref,
                        reason_code="mapping_message_not_object",
                        value=message,
                        item_index=item_index,
                        location=f"mapping[{mapping_index}].message",
                    )
                )
    messages = conversation.get("messages")
    if isinstance(messages, list):
        for message_index, message in enumerate(messages):
            if not isinstance(message, dict):
                rows.append(
                    _quarantine_row(
                        source_ref=source_ref,
                        reason_code="message_not_object",
                        value=message,
                        item_index=item_index,
                        location=f"messages[{message_index}]",
                    )
                )
    return rows


def _parse_conversation_items(
    items: list[Any],
    *,
    source_ref: str,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    conversations: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    attachment_count = 0
    for item_index, item in enumerate(items):
        if not isinstance(item, dict):
            quarantine.append(
                _quarantine_row(
                    source_ref=source_ref,
                    reason_code="conversation_not_object",
                    value=item,
                    item_index=item_index,
                )
            )
            continue
        if not _looks_like_conversation(item):
            quarantine.append(
                _quarantine_row(
                    source_ref=source_ref,
                    reason_code="conversation_shape_unrecognized",
                    value=item,
                    item_index=item_index,
                )
            )
            continue
        parsed = copy.deepcopy(item)
        current_attachment_count = _conversation_attachment_count(parsed)
        provenance: dict[str, Any] = {
            "schema_version": REPORT_SCHEMA_VERSION,
            "source_ref": source_ref,
            "item_index": item_index,
            "attachment_count": current_attachment_count,
        }
        if "_memory_atlas_parser" in parsed:
            provenance["source_field_preserved"] = parsed["_memory_atlas_parser"]
        parsed["_memory_atlas_parser"] = provenance
        conversations.append(parsed)
        attachment_count += current_attachment_count
        quarantine.extend(
            _message_shape_quarantine(
                parsed,
                source_ref=source_ref,
                item_index=item_index,
            )
        )
        if len(conversations) > MAXIMUM_CONVERSATIONS:
            raise ChatGPTExportParserError("chatgpt_parser_conversation_limit_exceeded")
    return conversations, quarantine, attachment_count


def _metadata_payload(
    payload: Any,
    *,
    source_ref: str,
) -> dict[str, Any]:
    return {
        "source_ref": source_ref,
        "payload": copy.deepcopy(payload),
        "payload_sha256": _payload_sha256(payload),
    }


def _decode_json(payload: bytes) -> Any:
    return json.loads(payload.decode("utf-8"))


def _parse_json_payload(
    payload: Any,
    *,
    source_ref: str,
    filename: str,
) -> dict[str, Any]:
    if _METADATA_JSON_RE.fullmatch(filename):
        return {
            "format": "export_metadata",
            "conversations": [],
            "quarantine": [],
            "attachment_count": 0,
            "metadata": [_metadata_payload(payload, source_ref=source_ref)],
        }

    format_name = ""
    items: list[Any] | None = None
    container_key = ""
    if isinstance(payload, list) and filename.lower().startswith("conversations"):
        format_name = "canonical_conversations"
        items = payload
    elif isinstance(payload, list) and any(
        _looks_like_conversation(item) for item in payload
    ):
        format_name = "future_recognizable_list"
        items = payload
    elif isinstance(payload, dict) and isinstance(payload.get("conversations"), list):
        format_name = "canonical_conversations"
        items = payload["conversations"]
        container_key = "conversations"
    elif isinstance(payload, dict):
        for key in ("data", "items"):
            if isinstance(payload.get(key), list):
                format_name = "future_recognizable_container"
                items = payload[key]
                container_key = key
                break
    if items is None and _looks_like_conversation(payload):
        format_name = (
            "numbered_conversation"
            if _NUMBERED_JSON_RE.fullmatch(filename)
            else "single_conversation"
        )
        items = [payload]

    if items is None:
        reason_code = (
            "conversation_shape_unrecognized"
            if _NUMBERED_JSON_RE.fullmatch(filename)
            or filename.lower().startswith("conversations")
            else "json_file_unrecognized"
        )
        return {
            "format": "unrecognized",
            "conversations": [],
            "quarantine": [
                _quarantine_row(
                    source_ref=source_ref,
                    reason_code=reason_code,
                    value=payload,
                )
            ],
            "attachment_count": 0,
            "metadata": [],
        }

    conversations, quarantine, attachment_count = _parse_conversation_items(
        items,
        source_ref=source_ref,
    )
    metadata: list[dict[str, Any]] = []
    if container_key:
        container_extensions = {
            key: value for key, value in payload.items() if key != container_key
        }
        if container_extensions:
            metadata.append(
                _metadata_payload(container_extensions, source_ref=source_ref)
            )
    return {
        "format": format_name,
        "conversations": conversations,
        "quarantine": quarantine,
        "attachment_count": attachment_count,
        "metadata": metadata,
    }


def _json_file_payloads(source: Path) -> list[tuple[str, bytes]]:
    if source.is_symlink():
        raise ChatGPTExportParserError("chatgpt_parser_source_symlink_rejected")
    if source.is_dir():
        candidates = sorted(
            (path for path in source.glob("**/*.json") if path.is_file()),
            key=lambda path: path.relative_to(source).as_posix(),
        )
        if len(candidates) > MAXIMUM_JSON_FILES:
            raise ChatGPTExportParserError("chatgpt_parser_file_limit_exceeded")
        rows: list[tuple[str, bytes]] = []
        total_bytes = 0
        for candidate in candidates:
            if candidate.is_symlink():
                raise ChatGPTExportParserError("chatgpt_parser_source_symlink_rejected")
            payload = _read_regular_bytes(
                candidate,
                maximum_bytes=MAXIMUM_JSON_BYTES,
                code="chatgpt_parser_json_file_invalid",
            )
            total_bytes += len(payload)
            if total_bytes > MAXIMUM_TOTAL_JSON_BYTES:
                raise ChatGPTExportParserError("chatgpt_parser_total_bytes_exceeded")
            rows.append((candidate.relative_to(source).as_posix(), payload))
        return rows
    if not source.is_file():
        raise ChatGPTExportParserError("chatgpt_parser_source_invalid")
    return [
        (
            source.name,
            _read_regular_bytes(
                source,
                maximum_bytes=MAXIMUM_JSON_BYTES,
                code="chatgpt_parser_json_file_invalid",
            ),
        )
    ]


def _zip_json_payloads(source: Path) -> list[tuple[str, bytes]]:
    if source.is_symlink():
        raise ChatGPTExportParserError("chatgpt_parser_source_symlink_rejected")
    rows: list[tuple[str, bytes]] = []
    total_bytes = 0
    try:
        with zipfile.ZipFile(source) as archive:
            members = sorted(
                (
                    member
                    for member in archive.infolist()
                    if not member.is_dir()
                    and PurePosixPath(member.filename).suffix.lower() == ".json"
                ),
                key=lambda member: member.filename,
            )
            if len(members) > MAXIMUM_JSON_FILES:
                raise ChatGPTExportParserError("chatgpt_parser_file_limit_exceeded")
            for member in members:
                member_path = PurePosixPath(member.filename)
                if member_path.is_absolute() or ".." in member_path.parts:
                    raise ChatGPTExportParserError("chatgpt_parser_zip_path_invalid")
                if member.flag_bits & 0x1:
                    raise ChatGPTExportParserError("chatgpt_parser_zip_encrypted")
                if member.file_size > MAXIMUM_JSON_BYTES:
                    raise ChatGPTExportParserError("chatgpt_parser_json_file_invalid")
                payload = archive.read(member)
                if len(payload) != member.file_size:
                    raise ChatGPTExportParserError("chatgpt_parser_zip_member_truncated")
                total_bytes += len(payload)
                if total_bytes > MAXIMUM_TOTAL_JSON_BYTES:
                    raise ChatGPTExportParserError(
                        "chatgpt_parser_total_bytes_exceeded"
                    )
                rows.append((member.filename, payload))
    except ChatGPTExportParserError:
        raise
    except (OSError, zipfile.BadZipFile, RuntimeError) as exc:
        raise ChatGPTExportParserError("chatgpt_parser_zip_invalid") from exc
    return rows


def parse_chatgpt_export(source: Path) -> dict[str, Any]:
    """Parse a JSON file, directory, or ZIP without mutating source bytes."""

    source = Path(source).expanduser().absolute()
    if source.suffix.lower() == ".zip" and source.is_file():
        payloads = _zip_json_payloads(source)
        source_kind = "zip_archive"
    else:
        payloads = _json_file_payloads(source)
        source_kind = "json_directory" if source.is_dir() else "json_file"
    if not payloads:
        raise ChatGPTExportParserError("chatgpt_parser_no_json_inputs")

    conversations: list[dict[str, Any]] = []
    quarantine: list[dict[str, Any]] = []
    export_metadata: list[dict[str, Any]] = []
    source_files: list[dict[str, Any]] = []
    attachment_count = 0

    for source_ref, raw_payload in payloads:
        try:
            decoded = _decode_json(raw_payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            quarantine.append(
                _quarantine_row(
                    source_ref=source_ref,
                    reason_code="json_decode_failed",
                    value=raw_payload,
                )
            )
            source_files.append(
                {
                    "source_ref": source_ref,
                    "format": "invalid_json",
                    "payload_sha256": _payload_sha256(raw_payload),
                    "conversation_count": 0,
                }
            )
            continue

        parsed = _parse_json_payload(
            decoded,
            source_ref=source_ref,
            filename=PurePosixPath(source_ref).name,
        )
        conversations.extend(parsed["conversations"])
        quarantine.extend(parsed["quarantine"])
        export_metadata.extend(parsed["metadata"])
        attachment_count += int(parsed["attachment_count"])
        source_files.append(
            {
                "source_ref": source_ref,
                "format": parsed["format"],
                "payload_sha256": _payload_sha256(raw_payload),
                "conversation_count": len(parsed["conversations"]),
            }
        )

    if conversations:
        status = "PASS_WITH_QUARANTINE" if quarantine else "PASS"
    else:
        status = "QUARANTINED" if quarantine else "NO_CONVERSATIONS"
    return {
        "schema_version": REPORT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "status": status,
        "source_kind": source_kind,
        "conversation_count": len(conversations),
        "attachment_count": attachment_count,
        "metadata_count": len(export_metadata),
        "quarantine_count": len(quarantine),
        "conversations": conversations,
        "export_metadata": export_metadata,
        "quarantine": quarantine,
        "source_files": source_files,
        "source_read_only": True,
        "phase_boundary": PHASE_BOUNDARY,
    }
