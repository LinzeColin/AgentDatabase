#!/usr/bin/env python3
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "scripts"))
from teleiosis_core.cli import main

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        args = ["check"]
    elif args[0] == "install":
        args = ["install", *args[1:]]
    raise SystemExit(main(args))
