from __future__ import annotations

import hashlib
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.codex_atlas import (  # noqa: E402
    CONTRACT_PATH,
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    EXPECTED_PHASE_BOUNDARY,
    MODEL_PARAMETERS_PATH,
    STATE_PATH,
    CodexAtlasError,
    load_codex_atlas_contract,
    publish_codex_atlas,
)
from memory_atlas_cli import codex_atlas  # noqa: E402
from memory_atlas_cli.codex_derived import (  # noqa: E402
    CONTRACT_PATH as DERIVED_CONTRACT_PATH,
    EXPECTED_OUTPUTS as DERIVED_OUTPUTS,
    EXPECTED_PHASE_BOUNDARY as DERIVED_PHASE_BOUNDARY,
    MODEL_PARAMETERS_PATH as DERIVED_MODEL_PARAMETERS_PATH,
    STATE_SCHEMA_VERSION as DERIVED_STATE_SCHEMA_VERSION,
)


def json_bytes(value: object) -> bytes:
    return (json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()


def jsonl_bytes(rows: list[dict[str, object]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
        for row in rows
    ).encode()


def write_bytes(root: Path, relative: str, payload: bytes) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def event(
    session_id: str,
    event_id: str,
    thread_name: str,
    updated_at: str,
) -> dict[str, object]:
    day = updated_at[:10]
    return {
        "schema_version": "memory_atlas.codex_derived_event.v1_2_1_s07_p2_t1",
        "source_id": "codex",
        "source": "codex",
        "event_id": event_id,
        "record_id": session_id,
        "session_id": session_id,
        "source_relative_path": f"sessions/{day}/{session_id}.jsonl",
        "thread_name": thread_name,
        "started_at": updated_at,
        "updated_at": updated_at,
        "day": day,
        "updated_day": day,
        "message_count": 12,
        "user_message_count": 3,
        "assistant_message_count": 9,
        "tool_call_count": 18,
        "error_event_count": 0,
        "abort_count": 0,
        "activity_score": 120,
        "topics": [{"id": "codex_local", "label": "Codex 本地数据 / agent 工作流", "count": 2}],
        "preference_signals": [{"id": "real_data_required", "label": "偏好真实数据和可验证证据", "count": 1}],
        "top_tools": [{"name": "exec_command", "count": 18}],
    }


def facet(event_id: str, session_id: str) -> dict[str, object]:
    return {
        "schema_version": "memory_atlas.codex_derived_facet.v1_2_1_s07_p2_t1",
        "source_id": "codex",
        "source": "codex",
        "event_id": event_id,
        "record_id": session_id,
        "occurred_at": "2026-07-15T02:00:00Z",
        "evidence_refs": [
            {
                "ref_type": "archive_manifest",
                "source_id": "codex",
                "evidence_level": "verified_recoverable_sanitized_raw_archive",
                "path": "data/raw_archives/codex/test/manifest.json",
                "sha256": "a" * 64,
            }
        ],
    }


def make_fixture(parent: Path) -> tuple[Path, list[str]]:
    database = parent / "OpenAIDatabase"
    database.mkdir()
    for source, relative in (
        (ROOT / DERIVED_CONTRACT_PATH, DERIVED_CONTRACT_PATH),
        (ROOT / DERIVED_MODEL_PARAMETERS_PATH, DERIVED_MODEL_PARAMETERS_PATH),
        (ROOT / CONTRACT_PATH, CONTRACT_PATH),
        (ROOT / MODEL_PARAMETERS_PATH, MODEL_PARAMETERS_PATH),
    ):
        target = database / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)

    events = [
        event("session-old", "codex_session_old", "旧 Codex 会话", "2026-07-14T01:00:00Z"),
        event("session-latest", "codex_session_latest", "最新 Memory Atlas 会话", "2026-07-15T02:00:00Z"),
    ]
    facets = [facet("codex_session_old", "session-old"), facet("codex_session_latest", "session-latest")]
    behavior = {
        "schema_version": "memory_atlas.codex_behavior_summary.v1_2_1_s07_p2_t1",
        "task_id": "S07-P2-T1",
        "source_id": "codex",
        "session_count": 2,
        "facet_count": 2,
        "archive_count": 1,
        "message_count": 24,
        "tool_call_count": 36,
        "source_truth": {
            "kind": "derived_from_verified_recoverable_sanitized_raw_archives",
            "full_raw_backup": False,
            "recoverable_sanitized_raw_available": True,
        },
    }
    universe = {
        "schema_version": "memory_atlas_universe_state_fixture.v1",
        "source_scope": "codex",
        "source_safety": {"raw_private_data_included": False},
    }
    payloads = {
        DERIVED_OUTPUTS["events"]: jsonl_bytes(events),
        DERIVED_OUTPUTS["facets"]: jsonl_bytes(facets),
        DERIVED_OUTPUTS["behavior_summary"]: json_bytes(behavior),
        DERIVED_OUTPUTS["universe_state_input"]: json_bytes(universe),
    }
    for relative, payload in payloads.items():
        write_bytes(database, relative, payload)

    derived_contract = json.loads((database / DERIVED_CONTRACT_PATH).read_text())
    derived_model = json.loads((database / DERIVED_MODEL_PARAMETERS_PATH).read_text())
    derived_state = {
        "schema_version": DERIVED_STATE_SCHEMA_VERSION,
        "task_id": "S07-P2-T1",
        "acceptance_id": "ACC-MA-V121-S07-P2-T1",
        "source_id": "codex",
        "contract_ref": DERIVED_CONTRACT_PATH.as_posix(),
        "contract_sha256": hashlib.sha256(json_bytes(derived_contract)).hexdigest(),
        "model_parameters_ref": DERIVED_MODEL_PARAMETERS_PATH.as_posix(),
        "model_parameters_sha256": hashlib.sha256(json_bytes(derived_model)).hexdigest(),
        "generated_at": "2026-07-15T02:05:00Z",
        "input_archives": [{"archive_id": "fixture", "archive_manifest_sha256": "b" * 64}],
        "event_count": 2,
        "facet_count": 2,
        "output_hashes": {
            relative: {"sha256": hashlib.sha256(payload).hexdigest(), "byte_size": len(payload)}
            for relative, payload in payloads.items()
        },
        "last_result": {"outcome": "BUILT_FROM_IMMUTABLE_RAW", "parsed_archive_count": 1},
        "phase_boundary": DERIVED_PHASE_BOUNDARY,
    }
    write_bytes(database, DERIVED_OUTPUTS["state"], json_bytes(derived_state))

    guarded = [
        "data/raw_archives/codex/fixture/manifest.json",
        "data/public_raw/codex/fixture.json",
        "data/sync_state/codex.json",
        "data/processed/codex/codex_session_manifest.jsonl",
        "data/processed/codex/codex_daily_activity.jsonl",
        "data/processed/codex/codex_activity_snapshot.json",
        "data/derived/codex/codex_activity_snapshot.json",
        "data/derived/codex/codex_agent_recommendations.json",
        "data/derived/codex/codex_behavior_report.md",
    ]
    for relative in guarded:
        write_bytes(database, relative, f"guard:{relative}\n".encode())
    return database, guarded


def evidence(database: Path, paths: list[str]) -> dict[str, str]:
    return {relative: hashlib.sha256((database / relative).read_bytes()).hexdigest() for relative in paths}


class CodexAtlasPublicationTests(unittest.TestCase):
    def test_contract_and_model_freeze_t2_scope(self) -> None:
        contract = load_codex_atlas_contract(ROOT)
        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(contract["phase_boundary"], EXPECTED_PHASE_BOUNDARY)
        self.assertEqual(contract["publication"]["session_identity"], "event_id")
        self.assertEqual(json.loads((ROOT / MODEL_PARAMETERS_PATH).read_text()), EXPECTED_MODEL_PARAMETERS)

    def test_publishes_snapshot_weekly_report_and_sync_state(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, guarded = make_fixture(Path(temp_dir))
            before = evidence(database, guarded)
            result = publish_codex_atlas(
                database,
                published_at="2026-07-16T06:00:00Z",
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["event_count"], 2)
            self.assertEqual(len(result["changed_paths"]), 3)
            self.assertEqual(before, evidence(database, guarded))

            snapshot = json.loads((database / "data/derived/visualization/memory_atlas.json").read_text())
            publication = snapshot["codex_publication"]
            self.assertEqual(publication["status"], "CURRENT_LOCAL")
            self.assertEqual(publication["counts"]["atlas_codex_node_count"], 2)
            latest = publication["latest_session"]
            self.assertEqual(latest["thread_name"], "最新 Memory Atlas 会话")
            node = next(item for item in snapshot["nodes"] if item["id"] == latest["node_id"])
            self.assertIn("最新 Memory Atlas 会话", f"{node['label']} {node['statement']}")
            self.assertEqual(node["source_record_id"], "session-latest")
            self.assertTrue(node["evidence_refs"])

            state = json.loads((database / STATE_PATH).read_text())
            weekly_path = database / state["outputs"]["weekly_report"]["path"]
            weekly = weekly_path.read_text()
            self.assertIn("Codex 同步状态", weekly)
            self.assertIn("最新 Memory Atlas 会话", weekly)
            self.assertEqual(state["phase_boundary"]["next_task"], "S07-P2-T3")

    def test_exact_repeat_is_no_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            first = publish_codex_atlas(database, published_at="2026-07-16T06:00:00Z")
            paths = [database / relative for relative in first["changed_paths"]]
            before = [(path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
            second = publish_codex_atlas(database, published_at="2026-07-17T06:00:00Z")
            after = [(path.stat().st_mtime_ns, hashlib.sha256(path.read_bytes()).hexdigest()) for path in paths]
            self.assertEqual(second["outcome"], "NO_CHANGES")
            self.assertFalse(second["writes_files"])
            self.assertEqual(before, after)

    def test_tampered_publication_state_is_rebuilt(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            publish_codex_atlas(database, published_at="2026-07-16T06:00:00Z")
            state_path = database / STATE_PATH
            state = json.loads(state_path.read_text())
            state["latest_session"]["thread_name"] = "伪造同步状态"
            state_path.write_bytes(json_bytes(state))

            result = publish_codex_atlas(
                database,
                published_at="2026-07-16T06:00:00Z",
            )

            self.assertEqual(result["outcome"], "PUBLISHED_CANONICAL_CODEX_ATLAS")
            self.assertEqual(result["changed_paths"], [STATE_PATH.as_posix()])
            repaired = json.loads(state_path.read_text())
            self.assertEqual(repaired["latest_session"]["thread_name"], "最新 Memory Atlas 会话")

    def test_fsync_failure_rolls_back_replaced_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            calls = 0

            def fail_once(_path: Path) -> None:
                nonlocal calls
                calls += 1
                if calls == 1:
                    raise OSError("synthetic fsync failure")

            with mock.patch.object(codex_atlas, "_fsync_directory", side_effect=fail_once):
                with self.assertRaisesRegex(OSError, "synthetic fsync failure"):
                    publish_codex_atlas(
                        database,
                        published_at="2026-07-16T06:00:00Z",
                    )

            self.assertFalse((database / STATE_PATH).exists())
            self.assertFalse((database / "data/derived/visualization/memory_atlas.json").exists())
            self.assertEqual(list((database / "data/derived/weekly").glob("*.md")), [])

    def test_dry_run_reports_outputs_without_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, guarded = make_fixture(Path(temp_dir))
            before = evidence(database, guarded)
            result = publish_codex_atlas(database, dry_run=True, published_at="2026-07-16T06:00:00Z")
            self.assertEqual(result["outcome"], "WOULD_PUBLISH_CANONICAL_CODEX_ATLAS")
            self.assertTrue(result["would_write_files"])
            self.assertFalse((database / STATE_PATH).exists())
            self.assertEqual(before, evidence(database, guarded))

    def test_derived_hash_drift_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            with (database / DERIVED_OUTPUTS["events"]).open("ab") as handle:
                handle.write(b"\n")
            with self.assertRaisesRegex(CodexAtlasError, "codex_atlas_derived_output_hash_mismatch"):
                publish_codex_atlas(database, dry_run=True)
            self.assertFalse((database / STATE_PATH).exists())

    def test_event_without_matching_facet_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            facet_path = database / DERIVED_OUTPUTS["facets"]
            rows = [json.loads(line) for line in facet_path.read_text().splitlines() if line]
            replacement = jsonl_bytes(rows[:1])
            facet_path.write_bytes(replacement)
            state_path = database / DERIVED_OUTPUTS["state"]
            state = json.loads(state_path.read_text())
            state["facet_count"] = 1
            state["output_hashes"][DERIVED_OUTPUTS["facets"]] = {
                "sha256": hashlib.sha256(replacement).hexdigest(),
                "byte_size": len(replacement),
            }
            behavior_path = database / DERIVED_OUTPUTS["behavior_summary"]
            behavior = json.loads(behavior_path.read_text())
            behavior["facet_count"] = 1
            behavior_payload = json_bytes(behavior)
            behavior_path.write_bytes(behavior_payload)
            state["output_hashes"][DERIVED_OUTPUTS["behavior_summary"]] = {
                "sha256": hashlib.sha256(behavior_payload).hexdigest(),
                "byte_size": len(behavior_payload),
            }
            state_path.write_bytes(json_bytes(state))
            with self.assertRaisesRegex(CodexAtlasError, "codex_atlas_event_facet_identity_mismatch"):
                publish_codex_atlas(database, dry_run=True)

    def test_unsafe_sync_state_symlink_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            database, _guarded = make_fixture(Path(temp_dir))
            target = database / "outside.json"
            target.write_text("{}\n")
            state_path = database / STATE_PATH
            state_path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, state_path)
            with self.assertRaises(CodexAtlasError):
                publish_codex_atlas(database, dry_run=True)
            self.assertEqual(target.read_text(), "{}\n")


if __name__ == "__main__":
    unittest.main()
