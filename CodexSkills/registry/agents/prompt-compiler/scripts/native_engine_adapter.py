#!/usr/bin/env python3
"""Native-only execution helpers for Prompt Compiler v0.0.0.4.

This module never emulates GEPA, AutoResearch, Meta-Harness, or Promptfoo. It
validates an upstream workspace/command, runs it in an isolated copy, snapshots
the file tree before and after execution, rejects out-of-contract mutations,
and returns evidence for independent evaluation by Prompt Compiler.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
from typing import Any, Iterable, Mapping, Sequence

IGNORED_TREE_PARTS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".cache",
}
IGNORED_SUFFIXES = {".pyc", ".pyo", ".tmp", ".log"}


class NativeEngineError(RuntimeError):
    def __init__(self, message: str, *, code: str, details: Any = None):
        super().__init__(message)
        self.code = code
        self.details = details


@dataclass(frozen=True)
class WorkspaceEvidence:
    source: str
    isolated: str
    origin: str
    required_files: tuple[str, ...]
    allowed_paths: tuple[str, ...]
    before_tree_sha256: str
    after_tree_sha256: str
    changed_paths: tuple[str, ...]
    command: tuple[str, ...]
    returncode: int
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "isolated": self.isolated,
            "origin": self.origin,
            "required_files": list(self.required_files),
            "allowed_paths": list(self.allowed_paths),
            "before_tree_sha256": self.before_tree_sha256,
            "after_tree_sha256": self.after_tree_sha256,
            "changed_paths": list(self.changed_paths),
            "command": list(self.command),
            "returncode": self.returncode,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }


def _safe_log(value: Any, limit: int = 80_000) -> str:
    text = str(value or "")
    secret_patterns = (
        r"\bsk-[A-Za-z0-9_-]{16,}\b",
        r"\bgh[pousr]_[A-Za-z0-9]{20,}\b",
        r"(?i)(api[_-]?key|token|secret|password)\s*[:=]\s*[^\s,;]{8,}",
    )
    for pattern in secret_patterns:
        text = re.sub(pattern, "[REDACTED]", text)
    return text[-limit:]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _iter_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(root)
        if any(part in IGNORED_TREE_PARTS for part in relative.parts):
            continue
        if path.suffix.lower() in IGNORED_SUFFIXES:
            continue
        yield path


def snapshot_tree(root: Path) -> dict[str, str]:
    root = root.resolve()
    return {path.relative_to(root).as_posix(): sha256_file(path) for path in _iter_files(root)}


def tree_digest(snapshot: Mapping[str, str]) -> str:
    payload = "\n".join(f"{path}\0{digest}" for path, digest in sorted(snapshot.items()))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def snapshot_diff(before: Mapping[str, str], after: Mapping[str, str]) -> list[str]:
    return sorted(path for path in set(before) | set(after) if before.get(path) != after.get(path))


def normalize_relative_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts:
        raise NativeEngineError("原生执行路径必须是工作区内相对路径。", code="NATIVE_PATH_ESCAPE", details=value)
    clean = path.as_posix().lstrip("./")
    if not clean:
        raise NativeEngineError("原生执行路径为空。", code="NATIVE_PATH_EMPTY")
    return clean


def path_is_allowed(path: str, allowed_paths: Sequence[str]) -> bool:
    for raw in allowed_paths:
        allowed = normalize_relative_path(str(raw))
        if path == allowed or path.startswith(allowed.rstrip("/") + "/"):
            return True
    return False


def validate_mutations(changed_paths: Sequence[str], allowed_paths: Sequence[str]) -> None:
    forbidden = [path for path in changed_paths if not path_is_allowed(path, allowed_paths)]
    if forbidden:
        raise NativeEngineError(
            "原生执行修改了合同外文件。",
            code="NATIVE_FORBIDDEN_MUTATION",
            details={"changed_paths": list(changed_paths), "forbidden_paths": forbidden, "allowed_paths": list(allowed_paths)},
        )


def git_origin(workspace: Path) -> str:
    if not (workspace / ".git").exists() or not shutil.which("git"):
        return ""
    completed = subprocess.run(
        ["git", "-C", str(workspace), "remote", "get-url", "origin"],
        text=True,
        capture_output=True,
        timeout=30,
    )
    return completed.stdout.strip() if completed.returncode == 0 else ""


def verify_origin(origin: str, expected_fragments: Sequence[str], *, allow_unverified: bool = False) -> None:
    normalized = origin.lower().replace("\\", "/")
    if any(fragment.lower() in normalized for fragment in expected_fragments):
        return
    if allow_unverified:
        return
    raise NativeEngineError(
        "工作区无法证明来自指定官方仓库。",
        code="NATIVE_ORIGIN_UNVERIFIED",
        details={"origin": origin, "expected_fragments": list(expected_fragments)},
    )


def verify_required_files(workspace: Path, required_files: Sequence[str]) -> None:
    missing = [item for item in required_files if not (workspace / normalize_relative_path(item)).is_file()]
    if missing:
        raise NativeEngineError(
            "原生工作区缺少官方入口或合同文件。",
            code="NATIVE_REQUIRED_FILES_MISSING",
            details=missing,
        )


def isolate_workspace(source: Path, destination: Path) -> Path:
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise NativeEngineError("原生工作区不存在。", code="NATIVE_WORKSPACE_MISSING", details=str(source))
    if destination.exists():
        shutil.rmtree(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if (source / ".git").exists() and shutil.which("git"):
        completed = subprocess.run(
            ["git", "clone", "--no-hardlinks", "--quiet", str(source), str(destination)],
            text=True,
            capture_output=True,
            timeout=300,
        )
        if completed.returncode != 0:
            raise NativeEngineError(
                "无法隔离克隆原生工作区。",
                code="NATIVE_CLONE_FAILED",
                details={"stderr": _safe_log(completed.stderr), "returncode": completed.returncode},
            )
    else:
        shutil.copytree(
            source,
            destination,
            ignore=shutil.ignore_patterns(".venv", "node_modules", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"),
        )
    return destination.resolve()


def command_from_value(value: Any) -> list[str]:
    if value is None or value == "":
        return []
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        return [str(part) for part in value]
    if isinstance(value, str):
        stripped = value.strip()
        if not stripped:
            return []
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, list):
            return [str(part) for part in parsed]
        return shlex.split(stripped)
    raise NativeEngineError("原生命令格式无效。", code="NATIVE_COMMAND_INVALID")


def render_command(command: Sequence[str], variables: Mapping[str, str]) -> list[str]:
    rendered: list[str] = []
    for part in command:
        text = str(part)
        for key, value in variables.items():
            text = text.replace("{" + key + "}", value)
        rendered.append(text)
    return rendered


def run_isolated_workspace(
    *,
    source: Path,
    destination: Path,
    command: Sequence[str],
    required_files: Sequence[str],
    allowed_paths: Sequence[str],
    expected_origin_fragments: Sequence[str],
    timeout_seconds: int,
    environment: Mapping[str, str] | None = None,
    initial_files: Mapping[str, str] | None = None,
    allow_unverified_origin: bool = False,
) -> WorkspaceEvidence:
    if not command:
        raise NativeEngineError("原生执行命令未配置。", code="NATIVE_COMMAND_MISSING")
    origin = git_origin(source)
    verify_origin(origin, expected_origin_fragments, allow_unverified=allow_unverified_origin)
    verify_required_files(source, required_files)
    isolated = isolate_workspace(source, destination)
    verify_required_files(isolated, required_files)
    normalized_allowed = tuple(normalize_relative_path(item) for item in allowed_paths)
    for raw_path, content in dict(initial_files or {}).items():
        relative = normalize_relative_path(str(raw_path))
        if not path_is_allowed(relative, normalized_allowed):
            raise NativeEngineError(
                "初始化文件不在允许修改范围内。",
                code="NATIVE_INITIAL_FILE_FORBIDDEN",
                details={"path": relative, "allowed_paths": list(normalized_allowed)},
            )
        target = isolated / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(str(content), encoding="utf-8")
    before = snapshot_tree(isolated)
    completed = subprocess.run(
        list(command),
        cwd=isolated,
        text=True,
        capture_output=True,
        timeout=timeout_seconds,
        env={**os.environ, **dict(environment or {})},
    )
    after = snapshot_tree(isolated)
    changed = snapshot_diff(before, after)
    validate_mutations(changed, normalized_allowed)
    evidence = WorkspaceEvidence(
        source=str(source),
        isolated=str(isolated),
        origin=origin,
        required_files=tuple(required_files),
        allowed_paths=normalized_allowed,
        before_tree_sha256=tree_digest(before),
        after_tree_sha256=tree_digest(after),
        changed_paths=tuple(changed),
        command=tuple(command),
        returncode=completed.returncode,
        stdout=_safe_log(completed.stdout),
        stderr=_safe_log(completed.stderr),
    )
    if completed.returncode != 0:
        raise NativeEngineError(
            "原生执行命令失败。",
            code="NATIVE_COMMAND_FAILED",
            details=evidence.to_dict(),
        )
    return evidence


def read_candidate_artifact(workspace: Path, candidate_path: str, *, original_sha256: str = "") -> str:
    relative = normalize_relative_path(candidate_path)
    path = workspace / relative
    if not path.is_file() or path.is_symlink():
        raise NativeEngineError(
            "原生执行未生成声明的候选文件。",
            code="NATIVE_CANDIDATE_MISSING",
            details=relative,
        )
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        raise NativeEngineError("原生候选为空。", code="NATIVE_CANDIDATE_EMPTY", details=relative)
    digest = hashlib.sha256(content.encode("utf-8")).hexdigest()
    if original_sha256 and digest == original_sha256:
        raise NativeEngineError("原生候选与种子完全相同。", code="NATIVE_CANDIDATE_UNCHANGED", details=relative)
    return content


def discover_meta_harness_entrypoint(workspace: Path, preferred: str = "") -> str:
    candidates = []
    if preferred:
        candidates.append(normalize_relative_path(preferred))
    candidates.extend(
        [
            "reference_examples/text_classification/meta_harness.py",
            "reference_examples/terminal_bench_2/meta_harness.py",
        ]
    )
    for relative in dict.fromkeys(candidates):
        if (workspace / relative).is_file():
            return relative
    raise NativeEngineError(
        "未发现 Meta-Harness 官方入口。",
        code="META_HARNESS_ENTRYPOINT_MISSING",
        details=candidates,
    )
