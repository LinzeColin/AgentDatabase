#!/usr/bin/env python3
"""Run the production R11 current-source reconstruction gate.

Normal current-data insufficiency is a truthful business block and exits 3.
This command never reads an expected-block contract.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MODULE_ROOT / "src"))

from project_cost_table.current_reconstruction import (  # noqa: E402
    CurrentReconstructionError,
    CurrentReconstructionRequest,
    run_current_source_reconstruction,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Production current-source calculate preflight. BLOCKED_SOURCE exits 3 and writes sealed diagnostics."
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--input-root", required=True)
    parser.add_argument("--current-source-contract", required=True)
    parser.add_argument("--current-source-contract-sha256", required=True)
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--output-dir", required=True)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    output_dir = Path(args.output_dir).expanduser().absolute()
    request = CurrentReconstructionRequest(
        run_id=args.run_id,
        as_of=args.as_of,
        input_root=Path(args.input_root).expanduser(),
        contract_path=Path(args.current_source_contract).expanduser(),
        contract_sha256=args.current_source_contract_sha256,
        output_dir=output_dir,
        module_root=MODULE_ROOT,
    )
    try:
        result = run_current_source_reconstruction(request)
    except CurrentReconstructionError as exc:
        print(
            json.dumps(
                {
                    "status": "FAILED_BEFORE_ATOMIC_OUTPUT",
                    "error_code": exc.code,
                    "output_dir": str(output_dir),
                    "output_index": str(output_dir / "OUTPUT_INDEX.md"),
                    "next_step": "修复合同/路径/快照门禁并使用新的 run ID 和输出目录重试。",
                },
                ensure_ascii=False,
                sort_keys=True,
            )
        )
        return 4
    print(result.locator_text())
    print(
        json.dumps(
            {
                "status": result.generated.status_planes.generation_status.value,
                "calculation_status": result.generated.status_planes.calculation_status.value,
                "blocker_codes": list(result.blocker_codes),
                "output_dir": str(result.generated.output_dir),
                "primary_output": str(result.generated.primary_output),
                "output_index": str(result.generated.output_index_md),
            },
            ensure_ascii=False,
            sort_keys=True,
        )
    )
    return 3


if __name__ == "__main__":
    raise SystemExit(main())
