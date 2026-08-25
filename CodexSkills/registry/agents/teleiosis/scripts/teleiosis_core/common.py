from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import stat
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Optional, Sequence, Tuple

VERSION = "v0.0.0.5"
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
MAX_FILES = 50000
MAX_TOTAL_BYTES = 2 * 1024 * 1024 * 1024
MAX_JSON_BYTES = 16 * 1024 * 1024
JUNK_NAMES = {".DS_Store", "Thumbs.db", "desktop.ini"}
JUNK_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules", ".git"}
EXECUTABLE_SUFFIXES = {".py", ".pyw", ".sh", ".bash", ".zsh", ".fish", ".command", ".bat", ".cmd", ".ps1", ".js", ".mjs", ".cjs", ".ts", ".exe", ".dll", ".so", ".dylib"}


class TeleiosisError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}

    def as_dict(self) -> Dict[str, Any]:
        return {"status": "ERROR", "error": {"code": self.code, "message": self.message, "details": redact(self.details)}}


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(1024 * 1024)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def canonical_json_hash(value: Any) -> str:
    return sha256_bytes(canonical_json_bytes(value))


def read_json(path: Path, max_bytes: int = MAX_JSON_BYTES) -> Any:
    require_regular_file(path)
    size = path.stat().st_size
    if size > max_bytes:
        raise TeleiosisError("INPUT_TOO_LARGE", "JSON 文件超过上限。", {"path": str(path), "size": size, "limit": max_bytes})
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise TeleiosisError("INVALID_JSON", "JSON 文件无法解析。", {"path": str(path), "reason": str(exc)})


def atomic_write_bytes(path: Path, data: bytes, mode: int = 0o600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.is_symlink():
        raise TeleiosisError("SYMLINK_REFUSED", "拒绝写入符号链接。", {"path": str(path)})
    fd, tmp_name = tempfile.mkstemp(prefix=".teleiosis-write-", dir=str(path.parent))
    tmp = Path(tmp_name)
    try:
        with os.fdopen(fd, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(tmp, mode)
        os.replace(str(tmp), str(path))
    except Exception:
        try:
            tmp.unlink()
        except OSError:
            pass
        raise


def atomic_write_json(path: Path, value: Any, mode: int = 0o600) -> None:
    atomic_write_bytes(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8") + b"\n", mode)


def atomic_write_text(path: Path, text: str, mode: int = 0o600) -> None:
    if not text.endswith("\n"):
        text += "\n"
    atomic_write_bytes(path, text.encode("utf-8"), mode)


def ensure_plain_directory(path: Path, must_exist: bool = True) -> Path:
    expanded = path.expanduser()
    if must_exist and not expanded.exists():
        raise TeleiosisError("DIRECTORY_MISSING", "目录不存在。", {"path": str(expanded)})
    if expanded.exists():
        if expanded.is_symlink():
            raise TeleiosisError("SYMLINK_REFUSED", "拒绝符号链接目录。", {"path": str(expanded)})
        if not expanded.is_dir():
            raise TeleiosisError("NOT_A_DIRECTORY", "路径不是目录。", {"path": str(expanded)})
        return expanded.resolve()
    return expanded.absolute()


def require_regular_file(path: Path) -> None:
    if not path.exists():
        raise TeleiosisError("FILE_MISSING", "文件不存在。", {"path": str(path)})
    if path.is_symlink() or not path.is_file():
        raise TeleiosisError("NOT_REGULAR_FILE", "路径不是普通文件。", {"path": str(path)})


def is_relative_to(path: Path, base: Path) -> bool:
    try:
        path.relative_to(base)
        return True
    except ValueError:
        return False


def ensure_not_nested(left: Path, right: Path) -> None:
    l = left.resolve()
    r = right.resolve() if right.exists() else right.absolute()
    if l == r or is_relative_to(l, r) or is_relative_to(r, l):
        raise TeleiosisError("NESTED_PATHS", "Subject、Workspace 或安装路径不得互相嵌套。", {"left": str(l), "right": str(r)})


def safe_relative_path(value: str) -> Path:
    p = Path(value)
    if p.is_absolute() or any(part in {"", ".", ".."} for part in p.parts):
        raise TeleiosisError("UNSAFE_PATH", "相对路径不安全。", {"path": value})
    return p


def iter_tree_files(root: Path, include_manifest: bool = True) -> Iterator[Tuple[Path, Path]]:
    root = ensure_plain_directory(root)
    count = 0
    total = 0
    for current, dirnames, filenames in os.walk(str(root), topdown=True, followlinks=False):
        current_path = Path(current)
        clean_dirs = []
        for name in sorted(dirnames):
            path = current_path / name
            if path.is_symlink():
                raise TeleiosisError("SYMLINK_REFUSED", "文件树包含符号链接目录。", {"path": str(path)})
            if name in JUNK_DIRS:
                raise TeleiosisError("JUNK_FOUND", "文件树包含缓存、版本库或构建垃圾目录。", {"path": str(path)})
            clean_dirs.append(name)
        dirnames[:] = clean_dirs
        for name in sorted(filenames):
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                raise TeleiosisError("NON_REGULAR_ENTRY", "文件树包含非普通文件。", {"path": str(path)})
            if name in JUNK_NAMES or name.endswith((".pyc", ".pyo", "~")):
                raise TeleiosisError("JUNK_FOUND", "文件树包含缓存或编辑器垃圾。", {"path": str(path)})
            rel = path.relative_to(root)
            if not include_manifest and rel.as_posix() == "MANIFEST.sha256":
                continue
            count += 1
            total += path.stat().st_size
            if count > MAX_FILES or total > MAX_TOTAL_BYTES:
                raise TeleiosisError("TREE_LIMIT_EXCEEDED", "文件树超过安全上限。", {"files": count, "bytes": total})
            yield rel, path


def tree_manifest(root: Path, include_manifest: bool = False) -> List[Dict[str, Any]]:
    entries = []
    for rel, path in iter_tree_files(root, include_manifest=include_manifest):
        entries.append({"path": rel.as_posix(), "sha256": sha256_file(path), "size": path.stat().st_size})
    return entries


def tree_digest(root: Path, include_manifest: bool = False) -> str:
    return canonical_json_hash(tree_manifest(root, include_manifest=include_manifest))


def copy_tree_secure(src: Path, dst: Path) -> None:
    src = ensure_plain_directory(src)
    if dst.exists():
        raise TeleiosisError("DESTINATION_EXISTS", "目标目录已存在。", {"path": str(dst)})
    dst.mkdir(parents=True)
    for rel, path in iter_tree_files(src, include_manifest=True):
        target = dst / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(path), str(target), follow_symlinks=False)


def remove_tree(path: Path) -> None:
    if not path.exists():
        return
    if path.is_symlink() or not path.is_dir():
        raise TeleiosisError("UNSAFE_REMOVE", "拒绝删除非普通目录。", {"path": str(path)})
    shutil.rmtree(str(path))


def parse_version(value: str) -> Tuple[int, int, int, int]:
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)\.(\d+)", value.strip())
    if not match:
        raise TeleiosisError("INVALID_VERSION", "版本号格式不合法。", {"version": value})
    return tuple(int(part) for part in match.groups())  # type: ignore[return-value]


def redact(value: Any) -> Any:
    sensitive_keys = {"token", "secret", "password", "passwd", "authorization", "api_key", "apikey", "credential", "cookie"}
    if isinstance(value, dict):
        out = {}
        for key, item in value.items():
            if str(key).lower() in sensitive_keys:
                out[key] = "[REDACTED]"
            else:
                out[key] = redact(item)
        return out
    if isinstance(value, list):
        return [redact(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", value)
        value = re.sub(r"(?i)(sk-[A-Za-z0-9_-]{16,})", "[REDACTED]", value)
        return value
    return value


def is_executable_like(rel: Path) -> bool:
    return rel.suffix.lower() in EXECUTABLE_SUFFIXES or rel.parts[:1] in [("scripts",)]


def write_json_stdout(value: Any) -> None:
    payload = json.dumps(redact(value), ensure_ascii=False, sort_keys=True)
    sys_stdout = getattr(__import__("sys"), "stdout")
    sys_stdout.write(payload + "\n")
    sys_stdout.flush()
