"""Append-only archival of a verified private ChatGPT export ZIP."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from raw_archive_manifest import (
    ManifestConflict,
    generate_raw_manifest,
    preflight_raw_ledger,
)

from .archive_chunking import (
    GITHUB_WARNING_BYTES,
    MAX_PART_BYTES,
    ArchiveChunkError,
    ArchiveChunkPartialWriteError,
    ArchiveChunkPostPublishError,
    chunk_archive_package,
)
from .archive_restore import ArchiveRestoreError, verify_archive
from .chatgpt_export_download import (
    ExportDownloadError,
    load_private_downloaded_export,
)
from .chatgpt_export_state import (
    ChatGPTExportStateError,
    apply_export_transition,
    export_state_lock,
    load_chatgpt_export_state,
    load_chatgpt_export_state_contract,
    load_chatgpt_export_state_model_parameters,
    write_chatgpt_export_state,
)


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_archive.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_archive.v1_2_1_s08_p3_t1.json"
)
ARCHIVE_ROOT = Path("data/raw_archives/chatgpt")
PUBLIC_INDEX_ROOT = Path("data/public_raw/chatgpt")
RAW_MANIFEST_ROOT = Path("机器治理/证据与日志/raw_archive_manifests")
RAW_LEDGER_RELATIVE = RAW_MANIFEST_ROOT / "raw_hash_ledger.jsonl"

TASK_ID = "S08-P3-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P3-T1"
SOURCE_ID = "chatgpt"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_archive_contract.v1_2_1_s08_p3_t1"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_archive_model.v1_2_1_s08_p3_t1"
)
PUBLIC_INDEX_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_archive_index.v1_2_1_s08_p3_t1"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_archive_result.v1_2_1_s08_p3_t1"
)

MAX_CONTRACT_BYTES = 128 * 1024
MAX_PUBLIC_INDEX_BYTES = 128 * 1024
MAX_ARCHIVED_REGISTRATION_SCAN = 10_000
READ_CHUNK_BYTES = 1024 * 1024
PUBLIC_INDEX_FILE_MODE = 0o600
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_ARCHIVE_ID_RE = re.compile(r"^chatgpt-export-[0-9a-f]{64}$")

PHASE_BOUNDARY = {
    "writes_append_only_raw_archive": True,
    "writes_public_provenance_index": True,
    "parses_export": False,
    "commits_or_pushes": False,
    "deploys": False,
    "real_archive_required_for_completion": True,
    "next_task": "S08-P3-T2",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": SOURCE_ID,
    "input": {
        "private_export_loader": "memory_atlas_cli.chatgpt_export_download:load_private_downloaded_export",
        "verified_private_zip_required": True,
        "request_id_must_match_state": True,
        "source_bytes_read_only": True,
        "private_path_emitted": False,
    },
    "state_gate": {
        "required_state": "DOWNLOADED",
        "success_state": "ARCHIVED",
        "idempotent_state": "ARCHIVED",
        "noneligible_state_reads_private_runtime": False,
        "state_lock_covers_archive_registration_and_transition": True,
    },
    "archive": {
        "chunk_contract_ref": "config/data_sources/archive_chunking.json",
        "restore_contract_ref": "config/data_sources/archive_restore.json",
        "root": ARCHIVE_ROOT.as_posix(),
        "archive_id_formula": "chatgpt-export-{download_sha256}",
        "maximum_part_bytes": MAX_PART_BYTES,
        "github_warning_bytes": GITHUB_WARNING_BYTES,
        "force_archive_below_threshold": True,
        "manifest_publish_last": True,
        "verify_after_publish": True,
        "package_hash_identity_required": True,
    },
    "provenance": {
        "public_index_root": PUBLIC_INDEX_ROOT.as_posix(),
        "public_index_filename_formula": "chatgpt_raw_archive.{archive_id}.{request_id}.json",
        "export_batch_id": "request_id",
        "request_metadata_sha256": True,
        "private_download_metadata_sha256": True,
        "preserve_request_fields": [
            "request_id",
            "reserved_at",
            "origin_state",
            "dispatch_status",
            "request_click_count",
            "connector_error_code",
            "connector_result_sha256",
        ],
        "preserve_download_fields": [
            "link_sha256",
            "account_digest",
            "download_sha256",
            "bytes_downloaded",
            "downloaded_at",
            "zip_member_count",
            "conversations_member_count",
            "uncompressed_bytes",
            "transport",
        ],
        "private_relative_path_public": False,
        "raw_account_or_url_public": False,
    },
    "append_only": {
        "archive_identity": "download_sha256",
        "same_hash_creates_second_archive": False,
        "new_request_same_hash_appends_provenance": True,
        "existing_archive_rewritten": False,
        "public_index_no_overwrite": True,
        "raw_ledger_required": True,
        "state_write_failure_reuses_archive_and_index": True,
    },
    "cli": {
        "command": "chatgpt-export-archive",
        "modes": ["--inspect", "--archive --confirm-archive"],
        "output_is_sanitized": True,
    },
    "security": {
        "browser_cookie_access": False,
        "browser_profile_access": False,
        "credential_access": False,
        "private_zip_committed": False,
        "private_path_emitted": False,
        "raw_account_or_url_emitted": False,
        "remote_git_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S08-P3-T1",
    "formula_id": "FORM-MA-V121-S08-P3-T1",
    "purpose": "Publish one verified private ChatGPT export as a recoverable append-only archive while preserving request and download provenance without exposing private paths or raw account/link values.",
    "parameters": {
        "maximum_part_bytes": MAX_PART_BYTES,
        "github_warning_bytes": GITHUB_WARNING_BYTES,
        "hash_algorithm": "sha256",
        "hash_hex_characters": 64,
        "read_chunk_bytes": READ_CHUNK_BYTES,
        "maximum_contract_bytes": MAX_CONTRACT_BYTES,
        "maximum_public_index_bytes": MAX_PUBLIC_INDEX_BYTES,
        "maximum_archived_registration_scan": MAX_ARCHIVED_REGISTRATION_SCAN,
        "archive_directory_mode_octal": "0700",
        "archive_file_mode_octal": "0600",
        "public_index_file_mode_octal": "0600",
        "duplicate_archives_per_download_hash_maximum": 1,
        "private_zip_bytes_in_repository": 0,
        "remote_push_attempts": 0,
    },
    "formulas": {
        "archive_id": "chatgpt-export-{download_sha256}",
        "part_count": "ceil(bytes_downloaded / 47185920)",
        "public_index_identity": "sha256(canonical_public_index_json)",
        "request_metadata_identity": "sha256(canonical_request_metadata_json)",
        "download_metadata_identity": "sha256(canonical_private_download_metadata_json)",
        "state_transition": "DOWNLOADED + verified_archive + public_index + raw_ledger -> ARCHIVED",
    },
    "invariants": [
        "archive parts reconstruct exactly to download_sha256 and bytes_downloaded",
        "all part files are at most 45 MiB and below the GitHub warning line",
        "same download hash never creates a second archive directory",
        "a new request for the same hash appends provenance without rewriting the archive",
        "ARCHIVED is written only after archive verification and public raw ledger verification",
        "no private path, raw account, one-time URL, cookie or credential is emitted or committed",
    ],
    "phase_boundary": {
        "parses_export": False,
        "commits_or_pushes": False,
        "next_task": "S08-P3-T2",
    },
}

PrivateLoader = Callable[..., tuple[Path, dict[str, Any]]]
StateWriter = Callable[[Path, dict[str, Any]], None]
Clock = Callable[[], datetime]


class ChatGPTExportArchiveError(ValueError):
    def __init__(
        self,
        code: str,
        *,
        writes_files: bool = False,
        archive_may_exist: bool = False,
    ) -> None:
        super().__init__(code)
        self.code = code
        self.writes_files = writes_files
        self.archive_may_exist = archive_may_exist


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
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


def _database_root(database_dir: Path) -> Path:
    candidate = Path(database_dir).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise ChatGPTExportArchiveError("export_archive_database_invalid")
    return candidate.resolve()


def _read_regular_bytes(path: Path, *, maximum_bytes: int, code: str) -> bytes:
    descriptor: int | None = None
    try:
        metadata = path.lstat()
        if path.is_symlink() or not stat.S_ISREG(metadata.st_mode):
            raise ChatGPTExportArchiveError(code)
        if metadata.st_size > maximum_bytes:
            raise ChatGPTExportArchiveError(code)
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        payload = b""
        while len(payload) <= maximum_bytes:
            chunk = os.read(descriptor, min(READ_CHUNK_BYTES, maximum_bytes + 1 - len(payload)))
            if not chunk:
                break
            payload += chunk
        if len(payload) > maximum_bytes or not _same_file_identity(
            os.fstat(descriptor), metadata
        ):
            raise ChatGPTExportArchiveError(code)
        return payload
    except ChatGPTExportArchiveError:
        raise
    except OSError as exc:
        raise ChatGPTExportArchiveError(code) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _read_json(path: Path, *, maximum_bytes: int, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            _read_regular_bytes(path, maximum_bytes=maximum_bytes, code=code).decode(
                "utf-8"
            )
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChatGPTExportArchiveError(code) from exc
    if not isinstance(payload, dict):
        raise ChatGPTExportArchiveError(code)
    return payload


def validate_chatgpt_export_archive_contract(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_CONTRACT:
        raise ChatGPTExportArchiveError("export_archive_contract_drift")
    return dict(payload)


def validate_chatgpt_export_archive_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if not isinstance(payload, dict) or payload != EXPECTED_MODEL_PARAMETERS:
        raise ChatGPTExportArchiveError("export_archive_model_drift")
    return dict(payload)


def load_chatgpt_export_archive_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_archive_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="export_archive_contract_invalid",
        )
    )


def load_chatgpt_export_archive_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_archive_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="export_archive_model_invalid",
        )
    )


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ChatGPTExportArchiveError("export_archive_clock_invalid")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _archive_id(download_sha256: object) -> str:
    if not isinstance(download_sha256, str) or not _SHA256_RE.fullmatch(
        download_sha256
    ):
        raise ChatGPTExportArchiveError("export_archive_download_hash_invalid")
    return f"chatgpt-export-{download_sha256}"


def _request_id(value: object) -> str:
    if not isinstance(value, str) or not _REQUEST_ID_RE.fullmatch(value):
        raise ChatGPTExportArchiveError("export_archive_request_invalid")
    return value


def _run_id(request_id: str) -> str:
    return f"s08_p3_t1_{request_id}"


def _public_index_relative(archive_id: str, request_id: str) -> Path:
    if not _ARCHIVE_ID_RE.fullmatch(archive_id):
        raise ChatGPTExportArchiveError("export_archive_id_invalid")
    _request_id(request_id)
    return PUBLIC_INDEX_ROOT / f"chatgpt_raw_archive.{archive_id}.{request_id}.json"


def _safe_request_metadata(state: dict[str, Any]) -> dict[str, Any]:
    request = state.get("request")
    if not isinstance(request, dict):
        raise ChatGPTExportArchiveError("export_archive_request_invalid")
    required = EXPECTED_CONTRACT["provenance"]["preserve_request_fields"]
    if set(request) != set(required):
        raise ChatGPTExportArchiveError("export_archive_request_invalid")
    _request_id(request.get("request_id"))
    return {field: request[field] for field in required}


def _safe_download_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    required = EXPECTED_CONTRACT["provenance"]["preserve_download_fields"]
    if not all(field in metadata for field in required):
        raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    result = {field: metadata[field] for field in required}
    for field in ("link_sha256", "account_digest", "download_sha256"):
        if not isinstance(result[field], str) or not _SHA256_RE.fullmatch(
            result[field]
        ):
            raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    for field in (
        "bytes_downloaded",
        "zip_member_count",
        "conversations_member_count",
        "uncompressed_bytes",
    ):
        if type(result[field]) is not int or result[field] < 0:
            raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    if result["bytes_downloaded"] <= 0:
        raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    if not isinstance(result["downloaded_at"], str):
        raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    transport = result["transport"]
    if not isinstance(transport, dict) or set(transport) != {
        "content_type",
        "final_url_sha256",
        "redirect_count",
    }:
        raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    if not isinstance(transport["final_url_sha256"], str) or not _SHA256_RE.fullmatch(
        transport["final_url_sha256"]
    ):
        raise ChatGPTExportArchiveError("export_archive_download_metadata_invalid")
    return result


def _prepare_private_export(
    root: Path,
    state: dict[str, Any],
    private_zip: Path,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    request = _safe_request_metadata(state)
    request_id = request["request_id"]
    if metadata.get("request_id") != request_id:
        raise ChatGPTExportArchiveError("export_archive_request_mismatch")
    download = _safe_download_metadata(metadata)
    try:
        private_zip = private_zip.resolve(strict=True)
        private_stat = private_zip.lstat()
    except OSError as exc:
        raise ChatGPTExportArchiveError("export_archive_private_zip_invalid") from exc
    if (
        private_zip.is_symlink()
        or not stat.S_ISREG(private_stat.st_mode)
        or root == private_zip
        or root in private_zip.parents
    ):
        raise ChatGPTExportArchiveError("export_archive_private_zip_invalid")
    if private_stat.st_size != download["bytes_downloaded"]:
        raise ChatGPTExportArchiveError("export_archive_private_zip_size_mismatch")
    expected_name = f"chatgpt-export-{download['download_sha256']}.zip"
    if Path(str(metadata.get("relative_path") or "")).name != expected_name:
        raise ChatGPTExportArchiveError("export_archive_private_zip_identity_mismatch")
    return {
        "private_zip": private_zip,
        "request": request,
        "download": download,
        "request_metadata_sha256": _sha256_bytes(_canonical_bytes(request)),
        "private_download_metadata_sha256": _sha256_bytes(
            _canonical_bytes(metadata)
        ),
        "archive_id": _archive_id(download["download_sha256"]),
    }


def _download_history_evidence(state: dict[str, Any]) -> str:
    matches = [row for row in state.get("history", []) if row.get("to_state") == "DOWNLOADED"]
    if len(matches) != 1:
        raise ChatGPTExportArchiveError("export_archive_download_history_invalid")
    evidence = matches[0].get("evidence_sha256")
    if not isinstance(evidence, str) or not _SHA256_RE.fullmatch(evidence):
        raise ChatGPTExportArchiveError("export_archive_download_history_invalid")
    return evidence


def _public_index_payload(
    state: dict[str, Any],
    prepared: dict[str, Any],
    chunk_result: dict[str, Any],
    verification: dict[str, Any],
) -> dict[str, Any]:
    archive_id = prepared["archive_id"]
    request = prepared["request"]
    download = prepared["download"]
    payload = {
        "schema_version": PUBLIC_INDEX_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": SOURCE_ID,
        "archive_id": archive_id,
        "archive_path": (ARCHIVE_ROOT / archive_id).as_posix(),
        "export_batch_id": request["request_id"],
        "archive_manifest_sha256": verification["manifest_sha256"],
        "package_sha256": verification["package"]["sha256"],
        "package_bytes": verification["package"]["byte_size"],
        "part_count": verification["part_count"],
        "largest_part_bytes": chunk_result["largest_part_bytes"],
        "request_metadata": request,
        "request_metadata_sha256": prepared["request_metadata_sha256"],
        "download_metadata": download,
        "private_download_metadata_sha256": prepared[
            "private_download_metadata_sha256"
        ],
        "download_state": {
            "revision": state["revision"],
            "download_event_evidence_sha256": _download_history_evidence(state),
            "history_sha256": _sha256_bytes(_canonical_bytes({"history": state["history"]})),
        },
        "restore": {
            "verifier": "scripts/raw_archive_manifest.py verify",
            "verify_arguments": [
                "--database-dir",
                ".",
                "--source-id",
                SOURCE_ID,
                "--archive-id",
                archive_id,
            ],
            "ordered_part_hashes_required": True,
            "whole_package_hash_required": True,
        },
        "visibility": {
            "public_github_authorized": True,
            "raw_transcript_allowed": True,
            "private_path_public": False,
            "raw_account_or_url_public": False,
            "credential_values_public": False,
        },
        "raw_ledger_required": True,
        "source_mutation": False,
        "existing_archive_rewritten": False,
        "remote_push": False,
        "phase_boundary": PHASE_BOUNDARY,
    }
    return validate_public_index(payload)


def _walk_strings(value: Any):
    if isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from _walk_strings(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_strings(item)
    elif isinstance(value, str):
        yield value


def validate_public_index(payload: object) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != {
        "schema_version",
        "task_id",
        "acceptance_id",
        "source_id",
        "archive_id",
        "archive_path",
        "export_batch_id",
        "archive_manifest_sha256",
        "package_sha256",
        "package_bytes",
        "part_count",
        "largest_part_bytes",
        "request_metadata",
        "request_metadata_sha256",
        "download_metadata",
        "private_download_metadata_sha256",
        "download_state",
        "restore",
        "visibility",
        "raw_ledger_required",
        "source_mutation",
        "existing_archive_rewritten",
        "remote_push",
        "phase_boundary",
    }:
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    archive_id = payload.get("archive_id")
    request_id = payload.get("export_batch_id")
    if (
        payload.get("schema_version") != PUBLIC_INDEX_SCHEMA_VERSION
        or payload.get("task_id") != TASK_ID
        or payload.get("acceptance_id") != ACCEPTANCE_ID
        or payload.get("source_id") != SOURCE_ID
        or not isinstance(archive_id, str)
        or not _ARCHIVE_ID_RE.fullmatch(archive_id)
        or payload.get("archive_path") != (ARCHIVE_ROOT / archive_id).as_posix()
        or not isinstance(request_id, str)
        or not _REQUEST_ID_RE.fullmatch(request_id)
        or payload.get("phase_boundary") != PHASE_BOUNDARY
    ):
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    for field in (
        "archive_manifest_sha256",
        "package_sha256",
        "request_metadata_sha256",
        "private_download_metadata_sha256",
    ):
        if not isinstance(payload.get(field), str) or not _SHA256_RE.fullmatch(
            payload[field]
        ):
            raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    request = payload.get("request_metadata")
    download = payload.get("download_metadata")
    if (
        not isinstance(request, dict)
        or request.get("request_id") != request_id
        or _sha256_bytes(_canonical_bytes(request))
        != payload["request_metadata_sha256"]
        or not isinstance(download, dict)
        or download.get("download_sha256") != payload["package_sha256"]
        or download.get("bytes_downloaded") != payload["package_bytes"]
    ):
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    if type(payload.get("part_count")) is not int or payload["part_count"] < 1:
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    if (
        type(payload.get("largest_part_bytes")) is not int
        or not 0 < payload["largest_part_bytes"] <= MAX_PART_BYTES
    ):
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    visibility = payload.get("visibility")
    if visibility != {
        "public_github_authorized": True,
        "raw_transcript_allowed": True,
        "private_path_public": False,
        "raw_account_or_url_public": False,
        "credential_values_public": False,
    }:
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid")
    if any(
        marker in text
        for text in _walk_strings(payload)
        for marker in ("/Users/", "file://", "https://", "http://")
    ):
        raise ChatGPTExportArchiveError("export_archive_public_index_private_value")
    canonical = _canonical_bytes(payload)
    if len(canonical) > MAX_PUBLIC_INDEX_BYTES:
        raise ChatGPTExportArchiveError("export_archive_public_index_too_large")
    return dict(payload)


def _ensure_directory(root: Path, relative: Path) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except FileNotFoundError:
            try:
                current.mkdir(mode=0o700)
                metadata = current.lstat()
            except OSError as exc:
                raise ChatGPTExportArchiveError(
                    "export_archive_public_index_root_unavailable"
                ) from exc
        except OSError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_public_index_root_unavailable"
            ) from exc
        if current.is_symlink() or not stat.S_ISDIR(metadata.st_mode):
            raise ChatGPTExportArchiveError(
                "export_archive_public_index_root_unsafe"
            )
    return current


def _fsync_directory(path: Path) -> None:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
        os.fsync(descriptor)
    except OSError as exc:
        raise ChatGPTExportArchiveError(
            "export_archive_public_index_durability_unverified",
            writes_files=True,
            archive_may_exist=True,
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _write_or_verify_public_index(path: Path, payload: bytes) -> bool:
    if path.exists() or path.is_symlink():
        existing = _read_regular_bytes(
            path,
            maximum_bytes=MAX_PUBLIC_INDEX_BYTES,
            code="export_archive_public_index_conflict",
        )
        if existing != payload:
            raise ChatGPTExportArchiveError("export_archive_public_index_conflict")
        return True
    descriptor: int | None = None
    identity: os.stat_result | None = None
    try:
        descriptor = os.open(
            path,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            PUBLIC_INDEX_FILE_MODE,
        )
        identity = os.fstat(descriptor)
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise OSError("short public index write")
            view = view[written:]
        os.fsync(descriptor)
        os.close(descriptor)
        descriptor = None
        metadata = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_dev != identity.st_dev
            or metadata.st_ino != identity.st_ino
            or metadata.st_size != len(payload)
        ):
            raise OSError("public index identity changed")
        _fsync_directory(path.parent)
        return False
    except ChatGPTExportArchiveError:
        raise
    except OSError as exc:
        if descriptor is not None:
            os.close(descriptor)
        if identity is not None:
            try:
                current = path.lstat()
                if current.st_dev == identity.st_dev and current.st_ino == identity.st_ino:
                    path.unlink()
            except OSError:
                pass
        raise ChatGPTExportArchiveError(
            "export_archive_public_index_write_failed",
            writes_files=True,
            archive_may_exist=True,
        ) from exc


def _manifest_path(root: Path, request_id: str) -> Path:
    return root / RAW_MANIFEST_ROOT / f"raw_manifest.{_run_id(request_id)}.jsonl"


def _verify_registration(
    root: Path,
    relative: Path,
    payload: dict[str, Any],
    *,
    expected_state_evidence: str | None = None,
) -> dict[str, Any]:
    path = root / relative
    payload_bytes = _read_regular_bytes(
        path,
        maximum_bytes=MAX_PUBLIC_INDEX_BYTES,
        code="export_archive_public_index_missing",
    )
    try:
        loaded = json.loads(payload_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ChatGPTExportArchiveError("export_archive_public_index_invalid") from exc
    loaded = validate_public_index(loaded)
    if loaded != payload or payload_bytes != _canonical_bytes(payload):
        raise ChatGPTExportArchiveError("export_archive_public_index_mismatch")
    index_sha256 = _sha256_bytes(payload_bytes)
    if expected_state_evidence is not None and index_sha256 != expected_state_evidence:
        raise ChatGPTExportArchiveError("export_archive_state_evidence_mismatch")
    try:
        verification = verify_archive(root, SOURCE_ID, payload["archive_id"])
    except ArchiveRestoreError as exc:
        raise ChatGPTExportArchiveError("export_archive_verification_failed") from exc
    if (
        verification["manifest_sha256"] != payload["archive_manifest_sha256"]
        or verification["package"]["sha256"] != payload["package_sha256"]
        or verification["package"]["byte_size"] != payload["package_bytes"]
        or verification["part_count"] != payload["part_count"]
    ):
        raise ChatGPTExportArchiveError("export_archive_public_index_mismatch")
    try:
        ledger = preflight_raw_ledger(root)
    except ManifestConflict as exc:
        raise ChatGPTExportArchiveError("export_archive_raw_ledger_invalid") from exc
    request_id = payload["export_batch_id"]
    raw_manifest_path = _manifest_path(root, request_id)
    raw_manifest_bytes = _read_regular_bytes(
        raw_manifest_path,
        maximum_bytes=4 * 1024 * 1024,
        code="export_archive_raw_manifest_missing",
    )
    raw_ledger_bytes = _read_regular_bytes(
        root / RAW_LEDGER_RELATIVE,
        maximum_bytes=4 * 1024 * 1024,
        code="export_archive_raw_ledger_invalid",
    )
    if not raw_ledger_bytes.startswith(raw_manifest_bytes):
        raise ChatGPTExportArchiveError("export_archive_raw_manifest_ledger_mismatch")
    return {
        "verification": verification,
        "public_index_sha256": index_sha256,
        "raw_manifest_path": raw_manifest_path.relative_to(root).as_posix(),
        "raw_manifest_sha256": _sha256_bytes(raw_manifest_bytes),
        "raw_ledger_path": RAW_LEDGER_RELATIVE.as_posix(),
        "raw_ledger_verified": ledger["status"] == "PASS",
        "largest_part_bytes": payload["largest_part_bytes"],
    }


def _archived_state_evidence(state: dict[str, Any]) -> str:
    matches = [row for row in state.get("history", []) if row.get("to_state") == "ARCHIVED"]
    if len(matches) != 1:
        raise ChatGPTExportArchiveError("export_archive_state_history_invalid")
    evidence = matches[0].get("evidence_sha256")
    if not isinstance(evidence, str) or not _SHA256_RE.fullmatch(evidence):
        raise ChatGPTExportArchiveError("export_archive_state_history_invalid")
    return evidence


def _find_archived_registration(root: Path, state: dict[str, Any]) -> tuple[Path, dict[str, Any]]:
    request = _safe_request_metadata(state)
    request_id = request["request_id"]
    index_root = root / PUBLIC_INDEX_ROOT
    try:
        candidates = sorted(
            index_root.glob(f"chatgpt_raw_archive.chatgpt-export-*.{request_id}.json")
        )
    except OSError as exc:
        raise ChatGPTExportArchiveError("export_archive_public_index_missing") from exc
    if len(candidates) != 1 or len(candidates) > MAX_ARCHIVED_REGISTRATION_SCAN:
        raise ChatGPTExportArchiveError("export_archive_public_index_missing")
    path = candidates[0]
    payload = _read_json(
        path,
        maximum_bytes=MAX_PUBLIC_INDEX_BYTES,
        code="export_archive_public_index_invalid",
    )
    payload = validate_public_index(payload)
    return path.relative_to(root), payload


def _success_payload(
    *,
    action: str,
    export_state: str,
    eligible: bool,
    registration: dict[str, Any] | None = None,
    prepared: dict[str, Any] | None = None,
    chunk_result: dict[str, Any] | None = None,
    raw_manifest: dict[str, Any] | None = None,
    archive_idempotent: bool = False,
    public_index_idempotent: bool = False,
    private_reads: int = 0,
    raw_reads: int = 0,
    raw_writes: bool = False,
) -> dict[str, Any]:
    verification = registration["verification"] if registration else None
    return {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "action": action,
        "export_state": export_state,
        "eligible_for_archive": eligible,
        "archive_id": (
            verification["archive_id"]
            if verification
            else prepared["archive_id"] if prepared else None
        ),
        "archive_path": verification["archive_path"] if verification else None,
        "archive_manifest_sha256": (
            verification["manifest_sha256"] if verification else None
        ),
        "package_sha256": (
            verification["package"]["sha256"]
            if verification
            else prepared["download"]["download_sha256"] if prepared else None
        ),
        "package_bytes": (
            verification["package"]["byte_size"]
            if verification
            else prepared["download"]["bytes_downloaded"] if prepared else None
        ),
        "part_count": verification["part_count"] if verification else 0,
        "largest_part_bytes": (
            chunk_result["largest_part_bytes"]
            if chunk_result
            else registration.get("largest_part_bytes", 0)
            if registration
            else 0
        ),
        "public_index_path": (
            registration.get("public_index_path") if registration else None
        ),
        "public_index_sha256": (
            registration.get("public_index_sha256") if registration else None
        ),
        "raw_manifest_path": (
            registration.get("raw_manifest_path") if registration else None
        ),
        "raw_manifest_sha256": (
            registration.get("raw_manifest_sha256") if registration else None
        ),
        "raw_ledger_path": (
            registration.get("raw_ledger_path") if registration else None
        ),
        "archive_idempotent": archive_idempotent,
        "public_index_idempotent": public_index_idempotent,
        "raw_manifest_idempotent": (
            bool(raw_manifest.get("idempotent")) if raw_manifest else action == "ALREADY_ARCHIVED"
        ),
        "private_runtime_reads": private_reads,
        "raw_archive_reads": raw_reads,
        "raw_archive_writes": raw_writes,
        "source_mutation": False,
        "private_path_emitted": False,
        "account_or_link_value_emitted": False,
        "private_zip_committed": False,
        "remote_actions": False,
        "phase_boundary": PHASE_BOUNDARY,
    }


def _failure_payload(
    code: str,
    *,
    writes_files: bool = False,
    archive_may_exist: bool = False,
) -> dict[str, Any]:
    return {
        "status": "FAIL_CLOSED",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "error_code": code,
        "writes_files": writes_files,
        "archive_may_exist": archive_may_exist,
        "source_mutation": False,
        "private_path_emitted": False,
        "account_or_link_value_emitted": False,
        "private_zip_committed": False,
        "remote_actions": False,
    }


def _inspect_archived(root: Path, state: dict[str, Any]) -> dict[str, Any]:
    relative, payload = _find_archived_registration(root, state)
    registration = _verify_registration(
        root,
        relative,
        payload,
        expected_state_evidence=_archived_state_evidence(state),
    )
    registration["public_index_path"] = relative.as_posix()
    return _success_payload(
        action="ALREADY_ARCHIVED",
        export_state="ARCHIVED",
        eligible=True,
        registration=registration,
        archive_idempotent=True,
        public_index_idempotent=True,
        raw_reads=1,
    )


def inspect_export_archive(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    private_loader: PrivateLoader | None = None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_archive_contract(root)
    load_chatgpt_export_archive_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    state = load_chatgpt_export_state(root)
    if state["status"] not in {"DOWNLOADED", "ARCHIVED"}:
        return _success_payload(
            action="STATE_NOT_ELIGIBLE",
            export_state=state["status"],
            eligible=False,
        )
    if state["status"] == "ARCHIVED":
        return _inspect_archived(root, state)
    loader = private_loader or load_private_downloaded_export
    try:
        private_zip, metadata = loader(root, runtime_dir=runtime_dir)
    except ExportDownloadError as exc:
        raise ChatGPTExportArchiveError("export_archive_private_download_invalid") from exc
    prepared = _prepare_private_export(root, state, private_zip, metadata)
    return _success_payload(
        action="READY_TO_ARCHIVE",
        export_state="DOWNLOADED",
        eligible=True,
        prepared=prepared,
        private_reads=1,
    )


def archive_export(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    private_loader: PrivateLoader | None = None,
    state_writer: StateWriter = write_chatgpt_export_state,
    clock: Clock = _now_utc,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_archive_contract(root)
    load_chatgpt_export_archive_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    initial = load_chatgpt_export_state(root)
    if initial["status"] not in {"DOWNLOADED", "ARCHIVED"}:
        raise ChatGPTExportArchiveError("export_archive_state_not_eligible")
    loader = private_loader or load_private_downloaded_export
    with export_state_lock(root):
        state = load_chatgpt_export_state(root)
        if state["status"] == "ARCHIVED":
            return _inspect_archived(root, state)
        if state["status"] != "DOWNLOADED":
            raise ChatGPTExportArchiveError("export_archive_state_changed")
        try:
            private_zip, metadata = loader(root, runtime_dir=runtime_dir)
        except ExportDownloadError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_private_download_invalid"
            ) from exc
        prepared = _prepare_private_export(root, state, private_zip, metadata)
        request_id = prepared["request"]["request_id"]
        index_relative = _public_index_relative(prepared["archive_id"], request_id)
        index_path = root / index_relative
        if not index_path.exists() and not index_path.is_symlink():
            try:
                preflight_raw_ledger(root)
            except ManifestConflict as exc:
                raise ChatGPTExportArchiveError(
                    "export_archive_raw_ledger_preflight_failed"
                ) from exc
        try:
            chunk_result = chunk_archive_package(
                root,
                prepared["private_zip"],
                SOURCE_ID,
                prepared["archive_id"],
                force_archive=True,
            )
        except ArchiveChunkPartialWriteError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_partial_write_unverified",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        except ArchiveChunkPostPublishError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_durability_unverified",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        except ArchiveChunkError as exc:
            raise ChatGPTExportArchiveError("export_archive_chunk_failed") from exc
        try:
            verification = verify_archive(root, SOURCE_ID, prepared["archive_id"])
        except ArchiveRestoreError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_verification_failed",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        if (
            verification["package"]["sha256"]
            != prepared["download"]["download_sha256"]
            or verification["package"]["byte_size"]
            != prepared["download"]["bytes_downloaded"]
        ):
            raise ChatGPTExportArchiveError(
                "export_archive_package_identity_mismatch",
                writes_files=True,
                archive_may_exist=True,
            )
        index_payload = _public_index_payload(
            state,
            prepared,
            chunk_result,
            verification,
        )
        index_bytes = _canonical_bytes(index_payload)
        _ensure_directory(root, PUBLIC_INDEX_ROOT)
        public_index_idempotent = _write_or_verify_public_index(
            index_path,
            index_bytes,
        )
        try:
            raw_manifest = generate_raw_manifest(
                root,
                _run_id(request_id),
                imported_at=prepared["download"]["downloaded_at"],
                require_non_empty=False,
            )
        except ManifestConflict as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_raw_ledger_write_failed",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        registration = _verify_registration(root, index_relative, index_payload)
        registration["public_index_path"] = index_relative.as_posix()
        evidence_sha256 = registration["public_index_sha256"]
        archived_at = _utc_text(clock())
        try:
            updated, changed = apply_export_transition(
                state,
                to_state="ARCHIVED",
                event_id=f"archived-{request_id}",
                reason_code="official_export_archived",
                evidence_sha256=evidence_sha256,
                occurred_at=archived_at,
                expected_revision=state["revision"],
            )
            if changed:
                state_writer(root, updated)
        except ChatGPTExportStateError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_state_transition_failed",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        except OSError as exc:
            raise ChatGPTExportArchiveError(
                "export_archive_state_write_failed",
                writes_files=True,
                archive_may_exist=True,
            ) from exc
        return _success_payload(
            action="ARCHIVED",
            export_state="ARCHIVED",
            eligible=True,
            registration=registration,
            prepared=prepared,
            chunk_result=chunk_result,
            raw_manifest=raw_manifest,
            archive_idempotent=bool(chunk_result["idempotent"]),
            public_index_idempotent=public_index_idempotent,
            private_reads=1,
            raw_reads=1,
            raw_writes=True,
        )


def run_chatgpt_export_archive(args: Any) -> int:
    try:
        inspect = bool(getattr(args, "inspect", False))
        archive = bool(getattr(args, "archive", False))
        if int(inspect) + int(archive) != 1:
            raise ChatGPTExportArchiveError("export_archive_mode_invalid")
        if archive and not bool(getattr(args, "confirm_archive", False)):
            raise ChatGPTExportArchiveError(
                "export_archive_confirmation_required"
            )
        database_dir = Path(args.database_dir)
        runtime_dir = getattr(args, "runtime_dir", None)
        if inspect:
            payload = inspect_export_archive(
                database_dir,
                runtime_dir=runtime_dir,
            )
        else:
            payload = archive_export(
                database_dir,
                runtime_dir=runtime_dir,
            )
        print(
            json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 0
    except ChatGPTExportArchiveError as exc:
        payload = _failure_payload(
            exc.code,
            writes_files=exc.writes_files,
            archive_may_exist=exc.archive_may_exist,
        )
    except (ArchiveChunkError, ArchiveRestoreError, ChatGPTExportStateError):
        payload = _failure_payload("export_archive_execution_failed")
    except (OSError, UnicodeError, ValueError):
        payload = _failure_payload("export_archive_execution_failed")
    print(
        json.dumps(
            payload,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    )
    return 2


__all__ = (
    "ACCEPTANCE_ID",
    "ARCHIVE_ROOT",
    "CONTRACT_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "MODEL_RELATIVE",
    "PUBLIC_INDEX_ROOT",
    "TASK_ID",
    "ChatGPTExportArchiveError",
    "archive_export",
    "inspect_export_archive",
    "load_chatgpt_export_archive_contract",
    "load_chatgpt_export_archive_model_parameters",
    "run_chatgpt_export_archive",
    "validate_chatgpt_export_archive_contract",
    "validate_chatgpt_export_archive_model_parameters",
    "validate_public_index",
)
