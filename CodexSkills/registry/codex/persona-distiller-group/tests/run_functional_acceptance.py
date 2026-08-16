#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Run functional acceptance for the expert-team candidate.")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    test_dir = Path(__file__).resolve().parent
    command = [sys.executable, "-m", "unittest", "discover", "-s", str(test_dir), "-p", "test_*.py", "-v"]
    completed = subprocess.run(command, text=True, capture_output=True)
    result = {
        "schema_version": "persona-team.functional-acceptance.v1",
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "command": command,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "returncode": completed.returncode,
        "scope": [
            "four owner-frozen modes and seat ranges",
            "mandatory hypothesis/adversary/review/judge/synthesis controls",
            "route-to-dossier subject_slug continuity",
            "real nested runtime payload loading",
            "C-to-B calibration fallback",
            "95 target and 75 floor score contract",
        ],
        "limitations": [
            "Synthetic registry fixtures prove candidate mechanics, not production Persona quality.",
            "Native commercial competitor runs, production blind tasks and external verifier remain separate gates.",
        ],
    }
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "returncode": completed.returncode}, ensure_ascii=False))
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
