"""Immutable R6 economic-event candidates with explicit lifecycle semantics."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional, Tuple


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVENT_ID_RE = re.compile(r"^evt_[0-9a-f]{32}$")
EVENT_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
SOURCE_KEY_RE = re.compile(r"^lifecycle_line_[0-9a-f]{32}$")
SOURCE_RECORD_RE = re.compile(r"^rec_lifecycle_[0-9a-f]{32}$")
RULE_REF_RE = re.compile(r"^rule_[0-9a-f]{32}$")
MAX_MINOR = 9_223_372_036_854_775_807
RELATION_EVENT_REF_RE = re.compile(r"^relation_event_[0-9a-f]{32}$")
RELATION_SOURCE_KEY_RE = re.compile(r"^(?:lifecycle_line|ledger_line|event_line)_[0-9a-f]{32}$")
RELATION_SOURCE_RECORD_RE = re.compile(r"^(?:rec_lifecycle|rec_source|rec_source_record)_[0-9a-f]{32}$")
RELATION_KEY_RE = re.compile(r"^relation_key_[0-9a-f]{32}$")
IDENTITY_RECORD_RE = re.compile(r"^identity_record_[0-9a-f]{32}$")
IDENTITY_RESOLUTION_RE = re.compile(r"^identity_resolution_[0-9a-f]{32}$")
EVIDENCE_REF_RE = re.compile(r"^(?:evidence:[0-9a-f]{64}|evidence://sha256/[0-9a-f]{64})$")
SOURCE_SYSTEM_RE = re.compile(r"^[a-z][a-z0-9_.-]{1,63}$")


def _digest(value: Any) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


class EventDirection(str, Enum):
    COST = "COST"
    REVENUE = "REVENUE"
    CASH_OUT = "CASH_OUT"
    CASH_IN = "CASH_IN"


class LifecycleStage(str, Enum):
    BUDGET = "BUDGET"
    COMMITMENT = "COMMITMENT"
    ACCRUAL = "ACCRUAL"
    POSTED_ACTUAL = "POSTED_ACTUAL"
    PAID = "PAID"
    FORECAST = "FORECAST"
    CONTRACT_VALUE = "CONTRACT_VALUE"
    BILLED = "BILLED"
    RECOGNIZED_REVENUE = "RECOGNIZED_REVENUE"
    COLLECTED = "COLLECTED"


class SourceEventStatus(str, Enum):
    SOURCE_ACTIVE = "SOURCE_ACTIVE"
    SOURCE_PENDING = "SOURCE_PENDING"
    SOURCE_CANCELLED = "SOURCE_CANCELLED"
    SOURCE_REVERSED = "SOURCE_REVERSED"


class RelationIdentityStatus(str, Enum):
    VALIDATED_IDENTITY = "VALIDATED_IDENTITY"
    ALLOCATION_REQUIRED = "ALLOCATION_REQUIRED"


ALLOWED_STAGE_BY_DIRECTION = {
    EventDirection.COST: frozenset(
        {
            LifecycleStage.BUDGET,
            LifecycleStage.COMMITMENT,
            LifecycleStage.ACCRUAL,
            LifecycleStage.POSTED_ACTUAL,
            LifecycleStage.FORECAST,
        }
    ),
    EventDirection.REVENUE: frozenset(
        {
            LifecycleStage.CONTRACT_VALUE,
            LifecycleStage.BILLED,
            LifecycleStage.RECOGNIZED_REVENUE,
        }
    ),
    EventDirection.CASH_OUT: frozenset({LifecycleStage.PAID}),
    EventDirection.CASH_IN: frozenset({LifecycleStage.COLLECTED}),
}


class EconomicEventError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class EconomicEventCandidate:
    """Candidate only: it has no final Metric inclusion or company approval meaning."""

    economic_event_id: str
    export_business_fingerprint: str
    source_business_key_hash: str
    source_business_digest: str
    mapping_rule_ref: str
    profile_sha256: str
    event_type: str
    direction: EventDirection
    lifecycle_stage: LifecycleStage
    event_status: SourceEventStatus
    legal_entity_source_key: Optional[str]
    project_source_key: Optional[str]
    wbs_source_key: Optional[str]
    contract_source_key: Optional[str]
    counterparty_source_key: Optional[str]
    document_id: Optional[str]
    document_line_id: Optional[str]
    document_date: Optional[str]
    approval_date: Optional[str]
    invoice_date: Optional[str]
    payment_date: Optional[str]
    collection_date: Optional[str]
    effective_date: Optional[str]
    reversal_date: Optional[str]
    transaction_amount_minor: int
    gross_amount_minor: Optional[int]
    net_amount_minor: Optional[int]
    tax_amount_minor: Optional[int]
    transaction_currency: str
    tax_recoverability: str
    source_arithmetic_status: str
    source_arithmetic_delta_minor: Optional[int]
    reversal_of_source_key: Optional[str]
    free_text_candidate_present: bool
    identity_status: str
    metric_inclusion_status: str
    source_record_refs: Tuple[str, ...]

    def _id_payload(self) -> Dict[str, Any]:
        return {
            "export_business_fingerprint": self.export_business_fingerprint,
            "source_business_key_hash": self.source_business_key_hash,
            "source_business_digest": self.source_business_digest,
            "mapping_rule_ref": self.mapping_rule_ref,
            "event_type": self.event_type,
            "direction": self.direction.value,
            "lifecycle_stage": self.lifecycle_stage.value,
            "event_status": self.event_status.value,
            "transaction_amount_minor": self.transaction_amount_minor,
        }

    def validate(self) -> None:
        if (
            not EVENT_ID_RE.fullmatch(self.economic_event_id)
            or not SHA256_RE.fullmatch(self.export_business_fingerprint)
            or not SOURCE_KEY_RE.fullmatch(self.source_business_key_hash)
            or not SHA256_RE.fullmatch(self.source_business_digest)
            or not RULE_REF_RE.fullmatch(self.mapping_rule_ref)
            or not SHA256_RE.fullmatch(self.profile_sha256)
            or not EVENT_TYPE_RE.fullmatch(self.event_type)
        ):
            raise EconomicEventError("EVENT_LINEAGE_INVALID", "event lineage identifiers are invalid")
        if not isinstance(self.direction, EventDirection) or not isinstance(self.lifecycle_stage, LifecycleStage):
            raise EconomicEventError("EVENT_LIFECYCLE_INVALID", "event direction and lifecycle require explicit enums")
        if self.lifecycle_stage not in ALLOWED_STAGE_BY_DIRECTION[self.direction]:
            raise EconomicEventError("EVENT_LIFECYCLE_CONFLICT", "event lifecycle is incompatible with its direction")
        if not isinstance(self.event_status, SourceEventStatus):
            raise EconomicEventError("EVENT_STATUS_INVALID", "source event status is not registered")
        if self.transaction_currency != "CNY" or self.tax_recoverability != "UNKNOWN":
            raise EconomicEventError("EVENT_CURRENCY_OR_TAX_SCOPE", "R6 supports CNY candidates with unknown recoverability only")
        for value in (
            self.transaction_amount_minor,
            self.gross_amount_minor,
            self.net_amount_minor,
            self.tax_amount_minor,
            self.source_arithmetic_delta_minor,
        ):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_MINOR):
                raise EconomicEventError("EVENT_AMOUNT_INVALID", "event amounts require signed 64-bit integer minor units")
        for value in (
            self.document_date,
            self.approval_date,
            self.invoice_date,
            self.payment_date,
            self.collection_date,
            self.effective_date,
            self.reversal_date,
        ):
            if value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError) as exc:
                    raise EconomicEventError("EVENT_DATE_INVALID", "event date is not canonical ISO") from exc
        if self.source_arithmetic_status not in {
            "BALANCED",
            "SOURCE_ARITHMETIC_DELTA",
            "INCOMPLETE",
            "NOT_APPLICABLE",
        }:
            raise EconomicEventError("EVENT_SOURCE_ARITHMETIC_INVALID", "source arithmetic status is not registered")
        if self.source_arithmetic_status in {"BALANCED", "SOURCE_ARITHMETIC_DELTA"}:
            if self.source_arithmetic_delta_minor is None:
                raise EconomicEventError("EVENT_SOURCE_ARITHMETIC_INVALID", "source arithmetic status requires a delta")
            if self.source_arithmetic_status == "BALANCED" and self.source_arithmetic_delta_minor != 0:
                raise EconomicEventError("EVENT_SOURCE_ARITHMETIC_INVALID", "balanced source arithmetic requires zero delta")
            if self.source_arithmetic_status == "SOURCE_ARITHMETIC_DELTA" and self.source_arithmetic_delta_minor == 0:
                raise EconomicEventError("EVENT_SOURCE_ARITHMETIC_INVALID", "source arithmetic anomaly requires nonzero delta")
        elif self.source_arithmetic_delta_minor is not None:
            raise EconomicEventError("EVENT_SOURCE_ARITHMETIC_INVALID", "non-applicable source arithmetic cannot carry a delta")
        required_date_by_stage = {
            LifecycleStage.BILLED: self.invoice_date,
            LifecycleStage.PAID: self.payment_date,
            LifecycleStage.COLLECTED: self.collection_date,
        }
        if self.lifecycle_stage in required_date_by_stage and required_date_by_stage[self.lifecycle_stage] is None:
            raise EconomicEventError("EVENT_STAGE_DATE_MISSING", "lifecycle candidate lacks its governed stage date")
        if self.lifecycle_stage == LifecycleStage.CONTRACT_VALUE and self.approval_date is None and self.effective_date is None:
            raise EconomicEventError("EVENT_STAGE_DATE_MISSING", "contract-value candidate needs approval or effective date")
        if self.event_status == SourceEventStatus.SOURCE_REVERSED and (
            self.reversal_of_source_key is None or self.reversal_date is None
        ):
            raise EconomicEventError(
                "EVENT_REVERSAL_LINEAGE_MISSING",
                "reversed source event requires original-source key and reversal date",
            )
        if type(self.free_text_candidate_present) is not bool:
            raise EconomicEventError("EVENT_FREE_TEXT_FLAG_INVALID", "free-text candidate flag must be boolean")
        if self.identity_status != "PENDING_IDENTITY" or self.metric_inclusion_status != "NOT_EVALUATED_R6":
            raise EconomicEventError(
                "EVENT_AUTHORITY_ESCALATION",
                "R6 candidates cannot claim resolved identity or final Metric inclusion",
            )
        if (
            not isinstance(self.source_record_refs, tuple)
            or not self.source_record_refs
            or tuple(sorted(set(self.source_record_refs))) != self.source_record_refs
            or any(not SOURCE_RECORD_RE.fullmatch(item) for item in self.source_record_refs)
        ):
            raise EconomicEventError("EVENT_SOURCE_REFS_INVALID", "event source references must be unique sorted R6 records")
        expected_id = "evt_" + _digest(self._id_payload())[:32]
        if self.economic_event_id != expected_id:
            raise EconomicEventError("EVENT_TAMPERED", "event ID no longer matches its immutable business payload")

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.economic_event_candidate.v1",
            "economic_event_id": self.economic_event_id,
            "export_business_fingerprint": self.export_business_fingerprint,
            "source_business_key_hash": self.source_business_key_hash,
            "source_business_digest": self.source_business_digest,
            "mapping_rule_ref": self.mapping_rule_ref,
            "profile_sha256": self.profile_sha256,
            "event_type": self.event_type,
            "direction": self.direction.value,
            "lifecycle_stage": self.lifecycle_stage.value,
            "event_status": self.event_status.value,
            "legal_entity_source_key": self.legal_entity_source_key,
            "project_source_key": self.project_source_key,
            "wbs_source_key": self.wbs_source_key,
            "contract_source_key": self.contract_source_key,
            "counterparty_source_key": self.counterparty_source_key,
            "document_id": self.document_id,
            "document_line_id": self.document_line_id,
            "document_date": self.document_date,
            "approval_date": self.approval_date,
            "invoice_date": self.invoice_date,
            "payment_date": self.payment_date,
            "collection_date": self.collection_date,
            "effective_date": self.effective_date,
            "reversal_date": self.reversal_date,
            "transaction_amount_minor": self.transaction_amount_minor,
            "gross_amount_minor": self.gross_amount_minor,
            "net_amount_minor": self.net_amount_minor,
            "tax_amount_minor": self.tax_amount_minor,
            "transaction_currency": self.transaction_currency,
            "tax_recoverability": self.tax_recoverability,
            "source_arithmetic_status": self.source_arithmetic_status,
            "source_arithmetic_delta_minor": self.source_arithmetic_delta_minor,
            "reversal_of_source_key": self.reversal_of_source_key,
            "free_text_candidate_present": self.free_text_candidate_present,
            "identity_status": self.identity_status,
            "metric_inclusion_status": self.metric_inclusion_status,
            "source_record_refs": list(self.source_record_refs),
        }


def event_id_for_payload(payload: Dict[str, Any]) -> str:
    """Create the candidate ID from the exact payload used by validation."""

    return "evt_" + _digest(payload)[:32]


def _strict_relation_text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or value != value.strip() or "\x00" in value or "\r" in value or "\n" in value:
        raise EconomicEventError("RELATION_EVENT_FIELD_INVALID", "%s must be canonical nonempty text" % field)
    return value


@dataclass(frozen=True)
class EventIdentityBinding:
    """R7 relation identity; this is data lineage, never company approval state."""

    economic_event_id: str
    identity_status: RelationIdentityStatus
    legal_entity_id: str
    canonical_project_id: Optional[str]
    wbs_or_cost_code: Optional[str]
    canonical_contract_id: Optional[str]
    identity_record_ref: Optional[str]
    mapping_resolution_ref: Optional[str]
    evidence_refs: Tuple[str, ...]
    company_approval_state_managed: bool = False

    def validate(self) -> None:
        if not EVENT_ID_RE.fullmatch(self.economic_event_id):
            raise EconomicEventError("RELATION_IDENTITY_EVENT_INVALID", "identity binding event ID is invalid")
        if not isinstance(self.identity_status, RelationIdentityStatus):
            raise EconomicEventError("RELATION_IDENTITY_STATUS_INVALID", "relation identity status is not registered")
        _strict_relation_text(self.legal_entity_id, "legal_entity_id")
        for field in ("canonical_project_id", "wbs_or_cost_code", "canonical_contract_id"):
            _strict_relation_text(getattr(self, field), field, optional=True)
        if (
            not isinstance(self.evidence_refs, tuple)
            or not self.evidence_refs
            or tuple(sorted(set(self.evidence_refs))) != self.evidence_refs
            or any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs)
        ):
            raise EconomicEventError("RELATION_IDENTITY_EVIDENCE_INVALID", "relation identity requires unique hash-bound evidence")
        if self.company_approval_state_managed is not False:
            raise EconomicEventError("RELATION_IDENTITY_AUTHORITY", "R7 cannot manage company approval state")
        if self.identity_status == RelationIdentityStatus.VALIDATED_IDENTITY:
            if any(
                item is None
                for item in (
                    self.canonical_project_id,
                    self.wbs_or_cost_code,
                    self.canonical_contract_id,
                    self.identity_record_ref,
                    self.mapping_resolution_ref,
                )
            ):
                raise EconomicEventError("RELATION_IDENTITY_INCOMPLETE", "validated relation identity requires full canonical scope")
            if not IDENTITY_RECORD_RE.fullmatch(self.identity_record_ref or "") or not IDENTITY_RESOLUTION_RE.fullmatch(
                self.mapping_resolution_ref or ""
            ):
                raise EconomicEventError("RELATION_IDENTITY_LINEAGE_INVALID", "validated relation identity refs are invalid")
        else:
            if any(
                item is not None
                for item in (
                    self.canonical_project_id,
                    self.wbs_or_cost_code,
                    self.canonical_contract_id,
                    self.identity_record_ref,
                    self.mapping_resolution_ref,
                )
            ):
                raise EconomicEventError(
                    "RELATION_IDENTITY_AMBIGUOUS_PARTIAL",
                    "allocation-required identity cannot carry a partly asserted canonical scope",
                )

    @property
    def scope_key(self) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
        self.validate()
        return (
            self.canonical_project_id,
            self.wbs_or_cost_code,
            self.canonical_contract_id,
            self.legal_entity_id,
        )

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "economic_event_id": self.economic_event_id,
            "identity_status": self.identity_status.value,
            "legal_entity_id": self.legal_entity_id,
            "canonical_project_id": self.canonical_project_id,
            "wbs_or_cost_code": self.wbs_or_cost_code,
            "canonical_contract_id": self.canonical_contract_id,
            "identity_record_ref": self.identity_record_ref,
            "mapping_resolution_ref": self.mapping_resolution_ref,
            "evidence_refs": list(self.evidence_refs),
            "company_approval_state_managed": False,
        }


@dataclass(frozen=True)
class RelationEvent:
    """R7 linkable event view binding an immutable event to governed identity evidence."""

    relation_event_ref: str
    economic_event_id: str
    source_system_id: str
    source_artifact_sha256: str
    source_business_key_hash: str
    source_business_digest: str
    event_type: str
    direction: EventDirection
    lifecycle_stage: LifecycleStage
    event_status: SourceEventStatus
    identity_binding: EventIdentityBinding
    counterparty_key: Optional[str]
    document_id: Optional[str]
    document_line_id: Optional[str]
    event_date: str
    base_amount_minor: int
    base_currency: str
    reversal_of_event_id: Optional[str]
    governed_relation_keys: Tuple[str, ...]
    source_record_refs: Tuple[str, ...]
    metric_inclusion_status: str = "NOT_EVALUATED_R7"

    def _relation_payload(self) -> Dict[str, Any]:
        return {
            "economic_event_id": self.economic_event_id,
            "source_system_id": self.source_system_id,
            "source_artifact_sha256": self.source_artifact_sha256,
            "source_business_key_hash": self.source_business_key_hash,
            "source_business_digest": self.source_business_digest,
            "event_type": self.event_type,
            "direction": self.direction.value,
            "lifecycle_stage": self.lifecycle_stage.value,
            "event_status": self.event_status.value,
            "identity_binding": self.identity_binding.as_private_dict(),
            "counterparty_key": self.counterparty_key,
            "document_id": self.document_id,
            "document_line_id": self.document_line_id,
            "event_date": self.event_date,
            "base_amount_minor": self.base_amount_minor,
            "base_currency": self.base_currency,
            "reversal_of_event_id": self.reversal_of_event_id,
            "governed_relation_keys": list(self.governed_relation_keys),
            "source_record_refs": list(self.source_record_refs),
            "metric_inclusion_status": self.metric_inclusion_status,
        }

    @property
    def business_content_fingerprint(self) -> str:
        self.validate()
        return _digest(
            {
                "event_type": self.event_type,
                "direction": self.direction.value,
                "lifecycle_stage": self.lifecycle_stage.value,
                "event_status": self.event_status.value,
                "scope": self.identity_binding.scope_key,
                "counterparty_key": self.counterparty_key,
                "document_id": self.document_id,
                "document_line_id": self.document_line_id,
                "event_date": self.event_date,
                "base_amount_minor": self.base_amount_minor,
                "base_currency": self.base_currency,
                "reversal_of_event_id": self.reversal_of_event_id,
            }
        )

    @property
    def partition_key(self) -> Tuple[Any, ...]:
        self.validate()
        return (
            self.identity_binding.legal_entity_id,
            self.identity_binding.canonical_project_id,
            self.identity_binding.wbs_or_cost_code,
            self.identity_binding.canonical_contract_id,
            self.direction.value,
            self.lifecycle_stage.value,
        )

    def validate(self) -> None:
        self.identity_binding.validate()
        if self.identity_binding.economic_event_id != self.economic_event_id:
            raise EconomicEventError("RELATION_EVENT_IDENTITY_MISMATCH", "identity binding points to another event")
        if (
            not RELATION_EVENT_REF_RE.fullmatch(self.relation_event_ref)
            or not EVENT_ID_RE.fullmatch(self.economic_event_id)
            or not SOURCE_SYSTEM_RE.fullmatch(self.source_system_id)
            or not SHA256_RE.fullmatch(self.source_artifact_sha256)
            or not RELATION_SOURCE_KEY_RE.fullmatch(self.source_business_key_hash)
            or not SHA256_RE.fullmatch(self.source_business_digest)
            or not EVENT_TYPE_RE.fullmatch(self.event_type)
        ):
            raise EconomicEventError("RELATION_EVENT_LINEAGE_INVALID", "relation event lineage is invalid")
        if not isinstance(self.direction, EventDirection) or not isinstance(self.lifecycle_stage, LifecycleStage):
            raise EconomicEventError("RELATION_EVENT_LIFECYCLE_INVALID", "relation event lifecycle enums are invalid")
        if self.lifecycle_stage not in ALLOWED_STAGE_BY_DIRECTION[self.direction]:
            raise EconomicEventError("RELATION_EVENT_LIFECYCLE_CONFLICT", "relation event direction and stage conflict")
        if not isinstance(self.event_status, SourceEventStatus):
            raise EconomicEventError("RELATION_EVENT_STATUS_INVALID", "relation event source status is invalid")
        for field in ("counterparty_key", "document_id", "document_line_id"):
            _strict_relation_text(getattr(self, field), field, optional=True)
        try:
            date.fromisoformat(self.event_date)
        except (TypeError, ValueError) as exc:
            raise EconomicEventError("RELATION_EVENT_DATE_INVALID", "relation event date must be canonical ISO") from exc
        if isinstance(self.base_amount_minor, bool) or not isinstance(self.base_amount_minor, int) or abs(self.base_amount_minor) > MAX_MINOR:
            raise EconomicEventError("RELATION_EVENT_AMOUNT_INVALID", "relation event amount must be signed 64-bit minor units")
        if self.base_currency != "CNY":
            raise EconomicEventError("RELATION_EVENT_CURRENCY_INVALID", "R7 relation events are CNY only")
        if self.reversal_of_event_id is not None and not EVENT_ID_RE.fullmatch(self.reversal_of_event_id):
            raise EconomicEventError("RELATION_EVENT_REVERSAL_INVALID", "reversal event reference is invalid")
        if self.event_status == SourceEventStatus.SOURCE_REVERSED and self.reversal_of_event_id is None:
            raise EconomicEventError("RELATION_EVENT_REVERSAL_REQUIRED", "reversed relation event requires its original event ID")
        if (
            not isinstance(self.governed_relation_keys, tuple)
            or tuple(sorted(set(self.governed_relation_keys))) != self.governed_relation_keys
            or any(not RELATION_KEY_RE.fullmatch(item) for item in self.governed_relation_keys)
        ):
            raise EconomicEventError("RELATION_EVENT_KEYS_INVALID", "governed relation keys must be unique opaque hashes")
        if (
            not isinstance(self.source_record_refs, tuple)
            or not self.source_record_refs
            or tuple(sorted(set(self.source_record_refs))) != self.source_record_refs
            or any(not RELATION_SOURCE_RECORD_RE.fullmatch(item) for item in self.source_record_refs)
        ):
            raise EconomicEventError("RELATION_EVENT_SOURCE_REFS_INVALID", "relation event source refs are invalid")
        if self.metric_inclusion_status != "NOT_EVALUATED_R7":
            raise EconomicEventError("RELATION_EVENT_AUTHORITY_ESCALATION", "R7 cannot decide final Metric inclusion")
        expected_ref = "relation_event_" + _digest({**self._relation_payload(), "relation_event_ref": None})[:32]
        if self.relation_event_ref != expected_ref:
            raise EconomicEventError("RELATION_EVENT_TAMPERED", "relation event no longer matches its content binding")

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.relation_event.v1",
            "relation_event_ref": self.relation_event_ref,
            **self._relation_payload(),
            "business_content_fingerprint": self.business_content_fingerprint,
        }


def relation_event_id_for_source(
    *,
    source_system_id: str,
    source_artifact_sha256: str,
    source_business_key_hash: str,
    source_business_digest: str,
    event_type: str,
    direction: EventDirection,
    lifecycle_stage: LifecycleStage,
    base_amount_minor: int,
    source_record_refs: Tuple[str, ...],
) -> str:
    """Return the stable R7 event ID before an identity binding is constructed."""

    return event_id_for_payload(
        {
            "source_system_id": source_system_id,
            "source_artifact_sha256": source_artifact_sha256,
            "source_business_key_hash": source_business_key_hash,
            "source_business_digest": source_business_digest,
            "event_type": event_type,
            "direction": direction.value,
            "lifecycle_stage": lifecycle_stage.value,
            "base_amount_minor": base_amount_minor,
            "source_record_refs": list(source_record_refs),
        }
    )


def create_relation_event(
    *,
    source_system_id: str,
    source_artifact_sha256: str,
    source_business_key_hash: str,
    source_business_digest: str,
    event_type: str,
    direction: EventDirection,
    lifecycle_stage: LifecycleStage,
    event_status: SourceEventStatus,
    identity_binding: EventIdentityBinding,
    counterparty_key: Optional[str],
    document_id: Optional[str],
    document_line_id: Optional[str],
    event_date: str,
    base_amount_minor: int,
    reversal_of_event_id: Optional[str],
    governed_relation_keys: Tuple[str, ...],
    source_record_refs: Tuple[str, ...],
    economic_event_id: Optional[str] = None,
) -> RelationEvent:
    """Create a tamper-evident R7 relation view; no relation or Metric inclusion is inferred."""

    if economic_event_id is None:
        economic_event_id = relation_event_id_for_source(
            source_system_id=source_system_id,
            source_artifact_sha256=source_artifact_sha256,
            source_business_key_hash=source_business_key_hash,
            source_business_digest=source_business_digest,
            event_type=event_type,
            direction=direction,
            lifecycle_stage=lifecycle_stage,
            base_amount_minor=base_amount_minor,
            source_record_refs=source_record_refs,
        )
    if identity_binding.economic_event_id != economic_event_id:
        raise EconomicEventError("RELATION_EVENT_IDENTITY_MISMATCH", "factory identity binding uses another event ID")
    provisional = RelationEvent(
        relation_event_ref="relation_event_" + "0" * 32,
        economic_event_id=economic_event_id,
        source_system_id=source_system_id,
        source_artifact_sha256=source_artifact_sha256,
        source_business_key_hash=source_business_key_hash,
        source_business_digest=source_business_digest,
        event_type=event_type,
        direction=direction,
        lifecycle_stage=lifecycle_stage,
        event_status=event_status,
        identity_binding=identity_binding,
        counterparty_key=counterparty_key,
        document_id=document_id,
        document_line_id=document_line_id,
        event_date=event_date,
        base_amount_minor=base_amount_minor,
        base_currency="CNY",
        reversal_of_event_id=reversal_of_event_id,
        governed_relation_keys=governed_relation_keys,
        source_record_refs=source_record_refs,
    )
    result = RelationEvent(
        **{
            **provisional.__dict__,
            "relation_event_ref": "relation_event_"
            + _digest({**provisional._relation_payload(), "relation_event_ref": None})[:32],
        }
    )
    result.validate()
    return result


def relation_event_from_lifecycle_candidate(
    candidate: EconomicEventCandidate,
    *,
    identity_binding: EventIdentityBinding,
    source_system_id: str,
    source_artifact_sha256: str,
    governed_relation_keys: Tuple[str, ...] = (),
    reversal_of_event_id: Optional[str] = None,
) -> RelationEvent:
    """Bind an R6 lifecycle candidate to R7 identity evidence without mutating the source event."""

    candidate.validate()
    event_date = {
        LifecycleStage.BILLED: candidate.invoice_date,
        LifecycleStage.PAID: candidate.payment_date,
        LifecycleStage.COLLECTED: candidate.collection_date,
        LifecycleStage.CONTRACT_VALUE: candidate.effective_date or candidate.approval_date,
        LifecycleStage.COMMITMENT: candidate.approval_date or candidate.effective_date,
    }.get(candidate.lifecycle_stage, candidate.document_date)
    if event_date is None:
        raise EconomicEventError("RELATION_EVENT_DATE_REQUIRED", "candidate lacks its R7 relation date")
    return create_relation_event(
        economic_event_id=candidate.economic_event_id,
        source_system_id=source_system_id,
        source_artifact_sha256=source_artifact_sha256,
        source_business_key_hash=candidate.source_business_key_hash,
        source_business_digest=candidate.source_business_digest,
        event_type=candidate.event_type,
        direction=candidate.direction,
        lifecycle_stage=candidate.lifecycle_stage,
        event_status=candidate.event_status,
        identity_binding=identity_binding,
        counterparty_key=candidate.counterparty_source_key,
        document_id=candidate.document_id,
        document_line_id=candidate.document_line_id,
        event_date=event_date,
        base_amount_minor=candidate.transaction_amount_minor,
        reversal_of_event_id=reversal_of_event_id,
        governed_relation_keys=governed_relation_keys,
        source_record_refs=candidate.source_record_refs,
    )
