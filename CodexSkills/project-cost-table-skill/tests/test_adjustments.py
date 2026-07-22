import json
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.adjustments import (
    AdjustmentError,
    AdjustmentStatus,
    AmountSign,
    ManualAdjustment,
    ReversalPolicy,
    validate_adjustment_chain,
)
from r8_helpers import CONFIG_HASH, EVIDENCE, INPUT_HASH, POLICY, REQUEST_HASH, opaque


MODULE_ROOT = Path(__file__).resolve().parents[1]


def adjustment(
    seed: str,
    *,
    amount=100,
    status=AdjustmentStatus.ACTIVE,
    supersedes=None,
    reverses=None,
    business_date="2001-01-01",
    expires_on=None,
):
    return ManualAdjustment(
        adjustment_id=opaque("adjustment_", seed), metric_id="COST_ACCRUED", lifecycle_stage="ACCRUAL",
        legal_entity_id="ENTITY-S", canonical_project_id="PROJECT-S", wbs_or_cost_code="WBS-S",
        cost_category="SYNTHETIC_ADJUSTMENT", amount_minor=amount,
        amount_sign=AmountSign.POSITIVE if amount > 0 else AmountSign.NEGATIVE,
        business_date=business_date, posting_period="2001-01", reason="Synthetic evidence-bound adjustment",
        evidence_refs=(EVIDENCE,), formula_profile_id=opaque("formula_profile_", "adjustment-formula"),
        company_policy_refs=(POLICY,), input_resolution_refs=(), valid_from="2000-01-01", valid_to=None,
        expires_on=expires_on, reversal_policy=ReversalPolicy.EXPLICIT_REVERSAL_RECORD_REQUIRED,
        supersedes=supersedes, reverses=reverses, bound_request_hash=REQUEST_HASH,
        bound_input_hash=INPUT_HASH, bound_config_hash=CONFIG_HASH, status=status,
    )


class ManualAdjustmentTests(unittest.TestCase):
    def test_active_adjustment_is_hash_bound_and_never_a_metric(self) -> None:
        item = adjustment("active")
        result = validate_adjustment_chain((item,), as_of=date(2001, 1, 2), request_hash=REQUEST_HASH)
        self.assertEqual(result.status, "PASS_R8_ADJUSTMENT_CHAIN_NOT_METRIC")
        self.assertEqual(result.active_adjustment_ids, (item.adjustment_id,))
        self.assertEqual(result.metric_inclusion_status, "NOT_EVALUATED_R8")
        schema = json.loads((MODULE_ROOT / "schemas" / "manual_adjustment.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(
            list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(item.as_dict())), []
        )

    def test_sign_reason_evidence_and_authority_are_non_waivable(self) -> None:
        item = adjustment("invalid")
        cases = (
            (replace(item, amount_sign=AmountSign.NEGATIVE), "ADJUSTMENT_SIGN_MISMATCH"),
            (replace(item, reason=""), "ADJUSTMENT_SCHEMA"),
            (replace(item, evidence_refs=()), "ADJUSTMENT_EVIDENCE_REQUIRED"),
            (replace(item, company_policy_refs=(), input_resolution_refs=()), "ADJUSTMENT_AUTHORITY_REQUIRED"),
            (replace(item, metric_inclusion_status="INCLUDED"), "ADJUSTMENT_AUTHORITY_ESCALATION"),
        )
        for candidate, code in cases:
            with self.subTest(code=code):
                with self.assertRaises(AdjustmentError) as caught:
                    candidate.validate(as_of=date(2001, 1, 2))
                self.assertEqual(caught.exception.code, code)

    def test_supersession_is_append_only_and_scope_locked(self) -> None:
        prior = adjustment("prior", status=AdjustmentStatus.SUPERSEDED)
        current = adjustment("current", amount=120, supersedes=prior.adjustment_id, business_date="2001-02-01")
        result = validate_adjustment_chain((prior, current), as_of=date(2001, 2, 2), request_hash=REQUEST_HASH)
        self.assertEqual(result.active_adjustment_ids, (current.adjustment_id,))
        self.assertEqual(result.excluded_adjustment_ids, (prior.adjustment_id,))
        with self.assertRaises(AdjustmentError) as caught:
            validate_adjustment_chain(
                (prior, replace(current, canonical_project_id="PROJECT-T")),
                as_of=date(2001, 2, 2), request_hash=REQUEST_HASH,
            )
        self.assertEqual(caught.exception.code, "ADJUSTMENT_SCOPE_MISMATCH")

    def test_reversal_must_exactly_negate_target(self) -> None:
        original = adjustment("original", status=AdjustmentStatus.REVERSED)
        reversal = adjustment(
            "reversal", amount=-100, reverses=original.adjustment_id, business_date="2001-02-01"
        )
        validate_adjustment_chain((original, reversal), as_of=date(2001, 2, 2), request_hash=REQUEST_HASH)
        with self.assertRaises(AdjustmentError) as caught:
            validate_adjustment_chain(
                (original, replace(reversal, amount_minor=-99)),
                as_of=date(2001, 2, 2), request_hash=REQUEST_HASH,
            )
        self.assertEqual(caught.exception.code, "ADJUSTMENT_REVERSAL_AMOUNT")

    def test_expired_active_adjustment_blocks_instead_of_silently_disappearing(self) -> None:
        expired = adjustment("expired-active", expires_on="2001-01-31")
        with self.assertRaises(AdjustmentError) as caught:
            validate_adjustment_chain((expired,), as_of=date(2001, 2, 1), request_hash=REQUEST_HASH)
        self.assertEqual(caught.exception.code, "ADJUSTMENT_EXPIRED_ACTIVE")
        explicit = replace(expired, status=AdjustmentStatus.EXPIRED)
        result = validate_adjustment_chain((explicit,), as_of=date(2001, 2, 1), request_hash=REQUEST_HASH)
        self.assertEqual(result.active_adjustment_ids, ())
        self.assertEqual(result.excluded_adjustment_ids, (explicit.adjustment_id,))

    def test_request_drift_and_relation_cycles_fail_closed(self) -> None:
        item = adjustment("request")
        with self.assertRaises(AdjustmentError) as caught:
            validate_adjustment_chain((item,), as_of=date(2001, 1, 2), request_hash="9" * 64)
        self.assertEqual(caught.exception.code, "ADJUSTMENT_REQUEST_BINDING")


if __name__ == "__main__":
    unittest.main()
