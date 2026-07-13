from __future__ import annotations

import argparse
import json
import sys

from .constants import (
    BUILD_ATLAS,
    CHATGPT_DEEP_EXPLORE_BUILDER,
    PERSONALIZATION_BUILDER,
    ROOT,
)
from .child_process import run_child_command


def run_build_atlas(args: argparse.Namespace) -> int:
    output = "data/derived/visualization/memory_atlas.json"
    if args.dry_run:
        print(json.dumps({
            "status": "PASS",
            "command": "build-atlas",
            "dry_run": True,
            "writes_files": False,
            "output": output,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    command = [sys.executable, str(BUILD_ATLAS), "--database-dir", str(ROOT), "--output", output]
    return run_child_command(command, cwd=ROOT)


def personalization_targets(target: str) -> list[str]:
    if target == "all":
        return ["chatgpt", "codex", "other_agent"]
    if target == "other-agent":
        return ["other_agent"]
    return [target]


def personalization_prompt_contract(args: argparse.Namespace) -> dict[str, object]:
    return {
        "status": "PASS",
        "command": "generate-personalization-prompt",
        "task_id": "MA-V12-S12P2",
        "acceptance_id": "ACC-MA-V12-S12P2",
        "prompt_version": "personalization_prompt.v1_2_s12_p2",
        "dry_run": True,
        "writes_files": False,
        "sends_to_chatgpt": False,
        "raw_mutation": False,
        "targets": personalization_targets(args.target),
        "source_reports": [
            "data/derived/personalization/personalization_export.json",
            "data/derived/behavior_intelligence/events.json",
            "data/derived/behavior_intelligence/clusters.json",
            "data/derived/behavior_intelligence/latent_signals.json",
            "data/derived/behavior_intelligence/self_iteration_suggestions.json",
            "data/derived/behavior_intelligence/decision_debt_ledger.json",
            "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
        ],
        "output_contract": {
            "human_zh": "data/derived/personalization/personalization_prompt_human_zh.md",
            "chatgpt": "data/derived/personalization/chatgpt_personalization.md",
            "codex": "data/derived/personalization/codex_personalization.md",
            "machine": "data/derived/personalization/personalization_export.json",
            "other_agent": "data/derived/personalization/other_agent_personalization.md",
        },
        "boundary": {
            "user_trigger_required": True,
            "no_automatic_send": True,
            "no_cookie_token_secret_export": True,
            "raw_mutation": False,
            "proposal_apply_execution": False,
            "chatgpt_deep_explore_deferred_to": "S12 P3",
        },
    }


def run_generate_personalization_prompt(args: argparse.Namespace) -> int:
    if args.dry_run:
        print(json.dumps(personalization_prompt_contract(args), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    command = [sys.executable, str(PERSONALIZATION_BUILDER), "--database-dir", str(args.database_dir)]
    return run_child_command(command, cwd=ROOT)


def chatgpt_deep_explore_contract(args: argparse.Namespace) -> dict[str, object]:
    return {
        "status": "PASS",
        "command": args.command,
        "task_id": "MA-V12-S12P3",
        "acceptance_id": "ACC-MA-V12-S12P3",
        "contract_version": "chatgpt_deep_explore.v1_2_s12_p3",
        "dry_run": True,
        "mode": args.mode,
        "writes_files": False,
        "opens_browser": False,
        "sends_to_chatgpt": False,
        "source_reports": [
            "data/derived/personalization/personalization_export.json",
            "data/derived/personalization/personalization_prompt_human_zh.md",
            "data/derived/behavior_intelligence/latent_signals.json",
            "data/derived/behavior_intelligence/self_iteration_suggestions.json",
            "data/derived/behavior_intelligence/decision_debt_ledger.json",
            "data/derived/agent_collaboration/agent_collaboration_quality_report.json",
        ],
        "output_contract": {
            "prompt": "data/derived/chatgpt_deep_explore/latest_memory_analysis_prompt.md",
            "machine": "data/derived/chatgpt_deep_explore/chatgpt_deep_explore_export.json",
            "chatgpt_launch_url": "https://chatgpt.com/?q=<encoded_prompt>",
        },
        "boundary": {
            "user_trigger_required": True,
            "default_mode": "prefill_only",
            "allowed_modes": ["prefill_only", "auto_submit"],
            "no_silent_send": True,
            "no_cookie_token_secret_export": True,
            "raw_mutation": False,
            "proposal_apply_execution": False,
            "auto_submit_requires_explicit_config": True,
        },
        "builder": "scripts/build_chatgpt_deep_explore_prompt.py",
    }


def run_chatgpt_deep_explore(args: argparse.Namespace) -> int:
    if args.dry_run:
        print(json.dumps(chatgpt_deep_explore_contract(args), ensure_ascii=False, indent=2, sort_keys=True))
        return 0
    command = [
        sys.executable,
        str(CHATGPT_DEEP_EXPLORE_BUILDER),
        "--database-dir",
        str(args.database_dir),
        "--mode",
        args.mode,
    ]
    if args.open:
        command.append("--open")
    if args.confirm_auto_submit:
        command.append("--confirm-auto-submit")
    return run_child_command(command, cwd=ROOT)

__all__ = (
    "run_build_atlas",
    "personalization_targets",
    "personalization_prompt_contract",
    "run_generate_personalization_prompt",
    "chatgpt_deep_explore_contract",
    "run_chatgpt_deep_explore",
)
