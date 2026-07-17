from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

from memory_atlas_owner_daily import (
    OWNER_DAILY_STEP_IDS,
    OwnerDailyContext,
    OwnerDailyRunner,
    owner_daily_profile_contract as build_owner_daily_profile_contract,
)

from .constants import ROOT
from .child_process import run_child_command
from .codex_public_raw_archive import run_codex_public_raw_archive
from .codex_push_main import run_codex_push_main
from .codex_scheduler import run_codex_scheduler
from .codex_sync_state import run_codex_sync_state
from .source_registry import (
    PUSH_DEFAULTS,
    SourceRegistryError,
    load_source_registry,
    resolve_sync_source,
    validate_portable_identifier,
)


_DISCOVERY_DESTINATIONS = {
    "--official-export": "official_export",
    "--codex-home": "codex_home",
    "--input": "input",
    "--markdown-report": "markdown_report",
}
_DISCOVERY_EXCLUSIVE_DESTINATIONS = {
    "input": ("input", "markdown_report"),
    "markdown_report": ("input", "markdown_report"),
}
def owner_daily_profile_contract() -> dict[str, object]:
    return build_owner_daily_profile_contract()


def run_profile(args: argparse.Namespace) -> int:
    if args.profile == "codex-scheduler":
        if getattr(args, "step", None) is not None:
            print(json.dumps({
                "status": "FAIL_CLOSED",
                "command": "run",
                "profile": "codex-scheduler",
                "writes_files": False,
                "remote_push": False,
                "中文原因": "Codex scheduler 不接受 Owner Daily step 参数。",
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        return run_codex_scheduler(args)
    if args.profile != "owner-daily":
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "run",
            "profile": args.profile,
            "中文原因": "当前只支持 owner-daily 和 codex-scheduler profile。",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    scheduler_only_options = [
        option
        for option in ("owner_run_id", "state_dir", "codex_home")
        if getattr(args, option, None) is not None
    ]
    if Path(getattr(args, "database_dir", ROOT)).resolve() != ROOT.resolve():
        scheduler_only_options.append("database_dir")
    if scheduler_only_options:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "command": "run",
            "profile": "owner-daily",
            "writes_files": False,
            "remote_push": False,
            "rejected_scheduler_options": scheduler_only_options,
            "中文原因": "Owner Daily 不接受 Codex scheduler 专用参数。",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if args.dry_run:
        runner = OwnerDailyRunner(OwnerDailyContext(source_root=ROOT, python_executable=sys.executable))
        result = runner.retry(args.step) if args.step else runner.run()
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 0 if result.get("status") == "PASS" else 2
    print(json.dumps({
        "status": "FAIL_CLOSED",
        "command": "run",
        "profile": "owner-daily",
        "dry_run": False,
        "writes_files": False,
        "remote_push": False,
        "github_main_upload": False,
        "中文原因": "Owner Daily 只允许八个固定 no-write dry-run；真实写入、推送、发送和部署均被拒绝。",
        "next_safe_command": "python3 scripts/atlasctl.py run --profile owner-daily --dry-run",
    }, ensure_ascii=False, indent=2, sort_keys=True))
    return 2


def chatgpt_contract(redact_for_public_backup: bool = False) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "chatgpt",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "writes_files": False,
        "raw_root": "data/public_raw/chatgpt",
        "derived_summary": "data/derived/chatgpt/chatgpt_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "no_browser_mutation": True,
        "redact_for_public_backup": redact_for_public_backup,
        "processed_manifest": "data/processed/conversations/conversation_manifest.jsonl",
        "canonical_events": {
            "status": "NOT_RUN",
            "events_path": "data/processed/conversations/chatgpt_canonical_events.jsonl",
            "appended_version_count": 0,
            "unchanged_version_count": 0,
            "event_count": 0,
            "writes_files": False,
            "append_only": True,
        },
        "derived_inputs": {
            "status": "NOT_RUN",
            "reason": "dry_run_without_committed_canonical_events",
            "output_paths": {
                "facets": "data/derived/chatgpt/chatgpt_facets.jsonl",
                "topics": "data/derived/chatgpt/chatgpt_topics.json",
                "activity": "data/derived/chatgpt/chatgpt_activity.jsonl",
                "universe_state_input": "data/derived/chatgpt/chatgpt_universe_state_input.json",
                "state": "data/derived/chatgpt/chatgpt_derived_state.json",
            },
            "writes_files": False,
            "raw_mutation": False,
            "canonical_mutation": False,
        },
    }


def codex_contract(public_transcripts: bool = False) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "codex",
        "dry_run": True,
        "sync_mode": "codex_local_sync",
        "writes_files": False,
        "raw_root": "data/public_raw/codex",
        "derived_summary": "data/derived/codex/codex_activity_snapshot.json",
        "legacy_summary_contract": "config/data_sources/codex_legacy_summary.json",
        "artifact_role": "redacted_derived_summary",
        "output_policy": "derived_summary_not_full_raw_backup",
        "full_raw_backup": False,
        "recoverable_raw_backup": False,
        "canonical_raw_archive_root": "data/raw_archives/codex",
        "run_log_dir": "data/run_logs/sync_runs",
        "append_only": True,
        "public_transcripts": public_transcripts,
    }


def future_agent_contract(
    agent_id: str,
    event_id: str | None = None,
    *,
    source_id: str = "future-agent",
) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": source_id,
        "agent_id": agent_id,
        "dry_run": True,
        "adapter_mode": "minimal_adapter",
        "read_adapter": "scripts/inspect_memory_atlas_generic_agent_export.py",
        "adapter_contract": "config/data_sources/generic_agent_read_adapter.json",
        "supported_source_shapes": ["file", "directory"],
        "supported_source_formats": ["json", "jsonl", "sqlite"],
        "source_read_only": True,
        "source_content_in_output": False,
        "sqlite_open_mode": "mode=ro&immutable=1",
        "writes_files": False,
        "raw_root": f"data/public_raw/agents/{agent_id}",
        "derived_summary": f"data/derived/agents/{agent_id}/agent_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "append_only": True,
        "event_id": event_id or "",
    }


def apply_environment_discovery(args: argparse.Namespace, registered_source: dict[str, object]) -> None:
    """Fill an unset source argument from the registry's ordered environment candidates."""

    for candidate in registered_source["discovery"]["candidates"]:  # type: ignore[index]
        if candidate["kind"] != "environment_variable":
            continue
        destination = _DISCOVERY_DESTINATIONS[str(candidate["target_argument"])]
        exclusive_destinations = _DISCOVERY_EXCLUSIVE_DESTINATIONS.get(destination, (destination,))
        if any(getattr(args, field) is not None for field in exclusive_destinations):
            continue
        environment_value = os.environ.get(str(candidate["value"]), "").strip()
        if environment_value:
            setattr(args, destination, Path(environment_value).expanduser())
            return


def assert_sync_execution_policy(registered_source: dict[str, object]) -> None:
    if registered_source.get("push_policy") != PUSH_DEFAULTS:
        raise SourceRegistryError("sync execution requires the final-delivery-only push policy")


def run_sync(args: argparse.Namespace) -> int:
    try:
        registry = load_source_registry(ROOT)
        registered_source = resolve_sync_source(registry, args.source)
        assert_sync_execution_policy(registered_source)
        apply_environment_discovery(args, registered_source)
    except SourceRegistryError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": args.source,
            "reason": str(exc),
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    source_type = str(registered_source["source_type"])
    parser_path = ROOT / str(registered_source["parser"]["entrypoint"])
    generic_agent_id = args.agent_id
    registered_source_id = str(registered_source["source_id"])
    if registered_source.get("status") == "fixture" and not args.dry_run:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": registered_source_id,
            "reason": "fixture source is acceptance-only; use --dry-run or the isolated fixture verifier",
            "writes_files": False,
            "production_database_mutation": False,
            "remote_push_attempted": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if bool(getattr(args, "push_main", False)):
        args.database_dir = ROOT
        return run_codex_push_main(args)
    if args.raw_archive:
        if source_type != "codex_local":
            print(json.dumps({
                "status": "FAIL_CLOSED",
                "source_id": args.source,
                "reason": "raw archive mode is reserved for the canonical Codex source",
                "writes_files": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        args.database_dir = ROOT
        if bool(getattr(args, "incremental", False)):
            return run_codex_sync_state(args)
        return run_codex_public_raw_archive(args)
    if bool(getattr(args, "incremental", False)):
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": args.source,
            "reason": "--incremental requires --raw-archive",
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if args.archive_id:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": args.source,
            "reason": "--archive-id requires --raw-archive",
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    if source_type == "generic_agent":
        try:
            validate_portable_identifier(generic_agent_id, "agent_id", max_length=128)
        except SourceRegistryError as exc:
            print(json.dumps({
                "status": "FAIL_CLOSED",
                "source_id": args.source,
                "reason": str(exc),
                "writes_files": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    concrete_generic_source = (
        source_type == "generic_agent"
        and registered_source_id != "generic_agent_template"
        and args.source != "future-agent"
    )
    if concrete_generic_source:
        if args.agent_id not in {"future-agent", registered_source_id}:
            print(json.dumps({
                "status": "FAIL_CLOSED",
                "source_id": registered_source_id,
                "reason": "registered generic source identity cannot be overridden by --agent-id",
                "writes_files": False,
            }, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
        generic_agent_id = registered_source_id

    concrete_generic_ids = {
        str(source["source_id"])
        for source in registry["sync_sources"]
        if source["source_type"] == "generic_agent"
        and source["source_id"] != "generic_agent_template"
    }
    if (
        source_type == "generic_agent"
        and registered_source_id == "generic_agent_template"
        and generic_agent_id in concrete_generic_ids
    ):
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": args.source,
            "reason": "generic template cannot claim a registered source namespace",
            "writes_files": False,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    generic_source_identity = registered_source_id
    if source_type == "generic_agent":
        if args.source == "future-agent":
            generic_source_identity = "future-agent"
        elif registered_source_id == "generic_agent_template":
            generic_source_identity = generic_agent_id

    if source_type == "chatgpt_export" and args.dry_run and not args.official_export:
        print(json.dumps(chatgpt_contract(args.redact_for_public_backup), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if source_type == "codex_local" and args.dry_run and not args.codex_home:
        print(json.dumps(codex_contract(args.public_transcripts), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if source_type == "generic_agent" and args.dry_run and not args.input and not args.markdown_report:
        print(json.dumps(
            future_agent_contract(generic_agent_id, args.event_id, source_id=generic_source_identity),
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        ))
        return 0

    if source_type == "chatgpt_export":
        command = [sys.executable, str(parser_path), "--database-dir", str(ROOT)]
        if args.official_export:
            command.extend(["--official-export", str(args.official_export)])
        if args.redact_for_public_backup:
            command.append("--redact-for-public-backup")
        if args.dry_run:
            command.append("--dry-run")
    elif source_type == "codex_local":
        command = [sys.executable, str(parser_path), "--database-dir", str(ROOT)]
        if args.codex_home:
            command.extend(["--codex-home", str(args.codex_home)])
        if args.public_transcripts:
            command.append("--public-transcripts")
        if args.dry_run:
            command.append("--dry-run")
    elif source_type == "generic_agent":
        command = [
            sys.executable,
            str(parser_path),
            "--database-dir",
            str(ROOT),
            "--source-id",
            generic_source_identity,
            "--agent-id",
            generic_agent_id,
        ]
        if args.input:
            command.extend(["--input", str(args.input)])
        if args.markdown_report:
            command.extend(["--markdown-report", str(args.markdown_report)])
        if args.event_id:
            command.extend(["--event-id", args.event_id])
        if args.dry_run:
            command.append("--dry-run")
    else:  # pragma: no cover - registry validation owns the allowed source types.
        raise AssertionError(f"unreachable source type: {source_type}")

    return run_child_command(command, cwd=ROOT)

__all__ = (
    "OWNER_DAILY_STEP_IDS",
    "OwnerDailyContext",
    "OwnerDailyRunner",
    "build_owner_daily_profile_contract",
    "owner_daily_profile_contract",
    "run_profile",
    "chatgpt_contract",
    "codex_contract",
    "future_agent_contract",
    "apply_environment_discovery",
    "assert_sync_execution_policy",
    "run_sync",
)
