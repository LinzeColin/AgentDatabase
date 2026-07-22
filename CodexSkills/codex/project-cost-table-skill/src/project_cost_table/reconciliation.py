"""R7 source conservation and genuinely independent dual-channel aggregation."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .dedup import DedupDisposition, DedupResult
from .events import RELATION_EVENT_REF_RE, RelationEvent, SourceEventStatus
from .links import LinkSetResult


RECONCILIATION_ID_RE = re.compile(r"^reconciliation_[0-9a-f]{32}$")
PARSE_ERROR_REF_RE = re.compile(r"^parse_error_[0-9a-f]{32}$")


def _digest(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()


class ReconciliationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


class ConservationDisposition(str, Enum):
    INCLUDED = "INCLUDED"
    EXCLUDED = "EXCLUDED"
    PENDING = "PENDING"
    PARSE_ERROR = "PARSE_ERROR"


@dataclass(frozen=True)
class ParseErrorAmount:
    parse_error_ref: str
    amount_minor: int
    reason_code: str

    def validate(self) -> None:
        if not PARSE_ERROR_REF_RE.fullmatch(self.parse_error_ref):
            raise ReconciliationError("PARSE_ERROR_REF_INVALID", "parse-error reference is invalid")
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise ReconciliationError("PARSE_ERROR_AMOUNT_INVALID", "parse-error amount must use integer minor units")
        if not isinstance(self.reason_code, str) or not self.reason_code:
            raise ReconciliationError("PARSE_ERROR_REASON_INVALID", "parse-error item requires a reason code")


@dataclass(frozen=True)
class ConservationItem:
    item_ref: str
    relation_event_ref: Optional[str]
    amount_minor: int
    absolute_amount_minor: int
    disposition: ConservationDisposition
    reason_code: str

    def validate(self) -> None:
        if self.relation_event_ref is None:
            if not PARSE_ERROR_REF_RE.fullmatch(self.item_ref) or self.disposition != ConservationDisposition.PARSE_ERROR:
                raise ReconciliationError("CONSERVATION_ITEM_REF_INVALID", "non-event item must be a parse error")
        elif self.item_ref != self.relation_event_ref or not RELATION_EVENT_REF_RE.fullmatch(self.relation_event_ref):
            raise ReconciliationError("CONSERVATION_ITEM_REF_INVALID", "event conservation reference is invalid")
        if not isinstance(self.disposition, ConservationDisposition):
            raise ReconciliationError("CONSERVATION_DISPOSITION_INVALID", "conservation disposition is invalid")
        if isinstance(self.amount_minor, bool) or not isinstance(self.amount_minor, int):
            raise ReconciliationError("CONSERVATION_AMOUNT_INVALID", "conservation amount must use integer minor units")
        if self.absolute_amount_minor != abs(self.amount_minor):
            raise ReconciliationError("CONSERVATION_ABSOLUTE_INVALID", "absolute amount does not match signed amount")
        if not self.reason_code:
            raise ReconciliationError("CONSERVATION_REASON_MISSING", "conservation item requires an explicit reason")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "item_ref": self.item_ref,
            "relation_event_ref": self.relation_event_ref,
            "amount_minor": self.amount_minor,
            "absolute_amount_minor": self.absolute_amount_minor,
            "disposition": self.disposition.value,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class SourceConservationReport:
    reconciliation_id: str
    items: Tuple[ConservationItem, ...]
    source_control_count: int
    included_count: int
    excluded_count: int
    pending_count: int
    parse_error_count: int
    source_control_amount_minor: int
    included_amount_minor: int
    excluded_amount_minor: int
    pending_amount_minor: int
    parse_error_amount_minor: int
    source_control_absolute_minor: int
    included_absolute_minor: int
    excluded_absolute_minor: int
    pending_absolute_minor: int
    parse_error_absolute_minor: int
    source_conservation_delta_minor: int
    source_conservation_absolute_delta_minor: int
    channel_a_included_amount_minor: int
    channel_b_included_amount_minor: int
    dual_channel_delta_minor: int
    channel_a_included_absolute_minor: int
    channel_b_included_absolute_minor: int
    dual_channel_absolute_delta_minor: int
    conservation_status: str
    execution_status: str
    company_approval_state_managed: bool = False

    def _payload(self) -> Dict[str, Any]:
        return {
            "items": [item.as_dict() for item in self.items],
            "source_control_count": self.source_control_count,
            "included_count": self.included_count,
            "excluded_count": self.excluded_count,
            "pending_count": self.pending_count,
            "parse_error_count": self.parse_error_count,
            "source_control_amount_minor": self.source_control_amount_minor,
            "included_amount_minor": self.included_amount_minor,
            "excluded_amount_minor": self.excluded_amount_minor,
            "pending_amount_minor": self.pending_amount_minor,
            "parse_error_amount_minor": self.parse_error_amount_minor,
            "source_control_absolute_minor": self.source_control_absolute_minor,
            "included_absolute_minor": self.included_absolute_minor,
            "excluded_absolute_minor": self.excluded_absolute_minor,
            "pending_absolute_minor": self.pending_absolute_minor,
            "parse_error_absolute_minor": self.parse_error_absolute_minor,
            "source_conservation_delta_minor": self.source_conservation_delta_minor,
            "source_conservation_absolute_delta_minor": self.source_conservation_absolute_delta_minor,
            "channel_a_included_amount_minor": self.channel_a_included_amount_minor,
            "channel_b_included_amount_minor": self.channel_b_included_amount_minor,
            "dual_channel_delta_minor": self.dual_channel_delta_minor,
            "channel_a_included_absolute_minor": self.channel_a_included_absolute_minor,
            "channel_b_included_absolute_minor": self.channel_b_included_absolute_minor,
            "dual_channel_absolute_delta_minor": self.dual_channel_absolute_delta_minor,
            "conservation_status": self.conservation_status,
            "execution_status": self.execution_status,
        }

    def validate(self) -> None:
        for item in self.items:
            item.validate()
        if tuple(sorted(self.items, key=lambda item: item.item_ref)) != self.items:
            raise ReconciliationError("CONSERVATION_ITEM_ORDER", "conservation items must be sorted")
        if len({item.item_ref for item in self.items}) != len(self.items):
            raise ReconciliationError("CONSERVATION_ITEM_DUPLICATE", "conservation items must be unique")
        counts = {item: 0 for item in ConservationDisposition}
        signed = {item: 0 for item in ConservationDisposition}
        absolute = {item: 0 for item in ConservationDisposition}
        for item in self.items:
            counts[item.disposition] += 1
            signed[item.disposition] += item.amount_minor
            absolute[item.disposition] += item.absolute_amount_minor
        expected_counts = (
            len(self.items),
            counts[ConservationDisposition.INCLUDED],
            counts[ConservationDisposition.EXCLUDED],
            counts[ConservationDisposition.PENDING],
            counts[ConservationDisposition.PARSE_ERROR],
        )
        if expected_counts != (
            self.source_control_count,
            self.included_count,
            self.excluded_count,
            self.pending_count,
            self.parse_error_count,
        ):
            raise ReconciliationError("CONSERVATION_COUNT_INVALID", "conservation counts do not match items")
        if (
            sum(item.amount_minor for item in self.items),
            signed[ConservationDisposition.INCLUDED],
            signed[ConservationDisposition.EXCLUDED],
            signed[ConservationDisposition.PENDING],
            signed[ConservationDisposition.PARSE_ERROR],
        ) != (
            self.source_control_amount_minor,
            self.included_amount_minor,
            self.excluded_amount_minor,
            self.pending_amount_minor,
            self.parse_error_amount_minor,
        ):
            raise ReconciliationError("CONSERVATION_SIGNED_INVALID", "signed conservation totals do not match items")
        if (
            sum(item.absolute_amount_minor for item in self.items),
            absolute[ConservationDisposition.INCLUDED],
            absolute[ConservationDisposition.EXCLUDED],
            absolute[ConservationDisposition.PENDING],
            absolute[ConservationDisposition.PARSE_ERROR],
        ) != (
            self.source_control_absolute_minor,
            self.included_absolute_minor,
            self.excluded_absolute_minor,
            self.pending_absolute_minor,
            self.parse_error_absolute_minor,
        ):
            raise ReconciliationError("CONSERVATION_ABSOLUTE_INVALID", "absolute conservation totals do not match items")
        expected_signed_delta = (
            self.source_control_amount_minor
            - self.included_amount_minor
            - self.excluded_amount_minor
            - self.pending_amount_minor
            - self.parse_error_amount_minor
        )
        expected_absolute_delta = (
            self.source_control_absolute_minor
            - self.included_absolute_minor
            - self.excluded_absolute_minor
            - self.pending_absolute_minor
            - self.parse_error_absolute_minor
        )
        if (expected_signed_delta, expected_absolute_delta) != (
            self.source_conservation_delta_minor,
            self.source_conservation_absolute_delta_minor,
        ):
            raise ReconciliationError("CONSERVATION_DELTA_INVALID", "source conservation deltas are inconsistent")
        if self.dual_channel_delta_minor != self.channel_a_included_amount_minor - self.channel_b_included_amount_minor:
            raise ReconciliationError("DUAL_CHANNEL_DELTA_INVALID", "signed dual-channel delta is inconsistent")
        if self.dual_channel_absolute_delta_minor != (
            self.channel_a_included_absolute_minor - self.channel_b_included_absolute_minor
        ):
            raise ReconciliationError("DUAL_CHANNEL_DELTA_INVALID", "absolute dual-channel delta is inconsistent")
        expected_conservation = (
            "PASS"
            if self.source_conservation_delta_minor == 0
            and self.source_conservation_absolute_delta_minor == 0
            and self.dual_channel_delta_minor == 0
            and self.dual_channel_absolute_delta_minor == 0
            else "ERROR"
        )
        if self.conservation_status != expected_conservation:
            raise ReconciliationError("CONSERVATION_STATUS_INVALID", "conservation status conflicts with deltas")
        expected_execution = (
            "PASS"
            if expected_conservation == "PASS" and self.pending_count == 0 and self.parse_error_count == 0
            else "BLOCKED"
            if expected_conservation == "PASS"
            else "ERROR"
        )
        if self.execution_status != expected_execution:
            raise ReconciliationError("CONSERVATION_STATUS_INVALID", "execution status conflicts with pending/error pools")
        if self.company_approval_state_managed is not False:
            raise ReconciliationError("RECONCILIATION_AUTHORITY", "R7 cannot manage company approval state")
        expected_id = "reconciliation_" + _digest({**self._payload(), "reconciliation_id": None})[:32]
        if self.reconciliation_id != expected_id:
            raise ReconciliationError("RECONCILIATION_TAMPERED", "reconciliation ID does not bind its content")

    @property
    def formal_ready(self) -> bool:
        return False

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.source_conservation.v1",
            "reconciliation_id": self.reconciliation_id,
            **self._payload(),
            "metric_inclusion_status": "NOT_EVALUATED_R7",
            "company_approval_state_managed": False,
        }

    def as_public_summary(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.source_conservation_public_summary.v1",
            "source_control_count": self.source_control_count,
            "included_count": self.included_count,
            "excluded_count": self.excluded_count,
            "pending_count": self.pending_count,
            "parse_error_count": self.parse_error_count,
            "source_control_amount_minor": self.source_control_amount_minor,
            "included_amount_minor": self.included_amount_minor,
            "excluded_amount_minor": self.excluded_amount_minor,
            "pending_amount_minor": self.pending_amount_minor,
            "parse_error_amount_minor": self.parse_error_amount_minor,
            "source_conservation_delta_minor": self.source_conservation_delta_minor,
            "source_conservation_absolute_delta_minor": self.source_conservation_absolute_delta_minor,
            "dual_channel_delta_minor": self.dual_channel_delta_minor,
            "dual_channel_absolute_delta_minor": self.dual_channel_absolute_delta_minor,
            "conservation_status": self.conservation_status,
            "execution_status": self.execution_status,
            "formal_ready": False,
        }


def _disposition_for_event(event: RelationEvent, dedup_disposition: DedupDisposition) -> Tuple[ConservationDisposition, str]:
    if dedup_disposition in {DedupDisposition.EXCLUDED_DUPLICATE, DedupDisposition.SUPERSEDED_VERSION}:
        return ConservationDisposition.EXCLUDED, dedup_disposition.value
    if dedup_disposition.value.startswith("PENDING_"):
        return ConservationDisposition.PENDING, dedup_disposition.value
    if event.event_status == SourceEventStatus.SOURCE_CANCELLED:
        return ConservationDisposition.EXCLUDED, "SOURCE_CANCELLED"
    if event.event_status == SourceEventStatus.SOURCE_PENDING:
        return ConservationDisposition.PENDING, "SOURCE_PENDING"
    return ConservationDisposition.INCLUDED, "ACTIVE_OR_EVIDENCED_REVERSAL"


def build_source_conservation(
    events: Sequence[RelationEvent],
    *,
    dedup_result: DedupResult,
    parse_errors: Sequence[ParseErrorAmount] = (),
    disposition_overrides: Optional[Mapping[str, ConservationDisposition]] = None,
) -> SourceConservationReport:
    """Reconcile source control. Channel A sums included rows; Channel B subtracts all other pools."""

    ordered_events = tuple(sorted(events, key=lambda item: item.relation_event_ref))
    for event in ordered_events:
        event.validate()
    decision_by_ref = {item.relation_event_ref: item for item in dedup_result.decisions}
    if set(decision_by_ref) != {item.relation_event_ref for item in ordered_events}:
        raise ReconciliationError("DEDUP_COVERAGE_MISMATCH", "dedup result must cover every relation event exactly once")
    overrides = dict(disposition_overrides or {})
    if not set(overrides).issubset(decision_by_ref):
        raise ReconciliationError("CONSERVATION_OVERRIDE_UNKNOWN", "disposition override references an unknown event")

    items = []
    for event in ordered_events:
        disposition, reason = _disposition_for_event(event, decision_by_ref[event.relation_event_ref].disposition)
        if event.relation_event_ref in overrides:
            disposition = overrides[event.relation_event_ref]
            if disposition == ConservationDisposition.PARSE_ERROR:
                raise ReconciliationError("CONSERVATION_OVERRIDE_INVALID", "an emitted event cannot become a parse error")
            reason = "EXPLICIT_R7_DISPOSITION_OVERRIDE"
        items.append(
            ConservationItem(
                item_ref=event.relation_event_ref,
                relation_event_ref=event.relation_event_ref,
                amount_minor=event.base_amount_minor,
                absolute_amount_minor=abs(event.base_amount_minor),
                disposition=disposition,
                reason_code=reason,
            )
        )
    for error in parse_errors:
        error.validate()
        items.append(
            ConservationItem(
                item_ref=error.parse_error_ref,
                relation_event_ref=None,
                amount_minor=error.amount_minor,
                absolute_amount_minor=abs(error.amount_minor),
                disposition=ConservationDisposition.PARSE_ERROR,
                reason_code=error.reason_code,
            )
        )
    ordered_items = tuple(sorted(items, key=lambda item: item.item_ref))
    if len({item.item_ref for item in ordered_items}) != len(ordered_items):
        raise ReconciliationError("CONSERVATION_ITEM_DUPLICATE", "source and parse-error references must be unique")

    # Channel A: direct included-row iteration. It intentionally does not use source-control subtraction.
    channel_a_signed = 0
    channel_a_absolute = 0
    for item in ordered_items:
        if item.disposition == ConservationDisposition.INCLUDED:
            channel_a_signed += item.amount_minor
            channel_a_absolute += item.absolute_amount_minor

    # Channel B: an independent control-minus-nonincluded implementation with separate accumulators.
    control_b_signed = 0
    excluded_b_signed = 0
    pending_b_signed = 0
    error_b_signed = 0
    control_b_absolute = 0
    excluded_b_absolute = 0
    pending_b_absolute = 0
    error_b_absolute = 0
    for item in ordered_items:
        control_b_signed += item.amount_minor
        control_b_absolute += item.absolute_amount_minor
        if item.disposition == ConservationDisposition.EXCLUDED:
            excluded_b_signed += item.amount_minor
            excluded_b_absolute += item.absolute_amount_minor
        elif item.disposition == ConservationDisposition.PENDING:
            pending_b_signed += item.amount_minor
            pending_b_absolute += item.absolute_amount_minor
        elif item.disposition == ConservationDisposition.PARSE_ERROR:
            error_b_signed += item.amount_minor
            error_b_absolute += item.absolute_amount_minor
    channel_b_signed = control_b_signed - excluded_b_signed - pending_b_signed - error_b_signed
    channel_b_absolute = control_b_absolute - excluded_b_absolute - pending_b_absolute - error_b_absolute

    counts = {item: 0 for item in ConservationDisposition}
    signed = {item: 0 for item in ConservationDisposition}
    absolute = {item: 0 for item in ConservationDisposition}
    for item in ordered_items:
        counts[item.disposition] += 1
        signed[item.disposition] += item.amount_minor
        absolute[item.disposition] += item.absolute_amount_minor
    control_signed = sum(item.amount_minor for item in ordered_items)
    control_absolute = sum(item.absolute_amount_minor for item in ordered_items)
    conservation_signed_delta = control_signed - sum(signed.values())
    conservation_absolute_delta = control_absolute - sum(absolute.values())
    dual_signed_delta = channel_a_signed - channel_b_signed
    dual_absolute_delta = channel_a_absolute - channel_b_absolute
    conservation_status = (
        "PASS"
        if conservation_signed_delta == conservation_absolute_delta == dual_signed_delta == dual_absolute_delta == 0
        else "ERROR"
    )
    execution_status = (
        "PASS"
        if conservation_status == "PASS"
        and counts[ConservationDisposition.PENDING] == 0
        and counts[ConservationDisposition.PARSE_ERROR] == 0
        else "BLOCKED"
        if conservation_status == "PASS"
        else "ERROR"
    )
    provisional = SourceConservationReport(
        reconciliation_id="reconciliation_" + "0" * 32,
        items=ordered_items,
        source_control_count=len(ordered_items),
        included_count=counts[ConservationDisposition.INCLUDED],
        excluded_count=counts[ConservationDisposition.EXCLUDED],
        pending_count=counts[ConservationDisposition.PENDING],
        parse_error_count=counts[ConservationDisposition.PARSE_ERROR],
        source_control_amount_minor=control_signed,
        included_amount_minor=signed[ConservationDisposition.INCLUDED],
        excluded_amount_minor=signed[ConservationDisposition.EXCLUDED],
        pending_amount_minor=signed[ConservationDisposition.PENDING],
        parse_error_amount_minor=signed[ConservationDisposition.PARSE_ERROR],
        source_control_absolute_minor=control_absolute,
        included_absolute_minor=absolute[ConservationDisposition.INCLUDED],
        excluded_absolute_minor=absolute[ConservationDisposition.EXCLUDED],
        pending_absolute_minor=absolute[ConservationDisposition.PENDING],
        parse_error_absolute_minor=absolute[ConservationDisposition.PARSE_ERROR],
        source_conservation_delta_minor=conservation_signed_delta,
        source_conservation_absolute_delta_minor=conservation_absolute_delta,
        channel_a_included_amount_minor=channel_a_signed,
        channel_b_included_amount_minor=channel_b_signed,
        dual_channel_delta_minor=dual_signed_delta,
        channel_a_included_absolute_minor=channel_a_absolute,
        channel_b_included_absolute_minor=channel_b_absolute,
        dual_channel_absolute_delta_minor=dual_absolute_delta,
        conservation_status=conservation_status,
        execution_status=execution_status,
    )
    result = SourceConservationReport(
        **{
            **provisional.__dict__,
            "reconciliation_id": "reconciliation_"
            + _digest({**provisional._payload(), "reconciliation_id": None})[:32],
        }
    )
    result.validate()
    return result


@dataclass(frozen=True)
class R7ReconciliationResult:
    status: str
    source_conservation: SourceConservationReport
    event_links: LinkSetResult
    stop_reasons: Tuple[str, ...]
    company_approval_state_managed: bool = False

    @property
    def formal_ready(self) -> bool:
        return False

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.r7_reconciliation.v1",
            "status": self.status,
            "source_conservation": self.source_conservation.as_private_dict(),
            "event_links": self.event_links.as_private_dict(),
            "stop_reasons": list(self.stop_reasons),
            "metric_inclusion_status": "NOT_EVALUATED_R7",
            "company_approval_state_managed": False,
        }

    def as_public_summary(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.r7_reconciliation_public_summary.v1",
            "status": self.status,
            "source_conservation": self.source_conservation.as_public_summary(),
            "event_links": self.event_links.as_public_summary(),
            "stop_reasons": list(self.stop_reasons),
            "formal_ready": False,
        }


def combine_r7_reconciliation(
    source_conservation: SourceConservationReport,
    event_links: LinkSetResult,
) -> R7ReconciliationResult:
    source_conservation.validate()
    reasons = []
    if source_conservation.execution_status != "PASS":
        reasons.append("SOURCE_CONSERVATION_%s" % source_conservation.execution_status)
    reasons.extend(event_links.conflict_codes)
    return R7ReconciliationResult(
        status="PASS_R7_CONTROLS" if not reasons else "BLOCKED_R7_CONTROLS",
        source_conservation=source_conservation,
        event_links=event_links,
        stop_reasons=tuple(sorted(set(reasons))),
    )
