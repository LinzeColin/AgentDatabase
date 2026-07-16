"""Publish canonical Codex derived data into the local Memory Atlas surfaces."""

from __future__ import annotations

import argparse
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

from build_memory_atlas_data import build_memory_atlas
from build_memory_atlas_weekly_report import (
    MAX_SECTION_ITEMS,
    build_weekly_report_payload,
)
from privacy_guard import LOCAL_ABSOLUTE_PATH_RE, credential_exclusion_hits

from .codex_derived import (
    CONTRACT_PATH as DERIVED_CONTRACT_PATH,
    EXPECTED_OUTPUTS as DERIVED_OUTPUTS,
    EXPECTED_PHASE_BOUNDARY as DERIVED_PHASE_BOUNDARY,
    MODEL_PARAMETERS_PATH as DERIVED_MODEL_PARAMETERS_PATH,
    STATE_SCHEMA_VERSION as DERIVED_STATE_SCHEMA_VERSION,
    load_codex_derived_contract,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("config/data_sources/codex_atlas_publication.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_atlas_publication.v1_2_1_s07_p2_t2.json"
)
STATE_PATH = Path("data/sync_state/codex_atlas.json")
SNAPSHOT_PATH = Path("data/derived/visualization/memory_atlas.json")
WEEKLY_OUTPUT_DIR = Path("data/derived/weekly")
SCHEMA_VERSION = "memory_atlas.codex_atlas_publication_contract.v1_2_1_s07_p2_t2"
MODEL_PARAMETERS_SCHEMA_VERSION = (
    "memory_atlas.codex_atlas_publication_model.v1_2_1_s07_p2_t2"
)
STATE_SCHEMA_VERSION = "memory_atlas.codex_atlas_publication_state.v1_2_1_s07_p2_t2"
SNAPSHOT_PUBLICATION_SCHEMA_VERSION = (
    "memory_atlas.codex_atlas_publication.v1_2_1_s07_p2_t2"
)
TASK_ID = "S07-P2-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P2-T2"
SOURCE_ID = "codex"
MAX_CONTROL_BYTES = 16 * 1024 * 1024
MAX_JSONL_BYTES = 64 * 1024 * 1024

EXPECTED_PHASE_BOUNDARY = {
    "does_not_modify_raw": True,
    "does_not_regenerate_legacy_consumers": True,
    "atlas_snapshot_updated": True,
    "weekly_report_updated": True,
    "sync_status_updated": True,
    "ui_code_updated_only_for_discoverability": True,
    "does_not_commit_or_push": True,
    "does_not_deploy": True,
    "next_task": "S07-P2-T3",
}
EXPECTED_CONTRACT = {
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "inputs": {
        "derived_contract_ref": DERIVED_CONTRACT_PATH.as_posix(),
        "derived_state_ref": DERIVED_OUTPUTS["state"],
        "events_ref": DERIVED_OUTPUTS["events"],
        "facets_ref": DERIVED_OUTPUTS["facets"],
        "behavior_summary_ref": DERIVED_OUTPUTS["behavior_summary"],
        "canonical_t1_required": True,
        "verified_output_hashes_required": True,
    },
    "outputs": {
        "atlas_snapshot": SNAPSHOT_PATH.as_posix(),
        "weekly_output_dir": WEEKLY_OUTPUT_DIR.as_posix(),
        "sync_state": STATE_PATH.as_posix(),
    },
    "publication": {
        "session_identity": "event_id",
        "latest_session_order": ["updated_at", "source_relative_path"],
        "exact_repeat_no_write": True,
        "snapshot_and_report_hash_bound_in_state": True,
        "latest_session_must_be_ui_searchable": True,
        "latest_session_must_have_archive_evidence": True,
        "legacy_recommendation_timestamp_policy": "preserve_source_generated_at",
    },
    "privacy": {
        "frontend_reads_raw": False,
        "raw_message_text_persisted": False,
        "plaintext_credentials_allowed": False,
        "local_absolute_paths_allowed": False,
        "source_policy": "verified_recoverable_sanitized_raw_archive_derived_only",
    },
    "model_parameters_ref": MODEL_PARAMETERS_PATH.as_posix(),
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}
EXPECTED_MODEL_PARAMETERS = {
    "schema_version": MODEL_PARAMETERS_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-008",
    "formula_id": "FORM-008",
    "purpose": (
        "Publish canonical Codex events and facets into the redacted Atlas "
        "snapshot, weekly report and independent publication state."
    ),
    "latest_session_order": ["updated_at", "source_relative_path"],
    "ui_discoverability": {
        "required_search_fields": ["public_label", "statement", "source_record_id"],
        "minimum_evidence_ref_count": 1,
        "maximum_public_session_nodes": 1000,
    },
    "weekly_report": {
        "section_item_limit": 25,
        "latest_session_summary_required": True,
    },
    "calibration_boundary": (
        "Publication parameters are deterministic safety and display bounds, not "
        "a claim of business-optimal ranking or model calibration."
    ),
}


class CodexAtlasError(ValueError):
    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(f"{code}: {message}" if message else code)
        self.code = code


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _same_stat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _safe_relative(value: str) -> Path:
    path = PurePosixPath(value)
    if path.is_absolute() or not path.parts or ".." in path.parts:
        raise CodexAtlasError("codex_atlas_path_invalid")
    return Path(*path.parts)


def _assert_safe_parents(database_dir: Path, path: Path) -> None:
    current = database_dir
    relative = path.relative_to(database_dir)
    for part in relative.parts[:-1]:
        current /= part
        if os.path.lexists(current):
            metadata = current.lstat()
            if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
                raise CodexAtlasError("codex_atlas_output_parent_unsafe")


def _read_regular_bytes(
    database_dir: Path,
    relative: str,
    *,
    max_bytes: int = MAX_CONTROL_BYTES,
) -> bytes:
    path = database_dir / _safe_relative(relative)
    _assert_safe_parents(database_dir, path)
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CodexAtlasError("codex_atlas_input_unreadable", relative) from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        raise CodexAtlasError("codex_atlas_input_unsafe", relative)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise CodexAtlasError("codex_atlas_input_unreadable", relative) from exc
    if not _same_stat(path.lstat(), metadata):
        raise CodexAtlasError("codex_atlas_input_changed", relative)
    return payload


def _load_json(database_dir: Path, relative: str) -> dict[str, Any]:
    try:
        payload = json.loads(_read_regular_bytes(database_dir, relative).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAtlasError("codex_atlas_json_invalid", relative) from exc
    if not isinstance(payload, dict):
        raise CodexAtlasError("codex_atlas_json_not_object", relative)
    return payload


def _load_jsonl(database_dir: Path, relative: str) -> tuple[list[dict[str, Any]], bytes]:
    payload = _read_regular_bytes(database_dir, relative, max_bytes=MAX_JSONL_BYTES)
    rows: list[dict[str, Any]] = []
    try:
        for line in payload.decode("utf-8").splitlines():
            if not line.strip():
                continue
            row = json.loads(line)
            if not isinstance(row, dict):
                raise CodexAtlasError("codex_atlas_jsonl_row_invalid", relative)
            rows.append(row)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAtlasError("codex_atlas_jsonl_invalid", relative) from exc
    return rows, payload


def load_codex_atlas_contract(database_dir: Path = PACKAGE_ROOT) -> dict[str, Any]:
    payload = _load_json(database_dir.resolve(), CONTRACT_PATH.as_posix())
    if payload != EXPECTED_CONTRACT:
        raise CodexAtlasError("codex_atlas_contract_drift")
    model = _load_json(database_dir.resolve(), MODEL_PARAMETERS_PATH.as_posix())
    if model != EXPECTED_MODEL_PARAMETERS:
        raise CodexAtlasError("codex_atlas_model_parameters_drift")
    if model["weekly_report"]["section_item_limit"] != MAX_SECTION_ITEMS:
        raise CodexAtlasError("codex_atlas_weekly_limit_drift")
    return payload


def _verified_derived_inputs(
    database_dir: Path,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any], str]:
    derived_contract = load_codex_derived_contract(database_dir)
    state_bytes = _read_regular_bytes(database_dir, DERIVED_OUTPUTS["state"])
    try:
        state = json.loads(state_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAtlasError("codex_atlas_derived_state_invalid") from exc
    if (
        not isinstance(state, dict)
        or state.get("schema_version") != DERIVED_STATE_SCHEMA_VERSION
        or state.get("task_id") != "S07-P2-T1"
        or state.get("phase_boundary") != DERIVED_PHASE_BOUNDARY
    ):
        raise CodexAtlasError("codex_atlas_derived_state_identity_invalid")
    if state.get("contract_sha256") != _sha256(_json_bytes(derived_contract)):
        raise CodexAtlasError("codex_atlas_derived_contract_hash_mismatch")
    derived_model = _load_json(database_dir, DERIVED_MODEL_PARAMETERS_PATH.as_posix())
    if state.get("model_parameters_sha256") != _sha256(_json_bytes(derived_model)):
        raise CodexAtlasError("codex_atlas_derived_model_hash_mismatch")

    output_hashes = state.get("output_hashes")
    if not isinstance(output_hashes, dict):
        raise CodexAtlasError("codex_atlas_derived_hashes_invalid")
    verified_bytes: dict[str, bytes] = {}
    for key in ("events", "facets", "behavior_summary", "universe_state_input"):
        relative = DERIVED_OUTPUTS[key]
        payload = _read_regular_bytes(
            database_dir,
            relative,
            max_bytes=MAX_JSONL_BYTES if key in {"events", "facets"} else MAX_CONTROL_BYTES,
        )
        expected = output_hashes.get(relative)
        if (
            not isinstance(expected, dict)
            or expected.get("sha256") != _sha256(payload)
            or expected.get("byte_size") != len(payload)
        ):
            raise CodexAtlasError("codex_atlas_derived_output_hash_mismatch", relative)
        verified_bytes[relative] = payload

    events, events_bytes = _load_jsonl(database_dir, DERIVED_OUTPUTS["events"])
    facets, facets_bytes = _load_jsonl(database_dir, DERIVED_OUTPUTS["facets"])
    if events_bytes != verified_bytes[DERIVED_OUTPUTS["events"]] or facets_bytes != verified_bytes[DERIVED_OUTPUTS["facets"]]:
        raise CodexAtlasError("codex_atlas_derived_input_changed")
    try:
        behavior = json.loads(
            verified_bytes[DERIVED_OUTPUTS["behavior_summary"]].decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexAtlasError("codex_atlas_behavior_summary_invalid") from exc
    if (
        not isinstance(behavior, dict)
        or len(events) != state.get("event_count")
        or len(facets) != state.get("facet_count")
        or behavior.get("session_count") != len(events)
        or behavior.get("facet_count") != len(facets)
        or behavior.get("source_truth", {}).get("full_raw_backup") is not False
    ):
        raise CodexAtlasError("codex_atlas_derived_count_or_truth_mismatch")
    event_ids = [str(row.get("event_id") or "") for row in events]
    facet_ids = [str(row.get("event_id") or "") for row in facets]
    if (
        not events
        or any(not event_id for event_id in event_ids)
        or len(set(event_ids)) != len(event_ids)
        or set(event_ids) != set(facet_ids)
    ):
        raise CodexAtlasError("codex_atlas_event_facet_identity_mismatch")
    return state, events, facets, behavior, _sha256(state_bytes)


def _latest_event(events: list[dict[str, Any]]) -> dict[str, Any]:
    return max(
        events,
        key=lambda row: (
            str(row.get("updated_at") or row.get("started_at") or ""),
            str(row.get("source_relative_path") or ""),
        ),
    )


def _latest_publication(
    latest: dict[str, Any],
    facet: dict[str, Any],
    *,
    state_ref: str,
) -> dict[str, Any]:
    session_id = str(latest.get("session_id") or latest.get("record_id") or "")
    event_id = str(latest.get("event_id") or "")
    thread_name = str(latest.get("thread_name") or session_id).strip()
    return {
        "session_id": session_id,
        "event_id": event_id,
        "node_id": f"memory:{event_id}",
        "thread_name": thread_name,
        "updated_at": str(latest.get("updated_at") or latest.get("started_at") or ""),
        "ui_query": thread_name,
        "evidence_ref_count": len(facet.get("evidence_refs") or []),
        "state_ref": state_ref,
        "explanation_zh": (
            "页面展示会话名、时间、消息/工具统计、主题、来源和已验证归档证据；"
            "不展示 raw transcript、明文凭据或本机绝对路径。"
        ),
    }


def _inject_publication(
    atlas: dict[str, Any],
    *,
    derived_state_sha256: str,
    events: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    behavior: dict[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    latest = _latest_event(events)
    facets_by_event = {str(row.get("event_id") or ""): row for row in facets}
    facet = facets_by_event.get(str(latest.get("event_id") or ""), {})
    latest_publication = _latest_publication(
        latest,
        facet,
        state_ref=STATE_PATH.as_posix(),
    )
    codex_session_nodes = [
        node
        for node in atlas.get("nodes", [])
        if isinstance(node, dict)
        and node.get("data_source") == "codex"
        and str(node.get("source_event_id") or "")
    ]
    if len(codex_session_nodes) != len(events):
        raise CodexAtlasError("codex_atlas_session_node_count_mismatch")
    if len(codex_session_nodes) > EXPECTED_MODEL_PARAMETERS["ui_discoverability"]["maximum_public_session_nodes"]:
        raise CodexAtlasError("codex_atlas_session_node_limit_exceeded")
    latest_node = next(
        (node for node in codex_session_nodes if node.get("id") == latest_publication["node_id"]),
        None,
    )
    if not isinstance(latest_node, dict):
        raise CodexAtlasError("codex_atlas_latest_session_missing")
    searchable = " ".join(
        str(latest_node.get(field) or "")
        for field in ("label", "statement", "source_record_id")
    )
    if latest_publication["thread_name"] not in searchable:
        raise CodexAtlasError("codex_atlas_latest_session_not_searchable")
    if len(latest_node.get("evidence_refs") or []) < EXPECTED_MODEL_PARAMETERS["ui_discoverability"]["minimum_evidence_ref_count"]:
        raise CodexAtlasError("codex_atlas_latest_session_evidence_missing")

    for source in atlas.get("data_sources", []):
        if not isinstance(source, dict) or source.get("id") != "codex":
            continue
        source.update(
            {
                "description": (
                    "已验证 Codex 归档生成的 canonical session events/facets；"
                    "兼容 recommendation 摘要保持只读，语义迁移留给 S07-P2-T3。"
                ),
                "platform": "codex_verified_archive_derived",
                "status": "active",
                "ingestion_status": "active_verified_archive_derived_published",
                "record_types": [
                    "canonical_codex_event",
                    "canonical_codex_facet",
                    "legacy_agent_recommendation_read_only",
                ],
                "activity_count": len(events),
                "latest_date": str(latest.get("updated_day") or latest.get("day") or ""),
            }
        )
    publication = {
        "schema_version": SNAPSHOT_PUBLICATION_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "status": "CURRENT_LOCAL",
        "state_ref": STATE_PATH.as_posix(),
        "derived_state_ref": DERIVED_OUTPUTS["state"],
        "derived_state_sha256": derived_state_sha256,
        "counts": {
            "archive_count": int(behavior.get("archive_count") or 0),
            "event_count": len(events),
            "facet_count": len(facets),
            "atlas_codex_node_count": len(codex_session_nodes),
            "message_count": int(behavior.get("message_count") or 0),
            "tool_call_count": int(behavior.get("tool_call_count") or 0),
        },
        "latest_session": latest_publication,
        "privacy": {
            "raw_private_data_included": False,
            "raw_message_text_included": False,
            "plaintext_credentials_included": False,
            "local_absolute_paths_included": False,
        },
    }
    atlas["codex_publication"] = publication
    return atlas, latest_publication


def _validate_public_payloads(payloads: dict[str, bytes]) -> None:
    for relative, payload in payloads.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CodexAtlasError("codex_atlas_output_not_utf8", relative) from exc
        if LOCAL_ABSOLUTE_PATH_RE.search(text):
            raise CodexAtlasError("codex_atlas_output_absolute_path", relative)
        if credential_exclusion_hits(text, source=relative):
            raise CodexAtlasError("codex_atlas_output_credential", relative)


def _state_is_current(
    database_dir: Path,
    state: dict[str, Any],
    *,
    contract_sha256: str,
    model_sha256: str,
    derived_state_sha256: str,
    derived_state: dict[str, Any],
    events: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    behavior: dict[str, Any],
) -> bool:
    facets_by_event = {str(row.get("event_id") or ""): row for row in facets}
    latest = _latest_event(events)
    expected_latest = _latest_publication(
        latest,
        facets_by_event.get(str(latest.get("event_id") or ""), {}),
        state_ref=STATE_PATH.as_posix(),
    )
    expected_counts = {
        "event_count": len(events),
        "facet_count": len(facets),
        "archive_count": int(behavior.get("archive_count") or 0),
        "message_count": int(behavior.get("message_count") or 0),
        "tool_call_count": int(behavior.get("tool_call_count") or 0),
    }
    expected_last_result = {
        "outcome": "PUBLISHED_CANONICAL_CODEX_ATLAS",
        "atlas_snapshot_updated": True,
        "weekly_report_updated": True,
        "sync_status_updated": True,
        "ui_discoverability_verified": True,
    }
    if (
        state.get("schema_version") != STATE_SCHEMA_VERSION
        or state.get("task_id") != TASK_ID
        or state.get("acceptance_id") != ACCEPTANCE_ID
        or state.get("source_id") != SOURCE_ID
        or state.get("state_path") != STATE_PATH.as_posix()
        or state.get("contract_ref") != CONTRACT_PATH.as_posix()
        or state.get("model_parameters_ref") != MODEL_PARAMETERS_PATH.as_posix()
        or state.get("derived_state_ref") != DERIVED_OUTPUTS["state"]
        or state.get("contract_sha256") != contract_sha256
        or state.get("model_parameters_sha256") != model_sha256
        or state.get("derived_state_sha256") != derived_state_sha256
        or state.get("input_archives") != derived_state.get("input_archives", [])
        or state.get("counts") != expected_counts
        or state.get("latest_session") != expected_latest
        or state.get("last_result") != expected_last_result
        or state.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
        or not isinstance(state.get("published_at"), str)
        or not state["published_at"]
    ):
        return False
    outputs = state.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != {"atlas_snapshot", "weekly_report"}:
        return False
    output_payloads: dict[str, bytes] = {}
    for output_name, record in outputs.items():
        if not isinstance(record, dict) or not isinstance(record.get("path"), str):
            return False
        if output_name == "atlas_snapshot" and record["path"] != SNAPSHOT_PATH.as_posix():
            return False
        if output_name == "weekly_report":
            weekly_path = PurePosixPath(record["path"])
            if (
                weekly_path.parent.as_posix() != WEEKLY_OUTPUT_DIR.as_posix()
                or not weekly_path.name.endswith(".memory_atlas_weekly_report.md")
            ):
                return False
        try:
            payload = _read_regular_bytes(database_dir, record["path"], max_bytes=MAX_JSONL_BYTES)
        except CodexAtlasError:
            return False
        if record.get("sha256") != _sha256(payload) or record.get("byte_size") != len(payload):
            return False
        output_payloads[output_name] = payload
    try:
        snapshot = json.loads(output_payloads["atlas_snapshot"].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return False
    publication = snapshot.get("codex_publication") if isinstance(snapshot, dict) else None
    overview = snapshot.get("overview") if isinstance(snapshot, dict) else None
    if (
        not isinstance(overview, dict)
        or overview.get("generated_at") != state["published_at"]
        or not isinstance(publication, dict)
        or publication.get("derived_state_sha256") != derived_state_sha256
        or publication.get("latest_session") != expected_latest
        or publication.get("counts", {}).get("event_count") != len(events)
        or publication.get("counts", {}).get("facet_count") != len(facets)
    ):
        return False
    return True


def _load_existing_state(database_dir: Path) -> dict[str, Any] | None:
    path = database_dir / STATE_PATH
    if not os.path.lexists(path):
        return None
    return _load_json(database_dir, STATE_PATH.as_posix())


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
            path = database_dir / _safe_relative(relative)
            _assert_safe_parents(database_dir, path)
            if os.path.lexists(path):
                metadata = path.lstat()
                if not stat.S_ISREG(metadata.st_mode):
                    raise CodexAtlasError("codex_atlas_output_target_unsafe", relative)
                current = path.read_bytes()
                if current == payload:
                    continue
                originals[relative] = current
            else:
                originals[relative] = None
            path.parent.mkdir(parents=True, exist_ok=True)
            descriptor, temp_name = tempfile.mkstemp(
                prefix=f".{path.name}.", suffix=".tmp", dir=path.parent
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


@contextmanager
def _publication_lock(database_dir: Path) -> Iterator[None]:
    identity = hashlib.sha256(str(database_dir).encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"memory-atlas-codex-atlas-{identity}.lock"
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CodexAtlasError("codex_atlas_lock_busy") from exc
        yield
    finally:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _publish_locked(
    database_dir: Path,
    *,
    dry_run: bool,
    published_at: str | None,
) -> dict[str, Any]:
    load_codex_atlas_contract(database_dir)
    derived_state, events, facets, behavior, derived_state_sha256 = _verified_derived_inputs(database_dir)
    contract_sha256 = _sha256(_read_regular_bytes(database_dir, CONTRACT_PATH.as_posix()))
    model_sha256 = _sha256(_read_regular_bytes(database_dir, MODEL_PARAMETERS_PATH.as_posix()))
    existing_state = _load_existing_state(database_dir)
    if existing_state is not None and _state_is_current(
        database_dir,
        existing_state,
        contract_sha256=contract_sha256,
        model_sha256=model_sha256,
        derived_state_sha256=derived_state_sha256,
        derived_state=derived_state,
        events=events,
        facets=facets,
        behavior=behavior,
    ):
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "status": "PASS",
            "outcome": "NO_CHANGES",
            "dry_run": dry_run,
            "writes_files": False,
            "changed_paths": [],
            "event_count": len(events),
            "facet_count": len(facets),
            "latest_session": existing_state.get("latest_session"),
            "outputs": existing_state.get("outputs"),
            "raw_mutation": False,
            "legacy_consumer_mutation": False,
            "remote_push": False,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }

    publication_time = published_at or datetime.now(timezone.utc).isoformat(
        timespec="seconds"
    ).replace("+00:00", "Z")
    atlas = build_memory_atlas(database_dir, generated_at=publication_time)
    atlas, latest_publication = _inject_publication(
        atlas,
        derived_state_sha256=derived_state_sha256,
        events=events,
        facets=facets,
        behavior=behavior,
    )
    snapshot_bytes = _json_bytes(atlas)
    weekly = build_weekly_report_payload(atlas)
    weekly_path = str(weekly["output"])
    weekly_bytes = (str(weekly["content"]) + ("" if str(weekly["content"]).endswith("\n") else "\n")).encode("utf-8")
    output_records = {
        "atlas_snapshot": {
            "path": SNAPSHOT_PATH.as_posix(),
            "sha256": _sha256(snapshot_bytes),
            "byte_size": len(snapshot_bytes),
        },
        "weekly_report": {
            "path": weekly_path,
            "sha256": _sha256(weekly_bytes),
            "byte_size": len(weekly_bytes),
        },
    }
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
        "derived_state_ref": DERIVED_OUTPUTS["state"],
        "derived_state_sha256": derived_state_sha256,
        "published_at": publication_time,
        "input_archives": derived_state.get("input_archives", []),
        "counts": {
            "event_count": len(events),
            "facet_count": len(facets),
            "archive_count": int(behavior.get("archive_count") or 0),
            "message_count": int(behavior.get("message_count") or 0),
            "tool_call_count": int(behavior.get("tool_call_count") or 0),
        },
        "latest_session": latest_publication,
        "outputs": output_records,
        "last_result": {
            "outcome": "PUBLISHED_CANONICAL_CODEX_ATLAS",
            "atlas_snapshot_updated": True,
            "weekly_report_updated": True,
            "sync_status_updated": True,
            "ui_discoverability_verified": True,
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    state_bytes = _json_bytes(state)
    payloads = {
        SNAPSHOT_PATH.as_posix(): snapshot_bytes,
        weekly_path: weekly_bytes,
        STATE_PATH.as_posix(): state_bytes,
    }
    _validate_public_payloads(payloads)
    if dry_run:
        changed = [
            relative
            for relative, payload in payloads.items()
            if not (database_dir / relative).is_file()
            or (database_dir / relative).read_bytes() != payload
        ]
    else:
        changed = _write_bundle(database_dir, payloads)
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": "PASS",
        "outcome": "WOULD_PUBLISH_CANONICAL_CODEX_ATLAS" if dry_run else "PUBLISHED_CANONICAL_CODEX_ATLAS",
        "dry_run": dry_run,
        "writes_files": bool(changed) and not dry_run,
        "would_write_files": bool(changed) if dry_run else False,
        "changed_paths": changed,
        "event_count": len(events),
        "facet_count": len(facets),
        "latest_session": latest_publication,
        "outputs": output_records,
        "raw_mutation": False,
        "legacy_consumer_mutation": False,
        "remote_push": False,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def publish_codex_atlas(
    database_dir: Path,
    *,
    dry_run: bool = False,
    published_at: str | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    with _publication_lock(database_dir):
        return _publish_locked(
            database_dir,
            dry_run=dry_run,
            published_at=published_at,
        )


def run_codex_atlas(args: argparse.Namespace) -> int:
    try:
        result = publish_codex_atlas(
            Path(args.database_dir),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    except CodexAtlasError as exc:
        print(
            json.dumps(
                {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "status": "FAIL",
                    "error_code": exc.code,
                    "reason": str(exc),
                    "writes_files": False,
                    "raw_mutation": False,
                    "legacy_consumer_mutation": False,
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
    "MODEL_PARAMETERS_PATH",
    "STATE_PATH",
    "TASK_ID",
    "CodexAtlasError",
    "load_codex_atlas_contract",
    "publish_codex_atlas",
    "run_codex_atlas",
)
