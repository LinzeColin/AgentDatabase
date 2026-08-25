#!/usr/bin/env python3
"""Scan evidence for likely secrets/PII and optionally create a separate redacted copy."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

SCHEMA_VERSION = "1.0"
MAX_TEXT_BYTES = 10_000_000
MAX_TOTAL_BYTES_DEFAULT = 2_000_000_000
MAX_FILES_DEFAULT = 100_000

PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    ("private_key", "critical", "secret", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("aws_access_key", "critical", "secret", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("github_token", "critical", "secret", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{20,255}|github_pat_[A-Za-z0-9_]{20,255})\b")),
    ("slack_token", "critical", "secret", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,200}\b")),
    ("bearer_token", "high", "secret", re.compile(r"(?i)\bAuthorization\s*:\s*Bearer\s+[A-Za-z0-9._~+/=-]{12,}")),
    ("generic_secret_assignment", "high", "secret", re.compile(r"(?i)\b(?:password|passwd|api[_-]?key|secret|access[_-]?token)\s*[:=]\s*['\"]?[A-Za-z0-9._~+/=-]{8,}")),
    ("connection_string_password", "high", "secret", re.compile(r"(?i)\b(?:postgres(?:ql)?|mysql|mongodb(?:\+srv)?)://[^\s:/]+:[^\s@]{4,}@")),
    ("email_address", "medium", "pii", re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)),
    ("ipv4_address", "low", "identifier", re.compile(r"(?<!\d)(?:(?:25[0-5]|2[0-4]\d|1?\d?\d)\.){3}(?:25[0-5]|2[0-4]\d|1?\d?\d)(?!\d)")),
)

TEXT_SUFFIXES = {
    ".txt", ".log", ".md", ".json", ".jsonl", ".yaml", ".yml", ".xml", ".csv", ".tsv", ".html", ".htm",
    ".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".go", ".rs", ".rb", ".php", ".sh", ".ps1", ".toml", ".ini", ".cfg",
}
IGNORED_PARTS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def is_probably_text(path: Path, prefix: bytes) -> bool:
    if path.suffix.casefold() in TEXT_SUFFIXES:
        return True
    if b"\x00" in prefix:
        return False
    if not prefix:
        return True
    printable = sum(byte in b"\n\r\t" or 32 <= byte < 127 or byte >= 128 for byte in prefix)
    return printable / len(prefix) > 0.90


def iter_files(root: Path, max_files: int, max_total_bytes: int) -> tuple[list[Path], list[dict[str, Any]], int]:
    files: list[Path] = []
    issues: list[dict[str, Any]] = []
    total = 0
    for path in sorted(root.rglob("*"), key=lambda p: p.relative_to(root).as_posix().casefold()):
        rel = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in rel.parts):
            continue
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            issues.append({"path": rel.as_posix(), "kind": "stat_error", "error": str(error)})
            continue
        if stat.S_ISLNK(mode):
            issues.append({"path": rel.as_posix(), "kind": "symlink_forbidden"})
            continue
        if stat.S_ISDIR(mode):
            continue
        if not stat.S_ISREG(mode):
            issues.append({"path": rel.as_posix(), "kind": "non_regular_file"})
            continue
        if len(files) >= max_files:
            issues.append({"path": rel.as_posix(), "kind": "file_limit_exceeded", "limit": max_files})
            break
        size = path.stat().st_size
        total += size
        if total > max_total_bytes:
            issues.append({"path": rel.as_posix(), "kind": "total_size_limit_exceeded", "limit": max_total_bytes})
            break
        files.append(path)
    return files, issues, total


def masked_excerpt(text: str, start: int, end: int) -> str:
    left = max(0, start - 30)
    right = min(len(text), end + 30)
    value = text[left:start] + "[REDACTED]" + text[end:right]
    return value.replace("\n", "\\n")[:240]


def scan_tree(root: Path, max_files: int, max_total_bytes: int) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"evidence root is not a directory: {root}")
    files, issues, total = iter_files(root, max_files, max_total_bytes)
    findings: list[dict[str, Any]] = []
    binary_files: list[dict[str, Any]] = []
    skipped_large_text: list[dict[str, Any]] = []
    for path in files:
        rel = path.relative_to(root).as_posix()
        size = path.stat().st_size
        try:
            with path.open("rb") as handle:
                prefix = handle.read(min(size, 8192))
        except OSError as error:
            issues.append({"path": rel, "kind": "read_error", "error": str(error)})
            continue
        if not is_probably_text(path, prefix):
            binary_files.append({"path": rel, "size": size, "sha256": sha256_file(path)})
            continue
        if size > MAX_TEXT_BYTES:
            skipped_large_text.append({"path": rel, "size": size, "sha256": sha256_file(path)})
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as error:
            issues.append({"path": rel, "kind": "read_error", "error": str(error)})
            continue
        line_offsets = [0]
        for match in re.finditer("\n", text):
            line_offsets.append(match.end())
        for pattern_id, severity, category, regex in PATTERNS:
            count = 0
            for match in regex.finditer(text):
                count += 1
                if count > 100:
                    findings.append({
                        "id": f"{pattern_id}:{rel}:overflow",
                        "path": rel,
                        "pattern": pattern_id,
                        "severity": severity,
                        "category": category,
                        "count_truncated": True,
                    })
                    break
                line = 1
                # Binary search without importing bisect manually for clarity.
                lo, hi = 0, len(line_offsets)
                while lo < hi:
                    mid = (lo + hi) // 2
                    if line_offsets[mid] <= match.start():
                        lo = mid + 1
                    else:
                        hi = mid
                line = lo
                findings.append({
                    "id": f"{pattern_id}:{rel}:{line}:{match.start()}",
                    "path": rel,
                    "line": line,
                    "pattern": pattern_id,
                    "severity": severity,
                    "category": category,
                    "excerpt": masked_excerpt(text, match.start(), match.end()),
                })
    blocking = [item for item in findings if item.get("severity") in {"critical", "high"} and item.get("category") == "secret"]
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "root": str(root),
        "scanned_file_count": len(files),
        "scanned_total_bytes": total,
        "findings": findings,
        "blocking_findings": blocking,
        "binary_files": binary_files,
        "skipped_large_text": skipped_large_text,
        "filesystem_issues": issues,
        "status": "BLOCKED" if blocking or issues else ("REVIEW" if findings or skipped_large_text else "PASS"),
        "limitations": [
            "Pattern matching is heuristic and can produce false positives and false negatives.",
            "Binary files are hashed but not content-inspected.",
            "Large text files are reported but not scanned automatically.",
        ],
    }


def redact_text(text: str) -> tuple[str, list[str]]:
    applied: list[str] = []
    for pattern_id, _severity, _category, regex in PATTERNS:
        text, count = regex.subn(f"[REDACTED:{pattern_id}]", text)
        if count:
            applied.append(f"{pattern_id}:{count}")
    return text, applied


def redacted_copy(
    root: Path,
    destination: Path,
    max_files: int,
    max_total_bytes: int,
    allow_uninspected_copy: bool = False,
) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise ValueError(f"destination already exists: {destination}")
    try:
        destination.relative_to(root)
    except ValueError:
        pass
    else:
        raise ValueError("destination must not be inside evidence root")
    files, issues, total = iter_files(root, max_files, max_total_bytes)
    if issues:
        raise ValueError(f"source tree is not safely copyable: {issues[0]}")
    destination.mkdir(parents=True)
    mappings: list[dict[str, Any]] = []
    try:
        for path in files:
            rel = path.relative_to(root)
            out = destination / rel
            out.parent.mkdir(parents=True, exist_ok=True)
            size = path.stat().st_size
            with path.open("rb") as handle:
                prefix = handle.read(min(size, 8192))
            applied: list[str] = []
            inspection_status = "TEXT_SCANNED_AND_REDACTED"
            if is_probably_text(path, prefix) and size <= MAX_TEXT_BYTES:
                text = path.read_text(encoding="utf-8", errors="replace")
                sanitized, applied = redact_text(text)
                out.write_text(sanitized, encoding="utf-8")
            else:
                if not allow_uninspected_copy:
                    kind = "large text" if is_probably_text(path, prefix) else "binary"
                    raise ValueError(
                        f"refusing to copy uninspected {kind} file {rel.as_posix()}; "
                        "review it separately or pass --allow-uninspected-copy explicitly"
                    )
                inspection_status = "UNINSPECTED_COPY_EXPLICITLY_AUTHORIZED"
                shutil.copy2(path, out)
            mappings.append({
                "path": rel.as_posix(),
                "source_sha256": sha256_file(path),
                "sanitized_sha256": sha256_file(out),
                "redactions": applied,
                "inspection_status": inspection_status,
            })
    except Exception:
        shutil.rmtree(destination, ignore_errors=True)
        raise
    report = {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "source_root": str(root),
        "destination_root": str(destination),
        "file_count": len(files),
        "source_total_bytes": total,
        "mappings": mappings,
        "allow_uninspected_copy": allow_uninspected_copy,
        "warning": (
            "Uninspected files were explicitly copied and still require separate privacy review."
            if allow_uninspected_copy
            else "Only bounded UTF-8-like text was copied after heuristic redaction; run policy/human review before sharing."
        ),
    }
    (destination / "REDACTION_MAP.json").write_text(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    scan = sub.add_parser("scan")
    scan.add_argument("root", type=Path)
    scan.add_argument("--output", type=Path)
    scan.add_argument("--max-files", type=int, default=MAX_FILES_DEFAULT)
    scan.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BYTES_DEFAULT)
    scan.add_argument("--json", action="store_true")
    copy = sub.add_parser("redact-copy")
    copy.add_argument("root", type=Path)
    copy.add_argument("destination", type=Path)
    copy.add_argument("--max-files", type=int, default=MAX_FILES_DEFAULT)
    copy.add_argument("--max-total-bytes", type=int, default=MAX_TOTAL_BYTES_DEFAULT)
    copy.add_argument(
        "--allow-uninspected-copy", action="store_true",
        help="explicitly copy binary/oversized files without content inspection (unsafe by default)",
    )
    copy.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        if args.command == "scan":
            result = scan_tree(args.root, args.max_files, args.max_total_bytes)
            text = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
            if args.output:
                args.output.parent.mkdir(parents=True, exist_ok=True)
                args.output.write_text(text, encoding="utf-8")
            if args.json or not args.output:
                print(text, end="")
            else:
                print(f"EVIDENCE_PRIVACY_REPORT: {args.output.resolve()} status={result['status']} findings={len(result['findings'])}")
            return 1 if result["status"] == "BLOCKED" else 0
        result = redacted_copy(
            args.root, args.destination, args.max_files, args.max_total_bytes, args.allow_uninspected_copy
        )
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"REDACTED_COPY: {args.destination.resolve()} files={result['file_count']}")
        return 0
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
