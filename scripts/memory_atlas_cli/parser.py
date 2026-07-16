from __future__ import annotations

import argparse
from pathlib import Path

from memory_atlas_owner_daily import OWNER_DAILY_STEP_IDS
from .constants import ROOT


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas control CLI.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser("run", help="Run a named low-burden Memory Atlas profile.")
    run.add_argument("--profile", choices=["owner-daily", "codex-scheduler"], required=True)
    run.add_argument("--dry-run", action="store_true")
    run.add_argument("--step", choices=OWNER_DAILY_STEP_IDS)
    run.add_argument("--owner-run-id")
    run.add_argument("--state-dir", type=Path)
    run.add_argument("--codex-home", type=Path)
    run.add_argument("--database-dir", type=Path, default=ROOT)

    sync = subparsers.add_parser("sync", help="Run source sync.")
    sync.add_argument("source_name", nargs="?", help="Source id, for example codex.")
    sync.add_argument("--source", dest="source_option")
    sync.add_argument("--dry-run", action="store_true")
    sync.add_argument("--official-export", type=Path)
    sync.add_argument("--redact-for-public-backup", action="store_true")
    sync.add_argument("--codex-home", type=Path)
    sync.add_argument("--public-transcripts", action="store_true")
    sync.add_argument(
        "--raw-archive",
        action="store_true",
        help="Create a recoverable Codex public raw archive.",
    )
    sync.add_argument(
        "--incremental",
        action="store_true",
        help="Use the S07-P1-T3 cursor, content dedupe and interrupted-run resume state.",
    )
    sync.add_argument("--archive-id", help="Explicit append-only Codex raw archive id.")
    sync.add_argument(
        "--push-main",
        action="store_true",
        help="Run the guarded Codex validate, commit and direct-main push flow.",
    )
    sync.add_argument("--message", help="Commit message for --push-main.")
    sync.add_argument("--agent-id", default="future-agent")
    future_input = sync.add_mutually_exclusive_group()
    future_input.add_argument("--input", type=Path)
    future_input.add_argument("--markdown-report", type=Path)
    sync.add_argument("--event-id")

    build_atlas = subparsers.add_parser("build-atlas", help="Build derived Memory Atlas visualization data.")
    build_atlas.add_argument("--dry-run", action="store_true")

    analyze = subparsers.add_parser("analyze", help="Run derived behavior intelligence analysis.")
    analyze.add_argument("--stage", required=True)
    analyze.add_argument("--dry-run", action="store_true")
    analyze.add_argument("--database-dir", type=Path, default=ROOT)
    analyze.add_argument("--source")
    analyze.add_argument("--time-from")
    analyze.add_argument("--time-to")
    analyze.add_argument("--project")
    analyze.add_argument("--task")
    analyze.add_argument("--language")

    audit = subparsers.add_parser("audit", help="Run Memory Atlas derived evidence audits.")
    audit.add_argument("--check")
    audit.add_argument("--dry-run", action="store_true")
    audit.add_argument("--require-built-dist", action="store_true")
    audit.add_argument("--ci-checkout", action="store_true")
    audit.add_argument("--push-scope", choices=["staged", "pending", "all"], default="staged")
    audit.add_argument("--expected-remote-oid")
    audit.add_argument("--database-dir", type=Path, default=ROOT)
    audit.add_argument("--codex-home", type=Path)
    audit.add_argument("--archive-id")

    push = subparsers.add_parser("push", help="Prepare local GitHub backup scope.")
    mode = push.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    push.add_argument("--database-dir", type=Path, default=ROOT)
    push.add_argument("--message", default="Memory Atlas GitHub backup snapshot")

    prompt = subparsers.add_parser("generate-personalization-prompt", help="Generate agent personalization prompt exports.")
    prompt.add_argument("--dry-run", action="store_true")
    prompt.add_argument("--database-dir", type=Path, default=ROOT)
    prompt.add_argument("--target", choices=["all", "chatgpt", "codex", "other-agent"], default="all")

    deep_explore = subparsers.add_parser("chatgpt-deep-explore", help="Prepare a user-triggered ChatGPT deep exploration prompt.")
    deep_explore.add_argument("--dry-run", action="store_true")
    deep_explore.add_argument("--database-dir", type=Path, default=ROOT)
    deep_explore.add_argument("--mode", choices=["prefill_only", "auto_submit"], default="prefill_only")
    deep_explore.add_argument("--open", action="store_true")
    deep_explore.add_argument("--confirm-auto-submit", action="store_true")

    deep_explore_alias = subparsers.add_parser("deep-explore", help="Unified alias for the ChatGPT deep exploration dry-run flow.")
    deep_explore_alias.add_argument("--dry-run", action="store_true")
    deep_explore_alias.add_argument("--database-dir", type=Path, default=ROOT)
    deep_explore_alias.add_argument("--mode", choices=["prefill_only", "auto_submit"], default="prefill_only")
    deep_explore_alias.add_argument("--open", action="store_true")
    deep_explore_alias.add_argument("--confirm-auto-submit", action="store_true")

    proposals = subparsers.add_parser("proposals", help="Inspect proposal authorization and review views.")
    proposals.add_argument("--dry-run", action="store_true")
    proposals.add_argument("--database-dir", type=Path, default=ROOT)
    proposals.add_argument("--view", choices=["state-machine", "diff-narrator"], default="state-machine")

    apply = subparsers.add_parser("apply", help="Apply an approved proposal or inspect the fail-closed dry-run.")
    apply.add_argument("--proposal", required=True)
    apply.add_argument("--dry-run", action="store_true")
    apply.add_argument("--database-dir", type=Path, default=ROOT)
    apply.add_argument("--simulate-validation-failure", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "sync":
        source_name = args.source_name
        source_option = args.source_option
        if source_name and source_option and source_name != source_option:
            parser.error("sync positional source and --source must match")
        args.source = source_option or source_name
        if not args.source:
            parser.error("sync requires a source or --source")
        del args.source_name
        del args.source_option
    return args

__all__ = (
    "parse_args",
)
