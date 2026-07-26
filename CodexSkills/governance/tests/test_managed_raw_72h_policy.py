from __future__ import annotations

import copy
import datetime as dt
import hashlib
import tempfile
import unittest
from pathlib import Path

from CodexSkills.governance.retention.managed_raw_policy import (
    MAX_AGE_SECONDS,
    ManagedRawPolicyError,
    build_managed_raw_policy_contract,
    evaluate_managed_raw_policy,
    receipt_evidence,
    recompute_retention_plan,
    validate_execution_receipt,
    validate_retention_plan,
)
from CodexSkills.governance.retention.root_lifecycle import (
    CandidateRequest,
    RootBinding,
    RootLifecycleError,
    evaluate_retention_scope,
    raw_ownership_marker,
)
from CodexSkills.governance.tools import (
    build_managed_raw_72h_policy as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    canonicalize_object,
    parse_json_bytes,
)


OBSERVATION_UID = "mro_01ARZ3NDEKTSV4RRFFQ69G5FAV"
PLAN_UID = "mrp_01ARZ3NDEKTSV4RRFFQ69G5FAW"
M060_OBSERVATION_UID = "rlo_01ARZ3NDEKTSV4RRFFQ69G5FAV"
M060_REPORT_UID = "rlr_01ARZ3NDEKTSV4RRFFQ69G5FAW"
FIXED_NOW = dt.datetime(
    2026,
    7,
    26,
    0,
    0,
    0,
    tzinfo=dt.timezone.utc,
)


def _format(value: dt.datetime) -> str:
    return value.astimezone(dt.timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%S.%fZ"
    )


class ManagedRaw72HourPolicyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.m060_bundle = builder._trusted_m060_bundle()
        cls.observation_schema = builder.build_observation_schema()
        cls.plan_schema = builder.build_plan_schema()
        cls.contract = build_managed_raw_policy_contract(
            cls.m060_bundle,
            cls.observation_schema,
            canonical_digest(cls.observation_schema),
            cls.plan_schema,
            canonical_digest(cls.plan_schema),
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
        age_seconds: int,
        number: int,
        mode: str = "TEST_ONLY",
        sealed_delay_seconds: int = 0,
        expires_from_sealed: bool = False,
    ):
        created = FIXED_NOW - dt.timedelta(seconds=age_seconds)
        sealed = created + dt.timedelta(seconds=sealed_delay_seconds)
        expires_anchor = sealed if expires_from_sealed else created
        expires = expires_anchor + dt.timedelta(hours=72)
        payload = ("synthetic managed payload " + str(number)).encode(
            "ascii"
        )
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
            "created_at": _format(created),
            "sealed_at": _format(sealed),
            "expires_at": _format(expires),
            "segment_digest": "0" * 64,
        }
        metadata["ownership_marker_digest"] = raw_ownership_marker(
            metadata
        )
        metadata["segment_digest"] = canonical_digest(
            metadata,
            "/segment_digest",
        )
        path = self.staging / ("segment-" + str(number) + ".json")
        path.write_bytes(canonicalize_object(metadata))
        path.with_suffix(".payload").write_bytes(payload)
        return path.resolve(strict=True), metadata

    def m060_selection(self, segments):
        requests = tuple(
            CandidateRequest(candidate_ref, path)
            for candidate_ref, path, _metadata in segments
        )
        result = evaluate_retention_scope(
            self.contract,
            root_bindings=self.roots(),
            candidates=requests,
            observation_uid=M060_OBSERVATION_UID,
            report_uid=M060_REPORT_UID,
            observed_at=_format(FIXED_NOW),
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            allow_test_only=True,
        )
        return (
            parse_json_bytes(result.canonical_observation_bytes),
            parse_json_bytes(result.canonical_report_bytes),
            {
                candidate_ref: metadata
                for candidate_ref, _path, metadata in segments
            },
        )

    def evaluate(
        self,
        segments,
        *,
        observed_at=FIXED_NOW,
        recovery_cycle=False,
        last_runtime_available_at=None,
    ):
        m060_observation, m060_report, metadata = self.m060_selection(
            segments
        )
        result = evaluate_managed_raw_policy(
            self.contract,
            m060_observation=m060_observation,
            m060_report=m060_report,
            metadata_by_candidate_ref=metadata,
            observation_uid=OBSERVATION_UID,
            plan_uid=PLAN_UID,
            observed_at=_format(observed_at),
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            recovery_cycle=recovery_cycle,
            last_runtime_available_at=(
                _format(last_runtime_available_at)
                if last_runtime_available_at is not None
                else None
            ),
        )
        return (
            result,
            parse_json_bytes(result.canonical_observation_bytes),
            parse_json_bytes(result.canonical_plan_bytes),
            m060_observation,
            m060_report,
            metadata,
        )

    def receipt(
        self,
        observation,
        plan,
        candidate_ref,
        *,
        failed_reprojection=False,
    ):
        observed_row = next(
            row
            for row in observation["candidate_observations"]
            if row["candidate_ref"] == candidate_ref
        )
        planned_row = next(
            row
            for row in plan["actions"]
            if row["candidate_ref"] == candidate_ref
        )
        breach = planned_row["ttl_breach"]
        receipt = {
            "schema_version": builder.RETENTION_RECEIPT_SCHEMA_ID,
            "protocol_revision": builder.PROTOCOL_REVISION,
            "bundle_digest": builder.CANDIDATE_BUNDLE_DIGEST,
            "receipt_uid": "rtr_01ARZ3NDEKTSV4RRFFQ69G5FAX",
            "retention_action_uid": (
                "rta_01ARZ3NDEKTSV4RRFFQ69G5FAY"
            ),
            "auto_transaction_uid": (
                "atx_01ARZ3NDEKTSV4RRFFQ69G5FAZ"
            ),
            "executed_at": observation["observed_at"],
            "cutoff_at": observed_row["expires_at"],
            "clock_basis": "UTC_WALL_CLOCK",
            "scope": "MANAGED_RAW",
            "action": (
                "OFFLINE_TTL_BREACH_CLEANUP"
                if breach
                else "DELETE_OWNED_SEGMENT"
            ),
            "retention_policy_id": builder.RETENTION_POLICY_ID,
            "policy_snapshot_digest": canonical_digest(
                self.contract.policies[builder.RETENTION_POLICY_ID]
            ),
            "selected_count": 1,
            "selected_bytes": observed_row["byte_count"],
            "affected_count": 1,
            "affected_bytes": observed_row["byte_count"],
            "protected_candidate_count": 0,
            "legacy_candidate_count": 0,
            "reprojection_status": (
                "FAILED_GAP_RECORDED"
                if failed_reprojection
                else "SUCCEEDED"
            ),
            "offline_duration_seconds": (
                observation["offline_duration_seconds"] if breach else 0
            ),
            "ttl_breach": breach,
            "history_rewrite_performed": False,
            "hard_delete_claimed": False,
            "evidence_digest": canonical_digest(
                receipt_evidence(
                    observation,
                    plan,
                    candidate_ref,
                )
            ),
            "receipt_digest": "0" * 64,
        }
        if breach:
            receipt["gap_code"] = "OFFLINE_TTL_BREACH"
        elif failed_reprojection:
            receipt["gap_code"] = "RAW_EXPIRED_UNPUBLISHED"
        receipt["receipt_digest"] = canonical_digest(
            receipt,
            "/receipt_digest",
        )
        return receipt

    def test_01_builder_and_readiness_are_byte_equivalent(self) -> None:
        builder._check()
        readiness = builder.build_readiness()
        stored = parse_json_bytes(builder.OUTPUT_PATH.read_bytes())
        self.assertEqual(readiness, stored)
        self.assertEqual(
            readiness["task_contract"]["completed_task_ids"],
            ["M-061"],
        )
        self.assertEqual(
            readiness["next_phase"],
            "MECHANISM_PUBLIC_SAFE_QUEUE_LIFECYCLE",
        )
        self.assertFalse(readiness["real_execution_permitted"])
        self.assertFalse(builder.VERSION_PATH.exists())

    def test_02_all_taskpack_clock_stages_are_exact(self) -> None:
        ages = (
            (0, "PROJECT_IMMEDIATELY"),
            (24 * 3600, "WARNING_24H"),
            (48 * 3600, "CRITICAL_48H"),
            (60 * 3600, "EMERGENCY_CATCH_UP_60H"),
            (72 * 3600 - 1, "EMERGENCY_CATCH_UP_60H"),
            (72 * 3600, "HARD_EXPIRY_72H"),
        )
        segments = []
        expected = {}
        for number, (age, stage) in enumerate(ages, start=1):
            path, metadata = self.raw_segment(
                age_seconds=age,
                number=number,
            )
            ref = "managed-" + str(number)
            segments.append((ref, path, metadata))
            expected[ref] = stage
        result, observation, plan, *_rest = self.evaluate(segments)
        self.assertEqual(
            {
                row["candidate_ref"]: row["stage"]
                for row in observation["candidate_observations"]
            },
            expected,
        )
        self.assertEqual(len(result.keep_candidate_refs), 5)
        self.assertEqual(result.expire_candidate_refs, ("managed-6",))
        self.assertEqual(plan["keep_count"], 5)
        self.assertEqual(plan["expire_count"], 1)

    def test_03_71_59_59_keeps_and_72_00_00_expires(self) -> None:
        before_path, before = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS - 1,
            number=1,
        )
        exact_path, exact = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=2,
        )
        result, observation, plan, *_rest = self.evaluate(
            (
                ("before-boundary", before_path, before),
                ("exact-boundary", exact_path, exact),
            )
        )
        self.assertEqual(
            result.keep_candidate_refs,
            ("before-boundary",),
        )
        self.assertEqual(
            result.expire_candidate_refs,
            ("exact-boundary",),
        )
        by_ref = {
            row["candidate_ref"]: row for row in plan["actions"]
        }
        self.assertEqual(
            by_ref["before-boundary"]["decision"],
            "KEEP",
        )
        self.assertEqual(
            by_ref["exact-boundary"]["decision"],
            "EXPIRE",
        )
        self.assertFalse(by_ref["exact-boundary"]["ttl_breach"])
        self.assertTrue(
            by_ref["exact-boundary"]["execution_receipt_required"]
        )
        self.assertFalse(
            by_ref["exact-boundary"]["delete_authority_granted"]
        )
        self.assertFalse(
            by_ref["before-boundary"][
                "unpublished_gap_required_if_reprojection_fails"
            ]
        )
        self.assertTrue(
            by_ref["exact-boundary"][
                "unpublished_gap_required_if_reprojection_fails"
            ]
        )
        self.assertFalse(observation["destructive_action_performed"])

    def test_04_created_at_is_anchor_and_seal_delay_never_extends_ttl(
        self,
    ) -> None:
        valid_path, valid = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
            sealed_delay_seconds=60,
        )
        result, *_rest = self.evaluate(
            (("created-anchor", valid_path, valid),)
        )
        self.assertEqual(
            result.expire_candidate_refs,
            ("created-anchor",),
        )
        invalid_path, invalid = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=2,
            sealed_delay_seconds=60,
            expires_from_sealed=True,
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_EXPIRES_NOT_CREATED_PLUS_72H",
        ):
            self.evaluate(
                (("sealed-anchor-forbidden", invalid_path, invalid),)
            )

    def test_05_strict_utc_and_time_order_fail_closed(self) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
        )
        m060_observation, m060_report, by_ref = self.m060_selection(
            (("managed-candidate", path, metadata),)
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_OBSERVED_AT_INVALID",
        ):
            evaluate_managed_raw_policy(
                self.contract,
                m060_observation=m060_observation,
                m060_report=m060_report,
                metadata_by_candidate_ref=by_ref,
                observation_uid=OBSERVATION_UID,
                plan_uid=PLAN_UID,
                observed_at="2026-07-26T10:00:00.000000+10:00",
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )
        altered = copy.deepcopy(metadata)
        altered["sealed_at"] = _format(
            FIXED_NOW - dt.timedelta(hours=73)
        )
        altered["segment_digest"] = canonical_digest(
            altered,
            "/segment_digest",
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_SEGMENT_TIME_ORDER_INVALID",
        ):
            evaluate_managed_raw_policy(
                self.contract,
                m060_observation=m060_observation,
                m060_report=m060_report,
                metadata_by_candidate_ref={
                    "managed-candidate": altered,
                },
                observation_uid=OBSERVATION_UID,
                plan_uid=PLAN_UID,
                observed_at=_format(FIXED_NOW),
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )

    def test_06_default_and_uncertified_persistence_never_execute(
        self,
    ) -> None:
        disabled_path, disabled = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
            mode="DISABLED",
        )
        result = evaluate_retention_scope(
            self.contract,
            root_bindings=self.roots(),
            candidates=(
                CandidateRequest("disabled-candidate", disabled_path),
            ),
            observation_uid=M060_OBSERVATION_UID,
            report_uid=M060_REPORT_UID,
            observed_at=_format(FIXED_NOW),
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            allow_test_only=True,
        )
        self.assertEqual(result.selected_candidate_refs, ())
        enabled_path, _enabled = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=2,
            mode="ENABLED_AFTER_CERTIFICATION",
        )
        with self.assertRaisesRegex(
            RootLifecycleError,
            "MANAGED_RAW_CERTIFICATION_NOT_IMPLEMENTED_M060",
        ):
            evaluate_retention_scope(
                self.contract,
                root_bindings=self.roots(),
                candidates=(
                    CandidateRequest(
                        "uncertified-candidate",
                        enabled_path,
                    ),
                ),
                observation_uid=M060_OBSERVATION_UID,
                report_uid=M060_REPORT_UID,
                observed_at=_format(FIXED_NOW),
                expected_bundle_digest=(
                    builder.CANDIDATE_BUNDLE_DIGEST
                ),
                allow_test_only=True,
            )

    def test_07_overdue_requires_offline_recovery_evidence(self) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS + 1,
            number=1,
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_OVERDUE_REQUIRES_OFFLINE_GAP_EVIDENCE",
        ):
            self.evaluate(
                (("overdue", path, metadata),)
            )
        result, observation, plan, *_rest = self.evaluate(
            (("overdue", path, metadata),),
            recovery_cycle=True,
            last_runtime_available_at=FIXED_NOW
            - dt.timedelta(hours=80),
        )
        self.assertEqual(result.expire_candidate_refs, ("overdue",))
        self.assertEqual(plan["ttl_breach_count"], 1)
        action = plan["actions"][0]
        self.assertTrue(action["offline_gap_receipt_required"])
        self.assertEqual(
            action["action_order"][0],
            "RECORD_OFFLINE_TTL_BREACH",
        )
        self.assertGreater(observation["offline_duration_seconds"], 0)

    def test_08_exact_expiry_receipt_binds_success_or_gap(self) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
        )
        (
            _result,
            observation,
            plan,
            m060_observation,
            m060_report,
            _metadata,
        ) = self.evaluate((("exact-expiry", path, metadata),))
        success = self.receipt(
            observation,
            plan,
            "exact-expiry",
        )
        validate_execution_receipt(
            self.contract,
            m060_observation,
            m060_report,
            observation,
            plan,
            "exact-expiry",
            success,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
        )
        gap = self.receipt(
            observation,
            plan,
            "exact-expiry",
            failed_reprojection=True,
        )
        validate_execution_receipt(
            self.contract,
            m060_observation,
            m060_report,
            observation,
            plan,
            "exact-expiry",
            gap,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
        )

    def test_09_offline_breach_receipt_is_mandatory_and_exact(self) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS + 1,
            number=1,
        )
        (
            _result,
            observation,
            plan,
            m060_observation,
            m060_report,
            _metadata,
        ) = self.evaluate(
            (("offline-breach", path, metadata),),
            recovery_cycle=True,
            last_runtime_available_at=FIXED_NOW
            - dt.timedelta(hours=80),
        )
        receipt = self.receipt(
            observation,
            plan,
            "offline-breach",
        )
        validate_execution_receipt(
            self.contract,
            m060_observation,
            m060_report,
            observation,
            plan,
            "offline-breach",
            receipt,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
        )
        missing_gap = copy.deepcopy(receipt)
        del missing_gap["gap_code"]
        missing_gap["receipt_digest"] = canonical_digest(
            missing_gap,
            "/receipt_digest",
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_BREACH_RECEIPT_INVALID",
        ):
            validate_execution_receipt(
                self.contract,
                m060_observation,
                m060_report,
                observation,
                plan,
                "offline-breach",
                missing_gap,
                expected_bundle_digest=(
                    builder.CANDIDATE_BUNDLE_DIGEST
                ),
            )

    def test_10_forged_observation_plan_and_selection_fail_closed(
        self,
    ) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS - 1,
            number=1,
        )
        _result, observation, plan, m060_observation, m060_report, by_ref = (
            self.evaluate(
                (("managed-candidate", path, metadata),)
            )
        )
        forged_observation = copy.deepcopy(observation)
        forged_observation["candidate_observations"][0][
            "elapsed_microseconds"
        ] = MAX_AGE_SECONDS * 1_000_000
        forged_observation["evidence_bundle_digest"] = canonical_digest(
            forged_observation,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_OBSERVATION_RECOMPUTATION_MISMATCH",
        ):
            recompute_retention_plan(
                self.contract,
                forged_observation,
                plan_uid=PLAN_UID,
                expected_bundle_digest=(
                    builder.CANDIDATE_BUNDLE_DIGEST
                ),
            )
        forged_plan = copy.deepcopy(plan)
        forged_plan["actions"][0]["decision"] = "EXPIRE"
        forged_plan["evidence_bundle_digest"] = canonical_digest(
            forged_plan,
            "/evidence_bundle_digest",
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_PLAN_RECOMPUTATION_MISMATCH",
        ):
            validate_retention_plan(
                self.contract,
                observation,
                forged_plan,
                expected_bundle_digest=(
                    builder.CANDIDATE_BUNDLE_DIGEST
                ),
            )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_METADATA_SELECTION_SET_MISMATCH",
        ):
            evaluate_managed_raw_policy(
                self.contract,
                m060_observation=m060_observation,
                m060_report=m060_report,
                metadata_by_candidate_ref={
                    **by_ref,
                    "extra-candidate": metadata,
                },
                observation_uid=OBSERVATION_UID,
                plan_uid=PLAN_UID,
                observed_at=_format(FIXED_NOW),
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
            )

    def test_11_receipt_counts_cutoff_and_evidence_are_recomputed(
        self,
    ) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
        )
        (
            _result,
            observation,
            plan,
            m060_observation,
            m060_report,
            _metadata,
        ) = self.evaluate((("exact-expiry", path, metadata),))
        for field, value in (
            ("affected_count", 0),
            ("cutoff_at", "2026-07-25T23:59:59.000000Z"),
            ("evidence_digest", "f" * 64),
        ):
            receipt = self.receipt(
                observation,
                plan,
                "exact-expiry",
            )
            receipt[field] = value
            receipt["receipt_digest"] = canonical_digest(
                receipt,
                "/receipt_digest",
            )
            with self.assertRaises(ManagedRawPolicyError):
                validate_execution_receipt(
                    self.contract,
                    m060_observation,
                    m060_report,
                    observation,
                    plan,
                    "exact-expiry",
                    receipt,
                    expected_bundle_digest=(
                        builder.CANDIDATE_BUNDLE_DIGEST
                    ),
                )

    def test_12_policy_is_public_safe_and_non_mutating(self) -> None:
        protected = self.legacy / "private-source.txt"
        protected.write_bytes(b"must remain byte-identical")
        before = (
            protected.read_bytes(),
            protected.stat().st_mtime_ns,
        )
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
        )
        _result, observation, plan, *_rest = self.evaluate(
            (("managed-candidate", path, metadata),)
        )
        self.assertEqual(
            before,
            (
                protected.read_bytes(),
                protected.stat().st_mtime_ns,
            ),
        )
        self.assertNotIn(
            str(self.base),
            canonicalize_object(
                {"observation": observation, "plan": plan}
            ).decode("utf-8"),
        )
        self.assertFalse(plan["real_execution_permitted"])
        self.assertFalse(plan["receipt_emitted"])
        self.assertFalse(plan["canonical_publication_permitted"])
        self.assertTrue(path.exists())
        self.assertTrue(path.with_suffix(".payload").exists())

    def test_13_receipt_cannot_detach_from_m060_scope_proof(self) -> None:
        path, metadata = self.raw_segment(
            age_seconds=MAX_AGE_SECONDS,
            number=1,
        )
        (
            _result,
            observation,
            _plan,
            m060_observation,
            m060_report,
            _metadata,
        ) = self.evaluate((("exact-expiry", path, metadata),))
        forged_observation = copy.deepcopy(observation)
        forged_observation["m060_selection_report_ref"][
            "artifact_digest"
        ] = "f" * 64
        forged_observation["evidence_bundle_digest"] = canonical_digest(
            forged_observation,
            "/evidence_bundle_digest",
        )
        forged_plan = recompute_retention_plan(
            self.contract,
            forged_observation,
            plan_uid=PLAN_UID,
            expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
        )
        forged_receipt = self.receipt(
            forged_observation,
            forged_plan,
            "exact-expiry",
        )
        with self.assertRaisesRegex(
            ManagedRawPolicyError,
            "MANAGED_RAW_M060_OBSERVATION_BINDING_MISMATCH",
        ):
            validate_execution_receipt(
                self.contract,
                m060_observation,
                m060_report,
                forged_observation,
                forged_plan,
                "exact-expiry",
                forged_receipt,
                expected_bundle_digest=(
                    builder.CANDIDATE_BUNDLE_DIGEST
                ),
            )
