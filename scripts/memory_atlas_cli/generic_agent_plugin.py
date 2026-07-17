"""Fail-closed host for data-only external generic-Agent plugin envelopes."""

from __future__ import annotations

import json
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from memory_atlas_cli.generic_agent_read_adapter import (
    GenericAgentReadError,
    GenericAgentReadResult,
    read_generic_agent_export,
)
from memory_atlas_cli.raw_ledger import RawLedgerError, RawLedgerPostWriteError
from memory_atlas_cli.source_registry import (
    PUSH_DEFAULTS,
    SourceRegistryError,
    load_source_registry,
    sync_source_map,
    validate_portable_identifier,
    validate_source_registry,
)
from privacy_guard import PrivacyViolation
from public_raw_sanitizer import (
    PublicRawLimitError,
    PublicRawSanitizationError,
    merge_counts,
    sanitize_public_value,
)
from sync_future_agent_data import (
    AppendOnlyViolation,
    SourceIdentityViolation,
    SourceInputError,
    normalize_event,
    stable_hash,
    sync_rows,
)


SCHEMA_VERSION = "memory_atlas.generic_agent_plugin.v1_2_1_s09_p2_t3"
RESULT_SCHEMA_VERSION = "memory_atlas.generic_agent_plugin_result.v1_2_1_s09_p2_t3"
ENVELOPE_SCHEMA_VERSION = "memory_atlas.generic_agent_plugin_envelope.v1"
TASK_ID = "S09-P2-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P2-T3"
CONTRACT_PATH = Path("config/data_sources/generic_agent_plugin.json")
MODEL_PATH = Path("机器治理/参数与公式/generic_agent_plugin.v1_2_1_s09_p2_t3.json")
ENTRYPOINT_PATH = Path("scripts/sync_generic_agent_plugin.py")
REGISTRY_PATH = Path("config/data_sources/source_registry.json")
READ_ADAPTER_CONTRACT_PATH = Path(
    "config/data_sources/generic_agent_read_adapter.json"
)
CREDENTIAL_CONTRACT_PATH = Path("config/data_sources/credential_exclusion.json")
RAW_LEDGER_CONTRACT_PATH = Path("config/data_sources/raw_ledger.json")
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ADAPTER_MODE = "external_plugin_envelope"
MAX_CONTROL_BYTES = 256 * 1024
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_ROLES = ["assistant", "developer", "system", "tool", "unknown", "user"]
_HOST_OWNED_GATES = [
    "credential_exclusion",
    "append_only_raw",
    "raw_ledger",
    "final_delivery_main",
]

EXPECTED_PROTOCOL = {
    "schema_version": ENVELOPE_SCHEMA_VERSION,
    "transport": "external_file_only",
    "encoding": "utf-8-json",
    "event_payload": "canonical_events",
    "events_hash": "canonical_json_sha256",
    "source_artifact_trust": "producer_claim_only",
}
EXPECTED_CANONICAL_EVENT = {
    "required_keys": ["event_id", "title", "messages"],
    "message_required_keys": ["message_id", "role", "text"],
    "roles": _ALLOWED_ROLES,
    "unknown_keys": "fail_closed",
}
EXPECTED_LIMITS = {
    "max_envelope_bytes": 67_108_864,
    "max_events": 10_000,
    "max_messages_per_event": 10_000,
    "max_total_messages": 200_000,
    "max_identifier_chars": 128,
    "max_title_utf8_bytes": 65_536,
    "max_message_utf8_bytes": 1_048_576,
    "max_source_artifact_bytes": 9_223_372_036_854_775_807,
}
EXPECTED_HOST_GATES = {
    "read_adapter_contract_ref": READ_ADAPTER_CONTRACT_PATH.as_posix(),
    "credential_exclusion_contract_ref": CREDENTIAL_CONTRACT_PATH.as_posix(),
    "raw_ledger_contract_ref": RAW_LEDGER_CONTRACT_PATH.as_posix(),
    "raw_root_template": "data/public_raw/agents/{source_id}",
    "derived_output_template": (
        "data/derived/agents/{source_id}/agent_sync_summary.json"
    ),
    "host_owned_write_pipeline": True,
    "plugin_direct_write_api": False,
    "push_policy": PUSH_DEFAULTS,
}
EXPECTED_SAFETY = {
    "arbitrary_plugin_code_execution": False,
    "network_access": False,
    "shell": False,
    "source_read_only": True,
    "envelope_outside_database_on_apply": True,
    "source_content_in_cli_output": False,
    "local_absolute_path_in_cli_output": False,
}
EXPECTED_PHASE_BOUNDARY = {
    "real_third_party_plugin_registered": False,
    "source_state_registry_implemented": False,
    "multi_source_restore_implemented": False,
    "remote_push": False,
    "next_task": "S09-P3-T1",
}


class GenericAgentPluginError(ValueError):
    """Path-free failure code for plugin contract and host rejection."""

    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


@dataclass(frozen=True)
class ValidatedPluginEnvelope:
    snapshot: GenericAgentReadResult
    source_format: str
    source_artifact: dict[str, Any]
    events: tuple[dict[str, Any], ...]
    events_sha256: str


def _read_control_json(path: Path, code: str) -> Any:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_CONTROL_BYTES:
            raise GenericAgentPluginError(code)
        data = bytearray()
        while True:
            chunk = os.read(descriptor, min(64 * 1024, MAX_CONTROL_BYTES + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            if len(data) > MAX_CONTROL_BYTES:
                raise GenericAgentPluginError(code)
        after = os.fstat(descriptor)
    except GenericAgentPluginError:
        raise
    except OSError as exc:
        raise GenericAgentPluginError(code) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    identity_before = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    identity_after = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if identity_before != identity_after or len(data) != after.st_size:
        raise GenericAgentPluginError(code)
    try:
        return json.loads(bytes(data).decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GenericAgentPluginError(code) from exc


def _mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise GenericAgentPluginError(code)
    return value


def _exact_keys(value: Mapping[str, Any], expected: set[str], code: str) -> None:
    if set(value) != expected:
        raise GenericAgentPluginError(code)


def validate_generic_agent_plugin_contract(payload: Any) -> dict[str, Any]:
    contract = _mapping(payload, "plugin_contract_not_object")
    _exact_keys(
        contract,
        {
            "schema_version",
            "task_id",
            "acceptance_id",
            "entrypoint",
            "model_ref",
            "registry_ref",
            "protocol",
            "canonical_event",
            "limits",
            "host_gates",
            "safety",
            "phase_boundary",
        },
        "plugin_contract_keys_mismatch",
    )
    expected_identity = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "entrypoint": ENTRYPOINT_PATH.as_posix(),
        "model_ref": MODEL_PATH.as_posix(),
        "registry_ref": REGISTRY_PATH.as_posix(),
    }
    if any(contract.get(key) != value for key, value in expected_identity.items()):
        raise GenericAgentPluginError("plugin_contract_identity_mismatch")
    expected_sections: tuple[tuple[str, Mapping[str, Any]], ...] = (
        ("protocol", EXPECTED_PROTOCOL),
        ("canonical_event", EXPECTED_CANONICAL_EVENT),
        ("limits", EXPECTED_LIMITS),
        ("host_gates", EXPECTED_HOST_GATES),
        ("safety", EXPECTED_SAFETY),
        ("phase_boundary", EXPECTED_PHASE_BOUNDARY),
    )
    for field, expected in expected_sections:
        if contract.get(field) != expected:
            raise GenericAgentPluginError(f"plugin_contract_{field}_mismatch")
    return contract


def load_generic_agent_plugin_contract(
    package_root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    try:
        root = package_root.resolve(strict=True)
    except OSError as exc:
        raise GenericAgentPluginError("package_root_unreadable") from exc
    if not root.is_dir():
        raise GenericAgentPluginError("package_root_unreadable")
    contract = validate_generic_agent_plugin_contract(
        _read_control_json(root / CONTRACT_PATH, "plugin_contract_unreadable")
    )
    for relative in (
        MODEL_PATH,
        ENTRYPOINT_PATH,
        REGISTRY_PATH,
        READ_ADAPTER_CONTRACT_PATH,
        CREDENTIAL_CONTRACT_PATH,
        RAW_LEDGER_CONTRACT_PATH,
    ):
        try:
            metadata = (root / relative).lstat()
        except OSError as exc:
            raise GenericAgentPluginError("plugin_contract_dependency_missing") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise GenericAgentPluginError("plugin_contract_dependency_not_regular")
    return contract


def _candidate_target(candidate: Mapping[str, Any]) -> str:
    if candidate.get("kind") == "operator_argument":
        return str(candidate.get("value"))
    return str(candidate.get("target_argument"))


def validate_plugin_source(
    registry: Any,
    contract: Mapping[str, Any],
    source_id: str,
    package_root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    try:
        root = package_root.resolve(strict=True)
        validated = validate_source_registry(registry, root)
        source = sync_source_map(validated)[source_id]
    except (KeyError, OSError, SourceRegistryError) as exc:
        raise GenericAgentPluginError("plugin_source_registry_invalid") from exc
    if (
        source.get("source_type") != "generic_agent"
        or source_id == "generic_agent_template"
        or source.get("push_policy") != PUSH_DEFAULTS
    ):
        raise GenericAgentPluginError("plugin_source_registry_invalid")
    parser = _mapping(source.get("parser"), "plugin_source_registry_invalid")
    plugin = _mapping(parser.get("plugin"), "plugin_source_registry_invalid")
    expected_static = {
        "mode": "external_envelope_only",
        "protocol": ENVELOPE_SCHEMA_VERSION,
        "host_entrypoint": ENTRYPOINT_PATH.as_posix(),
        "contract_ref": CONTRACT_PATH.as_posix(),
        "model_ref": MODEL_PATH.as_posix(),
        "arbitrary_code_execution": False,
        "host_owned_gates": _HOST_OWNED_GATES,
        "push_policy": PUSH_DEFAULTS,
    }
    if any(plugin.get(key) != value for key, value in expected_static.items()):
        raise GenericAgentPluginError("plugin_source_registry_invalid")
    if set(plugin) != set(expected_static) | {"plugin_id"}:
        raise GenericAgentPluginError("plugin_source_registry_invalid")
    try:
        validate_portable_identifier(
            plugin.get("plugin_id"),
            f"{source_id}.parser.plugin.plugin_id",
            max_length=64,
        )
    except SourceRegistryError as exc:
        raise GenericAgentPluginError("plugin_source_registry_invalid") from exc
    if parser.get("input_formats") != [ENVELOPE_SCHEMA_VERSION]:
        raise GenericAgentPluginError("plugin_source_registry_invalid")
    candidates = source.get("discovery", {}).get("candidates", [])
    if not candidates or any(
        _candidate_target(candidate) != "--plugin-envelope"
        for candidate in candidates
        if isinstance(candidate, dict)
    ):
        raise GenericAgentPluginError("plugin_source_registry_invalid")
    if contract.get("host_gates") != EXPECTED_HOST_GATES:
        raise GenericAgentPluginError("plugin_contract_host_gates_mismatch")
    return source


def _utf8_size(value: str) -> int:
    return len(value.encode("utf-8"))


def _identifier(value: Any, field: str, maximum: int) -> str:
    try:
        return validate_portable_identifier(value, field, max_length=maximum)
    except SourceRegistryError as exc:
        raise GenericAgentPluginError("plugin_envelope_event_schema_invalid") from exc


def _validate_event(
    value: Any,
    *,
    limits: Mapping[str, int],
) -> tuple[dict[str, Any], int]:
    event = _mapping(value, "plugin_envelope_event_schema_invalid")
    _exact_keys(
        event,
        {"event_id", "title", "messages"},
        "plugin_envelope_event_schema_invalid",
    )
    _identifier(
        event.get("event_id"),
        "plugin_event_id",
        limits["max_identifier_chars"],
    )
    title = event.get("title")
    if (
        not isinstance(title, str)
        or not title.strip()
        or _utf8_size(title) > limits["max_title_utf8_bytes"]
    ):
        raise GenericAgentPluginError("plugin_envelope_event_schema_invalid")
    messages = event.get("messages")
    if (
        not isinstance(messages, list)
        or not messages
        or len(messages) > limits["max_messages_per_event"]
    ):
        raise GenericAgentPluginError("plugin_envelope_event_schema_invalid")
    message_ids: set[str] = set()
    for message_value in messages:
        message = _mapping(
            message_value,
            "plugin_envelope_message_schema_invalid",
        )
        _exact_keys(
            message,
            {"message_id", "role", "text"},
            "plugin_envelope_message_schema_invalid",
        )
        message_id = _identifier(
            message.get("message_id"),
            "plugin_message_id",
            limits["max_identifier_chars"],
        )
        if message_id in message_ids:
            raise GenericAgentPluginError("plugin_envelope_duplicate_message_id")
        message_ids.add(message_id)
        if message.get("role") not in _ALLOWED_ROLES:
            raise GenericAgentPluginError("plugin_envelope_message_role_invalid")
        text = message.get("text")
        if (
            not isinstance(text, str)
            or not text.strip()
            or _utf8_size(text) > limits["max_message_utf8_bytes"]
        ):
            raise GenericAgentPluginError("plugin_envelope_message_schema_invalid")
    return event, len(messages)


def _validate_plugin_envelope(
    snapshot: GenericAgentReadResult,
    *,
    source_id: str,
    plugin_id: str,
    contract: Mapping[str, Any],
) -> ValidatedPluginEnvelope:
    if (
        snapshot.source_kind != "file"
        or len(snapshot.files) != 1
        or snapshot.files[0].source_format != "json"
        or len(snapshot.records) != 1
        or snapshot.files[0].size_bytes > contract["limits"]["max_envelope_bytes"]
    ):
        raise GenericAgentPluginError("plugin_envelope_transport_invalid")
    payload = _mapping(
        snapshot.records[0].payload,
        "plugin_envelope_not_object",
    )
    _exact_keys(
        payload,
        {
            "schema_version",
            "source_id",
            "plugin_id",
            "source_format",
            "source_artifact",
            "event_count",
            "events_sha256",
            "canonical_events",
        },
        "plugin_envelope_keys_mismatch",
    )
    if payload.get("schema_version") != ENVELOPE_SCHEMA_VERSION:
        raise GenericAgentPluginError("plugin_envelope_schema_mismatch")
    if payload.get("source_id") != source_id or payload.get("plugin_id") != plugin_id:
        raise GenericAgentPluginError("plugin_envelope_identity_mismatch")
    source_format = _identifier(
        payload.get("source_format"),
        "plugin_source_format",
        64,
    )
    source_artifact = _mapping(
        payload.get("source_artifact"),
        "plugin_source_artifact_invalid",
    )
    _exact_keys(
        source_artifact,
        {"byte_size", "sha256"},
        "plugin_source_artifact_invalid",
    )
    artifact_size = source_artifact.get("byte_size")
    artifact_sha256 = source_artifact.get("sha256")
    if (
        not isinstance(artifact_size, int)
        or isinstance(artifact_size, bool)
        or artifact_size < 0
        or artifact_size > contract["limits"]["max_source_artifact_bytes"]
        or not isinstance(artifact_sha256, str)
        or not _SHA256_RE.fullmatch(artifact_sha256)
    ):
        raise GenericAgentPluginError("plugin_source_artifact_invalid")
    events = payload.get("canonical_events")
    if (
        not isinstance(events, list)
        or not events
        or len(events) > contract["limits"]["max_events"]
        or payload.get("event_count") != len(events)
    ):
        raise GenericAgentPluginError("plugin_envelope_event_count_invalid")
    events_sha256 = payload.get("events_sha256")
    if (
        not isinstance(events_sha256, str)
        or not _SHA256_RE.fullmatch(events_sha256)
        or stable_hash(events) != events_sha256
    ):
        raise GenericAgentPluginError("plugin_envelope_events_hash_invalid")
    validated_events: list[dict[str, Any]] = []
    event_ids: set[str] = set()
    total_messages = 0
    limits = contract["limits"]
    for event_value in events:
        event, message_count = _validate_event(event_value, limits=limits)
        event_id = str(event["event_id"])
        if event_id in event_ids:
            raise GenericAgentPluginError("plugin_envelope_duplicate_event_id")
        event_ids.add(event_id)
        total_messages += message_count
        if total_messages > limits["max_total_messages"]:
            raise GenericAgentPluginError("plugin_envelope_message_limit_exceeded")
        validated_events.append(event)
    return ValidatedPluginEnvelope(
        snapshot=snapshot,
        source_format=source_format,
        source_artifact={
            "byte_size": artifact_size,
            "sha256": artifact_sha256,
        },
        events=tuple(validated_events),
        events_sha256=events_sha256,
    )


def _normalize_plugin_event(
    event: dict[str, Any],
    *,
    source_id: str,
    plugin_id: str,
    source_format: str,
    source_artifact: Mapping[str, Any],
    envelope_sha256: str,
) -> dict[str, Any]:
    try:
        row = normalize_event(source_id, event, source_id=source_id)
    except PrivacyViolation as exc:
        raise GenericAgentPluginError("plugin_credential_gate_rejected") from exc
    except (SourceIdentityViolation, SourceInputError) as exc:
        raise GenericAgentPluginError("plugin_event_normalization_failed") from exc
    row.update(
        {
            "adapter_mode": PLUGIN_ADAPTER_MODE,
            "source_format": f"plugin:{source_format}",
            "plugin_provenance": {
                "plugin_id": plugin_id,
                "protocol": ENVELOPE_SCHEMA_VERSION,
                "envelope_sha256": envelope_sha256,
                "events_sha256": stable_hash([event]),
                "source_artifact": {
                    "byte_size": source_artifact["byte_size"],
                    "sha256": source_artifact["sha256"],
                    "trust": "producer_claim_only",
                },
            },
        }
    )
    try:
        sanitized, counts = sanitize_public_value(row)
    except PublicRawSanitizationError as exc:
        raise GenericAgentPluginError("plugin_public_sanitization_failed") from exc
    if not isinstance(sanitized, dict):
        raise GenericAgentPluginError("plugin_public_sanitization_failed")
    sanitized["redaction_counts"] = merge_counts(
        row.get("redaction_counts") or {},
        counts,
    )
    sanitized["content_sha256"] = stable_hash(sanitized)
    return sanitized


def run_generic_agent_plugin(
    *,
    package_root: Path,
    database_dir: Path,
    source_id: str,
    plugin_id: str,
    envelope_path: Path,
    dry_run: bool,
    generated_at: str | None = None,
) -> dict[str, Any]:
    contract = load_generic_agent_plugin_contract(package_root)
    try:
        root = package_root.resolve(strict=True)
        database = database_dir.resolve(strict=True)
    except OSError as exc:
        raise GenericAgentPluginError("plugin_runtime_root_unreadable") from exc
    if not database.is_dir():
        raise GenericAgentPluginError("plugin_database_not_directory")
    try:
        source_id = validate_portable_identifier(
            source_id,
            "source_id",
            max_length=64,
        )
        plugin_id = validate_portable_identifier(
            plugin_id,
            "plugin_id",
            max_length=64,
        )
    except SourceRegistryError as exc:
        raise GenericAgentPluginError("plugin_identity_invalid") from exc
    registry = load_source_registry(root)
    source = validate_plugin_source(registry, contract, source_id, root)
    binding = source["parser"]["plugin"]
    if binding["plugin_id"] != plugin_id:
        raise GenericAgentPluginError("plugin_registry_identity_mismatch")
    if source.get("status") == "fixture" and not dry_run and database == root:
        raise GenericAgentPluginError("plugin_fixture_production_apply_rejected")
    try:
        snapshot = read_generic_agent_export(database, envelope_path)
    except GenericAgentReadError as exc:
        raise GenericAgentPluginError("plugin_envelope_read_failed") from exc
    if (
        not dry_run
        and (
            snapshot.source_path == database
            or database in snapshot.source_path.parents
        )
    ):
        raise GenericAgentPluginError("plugin_envelope_inside_database")
    envelope = _validate_plugin_envelope(
        snapshot,
        source_id=source_id,
        plugin_id=plugin_id,
        contract=contract,
    )
    rows = [
        _normalize_plugin_event(
            event,
            source_id=source_id,
            plugin_id=plugin_id,
            source_format=envelope.source_format,
            source_artifact=envelope.source_artifact,
            envelope_sha256=snapshot.source_sha256,
        )
        for event in envelope.events
    ]
    try:
        result = sync_rows(
            database,
            source_id,
            rows,
            dry_run,
            source_sha256=snapshot.source_sha256,
            source_id=source_id,
            source_snapshot=snapshot,
            generated_at=generated_at,
            adapter_mode=PLUGIN_ADAPTER_MODE,
        )
    except GenericAgentPluginError:
        raise
    except PrivacyViolation as exc:
        raise GenericAgentPluginError("plugin_credential_gate_rejected") from exc
    except (
        AppendOnlyViolation,
        PublicRawLimitError,
        PublicRawSanitizationError,
        RawLedgerError,
        RawLedgerPostWriteError,
        SourceIdentityViolation,
        SourceInputError,
        OSError,
        TypeError,
        ValueError,
    ) as exc:
        raise GenericAgentPluginError("plugin_host_pipeline_failed") from exc
    result.update(
        {
            "schema_version": RESULT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "acceptance_id": ACCEPTANCE_ID,
            "adapter_mode": PLUGIN_ADAPTER_MODE,
            "envelope_sha256": snapshot.source_sha256,
            "events_sha256": envelope.events_sha256,
            "source_read_only": True,
            "source_content_in_output": False,
            "local_absolute_path_in_output": False,
            "main_push_contract": dict(PUSH_DEFAULTS),
            "production_database_mutation": bool(not dry_run and database == root),
            "plugin": {
                "plugin_id": plugin_id,
                "protocol": ENVELOPE_SCHEMA_VERSION,
                "execution_mode": "external_envelope_only",
                "arbitrary_code_execution": False,
                "host_owned_write_pipeline": True,
                "direct_write_api": False,
                "network_access": False,
                "remote_push": False,
            },
        }
    )
    return result


__all__ = (
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "ENTRYPOINT_PATH",
    "ENVELOPE_SCHEMA_VERSION",
    "MODEL_PATH",
    "RESULT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "TASK_ID",
    "GenericAgentPluginError",
    "load_generic_agent_plugin_contract",
    "run_generic_agent_plugin",
    "validate_generic_agent_plugin_contract",
    "validate_plugin_source",
)
