from __future__ import annotations

import argparse
import copy
import json
import os
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

from memory_atlas_cli.source_registry import (  # noqa: E402
    PUSH_DEFAULTS,
    REGISTRY_PATH,
    REQUIRED_SOURCE_IDS,
    REQUIRED_SYNC_FIELDS,
    SOURCE_TYPES,
    SourceRegistryError,
    load_source_registry,
    resolve_sync_source,
    sync_source_map,
    validate_source_registry,
)
from memory_atlas_cli.sync import apply_environment_discovery  # noqa: E402


def canonical_payload() -> dict:
    return json.loads((ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))


class SourceRegistryContractTests(unittest.TestCase):
    def test_canonical_registry_matches_taskpack_fields_and_source_types(self) -> None:
        registry = load_source_registry(ROOT)
        contract = registry["sync_contract"]

        self.assertEqual(contract["required_fields"], list(REQUIRED_SYNC_FIELDS))
        self.assertEqual(contract["source_types"], list(SOURCE_TYPES))
        self.assertEqual(contract["required_source_ids"], list(REQUIRED_SOURCE_IDS))
        self.assertEqual(contract["push_defaults"], PUSH_DEFAULTS)
        self.assertIs(contract["source_read_only"], True)
        self.assertIs(contract["archive_append_only"], True)
        self.assertIs(contract["repository_relative_paths"], True)
        self.assertEqual(
            contract["public_raw_layout_ref"],
            "config/data_sources/public_raw_layout.json",
        )
        self.assertEqual(
            contract["credential_exclusion_ref"],
            "config/data_sources/credential_exclusion.json",
        )

    def test_canonical_registry_covers_chatgpt_codex_and_generic_agent(self) -> None:
        sources = sync_source_map(load_source_registry(ROOT))

        self.assertTrue(set(REQUIRED_SOURCE_IDS).issubset(sources))
        self.assertEqual(sources["chatgpt"]["source_type"], "chatgpt_export")
        self.assertEqual(sources["codex"]["source_type"], "codex_local")
        self.assertEqual(sources["generic_agent_template"]["source_type"], "generic_agent")
        self.assertEqual(sources["chatgpt"]["archive_path"], "data/public_raw/chatgpt")
        self.assertEqual(sources["codex"]["archive_path"], "data/public_raw/codex")
        self.assertEqual(
            sources["generic_agent_template"]["archive_path"],
            "data/public_raw/agents/{source_id}",
        )
        self.assertEqual(sources["codex-reviewer"]["source_type"], "generic_agent")
        for source in sources.values():
            self.assertEqual(source["push_policy"], PUSH_DEFAULTS)
            self.assertEqual(
                source["credential_exclusions"],
                {
                    "policy": "credentials_not_transcript",
                    "contract_ref": "config/data_sources/credential_exclusion.json",
                    "status": "active",
                },
            )
            self.assertTrue((ROOT / source["parser"]["entrypoint"]).is_file())

    def test_standard_generic_source_can_be_added_with_config_only(self) -> None:
        payload = canonical_payload()
        source = copy.deepcopy(payload["sync_sources"][2])
        source.update(
            {
                "source_id": "claude_local",
                "label": "Claude 本地导出",
                "status": "configured",
                "template_parameters": [],
                "state_path": "data/sync_state/agents/claude_local.json",
                "archive_path": "data/public_raw/agents/claude_local",
                "derived_outputs": ["data/derived/agents/claude_local/agent_sync_summary.json"],
            }
        )
        source["discovery"]["candidates"] = [
            {
                "kind": "environment_variable",
                "value": "MEMORY_ATLAS_CLAUDE_INPUT",
                "target_argument": "--input",
            },
            {"kind": "operator_argument", "value": "--input"},
        ]
        payload["sync_sources"].append(source)

        validated = validate_source_registry(payload, ROOT)

        self.assertIn("claude_local", sync_source_map(validated))
        self.assertEqual(resolve_sync_source(validated, "claude_local")["source_type"], "generic_agent")

    def test_atlasctl_sync_dispatch_reads_parser_and_source_type_from_registry(self) -> None:
        source = (ROOT / "scripts/memory_atlas_cli/sync.py").read_text(encoding="utf-8")

        self.assertIn("registry = load_source_registry(ROOT)", source)
        self.assertIn("resolve_sync_source(registry, args.source)", source)
        self.assertIn('registered_source["parser"]["entrypoint"]', source)
        self.assertNotIn("CHATGPT_SYNC", source)
        self.assertNotIn("CODEX_SYNC", source)
        self.assertNotIn("FUTURE_AGENT_SYNC", source)

    def test_registered_generic_agent_is_available_through_atlasctl_without_core_edit(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                "codex-reviewer",
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
        self.assertEqual(payload["source_id"], "codex-reviewer")
        self.assertEqual(payload["agent_id"], "codex-reviewer")
        self.assertIs(payload["writes_files"], False)

    def test_registered_generic_agent_environment_discovery_drives_real_adapter_dry_run(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            report = Path(temp_dir) / "review.md"
            report.write_text("# Independent review\n\nNo blocking findings.\n", encoding="utf-8")
            environment = os.environ.copy()
            environment["MEMORY_ATLAS_CODEX_REVIEWER_INPUT"] = str(report)
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/atlasctl.py"),
                    "sync",
                    "--source",
                    "codex-reviewer",
                    "--dry-run",
                ],
                cwd=ROOT,
                env=environment,
                text=True,
                capture_output=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "PASS")
        self.assertEqual(payload["source_id"], "codex-reviewer")
        self.assertEqual(payload["agent_id"], "codex-reviewer")
        self.assertEqual(payload["source_format"], "markdown_report")
        self.assertEqual(payload["raw_root"], "data/public_raw/agents/codex-reviewer")
        self.assertEqual(
            payload["derived_summary"],
            "data/derived/agents/codex-reviewer/agent_sync_summary.json",
        )
        self.assertIs(payload["writes_files"], False)

    def test_explicit_generic_input_blocks_conflicting_environment_discovery(self) -> None:
        cases = (
            ("input", "markdown_report", "--markdown-report"),
            ("markdown_report", "input", "--input"),
        )
        for explicit_field, environment_field, target_argument in cases:
            with self.subTest(explicit_field=explicit_field):
                args = argparse.Namespace(input=None, markdown_report=None)
                explicit_path = Path(f"explicit.{explicit_field}")
                setattr(args, explicit_field, explicit_path)
                registered_source = {
                    "discovery": {
                        "candidates": [
                            {
                                "kind": "environment_variable",
                                "value": "MEMORY_ATLAS_CONFLICTING_INPUT",
                                "target_argument": target_argument,
                            }
                        ]
                    }
                }
                environment = {"MEMORY_ATLAS_CONFLICTING_INPUT": f"environment.{environment_field}"}

                with mock.patch.dict(os.environ, environment, clear=False):
                    apply_environment_discovery(args, registered_source)

                self.assertEqual(getattr(args, explicit_field), explicit_path)
                self.assertIsNone(getattr(args, environment_field))

    def test_generic_agent_jsonl_input_runs_all_records_without_writes(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "events.jsonl"
            source.write_text(
                "\n".join(
                    (
                        json.dumps({"event_id": "event-1", "title": "First", "messages": []}),
                        json.dumps({"event_id": "event-2", "title": "Second", "messages": []}),
                    )
                )
                + "\n",
                encoding="utf-8",
            )
            result = subprocess.run(
                [
                    sys.executable,
                    str(ROOT / "scripts/atlasctl.py"),
                    "sync",
                    "--source",
                    "future-agent",
                    "--agent-id",
                    "jsonl-reviewer",
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
        self.assertEqual(payload["source_id"], "future-agent")
        self.assertEqual(payload["agent_id"], "jsonl-reviewer")
        self.assertEqual(payload["event_count"], 2)
        self.assertEqual(payload["source_formats"], ["json_event"])
        self.assertIs(payload["writes_files"], False)

        invalid_cases = {
            "empty": "",
            "scalar_only": "42\n",
            "mixed_valid_invalid": '{"event_id":"valid","messages":[]}\n42\n',
        }
        for label, content in invalid_cases.items():
            with self.subTest(label=label), tempfile.TemporaryDirectory() as invalid_dir:
                invalid_source = Path(invalid_dir) / "events.jsonl"
                invalid_source.write_text(content, encoding="utf-8")
                invalid_result = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/atlasctl.py"),
                        "sync",
                        "--source",
                        "future-agent",
                        "--agent-id",
                        "jsonl-reviewer",
                        "--input",
                        str(invalid_source),
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(invalid_result.returncode, 2, invalid_result.stderr)
                invalid_payload = json.loads(invalid_result.stdout)
                self.assertEqual(invalid_payload["status"], "FAIL_CLOSED")
                self.assertEqual(invalid_payload["reason"], "source_input_invalid")
                self.assertIs(invalid_payload["writes_files"], False)

    def test_registered_generic_agent_rejects_agent_id_namespace_override(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                "codex-reviewer",
                "--agent-id",
                "alternate-reviewer",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertEqual(payload["source_id"], "codex-reviewer")
        self.assertIs(payload["writes_files"], False)

        template_result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/atlasctl.py"),
                "sync",
                "--source",
                "future-agent",
                "--agent-id",
                "codex-reviewer",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(template_result.returncode, 2, template_result.stderr)
        template_payload = json.loads(template_result.stdout)
        self.assertEqual(template_payload["status"], "FAIL_CLOSED")
        self.assertEqual(template_payload["source_id"], "future-agent")
        self.assertIs(template_payload["writes_files"], False)

        for agent_id in (
            "../codex-reviewer",
            "./codex-reviewer",
            "codex-reviewer.",
            "codex-reviewer-",
            "codex-reviewer_",
            "CODEX-REVIEWER",
            "Codex-Reviewer",
            "con",
            "con.txt",
            "nul",
            "com1",
            "lpt1",
            " codex-reviewer",
            "codex-reviewer ",
        ):
            with self.subTest(agent_id=agent_id):
                normalized_collision = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/atlasctl.py"),
                        "sync",
                        "--source",
                        "future-agent",
                        "--agent-id",
                        agent_id,
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(normalized_collision.returncode, 2, normalized_collision.stderr)
                normalized_payload = json.loads(normalized_collision.stdout)
                self.assertEqual(normalized_payload["status"], "FAIL_CLOSED")
                self.assertIs(normalized_payload["writes_files"], False)

    def test_registry_rejects_source_specific_core_drift(self) -> None:
        mutations = {
            "missing required field": lambda source: source.pop("schedule"),
            "absolute user path": lambda source: source["discovery"]["candidates"].append(
                {
                    "kind": "home_relative",
                    "value": "/Users/alice/.codex",
                    "target_argument": "--codex-home",
                }
            ),
            "windows drive path": lambda source: source["discovery"]["candidates"].append(
                {
                    "kind": "home_relative",
                    "value": "D:/Profiles/alice/.codex",
                    "target_argument": "--codex-home",
                }
            ),
            "unc path": lambda source: source["discovery"]["candidates"].append(
                {
                    "kind": "home_relative",
                    "value": "//server/share/.codex",
                    "target_argument": "--codex-home",
                }
            ),
            "archive traversal": lambda source: source.update(
                {"archive_path": "data/public_raw/../private"}
            ),
            "missing parser": lambda source: source["parser"].update(
                {"entrypoint": "scripts/missing_source_parser.py"}
            ),
            "existing but incompatible parser": lambda source: source["parser"].update(
                {"entrypoint": "scripts/build_personalization_exports.py"}
            ),
            "push policy drift": lambda source: source["push_policy"].update({"force": True}),
            "unknown source type": lambda source: source.update({"source_type": "claude_special"}),
            "canonical status drift": lambda source: source.update({"status": "template"}),
            "unsupported operator argument": lambda source: source["discovery"]["candidates"].append(
                {"kind": "operator_argument", "value": "--export"}
            ),
        }

        for label, mutate in mutations.items():
            with self.subTest(label=label):
                payload = canonical_payload()
                mutate(payload["sync_sources"][1])
                with self.assertRaises(SourceRegistryError):
                    validate_source_registry(payload, ROOT)

    def test_registry_rejects_canonical_source_id_type_swap(self) -> None:
        payload = canonical_payload()
        payload["sync_sources"][0]["source_id"] = "codex"
        payload["sync_sources"][1]["source_id"] = "chatgpt"

        with self.assertRaises(SourceRegistryError):
            validate_source_registry(payload, ROOT)

        extra_chatgpt = canonical_payload()
        duplicate = copy.deepcopy(extra_chatgpt["sync_sources"][0])
        duplicate["source_id"] = "chatgpt_alt"
        extra_chatgpt["sync_sources"].append(duplicate)
        with self.assertRaises(SourceRegistryError):
            validate_source_registry(extra_chatgpt, ROOT)

        reserved_alias = canonical_payload()
        alias_source = copy.deepcopy(reserved_alias["sync_sources"][2])
        alias_source.update({
            "source_id": "future-agent",
            "status": "configured",
            "template_parameters": [],
            "state_path": "data/sync_state/agents/future-agent.json",
            "archive_path": "data/public_raw/agents/future-agent",
            "derived_outputs": ["data/derived/agents/future-agent/agent_sync_summary.json"],
        })
        reserved_alias["sync_sources"].append(alias_source)
        with self.assertRaises(SourceRegistryError):
            validate_source_registry(reserved_alias, ROOT)

        trailing_delimiter = canonical_payload()
        trailing_source = copy.deepcopy(trailing_delimiter["sync_sources"][2])
        trailing_source.update({
            "source_id": "generic-agent-",
            "status": "configured",
            "template_parameters": [],
            "state_path": "data/sync_state/agents/generic-agent-.json",
            "archive_path": "data/public_raw/agents/generic-agent-",
            "derived_outputs": ["data/derived/agents/generic-agent-/agent_sync_summary.json"],
        })
        trailing_delimiter["sync_sources"].append(trailing_source)
        with self.assertRaises(SourceRegistryError):
            validate_source_registry(trailing_delimiter, ROOT)

        for source_id in ("con", "con.txt", "nul", "com1", "lpt1"):
            with self.subTest(reserved_windows_source_id=source_id):
                reserved_device = canonical_payload()
                source = copy.deepcopy(reserved_device["sync_sources"][2])
                source.update({
                    "source_id": source_id,
                    "status": "configured",
                    "template_parameters": [],
                    "state_path": f"data/sync_state/agents/{source_id}.json",
                    "archive_path": f"data/public_raw/agents/{source_id}",
                    "derived_outputs": [f"data/derived/agents/{source_id}/agent_sync_summary.json"],
                })
                reserved_device["sync_sources"].append(source)
                with self.assertRaises(SourceRegistryError):
                    validate_source_registry(reserved_device, ROOT)

        for source_id in (" generic-agent", "generic-agent "):
            with self.subTest(whitespace_source_id=source_id):
                whitespace_identity = canonical_payload()
                source = copy.deepcopy(whitespace_identity["sync_sources"][2])
                source["source_id"] = source_id
                whitespace_identity["sync_sources"].append(source)
                with self.assertRaises(SourceRegistryError):
                    validate_source_registry(whitespace_identity, ROOT)

    def test_generic_adapter_rejects_spoofed_canonical_provenance(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "scripts/sync_future_agent_data.py"),
                "--source-id",
                "chatgpt",
                "--agent-id",
                "codex-reviewer",
                "--dry-run",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )

        self.assertEqual(result.returncode, 2, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["status"], "FAIL_CLOSED")
        self.assertEqual(payload["reason"], "source_identity_mismatch")
        self.assertIs(payload["writes_files"], False)

        for agent_id in (
            "../codex-reviewer",
            "codex-reviewer.",
            "codex-reviewer-",
            "codex-reviewer_",
            "CODEX-REVIEWER",
            "Codex-Reviewer",
            "con",
            "con.txt",
            "nul",
            "com1",
            "lpt1",
            " codex-reviewer",
            "codex-reviewer ",
        ):
            with self.subTest(direct_agent_id=agent_id):
                normalized = subprocess.run(
                    [
                        sys.executable,
                        str(ROOT / "scripts/sync_future_agent_data.py"),
                        "--source-id",
                        "future-agent",
                        "--agent-id",
                        agent_id,
                        "--dry-run",
                    ],
                    cwd=ROOT,
                    text=True,
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(normalized.returncode, 2, normalized.stderr)
                normalized_payload = json.loads(normalized.stdout)
                self.assertEqual(normalized_payload["status"], "FAIL_CLOSED")
                self.assertEqual(normalized_payload["reason"], "source_identity_mismatch")
                self.assertIs(normalized_payload["writes_files"], False)

    def test_live_code_and_configuration_do_not_reference_legacy_machine_registry(self) -> None:
        legacy_reference = "机器治理/同步与备份/" + "sync_source_registry.json"
        live_roots = ("scripts", "tests", "config", "apps")
        references: list[str] = []
        for root_name in live_roots:
            for path in (ROOT / root_name).rglob("*"):
                if not path.is_file() or path.suffix not in {
                    ".cjs",
                    ".js",
                    ".json",
                    ".mjs",
                    ".py",
                    ".sh",
                    ".toml",
                    ".ts",
                    ".tsx",
                    ".yaml",
                    ".yml",
                }:
                    continue
                if legacy_reference in path.read_text(encoding="utf-8", errors="ignore"):
                    references.append(path.relative_to(ROOT).as_posix())

        self.assertEqual(references, [])

    def test_existing_derived_source_contract_remains_backward_compatible(self) -> None:
        registry = load_source_registry(ROOT)
        source_ids = [source["id"] for source in registry["sources"]]

        self.assertEqual(
            source_ids,
            ["memory_atlas", "codex", "wechat", "xiaohongshu", "douyin"],
        )
        self.assertEqual(registry["schema_version"], "memory_atlas_data_source_registry.v1")
        self.assertIn("source_id", registry["canonical_event_contract"]["required_fields"])


if __name__ == "__main__":
    unittest.main()
