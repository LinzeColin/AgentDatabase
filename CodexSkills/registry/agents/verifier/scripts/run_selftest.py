#!/usr/bin/env python3
"""Run cache-safe Verifier validation and tests repeatedly from any working directory."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional


def run(argv: list[str], cwd: Path, env: dict[str, str]) -> dict[str, object]:
    proc = subprocess.run(
        argv,
        cwd=cwd,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
        env=env,
        timeout=180,
    )
    return {
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repeat", type=int, default=2)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    if args.repeat < 1 or args.repeat > 20:
        print("--repeat must be between 1 and 20", file=sys.stderr)
        return 2
    root = Path(__file__).resolve().parent.parent
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    env["PYTHONHASHSEED"] = "0"
    results: list[dict[str, object]] = []

    # Installed mode deliberately ignores runtime caches; distribution mode is used by the packager before execution.
    results.append(run([sys.executable, "-B", "scripts/validate_pack.py", ".", "--mode", "installed", "--json"], root, env))
    results.append(run([sys.executable, "-B", "scripts/verify_distribution.py", "verify", ".", "--mode", "installed", "--json"], root, env))
    for _index in range(args.repeat):
        results.append(run([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"], root, env))
    results.append(run([sys.executable, "-B", "scripts/validate_pack.py", ".", "--mode", "installed", "--json"], root, env))
    results.append(run([sys.executable, "-B", "scripts/verify_distribution.py", "verify", ".", "--mode", "installed", "--json"], root, env))

    ok = all(item["returncode"] == 0 for item in results)
    summary = {
        "ok": ok,
        "root": str(root),
        "repeat": args.repeat,
        "steps": [
            {
                "argv": item["argv"],
                "returncode": item["returncode"],
                "stdout_tail": str(item["stdout"])[-4_000:],
                "stderr_tail": str(item["stderr"])[-4_000:],
            }
            for item in results
        ],
    }
    if args.json or not ok:
        print(json.dumps(summary, ensure_ascii=False, indent=2), file=sys.stdout if ok else sys.stderr)
    else:
        print(f"SELFTEST PASS: {len(results)} steps, unittest repeated {args.repeat} times")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
