#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict

sys.dont_write_bytecode = True
SCRIPT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_ROOT))
from wbi_run import build_contract, init_run, record_stage, run_status, validate_run, simulate_run  # noqa: E402

_SECRET = re.compile(
    r"(?i)(github_pat_[A-Za-z0-9_]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{20,}|"
    r"bearer\s+[A-Za-z0-9._~+/-]{16,}|https?://[^\s/@:]+:[^\s/@]+@)"
)


class CleanParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:  # pragma: no cover - argparse callback
        raise ValueError(message)


def redact(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        return _SECRET.sub("[REDACTED]", value)
    return value


def emit(obj: Dict[str, Any]) -> None:
    # Exactly one JSON document; no traceback, usage block, progress noise or cache output.
    print(json.dumps(redact(obj), ensure_ascii=False, indent=2, sort_keys=True))


def build_parser() -> argparse.ArgumentParser:
    parser = CleanParser(
        description="Teleiosis v0.0.0.3 full non-routed Candidate evolution controller",
        add_help=True,
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("contract")
    item = sub.add_parser("init")
    item.add_argument("--subject", required=True)
    item.add_argument("--workspace", required=True)
    item.add_argument("--candidate-id")
    item.add_argument("--max-files", type=int, default=100_000)
    item.add_argument("--max-total-mb", type=int, default=10_240)
    item.add_argument("--max-file-mb", type=int, default=2_048)
    item.add_argument("--max-input-mb", type=int, default=8)
    item.add_argument("--max-evidence-mb", type=int, default=256)
    item = sub.add_parser("next")
    item.add_argument("--workspace", required=True)
    item.add_argument("--module", choices=["T", "S", "P", "t", "s", "p"], required=True)
    item.add_argument("--result", choices=["AUTO", "EXECUTED", "NOT_APPLICABLE_WITH_REASON", "NOT_RUN", "BLOCKED"], default="AUTO")
    item.add_argument("--capability-results")
    item.add_argument("--evidence")
    item.add_argument("--decision", choices=["KEEP", "NO_CHANGE", "REVERT"], default="KEEP")
    item.add_argument("--rollback-pointer")
    item.add_argument("--note", default="")
    item = sub.add_parser("status")
    item.add_argument("--workspace", required=True)
    item = sub.add_parser("validate")
    item.add_argument("--workspace", required=True)
    item.add_argument("--require-complete", action="store_true")
    item = sub.add_parser("simulate")
    item.add_argument("--subject", required=True)
    item.add_argument("--workspace", required=True)
    return parser


def main() -> int:
    try:
        args = build_parser().parse_args()
        if args.command == "contract":
            result = build_contract()
        elif args.command == "init":
            mib = 1024 * 1024
            result = init_run(
                Path(args.subject),
                Path(args.workspace),
                candidate_id=args.candidate_id or "",
                limits={
                    "candidate_max_files": args.max_files,
                    "candidate_max_total_bytes": args.max_total_mb * mib,
                    "candidate_max_single_file_bytes": args.max_file_mb * mib,
                    "input_max_bytes": args.max_input_mb * mib,
                    "evidence_max_bytes": args.max_evidence_mb * mib,
                },
            )
        elif args.command == "next":
            workspace = Path(args.workspace)
            capability = Path(args.capability_results) if args.capability_results else workspace / "NEXT_STAGE.json"
            result = record_stage(
                workspace,
                args.module,
                args.result,
                capability,
                evidence=Path(args.evidence) if args.evidence else None,
                decision=args.decision,
                rollback_pointer=args.rollback_pointer or "",
                note=args.note,
            )
        elif args.command == "status":
            result = run_status(Path(args.workspace))
        elif args.command == "validate":
            result = validate_run(Path(args.workspace), require_complete=args.require_complete)
        else:
            result = simulate_run(Path(args.subject), Path(args.workspace))
        emit(result)
        return 0 if result.get("status") not in {"FAIL", "BLOCKED"} else 2
    except SystemExit as exc:  # --help remains the only intentional non-JSON path.
        return int(exc.code or 0)
    except Exception as exc:
        emit({
            "status": "BLOCKED",
            "error": str(exc),
            "next_action": "按 error 修正输入；Candidate 和既有 Run 状态不会被静默丢弃",
        })
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
