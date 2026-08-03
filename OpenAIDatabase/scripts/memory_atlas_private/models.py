from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class RunState(str, Enum):
    DISCOVERING = "DISCOVERING"
    CAPTURING = "CAPTURING"
    VERIFYING_OBJECTS = "VERIFYING_OBJECTS"
    PUBLISHING_FACTS = "PUBLISHING_FACTS"
    REFRESHING_ATLAS = "REFRESHING_ATLAS"
    SUCCEEDED = "SUCCEEDED"
    WAITING_SOURCE = "WAITING_SOURCE"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"


class SourceState(str, Enum):
    READY = "READY"
    MISSING_OPTIONAL = "MISSING_OPTIONAL"
    MISSING_REQUIRED = "MISSING_REQUIRED"
    UNREADABLE = "UNREADABLE"
    EMPTY = "EMPTY"


@dataclass(frozen=True)
class SourceSpec:
    source_id: str
    label_zh: str
    path_template: str
    kind: str
    required: bool
    recursive: bool = True
    env_var: str | None = None
    include_globs: tuple[str, ...] = ("**/*",)
    exclude_globs: tuple[str, ...] = ()


@dataclass(frozen=True)
class InventoryRecord:
    source_id: str
    source_root: str
    relative_path: str
    materialized_path: str
    kind: str
    size_bytes: int
    mtime_ns: int
    sha256: str
    original_sha256: str
    snapshot_created: bool


@dataclass(frozen=True)
class ObjectReceipt:
    sha256: str
    object_key: str
    size_bytes: int
    operation: str
    readback_sha256: str
    readback_verified: bool
    provider_version: str


@dataclass
class SourceCoverage:
    source_id: str
    label_zh: str
    required: bool
    state: SourceState
    object_count: int = 0
    size_bytes: int = 0
    message_zh: str = ""


@dataclass
class RunManifest:
    schema_version: str
    run_id: str
    started_at: str
    completed_at: str | None
    state: RunState
    source_coverages: list[SourceCoverage] = field(default_factory=list)
    objects: list[ObjectReceipt] = field(default_factory=list)
    normalized_batch_key: str | None = None
    private_database_paths: list[str] = field(default_factory=list)
    error_signatures: list[str] = field(default_factory=list)
    bytes_discovered: int = 0
    bytes_uploaded: int = 0
    objects_new: int = 0
    objects_repaired: int = 0
    objects_unchanged: int = 0
    source_capture_host: str = ""
    product_version: str = "0.0.0.31"
    taskpack_version: str = "0.0.0.2"
    github_private_release_backup: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        value = asdict(self)
        value["state"] = self.state.value
        for coverage in value["source_coverages"]:
            state = coverage.get("state")
            if isinstance(state, SourceState):
                coverage["state"] = state.value
        return value


@dataclass(frozen=True)
class NormalizedEvent:
    event_id: str
    source_id: str
    object_sha256: str
    relative_path: str
    occurred_at: str
    record_type: str
    project: str
    activity: str
    augmentation_mode: str
    outcome_state: str
    effort_minutes: float | None
    evidence_ref: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class ActionRequest:
    request_id: str
    action: str
    requested_at: str
    idempotency_key: str
    state: str
    source_required: bool
    message_zh: str
