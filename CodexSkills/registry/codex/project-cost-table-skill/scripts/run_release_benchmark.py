#!/usr/bin/env python3
"""Run the R12 private bound-snapshot performance gate.

The parent process launches every sample in a fresh Python process. The first
sample is the cold application-process baseline; subsequent samples may benefit
from operating-system file cache, but each still reopens and fully hashes every
selected source. No application cache or source-body parsing is used.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Mapping


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table.release import (  # noqa: E402
    PerformanceBudget,
    PerformanceSample,
    ReleaseError,
    evaluate_performance,
    measure_bound_snapshot_once,
    publish_performance_summary,
    release_code_fingerprint,
    verify_performance_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="R12 bound private snapshot cold/subsequent benchmark; prints absolute output locators."
    )
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--current-source-contract", required=True)
    parser.add_argument("--current-source-contract-sha256", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument(
        "--performance-budget",
        default=str(MODULE_ROOT / "config" / "performance_budgets.yml"),
    )
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--phase", choices=("COLD_PROCESS", "SUBSEQUENT_PROCESS"), help=argparse.SUPPRESS)
    parser.add_argument("--sample-index", type=int, help=argparse.SUPPRESS)
    return parser


def _worker(args: argparse.Namespace) -> int:
    try:
        sample = measure_bound_snapshot_once(
            phase=args.phase,
            sample_index=args.sample_index,
            input_root=Path(args.input_root).expanduser(),
            contract_path=Path(args.current_source_contract).expanduser(),
            contract_sha256=args.current_source_contract_sha256,
        )
    except ReleaseError as exc:
        print(json.dumps({"status": "FAILED", "error_code": exc.code}, sort_keys=True))
        return 4
    print(json.dumps(sample.as_dict(), sort_keys=True))
    return 0


def _run_worker(args: argparse.Namespace, phase: str, sample_index: int) -> PerformanceSample:
    command = [
        sys.executable,
        str(Path(__file__).resolve()),
        "--worker",
        "--phase",
        phase,
        "--sample-index",
        str(sample_index),
        "--input-root",
        str(Path(args.input_root).expanduser()),
        "--current-source-contract",
        str(Path(args.current_source_contract).expanduser()),
        "--current-source-contract-sha256",
        args.current_source_contract_sha256,
        "--output-dir",
        str(Path(args.output_dir).expanduser()),
        "--performance-budget",
        str(Path(args.performance_budget).expanduser()),
    ]
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        command,
        cwd=str(MODULE_ROOT),
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    try:
        payload: Mapping[str, Any] = json.loads(completed.stdout)
    except (json.JSONDecodeError, UnicodeError) as exc:
        raise ReleaseError("BENCHMARK_WORKER_PROTOCOL", "benchmark worker returned invalid aggregate JSON") from exc
    if completed.returncode != 0:
        code = payload.get("error_code") if isinstance(payload, dict) else None
        raise ReleaseError(
            code if isinstance(code, str) else "BENCHMARK_WORKER_FAILED",
            "benchmark worker failed a bound snapshot gate",
        )
    return PerformanceSample.from_mapping(payload)


def _validate_output_boundary(input_root: Path, output_dir: Path) -> None:
    if not output_dir.is_absolute() or output_dir.exists() or not output_dir.parent.is_dir():
        raise ReleaseError("OUTPUT_DIR_INVALID", "output must be a new absolute directory with an existing parent")
    if output_dir.parent.is_symlink():
        raise ReleaseError("OUTPUT_PARENT_SYMLINK", "output parent must not be a symbolic link")
    try:
        resolved_input = input_root.resolve(strict=True)
        resolved_parent = output_dir.parent.resolve(strict=True)
    except OSError as exc:
        raise ReleaseError("PATH_RESOLUTION_FAILED", "input/output roots cannot be resolved") from exc
    if resolved_parent == resolved_input or resolved_input in resolved_parent.parents:
        raise ReleaseError("OUTPUT_OVERLAPS_INPUT", "benchmark output must remain outside the raw input root")


def main() -> int:
    args = build_parser().parse_args()
    if args.worker:
        if args.phase is None or args.sample_index is None:
            print(json.dumps({"status": "FAILED", "error_code": "WORKER_ARGUMENTS_MISSING"}, sort_keys=True))
            return 4
        return _worker(args)
    output_dir = Path(args.output_dir).expanduser().absolute()
    try:
        budget = PerformanceBudget.from_yaml(Path(args.performance_budget).expanduser())
        _validate_output_boundary(Path(args.input_root).expanduser(), output_dir)
        samples = [
            _run_worker(args, "COLD_PROCESS", index)
            for index in range(1, budget.cold_process_runs + 1)
        ]
        samples.extend(
            _run_worker(args, "SUBSEQUENT_PROCESS", index)
            for index in range(1, budget.subsequent_process_runs + 1)
        )
        product_version = (MODULE_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        summary = evaluate_performance(
            budget,
            samples,
            product_version=product_version,
            release_code_sha256=release_code_fingerprint(MODULE_ROOT),
        )
        published = publish_performance_summary(summary, output_dir=output_dir)
        if not verify_performance_bundle(output_dir):
            raise ReleaseError("PERFORMANCE_BUNDLE_VERIFICATION", "published performance bundle failed its detached seal")
    except ReleaseError as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED_BEFORE_VERIFIED_OUTPUT",
                    "error_code": exc.code,
                    "output_dir": str(output_dir),
                    "output_index": str(output_dir / "OUTPUT_INDEX.md"),
                    "next_step": "修复性能/快照/路径门禁并使用新的绝对输出目录重试。",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 4
    print(published.locator_text())
    print(
        json.dumps(
            {
                "status": "PERFORMANCE_PASS" if published.passed else "PERFORMANCE_FAILED",
                "output_dir": str(published.output_dir),
                "primary_output": str(published.primary_output),
                "output_index": str(published.output_index_md),
                "real_calculation_baseline_status": summary["real_calculation_baseline_status"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if published.passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
