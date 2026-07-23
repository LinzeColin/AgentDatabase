"""Fail-closed secret scanning and public serialization gates."""

from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Tuple

from CodexSkills.registry.auto.tools.validate_auto import AutoContract, validate_auto_instance
from CodexSkills.governance.tools.canonical_json import parse_json_bytes
from CodexSkills.governance.tools.validate_mechanism import scan_public_value

from .core import AutoRuntimeError


SECRET_PATTERNS = (
    ("OPENAI_SECRET", re.compile(rb"sk-[A-Za-z0-9]{20,}")),
    ("ANTHROPIC_SECRET", re.compile(rb"sk-ant-[A-Za-z0-9_-]{20,}")),
    (
        "GITHUB_TOKEN",
        re.compile(rb"(?:\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{20,}|\bgithub_pat_[A-Za-z0-9_]{20,})"),
    ),
    ("AWS_ACCESS_KEY", re.compile(rb"\bAKIA[0-9A-Z]{16}\b")),
    ("SLACK_TOKEN", re.compile(rb"\bxox[baprs]-[A-Za-z0-9-]{10,}")),
    ("PRIVATE_KEY", re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----")),
    (
        "JWT",
        re.compile(rb"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),
    ),
    ("GOOGLE_API_KEY", re.compile(rb"\bAIza[A-Za-z0-9_-]{35}\b")),
)


@dataclass(frozen=True)
class SecretHit:
    path_ref: str
    reason_code: str


class SecretScanner:
    def __init__(self, chunk_bytes: int = 1024 * 1024, overlap_bytes: int = 4096) -> None:
        if chunk_bytes <= 0 or overlap_bytes <= 0 or overlap_bytes > chunk_bytes:
            raise AutoRuntimeError("SECRET_SCAN_CHUNK_CONFIG_INVALID")
        self.chunk_bytes = chunk_bytes
        self.overlap_bytes = overlap_bytes

    def scan_file(self, path: Path, path_ref: str) -> Tuple[SecretHit, ...]:
        try:
            info = os.lstat(str(path))
        except OSError as exc:
            raise AutoRuntimeError("SECRET_SCAN_STAT_FAILED") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
            raise AutoRuntimeError("SECRET_SCAN_REGULAR_FILE_REQUIRED")
        found = set()
        descriptor = None
        try:
            descriptor = os.open(str(path), os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
            overlap = b""
            while True:
                block = os.read(descriptor, self.chunk_bytes)
                if not block:
                    break
                material = overlap + block
                for reason, pattern in SECRET_PATTERNS:
                    if pattern.search(material):
                        found.add(reason)
                overlap = material[-self.overlap_bytes :]
        except PermissionError as exc:
            raise AutoRuntimeError("SECRET_SCAN_PERMISSION_ERROR") from exc
        except OSError as exc:
            raise AutoRuntimeError("SECRET_SCAN_READ_FAILED") from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
        return tuple(SecretHit(path_ref, reason) for reason in sorted(found))


def validate_public_serialization(
    raw: bytes,
    contract: AutoContract,
    schema_id: str,
    expected_bundle_digest: str,
) -> Mapping[str, object]:
    """Reparse serialized bytes, validate exact schema, then rescan values."""

    try:
        instance = parse_json_bytes(raw)
    except Exception as exc:
        raise AutoRuntimeError("PUBLIC_SERIALIZATION_PARSE_FAILED") from exc
    if not isinstance(instance, dict):
        raise AutoRuntimeError("PUBLIC_SERIALIZATION_ROOT_INVALID")
    try:
        validate_auto_instance(
            contract,
            instance,
            schema_id,
            expected_bundle_digest=expected_bundle_digest,
        )
        scan_public_value(instance, contract.shared.policies)
    except Exception as exc:
        raise AutoRuntimeError(f"PUBLIC_SERIALIZATION_GATE_FAILED:{exc}") from exc
    return instance
