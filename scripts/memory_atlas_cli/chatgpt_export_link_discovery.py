"""Privacy-safe discovery of official ChatGPT export download links."""

from __future__ import annotations

import hashlib
import html
import json
import os
import platform
import re
import secrets
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta, timezone
from email import policy
from email.parser import BytesParser
from email.utils import getaddresses, parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

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
    inspect_notification_connector,
    notification_runtime_directory,
)


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_export_link_discovery.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_export_link_discovery.v1_2_1_s08_p2_t2.json"
)
TASK_ID = "S08-P2-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P2-T2"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_link_discovery_contract.v1_2_1_s08_p2_t2"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_link_discovery_model.v1_2_1_s08_p2_t2"
)
ACCOUNT_BINDING_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_account_binding.v1_2_1_s08_p2_t2"
)
PRIVATE_LINK_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_private_link.v1_2_1_s08_p2_t2"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_link_discovery_result.v1_2_1_s08_p2_t2"
)
EVIDENCE_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_export_link_evidence.v1_2_1_s08_p2_t2"
)

ACCOUNT_ENVIRONMENT_VARIABLE = "MEMORY_ATLAS_CHATGPT_EXPORT_ACCOUNT"
ACCOUNT_BINDING_FILENAME = "chatgpt_export_account_binding.json"
PRIVATE_LINK_FILENAME = "chatgpt_export_link.json"
OFFICIAL_SENDERS = ("noreply@tm.openai.com",)
OFFICIAL_HOST_SUFFIXES = ("openai.com", "chatgpt.com")
SUBJECT_REQUIRED_MARKERS = ("chatgpt", "data", "export")
SUBJECT_READY_MARKERS = ("ready", "download")
LINK_REQUIRED_MARKERS = ("export", "download")
LINK_VALIDITY_SECONDS = 24 * 60 * 60
MAX_REQUEST_TO_NOTIFICATION_SECONDS = 7 * 24 * 60 * 60
MAIL_SCAN_LOOKBACK_SECONDS = LINK_VALIDITY_SECONDS + 5 * 60
MAX_CLOCK_SKEW_SECONDS = 5 * 60
MAIL_SCAN_TIMEOUT_SECONDS = 15
MAX_SCAN_MESSAGES = 8
MAX_MESSAGE_SOURCE_BYTES = 512 * 1024
MAX_SCAN_STDOUT_BYTES = (MAX_SCAN_MESSAGES * (MAX_MESSAGE_SOURCE_BYTES + 32)) + 64
MAX_TEXT_BODY_BYTES = 512 * 1024
MAX_URL_CHARS = 4096
MAX_CONTRACT_BYTES = 128 * 1024
MAX_PRIVATE_FILE_BYTES = 16 * 1024
PRIVATE_FILE_MODE = 0o600
RECORD_SEPARATOR = b"\x1e"
SAFE_CHILD_ENV_KEYS = (
    "HOME",
    "USER",
    "LOGNAME",
    "LANG",
    "LC_ALL",
    "TMPDIR",
    "__CF_USER_TEXT_ENCODING",
)
DEFAULT_APPLICATION_PATHS = (
    Path("/System/Applications/Mail.app"),
    Path("/Applications/Mail.app"),
)
DEFAULT_OSASCRIPT_PATH = Path("/usr/bin/osascript")
_EMAIL_RE = re.compile(r"^[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_HEX_32_RE = re.compile(r"^[0-9a-f]{32}$")
_PLAIN_URL_RE = re.compile(r"https://[^\s<>\"']+", re.IGNORECASE)

APPLE_MAIL_DISCOVERY_SCRIPT = (
    "on run",
    'set recordSeparator to ASCII character 30',
    "set cutoffDate to (current date) - 86700",
    'set outputText to ""',
    "set emittedCount to 0",
    'tell application "Mail"',
    "set recentMessages to every message of inbox whose date received is greater than or equal to cutoffDate",
    "repeat with mailMessage in recentMessages",
    "set senderText to sender of mailMessage as text",
    'if senderText contains "noreply@tm.openai.com" then',
    "set emittedCount to emittedCount + 1",
    "if emittedCount > 8 then",
    'set outputText to outputText & "TOO_MANY" & recordSeparator',
    "exit repeat",
    "end if",
    "set sourceText to source of mailMessage as text",
    "if (length of sourceText) > 524288 then",
    'set outputText to outputText & "OVERSIZE" & recordSeparator',
    "else if sourceText contains recordSeparator then",
    'set outputText to outputText & "UNSAFE" & recordSeparator',
    "else",
    'set outputText to outputText & "SOURCE" & linefeed & sourceText & recordSeparator',
    "end if",
    "end if",
    "end repeat",
    "end tell",
    'return outputText & "DONE"',
    "end run",
)

PHASE_BOUNDARY = {
    "discovers_official_export_notifications": True,
    "validates_account_time_and_state": True,
    "extracts_private_one_time_link": True,
    "downloads_export": False,
    "writes_raw_archive": False,
    "commits_or_pushes": False,
    "deploys": False,
    "next_task": "S08-P2-T3",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "official_source": {
        "documentation": "https://help.openai.com/en/articles/7260999-how-do-i-export-my-data",
        "sender_allowlist": list(OFFICIAL_SENDERS),
        "subject_required_markers": list(SUBJECT_REQUIRED_MARKERS),
        "subject_ready_any_of": list(SUBJECT_READY_MARKERS),
        "link_host_suffix_allowlist": list(OFFICIAL_HOST_SUFFIXES),
        "link_required_any_of": list(LINK_REQUIRED_MARKERS),
        "link_validity_seconds": LINK_VALIDITY_SECONDS,
        "maximum_request_to_notification_seconds": MAX_REQUEST_TO_NOTIFICATION_SECONDS,
    },
    "account_binding": {
        "input": f"environment:{ACCOUNT_ENVIRONMENT_VARIABLE}",
        "input_persisted": False,
        "stored_form": "random_salt_plus_sha256_of_normalized_account",
        "location": "outside_repository",
        "file_mode_octal": "0600",
        "message_recipient_must_match": True,
    },
    "mail_scan": {
        "adapter_id": "apple-mail-local",
        "read_only": True,
        "fixed_applescript": True,
        "shell": False,
        "timeout_seconds": MAIL_SCAN_TIMEOUT_SECONDS,
        "lookback_seconds": MAIL_SCAN_LOOKBACK_SECONDS,
        "maximum_messages": MAX_SCAN_MESSAGES,
        "maximum_message_source_bytes": MAX_MESSAGE_SOURCE_BYTES,
        "raw_source_retained": False,
        "raw_source_emitted": False,
    },
    "state_gate": {
        "required_state": "WAITING_FOR_EXPORT",
        "success_state": "LINK_READY",
        "request_time_source": "data/sync_state/chatgpt.json:request.reserved_at",
        "noneligible_state_scans_mail": False,
        "state_lock_required_before_write": True,
    },
    "private_link_store": {
        "location": "outside_repository",
        "filename": PRIVATE_LINK_FILENAME,
        "file_mode_octal": "0600",
        "atomic_replace_and_directory_fsync": True,
        "contains_one_time_url": True,
        "url_or_mail_content_emitted": False,
    },
    "cli": {
        "command": "chatgpt-export-link",
        "modes": ["--inspect", "--bind-account-from-env", "--discover"],
        "output_is_sanitized": True,
        "inspect_reads_mail": False,
    },
    "security": {
        "credentials_read": False,
        "mail_body_persisted": False,
        "account_value_persisted": False,
        "one_time_url_in_repository": False,
        "raw_mutation": False,
        "download": False,
        "remote_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-MA-V121-S08-P2-T2",
    "formula_id": "FORM-MA-V121-S08-P2-T2",
    "purpose": "Accept exactly one current official export notification only when state, sender, subject, bound recipient, request time and first-party HTTPS link all agree.",
    "parameters": {
        "link_validity_seconds": LINK_VALIDITY_SECONDS,
        "maximum_request_to_notification_seconds": MAX_REQUEST_TO_NOTIFICATION_SECONDS,
        "mail_scan_lookback_seconds": MAIL_SCAN_LOOKBACK_SECONDS,
        "maximum_clock_skew_seconds": MAX_CLOCK_SKEW_SECONDS,
        "mail_scan_timeout_seconds": MAIL_SCAN_TIMEOUT_SECONDS,
        "maximum_scan_messages": MAX_SCAN_MESSAGES,
        "maximum_message_source_bytes": MAX_MESSAGE_SOURCE_BYTES,
        "maximum_text_body_bytes": MAX_TEXT_BODY_BYTES,
        "maximum_url_characters": MAX_URL_CHARS,
        "account_value_bytes_persisted": 0,
        "mail_body_bytes_persisted": 0,
        "repository_url_bytes_persisted": 0,
    },
    "formula": "link_ready = export_state=WAITING_FOR_EXPORT AND one_valid_notification AND sender_allowlisted AND subject_ready AND recipient_digest=bound_account_digest AND request_reserved_at<=message_received_at<=request_reserved_at+7d AND now<=message_received_at+24h AND first_party_https_export_link; repository_url_bytes=0",
    "parameter_rationale": {
        "link_validity_seconds": "OpenAI documents that the email download link expires after 24 hours.",
        "maximum_request_to_notification_seconds": "OpenAI documents that an export can take up to seven days to arrive.",
        "mail_scan_lookback_seconds": "Only notifications whose 24-hour link can still be usable need content inspection; five minutes covers bounded clock skew.",
        "maximum_scan_messages": "Eight official-sender candidates is enough for one pending request while bounding ambiguity and Mail output.",
        "account_value_bytes_persisted": "The normalized account exists only in process memory; private runtime stores a random salt and digest.",
    },
    "failure_semantics": "Wrong state exits before Mail access. Missing account binding, unsupported sender, unready subject, recipient mismatch, out-of-window time, expired link, unsafe URL, oversized output or multiple valid candidates fails closed without persisting Mail content or emitting account/link values.",
    "calibration_boundary": "S08-P2-T2 discovers and stores one validated link outside Git. It does not download the ZIP, write raw archives, commit, push or deploy; those begin at S08-P2-T3 or later.",
}


class LinkDiscoveryError(RuntimeError):
    """Path-free discovery error safe for machine output."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


CommandRunner = Callable[..., subprocess.CompletedProcess[bytes]]
MailScanner = Callable[..., list[bytes]]
ConnectorInspector = Callable[..., dict[str, Any]]


def _canonical_bytes(payload: Mapping[str, Any]) -> bytes:
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _database_root(database_dir: Path) -> Path:
    candidate = Path(database_dir).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise LinkDiscoveryError("link_discovery_database_invalid")
    return candidate.resolve()


def _read_json(path: Path, *, maximum_bytes: int, code: str) -> dict[str, Any]:
    if path.is_symlink():
        raise LinkDiscoveryError(code)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise LinkDiscoveryError(code) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum_bytes:
            raise LinkDiscoveryError(code)
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(maximum_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > maximum_bytes:
        raise LinkDiscoveryError(code)
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise LinkDiscoveryError(code) from exc
    if not isinstance(payload, dict):
        raise LinkDiscoveryError(code)
    return payload


def validate_chatgpt_export_link_discovery_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise LinkDiscoveryError("link_discovery_contract_drift")
    return dict(payload)


def validate_chatgpt_export_link_discovery_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise LinkDiscoveryError("link_discovery_model_drift")
    return dict(payload)


def load_chatgpt_export_link_discovery_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_link_discovery_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="link_discovery_contract_unreadable",
        )
    )


def load_chatgpt_export_link_discovery_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_export_link_discovery_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="link_discovery_model_unreadable",
        )
    )


def _normalize_account(value: str) -> str:
    normalized = value.strip().casefold()
    if len(normalized) > 320 or not _EMAIL_RE.fullmatch(normalized):
        raise LinkDiscoveryError("link_discovery_account_invalid")
    local, domain = normalized.rsplit("@", 1)
    if not local or not domain or domain.startswith(".") or domain.endswith("."):
        raise LinkDiscoveryError("link_discovery_account_invalid")
    return normalized


def _account_digest(account: str, salt_hex: str) -> str:
    if not _HEX_32_RE.fullmatch(salt_hex):
        raise LinkDiscoveryError("link_discovery_account_binding_invalid")
    return _sha256_bytes(bytes.fromhex(salt_hex) + _normalize_account(account).encode("utf-8"))


def _validate_account_binding(payload: object) -> dict[str, Any]:
    required = {"schema_version", "algorithm", "salt_hex", "account_digest"}
    if not isinstance(payload, dict) or set(payload) != required:
        raise LinkDiscoveryError("link_discovery_account_binding_invalid")
    if (
        payload["schema_version"] != ACCOUNT_BINDING_SCHEMA_VERSION
        or payload["algorithm"] != "sha256_random_salt_normalized_email_v1"
        or not isinstance(payload["salt_hex"], str)
        or not _HEX_32_RE.fullmatch(payload["salt_hex"])
        or not isinstance(payload["account_digest"], str)
        or not _SHA256_RE.fullmatch(payload["account_digest"])
    ):
        raise LinkDiscoveryError("link_discovery_account_binding_invalid")
    return dict(payload)


def _load_private_json(directory: Path, filename: str, code: str) -> dict[str, Any]:
    path = directory / filename
    if path.is_symlink():
        raise LinkDiscoveryError(code)
    try:
        metadata = path.stat()
    except OSError as exc:
        raise LinkDiscoveryError(code) from exc
    if not stat.S_ISREG(metadata.st_mode) or stat.S_IMODE(metadata.st_mode) != PRIVATE_FILE_MODE:
        raise LinkDiscoveryError(code)
    return _read_json(path, maximum_bytes=MAX_PRIVATE_FILE_BYTES, code=code)


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_private_json(
    directory: Path,
    filename: str,
    payload: dict[str, Any],
    *,
    existing_validator: Callable[[object], dict[str, Any]],
    conflict_code: str,
) -> bool:
    path = directory / filename
    content = _canonical_bytes(payload)
    if len(content) > MAX_PRIVATE_FILE_BYTES:
        raise LinkDiscoveryError("link_discovery_private_payload_oversized")
    if path.exists() or path.is_symlink():
        existing = existing_validator(
            _load_private_json(directory, filename, conflict_code)
        )
        if existing == payload:
            return False
        raise LinkDiscoveryError(conflict_code)
    temporary = directory / f".{filename}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(temporary, flags, PRIVATE_FILE_MODE)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, PRIVATE_FILE_MODE)
        _fsync_directory(directory)
    except OSError as exc:
        raise LinkDiscoveryError("link_discovery_private_write_failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()
    return True


def bind_export_account(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    account: str,
    salt_hex: str | None = None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_link_discovery_contract(root)
    load_chatgpt_export_link_discovery_model_parameters(root)
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    normalized = _normalize_account(account)
    path = directory / ACCOUNT_BINDING_FILENAME
    if path.exists() or path.is_symlink():
        existing = _validate_account_binding(
            _load_private_json(
                directory,
                ACCOUNT_BINDING_FILENAME,
                "link_discovery_account_binding_invalid",
            )
        )
        if _account_digest(normalized, existing["salt_hex"]) != existing["account_digest"]:
            raise LinkDiscoveryError("link_discovery_account_binding_conflict")
        changed = False
    else:
        chosen_salt = secrets.token_hex(16) if salt_hex is None else salt_hex
        payload = _validate_account_binding(
            {
                "schema_version": ACCOUNT_BINDING_SCHEMA_VERSION,
                "algorithm": "sha256_random_salt_normalized_email_v1",
                "salt_hex": chosen_salt,
                "account_digest": _account_digest(normalized, chosen_salt),
            }
        )
        changed = _write_private_json(
            directory,
            ACCOUNT_BINDING_FILENAME,
            payload,
            existing_validator=_validate_account_binding,
            conflict_code="link_discovery_account_binding_conflict",
        )
    return _success_payload(
        action="ACCOUNT_BOUND" if changed else "ACCOUNT_ALREADY_BOUND",
        export_state=None,
        eligible=False,
        link_fields=None,
    )


def _safe_child_env(environ: Mapping[str, str] | None) -> dict[str, str]:
    source = os.environ if environ is None else environ
    return {
        key: value
        for key in SAFE_CHILD_ENV_KEYS
        if isinstance((value := source.get(key)), str) and value
    }


def _apple_mail_argv(osascript_path: Path) -> list[str]:
    argv = [str(osascript_path)]
    for line in APPLE_MAIL_DISCOVERY_SCRIPT:
        argv.extend(("-e", line))
    return argv


def scan_apple_mail_sources(
    *,
    runner: CommandRunner = subprocess.run,
    system_name: str | None = None,
    application_paths: Sequence[Path] = DEFAULT_APPLICATION_PATHS,
    osascript_path: Path = DEFAULT_OSASCRIPT_PATH,
    environ: Mapping[str, str] | None = None,
) -> list[bytes]:
    if (platform.system() if system_name is None else system_name) != "Darwin":
        raise LinkDiscoveryError("link_discovery_platform_unsupported")
    if not any(Path(path).is_dir() and not Path(path).is_symlink() for path in application_paths):
        raise LinkDiscoveryError("link_discovery_mail_unavailable")
    executable = Path(osascript_path)
    if executable.is_symlink() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise LinkDiscoveryError("link_discovery_osascript_unavailable")
    try:
        result = runner(
            _apple_mail_argv(executable),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=MAIL_SCAN_TIMEOUT_SECONDS,
            shell=False,
            env=_safe_child_env(environ),
        )
    except subprocess.TimeoutExpired as exc:
        raise LinkDiscoveryError("link_discovery_mail_timeout") from exc
    except OSError as exc:
        raise LinkDiscoveryError("link_discovery_mail_failed") from exc
    if result.returncode != 0:
        raise LinkDiscoveryError("link_discovery_mail_failed")
    stdout = result.stdout
    if not isinstance(stdout, bytes) or len(stdout) > MAX_SCAN_STDOUT_BYTES:
        raise LinkDiscoveryError("link_discovery_mail_response_invalid")
    records = stdout.rstrip(b"\r\n").split(RECORD_SEPARATOR)
    if not records or records[-1] != b"DONE":
        raise LinkDiscoveryError("link_discovery_mail_response_invalid")
    sources: list[bytes] = []
    for record in records[:-1]:
        if record in {b"TOO_MANY", b"OVERSIZE", b"UNSAFE"}:
            raise LinkDiscoveryError("link_discovery_mail_response_invalid")
        if not record.startswith(b"SOURCE\n"):
            raise LinkDiscoveryError("link_discovery_mail_response_invalid")
        source = record[len(b"SOURCE\n") :]
        if not source or len(source) > MAX_MESSAGE_SOURCE_BYTES:
            raise LinkDiscoveryError("link_discovery_mail_response_invalid")
        sources.append(source)
    if len(sources) > MAX_SCAN_MESSAGES:
        raise LinkDiscoveryError("link_discovery_mail_response_invalid")
    return sources


class _HrefCollector(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.urls: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.casefold() != "a":
            return
        for key, value in attrs:
            if key.casefold() == "href" and isinstance(value, str):
                self.urls.append(value)


def _message_text_and_urls(source: bytes) -> tuple[Any, str, list[str]]:
    if not source or len(source) > MAX_MESSAGE_SOURCE_BYTES or RECORD_SEPARATOR in source:
        raise LinkDiscoveryError("link_discovery_message_invalid")
    try:
        message = BytesParser(policy=policy.default).parsebytes(source)
    except Exception as exc:
        raise LinkDiscoveryError("link_discovery_message_invalid") from exc
    if message.defects:
        raise LinkDiscoveryError("link_discovery_message_invalid")
    texts: list[str] = []
    urls: list[str] = []
    consumed = 0
    for part in message.walk():
        if part.is_multipart() or part.get_content_type() not in {"text/plain", "text/html"}:
            continue
        payload = part.get_payload(decode=True)
        if payload is None:
            raw = part.get_payload()
            payload = raw.encode("utf-8") if isinstance(raw, str) else b""
        if not isinstance(payload, bytes):
            raise LinkDiscoveryError("link_discovery_message_invalid")
        consumed += len(payload)
        if consumed > MAX_TEXT_BODY_BYTES:
            raise LinkDiscoveryError("link_discovery_message_oversized")
        charset = part.get_content_charset() or "utf-8"
        try:
            text = payload.decode(charset, errors="strict")
        except (LookupError, UnicodeDecodeError) as exc:
            raise LinkDiscoveryError("link_discovery_message_invalid") from exc
        texts.append(text)
        urls.extend(html.unescape(url) for url in _PLAIN_URL_RE.findall(text))
        if part.get_content_type() == "text/html":
            collector = _HrefCollector()
            try:
                collector.feed(text)
            except Exception as exc:
                raise LinkDiscoveryError("link_discovery_message_invalid") from exc
            urls.extend(html.unescape(url) for url in collector.urls)
    return message, "\n".join(texts), urls


def _validate_official_url(value: str) -> str:
    candidate = value.strip().rstrip(".,);]")
    if not candidate or len(candidate) > MAX_URL_CHARS:
        raise LinkDiscoveryError("link_discovery_url_invalid")
    try:
        parsed = urlsplit(candidate)
        port = parsed.port
    except ValueError as exc:
        raise LinkDiscoveryError("link_discovery_url_invalid") from exc
    host = (parsed.hostname or "").casefold().rstrip(".")
    host_allowed = any(host == suffix or host.endswith(f".{suffix}") for suffix in OFFICIAL_HOST_SUFFIXES)
    marker_text = f"{parsed.path}?{parsed.query}".casefold()
    if (
        parsed.scheme.casefold() != "https"
        or not host_allowed
        or parsed.username is not None
        or parsed.password is not None
        or port not in {None, 443}
        or bool(parsed.fragment)
        or not any(marker in marker_text for marker in LINK_REQUIRED_MARKERS)
    ):
        raise LinkDiscoveryError("link_discovery_url_invalid")
    return candidate


def _parse_utc(value: str, code: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (TypeError, ValueError) as exc:
        raise LinkDiscoveryError(code) from exc
    if parsed.tzinfo is None:
        raise LinkDiscoveryError(code)
    return parsed.astimezone(timezone.utc)


def _utc_text(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _recipient_matches(message: Any, binding: Mapping[str, Any]) -> bool:
    raw_headers: list[str] = []
    for name in ("to", "delivered-to", "x-original-to"):
        raw_headers.extend(str(value) for value in message.get_all(name, []))
    addresses = {address.casefold() for _, address in getaddresses(raw_headers) if address}
    return any(
        _EMAIL_RE.fullmatch(address)
        and _account_digest(address, str(binding["salt_hex"])) == binding["account_digest"]
        for address in addresses
    )


def validate_notification_source(
    source: bytes,
    *,
    account_binding: Mapping[str, Any],
    request_reserved_at: str,
    now: datetime,
) -> dict[str, Any]:
    binding = _validate_account_binding(account_binding)
    if now.tzinfo is None:
        raise LinkDiscoveryError("link_discovery_clock_invalid")
    current = now.astimezone(timezone.utc)
    request_time = _parse_utc(request_reserved_at, "link_discovery_request_time_invalid")
    message, body_text, urls = _message_text_and_urls(source)
    senders = getaddresses([str(message.get("from", ""))])
    sender_addresses = [address.casefold() for _, address in senders if address]
    if sender_addresses != list(OFFICIAL_SENDERS):
        raise LinkDiscoveryError("link_discovery_sender_invalid")
    subject = " ".join(str(message.get("subject", "")).casefold().split())
    if (
        not all(marker in subject for marker in SUBJECT_REQUIRED_MARKERS)
        or not any(marker in subject for marker in SUBJECT_READY_MARKERS)
    ):
        raise LinkDiscoveryError("link_discovery_status_invalid")
    if not _recipient_matches(message, binding):
        raise LinkDiscoveryError("link_discovery_account_mismatch")
    try:
        received = parsedate_to_datetime(str(message.get("date", "")))
    except (TypeError, ValueError) as exc:
        raise LinkDiscoveryError("link_discovery_message_time_invalid") from exc
    if received is None or received.tzinfo is None:
        raise LinkDiscoveryError("link_discovery_message_time_invalid")
    received = received.astimezone(timezone.utc)
    if received < request_time or received > request_time + timedelta(seconds=MAX_REQUEST_TO_NOTIFICATION_SECONDS):
        raise LinkDiscoveryError("link_discovery_message_time_invalid")
    if received > current + timedelta(seconds=MAX_CLOCK_SKEW_SECONDS):
        raise LinkDiscoveryError("link_discovery_message_time_invalid")
    expires = received + timedelta(seconds=LINK_VALIDITY_SECONDS)
    if current >= expires:
        raise LinkDiscoveryError("link_discovery_link_expired")
    normalized_body = " ".join(body_text.casefold().split())
    if "download" not in normalized_body or "data export" not in normalized_body:
        raise LinkDiscoveryError("link_discovery_status_invalid")
    valid_urls: list[str] = []
    for value in dict.fromkeys(urls):
        try:
            valid_urls.append(_validate_official_url(value))
        except LinkDiscoveryError:
            continue
    valid_urls = list(dict.fromkeys(valid_urls))
    if len(valid_urls) != 1:
        raise LinkDiscoveryError(
            "link_discovery_url_ambiguous" if valid_urls else "link_discovery_url_invalid"
        )
    link = valid_urls[0]
    return {
        "url": link,
        "link_sha256": _sha256_bytes(link.encode("utf-8")),
        "source_sha256": _sha256_bytes(source),
        "received_at": _utc_text(received),
        "expires_at": _utc_text(expires),
        "account_digest": binding["account_digest"],
    }


def _validate_private_link(payload: object) -> dict[str, Any]:
    required = {
        "schema_version",
        "task_id",
        "request_id",
        "url",
        "link_sha256",
        "source_sha256",
        "received_at",
        "expires_at",
        "account_digest",
        "stored_at",
    }
    if not isinstance(payload, dict) or set(payload) != required:
        raise LinkDiscoveryError("link_discovery_private_link_invalid")
    if (
        payload["schema_version"] != PRIVATE_LINK_SCHEMA_VERSION
        or payload["task_id"] != TASK_ID
        or not isinstance(payload["request_id"], str)
        or not re.fullmatch(r"[0-9a-f]{32}", payload["request_id"])
        or not isinstance(payload["url"], str)
        or _validate_official_url(payload["url"]) != payload["url"]
    ):
        raise LinkDiscoveryError("link_discovery_private_link_invalid")
    for field in ("link_sha256", "source_sha256", "account_digest"):
        if not isinstance(payload[field], str) or not _SHA256_RE.fullmatch(payload[field]):
            raise LinkDiscoveryError("link_discovery_private_link_invalid")
    if _sha256_bytes(payload["url"].encode("utf-8")) != payload["link_sha256"]:
        raise LinkDiscoveryError("link_discovery_private_link_invalid")
    _parse_utc(payload["received_at"], "link_discovery_private_link_invalid")
    _parse_utc(payload["expires_at"], "link_discovery_private_link_invalid")
    _parse_utc(payload["stored_at"], "link_discovery_private_link_invalid")
    return dict(payload)


def _load_account_binding(directory: Path) -> dict[str, Any]:
    return _validate_account_binding(
        _load_private_json(
            directory,
            ACCOUNT_BINDING_FILENAME,
            "link_discovery_account_binding_unavailable",
        )
    )


def load_private_export_account_binding(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
) -> dict[str, Any]:
    """Load the salted private account binding for the T3 identity check."""
    root = _database_root(database_dir)
    load_chatgpt_export_link_discovery_contract(root)
    load_chatgpt_export_link_discovery_model_parameters(root)
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    return _load_account_binding(directory)


def load_private_export_link(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    now: datetime | None = None,
    require_unexpired: bool = True,
) -> dict[str, Any]:
    """Load the validated URL for T3 without emitting it through the CLI."""
    root = _database_root(database_dir)
    load_chatgpt_export_link_discovery_contract(root)
    load_chatgpt_export_link_discovery_model_parameters(root)
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    payload = _validate_private_link(
        _load_private_json(
            directory,
            PRIVATE_LINK_FILENAME,
            "link_discovery_private_link_unavailable",
        )
    )
    current = datetime.now(timezone.utc) if now is None else now
    if current.tzinfo is None:
        raise LinkDiscoveryError("link_discovery_clock_invalid")
    if type(require_unexpired) is not bool:
        raise LinkDiscoveryError("link_discovery_expiry_policy_invalid")
    if require_unexpired and current.astimezone(timezone.utc) >= _parse_utc(
        payload["expires_at"], "link_discovery_private_link_invalid"
    ):
        raise LinkDiscoveryError("link_discovery_link_expired")
    return payload


def _success_payload(
    *,
    action: str,
    export_state: str | None,
    eligible: bool,
    link_fields: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "action": action,
        "export_state": export_state,
        "eligible_for_discovery": eligible,
        "account_value_emitted": False,
        "mail_values_emitted": False,
        "one_time_url_emitted": False,
        "credential_values_emitted": False,
        "configuration_path_emitted": False,
        "repository_url_persisted": False,
        "mail_body_persisted": False,
        "raw_mutation": False,
        "downloaded": False,
        "remote_actions": False,
    }
    if link_fields is not None:
        payload.update(
            {
                "link_sha256": link_fields["link_sha256"],
                "received_at": link_fields["received_at"],
                "expires_at": link_fields["expires_at"],
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
        "account_value_emitted": False,
        "mail_values_emitted": False,
        "one_time_url_emitted": False,
        "credential_values_emitted": False,
        "configuration_path_emitted": False,
        "repository_url_persisted": False,
        "mail_body_persisted": False,
        "raw_mutation": False,
        "downloaded": False,
        "remote_actions": False,
    }


def inspect_export_link_discovery(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_link_discovery_contract(root)
    load_chatgpt_export_link_discovery_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    state = load_chatgpt_export_state(root)
    if state["status"] != "WAITING_FOR_EXPORT":
        return _success_payload(
            action="STATE_NOT_ELIGIBLE",
            export_state=state["status"],
            eligible=False,
            link_fields=None,
        )
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    _load_account_binding(directory)
    return _success_payload(
        action="READY_TO_DISCOVER",
        export_state=state["status"],
        eligible=True,
        link_fields=None,
    )


def discover_export_link(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    scanner: MailScanner = scan_apple_mail_sources,
    connector_inspector: ConnectorInspector = inspect_notification_connector,
    now: datetime | None = None,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_export_link_discovery_contract(root)
    load_chatgpt_export_link_discovery_model_parameters(root)
    load_chatgpt_export_state_contract(root)
    load_chatgpt_export_state_model_parameters(root)
    initial_state = load_chatgpt_export_state(root)
    if initial_state["status"] != "WAITING_FOR_EXPORT":
        raise LinkDiscoveryError("link_discovery_state_not_eligible")
    request = initial_state.get("request")
    if not isinstance(request, dict) or request.get("dispatch_status") != "DISPATCHED":
        raise LinkDiscoveryError("link_discovery_request_state_invalid")
    directory = notification_runtime_directory(root, runtime_dir=runtime_dir)
    binding = _load_account_binding(directory)
    connector_result = connector_inspector(root, runtime_dir=runtime_dir)
    if connector_result.get("real_adapter_ready") is not True:
        raise LinkDiscoveryError("link_discovery_connector_not_ready")
    observed_now = datetime.now(timezone.utc) if now is None else now
    sources = scanner()
    valid: list[dict[str, Any]] = []
    for source in sources:
        try:
            valid.append(
                validate_notification_source(
                    source,
                    account_binding=binding,
                    request_reserved_at=request["reserved_at"],
                    now=observed_now,
                )
            )
        except LinkDiscoveryError:
            continue
    if len(valid) != 1:
        raise LinkDiscoveryError(
            "link_discovery_notification_ambiguous"
            if len(valid) > 1
            else "link_discovery_notification_not_found"
        )
    candidate = valid[0]
    evidence = {
        "schema_version": EVIDENCE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "request_id_sha256": _sha256_bytes(request["request_id"].encode("ascii")),
        "source_sha256": candidate["source_sha256"],
        "link_sha256": candidate["link_sha256"],
        "received_at": candidate["received_at"],
        "expires_at": candidate["expires_at"],
        "account_match": True,
        "sender_match": True,
        "status_match": True,
        "time_match": True,
    }
    evidence_sha256 = _sha256_bytes(_canonical_bytes(evidence))
    stored_at = _utc_text(observed_now)
    private_payload = _validate_private_link(
        {
            "schema_version": PRIVATE_LINK_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "request_id": request["request_id"],
            "url": candidate["url"],
            "link_sha256": candidate["link_sha256"],
            "source_sha256": candidate["source_sha256"],
            "received_at": candidate["received_at"],
            "expires_at": candidate["expires_at"],
            "account_digest": candidate["account_digest"],
            "stored_at": stored_at,
        }
    )
    private_path = directory / PRIVATE_LINK_FILENAME
    if private_path.exists() or private_path.is_symlink():
        existing_private = _validate_private_link(
            _load_private_json(
                directory,
                PRIVATE_LINK_FILENAME,
                "link_discovery_private_link_invalid",
            )
        )
        comparable_fields = set(private_payload) - {"stored_at"}
        if any(existing_private[field] != private_payload[field] for field in comparable_fields):
            raise LinkDiscoveryError("link_discovery_private_link_conflict")
        private_payload = existing_private
    with export_state_lock(root):
        current = load_chatgpt_export_state(root)
        if (
            current["status"] != "WAITING_FOR_EXPORT"
            or current["revision"] != initial_state["revision"]
            or current["request"] != request
        ):
            raise LinkDiscoveryError("link_discovery_state_changed")
        stored = _write_private_json(
            directory,
            PRIVATE_LINK_FILENAME,
            private_payload,
            existing_validator=_validate_private_link,
            conflict_code="link_discovery_private_link_conflict",
        )
        updated, state_changed = apply_export_transition(
            current,
            to_state="LINK_READY",
            event_id=f"link-ready-{request['request_id']}",
            reason_code="official_export_link_verified",
            evidence_sha256=evidence_sha256,
            occurred_at=stored_at,
            expected_revision=current["revision"],
        )
        if state_changed:
            write_chatgpt_export_state(root, updated)
    return _success_payload(
        action="LINK_STORED" if stored else "LINK_ALREADY_STORED",
        export_state="LINK_READY",
        eligible=True,
        link_fields=candidate,
    )


def run_chatgpt_export_link_discovery(args: Any) -> int:
    try:
        inspect = bool(getattr(args, "inspect", False))
        bind = bool(getattr(args, "bind_account_from_env", False))
        discover = bool(getattr(args, "discover", False))
        if int(inspect) + int(bind) + int(discover) != 1:
            raise LinkDiscoveryError("link_discovery_mode_invalid")
        database_dir = Path(args.database_dir)
        runtime_dir = getattr(args, "runtime_dir", None)
        if inspect:
            payload = inspect_export_link_discovery(
                database_dir,
                runtime_dir=runtime_dir,
            )
        elif bind:
            account = os.environ.get(ACCOUNT_ENVIRONMENT_VARIABLE)
            if not isinstance(account, str) or not account:
                raise LinkDiscoveryError("link_discovery_account_environment_missing")
            payload = bind_export_account(
                database_dir,
                runtime_dir=runtime_dir,
                account=account,
            )
        else:
            payload = discover_export_link(
                database_dir,
                runtime_dir=runtime_dir,
            )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except (LinkDiscoveryError, ChatGPTExportStateError, NotificationConnectorError) as exc:
        code = exc.code if hasattr(exc, "code") else "link_discovery_execution_failed"
        print(json.dumps(_failure_payload(code), ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 2
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        print(
            json.dumps(
                _failure_payload("link_discovery_execution_failed"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2


__all__ = (
    "ACCOUNT_BINDING_FILENAME",
    "ACCOUNT_ENVIRONMENT_VARIABLE",
    "APPLE_MAIL_DISCOVERY_SCRIPT",
    "CONTRACT_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "LinkDiscoveryError",
    "MODEL_RELATIVE",
    "PRIVATE_LINK_FILENAME",
    "TASK_ID",
    "bind_export_account",
    "discover_export_link",
    "inspect_export_link_discovery",
    "load_chatgpt_export_link_discovery_contract",
    "load_chatgpt_export_link_discovery_model_parameters",
    "load_private_export_account_binding",
    "load_private_export_link",
    "run_chatgpt_export_link_discovery",
    "scan_apple_mail_sources",
    "validate_chatgpt_export_link_discovery_contract",
    "validate_chatgpt_export_link_discovery_model_parameters",
    "validate_notification_source",
)
