"""Append-only separation for source, candidate, decision, and validated-fact records."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from .paths import PathSafetyError, atomic_write_text


RECORD_ID_RE = re.compile(r"^rec_[a-z_]+_[0-9a-f]{32}$")
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class RecordLayer(str, Enum):
    SOURCE_RECORD = "SOURCE_RECORD"
    CANDIDATE = "CANDIDATE"
    DECISION = "DECISION"
    APPROVED_FACT = "APPROVED_FACT"


class RecordLayerError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


@dataclass(frozen=True)
class LayerRecord:
    """Private lineage envelope; APPROVED_FACT is a data gate, not company approval."""

    record_id: str
    layer: RecordLayer
    payload_hash: str
    private_payload_ref: str
    source_refs: Tuple[str, ...] = ()
    candidate_refs: Tuple[str, ...] = ()
    decision_refs: Tuple[str, ...] = ()
    evidence_refs: Tuple[str, ...] = ()
    supersedes_ref: Optional[str] = None

    def validate(self) -> None:
        if not RECORD_ID_RE.fullmatch(self.record_id):
            raise RecordLayerError("RECORD_ID_INVALID", "record ID must be opaque and canonical")
        if not isinstance(self.layer, RecordLayer):
            raise RecordLayerError("RECORD_LAYER_INVALID", "record layer must be an explicit enum")
        if not SHA256_RE.fullmatch(self.payload_hash):
            raise RecordLayerError("PAYLOAD_HASH_INVALID", "private payload hash must be lowercase SHA256")
        if not self.private_payload_ref.startswith("private://") or len(self.private_payload_ref) <= len("private://"):
            raise RecordLayerError("PAYLOAD_REF_INVALID", "payload reference must use the private namespace")
        references = self.source_refs + self.candidate_refs + self.decision_refs
        if any(not RECORD_ID_RE.fullmatch(item) for item in references):
            raise RecordLayerError("RECORD_REF_INVALID", "record references must use canonical opaque IDs")
        if any(not isinstance(item, str) or not item for item in self.evidence_refs):
            raise RecordLayerError("EVIDENCE_REF_INVALID", "evidence references must be nonempty opaque text")
        if self.supersedes_ref is not None and not RECORD_ID_RE.fullmatch(self.supersedes_ref):
            raise RecordLayerError("SUPERSEDES_REF_INVALID", "supersession reference must be canonical")
        if self.layer is RecordLayer.SOURCE_RECORD:
            if references:
                raise RecordLayerError("SOURCE_LAYER_HAS_DERIVED_REFS", "source records cannot point to derived layers")
        elif self.layer is RecordLayer.CANDIDATE:
            if not self.source_refs or self.candidate_refs or self.decision_refs:
                raise RecordLayerError("CANDIDATE_LINEAGE_INVALID", "candidates require source refs only")
        elif self.layer is RecordLayer.DECISION:
            if not self.candidate_refs or not self.evidence_refs or self.decision_refs:
                raise RecordLayerError("DECISION_LINEAGE_INVALID", "decisions require candidate and evidence refs")
        elif self.layer is RecordLayer.APPROVED_FACT:
            if not self.source_refs or not self.decision_refs or not self.evidence_refs:
                raise RecordLayerError(
                    "FACT_LINEAGE_INVALID",
                    "validated facts require source, decision, and evidence refs",
                )

    def as_private_dict(self) -> Dict[str, Any]:
        self.validate()
        return {
            "schema_version": "kmfa.project_cost.layer_record.v1",
            "record_id": self.record_id,
            "layer": self.layer.value,
            "payload_hash": self.payload_hash,
            "private_payload_ref": self.private_payload_ref,
            "source_refs": list(self.source_refs),
            "candidate_refs": list(self.candidate_refs),
            "decision_refs": list(self.decision_refs),
            "evidence_refs": list(self.evidence_refs),
            "supersedes_ref": self.supersedes_ref,
        }


def append_layer_record(private_run_root: Path, record: LayerRecord) -> Path:
    """Persist one immutable envelope with exclusive creation; never update in place."""

    record.validate()
    root = Path(private_run_root)
    if root.is_symlink():
        raise RecordLayerError("PRIVATE_RUN_ROOT_SYMLINK", "private run root must not be a symbolic link")
    root.mkdir(parents=True, exist_ok=True)
    try:
        resolved = root.resolve(strict=True)
    except OSError as exc:
        raise RecordLayerError("PRIVATE_RUN_ROOT_UNAVAILABLE", "private run root cannot be resolved") from exc
    layer_dir = resolved / "layers" / record.layer.value.lower()
    current = resolved
    for component in ("layers", record.layer.value.lower()):
        current = current / component
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            raise RecordLayerError("PRIVATE_LAYER_PATH_UNSAFE", "private layer path is not a safe directory")
        current.mkdir(exist_ok=True)
    payload = json.dumps(record.as_private_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    try:
        return atomic_write_text(layer_dir, record.record_id + ".json", payload)
    except PathSafetyError as exc:
        raise RecordLayerError(exc.code, exc.message) from exc
