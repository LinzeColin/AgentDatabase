from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator
from referencing import Registry, Resource

from CodexSkills.governance.release.foundations import (
    BOOTSTRAP_SRV,
    FOUNDATION_INTERFACE_SCHEMA_ID,
    LOCKED_MAJOR_TRIGGER_CODES,
    MATERIAL_TRIGGER_CODES,
    RELEASE_HANDOFF_SCHEMA_ID,
    REQUIRED_RELEASE_GATES,
    ROUTINE_TRIGGER_CODES,
    REVISION_LEDGER_SCHEMA_ID,
    PolicyClaim,
    ReleaseContractError,
    abandon_revision,
    assert_impact_policy_coverage,
    assert_no_policy_conflicts,
    build_release_handoff,
    classify_impact,
    compare_srv,
    detect_policy_conflicts,
    format_srv,
    increment_srv,
    new_revision_ledger,
    parse_srv,
    reserve_revision,
    settle_revision,
    validate_release_handoff,
    validate_revision_ledger,
)
from CodexSkills.governance.tools.build_release_foundations import (
    INTERFACE_PATH,
    VERSION_POLICY_PATH,
    build_interface,
    render_interface,
    validate_interface,
)
from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)
ROOT = Path(__file__).resolve().parents[3]
GOVERNANCE = ROOT / "CodexSkills" / "governance"
SCHEMA_DIR = GOVERNANCE / "release" / "schemas"
COMMON_SCHEMA = GOVERNANCE / "schemas" / "common-definitions.schema.json"
sys.path.insert(0, str(GOVERNANCE / "tools"))
from validate_mechanism import scan_public_value  # noqa: E402


PUBLIC_VALUE_POLICY = (
    GOVERNANCE / "policies-v2" / "public-value-policy.v2.json"
)
HEAD_1 = "sha1:" + "1" * 40
HEAD_2 = "sha1:" + "2" * 40
TX_1 = "autx_" + "0" * 26
TX_2 = "autx_" + "1" * 26
TX_3 = "autx_" + "2" * 26
TIME_1 = "2026-07-26T00:00:00.000000Z"
TIME_2 = "2026-07-26T00:00:01.000000Z"
DIGEST_A = "a" * 64
BUNDLE_DIGEST = "b" * 64


def _load(path: Path):
    return parse_json_bytes(path.read_bytes())


def _version_policy():
    return _load(VERSION_POLICY_PATH)


def _schema_documents():
    documents = [_load(COMMON_SCHEMA)]
    documents.extend(_load(path) for path in sorted(SCHEMA_DIR.glob("*.json")))
    return {document["$id"]: document for document in documents}


def _assert_schema_valid(test: unittest.TestCase, schema_id: str, value):
    documents = _schema_documents()
    registry = Registry().with_resources(
        (key, Resource.from_contents(document))
        for key, document in documents.items()
    )
    errors = list(
        Draft202012Validator(
            documents[schema_id],
            registry=registry,
        ).iter_errors(value)
    )
    test.assertEqual([], errors)


def _gates(status: str = "PASS"):
    rows = []
    for code in REQUIRED_RELEASE_GATES:
        rows.append(
            {
                "gate_code": code,
                "status": status,
                "evidence_digest": DIGEST_A if status != "UNKNOWN" else None,
                "reason_code": None if status == "PASS" else "GATE_NOT_READY",
            }
        )
    return rows


class ReleaseFoundationTests(unittest.TestCase):
    def test_srv_parser_increment_and_unbounded_counter(self):
        self.assertEqual(2, parse_srv(BOOTSTRAP_SRV))
        self.assertEqual("v0.0.0.1000", increment_srv("v0.0.0.999"))
        self.assertEqual(1, compare_srv("v0.0.0.1000", "v0.0.0.999"))
        self.assertEqual(-1, compare_srv("v0.0.0.2", "v0.0.0.3"))
        self.assertEqual(0, compare_srv("v0.0.0.3", "v0.0.0.3"))
        self.assertEqual("v0.0.0.12345678901234567890", format_srv(12345678901234567890))
        for value in (
            "0.0.0.3",
            "v0.0.0.0",
            "v0.0.0.03",
            "v1.0.0.3",
            "v0.0.1.3",
            "v0.0.0.-1",
        ):
            with self.subTest(value=value), self.assertRaises(ReleaseContractError):
                parse_srv(value)

    def test_revision_absent_bootstraps_to_three_and_settles_atomically(self):
        initial = new_revision_ledger(None)
        self.assertFalse(initial["version_file_present"])
        self.assertIsNone(initial["committed_srv"])
        reserved = reserve_revision(
            initial,
            transaction_uid=TX_1,
            expected_remote_head=HEAD_1,
            impact="MAJOR",
            trigger_codes=["ACTIVE_BUNDLE_CHANGE"],
            reserved_at=TIME_1,
        )
        self.assertEqual("v0.0.0.3", reserved["allocations"][0]["target_srv"])
        settled = settle_revision(
            reserved,
            transaction_uid=TX_1,
            version_payload=b"v0.0.0.3\n",
            artifact_srv_revisions=["v0.0.0.3", "v0.0.0.3"],
            remote_readback_head=HEAD_2,
            settled_at=TIME_2,
        )
        self.assertEqual("v0.0.0.3", settled["committed_srv"])
        self.assertTrue(settled["version_file_present"])
        self.assertEqual("RESERVED", reserved["allocations"][0]["status"])
        validate_revision_ledger(settled)
        _assert_schema_valid(self, REVISION_LEDGER_SCHEMA_ID, settled)

    def test_abandoned_revision_is_never_reused(self):
        reserved = reserve_revision(
            new_revision_ledger(None),
            transaction_uid=TX_1,
            expected_remote_head=HEAD_1,
            impact="PATCH",
            trigger_codes=["DERIVED_VIEW_REBUILD"],
            reserved_at=TIME_1,
        )
        abandoned = abandon_revision(
            reserved,
            transaction_uid=TX_1,
            reason_code="CRASH_RECOVERY_ABANDONED",
        )
        next_reserved = reserve_revision(
            abandoned,
            transaction_uid=TX_2,
            expected_remote_head=HEAD_1,
            impact="MINOR",
            trigger_codes=["DATASET_EXTENSION"],
            reserved_at=TIME_2,
        )
        self.assertEqual(
            ["v0.0.0.3", "v0.0.0.4"],
            [row["target_srv"] for row in next_reserved["allocations"]],
        )

    def test_revision_failures_do_not_mutate_input_or_partially_settle(self):
        reserved = reserve_revision(
            new_revision_ledger("v0.0.0.999"),
            transaction_uid=TX_1,
            expected_remote_head=HEAD_1,
            impact="MAJOR",
            trigger_codes=["RETENTION_POLICY_CHANGE"],
            reserved_at=TIME_1,
        )
        before = copy.deepcopy(reserved)
        for kwargs in (
            {
                "version_payload": b"v0.0.0.999\n",
                "artifact_srv_revisions": ["v0.0.0.1000"],
                "remote_readback_head": HEAD_2,
            },
            {
                "version_payload": b"v0.0.0.1000\n",
                "artifact_srv_revisions": ["v0.0.0.999"],
                "remote_readback_head": HEAD_2,
            },
            {
                "version_payload": b"v0.0.0.1000\n",
                "artifact_srv_revisions": ["v0.0.0.1000"],
                "remote_readback_head": HEAD_1,
            },
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ReleaseContractError):
                settle_revision(
                    reserved,
                    transaction_uid=TX_1,
                    settled_at=TIME_2,
                    **kwargs,
                )
            self.assertEqual(before, reserved)

    def test_revision_single_flight_and_transaction_reuse_fail_closed(self):
        reserved = reserve_revision(
            new_revision_ledger(None),
            transaction_uid=TX_1,
            expected_remote_head=HEAD_1,
            impact="PATCH",
            trigger_codes=["NON_BEHAVIORAL_DOCUMENTATION"],
            reserved_at=TIME_1,
        )
        with self.assertRaisesRegex(
            ReleaseContractError,
            "REVISION_RESERVATION_ALREADY_OPEN",
        ):
            reserve_revision(
                reserved,
                transaction_uid=TX_2,
                expected_remote_head=HEAD_1,
                impact="PATCH",
                trigger_codes=["DERIVED_VIEW_REBUILD"],
                reserved_at=TIME_2,
            )
        abandoned = abandon_revision(
            reserved,
            transaction_uid=TX_1,
            reason_code="CONTROLLED_ABORT",
        )
        with self.assertRaisesRegex(
            ReleaseContractError,
            "REVISION_TRANSACTION_REUSED",
        ):
            reserve_revision(
                abandoned,
                transaction_uid=TX_1,
                expected_remote_head=HEAD_1,
                impact="PATCH",
                trigger_codes=["DERIVED_VIEW_REBUILD"],
                reserved_at=TIME_2,
            )

    def test_revision_impact_cannot_be_softened_by_caller(self):
        with self.assertRaisesRegex(
            ReleaseContractError,
            "REVISION_IMPACT_TRIGGER_MISMATCH",
        ):
            reserve_revision(
                new_revision_ledger(None),
                transaction_uid=TX_1,
                expected_remote_head=HEAD_1,
                impact="PATCH",
                trigger_codes=["PRIVACY_POLICY_CHANGE"],
                reserved_at=TIME_1,
            )

    def test_impact_classifier_maps_taskpack_vocabulary_without_semver(self):
        policy = _version_policy()
        routine = classify_impact(sorted(ROUTINE_TRIGGER_CODES), policy)
        material = classify_impact(sorted(MATERIAL_TRIGGER_CODES), policy)
        major = classify_impact(
            ["PRIVACY_POLICY_CHANGE", "DERIVED_VIEW_REBUILD"],
            policy,
        )
        self.assertEqual(("PATCH", "ROUTINE"), (routine.canonical_level, routine.taskpack_level))
        self.assertEqual(("MINOR", "MATERIAL"), (material.canonical_level, material.taskpack_level))
        self.assertEqual(("MAJOR", "MAJOR"), (major.canonical_level, major.taskpack_level))
        self.assertFalse(major.policy_coverage_complete)
        self.assertIn(
            "PRIVACY_POLICY_CHANGE",
            major.missing_policy_major_trigger_codes,
        )

    def test_current_v2_policy_fails_locked_major_trigger_coverage(self):
        with self.assertRaisesRegex(
            ReleaseContractError,
            "VERSION_POLICY_MAJOR_TRIGGER_COVERAGE_INCOMPLETE",
        ):
            assert_impact_policy_coverage(_version_policy())
        corrected = copy.deepcopy(_version_policy())
        corrected["major_trigger_codes"] = sorted(LOCKED_MAJOR_TRIGGER_CODES)
        assert_impact_policy_coverage(corrected)
        decision = classify_impact(
            ["NETWORK_OR_PERMISSION_CHANGE"],
            corrected,
        )
        self.assertTrue(decision.policy_coverage_complete)

    def test_unknown_or_duplicate_impact_code_never_softens(self):
        policy = _version_policy()
        with self.assertRaisesRegex(ReleaseContractError, "IMPACT_TRIGGER_UNKNOWN"):
            classify_impact(["UNKNOWN_CHANGE"], policy)
        with self.assertRaisesRegex(ReleaseContractError, "IMPACT_TRIGGER_DUPLICATE"):
            classify_impact(
                ["DERIVED_VIEW_REBUILD", "DERIVED_VIEW_REBUILD"],
                policy,
            )

    def test_policy_precedence_conflict_is_sanitized_and_blocks_write(self):
        secret_a = {"value": "must-not-appear-alpha"}
        secret_b = {"value": "must-not-appear-beta"}
        conflicts = detect_policy_conflicts(
            [
                PolicyClaim(
                    "/privacy/retention",
                    "OWNER_LOCK",
                    "OWNER_DECISIONS",
                    secret_a,
                ),
                PolicyClaim(
                    "/privacy/retention",
                    "EXAMPLE_OR_PDF",
                    "PDF_EXAMPLE",
                    secret_b,
                ),
            ]
        )
        self.assertEqual(1, len(conflicts))
        conflict = conflicts[0]
        self.assertEqual("OWNER_LOCK", conflict["authoritative_source_class"])
        self.assertEqual("MAJOR", conflict["impact"])
        self.assertFalse(conflict["write_permitted"])
        encoded = canonicalize_object(list(conflicts))
        self.assertNotIn(b"must-not-appear-alpha", encoded)
        self.assertNotIn(b"must-not-appear-beta", encoded)
        with self.assertRaisesRegex(
            ReleaseContractError,
            "POLICY_PRECEDENCE_CONFLICT",
        ):
            assert_no_policy_conflicts(
                [
                    PolicyClaim(
                        "/privacy/retention",
                        "OWNER_LOCK",
                        "OWNER_DECISIONS",
                        secret_a,
                    ),
                    PolicyClaim(
                        "/privacy/retention",
                        "EXAMPLE_OR_PDF",
                        "PDF_EXAMPLE",
                        secret_b,
                    ),
                ]
            )

    def test_same_policy_value_across_sources_is_not_a_conflict(self):
        claims = [
            PolicyClaim("/schedule/timezone", source, source, "Australia/Sydney")
            for source in ("OWNER_LOCK", "VALIDATED_CONFIG", "EXAMPLE_OR_PDF")
        ]
        self.assertEqual((), detect_policy_conflicts(claims))
        assert_no_policy_conflicts(claims)
        with self.assertRaisesRegex(
            ReleaseContractError,
            "POLICY_CLAIM_SOURCE_REF_INVALID",
        ):
            detect_policy_conflicts(
                [
                    PolicyClaim(
                        "/schedule/timezone",
                        "OWNER_LOCK",
                        "owner/ref",
                        "Australia/Sydney",
                    ),
                    PolicyClaim(
                        "/schedule/timezone",
                        "VALIDATED_CONFIG",
                        "VERSION_POLICY_V2",
                        "UTC",
                    ),
                ]
            )
        for unsafe_field in (
            "/privacy/absolute.path",
            "/privacy/UPPERCASE",
            "/privacy/~1escaped",
        ):
            with self.subTest(unsafe_field=unsafe_field), self.assertRaisesRegex(
                ReleaseContractError,
                "POLICY_CLAIM_FIELD_INVALID",
            ):
                detect_policy_conflicts(
                    [
                        PolicyClaim(
                            unsafe_field,
                            "OWNER_LOCK",
                            "OWNER_DECISIONS",
                            "A",
                        ),
                        PolicyClaim(
                            unsafe_field,
                            "VALIDATED_CONFIG",
                            "VERSION_POLICY_V2",
                            "B",
                        ),
                    ]
                )

    def test_handoff_stale_context_and_digest_tamper_fail_closed(self):
        handoff = build_release_handoff(
            status="BLOCKED",
            phase="MECHANISM_M0_GOVERNANCE_RUNTIME_FOUNDATIONS",
            srv_revision="v0.0.0.3",
            bundle_digest=BUNDLE_DIGEST,
            expected_remote_head=HEAD_1,
            impact="MAJOR",
            trigger_codes=["PRIVACY_POLICY_CHANGE"],
            policy_conflict_count=1,
            version_policy_major_trigger_coverage_complete=False,
            external_runtime_readiness="NOT_READY",
            schedule_authority_resolved=False,
            gates=_gates("UNKNOWN"),
            residual_risk_codes=["EXTERNAL_STATE_NOT_READY"],
            next_phase="MECHANISM_VERSION_POLICY_V3_DRAFT",
            updated_at=TIME_1,
        )
        _assert_schema_valid(self, RELEASE_HANDOFF_SCHEMA_ID, handoff)
        validate_release_handoff(
            handoff,
            expected_srv_revision="v0.0.0.3",
            expected_bundle_digest=BUNDLE_DIGEST,
            expected_remote_head=HEAD_1,
        )
        public_policy = _load(PUBLIC_VALUE_POLICY)
        scan_public_value(
            handoff,
            {public_policy["policy_id"]: public_policy},
        )
        with self.assertRaisesRegex(
            ReleaseContractError,
            "RELEASE_HANDOFF_MISSING",
        ):
            validate_release_handoff(None)
        cases = (
            ("expected_srv_revision", "v0.0.0.4", "RELEASE_HANDOFF_SRV_STALE"),
            ("expected_bundle_digest", DIGEST_A, "RELEASE_HANDOFF_BUNDLE_STALE"),
            ("expected_remote_head", HEAD_2, "RELEASE_HANDOFF_EXPECTED_HEAD_STALE"),
        )
        for key, value, code in cases:
            with self.subTest(key=key), self.assertRaisesRegex(ReleaseContractError, code):
                validate_release_handoff(handoff, **{key: value})
        tampered = copy.deepcopy(handoff)
        tampered["next_phase"] = "MECHANISM_OTHER_PHASE"
        with self.assertRaisesRegex(
            ReleaseContractError,
            "RELEASE_HANDOFF_DIGEST_MISMATCH",
        ):
            validate_release_handoff(tampered)

    def test_ready_handoff_requires_every_release_gate(self):
        ready = build_release_handoff(
            status="READY_FOR_ACTIVATION",
            phase="MECHANISM_RELEASE_REVIEW",
            srv_revision="v0.0.0.3",
            bundle_digest=BUNDLE_DIGEST,
            expected_remote_head=HEAD_1,
            impact="MAJOR",
            trigger_codes=["ACTIVE_BUNDLE_CHANGE"],
            policy_conflict_count=0,
            version_policy_major_trigger_coverage_complete=True,
            external_runtime_readiness="READY",
            schedule_authority_resolved=True,
            gates=_gates("PASS"),
            residual_risk_codes=[],
            next_phase="MECHANISM_COORDINATED_ACTIVATION",
            updated_at=TIME_1,
        )
        self.assertFalse(ready["activation_forbidden"])
        validate_release_handoff(ready)
        for field, value in (
            ("policy_conflict_count", 1),
            ("version_policy_major_trigger_coverage_complete", False),
            ("external_runtime_readiness", "NOT_READY"),
            ("schedule_authority_resolved", False),
        ):
            kwargs = dict(
                status="READY_FOR_ACTIVATION",
                phase="MECHANISM_RELEASE_REVIEW",
                srv_revision="v0.0.0.3",
                bundle_digest=BUNDLE_DIGEST,
                expected_remote_head=HEAD_1,
                impact="MAJOR",
                trigger_codes=["ACTIVE_BUNDLE_CHANGE"],
                policy_conflict_count=0,
                version_policy_major_trigger_coverage_complete=True,
                external_runtime_readiness="READY",
                schedule_authority_resolved=True,
                gates=_gates("PASS"),
                residual_risk_codes=[],
                next_phase="MECHANISM_COORDINATED_ACTIVATION",
                updated_at=TIME_1,
            )
            kwargs[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(
                ReleaseContractError,
                "RELEASE_HANDOFF_READINESS_MISMATCH",
            ):
                build_release_handoff(**kwargs)

    def test_foundation_interface_is_byte_equivalent_and_non_active(self):
        self.assertEqual(render_interface(), INTERFACE_PATH.read_bytes())
        interface = _load(INTERFACE_PATH)
        self.assertEqual(build_interface(), interface)
        validate_interface(interface)
        _assert_schema_valid(
            self,
            FOUNDATION_INTERFACE_SCHEMA_ID,
            interface,
        )
        self.assertFalse(interface["release_write_permitted"])
        self.assertTrue(interface["activation_forbidden"])
        self.assertTrue(interface["candidate_bundle_unchanged"])
        self.assertFalse((ROOT / "CodexSkills" / "VERSION").exists())
        public_policy = _load(PUBLIC_VALUE_POLICY)
        scan_public_value(
            interface,
            {public_policy["policy_id"]: public_policy},
        )

    def test_foundation_schemas_are_closed_and_not_candidate_members(self):
        interface = build_interface()
        candidate = _load(
            GOVERNANCE / "bundles" / "schema-bundle-manifest.v1.json"
        )
        candidate_ids = {row["id"] for row in candidate["schemas"]}
        foundation_ids = {row["id"] for row in interface["foundation_schemas"]}
        self.assertFalse(candidate_ids.intersection(foundation_ids))
        for schema_id, document in _schema_documents().items():
            Draft202012Validator.check_schema(document)
            if schema_id != _load(COMMON_SCHEMA)["$id"]:
                self.assertFalse(document.get("additionalProperties", True))


if __name__ == "__main__":
    unittest.main()
