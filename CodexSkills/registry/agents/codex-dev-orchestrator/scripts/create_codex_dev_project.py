#!/usr/bin/env python3
"""Scaffold a Codex Dev output folder with the standard structure."""
from __future__ import annotations
import argparse, datetime, json
from pathlib import Path

DIRS = [
    "outputs/requirements", "outputs/agent_research", "outputs/reports",
    "outputs/task_pack", "outputs/implementation", "outputs/tests",
    "outputs/package", "outputs/audit",
]
TASK_FILES = [
    "00_PROJECT_BRIEF.md", "01_REQUIREMENTS.md", "02_ARCHITECTURE.md",
    "03_DATA_SCHEMA.md", "04_API_AND_INTERFACES.md", "05_UI_PAGES.md",
    "06_IMPLEMENTATION_PHASES.md", "07_ACCEPTANCE_CRITERIA.md",
    "08_TESTING_CHECKLIST.md", "09_DEPLOYMENT_GUIDE.md",
    "10_README_REQUIREMENTS.md", "11_RISK_AND_BOUNDARY_RULES.md",
    "12_EVIDENCE_AND_AUDIT_RULES.md", "13_CODEX_PROMPT.md", "CHANGELOG.md",
]

def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("project", help="Project name, e.g. consumption-analysis-system")
    p.add_argument("--root", default=".", help="Root folder to scaffold into")
    args = p.parse_args()
    root = Path(args.root).resolve() / args.project
    root.mkdir(parents=True, exist_ok=True)
    for d in DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    for f in TASK_FILES:
        path = root / "outputs/task_pack" / f
        if not path.exists():
            path.write_text(f"# {f}\n\nProject: {args.project}\n\n## Chinese Review Summary\n\n## English Execution Instructions\n\n## Assumptions\n\n## Acceptance Criteria\n", encoding="utf-8")
    manifest = {
        "project": args.project,
        "created_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "dirs": DIRS,
        "task_pack_files": TASK_FILES,
    }
    (root / "outputs/audit/scaffold_manifest.json").write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Created Codex Dev scaffold at: {root}")

if __name__ == "__main__":
    main()
