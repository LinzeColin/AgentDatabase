from __future__ import annotations

import copy
import unittest

from wbi_core.telemetry import aggregate_invocations, validate_invocation


def invocation(identifier="i1", attempts=None, token_state="MEASURED", cost_state="MEASURED"):
    attempts = attempts or [identifier + "-a1"]
    unknown_tokens = {"input": None, "output": None, "cached": None, "reasoning": None}
    known_tokens = {"input": 10, "output": 5, "cached": 1, "reasoning": 2}
    return {
        "invocation_id": identifier,
        "phase": "evaluation",
        "provider": "provider",
        "model": "model",
        "runtime": "runtime",
        "adapter_version": "1",
        "started_at": "2026-07-26T00:00:00Z",
        "finished_at": "2026-07-26T00:00:01Z",
        "latency_ms": 1000,
        "human_minutes": 1,
        "attempt_ids": attempts,
        "retry_count": len(attempts) - 1,
        "token_evidence_status": token_state,
        "token_usage": unknown_tokens if token_state == "UNKNOWN" else known_tokens,
        "monetary_cost": {"status": cost_state, "amount": None if cost_state == "UNKNOWN" else 0.25, "currency": None if cost_state == "UNKNOWN" else "USD"},
    }


class TelemetryTests(unittest.TestCase):
    def test_valid_measured_invocation(self):
        self.assertEqual(validate_invocation(invocation()), [])

    def test_unknown_usage_requires_null_not_zero(self):
        row = invocation(token_state="UNKNOWN", cost_state="UNKNOWN")
        row["token_usage"]["input"] = 0
        row["monetary_cost"]["amount"] = 0
        errors = validate_invocation(row)
        self.assertTrue(any("UNKNOWN token usage" in item for item in errors))
        self.assertTrue(any("UNKNOWN monetary cost" in item for item in errors))

    def test_retry_count_matches_attempts(self):
        row = invocation(attempts=["a", "b"])
        row["retry_count"] = 0
        self.assertTrue(any("len(attempt_ids)-1" in item for item in validate_invocation(row)))

    def test_attempt_ids_unique_within_invocation(self):
        row = invocation(attempts=["a", "a"])
        self.assertTrue(any("attempt_ids must be unique" in item for item in validate_invocation(row)))

    def test_aggregate_retry_exactly_once(self):
        result = aggregate_invocations([invocation("i1", ["a1", "a2"]), invocation("i2", ["b1"])])
        self.assertEqual(result["aggregation_status"], "PASS")
        self.assertEqual(result["attempts"], 3)
        self.assertEqual(result["retries"], 1)
        self.assertEqual(result["total_tokens"], 36)

    def test_attempt_reuse_across_invocations_fails(self):
        result = aggregate_invocations([invocation("i1", ["same"]), invocation("i2", ["same"])])
        self.assertEqual(result["aggregation_status"], "FAIL")

    def test_partial_evidence_status(self):
        result = aggregate_invocations([invocation("i1"), invocation("i2", token_state="UNKNOWN", cost_state="UNKNOWN")])
        self.assertEqual(result["token_evidence_status"], "PARTIAL")
        self.assertEqual(result["cost_evidence_status"], "PARTIAL")
        self.assertIsNone(result["total_tokens"])
        self.assertEqual(result["known_total_tokens"], 18)
        self.assertEqual(result["unknown_token_invocations"], 1)
        self.assertIsNone(result["total_monetary_cost"])
        self.assertEqual(result["known_monetary_cost"], 0.25)
        self.assertEqual(result["unknown_cost_invocations"], 1)

    def test_all_unknown_aggregate_never_serializes_zero_total(self):
        result = aggregate_invocations([invocation("i1", token_state="UNKNOWN", cost_state="UNKNOWN")])
        self.assertIsNone(result["total_tokens"])
        self.assertEqual(result["known_total_tokens"], 0)
        self.assertIsNone(result["total_monetary_cost"])
        self.assertEqual(result["known_monetary_cost"], 0.0)

    def test_mixed_currency_fails(self):
        first, second = invocation("i1"), invocation("i2")
        second["monetary_cost"]["currency"] = "AUD"
        self.assertEqual(aggregate_invocations([first, second])["aggregation_status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
