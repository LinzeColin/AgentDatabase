#!/usr/bin/env python3
"""Deterministic, zero-LLM recurring-prompt analysis for sanitized Codex JSONL.

The module is deliberately standard-library only. It treats tracked public_raw data as
untrusted input, extracts only explicit user message event shapes, removes injected
context, deduplicates Codex's dual event representation, splits long prompts into
clauses, assigns exactly three categories, and publishes candidate analytics.
"""

from __future__ import annotations

import collections
import dataclasses
import datetime as dt
import difflib
import hashlib
import json
import math
import os
import re
import shutil
import tempfile
import unicodedata
import urllib.parse
from pathlib import Path
from typing import Any, Iterable, Iterator, Mapping, MutableMapping, Sequence

UTC = dt.timezone.utc
SCHEMA_OCCURRENCE = "recurring_occurrence.v4"
SCHEMA_CLUSTER = "recurring_cluster.v4"
SCHEMA_CONTEXT = "recurring_agent_context.v3"
SCHEMA_FRESHNESS = "recurring_freshness.v4"
SCHEMA_RUN = "recurring_run.v4"
SCHEMA_STATE = "recurring_state.v4"
ALLOWED_CATEGORIES = {
    "rules_preferences",
    "tasks_topics",
    "problems_corrections",
}
ALLOWED_ORIGINS = {"human_interactive", "codex_automation"}
SOURCE_PRIORITY = {"event_msg": 0, "response_item": 1}


class AnalysisError(RuntimeError):
    """Raised when an input or governance invariant is violated."""


class SourceMutationError(AnalysisError):
    """Raised when an append-only raw source was mutated or deleted."""


@dataclasses.dataclass(frozen=True)
class FileInspection:
    relative_path: str
    size_bytes: int
    line_count: int
    sha256: str


@dataclasses.dataclass(frozen=True)
class ExtractedUserMessage:
    source_kind: str
    text_blocks: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class SanitizedUserMessage:
    text: str
    retained_block_count: int
    removed_injected_block_count: int
    max_retained_injection_score: int
    retained_configured_markers: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class StrippedInjectedText:
    text: str
    removed_pattern_blocks: int
    removed_header_lines: int


@dataclasses.dataclass(frozen=True)
class MessageCandidate:
    relative_path: str
    jsonl_line: int
    session_key: str
    timestamp: str | None
    turn_id: str | None
    source_kind: str
    origin: str
    text: str
    normalized_full_text: str
    message_text_sha256: str
    message_key: str
    retained_block_count: int
    removed_injected_block_count: int
    max_retained_injection_score: int
    retained_configured_markers: tuple[str, ...]


@dataclasses.dataclass
class ParseCounters:
    raw_lines: int = 0
    malformed_lines: int = 0
    ignored_non_user_events: int = 0
    excluded_injected_messages: int = 0
    excluded_injected_blocks: int = 0
    mixed_messages_preserved: int = 0
    retained_configured_marker_messages: int = 0
    excluded_empty_messages: int = 0
    candidate_user_messages: int = 0
    deduplicated_event_copies: int = 0
    response_items_suppressed_by_event_msg: int = 0
    clauses_created: int = 0
    clauses_discarded: int = 0

    def add(self, other: "ParseCounters") -> None:
        for field in dataclasses.fields(self):
            setattr(self, field.name, getattr(self, field.name) + getattr(other, field.name))

    def as_dict(self) -> dict[str, int]:
        return dataclasses.asdict(self)


@dataclasses.dataclass(frozen=True)
class RuntimeConfig:
    raw: Mapping[str, Any]
    config_path: Path
    config_sha256: str
    algorithm_version: str
    categories: tuple[str, ...]
    category_labels: Mapping[str, str]
    origin_labels: Mapping[str, str]
    min_clause_chars: int
    max_clause_chars: int
    display_chars: int
    minimum_cluster_count: int
    minimum_cross_session_count: int
    duplicate_window_seconds: int
    source_samples_per_cluster: int
    summary_items_per_category: int
    automation_summary_items: int
    candidate_context_max_items: int
    current_hours: int
    delayed_hours: int
    fuzzy_enabled: bool
    fuzzy_sequence_ratio: float
    fuzzy_jaccard_ratio: float
    fuzzy_min_shared_tokens: int
    fuzzy_max_candidates: int
    remove_block_patterns: tuple[re.Pattern[str], ...]
    whole_message_prefixes: tuple[str, ...]
    long_message_markers: tuple[str, ...]
    request_boundary_patterns: tuple[re.Pattern[str], ...]
    block_header_patterns: tuple[re.Pattern[str], ...]
    instruction_heading_patterns: tuple[re.Pattern[str], ...]
    directive_line_patterns: tuple[re.Pattern[str], ...]
    minimum_instruction_block_chars: int
    minimum_instruction_structure_score: int
    automation_prefix_patterns: tuple[re.Pattern[str], ...]
    automation_metadata_patterns: tuple[re.Pattern[str], ...]
    automation_exclude_line_patterns: tuple[re.Pattern[str], ...]
    correction_patterns: tuple[re.Pattern[str], ...]
    rule_patterns: tuple[re.Pattern[str], ...]
    task_patterns: tuple[re.Pattern[str], ...]
    secret_patterns: tuple[re.Pattern[str], ...]
    absolute_path_patterns: tuple[re.Pattern[str], ...]
    stop_tokens: frozenset[str]

    @classmethod
    def load(cls, path: Path) -> "RuntimeConfig":
        data = json.loads(path.read_text(encoding="utf-8"))
        categories = tuple(data["categories"])
        if set(categories) != ALLOWED_CATEGORIES or len(categories) != 3:
            raise AnalysisError("config must define exactly the three allowed categories")

        def compile_many(values: Sequence[str]) -> tuple[re.Pattern[str], ...]:
            return tuple(re.compile(value) for value in values)

        raw_bytes = canonical_json_bytes(data)
        fuzzy = data["fuzzy_lexical"]
        freshness = data["freshness"]
        injected = data["injected_context"]
        automation = data["automation"]
        classification = data["classification"]
        return cls(
            raw=data,
            config_path=path,
            config_sha256=sha256_bytes(raw_bytes),
            algorithm_version=str(data["algorithm_version"]),
            categories=categories,
            category_labels=data["category_labels_zh"],
            origin_labels=data["origin_labels_zh"],
            min_clause_chars=int(data["minimum_clause_chars"]),
            max_clause_chars=int(data["maximum_clause_chars"]),
            display_chars=int(data["display_text_chars"]),
            minimum_cluster_count=int(data["minimum_cluster_count"]),
            minimum_cross_session_count=int(data["minimum_cross_session_count"]),
            duplicate_window_seconds=int(data["duplicate_window_seconds"]),
            source_samples_per_cluster=int(data["source_samples_per_cluster"]),
            summary_items_per_category=int(data["summary_items_per_category"]),
            automation_summary_items=int(data["automation_summary_items"]),
            candidate_context_max_items=int(data["candidate_context_max_items"]),
            current_hours=int(freshness["current_hours"]),
            delayed_hours=int(freshness["delayed_hours"]),
            fuzzy_enabled=bool(fuzzy["enabled"]),
            fuzzy_sequence_ratio=float(fuzzy["sequence_ratio"]),
            fuzzy_jaccard_ratio=float(fuzzy["jaccard_ratio"]),
            fuzzy_min_shared_tokens=int(fuzzy["minimum_shared_tokens"]),
            fuzzy_max_candidates=int(fuzzy["maximum_group_candidates"]),
            remove_block_patterns=compile_many(injected["remove_block_patterns"]),
            whole_message_prefixes=tuple(injected["whole_message_prefixes"]),
            long_message_markers=tuple(injected["long_message_markers"]),
            request_boundary_patterns=compile_many(injected["request_boundary_patterns"]),
            block_header_patterns=compile_many(injected["block_header_patterns"]),
            instruction_heading_patterns=compile_many(
                injected["instruction_heading_patterns"]
            ),
            directive_line_patterns=compile_many(injected["directive_line_patterns"]),
            minimum_instruction_block_chars=int(
                injected["minimum_instruction_block_chars"]
            ),
            minimum_instruction_structure_score=int(
                injected["minimum_instruction_structure_score"]
            ),
            automation_prefix_patterns=compile_many(automation["prefix_patterns"]),
            automation_metadata_patterns=compile_many(automation["metadata_patterns"]),
            automation_exclude_line_patterns=compile_many(
                automation["exclude_metadata_line_patterns"]
            ),
            correction_patterns=compile_many(classification["correction_patterns"]),
            rule_patterns=compile_many(classification["rule_patterns"]),
            task_patterns=compile_many(classification["task_patterns"]),
            secret_patterns=compile_many(data["secret_redaction_patterns"]),
            absolute_path_patterns=compile_many(data["absolute_path_patterns"]),
            stop_tokens=frozenset(str(token).lower() for token in data["stop_tokens"]),
        )


class DisjointSet:
    def __init__(self, size: int) -> None:
        self.parent = list(range(size))
        self.rank = [0] * size

    def find(self, value: int) -> int:
        parent = self.parent[value]
        if parent != value:
            self.parent[value] = self.find(parent)
        return self.parent[value]

    def union(self, left: int, right: int) -> None:
        root_left = self.find(left)
        root_right = self.find(right)
        if root_left == root_right:
            return
        if self.rank[root_left] < self.rank[root_right]:
            root_left, root_right = root_right, root_left
        self.parent[root_right] = root_left
        if self.rank[root_left] == self.rank[root_right]:
            self.rank[root_left] += 1


def canonical_json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def pretty_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2) + "\n"


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def namespaced_id(namespace: str, *parts: str) -> str:
    payload = "\x1f".join((namespace, *parts))
    return f"sha256:{sha256_text(payload)}"


def parse_timestamp(value: Any) -> dt.datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = dt.datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed.astimezone(UTC)


def format_timestamp(value: dt.datetime | None) -> str | None:
    if value is None:
        return None
    normalized = value.astimezone(UTC).replace(microsecond=0)
    return normalized.isoformat().replace("+00:00", "Z")


def timestamp_bucket(value: dt.datetime | None, seconds: int) -> str:
    if value is None:
        return "unknown-time"
    epoch = int(value.timestamp())
    return str(epoch // max(1, seconds))


def nested_get(value: Any, *keys: str) -> Any:
    current = value
    for key in keys:
        if not isinstance(current, Mapping):
            return None
        current = current.get(key)
    return current


def extract_turn_id(obj: Mapping[str, Any], payload: Mapping[str, Any]) -> str | None:
    candidates = (
        obj.get("turn_id"),
        payload.get("turn_id"),
        nested_get(obj, "internal_chat_message_metadata_passthrough", "turn_id"),
        nested_get(payload, "internal_chat_message_metadata_passthrough", "turn_id"),
        nested_get(obj, "metadata", "turn_id"),
        nested_get(payload, "metadata", "turn_id"),
    )
    for candidate in candidates:
        if isinstance(candidate, str) and candidate.strip():
            return candidate.strip()
    return None


def flatten_text_content(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        for key in ("text", "message", "content", "value"):
            if key in value:
                result = flatten_text_content(value[key])
                if result:
                    return result
        return ""
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        parts: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                block_type = str(item.get("type", ""))
                if block_type and block_type not in {
                    "input_text",
                    "text",
                    "output_text",
                    "message",
                }:
                    continue
            item_text = flatten_text_content(item)
            if item_text:
                parts.append(item_text)
        return "\n".join(parts)
    return ""


def extract_text_blocks(value: Any) -> tuple[str, ...]:
    """Preserve top-level message content boundaries before injection filtering."""
    if isinstance(value, str):
        return (value,) if value else ()
    if isinstance(value, Mapping):
        text = flatten_text_content(value)
        return (text,) if text else ()
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        blocks: list[str] = []
        for item in value:
            if isinstance(item, Mapping):
                block_type = str(item.get("type", ""))
                if block_type and block_type not in {
                    "input_text",
                    "text",
                    "output_text",
                    "message",
                }:
                    continue
            item_text = flatten_text_content(item)
            if item_text:
                blocks.append(item_text)
        return tuple(blocks)
    return ()


def extract_user_message(obj: Mapping[str, Any]) -> ExtractedUserMessage | None:
    """Return explicit Codex user-message shapes while preserving text-block provenance."""
    obj_type = obj.get("type")
    payload = obj.get("payload")
    if not isinstance(payload, Mapping):
        return None

    if obj_type == "event_msg" and payload.get("type") == "user_message":
        blocks = extract_text_blocks(
            payload.get("message", payload.get("text", payload.get("content")))
        )
        return ExtractedUserMessage("event_msg", blocks)

    if (
        obj_type == "response_item"
        and payload.get("type") == "message"
        and payload.get("role") == "user"
    ):
        blocks = extract_text_blocks(payload.get("content", payload.get("message")))
        return ExtractedUserMessage("response_item", blocks)

    return None


def strip_injected_blocks(text: str, config: RuntimeConfig) -> StrippedInjectedText:
    """Remove explicit wrappers while reporting what was removed.

    The caller uses this provenance to distinguish a safe suffix left after a complete
    tagged block from an instruction body whose identifying header was merely deleted.
    """
    result = text
    removed_pattern_blocks = 0
    for pattern in config.remove_block_patterns:
        result, replacements = pattern.subn("\n", result)
        removed_pattern_blocks += replacements
    result, removed_header_lines = re.subn(
        r"(?im)^\s*#\s*AGENTS\.md instructions(?:\s+for\b[^\n]*)?\s*$",
        "",
        result,
    )
    return StrippedInjectedText(
        text=result.strip(),
        removed_pattern_blocks=removed_pattern_blocks,
        removed_header_lines=removed_header_lines,
    )


def looks_like_environment_only(text: str) -> bool:
    lowered = text.lower()
    marker_count = sum(
        lowered.count(marker)
        for marker in (
            "[redacted_local_path]",
            "australia/sydney",
            "australia/melbourne",
            "zsh",
            "bash",
            "permission_profile",
            "sandbox_policy",
            "type=\"disabled\"",
        )
    )
    meaningful_chars = len(re.sub(r"[\s\W_]+", "", text, flags=re.UNICODE))
    return len(text) <= 900 and marker_count >= 2 and meaningful_chars <= 360


def injection_block_evidence(
    text: str,
    source_kind: str,
    config: RuntimeConfig,
) -> tuple[int, tuple[str, ...], tuple[str, ...]]:
    """Return independent injection risk evidence without mutating the text."""
    stripped = text.lstrip()
    lowered = text.lower()
    reasons: list[str] = []
    marker_matches = tuple(
        marker for marker in config.long_message_markers if marker.lower() in lowered
    )
    if any(stripped.startswith(prefix) for prefix in config.whole_message_prefixes):
        reasons.append("whole_message_prefix")
    header_hits = sum(bool(pattern.search(text)) for pattern in config.block_header_patterns)
    if header_hits:
        reasons.append(f"block_header:{header_hits}")
    if looks_like_environment_only(text):
        reasons.append("environment_only")
    heading_hits = sum(
        len(pattern.findall(text)) for pattern in config.instruction_heading_patterns
    )
    directive_hits = sum(
        len(pattern.findall(text)) for pattern in config.directive_line_patterns
    )
    if heading_hits:
        reasons.append(f"known_instruction_headings:{heading_hits}")
    if directive_hits:
        reasons.append(f"directive_lines:{directive_hits}")
    if marker_matches:
        reasons.append(f"configured_markers:{len(marker_matches)}")

    hard_signal = bool(
        "whole_message_prefix" in reasons
        or "environment_only" in reasons
        or header_hits
    )
    score = 10 if hard_signal else 0
    score += min(4, len(marker_matches) * 2)
    score += 2 if heading_hits >= 2 else (1 if heading_hits else 0)
    score += 2 if directive_hits >= 4 else (1 if directive_hits >= 2 else 0)
    if len(text) >= config.minimum_instruction_block_chars:
        score += 1
    if (
        source_kind == "response_item"
        and marker_matches
        and len(text) >= config.minimum_instruction_block_chars
    ):
        score += 1
    return score, tuple(sorted(set(reasons))), marker_matches


def is_injected_context(
    text: str,
    config: RuntimeConfig,
    source_kind: str = "response_item",
) -> bool:
    score, reasons, markers = injection_block_evidence(text, source_kind, config)
    if any(
        reason == "whole_message_prefix"
        or reason == "environment_only"
        or reason.startswith("block_header:")
        for reason in reasons
    ):
        return True
    # Structural heuristics are limited to response_item blocks. Codex's event_msg
    # shape is the strongest available evidence that text is an actual user message;
    # this prevents a genuine user-authored operating contract from being discarded.
    if source_kind != "response_item":
        return False
    heading_hits = next(
        (
            int(reason.rsplit(":", 1)[1])
            for reason in reasons
            if reason.startswith("known_instruction_headings:")
        ),
        0,
    )
    return bool(
        (markers and score >= config.minimum_instruction_structure_score)
        or (
            heading_hits >= 3
            and score >= config.minimum_instruction_structure_score + 1
        )
    )


def extract_user_request_tail(
    text: str,
    source_kind: str,
    config: RuntimeConfig,
) -> tuple[str, bool]:
    """Keep an explicit user-request suffix after a positively identified injected prefix."""
    for pattern in config.request_boundary_patterns:
        matches = list(pattern.finditer(text))
        for match in reversed(matches):
            prefix = text[: match.start()].strip()
            suffix = text[match.end() :].strip()
            if not suffix:
                continue
            if prefix and is_injected_context(prefix, config, source_kind):
                return suffix, True
    return text, False


def sanitize_user_text_blocks(
    blocks: Sequence[str],
    source_kind: str,
    config: RuntimeConfig,
) -> SanitizedUserMessage:
    retained: list[str] = []
    removed = 0
    max_retained_score = 0
    retained_markers: set[str] = set()

    for raw_block in blocks:
        normalized = normalize_unicode(raw_block).strip()
        if not normalized:
            continue

        candidate, split_prefix = extract_user_request_tail(
            normalized, source_kind, config
        )
        candidate_is_injected = is_injected_context(candidate, config, source_kind)
        strip_result = strip_injected_blocks(candidate, config)
        stripped = strip_result.text
        explicit_wrapper_removed = strip_result.removed_pattern_blocks > 0
        header_only_removed = (
            strip_result.removed_header_lines > 0 and not explicit_wrapper_removed
        )
        changed = bool(
            split_prefix
            or strip_result.removed_pattern_blocks
            or strip_result.removed_header_lines
        )

        if not stripped:
            removed += 1
            continue

        # A hard/structured injected block remains injected even if deleting its title
        # makes the body look ordinary. A complete tagged wrapper may safely leave an
        # unrelated suffix; an explicit request boundary is handled above.
        if (
            candidate_is_injected
            and not split_prefix
            and (header_only_removed or not explicit_wrapper_removed)
        ):
            removed += 1
            continue
        if is_injected_context(stripped, config, source_kind):
            removed += 1
            continue

        if changed:
            removed += 1
        score, _reasons, markers = injection_block_evidence(
            stripped, source_kind, config
        )
        max_retained_score = max(max_retained_score, score)
        retained_markers.update(markers)
        retained.append(stripped)

    return SanitizedUserMessage(
        text="\n".join(retained).strip(),
        retained_block_count=len(retained),
        removed_injected_block_count=removed,
        max_retained_injection_score=max_retained_score,
        retained_configured_markers=tuple(sorted(retained_markers)),
    )


def redact_text(text: str, config: RuntimeConfig) -> str:
    result = text
    for pattern in config.secret_patterns:
        result = pattern.sub("[REDACTED_SECRET]", result)
    for pattern in config.absolute_path_patterns:
        result = pattern.sub("[REDACTED_LOCAL_PATH]", result)
    result = re.sub(
        r"(?i)\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
        "[REDACTED_EMAIL]",
        result,
    )
    return result


def normalize_unicode(text: str) -> str:
    return unicodedata.normalize("NFKC", text).replace("\r\n", "\n").replace("\r", "\n")


def normalize_message_identity(text: str) -> str:
    """Normalize a full message for event-copy identity without discarding code payloads."""
    value = normalize_unicode(text).lower()
    value = re.sub(r"\s+", " ", value)
    return value.strip(" \t\n")


def normalize_exact(text: str) -> str:
    value = normalize_unicode(text).lower()
    value = re.sub(r"```.*?```", " [code] ", value, flags=re.DOTALL)
    value = re.sub(r"`([^`]+)`", r"\1", value)
    value = re.sub(r"(?m)^\s*(?:[-*+•]|\d+[.)、]|[一二三四五六七八九十]+[.)、])\s*", "", value)
    value = re.sub(r"\s+", " ", value)
    value = value.strip(" \t\n.,，。;；:：!?！？'\"“”‘’()[]{}")
    return value


def normalize_template(text: str) -> str:
    value = normalize_exact(text)
    substitutions = (
        (r"https?://[^\s]+", "<url>"),
        (r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", "<email>"),
        (r"\b[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b", "<uuid>"),
        (r"\b[0-9a-f]{7,40}\b", "<sha>"),
        (r"\bv?\d+(?:\.\d+){1,4}(?:[-+._][a-z0-9]+)*\b", "<version>"),
        (r"\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b", "<date>"),
        (r"\b\d{1,2}:\d{2}(?::\d{2})?\b", "<time>"),
        (r"(?<![a-z0-9_])/(?:users|home|tmp|var|private)/[^\s]+", "<path>"),
        (r"[a-z]:\\[^\s]+", "<path>"),
        (r"\b\d+(?:\.\d+)?\b", "<num>"),
    )
    for pattern, replacement in substitutions:
        value = re.sub(pattern, replacement, value, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", value).strip()


def detect_origin(text: str, payload: Mapping[str, Any], config: RuntimeConfig) -> str:
    # Origin must not be inferred from ordinary prompt prose. A human may discuss
    # "scheduled automation" without that turn being an Automation execution.
    if any(pattern.search(text[:1000]) for pattern in config.automation_prefix_patterns):
        return "codex_automation"
    if any(pattern.search(text[:1000]) for pattern in config.automation_metadata_patterns):
        return "codex_automation"
    explicit_metadata = {
        "metadata": payload.get("metadata"),
        "internal": payload.get("internal_chat_message_metadata_passthrough"),
        "automation_id": payload.get("automation_id"),
        "scheduled": payload.get("scheduled"),
    }
    metadata = json.dumps(explicit_metadata, ensure_ascii=False, sort_keys=True)[:3000]
    if re.search(r"(?i)\bautomation\b", metadata) and re.search(
        r"(?i)\b(?:scheduled|cron|automation_id|automation id)\b", metadata
    ):
        return "codex_automation"
    return "human_interactive"


def inspect_file(path: Path, repo_root: Path) -> FileInspection:
    digest = hashlib.sha256()
    size = 0
    newline_count = 0
    last_byte = b""
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            size += len(chunk)
            newline_count += chunk.count(b"\n")
            last_byte = chunk[-1:]
    line_count = newline_count + (1 if size and last_byte != b"\n" else 0)
    return FileInspection(
        relative_path=path.relative_to(repo_root).as_posix(),
        size_bytes=size,
        line_count=line_count,
        sha256=digest.hexdigest(),
    )


def hash_prefix(path: Path, length: int) -> str:
    digest = hashlib.sha256()
    remaining = length
    with path.open("rb") as handle:
        while remaining > 0:
            chunk = handle.read(min(1024 * 1024, remaining))
            if not chunk:
                break
            digest.update(chunk)
            remaining -= len(chunk)
    if remaining != 0:
        raise SourceMutationError(f"cannot read expected prefix length from {path}")
    return digest.hexdigest()


def extract_messages_from_file(
    path: Path,
    repo_root: Path,
    config: RuntimeConfig,
    *,
    start_offset: int = 0,
    starting_line: int = 0,
) -> tuple[list[MessageCandidate], ParseCounters]:
    counters = ParseCounters()
    relative_path = path.relative_to(repo_root).as_posix()
    session_raw = path.name.split(".", 1)[0]
    session_key = namespaced_id("codex-session", session_raw)
    candidates: list[MessageCandidate] = []

    with path.open("rb") as handle:
        handle.seek(start_offset)
        for line_number, raw_line in enumerate(handle, start=starting_line + 1):
            counters.raw_lines += 1
            try:
                obj = json.loads(raw_line.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError):
                counters.malformed_lines += 1
                continue
            if not isinstance(obj, Mapping):
                counters.ignored_non_user_events += 1
                continue
            extracted = extract_user_message(obj)
            if extracted is None:
                counters.ignored_non_user_events += 1
                continue
            source_kind = extracted.source_kind
            payload = obj.get("payload")
            if not isinstance(payload, Mapping):
                counters.ignored_non_user_events += 1
                continue
            sanitized = sanitize_user_text_blocks(
                extracted.text_blocks, source_kind, config
            )
            counters.excluded_injected_blocks += sanitized.removed_injected_block_count
            if sanitized.removed_injected_block_count and sanitized.text:
                counters.mixed_messages_preserved += 1
            if sanitized.retained_configured_markers:
                counters.retained_configured_marker_messages += 1
            text = sanitized.text
            if not text:
                if any(block.strip() for block in extracted.text_blocks):
                    counters.excluded_injected_messages += 1
                else:
                    counters.excluded_empty_messages += 1
                continue
            text = redact_text(text, config).strip()
            normalized = normalize_message_identity(text)
            if not normalized:
                counters.excluded_empty_messages += 1
                continue
            parsed_time = parse_timestamp(obj.get("timestamp") or payload.get("timestamp"))
            timestamp = format_timestamp(parsed_time)
            turn_id = extract_turn_id(obj, payload)
            origin = detect_origin(text, payload, config)
            message_sha = sha256_text(normalized)
            dedupe_anchor = (
                f"turn:{turn_id}"
                if turn_id
                else f"bucket:{timestamp_bucket(parsed_time, config.duplicate_window_seconds)}"
            )
            message_key = namespaced_id(
                "codex-user-message",
                session_key,
                message_sha,
                dedupe_anchor,
            )
            candidates.append(
                MessageCandidate(
                    relative_path=relative_path,
                    jsonl_line=line_number,
                    session_key=session_key,
                    timestamp=timestamp,
                    turn_id=turn_id,
                    source_kind=source_kind,
                    origin=origin,
                    text=text,
                    normalized_full_text=normalized,
                    message_text_sha256=message_sha,
                    message_key=message_key,
                    retained_block_count=sanitized.retained_block_count,
                    removed_injected_block_count=sanitized.removed_injected_block_count,
                    max_retained_injection_score=sanitized.max_retained_injection_score,
                    retained_configured_markers=sanitized.retained_configured_markers,
                )
            )
            counters.candidate_user_messages += 1

    # Codex can emit injected/runtime context as a user-role response_item and the
    # actual user prompt as event_msg in the same turn. event_msg is authoritative.
    # This source-level rule runs before text/keyword logic, so differing text cannot
    # leak merely because it evades an injection-marker heuristic.
    event_turns = {
        (candidate.session_key, candidate.turn_id)
        for candidate in candidates
        if candidate.source_kind == "event_msg" and candidate.turn_id
    }
    authoritative_candidates: list[MessageCandidate] = []
    for candidate in candidates:
        if (
            candidate.source_kind == "response_item"
            and candidate.turn_id
            and (candidate.session_key, candidate.turn_id) in event_turns
        ):
            counters.response_items_suppressed_by_event_msg += 1
            continue
        authoritative_candidates.append(candidate)
    candidates = authoritative_candidates

    deduped: dict[tuple[str, str, str], MessageCandidate] = {}
    for candidate in candidates:
        key = (candidate.session_key, candidate.message_key, candidate.message_text_sha256)
        existing = deduped.get(key)
        if existing is None:
            deduped[key] = candidate
            continue
        counters.deduplicated_event_copies += 1
        existing_priority = SOURCE_PRIORITY.get(existing.source_kind, 99)
        candidate_priority = SOURCE_PRIORITY.get(candidate.source_kind, 99)
        if (candidate_priority, candidate.jsonl_line) < (
            existing_priority,
            existing.jsonl_line,
        ):
            deduped[key] = candidate

    return sorted(
        deduped.values(),
        key=lambda item: (
            item.timestamp or "",
            item.relative_path,
            item.jsonl_line,
            item.message_key,
        ),
    ), counters


def clean_clause_prefix(text: str) -> str:
    value = re.sub(r"^\s{0,3}#{1,6}\s*", "", text)
    value = re.sub(
        r"^\s*(?:[-*+•]|\d+[.)、]|[一二三四五六七八九十]+[.)、])\s*",
        "",
        value,
    )
    return value.strip()


def split_oversized_clause(text: str, maximum: int) -> list[str]:
    if len(text) <= maximum:
        return [text]
    pieces = re.split(r"(?<=[，,、：:])\s*", text)
    result: list[str] = []
    buffer = ""
    for piece in pieces:
        if not piece:
            continue
        if buffer and len(buffer) + len(piece) > maximum:
            result.append(buffer.strip())
            buffer = piece
        else:
            buffer += piece
    if buffer.strip():
        result.append(buffer.strip())
    final: list[str] = []
    for piece in result:
        if len(piece) <= maximum:
            final.append(piece)
            continue
        for start in range(0, len(piece), maximum):
            final.append(piece[start : start + maximum])
    return final


def split_clauses(text: str, origin: str, config: RuntimeConfig) -> list[str]:
    value = re.sub(r"```.*?```", "\n", text, flags=re.DOTALL)
    value = re.sub(r"<details>.*?</details>", "\n", value, flags=re.DOTALL | re.IGNORECASE)
    clauses: list[str] = []
    seen: set[str] = set()
    for raw_line in value.splitlines():
        line = clean_clause_prefix(raw_line)
        if not line:
            continue
        if origin == "codex_automation" and any(
            pattern.search(line) for pattern in config.automation_exclude_line_patterns
        ):
            continue
        if re.fullmatch(r"[\W_]+", line, flags=re.UNICODE):
            continue
        sentence_parts = re.split(
            r"(?<=[。！？!?；;])\s*|(?<=\.)\s+(?=[A-Z0-9])",
            line,
        )
        for sentence in sentence_parts:
            sentence = clean_clause_prefix(sentence)
            if not sentence:
                continue
            # Long Chinese user prompts frequently encode independent requirements with
            # commas instead of full stops. Splitting comma chains here makes repeated
            # standing instructions observable without any LLM call. Recurrence and
            # cross-session thresholds suppress most one-off fragments downstream.
            comma_parts = re.split(r"(?<=[，,])\s*", sentence)
            if len(comma_parts) == 1:
                comma_parts = [sentence]
            for comma_part in comma_parts:
                comma_part = clean_clause_prefix(comma_part)
                if not comma_part:
                    continue
                for piece in split_oversized_clause(comma_part, config.max_clause_chars):
                    normalized = normalize_exact(piece)
                    meaningful = len(re.sub(r"[\s\W_]+", "", normalized, flags=re.UNICODE))
                    if meaningful < config.min_clause_chars:
                        continue
                    if normalized in seen:
                        continue
                    seen.add(normalized)
                    clauses.append(piece.strip())
    return clauses


def classify_clause(text: str, config: RuntimeConfig) -> tuple[str, float, bool]:
    if any(pattern.search(text) for pattern in config.correction_patterns):
        return "problems_corrections", 0.96, False
    if any(pattern.search(text) for pattern in config.rule_patterns):
        return "rules_preferences", 0.90, False
    if any(pattern.search(text) for pattern in config.task_patterns):
        return "tasks_topics", 0.83, False
    return "tasks_topics", 0.68, True


def compact_display(text: str, limit: int) -> str:
    value = re.sub(r"\s+", " ", text).strip()
    if len(value) <= limit:
        return value
    return value[: max(1, limit - 1)].rstrip() + "…"


def message_to_occurrences(
    message: MessageCandidate,
    config: RuntimeConfig,
    counters: ParseCounters,
) -> list[dict[str, Any]]:
    clauses = split_clauses(message.text, message.origin, config)
    counters.clauses_created += len(clauses)
    if not clauses:
        counters.clauses_discarded += 1
    records: list[dict[str, Any]] = []
    for ordinal, clause in enumerate(clauses, start=1):
        redacted = redact_text(clause, config)
        normalized = normalize_exact(redacted)
        template = normalize_template(redacted)
        if not normalized or not template:
            counters.clauses_discarded += 1
            continue
        category, confidence, needs_review = classify_clause(redacted, config)
        normalized_hash = sha256_text(normalized)
        template_hash = sha256_text(template)
        occurrence_id = namespaced_id(
            "recurring-occurrence",
            message.message_key,
            normalized_hash,
            str(ordinal),
        )
        records.append(
            {
                "schema_version": SCHEMA_OCCURRENCE,
                "occurrence_id": occurrence_id,
                "cluster_id": None,
                "message_key": message.message_key,
                "message_text_sha256": message.message_text_sha256,
                "session_key": message.session_key,
                "category": category,
                "origin": message.origin,
                "source_kind": message.source_kind,
                "display_text": compact_display(redacted, config.display_chars),
                "normalized_text": normalized,
                "template_text": template,
                "normalized_sha256": f"sha256:{normalized_hash}",
                "template_sha256": f"sha256:{template_hash}",
                "source_event_at": message.timestamp,
                "source_pointer": {
                    "relative_path": message.relative_path,
                    "jsonl_line": message.jsonl_line,
                    "turn_id": message.turn_id,
                    "clause_ordinal": ordinal,
                },
                "source_provenance": {
                    "retained_text_blocks": message.retained_block_count,
                    "removed_injected_blocks": message.removed_injected_block_count,
                    "max_retained_injection_score": message.max_retained_injection_score,
                    "retained_configured_markers": list(
                        message.retained_configured_markers
                    ),
                },
                "classification_confidence": confidence,
                "needs_review": needs_review,
            }
        )
    return records


def enforce_event_msg_authority(
    occurrences: Iterable[dict[str, Any]], counters: ParseCounters
) -> list[dict[str, Any]]:
    """Drop response_item clauses when an authoritative event_msg exists for that turn.

    The second pass is intentional: incremental builds can reuse an occurrence from a
    prior part/file while the matching event_msg arrives in a newly appended segment.
    """
    records = list(occurrences)
    event_turns = {
        (str(item.get("session_key")), str(pointer.get("turn_id")))
        for item in records
        for pointer in [item.get("source_pointer")]
        if item.get("source_kind") == "event_msg"
        and isinstance(pointer, Mapping)
        and pointer.get("turn_id")
    }
    filtered: list[dict[str, Any]] = []
    for item in records:
        pointer = item.get("source_pointer")
        turn_id = pointer.get("turn_id") if isinstance(pointer, Mapping) else None
        if (
            item.get("source_kind") == "response_item"
            and turn_id
            and (str(item.get("session_key")), str(turn_id)) in event_turns
        ):
            counters.response_items_suppressed_by_event_msg += 1
            continue
        filtered.append(item)
    return filtered


def deduplicate_occurrences(
    occurrences: Iterable[dict[str, Any]], counters: ParseCounters
) -> list[dict[str, Any]]:
    chosen: dict[str, dict[str, Any]] = {}
    for occurrence in occurrences:
        occurrence_id = str(occurrence["occurrence_id"])
        existing = chosen.get(occurrence_id)
        if existing is None:
            chosen[occurrence_id] = occurrence
            continue
        counters.deduplicated_event_copies += 1
        old_priority = SOURCE_PRIORITY.get(str(existing.get("source_kind")), 99)
        new_priority = SOURCE_PRIORITY.get(str(occurrence.get("source_kind")), 99)
        if new_priority < old_priority:
            chosen[occurrence_id] = occurrence
    return sorted(
        chosen.values(),
        key=lambda item: (
            item.get("source_event_at") or "",
            item["source_pointer"]["relative_path"],
            int(item["source_pointer"]["jsonl_line"]),
            str(item["occurrence_id"]),
        ),
    )


def tokenize_for_similarity(text: str, config: RuntimeConfig) -> frozenset[str]:
    latin = [
        token.lower()
        for token in re.findall(r"[A-Za-z0-9_<>-]{2,}", text)
        if token.lower() not in config.stop_tokens
    ]
    cjk_sequences = re.findall(r"[\u3400-\u9fff]{2,}", text)
    cjk_tokens: list[str] = []
    for sequence in cjk_sequences:
        if len(sequence) <= 3:
            cjk_tokens.append(sequence)
        else:
            cjk_tokens.extend(sequence[index : index + 2] for index in range(len(sequence) - 1))
    return frozenset(latin + cjk_tokens)


def lexical_match(
    left: str,
    right: str,
    left_tokens: frozenset[str],
    right_tokens: frozenset[str],
    config: RuntimeConfig,
) -> bool:
    if not left_tokens or not right_tokens:
        return False
    shared = left_tokens & right_tokens
    union = left_tokens | right_tokens
    jaccard = len(shared) / len(union)
    sequence = difflib.SequenceMatcher(None, left, right, autojunk=False).ratio()
    return sequence >= config.fuzzy_sequence_ratio or (
        jaccard >= config.fuzzy_jaccard_ratio
        and len(shared) >= config.fuzzy_min_shared_tokens
    )


def compute_trend(
    timestamps: Sequence[dt.datetime], as_of: dt.datetime
) -> str:
    current_start = as_of - dt.timedelta(days=28)
    previous_start = as_of - dt.timedelta(days=56)
    current = sum(value >= current_start for value in timestamps)
    previous = sum(previous_start <= value < current_start for value in timestamps)
    if current >= 2 and current > previous * 1.25:
        return "rising"
    if previous >= 2 and current * 1.25 < previous:
        return "falling"
    if current == 0 and previous == 0:
        return "dormant"
    return "stable"


def build_clusters(
    occurrences: list[dict[str, Any]],
    config: RuntimeConfig,
    as_of: dt.datetime,
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    grouped: dict[tuple[str, str, str], list[dict[str, Any]]] = collections.defaultdict(list)
    for occurrence in occurrences:
        grouped[
            (
                str(occurrence["origin"]),
                str(occurrence["category"]),
                str(occurrence["template_text"]),
            )
        ].append(occurrence)

    group_items = sorted(grouped.items(), key=lambda item: item[0])
    dsu = DisjointSet(len(group_items))
    group_tokens: list[frozenset[str]] = [
        tokenize_for_similarity(key[2], config) for key, _ in group_items
    ]

    if config.fuzzy_enabled:
        inverted: dict[tuple[str, str, str], list[int]] = collections.defaultdict(list)
        for index, ((origin, category, _template), _records) in enumerate(group_items):
            tokens = sorted(group_tokens[index])
            for token in tokens[:12]:
                inverted[(origin, category, token)].append(index)
        for index, ((origin, category, template), _records) in enumerate(group_items):
            candidate_ids: set[int] = set()
            for token in sorted(group_tokens[index])[:12]:
                candidate_ids.update(inverted[(origin, category, token)])
            checked = 0
            for other in sorted(candidate_ids):
                if other <= index:
                    continue
                checked += 1
                if checked > config.fuzzy_max_candidates:
                    break
                other_key = group_items[other][0]
                if lexical_match(
                    template,
                    other_key[2],
                    group_tokens[index],
                    group_tokens[other],
                    config,
                ):
                    dsu.union(index, other)

    merged: dict[int, list[int]] = collections.defaultdict(list)
    for index in range(len(group_items)):
        merged[dsu.find(index)].append(index)

    clusters: list[dict[str, Any]] = []
    occurrence_to_cluster: dict[str, str] = {}
    for member_indices in merged.values():
        records: list[dict[str, Any]] = []
        templates: set[str] = set()
        normalized_values: set[str] = set()
        for index in sorted(member_indices):
            key, members = group_items[index]
            templates.add(key[2])
            records.extend(members)
            normalized_values.update(str(item["normalized_text"]) for item in members)
        if len(records) < config.minimum_cluster_count:
            continue

        origin = str(records[0]["origin"])
        category = str(records[0]["category"])
        if len(templates) > 1:
            detection_method = "fuzzy_lexical"
        elif len(normalized_values) > 1:
            detection_method = "template"
        else:
            detection_method = "exact"

        template_counts = collections.Counter(str(item["template_text"]) for item in records)
        canonical_template = sorted(
            template_counts,
            key=lambda value: (-template_counts[value], len(value), value),
        )[0]
        display_counts = collections.Counter(str(item["display_text"]) for item in records)
        display_text = sorted(
            display_counts,
            key=lambda value: (-display_counts[value], len(value), value),
        )[0]
        sessions = {str(item["session_key"]) for item in records}
        parsed_times = [
            parsed
            for parsed in (parse_timestamp(item.get("source_event_at")) for item in records)
            if parsed is not None
        ]
        first_seen = min(parsed_times) if parsed_times else None
        last_seen = max(parsed_times) if parsed_times else None
        scope = (
            "cross_session"
            if len(sessions) >= config.minimum_cross_session_count
            else "same_session"
        )
        recurrence_score = (
            math.log1p(len(records))
            * math.log1p(len(sessions) + 1)
            * (1.30 if category == "problems_corrections" else 1.0)
        )
        canonical_template_hash = sha256_text(canonical_template)
        cluster_id = namespaced_id(
            "recurring-cluster",
            origin,
            category,
            canonical_template_hash,
        )
        source_samples = []
        for item in sorted(
            records,
            key=lambda value: (
                value.get("source_event_at") or "",
                value["source_pointer"]["relative_path"],
                value["source_pointer"]["jsonl_line"],
            ),
            reverse=True,
        )[: config.source_samples_per_cluster]:
            source_samples.append(
                {
                    "relative_path": item["source_pointer"]["relative_path"],
                    "jsonl_line": item["source_pointer"]["jsonl_line"],
                    "source_event_at": item.get("source_event_at"),
                }
            )
        cluster = {
            "schema_version": SCHEMA_CLUSTER,
            "cluster_id": cluster_id,
            "display_text": display_text,
            "category": category,
            "origin": origin,
            "detection_method": detection_method,
            "scope": scope,
            "count": len(records),
            "unique_sessions": len(sessions),
            "first_seen": format_timestamp(first_seen),
            "last_seen": format_timestamp(last_seen),
            "trend_28d": compute_trend(parsed_times, as_of),
            "recurrence_score": round(recurrence_score, 4),
            "classification_confidence": round(
                min(float(item["classification_confidence"]) for item in records), 4
            ),
            "needs_review": detection_method == "fuzzy_lexical"
            or any(bool(item["needs_review"]) for item in records),
            "source_samples": source_samples,
        }
        clusters.append(cluster)
        for item in records:
            occurrence_to_cluster[str(item["occurrence_id"])] = cluster_id

    clusters.sort(
        key=lambda item: (
            -float(item["recurrence_score"]),
            -int(item["count"]),
            str(item["cluster_id"]),
        )
    )
    return clusters, occurrence_to_cluster


def build_candidate_context(
    clusters: Sequence[Mapping[str, Any]],
    source_cutoff_at: str | None,
    config: RuntimeConfig,
) -> dict[str, Any]:
    human_clusters = [
        cluster for cluster in clusters if cluster["origin"] == "human_interactive"
    ][: config.candidate_context_max_items]
    sections: dict[str, list[dict[str, Any]]] = {
        category: [] for category in config.categories
    }
    for cluster in human_clusters:
        sections[str(cluster["category"])].append(
            {
                "cluster_id": cluster["cluster_id"],
                "display_text": cluster["display_text"],
                "count": cluster["count"],
                "unique_sessions": cluster["unique_sessions"],
                "last_seen": cluster["last_seen"],
                "trend_28d": cluster["trend_28d"],
                "recurrence_score": cluster["recurrence_score"],
                "needs_review": cluster["needs_review"],
            }
        )
    return {
        "schema_version": SCHEMA_CONTEXT,
        "status": "candidate_not_routed",
        "notice_zh": "仅供审核和低成本读取；未自动写入长期记忆、个性化或 Memory Atlas canonical 层。",
        "source_cutoff_at": source_cutoff_at,
        "max_items": config.candidate_context_max_items,
        "item_count": len(human_clusters),
        "sections": sections,
    }



def standalone_configured_marker(text: str, config: RuntimeConfig) -> str | None:
    """Return a configured marker when the output is only that marker/heading."""
    def compact(value: str) -> str:
        normalized = normalize_unicode(value).lower()
        normalized = re.sub(r"[\s#*_`：:;,.，。!！?？\-–—]+", "", normalized)
        return normalized.strip()

    candidate = compact(text)
    if not candidate:
        return None
    for marker in config.long_message_markers:
        if candidate == compact(marker):
            return marker
    return None


def audit_human_injection_leakage(
    occurrences: Sequence[Mapping[str, Any]],
    candidate_context: Mapping[str, Any],
    config: RuntimeConfig,
) -> list[str]:
    """Fail closed when instruction provenance leaks into human-facing memory outputs."""
    errors: list[str] = []
    risky_clusters: set[str] = set()
    cluster_ids = {
        str(item.get("cluster_id"))
        for item in occurrences
        if item.get("origin") == "human_interactive"
        and item.get("cluster_id") is not None
    }

    for occurrence in occurrences:
        if occurrence.get("origin") != "human_interactive":
            continue
        occurrence_id = str(occurrence.get("occurrence_id"))
        display_text = str(occurrence.get("display_text", ""))
        normalized_text = str(occurrence.get("normalized_text", ""))
        provenance = occurrence.get("source_provenance")
        if not isinstance(provenance, Mapping):
            errors.append(f"human occurrence missing source_provenance: {occurrence_id}")
            continue
        score = int(provenance.get("max_retained_injection_score", -1))
        if score < 0:
            errors.append(f"human occurrence has invalid injection score: {occurrence_id}")
        source_kind = str(occurrence.get("source_kind", ""))
        # Content heuristics only hard-fail response_item records. event_msg/user_message
        # is treated as the strongest available proof that the user authored the text.
        if source_kind == "response_item" and score >= config.minimum_instruction_structure_score:
            errors.append(
                f"human occurrence retained high-risk injected context: {occurrence_id} score={score}"
            )
            if occurrence.get("cluster_id") is not None:
                risky_clusters.add(str(occurrence.get("cluster_id")))

        combined = f"{display_text}\n{normalized_text}"
        if source_kind == "response_item" and any(
            pattern.search(combined) for pattern in config.block_header_patterns
        ):
            errors.append(f"human occurrence contains injected block header: {occurrence_id}")
            if occurrence.get("cluster_id") is not None:
                risky_clusters.add(str(occurrence.get("cluster_id")))
        stripped = combined.lstrip()
        if source_kind == "response_item" and any(
            stripped.startswith(prefix) for prefix in config.whole_message_prefixes
        ):
            errors.append(f"human occurrence contains injected message prefix: {occurrence_id}")
            if occurrence.get("cluster_id") is not None:
                risky_clusters.add(str(occurrence.get("cluster_id")))
        standalone_marker = standalone_configured_marker(display_text, config)
        if source_kind == "response_item" and standalone_marker is not None:
            errors.append(
                f"human occurrence is standalone configured injection marker: "
                f"{occurrence_id} marker={standalone_marker}"
            )
            if occurrence.get("cluster_id") is not None:
                risky_clusters.add(str(occurrence.get("cluster_id")))

    sections = candidate_context.get("sections", {})
    if isinstance(sections, Mapping):
        for category, items in sections.items():
            if not isinstance(items, Sequence) or isinstance(items, (str, bytes, bytearray)):
                continue
            for item in items:
                if not isinstance(item, Mapping):
                    continue
                cluster_id = str(item.get("cluster_id"))
                if cluster_id not in cluster_ids:
                    errors.append(
                        f"agent_context points to unknown human cluster: {category}:{cluster_id}"
                    )
                if cluster_id in risky_clusters:
                    errors.append(
                        f"agent_context contains high-risk injected cluster: {category}:{cluster_id}"
                    )
                display_text = str(item.get("display_text", ""))
                if any(
                    pattern.search(display_text)
                    for pattern in config.block_header_patterns
                ):
                    errors.append(
                        f"agent_context contains injected block header: {category}:{cluster_id}"
                    )

    return sorted(set(errors))

def build_freshness(
    source_cutoff: dt.datetime | None,
    as_of: dt.datetime,
    source_commit: str,
    config: RuntimeConfig,
) -> dict[str, Any]:
    if source_cutoff is None:
        lag_hours = None
        state = "missing"
    else:
        lag_hours = max(0.0, (as_of - source_cutoff).total_seconds() / 3600.0)
        if lag_hours <= config.current_hours:
            state = "current"
        elif lag_hours <= config.delayed_hours:
            state = "delayed"
        else:
            state = "stale"
    return {
        "schema_version": SCHEMA_FRESHNESS,
        "source_cutoff_at": format_timestamp(source_cutoff),
        "source_upload_commit": source_commit,
        "analysis_completed_at": format_timestamp(as_of),
        "data_lag_hours_at_analysis": None if lag_hours is None else round(lag_hours, 2),
        "pipeline_state": state,
        "cadence_claim": "upload-dependent; not real-time",
    }


def load_json_if_exists(path: Path) -> Any | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl_if_exists(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnalysisError(f"invalid previous JSONL {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise AnalysisError(f"previous JSONL record is not an object: {path}:{line_number}")
            records.append(value)
    return records


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(pretty_json_text(value), encoding="utf-8")


def write_jsonl(path: Path, records: Sequence[Mapping[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in records:
            handle.write(
                json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                + "\n"
            )


def escape_markdown_cell(value: Any) -> str:
    text = str(value if value is not None else "-").replace("\n", " ")
    # Prompt text is untrusted data. Escape Markdown/HTML metacharacters so a prompt
    # cannot turn the generated acceptance page into links, images or HTML blocks.
    escaped: list[str] = []
    for char in text:
        if char in "\\`*_{}[]<>#!|":
            escaped.append("\\" + char)
        else:
            escaped.append(char)
    return "".join(escaped)


def source_markdown_link(sample: Mapping[str, Any]) -> str:
    relative_path = str(sample.get("relative_path", ""))
    line_number = int(sample.get("jsonl_line", 0) or 0)
    if not relative_path or line_number < 1:
        return "-"
    if relative_path.startswith("OpenAIDatabase/"):
        relative_path = relative_path.removeprefix("OpenAIDatabase/")
    encoded = urllib.parse.quote(relative_path, safe="/._-")
    return f"[查看原始记录](../{encoded}#L{line_number})"


def render_cluster_table(clusters: Sequence[Mapping[str, Any]], limit: int) -> list[str]:
    if not clusters:
        return ["暂无满足重复阈值的结果。", ""]
    lines = [
        "| 排名 | 重复内容 | 次数 | Session | 最近出现 | 趋势 | 追溯 |",
        "|---:|---|---:|---:|---|---|---|",
    ]
    for index, cluster in enumerate(clusters[:limit], start=1):
        sample = cluster.get("source_samples", [{}])[0] if cluster.get("source_samples") else {}
        source = source_markdown_link(sample) if isinstance(sample, Mapping) else "-"
        lines.append(
            "| {rank} | {text} | {count} | {sessions} | {last} | {trend} | {source} |".format(
                rank=index,
                text=escape_markdown_cell(cluster.get("display_text", "")),
                count=cluster.get("count", 0),
                sessions=cluster.get("unique_sessions", 0),
                last=escape_markdown_cell(cluster.get("last_seen")),
                trend=escape_markdown_cell(cluster.get("trend_28d")),
                source=source,
            )
        )
    lines.append("")
    return lines


def render_summary(
    clusters: Sequence[Mapping[str, Any]],
    freshness: Mapping[str, Any],
    run_manifest: Mapping[str, Any],
    config: RuntimeConfig,
) -> str:
    human = [cluster for cluster in clusters if cluster["origin"] == "human_interactive"]
    automation = [cluster for cluster in clusters if cluster["origin"] == "codex_automation"]
    counts_by_category = collections.Counter(str(item["category"]) for item in human)
    state_labels = {
        "current": "正常",
        "delayed": "延迟",
        "stale": "过期",
        "missing": "无可用数据",
    }
    state = str(freshness.get("pipeline_state", "missing"))
    lines = [
        "# 00｜Recurring 分析（最新）",
        "",
        "> GitHub Actions 自动生成。只分析已经上传到仓库的治理后 Codex session；不是本机实时记忆。",
        "",
        "## 当前结论",
        "",
        f"- 验证状态：`{run_manifest.get('status', 'UNKNOWN')}`",
        f"- 数据状态：`{state_labels.get(state, state)}`",
        f"- 数据覆盖至：`{freshness.get('source_cutoff_at') or '无可用 user Prompt 时间'}`",
        f"- 本次核验时间：`{freshness.get('analysis_completed_at')}`",
        f"- 人工对话重复组：`{len(human)}`",
        f"- Automation 重复组：`{len(automation)}`（单独统计，不进入个人画像）",
        f"- 三类数量：问题与纠正 `{counts_by_category['problems_corrections']}`；规则与偏好 `{counts_by_category['rules_preferences']}`；任务与主题 `{counts_by_category['tasks_topics']}`",
        f"- 模型/API 调用：`{run_manifest.get('llm_calls', 0)}`；模型 Token：`{run_manifest.get('llm_input_tokens', 0) + run_manifest.get('llm_output_tokens', 0)}`",
        f"- 生产稳定性：`{run_manifest.get('production_acceptance', {}).get('label_zh', '待验证')}`",
        "",
    ]
    for category in (
        "problems_corrections",
        "rules_preferences",
        "tasks_topics",
    ):
        lines.append(f"## {config.category_labels[category]}")
        lines.append("")
        category_clusters = [item for item in human if item["category"] == category]
        lines.extend(
            render_cluster_table(category_clusters, config.summary_items_per_category)
        )

    lines.extend(
        [
            "## Codex Automation（隔离区）",
            "",
            "以下只反映自动任务本身的重复，不进入个人画像或 Agent Context。",
            "",
        ]
    )
    lines.extend(render_cluster_table(automation, config.automation_summary_items))
    lines.extend(
        [
            "## 你怎么验收",
            "",
            "1. 先看顶部 `验证状态`、`数据状态` 和 `数据覆盖至`。",
            "2. 重点看“问题与纠正”：应当是你的真实纠正，不应出现 AGENTS、environment、turn_context 或权限说明。",
            "3. 同一句 Prompt 即使同时存在 `event_msg` 与 `response_item`，表中次数也只能增加一次。",
            "4. 点击每条的“查看原始记录”可追溯到对应 JSONL 行。",
            "5. 运行健康度看同目录 `00_Recurring运行状态.md`；Action 页面看 `Recurring Prompt Analysis｜重复提示词自动分析` 的最新 Summary。",
            "",
            "## 数据边界",
            "",
            "- 只处理 `OpenAIDatabase/data/public_raw/codex/sessions/**/*.jsonl` 中已经上传的数据。",
            "- 只提取明确的 user message event；忽略 assistant、reasoning、tool output、turn_context 与 base instructions。",
            "- 本结果仍是 candidate analytics，不会自动写入长期记忆或 Memory Atlas canonical 层。",
            "- 全流程只使用 Python 标准库；LLM、embedding、外部网络调用均为 0。",
            "",
        ]
    )
    return "\n".join(lines)


def render_status(
    clusters: Sequence[Mapping[str, Any]],
    freshness: Mapping[str, Any],
    run_manifest: Mapping[str, Any],
) -> str:
    human = [cluster for cluster in clusters if cluster["origin"] == "human_interactive"]
    automation = [cluster for cluster in clusters if cluster["origin"] == "codex_automation"]
    counts = collections.Counter(str(item["category"]) for item in human)
    state_labels = {
        "current": "正常",
        "delayed": "延迟",
        "stale": "过期",
        "missing": "无可用数据",
    }
    state = str(freshness.get("pipeline_state", "missing"))
    lines = [
        "# 00｜Recurring 运行状态",
        "",
        "> 这是最浅层的验收入口。正常情况下只看本页和《00_Recurring分析_最新.md》。",
        "",
        "| 验收项 | 当前值 |",
        "|---|---|",
        f"| 总体验证 | **{run_manifest.get('status', 'UNKNOWN')}** |",
        f"| 数据状态 | **{state_labels.get(state, state)}** |",
        f"| 数据覆盖至 | `{freshness.get('source_cutoff_at') or '无可用 user Prompt 时间'}` |",
        f"| 本次核验时间 | `{freshness.get('analysis_completed_at')}` |",
        f"| 人工重复组 | `{len(human)}` |",
        f"| Automation 重复组 | `{len(automation)}`（隔离） |",
        f"| 问题与纠正 | `{counts['problems_corrections']}` |",
        f"| 规则与偏好 | `{counts['rules_preferences']}` |",
        f"| 任务与主题 | `{counts['tasks_topics']}` |",
        f"| 分析脚本 LLM / embedding / 外部模型 API | `0 / 0 / 0` |",
        f"| 注入完整性防护 | **{run_manifest.get('injection_guard', {}).get('status', 'UNKNOWN')}** |",
        f"| 修复后真实数据批次 | **{run_manifest.get('production_acceptance', {}).get('label_zh', '待验证')}** |",
        f"| 原始文件 | `{run_manifest.get('raw_files_seen', 0)}` |",
        f"| 派生数据指纹 | `{run_manifest.get('derived_payload_sha256', '生成中')}` |",
        "",
        "## 自动防护",
        "",
        "- ✅ 只读取明确的 user message event。",
        "- ✅ 同一 turn 优先信任 `event_msg/user_message`，并在条款拆分前丢弃对应 `response_item`。",
        "- ✅ 再按 content block 保留来源边界，剥离 AGENTS、environment、turn_context 和系统/开发者注入。",
        "- ✅ Builder 发布前与 Validator 发布后分别独立执行注入完整性硬门。",
        "- ✅ 增量复用后再次执行全局来源权威检查，避免跨 part 文件漏网。",
        "- ✅ 人工 Prompt 与 Codex Automation 分开统计。",
        "- ✅ 严格只有三类；Action 内执行单元测试、来源校验、隐私扫描和独立全量对账。",
        "",
        "## 去哪里看",
        "",
        "1. 结果正文：[打开 00_Recurring分析_最新.md](./00_Recurring分析_最新.md)",
        "2. GitHub：仓库顶部 `Actions` → `Recurring Prompt Analysis｜重复提示词自动分析` → 最新绿色运行 → `Summary`。",
        "3. 下载包：同一次 Action 页面底部 `Artifacts` → `Recurring中文验收包-*`。",
        "",
    ]
    return "\n".join(lines)

def compute_output_hashes(
    output_dir: Path, summary_path: Path, status_path: Path | None = None
) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(output_dir.glob("*")):
        if path.is_file() and path.name != "run_manifest.json":
            hashes[path.name] = sha256_bytes(path.read_bytes())
    for path in (summary_path, status_path):
        if path is not None and path.exists():
            hashes[path.name] = sha256_bytes(path.read_bytes())
    return hashes


def atomic_publish_directory(source: Path, target: Path) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    backup = target.with_name(target.name + ".previous")
    if backup.exists():
        shutil.rmtree(backup)
    if target.exists():
        target.replace(backup)
    try:
        source.replace(target)
    except Exception:
        if backup.exists() and not target.exists():
            backup.replace(target)
        raise
    if backup.exists():
        shutil.rmtree(backup)


def build_analysis(
    *,
    repo_root: Path,
    config_path: Path,
    output_dir: Path,
    summary_path: Path,
    status_path: Path,
    source_commit: str,
    as_of: dt.datetime,
    previous_output_dir: Path | None = None,
    force_full: bool = False,
    publish_atomically: bool = True,
) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    config = RuntimeConfig.load(config_path.resolve())
    implementation_sha256 = sha256_bytes(Path(__file__).resolve().read_bytes())
    input_pattern = str(config.raw["input_glob"])
    if input_pattern.startswith("OpenAIDatabase/"):
        glob_pattern = input_pattern
    else:
        glob_pattern = input_pattern
    source_paths = sorted(path for path in repo_root.glob(glob_pattern) if path.is_file())
    inspections = {item.relative_path: item for item in (inspect_file(path, repo_root) for path in source_paths)}

    previous_dir = previous_output_dir.resolve() if previous_output_dir else output_dir.resolve()
    previous_state = load_json_if_exists(previous_dir / "state.json")
    previous_occurrences = load_jsonl_if_exists(previous_dir / "occurrences.jsonl")
    compatible_previous = bool(
        previous_state
        and previous_state.get("schema_version") == SCHEMA_STATE
        and previous_state.get("algorithm_version") == config.algorithm_version
        and previous_state.get("config_sha256") == f"sha256:{config.config_sha256}"
        and previous_state.get("implementation_sha256")
        == f"sha256:{implementation_sha256}"
    )
    full_rebuild = force_full or not compatible_previous
    previous_files: Mapping[str, Any] = (
        previous_state.get("files", {}) if compatible_previous else {}
    )

    if compatible_previous:
        deleted = sorted(set(previous_files) - set(inspections))
        if deleted:
            raise SourceMutationError(
                "append-only source file deletion detected: " + ", ".join(deleted[:5])
            )

    counters = ParseCounters()
    all_occurrences: list[dict[str, Any]] = []
    reused_paths: set[str] = set()
    new_files = 0
    appended_files = 0
    reparsed_files = 0

    previous_by_path: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
    if compatible_previous and not full_rebuild:
        for occurrence in previous_occurrences:
            pointer = occurrence.get("source_pointer")
            if isinstance(pointer, Mapping) and isinstance(pointer.get("relative_path"), str):
                previous_by_path[str(pointer["relative_path"])].append(occurrence)

    path_lookup = {path.relative_to(repo_root).as_posix(): path for path in source_paths}
    for relative_path in sorted(inspections):
        inspection = inspections[relative_path]
        path = path_lookup[relative_path]
        previous_file = (
            previous_files.get(relative_path)
            if compatible_previous and not full_rebuild
            else None
        )
        start_offset = 0
        starting_line = 0
        parse_required = True
        if not full_rebuild and isinstance(previous_file, Mapping):
            previous_size = int(previous_file.get("size_bytes", -1))
            previous_hash = str(previous_file.get("sha256", "")).removeprefix("sha256:")
            if inspection.size_bytes == previous_size and inspection.sha256 == previous_hash:
                parse_required = False
                reused_paths.add(relative_path)
                all_occurrences.extend(previous_by_path.get(relative_path, []))
            elif inspection.size_bytes > previous_size and previous_size >= 0:
                if hash_prefix(path, previous_size) != previous_hash:
                    raise SourceMutationError(
                        f"non-append mutation detected in {relative_path}"
                    )
                start_offset = previous_size
                starting_line = int(previous_file.get("line_count", 0))
                appended_files += 1
                all_occurrences.extend(previous_by_path.get(relative_path, []))
            else:
                raise SourceMutationError(
                    f"non-append mutation or truncation detected in {relative_path}"
                )
        elif previous_file is None:
            new_files += 1
        else:
            reparsed_files += 1

        if parse_required:
            messages, file_counters = extract_messages_from_file(
                path,
                repo_root,
                config,
                start_offset=start_offset,
                starting_line=starting_line,
            )
            counters.add(file_counters)
            for message in messages:
                all_occurrences.extend(message_to_occurrences(message, config, counters))

    all_occurrences = enforce_event_msg_authority(all_occurrences, counters)
    occurrences = deduplicate_occurrences(all_occurrences, counters)
    clusters, occurrence_to_cluster = build_clusters(occurrences, config, as_of)
    for occurrence in occurrences:
        occurrence["cluster_id"] = occurrence_to_cluster.get(str(occurrence["occurrence_id"]))

    parsed_times = [
        parsed
        for parsed in (parse_timestamp(item.get("source_event_at")) for item in occurrences)
        if parsed is not None
    ]
    source_cutoff = max(parsed_times) if parsed_times else None
    freshness = build_freshness(source_cutoff, as_of, source_commit, config)
    candidate_context = build_candidate_context(
        clusters, freshness["source_cutoff_at"], config
    )
    injection_guard_errors = audit_human_injection_leakage(
        occurrences, candidate_context, config
    )
    if injection_guard_errors:
        raise AnalysisError(
            "injection guard blocked publish: " + "; ".join(injection_guard_errors[:8])
        )

    input_state_payload = [
        {
            "relative_path": inspection.relative_path,
            "size_bytes": inspection.size_bytes,
            "line_count": inspection.line_count,
            "sha256": inspection.sha256,
        }
        for inspection in sorted(inspections.values(), key=lambda value: value.relative_path)
    ]
    input_state_sha = sha256_bytes(canonical_json_bytes(input_state_payload))
    current_source_batch = f"sha256:{input_state_sha}"
    previous_batches: list[str] = []
    if compatible_previous and isinstance(previous_state, Mapping):
        previous_batches = [
            str(value)
            for value in previous_state.get("verified_source_batches", [])
            if isinstance(value, str) and value.startswith("sha256:")
        ]
    verified_source_batches = list(
        dict.fromkeys(previous_batches + [current_source_batch])
    )[-8:]
    verified_batch_count = len(verified_source_batches)
    production_acceptance = {
        "required_distinct_source_batches": 2,
        "verified_distinct_source_batches": verified_batch_count,
        "status": "stable" if verified_batch_count >= 2 else "candidate",
        "label_zh": (
            "稳定通过 2/2"
            if verified_batch_count >= 2
            else f"候选通过 {verified_batch_count}/2"
        ),
        "current_source_batch_sha256": current_source_batch,
    }
    state = {
        "schema_version": SCHEMA_STATE,
        "algorithm_version": config.algorithm_version,
        "config_sha256": f"sha256:{config.config_sha256}",
        "implementation_sha256": f"sha256:{implementation_sha256}",
        "input_state_sha256": f"sha256:{input_state_sha}",
        "source_commit": source_commit,
        "source_cutoff_at": format_timestamp(source_cutoff),
        "verified_source_batches": verified_source_batches,
        "production_acceptance": production_acceptance,
        "files": {
            relative_path: {
                "size_bytes": inspection.size_bytes,
                "line_count": inspection.line_count,
                "sha256": f"sha256:{inspection.sha256}",
            }
            for relative_path, inspection in sorted(inspections.items())
        },
    }

    target_parent = output_dir.resolve().parent
    target_parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix="recurring-prompt-build-", dir=str(target_parent))
    )
    build_dir = temporary_root / output_dir.name
    build_dir.mkdir(parents=True, exist_ok=True)
    temp_summary = temporary_root / summary_path.name
    temp_status = temporary_root / status_path.name
    try:
        write_jsonl(build_dir / "occurrences.jsonl", occurrences)
        write_jsonl(build_dir / "clusters.jsonl", clusters)
        write_json(build_dir / "agent_context.json", candidate_context)
        write_json(build_dir / "freshness.json", freshness)
        write_json(build_dir / "state.json", state)

        human_occurrences = sum(
            item["origin"] == "human_interactive" for item in occurrences
        )
        automation_occurrences = sum(
            item["origin"] == "codex_automation" for item in occurrences
        )
        run_manifest: dict[str, Any] = {
            "schema_version": SCHEMA_RUN,
            "algorithm_version": config.algorithm_version,
            "config_sha256": f"sha256:{config.config_sha256}",
            "implementation_sha256": f"sha256:{implementation_sha256}",
            "input_state_sha256": f"sha256:{input_state_sha}",
            "source_commit": source_commit,
            "analysis_completed_at": format_timestamp(as_of),
            "diagnostic_counter_scope": "processed_delta_for_this_run",
            "raw_files_seen": len(inspections),
            "new_files_processed": new_files,
            "appended_files_processed": appended_files,
            "reparsed_files": reparsed_files,
            "reused_files": len(reused_paths),
            **counters.as_dict(),
            "occurrences": len(occurrences),
            "human_occurrences": human_occurrences,
            "automation_occurrences": automation_occurrences,
            "clusters": len(clusters),
            "human_clusters": sum(
                item["origin"] == "human_interactive" for item in clusters
            ),
            "automation_clusters": sum(
                item["origin"] == "codex_automation" for item in clusters
            ),
            "llm_calls": 0,
            "llm_input_tokens": 0,
            "llm_output_tokens": 0,
            "embedding_calls": 0,
            "external_model_api_calls": 0,
            "raw_session_payload_exported": False,
            "derived_prompt_text_included": True,
            "derived_prompt_text_redacted": True,
            "injection_guard": {
                "status": "PASS",
                "human_high_risk_occurrences": 0,
                "human_injected_headers": 0,
                "retained_configured_marker_messages": counters.retained_configured_marker_messages,
            },
            "production_acceptance": production_acceptance,
            "status": "PASS",
        }
        temp_summary.write_text(
            render_summary(clusters, freshness, run_manifest, config),
            encoding="utf-8",
        )
        core_hashes = compute_output_hashes(build_dir, temp_summary)
        run_manifest["derived_payload_sha256"] = f"sha256:{sha256_bytes(canonical_json_bytes(core_hashes))}"
        temp_status.write_text(
            render_status(clusters, freshness, run_manifest),
            encoding="utf-8",
        )
        run_manifest["output_hashes"] = compute_output_hashes(
            build_dir, temp_summary, temp_status
        )
        write_json(build_dir / "run_manifest.json", run_manifest)

        if publish_atomically:
            atomic_publish_directory(build_dir, output_dir.resolve())
            summary_path.resolve().parent.mkdir(parents=True, exist_ok=True)
            status_path.resolve().parent.mkdir(parents=True, exist_ok=True)
            os.replace(temp_summary, summary_path.resolve())
            os.replace(temp_status, status_path.resolve())
        else:
            if output_dir.exists():
                shutil.rmtree(output_dir)
            shutil.copytree(build_dir, output_dir)
            summary_path.parent.mkdir(parents=True, exist_ok=True)
            status_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(temp_summary, summary_path)
            shutil.copy2(temp_status, status_path)
        return run_manifest
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root, ignore_errors=True)


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError as exc:
                raise AnalysisError(f"invalid JSONL {path}:{line_number}: {exc}") from exc
            if not isinstance(value, dict):
                raise AnalysisError(f"JSONL record must be an object: {path}:{line_number}")
            yield value


def validate_outputs(
    *,
    repo_root: Path,
    config_path: Path,
    output_dir: Path,
    summary_path: Path,
    status_path: Path,
    check_sources: bool = True,
) -> list[str]:
    config = RuntimeConfig.load(config_path)
    errors: list[str] = []
    required = {
        "occurrences.jsonl",
        "clusters.jsonl",
        "agent_context.json",
        "freshness.json",
        "run_manifest.json",
        "state.json",
    }
    missing = sorted(name for name in required if not (output_dir / name).is_file())
    if missing:
        return ["missing required outputs: " + ", ".join(missing)]
    if not summary_path.is_file():
        errors.append(f"missing human summary: {summary_path}")
    if not status_path.is_file():
        errors.append(f"missing human status: {status_path}")

    try:
        occurrences = list(iter_jsonl(output_dir / "occurrences.jsonl"))
        clusters = list(iter_jsonl(output_dir / "clusters.jsonl"))
        candidate_context = json.loads(
            (output_dir / "agent_context.json").read_text(encoding="utf-8")
        )
        freshness = json.loads((output_dir / "freshness.json").read_text(encoding="utf-8"))
        run_manifest = json.loads(
            (output_dir / "run_manifest.json").read_text(encoding="utf-8")
        )
        state = json.loads((output_dir / "state.json").read_text(encoding="utf-8"))
    except (AnalysisError, json.JSONDecodeError) as exc:
        return [str(exc)]

    cluster_ids = {str(item.get("cluster_id")) for item in clusters}
    occurrence_cluster_counts = collections.Counter(
        str(item["cluster_id"])
        for item in occurrences
        if item.get("cluster_id") is not None
    )
    occurrence_ids: set[str] = set()
    for item in occurrences:
        if item.get("schema_version") != SCHEMA_OCCURRENCE:
            errors.append("occurrence schema_version mismatch")
        if item.get("category") not in ALLOWED_CATEGORIES:
            errors.append(f"invalid occurrence category: {item.get('category')}")
        if item.get("origin") not in ALLOWED_ORIGINS:
            errors.append(f"invalid occurrence origin: {item.get('origin')}")
        occurrence_id = str(item.get("occurrence_id"))
        if occurrence_id in occurrence_ids:
            errors.append(f"duplicate occurrence_id: {occurrence_id}")
        occurrence_ids.add(occurrence_id)
        if item.get("cluster_id") is not None and str(item["cluster_id"]) not in cluster_ids:
            errors.append(f"occurrence points to unknown cluster: {item['cluster_id']}")
        pointer = item.get("source_pointer")
        if not isinstance(pointer, Mapping):
            errors.append(f"occurrence has invalid source_pointer: {occurrence_id}")
            continue
        relative_path = pointer.get("relative_path")
        if not isinstance(relative_path, str) or relative_path.startswith("/") or ".." in Path(relative_path).parts:
            errors.append(f"unsafe source path: {relative_path!r}")
        elif check_sources:
            source = repo_root / relative_path
            if not source.is_file():
                errors.append(f"source file missing: {relative_path}")
            else:
                line_no = int(pointer.get("jsonl_line", 0))
                state_line_count = int(
                    state.get("files", {}).get(relative_path, {}).get("line_count", 0)
                )
                if line_no < 1 or (state_line_count and line_no > state_line_count):
                    errors.append(f"source line out of range: {relative_path}:{line_no}")

    for cluster in clusters:
        if cluster.get("schema_version") != SCHEMA_CLUSTER:
            errors.append("cluster schema_version mismatch")
        category = cluster.get("category")
        if category not in ALLOWED_CATEGORIES:
            errors.append(f"invalid cluster category: {category}")
        cluster_id = str(cluster.get("cluster_id"))
        if int(cluster.get("count", -1)) != occurrence_cluster_counts[cluster_id]:
            errors.append(f"cluster count mismatch: {cluster_id}")
        if int(cluster.get("count", 0)) < config.minimum_cluster_count:
            errors.append(f"cluster below recurrence threshold: {cluster_id}")

    if candidate_context.get("schema_version") != SCHEMA_CONTEXT:
        errors.append("candidate_context schema_version mismatch")
    if candidate_context.get("status") != "candidate_not_routed":
        errors.append("candidate_context must remain candidate_not_routed")
    if int(candidate_context.get("item_count", 0)) > config.candidate_context_max_items:
        errors.append("candidate_context exceeds max items")
    if set(candidate_context.get("sections", {})) != ALLOWED_CATEGORIES:
        errors.append("candidate_context must expose exactly three category sections")

    if freshness.get("schema_version") != SCHEMA_FRESHNESS:
        errors.append("freshness schema_version mismatch")
    if run_manifest.get("schema_version") != SCHEMA_RUN:
        errors.append("run_manifest schema_version mismatch")
    if state.get("schema_version") != SCHEMA_STATE:
        errors.append("state schema_version mismatch")
    current_implementation = f"sha256:{sha256_bytes(Path(__file__).resolve().read_bytes())}"
    if state.get("implementation_sha256") != current_implementation:
        errors.append("state implementation_sha256 mismatch")
    if run_manifest.get("implementation_sha256") != current_implementation:
        errors.append("run_manifest implementation_sha256 mismatch")
    if any(
        int(run_manifest.get(key, -1)) != 0
        for key in (
            "llm_calls",
            "llm_input_tokens",
            "llm_output_tokens",
            "embedding_calls",
            "external_model_api_calls",
        )
    ):
        errors.append("LLM/embedding/external-model API usage must remain zero")
    if run_manifest.get("raw_session_payload_exported") is not False:
        errors.append("run_manifest raw_session_payload_exported must be false")
    if run_manifest.get("derived_prompt_text_included") is not True:
        errors.append("run_manifest must disclose derived prompt text inclusion")
    if run_manifest.get("derived_prompt_text_redacted") is not True:
        errors.append("run_manifest must disclose prompt-text redaction")
    if run_manifest.get("status") != "PASS":
        errors.append("run_manifest status must be PASS")
    batch_history = state.get("verified_source_batches")
    if not isinstance(batch_history, list) or not batch_history:
        errors.append("state verified_source_batches must be a non-empty list")
    elif len(batch_history) != len(set(batch_history)) or len(batch_history) > 8:
        errors.append("state verified_source_batches must be unique and capped at 8")
    acceptance = state.get("production_acceptance")
    if not isinstance(acceptance, Mapping):
        errors.append("state production_acceptance missing")
    else:
        expected_count = len(batch_history) if isinstance(batch_history, list) else 0
        if int(acceptance.get("verified_distinct_source_batches", -1)) != expected_count:
            errors.append("production_acceptance batch count mismatch")
        expected_status = "stable" if expected_count >= 2 else "candidate"
        if acceptance.get("status") != expected_status:
            errors.append("production_acceptance status mismatch")
        if batch_history and acceptance.get("current_source_batch_sha256") != batch_history[-1]:
            errors.append("production_acceptance current batch mismatch")
    if run_manifest.get("production_acceptance") != acceptance:
        errors.append("production_acceptance mismatch between state and run_manifest")
    injection_guard = run_manifest.get("injection_guard")
    if not isinstance(injection_guard, Mapping) or injection_guard.get("status") != "PASS":
        errors.append("run_manifest injection_guard status must be PASS")

    errors.extend(audit_human_injection_leakage(occurrences, candidate_context, config))

    if check_sources:
        # Reconstruct authoritative user turns directly from raw envelopes. Any surviving
        # response_item clause in a turn that also has event_msg is a hard provenance error.
        authoritative_event_turns: set[tuple[str, str]] = set()
        input_pattern = str(config.raw["input_glob"])
        for source_path in sorted(path for path in repo_root.glob(input_pattern) if path.is_file()):
            session_raw = source_path.name.split(".", 1)[0]
            session_key = namespaced_id("codex-session", session_raw)
            with source_path.open("rb") as handle:
                for raw_line in handle:
                    try:
                        raw_obj = json.loads(raw_line.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError):
                        continue
                    if not isinstance(raw_obj, Mapping):
                        continue
                    extracted = extract_user_message(raw_obj)
                    payload = raw_obj.get("payload")
                    if (
                        extracted is None
                        or extracted.source_kind != "event_msg"
                        or not isinstance(payload, Mapping)
                    ):
                        continue
                    turn_id = extract_turn_id(raw_obj, payload)
                    if turn_id:
                        authoritative_event_turns.add((session_key, str(turn_id)))
        for item in occurrences:
            pointer = item.get("source_pointer")
            turn_id = pointer.get("turn_id") if isinstance(pointer, Mapping) else None
            if (
                item.get("source_kind") == "response_item"
                and turn_id
                and (str(item.get("session_key")), str(turn_id))
                in authoritative_event_turns
            ):
                errors.append(
                    "response_item occurrence survived authoritative event_msg turn: "
                    + str(item.get("occurrence_id"))
                )

    expected_output_hashes = compute_output_hashes(output_dir, summary_path, status_path)
    if run_manifest.get("output_hashes") != expected_output_hashes:
        errors.append("run_manifest output_hashes mismatch")
    expected_core_hashes = compute_output_hashes(output_dir, summary_path)
    expected_payload_sha = f"sha256:{sha256_bytes(canonical_json_bytes(expected_core_hashes))}"
    if run_manifest.get("derived_payload_sha256") != expected_payload_sha:
        errors.append("run_manifest derived_payload_sha256 mismatch")

    scan_paths = [
        output_dir / "occurrences.jsonl",
        output_dir / "clusters.jsonl",
        output_dir / "agent_context.json",
        output_dir / "freshness.json",
        output_dir / "run_manifest.json",
        output_dir / "state.json",
        summary_path,
        status_path,
    ]
    for path in scan_paths:
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        for pattern in config.secret_patterns:
            match = pattern.search(text)
            if match and "[REDACTED_SECRET]" not in match.group(0):
                errors.append(f"possible secret in {path.name}: {pattern.pattern}")
                break
        for pattern in config.absolute_path_patterns:
            if pattern.search(text):
                errors.append(f"absolute local path in {path.name}: {pattern.pattern}")
                break

    return sorted(set(errors))


SEMANTIC_OUTPUT_FILES = (
    "occurrences.jsonl",
    "clusters.jsonl",
    "agent_context.json",
    "freshness.json",
    "state.json",
)


def compare_trees(left: Path, right: Path) -> list[str]:
    left_files = {
        path.relative_to(left).as_posix(): sha256_bytes(path.read_bytes())
        for path in left.rglob("*")
        if path.is_file()
    }
    right_files = {
        path.relative_to(right).as_posix(): sha256_bytes(path.read_bytes())
        for path in right.rglob("*")
        if path.is_file()
    }
    differences: list[str] = []
    for name in sorted(set(left_files) | set(right_files)):
        if left_files.get(name) != right_files.get(name):
            differences.append(name)
    return differences


def compare_semantic_outputs(left: Path, right: Path) -> list[str]:
    """Compare result-bearing outputs while ignoring run-local diagnostics."""
    differences: list[str] = []
    for name in SEMANTIC_OUTPUT_FILES:
        left_path = left / name
        right_path = right / name
        if not left_path.is_file() or not right_path.is_file():
            differences.append(name)
            continue
        if sha256_bytes(left_path.read_bytes()) != sha256_bytes(right_path.read_bytes()):
            differences.append(name)
    return differences
