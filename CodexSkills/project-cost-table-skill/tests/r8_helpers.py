from __future__ import annotations

import hashlib
from datetime import date
from typing import Mapping, Optional, Tuple

from project_cost_table.formulas import (
    AuthorityMode,
    FormulaExpression,
    FormulaKind,
    FormulaProfile,
    FormulaScope,
    FormulaStatus,
    FormulaTestVector,
    evaluate_formula_inputs,
)
from project_cost_table.money import RoundingLayer
from project_cost_table.payroll import (
    PayComponentRegistry,
    PayComponentRule,
    PayComponentTreatment,
    PayrollAllocationPolicy,
)


EVIDENCE = "evidence://sha256/" + "a" * 64
EVIDENCE_B = "evidence://sha256/" + "b" * 64
POLICY = "policy://sha256/" + "c" * 64
RESOLUTION = "resolution_" + "d" * 32
REQUEST_HASH = "1" * 64
INPUT_HASH = "2" * 64
CONFIG_HASH = "3" * 64


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def opaque(prefix: str, seed: str) -> str:
    return prefix + digest(seed)[:32]


def scope(
    *, metric: str = "COST_ACCRUED", entity: str = "ENTITY-S", project: str = "PROJECT-S", wbs: str = "WBS-S"
) -> FormulaScope:
    return FormulaScope(metric, entity, project, wbs)


def formula_profile(
    seed: str,
    *,
    formula_id: str = "FORM-MGMT-V2",
    kind: FormulaKind = FormulaKind.MANAGEMENT_RATE,
    status: FormulaStatus = FormulaStatus.ACTIVE,
    profile_scope: Optional[FormulaScope] = None,
    parameters: Optional[Mapping[str, int]] = None,
    valid_from: str = "2000-01-01",
    valid_to: Optional[str] = None,
    supersedes: Optional[str] = None,
    authority_mode: AuthorityMode = AuthorityMode.COMPANY_POLICY,
    company_policy_refs: Tuple[str, ...] = (POLICY,),
    evidence_refs: Tuple[str, ...] = (EVIDENCE,),
    input_resolution_refs: Tuple[str, ...] = (),
    bound_request_hash: Optional[str] = REQUEST_HASH,
) -> FormulaProfile:
    expressions = {
        FormulaKind.MANAGEMENT_RATE: FormulaExpression.RATE_TIMES_BASE,
        FormulaKind.PAYROLL_TIME_ALLOCATION: FormulaExpression.APPROVED_TIME_PRORATION,
        FormulaKind.PROJECT_TAX_RATE: FormulaExpression.RATE_TIMES_BASE,
        FormulaKind.CAPITAL_INTEREST: FormulaExpression.SIMPLE_INTEREST_DAILY,
        FormulaKind.FX_RATE: FormulaExpression.FX_RATE_TIMES_AMOUNT,
    }
    layers = {
        FormulaKind.MANAGEMENT_RATE: RoundingLayer.LINE_FORMULA,
        FormulaKind.PAYROLL_TIME_ALLOCATION: RoundingLayer.ALLOCATION_RESIDUAL,
        FormulaKind.PROJECT_TAX_RATE: RoundingLayer.TAX_CALCULATION,
        FormulaKind.CAPITAL_INTEREST: RoundingLayer.LINE_FORMULA,
        FormulaKind.FX_RATE: RoundingLayer.LINE_FORMULA,
    }
    if parameters is None:
        if kind in {FormulaKind.MANAGEMENT_RATE, FormulaKind.PROJECT_TAX_RATE, FormulaKind.FX_RATE}:
            parameters = {"rate_numerator": 2, "rate_denominator": 100}
        elif kind is FormulaKind.CAPITAL_INTEREST:
            parameters = {"annual_rate_numerator": 5, "annual_rate_denominator": 100, "day_count_denominator": 365}
        else:
            parameters = {}
    profile = FormulaProfile(
        profile_id=opaque("formula_profile_", seed),
        profile_version="1.0.0",
        formula_id=formula_id,
        formula_kind=kind,
        expression_id=expressions[kind],
        status=status,
        valid_from=valid_from,
        valid_to=valid_to,
        scope=profile_scope or scope(),
        base_currency="CNY",
        rounding_layer=layers[kind],
        rounding_mode="ROUND_HALF_UP",
        parameters=dict(parameters),
        authority_mode=authority_mode,
        company_policy_refs=company_policy_refs,
        evidence_refs=evidence_refs,
        input_resolution_refs=input_resolution_refs,
        bound_request_hash=bound_request_hash,
        bound_input_hash=INPUT_HASH if bound_request_hash else None,
        bound_config_hash=CONFIG_HASH if bound_request_hash else None,
        supersedes=supersedes,
        test_vectors=(),
        content_sha256=digest("profile:" + seed),
    )
    if status is FormulaStatus.ACTIVE:
        if kind in {FormulaKind.MANAGEMENT_RATE, FormulaKind.PROJECT_TAX_RATE}:
            inputs = {"base_amount_minor": 10050}
        elif kind is FormulaKind.PAYROLL_TIME_ALLOCATION:
            inputs = {"employer_cost_minor": 10001, "approved_project_time_units": 1, "approved_total_time_units": 2}
        elif kind is FormulaKind.CAPITAL_INTEREST:
            inputs = {"principal_minor": 100000, "elapsed_days": 365}
        else:
            inputs = {"base_amount_minor": 10000}
        if kind is FormulaKind.FX_RATE:
            expected = 0
        else:
            expected = evaluate_formula_inputs(profile, inputs)
        profile = FormulaProfile(**{**profile.__dict__, "test_vectors": (FormulaTestVector("synthetic-vector", inputs, expected),)})
    return profile


def component_registry(*, rules: Optional[Tuple[PayComponentRule, ...]] = None) -> PayComponentRegistry:
    if rules is None:
        rules = (
            PayComponentRule("BASE", PayComponentTreatment.INCLUDED_EMPLOYER_COST, "ENTITY-S", "2000-01-01", None, (EVIDENCE,)),
            PayComponentRule("DEDUCTION", PayComponentTreatment.EXCLUDED_FROM_EMPLOYER_COST, "ENTITY-S", "2000-01-01", None, (EVIDENCE,)),
        )
    return PayComponentRegistry(
        registry_id=opaque("pay_component_registry_", "registry"),
        registry_version="1.0.0",
        status="ACTIVE",
        valid_from="2000-01-01",
        valid_to=None,
        base_currency="CNY",
        rules=rules,
        evidence_refs=(EVIDENCE,),
        company_policy_refs=(POLICY,),
        bound_config_hash=CONFIG_HASH,
        content_sha256=digest("component-registry"),
    )


def payroll_policy() -> PayrollAllocationPolicy:
    return PayrollAllocationPolicy(
        policy_id=opaque("payroll_policy_", "policy"),
        policy_version="1.0.0",
        status="ACTIVE",
        valid_from="2000-01-01",
        valid_to=None,
        allocation_method="APPROVED_TIME_PRO_RATA",
        time_unit="HOUR_X100",
        residual_destination="UNALLOCATED_PAYROLL_POOL",
        evidence_refs=(EVIDENCE,),
        company_policy_refs=(POLICY,),
        input_resolution_refs=(),
        bound_request_hash=REQUEST_HASH,
        bound_input_hash=INPUT_HASH,
        bound_config_hash=CONFIG_HASH,
        content_sha256=digest("payroll-policy"),
    )
