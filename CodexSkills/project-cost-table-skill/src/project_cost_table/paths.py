"""Root containment and rollback-safe atomic output primitives."""

from __future__ import annotations

import ctypes
import errno
import os
import re
import shutil
import stat
import tempfile
import sys
from contextlib import contextmanager
from pathlib import Path, PurePosixPath
from typing import BinaryIO, Callable, Iterator, Union


PathLike = Union[str, Path]


class PathSafetyError(RuntimeError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__("%s: %s" % (code, message))
        self.code = code
        self.message = message


def _existing_root(root: PathLike) -> Path:
    value = Path(root)
    if value.is_symlink():
        raise PathSafetyError("ROOT_SYMLINK", "allowed root must not be a symbolic link")
    try:
        resolved = value.resolve(strict=True)
    except OSError as exc:
        raise PathSafetyError("ROOT_UNAVAILABLE", "allowed root does not exist") from exc
    if not resolved.is_dir():
        raise PathSafetyError("ROOT_NOT_DIRECTORY", "allowed root must be a directory")
    return resolved


def _contains(root: Path, candidate: Path) -> bool:
    try:
        candidate.relative_to(root)
        return True
    except ValueError:
        return False


def resolve_input_file(root: PathLike, candidate: PathLike, *, max_bytes: int = 0) -> Path:
    """Resolve one regular, single-link input without following in-root symlinks."""

    lexical_root = Path(os.path.abspath(str(Path(root))))
    resolved_root = _existing_root(root)
    raw = Path(candidate)
    if "\x00" in str(candidate) or "\\" in str(candidate) or ".." in raw.parts:
        raise PathSafetyError("PATH_TRAVERSAL", "input path contains a forbidden component")
    lexical = Path(os.path.abspath(str(raw if raw.is_absolute() else lexical_root / raw)))
    try:
        relative = lexical.relative_to(lexical_root)
        current = lexical_root
    except ValueError:
        try:
            relative = lexical.relative_to(resolved_root)
            current = resolved_root
        except ValueError as exc:
            raise PathSafetyError("OUTSIDE_ROOT", "input path is outside the allowed root") from exc
    for part in relative.parts:
        current = current / part
        try:
            metadata = current.lstat()
        except OSError as exc:
            raise PathSafetyError("INPUT_UNAVAILABLE", "input path does not exist") from exc
        if stat.S_ISLNK(metadata.st_mode):
            raise PathSafetyError("INPUT_SYMLINK", "symbolic links are forbidden for governed inputs")
    try:
        resolved = lexical.resolve(strict=True)
    except OSError as exc:
        raise PathSafetyError("INPUT_UNAVAILABLE", "input path cannot be resolved") from exc
    if not _contains(resolved_root, resolved):
        raise PathSafetyError("SYMLINK_ESCAPE", "resolved input escapes the allowed root")
    metadata = resolved.stat()
    if not stat.S_ISREG(metadata.st_mode):
        raise PathSafetyError("INPUT_NOT_REGULAR", "input must be a regular file")
    if metadata.st_nlink != 1:
        raise PathSafetyError("INPUT_HARDLINK", "governed input must have exactly one hard link")
    if max_bytes > 0 and metadata.st_size > max_bytes:
        raise PathSafetyError("INPUT_TOO_LARGE", "input exceeds the configured size ceiling")
    return resolved


def _safe_output_target(root: PathLike, relative_path: PathLike) -> Path:
    root_path = Path(root)
    if root_path.exists() and root_path.is_symlink():
        raise PathSafetyError("OUTPUT_ROOT_SYMLINK", "output root must not be a symbolic link")
    root_path.mkdir(parents=True, exist_ok=True)
    resolved_root = _existing_root(root_path)
    raw = str(relative_path)
    if not raw or "\x00" in raw or "\\" in raw or re.match(r"^[A-Za-z]:", raw):
        raise PathSafetyError("UNSAFE_OUTPUT_PATH", "output path must be portable and relative")
    relative = PurePosixPath(raw)
    raw_components = raw.split("/")
    if (
        relative.is_absolute()
        or not relative.parts
        or any(component in ("", ".", "..") for component in raw_components)
    ):
        raise PathSafetyError("UNSAFE_OUTPUT_PATH", "output path contains a forbidden component")
    current = resolved_root
    for part in relative.parts[:-1]:
        current = current / part
        if current.exists() and (current.is_symlink() or not current.is_dir()):
            raise PathSafetyError("UNSAFE_OUTPUT_PARENT", "output parent is not a safe directory")
        current.mkdir(exist_ok=True)
    target = current / relative.parts[-1]
    if target.exists() or target.is_symlink():
        raise PathSafetyError("OUTPUT_EXISTS", "atomic output never overwrites an existing target")
    return target


def _fsync_directory(path: Path) -> None:
    descriptor = os.open(str(path), os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _rename_directory_no_replace(source: Path, target: Path) -> None:
    """Use the host's atomic no-replace rename or fail closed."""

    libc = ctypes.CDLL(None, use_errno=True)
    source_bytes = os.fsencode(str(source))
    target_bytes = os.fsencode(str(target))
    if sys.platform == "darwin" and hasattr(libc, "renamex_np"):
        function = libc.renamex_np
        function.argtypes = (ctypes.c_char_p, ctypes.c_char_p, ctypes.c_uint)
        function.restype = ctypes.c_int
        result = function(source_bytes, target_bytes, 0x00000004)  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        function = libc.renameat2
        function.argtypes = (
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_int,
            ctypes.c_char_p,
            ctypes.c_uint,
        )
        function.restype = ctypes.c_int
        result = function(-100, source_bytes, -100, target_bytes, 0x00000001)  # AT_FDCWD, RENAME_NOREPLACE
    else:
        raise PathSafetyError(
            "ATOMIC_DIRECTORY_UNSUPPORTED",
            "host does not expose an atomic no-replace directory rename",
        )
    if result == 0:
        return
    error_number = ctypes.get_errno()
    if error_number in (errno.EEXIST, errno.ENOTEMPTY):
        raise PathSafetyError("OUTPUT_EXISTS", "atomic output directory target appeared during publish")
    raise OSError(error_number, os.strerror(error_number), str(target))


def atomic_write_with_writer(
    root: PathLike,
    relative_path: PathLike,
    writer: Callable[[BinaryIO], None],
) -> Path:
    """Write through a non-final-looking sibling and publish without overwrite."""

    target = _safe_output_target(root, relative_path)
    descriptor, temporary_name = tempfile.mkstemp(prefix=".partial-", dir=str(target.parent))
    temporary = Path(temporary_name)
    published = False
    try:
        with os.fdopen(descriptor, "wb") as handle:
            writer(handle)
            handle.flush()
            os.fsync(handle.fileno())
        try:
            os.link(str(temporary), str(target))
            published = True
        except FileExistsError as exc:
            raise PathSafetyError("OUTPUT_EXISTS", "atomic output target appeared during publish") from exc
        _fsync_directory(target.parent)
        temporary.unlink()
        _fsync_directory(target.parent)
        return target
    except Exception:
        if temporary.exists():
            temporary.unlink()
        if published and target.exists():
            target.unlink()
        raise


def atomic_write_bytes(root: PathLike, relative_path: PathLike, data: bytes) -> Path:
    if not isinstance(data, bytes):
        raise TypeError("atomic_write_bytes requires bytes")
    return atomic_write_with_writer(root, relative_path, lambda handle: handle.write(data))


def atomic_write_text(root: PathLike, relative_path: PathLike, text: str) -> Path:
    if not isinstance(text, str):
        raise TypeError("atomic_write_text requires str")
    return atomic_write_bytes(root, relative_path, text.encode("utf-8"))


@contextmanager
def atomic_output_directory(root: PathLike, relative_path: PathLike) -> Iterator[Path]:
    """Publish a complete directory only after the caller exits successfully."""

    target = _safe_output_target(root, relative_path)
    temporary = Path(tempfile.mkdtemp(prefix=".partial-dir-", dir=str(target.parent)))
    published = False
    try:
        yield temporary
        if target.exists():
            raise PathSafetyError("OUTPUT_EXISTS", "atomic output directory target already exists")
        _rename_directory_no_replace(temporary, target)
        published = True
        _fsync_directory(target.parent)
    except Exception:
        if temporary.exists():
            shutil.rmtree(temporary)
        if published and target.exists():
            shutil.rmtree(target)
        raise
