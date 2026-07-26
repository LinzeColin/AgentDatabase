"""Regression gates for Mechanism M-065 read-only migration/cutover."""

from __future__ import annotations

import copy
import inspect
import unittest

from CodexSkills.governance.migration import read_only_cutover as policy
from CodexSkills.governance.migration.read_only_cutover import (
    ReadOnlyCutoverError,
    build_observation,
    derive_cutover_plan,
    validate_cutover_plan,
    validate_observation,
)
from CodexSkills.governance.tools import (
    build_read_only_migration_cutover as builder,
)
from CodexSkills.governance.tools.canonical_json import (
    canonical_digest,
    parse_json_bytes,
)
from CodexSkills.governance.tools.validate_au040_semantic_acceptance import (
    load_au040_acceptance,
)
from CodexSkills.governance.tools.validate_mechanism import (
    scan_public_value,
    validate_instance,
)


class ReadOnlyMigrationCutoverTests(unittest.TestCase):
    """M-065 must derive a shadow decision from immutable evidence."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        cls.observation = parse_json_bytes(
            cls.documents[builder.OBSERVATION_PATH]
        )
        cls.plan = parse_json_bytes(cls.documents[builder.PLAN_PATH])
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )

    @staticmethod
    def snapshot(seed: str = "1"):
        return {
            "file_count": 2,
            "byte_count": 123,
            "regular_file_count": 1,
            "symlink_count": 1,
            "tree_digest": seed * 64,
            "link_digest": ("f" if seed != "f" else "e") * 64,
        }

    @classmethod
    def complete_sources(cls):
        rows = []
        for index, source_class in enumerate(policy.SOURCE_CLASSES, 1):
            snapshot = cls.snapshot(str(index))
            rows.append(
                {
                    "source_class": source_class,
                    "source_ref": (
                        source_class.lower().replace("_", "-") + "-source"
                    ),
                    "state": "COMPLETE",
                    "pre_snapshot": copy.deepcopy(snapshot),
                    "post_snapshot": copy.deepcopy(snapshot),
                    "target_snapshot": copy.deepcopy(snapshot),
                }
            )
        return rows

    @staticmethod
    def complete_history():
        rows = []
        for index, source_class in enumerate(policy.SOURCE_CLASSES, 1):
            tree = "sha1:" + str(index) * 40
            rows.append(
                {
                    "source_class": source_class,
                    "predecessor_git_object_id": builder.M064_GIT_OBJECT,
                    "source_tree_git_object_id": tree,
                    "target_tree_git_object_id": tree,
                    "target_path_present": True,
                    "tree_object_equal": True,
                }
            )
        return rows

    @staticmethod
    def audit():
        value = {
            "mode": "CONTROLLED_SYSCALL_AND_COMMAND_AUDIT",
            "forbidden_command_observed": False,
            "audit_complete": True,
        }
        value.update({field: 0 for field in policy.AUDIT_COUNTER_FIELDS})
        return value

    @staticmethod
    def queries():
        return [
            {
                "query_ref": "identity-version-closure",
                "state": "COMPLETE",
                "old_view": {
                    "record_count": 4,
                    "evidence_digest": "a" * 64,
                },
                "new_view": {
                    "record_count": 4,
                    "evidence_digest": "a" * 64,
                },
            }
        ]

    @classmethod
    def complete_observation(cls):
        return build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FAX",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=cls.complete_sources(),
            historical_path_parity=cls.complete_history(),
            dual_read_queries=cls.queries(),
            mutation_audit=cls.audit(),
            delete_budget=0,
        )

    def test_01_builder_is_byte_equivalent_and_dependencies_are_exact(
        self,
    ) -> None:
        builder._check()
        predecessors = builder._validate_predecessors()
        self.assertEqual(
            predecessors["m064"]["artifact_digest"],
            builder.M064_READINESS_SELF_DIGEST,
        )
        self.assertEqual(
            predecessors["m060"]["artifact_digest"],
            builder.M060_READINESS_SELF_DIGEST,
        )
        self.assertEqual(
            self.readiness["task_contract"]["implemented_task_ids"],
            ["M-065"],
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_PERFORMANCE_CAPACITY_BUDGETS",
        )
        self.assertEqual(self.readiness["schema_closure_count"], 34)

    def test_02_current_evidence_is_truthfully_blocked(self) -> None:
        self.assertEqual(self.plan["decision"], "BLOCKED")
        self.assertEqual(self.plan["cutover_mode"], "SHADOW_ONLY")
        self.assertFalse(self.plan["current_cutover_permitted"])
        self.assertEqual(self.plan["delete_budget"], 0)
        expected = {
            "DUAL_READ_EVIDENCE_MISSING",
            "HISTORICAL_TREE_PARITY_MISMATCH_CODEX",
            "M014_SOURCE_MIGRATION_RECEIPT_MISSING",
            "M015_COMPLETE_SOURCE_TARGET_PARITY_MISSING",
            "RESOLVER_PRODUCTION_TRUST_NOT_PERMITTED",
            "RESOLVER_SOURCE_ROOT_PARITY_NOT_PROVEN",
            "RESOLVER_WHOLE_SOURCE_PARITY_NOT_PROVEN",
            "SOURCE_MISSING_AGENTS",
            "SOURCE_MISSING_CLAUDE",
            "SOURCE_MISSING_CODEX",
            "SOURCE_MISSING_CODEX_SYSTEM",
        }
        self.assertEqual(set(self.plan["blocker_codes"]), expected)
        self.assertFalse(
            self.readiness["current_evidence"]["real_migration_executed"]
        )

    def test_03_complete_synthetic_evidence_is_only_cutover_eligible(
        self,
    ) -> None:
        observation = self.complete_observation()
        plan = derive_cutover_plan(
            observation,
            plan_uid="cut_01ARZ3NDEKTSV4RRFFQ69G5FAY",
        )
        self.assertEqual(plan["decision"], "CUTOVER_ELIGIBLE")
        self.assertEqual(plan["blocker_codes"], [])
        self.assertTrue(plan["parity_complete"])
        self.assertTrue(plan["dual_read_complete"])
        self.assertTrue(plan["zero_local_mutation_verified"])
        self.assertFalse(plan["current_cutover_permitted"])
        validate_cutover_plan(plan, observation)

    def test_04_every_parity_dimension_is_required(self) -> None:
        fields = (
            "file_count",
            "byte_count",
            "regular_file_count",
            "symlink_count",
            "tree_digest",
            "link_digest",
        )
        for field in fields:
            with self.subTest(field=field):
                sources = self.complete_sources()
                if field in {"tree_digest", "link_digest"}:
                    sources[0]["target_snapshot"][field] = "e" * 64
                elif field == "file_count":
                    sources[0]["target_snapshot"]["file_count"] += 1
                    sources[0]["target_snapshot"]["regular_file_count"] += 1
                else:
                    sources[0]["target_snapshot"][field] += 1
                    if field in {"regular_file_count", "symlink_count"}:
                        sources[0]["target_snapshot"]["file_count"] = (
                            sources[0]["target_snapshot"]["regular_file_count"]
                            + sources[0]["target_snapshot"]["symlink_count"]
                        )
                observation = build_observation(
                    observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FAZ",
                    baseline_git_object_id=builder.M064_GIT_OBJECT,
                    sources=sources,
                    historical_path_parity=self.complete_history(),
                    dual_read_queries=self.queries(),
                    mutation_audit=self.audit(),
                )
                self.assertIn(
                    "SOURCE_TARGET_PARITY_MISMATCH_AGENTS",
                    observation["derived_blocker_codes"],
                )

    def test_05_pre_post_source_mutation_blocks(self) -> None:
        sources = self.complete_sources()
        sources[2]["post_snapshot"]["tree_digest"] = "e" * 64
        observation = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB0",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=sources,
            historical_path_parity=self.complete_history(),
            dual_read_queries=self.queries(),
            mutation_audit=self.audit(),
        )
        self.assertIn(
            "PROTECTED_SOURCE_MUTATION_CODEX",
            observation["derived_blocker_codes"],
        )
        self.assertTrue(observation["local_data_mutation_performed"])
        plan = derive_cutover_plan(
            observation,
            plan_uid="cut_01ARZ3NDEKTSV4RRFFQ69G5FBA",
        )
        self.assertFalse(plan["zero_local_mutation_verified"])

    def test_06_missing_empty_and_error_sources_fail_closed(self) -> None:
        for state in ("MISSING", "EMPTY", "ERROR"):
            with self.subTest(state=state):
                sources = self.complete_sources()
                sources[1] = {
                    "source_class": "CLAUDE",
                    "source_ref": "claude-source",
                    "state": state,
                    "reason_code": "SOURCE_UNAVAILABLE",
                }
                observation = build_observation(
                    observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB1",
                    baseline_git_object_id=builder.M064_GIT_OBJECT,
                    sources=sources,
                    historical_path_parity=self.complete_history(),
                    dual_read_queries=self.queries(),
                    mutation_audit=self.audit(),
                )
                self.assertIn(
                    "SOURCE_" + state + "_CLAUDE",
                    observation["derived_blocker_codes"],
                )
                self.assertEqual(observation["delete_budget"], 0)

    def test_07_dual_read_missing_or_mismatch_blocks(self) -> None:
        missing = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB2",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=self.complete_sources(),
            historical_path_parity=self.complete_history(),
            dual_read_queries=(),
            mutation_audit=self.audit(),
        )
        self.assertIn(
            "DUAL_READ_EVIDENCE_MISSING",
            missing["derived_blocker_codes"],
        )
        queries = self.queries()
        queries[0]["new_view"]["evidence_digest"] = "b" * 64
        mismatch = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB3",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=self.complete_sources(),
            historical_path_parity=self.complete_history(),
            dual_read_queries=queries,
            mutation_audit=self.audit(),
        )
        self.assertIn(
            "DUAL_READ_RESULT_MISMATCH_IDENTITY_VERSION_CLOSURE",
            mismatch["derived_blocker_codes"],
        )

    def test_08_every_mutating_audit_counter_blocks(self) -> None:
        for field in policy.AUDIT_COUNTER_FIELDS:
            with self.subTest(field=field):
                audit = self.audit()
                audit[field] = 1
                observation = build_observation(
                    observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB4",
                    baseline_git_object_id=builder.M064_GIT_OBJECT,
                    sources=self.complete_sources(),
                    historical_path_parity=self.complete_history(),
                    dual_read_queries=self.queries(),
                    mutation_audit=audit,
                )
                self.assertIn(
                    "NONZERO_" + field.upper(),
                    observation["derived_blocker_codes"],
                )
                self.assertTrue(
                    observation["local_data_mutation_performed"]
                )

    def test_09_incomplete_audit_and_forbidden_command_block(self) -> None:
        audit = self.audit()
        audit["audit_complete"] = False
        audit["forbidden_command_observed"] = True
        observation = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB5",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=self.complete_sources(),
            historical_path_parity=self.complete_history(),
            dual_read_queries=self.queries(),
            mutation_audit=audit,
        )
        self.assertIn(
            "MIGRATION_AUDIT_INCOMPLETE",
            observation["derived_blocker_codes"],
        )
        self.assertIn(
            "FORBIDDEN_COMMAND_OBSERVED",
            observation["derived_blocker_codes"],
        )

    def test_10_nonzero_delete_budget_cannot_be_authorized(self) -> None:
        observation = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB6",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=self.complete_sources(),
            historical_path_parity=self.complete_history(),
            dual_read_queries=self.queries(),
            mutation_audit=self.audit(),
            delete_budget=1,
        )
        self.assertIn(
            "DELETE_BUDGET_NONZERO",
            observation["derived_blocker_codes"],
        )
        plan = derive_cutover_plan(
            observation,
            plan_uid="cut_01ARZ3NDEKTSV4RRFFQ69G5FB7",
        )
        self.assertEqual(plan["delete_budget"], 0)
        self.assertEqual(plan["decision"], "BLOCKED")

    def test_11_historical_git_path_mismatch_is_not_grandfathered(
        self,
    ) -> None:
        rows = self.complete_history()
        rows[2]["target_tree_git_object_id"] = "sha1:" + "e" * 40
        rows[2]["tree_object_equal"] = False
        observation = build_observation(
            observation_uid="mig_01ARZ3NDEKTSV4RRFFQ69G5FB8",
            baseline_git_object_id=builder.M064_GIT_OBJECT,
            sources=self.complete_sources(),
            historical_path_parity=rows,
            dual_read_queries=self.queries(),
            mutation_audit=self.audit(),
        )
        self.assertIn(
            "HISTORICAL_TREE_PARITY_MISMATCH_CODEX",
            observation["derived_blocker_codes"],
        )

    def test_12_caller_decision_and_recomputed_digest_cannot_weaken(self) -> None:
        altered = copy.deepcopy(self.plan)
        altered["decision"] = "CUTOVER_ELIGIBLE"
        altered["current_cutover_permitted"] = True
        altered["blocker_codes"] = []
        altered["evidence_bundle_digest"] = canonical_digest(
            altered,
            policy.PLAN_SELF_POINTER,
        )
        with self.assertRaises(ReadOnlyCutoverError):
            validate_cutover_plan(altered, self.observation)

    def test_13_rollback_is_new_commit_only_and_source_preserving(
        self,
    ) -> None:
        rollback = self.plan["rollback_contract"]
        self.assertEqual(rollback, policy.FIXED_ROLLBACK_CONTRACT)
        self.assertFalse(rollback["local_source_deletion_permitted"])
        self.assertFalse(rollback["history_rewrite_permitted"])
        altered = copy.deepcopy(self.plan)
        altered["rollback_contract"]["force_push_permitted"] = True
        altered["evidence_bundle_digest"] = canonical_digest(
            altered,
            policy.PLAN_SELF_POINTER,
        )
        with self.assertRaisesRegex(
            ReadOnlyCutoverError,
            "CUTOVER_ROLLBACK_CONTRACT_INVALID",
        ):
            validate_cutover_plan(altered, self.observation)

    def test_14_instances_validate_offline_and_are_public_safe(self) -> None:
        acceptance = load_au040_acceptance()
        observation_schema = builder.build_observation_schema()
        plan_schema = builder.build_plan_schema()
        readiness_schema = builder.build_readiness_schema(self.readiness)
        contract = builder._extend_bundle(
            acceptance.bundle,
            {
                policy.OBSERVATION_SCHEMA_ID: observation_schema,
                policy.PLAN_SCHEMA_ID: plan_schema,
                builder.READINESS_SCHEMA_ID: readiness_schema,
            },
            {
                policy.OBSERVATION_SCHEMA_ID: (
                    policy.OBSERVATION_SELF_POINTER
                ),
                policy.PLAN_SCHEMA_ID: policy.PLAN_SELF_POINTER,
                builder.READINESS_SCHEMA_ID: "/artifact_digest",
            },
        )
        for instance, schema_id in (
            (self.observation, policy.OBSERVATION_SCHEMA_ID),
            (self.plan, policy.PLAN_SCHEMA_ID),
            (self.readiness, builder.READINESS_SCHEMA_ID),
        ):
            validate_instance(
                contract,
                instance,
                schema_id,
                expected_bundle_digest=builder.CANDIDATE_BUNDLE_DIGEST,
                verify_digest=True,
                public=True,
            )
            scan_public_value(instance, contract.policies)

    def test_15_private_paths_and_mutable_capabilities_are_absent(self) -> None:
        serialized = b"".join(
            (
                self.documents[builder.OBSERVATION_PATH],
                self.documents[builder.PLAN_PATH],
                self.documents[builder.READINESS_PATH],
            )
        )
        self.assertNotIn(b"/Users/", serialized)
        self.assertNotIn(b"file://", serialized)
        source = inspect.getsource(policy)
        for forbidden in (
            "import os",
            "import pathlib",
            "import subprocess",
            "from pathlib",
            "open(",
            ".write_",
            ".unlink(",
            ".rename(",
        ):
            self.assertNotIn(forbidden, source)

    def test_16_dependency_blockers_are_additive_and_immutable(self) -> None:
        observation = self.complete_observation()
        plan = derive_cutover_plan(
            observation,
            plan_uid="cut_01ARZ3NDEKTSV4RRFFQ69G5FB9",
            dependency_blocker_codes=(
                "M014_SOURCE_MIGRATION_RECEIPT_MISSING",
            ),
        )
        self.assertEqual(plan["decision"], "BLOCKED")
        self.assertEqual(
            plan["blocker_codes"],
            ["M014_SOURCE_MIGRATION_RECEIPT_MISSING"],
        )
        self.assertTrue(plan["parity_complete"])
        self.assertTrue(plan["dual_read_complete"])
        self.assertTrue(plan["zero_local_mutation_verified"])


if __name__ == "__main__":
    unittest.main()
