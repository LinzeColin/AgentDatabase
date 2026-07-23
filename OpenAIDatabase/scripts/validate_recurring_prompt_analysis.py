#!/usr/bin/env python3
"""Validate recurring-prompt outputs and optional deterministic build pairs."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from recurring_prompt_core import compare_semantic_outputs, compare_trees, validate_outputs


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate recurring-prompt derived outputs.")
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
    parser.add_argument("--compare-left", type=Path)
    parser.add_argument("--compare-right", type=Path)
    parser.add_argument(
        "--semantic-compare",
        action="store_true",
        help="Compare result-bearing files while ignoring run-local diagnostics in run_manifest.json.",
    )
    parser.add_argument("--skip-source-check", action="store_true")
    return parser


def resolve(root: Path, value: Path) -> Path:
    return value if value.is_absolute() else root / value


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = args.repo_root.resolve()
    errors = validate_outputs(
        repo_root=repo_root,
        config_path=resolve(repo_root, args.config),
        output_dir=resolve(repo_root, args.output_dir),
        summary_path=resolve(repo_root, args.summary_output),
        status_path=resolve(repo_root, args.status_output),
        check_sources=not args.skip_source_check,
    )
    if (args.compare_left is None) != (args.compare_right is None):
        errors.append("--compare-left and --compare-right must be provided together")
    elif args.compare_left and args.compare_right:
        comparator = compare_semantic_outputs if args.semantic_compare else compare_trees
        differences = comparator(
            resolve(repo_root, args.compare_left), resolve(repo_root, args.compare_right)
        )
        if differences:
            errors.append("non-deterministic build outputs: " + ", ".join(differences))
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1
    print("PASS: recurring-prompt outputs are valid, source-linked, privacy-scanned and zero-LLM")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
