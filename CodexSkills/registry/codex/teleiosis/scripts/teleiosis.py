#!/usr/bin/env python3
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from teleiosis_core.cli import main
if __name__ == "__main__":
    raise SystemExit(main())
