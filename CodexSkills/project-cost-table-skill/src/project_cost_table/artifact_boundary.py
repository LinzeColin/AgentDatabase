"""Default-deny public/private/raw artifact boundary enforcement."""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from enum import Enum
from pathlib import Path, PurePosixPath
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

import yaml


class Plane(str, Enum):
    PUBLIC_SAFE = "PUBLIC_SAFE"
    PRIVATE_RUNTIME = "PRIVATE_RUNTIME"
    RAW_SOURCE = "RAW_SOURCE"
    UNCLASSIFIED = "UNCLASSIFIED"


@dataclass(frozen=True)
class Finding:
    path: str
    code: str
    message: str

    def as_dict(self) -> Dict[str, str]:
        return {"path": self.path, "code": self.code, "message": self.message}


class PolicyError(RuntimeError):
    """Raised when the boundary policy cannot be loaded safely."""


def _normalize_relative_path(raw_path: str) -> PurePosixPath:
    candidate = raw_path.replace("\\", "/")
    if not candidate or candidate.startswith("/") or re.match(r"^[A-Za-z]:/", candidate):
        raise ValueError("path must be non-empty and module-relative")
    path = PurePosixPath(candidate)
    if any(part in ("", ".", "..") for part in path.parts):
        raise ValueError("path traversal and ambiguous components are forbidden")
    return path


def _string_list(config: Mapping[str, Any], key: str) -> Tuple[str, ...]:
    value = config.get(key)
    if not isinstance(value, list) or not value or not all(isinstance(item, str) for item in value):
        raise PolicyError("%s must be a non-empty string list" % key)
    return tuple(value)


class ArtifactBoundaryPolicy:
    def __init__(self, config: Mapping[str, Any]) -> None:
        if config.get("policy_version") != 1:
            raise PolicyError("unsupported or missing policy_version")
        self.scope = str(config.get("scope") or "")
        if not self.scope:
            raise PolicyError("scope is required")
        self.public_root_files = frozenset(_string_list(config, "public_root_files"))
        self.public_roots = frozenset(_string_list(config, "public_roots"))
        self.private_roots = frozenset(_string_list(config, "private_roots"))
        self.raw_roots = frozenset(_string_list(config, "raw_roots"))
        overlap = (self.public_roots & self.private_roots) | (self.public_roots & self.raw_roots) | (
            self.private_roots & self.raw_roots
        )
        if overlap:
            raise PolicyError("artifact roots overlap: %s" % sorted(overlap))
        extensions = _string_list(config, "forbidden_public_extensions")
        if any(not item.startswith(".") or item != item.lower() for item in extensions):
            raise PolicyError("forbidden extensions must be lowercase and start with a dot")
        self.forbidden_public_extensions = frozenset(extensions)
        max_text_bytes = config.get("max_text_bytes")
        if not isinstance(max_text_bytes, int) or isinstance(max_text_bytes, bool) or max_text_bytes <= 0:
            raise PolicyError("max_text_bytes must be a positive integer")
        self.max_text_bytes = max_text_bytes
        patterns = config.get("forbidden_content_patterns")
        if not isinstance(patterns, list) or not patterns:
            raise PolicyError("forbidden_content_patterns must be non-empty")
        compiled: List[Tuple[str, re.Pattern[str]]] = []
        for item in patterns:
            if not isinstance(item, dict) or not isinstance(item.get("pattern_id"), str) or not isinstance(
                item.get("regex"), str
            ):
                raise PolicyError("each forbidden content pattern needs pattern_id and regex")
            try:
                compiled.append((item["pattern_id"], re.compile(item["regex"])))
            except re.error as exc:
                raise PolicyError("invalid regex for %s: %s" % (item["pattern_id"], exc)) from exc
        self.forbidden_content_patterns = tuple(compiled)

    @classmethod
    def from_yaml(cls, path: Path) -> "ArtifactBoundaryPolicy":
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, yaml.YAMLError) as exc:
            raise PolicyError("cannot load artifact policy: %s" % exc) from exc
        if not isinstance(raw, dict):
            raise PolicyError("artifact policy must be a mapping")
        return cls(raw)

    def classify(self, raw_path: str) -> Plane:
        try:
            path = _normalize_relative_path(raw_path)
        except ValueError:
            return Plane.UNCLASSIFIED
        first = path.parts[0]
        if first in self.private_roots:
            return Plane.PRIVATE_RUNTIME
        if first in self.raw_roots:
            return Plane.RAW_SOURCE
        if len(path.parts) == 1 and first in self.public_root_files:
            return Plane.PUBLIC_SAFE
        if first in self.public_roots:
            return Plane.PUBLIC_SAFE
        return Plane.UNCLASSIFIED

    def inspect_public_bytes(self, raw_path: str, data: bytes, git_mode: Optional[str] = None) -> List[Finding]:
        findings: List[Finding] = []
        plane = self.classify(raw_path)
        if plane is not Plane.PUBLIC_SAFE:
            findings.append(
                Finding(raw_path, "NON_PUBLIC_PATH", "tracked candidate is classified as %s" % plane.value)
            )
            return findings
        suffix = PurePosixPath(raw_path).suffix.lower()
        if suffix in self.forbidden_public_extensions:
            findings.append(Finding(raw_path, "FORBIDDEN_EXTENSION", "public extension %s is forbidden" % suffix))
        if git_mode == "120000":
            findings.append(Finding(raw_path, "SYMLINK_FORBIDDEN", "symbolic links are forbidden in the public plane"))
        if len(data) > self.max_text_bytes:
            findings.append(
                Finding(
                    raw_path,
                    "FILE_TOO_LARGE",
                    "public text exceeds %d bytes" % self.max_text_bytes,
                )
            )
            return findings
        if b"\x00" in data:
            findings.append(Finding(raw_path, "BINARY_FORBIDDEN", "binary content is forbidden in the public plane"))
            return findings
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            findings.append(Finding(raw_path, "NON_UTF8_FORBIDDEN", "public content must be UTF-8 text"))
            return findings
        for pattern_id, pattern in self.forbidden_content_patterns:
            if pattern.search(text):
                findings.append(
                    Finding(raw_path, "FORBIDDEN_CONTENT", "content matched policy pattern %s" % pattern_id)
                )
        return findings


def scan_working_tree(module_root: Path, policy: ArtifactBoundaryPolicy) -> List[Finding]:
    root = module_root.resolve()
    findings: List[Finding] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        plane = policy.classify(relative)
        if path.is_symlink():
            if plane is Plane.PUBLIC_SAFE:
                findings.extend(policy.inspect_public_bytes(relative, b"", git_mode="120000"))
            continue
        if not path.is_file():
            continue
        if plane in (Plane.PRIVATE_RUNTIME, Plane.RAW_SOURCE):
            continue
        if plane is Plane.UNCLASSIFIED:
            findings.append(Finding(relative, "UNCLASSIFIED_PATH", "working-tree path is not classified"))
            continue
        try:
            data = path.read_bytes()
        except OSError as exc:
            findings.append(Finding(relative, "UNREADABLE_FILE", "cannot read public file: %s" % exc))
            continue
        findings.extend(policy.inspect_public_bytes(relative, data))
    return findings


def _git(repo_root: Path, args: Sequence[str]) -> bytes:
    try:
        return subprocess.check_output(["git", *args], cwd=str(repo_root), stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exc:
        detail = exc.output.decode("utf-8", errors="replace").strip()
        raise PolicyError("git command failed: %s" % detail) from exc


def scan_staged(repo_root: Path, module_relative_root: str, policy: ArtifactBoundaryPolicy) -> List[Finding]:
    repo = repo_root.resolve()
    module_prefix = _normalize_relative_path(module_relative_root).as_posix().rstrip("/") + "/"
    raw_names = _git(repo, ["diff", "--cached", "--name-only", "-z", "--diff-filter=ACMR"])
    staged_names = [name.decode("utf-8") for name in raw_names.split(b"\0") if name]
    findings: List[Finding] = []
    for full_path in sorted(staged_names):
        if not full_path.startswith(module_prefix):
            continue
        relative = full_path[len(module_prefix) :]
        try:
            index_row = _git(repo, ["ls-files", "-s", "--", full_path]).decode("utf-8").strip()
            git_mode = index_row.split(None, 1)[0]
            data = _git(repo, ["show", ":%s" % full_path])
        except (PolicyError, IndexError) as exc:
            findings.append(Finding(relative, "INDEX_READ_FAILED", str(exc)))
            continue
        findings.extend(policy.inspect_public_bytes(relative, data, git_mode=git_mode))
    return findings
