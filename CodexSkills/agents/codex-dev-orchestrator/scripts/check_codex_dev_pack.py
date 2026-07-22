#!/usr/bin/env python3
"""Validate that a Codex Dev delivery contains required files."""
from __future__ import annotations
import argparse
from pathlib import Path

REQUIRED = [
    "outputs/task_pack/00_PROJECT_BRIEF.md", "outputs/task_pack/01_REQUIREMENTS.md",
    "outputs/task_pack/02_ARCHITECTURE.md", "outputs/task_pack/03_DATA_SCHEMA.md",
    "outputs/task_pack/04_API_AND_INTERFACES.md", "outputs/task_pack/05_UI_PAGES.md",
    "outputs/task_pack/06_IMPLEMENTATION_PHASES.md", "outputs/task_pack/07_ACCEPTANCE_CRITERIA.md",
    "outputs/task_pack/08_TESTING_CHECKLIST.md", "outputs/task_pack/09_DEPLOYMENT_GUIDE.md",
    "outputs/task_pack/10_README_REQUIREMENTS.md", "outputs/task_pack/11_RISK_AND_BOUNDARY_RULES.md",
    "outputs/task_pack/12_EVIDENCE_AND_AUDIT_RULES.md", "outputs/task_pack/13_CODEX_PROMPT.md",
    "outputs/task_pack/CHANGELOG.md",
]

def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("root", help="Codex Dev project root")
    args = p.parse_args()
    root = Path(args.root).resolve()
    missing = [rel for rel in REQUIRED if not (root / rel).exists()]
    if missing:
        print("Missing required files:")
        for rel in missing:
            print(f"- {rel}")
        return 1
    print("Codex Dev pack check passed.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
