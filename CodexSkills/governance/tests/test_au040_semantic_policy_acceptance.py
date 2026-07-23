"""Regression gates for Mechanism AU-040 semantic policy acceptance."""

from __future__ import annotations

import copy
import hashlib
import json
import sys
import unittest
from pathlib import Path


GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = GOVERNANCE_DIR.parents[1]
TOOLS_DIR = GOVERNANCE_DIR / "tools"
sys.path.insert(0, str(TOOLS_DIR))
sys.path.insert(0, str(REPO_ROOT))

from build_au040_semantic_acceptance import (  # noqa: E402
    AUTO_SCHEMA_CONTRACTS,
    CURRENT_CANDIDATE_BUNDLE_DIGEST,
    PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
    PUBLIC_VALUE_POLICY_V1,
    PUBLIC_VALUE_POLICY_V2,
    RETENTION_POLICY_V2,
    RETENTION_POLICY_V3,
    materialize,
    semantic_policy_acceptance,
)
from canonical_json import canonical_digest, canonicalize_object  # noqa: E402
from validate_au040_semantic_acceptance import (  # noqa: E402
    ContractError,
    current_tree_prune_eligible,
    load_au040_acceptance,
    prune_deadline_breached,
    validate_daily_manifest_semantics,
    validate_manifest_revision_chain,
    validate_part_index_manifest_closure,
    validate_public_value_v2,
    validate_publication_artifact_set,
    validate_prune_transaction_closure,
    validate_retention_receipt_semantics,
    validate_shard_transaction_closure,
)
from CodexSkills.registry.auto.tools.validate_transport_draft import (  # noqa: E402
    DAILY_MANIFEST_ID,
    INDEX_ENTRY_ID,
    JSONL_SERIALIZATION,
    OBJECT_SERIALIZATION,
    RETENTION_V3_ID,
    _digest,
    _finalize,
    _uid,
    daily_manifest_fixture,
    discover_required_allowlist_additions,
    index_entry_fixture,
    publication_manifest_fixture,
    retention_receipt_fixture,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
PUBLIC_RUN_EVENT_ID = (
    "urn:linzecolin:agentdatabase:skillops:schema:public-run-event:v2"
)
FIRST_PUBLISHED = "2026-07-22T16:00:00.000000Z"
RETENTION_ANCHOR = "2027-07-22T16:00:00.000000Z"


def _seal(value: dict, pointer: str) -> dict:
    result = copy.deepcopy(value)
    field = pointer.removeprefix("/")
    result[field] = "0" * 64
    result[field] = canonical_digest(result, pointer)
    return result


def _event(number: str, occurred_at: str) -> dict:
    value = {
        "schema_version": PUBLIC_RUN_EVENT_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
        "event_uid": _uid("evt", number),
        "run_uid": _uid("run", number),
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
            "policy_snapshot_digest": _digest("public-value-policy"),
            "post_serialization_scan_passed": True,
            "unknown_fields_dropped": 0,
        },
        "immutable": True,
    }
    return _seal(value, "/event_digest")


def _index(event: dict, line_number: int) -> dict:
    return _seal(
        {
            "schema_version": INDEX_ENTRY_ID,
            "protocol_revision": PROTOCOL,
            "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
            "event_uid": event["event_uid"],
            "event_digest": event["event_digest"],
            "event_type": event["event_type"],
            "occurred_at": event["occurred_at"],
            "part_number": 1,
            "line_number": line_number,
            "first_published_at": FIRST_PUBLISHED,
        },
        "/index_entry_digest",
    )


def _jsonl(rows: list[dict]) -> bytes:
    return b"".join(canonicalize_object(row) + b"\n" for row in rows)


def _active_manifest() -> tuple[dict, bytes, bytes]:
    events = [
        _event("1", "2026-07-22T14:00:00.000000Z"),
        _event("2", "2026-07-22T15:00:00.000000Z"),
    ]
    indexes = [_index(event, number) for number, event in enumerate(events, 1)]
    part_bytes = _jsonl(events)
    index_bytes = _jsonl(indexes)
    part = {
        "part_number": 1,
        "shard_name": "part-0001.jsonl",
        "state": "ACTIVE",
        "shard_digest": hashlib.sha256(part_bytes).hexdigest(),
        "shard_bytes": len(part_bytes),
        "record_count": 2,
        "index_name": "index-0001.jsonl",
        "index_digest": hashlib.sha256(index_bytes).hexdigest(),
        "index_bytes": len(index_bytes),
        "index_record_count": 2,
        "first_event_uid": events[0]["event_uid"],
        "first_event_digest": events[0]["event_digest"],
        "first_occurred_at": events[0]["occurred_at"],
        "last_event_uid": events[-1]["event_uid"],
        "last_event_digest": events[-1]["event_digest"],
        "last_occurred_at": events[-1]["occurred_at"],
        "first_published_at": FIRST_PUBLISHED,
        "retention_not_before": RETENTION_ANCHOR,
    }
    manifest = {
        "schema_version": DAILY_MANIFEST_ID,
        "protocol_revision": PROTOCOL,
        "bundle_digest": CURRENT_CANDIDATE_BUNDLE_DIGEST,
        "manifest_uid": _uid("drm", "1"),
        "local_date": "2026-07-23",
        "timezone": "Australia/Sydney",
        "record_schema_id": PUBLIC_RUN_EVENT_ID,
        "artifact_serialization": JSONL_SERIALIZATION,
        "max_part_bytes": 20 * 1024 * 1024,
        "manifest_revision": 1,
        "previous_manifest_digest": None,
        "auto_transaction_uid": _uid("atx", "1"),
        "publication_transaction_at": FIRST_PUBLISHED,
        "max_part_number": 1,
        "total_part_count": 1,
        "active_part_count": 1,
        "pruned_part_count": 0,
        "active_shard_bytes": len(part_bytes),
        "active_record_count": 2,
        "retained_index_bytes": len(index_bytes),
        "retained_index_record_count": 2,
        "parts": [part],
    }
    return _seal(manifest, "/manifest_digest"), part_bytes, index_bytes


def _pruned_revision(prior: dict) -> dict:
    current = copy.deepcopy(prior)
    current["manifest_uid"] = _uid("drm", "2")
    current["manifest_revision"] = 2
    current["previous_manifest_digest"] = prior["manifest_digest"]
    current["auto_transaction_uid"] = _uid("atx", "2")
    current["publication_transaction_at"] = (
        "2027-07-22T19:00:00.000000Z"
    )
    current["active_part_count"] = 0
    current["pruned_part_count"] = 1
    current["active_shard_bytes"] = 0
    current["active_record_count"] = 0
    part = current["parts"][0]
    receipt = retention_receipt_fixture()
    part["state"] = "PRUNED"
    part["retention_receipt_path"] = (
        "OpenAIDatabase/data/run_logs/skills_runs/"
        "2026/07/23/retention-receipt-0001.json"
    )
    part["retention_receipt_uid"] = receipt["receipt_uid"]
    part["retention_receipt_digest"] = receipt["receipt_digest"]
    part["pruned_at"] = "2027-07-22T18:00:00.000000Z"
    return _seal(current, "/manifest_digest")


def _publication_with_receipt() -> dict:
    value = publication_manifest_fixture()
    artifacts = value["lane_manifests"][0]["artifacts"]
    artifacts.append(
        {
            "artifact_uid": _uid("rtr", "5"),
            "artifact_operation": "PUT",
            "artifact_schema_id": RETENTION_V3_ID,
            "artifact_repo_path": (
                "OpenAIDatabase/data/run_logs/skills_runs/"
                "2026/07/23/retention-receipt-0001.json"
            ),
            "artifact_serialization": OBJECT_SERIALIZATION,
            "artifact_digest": _digest("retention-receipt-put"),
            "artifact_bytes": 2048,
            "artifact_record_count": 1,
        }
    )
    artifacts.sort(
        key=lambda item: (item["artifact_repo_path"], item["artifact_uid"])
    )
    value["lane_manifests"][0]["artifact_count"] = len(artifacts)
    return _seal(value, "/manifest_digest")


def _put_descriptor(
    uid: str,
    path: str,
    schema_id: str,
    serialization: str,
    raw: bytes,
    record_count: int,
) -> dict:
    return {
        "artifact_uid": uid,
        "artifact_operation": "PUT",
        "artifact_schema_id": schema_id,
        "artifact_repo_path": path,
        "artifact_serialization": serialization,
        "artifact_digest": hashlib.sha256(raw).hexdigest(),
        "artifact_bytes": len(raw),
        "artifact_record_count": record_count,
    }


def _publication(
    artifacts: list[dict],
    *,
    transaction_uid: str,
    created_at: str,
) -> dict:
    value = publication_manifest_fixture()
    value["auto_transaction_uid"] = transaction_uid
    value["created_at"] = created_at
    artifacts.sort(
        key=lambda item: (item["artifact_repo_path"], item["artifact_uid"])
    )
    value["lane_manifests"][0]["artifacts"] = artifacts
    value["lane_manifests"][0]["artifact_count"] = len(artifacts)
    return _seal(value, "/manifest_digest")


class AU040SemanticPolicyAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_au040_acceptance()

    def test_builder_and_interface_are_byte_equivalent_and_non_active(self) -> None:
        materialize(check=True)
        interface = semantic_policy_acceptance()
        self.assertEqual(
            interface["status"],
            "DRAFT_NON_ACTIVE_SEMANTIC_POLICY_ACCEPTED",
        )
        self.assertFalse(interface["repository_bound"])
        self.assertTrue(interface["bundle_materialization_forbidden"])
        self.assertFalse(interface["canonical_publication_permitted"])
        self.assertEqual(interface["target_shared_set"]["target_schema_count"], 31)
        self.assertEqual(interface["target_shared_set"]["target_policy_count"], 5)
        self.assertEqual(len(self.contract.bundle.schemas), 31)
        self.assertEqual(len(self.contract.bundle.policies), 5)
        self.assertEqual(
            {
                (
                    entry["id"],
                    entry["schema_sha256"],
                    entry["self_digest_pointer"],
                )
                for entry in interface["accepted_auto_transport_schemas"]
            },
            set(AUTO_SCHEMA_CONTRACTS),
        )

    def test_public_value_v2_is_exact_versioned_ten_field_delta(self) -> None:
        current = self.contract.transport.current_candidate.policies[
            PUBLIC_VALUE_POLICY_V1
        ]
        discovered = discover_required_allowlist_additions(
            [
                daily_manifest_fixture(),
                index_entry_fixture(),
                publication_manifest_fixture(),
                retention_receipt_fixture(),
            ],
            self.contract.transport.current_candidate.policies,
        )
        self.assertEqual(discovered, list(PUBLIC_VALUE_ALLOWLIST_ADDITIONS))
        old = set(current["allowed_high_entropy_field_names"])
        new = set(
            self.contract.public_value_policy[
                "allowed_high_entropy_field_names"
            ]
        )
        self.assertEqual(new - old, set(PUBLIC_VALUE_ALLOWLIST_ADDITIONS))
        self.assertEqual(
            self.contract.public_value_policy["policy_id"],
            PUBLIC_VALUE_POLICY_V2,
        )

    def test_public_value_v2_rejects_malformed_and_generic_digest_fields(self) -> None:
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_APPROVED_DIGEST_MALFORMED",
        ):
            validate_public_value_v2(
                self.contract,
                {"shard_digest": "not-a-sha256"},
            )
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK",
        ):
            validate_public_value_v2(
                self.contract,
                {"generic_digest": "a" * 64},
            )
        validate_public_value_v2(
            self.contract,
            {"shard_digest": "a" * 64},
        )

    def test_retention_policy_replaces_both_old_policy_contracts(self) -> None:
        target = self.contract.interface["target_shared_set"]
        self.assertEqual(
            set(target["replaced_policy_ids"]),
            {PUBLIC_VALUE_POLICY_V1, RETENTION_POLICY_V2},
        )
        self.assertEqual(
            set(target["replacement_policy_ids"]),
            {PUBLIC_VALUE_POLICY_V2, RETENTION_POLICY_V3},
        )
        self.assertEqual(
            self.contract.retention_policy[
                "sanitized_public_elapsed_seconds"
            ],
            365 * 24 * 60 * 60,
        )
        self.assertFalse(
            self.contract.retention_policy[
                "prune_deadline_hard_guarantee_claimed"
            ]
        )

    def test_exact_365_day_anchor_rejects_plus_one_microsecond(self) -> None:
        invalid = daily_manifest_fixture()
        invalid["parts"][0]["retention_not_before"] = (
            "2027-07-22T16:00:00.000001Z"
        )
        invalid = _finalize(invalid, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_RETENTION_ANCHOR_NOT_EXACT_365D",
        ):
            validate_daily_manifest_semantics(self.contract, invalid)

        invalid_receipt = retention_receipt_fixture()
        item = invalid_receipt["affected_public_artifacts"][0]
        item["retention_not_before"] = "2027-07-22T17:00:00.000001Z"
        item["prune_deadline_at"] = "2027-07-23T17:00:00.000001Z"
        invalid_receipt = _finalize(
            invalid_receipt,
            "/receipt_digest",
        )
        with self.assertRaisesRegex(
            ContractError,
            "AU040_RETENTION_ANCHOR_NOT_EXACT_365D",
        ):
            validate_retention_receipt_semantics(
                self.contract,
                invalid_receipt,
            )

    def test_retention_and_deadline_boundaries_are_strict_and_truthful(self) -> None:
        self.assertFalse(
            current_tree_prune_eligible(RETENTION_ANCHOR, RETENTION_ANCHOR)
        )
        self.assertTrue(
            current_tree_prune_eligible(
                "2027-07-22T16:00:00.000001Z",
                RETENTION_ANCHOR,
            )
        )
        self.assertFalse(
            prune_deadline_breached(
                "2027-07-23T16:00:00.000000Z",
                RETENTION_ANCHOR,
            )
        )
        self.assertTrue(
            prune_deadline_breached(
                "2027-07-23T16:00:00.000001Z",
                RETENTION_ANCHOR,
            )
        )

    def test_manifest_chain_binds_exact_predecessor_and_immutable_parts(self) -> None:
        prior, _, _ = _active_manifest()
        current = _pruned_revision(prior)
        root = (
            "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23/"
        )
        validate_manifest_revision_chain(
            self.contract,
            current,
            root + "manifest-0002.json",
            prior,
            root + "manifest-0001.json",
        )
        wrong_digest = copy.deepcopy(current)
        wrong_digest["previous_manifest_digest"] = _digest("wrong-prior")
        wrong_digest = _seal(wrong_digest, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_MANIFEST_PREDECESSOR_DIGEST_MISMATCH",
        ):
            validate_manifest_revision_chain(
                self.contract,
                wrong_digest,
                root + "manifest-0002.json",
                prior,
                root + "manifest-0001.json",
            )
        mutated = copy.deepcopy(current)
        mutated["parts"][0]["shard_digest"] = _digest("mutated-shard")
        mutated = _seal(mutated, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_MANIFEST_EXISTING_PART_MUTATED",
        ):
            validate_manifest_revision_chain(
                self.contract,
                mutated,
                root + "manifest-0002.json",
                prior,
                root + "manifest-0001.json",
            )

    def test_manifest_chain_rejects_revision_gap(self) -> None:
        prior, _, _ = _active_manifest()
        current = _pruned_revision(prior)
        current["manifest_revision"] = 3
        current = _seal(current, "/manifest_digest")
        root = "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23/"
        with self.assertRaisesRegex(
            ContractError,
            "AU040_MANIFEST_PREDECESSOR_SEQUENCE_INVALID",
        ):
            validate_manifest_revision_chain(
                self.contract,
                current,
                root + "manifest-0003.json",
                prior,
                root + "manifest-0001.json",
            )

    def test_index_event_manifest_and_physical_bytes_close_exactly(self) -> None:
        manifest, part_bytes, index_bytes = _active_manifest()
        validate_part_index_manifest_closure(
            self.contract,
            manifest,
            part_number=1,
            part_bytes=part_bytes,
            index_bytes=index_bytes,
        )
        wrong = copy.deepcopy(manifest)
        wrong["parts"][0]["first_event_digest"] = _digest("wrong-first")
        wrong = _seal(wrong, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_MANIFEST_EVENT_BOUNDARY_MISMATCH",
        ):
            validate_part_index_manifest_closure(
                self.contract,
                wrong,
                part_number=1,
                part_bytes=part_bytes,
                index_bytes=index_bytes,
            )

    def test_index_first_publication_must_match_part_anchor(self) -> None:
        manifest, part_bytes, index_bytes = _active_manifest()
        rows = [
            parse
            for parse in (
                # Parsing is strict in the validator; this reconstructs rows
                # only to create a correctly re-digested negative fixture.
                json.loads(line)
                for line in index_bytes.decode("utf-8").splitlines()
            )
        ]
        rows[0]["first_published_at"] = "2026-07-22T16:00:00.000001Z"
        rows[0] = _seal(rows[0], "/index_entry_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_INDEX_FIRST_PUBLISHED_AT_PART_MISMATCH",
        ):
            validate_part_index_manifest_closure(
                self.contract,
                manifest,
                part_number=1,
                part_bytes=part_bytes,
                index_bytes=_jsonl(rows),
            )

    def test_publication_requires_paired_part_index_manifest_and_prune_receipt(self) -> None:
        valid = _publication_with_receipt()
        validate_publication_artifact_set(self.contract, valid)

        missing_index = copy.deepcopy(valid)
        artifacts = missing_index["lane_manifests"][0]["artifacts"]
        artifacts[:] = [
            item
            for item in artifacts
            if not item["artifact_repo_path"].endswith("index-0001.jsonl")
        ]
        missing_index["lane_manifests"][0]["artifact_count"] = len(artifacts)
        missing_index = _seal(missing_index, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_PUBLICATION_PART_INDEX_PUT_SET_MISMATCH",
        ):
            validate_publication_artifact_set(self.contract, missing_index)

        missing_receipt = copy.deepcopy(valid)
        artifacts = missing_receipt["lane_manifests"][0]["artifacts"]
        artifacts[:] = [
            item
            for item in artifacts
            if "retention-receipt-" not in item["artifact_repo_path"]
        ]
        missing_receipt["lane_manifests"][0]["artifact_count"] = len(artifacts)
        missing_receipt = _seal(missing_receipt, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_PUBLICATION_PRUNE_RECEIPT_PUT_REQUIRED",
        ):
            validate_publication_artifact_set(self.contract, missing_receipt)

    def test_publication_rejects_orphan_part_and_orphan_receipt(self) -> None:
        valid = _publication_with_receipt()
        orphan_part = copy.deepcopy(valid)
        lane = orphan_part["lane_manifests"][0]
        lane["artifacts"] = [
            item
            for item in lane["artifacts"]
            if item["artifact_repo_path"].endswith("part-0001.jsonl")
        ]
        lane["artifact_count"] = 1
        orphan_part = _seal(orphan_part, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "EXACTLY_ONE_DAILY_MANIFEST_REQUIRED",
        ):
            validate_publication_artifact_set(self.contract, orphan_part)

        orphan_receipt = copy.deepcopy(valid)
        lane = orphan_receipt["lane_manifests"][0]
        lane["artifacts"] = [
            item
            for item in lane["artifacts"]
            if (
                item["artifact_repo_path"].endswith("manifest-0002.json")
                or "retention-receipt-" in item["artifact_repo_path"]
            )
        ]
        lane["artifacts"].sort(
            key=lambda item: (
                item["artifact_repo_path"],
                item["artifact_uid"],
            )
        )
        lane["artifact_count"] = len(lane["artifacts"])
        orphan_receipt = _seal(orphan_receipt, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_PUBLICATION_ORPHAN_RETENTION_RECEIPT",
        ):
            validate_publication_artifact_set(self.contract, orphan_receipt)

    def test_new_shard_transaction_closes_descriptor_bytes(self) -> None:
        manifest, part_bytes, index_bytes = _active_manifest()
        root = "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23/"
        manifest_path = root + "manifest-0001.json"
        manifest_bytes = canonicalize_object(manifest)
        publication = _publication(
            [
                _put_descriptor(
                    _uid("idx", "1"),
                    root + "index-0001.jsonl",
                    INDEX_ENTRY_ID,
                    JSONL_SERIALIZATION,
                    index_bytes,
                    2,
                ),
                _put_descriptor(
                    _uid("drm", "1"),
                    manifest_path,
                    DAILY_MANIFEST_ID,
                    OBJECT_SERIALIZATION,
                    manifest_bytes,
                    1,
                ),
                _put_descriptor(
                    _uid("evt", "1"),
                    root + "part-0001.jsonl",
                    PUBLIC_RUN_EVENT_ID,
                    JSONL_SERIALIZATION,
                    part_bytes,
                    2,
                ),
            ],
            transaction_uid=manifest["auto_transaction_uid"],
            created_at=manifest["publication_transaction_at"],
        )
        validate_shard_transaction_closure(
            self.contract,
            publication,
            manifest,
            manifest_path,
            part_number=1,
            part_bytes=part_bytes,
            index_bytes=index_bytes,
        )
        bad = copy.deepcopy(publication)
        descriptor = next(
            item
            for item in bad["lane_manifests"][0]["artifacts"]
            if item["artifact_repo_path"].endswith("part-0001.jsonl")
        )
        descriptor["artifact_digest"] = _digest("wrong-physical-part")
        bad = _seal(bad, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AU040_PUBLICATION_PUT_DESCRIPTOR_BYTES_MISMATCH",
        ):
            validate_shard_transaction_closure(
                self.contract,
                bad,
                manifest,
                manifest_path,
                part_number=1,
                part_bytes=part_bytes,
                index_bytes=index_bytes,
            )

    def test_prune_transaction_closes_delete_receipt_and_manifest(self) -> None:
        prior, _, _ = _active_manifest()
        root = "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23/"
        receipt_path = root + "retention-receipt-0001.json"
        receipt = retention_receipt_fixture()
        receipt["auto_transaction_uid"] = _uid("atx", "2")
        receipt["selected_bytes"] = prior["parts"][0]["shard_bytes"]
        receipt["affected_bytes"] = prior["parts"][0]["shard_bytes"]
        receipt["affected_public_artifacts"][0].update(
            {
                "artifact_repo_path": root + "part-0001.jsonl",
                "prior_artifact_digest": prior["parts"][0][
                    "shard_digest"
                ],
                "prior_artifact_bytes": prior["parts"][0]["shard_bytes"],
                "prior_record_count": prior["parts"][0]["record_count"],
                "first_published_at": prior["parts"][0][
                    "first_published_at"
                ],
                "retention_not_before": prior["parts"][0][
                    "retention_not_before"
                ],
                "prune_deadline_at": (
                    "2027-07-23T16:00:00.000000Z"
                ),
                "retained_index_path": root + "index-0001.jsonl",
                "retained_index_digest": prior["parts"][0][
                    "index_digest"
                ],
                "prior_daily_manifest_digest": prior["manifest_digest"],
            }
        )
        receipt = _seal(receipt, "/receipt_digest")
        current = _pruned_revision(prior)
        current["parts"][0].update(
            {
                "retention_receipt_path": receipt_path,
                "retention_receipt_uid": receipt["receipt_uid"],
                "retention_receipt_digest": receipt["receipt_digest"],
                "pruned_at": receipt["executed_at"],
            }
        )
        current = _seal(current, "/manifest_digest")
        manifest_path = root + "manifest-0002.json"
        publication = _publication(
            [
                _put_descriptor(
                    _uid("drm", "2"),
                    manifest_path,
                    DAILY_MANIFEST_ID,
                    OBJECT_SERIALIZATION,
                    canonicalize_object(current),
                    1,
                ),
                {
                    "artifact_uid": _uid("evt", "2"),
                    "artifact_operation": "DELETE",
                    "artifact_schema_id": PUBLIC_RUN_EVENT_ID,
                    "artifact_repo_path": root + "part-0001.jsonl",
                    "prior_artifact_serialization": JSONL_SERIALIZATION,
                    "prior_artifact_digest": prior["parts"][0][
                        "shard_digest"
                    ],
                    "prior_artifact_bytes": prior["parts"][0][
                        "shard_bytes"
                    ],
                    "prior_artifact_record_count": prior["parts"][0][
                        "record_count"
                    ],
                },
                _put_descriptor(
                    receipt["receipt_uid"],
                    receipt_path,
                    RETENTION_V3_ID,
                    OBJECT_SERIALIZATION,
                    canonicalize_object(receipt),
                    1,
                ),
            ],
            transaction_uid=current["auto_transaction_uid"],
            created_at=current["publication_transaction_at"],
        )
        validate_prune_transaction_closure(
            self.contract,
            publication,
            current,
            manifest_path,
            {receipt_path: receipt},
        )
        wrong = copy.deepcopy(receipt)
        wrong["affected_public_artifacts"][0][
            "prior_artifact_digest"
        ] = _digest("wrong-prior-part")
        wrong = _seal(wrong, "/receipt_digest")
        with self.assertRaisesRegex(
            ContractError,
            (
                "AU040_RETENTION_DELETE_DESCRIPTOR_MISMATCH|"
                "DAILY_MANIFEST_RETENTION|"
                "AU040_PUBLICATION_PUT_DESCRIPTOR_BYTES_MISMATCH"
            ),
        ):
            validate_prune_transaction_closure(
                self.contract,
                publication,
                current,
                manifest_path,
                {receipt_path: wrong},
            )


if __name__ == "__main__":
    unittest.main()
