#!/usr/bin/env python3
"""Fail-closed validator for the one-file dynamic profile contract."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


MAX_OUTPUT_BYTES = 80 * 1024
REQUIRED = (
    "schema_version:",
    "artifact_status:",
    "skill_version:",
    "input_mode:",
    "canonical_stable_profile_write:",
    "source_snapshot_sha256:",
    "semantic_snapshot_sha256:",
    "source_files:",
    "entries:",
    "# Dynamic Personal Profile",
    "## 先看结论",
    "## 变化条目",
    "## 可立即试用的 Agent 行为",
    "## Recurring Asset 候选",
    "## 边界与不确定性",
)
FORBIDDEN = (
    "data/raw",
    "data/public_raw",
    "data/private",
    "private_imports",
    "cookies",
    "plaintext secret",
    "api_key",
    "BEGIN PRIVATE KEY",
    "CORE_PROFILE.md` will be modified",
)


def validate(path: Path) -> list[str]:
    errors: list[str] = []
    if not path.is_file():
        return [f"missing profile: {path}"]
    content = path.read_text(encoding="utf-8", errors="replace")
    if len(content.encode("utf-8")) > MAX_OUTPUT_BYTES:
        errors.append("profile exceeds 80 KiB")
    if not content.startswith("---\n") or "\n---\n\n# Dynamic Personal Profile" not in content:
        errors.append("missing dual-plane front matter boundary")
    for marker in REQUIRED:
        if marker not in content:
            errors.append(f"missing required marker: {marker}")
    for marker in FORBIDDEN:
        if marker.lower() in content.lower():
            errors.append(f"forbidden content: {marker}")
    if "status: \"stable\"" in content or "status: stable" in content:
        errors.append("stable status is forbidden in generated view")
    ids = re.findall(r"^\s+- id:\s*[\"']?([^\"'\n]+)", content, re.MULTILINE)
    if len(ids) != len(set(ids)):
        errors.append("duplicate entry id")
    for evidence in re.findall(r"^\s+- (OpenAIDatabase/[^\n]+)$", content, re.MULTILINE):
        if "/data/derived/" not in evidence:
            errors.append(f"evidence outside derived data: {evidence}")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, required=True)
    args = parser.parse_args(argv)
    errors = validate(args.profile)
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        return 1
    print("PASS: dynamic profile contract")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
