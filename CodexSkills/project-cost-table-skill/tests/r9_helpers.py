from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional, Sequence, Tuple

from project_cost_table.generation import SourceLineage
from project_cost_table.input_gate import InputSufficiencyReport, MetricCatalog, RequirementItem
from project_cost_table.metrics import (
    MetricBatchResult,
    MetricDisposition,
    MetricFact,
    MetricScope,
    MetricSourceControl,
    MetricSnapshot,
    build_metric_batch,
    calculate_direct_metric,
)


MODULE_ROOT = Path(__file__).resolve().parents[1]
REQUEST_HASH = "1" * 64
CONFIG_HASH = "2" * 64


def digest(seed: str) -> str:
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()


def opaque(prefix: str, seed: str) -> str:
    return prefix + "_" + digest(seed)[:32]


def catalog() -> MetricCatalog:
    return MetricCatalog.from_yaml(MODULE_ROOT / "config" / "metric_catalog.yml")


def scope() -> MetricScope:
    return MetricScope("ENTITY-S", "PROJECT-S", "WBS-S")


def fact(
    seed: str,
    *,
    metric_id: str,
    basis_id: str,
    direction: str,
    lifecycle_stage: str,
    amount_minor: int,
    disposition: MetricDisposition = MetricDisposition.INCLUDED,
    metric_date: str = "2026-05-31",
    fact_scope: Optional[MetricScope] = None,
) -> MetricFact:
    return MetricFact(
        fact_id=opaque("fact", seed),
        metric_id=metric_id,
        accounting_basis_id=basis_id,
        direction=direction,
        lifecycle_stage=lifecycle_stage,
        metric_date=metric_date,
        scope=fact_scope or scope(),
        base_amount_minor=amount_minor,
        disposition=disposition,
        disposition_reason="IN_SCOPE_VALIDATED" if disposition == MetricDisposition.INCLUDED else "EXPLICIT_TEST_POOL",
        source_record_refs=(opaque("source_record", seed),),
        mapping_resolution_ref=opaque("mapping_resolution", seed),
        formula_profile_id=opaque("formula_profile", seed),
        parameter_profile_id=opaque("parameter_profile", seed),
        company_policy_refs=("policy://sha256/" + digest("policy:" + seed),),
        input_resolution_refs=(),
        metric_inclusion_decision_ref=opaque("metric_decision", seed),
        metric_inclusion_evidence_refs=("evidence://sha256/" + digest("metric-evidence:" + seed),),
    )


def snapshot(
    seed: str,
    *,
    metric_id: str,
    basis_id: str,
    direction: str,
    lifecycle_stage: str,
    amount_minor: int,
    disposition: MetricDisposition = MetricDisposition.INCLUDED,
    reported_source_value_minor: Optional[int] = None,
) -> Tuple[MetricSnapshot, MetricFact]:
    item = fact(
        seed,
        metric_id=metric_id,
        basis_id=basis_id,
        direction=direction,
        lifecycle_stage=lifecycle_stage,
        amount_minor=amount_minor,
        disposition=disposition,
    )
    value = amount_minor if reported_source_value_minor is None else reported_source_value_minor
    control = MetricSourceControl(1, amount_minor, abs(amount_minor), value)
    result = calculate_direct_metric(
        catalog=catalog(),
        metric_id=metric_id,
        accounting_basis_id=basis_id,
        as_of="2026-05-31",
        scope=scope(),
        facts=(item,),
        source_control=control,
    )
    return result, item


def cost_actual_batch() -> Tuple[MetricBatchResult, Tuple[MetricFact, ...]]:
    job, job_fact = snapshot(
        "job",
        metric_id="COST_POSTED_ACTUAL",
        basis_id="JOB_COST_INCURRED",
        direction="COST",
        lifecycle_stage="POSTED_ACTUAL",
        amount_minor=12345,
    )
    gl, gl_fact = snapshot(
        "gl",
        metric_id="COST_POSTED_ACTUAL",
        basis_id="GL_RECOGNIZED_COGS",
        direction="COST",
        lifecycle_stage="POSTED_ACTUAL",
        amount_minor=10000,
    )
    return (
        build_metric_batch(
            requested_pairs=(
                ("COST_POSTED_ACTUAL", "JOB_COST_INCURRED"),
                ("COST_POSTED_ACTUAL", "GL_RECOGNIZED_COGS"),
            ),
            snapshots=(job, gl),
        ),
        (job_fact, gl_fact),
    )


def sufficient_report(output_dir: Path, *, run_id: str = "r9-synthetic") -> InputSufficiencyReport:
    return InputSufficiencyReport(
        run_id=run_id,
        request_hash=REQUEST_HASH,
        mode="calculate",
        requested_metrics=("COST_POSTED_ACTUAL",),
        requested_basis_ids=("GL_RECOGNIZED_COGS", "JOB_COST_INCURRED"),
        output_dir=str(output_dir),
        overall_status="SUFFICIENT",
        items=(),
        user_action_required=False,
        resolution_ref=None,
    )


def blocked_report(output_dir: Path, *, run_id: str = "r9-blocked") -> InputSufficiencyReport:
    item = RequirementItem(
        requirement_id="RAW_ROOT_AND_MANIFEST",
        classification="NON_WAIVABLE",
        observed_status="MISSING",
        allowed_resolutions=("SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"),
        applies_to_metrics=("COST_POSTED_ACTUAL",),
        expected_source_or_policy="read-only raw root plus explicit manifest",
        evidence_ref=None,
    )
    return InputSufficiencyReport(
        run_id=run_id,
        request_hash=REQUEST_HASH,
        mode="calculate",
        requested_metrics=("COST_POSTED_ACTUAL",),
        requested_basis_ids=("GL_RECOGNIZED_COGS", "JOB_COST_INCURRED"),
        output_dir=str(output_dir),
        overall_status="NEEDS_SUPPLEMENT",
        items=(item,),
        user_action_required=True,
        resolution_ref=None,
    )


def lineage() -> Tuple[SourceLineage, ...]:
    return (
        SourceLineage(
            source_slot_id="general_ledger",
            opaque_source_id="source-synthetic",
            source_sha256=digest("source"),
            reader_version="2.0.0",
            schema_fingerprint=digest("schema"),
            logical_source_period="2026-05",
        ),
    )
