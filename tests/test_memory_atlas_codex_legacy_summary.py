from __future__ import annotations

import hashlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ATLASCTL = SCRIPTS / "atlasctl.py"


def load_module():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module("memory_atlas_cli.codex_legacy_summary")


def json_bytes(payload: object) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def write_bytes(database: Path, relative: str, payload: bytes) -> None:
    path = database / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def write_json(database: Path, relative: str, payload: object) -> None:
    write_bytes(database, relative, json_bytes(payload))


def write_jsonl(database: Path, relative: str, rows: list[dict]) -> None:
    write_bytes(
        database,
        relative,
        "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows).encode(),
    )


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare_fixture(base: Path) -> tuple[Path, list[str]]:
    module = load_module()
    database = base / "db"
    for relative in (module.CONTRACT_PATH, module.MODEL_PARAMETERS_PATH):
        source = ROOT / relative
        target = database / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    behavior = {
        "schema_version": "memory_atlas.codex_behavior_summary.v1_2_1_s07_p2_t1",
        "source_truth": {
            "kind": "derived_from_verified_recoverable_sanitized_raw_archives",
            "full_raw_backup": False,
            "recoverable_sanitized_raw_available": True,
        },
        "archive_count": 1,
        "session_count": 1,
    }
    behavior_payload = json_bytes(behavior)
    write_bytes(database, module.CANONICAL_BEHAVIOR_PATH.as_posix(), behavior_payload)
    derived_state = {
        "schema_version": "memory_atlas.codex_derived_state.v1_2_1_s07_p2_t1",
        "output_hashes": {
            module.CANONICAL_BEHAVIOR_PATH.as_posix(): {
                "sha256": hashlib.sha256(behavior_payload).hexdigest(),
                "byte_size": len(behavior_payload),
            }
        },
    }
    write_json(database, module.DERIVED_STATE_PATH.as_posix(), derived_state)

    session = {
        "schema_version": "codex_session_manifest.v1",
        "session_id": "session-fixture",
        "day": "2026-07-15",
        "message_count": 3,
        "tool_call_count": 4,
        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
        "fixture_field": "preserve-session",
    }
    daily = {"date": "2026-07-15", "conversation_count": 1, "fixture_field": "preserve-day"}
    snapshot = {
        "schema_version": "codex_activity_snapshot.v1",
        "generated_at": "2026-07-15T00:00:00Z",
        "source": "real_codex_local_data",
        "backup_policy": "redacted_summary_only_no_raw_transcript_no_plaintext_secret",
        "session_count": 1,
        "message_count": 3,
        "tool_call_count": 4,
        "fixture_field": "preserve-snapshot",
    }
    recommendations = {
        "schema_version": "codex_agent_recommendations.v1",
        "generated_at": "2026-07-15T00:00:00Z",
        "source": "real_codex_local_sessions_redacted_summary",
        "session_count": 1,
        "top_topics": [{"label": "fixture", "count": 1}],
        "memory": {"current": [{"id": "m1", "title": "keep"}], "added": [], "modified": [], "deleted": []},
        "meta_data": {"current": [], "added": [], "modified": [], "deleted": []},
        "fixture_field": "preserve-recommendations",
    }
    write_jsonl(database, module.LEGACY_OUTPUTS["session_manifest"], [session])
    write_jsonl(database, module.LEGACY_OUTPUTS["daily_activity"], [daily])
    write_json(database, module.LEGACY_OUTPUTS["processed_snapshot"], snapshot)
    write_json(database, module.LEGACY_OUTPUTS["derived_snapshot"], snapshot)
    write_json(database, module.LEGACY_OUTPUTS["recommendations"], recommendations)
    write_bytes(
        database,
        module.LEGACY_OUTPUTS["behavior_report"],
        "# Codex fixture report\n\n- keep this report line\n".encode(),
    )

    atlas = {
        "schema_version": "memory_atlas.v1",
        "overview": {"generated_at": "2026-07-15T01:00:00Z", "node_count": 1, "edge_count": 0},
        "source_contract": {"source_files": {}},
        "data_sources": [{"id": "codex", "label": "Codex", "record_types": ["legacy"]}],
        "agent_recommendations": recommendations,
        "codex_publication": {"counts": {"event_count": 1, "facet_count": 1}},
        "fixture_field": "preserve-atlas",
    }
    atlas_payload = json_bytes(atlas)
    write_bytes(database, module.CONSUMER_OUTPUTS["atlas_snapshot"], atlas_payload)
    atlas_state = {
        "schema_version": "memory_atlas.codex_atlas_publication_state.v1_2_1_s07_p2_t2",
        "outputs": {
            "atlas_snapshot": {
                "path": module.CONSUMER_OUTPUTS["atlas_snapshot"],
                "sha256": hashlib.sha256(atlas_payload).hexdigest(),
                "byte_size": len(atlas_payload),
            },
            "weekly_report": {
                "path": "data/derived/weekly/fixture.memory_atlas_weekly_report.md",
                "sha256": hashlib.sha256(b"weekly\n").hexdigest(),
                "byte_size": len(b"weekly\n"),
            },
        },
        "fixture_field": "preserve-atlas-state",
    }
    write_json(database, module.ATLAS_STATE_PATH.as_posix(), atlas_state)
    write_bytes(database, "data/derived/weekly/fixture.memory_atlas_weekly_report.md", b"weekly\n")
    agent_context = {
        "schema_version": "agent_context_pack.v1",
        "source_files": {},
        "behavior": {"session_count": 1},
        "safety": {"raw_transcripts_included": False},
        "fixture_field": "preserve-context",
    }
    write_json(database, module.CONSUMER_OUTPUTS["agent_context_json"], agent_context)
    write_bytes(
        database,
        module.CONSUMER_OUTPUTS["agent_context_markdown"],
        "# Agent Context fixture\n\n- keep this context line\n".encode(),
    )

    protected = [
        "data/raw_archives/codex/fixture/source.bin",
        "data/public_raw/codex/fixture.json",
        module.RAW_LEDGER_PATH.as_posix(),
        "data/sync_state/codex.json",
    ]
    for index, relative in enumerate(protected):
        write_bytes(database, relative, f"protected-{index}\n".encode())
    return database, protected


class CodexLegacySummaryTests(unittest.TestCase):
    def test_contract_and_model_freeze_truth_and_phase_boundary(self) -> None:
        module = load_module()
        self.assertEqual(module.load_codex_legacy_summary_contract(ROOT), module.EXPECTED_CONTRACT)
        self.assertEqual(module.EXPECTED_CONTRACT["semantics"]["full_raw_backup"], False)
        self.assertEqual(module.EXPECTED_CONTRACT["semantics"]["recoverable_raw_backup"], False)
        self.assertEqual(module.EXPECTED_PHASE_BOUNDARY["next_task"], "S07-P3-T1")

    def test_normalizes_metadata_free_legacy_payload_additively_and_rejects_conflicts(self) -> None:
        module = load_module()
        legacy = {"schema_version": "codex_activity_snapshot.v1", "fixture": {"keep": True}}
        normalized = module.normalize_legacy_summary_payload(legacy, "processed_activity_snapshot")
        self.assertEqual(legacy, {"schema_version": "codex_activity_snapshot.v1", "fixture": {"keep": True}})
        self.assertEqual(normalized["schema_version"], legacy["schema_version"])
        self.assertEqual(normalized["fixture"], legacy["fixture"])
        self.assertIs(normalized["summary_semantics"]["full_raw_backup"], False)
        self.assertEqual(
            normalized["summary_semantics"]["canonical_raw_source"]["availability"],
            "not_asserted_by_legacy_summary",
        )
        with self.assertRaisesRegex(module.CodexLegacySummaryError, "conflicting_raw_claim"):
            module.normalize_legacy_summary_payload(
                {"summary_semantics": {"full_raw_backup": True}}, "snapshot"
            )

    def test_real_fixture_migration_preserves_old_fields_updates_consumers_and_is_idempotent(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database, protected = prepare_fixture(Path(temp_dir))
            protected_before = {relative: sha256(database / relative) for relative in protected}
            before_dry_run = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            preview = module.migrate_codex_legacy_summary(
                database, dry_run=True, migrated_at="2026-07-16T00:00:00Z"
            )
            after_dry_run = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before_dry_run, after_dry_run)
            self.assertEqual(preview["status"], "PASS")
            self.assertTrue(preview["would_write_files"])

            result = module.migrate_codex_legacy_summary(
                database, migrated_at="2026-07-16T00:00:00Z"
            )
            expected_changes = set(module.LEGACY_OUTPUTS.values()) | {
                module.CONSUMER_OUTPUTS["atlas_snapshot"],
                module.ATLAS_STATE_PATH.as_posix(),
                module.CONSUMER_OUTPUTS["agent_context_json"],
                module.CONSUMER_OUTPUTS["agent_context_markdown"],
                module.STATE_PATH.as_posix(),
            }
            self.assertEqual(set(result["changed_paths"]), expected_changes)
            self.assertFalse(result["raw_mutation"])
            self.assertEqual(
                protected_before,
                {relative: sha256(database / relative) for relative in protected},
            )

            sessions = [
                json.loads(line)
                for line in (database / module.LEGACY_OUTPUTS["session_manifest"]).read_text().splitlines()
            ]
            snapshot = json.loads((database / module.LEGACY_OUTPUTS["processed_snapshot"]).read_text())
            recommendations = json.loads((database / module.LEGACY_OUTPUTS["recommendations"]).read_text())
            atlas = json.loads((database / module.CONSUMER_OUTPUTS["atlas_snapshot"]).read_text())
            atlas_state = json.loads((database / module.ATLAS_STATE_PATH).read_text())
            context = json.loads((database / module.CONSUMER_OUTPUTS["agent_context_json"]).read_text())
            state = json.loads((database / module.STATE_PATH).read_text())
            self.assertEqual(sessions[0]["schema_version"], "codex_session_manifest.v1")
            self.assertEqual(sessions[0]["fixture_field"], "preserve-session")
            self.assertEqual(snapshot["schema_version"], "codex_activity_snapshot.v1")
            self.assertEqual(snapshot["fixture_field"], "preserve-snapshot")
            self.assertEqual(recommendations["fixture_field"], "preserve-recommendations")
            self.assertIs(recommendations["summary_semantics"]["full_raw_backup"], False)
            self.assertEqual(
                recommendations["summary_semantics"]["canonical_raw_source"]["availability"],
                "verified_recoverable_sanitized_archives",
            )
            self.assertEqual(atlas["fixture_field"], "preserve-atlas")
            self.assertIn("不是 full raw backup", atlas["data_sources"][0]["description"])
            self.assertIs(
                atlas["codex_publication"]["legacy_summary_compatibility"]["full_raw_backup"],
                False,
            )
            atlas_payload = (database / module.CONSUMER_OUTPUTS["atlas_snapshot"]).read_bytes()
            self.assertEqual(
                atlas_state["outputs"]["atlas_snapshot"]["sha256"],
                hashlib.sha256(atlas_payload).hexdigest(),
            )
            self.assertFalse(context["safety"]["full_raw_backup"])
            self.assertEqual(state["legacy_counts"]["legacy_session_count"], 1)
            self.assertEqual(state["phase_boundary"], module.EXPECTED_PHASE_BOUNDARY)

            mtimes = {
                relative: (database / relative).stat().st_mtime_ns
                for relative in expected_changes
            }
            replay = module.migrate_codex_legacy_summary(database)
            self.assertEqual(replay["outcome"], "NO_CHANGES")
            self.assertEqual(replay["changed_paths"], [])
            self.assertEqual(
                mtimes,
                {relative: (database / relative).stat().st_mtime_ns for relative in expected_changes},
            )

    def test_transaction_rolls_back_every_changed_summary_on_post_replace_failure(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _protected = prepare_fixture(Path(temp_dir))
            before = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            original_fsync = module._fsync_directory
            calls = 0

            def fail_once(path: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 3:
                    raise OSError("fixture post-replace fsync failure")
                original_fsync(path)

            with mock.patch.object(module, "_fsync_directory", side_effect=fail_once):
                with self.assertRaisesRegex(OSError, "post-replace"):
                    module.migrate_codex_legacy_summary(
                        database, migrated_at="2026-07-16T00:00:00Z"
                    )
            after = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file() and ".tmp" not in path.name
            }
            self.assertEqual(before, after)
            self.assertEqual(list(database.rglob("*.tmp")), [])

    def test_conflicting_existing_claim_fails_before_any_write(self) -> None:
        module = load_module()
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _protected = prepare_fixture(Path(temp_dir))
            snapshot_path = database / module.LEGACY_OUTPUTS["processed_snapshot"]
            snapshot = json.loads(snapshot_path.read_text())
            snapshot["summary_semantics"] = {
                "artifact_role": "redacted_derived_summary",
                "output_policy": "derived_summary_not_full_raw_backup",
                "full_raw_backup": True,
                "recoverable_raw_backup": False,
                "raw_message_text_included": False,
                "plaintext_credentials_included": False,
                "local_absolute_paths_included": False,
            }
            snapshot_path.write_bytes(json_bytes(snapshot))
            before = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            with self.assertRaisesRegex(module.CodexLegacySummaryError, "conflicting_raw_claim"):
                module.migrate_codex_legacy_summary(database)
            after = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            self.assertEqual(before, after)

    def test_atlasctl_dry_run_routes_to_compatibility_migration_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _protected = prepare_fixture(Path(temp_dir))
            before = {
                path.relative_to(database).as_posix(): path.read_bytes()
                for path in database.rglob("*")
                if path.is_file()
            }
            result = subprocess.run(
                [
                    sys.executable,
                    str(ATLASCTL),
                    "analyze",
                    "--stage",
                    "codex-legacy-summary",
                    "--database-dir",
                    str(database),
                    "--dry-run",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "PASS")
            self.assertTrue(payload["would_write_files"])
            self.assertFalse(payload["raw_mutation"])
            self.assertEqual(
                before,
                {
                    path.relative_to(database).as_posix(): path.read_bytes()
                    for path in database.rglob("*")
                    if path.is_file()
                },
            )


if __name__ == "__main__":
    unittest.main()
