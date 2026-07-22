"""Explicit, append-only input-resolution records bound to exact requests and configs."""

from __future__ import annotations

import json
import re
import stat
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Mapping, Optional, Tuple

from .paths import PathSafetyError, atomic_write_text


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
RESOLUTION_ID_RE = re.compile(r"^resolution_[0-9a-f]{32}$")
RESOLUTION_BYTES_MAX = 1024 * 1024
CLASSIFICATIONS = frozenset({"NON_WAIVABLE", "SCOPE_DEPENDENT", "OPTIONAL_PRESENTATION"})
ALLOWED_RESOLUTIONS = {
    "NON_WAIVABLE": frozenset({"SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"}),
    "SCOPE_DEPENDENT": frozenset({"SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "BLOCKED"}),
    "OPTIONAL_PRESENTATION": frozenset({"SUPPLIED", "OMIT_OPTIONAL_PRESENTATION", "BLOCKED"}),
}
INSTRUCTION_REQUIRED = frozenset(
    {"QUALIFIED_ALTERNATE_EVIDENCE", "SCOPE_REDUCED", "OMIT_OPTIONAL_PRESENTATION", "BLOCKED"}
)
EVIDENCE_REQUIRED = frozenset({"SUPPLIED", "QUALIFIED_ALTERNATE_EVIDENCE"})


class ResolutionError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class ResolutionItem:
    requirement_id: str
    classification: str
    resolution: str
    user_instruction: Optional[str]
    user_instruction_ref: Optional[str]
    affected_metrics: Tuple[str, ...]
    effect_on_scope_or_metrics: str
    evidence_refs: Tuple[str, ...]

    def validate(self) -> None:
        if not self.requirement_id:
            raise ResolutionError("REQUIREMENT_ID_MISSING", "resolution item requires a requirement ID")
        if self.classification not in CLASSIFICATIONS:
            raise ResolutionError("CLASSIFICATION_INVALID", "resolution classification is not registered")
        if self.resolution not in ALLOWED_RESOLUTIONS[self.classification]:
            raise ResolutionError("RESOLUTION_NOT_ALLOWED", "resolution is not allowed for its classification")
        if not self.effect_on_scope_or_metrics:
            raise ResolutionError("SCOPE_EFFECT_MISSING", "resolution requires an explicit scope or metric effect")
        if self.resolution in INSTRUCTION_REQUIRED:
            if not self.user_instruction or not self.user_instruction_ref:
                raise ResolutionError(
                    "USER_INSTRUCTION_REQUIRED",
                    "resolution requires exact user instruction text and an opaque instruction reference",
                )
        if self.resolution in EVIDENCE_REQUIRED and not self.evidence_refs:
            raise ResolutionError("EVIDENCE_REQUIRED", "resolution requires qualified evidence references")
        if self.resolution == "SCOPE_REDUCED" and not self.affected_metrics:
            raise ResolutionError("AFFECTED_METRICS_REQUIRED", "scope reduction must identify affected Metrics")
        if self.resolution == "OMIT_OPTIONAL_PRESENTATION" and self.classification != "OPTIONAL_PRESENTATION":
            raise ResolutionError("NON_WAIVABLE_OMISSION", "only optional presentation may be omitted")

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "requirement_id": self.requirement_id,
            "classification": self.classification,
            "resolution": self.resolution,
            "user_instruction": self.user_instruction,
            "user_instruction_ref": self.user_instruction_ref,
            "affected_metrics": list(self.affected_metrics),
            "effect_on_scope_or_metrics": self.effect_on_scope_or_metrics,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class InputResolution:
    resolution_id: str
    run_id: str
    recorded_at: str
    bound_request_hash: str
    resulting_request_hash: str
    bound_manifest_sha256: str
    bound_requirements_sha256: str
    items: Tuple[ResolutionItem, ...]

    def validate(self) -> None:
        if not RESOLUTION_ID_RE.fullmatch(self.resolution_id):
            raise ResolutionError("RESOLUTION_ID_INVALID", "resolution ID must be opaque and canonical")
        if not self.run_id:
            raise ResolutionError("RUN_ID_MISSING", "resolution requires a run ID")
        try:
            timestamp = datetime.fromisoformat(self.recorded_at.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ResolutionError("RECORDED_AT_INVALID", "resolution timestamp must be ISO 8601") from exc
        if timestamp.tzinfo is None:
            raise ResolutionError("RECORDED_AT_TIMEZONE_MISSING", "resolution timestamp requires a timezone")
        hashes = (
            self.bound_request_hash,
            self.resulting_request_hash,
            self.bound_manifest_sha256,
            self.bound_requirements_sha256,
        )
        if any(not SHA256_RE.fullmatch(value) for value in hashes):
            raise ResolutionError("RESOLUTION_HASH_INVALID", "resolution bindings must be lowercase SHA256")
        if not self.items:
            raise ResolutionError("RESOLUTION_ITEMS_MISSING", "resolution requires at least one item")
        seen = set()
        for item in self.items:
            item.validate()
            if item.requirement_id in seen:
                raise ResolutionError("DUPLICATE_RESOLUTION_ITEM", "requirement may be resolved at most once per record")
            seen.add(item.requirement_id)

    def item_map(self) -> Dict[str, ResolutionItem]:
        return {item.requirement_id: item for item in self.items}

    def as_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.input_resolution.v1",
            "resolution_id": self.resolution_id,
            "run_id": self.run_id,
            "recorded_at": self.recorded_at,
            "bound_request_hash": self.bound_request_hash,
            "resulting_request_hash": self.resulting_request_hash,
            "bound_manifest_sha256": self.bound_manifest_sha256,
            "bound_requirements_sha256": self.bound_requirements_sha256,
            "items": [item.as_dict() for item in self.items],
        }


def _nonempty_text(value: Any, field: str, *, optional: bool = False) -> Optional[str]:
    if value is None and optional:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ResolutionError("RESOLUTION_FIELD_INVALID", "%s must be nonempty text" % field)
    return value.strip()


def _string_list(value: Any, field: str) -> Tuple[str, ...]:
    if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
        raise ResolutionError("RESOLUTION_FIELD_INVALID", "%s must be a string list" % field)
    return tuple(item.strip() for item in value)


def input_resolution_from_mapping(raw: Mapping[str, Any]) -> InputResolution:
    allowed_top = {
        "schema_version",
        "resolution_id",
        "run_id",
        "recorded_at",
        "bound_request_hash",
        "resulting_request_hash",
        "bound_manifest_sha256",
        "bound_requirements_sha256",
        "items",
    }
    if set(raw) != allowed_top or raw.get("schema_version") != "kmfa.project_cost.input_resolution.v1":
        raise ResolutionError("RESOLUTION_SCHEMA_DRIFT", "resolution fields or schema version differ from v1")
    raw_items = raw.get("items")
    if not isinstance(raw_items, list):
        raise ResolutionError("RESOLUTION_ITEMS_INVALID", "resolution items must be a list")
    item_keys = {
        "requirement_id",
        "classification",
        "resolution",
        "user_instruction",
        "user_instruction_ref",
        "affected_metrics",
        "effect_on_scope_or_metrics",
        "evidence_refs",
    }
    items = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict) or set(raw_item) != item_keys:
            raise ResolutionError("RESOLUTION_ITEM_SCHEMA_DRIFT", "resolution item fields differ from v1")
        items.append(
            ResolutionItem(
                requirement_id=_nonempty_text(raw_item.get("requirement_id"), "requirement_id") or "",
                classification=_nonempty_text(raw_item.get("classification"), "classification") or "",
                resolution=_nonempty_text(raw_item.get("resolution"), "resolution") or "",
                user_instruction=_nonempty_text(raw_item.get("user_instruction"), "user_instruction", optional=True),
                user_instruction_ref=_nonempty_text(
                    raw_item.get("user_instruction_ref"), "user_instruction_ref", optional=True
                ),
                affected_metrics=_string_list(raw_item.get("affected_metrics"), "affected_metrics"),
                effect_on_scope_or_metrics=_nonempty_text(
                    raw_item.get("effect_on_scope_or_metrics"), "effect_on_scope_or_metrics"
                )
                or "",
                evidence_refs=_string_list(raw_item.get("evidence_refs"), "evidence_refs"),
            )
        )
    resolution = InputResolution(
        resolution_id=_nonempty_text(raw.get("resolution_id"), "resolution_id") or "",
        run_id=_nonempty_text(raw.get("run_id"), "run_id") or "",
        recorded_at=_nonempty_text(raw.get("recorded_at"), "recorded_at") or "",
        bound_request_hash=_nonempty_text(raw.get("bound_request_hash"), "bound_request_hash") or "",
        resulting_request_hash=_nonempty_text(raw.get("resulting_request_hash"), "resulting_request_hash") or "",
        bound_manifest_sha256=_nonempty_text(raw.get("bound_manifest_sha256"), "bound_manifest_sha256") or "",
        bound_requirements_sha256=_nonempty_text(
            raw.get("bound_requirements_sha256"), "bound_requirements_sha256"
        )
        or "",
        items=tuple(items),
    )
    resolution.validate()
    return resolution


def load_input_resolution(path: Path) -> InputResolution:
    value = Path(path)
    try:
        metadata = value.lstat()
    except OSError as exc:
        raise ResolutionError("RESOLUTION_UNAVAILABLE", "input resolution cannot be accessed") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1:
        raise ResolutionError("RESOLUTION_PATH_UNSAFE", "input resolution must be a single-link regular file")
    if metadata.st_size > RESOLUTION_BYTES_MAX:
        raise ResolutionError("RESOLUTION_TOO_LARGE", "input resolution exceeds its metadata size ceiling")
    try:
        raw = json.loads(value.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ResolutionError("RESOLUTION_PARSE_ERROR", "input resolution is not valid UTF-8 JSON") from exc
    if not isinstance(raw, dict):
        raise ResolutionError("RESOLUTION_NOT_MAPPING", "input resolution must be an object")
    return input_resolution_from_mapping(raw)


def validate_resolution_bindings(
    resolution: InputResolution,
    *,
    run_id: str,
    bound_request_hash: str,
    resulting_request_hash: str,
    manifest_sha256: str,
    requirements_sha256: str,
) -> None:
    resolution.validate()
    if resolution.run_id != run_id:
        raise ResolutionError("RESOLUTION_RUN_MISMATCH", "resolution is bound to another run")
    if resolution.bound_request_hash != bound_request_hash:
        raise ResolutionError("RESOLUTION_BOUND_REQUEST_STALE", "resolution does not bind the prior input report")
    if resolution.resulting_request_hash != resulting_request_hash:
        raise ResolutionError("RESOLUTION_REQUEST_STALE", "resolution does not bind the current resulting request")
    if resolution.bound_manifest_sha256 != manifest_sha256:
        raise ResolutionError("RESOLUTION_MANIFEST_STALE", "resolution manifest binding is stale")
    if resolution.bound_requirements_sha256 != requirements_sha256:
        raise ResolutionError("RESOLUTION_CONFIG_STALE", "resolution requirement-config binding is stale")


def persist_input_resolution(private_runtime_root: Path, resolution: InputResolution) -> Path:
    """Write an input resolution once under ignored private runtime; never overwrite."""

    resolution.validate()
    root = Path(private_runtime_root)
    if root.is_symlink():
        raise ResolutionError("PRIVATE_RUNTIME_SYMLINK", "private runtime must not be a symbolic link")
    root.mkdir(parents=True, exist_ok=True)
    destination = root / "input_resolutions"
    if destination.exists() and (destination.is_symlink() or not destination.is_dir()):
        raise ResolutionError("RESOLUTION_DIRECTORY_UNSAFE", "input-resolution directory is unsafe")
    destination.mkdir(exist_ok=True)
    payload = json.dumps(resolution.as_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        return atomic_write_text(destination, resolution.resolution_id + ".json", payload)
    except PathSafetyError as exc:
        raise ResolutionError(exc.code, exc.message) from exc
