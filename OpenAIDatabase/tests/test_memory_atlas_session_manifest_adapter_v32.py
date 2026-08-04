"""The join itself: live events must rebuild the ten views' inputs, redacted.

The event plane is lossless and carries whole transcripts. `memory_atlas.json`
is downloaded by the browser. So the single most important property here is not
that the counts are right — it is that nothing derived from message content can
cross from one to the other.
"""

from __future__ import annotations

import json

from OpenAIDatabase.scripts.memory_atlas_private.session_manifest_adapter import (
    ALLOWED_SESSION_FIELDS,
    build_daily_rows,
    build_session_rows,
)

PATH_A = "2026/08/04/rollout-2026-08-04T03-02-02-019fc893-4369-7632-9847-a0b19a6f5fd4.jsonl"
PATH_B = "2026/06/29/rollout-2026-06-29T19-33-28-019f1327-e289-73b3-903f-dbdf600fb2fd.jsonl"
SECRET = "sk-live-DO-NOT-LEAK-0123456789"


def _event(path: str, kind: str, inner: dict, stamp: str, source: str = "codex_sessions") -> dict:
    return {
        "source_id": source,
        "relative_path": path,
        "occurred_at": stamp,
        "payload": {"type": kind, "timestamp": stamp, "payload": inner},
    }


def _session(path: str) -> list[dict]:
    return [
        _event(path, "session_meta", {
            "id": "019fc893-4369-7632-9847-a0b19a6f5fd4",
            "cwd": "/Users/linzezhang/Documents/Codex/GithubProject/AgentDatabase",
            "originator": "Codex Desktop", "cli_version": "0.142.5",
            "client_source": "vscode", "model_provider": "openai",
            "base_instructions": {"text": "You are Codex. " + SECRET},
        }, "2026-08-04T03:02:02Z"),
        _event(path, "response_item", {"role": "user", "content": [{"text": SECRET}]}, "2026-08-04T03:02:10Z"),
        _event(path, "response_item", {"role": "assistant", "content": [{"text": "reply " + SECRET}]}, "2026-08-04T03:03:00Z"),
        _event(path, "response_item", {"type": "function_call", "name": "exec_command", "arguments": SECRET}, "2026-08-04T03:04:00Z"),
        _event(path, "event_msg", {"type": "error", "message": SECRET}, "2026-08-04T03:05:00Z"),
        _event(path, "event_msg", {"type": "task_started"}, "2026-08-04T03:02:03Z"),
    ]


def test_sessions_are_grouped_and_counted() -> None:
    rows = build_session_rows(_session(PATH_A))
    assert len(rows) == 1
    row = rows[0]
    assert row["session_id"] == "019fc893-4369-7632-9847-a0b19a6f5fd4"
    assert row["day"] == "2026-08-04"
    assert row["started_at"] == "2026-08-04T03:02:02Z"
    assert row["updated_at"] == "2026-08-04T03:05:00Z"
    assert row["event_count"] == 6
    assert (row["message_count"], row["user_message_count"], row["assistant_message_count"]) == (2, 1, 1)
    assert row["tool_call_count"] == 1
    assert row["error_event_count"] == 1
    assert row["originator"] == "Codex Desktop"


def test_no_transcript_or_secret_can_reach_the_browser_payload() -> None:
    rows = build_session_rows(_session(PATH_A))
    serialized = json.dumps(rows + build_daily_rows(rows), ensure_ascii=False)
    assert SECRET not in serialized
    assert "You are Codex" not in serialized
    assert "exec_command" not in serialized
    # And the absolute path that names the account is never emitted, only a hash
    # and the trailing two segments.
    assert "/Users/linzezhang" not in serialized
    assert rows[0]["cwd_label"] == "GithubProject/AgentDatabase"
    assert len(rows[0]["cwd_hash"]) == 16


def test_the_emitted_field_set_is_closed() -> None:
    # A future field added upstream must not silently ride along into the
    # browser payload; it has to be added to the allowlist deliberately.
    for row in build_session_rows(_session(PATH_A)):
        assert set(row) <= ALLOWED_SESSION_FIELDS, set(row) - ALLOWED_SESSION_FIELDS


def test_archived_sessions_are_labelled_and_still_counted() -> None:
    events = [
        _event(PATH_B, "session_meta", {"id": "old"}, "2026-06-29T19:33:28Z", source="codex_archived_sessions"),
    ]
    rows = build_session_rows(events)
    assert rows[0]["source_bucket"] == "archived_sessions"
    assert rows[0]["day"] == "2026-06-29"


def test_events_from_other_sources_are_ignored() -> None:
    noise = [_event(PATH_A, "session_meta", {"id": "x"}, "2026-08-04T03:02:02Z", source="openaidatabase_live_data")]
    assert build_session_rows(noise) == []


def test_daily_activity_aggregates_every_day_present() -> None:
    rows = build_session_rows(_session(PATH_A) + [
        _event(PATH_B, "session_meta", {"id": "old"}, "2026-06-29T19:33:28Z"),
        _event(PATH_B, "response_item", {"role": "user", "content": [{"text": "hi"}]}, "2026-06-29T19:34:00Z"),
    ])
    daily = build_daily_rows(rows)
    assert [d["date"] for d in daily] == ["2026-06-29", "2026-08-04"]
    assert daily[1]["conversation_count"] == 1
    assert daily[1]["message_count"] == 2
    assert daily[1]["tool_call_count"] == 1
    assert all(d["schema_version"] == "codex_daily_activity.v1" for d in daily)


def test_a_session_with_no_metadata_still_produces_a_row() -> None:
    # Sessions rotate; a run may capture only the tail of one. Dropping it would
    # silently under-count, which is the failure this whole task exists to fix.
    rows = build_session_rows([_event(PATH_B, "event_msg", {"type": "task_started"}, "2026-06-29T19:33:28Z")])
    assert len(rows) == 1
    assert rows[0]["session_id"] == "019f1327-e289-73b3-903f-dbdf600fb2fd"
    assert rows[0]["event_count"] == 1
