from __future__ import annotations

import copy
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.generic_agent_plugin import (  # noqa: E402
    ACCEPTANCE_ID,
    CONTRACT_PATH,
    ENTRYPOINT_PATH,
    ENVELOPE_SCHEMA_VERSION,
    MODEL_PATH,
    RESULT_SCHEMA_VERSION,
    SCHEMA_VERSION,
    TASK_ID,
    GenericAgentPluginError,
    load_generic_agent_plugin_contract,
    run_generic_agent_plugin,
    validate_generic_agent_plugin_contract,
    validate_plugin_source,
)
from memory_atlas_cli.source_registry import (  # noqa: E402
    PUSH_DEFAULTS,
    load_source_registry,
    sync_source_map,
    validate_source_registry,
)


SOURCE_ID = "nonstandard-agent-example"
PLUGIN_ID = "nonstandard-envelope-example"
FIXTURE_PATH = Path(
    "tests/fixtures/memory_atlas/generic_agent_plugin/example.plugin-envelope.json"
)
RAW_LEDGER_CONTRACT = Path("config/data_sources/raw_ledger.json")
FIXED_TIME = "2026-07-17T04:30:00Z"


def canonical_hash(value: object) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def fixture_payload() -> dict[str, object]:
    return json.loads((ROOT / FIXTURE_PATH).read_text(encoding="utf-8"))


def rewrite_event_digest(payload: dict[str, object]) -> None:
    events = payload["canonical_events"]
    assert isinstance(events, list)
    payload["event_count"] = len(events)
    payload["events_sha256"] = canonical_hash(events)


def write_envelope(path: Path, payload: dict[str, object]) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def install_temp_database(root: Path) -> Path:
    database = root / "database"
    target = database / RAW_LEDGER_CONTRACT
    target.parent.mkdir(parents=True)
    shutil.copy2(ROOT / RAW_LEDGER_CONTRACT, target)
    return database


def fingerprint(path: Path) -> tuple[int, int, str]:
    metadata = path.stat()
    return (
        metadata.st_size,
        metadata.st_mtime_ns,
        hashlib.sha256(path.read_bytes()).hexdigest(),
    )


class GenericAgentPluginTests(unittest.TestCase):
    def test_contract_and_registry_bind_external_envelope_without_code_execution(self) -> None:
        contract = load_generic_agent_plugin_contract(ROOT)
        registry = load_source_registry(ROOT)
        source = validate_plugin_source(registry, contract, SOURCE_ID, ROOT)
        plugin = source["parser"]["plugin"]

        self.assertEqual(contract["schema_version"], SCHEMA_VERSION)
        self.assertEqual(contract["task_id"], TASK_ID)
        self.assertEqual(contract["acceptance_id"], ACCEPTANCE_ID)
        self.assertEqual(contract["entrypoint"], ENTRYPOINT_PATH.as_posix())
        self.assertEqual(contract["model_ref"], MODEL_PATH.as_posix())
        self.assertEqual(contract["protocol"]["schema_version"], ENVELOPE_SCHEMA_VERSION)
        self.assertEqual(source["status"], "fixture")
        self.assertEqual(plugin["plugin_id"], PLUGIN_ID)
        self.assertEqual(plugin["mode"], "external_envelope_only")
        self.assertEqual(plugin["push_policy"], PUSH_DEFAULTS)
        self.assertIs(plugin["arbitrary_code_execution"], False)
        self.assertIs(contract["safety"]["arbitrary_plugin_code_execution"], False)
        self.assertEqual(
            set(plugin),
            {
                "mode",
                "plugin_id",
                "protocol",
                "host_entrypoint",
                "contract_ref",
                "model_ref",
                "arbitrary_code_execution",
                "host_owned_gates",
                "push_policy",
            },
        )
        self.assertTrue((ROOT / CONTRACT_PATH).is_file())
        self.assertTrue((ROOT / MODEL_PATH).is_file())
        self.assertTrue((ROOT / ENTRYPOINT_PATH).is_file())

        for runtime_path in (
            ROOT / "scripts/memory_atlas_cli/generic_agent_plugin.py",
            ROOT / "scripts/sync_generic_agent_plugin.py",
            ROOT / "scripts/memory_atlas_cli/source_registry.py",
            ROOT / "scripts/memory_atlas_cli/sync.py",
        ):
            text = runtime_path.read_text(encoding="utf-8")
            self.assertNotIn(SOURCE_ID, text)
            self.assertNotIn(PLUGIN_ID, text)

    def test_second_plugin_source_requires_only_registry_configuration(self) -> None:
        contract = load_generic_agent_plugin_contract(ROOT)
        payload = load_source_registry(ROOT)
        second = copy.deepcopy(sync_source_map(payload)[SOURCE_ID])
        second_source_id = "second-nonstandard-agent"
        second_plugin_id = "second-envelope-plugin"
        second.update(
            {
                "source_id": second_source_id,
                "label": "Second non-standard Agent",
                "status": "configured",
                "state_path": f"data/sync_state/agents/{second_source_id}.json",
                "archive_path": f"data/public_raw/agents/{second_source_id}",
                "derived_outputs": [
                    f"data/derived/agents/{second_source_id}/agent_sync_summary.json"
                ],
            }
        )
        second["parser"]["plugin"]["plugin_id"] = second_plugin_id
        second["discovery"]["candidates"] = [
            {
                "kind": "environment_variable",
                "value": "MEMORY_ATLAS_SECOND_PLUGIN_ENVELOPE",
                "target_argument": "--plugin-envelope",
            },
            {"kind": "operator_argument", "value": "--plugin-envelope"},
        ]
        payload["sync_sources"].append(second)

        validated = validate_source_registry(payload, ROOT)
        validated_source = validate_plugin_source(
            validated,
            contract,
            second_source_id,
            ROOT,
        )

        self.assertEqual(
            validated_source["parser"]["plugin"]["plugin_id"],
            second_plugin_id,
        )
        self.assertEqual(
            validated_source["parser"]["plugin"]["host_entrypoint"],
            ENTRYPOINT_PATH.as_posix(),
        )

    def test_plugin_dry_run_validates_envelope_and_emits_no_content_or_path(self) -> None:
        result = run_generic_agent_plugin(
            package_root=ROOT,
            database_dir=ROOT,
            source_id=SOURCE_ID,
            plugin_id=PLUGIN_ID,
            envelope_path=ROOT / FIXTURE_PATH,
            dry_run=True,
            generated_at=FIXED_TIME,
        )

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["schema_version"], RESULT_SCHEMA_VERSION)
        self.assertEqual(result["task_id"], TASK_ID)
        self.assertEqual(result["acceptance_id"], ACCEPTANCE_ID)
        self.assertEqual(result["source_id"], SOURCE_ID)
        self.assertEqual(result["plugin"]["plugin_id"], PLUGIN_ID)
        self.assertEqual(result["plugin"]["execution_mode"], "external_envelope_only")
        self.assertEqual(result["event_count"], 2)
        self.assertEqual(result["message_count"], 3)
        self.assertEqual(result["adapter_mode"], "external_plugin_envelope")
        self.assertIs(result["dry_run"], True)
        self.assertIs(result["writes_files"], False)
        self.assertIs(result["plugin"]["arbitrary_code_execution"], False)
        self.assertIs(result["plugin"]["host_owned_write_pipeline"], True)
        self.assertIs(result["source_read_only"], True)
        self.assertEqual(result["main_push_contract"], PUSH_DEFAULTS)

        serialized = json.dumps(result, ensure_ascii=False, sort_keys=True)
        self.assertNotIn(str(ROOT), serialized)
        self.assertNotIn("Plugin roadmap review", serialized)
        self.assertNotIn("Synthetic non-standard source", serialized)

    def test_temp_apply_uses_host_owned_raw_ledger_and_derived_gates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            database = install_temp_database(workspace)
            envelope = workspace / "input.plugin-envelope.json"
            shutil.copy2(ROOT / FIXTURE_PATH, envelope)
            envelope_before = fingerprint(envelope)

            result = run_generic_agent_plugin(
                package_root=ROOT,
                database_dir=database,
                source_id=SOURCE_ID,
                plugin_id=PLUGIN_ID,
                envelope_path=envelope,
                dry_run=False,
                generated_at=FIXED_TIME,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["raw_ledger"]["status"], "PASS")
            self.assertEqual(result["raw_ledger"]["ledger_appended_count"], 2)
            self.assertEqual(result["event_count"], 2)
            self.assertEqual(result["message_count"], 3)
            self.assertIs(result["writes_files"], True)
            self.assertIs(result["production_database_mutation"], False)
            self.assertEqual(fingerprint(envelope), envelope_before)

            raw_root = database / f"data/public_raw/agents/{SOURCE_ID}"
            raw_files = sorted(raw_root.glob("*.json"))
            self.assertEqual(len(raw_files), 2)
            for raw_file in raw_files:
                row = json.loads(raw_file.read_text(encoding="utf-8"))
                self.assertEqual(row["source_id"], SOURCE_ID)
                self.assertEqual(row["adapter_mode"], "external_plugin_envelope")
                self.assertEqual(row["source_format"], "plugin:example-delimited-v1")
                self.assertEqual(row["plugin_provenance"]["plugin_id"], PLUGIN_ID)
                self.assertEqual(
                    row["plugin_provenance"]["protocol"],
                    ENVELOPE_SCHEMA_VERSION,
                )
                self.assertEqual(
                    row["plugin_provenance"]["source_artifact"]["trust"],
                    "producer_claim_only",
                )

            derived = (
                database
                / f"data/derived/agents/{SOURCE_ID}/agent_sync_summary.json"
            )
            summary = json.loads(derived.read_text(encoding="utf-8"))
            self.assertEqual(summary["adapter_mode"], "external_plugin_envelope")
            self.assertEqual(summary["source_formats"], ["plugin:example-delimited-v1"])

    def test_replay_keeps_append_only_raw_and_ledger_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            database = install_temp_database(workspace)
            envelope = workspace / "input.plugin-envelope.json"
            shutil.copy2(ROOT / FIXTURE_PATH, envelope)
            first = run_generic_agent_plugin(
                package_root=ROOT,
                database_dir=database,
                source_id=SOURCE_ID,
                plugin_id=PLUGIN_ID,
                envelope_path=envelope,
                dry_run=False,
                generated_at=FIXED_TIME,
            )
            tracked = sorted(
                (database / f"data/public_raw/agents/{SOURCE_ID}").glob("*.json")
            ) + [
                database
                / "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
            ]
            before = {path: fingerprint(path) for path in tracked}

            second = run_generic_agent_plugin(
                package_root=ROOT,
                database_dir=database,
                source_id=SOURCE_ID,
                plugin_id=PLUGIN_ID,
                envelope_path=envelope,
                dry_run=False,
                generated_at=FIXED_TIME,
            )

            self.assertEqual(first["envelope_sha256"], second["envelope_sha256"])
            self.assertEqual(second["raw_ledger"]["ledger_appended_count"], 0)
            self.assertIs(second["raw_ledger"]["idempotent"], True)
            self.assertEqual({path: fingerprint(path) for path in tracked}, before)

    def test_credential_is_rejected_before_database_write_without_value_echo(self) -> None:
        payload = fixture_payload()
        events = payload["canonical_events"]
        assert isinstance(events, list)
        first = events[0]
        assert isinstance(first, dict)
        messages = first["messages"]
        assert isinstance(messages, list)
        message = messages[0]
        assert isinstance(message, dict)
        credential_probe = "-".join(("sk", "proj", "1234567890abcdefghijklmnop"))
        message["text"] = credential_probe
        rewrite_event_digest(payload)

        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            database = install_temp_database(workspace)
            envelope = workspace / "credential.plugin-envelope.json"
            write_envelope(envelope, payload)

            with self.assertRaises(GenericAgentPluginError) as raised:
                run_generic_agent_plugin(
                    package_root=ROOT,
                    database_dir=database,
                    source_id=SOURCE_ID,
                    plugin_id=PLUGIN_ID,
                    envelope_path=envelope,
                    dry_run=False,
                    generated_at=FIXED_TIME,
                )

            self.assertEqual(str(raised.exception), "plugin_credential_gate_rejected")
            self.assertNotIn(credential_probe, str(raised.exception))
            self.assertFalse((database / "data").exists())

    def test_envelope_identity_hash_and_exact_schema_drift_fail_closed(self) -> None:
        mutations = (
            lambda value: value.__setitem__("source_id", "other-source"),
            lambda value: value.__setitem__("plugin_id", "other-plugin"),
            lambda value: value.__setitem__("events_sha256", "0" * 64),
            lambda value: value.__setitem__("unexpected", True),
        )
        for mutate in mutations:
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp_dir:
                payload = fixture_payload()
                mutate(payload)
                envelope = Path(temp_dir) / "drift.plugin-envelope.json"
                write_envelope(envelope, payload)
                with self.assertRaises(GenericAgentPluginError):
                    run_generic_agent_plugin(
                        package_root=ROOT,
                        database_dir=ROOT,
                        source_id=SOURCE_ID,
                        plugin_id=PLUGIN_ID,
                        envelope_path=envelope,
                        dry_run=True,
                        generated_at=FIXED_TIME,
                    )

    def test_event_duplicates_limits_and_role_drift_fail_closed(self) -> None:
        def duplicate_event(value: dict[str, object]) -> None:
            events = value["canonical_events"]
            assert isinstance(events, list)
            events.append(copy.deepcopy(events[0]))

        def duplicate_message(value: dict[str, object]) -> None:
            events = value["canonical_events"]
            assert isinstance(events, list)
            event = events[0]
            assert isinstance(event, dict)
            messages = event["messages"]
            assert isinstance(messages, list)
            messages.append(copy.deepcopy(messages[0]))

        def invalid_role(value: dict[str, object]) -> None:
            events = value["canonical_events"]
            assert isinstance(events, list)
            event = events[0]
            assert isinstance(event, dict)
            messages = event["messages"]
            assert isinstance(messages, list)
            message = messages[0]
            assert isinstance(message, dict)
            message["role"] = "root"

        def oversize_title(value: dict[str, object]) -> None:
            events = value["canonical_events"]
            assert isinstance(events, list)
            event = events[0]
            assert isinstance(event, dict)
            event["title"] = "x" * 65537

        for mutate in (duplicate_event, duplicate_message, invalid_role, oversize_title):
            with self.subTest(mutate=mutate), tempfile.TemporaryDirectory() as temp_dir:
                payload = fixture_payload()
                mutate(payload)
                rewrite_event_digest(payload)
                envelope = Path(temp_dir) / "invalid.plugin-envelope.json"
                write_envelope(envelope, payload)
                with self.assertRaises(GenericAgentPluginError):
                    run_generic_agent_plugin(
                        package_root=ROOT,
                        database_dir=ROOT,
                        source_id=SOURCE_ID,
                        plugin_id=PLUGIN_ID,
                        envelope_path=envelope,
                        dry_run=True,
                        generated_at=FIXED_TIME,
                    )

    def test_apply_rejects_database_internal_and_symlink_envelopes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            database = install_temp_database(workspace)
            internal = database / "input.plugin-envelope.json"
            shutil.copy2(ROOT / FIXTURE_PATH, internal)
            with self.assertRaises(GenericAgentPluginError) as internal_error:
                run_generic_agent_plugin(
                    package_root=ROOT,
                    database_dir=database,
                    source_id=SOURCE_ID,
                    plugin_id=PLUGIN_ID,
                    envelope_path=internal,
                    dry_run=False,
                    generated_at=FIXED_TIME,
                )
            self.assertEqual(
                str(internal_error.exception),
                "plugin_envelope_inside_database",
            )

            external = workspace / "external.plugin-envelope.json"
            shutil.copy2(ROOT / FIXTURE_PATH, external)
            symlink = workspace / "symlink.plugin-envelope.json"
            symlink.symlink_to(external)
            with self.assertRaises(GenericAgentPluginError):
                run_generic_agent_plugin(
                    package_root=ROOT,
                    database_dir=database,
                    source_id=SOURCE_ID,
                    plugin_id=PLUGIN_ID,
                    envelope_path=symlink,
                    dry_run=False,
                    generated_at=FIXED_TIME,
                )

    def test_atlasctl_routes_plugin_dry_run_and_rejects_standard_input_mode(self) -> None:
        routed = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                SOURCE_ID,
                "--plugin-envelope",
                str(ROOT / FIXTURE_PATH),
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(routed.returncode, 0, routed.stderr)
        payload = json.loads(routed.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["source_id"], SOURCE_ID)
        self.assertEqual(payload["plugin"]["plugin_id"], PLUGIN_ID)
        self.assertIs(payload["writes_files"], False)
        self.assertNotIn(str(ROOT), routed.stdout)

        wrong_mode = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                SOURCE_ID,
                "--input",
                str(ROOT / FIXTURE_PATH),
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(wrong_mode.returncode, 2, wrong_mode.stderr)
        wrong_payload = json.loads(wrong_mode.stdout)
        self.assertEqual(
            wrong_payload["reason"],
            "plugin source requires --plugin-envelope",
        )
        self.assertIs(wrong_payload["writes_files"], False)

        standard_source = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                "standard-agent-example",
                "--plugin-envelope",
                str(ROOT / FIXTURE_PATH),
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(standard_source.returncode, 2, standard_source.stderr)
        standard_payload = json.loads(standard_source.stdout)
        self.assertEqual(
            standard_payload["reason"],
            "--plugin-envelope requires a registry-bound plugin source",
        )
        self.assertIs(standard_payload["writes_files"], False)

    def test_fixture_apply_and_main_push_fail_before_production_effects(self) -> None:
        production_root = ROOT / f"data/public_raw/agents/{SOURCE_ID}"
        before = (
            {
                path.relative_to(production_root).as_posix(): fingerprint(path)
                for path in production_root.rglob("*")
                if path.is_file()
            }
            if production_root.exists()
            else None
        )
        apply_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                SOURCE_ID,
                "--plugin-envelope",
                str(ROOT / FIXTURE_PATH),
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(apply_result.returncode, 2, apply_result.stderr)
        apply_payload = json.loads(apply_result.stdout)
        self.assertIn("fixture source is acceptance-only", apply_payload["reason"])
        self.assertIs(apply_payload["writes_files"], False)
        self.assertIs(apply_payload["production_database_mutation"], False)

        push_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                SOURCE_ID,
                "--plugin-envelope",
                str(ROOT / FIXTURE_PATH),
                "--push-main",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(push_result.returncode, 2, push_result.stderr)
        push_payload = json.loads(push_result.stdout)
        self.assertEqual(
            push_payload["reason"],
            "push_main_requires_canonical_codex_source",
        )
        self.assertEqual(push_payload["push_attempt_count"], 0)
        self.assertIs(push_payload["remote_push_attempted"], False)
        self.assertIs(push_payload["fetch_executed"], False)
        self.assertIs(push_payload["commit_created"], False)
        after = (
            {
                path.relative_to(production_root).as_posix(): fingerprint(path)
                for path in production_root.rglob("*")
                if path.is_file()
            }
            if production_root.exists()
            else None
        )
        self.assertEqual(after, before)

    def test_contract_and_registry_drift_cannot_weaken_host_gates(self) -> None:
        contract = load_generic_agent_plugin_contract(ROOT)
        for mutate in (
            lambda value: value["host_gates"].__setitem__(
                "host_owned_write_pipeline",
                False,
            ),
            lambda value: value["safety"].__setitem__(
                "arbitrary_plugin_code_execution",
                True,
            ),
            lambda value: value["host_gates"]["push_policy"].__setitem__(
                "force",
                True,
            ),
        ):
            with self.subTest(contract_mutate=mutate):
                drifted = copy.deepcopy(contract)
                mutate(drifted)
                with self.assertRaises(GenericAgentPluginError):
                    validate_generic_agent_plugin_contract(drifted)

        registry = load_source_registry(ROOT)
        for mutate in (
            lambda plugin: plugin.__setitem__("arbitrary_code_execution", True),
            lambda plugin: plugin["push_policy"].__setitem__("force", True),
            lambda plugin: plugin.__setitem__("executable", "unsafe-command"),
        ):
            with self.subTest(registry_mutate=mutate):
                drifted = copy.deepcopy(registry)
                plugin = sync_source_map(drifted)[SOURCE_ID]["parser"]["plugin"]
                mutate(plugin)
                with self.assertRaises(Exception):
                    validate_source_registry(drifted, ROOT)


if __name__ == "__main__":
    unittest.main()
