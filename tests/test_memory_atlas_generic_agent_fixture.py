from __future__ import annotations

import base64
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.archive_restore import ArchiveRestoreError, verify_archive  # noqa: E402
from memory_atlas_cli.generic_agent_fixture import (  # noqa: E402
    ACCEPTANCE_ID,
    ARCHIVE_ID,
    CONTRACT_PATH,
    ENTRYPOINT_PATH,
    EXAMPLE_SOURCE_ID,
    FIXTURE_INPUT_PATH,
    MODEL_PATH,
    RESULT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    TASK_ID,
    FixtureAcceptanceError,
    load_generic_agent_fixture_contract,
    run_generic_agent_fixture,
    validate_fixture_source,
    validate_generic_agent_fixture_contract,
)
from memory_atlas_cli.source_registry import (  # noqa: E402
    PUSH_DEFAULTS,
    load_source_registry,
    sync_source_map,
    validate_source_registry,
)


def file_fingerprint(path: Path) -> tuple[int, int, str]:
    metadata = path.stat()
    return (
        metadata.st_size,
        metadata.st_mtime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def result_json(result: dict[str, object]) -> str:
    return json.dumps(result, ensure_ascii=False, sort_keys=True)


class GenericAgentFixtureTests(unittest.TestCase):
    def test_contract_registry_and_fixture_bind_one_reusable_standard_source(self) -> None:
        contract = load_generic_agent_fixture_contract(ROOT)
        registry = load_source_registry(ROOT)
        sources = sync_source_map(registry)
        source = validate_fixture_source(registry, contract)

        self.assertEqual(contract["schema_version"], SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], TASK_ID)
        self.assertEqual(contract["acceptance_id"], ACCEPTANCE_ID)
        self.assertEqual(contract["entrypoint"], ENTRYPOINT_PATH.as_posix())
        self.assertEqual(contract["model_ref"], MODEL_PATH.as_posix())
        self.assertEqual(contract["fixture_input"], FIXTURE_INPUT_PATH.as_posix())
        self.assertEqual(contract["example_source_id"], EXAMPLE_SOURCE_ID)
        self.assertEqual(source, sources[EXAMPLE_SOURCE_ID])
        self.assertEqual(source["source_type"], "generic_agent")
        self.assertEqual(source["status"], "fixture")
        self.assertEqual(source["push_policy"], PUSH_DEFAULTS)
        self.assertEqual(
            source["archive_path"],
            f"data/public_raw/agents/{EXAMPLE_SOURCE_ID}",
        )
        self.assertEqual(
            source["derived_outputs"],
            [f"data/derived/agents/{EXAMPLE_SOURCE_ID}/agent_sync_summary.json"],
        )
        self.assertTrue((ROOT / CONTRACT_PATH).is_file())
        self.assertTrue((ROOT / MODEL_PATH).is_file())
        self.assertTrue((ROOT / ENTRYPOINT_PATH).is_file())
        self.assertTrue((ROOT / FIXTURE_INPUT_PATH).is_file())
        self.assertEqual(
            hashlib.sha256((ROOT / FIXTURE_INPUT_PATH).read_bytes()).hexdigest(),
            contract["fixture"]["input_sha256"],
        )

        for runtime_path in (
            ROOT / "scripts/sync_future_agent_data.py",
            ROOT / "scripts/memory_atlas_cli/source_registry.py",
            ROOT / "scripts/memory_atlas_cli/sync.py",
        ):
            self.assertNotIn(EXAMPLE_SOURCE_ID, runtime_path.read_text(encoding="utf-8"))

    def test_same_template_accepts_a_second_config_only_source(self) -> None:
        payload = load_source_registry(ROOT)
        example = copy.deepcopy(sync_source_map(payload)[EXAMPLE_SOURCE_ID])
        second_id = "second-standard-agent"
        example.update(
            {
                "source_id": second_id,
                "label": "Second standard Agent",
                "status": "configured",
                "state_path": f"data/sync_state/agents/{second_id}.json",
                "archive_path": f"data/public_raw/agents/{second_id}",
                "derived_outputs": [
                    f"data/derived/agents/{second_id}/agent_sync_summary.json"
                ],
            }
        )
        example["discovery"]["candidates"] = [
            {
                "kind": "environment_variable",
                "value": "MEMORY_ATLAS_SECOND_STANDARD_AGENT_INPUT",
                "target_argument": "--input",
            },
            {"kind": "operator_argument", "value": "--input"},
        ]
        payload["sync_sources"].append(example)

        validated = validate_source_registry(payload, ROOT)

        self.assertIn(second_id, sync_source_map(validated))
        self.assertEqual(
            sync_source_map(validated)[second_id]["parser"],
            sync_source_map(validated)[EXAMPLE_SOURCE_ID]["parser"],
        )

    def test_fixture_covers_raw_manifest_parser_derived_archive_restore_and_push_contract(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            result = run_generic_agent_fixture(ROOT, workspace)
            database = workspace / "database"
            package = workspace / "fixture-recovery-bundle.json"
            restored = workspace / "restored-fixture-recovery-bundle.json"

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["schema_version"], RESULT_SCHEMA_VERSION)
            self.assertEqual(result["task_id"], TASK_ID)
            self.assertEqual(result["acceptance_id"], ACCEPTANCE_ID)
            self.assertEqual(result["source_id"], EXAMPLE_SOURCE_ID)
            self.assertEqual(result["parser"]["adapter_source_formats"], ["jsonl"])
            self.assertEqual(result["parser"]["event_count"], 2)
            self.assertEqual(result["parser"]["message_count"], 3)
            self.assertEqual(result["raw"]["file_count"], 2)
            self.assertEqual(result["raw"]["ledger_status"], "PASS")
            self.assertEqual(result["raw"]["ledger_appended_count"], 2)
            self.assertEqual(
                result["manifest"]["source_families"],
                [f"agent:{EXAMPLE_SOURCE_ID}"],
            )
            self.assertEqual(result["derived"]["file_count"], 1)
            self.assertEqual(result["archive"]["chunk_status"], "PASS")
            self.assertEqual(result["archive"]["verify_status"], "PASS")
            self.assertEqual(result["archive"]["restore_status"], "PASS")
            self.assertEqual(result["archive"]["part_count"], 1)
            self.assertEqual(result["archive"]["bundle_sha256"], result["archive"]["restored_sha256"])
            self.assertEqual(result["main_push_contract"], PUSH_DEFAULTS)
            self.assertIs(result["push_executed"], False)
            self.assertIs(result["remote_push"], False)
            self.assertIs(result["plugin_contract_implemented"], False)
            self.assertIs(result["production_database_mutation"], False)

            raw_files = sorted(
                (database / f"data/public_raw/agents/{EXAMPLE_SOURCE_ID}").glob("*.json")
            )
            self.assertEqual(len(raw_files), 2)
            derived = (
                database
                / f"data/derived/agents/{EXAMPLE_SOURCE_ID}/agent_sync_summary.json"
            )
            self.assertTrue(derived.is_file())
            self.assertEqual(json.loads(derived.read_text(encoding="utf-8"))["event_count"], 2)
            self.assertTrue(
                (
                    database
                    / "机器治理/证据与日志/raw_archive_manifests"
                    / "raw_manifest.s09-p2-t2-fixture.jsonl"
                ).is_file()
            )
            archive = database / f"data/raw_archives/{EXAMPLE_SOURCE_ID}/{ARCHIVE_ID}"
            self.assertTrue((archive / "manifest.json").is_file())
            self.assertTrue(package.is_file())
            self.assertTrue(restored.is_file())
            self.assertEqual(package.read_bytes(), restored.read_bytes())

            bundle = json.loads(restored.read_text(encoding="utf-8"))
            self.assertEqual(bundle["source_id"], EXAMPLE_SOURCE_ID)
            self.assertEqual(len(bundle["files"]), 5)
            for item in bundle["files"]:
                decoded = base64.b64decode(item["payload_base64"], validate=True)
                self.assertEqual(len(decoded), item["byte_size"])
                self.assertEqual(hashlib.sha256(decoded).hexdigest(), item["sha256"])
                self.assertEqual(
                    decoded,
                    (database / item["relative_path"]).read_bytes(),
                )

            serialized = result_json(result)
            self.assertNotIn(str(workspace), serialized)
            self.assertNotIn("Fixture planning review", serialized)
            self.assertNotIn("No production write is allowed", serialized)

    def test_replay_keeps_raw_manifest_archive_and_restore_bytes_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            first = run_generic_agent_fixture(ROOT, workspace)
            database = workspace / "database"
            tracked_paths = sorted(
                (database / f"data/public_raw/agents/{EXAMPLE_SOURCE_ID}").glob("*.json")
            ) + [
                database / "机器治理/证据与日志/raw_archive_manifests/raw_manifest.s09-p2-t2-fixture.jsonl",
                database
                / "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl",
                database / f"data/raw_archives/{EXAMPLE_SOURCE_ID}/{ARCHIVE_ID}/manifest.json",
                workspace / "fixture-recovery-bundle.json",
                workspace / "restored-fixture-recovery-bundle.json",
            ]
            before = {path: file_fingerprint(path) for path in tracked_paths}

            second = run_generic_agent_fixture(ROOT, workspace)

            self.assertEqual(first["archive"]["bundle_sha256"], second["archive"]["bundle_sha256"])
            self.assertEqual(second["raw"]["ledger_appended_count"], 0)
            self.assertIs(second["raw"]["ledger_idempotent"], True)
            self.assertIs(second["manifest"]["idempotent"], True)
            self.assertIs(second["archive"]["chunk_idempotent"], True)
            self.assertIs(second["archive"]["restore_idempotent"], True)
            self.assertEqual(
                {path: file_fingerprint(path) for path in tracked_paths},
                before,
            )

    def test_archive_tamper_fails_closed_without_replacing_restore(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            run_generic_agent_fixture(ROOT, workspace)
            database = workspace / "database"
            archive = database / f"data/raw_archives/{EXAMPLE_SOURCE_ID}/{ARCHIVE_ID}"
            part = next((archive / "parts").glob("*.part-*"))
            restored = workspace / "restored-fixture-recovery-bundle.json"
            restored_before = file_fingerprint(restored)
            part.write_bytes(part.read_bytes() + b"tamper")

            with self.assertRaises(ArchiveRestoreError):
                verify_archive(database, EXAMPLE_SOURCE_ID, ARCHIVE_ID)

            self.assertEqual(file_fingerprint(restored), restored_before)

    def test_workspace_must_be_empty_and_outside_the_package_root(self) -> None:
        with self.assertRaises(FixtureAcceptanceError):
            run_generic_agent_fixture(ROOT, ROOT)
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            (workspace / "unrelated.txt").write_text("keep", encoding="utf-8")
            with self.assertRaises(FixtureAcceptanceError):
                run_generic_agent_fixture(ROOT, workspace)
            self.assertEqual(
                (workspace / "unrelated.txt").read_text(encoding="utf-8"),
                "keep",
            )

    def test_owned_replay_rejects_internal_symlink_before_external_write(self) -> None:
        with (
            tempfile.TemporaryDirectory() as temp_dir,
            tempfile.TemporaryDirectory() as external_dir,
        ):
            workspace = Path(temp_dir)
            external = Path(external_dir)
            sentinel = external / "sentinel.txt"
            sentinel.write_text("unchanged", encoding="utf-8")
            run_generic_agent_fixture(ROOT, workspace)
            (workspace / "database/unsafe-link").symlink_to(external, target_is_directory=True)

            with self.assertRaises(FixtureAcceptanceError):
                run_generic_agent_fixture(ROOT, workspace)

            self.assertEqual(sentinel.read_text(encoding="utf-8"), "unchanged")

    def test_cli_runs_ephemerally_and_prints_no_local_path_or_fixture_content(self) -> None:
        result = subprocess.run(
            [sys.executable, str(ROOT / ENTRYPOINT_PATH), "--database-dir", str(ROOT)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["source_id"], EXAMPLE_SOURCE_ID)
        self.assertIs(payload["workspace_persisted"], False)
        self.assertIs(payload["production_database_mutation"], False)
        self.assertNotIn(str(ROOT), result.stdout)
        self.assertNotIn("Fixture planning review", result.stdout)
        self.assertNotIn("No production write is allowed", result.stdout)

    def test_registry_routes_example_but_direct_main_push_fails_before_git_effects(self) -> None:
        dry_run = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                EXAMPLE_SOURCE_ID,
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(dry_run.returncode, 0, dry_run.stderr)
        dry_payload = json.loads(dry_run.stdout)
        self.assertEqual(dry_payload["source_id"], EXAMPLE_SOURCE_ID)
        self.assertEqual(dry_payload["agent_id"], EXAMPLE_SOURCE_ID)
        self.assertIs(dry_payload["writes_files"], False)

        push = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                EXAMPLE_SOURCE_ID,
                "--push-main",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(push.returncode, 2, push.stderr)
        push_payload = json.loads(push.stdout)
        self.assertEqual(push_payload["status"], "FAIL_CLOSED")
        self.assertEqual(
            push_payload["reason"],
            "push_main_requires_canonical_codex_source",
        )
        self.assertEqual(push_payload["push_attempt_count"], 0)
        self.assertIs(push_payload["remote_push_attempted"], False)
        self.assertIs(push_payload["fetch_executed"], False)
        self.assertIs(push_payload["commit_created"], False)
        self.assertIs(push_payload["writes_files"], False)

    def test_fixture_source_apply_is_rejected_before_production_raw_write(self) -> None:
        production_root = (
            ROOT / f"data/public_raw/agents/{EXAMPLE_SOURCE_ID}"
        )
        before = (
            {
                path.relative_to(production_root).as_posix(): file_fingerprint(path)
                for path in production_root.rglob("*")
                if path.is_file()
            }
            if production_root.exists()
            else None
        )
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                EXAMPLE_SOURCE_ID,
                "--input",
                str(ROOT / FIXTURE_INPUT_PATH),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertIn("fixture source is acceptance-only", payload["reason"])
        self.assertIs(payload["writes_files"], False)
        self.assertIs(payload["production_database_mutation"], False)
        self.assertIs(payload["remote_push_attempted"], False)
        after = (
            {
                path.relative_to(production_root).as_posix(): file_fingerprint(path)
                for path in production_root.rglob("*")
                if path.is_file()
            }
            if production_root.exists()
            else None
        )
        self.assertEqual(after, before)

    def test_contract_drift_and_noncanonical_push_policy_fail_closed(self) -> None:
        contract = load_generic_agent_fixture_contract(ROOT)
        for mutate in (
            lambda value: value["pipeline"].__setitem__("parser_entrypoint", "scripts/other.py"),
            lambda value: value["main_push_contract"].__setitem__("force", True),
            lambda value: value["safety"].__setitem__("isolated_workspace_required", False),
            lambda value: value["phase_boundary"].__setitem__("plugin_contract_implemented", True),
        ):
            with self.subTest(mutate=mutate):
                drifted = copy.deepcopy(contract)
                mutate(drifted)
                with self.assertRaises(FixtureAcceptanceError):
                    validate_generic_agent_fixture_contract(drifted)

        registry = load_source_registry(ROOT)
        drifted_registry = copy.deepcopy(registry)
        source = sync_source_map(drifted_registry)[EXAMPLE_SOURCE_ID]
        source["push_policy"]["force"] = True
        with self.assertRaises(FixtureAcceptanceError):
            validate_fixture_source(drifted_registry, contract)


if __name__ == "__main__":
    unittest.main()
