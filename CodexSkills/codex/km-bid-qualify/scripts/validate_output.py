#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from jsonschema import Draft202012Validator
except ImportError as exc:
    raise SystemExit("jsonschema is required to validate Skill output") from exc

if len(sys.argv) != 2:
    raise SystemExit("usage: validate_output.py OUTPUT.json")

root = Path(__file__).resolve().parents[1]
schema = json.loads((root / "assets" / "output.schema.json").read_text(encoding="utf-8"))
instance = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
errors = sorted(Draft202012Validator(schema).iter_errors(instance), key=lambda err: list(err.path))
if errors:
    for error in errors:
        location = "/".join(str(part) for part in error.path) or "$"
        print(f"FAIL {location}: {error.message}")
    raise SystemExit(1)
print("PASS: output conforms to assets/output.schema.json")
