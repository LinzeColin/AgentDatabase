"""Regression gates for Mechanism M-046 Failure-to-Test conversion."""

from __future__ import annotations

import copy
import inspect
import unittest

from CodexSkills.governance.evaluation import failure_to_test as policy
from CodexSkills.governance.evaluation.failure_to_test import (
    FailureToTestError,
    convert_confirmed_incident,
    validate_confirmed_incident,
    validate_regression_case,
)
from CodexSkills.governance.tools import build_failure_to_test as builder
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    scan_public_value,
)


class FailureToTestTests(unittest.TestCase):
    """Confirmed failures become public-safe regression metadata only."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        cls.incident = parse_json_bytes(
            cls.documents[builder.INCIDENT_PATH]
        )
        cls.regression = parse_json_bytes(
            cls.documents[builder.REGRESSION_PATH]
        )
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )
        cls.policies = builder.load_au040_acceptance().bundle.policies

    @staticmethod
    def refinalize(value):
        value["artifact_digest"] = canonical_digest(
            value,
            policy.SELF_POINTER,
        )
        return value

    def convert(self, incident=None, **changes):
        values = {
            "regression_case_uid": builder.FIXTURE_REGRESSION_UID,
            "deterministic_check_manifest_digest": (
                builder.FIXTURE_DETERMINISTIC_CHECK_DIGEST
            ),
            "sealed_holdout_manifest_digest": (
                builder.FIXTURE_SEALED_HOLDOUT_DIGEST
            ),
            "created_at": "2026-07-26T01:00:01.000000Z",
        }
        values.update(changes)
        return convert_confirmed_incident(
            self.incident if incident is None else incident,
            **values,
        )

    def test_01_builder_is_byte_equivalent_and_dependency_is_explicit(
        self,
    ):
        builder._check()
        self.assertEqual(
            self.readiness["task_contract"]["implemented_task_ids"],
            ["M-046"],
        )
        self.assertEqual(
            self.readiness["task_contract"]["dependency_task_ids"],
            ["M-045"],
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_THREE_REPRESENTATIVE_PILOTS",
        )
        self.assertEqual(self.readiness["schema_closure_count"], 34)
        self.assertFalse(
            self.readiness["dependency_contract"][
                "standalone_repository_artifact_present"
            ]
        )
        self.assertEqual(
            self.readiness["dependency_contract"]["dependency_status"],
            "FUNCTIONAL_CONTRACT_RECONSTRUCTED_FAIL_CLOSED",
        )

    def test_02_shadow_fixture_has_closed_lineage_and_no_contamination(
        self,
    ):
        validate_confirmed_incident(self.incident)
        validate_regression_case(self.regression, self.incident)
        self.assertEqual(
            self.regression["lineage"]["artifact_digest"],
            self.incident["artifact_digest"],
        )
        self.assertEqual(
            self.regression["lineage"]["source_fact_digests"],
            self.incident["source_fact_digests"],
        )
        sealed = self.regression["sealed_boundary"]
        self.assertFalse(sealed["sealed_holdout_accessed"])
        self.assertFalse(sealed["sealed_holdout_labels_copied"])
        self.assertEqual(sealed["optimizer_visibility"], "DENIED")
        self.assertNotIn(
            sealed["sealed_holdout_manifest_digest"],
            self.incident["source_fact_digests"],
        )

    def test_03_only_confirmed_root_caused_incident_converts(self):
        for path, value, code in (
            (("status",), "TRIAGED", "CLASSIFICATION"),
            (
                ("root_cause", "status"),
                "PENDING",
                "ROOT_CAUSE_UNCONFIRMED",
            ),
        ):
            with self.subTest(path=path):
                altered = copy.deepcopy(self.incident)
                target = altered
                for key in path[:-1]:
                    target = target[key]
                target[path[-1]] = value
                self.refinalize(altered)
                with self.assertRaisesRegex(FailureToTestError, code):
                    self.convert(altered)

    def test_04_privacy_triage_is_a_hard_gate(self):
        for field in (
            "raw_content_present",
            "personal_data_present",
            "sealed_holdout_content_present",
        ):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.incident)
                altered["privacy_triage"][field] = True
                self.refinalize(altered)
                with self.assertRaisesRegex(
                    FailureToTestError,
                    "PRIVACY_TRIAGE_NOT_SAFE",
                ):
                    self.convert(altered)

    def test_05_root_cause_evidence_must_be_source_lineage(self):
        altered = copy.deepcopy(self.incident)
        altered["root_cause"]["evidence_digests"] = ["3" * 64]
        self.refinalize(altered)
        with self.assertRaisesRegex(
            FailureToTestError,
            "ROOT_CAUSE_LINEAGE_INCOMPLETE",
        ):
            self.convert(altered)

    def test_06_holdout_digest_cannot_enter_any_conversion_input(self):
        for kwargs in (
            {
                "sealed_holdout_manifest_digest": (
                    builder.FIXTURE_DETERMINISTIC_CHECK_DIGEST
                )
            },
            {
                "sealed_holdout_manifest_digest": (
                    builder.FIXTURE_SOURCE_FACT_DIGESTS[0]
                )
            },
        ):
            with self.subTest(kwargs=kwargs):
                with self.assertRaisesRegex(
                    FailureToTestError,
                    "SEALED_HOLDOUT_CONTAMINATION",
                ):
                    self.convert(**kwargs)

    def test_07_case_cannot_precede_incident(self):
        with self.assertRaisesRegex(
            FailureToTestError,
            "REGRESSION_CREATED_BEFORE_INCIDENT",
        ):
            self.convert(created_at="2026-07-26T00:59:59.999999Z")

    def test_08_strict_utc_and_digest_validation(self):
        altered = copy.deepcopy(self.incident)
        altered["observed_at"] = "2026-07-26T11:00:00+10:00"
        self.refinalize(altered)
        with self.assertRaisesRegex(
            FailureToTestError,
            "FAILURE_INCIDENT_TIME_INVALID",
        ):
            self.convert(altered)
        altered = copy.deepcopy(self.incident)
        altered["artifact_digest"] = "f" * 64
        with self.assertRaisesRegex(
            FailureToTestError,
            "FAILURE_INCIDENT_SELF_DIGEST_MISMATCH",
        ):
            self.convert(altered)

    def test_09_caller_cannot_change_regression_claim_and_rehash(self):
        for mutate in (
            lambda value: value["sealed_boundary"].update(
                {"sealed_holdout_accessed": True}
            ),
            lambda value: value["replay_contract"].update(
                {"side_effects_permitted": True}
            ),
            lambda value: value["lineage"].update(
                {"conversion_mode": "RAW_COPY"}
            ),
        ):
            with self.subTest(mutate=mutate):
                altered = copy.deepcopy(self.regression)
                mutate(altered)
                self.refinalize(altered)
                with self.assertRaisesRegex(
                    FailureToTestError,
                    "REGRESSION_CASE_RECOMPUTATION_MISMATCH",
                ):
                    validate_regression_case(altered, self.incident)

    def test_10_extra_incident_or_case_field_fails_closed(self):
        altered_incident = copy.deepcopy(self.incident)
        altered_incident["raw"] = "forbidden"
        self.refinalize(altered_incident)
        with self.assertRaisesRegex(
            FailureToTestError,
            "FAILURE_INCIDENT_FIELDS_INVALID",
        ):
            self.convert(altered_incident)
        altered_case = copy.deepcopy(self.regression)
        altered_case["output"] = "forbidden"
        self.refinalize(altered_case)
        with self.assertRaisesRegex(
            FailureToTestError,
            "REGRESSION_CASE_FIELDS_INVALID",
        ):
            validate_regression_case(altered_case, self.incident)

    def test_11_public_scanner_accepts_fixtures_and_blocks_raw(self):
        scan_public_value(self.incident, self.policies)
        scan_public_value(self.regression, self.policies)
        scan_public_value(self.readiness, self.policies)
        altered = copy.deepcopy(self.incident)
        altered["raw"] = "value"
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_FORBIDDEN_FIELD",
        ):
            scan_public_value(altered, self.policies)

    def test_12_conversion_is_deterministic_and_input_immutable(self):
        before = copy.deepcopy(self.incident)
        first = self.convert()
        second = self.convert()
        self.assertEqual(first, second)
        self.assertEqual(self.incident, before)
        self.assertEqual(
            first["artifact_digest"],
            canonical_digest(first, policy.SELF_POINTER),
        )

    def test_13_component_has_no_side_effect_capability(self):
        source = inspect.getsource(policy)
        for forbidden in (
            "subprocess",
            "pathlib",
            "open(",
            "write_",
            "requests",
            "urllib",
            "socket",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        contract = self.readiness["implementation_contract"]
        self.assertFalse(contract["filesystem_capability_present"])
        self.assertFalse(contract["git_capability_present"])
        self.assertFalse(contract["network_capability_present"])
        self.assertFalse(contract["sealed_holdout_read_capability_present"])

    def test_14_current_evidence_does_not_claim_production(self):
        self.assertFalse(self.readiness["production_conversion_ready"])
        self.assertFalse(
            self.readiness["shadow_fixture"][
                "production_incident_converted"
            ]
        )
        self.assertTrue(
            self.readiness["nonmutation"]["auto_plane_unchanged"]
        )
        self.assertTrue(
            self.readiness["nonmutation"]["candidate_bundle_unchanged"]
        )
        self.assertFalse(
            self.readiness["nonmutation"]["real_incident_read"]
        )
        self.assertFalse(
            self.readiness["nonmutation"]["evaluation_profile_mutated"]
        )
        self.assertFalse(
            self.readiness["nonmutation"][
                "canonical_publication_permitted"
            ]
        )

    def test_15_version_remains_absent(self):
        self.assertFalse(builder.VERSION_PATH.exists())


if __name__ == "__main__":
    unittest.main()
