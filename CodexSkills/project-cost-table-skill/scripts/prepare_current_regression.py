#!/usr/bin/env python3
"""Prepare the sealed private R11 current-source and expected-block contracts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table.current_regression import (  # noqa: E402
    CurrentRegressionError,
    prepare_current_regression_bundle,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Prepare an ignored, hash-bound R11 current-source regression binding before production runs."
    )
    parser.add_argument("--task-pack-root", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--contract-id", required=True)
    parser.add_argument("--as-of", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().absolute()
    try:
        prepared = prepare_current_regression_bundle(
            task_pack_root=Path(args.task_pack_root).expanduser(),
            input_root=Path(args.input_root).expanduser(),
            output_dir=output_dir,
            contract_id=args.contract_id,
            as_of=args.as_of,
        )
    except CurrentRegressionError as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED_BEFORE_BINDING_PUBLISH",
                    "error_code": exc.code,
                    "output_dir": str(output_dir),
                    "next_step": "复核密封 Task Pack、当前源漂移或私有期望；不得覆盖旧快照或改写 blocker。",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 3
    print(prepared.locator_text())
    print(
        json.dumps(
            {
                "status": "CURRENT_REGRESSION_BINDING_PREPARED",
                "output_dir": str(prepared.output_dir),
                "current_source_contract": str(prepared.current_source_contract),
                "current_source_contract_sha256": prepared.current_source_contract_sha256,
                "expected_block_contract": str(prepared.expected_block_contract),
                "expected_block_contract_sha256": prepared.expected_block_contract_sha256,
                "source_drift_review": str(prepared.source_drift_review),
                "output_index": str(prepared.output_index_md),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
