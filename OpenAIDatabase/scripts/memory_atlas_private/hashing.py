from __future__ import annotations

import hashlib
from pathlib import Path
from typing import BinaryIO


CHUNK_SIZE = 8 * 1024 * 1024


def sha256_stream(stream: BinaryIO) -> str:
    digest = hashlib.sha256()
    while True:
        chunk = stream.read(CHUNK_SIZE)
        if not chunk:
            return digest.hexdigest()
        digest.update(chunk)


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        return sha256_stream(handle)


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def stable_id(*parts: str, prefix: str = "id") -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return f"{prefix}_{hashlib.sha256(payload).hexdigest()[:24]}"
