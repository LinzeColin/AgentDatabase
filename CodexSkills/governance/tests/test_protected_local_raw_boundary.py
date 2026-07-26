from __future__ import annotations

import copy
import hashlib
import tempfile
import unittest
from pathlib import Path

from CodexSkills.governance.retention.root_lifecycle import (
    CandidateRequest,
    RootBinding,
    RootLifecycleError,
    build_root_lifecycle_contract,
    evaluate_retention_scope,
    raw_ownership_marker,
    recompute_selection_report,
    validate_selection_report,
)
from CodexSkills.governance.tools import (
    build_protected_local_raw_boundary as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)


OBSERVATION_UID = "rlo_01ARZ3NDEKTSV4RRFFQ69G5FAV"
REPORT_UID = "rlr_01ARZ3NDEKTSV4RRFFQ69G5FAW"
OBSERVED_AT = "2026-07-26T00:00:00.000000Z"


class ProtectedLocalRawBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.candidate = builder._trusted_candidate()
        cls.raw_schema = builder._trusted_raw_schema()
        cls.observation_schema = builder.build_observation_schema()
        cls.report_schema = builder.build_report_schema()
        cls.contract = build_root_lifecycle_contract(
            cls.candidate,
            cls.raw_schema,
            builder.RAW_SEGMENT_SCHEMA_SHA256,
            cls.observation_schema,
            canonical_digest(cls.observation_schema),
            cls.report_schema,
            canonical_digest(cls.report_schema),
        )

    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.base = Path(self.temporary.name).resolve(strict=True)
        self.skill_source = self.base / "skill-source"
        self.run_source = self.base / "run-source"
        self.legacy = self.base / "legacy"
        self.staging = self.base / "staging"
        self.public_queue = self.base / "public-queue"
        for path in (
            self.skill_source,
            self.run_source,
            self.legacy,
            self.staging,
            self.public_queue,
        ):
            path.mkdir()

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def roots(self):
        return (
            RootBinding(
                "legacy-data",
                "LEGACY_DATA",
                self.legacy.resolve(strict=True),
            ),
            RootBinding(
                "public-queue",
                "PUBLIC_QUEUE",
                self.public_queue.resolve(strict=True),
            ),
            RootBinding(
                "run-source",
                "RUN_SOURCE",
                self.run_source.resolve(strict=True),
            ),
            RootBinding(
                "skill-source",
                "SKILL_SOURCE",
                self.skill_source.resolve(strict=True),
            ),
            RootBinding(
                "managed-staging",
                "STAGING",
                self.staging.resolve(strict=True),
            ),
        )

    def raw_segment(
        self,
        *,
        number: int,
        mode: str = "TEST_ONLY",
        payload: bytes = b"synthetic managed payload",
    ) -> Path:
        metadata_path = self.staging / f"segment-{number}.json"
        metadata = {
            "schema_version": builder.RAW_SEGMENT_SCHEMA_ID,
            "protocol_revision": builder.PROTOCOL_REVISION,
            "bundle_digest": builder.CANDIDATE_BUNDLE_DIGEST,
            "segment_uid": (
                "raw_01ARZ3NDEKTSV4RRFFQ69G5FA"
                + str(number)
            ),
            "source_generation_uid": (
                "gen_01ARZ3NDEKTSV4RRFFQ69G6FA"
                + str(number)
            ),
            "adapter_id": "synthetic-adapter",
            "adapter_version": "1.0.0",
            "persistence_mode": mode,
            "managed_owned": True,
            "protected_or_legacy": False,
            "ownership_marker_digest": "0" * 64,
            "payload_digest": hashlib.sha256(payload).hexdigest(),
            "record_count": 1,
            "byte_count": len(payload),
            "created_at": "2026-07-22T00:00:00.000000Z",
            "sealed_at": "2026-07-22T00:00:01.000000Z",
            "expires_at": "2026-07-25T00:00:01.000000Z",
            "segment_digest": "0" * 64,
        }
        metadata["ownership_marker_digest"] = raw_ownership_marker(
            metadata
        )
        metadata["segment_digest"] = canonical_digest(
            metadata,
            "/segment_digest",
        )
        metadata_path.write_bytes(canonicalize_object(metadata))
        metadata_path.with_suffix(".payload").write_bytes(payload)
        return metadata_path.resolve(strict=True)

    def evaluate(self, candidates, *, allow_test_only=False):
        return evaluate_retention_scope(
            self.contract,
            root_bindings=self.roots(),
            candidates=candidates,
            observation_uid=OBSERVATION_UID,
            report_uid=REPORT_UID,
            observed_at=OBSERVED_AT,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            allow_test_only=allow_test_only,
        )

    def test_01_builder_and_readiness_are_byte_equivalent(self) -> None:
        builder._check()
        readiness = builder.build_readiness()
        stored = parse_json_bytes(builder.OUTPUT_PATH.read_bytes())
        self.assertEqual(readiness, stored)
        self.assertEqual(
            readiness["task_contract"]["completed_task_ids"],
            ["M-060"],
        )
        self.assertEqual(
            readiness["task_contract"]["dependency_task_ids"],
            ["M-003", "M-031"],
        )
        self.assertEqual(
            readiness["next_phase"],
            "MECHANISM_MANAGED_RAW_72H_POLICY",
        )
        self.assertFalse(
            readiness["root_lifecycle_contract"][
                "destructive_action_permitted"
            ]
        )
        self.assertFalse(builder.VERSION_PATH.exists())

    def test_02_only_managed_raw_reaches_m061(self) -> None:
        protected_paths = []
        for root, name in (
            (self.skill_source, "skill-private.txt"),
            (self.run_source, "run-private.txt"),
            (self.legacy, "legacy-private.txt"),
        ):
            path = root / name
            path.write_bytes(b"not json and must not be read")
            protected_paths.append(path.resolve(strict=True))
        queue_path = self.public_queue / "queue-item.json"
        queue_path.write_bytes(b"public safe queue, not raw")
        managed = self.raw_segment(number=1)
        before = {
            path: (path.read_bytes(), path.stat().st_mtime_ns)
            for path in protected_paths
        }
        result = self.evaluate(
            (
                CandidateRequest("legacy-candidate", protected_paths[2]),
                CandidateRequest("managed-candidate", managed),
                CandidateRequest(
                    "public-queue-candidate",
                    queue_path.resolve(strict=True),
                ),
                CandidateRequest("run-source-candidate", protected_paths[1]),
                CandidateRequest(
                    "skill-source-candidate",
                    protected_paths[0],
                ),
            ),
            allow_test_only=True,
        )
        self.assertEqual(
            result.selected_candidate_refs,
            ("managed-candidate",),
        )
        report = parse_json_bytes(result.canonical_report_bytes)
        self.assertEqual(report["protected_input_count"], 3)
        self.assertEqual(report["legacy_input_count"], 1)
        self.assertEqual(report["public_queue_input_count"], 1)
        self.assertEqual(report["protected_selected_count"], 0)
        self.assertEqual(report["legacy_selected_count"], 0)
        self.assertEqual(report["public_queue_selected_count"], 0)
        self.assertEqual(report["protected_delete_budget"], 0)
        self.assertFalse(report["time_evaluation_performed"])
        self.assertFalse(report["destructive_action_performed"])
        for path, snapshot in before.items():
            self.assertEqual(
                (path.read_bytes(), path.stat().st_mtime_ns),
                snapshot,
            )

    def test_03_protected_and_queue_content_is_never_parsed(self) -> None:
        protected = self.legacy / "duplicate-keys.json"
        protected.write_bytes(b'{"raw":"secret","raw":"still-secret"}')
        queue = self.public_queue / "malformed.json"
        queue.write_bytes(b"{not-json")
        result = self.evaluate(
            (
                CandidateRequest(
                    "legacy-candidate",
                    protected.resolve(strict=True),
                ),
                CandidateRequest(
                    "queue-candidate",
                    queue.resolve(strict=True),
                ),
            )
        )
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        self.assertTrue(
            all(
                row["metadata_read"] is False
                for row in observation["candidate_evaluations"]
            )
        )
        self.assertEqual(result.selected_candidate_refs, ())

    def test_04_default_disabled_and_uncertified_modes_fail_closed(self) -> None:
        disabled = self.raw_segment(number=1, mode="DISABLED")
        test_only = self.raw_segment(number=2, mode="TEST_ONLY")
        result = self.evaluate(
            (
                CandidateRequest("disabled-candidate", disabled),
                CandidateRequest("test-candidate", test_only),
            )
        )
        self.assertEqual(result.selected_candidate_refs, ())
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        self.assertEqual(
            [row["reason_code"] for row in observation["candidate_evaluations"]],
            ["PERSISTENCE_DISABLED", "TEST_ONLY_NOT_AUTHORIZED"],
        )
        certified = self.raw_segment(
            number=3,
            mode="ENABLED_AFTER_CERTIFICATION",
        )
        with self.assertRaisesRegex(
            RootLifecycleError,
            "MANAGED_RAW_CERTIFICATION_NOT_IMPLEMENTED_M060",
        ):
            self.evaluate(
                (CandidateRequest("certified-candidate", certified),)
            )

    def test_05_symlink_root_candidate_and_special_file_fail_closed(
        self,
    ) -> None:
        root_link = self.base / "staging-link"
        root_link.symlink_to(self.staging, target_is_directory=True)
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_SYMLINK_FORBIDDEN",
        ):
            evaluate_retention_scope(
                self.contract,
                root_bindings=(
                    RootBinding("linked-root", "STAGING", root_link),
                ),
                candidates=(),
                observation_uid=OBSERVATION_UID,
                report_uid=REPORT_UID,
                observed_at=OBSERVED_AT,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )
        outside = self.base / "outside.json"
        outside.write_bytes(b"outside")
        candidate_link = self.staging / "candidate-link.json"
        candidate_link.symlink_to(outside)
        with self.assertRaisesRegex(
            RootLifecycleError,
            "CANDIDATE_SYMLINK_FORBIDDEN",
        ):
            self.evaluate(
                (
                    CandidateRequest(
                        "linked-candidate",
                        candidate_link,
                    ),
                )
            )
        directory_candidate = self.staging / "directory.json"
        directory_candidate.mkdir()
        with self.assertRaisesRegex(
            RootLifecycleError,
            "CANDIDATE_NOT_REGULAR_FILE",
        ):
            self.evaluate(
                (
                    CandidateRequest(
                        "directory-candidate",
                        directory_candidate.resolve(strict=True),
                    ),
                )
            )

    def test_06_sibling_prefix_escape_and_overlap_fail_closed(self) -> None:
        sibling = self.base / "staging-copy"
        sibling.mkdir()
        outside = sibling / "segment.json"
        outside.write_bytes(b"{}")
        with self.assertRaisesRegex(
            RootLifecycleError,
            "CANDIDATE_OUTSIDE_DECLARED_ROOTS",
        ):
            self.evaluate(
                (
                    CandidateRequest(
                        "sibling-candidate",
                        outside.resolve(strict=True),
                    ),
                )
            )
        nested = self.staging / "nested"
        nested.mkdir()
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_OVERLAP_FORBIDDEN",
        ):
            evaluate_retention_scope(
                self.contract,
                root_bindings=(
                    RootBinding(
                        "managed-staging",
                        "STAGING",
                        self.staging.resolve(strict=True),
                    ),
                    RootBinding(
                        "nested-state",
                        "PUBLIC_QUEUE",
                        nested.resolve(strict=True),
                    ),
                ),
                candidates=(),
                observation_uid=OBSERVATION_UID,
                report_uid=REPORT_UID,
                observed_at=OBSERVED_AT,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )

    def test_07_marker_payload_and_schema_tamper_fail_closed(self) -> None:
        marker_path = self.raw_segment(number=1)
        marker = parse_json_bytes(marker_path.read_bytes())
        marker["ownership_marker_digest"] = "f" * 64
        marker["segment_digest"] = canonical_digest(
            marker,
            "/segment_digest",
        )
        marker_path.write_bytes(canonicalize_object(marker))
        with self.assertRaisesRegex(
            RootLifecycleError,
            "RAW_OWNERSHIP_MARKER_INVALID",
        ):
            self.evaluate(
                (CandidateRequest("marker-candidate", marker_path),),
                allow_test_only=True,
            )

        payload_path = self.raw_segment(number=2)
        payload_path.with_suffix(".payload").write_bytes(b"tampered")
        with self.assertRaisesRegex(
            RootLifecycleError,
            "RAW_PAYLOAD_EVIDENCE_INVALID",
        ):
            self.evaluate(
                (CandidateRequest("payload-candidate", payload_path),),
                allow_test_only=True,
            )

        malformed = self.staging / "malformed.json"
        malformed.write_bytes(b'{"a":1,"a":2}')
        malformed.with_suffix(".payload").write_bytes(b"x")
        with self.assertRaisesRegex(
            RootLifecycleError,
            "RAW_METADATA_JSON_INVALID",
        ):
            self.evaluate(
                (CandidateRequest("malformed-candidate", malformed),),
                allow_test_only=True,
            )

    def test_08_schema_trust_and_rebinding_fail_closed(self) -> None:
        altered = copy.deepcopy(self.raw_schema)
        altered["title"] = "attacker replacement"
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_LIFECYCLE_SCHEMA_TRUST_MISMATCH",
        ):
            build_root_lifecycle_contract(
                self.candidate,
                altered,
                builder.RAW_SEGMENT_SCHEMA_SHA256,
                self.observation_schema,
                canonical_digest(self.observation_schema),
                self.report_schema,
                canonical_digest(self.report_schema),
            )
        first = build_root_lifecycle_contract(
            self.candidate,
            self.raw_schema,
            builder.RAW_SEGMENT_SCHEMA_SHA256,
            self.observation_schema,
            canonical_digest(self.observation_schema),
            self.report_schema,
            canonical_digest(self.report_schema),
        )
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_LIFECYCLE_SCHEMA_REBIND_FORBIDDEN",
        ):
            build_root_lifecycle_contract(
                first,
                self.raw_schema,
                builder.RAW_SEGMENT_SCHEMA_SHA256,
                self.observation_schema,
                canonical_digest(self.observation_schema),
                self.report_schema,
                canonical_digest(self.report_schema),
            )

    def test_09_observation_and_report_are_recomputed(self) -> None:
        managed = self.raw_segment(number=1)
        result = self.evaluate(
            (CandidateRequest("managed-candidate", managed),),
            allow_test_only=True,
        )
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        report = parse_json_bytes(result.canonical_report_bytes)
        validate_selection_report(
            self.contract,
            observation,
            report,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
        )
        forged_report = copy.deepcopy(report)
        forged_report["selected_count"] = 0
        forged_report["evidence_bundle_digest"] = canonical_digest(
            forged_report,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_LIFECYCLE_REPORT_RECOMPUTATION_MISMATCH",
        ):
            validate_selection_report(
                self.contract,
                observation,
                forged_report,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )
        forged_observation = copy.deepcopy(observation)
        forged_observation["candidate_evaluations"][0][
            "root_class"
        ] = "LEGACY_DATA"
        forged_observation["candidate_evaluations"][0][
            "lifecycle_class"
        ] = "PROTECTED_LOCAL_DATA"
        forged_observation["evidence_bundle_digest"] = canonical_digest(
            forged_observation,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            RootLifecycleError,
            "ROOT_LIFECYCLE_CANDIDATE_ROOT_MISMATCH",
        ):
            recompute_selection_report(
                self.contract,
                forged_observation,
                report_uid=REPORT_UID,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )

    def test_10_public_evidence_contains_no_paths_or_private_values(
        self,
    ) -> None:
        payload = b"private-value-never-published"
        managed = self.raw_segment(number=1, payload=payload)
        result = self.evaluate(
            (CandidateRequest("managed-candidate", managed),),
            allow_test_only=True,
        )
        combined = (
            result.canonical_observation_bytes
            + result.canonical_report_bytes
        )
        self.assertNotIn(str(self.base).encode("utf-8"), combined)
        self.assertNotIn(payload, combined)
        metadata = parse_json_bytes(managed.read_bytes())
        self.assertNotIn(
            metadata["payload_digest"].encode("ascii"),
            combined,
        )
        observation = parse_json_bytes(
            result.canonical_observation_bytes
        )
        self.assertTrue(
            all(
                row["private_path_serialized"] is False
                for row in observation["root_bindings"]
            )
        )


if __name__ == "__main__":
    unittest.main()
