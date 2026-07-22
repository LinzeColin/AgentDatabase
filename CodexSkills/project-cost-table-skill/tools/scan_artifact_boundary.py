#!/usr/bin/env python3
"""Scan the project-cost Skill public boundary."""

import argparse
import json
import subprocess
import sys
from pathlib import Path


MODULE_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = MODULE_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from project_cost_table.artifact_boundary import (  # noqa: E402
    ArtifactBoundaryPolicy,
    PolicyError,
    scan_staged,
    scan_working_tree,
)


def _repo_root(start: Path) -> Path:
    output = subprocess.check_output(
        ["git", "rev-parse", "--show-toplevel"], cwd=str(start), stderr=subprocess.STDOUT
    )
    return Path(output.decode("utf-8").strip()).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--working-tree", action="store_true", help="scan current module files")
    mode.add_argument("--staged", action="store_true", help="scan staged index content (default)")
    parser.add_argument("--module-root", type=Path, default=MODULE_ROOT)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--module-relative-root", default="KMFA/project-cost-table-skill")
    args = parser.parse_args()

    module_root = args.module_root.resolve()
    try:
        policy = ArtifactBoundaryPolicy.from_yaml(module_root / "config" / "artifact_classification.yml")
        if args.working_tree:
            findings = scan_working_tree(module_root, policy)
            scan_mode = "working_tree"
        else:
            repo_root = (args.repo_root or _repo_root(module_root)).resolve()
            findings = scan_staged(repo_root, args.module_relative_root, policy)
            scan_mode = "staged_index"
    except (OSError, subprocess.CalledProcessError, PolicyError) as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, indent=2))
        return 3

    payload = {
        "status": "PASS" if not findings else "BLOCKED",
        "scan_mode": scan_mode,
        "module_root": str(module_root),
        "finding_count": len(findings),
        "findings": [finding.as_dict() for finding in findings],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":
    raise SystemExit(main())
