from __future__ import annotations

import copy
import datetime as dt
import hashlib
import inspect
import unittest
from typing import Dict, Optional
from unittest import mock

from CodexSkills.governance.retention.public_safe_queue import (
    MAX_SHARD_BYTES,
    PublicSafeQueueError,
    evaluate_public_safe_queue,
    validate_lifecycle_plan,
    validate_remote_readback_evidence,
)
from CodexSkills.governance.tools import (
    build_public_safe_queue_lifecycle as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
BUNDLE = builder.CANDIDATE_BUNDLE_DIGEST
EVENT_SCHEMA = builder.PUBLIC_RUN_EVENT_SCHEMA_ID
QUEUE_SCHEMA = builder.QUEUE_ENVELOPE_SCHEMA_ID
EXPECTED_HEAD = "sha1:" + ("a" * 40)
OBSERVED_HEAD = "sha1:" + ("b" * 40)
EVENT_UID_1 = "evt_01ARZ3NDEKTSV4RRFFQ69G5FAV"
EVENT_UID_2 = "evt_01ARZ3NDEKTSV4RRFFQ69G5FAW"
RUN_UID_1 = "run_01ARZ3NDEKTSV4RRFFQ69G5FAX"
RUN_UID_2 = "run_01ARZ3NDEKTSV4RRFFQ69G5FAY"
ENVELOPE_UID = "env_01ARZ3NDEKTSV4RRFFQ69G5FAZ"
TRANSACTION_UID = "atx_01ARZ3NDEKTSV4RRFFQ69G5FB0"
OBSERVATION_UID = "qob_01ARZ3NDEKTSV4RRFFQ69G5FB1"
READBACK_UID = "qrr_01ARZ3NDEKTSV4RRFFQ69G5FB2"
PLAN_UID = "qlp_01ARZ3NDEKTSV4RRFFQ69G5FB3"
PART_PATH = (
    "OpenAIDatabase/data/run_logs/skills_runs/"
    "2026/07/23/part-0001.jsonl"
)
OCCURRED_1 = "2026-07-22T14:00:00.000000Z"
OCCURRED_2 = "2026-07-22T14:05:00.000000Z"
SEALED_AT = "2026-07-22T14:10:00.000000Z"
READBACK_AT = "2026-07-22T14:30:00.000000Z"
OBSERVED_AT = "2026-07-22T15:00:00.000000Z"


def _digest(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _event(
    *,
    event_uid: str = EVENT_UID_1,
    run_uid: str = RUN_UID_1,
    occurred_at: str = OCCURRED_1,
) -> dict:
    value = {
        "schema_version": EVENT_SCHEMA,
        "protocol_revision": PROTOCOL,
        "bundle_digest": BUNDLE,
        "event_uid": event_uid,
        "run_uid": run_uid,
        "event_type": "RUN_OBSERVED",
        "occurred_at": occurred_at,
        "surface_class": "CODEX_AUTOMATION",
        "actor_role": "AUTOMATION",
        "adapter_id": "run-observer-adapter",
        "adapter_version": "2.0.0",
        "adapter_schema_digest": _digest("adapter-schema"),
        "mapping_policy_id": (
            "urn:linzecolin:agentdatabase:skillops:policy:run-mapping:v1"
        ),
        "mapping_policy_digest": _digest("mapping-policy"),
        "trigger_kind": "SCHEDULED",
        "run_status": "SUCCESS",
        "model_ref": "gpt-5-6-sol",
        "reasoning_effort": "ULTRA",
        "metrics": {
            "duration_ms": 1000,
            "input_tokens": None,
            "output_tokens": None,
            "token_usage_status": "UNAVAILABLE",
            "tool_call_count": 1,
        },
        "binding_state": "UNKNOWN",
        "unknown_reason_code": "MAPPING_NOT_PROVABLE",
        "redaction": {
            "omitted_category_codes": [],
            "policy_snapshot_digest": _digest(
                "public-value-policy"
            ),
            "post_serialization_scan_passed": True,
            "unknown_fields_dropped": 0,
        },
        "immutable": True,
        "event_digest": "0" * 64,
    }
    value["event_digest"] = canonical_digest(
        value,
        "/event_digest",
    )
    return value


def _envelope(
    event: dict,
    *,
    state: str = "READY",
    path: str = PART_PATH,
) -> dict:
    value = {
        "schema_version": QUEUE_SCHEMA,
        "protocol_revision": PROTOCOL,
        "bundle_digest": BUNDLE,
        "envelope_uid": ENVELOPE_UID,
        "auto_transaction_uid": TRANSACTION_UID,
        "lane": "RUN_LOG",
        "artifact_schema_id": EVENT_SCHEMA,
        "artifact_uid": event["event_uid"],
        "artifact_digest": event["event_digest"],
        "artifact_repo_path": path,
        "queue_state": state,
        "sealed_at": SEALED_AT,
        "retry_count": 0,
        "envelope_digest": "0" * 64,
    }
    value["envelope_digest"] = canonical_digest(
        value,
        "/envelope_digest",
    )
    return value


class MemoryRemoteReader:
    def __init__(
        self,
        *,
        head: str = OBSERVED_HEAD,
        blobs: Optional[Dict[str, bytes]] = None,
        fail_ref: bool = False,
        fail_blob: bool = False,
    ) -> None:
        self.head = head
        self.blobs = blobs or {}
        self.fail_ref = fail_ref
        self.fail_blob = fail_blob
        self.calls: list[tuple[str, ...]] = []

    def resolve_remote_head(
        self,
        remote_name: str,
        remote_ref: str,
    ) -> str:
        self.calls.append(("resolve", remote_name, remote_ref))
        if self.fail_ref:
            raise OSError("synthetic remote ref failure")
        return self.head

    def read_blob(
        self,
        verified_git_object_id: str,
        artifact_repo_path: str,
    ) -> bytes:
        self.calls.append(
            ("blob", verified_git_object_id, artifact_repo_path)
        )
        if self.fail_blob:
            raise OSError("synthetic remote blob failure")
        return self.blobs[artifact_repo_path]


class PublicSafeQueueLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = builder.trusted_contract()

    def evaluate(
        self,
        event: dict,
        envelope: dict,
        *,
        reader: Optional[MemoryRemoteReader] = None,
        expected_head: Optional[str] = None,
        readback_uid: Optional[str] = None,
        readback_at: Optional[str] = None,
        observed_at: str = OBSERVED_AT,
        artifact_bytes: Optional[bytes] = None,
    ):
        return evaluate_public_safe_queue(
            self.contract,
            envelope=envelope,
            artifact_bytes=(
                canonicalize_object(event)
                if artifact_bytes is None
                else artifact_bytes
            ),
            observation_uid=OBSERVATION_UID,
            plan_uid=PLAN_UID,
            observed_at=observed_at,
            expected_bundle_digest=BUNDLE,
            remote_reader=reader,
            expected_remote_head=expected_head,
            readback_uid=readback_uid,
            readback_at=readback_at,
        )

    @staticmethod
    def proof_args(reader: MemoryRemoteReader) -> dict:
        return {
            "reader": reader,
            "expected_head": EXPECTED_HEAD,
            "readback_uid": READBACK_UID,
            "readback_at": READBACK_AT,
        }

    def test_01_builder_is_byte_equivalent_and_trust_is_exact(self) -> None:
        builder._check()
        readiness = builder.build_readiness()
        self.assertEqual(
            readiness["source_trust"]["m061_predecessor"][
                "verified_git_object_id"
            ],
            builder.M061_GIT_OBJECT,
        )
        self.assertEqual(
            readiness["public_safe_queue_contract"][
                "payload_contains_raw_or_private_fields"
            ],
            False,
        )
        self.assertFalse(
            readiness["public_safe_queue_contract"][
                "caller_boolean_trusted"
            ]
        )
        self.assertEqual(
            readiness["next_phase"],
            "MECHANISM_GIT_ACTIVE_TREE_365D_POLICY",
        )
        parameters = inspect.signature(
            evaluate_public_safe_queue
        ).parameters
        self.assertNotIn("remote_readback_verified", parameters)

    def test_02_ready_without_remote_proof_is_retained(self) -> None:
        event = _event()
        envelope = _envelope(event)
        before_event = copy.deepcopy(event)
        before_envelope = copy.deepcopy(envelope)
        result = self.evaluate(event, envelope)
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        plan = parse_json_bytes(result.canonical_plan_bytes)
        self.assertEqual(result.next_queue_state, "READY")
        self.assertTrue(result.queue_retention_required)
        self.assertIsNone(result.canonical_readback_bytes)
        self.assertEqual(plan["decision"], "RETAIN_READY")
        self.assertFalse(plan["settlement_eligible"])
        self.assertTrue(plan["queue_retention_required"])
        self.assertEqual(
            observation["raw_or_private_field_count"],
            0,
        )
        self.assertFalse(
            observation["physical_queue_path_consumed"]
        )
        self.assertEqual(event, before_event)
        self.assertEqual(envelope, before_envelope)

    def test_03_exact_remote_jsonl_inclusion_allows_settlement(self) -> None:
        first = _event()
        second = _event(
            event_uid=EVENT_UID_2,
            run_uid=RUN_UID_2,
            occurred_at=OCCURRED_2,
        )
        shard = (
            canonicalize_object(first)
            + b"\n"
            + canonicalize_object(second)
            + b"\n"
        )
        reader = MemoryRemoteReader(blobs={PART_PATH: shard})
        result = self.evaluate(
            second,
            _envelope(second),
            **self.proof_args(reader),
        )
        readback = parse_json_bytes(
            result.canonical_readback_bytes
        )
        plan = parse_json_bytes(result.canonical_plan_bytes)
        self.assertEqual(
            reader.calls,
            [
                ("resolve", "origin", "refs/heads/main"),
                ("blob", OBSERVED_HEAD, PART_PATH),
            ],
        )
        self.assertEqual(readback["line_number"], 2)
        self.assertEqual(readback["record_count"], 2)
        self.assertEqual(
            readback["shard_digest"],
            hashlib.sha256(shard).hexdigest(),
        )
        self.assertFalse(readback["caller_boolean_trusted"])
        self.assertEqual(
            plan["decision"],
            "ELIGIBLE_TO_MARK_SETTLED",
        )
        self.assertEqual(result.next_queue_state, "SETTLED")
        self.assertFalse(result.queue_retention_required)
        self.assertFalse(
            plan["queue_content_delete_authority_granted"]
        )
        self.assertFalse(
            plan["watermark_advance_authority_granted"]
        )

    def test_04_settled_requires_and_can_reconfirm_exact_proof(self) -> None:
        event = _event()
        envelope = _envelope(event, state="SETTLED")
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_SETTLED_REQUIRES_REMOTE_PROOF",
        ):
            self.evaluate(event, envelope)
        shard = canonicalize_object(event) + b"\n"
        reader = MemoryRemoteReader(blobs={PART_PATH: shard})
        result = self.evaluate(
            event,
            envelope,
            **self.proof_args(reader),
        )
        plan = parse_json_bytes(result.canonical_plan_bytes)
        self.assertEqual(plan["decision"], "CONFIRM_SETTLED")
        self.assertEqual(result.next_queue_state, "SETTLED")

    def test_05_quarantined_is_retained_and_never_settled(self) -> None:
        event = _event()
        envelope = _envelope(event, state="QUARANTINED")
        result = self.evaluate(event, envelope)
        self.assertEqual(result.next_queue_state, "QUARANTINED")
        self.assertTrue(result.queue_retention_required)
        reader = MemoryRemoteReader(
            blobs={PART_PATH: canonicalize_object(event) + b"\n"}
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_QUARANTINED_NOT_SETTLEABLE",
        ):
            self.evaluate(
                event,
                envelope,
                **self.proof_args(reader),
            )

    def test_06_raw_or_private_fields_are_structurally_rejected(self) -> None:
        event = _event()
        envelope = _envelope(event)
        private_event = copy.deepcopy(event)
        private_event["raw"] = "not-public"
        private_event["event_digest"] = canonical_digest(
            private_event,
            "/event_digest",
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_EVENT_INVALID",
        ):
            self.evaluate(private_event, _envelope(private_event))
        private_envelope = copy.deepcopy(envelope)
        private_envelope["prompt"] = "not-public"
        private_envelope["envelope_digest"] = canonical_digest(
            private_envelope,
            "/envelope_digest",
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_ENVELOPE_INVALID",
        ):
            self.evaluate(event, private_envelope)

    def test_07_envelope_event_binding_is_exact(self) -> None:
        event = _event()
        for field, value in (
            ("lane", "REGISTRY"),
            ("artifact_schema_id", builder.READBACK_SCHEMA_ID),
            ("artifact_uid", EVENT_UID_2),
            ("artifact_digest", _digest("wrong-event")),
            ("bundle_digest", _digest("wrong-bundle")),
        ):
            with self.subTest(field=field):
                envelope = _envelope(event)
                envelope[field] = value
                envelope["envelope_digest"] = canonical_digest(
                    envelope,
                    "/envelope_digest",
                )
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(event, envelope)

    def test_08_path_shape_calendar_date_and_sydney_day_are_exact(self) -> None:
        event = _event()
        invalid_paths = (
            "../part-0001.jsonl",
            (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/02/30/part-0001.jsonl"
            ),
            (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/22/part-0001.jsonl"
            ),
            (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/part-0000.jsonl"
            ),
        )
        for path in invalid_paths:
            with self.subTest(path=path):
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(event, _envelope(event, path=path))

    def test_09_remote_head_must_be_valid_and_advanced(self) -> None:
        event = _event()
        shard = canonicalize_object(event) + b"\n"
        for head, expected in (
            (EXPECTED_HEAD, EXPECTED_HEAD),
            ("not-a-git-object", EXPECTED_HEAD),
            ("sha256:" + ("b" * 64), EXPECTED_HEAD),
            (OBSERVED_HEAD, "not-a-git-object"),
        ):
            with self.subTest(head=head, expected=expected):
                reader = MemoryRemoteReader(
                    head=head,
                    blobs={PART_PATH: shard},
                )
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(
                        event,
                        _envelope(event),
                        reader=reader,
                        expected_head=expected,
                        readback_uid=READBACK_UID,
                        readback_at=READBACK_AT,
                    )
                self.assertFalse(
                    any(call[0] == "blob" for call in reader.calls)
                )

    def test_10_remote_jsonl_framing_and_all_records_are_validated(self) -> None:
        event = _event()
        malformed_other = canonicalize_object(
            _event(
                event_uid=EVENT_UID_2,
                run_uid=RUN_UID_2,
                occurred_at=OCCURRED_2,
            )
        )[:-1] + b" }"
        invalid_shards = (
            canonicalize_object(event),
            b"\xef\xbb\xbf" + canonicalize_object(event) + b"\n",
            canonicalize_object(event) + b"\r\n",
            canonicalize_object(event) + b"\n\n",
            canonicalize_object(event) + b"\n" + malformed_other + b"\n",
            b"x" * (MAX_SHARD_BYTES + 1),
        )
        for shard in invalid_shards:
            with self.subTest(length=len(shard)):
                reader = MemoryRemoteReader(blobs={PART_PATH: shard})
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(
                        event,
                        _envelope(event),
                        **self.proof_args(reader),
                    )

    def test_11_duplicate_remote_uid_or_digest_fails_closed(self) -> None:
        event = _event()
        raw = canonicalize_object(event)
        reader = MemoryRemoteReader(
            blobs={PART_PATH: raw + b"\n" + raw + b"\n"}
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_REMOTE_RECORD_DUPLICATE",
        ):
            self.evaluate(
                event,
                _envelope(event),
                **self.proof_args(reader),
            )

    def test_12_missing_or_different_remote_artifact_fails_closed(self) -> None:
        event = _event()
        other = _event(
            event_uid=EVENT_UID_2,
            run_uid=RUN_UID_2,
            occurred_at=OCCURRED_2,
        )
        reader = MemoryRemoteReader(
            blobs={PART_PATH: canonicalize_object(other) + b"\n"}
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_REMOTE_ARTIFACT_NOT_UNIQUE",
        ):
            self.evaluate(
                event,
                _envelope(event),
                **self.proof_args(reader),
            )
        changed = copy.deepcopy(event)
        changed["metrics"]["duration_ms"] = 2000
        changed["event_digest"] = canonical_digest(
            changed,
            "/event_digest",
        )
        reader = MemoryRemoteReader(
            blobs={PART_PATH: canonicalize_object(changed) + b"\n"}
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_REMOTE_ARTIFACT_BYTES_MISMATCH",
        ):
            self.evaluate(
                event,
                _envelope(event),
                **self.proof_args(reader),
            )

    def test_13_reader_failures_and_partial_arguments_fail_closed(self) -> None:
        event = _event()
        envelope = _envelope(event)
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_REMOTE_ARGUMENTS_WITHOUT_READER",
        ):
            self.evaluate(
                event,
                envelope,
                expected_head=EXPECTED_HEAD,
            )
        for reader in (
            MemoryRemoteReader(fail_ref=True),
            MemoryRemoteReader(fail_blob=True),
        ):
            with self.subTest(reader=reader):
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(
                        event,
                        envelope,
                        **self.proof_args(reader),
                    )

    def test_14_clock_order_is_strict(self) -> None:
        event = _event()
        envelope = _envelope(event)
        reader = MemoryRemoteReader(
            blobs={
                PART_PATH: canonicalize_object(event) + b"\n",
            }
        )
        for observed_at, readback_at in (
            ("2026-07-22T14:09:59.000000Z", None),
            (OBSERVED_AT, "2026-07-22T14:09:59.000000Z"),
            (OBSERVED_AT, "2026-07-22T15:00:01.000000Z"),
        ):
            with self.subTest(
                observed_at=observed_at,
                readback_at=readback_at,
            ):
                kwargs = {}
                if readback_at is not None:
                    kwargs = {
                        "reader": reader,
                        "expected_head": EXPECTED_HEAD,
                        "readback_uid": READBACK_UID,
                        "readback_at": readback_at,
                    }
                with self.assertRaises(PublicSafeQueueError):
                    self.evaluate(
                        event,
                        envelope,
                        observed_at=observed_at,
                        **kwargs,
                    )

    def test_15_predecessor_blob_drift_is_not_trusted(self) -> None:
        original = builder._git_blob

        def drifted(object_id: str, path: str) -> bytes:
            raw = original(object_id, path)
            if (
                object_id == builder.M061_GIT_OBJECT
                and path == builder.M061_READINESS_PATH
            ):
                return raw + b" "
            return raw

        with mock.patch.object(
            builder,
            "_git_blob",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                builder.PublicSafeQueueBuildError,
                "M062_M061_PREDECESSOR_TRUST_MISMATCH",
            ):
                builder.build_readiness()

    def test_16_evidence_state_machine_cannot_be_self_consistently_forged(
        self,
    ) -> None:
        event = _event()
        reader = MemoryRemoteReader(
            blobs={
                PART_PATH: canonicalize_object(event) + b"\n",
            }
        )
        result = self.evaluate(
            event,
            _envelope(event),
            **self.proof_args(reader),
        )
        readback = parse_json_bytes(
            result.canonical_readback_bytes
        )
        forged_readback = copy.deepcopy(readback)
        forged_readback["observed_remote_head"] = EXPECTED_HEAD
        forged_readback["evidence_bundle_digest"] = canonical_digest(
            forged_readback,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            PublicSafeQueueError,
            "PUBLIC_SAFE_QUEUE_REMOTE_HEAD_NOT_ADVANCED",
        ):
            validate_remote_readback_evidence(
                self.contract,
                forged_readback,
                expected_bundle_digest=BUNDLE,
            )

        plan = parse_json_bytes(result.canonical_plan_bytes)
        forged_plan = copy.deepcopy(plan)
        forged_plan["decision"] = "RETAIN_READY"
        forged_plan["evidence_bundle_digest"] = canonical_digest(
            forged_plan,
            "/evidence_bundle_digest",
        )
        with self.assertRaises(PublicSafeQueueError):
            validate_lifecycle_plan(
                self.contract,
                forged_plan,
                expected_bundle_digest=BUNDLE,
                expected_observation_digest=(
                    result.observation_digest
                ),
                expected_readback_digest=result.readback_digest,
            )


if __name__ == "__main__":
    unittest.main()
