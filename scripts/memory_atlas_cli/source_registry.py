"""Canonical, configuration-driven Memory Atlas source registry contract."""

from __future__ import annotations

import json
import re
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from memory_atlas_cli.credential_exclusion import (
    CREDENTIAL_CONTRACT_PATH,
    CredentialExclusionError,
    POLICY_ID,
    load_credential_exclusion_contract,
)
from memory_atlas_cli.archive_chunking import (
    CONTRACT_PATH as ARCHIVE_CHUNKING_CONTRACT_PATH,
    ArchiveChunkError,
    load_archive_chunking_contract,
)
from memory_atlas_cli.archive_restore import (
    CONTRACT_PATH as ARCHIVE_RESTORE_CONTRACT_PATH,
    ArchiveRestoreError,
    load_archive_restore_contract,
)
from memory_atlas_cli.raw_ledger import (
    RAW_LEDGER_CONTRACT_PATH,
    RawLedgerError,
    load_raw_ledger_contract,
)


REGISTRY_PATH = Path("config/data_sources/source_registry.json")
PUBLIC_RAW_LAYOUT_PATH = Path("config/data_sources/public_raw_layout.json")
CHATGPT_EXPORT_ARCHIVE_CONTRACT_PATH = Path(
    "config/data_sources/chatgpt_export_archive.json"
)
CHATGPT_EXPORT_ARCHIVE_ENTRYPOINT = Path(
    "scripts/memory_atlas_cli/chatgpt_export_archive.py"
)
CHATGPT_EXPORT_PARSER_CONTRACT_PATH = Path(
    "config/data_sources/chatgpt_export_parser.json"
)
CHATGPT_EXPORT_PARSER_MODEL_PATH = Path(
    "机器治理/参数与公式/chatgpt_export_parser.v1_2_1_s09_p1_t1.json"
)
CHATGPT_EXPORT_PARSER_ENTRYPOINT = Path(
    "scripts/memory_atlas_cli/chatgpt_export_parser.py"
)
CHATGPT_EXPORT_PARSER_QUARANTINE_PATH = Path(
    "data/processed/conversations/chatgpt_parse_quarantine.jsonl"
)
CHATGPT_COMPLETE_ARCHIVE_ROOT = Path("data/raw_archives/chatgpt")
CODEX_DISCOVERY_CONTRACT_PATH = Path("config/data_sources/codex_source_discovery.json")
CODEX_PUBLIC_RAW_ARCHIVE_CONTRACT_PATH = Path(
    "config/data_sources/codex_public_raw_archive.json"
)
CODEX_PUBLIC_RAW_ARCHIVE_ENTRYPOINT = Path(
    "scripts/memory_atlas_cli/codex_public_raw_archive.py"
)
CODEX_SYNC_STATE_CONTRACT_PATH = Path("config/data_sources/codex_sync_state.json")
CODEX_SYNC_STATE_ENTRYPOINT = Path("scripts/memory_atlas_cli/codex_sync_state.py")
CODEX_DERIVED_CONTRACT_PATH = Path("config/data_sources/codex_derived.json")
CODEX_DERIVED_ENTRYPOINT = Path("scripts/build_memory_atlas_codex_derived.py")
CODEX_LEGACY_SUMMARY_CONTRACT_PATH = Path(
    "config/data_sources/codex_legacy_summary.json"
)
CODEX_LEGACY_SUMMARY_ENTRYPOINT = Path(
    "scripts/memory_atlas_cli/codex_legacy_summary.py"
)
CODEX_PUSH_MAIN_CONTRACT_PATH = Path("config/data_sources/codex_push_main.json")
CODEX_PUSH_MAIN_ENTRYPOINT = Path("scripts/memory_atlas_cli/codex_push_main.py")
CODEX_SCHEDULER_PROFILE_PATH = Path("config/data_sources/codex_scheduler_profile.json")
CODEX_SCHEDULER_ENTRYPOINT = Path("scripts/memory_atlas_cli/codex_scheduler.py")
CODEX_COMPLETE_ARCHIVE_ROOT = Path("data/raw_archives/codex")
REGISTRY_SCHEMA_VERSION = "memory_atlas_data_source_registry.v1"
SYNC_CONTRACT_VERSION = "memory_atlas.source_sync_contract.v1_2_1_s06_p1_t1"
TASK_ID = "S06-P1-T1"
REQUIRED_SYNC_FIELDS = (
    "source_id",
    "source_type",
    "discovery",
    "raw_paths",
    "credential_exclusions",
    "parser",
    "schedule",
    "state_path",
    "archive_path",
    "derived_outputs",
    "push_policy",
)
SOURCE_TYPES = ("chatgpt_export", "codex_local", "generic_agent")
REQUIRED_SOURCE_IDS = ("chatgpt", "codex", "generic_agent_template")
REQUIRED_SOURCE_TYPES = {
    "chatgpt": "chatgpt_export",
    "codex": "codex_local",
    "generic_agent_template": "generic_agent",
}
PUSH_DEFAULTS = {
    "mode": "final_delivery_only",
    "branch": "main",
    "open_pr": False,
    "force": False,
    "remote_race_stop": True,
}
_PORTABLE_ID_RE = re.compile(r"^[a-z0-9](?:[a-z0-9._-]*[a-z0-9])?$")
_WINDOWS_RESERVED_ID_RE = re.compile(r"^(?:con|prn|aux|nul|com[1-9]|lpt[1-9])(?:\..*)?$", re.IGNORECASE)
_ENV_NAME_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_DISCOVERY_KINDS = {"environment_variable", "home_relative", "operator_argument"}
_ALLOWED_TEMPLATE_TOKENS = {"{source_id}"}
_CLI_SOURCE_ALIASES = {"future-agent": "generic_agent_template"}
_DISCOVERY_ARGUMENTS = {
    "chatgpt_export": {"--official-export"},
    "codex_local": {"--codex-home"},
    "generic_agent": {"--input", "--markdown-report"},
}


class SourceRegistryError(ValueError):
    """Raised when the source registry cannot be trusted."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SourceRegistryError(f"{field} must be an object")
    return value


def _non_empty_string(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise SourceRegistryError(f"{field} must be a non-empty string")
    return value.strip()


def validate_portable_identifier(value: Any, field: str, *, max_length: int) -> str:
    """Validate identifiers that are also used as cross-platform path components."""

    text = _non_empty_string(value, field)
    if value != text:
        raise SourceRegistryError(f"{field} must not contain leading or trailing whitespace")
    if len(text) > max_length or not _PORTABLE_ID_RE.fullmatch(text):
        raise SourceRegistryError(f"{field} is not a portable identifier: {text}")
    if _WINDOWS_RESERVED_ID_RE.fullmatch(text):
        raise SourceRegistryError(f"{field} is a reserved Windows path component: {text}")
    return text


def _repo_relative_path(value: Any, field: str, prefixes: tuple[str, ...] = ()) -> str:
    text = _non_empty_string(value, field)
    if "\\" in text:
        raise SourceRegistryError(f"{field} must use repository-style forward slashes")
    path = PurePosixPath(text)
    windows_path = PureWindowsPath(text)
    if (
        path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or text.startswith("//")
        or ".." in path.parts
        or "." in path.parts
    ):
        raise SourceRegistryError(f"{field} must be a safe relative path")
    if prefixes and not any(text == prefix.rstrip("/") or text.startswith(prefix) for prefix in prefixes):
        raise SourceRegistryError(f"{field} must stay under one of {prefixes}")
    return text


def _string_list(value: Any, field: str) -> list[str]:
    if not isinstance(value, list) or not value:
        raise SourceRegistryError(f"{field} must be a non-empty list")
    result = [_non_empty_string(item, f"{field}[{index}]") for index, item in enumerate(value)]
    if len(result) != len(set(result)):
        raise SourceRegistryError(f"{field} must not contain duplicates")
    return result


def _validate_discovery(
    value: Any,
    field: str,
    allowed_arguments: set[str],
    *,
    contract_ref: Path | None = None,
) -> None:
    discovery = _mapping(value, field)
    expected_keys = {"strategy", "candidates"}
    if contract_ref is not None:
        expected_keys.add("contract_ref")
    if set(discovery) != expected_keys:
        raise SourceRegistryError(f"{field} keys do not match the source contract")
    if discovery.get("strategy") != "ordered_candidates":
        raise SourceRegistryError(f"{field}.strategy must be ordered_candidates")
    if contract_ref is not None:
        discovered_ref = _repo_relative_path(
            discovery.get("contract_ref"),
            f"{field}.contract_ref",
            ("config/data_sources/",),
        )
        if discovered_ref != contract_ref.as_posix():
            raise SourceRegistryError(f"{field}.contract_ref must name the canonical contract")
    candidates = discovery.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise SourceRegistryError(f"{field}.candidates must be a non-empty list")
    for index, candidate_value in enumerate(candidates):
        candidate = _mapping(candidate_value, f"{field}.candidates[{index}]")
        kind = _non_empty_string(candidate.get("kind"), f"{field}.candidates[{index}].kind")
        candidate_text = _non_empty_string(candidate.get("value"), f"{field}.candidates[{index}].value")
        if kind not in _DISCOVERY_KINDS:
            raise SourceRegistryError(f"{field}.candidates[{index}].kind is unsupported")
        if kind == "operator_argument":
            if set(candidate) != {"kind", "value"} or not candidate_text.startswith("--"):
                raise SourceRegistryError(f"{field}.candidates[{index}] must name a command argument")
            if candidate_text not in allowed_arguments:
                raise SourceRegistryError(f"{field}.candidates[{index}] is not supported by the adapter")
            continue
        if set(candidate) != {"kind", "value", "target_argument"}:
            raise SourceRegistryError(f"{field}.candidates[{index}] has unsupported keys")
        target_argument = _non_empty_string(
            candidate.get("target_argument"),
            f"{field}.candidates[{index}].target_argument",
        )
        if not target_argument.startswith("--"):
            raise SourceRegistryError(f"{field}.candidates[{index}].target_argument is invalid")
        if target_argument not in allowed_arguments:
            raise SourceRegistryError(f"{field}.candidates[{index}].target_argument is not supported by the adapter")
        if kind == "environment_variable" and not _ENV_NAME_RE.fullmatch(candidate_text):
            raise SourceRegistryError(f"{field}.candidates[{index}] has an invalid environment name")
        if kind == "home_relative":
            _repo_relative_path(candidate_text, f"{field}.candidates[{index}].value")


def _validate_source(source: dict[str, Any], database_dir: Path, push_defaults: dict[str, Any]) -> None:
    missing = [field for field in REQUIRED_SYNC_FIELDS if field not in source]
    if missing:
        raise SourceRegistryError(f"sync source is missing required fields: {missing}")

    source_id = validate_portable_identifier(source.get("source_id"), "source_id", max_length=64)
    if source_id in _CLI_SOURCE_ALIASES:
        raise SourceRegistryError(f"source_id is reserved for CLI compatibility: {source_id}")
    source_type = _non_empty_string(source.get("source_type"), f"{source_id}.source_type")
    if source_type not in SOURCE_TYPES:
        raise SourceRegistryError(f"{source_id}.source_type is unsupported: {source_type}")
    if source_type == "chatgpt_export" and source_id != "chatgpt":
        raise SourceRegistryError("chatgpt_export is reserved for the canonical chatgpt source")
    if source_type == "codex_local" and source_id != "codex":
        raise SourceRegistryError("codex_local is reserved for the canonical codex source")
    status = _non_empty_string(source.get("status"), f"{source_id}.status")
    if source_id == "chatgpt" and status != "active_manual":
        raise SourceRegistryError("chatgpt.status must be active_manual")
    if source_id == "codex" and status != "active_local":
        raise SourceRegistryError("codex.status must be active_local")
    if source_id == "generic_agent_template" and status != "template":
        raise SourceRegistryError("generic_agent_template.status must be template")
    if source_type == "generic_agent" and source_id != "generic_agent_template" and status not in {
        "active_manual",
        "configured",
    }:
        raise SourceRegistryError(f"{source_id}.status is unsupported for a concrete generic source")

    _validate_discovery(
        source.get("discovery"),
        f"{source_id}.discovery",
        _DISCOVERY_ARGUMENTS[source_type],
        contract_ref=CODEX_DISCOVERY_CONTRACT_PATH if source_type == "codex_local" else None,
    )
    for index, raw_path in enumerate(_string_list(source.get("raw_paths"), f"{source_id}.raw_paths")):
        _repo_relative_path(raw_path, f"{source_id}.raw_paths[{index}]")

    credential_exclusions = _mapping(source.get("credential_exclusions"), f"{source_id}.credential_exclusions")
    if credential_exclusions != {
        "policy": POLICY_ID,
        "contract_ref": CREDENTIAL_CONTRACT_PATH.as_posix(),
        "status": "active",
    }:
        raise SourceRegistryError(f"{source_id}.credential_exclusions must use the active canonical contract")

    parser = _mapping(source.get("parser"), f"{source_id}.parser")
    parser_path = _repo_relative_path(parser.get("entrypoint"), f"{source_id}.parser.entrypoint", ("scripts/",))
    _string_list(parser.get("input_formats"), f"{source_id}.parser.input_formats")
    expected_parser = {
        "chatgpt_export": "scripts/sync_chatgpt_memory_data.py",
        "codex_local": "scripts/sync_codex_memory_data.py",
        "generic_agent": "scripts/sync_future_agent_data.py",
    }[source_type]
    if parser_path != expected_parser:
        raise SourceRegistryError(f"{source_id}.parser.entrypoint is incompatible with {source_type}")
    resolved_parser = (database_dir / parser_path).resolve()
    if database_dir.resolve() not in resolved_parser.parents or not resolved_parser.is_file():
        raise SourceRegistryError(f"{source_id}.parser.entrypoint does not exist: {parser_path}")
    if source_type == "chatgpt_export":
        format_parser_entrypoint = _repo_relative_path(
            parser.get("format_parser_entrypoint"),
            f"{source_id}.parser.format_parser_entrypoint",
            ("scripts/",),
        )
        format_parser_contract_ref = _repo_relative_path(
            parser.get("format_parser_contract_ref"),
            f"{source_id}.parser.format_parser_contract_ref",
            ("config/data_sources/",),
        )
        format_parser_model_ref = _repo_relative_path(
            parser.get("format_parser_model_ref"),
            f"{source_id}.parser.format_parser_model_ref",
            ("机器治理/参数与公式/",),
        )
        quarantine_path = _repo_relative_path(
            parser.get("quarantine_path"),
            f"{source_id}.parser.quarantine_path",
            ("data/processed/conversations/",),
        )
        raw_archive_entrypoint = _repo_relative_path(
            parser.get("raw_archive_entrypoint"),
            f"{source_id}.parser.raw_archive_entrypoint",
            ("scripts/",),
        )
        raw_archive_contract_ref = _repo_relative_path(
            parser.get("raw_archive_contract_ref"),
            f"{source_id}.parser.raw_archive_contract_ref",
            ("config/data_sources/",),
        )
        complete_archive_root = _repo_relative_path(
            parser.get("complete_archive_root"),
            f"{source_id}.parser.complete_archive_root",
            ("data/raw_archives/",),
        )
        if (
            format_parser_entrypoint != CHATGPT_EXPORT_PARSER_ENTRYPOINT.as_posix()
            or format_parser_contract_ref
            != CHATGPT_EXPORT_PARSER_CONTRACT_PATH.as_posix()
            or format_parser_model_ref != CHATGPT_EXPORT_PARSER_MODEL_PATH.as_posix()
            or quarantine_path != CHATGPT_EXPORT_PARSER_QUARANTINE_PATH.as_posix()
            or raw_archive_entrypoint
            != CHATGPT_EXPORT_ARCHIVE_ENTRYPOINT.as_posix()
            or raw_archive_contract_ref
            != CHATGPT_EXPORT_ARCHIVE_CONTRACT_PATH.as_posix()
            or complete_archive_root != CHATGPT_COMPLETE_ARCHIVE_ROOT.as_posix()
        ):
            raise SourceRegistryError(
                "chatgpt.parser must name the canonical S09 parser and S08 archive adapter"
            )
        if not (database_dir / raw_archive_entrypoint).is_file():
            raise SourceRegistryError("chatgpt raw archive entrypoint does not exist")
        if not (database_dir / raw_archive_contract_ref).is_file():
            raise SourceRegistryError("chatgpt raw archive contract does not exist")
    elif source_type == "codex_local":
        raw_archive_entrypoint = _repo_relative_path(
            parser.get("raw_archive_entrypoint"),
            f"{source_id}.parser.raw_archive_entrypoint",
            ("scripts/",),
        )
        raw_archive_contract_ref = _repo_relative_path(
            parser.get("raw_archive_contract_ref"),
            f"{source_id}.parser.raw_archive_contract_ref",
            ("config/data_sources/",),
        )
        complete_archive_root = _repo_relative_path(
            parser.get("complete_archive_root"),
            f"{source_id}.parser.complete_archive_root",
            ("data/raw_archives/",),
        )
        sync_state_entrypoint = _repo_relative_path(
            parser.get("sync_state_entrypoint"),
            f"{source_id}.parser.sync_state_entrypoint",
            ("scripts/",),
        )
        sync_state_contract_ref = _repo_relative_path(
            parser.get("sync_state_contract_ref"),
            f"{source_id}.parser.sync_state_contract_ref",
            ("config/data_sources/",),
        )
        derived_entrypoint = _repo_relative_path(
            parser.get("derived_entrypoint"),
            f"{source_id}.parser.derived_entrypoint",
            ("scripts/",),
        )
        derived_contract_ref = _repo_relative_path(
            parser.get("derived_contract_ref"),
            f"{source_id}.parser.derived_contract_ref",
            ("config/data_sources/",),
        )
        legacy_summary_entrypoint = _repo_relative_path(
            parser.get("legacy_summary_entrypoint"),
            f"{source_id}.parser.legacy_summary_entrypoint",
            ("scripts/",),
        )
        legacy_summary_contract_ref = _repo_relative_path(
            parser.get("legacy_summary_contract_ref"),
            f"{source_id}.parser.legacy_summary_contract_ref",
            ("config/data_sources/",),
        )
        push_main_entrypoint = _repo_relative_path(
            parser.get("push_main_entrypoint"),
            f"{source_id}.parser.push_main_entrypoint",
            ("scripts/",),
        )
        push_main_contract_ref = _repo_relative_path(
            parser.get("push_main_contract_ref"),
            f"{source_id}.parser.push_main_contract_ref",
            ("config/data_sources/",),
        )
        scheduler_entrypoint = _repo_relative_path(
            parser.get("scheduler_entrypoint"),
            f"{source_id}.parser.scheduler_entrypoint",
            ("scripts/",),
        )
        scheduler_profile_ref = _repo_relative_path(
            parser.get("scheduler_profile_ref"),
            f"{source_id}.parser.scheduler_profile_ref",
            ("config/data_sources/",),
        )
        if (
            raw_archive_entrypoint != CODEX_PUBLIC_RAW_ARCHIVE_ENTRYPOINT.as_posix()
            or raw_archive_contract_ref
            != CODEX_PUBLIC_RAW_ARCHIVE_CONTRACT_PATH.as_posix()
            or complete_archive_root != CODEX_COMPLETE_ARCHIVE_ROOT.as_posix()
            or sync_state_entrypoint != CODEX_SYNC_STATE_ENTRYPOINT.as_posix()
            or sync_state_contract_ref != CODEX_SYNC_STATE_CONTRACT_PATH.as_posix()
            or derived_entrypoint != CODEX_DERIVED_ENTRYPOINT.as_posix()
            or derived_contract_ref != CODEX_DERIVED_CONTRACT_PATH.as_posix()
            or legacy_summary_entrypoint
            != CODEX_LEGACY_SUMMARY_ENTRYPOINT.as_posix()
            or legacy_summary_contract_ref
            != CODEX_LEGACY_SUMMARY_CONTRACT_PATH.as_posix()
            or push_main_entrypoint != CODEX_PUSH_MAIN_ENTRYPOINT.as_posix()
            or push_main_contract_ref != CODEX_PUSH_MAIN_CONTRACT_PATH.as_posix()
            or scheduler_entrypoint != CODEX_SCHEDULER_ENTRYPOINT.as_posix()
            or scheduler_profile_ref != CODEX_SCHEDULER_PROFILE_PATH.as_posix()
        ):
            raise SourceRegistryError(
                "codex.parser must name the canonical S07 raw, state, derived, legacy-summary, push-main and scheduler adapters"
            )
        if not (database_dir / raw_archive_entrypoint).is_file():
            raise SourceRegistryError("codex raw archive entrypoint does not exist")
        if not (database_dir / raw_archive_contract_ref).is_file():
            raise SourceRegistryError("codex raw archive contract does not exist")
        if not (database_dir / sync_state_entrypoint).is_file():
            raise SourceRegistryError("codex sync-state entrypoint does not exist")
        if not (database_dir / sync_state_contract_ref).is_file():
            raise SourceRegistryError("codex sync-state contract does not exist")
        if not (database_dir / derived_entrypoint).is_file():
            raise SourceRegistryError("codex derived entrypoint does not exist")
        if not (database_dir / derived_contract_ref).is_file():
            raise SourceRegistryError("codex derived contract does not exist")
        if not (database_dir / legacy_summary_entrypoint).is_file():
            raise SourceRegistryError("codex legacy-summary entrypoint does not exist")
        if not (database_dir / legacy_summary_contract_ref).is_file():
            raise SourceRegistryError("codex legacy-summary contract does not exist")
        if not (database_dir / push_main_entrypoint).is_file():
            raise SourceRegistryError("codex push-main entrypoint does not exist")
        if not (database_dir / push_main_contract_ref).is_file():
            raise SourceRegistryError("codex push-main contract does not exist")
        if not (database_dir / scheduler_entrypoint).is_file():
            raise SourceRegistryError("codex scheduler entrypoint does not exist")
        if not (database_dir / scheduler_profile_ref).is_file():
            raise SourceRegistryError("codex scheduler profile does not exist")
    elif any(
        key in parser
        for key in (
            "raw_archive_entrypoint",
            "raw_archive_contract_ref",
            "sync_state_entrypoint",
            "sync_state_contract_ref",
            "derived_entrypoint",
            "derived_contract_ref",
            "legacy_summary_entrypoint",
            "legacy_summary_contract_ref",
            "push_main_entrypoint",
            "push_main_contract_ref",
            "scheduler_entrypoint",
            "scheduler_profile_ref",
            "complete_archive_root",
        )
    ):
        raise SourceRegistryError(f"{source_id}.parser cannot claim a canonical raw archive adapter")

    schedule = _mapping(source.get("schedule"), f"{source_id}.schedule")
    if source_type == "codex_local":
        expected_schedule = {
            "mode": "scheduled",
            "frequency": "every_15_minutes",
            "timezone": "Australia/Sydney",
            "interval_seconds": 900,
            "profile_ref": CODEX_SCHEDULER_PROFILE_PATH.as_posix(),
        }
        if schedule != expected_schedule:
            raise SourceRegistryError("codex.schedule must bind the canonical S07-P3-T2 profile")
    else:
        if set(schedule) != {"mode", "frequency", "timezone"}:
            raise SourceRegistryError(f"{source_id}.schedule keys do not match the contract")
        if schedule.get("mode") not in {"manual", "scheduled", "template"}:
            raise SourceRegistryError(f"{source_id}.schedule.mode is unsupported")
        _non_empty_string(schedule.get("frequency"), f"{source_id}.schedule.frequency")
        if schedule.get("timezone") not in {"local", "UTC"}:
            raise SourceRegistryError(f"{source_id}.schedule.timezone is unsupported")

    state_path = _repo_relative_path(source.get("state_path"), f"{source_id}.state_path", ("data/sync_state/",))
    archive_path = _repo_relative_path(
        source.get("archive_path"),
        f"{source_id}.archive_path",
        ("data/public_raw/",),
    )
    if source_type == "chatgpt_export" and archive_path != "data/public_raw/chatgpt":
        raise SourceRegistryError("chatgpt_export archive_path must be data/public_raw/chatgpt")
    if source_type == "codex_local" and archive_path != "data/public_raw/codex":
        raise SourceRegistryError("codex_local archive_path must be data/public_raw/codex")
    if source_type == "generic_agent" and not archive_path.startswith("data/public_raw/agents/"):
        raise SourceRegistryError("generic_agent archive_path must stay under data/public_raw/agents/")

    derived_outputs = _string_list(source.get("derived_outputs"), f"{source_id}.derived_outputs")
    for index, output_path in enumerate(derived_outputs):
        _repo_relative_path(
            output_path,
            f"{source_id}.derived_outputs[{index}]",
            ("data/derived/", "data/processed/"),
        )

    path_source_id = "{source_id}" if source_id == "generic_agent_template" else source_id
    if source_type == "chatgpt_export":
        expected_state = "data/sync_state/chatgpt.json"
        expected_outputs = [
            "data/processed/conversations/conversation_manifest.jsonl",
            "data/processed/conversations/chatgpt_parse_quarantine.jsonl",
            "data/derived/chatgpt/chatgpt_sync_summary.json",
        ]
    elif source_type == "codex_local":
        expected_state = "data/sync_state/codex.json"
        expected_outputs = [
            "data/processed/codex/codex_session_manifest.jsonl",
            "data/processed/codex/codex_daily_activity.jsonl",
            "data/derived/codex/codex_activity_snapshot.json",
            "data/derived/codex/codex_agent_recommendations.json",
            "data/derived/codex/codex_events.jsonl",
            "data/derived/codex/codex_facets.jsonl",
            "data/derived/codex/codex_behavior_summary.json",
            "data/derived/codex/codex_universe_state_input.json",
            "data/derived/codex/codex_derived_state.json",
        ]
    else:
        expected_state = f"data/sync_state/agents/{path_source_id}.json"
        expected_outputs = [f"data/derived/agents/{path_source_id}/agent_sync_summary.json"]
        if archive_path != f"data/public_raw/agents/{path_source_id}":
            raise SourceRegistryError(f"{source_id}.archive_path does not match the generic adapter convention")
    if state_path != expected_state:
        raise SourceRegistryError(f"{source_id}.state_path does not match the adapter convention")
    if derived_outputs != expected_outputs:
        raise SourceRegistryError(f"{source_id}.derived_outputs do not match the adapter convention")

    if _mapping(source.get("push_policy"), f"{source_id}.push_policy") != push_defaults:
        raise SourceRegistryError(f"{source_id}.push_policy must match the final-delivery-only defaults")

    template_parameters = source.get("template_parameters", [])
    if not isinstance(template_parameters, list) or any(token not in _ALLOWED_TEMPLATE_TOKENS for token in template_parameters):
        raise SourceRegistryError(f"{source_id}.template_parameters contains unsupported tokens")
    if source_id == "generic_agent_template" and template_parameters != ["{source_id}"]:
        raise SourceRegistryError("generic_agent_template must expose the {source_id} parameter")
    if source_id != "generic_agent_template" and template_parameters:
        raise SourceRegistryError(f"{source_id}.template_parameters is only allowed on the generic template")


def validate_source_registry(payload: Any, database_dir: Path) -> dict[str, Any]:
    """Validate and return a canonical registry mapping without mutating it."""

    registry = _mapping(payload, "registry")
    if registry.get("schema_version") != REGISTRY_SCHEMA_VERSION:
        raise SourceRegistryError("registry schema_version is unsupported")
    if not isinstance(registry.get("sources"), list):
        raise SourceRegistryError("registry.sources must preserve the derived-source list")

    contract = _mapping(registry.get("sync_contract"), "sync_contract")
    expected_contract_keys = {
        "schema_version",
        "task_id",
        "required_fields",
        "source_types",
        "required_source_ids",
        "source_read_only",
        "archive_append_only",
        "repository_relative_paths",
        "public_raw_layout_ref",
        "credential_exclusion_ref",
        "raw_ledger_ref",
        "archive_chunking_ref",
        "archive_restore_ref",
        "push_defaults",
    }
    if set(contract) != expected_contract_keys:
        raise SourceRegistryError("sync_contract keys do not match the canonical contract")
    if contract.get("schema_version") != SYNC_CONTRACT_VERSION or contract.get("task_id") != TASK_ID:
        raise SourceRegistryError("sync_contract identity is unsupported")
    if contract.get("required_fields") != list(REQUIRED_SYNC_FIELDS):
        raise SourceRegistryError("sync_contract.required_fields drifted from the TaskPack")
    if contract.get("source_types") != list(SOURCE_TYPES):
        raise SourceRegistryError("sync_contract.source_types drifted from the TaskPack")
    if contract.get("required_source_ids") != list(REQUIRED_SOURCE_IDS):
        raise SourceRegistryError("sync_contract.required_source_ids is incomplete")
    for flag in ("source_read_only", "archive_append_only", "repository_relative_paths"):
        if contract.get(flag) is not True:
            raise SourceRegistryError(f"sync_contract.{flag} must remain true")
    layout_ref = _repo_relative_path(
        contract.get("public_raw_layout_ref"),
        "sync_contract.public_raw_layout_ref",
        ("config/data_sources/",),
    )
    if layout_ref != PUBLIC_RAW_LAYOUT_PATH.as_posix() or not (database_dir / layout_ref).is_file():
        raise SourceRegistryError("sync_contract.public_raw_layout_ref must name the canonical layout contract")
    credential_ref = _repo_relative_path(
        contract.get("credential_exclusion_ref"),
        "sync_contract.credential_exclusion_ref",
        ("config/data_sources/",),
    )
    if credential_ref != CREDENTIAL_CONTRACT_PATH.as_posix():
        raise SourceRegistryError("sync_contract.credential_exclusion_ref must name the canonical contract")
    try:
        load_credential_exclusion_contract(database_dir, database_dir / credential_ref)
    except CredentialExclusionError as exc:
        raise SourceRegistryError("sync_contract credential exclusion contract is invalid") from exc
    raw_ledger_ref = _repo_relative_path(
        contract.get("raw_ledger_ref"),
        "sync_contract.raw_ledger_ref",
        ("config/data_sources/",),
    )
    if raw_ledger_ref != RAW_LEDGER_CONTRACT_PATH.as_posix():
        raise SourceRegistryError("sync_contract.raw_ledger_ref must name the canonical contract")
    try:
        load_raw_ledger_contract(database_dir, database_dir / raw_ledger_ref)
    except RawLedgerError as exc:
        raise SourceRegistryError("sync_contract raw-ledger contract is invalid") from exc
    archive_chunking_ref = _repo_relative_path(
        contract.get("archive_chunking_ref"),
        "sync_contract.archive_chunking_ref",
        ("config/data_sources/",),
    )
    if archive_chunking_ref != ARCHIVE_CHUNKING_CONTRACT_PATH.as_posix():
        raise SourceRegistryError("sync_contract.archive_chunking_ref must name the canonical contract")
    try:
        load_archive_chunking_contract(database_dir, database_dir / archive_chunking_ref)
    except ArchiveChunkError as exc:
        raise SourceRegistryError("sync_contract archive-chunking contract is invalid") from exc
    archive_restore_ref = _repo_relative_path(
        contract.get("archive_restore_ref"),
        "sync_contract.archive_restore_ref",
        ("config/data_sources/",),
    )
    if archive_restore_ref != ARCHIVE_RESTORE_CONTRACT_PATH.as_posix():
        raise SourceRegistryError("sync_contract.archive_restore_ref must name the canonical contract")
    try:
        load_archive_restore_contract(database_dir, database_dir / archive_restore_ref)
    except ArchiveRestoreError as exc:
        raise SourceRegistryError("sync_contract archive-restore contract is invalid") from exc
    if contract.get("push_defaults") != PUSH_DEFAULTS:
        raise SourceRegistryError("sync_contract.push_defaults drifted from the delivery boundary")

    sync_sources = registry.get("sync_sources")
    if not isinstance(sync_sources, list) or not sync_sources:
        raise SourceRegistryError("sync_sources must be a non-empty list")
    source_ids: list[str] = []
    source_types: set[str] = set()
    for index, source_value in enumerate(sync_sources):
        source = _mapping(source_value, f"sync_sources[{index}]")
        _validate_source(source, database_dir, PUSH_DEFAULTS)
        source_ids.append(str(source["source_id"]))
        source_types.add(str(source["source_type"]))
    if len(source_ids) != len(set(source_ids)):
        raise SourceRegistryError("sync_sources source_id values must be unique")
    if not set(REQUIRED_SOURCE_IDS).issubset(source_ids):
        raise SourceRegistryError("sync_sources is missing a required canonical source")
    if source_types != set(SOURCE_TYPES):
        raise SourceRegistryError("sync_sources must cover all TaskPack source types")
    sources_by_id = sync_source_map(registry)
    for source_id, expected_type in REQUIRED_SOURCE_TYPES.items():
        if sources_by_id[source_id]["source_type"] != expected_type:
            raise SourceRegistryError(f"{source_id}.source_type must be {expected_type}")

    serialized = json.dumps(sync_sources, ensure_ascii=False, sort_keys=True)
    if any(prefix in serialized for prefix in ("/Users/", "/home/", "C:\\")):
        raise SourceRegistryError("sync_sources must not hardcode a user absolute path")
    return registry


def load_source_registry(database_dir: Path) -> dict[str, Any]:
    path = database_dir.resolve() / REGISTRY_PATH
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SourceRegistryError(f"cannot read canonical source registry: {path}") from exc
    return validate_source_registry(payload, database_dir.resolve())


def sync_source_map(registry: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {str(source["source_id"]): source for source in registry["sync_sources"]}


def resolve_sync_source(registry: dict[str, Any], requested_source_id: str) -> dict[str, Any]:
    source_id = _CLI_SOURCE_ALIASES.get(requested_source_id, requested_source_id)
    source = sync_source_map(registry).get(source_id)
    if source is None:
        raise SourceRegistryError(f"sync source is not registered: {requested_source_id}")
    return source
