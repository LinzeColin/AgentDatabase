#!/usr/bin/env python3
"""Read-only capability and risk discovery for one verification target (stdlib only)."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import shutil
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

SCHEMA_VERSION = "1.0"
MAX_WALK_FILES = 200_000
MAX_PARSE_BYTES = 2_000_000

BUILD_MARKERS: dict[str, tuple[str, ...]] = {
    "python": ("pyproject.toml", "requirements.txt", "setup.py", "setup.cfg", "Pipfile", "poetry.lock", "uv.lock"),
    "node": ("package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb"),
    "go": ("go.mod", "go.sum"),
    "rust": ("Cargo.toml", "Cargo.lock"),
    "java": ("pom.xml", "build.gradle", "build.gradle.kts", "gradlew"),
    "dotnet": ("global.json", "Directory.Build.props", "packages.lock.json"),
    "ruby": ("Gemfile", "Gemfile.lock"),
    "php": ("composer.json", "composer.lock"),
}

RISK_PATTERNS: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("database_migration", ("migration", "migrations", "alembic", "flyway", "liquibase"), "high"),
    ("authentication_or_authorization", ("auth", "oauth", "sso", "permission", "rbac", "acl"), "high"),
    ("payment_or_billing", ("payment", "billing", "stripe", "invoice", "checkout"), "critical"),
    ("secret_or_credential", ("secret", "credential", "token", "private_key", ".env"), "critical"),
    ("deployment_or_infrastructure", ("deploy", "terraform", "kubernetes", "helm", "docker", "cloudformation"), "high"),
    ("ai_or_agent_behavior", ("prompt", "llm", "agent", "model", "retrieval", "rag", "tool_call"), "high"),
    ("schema_or_contract", ("schema", "openapi", "swagger", "graphql", "proto", "contract"), "high"),
    ("message_or_external_side_effect", ("email", "sms", "webhook", "queue", "kafka", "publish"), "high"),
)

IGNORED_DIRS = {".git", ".hg", ".svn", "node_modules", ".venv", "venv", "dist", "build", "target", "__pycache__"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def safe_relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix() or "."


def ensure_within(path: Path, root: Path, label: str) -> Path:
    resolved = path.expanduser().resolve(strict=True)
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ValueError(f"{label} escapes repository root: {resolved}") from error
    return resolved


def run_read_only(argv: list[str], cwd: Path, timeout: int = 8) -> dict[str, Any]:
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout,
            check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"ok": False, "argv": argv, "error": str(error), "stdout": "", "stderr": ""}
    return {
        "ok": proc.returncode == 0,
        "argv": argv,
        "returncode": proc.returncode,
        "stdout": proc.stdout[:100_000].strip(),
        "stderr": proc.stderr[:20_000].strip(),
    }


def discover_git(repository: Path) -> dict[str, Any]:
    if shutil.which("git") is None:
        return {"available": False, "reason": "git executable not found"}
    inside = run_read_only(["git", "rev-parse", "--is-inside-work-tree"], repository)
    if not inside.get("ok") or inside.get("stdout") != "true":
        return {"available": True, "is_worktree": False}

    commands = {
        "root": ["git", "rev-parse", "--show-toplevel"],
        "head": ["git", "rev-parse", "HEAD"],
        "branch": ["git", "branch", "--show-current"],
        "status": ["git", "status", "--porcelain=v1", "--untracked-files=normal"],
        "remote": ["git", "remote", "get-url", "origin"],
        "upstream": ["git", "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}"],
    }
    raw = {name: run_read_only(argv, repository) for name, argv in commands.items()}
    status = raw["status"].get("stdout", "") if raw["status"].get("ok") else "UNKNOWN"
    return {
        "available": True,
        "is_worktree": True,
        "root": raw["root"].get("stdout", ""),
        "head": raw["head"].get("stdout", ""),
        "branch": raw["branch"].get("stdout", ""),
        "dirty": bool(status and status != "UNKNOWN"),
        "status_porcelain": status.splitlines()[:2_000] if status else [],
        "remote_origin": raw["remote"].get("stdout", ""),
        "upstream": raw["upstream"].get("stdout", ""),
        "errors": {name: value.get("stderr") or value.get("error") for name, value in raw.items() if not value.get("ok")},
    }


def walk_names(root: Path) -> tuple[list[str], list[dict[str, str]], bool]:
    names: list[str] = []
    unsafe: list[dict[str, str]] = []
    count = 0
    truncated = False
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = sorted(current.iterdir(), key=lambda p: p.name.casefold(), reverse=True)
        except OSError as error:
            unsafe.append({"path": safe_relative(current, root), "reason": f"cannot list: {error}"})
            continue
        for path in entries:
            count += 1
            if count > MAX_WALK_FILES:
                truncated = True
                return names, unsafe, truncated
            rel = safe_relative(path, root)
            try:
                mode = path.lstat().st_mode
            except OSError as error:
                unsafe.append({"path": rel, "reason": f"cannot stat: {error}"})
                continue
            if stat.S_ISLNK(mode):
                unsafe.append({"path": rel, "reason": "symlink present; target not followed"})
                names.append(rel)
                continue
            names.append(rel)
            if stat.S_ISDIR(mode) and path.name not in IGNORED_DIRS:
                stack.append(path)
            elif not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                unsafe.append({"path": rel, "reason": "non-regular filesystem entry"})
    return names, unsafe, truncated


def discover_project_types(names: Iterable[str]) -> tuple[list[str], list[str]]:
    basenames = {Path(name).name for name in names}
    ecosystems: list[str] = []
    markers: list[str] = []
    for ecosystem, candidates in BUILD_MARKERS.items():
        matched = sorted(basenames.intersection(candidates))
        if matched:
            ecosystems.append(ecosystem)
            markers.extend(f"{ecosystem}:{value}" for value in matched)
    return ecosystems, sorted(markers)


def parse_package_json(path: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size > MAX_PARSE_BYTES:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    if not isinstance(value, dict):
        return {}
    scripts = value.get("scripts") if isinstance(value.get("scripts"), dict) else {}
    safe_names = [name for name in ("test", "lint", "typecheck", "build", "start", "e2e", "ci") if name in scripts]
    manager = "npm"
    if (path.parent / "pnpm-lock.yaml").is_file():
        manager = "pnpm"
    elif (path.parent / "yarn.lock").is_file():
        manager = "yarn"
    elif (path.parent / "bun.lock").exists() or (path.parent / "bun.lockb").exists():
        manager = "bun"
    return {
        "name": value.get("name", ""),
        "package_manager": manager,
        "declared_script_names": sorted(safe_names),
        "candidate_argv": [[manager, "run", name] for name in sorted(safe_names)],
    }


def candidate_commands(target: Path, ecosystems: list[str]) -> list[dict[str, Any]]:
    commands: list[dict[str, Any]] = []
    package = parse_package_json(target / "package.json")
    for argv in package.get("candidate_argv", []):
        commands.append({"source": "package.json script name", "argv": argv, "execute": False})
    if "python" in ecosystems:
        if (target / "pytest.ini").exists() or (target / "pyproject.toml").exists() or (target / "tests").is_dir():
            commands.append({"source": "python project markers", "argv": [sys.executable, "-m", "pytest"], "execute": False})
        commands.append({"source": "stdlib fallback", "argv": [sys.executable, "-m", "unittest", "discover"], "execute": False})
    if "go" in ecosystems:
        commands.append({"source": "go.mod", "argv": ["go", "test", "./..."], "execute": False})
    if "rust" in ecosystems:
        commands.append({"source": "Cargo.toml", "argv": ["cargo", "test", "--locked"], "execute": False})
    if "java" in ecosystems:
        if (target / "gradlew").exists():
            commands.append({"source": "gradle wrapper", "argv": ["./gradlew", "test"], "execute": False})
        if (target / "pom.xml").exists():
            commands.append({"source": "pom.xml", "argv": ["mvn", "test"], "execute": False})
    return commands


def risk_signals(names: Iterable[str]) -> list[dict[str, str]]:
    lower_names = [name.casefold() for name in names]
    signals: list[dict[str, str]] = []
    for signal, needles, severity in RISK_PATTERNS:
        matches = sorted({name for name, lowered in zip(names, lower_names) if any(needle in lowered for needle in needles)})[:20]
        if matches:
            signals.append({"signal": signal, "suggested_severity": severity, "examples": matches})
    return signals


def detect_ci(names: Iterable[str]) -> list[str]:
    prefixes = {
        ".github/workflows/": "github-actions",
        ".gitlab-ci.yml": "gitlab-ci",
        "azure-pipelines.yml": "azure-pipelines",
        "Jenkinsfile": "jenkins",
        ".circleci/": "circleci",
    }
    found: set[str] = set()
    for name in names:
        for marker, label in prefixes.items():
            if name == marker or name.startswith(marker):
                found.add(label)
    return sorted(found)


def build_report(repository_arg: Path, target_arg: str) -> dict[str, Any]:
    repository = repository_arg.expanduser().resolve(strict=True)
    if not repository.is_dir():
        raise ValueError(f"repository is not a directory: {repository}")
    target = ensure_within(repository / target_arg, repository, "target project")
    if not target.is_dir():
        raise ValueError(f"target project is not a directory: {target}")

    names, unsafe_entries, truncated = walk_names(target)
    ecosystems, markers = discover_project_types(names)
    git = discover_git(repository)
    signals = risk_signals(names)
    critical = any(item["suggested_severity"] == "critical" for item in signals)
    high = any(item["suggested_severity"] == "high" for item in signals)
    suggested_profile = "deep" if critical or high else ("standard" if ecosystems else "standard")

    casefold: dict[str, str] = {}
    case_collisions: list[list[str]] = []
    for name in sorted(names):
        key = name.casefold()
        prior = casefold.get(key)
        if prior is not None and prior != name:
            case_collisions.append([prior, name])
        casefold[key] = name

    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": utc_now(),
        "read_only": True,
        "repository": {
            "root": str(repository),
            "target_project_path": safe_relative(target, repository),
            "target_inventory_digest_sha256": sha256_text("\n".join(sorted(names))),
            "observed_entry_count": len(names),
            "walk_truncated": truncated,
            "unsafe_entries": unsafe_entries,
            "case_collisions": case_collisions,
        },
        "git": git,
        "environment": {
            "platform": platform.platform(),
            "python": platform.python_version(),
            "executable": sys.executable,
            "cwd": str(Path.cwd()),
            "ci_environment": bool(os.getenv("CI")),
            "available_executables": sorted(name for name in ("git", "python3", "node", "npm", "pnpm", "yarn", "go", "cargo", "mvn", "docker", "kubectl") if shutil.which(name)),
        },
        "project": {
            "ecosystems": ecosystems,
            "markers": markers,
            "ci_systems": detect_ci(names),
            "candidate_commands": candidate_commands(target, ecosystems),
        },
        "risk": {
            "signals": signals,
            "suggested_profile": suggested_profile,
            "requires_owner_authorization_before_side_effects": True,
        },
        "limitations": [
            "Discovery did not execute project code or candidate commands.",
            "File-name heuristics can miss risks or produce false positives.",
            "Ignored dependency/build directories were not recursively inventoried.",
        ],
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repository", type=Path)
    parser.add_argument("--target-project", default=".")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true", help="print compact JSON instead of human summary")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        report = build_report(args.repository, args.target_project)
    except (OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False), file=sys.stderr)
        return 2
    text = json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
    if args.json or not args.output:
        print(text, end="")
    else:
        print(f"CAPABILITY_REPORT: {args.output.resolve()}")
        print(f"profile={report['risk']['suggested_profile']} entries={report['repository']['observed_entry_count']} read_only=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
