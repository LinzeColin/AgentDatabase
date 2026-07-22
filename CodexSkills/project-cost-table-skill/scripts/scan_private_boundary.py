#!/usr/bin/env python3
"""Canonical command wrapper for the artifact boundary scanner."""

import subprocess
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SCANNER = MODULE_ROOT / "tools" / "scan_artifact_boundary.py"


def main() -> int:
    completed = subprocess.run([sys.executable, str(SCANNER), *sys.argv[1:]], check=False)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
