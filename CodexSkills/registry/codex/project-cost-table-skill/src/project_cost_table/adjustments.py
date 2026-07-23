"""R8 append-only manual-adjustment validation; never a final financial fact."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum
from typing import Any, Dict, Optional, Sequence, Tuple

from .formulas import EVIDENCE_REF_RE, MAX_ABS_MINOR_UNITS, POLICY_REF_RE, RESOLUTION_REF_RE, SHA256_RE


ADJUSTMENT_ID_RE = re.compile(r"^adjustment_[0-9a-f]{32}$")
FORMULA_PROFILE_ID_RE = re.compile(r"^formula_profile_[0-9a-f]{32}$")
ALLOWED_LIFECYCLE_STAGES = frozenset({"ACCRUAL", "POSTED_ACTUAL", "PAID", "FORECAST"})


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _text(value: Any, field_name: str) -> str:
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or unicodedata.normalize("NFC", value) != value
    ):
        raise AdjustmentError("ADJUSTMENT_SCHEMA", "%s must be nonempty normalized text" % field_name)
    return value


def _iso_date(value: Any, field_name: str, *, optional: bool = False) -> Optional[date]:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise AdjustmentError("ADJUSTMENT_SCHEMA", "%s must be an ISO date" % field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AdjustmentError("ADJUSTMENT_SCHEMA", "%s must be an ISO date" % field_name) from exc


class AdjustmentError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class AdjustmentStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TEMPLATE_NOT_ACTIVE = "TEMPLATE_NOT_ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    REVERSED = "REVERSED"
    EXPIRED = "EXPIRED"


class AmountSign(str, Enum):
    POSITIVE = "POSITIVE"
    NEGATIVE = "NEGATIVE"


class ReversalPolicy(str, Enum):
    EXPLICIT_REVERSAL_RECORD_REQUIRED = "EXPLICIT_REVERSAL_RECORD_REQUIRED"
    NO_AUTOMATIC_REVERSAL = "NO_AUTOMATIC_REVERSAL"


@dataclass(frozen=True)
class ManualAdjustment:
    adjustment_id: str
    metric_id: str
    lifecycle_stage: str
    legal_entity_id: str
    canonical_project_id: str
    wbs_or_cost_code: str
    cost_category: str
    amount_minor: int
    amount_sign: AmountSign
    business_date: str
    posting_period: str
    reason: str
    evidence_refs: Tuple[str, ...]
    formula_profile_id: str
    company_policy_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    valid_from: str
    valid_to: Optional[str]
    expires_on: Optional[str]
    reversal_policy: ReversalPolicy
    supersedes: Optional[str]
    reverses: Optional[str]
    bound_request_hash: str
    bound_input_hash: str
    bound_config_hash: str
    status: AdjustmentStatus
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def scope_key(self) -> Tuple[str, ...]:
        return (
            self.metric_id,
            self.lifecycle_stage,
            self.legal_entity_id,
            self.canonical_project_id,
            self.wbs_or_cost_code,
            self.cost_category,
        )

    def validate(self, *, as_of: Optional[date] = None) -> None:
        if not ADJUSTMENT_ID_RE.fullmatch(self.adjustment_id):
            raise AdjustmentError("ADJUSTMENT_ID", "adjustment ID must be opaque and canonical")
        for field_name in (
            "metric_id", "legal_entity_id", "canonical_project_id", "wbs_or_cost_code",
            "cost_category", "posting_period", "reason",
        ):
            _text(getattr(self, field_name), field_name)
        if self.lifecycle_stage not in ALLOWED_LIFECYCLE_STAGES:
            raise AdjustmentError("ADJUSTMENT_LIFECYCLE_STAGE", "adjustment lifecycle stage is not allowlisted")
        if type(self.amount_minor) is not int or self.amount_minor == 0 or abs(self.amount_minor) > MAX_ABS_MINOR_UNITS:
            raise AdjustmentError("ADJUSTMENT_AMOUNT", "adjustment amount must be a nonzero bounded integer")
        if not isinstance(self.amount_sign, AmountSign):
            raise AdjustmentError("ADJUSTMENT_SIGN", "adjustment sign must be explicit")
        if (self.amount_minor > 0) != (self.amount_sign is AmountSign.POSITIVE):
            raise AdjustmentError("ADJUSTMENT_SIGN_MISMATCH", "explicit sign differs from signed amount")
        business_date = _iso_date(self.business_date, "business_date")
        valid_from = _iso_date(self.valid_from, "valid_from")
        valid_to = _iso_date(self.valid_to, "valid_to", optional=True) or date.max
        expires_on = _iso_date(self.expires_on, "expires_on", optional=True)
        if valid_to < valid_from or not valid_from <= business_date <= valid_to:
            raise AdjustmentError("ADJUSTMENT_EFFECTIVE_PERIOD", "adjustment dates are outside the effective period")
        if expires_on is not None and expires_on < business_date:
            raise AdjustmentError("ADJUSTMENT_EXPIRY", "adjustment expiry predates its business date")
        if not isinstance(self.reversal_policy, ReversalPolicy) or not isinstance(self.status, AdjustmentStatus):
            raise AdjustmentError("ADJUSTMENT_ENUM", "adjustment status and reversal policy must be registered")
        if self.metric_inclusion_status != "NOT_EVALUATED_R8":
            raise AdjustmentError("ADJUSTMENT_AUTHORITY_ESCALATION", "R8 adjustment cannot claim final Metric inclusion")
        if not self.evidence_refs or len(self.evidence_refs) != len(set(self.evidence_refs)) or any(
            not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs
        ):
            raise AdjustmentError("ADJUSTMENT_EVIDENCE_REQUIRED", "adjustment requires unique hash-bound evidence")
        if len(self.company_policy_refs) != len(set(self.company_policy_refs)) or any(
            not POLICY_REF_RE.fullmatch(item) for item in self.company_policy_refs
        ):
            raise AdjustmentError("ADJUSTMENT_POLICY_REF", "adjustment policy references must be hash-bound")
        if len(self.input_resolution_refs) != len(set(self.input_resolution_refs)) or any(
            not RESOLUTION_REF_RE.fullmatch(item) for item in self.input_resolution_refs
        ):
            raise AdjustmentError("ADJUSTMENT_RESOLUTION_REF", "adjustment input resolutions must be canonical")
        if not self.company_policy_refs and not self.input_resolution_refs:
            raise AdjustmentError("ADJUSTMENT_AUTHORITY_REQUIRED", "adjustment requires a policy or qualified input resolution")
        if not FORMULA_PROFILE_ID_RE.fullmatch(self.formula_profile_id):
            raise AdjustmentError("ADJUSTMENT_FORMULA_PROFILE", "adjustment formula profile reference is invalid")
        if self.supersedes is not None and not ADJUSTMENT_ID_RE.fullmatch(self.supersedes):
            raise AdjustmentError("ADJUSTMENT_SUPERSEDES_REF", "superseded adjustment reference is invalid")
        if self.reverses is not None and not ADJUSTMENT_ID_RE.fullmatch(self.reverses):
            raise AdjustmentError("ADJUSTMENT_REVERSES_REF", "reversed adjustment reference is invalid")
        if self.supersedes is not None and self.reverses is not None:
            raise AdjustmentError("ADJUSTMENT_RELATION_CONFLICT", "adjustment cannot supersede and reverse simultaneously")
        for value, field_name in (
            (self.bound_request_hash, "bound_request_hash"),
            (self.bound_input_hash, "bound_input_hash"),
            (self.bound_config_hash, "bound_config_hash"),
        ):
            if not SHA256_RE.fullmatch(value):
                raise AdjustmentError("ADJUSTMENT_BINDING_HASH", "%s must be lowercase SHA256" % field_name)
        if as_of is not None:
            if self.status is AdjustmentStatus.ACTIVE and expires_on is not None and as_of > expires_on:
                raise AdjustmentError("ADJUSTMENT_EXPIRED_ACTIVE", "expired adjustment cannot remain active")
            if self.status is AdjustmentStatus.EXPIRED and (expires_on is None or as_of <= expires_on):
                raise AdjustmentError("ADJUSTMENT_EXPIRY_STATUS", "expiry status conflicts with the as-of date")

    def as_dict(self) -> Dict[str, Any]:
        payload = dict(self.__dict__)
        payload["amount_sign"] = self.amount_sign.value
        payload["reversal_policy"] = self.reversal_policy.value
        payload["status"] = self.status.value
        payload["evidence_refs"] = list(self.evidence_refs)
        payload["company_policy_refs"] = list(self.company_policy_refs)
        payload["input_resolution_refs"] = list(self.input_resolution_refs)
        return payload


@dataclass(frozen=True)
class AdjustmentChainResult:
    status: str
    active_adjustment_ids: Tuple[str, ...]
    excluded_adjustment_ids: Tuple[str, ...]
    chain_hash: str
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.manual_adjustment_chain.v1",
            "status": self.status,
            "active_adjustment_ids": list(self.active_adjustment_ids),
            "excluded_adjustment_ids": list(self.excluded_adjustment_ids),
            "chain_hash": self.chain_hash,
            "metric_inclusion_status": self.metric_inclusion_status,
        }


def validate_adjustment_chain(
    adjustments: Sequence[ManualAdjustment],
    *,
    as_of: date,
    request_hash: str,
) -> AdjustmentChainResult:
    if not adjustments:
        raise AdjustmentError("ADJUSTMENT_CHAIN_EMPTY", "adjustment chain requires at least one record")
    if not SHA256_RE.fullmatch(request_hash):
        raise AdjustmentError("ADJUSTMENT_REQUEST_HASH", "request hash must be lowercase SHA256")
    by_id: Dict[str, ManualAdjustment] = {}
    for item in adjustments:
        item.validate(as_of=as_of)
        if item.bound_request_hash != request_hash:
            raise AdjustmentError("ADJUSTMENT_REQUEST_BINDING", "adjustment does not bind the exact request")
        if item.adjustment_id in by_id:
            raise AdjustmentError("ADJUSTMENT_DUPLICATE", "adjustment ID is duplicated")
        by_id[item.adjustment_id] = item
    for item in adjustments:
        relation_id = item.supersedes or item.reverses
        if relation_id is None:
            continue
        target = by_id.get(relation_id)
        if target is None:
            raise AdjustmentError("ADJUSTMENT_TARGET_MISSING", "adjustment relation target is absent")
        if target.scope_key() != item.scope_key():
            raise AdjustmentError("ADJUSTMENT_SCOPE_MISMATCH", "adjustment relation cannot cross Metric or canonical scope")
        if _iso_date(item.business_date, "business_date") < _iso_date(target.business_date, "business_date"):
            raise AdjustmentError("ADJUSTMENT_RELATION_ORDER", "adjustment relation cannot predate its target")
        if item.supersedes is not None and target.status is not AdjustmentStatus.SUPERSEDED:
            raise AdjustmentError("ADJUSTMENT_SUPERSESSION_STATUS", "superseded target must retain explicit superseded status")
        if item.reverses is not None:
            if target.status is not AdjustmentStatus.REVERSED:
                raise AdjustmentError("ADJUSTMENT_REVERSAL_STATUS", "reversed target must retain explicit reversed status")
            if item.amount_minor != -target.amount_minor:
                raise AdjustmentError("ADJUSTMENT_REVERSAL_AMOUNT", "reversal must exactly negate its target")
    for item in adjustments:
        seen = set()
        current = item
        while current.supersedes or current.reverses:
            if current.adjustment_id in seen:
                raise AdjustmentError("ADJUSTMENT_CHAIN_CYCLE", "adjustment chain contains a cycle")
            seen.add(current.adjustment_id)
            current = by_id[current.supersedes or current.reverses]
    active = tuple(sorted(item.adjustment_id for item in adjustments if item.status is AdjustmentStatus.ACTIVE))
    excluded = tuple(sorted(item.adjustment_id for item in adjustments if item.status is not AdjustmentStatus.ACTIVE))
    payload = {
        "as_of": as_of.isoformat(),
        "request_hash": request_hash,
        "adjustments": [item.as_dict() for item in sorted(adjustments, key=lambda value: value.adjustment_id)],
    }
    return AdjustmentChainResult(
        status="PASS_R8_ADJUSTMENT_CHAIN_NOT_METRIC",
        active_adjustment_ids=active,
        excluded_adjustment_ids=excluded,
        chain_hash=_digest(payload),
    )
