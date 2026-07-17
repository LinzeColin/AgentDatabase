from __future__ import annotations

import copy
import importlib.util
import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli.chatgpt_export_parser import (  # noqa: E402
    EXPECTED_CONTRACT,
    EXPECTED_MODEL_PARAMETERS,
    ChatGPTExportParserError,
    load_chatgpt_export_parser_contract,
    load_chatgpt_export_parser_model_parameters,
    parse_chatgpt_export,
    validate_chatgpt_export_parser_contract,
    validate_chatgpt_export_parser_model_parameters,
)


def conversation(
    conversation_id: str,
    *,
    content: object = "hello",
    extra: dict[str, object] | None = None,
) -> dict[str, object]:
    payload: dict[str, object] = {
        "id": conversation_id,
        "title": f"Conversation {conversation_id}",
        "create_time": 1_760_000_000,
        "update_time": 1_760_000_060,
        "mapping": {
            "root": {"id": "root", "parent": None, "children": ["message"]},
            "message": {
                "id": "message",
                "message": {
                    "id": f"message-{conversation_id}",
                    "author": {"role": "user", "name": "fixture-author"},
                    "create_time": 1_760_000_001,
                    "content": {
                        "content_type": "multimodal_text",
                        "parts": [content],
                        "future_content_field": {"kept": True},
                    },
                    "metadata": {"future_message_metadata": "kept"},
                    "recipient": "all",
                },
            },
        },
        "future_conversation_field": {"kept": True},
    }
    if extra:
        payload.update(extra)
    return payload


def load_sync_module(name: str):
    module_path = SCRIPTS / "sync_chatgpt_memory_data.py"
    spec = importlib.util.spec_from_file_location(name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


class ChatGPTExportParserContractTests(unittest.TestCase):
    def test_contract_and_model_are_strict_and_task_bounded(self) -> None:
        contract = load_chatgpt_export_parser_contract(ROOT)
        model = load_chatgpt_export_parser_model_parameters(ROOT)

        self.assertEqual(contract, EXPECTED_CONTRACT)
        self.assertEqual(model, EXPECTED_MODEL_PARAMETERS)
        self.assertEqual(contract["task_id"], "S09-P1-T1")
        self.assertEqual(contract["acceptance_id"], "ACC-MA-V121-S09-P1-T1")
        self.assertEqual(
            contract["quarantine"]["path"],
            "data/processed/conversations/chatgpt_parse_quarantine.jsonl",
        )
        self.assertIs(contract["unknown_fields"]["preserve"], True)
        self.assertIs(contract["security"]["source_read_only"], True)
        self.assertIs(contract["phase_boundary"]["implements_incremental_ids"], False)
        self.assertEqual(contract["phase_boundary"]["next_task"], "S09-P1-T2")

    def test_contract_and_model_drift_fail_closed(self) -> None:
        contract = copy.deepcopy(EXPECTED_CONTRACT)
        contract["unknown_fields"]["preserve"] = False
        with self.assertRaises(ChatGPTExportParserError):
            validate_chatgpt_export_parser_contract(contract)

        model = copy.deepcopy(EXPECTED_MODEL_PARAMETERS)
        model["limits"]["maximum_json_files"] = 0
        with self.assertRaises(ChatGPTExportParserError):
            validate_chatgpt_export_parser_model_parameters(model)


class ChatGPTExportParserFormatTests(unittest.TestCase):
    def test_canonical_export_preserves_unknown_fields_and_attachment_payload(self) -> None:
        attachment = {
            "content_type": "image_asset_pointer",
            "asset_pointer": "file-service://fixture-image",
            "size_bytes": 42,
            "future_attachment_field": {"kept": True},
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "conversations.json"
            source.write_text(
                json.dumps([conversation("canonical", content=attachment)]),
                encoding="utf-8",
            )

            report = parse_chatgpt_export(source)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["conversation_count"], 1)
        self.assertEqual(report["attachment_count"], 1)
        self.assertEqual(report["quarantine_count"], 0)
        parsed = report["conversations"][0]
        self.assertEqual(parsed["future_conversation_field"], {"kept": True})
        message = parsed["mapping"]["message"]["message"]
        self.assertEqual(message["recipient"], "all")
        self.assertEqual(message["metadata"]["future_message_metadata"], "kept")
        self.assertEqual(
            message["content"]["future_content_field"], {"kept": True}
        )
        self.assertEqual(
            message["content"]["parts"][0]["future_attachment_field"],
            {"kept": True},
        )
        provenance = parsed["_memory_atlas_parser"]
        self.assertEqual(provenance["source_ref"], "conversations.json")
        self.assertEqual(provenance["attachment_count"], 1)

    def test_numbered_files_metadata_and_future_container_are_supported(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "1.json").write_text(
                json.dumps(conversation("numbered-one")), encoding="utf-8"
            )
            (source / "conversation_2.json").write_text(
                json.dumps(
                    {
                        "data": [conversation("numbered-two")],
                        "batch_metadata": {"kept": True},
                    }
                ),
                encoding="utf-8",
            )
            (source / "metadata.json").write_text(
                json.dumps(
                    {
                        "export_batch": "fixture-batch",
                        "future_metadata": {"kept": True},
                    }
                ),
                encoding="utf-8",
            )

            report = parse_chatgpt_export(source)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["conversation_count"], 2)
        self.assertEqual(report["metadata_count"], 2)
        self.assertEqual(
            {row["id"] for row in report["conversations"]},
            {"numbered-one", "numbered-two"},
        )
        metadata = next(
            row
            for row in report["export_metadata"]
            if row["source_ref"] == "metadata.json"
        )
        self.assertEqual(metadata["payload"]["future_metadata"], {"kept": True})
        self.assertRegex(metadata["payload_sha256"], r"^[0-9a-f]{64}$")
        container_metadata = next(
            row
            for row in report["export_metadata"]
            if row["source_ref"] == "conversation_2.json"
        )
        self.assertEqual(
            container_metadata["payload"],
            {"batch_metadata": {"kept": True}},
        )
        formats = {row["format"] for row in report["source_files"]}
        self.assertIn("numbered_conversation", formats)
        self.assertIn("future_recognizable_container", formats)
        self.assertIn("export_metadata", formats)

    def test_recognizable_future_list_is_parsed_and_empty_source_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "future-batch.json").write_text(
                json.dumps([conversation("future-list")]),
                encoding="utf-8",
            )

            report = parse_chatgpt_export(source)

        self.assertEqual(report["conversation_count"], 1)
        self.assertEqual(report["source_files"][0]["format"], "future_recognizable_list")
        with tempfile.TemporaryDirectory() as temp_dir:
            with self.assertRaisesRegex(
                ChatGPTExportParserError,
                "chatgpt_parser_no_json_inputs",
            ):
                parse_chatgpt_export(Path(temp_dir))

    def test_zip_supports_canonical_numbered_and_metadata_members(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "export.zip"
            with zipfile.ZipFile(source, "w") as archive:
                archive.writestr(
                    "export/conversations.json",
                    json.dumps([conversation("zip-canonical")]),
                )
                archive.writestr(
                    "export/3.json", json.dumps(conversation("zip-numbered"))
                )
                archive.writestr(
                    "export/attachments.json",
                    json.dumps({"attachments": [{"id": "attachment-1"}]}),
                )

            report = parse_chatgpt_export(source)

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["conversation_count"], 2)
        self.assertEqual(report["metadata_count"], 1)
        self.assertEqual(report["quarantine_count"], 0)
        self.assertEqual(
            {row["id"] for row in report["conversations"]},
            {"zip-canonical", "zip-numbered"},
        )

    def test_every_unparseable_item_and_file_enters_sanitized_quarantine(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir)
            (source / "conversations.json").write_text(
                json.dumps(
                    [
                        conversation("valid"),
                        "private text must not be copied",
                        {"unknown_only": "private value must not be copied"},
                    ]
                ),
                encoding="utf-8",
            )
            (source / "4.json").write_text("{broken", encoding="utf-8")
            (source / "notes.json").write_text(
                json.dumps({"notes": "private note must not be copied"}),
                encoding="utf-8",
            )

            report = parse_chatgpt_export(source)

        self.assertEqual(report["status"], "PASS_WITH_QUARANTINE")
        self.assertEqual(report["conversation_count"], 1)
        self.assertEqual(report["quarantine_count"], 4)
        reasons = {row["reason_code"] for row in report["quarantine"]}
        self.assertEqual(
            reasons,
            {
                "conversation_not_object",
                "conversation_shape_unrecognized",
                "json_decode_failed",
                "json_file_unrecognized",
            },
        )
        encoded = json.dumps(report["quarantine"], ensure_ascii=False)
        self.assertNotIn("private text", encoded)
        self.assertNotIn("private value", encoded)
        self.assertNotIn("private note", encoded)
        for row in report["quarantine"]:
            self.assertRegex(row["payload_sha256"], r"^[0-9a-f]{64}$")
            self.assertNotIn("payload", row)

    def test_message_shape_failures_are_visible_without_dropping_conversation(self) -> None:
        payload = conversation("message-shapes")
        payload["mapping"] = {
            "root": {"id": "root", "message": None},
            "bad-node": "not-an-object",
            "bad-message": {"id": "bad-message", "message": "not-an-object"},
        }
        payload["messages"] = [
            {
                "id": "valid-message",
                "role": "assistant",
                "content": {"parts": ["valid"]},
            },
            17,
        ]
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "conversations.json"
            source.write_text(json.dumps([payload]), encoding="utf-8")

            report = parse_chatgpt_export(source)

        self.assertEqual(report["conversation_count"], 1)
        reasons = [row["reason_code"] for row in report["quarantine"]]
        self.assertEqual(
            reasons,
            [
                "mapping_node_not_object",
                "mapping_message_not_object",
                "message_not_object",
            ],
        )

    def test_reserved_parser_field_is_preserved_inside_trusted_provenance(self) -> None:
        original = {"future_source_value": {"kept": True}}
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "conversations.json"
            source.write_text(
                json.dumps(
                    [conversation("reserved", extra={"_memory_atlas_parser": original})]
                ),
                encoding="utf-8",
            )

            report = parse_chatgpt_export(source)

        provenance = report["conversations"][0]["_memory_atlas_parser"]
        self.assertEqual(provenance["source_field_preserved"], original)
        self.assertEqual(provenance["source_ref"], "conversations.json")


class ChatGPTExportParserIntegrationTests(unittest.TestCase):
    def test_legacy_loader_exposes_parse_report_without_breaking_list_contract(self) -> None:
        module = load_sync_module("s09_p1_t1_loader")
        with tempfile.TemporaryDirectory() as temp_dir:
            source = Path(temp_dir) / "conversations.json"
            source.write_text(
                json.dumps([conversation("legacy-loader"), "invalid"]),
                encoding="utf-8",
            )

            rows = module.load_official_export(source)

        self.assertIsInstance(rows, list)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["id"], "legacy-loader")
        self.assertEqual(rows.parse_report["quarantine_count"], 1)

    def test_sync_dry_run_reports_parser_coverage_and_preserves_extensions(self) -> None:
        module = load_sync_module("s09_p1_t1_sync")
        attachment = {
            "content_type": "file_attachment",
            "asset_pointer": "file-service://fixture-file",
            "future_attachment_field": "kept",
        }
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            source = root / "conversations.json"
            source.write_text(
                json.dumps(
                    [conversation("sync", content=attachment), {"unknown": True}]
                ),
                encoding="utf-8",
            )

            result = module.sync_official_export(
                root / "database", source, dry_run=True
            )

        self.assertEqual(result["status"], "PASS_WITH_QUARANTINE")
        self.assertEqual(result["conversation_count"], 1)
        self.assertEqual(result["attachment_count"], 1)
        self.assertEqual(result["quarantine_count"], 1)
        self.assertEqual(result["metadata_count"], 0)
        self.assertFalse(result["writes_files"])
        normalized = module.conversation_payload(conversation("extensions"))
        self.assertEqual(
            normalized["source_extensions"]["future_conversation_field"],
            {"kept": True},
        )
        message = normalized["messages"][0]
        self.assertEqual(message["source_extensions"]["recipient"], "all")
        self.assertEqual(message["author_extensions"]["name"], "fixture-author")
        self.assertEqual(
            message["content_extensions"]["future_content_field"],
            {"kept": True},
        )

    def test_sync_apply_writes_only_sanitized_quarantine_payloads(self) -> None:
        module = load_sync_module("s09_p1_t1_quarantine_apply")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database"
            for relative in (
                Path("config/data_sources/raw_ledger.json"),
                Path("config/data_sources/chatgpt_derived.json"),
                Path(
                    "机器治理/参数与公式/chatgpt_derived.v1_2_1_s09_p1_t3.json"
                ),
            ):
                target = database / relative
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes((ROOT / relative).read_bytes())
            source = root / "conversations.json"
            source.write_text(
                json.dumps(
                    [conversation("apply"), "private text must not be copied"]
                ),
                encoding="utf-8",
            )

            result = module.sync_official_export(database, source, dry_run=False)

            quarantine_path = database / result["quarantine_path"]
            quarantine_payload = quarantine_path.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "PASS_WITH_QUARANTINE")
        self.assertEqual(result["quarantine_count"], 1)
        self.assertNotIn("private text", quarantine_payload)
        row = json.loads(quarantine_payload)
        self.assertEqual(row["reason_code"], "conversation_not_object")
        self.assertNotIn("payload", row)

    def test_all_rejected_apply_preserves_existing_processed_outputs(self) -> None:
        module = load_sync_module("s09_p1_t1_all_rejected_apply")
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            database = root / "database"
            manifest = database / module.PROCESSED_MANIFEST
            summary = database / module.DERIVED_SUMMARY
            manifest.parent.mkdir(parents=True)
            summary.parent.mkdir(parents=True)
            manifest.write_text("existing-manifest\n", encoding="utf-8")
            summary.write_text("existing-summary\n", encoding="utf-8")
            source = root / "notes.json"
            source.write_text(
                json.dumps({"notes": "private value must not be copied"}),
                encoding="utf-8",
            )

            result = module.sync_official_export(database, source, dry_run=False)

            quarantine = (database / result["quarantine_path"]).read_text(
                encoding="utf-8"
            )
            manifest_after = manifest.read_text(encoding="utf-8")
            summary_after = summary.read_text(encoding="utf-8")

        self.assertEqual(result["status"], "QUARANTINED")
        self.assertEqual(result["conversation_count"], 0)
        self.assertTrue(result["writes_files"])
        self.assertEqual(manifest_after, "existing-manifest\n")
        self.assertEqual(summary_after, "existing-summary\n")
        self.assertNotIn("private value", quarantine)


if __name__ == "__main__":
    unittest.main()
