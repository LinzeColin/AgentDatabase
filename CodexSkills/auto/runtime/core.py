"""Shared deterministic primitives for the Auto runtime."""

from __future__ import annotations

import datetime as dt
import hashlib
import os
import secrets
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

from CodexSkills.governance.tools.canonical_json import (
    CanonicalizationError,
    canonicalize_object,
    parse_json_bytes,
)


PROTOCOL = "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
SCHEMA_PREFIX = "urn:linzecolin:agentdatabase:skillops:schema:"
CANDIDATE_MANIFEST_PATH = (
    "CodexSkills/governance/bundles/schema-bundle-manifest.v1.json"
)
CROCKFORD = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"
UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


class AutoRuntimeError(RuntimeError):
    """A stable fail-closed runtime error code."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class Clock:
    """UTC wall-clock interface used by runtime and fake-clock tests."""

    def now(self) -> dt.datetime:
        raise NotImplementedError


class SystemClock(Clock):
    def now(self) -> dt.datetime:
        return dt.datetime.now(dt.timezone.utc)


@dataclass
class FakeClock(Clock):
    instant: dt.datetime

    def __post_init__(self) -> None:
        self.instant = require_utc(self.instant)

    def now(self) -> dt.datetime:
        return self.instant

    def advance(self, **kwargs: float) -> None:
        self.instant = self.instant + dt.timedelta(**kwargs)


def require_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None or value.utcoffset() != dt.timedelta(0):
        raise AutoRuntimeError("UTC_AWARE_INSTANT_REQUIRED")
    return value.astimezone(dt.timezone.utc)


def format_utc(value: dt.datetime) -> str:
    return require_utc(value).strftime(UTC_FORMAT)


def parse_utc(value: str) -> dt.datetime:
    try:
        parsed = dt.datetime.strptime(value, UTC_FORMAT)
    except (TypeError, ValueError) as exc:
        raise AutoRuntimeError("UTC_TIMESTAMP_INVALID") from exc
    return parsed.replace(tzinfo=dt.timezone.utc)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _encode_ulid(value: int) -> str:
    if value < 0 or value >= 1 << 128:
        raise AutoRuntimeError("ULID_VALUE_OUT_OF_RANGE")
    chars = ["0"] * 26
    for index in range(25, -1, -1):
        chars[index] = CROCKFORD[value & 31]
        value >>= 5
    if chars[0] not in "01234567":
        raise AutoRuntimeError("ULID_FIRST_CHARACTER_INVALID")
    return "".join(chars)


def new_uid(
    prefix: str,
    when: dt.datetime,
    entropy: Optional[bytes] = None,
) -> str:
    """Create a canonical typed ULID; injected entropy makes tests stable."""

    if not prefix.islower() or not prefix.isalpha() or not (2 <= len(prefix) <= 12):
        raise AutoRuntimeError("UID_PREFIX_INVALID")
    timestamp_ms = int(require_utc(when).timestamp() * 1000)
    if timestamp_ms < 0 or timestamp_ms >= 1 << 48:
        raise AutoRuntimeError("ULID_TIMESTAMP_OUT_OF_RANGE")
    random_part = entropy if entropy is not None else secrets.token_bytes(10)
    if len(random_part) != 10:
        raise AutoRuntimeError("ULID_ENTROPY_LENGTH_INVALID")
    return f"{prefix}_{_encode_ulid((timestamp_ms << 80) | int.from_bytes(random_part, 'big'))}"


def _ensure_regular_parent(path: Path) -> None:
    parent = path.parent
    try:
        info = os.lstat(str(parent))
    except OSError as exc:
        raise AutoRuntimeError("ATOMIC_PARENT_UNAVAILABLE") from exc
    if not stat.S_ISDIR(info.st_mode) or stat.S_ISLNK(info.st_mode):
        raise AutoRuntimeError("ATOMIC_PARENT_NOT_REAL_DIRECTORY")


def atomic_write_bytes(
    path: Path,
    payload: bytes,
    *,
    mode: int = 0o600,
    failpoint: Optional[Callable[[str], None]] = None,
) -> None:
    """Write temp+fsync+rename+directory-fsync without following a target link."""

    _ensure_regular_parent(path)
    try:
        existing = os.lstat(str(path))
    except FileNotFoundError:
        existing = None
    except OSError as exc:
        raise AutoRuntimeError("ATOMIC_TARGET_LSTAT_FAILED") from exc
    if existing is not None and (stat.S_ISLNK(existing.st_mode) or not stat.S_ISREG(existing.st_mode)):
        raise AutoRuntimeError("ATOMIC_TARGET_NOT_REGULAR")

    token = secrets.token_hex(12)
    temporary = path.parent / f".{path.name}.{token}.tmp"
    descriptor: Optional[int] = None
    try:
        descriptor = os.open(
            str(temporary),
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0),
            mode,
        )
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            if written <= 0:
                raise AutoRuntimeError("ATOMIC_WRITE_SHORT")
            view = view[written:]
        os.fsync(descriptor)
        if failpoint is not None:
            failpoint("AFTER_FILE_FSYNC")
        os.close(descriptor)
        descriptor = None
        os.replace(str(temporary), str(path))
        if failpoint is not None:
            failpoint("AFTER_RENAME")
        directory_fd = os.open(str(path.parent), os.O_RDONLY)
        try:
            os.fsync(directory_fd)
        finally:
            os.close(directory_fd)
        os.chmod(str(path), mode, follow_symlinks=False)
    except AutoRuntimeError:
        raise
    except CanonicalizationError as exc:
        raise AutoRuntimeError("STATE_FILE_JSON_INVALID") from exc
    except OSError as exc:
        raise AutoRuntimeError("ATOMIC_WRITE_FAILED") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(
    path: Path,
    value: Any,
    *,
    failpoint: Optional[Callable[[str], None]] = None,
) -> None:
    atomic_write_bytes(path, canonicalize_object(value), failpoint=failpoint)


def read_json(path: Path) -> Any:
    try:
        info = os.lstat(str(path))
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AutoRuntimeError("STATE_FILE_NOT_REGULAR")
        return parse_json_bytes(path.read_bytes())
    except AutoRuntimeError:
        raise
    except OSError as exc:
        raise AutoRuntimeError("STATE_FILE_READ_FAILED") from exc


def canonical_with_digest(value: dict, field: str) -> dict:
    """Return a copy with its exact top-level self-digest populated."""

    from CodexSkills.governance.tools.canonical_json import canonical_digest

    if field not in value:
        raise AutoRuntimeError("SELF_DIGEST_FIELD_MISSING")
    output = dict(value)
    output[field] = canonical_digest(output, f"/{field}")
    return output
