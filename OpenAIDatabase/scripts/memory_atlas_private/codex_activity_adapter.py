from __future__ import annotations

"""Rebuild the atlas graph's session inputs from the live event plane.

The ten original views read `data/processed/codex/codex_session_manifest.jsonl`
and `codex_daily_activity.jsonl`, written by a local sync that last ran on
2026-07-17. They therefore showed 128 sessions over 7 days while the capture
plane already held 505 session files over 28 days. Both planes describe the
same Codex sessions; only the frozen one was wired to the product.

This rebuilds those two files from the canonical event union, so the same
builder produces a current graph with no local script and no change to the
capture automation.

**The event plane is lossless and carries full transcripts. This adapter emits
counts, timestamps and identity only.** Nothing derived from message content
leaves this module — `memory_atlas.json` is downloaded by the browser, and the
manifest contract it satisfies is
`redacted_summary_only_no_raw_transcript_no_plaintext_secret`.
"""

import hashlib
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable, Mapping

SESSION_SOURCES = {"codex_sessions", "codex_archived_sessions"}
ROLLOUT = re.compile(r"rollout-(?P<stamp>\d{4}-\d{2}-\d{2}T[\d-]+)-(?P<uuid>[0-9a-f-]{36})\.jsonl$")
DAY_IN_PATH = re.compile(r"(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})")

# Every field this adapter is allowed to emit. Anything not listed cannot reach
# the browser, and a test asserts the produced rows never exceed this set.
ALLOWED_SESSION_FIELDS = {
    "schema_version", "session_id", "source_bucket", "day", "started_day", "updated_day",
    "started_at", "updated_at", "event_count", "message_count", "user_message_count",
    "assistant_message_count", "tool_call_count", "error_event_count", "abort_count",
    "decode_error_count", "activity_score", "cwd_hash", "cwd_label", "originator",
    "client_source", "cli_version", "model_provider", "backup_policy", "credential_boundary",
    "derived_from", "record_count",
}


def _parse(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except ValueError:
        return None


def _cwd_label(cwd: object) -> tuple[str, str]:
    """A short, stable label plus a hash. Never the absolute path."""
    text = str(cwd or "").strip()
    if not text:
        return "", ""
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
    parts = [part for part in text.replace("\\", "/").split("/") if part]
    # Home directories carry the account name; keep only the trailing two
    # segments, which name the project rather than the person.
    return digest, "/".join(parts[-2:]) if parts else ""


def _activity_score(messages: int, tools: int, events: int) -> int:
    """Same shape as the retired sync: messages and tool calls dominate, events damp.

    Documented rather than reverse-engineered exactly — the retired writer is
    gone, so this is a stated formula, not a claim of byte-compatibility.
    """
    return int(messages * 10 + tools * 2 + min(events, 500) // 5)


def build_session_rows(events: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "records": 0, "messages": 0, "user": 0, "assistant": 0, "tools": 0,
            "errors": 0, "aborts": 0, "first": None, "last": None, "meta": {},
            "bucket": "sessions", "path": "",
        }
    )
    for event in events:
        if event.get("source_id") not in SESSION_SOURCES:
            continue
        path = str(event.get("relative_path") or "")
        if not path:
            continue
        row = grouped[path]
        row["path"] = path
        row["records"] += 1
        if event.get("source_id") == "codex_archived_sessions":
            row["bucket"] = "archived_sessions"
        payload = event.get("payload") if isinstance(event.get("payload"), Mapping) else {}
        stamp = _parse(payload.get("timestamp")) or _parse(event.get("occurred_at"))
        if stamp:
            if row["first"] is None or stamp < row["first"]:
                row["first"] = stamp
            if row["last"] is None or stamp > row["last"]:
                row["last"] = stamp
        kind = payload.get("type")
        inner = payload.get("payload") if isinstance(payload.get("payload"), Mapping) else {}
        if kind == "session_meta":
            # Identity only. base_instructions and any other text is ignored.
            for field in ("originator", "cli_version", "client_source", "model_provider", "cwd", "id"):
                if isinstance(inner.get(field), str):
                    row["meta"].setdefault(field, inner[field])
        elif kind == "response_item":
            item_type = str(inner.get("type") or "")
            role = str(inner.get("role") or "")
            if item_type in {"function_call", "local_shell_call", "custom_tool_call"}:
                row["tools"] += 1
            elif role in {"user", "assistant"}:
                row["messages"] += 1
                row["user" if role == "user" else "assistant"] += 1
        elif kind == "event_msg":
            event_type = str(inner.get("type") or "")
            if event_type in {"error", "stream_error"}:
                row["errors"] += 1
            elif event_type in {"turn_aborted", "task_aborted"}:
                row["aborts"] += 1

    rows: list[dict[str, Any]] = []
    for path, row in sorted(grouped.items()):
        match = ROLLOUT.search(path)
        day_match = DAY_IN_PATH.search(path)
        session_id = row["meta"].get("id") or (match.group("uuid") if match else path)
        started = row["first"]
        updated = row["last"] or started
        day = (
            f"{day_match.group('y')}-{day_match.group('m')}-{day_match.group('d')}"
            if day_match
            else (started.date().isoformat() if started else "")
        )
        cwd_hash, cwd_label = _cwd_label(row["meta"].get("cwd"))
        rows.append(
            {
                "schema_version": "codex_session_manifest.v1",
                "session_id": str(session_id),
                "source_bucket": row["bucket"],
                "day": day,
                "started_day": started.date().isoformat() if started else day,
                "updated_day": updated.date().isoformat() if updated else day,
                "started_at": started.isoformat().replace("+00:00", "Z") if started else "",
                "updated_at": updated.isoformat().replace("+00:00", "Z") if updated else "",
                "event_count": row["records"],
                "record_count": row["records"],
                "message_count": row["messages"],
                "user_message_count": row["user"],
                "assistant_message_count": row["assistant"],
                "tool_call_count": row["tools"],
                "error_event_count": row["errors"],
                "abort_count": row["aborts"],
                "decode_error_count": 0,
                "activity_score": _activity_score(row["messages"], row["tools"], row["records"]),
                "cwd_hash": cwd_hash,
                "cwd_label": cwd_label,
                "originator": str(row["meta"].get("originator") or ""),
                "client_source": str(row["meta"].get("client_source") or ""),
                "cli_version": str(row["meta"].get("cli_version") or ""),
                "model_provider": str(row["meta"].get("model_provider") or ""),
                "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
                "credential_boundary": "credentials_not_transcript",
                "derived_from": "canonical_event_union",
            }
        )
    return rows


def build_daily_rows(session_rows: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_day: dict[str, Counter] = defaultdict(Counter)
    for row in session_rows:
        day = str(row.get("day") or "")
        if not day:
            continue
        bucket = by_day[day]
        bucket["conversation_count"] += 1
        for field in (
            "message_count", "user_message_count", "assistant_message_count",
            "tool_call_count", "error_event_count", "abort_count", "activity_score",
        ):
            bucket[field] += int(row.get(field) or 0)
    out: list[dict[str, Any]] = []
    for day in sorted(by_day):
        bucket = by_day[day]
        score = int(bucket["activity_score"])
        out.append(
            {
                "date": day,
                "conversation_count": int(bucket["conversation_count"]),
                "message_count": int(bucket["message_count"]),
                "user_message_count": int(bucket["user_message_count"]),
                "assistant_message_count": int(bucket["assistant_message_count"]),
                "tool_call_count": int(bucket["tool_call_count"]),
                "error_event_count": int(bucket["error_event_count"]),
                "abort_count": int(bucket["abort_count"]),
                "activity_score": score,
                "activity_level": 1 if score < 500 else (2 if score < 2000 else 3),
                "candidate_count": 0,
                "core_memory_count": 0,
                "decision_count": 0,
                "memory_count": 0,
                "mid_long_memory_count": 0,
                "schema_version": "codex_daily_activity.v1",
                "derived_from": "canonical_event_union",
            }
        )
    return out
