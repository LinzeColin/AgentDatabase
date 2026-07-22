"""Explicit manifest loading, source-slot selection, schema locks, and digest binding."""

from __future__ import annotations

import hashlib
import json
import re
import stat
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

import yaml

from .inventory import (
    FileIdentity,
    InventoryEntry,
    InventoryError,
    match_inventory_entries,
    verify_source_file,
)


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
SOURCE_ID_RE = re.compile(r"^src_[0-9a-f]{32}$")
SLOT_ID_RE = re.compile(r"^[a-z][a-z0-9_]{1,63}$")
MANIFEST_BYTES_MAX = 1024 * 1024


class ManifestError(ValueError):
    """Structured manifest failure without raw paths or filenames."""

    def __init__(self, code: str, message: str, *, slot_id: Optional[str] = None) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message
        self.slot_id = slot_id

    def as_dict(self) -> Dict[str, str]:
        result = {"code": self.code, "message": self.message}
        if self.slot_id:
            result["slot_ref"] = hashlib.sha256(self.slot_id.encode("utf-8")).hexdigest()[:16]
        return result


class _NoAliasSafeLoader(yaml.SafeLoader):
    def compose_node(self, parent: Any, index: Any) -> Any:
        if self.check_event(yaml.AliasEvent):
            raise yaml.YAMLError("YAML aliases are forbidden in governed manifests")
        return super().compose_node(parent, index)

    def construct_mapping(self, node: Any, deep: bool = False) -> Dict[Any, Any]:
        self.flatten_mapping(node)
        mapping: Dict[Any, Any] = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            try:
                duplicate = key in mapping
            except TypeError as exc:
                raise yaml.YAMLError("unhashable YAML mapping key is forbidden") from exc
            if duplicate:
                raise yaml.YAMLError("duplicate YAML mapping keys are forbidden")
            mapping[key] = self.construct_object(value_node, deep=deep)
        return mapping


@dataclass(frozen=True)
class SelectedSourceLock:
    source_id: str
    sha256: str


@dataclass(frozen=True)
class ManifestSlot:
    slot_id: str
    reader: str
    reader_version: str
    missing_behavior: str
    required_for: Tuple[str, ...]
    private_patterns: Tuple[str, ...]
    logical_source_period: str
    expected_schema_id: str
    expected_schema_fingerprint: Optional[str]
    selected_source_id: Optional[str]
    selected_sha256: Optional[str]
    selected_sources: Tuple[SelectedSourceLock, ...]
    selection_resolution_ref: Optional[str]
    prohibited_in_calculate: bool

    def source_locks(self) -> Tuple[SelectedSourceLock, ...]:
        if self.selected_sources:
            return self.selected_sources
        if self.selected_source_id is not None and self.selected_sha256 is not None:
            return (SelectedSourceLock(self.selected_source_id, self.selected_sha256),)
        return ()


@dataclass(frozen=True)
class InputManifest:
    schema_version: str
    manifest_id: str
    input_root: str
    read_only: bool
    base_currency: str
    as_of: str
    project_selector: Tuple[Tuple[str, str], ...]
    metric_id: str
    accounting_basis_id: str
    requested_basis_ids: Tuple[str, ...]
    security_profile_id: str
    selection_policy: Tuple[Tuple[str, bool], ...]
    slots: Tuple[ManifestSlot, ...]
    content_sha256: str

    def slot_map(self) -> Dict[str, ManifestSlot]:
        return {slot.slot_id: slot for slot in self.slots}

    def project_selector_dict(self) -> Dict[str, str]:
        return dict(self.project_selector)


@dataclass(frozen=True)
class SourceSchemaObservation:
    source_id: str
    reader_version: str
    schema_id: str
    schema_fingerprint: str
    security_profile_id: str
    security_status: str


@dataclass(frozen=True)
class SourceSelection:
    slot_id: str
    source_id: str
    private_relative_path: str
    sha256: str
    identity: FileIdentity
    reader: str
    reader_version: str
    logical_source_period: str
    schema_id: str
    schema_fingerprint: str
    selection_resolution_ref: Optional[str]

    def as_private_dict(self) -> Dict[str, Any]:
        return {
            "slot_id": self.slot_id,
            "source_id": self.source_id,
            "private_relative_path": self.private_relative_path,
            "sha256": self.sha256,
            "identity": {
                "device": self.identity.device,
                "inode": self.identity.inode,
                "size_bytes": self.identity.size_bytes,
                "mtime_ns": self.identity.mtime_ns,
                "link_count": self.identity.link_count,
            },
            "reader": self.reader,
            "reader_version": self.reader_version,
            "logical_source_period": self.logical_source_period,
            "schema_id": self.schema_id,
            "schema_fingerprint": self.schema_fingerprint,
            "selection_resolution_ref": self.selection_resolution_ref,
        }


def _exact_string(mapping: Mapping[str, Any], key: str) -> str:
    value = mapping.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ManifestError("MANIFEST_FIELD_INVALID", "%s must be a nonempty string" % key)
    return value.strip()


def _optional_string(mapping: Mapping[str, Any], key: str) -> Optional[str]:
    value = mapping.get(key)
    if value is None:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ManifestError("MANIFEST_FIELD_INVALID", "%s must be null or nonempty text" % key)
    return value.strip()


def _string_list(mapping: Mapping[str, Any], key: str) -> Tuple[str, ...]:
    value = mapping.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ManifestError("MANIFEST_FIELD_INVALID", "%s must be a string list" % key)
    result = tuple(item.strip() for item in value)
    if len(set(result)) != len(result):
        raise ManifestError("MANIFEST_FIELD_INVALID", "%s cannot contain duplicates" % key)
    return result


def _read_manifest_bytes(path: Path) -> bytes:
    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise ManifestError("MANIFEST_UNAVAILABLE", "private manifest cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ManifestError("MANIFEST_PATH_UNSAFE", "private manifest must be a single-link regular file")
    if metadata.st_size > MANIFEST_BYTES_MAX:
        raise ManifestError("MANIFEST_TOO_LARGE", "private manifest exceeds its metadata size ceiling")
    try:
        return value.read_bytes()
    except OSError as exc:
        raise ManifestError("MANIFEST_UNREADABLE", "private manifest cannot be read") from exc


def _validate_pattern(pattern: str) -> None:
    if not pattern or "\x00" in pattern or "\\" in pattern or pattern.startswith("/"):
        raise ManifestError("UNSAFE_PRIVATE_PATTERN", "source patterns must be portable and relative")
    components = pattern.split("/")
    if any(component in ("", ".", "..") for component in components):
        raise ManifestError("UNSAFE_PRIVATE_PATTERN", "source pattern contains an ambiguous component")


def _parse_slot(slot_id: str, raw: Any) -> ManifestSlot:
    if not SLOT_ID_RE.fullmatch(slot_id) or not isinstance(raw, dict):
        raise ManifestError("MANIFEST_SLOT_INVALID", "slot identifier or body is invalid")
    allowed_fields = {
        "reader",
        "reader_version",
        "missing_behavior",
        "required_for",
        "private_patterns",
        "logical_source_period",
        "expected_schema_id",
        "expected_schema_fingerprint",
        "selected_source_id",
        "selected_sha256",
        "selected_sources",
        "selection_resolution_ref",
        "prohibited_in_calculate",
    }
    if set(raw) - allowed_fields:
        raise ManifestError("MANIFEST_SLOT_SCHEMA_DRIFT", "manifest slot contains unknown fields", slot_id=slot_id)
    patterns = _string_list(raw, "private_patterns")
    for pattern in patterns:
        _validate_pattern(pattern)
    required_for = _string_list(raw, "required_for") if "required_for" in raw else ()
    selected_source_id = _optional_string(raw, "selected_source_id")
    if selected_source_id is not None and not SOURCE_ID_RE.fullmatch(selected_source_id):
        raise ManifestError("SELECTED_SOURCE_ID_INVALID", "selected source ID is not opaque and canonical", slot_id=slot_id)
    selected_sha256 = _optional_string(raw, "selected_sha256")
    if selected_sha256 is not None and not SHA256_RE.fullmatch(selected_sha256):
        raise ManifestError("SELECTED_DIGEST_INVALID", "selected digest must be lowercase SHA256", slot_id=slot_id)
    if (selected_source_id is None) != (selected_sha256 is None):
        raise ManifestError(
            "SELECTED_SOURCE_LOCK_INCOMPLETE",
            "single-source selection requires both source ID and full digest",
            slot_id=slot_id,
        )
    selected_sources_raw = raw.get("selected_sources", [])
    if not isinstance(selected_sources_raw, list):
        raise ManifestError("SELECTED_SOURCES_INVALID", "selected_sources must be a list", slot_id=slot_id)
    selected_sources = []
    for item in selected_sources_raw:
        if not isinstance(item, Mapping) or set(item) != {"source_id", "sha256"}:
            raise ManifestError(
                "SELECTED_SOURCES_INVALID",
                "each selected source lock requires exact source_id and sha256 fields",
                slot_id=slot_id,
            )
        source_id = _exact_string(item, "source_id")
        sha256 = _exact_string(item, "sha256")
        if not SOURCE_ID_RE.fullmatch(source_id) or not SHA256_RE.fullmatch(sha256):
            raise ManifestError(
                "SELECTED_SOURCES_INVALID",
                "batch source locks require canonical opaque IDs and lowercase SHA256",
                slot_id=slot_id,
            )
        selected_sources.append(SelectedSourceLock(source_id, sha256))
    if len({item.source_id for item in selected_sources}) != len(selected_sources):
        raise ManifestError("SELECTED_SOURCES_DUPLICATE", "batch source locks must be unique", slot_id=slot_id)
    if selected_sources and selected_source_id is not None:
        raise ManifestError(
            "SELECTED_SOURCE_MODES_CONFLICT",
            "single-source and batch source locks cannot be active together",
            slot_id=slot_id,
        )
    expected_schema_fingerprint = _optional_string(raw, "expected_schema_fingerprint")
    if expected_schema_fingerprint is not None and not SHA256_RE.fullmatch(expected_schema_fingerprint):
        raise ManifestError("SCHEMA_FINGERPRINT_INVALID", "schema fingerprint must be lowercase SHA256", slot_id=slot_id)
    prohibited = raw.get("prohibited_in_calculate", False)
    if type(prohibited) is not bool:
        raise ManifestError("MANIFEST_FIELD_INVALID", "prohibited_in_calculate must be boolean", slot_id=slot_id)
    if slot_id == "reference_reports" and prohibited is not True:
        raise ManifestError(
            "REFERENCE_CALCULATE_ISOLATION_RELAXED",
            "reference report slots must remain prohibited in calculate",
            slot_id=slot_id,
        )
    return ManifestSlot(
        slot_id=slot_id,
        reader=_exact_string(raw, "reader"),
        reader_version=_exact_string(raw, "reader_version"),
        missing_behavior=_exact_string(raw, "missing_behavior"),
        required_for=required_for,
        private_patterns=patterns,
        logical_source_period=_exact_string(raw, "logical_source_period"),
        expected_schema_id=_exact_string(raw, "expected_schema_id"),
        expected_schema_fingerprint=expected_schema_fingerprint,
        selected_source_id=selected_source_id,
        selected_sha256=selected_sha256,
        selected_sources=tuple(sorted(selected_sources, key=lambda item: item.source_id)),
        selection_resolution_ref=_optional_string(raw, "selection_resolution_ref"),
        prohibited_in_calculate=prohibited,
    )


def load_input_manifest(path: Path) -> InputManifest:
    data = _read_manifest_bytes(path)
    try:
        raw = yaml.load(data.decode("utf-8"), Loader=_NoAliasSafeLoader)
    except (UnicodeError, yaml.YAMLError) as exc:
        raise ManifestError("MANIFEST_PARSE_ERROR", "private manifest is not safe UTF-8 YAML") from exc
    if not isinstance(raw, dict):
        raise ManifestError("MANIFEST_NOT_MAPPING", "private manifest must be a mapping")
    allowed_top_fields = {
        "schema_version",
        "manifest_id",
        "input_root",
        "read_only",
        "base_currency",
        "as_of",
        "project_selector",
        "metric_id",
        "accounting_basis_id",
        "requested_basis_ids",
        "security_profile_id",
        "selection_policy",
        "slots",
    }
    if set(raw) - allowed_top_fields:
        raise ManifestError("MANIFEST_SCHEMA_DRIFT", "input manifest contains unknown fields")
    if raw.get("schema_version") != "kmfa.project_cost.input_manifest.v3":
        raise ManifestError("MANIFEST_SCHEMA_DRIFT", "input manifest schema version is not supported")
    if type(raw.get("read_only")) is not bool or raw.get("read_only") is not True:
        raise ManifestError("MANIFEST_NOT_READ_ONLY", "manifest must lock sources read-only")
    if raw.get("base_currency") != "CNY":
        raise ManifestError("BASE_CURRENCY_UNSUPPORTED", "product 0.2.0 supports CNY only")
    as_of = _exact_string(raw, "as_of")
    try:
        date.fromisoformat(as_of)
    except ValueError as exc:
        raise ManifestError("MANIFEST_DATE_INVALID", "manifest as-of date must be ISO 8601") from exc
    input_root = _exact_string(raw, "input_root")
    if not Path(input_root).is_absolute():
        raise ManifestError("MANIFEST_ROOT_NOT_ABSOLUTE", "private manifest input root must be absolute")
    selector_raw = raw.get("project_selector")
    if not isinstance(selector_raw, dict) or not selector_raw:
        raise ManifestError("PROJECT_SELECTOR_INVALID", "manifest project selector must be nonempty")
    selector = []
    for key, value in selector_raw.items():
        if not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip():
            raise ManifestError("PROJECT_SELECTOR_INVALID", "project selector keys and values must be nonempty text")
        selector.append((key.strip(), value.strip()))
    policy_raw = raw.get("selection_policy")
    if not isinstance(policy_raw, dict):
        raise ManifestError("SELECTION_POLICY_INVALID", "manifest selection policy is required")
    required_policy = {
        "explicit_private_manifest_required": True,
        "fail_on_multiple_without_decision": True,
        "fail_on_missing_required": True,
        "full_digest_required_for_final_run": True,
        "mtime_is_authority": False,
        "never_mutate_sources": True,
        "input_sufficiency_required_before_source_body_read": True,
    }
    if set(policy_raw) != set(required_policy):
        raise ManifestError("SELECTION_POLICY_INVALID", "manifest selection policy fields drifted")
    for key, expected in required_policy.items():
        if type(policy_raw.get(key)) is not bool or policy_raw.get(key) is not expected:
            raise ManifestError("SELECTION_POLICY_RELAXED", "manifest selection policy cannot relax %s" % key)
    slots_raw = raw.get("slots")
    if not isinstance(slots_raw, dict) or not slots_raw:
        raise ManifestError("MANIFEST_SLOTS_INVALID", "manifest requires at least one source slot")
    slots = tuple(_parse_slot(slot_id, slots_raw[slot_id]) for slot_id in sorted(slots_raw))
    accounting_basis_id = _exact_string(raw, "accounting_basis_id")
    requested_basis_ids = _string_list(raw, "requested_basis_ids") if "requested_basis_ids" in raw else (
        accounting_basis_id,
    )
    if accounting_basis_id not in requested_basis_ids or len(set(requested_basis_ids)) != len(requested_basis_ids):
        raise ManifestError("MANIFEST_BASIS_INVALID", "primary basis must occur exactly once in requested basis IDs")
    return InputManifest(
        schema_version="kmfa.project_cost.input_manifest.v3",
        manifest_id=_exact_string(raw, "manifest_id"),
        input_root=input_root,
        read_only=True,
        base_currency="CNY",
        as_of=as_of,
        project_selector=tuple(sorted(selector)),
        metric_id=_exact_string(raw, "metric_id"),
        accounting_basis_id=accounting_basis_id,
        requested_basis_ids=requested_basis_ids,
        security_profile_id=_exact_string(raw, "security_profile_id"),
        selection_policy=tuple(sorted(required_policy.items())),
        slots=slots,
        content_sha256=hashlib.sha256(data).hexdigest(),
    )


def validate_manifest_request(
    manifest: InputManifest,
    *,
    mode: str,
    requested_metrics: Sequence[str],
    requested_basis_ids: Sequence[str],
    project_selector: Mapping[str, str],
    as_of: Optional[str],
) -> None:
    if mode in {"calculate", "restate"} and manifest.metric_id not in requested_metrics:
        raise ManifestError("MANIFEST_METRIC_CONFLICT", "manifest metric is outside the requested metric scope")
    if requested_basis_ids and not set(manifest.requested_basis_ids).issubset(set(requested_basis_ids)):
        raise ManifestError("MANIFEST_BASIS_CONFLICT", "manifest basis scope differs from the request")
    if as_of is not None and manifest.as_of != as_of:
        raise ManifestError("MANIFEST_PERIOD_CONFLICT", "manifest as-of differs from the request")
    normalized_selector = {str(key): str(value) for key, value in project_selector.items()}
    if mode != "inventory" and manifest.project_selector_dict() != normalized_selector:
        raise ManifestError("MANIFEST_PROJECT_SCOPE_CONFLICT", "manifest project selector differs from the request")
    if mode in {"calculate", "restate"}:
        selected_reference = [
            slot for slot in manifest.slots if slot.prohibited_in_calculate and slot.source_locks()
        ]
        if selected_reference:
            raise ManifestError(
                "REFERENCE_SELECTED_IN_CALCULATE",
                "calculate or restate manifest selects a prohibited reference slot",
            )


def _resolved_root(value: str) -> Path:
    path = Path(value)
    if path.is_symlink():
        raise ManifestError("INPUT_ROOT_SYMLINK", "input root must not be a symbolic link")
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise ManifestError("INPUT_ROOT_UNAVAILABLE", "input root cannot be resolved") from exc
    if not resolved.is_dir():
        raise ManifestError("INPUT_ROOT_NOT_DIRECTORY", "input root must be a directory")
    return resolved


def select_manifest_sources(
    manifest: InputManifest,
    *,
    input_root: Path,
    required_slot_ids: Sequence[str],
    inventory_entries: Sequence[InventoryEntry],
    schema_observations: Mapping[str, SourceSchemaObservation],
) -> Tuple[SourceSelection, ...]:
    """Select explicit slots and always rehash selected source bodies."""

    if _resolved_root(manifest.input_root) != _resolved_root(str(input_root)):
        raise ManifestError("MANIFEST_ROOT_CONFLICT", "manifest input root differs from the governed run root")
    slot_map = manifest.slot_map()
    if len(set(required_slot_ids)) != len(tuple(required_slot_ids)):
        raise ManifestError("DUPLICATE_REQUIRED_SLOT", "required slot list contains duplicates")
    selections = []
    for slot_id in sorted(required_slot_ids):
        slot = slot_map.get(slot_id)
        if slot is None:
            raise ManifestError("REQUIRED_SLOT_MISSING", "manifest lacks a required slot", slot_id=slot_id)
        if not slot.private_patterns:
            raise ManifestError("SLOT_PATTERNS_MISSING", "required slot has no private discovery patterns", slot_id=slot_id)
        candidates = match_inventory_entries(inventory_entries, slot.private_patterns)
        if not candidates:
            raise ManifestError("SLOT_CANDIDATE_MISSING", "required slot has no candidate", slot_id=slot_id)
        source_locks = slot.source_locks()
        if not source_locks:
            raise ManifestError(
                "SLOT_SELECTION_REQUIRED",
                "required slot needs an explicit selected source even when only one candidate exists",
                slot_id=slot_id,
            )
        if slot.expected_schema_fingerprint is None:
            raise ManifestError("SLOT_SCHEMA_LOCK_REQUIRED", "required slot lacks a schema fingerprint lock", slot_id=slot_id)
        for source_lock in source_locks:
            matching = [entry for entry in candidates if entry.source_id == source_lock.source_id]
            if len(matching) != 1:
                raise ManifestError(
                    "SELECTED_SOURCE_NOT_UNIQUE",
                    "selected source is absent or not unique among slot candidates",
                    slot_id=slot_id,
                )
            entry = matching[0]
            try:
                verified = verify_source_file(input_root, entry)
            except InventoryError as exc:
                raise ManifestError(exc.code, exc.message, slot_id=slot_id) from exc
            if verified.sha256 != source_lock.sha256:
                raise ManifestError("SOURCE_DIGEST_DRIFT", "selected source full digest differs from manifest", slot_id=slot_id)
            observation = schema_observations.get(entry.source_id)
            if observation is None:
                raise ManifestError("SOURCE_SCHEMA_NOT_VERIFIED", "selected source lacks a reader schema observation", slot_id=slot_id)
            if observation.source_id != entry.source_id:
                raise ManifestError("SOURCE_SCHEMA_REF_MISMATCH", "schema observation source reference does not match", slot_id=slot_id)
            if observation.security_status != "PREFLIGHT_PASS" or observation.security_profile_id != manifest.security_profile_id:
                raise ManifestError("SOURCE_SECURITY_NOT_VERIFIED", "selected source lacks the bound R2 security gate", slot_id=slot_id)
            if observation.reader_version != slot.reader_version:
                raise ManifestError("READER_VERSION_DRIFT", "selected reader version differs from manifest", slot_id=slot_id)
            if observation.schema_id != slot.expected_schema_id or observation.schema_fingerprint != slot.expected_schema_fingerprint:
                raise ManifestError("SOURCE_SCHEMA_DRIFT", "selected source schema differs from manifest lock", slot_id=slot_id)
            selections.append(
                SourceSelection(
                    slot_id=slot_id,
                    source_id=entry.source_id,
                    private_relative_path=verified.relative_path,
                    sha256=verified.sha256,
                    identity=verified.identity,
                    reader=slot.reader,
                    reader_version=slot.reader_version,
                    logical_source_period=slot.logical_source_period,
                    schema_id=observation.schema_id,
                    schema_fingerprint=observation.schema_fingerprint,
                    selection_resolution_ref=slot.selection_resolution_ref,
                )
            )
    return tuple(selections)


def selection_business_fingerprint(selections: Sequence[SourceSelection]) -> str:
    """Exclude volatile filesystem identity while binding every business-relevant lock."""

    payload = [
        {
            "slot_id": item.slot_id,
            "source_id": item.source_id,
            "sha256": item.sha256,
            "reader": item.reader,
            "reader_version": item.reader_version,
            "logical_source_period": item.logical_source_period,
            "schema_id": item.schema_id,
            "schema_fingerprint": item.schema_fingerprint,
            "selection_resolution_ref": item.selection_resolution_ref,
        }
        for item in sorted(selections, key=lambda value: (value.slot_id, value.source_id))
    ]
    encoded = json.dumps(payload, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()
