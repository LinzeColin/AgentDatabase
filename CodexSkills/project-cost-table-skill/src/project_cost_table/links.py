"""Typed R7 lifecycle links with explicit allocation, residual, and evidence controls."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .events import (
    EVIDENCE_REF_RE,
    EVENT_ID_RE,
    RELATION_EVENT_REF_RE,
    EventDirection,
    LifecycleStage,
    RelationEvent,
    RelationIdentityStatus,
)


LINK_ID_RE = re.compile(r"^event_link_[0-9a-f]{32}$")
INPUT_RESOLUTION_RE = re.compile(r"^resolution_[0-9a-f]{32}$")
COMPANY_POLICY_RE = re.compile(r"^policy_(?:[0-9a-f]{32}|[A-Z0-9][A-Z0-9_.-]{1,95})$")
LINK_REVIEW_RE = re.compile(r"^link_review_[0-9a-f]{32}$")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class LinkError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class RelationType(str, Enum):
    DERIVED_FROM = "DERIVED_FROM"
    FULFILLS_COMMITMENT = "FULFILLS_COMMITMENT"
    ACCRUAL_FOR = "ACCRUAL_FOR"
    REVERSES = "REVERSES"
    SUPERSEDES = "SUPERSEDES"
    INVOICES = "INVOICES"
    POSTS_TO_GL = "POSTS_TO_GL"
    SETTLES = "SETTLES"
    ALLOCATES_TO = "ALLOCATES_TO"
    TRANSFERRED_BETWEEN = "TRANSFERRED_BETWEEN"
    REFERENCES_ONLY = "REFERENCES_ONLY"


class MatchMethod(str, Enum):
    STABLE_IDENTIFIER = "STABLE_IDENTIFIER"
    VALIDATED_IDENTITY_CONTRACT = "VALIDATED_IDENTITY_CONTRACT"
    INPUT_RESOLUTION_ALLOCATION = "INPUT_RESOLUTION_ALLOCATION"
    REVERSAL_LINEAGE = "REVERSAL_LINEAGE"
    VERSION_RESOLUTION = "VERSION_RESOLUTION"
    AMOUNT_DATE_TEXT_SIMILARITY = "AMOUNT_DATE_TEXT_SIMILARITY"


class LinkStatus(str, Enum):
    CANDIDATE = "CANDIDATE"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    BLOCKED = "BLOCKED"
    SUPERSEDED = "SUPERSEDED"


class LinkCompletionStatus(str, Enum):
    FULLY_ALLOCATED = "FULLY_ALLOCATED"
    PENDING_RESIDUAL = "PENDING_RESIDUAL"
    NOT_APPLICABLE = "NOT_APPLICABLE"


FINANCIAL_RELATIONS = frozenset(
    {
        RelationType.FULFILLS_COMMITMENT,
        RelationType.ACCRUAL_FOR,
        RelationType.REVERSES,
        RelationType.INVOICES,
        RelationType.POSTS_TO_GL,
        RelationType.SETTLES,
        RelationType.ALLOCATES_TO,
        RelationType.TRANSFERRED_BETWEEN,
    }
)
SCOPE_RESOLUTION_RELATIONS = frozenset(
    {RelationType.SETTLES, RelationType.ALLOCATES_TO, RelationType.TRANSFERRED_BETWEEN}
)
LINK_AXIS = {
    RelationType.DERIVED_FROM: "DERIVATION",
    RelationType.FULFILLS_COMMITMENT: "COMMITMENT_FULFILLMENT",
    RelationType.ACCRUAL_FOR: "ACCRUAL_POSTING",
    RelationType.REVERSES: "REVERSAL",
    RelationType.SUPERSEDES: "VERSION",
    RelationType.INVOICES: "CONTRACT_INVOICE",
    RelationType.POSTS_TO_GL: "INVOICE_GL",
    RelationType.SETTLES: "CASH_SETTLEMENT",
    RelationType.ALLOCATES_TO: "GENERAL_ALLOCATION",
    RelationType.TRANSFERRED_BETWEEN: "SCOPE_TRANSFER",
    RelationType.REFERENCES_ONLY: "REFERENCE",
}


@dataclass(frozen=True)
class EventParticipation:
    relation_event_ref: str
    economic_event_id: str
    event_binding_sha256: str
    direction: EventDirection
    lifecycle_stage: LifecycleStage
    identity_status: RelationIdentityStatus
    legal_entity_id: str
    canonical_project_id: Optional[str]
    wbs_or_cost_code: Optional[str]
    canonical_contract_id: Optional[str]
    base_amount_minor: int
    allocated_base_amount_minor: int
    reversal_of_event_id: Optional[str]

    @property
    def scope_key(self) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
        return (
            self.canonical_project_id,
            self.wbs_or_cost_code,
            self.canonical_contract_id,
            self.legal_entity_id,
        )

    def validate(self, *, financial: bool) -> None:
        if (
            not RELATION_EVENT_REF_RE.fullmatch(self.relation_event_ref)
            or not EVENT_ID_RE.fullmatch(self.economic_event_id)
            or not re.fullmatch(r"[0-9a-f]{64}", self.event_binding_sha256)
        ):
            raise LinkError("LINK_PARTICIPANT_ID_INVALID", "event participation lineage is invalid")
        if not isinstance(self.direction, EventDirection) or not isinstance(self.lifecycle_stage, LifecycleStage):
            raise LinkError("LINK_PARTICIPANT_LIFECYCLE_INVALID", "event participation lifecycle is invalid")
        if not isinstance(self.identity_status, RelationIdentityStatus):
            raise LinkError("LINK_PARTICIPANT_IDENTITY_INVALID", "event participation identity status is invalid")
        if not isinstance(self.base_amount_minor, int) or isinstance(self.base_amount_minor, bool):
            raise LinkError("LINK_PARTICIPANT_AMOUNT_INVALID", "participant amount must use integer minor units")
        if not isinstance(self.allocated_base_amount_minor, int) or isinstance(
            self.allocated_base_amount_minor, bool
        ):
            raise LinkError("LINK_ALLOCATION_INVALID", "allocation must use integer minor units")
        if financial:
            if self.allocated_base_amount_minor <= 0 or self.allocated_base_amount_minor > abs(
                self.base_amount_minor
            ):
                raise LinkError("LINK_ALLOCATION_OUT_OF_RANGE", "financial allocation exceeds event magnitude")
        elif self.allocated_base_amount_minor != 0:
            raise LinkError("LINK_NONFINANCIAL_ALLOCATION", "nonfinancial relations cannot allocate money")

    def as_dict(self) -> Dict[str, Any]:
        return {
            "relation_event_ref": self.relation_event_ref,
            "economic_event_id": self.economic_event_id,
            "event_binding_sha256": self.event_binding_sha256,
            "direction": self.direction.value,
            "lifecycle_stage": self.lifecycle_stage.value,
            "identity_status": self.identity_status.value,
            "legal_entity_id": self.legal_entity_id,
            "canonical_project_id": self.canonical_project_id,
            "wbs_or_cost_code": self.wbs_or_cost_code,
            "canonical_contract_id": self.canonical_contract_id,
            "base_amount_minor": self.base_amount_minor,
            "allocated_base_amount_minor": self.allocated_base_amount_minor,
            "reversal_of_event_id": self.reversal_of_event_id,
        }


@dataclass(frozen=True)
class EventLink:
    link_id: str
    relation_type: RelationType
    link_axis: str
    source_participations: Tuple[EventParticipation, ...]
    target_participations: Tuple[EventParticipation, ...]
    allocated_base_amount_minor: int
    source_residual_base_amount_minor: int
    target_residual_base_amount_minor: int
    completion_status: LinkCompletionStatus
    status: LinkStatus
    match_method: MatchMethod
    input_resolution_ref: Optional[str]
    company_policy_ref: Optional[str]
    evidence_refs: Tuple[str, ...]
    metric_inclusion_status: str = "NOT_EVALUATED_R7"
    company_approval_state_managed: bool = False

    def _payload(self) -> Dict[str, Any]:
        return {
            "relation_type": self.relation_type.value,
            "link_axis": self.link_axis,
            "source_participations": [item.as_dict() for item in self.source_participations],
            "target_participations": [item.as_dict() for item in self.target_participations],
            "allocated_base_amount_minor": self.allocated_base_amount_minor,
            "source_residual_base_amount_minor": self.source_residual_base_amount_minor,
            "target_residual_base_amount_minor": self.target_residual_base_amount_minor,
            "completion_status": self.completion_status.value,
            "status": self.status.value,
            "match_method": self.match_method.value,
            "input_resolution_ref": self.input_resolution_ref,
            "company_policy_ref": self.company_policy_ref,
            "evidence_refs": list(self.evidence_refs),
            "metric_inclusion_status": self.metric_inclusion_status,
        }

    def validate(self) -> None:
        if not isinstance(self.relation_type, RelationType) or not isinstance(self.status, LinkStatus):
            raise LinkError("LINK_ENUM_INVALID", "relation type or status is not registered")
        if not isinstance(self.match_method, MatchMethod) or not isinstance(
            self.completion_status, LinkCompletionStatus
        ):
            raise LinkError("LINK_ENUM_INVALID", "link method or completion status is not registered")
        if self.link_axis != LINK_AXIS[self.relation_type]:
            raise LinkError("LINK_AXIS_INVALID", "link axis does not match relation type")
        financial = self.relation_type in FINANCIAL_RELATIONS
        if not self.source_participations or not self.target_participations:
            raise LinkError("LINK_PARTICIPANTS_MISSING", "link requires source and target events")
        all_parts = (*self.source_participations, *self.target_participations)
        for item in all_parts:
            item.validate(financial=financial)
        refs = [item.relation_event_ref for item in all_parts]
        if len(refs) != len(set(refs)):
            raise LinkError("LINK_PARTICIPANT_DUPLICATE", "an event can participate only once within one link")
        if tuple(sorted(self.source_participations, key=lambda item: item.relation_event_ref)) != self.source_participations:
            raise LinkError("LINK_PARTICIPANT_ORDER", "source event participations must be sorted")
        if tuple(sorted(self.target_participations, key=lambda item: item.relation_event_ref)) != self.target_participations:
            raise LinkError("LINK_PARTICIPANT_ORDER", "target event participations must be sorted")
        _validate_stage_and_direction(self.relation_type, self.source_participations, self.target_participations)
        scopes = {item.scope_key for item in all_parts}
        ambiguous = any(item.identity_status == RelationIdentityStatus.ALLOCATION_REQUIRED for item in all_parts)
        if (len(scopes) != 1 or ambiguous) and (
            self.relation_type not in SCOPE_RESOLUTION_RELATIONS
            or self.input_resolution_ref is None
            or not self.evidence_refs
        ):
            raise LinkError(
                "LINK_SCOPE_RESOLUTION_REQUIRED",
                "ambiguous or cross-scope link requires an allowed relation plus hash-bound input resolution",
            )
        source_allocated = sum(item.allocated_base_amount_minor for item in self.source_participations)
        target_allocated = sum(item.allocated_base_amount_minor for item in self.target_participations)
        source_capacity = sum(abs(item.base_amount_minor) for item in self.source_participations)
        target_capacity = sum(abs(item.base_amount_minor) for item in self.target_participations)
        if source_allocated != target_allocated or source_allocated != self.allocated_base_amount_minor:
            raise LinkError("LINK_ALLOCATION_NOT_CONSERVED", "source and target allocations must reconcile exactly")
        if self.source_residual_base_amount_minor != source_capacity - source_allocated or self.target_residual_base_amount_minor != (
            target_capacity - target_allocated
        ):
            raise LinkError("LINK_RESIDUAL_INVALID", "link residual does not reconcile to event capacity")
        expected_completion = (
            LinkCompletionStatus.NOT_APPLICABLE
            if not financial
            else LinkCompletionStatus.FULLY_ALLOCATED
            if self.source_residual_base_amount_minor == 0 and self.target_residual_base_amount_minor == 0
            else LinkCompletionStatus.PENDING_RESIDUAL
        )
        if self.completion_status != expected_completion:
            raise LinkError("LINK_COMPLETION_INVALID", "link completion status does not match residuals")
        if not isinstance(self.evidence_refs, tuple) or tuple(sorted(set(self.evidence_refs))) != self.evidence_refs:
            raise LinkError("LINK_EVIDENCE_INVALID", "link evidence references must be unique and sorted")
        if any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs):
            raise LinkError("LINK_EVIDENCE_INVALID", "link evidence must be hash-bound")
        if self.input_resolution_ref is not None and not INPUT_RESOLUTION_RE.fullmatch(self.input_resolution_ref):
            raise LinkError("LINK_INPUT_RESOLUTION_INVALID", "input-resolution reference is invalid")
        if self.company_policy_ref is not None and not COMPANY_POLICY_RE.fullmatch(self.company_policy_ref):
            raise LinkError("LINK_POLICY_REF_INVALID", "company policy reference is invalid")
        if self.status == LinkStatus.APPROVED:
            if not self.evidence_refs:
                raise LinkError("LINK_APPROVED_EVIDENCE_REQUIRED", "approved data link requires qualified evidence")
            if self.match_method == MatchMethod.AMOUNT_DATE_TEXT_SIMILARITY:
                raise LinkError("LINK_SIMILARITY_CANNOT_APPROVE", "amount, date, or text similarity is candidate-only")
        if self.match_method == MatchMethod.AMOUNT_DATE_TEXT_SIMILARITY and self.status != LinkStatus.CANDIDATE:
            raise LinkError("LINK_SIMILARITY_CANDIDATE_ONLY", "similarity match cannot become a decided link")
        if self.match_method == MatchMethod.INPUT_RESOLUTION_ALLOCATION and self.input_resolution_ref is None:
            raise LinkError("LINK_INPUT_RESOLUTION_REQUIRED", "allocation method requires an input resolution")
        if self.relation_type == RelationType.REVERSES:
            if len(self.source_participations) != 1 or len(self.target_participations) != 1:
                raise LinkError("LINK_REVERSAL_CARDINALITY", "reversal link must be one-to-one")
            original = self.source_participations[0]
            reversal = self.target_participations[0]
            if (
                reversal.reversal_of_event_id != original.economic_event_id
                or original.base_amount_minor + reversal.base_amount_minor != 0
                or self.allocated_base_amount_minor != abs(original.base_amount_minor)
                or self.match_method != MatchMethod.REVERSAL_LINEAGE
            ):
                raise LinkError("LINK_REVERSAL_NOT_CONSERVED", "reversal must bind the original and net to zero cents")
        if self.relation_type == RelationType.SUPERSEDES and self.match_method != MatchMethod.VERSION_RESOLUTION:
            raise LinkError("LINK_SUPERSESSION_METHOD_INVALID", "supersession requires explicit version resolution")
        if self.metric_inclusion_status != "NOT_EVALUATED_R7":
            raise LinkError("LINK_METRIC_AUTHORITY_ESCALATION", "R7 cannot decide final Metric inclusion")
        if self.company_approval_state_managed is not False:
            raise LinkError("LINK_COMPANY_APPROVAL_AUTHORITY", "Skill cannot manage company approval state")
        expected_id = "event_link_" + _digest({**self._payload(), "link_id": None})[:32]
        if self.link_id != expected_id:
            raise LinkError("LINK_TAMPERED", "link ID no longer matches its immutable payload")

    @property
    def allocation_delta_minor(self) -> int:
        return sum(item.allocated_base_amount_minor for item in self.source_participations) - sum(
            item.allocated_base_amount_minor for item in self.target_participations
        )

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.event_link.v1",
            "link_id": self.link_id,
            **self._payload(),
            "source_event_ids": [item.economic_event_id for item in self.source_participations],
            "target_event_ids": [item.economic_event_id for item in self.target_participations],
            "allocation_delta_minor": self.allocation_delta_minor,
            "company_approval_state_managed": False,
        }


def _participation(event: RelationEvent, amount: int) -> EventParticipation:
    event.validate()
    return EventParticipation(
        relation_event_ref=event.relation_event_ref,
        economic_event_id=event.economic_event_id,
        event_binding_sha256=_digest(event.as_private_dict()),
        direction=event.direction,
        lifecycle_stage=event.lifecycle_stage,
        identity_status=event.identity_binding.identity_status,
        legal_entity_id=event.identity_binding.legal_entity_id,
        canonical_project_id=event.identity_binding.canonical_project_id,
        wbs_or_cost_code=event.identity_binding.wbs_or_cost_code,
        canonical_contract_id=event.identity_binding.canonical_contract_id,
        base_amount_minor=event.base_amount_minor,
        allocated_base_amount_minor=amount,
        reversal_of_event_id=event.reversal_of_event_id,
    )


def _validate_stage_and_direction(
    relation_type: RelationType,
    sources: Sequence[RelationEvent],
    targets: Sequence[RelationEvent],
) -> None:
    source_stages = {item.lifecycle_stage for item in sources}
    target_stages = {item.lifecycle_stage for item in targets}
    source_directions = {item.direction for item in sources}
    target_directions = {item.direction for item in targets}
    valid = True
    if relation_type == RelationType.FULFILLS_COMMITMENT:
        valid = source_stages == {LifecycleStage.COMMITMENT} and target_stages == {LifecycleStage.POSTED_ACTUAL}
        valid = valid and source_directions == target_directions == {EventDirection.COST}
    elif relation_type == RelationType.ACCRUAL_FOR:
        valid = source_stages == {LifecycleStage.ACCRUAL} and target_stages == {LifecycleStage.POSTED_ACTUAL}
        valid = valid and source_directions == target_directions == {EventDirection.COST}
    elif relation_type == RelationType.INVOICES:
        valid = source_stages == {LifecycleStage.CONTRACT_VALUE} and target_stages == {LifecycleStage.BILLED}
        valid = valid and source_directions == target_directions == {EventDirection.REVENUE}
    elif relation_type == RelationType.POSTS_TO_GL:
        valid = source_stages == {LifecycleStage.BILLED} and target_stages == {LifecycleStage.RECOGNIZED_REVENUE}
        valid = valid and source_directions == target_directions == {EventDirection.REVENUE}
    elif relation_type == RelationType.SETTLES:
        valid = (
            source_stages == {LifecycleStage.POSTED_ACTUAL}
            and target_stages == {LifecycleStage.PAID}
            and source_directions == {EventDirection.COST}
            and target_directions == {EventDirection.CASH_OUT}
        ) or (
            source_stages.issubset({LifecycleStage.BILLED, LifecycleStage.RECOGNIZED_REVENUE})
            and target_stages == {LifecycleStage.COLLECTED}
            and source_directions == {EventDirection.REVENUE}
            and target_directions == {EventDirection.CASH_IN}
        )
    elif relation_type in {RelationType.REVERSES, RelationType.SUPERSEDES, RelationType.TRANSFERRED_BETWEEN}:
        valid = source_stages == target_stages and source_directions == target_directions
    if not valid:
        raise LinkError("LINK_LIFECYCLE_INCOMPATIBLE", "relation type conflicts with source and target lifecycle stages")


def _validate_scope(
    relation_type: RelationType,
    all_events: Sequence[RelationEvent],
    *,
    input_resolution_ref: Optional[str],
    evidence_refs: Tuple[str, ...],
) -> None:
    scopes = {item.identity_binding.scope_key for item in all_events}
    ambiguous = any(item.identity_binding.identity_status == RelationIdentityStatus.ALLOCATION_REQUIRED for item in all_events)
    if len(scopes) == 1 and not ambiguous:
        return
    if (
        relation_type not in SCOPE_RESOLUTION_RELATIONS
        or input_resolution_ref is None
        or not INPUT_RESOLUTION_RE.fullmatch(input_resolution_ref)
        or not evidence_refs
    ):
        raise LinkError(
            "LINK_SCOPE_RESOLUTION_REQUIRED",
            "ambiguous or cross-scope link requires an allowed relation plus hash-bound input resolution",
        )


def create_event_link(
    *,
    relation_type: RelationType,
    source_events: Sequence[RelationEvent],
    target_events: Sequence[RelationEvent],
    source_allocations: Mapping[str, int],
    target_allocations: Mapping[str, int],
    status: LinkStatus,
    match_method: MatchMethod,
    input_resolution_ref: Optional[str] = None,
    company_policy_ref: Optional[str] = None,
    evidence_refs: Tuple[str, ...] = (),
) -> EventLink:
    """Create a typed link. Allocation uses absolute magnitudes; event signs remain untouched."""

    if not isinstance(relation_type, RelationType) or not isinstance(status, LinkStatus) or not isinstance(
        match_method, MatchMethod
    ):
        raise LinkError("LINK_ENUM_INVALID", "link arguments require registered enums")
    sources = tuple(sorted(source_events, key=lambda item: item.relation_event_ref))
    targets = tuple(sorted(target_events, key=lambda item: item.relation_event_ref))
    if not sources or not targets:
        raise LinkError("LINK_PARTICIPANTS_MISSING", "link requires source and target events")
    for event in (*sources, *targets):
        event.validate()
    source_refs = {item.relation_event_ref for item in sources}
    target_refs = {item.relation_event_ref for item in targets}
    if source_refs & target_refs:
        raise LinkError("LINK_SELF_REFERENCE", "source and target event sets must be disjoint")
    if set(source_allocations) != source_refs or set(target_allocations) != target_refs:
        raise LinkError("LINK_ALLOCATION_COVERAGE", "allocation maps must cover each participant exactly once")
    evidence = tuple(sorted(evidence_refs))
    _validate_stage_and_direction(relation_type, sources, targets)
    _validate_scope(
        relation_type,
        (*sources, *targets),
        input_resolution_ref=input_resolution_ref,
        evidence_refs=evidence,
    )
    financial = relation_type in FINANCIAL_RELATIONS
    source_parts = tuple(_participation(item, source_allocations[item.relation_event_ref]) for item in sources)
    target_parts = tuple(_participation(item, target_allocations[item.relation_event_ref]) for item in targets)
    source_total = sum(item.allocated_base_amount_minor for item in source_parts)
    target_total = sum(item.allocated_base_amount_minor for item in target_parts)
    if source_total != target_total:
        raise LinkError("LINK_ALLOCATION_NOT_CONSERVED", "source and target allocations differ")
    if financial and source_total <= 0:
        raise LinkError("LINK_ALLOCATION_REQUIRED", "financial link requires a positive allocation magnitude")
    if not financial and source_total != 0:
        raise LinkError("LINK_NONFINANCIAL_ALLOCATION", "nonfinancial link allocation must be zero")
    if relation_type == RelationType.REVERSES:
        if len(sources) != 1 or len(targets) != 1:
            raise LinkError("LINK_REVERSAL_CARDINALITY", "reversal link must be one-to-one")
        original, reversal = sources[0], targets[0]
        if (
            reversal.reversal_of_event_id != original.economic_event_id
            or original.base_amount_minor + reversal.base_amount_minor != 0
            or source_total != abs(original.base_amount_minor)
        ):
            raise LinkError("LINK_REVERSAL_NOT_CONSERVED", "reversal must bind the original and net to zero cents")
        if match_method != MatchMethod.REVERSAL_LINEAGE:
            raise LinkError("LINK_REVERSAL_METHOD_INVALID", "reversal requires source lineage matching")
    if relation_type == RelationType.SUPERSEDES and match_method != MatchMethod.VERSION_RESOLUTION:
        raise LinkError("LINK_SUPERSESSION_METHOD_INVALID", "supersession requires explicit version resolution")

    source_capacity = sum(abs(item.base_amount_minor) for item in source_parts)
    target_capacity = sum(abs(item.base_amount_minor) for item in target_parts)
    source_residual = source_capacity - source_total
    target_residual = target_capacity - target_total
    completion = (
        LinkCompletionStatus.NOT_APPLICABLE
        if not financial
        else LinkCompletionStatus.FULLY_ALLOCATED
        if source_residual == 0 and target_residual == 0
        else LinkCompletionStatus.PENDING_RESIDUAL
    )
    provisional = EventLink(
        link_id="event_link_" + "0" * 32,
        relation_type=relation_type,
        link_axis=LINK_AXIS[relation_type],
        source_participations=source_parts,
        target_participations=target_parts,
        allocated_base_amount_minor=source_total,
        source_residual_base_amount_minor=source_residual,
        target_residual_base_amount_minor=target_residual,
        completion_status=completion,
        status=status,
        match_method=match_method,
        input_resolution_ref=input_resolution_ref,
        company_policy_ref=company_policy_ref,
        evidence_refs=evidence,
    )
    result = EventLink(**{**provisional.__dict__, "link_id": "event_link_" + _digest({**provisional._payload(), "link_id": None})[:32]})
    result.validate()
    return result


@dataclass(frozen=True)
class LinkReviewTask:
    review_task_ref: str
    link_id: str
    reason_code: str
    required_evidence: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "review_task_ref": self.review_task_ref,
            "link_id": self.link_id,
            "reason_code": self.reason_code,
            "required_evidence": self.required_evidence,
        }


@dataclass(frozen=True)
class LinkSetResult:
    status: str
    links: Tuple[EventLink, ...]
    match_groups: Tuple["MatchGroupControl", ...]
    review_tasks: Tuple[LinkReviewTask, ...]
    conflict_codes: Tuple[str, ...]
    approved_link_count: int
    candidate_link_count: int
    pending_residual_count: int
    allocation_conservation_delta_minor: int
    company_approval_state_managed: bool = False

    @property
    def formal_ready(self) -> bool:
        return False

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.event_link_set.v1",
            "status": self.status,
            "links": [item.as_private_dict() for item in self.links],
            "match_groups": [item.as_dict() for item in self.match_groups],
            "review_tasks": [item.as_dict() for item in self.review_tasks],
            "conflict_codes": list(self.conflict_codes),
            "approved_link_count": self.approved_link_count,
            "candidate_link_count": self.candidate_link_count,
            "pending_residual_count": self.pending_residual_count,
            "allocation_conservation_delta_minor": self.allocation_conservation_delta_minor,
            "metric_inclusion_status": "NOT_EVALUATED_R7",
            "company_approval_state_managed": False,
        }

    def as_public_summary(self) -> Dict[str, Any]:
        relation_counts = {item.value: 0 for item in RelationType}
        for link in self.links:
            relation_counts[link.relation_type.value] += 1
        return {
            "schema_version": "kmfa.project_cost.event_link_public_summary.v1",
            "status": self.status,
            "link_count": len(self.links),
            "match_group_count": len(self.match_groups),
            "relation_counts": relation_counts,
            "approved_link_count": self.approved_link_count,
            "candidate_link_count": self.candidate_link_count,
            "pending_residual_count": self.pending_residual_count,
            "review_task_count": len(self.review_tasks),
            "conflict_codes": list(self.conflict_codes),
            "allocation_conservation_delta_minor": self.allocation_conservation_delta_minor,
            "formal_ready": False,
        }


@dataclass(frozen=True)
class MatchGroupControl:
    match_group_ref: str
    link_axis: str
    link_ids: Tuple[str, ...]
    relation_event_refs: Tuple[str, ...]
    allocated_participation_minor: int
    event_capacity_minor: int
    residual_capacity_minor: int
    allocation_delta_minor: int
    status: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "match_group_ref": self.match_group_ref,
            "link_axis": self.link_axis,
            "link_ids": list(self.link_ids),
            "relation_event_refs": list(self.relation_event_refs),
            "allocated_participation_minor": self.allocated_participation_minor,
            "event_capacity_minor": self.event_capacity_minor,
            "residual_capacity_minor": self.residual_capacity_minor,
            "allocation_delta_minor": self.allocation_delta_minor,
            "status": self.status,
        }


def _connected_link_groups(links: Sequence[EventLink]) -> Tuple[Tuple[EventLink, ...], ...]:
    by_axis: Dict[str, List[EventLink]] = {}
    for link in links:
        if link.status == LinkStatus.APPROVED and link.relation_type in FINANCIAL_RELATIONS:
            by_axis.setdefault(link.link_axis, []).append(link)
    result: List[Tuple[EventLink, ...]] = []
    for axis in sorted(by_axis):
        remaining = {item.link_id: item for item in by_axis[axis]}
        event_refs = {
            item.link_id: {part.relation_event_ref for part in (*item.source_participations, *item.target_participations)}
            for item in by_axis[axis]
        }
        while remaining:
            start_id = min(remaining)
            pending = [start_id]
            component_ids = set()
            component_events = set()
            while pending:
                link_id = pending.pop()
                if link_id in component_ids:
                    continue
                component_ids.add(link_id)
                component_events.update(event_refs[link_id])
                for candidate_id in sorted(remaining):
                    if candidate_id not in component_ids and event_refs[candidate_id] & component_events:
                        pending.append(candidate_id)
            component = tuple(sorted((remaining.pop(item) for item in component_ids), key=lambda link: link.link_id))
            result.append(component)
    return tuple(result)


def _match_group_control(group: Sequence[EventLink]) -> MatchGroupControl:
    axis = group[0].link_axis
    usage: Dict[str, int] = {}
    capacity: Dict[str, int] = {}
    for link in group:
        for participant in (*link.source_participations, *link.target_participations):
            event_ref = participant.relation_event_ref
            usage[event_ref] = usage.get(event_ref, 0) + participant.allocated_base_amount_minor
            prior = capacity.setdefault(event_ref, abs(participant.base_amount_minor))
            if prior != abs(participant.base_amount_minor):
                raise LinkError("LINK_EVENT_CAPACITY_CHANGED", "event capacity changed within a match group")
    overallocated = any(usage[event_ref] > capacity[event_ref] for event_ref in usage)
    event_capacity = sum(capacity.values())
    allocated = sum(usage.values())
    residual = event_capacity - allocated
    allocation_delta = sum(link.allocation_delta_minor for link in group)
    status = (
        "BLOCKED_OVERALLOCATION"
        if overallocated
        else "ERROR_NOT_CONSERVED"
        if allocation_delta != 0
        else "PENDING_RESIDUAL"
        if residual != 0
        else "PASS"
    )
    payload = {
        "link_axis": axis,
        "link_ids": [item.link_id for item in group],
        "relation_event_refs": sorted(usage),
        "allocated_participation_minor": allocated,
        "event_capacity_minor": event_capacity,
        "residual_capacity_minor": residual,
        "allocation_delta_minor": allocation_delta,
        "status": status,
    }
    return MatchGroupControl(
        match_group_ref="match_group_" + _digest(payload)[:32],
        link_axis=axis,
        link_ids=tuple(payload["link_ids"]),
        relation_event_refs=tuple(payload["relation_event_refs"]),
        allocated_participation_minor=allocated,
        event_capacity_minor=event_capacity,
        residual_capacity_minor=residual,
        allocation_delta_minor=allocation_delta,
        status=status,
    )


def _link_review(link: EventLink, reason: str, required: str) -> LinkReviewTask:
    payload = {"link_id": link.link_id, "reason_code": reason, "required_evidence": required}
    return LinkReviewTask(
        review_task_ref="link_review_" + _digest(payload)[:32],
        link_id=link.link_id,
        reason_code=reason,
        required_evidence=required,
    )


def reconcile_event_links(links: Sequence[EventLink]) -> LinkSetResult:
    """Enforce per-axis capacity so one event can link across axes but not double allocate within one axis."""

    ordered = tuple(sorted(links, key=lambda item: item.link_id))
    for link in ordered:
        link.validate()
    if len({item.link_id for item in ordered}) != len(ordered):
        raise LinkError("LINK_ID_COLLISION", "event link IDs must be unique")
    usage: Dict[Tuple[str, str], int] = {}
    capacity: Dict[Tuple[str, str], int] = {}
    conflicts: List[str] = []
    reviews: List[LinkReviewTask] = []
    for link in ordered:
        if link.status == LinkStatus.CANDIDATE:
            reviews.append(
                _link_review(
                    link,
                    "AMBIGUOUS_LINK_CANDIDATE",
                    "stable identifier, qualified identity/contract, or hash-bound input resolution",
                )
            )
        if link.status != LinkStatus.APPROVED:
            continue
        for participant in (*link.source_participations, *link.target_participations):
            key = (link.link_axis, participant.relation_event_ref)
            usage[key] = usage.get(key, 0) + participant.allocated_base_amount_minor
            prior_capacity = capacity.setdefault(key, abs(participant.base_amount_minor))
            if prior_capacity != abs(participant.base_amount_minor):
                conflicts.append("LINK_EVENT_CAPACITY_CHANGED")
    if any(usage[key] > capacity[key] for key in usage):
        conflicts.append("LINK_AXIS_OVERALLOCATED")
    match_groups = tuple(_match_group_control(group) for group in _connected_link_groups(ordered))
    pending_residual_count = sum(item.status == "PENDING_RESIDUAL" for item in match_groups)
    if pending_residual_count:
        conflicts.append("PENDING_LINK_RESIDUAL")
        for group in match_groups:
            if group.status == "PENDING_RESIDUAL":
                link = next(item for item in ordered if item.link_id == group.link_ids[0])
                reviews.append(
                    _link_review(link, "PENDING_LINK_RESIDUAL", "complete the connected match-group allocation")
                )
    candidate_count = sum(1 for item in ordered if item.status == LinkStatus.CANDIDATE)
    if candidate_count:
        conflicts.append("AMBIGUOUS_LINK_CANDIDATE")
    allocation_delta = sum(item.allocation_delta_minor for item in ordered)
    if allocation_delta != 0:
        conflicts.append("LINK_ALLOCATION_NOT_CONSERVED")
    conflict_codes = tuple(sorted(set(conflicts)))
    return LinkSetResult(
        status="PASS" if not conflict_codes else "BLOCKED",
        links=ordered,
        match_groups=match_groups,
        review_tasks=tuple(sorted(reviews, key=lambda item: item.review_task_ref)),
        conflict_codes=conflict_codes,
        approved_link_count=sum(1 for item in ordered if item.status == LinkStatus.APPROVED),
        candidate_link_count=candidate_count,
        pending_residual_count=pending_residual_count,
        allocation_conservation_delta_minor=allocation_delta,
    )
