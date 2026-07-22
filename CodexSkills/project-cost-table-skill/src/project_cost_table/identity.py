"""Evidence-bound project/entity/WBS/contract identity with hard conflict gates."""

from __future__ import annotations

import hashlib
import json
import re
import stat
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from .paths import PathSafetyError, atomic_write_text


IDENTITY_POLICY_BYTES_MAX = 1024 * 1024
EXPECTED_POLICY_ID = "POLICY-KMFA-IDENTITY-MASTER-001"
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAPPING_RESOLUTION_RE = re.compile(r"^identity_resolution_[0-9a-f]{32}$")
EVIDENCE_REF_RE = re.compile(r"^evidence:[0-9a-f]{64}$")
SOURCE_ALIAS_RE = re.compile(r"^source://[A-Za-z0-9._-]{1,64}/\S{1,256}$")
SOURCE_RECORD_REF_RE = re.compile(r"^rec_source_record_[0-9a-f]{32}$")
IDENTITY_RECORD_REF_RE = re.compile(r"^identity_record_[0-9a-f]{32}$")
CANDIDATE_ID_RE = re.compile(r"^identity_candidate_[0-9a-f]{32}$")
REVIEW_TASK_ID_RE = re.compile(r"^review_identity_[0-9a-f]{32}$")
PRIVATE_TEXT_REF_RE = re.compile(r"^private://[A-Za-z0-9._/-]{1,256}$")
IDENTITY_STATUSES = frozenset({"APPROVED", "CANDIDATE", "CONFLICT", "UNMAPPED", "REVOKED", "SUPERSEDED"})
ACTIVE_MAPPING_STATUSES = frozenset({"APPROVED"})
EXPECTED_CANONICAL_KEY_FIELDS = (
    "canonical_project_id",
    "legal_entity_id",
    "wbs_or_cost_code",
    "valid_at",
)
EXPECTED_MATCH_ORDER = (
    "EXACT_CANONICAL_SCOPE",
    "EXACT_CONTRACT_ID",
    "EXACT_GOVERNED_SOURCE_ID",
    "QUALIFIED_MAPPING_RESOLUTION",
    "CANDIDATE_ONLY",
)
EXPECTED_CANDIDATE_ONLY_FIELDS = (
    "project_code",
    "project_name",
    "customer_id",
    "free_text_ref",
    "amount_only",
)
EXPECTED_HARD_CONFLICT_CODES = frozenset(
    {
        "IDENTITY_EFFECTIVE_PERIOD_OVERLAP",
        "IDENTITY_ALIAS_CONFLICT",
        "IDENTITY_MULTIPLE_ACTIVE_MATCHES",
        "IDENTITY_CONTRACT_PROJECT_CONFLICT",
        "IDENTITY_IDENTIFIER_CONFLICT",
        "IDENTITY_CROSS_ENTITY_AMBIGUOUS",
        "IDENTITY_STALE_MAPPING",
        "IDENTITY_INCOMPLETE_CANONICAL_KEY",
        "IDENTITY_CANDIDATE_ONLY",
        "IDENTITY_UNMAPPED",
    }
)


class IdentityError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


def _normalized_text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise IdentityError("IDENTITY_FIELD_INVALID", "%s must be nonempty text" % field)
    normalized = unicodedata.normalize("NFC", value.strip())
    if normalized != value:
        raise IdentityError(
            "IDENTITY_IDENTIFIER_NOT_CANONICAL",
            "%s must already be NFC-normalized without surrounding whitespace" % field,
        )
    if "\x00" in normalized or "\r" in normalized or "\n" in normalized:
        raise IdentityError("IDENTITY_FIELD_INVALID", "%s contains a forbidden control character" % field)
    return normalized


def _string_tuple(value: Any, field: str, *, allow_empty: bool = True) -> Tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise IdentityError("IDENTITY_FIELD_INVALID", "%s must be a string list" % field)
    result = tuple(_normalized_text(item, field) or "" for item in value)
    if not allow_empty and not result:
        raise IdentityError("IDENTITY_FIELD_INVALID", "%s cannot be empty" % field)
    if len(set(result)) != len(result):
        raise IdentityError("IDENTITY_FIELD_INVALID", "%s cannot contain duplicates" % field)
    return result


def _iso_date(value: str, field: str) -> date:
    try:
        return date.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise IdentityError("IDENTITY_DATE_INVALID", "%s must be an ISO date" % field) from exc


def _canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _opaque_ref(prefix: str, value: Any) -> str:
    return prefix + hashlib.sha256(_canonical_json(value)).hexdigest()[:32]


@dataclass(frozen=True)
class IdentityPolicy:
    policy_id: str
    canonical_key_fields: Tuple[str, ...]
    active_mapping_statuses: Tuple[str, ...]
    final_match_order: Tuple[str, ...]
    candidate_only_fields: Tuple[str, ...]
    hard_conflict_codes: Tuple[str, ...]
    identifier_normalization: str
    effective_period_end_inclusive: bool
    identity_ambiguity_allowed: int
    unresolved_final_mapping_allowed: int
    fuzzy_final_mapping_allowed: bool
    cross_entity_destructive_normalization_allowed: bool
    company_approval_state_managed: bool
    content_sha256: str

    def validate(self) -> None:
        if (
            self.policy_id != EXPECTED_POLICY_ID
            or self.canonical_key_fields != EXPECTED_CANONICAL_KEY_FIELDS
            or self.active_mapping_statuses != ("APPROVED",)
            or self.final_match_order != EXPECTED_MATCH_ORDER
            or self.candidate_only_fields != EXPECTED_CANDIDATE_ONLY_FIELDS
            or self.hard_conflict_codes != tuple(sorted(EXPECTED_HARD_CONFLICT_CODES))
            or self.identifier_normalization != "NFC_TRIM_CASE_SENSITIVE"
            or self.effective_period_end_inclusive is not True
            or type(self.identity_ambiguity_allowed) is not int
            or self.identity_ambiguity_allowed != 0
            or type(self.unresolved_final_mapping_allowed) is not int
            or self.unresolved_final_mapping_allowed != 0
            or self.fuzzy_final_mapping_allowed is not False
            or self.cross_entity_destructive_normalization_allowed is not False
            or self.company_approval_state_managed is not False
        ):
            raise IdentityError("IDENTITY_POLICY_RELAXED", "identity policy object is not the locked R4 policy")
        if not isinstance(self.content_sha256, str) or not SHA256_RE.fullmatch(self.content_sha256):
            raise IdentityError("IDENTITY_POLICY_HASH_INVALID", "identity policy hash is invalid")

    @classmethod
    def from_yaml(cls, path: Path) -> "IdentityPolicy":
        value = Path(path)
        try:
            metadata = value.lstat()
        except OSError as exc:
            raise IdentityError("IDENTITY_POLICY_UNAVAILABLE", "identity policy cannot be accessed") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
            raise IdentityError("IDENTITY_POLICY_PATH_UNSAFE", "identity policy must be a single-link regular file")
        if metadata.st_size > IDENTITY_POLICY_BYTES_MAX:
            raise IdentityError("IDENTITY_POLICY_TOO_LARGE", "identity policy exceeds its metadata ceiling")
        try:
            data = value.read_bytes()
            raw = yaml.safe_load(data.decode("utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise IdentityError("IDENTITY_POLICY_PARSE", "identity policy is not valid UTF-8 YAML") from exc
        expected_fields = {
            "schema_version",
            "policy_id",
            "canonical_key_fields",
            "active_mapping_statuses",
            "final_match_order",
            "candidate_only_fields",
            "hard_conflict_codes",
            "identifier_normalization",
            "effective_period_end_inclusive",
            "identity_ambiguity_allowed",
            "unresolved_final_mapping_allowed",
            "fuzzy_final_mapping_allowed",
            "cross_entity_destructive_normalization_allowed",
            "company_approval_state_managed",
        }
        if not isinstance(raw, dict) or set(raw) != expected_fields:
            raise IdentityError("IDENTITY_POLICY_SCHEMA", "identity policy fields differ from v1")
        if raw.get("schema_version") != "kmfa.project_cost.identity_policy.v1":
            raise IdentityError("IDENTITY_POLICY_SCHEMA", "identity policy schema version is unsupported")
        canonical_fields = _string_tuple(raw.get("canonical_key_fields"), "canonical_key_fields", allow_empty=False)
        active_statuses = _string_tuple(raw.get("active_mapping_statuses"), "active_mapping_statuses", allow_empty=False)
        match_order = _string_tuple(raw.get("final_match_order"), "final_match_order", allow_empty=False)
        candidate_fields = _string_tuple(raw.get("candidate_only_fields"), "candidate_only_fields", allow_empty=False)
        conflict_codes = _string_tuple(raw.get("hard_conflict_codes"), "hard_conflict_codes", allow_empty=False)
        exact_integers = (
            type(raw.get("identity_ambiguity_allowed")) is int
            and type(raw.get("unresolved_final_mapping_allowed")) is int
        )
        exact_booleans = all(
            type(raw.get(field)) is bool
            for field in (
                "effective_period_end_inclusive",
                "fuzzy_final_mapping_allowed",
                "cross_entity_destructive_normalization_allowed",
                "company_approval_state_managed",
            )
        )
        if not exact_integers or not exact_booleans:
            raise IdentityError("IDENTITY_POLICY_TYPE", "identity policy booleans and integers require exact types")
        if (
            canonical_fields != EXPECTED_CANONICAL_KEY_FIELDS
            or active_statuses != ("APPROVED",)
            or match_order != EXPECTED_MATCH_ORDER
            or candidate_fields != EXPECTED_CANDIDATE_ONLY_FIELDS
            or set(conflict_codes) != EXPECTED_HARD_CONFLICT_CODES
            or raw.get("policy_id") != EXPECTED_POLICY_ID
            or raw.get("identifier_normalization") != "NFC_TRIM_CASE_SENSITIVE"
            or raw.get("effective_period_end_inclusive") is not True
            or raw.get("identity_ambiguity_allowed") != 0
            or raw.get("unresolved_final_mapping_allowed") != 0
            or raw.get("fuzzy_final_mapping_allowed") is not False
            or raw.get("cross_entity_destructive_normalization_allowed") is not False
            or raw.get("company_approval_state_managed") is not False
        ):
            raise IdentityError("IDENTITY_POLICY_RELAXED", "identity correctness or company-process boundary was relaxed")
        policy = cls(
            policy_id=_normalized_text(raw.get("policy_id"), "policy_id") or "",
            canonical_key_fields=canonical_fields,
            active_mapping_statuses=active_statuses,
            final_match_order=match_order,
            candidate_only_fields=candidate_fields,
            hard_conflict_codes=tuple(sorted(conflict_codes)),
            identifier_normalization=raw["identifier_normalization"],
            effective_period_end_inclusive=True,
            identity_ambiguity_allowed=0,
            unresolved_final_mapping_allowed=0,
            fuzzy_final_mapping_allowed=False,
            cross_entity_destructive_normalization_allowed=False,
            company_approval_state_managed=False,
            content_sha256=hashlib.sha256(data).hexdigest(),
        )
        policy.validate()
        return policy


@dataclass(frozen=True)
class ProjectIdentityRecord:
    canonical_project_id: str
    legal_entity_id: str
    wbs_or_cost_code: str
    project_code: Optional[str]
    project_name: Optional[str]
    customer_id: Optional[str]
    contract_ids: Tuple[str, ...]
    source_aliases: Tuple[str, ...]
    valid_from: str
    valid_to: Optional[str]
    identity_status: str
    mapping_resolution_ref: str
    evidence_refs: Tuple[str, ...]

    def validate(self) -> None:
        for field in ("canonical_project_id", "legal_entity_id", "wbs_or_cost_code"):
            _normalized_text(getattr(self, field), field)
        for field in ("project_code", "project_name", "customer_id"):
            _normalized_text(getattr(self, field), field, optional=True)
        contracts = _string_tuple(self.contract_ids, "contract_ids")
        aliases = _string_tuple(self.source_aliases, "source_aliases")
        evidence = _string_tuple(self.evidence_refs, "evidence_refs")
        if contracts != self.contract_ids or aliases != self.source_aliases or evidence != self.evidence_refs:
            raise IdentityError("IDENTITY_FIELD_INVALID", "identity list fields must use immutable tuples")
        if any(not SOURCE_ALIAS_RE.fullmatch(item) for item in aliases):
            raise IdentityError("GOVERNED_SOURCE_ID_INVALID", "source aliases require source://system/id form")
        if self.identity_status not in IDENTITY_STATUSES:
            raise IdentityError("IDENTITY_STATUS_INVALID", "identity status is not registered")
        if not MAPPING_RESOLUTION_RE.fullmatch(self.mapping_resolution_ref):
            raise IdentityError("MAPPING_RESOLUTION_REF_INVALID", "mapping resolution reference is not opaque")
        if any(not EVIDENCE_REF_RE.fullmatch(item) for item in evidence):
            raise IdentityError("IDENTITY_EVIDENCE_REF_INVALID", "evidence references must be hash-bound and opaque")
        if self.identity_status == "APPROVED" and not contracts:
            raise IdentityError("IDENTITY_CONTRACT_REQUIRED", "active mapping requires at least one contract ID")
        if self.identity_status == "APPROVED" and not evidence:
            raise IdentityError("IDENTITY_EVIDENCE_REQUIRED", "active mapping requires qualified evidence")
        start = _iso_date(self.valid_from, "valid_from")
        if self.valid_to is not None and _iso_date(self.valid_to, "valid_to") < start:
            raise IdentityError("IDENTITY_PERIOD_REVERSED", "valid_to cannot precede valid_from")

    @property
    def identity_ref(self) -> str:
        return _opaque_ref("identity_record_", self.as_private_dict())

    @property
    def scope_key(self) -> Tuple[str, str, str]:
        return (self.canonical_project_id, self.legal_entity_id, self.wbs_or_cost_code)

    def is_active_at(self, valid_at: date) -> bool:
        if self.identity_status not in ACTIVE_MAPPING_STATUSES:
            return False
        start = _iso_date(self.valid_from, "valid_from")
        end = _iso_date(self.valid_to, "valid_to") if self.valid_to is not None else date.max
        return start <= valid_at <= end

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "canonical_project_id": self.canonical_project_id,
            "legal_entity_id": self.legal_entity_id,
            "wbs_or_cost_code": self.wbs_or_cost_code,
            "project_code": self.project_code,
            "project_name": self.project_name,
            "customer_id": self.customer_id,
            "contract_ids": sorted(self.contract_ids),
            "source_aliases": sorted(self.source_aliases),
            "valid_from": self.valid_from,
            "valid_to": self.valid_to,
            "identity_status": self.identity_status,
            "mapping_resolution_ref": self.mapping_resolution_ref,
            "evidence_refs": sorted(self.evidence_refs),
        }


def project_identity_from_mapping(raw: Mapping[str, Any]) -> ProjectIdentityRecord:
    expected = {
        "canonical_project_id",
        "legal_entity_id",
        "wbs_or_cost_code",
        "project_code",
        "project_name",
        "customer_id",
        "contract_ids",
        "source_aliases",
        "valid_from",
        "valid_to",
        "identity_status",
        "mapping_resolution_ref",
        "evidence_refs",
    }
    if not isinstance(raw, Mapping) or set(raw) != expected:
        raise IdentityError("PROJECT_RECORD_SCHEMA_DRIFT", "project identity fields differ from v2")
    record = ProjectIdentityRecord(
        canonical_project_id=_normalized_text(raw.get("canonical_project_id"), "canonical_project_id") or "",
        legal_entity_id=_normalized_text(raw.get("legal_entity_id"), "legal_entity_id") or "",
        wbs_or_cost_code=_normalized_text(raw.get("wbs_or_cost_code"), "wbs_or_cost_code") or "",
        project_code=_normalized_text(raw.get("project_code"), "project_code", optional=True),
        project_name=_normalized_text(raw.get("project_name"), "project_name", optional=True),
        customer_id=_normalized_text(raw.get("customer_id"), "customer_id", optional=True),
        contract_ids=_string_tuple(raw.get("contract_ids"), "contract_ids"),
        source_aliases=_string_tuple(raw.get("source_aliases"), "source_aliases"),
        valid_from=_normalized_text(raw.get("valid_from"), "valid_from") or "",
        valid_to=_normalized_text(raw.get("valid_to"), "valid_to", optional=True),
        identity_status=_normalized_text(raw.get("identity_status"), "identity_status") or "",
        mapping_resolution_ref=_normalized_text(raw.get("mapping_resolution_ref"), "mapping_resolution_ref") or "",
        evidence_refs=_string_tuple(raw.get("evidence_refs"), "evidence_refs"),
    )
    record.validate()
    return record


@dataclass(frozen=True)
class IdentityLookup:
    valid_at: str
    expected_master_hash: str
    source_record_refs: Tuple[str, ...]
    requested_metrics: Tuple[str, ...] = ()
    canonical_project_id: Optional[str] = None
    legal_entity_id: Optional[str] = None
    wbs_or_cost_code: Optional[str] = None
    contract_id: Optional[str] = None
    governed_source_identifier: Optional[str] = None
    mapping_resolution_ref: Optional[str] = None
    project_code: Optional[str] = None
    project_name: Optional[str] = None
    customer_id: Optional[str] = None
    free_text_ref: Optional[str] = None

    def validate(self) -> None:
        _iso_date(self.valid_at, "valid_at")
        if not SHA256_RE.fullmatch(self.expected_master_hash):
            raise IdentityError("IDENTITY_MASTER_HASH_INVALID", "lookup requires the current identity-master hash")
        source_refs = _string_tuple(self.source_record_refs, "source_record_refs", allow_empty=False)
        metrics = _string_tuple(self.requested_metrics, "requested_metrics")
        if source_refs != self.source_record_refs or metrics != self.requested_metrics:
            raise IdentityError("IDENTITY_FIELD_INVALID", "lookup list fields must use immutable tuples")
        if any(not SOURCE_RECORD_REF_RE.fullmatch(item) for item in source_refs):
            raise IdentityError("SOURCE_RECORD_REF_INVALID", "identity lookup requires opaque source-record refs")
        optional_fields = (
            "canonical_project_id",
            "legal_entity_id",
            "wbs_or_cost_code",
            "contract_id",
            "governed_source_identifier",
            "mapping_resolution_ref",
            "project_code",
            "project_name",
            "customer_id",
            "free_text_ref",
        )
        for field in optional_fields:
            _normalized_text(getattr(self, field), field, optional=True)
        if self.governed_source_identifier is not None and not SOURCE_ALIAS_RE.fullmatch(
            self.governed_source_identifier
        ):
            raise IdentityError("GOVERNED_SOURCE_ID_INVALID", "governed source ID requires source://system/id form")
        if self.mapping_resolution_ref is not None and not MAPPING_RESOLUTION_RE.fullmatch(
            self.mapping_resolution_ref
        ):
            raise IdentityError("MAPPING_RESOLUTION_REF_INVALID", "mapping resolution reference is not opaque")
        if self.free_text_ref is not None and not PRIVATE_TEXT_REF_RE.fullmatch(self.free_text_ref):
            raise IdentityError("FREE_TEXT_REF_INVALID", "free text must remain behind a private opaque reference")
        if not any(getattr(self, field) is not None for field in optional_fields):
            raise IdentityError("IDENTITY_LOOKUP_EMPTY", "identity lookup has no governed or candidate identifiers")

    @property
    def binding_hash(self) -> str:
        self.validate()
        return hashlib.sha256(
            _canonical_json(
                {
                    "valid_at": self.valid_at,
                    "expected_master_hash": self.expected_master_hash,
                    "source_record_refs": sorted(self.source_record_refs),
                    "requested_metrics": sorted(self.requested_metrics),
                    "canonical_project_id": self.canonical_project_id,
                    "legal_entity_id": self.legal_entity_id,
                    "wbs_or_cost_code": self.wbs_or_cost_code,
                    "contract_id": self.contract_id,
                    "governed_source_identifier": self.governed_source_identifier,
                    "mapping_resolution_ref": self.mapping_resolution_ref,
                    "project_code": self.project_code,
                    "project_name": self.project_name,
                    "customer_id": self.customer_id,
                    "free_text_ref": self.free_text_ref,
                }
            )
        ).hexdigest()


@dataclass(frozen=True)
class IdentityCandidate:
    candidate_id: str
    lookup_hash: str
    reason_code: str
    candidate_record_refs: Tuple[str, ...]
    source_record_refs: Tuple[str, ...]
    requested_metrics: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]

    def validate(self) -> None:
        for field, values in (
            ("candidate_record_refs", self.candidate_record_refs),
            ("source_record_refs", self.source_record_refs),
            ("requested_metrics", self.requested_metrics),
            ("evidence_refs", self.evidence_refs),
        ):
            if _string_tuple(values, field) != values:
                raise IdentityError("IDENTITY_FIELD_INVALID", "%s must use an immutable tuple" % field)
        if not CANDIDATE_ID_RE.fullmatch(self.candidate_id) or not SHA256_RE.fullmatch(self.lookup_hash):
            raise IdentityError("IDENTITY_CANDIDATE_ID_INVALID", "identity candidate references are invalid")
        if self.reason_code not in EXPECTED_HARD_CONFLICT_CODES:
            raise IdentityError("IDENTITY_CANDIDATE_REASON_INVALID", "candidate reason is not a registered R4 blocker")
        if any(not IDENTITY_RECORD_REF_RE.fullmatch(item) for item in self.candidate_record_refs):
            raise IdentityError("IDENTITY_RECORD_REF_INVALID", "candidate record refs must be opaque")
        if any(not SOURCE_RECORD_REF_RE.fullmatch(item) for item in self.source_record_refs):
            raise IdentityError("SOURCE_RECORD_REF_INVALID", "candidate source refs must be opaque")
        if any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs):
            raise IdentityError("IDENTITY_EVIDENCE_REF_INVALID", "candidate evidence refs must be hash-bound")
    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.identity_candidate.v1",
            "candidate_id": self.candidate_id,
            "lookup_hash": self.lookup_hash,
            "reason_code": self.reason_code,
            "candidate_record_refs": sorted(self.candidate_record_refs),
            "source_record_refs": sorted(self.source_record_refs),
            "requested_metrics": sorted(self.requested_metrics),
            "evidence_refs": sorted(self.evidence_refs),
        }


@dataclass(frozen=True)
class IdentityReviewTask:
    task_id: str
    severity: str
    task_type: str
    status: str
    blocking_metrics: Tuple[str, ...]
    description: str
    required_input_or_resolution_type: Optional[str]
    candidate_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    resolution_ref: Optional[str]

    def validate(self) -> None:
        for field, values in (
            ("blocking_metrics", self.blocking_metrics),
            ("candidate_refs", self.candidate_refs),
            ("evidence_refs", self.evidence_refs),
        ):
            if _string_tuple(values, field) != values:
                raise IdentityError("IDENTITY_FIELD_INVALID", "%s must use an immutable tuple" % field)
        if not REVIEW_TASK_ID_RE.fullmatch(self.task_id):
            raise IdentityError("REVIEW_TASK_ID_INVALID", "identity review task ID must be opaque")
        if self.severity not in {"P0", "P1", "P2", "P3"}:
            raise IdentityError("REVIEW_TASK_SEVERITY_INVALID", "review task severity is invalid")
        if self.status not in {"PENDING", "IN_REVIEW", "APPROVED", "REJECTED", "CLOSED", "SUPERSEDED"}:
            raise IdentityError("REVIEW_TASK_STATUS_INVALID", "review task status is invalid")
        if not re.fullmatch(r"IDENTITY_[A-Z0-9_]{2,127}", self.task_type):
            raise IdentityError("REVIEW_TASK_TYPE_INVALID", "identity review task type is invalid")
        _normalized_text(self.description, "description")
        _normalized_text(
            self.required_input_or_resolution_type,
            "required_input_or_resolution_type",
            optional=True,
        )
        if any(not EVIDENCE_REF_RE.fullmatch(item) for item in self.evidence_refs):
            raise IdentityError("IDENTITY_EVIDENCE_REF_INVALID", "review evidence refs must be hash-bound")
        if self.resolution_ref is not None and not MAPPING_RESOLUTION_RE.fullmatch(self.resolution_ref):
            raise IdentityError("MAPPING_RESOLUTION_REF_INVALID", "review resolution ref is invalid")
        if any(
            not (IDENTITY_RECORD_REF_RE.fullmatch(item) or CANDIDATE_ID_RE.fullmatch(item))
            for item in self.candidate_refs
        ):
            raise IdentityError("IDENTITY_CANDIDATE_REF_INVALID", "review candidate refs must be opaque")
    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "task_id": self.task_id,
            "severity": self.severity,
            "task_type": self.task_type,
            "status": self.status,
            "blocking_metrics": sorted(self.blocking_metrics),
            "description": self.description,
            "required_input_or_resolution_type": self.required_input_or_resolution_type,
            "candidate_refs": sorted(self.candidate_refs),
            "evidence_refs": sorted(self.evidence_refs),
            "resolution_ref": self.resolution_ref,
        }


@dataclass(frozen=True)
class IdentityResolutionResult:
    calculation_status: str
    lookup_hash: str
    identity_master_hash: str
    match_method: Optional[str]
    identity_record_ref: Optional[str]
    blocker_codes: Tuple[str, ...]
    candidates: Tuple[IdentityCandidate, ...]
    review_tasks: Tuple[IdentityReviewTask, ...]

    @property
    def resolved(self) -> bool:
        return self.calculation_status == "VALIDATED_IDENTITY"

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.identity_resolution_result.v1",
            "calculation_status": self.calculation_status,
            "lookup_hash": self.lookup_hash,
            "identity_master_hash": self.identity_master_hash,
            "match_method": self.match_method,
            "identity_record_ref": self.identity_record_ref,
            "blocker_codes": list(self.blocker_codes),
            "candidates": [item.as_private_dict() for item in self.candidates],
            "review_tasks": [item.as_private_dict() for item in self.review_tasks],
        }


@dataclass(frozen=True)
class CrossEntityIdentityView:
    canonical_project_id: str
    valid_at: str
    identity_master_hash: str
    entity_scopes: Tuple[Tuple[str, str, str], ...]

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": "kmfa.project_cost.cross_entity_identity_view.v1",
            "canonical_project_id": self.canonical_project_id,
            "valid_at": self.valid_at,
            "identity_master_hash": self.identity_master_hash,
            "entity_scopes": [
                {"legal_entity_id": entity, "wbs_or_cost_code": wbs, "identity_record_ref": record_ref}
                for entity, wbs, record_ref in self.entity_scopes
            ],
            "destructive_normalization_performed": False,
        }


def _period_bounds(record: ProjectIdentityRecord) -> Tuple[date, date]:
    return (
        _iso_date(record.valid_from, "valid_from"),
        _iso_date(record.valid_to, "valid_to") if record.valid_to is not None else date.max,
    )


def _overlap_groups(records: Sequence[ProjectIdentityRecord]) -> Tuple[Tuple[ProjectIdentityRecord, ...], ...]:
    ordered = sorted(records, key=lambda item: (_period_bounds(item)[0], _period_bounds(item)[1], item.identity_ref))
    groups: List[Tuple[ProjectIdentityRecord, ...]] = []
    current: List[ProjectIdentityRecord] = []
    current_end: Optional[date] = None
    for record in ordered:
        start, end = _period_bounds(record)
        if not current or (current_end is not None and start <= current_end):
            current.append(record)
            current_end = max(current_end, end) if current_end is not None else end
            continue
        if len(current) > 1:
            groups.append(tuple(current))
        current = [record]
        current_end = end
    if len(current) > 1:
        groups.append(tuple(current))
    return tuple(groups)


def _review_description(code: str) -> str:
    descriptions = {
        "IDENTITY_EFFECTIVE_PERIOD_OVERLAP": "Identity resolution blocked because effective mapping periods overlap.",
        "IDENTITY_ALIAS_CONFLICT": "Identity resolution blocked because one governed alias maps to conflicting scopes.",
        "IDENTITY_MULTIPLE_ACTIVE_MATCHES": "Identity resolution blocked because multiple active mappings match.",
        "IDENTITY_CONTRACT_PROJECT_CONFLICT": "Identity resolution blocked because contract and project scope disagree.",
        "IDENTITY_IDENTIFIER_CONFLICT": "Identity resolution blocked because governed identifiers disagree.",
        "IDENTITY_CROSS_ENTITY_AMBIGUOUS": "Identity resolution blocked because legal-entity scope is ambiguous.",
        "IDENTITY_STALE_MAPPING": "Identity resolution blocked because the mapping snapshot or resolution reference is stale.",
        "IDENTITY_INCOMPLETE_CANONICAL_KEY": "Identity resolution blocked because the canonical key is incomplete.",
        "IDENTITY_CANDIDATE_ONLY": "Identity resolution blocked because only candidate-level aliases are available.",
        "IDENTITY_UNMAPPED": "Identity resolution blocked because no qualified effective mapping exists.",
    }
    return descriptions[code]


def _required_resolution_type(code: str) -> str:
    if code == "IDENTITY_STALE_MAPPING":
        return "REFRESH_IDENTITY_MASTER_OR_MAPPING_RESOLUTION"
    if code == "IDENTITY_INCOMPLETE_CANONICAL_KEY":
        return "LEGAL_ENTITY_WBS_OR_QUALIFIED_CONTRACT_SOURCE_MAPPING"
    return "QUALIFIED_EFFECTIVE_MAPPING_EVIDENCE_OR_SCOPE_REDUCTION"


def _make_review_task(
    code: str,
    *,
    lookup_hash: str,
    blocking_metrics: Sequence[str],
    candidate_refs: Sequence[str],
    evidence_refs: Sequence[str],
) -> IdentityReviewTask:
    task = IdentityReviewTask(
        task_id=_opaque_ref(
            "review_identity_",
            {
                "code": code,
                "lookup_hash": lookup_hash,
                "candidate_refs": sorted(set(candidate_refs)),
            },
        ),
        severity="P0",
        task_type=code,
        status="PENDING",
        blocking_metrics=tuple(sorted(set(blocking_metrics))),
        description=_review_description(code),
        required_input_or_resolution_type=_required_resolution_type(code),
        candidate_refs=tuple(sorted(set(candidate_refs))),
        evidence_refs=tuple(sorted(set(evidence_refs))),
        resolution_ref=None,
    )
    task.validate()
    return task


@dataclass(frozen=True)
class IdentityMaster:
    policy: IdentityPolicy
    records: Tuple[ProjectIdentityRecord, ...]

    def validate(self) -> None:
        self.policy.validate()
        if not isinstance(self.records, tuple):
            raise IdentityError("IDENTITY_MASTER_MUTABLE", "identity master records must use an immutable tuple")
        for record in self.records:
            record.validate()

    @property
    def content_hash(self) -> str:
        self.validate()
        payload = {
            "policy_id": self.policy.policy_id,
            "policy_sha256": self.policy.content_sha256,
            "records": [
                record.as_private_dict()
                for record in sorted(self.records, key=lambda item: item.identity_ref)
            ],
        }
        return hashlib.sha256(_canonical_json(payload)).hexdigest()

    def active_records(self, valid_at: date) -> Tuple[ProjectIdentityRecord, ...]:
        return tuple(sorted((item for item in self.records if item.is_active_at(valid_at)), key=lambda item: item.identity_ref))

    def conflict_tasks(self, blocking_metrics: Sequence[str] = ()) -> Tuple[IdentityReviewTask, ...]:
        """Detect overlaps through indexed partitions, never global fuzzy pair matching."""

        self.validate()
        active = [item for item in self.records if item.identity_status in ACTIVE_MAPPING_STATUSES]
        buckets: Dict[Tuple[str, ...], List[ProjectIdentityRecord]] = defaultdict(list)
        for record in active:
            buckets[("scope",) + record.scope_key].append(record)
            if record.project_code is not None:
                buckets[("project_code", record.project_code)].append(record)
            for contract_id in record.contract_ids:
                buckets[("contract", contract_id)].append(record)
            for source_alias in record.source_aliases:
                buckets[("source", source_alias)].append(record)
            buckets[("resolution", record.mapping_resolution_ref)].append(record)
        tasks: Dict[str, IdentityReviewTask] = {}
        for key, bucket in buckets.items():
            for group in _overlap_groups(bucket):
                scopes = {item.scope_key for item in group}
                codes: List[str] = []
                if key[0] == "scope":
                    codes.append("IDENTITY_EFFECTIVE_PERIOD_OVERLAP")
                elif key[0] == "contract" and len(scopes) > 1:
                    codes.append("IDENTITY_CONTRACT_PROJECT_CONFLICT")
                elif key[0] in {"project_code", "source"} and len(scopes) > 1:
                    codes.append("IDENTITY_ALIAS_CONFLICT")
                elif key[0] == "resolution" and len(scopes) > 1:
                    codes.append("IDENTITY_IDENTIFIER_CONFLICT")
                for code in codes:
                    record_refs = tuple(sorted(item.identity_ref for item in group))
                    evidence_refs = tuple(sorted({ref for item in group for ref in item.evidence_refs}))
                    lookup_hash = hashlib.sha256(
                        _canonical_json(
                            {
                                "code": code,
                                "policy_sha256": self.policy.content_sha256,
                                "records": record_refs,
                            }
                        )
                    ).hexdigest()
                    task = _make_review_task(
                        code,
                        lookup_hash=lookup_hash,
                        blocking_metrics=blocking_metrics,
                        candidate_refs=record_refs,
                        evidence_refs=evidence_refs,
                    )
                    tasks[task.task_id] = task
        return tuple(tasks[key] for key in sorted(tasks))

    def resolve(self, lookup: IdentityLookup) -> IdentityResolutionResult:
        lookup.validate()
        self.validate()
        if lookup.expected_master_hash != self.content_hash:
            return self._blocked(lookup, "IDENTITY_STALE_MAPPING", ())
        valid_at = _iso_date(lookup.valid_at, "valid_at")
        active = self.active_records(valid_at)
        complete_scope = all(
            value is not None
            for value in (lookup.canonical_project_id, lookup.legal_entity_id, lookup.wbs_or_cost_code)
        )
        scope_matches = tuple(
            item
            for item in active
            if complete_scope
            and item.scope_key
            == (lookup.canonical_project_id, lookup.legal_entity_id, lookup.wbs_or_cost_code)
        )
        contract_matches = tuple(
            item for item in active if lookup.contract_id is not None and lookup.contract_id in item.contract_ids
        )
        source_matches = tuple(
            item
            for item in active
            if lookup.governed_source_identifier is not None
            and lookup.governed_source_identifier in item.source_aliases
        )
        resolution_matches = tuple(
            item
            for item in active
            if lookup.mapping_resolution_ref is not None
            and lookup.mapping_resolution_ref == item.mapping_resolution_ref
        )
        if lookup.mapping_resolution_ref is not None and not resolution_matches:
            return self._blocked(lookup, "IDENTITY_STALE_MAPPING", ())
        supplied_candidate_aliases = (
            (lookup.project_code, lambda item: item.project_code),
            (lookup.project_name, lambda item: item.project_name),
            (lookup.customer_id, lambda item: item.customer_id),
        )
        for supplied_alias, getter in supplied_candidate_aliases:
            if supplied_alias is None:
                continue
            alias_matches = tuple(item for item in active if getter(item) == supplied_alias)
            if len({item.scope_key for item in alias_matches}) > 1:
                return self._blocked(lookup, "IDENTITY_ALIAS_CONFLICT", alias_matches)
        named_sets = (
            ("EXACT_CANONICAL_SCOPE", scope_matches, complete_scope),
            ("EXACT_CONTRACT_ID", contract_matches, lookup.contract_id is not None),
            ("EXACT_GOVERNED_SOURCE_ID", source_matches, lookup.governed_source_identifier is not None),
            ("QUALIFIED_MAPPING_RESOLUTION", resolution_matches, lookup.mapping_resolution_ref is not None),
        )
        for _, matches, supplied in named_sets:
            if supplied and len(matches) > 1:
                code = "IDENTITY_MULTIPLE_ACTIVE_MATCHES"
                if len({item.legal_entity_id for item in matches}) > 1:
                    code = "IDENTITY_CROSS_ENTITY_AMBIGUOUS"
                return self._blocked(lookup, code, matches)
        nonempty = [(method, matches[0]) for method, matches, _ in named_sets if len(matches) == 1]
        unique_refs = {record.identity_ref for _, record in nonempty}
        if len(unique_refs) > 1:
            code = (
                "IDENTITY_CONTRACT_PROJECT_CONFLICT"
                if lookup.contract_id is not None
                else "IDENTITY_IDENTIFIER_CONFLICT"
            )
            return self._blocked(lookup, code, tuple(record for _, record in nonempty))
        if nonempty:
            method, record = nonempty[0]
            if not self._record_consistent_with_lookup(record, lookup):
                code = (
                    "IDENTITY_CONTRACT_PROJECT_CONFLICT"
                    if lookup.contract_id is not None
                    else "IDENTITY_IDENTIFIER_CONFLICT"
                )
                return self._blocked(lookup, code, (record,))
            return IdentityResolutionResult(
                calculation_status="VALIDATED_IDENTITY",
                lookup_hash=lookup.binding_hash,
                identity_master_hash=self.content_hash,
                match_method=method,
                identity_record_ref=record.identity_ref,
                blocker_codes=(),
                candidates=(),
                review_tasks=(),
            )
        partial = self._candidate_records(active, lookup)
        provided_canonical_count = sum(
            value is not None
            for value in (lookup.canonical_project_id, lookup.legal_entity_id, lookup.wbs_or_cost_code)
        )
        if (
            lookup.canonical_project_id is not None
            and lookup.wbs_or_cost_code is not None
            and lookup.legal_entity_id is None
            and len({item.legal_entity_id for item in partial}) > 1
        ):
            return self._blocked(lookup, "IDENTITY_CROSS_ENTITY_AMBIGUOUS", partial)
        if 0 < provided_canonical_count < 3:
            return self._blocked(lookup, "IDENTITY_INCOMPLETE_CANONICAL_KEY", partial)
        alias_supplied = any(
            value is not None
            for value in (lookup.project_code, lookup.project_name, lookup.customer_id, lookup.free_text_ref)
        )
        if alias_supplied:
            return self._blocked(lookup, "IDENTITY_CANDIDATE_ONLY", partial)
        return self._blocked(lookup, "IDENTITY_UNMAPPED", partial)

    @staticmethod
    def _record_consistent_with_lookup(record: ProjectIdentityRecord, lookup: IdentityLookup) -> bool:
        comparisons = (
            (lookup.canonical_project_id, record.canonical_project_id),
            (lookup.legal_entity_id, record.legal_entity_id),
            (lookup.wbs_or_cost_code, record.wbs_or_cost_code),
            (lookup.project_code, record.project_code),
            (lookup.project_name, record.project_name),
            (lookup.customer_id, record.customer_id),
        )
        if any(provided is not None and provided != actual for provided, actual in comparisons):
            return False
        if lookup.contract_id is not None and lookup.contract_id not in record.contract_ids:
            return False
        if (
            lookup.governed_source_identifier is not None
            and lookup.governed_source_identifier not in record.source_aliases
        ):
            return False
        if (
            lookup.mapping_resolution_ref is not None
            and lookup.mapping_resolution_ref != record.mapping_resolution_ref
        ):
            return False
        return True

    @staticmethod
    def _candidate_records(
        records: Sequence[ProjectIdentityRecord], lookup: IdentityLookup
    ) -> Tuple[ProjectIdentityRecord, ...]:
        candidates = []
        for record in records:
            matched = False
            if lookup.canonical_project_id is not None and lookup.canonical_project_id == record.canonical_project_id:
                matched = True
            if lookup.legal_entity_id is not None and lookup.legal_entity_id == record.legal_entity_id:
                matched = True
            if lookup.wbs_or_cost_code is not None and lookup.wbs_or_cost_code == record.wbs_or_cost_code:
                matched = True
            if lookup.project_code is not None and lookup.project_code == record.project_code:
                matched = True
            if lookup.project_name is not None and lookup.project_name == record.project_name:
                matched = True
            if lookup.customer_id is not None and lookup.customer_id == record.customer_id:
                matched = True
            if matched:
                candidates.append(record)
        return tuple(sorted(candidates, key=lambda item: item.identity_ref))

    def _blocked(
        self,
        lookup: IdentityLookup,
        code: str,
        records: Sequence[ProjectIdentityRecord],
    ) -> IdentityResolutionResult:
        record_refs = tuple(sorted({item.identity_ref for item in records}))
        evidence_refs = tuple(sorted({ref for item in records for ref in item.evidence_refs}))
        candidate_id = _opaque_ref(
            "identity_candidate_",
            {"lookup_hash": lookup.binding_hash, "code": code, "records": record_refs},
        )
        candidate = IdentityCandidate(
            candidate_id=candidate_id,
            lookup_hash=lookup.binding_hash,
            reason_code=code,
            candidate_record_refs=record_refs,
            source_record_refs=tuple(sorted(lookup.source_record_refs)),
            requested_metrics=tuple(sorted(lookup.requested_metrics)),
            evidence_refs=evidence_refs,
        )
        candidate.validate()
        task = _make_review_task(
            code,
            lookup_hash=lookup.binding_hash,
            blocking_metrics=lookup.requested_metrics,
            candidate_refs=(candidate.candidate_id,),
            evidence_refs=evidence_refs,
        )
        return IdentityResolutionResult(
            calculation_status="BLOCKED_IDENTITY",
            lookup_hash=lookup.binding_hash,
            identity_master_hash=self.content_hash,
            match_method=None,
            identity_record_ref=None,
            blocker_codes=(code,),
            candidates=(candidate,),
            review_tasks=(task,),
        )


def build_cross_entity_view(
    master: IdentityMaster,
    *,
    canonical_project_id: str,
    valid_at: str,
) -> CrossEntityIdentityView:
    master.validate()
    _normalized_text(canonical_project_id, "canonical_project_id")
    point = _iso_date(valid_at, "valid_at")
    records = [item for item in master.active_records(point) if item.canonical_project_id == canonical_project_id]
    if not records:
        raise IdentityError("IDENTITY_UNMAPPED", "no active identity records exist for the cross-entity view")
    dimensions = [(item.legal_entity_id, item.wbs_or_cost_code) for item in records]
    if len(set(dimensions)) != len(dimensions):
        raise IdentityError(
            "IDENTITY_MULTIPLE_ACTIVE_MATCHES",
            "cross-entity view contains multiple active mappings for one entity/WBS scope",
        )
    scopes = tuple(sorted((item.legal_entity_id, item.wbs_or_cost_code, item.identity_ref) for item in records))
    return CrossEntityIdentityView(canonical_project_id, valid_at, master.content_hash, scopes)


def public_identity_summary(master: IdentityMaster) -> Dict[str, Any]:
    master.validate()
    statuses = Counter(item.identity_status for item in master.records)
    return {
        "schema_version": "kmfa.project_cost.public_identity_summary.v1",
        "record_count": len(master.records),
        "active_mapping_count": statuses.get("APPROVED", 0),
        "candidate_or_nonactive_count": len(master.records) - statuses.get("APPROVED", 0),
        "conflict_task_count": len(master.conflict_tasks()),
        "contains_private_identifiers": False,
        "cross_entity_dimension_preserved": True,
    }


def _safe_private_directory(root: Path, components: Sequence[str]) -> Path:
    value = Path(root)
    if value.exists() and value.is_symlink():
        raise IdentityError("PRIVATE_RUNTIME_SYMLINK", "private runtime must not be a symbolic link")
    value.mkdir(parents=True, exist_ok=True)
    try:
        current = value.resolve(strict=True)
    except OSError as exc:
        raise IdentityError("PRIVATE_RUNTIME_UNAVAILABLE", "private runtime cannot be resolved") from exc
    for component in components:
        if not re.fullmatch(r"[a-z_]{2,64}", component):
            raise IdentityError("PRIVATE_IDENTITY_PATH_INVALID", "private identity path component is invalid")
        current = current / component
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            raise IdentityError("PRIVATE_IDENTITY_PATH_UNSAFE", "private identity path is unsafe")
        current.mkdir(exist_ok=True)
    return current


def _append_private_json(root: Path, components: Sequence[str], filename: str, payload: Mapping[str, Any]) -> Path:
    directory = _safe_private_directory(root, components)
    text = json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        return atomic_write_text(directory, filename, text)
    except PathSafetyError as exc:
        raise IdentityError(exc.code, exc.message) from exc


def append_identity_record(private_runtime_root: Path, record: ProjectIdentityRecord) -> Path:
    record.validate()
    if record.identity_status == "APPROVED":
        record_plane = "approved_records"
    elif record.identity_status in {"CANDIDATE", "CONFLICT", "UNMAPPED"}:
        record_plane = "candidate_records"
    else:
        record_plane = "historical_records"
    return _append_private_json(
        private_runtime_root,
        ("identity_master", record_plane),
        record.identity_ref + ".json",
        record.as_private_dict(),
    )


def append_identity_candidate(private_runtime_root: Path, candidate: IdentityCandidate) -> Path:
    candidate.validate()
    return _append_private_json(
        private_runtime_root,
        ("identity_master", "candidates"),
        candidate.candidate_id + ".json",
        candidate.as_private_dict(),
    )


def append_identity_review_task(private_runtime_root: Path, task: IdentityReviewTask) -> Path:
    task.validate()
    return _append_private_json(
        private_runtime_root,
        ("review_tasks", "identity"),
        task.task_id + ".json",
        task.as_private_dict(),
    )
