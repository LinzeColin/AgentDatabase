"""Private, retryable download of a validated ChatGPT export ZIP."""

from __future__ import annotations

import hashlib
import ipaddress
import json
import os
import re
import secrets
import shutil
import socket
import stat
import time
import unicodedata
import zipfile
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any
from urllib import error as urllib_error
from urllib import request as urllib_request
from urllib.parse import urlsplit

from .chatgpt_export_link_discovery import (
    LinkDiscoveryError,
    load_private_export_account_binding,
    load_private_export_link,
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
from .chatgpt_notification_connector import (
    NotificationConnectorError,
    notification_runtime_directory,
)


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_download.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_download.v1_2_1_s08_p2_t3.json"
)
TASK_ID = "S08-P2-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P2-T3"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_download_contract.v1_2_1_s08_p2_t3"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_download_model.v1_2_1_s08_p2_t3"
)
PRIVATE_METADATA_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_private_download.v1_2_1_s08_p2_t3"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_download_result.v1_2_1_s08_p2_t3"
)
EVIDENCE_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_download_evidence.v1_2_1_s08_p2_t3"
)

DOWNLOAD_DIRECTORY_NAME = "chatgpt_exports"
DOWNLOAD_METADATA_FILENAME = "chatgpt_export_download.json"
DOWNLOAD_FILE_PREFIX = "chatgpt-export-"
DOWNLOAD_FILE_SUFFIX = ".zip"
PRIVATE_DIRECTORY_MODE = 0o700
PRIVATE_FILE_MODE = 0o600
MAX_CONTRACT_BYTES = 128 * 1024
MAX_PRIVATE_METADATA_BYTES = 64 * 1024
MAX_DOWNLOAD_BYTES = 2 * 1024 * 1024 * 1024
MAX_UNCOMPRESSED_BYTES = 16 * 1024 * 1024 * 1024
MAX_ZIP_MEMBERS = 200_000
MAX_ZIP_MEMBER_NAME_CHARS = 1024
MAX_COMPRESSION_RATIO = 1000
DOWNLOAD_CHUNK_BYTES = 1024 * 1024
DOWNLOAD_TIMEOUT_SECONDS = 30 * 60
SOCKET_TIMEOUT_SECONDS = 30
MAX_REDIRECTS = 5
MINIMUM_FREE_SPACE_RESERVE_BYTES = 512 * 1024 * 1024
ALLOWED_CONTENT_TYPES = (
    "",
    "application/octet-stream",
    "application/x-zip-compressed",
    "application/zip",
)
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_REQUEST_ID_RE = re.compile(r"^[0-9a-f]{32}$")
_CONVERSATIONS_MEMBER_RE = re.compile(
    r"^conversations(?:-\d+)?\.json$", re.IGNORECASE
)

PHASE_BOUNDARY = {
    "downloads_and_validates_private_export_zip": True,
    "writes_raw_archive": False,
    "parses_export": False,
    "commits_or_pushes": False,
    "deploys": False,
    "next_task": "S08-P3-T1",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "input": {
        "private_link_loader": "memory_atlas_cli.chatgpt_export_link_discovery:load_private_export_link",
        "private_account_binding_loader": "memory_atlas_cli.chatgpt_export_link_discovery:load_private_export_account_binding",
        "link_must_be_unexpired_at_start": True,
        "request_id_must_match_state": True,
        "salted_account_digest_must_match": True,
        "browser_session_or_cookie_read": False,
    },
    "state_gate": {
        "required_state": "LINK_READY",
        "success_state": "DOWNLOADED",
        "idempotent_state": "DOWNLOADED",
        "noneligible_state_reads_private_runtime": False,
        "state_lock_covers_download_and_transition": True,
    },
    "download": {
        "transport": "stdlib_https_get_without_ambient_cookie_auth_or_proxy",
        "https_only": True,
        "redirect_policy": "https_global_hostname_no_userinfo_no_ip_literal",
        "maximum_redirects": MAX_REDIRECTS,
        "socket_timeout_seconds": SOCKET_TIMEOUT_SECONDS,
        "total_timeout_seconds": DOWNLOAD_TIMEOUT_SECONDS,
        "chunk_bytes": DOWNLOAD_CHUNK_BYTES,
        "maximum_download_bytes": MAX_DOWNLOAD_BYTES,
        "minimum_free_space_reserve_bytes": MINIMUM_FREE_SPACE_RESERVE_BYTES,
        "content_type_allowlist": list(ALLOWED_CONTENT_TYPES),
        "retryable": True,
        "partial_file_removed_on_failure": True,
    },
    "zip_validation": {
        "crc_all_members": True,
        "maximum_members": MAX_ZIP_MEMBERS,
        "maximum_member_name_characters": MAX_ZIP_MEMBER_NAME_CHARS,
        "maximum_uncompressed_bytes": MAX_UNCOMPRESSED_BYTES,
        "maximum_compression_ratio": MAX_COMPRESSION_RATIO,
        "reject_encrypted_members": True,
        "reject_symlinks": True,
        "reject_unsafe_or_duplicate_paths": True,
        "require_conversations_json_or_numbered_variant": True,
        "extracts_members": False,
    },
    "private_store": {
        "location": "outside_repository",
        "directory": DOWNLOAD_DIRECTORY_NAME,
        "directory_mode_octal": "0700",
        "file_mode_octal": "0600",
        "filename_formula": "chatgpt-export-{zip_sha256}.zip",
        "metadata_filename": DOWNLOAD_METADATA_FILENAME,
        "downstream_loader": "memory_atlas_cli.chatgpt_export_download:load_private_downloaded_export",
        "atomic_publish_and_directory_fsync": True,
        "absolute_path_emitted": False,
        "download_url_in_metadata": False,
    },
    "deduplication": {
        "identity": "zip_sha256",
        "same_hash_creates_second_file": False,
        "state_write_failure_reuses_private_download": True,
        "network_retry_after_valid_private_download": False,
    },
    "cli": {
        "command": "chatgpt-export-download",
        "modes": ["--inspect", "--download --confirm-download"],
        "output_is_sanitized": True,
        "inspect_uses_network": False,
    },
    "security": {
        "browser_cookie_access": False,
        "browser_profile_access": False,
        "credential_access": False,
        "ambient_proxy_access": False,
        "one_time_url_emitted": False,
        "private_zip_in_repository": False,
        "raw_mutation": False,
        "remote_git_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S08-P2-T3",
    "formula_id": "FORM-MA-V121-S08-P2-T3",
    "purpose": "Download one unexpired account-bound export link into a private hash-addressed ZIP, validate it without extraction, and make retries idempotent.",
    "parameters": {
        "maximum_download_bytes": MAX_DOWNLOAD_BYTES,
        "maximum_uncompressed_bytes": MAX_UNCOMPRESSED_BYTES,
        "maximum_zip_members": MAX_ZIP_MEMBERS,
        "maximum_zip_member_name_characters": MAX_ZIP_MEMBER_NAME_CHARS,
        "maximum_compression_ratio": MAX_COMPRESSION_RATIO,
        "download_chunk_bytes": DOWNLOAD_CHUNK_BYTES,
        "download_timeout_seconds": DOWNLOAD_TIMEOUT_SECONDS,
        "socket_timeout_seconds": SOCKET_TIMEOUT_SECONDS,
        "maximum_redirects": MAX_REDIRECTS,
        "minimum_free_space_reserve_bytes": MINIMUM_FREE_SPACE_RESERVE_BYTES,
        "private_directory_mode_octal": "0700",
        "private_file_mode_octal": "0600",
        "repository_private_zip_bytes": 0,
        "repository_url_bytes": 0,
    },
    "formula": "downloaded = state=LINK_READY AND link_unexpired AND request_id_match AND salted_account_digest_match AND https_transport_safe AND bytes<=2GiB AND zip_crc_valid AND safe_unique_members AND conversations_member_count>=1; destination=private/chatgpt_exports/chatgpt-export-{sha256}.zip; duplicate_files_per_sha256<=1",
    "parameter_rationale": {
        "maximum_download_bytes": "Two GiB accommodates a large account export while bounding disk and network exposure.",
        "maximum_uncompressed_bytes": "Sixteen GiB permits ordinary export expansion but rejects unbounded archive bombs.",
        "maximum_compression_ratio": "A 1000:1 ceiling is deliberately generous for JSON and HTML while blocking pathological expansion.",
        "minimum_free_space_reserve_bytes": "A 512 MiB reserve prevents the private download from consuming the final operating-system headroom.",
        "download_timeout_seconds": "Thirty minutes bounds a large streamed export without relying only on per-socket timeouts.",
    },
    "failure_semantics": "Wrong state exits before private runtime or network access. Missing, expired or account-mismatched links, unsafe redirects, oversized responses, disk pressure, invalid ZIP structure or CRC, metadata conflict and concurrent state changes fail closed. Partial files are removed; a validated hash-addressed file survives a later metadata or state-write interruption and is reused on retry.",
    "calibration_boundary": "S08-P2-T3 stores and validates the private downloaded ZIP only. S08-P3-T1 owns public raw archive chunking, manifest and append-only publication; parsing, commit, push and real end-to-end proof remain later tasks.",
}


class ExportDownloadError(RuntimeError):
    """Path-free download error safe for sanitized machine output."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


Downloader = Callable[[str, Path], dict[str, object]]
Resolver = Callable[..., Sequence[tuple[Any, ...]]]


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as handle:
            for chunk in iter(lambda: handle.read(DOWNLOAD_CHUNK_BYTES), b""):
                digest.update(chunk)
    except OSError as exc:
        raise ExportDownloadError("export_download_private_file_unreadable") from exc
    return digest.hexdigest()


def _database_root(database_dir: Path) -> Path:
    candidate = Path(database_dir).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise ExportDownloadError("export_download_database_invalid")
    return candidate.resolve()


def _read_json(path: Path, *, maximum_bytes: int, code: str) -> dict[str, Any]:
    try:
        metadata = path.lstat()
        if (
            path.is_symlink()
            or not stat.S_ISREG(metadata.st_mode)
            or metadata.st_size > maximum_bytes
        ):
            raise ExportDownloadError(code)
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except ExportDownloadError:
        raise
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ExportDownloadError(code) from exc
    if not isinstance(payload, dict):
        raise ExportDownloadError(code)
    return payload


def validate_chatgpt_export_download_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise ExportDownloadError("export_download_contract_drift")
    return dict(payload)


def validate_chatgpt_export_download_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise ExportDownloadError("export_download_model_drift")
    return dict(payload)


def load_chatgpt_export_download_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_download_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="export_download_contract_unreadable",
        )
    )


def load_chatgpt_export_download_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_download_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="export_download_model_unreadable",
        )
    )


def _parse_utc(value: object, code: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ExportDownloadError(code)
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ExportDownloadError(code) from exc
    if parsed.tzinfo is None:
        raise ExportDownloadError(code)
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    if value.tzinfo is None:
        raise ExportDownloadError("export_download_clock_invalid")
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _safe_zip_member_name(name: str) -> bool:
    if (
        not name
        or len(name) > MAX_ZIP_MEMBER_NAME_CHARS
        or "\x00" in name
        or "\\" in name
        or name.startswith("/")
    ):
        return False
    raw_parts = name.split("/")
    if name.endswith("/"):
        raw_parts = raw_parts[:-1]
    if not raw_parts or any(part in {"", ".", ".."} for part in raw_parts):
        return False
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        return False
    return not (path.parts and ":" in path.parts[0])


def validate_downloaded_zip(path: Path) -> dict[str, int]:
    candidate = Path(path)
    try:
        metadata = candidate.lstat()
    except OSError as exc:
        raise ExportDownloadError("export_download_zip_unavailable") from exc
    if (
        candidate.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or metadata.st_size <= 0
        or metadata.st_size > MAX_DOWNLOAD_BYTES
    ):
        raise ExportDownloadError("export_download_zip_invalid")
    try:
        with zipfile.ZipFile(candidate) as archive:
            members = archive.infolist()
            if not members or len(members) > MAX_ZIP_MEMBERS:
                raise ExportDownloadError("export_download_zip_member_count_invalid")
            seen: set[str] = set()
            uncompressed_bytes = 0
            compressed_bytes = 0
            conversations_members = 0
            for member in members:
                name = member.filename
                if not _safe_zip_member_name(name):
                    raise ExportDownloadError("export_download_zip_member_unsafe")
                identity = unicodedata.normalize("NFC", name).casefold()
                if identity in seen:
                    raise ExportDownloadError("export_download_zip_member_duplicate")
                seen.add(identity)
                unix_mode = (member.external_attr >> 16) & 0o170000
                if unix_mode == stat.S_IFLNK:
                    raise ExportDownloadError("export_download_zip_symlink_forbidden")
                if member.flag_bits & 0x1:
                    raise ExportDownloadError("export_download_zip_encrypted_forbidden")
                if member.file_size < 0 or member.compress_size < 0:
                    raise ExportDownloadError("export_download_zip_size_invalid")
                uncompressed_bytes += member.file_size
                compressed_bytes += member.compress_size
                if uncompressed_bytes > MAX_UNCOMPRESSED_BYTES:
                    raise ExportDownloadError("export_download_zip_uncompressed_too_large")
                if (
                    member.file_size > 0
                    and member.compress_size == 0
                    and not member.is_dir()
                ):
                    raise ExportDownloadError("export_download_zip_ratio_invalid")
                if (
                    member.compress_size > 0
                    and member.file_size > member.compress_size * MAX_COMPRESSION_RATIO
                ):
                    raise ExportDownloadError("export_download_zip_ratio_invalid")
                if _CONVERSATIONS_MEMBER_RE.fullmatch(PurePosixPath(name).name):
                    conversations_members += 1
            if (
                compressed_bytes > 0
                and uncompressed_bytes > compressed_bytes * MAX_COMPRESSION_RATIO
            ):
                raise ExportDownloadError("export_download_zip_ratio_invalid")
            if conversations_members < 1:
                raise ExportDownloadError("export_download_conversations_missing")
            if archive.testzip() is not None:
                raise ExportDownloadError("export_download_zip_crc_invalid")
    except ExportDownloadError:
        raise
    except (OSError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile) as exc:
        raise ExportDownloadError("export_download_zip_invalid") from exc
    return {
        "zip_member_count": len(members),
        "conversations_member_count": conversations_members,
        "uncompressed_bytes": uncompressed_bytes,
    }


def _ensure_download_directory(runtime_directory: Path) -> Path:
    directory = runtime_directory / DOWNLOAD_DIRECTORY_NAME
    if directory.is_symlink():
        raise ExportDownloadError("export_download_private_directory_unsafe")
    try:
        directory.mkdir(mode=PRIVATE_DIRECTORY_MODE, exist_ok=True)
        os.chmod(directory, PRIVATE_DIRECTORY_MODE)
        metadata = directory.lstat()
    except OSError as exc:
        raise ExportDownloadError("export_download_private_directory_unavailable") from exc
    if (
        directory.is_symlink()
        or not stat.S_ISDIR(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != PRIVATE_DIRECTORY_MODE
    ):
        raise ExportDownloadError("export_download_private_directory_unsafe")
    try:
        if shutil.disk_usage(directory).free <= MINIMUM_FREE_SPACE_RESERVE_BYTES:
            raise ExportDownloadError("export_download_disk_reserve_insufficient")
    except OSError as exc:
        raise ExportDownloadError("export_download_disk_status_unavailable") from exc
    return directory


def _fsync_directory(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)
    except OSError as exc:
        raise ExportDownloadError("export_download_private_fsync_failed") from exc


def _write_private_metadata(
    runtime_directory: Path,
    payload: dict[str, Any],
) -> bool:
    content = _canonical_bytes(payload)
    if len(content) > MAX_PRIVATE_METADATA_BYTES:
        raise ExportDownloadError("export_download_metadata_too_large")
    path = runtime_directory / DOWNLOAD_METADATA_FILENAME
    if path.exists() or path.is_symlink():
        existing = _validate_private_metadata(
            _load_private_metadata_json(runtime_directory)
        )
        if existing != payload:
            raise ExportDownloadError("export_download_metadata_conflict")
        return False
    temporary = runtime_directory / (
        f".{DOWNLOAD_METADATA_FILENAME}.{secrets.token_hex(8)}.tmp"
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(temporary, flags, PRIVATE_FILE_MODE)
        try:
            with os.fdopen(descriptor, "wb", closefd=False) as handle:
                handle.write(content)
                handle.flush()
                os.fsync(handle.fileno())
        finally:
            os.close(descriptor)
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
        _fsync_directory(runtime_directory)
    except OSError as exc:
        try:
            temporary.unlink(missing_ok=True)
        except OSError:
            pass
        raise ExportDownloadError("export_download_metadata_write_failed") from exc
    return True


def _load_private_metadata_json(runtime_directory: Path) -> dict[str, Any]:
    path = runtime_directory / DOWNLOAD_METADATA_FILENAME
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise ExportDownloadError("export_download_metadata_unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(metadata.st_mode)
        or stat.S_IMODE(metadata.st_mode) != PRIVATE_FILE_MODE
    ):
        raise ExportDownloadError("export_download_metadata_unsafe")
    return _read_json(
        path,
        maximum_bytes=MAX_PRIVATE_METADATA_BYTES,
        code="export_download_metadata_invalid",
    )


def _validate_private_metadata(payload: object) -> dict[str, Any]:
    required = {
        "schema_version",
        "task_id",
        "request_id",
        "link_sha256",
        "account_digest",
        "download_sha256",
        "bytes_downloaded",
        "downloaded_at",
        "relative_path",
        "zip_member_count",
        "conversations_member_count",
        "uncompressed_bytes",
        "transport",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ExportDownloadError("export_download_metadata_invalid")
    if (
        payload["schema_version"] != PRIVATE_METADATA_SCHEMA_VERSION
        or payload["task_id"] != TASK_ID
        or not isinstance(payload["request_id"], str)
        or not _REQUEST_ID_RE.fullmatch(payload["request_id"])
    ):
        raise ExportDownloadError("export_download_metadata_invalid")
    for field in ("link_sha256", "account_digest", "download_sha256"):
        if not isinstance(payload[field], str) or not _SHA256_RE.fullmatch(payload[field]):
            raise ExportDownloadError("export_download_metadata_invalid")
    expected_relative = (
        f"{DOWNLOAD_DIRECTORY_NAME}/{DOWNLOAD_FILE_PREFIX}"
        f"{payload['download_sha256']}{DOWNLOAD_FILE_SUFFIX}"
    )
    if payload["relative_path"] != expected_relative:
        raise ExportDownloadError("export_download_metadata_invalid")
    numeric_bounds = {
        "bytes_downloaded": (1, MAX_DOWNLOAD_BYTES),
        "zip_member_count": (1, MAX_ZIP_MEMBERS),
        "conversations_member_count": (1, MAX_ZIP_MEMBERS),
        "uncompressed_bytes": (0, MAX_UNCOMPRESSED_BYTES),
    }
    for field, (minimum, maximum) in numeric_bounds.items():
        value = payload[field]
        if type(value) is not int or not minimum <= value <= maximum:
            raise ExportDownloadError("export_download_metadata_invalid")
    _parse_utc(payload["downloaded_at"], "export_download_metadata_invalid")
    transport = payload["transport"]
    if not isinstance(transport, dict) or set(transport) != {
        "content_type",
        "final_url_sha256",
        "redirect_count",
    }:
        raise ExportDownloadError("export_download_metadata_invalid")
    if (
        transport["content_type"] not in ALLOWED_CONTENT_TYPES
        or not isinstance(transport["final_url_sha256"], str)
        or not _SHA256_RE.fullmatch(transport["final_url_sha256"])
        or type(transport["redirect_count"]) is not int
        or not 0 <= transport["redirect_count"] <= MAX_REDIRECTS
    ):
        raise ExportDownloadError("export_download_metadata_invalid")
    return dict(payload)


def _validate_existing_download(
    runtime_directory: Path,
    metadata: Mapping[str, Any],
) -> dict[str, int]:
    relative = PurePosixPath(str(metadata["relative_path"]))
    if len(relative.parts) != 2 or relative.parts[0] != DOWNLOAD_DIRECTORY_NAME:
        raise ExportDownloadError("export_download_metadata_invalid")
    path = runtime_directory.joinpath(*relative.parts)
    try:
        file_metadata = path.lstat()
    except OSError as exc:
        raise ExportDownloadError("export_download_private_file_unavailable") from exc
    if (
        path.is_symlink()
        or not stat.S_ISREG(file_metadata.st_mode)
        or stat.S_IMODE(file_metadata.st_mode) != PRIVATE_FILE_MODE
        or file_metadata.st_size != metadata["bytes_downloaded"]
        or _sha256_file(path) != metadata["download_sha256"]
    ):
        raise ExportDownloadError("export_download_private_file_invalid")
    zip_evidence = validate_downloaded_zip(path)
    if any(
        zip_evidence[field] != metadata[field]
        for field in (
            "zip_member_count",
            "conversations_member_count",
            "uncompressed_bytes",
        )
    ):
        raise ExportDownloadError("export_download_metadata_file_mismatch")
    return zip_evidence


def _load_verified_metadata(
    runtime_directory: Path,
    *,
    request_id: str,
    link_sha256: str | None,
    account_digest: str | None,
) -> dict[str, Any]:
    metadata = _validate_private_metadata(
        _load_private_metadata_json(runtime_directory)
    )
    if metadata["request_id"] != request_id:
        raise ExportDownloadError("export_download_metadata_request_mismatch")
    if link_sha256 is not None and metadata["link_sha256"] != link_sha256:
        raise ExportDownloadError("export_download_metadata_link_mismatch")
    if account_digest is not None and metadata["account_digest"] != account_digest:
        raise ExportDownloadError("export_download_account_mismatch")
    _validate_existing_download(runtime_directory, metadata)
    return metadata


def _validate_global_https_url(value: str, *, resolver: Resolver) -> str:
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise ExportDownloadError("export_download_redirect_unsafe") from exc
    host = parsed.hostname
    if (
        parsed.scheme.casefold() != "https"
        or not host
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or parsed.fragment
    ):
        raise ExportDownloadError("export_download_redirect_unsafe")
    normalized = host.rstrip(".").casefold()
    if (
        normalized == "localhost"
        or normalized.endswith((".localhost", ".local", ".internal"))
    ):
        raise ExportDownloadError("export_download_redirect_unsafe")
    try:
        ipaddress.ip_address(normalized)
    except ValueError:
        pass
    else:
        raise ExportDownloadError("export_download_redirect_unsafe")
    try:
        addresses = resolver(normalized, 443, type=socket.SOCK_STREAM)
    except OSError as exc:
        raise ExportDownloadError("export_download_dns_failed") from exc
    if not addresses:
        raise ExportDownloadError("export_download_dns_failed")
    for row in addresses:
        try:
            address = ipaddress.ip_address(row[4][0])
        except (IndexError, TypeError, ValueError) as exc:
            raise ExportDownloadError("export_download_dns_invalid") from exc
        if not address.is_global:
            raise ExportDownloadError("export_download_redirect_unsafe")
    return value


class _SafeRedirectHandler(urllib_request.HTTPRedirectHandler):
    def __init__(self, resolver: Resolver) -> None:
        super().__init__()
        self.resolver = resolver
        self.redirect_count = 0

    def redirect_request(
        self,
        req: urllib_request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib_request.Request | None:
        self.redirect_count += 1
        if self.redirect_count > MAX_REDIRECTS:
            raise ExportDownloadError("export_download_too_many_redirects")
        _validate_global_https_url(newurl, resolver=self.resolver)
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is None:
            return None
        for header in ("Authorization", "Cookie", "Proxy-Authorization", "Referer"):
            redirected.remove_header(header)
        return redirected


def _download_https(
    url: str,
    destination: Path,
    *,
    resolver: Resolver = socket.getaddrinfo,
) -> dict[str, object]:
    _validate_global_https_url(url, resolver=resolver)
    redirect_handler = _SafeRedirectHandler(resolver)
    opener = urllib_request.build_opener(
        urllib_request.ProxyHandler({}),
        redirect_handler,
        urllib_request.HTTPSHandler(),
    )
    request = urllib_request.Request(
        url,
        headers={
            "Accept": "application/zip, application/octet-stream;q=0.9",
            "User-Agent": "MemoryAtlas-ChatGPT-Export/1.2.1",
        },
        method="GET",
    )
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    started = time.monotonic()
    try:
        writable_budget = (
            shutil.disk_usage(destination.parent).free
            - MINIMUM_FREE_SPACE_RESERVE_BYTES
        )
        if writable_budget <= 0:
            raise ExportDownloadError("export_download_disk_reserve_insufficient")
        response = opener.open(request, timeout=SOCKET_TIMEOUT_SECONDS)
        with response:
            status_code = response.getcode()
            if status_code != 200:
                raise ExportDownloadError("export_download_http_status_invalid")
            final_url = response.geturl()
            _validate_global_https_url(final_url, resolver=resolver)
            content_type = response.headers.get_content_type().casefold()
            if content_type not in ALLOWED_CONTENT_TYPES:
                raise ExportDownloadError("export_download_content_type_invalid")
            length_header = response.headers.get("Content-Length")
            if length_header is not None:
                try:
                    declared_length = int(length_header)
                except ValueError as exc:
                    raise ExportDownloadError("export_download_content_length_invalid") from exc
                if not 0 < declared_length <= MAX_DOWNLOAD_BYTES:
                    raise ExportDownloadError("export_download_content_length_invalid")
                if declared_length > writable_budget:
                    raise ExportDownloadError("export_download_disk_reserve_insufficient")
            descriptor = os.open(destination, flags, PRIVATE_FILE_MODE)
            bytes_downloaded = 0
            try:
                with os.fdopen(descriptor, "wb", closefd=False) as handle:
                    while True:
                        if time.monotonic() - started > DOWNLOAD_TIMEOUT_SECONDS:
                            raise ExportDownloadError("export_download_timeout")
                        chunk = response.read(DOWNLOAD_CHUNK_BYTES)
                        if not chunk:
                            break
                        bytes_downloaded += len(chunk)
                        if bytes_downloaded > MAX_DOWNLOAD_BYTES:
                            raise ExportDownloadError("export_download_too_large")
                        if bytes_downloaded > writable_budget:
                            raise ExportDownloadError(
                                "export_download_disk_reserve_insufficient"
                            )
                        handle.write(chunk)
                    handle.flush()
                    os.fsync(handle.fileno())
            finally:
                os.close(descriptor)
            if bytes_downloaded <= 0:
                raise ExportDownloadError("export_download_empty_response")
            if length_header is not None and bytes_downloaded != declared_length:
                raise ExportDownloadError("export_download_content_length_mismatch")
            os.chmod(destination, PRIVATE_FILE_MODE)
            return {
                "bytes_downloaded": bytes_downloaded,
                "content_type": content_type,
                "final_url_sha256": _sha256_bytes(final_url.encode("utf-8")),
                "redirect_count": redirect_handler.redirect_count,
            }
    except ExportDownloadError:
        raise
    except (
        OSError,
        TimeoutError,
        urllib_error.HTTPError,
        urllib_error.URLError,
        ValueError,
    ) as exc:
        raise ExportDownloadError("export_download_network_failed") from exc


def _validate_transport_result(
    payload: object,
    *,
    actual_bytes: int,
) -> dict[str, Any]:
    required = {
        "bytes_downloaded",
        "content_type",
        "final_url_sha256",
        "redirect_count",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise ExportDownloadError("export_download_transport_result_invalid")
    if (
        type(payload["bytes_downloaded"]) is not int
        or payload["bytes_downloaded"] != actual_bytes
        or not 0 < actual_bytes <= MAX_DOWNLOAD_BYTES
        or payload["content_type"] not in ALLOWED_CONTENT_TYPES
        or not isinstance(payload["final_url_sha256"], str)
        or not _SHA256_RE.fullmatch(payload["final_url_sha256"])
        or type(payload["redirect_count"]) is not int
        or not 0 <= payload["redirect_count"] <= MAX_REDIRECTS
    ):
        raise ExportDownloadError("export_download_transport_result_invalid")
    return dict(payload)


def _private_identity(
    root: Path,
    *,
    runtime_dir: Path | None,
    now: datetime,
    require_unexpired: bool = True,
) -> tuple[Path, dict[str, Any], dict[str, Any]]:
    try:
        link = load_private_export_link(
            root,
            runtime_dir=runtime_dir,
            now=now,
            require_unexpired=require_unexpired,
        )
        binding = load_private_export_account_binding(root, runtime_dir=runtime_dir)
        directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    except LinkDiscoveryError as exc:
        mapped = {
            "link_discovery_link_expired": "export_download_link_expired",
            "link_discovery_private_link_unavailable": "export_download_private_link_unavailable",
        }.get(exc.code, "export_download_private_identity_invalid")
        raise ExportDownloadError(mapped) from exc
    if binding["account_digest"] != link["account_digest"]:
        raise ExportDownloadError("export_download_account_mismatch")
    return directory, link, binding


def _evidence_payload(metadata: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "request_id_sha256": _sha256_bytes(metadata["request_id"].encode("ascii")),
        "link_sha256": metadata["link_sha256"],
        "download_sha256": metadata["download_sha256"],
        "bytes_downloaded": metadata["bytes_downloaded"],
        "zip_member_count": metadata["zip_member_count"],
        "conversations_member_count": metadata["conversations_member_count"],
        "account_binding_verified": True,
        "zip_crc_verified": True,
        "private_store_only": True,
    }


def _success_payload(
    *,
    action: str,
    export_state: str,
    eligible: bool,
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "action": action,
        "export_state": export_state,
        "eligible_for_download": eligible,
        "downloaded": metadata is not None,
        "account_binding_verified": metadata is not None,
        "zip_crc_verified": metadata is not None,
        "duplicate_private_files_created": 0,
        "one_time_url_emitted": False,
        "account_value_emitted": False,
        "credential_values_emitted": False,
        "private_path_emitted": False,
        "private_zip_in_repository": False,
        "raw_mutation": False,
        "remote_actions": False,
    }
    if metadata is not None:
        payload.update(
            {
                "download_sha256": metadata["download_sha256"],
                "bytes_downloaded": metadata["bytes_downloaded"],
                "zip_member_count": metadata["zip_member_count"],
                "conversations_member_count": metadata[
                    "conversations_member_count"
                ],
            }
        )
    return payload


def _failure_payload(code: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "error_code": code,
        "one_time_url_emitted": False,
        "account_value_emitted": False,
        "credential_values_emitted": False,
        "private_path_emitted": False,
        "private_zip_in_repository": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def inspect_export_download(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_download_contract(root)
    load_chatgpt_export_download_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    state = load_chatgpt_export_state(root)
    if state["status"] not in {"LINK_READY", "DOWNLOADED"}:
        return _success_payload(
            action="STATE_NOT_ELIGIBLE",
            export_state=state["status"],
            eligible=False,
            metadata=None,
        )
    request = state.get("request")
    if not isinstance(request, dict):
        raise ExportDownloadError("export_download_request_state_invalid")
    if state["status"] == "DOWNLOADED":
        directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
        metadata = _load_verified_metadata(
            directory,
            request_id=request["request_id"],
            link_sha256=None,
            account_digest=None,
        )
        return _success_payload(
            action="DOWNLOAD_VERIFIED",
            export_state="DOWNLOADED",
            eligible=True,
            metadata=metadata,
        )
    observed_now = datetime.now(timezone.utc) if now is None else now
    if observed_now.tzinfo is None:
        raise ExportDownloadError("export_download_clock_invalid")
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    metadata_path = directory / DOWNLOAD_METADATA_FILENAME
    directory, link, binding = _private_identity(
        root,
        runtime_dir=runtime_dir,
        now=observed_now,
        require_unexpired=not (metadata_path.exists() or metadata_path.is_symlink()),
    )
    if link["request_id"] != request["request_id"]:
        raise ExportDownloadError("export_download_request_mismatch")
    metadata = None
    action = "READY_TO_DOWNLOAD"
    if metadata_path.exists() or metadata_path.is_symlink():
        metadata = _load_verified_metadata(
            directory,
            request_id=request["request_id"],
            link_sha256=link["link_sha256"],
            account_digest=binding["account_digest"],
        )
        action = "DOWNLOAD_RECOVERY_READY"
    return _success_payload(
        action=action,
        export_state="LINK_READY",
        eligible=True,
        metadata=metadata,
    )


def load_private_downloaded_export(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
) -> tuple[Path, dict[str, Any]]:
    """Return the verified private ZIP to the next archive task without CLI output."""
    root = _database_root(database_dir)
    load_chatgpt_export_download_contract(root)
    load_chatgpt_export_download_model_parameters(root)
    state = load_chatgpt_export_state(root)
    request = state.get("request")
    if state["status"] != "DOWNLOADED" or not isinstance(request, dict):
        raise ExportDownloadError("export_download_not_ready_for_archive")
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    metadata = _load_verified_metadata(
        directory,
        request_id=request["request_id"],
        link_sha256=None,
        account_digest=None,
    )
    relative = PurePosixPath(metadata["relative_path"])
    return directory.joinpath(*relative.parts), metadata


def _transition_downloaded(
    root: Path,
    state: dict[str, Any],
    metadata: Mapping[str, Any],
) -> None:
    evidence_sha256 = _sha256_bytes(_canonical_bytes(_evidence_payload(metadata)))
    updated, changed = apply_export_transition(
        state,
        to_state="DOWNLOADED",
        event_id=f"downloaded-{metadata['request_id']}",
        reason_code="official_export_zip_downloaded",
        evidence_sha256=evidence_sha256,
        occurred_at=metadata["downloaded_at"],
        expected_revision=state["revision"],
    )
    if changed:
        write_chatgpt_export_state(root, updated)


def download_export_zip(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    downloader: Downloader = _download_https,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_download_contract(root)
    load_chatgpt_export_download_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    initial_state = load_chatgpt_export_state(root)
    if initial_state["status"] not in {"LINK_READY", "DOWNLOADED"}:
        raise ExportDownloadError("export_download_state_not_eligible")
    observed_now = datetime.now(timezone.utc) if now is None else now
    if observed_now.tzinfo is None:
        raise ExportDownloadError("export_download_clock_invalid")
    with export_state_lock(root):
        state = load_chatgpt_export_state(root)
        request = state.get("request")
        if not isinstance(request, dict):
            raise ExportDownloadError("export_download_request_state_invalid")
        if state["status"] == "DOWNLOADED":
            directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
            metadata = _load_verified_metadata(
                directory,
                request_id=request["request_id"],
                link_sha256=None,
                account_digest=None,
            )
            return _success_payload(
                action="ALREADY_DOWNLOADED",
                export_state="DOWNLOADED",
                eligible=True,
                metadata=metadata,
            )
        if state["status"] != "LINK_READY":
            raise ExportDownloadError("export_download_state_changed")
        directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
        metadata_path = directory / DOWNLOAD_METADATA_FILENAME
        directory, link, binding = _private_identity(
            root,
            runtime_dir=runtime_dir,
            now=observed_now,
            require_unexpired=not (
                metadata_path.exists() or metadata_path.is_symlink()
            ),
        )
        if link["request_id"] != request["request_id"]:
            raise ExportDownloadError("export_download_request_mismatch")
        if metadata_path.exists() or metadata_path.is_symlink():
            metadata = _load_verified_metadata(
                directory,
                request_id=request["request_id"],
                link_sha256=link["link_sha256"],
                account_digest=binding["account_digest"],
            )
            _transition_downloaded(root, state, metadata)
            return _success_payload(
                action="DOWNLOAD_ALREADY_STORED",
                export_state="DOWNLOADED",
                eligible=True,
                metadata=metadata,
            )
        download_directory = _ensure_download_directory(directory)
        temporary = download_directory / f".download-{secrets.token_hex(16)}.partial"
        promoted_path: Path | None = None
        try:
            try:
                transport_raw = downloader(link["url"], temporary)
            except ExportDownloadError:
                raise
            except (OSError, TimeoutError) as exc:
                raise ExportDownloadError("export_download_network_failed") from exc
            try:
                temporary_metadata = temporary.lstat()
            except OSError as exc:
                raise ExportDownloadError("export_download_transport_file_missing") from exc
            if temporary.is_symlink() or not stat.S_ISREG(temporary_metadata.st_mode):
                raise ExportDownloadError("export_download_transport_file_unsafe")
            os.chmod(temporary, PRIVATE_FILE_MODE)
            transport = _validate_transport_result(
                transport_raw,
                actual_bytes=temporary_metadata.st_size,
            )
            zip_evidence = validate_downloaded_zip(temporary)
            download_sha256 = _sha256_file(temporary)
            destination = download_directory / (
                f"{DOWNLOAD_FILE_PREFIX}{download_sha256}{DOWNLOAD_FILE_SUFFIX}"
            )
            if destination.exists() or destination.is_symlink():
                if (
                    destination.is_symlink()
                    or not destination.is_file()
                    or stat.S_IMODE(destination.stat().st_mode) != PRIVATE_FILE_MODE
                    or destination.stat().st_size != temporary_metadata.st_size
                    or _sha256_file(destination) != download_sha256
                ):
                    raise ExportDownloadError("export_download_hash_destination_conflict")
                temporary.unlink()
            else:
                os.replace(temporary, destination)
                os.chmod(destination, PRIVATE_FILE_MODE)
                _fsync_directory(download_directory)
            promoted_path = destination
            downloaded_at = _utc_text(observed_now)
            metadata = _validate_private_metadata(
                {
                    "schema_version": PRIVATE_METADATA_SCHEMA_VERSION,
                    "task_id": TASK_ID,
                    "request_id": request["request_id"],
                    "link_sha256": link["link_sha256"],
                    "account_digest": binding["account_digest"],
                    "download_sha256": download_sha256,
                    "bytes_downloaded": temporary_metadata.st_size,
                    "downloaded_at": downloaded_at,
                    "relative_path": (
                        f"{DOWNLOAD_DIRECTORY_NAME}/{destination.name}"
                    ),
                    "zip_member_count": zip_evidence["zip_member_count"],
                    "conversations_member_count": zip_evidence[
                        "conversations_member_count"
                    ],
                    "uncompressed_bytes": zip_evidence["uncompressed_bytes"],
                    "transport": {
                        "content_type": transport["content_type"],
                        "final_url_sha256": transport["final_url_sha256"],
                        "redirect_count": transport["redirect_count"],
                    },
                }
            )
            _write_private_metadata(directory, metadata)
            _transition_downloaded(root, state, metadata)
            return _success_payload(
                action="DOWNLOADED",
                export_state="DOWNLOADED",
                eligible=True,
                metadata=metadata,
            )
        except Exception:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass
            # A promoted hash-addressed ZIP is intentionally retained for retry.
            if promoted_path is not None and not promoted_path.exists():
                promoted_path = None
            raise


def run_chatgpt_export_download(args: Any) -> int:
    try:
        inspect = bool(getattr(args, "inspect", False))
        download = bool(getattr(args, "download", False))
        if int(inspect) + int(download) != 1:
            raise ExportDownloadError("export_download_mode_invalid")
        if download and not bool(getattr(args, "confirm_download", False)):
            raise ExportDownloadError("export_download_confirmation_required")
        database_dir = Path(args.database_dir)
        runtime_dir = getattr(args, "runtime_dir", None)
        if inspect:
            payload = inspect_export_download(
                database_dir,
                runtime_dir=runtime_dir,
            )
        else:
            payload = download_export_zip(
                database_dir,
                runtime_dir=runtime_dir,
            )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except ExportDownloadError as exc:
        code = exc.code
    except LinkDiscoveryError as exc:
        code = (
            "export_download_link_expired"
            if exc.code == "link_discovery_link_expired"
            else "export_download_private_identity_invalid"
        )
    except (ChatGPTExportStateError, NotificationConnectorError) as exc:
        code = exc.code
    except (OSError, UnicodeError, ValueError, zipfile.BadZipFile):
        code = "export_download_execution_failed"
    print(json.dumps(_failure_payload(code), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 2


__all__ = (
    "CONTRACT_RELATIVE",
    "DOWNLOAD_DIRECTORY_NAME",
    "DOWNLOAD_METADATA_FILENAME",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "ExportDownloadError",
    "MODEL_RELATIVE",
    "TASK_ID",
    "download_export_zip",
    "inspect_export_download",
    "load_chatgpt_export_download_contract",
    "load_chatgpt_export_download_model_parameters",
    "load_private_downloaded_export",
    "run_chatgpt_export_download",
    "validate_chatgpt_export_download_contract",
    "validate_chatgpt_export_download_model_parameters",
    "validate_downloaded_zip",
)
