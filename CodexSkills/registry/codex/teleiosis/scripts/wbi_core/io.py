from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import tempfile
import uuid
import unicodedata
import zipfile
from typing import Any, Dict, Iterable, Iterator, List, Optional, Tuple

SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".tox", ".venv"}
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
TEXT_SUFFIXES = {".md", ".txt", ".json", ".jsonl", ".py", ".sh", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".csv", ".tsv", ".html", ".css", ".js"}
NAME_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
VERSION_RE = re.compile(r"^v\d+\.\d+\.\d+\.\d+$")
SECRET_PATTERNS = [
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"gh[pousr]_[A-Za-z0-9]{20,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    re.compile(r"(?i)(?:api[_-]?key|secret|password)\s*[:=]\s*['\"]?[A-Za-z0-9_./+\-=]{16,}"),
]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def canonical_json(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def iter_files(root: Path) -> Iterator[Path]:
    root = root.resolve()
    for path in root.rglob("*"):
        try:
            relative = path.relative_to(root)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in relative.parts):
            continue
        if path.is_file() or path.is_symlink():
            yield path


def sha256_tree(root: Path, *, exclude: Optional[Iterable[str]] = None) -> str:
    root = root.resolve()
    excluded = set(exclude or ())
    digest = hashlib.sha256()
    for path in sorted(iter_files(root), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative in excluded:
            continue
        digest.update(relative.encode("utf-8") + b"\0")
        if path.is_symlink():
            digest.update(b"SYMLINK\0" + os.readlink(path).encode("utf-8"))
        else:
            digest.update(bytes.fromhex(sha256_file(path)))
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_relative_file(root: Path, relative: str, *, label: str = "file") -> Path:
    """Resolve one governed file without allowing absolute paths or traversal."""
    root = root.resolve()
    candidate = Path(str(relative))
    if not str(relative) or candidate.is_absolute() or ".." in candidate.parts or "\\" in str(relative):
        raise ValueError("unsafe %s path: %s" % (label, relative))
    resolved = (root / candidate).resolve()
    if root not in resolved.parents or not resolved.is_file() or resolved.is_symlink():
        raise ValueError("%s missing, linked or escaped root: %s" % (label, relative))
    return resolved


def bind_files(root: Path, paths: Any, *, label: str = "evidence") -> List[Dict[str, Any]]:
    """Create immutable content bindings for governed relative file paths."""
    if not isinstance(paths, list) or not paths:
        raise ValueError("%s paths must be a non-empty list" % label)
    bindings: List[Dict[str, Any]] = []
    seen = set()
    for value in paths:
        relative = str(value)
        if relative in seen:
            continue
        seen.add(relative)
        path = resolve_relative_file(root, relative, label=label)
        bindings.append({"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    if not bindings:
        raise ValueError("%s paths resolved to no files" % label)
    return bindings


def verify_file_bindings(root: Path, bindings: Any, *, label: str = "evidence") -> List[str]:
    """Recheck path, hash and size for a list of previously frozen bindings."""
    errors: List[str] = []
    if not isinstance(bindings, list) or not bindings:
        return ["%s bindings missing" % label]
    seen = set()
    for index, binding in enumerate(bindings, 1):
        if not isinstance(binding, dict):
            errors.append("%s binding %d must be an object" % (label, index))
            continue
        relative = str(binding.get("path", ""))
        if relative in seen:
            errors.append("duplicate %s binding path: %s" % (label, relative))
            continue
        seen.add(relative)
        try:
            path = resolve_relative_file(root, relative, label=label)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if binding.get("sha256") != sha256_file(path):
            errors.append("%s hash mismatch: %s" % (label, relative))
        supplied_size = binding.get("bytes")
        if isinstance(supplied_size, bool) or not isinstance(supplied_size, int):
            errors.append("%s size is not an integer: %s" % (label, relative))
        elif supplied_size != path.stat().st_size:
            errors.append("%s size mismatch: %s" % (label, relative))
    return errors


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(".%s.%s.tmp" % (path.name, uuid.uuid4().hex))
    try:
        with temporary.open("w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(str(temporary), str(path))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=False) + "\n")


def _yaml_scalar(raw: str) -> Any:
    value = raw.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"\"", "\'"}:
        return value[1:-1]
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    if lowered in {"null", "~"}:
        return None
    if re.fullmatch(r"-?\d+", value):
        try:
            return int(value)
        except ValueError:
            pass
    return value


def read_frontmatter(path: Path) -> Tuple[Dict[str, Any], str]:
    """Parse the dependency-free YAML subset needed by Agent Skill metadata.

    It supports nested mappings plus literal/folded block scalars, which avoids
    rejecting otherwise valid Skills that use a multiline description. Lists
    and advanced YAML objects are intentionally left as strings because the
    validator only needs name, description and metadata.version.
    """
    text = path.read_text(encoding="utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]
    if not text.startswith("---\n"):
        raise ValueError("SKILL.md must begin with YAML frontmatter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise ValueError("SKILL.md frontmatter is not closed")
    lines = text[4:end].splitlines()
    root: Dict[str, Any] = {}
    stack: List[Tuple[int, Dict[str, Any]]] = [(-1, root)]
    index = 0
    while index < len(lines):
        raw = lines[index]
        index += 1
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        if "\t" in raw[: len(raw) - len(raw.lstrip())]:
            raise ValueError("frontmatter indentation must use spaces")
        if ":" not in raw:
            continue
        indent = len(raw) - len(raw.lstrip(" "))
        key, raw_value = raw.strip().split(":", 1)
        key = key.strip()
        if not key:
            raise ValueError("frontmatter key cannot be empty")
        while stack and stack[-1][0] >= indent:
            stack.pop()
        if not stack:
            raise ValueError("invalid frontmatter indentation")
        parent = stack[-1][1]
        value = raw_value.strip()
        if value in {"|", ">", "|-", ">-", "|+", ">+"}:
            block: List[str] = []
            while index < len(lines):
                candidate = lines[index]
                candidate_indent = len(candidate) - len(candidate.lstrip(" "))
                if candidate.strip() and candidate_indent <= indent:
                    break
                index += 1
                if not candidate.strip():
                    block.append("")
                else:
                    strip_by = min(len(candidate), indent + 2)
                    block.append(candidate[strip_by:])
            if value.startswith(">"): 
                parent[key] = " ".join(part.strip() for part in block if part.strip())
            else:
                parent[key] = "\n".join(block).strip("\n")
        elif value:
            parent[key] = _yaml_scalar(value)
        else:
            child: Dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
    return root, text[end + 5 :]


def ensure_external(path: Path, protected: Iterable[Path], label: str) -> None:
    resolved = path.resolve()
    for item in protected:
        protected_path = item.resolve()
        if resolved == protected_path or protected_path in resolved.parents or resolved in protected_path.parents:
            raise ValueError("%s must be outside protected directory: %s" % (label, protected_path))


def _find_symlinks(root: Path) -> List[str]:
    found: List[str] = []
    for path in root.rglob("*"):
        if path.is_symlink():
            found.append(path.relative_to(root).as_posix())
    return sorted(found)


def copy_clean(source: Path, destination: Path) -> None:
    source, destination = source.resolve(), destination.resolve()
    if not source.is_dir():
        raise ValueError("copy source is not a directory: %s" % source)
    if source == destination or source in destination.parents or destination in source.parents:
        raise ValueError("copy source and destination must not overlap")
    symlinks = _find_symlinks(source)
    if symlinks:
        raise ValueError("symlinks are not allowed in governed Skill trees: %s" % symlinks)
    if destination.exists():
        shutil.rmtree(str(destination))

    def ignore(_directory: str, names: List[str]) -> List[str]:
        return [name for name in names if name in SKIP_DIRS or name.endswith((".pyc", ".pyo"))]

    shutil.copytree(str(source), str(destination), ignore=ignore, symlinks=True)


def generate_manifest(root: Path, manifest_name: str = "MANIFEST.sha256") -> int:
    root = root.resolve()
    rows: List[str] = []
    for path in sorted(iter_files(root), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if relative == manifest_name:
            continue
        if path.is_symlink():
            raise ValueError("symlink cannot enter manifest: %s" % relative)
        rows.append("%s  %s" % (sha256_file(path), relative))
    atomic_write_text(root / manifest_name, "\n".join(rows) + "\n")
    return len(rows)


def verify_manifest(root: Path, manifest_name: str = "MANIFEST.sha256") -> List[str]:
    root = root.resolve()
    manifest = root / manifest_name
    if not manifest.is_file():
        return ["missing %s" % manifest_name]
    errors: List[str] = []
    listed: Dict[str, str] = {}
    for number, raw in enumerate(manifest.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            expected, relative = raw.split("  ", 1)
        except ValueError:
            errors.append("invalid manifest line %d" % number)
            continue
        candidate = Path(relative)
        if not re.fullmatch(r"[a-f0-9]{64}", expected):
            errors.append("invalid hash at manifest line %d" % number)
        if candidate.is_absolute() or ".." in candidate.parts:
            errors.append("unsafe manifest path: %s" % relative)
            continue
        if relative in listed:
            errors.append("duplicate manifest path: %s" % relative)
            continue
        listed[relative] = expected
        file_path = root / candidate
        if not file_path.is_file():
            errors.append("manifest file missing: %s" % relative)
        elif sha256_file(file_path) != expected:
            errors.append("manifest hash mismatch: %s" % relative)
    actual = {
        path.relative_to(root).as_posix()
        for path in iter_files(root)
        if not path.is_symlink() and path.relative_to(root).as_posix() != manifest_name
    }
    if actual - set(listed):
        errors.append("manifest missing entries: %s" % sorted(actual - set(listed)))
    if set(listed) - actual:
        errors.append("manifest stale entries: %s" % sorted(set(listed) - actual))
    return errors


def _zip_datetime() -> Tuple[int, int, int, int, int, int]:
    epoch = os.environ.get("SOURCE_DATE_EPOCH")
    if epoch:
        try:
            value = dt.datetime.fromtimestamp(int(epoch), tz=dt.timezone.utc)
            year = max(1980, value.year)
            return (year, value.month, value.day, value.hour, value.minute, value.second)
        except (ValueError, OverflowError):
            pass
    return (2020, 1, 1, 0, 0, 0)


def _canonical_archive_mode(relative: Path) -> int:
    if relative.parts and relative.parts[0] == "scripts" and relative.suffix.lower() in {".py", ".sh"}:
        return 0o755
    return 0o644


def deterministic_zip(root: Path, output: Path) -> Dict[str, Any]:
    root, output = root.resolve(), output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(".%s.%s.tmp" % (output.name, uuid.uuid4().hex))
    top = root.name
    count = 0
    try:
        with zipfile.ZipFile(str(temporary), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(iter_files(root), key=lambda item: item.relative_to(root).as_posix()):
                if path.is_symlink():
                    raise ValueError("symlink cannot be packaged: %s" % path)
                local_relative = path.relative_to(root)
                relative = "%s/%s" % (top, local_relative.as_posix())
                info = zipfile.ZipInfo(relative, _zip_datetime())
                info.create_system = 3
                info.external_attr = (_canonical_archive_mode(local_relative) & 0xFFFF) << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, path.read_bytes())
                count += 1
        os.replace(str(temporary), str(output))
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass
    return {"status": "PASS", "path": str(output), "sha256": sha256_file(output), "entries": count, "top_level": top}


def _normalized_archive_name(name: str) -> str:
    if not name or "\x00" in name or "\\" in name:
        raise ValueError("unsafe archive path: %r" % name)
    normalized = unicodedata.normalize("NFC", name)
    path = Path(normalized)
    if path.is_absolute() or ".." in path.parts or any(part in {"", "."} for part in path.parts):
        raise ValueError("unsafe archive path: %s" % name)
    if path.parts and (":" in path.parts[0] or path.parts[0].strip() != path.parts[0]):
        raise ValueError("unsafe archive path: %s" % name)
    return path.as_posix()


def safe_extract_zip(archive: Path, destination: Path, max_files: int = 5000, max_bytes: int = 500 * 1024 * 1024) -> Dict[str, int]:
    destination = destination.resolve()
    destination.mkdir(parents=True, exist_ok=True)
    file_count = 0
    byte_count = 0
    seen: set = set()
    seen_casefold: set = set()
    with zipfile.ZipFile(str(archive), "r") as handle:
        members = handle.infolist()
        if len(members) > max_files:
            raise ValueError("archive exceeds max file count")
        for member in members:
            normalized = _normalized_archive_name(member.filename.rstrip("/") if member.is_dir() else member.filename)
            identity = normalized.rstrip("/")
            folded = identity.casefold()
            if identity in seen:
                raise ValueError("duplicate archive path: %s" % member.filename)
            if folded in seen_casefold:
                raise ValueError("case-colliding archive path: %s" % member.filename)
            seen.add(identity)
            seen_casefold.add(folded)
            path = Path(identity)
            unix_mode = (member.external_attr >> 16) & 0xFFFF
            file_type = unix_mode & 0o170000
            allowed_types = {0, 0o040000 if member.is_dir() else 0o100000}
            if file_type not in allowed_types:
                raise ValueError("archive special file rejected: %s" % member.filename)
            byte_count += int(member.file_size)
            if byte_count > max_bytes:
                raise ValueError("archive exceeds max bytes")
            if member.is_dir():
                continue
            file_count += 1
            target = (destination / path).resolve()
            if destination not in target.parents and target != destination:
                raise ValueError("archive escapes destination")
            target.parent.mkdir(parents=True, exist_ok=True)
            with handle.open(member) as source, target.open("wb") as sink:
                shutil.copyfileobj(source, sink)
            mode = unix_mode & 0o777
            target.chmod(mode if mode in {0o644, 0o755} else 0o644)
    return {"files": file_count, "bytes": byte_count}


def temp_directory(prefix: str = "wbi-") -> tempfile.TemporaryDirectory:
    return tempfile.TemporaryDirectory(prefix=prefix)
