from __future__ import annotations

import copy
import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import generic_agent_read_adapter as read_adapter  # noqa: E402
from memory_atlas_cli.generic_agent_read_adapter import (  # noqa: E402
    ACCEPTANCE_ID,
    CONTRACT_PATH,
    ENTRYPOINT_PATH,
    MODEL_PATH,
    SCHEMA_VERSION,
    TASK_ID,
    AdapterLimits,
    GenericAgentReadError,
    generic_agent_export_guard,
    load_generic_agent_read_contract,
    read_generic_agent_export,
    validate_generic_agent_read_contract,
    verify_generic_agent_export_unchanged,
)
from memory_atlas_cli.source_registry import (  # noqa: E402
    REGISTRY_PATH,
    SourceRegistryError,
    load_source_registry,
    sync_source_map,
    validate_source_registry,
)


def write_sqlite(path: Path, rows: list[dict[str, object]]) -> None:
    connection = sqlite3.connect(path)
    try:
        connection.execute("CREATE TABLE events (record_json TEXT NOT NULL)")
        connection.executemany(
            "INSERT INTO events(record_json) VALUES (?)",
            [(json.dumps(row, sort_keys=True),) for row in rows],
        )
        connection.commit()
    finally:
        connection.close()


def file_state(path: Path) -> tuple[int, int, int, int, int, str]:
    metadata = path.stat()
    return (
        metadata.st_dev,
        metadata.st_ino,
        metadata.st_size,
        metadata.st_mtime_ns,
        metadata.st_ctime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


class GenericAgentReadAdapterTests(unittest.TestCase):
    def test_contract_model_and_registry_bind_the_t1_adapter(self) -> None:
        contract = load_generic_agent_read_contract(ROOT)

        self.assertEqual(contract["schema_version"], SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], TASK_ID)
        self.assertEqual(contract["acceptance_id"], ACCEPTANCE_ID)
        self.assertEqual(contract["entrypoint"], ENTRYPOINT_PATH.as_posix())
        self.assertEqual(contract["model_ref"], MODEL_PATH.as_posix())
        self.assertTrue((ROOT / CONTRACT_PATH).is_file())
        self.assertTrue((ROOT / ENTRYPOINT_PATH).is_file())
        self.assertTrue((ROOT / MODEL_PATH).is_file())
        self.assertEqual(contract["source_shapes"], ["file", "directory"])
        self.assertEqual(contract["formats"], ["json", "jsonl", "sqlite"])
        self.assertIs(contract["safety"]["source_read_only"], True)
        self.assertIs(contract["safety"]["source_content_in_cli_output"], False)
        self.assertIs(contract["phase_boundary"]["future_agent_fixture_implemented"], False)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S09-P2-T2")

        sources = sync_source_map(load_source_registry(ROOT))
        for source_id in ("generic_agent_template", "codex-reviewer"):
            parser = sources[source_id]["parser"]
            self.assertEqual(parser["read_adapter_entrypoint"], ENTRYPOINT_PATH.as_posix())
            self.assertEqual(parser["read_adapter_contract_ref"], CONTRACT_PATH.as_posix())
            self.assertEqual(parser["read_adapter_model_ref"], MODEL_PATH.as_posix())
        self.assertEqual(
            sources["generic_agent_template"]["parser"]["read_adapter_formats"],
            ["file", "directory", "json", "jsonl", "sqlite"],
        )

    def test_json_file_supports_object_list_and_events_container(self) -> None:
        payloads = (
            ({"event_id": "one", "title": "One", "messages": []}, ["one"]),
            (
                [
                    {"event_id": "one", "title": "One", "messages": []},
                    {"event_id": "two", "title": "Two", "messages": []},
                ],
                ["one", "two"],
            ),
            (
                {
                    "events": [
                        {"event_id": "one", "title": "One", "messages": []},
                        {"event_id": "two", "title": "Two", "messages": []},
                    ]
                },
                ["one", "two"],
            ),
        )
        for payload, expected_ids in payloads:
            with self.subTest(expected_ids=expected_ids), tempfile.TemporaryDirectory() as temp_dir:
                source = Path(temp_dir) / "events.json"
                source.write_text(json.dumps(payload), encoding="utf-8")

                result = read_generic_agent_export(ROOT, source)

                self.assertEqual([record.payload["event_id"] for record in result.records], expected_ids)
                self.assertEqual(result.source_kind, "file")
                self.assertEqual(result.format_counts, {"json": len(expected_ids)})
                summary = result.public_summary()
                self.assertEqual(summary["record_count"], len(expected_ids))
                self.assertNotIn(str(source), json.dumps(summary))
                self.assertNotIn("One", json.dumps(summary))
                self.assertIs(summary["writes_files"], False)

    def test_jsonl_file_is_strict_and_preserves_legacy_event_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "events.jsonl"
            source.write_text(
                "\n".join(
                    (
                        json.dumps({"event_id": "one", "title": "One", "messages": []}),
                        "",
                        json.dumps({"event_id": "two", "title": "Two", "messages": []}),
                    )
                )
                + "\n",
                encoding="utf-8",
            )

            result = read_generic_agent_export(ROOT, source)

            self.assertEqual([record.payload["event_id"] for record in result.records], ["one", "two"])
            self.assertEqual(result.format_counts, {"jsonl": 2})
            self.assertEqual([record.ordinal for record in result.records], [1, 2])

            source.write_text('{"event_id":"valid"}\n42\n', encoding="utf-8")
            with self.assertRaisesRegex(GenericAgentReadError, "jsonl_record_not_object"):
                read_generic_agent_export(ROOT, source)

    def test_directory_reads_supported_files_recursively_in_relative_path_order(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "export"
            (source / "nested").mkdir(parents=True)
            (source / "ignored.txt").write_text("not read", encoding="utf-8")
            (source / "z.jsonl").write_text(
                json.dumps({"event_id": "z", "title": "Z", "messages": []}) + "\n",
                encoding="utf-8",
            )
            (source / "nested/a.json").write_text(
                json.dumps({"event_id": "a", "title": "A", "messages": []}),
                encoding="utf-8",
            )
            write_sqlite(
                source / "nested/m.sqlite",
                [{"event_id": "m", "title": "M", "messages": []}],
            )

            result = read_generic_agent_export(ROOT, source)

            self.assertEqual([record.payload["event_id"] for record in result.records], ["a", "m", "z"])
            self.assertEqual(result.source_kind, "directory")
            self.assertEqual(result.source_file_count, 3)
            self.assertEqual(result.skipped_file_count, 1)
            self.assertEqual(result.format_counts, {"json": 1, "jsonl": 1, "sqlite": 1})
            self.assertEqual(result.public_summary()["source_formats"], ["json", "jsonl", "sqlite"])

    def test_sqlite_uses_self_contained_read_only_export_without_side_effects(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "agent.sqlite"
            rows = [
                {"event_id": "two", "title": "Two", "messages": []},
                {"event_id": "one", "title": "One", "messages": []},
            ]
            write_sqlite(source, rows)
            before = file_state(source)

            result = read_generic_agent_export(ROOT, source)

            self.assertEqual(file_state(source), before)
            self.assertFalse(Path(f"{source}-wal").exists())
            self.assertFalse(Path(f"{source}-shm").exists())
            self.assertFalse(Path(f"{source}-journal").exists())
            self.assertEqual(
                sorted(record.payload["event_id"] for record in result.records),
                ["one", "two"],
            )
            self.assertTrue(all(record.source_format == "sqlite" for record in result.records))
            summary = result.public_summary()
            self.assertEqual(summary["sqlite_open_mode"], "mode=ro&immutable=1")
            self.assertIs(summary["source_read_only"], True)
            self.assertIs(summary["network_access"], False)

    def test_sqlite_direct_columns_are_object_records_and_blobs_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "direct.db"
            connection = sqlite3.connect(source)
            try:
                connection.execute("CREATE TABLE events (event_id TEXT, title TEXT)")
                connection.execute("INSERT INTO events VALUES ('one', 'One')")
                connection.commit()
            finally:
                connection.close()

            result = read_generic_agent_export(ROOT, source)
            self.assertEqual(result.records[0].payload, {"event_id": "one", "title": "One"})

            blob_source = Path(temp_dir) / "blob.sqlite3"
            connection = sqlite3.connect(blob_source)
            try:
                connection.execute("CREATE TABLE events (payload BLOB)")
                connection.execute("INSERT INTO events VALUES (?)", (b"secret-binary",))
                connection.commit()
            finally:
                connection.close()
            with self.assertRaisesRegex(GenericAgentReadError, "sqlite_blob_unsupported"):
                read_generic_agent_export(ROOT, blob_source)

    def test_symlinks_special_files_and_sqlite_sidecars_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            target = root / "target.json"
            target.write_text('{"event_id":"one"}', encoding="utf-8")
            source_link = root / "source.json"
            source_link.symlink_to(target)
            with self.assertRaisesRegex(GenericAgentReadError, "source_symlink_rejected"):
                read_generic_agent_export(ROOT, source_link)

            directory = root / "export"
            directory.mkdir()
            (directory / "events.json").write_text('{"event_id":"one"}', encoding="utf-8")
            (directory / "linked.json").symlink_to(target)
            with self.assertRaisesRegex(GenericAgentReadError, "tree_symlink_rejected"):
                read_generic_agent_export(ROOT, directory)

            sqlite_path = root / "events.sqlite"
            write_sqlite(sqlite_path, [{"event_id": "one"}])
            Path(f"{sqlite_path}-wal").write_bytes(b"not-a-self-contained-export")
            with self.assertRaisesRegex(GenericAgentReadError, "sqlite_sidecar_present"):
                read_generic_agent_export(ROOT, sqlite_path)

    def test_unsupported_explicit_file_and_empty_directory_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            unsupported = root / "events.csv"
            unsupported.write_text("event_id\none\n", encoding="utf-8")
            with self.assertRaisesRegex(GenericAgentReadError, "source_format_unsupported"):
                read_generic_agent_export(ROOT, unsupported)

            empty = root / "empty"
            empty.mkdir()
            (empty / "notes.txt").write_text("ignored", encoding="utf-8")
            with self.assertRaisesRegex(GenericAgentReadError, "supported_source_file_missing"):
                read_generic_agent_export(ROOT, empty)

    def test_limits_and_source_mutation_fail_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "events.json"
            source.write_text(
                json.dumps(
                    [
                        {"event_id": "one", "messages": []},
                        {"event_id": "two", "messages": []},
                    ]
                ),
                encoding="utf-8",
            )
            limits = AdapterLimits(
                max_tree_entries=8,
                max_source_files=2,
                max_file_bytes=1024,
                max_total_bytes=2048,
                max_records=1,
                max_sqlite_tables=2,
                max_sqlite_columns=8,
                max_scalar_utf8_bytes=256,
            )
            with self.assertRaisesRegex(GenericAgentReadError, "record_limit_exceeded"):
                read_generic_agent_export(ROOT, source, limits=limits)

            result = read_generic_agent_export(ROOT, source)
            source.write_text('{"event_id":"changed"}', encoding="utf-8")
            with self.assertRaisesRegex(GenericAgentReadError, "source_snapshot_changed"):
                verify_generic_agent_export_unchanged(result)
            with self.assertRaisesRegex(GenericAgentReadError, "source_snapshot_changed"):
                with generic_agent_export_guard(result):
                    pass

    def test_registry_rejects_generic_read_adapter_drift(self) -> None:
        payload = json.loads((ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))
        mutations = (
            ("read_adapter_entrypoint", "scripts/sync_future_agent_data.py"),
            ("read_adapter_contract_ref", "config/data_sources/source_registry.json"),
            ("read_adapter_model_ref", "config/data_sources/source_registry.json"),
            ("read_adapter_formats", ["json"]),
        )
        for field, value in mutations:
            with self.subTest(field=field):
                drifted = copy.deepcopy(payload)
                drifted["sync_sources"][2]["parser"][field] = value
                with self.assertRaises(SourceRegistryError):
                    validate_source_registry(drifted, ROOT)

    def test_contract_rejects_weakened_read_only_or_phase_boundary(self) -> None:
        canonical = json.loads((ROOT / CONTRACT_PATH).read_text(encoding="utf-8"))
        mutations = (
            lambda value: value["safety"].update({"source_read_only": False}),
            lambda value: value["sqlite"].update({"open_mode": "mode=rw"}),
            lambda value: value["directory"].update({"follow_symlinks": True}),
            lambda value: value["phase_boundary"].update({"future_agent_fixture_implemented": True}),
        )
        for mutate in mutations:
            drifted = copy.deepcopy(canonical)
            mutate(drifted)
            with self.assertRaises(GenericAgentReadError):
                validate_generic_agent_read_contract(drifted)

    def test_atlasctl_dry_run_accepts_directory_and_sqlite_without_content_echo_or_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "export"
            source.mkdir()
            (source / "events.jsonl").write_text(
                json.dumps(
                    {
                        "event_id": "one",
                        "title": "PRIVATE_TITLE_SENTINEL",
                        "messages": [{"role": "assistant", "text": "PRIVATE_BODY_SENTINEL"}],
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            write_sqlite(
                source / "events.sqlite",
                [{"event_id": "two", "title": "SQLITE_PRIVATE_SENTINEL", "messages": []}],
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/atlasctl.py"),
                    "sync",
                    "--source",
                    "future-agent",
                    "--agent-id",
                    "generic-reader-test",
                    "--input",
                    str(source),
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
        self.assertEqual(payload["source_kind"], "directory")
        self.assertEqual(payload["source_file_count"], 2)
        self.assertEqual(payload["event_count"], 2)
        self.assertEqual(payload["adapter_contract"], CONTRACT_PATH.as_posix())
        self.assertIs(payload["source_read_only"], True)
        self.assertIs(payload["writes_files"], False)
        self.assertNotIn("PRIVATE_TITLE_SENTINEL", result.stdout)
        self.assertNotIn("PRIVATE_BODY_SENTINEL", result.stdout)
        self.assertNotIn("SQLITE_PRIVATE_SENTINEL", result.stdout)
        self.assertNotIn(str(source), result.stdout)

    def test_source_mutation_during_read_is_detected_before_return(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "events.json"
            source.write_text('{"event_id":"one"}', encoding="utf-8")
            original_read_bytes = read_adapter._read_regular_bytes

            def mutate_after_read(path: Path, max_bytes: int) -> tuple[bytes, str]:
                content = original_read_bytes(path, max_bytes)
                if path == source.resolve():
                    path.write_text('{"event_id":"changed"}', encoding="utf-8")
                return content

            with mock.patch.object(read_adapter, "_read_regular_bytes", mutate_after_read):
                with self.assertRaisesRegex(GenericAgentReadError, "source_snapshot_changed"):
                    read_generic_agent_export(ROOT, source)

    def test_apply_rejects_database_output_inside_source_directory_before_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "export"
            database = source / "database"
            database.mkdir(parents=True)
            (source / "events.json").write_text(
                '{"event_id":"one","title":"One","messages":[]}',
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/sync_future_agent_data.py"),
                    "--database-dir",
                    str(database),
                    "--agent-id",
                    "overlap-test",
                    "--input",
                    str(source),
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )

            self.assertEqual(result.returncode, 2, result.stderr)
            payload = json.loads(result.stdout)
            self.assertEqual(payload["status"], "FAIL_CLOSED")
            self.assertEqual(payload["reason"], "source_input_invalid")
            self.assertEqual(payload["error"], "source_directory_contains_database_output")
            self.assertFalse((database / "data").exists())


if __name__ == "__main__":
    unittest.main()
