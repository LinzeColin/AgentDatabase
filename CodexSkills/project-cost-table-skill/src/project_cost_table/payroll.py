"""R8 fully-loaded payroll controls with approved-time allocation and residuals."""

from __future__ import annotations

import calendar
import hashlib
import json
import re
import unicodedata
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .config_io import GovernedConfigError, load_governed_yaml_mapping
from .formulas import (
    EVIDENCE_REF_RE,
    MAX_ABS_MINOR_UNITS,
    POLICY_REF_RE,
    RESOLUTION_REF_RE,
    SHA256_RE,
    FormulaError,
    FormulaKind,
    FormulaProfile,
    FormulaScope,
    FormulaStatus,
    evaluate_formula_inputs,
)


PAYROLL_CONFIG_BYTES_MAX = 1024 * 1024
REGISTRY_ID_RE = re.compile(r"^pay_component_registry_[0-9a-f]{32}$")
POLICY_ID_RE = re.compile(r"^payroll_policy_[0-9a-f]{32}$")
RECORD_ID_RE = re.compile(r"^payroll_record_[0-9a-f]{32}$")
TIME_ID_RE = re.compile(r"^time_record_[0-9a-f]{32}$")
CONTROL_ID_RE = re.compile(r"^payroll_control_[0-9a-f]{32}$")
EMPLOYEE_ID_RE = re.compile(r"^employee_[0-9a-f]{32}$")
PERIOD_RE = re.compile(r"^[0-9]{4}-(?:0[1-9]|1[0-2])$")


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
        raise PayrollError("PAYROLL_SCHEMA", "%s must be nonempty normalized text" % field_name)
    return value


def _iso_date(value: Any, field_name: str, *, optional: bool = False) -> Optional[date]:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise PayrollError("PAYROLL_SCHEMA", "%s must be an ISO date" % field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise PayrollError("PAYROLL_SCHEMA", "%s must be an ISO date" % field_name) from exc


def _period_end(value: str) -> date:
    if not isinstance(value, str) or not PERIOD_RE.fullmatch(value):
        raise PayrollError("PAYROLL_PERIOD", "payroll period must use YYYY-MM")
    year, month = (int(part) for part in value.split("-"))
    return date(year, month, calendar.monthrange(year, month)[1])


def _exact_int(value: Any, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise PayrollError("PAYROLL_INTEGER_REQUIRED", "%s must use an exact integer" % field_name)
    if positive and value <= 0:
        raise PayrollError("PAYROLL_INTEGER_RANGE", "%s must be positive" % field_name)
    if nonnegative and value < 0:
        raise PayrollError("PAYROLL_INTEGER_RANGE", "%s must be nonnegative" % field_name)
    return value


def _minor(value: Any, field_name: str, *, nonnegative: bool = False) -> int:
    result = _exact_int(value, field_name, nonnegative=nonnegative)
    if abs(result) > MAX_ABS_MINOR_UNITS:
        raise PayrollError("PAYROLL_MINOR_OVERFLOW", "%s exceeds the integer money ceiling" % field_name)
    return result


def _refs(values: Sequence[str], pattern: re.Pattern[str], field_name: str, *, required: bool = False) -> Tuple[str, ...]:
    if not isinstance(values, (list, tuple)) or any(not isinstance(item, str) for item in values):
        raise PayrollError("PAYROLL_REFERENCE", "%s must be a string list" % field_name)
    result = tuple(values)
    if (required and not result) or len(result) != len(set(result)) or any(not pattern.fullmatch(item) for item in result):
        raise PayrollError("PAYROLL_REFERENCE", "%s must be unique and correctly bound" % field_name)
    return result


class PayrollError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class PayComponentTreatment(str, Enum):
    INCLUDED_EMPLOYER_COST = "INCLUDED_EMPLOYER_COST"
    EXCLUDED_FROM_EMPLOYER_COST = "EXCLUDED_FROM_EMPLOYER_COST"
    EXTERNAL_LABOR_NOT_PAYROLL = "EXTERNAL_LABOR_NOT_PAYROLL"


class PayrollRecordKind(str, Enum):
    REGULAR = "REGULAR"
    CORRECTION = "CORRECTION"
    REVERSAL = "REVERSAL"
    RETROACTIVE = "RETROACTIVE"


class LaborClassification(str, Enum):
    EMPLOYEE_PAYROLL = "EMPLOYEE_PAYROLL"
    EXTERNAL_LABOR = "EXTERNAL_LABOR"


class TimeAllocationStatus(str, Enum):
    PROJECT = "PROJECT"
    UNALLOCATED = "UNALLOCATED"


@dataclass(frozen=True)
class PayComponentRule:
    component_id: str
    treatment: PayComponentTreatment
    legal_entity_id: str
    valid_from: str
    valid_to: Optional[str]
    evidence_refs: Tuple[str, ...]

    def period(self) -> Tuple[date, date]:
        start = _iso_date(self.valid_from, "component.valid_from")
        end = _iso_date(self.valid_to, "component.valid_to", optional=True) or date.max
        if end < start:
            raise PayrollError("PAY_COMPONENT_PERIOD", "pay-component effective period is reversed")
        return start, end

    def validate(self, *, active: bool) -> None:
        _text(self.component_id, "component_id")
        _text(self.legal_entity_id, "legal_entity_id")
        if self.legal_entity_id != "*" and "*" in self.legal_entity_id:
            raise PayrollError("PAY_COMPONENT_ENTITY", "entity wildcard must occupy the complete value")
        if not isinstance(self.treatment, PayComponentTreatment):
            raise PayrollError("PAY_COMPONENT_TREATMENT", "pay-component treatment is not registered")
        self.period()
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "component.evidence_refs", required=active)

    def applies(self, *, legal_entity_id: str, at: date) -> bool:
        start, end = self.period()
        return (self.legal_entity_id == "*" or self.legal_entity_id == legal_entity_id) and start <= at <= end


@dataclass(frozen=True)
class PayComponentRegistry:
    registry_id: str
    registry_version: str
    status: str
    valid_from: str
    valid_to: Optional[str]
    base_currency: str
    rules: Tuple[PayComponentRule, ...]
    evidence_refs: Tuple[str, ...]
    company_policy_refs: Tuple[str, ...]
    bound_config_hash: Optional[str]
    content_sha256: str

    def validate(self, *, require_active: bool = False) -> None:
        if not REGISTRY_ID_RE.fullmatch(self.registry_id):
            raise PayrollError("PAY_COMPONENT_REGISTRY_ID", "component registry ID must be opaque and canonical")
        _text(self.registry_version, "registry_version")
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise PayrollError("PAY_COMPONENT_REGISTRY_STATUS", "component registry status is not registered")
        start = _iso_date(self.valid_from, "valid_from")
        end = _iso_date(self.valid_to, "valid_to", optional=True) or date.max
        if end < start:
            raise PayrollError("PAY_COMPONENT_REGISTRY_PERIOD", "component registry period is reversed")
        if self.base_currency != "CNY":
            raise PayrollError("BLOCKED_CURRENCY", "product 0.2 payroll supports CNY only")
        active = self.status == "ACTIVE"
        if require_active and not active:
            raise PayrollError("PAY_COMPONENT_REGISTRY_NOT_ACTIVE", "component registry is not active")
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "registry.evidence_refs", required=active)
        _refs(self.company_policy_refs, POLICY_REF_RE, "registry.company_policy_refs", required=active)
        if active and (self.bound_config_hash is None or not SHA256_RE.fullmatch(self.bound_config_hash)):
            raise PayrollError("PAY_COMPONENT_REGISTRY_BINDING", "active component registry must bind its config hash")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise PayrollError("PAY_COMPONENT_REGISTRY_HASH", "component registry content hash is invalid")
        if not self.rules:
            raise PayrollError("PAY_COMPONENT_RULES_MISSING", "component registry requires explicit rules")
        for rule in self.rules:
            rule.validate(active=active)
        for index, left in enumerate(self.rules):
            left_start, left_end = left.period()
            for right in self.rules[index + 1 :]:
                right_start, right_end = right.period()
                entities_overlap = (
                    left.legal_entity_id == "*"
                    or right.legal_entity_id == "*"
                    or left.legal_entity_id == right.legal_entity_id
                )
                if (
                    left.component_id == right.component_id
                    and entities_overlap
                    and max(left_start, right_start) <= min(left_end, right_end)
                ):
                    raise PayrollError("PAY_COMPONENT_ACTIVE_OVERLAP", "component rules overlap by entity and date")

    def resolve(self, component_id: str, *, legal_entity_id: str, at: date) -> PayComponentRule:
        self.validate(require_active=True)
        candidates = [
            rule for rule in self.rules
            if rule.component_id == component_id and rule.applies(legal_entity_id=legal_entity_id, at=at)
        ]
        if not candidates:
            raise PayrollError("PAY_COMPONENT_UNKNOWN", "observed payroll component has no effective rule")
        exact = [rule for rule in candidates if rule.legal_entity_id == legal_entity_id]
        selected = exact or candidates
        if len(selected) != 1:
            raise PayrollError("PAY_COMPONENT_AMBIGUOUS", "component registry did not resolve to exactly one rule")
        return selected[0]

    @classmethod
    def from_yaml(cls, path: Path) -> "PayComponentRegistry":
        try:
            raw, content_sha256 = load_governed_yaml_mapping(path, max_bytes=PAYROLL_CONFIG_BYTES_MAX)
        except GovernedConfigError as exc:
            raise PayrollError(exc.code, exc.message) from exc
        expected = {
            "schema_version", "registry_id", "registry_version", "status", "valid_from", "valid_to",
            "base_currency", "rules", "evidence_refs", "company_policy_refs", "bound_config_hash",
        }
        if raw.get("schema_version") != "kmfa.project_cost.pay_component_registry.v1" or set(raw) != expected:
            raise PayrollError("PAY_COMPONENT_REGISTRY_SCHEMA", "component registry fields or schema version are unsupported")
        raw_rules = raw.get("rules")
        if not isinstance(raw_rules, list):
            raise PayrollError("PAY_COMPONENT_REGISTRY_SCHEMA", "component rules must be a list")
        rules = []
        for item in raw_rules:
            if not isinstance(item, dict) or set(item) != {
                "component_id", "treatment", "legal_entity_id", "valid_from", "valid_to", "evidence_refs"
            }:
                raise PayrollError("PAY_COMPONENT_REGISTRY_SCHEMA", "component rule fields are invalid")
            try:
                treatment = PayComponentTreatment(item["treatment"])
            except (KeyError, ValueError) as exc:
                raise PayrollError("PAY_COMPONENT_TREATMENT", "component treatment is not registered") from exc
            rules.append(
                PayComponentRule(
                    component_id=item["component_id"], treatment=treatment,
                    legal_entity_id=item["legal_entity_id"], valid_from=item["valid_from"],
                    valid_to=item["valid_to"],
                    evidence_refs=_refs(item["evidence_refs"], EVIDENCE_REF_RE, "component.evidence_refs"),
                )
            )
        try:
            result = cls(
                registry_id=raw["registry_id"], registry_version=raw["registry_version"], status=raw["status"],
                valid_from=raw["valid_from"], valid_to=raw["valid_to"], base_currency=raw["base_currency"],
                rules=tuple(rules), evidence_refs=_refs(raw["evidence_refs"], EVIDENCE_REF_RE, "evidence_refs"),
                company_policy_refs=_refs(raw["company_policy_refs"], POLICY_REF_RE, "company_policy_refs"),
                bound_config_hash=raw["bound_config_hash"], content_sha256=content_sha256,
            )
        except (KeyError, TypeError) as exc:
            raise PayrollError("PAY_COMPONENT_REGISTRY_SCHEMA", "component registry values are invalid") from exc
        result.validate()
        return result


@dataclass(frozen=True)
class PayrollRecord:
    record_id: str
    legal_entity_id: str
    employee_id: str
    payroll_period: str
    component_id: str
    amount_minor: int
    record_kind: PayrollRecordKind
    labor_classification: LaborClassification
    adjusts_record_id: Optional[str]
    reverses_record_id: Optional[str]
    evidence_refs: Tuple[str, ...]
    bound_input_hash: str

    def group_key(self) -> Tuple[str, str, str]:
        return (self.legal_entity_id, self.employee_id, self.payroll_period)

    def validate(self) -> None:
        if not RECORD_ID_RE.fullmatch(self.record_id) or not EMPLOYEE_ID_RE.fullmatch(self.employee_id):
            raise PayrollError("PAYROLL_RECORD_ID", "payroll and employee IDs must be opaque and canonical")
        _text(self.legal_entity_id, "legal_entity_id")
        _period_end(self.payroll_period)
        _text(self.component_id, "component_id")
        amount = _minor(self.amount_minor, "amount_minor")
        if amount == 0:
            raise PayrollError("PAYROLL_ZERO_RECORD", "payroll records cannot silently carry zero")
        if not isinstance(self.record_kind, PayrollRecordKind) or not isinstance(self.labor_classification, LaborClassification):
            raise PayrollError("PAYROLL_RECORD_ENUM", "payroll record kind and labor classification must be registered")
        if self.labor_classification is not LaborClassification.EMPLOYEE_PAYROLL:
            raise PayrollError("PAYROLL_EXTERNAL_LABOR_MISCLASSIFIED", "external labor cannot enter employee payroll allocation")
        if self.record_kind is PayrollRecordKind.REGULAR:
            if self.adjusts_record_id is not None or self.reverses_record_id is not None:
                raise PayrollError("PAYROLL_LINEAGE_INVALID", "regular payroll record cannot adjust or reverse another record")
        elif self.record_kind is PayrollRecordKind.REVERSAL:
            if self.reverses_record_id is None or self.adjusts_record_id is not None:
                raise PayrollError("PAYROLL_LINEAGE_REQUIRED", "reversal requires exactly one reversed record")
        else:
            if self.adjusts_record_id is None or self.reverses_record_id is not None:
                raise PayrollError("PAYROLL_LINEAGE_REQUIRED", "correction or retroactive record requires an adjusted record")
        for reference in (self.adjusts_record_id, self.reverses_record_id):
            if reference is not None and not RECORD_ID_RE.fullmatch(reference):
                raise PayrollError("PAYROLL_LINEAGE_REF", "payroll lineage reference is invalid")
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "record.evidence_refs", required=True)
        if not SHA256_RE.fullmatch(self.bound_input_hash):
            raise PayrollError("PAYROLL_INPUT_HASH", "payroll record requires an exact input hash")


@dataclass(frozen=True)
class ApprovedTimeRecord:
    time_record_id: str
    legal_entity_id: str
    project_legal_entity_id: Optional[str]
    employee_id: str
    payroll_period: str
    approved_time_units: int
    time_unit: str
    allocation_status: TimeAllocationStatus
    canonical_project_id: Optional[str]
    wbs_or_cost_code: Optional[str]
    mapping_resolution_ref: Optional[str]
    evidence_refs: Tuple[str, ...]
    bound_input_hash: str

    def group_key(self) -> Tuple[str, str, str]:
        return (self.legal_entity_id, self.employee_id, self.payroll_period)

    def validate(self) -> None:
        if not TIME_ID_RE.fullmatch(self.time_record_id) or not EMPLOYEE_ID_RE.fullmatch(self.employee_id):
            raise PayrollError("PAYROLL_TIME_ID", "time and employee IDs must be opaque and canonical")
        _text(self.legal_entity_id, "legal_entity_id")
        _period_end(self.payroll_period)
        _exact_int(self.approved_time_units, "approved_time_units", positive=True)
        _text(self.time_unit, "time_unit")
        if not isinstance(self.allocation_status, TimeAllocationStatus):
            raise PayrollError("PAYROLL_TIME_STATUS", "time allocation status is not registered")
        if self.allocation_status is TimeAllocationStatus.PROJECT:
            if not self.canonical_project_id or not self.wbs_or_cost_code or not self.mapping_resolution_ref:
                raise PayrollError("PAYROLL_PROJECT_WBS_REQUIRED", "project time requires project, WBS, and mapping resolution")
            _text(self.canonical_project_id, "canonical_project_id")
            _text(self.wbs_or_cost_code, "wbs_or_cost_code")
            _text(self.project_legal_entity_id, "project_legal_entity_id")
            if self.project_legal_entity_id != self.legal_entity_id:
                raise PayrollError("PAYROLL_CROSS_ENTITY", "payroll cannot allocate across legal entities")
            if not re.fullmatch(r"^identity_resolution_[0-9a-f]{32}$", self.mapping_resolution_ref):
                raise PayrollError("PAYROLL_MAPPING_REF", "project time requires a canonical identity resolution")
        elif any(value is not None for value in (
            self.project_legal_entity_id, self.canonical_project_id, self.wbs_or_cost_code, self.mapping_resolution_ref
        )):
            raise PayrollError("PAYROLL_UNALLOCATED_SCOPE", "unallocated time cannot claim project identity")
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "time.evidence_refs", required=True)
        if not SHA256_RE.fullmatch(self.bound_input_hash):
            raise PayrollError("PAYROLL_TIME_INPUT_HASH", "approved time requires an exact input hash")


@dataclass(frozen=True)
class PayrollControl:
    control_id: str
    legal_entity_id: str
    employee_id: str
    payroll_period: str
    payroll_control_total_minor: int
    approved_time_control_units: int
    time_unit: str
    evidence_refs: Tuple[str, ...]
    bound_input_hash: str

    def group_key(self) -> Tuple[str, str, str]:
        return (self.legal_entity_id, self.employee_id, self.payroll_period)

    def validate(self) -> None:
        if not CONTROL_ID_RE.fullmatch(self.control_id) or not EMPLOYEE_ID_RE.fullmatch(self.employee_id):
            raise PayrollError("PAYROLL_CONTROL_ID", "control and employee IDs must be opaque and canonical")
        _text(self.legal_entity_id, "legal_entity_id")
        _period_end(self.payroll_period)
        _minor(self.payroll_control_total_minor, "payroll_control_total_minor", nonnegative=True)
        _exact_int(self.approved_time_control_units, "approved_time_control_units", positive=True)
        _text(self.time_unit, "time_unit")
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "control.evidence_refs", required=True)
        if not SHA256_RE.fullmatch(self.bound_input_hash):
            raise PayrollError("PAYROLL_CONTROL_INPUT_HASH", "payroll control requires an exact input hash")


@dataclass(frozen=True)
class PayrollAllocationPolicy:
    policy_id: str
    policy_version: str
    status: str
    valid_from: str
    valid_to: Optional[str]
    allocation_method: str
    time_unit: str
    residual_destination: str
    evidence_refs: Tuple[str, ...]
    company_policy_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    bound_request_hash: Optional[str]
    bound_input_hash: Optional[str]
    bound_config_hash: Optional[str]
    content_sha256: str

    def validate(self, *, require_active: bool = False) -> None:
        if not POLICY_ID_RE.fullmatch(self.policy_id):
            raise PayrollError("PAYROLL_POLICY_ID", "payroll policy ID must be opaque and canonical")
        _text(self.policy_version, "policy_version")
        if self.status not in {"ACTIVE", "TEMPLATE_NOT_ACTIVE"}:
            raise PayrollError("PAYROLL_POLICY_STATUS", "payroll policy status is not registered")
        start = _iso_date(self.valid_from, "valid_from")
        end = _iso_date(self.valid_to, "valid_to", optional=True) or date.max
        if end < start:
            raise PayrollError("PAYROLL_POLICY_PERIOD", "payroll policy period is reversed")
        if self.allocation_method != "APPROVED_TIME_PRO_RATA" or self.residual_destination != "UNALLOCATED_PAYROLL_POOL":
            raise PayrollError("PAYROLL_POLICY_RELAXED", "payroll must use approved time with a visible unallocated pool")
        _text(self.time_unit, "time_unit")
        active = self.status == "ACTIVE"
        if require_active and not active:
            raise PayrollError("PAYROLL_POLICY_NOT_ACTIVE", "payroll allocation policy is not active")
        _refs(self.evidence_refs, EVIDENCE_REF_RE, "policy.evidence_refs", required=active)
        _refs(self.company_policy_refs, POLICY_REF_RE, "policy.company_policy_refs", required=active)
        _refs(self.input_resolution_refs, RESOLUTION_REF_RE, "policy.input_resolution_refs")
        if active and any(value is None or not SHA256_RE.fullmatch(value) for value in (
            self.bound_request_hash, self.bound_input_hash, self.bound_config_hash
        )):
            raise PayrollError("PAYROLL_POLICY_BINDING", "active payroll policy must bind request, input, and config hashes")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise PayrollError("PAYROLL_POLICY_HASH", "payroll policy content hash is invalid")

    @classmethod
    def from_yaml(cls, path: Path) -> "PayrollAllocationPolicy":
        try:
            raw, content_sha256 = load_governed_yaml_mapping(path, max_bytes=PAYROLL_CONFIG_BYTES_MAX)
        except GovernedConfigError as exc:
            raise PayrollError(exc.code, exc.message) from exc
        expected = {
            "schema_version", "policy_id", "policy_version", "status", "valid_from", "valid_to",
            "allocation_method", "time_unit", "residual_destination", "evidence_refs", "company_policy_refs",
            "input_resolution_refs", "bound_request_hash", "bound_input_hash", "bound_config_hash",
        }
        if raw.get("schema_version") != "kmfa.project_cost.payroll_allocation_policy.v1" or set(raw) != expected:
            raise PayrollError("PAYROLL_POLICY_SCHEMA", "payroll policy fields or schema version are unsupported")
        try:
            result = cls(
                policy_id=raw["policy_id"], policy_version=raw["policy_version"], status=raw["status"],
                valid_from=raw["valid_from"], valid_to=raw["valid_to"],
                allocation_method=raw["allocation_method"], time_unit=raw["time_unit"],
                residual_destination=raw["residual_destination"],
                evidence_refs=_refs(raw["evidence_refs"], EVIDENCE_REF_RE, "evidence_refs"),
                company_policy_refs=_refs(raw["company_policy_refs"], POLICY_REF_RE, "company_policy_refs"),
                input_resolution_refs=_refs(raw["input_resolution_refs"], RESOLUTION_REF_RE, "input_resolution_refs"),
                bound_request_hash=raw["bound_request_hash"], bound_input_hash=raw["bound_input_hash"],
                bound_config_hash=raw["bound_config_hash"], content_sha256=content_sha256,
            )
        except (KeyError, TypeError) as exc:
            raise PayrollError("PAYROLL_POLICY_SCHEMA", "payroll policy values are invalid") from exc
        result.validate()
        return result


@dataclass(frozen=True)
class PayrollAllocationLine:
    legal_entity_id: str
    employee_id: str
    payroll_period: str
    requested_metric_id: str
    canonical_project_id: Optional[str]
    wbs_or_cost_code: Optional[str]
    approved_time_units: int
    allocated_amount_minor: int
    allocation_status: str
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


@dataclass(frozen=True)
class PayrollGroupReconciliation:
    legal_entity_id: str
    employee_id: str
    payroll_period: str
    payroll_control_total_minor: int
    payroll_source_total_minor: int
    payroll_control_delta_minor: int
    allocable_employer_cost_minor: int
    excluded_component_amount_minor: int
    approved_time_control_units: int
    approved_time_source_units: int
    approved_time_delta_units: int
    project_allocated_amount_minor: int
    unallocated_payroll_amount_minor: int
    allocation_delta_minor: int
    status: str
    reason_codes: Tuple[str, ...]

    def as_dict(self) -> Dict[str, Any]:
        payload = dict(self.__dict__)
        payload["reason_codes"] = list(self.reason_codes)
        return payload


@dataclass(frozen=True)
class PayrollReconciliationResult:
    status: str
    requested_metric_id: str
    formula_profile_id: str
    component_registry_id: str
    allocation_policy_id: str
    allocations: Tuple[PayrollAllocationLine, ...]
    reconciliations: Tuple[PayrollGroupReconciliation, ...]
    calculation_hash: str
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.payroll_allocation.v1",
            "status": self.status,
            "requested_metric_id": self.requested_metric_id,
            "formula_profile_id": self.formula_profile_id,
            "component_registry_id": self.component_registry_id,
            "allocation_policy_id": self.allocation_policy_id,
            "allocations": [item.as_dict() for item in self.allocations],
            "reconciliations": [item.as_dict() for item in self.reconciliations],
            "calculation_hash": self.calculation_hash,
            "metric_inclusion_status": self.metric_inclusion_status,
        }


def _validate_payroll_lineage(records: Sequence[PayrollRecord]) -> None:
    by_id: Dict[str, PayrollRecord] = {}
    for record in records:
        record.validate()
        if record.record_id in by_id:
            raise PayrollError("PAYROLL_RECORD_DUPLICATE", "payroll record ID is duplicated")
        by_id[record.record_id] = record
    for record in records:
        reference = record.reverses_record_id or record.adjusts_record_id
        if reference is None:
            continue
        target = by_id.get(reference)
        if target is None:
            raise PayrollError("PAYROLL_LINEAGE_TARGET_MISSING", "payroll lineage target is absent")
        if target.group_key() != record.group_key() or target.component_id != record.component_id:
            raise PayrollError("PAYROLL_LINEAGE_SCOPE", "payroll correction lineage cannot cross group or component")
        if record.record_kind is PayrollRecordKind.REVERSAL and record.amount_minor != -target.amount_minor:
            raise PayrollError("PAYROLL_REVERSAL_AMOUNT", "payroll reversal must exactly negate its target")
    for record in records:
        seen = set()
        current = record
        while current.reverses_record_id or current.adjusts_record_id:
            if current.record_id in seen:
                raise PayrollError("PAYROLL_LINEAGE_CYCLE", "payroll lineage contains a cycle")
            seen.add(current.record_id)
            current = by_id[current.reverses_record_id or current.adjusts_record_id]


def reconcile_payroll(
    records: Sequence[PayrollRecord],
    time_records: Sequence[ApprovedTimeRecord],
    controls: Sequence[PayrollControl],
    *,
    component_registry: PayComponentRegistry,
    allocation_policy: PayrollAllocationPolicy,
    formula_profile: FormulaProfile,
    request_hash: str,
    requested_metric_id: str,
) -> PayrollReconciliationResult:
    if not records or not time_records or not controls:
        raise PayrollError("PAYROLL_REQUIRED_INPUT_MISSING", "payroll, approved time, and controls are non-waivable")
    component_registry.validate(require_active=True)
    allocation_policy.validate(require_active=True)
    formula_profile.validate(require_active=True)
    if formula_profile.formula_id != "FORM-PAYROLL-V2" or formula_profile.formula_kind is not FormulaKind.PAYROLL_TIME_ALLOCATION:
        raise PayrollError("PAYROLL_FORMULA_PROFILE", "payroll requires the registered approved-time formula")
    if not SHA256_RE.fullmatch(request_hash):
        raise PayrollError("PAYROLL_REQUEST_HASH", "payroll request hash must be lowercase SHA256")
    _text(requested_metric_id, "requested_metric_id")
    if formula_profile.bound_request_hash != request_hash or allocation_policy.bound_request_hash != request_hash:
        raise PayrollError("PAYROLL_REQUEST_BINDING", "payroll formula and policy must bind the exact request")
    if formula_profile.bound_input_hash != allocation_policy.bound_input_hash:
        raise PayrollError("PAYROLL_INPUT_BINDING", "payroll formula and policy must bind the same input snapshot")
    if not (
        formula_profile.bound_config_hash
        == allocation_policy.bound_config_hash
        == component_registry.bound_config_hash
    ):
        raise PayrollError(
            "PAYROLL_CONFIG_BINDING",
            "payroll formula, policy, and component registry must bind one config snapshot",
        )
    _validate_payroll_lineage(records)
    for item in time_records:
        item.validate()
    control_map: Dict[Tuple[str, str, str], PayrollControl] = {}
    for control in controls:
        control.validate()
        if control.bound_input_hash != allocation_policy.bound_input_hash:
            raise PayrollError("PAYROLL_INPUT_BINDING", "payroll control differs from the policy-bound input snapshot")
        key = control.group_key()
        if key in control_map:
            raise PayrollError("PAYROLL_CONTROL_DUPLICATE", "payroll group has more than one control")
        control_map[key] = control
        if control.time_unit != allocation_policy.time_unit:
            raise PayrollError("PAYROLL_TIME_UNIT", "control time unit differs from allocation policy")
    record_groups: Dict[Tuple[str, str, str], list[PayrollRecord]] = defaultdict(list)
    time_groups: Dict[Tuple[str, str, str], list[ApprovedTimeRecord]] = defaultdict(list)
    for record in records:
        if record.bound_input_hash != allocation_policy.bound_input_hash:
            raise PayrollError("PAYROLL_INPUT_BINDING", "payroll record differs from the policy-bound input snapshot")
        record_groups[record.group_key()].append(record)
    for item in time_records:
        if item.bound_input_hash != allocation_policy.bound_input_hash:
            raise PayrollError("PAYROLL_INPUT_BINDING", "approved time differs from the policy-bound input snapshot")
        if item.time_unit != allocation_policy.time_unit:
            raise PayrollError("PAYROLL_TIME_UNIT", "approved-time unit differs from allocation policy")
        time_groups[item.group_key()].append(item)
    if set(record_groups) != set(control_map) or set(time_groups) != set(control_map):
        raise PayrollError("PAYROLL_CONTROL_SCOPE_MISMATCH", "every payroll group requires records, time, and exactly one control")

    allocations = []
    reconciliations = []
    for key in sorted(control_map):
        entity, employee, period = key
        control = control_map[key]
        source_total = sum(item.amount_minor for item in record_groups[key])
        included = 0
        excluded = 0
        for record in record_groups[key]:
            rule = component_registry.resolve(record.component_id, legal_entity_id=entity, at=_period_end(period))
            if rule.treatment is PayComponentTreatment.EXTERNAL_LABOR_NOT_PAYROLL:
                raise PayrollError("PAYROLL_EXTERNAL_LABOR_COMPONENT", "external-labor component cannot enter payroll")
            if rule.treatment is PayComponentTreatment.INCLUDED_EMPLOYER_COST:
                included += record.amount_minor
            else:
                excluded += record.amount_minor
        _minor(included, "allocable_employer_cost_minor", nonnegative=True)
        time_total = sum(item.approved_time_units for item in time_groups[key])
        payroll_delta = source_total - control.payroll_control_total_minor
        time_delta = time_total - control.approved_time_control_units
        reasons = []
        if payroll_delta:
            reasons.append("PAYROLL_CONTROL_DELTA")
        if time_delta:
            reasons.append("APPROVED_TIME_CONTROL_DELTA")

        grouped_project_time: Dict[Tuple[str, str], int] = defaultdict(int)
        unallocated_time = 0
        for item in time_groups[key]:
            if item.allocation_status is TimeAllocationStatus.PROJECT:
                grouped_project_time[(item.canonical_project_id, item.wbs_or_cost_code)] += item.approved_time_units
            else:
                unallocated_time += item.approved_time_units

        project_allocated = 0
        if not reasons:
            for (project_id, wbs), project_time in sorted(grouped_project_time.items()):
                scope = FormulaScope(
                    metric_id=requested_metric_id,
                    legal_entity_id=entity,
                    canonical_project_id=project_id,
                    wbs_or_cost_code=wbs,
                )
                if not formula_profile.scope.matches(scope) or not formula_profile.active_at(_period_end(period)):
                    raise PayrollError("PAYROLL_FORMULA_SCOPE", "payroll formula does not apply to an allocated project scope")
                amount = evaluate_formula_inputs(
                    formula_profile,
                    {
                        "employer_cost_minor": included,
                        "approved_project_time_units": project_time,
                        "approved_total_time_units": control.approved_time_control_units,
                    },
                )
                project_allocated += amount
                allocations.append(
                    PayrollAllocationLine(
                        entity, employee, period, requested_metric_id,
                        project_id, wbs, project_time, amount, "PROJECT_ALLOCATED",
                    )
                )
        unallocated_amount = included - project_allocated
        if unallocated_amount < 0:
            reasons.append("PAYROLL_ROUNDING_OVERALLOCATION")
        allocation_delta = included - project_allocated - unallocated_amount
        if allocation_delta:
            reasons.append("PAYROLL_ALLOCATION_DELTA")
        allocations.append(
            PayrollAllocationLine(
                entity, employee, period, requested_metric_id, None, None, unallocated_time,
                unallocated_amount, "UNALLOCATED_PAYROLL_POOL",
            )
        )
        reconciliations.append(
            PayrollGroupReconciliation(
                legal_entity_id=entity,
                employee_id=employee,
                payroll_period=period,
                payroll_control_total_minor=control.payroll_control_total_minor,
                payroll_source_total_minor=source_total,
                payroll_control_delta_minor=payroll_delta,
                allocable_employer_cost_minor=included,
                excluded_component_amount_minor=excluded,
                approved_time_control_units=control.approved_time_control_units,
                approved_time_source_units=time_total,
                approved_time_delta_units=time_delta,
                project_allocated_amount_minor=project_allocated,
                unallocated_payroll_amount_minor=unallocated_amount,
                allocation_delta_minor=allocation_delta,
                status="BLOCKED_R8_PAYROLL_CONTROL" if reasons else "PASS_R8_PAYROLL_CONTROL",
                reason_codes=tuple(sorted(set(reasons))),
            )
        )

    overall = "PASS_R8_PAYROLL_CONTROLS_NOT_METRIC"
    if any(item.status.startswith("BLOCKED") for item in reconciliations):
        overall = "BLOCKED_R8_PAYROLL_CONTROLS"
    payload = {
        "formula_profile_id": formula_profile.profile_id,
        "formula_profile_hash": formula_profile.content_sha256,
        "component_registry_id": component_registry.registry_id,
        "component_registry_hash": component_registry.content_sha256,
        "allocation_policy_id": allocation_policy.policy_id,
        "allocation_policy_hash": allocation_policy.content_sha256,
        "request_hash": request_hash,
        "allocations": [item.as_dict() for item in allocations],
        "reconciliations": [item.as_dict() for item in reconciliations],
    }
    return PayrollReconciliationResult(
        status=overall,
        requested_metric_id=requested_metric_id,
        formula_profile_id=formula_profile.profile_id,
        component_registry_id=component_registry.registry_id,
        allocation_policy_id=allocation_policy.policy_id,
        allocations=tuple(allocations),
        reconciliations=tuple(reconciliations),
        calculation_hash=_digest(payload),
    )
