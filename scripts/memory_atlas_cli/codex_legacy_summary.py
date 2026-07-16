"""Additive compatibility migration for legacy redacted Codex summaries."""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import stat
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

SCHEMA_VERSION = "memory_atlas.codex_legacy_summary_contract.v1_2_1_s07_p2_t3"
SEMANTICS_SCHEMA_VERSION = "memory_atlas.codex_legacy_summary_semantics.v1_2_1_s07_p2_t3"
MODEL_SCHEMA_VERSION = "memory_atlas.codex_legacy_summary_model.v1_2_1_s07_p2_t3"
STATE_SCHEMA_VERSION = "memory_atlas.codex_legacy_summary_state.v1_2_1_s07_p2_t3"
TASK_ID = "S07-P2-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P2-T3"
SOURCE_ID = "codex"
CONTRACT_PATH = Path("config/data_sources/codex_legacy_summary.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_legacy_summary.v1_2_1_s07_p2_t3.json"
)
DERIVED_STATE_PATH = Path("data/derived/codex/codex_derived_state.json")
CANONICAL_BEHAVIOR_PATH = Path("data/derived/codex/codex_behavior_summary.json")
ATLAS_STATE_PATH = Path("data/sync_state/codex_atlas.json")
STATE_PATH = Path("data/sync_state/codex_legacy_summary.json")
RAW_ARCHIVE_ROOT = Path("data/raw_archives/codex")
RAW_LEDGER_PATH = Path(
    "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
)
LEGACY_OUTPUTS = {
    "session_manifest": "data/processed/codex/codex_session_manifest.jsonl",
    "daily_activity": "data/processed/codex/codex_daily_activity.jsonl",
    "processed_snapshot": "data/processed/codex/codex_activity_snapshot.json",
    "derived_snapshot": "data/derived/codex/codex_activity_snapshot.json",
    "recommendations": "data/derived/codex/codex_agent_recommendations.json",
    "behavior_report": "data/derived/codex/codex_behavior_report.md",
}
CONSUMER_OUTPUTS = {
    "atlas_snapshot": "data/derived/visualization/memory_atlas.json",
    "atlas_publication_state": ATLAS_STATE_PATH.as_posix(),
    "agent_context_json": "data/derived/agent_context/agent_context_pack.json",
    "agent_context_markdown": "data/derived/agent_context/AGENT_CONTEXT.md",
    "migration_state": STATE_PATH.as_posix(),
}
EXPECTED_PHASE_BOUNDARY = {
    "legacy_summary_migrated": True,
    "does_not_modify_raw": True,
    "does_not_rewrite_legacy_schema_versions": True,
    "does_not_commit_or_push": True,
    "does_not_deploy": True,
    "next_task": "S07-P3-T1",
}
EXPECTED_CONTRACT = {
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "purpose": (
        "Preserve additive reads of the legacy redacted Codex summaries while "
        "making it impossible to treat those summaries as a full or recoverable raw backup."
    ),
    "legacy_outputs": LEGACY_OUTPUTS,
    "canonical_truth": {
        "derived_state_ref": DERIVED_STATE_PATH.as_posix(),
        "behavior_summary_ref": CANONICAL_BEHAVIOR_PATH.as_posix(),
        "raw_archive_root": RAW_ARCHIVE_ROOT.as_posix(),
        "raw_ledger_ref": RAW_LEDGER_PATH.as_posix(),
        "required_source_kind": "derived_from_verified_recoverable_sanitized_raw_archives",
        "recoverable_sanitized_raw_required": True,
    },
    "semantics": {
        "metadata_field": "summary_semantics",
        "artifact_role": "redacted_derived_summary",
        "output_policy": "derived_summary_not_full_raw_backup",
        "full_raw_backup": False,
        "recoverable_raw_backup": False,
        "raw_message_text_included": False,
        "plaintext_credentials_included": False,
        "local_absolute_paths_included": False,
    },
    "compatibility": {
        "legacy_schema_versions_preserved": True,
        "existing_fields_preserved": True,
        "additive_metadata_only": True,
        "missing_metadata_read_policy": "normalize_in_memory_as_legacy_redacted_summary",
        "conflicting_truth_policy": "fail_closed",
    },
    "consumers": CONSUMER_OUTPUTS,
    "model_parameters_ref": MODEL_PARAMETERS_PATH.as_posix(),
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}
EXPECTED_MODEL_PARAMETERS = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-008",
    "formula_id": "FORM-008",
    "purpose": (
        "Classify legacy Codex summary artifacts without changing their historical "
        "schema or recommendation values."
    ),
    "classification": {
        "artifact_role": "redacted_derived_summary",
        "output_policy": "derived_summary_not_full_raw_backup",
        "full_raw_backup": False,
        "recoverable_raw_backup": False,
        "canonical_raw_source_role": "separate_verified_recoverable_sanitized_archive",
    },
    "compatibility": {
        "metadata_mode": "additive_summary_semantics_field",
        "legacy_missing_field_mode": "normalize_on_read",
        "conflicting_claim_mode": "fail_closed",
    },
    "calibration_boundary": (
        "This Task adds deterministic truth labels only. It does not recalculate "
        "historical recommendations, activity scores, ranking weights or business-optimal model parameters."
    ),
}
_MAX_CONTROL_BYTES = 16 * 1024 * 1024
_MAX_JSONL_BYTES = 32 * 1024 * 1024
_REPORT_START = "<!-- codex-legacy-summary-semantics:start -->"
_REPORT_END = "<!-- codex-legacy-summary-semantics:end -->"


class CodexLegacySummaryError(ValueError):
    """Raised when legacy summary compatibility cannot be proven safely."""

    def __init__(self, code: str, detail: str | None = None) -> None:
        super().__init__(detail or code)
        self.code = code


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _json_bytes(payload: Any) -> bytes:
    return (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _jsonl_bytes(rows: list[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    ).encode("utf-8")


def _safe_relative(value: str) -> PurePosixPath:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or any(part in {"", ".", ".."} for part in path.parts):
        raise CodexLegacySummaryError("codex_legacy_summary_path_invalid")
    return path


def _assert_safe_parents(database_dir: Path, path: Path) -> None:
    database_dir = database_dir.resolve()
    current = path.parent
    while current != database_dir:
        if database_dir not in current.parents:
            raise CodexLegacySummaryError("codex_legacy_summary_path_invalid")
        if os.path.lexists(current):
            metadata = current.lstat()
            if not stat.S_ISDIR(metadata.st_mode):
                raise CodexLegacySummaryError("codex_legacy_summary_parent_unsafe")
        current = current.parent


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_bundle(database_dir: Path, payloads: dict[str, bytes]) -> list[str]:
    changed: list[str] = []
    staged: dict[str, Path] = {}
    originals: dict[str, bytes | None] = {}
    try:
        for relative, payload in payloads.items():
            target = database_dir / _safe_relative(relative)
            _assert_safe_parents(database_dir, target)
            if os.path.lexists(target):
                metadata = target.lstat()
                if not stat.S_ISREG(metadata.st_mode):
                    raise CodexLegacySummaryError(
                        "codex_legacy_summary_output_target_unsafe", relative
                    )
                current = target.read_bytes()
                if current == payload:
                    continue
                originals[relative] = current
            else:
                originals[relative] = None
            target.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{target.name}.", suffix=".tmp", dir=target.parent
            )
            temp_path = Path(temp_name)
            with os.fdopen(descriptor, "wb") as handle:
                os.fchmod(handle.fileno(), 0o644)
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            staged[relative] = temp_path
        for relative, temp_path in staged.items():
            target = database_dir / _safe_relative(relative)
            os.replace(temp_path, target)
            changed.append(relative)
            _fsync_directory(target.parent)
    except Exception:
        for relative in reversed(changed):
            target = database_dir / _safe_relative(relative)
            original = originals[relative]
            if original is None:
                target.unlink(missing_ok=True)
            else:
                descriptor, temp_name = tempfile.mkstemp(
                    prefix=f".{target.name}.rollback.", suffix=".tmp", dir=target.parent
                )
                with os.fdopen(descriptor, "wb") as handle:
                    handle.write(original)
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(temp_name, target)
                _fsync_directory(target.parent)
        raise
    finally:
        for temp_path in staged.values():
            temp_path.unlink(missing_ok=True)
    return changed


def _read_regular_bytes(database_dir: Path, relative: str, *, max_bytes: int = _MAX_CONTROL_BYTES) -> bytes:
    path = database_dir / _safe_relative(relative)
    if not os.path.lexists(path):
        raise CodexLegacySummaryError("codex_legacy_summary_input_missing", relative)
    metadata = path.lstat()
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        raise CodexLegacySummaryError("codex_legacy_summary_input_unsafe", relative)
    return path.read_bytes()


def _load_json_bytes(payload: bytes, code: str) -> dict[str, Any]:
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexLegacySummaryError(code) from exc
    if not isinstance(value, dict):
        raise CodexLegacySummaryError(code)
    return value


def _load_json(database_dir: Path, relative: str, code: str) -> tuple[dict[str, Any], bytes]:
    payload = _read_regular_bytes(database_dir, relative)
    return _load_json_bytes(payload, code), payload


def _load_jsonl(database_dir: Path, relative: str) -> tuple[list[dict[str, Any]], bytes]:
    payload = _read_regular_bytes(database_dir, relative, max_bytes=_MAX_JSONL_BYTES)
    rows: list[dict[str, Any]] = []
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CodexLegacySummaryError("codex_legacy_summary_jsonl_invalid", relative) from exc
    for line_number, line in enumerate(text.splitlines(), start=1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexLegacySummaryError(
                "codex_legacy_summary_jsonl_invalid", f"{relative}:{line_number}"
            ) from exc
        if not isinstance(row, dict):
            raise CodexLegacySummaryError(
                "codex_legacy_summary_jsonl_invalid", f"{relative}:{line_number}"
            )
        rows.append(row)
    if not rows:
        raise CodexLegacySummaryError("codex_legacy_summary_jsonl_empty", relative)
    return rows, payload


def load_codex_legacy_summary_contract(database_dir: Path) -> dict[str, Any]:
    contract, _ = _load_json(
        database_dir.resolve(), CONTRACT_PATH.as_posix(), "codex_legacy_summary_contract_invalid"
    )
    if contract != EXPECTED_CONTRACT:
        raise CodexLegacySummaryError("codex_legacy_summary_contract_drift")
    model, _ = _load_json(
        database_dir.resolve(),
        MODEL_PARAMETERS_PATH.as_posix(),
        "codex_legacy_summary_model_invalid",
    )
    if model != EXPECTED_MODEL_PARAMETERS:
        raise CodexLegacySummaryError("codex_legacy_summary_model_drift")
    return contract


def build_summary_semantics(
    artifact_kind: str,
    canonical_truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    truth = canonical_truth or {}
    archive_count = int(truth.get("archive_count") or 0)
    canonical_session_count = int(truth.get("session_count") or 0)
    return {
        "schema_version": SEMANTICS_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "artifact_kind": artifact_kind,
        "artifact_role": "redacted_derived_summary",
        "output_policy": "derived_summary_not_full_raw_backup",
        "full_raw_backup": False,
        "recoverable_raw_backup": False,
        "raw_message_text_included": False,
        "plaintext_credentials_included": False,
        "local_absolute_paths_included": False,
        "canonical_raw_source": {
            "role": "separate_source_of_truth",
            "availability": (
                "verified_recoverable_sanitized_archives"
                if archive_count > 0 and canonical_session_count > 0
                else "not_asserted_by_legacy_summary"
            ),
            "archive_root": RAW_ARCHIVE_ROOT.as_posix(),
            "raw_ledger_ref": RAW_LEDGER_PATH.as_posix(),
            "behavior_summary_ref": CANONICAL_BEHAVIOR_PATH.as_posix(),
            "archive_count": archive_count,
            "canonical_session_count": canonical_session_count,
        },
        "compatibility": {
            "legacy_schema_preserved": True,
            "existing_fields_preserved": True,
            "additive_metadata_only": True,
        },
    }


def _reject_conflicting_truth(payload: dict[str, Any]) -> None:
    if payload.get("full_raw_backup") is True or payload.get("recoverable_raw_backup") is True:
        raise CodexLegacySummaryError("codex_legacy_summary_conflicting_raw_claim")
    semantics = payload.get("summary_semantics")
    if semantics is None:
        return
    if not isinstance(semantics, dict):
        raise CodexLegacySummaryError("codex_legacy_summary_semantics_invalid")
    required_false = (
        "full_raw_backup",
        "recoverable_raw_backup",
        "raw_message_text_included",
        "plaintext_credentials_included",
        "local_absolute_paths_included",
    )
    if any(semantics.get(field) is not False for field in required_false):
        raise CodexLegacySummaryError("codex_legacy_summary_conflicting_raw_claim")
    if semantics.get("artifact_role") not in {None, "redacted_derived_summary"}:
        raise CodexLegacySummaryError("codex_legacy_summary_role_conflict")
    if semantics.get("output_policy") not in {None, "derived_summary_not_full_raw_backup"}:
        raise CodexLegacySummaryError("codex_legacy_summary_policy_conflict")


def normalize_legacy_summary_payload(
    payload: dict[str, Any],
    artifact_kind: str,
    canonical_truth: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return an additive normalized copy while accepting metadata-free legacy input."""

    if not isinstance(payload, dict):
        raise CodexLegacySummaryError("codex_legacy_summary_payload_invalid")
    _reject_conflicting_truth(payload)
    normalized = copy.deepcopy(payload)
    existing = normalized.get("summary_semantics")
    if canonical_truth is None and isinstance(existing, dict):
        normalized["summary_semantics"] = existing
    else:
        normalized["summary_semantics"] = build_summary_semantics(
            artifact_kind, canonical_truth
        )
    return normalized


def _canonical_truth(database_dir: Path) -> tuple[dict[str, Any], dict[str, str]]:
    behavior, behavior_bytes = _load_json(
        database_dir,
        CANONICAL_BEHAVIOR_PATH.as_posix(),
        "codex_legacy_summary_canonical_behavior_invalid",
    )
    state, state_bytes = _load_json(
        database_dir,
        DERIVED_STATE_PATH.as_posix(),
        "codex_legacy_summary_derived_state_invalid",
    )
    source_truth = behavior.get("source_truth")
    output_record = state.get("output_hashes", {}).get(CANONICAL_BEHAVIOR_PATH.as_posix())
    if (
        state.get("schema_version")
        != "memory_atlas.codex_derived_state.v1_2_1_s07_p2_t1"
        or not isinstance(source_truth, dict)
        or source_truth.get("kind")
        != "derived_from_verified_recoverable_sanitized_raw_archives"
        or source_truth.get("full_raw_backup") is not False
        or source_truth.get("recoverable_sanitized_raw_available") is not True
        or int(behavior.get("archive_count") or 0) <= 0
        or int(behavior.get("session_count") or 0) <= 0
        or not isinstance(output_record, dict)
        or output_record.get("sha256") != _sha256(behavior_bytes)
        or output_record.get("byte_size") != len(behavior_bytes)
    ):
        raise CodexLegacySummaryError("codex_legacy_summary_canonical_truth_unverified")
    return {
        "archive_count": int(behavior["archive_count"]),
        "session_count": int(behavior["session_count"]),
        "behavior_summary_sha256": _sha256(behavior_bytes),
        "derived_state_sha256": _sha256(state_bytes),
    }, {
        CANONICAL_BEHAVIOR_PATH.as_posix(): _sha256(behavior_bytes),
        DERIVED_STATE_PATH.as_posix(): _sha256(state_bytes),
    }


def _replace_marked_section(
    text: str,
    start: str,
    end: str,
    section_lines: list[str],
) -> str:
    section = "\n".join([start, *section_lines, end])
    if start in text or end in text:
        if text.count(start) != 1 or text.count(end) != 1 or text.index(start) > text.index(end):
            raise CodexLegacySummaryError("codex_legacy_summary_markdown_marker_invalid")
        prefix, rest = text.split(start, 1)
        _old, suffix = rest.split(end, 1)
        return prefix.rstrip() + "\n\n" + section + "\n" + suffix.lstrip("\n")
    return text.rstrip() + "\n\n" + section + "\n"


def _report_semantics(text: str, canonical_truth: dict[str, Any]) -> str:
    return _replace_marked_section(
        text,
        _REPORT_START,
        _REPORT_END,
        [
            "## 数据语义与恢复边界",
            "",
            "- 本报告及配套 JSON/JSONL 是脱敏派生摘要，不是 full raw backup，也不能单独恢复 Codex 原始数据。",
            "- 旧 schema 和既有字段继续兼容读取；新增 `summary_semantics` 只负责说明真相，不重算历史建议或活动分数。",
            (
                "- 可恢复真源是另行验证的 sanitized Codex archives："
                f"`{RAW_ARCHIVE_ROOT.as_posix()}`（{canonical_truth['archive_count']} 个 archive，"
                f"{canonical_truth['session_count']} 个 canonical session）。"
            ),
        ],
    )


def _migrated_legacy_payloads(
    database_dir: Path,
    canonical_truth: dict[str, Any],
) -> tuple[dict[str, bytes], dict[str, Any], dict[str, int]]:
    session_rows, _ = _load_jsonl(database_dir, LEGACY_OUTPUTS["session_manifest"])
    daily_rows, _ = _load_jsonl(database_dir, LEGACY_OUTPUTS["daily_activity"])
    processed, _ = _load_json(
        database_dir,
        LEGACY_OUTPUTS["processed_snapshot"],
        "codex_legacy_summary_processed_snapshot_invalid",
    )
    derived, _ = _load_json(
        database_dir,
        LEGACY_OUTPUTS["derived_snapshot"],
        "codex_legacy_summary_derived_snapshot_invalid",
    )
    recommendations, _ = _load_json(
        database_dir,
        LEGACY_OUTPUTS["recommendations"],
        "codex_legacy_summary_recommendations_invalid",
    )
    report_bytes = _read_regular_bytes(database_dir, LEGACY_OUTPUTS["behavior_report"])
    try:
        report = report_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CodexLegacySummaryError("codex_legacy_summary_report_invalid") from exc
    if (
        any(row.get("schema_version") != "codex_session_manifest.v1" for row in session_rows)
        or processed.get("schema_version") != "codex_activity_snapshot.v1"
        or derived.get("schema_version") != "codex_activity_snapshot.v1"
        or recommendations.get("schema_version") != "codex_agent_recommendations.v1"
    ):
        raise CodexLegacySummaryError("codex_legacy_summary_schema_incompatible")
    migrated_sessions = [
        normalize_legacy_summary_payload(row, "session_manifest_row", canonical_truth)
        for row in session_rows
    ]
    migrated_daily = [
        normalize_legacy_summary_payload(row, "daily_activity_row", canonical_truth)
        for row in daily_rows
    ]
    migrated_processed = normalize_legacy_summary_payload(
        processed, "processed_activity_snapshot", canonical_truth
    )
    migrated_derived = normalize_legacy_summary_payload(
        derived, "derived_activity_snapshot", canonical_truth
    )
    migrated_recommendations = normalize_legacy_summary_payload(
        recommendations, "agent_recommendations", canonical_truth
    )
    payloads = {
        LEGACY_OUTPUTS["session_manifest"]: _jsonl_bytes(migrated_sessions),
        LEGACY_OUTPUTS["daily_activity"]: _jsonl_bytes(migrated_daily),
        LEGACY_OUTPUTS["processed_snapshot"]: _json_bytes(migrated_processed),
        LEGACY_OUTPUTS["derived_snapshot"]: _json_bytes(migrated_derived),
        LEGACY_OUTPUTS["recommendations"]: _json_bytes(migrated_recommendations),
        LEGACY_OUTPUTS["behavior_report"]: _report_semantics(
            report, canonical_truth
        ).encode("utf-8"),
    }
    counts = {
        "legacy_session_count": len(session_rows),
        "legacy_day_count": len(daily_rows),
        "legacy_recommendation_count": sum(
            len(recommendations.get(group, {}).get("current", []))
            for group in ("memory", "meta_data")
            if isinstance(recommendations.get(group), dict)
        ),
    }
    return payloads, migrated_recommendations, counts


def _migrate_atlas(
    database_dir: Path,
    recommendations: dict[str, Any],
    canonical_truth: dict[str, Any],
) -> tuple[bytes, dict[str, Any], bytes]:
    atlas_relative = CONSUMER_OUTPUTS["atlas_snapshot"]
    atlas, atlas_bytes = _load_json(
        database_dir, atlas_relative, "codex_legacy_summary_atlas_invalid"
    )
    atlas_state, atlas_state_bytes = _load_json(
        database_dir,
        ATLAS_STATE_PATH.as_posix(),
        "codex_legacy_summary_atlas_state_invalid",
    )
    snapshot_record = atlas_state.get("outputs", {}).get("atlas_snapshot")
    publication = atlas.get("codex_publication")
    if (
        atlas_state.get("schema_version")
        != "memory_atlas.codex_atlas_publication_state.v1_2_1_s07_p2_t2"
        or not isinstance(snapshot_record, dict)
        or snapshot_record.get("path") != atlas_relative
        or snapshot_record.get("sha256") != _sha256(atlas_bytes)
        or snapshot_record.get("byte_size") != len(atlas_bytes)
        or not isinstance(publication, dict)
        or publication.get("counts", {}).get("event_count")
        != canonical_truth["session_count"]
    ):
        raise CodexLegacySummaryError("codex_legacy_summary_atlas_truth_unverified")
    migrated = copy.deepcopy(atlas)
    migrated["agent_recommendations"] = recommendations
    source_contract = migrated.setdefault("source_contract", {})
    if not isinstance(source_contract, dict):
        raise CodexLegacySummaryError("codex_legacy_summary_atlas_contract_invalid")
    source_contract["codex_legacy_summary_compatibility"] = build_summary_semantics(
        "atlas_legacy_summary_compatibility", canonical_truth
    )
    source_files = source_contract.setdefault("source_files", {})
    if not isinstance(source_files, dict):
        raise CodexLegacySummaryError("codex_legacy_summary_atlas_contract_invalid")
    source_files["codex_legacy_summary_contract"] = CONTRACT_PATH.as_posix()
    for source in migrated.get("data_sources", []):
        if isinstance(source, dict) and source.get("id") == SOURCE_ID:
            source.update(
                {
                    "description": (
                        "已验证 Codex raw archives 生成 canonical events/facets；"
                        "旧 snapshot/recommendations 仅作为兼容脱敏摘要读取，不是 full raw backup。"
                    ),
                    "platform": "codex_verified_archive_derived",
                    "ingestion_status": "active_verified_archive_derived_with_legacy_summary_compat",
                    "record_types": [
                        "canonical_codex_event",
                        "canonical_codex_facet",
                        "legacy_redacted_summary_read_only",
                    ],
                }
            )
    publication = migrated.get("codex_publication")
    if isinstance(publication, dict):
        publication["legacy_summary_compatibility"] = {
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "state_ref": STATE_PATH.as_posix(),
            "output_policy": "derived_summary_not_full_raw_backup",
            "full_raw_backup": False,
        }
    migrated_bytes = _json_bytes(migrated)
    next_atlas_state = copy.deepcopy(atlas_state)
    next_atlas_state["outputs"]["atlas_snapshot"] = {
        "path": atlas_relative,
        "sha256": _sha256(migrated_bytes),
        "byte_size": len(migrated_bytes),
    }
    return migrated_bytes, next_atlas_state, atlas_state_bytes


def _migrate_agent_context(
    database_dir: Path,
    canonical_truth: dict[str, Any],
) -> tuple[bytes, bytes]:
    context, _ = _load_json(
        database_dir,
        CONSUMER_OUTPUTS["agent_context_json"],
        "codex_legacy_summary_agent_context_invalid",
    )
    _read_regular_bytes(database_dir, CONSUMER_OUTPUTS["agent_context_markdown"])
    from build_agent_context_pack import build_agent_context_pack, markdown_lines

    migrated = build_agent_context_pack(database_dir)
    for key, value in context.items():
        migrated.setdefault(key, copy.deepcopy(value))
    source_files = migrated.get("source_files")
    behavior = migrated.get("behavior")
    safety = migrated.get("safety")
    if not all(isinstance(section, dict) for section in (source_files, behavior, safety)):
        raise CodexLegacySummaryError("codex_legacy_summary_agent_context_invalid")
    source_files["codex_legacy_summary_contract"] = CONTRACT_PATH.as_posix()
    behavior["summary_semantics"] = build_summary_semantics(
        "processed_activity_snapshot", canonical_truth
    )
    safety.update(
        {
            "full_raw_backup": False,
            "recoverable_raw_backup": False,
            "canonical_raw_archive_ref": RAW_ARCHIVE_ROOT.as_posix(),
            "legacy_codex_summary_role": "redacted_derived_summary_read_only",
        }
    )
    return _json_bytes(migrated), "\n".join(markdown_lines(migrated)).encode("utf-8")


def _output_records(payloads: dict[str, bytes]) -> dict[str, dict[str, Any]]:
    return {
        relative: {"sha256": _sha256(payload), "byte_size": len(payload)}
        for relative, payload in sorted(payloads.items())
    }


def _state_is_current(
    database_dir: Path,
    state: dict[str, Any],
    *,
    contract_sha256: str,
    model_sha256: str,
    canonical_hashes: dict[str, str],
) -> bool:
    if (
        state.get("schema_version") != STATE_SCHEMA_VERSION
        or state.get("task_id") != TASK_ID
        or state.get("acceptance_id") != ACCEPTANCE_ID
        or state.get("source_id") != SOURCE_ID
        or state.get("contract_sha256") != contract_sha256
        or state.get("model_parameters_sha256") != model_sha256
        or state.get("canonical_input_hashes") != canonical_hashes
        or state.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
        or not isinstance(state.get("migrated_at"), str)
        or not state["migrated_at"]
    ):
        return False
    output_hashes = state.get("output_hashes")
    if not isinstance(output_hashes, dict) or not output_hashes:
        return False
    for relative, record in output_hashes.items():
        if not isinstance(record, dict):
            return False
        try:
            payload = _read_regular_bytes(database_dir, relative, max_bytes=_MAX_JSONL_BYTES)
        except CodexLegacySummaryError:
            return False
        if record.get("sha256") != _sha256(payload) or record.get("byte_size") != len(payload):
            return False
    return True


@contextmanager
def _migration_lock(database_dir: Path) -> Iterator[None]:
    identity = hashlib.sha256(str(database_dir).encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"memory-atlas-codex-legacy-{identity}.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CodexLegacySummaryError("codex_legacy_summary_lock_busy") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def migrate_codex_legacy_summary(
    database_dir: Path,
    *,
    dry_run: bool = False,
    migrated_at: str | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    with _migration_lock(database_dir):
        load_codex_legacy_summary_contract(database_dir)
        contract_bytes = _read_regular_bytes(database_dir, CONTRACT_PATH.as_posix())
        model_bytes = _read_regular_bytes(database_dir, MODEL_PARAMETERS_PATH.as_posix())
        contract_sha256 = _sha256(contract_bytes)
        model_sha256 = _sha256(model_bytes)
        canonical_truth, canonical_hashes = _canonical_truth(database_dir)
        existing_state: dict[str, Any] = {}
        if os.path.lexists(database_dir / STATE_PATH):
            existing_state, _ = _load_json(
                database_dir, STATE_PATH.as_posix(), "codex_legacy_summary_state_invalid"
            )
        if _state_is_current(
            database_dir,
            existing_state,
            contract_sha256=contract_sha256,
            model_sha256=model_sha256,
            canonical_hashes=canonical_hashes,
        ):
            return {
                "schema_version": STATE_SCHEMA_VERSION,
                "status": "PASS",
                "outcome": "NO_CHANGES",
                "dry_run": dry_run,
                "writes_files": False,
                "changed_paths": [],
                "legacy_counts": existing_state.get("legacy_counts"),
                "raw_mutation": False,
                "remote_push": False,
                "phase_boundary": EXPECTED_PHASE_BOUNDARY,
            }

        payloads, recommendations, legacy_counts = _migrated_legacy_payloads(
            database_dir, canonical_truth
        )
        atlas_bytes, atlas_state, _old_atlas_state_bytes = _migrate_atlas(
            database_dir, recommendations, canonical_truth
        )
        context_json, context_markdown = _migrate_agent_context(
            database_dir, canonical_truth
        )
        payloads.update(
            {
                CONSUMER_OUTPUTS["atlas_snapshot"]: atlas_bytes,
                ATLAS_STATE_PATH.as_posix(): _json_bytes(atlas_state),
                CONSUMER_OUTPUTS["agent_context_json"]: context_json,
                CONSUMER_OUTPUTS["agent_context_markdown"]: context_markdown,
            }
        )
        migration_time = (
            str(existing_state.get("migrated_at") or "")
            or migrated_at
            or datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
        )
        state = {
            "schema_version": STATE_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "source_id": SOURCE_ID,
            "state_path": STATE_PATH.as_posix(),
            "contract_ref": CONTRACT_PATH.as_posix(),
            "contract_sha256": contract_sha256,
            "model_parameters_ref": MODEL_PARAMETERS_PATH.as_posix(),
            "model_parameters_sha256": model_sha256,
            "migrated_at": migration_time,
            "canonical_input_hashes": canonical_hashes,
            "canonical_truth": canonical_truth,
            "legacy_counts": legacy_counts,
            "output_hashes": _output_records(payloads),
            "last_result": {
                "outcome": "MIGRATED_LEGACY_REDACTED_SUMMARY_SEMANTICS",
                "compatibility_preserved": True,
                "full_raw_backup": False,
                "raw_mutation": False,
            },
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }
        payloads[STATE_PATH.as_posix()] = _json_bytes(state)
        changed = [
            relative
            for relative, payload in payloads.items()
            if not (database_dir / relative).is_file()
            or (database_dir / relative).read_bytes() != payload
        ]
        if not dry_run:
            changed = _write_bundle(database_dir, payloads)
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "status": "PASS",
            "outcome": (
                "WOULD_MIGRATE_LEGACY_REDACTED_SUMMARY_SEMANTICS"
                if dry_run
                else "MIGRATED_LEGACY_REDACTED_SUMMARY_SEMANTICS"
            ),
            "dry_run": dry_run,
            "writes_files": bool(changed) and not dry_run,
            "would_write_files": bool(changed) if dry_run else False,
            "changed_paths": changed,
            "legacy_counts": legacy_counts,
            "canonical_truth": canonical_truth,
            "raw_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }


def run_codex_legacy_summary(args: argparse.Namespace) -> int:
    try:
        result = migrate_codex_legacy_summary(
            Path(args.database_dir), dry_run=bool(getattr(args, "dry_run", False))
        )
    except CodexLegacySummaryError as exc:
        print(
            json.dumps(
                {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "status": "FAIL",
                    "error_code": exc.code,
                    "writes_files": False,
                    "raw_mutation": False,
                    "remote_push": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = (
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "EXPECTED_PHASE_BOUNDARY",
    "LEGACY_OUTPUTS",
    "MODEL_PARAMETERS_PATH",
    "SEMANTICS_SCHEMA_VERSION",
    "STATE_PATH",
    "TASK_ID",
    "CodexLegacySummaryError",
    "build_summary_semantics",
    "load_codex_legacy_summary_contract",
    "migrate_codex_legacy_summary",
    "normalize_legacy_summary_payload",
    "run_codex_legacy_summary",
)
