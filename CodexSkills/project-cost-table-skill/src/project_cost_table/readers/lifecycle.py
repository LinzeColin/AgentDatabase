"""Governed R6 XLSX readers and exact duplicate-export handling for lifecycle candidates."""

from __future__ import annotations

import hashlib
import json
import os
import posixpath
import re
import stat
import unicodedata
import zipfile
from collections import Counter
from dataclasses import dataclass, replace
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Dict, Iterable, Mapping, Optional, Sequence, Tuple
from xml.etree import ElementTree as ET

from ..config_io import GovernedConfigError, load_governed_yaml_mapping
from ..events import (
    EconomicEventCandidate,
    EconomicEventError,
    EventDirection,
    LifecycleStage,
    SourceEventStatus,
    event_id_for_payload,
)
from ..manifest import SourceSelection
from ..money import BlankPolicy, MoneyParseError, MoneyProfile, RoundingLayer, parse_money
from ..paths import PathSafetyError, resolve_input_file
from ..security import FileSecurityError, SecurityProfile, preflight_source_file


LIFECYCLE_READER_VERSION = "2.0.0"
LIFECYCLE_PROFILE_BYTES_MAX = 1024 * 1024
SLOT_READER_IDS = {
    "project_billing": "project_invoice_v2",
    "cash_out": "payment_v2",
    "contract_and_changes": "contract_change_v2",
    "cash_in": "collection_v2",
}
EVIDENCE_REF_RE = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^src_[0-9a-f]{32}$")
SOURCE_RECORD_RE = re.compile(r"^rec_lifecycle_[0-9a-f]{32}$")
SOURCE_KEY_RE = re.compile(r"^lifecycle_line_[0-9a-f]{32}$")
SHEET_REF_RE = re.compile(r"^sheet_[0-9a-f]{16}$")
CELL_REF_RE = re.compile(r"^([A-Z]{1,4})([1-9][0-9]*)$")
EVENT_TYPE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
REASON_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{1,63}$")
MAX_MINOR = 9_223_372_036_854_775_807

TEXT_FIELDS = (
    "legal_entity_source_key",
    "project_source_key",
    "wbs_source_key",
    "contract_source_key",
    "counterparty_source_key",
    "document_id",
    "document_line_id",
    "source_event_type",
    "source_status",
    "source_row_kind",
    "reversal_of_source_key",
    "free_text",
)
DATE_FIELDS = (
    "document_date",
    "approval_date",
    "invoice_date",
    "payment_date",
    "collection_date",
    "effective_date",
    "reversal_date",
)
AMOUNT_FIELDS = ("transaction_amount", "gross_amount", "net_amount", "tax_amount")
CANONICAL_FIELDS = TEXT_FIELDS + DATE_FIELDS + AMOUNT_FIELDS + ("currency",)
ALLOWED_DATE_MODES = frozenset({"ISO_TEXT", "ISO_OR_EXCEL_SERIAL"})
ALLOWED_ROW_ACTIONS = frozenset({"EMIT_EVENT", "EXCLUDE_CONTROL"})
SLOT_ALLOWED_LIFECYCLES = {
    "project_billing": frozenset({(EventDirection.REVENUE, LifecycleStage.BILLED)}),
    "cash_out": frozenset({(EventDirection.CASH_OUT, LifecycleStage.PAID)}),
    "cash_in": frozenset({(EventDirection.CASH_IN, LifecycleStage.COLLECTED)}),
    "contract_and_changes": frozenset(
        {
            (EventDirection.REVENUE, LifecycleStage.CONTRACT_VALUE),
            (EventDirection.COST, LifecycleStage.COMMITMENT),
        }
    ),
}


def _canonical_digest(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _strict_text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or value != value.strip() or unicodedata.normalize("NFC", value) != value:
        raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "%s must be nonempty normalized text" % field)
    return value


def _string_tuple(value: Any, field: str, *, allow_empty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "%s must be a string list" % field)
    result = tuple(value)
    if (not allow_empty and not result) or len(result) != len(set(result)):
        raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "%s must be unique and satisfy cardinality" % field)
    for item in result:
        _strict_text(item, field)
    return result


class LifecycleReaderError(ValueError):
    """Structured R6 failure that never echoes a source path or cell value."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        row_number: Optional[int] = None,
        column_id: Optional[str] = None,
        partial_control: Optional["LifecycleReaderControl"] = None,
    ) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.row_number = row_number
        self.column_id = column_id
        self.partial_control = partial_control

    def as_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {"code": self.code, "message": self.message}
        if self.row_number is not None:
            result["row_number"] = self.row_number
        if self.column_id is not None:
            result["column_id"] = self.column_id
        if self.partial_control is not None:
            result["partial_control"] = self.partial_control.public_counts()
        return result


@dataclass(frozen=True)
class LifecycleStatusRule:
    source_status: str
    event_status: SourceEventStatus
    evidence_ref: Optional[str]

    def validate(self, *, active: bool) -> None:
        _strict_text(self.source_status, "source_status")
        if not isinstance(self.event_status, SourceEventStatus):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_STATUS_RULE", "normalized event status is not registered")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "status evidence must be hash-bound")
        if active and self.evidence_ref is None:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "active status rule requires evidence")


@dataclass(frozen=True)
class LifecycleEventTypeRule:
    source_event_type: Optional[str]
    event_type: str
    direction: EventDirection
    lifecycle_stage: LifecycleStage
    amount_multiplier: int
    evidence_ref: Optional[str]

    @property
    def rule_ref(self) -> str:
        return "rule_" + _canonical_digest(
            {
                "source_event_type": self.source_event_type,
                "event_type": self.event_type,
                "direction": self.direction.value,
                "lifecycle_stage": self.lifecycle_stage.value,
                "amount_multiplier": self.amount_multiplier,
                "evidence_ref": self.evidence_ref,
            }
        )[:32]

    def validate(self, *, active: bool, slot_id: str) -> None:
        if self.source_event_type is not None:
            _strict_text(self.source_event_type, "source_event_type")
        if not isinstance(self.event_type, str) or not EVENT_TYPE_RE.fullmatch(self.event_type):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "event type must be a canonical uppercase ID")
        if not isinstance(self.direction, EventDirection) or not isinstance(self.lifecycle_stage, LifecycleStage):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "direction/lifecycle must use registered enums")
        if (self.direction, self.lifecycle_stage) not in SLOT_ALLOWED_LIFECYCLES[slot_id]:
            raise LifecycleReaderError(
                "LIFECYCLE_PROFILE_STAGE_CONFLICT",
                "event rule would mix the governed slot with another lifecycle",
            )
        if type(self.amount_multiplier) is not int or self.amount_multiplier not in {-1, 1}:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "amount multiplier must be exactly -1 or 1")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "event-rule evidence must be hash-bound")
        if active and self.evidence_ref is None:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "active event rule requires evidence")


@dataclass(frozen=True)
class LifecycleRowKindRule:
    source_row_kind: str
    action: str
    reason_code: Optional[str]
    evidence_ref: Optional[str]

    def validate(self, *, active: bool) -> None:
        _strict_text(self.source_row_kind, "source_row_kind")
        if self.action not in ALLOWED_ROW_ACTIONS:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "row action is not registered")
        if self.action == "EMIT_EVENT" and self.reason_code is not None:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "business rows cannot carry an exclusion reason")
        if self.action == "EXCLUDE_CONTROL" and (
            self.reason_code is None or not REASON_CODE_RE.fullmatch(self.reason_code)
        ):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "control exclusion requires a reason code")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "row-rule evidence must be hash-bound")
        if active and self.evidence_ref is None:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "active row rule requires evidence")


@dataclass(frozen=True)
class LifecycleReaderProfile:
    profile_id: str
    status: str
    slot_id: str
    reader_id: str
    reader_version: str
    schema_id: str
    sheet_name: str
    header_row: int
    first_data_row: int
    max_data_rows: int
    expected_headers: Tuple[str, ...]
    column_bindings: Tuple[Tuple[str, Optional[str]], ...]
    date_modes: Tuple[Tuple[str, str], ...]
    default_currency: Optional[str]
    required_business_fields: Tuple[str, ...]
    status_rules: Tuple[LifecycleStatusRule, ...]
    event_type_rules: Tuple[LifecycleEventTypeRule, ...]
    default_event_rule: Optional[LifecycleEventTypeRule]
    row_kind_rules: Tuple[LifecycleRowKindRule, ...]
    automatic_project_assignment_allowed: bool
    reader_decides_final_metric_inclusion: bool
    evidence_refs: Tuple[str, ...]
    content_sha256: str

    @property
    def schema_fingerprint(self) -> str:
        return _canonical_digest(
            {
                "schema_id": self.schema_id,
                "slot_id": self.slot_id,
                "reader_id": self.reader_id,
                "reader_version": self.reader_version,
                "sheet_name": self.sheet_name,
                "header_row": self.header_row,
                "first_data_row": self.first_data_row,
                "expected_headers": list(self.expected_headers),
                "column_bindings": dict(self.column_bindings),
                "date_modes": dict(self.date_modes),
                "default_currency": self.default_currency,
                "required_business_fields": list(self.required_business_fields),
                "status_rules": [
                    (item.source_status, item.event_status.value, item.evidence_ref) for item in self.status_rules
                ],
                "event_type_rules": [
                    (
                        item.source_event_type,
                        item.event_type,
                        item.direction.value,
                        item.lifecycle_stage.value,
                        item.amount_multiplier,
                        item.evidence_ref,
                    )
                    for item in self.event_type_rules
                ],
                "default_event_rule": None
                if self.default_event_rule is None
                else (
                    self.default_event_rule.event_type,
                    self.default_event_rule.direction.value,
                    self.default_event_rule.lifecycle_stage.value,
                    self.default_event_rule.amount_multiplier,
                    self.default_event_rule.evidence_ref,
                ),
                "row_kind_rules": [
                    (item.source_row_kind, item.action, item.reason_code, item.evidence_ref)
                    for item in self.row_kind_rules
                ],
            }
        )

    def binding_map(self) -> Dict[str, Optional[str]]:
        return dict(self.column_bindings)

    def date_mode_map(self) -> Dict[str, str]:
        return dict(self.date_modes)

    def status_rule_map(self) -> Dict[str, LifecycleStatusRule]:
        return {item.source_status: item for item in self.status_rules}

    def event_rule_map(self) -> Dict[str, LifecycleEventTypeRule]:
        return {item.source_event_type or "": item for item in self.event_type_rules}

    def row_rule_map(self) -> Dict[str, LifecycleRowKindRule]:
        return {item.source_row_kind: item for item in self.row_kind_rules}

    def validate(self, *, require_active: bool = False) -> None:
        for field in ("profile_id", "slot_id", "reader_id", "reader_version", "schema_id", "sheet_name"):
            _strict_text(getattr(self, field), field)
        if self.slot_id not in SLOT_READER_IDS or self.reader_id != SLOT_READER_IDS[self.slot_id]:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_READER", "slot and reader identity are incompatible")
        if self.reader_version != LIFECYCLE_READER_VERSION:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_READER", "reader version is not the locked R6 implementation")
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_STATUS", "profile status is not registered")
        active = self.status == "ACTIVE"
        if any(type(item) is not int for item in (self.header_row, self.first_data_row, self.max_data_rows)):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "row controls require exact integers")
        if self.header_row < 1 or self.first_data_row <= self.header_row or not 1 <= self.max_data_rows <= 5_000_000:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "row controls are inconsistent or exceed the ceiling")
        headers = _string_tuple(self.expected_headers, "expected_headers", allow_empty=False)
        if headers != self.expected_headers:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "headers must use an immutable tuple")
        bindings = dict(self.column_bindings)
        if len(bindings) != len(self.column_bindings) or set(bindings) != set(CANONICAL_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "column bindings must cover every canonical R6 field")
        for key, value in self.column_bindings:
            if not isinstance(key, str) or (value is not None and not isinstance(value, str)):
                raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "column bindings require text or null")
            if value is not None and value not in headers:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "bound column is absent from the locked headers")
        modes = dict(self.date_modes)
        if len(modes) != len(self.date_modes) or set(modes) != set(DATE_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "date modes must cover every R6 date field")
        if any(value not in ALLOWED_DATE_MODES for value in modes.values()):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "date mode is not registered")
        if self.default_currency not in {None, "CNY"}:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_CURRENCY", "R6 default currency can only be CNY")
        required = _string_tuple(self.required_business_fields, "required_business_fields", allow_empty=False)
        if required != self.required_business_fields or not set(required) <= set(CANONICAL_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "required business fields are invalid")
        always_required = {"document_id", "source_status", "transaction_amount", "currency"}
        if not always_required <= set(required):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "every R6 business row needs ID/status/amount/currency")
        if self.slot_id == "project_billing" and not {
            "invoice_date",
            "gross_amount",
            "net_amount",
            "tax_amount",
        } <= set(required):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "billing profile must require date/gross/net/tax")
        if self.slot_id == "cash_out" and "payment_date" not in required:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "payment profile must require payment date")
        if self.slot_id == "cash_in" and "collection_date" not in required:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "collection profile must require collection date")
        if self.slot_id == "contract_and_changes" and not {"approval_date", "effective_date"} & set(required):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "contract profile requires approval or effective date")
        for field in required:
            if field == "currency" and self.default_currency is not None:
                continue
            if bindings[field] is None:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "required field lacks a bound source column")
        if bindings["source_status"] is None:
            raise LifecycleReaderError("LIFECYCLE_PROFILE_INCOMPLETE", "source status column is mandatory")
        for item in self.status_rules:
            item.validate(active=active)
        if not self.status_rules or len(self.status_rule_map()) != len(self.status_rules):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_STATUS_RULE", "status rules must be nonempty and unique")
        if bindings["source_event_type"] is None:
            if self.default_event_rule is None or self.event_type_rules:
                raise LifecycleReaderError(
                    "LIFECYCLE_PROFILE_EVENT_RULE",
                    "unbound source event type requires exactly one default rule",
                )
            self.default_event_rule.validate(active=active, slot_id=self.slot_id)
            if self.default_event_rule.source_event_type is not None:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "default event rule cannot name a source type")
        else:
            if self.default_event_rule is not None or not self.event_type_rules:
                raise LifecycleReaderError(
                    "LIFECYCLE_PROFILE_EVENT_RULE",
                    "bound source event type requires explicit unique rules",
                )
            for item in self.event_type_rules:
                item.validate(active=active, slot_id=self.slot_id)
                if item.source_event_type is None:
                    raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "mapped event rule requires a source type")
            if len(self.event_rule_map()) != len(self.event_type_rules):
                raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "source event-type rules must be unique")
        if bindings["source_row_kind"] is None:
            if self.row_kind_rules:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "unbound row kind cannot have mapping rules")
        else:
            if not self.row_kind_rules:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "bound row kind requires explicit rules")
            for item in self.row_kind_rules:
                item.validate(active=active)
            if len(self.row_rule_map()) != len(self.row_kind_rules):
                raise LifecycleReaderError("LIFECYCLE_PROFILE_ROW_RULE", "row-kind rules must be unique")
        if self.automatic_project_assignment_allowed is not False or self.reader_decides_final_metric_inclusion is not False:
            raise LifecycleReaderError(
                "LIFECYCLE_PROFILE_AUTHORITY",
                "R6 cannot auto-assign a project or decide final Metric inclusion",
            )
        refs = _string_tuple(self.evidence_refs, "evidence_refs")
        if refs != self.evidence_refs or any(not EVIDENCE_REF_RE.fullmatch(item) for item in refs):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_EVIDENCE", "profile evidence references must be hash-bound")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_HASH", "profile content hash is invalid")
        if require_active and (not active or not refs):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_NOT_ACTIVE", "a hash-bound ACTIVE R6 profile is required")

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, content_sha256: Optional[str] = None) -> "LifecycleReaderProfile":
        expected = {
            "schema_version",
            "profile_id",
            "status",
            "slot_id",
            "reader_id",
            "reader_version",
            "schema_id",
            "sheet_name",
            "header_row",
            "first_data_row",
            "max_data_rows",
            "expected_headers",
            "column_bindings",
            "date_modes",
            "default_currency",
            "required_business_fields",
            "status_rules",
            "event_type_rules",
            "default_event_rule",
            "row_kind_rules",
            "automatic_project_assignment_allowed",
            "reader_decides_final_metric_inclusion",
            "evidence_refs",
        }
        if not isinstance(raw, Mapping) or set(raw) != expected or raw.get("schema_version") != "kmfa.project_cost.lifecycle_reader_profile.v1":
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "profile fields differ from lifecycle v1")
        bindings = raw.get("column_bindings")
        date_modes = raw.get("date_modes")
        if not isinstance(bindings, Mapping) or set(bindings) != set(CANONICAL_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "column bindings differ from lifecycle v1")
        if not isinstance(date_modes, Mapping) or set(date_modes) != set(DATE_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "date modes differ from lifecycle v1")

        def status_rule(item: Any) -> LifecycleStatusRule:
            if not isinstance(item, Mapping) or set(item) != {"source_status", "event_status", "evidence_ref"}:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "status-rule fields differ from lifecycle v1")
            try:
                return LifecycleStatusRule(
                    source_status=_strict_text(item.get("source_status"), "source_status") or "",
                    event_status=SourceEventStatus(_strict_text(item.get("event_status"), "event_status") or ""),
                    evidence_ref=_strict_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            except ValueError as exc:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_STATUS_RULE", "event status is not registered") from exc

        def event_rule(item: Any) -> LifecycleEventTypeRule:
            fields = {
                "source_event_type",
                "event_type",
                "direction",
                "lifecycle_stage",
                "amount_multiplier",
                "evidence_ref",
            }
            if not isinstance(item, Mapping) or set(item) != fields:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "event-rule fields differ from lifecycle v1")
            try:
                return LifecycleEventTypeRule(
                    source_event_type=_strict_text(
                        item.get("source_event_type"), "source_event_type", optional=True
                    ),
                    event_type=_strict_text(item.get("event_type"), "event_type") or "",
                    direction=EventDirection(_strict_text(item.get("direction"), "direction") or ""),
                    lifecycle_stage=LifecycleStage(
                        _strict_text(item.get("lifecycle_stage"), "lifecycle_stage") or ""
                    ),
                    amount_multiplier=item.get("amount_multiplier"),
                    evidence_ref=_strict_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            except ValueError as exc:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_EVENT_RULE", "event rule enum is not registered") from exc

        def row_rule(item: Any) -> LifecycleRowKindRule:
            if not isinstance(item, Mapping) or set(item) != {
                "source_row_kind",
                "action",
                "reason_code",
                "evidence_ref",
            }:
                raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "row-rule fields differ from lifecycle v1")
            return LifecycleRowKindRule(
                source_row_kind=_strict_text(item.get("source_row_kind"), "source_row_kind") or "",
                action=_strict_text(item.get("action"), "action") or "",
                reason_code=_strict_text(item.get("reason_code"), "reason_code", optional=True),
                evidence_ref=_strict_text(item.get("evidence_ref"), "evidence_ref", optional=True),
            )

        status_raw = raw.get("status_rules")
        event_raw = raw.get("event_type_rules")
        row_raw = raw.get("row_kind_rules")
        if not isinstance(status_raw, list) or not isinstance(event_raw, list) or not isinstance(row_raw, list):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "profile rules must be lists")
        default_raw = raw.get("default_event_rule")
        if default_raw is not None and not isinstance(default_raw, Mapping):
            raise LifecycleReaderError("LIFECYCLE_PROFILE_SCHEMA", "default event rule must be a mapping or null")
        profile = cls(
            profile_id=_strict_text(raw.get("profile_id"), "profile_id") or "",
            status=_strict_text(raw.get("status"), "status") or "",
            slot_id=_strict_text(raw.get("slot_id"), "slot_id") or "",
            reader_id=_strict_text(raw.get("reader_id"), "reader_id") or "",
            reader_version=_strict_text(raw.get("reader_version"), "reader_version") or "",
            schema_id=_strict_text(raw.get("schema_id"), "schema_id") or "",
            sheet_name=_strict_text(raw.get("sheet_name"), "sheet_name") or "",
            header_row=raw.get("header_row"),
            first_data_row=raw.get("first_data_row"),
            max_data_rows=raw.get("max_data_rows"),
            expected_headers=_string_tuple(raw.get("expected_headers"), "expected_headers", allow_empty=False),
            column_bindings=tuple(sorted((str(key), value) for key, value in bindings.items())),
            date_modes=tuple(sorted((str(key), str(value)) for key, value in date_modes.items())),
            default_currency=_strict_text(raw.get("default_currency"), "default_currency", optional=True),
            required_business_fields=_string_tuple(
                raw.get("required_business_fields"), "required_business_fields", allow_empty=False
            ),
            status_rules=tuple(status_rule(item) for item in status_raw),
            event_type_rules=tuple(event_rule(item) for item in event_raw),
            default_event_rule=None if default_raw is None else event_rule(default_raw),
            row_kind_rules=tuple(row_rule(item) for item in row_raw),
            automatic_project_assignment_allowed=raw.get("automatic_project_assignment_allowed"),
            reader_decides_final_metric_inclusion=raw.get("reader_decides_final_metric_inclusion"),
            evidence_refs=_string_tuple(raw.get("evidence_refs"), "evidence_refs"),
            content_sha256=content_sha256 or _canonical_digest(raw),
        )
        profile.validate()
        return profile

    @classmethod
    def from_yaml(cls, path: Path) -> "LifecycleReaderProfile":
        try:
            raw, content_hash = load_governed_yaml_mapping(path, max_bytes=LIFECYCLE_PROFILE_BYTES_MAX)
        except GovernedConfigError as exc:
            raise LifecycleReaderError(exc.code, exc.message) from exc
        return cls.from_mapping(raw, content_sha256=content_hash)


@dataclass(frozen=True)
class LifecycleSourceRecord:
    source_record_ref: str
    source_business_key_hash: str
    normalized_business_digest: str
    unbound_content_digest: str
    source_id: str
    source_sha256: str
    slot_id: str
    reader_id: str
    reader_version: str
    schema_id: str
    schema_fingerprint: str
    profile_sha256: str
    sheet_name: str
    sheet_ref: str
    row_number: int
    row_action: str
    exclusion_reason_code: Optional[str]
    legal_entity_source_key: Optional[str]
    project_source_key: Optional[str]
    wbs_source_key: Optional[str]
    contract_source_key: Optional[str]
    counterparty_source_key: Optional[str]
    document_id: Optional[str]
    document_line_id: Optional[str]
    source_event_type: Optional[str]
    source_status: Optional[str]
    source_row_kind: Optional[str]
    reversal_of_source_key: Optional[str]
    free_text: Optional[str]
    document_date: Optional[str]
    approval_date: Optional[str]
    invoice_date: Optional[str]
    payment_date: Optional[str]
    collection_date: Optional[str]
    effective_date: Optional[str]
    reversal_date: Optional[str]
    transaction_amount_minor: Optional[int]
    gross_amount_minor: Optional[int]
    net_amount_minor: Optional[int]
    tax_amount_minor: Optional[int]
    currency: Optional[str]
    source_arithmetic_status: str
    source_arithmetic_delta_minor: Optional[int]

    def _business_payload(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "row_action": self.row_action,
            "exclusion_reason_code": self.exclusion_reason_code,
            "legal_entity_source_key": self.legal_entity_source_key,
            "project_source_key": self.project_source_key,
            "wbs_source_key": self.wbs_source_key,
            "contract_source_key": self.contract_source_key,
            "counterparty_source_key": self.counterparty_source_key,
            "document_id": self.document_id,
            "document_line_id": self.document_line_id,
            "source_event_type": self.source_event_type,
            "source_status": self.source_status,
            "source_row_kind": self.source_row_kind,
            "reversal_of_source_key": self.reversal_of_source_key,
            "free_text": self.free_text,
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
            "currency": self.currency,
            "source_arithmetic_status": self.source_arithmetic_status,
            "source_arithmetic_delta_minor": self.source_arithmetic_delta_minor,
            "unbound_content_digest": self.unbound_content_digest,
        }

    def validate(self) -> None:
        if (
            not SOURCE_RECORD_RE.fullmatch(self.source_record_ref)
            or not SOURCE_KEY_RE.fullmatch(self.source_business_key_hash)
            or not SHA256_RE.fullmatch(self.normalized_business_digest)
            or not SHA256_RE.fullmatch(self.unbound_content_digest)
            or not SOURCE_ID_RE.fullmatch(self.source_id)
            or not SHA256_RE.fullmatch(self.source_sha256)
            or not SHA256_RE.fullmatch(self.schema_fingerprint)
            or not SHA256_RE.fullmatch(self.profile_sha256)
            or not SHEET_REF_RE.fullmatch(self.sheet_ref)
        ):
            raise LifecycleReaderError("LIFECYCLE_RECORD_LINEAGE", "source-record lineage is invalid")
        if self.slot_id not in SLOT_READER_IDS or self.reader_id != SLOT_READER_IDS[self.slot_id]:
            raise LifecycleReaderError("LIFECYCLE_RECORD_SCHEMA", "source-record slot/reader is invalid")
        if self.reader_version != LIFECYCLE_READER_VERSION or type(self.row_number) is not int or self.row_number < 1:
            raise LifecycleReaderError("LIFECYCLE_RECORD_SCHEMA", "source-record reader version or row is invalid")
        if self.row_action not in ALLOWED_ROW_ACTIONS:
            raise LifecycleReaderError("LIFECYCLE_RECORD_ACTION", "source-record row action is invalid")
        if self.row_action == "EMIT_EVENT" and self.exclusion_reason_code is not None:
            raise LifecycleReaderError("LIFECYCLE_RECORD_ACTION", "event row cannot carry an exclusion reason")
        if self.row_action == "EXCLUDE_CONTROL" and (
            self.exclusion_reason_code is None or not REASON_CODE_RE.fullmatch(self.exclusion_reason_code)
        ):
            raise LifecycleReaderError("LIFECYCLE_RECORD_ACTION", "control row requires an exclusion reason")
        for value in (
            self.transaction_amount_minor,
            self.gross_amount_minor,
            self.net_amount_minor,
            self.tax_amount_minor,
            self.source_arithmetic_delta_minor,
        ):
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_MINOR):
                raise LifecycleReaderError("LIFECYCLE_RECORD_AMOUNT", "source amounts require signed 64-bit minor units")
        for field in DATE_FIELDS:
            value = getattr(self, field)
            if value is not None:
                try:
                    date.fromisoformat(value)
                except (TypeError, ValueError) as exc:
                    raise LifecycleReaderError("LIFECYCLE_RECORD_DATE", "source date is not canonical ISO") from exc
        expected_status, expected_delta = _source_arithmetic(
            self.gross_amount_minor,
            self.net_amount_minor,
            self.tax_amount_minor,
        )
        if self.source_arithmetic_status != expected_status or self.source_arithmetic_delta_minor != expected_delta:
            raise LifecycleReaderError("LIFECYCLE_RECORD_ARITHMETIC", "source arithmetic fields do not reconcile")
        business_digest = _canonical_digest(self._business_payload())
        stable_key = _canonical_digest(
            {
                "slot_id": self.slot_id,
                "legal_entity_source_key": self.legal_entity_source_key,
                "document_id": self.document_id,
                "document_line_id": self.document_line_id,
                "source_event_type": self.source_event_type,
                "document_date": self.document_date,
            }
        )
        record_ref = "rec_lifecycle_" + _canonical_digest(
            {
                "source_id": self.source_id,
                "source_sha256": self.source_sha256,
                "sheet_ref": self.sheet_ref,
                "row_number": self.row_number,
                "business_digest": business_digest,
            }
        )[:32]
        if (
            self.normalized_business_digest != business_digest
            or self.source_business_key_hash != "lifecycle_line_" + stable_key[:32]
            or self.source_record_ref != record_ref
        ):
            raise LifecycleReaderError("LIFECYCLE_RECORD_TAMPERED", "source record no longer matches its lineage digests")

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        payload = {
            "schema_version": "kmfa.project_cost.lifecycle_source_record.v1",
            **self.__dict__,
        }
        return payload


@dataclass(frozen=True)
class AmountColumnControl:
    positive_count: int
    negative_count: int
    zero_count: int
    null_count: int
    total_minor: int


@dataclass(frozen=True)
class LifecycleReaderControl:
    physical_data_row_count: int
    emitted_record_count: int
    business_record_count: int
    control_record_count: int
    empty_row_count: int
    parse_failure_count: int
    source_arithmetic_anomaly_count: int
    exclusion_counts: Tuple[Tuple[str, int], ...]
    transaction_amount: AmountColumnControl
    gross_amount: AmountColumnControl
    net_amount: AmountColumnControl
    tax_amount: AmountColumnControl
    business_amount_totals: Tuple[Tuple[str, int], ...]
    control_amount_totals: Tuple[Tuple[str, int], ...]
    amount_partition_deltas: Tuple[Tuple[str, int], ...]
    row_conservation_delta: int

    def validate(self) -> None:
        if self.business_record_count + self.control_record_count != self.emitted_record_count:
            raise LifecycleReaderError("LIFECYCLE_ROW_CONSERVATION", "business/control source rows do not conserve")
        if (
            self.row_conservation_delta != 0
            or self.physical_data_row_count
            != self.emitted_record_count + self.empty_row_count + self.parse_failure_count
        ):
            raise LifecycleReaderError("LIFECYCLE_ROW_CONSERVATION", "reader physical rows do not conserve")
        all_totals = {
            "transaction_amount": self.transaction_amount.total_minor,
            "gross_amount": self.gross_amount.total_minor,
            "net_amount": self.net_amount.total_minor,
            "tax_amount": self.tax_amount.total_minor,
        }
        business = dict(self.business_amount_totals)
        controls = dict(self.control_amount_totals)
        deltas = dict(self.amount_partition_deltas)
        if set(business) != set(AMOUNT_FIELDS) or set(controls) != set(AMOUNT_FIELDS) or set(deltas) != set(AMOUNT_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_AMOUNT_CONSERVATION", "amount partitions do not cover every source amount")
        if any(deltas[field] != all_totals[field] - business[field] - controls[field] for field in AMOUNT_FIELDS):
            raise LifecycleReaderError("LIFECYCLE_AMOUNT_CONSERVATION", "amount partition delta is inconsistent")
        if any(deltas.values()):
            raise LifecycleReaderError("LIFECYCLE_AMOUNT_CONSERVATION", "business and control amounts do not conserve")

    def public_counts(self) -> Dict[str, int]:
        return {
            "physical_data_row_count": self.physical_data_row_count,
            "emitted_record_count": self.emitted_record_count,
            "business_record_count": self.business_record_count,
            "control_record_count": self.control_record_count,
            "empty_row_count": self.empty_row_count,
            "parse_failure_count": self.parse_failure_count,
            "source_arithmetic_anomaly_count": self.source_arithmetic_anomaly_count,
            "amount_partition_conservation_delta_count": sum(value != 0 for _, value in self.amount_partition_deltas),
            "row_conservation_delta": self.row_conservation_delta,
        }


@dataclass(frozen=True)
class LifecycleReaderResult:
    records: Tuple[LifecycleSourceRecord, ...]
    events: Tuple[EconomicEventCandidate, ...]
    control: LifecycleReaderControl
    source_sha256: str
    profile_sha256: str
    schema_fingerprint: str
    business_fingerprint: str


@dataclass(frozen=True)
class DuplicateExportGroup:
    slot_id: str
    business_fingerprint: str
    canonical_source_id: str
    alias_source_ids: Tuple[str, ...]
    event_count: int


@dataclass(frozen=True)
class LifecycleBatchControl:
    selected_source_count: int
    unique_export_count: int
    duplicate_alias_count: int
    source_record_count: int
    pre_dedup_event_count: int
    emitted_event_count: int
    duplicate_suppressed_event_count: int
    source_row_conservation_delta: int
    event_count_conservation_delta: int
    event_amount_conservation_delta_minor: int
    source_arithmetic_anomaly_count: int
    lifecycle_counts: Tuple[Tuple[str, int], ...]

    def validate(self) -> None:
        if self.selected_source_count != self.unique_export_count + self.duplicate_alias_count:
            raise LifecycleReaderError("LIFECYCLE_EXPORT_CONSERVATION", "selected exports do not conserve")
        if self.pre_dedup_event_count != self.emitted_event_count + self.duplicate_suppressed_event_count:
            raise LifecycleReaderError("LIFECYCLE_EVENT_CONSERVATION", "duplicate-export event counts do not conserve")
        if self.source_row_conservation_delta != 0 or self.event_count_conservation_delta != 0:
            raise LifecycleReaderError("LIFECYCLE_EVENT_CONSERVATION", "R6 source/event rows do not conserve")
        if self.event_amount_conservation_delta_minor != 0:
            raise LifecycleReaderError("LIFECYCLE_EVENT_CONSERVATION", "duplicate-export event amounts do not conserve")


@dataclass(frozen=True)
class LifecycleBatchResult:
    records: Tuple[LifecycleSourceRecord, ...]
    events: Tuple[EconomicEventCandidate, ...]
    duplicate_export_groups: Tuple[DuplicateExportGroup, ...]
    source_results: Tuple[LifecycleReaderResult, ...]
    control: LifecycleBatchControl
    business_fingerprint: str


@dataclass(frozen=True)
class _CellValue:
    text: Optional[str]
    kind: str


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _read_xml(archive: zipfile.ZipFile, name: str, security_profile: SecurityProfile) -> ET.Element:
    try:
        info = archive.getinfo(name)
    except KeyError as exc:
        raise LifecycleReaderError("LIFECYCLE_XLSX_PART_MISSING", "locked workbook part is missing") from exc
    if info.file_size > security_profile.xml_single_part_bytes_max:
        raise LifecycleReaderError("LIFECYCLE_XLSX_XML_LIMIT", "workbook XML exceeds the security ceiling")
    try:
        payload = archive.read(info)
    except (OSError, EOFError, RuntimeError, zipfile.BadZipFile) as exc:
        raise LifecycleReaderError("LIFECYCLE_XLSX_PART_READ", "workbook XML cannot be read") from exc
    upper = payload.upper()
    if b"<!DOCTYPE" in upper or b"<!ENTITY" in upper:
        raise LifecycleReaderError("LIFECYCLE_XLSX_ENTITY", "DTD/entity content is forbidden")
    try:
        return ET.fromstring(payload)
    except ET.ParseError as exc:
        raise LifecycleReaderError("LIFECYCLE_XLSX_XML_INVALID", "workbook XML is malformed") from exc


def _safe_sheet_target(target: str) -> str:
    if not target or "\\" in target or "\x00" in target or "?" in target or "#" in target:
        raise LifecycleReaderError("LIFECYCLE_XLSX_TARGET", "worksheet relationship target is unsafe")
    normalized = (
        posixpath.normpath(target.lstrip("/"))
        if target.startswith("/")
        else posixpath.normpath(posixpath.join("xl", target))
    )
    pure = PurePosixPath(normalized)
    if normalized.startswith("../") or any(part in {"", ".", ".."} for part in pure.parts) or not normalized.startswith("xl/"):
        raise LifecycleReaderError("LIFECYCLE_XLSX_TARGET", "worksheet relationship escapes the workbook root")
    return normalized


def _column_index(reference: str) -> Tuple[int, int]:
    match = CELL_REF_RE.fullmatch(reference)
    if match is None:
        raise LifecycleReaderError("LIFECYCLE_XLSX_CELL_REF", "cell reference is not canonical")
    letters, row_text = match.groups()
    column = 0
    for character in letters:
        column = column * 26 + ord(character) - 64
    return column, int(row_text)


def _cell_value(cell: ET.Element, shared_strings: Sequence[str]) -> _CellValue:
    if any(_local_name(node.tag) == "f" for node in cell):
        raise LifecycleReaderError("LIFECYCLE_XLSX_FORMULA", "formula reached the value-only R6 reader")
    cell_type = cell.attrib.get("t")
    values = [node for node in cell if _local_name(node.tag) == "v"]
    if cell_type == "inlineStr":
        return _CellValue("".join(node.text or "" for node in cell.iter() if _local_name(node.tag) == "t"), "text")
    raw = values[0].text if values else None
    if cell_type == "s":
        try:
            return _CellValue(shared_strings[int(raw or "")], "text")
        except (ValueError, IndexError) as exc:
            raise LifecycleReaderError("LIFECYCLE_XLSX_SHARED_STRING", "shared-string reference is invalid") from exc
    if cell_type in (None, "n"):
        return _CellValue(raw, "number" if raw is not None else "blank")
    if cell_type in {"str", "d"}:
        return _CellValue(raw, "date" if cell_type == "d" else "text")
    if cell_type == "b":
        if raw not in {"0", "1"}:
            raise LifecycleReaderError("LIFECYCLE_XLSX_BOOLEAN", "boolean cell is invalid")
        return _CellValue(raw, "boolean")
    if cell_type == "e":
        raise LifecycleReaderError("LIFECYCLE_XLSX_ERROR", "error-valued cell is invalid source evidence")
    raise LifecycleReaderError("LIFECYCLE_XLSX_CELL_TYPE", "cell type is not supported")


def _shared_strings(archive: zipfile.ZipFile, security_profile: SecurityProfile) -> Tuple[str, ...]:
    if "xl/sharedStrings.xml" not in archive.namelist():
        return ()
    root = _read_xml(archive, "xl/sharedStrings.xml", security_profile)
    return tuple(
        "".join(item.text or "" for item in node.iter() if _local_name(item.tag) == "t")
        for node in root
        if _local_name(node.tag) == "si"
    )


def _workbook_sheet(
    archive: zipfile.ZipFile,
    *,
    profile: LifecycleReaderProfile,
    security_profile: SecurityProfile,
) -> Tuple[str, bool]:
    workbook = _read_xml(archive, "xl/workbook.xml", security_profile)
    date_1904 = False
    relation_ids = []
    for node in workbook.iter():
        local = _local_name(node.tag)
        if local == "workbookPr":
            raw = node.attrib.get("date1904", "0")
            if raw not in {"0", "false", "FALSE", "1", "true", "TRUE"}:
                raise LifecycleReaderError("LIFECYCLE_XLSX_DATE_SYSTEM", "date system flag is invalid")
            date_1904 = raw in {"1", "true", "TRUE"}
        elif local == "sheet" and node.attrib.get("name") == profile.sheet_name:
            relation = next((value for key, value in node.attrib.items() if key.endswith("}id")), None)
            if relation is None:
                raise LifecycleReaderError("LIFECYCLE_XLSX_SHEET_REL", "selected sheet has no relationship")
            relation_ids.append(relation)
    if len(relation_ids) != 1:
        raise LifecycleReaderError("LIFECYCLE_XLSX_SHEET", "selected sheet must exist exactly once")
    relations = _read_xml(archive, "xl/_rels/workbook.xml.rels", security_profile)
    targets = []
    for node in relations.iter():
        if _local_name(node.tag) != "Relationship" or node.attrib.get("Id") != relation_ids[0]:
            continue
        if node.attrib.get("TargetMode", "").casefold() == "external":
            raise LifecycleReaderError("LIFECYCLE_XLSX_EXTERNAL_SHEET", "external worksheet is forbidden")
        targets.append(_safe_sheet_target(node.attrib.get("Target", "")))
    if len(targets) != 1:
        raise LifecycleReaderError("LIFECYCLE_XLSX_SHEET_REL", "selected sheet relationship is ambiguous")
    return targets[0], date_1904


def _normalized_text(value: _CellValue) -> Optional[str]:
    if value.text is None:
        return None
    normalized = unicodedata.normalize("NFC", value.text.replace("\r\n", "\n").replace("\r", "\n").strip())
    return normalized or None


def _excel_serial_date(raw: str, *, date_1904: bool) -> date:
    try:
        value = Decimal(raw)
    except InvalidOperation as exc:
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "numeric date cannot be represented exactly") from exc
    if not value.is_finite() or value != value.to_integral_value():
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "date serial must be a finite whole day")
    serial = int(value)
    if date_1904:
        if serial < 0:
            raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "1904-system date cannot be negative")
        return date(1904, 1, 1) + timedelta(days=serial)
    if serial <= 0 or serial == 60:
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "invalid or fictitious 1900-system date")
    return date(1899, 12, 31) + timedelta(days=serial - (1 if serial > 60 else 0))


def _parse_date(value: _CellValue, *, mode: str, date_1904: bool) -> Optional[str]:
    raw = _normalized_text(value)
    if raw is None:
        return None
    if value.kind == "boolean":
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "boolean cannot become a date")
    if value.kind == "number":
        if mode != "ISO_OR_EXCEL_SERIAL":
            raise LifecycleReaderError("LIFECYCLE_DATE_MODE", "numeric date is forbidden by the profile")
        return _excel_serial_date(raw, date_1904=date_1904).isoformat()
    if len(raw) != 10:
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "timestamp text cannot be truncated into a governed date")
    try:
        parsed = date.fromisoformat(raw)
    except ValueError as exc:
        raise LifecycleReaderError("LIFECYCLE_DATE_PARSE", "date must use governed ISO text or enabled serial") from exc
    return parsed.isoformat()


def _parse_amount(value: _CellValue, *, money_profile: MoneyProfile) -> Optional[int]:
    if value.kind == "boolean":
        raise LifecycleReaderError("LIFECYCLE_AMOUNT_TYPE", "boolean cannot become money")
    try:
        parsed = parse_money(
            _normalized_text(value),
            profile=money_profile,
            rounding_layer=RoundingLayer.SOURCE_PARSE,
            blank_policy=BlankPolicy.NULL,
        )
    except MoneyParseError as exc:
        raise LifecycleReaderError("LIFECYCLE_AMOUNT_" + exc.code, "amount failed the strict money parser") from exc
    return None if parsed is None else parsed.minor_units


def _source_arithmetic(
    gross: Optional[int], net: Optional[int], tax: Optional[int]
) -> Tuple[str, Optional[int]]:
    values = (gross, net, tax)
    if all(item is None for item in values):
        return "NOT_APPLICABLE", None
    if any(item is None for item in values):
        return "INCOMPLETE", None
    delta = int(gross) - int(net) - int(tax)
    if abs(delta) > MAX_MINOR:
        raise LifecycleReaderError("LIFECYCLE_ARITHMETIC_OVERFLOW", "source arithmetic exceeds signed 64-bit range")
    return ("BALANCED" if delta == 0 else "SOURCE_ARITHMETIC_DELTA"), delta


def _amount_control(values: Iterable[Optional[int]]) -> AmountColumnControl:
    positive = negative = zero = null = total = 0
    for value in values:
        if value is None:
            null += 1
        elif value > 0:
            positive += 1
            total += value
        elif value < 0:
            negative += 1
            total += value
        else:
            zero += 1
    if abs(total) > MAX_MINOR:
        raise LifecycleReaderError("LIFECYCLE_CONTROL_OVERFLOW", "source amount control exceeds signed 64-bit range")
    return AmountColumnControl(positive, negative, zero, null, total)


def _record_control(records: Sequence[LifecycleSourceRecord], physical: int, empty: int, failures: int) -> LifecycleReaderControl:
    exclusions = Counter(
        item.exclusion_reason_code for item in records if item.exclusion_reason_code is not None
    )
    if empty:
        exclusions["EMPTY_ROW"] += empty
    if failures:
        exclusions["PARSE_FAILURE"] += failures
    amount_controls = {
        field: _amount_control(getattr(item, field + "_minor") for item in records)
        for field in AMOUNT_FIELDS
    }
    business_amounts = {
        field: _amount_control(
            getattr(item, field + "_minor") for item in records if item.row_action == "EMIT_EVENT"
        ).total_minor
        for field in AMOUNT_FIELDS
    }
    control_amounts = {
        field: _amount_control(
            getattr(item, field + "_minor") for item in records if item.row_action == "EXCLUDE_CONTROL"
        ).total_minor
        for field in AMOUNT_FIELDS
    }
    partition_deltas = {
        field: amount_controls[field].total_minor - business_amounts[field] - control_amounts[field]
        for field in AMOUNT_FIELDS
    }
    control = LifecycleReaderControl(
        physical_data_row_count=physical,
        emitted_record_count=len(records),
        business_record_count=sum(item.row_action == "EMIT_EVENT" for item in records),
        control_record_count=sum(item.row_action == "EXCLUDE_CONTROL" for item in records),
        empty_row_count=empty,
        parse_failure_count=failures,
        source_arithmetic_anomaly_count=sum(
            item.source_arithmetic_status in {"SOURCE_ARITHMETIC_DELTA", "INCOMPLETE"} for item in records
        ),
        exclusion_counts=tuple(sorted(exclusions.items())),
        transaction_amount=amount_controls["transaction_amount"],
        gross_amount=amount_controls["gross_amount"],
        net_amount=amount_controls["net_amount"],
        tax_amount=amount_controls["tax_amount"],
        business_amount_totals=tuple(sorted(business_amounts.items())),
        control_amount_totals=tuple(sorted(control_amounts.items())),
        amount_partition_deltas=tuple(sorted(partition_deltas.items())),
        row_conservation_delta=physical - len(records) - empty - failures,
    )
    control.validate()
    return control


def _lifecycle_record(
    *,
    row_number: int,
    cells: Mapping[str, _CellValue],
    unbound_content_digest: str,
    selection: SourceSelection,
    profile: LifecycleReaderProfile,
    money_profile: MoneyProfile,
    date_1904: bool,
    sheet_ref: str,
) -> LifecycleSourceRecord:
    bindings = profile.binding_map()
    text_fields = {
        field: None if bindings[field] is None else _normalized_text(cells[field]) for field in TEXT_FIELDS
    }
    dates: Dict[str, Optional[str]] = {}
    for field in DATE_FIELDS:
        if bindings[field] is None:
            dates[field] = None
            continue
        try:
            dates[field] = _parse_date(
                cells[field], mode=profile.date_mode_map()[field], date_1904=date_1904
            )
        except LifecycleReaderError as exc:
            raise LifecycleReaderError(exc.code, exc.message, column_id=field) from exc
    amounts: Dict[str, Optional[int]] = {}
    for field in AMOUNT_FIELDS:
        if bindings[field] is None:
            amounts[field] = None
            continue
        try:
            amounts[field] = _parse_amount(cells[field], money_profile=money_profile)
        except LifecycleReaderError as exc:
            raise LifecycleReaderError(exc.code, exc.message, column_id=field) from exc
    currency = None if bindings["currency"] is None else _normalized_text(cells["currency"])
    currency = currency or profile.default_currency
    if bindings["source_row_kind"] is None:
        row_action, reason = "EMIT_EVENT", None
    else:
        row_rule = profile.row_rule_map().get(text_fields["source_row_kind"] or "")
        if row_rule is None:
            raise LifecycleReaderError("BLOCKED_ROW_KIND_POLICY", "source row kind lacks an exact profile rule")
        row_action, reason = row_rule.action, row_rule.reason_code
    gross, net, tax = amounts["gross_amount"], amounts["net_amount"], amounts["tax_amount"]
    arithmetic_status, arithmetic_delta = _source_arithmetic(gross, net, tax)
    values: Dict[str, Any] = {
        **text_fields,
        **dates,
        **amounts,
        "currency": currency,
    }
    if row_action == "EMIT_EVENT":
        for field in profile.required_business_fields:
            if values[field] is None:
                raise LifecycleReaderError(
                    "BLOCKED_REQUIRED_SOURCE_FIELD",
                    "business row is missing a profile-required field",
                    column_id=field,
                )
        if currency != "CNY":
            raise LifecycleReaderError("BLOCKED_CURRENCY", "R6 lifecycle candidate is outside CNY scope")
    business = {
        "slot_id": selection.slot_id,
        "row_action": row_action,
        "exclusion_reason_code": reason,
        **text_fields,
        **dates,
        "transaction_amount_minor": amounts["transaction_amount"],
        "gross_amount_minor": gross,
        "net_amount_minor": net,
        "tax_amount_minor": tax,
        "currency": currency,
        "source_arithmetic_status": arithmetic_status,
        "source_arithmetic_delta_minor": arithmetic_delta,
        "unbound_content_digest": unbound_content_digest,
    }
    business_digest = _canonical_digest(business)
    stable_key = _canonical_digest(
        {
            "slot_id": selection.slot_id,
            "legal_entity_source_key": text_fields["legal_entity_source_key"],
            "document_id": text_fields["document_id"],
            "document_line_id": text_fields["document_line_id"],
            "source_event_type": text_fields["source_event_type"],
            "document_date": dates["document_date"],
        }
    )
    record_ref = "rec_lifecycle_" + _canonical_digest(
        {
            "source_id": selection.source_id,
            "source_sha256": selection.sha256,
            "sheet_ref": sheet_ref,
            "row_number": row_number,
            "business_digest": business_digest,
        }
    )[:32]
    record = LifecycleSourceRecord(
        source_record_ref=record_ref,
        source_business_key_hash="lifecycle_line_" + stable_key[:32],
        normalized_business_digest=business_digest,
        unbound_content_digest=unbound_content_digest,
        source_id=selection.source_id,
        source_sha256=selection.sha256,
        slot_id=selection.slot_id,
        reader_id=selection.reader,
        reader_version=selection.reader_version,
        schema_id=selection.schema_id,
        schema_fingerprint=selection.schema_fingerprint,
        profile_sha256=profile.content_sha256,
        sheet_name=profile.sheet_name,
        sheet_ref=sheet_ref,
        row_number=row_number,
        row_action=row_action,
        exclusion_reason_code=reason,
        legal_entity_source_key=text_fields["legal_entity_source_key"],
        project_source_key=text_fields["project_source_key"],
        wbs_source_key=text_fields["wbs_source_key"],
        contract_source_key=text_fields["contract_source_key"],
        counterparty_source_key=text_fields["counterparty_source_key"],
        document_id=text_fields["document_id"],
        document_line_id=text_fields["document_line_id"],
        source_event_type=text_fields["source_event_type"],
        source_status=text_fields["source_status"],
        source_row_kind=text_fields["source_row_kind"],
        reversal_of_source_key=text_fields["reversal_of_source_key"],
        free_text=text_fields["free_text"],
        document_date=dates["document_date"],
        approval_date=dates["approval_date"],
        invoice_date=dates["invoice_date"],
        payment_date=dates["payment_date"],
        collection_date=dates["collection_date"],
        effective_date=dates["effective_date"],
        reversal_date=dates["reversal_date"],
        transaction_amount_minor=amounts["transaction_amount"],
        gross_amount_minor=gross,
        net_amount_minor=net,
        tax_amount_minor=tax,
        currency=currency,
        source_arithmetic_status=arithmetic_status,
        source_arithmetic_delta_minor=arithmetic_delta,
    )
    record.validate()
    return record


def _checked_multiply(value: Optional[int], multiplier: int) -> Optional[int]:
    if value is None:
        return None
    result = value * multiplier
    if abs(result) > MAX_MINOR:
        raise LifecycleReaderError("LIFECYCLE_EVENT_OVERFLOW", "mapped event amount exceeds signed 64-bit range")
    return result


def _event_for_record(
    record: LifecycleSourceRecord,
    *,
    export_business_fingerprint: str,
    profile: LifecycleReaderProfile,
) -> EconomicEventCandidate:
    if record.row_action != "EMIT_EVENT" or record.transaction_amount_minor is None or record.currency is None:
        raise LifecycleReaderError("LIFECYCLE_EVENT_SOURCE_INVALID", "only complete business rows can create candidates")
    if profile.binding_map()["source_event_type"] is None:
        rule = profile.default_event_rule
    else:
        rule = profile.event_rule_map().get(record.source_event_type or "")
    if rule is None:
        raise LifecycleReaderError("BLOCKED_EVENT_TYPE_POLICY", "source event type lacks an exact profile rule")
    status_rule = profile.status_rule_map().get(record.source_status or "")
    if status_rule is None:
        raise LifecycleReaderError("BLOCKED_STATUS_POLICY", "source status lacks an exact profile rule")
    multiplier = rule.amount_multiplier
    transaction_amount = _checked_multiply(record.transaction_amount_minor, multiplier)
    if transaction_amount is None:
        raise LifecycleReaderError("LIFECYCLE_EVENT_AMOUNT_MISSING", "business event amount cannot be null")
    delta = _checked_multiply(record.source_arithmetic_delta_minor, multiplier)
    id_payload = {
        "export_business_fingerprint": export_business_fingerprint,
        "source_business_key_hash": record.source_business_key_hash,
        "source_business_digest": record.normalized_business_digest,
        "mapping_rule_ref": rule.rule_ref,
        "event_type": rule.event_type,
        "direction": rule.direction.value,
        "lifecycle_stage": rule.lifecycle_stage.value,
        "event_status": status_rule.event_status.value,
        "transaction_amount_minor": transaction_amount,
    }
    event = EconomicEventCandidate(
        economic_event_id=event_id_for_payload(id_payload),
        export_business_fingerprint=export_business_fingerprint,
        source_business_key_hash=record.source_business_key_hash,
        source_business_digest=record.normalized_business_digest,
        mapping_rule_ref=rule.rule_ref,
        profile_sha256=profile.content_sha256,
        event_type=rule.event_type,
        direction=rule.direction,
        lifecycle_stage=rule.lifecycle_stage,
        event_status=status_rule.event_status,
        legal_entity_source_key=record.legal_entity_source_key,
        project_source_key=record.project_source_key,
        wbs_source_key=record.wbs_source_key,
        contract_source_key=record.contract_source_key,
        counterparty_source_key=record.counterparty_source_key,
        document_id=record.document_id,
        document_line_id=record.document_line_id,
        document_date=record.document_date,
        approval_date=record.approval_date,
        invoice_date=record.invoice_date,
        payment_date=record.payment_date,
        collection_date=record.collection_date,
        effective_date=record.effective_date,
        reversal_date=record.reversal_date,
        transaction_amount_minor=transaction_amount,
        gross_amount_minor=_checked_multiply(record.gross_amount_minor, multiplier),
        net_amount_minor=_checked_multiply(record.net_amount_minor, multiplier),
        tax_amount_minor=_checked_multiply(record.tax_amount_minor, multiplier),
        transaction_currency=record.currency,
        tax_recoverability="UNKNOWN",
        source_arithmetic_status=record.source_arithmetic_status,
        source_arithmetic_delta_minor=delta,
        reversal_of_source_key=record.reversal_of_source_key,
        free_text_candidate_present=record.free_text is not None,
        identity_status="PENDING_IDENTITY",
        metric_inclusion_status="NOT_EVALUATED_R6",
        source_record_refs=(record.source_record_ref,),
    )
    try:
        event.validate()
    except EconomicEventError as exc:
        raise LifecycleReaderError(exc.code, exc.message) from exc
    return event


def _parse_xlsx(
    source: BinaryIO,
    *,
    selection: SourceSelection,
    profile: LifecycleReaderProfile,
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
) -> Tuple[Tuple[LifecycleSourceRecord, ...], LifecycleReaderControl]:
    try:
        context = zipfile.ZipFile(source)
    except zipfile.BadZipFile as exc:
        raise LifecycleReaderError("LIFECYCLE_XLSX_INVALID", "preflighted workbook cannot be reopened") from exc
    with context as archive:
        sheet_part, date_1904 = _workbook_sheet(archive, profile=profile, security_profile=security_profile)
        sheet_ref = "sheet_" + hashlib.sha256(sheet_part.encode("utf-8")).hexdigest()[:16]
        worksheet = _read_xml(archive, sheet_part, security_profile)
        shared = _shared_strings(archive, security_profile)
        rows: Dict[int, Dict[int, _CellValue]] = {}
        for row in worksheet.iter():
            if _local_name(row.tag) != "row":
                continue
            try:
                row_number = int(row.attrib.get("r", ""))
            except ValueError as exc:
                raise LifecycleReaderError("LIFECYCLE_XLSX_ROW_REF", "row reference is invalid") from exc
            if row_number in rows:
                raise LifecycleReaderError("LIFECYCLE_XLSX_DUPLICATE_ROW", "worksheet repeats a row reference")
            values: Dict[int, _CellValue] = {}
            for cell in row:
                if _local_name(cell.tag) != "c":
                    continue
                column, cell_row = _column_index(cell.attrib.get("r", ""))
                if cell_row != row_number or column in values:
                    raise LifecycleReaderError("LIFECYCLE_XLSX_CELL_REF", "cell reference conflicts with its row")
                values[column] = _cell_value(cell, shared)
            rows[row_number] = values
        header_cells = rows.get(profile.header_row)
        if header_cells is None:
            raise LifecycleReaderError("LIFECYCLE_HEADER_MISSING", "locked header row is absent")
        header_by_column = {
            column: _normalized_text(value)
            for column, value in sorted(header_cells.items())
            if _normalized_text(value) is not None
        }
        actual_headers = tuple(header_by_column.values())
        if len(actual_headers) != len(set(actual_headers)):
            raise LifecycleReaderError("LIFECYCLE_DUPLICATE_HEADER", "header labels must be unique")
        if actual_headers != profile.expected_headers:
            raise LifecycleReaderError("LIFECYCLE_SCHEMA_DRIFT", "header sequence differs from the active profile")
        column_by_header = {header: column for column, header in header_by_column.items()}
        binding_map = profile.binding_map()
        field_columns = {
            field: None if header is None else column_by_header[header] for field, header in binding_map.items()
        }
        bound_columns = {column for column in field_columns.values() if column is not None}
        physical = empty = 0
        records = []
        for row_number in sorted(rows):
            if row_number < profile.first_data_row:
                continue
            physical += 1
            if physical > profile.max_data_rows:
                raise LifecycleReaderError("LIFECYCLE_ROW_LIMIT", "workbook exceeds the locked row ceiling")
            row_values = rows[row_number]
            all_schema_cells = {
                header: row_values.get(column, _CellValue(None, "blank"))
                for column, header in header_by_column.items()
            }
            if all(_normalized_text(value) is None for value in all_schema_cells.values()):
                empty += 1
                continue
            cells = {
                field: _CellValue(None, "blank") if column is None else row_values.get(column, _CellValue(None, "blank"))
                for field, column in field_columns.items()
            }
            unbound = {
                header: _normalized_text(value)
                for column, header in header_by_column.items()
                if column not in bound_columns
                for value in (row_values.get(column, _CellValue(None, "blank")),)
            }
            try:
                records.append(
                    _lifecycle_record(
                        row_number=row_number,
                        cells=cells,
                        unbound_content_digest=_canonical_digest(unbound),
                        selection=selection,
                        profile=profile,
                        money_profile=money_profile,
                        date_1904=date_1904,
                        sheet_ref=sheet_ref,
                    )
                )
            except LifecycleReaderError as exc:
                partial = _record_control(records, physical, empty, 1)
                raise LifecycleReaderError(
                    exc.code,
                    exc.message,
                    row_number=row_number,
                    column_id=exc.column_id,
                    partial_control=partial,
                ) from exc
    result = tuple(records)
    return result, _record_control(result, physical, empty, 0)


def _hash_open_file(handle: BinaryIO) -> str:
    handle.seek(0)
    digest = hashlib.sha256()
    for block in iter(lambda: handle.read(1024 * 1024), b""):
        digest.update(block)
    handle.seek(0)
    return digest.hexdigest()


def read_lifecycle_source(
    *,
    input_root: Path,
    selection: SourceSelection,
    reader_profile: LifecycleReaderProfile,
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
) -> LifecycleReaderResult:
    """Read one explicitly selected R6 source; no final Metric inclusion occurs here."""

    reader_profile.validate(require_active=True)
    if selection.slot_id != reader_profile.slot_id:
        raise LifecycleReaderError("LIFECYCLE_SLOT_MISMATCH", "selection slot differs from the active profile")
    if selection.reader != reader_profile.reader_id or selection.reader_version != reader_profile.reader_version:
        raise LifecycleReaderError("LIFECYCLE_READER_DRIFT", "selection reader binding differs from the profile")
    if selection.schema_id != reader_profile.schema_id or selection.schema_fingerprint != reader_profile.schema_fingerprint:
        raise LifecycleReaderError("LIFECYCLE_SCHEMA_BINDING_DRIFT", "selection schema differs from the profile")
    suffix = Path(selection.private_relative_path).suffix.casefold()
    expected_kind = "xlsx" if suffix == ".xlsx" else "xls" if suffix == ".xls" else ""
    if not expected_kind:
        raise LifecycleReaderError("LIFECYCLE_FILE_TYPE", "R6 source must be XLSX or an explicitly blocked legacy XLS")
    try:
        preflight = preflight_source_file(
            input_root,
            Path(selection.private_relative_path),
            expected_kind=expected_kind,
            profile=security_profile,
        )
    except FileSecurityError as exc:
        raise LifecycleReaderError(exc.code, exc.message) from exc
    if preflight.sha256 != selection.sha256:
        raise LifecycleReaderError("LIFECYCLE_SOURCE_DIGEST_DRIFT", "preflight digest differs from selection")
    try:
        source_path = resolve_input_file(
            input_root,
            Path(selection.private_relative_path),
            max_bytes=security_profile.source_file_bytes_max,
        )
    except PathSafetyError as exc:
        raise LifecycleReaderError(exc.code, exc.message) from exc
    try:
        with source_path.open("rb") as handle:
            before = os.fstat(handle.fileno())
            selected = selection.identity
            if (
                not stat.S_ISREG(before.st_mode)
                or before.st_nlink != 1
                or before.st_dev != selected.device
                or before.st_ino != selected.inode
                or before.st_size != selected.size_bytes
                or before.st_mtime_ns != selected.mtime_ns
                or before.st_nlink != selected.link_count
            ):
                raise LifecycleReaderError("LIFECYCLE_SELECTION_IDENTITY_DRIFT", "source identity differs from selection")
            first_hash = _hash_open_file(handle)
            if first_hash != selection.sha256 or before.st_size != preflight.size_bytes:
                raise LifecycleReaderError("LIFECYCLE_SOURCE_CHANGED_AFTER_PREFLIGHT", "source changed after preflight")
            records, control = _parse_xlsx(
                handle,
                selection=selection,
                profile=reader_profile,
                security_profile=security_profile,
                money_profile=money_profile,
            )
            final_hash = _hash_open_file(handle)
            after = os.fstat(handle.fileno())
    except LifecycleReaderError:
        raise
    except OSError as exc:
        raise LifecycleReaderError("LIFECYCLE_SOURCE_READ", "source cannot be read safely") from exc
    identity_before = (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_nlink)
    identity_after = (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_nlink)
    if final_hash != selection.sha256 or identity_after != identity_before:
        raise LifecycleReaderError("LIFECYCLE_SOURCE_CHANGED_DURING_PARSE", "source changed during parse")
    business_fingerprint = _canonical_digest(
        {
            "slot_id": selection.slot_id,
            "reader_id": reader_profile.reader_id,
            "reader_version": reader_profile.reader_version,
            "profile_sha256": reader_profile.content_sha256,
            "schema_fingerprint": reader_profile.schema_fingerprint,
            "record_business_digests": sorted(item.normalized_business_digest for item in records),
        }
    )
    events = tuple(
        sorted(
            (
                _event_for_record(item, export_business_fingerprint=business_fingerprint, profile=reader_profile)
                for item in records
                if item.row_action == "EMIT_EVENT"
            ),
            key=lambda item: item.economic_event_id,
        )
    )
    if not events:
        raise LifecycleReaderError("LIFECYCLE_NO_BUSINESS_EVENTS", "selected source contains no business event rows")
    if len({item.economic_event_id for item in events}) != len(events):
        raise LifecycleReaderError(
            "LIFECYCLE_DUPLICATE_EVENT_WITHIN_EXPORT",
            "duplicate business event candidates inside one export require R7 handling",
        )
    return LifecycleReaderResult(
        records=records,
        events=events,
        control=control,
        source_sha256=selection.sha256,
        profile_sha256=reader_profile.content_sha256,
        schema_fingerprint=reader_profile.schema_fingerprint,
        business_fingerprint=business_fingerprint,
    )


def read_lifecycle_batch(
    *,
    input_root: Path,
    selections: Sequence[SourceSelection],
    reader_profiles: Mapping[str, LifecycleReaderProfile],
    security_profile: SecurityProfile,
    money_profile: MoneyProfile,
) -> LifecycleBatchResult:
    """Read an explicit source batch and merge only exact whole-export business duplicates."""

    if not selections:
        raise LifecycleReaderError("LIFECYCLE_BATCH_EMPTY", "R6 batch requires at least one selected source")
    selection_keys = [(item.slot_id, item.source_id) for item in selections]
    if len(selection_keys) != len(set(selection_keys)):
        raise LifecycleReaderError("LIFECYCLE_BATCH_SELECTION_DUPLICATE", "selected source batch contains duplicates")
    results_by_key: Dict[Tuple[str, str], LifecycleReaderResult] = {}
    selection_by_key = {(item.slot_id, item.source_id): item for item in selections}
    for selection in sorted(selections, key=lambda item: (item.slot_id, item.source_id)):
        profile = reader_profiles.get(selection.reader)
        if profile is None:
            raise LifecycleReaderError("LIFECYCLE_BATCH_PROFILE_MISSING", "selected reader lacks its active profile")
        results_by_key[(selection.slot_id, selection.source_id)] = read_lifecycle_source(
            input_root=input_root,
            selection=selection,
            reader_profile=profile,
            security_profile=security_profile,
            money_profile=money_profile,
        )
    groups: Dict[Tuple[str, str], list[Tuple[SourceSelection, LifecycleReaderResult]]] = {}
    for key, result in results_by_key.items():
        selection = selection_by_key[key]
        groups.setdefault((selection.slot_id, result.business_fingerprint), []).append((selection, result))
    merged_events = []
    duplicate_groups = []
    suppressed_event_count = 0
    suppressed_event_amount = 0
    for (slot_id, fingerprint), group in sorted(groups.items()):
        ordered = sorted(group, key=lambda item: item[0].source_id)
        canonical_selection, canonical_result = ordered[0]
        canonical_map = {item.economic_event_id: item for item in canonical_result.events}
        for _, alias_result in ordered[1:]:
            alias_map = {item.economic_event_id: item for item in alias_result.events}
            if set(alias_map) != set(canonical_map):
                raise LifecycleReaderError(
                    "LIFECYCLE_DUPLICATE_EXPORT_INCONSISTENT",
                    "equal export fingerprints produced inconsistent event sets",
                )
            suppressed_event_count += len(alias_result.events)
            suppressed_event_amount += sum(item.transaction_amount_minor for item in alias_result.events)
            if abs(suppressed_event_amount) > MAX_MINOR:
                raise LifecycleReaderError("LIFECYCLE_BATCH_OVERFLOW", "suppressed event total exceeds signed 64-bit range")
            for event_id, alias_event in alias_map.items():
                canonical = canonical_map[event_id]
                canonical_map[event_id] = replace(
                    canonical,
                    source_record_refs=tuple(sorted(set(canonical.source_record_refs + alias_event.source_record_refs))),
                )
                try:
                    canonical_map[event_id].validate()
                except EconomicEventError as exc:
                    raise LifecycleReaderError(exc.code, exc.message) from exc
        merged_events.extend(canonical_map.values())
        if len(ordered) > 1:
            duplicate_groups.append(
                DuplicateExportGroup(
                    slot_id=slot_id,
                    business_fingerprint=fingerprint,
                    canonical_source_id=canonical_selection.source_id,
                    alias_source_ids=tuple(item[0].source_id for item in ordered[1:]),
                    event_count=len(canonical_map),
                )
            )
    all_results = tuple(results_by_key[key] for key in sorted(results_by_key))
    all_records = tuple(item for result in all_results for item in result.records)
    final_events = tuple(sorted(merged_events, key=lambda item: item.economic_event_id))
    pre_dedup_count = sum(len(item.events) for item in all_results)
    pre_dedup_amount = sum(event.transaction_amount_minor for item in all_results for event in item.events)
    emitted_amount = sum(item.transaction_amount_minor for item in final_events)
    for value in (pre_dedup_amount, emitted_amount, suppressed_event_amount):
        if abs(value) > MAX_MINOR:
            raise LifecycleReaderError("LIFECYCLE_BATCH_OVERFLOW", "batch event total exceeds signed 64-bit range")
    lifecycle_counts = Counter("%s:%s" % (item.direction.value, item.lifecycle_stage.value) for item in final_events)
    control = LifecycleBatchControl(
        selected_source_count=len(all_results),
        unique_export_count=len(groups),
        duplicate_alias_count=len(all_results) - len(groups),
        source_record_count=len(all_records),
        pre_dedup_event_count=pre_dedup_count,
        emitted_event_count=len(final_events),
        duplicate_suppressed_event_count=suppressed_event_count,
        source_row_conservation_delta=sum(item.control.row_conservation_delta for item in all_results),
        event_count_conservation_delta=pre_dedup_count - len(final_events) - suppressed_event_count,
        event_amount_conservation_delta_minor=pre_dedup_amount - emitted_amount - suppressed_event_amount,
        source_arithmetic_anomaly_count=sum(
            item.control.source_arithmetic_anomaly_count for item in all_results
        ),
        lifecycle_counts=tuple(sorted(lifecycle_counts.items())),
    )
    control.validate()
    batch_fingerprint = _canonical_digest(
        {
            "unique_export_fingerprints": sorted((slot_id, fingerprint) for slot_id, fingerprint in groups),
            "event_ids": [item.economic_event_id for item in final_events],
        }
    )
    return LifecycleBatchResult(
        records=all_records,
        events=final_events,
        duplicate_export_groups=tuple(duplicate_groups),
        source_results=all_results,
        control=control,
        business_fingerprint=batch_fingerprint,
    )


def public_lifecycle_reader_summary(result: LifecycleReaderResult) -> Dict[str, Any]:
    result.control.validate()
    return {
        "schema_version": "kmfa.project_cost.public_lifecycle_reader_summary.v1",
        "status": "R6_SOURCE_READER_PASS_NOT_FINAL",
        "reader_version": LIFECYCLE_READER_VERSION,
        **result.control.public_counts(),
        "event_candidate_count": len(result.events),
    }


def public_lifecycle_batch_summary(result: LifecycleBatchResult) -> Dict[str, Any]:
    result.control.validate()
    return {
        "schema_version": "kmfa.project_cost.public_lifecycle_batch_summary.v1",
        "status": "R6_LIFECYCLE_CANDIDATES_NOT_FINAL",
        "selected_source_count": result.control.selected_source_count,
        "unique_export_count": result.control.unique_export_count,
        "duplicate_alias_count": result.control.duplicate_alias_count,
        "duplicate_group_count": len(result.duplicate_export_groups),
        "source_record_count": result.control.source_record_count,
        "pre_dedup_event_count": result.control.pre_dedup_event_count,
        "event_candidate_count": result.control.emitted_event_count,
        "duplicate_suppressed_event_count": result.control.duplicate_suppressed_event_count,
        "source_row_conservation_delta": result.control.source_row_conservation_delta,
        "event_count_conservation_delta": result.control.event_count_conservation_delta,
        "event_amount_conservation_delta_minor": result.control.event_amount_conservation_delta_minor,
        "source_arithmetic_anomaly_count": result.control.source_arithmetic_anomaly_count,
        "lifecycle_counts": dict(result.control.lifecycle_counts),
    }
