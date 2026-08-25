#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
SKILL_ROOT = Path(__file__).resolve().parents[1]
ROOT = SKILL_ROOT


def run_command(command):
    print("$", " ".join(str(item) for item in command))
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, env=env)
    if completed.stdout:
        print(completed.stdout, end="")
    if completed.stderr:
        print(completed.stderr, file=sys.stderr, end="")
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def compile_sources() -> int:
    count = 0
    for path in sorted(SKILL_ROOT.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")
        count += 1
    print(f"✓ Python 语法检查：{count} 个文件")
    return count


def main() -> int:
    compile_sources()
    run_command(
        [
            sys.executable,
            str(SKILL_ROOT / "scripts" / "market_lab.py"),
            "doctor",
            "--skill-root",
            str(SKILL_ROOT),
        ]
    )
    suite = unittest.defaultTestLoader.discover(str(SKILL_ROOT / "tests"), pattern="test_*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
