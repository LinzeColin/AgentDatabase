"""Build traceable ChatGPT derived inputs from canonical events and public raw."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import stat
import tempfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterable, Iterator

from extract_memory_atlas_facets import (
    detect_language,
    infer_friction,
    infer_intent,
    infer_output_type,
    infer_project,
    infer_risk_signals,
    infer_value_signals,
)
from privacy_guard import LOCAL_ABSOLUTE_PATH_RE, credential_exclusion_hits
from sync_codex_memory_data import TOPIC_RULES, parse_time, redact_text

from memory_atlas_cli.chatgpt_canonical_events import (
    EVENTS_RELATIVE,
    ChatGPTCanonicalEventError,
    build_chatgpt_canonical_event,
    load_chatgpt_canonical_events,
)


CONTRACT_PATH = Path("config/data_sources/chatgpt_derived.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/chatgpt_derived.v1_2_1_s09_p1_t3.json"
)
SCHEMA_VERSION = "memory_atlas.chatgpt_derived_contract.v1_2_1_s09_p1_t3"
MODEL_SCHEMA_VERSION = "memory_atlas.chatgpt_derived_model.v1_2_1_s09_p1_t3"
STATE_SCHEMA_VERSION = "memory_atlas.chatgpt_derived_state.v1_2_1_s09_p1_t3"
FACET_SCHEMA_VERSION = "memory_atlas.chatgpt_derived_facet.v1_2_1_s09_p1_t3"
TOPICS_SCHEMA_VERSION = "memory_atlas.chatgpt_topics.v1_2_1_s09_p1_t3"
ACTIVITY_SCHEMA_VERSION = "memory_atlas.chatgpt_activity.v1_2_1_s09_p1_t3"
TASK_ID = "S09-P1-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P1-T3"
SOURCE_ID = "chatgpt"
RAW_ROOT = Path("data/public_raw/chatgpt")
MODEL_PARAMETERS_REF = MODEL_PARAMETERS_PATH.as_posix()

EXPECTED_OUTPUTS = {
    "facets": "data/derived/chatgpt/chatgpt_facets.jsonl",
    "topics": "data/derived/chatgpt/chatgpt_topics.json",
    "activity": "data/derived/chatgpt/chatgpt_activity.jsonl",
    "universe_state_input": "data/derived/chatgpt/chatgpt_universe_state_input.json",
    "state": "data/derived/chatgpt/chatgpt_derived_state.json",
}
EXPECTED_PHASE_BOUNDARY = {
    "does_not_modify_raw": True,
    "does_not_modify_canonical_events": True,
    "does_not_update_atlas_snapshot": True,
    "does_not_update_ui": True,
    "does_not_implement_generic_agent_adapter": True,
    "does_not_commit_or_push": True,
    "does_not_deploy": True,
    "next_task": "S09-P2-T1",
}
EXPECTED_CONTRACT = {
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "inputs": {
        "canonical_event_ledger": EVENTS_RELATIVE.as_posix(),
        "canonical_event_contract_ref": "config/data_sources/chatgpt_canonical_events.json",
        "public_raw_root": RAW_ROOT.as_posix(),
        "source_read_only": True,
        "canonical_read_only": True,
        "validated_canonical_ledger_required": True,
    },
    "raw_evidence": {
        "required": True,
        "repository_relative_ref_required": True,
        "regular_file_required": True,
        "raw_content_sha256_required": True,
        "raw_file_sha256_recorded": True,
        "canonical_rebuild_match_required": True,
        "evidence_ref_types": ["raw", "canonical_event"],
    },
    "derivation": {
        "facet_scope": "latest_canonical_version_per_conversation",
        "topic_scope": "latest_canonical_version_per_conversation",
        "activity_scope": "all_canonical_version_events",
        "universe_scope": "latest_topic_clusters",
        "message_text_usage": "transient_classification_only",
        "message_text_persisted": False,
        "deterministic_from_validated_inputs": True,
    },
    "outputs": EXPECTED_OUTPUTS,
    "incremental": {
        "canonical_ledger_must_remain_append_only": True,
        "exact_repeat_no_write": True,
        "changed_ledger_policy": "rebuild_replaceable_derived_projection",
        "missing_or_drifted_output_policy": "rebuild_from_validated_canonical_and_raw",
        "raw_and_canonical_never_modified": True,
    },
    "privacy": {
        "output_policy": "derived_summary_not_full_raw_backup",
        "plaintext_credentials_allowed": False,
        "local_absolute_paths_allowed": False,
        "raw_message_text_persisted": False,
        "frontend_reads_raw": False,
    },
    "model_parameters_ref": MODEL_PARAMETERS_REF,
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}
EXPECTED_MODEL_PARAMETERS = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S09-P1-T3",
    "formula_id": "FORM-MA-V121-S09-P1-T3",
    "purpose": "从已验证的 ChatGPT canonical version ledger 和对应 append-only public raw 生成可追溯 facets、主题、活动与 Universe State 输入。",
    "input_truth": {
        "source": "validated_append_only_canonical_events_plus_public_raw",
        "raw_and_canonical_read_only": True,
        "message_text_used_transiently": True,
        "message_text_persisted_in_derived": False,
    },
    "topic_parameters": {
        "label_source": "first matching shared TOPIC_RULE, else redacted compacted latest conversation title",
        "fallback_label": "unknown_topic",
        "maximum_label_characters": 160,
        "topic_identity": "shared rule id when matched, else sha256(casefolded whitespace-normalized topic label)[0:20]",
        "aggregate_scope": "latest canonical version per conversation",
    },
    "activity_formula": {
        "expression": "message_count + user_message_count*2 + assistant_message_count",
        "coefficients": {
            "message_count": 1,
            "user_message_count": 2,
            "assistant_message_count": 1,
        },
        "semantic_status": "HUMAN_REVIEW_REQUIRED",
    },
    "universe_state_input": {
        "recent_window_days": 45,
        "inactive_normalization_days": 180,
        "confidence_base": 0.5,
        "confidence_max_increment": 0.45,
        "confidence_per_conversation": 0.02,
        "mass_score": "topic_conversation_count / max_topic_conversation_count, clamped 0..1",
        "growth_score": "recent_topic_conversation_count / topic_conversation_count, clamped 0..1",
        "decline_score": "inactive_days / inactive_normalization_days, clamped 0..1",
        "confidence": "confidence_base + min(confidence_max_increment, topic_conversation_count*confidence_per_conversation), clamped 0..1",
        "roi_potential": "conversations_with_value_signal / topic_conversation_count, clamped 0..1",
        "activity_density": "recent_canonical_version_count / recent_window_days, clamped 0..1",
        "semantic_status": "HUMAN_REVIEW_REQUIRED",
    },
    "facet_fallbacks": {
        "topic": "latest title then unknown_topic",
        "intent": "unknown",
        "task_type": "unknown",
        "project": None,
        "output_type": "unknown",
        "language": "unknown",
        "tool": "chatgpt",
        "friction": [],
        "value_signal": [],
    },
    "safety_limits": {
        "maximum_raw_file_bytes": 67_108_864,
        "maximum_classification_characters": 32_768,
        "maximum_evidence_refs_per_aggregate": 4_000_000,
    },
    "privacy_parameters": {
        "backup_policy": "derived_summary_not_full_raw_backup",
        "credential_values_forbidden": True,
        "local_absolute_paths_forbidden": True,
        "message_body_in_output": False,
    },
    "calibration_boundary": "主题分类与活动/Universe State 系数延续现有 MOD-008 工程启发式，仅完成机器可验证输入生成；不声称业务最优或因果解释。",
}


class ChatGPTDerivedError(ValueError):
    """Fail-closed derived-input contract, evidence, or publication error."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _canonical_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise ChatGPTDerivedError("chatgpt_derived_payload_invalid") from exc


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return b"".join(_canonical_bytes(row) + b"\n" for row in rows)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _stable_id(prefix: str, value: Any, length: int = 20) -> str:
    return f"{prefix}-{_sha256(_canonical_bytes(value))[:length]}"


def _database_root(database_dir: Path) -> Path:
    root = Path(database_dir).resolve()
    if not root.is_dir():
        raise ChatGPTDerivedError("chatgpt_derived_database_invalid")
    return root


def _read_regular_bytes(path: Path, *, maximum_bytes: int, code: str) -> bytes:
    try:
        before = path.stat(follow_symlinks=False)
        if not stat.S_ISREG(before.st_mode) or before.st_size > maximum_bytes:
            raise ChatGPTDerivedError(code)
        with path.open("rb") as handle:
            payload = handle.read(maximum_bytes + 1)
            after_handle = os.fstat(handle.fileno())
        after = path.stat(follow_symlinks=False)
    except (FileNotFoundError, OSError) as exc:
        raise ChatGPTDerivedError(code) from exc
    if (
        len(payload) > maximum_bytes
        or before.st_dev != after_handle.st_dev
        or before.st_ino != after_handle.st_ino
        or before.st_size != after_handle.st_size
        or before.st_mtime_ns != after_handle.st_mtime_ns
        or before.st_dev != after.st_dev
        or before.st_ino != after.st_ino
        or before.st_size != after.st_size
        or before.st_mtime_ns != after.st_mtime_ns
    ):
        raise ChatGPTDerivedError(code)
    return payload


def _read_json(path: Path, *, code: str) -> dict[str, Any]:
    payload = _read_regular_bytes(path, maximum_bytes=4 * 1024 * 1024, code=code)
    try:
        decoded = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChatGPTDerivedError(code) from exc
    if not isinstance(decoded, dict):
        raise ChatGPTDerivedError(code)
    return decoded


def validate_chatgpt_derived_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise ChatGPTDerivedError("chatgpt_derived_contract_drift")
    return copy.deepcopy(EXPECTED_CONTRACT)


def validate_chatgpt_derived_model_parameters(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTDerivedError("chatgpt_derived_model_drift")
    return copy.deepcopy(EXPECTED_MODEL_PARAMETERS)


def load_chatgpt_derived_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_derived_contract(
        _read_json(root / CONTRACT_PATH, code="chatgpt_derived_contract_invalid")
    )


def load_chatgpt_derived_model_parameters(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_derived_model_parameters(
        _read_json(
            root / MODEL_PARAMETERS_PATH,
            code="chatgpt_derived_model_invalid",
        )
    )


def _safe_raw_path(root: Path, raw_ref: str) -> Path:
    pure = PurePosixPath(raw_ref)
    if (
        not raw_ref.startswith(f"{RAW_ROOT.as_posix()}/")
        or pure.is_absolute()
        or ".." in pure.parts
        or pure.as_posix() != raw_ref
    ):
        raise ChatGPTDerivedError("chatgpt_derived_raw_ref_invalid")
    path = root / pure
    try:
        resolved = path.resolve(strict=True)
    except (FileNotFoundError, OSError) as exc:
        raise ChatGPTDerivedError("chatgpt_derived_raw_missing") from exc
    if root not in resolved.parents or path.is_symlink() or not path.is_file():
        raise ChatGPTDerivedError("chatgpt_derived_raw_ref_invalid")
    return path


def _raw_content_sha256(payload: dict[str, Any]) -> str:
    value = payload.get("content_sha256")
    if not isinstance(value, str) or len(value) != 64:
        raise ChatGPTDerivedError("chatgpt_derived_raw_content_hash_invalid")
    content = dict(payload)
    content.pop("content_sha256", None)
    if _sha256(_canonical_bytes(content)) != value:
        raise ChatGPTDerivedError("chatgpt_derived_raw_content_hash_invalid")
    return value


def _verify_raw_event(
    root: Path,
    event: dict[str, Any],
    *,
    maximum_raw_bytes: int,
) -> tuple[dict[str, Any], dict[str, Any]]:
    raw_ref = str(event["raw_ref"])
    path = _safe_raw_path(root, raw_ref)
    raw_bytes = _read_regular_bytes(
        path,
        maximum_bytes=maximum_raw_bytes,
        code="chatgpt_derived_raw_invalid",
    )
    try:
        payload = json.loads(raw_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChatGPTDerivedError("chatgpt_derived_raw_invalid") from exc
    if not isinstance(payload, dict):
        raise ChatGPTDerivedError("chatgpt_derived_raw_invalid")
    if _raw_content_sha256(payload) != event["raw_content_sha256"]:
        raise ChatGPTDerivedError("chatgpt_derived_raw_canonical_mismatch")
    try:
        rebuilt = build_chatgpt_canonical_event(
            payload,
            raw_ref=raw_ref,
            export_sha256=str(event["export_sha256"]),
            observed_at=str(event["observed_at"]),
        )
    except ChatGPTCanonicalEventError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_raw_canonical_mismatch") from exc
    for field in (
        "event_id",
        "conversation_id",
        "source_conversation_id",
        "version_id",
        "version_sha256",
        "raw_ref",
        "raw_content_sha256",
        "export_sha256",
        "observed_at",
        "parser_provenance",
        "conversation",
    ):
        if rebuilt[field] != event[field]:
            raise ChatGPTDerivedError("chatgpt_derived_raw_canonical_mismatch")
    evidence = {
        "raw_ref": raw_ref,
        "raw_content_sha256": event["raw_content_sha256"],
        "raw_file_sha256": _sha256(raw_bytes),
        "raw_byte_size": len(raw_bytes),
        "canonical_event_id": event["event_id"],
        "canonical_version_id": event["version_id"],
        "canonical_version_sha256": event["version_sha256"],
    }
    signature = {
        "path": path,
        "size": path.stat(follow_symlinks=False).st_size,
        "mtime_ns": path.stat(follow_symlinks=False).st_mtime_ns,
        "sha256": evidence["raw_file_sha256"],
    }
    return evidence, signature


def _evidence_refs(event: dict[str, Any], raw: dict[str, Any]) -> list[dict[str, Any]]:
    identity = {
        "source_id": SOURCE_ID,
        "record_id": event["conversation_id"],
        "canonical_event_id": event["event_id"],
        "canonical_version_id": event["version_id"],
    }
    return [
        {
            **identity,
            "ref_type": "raw",
            "evidence_level": "verified_append_only_public_raw",
            "path": raw["raw_ref"],
            "content_sha256": raw["raw_content_sha256"],
            "file_sha256": raw["raw_file_sha256"],
            "byte_size": raw["raw_byte_size"],
        },
        {
            **identity,
            "ref_type": "canonical_event",
            "evidence_level": "validated_append_only_canonical_event",
            "path": EVENTS_RELATIVE.as_posix(),
            "version_sha256": event["version_sha256"],
            "version_number": event["version_number"],
        },
    ]


def _latest_events(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    latest: dict[str, dict[str, Any]] = {}
    for event in events:
        latest[str(event["conversation_id"])] = event
    return sorted(
        latest.values(),
        key=lambda row: (str(row["conversation_id"]), int(row["version_number"])),
    )


def _event_time(event: dict[str, Any]) -> datetime:
    conversation = event["conversation"]
    parsed = (
        parse_time(conversation.get("updated_at"))
        or parse_time(conversation.get("created_at"))
        or parse_time(event.get("observed_at"))
    )
    if parsed is None:
        raise ChatGPTDerivedError("chatgpt_derived_timestamp_invalid")
    return parsed


def _topic(event: dict[str, Any], model: dict[str, Any]) -> tuple[str, str]:
    parameters = model["topic_parameters"]
    fallback = str(parameters["fallback_label"])
    maximum = int(parameters["maximum_label_characters"])
    context = _classification_text(event, model).casefold()
    for rule_id, rule_label, keywords in TOPIC_RULES:
        if any(keyword.casefold() in context for keyword in keywords):
            return f"topic-chatgpt-{rule_id}", redact_text(rule_label, maximum)
    title = str(event["conversation"].get("title") or fallback)
    label = redact_text(title, maximum) or fallback
    return _stable_id("topic-chatgpt", label.casefold()), label


def _classification_text(event: dict[str, Any], model: dict[str, Any]) -> str:
    maximum = int(model["safety_limits"]["maximum_classification_characters"])
    conversation = event["conversation"]
    parts = [str(conversation.get("title") or "")]
    length = len(parts[0])
    for message in conversation["messages"]:
        if message.get("role") == "user":
            text = str(message.get("text") or "")
            parts.append(text)
            length += len(text)
        if length >= maximum:
            break
    return " ".join(parts)[:maximum]


def _role_counts(event: dict[str, Any]) -> Counter[str]:
    return Counter(
        str(message.get("role") or "unknown")
        for message in event["conversation"]["messages"]
    )


def _infer_task_type(text: str) -> str:
    lowered = text.lower()
    mappings = (
        ("design", ("ui", "visual", "three.js", "frontend", "design", "设计", "可视化")),
        ("automation", ("automation", "schedule", "sync", "backup", "自动", "同步", "备份")),
        ("engineering", ("code", "script", "test", "validator", "cli", "build", "实现", "开发")),
        ("data", ("data", "database", "memory", "rag", "manifest", "json", "数据", "记忆")),
        ("research", ("research", "调研", "研究")),
        ("writing", ("doc", "report", "write", "文档", "报告", "说明")),
        ("governance", ("review", "audit", "gate", "policy", "验收", "治理", "门禁")),
        ("operations", ("operate", "cleanup", "恢复", "运行", "清理")),
        ("product", ("prd", "mvp", "product", "产品")),
    )
    for task_type, keywords in mappings:
        for keyword in keywords:
            if keyword.isascii():
                pattern = rf"(?<![a-z0-9]){re.escape(keyword)}(?![a-z0-9])"
                if re.search(pattern, lowered):
                    return task_type
            elif keyword in lowered:
                return task_type
    return "unknown"


def _activity_score(event: dict[str, Any], model: dict[str, Any]) -> int:
    roles = _role_counts(event)
    coefficients = model["activity_formula"]["coefficients"]
    return (
        int(event["conversation"]["message_count"])
        * int(coefficients["message_count"])
        + roles["user"] * int(coefficients["user_message_count"])
        + roles["assistant"] * int(coefficients["assistant_message_count"])
    )


def _facet(
    event: dict[str, Any],
    raw: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    topic_id, label = _topic(event, model)
    context = _classification_text(event, model)
    roles = _role_counts(event)
    activity_row = {"activity_score": _activity_score(event, model)}
    return {
        "schema_version": FACET_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "event_id": _stable_id("chatgpt-facet", event["version_id"]),
        "source": SOURCE_ID,
        "source_id": SOURCE_ID,
        "record_id": event["conversation_id"],
        "conversation_id": event["conversation_id"],
        "canonical_event_id": event["event_id"],
        "version_id": event["version_id"],
        "version_number": event["version_number"],
        "occurred_at": _event_time(event).isoformat().replace("+00:00", "Z"),
        "topic_id": topic_id,
        "topic": label,
        "intent": infer_intent(context),
        "task_type": _infer_task_type(context),
        "project": infer_project(context),
        "output_type": infer_output_type(context),
        "language": detect_language(context),
        "tool": SOURCE_ID,
        "turn_count": int(event["conversation"]["message_count"]),
        "user_message_count": roles["user"],
        "assistant_message_count": roles["assistant"],
        "activity_score": activity_row["activity_score"],
        "friction": infer_friction(context, activity_row, None),
        "value_signal": infer_value_signals(context, activity_row),
        "future_agent_source": None,
        "risk_signal": infer_risk_signals(context, activity_row),
        "tools_used": [],
        "confidence": "high",
        "raw_ref": raw["raw_ref"],
        "canonical_event_ref": EVENTS_RELATIVE.as_posix(),
        "evidence_refs": _evidence_refs(event, raw),
        "backup_policy": "derived_summary_not_full_raw_backup",
    }


def _activity(
    event: dict[str, Any],
    raw: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    roles = _role_counts(event)
    topic_id, label = _topic(event, model)
    return {
        "schema_version": ACTIVITY_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "activity_id": _stable_id("chatgpt-activity", event["version_id"]),
        "source_id": SOURCE_ID,
        "record_id": event["conversation_id"],
        "conversation_id": event["conversation_id"],
        "canonical_event_id": event["event_id"],
        "version_id": event["version_id"],
        "version_number": event["version_number"],
        "previous_version_id": event["previous_version_id"],
        "occurred_at": _event_time(event).isoformat().replace("+00:00", "Z"),
        "topic_id": topic_id,
        "topic": label,
        "message_count": int(event["conversation"]["message_count"]),
        "user_message_count": roles["user"],
        "assistant_message_count": roles["assistant"],
        "activity_score": _activity_score(event, model),
        "raw_ref": raw["raw_ref"],
        "canonical_event_ref": EVENTS_RELATIVE.as_posix(),
        "evidence_refs": _evidence_refs(event, raw),
    }


def _dedupe_refs(refs: Iterable[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: dict[tuple[str, str, str], dict[str, Any]] = {}
    for ref in refs:
        key = (
            str(ref["ref_type"]),
            str(ref["canonical_event_id"]),
            str(ref["path"]),
        )
        deduped[key] = ref
    return [deduped[key] for key in sorted(deduped)]


def _topics(
    facets: list[dict[str, Any]],
    *,
    maximum_evidence_refs: int,
) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for facet in facets:
        grouped[str(facet["topic_id"])].append(facet)
    maximum_count = max((len(rows) for rows in grouped.values()), default=1)
    topics: list[dict[str, Any]] = []
    for topic_id, rows in grouped.items():
        evidence_refs = _dedupe_refs(
            ref for row in rows for ref in row["evidence_refs"]
        )
        if len(evidence_refs) > maximum_evidence_refs:
            raise ChatGPTDerivedError("chatgpt_derived_evidence_limit_exceeded")
        latest = max(str(row["occurred_at"]) for row in rows)
        topics.append(
            {
                "topic_id": topic_id,
                "label": rows[0]["topic"],
                "source_id": SOURCE_ID,
                "conversation_count": len(rows),
                "message_count": sum(int(row["turn_count"]) for row in rows),
                "activity_score": sum(int(row["activity_score"]) for row in rows),
                "latest_signal_at": latest,
                "mass_score": round(len(rows) / maximum_count, 6),
                "value_signal_count": sum(bool(row["value_signal"]) for row in rows),
                "evidence_refs": evidence_refs,
            }
        )
    return sorted(topics, key=lambda row: (-int(row["conversation_count"]), str(row["topic_id"])))


def _clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _universe_input(
    topics: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    activities: list[dict[str, Any]],
    generated_at: str,
    model: dict[str, Any],
    model_sha256: str,
    ledger_sha256: str,
) -> dict[str, Any]:
    generated = parse_time(generated_at)
    if generated is None:
        raise ChatGPTDerivedError("chatgpt_derived_timestamp_invalid")
    parameters = model["universe_state_input"]
    recent_window_days = int(parameters["recent_window_days"])
    inactive_normalization_days = int(parameters["inactive_normalization_days"])
    recent_start = generated - timedelta(days=recent_window_days)
    facets_by_topic: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for facet in facets:
        facets_by_topic[str(facet["topic_id"])].append(facet)
    clusters: list[dict[str, Any]] = []
    for topic in topics:
        rows = facets_by_topic[str(topic["topic_id"])]
        latest = max(parse_time(row["occurred_at"]) or generated for row in rows)
        recent_rows = [
            row
            for row in rows
            if (parse_time(row["occurred_at"]) or datetime.min.replace(tzinfo=timezone.utc))
            >= recent_start
        ]
        inactive_days = max(0, (generated.date() - latest.date()).days)
        conversation_count = int(topic["conversation_count"])
        clusters.append(
            {
                "cluster_id": _stable_id("cluster-chatgpt", topic["topic_id"], 12),
                "label": topic["label"],
                "theme_id": topic["topic_id"],
                "source_scope": SOURCE_ID,
                "mass_score": topic["mass_score"],
                "evidence_count": conversation_count,
                "growth_score": _clamp01(len(recent_rows) / max(1, conversation_count)),
                "recent_signal_count": len(recent_rows),
                "decline_score": _clamp01(inactive_days / inactive_normalization_days),
                "inactive_days": inactive_days,
                "latest_signal_date": latest.date().isoformat(),
                "confidence": _clamp01(
                    float(parameters["confidence_base"])
                    + min(
                        float(parameters["confidence_max_increment"]),
                        conversation_count
                        * float(parameters["confidence_per_conversation"]),
                    )
                ),
                "recommended_action": "在后续 Atlas 更新中复核该主题的可解释关联。",
                "relation_count": 0,
                "roi_potential": _clamp01(
                    int(topic["value_signal_count"]) / max(1, conversation_count)
                ),
                "evidence_refs": copy.deepcopy(topic["evidence_refs"]),
            }
        )
    clusters.sort(key=lambda row: (-float(row["mass_score"]), str(row["cluster_id"])))
    recent_activity_count = sum(
        1
        for activity in activities
        if (parse_time(activity["occurred_at"]) or datetime.min.replace(tzinfo=timezone.utc))
        >= recent_start
    )
    dates = sorted(
        (parse_time(facet["occurred_at"]) or generated).date().isoformat()
        for facet in facets
    )
    return {
        "schema_version": "memory_atlas_universe_state_fixture.v1",
        "generated_at": generated_at,
        "source_scope": SOURCE_ID,
        "time_range": {"start": dates[0], "end": dates[-1]},
        "redaction_mode": "public_redacted_read_only_visualization",
        "source_safety": {
            "raw_private_data_included": False,
            "plaintext_secrets_included": False,
            "local_absolute_paths_included": False,
            "writeback_allowed": False,
        },
        "clusters": clusters,
        "conflict_zones": [],
        "black_hole_candidates": [],
        "proto_star_candidates": [],
        "activity": {
            "recent_window_days": recent_window_days,
            "activity_density": _clamp01(recent_activity_count / recent_window_days),
            "dominant_lane_ids": [row["cluster_id"] for row in clusters[:3]],
            "recent_event_count": recent_activity_count,
        },
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": model_sha256,
        "provenance": {
            "canonical_event_ledger": EVENTS_RELATIVE.as_posix(),
            "canonical_event_ledger_sha256": ledger_sha256,
            "canonical_event_count": len(activities),
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _validate_output_privacy(payloads: dict[str, bytes]) -> None:
    for relative, payload in payloads.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ChatGPTDerivedError("chatgpt_derived_output_not_utf8") from exc
        if LOCAL_ABSOLUTE_PATH_RE.search(text):
            raise ChatGPTDerivedError("chatgpt_derived_output_absolute_path")
        if credential_exclusion_hits(text, source=relative):
            raise ChatGPTDerivedError("chatgpt_derived_output_credential")


def _load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = _read_json(path, code="chatgpt_derived_state_invalid")
    if (
        payload.get("schema_version") != STATE_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != SOURCE_ID
        or not isinstance(payload.get("output_hashes"), dict)
    ):
        raise ChatGPTDerivedError("chatgpt_derived_state_invalid")
    return payload


def _outputs_match_state(root: Path, state: dict[str, Any]) -> bool:
    output_hashes = state["output_hashes"]
    expected_paths = set(EXPECTED_OUTPUTS.values()) - {EXPECTED_OUTPUTS["state"]}
    if set(output_hashes) != expected_paths:
        return False
    for relative in expected_paths:
        path = root / relative
        if path.is_symlink() or not path.is_file():
            return False
        payload = _read_regular_bytes(
            path,
            maximum_bytes=512 * 1024 * 1024,
            code="chatgpt_derived_output_invalid",
        )
        expected = output_hashes[relative]
        if not isinstance(expected, dict):
            return False
        if expected != {"sha256": _sha256(payload), "byte_size": len(payload)}:
            return False
    return True


def _safe_output_path(root: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or pure.as_posix() != relative:
        raise ChatGPTDerivedError("chatgpt_derived_output_path_invalid")
    target = root / pure
    cursor = root
    for part in pure.parts[:-1]:
        cursor = cursor / part
        if cursor.exists() and cursor.is_symlink():
            raise ChatGPTDerivedError("chatgpt_derived_output_parent_unsafe")
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        resolved_parent = target.parent.resolve(strict=True)
    except OSError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_output_parent_unsafe") from exc
    if root != resolved_parent and root not in resolved_parent.parents:
        raise ChatGPTDerivedError("chatgpt_derived_output_parent_unsafe")
    if target.exists() and (target.is_symlink() or not target.is_file()):
        raise ChatGPTDerivedError("chatgpt_derived_output_path_invalid")
    return target


def _fsync_parent(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_bundle(root: Path, payloads: dict[str, bytes]) -> list[str]:
    targets = {
        relative: _safe_output_path(root, relative)
        for relative in payloads
    }
    changed = [
        relative
        for relative, target in targets.items()
        if not target.exists() or target.read_bytes() != payloads[relative]
    ]
    staged: list[tuple[Path, Path]] = []
    try:
        for relative in changed:
            target = targets[relative]
            temp = target.with_name(f".{target.name}.{os.getpid()}.tmp")
            descriptor = os.open(
                temp,
                os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
                0o644,
            )
            with os.fdopen(descriptor, "wb") as handle:
                handle.write(payloads[relative])
                handle.flush()
                os.fsync(handle.fileno())
            staged.append((temp, target))
        state_target = targets[EXPECTED_OUTPUTS["state"]]
        staged.sort(key=lambda row: row[1] == state_target)
        parents: set[Path] = set()
        for temp, target in staged:
            os.replace(temp, target)
            parents.add(target.parent)
        for parent in sorted(parents):
            _fsync_parent(parent)
    except OSError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_output_write_failed") from exc
    finally:
        for temp, _target in staged:
            if temp.exists():
                temp.unlink()
    return sorted(changed)


@contextmanager
def _derived_lock(root: Path) -> Iterator[None]:
    identity = hashlib.sha256(str(root.resolve()).encode("utf-8")).hexdigest()[:24]
    path = Path(tempfile.gettempdir()) / f"memory-atlas-chatgpt-derived-{identity}.lock"
    try:
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0),
            0o600,
        )
    except OSError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_lock_unavailable") from exc
    handle = os.fdopen(descriptor, "a+b")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ChatGPTDerivedError("chatgpt_derived_lock_busy") from exc
        yield
    finally:
        fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


def _verify_raw_signatures(signatures: list[dict[str, Any]]) -> None:
    for signature in signatures:
        path = signature["path"]
        payload = _read_regular_bytes(
            path,
            maximum_bytes=int(signature["size"]),
            code="chatgpt_derived_raw_changed_while_building",
        )
        if (
            len(payload) != signature["size"]
            or path.stat(follow_symlinks=False).st_mtime_ns != signature["mtime_ns"]
            or _sha256(payload) != signature["sha256"]
        ):
            raise ChatGPTDerivedError("chatgpt_derived_raw_changed_while_building")


def _build_chatgpt_derived_locked(
    root: Path,
    *,
    dry_run: bool,
) -> dict[str, Any]:
    contract = load_chatgpt_derived_contract(root)
    model = load_chatgpt_derived_model_parameters(root)
    contract_sha256 = _sha256(_canonical_bytes(contract))
    model_sha256 = _sha256(_canonical_bytes(model))
    try:
        ledger_bytes, events = load_chatgpt_canonical_events(root)
    except ChatGPTCanonicalEventError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_canonical_ledger_invalid") from exc
    if not ledger_bytes or not events:
        raise ChatGPTDerivedError("chatgpt_derived_canonical_events_missing")
    ledger_sha256 = _sha256(ledger_bytes)
    maximum_raw_bytes = int(model["safety_limits"]["maximum_raw_file_bytes"])
    raw_by_version: dict[str, dict[str, Any]] = {}
    signatures: list[dict[str, Any]] = []
    for event in events:
        evidence, signature = _verify_raw_event(
            root,
            event,
            maximum_raw_bytes=maximum_raw_bytes,
        )
        raw_by_version[str(event["version_id"])] = evidence
        signatures.append(signature)
    latest = _latest_events(events)
    facets = [
        _facet(event, raw_by_version[str(event["version_id"])], model)
        for event in latest
    ]
    facets.sort(key=lambda row: (str(row["occurred_at"]), str(row["record_id"])))
    activities = [
        _activity(event, raw_by_version[str(event["version_id"])], model)
        for event in events
    ]
    activities.sort(
        key=lambda row: (
            str(row["occurred_at"]),
            str(row["conversation_id"]),
            int(row["version_number"]),
        )
    )
    topic_rows = _topics(
        facets,
        maximum_evidence_refs=int(
            model["safety_limits"]["maximum_evidence_refs_per_aggregate"]
        ),
    )
    generated = max(_event_time(event) for event in events)
    generated_at = generated.isoformat().replace("+00:00", "Z")
    topics_payload = {
        "schema_version": TOPICS_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_id": SOURCE_ID,
        "topic_count": len(topic_rows),
        "topics": topic_rows,
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": model_sha256,
        "provenance": {
            "canonical_event_ledger": EVENTS_RELATIVE.as_posix(),
            "canonical_event_ledger_sha256": ledger_sha256,
            "canonical_event_count": len(events),
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    universe = _universe_input(
        topic_rows,
        facets,
        activities,
        generated_at,
        model,
        model_sha256,
        ledger_sha256,
    )
    payloads = {
        EXPECTED_OUTPUTS["facets"]: _jsonl_bytes(facets),
        EXPECTED_OUTPUTS["topics"]: _json_bytes(topics_payload),
        EXPECTED_OUTPUTS["activity"]: _jsonl_bytes(activities),
        EXPECTED_OUTPUTS["universe_state_input"]: _json_bytes(universe),
    }
    _validate_output_privacy(payloads)
    output_hashes = {
        relative: {"sha256": _sha256(payload), "byte_size": len(payload)}
        for relative, payload in sorted(payloads.items())
    }
    state_path = root / EXPECTED_OUTPUTS["state"]
    state = _load_state(state_path)
    state_current = bool(
        state
        and state.get("contract_sha256") == contract_sha256
        and state.get("model_parameters_sha256") == model_sha256
        and state.get("canonical_event_ledger_sha256") == ledger_sha256
        and state.get("canonical_event_count") == len(events)
        and state.get("latest_conversation_count") == len(latest)
        and state.get("output_hashes") == output_hashes
        and _outputs_match_state(root, state)
    )
    _verify_raw_signatures(signatures)
    try:
        final_ledger_bytes, _final_events = load_chatgpt_canonical_events(root)
    except ChatGPTCanonicalEventError as exc:
        raise ChatGPTDerivedError("chatgpt_derived_canonical_changed_while_building") from exc
    if final_ledger_bytes != ledger_bytes:
        raise ChatGPTDerivedError("chatgpt_derived_canonical_changed_while_building")
    if state_current:
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "status": "PASS",
            "outcome": "NO_CHANGES",
            "dry_run": dry_run,
            "writes_files": False,
            "raw_mutation": False,
            "canonical_mutation": False,
            "canonical_event_count": len(events),
            "latest_conversation_count": len(latest),
            "facet_count": len(facets),
            "topic_count": len(topic_rows),
            "activity_count": len(activities),
            "output_paths": EXPECTED_OUTPUTS,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
    outcome = (
        "REBUILT_FROM_CANONICAL_EVENTS" if state else "BUILT_FROM_CANONICAL_EVENTS"
    )
    state_payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "contract_ref": CONTRACT_PATH.as_posix(),
        "contract_sha256": contract_sha256,
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": model_sha256,
        "generated_at": generated_at,
        "canonical_event_ledger": EVENTS_RELATIVE.as_posix(),
        "canonical_event_ledger_sha256": ledger_sha256,
        "canonical_event_count": len(events),
        "latest_conversation_count": len(latest),
        "facet_count": len(facets),
        "topic_count": len(topic_rows),
        "activity_count": len(activities),
        "raw_evidence": [raw_by_version[str(event["version_id"])] for event in events],
        "output_hashes": output_hashes,
        "last_result": {"outcome": outcome},
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    payloads[EXPECTED_OUTPUTS["state"]] = _json_bytes(state_payload)
    _validate_output_privacy(
        {EXPECTED_OUTPUTS["state"]: payloads[EXPECTED_OUTPUTS["state"]]}
    )
    changed = [] if dry_run else _write_bundle(root, payloads)
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": "PASS",
        "outcome": outcome if not dry_run else f"WOULD_{outcome}",
        "dry_run": dry_run,
        "writes_files": bool(changed),
        "raw_mutation": False,
        "canonical_mutation": False,
        "canonical_event_count": len(events),
        "latest_conversation_count": len(latest),
        "facet_count": len(facets),
        "topic_count": len(topic_rows),
        "activity_count": len(activities),
        "changed_paths": changed,
        "output_paths": EXPECTED_OUTPUTS,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def build_chatgpt_derived(
    database_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    with _derived_lock(root):
        return _build_chatgpt_derived_locked(root, dry_run=dry_run)


def run_chatgpt_derived(args: argparse.Namespace) -> int:
    try:
        result = build_chatgpt_derived(
            Path(args.database_dir),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    except ChatGPTDerivedError as exc:
        print(
            json.dumps(
                {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "status": "FAIL",
                    "error_code": exc.code,
                    "reason": str(exc),
                    "writes_files": False,
                    "raw_mutation": False,
                    "canonical_mutation": False,
                    "remote_push": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = [
    "CONTRACT_PATH",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "EXPECTED_OUTPUTS",
    "EXPECTED_PHASE_BOUNDARY",
    "MODEL_PARAMETERS_PATH",
    "ChatGPTDerivedError",
    "build_chatgpt_derived",
    "load_chatgpt_derived_contract",
    "load_chatgpt_derived_model_parameters",
    "run_chatgpt_derived",
    "validate_chatgpt_derived_contract",
    "validate_chatgpt_derived_model_parameters",
]
