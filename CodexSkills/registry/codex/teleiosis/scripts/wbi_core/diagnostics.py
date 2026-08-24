from __future__ import annotations

import os
import platform
import re
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .io import SECRET_PATTERNS, TEXT_SUFFIXES, iter_files, read_frontmatter, sha256_tree, utc_now, write_json

MAX_FILES_DEFAULT = 5000
MAX_TEXT_BYTES_DEFAULT = 8 * 1024 * 1024
MAX_FILE_READ_BYTES = 256 * 1024

_EXECUTABLE_SUFFIXES = {".py", ".sh", ".js", ".ts", ".go", ".rs", ".rb", ".ps1", ".bat", ".cmd"}
_ARTIFACT_SUFFIXES = {".html", ".css", ".png", ".jpg", ".jpeg", ".svg", ".gif", ".pdf", ".pptx", ".docx", ".xlsx"}
_TEST_MARKERS = {"tests", "test", "spec", "specs", "evals", "benchmarks"}
_RUNTIME_NAMES = ("claude code", "codex", "cursor", "gemini cli", "opencode", "openclaw", "hermes")

# These are diagnostic signals, not automatic proof of maliciousness.
_RISK_PATTERNS: List[Tuple[str, re.Pattern[str], str]] = [
    ("destructive-delete", re.compile(r"\brm\s+-rf\b|\bshutil\.rmtree\s*\(", re.I), "high"),
    ("privilege-escalation", re.compile(r"\bsudo\b|\bchmod\s+777\b", re.I), "high"),
    ("remote-pipe-exec", re.compile(r"(?:curl|wget)[^\n|]{0,240}\|\s*(?:sh|bash|zsh)\b", re.I), "high"),
    ("dynamic-execution", re.compile(r"\beval\s*\(|\bexec\s*\(|shell\s*=\s*True", re.I), "medium"),
    ("process-spawn", re.compile(r"\bsubprocess\.|\bos\.system\s*\(", re.I), "medium"),
    ("network-access", re.compile(r"\brequests\.|\burllib\.|\bfetch\s*\(|\bcurl\b|\bwget\b", re.I), "medium"),
    ("deployment-or-service", re.compile(r"\bdeploy(?:ment)?\b|systemctl|launchctl|docker\s+(?:run|compose)|kubectl", re.I), "medium"),
    ("production-mutation", re.compile(r"\bproduction\b.{0,80}\b(?:write|delete|replace|migrate|restart)\b", re.I), "high"),
]


def _bounded_text(path: Path) -> Tuple[str, int, Optional[str]]:
    """Read a bounded UTF-8 prefix and report bytes consumed and any decode issue."""
    try:
        raw = path.read_bytes()[:MAX_FILE_READ_BYTES]
    except OSError as exc:
        return "", 0, str(exc)
    try:
        return raw.decode("utf-8"), len(raw), None
    except UnicodeDecodeError:
        return "", len(raw), "invalid UTF-8"


def _severity_rank(value: str) -> int:
    return {"low": 1, "medium": 2, "high": 3}.get(value, 0)


def _target_class(capabilities: Dict[str, Any], risk_level: str, file_count: int) -> str:
    if risk_level == "high":
        return "high-risk-or-side-effecting"
    if capabilities["has_scripts"] and capabilities["has_assets"]:
        return "tool-and-artifact"
    if capabilities["has_scripts"]:
        return "tool-execution"
    if capabilities["has_assets"] or capabilities["has_showcase"]:
        return "artifact-productization"
    if file_count > 800:
        return "large-mixed-repository"
    return "text-and-reasoning"


def diagnose_target(
    target: Path,
    *,
    valid_as_of: str = "",
    output: Optional[Path] = None,
    max_files: int = MAX_FILES_DEFAULT,
    max_text_bytes: int = MAX_TEXT_BYTES_DEFAULT,
) -> Dict[str, Any]:
    """Perform a bounded, no-exec, no-follow target diagnosis.

    The diagnosis is intentionally conservative. A risk signal means "inspect",
    not "the target is unsafe". Secret-like material and symlinks are blockers
    because copying or publishing them can create irreversible exposure.
    """
    target = target.resolve()
    if max_files < 1 or max_text_bytes < 1:
        raise ValueError("max_files and max_text_bytes must be positive")
    if not target.is_dir():
        raise ValueError("target must be an existing directory")

    extension_counts: Counter[str] = Counter()
    directory_counts: Counter[str] = Counter()
    risk_hits: List[Dict[str, Any]] = []
    blockers: List[str] = []
    warnings: List[str] = []
    invalid_text: List[str] = []
    symlinks: List[str] = []
    possible_secrets: List[str] = []
    runtime_mentions: Counter[str] = Counter()
    scanned_files = 0
    scanned_text_bytes = 0
    total_bytes = 0
    truncated = False

    files = sorted(iter_files(target), key=lambda item: item.relative_to(target).as_posix())
    total_file_candidates = len(files)
    for path in files:
        if scanned_files >= max_files:
            truncated = True
            break
        relative = path.relative_to(target).as_posix()
        scanned_files += 1
        try:
            size = path.lstat().st_size
        except OSError:
            size = 0
        total_bytes += size
        suffix = path.suffix.lower() or "[no-extension]"
        extension_counts[suffix] += 1
        if path.relative_to(target).parts:
            directory_counts[path.relative_to(target).parts[0]] += 1
        if path.is_symlink():
            symlinks.append(relative)
            continue
        if suffix not in TEXT_SUFFIXES or scanned_text_bytes >= max_text_bytes:
            continue
        text, consumed, error = _bounded_text(path)
        scanned_text_bytes += consumed
        if error:
            invalid_text.append(relative)
            continue
        lowered = text.lower()
        for runtime in _RUNTIME_NAMES:
            if runtime in lowered:
                runtime_mentions[runtime] += lowered.count(runtime)
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                possible_secrets.append(relative)
                break
        for signal, pattern, severity in _RISK_PATTERNS:
            match = pattern.search(text)
            if match:
                risk_hits.append({
                    "signal": signal,
                    "severity": severity,
                    "path": relative,
                    "line": text.count("\n", 0, match.start()) + 1,
                })

    skill_path = target / "SKILL.md"
    skill_frontmatter: Dict[str, Any] = {}
    skill_lines: Optional[int] = None
    if skill_path.is_file() and not skill_path.is_symlink():
        try:
            skill_frontmatter, _ = read_frontmatter(skill_path)
            skill_lines = len(skill_path.read_text(encoding="utf-8").splitlines())
        except Exception as exc:
            blockers.append("SKILL.md cannot be parsed: %s" % exc)
    else:
        blockers.append("SKILL.md is missing or linked")

    top_dirs = {path.name.lower() for path in target.iterdir() if path.is_dir() and not path.is_symlink()}
    names = {path.name.lower() for path in target.iterdir() if path.is_file() and not path.is_symlink()}
    all_regular_names = {path.name.lower() for path in files if not path.is_symlink()}
    relative_paths_lower = {path.relative_to(target).as_posix().lower() for path in files if not path.is_symlink()}
    has_scripts = "scripts" in top_dirs or any(suffix in _EXECUTABLE_SUFFIXES for suffix in extension_counts)
    has_assets = "assets" in top_dirs or any(suffix in _ARTIFACT_SUFFIXES for suffix in extension_counts)
    has_tests = bool(top_dirs & _TEST_MARKERS) or any(name.startswith("test_") for name in all_regular_names)
    has_ci = (target / ".github/workflows").is_dir()
    has_showcase = any(token in all_regular_names for token in {"showcase.html", "demo.html", "index.html"}) or "examples" in top_dirs
    capabilities: Dict[str, Any] = {
        "has_skill_md": skill_path.is_file() and not skill_path.is_symlink(),
        "has_readme": any(name.startswith("readme") for name in names),
        "has_version": "version" in names or "pyproject.toml" in names or "package.json" in names,
        "has_license": any(name.startswith("license") for name in names),
        "has_manifest": "manifest.sha256" in names,
        "has_scripts": has_scripts,
        "has_assets": has_assets,
        "has_tests": has_tests,
        "has_ci": has_ci,
        "has_showcase": has_showcase,
        "has_schemas": "schemas" in top_dirs,
        "has_references": "references" in top_dirs,
        "has_install_docs": any("install" in path for path in relative_paths_lower),
        "has_rollback_docs": any("rollback" in path for path in relative_paths_lower),
    }

    if symlinks:
        blockers.append("symlink paths require explicit review before packaging")
    if possible_secrets:
        blockers.append("possible credential material requires removal or owner-approved isolation")
    if invalid_text:
        warnings.append("some declared text files are not valid UTF-8")
    if truncated or scanned_text_bytes >= max_text_bytes:
        warnings.append("bounded scan reached a limit; evidence completeness is PARTIAL")
    if not capabilities["has_tests"]:
        warnings.append("no test/eval directory was detected")
    if not capabilities["has_readme"]:
        warnings.append("README was not detected")
    if not capabilities["has_license"]:
        warnings.append("licence file was not detected")
    if skill_lines is not None and skill_lines > 500:
        warnings.append("SKILL.md exceeds 500 lines; progressive disclosure may be weak")

    highest = max((_severity_rank(item["severity"]) for item in risk_hits), default=0)
    risk_level = {0: "low", 1: "low", 2: "medium", 3: "high"}[highest]
    target_class = _target_class(capabilities, risk_level, total_file_candidates)
    suggested_verification = "deep" if risk_level == "high" else "release" if (has_scripts or has_assets) else "fast"

    diagnostic_status = "BLOCKED" if blockers else "WARN" if warnings or risk_hits else "PASS"
    evidence_completeness = "PARTIAL" if truncated or scanned_text_bytes >= max_text_bytes else "COMPLETE"
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "diagnostic_status": diagnostic_status,
        "valid_as_of": valid_as_of or utc_now()[:10],
        "generated_at": utc_now(),
        "target": {
            "path": str(target),
            "tree_sha256": sha256_tree(target, exclude={"MANIFEST.sha256"}),
            "name": str(skill_frontmatter.get("name", target.name)),
            "description_present": bool(skill_frontmatter.get("description")),
            "skill_lines": skill_lines,
            "file_count": total_file_candidates,
            "scanned_file_count": scanned_files,
            "total_bytes_scanned_inventory": total_bytes,
            "scanned_text_bytes": scanned_text_bytes,
        },
        "classification": {
            "target_class": target_class,
            "risk_level": risk_level,
            "suggested_verification_level": suggested_verification,
            "evidence_completeness": evidence_completeness,
        },
        "capabilities": capabilities,
        "inventory": {
            "top_extensions": dict(extension_counts.most_common(20)),
            "top_directories": dict(directory_counts.most_common(20)),
            "runtime_mentions": dict(runtime_mentions.most_common()),
        },
        "risk_signals": sorted(risk_hits, key=lambda item: (-_severity_rank(item["severity"]), item["path"], item["line"], item["signal"])),
        "blockers": sorted(set(blockers)),
        "warnings": sorted(set(warnings)),
        "bounded_scan": {
            "max_files": max_files,
            "max_text_bytes": max_text_bytes,
            "max_file_read_bytes": MAX_FILE_READ_BYTES,
            "truncated": truncated,
            "symlinks": sorted(symlinks)[:100],
            "possible_secret_paths": sorted(set(possible_secrets))[:100],
            "invalid_utf8_paths": sorted(set(invalid_text))[:100],
        },
        "environment": {
            "python": platform.python_version(),
            "python_supported": sys.version_info >= (3, 9),
            "git_available": shutil.which("git") is not None,
            "platform": platform.system(),
            "machine": platform.machine(),
            "filesystem_case_sensitive_probe": os.path.normcase("A") != os.path.normcase("a"),
        },
        "claim_boundary": "This static diagnosis does not execute the target and cannot prove task outcome or safety.",
    }
    if output is not None:
        write_json(output.resolve(), result)
    return result
