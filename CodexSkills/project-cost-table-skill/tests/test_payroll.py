import json
import unittest
from dataclasses import replace
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.formulas import FormulaKind, FormulaScope
from project_cost_table.payroll import (
    ApprovedTimeRecord,
    LaborClassification,
    PayComponentRegistry,
    PayComponentRule,
    PayComponentTreatment,
    PayrollAllocationPolicy,
    PayrollControl,
    PayrollError,
    PayrollRecord,
    PayrollRecordKind,
    TimeAllocationStatus,
    reconcile_payroll,
)
from r8_helpers import (
    EVIDENCE,
    INPUT_HASH,
    REQUEST_HASH,
    component_registry,
    formula_profile,
    opaque,
    payroll_policy,
)


MODULE_ROOT = Path(__file__).resolve().parents[1]
EMPLOYEE = opaque("employee_", "employee")
MAPPING = opaque("identity_resolution_", "mapping")


def payroll_formula():
    return formula_profile(
        "payroll-formula",
        formula_id="FORM-PAYROLL-V2",
        kind=FormulaKind.PAYROLL_TIME_ALLOCATION,
        profile_scope=FormulaScope("COST_ACCRUED", "ENTITY-S", "*", "*"),
    )


def payroll_record(
    seed: str,
    *,
    component: str = "BASE",
    amount: int = 10000,
    kind: PayrollRecordKind = PayrollRecordKind.REGULAR,
    adjusts=None,
    reverses=None,
    labor: LaborClassification = LaborClassification.EMPLOYEE_PAYROLL,
):
    return PayrollRecord(
        record_id=opaque("payroll_record_", seed), legal_entity_id="ENTITY-S", employee_id=EMPLOYEE,
        payroll_period="2001-01", component_id=component, amount_minor=amount, record_kind=kind,
        labor_classification=labor, adjusts_record_id=adjusts, reverses_record_id=reverses,
        evidence_refs=(EVIDENCE,), bound_input_hash=INPUT_HASH,
    )


def time_record(
    seed: str,
    units: int,
    *,
    project="PROJECT-S",
    wbs="WBS-S",
    status: TimeAllocationStatus = TimeAllocationStatus.PROJECT,
    project_entity="ENTITY-S",
):
    allocated = status is TimeAllocationStatus.PROJECT
    return ApprovedTimeRecord(
        time_record_id=opaque("time_record_", seed), legal_entity_id="ENTITY-S",
        project_legal_entity_id=project_entity if allocated else None, employee_id=EMPLOYEE,
        payroll_period="2001-01", approved_time_units=units, time_unit="HOUR_X100",
        allocation_status=status, canonical_project_id=project if allocated else None,
        wbs_or_cost_code=wbs if allocated else None, mapping_resolution_ref=MAPPING if allocated else None,
        evidence_refs=(EVIDENCE,), bound_input_hash=INPUT_HASH,
    )


def control(payroll_total=11000, time_total=100):
    return PayrollControl(
        control_id=opaque("payroll_control_", "control"), legal_entity_id="ENTITY-S",
        employee_id=EMPLOYEE, payroll_period="2001-01", payroll_control_total_minor=payroll_total,
        approved_time_control_units=time_total, time_unit="HOUR_X100",
        evidence_refs=(EVIDENCE,), bound_input_hash=INPUT_HASH,
    )


class PayrollAllocationTests(unittest.TestCase):
    def test_public_templates_are_inactive_parseable_and_schema_valid(self) -> None:
        pairs = (
            ("pay_component_registry.template.yml", "pay_component_registry.schema.json", PayComponentRegistry.from_yaml),
            ("payroll_allocation_policy.template.yml", "payroll_allocation_policy.schema.json", PayrollAllocationPolicy.from_yaml),
        )
        for config_name, schema_name, loader in pairs:
            with self.subTest(config=config_name):
                path = MODULE_ROOT / "config" / config_name
                result = loader(path)
                self.assertEqual(result.status, "TEMPLATE_NOT_ACTIVE")
                with self.assertRaises(PayrollError):
                    result.validate(require_active=True)
                payload = yaml.safe_load(path.read_text(encoding="utf-8"))
                schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
                self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)), [])

    def test_fully_loaded_cost_time_and_allocation_controls_reconcile(self) -> None:
        records = (payroll_record("base"), payroll_record("deduction", component="DEDUCTION", amount=1000))
        times = (time_record("project", 60), time_record("unallocated", 40, status=TimeAllocationStatus.UNALLOCATED))
        result = reconcile_payroll(
            records, times, (control(),), component_registry=component_registry(),
            allocation_policy=payroll_policy(), formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
        )
        self.assertEqual(result.status, "PASS_R8_PAYROLL_CONTROLS_NOT_METRIC")
        reconciliation = result.reconciliations[0]
        self.assertEqual(reconciliation.payroll_control_delta_minor, 0)
        self.assertEqual(reconciliation.approved_time_delta_units, 0)
        self.assertEqual(reconciliation.allocable_employer_cost_minor, 10000)
        self.assertEqual(reconciliation.excluded_component_amount_minor, 1000)
        self.assertEqual(reconciliation.project_allocated_amount_minor, 6000)
        self.assertEqual(reconciliation.unallocated_payroll_amount_minor, 4000)
        self.assertEqual(reconciliation.allocation_delta_minor, 0)
        self.assertTrue(all(item.metric_inclusion_status == "NOT_EVALUATED_R8" for item in result.allocations))
        schema = json.loads((MODULE_ROOT / "schemas" / "payroll_allocation.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(list(Draft202012Validator(schema).iter_errors(result.as_dict())), [])

    def test_control_mismatch_blocks_and_keeps_cost_in_visible_unallocated_pool(self) -> None:
        result = reconcile_payroll(
            (payroll_record("base"), payroll_record("deduction", component="DEDUCTION", amount=1000)),
            (time_record("project", 50), time_record("unallocated", 40, status=TimeAllocationStatus.UNALLOCATED)),
            (control(payroll_total=12000, time_total=100),),
            component_registry=component_registry(), allocation_policy=payroll_policy(),
            formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
        )
        self.assertEqual(result.status, "BLOCKED_R8_PAYROLL_CONTROLS")
        reconciliation = result.reconciliations[0]
        self.assertEqual(
            set(reconciliation.reason_codes), {"PAYROLL_CONTROL_DELTA", "APPROVED_TIME_CONTROL_DELTA"}
        )
        self.assertEqual(reconciliation.project_allocated_amount_minor, 0)
        self.assertEqual(reconciliation.unallocated_payroll_amount_minor, 10000)

    def test_unknown_component_never_defaults_to_zero_or_included(self) -> None:
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (payroll_record("unknown", component="UNKNOWN", amount=100),),
                (time_record("project", 100),), (control(payroll_total=100, time_total=100),),
                component_registry=component_registry(), allocation_policy=payroll_policy(),
                formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
            )
        self.assertEqual(caught.exception.code, "PAY_COMPONENT_UNKNOWN")

    def test_missing_wbs_and_cross_entity_time_are_hard_blockers(self) -> None:
        missing_wbs = time_record("missing-wbs", 100, wbs=None)
        with self.assertRaises(PayrollError) as caught:
            missing_wbs.validate()
        self.assertEqual(caught.exception.code, "PAYROLL_PROJECT_WBS_REQUIRED")
        cross_entity = time_record("cross", 100, project_entity="ENTITY-T")
        with self.assertRaises(PayrollError) as caught:
            cross_entity.validate()
        self.assertEqual(caught.exception.code, "PAYROLL_CROSS_ENTITY")

    def test_external_labor_is_not_inferred_as_employee_payroll(self) -> None:
        with self.assertRaises(PayrollError) as caught:
            payroll_record("external", labor=LaborClassification.EXTERNAL_LABOR).validate()
        self.assertEqual(caught.exception.code, "PAYROLL_EXTERNAL_LABOR_MISCLASSIFIED")
        external_rule = PayComponentRule(
            "OUTSIDE", PayComponentTreatment.EXTERNAL_LABOR_NOT_PAYROLL, "ENTITY-S",
            "2000-01-01", None, (EVIDENCE,),
        )
        registry = component_registry(rules=(external_rule,))
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (payroll_record("outside", component="OUTSIDE", amount=100),), (time_record("project", 100),),
                (control(payroll_total=100, time_total=100),), component_registry=registry,
                allocation_policy=payroll_policy(), formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
            )
        self.assertEqual(caught.exception.code, "PAYROLL_EXTERNAL_LABOR_COMPONENT")

    def test_reversal_requires_exact_lineage_and_amount(self) -> None:
        original = payroll_record("original", amount=10000)
        reversal = payroll_record(
            "reversal", amount=-10000, kind=PayrollRecordKind.REVERSAL, reverses=original.record_id
        )
        result = reconcile_payroll(
            (original, reversal), (time_record("project", 100),), (control(payroll_total=0, time_total=100),),
            component_registry=component_registry(), allocation_policy=payroll_policy(),
            formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
        )
        self.assertEqual(result.reconciliations[0].allocable_employer_cost_minor, 0)
        wrong = replace(reversal, amount_minor=-9999)
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (original, wrong), (time_record("project-2", 100),), (control(payroll_total=1, time_total=100),),
                component_registry=component_registry(), allocation_policy=payroll_policy(),
                formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
            )
        self.assertEqual(caught.exception.code, "PAYROLL_REVERSAL_AMOUNT")

    def test_independent_rounding_cannot_overallocate_one_cent(self) -> None:
        records = (payroll_record("one-cent", amount=1),)
        times = (
            time_record("project-a", 1, project="PROJECT-A", wbs="WBS-A"),
            time_record("project-b", 1, project="PROJECT-B", wbs="WBS-B"),
        )
        result = reconcile_payroll(
            records, times, (control(payroll_total=1, time_total=2),),
            component_registry=component_registry(), allocation_policy=payroll_policy(),
            formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
        )
        self.assertEqual(result.status, "BLOCKED_R8_PAYROLL_CONTROLS")
        reconciliation = result.reconciliations[0]
        self.assertIn("PAYROLL_ROUNDING_OVERALLOCATION", reconciliation.reason_codes)
        self.assertEqual(reconciliation.project_allocated_amount_minor, 2)
        self.assertEqual(reconciliation.unallocated_payroll_amount_minor, -1)
        self.assertEqual(reconciliation.allocation_delta_minor, 0)

    def test_component_registry_overlap_and_request_drift_fail_closed(self) -> None:
        rule_a = PayComponentRule("BASE", PayComponentTreatment.INCLUDED_EMPLOYER_COST, "*", "2000-01-01", None, (EVIDENCE,))
        rule_b = PayComponentRule("BASE", PayComponentTreatment.EXCLUDED_FROM_EMPLOYER_COST, "ENTITY-S", "2001-01-01", None, (EVIDENCE,))
        with self.assertRaises(PayrollError) as caught:
            component_registry(rules=(rule_a, rule_b)).validate(require_active=True)
        self.assertEqual(caught.exception.code, "PAY_COMPONENT_ACTIVE_OVERLAP")
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (payroll_record("base"),), (time_record("project", 100),),
                (control(payroll_total=10000, time_total=100),), component_registry=component_registry(),
                allocation_policy=payroll_policy(), formula_profile=payroll_formula(), request_hash="f" * 64, requested_metric_id="COST_ACCRUED",
            )
        self.assertEqual(caught.exception.code, "PAYROLL_REQUEST_BINDING")
        drifted_record = replace(payroll_record("drifted"), bound_input_hash="7" * 64)
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (drifted_record,), (time_record("project-drift", 100),),
                (control(payroll_total=10000, time_total=100),), component_registry=component_registry(),
                allocation_policy=payroll_policy(), formula_profile=payroll_formula(), request_hash=REQUEST_HASH, requested_metric_id="COST_ACCRUED",
            )
        self.assertEqual(caught.exception.code, "PAYROLL_INPUT_BINDING")
        with self.assertRaises(PayrollError) as caught:
            reconcile_payroll(
                (payroll_record("metric"),), (time_record("project-metric", 100),),
                (control(payroll_total=10000, time_total=100),), component_registry=component_registry(),
                allocation_policy=payroll_policy(), formula_profile=payroll_formula(), request_hash=REQUEST_HASH,
                requested_metric_id="COST_POSTED_ACTUAL",
            )
        self.assertEqual(caught.exception.code, "PAYROLL_FORMULA_SCOPE")


if __name__ == "__main__":
    unittest.main()
