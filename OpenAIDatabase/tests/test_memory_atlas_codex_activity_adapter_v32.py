"""The join itself: live events must rebuild the ten views' inputs, redacted.

The event plane is lossless and carries whole transcripts. `memory_atlas.json`
is downloaded by the browser. So the single most important property here is not
that the counts are right — it is that nothing derived from message content can
cross from one to the other.
"""

from __future__ import annotations

import json

from OpenAIDatabase.scripts.memory_atlas_private.codex_activity_adapter import (
    ALLOWED_SESSION_FIELDS,
    build_daily_rows,
    build_session_rows,
)

PATH_A = "2026/08/04/rollout-2026-08-04T03-02-02-019fc893-4369-7632-9847-a0b19a6f5fd4.jsonl"
PATH_B = "2026/06/29/rollout-2026-06-29T19-33-28-019f1327-e289-73b3-903f-dbdf600fb2fd.jsonl"
# Assembled at runtime. A key-shaped literal in a tracked file trips the
# repository's own secret scanner, which is correct behaviour — so the
# canary is built from parts and never appears whole in the source.
SECRET = "sk-" + "live-" + "CANARY-MUST-NOT-LEAK-" + "0123456789abcdef"


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


def test_reconcile_regenerates_the_snapshot_the_ten_views_read() -> None:
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    assert "regenerate_atlas_snapshot(" in source
    assert 'output=self.config.web_data_dir / "memory_atlas.json"' in source
    assert '"atlas_snapshot": atlas_rebuild' in source


def test_the_regenerated_snapshot_is_what_nginx_serves() -> None:
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    compose = (repo / "ops" / "memory-atlas" / "docker-compose.yml").read_text(encoding="utf-8")
    assert "/srv/linze/apps/memory-atlas/shared/data:/usr/share/nginx/live:ro" in compose
    conf = (repo / "ops" / "memory-atlas" / "nginx" / "default.conf").read_text(encoding="utf-8")
    assert "root /usr/share/nginx/live;" in conf
    # A failed regeneration must fall back to the shipped snapshot, not 404.
    assert "@atlas_release_snapshot" in conf
    assert "try_files /memory_atlas.json =404;" in conf


def test_regeneration_refuses_to_publish_a_partial_snapshot(tmp_path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import regenerate_atlas_snapshot

    database = tmp_path / "db"
    (database / "data" / "processed" / "codex").mkdir(parents=True)
    (database / "data" / "memory").mkdir(parents=True)
    (database / "scripts").mkdir(parents=True)
    (database / "scripts" / "build_memory_atlas_data.py").write_text("", encoding="utf-8")
    served = tmp_path / "web" / "memory_atlas.json"
    served.parent.mkdir(parents=True)
    served.write_text('{"kept": "last good"}', encoding="utf-8")

    class _Failed:
        returncode = 1
        stdout = ""
        stderr = "builder exploded"

    result = regenerate_atlas_snapshot(
        _session(PATH_A), database_dir=database, work_dir=tmp_path / "work",
        output=served, runner=lambda *a, **k: _Failed(),
    )
    assert result["state"] == "FAILED"
    assert json.loads(served.read_text(encoding="utf-8")) == {"kept": "last good"}


def test_regeneration_skips_when_a_run_carries_no_sessions(tmp_path) -> None:
    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import regenerate_atlas_snapshot

    result = regenerate_atlas_snapshot(
        [], database_dir=tmp_path, work_dir=tmp_path / "work", output=tmp_path / "out.json",
    )
    assert result["state"] == "SKIPPED"
    assert not (tmp_path / "out.json").exists()


def test_the_adapter_is_fed_dicts_not_dataclasses() -> None:
    """The end-to-end tests caught this: _iter_events yields NormalizedEvent
    instances, and the adapter reads events with .get(). It is fed the already
    materialized rows, which also avoids reading the batch file twice."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    import re

    call = re.search(r"atlas_rebuild = regenerate_atlas_snapshot\(\s*(\w+)", source)
    assert call and call.group(1) == "live_events", call.group(1) if call else None
    assert "_iter_events(temporary)," not in source.split("regenerate_atlas_snapshot")[1][:200]


def test_this_slice_adds_no_file_the_release_audit_would_reject() -> None:
    """The repository forbids tracked filenames matching `sessions?`, to stop raw
    session data being committed, and CI caught this slice's first filenames
    after the local gate had gone green.

    The first version of this check reimplemented the rule and was wrong — it
    flagged pre-existing, legitimately allowlisted fixtures. It now asks the
    authority instead of inventing a stricter one.
    """
    import sys
    from pathlib import Path

    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo / "OpenAIDatabase" / "scripts"))
    from audit_memory_atlas_release import ALLOWED_TRACKED_FILES, forbidden_name_pattern

    added = [
        "scripts/memory_atlas_private/codex_activity_adapter.py",
        "tests/test_memory_atlas_codex_activity_adapter_v32.py",
    ]
    for name in added:
        assert (repo / "OpenAIDatabase" / name).is_file(), name
        assert name in ALLOWED_TRACKED_FILES or not forbidden_name_pattern(
            name, allow_public_raw_sessions=True
        ), f"the release audit would reject {name}"


def test_the_join_actually_moves_the_graph_the_ten_views_render(tmp_path) -> None:
    """The acceptance criterion for "把数据打通", run through the real builder.

    Adding a panel that read the live plane did not change the ten views; only
    replacing their frozen input does. The frozen snapshot reports 128 Codex
    sessions and a 2026-07-16 timestamp, so a rebuild from N sessions must
    report N and a newer timestamp — otherwise the join is decorative.
    """
    from pathlib import Path

    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import regenerate_atlas_snapshot

    repo = Path(__file__).resolve().parents[2]
    database = repo / "OpenAIDatabase"
    frozen = json.loads(
        (database / "data/derived/visualization/memory_atlas.json").read_text(encoding="utf-8")
    )["overview"]

    events = []
    for index in range(40):
        uuid = f"019fc893-4369-7632-9847-a0b19a6f{index:04d}"
        day = 10 + index % 20
        folder, stamp = f"2026/07/{day:02d}", f"2026-07-{day:02d}T03:{index % 60:02d}:02Z"
        events.append(_event(f"{folder}/rollout-{stamp}-{uuid}.jsonl", "session_meta",
                             {"id": uuid, "cwd": "/x/y", "originator": "Codex Desktop"}, stamp))

    output = tmp_path / "memory_atlas.json"
    result = regenerate_atlas_snapshot(
        events, database_dir=database, work_dir=tmp_path / "work", output=output
    )
    assert result["state"] == "PUBLISHED", result
    assert result["session_count"] == 40

    rebuilt = json.loads(output.read_text(encoding="utf-8"))["overview"]
    assert frozen["codex_session_count"] == 128, "the frozen baseline moved; re-read it"
    assert rebuilt["codex_session_count"] == 40, rebuilt["codex_session_count"]
    assert rebuilt["generated_at"] > frozen["generated_at"]
    # The graph itself has to grow, not just a counter.
    assert rebuilt["node_count"] > 0 and rebuilt["edge_count"] > 0


def test_the_repositorys_own_data_is_never_rewritten(tmp_path) -> None:
    """The work tree is hardlinked, so writing through a link would rewrite the
    repository's own manifest. The link is broken before writing."""
    import hashlib
    from pathlib import Path

    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import regenerate_atlas_snapshot

    database = Path(__file__).resolve().parents[2] / "OpenAIDatabase"
    tracked = database / "data/processed/codex/codex_session_manifest.jsonl"
    before = hashlib.sha256(tracked.read_bytes()).hexdigest()
    regenerate_atlas_snapshot(
        _session(PATH_A), database_dir=database, work_dir=tmp_path / "work",
        output=tmp_path / "out.json",
    )
    assert hashlib.sha256(tracked.read_bytes()).hexdigest() == before


def test_a_hardlink_that_cannot_cross_devices_falls_back_to_copying() -> None:
    """Production put the release tree and the work directory on different
    filesystems, so os.link raised EXDEV and the whole reconcile died."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    assert "def _link_or_copy(" in source
    assert "except OSError:" in source
    assert "shutil.copy2(src, dst)" in source
    assert "copy_function=_link_or_copy" in source
    assert "copy_function=os.link" not in source


def test_a_failed_graph_rebuild_cannot_cancel_the_reconcile() -> None:
    """The reconcile also publishes the live snapshot and the status projection.
    When the rebuild raised, all of it was lost and the deployment rolled back."""
    source = (
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "scripts" / "memory_atlas_private" / "pipeline.py"
    ).read_text(encoding="utf-8")
    guarded = source[source.index("atlas_rebuild = regenerate_atlas_snapshot") - 400:]
    assert "try:" in guarded.split("atlas_rebuild = regenerate_atlas_snapshot")[0]
    assert 'atlas_rebuild = {"state": "FAILED", "reason":' in source


def test_the_served_snapshot_is_readable_by_the_container(tmp_path) -> None:
    """The join was correct on disk and invisible in the browser: the pipeline
    writes 0600 and nginx runs unprivileged inside the container, so it fell
    back to the snapshot baked into the release and kept showing July."""
    import os
    import stat
    from pathlib import Path

    from OpenAIDatabase.scripts.memory_atlas_private.pipeline import regenerate_atlas_snapshot

    database = Path(__file__).resolve().parents[2] / "OpenAIDatabase"
    output = tmp_path / "web" / "data" / "memory_atlas.json"
    result = regenerate_atlas_snapshot(
        _session(PATH_A), database_dir=database, work_dir=tmp_path / "work", output=output
    )
    assert result["state"] == "PUBLISHED", result
    assert stat.S_IMODE(output.stat().st_mode) & 0o004, "the container cannot read it"
    for directory in (output.parent, output.parent.parent):
        assert stat.S_IMODE(directory.stat().st_mode) & 0o001, f"{directory} is not traversable"
    # The staged tree must not survive: it is ~100 MB every fifteen minutes.
    assert not (tmp_path / "work" / "atlas-build").exists()
