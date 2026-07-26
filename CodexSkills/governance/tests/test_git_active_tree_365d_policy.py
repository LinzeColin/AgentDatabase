"""Regression gates for Mechanism M-063 Git active-tree retention."""

from __future__ import annotations

import copy
import hashlib
import inspect
import unittest
from unittest import mock

from CodexSkills.governance.retention.git_active_tree_policy import (
    GitActiveTreePolicyError,
    evaluate_git_active_tree,
    validate_daily_tree_material,
    validate_prune_plan,
    validate_prune_transition,
    validate_retention_observation,
)
from CodexSkills.governance.tests.test_au040_semantic_policy_acceptance import (
    FIRST_PUBLISHED,
    _active_manifest,
    _pruned_revision,
    _publication,
    _put_descriptor,
    _seal,
)
from CodexSkills.governance.tools import (
    build_git_active_tree_365d_policy as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)
from CodexSkills.registry.auto.tools.validate_transport_draft import (
    DAILY_MANIFEST_ID,
    JSONL_SERIALIZATION,
    OBJECT_SERIALIZATION,
    RETENTION_V3_ID,
    _digest,
    _uid,
    retention_receipt_fixture,
)


BUNDLE = builder.CANDIDATE_BUNDLE_DIGEST
ROOT = "OpenAIDatabase/data/run_logs/skills_runs/2026/07/23"
MANIFEST_1 = ROOT + "/manifest-0001.json"
MANIFEST_2 = ROOT + "/manifest-0002.json"
PART_1 = ROOT + "/part-0001.jsonl"
INDEX_1 = ROOT + "/index-0001.jsonl"
RECEIPT_1 = ROOT + "/retention-receipt-0001.json"
OBSERVATION_UID = _uid("atr", "1")
PLAN_UID = _uid("atp", "1")


def _active_tree():
    manifest, part_raw, index_raw = _final_active_manifest()
    return (
        manifest,
        {MANIFEST_1: canonicalize_object(manifest)},
        {PART_1: part_raw},
        {INDEX_1: index_raw},
        {},
    )


def _final_active_manifest():
    manifest, part_raw, index_raw = _active_manifest()
    events = [
        parse_json_bytes(line)
        for line in part_raw[:-1].split(b"\n")
    ]
    indexes = [
        parse_json_bytes(line)
        for line in index_raw[:-1].split(b"\n")
    ]
    for event in events:
        event["bundle_digest"] = BUNDLE
        sealed = _seal(event, "/event_digest")
        event.clear()
        event.update(sealed)
    for index, event in zip(indexes, events):
        index["bundle_digest"] = BUNDLE
        index["event_digest"] = event["event_digest"]
        sealed = _seal(index, "/index_entry_digest")
        index.clear()
        index.update(sealed)
    part_raw = b"".join(
        canonicalize_object(event) + b"\n" for event in events
    )
    index_raw = b"".join(
        canonicalize_object(index) + b"\n" for index in indexes
    )
    manifest["bundle_digest"] = BUNDLE
    part = manifest["parts"][0]
    part.update(
        {
            "shard_digest": hashlib.sha256(part_raw).hexdigest(),
            "shard_bytes": len(part_raw),
            "index_digest": hashlib.sha256(index_raw).hexdigest(),
            "index_bytes": len(index_raw),
            "first_event_digest": events[0]["event_digest"],
            "last_event_digest": events[-1]["event_digest"],
        }
    )
    manifest["active_shard_bytes"] = len(part_raw)
    manifest["retained_index_bytes"] = len(index_raw)
    return _seal(manifest, "/manifest_digest"), part_raw, index_raw


def _evaluate(observed_at: str):
    manifest, history, parts, indexes, receipts = _active_tree()
    result = evaluate_git_active_tree(
        GitActiveTree365DayTests.context,
        manifest_history_bytes=history,
        part_bytes=parts,
        index_bytes=indexes,
        receipt_bytes=receipts,
        observation_uid=OBSERVATION_UID,
        plan_uid=PLAN_UID,
        observed_at=observed_at,
        expected_bundle_digest=BUNDLE,
    )
    return manifest, result


def _prune_material():
    prior, part_raw, index_raw = _final_active_manifest()
    receipt = retention_receipt_fixture()
    receipt["bundle_digest"] = BUNDLE
    receipt["auto_transaction_uid"] = _uid("atx", "2")
    receipt["cutoff_at"] = prior["parts"][0]["retention_not_before"]
    receipt["selected_bytes"] = prior["parts"][0]["shard_bytes"]
    receipt["affected_bytes"] = prior["parts"][0]["shard_bytes"]
    receipt["affected_public_artifacts"][0].update(
        {
            "artifact_repo_path": PART_1,
            "prior_artifact_digest": prior["parts"][0]["shard_digest"],
            "prior_artifact_bytes": prior["parts"][0]["shard_bytes"],
            "prior_record_count": prior["parts"][0]["record_count"],
            "first_published_at": prior["parts"][0][
                "first_published_at"
            ],
            "retention_not_before": prior["parts"][0][
                "retention_not_before"
            ],
            "prune_deadline_at": "2027-07-23T16:00:00.000000Z",
            "retained_index_path": INDEX_1,
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
            "retention_receipt_path": RECEIPT_1,
            "retention_receipt_uid": receipt["receipt_uid"],
            "retention_receipt_digest": receipt["receipt_digest"],
            "pruned_at": receipt["executed_at"],
        }
    )
    current = _seal(current, "/manifest_digest")
    current_raw = canonicalize_object(current)
    receipt_raw = canonicalize_object(receipt)
    publication = _publication(
        [
            _put_descriptor(
                _uid("drm", "2"),
                MANIFEST_2,
                DAILY_MANIFEST_ID,
                OBJECT_SERIALIZATION,
                current_raw,
                1,
            ),
            {
                "artifact_uid": _uid("evt", "6"),
                "artifact_operation": "DELETE",
                "artifact_schema_id": (
                    "urn:linzecolin:agentdatabase:skillops:"
                    "schema:public-run-event:v2"
                ),
                "artifact_repo_path": PART_1,
                "prior_artifact_serialization": JSONL_SERIALIZATION,
                "prior_artifact_digest": prior["parts"][0][
                    "shard_digest"
                ],
                "prior_artifact_bytes": prior["parts"][0]["shard_bytes"],
                "prior_artifact_record_count": prior["parts"][0][
                    "record_count"
                ],
            },
            _put_descriptor(
                receipt["receipt_uid"],
                RECEIPT_1,
                RETENTION_V3_ID,
                OBJECT_SERIALIZATION,
                receipt_raw,
                1,
            ),
        ],
        transaction_uid=current["auto_transaction_uid"],
        created_at=current["publication_transaction_at"],
    )
    publication["bundle_digest"] = BUNDLE
    publication = _seal(publication, "/manifest_digest")
    return {
        "prior": prior,
        "current": current,
        "history": {
            MANIFEST_1: canonicalize_object(prior),
            MANIFEST_2: current_raw,
        },
        "current_parts": {},
        "current_indexes": {INDEX_1: index_raw},
        "current_receipts": {RECEIPT_1: receipt_raw},
        "deleted_parts": {PART_1: part_raw},
        "publication": publication,
        "receipt": receipt,
    }


class GitActiveTree365DayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.context = builder.trusted_context()

    def test_01_builder_is_byte_equivalent_and_predecessor_is_exact(
        self,
    ) -> None:
        builder._check()
        readiness = builder.build_readiness()
        self.assertEqual(
            readiness["status"],
            "DRAFT_NON_ACTIVE_GIT_ACTIVE_TREE_365D_READY",
        )
        self.assertEqual(
            readiness["source_trust"]["m062_predecessor"][
                "verified_git_object_id"
            ],
            builder.M062_GIT_OBJECT,
        )
        self.assertEqual(
            readiness["task_contract"]["completed_task_ids"],
            ["M-063"],
        )
        self.assertEqual(
            readiness["next_phase"],
            "MECHANISM_GIT_HISTORY_PERSISTENCE_DISCLOSURE",
        )
        self.assertFalse(readiness["real_execution_permitted"])
        self.assertEqual(readiness["schema_closure_count"], 33)
        self.assertEqual(readiness["policy_count"], 5)

    def test_02_day_364_retains_full_fidelity(self) -> None:
        _, result = _evaluate("2027-07-21T16:00:00.000000Z")
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        plan = parse_json_bytes(result.canonical_plan_bytes)
        self.assertEqual(result.keep_part_numbers, (1,))
        self.assertEqual(result.eligible_part_numbers, ())
        self.assertEqual(
            observation["part_observations"][0]["retention_state"],
            "RETAIN_BEFORE_BOUNDARY",
        )
        self.assertTrue(
            observation["part_observations"][0][
                "full_fidelity_verified"
            ]
        )
        self.assertEqual(plan["decision"], "KEEP_ACTIVE_TREE")
        self.assertEqual(plan["selected_count"], 0)

    def test_03_exact_day_365_boundary_is_still_retained(self) -> None:
        _, result = _evaluate("2027-07-22T16:00:00.000000Z")
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        self.assertEqual(result.keep_part_numbers, (1,))
        self.assertEqual(result.eligible_part_numbers, ())
        self.assertEqual(
            observation["part_observations"][0]["elapsed_microseconds"],
            365 * 24 * 60 * 60 * 1_000_000,
        )
        self.assertEqual(
            observation["part_observations"][0]["retention_state"],
            "RETAIN_AT_BOUNDARY",
        )

    def test_04_one_microsecond_after_day_365_is_eligible(self) -> None:
        manifest, result = _evaluate("2027-07-22T16:00:00.000001Z")
        plan = parse_json_bytes(result.canonical_plan_bytes)
        self.assertEqual(result.keep_part_numbers, ())
        self.assertEqual(result.eligible_part_numbers, (1,))
        self.assertEqual(plan["decision"], "PLAN_CURRENT_TREE_PRUNE")
        self.assertEqual(plan["selected_count"], 1)
        self.assertEqual(
            plan["candidates"][0]["prior_daily_manifest_digest"],
            manifest["manifest_digest"],
        )
        self.assertFalse(plan["delete_authority_granted"])
        self.assertFalse(plan["real_execution_permitted"])
        self.assertFalse(plan["history_rewrite_performed"])
        self.assertFalse(plan["hard_delete_claimed"])

    def test_05_prune_deadline_equality_is_on_time_then_breaches(
        self,
    ) -> None:
        _, at_deadline = _evaluate("2027-07-23T16:00:00.000000Z")
        at_plan = parse_json_bytes(at_deadline.canonical_plan_bytes)
        self.assertEqual(
            at_plan["candidates"][0]["deadline_status"],
            "ON_TIME_WINDOW",
        )
        self.assertIsNone(
            at_plan["candidates"][0]["required_gap_code"]
        )
        _, late = _evaluate("2027-07-23T16:00:00.000001Z")
        late_plan = parse_json_bytes(late.canonical_plan_bytes)
        self.assertEqual(
            late_plan["candidates"][0]["deadline_status"],
            "DEADLINE_BREACHED",
        )
        self.assertEqual(
            late_plan["candidates"][0]["required_gap_code"],
            "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH",
        )

    def test_06_manifest_history_is_gapless_and_parts_are_immutable(
        self,
    ) -> None:
        material = _prune_material()
        validate_daily_tree_material(
            self.context,
            manifest_history_bytes=material["history"],
            part_bytes=material["current_parts"],
            index_bytes=material["current_indexes"],
            receipt_bytes=material["current_receipts"],
            expected_bundle_digest=BUNDLE,
        )
        missing = dict(material["history"])
        missing.pop(MANIFEST_1)
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "MANIFEST_HISTORY_NOT_CONTIGUOUS",
        ):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=missing,
                part_bytes=material["current_parts"],
                index_bytes=material["current_indexes"],
                receipt_bytes=material["current_receipts"],
                expected_bundle_digest=BUNDLE,
            )
        changed = copy.deepcopy(material["current"])
        changed["parts"][0]["index_digest"] = _digest("mutated-index")
        changed = _seal(changed, "/manifest_digest")
        history = dict(material["history"])
        history[MANIFEST_2] = canonicalize_object(changed)
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "MANIFEST_HISTORY_INVALID",
        ):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=history,
                part_bytes=material["current_parts"],
                index_bytes=material["current_indexes"],
                receipt_bytes=material["current_receipts"],
                expected_bundle_digest=BUNDLE,
            )

    def test_07_active_shard_and_retained_index_bytes_are_exact(self) -> None:
        _, history, parts, indexes, receipts = _active_tree()
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "ACTIVE_SHARD_MISSING",
        ):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=history,
                part_bytes={},
                index_bytes=indexes,
                receipt_bytes=receipts,
                expected_bundle_digest=BUNDLE,
            )
        changed = dict(indexes)
        changed[INDEX_1] = changed[INDEX_1] + b"\n"
        with self.assertRaises(GitActiveTreePolicyError):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=history,
                part_bytes=parts,
                index_bytes=changed,
                receipt_bytes=receipts,
                expected_bundle_digest=BUNDLE,
            )
        unlisted = dict(parts)
        unlisted[ROOT + "/part-0002.jsonl"] = next(iter(parts.values()))
        with self.assertRaises(GitActiveTreePolicyError):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=history,
                part_bytes=unlisted,
                index_bytes=indexes,
                receipt_bytes=receipts,
                expected_bundle_digest=BUNDLE,
            )

    def test_08_jsonl_and_object_framing_fail_closed(self) -> None:
        _, history, parts, indexes, receipts = _active_tree()
        bad_parts = (
            {PART_1: parts[PART_1][:-1]},
            {PART_1: b"\xef\xbb\xbf" + parts[PART_1]},
            {PART_1: parts[PART_1].replace(b"\n", b"\r\n")},
        )
        for candidate in bad_parts:
            with self.subTest(candidate=candidate):
                with self.assertRaises(GitActiveTreePolicyError):
                    validate_daily_tree_material(
                        self.context,
                        manifest_history_bytes=history,
                        part_bytes=candidate,
                        index_bytes=indexes,
                        receipt_bytes=receipts,
                        expected_bundle_digest=BUNDLE,
                    )
        bad_history = dict(history)
        bad_history[MANIFEST_1] += b"\n"
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "MANIFEST_FRAMING_INVALID",
        ):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=bad_history,
                part_bytes=parts,
                index_bytes=indexes,
                receipt_bytes=receipts,
                expected_bundle_digest=BUNDLE,
            )

    def test_09_retained_index_cannot_smuggle_full_event_fields(self) -> None:
        material = _prune_material()
        rows = [
            parse_json_bytes(line)
            for line in material["current_indexes"][INDEX_1][:-1].split(
                b"\n"
            )
        ]
        rows[0]["model_ref"] = "not-allowed-in-index"
        rows[0] = _seal(rows[0], "/index_entry_digest")
        bad_index = b"".join(
            canonicalize_object(row) + b"\n" for row in rows
        )
        with self.assertRaises(GitActiveTreePolicyError):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=material["history"],
                part_bytes=material["current_parts"],
                index_bytes={INDEX_1: bad_index},
                receipt_bytes=material["current_receipts"],
                expected_bundle_digest=BUNDLE,
            )

    def test_10_receipt_binds_transition_predecessor_not_latest(self) -> None:
        material = _prune_material()
        revision_three = copy.deepcopy(material["current"])
        revision_three["manifest_uid"] = _uid("drm", "3")
        revision_three["manifest_revision"] = 3
        revision_three["previous_manifest_digest"] = material["current"][
            "manifest_digest"
        ]
        revision_three["auto_transaction_uid"] = _uid("atx", "3")
        revision_three["publication_transaction_at"] = (
            "2027-07-22T20:00:00.000000Z"
        )
        revision_three = _seal(revision_three, "/manifest_digest")
        history = dict(material["history"])
        history[ROOT + "/manifest-0003.json"] = canonicalize_object(
            revision_three
        )
        validated = validate_daily_tree_material(
            self.context,
            manifest_history_bytes=history,
            part_bytes={},
            index_bytes=material["current_indexes"],
            receipt_bytes=material["current_receipts"],
            expected_bundle_digest=BUNDLE,
        )
        self.assertEqual(
            validated.latest_manifest["manifest_revision"],
            3,
        )
        self.assertEqual(
            material["receipt"]["affected_public_artifacts"][0][
                "prior_daily_manifest_digest"
            ],
            material["prior"]["manifest_digest"],
        )

    def test_11_exact_prune_transition_closes_all_artifacts(self) -> None:
        material = _prune_material()
        evidence = validate_prune_transition(
            self.context,
            manifest_history_bytes=material["history"],
            current_part_bytes=material["current_parts"],
            current_index_bytes=material["current_indexes"],
            current_receipt_bytes=material["current_receipts"],
            deleted_prior_part_bytes=material["deleted_parts"],
            publication=material["publication"],
            expected_bundle_digest=BUNDLE,
        )
        self.assertEqual(evidence["deleted_part_numbers"], (1,))
        self.assertEqual(evidence["retained_index_count"], 1)
        self.assertFalse(evidence["history_rewrite_performed"])
        self.assertFalse(evidence["hard_delete_claimed"])
        self.assertFalse(evidence["real_execution_performed"])

    def test_12_wrong_receipt_or_extra_transaction_path_fails(self) -> None:
        material = _prune_material()
        wrong_receipt = copy.deepcopy(material["receipt"])
        wrong_receipt["affected_public_artifacts"][0][
            "prior_daily_manifest_digest"
        ] = _digest("wrong-prior-manifest")
        wrong_receipt = _seal(wrong_receipt, "/receipt_digest")
        wrong_current = copy.deepcopy(material["current"])
        wrong_current["parts"][0]["retention_receipt_digest"] = (
            wrong_receipt["receipt_digest"]
        )
        wrong_current = _seal(wrong_current, "/manifest_digest")
        wrong_history = dict(material["history"])
        wrong_history[MANIFEST_2] = canonicalize_object(wrong_current)
        with self.assertRaises(GitActiveTreePolicyError):
            validate_daily_tree_material(
                self.context,
                manifest_history_bytes=wrong_history,
                part_bytes={},
                index_bytes=material["current_indexes"],
                receipt_bytes={
                    RECEIPT_1: canonicalize_object(wrong_receipt)
                },
                expected_bundle_digest=BUNDLE,
            )
        extra = copy.deepcopy(material["publication"])
        artifact = copy.deepcopy(
            extra["lane_manifests"][0]["artifacts"][0]
        )
        artifact["artifact_uid"] = _uid("idx", "7")
        artifact["artifact_repo_path"] = INDEX_1
        artifact["artifact_schema_id"] = (
            "urn:linzecolin:agentdatabase:skillops:"
            "schema:run-event-index-entry:v1"
        )
        artifact["artifact_serialization"] = JSONL_SERIALIZATION
        artifact["artifact_digest"] = _digest("extra-index")
        artifact["artifact_bytes"] = 1
        artifact["artifact_record_count"] = 1
        extra["lane_manifests"][0]["artifacts"].append(artifact)
        extra["lane_manifests"][0]["artifacts"].sort(
            key=lambda item: (
                item["artifact_repo_path"],
                item["artifact_uid"],
            )
        )
        extra["lane_manifests"][0]["artifact_count"] += 1
        extra = _seal(extra, "/manifest_digest")
        with self.assertRaises(GitActiveTreePolicyError):
            validate_prune_transition(
                self.context,
                manifest_history_bytes=material["history"],
                current_part_bytes={},
                current_index_bytes=material["current_indexes"],
                current_receipt_bytes=material["current_receipts"],
                deleted_prior_part_bytes=material["deleted_parts"],
                publication=extra,
                expected_bundle_digest=BUNDLE,
            )

    def test_13_self_consistent_observation_and_plan_forgery_fails(
        self,
    ) -> None:
        _, result = _evaluate("2027-07-22T16:00:00.000001Z")
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        forged_observation = copy.deepcopy(observation)
        forged_observation["part_observations"][0][
            "retention_state"
        ] = "RETAIN_AT_BOUNDARY"
        forged_observation["evidence_bundle_digest"] = canonical_digest(
            forged_observation,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "PART_SEMANTIC_MISMATCH",
        ):
            validate_retention_observation(
                self.context,
                forged_observation,
                expected_bundle_digest=BUNDLE,
            )
        plan = parse_json_bytes(result.canonical_plan_bytes)
        forged_plan = copy.deepcopy(plan)
        forged_plan["selected_count"] = 0
        forged_plan["evidence_bundle_digest"] = canonical_digest(
            forged_plan,
            "/evidence_bundle_digest",
        )
        with self.assertRaises(GitActiveTreePolicyError):
            validate_prune_plan(
                self.context,
                forged_plan,
                observation,
                expected_bundle_digest=BUNDLE,
            )

    def test_14_clock_and_anchor_cannot_be_rebased(self) -> None:
        manifest, history, parts, indexes, receipts = _active_tree()
        changed = copy.deepcopy(manifest)
        changed["parts"][0]["retention_not_before"] = (
            "2027-07-22T16:00:00.000001Z"
        )
        changed = _seal(changed, "/manifest_digest")
        with self.assertRaises(GitActiveTreePolicyError):
            evaluate_git_active_tree(
                self.context,
                manifest_history_bytes={
                    MANIFEST_1: canonicalize_object(changed)
                },
                part_bytes=parts,
                index_bytes=indexes,
                receipt_bytes=receipts,
                observation_uid=OBSERVATION_UID,
                plan_uid=PLAN_UID,
                observed_at="2027-07-22T16:00:00.000001Z",
                expected_bundle_digest=BUNDLE,
            )
        with self.assertRaisesRegex(
            GitActiveTreePolicyError,
            "OBSERVED_BEFORE_FIRST_PUBLICATION",
        ):
            _evaluate("2026-07-22T15:59:59.999999Z")

    def test_15_predecessor_drift_is_never_current_tree_trust(self) -> None:
        original = builder._git_blob

        def drifted(object_id: str, path: str) -> bytes:
            raw = original(object_id, path)
            if (
                object_id == builder.M062_GIT_OBJECT
                and path == builder.M062_READINESS_PATH
            ):
                return raw + b" "
            return raw

        with mock.patch.object(
            builder,
            "_git_blob",
            side_effect=drifted,
        ):
            with self.assertRaisesRegex(
                builder.GitActiveTreePolicyBuildError,
                "M063_M062_PREDECESSOR_TRUST_MISMATCH",
            ):
                builder.build_readiness()

    def test_16_policy_api_has_no_mutable_runtime_capability(self) -> None:
        parameters = inspect.signature(evaluate_git_active_tree).parameters
        for forbidden in (
            "repo_root",
            "state_root",
            "lock",
            "watermark",
            "publisher",
            "delete",
            "remote_reader",
        ):
            self.assertNotIn(forbidden, parameters)
        readiness = builder.build_readiness()
        self.assertFalse(
            readiness["nonmutation"][
                "git_current_tree_mutation_performed"
            ]
        )
        self.assertFalse(
            readiness["nonmutation"][
                "git_history_rewrite_performed"
            ]
        )
        self.assertFalse(
            readiness["nonmutation"][
                "canonical_publication_permitted"
            ]
        )


if __name__ == "__main__":
    unittest.main()
