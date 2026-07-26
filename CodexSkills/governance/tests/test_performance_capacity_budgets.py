"""Regression gates for Mechanism M-066 capacity budgets."""

from __future__ import annotations

import copy
import hashlib
import inspect
import unittest

from CodexSkills.governance.performance import capacity_budgets as policy
from CodexSkills.governance.performance.capacity_budgets import (
    CapacityBudgetError,
    build_budget_contract,
    build_profile,
    evaluate_profile,
    validate_budget_contract,
)
from CodexSkills.governance.tools import (
    build_performance_capacity_budgets as builder,
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


class PerformanceCapacityBudgetTests(unittest.TestCase):
    """M-066 must fail closed without sampling, skipping, or truncation."""

    @classmethod
    def setUpClass(cls) -> None:
        cls.documents = builder._documents()
        cls.budget = parse_json_bytes(
            cls.documents[builder.BUDGET_PATH]
        )
        cls.readiness = parse_json_bytes(
            cls.documents[builder.READINESS_PATH]
        )

    @staticmethod
    def cache_keys():
        return {
            field: format(index, "x") * 64
            for index, field in enumerate(policy.CACHE_KEY_FIELDS, 1)
        }

    @classmethod
    def profile(cls, scenario: str, **overrides):
        values = {
            "profile_uid": "prf_01ARZ3NDEKTSV4RRFFQ69G5FAV",
            "scenario": scenario,
            "cache_state": "COLD",
            "environment_fingerprint_digest": "a" * 64,
            "input_contract_digest": "b" * 64,
            "input_count": 4,
            "processed_count": 4,
            "duration_ms": 1,
            "peak_memory_bytes": 1,
            "output_artifact_bytes": 1,
            "commit_count": 0,
            "source_classes": policy.SOURCE_CLASSES,
            "cache_key_digests": {},
            "graph_pairing_mode": "NOT_APPLICABLE",
            "growth_warning_horizon_days": 0,
        }
        if scenario == "PUBLIC_EVENTS_10000":
            values.update(
                {
                    "input_count": 10_000,
                    "processed_count": 10_000,
                    "duration_ms": policy.PUBLIC_EVENTS_MAX_MS,
                    "peak_memory_bytes": (
                        policy.PUBLIC_EVENTS_MAX_PEAK_BYTES
                    ),
                }
            )
        elif scenario == "SINGLE_GIT_SHARD":
            values["output_artifact_bytes"] = policy.MAX_SHARD_BYTES
        elif scenario == "CANONICAL_TRANSACTION":
            values["commit_count"] = 1
        elif scenario == "REPOSITORY_GROWTH_FORECAST":
            values["growth_warning_horizon_days"] = 90
        elif scenario == "CAPABILITY_GRAPH_PAIRING":
            values["graph_pairing_mode"] = "FILTERED_CANDIDATE_SET"
        elif scenario == "EVALUATION_CACHE":
            values["cache_key_digests"] = cls.cache_keys()
        elif scenario == "REGISTRY_FAST_PATH":
            values["duration_ms"] = policy.REGISTRY_FAST_PATH_MAX_MS
        elif scenario == "FOUR_SOURCE_FULL_INVENTORY":
            values["duration_ms"] = policy.FULL_INVENTORY_MAX_MS
        values.update(overrides)
        return build_profile(**values)

    def test_01_builder_is_byte_equivalent_and_dependencies_are_exact(
        self,
    ) -> None:
        builder._check()
        dependencies = builder._validate_dependencies()
        self.assertEqual(
            dependencies["m065"]["artifact_digest"],
            builder.M065_READINESS_SELF_DIGEST,
        )
        self.assertEqual(
            dependencies["m063"]["artifact_digest"],
            builder.M063_READINESS_SELF_DIGEST,
        )
        self.assertEqual(
            self.readiness["task_contract"]["implemented_task_ids"],
            ["M-066"],
        )
        self.assertEqual(
            self.readiness["next_phase"],
            "MECHANISM_DASHBOARDS_ACTIONABLE_ALERTS",
        )
        self.assertEqual(self.readiness["schema_closure_count"], 34)

    def test_02_budget_contract_is_provisional_not_a_fake_sla(self) -> None:
        validate_budget_contract(self.budget)
        self.assertEqual(
            self.budget["calibration"]["state"],
            "UNCALIBRATED",
        )
        self.assertFalse(
            self.budget["calibration"][
                "provisional_budget_is_production_sla"
            ]
        )
        self.assertFalse(
            self.readiness["calibration_state"]["production_sla_proven"]
        )
        self.assertEqual(
            self.readiness["calibration_state"]["real_profile_count"],
            0,
        )

    def test_03_every_scenario_passes_at_its_exact_boundary(self) -> None:
        for scenario in policy.SCENARIOS:
            with self.subTest(scenario=scenario):
                result = evaluate_profile(
                    self.profile(scenario),
                    self.budget,
                )
                self.assertEqual(
                    result["outcome"],
                    "WITHIN_PROVISIONAL_BUDGET",
                )
                self.assertEqual(result["completeness_blocker_codes"], [])
                self.assertEqual(result["budget_exceedance_codes"], [])
                self.assertTrue(result["watermark_advance_permitted"])
                self.assertFalse(result["production_sla_proven"])

    def test_04_registry_and_inventory_duration_overage_is_explicit(
        self,
    ) -> None:
        cases = (
            (
                "REGISTRY_FAST_PATH",
                policy.REGISTRY_FAST_PATH_MAX_MS + 1,
                "REGISTRY_FAST_PATH_DURATION_EXCEEDED",
            ),
            (
                "FOUR_SOURCE_FULL_INVENTORY",
                policy.FULL_INVENTORY_MAX_MS + 1,
                "FULL_INVENTORY_DURATION_EXCEEDED",
            ),
        )
        for scenario, duration, code in cases:
            with self.subTest(scenario=scenario):
                result = evaluate_profile(
                    self.profile(scenario, duration_ms=duration),
                    self.budget,
                )
                self.assertEqual(
                    result["outcome"],
                    "OVER_BUDGET_FAIL_CLOSED",
                )
                self.assertIn(code, result["budget_exceedance_codes"])
                self.assertFalse(result["watermark_advance_permitted"])

    def test_05_event_time_and_memory_overage_backpressures_no_drop(
        self,
    ) -> None:
        profile = self.profile(
            "PUBLIC_EVENTS_10000",
            duration_ms=policy.PUBLIC_EVENTS_MAX_MS + 1,
            peak_memory_bytes=policy.PUBLIC_EVENTS_MAX_PEAK_BYTES + 1,
        )
        result = evaluate_profile(profile, self.budget)
        self.assertEqual(result["outcome"], "OVER_BUDGET_FAIL_CLOSED")
        self.assertEqual(
            result["budget_exceedance_codes"],
            [
                "PUBLIC_EVENT_DURATION_EXCEEDED",
                "PUBLIC_EVENT_MEMORY_EXCEEDED",
            ],
        )
        self.assertEqual(
            result["remediation"],
            "BACKPRESSURE_AND_ROTATE_NO_EVENT_DROP",
        )

    def test_06_shard_overage_rotates_without_truncation(self) -> None:
        result = evaluate_profile(
            self.profile(
                "SINGLE_GIT_SHARD",
                output_artifact_bytes=policy.MAX_SHARD_BYTES + 1,
            ),
            self.budget,
        )
        self.assertEqual(result["outcome"], "OVER_BUDGET_FAIL_CLOSED")
        self.assertEqual(
            result["budget_exceedance_codes"],
            ["SHARD_SIZE_EXCEEDED"],
        )
        self.assertEqual(
            result["remediation"],
            "ROTATE_NEW_SHARD_NO_TRUNCATION",
        )

    def test_07_transaction_overage_aborts_without_watermark(self) -> None:
        result = evaluate_profile(
            self.profile("CANONICAL_TRANSACTION", commit_count=2),
            self.budget,
        )
        self.assertEqual(result["outcome"], "OVER_BUDGET_FAIL_CLOSED")
        self.assertEqual(
            result["budget_exceedance_codes"],
            ["TRANSACTION_COMMIT_COUNT_EXCEEDED"],
        )
        self.assertFalse(result["watermark_advance_permitted"])

    def test_08_growth_warning_below_90_days_requires_major(self) -> None:
        result = evaluate_profile(
            self.profile(
                "REPOSITORY_GROWTH_FORECAST",
                growth_warning_horizon_days=89,
            ),
            self.budget,
        )
        self.assertEqual(result["outcome"], "OVER_BUDGET_FAIL_CLOSED")
        self.assertEqual(
            result["remediation"],
            "OWNER_MAJOR_ARCHITECTURE_PROPOSAL",
        )

    def test_09_sampling_skipping_and_truncation_always_block(self) -> None:
        cases = (
            ("skipped_count", 1, "SKIPPED_INPUT_NONZERO"),
            ("sampled_count", 1, "SAMPLED_INPUT_NONZERO"),
            ("truncated", True, "TRUNCATION_FORBIDDEN"),
        )
        for field, value, code in cases:
            with self.subTest(field=field):
                result = evaluate_profile(
                    self.profile("REGISTRY_FAST_PATH", **{field: value}),
                    self.budget,
                )
                self.assertEqual(result["outcome"], "BLOCKED_INCOMPLETE")
                self.assertIn(
                    code,
                    result["completeness_blocker_codes"],
                )

    def test_10_incomplete_processing_and_source_coverage_block(self) -> None:
        profile = self.profile(
            "FOUR_SOURCE_FULL_INVENTORY",
            processed_count=3,
            source_classes=("AGENTS", "CLAUDE", "CODEX"),
        )
        result = evaluate_profile(profile, self.budget)
        self.assertEqual(result["outcome"], "BLOCKED_INCOMPLETE")
        self.assertEqual(
            result["completeness_blocker_codes"],
            [
                "FOUR_SOURCE_COVERAGE_INCOMPLETE",
                "INPUT_PROCESSED_COUNT_MISMATCH",
            ],
        )

    def test_11_unfiltered_capability_all_pairs_is_forbidden(self) -> None:
        result = evaluate_profile(
            self.profile(
                "CAPABILITY_GRAPH_PAIRING",
                graph_pairing_mode="UNCONDITIONAL_ALL_PAIRS",
            ),
            self.budget,
        )
        self.assertEqual(result["outcome"], "BLOCKED_INCOMPLETE")
        self.assertIn(
            "UNFILTERED_ALL_PAIR_ANALYSIS_FORBIDDEN",
            result["completeness_blocker_codes"],
        )

    def test_12_each_cache_axis_is_mandatory(self) -> None:
        for field in policy.CACHE_KEY_FIELDS:
            with self.subTest(field=field):
                keys = self.cache_keys()
                keys.pop(field)
                result = evaluate_profile(
                    self.profile(
                        "EVALUATION_CACHE",
                        cache_key_digests=keys,
                    ),
                    self.budget,
                )
                self.assertEqual(result["outcome"], "BLOCKED_INCOMPLETE")
                self.assertIn(
                    "EVALUATION_CACHE_KEY_INCOMPLETE",
                    result["completeness_blocker_codes"],
                )

    def test_13_watermark_on_failed_profile_is_an_extra_blocker(self) -> None:
        result = evaluate_profile(
            self.profile(
                "SINGLE_GIT_SHARD",
                output_artifact_bytes=policy.MAX_SHARD_BYTES + 1,
                watermark_advanced=True,
            ),
            self.budget,
        )
        self.assertEqual(result["outcome"], "BLOCKED_INCOMPLETE")
        self.assertIn(
            "WATERMARK_ADVANCED_ON_FAILURE",
            result["completeness_blocker_codes"],
        )

    def test_14_schema_validation_is_offline_and_public_safe(self) -> None:
        acceptance = load_au040_acceptance()
        profile_schema = builder.build_profile_schema()
        budget_schema = builder.build_budget_schema(self.budget)
        readiness_schema = builder.build_readiness_schema(self.readiness)
        contract = builder._extend_bundle(
            acceptance.bundle,
            {
                policy.PROFILE_SCHEMA_ID: profile_schema,
                policy.BUDGET_SCHEMA_ID: budget_schema,
                builder.READINESS_SCHEMA_ID: readiness_schema,
            },
            {
                policy.PROFILE_SCHEMA_ID: policy.PROFILE_SELF_POINTER,
                policy.BUDGET_SCHEMA_ID: policy.BUDGET_SELF_POINTER,
                builder.READINESS_SCHEMA_ID: "/artifact_digest",
            },
        )
        profile = self.profile("EVALUATION_CACHE")
        for instance, schema_id in (
            (profile, policy.PROFILE_SCHEMA_ID),
            (self.budget, policy.BUDGET_SCHEMA_ID),
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

    def test_15_self_consistent_budget_weakening_is_rejected(self) -> None:
        altered = copy.deepcopy(self.budget)
        altered["completeness_invariants"][
            "silent_sampling_permitted"
        ] = True
        altered["artifact_digest"] = canonical_digest(
            altered,
            policy.BUDGET_SELF_POINTER,
        )
        with self.assertRaisesRegex(
            CapacityBudgetError,
            "CAPACITY_BUDGET_CONTRACT_DRIFT",
        ):
            validate_budget_contract(altered)

    def test_16_guard_has_no_runtime_or_mutation_capability(self) -> None:
        source = inspect.getsource(policy)
        for forbidden in (
            "from pathlib",
            "import os",
            "import subprocess",
            "import socket",
            "import time",
            "Path(",
            "open(",
            "write_bytes(",
            "unlink(",
        ):
            self.assertNotIn(forbidden, source)
        nonmutation = self.readiness["nonmutation"]
        self.assertFalse(nonmutation["real_profile_executed"])
        self.assertFalse(nonmutation["cache_write_permitted"])
        self.assertFalse(nonmutation["shard_write_permitted"])
        self.assertFalse(nonmutation["watermark_advance_permitted"])

    def test_17_handoff_binds_exact_m066_artifact_digests(self) -> None:
        handoff = (
            builder.GOVERNANCE_DIR / "HANDOFF.md"
        ).read_text(encoding="utf-8")
        expected = {
            builder.COMPONENT_PATH: (
                "f306b278179eb4abe5abb5bd96e6af4b5d41683394fa2473cd0cc81016a2b053"
            ),
            builder.BUDGET_PATH: (
                "858b6c7c6607b1feb05394cb84fc8c73b4a8f475f39aa2f2eb11effd16f4e01a"
            ),
            builder.READINESS_PATH: (
                "000154c32d895b35960cadbad80582c09121ee1103a31a63577ad8a6cf5b1a3d"
            ),
            builder.PROFILE_SCHEMA_PATH: (
                "1ca909c5d641618d93dbbd528500999f84bbbeb1f935de1b704ca0387f9e1a14"
            ),
            builder.BUDGET_SCHEMA_PATH: (
                "531fb0c1b0bdac9399854c040ec8cb6a2b0680c38a7a9db9b2d38907198cb93f"
            ),
            builder.READINESS_SCHEMA_PATH: (
                "1d88c6b2363a76804a42beb8ce3e1ac978ab4efe81a4c3312f32d43f0ee5957d"
            ),
        }
        for path, digest in expected.items():
            with self.subTest(path=path):
                self.assertEqual(
                    hashlib.sha256(path.read_bytes()).hexdigest(),
                    digest,
                )
                self.assertIn(digest, handoff)
        self.assertIn(self.budget["artifact_digest"], handoff)
        self.assertIn(self.readiness["artifact_digest"], handoff)


if __name__ == "__main__":
    unittest.main()
