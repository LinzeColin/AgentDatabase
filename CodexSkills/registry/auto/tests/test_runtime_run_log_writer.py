from __future__ import annotations

import datetime as dt
import os
import tempfile
import unittest
from pathlib import Path

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.runtime.core import (
    AutoRuntimeError,
    PROTOCOL,
    SCHEMA_PREFIX,
    canonical_with_digest,
)
from CodexSkills.registry.auto.runtime.run_log_writer import (
    DAILY_MANIFEST_SCHEMA,
    INDEX_ENTRY_SCHEMA,
    JSONL_SERIALIZATION,
    OBJECT_SERIALIZATION,
    PUBLIC_RUN_EVENT_SCHEMA,
    DailyRunShardWriter,
    DailyRunTreeReader,
)
from CodexSkills.registry.auto.tools.validate_auto import (
    validate_auto_instance,
)

from runtime_helpers import (
    CANDIDATE_DIGEST,
    final_contract,
    uid,
)


UTC = dt.timezone.utc


def event(
    number: int,
    occurred_at: str,
    *,
    supersedes=None,
):
    value = {
        "schema_version": PUBLIC_RUN_EVENT_SCHEMA,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CANDIDATE_DIGEST,
        "event_uid": uid("evt", number),
        "run_uid": uid("run", number),
        "event_type": (
            "BINDING_CORRECTION"
            if supersedes is not None
            else "RUN_OBSERVED"
        ),
        "occurred_at": occurred_at,
        "surface_class": "CODEX_AUTOMATION",
        "actor_role": "AUTOMATION",
        "adapter_id": "run-observer-adapter",
        "adapter_version": "2.0.0",
        "adapter_schema_digest": "a" * 64,
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:"
            "policy:run-mapping:v1"
        ),
        "mapping_policy_digest": "b" * 64,
        "trigger_kind": "MANUAL",
        "run_status": "SUCCESS",
        "model_ref": "gpt-5-6-sol",
        "reasoning_effort": "XHIGH",
        "metrics": {
            "duration_ms": 1000,
            "tool_call_count": 2,
            "input_tokens": None,
            "output_tokens": None,
            "token_usage_status": "UNAVAILABLE",
        },
        "binding_state": "UNKNOWN",
        "unknown_reason_code": "MAPPING_NOT_PROVABLE",
        "redaction": {
            "policy_snapshot_digest": "c" * 64,
            "unknown_fields_dropped": 0,
            "omitted_category_codes": [],
            "post_serialization_scan_passed": True,
        },
        "immutable": True,
        "event_digest": "0" * 64,
    }
    if supersedes is not None:
        value["supersedes_event_uid"] = supersedes["event_uid"]
        value["supersedes_event_digest"] = supersedes["event_digest"]
    return canonical_with_digest(value, "event_digest")


def write_plan(root: Path, plan) -> None:
    for artifact in plan.artifacts:
        target = root.joinpath(*artifact.relative_path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(artifact.payload)


class RuntimeRunLogWriterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = final_contract()
        self.writer = DailyRunShardWriter(
            self.contract,
            CANDIDATE_DIGEST,
        )
        self.first = event(
            1,
            "2026-07-22T23:00:00.000000Z",
        )
        self.second = event(
            2,
            "2026-07-22T23:30:00.000000Z",
        )
        self.published = dt.datetime(
            2026,
            7,
            23,
            0,
            0,
            tzinfo=UTC,
        )

    def plan(self, events, **kwargs):
        return self.writer.plan(
            events,
            manifest_uid=kwargs.pop("manifest_uid", uid("drm", 1)),
            auto_transaction_uid=kwargs.pop(
                "auto_transaction_uid",
                uid("atx", 1),
            ),
            publication_transaction_at=kwargs.pop(
                "publication_transaction_at",
                self.published,
            ),
            **kwargs,
        )

    def test_writer_builds_exact_jcs_lines_and_daily_manifest(self) -> None:
        plan = self.plan([self.second, self.first])
        self.assertEqual(plan.local_date, "2026-07-23")
        self.assertEqual(plan.manifest_revision, 1)
        self.assertIsNone(plan.previous_manifest_digest)
        self.assertEqual(plan.input_event_count, 2)
        self.assertEqual(plan.deduplicated_event_count, 0)
        self.assertEqual(plan.new_event_count, 2)
        self.assertEqual(len(plan.artifacts), 3)
        artifacts = {
            artifact.relative_path: artifact
            for artifact in plan.artifacts
        }
        part = next(
            artifact
            for artifact in plan.artifacts
            if "/part-" in artifact.relative_path
        )
        index = next(
            artifact
            for artifact in plan.artifacts
            if "/index-" in artifact.relative_path
        )
        manifest = next(
            artifact
            for artifact in plan.artifacts
            if "/manifest-" in artifact.relative_path
        )
        self.assertEqual(part.schema_id, PUBLIC_RUN_EVENT_SCHEMA)
        self.assertEqual(index.schema_id, INDEX_ENTRY_SCHEMA)
        self.assertEqual(
            part.serialization,
            JSONL_SERIALIZATION,
        )
        self.assertEqual(
            index.serialization,
            JSONL_SERIALIZATION,
        )
        self.assertTrue(part.payload.endswith(b"\n"))
        self.assertTrue(index.payload.endswith(b"\n"))
        self.assertNotIn(b"\r", part.payload)
        self.assertNotIn(b"\r", index.payload)
        self.assertEqual(manifest.schema_id, DAILY_MANIFEST_SCHEMA)
        self.assertEqual(manifest.serialization, OBJECT_SERIALIZATION)
        self.assertFalse(manifest.payload.endswith(b"\n"))
        parsed_manifest = parse_json_bytes(manifest.payload)
        self.assertEqual(
            canonicalize_object(parsed_manifest),
            manifest.payload,
        )
        self.assertEqual(
            parsed_manifest["parts"][0]["retention_not_before"],
            "2027-07-23T00:00:00.000000Z",
        )
        self.assertEqual(
            parsed_manifest["active_shard_bytes"],
            len(part.payload),
        )
        self.assertEqual(
            parsed_manifest["retained_index_bytes"],
            len(index.payload),
        )
        validate_auto_instance(
            self.contract,
            parsed_manifest,
            DAILY_MANIFEST_SCHEMA,
            expected_bundle_digest=CANDIDATE_DIGEST,
        )
        self.assertEqual(
            set(artifacts),
            {
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/part-0001.jsonl",
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/index-0001.jsonl",
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/manifest-0001.json",
            },
        )

    def test_partitioning_keeps_part_and_index_one_to_one(self) -> None:
        sample_raw = canonicalize_object(self.first) + b"\n"
        writer = DailyRunShardWriter(
            self.contract,
            CANDIDATE_DIGEST,
            partition_byte_limit=len(sample_raw) + 32,
        )
        plan = writer.plan(
            [self.first, self.second],
            manifest_uid=uid("drm", 1),
            auto_transaction_uid=uid("atx", 1),
            publication_transaction_at=self.published,
        )
        parts = plan.manifest["parts"]
        self.assertEqual(len(parts), 2)
        self.assertEqual(
            [item["part_number"] for item in parts],
            [1, 2],
        )
        self.assertTrue(
            all(
                item["record_count"] == item["index_record_count"] == 1
                for item in parts
            )
        )

    def test_reader_closes_tree_and_append_deduplicates(self) -> None:
        first_plan = self.plan([self.first])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plan(root, first_plan)
            previous = DailyRunTreeReader(
                root,
                self.contract,
                CANDIDATE_DIGEST,
            ).load("2026-07-23")
            correction = event(
                3,
                "2026-07-22T23:45:00.000000Z",
                supersedes=self.first,
            )
            second_plan = self.plan(
                [self.first, correction],
                previous=previous,
                manifest_uid=uid("drm", 2),
                auto_transaction_uid=uid("atx", 2),
                publication_transaction_at=(
                    self.published + dt.timedelta(hours=1)
                ),
            )
            self.assertEqual(second_plan.manifest_revision, 2)
            self.assertEqual(second_plan.deduplicated_event_count, 1)
            self.assertEqual(second_plan.new_event_count, 1)
            self.assertEqual(
                second_plan.previous_manifest_digest,
                first_plan.manifest["manifest_digest"],
            )
            self.assertEqual(
                second_plan.manifest["parts"][0],
                first_plan.manifest["parts"][0],
            )
            write_plan(root, second_plan)
            observed = DailyRunTreeReader(
                root,
                self.contract,
                CANDIDATE_DIGEST,
            ).load("2026-07-23")
            self.assertEqual(observed.manifest["manifest_revision"], 2)
            self.assertEqual(len(observed.index_entries), 2)
            self.assertEqual(
                observed.event_digests[correction["event_uid"]],
                correction["event_digest"],
            )

    def test_late_append_and_uid_conflict_fail_closed(self) -> None:
        first_plan = self.plan([self.second])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plan(root, first_plan)
            previous = DailyRunTreeReader(
                root,
                self.contract,
                CANDIDATE_DIGEST,
            ).load("2026-07-23")
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "RUN_LOG_APPEND_ORDER_VIOLATION",
            ):
                self.plan(
                    [self.first],
                    previous=previous,
                    publication_transaction_at=(
                        self.published + dt.timedelta(hours=1)
                    ),
                )
            conflicting = dict(self.second)
            conflicting["run_status"] = "FAILED"
            conflicting["event_digest"] = "0" * 64
            conflicting = canonical_with_digest(
                conflicting,
                "event_digest",
            )
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "RUN_LOG_EXISTING_EVENT_UID_DIGEST_CONFLICT",
            ):
                self.plan(
                    [conflicting],
                    previous=previous,
                    publication_transaction_at=(
                        self.published + dt.timedelta(hours=1)
                    ),
                )

    def test_reader_rejects_symlinked_artifact(self) -> None:
        plan = self.plan([self.first])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_plan(root, plan)
            index = root / (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/index-0001.jsonl"
            )
            payload = index.read_bytes()
            replacement = root / "outside.jsonl"
            replacement.write_bytes(payload)
            index.unlink()
            os.symlink(
                os.path.relpath(replacement, index.parent),
                index,
            )
            with self.assertRaisesRegex(
                AutoRuntimeError,
                "RUN_LOG_TREE_FILE_NOT_REGULAR",
            ):
                DailyRunTreeReader(
                    root,
                    self.contract,
                    CANDIDATE_DIGEST,
                ).load("2026-07-23")


if __name__ == "__main__":
    unittest.main()
