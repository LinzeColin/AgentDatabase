#!/usr/bin/env python3
"""Run production current reconstruction and pass only its exact sealed block."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table.current_regression import (  # noqa: E402
    CurrentRegressionError,
    publish_expected_block_validation,
    validate_current_expected_block,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Independent R11 harness. Returns 0 only for exact EXPECTED_BLOCKED behavior."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--current-source-contract", required=True)
    parser.add_argument("--current-source-contract-sha256", required=True)
    parser.add_argument("--expected-block-contract", required=True)
    parser.add_argument("--expected-block-contract-sha256", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--production-output-dir", required=True)
    parser.add_argument("--harness-output-dir", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    production_output = Path(args.production_output_dir).expanduser().absolute()
    harness_output = Path(args.harness_output_dir).expanduser().absolute()
    command = [
        sys.executable,
        str(MODULE_ROOT / "scripts" / "run_current_source_reconstruction.py"),
        "--run-id",
        args.run_id,
        "--input-root",
        str(Path(args.input_root).expanduser()),
        "--current-source-contract",
        str(Path(args.current_source_contract).expanduser()),
        "--current-source-contract-sha256",
        args.current_source_contract_sha256,
        "--as-of",
        args.as_of,
        "--output-dir",
        str(production_output),
    ]
    completed = subprocess.run(command, cwd=str(MODULE_ROOT), capture_output=True, text=False, check=False)
    payload = dict(
        validate_current_expected_block(
            production_output_dir=production_output,
            production_exit_code=completed.returncode,
            input_root=Path(args.input_root).expanduser(),
            source_contract_path=Path(args.current_source_contract).expanduser(),
            source_contract_sha256=args.current_source_contract_sha256,
            expected_contract_path=Path(args.expected_block_contract).expanduser(),
            expected_contract_sha256=args.expected_block_contract_sha256,
        )
    )
    payload["production_stdout_sha256"] = hashlib.sha256(completed.stdout).hexdigest()
    payload["production_stderr_sha256"] = hashlib.sha256(completed.stderr).hexdigest()
    payload["production_command_argument_count"] = len(command)
    try:
        published = publish_expected_block_validation(payload, output_dir=harness_output)
    except CurrentRegressionError as exc:
        print(
            json.dumps(
                {
                    "status": "HARNESS_PUBLISH_FAILED",
                    "error_code": exc.code,
                    "production_output_dir": str(production_output),
                    "harness_output_dir": str(harness_output),
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
                "status": "EXPECTED_BLOCKED" if published.passed else "FAILED",
                "production_exit_code": completed.returncode,
                "production_output_dir": str(production_output),
                "production_output_index": str(production_output / "OUTPUT_INDEX.md"),
                "harness_output_dir": str(published.output_dir),
                "harness_primary_output": str(published.primary_output),
                "harness_output_index": str(published.output_index_md),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0 if published.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
