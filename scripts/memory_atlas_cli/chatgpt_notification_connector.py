"""Read-only notification connector configuration for ChatGPT exports."""

from __future__ import annotations

import json
import os
import platform
import secrets
import stat
import subprocess
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Any


CONTRACT_RELATIVE = Path("config/data_sources/chatgpt_notification_connector.json")
MODEL_RELATIVE = Path(
    "机器治理/参数与公式/chatgpt_notification_connector.v1_2_1_s08_p2_t1.json"
)
TASK_ID = "S08-P2-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S08-P2-T1"
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_notification_connector_contract.v1_2_1_s08_p2_t1"
)
MODEL_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_notification_connector_model.v1_2_1_s08_p2_t1"
)
LOCAL_CONFIG_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_notification_local_config.v1_2_1_s08_p2_t1"
)
RESULT_SCHEMA_VERSION = (
    "memory_atlas.chatgpt_notification_connector_result.v1_2_1_s08_p2_t1"
)
ADAPTER_IDS = ("apple-mail-local",)
LOCAL_CONFIG_FILENAME = "chatgpt_notification_connector.json"
PROBE_TIMEOUT_SECONDS = 10
MAX_PROBE_STDOUT_BYTES = 64
MAX_CONTRACT_BYTES = 128 * 1024
MAX_LOCAL_CONFIG_BYTES = 4 * 1024
LOCAL_CONFIG_FILE_MODE = 0o600
RUNTIME_DIRECTORY_MODE = 0o700
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
DEFAULT_RUNTIME_RELATIVE = Path(
    "Library/Application Support/OpenAIDatabase/MemoryAtlas/private_runtime/notification_connector"
)

APPLE_MAIL_PROBE_SCRIPT = (
    'tell application "Mail"',
    "set accountTotal to count every account",
    'if accountTotal < 1 then return "NO_ACCOUNTS"',
    "set enabledTotal to 0",
    "repeat with mailAccount in every account",
    "if enabled of mailAccount is true then set enabledTotal to enabledTotal + 1",
    "end repeat",
    'if enabledTotal < 1 then return "NO_ENABLED_ACCOUNTS"',
    "try",
    "set inboxTotal to count messages of inbox",
    "on error",
    'return "INBOX_UNREADABLE"',
    "end try",
    'return "READY"',
    "end tell",
)

PHASE_BOUNDARY = {
    "configures_read_only_connector": True,
    "discovers_export_notifications": False,
    "extracts_download_links": False,
    "downloads_export": False,
    "writes_raw_archive": False,
    "commits_or_pushes": False,
    "deploys": False,
    "next_task": "S08-P2-T2",
}

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "chatgpt",
    "connector": {
        "interface_version": "memory_atlas.notification_connector.v1",
        "read_only": True,
        "adapter_registry": list(ADAPTER_IDS),
        "active_adapter_source": "machine_local_config",
        "configuration_requires_live_probe": True,
        "configuration_location": "outside_repository",
    },
    "adapters": {
        "apple-mail-local": {
            "transport": "apple_mail_applescript",
            "credential_policy": "os_keychain_via_apple_mail",
            "connector_reads_credentials": False,
            "probe_reads_account_identity": False,
            "probe_reads_message_metadata": False,
            "probe_reads_message_content": False,
            "probe_emits_counts": False,
            "probe_operations": [
                "count_accounts",
                "count_enabled_accounts",
                "count_inbox_messages",
            ],
        }
    },
    "local_config": {
        "schema_version": LOCAL_CONFIG_SCHEMA_VERSION,
        "filename": LOCAL_CONFIG_FILENAME,
        "file_mode_octal": "0600",
        "directory_mode_octal": "0700",
        "contains_credentials": False,
        "contains_account_identity": False,
        "contains_absolute_paths": False,
        "atomic_replace_and_directory_fsync": True,
    },
    "cli": {
        "command": "chatgpt-notification-connector",
        "modes": ["--configure", "--inspect"],
        "configure_requires": ["--adapter"],
        "inspect_is_read_only": True,
        "output_is_sanitized": True,
    },
    "security": {
        "reads_credentials": False,
        "reads_account_identity": False,
        "reads_message_metadata": False,
        "reads_message_content": False,
        "emits_mail_values": False,
        "uses_private_api": False,
        "raw_mutation": False,
        "repository_mutation": False,
        "remote_actions": False,
    },
    "model_parameters_ref": MODEL_RELATIVE.as_posix(),
    "phase_boundary": PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS: dict[str, Any] = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-009",
    "formula_id": "FORM-009",
    "purpose": "Declare a notification adapter ready only after a bounded, content-free, read-only capability probe succeeds in the user environment.",
    "parameters": {
        "supported_adapter_count": 1,
        "probe_timeout_seconds": PROBE_TIMEOUT_SECONDS,
        "maximum_probe_stdout_bytes": MAX_PROBE_STDOUT_BYTES,
        "probe_account_identity_reads": 0,
        "probe_message_metadata_reads": 0,
        "probe_message_content_reads": 0,
        "probe_credential_store_reads": 0,
        "configuration_file_mode_octal": "0600",
        "runtime_directory_mode_octal": "0700",
        "live_ready_observations_required": 1,
    },
    "formula": "adapter_ready = supported_adapter AND platform_supported AND application_available AND enabled_account_present AND inbox_count_readable AND live_probe_token=READY; account_identity_reads=0; message_metadata_reads=0; message_content_reads=0; credential_store_reads=0",
    "parameter_rationale": {
        "supported_adapter_count": "S08-P2-T1 configures one real adapter; later adapters plug into the same registry without changing the result contract.",
        "probe_timeout_seconds": "Ten seconds bounds Apple event or permission stalls without retrying or reading fallback data.",
        "maximum_probe_stdout_bytes": "The adapter accepts only one short allowlisted readiness token and rejects all other output.",
        "probe_message_content_reads": "Message content and export-link discovery belong to S08-P2-T2, not this Task.",
        "configuration_file_mode_octal": "The machine-local adapter selection is private-by-default even though it contains no credentials.",
    },
    "failure_semantics": "Unsupported platform, missing Mail access, unknown probe output, timeout, unsafe runtime path, config drift, symlink or permission mismatch fails closed without storing config or echoing Mail and process values.",
    "calibration_boundary": "S08-P2-T1 proves one real read-only notification transport is configured. It does not inspect message fields, discover OpenAI notifications, extract links, download exports, mutate raw data or perform Git remote actions.",
}


class NotificationConnectorError(RuntimeError):
    """Path-free connector error safe for machine output."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


CommandRunner = Callable[..., subprocess.CompletedProcess[bytes]]
AdapterProbe = Callable[..., dict[str, Any]]


def _database_root(database_dir: Path) -> Path:
    candidate = Path(database_dir).expanduser()
    if candidate.is_symlink() or not candidate.is_dir():
        raise NotificationConnectorError("notification_database_invalid")
    return candidate.resolve()


def _read_json(path: Path, *, maximum_bytes: int, code: str) -> dict[str, Any]:
    if path.is_symlink():
        raise NotificationConnectorError(code)
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise NotificationConnectorError(code) from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > maximum_bytes:
            raise NotificationConnectorError(code)
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(maximum_bytes + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > maximum_bytes:
        raise NotificationConnectorError(code)
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise NotificationConnectorError(code) from exc
    if not isinstance(payload, dict):
        raise NotificationConnectorError(code)
    return payload


def validate_chatgpt_notification_connector_contract(payload: object) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise NotificationConnectorError("notification_connector_contract_drift")
    return dict(payload)


def validate_chatgpt_notification_connector_model_parameters(
    payload: object,
) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise NotificationConnectorError("notification_connector_model_drift")
    return dict(payload)


def load_chatgpt_notification_connector_contract(database_dir: Path) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_notification_connector_contract(
        _read_json(
            root / CONTRACT_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="notification_connector_contract_unreadable",
        )
    )


def load_chatgpt_notification_connector_model_parameters(
    database_dir: Path,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    return validate_chatgpt_notification_connector_model_parameters(
        _read_json(
            root / MODEL_RELATIVE,
            maximum_bytes=MAX_CONTRACT_BYTES,
            code="notification_connector_model_unreadable",
        )
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
    for line in APPLE_MAIL_PROBE_SCRIPT:
        argv.extend(("-e", line))
    return argv


def probe_apple_mail(
    *,
    runner: CommandRunner = subprocess.run,
    system_name: str | None = None,
    application_paths: Sequence[Path] = DEFAULT_APPLICATION_PATHS,
    osascript_path: Path = DEFAULT_OSASCRIPT_PATH,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    if (platform.system() if system_name is None else system_name) != "Darwin":
        raise NotificationConnectorError("apple_mail_platform_unsupported")
    application_available = any(
        Path(path).is_dir() and not Path(path).is_symlink()
        for path in application_paths
    )
    if not application_available:
        raise NotificationConnectorError("apple_mail_application_unavailable")
    executable = Path(osascript_path)
    if executable.is_symlink() or not executable.is_file() or not os.access(executable, os.X_OK):
        raise NotificationConnectorError("apple_mail_osascript_unavailable")
    argv = _apple_mail_argv(executable)
    try:
        result = runner(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=PROBE_TIMEOUT_SECONDS,
            shell=False,
            env=_safe_child_env(environ),
        )
    except subprocess.TimeoutExpired as exc:
        raise NotificationConnectorError("apple_mail_probe_timeout") from exc
    except OSError as exc:
        raise NotificationConnectorError("apple_mail_probe_failed") from exc
    if result.returncode != 0:
        raise NotificationConnectorError("apple_mail_probe_failed")
    stdout = result.stdout
    if not isinstance(stdout, bytes) or len(stdout) > MAX_PROBE_STDOUT_BYTES:
        raise NotificationConnectorError("apple_mail_probe_response_invalid")
    try:
        token = stdout.decode("ascii").strip()
    except UnicodeDecodeError as exc:
        raise NotificationConnectorError("apple_mail_probe_response_invalid") from exc
    if token not in {"READY", "NO_ACCOUNTS", "NO_ENABLED_ACCOUNTS", "INBOX_UNREADABLE"}:
        raise NotificationConnectorError("apple_mail_probe_response_invalid")
    ready = token == "READY"
    return {
        "adapter_id": "apple-mail-local",
        "probe_status": token,
        "ready": ready,
        "application_available": True,
        "enabled_account_available": token in {"READY", "INBOX_UNREADABLE"},
        "inbox_readable": ready,
        "account_identity_read": False,
        "message_metadata_read": False,
        "message_content_read": False,
        "mail_values_emitted": False,
        "credential_store_access": False,
        "private_api_calls": False,
    }


ADAPTER_PROBES: dict[str, AdapterProbe] = {
    "apple-mail-local": probe_apple_mail,
}


def _repository_root(database_root: Path) -> Path:
    for candidate in (database_root, *database_root.parents):
        if (candidate / ".git").exists():
            return candidate.resolve()
    raise NotificationConnectorError("notification_repository_root_missing")


def _is_within(path: Path, parent: Path) -> bool:
    try:
        path.relative_to(parent)
    except ValueError:
        return False
    return True


def _runtime_directory(
    database_root: Path,
    runtime_dir: Path | None,
    *,
    create: bool,
) -> Path:
    raw = (
        Path.home() / DEFAULT_RUNTIME_RELATIVE
        if runtime_dir is None
        else Path(runtime_dir).expanduser()
    )
    if raw.is_symlink():
        raise NotificationConnectorError("notification_runtime_unsafe")
    candidate = raw.absolute().resolve(strict=False)
    if _is_within(candidate, _repository_root(database_root)):
        raise NotificationConnectorError("notification_runtime_inside_repository")
    if candidate.exists() and not candidate.is_dir():
        raise NotificationConnectorError("notification_runtime_invalid")
    if create:
        try:
            candidate.mkdir(parents=True, exist_ok=True, mode=RUNTIME_DIRECTORY_MODE)
            os.chmod(candidate, RUNTIME_DIRECTORY_MODE)
        except OSError as exc:
            raise NotificationConnectorError("notification_runtime_unavailable") from exc
    elif not candidate.is_dir():
        raise NotificationConnectorError("notification_runtime_unavailable")
    if candidate.is_symlink():
        raise NotificationConnectorError("notification_runtime_unsafe")
    if stat.S_IMODE(candidate.stat().st_mode) != RUNTIME_DIRECTORY_MODE:
        raise NotificationConnectorError("notification_runtime_mode_invalid")
    return candidate


def _local_config_payload(adapter_id: str) -> dict[str, Any]:
    if adapter_id != "apple-mail-local":
        raise NotificationConnectorError("notification_adapter_unsupported")
    return {
        "adapter_id": adapter_id,
        "credential_policy": "os_keychain_via_apple_mail",
        "read_only": True,
        "schema_version": LOCAL_CONFIG_SCHEMA_VERSION,
        "stores_credentials": False,
    }


def _load_local_config(runtime_directory: Path) -> dict[str, Any]:
    path = runtime_directory / LOCAL_CONFIG_FILENAME
    if path.is_symlink():
        raise NotificationConnectorError("notification_local_config_unsafe")
    try:
        metadata = path.stat()
    except OSError as exc:
        raise NotificationConnectorError("notification_local_config_unavailable") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise NotificationConnectorError("notification_local_config_unsafe")
    if stat.S_IMODE(metadata.st_mode) != LOCAL_CONFIG_FILE_MODE:
        raise NotificationConnectorError("notification_local_config_mode_invalid")
    payload = _read_json(
        path,
        maximum_bytes=MAX_LOCAL_CONFIG_BYTES,
        code="notification_local_config_invalid",
    )
    adapter_id = payload.get("adapter_id")
    if not isinstance(adapter_id, str) or payload != _local_config_payload(adapter_id):
        raise NotificationConnectorError("notification_local_config_invalid")
    return payload


def _fsync_directory(path: Path) -> None:
    flags = os.O_RDONLY | getattr(os, "O_DIRECTORY", 0)
    descriptor = os.open(path, flags)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _write_local_config(runtime_directory: Path, payload: dict[str, Any]) -> bool:
    path = runtime_directory / LOCAL_CONFIG_FILENAME
    if path.exists() or path.is_symlink():
        existing = _load_local_config(runtime_directory)
        if existing == payload:
            return False
        raise NotificationConnectorError("notification_local_config_conflict")
    content = (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")
    temporary = runtime_directory / (
        f".{LOCAL_CONFIG_FILENAME}.{os.getpid()}.{secrets.token_hex(8)}.tmp"
    )
    flags = (
        os.O_WRONLY
        | os.O_CREAT
        | os.O_EXCL
        | getattr(os, "O_CLOEXEC", 0)
        | getattr(os, "O_NOFOLLOW", 0)
    )
    descriptor = -1
    try:
        descriptor = os.open(temporary, flags, LOCAL_CONFIG_FILE_MODE)
        with os.fdopen(descriptor, "wb", closefd=True) as handle:
            descriptor = -1
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
        os.chmod(path, LOCAL_CONFIG_FILE_MODE)
        _fsync_directory(runtime_directory)
    except OSError as exc:
        raise NotificationConnectorError("notification_local_config_write_failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
        if temporary.exists():
            temporary.unlink()
    return True


def _probe_adapter(adapter_id: str, **probe_kwargs: Any) -> dict[str, Any]:
    probe = ADAPTER_PROBES.get(adapter_id)
    if probe is None:
        raise NotificationConnectorError("notification_adapter_unsupported")
    return probe(**probe_kwargs)


def _result_payload(
    *,
    action: str,
    adapter_id: str,
    probe: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "action": action,
        "adapter_id": adapter_id,
        "configured": True,
        "real_adapter_ready": probe["ready"],
        "probe_status": probe["probe_status"],
        "read_only": True,
        "credential_policy": "os_keychain_via_apple_mail",
        "credential_store_access": False,
        "account_identity_emitted": False,
        "message_metadata_read": False,
        "message_content_read": False,
        "mail_values_emitted": False,
        "configuration_path_emitted": False,
        "repository_mutation": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def _failure_payload(code: str) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "FAIL",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "error_code": code,
        "mail_values_emitted": False,
        "credential_values_emitted": False,
        "configuration_path_emitted": False,
        "repository_mutation": False,
        "raw_mutation": False,
        "remote_actions": False,
    }


def configure_notification_connector(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    adapter_id: str,
    **probe_kwargs: Any,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_notification_connector_contract(root)
    load_chatgpt_notification_connector_model_parameters(root)
    payload = _local_config_payload(adapter_id)
    probe = _probe_adapter(adapter_id, **probe_kwargs)
    if not probe["ready"]:
        raise NotificationConnectorError("notification_adapter_not_ready")
    runtime_directory = _runtime_directory(root, runtime_dir, create=True)
    changed = _write_local_config(runtime_directory, payload)
    return _result_payload(
        action="CONFIGURED" if changed else "ALREADY_CONFIGURED",
        adapter_id=adapter_id,
        probe=probe,
    )


def inspect_notification_connector(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
    **probe_kwargs: Any,
) -> dict[str, Any]:
    root = _database_root(database_dir)
    load_chatgpt_notification_connector_contract(root)
    load_chatgpt_notification_connector_model_parameters(root)
    runtime_directory = _runtime_directory(root, runtime_dir, create=False)
    config = _load_local_config(runtime_directory)
    adapter_id = config["adapter_id"]
    probe = _probe_adapter(adapter_id, **probe_kwargs)
    if not probe["ready"]:
        raise NotificationConnectorError("notification_adapter_not_ready")
    return _result_payload(
        action="INSPECTED_NO_CHANGES",
        adapter_id=adapter_id,
        probe=probe,
    )


def notification_runtime_directory(
    database_dir: Path,
    *,
    runtime_dir: Path | None,
) -> Path:
    """Return the configured private runtime without exposing its path."""
    root = _database_root(database_dir)
    directory = _runtime_directory(root, runtime_dir, create=False)
    _load_local_config(directory)
    return directory


def run_chatgpt_notification_connector(args: Any) -> int:
    try:
        inspect = bool(getattr(args, "inspect", False))
        configure = bool(getattr(args, "configure", False))
        if int(inspect) + int(configure) != 1:
            raise NotificationConnectorError("notification_connector_mode_invalid")
        adapter_id = getattr(args, "adapter", None)
        runtime_dir = getattr(args, "runtime_dir", None)
        database_dir = Path(args.database_dir)
        if configure:
            if adapter_id is None:
                raise NotificationConnectorError("notification_adapter_required")
            payload = configure_notification_connector(
                database_dir,
                runtime_dir=runtime_dir,
                adapter_id=adapter_id,
            )
        else:
            if adapter_id is not None:
                raise NotificationConnectorError("notification_inspect_adapter_forbidden")
            payload = inspect_notification_connector(
                database_dir,
                runtime_dir=runtime_dir,
            )
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
        return 0
    except NotificationConnectorError as exc:
        print(
            json.dumps(
                _failure_payload(exc.code),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2
    except (OSError, UnicodeError, ValueError, subprocess.SubprocessError):
        print(
            json.dumps(
                _failure_payload("notification_connector_execution_failed"),
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return 2


__all__ = (
    "ADAPTER_IDS",
    "CONTRACT_RELATIVE",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "LOCAL_CONFIG_FILENAME",
    "MODEL_RELATIVE",
    "NotificationConnectorError",
    "configure_notification_connector",
    "inspect_notification_connector",
    "load_chatgpt_notification_connector_contract",
    "load_chatgpt_notification_connector_model_parameters",
    "notification_runtime_directory",
    "probe_apple_mail",
    "run_chatgpt_notification_connector",
    "validate_chatgpt_notification_connector_contract",
    "validate_chatgpt_notification_connector_model_parameters",
)
