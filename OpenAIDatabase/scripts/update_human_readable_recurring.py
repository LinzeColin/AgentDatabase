#!/usr/bin/env python3
"""Atomically refresh the generated Recurring sections in the consolidated 00 document.

The script intentionally uses only the Python standard library. It never writes either
legacy standalone human-readable file, so the canonical directory remains 00-07.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import tempfile
from pathlib import Path
from typing import Any

DEFAULT_CONFIG = Path("OpenAIDatabase/config/human_readable_merge.v1.json")
ANALYSIS_MARKER = "recurring-analysis"
STATUS_MARKER = "recurring-status"


class ConsolidationError(ValueError):
    """Raised when the consolidated document contract is malformed."""


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError as exc:
        raise ConsolidationError(f"required file does not exist: {path}") from exc
    except UnicodeDecodeError as exc:
        raise ConsolidationError(f"file is not valid UTF-8: {path}") from exc


def load_config(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(read_text(path))
    except json.JSONDecodeError as exc:
        raise ConsolidationError(f"invalid JSON config {path}: {exc}") from exc
    if data.get("schema_version") != 1:
        raise ConsolidationError(f"unsupported schema_version in {path}")
    return data


def canonical_index_path(repo_root: Path, config: dict[str, Any]) -> Path:
    docs = config.get("canonical_documents", [])
    index_docs = [item for item in docs if item.get("number") == "00"]
    if len(index_docs) != 1:
        raise ConsolidationError("config must define exactly one canonical 00 document")
    return repo_root / config["target_directory"] / index_docs[0]["filename"]


def legacy_reference_map(config: dict[str, Any]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for document in config.get("canonical_documents", []):
        filename = document["filename"]
        for source in document.get("sources", []):
            original = source["original_filename"]
            replacement = f"{filename}#{source['id']}"
            if original in mapping:
                raise ConsolidationError(f"duplicate original filename in config: {original}")
            mapping[original] = replacement
    return mapping


def rewrite_legacy_references(text: str, config: dict[str, Any]) -> str:
    """Rewrite only old Markdown filenames; all other generated prose stays byte-stable."""
    for original, replacement in sorted(
        legacy_reference_map(config).items(), key=lambda item: len(item[0]), reverse=True
    ):
        text = text.replace(original, replacement)
    return text


def replace_generated_block(document: str, marker: str, replacement: str) -> str:
    start = f"<!-- BEGIN GENERATED: {marker} -->"
    end = f"<!-- END GENERATED: {marker} -->"
    if document.count(start) != 1 or document.count(end) != 1:
        raise ConsolidationError(
            f"expected exactly one generated block for {marker}; "
            f"found start={document.count(start)}, end={document.count(end)}"
        )
    start_index = document.index(start)
    end_index = document.index(end, start_index + len(start))
    if end_index <= start_index:
        raise ConsolidationError(f"generated block markers are out of order: {marker}")
    if start in replacement or end in replacement:
        raise ConsolidationError(f"generated input attempts to inject block marker: {marker}")

    normalized = replacement.replace("\r\n", "\n").replace("\r", "\n").strip("\n")
    if not normalized.strip():
        raise ConsolidationError(f"generated input is empty: {marker}")
    return (
        document[: start_index + len(start)]
        + "\n"
        + normalized
        + "\n"
        + document[end_index:]
    )


def build_consolidated_document(
    base_text: str,
    summary_text: str,
    status_text: str,
    config: dict[str, Any],
) -> str:
    summary = rewrite_legacy_references(summary_text, config)
    status = rewrite_legacy_references(status_text, config)
    output = replace_generated_block(base_text, ANALYSIS_MARKER, summary)
    output = replace_generated_block(output, STATUS_MARKER, status)
    return output.rstrip() + "\n"


def atomic_write(path: Path, content: str) -> bool:
    """Write UTF-8/LF content atomically. Return True only when bytes changed."""
    encoded = content.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temp_path, 0o644)
        os.replace(temp_path, path)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise
    return True


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=Path("."))
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--base", type=Path, help="base consolidated 00 document")
    parser.add_argument("--summary", type=Path, required=True, help="generated analysis Markdown")
    parser.add_argument("--status", type=Path, required=True, help="generated status Markdown")
    parser.add_argument("--output", type=Path, help="output path; defaults to --base")
    parser.add_argument(
        "--check",
        action="store_true",
        help="do not write; exit 1 when the assembled bytes differ from the output",
    )
    return parser.parse_args()


def resolve_under_root(repo_root: Path, path: Path) -> Path:
    return path if path.is_absolute() else repo_root / path


def main() -> int:
    args = parse_args()
    repo_root = args.repo_root.resolve()
    config_path = resolve_under_root(repo_root, args.config)
    config = load_config(config_path)
    base_path = resolve_under_root(repo_root, args.base) if args.base else canonical_index_path(repo_root, config)
    output_path = resolve_under_root(repo_root, args.output) if args.output else base_path
    summary_path = resolve_under_root(repo_root, args.summary)
    status_path = resolve_under_root(repo_root, args.status)

    assembled = build_consolidated_document(
        read_text(base_path),
        read_text(summary_path),
        read_text(status_path),
        config,
    )
    digest = hashlib.sha256(assembled.encode("utf-8")).hexdigest()
    if args.check:
        current = output_path.read_bytes() if output_path.exists() else b""
        if current != assembled.encode("utf-8"):
            print(f"STALE: {output_path} expected_sha256={digest}")
            return 1
        print(f"PASS: {output_path} sha256={digest}")
        return 0

    changed = atomic_write(output_path, assembled)
    state = "UPDATED" if changed else "UNCHANGED"
    print(f"{state}: {output_path} sha256={digest}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ConsolidationError as exc:
        print(f"ERROR: {exc}")
        raise SystemExit(2) from exc
