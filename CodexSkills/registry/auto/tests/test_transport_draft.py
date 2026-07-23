from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path


AUTO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = AUTO_DIR.parents[2]
sys.path.insert(
    0,
    str(REPO_ROOT / "CodexSkills" / "governance" / "tools"),
)

from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    scan_public_value,
)
from CodexSkills.registry.auto.tools import build_transport_draft as builder
from CodexSkills.registry.auto.tools.validate_transport_draft import (
    CURRENT_CANDIDATE_BUNDLE_DIGEST,
    DAILY_MANIFEST_ID,
    INDEX_ENTRY_ID,
    JSONL_SERIALIZATION,
    OBJECT_SERIALIZATION,
    PUBLICATION_V2_ID,
    REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
    RETENTION_V3_ID,
    RUN_LOG_ROOT,
    _digest,
    _policy_with_allowlist_delta,
    _sydney_date,
    daily_manifest_fixture,
    discover_required_allowlist_additions,
    index_entry_fixture,
    legal_fixtures,
    load_transport_draft,
    publication_manifest_fixture,
    retention_receipt_fixture,
    validate_index_entries,
    validate_jcs_jsonl_bytes,
    validate_jcs_object_bytes,
    validate_manifest_tree,
    validate_pruned_manifest_receipt_links,
    validate_transport_instance,
)


class TransportDraftTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract = load_transport_draft()

    def resign(self, instance, pointer):
        copied = copy.deepcopy(instance)
        copied[pointer.removeprefix("/")] = "0" * 64
        copied[pointer.removeprefix("/")] = canonical_digest(copied, pointer)
        return copied

    def validate(self, instance, schema_id):
        validate_transport_instance(
            self.contract,
            instance,
            schema_id,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            allow_draft_policy_delta=True,
        )

    def assert_invalid(self, instance, schema_id, pattern):
        with self.assertRaisesRegex(ContractError, pattern):
            self.validate(instance, schema_id)

    def test_builder_is_byte_equivalent(self) -> None:
        for path, expected in builder.generated_files().items():
            self.assertEqual(path.read_bytes(), expected)

    def test_current_candidate_remains_29_5_and_target_is_31_5(self) -> None:
        self.assertEqual(len(self.contract.current_candidate.schemas), 29)
        self.assertEqual(len(self.contract.current_candidate.policies), 5)
        self.assertEqual(len(self.contract.bundle.schemas), 31)
        self.assertEqual(len(self.contract.bundle.policies), 5)
        self.assertNotIn(builder.PUBLICATION_V1_ID, self.contract.bundle.schemas)
        self.assertNotIn(builder.RETENTION_V2_ID, self.contract.bundle.schemas)

    def test_unknown_schema_urn_fails_closed(self) -> None:
        with self.assertRaisesRegex(
            ContractError,
            "AUTO_TRANSPORT_SCHEMA_ID_UNKNOWN",
        ):
            validate_transport_instance(
                self.contract,
                {},
                builder.SCHEMA_PREFIX + "unknown-transport:v1",
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            )

    def test_interface_pins_promotion_and_loader_isolation(self) -> None:
        interface = self.contract.interface
        self.assertTrue(
            interface["promotion_required_before_candidate_materialization"]
        )
        self.assertTrue(interface["draft_paths_forbidden_in_candidate_manifest"])
        self.assertFalse(interface["repository_bound"])
        self.assertFalse(interface["au_040_complete"])
        self.assertFalse(
            interface["draft_validation_context"][
                "retention_policy_v3_present"
            ]
        )
        self.assertTrue(
            interface["draft_validation_context"][
                "current_policy_set_used_for_schema_validation_only"
            ]
        )
        self.assertEqual(
            interface["proposed_active_shared_set"]["replaced_policy_ids"],
            [
                "urn:linzecolin:agentdatabase:skillops:"
                "policy:retention:v2"
            ],
        )
        self.assertEqual(
            interface["proposed_active_shared_set"][
                "replacement_policy_ids"
            ],
            [
                "urn:linzecolin:agentdatabase:skillops:"
                "policy:retention:v3"
            ],
        )
        self.assertEqual(
            interface["next_phase"],
            "MECHANISM_AU040_SEMANTIC_POLICY_ACCEPTANCE",
        )
        for entry in interface["draft_schema_entries"]:
            self.assertIn("/transport-draft/", entry["draft_relative_path"])
            self.assertTrue(
                entry["proposed_canonical_relative_path"].startswith(
                    "CodexSkills/registry/auto/schemas/public-v2/"
                )
            )
            self.assertNotIn(
                "/schemas/public/",
                entry["proposed_canonical_relative_path"],
            )
            self.assertNotIn(
                "draft",
                entry["proposed_canonical_relative_path"].split("/"),
            )

    def test_legal_fixtures_validate_with_exact_draft_policy_delta(self) -> None:
        for schema_id, fixture in legal_fixtures().items():
            with self.subTest(schema_id=schema_id):
                self.validate(fixture, schema_id)

    def test_current_scanner_discovers_only_machine_declared_delta(self) -> None:
        fixtures = list(legal_fixtures().values())
        discovered = discover_required_allowlist_additions(
            fixtures,
            self.contract.bundle.policies,
        )
        self.assertEqual(
            discovered,
            REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
        )
        self.assertEqual(
            discovered,
            self.contract.interface[
                "required_mechanism_public_value_allowlist_additions"
            ],
        )
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_HIGH_ENTROPY_FREE_STRING_BLOCK",
        ):
            scan_public_value(
                daily_manifest_fixture(),
                self.contract.bundle.policies,
            )

    def test_forbidden_public_field_still_fails_with_draft_delta(self) -> None:
        policies = _policy_with_allowlist_delta(
            self.contract.bundle.policies,
            REQUIRED_MECHANISM_PUBLIC_VALUE_ALLOWLIST_ADDITIONS,
        )
        with self.assertRaisesRegex(ContractError, "PUBLIC_FORBIDDEN_FIELD"):
            scan_public_value({"raw": "not-public"}, policies)

    def test_self_digest_and_context_digest_fail_closed(self) -> None:
        fixture = daily_manifest_fixture()
        fixture["active_record_count"] += 1
        with self.assertRaisesRegex(ContractError, "SELF_DIGEST_MISMATCH"):
            self.validate(fixture, DAILY_MANIFEST_ID)
        fixture = daily_manifest_fixture()
        fixture["bundle_digest"] = "f" * 64
        fixture = self.resign(fixture, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "CONTEXT_BUNDLE_DIGEST_MISMATCH",
        ):
            self.validate(fixture, DAILY_MANIFEST_ID)

    def test_jcs_object_duplicate_key_ijson_and_pretty_bytes_rejected(self) -> None:
        fixture = daily_manifest_fixture()
        canonical = canonicalize_object(fixture)
        observed = validate_jcs_object_bytes(
            canonical,
            self.contract,
            DAILY_MANIFEST_ID,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            allow_draft_policy_delta=True,
        )
        self.assertEqual(observed, fixture)
        with self.assertRaisesRegex(Exception, "DUPLICATE_KEY"):
            validate_jcs_object_bytes(
                b'{"schema_version":"x","schema_version":"y"}',
                self.contract,
                DAILY_MANIFEST_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            )
        with self.assertRaisesRegex(Exception, "NON_FINITE_NUMBER"):
            validate_jcs_object_bytes(
                b'{"value":NaN}',
                self.contract,
                DAILY_MANIFEST_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            )
        pretty = json.dumps(fixture, indent=2).encode("utf-8")
        with self.assertRaisesRegex(
            ContractError,
            "JCS_BYTES_NOT_CANONICAL",
        ):
            validate_jcs_object_bytes(
                pretty,
                self.contract,
                DAILY_MANIFEST_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
                allow_draft_policy_delta=True,
            )

    def test_jsonl_requires_per_line_jcs_and_final_lf(self) -> None:
        rows = [index_entry_fixture(), index_entry_fixture(correction=True)]
        raw = b"".join(canonicalize_object(row) + b"\n" for row in rows)
        observed = validate_jcs_jsonl_bytes(
            raw,
            self.contract,
            INDEX_ENTRY_ID,
            expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
            allow_draft_policy_delta=True,
        )
        self.assertEqual(observed, rows)
        with self.assertRaisesRegex(
            ContractError,
            "JSONL_FRAMING_INVALID",
        ):
            validate_jcs_jsonl_bytes(
                raw[:-1],
                self.contract,
                INDEX_ENTRY_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
                allow_draft_policy_delta=True,
            )
        with self.assertRaisesRegex(
            ContractError,
            "JSONL_FRAMING_INVALID",
        ):
            validate_jcs_jsonl_bytes(
                raw.replace(b"\n", b"\r\n"),
                self.contract,
                INDEX_ENTRY_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
                allow_draft_policy_delta=True,
            )
        noncanonical = json.dumps(rows[0], indent=2).encode("utf-8") + b"\n"
        with self.assertRaisesRegex(
            ContractError,
            "JSONL_LINE_NOT_JCS",
        ):
            validate_jcs_jsonl_bytes(
                noncanonical,
                self.contract,
                INDEX_ENTRY_ID,
                expected_bundle_digest=CURRENT_CANDIDATE_BUNDLE_DIGEST,
                allow_draft_policy_delta=True,
            )

    def test_manifest_revision_previous_digest_conditional(self) -> None:
        revision_one = daily_manifest_fixture()
        revision_one["manifest_revision"] = 1
        revision_one["previous_manifest_digest"] = None
        revision_one = self.resign(revision_one, "/manifest_digest")
        self.validate(revision_one, DAILY_MANIFEST_ID)
        invalid = daily_manifest_fixture()
        invalid["previous_manifest_digest"] = None
        invalid = self.resign(invalid, "/manifest_digest")
        self.assert_invalid(
            invalid,
            DAILY_MANIFEST_ID,
            "SCHEMA_VALIDATION_FAILED",
        )

    def test_manifest_active_and_pruned_receipt_conditionals(self) -> None:
        active_with_receipt = daily_manifest_fixture()
        for field in (
            "retention_receipt_path",
            "retention_receipt_uid",
            "retention_receipt_digest",
            "pruned_at",
        ):
            active_with_receipt["parts"][0][field] = copy.deepcopy(
                active_with_receipt["parts"][1][field]
            )
        active_with_receipt = self.resign(
            active_with_receipt,
            "/manifest_digest",
        )
        self.assert_invalid(
            active_with_receipt,
            DAILY_MANIFEST_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        pruned_without_receipt = daily_manifest_fixture()
        del pruned_without_receipt["parts"][1]["retention_receipt_digest"]
        pruned_without_receipt = self.resign(
            pruned_without_receipt,
            "/manifest_digest",
        )
        self.assert_invalid(
            pruned_without_receipt,
            DAILY_MANIFEST_ID,
            "SCHEMA_VALIDATION_FAILED",
        )

    def test_manifest_arithmetic_order_and_sydney_date(self) -> None:
        invalid = daily_manifest_fixture()
        invalid["active_shard_bytes"] += 1
        invalid = self.resign(invalid, "/manifest_digest")
        self.assert_invalid(
            invalid,
            DAILY_MANIFEST_ID,
            "ACTIVE_BYTES_MISMATCH",
        )
        invalid = daily_manifest_fixture()
        invalid["parts"].reverse()
        invalid = self.resign(invalid, "/manifest_digest")
        self.assert_invalid(
            invalid,
            DAILY_MANIFEST_ID,
            "PART_NUMBERS_NOT_CONTIGUOUS",
        )
        invalid = daily_manifest_fixture()
        invalid["local_date"] = "2026-07-22"
        invalid = self.resign(invalid, "/manifest_digest")
        self.assert_invalid(
            invalid,
            DAILY_MANIFEST_ID,
            "SYDNEY_DATE_MISMATCH",
        )
        self.assertEqual(
            _sydney_date("2026-10-03T16:30:00.000000Z"),
            "2026-10-04",
        )

    def test_manifest_tree_requires_active_shard_and_persistent_indexes(self) -> None:
        manifest = daily_manifest_fixture()
        root = RUN_LOG_ROOT + "2026/07/23/"
        artifacts = {
            root + "part-0001.jsonl": {
                "digest": manifest["parts"][0]["shard_digest"],
                "bytes": manifest["parts"][0]["shard_bytes"],
                "records": manifest["parts"][0]["record_count"],
            },
            root + "index-0001.jsonl": {
                "digest": manifest["parts"][0]["index_digest"],
                "bytes": manifest["parts"][0]["index_bytes"],
                "records": manifest["parts"][0]["index_record_count"],
            },
            root + "index-0002.jsonl": {
                "digest": manifest["parts"][1]["index_digest"],
                "bytes": manifest["parts"][1]["index_bytes"],
                "records": manifest["parts"][1]["index_record_count"],
            },
        }
        validate_manifest_tree(
            manifest,
            root + "manifest-0002.json",
            artifacts,
        )
        missing_index = copy.deepcopy(artifacts)
        del missing_index[root + "index-0002.jsonl"]
        with self.assertRaisesRegex(ContractError, "RETAINED_INDEX_MISSING"):
            validate_manifest_tree(
                manifest,
                root + "manifest-0002.json",
                missing_index,
            )
        pruned_present = copy.deepcopy(artifacts)
        pruned_present[root + "part-0002.jsonl"] = {
            "digest": manifest["parts"][1]["shard_digest"],
            "bytes": manifest["parts"][1]["shard_bytes"],
            "records": manifest["parts"][1]["record_count"],
        }
        with self.assertRaisesRegex(ContractError, "PRUNED_SHARD_PRESENT"):
            validate_manifest_tree(
                manifest,
                root + "manifest-0002.json",
                pruned_present,
            )

    def test_index_closure_order_and_exact_correction_target(self) -> None:
        rows = [index_entry_fixture(), index_entry_fixture(correction=True)]
        validate_index_entries(
            rows,
            event_rows=rows,
            expected_part_number=1,
            expected_record_count=2,
        )
        reversed_rows = list(reversed(rows))
        with self.assertRaisesRegex(ContractError, "LINE_NUMBERS_NOT_CONTIGUOUS"):
            validate_index_entries(
                reversed_rows,
                event_rows=rows,
                expected_part_number=1,
                expected_record_count=2,
            )
        wrong = copy.deepcopy(rows)
        wrong[1]["supersedes_event_digest"] = _digest("wrong-target")
        wrong[1] = self.resign(wrong[1], "/index_entry_digest")
        with self.assertRaisesRegex(
            ContractError,
            "CORRECTION_TARGET_NOT_EXACT",
        ):
            validate_index_entries(
                wrong,
                event_rows=wrong,
                expected_part_number=1,
                expected_record_count=2,
            )
        row_mismatch = copy.deepcopy(rows)
        events = copy.deepcopy(rows)
        events[1]["event_digest"] = _digest("different-part-event")
        with self.assertRaisesRegex(
            ContractError,
            "EVENT_ROW_MISMATCH",
        ):
            validate_index_entries(
                row_mismatch,
                event_rows=events,
                expected_part_number=1,
                expected_record_count=2,
            )

    def test_manifest_pruned_entry_binds_exact_retention_receipt(self) -> None:
        manifest = daily_manifest_fixture()
        receipt = retention_receipt_fixture()
        root = RUN_LOG_ROOT + "2026/07/23/"
        validate_pruned_manifest_receipt_links(
            manifest,
            root + "manifest-0002.json",
            {
                manifest["parts"][1]["retention_receipt_path"]: receipt,
            },
        )
        wrong = copy.deepcopy(receipt)
        wrong["affected_public_artifacts"][0][
            "retained_index_digest"
        ] = _digest("wrong-retained-index")
        wrong = self.resign(wrong, "/receipt_digest")
        manifest_wrong = copy.deepcopy(manifest)
        manifest_wrong["parts"][1]["retention_receipt_digest"] = wrong[
            "receipt_digest"
        ]
        manifest_wrong = self.resign(manifest_wrong, "/manifest_digest")
        with self.assertRaisesRegex(
            ContractError,
            "AFFECTED_PART_MISMATCH",
        ):
            validate_pruned_manifest_receipt_links(
                manifest_wrong,
                root + "manifest-0002.json",
                {
                    manifest_wrong["parts"][1][
                        "retention_receipt_path"
                    ]: wrong,
                },
            )

    def test_index_correction_conditional_and_self_reference(self) -> None:
        missing = index_entry_fixture(correction=True)
        del missing["supersedes_event_digest"]
        missing = self.resign(missing, "/index_entry_digest")
        self.assert_invalid(
            missing,
            INDEX_ENTRY_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        self_reference = index_entry_fixture(correction=True)
        self_reference["supersedes_event_uid"] = self_reference["event_uid"]
        self_reference = self.resign(
            self_reference,
            "/index_entry_digest",
        )
        self.assert_invalid(
            self_reference,
            INDEX_ENTRY_ID,
            "CORRECTION_SELF_REFERENCE",
        )

    def test_publication_put_delete_conditionals(self) -> None:
        missing_put_serialization = publication_manifest_fixture()
        artifact = missing_put_serialization["lane_manifests"][0]["artifacts"][0]
        del artifact["artifact_serialization"]
        missing_put_serialization = self.resign(
            missing_put_serialization,
            "/manifest_digest",
        )
        self.assert_invalid(
            missing_put_serialization,
            PUBLICATION_V2_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        delete_with_new_digest = publication_manifest_fixture()
        delete_artifact = delete_with_new_digest["lane_manifests"][0][
            "artifacts"
        ][3]
        delete_artifact["artifact_digest"] = _digest("forbidden-new")
        delete_with_new_digest = self.resign(
            delete_with_new_digest,
            "/manifest_digest",
        )
        self.assert_invalid(
            delete_with_new_digest,
            PUBLICATION_V2_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        delete_with_payload = publication_manifest_fixture()
        delete_with_payload["lane_manifests"][0]["artifacts"][3][
            "payload"
        ] = "forbidden"
        delete_with_payload = self.resign(
            delete_with_payload,
            "/manifest_digest",
        )
        self.assert_invalid(
            delete_with_payload,
            PUBLICATION_V2_ID,
            "SCHEMA_VALIDATION_FAILED",
        )

    def test_publication_rejects_whole_jsonl_as_object_and_path_mismatch(self) -> None:
        whole_object = publication_manifest_fixture()
        whole_object["lane_manifests"][0]["artifacts"][0][
            "artifact_serialization"
        ] = OBJECT_SERIALIZATION
        whole_object = self.resign(whole_object, "/manifest_digest")
        self.assert_invalid(
            whole_object,
            PUBLICATION_V2_ID,
            "INDEX_PATH_OPERATION_SCHEMA_MISMATCH",
        )
        mismatch = publication_manifest_fixture()
        mismatch["lane_manifests"][0]["artifacts"][2][
            "artifact_schema_id"
        ] = INDEX_ENTRY_ID
        mismatch = self.resign(mismatch, "/manifest_digest")
        self.assert_invalid(
            mismatch,
            PUBLICATION_V2_ID,
            "PART_PATH_OPERATION_SCHEMA_MISMATCH",
        )

    def test_publication_rejects_unlisted_delete_and_order_mismatch(self) -> None:
        unlisted = publication_manifest_fixture()
        artifact = unlisted["lane_manifests"][0]["artifacts"][0]
        artifact["artifact_operation"] = "DELETE"
        artifact["prior_artifact_serialization"] = artifact.pop(
            "artifact_serialization"
        )
        artifact["prior_artifact_digest"] = artifact.pop("artifact_digest")
        artifact["prior_artifact_bytes"] = artifact.pop("artifact_bytes")
        artifact["prior_artifact_record_count"] = artifact.pop(
            "artifact_record_count"
        )
        unlisted = self.resign(unlisted, "/manifest_digest")
        self.assert_invalid(
            unlisted,
            PUBLICATION_V2_ID,
            "PUBLICATION_UNLISTED_DELETION",
        )
        unsorted = publication_manifest_fixture()
        unsorted["lane_manifests"][0]["artifacts"].reverse()
        unsorted = self.resign(unsorted, "/manifest_digest")
        self.assert_invalid(
            unsorted,
            PUBLICATION_V2_ID,
            "ARTIFACT_ORDER",
        )

    def test_retention_exact_aggregate_and_strict_boundary(self) -> None:
        invalid = retention_receipt_fixture()
        invalid["affected_bytes"] += 1
        invalid["selected_bytes"] += 1
        invalid = self.resign(invalid, "/receipt_digest")
        self.assert_invalid(
            invalid,
            RETENTION_V3_ID,
            "AFFECTED_ARTIFACT_BYTES_MISMATCH",
        )
        boundary = retention_receipt_fixture()
        boundary["executed_at"] = boundary["affected_public_artifacts"][0][
            "retention_not_before"
        ]
        boundary["cutoff_at"] = boundary["executed_at"]
        boundary = self.resign(boundary, "/receipt_digest")
        self.assert_invalid(
            boundary,
            RETENTION_V3_ID,
            "EXECUTION_NOT_STRICTLY_AFTER_ANCHOR",
        )

    def test_retention_deadline_truthfulness_and_boundary(self) -> None:
        at_deadline = retention_receipt_fixture()
        at_deadline["executed_at"] = at_deadline[
            "affected_public_artifacts"
        ][0]["prune_deadline_at"]
        at_deadline["cutoff_at"] = at_deadline["executed_at"]
        at_deadline = self.resign(at_deadline, "/receipt_digest")
        self.validate(at_deadline, RETENTION_V3_ID)

        late = retention_receipt_fixture()
        late["executed_at"] = "2027-07-23T17:00:00.000001Z"
        late["cutoff_at"] = "2027-07-23T17:00:00.000000Z"
        late = self.resign(late, "/receipt_digest")
        self.assert_invalid(
            late,
            RETENTION_V3_ID,
            "PRUNE_DEADLINE_BREACH_STATE_MISMATCH",
        )
        late["prune_deadline_breached"] = True
        late = self.resign(late, "/receipt_digest")
        self.assert_invalid(
            late,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        late["gap_code"] = "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
        late = self.resign(late, "/receipt_digest")
        self.validate(late, RETENTION_V3_ID)

        on_time_with_gap = retention_receipt_fixture()
        on_time_with_gap[
            "gap_code"
        ] = "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
        on_time_with_gap = self.resign(
            on_time_with_gap,
            "/receipt_digest",
        )
        self.assert_invalid(
            on_time_with_gap,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )

        wrong_deadline = retention_receipt_fixture()
        wrong_deadline["affected_public_artifacts"][0][
            "prune_deadline_at"
        ] = "2027-07-23T16:59:59.999999Z"
        wrong_deadline = self.resign(wrong_deadline, "/receipt_digest")
        self.assert_invalid(
            wrong_deadline,
            RETENTION_V3_ID,
            "PRUNE_DEADLINE_NOT_24H_AFTER_ANCHOR",
        )

    def test_retention_active_tree_requires_ordered_exact_details(self) -> None:
        missing = retention_receipt_fixture()
        del missing["affected_public_artifacts"]
        missing = self.resign(missing, "/receipt_digest")
        self.assert_invalid(
            missing,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        unsorted = retention_receipt_fixture()
        second = copy.deepcopy(unsorted["affected_public_artifacts"][0])
        second["artifact_repo_path"] = second["artifact_repo_path"].replace(
            "part-0002",
            "part-0001",
        )
        second["retained_index_path"] = second["retained_index_path"].replace(
            "index-0002",
            "index-0001",
        )
        second["prior_artifact_digest"] = _digest("part-1-prior")
        unsorted["affected_public_artifacts"].append(second)
        unsorted["affected_count"] = 2
        unsorted["selected_count"] = 2
        unsorted["affected_bytes"] = 8192
        unsorted["selected_bytes"] = 8192
        unsorted = self.resign(unsorted, "/receipt_digest")
        self.assert_invalid(
            unsorted,
            RETENTION_V3_ID,
            "AFFECTED_ARTIFACT_ORDER",
        )

    def test_retention_managed_raw_forbids_public_details(self) -> None:
        managed_raw = retention_receipt_fixture()
        managed_raw["scope"] = "MANAGED_RAW"
        managed_raw["action"] = "KEEP"
        managed_raw["selected_count"] = 0
        managed_raw["selected_bytes"] = 0
        managed_raw["affected_count"] = 0
        managed_raw["affected_bytes"] = 0
        del managed_raw["affected_public_artifacts"]
        del managed_raw["prune_deadline_breached"]
        managed_raw = self.resign(managed_raw, "/receipt_digest")
        self.validate(managed_raw, RETENTION_V3_ID)
        managed_raw["affected_public_artifacts"] = retention_receipt_fixture()[
            "affected_public_artifacts"
        ]
        managed_raw = self.resign(managed_raw, "/receipt_digest")
        self.assert_invalid(
            managed_raw,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )
        wrong_gap = retention_receipt_fixture()
        wrong_gap["scope"] = "MANAGED_RAW"
        wrong_gap["action"] = "KEEP"
        wrong_gap["selected_count"] = 0
        wrong_gap["selected_bytes"] = 0
        wrong_gap["affected_count"] = 0
        wrong_gap["affected_bytes"] = 0
        del wrong_gap["affected_public_artifacts"]
        del wrong_gap["prune_deadline_breached"]
        wrong_gap["gap_code"] = "GIT_CURRENT_TREE_PRUNE_DEADLINE_BREACH"
        wrong_gap = self.resign(wrong_gap, "/receipt_digest")
        self.assert_invalid(
            wrong_gap,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )

    def test_retention_receipt_cannot_reference_new_manifest_digest(self) -> None:
        invalid = retention_receipt_fixture()
        invalid["new_manifest_digest"] = _digest("cycle")
        invalid = self.resign(invalid, "/receipt_digest")
        self.assert_invalid(
            invalid,
            RETENTION_V3_ID,
            "SCHEMA_VALIDATION_FAILED",
        )


if __name__ == "__main__":
    unittest.main()
