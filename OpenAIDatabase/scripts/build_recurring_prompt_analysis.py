#!/usr/bin/env python3
"""CLI entry point for deterministic recurring-prompt analysis."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
from pathlib import Path

from recurring_prompt_core import AnalysisError, build_analysis, parse_timestamp


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Build zero-LLM recurring-prompt candidate analytics from sanitized Codex JSONL."
    )
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("OpenAIDatabase/config/behavior/recurring_prompt_analysis.json"),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path(
            "OpenAIDatabase/data/derived/behavior_intelligence/recurring_prompts"
        ),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("OpenAIDatabase/人类可读/00_Recurring分析_最新.md"),
    )
    parser.add_argument(
        "--status-output",
        type=Path,
        default=Path("OpenAIDatabase/人类可读/00_Recurring运行状态.md"),
    )
    parser.add_argument("--previous-output-dir", type=Path)
    parser.add_argument("--source-commit", default="unknown")
    parser.add_argument(
        "--as-of",
        help="ISO-8601 analysis timestamp. Required for deterministic CI; defaults to current UTC only for local preview.",
    )
    parser.add_argument("--force-full", action="store_true")
    parser.add_argument(
        "--no-atomic-publish",
        action="store_true",
        help="Write directly to the requested output paths; intended only for disposable CI build directories.",
    )
    return parser


def resolve_under(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    parsed_as_of = parse_timestamp(args.as_of) if args.as_of else dt.datetime.now(dt.timezone.utc)
    if parsed_as_of is None:
        print(f"ERROR: invalid --as-of timestamp: {args.as_of!r}", file=sys.stderr)
        return 2
    try:
        manifest = build_analysis(
            repo_root=repo_root,
            config_path=resolve_under(repo_root, args.config),
            output_dir=resolve_under(repo_root, args.output_dir),
            summary_path=resolve_under(repo_root, args.summary_output),
            status_path=resolve_under(repo_root, args.status_output),
            previous_output_dir=(
                resolve_under(repo_root, args.previous_output_dir)
                if args.previous_output_dir
                else None
            ),
            source_commit=args.source_commit,
            as_of=parsed_as_of,
            force_full=args.force_full,
            publish_atomically=not args.no_atomic_publish,
        )
    except AnalysisError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
