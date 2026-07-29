from __future__ import annotations

import copy
import unittest

from wbi_core.status import build_status_summary, validate_status_summary

HASH = "a" * 64


def base_cost():
    return {
        "total_tokens": 10,
        "known_total_tokens": 10,
        "unknown_token_invocations": 0,
        "total_monetary_cost": 1.0,
        "known_monetary_cost": 1.0,
        "unknown_cost_invocations": 0,
        "currency": "USD",
    }


def base_summary():
    return build_status_summary(
        "run-1", "candidate-1", HASH, "2026-07-26",
        {
            "control_plane_status": "PASS",
            "benchmark_integrity_status": "VALID",
            "outcome_status": "SUPPORTED",
            "cost_evidence_status": "MEASURED",
            "independent_review_status": "PASS",
            "engineering_release_status": "INSTALLABLE",
            "formal_promotion_status": "PASS",
            "current_environment_strength_status": "PARETO_UNDOMINATED_FOR_VERIFIED_CURRENT_ENVIRONMENT",
        },
        {name: ["evidence-backed"] for name in (
            "control_plane_status", "benchmark_integrity_status", "outcome_status", "cost_evidence_status",
            "independent_review_status", "engineering_release_status", "formal_promotion_status",
            "current_environment_strength_status"
        )},
        cost_evidence=base_cost(),
    )


class StatusTests(unittest.TestCase):
    def test_valid_formal_pass(self):
        self.assertEqual(validate_status_summary(base_summary()), [])

    def test_engineering_installable_can_coexist_with_formal_blocked(self):
        value = base_summary()
        value["domains"]["independent_review_status"]["value"] = "UNAVAILABLE"
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        self.assertEqual(validate_status_summary(value), [])

    def test_formal_pass_requires_independent_review(self):
        value = base_summary()
        value["domains"]["independent_review_status"]["value"] = "UNAVAILABLE"
        errors = validate_status_summary(value)
        self.assertTrue(any("independent_review_status=PASS" in item for item in errors))

    def test_formal_pass_rejects_partial_cost_evidence(self):
        value = base_summary()
        value["domains"]["cost_evidence_status"]["value"] = "PARTIAL"
        value["cost_evidence"] = {
            "total_tokens": None, "known_total_tokens": 10, "unknown_token_invocations": 1,
            "total_monetary_cost": None, "known_monetary_cost": 1.0, "unknown_cost_invocations": 1,
            "currency": "USD",
        }
        errors = validate_status_summary(value)
        self.assertTrue(any("complete MEASURED or ESTIMATED" in item for item in errors))

    def test_outcome_supported_requires_valid_benchmark(self):
        value = base_summary()
        value["domains"]["benchmark_integrity_status"]["value"] = "INCOMPLETE"
        errors = validate_status_summary(value)
        self.assertTrue(any("benchmark integrity VALID" in item for item in errors))

    def test_regressed_requires_formal_fail(self):
        value = base_summary()
        value["domains"]["outcome_status"]["value"] = "REGRESSED"
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        self.assertTrue(any("REGRESSED requires" in item for item in validate_status_summary(value)))

    def test_unknown_cost_is_not_zero(self):
        value = base_summary()
        value["domains"]["cost_evidence_status"]["value"] = "UNKNOWN"
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        value["cost_evidence"] = {
            "total_tokens": 0, "known_total_tokens": 0, "unknown_token_invocations": 1,
            "total_monetary_cost": 0, "known_monetary_cost": 0.0, "unknown_cost_invocations": 1,
            "currency": None,
        }
        errors = validate_status_summary(value)
        self.assertTrue(any("UNKNOWN cost evidence" in item for item in errors))

    def test_partial_unknowns_cannot_serialize_zero_totals(self):
        value = base_summary()
        value["domains"]["cost_evidence_status"]["value"] = "PARTIAL"
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        value["cost_evidence"] = {
            "total_tokens": 0, "known_total_tokens": 0, "unknown_token_invocations": 2,
            "total_monetary_cost": 0.0, "known_monetary_cost": 0.0, "unknown_cost_invocations": 2,
            "currency": "USD",
        }
        errors = validate_status_summary(value)
        self.assertTrue(any("unknown token invocations require" in item for item in errors))
        self.assertTrue(any("unknown cost invocations require" in item for item in errors))

    def test_partial_requires_actual_unknown_count(self):
        value = base_summary()
        value["domains"]["cost_evidence_status"]["value"] = "PARTIAL"
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        errors = validate_status_summary(value)
        self.assertTrue(any("PARTIAL cost evidence requires" in item for item in errors))

    def test_measured_requires_complete_totals(self):
        value = base_summary()
        value["cost_evidence"]["total_tokens"] = None
        errors = validate_status_summary(value)
        self.assertTrue(any("MEASURED cost evidence requires" in item for item in errors))

    def test_estimated_requires_method(self):
        value = base_summary()
        value["domains"]["cost_evidence_status"]["value"] = "ESTIMATED"
        errors = validate_status_summary(value)
        self.assertTrue(any("estimation_methods" in item for item in errors))
        value["cost_evidence"]["estimation_methods"] = ["provider price table dated 2026-07-26"]
        self.assertEqual(validate_status_summary(value), [])

    def test_formal_pass_requires_current_environment_strength(self):
        value = base_summary()
        value["domains"]["current_environment_strength_status"]["value"] = "NOT_PROVEN"
        errors = validate_status_summary(value)
        self.assertTrue(any("current_environment_strength_status=PARETO_UNDOMINATED" in item for item in errors))

    def test_expired_or_regressed_strength_cannot_formally_pass(self):
        value = base_summary()
        value["domains"]["current_environment_strength_status"]["value"] = "REHEAT_REQUIRED"
        self.assertTrue(any("must block formal promotion" in item for item in validate_status_summary(value)))
        value["domains"]["formal_promotion_status"]["value"] = "BLOCKED"
        value["domains"]["current_environment_strength_status"]["value"] = "REGRESSED"
        self.assertTrue(any("REGRESSED requires formal promotion FAIL" in item for item in validate_status_summary(value)))

    def test_candidate_tree_hash_must_be_real_sha256(self):
        value = base_summary()
        value["identity"]["candidate_tree_hash"] = "not-a-hash"
        self.assertTrue(any("candidate_tree_hash" in item for item in validate_status_summary(value)))

    def test_ambiguous_top_level_pass_rejected(self):
        value = base_summary()
        value["status"] = "PASS"
        self.assertTrue(any("ambiguous" in item for item in validate_status_summary(value)))

    def test_missing_reason_rejected(self):
        value = copy.deepcopy(base_summary())
        value["domains"]["outcome_status"]["reasons"] = []
        self.assertTrue(any("outcome_status reasons" in item for item in validate_status_summary(value)))


if __name__ == "__main__":
    unittest.main()
