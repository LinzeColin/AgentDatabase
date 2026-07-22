"""Evidence-backed 5001/6401/WIP bridge and two non-combinable cost bases."""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .config_io import GovernedConfigError, load_governed_yaml_mapping
from .identity import ProjectIdentityRecord
from .readers.kingdee import KingdeeLedgerRecord, KingdeeReaderError


ACCOUNTING_POLICY_BYTES_MAX = 1024 * 1024
EVIDENCE_REF_RE = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
IDENTITY_REF_RE = re.compile(r"^identity_record_[0-9a-f]{32}$")
SNAPSHOT_REF_RE = re.compile(r"^snapshot_[0-9a-f]{32}$")
LEDGER_LINE_KEY_RE = re.compile(r"^ledger_line_[0-9a-f]{32}$")
SOURCE_RECORD_REF_RE = re.compile(r"^rec_source_[0-9a-f]{32}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_ABS_MINOR_UNITS = 9223372036854775807


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical_json(value)).hexdigest()


def _iso_date(value: Any, field_name: str, *, optional: bool = False) -> Optional[date]:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "%s must be an ISO date" % field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "%s must be an ISO date" % field_name) from exc


def _text(value: Any, field_name: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value or value != value.strip() or unicodedata.normalize("NFC", value) != value:
        raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "%s must be nonempty normalized text" % field_name)
    return value


def _strings(value: Any, field_name: str, *, allow_empty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "%s must be a string list" % field_name)
    result = tuple(value)
    if (not allow_empty and not result) or len(result) != len(set(result)):
        raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "%s must be nonempty and unique" % field_name)
    for item in result:
        _text(item, field_name)
    return result


class AccountingBasisError(ValueError):
    """Fail-closed accounting result; private diagnostics are never serialized by default."""

    def __init__(
        self,
        code: str,
        message: str,
        *,
        private_diagnostics: Tuple["WipBridge", ...] = (),
    ) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.private_diagnostics = private_diagnostics

    def as_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "diagnostic_group_count": len(self.private_diagnostics),
        }


class BasisId(str, Enum):
    JOB_COST_INCURRED = "JOB_COST_INCURRED"
    GL_RECOGNIZED_COGS = "GL_RECOGNIZED_COGS"


class LedgerSemantic(str, Enum):
    WIP_OPENING = "WIP_OPENING"
    WIP_CLOSING = "WIP_CLOSING"
    WIP_ADDITION = "WIP_ADDITION"
    WIP_ADJUSTMENT = "WIP_ADJUSTMENT"
    WIP_TRANSFER_IN = "WIP_TRANSFER_IN"
    WIP_REVERSAL = "WIP_REVERSAL"
    WIP_OTHER_TRANSFER_OUT = "WIP_OTHER_TRANSFER_OUT"
    WIP_TO_COGS_TRANSFER = "WIP_TO_COGS_TRANSFER"
    WIP_FROM_COGS_REVERSAL = "WIP_FROM_COGS_REVERSAL"
    COGS_RECOGNITION = "COGS_RECOGNITION"
    COGS_REVERSAL = "COGS_REVERSAL"
    EXCLUDE_CONTROL = "EXCLUDE_CONTROL"


DEBIT_SEMANTICS = frozenset(
    {
        LedgerSemantic.WIP_ADDITION,
        LedgerSemantic.WIP_ADJUSTMENT,
        LedgerSemantic.WIP_TRANSFER_IN,
        LedgerSemantic.WIP_FROM_COGS_REVERSAL,
        LedgerSemantic.COGS_RECOGNITION,
    }
)
CREDIT_SEMANTICS = frozenset(
    {
        LedgerSemantic.WIP_REVERSAL,
        LedgerSemantic.WIP_OTHER_TRANSFER_OUT,
        LedgerSemantic.WIP_TO_COGS_TRANSFER,
        LedgerSemantic.COGS_REVERSAL,
    }
)
CORE_ACTIVE_SEMANTICS = frozenset(
    {
        LedgerSemantic.WIP_OPENING,
        LedgerSemantic.WIP_CLOSING,
        LedgerSemantic.WIP_ADDITION,
        LedgerSemantic.WIP_TO_COGS_TRANSFER,
        LedgerSemantic.COGS_RECOGNITION,
    }
)


@dataclass(frozen=True)
class StatusRule:
    source_status: str
    action: str
    reason_code: str
    evidence_ref: Optional[str]

    def validate(self, *, active: bool) -> None:
        _text(self.source_status, "source_status")
        if self.action not in {"INCLUDE", "EXCLUDE"}:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "status action must be INCLUDE or EXCLUDE")
        _text(self.reason_code, "reason_code")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "status evidence reference is not hash-bound")
        if active and self.evidence_ref is None:
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "every active status rule requires evidence")


@dataclass(frozen=True)
class RowKindRule:
    source_row_kind: str
    semantic: LedgerSemantic
    evidence_ref: Optional[str]

    def validate(self, *, active: bool) -> None:
        _text(self.source_row_kind, "source_row_kind")
        if not isinstance(self.semantic, LedgerSemantic):
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "row semantic is not registered")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "row-kind evidence reference is not hash-bound")
        if active and self.evidence_ref is None:
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "every active row-kind rule requires evidence")


@dataclass(frozen=True)
class AccountRule:
    account_code: str
    bridge_group_id: str
    valid_from: str
    valid_to: Optional[str]
    allowed_semantics: Tuple[LedgerSemantic, ...]
    evidence_ref: Optional[str]

    def validate(self, *, active: bool) -> None:
        _text(self.account_code, "account_code")
        _text(self.bridge_group_id, "bridge_group_id")
        start = _iso_date(self.valid_from, "account_rule.valid_from")
        end = _iso_date(self.valid_to, "account_rule.valid_to", optional=True)
        if end is not None and end < start:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "account-rule effective period is reversed")
        if not isinstance(self.allowed_semantics, tuple) or not self.allowed_semantics:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "account rule needs immutable allowed semantics")
        if len(self.allowed_semantics) != len(set(self.allowed_semantics)) or any(
            not isinstance(item, LedgerSemantic) for item in self.allowed_semantics
        ):
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "account allowed semantics are invalid")
        if self.evidence_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.evidence_ref):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "account evidence reference is not hash-bound")
        if active and self.evidence_ref is None:
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "every active account rule requires evidence")

    def active_at(self, value: date) -> bool:
        start = _iso_date(self.valid_from, "account_rule.valid_from")
        end = _iso_date(self.valid_to, "account_rule.valid_to", optional=True) or date.max
        return bool(start <= value <= end)


@dataclass(frozen=True)
class PeriodPolicy:
    calendar_id: str
    closed_through: Optional[str]
    late_posting_mode: str

    def validate(self) -> None:
        _text(self.calendar_id, "calendar_id")
        _iso_date(self.closed_through, "closed_through", optional=True)
        if self.late_posting_mode != "REQUIRE_BOUND_PRIOR_SNAPSHOT_FOR_CLOSED_PERIOD":
            raise AccountingBasisError("ACCOUNTING_POLICY_PERIOD", "late-posting policy cannot be relaxed")


@dataclass(frozen=True)
class AccountingBasisPolicy:
    policy_id: str
    policy_version: str
    status: str
    effective_from: str
    effective_to: Optional[str]
    base_currency: str
    evidence_refs: Tuple[str, ...]
    valuation_policy_ref: Optional[str]
    blank_counter_side_as_zero: bool
    wip_to_cogs_control_required: bool
    status_rules: Tuple[StatusRule, ...]
    row_kind_rules: Tuple[RowKindRule, ...]
    account_rules: Tuple[AccountRule, ...]
    period_policy: PeriodPolicy
    content_sha256: str

    def validate(self, *, require_active: bool = False) -> None:
        for field_name in ("policy_id", "policy_version"):
            _text(getattr(self, field_name), field_name)
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise AccountingBasisError("ACCOUNTING_POLICY_STATUS", "accounting policy status is not registered")
        start = _iso_date(self.effective_from, "effective_from")
        end = _iso_date(self.effective_to, "effective_to", optional=True)
        if end is not None and end < start:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "policy effective period is reversed")
        if self.base_currency != "CNY":
            raise AccountingBasisError("BLOCKED_CURRENCY", "product 0.2 requires CNY accounting policy")
        if type(self.blank_counter_side_as_zero) is not bool or type(self.wip_to_cogs_control_required) is not bool:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "accounting switches require exact booleans")
        if require_active and self.wip_to_cogs_control_required is not True:
            raise AccountingBasisError("ACCOUNTING_POLICY_RELAXED", "5001-to-6401 transfer control is non-waivable")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise AccountingBasisError("ACCOUNTING_POLICY_HASH", "accounting policy hash is invalid")
        refs = _strings(self.evidence_refs, "evidence_refs")
        if refs != self.evidence_refs or any(not EVIDENCE_REF_RE.fullmatch(item) for item in refs):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "policy evidence references must be hash-bound")
        if self.valuation_policy_ref is not None and not EVIDENCE_REF_RE.fullmatch(self.valuation_policy_ref):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "valuation policy reference must be hash-bound")
        active = self.status == "ACTIVE"
        if require_active and not active:
            raise AccountingBasisError("ACCOUNTING_POLICY_NOT_ACTIVE", "an evidence-backed ACTIVE accounting policy is required")
        if active and (not refs or self.valuation_policy_ref is None):
            raise AccountingBasisError("ACCOUNTING_POLICY_EVIDENCE", "active accounting and valuation policies require evidence")
        if not self.status_rules or not self.row_kind_rules or not self.account_rules:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "accounting policy rule sets cannot be empty")
        if len({item.source_status for item in self.status_rules}) != len(self.status_rules):
            raise AccountingBasisError("ACCOUNTING_POLICY_CONFLICT", "source status has multiple actions")
        if len({item.source_row_kind for item in self.row_kind_rules}) != len(self.row_kind_rules):
            raise AccountingBasisError("ACCOUNTING_POLICY_CONFLICT", "source row kind has multiple semantics")
        for rule in self.status_rules:
            rule.validate(active=active)
        for rule in self.row_kind_rules:
            rule.validate(active=active)
        for rule in self.account_rules:
            rule.validate(active=active)
        for left_index, left in enumerate(self.account_rules):
            left_start = _iso_date(left.valid_from, "account_rule.valid_from")
            left_end = _iso_date(left.valid_to, "account_rule.valid_to", optional=True) or date.max
            for right in self.account_rules[left_index + 1 :]:
                if left.account_code != right.account_code:
                    continue
                right_start = _iso_date(right.valid_from, "account_rule.valid_from")
                right_end = _iso_date(right.valid_to, "account_rule.valid_to", optional=True) or date.max
                if max(left_start, right_start) <= min(left_end, right_end):
                    raise AccountingBasisError("ACCOUNTING_POLICY_CONFLICT", "account rules overlap in effective time")
        self.period_policy.validate()
        if active:
            semantics = {item.semantic for item in self.row_kind_rules}
            if not CORE_ACTIVE_SEMANTICS.issubset(semantics):
                raise AccountingBasisError("ACCOUNTING_POLICY_INCOMPLETE", "active policy lacks required WIP/COGS semantics")
            allowed = {semantic for rule in self.account_rules for semantic in rule.allowed_semantics}
            if not semantics.difference({LedgerSemantic.EXCLUDE_CONTROL}).issubset(allowed):
                raise AccountingBasisError("ACCOUNTING_POLICY_INCOMPLETE", "row semantics are not covered by account rules")
            if not any(item.action == "INCLUDE" for item in self.status_rules):
                raise AccountingBasisError("ACCOUNTING_POLICY_INCOMPLETE", "active policy lacks an includable source status")
            group_semantics: Dict[str, set] = defaultdict(set)
            for rule in self.account_rules:
                group_semantics[rule.bridge_group_id].update(rule.allowed_semantics)
            if any(not CORE_ACTIVE_SEMANTICS.issubset(values) for values in group_semantics.values()):
                raise AccountingBasisError(
                    "ACCOUNTING_POLICY_INCOMPLETE",
                    "every active bridge group must cover opening, closing, WIP addition, transfer and COGS recognition",
                )

    def status_map(self) -> Dict[str, StatusRule]:
        return {item.source_status: item for item in self.status_rules}

    def row_kind_map(self) -> Dict[str, RowKindRule]:
        return {item.source_row_kind: item for item in self.row_kind_rules}

    def account_rule(self, account_code: str, valid_at: date) -> AccountRule:
        matches = [item for item in self.account_rules if item.account_code == account_code and item.active_at(valid_at)]
        if len(matches) != 1:
            raise AccountingBasisError("BLOCKED_ACCOUNT_POLICY", "account mapping must resolve exactly once at posting date")
        return matches[0]

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any], *, content_sha256: Optional[str] = None) -> "AccountingBasisPolicy":
        expected = {
            "schema_version",
            "policy_id",
            "policy_version",
            "status",
            "effective_from",
            "effective_to",
            "base_currency",
            "evidence_refs",
            "valuation_policy_ref",
            "blank_counter_side_as_zero",
            "wip_to_cogs_control_required",
            "status_rules",
            "row_kind_rules",
            "account_rules",
            "period_policy",
        }
        if not isinstance(raw, Mapping) or set(raw) != expected or raw.get("schema_version") != "kmfa.project_cost.accounting_basis_policy.v1":
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "accounting policy fields differ from v1")
        status_rules_raw = raw.get("status_rules")
        row_rules_raw = raw.get("row_kind_rules")
        account_rules_raw = raw.get("account_rules")
        period_raw = raw.get("period_policy")
        if not isinstance(status_rules_raw, list) or not isinstance(row_rules_raw, list) or not isinstance(account_rules_raw, list):
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "accounting rules must be lists")
        if not isinstance(period_raw, Mapping) or set(period_raw) != {"calendar_id", "closed_through", "late_posting_mode"}:
            raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "period policy fields differ from v1")
        status_rules = []
        for item in status_rules_raw:
            if not isinstance(item, Mapping) or set(item) != {"source_status", "action", "reason_code", "evidence_ref"}:
                raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "status-rule fields differ from v1")
            status_rules.append(
                StatusRule(
                    source_status=_text(item.get("source_status"), "source_status") or "",
                    action=_text(item.get("action"), "action") or "",
                    reason_code=_text(item.get("reason_code"), "reason_code") or "",
                    evidence_ref=_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            )
        row_rules = []
        for item in row_rules_raw:
            if not isinstance(item, Mapping) or set(item) != {"source_row_kind", "semantic", "evidence_ref"}:
                raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "row-kind-rule fields differ from v1")
            try:
                semantic = LedgerSemantic(item.get("semantic"))
            except (TypeError, ValueError) as exc:
                raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "row semantic is not registered") from exc
            row_rules.append(
                RowKindRule(
                    source_row_kind=_text(item.get("source_row_kind"), "source_row_kind") or "",
                    semantic=semantic,
                    evidence_ref=_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            )
        account_rules = []
        for item in account_rules_raw:
            if not isinstance(item, Mapping) or set(item) != {
                "account_code",
                "bridge_group_id",
                "valid_from",
                "valid_to",
                "allowed_semantics",
                "evidence_ref",
            }:
                raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "account-rule fields differ from v1")
            raw_semantics = _strings(item.get("allowed_semantics"), "allowed_semantics", allow_empty=False)
            try:
                semantics = tuple(LedgerSemantic(value) for value in raw_semantics)
            except ValueError as exc:
                raise AccountingBasisError("ACCOUNTING_POLICY_SCHEMA", "account semantic is not registered") from exc
            account_rules.append(
                AccountRule(
                    account_code=_text(item.get("account_code"), "account_code") or "",
                    bridge_group_id=_text(item.get("bridge_group_id"), "bridge_group_id") or "",
                    valid_from=_text(item.get("valid_from"), "valid_from") or "",
                    valid_to=_text(item.get("valid_to"), "valid_to", optional=True),
                    allowed_semantics=semantics,
                    evidence_ref=_text(item.get("evidence_ref"), "evidence_ref", optional=True),
                )
            )
        policy = cls(
            policy_id=_text(raw.get("policy_id"), "policy_id") or "",
            policy_version=_text(raw.get("policy_version"), "policy_version") or "",
            status=_text(raw.get("status"), "status") or "",
            effective_from=_text(raw.get("effective_from"), "effective_from") or "",
            effective_to=_text(raw.get("effective_to"), "effective_to", optional=True),
            base_currency=_text(raw.get("base_currency"), "base_currency") or "",
            evidence_refs=_strings(raw.get("evidence_refs"), "evidence_refs"),
            valuation_policy_ref=_text(raw.get("valuation_policy_ref"), "valuation_policy_ref", optional=True),
            blank_counter_side_as_zero=raw.get("blank_counter_side_as_zero"),
            wip_to_cogs_control_required=raw.get("wip_to_cogs_control_required"),
            status_rules=tuple(status_rules),
            row_kind_rules=tuple(row_rules),
            account_rules=tuple(account_rules),
            period_policy=PeriodPolicy(
                calendar_id=_text(period_raw.get("calendar_id"), "calendar_id") or "",
                closed_through=_text(period_raw.get("closed_through"), "closed_through", optional=True),
                late_posting_mode=_text(period_raw.get("late_posting_mode"), "late_posting_mode") or "",
            ),
            content_sha256=content_sha256 or _digest(raw),
        )
        policy.validate()
        return policy

    @classmethod
    def from_yaml(cls, path: Path) -> "AccountingBasisPolicy":
        try:
            raw, file_hash = load_governed_yaml_mapping(path, max_bytes=ACCOUNTING_POLICY_BYTES_MAX)
        except GovernedConfigError as exc:
            raise AccountingBasisError(exc.code, exc.message) from exc
        return cls.from_mapping(raw, content_sha256=file_hash)


@dataclass(frozen=True)
class LedgerIdentityBinding:
    source_record_ref: str
    identity_record: ProjectIdentityRecord
    canonical_contract_id: str
    binding_evidence_ref: str

    def validate_for(self, record: KingdeeLedgerRecord) -> None:
        if self.source_record_ref != record.source_record_ref:
            raise AccountingBasisError("BLOCKED_IDENTITY", "identity binding points to a different ledger record")
        self.identity_record.validate()
        if not IDENTITY_REF_RE.fullmatch(self.identity_record.identity_ref):
            raise AccountingBasisError("BLOCKED_IDENTITY", "identity record reference is not canonical")
        if self.canonical_contract_id not in self.identity_record.contract_ids:
            raise AccountingBasisError("BLOCKED_IDENTITY", "bound contract is not in the effective identity record")
        if not EVIDENCE_REF_RE.fullmatch(self.binding_evidence_ref):
            raise AccountingBasisError("BLOCKED_IDENTITY", "identity binding evidence is not hash-bound")
        if record.posting_date is None or not self.identity_record.is_active_at(date.fromisoformat(record.posting_date)):
            raise AccountingBasisError("BLOCKED_IDENTITY", "identity record is not active at the ledger posting date")


@dataclass(frozen=True)
class ClosedPeriodRecord:
    source_business_key_hash: str
    normalized_business_digest: str

    def validate(self) -> None:
        if not LEDGER_LINE_KEY_RE.fullmatch(self.source_business_key_hash) or not SHA256_RE.fullmatch(
            self.normalized_business_digest
        ):
            raise AccountingBasisError("CLOSED_SNAPSHOT_SCHEMA", "closed-period record binding is invalid")


@dataclass(frozen=True)
class ClosedPeriodSnapshot:
    snapshot_ref: str
    scope_fingerprint: str
    period_start: str
    closed_through: str
    records: Tuple[ClosedPeriodRecord, ...]
    evidence_refs: Tuple[str, ...]

    def _content(self) -> Dict[str, Any]:
        return {
            "scope_fingerprint": self.scope_fingerprint,
            "period_start": self.period_start,
            "closed_through": self.closed_through,
            "records": sorted(
                (item.source_business_key_hash, item.normalized_business_digest) for item in self.records
            ),
            "evidence_refs": sorted(self.evidence_refs),
        }

    def validate(self) -> None:
        if not SHA256_RE.fullmatch(self.scope_fingerprint):
            raise AccountingBasisError("CLOSED_SNAPSHOT_SCHEMA", "closed-period scope fingerprint is invalid")
        start = _iso_date(self.period_start, "closed_snapshot.period_start")
        closed = _iso_date(self.closed_through, "closed_snapshot.closed_through")
        if closed < start:
            raise AccountingBasisError("CLOSED_SNAPSHOT_SCHEMA", "closed-period snapshot range is reversed")
        expected_ref = "snapshot_" + _digest(self._content())[:32]
        if not SNAPSHOT_REF_RE.fullmatch(self.snapshot_ref) or self.snapshot_ref != expected_ref:
            raise AccountingBasisError("CLOSED_SNAPSHOT_SCHEMA", "closed-period snapshot reference is invalid")
        if not isinstance(self.records, tuple) or len({item.source_business_key_hash for item in self.records}) != len(self.records):
            raise AccountingBasisError("CLOSED_SNAPSHOT_SCHEMA", "closed-period snapshot records must be immutable and unique")
        for item in self.records:
            item.validate()
        if not self.evidence_refs or any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs):
            raise AccountingBasisError("CLOSED_SNAPSHOT_EVIDENCE", "closed-period snapshot requires hash-bound evidence")

    @classmethod
    def create(
        cls,
        *,
        scope_fingerprint: str,
        period_start: str,
        closed_through: str,
        records: Tuple[ClosedPeriodRecord, ...],
        evidence_refs: Tuple[str, ...],
    ) -> "ClosedPeriodSnapshot":
        provisional = cls(
            snapshot_ref="snapshot_" + "0" * 32,
            scope_fingerprint=scope_fingerprint,
            period_start=period_start,
            closed_through=closed_through,
            records=records,
            evidence_refs=evidence_refs,
        )
        snapshot = cls(
            snapshot_ref="snapshot_" + _digest(provisional._content())[:32],
            scope_fingerprint=scope_fingerprint,
            period_start=period_start,
            closed_through=closed_through,
            records=records,
            evidence_refs=evidence_refs,
        )
        snapshot.validate()
        return snapshot


@dataclass(frozen=True)
class AccountingScope:
    canonical_project_id: str
    legal_entity_id: str
    wbs_or_cost_code: str
    canonical_contract_id: str

    def validate(self) -> None:
        for field_name in (
            "canonical_project_id",
            "legal_entity_id",
            "wbs_or_cost_code",
            "canonical_contract_id",
        ):
            _text(getattr(self, field_name), field_name)

    @property
    def key(self) -> Tuple[str, str, str, str]:
        self.validate()
        return (
            self.canonical_project_id,
            self.legal_entity_id,
            self.wbs_or_cost_code,
            self.canonical_contract_id,
        )


def accounting_scope_fingerprint(scopes: Sequence[AccountingScope]) -> str:
    if not isinstance(scopes, (tuple, list)) or not scopes:
        raise AccountingBasisError("BASIS_SCOPE_BINDING", "at least one requested accounting scope is required")
    keys = []
    for scope in scopes:
        if not isinstance(scope, AccountingScope):
            raise AccountingBasisError("BASIS_SCOPE_BINDING", "requested scope has an invalid type")
        keys.append(scope.key)
    if len(keys) != len(set(keys)):
        raise AccountingBasisError("BASIS_SCOPE_BINDING", "requested accounting scopes must be unique")
    return _digest({"requested_accounting_scopes": sorted(keys)})


@dataclass(frozen=True)
class BasisRunContext:
    mode: str
    period_start: str
    period_end: str
    as_of: str
    requested_scopes: Tuple[AccountingScope, ...]
    prior_closed_snapshot: Optional[ClosedPeriodSnapshot] = None
    supersedes_run_ref: Optional[str] = None

    @property
    def scope_fingerprint(self) -> str:
        return accounting_scope_fingerprint(self.requested_scopes)

    def validate(self) -> None:
        if self.mode not in {"calculate", "restate"}:
            raise AccountingBasisError("BASIS_RUN_MODE", "accounting basis run mode must be calculate or restate")
        start = _iso_date(self.period_start, "period_start")
        end = _iso_date(self.period_end, "period_end")
        cutoff = _iso_date(self.as_of, "as_of")
        if end < start or cutoff < start:
            raise AccountingBasisError("BASIS_RUN_PERIOD", "accounting period or cutoff is reversed")
        if not isinstance(self.requested_scopes, tuple):
            raise AccountingBasisError("BASIS_SCOPE_BINDING", "requested accounting scopes must use an immutable tuple")
        accounting_scope_fingerprint(self.requested_scopes)
        if self.mode == "restate" and not self.supersedes_run_ref:
            raise AccountingBasisError("RESTATEMENT_BINDING_REQUIRED", "restate mode requires a superseded run reference")
        if self.mode == "calculate" and self.supersedes_run_ref is not None:
            raise AccountingBasisError("RESTATEMENT_BINDING_INVALID", "calculate mode cannot claim a superseded run")
        if self.prior_closed_snapshot is not None:
            self.prior_closed_snapshot.validate()


@dataclass(frozen=True)
class BasisDimension:
    legal_entity_id: str
    canonical_project_id: str
    wbs_or_cost_code: str
    canonical_contract_id: str
    bridge_group_id: str
    period_start: str
    period_end: str


@dataclass(frozen=True)
class WipBridge:
    dimension: BasisDimension
    opening_wip_minor: int
    additions_minor: int
    adjustments_minor: int
    transfer_in_minor: int
    reversals_minor: int
    other_transfers_out_minor: int
    recognized_cogs_minor: int
    cogs_reversals_minor: int
    closing_wip_minor: int
    wip_to_cogs_transfer_minor: int
    wip_from_cogs_reversal_minor: int
    expected_closing_wip_minor: int
    bridge_delta_minor: int
    transfer_control_delta_minor: int
    opening_record_count: int
    closing_record_count: int


@dataclass(frozen=True)
class BasisComponent:
    dimension: BasisDimension
    amount_minor: int


@dataclass(frozen=True)
class BasisView:
    basis_id: BasisId
    amount_minor: int
    components: Tuple[BasisComponent, ...]


@dataclass(frozen=True)
class AccountControl:
    dimension: BasisDimension
    account_code: str
    record_count: int
    debit_minor: int
    credit_minor: int
    balance_minor: int
    semantic_counts: Tuple[Tuple[str, int], ...]


@dataclass(frozen=True)
class BasisConservation:
    input_record_count: int
    classified_record_count: int
    excluded_record_count: int
    row_delta: int
    input_debit_minor: int
    classified_debit_minor: int
    excluded_debit_minor: int
    debit_delta_minor: int
    input_credit_minor: int
    classified_credit_minor: int
    excluded_credit_minor: int
    credit_delta_minor: int
    exclusion_counts: Tuple[Tuple[str, int], ...]

    def validate(self) -> None:
        if self.row_delta or self.debit_delta_minor or self.credit_delta_minor:
            raise AccountingBasisError("BLOCKED_SOURCE_CONSERVATION", "accounting classification does not conserve source rows and sides")


@dataclass(frozen=True)
class AccountingBasisResult:
    status: str
    policy_id: str
    policy_version: str
    policy_sha256: str
    views: Tuple[BasisView, ...]
    bridges: Tuple[WipBridge, ...]
    account_controls: Tuple[AccountControl, ...]
    conservation: BasisConservation
    late_posting_record_count: int
    business_fingerprint: str

    def view_map(self) -> Dict[BasisId, BasisView]:
        return {item.basis_id: item for item in self.views}


@dataclass
class _BridgeAccumulator:
    dimension: BasisDimension
    opening: int = 0
    additions: int = 0
    adjustments: int = 0
    transfer_in: int = 0
    reversals: int = 0
    other_transfers_out: int = 0
    cogs: int = 0
    cogs_reversals: int = 0
    closing: int = 0
    transfer_to_cogs: int = 0
    transfer_from_cogs: int = 0
    opening_count: int = 0
    closing_count: int = 0

    def add(self, semantic: LedgerSemantic, amount: int) -> None:
        mapping = {
            LedgerSemantic.WIP_ADDITION: "additions",
            LedgerSemantic.WIP_ADJUSTMENT: "adjustments",
            LedgerSemantic.WIP_TRANSFER_IN: "transfer_in",
            LedgerSemantic.WIP_REVERSAL: "reversals",
            LedgerSemantic.WIP_OTHER_TRANSFER_OUT: "other_transfers_out",
            LedgerSemantic.COGS_RECOGNITION: "cogs",
            LedgerSemantic.COGS_REVERSAL: "cogs_reversals",
            LedgerSemantic.WIP_TO_COGS_TRANSFER: "transfer_to_cogs",
            LedgerSemantic.WIP_FROM_COGS_REVERSAL: "transfer_from_cogs",
        }
        if semantic == LedgerSemantic.WIP_OPENING:
            self.opening += amount
            self.opening_count += 1
        elif semantic == LedgerSemantic.WIP_CLOSING:
            self.closing += amount
            self.closing_count += 1
        else:
            setattr(self, mapping[semantic], getattr(self, mapping[semantic]) + amount)

    def result(self) -> WipBridge:
        net_cogs = self.cogs - self.cogs_reversals
        expected = (
            self.opening
            + self.additions
            + self.adjustments
            + self.transfer_in
            - self.reversals
            - self.other_transfers_out
            - net_cogs
        )
        transfer_control = (self.transfer_to_cogs - self.transfer_from_cogs) - net_cogs
        return WipBridge(
            dimension=self.dimension,
            opening_wip_minor=self.opening,
            additions_minor=self.additions,
            adjustments_minor=self.adjustments,
            transfer_in_minor=self.transfer_in,
            reversals_minor=self.reversals,
            other_transfers_out_minor=self.other_transfers_out,
            recognized_cogs_minor=self.cogs,
            cogs_reversals_minor=self.cogs_reversals,
            closing_wip_minor=self.closing,
            wip_to_cogs_transfer_minor=self.transfer_to_cogs,
            wip_from_cogs_reversal_minor=self.transfer_from_cogs,
            expected_closing_wip_minor=expected,
            bridge_delta_minor=expected - self.closing,
            transfer_control_delta_minor=transfer_control,
            opening_record_count=self.opening_count,
            closing_record_count=self.closing_count,
        )


@dataclass
class _AccountAccumulator:
    dimension: BasisDimension
    account_code: str
    record_count: int = 0
    debit: int = 0
    credit: int = 0
    balance: int = 0
    semantics: Counter = field(default_factory=Counter)

    def add(self, record: KingdeeLedgerRecord, semantic: LedgerSemantic) -> None:
        self.record_count += 1
        self.debit += record.debit_minor or 0
        self.credit += record.credit_minor or 0
        self.balance += record.balance_minor or 0
        self.semantics[semantic.value] += 1

    def result(self) -> AccountControl:
        return AccountControl(
            dimension=self.dimension,
            account_code=self.account_code,
            record_count=self.record_count,
            debit_minor=self.debit,
            credit_minor=self.credit,
            balance_minor=self.balance,
            semantic_counts=tuple(sorted(self.semantics.items())),
        )


def _sum_side(records: Sequence[KingdeeLedgerRecord], field_name: str) -> int:
    return sum(getattr(item, field_name) or 0 for item in records)


def _assert_minor_range(*values: int) -> None:
    if any(isinstance(value, bool) or not isinstance(value, int) or abs(value) > MAX_ABS_MINOR_UNITS for value in values):
        raise AccountingBasisError("BLOCKED_AGGREGATE_OVERFLOW", "accounting aggregate exceeds the registered minor-unit ceiling")


def _validate_ledger_record(record: KingdeeLedgerRecord) -> None:
    try:
        record.validate()
    except KingdeeReaderError as exc:
        raise AccountingBasisError(exc.code, exc.message) from exc
    if (
        not SOURCE_RECORD_REF_RE.fullmatch(record.source_record_ref)
        or not LEDGER_LINE_KEY_RE.fullmatch(record.source_business_key_hash)
        or not SHA256_RE.fullmatch(record.normalized_business_digest)
    ):
        raise AccountingBasisError("LEDGER_RECORD_SCHEMA", "ledger lineage identifiers are invalid")
    for value in (record.debit_minor, record.credit_minor, record.balance_minor):
        if value is not None:
            _assert_minor_range(value)


def _movement_amount(record: KingdeeLedgerRecord, semantic: LedgerSemantic, policy: AccountingBasisPolicy) -> int:
    debit = record.debit_minor
    credit = record.credit_minor
    if debit is None and credit is None:
        raise AccountingBasisError("BLOCKED_LEDGER_AMOUNT", "posting row has neither debit nor credit")
    if debit is None or credit is None:
        if not policy.blank_counter_side_as_zero:
            raise AccountingBasisError("BLOCKED_LEDGER_AMOUNT", "blank debit/credit side needs an evidence-backed zero policy")
        debit = debit or 0
        credit = credit or 0
    if semantic in DEBIT_SEMANTICS:
        amount = debit - credit
    elif semantic in CREDIT_SEMANTICS:
        amount = credit - debit
    else:
        raise AccountingBasisError("BLOCKED_ACCOUNT_SEMANTIC", "control semantic cannot use posting movement logic")
    if amount <= 0:
        raise AccountingBasisError("BLOCKED_LEDGER_DIRECTION", "posting side conflicts with the governed row semantic")
    return amount


def _closed_period_changes(
    records: Sequence[KingdeeLedgerRecord],
    *,
    policy: AccountingBasisPolicy,
    context: BasisRunContext,
) -> int:
    closed_text = policy.period_policy.closed_through
    if closed_text is None:
        return 0
    closed = date.fromisoformat(closed_text)
    start = date.fromisoformat(context.period_start)
    end = min(date.fromisoformat(context.period_end), date.fromisoformat(context.as_of), closed)
    if end < start:
        return 0
    snapshot = context.prior_closed_snapshot
    if snapshot is None:
        raise AccountingBasisError("CLOSED_PERIOD_SNAPSHOT_REQUIRED", "closed-period calculation requires a bound prior snapshot")
    if (
        snapshot.closed_through != closed_text
        or snapshot.period_start != context.period_start
        or snapshot.scope_fingerprint != context.scope_fingerprint
    ):
        raise AccountingBasisError("CLOSED_PERIOD_SNAPSHOT_STALE", "prior snapshot period or scope differs from the active run")
    current: Dict[str, str] = {}
    for record in records:
        if record.posting_date is None:
            raise AccountingBasisError("BLOCKED_PERIOD", "ledger row lacks posting date")
        posted = date.fromisoformat(record.posting_date)
        if start <= posted <= end:
            if record.source_business_key_hash in current:
                raise AccountingBasisError("DUPLICATE_LEDGER_LINE_KEY", "ledger stable line key is not unique")
            current[record.source_business_key_hash] = record.normalized_business_digest
    prior = {item.source_business_key_hash: item.normalized_business_digest for item in snapshot.records}
    changed_keys = set(current).symmetric_difference(prior)
    changed_keys.update(key for key in set(current).intersection(prior) if current[key] != prior[key])
    if changed_keys and context.mode != "restate":
        raise AccountingBasisError("RESTATEMENT_REQUIRED", "closed-period ledger changed and requires a superseding run")
    return len(changed_keys)


def reconcile_accounting_bases(
    records: Sequence[KingdeeLedgerRecord],
    *,
    identity_bindings: Sequence[LedgerIdentityBinding],
    policy: AccountingBasisPolicy,
    context: BasisRunContext,
) -> AccountingBasisResult:
    """Reconcile WIP controls and emit separate JOB_COST and GL_COGS views."""

    policy.validate(require_active=True)
    context.validate()
    if not isinstance(records, (tuple, list)):
        raise AccountingBasisError("LEDGER_RECORD_CONTAINER", "ledger records must use a deterministic sequence")
    records_tuple = tuple(records)
    for record in records_tuple:
        _validate_ledger_record(record)
    if len({item.source_record_ref for item in records_tuple}) != len(records_tuple):
        raise AccountingBasisError("DUPLICATE_SOURCE_RECORD_REF", "ledger source record references must be unique")
    if len({item.source_business_key_hash for item in records_tuple}) != len(records_tuple):
        raise AccountingBasisError("DUPLICATE_LEDGER_LINE_KEY", "ledger stable line keys must be unique")
    start = date.fromisoformat(context.period_start)
    end = date.fromisoformat(context.period_end)
    cutoff = date.fromisoformat(context.as_of)
    policy_start = date.fromisoformat(policy.effective_from)
    policy_end = date.fromisoformat(policy.effective_to) if policy.effective_to else date.max
    if policy_start > start or policy_end < min(end, cutoff):
        raise AccountingBasisError("ACCOUNTING_POLICY_NOT_EFFECTIVE", "active accounting policy does not cover the run period")
    late_count = 0
    binding_map: Dict[str, LedgerIdentityBinding] = {}
    record_refs = {item.source_record_ref for item in records_tuple}
    for binding in identity_bindings:
        if binding.source_record_ref not in record_refs:
            raise AccountingBasisError("BLOCKED_IDENTITY", "identity binding references a ledger record outside this run")
        if binding.source_record_ref in binding_map:
            raise AccountingBasisError("BLOCKED_IDENTITY", "ledger record has multiple identity bindings")
        binding_map[binding.source_record_ref] = binding
    status_map = policy.status_map()
    row_kind_map = policy.row_kind_map()
    excluded_records = []
    classified_records = []
    exclusion_counts: Counter = Counter()
    bridges: Dict[BasisDimension, _BridgeAccumulator] = {}
    accounts: Dict[Tuple[BasisDimension, str], _AccountAccumulator] = {}
    closed_scope_records = []
    requested_scope_keys = {item.key for item in context.requested_scopes}
    for record in records_tuple:
        if record.posting_date is None:
            raise AccountingBasisError("BLOCKED_PERIOD", "ledger row lacks posting date")
        try:
            posted = date.fromisoformat(record.posting_date)
        except ValueError as exc:
            raise AccountingBasisError("BLOCKED_PERIOD", "ledger posting date is not canonical ISO") from exc
        exclusion_reason: Optional[str] = None
        if posted < start:
            exclusion_reason = "BEFORE_PERIOD"
        elif posted > end:
            exclusion_reason = "AFTER_PERIOD"
        elif posted > cutoff:
            exclusion_reason = "AFTER_AS_OF"
        if exclusion_reason is not None:
            excluded_records.append(record)
            exclusion_counts[exclusion_reason] += 1
            continue
        if record.source_status is None or record.source_status not in status_map:
            raise AccountingBasisError("BLOCKED_STATUS_POLICY", "in-scope source status lacks an exact policy rule")
        status_rule = status_map[record.source_status]
        if record.source_row_kind is None or record.source_row_kind not in row_kind_map:
            raise AccountingBasisError("BLOCKED_ROW_KIND_POLICY", "in-scope row kind lacks an exact semantic rule")
        row_rule = row_kind_map[record.source_row_kind]
        semantic = row_rule.semantic
        if semantic == LedgerSemantic.EXCLUDE_CONTROL:
            excluded_records.append(record)
            exclusion_counts["EXCLUDED_CONTROL_ROW"] += 1
            continue
        binding = binding_map.get(record.source_record_ref)
        if binding is None:
            raise AccountingBasisError("BLOCKED_IDENTITY", "included ledger row lacks one qualified identity binding")
        binding.validate_for(record)
        identity = binding.identity_record
        accounting_scope = AccountingScope(
            canonical_project_id=identity.canonical_project_id,
            legal_entity_id=identity.legal_entity_id,
            wbs_or_cost_code=identity.wbs_or_cost_code,
            canonical_contract_id=binding.canonical_contract_id,
        )
        if accounting_scope.key not in requested_scope_keys:
            excluded_records.append(record)
            exclusion_counts["OUTSIDE_REQUESTED_SCOPE"] += 1
            continue
        closed_scope_records.append(record)
        if status_rule.action == "EXCLUDE":
            excluded_records.append(record)
            exclusion_counts[status_rule.reason_code] += 1
            continue
        if record.currency != policy.base_currency:
            raise AccountingBasisError("BLOCKED_CURRENCY", "non-CNY or missing-currency ledger row blocks product 0.2")
        if record.account_code is None or record.voucher_id is None or record.voucher_line_id is None:
            raise AccountingBasisError("BLOCKED_LEDGER_KEY", "included ledger row lacks account or stable voucher-line key")
        account_rule = policy.account_rule(record.account_code, posted)
        if semantic not in account_rule.allowed_semantics:
            raise AccountingBasisError("BLOCKED_ACCOUNT_SEMANTIC", "row semantic is not allowed for the effective account rule")
        dimension = BasisDimension(
            legal_entity_id=identity.legal_entity_id,
            canonical_project_id=identity.canonical_project_id,
            wbs_or_cost_code=identity.wbs_or_cost_code,
            canonical_contract_id=binding.canonical_contract_id,
            bridge_group_id=account_rule.bridge_group_id,
            period_start=context.period_start,
            period_end=context.period_end,
        )
        accumulator = bridges.setdefault(dimension, _BridgeAccumulator(dimension=dimension))
        if semantic in {LedgerSemantic.WIP_OPENING, LedgerSemantic.WIP_CLOSING}:
            if record.balance_minor is None:
                raise AccountingBasisError("BLOCKED_WIP_CONTROL", "opening/closing WIP control row lacks an explicit balance")
            amount = record.balance_minor
        else:
            amount = _movement_amount(record, semantic, policy)
        accumulator.add(semantic, amount)
        account_key = (dimension, record.account_code)
        accounts.setdefault(
            account_key,
            _AccountAccumulator(dimension=dimension, account_code=record.account_code),
        ).add(record, semantic)
        classified_records.append(record)
    late_count = _closed_period_changes(closed_scope_records, policy=policy, context=context)
    bridge_results = tuple(
        bridges[key].result()
        for key in sorted(
            bridges,
            key=lambda item: (
                item.legal_entity_id,
                item.canonical_project_id,
                item.wbs_or_cost_code,
                item.canonical_contract_id,
                item.bridge_group_id,
            ),
        )
    )
    if not bridge_results:
        raise AccountingBasisError("BLOCKED_WIP_CONTROL", "requested scope produced no reconciled WIP bridge")
    for item in bridge_results:
        _assert_minor_range(
            item.opening_wip_minor,
            item.additions_minor,
            item.adjustments_minor,
            item.transfer_in_minor,
            item.reversals_minor,
            item.other_transfers_out_minor,
            item.recognized_cogs_minor,
            item.cogs_reversals_minor,
            item.closing_wip_minor,
            item.wip_to_cogs_transfer_minor,
            item.wip_from_cogs_reversal_minor,
            item.expected_closing_wip_minor,
            item.bridge_delta_minor,
            item.transfer_control_delta_minor,
        )
    incomplete = tuple(item for item in bridge_results if item.opening_record_count == 0 or item.closing_record_count == 0)
    if incomplete:
        raise AccountingBasisError(
            "BLOCKED_WIP_CONTROL",
            "every reconciled scope requires explicit opening and closing WIP controls",
            private_diagnostics=incomplete,
        )
    failed = tuple(
        item
        for item in bridge_results
        if item.bridge_delta_minor != 0
        or (policy.wip_to_cogs_control_required and item.transfer_control_delta_minor != 0)
    )
    if failed:
        raise AccountingBasisError(
            "BLOCKED_WIP_BRIDGE",
            "WIP or 5001-to-6401 transfer control has a non-zero unexplained delta",
            private_diagnostics=failed,
        )
    job_components = tuple(
        BasisComponent(
            dimension=item.dimension,
            amount_minor=(
                item.additions_minor
                + item.adjustments_minor
                + item.transfer_in_minor
                - item.reversals_minor
                - item.other_transfers_out_minor
            ),
        )
        for item in bridge_results
    )
    gl_components = tuple(
        BasisComponent(
            dimension=item.dimension,
            amount_minor=item.recognized_cogs_minor - item.cogs_reversals_minor,
        )
        for item in bridge_results
    )
    views = (
        BasisView(BasisId.JOB_COST_INCURRED, sum(item.amount_minor for item in job_components), job_components),
        BasisView(BasisId.GL_RECOGNIZED_COGS, sum(item.amount_minor for item in gl_components), gl_components),
    )
    _assert_minor_range(*(item.amount_minor for item in job_components), *(item.amount_minor for item in gl_components))
    _assert_minor_range(*(item.amount_minor for item in views))
    all_debit = _sum_side(records_tuple, "debit_minor")
    classified_debit = _sum_side(classified_records, "debit_minor")
    excluded_debit = _sum_side(excluded_records, "debit_minor")
    all_credit = _sum_side(records_tuple, "credit_minor")
    classified_credit = _sum_side(classified_records, "credit_minor")
    excluded_credit = _sum_side(excluded_records, "credit_minor")
    conservation = BasisConservation(
        input_record_count=len(records_tuple),
        classified_record_count=len(classified_records),
        excluded_record_count=len(excluded_records),
        row_delta=len(records_tuple) - len(classified_records) - len(excluded_records),
        input_debit_minor=all_debit,
        classified_debit_minor=classified_debit,
        excluded_debit_minor=excluded_debit,
        debit_delta_minor=all_debit - classified_debit - excluded_debit,
        input_credit_minor=all_credit,
        classified_credit_minor=classified_credit,
        excluded_credit_minor=excluded_credit,
        credit_delta_minor=all_credit - classified_credit - excluded_credit,
        exclusion_counts=tuple(sorted(exclusion_counts.items())),
    )
    conservation.validate()
    account_controls = tuple(
        accounts[key].result()
        for key in sorted(
            accounts,
            key=lambda item: (
                item[0].legal_entity_id,
                item[0].canonical_project_id,
                item[0].wbs_or_cost_code,
                item[0].canonical_contract_id,
                item[0].bridge_group_id,
                item[1],
            ),
        )
    )
    business_fingerprint = _digest(
        {
            "policy_sha256": policy.content_sha256,
            "context": {
                "mode": context.mode,
                "period_start": context.period_start,
                "period_end": context.period_end,
                "as_of": context.as_of,
                "scope_fingerprint": context.scope_fingerprint,
                "requested_scopes": sorted(item.key for item in context.requested_scopes),
                "supersedes_run_ref": context.supersedes_run_ref,
                "prior_snapshot_ref": context.prior_closed_snapshot.snapshot_ref
                if context.prior_closed_snapshot
                else None,
            },
            "records": sorted(item.normalized_business_digest for item in records_tuple),
            "identity_bindings": sorted(
                (item.source_record_ref, item.identity_record.identity_ref, item.canonical_contract_id)
                for item in identity_bindings
            ),
            "basis_ids": [item.value for item in BasisId],
        }
    )
    return AccountingBasisResult(
        status="R5_RECONCILED_NOT_FINAL",
        policy_id=policy.policy_id,
        policy_version=policy.policy_version,
        policy_sha256=policy.content_sha256,
        views=views,
        bridges=bridge_results,
        account_controls=account_controls,
        conservation=conservation,
        late_posting_record_count=late_count,
        business_fingerprint=business_fingerprint,
    )


def public_accounting_summary(result: AccountingBasisResult) -> Dict[str, Any]:
    """Aggregate status only; private dimensions, hashes and amounts stay private."""

    result.conservation.validate()
    return {
        "schema_version": "kmfa.project_cost.public_accounting_summary.v1",
        "status": result.status,
        "basis_ids": [item.basis_id.value for item in result.views],
        "bridge_group_count": len(result.bridges),
        "account_control_count": len(result.account_controls),
        "classified_record_count": result.conservation.classified_record_count,
        "excluded_record_count": result.conservation.excluded_record_count,
        "row_conservation_delta": result.conservation.row_delta,
        "debit_conservation_delta_minor": result.conservation.debit_delta_minor,
        "credit_conservation_delta_minor": result.conservation.credit_delta_minor,
        "late_posting_record_count": result.late_posting_record_count,
    }
