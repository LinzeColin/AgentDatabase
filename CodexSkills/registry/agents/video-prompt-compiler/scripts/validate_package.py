#!/usr/bin/env python3
"""Validate package inventory, JSON documents and Python syntax."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
REQUIRED = [
    "SKILL.md", "README.md", "README_FIRST.md", "VERSION", "LICENSE", "NOTICE.md", "manifest.json",
    ".ramify/KERNEL.md", ".ramify/DECISIONS.md", ".ramify/HANDOFF.md",
    "taskpack/CODEX_EXECUTION.md", "taskpack/ACCEPTANCE.md", "taskpack/TEST_RESULTS.md",
    "taskpack/TASKPACK_MANIFEST.md", "taskpack/VERIFIER_HANDOFF.md",
    "references/compiler-ir.md", "references/scoring-contract.md", "references/optimization-loop.md",
    "references/industrial-physics-ledger.md", "references/model-adapter-contract.md",
    "references/models/minimax-h3.md", "references/models/hailuo-2.3.md",
    "references/models/seedance-2.0.md", "references/models/kling-video-3.0.md",
    "references/models/veo-3.1.md", "references/models/runway-gen-4.5.md",
    "references/models/wan2.2.md", "references/models/ltx-2.md",
    "research/comparison_matrix.csv", "research/comparison_matrix.json", "research/comparison_matrix.md",
    "research/scoring_method.json", "research/evidence_ledger.md", "research/model_status_2026-08-17.md",
    "schemas/request.schema.json", "schemas/video_prompt_ir.schema.json", "schemas/score.schema.json",
    "scripts/install.py", "scripts/model_registry.py", "scripts/route_request.py", "scripts/compile_request.py",
    "scripts/score_prompt.py", "scripts/validate_output.py", "scripts/inspect_video.py",
    "tests/test_model_registry.py", "tests/test_compile_request.py", "tests/test_score_prompt.py",
    "tests/test_install.py", "tests/test_research_matrix.py"
]


def main() -> int:
    problems: list[str] = []
    for rel in REQUIRED:
        if not (ROOT / rel).exists():
            problems.append(f"missing: {rel}")
    json_paths = sorted(path for path in ROOT.rglob("*.json") if "__pycache__" not in path.parts)
    for path in json_paths:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"invalid JSON {path.relative_to(ROOT)}: {exc}")
    for path in sorted(ROOT.rglob("*.jsonl")):
        line_number = 0
        try:
            for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
                if line.strip():
                    json.loads(line)
        except (OSError, json.JSONDecodeError) as exc:
            problems.append(f"invalid JSONL {path.relative_to(ROOT)} line {line_number}: {exc}")
    for path in (ROOT / "scripts").glob("*.py"):
        try:
            source = path.read_text(encoding="utf-8")
            compile(source, str(path), "exec")
        except (OSError, SyntaxError, UnicodeError) as exc:
            problems.append(f"Python compile failure {path.name}: {exc}")
    if problems:
        print("FAIL")
        for item in problems:
            print(f"- {item}")
        return 1
    print("PASS: package inventory, JSON documents and Python syntax")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
