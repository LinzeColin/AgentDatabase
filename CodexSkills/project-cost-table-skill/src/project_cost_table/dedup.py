"""Deterministic R7 same-stage deduplication with fail-closed version handling."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from itertools import combinations
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from .events import EVIDENCE_REF_RE, RELATION_EVENT_REF_RE, RELATION_SOURCE_KEY_RE, RelationEvent


DEDUP_RESOLUTION_RE = re.compile(r"^dedup_resolution_[0-9a-f]{32}$")
INPUT_RESOLUTION_RE = re.compile(r"^resolution_[0-9a-f]{32}$")
REVIEW_TASK_RE = re.compile(r"^dedup_review_[0-9a-f]{32}$")
DEFAULT_CANDIDATE_PAIR_BUDGET = 1_000_000


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class DedupError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class DuplicateClass(str, Enum):
    BYTE_DUPLICATE = "BYTE_DUPLICATE"
    BUSINESS_CONTENT_DUPLICATE = "BUSINESS_CONTENT_DUPLICATE"
    SAME_KEY_SAME_VERSION = "SAME_KEY_SAME_VERSION"
    SAME_KEY_CHANGED_VERSION = "SAME_KEY_CHANGED_VERSION"
    POSSIBLE_DUPLICATE = "POSSIBLE_DUPLICATE"
    DISTINCT = "DISTINCT"


class DedupDisposition(str, Enum):
    INCLUDED = "INCLUDED"
    EXCLUDED_DUPLICATE = "EXCLUDED_DUPLICATE"
    SUPERSEDED_VERSION = "SUPERSEDED_VERSION"
    PENDING_VERSION_CONFLICT = "PENDING_VERSION_CONFLICT"
    PENDING_BUSINESS_DUPLICATE = "PENDING_BUSINESS_DUPLICATE"
    PENDING_POSSIBLE_DUPLICATE = "PENDING_POSSIBLE_DUPLICATE"


@dataclass(frozen=True)
class BusinessDuplicateResolution:
    resolution_ref: str
    canonical_event_ref: str
    duplicate_event_refs: Tuple[str, ...]
    bound_business_content_fingerprint: str
    input_resolution_ref: str
    evidence_refs: Tuple[str, ...]
    company_approval_state_managed: bool = False

    def validate(self) -> None:
        if not DEDUP_RESOLUTION_RE.fullmatch(self.resolution_ref):
            raise DedupError("DEDUP_RESOLUTION_REF_INVALID", "business duplicate resolution reference is invalid")
        if not RELATION_EVENT_REF_RE.fullmatch(self.canonical_event_ref):
            raise DedupError("DEDUP_RESOLUTION_EVENT_INVALID", "canonical event reference is invalid")
        if (
            not self.duplicate_event_refs
            or tuple(sorted(set(self.duplicate_event_refs))) != self.duplicate_event_refs
            or self.canonical_event_ref in self.duplicate_event_refs
            or any(not RELATION_EVENT_REF_RE.fullmatch(item) for item in self.duplicate_event_refs)
        ):
            raise DedupError("DEDUP_RESOLUTION_EVENTS_INVALID", "duplicate event references must be unique and canonical")
        if not re.fullmatch(r"[0-9a-f]{64}", self.bound_business_content_fingerprint):
            raise DedupError("DEDUP_RESOLUTION_BINDING_INVALID", "business fingerprint binding is invalid")
        _validate_resolution_evidence(self.input_resolution_ref, self.evidence_refs)
        if self.company_approval_state_managed is not False:
            raise DedupError("DEDUP_AUTHORITY_ESCALATION", "dedup resolution cannot manage company approval")
        expected = "dedup_resolution_" + _digest(self._payload())[:32]
        if self.resolution_ref != expected:
            raise DedupError("DEDUP_RESOLUTION_TAMPERED", "business duplicate resolution binding changed")

    def _payload(self) -> Dict[str, Any]:
        return {
            "resolution_type": "BUSINESS_CONTENT_EQUIVALENCE",
            "canonical_event_ref": self.canonical_event_ref,
            "duplicate_event_refs": list(self.duplicate_event_refs),
            "bound_business_content_fingerprint": self.bound_business_content_fingerprint,
            "input_resolution_ref": self.input_resolution_ref,
            "evidence_refs": list(self.evidence_refs),
        }

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {"resolution_ref": self.resolution_ref, **self._payload(), "company_approval_state_managed": False}


@dataclass(frozen=True)
class VersionResolution:
    resolution_ref: str
    canonical_event_ref: str
    superseded_event_refs: Tuple[str, ...]
    bound_source_business_key_hash: str
    input_resolution_ref: str
    evidence_refs: Tuple[str, ...]
    company_approval_state_managed: bool = False

    def validate(self) -> None:
        if not DEDUP_RESOLUTION_RE.fullmatch(self.resolution_ref):
            raise DedupError("DEDUP_RESOLUTION_REF_INVALID", "version resolution reference is invalid")
        if not RELATION_EVENT_REF_RE.fullmatch(self.canonical_event_ref):
            raise DedupError("DEDUP_RESOLUTION_EVENT_INVALID", "canonical version event reference is invalid")
        if (
            not self.superseded_event_refs
            or tuple(sorted(set(self.superseded_event_refs))) != self.superseded_event_refs
            or self.canonical_event_ref in self.superseded_event_refs
            or any(not RELATION_EVENT_REF_RE.fullmatch(item) for item in self.superseded_event_refs)
        ):
            raise DedupError("DEDUP_RESOLUTION_EVENTS_INVALID", "superseded events must be unique and canonical")
        if not RELATION_SOURCE_KEY_RE.fullmatch(self.bound_source_business_key_hash):
            raise DedupError("DEDUP_RESOLUTION_BINDING_INVALID", "version source-key binding is invalid")
        _validate_resolution_evidence(self.input_resolution_ref, self.evidence_refs)
        if self.company_approval_state_managed is not False:
            raise DedupError("DEDUP_AUTHORITY_ESCALATION", "version resolution cannot manage company approval")
        expected = "dedup_resolution_" + _digest(self._payload())[:32]
        if self.resolution_ref != expected:
            raise DedupError("DEDUP_RESOLUTION_TAMPERED", "version resolution binding changed")

    def _payload(self) -> Dict[str, Any]:
        return {
            "resolution_type": "SAME_KEY_VERSION_SELECTION",
            "canonical_event_ref": self.canonical_event_ref,
            "superseded_event_refs": list(self.superseded_event_refs),
            "bound_source_business_key_hash": self.bound_source_business_key_hash,
            "input_resolution_ref": self.input_resolution_ref,
            "evidence_refs": list(self.evidence_refs),
        }

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {"resolution_ref": self.resolution_ref, **self._payload(), "company_approval_state_managed": False}


def _validate_resolution_evidence(input_resolution_ref: str, evidence_refs: Tuple[str, ...]) -> None:
    if not INPUT_RESOLUTION_RE.fullmatch(input_resolution_ref):
        raise DedupError("DEDUP_INPUT_RESOLUTION_INVALID", "dedup decision requires an input-resolution reference")
    if (
        not evidence_refs
        or tuple(sorted(set(evidence_refs))) != evidence_refs
        or any(not EVIDENCE_REF_RE.fullmatch(item) for item in evidence_refs)
    ):
        raise DedupError("DEDUP_EVIDENCE_INVALID", "dedup decision requires unique hash-bound evidence")


def create_business_duplicate_resolution(
    *,
    canonical_event_ref: str,
    duplicate_event_refs: Tuple[str, ...],
    bound_business_content_fingerprint: str,
    input_resolution_ref: str,
    evidence_refs: Tuple[str, ...],
) -> BusinessDuplicateResolution:
    provisional = BusinessDuplicateResolution(
        resolution_ref="dedup_resolution_" + "0" * 32,
        canonical_event_ref=canonical_event_ref,
        duplicate_event_refs=tuple(sorted(duplicate_event_refs)),
        bound_business_content_fingerprint=bound_business_content_fingerprint,
        input_resolution_ref=input_resolution_ref,
        evidence_refs=tuple(sorted(evidence_refs)),
    )
    result = BusinessDuplicateResolution(
        **{**provisional.__dict__, "resolution_ref": "dedup_resolution_" + _digest(provisional._payload())[:32]}
    )
    result.validate()
    return result


def create_version_resolution(
    *,
    canonical_event_ref: str,
    superseded_event_refs: Tuple[str, ...],
    bound_source_business_key_hash: str,
    input_resolution_ref: str,
    evidence_refs: Tuple[str, ...],
) -> VersionResolution:
    provisional = VersionResolution(
        resolution_ref="dedup_resolution_" + "0" * 32,
        canonical_event_ref=canonical_event_ref,
        superseded_event_refs=tuple(sorted(superseded_event_refs)),
        bound_source_business_key_hash=bound_source_business_key_hash,
        input_resolution_ref=input_resolution_ref,
        evidence_refs=tuple(sorted(evidence_refs)),
    )
    result = VersionResolution(
        **{**provisional.__dict__, "resolution_ref": "dedup_resolution_" + _digest(provisional._payload())[:32]}
    )
    result.validate()
    return result


@dataclass(frozen=True)
class DuplicatePairDecision:
    left_event_ref: str
    right_event_ref: str
    duplicate_class: DuplicateClass

    def as_dict(self) -> Dict[str, Any]:
        return {
            "left_event_ref": self.left_event_ref,
            "right_event_ref": self.right_event_ref,
            "duplicate_class": self.duplicate_class.value,
        }


@dataclass(frozen=True)
class DedupDecision:
    relation_event_ref: str
    economic_event_id: str
    disposition: DedupDisposition
    duplicate_class: DuplicateClass
    canonical_event_ref: Optional[str]
    resolution_ref: Optional[str]
    evidence_refs: Tuple[str, ...]
    reason_code: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "relation_event_ref": self.relation_event_ref,
            "economic_event_id": self.economic_event_id,
            "disposition": self.disposition.value,
            "duplicate_class": self.duplicate_class.value,
            "canonical_event_ref": self.canonical_event_ref,
            "resolution_ref": self.resolution_ref,
            "evidence_refs": list(self.evidence_refs),
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class DedupReviewTask:
    review_task_ref: str
    task_type: str
    candidate_event_refs: Tuple[str, ...]
    reason_code: str
    required_resolution: str

    def as_dict(self) -> Dict[str, Any]:
        return {
            "review_task_ref": self.review_task_ref,
            "task_type": self.task_type,
            "candidate_event_refs": list(self.candidate_event_refs),
            "reason_code": self.reason_code,
            "required_resolution": self.required_resolution,
        }


@dataclass(frozen=True)
class DedupResult:
    decisions: Tuple[DedupDecision, ...]
    pair_decisions: Tuple[DuplicatePairDecision, ...]
    review_tasks: Tuple[DedupReviewTask, ...]
    candidate_pair_count: int
    candidate_pair_budget: int
    business_fingerprint: str
    company_approval_state_managed: bool = False

    @property
    def pending_count(self) -> int:
        return sum(1 for item in self.decisions if item.disposition.value.startswith("PENDING_"))

    @property
    def formal_ready(self) -> bool:
        return False

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.dedup_result.v1",
            "decisions": [item.as_dict() for item in self.decisions],
            "pair_decisions": [item.as_dict() for item in self.pair_decisions],
            "review_tasks": [item.as_dict() for item in self.review_tasks],
            "candidate_pair_count": self.candidate_pair_count,
            "candidate_pair_budget": self.candidate_pair_budget,
            "business_fingerprint": self.business_fingerprint,
            "pending_count": self.pending_count,
            "metric_inclusion_status": "NOT_EVALUATED_R7",
            "company_approval_state_managed": False,
        }

    def as_public_summary(self) -> Dict[str, Any]:
        counts = {item.value: 0 for item in DedupDisposition}
        for decision in self.decisions:
            counts[decision.disposition.value] += 1
        return {
            "schema_version": "kmfa.project_cost.dedup_public_summary.v1",
            "event_count": len(self.decisions),
            "disposition_counts": counts,
            "review_task_count": len(self.review_tasks),
            "candidate_pair_count": self.candidate_pair_count,
            "candidate_pair_budget": self.candidate_pair_budget,
            "formal_ready": False,
        }


def _classify_pair(left: RelationEvent, right: RelationEvent) -> DuplicateClass:
    if left.lifecycle_stage != right.lifecycle_stage or left.direction != right.direction:
        return DuplicateClass.DISTINCT
    if left.partition_key != right.partition_key:
        return DuplicateClass.DISTINCT
    if left.source_business_key_hash == right.source_business_key_hash:
        if left.source_business_digest != right.source_business_digest:
            return DuplicateClass.SAME_KEY_CHANGED_VERSION
        if left.source_artifact_sha256 == right.source_artifact_sha256:
            return DuplicateClass.BYTE_DUPLICATE
        return DuplicateClass.SAME_KEY_SAME_VERSION
    if left.business_content_fingerprint == right.business_content_fingerprint:
        return DuplicateClass.BUSINESS_CONTENT_DUPLICATE
    same_amount_date = (
        abs(left.base_amount_minor) == abs(right.base_amount_minor) and left.event_date == right.event_date
    )
    corroborating_candidate = (
        left.counterparty_key is not None
        and left.counterparty_key == right.counterparty_key
        or left.document_id is not None
        and left.document_id == right.document_id
    )
    if same_amount_date and corroborating_candidate:
        return DuplicateClass.POSSIBLE_DUPLICATE
    return DuplicateClass.DISTINCT


def _review_task(task_type: str, event_refs: Iterable[str], reason_code: str, required: str) -> DedupReviewTask:
    refs = tuple(sorted(set(event_refs)))
    payload = {
        "task_type": task_type,
        "candidate_event_refs": list(refs),
        "reason_code": reason_code,
        "required_resolution": required,
    }
    return DedupReviewTask(
        review_task_ref="dedup_review_" + _digest(payload)[:32],
        task_type=task_type,
        candidate_event_refs=refs,
        reason_code=reason_code,
        required_resolution=required,
    )


def _components(edges: Iterable[Tuple[str, str]]) -> Tuple[Tuple[str, ...], ...]:
    neighbours: Dict[str, Set[str]] = {}
    for left, right in edges:
        neighbours.setdefault(left, set()).add(right)
        neighbours.setdefault(right, set()).add(left)
    result: List[Tuple[str, ...]] = []
    seen: Set[str] = set()
    for start in sorted(neighbours):
        if start in seen:
            continue
        stack = [start]
        component: Set[str] = set()
        while stack:
            current = stack.pop()
            if current in component:
                continue
            component.add(current)
            stack.extend(sorted(neighbours.get(current, ()), reverse=True))
        seen.update(component)
        result.append(tuple(sorted(component)))
    return tuple(result)


def deduplicate_events(
    events: Sequence[RelationEvent],
    *,
    business_resolutions: Sequence[BusinessDuplicateResolution] = (),
    version_resolutions: Sequence[VersionResolution] = (),
    candidate_pair_budget: int = DEFAULT_CANDIDATE_PAIR_BUDGET,
) -> DedupResult:
    """Classify same-stage candidates; only exact or explicitly evidenced equivalents are excluded."""

    if (
        isinstance(candidate_pair_budget, bool)
        or not isinstance(candidate_pair_budget, int)
        or candidate_pair_budget < 0
        or candidate_pair_budget > DEFAULT_CANDIDATE_PAIR_BUDGET
    ):
        raise DedupError("CANDIDATE_PAIR_BUDGET_INVALID", "candidate-pair budget must be within the governed ceiling")
    ordered = tuple(sorted(events, key=lambda item: item.relation_event_ref))
    for event in ordered:
        event.validate()
    if len({item.relation_event_ref for item in ordered}) != len(ordered) or len(
        {item.economic_event_id for item in ordered}
    ) != len(ordered):
        raise DedupError("DEDUP_EVENT_ID_COLLISION", "relation events must have unique event identities")

    for resolution in business_resolutions:
        resolution.validate()
    for resolution in version_resolutions:
        resolution.validate()
    all_resolution_refs = [item.resolution_ref for item in (*business_resolutions, *version_resolutions)]
    if len(set(all_resolution_refs)) != len(all_resolution_refs):
        raise DedupError("DEDUP_RESOLUTION_DUPLICATE", "dedup resolution references must be unique")

    partitions: Dict[Tuple[Any, ...], List[RelationEvent]] = {}
    for event in ordered:
        partitions.setdefault(event.partition_key, []).append(event)
    candidate_pair_count = sum(len(group) * (len(group) - 1) // 2 for group in partitions.values())
    if candidate_pair_count > candidate_pair_budget:
        raise DedupError(
            "CANDIDATE_PAIR_BUDGET_EXCEEDED",
            "partitioned duplicate comparison exceeds the governed candidate-pair budget",
        )

    pair_decisions: List[DuplicatePairDecision] = []
    pair_class: Dict[Tuple[str, str], DuplicateClass] = {}
    for group in partitions.values():
        for left, right in combinations(sorted(group, key=lambda item: item.relation_event_ref), 2):
            duplicate_class = _classify_pair(left, right)
            pair_class[(left.relation_event_ref, right.relation_event_ref)] = duplicate_class
            if duplicate_class != DuplicateClass.DISTINCT:
                pair_decisions.append(
                    DuplicatePairDecision(left.relation_event_ref, right.relation_event_ref, duplicate_class)
                )

    event_by_ref = {item.relation_event_ref: item for item in ordered}
    decisions: Dict[str, DedupDecision] = {}
    review_tasks: List[DedupReviewTask] = []
    used_business_resolutions: Set[str] = set()
    used_version_resolutions: Set[str] = set()

    key_groups: Dict[Tuple[Any, ...], List[RelationEvent]] = {}
    for event in ordered:
        key_groups.setdefault((*event.partition_key, event.source_business_key_hash), []).append(event)
    version_by_event_set = {
        frozenset((item.canonical_event_ref, *item.superseded_event_refs)): item for item in version_resolutions
    }
    if len(version_by_event_set) != len(version_resolutions):
        raise DedupError("DEDUP_VERSION_RESOLUTION_AMBIGUOUS", "multiple version resolutions bind the same event set")
    for group in sorted(key_groups.values(), key=lambda items: tuple(item.relation_event_ref for item in items)):
        if len(group) < 2:
            continue
        refs = tuple(sorted(item.relation_event_ref for item in group))
        digests = {item.source_business_digest for item in group}
        if len(digests) > 1:
            resolution = version_by_event_set.get(frozenset(refs))
            if resolution is not None:
                canonical = event_by_ref.get(resolution.canonical_event_ref)
                if canonical is None or canonical.source_business_key_hash != resolution.bound_source_business_key_hash:
                    raise DedupError("DEDUP_VERSION_RESOLUTION_STALE", "version resolution does not bind this source key")
                used_version_resolutions.add(resolution.resolution_ref)
                for event in group:
                    if event.relation_event_ref == canonical.relation_event_ref:
                        disposition = DedupDisposition.INCLUDED
                        reason = "VERSION_SELECTED_BY_EVIDENCE"
                        duplicate_class = DuplicateClass.SAME_KEY_CHANGED_VERSION
                        canonical_ref = None
                    elif event.source_business_digest == canonical.source_business_digest:
                        disposition = DedupDisposition.EXCLUDED_DUPLICATE
                        reason = "SELECTED_VERSION_EXACT_ALIAS"
                        duplicate_class = (
                            DuplicateClass.BYTE_DUPLICATE
                            if event.source_artifact_sha256 == canonical.source_artifact_sha256
                            else DuplicateClass.SAME_KEY_SAME_VERSION
                        )
                        canonical_ref = canonical.relation_event_ref
                    else:
                        disposition = DedupDisposition.SUPERSEDED_VERSION
                        reason = "SUPERSEDED_BY_EVIDENCED_VERSION_RESOLUTION"
                        duplicate_class = DuplicateClass.SAME_KEY_CHANGED_VERSION
                        canonical_ref = canonical.relation_event_ref
                    decisions[event.relation_event_ref] = DedupDecision(
                        event.relation_event_ref,
                        event.economic_event_id,
                        disposition,
                        duplicate_class,
                        canonical_ref,
                        resolution.resolution_ref,
                        resolution.evidence_refs,
                        reason,
                    )
            else:
                for event in group:
                    decisions[event.relation_event_ref] = DedupDecision(
                        event.relation_event_ref,
                        event.economic_event_id,
                        DedupDisposition.PENDING_VERSION_CONFLICT,
                        DuplicateClass.SAME_KEY_CHANGED_VERSION,
                        None,
                        None,
                        (),
                        "SAME_KEY_CHANGED_VERSION_REQUIRES_RESOLUTION",
                    )
                review_tasks.append(
                    _review_task(
                        "VERSION_CONFLICT",
                        refs,
                        "SAME_KEY_CHANGED_VERSION",
                        "hash-bound version selection and evidence",
                    )
                )
        else:
            canonical = min(group, key=lambda item: item.relation_event_ref)
            for event in group:
                if event.relation_event_ref == canonical.relation_event_ref:
                    continue
                duplicate_class = (
                    DuplicateClass.BYTE_DUPLICATE
                    if event.source_artifact_sha256 == canonical.source_artifact_sha256
                    else DuplicateClass.SAME_KEY_SAME_VERSION
                )
                decisions[event.relation_event_ref] = DedupDecision(
                    event.relation_event_ref,
                    event.economic_event_id,
                    DedupDisposition.EXCLUDED_DUPLICATE,
                    duplicate_class,
                    canonical.relation_event_ref,
                    None,
                    (),
                    "EXACT_SAME_KEY_SAME_VERSION",
                )

    business_groups: Dict[Tuple[Any, ...], List[RelationEvent]] = {}
    for event in ordered:
        existing = decisions.get(event.relation_event_ref)
        if existing is None or existing.disposition == DedupDisposition.INCLUDED:
            business_groups.setdefault((*event.partition_key, event.business_content_fingerprint), []).append(event)
    business_by_event_set = {
        frozenset((item.canonical_event_ref, *item.duplicate_event_refs)): item for item in business_resolutions
    }
    if len(business_by_event_set) != len(business_resolutions):
        raise DedupError("DEDUP_BUSINESS_RESOLUTION_AMBIGUOUS", "multiple equivalence resolutions bind the same event set")
    for group in sorted(business_groups.values(), key=lambda items: tuple(item.relation_event_ref for item in items)):
        source_keys = {item.source_business_key_hash for item in group}
        if len(group) < 2 or len(source_keys) < 2:
            continue
        refs = tuple(sorted(item.relation_event_ref for item in group))
        resolution = business_by_event_set.get(frozenset(refs))
        if resolution is not None:
            canonical = event_by_ref.get(resolution.canonical_event_ref)
            if canonical is None or canonical.business_content_fingerprint != resolution.bound_business_content_fingerprint:
                raise DedupError("DEDUP_BUSINESS_RESOLUTION_STALE", "business duplicate resolution fingerprint is stale")
            used_business_resolutions.add(resolution.resolution_ref)
            for event in group:
                decisions[event.relation_event_ref] = DedupDecision(
                    event.relation_event_ref,
                    event.economic_event_id,
                    DedupDisposition.INCLUDED
                    if event.relation_event_ref == canonical.relation_event_ref
                    else DedupDisposition.EXCLUDED_DUPLICATE,
                    DuplicateClass.BUSINESS_CONTENT_DUPLICATE,
                    None if event.relation_event_ref == canonical.relation_event_ref else canonical.relation_event_ref,
                    resolution.resolution_ref,
                    resolution.evidence_refs,
                    "EVIDENCED_BUSINESS_CONTENT_EQUIVALENCE",
                )
        else:
            for event in group:
                decisions[event.relation_event_ref] = DedupDecision(
                    event.relation_event_ref,
                    event.economic_event_id,
                    DedupDisposition.PENDING_BUSINESS_DUPLICATE,
                    DuplicateClass.BUSINESS_CONTENT_DUPLICATE,
                    None,
                    None,
                    (),
                    "BUSINESS_CONTENT_EQUIVALENCE_REQUIRES_RESOLUTION",
                )
            review_tasks.append(
                _review_task(
                    "BUSINESS_DUPLICATE",
                    refs,
                    "BUSINESS_CONTENT_DUPLICATE",
                    "hash-bound equivalence resolution and evidence",
                )
            )

    possible_edges = []
    for pair in pair_decisions:
        if pair.duplicate_class != DuplicateClass.POSSIBLE_DUPLICATE:
            continue
        left = decisions.get(pair.left_event_ref)
        right = decisions.get(pair.right_event_ref)
        if (left is None or left.disposition == DedupDisposition.INCLUDED) and (
            right is None or right.disposition == DedupDisposition.INCLUDED
        ):
            possible_edges.append((pair.left_event_ref, pair.right_event_ref))
    for component in _components(possible_edges):
        for event_ref in component:
            event = event_by_ref[event_ref]
            decisions[event_ref] = DedupDecision(
                event_ref,
                event.economic_event_id,
                DedupDisposition.PENDING_POSSIBLE_DUPLICATE,
                DuplicateClass.POSSIBLE_DUPLICATE,
                None,
                None,
                (),
                "SIMILARITY_IS_CANDIDATE_ONLY",
            )
        review_tasks.append(
            _review_task(
                "POSSIBLE_DUPLICATE",
                component,
                "AMOUNT_DATE_COUNTERPARTY_OR_DOCUMENT_SIMILARITY",
                "stable identifier or explicit evidence; similarity cannot auto-resolve",
            )
        )

    for event in ordered:
        if event.relation_event_ref not in decisions:
            decisions[event.relation_event_ref] = DedupDecision(
                event.relation_event_ref,
                event.economic_event_id,
                DedupDisposition.INCLUDED,
                DuplicateClass.DISTINCT,
                None,
                None,
                (),
                "DISTINCT_SAME_STAGE_EVENT",
            )

    unused_business = {item.resolution_ref for item in business_resolutions} - used_business_resolutions
    unused_version = {item.resolution_ref for item in version_resolutions} - used_version_resolutions
    if unused_business or unused_version:
        raise DedupError("DEDUP_RESOLUTION_STALE", "a supplied dedup resolution did not bind an exact candidate group")

    ordered_decisions = tuple(decisions[item.relation_event_ref] for item in ordered)
    unique_fact_rows = []
    for decision in ordered_decisions:
        if decision.disposition == DedupDisposition.EXCLUDED_DUPLICATE:
            continue
        event = event_by_ref[decision.relation_event_ref]
        unique_fact_rows.append(
            {
                "source_business_key_hash": event.source_business_key_hash,
                "source_business_digest": event.source_business_digest,
                "business_content_fingerprint": event.business_content_fingerprint,
                "disposition": decision.disposition.value,
                "resolution_ref": decision.resolution_ref,
            }
        )
    business_fingerprint = _digest(sorted(unique_fact_rows, key=lambda item: json.dumps(item, sort_keys=True)))
    return DedupResult(
        decisions=ordered_decisions,
        pair_decisions=tuple(sorted(pair_decisions, key=lambda item: (item.left_event_ref, item.right_event_ref))),
        review_tasks=tuple(sorted(review_tasks, key=lambda item: item.review_task_ref)),
        candidate_pair_count=candidate_pair_count,
        candidate_pair_budget=candidate_pair_budget,
        business_fingerprint=business_fingerprint,
    )
