from __future__ import annotations

import argparse
import json
import subprocess
import sys

from memory_atlas_owner_daily import (
    OWNER_DAILY_STEP_IDS,
    OwnerDailyContext,
    OwnerDailyRunner,
    owner_daily_profile_contract as build_owner_daily_profile_contract,
)

from .constants import (
    CHATGPT_SYNC,
    CODEX_SYNC,
    FUTURE_AGENT_SYNC,
    ROOT,
)


def owner_daily_profile_contract() -> dict[str, object]:
    return build_owner_daily_profile_contract()


def run_profile(args: argparse.Namespace) -> int:
    if args.profile != "owner-daily":
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "command": "run",
            "profile": args.profile,
            "中文原因": "当前只支持 owner-daily profile。",
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
        "run_log_dir": "data/run_logs/sync_runs",
        "append_only": True,
        "public_transcripts": public_transcripts,
    }


def future_agent_contract(agent_id: str, event_id: str | None = None) -> dict[str, object]:
    return {
        "status": "PASS",
        "source_id": "future-agent",
        "agent_id": agent_id,
        "dry_run": True,
        "adapter_mode": "minimal_adapter",
        "writes_files": False,
        "raw_root": f"data/public_raw/agents/{agent_id}",
        "derived_summary": f"data/derived/agents/{agent_id}/agent_sync_summary.json",
        "run_log_dir": "data/run_logs/sync_runs",
        "input_required_for_apply": True,
        "append_only": True,
        "event_id": event_id or "",
    }


def run_sync(args: argparse.Namespace) -> int:
    if args.source == "chatgpt" and args.dry_run and not args.official_export:
        print(json.dumps(chatgpt_contract(args.redact_for_public_backup), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "codex" and args.dry_run and not args.codex_home:
        print(json.dumps(codex_contract(args.public_transcripts), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "future-agent" and args.dry_run and not args.input and not args.markdown_report:
        print(json.dumps(future_agent_contract(args.agent_id, args.event_id), ensure_ascii=False, indent=2, sort_keys=True))
        return 0

    if args.source == "chatgpt":
        command = [sys.executable, str(CHATGPT_SYNC), "--database-dir", str(ROOT)]
        if args.official_export:
            command.extend(["--official-export", str(args.official_export)])
        if args.redact_for_public_backup:
            command.append("--redact-for-public-backup")
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "codex":
        command = [sys.executable, str(CODEX_SYNC), "--database-dir", str(ROOT)]
        if args.codex_home:
            command.extend(["--codex-home", str(args.codex_home)])
        if args.public_transcripts:
            command.append("--public-transcripts")
        if args.dry_run:
            command.append("--dry-run")
    elif args.source == "future-agent":
        command = [sys.executable, str(FUTURE_AGENT_SYNC), "--database-dir", str(ROOT), "--agent-id", args.agent_id]
        if args.input:
            command.extend(["--input", str(args.input)])
        if args.markdown_report:
            command.extend(["--markdown-report", str(args.markdown_report)])
        if args.event_id:
            command.extend(["--event-id", args.event_id])
        if args.dry_run:
            command.append("--dry-run")
    else:
        print(json.dumps({
            "status": "NOT_IMPLEMENTED",
            "source_id": args.source,
            "reason": "Unknown sync source. Supported sources: chatgpt, codex, future-agent.",
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode

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
    "run_sync",
)
