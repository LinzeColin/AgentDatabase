"""R8 evidence-bound formula, rate, tax, interest, and readiness controls.

This module deliberately stops before named-Metric inclusion.  It contains no
expression evaluator, float path, inferred rate, or company approval state.
"""

from __future__ import annotations

import hashlib
import json
import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

from .config_io import GovernedConfigError, load_governed_yaml_mapping
from .money import RoundingLayer


FORMULA_PROFILE_BYTES_MAX = 1024 * 1024
MAX_ABS_MINOR_UNITS = 9223372036854775807
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
EVIDENCE_REF_RE = re.compile(r"^evidence://sha256/[0-9a-f]{64}$")
POLICY_REF_RE = re.compile(r"^policy://sha256/[0-9a-f]{64}$")
RESOLUTION_REF_RE = re.compile(r"^resolution_[0-9a-f]{32}$")
PROFILE_ID_RE = re.compile(r"^formula_profile_[0-9a-f]{32}$")
RECORD_ID_RE = re.compile(r"^[a-z][a-z0-9_]{2,63}_[0-9a-f]{32}$")


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
        raise FormulaError("FORMULA_PROFILE_SCHEMA", "%s must be nonempty normalized text" % field_name)
    return value


def _iso_date(value: Any, field_name: str, *, optional: bool = False) -> Optional[date]:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise FormulaError("FORMULA_PROFILE_SCHEMA", "%s must be an ISO date" % field_name)
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise FormulaError("FORMULA_PROFILE_SCHEMA", "%s must be an ISO date" % field_name) from exc


def _strings(value: Any, field_name: str) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) for item in value):
        raise FormulaError("FORMULA_PROFILE_SCHEMA", "%s must be a string list" % field_name)
    result = tuple(value)
    if len(result) != len(set(result)):
        raise FormulaError("FORMULA_PROFILE_SCHEMA", "%s cannot contain duplicates" % field_name)
    for item in result:
        _text(item, field_name)
    return result


def _exact_int(value: Any, field_name: str, *, positive: bool = False, nonnegative: bool = False) -> int:
    if type(value) is not int:
        raise FormulaError("FORMULA_INTEGER_REQUIRED", "%s must use an exact integer" % field_name)
    if positive and value <= 0:
        raise FormulaError("FORMULA_INTEGER_RANGE", "%s must be positive" % field_name)
    if nonnegative and value < 0:
        raise FormulaError("FORMULA_INTEGER_RANGE", "%s must be nonnegative" % field_name)
    return value


def _bounded_minor(value: Any, field_name: str, *, nonnegative: bool = False) -> int:
    result = _exact_int(value, field_name, nonnegative=nonnegative)
    if abs(result) > MAX_ABS_MINOR_UNITS:
        raise FormulaError("FORMULA_MINOR_OVERFLOW", "%s exceeds the integer money ceiling" % field_name)
    return result


def round_half_up_ratio(numerator: int, denominator: int) -> int:
    """Round an exact integer ratio half away from zero without Decimal drift."""

    _exact_int(numerator, "numerator")
    _exact_int(denominator, "denominator", positive=True)
    sign = -1 if numerator < 0 else 1
    quotient, remainder = divmod(abs(numerator), denominator)
    if remainder * 2 >= denominator:
        quotient += 1
    result = sign * quotient
    if abs(result) > MAX_ABS_MINOR_UNITS:
        raise FormulaError("FORMULA_MINOR_OVERFLOW", "formula result exceeds the integer money ceiling")
    return result


class FormulaError(ValueError):
    """Fail-closed R8 error that never serializes source values."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


class FormulaKind(str, Enum):
    MANAGEMENT_RATE = "MANAGEMENT_RATE"
    PAYROLL_TIME_ALLOCATION = "PAYROLL_TIME_ALLOCATION"
    PROJECT_TAX_RATE = "PROJECT_TAX_RATE"
    CAPITAL_INTEREST = "CAPITAL_INTEREST"
    FX_RATE = "FX_RATE"


class FormulaStatus(str, Enum):
    ACTIVE = "ACTIVE"
    TEMPLATE_NOT_ACTIVE = "TEMPLATE_NOT_ACTIVE"
    REFERENCE_OBSERVED_NOT_ACTIVE = "REFERENCE_OBSERVED_NOT_ACTIVE"
    SUPERSEDED = "SUPERSEDED"
    DEFERRED_NOT_ACTIVE = "DEFERRED_NOT_ACTIVE"


class FormulaExpression(str, Enum):
    RATE_TIMES_BASE = "RATE_TIMES_BASE"
    APPROVED_TIME_PRORATION = "APPROVED_TIME_PRORATION"
    SIMPLE_INTEREST_DAILY = "SIMPLE_INTEREST_DAILY"
    FX_RATE_TIMES_AMOUNT = "FX_RATE_TIMES_AMOUNT"


class AuthorityMode(str, Enum):
    DIRECT_SOURCE_EVIDENCE = "DIRECT_SOURCE_EVIDENCE"
    COMPANY_POLICY = "COMPANY_POLICY"
    QUALIFIED_ALTERNATE_EVIDENCE = "QUALIFIED_ALTERNATE_EVIDENCE"


ALLOWED_EXPRESSION_BY_KIND = {
    FormulaKind.MANAGEMENT_RATE: FormulaExpression.RATE_TIMES_BASE,
    FormulaKind.PAYROLL_TIME_ALLOCATION: FormulaExpression.APPROVED_TIME_PRORATION,
    FormulaKind.PROJECT_TAX_RATE: FormulaExpression.RATE_TIMES_BASE,
    FormulaKind.CAPITAL_INTEREST: FormulaExpression.SIMPLE_INTEREST_DAILY,
    FormulaKind.FX_RATE: FormulaExpression.FX_RATE_TIMES_AMOUNT,
}

ALLOWED_ROUNDING_BY_KIND = {
    FormulaKind.MANAGEMENT_RATE: RoundingLayer.LINE_FORMULA,
    FormulaKind.PAYROLL_TIME_ALLOCATION: RoundingLayer.ALLOCATION_RESIDUAL,
    FormulaKind.PROJECT_TAX_RATE: RoundingLayer.TAX_CALCULATION,
    FormulaKind.CAPITAL_INTEREST: RoundingLayer.LINE_FORMULA,
    FormulaKind.FX_RATE: RoundingLayer.LINE_FORMULA,
}


@dataclass(frozen=True)
class FormulaScope:
    metric_id: str
    legal_entity_id: str
    canonical_project_id: str
    wbs_or_cost_code: str

    def validate(self) -> None:
        for field_name in ("metric_id", "legal_entity_id", "canonical_project_id", "wbs_or_cost_code"):
            value = _text(getattr(self, field_name), "scope.%s" % field_name)
            if value != "*" and "*" in value:
                raise FormulaError("FORMULA_SCOPE_WILDCARD", "scope wildcard must occupy the complete dimension")

    def matches(self, candidate: "FormulaScope") -> bool:
        self.validate()
        candidate.validate()
        return all(
            configured == "*" or configured == requested
            for configured, requested in zip(self.as_tuple(), candidate.as_tuple())
        )

    def overlaps(self, other: "FormulaScope") -> bool:
        self.validate()
        other.validate()
        return all(left == "*" or right == "*" or left == right for left, right in zip(self.as_tuple(), other.as_tuple()))

    def specificity(self) -> int:
        return sum(value != "*" for value in self.as_tuple())

    def as_tuple(self) -> Tuple[str, str, str, str]:
        return (self.metric_id, self.legal_entity_id, self.canonical_project_id, self.wbs_or_cost_code)

    def as_dict(self) -> Dict[str, str]:
        return {
            "metric_id": self.metric_id,
            "legal_entity_id": self.legal_entity_id,
            "canonical_project_id": self.canonical_project_id,
            "wbs_or_cost_code": self.wbs_or_cost_code,
        }


@dataclass(frozen=True)
class FormulaTestVector:
    vector_id: str
    inputs: Mapping[str, int]
    expected_amount_minor: int

    def validate(self) -> None:
        _text(self.vector_id, "test_vector.vector_id")
        if not isinstance(self.inputs, Mapping) or not self.inputs:
            raise FormulaError("FORMULA_TEST_VECTOR", "test vector inputs must be a nonempty mapping")
        for key, value in self.inputs.items():
            _text(key, "test_vector.input")
            _exact_int(value, "test_vector.input_value")
        _bounded_minor(self.expected_amount_minor, "expected_amount_minor")


@dataclass(frozen=True)
class FormulaEvaluation:
    formula_id: str
    profile_id: str
    amount_minor: int
    calculation_hash: str
    calculation_status: str = "R8_POLICY_EVALUATED_NOT_METRIC"
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "formula_id": self.formula_id,
            "profile_id": self.profile_id,
            "amount_minor": self.amount_minor,
            "calculation_hash": self.calculation_hash,
            "calculation_status": self.calculation_status,
            "metric_inclusion_status": self.metric_inclusion_status,
        }


@dataclass(frozen=True)
class FormulaProfile:
    profile_id: str
    profile_version: str
    formula_id: str
    formula_kind: FormulaKind
    expression_id: FormulaExpression
    status: FormulaStatus
    valid_from: str
    valid_to: Optional[str]
    scope: FormulaScope
    base_currency: str
    rounding_layer: RoundingLayer
    rounding_mode: str
    parameters: Mapping[str, int]
    authority_mode: AuthorityMode
    company_policy_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    bound_request_hash: Optional[str]
    bound_input_hash: Optional[str]
    bound_config_hash: Optional[str]
    supersedes: Optional[str]
    test_vectors: Tuple[FormulaTestVector, ...]
    content_sha256: str

    def active_period(self) -> Tuple[date, date]:
        start = _iso_date(self.valid_from, "valid_from")
        end = _iso_date(self.valid_to, "valid_to", optional=True) or date.max
        if end < start:
            raise FormulaError("FORMULA_EFFECTIVE_PERIOD", "formula effective period is reversed")
        return start, end

    def active_at(self, value: date) -> bool:
        start, end = self.active_period()
        return self.status is FormulaStatus.ACTIVE and start <= value <= end

    def validate(self, *, require_active: bool = False, execute_vectors: bool = True) -> None:
        if not PROFILE_ID_RE.fullmatch(self.profile_id):
            raise FormulaError("FORMULA_PROFILE_ID", "profile ID must be opaque and canonical")
        _text(self.profile_version, "profile_version")
        _text(self.formula_id, "formula_id")
        if not isinstance(self.formula_kind, FormulaKind) or not isinstance(self.expression_id, FormulaExpression):
            raise FormulaError("FORMULA_KIND_UNKNOWN", "formula kind and expression must be registered")
        if self.expression_id is not ALLOWED_EXPRESSION_BY_KIND[self.formula_kind]:
            raise FormulaError("FORMULA_EXPRESSION_NOT_ALLOWED", "expression is not allowlisted for the formula kind")
        if not isinstance(self.status, FormulaStatus):
            raise FormulaError("FORMULA_STATUS_UNKNOWN", "formula status is not registered")
        self.active_period()
        self.scope.validate()
        if self.base_currency != "CNY":
            raise FormulaError("BLOCKED_CURRENCY", "product 0.2 supports CNY policy calculations only")
        if self.rounding_layer is not ALLOWED_ROUNDING_BY_KIND[self.formula_kind] or self.rounding_mode != "ROUND_HALF_UP":
            raise FormulaError("FORMULA_ROUNDING_POLICY", "formula requires its registered rounding layer and half-up mode")
        if not isinstance(self.parameters, Mapping) or any(type(value) is not int for value in self.parameters.values()):
            raise FormulaError("FORMULA_PARAMETER_TYPE", "formula parameters must be exact integers")
        expected_parameters = {
            FormulaExpression.RATE_TIMES_BASE: {"rate_numerator", "rate_denominator"},
            FormulaExpression.APPROVED_TIME_PRORATION: set(),
            FormulaExpression.SIMPLE_INTEREST_DAILY: {"annual_rate_numerator", "annual_rate_denominator", "day_count_denominator"},
            FormulaExpression.FX_RATE_TIMES_AMOUNT: {"rate_numerator", "rate_denominator"},
        }[self.expression_id]
        if set(self.parameters) != expected_parameters:
            raise FormulaError("FORMULA_PARAMETER_SET", "formula parameter set does not match the allowlisted expression")
        for name, value in self.parameters.items():
            _exact_int(value, name, positive=name.endswith("denominator"), nonnegative=name.endswith("numerator"))
        if not isinstance(self.authority_mode, AuthorityMode):
            raise FormulaError("FORMULA_AUTHORITY_UNKNOWN", "formula authority mode is not registered")
        for refs, pattern, field_name in (
            (self.company_policy_refs, POLICY_REF_RE, "company_policy_refs"),
            (self.evidence_refs, EVIDENCE_REF_RE, "evidence_refs"),
            (self.input_resolution_refs, RESOLUTION_REF_RE, "input_resolution_refs"),
        ):
            if len(refs) != len(set(refs)) or any(not pattern.fullmatch(item) for item in refs):
                raise FormulaError("FORMULA_REFERENCE_INVALID", "%s must be unique and hash-bound" % field_name)
        active = self.status is FormulaStatus.ACTIVE
        if require_active and not active:
            raise FormulaError("FORMULA_PROFILE_NOT_ACTIVE", "formula profile is not active")
        if active:
            if self.formula_kind is FormulaKind.FX_RATE:
                raise FormulaError("FX_DEFERRED_PRODUCT_0_2", "active FX conversion is deferred beyond product 0.2")
            if not self.evidence_refs:
                raise FormulaError("FORMULA_EVIDENCE_REQUIRED", "active formula requires hash-bound evidence")
            if self.authority_mode is AuthorityMode.COMPANY_POLICY and not self.company_policy_refs:
                raise FormulaError("FORMULA_POLICY_REQUIRED", "company-policy formula requires a hash-bound policy reference")
            if self.authority_mode is AuthorityMode.QUALIFIED_ALTERNATE_EVIDENCE and not self.input_resolution_refs:
                raise FormulaError("FORMULA_RESOLUTION_REQUIRED", "alternate evidence requires an input resolution")
            if any(value is None or not SHA256_RE.fullmatch(value) for value in (
                self.bound_request_hash,
                self.bound_input_hash,
                self.bound_config_hash,
            )):
                raise FormulaError("FORMULA_BINDING_HASH_REQUIRED", "active formula must bind request, input, and config hashes")
            if not self.test_vectors:
                raise FormulaError("FORMULA_TEST_VECTOR_REQUIRED", "active formula requires at least one executable test vector")
        if self.supersedes is not None and not PROFILE_ID_RE.fullmatch(self.supersedes):
            raise FormulaError("FORMULA_SUPERSESSION_REF", "superseded profile reference is invalid")
        if not SHA256_RE.fullmatch(self.content_sha256):
            raise FormulaError("FORMULA_CONTENT_HASH", "formula profile content hash is invalid")
        vector_ids = set()
        for vector in self.test_vectors:
            vector.validate()
            if vector.vector_id in vector_ids:
                raise FormulaError("FORMULA_TEST_VECTOR_DUPLICATE", "test vector IDs must be unique")
            vector_ids.add(vector.vector_id)
            if execute_vectors and evaluate_formula_inputs(self, vector.inputs) != vector.expected_amount_minor:
                raise FormulaError("FORMULA_TEST_VECTOR_FAILED", "formula test vector does not match the expected amount")

    def applies_to(self, value: date, scope: FormulaScope) -> bool:
        return self.active_at(value) and self.scope.matches(scope)

    @classmethod
    def from_yaml(cls, path: Path) -> "FormulaProfile":
        try:
            raw, content_sha256 = load_governed_yaml_mapping(path, max_bytes=FORMULA_PROFILE_BYTES_MAX)
        except GovernedConfigError as exc:
            raise FormulaError(exc.code, exc.message) from exc
        expected = {
            "schema_version", "profile_id", "profile_version", "formula_id", "formula_kind", "expression_id",
            "status", "valid_from", "valid_to", "scope", "base_currency", "rounding_layer", "rounding_mode",
            "parameters", "authority_mode", "company_policy_refs", "evidence_refs", "input_resolution_refs",
            "bound_request_hash", "bound_input_hash", "bound_config_hash", "supersedes", "test_vectors",
        }
        if raw.get("schema_version") != "kmfa.project_cost.formula_profile.v1" or set(raw) != expected:
            raise FormulaError("FORMULA_PROFILE_SCHEMA", "formula profile fields or schema version are unsupported")
        scope_raw = raw.get("scope")
        if not isinstance(scope_raw, dict) or set(scope_raw) != {
            "metric_id", "legal_entity_id", "canonical_project_id", "wbs_or_cost_code"
        }:
            raise FormulaError("FORMULA_PROFILE_SCHEMA", "formula scope fields are invalid")
        parameter_raw = raw.get("parameters")
        if not isinstance(parameter_raw, dict) or any(not isinstance(key, str) for key in parameter_raw):
            raise FormulaError("FORMULA_PROFILE_SCHEMA", "formula parameters must be a string-keyed mapping")
        vectors_raw = raw.get("test_vectors")
        if not isinstance(vectors_raw, list):
            raise FormulaError("FORMULA_PROFILE_SCHEMA", "test vectors must be a list")
        vectors = []
        for item in vectors_raw:
            if not isinstance(item, dict) or set(item) != {"vector_id", "inputs", "expected_amount_minor"}:
                raise FormulaError("FORMULA_PROFILE_SCHEMA", "test vector fields are invalid")
            if not isinstance(item.get("inputs"), dict):
                raise FormulaError("FORMULA_PROFILE_SCHEMA", "test vector inputs must be a mapping")
            vectors.append(FormulaTestVector(item["vector_id"], dict(item["inputs"]), item["expected_amount_minor"]))
        try:
            profile = cls(
                profile_id=raw["profile_id"], profile_version=raw["profile_version"], formula_id=raw["formula_id"],
                formula_kind=FormulaKind(raw["formula_kind"]), expression_id=FormulaExpression(raw["expression_id"]),
                status=FormulaStatus(raw["status"]), valid_from=raw["valid_from"], valid_to=raw["valid_to"],
                scope=FormulaScope(**scope_raw), base_currency=raw["base_currency"],
                rounding_layer=RoundingLayer(raw["rounding_layer"]), rounding_mode=raw["rounding_mode"],
                parameters=dict(parameter_raw), authority_mode=AuthorityMode(raw["authority_mode"]),
                company_policy_refs=_strings(raw["company_policy_refs"], "company_policy_refs"),
                evidence_refs=_strings(raw["evidence_refs"], "evidence_refs"),
                input_resolution_refs=_strings(raw["input_resolution_refs"], "input_resolution_refs"),
                bound_request_hash=raw["bound_request_hash"], bound_input_hash=raw["bound_input_hash"],
                bound_config_hash=raw["bound_config_hash"], supersedes=raw["supersedes"],
                test_vectors=tuple(vectors), content_sha256=content_sha256,
            )
        except (KeyError, TypeError, ValueError) as exc:
            if isinstance(exc, FormulaError):
                raise
            raise FormulaError("FORMULA_PROFILE_SCHEMA", "formula profile values are invalid") from exc
        profile.validate()
        return profile


def evaluate_formula_inputs(profile: FormulaProfile, inputs: Mapping[str, int]) -> int:
    if not isinstance(inputs, Mapping) or any(type(value) is not int for value in inputs.values()):
        raise FormulaError("FORMULA_INPUT_TYPE", "formula inputs must be exact integers")
    expression = profile.expression_id
    if expression is FormulaExpression.RATE_TIMES_BASE:
        if set(inputs) != {"base_amount_minor"}:
            raise FormulaError("FORMULA_INPUT_SET", "rate formula requires base_amount_minor")
        base = _bounded_minor(inputs["base_amount_minor"], "base_amount_minor")
        return round_half_up_ratio(
            base * profile.parameters["rate_numerator"], profile.parameters["rate_denominator"]
        )
    if expression is FormulaExpression.APPROVED_TIME_PRORATION:
        if set(inputs) != {"employer_cost_minor", "approved_project_time_units", "approved_total_time_units"}:
            raise FormulaError("FORMULA_INPUT_SET", "payroll formula requires cost, project time, and total time")
        cost = _bounded_minor(inputs["employer_cost_minor"], "employer_cost_minor", nonnegative=True)
        project_time = _exact_int(inputs["approved_project_time_units"], "approved_project_time_units", nonnegative=True)
        total_time = _exact_int(inputs["approved_total_time_units"], "approved_total_time_units", positive=True)
        if project_time > total_time:
            raise FormulaError("FORMULA_TIME_RANGE", "project time cannot exceed approved total time")
        return round_half_up_ratio(cost * project_time, total_time)
    if expression is FormulaExpression.SIMPLE_INTEREST_DAILY:
        if set(inputs) != {"principal_minor", "elapsed_days"}:
            raise FormulaError("FORMULA_INPUT_SET", "interest formula requires principal_minor and elapsed_days")
        principal = _bounded_minor(inputs["principal_minor"], "principal_minor", nonnegative=True)
        days = _exact_int(inputs["elapsed_days"], "elapsed_days", nonnegative=True)
        denominator = profile.parameters["annual_rate_denominator"] * profile.parameters["day_count_denominator"]
        return round_half_up_ratio(principal * profile.parameters["annual_rate_numerator"] * days, denominator)
    if expression is FormulaExpression.FX_RATE_TIMES_AMOUNT:
        raise FormulaError("FX_DEFERRED_PRODUCT_0_2", "FX conversion is registered but inactive in product 0.2")
    raise FormulaError("FORMULA_EXPRESSION_UNKNOWN", "formula expression is not registered")


@dataclass(frozen=True)
class FormulaRegistry:
    profiles: Tuple[FormulaProfile, ...]

    def validate(self) -> None:
        by_id: Dict[str, FormulaProfile] = {}
        for profile in self.profiles:
            profile.validate()
            if profile.profile_id in by_id:
                raise FormulaError("FORMULA_PROFILE_DUPLICATE", "formula profile ID is duplicated")
            by_id[profile.profile_id] = profile
        for profile in self.profiles:
            if profile.supersedes is not None:
                prior = by_id.get(profile.supersedes)
                if (
                    prior is None
                    or prior.formula_id != profile.formula_id
                    or prior.scope.as_tuple() != profile.scope.as_tuple()
                    or profile.status is not FormulaStatus.ACTIVE
                ):
                    raise FormulaError("FORMULA_SUPERSESSION_INVALID", "supersession must reference the same formula and scope")
                if prior.profile_id == profile.profile_id:
                    raise FormulaError("FORMULA_SUPERSESSION_CYCLE", "formula cannot supersede itself")
                prior_start, prior_end = prior.active_period()
                current_start, _ = profile.active_period()
                if current_start <= prior_start or prior_end >= current_start:
                    raise FormulaError(
                        "FORMULA_SUPERSESSION_ORDER",
                        "superseding profile must start after the prior effective period ends",
                    )
        for profile in self.profiles:
            seen = set()
            current = profile
            while current.supersedes is not None:
                if current.profile_id in seen:
                    raise FormulaError("FORMULA_SUPERSESSION_CYCLE", "formula supersession chain contains a cycle")
                seen.add(current.profile_id)
                current = by_id[current.supersedes]
        active = [item for item in self.profiles if item.status is FormulaStatus.ACTIVE]
        for index, left in enumerate(active):
            left_start, left_end = left.active_period()
            for right in active[index + 1 :]:
                right_start, right_end = right.active_period()
                if (
                    left.formula_id == right.formula_id
                    and left.scope.overlaps(right.scope)
                    and max(left_start, right_start) <= min(left_end, right_end)
                ):
                    raise FormulaError("FORMULA_ACTIVE_SCOPE_OVERLAP", "active formula scopes and effective dates overlap")

    def select(self, *, formula_id: str, as_of: date, scope: FormulaScope) -> FormulaProfile:
        self.validate()
        _text(formula_id, "formula_id")
        candidates = [item for item in self.profiles if item.formula_id == formula_id and item.applies_to(as_of, scope)]
        if not any(item.formula_id == formula_id for item in self.profiles):
            raise FormulaError("UNKNOWN_FORMULA", "requested formula is not registered")
        if not candidates:
            raise FormulaError("FORMULA_ACTIVE_PROFILE_MISSING", "no active formula profile applies to the requested date and scope")
        highest = max(item.scope.specificity() for item in candidates)
        selected = [item for item in candidates if item.scope.specificity() == highest]
        if len(selected) != 1:
            raise FormulaError("FORMULA_SELECTION_AMBIGUOUS", "formula selection did not resolve to exactly one profile")
        return selected[0]


def evaluate_formula(
    profile: FormulaProfile,
    *,
    inputs: Mapping[str, int],
    as_of: date,
    scope: FormulaScope,
    request_hash: str,
) -> FormulaEvaluation:
    profile.validate(require_active=True)
    if not profile.applies_to(as_of, scope):
        raise FormulaError("FORMULA_SCOPE_OR_DATE_MISMATCH", "formula is not active for the requested scope and date")
    if not SHA256_RE.fullmatch(request_hash) or profile.bound_request_hash != request_hash:
        raise FormulaError("FORMULA_REQUEST_BINDING_MISMATCH", "formula profile is not bound to the exact run request")
    amount = evaluate_formula_inputs(profile, inputs)
    payload = {
        "formula_id": profile.formula_id,
        "profile_id": profile.profile_id,
        "profile_content_sha256": profile.content_sha256,
        "request_hash": request_hash,
        "as_of": as_of.isoformat(),
        "scope": scope.as_dict(),
        "inputs": dict(inputs),
        "amount_minor": amount,
    }
    return FormulaEvaluation(profile.formula_id, profile.profile_id, amount, _digest(payload))


@dataclass(frozen=True)
class FormulaReadinessItem:
    formula_id: str
    status: str
    reason_code: Optional[str]
    allowed_resolutions: Tuple[str, ...] = (
        "SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"
    )

    def as_dict(self) -> Dict[str, Any]:
        return {
            "formula_id": self.formula_id,
            "status": self.status,
            "reason_code": self.reason_code,
            "allowed_resolutions": list(self.allowed_resolutions),
        }


@dataclass(frozen=True)
class FormulaReadinessReport:
    request_hash: str
    input_hash: str
    config_hash: str
    overall_status: str
    items: Tuple[FormulaReadinessItem, ...]
    user_action_required: bool
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.formula_readiness.v1",
            "request_hash": self.request_hash,
            "input_hash": self.input_hash,
            "config_hash": self.config_hash,
            "overall_status": self.overall_status,
            "items": [item.as_dict() for item in self.items],
            "user_action_required": self.user_action_required,
            "metric_inclusion_status": self.metric_inclusion_status,
        }


def assess_formula_readiness(
    registry: FormulaRegistry,
    *,
    requested_formula_ids: Sequence[str],
    as_of: date,
    scope: FormulaScope,
    request_hash: str,
    input_hash: str,
    config_hash: str,
) -> FormulaReadinessReport:
    if not requested_formula_ids or len(set(requested_formula_ids)) != len(tuple(requested_formula_ids)):
        raise FormulaError("FORMULA_REQUEST_INVALID", "requested formulas must be nonempty and unique")
    if not SHA256_RE.fullmatch(request_hash):
        raise FormulaError("FORMULA_REQUEST_HASH_INVALID", "request hash must be lowercase SHA256")
    if not SHA256_RE.fullmatch(input_hash) or not SHA256_RE.fullmatch(config_hash):
        raise FormulaError("FORMULA_BINDING_HASH_INVALID", "input and config hashes must be lowercase SHA256")
    items = []
    for formula_id in requested_formula_ids:
        try:
            profile = registry.select(formula_id=formula_id, as_of=as_of, scope=scope)
            profile.validate(require_active=True)
            if (
                profile.bound_request_hash != request_hash
                or profile.bound_input_hash != input_hash
                or profile.bound_config_hash != config_hash
            ):
                raise FormulaError(
                    "FORMULA_RUN_BINDING_MISMATCH",
                    "profile does not bind the exact request, input, and config",
                )
        except FormulaError as exc:
            items.append(FormulaReadinessItem(formula_id, "BLOCKED", exc.code))
        else:
            items.append(FormulaReadinessItem(formula_id, "PRESENT", None, ()))
    blocked = any(item.status != "PRESENT" for item in items)
    return FormulaReadinessReport(
        request_hash=request_hash,
        input_hash=input_hash,
        config_hash=config_hash,
        overall_status="BLOCKED_R8_POLICY_INPUTS" if blocked else "READY_R8_POLICY_INPUTS",
        items=tuple(items),
        user_action_required=blocked,
    )


class TaxSourceTier(str, Enum):
    DIRECT_PROJECT_EVIDENCE = "DIRECT_PROJECT_EVIDENCE"
    GOVERNED_PROJECT_LEDGER = "GOVERNED_PROJECT_LEDGER"
    EVIDENCE_BACKED_ALLOCATION_POLICY = "EVIDENCE_BACKED_ALLOCATION_POLICY"


class TaxRecoverability(str, Enum):
    RECOVERABLE = "RECOVERABLE"
    NON_RECOVERABLE = "NON_RECOVERABLE"
    PARTIALLY_RECOVERABLE = "PARTIALLY_RECOVERABLE"


@dataclass(frozen=True)
class ProjectTaxRecord:
    record_id: str
    scope: FormulaScope
    business_date: str
    gross_amount_minor: int
    tax_base_minor: int
    source_tax_amount_minor: int
    rate_numerator: int
    rate_denominator: int
    invoice_type: str
    recoverability: TaxRecoverability
    recoverable_tax_minor: int
    source_tier: TaxSourceTier
    evidence_refs: Tuple[str, ...]
    company_policy_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    bound_input_hash: str

    def validate(self) -> None:
        if not RECORD_ID_RE.fullmatch(self.record_id):
            raise FormulaError("TAX_RECORD_ID", "tax record ID must be opaque and canonical")
        self.scope.validate()
        _iso_date(self.business_date, "business_date")
        for name in ("gross_amount_minor", "tax_base_minor", "source_tax_amount_minor", "recoverable_tax_minor"):
            _bounded_minor(getattr(self, name), name, nonnegative=True)
        _exact_int(self.rate_numerator, "rate_numerator", nonnegative=True)
        _exact_int(self.rate_denominator, "rate_denominator", positive=True)
        _text(self.invoice_type, "invoice_type")
        if not isinstance(self.recoverability, TaxRecoverability) or not isinstance(self.source_tier, TaxSourceTier):
            raise FormulaError("TAX_ENUM_UNKNOWN", "tax source tier and recoverability must be registered")
        if self.recoverable_tax_minor > self.source_tax_amount_minor:
            raise FormulaError("TAX_RECOVERABLE_RANGE", "recoverable tax cannot exceed source tax")
        if self.recoverability is TaxRecoverability.RECOVERABLE and self.recoverable_tax_minor != self.source_tax_amount_minor:
            raise FormulaError("TAX_RECOVERABILITY_CONFLICT", "recoverable tax must equal source tax")
        if self.recoverability is TaxRecoverability.NON_RECOVERABLE and self.recoverable_tax_minor != 0:
            raise FormulaError("TAX_RECOVERABILITY_CONFLICT", "non-recoverable tax must have zero recoverable amount")
        if (
            not self.evidence_refs
            or len(self.evidence_refs) != len(set(self.evidence_refs))
            or any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs)
        ):
            raise FormulaError("TAX_EVIDENCE_REQUIRED", "project tax requires direct hash-bound evidence")
        if len(self.company_policy_refs) != len(set(self.company_policy_refs)) or any(
            not POLICY_REF_RE.fullmatch(item) for item in self.company_policy_refs
        ):
            raise FormulaError("TAX_POLICY_REF_INVALID", "tax policy references must be hash-bound")
        if len(self.input_resolution_refs) != len(set(self.input_resolution_refs)) or any(
            not RESOLUTION_REF_RE.fullmatch(item) for item in self.input_resolution_refs
        ):
            raise FormulaError("TAX_RESOLUTION_REF_INVALID", "tax input resolutions must be canonical")
        if self.source_tier is TaxSourceTier.EVIDENCE_BACKED_ALLOCATION_POLICY and not self.company_policy_refs:
            raise FormulaError("TAX_ALLOCATION_POLICY_REQUIRED", "allocated project tax requires a company policy reference")
        if not SHA256_RE.fullmatch(self.bound_input_hash):
            raise FormulaError("TAX_INPUT_HASH", "tax record requires an exact input hash")
        if self.recoverability is TaxRecoverability.PARTIALLY_RECOVERABLE and not (
            0 < self.recoverable_tax_minor < self.source_tax_amount_minor
        ):
            raise FormulaError(
                "TAX_RECOVERABILITY_CONFLICT",
                "partially recoverable tax requires a strict partial amount",
            )


@dataclass(frozen=True)
class TaxEvaluation:
    record_id: str
    source_tax_amount_minor: int
    recomputed_tax_amount_minor: int
    tax_delta_minor: int
    gross_arithmetic_delta_minor: int
    recoverable_tax_minor: int
    status: str
    profile_id: str
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def evaluate_project_tax(record: ProjectTaxRecord, profile: FormulaProfile, *, request_hash: str) -> TaxEvaluation:
    record.validate()
    if profile.formula_kind is not FormulaKind.PROJECT_TAX_RATE or profile.formula_id != "FORM-TAX-V2":
        raise FormulaError("TAX_FORMULA_PROFILE_MISMATCH", "tax record requires the registered project-tax formula")
    if dict(profile.parameters) != {
        "rate_numerator": record.rate_numerator,
        "rate_denominator": record.rate_denominator,
    }:
        raise FormulaError("TAX_RATE_PROFILE_MISMATCH", "record tax rate differs from the bound formula profile")
    if profile.bound_input_hash != record.bound_input_hash:
        raise FormulaError("TAX_INPUT_BINDING_MISMATCH", "tax record differs from the formula-bound input snapshot")
    evaluated = evaluate_formula(
        profile,
        inputs={"base_amount_minor": record.tax_base_minor},
        as_of=_iso_date(record.business_date, "business_date"),
        scope=record.scope,
        request_hash=request_hash,
    )
    tax_delta = record.source_tax_amount_minor - evaluated.amount_minor
    gross_delta = record.gross_amount_minor - record.tax_base_minor - record.source_tax_amount_minor
    status = "PASS_R8_TAX_CONTROL" if tax_delta == 0 and gross_delta == 0 else "BLOCKED_R8_TAX_ARITHMETIC"
    return TaxEvaluation(
        record_id=record.record_id,
        source_tax_amount_minor=record.source_tax_amount_minor,
        recomputed_tax_amount_minor=evaluated.amount_minor,
        tax_delta_minor=tax_delta,
        gross_arithmetic_delta_minor=gross_delta,
        recoverable_tax_minor=record.recoverable_tax_minor,
        status=status,
        profile_id=profile.profile_id,
    )


class InterestMovementKind(str, Enum):
    RECEIPT = "RECEIPT"
    PAYMENT = "PAYMENT"
    PREPAYMENT = "PREPAYMENT"


class InterestDayCountConvention(str, Enum):
    ACTUAL_365 = "ACTUAL_365"
    ACTUAL_360 = "ACTUAL_360"


@dataclass(frozen=True)
class InterestMovement:
    movement_id: str
    movement_date: str
    kind: InterestMovementKind
    principal_delta_minor: int
    evidence_refs: Tuple[str, ...]

    def validate(self) -> None:
        if not RECORD_ID_RE.fullmatch(self.movement_id):
            raise FormulaError("INTEREST_MOVEMENT_ID", "interest movement ID must be opaque and canonical")
        _iso_date(self.movement_date, "movement_date")
        if not isinstance(self.kind, InterestMovementKind):
            raise FormulaError("INTEREST_MOVEMENT_KIND", "interest movement kind is not registered")
        delta = _bounded_minor(self.principal_delta_minor, "principal_delta_minor")
        if delta == 0:
            raise FormulaError("INTEREST_MOVEMENT_ZERO", "interest movement cannot be zero")
        if self.kind is InterestMovementKind.RECEIPT and delta < 0:
            raise FormulaError("INTEREST_MOVEMENT_SIGN", "receipt must increase principal")
        if self.kind in {InterestMovementKind.PAYMENT, InterestMovementKind.PREPAYMENT} and delta > 0:
            raise FormulaError("INTEREST_MOVEMENT_SIGN", "payment and prepayment must reduce principal")
        if (
            not self.evidence_refs
            or len(self.evidence_refs) != len(set(self.evidence_refs))
            or any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs)
        ):
            raise FormulaError("INTEREST_EVIDENCE_REQUIRED", "interest movement requires hash-bound evidence")


@dataclass(frozen=True)
class InterestInput:
    calculation_id: str
    scope: FormulaScope
    start_date: str
    end_date: str
    opening_principal_minor: int
    movements: Tuple[InterestMovement, ...]
    same_day_order: Tuple[InterestMovementKind, ...]
    day_count_convention: InterestDayCountConvention
    evidence_refs: Tuple[str, ...]
    company_policy_refs: Tuple[str, ...]
    input_resolution_refs: Tuple[str, ...]
    bound_input_hash: str

    def validate(self) -> None:
        if not RECORD_ID_RE.fullmatch(self.calculation_id):
            raise FormulaError("INTEREST_CALCULATION_ID", "interest calculation ID must be opaque and canonical")
        self.scope.validate()
        start = _iso_date(self.start_date, "start_date")
        end = _iso_date(self.end_date, "end_date")
        if end <= start:
            raise FormulaError("INTEREST_DATE_RANGE", "interest end date must be after start date")
        _bounded_minor(self.opening_principal_minor, "opening_principal_minor", nonnegative=True)
        if set(self.same_day_order) != set(InterestMovementKind) or len(self.same_day_order) != len(InterestMovementKind):
            raise FormulaError("INTEREST_CASH_ORDER", "same-day receipt, payment, and prepayment order must be explicit")
        if not isinstance(self.day_count_convention, InterestDayCountConvention):
            raise FormulaError("INTEREST_DAY_COUNT", "interest day-count convention is not registered")
        seen = set()
        for movement in self.movements:
            movement.validate()
            if movement.movement_id in seen:
                raise FormulaError("INTEREST_MOVEMENT_DUPLICATE", "interest movement ID is duplicated")
            seen.add(movement.movement_id)
            movement_date = _iso_date(movement.movement_date, "movement_date")
            if not start <= movement_date <= end:
                raise FormulaError("INTEREST_MOVEMENT_RANGE", "interest movement lies outside the calculation period")
        if (
            not self.evidence_refs
            or len(self.evidence_refs) != len(set(self.evidence_refs))
            or any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs)
        ):
            raise FormulaError("INTEREST_EVIDENCE_REQUIRED", "interest calculation requires hash-bound evidence")
        if (
            not self.company_policy_refs
            or len(self.company_policy_refs) != len(set(self.company_policy_refs))
            or any(not POLICY_REF_RE.fullmatch(item) for item in self.company_policy_refs)
        ):
            raise FormulaError("INTEREST_POLICY_REQUIRED", "interest calculation requires a hash-bound policy")
        if len(self.input_resolution_refs) != len(set(self.input_resolution_refs)) or any(
            not RESOLUTION_REF_RE.fullmatch(item) for item in self.input_resolution_refs
        ):
            raise FormulaError("INTEREST_RESOLUTION_REF_INVALID", "interest input resolutions must be canonical")
        if not SHA256_RE.fullmatch(self.bound_input_hash):
            raise FormulaError("INTEREST_INPUT_HASH", "interest input requires an exact input hash")


@dataclass(frozen=True)
class InterestEvaluation:
    calculation_id: str
    interest_amount_minor: int
    ending_principal_minor: int
    elapsed_days: int
    interval_count: int
    profile_id: str
    status: str = "PASS_R8_INTEREST_CONTROL_NOT_METRIC"
    metric_inclusion_status: str = "NOT_EVALUATED_R8"

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.__dict__)


def calculate_interest(value: InterestInput, profile: FormulaProfile, *, request_hash: str) -> InterestEvaluation:
    value.validate()
    profile.validate(require_active=True)
    if profile.formula_id != "FORM-INTEREST-V2" or profile.formula_kind is not FormulaKind.CAPITAL_INTEREST:
        raise FormulaError("INTEREST_FORMULA_PROFILE_MISMATCH", "interest input requires the registered interest formula")
    expected_day_basis = {
        InterestDayCountConvention.ACTUAL_365: 365,
        InterestDayCountConvention.ACTUAL_360: 360,
    }[value.day_count_convention]
    if profile.parameters["day_count_denominator"] != expected_day_basis:
        raise FormulaError("INTEREST_DAY_COUNT_PROFILE_MISMATCH", "interest day-count convention differs from the formula profile")
    as_of = _iso_date(value.start_date, "start_date")
    if not profile.applies_to(as_of, value.scope) or profile.bound_request_hash != request_hash:
        raise FormulaError("INTEREST_PROFILE_BINDING", "interest profile does not bind the exact period, scope, and request")
    if profile.bound_input_hash != value.bound_input_hash:
        raise FormulaError("INTEREST_INPUT_BINDING", "interest schedule differs from the formula-bound input snapshot")
    order = {kind: index for index, kind in enumerate(value.same_day_order)}
    movements = sorted(
        value.movements,
        key=lambda item: (_iso_date(item.movement_date, "movement_date"), order[item.kind], item.movement_id),
    )
    current_date = _iso_date(value.start_date, "start_date")
    end_date = _iso_date(value.end_date, "end_date")
    principal = value.opening_principal_minor
    interest = 0
    intervals = 0
    for movement in movements:
        movement_date = _iso_date(movement.movement_date, "movement_date")
        elapsed = (movement_date - current_date).days
        if elapsed:
            interest += evaluate_formula_inputs(profile, {"principal_minor": principal, "elapsed_days": elapsed})
            intervals += 1
            current_date = movement_date
        principal += movement.principal_delta_minor
        if principal < 0:
            raise FormulaError("INTEREST_NEGATIVE_PRINCIPAL", "cash ordering would produce a negative principal")
        _bounded_minor(principal, "principal")
    elapsed = (end_date - current_date).days
    if elapsed:
        interest += evaluate_formula_inputs(profile, {"principal_minor": principal, "elapsed_days": elapsed})
        intervals += 1
    _bounded_minor(interest, "interest_amount_minor")
    return InterestEvaluation(
        calculation_id=value.calculation_id,
        interest_amount_minor=interest,
        ending_principal_minor=principal,
        elapsed_days=(end_date - _iso_date(value.start_date, "start_date")).days,
        interval_count=intervals,
        profile_id=profile.profile_id,
    )
