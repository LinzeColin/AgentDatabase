"""Minimal TOML reader used only when the runtime lacks Python 3.11's tomllib.

The repository manifests use a deliberately small TOML subset: tables, scalar
strings/booleans/integers, and arrays of those values.  Keeping the fallback
here avoids adding a network-installed dependency just to run the test suite
on the supported local Python 3.9 runtime.
"""

from __future__ import annotations

import ast
import json
from typing import Any


class TOMLDecodeError(ValueError):
    """Compatibility error with a tomllib-like name."""


def _without_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, character in enumerate(line):
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"\"", "'"}:
            quote = character
        elif character == "#":
            return line[:index]
    return line


def _array_complete(value: str) -> bool:
    depth = 0
    quote: str | None = None
    escaped = False
    for character in value:
        if quote:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == quote:
                quote = None
        elif character in {"\"", "'"}:
            quote = character
        elif character == "[":
            depth += 1
        elif character == "]":
            depth -= 1
            if depth < 0:
                raise TOMLDecodeError("unexpected closing array bracket")
    return depth == 0 and quote is None


def _parse_value(value: str) -> Any:
    value = value.strip()
    if value == "true":
        return True
    if value == "false":
        return False
    if value.startswith("["):
        try:
            return json.loads(value)
        except json.JSONDecodeError as exc:
            raise TOMLDecodeError("invalid array value") from exc
    if value.startswith(("\"", "'")):
        try:
            return ast.literal_eval(value)
        except (SyntaxError, ValueError) as exc:
            raise TOMLDecodeError("invalid string value") from exc
    try:
        return int(value)
    except ValueError as exc:
        raise TOMLDecodeError(f"unsupported TOML value: {value}") from exc


def loads(source: str) -> dict[str, Any]:
    """Parse the manifest subset used by the repository's TOML fixtures."""

    payload: dict[str, Any] = {}
    current: dict[str, Any] = payload
    pending_key: str | None = None
    pending_value: list[str] = []

    def assign(key: str, value: str) -> None:
        if not key or key in current:
            raise TOMLDecodeError(f"invalid or duplicate key: {key}")
        current[key] = _parse_value(value)

    for raw_line in source.splitlines():
        line = _without_comment(raw_line).strip()
        if not line:
            continue
        if pending_key is not None:
            pending_value.append(line)
            joined = " ".join(pending_value)
            if _array_complete(joined):
                assign(pending_key, joined)
                pending_key = None
                pending_value = []
            continue
        if line.startswith("[") and line.endswith("]"):
            table_path = [part.strip() for part in line[1:-1].split(".")]
            if not table_path or any(not part for part in table_path):
                raise TOMLDecodeError("invalid table header")
            current = payload
            for part in table_path:
                existing = current.get(part)
                if existing is None:
                    existing = {}
                    current[part] = existing
                if not isinstance(existing, dict):
                    raise TOMLDecodeError("table conflicts with scalar")
                current = existing
            continue
        if "=" not in line:
            raise TOMLDecodeError(f"invalid assignment: {line}")
        key, value = (part.strip() for part in line.split("=", 1))
        if value.startswith("[") and not _array_complete(value):
            pending_key = key
            pending_value = [value]
            continue
        assign(key, value)

    if pending_key is not None:
        raise TOMLDecodeError("unterminated array")
    return payload


def load(file: Any) -> dict[str, Any]:
    """Small convenience wrapper matching tomllib.load for test callers."""

    source = file.read()
    if isinstance(source, bytes):
        source = source.decode("utf-8")
    return loads(source)
