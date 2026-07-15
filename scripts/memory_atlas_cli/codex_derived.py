"""Build traceable Codex derived outputs from immutable registered raw archives."""

from __future__ import annotations

import argparse
import fcntl
import hashlib
import json
import math
import os
import re
import stat
import tarfile
import tempfile
from collections import Counter, defaultdict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any, BinaryIO, Iterable, Iterator

from privacy_guard import LOCAL_ABSOLUTE_PATH_RE, credential_exclusion_hits

from memory_atlas_cli.codex_public_raw_archive import (
    CodexPublicRawArchiveError,
    verify_codex_public_raw_archive,
)
from memory_atlas_cli.codex_sync_state import (
    CodexSyncStateError,
    verify_codex_incremental_archive,
)
from sync_codex_memory_data import (
    SIGNAL_RULES,
    TOPIC_RULES,
    extract_message_text,
    parse_time,
    redact_text,
    update_rules,
)


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("config/data_sources/codex_derived.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json"
)
SCHEMA_VERSION = "memory_atlas.codex_derived_contract.v1_2_1_s07_p2_t1"
MODEL_PARAMETERS_SCHEMA_VERSION = (
    "memory_atlas.codex_derived_model.v1_2_1_s07_p2_t1"
)
STATE_SCHEMA_VERSION = "memory_atlas.codex_derived_state.v1_2_1_s07_p2_t1"
EVENT_SCHEMA_VERSION = "memory_atlas.codex_derived_event.v1_2_1_s07_p2_t1"
FACET_SCHEMA_VERSION = "memory_atlas.codex_derived_facet.v1_2_1_s07_p2_t1"
BEHAVIOR_SCHEMA_VERSION = "memory_atlas.codex_behavior_summary.v1_2_1_s07_p2_t1"
TASK_ID = "S07-P2-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P2-T1"
SOURCE_ID = "codex"
PUBLIC_INDEX_ROOT = Path("data/public_raw/codex")
ARCHIVE_ROOT = Path("data/raw_archives/codex")
RAW_LEDGER_CONTRACT = Path("config/data_sources/raw_ledger.json")
SOURCE_MANIFEST_MEMBER = "codex/_memory_atlas/source_manifest.json"
MODEL_PARAMETERS_REF = MODEL_PARAMETERS_PATH.as_posix()
T2_INDEX_SCHEMA = "memory_atlas.codex_public_raw_archive_index.v1_2_1_s07_p1_t2"
T3_INDEX_SCHEMA = "memory_atlas.codex_incremental_archive_index.v1_2_1_s07_p1_t3"
ELIGIBLE_SOURCE_KINDS = ("active_sessions", "archived_sessions")
READ_CHUNK_BYTES = 1024 * 1024
MAX_CONTROL_BYTES = 16 * 1024 * 1024

EXPECTED_OUTPUTS = {
    "events": "data/derived/codex/codex_events.jsonl",
    "facets": "data/derived/codex/codex_facets.jsonl",
    "behavior_summary": "data/derived/codex/codex_behavior_summary.json",
    "universe_state_input": "data/derived/codex/codex_universe_state_input.json",
    "state": "data/derived/codex/codex_derived_state.json",
}
EXPECTED_PHASE_BOUNDARY = {
    "does_not_modify_raw": True,
    "does_not_update_atlas_snapshot": True,
    "does_not_update_weekly_report": True,
    "does_not_update_sync_state": True,
    "does_not_update_ui": True,
    "does_not_commit_or_push": True,
    "does_not_deploy": True,
    "next_task": "S07-P2-T2",
}
REQUIRED_PROVENANCE_REFS = [
    "public_index_ref",
    "archive_manifest_ref",
    "archive_manifest_sha256",
    "source_manifest_member",
    "archive_member",
    "archive_member_sha256",
    "source_relative_path",
    "source_sha256",
]
EXPECTED_CONTRACT = {
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "inputs": {
        "public_index_root": PUBLIC_INDEX_ROOT.as_posix(),
        "archive_root": ARCHIVE_ROOT.as_posix(),
        "raw_ledger_contract_ref": RAW_LEDGER_CONTRACT.as_posix(),
        "registration_patterns": [
            "codex_raw_archive.*.json",
            "codex_incremental_archive.*.json",
        ],
        "supported_index_schemas": [T2_INDEX_SCHEMA, T3_INDEX_SCHEMA],
        "source_manifest_member": SOURCE_MANIFEST_MEMBER,
        "eligible_source_kinds": list(ELIGIBLE_SOURCE_KINDS),
        "source_read_only": True,
        "verified_archive_required": True,
    },
    "incremental": {
        "archive_order": "raw_ledger_append_order",
        "archive_identity": "archive_manifest_sha256",
        "session_identity": "source_relative_path",
        "latest_registered_archive_wins": True,
        "prior_archive_history_must_remain_prefix": True,
        "exact_repeat_no_write": True,
        "missing_or_drifted_output_policy": "rebuild_from_all_immutable_archives",
    },
    "concurrency": {
        "lock": "process_scoped_advisory_lock",
        "scope": "resolved_database_dir",
        "busy_policy": "fail_closed",
        "registration_change_policy": "fail_before_output_write",
    },
    "provenance": {
        "required_refs": REQUIRED_PROVENANCE_REFS,
        "evidence_level": "verified_recoverable_sanitized_raw_archive",
    },
    "outputs": EXPECTED_OUTPUTS,
    "privacy": {
        "input_policy": "recoverable_sanitized_raw_package",
        "output_policy": "derived_summary_not_full_raw_backup",
        "raw_message_text_persisted": False,
        "plaintext_credentials_allowed": False,
        "local_absolute_paths_allowed": False,
        "frontend_reads_raw": False,
    },
    "model_parameters_ref": MODEL_PARAMETERS_REF,
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}


class CodexDerivedError(ValueError):
    """Raised when immutable archive provenance or derived output safety fails."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


@dataclass(frozen=True)
class ArchiveRegistration:
    sequence: int
    archive_id: str
    kind: str
    index_ref: str
    index_sha256: str
    manifest_ref: str
    manifest_sha256: str
    package_sha256: str
    recorded_at_utc: str
    index: dict[str, Any]
    manifest: dict[str, Any]

    def state_record(self) -> dict[str, Any]:
        return {
            "sequence": self.sequence,
            "archive_id": self.archive_id,
            "kind": self.kind,
            "public_index_ref": self.index_ref,
            "public_index_sha256": self.index_sha256,
            "archive_manifest_ref": self.manifest_ref,
            "archive_manifest_sha256": self.manifest_sha256,
            "package_sha256": self.package_sha256,
            "recorded_at_utc": self.recorded_at_utc,
        }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _stable_hash(value: Any, length: int = 20) -> str:
    payload = json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return _sha256(payload)[:length]


def _json_bytes(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def _jsonl_bytes(rows: Iterable[dict[str, Any]]) -> bytes:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
        for row in rows
    ).encode("utf-8")


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


def _read_regular_bytes(path: Path, *, max_bytes: int, code: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CodexDerivedError(code) from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        raise CodexDerivedError(code)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise CodexDerivedError(code) from exc
    if not _same_stat(path.lstat(), metadata):
        raise CodexDerivedError(f"{code}_changed")
    return payload


def validate_codex_derived_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_CONTRACT:
        raise CodexDerivedError("codex_derived_contract_drift")
    return payload


def load_codex_derived_contract(
    database_dir: Path = PACKAGE_ROOT,
    path: Path | None = None,
) -> dict[str, Any]:
    contract_path = path or (database_dir.resolve() / CONTRACT_PATH)
    try:
        payload = json.loads(
            _read_regular_bytes(
                contract_path,
                max_bytes=MAX_CONTROL_BYTES,
                code="codex_derived_contract_unreadable",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexDerivedError("codex_derived_contract_invalid_json") from exc
    contract = validate_codex_derived_contract(payload)
    load_codex_derived_model_parameters(database_dir)
    return contract


def _load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            _read_regular_bytes(path, max_bytes=MAX_CONTROL_BYTES, code=code).decode(
                "utf-8"
            )
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexDerivedError(f"{code}_invalid_json") from exc
    if not isinstance(payload, dict):
        raise CodexDerivedError(f"{code}_not_object")
    return payload


def load_codex_derived_model_parameters(
    database_dir: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    payload = _load_json(
        database_dir.resolve() / MODEL_PARAMETERS_PATH,
        "codex_derived_model_parameters_unreadable",
    )
    if (
        payload.get("schema_version") != MODEL_PARAMETERS_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("model_id") != "MOD-008"
        or payload.get("formula_id") != "FORM-008"
        or payload.get("calibration_boundary") == ""
    ):
        raise CodexDerivedError("codex_derived_model_parameters_invalid")
    activity = payload.get("session_activity_formula")
    universe = payload.get("universe_state_input")
    privacy = payload.get("privacy_parameters")
    if not isinstance(activity, dict) or not isinstance(activity.get("coefficients"), dict):
        raise CodexDerivedError("codex_derived_activity_parameters_invalid")
    coefficients = activity["coefficients"]
    expected_coefficients = {
        "message_count",
        "user_message_count",
        "tool_call_count",
        "topic_label_count",
        "error_event_count",
    }
    if set(coefficients) != expected_coefficients:
        raise CodexDerivedError("codex_derived_activity_parameters_invalid")
    if any(
        isinstance(coefficients[name], bool)
        or not isinstance(coefficients[name], (int, float))
        or not math.isfinite(float(coefficients[name]))
        or float(coefficients[name]) < 0
        for name in expected_coefficients
    ):
        raise CodexDerivedError("codex_derived_activity_parameters_invalid")
    if not isinstance(universe, dict):
        raise CodexDerivedError("codex_derived_universe_parameters_invalid")
    required_universe_numbers = {
        "recent_window_days": (1, 3650),
        "inactive_normalization_days": (1, 36500),
        "confidence_base": (0, 1),
        "confidence_max_increment": (0, 1),
        "confidence_per_session": (0, 1),
    }
    for name, (minimum, maximum) in required_universe_numbers.items():
        value = universe.get(name)
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(float(value))
            or not minimum <= float(value) <= maximum
        ):
            raise CodexDerivedError("codex_derived_universe_parameters_invalid")
    if float(universe["confidence_base"]) + float(
        universe["confidence_max_increment"]
    ) > 1:
        raise CodexDerivedError("codex_derived_universe_parameters_invalid")
    if (
        not isinstance(privacy, dict)
        or privacy.get("backup_policy") != "derived_summary_not_full_raw_backup"
        or privacy.get("credential_values_forbidden") is not True
        or privacy.get("archive_member_body_in_output") is not False
    ):
        raise CodexDerivedError("codex_derived_privacy_parameters_invalid")
    return payload


def _load_raw_ledger(database_dir: Path) -> tuple[Path, list[dict[str, Any]]]:
    contract = _load_json(
        database_dir / RAW_LEDGER_CONTRACT,
        "raw_ledger_contract_unreadable",
    )
    try:
        ledger_relative = str(contract["ledger"]["path"])
    except (KeyError, TypeError) as exc:
        raise CodexDerivedError("raw_ledger_contract_invalid") from exc
    ledger_path = database_dir / ledger_relative
    payload = _read_regular_bytes(
        ledger_path,
        max_bytes=128 * 1024 * 1024,
        code="raw_ledger_unreadable",
    )
    rows: list[dict[str, Any]] = []
    for line_number, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexDerivedError(
                "raw_ledger_invalid_json", f"invalid raw ledger row {line_number}"
            ) from exc
        if not isinstance(row, dict):
            raise CodexDerivedError("raw_ledger_row_not_object")
        rows.append(row)
    return ledger_path, rows


def _registration_kind(schema: str) -> str:
    if schema == T2_INDEX_SCHEMA:
        return "baseline"
    if schema == T3_INDEX_SCHEMA:
        return "incremental"
    raise CodexDerivedError("codex_archive_index_schema_unsupported")


def _load_registrations(database_dir: Path) -> list[ArchiveRegistration]:
    public_root = database_dir / PUBLIC_INDEX_ROOT
    if public_root.is_symlink() or not public_root.is_dir():
        raise CodexDerivedError("codex_public_index_root_missing")
    _ledger_path, ledger_rows = _load_raw_ledger(database_dir)
    ledger_positions: dict[tuple[str, str, str, int], int] = {}
    for position, row in enumerate(ledger_rows):
        try:
            key = (
                str(row["source_id"]),
                str(row["relative_path"]),
                str(row["sha256"]),
                int(row["size_bytes"]),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise CodexDerivedError("raw_ledger_row_invalid") from exc
        if key in ledger_positions:
            raise CodexDerivedError("raw_ledger_duplicate_registration")
        ledger_positions[key] = position

    candidates: set[Path] = set()
    for pattern in EXPECTED_CONTRACT["inputs"]["registration_patterns"]:
        candidates.update(public_root.glob(pattern))
    if not candidates:
        raise CodexDerivedError("codex_archive_registration_missing")

    loaded: list[tuple[int, ArchiveRegistration]] = []
    seen_archive_ids: set[str] = set()
    for path in sorted(candidates):
        index_bytes = _read_regular_bytes(
            path,
            max_bytes=MAX_CONTROL_BYTES,
            code="codex_archive_index_unreadable",
        )
        try:
            index = json.loads(index_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexDerivedError("codex_archive_index_invalid_json") from exc
        if not isinstance(index, dict) or index.get("source_id") != SOURCE_ID:
            raise CodexDerivedError("codex_archive_index_invalid")
        kind = _registration_kind(str(index.get("schema_version") or ""))
        archive_id = str(index.get("archive_id") or "")
        if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", archive_id):
            raise CodexDerivedError("codex_archive_index_id_invalid")
        if archive_id in seen_archive_ids:
            raise CodexDerivedError("codex_archive_index_duplicate_id")
        seen_archive_ids.add(archive_id)
        expected_archive_path = (ARCHIVE_ROOT / archive_id).as_posix()
        if index.get("archive_path") != expected_archive_path:
            raise CodexDerivedError("codex_archive_index_path_mismatch")
        archive_dir = database_dir / ARCHIVE_ROOT / archive_id
        manifest_path = archive_dir / "manifest.json"
        manifest_bytes = _read_regular_bytes(
            manifest_path,
            max_bytes=MAX_CONTROL_BYTES,
            code="codex_archive_manifest_unreadable",
        )
        manifest_sha256 = _sha256(manifest_bytes)
        if index.get("archive_manifest_sha256") != manifest_sha256:
            raise CodexDerivedError("codex_archive_manifest_digest_mismatch")
        try:
            manifest = json.loads(manifest_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexDerivedError("codex_archive_manifest_invalid_json") from exc
        if not isinstance(manifest, dict) or manifest.get("archive_id") != archive_id:
            raise CodexDerivedError("codex_archive_manifest_identity_mismatch")
        package = manifest.get("package")
        if not isinstance(package, dict) or package.get("sha256") != index.get(
            "package_sha256"
        ):
            raise CodexDerivedError("codex_archive_package_digest_mismatch")
        index_ref = path.relative_to(database_dir).as_posix()
        index_sha256 = _sha256(index_bytes)
        ledger_relative = path.relative_to(database_dir / "data/public_raw").as_posix()
        ledger_key = (SOURCE_ID, ledger_relative, index_sha256, len(index_bytes))
        if ledger_key not in ledger_positions:
            raise CodexDerivedError("codex_archive_index_not_in_raw_ledger")
        recorded_at = str(manifest.get("recorded_at_utc") or "")
        if parse_time(recorded_at) is None:
            raise CodexDerivedError("codex_archive_recorded_at_invalid")
        registration = ArchiveRegistration(
            sequence=-1,
            archive_id=archive_id,
            kind=kind,
            index_ref=index_ref,
            index_sha256=index_sha256,
            manifest_ref=manifest_path.relative_to(database_dir).as_posix(),
            manifest_sha256=manifest_sha256,
            package_sha256=str(package["sha256"]),
            recorded_at_utc=recorded_at,
            index=index,
            manifest=manifest,
        )
        loaded.append((ledger_positions[ledger_key], registration))

    registrations: list[ArchiveRegistration] = []
    for sequence, (_ledger_position, item) in enumerate(sorted(loaded, key=lambda row: row[0])):
        registrations.append(
            ArchiveRegistration(
                sequence=sequence,
                archive_id=item.archive_id,
                kind=item.kind,
                index_ref=item.index_ref,
                index_sha256=item.index_sha256,
                manifest_ref=item.manifest_ref,
                manifest_sha256=item.manifest_sha256,
                package_sha256=item.package_sha256,
                recorded_at_utc=item.recorded_at_utc,
                index=item.index,
                manifest=item.manifest,
            )
        )
    if registrations[0].kind != "baseline":
        raise CodexDerivedError("codex_archive_history_missing_baseline")
    return registrations


def _verify_registration(database_dir: Path, item: ArchiveRegistration) -> None:
    try:
        if item.kind == "baseline":
            result = verify_codex_public_raw_archive(
                database_dir,
                item.archive_id,
                require_public_registration=True,
            )
        else:
            result = verify_codex_incremental_archive(
                database_dir,
                item.archive_id,
                require_public_registration=True,
            )
    except (CodexPublicRawArchiveError, CodexSyncStateError, OSError) as exc:
        raise CodexDerivedError(
            "codex_archive_verification_failed",
            f"{item.archive_id}: {exc}",
        ) from exc
    if result.get("status") != "PASS":
        raise CodexDerivedError("codex_archive_verification_failed")


class _JoinedPartReader:
    def __init__(self, archive_dir: Path, manifest: dict[str, Any]) -> None:
        parts = manifest.get("parts")
        package = manifest.get("package")
        if not isinstance(parts, list) or not parts or not isinstance(package, dict):
            raise CodexDerivedError("codex_archive_part_manifest_invalid")
        self._archive_dir = archive_dir
        self._parts = parts
        self._package_sha256 = str(package.get("sha256") or "")
        self._package_bytes = int(package.get("byte_size") or 0)
        self._package_digest = hashlib.sha256()
        self._package_count = 0
        self._part_index = -1
        self._handle: BinaryIO | None = None
        self._part_digest = hashlib.sha256()
        self._part_count = 0
        self._part_stat: os.stat_result | None = None
        self._open_next()

    def readable(self) -> bool:
        return True

    def _finish_current(self) -> None:
        if self._handle is None:
            return
        expected = self._parts[self._part_index]
        current_stat = os.fstat(self._handle.fileno())
        self._handle.close()
        self._handle = None
        if self._part_stat is None or not _same_stat(current_stat, self._part_stat):
            raise CodexDerivedError("codex_archive_part_changed_while_reading")
        if self._part_count != int(expected.get("byte_size") or -1):
            raise CodexDerivedError("codex_archive_part_size_mismatch")
        if self._part_digest.hexdigest() != expected.get("sha256"):
            raise CodexDerivedError("codex_archive_part_digest_mismatch")

    def _open_next(self) -> bool:
        if self._handle is not None:
            self._finish_current()
        self._part_index += 1
        if self._part_index >= len(self._parts):
            return False
        expected = self._parts[self._part_index]
        if expected.get("index") != self._part_index:
            raise CodexDerivedError("codex_archive_part_order_invalid")
        relative = str(expected.get("filename") or "")
        pure = PurePosixPath(relative)
        if pure.is_absolute() or pure.parts[:1] != ("parts",) or len(pure.parts) != 2:
            raise CodexDerivedError("codex_archive_part_path_invalid")
        path = self._archive_dir / relative
        try:
            metadata = path.lstat()
        except OSError as exc:
            raise CodexDerivedError("codex_archive_part_missing") from exc
        if not stat.S_ISREG(metadata.st_mode):
            raise CodexDerivedError("codex_archive_part_not_regular")
        try:
            self._handle = path.open("rb")
        except OSError as exc:
            raise CodexDerivedError("codex_archive_part_unreadable") from exc
        self._part_stat = os.fstat(self._handle.fileno())
        if not _same_stat(self._part_stat, metadata):
            self._handle.close()
            self._handle = None
            raise CodexDerivedError("codex_archive_part_identity_changed")
        self._part_digest = hashlib.sha256()
        self._part_count = 0
        return True

    def read(self, size: int = -1) -> bytes:
        if size == 0:
            return b""
        chunks: list[bytes] = []
        remaining = size
        while self._handle is not None and (size < 0 or remaining > 0):
            request = READ_CHUNK_BYTES if size < 0 else min(READ_CHUNK_BYTES, remaining)
            chunk = self._handle.read(request)
            if not chunk:
                if not self._open_next():
                    break
                continue
            chunks.append(chunk)
            self._part_digest.update(chunk)
            self._part_count += len(chunk)
            self._package_digest.update(chunk)
            self._package_count += len(chunk)
            if size >= 0:
                remaining -= len(chunk)
        return b"".join(chunks)

    def finish(self) -> None:
        while self.read(READ_CHUNK_BYTES):
            pass
        if self._handle is not None:
            self._finish_current()
        if self._part_index < len(self._parts):
            raise CodexDerivedError("codex_archive_part_stream_incomplete")
        if self._package_count != self._package_bytes:
            raise CodexDerivedError("codex_archive_package_size_mismatch")
        if self._package_digest.hexdigest() != self._package_sha256:
            raise CodexDerivedError("codex_archive_package_digest_mismatch")


def _detect_language(text: str) -> str:
    has_zh = bool(re.search(r"[\u4e00-\u9fff]", text))
    has_en = bool(re.search(r"[A-Za-z]", text))
    if has_zh and has_en:
        return "mixed"
    if has_zh:
        return "zh"
    if has_en:
        return "en"
    return "unknown" if not text.strip() else "other"


def _keyword_value(
    text: str,
    rules: list[tuple[str, tuple[str, ...]]],
    fallback: str,
) -> str:
    lowered = text.lower()
    for value, keywords in rules:
        if any(keyword in lowered for keyword in keywords):
            return value
    return fallback


def _infer_project(text: str) -> str | None:
    value = _keyword_value(
        text,
        [
            ("Memory Atlas", ("memory atlas", "openaidatabase", "记忆星图", "长期记忆")),
            ("KMFA", ("kmfa", "开明", "武汉")),
            ("CodexProject", ("codexproject", "主仓库", "durable memory")),
            ("Finance", ("finance", "trading", "金融", "交易")),
            ("Notion", ("notion",)),
            ("macOS Operations", ("macos", "launchagent", "清理")),
        ],
        "",
    )
    return value or None


def _infer_intent(text: str) -> str:
    return _keyword_value(
        text,
        [
            ("review", ("review", "audit", "复审", "审核", "验收", "检查")),
            ("debug", ("debug", "fix", "bug", "error", "失败", "修复", "排查")),
            ("research", ("research", "调研", "研究")),
            ("write", ("write", "文档", "报告", "总结")),
            ("operate", ("sync", "backup", "run", "执行", "同步", "备份", "清理")),
            ("build", ("build", "implement", "code", "开发", "实现", "构建")),
            ("plan", ("plan", "roadmap", "task pack", "计划", "规划")),
            ("decide", ("decide", "decision", "判断", "决策")),
            ("handoff", ("handoff", "交接", "移交")),
        ],
        "unknown",
    )


def _infer_task_type(text: str) -> str:
    return _keyword_value(
        text,
        [
            ("governance", ("review", "audit", "gate", "policy", "复审", "治理", "验收", "门禁")),
            ("automation", ("automation", "schedule", "sync", "backup", "自动", "同步", "备份")),
            ("design", ("ui", "visual", "three.js", "frontend", "设计", "可视化")),
            ("engineering", ("code", "script", "test", "validator", "cli", "实现", "开发", "构建")),
            ("data", ("data", "database", "memory", "rag", "manifest", "数据", "记忆")),
            ("research", ("research", "调研", "研究")),
            ("writing", ("doc", "report", "write", "文档", "报告")),
            ("operations", ("operate", "cleanup", "恢复", "运行", "清理")),
            ("product", ("prd", "mvp", "product", "产品")),
        ],
        "unknown",
    )


def _infer_output_type(text: str) -> str:
    return _keyword_value(
        text,
        [
            ("test", ("test", "validator", "验收", "测试", "验证")),
            ("code", ("code", "script", "cli", "实现", "开发", "构建")),
            ("report", ("report", "review", "audit", "报告", "复审")),
            ("doc", ("doc", "文档", "说明")),
            ("data", ("data", "json", "database", "manifest", "数据")),
            ("ui", ("ui", "visual", "frontend", "可视化")),
            ("config", ("config", "policy", "toml", "yaml", "配置")),
            ("plan", ("plan", "roadmap", "task pack", "计划")),
            ("decision", ("decision", "decide", "决策")),
            ("handoff", ("handoff", "交接")),
        ],
        "unknown",
    )


def _value_signals(text: str) -> list[str]:
    lowered = text.lower()
    checks = [
        ("durable_memory", ("github", "durable", "openaidatabase", "备份", "长期记忆")),
        ("verifiability", ("test", "validator", "acceptance", "evidence", "验收", "证据", "验证")),
        ("personalization", ("profile", "preference", "personalization", "偏好", "画像")),
        ("decision_support", ("roi", "decision", "report", "决策", "报告")),
        ("operational_efficiency", ("automation", "sync", "自动", "同步")),
        ("risk_reduction", ("secret", "credential", "privacy", "风险", "凭证", "安全")),
        ("knowledge_reuse", ("memory", "rag", "context", "复用", "知识", "记忆")),
    ]
    return [value for value, keywords in checks if any(token in lowered for token in keywords)]


def _risk_signals(text: str) -> list[str]:
    lowered = text.lower()
    checks = [
        ("credential_or_secret", ("secret", "credential", "token", "凭证", "密钥")),
        ("privacy_boundary", ("privacy", "private", "隐私", "脱敏")),
        ("remote_or_release", ("push", "deploy", "github main", "发布", "部署")),
        ("scope_drift", ("scope", "越界", "范围扩张")),
    ]
    return [value for value, keywords in checks if any(token in lowered for token in keywords)]


def _counter_choice(counter: Counter[str], fallback: str) -> str:
    if not counter:
        return fallback
    return sorted(counter.items(), key=lambda row: (-row[1], row[0]))[0][0]


def _parse_session_member(
    handle: BinaryIO,
    member_name: str,
    model_parameters: dict[str, Any],
) -> tuple[dict[str, Any], str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    started_at: datetime | None = None
    updated_at: datetime | None = None
    session_id = ""
    metadata: dict[str, Any] = {}
    counters: Counter[str] = Counter()
    topics: Counter[str] = Counter()
    signals: Counter[str] = Counter()
    tools: Counter[str] = Counter()
    event_types: Counter[str] = Counter()
    languages: Counter[str] = Counter()
    projects: Counter[str] = Counter()
    intents: Counter[str] = Counter()
    task_types: Counter[str] = Counter()
    output_types: Counter[str] = Counter()
    value_signals: Counter[str] = Counter()
    risk_signals: Counter[str] = Counter()

    for raw_line in handle:
        digest.update(raw_line)
        byte_count += len(raw_line)
        try:
            event = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            counters["decode_error_count"] += 1
            continue
        if not isinstance(event, dict):
            continue
        counters["event_count"] += 1
        event_time = parse_time(event.get("timestamp"))
        if event_time:
            started_at = min(started_at, event_time) if started_at else event_time
            updated_at = max(updated_at, event_time) if updated_at else event_time
        event_type = str(event.get("type") or "")
        payload = event.get("payload") if isinstance(event.get("payload"), dict) else {}
        if event_type == "session_meta":
            metadata.update(payload)
            session_id = str(payload.get("id") or session_id)
            meta_time = parse_time(payload.get("timestamp"))
            if meta_time:
                started_at = min(started_at, meta_time) if started_at else meta_time
        elif event_type == "response_item":
            item_type = str(payload.get("type") or "")
            if item_type == "message":
                role = str(payload.get("role") or "unknown")
                counters["message_count"] += 1
                counters[f"{role}_message_count"] += 1
                text = extract_message_text(payload.get("content"))
                if role == "user" and text:
                    update_rules(text, topics, TOPIC_RULES)
                    update_rules(text, signals, SIGNAL_RULES)
                    languages[_detect_language(text)] += 1
                    project = _infer_project(text)
                    if project:
                        projects[project] += 1
                    intents[_infer_intent(text)] += 1
                    task_types[_infer_task_type(text)] += 1
                    output_types[_infer_output_type(text)] += 1
                    value_signals.update(_value_signals(text))
                    risk_signals.update(_risk_signals(text))
            elif "call" in item_type or item_type in {"tool_use", "function_call"}:
                counters["tool_call_count"] += 1
                name = str(
                    payload.get("name")
                    or payload.get("recipient_name")
                    or payload.get("tool_name")
                    or item_type
                )
                tools[redact_text(name, 80)] += 1
        elif event_type == "event_msg":
            inner_type = str(payload.get("type") or "unknown")
            event_types[inner_type] += 1
            if "abort" in inner_type:
                counters["abort_count"] += 1
            if any(token in inner_type.lower() for token in ("error", "fail", "exception")):
                counters["error_event_count"] += 1

    if not session_id:
        match = re.search(r"(019[0-9a-f-]{32,})", PurePosixPath(member_name).name)
        session_id = match.group(1) if match else f"session-{_stable_hash(member_name, 24)}"
    topic_rows = [
        {"id": rule_id, "label": label, "count": topics.get(rule_id, 0)}
        for rule_id, label, _keywords in TOPIC_RULES
        if topics.get(rule_id, 0)
    ]
    signal_rows = [
        {"id": rule_id, "label": label, "count": signals.get(rule_id, 0)}
        for rule_id, label, _keywords in SIGNAL_RULES
        if signals.get(rule_id, 0)
    ]
    message_count = int(counters.get("message_count", 0))
    user_message_count = int(counters.get("user_message_count", 0))
    tool_call_count = int(counters.get("tool_call_count", 0))
    coefficients = model_parameters["session_activity_formula"]["coefficients"]
    activity_score = (
        message_count * float(coefficients["message_count"])
        + user_message_count * float(coefficients["user_message_count"])
        + tool_call_count * float(coefficients["tool_call_count"])
        + len(topic_rows) * float(coefficients["topic_label_count"])
        + int(counters.get("error_event_count", 0))
        * float(coefficients["error_event_count"])
    )
    if activity_score.is_integer():
        activity_score = int(activity_score)
    topic = (
        sorted(topic_rows, key=lambda row: (-int(row["count"]), str(row["id"])))[0][
            "label"
        ]
        if topic_rows
        else ""
    )
    top_tools = [
        {"name": name, "count": count} for name, count in tools.most_common(12)
    ]
    tool = "codex"
    if any("exec" in name or "terminal" in name for name in tools):
        tool = "terminal"
    elif any("file" in name or "patch" in name for name in tools):
        tool = "filesystem"
    friction: list[str] = []
    if counters.get("abort_count"):
        friction.append("aborted_or_interrupted")
    if counters.get("error_event_count") or counters.get("decode_error_count"):
        friction.append("errors_or_decode_issues")
    started_text = started_at.isoformat().replace("+00:00", "Z") if started_at else ""
    updated_text = updated_at.isoformat().replace("+00:00", "Z") if updated_at else ""
    return (
        {
            "session_id": session_id,
            "record_id": session_id,
            "thread_name": redact_text(str(metadata.get("thread_name") or ""), 120),
            "started_at": started_text,
            "updated_at": updated_text,
            "started_day": started_text[:10],
            "updated_day": updated_text[:10],
            "day": (updated_text or started_text)[:10],
            "originator": redact_text(str(metadata.get("originator") or ""), 80),
            "client_source": redact_text(str(metadata.get("source") or ""), 80),
            "model_provider": redact_text(str(metadata.get("model_provider") or ""), 80),
            "cli_version": redact_text(str(metadata.get("cli_version") or ""), 80),
            "message_count": message_count,
            "user_message_count": user_message_count,
            "assistant_message_count": int(counters.get("assistant_message_count", 0)),
            "tool_call_count": tool_call_count,
            "event_count": int(counters.get("event_count", 0)),
            "abort_count": int(counters.get("abort_count", 0)),
            "error_event_count": int(counters.get("error_event_count", 0)),
            "decode_error_count": int(counters.get("decode_error_count", 0)),
            "top_tools": top_tools,
            "event_types": [
                {"name": name, "count": count}
                for name, count in event_types.most_common(12)
            ],
            "topics": topic_rows,
            "preference_signals": signal_rows,
            "activity_score": activity_score,
            "topic": str(topic),
            "intent": _counter_choice(intents, "unknown"),
            "task_type": _counter_choice(task_types, "unknown"),
            "project": _counter_choice(projects, "") or None,
            "output_type": _counter_choice(output_types, "unknown"),
            "language": _counter_choice(languages, "unknown"),
            "tool": tool,
            "tools_used": [row["name"] for row in top_tools],
            "turn_count": user_message_count,
            "friction": friction,
            "value_signal": sorted(value_signals),
            "risk_signal": sorted(risk_signals),
        },
        digest.hexdigest(),
        byte_count,
    )


def _parse_index_member(handle: BinaryIO) -> tuple[dict[str, str], str, int]:
    digest = hashlib.sha256()
    byte_count = 0
    result: dict[str, str] = {}
    for raw_line in handle:
        digest.update(raw_line)
        byte_count += len(raw_line)
        try:
            row = json.loads(raw_line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            continue
        if not isinstance(row, dict):
            continue
        session_id = str(row.get("id") or row.get("session_id") or "")
        thread_name = str(
            row.get("thread_name") or row.get("name") or row.get("title") or ""
        )
        if session_id and thread_name:
            result[session_id] = redact_text(thread_name, 120)
    return result, digest.hexdigest(), byte_count


def _safe_tar_member(name: str) -> None:
    path = PurePosixPath(name)
    if (
        path.is_absolute()
        or ".." in path.parts
        or not path.parts
        or path.parts[0] != "codex"
        or "\\" in name
    ):
        raise CodexDerivedError("codex_archive_member_path_unsafe")


def _expected_archive_object(
    source_manifest: dict[str, Any],
    file_row: dict[str, Any],
) -> tuple[str, int]:
    archive_sha256 = file_row.get("archive_sha256")
    archive_size = file_row.get("archive_size_bytes")
    if archive_sha256 and archive_size is not None:
        return str(archive_sha256), int(archive_size)
    objects = source_manifest.get("objects")
    source_sha256 = str(file_row.get("source_sha256") or "")
    if not isinstance(objects, dict) or not isinstance(objects.get(source_sha256), dict):
        raise CodexDerivedError("codex_source_manifest_object_missing")
    row = objects[source_sha256]
    return str(row.get("archive_sha256") or ""), int(row.get("archive_size_bytes") or -1)


def _event_from_source_file(
    parsed: dict[str, Any],
    archive_sha256: str,
    archive_size: int,
    source_manifest: dict[str, Any],
    source_row: dict[str, Any],
    registration: ArchiveRegistration,
) -> dict[str, Any]:
    source_relative = str(source_row.get("source_relative_path") or "")
    source_sha256 = str(source_row.get("source_sha256") or "")
    source_kind = str(source_row.get("source_kind") or "")
    archive_member = str(source_row.get("archive_member") or "")
    if (
        not source_relative
        or PurePosixPath(source_relative).is_absolute()
        or ".." in PurePosixPath(source_relative).parts
        or "\\" in source_relative
        or len(source_sha256) != 64
        or source_kind not in ELIGIBLE_SOURCE_KINDS
    ):
        raise CodexDerivedError("codex_source_manifest_session_invalid")
    provenance = {
        "archive_id": registration.archive_id,
        "archive_sequence": registration.sequence,
        "public_index_ref": registration.index_ref,
        "public_index_sha256": registration.index_sha256,
        "archive_manifest_ref": registration.manifest_ref,
        "archive_manifest_sha256": registration.manifest_sha256,
        "source_manifest_member": SOURCE_MANIFEST_MEMBER,
        "source_manifest_schema_version": str(
            source_manifest.get("schema_version") or ""
        ),
        "archive_member": archive_member,
        "archive_member_sha256": archive_sha256,
        "source_relative_path": source_relative,
        "source_sha256": source_sha256,
    }
    if any(not provenance.get(field) for field in REQUIRED_PROVENANCE_REFS):
        raise CodexDerivedError("codex_derived_provenance_incomplete")
    event = dict(parsed)
    event.update(
        {
            "schema_version": EVENT_SCHEMA_VERSION,
            "event_id": f"codex_session_{_stable_hash([SOURCE_ID, source_relative])}",
            "source": SOURCE_ID,
            "source_id": SOURCE_ID,
            "source_kind": source_kind,
            "source_relative_path": source_relative,
            "source_bucket": source_relative.split("/", 1)[0],
            "source_file_hash": _stable_hash(source_relative, 16),
            "source_size_bytes": int(source_row.get("source_size_bytes") or 0),
            "content_sha256": archive_sha256,
            "archive_size_bytes": archive_size,
            "manifest_ref": registration.manifest_ref,
            "backup_policy": "derived_summary_not_full_raw_backup",
            "credential_boundary": "credentials_not_transcript",
            "model_parameters_ref": MODEL_PARAMETERS_REF,
            "provenance": provenance,
        }
    )
    if not event.get("topic"):
        event["topic"] = event.get("thread_name") or "unknown_topic"
    return event


def _parse_archive(
    database_dir: Path,
    registration: ArchiveRegistration,
    model_parameters: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    archive_dir = database_dir / ARCHIVE_ROOT / registration.archive_id
    reader = _JoinedPartReader(archive_dir, registration.manifest)
    parsed_sessions: dict[str, tuple[dict[str, Any], str, int]] = {}
    parsed_indexes: dict[str, tuple[dict[str, str], str, int]] = {}
    source_manifest: dict[str, Any] | None = None
    try:
        with tarfile.open(fileobj=reader, mode="r|gz") as archive:
            for member in archive:
                _safe_tar_member(member.name)
                if not member.isfile():
                    raise CodexDerivedError("codex_archive_member_not_regular")
                handle = archive.extractfile(member)
                if handle is None:
                    raise CodexDerivedError("codex_archive_member_unreadable")
                if member.name == SOURCE_MANIFEST_MEMBER:
                    if member.size > MAX_CONTROL_BYTES:
                        raise CodexDerivedError("codex_source_manifest_too_large")
                    payload = handle.read()
                    if len(payload) != member.size:
                        raise CodexDerivedError("codex_source_manifest_truncated")
                    try:
                        loaded = json.loads(payload.decode("utf-8"))
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise CodexDerivedError("codex_source_manifest_invalid_json") from exc
                    if not isinstance(loaded, dict):
                        raise CodexDerivedError("codex_source_manifest_not_object")
                    source_manifest = loaded
                elif (
                    member.name.startswith("codex/sessions/")
                    or member.name.startswith("codex/archived_sessions/")
                ) and member.name.endswith(".jsonl"):
                    parsed_sessions[member.name] = _parse_session_member(
                        handle,
                        member.name,
                        model_parameters,
                    )
                elif member.name == "codex/session_index.jsonl":
                    parsed_indexes[member.name] = _parse_index_member(handle)
        reader.finish()
    except CodexDerivedError:
        raise
    except (tarfile.TarError, OSError, EOFError) as exc:
        raise CodexDerivedError("codex_archive_stream_invalid") from exc

    if source_manifest is None:
        raise CodexDerivedError("codex_source_manifest_missing")
    if (
        source_manifest.get("archive_id") != registration.archive_id
        or source_manifest.get("source_id") != SOURCE_ID
    ):
        raise CodexDerivedError("codex_source_manifest_identity_mismatch")
    source_files = source_manifest.get("files")
    if not isinstance(source_files, list):
        raise CodexDerivedError("codex_source_manifest_files_invalid")

    events: list[dict[str, Any]] = []
    matched_members: set[str] = set()
    index_updates: dict[str, str] = {}
    for source_row in source_files:
        if not isinstance(source_row, dict):
            raise CodexDerivedError("codex_source_manifest_file_invalid")
        member_name = str(source_row.get("archive_member") or "")
        if member_name in parsed_indexes:
            rows, digest, size = parsed_indexes[member_name]
            expected_digest, expected_size = _expected_archive_object(
                source_manifest, source_row
            )
            if digest != expected_digest or size != expected_size:
                raise CodexDerivedError("codex_archive_index_member_digest_mismatch")
            index_updates.update(rows)
            continue
        if str(source_row.get("source_kind") or "") not in ELIGIBLE_SOURCE_KINDS:
            continue
        if member_name not in parsed_sessions:
            raise CodexDerivedError("codex_source_manifest_session_member_missing")
        parsed, digest, size = parsed_sessions[member_name]
        expected_digest, expected_size = _expected_archive_object(
            source_manifest, source_row
        )
        if digest != expected_digest or size != expected_size:
            raise CodexDerivedError("codex_archive_session_member_digest_mismatch")
        matched_members.add(member_name)
        events.append(
            _event_from_source_file(
                parsed,
                digest,
                size,
                source_manifest,
                source_row,
                registration,
            )
        )
    if matched_members != set(parsed_sessions):
        raise CodexDerivedError("codex_archive_unproven_session_member")
    return events, index_updates


def _load_existing_events(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CodexDerivedError("codex_derived_events_unreadable") from exc
    for line in lines:
        if not line:
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexDerivedError("codex_derived_events_invalid_json") from exc
        if not isinstance(row, dict) or row.get("schema_version") != EVENT_SCHEMA_VERSION:
            raise CodexDerivedError("codex_derived_events_schema_invalid")
        rows.append(row)
    return rows


def _load_state(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    state = _load_json(path, "codex_derived_state_unreadable")
    if (
        state.get("schema_version") != STATE_SCHEMA_VERSION
        or state.get("task_id") != TASK_ID
        or state.get("acceptance_id") != ACCEPTANCE_ID
        or state.get("source_id") != SOURCE_ID
        or state.get("phase_boundary") != EXPECTED_PHASE_BOUNDARY
        or not isinstance(state.get("input_archives"), list)
        or not isinstance(state.get("output_hashes"), dict)
    ):
        raise CodexDerivedError("codex_derived_state_invalid")
    return state


def _outputs_match_state(database_dir: Path, state: dict[str, Any]) -> bool:
    expected = state["output_hashes"]
    all_paths = list(EXPECTED_OUTPUTS.values())[:-1]
    if set(expected) != set(all_paths):
        return False
    for relative in all_paths:
        pure = PurePosixPath(relative)
        if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
            return False
        parent = database_dir
        for component in pure.parts[:-1]:
            parent = parent / component
            if not os.path.lexists(parent):
                return False
            metadata = parent.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                return False
        path = database_dir / relative
        if not os.path.lexists(path):
            return False
        metadata = path.lstat()
        if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
            return False
        payload = path.read_bytes()
        row = expected.get(relative)
        if not isinstance(row, dict):
            return False
        if row.get("sha256") != _sha256(payload) or row.get("byte_size") != len(payload):
            return False
    return True


def _archive_records(registrations: list[ArchiveRegistration]) -> list[dict[str, Any]]:
    return [item.state_record() for item in registrations]


def _topic_counts(events: list[dict[str, Any]]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for event in events:
        for topic in event.get("topics", []):
            if isinstance(topic, dict):
                counts[str(topic.get("label") or "unknown_topic")] += int(
                    topic.get("count") or 0
                )
    return counts


def _build_facets(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    facets: list[dict[str, Any]] = []
    for event in events:
        provenance = event["provenance"]
        facets.append(
            {
                "schema_version": FACET_SCHEMA_VERSION,
                "event_id": event["event_id"],
                "source": SOURCE_ID,
                "source_id": SOURCE_ID,
                "record_id": event["record_id"],
                "occurred_at": event.get("updated_at") or event.get("started_at") or "",
                "topic": event.get("topic") or event.get("thread_name") or "unknown_topic",
                "intent": event.get("intent") or "unknown",
                "task_type": event.get("task_type") or "unknown",
                "project": event.get("project"),
                "output_type": event.get("output_type") or "unknown",
                "language": event.get("language") or "unknown",
                "tool": event.get("tool") or "codex",
                "turn_count": int(event.get("turn_count") or 0),
                "friction": event.get("friction") or [],
                "value_signal": event.get("value_signal") or [],
                "future_agent_source": None,
                "risk_signal": event.get("risk_signal") or [],
                "tools_used": event.get("tools_used") or [],
                "manifest_ref": provenance["archive_manifest_ref"],
                "confidence": "high",
                "evidence_refs": [
                    {
                        "ref_type": "archive_manifest",
                        "evidence_level": "verified_recoverable_sanitized_raw_archive",
                        "path": provenance["archive_manifest_ref"],
                        "sha256": provenance["archive_manifest_sha256"],
                        "source_id": SOURCE_ID,
                        "record_id": event["record_id"],
                    },
                    {
                        "ref_type": "archive_member",
                        "evidence_level": "verified_recoverable_sanitized_raw_archive",
                        "archive_id": provenance["archive_id"],
                        "member": provenance["archive_member"],
                        "sha256": provenance["archive_member_sha256"],
                        "source_sha256": provenance["source_sha256"],
                        "source_id": SOURCE_ID,
                        "record_id": event["record_id"],
                    },
                ],
            }
        )
    return facets


def _build_behavior_summary(
    events: list[dict[str, Any]],
    facets: list[dict[str, Any]],
    registrations: list[ArchiveRegistration],
    generated_at: str,
    model_parameters_sha256: str,
) -> dict[str, Any]:
    topics = _topic_counts(events)
    tools: Counter[str] = Counter()
    projects: Counter[str] = Counter()
    intents: Counter[str] = Counter()
    days = sorted({str(event.get("day") or "") for event in events if event.get("day")})
    for event in events:
        for row in event.get("top_tools", []):
            if isinstance(row, dict):
                tools[str(row.get("name") or "unknown")] += int(row.get("count") or 0)
    for facet in facets:
        if facet.get("project"):
            projects[str(facet["project"])] += 1
        intents[str(facet.get("intent") or "unknown")] += 1
    return {
        "schema_version": BEHAVIOR_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "generated_at": generated_at,
        "source_id": SOURCE_ID,
        "source_truth": {
            "kind": "derived_from_verified_recoverable_sanitized_raw_archives",
            "full_raw_backup": False,
            "recoverable_sanitized_raw_available": True,
            "credentials_excluded": True,
            "local_absolute_paths_excluded": True,
        },
        "archive_count": len(registrations),
        "session_count": len(events),
        "facet_count": len(facets),
        "day_count": len(days),
        "range_start": days[0] if days else "",
        "range_end": days[-1] if days else "",
        "message_count": sum(int(row.get("message_count") or 0) for row in events),
        "tool_call_count": sum(int(row.get("tool_call_count") or 0) for row in events),
        "error_event_count": sum(int(row.get("error_event_count") or 0) for row in events),
        "abort_count": sum(int(row.get("abort_count") or 0) for row in events),
        "top_topics": [
            {"label": label, "count": count} for label, count in topics.most_common(12)
        ],
        "top_tools": [
            {"name": name, "count": count} for name, count in tools.most_common(12)
        ],
        "top_projects": [
            {"name": name, "count": count} for name, count in projects.most_common(12)
        ],
        "top_intents": [
            {"name": name, "count": count} for name, count in intents.most_common(12)
        ],
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": model_parameters_sha256,
        "provenance": _archive_records(registrations),
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _clamp01(value: float) -> float:
    return round(max(0.0, min(1.0, value)), 6)


def _build_universe_input(
    events: list[dict[str, Any]],
    behavior: dict[str, Any],
    registrations: list[ArchiveRegistration],
    model_parameters: dict[str, Any],
) -> dict[str, Any]:
    generated = parse_time(behavior["generated_at"]) or datetime.now(timezone.utc)
    universe_parameters = model_parameters["universe_state_input"]
    recent_window_days = int(universe_parameters["recent_window_days"])
    inactive_normalization_days = int(
        universe_parameters["inactive_normalization_days"]
    )
    confidence_base = float(universe_parameters["confidence_base"])
    confidence_max_increment = float(
        universe_parameters["confidence_max_increment"]
    )
    confidence_per_session = float(
        universe_parameters["confidence_per_session"]
    )
    recent_start = generated - timedelta(days=recent_window_days)
    grouped: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(list)
    for event in events:
        topics = event.get("topics") if isinstance(event.get("topics"), list) else []
        if topics:
            for topic in topics:
                if isinstance(topic, dict):
                    grouped[(str(topic.get("id") or "unknown"), str(topic.get("label") or "unknown_topic"))].append(event)
        else:
            grouped[("unknown", str(event.get("thread_name") or "unknown_topic"))].append(event)
    max_count = max((len(rows) for rows in grouped.values()), default=1)
    clusters: list[dict[str, Any]] = []
    for (topic_id, label), rows in grouped.items():
        observed_times = [
            parsed
            for row in rows
            if (parsed := parse_time(row.get("updated_at") or row.get("started_at")))
            is not None
        ]
        latest = max(observed_times, default=generated)
        recent_rows = [
            row
            for row in rows
            if (parse_time(row.get("updated_at") or row.get("started_at")) or datetime.min.replace(tzinfo=timezone.utc))
            >= recent_start
        ]
        inactive_days = max(0, (generated.date() - latest.date()).days)
        value_count = sum(1 for row in rows if row.get("value_signal"))
        relation_count = len(
            {
                str(tool)
                for row in rows
                for tool in (row.get("tools_used") or [])
                if tool
            }
        )
        clusters.append(
            {
                "cluster_id": f"cluster-codex-{_stable_hash([topic_id, label], 12)}",
                "label": label,
                "theme_id": f"theme-codex-{re.sub(r'[^a-z0-9]+', '-', topic_id.lower()).strip('-') or 'unknown'}",
                "source_scope": "codex",
                "mass_score": _clamp01(len(rows) / max_count),
                "evidence_count": len(rows),
                "growth_score": _clamp01(len(recent_rows) / max(1, len(rows))),
                "recent_signal_count": len(recent_rows),
                "decline_score": _clamp01(
                    inactive_days / inactive_normalization_days
                ),
                "inactive_days": inactive_days,
                "latest_signal_date": latest.date().isoformat(),
                "confidence": _clamp01(
                    confidence_base
                    + min(
                        confidence_max_increment,
                        len(rows) * confidence_per_session,
                    )
                ),
                "recommended_action": "在后续 Atlas 更新中复核该主题的可解释关联。",
                "relation_count": relation_count,
                "roi_potential": _clamp01(value_count / max(1, len(rows))),
            }
        )
    clusters.sort(key=lambda row: (-float(row["mass_score"]), str(row["cluster_id"])))
    recent_event_count = sum(
        1
        for event in events
        if (parse_time(event.get("updated_at") or event.get("started_at")) or datetime.min.replace(tzinfo=timezone.utc))
        >= recent_start
    )
    return {
        "schema_version": "memory_atlas_universe_state_fixture.v1",
        "generated_at": behavior["generated_at"],
        "source_scope": "codex",
        "time_range": {
            "start": behavior["range_start"] or generated.date().isoformat(),
            "end": behavior["range_end"] or generated.date().isoformat(),
        },
        "redaction_mode": "public_redacted_read_only_visualization",
        "source_safety": {
            "raw_private_data_included": False,
            "plaintext_secrets_included": False,
            "local_absolute_paths_included": False,
            "writeback_allowed": False,
        },
        "clusters": clusters,
        "conflict_zones": [],
        "black_hole_candidates": [],
        "proto_star_candidates": [],
        "activity": {
            "recent_window_days": recent_window_days,
            "activity_density": _clamp01(
                recent_event_count / recent_window_days
            ),
            "dominant_lane_ids": [row["cluster_id"] for row in clusters[:3]],
            "recent_event_count": recent_event_count,
        },
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": behavior["model_parameters_sha256"],
        "provenance": _archive_records(registrations),
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def _validate_output_privacy(payloads: dict[str, bytes]) -> None:
    for relative, payload in payloads.items():
        try:
            text = payload.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise CodexDerivedError("codex_derived_output_not_utf8") from exc
        if LOCAL_ABSOLUTE_PATH_RE.search(text):
            raise CodexDerivedError(
                "codex_derived_output_absolute_path", f"absolute path in {relative}"
            )
        if credential_exclusion_hits(text, source=relative):
            raise CodexDerivedError(
                "codex_derived_output_credential", f"credential-shaped value in {relative}"
            )


def _fsync_parent(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _ensure_safe_output_parent(database_dir: Path, relative: str) -> Path:
    pure = PurePosixPath(relative)
    if pure.is_absolute() or ".." in pure.parts or "\\" in relative:
        raise CodexDerivedError("codex_derived_output_path_invalid")
    parent = database_dir
    for component in pure.parts[:-1]:
        parent = parent / component
        if os.path.lexists(parent):
            metadata = parent.lstat()
            if not stat.S_ISDIR(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                raise CodexDerivedError("codex_derived_output_parent_unsafe")
        else:
            try:
                parent.mkdir(mode=0o700)
            except OSError as exc:
                raise CodexDerivedError("codex_derived_output_parent_unwritable") from exc
    return database_dir / relative


def _write_bundle(database_dir: Path, payloads: dict[str, bytes]) -> list[str]:
    staged: list[tuple[Path, Path]] = []
    changed: list[str] = []
    try:
        for relative, payload in payloads.items():
            path = _ensure_safe_output_parent(database_dir, relative)
            if os.path.lexists(path):
                metadata = path.lstat()
                if not stat.S_ISREG(metadata.st_mode) or stat.S_ISLNK(metadata.st_mode):
                    raise CodexDerivedError("codex_derived_output_target_unsafe")
            if path.is_file() and path.read_bytes() == payload:
                continue
            temp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
            if temp.exists():
                raise CodexDerivedError("codex_derived_temp_conflict")
            descriptor = os.open(temp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            try:
                view = memoryview(payload)
                while view:
                    written = os.write(descriptor, view)
                    if written <= 0:
                        raise CodexDerivedError("codex_derived_output_short_write")
                    view = view[written:]
                os.fsync(descriptor)
            finally:
                os.close(descriptor)
            staged.append((temp, path))
            changed.append(relative)
        state_relative = EXPECTED_OUTPUTS["state"]
        staged.sort(key=lambda row: row[1].relative_to(database_dir).as_posix() == state_relative)
        parents: set[Path] = set()
        for temp, path in staged:
            os.replace(temp, path)
            parents.add(path.parent)
        for parent in sorted(parents):
            _fsync_parent(parent)
    finally:
        for temp, _path in staged:
            if temp.exists():
                temp.unlink()
    return changed


@contextmanager
def _derived_lock(database_dir: Path) -> Iterator[None]:
    identity = hashlib.sha256(str(database_dir.resolve()).encode("utf-8")).hexdigest()[:24]
    lock_path = Path(tempfile.gettempdir()) / f"memory-atlas-codex-derived-{identity}.lock"
    flags = os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise CodexDerivedError("codex_derived_lock_unavailable") from exc
    handle = os.fdopen(descriptor, "a+b")
    try:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise CodexDerivedError("codex_derived_lock_busy") from exc
        yield
    finally:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


def _build_codex_derived_locked(
    database_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    contract = load_codex_derived_contract(database_dir)
    model_parameters = load_codex_derived_model_parameters(database_dir)
    contract_sha256 = _sha256(_json_bytes(contract))
    model_parameters_sha256 = _sha256(_json_bytes(model_parameters))
    registrations = _load_registrations(database_dir)
    for registration in registrations:
        _verify_registration(database_dir, registration)
    current_records = _archive_records(registrations)
    state_path = database_dir / EXPECTED_OUTPUTS["state"]
    state = _load_state(state_path)
    old_records = state["input_archives"] if state else []
    if old_records and old_records != current_records[: len(old_records)]:
        raise CodexDerivedError("codex_archive_history_not_append_only")
    state_contract_current = bool(
        state
        and state.get("contract_sha256") == contract_sha256
        and state.get("model_parameters_ref") == MODEL_PARAMETERS_REF
        and state.get("model_parameters_sha256") == model_parameters_sha256
    )
    outputs_current = bool(
        state_contract_current and state and _outputs_match_state(database_dir, state)
    )
    if state and old_records == current_records and outputs_current:
        if _archive_records(_load_registrations(database_dir)) != current_records:
            raise CodexDerivedError("codex_archive_history_changed_while_building")
        return {
            "schema_version": STATE_SCHEMA_VERSION,
            "status": "PASS",
            "outcome": "NO_CHANGES",
            "dry_run": dry_run,
            "writes_files": False,
            "raw_mutation": False,
            "atlas_snapshot_updated": False,
            "weekly_report_updated": False,
            "sync_state_updated": False,
            "input_archive_count": len(registrations),
            "parsed_archive_count": 0,
            "event_count": int(state.get("event_count") or 0),
            "facet_count": int(state.get("facet_count") or 0),
            "output_paths": EXPECTED_OUTPUTS,
            "phase_boundary": EXPECTED_PHASE_BOUNDARY,
        }

    incremental = bool(state and outputs_current and len(old_records) < len(current_records))
    parse_from = len(old_records) if incremental else 0
    if incremental:
        events_by_path = {
            str(row["source_relative_path"]): row
            for row in _load_existing_events(database_dir / EXPECTED_OUTPUTS["events"])
        }
    else:
        events_by_path = {}
    index_updates: dict[str, str] = {}
    for registration in registrations[parse_from:]:
        parsed_events, parsed_index = _parse_archive(
            database_dir,
            registration,
            model_parameters,
        )
        for event in parsed_events:
            events_by_path[str(event["source_relative_path"])] = event
        index_updates.update(parsed_index)
    for event in events_by_path.values():
        thread_name = index_updates.get(str(event.get("session_id") or ""))
        if thread_name:
            event["thread_name"] = thread_name
        if not event.get("thread_name"):
            event["thread_name"] = redact_text(
                PurePosixPath(str(event["source_relative_path"])).stem, 120
            )
        if not event.get("topic") or event.get("topic") == "unknown_topic":
            event["topic"] = event["thread_name"] or "unknown_topic"
    events = sorted(
        events_by_path.values(),
        key=lambda row: (
            str(row.get("updated_at") or row.get("started_at") or ""),
            str(row.get("source_relative_path") or ""),
        ),
    )
    facets = _build_facets(events)
    generated_at = registrations[-1].recorded_at_utc
    behavior = _build_behavior_summary(
        events,
        facets,
        registrations,
        generated_at,
        model_parameters_sha256,
    )
    universe = _build_universe_input(
        events,
        behavior,
        registrations,
        model_parameters,
    )
    payloads: dict[str, bytes] = {
        EXPECTED_OUTPUTS["events"]: _jsonl_bytes(events),
        EXPECTED_OUTPUTS["facets"]: _jsonl_bytes(facets),
        EXPECTED_OUTPUTS["behavior_summary"]: _json_bytes(behavior),
        EXPECTED_OUTPUTS["universe_state_input"]: _json_bytes(universe),
    }
    _validate_output_privacy(payloads)
    output_hashes = {
        relative: {"sha256": _sha256(payload), "byte_size": len(payload)}
        for relative, payload in sorted(payloads.items())
    }
    if incremental:
        outcome = "INCREMENTAL_BUILD"
    elif state:
        outcome = "REBUILT_FROM_IMMUTABLE_RAW"
    else:
        outcome = "BUILT_FROM_IMMUTABLE_RAW"
    state_payload = {
        "schema_version": STATE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "contract_ref": CONTRACT_PATH.as_posix(),
        "contract_sha256": contract_sha256,
        "model_parameters_ref": MODEL_PARAMETERS_REF,
        "model_parameters_sha256": model_parameters_sha256,
        "generated_at": generated_at,
        "input_archives": current_records,
        "event_count": len(events),
        "facet_count": len(facets),
        "output_hashes": output_hashes,
        "last_result": {
            "outcome": outcome,
            "parsed_archive_count": len(registrations) - parse_from,
            "input_archive_count": len(registrations),
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }
    payloads[EXPECTED_OUTPUTS["state"]] = _json_bytes(state_payload)
    _validate_output_privacy({EXPECTED_OUTPUTS["state"]: payloads[EXPECTED_OUTPUTS["state"]]})
    if _archive_records(_load_registrations(database_dir)) != current_records:
        raise CodexDerivedError("codex_archive_history_changed_while_building")
    changed = [] if dry_run else _write_bundle(database_dir, payloads)
    return {
        "schema_version": STATE_SCHEMA_VERSION,
        "status": "PASS",
        "outcome": outcome if not dry_run else f"WOULD_{outcome}",
        "dry_run": dry_run,
        "writes_files": bool(changed),
        "raw_mutation": False,
        "atlas_snapshot_updated": False,
        "weekly_report_updated": False,
        "sync_state_updated": False,
        "input_archive_count": len(registrations),
        "parsed_archive_count": len(registrations) - parse_from,
        "event_count": len(events),
        "facet_count": len(facets),
        "changed_paths": changed,
        "output_paths": EXPECTED_OUTPUTS,
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def build_codex_derived(
    database_dir: Path,
    *,
    dry_run: bool = False,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    with _derived_lock(database_dir):
        return _build_codex_derived_locked(database_dir, dry_run=dry_run)


def run_codex_derived(args: argparse.Namespace) -> int:
    try:
        result = build_codex_derived(
            Path(args.database_dir),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    except CodexDerivedError as exc:
        print(
            json.dumps(
                {
                    "schema_version": STATE_SCHEMA_VERSION,
                    "status": "FAIL",
                    "error_code": exc.code,
                    "reason": str(exc),
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
    "EXPECTED_OUTPUTS",
    "EXPECTED_PHASE_BOUNDARY",
    "MODEL_PARAMETERS_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "TASK_ID",
    "CodexDerivedError",
    "build_codex_derived",
    "load_codex_derived_contract",
    "load_codex_derived_model_parameters",
    "run_codex_derived",
    "validate_codex_derived_contract",
)
