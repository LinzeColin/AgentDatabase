#!/usr/bin/env python3
"""Initialize a verifier v2.1 acceptance evidence directory."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


TEMPLATE_MAP = {
    "ACCEPTANCE_REQUEST.yaml": "ACCEPTANCE_REQUEST.yaml",
    "TEST_MATRIX.md": "TEST_MATRIX.md",
    "HUMAN_JOURNEY.md": "HUMAN_JOURNEY.md",
    "AI_EVAL_MATRIX.md": "AI_EVAL_MATRIX.md",
    "RELEASE_ASSURANCE.md": "RELEASE_ASSURANCE.md",
    "DEFECT_REPORT.md": "DEFECT_REPORT.md",
    "MODIFICATION_REPORT.md": "MODIFICATION_REPORT.md",
    "VERDICT_TEMPLATE.md": "VERDICT.md",
    "RUN_MANIFEST.yaml": "RUN_MANIFEST.yaml",
    "TRACEABILITY_MATRIX.json": "TRACEABILITY_MATRIX.json",
    "GALLERY_PAIRS.csv": "pairs.csv",
}
EVIDENCE_DIRECTORIES = (
    "logs",
    "traces",
    "screenshots",
    "metrics",
    "artifacts",
    "raw-results",
    "taskpack",
)
ALLOWED_DECISION_SCOPES = (
    "developer_check",
    "release_candidate",
    "staged_release",
    "post_deploy",
)


def slugify(value: str) -> str:
    original = value.strip()
    if not original:
        raise ValueError("project name must not be empty")
    normalized = unicodedata.normalize("NFKC", original)
    ascii_part = normalized.encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-zA-Z0-9._-]+", "-", ascii_part).strip("-.")
    if not slug:
        slug = "project-" + hashlib.sha256(normalized.encode("utf-8")).hexdigest()[:10]
    return slug[:80]


def _atomic_json(path: Path, value: object) -> None:
    temporary = path.with_name(f".{path.name}.tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    temporary.replace(path)


def initialize(
    output_root: Path,
    project: str,
    run_id: Optional[str] = None,
    decision_scope: str = "release_candidate",
    target_path: str = "",
) -> Path:
    if decision_scope not in ALLOWED_DECISION_SCOPES:
        raise ValueError(f"invalid decision scope: {decision_scope}")
    safe_project = slugify(project)
    actual_run_id = run_id or datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_run_id = slugify(actual_run_id)
    root = output_root.expanduser().resolve()
    destination = root / f"{safe_project}_acceptance_{safe_run_id}"
    if destination.exists():
        raise FileExistsError(f"refusing to overwrite existing run directory: {destination}")

    template_root = Path(__file__).resolve().parent.parent / "templates"
    missing = [name for name in TEMPLATE_MAP if not (template_root / name).is_file()]
    if missing:
        raise FileNotFoundError(f"bundled templates missing: {', '.join(missing)}")

    destination.mkdir(parents=True)
    try:
        for source_name, target_name in TEMPLATE_MAP.items():
            shutil.copyfile(template_root / source_name, destination / target_name)
        for directory in EVIDENCE_DIRECTORIES:
            (destination / directory).mkdir()

        manifest_path = destination / "RUN_MANIFEST.yaml"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        now = datetime.now(timezone.utc).isoformat()
        manifest["run"]["id"] = actual_run_id
        manifest["run"]["started_at"] = now
        manifest["run"]["timezone"] = "UTC"
        manifest["scope"]["target_project_name"] = project
        manifest["scope"]["target_project_path"] = target_path or project
        manifest["release"]["decision_scope"] = decision_scope
        _atomic_json(manifest_path, manifest)

        traceability_path = destination / "TRACEABILITY_MATRIX.json"
        traceability = json.loads(traceability_path.read_text(encoding="utf-8"))
        traceability["target_project_name"] = project
        _atomic_json(traceability_path, traceability)

        request_path = destination / "ACCEPTANCE_REQUEST.yaml"
        request = request_path.read_text(encoding="utf-8")
        request = request.replace('    name: ""', f'    name: {json.dumps(project, ensure_ascii=False)}', 1)
        request = request.replace('    path: ""', f'    path: {json.dumps(target_path, ensure_ascii=False)}', 1)
        request = request.replace(
            '  decision_scope: "release_candidate"',
            f'  decision_scope: "{decision_scope}"',
            1,
        )
        request_path.write_text(request, encoding="utf-8")
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    return destination


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_root", type=Path)
    parser.add_argument("project")
    parser.add_argument("--run-id")
    parser.add_argument("--target-path", default="")
    parser.add_argument(
        "--decision-scope",
        choices=ALLOWED_DECISION_SCOPES,
        default="release_candidate",
    )
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        destination = initialize(
            args.output_root,
            args.project,
            args.run_id,
            args.decision_scope,
            args.target_path,
        )
    except (OSError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    print(f"created: {destination}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
