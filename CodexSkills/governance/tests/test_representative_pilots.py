"""Regression gates for Mechanism M-068 representative Shadow pilots."""

from __future__ import annotations

import copy
import inspect
import unittest
from unittest import mock

from CodexSkills.governance.pilots import representative_pilots as policy
from CodexSkills.governance.pilots.representative_pilots import (
    RepresentativePilotError,
    build_all_pilots,
    build_pilot,
    validate_pilot,
)
from CodexSkills.governance.promotion.rollback_controller import (
    REQUIRED_VERIFICATION_KINDS,
)
from CodexSkills.governance.tools import (
    build_representative_pilots as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_mechanism import (
    ContractError,
    scan_public_value,
)


class RepresentativePilotTests(unittest.TestCase):
    """Three clean cycles must remain Shadow-only and exactly attributable."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        (
            cls.snapshot,
            cls.dependencies,
            cls.external_schemas,
            cls.external_pointers,
        ) = builder._source_material()
        cls.pilots = {
            pilot_class: parse_json_bytes(
                cls.documents[builder.PILOT_PATHS[pilot_class]]
            )
            for pilot_class in policy.PILOT_CLASSES
        }
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )
        cls.policies = builder.load_au040_acceptance().bundle.policies

    @staticmethod
    def refinalize(value, pointer=policy.SELF_POINTER):
        field = pointer.rsplit("/", 1)[-1]
        value[field] = canonical_digest(value, pointer)
        return value

    def test_01_builder_is_byte_equivalent_and_dependencies_are_exact(
        self,
    ):
        builder._check()
        self.assertEqual(
            self.readiness["task_contract"]["implemented_task_ids"],
            ["M-068"],
        )
        self.assertEqual(
            self.readiness["task_contract"]["dependency_task_ids"],
            ["M-046", "M-057", "M-065"],
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_COLD_START_HANDOFF_RELEASE_REVIEW",
        )
        self.assertEqual(self.readiness["schema_closure_count"], 42)
        self.assertEqual(len(self.external_schemas), 9)

    def test_02_exact_taskpack_pilot_selection_is_materialized(self):
        expected = {
            "DETERMINISTIC_SYNC": (
                "skill-github-sync",
                [("CODEX", "codex/skill-github-sync")],
            ),
            "SAME_NAME_MULTI_SOURCE": (
                "agent-reach",
                [
                    ("AGENTS", "agents/agent-reach"),
                    ("CODEX", "codex/agent-reach"),
                ],
            ),
            "HIGH_RISK_ITERATIVE": (
                "km-bid-evolve",
                [("CODEX", "codex/km-bid-evolve")],
            ),
        }
        for pilot_class, (name, members) in expected.items():
            with self.subTest(pilot_class=pilot_class):
                pilot = self.pilots[pilot_class]
                self.assertEqual(pilot["canonical_name"], name)
                self.assertEqual(
                    [
                        (
                            member["source_class"],
                            member["source_relative_path"],
                        )
                        for member in pilot["members"]
                    ],
                    members,
                )
                self.assertTrue(
                    all(
                        not member["binding_eligible"]
                        and not member["eval_profile_present"]
                        and not member["permissions_resolved"]
                        for member in pilot["members"]
                    )
                )

    def test_03_every_pilot_has_three_clean_stable_cycles(self):
        for pilot in self.pilots.values():
            with self.subTest(pilot=pilot["pilot_class"]):
                self.assertEqual(
                    [cycle["cycle_index"] for cycle in pilot["cycles"]],
                    [1, 2, 3],
                )
                self.assertEqual(
                    len(
                        {
                            cycle["shadow_evidence_digest"]
                            for cycle in pilot["cycles"]
                        }
                    ),
                    1,
                )
                self.assertEqual(pilot["summary"]["clean_cycle_count"], 3)
                self.assertTrue(
                    pilot["summary"]["three_cycle_result_stable"]
                )
                for cycle in pilot["cycles"]:
                    self.assertEqual(cycle["side_effect_count"], 0)
                    self.assertEqual(cycle["registry_write_count"], 0)
                    self.assertEqual(cycle["state_write_count"], 0)
                    self.assertEqual(cycle["notification_count"], 0)
                    self.assertEqual(cycle["publication_count"], 0)

    def test_04_same_name_identities_remain_distinct_and_unmerged(self):
        pilot = self.pilots["SAME_NAME_MULTI_SOURCE"]
        identity = pilot["identity_resolution"]
        self.assertEqual(identity["registry_identity_count"], 2)
        self.assertEqual(identity["selected_identity_count"], 2)
        self.assertEqual(
            identity["registry_identity_uids"],
            identity["selected_identity_uids"],
        )
        self.assertEqual(len(set(identity["selected_identity_uids"])), 2)
        self.assertTrue(identity["owner_review_required"])
        self.assertFalse(identity["same_name_auto_merge_permitted"])
        gate_codes = {
            gate["gate_code"]
            for gate in pilot["cycles"][0]["gate_results"]
        }
        self.assertIn(
            "SAME_NAME_DISTINCT_IDENTITY_PRESERVED",
            gate_codes,
        )
        self.assertIn(
            "OWNER_REVIEW_REQUIRED_NO_AUTO_MERGE",
            gate_codes,
        )

    def test_05_high_risk_pilot_binds_failure_to_test_and_holdout(self):
        pilot = self.pilots["HIGH_RISK_ITERATIVE"]
        member = pilot["members"][0]
        regression = self.dependencies["regression_case"]
        self.assertEqual(
            member["skill_identity_uid"],
            regression["skill_identity_uid"],
        )
        self.assertEqual(
            member["skill_version_uid"],
            regression["skill_version_uid"],
        )
        self.assertFalse(
            regression["sealed_boundary"]["sealed_holdout_accessed"]
        )
        self.assertFalse(
            regression["sealed_boundary"][
                "sealed_holdout_labels_copied"
            ]
        )
        for cycle in pilot["cycles"]:
            gate_codes = {
                gate["gate_code"] for gate in cycle["gate_results"]
            }
            self.assertTrue(
                {
                    "FAILURE_TO_TEST_LINEAGE",
                    "NO_AUTONOMOUS_PROMOTION",
                    "SEALED_HOLDOUT_ISOLATION",
                }.issubset(gate_codes)
            )

    def test_06_every_cycle_has_complete_shadow_rollback_drill(self):
        for pilot in self.pilots.values():
            for cycle in pilot["cycles"]:
                with self.subTest(
                    pilot=pilot["pilot_class"],
                    cycle=cycle["cycle_index"],
                ):
                    drill = cycle["rollback_drill"]
                    self.assertEqual(drill["status"], "SHADOW_PASS")
                    self.assertEqual(
                        [
                            ref["kind"]
                            for ref in drill[
                                "verification_evidence_refs"
                            ]
                        ],
                        list(REQUIRED_VERIFICATION_KINDS),
                    )
                    self.assertEqual(
                        len(
                            {
                                ref["artifact_digest"]
                                for ref in drill[
                                    "verification_evidence_refs"
                                ]
                            }
                        ),
                        len(REQUIRED_VERIFICATION_KINDS),
                    )
                    self.assertTrue(
                        drill["synthetic_prior_champion_restorable"]
                    )
                    self.assertFalse(
                        drill["real_registry_champion_present"]
                    )
                    self.assertFalse(drill["history_rewrite_performed"])
                    self.assertFalse(drill["state_write_observed"])
                    self.assertFalse(drill["notification_sent"])
                    self.assertFalse(drill["production_drill"])
                    self.assertEqual(
                        drill["evidence_bundle_digest"],
                        canonical_digest(
                            drill,
                            policy.DRILL_SELF_POINTER,
                        ),
                    )

    def test_07_shadow_pass_never_becomes_production_claim(self):
        summary = self.readiness["current_summary"]
        self.assertEqual(summary["pilot_count"], 3)
        self.assertEqual(summary["cycle_count"], 9)
        self.assertEqual(summary["clean_cycle_count"], 9)
        self.assertEqual(summary["shadow_rollback_drill_count"], 9)
        self.assertTrue(summary["all_shadow_critical_gates_passed"])
        self.assertTrue(summary["all_shadow_rollback_drills_passed"])
        self.assertFalse(summary["production_critical_gates_passed"])
        self.assertFalse(summary["production_pilots_ready"])
        self.assertFalse(summary["real_skill_execution_performed"])
        self.assertFalse(summary["real_rollback_execution_performed"])
        self.assertFalse(summary["real_notification_sent"])
        self.assertIn(
            "BINDING_ELIGIBLE_VERSION_COUNT_ZERO",
            summary["production_blocker_codes"],
        )
        self.assertFalse(
            self.readiness["task_contract"][
                "production_done_gate_satisfied"
            ]
        )
        self.assertEqual(
            self.readiness["task_contract"]["done_gate_scope"],
            "DETERMINISTIC_SHADOW_ONLY",
        )

    def test_08_registry_raw_and_self_digest_drift_fail_closed(self):
        original = builder._git_blob

        def drift(object_id, path):
            raw = original(object_id, path)
            if path == builder.REGISTRY_PATH:
                return raw + b" "
            return raw

        with mock.patch.object(builder, "_git_blob", side_effect=drift):
            with self.assertRaisesRegex(
                builder.RepresentativePilotBuildError,
                "M068_REGISTRY_RAW_DRIFT",
            ):
                builder._source_material()
        altered = copy.deepcopy(self.snapshot)
        altered["registry_snapshot_digest"] = "f" * 64
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_REGISTRY_SELF_DIGEST_MISMATCH",
        ):
            build_pilot(
                "DETERMINISTIC_SYNC",
                altered,
                self.dependencies,
            )

    def test_09_dependency_raw_drift_fails_closed(self):
        original = builder._git_blob
        target = builder.SOURCE_DOCUMENTS["rollback_readiness"][
            "canonical_path"
        ]

        def drift(object_id, path):
            raw = original(object_id, path)
            return raw + b" " if path == target else raw

        with mock.patch.object(builder, "_git_blob", side_effect=drift):
            with self.assertRaisesRegex(
                builder.RepresentativePilotBuildError,
                "M068_DEPENDENCY_RAW_DRIFT:rollback_readiness",
            ):
                builder._source_material()

    def test_10_missing_or_self_rehashed_dependency_fails_closed(self):
        missing = dict(self.dependencies)
        missing.pop("migration_readiness")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_DEPENDENCY_SET_INCOMPLETE",
        ):
            build_pilot("DETERMINISTIC_SYNC", self.snapshot, missing)
        altered = copy.deepcopy(self.dependencies)
        altered["rollback_readiness"]["registry_observation"][
            "base_champion_count"
        ] = 1
        self.refinalize(altered["rollback_readiness"])
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_ROLLBACK_DEPENDENCY_INVALID",
        ):
            build_pilot("DETERMINISTIC_SYNC", self.snapshot, altered)

    def test_11_registry_eligibility_or_quarantine_drift_blocks(self):
        altered = copy.deepcopy(self.snapshot)
        altered["counts"]["binding_eligible_version_count"] = 1
        self.refinalize(altered, "/registry_snapshot_digest")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_REGISTRY_COUNT_OR_ELIGIBILITY_INVALID",
        ):
            build_pilot(
                "DETERMINISTIC_SYNC",
                altered,
                self.dependencies,
            )
        altered = copy.deepcopy(self.snapshot)
        target = next(
            value
            for value in altered["versions"]
            if value["record"]["skill_version_uid"]
            == self.pilots["DETERMINISTIC_SYNC"]["members"][0][
                "skill_version_uid"
            ]
        )
        target["record"]["lifecycle_status"] = "CHALLENGER"
        self.refinalize(altered, "/registry_snapshot_digest")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_VERSION_NOT_FAIL_CLOSED",
        ):
            build_pilot(
                "DETERMINISTIC_SYNC",
                altered,
                self.dependencies,
            )

    def test_12_missing_selected_path_or_duplicate_instance_blocks(self):
        altered = copy.deepcopy(self.snapshot)
        altered["instances"] = [
            value
            for value in altered["instances"]
            if value["record"]["source_relative_path"]
            != "codex/skill-github-sync"
        ]
        altered["counts"]["instance_count"] -= 1
        self.refinalize(altered, "/registry_snapshot_digest")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_REGISTRY_COUNT_OR_ELIGIBILITY_INVALID",
        ):
            build_pilot(
                "DETERMINISTIC_SYNC",
                altered,
                self.dependencies,
            )
        altered = copy.deepcopy(self.snapshot)
        target = next(
            value
            for value in altered["instances"]
            if value["record"]["source_relative_path"]
            == "codex/skill-github-sync"
        )
        altered["instances"].append(copy.deepcopy(target))
        altered["counts"]["instance_count"] += 1
        self.refinalize(altered, "/registry_snapshot_digest")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_REGISTRY_COUNT_OR_ELIGIBILITY_INVALID",
        ):
            build_pilot(
                "DETERMINISTIC_SYNC",
                altered,
                self.dependencies,
            )

    def test_13_missing_merge_candidate_blocks_duplicate_pilot(self):
        altered = copy.deepcopy(self.snapshot)
        altered["identity_merge_candidates"] = [
            value
            for value in altered["identity_merge_candidates"]
            if value["canonical_name"] != "agent-reach"
        ]
        self.refinalize(altered, "/registry_snapshot_digest")
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_MERGE_CANDIDATE_NOT_UNIQUE",
        ):
            build_pilot(
                "SAME_NAME_MULTI_SOURCE",
                altered,
                self.dependencies,
            )

    def test_14_high_risk_regression_binding_cannot_be_forged(self):
        altered = copy.deepcopy(self.dependencies)
        regression = altered["regression_case"]
        regression["skill_version_uid"] = (
            self.pilots["DETERMINISTIC_SYNC"]["members"][0][
                "skill_version_uid"
            ]
        )
        self.refinalize(regression)
        readiness = altered["failure_readiness"]
        readiness["shadow_fixture"]["regression_case"][
            "artifact_digest"
        ] = regression["artifact_digest"]
        self.refinalize(readiness)
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_HIGH_RISK_REGRESSION_BINDING_INVALID",
        ):
            build_pilot("HIGH_RISK_ITERATIVE", self.snapshot, altered)

    def test_15_caller_cannot_change_summary_and_rehash(self):
        altered = copy.deepcopy(self.pilots["DETERMINISTIC_SYNC"])
        altered["summary"]["production_pilot_executed"] = True
        self.refinalize(altered)
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_EVIDENCE_RECOMPUTATION_MISMATCH",
        ):
            validate_pilot(altered, self.snapshot, self.dependencies)

    def test_16_caller_cannot_remove_gate_or_rehash_cycle(self):
        altered = copy.deepcopy(self.pilots["SAME_NAME_MULTI_SOURCE"])
        altered["cycles"][0]["gate_results"].pop()
        self.refinalize(altered["cycles"][0], "/evidence_digest")
        self.refinalize(altered)
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_EVIDENCE_RECOMPUTATION_MISMATCH",
        ):
            validate_pilot(altered, self.snapshot, self.dependencies)

    def test_17_caller_cannot_weaken_rollback_and_rehash(self):
        altered = copy.deepcopy(self.pilots["HIGH_RISK_ITERATIVE"])
        drill = altered["cycles"][0]["rollback_drill"]
        drill["verification_evidence_refs"].pop()
        self.refinalize(drill, policy.DRILL_SELF_POINTER)
        self.refinalize(altered["cycles"][0], "/evidence_digest")
        self.refinalize(altered)
        with self.assertRaisesRegex(
            RepresentativePilotError,
            "PILOT_EVIDENCE_RECOMPUTATION_MISMATCH",
        ):
            validate_pilot(altered, self.snapshot, self.dependencies)

    def test_18_public_scanner_accepts_outputs_and_blocks_raw(self):
        for pilot in self.pilots.values():
            scan_public_value(pilot, self.policies)
        scan_public_value(self.readiness, self.policies)
        altered = copy.deepcopy(self.pilots["DETERMINISTIC_SYNC"])
        altered["raw"] = "forbidden"
        with self.assertRaisesRegex(
            ContractError,
            "PUBLIC_FORBIDDEN_FIELD",
        ):
            scan_public_value(altered, self.policies)

    def test_19_harness_has_no_side_effect_capability(self):
        source = inspect.getsource(policy)
        for forbidden in (
            "subprocess",
            "pathlib",
            "open(",
            "requests",
            "urllib",
            "socket",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        contract = self.readiness["implementation_contract"]
        self.assertFalse(contract["skill_execution_capability_present"])
        self.assertFalse(contract["source_content_read_capability_present"])
        self.assertFalse(contract["sealed_holdout_read_capability_present"])
        self.assertFalse(contract["state_capability_present"])
        self.assertFalse(contract["publisher_capability_present"])

    def test_20_build_is_deterministic_and_version_absent(self):
        first = build_all_pilots(self.snapshot, self.dependencies)
        second = build_all_pilots(self.snapshot, self.dependencies)
        self.assertEqual(first, second)
        self.assertFalse(builder.VERSION_PATH.exists())


if __name__ == "__main__":
    unittest.main()
