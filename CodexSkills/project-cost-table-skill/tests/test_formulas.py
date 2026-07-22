import json
import os
import shutil
import tempfile
import unittest
from dataclasses import replace
from datetime import date
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.formulas import (
    AuthorityMode,
    FormulaError,
    FormulaKind,
    FormulaProfile,
    FormulaRegistry,
    FormulaStatus,
    InterestDayCountConvention,
    InterestInput,
    InterestMovement,
    InterestMovementKind,
    ProjectTaxRecord,
    TaxRecoverability,
    TaxSourceTier,
    assess_formula_readiness,
    calculate_interest,
    evaluate_formula,
    evaluate_project_tax,
    round_half_up_ratio,
)
from r8_helpers import (
    CONFIG_HASH,
    EVIDENCE,
    INPUT_HASH,
    POLICY,
    REQUEST_HASH,
    RESOLUTION,
    formula_profile,
    opaque,
    scope,
)


MODULE_ROOT = Path(__file__).resolve().parents[1]


class FormulaPolicyTests(unittest.TestCase):
    def test_integer_half_up_has_symmetric_ties_and_no_float_path(self) -> None:
        self.assertEqual(round_half_up_ratio(1, 2), 1)
        self.assertEqual(round_half_up_ratio(-1, 2), -1)
        self.assertEqual(round_half_up_ratio(1, 3), 0)
        with self.assertRaises(FormulaError):
            round_half_up_ratio(1.0, 2)

    def test_public_template_is_inactive_parseable_and_schema_valid(self) -> None:
        path = MODULE_ROOT / "config" / "formula_profile.template.yml"
        profile = FormulaProfile.from_yaml(path)
        self.assertEqual(profile.status, FormulaStatus.TEMPLATE_NOT_ACTIVE)
        with self.assertRaises(FormulaError) as caught:
            profile.validate(require_active=True)
        self.assertEqual(caught.exception.code, "FORMULA_PROFILE_NOT_ACTIVE")
        schema = json.loads((MODULE_ROOT / "schemas" / "formula_profile.schema.json").read_text(encoding="utf-8"))
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)), [])

    def test_active_profile_requires_authority_evidence_bindings_and_vector(self) -> None:
        base = formula_profile("valid")
        base.validate(require_active=True)
        invalid = (
            replace(base, evidence_refs=()),
            replace(base, company_policy_refs=()),
            replace(base, bound_input_hash=None),
            replace(base, test_vectors=()),
        )
        expected = (
            "FORMULA_EVIDENCE_REQUIRED", "FORMULA_POLICY_REQUIRED",
            "FORMULA_BINDING_HASH_REQUIRED", "FORMULA_TEST_VECTOR_REQUIRED",
        )
        for profile, code in zip(invalid, expected):
            with self.subTest(code=code):
                with self.assertRaises(FormulaError) as caught:
                    profile.validate(require_active=True)
                self.assertEqual(caught.exception.code, code)

    def test_management_formula_is_exact_bound_and_not_a_metric(self) -> None:
        profile = formula_profile("management")
        result = evaluate_formula(
            profile,
            inputs={"base_amount_minor": 10050},
            as_of=date(2001, 1, 1),
            scope=scope(),
            request_hash=REQUEST_HASH,
        )
        self.assertEqual(result.amount_minor, 201)
        self.assertEqual(result.metric_inclusion_status, "NOT_EVALUATED_R8")
        with self.assertRaises(FormulaError) as caught:
            evaluate_formula(profile, inputs={"base_amount_minor": 1}, as_of=date(2001, 1, 1), scope=scope(), request_hash="9" * 64)
        self.assertEqual(caught.exception.code, "FORMULA_REQUEST_BINDING_MISMATCH")

    def test_historical_observation_cannot_activate_management_rate(self) -> None:
        observed = formula_profile(
            "observed", status=FormulaStatus.REFERENCE_OBSERVED_NOT_ACTIVE, bound_request_hash=None
        )
        registry = FormulaRegistry((observed,))
        report = assess_formula_readiness(
            registry, requested_formula_ids=("FORM-MGMT-V2",), as_of=date(2001, 1, 1),
            scope=scope(), request_hash=REQUEST_HASH, input_hash=INPUT_HASH, config_hash=CONFIG_HASH,
        )
        self.assertEqual(report.overall_status, "BLOCKED_R8_POLICY_INPUTS")
        self.assertTrue(report.user_action_required)
        self.assertEqual(report.items[0].reason_code, "FORMULA_ACTIVE_PROFILE_MISSING")
        self.assertIn("SCOPE_REDUCED", report.items[0].allowed_resolutions)

    def test_unknown_formula_and_missing_profile_are_distinct_blockers(self) -> None:
        registry = FormulaRegistry((formula_profile("known"),))
        unknown = assess_formula_readiness(
            registry, requested_formula_ids=("FORM-UNKNOWN",), as_of=date(2001, 1, 1),
            scope=scope(), request_hash=REQUEST_HASH, input_hash=INPUT_HASH, config_hash=CONFIG_HASH,
        )
        self.assertEqual(unknown.items[0].reason_code, "UNKNOWN_FORMULA")
        ready = assess_formula_readiness(
            registry, requested_formula_ids=("FORM-MGMT-V2",), as_of=date(2001, 1, 1),
            scope=scope(), request_hash=REQUEST_HASH, input_hash=INPUT_HASH, config_hash=CONFIG_HASH,
        )
        self.assertEqual(ready.overall_status, "READY_R8_POLICY_INPUTS")
        self.assertFalse(ready.user_action_required)
        readiness_schema = json.loads(
            (MODULE_ROOT / "schemas" / "formula_readiness.schema.json").read_text(encoding="utf-8")
        )
        self.assertEqual(list(Draft202012Validator(readiness_schema).iter_errors(ready.as_dict())), [])
        drifted = assess_formula_readiness(
            registry, requested_formula_ids=("FORM-MGMT-V2",), as_of=date(2001, 1, 1),
            scope=scope(), request_hash=REQUEST_HASH, input_hash="8" * 64, config_hash=CONFIG_HASH,
        )
        self.assertEqual(drifted.items[0].reason_code, "FORMULA_RUN_BINDING_MISMATCH")

    def test_active_scope_overlap_blocks_while_effective_supersession_passes(self) -> None:
        left = formula_profile("left", valid_to="2001-12-31")
        overlap = formula_profile("overlap", valid_from="2001-01-01")
        with self.assertRaises(FormulaError) as caught:
            FormulaRegistry((left, overlap)).validate()
        self.assertEqual(caught.exception.code, "FORMULA_ACTIVE_SCOPE_OVERLAP")

        prior = formula_profile(
            "prior", status=FormulaStatus.SUPERSEDED, valid_to="2001-12-31", bound_request_hash=None
        )
        current = formula_profile("current", valid_from="2002-01-01", supersedes=prior.profile_id)
        FormulaRegistry((prior, current)).validate()
        selected = FormulaRegistry((prior, current)).select(
            formula_id="FORM-MGMT-V2", as_of=date(2002, 1, 1), scope=scope()
        )
        self.assertEqual(selected.profile_id, current.profile_id)

    def test_active_fx_is_registered_but_deferred(self) -> None:
        profile = formula_profile("fx", formula_id="FORM-FX-V2", kind=FormulaKind.FX_RATE)
        with self.assertRaises(FormulaError) as caught:
            profile.validate(require_active=True)
        self.assertEqual(caught.exception.code, "FX_DEFERRED_PRODUCT_0_2")

    def test_direct_project_tax_preserves_source_and_recomputed_deltas(self) -> None:
        profile = formula_profile(
            "tax", formula_id="FORM-TAX-V2", kind=FormulaKind.PROJECT_TAX_RATE,
            parameters={"rate_numerator": 6, "rate_denominator": 100},
            authority_mode=AuthorityMode.DIRECT_SOURCE_EVIDENCE, company_policy_refs=(),
        )
        record = ProjectTaxRecord(
            record_id=opaque("tax_record_", "tax"), scope=scope(), business_date="2001-01-01",
            gross_amount_minor=10600, tax_base_minor=10000, source_tax_amount_minor=600,
            rate_numerator=6, rate_denominator=100, invoice_type="SYNTHETIC_STANDARD",
            recoverability=TaxRecoverability.RECOVERABLE, recoverable_tax_minor=600,
            source_tier=TaxSourceTier.DIRECT_PROJECT_EVIDENCE, evidence_refs=(EVIDENCE,),
            company_policy_refs=(), input_resolution_refs=(), bound_input_hash=INPUT_HASH,
        )
        passed = evaluate_project_tax(record, profile, request_hash=REQUEST_HASH)
        self.assertEqual(passed.status, "PASS_R8_TAX_CONTROL")
        self.assertEqual(passed.tax_delta_minor, 0)
        mismatched = evaluate_project_tax(replace(record, source_tax_amount_minor=599, gross_amount_minor=10599, recoverable_tax_minor=599), profile, request_hash=REQUEST_HASH)
        self.assertEqual(mismatched.status, "BLOCKED_R8_TAX_ARITHMETIC")
        self.assertEqual(mismatched.source_tax_amount_minor, 599)
        self.assertEqual(mismatched.recomputed_tax_amount_minor, 600)
        with self.assertRaises(FormulaError) as caught:
            evaluate_project_tax(replace(record, bound_input_hash="7" * 64), profile, request_hash=REQUEST_HASH)
        self.assertEqual(caught.exception.code, "TAX_INPUT_BINDING_MISMATCH")

    def test_company_level_tax_allocation_needs_project_policy(self) -> None:
        record = ProjectTaxRecord(
            record_id=opaque("tax_record_", "allocation"), scope=scope(), business_date="2001-01-01",
            gross_amount_minor=100, tax_base_minor=100, source_tax_amount_minor=0,
            rate_numerator=0, rate_denominator=1, invoice_type="SYNTHETIC",
            recoverability=TaxRecoverability.NON_RECOVERABLE, recoverable_tax_minor=0,
            source_tier=TaxSourceTier.EVIDENCE_BACKED_ALLOCATION_POLICY,
            evidence_refs=(EVIDENCE,), company_policy_refs=(), input_resolution_refs=(RESOLUTION,),
            bound_input_hash=INPUT_HASH,
        )
        with self.assertRaises(FormulaError) as caught:
            record.validate()
        self.assertEqual(caught.exception.code, "TAX_ALLOCATION_POLICY_REQUIRED")

    def test_interest_uses_explicit_day_basis_and_cash_order(self) -> None:
        profile = formula_profile(
            "interest", formula_id="FORM-INTEREST-V2", kind=FormulaKind.CAPITAL_INTEREST,
            parameters={"annual_rate_numerator": 10, "annual_rate_denominator": 100, "day_count_denominator": 365},
        )
        movement = InterestMovement(
            movement_id=opaque("interest_movement_", "payment"), movement_date="2001-01-11",
            kind=InterestMovementKind.PAYMENT, principal_delta_minor=-50000, evidence_refs=(EVIDENCE,),
        )
        calculation = InterestInput(
            calculation_id=opaque("interest_calc_", "calc"), scope=scope(),
            start_date="2001-01-01", end_date="2001-01-21", opening_principal_minor=100000,
            movements=(movement,),
            same_day_order=(InterestMovementKind.RECEIPT, InterestMovementKind.PAYMENT, InterestMovementKind.PREPAYMENT),
            day_count_convention=InterestDayCountConvention.ACTUAL_365,
            evidence_refs=(EVIDENCE,), company_policy_refs=(POLICY,), input_resolution_refs=(),
            bound_input_hash=INPUT_HASH,
        )
        result = calculate_interest(calculation, profile, request_hash=REQUEST_HASH)
        expected = round_half_up_ratio(100000 * 10 * 10, 100 * 365) + round_half_up_ratio(50000 * 10 * 10, 100 * 365)
        self.assertEqual(result.interest_amount_minor, expected)
        self.assertEqual(result.ending_principal_minor, 50000)
        self.assertEqual(result.metric_inclusion_status, "NOT_EVALUATED_R8")
        with self.assertRaises(FormulaError) as caught:
            calculate_interest(replace(calculation, bound_input_hash="7" * 64), profile, request_hash=REQUEST_HASH)
        self.assertEqual(caught.exception.code, "INTEREST_INPUT_BINDING")
        with self.assertRaises(FormulaError) as caught:
            calculate_interest(
                replace(calculation, day_count_convention=InterestDayCountConvention.ACTUAL_360),
                profile,
                request_hash=REQUEST_HASH,
            )
        self.assertEqual(caught.exception.code, "INTEREST_DAY_COUNT_PROFILE_MISMATCH")
        with self.assertRaises(FormulaError) as caught:
            replace(calculation, same_day_order=(InterestMovementKind.RECEIPT, InterestMovementKind.PAYMENT)).validate()
        self.assertEqual(caught.exception.code, "INTEREST_CASH_ORDER")

    def test_strict_yaml_rejects_alias_duplicate_and_hardlink(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            alias = root / "alias.yml"
            alias.write_text("root: &value 1\ncopy: *value\n", encoding="utf-8")
            duplicate = root / "duplicate.yml"
            duplicate.write_text("schema_version: one\nschema_version: two\n", encoding="utf-8")
            for path in (alias, duplicate):
                with self.assertRaises(FormulaError) as caught:
                    FormulaProfile.from_yaml(path)
                self.assertEqual(caught.exception.code, "CONFIG_PARSE")
            copied = root / "profile.yml"
            linked = root / "profile-linked.yml"
            shutil.copyfile(MODULE_ROOT / "config" / "formula_profile.template.yml", copied)
            os.link(copied, linked)
            with self.assertRaises(FormulaError) as caught:
                FormulaProfile.from_yaml(copied)
            self.assertEqual(caught.exception.code, "CONFIG_PATH_UNSAFE")


if __name__ == "__main__":
    unittest.main()
