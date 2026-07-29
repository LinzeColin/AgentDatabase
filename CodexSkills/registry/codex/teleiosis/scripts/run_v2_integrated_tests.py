#!/usr/bin/env python3
from __future__ import annotations

import os
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TESTS = ROOT / "tests"
TARGET_PREFIX = "test_teleiosis_v2_"


def compile_v2_sources() -> int:
    paths = [ROOT / "scripts" / "wbi_market.py", ROOT / "scripts" / "teleiosis_cycle.py"]
    paths.extend(sorted((ROOT / "scripts" / "wbi_market").glob("*.py")))
    paths.extend(sorted((ROOT / "scripts" / "wbi_cycle").glob("*.py")))
    paths.extend(sorted(TESTS.glob(f"{TARGET_PREFIX}*.py")))
    count = 0
    for path in paths:
        compile(path.read_text(encoding="utf-8"), str(path), "exec")
        count += 1
    print(f"✓ v0.0.0.2 Python 语法检查：{count} 个文件")
    return count


def run_doctor() -> None:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "wbi_market.py"), "doctor", "--skill-root", str(ROOT)],
        cwd=ROOT,
        text=True,
        env=env,
        check=False,
    )
    if completed.returncode != 0:
        raise SystemExit(completed.returncode)


def main() -> int:
    sys.dont_write_bytecode = True
    compile_v2_sources()
    run_doctor()
    suite = unittest.defaultTestLoader.discover(str(TESTS), pattern=f"{TARGET_PREFIX}*.py")
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
