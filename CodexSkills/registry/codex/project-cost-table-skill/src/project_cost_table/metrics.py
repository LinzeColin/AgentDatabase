"""R9 named, basis-specific Metrics with independent aggregation channels."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence, Tuple

from .accounting_basis import BasisView
from .events import RelationEvent, RelationIdentityStatus
from .input_gate import MetricCatalog, MetricComponentRule, MetricRule
from .statuses import CalculationStatus


MAX_MINOR = 9_000_000_000_000_000
OPAQUE_REF_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}_[0-9a-f]{32}$")
REASON_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
VALID_DIRECTIONS = frozenset({"COST", "REVENUE", "CASH_OUT", "CASH_IN", "REFERENCE"})
VALID_LIFECYCLE_STAGES = frozenset(
    {"BUDGET", "COMMITMENT", "ACCRUAL", "POSTED_ACTUAL", "PAID", "FORECAST", "CONTRACT_VALUE", "BILLED", "RECOGNIZED_REVENUE", "COLLECTED", "REFERENCE_DISPLAY"}
)


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class MetricError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class MetricDisposition(str, Enum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    PENDING = "PENDING"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass(frozen=True)
class MetricScope:
    legal_entity_id: str
    canonical_project_id: str
    wbs_or_cost_code: str

    def validate(self) -> None:
        for field in ("legal_entity_id", "canonical_project_id", "wbs_or_cost_code"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value or any(char in value for char in "\r\n\x00"):
                raise MetricError("METRIC_SCOPE_INVALID", "%s must be nonempty single-line text" % field)

    @property
    def fingerprint(self) -> str:
        self.validate()
        return _digest(self.as_dict())

    def as_dict(self) -> Dict[str, str]:
        self.validate()
        return {
            "legal_entity_id": self.legal_entity_id,
            "canonical_project_id": self.canonical_project_id,
            "wbs_or_cost_code": self.wbs_or_cost_code,
        }


@dataclass(frozen=True)
class MetricFact:
    fact_id: str
    metric_id: str
    accounting_basis_id: str
    direction: str
    lifecycle_stage: str
    metric_date: str
    scope: MetricScope
    base_amount_minor: int
    disposition: MetricDisposition
    disposition_reason: str
    source_record_refs: Tuple[str, ...]
    mapping_resolution_ref: str
    formula_profile_id: str
    parameter_profile_id: Optional[str] = None
    company_policy_refs: Tuple[str, ...] = ()
    input_resolution_refs: Tuple[str, ...] = ()
    metric_inclusion_decision_ref: str = ""
    metric_inclusion_evidence_refs: Tuple[str, ...] = ()
    upstream_validation_status: str = "VALIDATED"

    def validate(self) -> None:
        if not OPAQUE_REF_RE.fullmatch(self.fact_id):
            raise MetricError("METRIC_FACT_ID_INVALID", "fact ID must be an opaque content reference")
        for field in ("metric_id", "accounting_basis_id", "direction", "lifecycle_stage"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise MetricError("METRIC_FACT_FIELD_INVALID", "%s is required" % field)
        if self.direction not in VALID_DIRECTIONS or self.lifecycle_stage not in VALID_LIFECYCLE_STAGES:
            raise MetricError("METRIC_FACT_LIFECYCLE_INVALID", "fact direction or lifecycle stage is not registered")
        try:
            date.fromisoformat(self.metric_date)
        except (TypeError, ValueError) as exc:
            raise MetricError("METRIC_DATE_INVALID", "Metric date must be canonical ISO") from exc
        self.scope.validate()
        if isinstance(self.base_amount_minor, bool) or not isinstance(self.base_amount_minor, int):
            raise MetricError("METRIC_AMOUNT_INVALID", "Metric amount must use integer minor units")
        if abs(self.base_amount_minor) > MAX_MINOR:
            raise MetricError("METRIC_AMOUNT_RANGE", "Metric amount exceeds the registered minor-unit range")
        if not isinstance(self.disposition, MetricDisposition) or not REASON_RE.fullmatch(self.disposition_reason):
            raise MetricError("METRIC_DISPOSITION_INVALID", "Metric disposition and reason are required")
        if (
            not isinstance(self.source_record_refs, tuple)
            or not self.source_record_refs
            or tuple(sorted(set(self.source_record_refs))) != self.source_record_refs
            or any(not isinstance(item, str) or not item for item in self.source_record_refs)
        ):
            raise MetricError("METRIC_SOURCE_REFS_INVALID", "Metric source refs must be sorted and unique")
        for field in ("mapping_resolution_ref", "formula_profile_id", "metric_inclusion_decision_ref"):
            value = getattr(self, field)
            if not isinstance(value, str) or not value:
                raise MetricError("METRIC_LINEAGE_INVALID", "%s is required" % field)
        if self.parameter_profile_id is not None and (not isinstance(self.parameter_profile_id, str) or not self.parameter_profile_id):
            raise MetricError("METRIC_LINEAGE_INVALID", "parameter profile must be nonempty text or null")
        if not OPAQUE_REF_RE.fullmatch(self.metric_inclusion_decision_ref):
            raise MetricError("METRIC_DECISION_REF_INVALID", "Metric inclusion decision must be content-addressed")
        for values in (self.company_policy_refs, self.input_resolution_refs, self.metric_inclusion_evidence_refs):
            if tuple(sorted(set(values))) != values or any(not isinstance(item, str) or not item for item in values):
                raise MetricError("METRIC_LINEAGE_INVALID", "lineage refs must be sorted and unique")
        if not self.metric_inclusion_evidence_refs:
            raise MetricError("METRIC_DECISION_EVIDENCE_MISSING", "Metric inclusion requires evidence")
        if self.upstream_validation_status != "VALIDATED":
            raise MetricError("METRIC_UPSTREAM_NOT_VALIDATED", "only upstream-validated facts may enter R9")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.metric_fact.v1",
            "fact_id": self.fact_id,
            "metric_id": self.metric_id,
            "accounting_basis_id": self.accounting_basis_id,
            "direction": self.direction,
            "lifecycle_stage": self.lifecycle_stage,
            "metric_date": self.metric_date,
            "scope": self.scope.as_dict(),
            "base_currency": "CNY",
            "base_amount_minor": self.base_amount_minor,
            "disposition": self.disposition.value,
            "disposition_reason": self.disposition_reason,
            "source_record_refs": list(self.source_record_refs),
            "mapping_resolution_ref": self.mapping_resolution_ref,
            "formula_profile_id": self.formula_profile_id,
            "parameter_profile_id": self.parameter_profile_id,
            "company_policy_refs": list(self.company_policy_refs),
            "input_resolution_refs": list(self.input_resolution_refs),
            "metric_inclusion_decision_ref": self.metric_inclusion_decision_ref,
            "metric_inclusion_evidence_refs": list(self.metric_inclusion_evidence_refs),
            "upstream_validation_status": self.upstream_validation_status,
        }


@dataclass(frozen=True)
class MetricSourceControl:
    item_count: int
    signed_amount_minor: int
    absolute_amount_minor: int
    reported_source_value_minor: Optional[int] = None

    def validate(self) -> None:
        if isinstance(self.item_count, bool) or not isinstance(self.item_count, int) or self.item_count < 0:
            raise MetricError("METRIC_CONTROL_COUNT_INVALID", "source control count must be a nonnegative integer")
        for field in ("signed_amount_minor", "absolute_amount_minor", "reported_source_value_minor"):
            value = getattr(self, field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_MINOR):
                raise MetricError("METRIC_CONTROL_AMOUNT_INVALID", "%s must use integer minor units" % field)
        if self.absolute_amount_minor < 0:
            raise MetricError("METRIC_CONTROL_ABSOLUTE_INVALID", "absolute source control cannot be negative")
        if self.absolute_amount_minor < abs(self.signed_amount_minor):
            raise MetricError("METRIC_CONTROL_ABSOLUTE_INVALID", "absolute source control cannot be below the signed magnitude")


@dataclass(frozen=True)
class MetricSnapshot:
    metric_id: str
    accounting_basis_id: str
    as_of: str
    as_of_date_rule: str
    included_lifecycle_stages: Tuple[str, ...]
    scope: MetricScope
    calculation_status: CalculationStatus
    source_value_minor: Optional[int]
    recomputed_value_minor: Optional[int]
    calculated_value_minor: Optional[int]
    source_recomputed_delta_minor: Optional[int]
    recomputed_calculated_delta_minor: Optional[int]
    channel_signed_delta_minor: Optional[int]
    channel_absolute_delta_minor: Optional[int]
    source_control_amount_minor: Optional[int]
    source_control_absolute_minor: Optional[int]
    source_record_count: int
    facts_hash: str
    formula_profile_ids: Tuple[str, ...]
    parameter_profile_ids: Tuple[str, ...]
    company_policy_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    blocker_codes: Tuple[str, ...]

    @property
    def key(self) -> Tuple[str, str]:
        return (self.metric_id, self.accounting_basis_id)

    def validate(self) -> None:
        if not self.metric_id or not self.accounting_basis_id or not self.as_of_date_rule:
            raise MetricError("METRIC_SNAPSHOT_FIELD_INVALID", "Metric snapshot identifiers are required")
        try:
            date.fromisoformat(self.as_of)
        except (TypeError, ValueError) as exc:
            raise MetricError("METRIC_SNAPSHOT_DATE_INVALID", "snapshot as-of must be canonical ISO") from exc
        self.scope.validate()
        if not isinstance(self.calculation_status, CalculationStatus):
            raise MetricError("METRIC_SNAPSHOT_STATUS_INVALID", "calculation status is not registered")
        if tuple(sorted(set(self.included_lifecycle_stages))) != self.included_lifecycle_stages:
            raise MetricError("METRIC_SNAPSHOT_STAGES_INVALID", "included lifecycle stages must be sorted and unique")
        for field in (
            "source_value_minor",
            "recomputed_value_minor",
            "calculated_value_minor",
            "source_recomputed_delta_minor",
            "recomputed_calculated_delta_minor",
            "channel_signed_delta_minor",
            "channel_absolute_delta_minor",
            "source_control_amount_minor",
            "source_control_absolute_minor",
        ):
            value = getattr(self, field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int)):
                raise MetricError("METRIC_SNAPSHOT_AMOUNT_INVALID", "%s must use integer minor units" % field)
        if not re.fullmatch(r"[0-9a-f]{64}", self.facts_hash):
            raise MetricError("METRIC_SNAPSHOT_HASH_INVALID", "facts hash must be SHA256")
        if isinstance(self.source_record_count, bool) or not isinstance(self.source_record_count, int) or self.source_record_count < 0:
            raise MetricError("METRIC_SNAPSHOT_COUNT_INVALID", "source record count must be nonnegative")
        for values in (
            self.formula_profile_ids,
            self.parameter_profile_ids,
            self.company_policy_refs,
            self.input_resolution_refs,
        ):
            if tuple(sorted(set(values))) != values or any(not isinstance(item, str) or not item for item in values):
                raise MetricError("METRIC_SNAPSHOT_LINEAGE_INVALID", "snapshot lineage refs must be sorted and unique")
        if tuple(sorted(set(self.blocker_codes))) != self.blocker_codes:
            raise MetricError("METRIC_BLOCKERS_INVALID", "blocker codes must be sorted and unique")
        if self.calculation_status == CalculationStatus.VALIDATED:
            if self.blocker_codes:
                raise MetricError("VALIDATED_METRIC_HAS_BLOCKERS", "validated Metric cannot retain blockers")
            if self.calculated_value_minor is None or self.recomputed_value_minor is None:
                raise MetricError("VALIDATED_METRIC_VALUE_MISSING", "validated Metric requires both calculation channels")
            if self.channel_signed_delta_minor != 0 or self.channel_absolute_delta_minor != 0:
                raise MetricError("VALIDATED_METRIC_CHANNEL_DELTA", "validated Metric channels must agree exactly")
            if self.source_recomputed_delta_minor not in {None, 0} or self.recomputed_calculated_delta_minor != 0:
                raise MetricError("VALIDATED_METRIC_SOURCE_DELTA", "validated Metric cannot retain a source or calculation delta")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.metric_snapshot.v2",
            "metric_id": self.metric_id,
            "accounting_basis_id": self.accounting_basis_id,
            "as_of": self.as_of,
            "as_of_date_rule": self.as_of_date_rule,
            "included_lifecycle_stages": list(self.included_lifecycle_stages),
            "scope": self.scope.as_dict(),
            "scope_fingerprint": self.scope.fingerprint,
            "calculation_status": self.calculation_status.value,
            "currency": "CNY",
            "source_value_minor": self.source_value_minor,
            "recomputed_value_minor": self.recomputed_value_minor,
            "calculated_value_minor": self.calculated_value_minor,
            "source_recomputed_delta_minor": self.source_recomputed_delta_minor,
            "recomputed_calculated_delta_minor": self.recomputed_calculated_delta_minor,
            "channel_signed_delta_minor": self.channel_signed_delta_minor,
            "channel_absolute_delta_minor": self.channel_absolute_delta_minor,
            "source_control_amount_minor": self.source_control_amount_minor,
            "source_control_absolute_minor": self.source_control_absolute_minor,
            "source_record_count": self.source_record_count,
            "facts_hash": self.facts_hash,
            "formula_profile_ids": list(self.formula_profile_ids),
            "parameter_profile_ids": list(self.parameter_profile_ids),
            "company_policy_refs": list(self.company_policy_refs),
            "input_resolution_refs": list(self.input_resolution_refs),
            "blocker_codes": list(self.blocker_codes),
        }


def _catalog_rule(catalog: MetricCatalog, metric_id: str) -> MetricRule:
    rule = catalog.metric_map().get(metric_id)
    if rule is None:
        raise MetricError("METRIC_UNKNOWN", "Metric is not registered: %s" % metric_id)
    return rule


@dataclass(frozen=True)
class AccountingMetricLineage:
    bridge_group_id: str
    source_record_refs: Tuple[str, ...]
    mapping_resolution_ref: str
    evidence_refs: Tuple[str, ...]

    def validate(self) -> None:
        if not self.bridge_group_id or not self.mapping_resolution_ref:
            raise MetricError("ACCOUNTING_METRIC_LINEAGE_INVALID", "bridge and mapping refs are required")
        for values in (self.source_record_refs, self.evidence_refs):
            if not values or tuple(sorted(set(values))) != values or any(not isinstance(item, str) or not item for item in values):
                raise MetricError("ACCOUNTING_METRIC_LINEAGE_INVALID", "source and evidence refs must be nonempty, sorted, and unique")


def metric_fact_from_relation_event(
    *,
    catalog: MetricCatalog,
    event: RelationEvent,
    metric_id: str,
    accounting_basis_id: str,
    disposition: MetricDisposition,
    disposition_reason: str,
    formula_profile_id: str,
    parameter_profile_id: Optional[str],
    company_policy_refs: Tuple[str, ...],
    input_resolution_refs: Tuple[str, ...],
    metric_inclusion_decision_ref: str,
    metric_inclusion_evidence_refs: Tuple[str, ...],
) -> MetricFact:
    """Promote an R7 relation event only through an explicit R9 inclusion decision."""

    event.validate()
    rule = _catalog_rule(catalog, metric_id)
    if rule.aggregation != "DIRECT" or accounting_basis_id not in rule.allowed_basis_ids:
        raise MetricError("METRIC_EVENT_RULE_INVALID", "event Metric/basis is not registered as direct")
    binding = event.identity_binding
    if binding.identity_status != RelationIdentityStatus.VALIDATED_IDENTITY:
        raise MetricError("METRIC_IDENTITY_UNRESOLVED", "R7 event identity must validate before R9 inclusion")
    if binding.canonical_project_id is None or binding.wbs_or_cost_code is None or binding.mapping_resolution_ref is None:
        raise MetricError("METRIC_IDENTITY_INCOMPLETE", "R7 event lacks the complete canonical scope")
    if disposition == MetricDisposition.INCLUDED and (
        event.direction.value != rule.direction or event.lifecycle_stage.value not in rule.included_lifecycle_stages
    ):
        raise MetricError("METRIC_EVENT_LIFECYCLE_MISMATCH", "included event conflicts with the Metric lifecycle rule")
    decision_payload = {
        "relation_event_ref": event.relation_event_ref,
        "metric_id": metric_id,
        "accounting_basis_id": accounting_basis_id,
        "disposition": disposition.value,
        "metric_inclusion_decision_ref": metric_inclusion_decision_ref,
    }
    return MetricFact(
        fact_id="fact_" + _digest(decision_payload)[:32],
        metric_id=metric_id,
        accounting_basis_id=accounting_basis_id,
        direction=event.direction.value,
        lifecycle_stage=event.lifecycle_stage.value,
        metric_date=event.event_date,
        scope=MetricScope(binding.legal_entity_id, binding.canonical_project_id, binding.wbs_or_cost_code),
        base_amount_minor=event.base_amount_minor,
        disposition=disposition,
        disposition_reason=disposition_reason,
        source_record_refs=event.source_record_refs,
        mapping_resolution_ref=binding.mapping_resolution_ref,
        formula_profile_id=formula_profile_id,
        parameter_profile_id=parameter_profile_id,
        company_policy_refs=company_policy_refs,
        input_resolution_refs=input_resolution_refs,
        metric_inclusion_decision_ref=metric_inclusion_decision_ref,
        metric_inclusion_evidence_refs=metric_inclusion_evidence_refs,
    )


def metric_facts_from_basis_view(
    *,
    view: BasisView,
    as_of: str,
    lineage: Sequence[AccountingMetricLineage],
    formula_profile_id: str,
    parameter_profile_id: Optional[str],
    company_policy_refs: Tuple[str, ...],
    input_resolution_refs: Tuple[str, ...],
    metric_inclusion_decision_ref: str,
    metric_inclusion_evidence_refs: Tuple[str, ...],
) -> Tuple[MetricFact, ...]:
    """Adapt an R5 basis view without inventing component source or identity lineage."""

    try:
        date.fromisoformat(as_of)
    except (TypeError, ValueError) as exc:
        raise MetricError("METRIC_AS_OF_INVALID", "as-of must be canonical ISO") from exc
    lineage_map = {}
    for item in lineage:
        item.validate()
        if item.bridge_group_id in lineage_map:
            raise MetricError("ACCOUNTING_METRIC_LINEAGE_DUPLICATE", "bridge lineage must be unique")
        lineage_map[item.bridge_group_id] = item
    component_ids = {item.dimension.bridge_group_id for item in view.components}
    if set(lineage_map) != component_ids:
        raise MetricError("ACCOUNTING_METRIC_LINEAGE_INCOMPLETE", "every and only basis component requires exact lineage")
    if sum(item.amount_minor for item in view.components) != view.amount_minor:
        raise MetricError("ACCOUNTING_METRIC_VIEW_CONTROL", "basis components do not equal the basis view amount")
    facts = []
    for component in sorted(view.components, key=lambda item: item.dimension.bridge_group_id):
        item_lineage = lineage_map[component.dimension.bridge_group_id]
        dimension = component.dimension
        fact_id = "fact_" + _digest(
            {
                "basis_id": view.basis_id.value,
                "dimension": dimension.__dict__,
                "amount_minor": component.amount_minor,
                "metric_inclusion_decision_ref": metric_inclusion_decision_ref,
                "source_record_refs": item_lineage.source_record_refs,
            }
        )[:32]
        facts.append(
            MetricFact(
                fact_id=fact_id,
                metric_id="COST_POSTED_ACTUAL",
                accounting_basis_id=view.basis_id.value,
                direction="COST",
                lifecycle_stage="POSTED_ACTUAL",
                metric_date=as_of,
                scope=MetricScope(dimension.legal_entity_id, dimension.canonical_project_id, dimension.wbs_or_cost_code),
                base_amount_minor=component.amount_minor,
                disposition=MetricDisposition.INCLUDED,
                disposition_reason="R5_BASIS_VIEW_VALIDATED",
                source_record_refs=item_lineage.source_record_refs,
                mapping_resolution_ref=item_lineage.mapping_resolution_ref,
                formula_profile_id=formula_profile_id,
                parameter_profile_id=parameter_profile_id,
                company_policy_refs=company_policy_refs,
                input_resolution_refs=input_resolution_refs,
                metric_inclusion_decision_ref=metric_inclusion_decision_ref,
                metric_inclusion_evidence_refs=tuple(sorted(set(metric_inclusion_evidence_refs + item_lineage.evidence_refs))),
            )
        )
    return tuple(facts)


def metric_control_from_basis_view(view: BasisView, *, reported_source_value_minor: Optional[int] = None) -> MetricSourceControl:
    if sum(item.amount_minor for item in view.components) != view.amount_minor:
        raise MetricError("ACCOUNTING_METRIC_VIEW_CONTROL", "basis components do not equal the basis view amount")
    return MetricSourceControl(
        item_count=len(view.components),
        signed_amount_minor=view.amount_minor,
        absolute_amount_minor=sum(abs(item.amount_minor) for item in view.components),
        reported_source_value_minor=reported_source_value_minor,
    )


def _status_for_blockers(blockers: Iterable[str]) -> CalculationStatus:
    values = set(blockers)
    priorities = (
        ("SECURITY", CalculationStatus.BLOCKED_SECURITY),
        ("IDENTITY", CalculationStatus.BLOCKED_IDENTITY),
        ("PERIOD", CalculationStatus.BLOCKED_PERIOD),
        ("FORMULA", CalculationStatus.BLOCKED_FORMULA),
        ("RELATION", CalculationStatus.BLOCKED_RELATIONSHIP),
        ("SOURCE", CalculationStatus.BLOCKED_SOURCE),
        ("SCHEMA", CalculationStatus.BLOCKED_SCHEMA),
        ("RECONCILIATION", CalculationStatus.BLOCKED_RECONCILIATION),
    )
    for token, status in priorities:
        if any(token in item for item in values):
            return status
    return CalculationStatus.BLOCKED_RECONCILIATION if values else CalculationStatus.VALIDATED


def _refs(facts: Sequence[MetricFact], field: str) -> Tuple[str, ...]:
    values = set()
    for fact in facts:
        value = getattr(fact, field)
        if value is None:
            continue
        if isinstance(value, tuple):
            values.update(value)
        else:
            values.add(value)
    return tuple(sorted(values))


def metric_facts_hash(facts: Sequence[MetricFact]) -> str:
    ordered = tuple(sorted(facts, key=lambda item: item.fact_id))
    if len({item.fact_id for item in ordered}) != len(ordered):
        raise MetricError("METRIC_FACT_DUPLICATE", "duplicate fact IDs are forbidden")
    return _digest([item.as_dict() for item in ordered])


def calculate_direct_metric(
    *,
    catalog: MetricCatalog,
    metric_id: str,
    accounting_basis_id: str,
    as_of: str,
    scope: MetricScope,
    facts: Sequence[MetricFact],
    source_control: MetricSourceControl,
) -> MetricSnapshot:
    """Calculate one direct Metric through two independent arithmetic paths."""

    rule = _catalog_rule(catalog, metric_id)
    if rule.aggregation != "DIRECT" or accounting_basis_id not in rule.allowed_basis_ids:
        raise MetricError("METRIC_BASIS_INVALID", "direct Metric/basis is not registered")
    try:
        cutoff = date.fromisoformat(as_of)
    except (TypeError, ValueError) as exc:
        raise MetricError("METRIC_AS_OF_INVALID", "as-of must be canonical ISO") from exc
    scope.validate()
    source_control.validate()
    ordered = tuple(sorted(facts, key=lambda item: item.fact_id))
    if len({item.fact_id for item in ordered}) != len(ordered):
        raise MetricError("METRIC_FACT_DUPLICATE", "duplicate fact IDs are forbidden")
    for fact in ordered:
        fact.validate()
        if fact.metric_id != metric_id or fact.accounting_basis_id != accounting_basis_id:
            raise MetricError("METRIC_FACT_SCOPE_INVALID", "fact belongs to another Metric or basis")

    blockers = set()
    for fact in ordered:
        if fact.disposition == MetricDisposition.INCLUDED:
            if fact.scope != scope:
                blockers.add("METRIC_IDENTITY_SCOPE_MISMATCH")
            if date.fromisoformat(fact.metric_date) > cutoff:
                blockers.add("METRIC_PERIOD_AFTER_CUTOFF")
            if fact.lifecycle_stage not in rule.included_lifecycle_stages or fact.direction != rule.direction:
                blockers.add("METRIC_SCHEMA_LIFECYCLE_MISMATCH")
        elif fact.disposition == MetricDisposition.PENDING:
            blockers.add("METRIC_RELATION_PENDING_POOL")
        elif fact.disposition == MetricDisposition.PARSE_ERROR:
            blockers.add("METRIC_SOURCE_PARSE_ERROR_POOL")

    all_signed = sum(item.base_amount_minor for item in ordered)
    all_absolute = sum(abs(item.base_amount_minor) for item in ordered)
    if source_control.item_count != len(ordered):
        blockers.add("METRIC_SOURCE_COUNT_CONSERVATION")
    if source_control.signed_amount_minor != all_signed:
        blockers.add("METRIC_SOURCE_SIGNED_CONSERVATION")
    if source_control.absolute_amount_minor != all_absolute:
        blockers.add("METRIC_SOURCE_ABSOLUTE_CONSERVATION")

    included = tuple(item for item in ordered if item.disposition == MetricDisposition.INCLUDED)
    other = tuple(item for item in ordered if item.disposition != MetricDisposition.INCLUDED)

    # Channel A: direct iteration of included facts only.
    channel_a_signed = sum(item.base_amount_minor for item in included)
    channel_a_absolute = sum(abs(item.base_amount_minor) for item in included)

    # Channel B: independently starts at the immutable source controls and subtracts every non-included pool.
    channel_b_signed = source_control.signed_amount_minor - sum(item.base_amount_minor for item in other)
    channel_b_absolute = source_control.absolute_amount_minor - sum(abs(item.base_amount_minor) for item in other)
    signed_delta = channel_a_signed - channel_b_signed
    absolute_delta = channel_a_absolute - channel_b_absolute
    if signed_delta or absolute_delta:
        blockers.add("METRIC_RECONCILIATION_CHANNEL_DELTA")

    source_delta = None
    if source_control.reported_source_value_minor is not None:
        source_delta = source_control.reported_source_value_minor - channel_b_signed
        if source_delta:
            blockers.add("METRIC_SOURCE_RECOMPUTED_DELTA")
    calculation_delta = channel_b_signed - channel_a_signed
    status = _status_for_blockers(blockers)
    return MetricSnapshot(
        metric_id=metric_id,
        accounting_basis_id=accounting_basis_id,
        as_of=as_of,
        as_of_date_rule=rule.as_of_date_rule,
        included_lifecycle_stages=rule.included_lifecycle_stages,
        scope=scope,
        calculation_status=status,
        source_value_minor=source_control.reported_source_value_minor,
        recomputed_value_minor=channel_b_signed,
        calculated_value_minor=channel_a_signed,
        source_recomputed_delta_minor=source_delta,
        recomputed_calculated_delta_minor=calculation_delta,
        channel_signed_delta_minor=signed_delta,
        channel_absolute_delta_minor=absolute_delta,
        source_control_amount_minor=source_control.signed_amount_minor,
        source_control_absolute_minor=source_control.absolute_amount_minor,
        source_record_count=len(ordered),
        facts_hash=metric_facts_hash(ordered),
        formula_profile_ids=_refs(ordered, "formula_profile_id"),
        parameter_profile_ids=_refs(ordered, "parameter_profile_id"),
        company_policy_refs=_refs(ordered, "company_policy_refs"),
        input_resolution_refs=_refs(ordered, "input_resolution_refs"),
        blocker_codes=tuple(sorted(blockers)),
    )


def calculate_derived_metric(
    *,
    catalog: MetricCatalog,
    metric_id: str,
    accounting_basis_id: str,
    as_of: str,
    scope: MetricScope,
    component_snapshots: Sequence[MetricSnapshot],
    reported_source_value_minor: Optional[int] = None,
) -> MetricSnapshot:
    """Derive a Metric from the registered component graph without collapsing bases."""

    rule = _catalog_rule(catalog, metric_id)
    if rule.aggregation != "DERIVED" or accounting_basis_id not in rule.allowed_basis_ids:
        raise MetricError("METRIC_DERIVED_BASIS_INVALID", "derived Metric/basis is not registered")
    expected: Tuple[MetricComponentRule, ...] = rule.components_by_basis[accounting_basis_id]
    component_map = {item.key: item for item in component_snapshots}
    if len(component_map) != len(component_snapshots):
        raise MetricError("METRIC_COMPONENT_DUPLICATE", "derived components must be unique")
    blockers = set()
    selected = []
    for component in expected:
        snapshot = component_map.get((component.metric_id, component.basis_id))
        if snapshot is None:
            blockers.add("METRIC_FORMULA_COMPONENT_MISSING")
            continue
        snapshot.validate()
        selected.append((component, snapshot))
        if snapshot.calculation_status != CalculationStatus.VALIDATED:
            blockers.add("METRIC_FORMULA_COMPONENT_BLOCKED")
        if snapshot.as_of != as_of:
            blockers.add("METRIC_PERIOD_COMPONENT_MISMATCH")
        if snapshot.scope != scope:
            blockers.add("METRIC_IDENTITY_COMPONENT_SCOPE_MISMATCH")

    calculated = None
    recomputed = None
    if len(selected) == len(expected):
        calculated = sum(component.sign * int(snapshot.calculated_value_minor or 0) for component, snapshot in selected)
        recomputed = sum(component.sign * int(snapshot.recomputed_value_minor or 0) for component, snapshot in selected)
    channel_delta = None if calculated is None or recomputed is None else calculated - recomputed
    if channel_delta:
        blockers.add("METRIC_RECONCILIATION_DERIVED_CHANNEL_DELTA")
    source_delta = None
    if reported_source_value_minor is not None and recomputed is not None:
        source_delta = reported_source_value_minor - recomputed
        if source_delta:
            blockers.add("METRIC_SOURCE_RECOMPUTED_DELTA")
    status = _status_for_blockers(blockers)
    snapshots_only = [snapshot for _, snapshot in selected]
    return MetricSnapshot(
        metric_id=metric_id,
        accounting_basis_id=accounting_basis_id,
        as_of=as_of,
        as_of_date_rule=rule.as_of_date_rule,
        included_lifecycle_stages=tuple(
            sorted({stage for snapshot in snapshots_only for stage in snapshot.included_lifecycle_stages})
        ),
        scope=scope,
        calculation_status=status,
        source_value_minor=reported_source_value_minor,
        recomputed_value_minor=recomputed,
        calculated_value_minor=calculated,
        source_recomputed_delta_minor=source_delta,
        recomputed_calculated_delta_minor=None if calculated is None or recomputed is None else recomputed - calculated,
        channel_signed_delta_minor=channel_delta,
        channel_absolute_delta_minor=0 if channel_delta == 0 else abs(channel_delta) if channel_delta is not None else None,
        source_control_amount_minor=None,
        source_control_absolute_minor=None,
        source_record_count=sum(item.source_record_count for item in snapshots_only),
        facts_hash=_digest(
            [
                {
                    "metric_id": component.metric_id,
                    "basis_id": component.basis_id,
                    "sign": component.sign,
                    "facts_hash": snapshot.facts_hash,
                }
                for component, snapshot in selected
            ]
        ),
        formula_profile_ids=tuple(sorted({value for item in snapshots_only for value in item.formula_profile_ids})),
        parameter_profile_ids=tuple(sorted({value for item in snapshots_only for value in item.parameter_profile_ids})),
        company_policy_refs=tuple(sorted({value for item in snapshots_only for value in item.company_policy_refs})),
        input_resolution_refs=tuple(sorted({value for item in snapshots_only for value in item.input_resolution_refs})),
        blocker_codes=tuple(sorted(blockers)),
    )


@dataclass(frozen=True)
class MetricBatchResult:
    requested_pairs: Tuple[Tuple[str, str], ...]
    required_pairs: Tuple[Tuple[str, str], ...]
    snapshots: Tuple[MetricSnapshot, ...]
    calculation_status: CalculationStatus
    blocker_codes: Tuple[str, ...]

    def snapshot_map(self) -> Dict[Tuple[str, str], MetricSnapshot]:
        return {item.key: item for item in self.snapshots}

    def validate(self) -> None:
        if not self.requested_pairs or not self.required_pairs:
            raise MetricError("METRIC_REQUEST_EMPTY", "at least one named Metric/basis pair is required")
        if tuple(sorted(set(self.requested_pairs))) != self.requested_pairs:
            raise MetricError("METRIC_REQUEST_PAIRS_INVALID", "requested Metric pairs must be sorted and unique")
        if tuple(sorted(set(self.required_pairs))) != self.required_pairs:
            raise MetricError("METRIC_REQUIRED_PAIRS_INVALID", "required Metric pairs must be sorted and unique")
        for snapshot in self.snapshots:
            snapshot.validate()
        if len(self.snapshot_map()) != len(self.snapshots):
            raise MetricError("METRIC_SNAPSHOT_DUPLICATE", "Metric snapshot keys must be unique")
        if self.calculation_status == CalculationStatus.VALIDATED and self.blocker_codes:
            raise MetricError("METRIC_BATCH_VALIDATED_WITH_BLOCKERS", "validated Metric batch cannot retain blockers")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.metric_batch.v1",
            "requested_pairs": [list(item) for item in self.requested_pairs],
            "required_pairs": [list(item) for item in self.required_pairs],
            "calculation_status": self.calculation_status.value,
            "blocker_codes": list(self.blocker_codes),
            "snapshots": [item.as_dict() for item in self.snapshots],
        }


def build_metric_batch(
    *,
    requested_pairs: Sequence[Tuple[str, str]],
    snapshots: Sequence[MetricSnapshot],
) -> MetricBatchResult:
    """Validate all requested views and force both actual-cost bases into one run."""

    requested = tuple(sorted(set(requested_pairs)))
    if not requested:
        raise MetricError("METRIC_REQUEST_EMPTY", "at least one named Metric/basis pair is required")
    required = set(requested)
    if any(metric_id == "COST_POSTED_ACTUAL" for metric_id, _ in requested):
        required.update(
            {
                ("COST_POSTED_ACTUAL", "JOB_COST_INCURRED"),
                ("COST_POSTED_ACTUAL", "GL_RECOGNIZED_COGS"),
            }
        )
    ordered = tuple(sorted(snapshots, key=lambda item: item.key))
    snapshot_map = {item.key: item for item in ordered}
    blockers = set()
    if len(snapshot_map) != len(ordered):
        blockers.add("METRIC_SCHEMA_DUPLICATE_SNAPSHOT")
    for pair in sorted(required):
        snapshot = snapshot_map.get(pair)
        if snapshot is None:
            blockers.add("METRIC_SCHEMA_REQUIRED_VIEW_MISSING_%s_%s" % pair)
        elif snapshot.calculation_status != CalculationStatus.VALIDATED:
            blockers.add("METRIC_RECONCILIATION_REQUIRED_VIEW_BLOCKED_%s_%s" % pair)
    for snapshot in ordered:
        snapshot.validate()
        if snapshot.calculation_status != CalculationStatus.VALIDATED:
            blockers.update(snapshot.blocker_codes or ("METRIC_RECONCILIATION_SNAPSHOT_BLOCKED",))
    status = _status_for_blockers(blockers)
    return MetricBatchResult(
        requested_pairs=requested,
        required_pairs=tuple(sorted(required)),
        snapshots=ordered,
        calculation_status=status,
        blocker_codes=tuple(sorted(blockers)),
    )
