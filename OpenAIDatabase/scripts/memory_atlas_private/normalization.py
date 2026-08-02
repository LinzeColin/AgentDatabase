from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .hashing import stable_id
from .models import InventoryRecord, NormalizedEvent


def _iso_from_ns(value: int) -> str:
    return datetime.fromtimestamp(value / 1_000_000_000, tz=timezone.utc).replace(microsecond=0).isoformat()


def _project_from_path(relative_path: str) -> str:
    parts = [part for part in relative_path.replace("\\", "/").split("/") if part]
    return parts[0] if len(parts) > 1 else "personal"


def _activity_from_text(text: str) -> str:
    lowered = text.lower()
    rules = (
        ("verification_repair", ("test", "verify", "验收", "修复", "bug", "failure", "error")),
        ("development_deployment", ("deploy", "build", "code", "开发", "上线", "docker", "systemd")),
        ("product_planning", ("prd", "roadmap", "产品", "需求", "架构", "scope")),
        ("research_diagnosis", ("research", "分析", "诊断", "调研", "compare", "benchmark")),
        ("management_learning", ("学习", "workshop", "管理", "meeting", "课程")),
        ("decision_execution", ("decision", "批准", "决定", "执行", "action")),
    )
    for activity, terms in rules:
        if any(term in lowered for term in terms):
            return activity
    return "unknown"


SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _verification_pass(record: InventoryRecord, payload: dict[str, Any]) -> bool:
    # Raw conversations, exports and arbitrary JSON are untrusted observations. They
    # may claim that deployment or restoration succeeded, but cannot promote
    # themselves into the Verified Outcome numerator. Only files discovered through
    # an explicitly configured, operations-owned evidence_adapter source may do so.
    if record.kind != "evidence_adapter":
        return False
    verification = payload.get("verification")
    if not isinstance(verification, dict):
        return False
    if verification.get("schema_version") != "memory_atlas.verification.v1":
        return False
    if verification.get("kind") != "evidence_adapter_result":
        return False
    status = str(verification.get("status") or verification.get("state") or "").upper()
    refs = verification.get("evidence_refs")
    verifier = str(verification.get("verifier") or "").strip()
    oracle = str(verification.get("oracle") or "").strip()
    subject_ref = str(verification.get("subject_ref") or "").strip()
    if status not in {"PASS", "VERIFIED"} or not verifier or not oracle or not subject_ref:
        return False
    if not isinstance(refs, list) or not refs:
        return False
    for ref in refs:
        if not isinstance(ref, dict):
            return False
        uri = str(ref.get("uri") or "").strip()
        digest = str(ref.get("sha256") or "").strip().lower()
        if not uri or not SHA256_RE.fullmatch(digest):
            return False
    return True


def _outcome_from_payload(record: InventoryRecord, payload: dict[str, Any]) -> str:
    verified_states = {
        "restore_verified", "deployed_verified", "adopted_verified", "decision_impact_verified"
    }
    explicit = str(payload.get("outcome_state") or "").strip().lower()
    if explicit in verified_states:
        # Raw text/JSON can claim success but cannot prove world state. A dedicated
        # evidence adapter must attach a PASS/VERIFIED status, at least one immutable
        # evidence reference, and the deterministic/human verifier identity.
        return explicit if _verification_pass(record, payload) else f"claimed_{explicit.removesuffix('_verified')}"
    if explicit:
        return explicit
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(term in text for term in ("restore_verified", "恢复成功", "restore pass")):
        return "claimed_restore"
    if any(term in text for term in ("deployed_verified", "上线并验证", "post_deploy pass")):
        return "claimed_deployed"
    if any(term in text for term in ("adopted_verified", "已采用", "workflow adopted")):
        return "claimed_adopted"
    if any(term in text for term in ("decision_impact_verified", "决策影响", "cash impact")):
        return "claimed_decision_impact"
    if any(term in text for term in ("failed", "error", "失败")):
        return "claimed_failure"
    return "unverified"


def _augmentation_mode(payload: dict[str, Any]) -> str:
    text = json.dumps(payload, ensure_ascii=False).lower()
    if any(term in text for term in ("automation", "自动化", "scheduled")):
        return "automation"
    if any(term in text for term in ("recommend", "建议", "analysis", "分析")):
        return "augmentation"
    return "mixed_or_unknown"


def _event_from_payload(record: InventoryRecord, index: int, payload: dict[str, Any], record_type: str) -> NormalizedEvent:
    text = json.dumps(payload, ensure_ascii=False)
    occurred = str(payload.get("created_at") or payload.get("updated_at") or payload.get("timestamp") or _iso_from_ns(record.mtime_ns))
    effort = payload.get("effort_minutes")
    effort_value = float(effort) if isinstance(effort, (int, float)) and effort >= 0 else None
    return NormalizedEvent(
        event_id=stable_id(record.sha256, str(index), record_type, prefix="evt"),
        source_id=record.source_id,
        object_sha256=record.sha256,
        relative_path=record.relative_path,
        occurred_at=occurred,
        record_type=record_type,
        project=str(payload.get("project") or _project_from_path(record.relative_path)),
        activity=str(payload.get("activity") or _activity_from_text(text)),
        augmentation_mode=str(payload.get("augmentation_mode") or _augmentation_mode(payload)),
        # Never trust an explicit success label by itself. `_outcome_from_payload`
        # preserves ordinary non-success states but requires a bound verification
        # envelope before any *_verified state can enter the outcome numerator.
        outcome_state=_outcome_from_payload(record, payload),
        effort_minutes=effort_value,
        evidence_ref=f"r2://sha256/{record.sha256}",
        payload=payload,
    )


def normalize_record(record: InventoryRecord, max_text_bytes: int = 8 * 1024 * 1024) -> Iterable[NormalizedEvent]:
    path = Path(record.materialized_path)
    suffix = path.suffix.lower()
    if record.kind == "sqlite":
        yield _event_from_payload(record, 0, {
            "source_id": record.source_id,
            "relative_path": record.relative_path,
            "size_bytes": record.size_bytes,
            "snapshot_sha256": record.sha256,
            "note": "SQLite 内容通过一致性快照保存；表级解析由显式适配器执行。",
        }, "sqlite_snapshot")
        return
    if record.size_bytes > max_text_bytes or suffix not in {".json", ".jsonl", ".ndjson", ".md", ".txt", ".toml", ".yaml", ".yml"}:
        yield _event_from_payload(record, 0, {
            "source_id": record.source_id,
            "relative_path": record.relative_path,
            "size_bytes": record.size_bytes,
            "content_ref": f"r2://sha256/{record.sha256}",
        }, "object_metadata")
        return
    raw = path.read_text(encoding="utf-8", errors="replace")
    if suffix in {".jsonl", ".ndjson"}:
        emitted = False
        for index, line in enumerate(raw.splitlines()):
            if not line.strip():
                continue
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                value = {"text": line}
            if not isinstance(value, dict):
                value = {"value": value}
            emitted = True
            yield _event_from_payload(record, index, value, "jsonl_record")
        if not emitted:
            yield _event_from_payload(record, 0, {"text": "", "empty": True}, "empty_text")
        return
    if suffix == ".json":
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            value = {"text": raw}
        if isinstance(value, list):
            for index, item in enumerate(value):
                yield _event_from_payload(record, index, item if isinstance(item, dict) else {"value": item}, "json_item")
        else:
            yield _event_from_payload(record, 0, value if isinstance(value, dict) else {"value": value}, "json_document")
        return
    # Plain text is preserved verbatim in the private normalized batch. No redaction occurs.
    yield _event_from_payload(record, 0, {"text": raw}, "text_document")
