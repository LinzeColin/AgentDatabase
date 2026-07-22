import json
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator, FormatChecker

from project_cost_table.accounting_basis import BasisComponent, BasisDimension, BasisId, BasisView
from project_cost_table.events import EventDirection, LifecycleStage, RelationIdentityStatus
from project_cost_table.metrics import (
    AccountingMetricLineage,
    MetricDisposition,
    MetricError,
    MetricSourceControl,
    build_metric_batch,
    calculate_derived_metric,
    calculate_direct_metric,
    metric_control_from_basis_view,
    metric_fact_from_relation_event,
    metric_facts_from_basis_view,
)
from project_cost_table.statuses import (
    CalculationStatus,
    ExecutionStatus,
    GenerationStatus,
    InputReadinessStatus,
    RunStatusPlanes,
    StatusPlaneError,
)

from r9_helpers import catalog, fact, scope, snapshot
from r7_helpers import EVIDENCE, opaque as r7_opaque, relation_event


MODULE_ROOT = Path(__file__).resolve().parents[1]


class MetricTests(unittest.TestCase):
    def test_catalog_separates_direct_and_derived_metrics(self) -> None:
        rules = catalog().metric_map()
        self.assertEqual(rules["COST_POSTED_ACTUAL"].aggregation, "DIRECT")
        self.assertEqual(rules["COST_POSTED_ACTUAL"].included_lifecycle_stages, ("POSTED_ACTUAL",))
        self.assertEqual(rules["MARGIN_ACCOUNTING"].aggregation, "DERIVED")
        self.assertEqual(
            set(rules["MARGIN_ACCOUNTING"].components_by_basis),
            {"REV_RECOGNIZED_MINUS_JOB_COST_INCURRED", "REV_RECOGNIZED_MINUS_GL_RECOGNIZED_COGS"},
        )

    def test_direct_metric_preserves_source_recomputed_and_calculated_values(self) -> None:
        item = fact(
            "direct",
            metric_id="COST_POSTED_ACTUAL",
            basis_id="JOB_COST_INCURRED",
            direction="COST",
            lifecycle_stage="POSTED_ACTUAL",
            amount_minor=12001,
        )
        result = calculate_direct_metric(
            catalog=catalog(),
            metric_id="COST_POSTED_ACTUAL",
            accounting_basis_id="JOB_COST_INCURRED",
            as_of="2026-05-31",
            scope=scope(),
            facts=(item,),
            source_control=MetricSourceControl(1, 12001, 12001, 12001),
        )
        self.assertEqual(result.calculation_status, CalculationStatus.VALIDATED)
        self.assertEqual((result.source_value_minor, result.recomputed_value_minor, result.calculated_value_minor), (12001, 12001, 12001))
        self.assertEqual((result.source_recomputed_delta_minor, result.recomputed_calculated_delta_minor), (0, 0))
        self.assertEqual((result.channel_signed_delta_minor, result.channel_absolute_delta_minor), (0, 0))

    def test_source_arithmetic_difference_is_visible_and_blocks(self) -> None:
        result, _ = snapshot(
            "source-delta",
            metric_id="COST_POSTED_ACTUAL",
            basis_id="JOB_COST_INCURRED",
            direction="COST",
            lifecycle_stage="POSTED_ACTUAL",
            amount_minor=10000,
            reported_source_value_minor=10001,
        )
        self.assertEqual(result.calculation_status, CalculationStatus.BLOCKED_SOURCE)
        self.assertEqual(result.source_recomputed_delta_minor, 1)
        self.assertEqual(result.calculated_value_minor, 10000)
        self.assertIn("METRIC_SOURCE_RECOMPUTED_DELTA", result.blocker_codes)

    def test_pending_pool_blocks_without_silent_zero(self) -> None:
        included = fact(
            "included",
            metric_id="COST_PAID",
            basis_id="CASH_VERIFIED",
            direction="CASH_OUT",
            lifecycle_stage="PAID",
            amount_minor=8000,
        )
        pending = fact(
            "pending",
            metric_id="COST_PAID",
            basis_id="CASH_VERIFIED",
            direction="CASH_OUT",
            lifecycle_stage="PAID",
            amount_minor=2000,
            disposition=MetricDisposition.PENDING,
        )
        result = calculate_direct_metric(
            catalog=catalog(),
            metric_id="COST_PAID",
            accounting_basis_id="CASH_VERIFIED",
            as_of="2026-05-31",
            scope=scope(),
            facts=(included, pending),
            source_control=MetricSourceControl(2, 10000, 10000, 8000),
        )
        self.assertEqual(result.calculation_status, CalculationStatus.BLOCKED_RELATIONSHIP)
        self.assertEqual(result.calculated_value_minor, 8000)
        self.assertIn("METRIC_RELATION_PENDING_POOL", result.blocker_codes)

    def test_period_scope_and_lifecycle_are_fail_closed(self) -> None:
        cases = (
            ("late", {"metric_date": "2026-06-01"}, "METRIC_PERIOD_AFTER_CUTOFF"),
            ("scope", {"fact_scope": type(scope())("ENTITY-X", "PROJECT-X", "WBS-X")}, "METRIC_IDENTITY_SCOPE_MISMATCH"),
        )
        for seed, changes, blocker in cases:
            with self.subTest(seed=seed):
                item = fact(
                    seed,
                    metric_id="COST_POSTED_ACTUAL",
                    basis_id="JOB_COST_INCURRED",
                    direction="COST",
                    lifecycle_stage="POSTED_ACTUAL",
                    amount_minor=100,
                    **changes,
                )
                result = calculate_direct_metric(
                    catalog=catalog(),
                    metric_id="COST_POSTED_ACTUAL",
                    accounting_basis_id="JOB_COST_INCURRED",
                    as_of="2026-05-31",
                    scope=scope(),
                    facts=(item,),
                    source_control=MetricSourceControl(1, 100, 100, 100),
                )
                self.assertIn(blocker, result.blocker_codes)

    def test_derived_accounting_margin_keeps_cost_bases_separate(self) -> None:
        revenue, _ = snapshot("rev", metric_id="REV_RECOGNIZED", basis_id="GL_RECOGNIZED_REVENUE", direction="REVENUE", lifecycle_stage="RECOGNIZED_REVENUE", amount_minor=100000)
        job, _ = snapshot("job-margin", metric_id="COST_POSTED_ACTUAL", basis_id="JOB_COST_INCURRED", direction="COST", lifecycle_stage="POSTED_ACTUAL", amount_minor=40000)
        accrual, _ = snapshot("accrual", metric_id="COST_ACCRUED", basis_id="JOB_COST_INCURRED", direction="COST", lifecycle_stage="ACCRUAL", amount_minor=10000)
        gl, _ = snapshot("gl-margin", metric_id="COST_POSTED_ACTUAL", basis_id="GL_RECOGNIZED_COGS", direction="COST", lifecycle_stage="POSTED_ACTUAL", amount_minor=35000)
        job_margin = calculate_derived_metric(
            catalog=catalog(), metric_id="MARGIN_ACCOUNTING", accounting_basis_id="REV_RECOGNIZED_MINUS_JOB_COST_INCURRED",
            as_of="2026-05-31", scope=scope(), component_snapshots=(revenue, job, accrual)
        )
        gl_margin = calculate_derived_metric(
            catalog=catalog(), metric_id="MARGIN_ACCOUNTING", accounting_basis_id="REV_RECOGNIZED_MINUS_GL_RECOGNIZED_COGS",
            as_of="2026-05-31", scope=scope(), component_snapshots=(revenue, gl)
        )
        self.assertEqual(job_margin.calculated_value_minor, 50000)
        self.assertEqual(gl_margin.calculated_value_minor, 65000)
        self.assertEqual(job_margin.calculation_status, CalculationStatus.VALIDATED)
        self.assertEqual(gl_margin.calculation_status, CalculationStatus.VALIDATED)

    def test_actual_cost_request_forces_both_bases(self) -> None:
        job, _ = snapshot("job-only", metric_id="COST_POSTED_ACTUAL", basis_id="JOB_COST_INCURRED", direction="COST", lifecycle_stage="POSTED_ACTUAL", amount_minor=1)
        batch = build_metric_batch(requested_pairs=(("COST_POSTED_ACTUAL", "JOB_COST_INCURRED"),), snapshots=(job,))
        self.assertEqual(batch.calculation_status, CalculationStatus.BLOCKED_SCHEMA)
        self.assertIn(("COST_POSTED_ACTUAL", "GL_RECOGNIZED_COGS"), batch.required_pairs)

    def test_r7_event_requires_validated_identity_and_explicit_metric_decision(self) -> None:
        event = relation_event("metric-adapter", direction=EventDirection.CASH_OUT, stage=LifecycleStage.PAID, event_date="2026-05-01")
        converted = metric_fact_from_relation_event(
            catalog=catalog(),
            event=event,
            metric_id="COST_PAID",
            accounting_basis_id="CASH_VERIFIED",
            disposition=MetricDisposition.INCLUDED,
            disposition_reason="EXPLICIT_METRIC_DECISION",
            formula_profile_id="NO_FORMULA_REQUIRED",
            parameter_profile_id=None,
            company_policy_refs=("policy://sha256/" + "a" * 64,),
            input_resolution_refs=(),
            metric_inclusion_decision_ref="metric_decision_" + "b" * 32,
            metric_inclusion_evidence_refs=("evidence://sha256/" + "c" * 64,),
        )
        self.assertEqual(converted.base_amount_minor, event.base_amount_minor)
        self.assertEqual(converted.scope.canonical_project_id, "PROJECT-S")
        unresolved = relation_event("metric-unresolved", identity_status=RelationIdentityStatus.ALLOCATION_REQUIRED)
        with self.assertRaises(MetricError):
            metric_fact_from_relation_event(
                catalog=catalog(), event=unresolved, metric_id="COST_POSTED_ACTUAL", accounting_basis_id="JOB_COST_INCURRED",
                disposition=MetricDisposition.INCLUDED, disposition_reason="EXPLICIT_METRIC_DECISION", formula_profile_id="NO_FORMULA_REQUIRED",
                parameter_profile_id=None, company_policy_refs=(), input_resolution_refs=(),
                metric_inclusion_decision_ref="metric_decision_" + "b" * 32,
                metric_inclusion_evidence_refs=("evidence://sha256/" + "c" * 64,),
            )

    def test_r5_basis_view_requires_exact_component_lineage(self) -> None:
        dimension = BasisDimension("ENTITY-S", "PROJECT-S", "WBS-S", "CONTRACT-S", "BRIDGE-S", "2026-05-01", "2026-05-31")
        view = BasisView(BasisId.JOB_COST_INCURRED, 1234, (BasisComponent(dimension, 1234),))
        lineage = AccountingMetricLineage("BRIDGE-S", (r7_opaque("rec_source_", "basis"),), r7_opaque("identity_resolution_", "basis"), (EVIDENCE,))
        converted = metric_facts_from_basis_view(
            view=view, as_of="2026-05-31", lineage=(lineage,), formula_profile_id="R5_BASIS_POLICY",
            parameter_profile_id=None, company_policy_refs=("policy://sha256/" + "a" * 64,), input_resolution_refs=(),
            metric_inclusion_decision_ref="metric_decision_" + "b" * 32,
            metric_inclusion_evidence_refs=("evidence://sha256/" + "c" * 64,),
        )
        self.assertEqual(len(converted), 1)
        self.assertEqual(metric_control_from_basis_view(view).signed_amount_minor, 1234)
        with self.assertRaises(MetricError):
            metric_facts_from_basis_view(
                view=view, as_of="2026-05-31", lineage=(), formula_profile_id="R5_BASIS_POLICY",
                parameter_profile_id=None, company_policy_refs=(), input_resolution_refs=(),
                metric_inclusion_decision_ref="metric_decision_" + "b" * 32,
                metric_inclusion_evidence_refs=("evidence://sha256/" + "c" * 64,),
            )

    def test_metric_batch_is_order_invariant(self) -> None:
        job, _ = snapshot("job-order", metric_id="COST_POSTED_ACTUAL", basis_id="JOB_COST_INCURRED", direction="COST", lifecycle_stage="POSTED_ACTUAL", amount_minor=1)
        gl, _ = snapshot("gl-order", metric_id="COST_POSTED_ACTUAL", basis_id="GL_RECOGNIZED_COGS", direction="COST", lifecycle_stage="POSTED_ACTUAL", amount_minor=2)
        requested = (("COST_POSTED_ACTUAL", "JOB_COST_INCURRED"), ("COST_POSTED_ACTUAL", "GL_RECOGNIZED_COGS"))
        self.assertEqual(build_metric_batch(requested_pairs=requested, snapshots=(job, gl)).as_dict(), build_metric_batch(requested_pairs=tuple(reversed(requested)), snapshots=(gl, job)).as_dict())

    def test_four_status_planes_cannot_collapse(self) -> None:
        valid = RunStatusPlanes(ExecutionStatus.SUCCEEDED, InputReadinessStatus.SUFFICIENT, CalculationStatus.VALIDATED, GenerationStatus.FINAL_GENERATED)
        valid.validate()
        invalid = RunStatusPlanes(ExecutionStatus.SUCCEEDED, InputReadinessStatus.NEEDS_SUPPLEMENT, CalculationStatus.VALIDATED, GenerationStatus.FINAL_GENERATED)
        with self.assertRaises(StatusPlaneError):
            invalid.validate()

    def test_empty_metric_request_is_rejected(self) -> None:
        with self.assertRaises(MetricError):
            build_metric_batch(requested_pairs=(), snapshots=())

    def test_metric_fact_and_snapshot_instances_match_public_schemas(self) -> None:
        item = fact(
            "schema",
            metric_id="COST_POSTED_ACTUAL",
            basis_id="JOB_COST_INCURRED",
            direction="COST",
            lifecycle_stage="POSTED_ACTUAL",
            amount_minor=123,
        )
        result = calculate_direct_metric(
            catalog=catalog(), metric_id="COST_POSTED_ACTUAL", accounting_basis_id="JOB_COST_INCURRED",
            as_of="2026-05-31", scope=scope(), facts=(item,), source_control=MetricSourceControl(1, 123, 123, 123)
        )
        for payload, schema_name in ((item.as_dict(), "metric_fact.schema.json"), (result.as_dict(), "metric_snapshot.schema.json")):
            schema = json.loads((MODULE_ROOT / "schemas" / schema_name).read_text(encoding="utf-8"))
            self.assertEqual(list(Draft202012Validator(schema, format_checker=FormatChecker()).iter_errors(payload)), [])


if __name__ == "__main__":
    unittest.main()
