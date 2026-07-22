#!/usr/bin/env python3
"""Strict I-JSON parsing and RFC 8785 canonicalization.

The canonicalizer is a pinned, provenance-checked author implementation. This
wrapper owns all input rejection, JSON Pointer exclusion, and digest behavior.
"""

from __future__ import annotations

import argparse
import copy
import functools
import hashlib
import importlib
import json
import math
import sys
import threading
from pathlib import Path
from typing import Any, Iterable, List, MutableMapping, MutableSequence, Optional


class CanonicalizationError(ValueError):
    """Input cannot be represented by the frozen canonicalization contract."""


class DuplicateKeyError(CanonicalizationError):
    """A JSON object contained the same property name more than once."""


_GOVERNANCE_DIR = Path(__file__).resolve().parents[1]
_VENDOR_DIR = _GOVERNANCE_DIR / "vendor" / "json_canonicalization"
_VENDOR_SRC = _VENDOR_DIR / "python3" / "src"
_VENDOR_MODULE_DIR = _VENDOR_SRC / "org" / "webpki" / "json"
_EXPECTED_VENDOR_SHA256 = {
    "Canonicalize.py": "644508c81fa4afa50e8f6c7626a8cb6ddbd9515b39128c55484222ad336fad35",
    "NumberToJson.py": "b8f78dab5bd7cf32cc620df39db18c8a55c777fa8acb69294d1a4d6702ee7e2a",
    "LICENSE": "cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30",
    "LICENSE.PSF": "af99833f38f9849acc41e2ca1de50a3cb266e712713efa6f377bae4befb16482",
}
_VENDOR_IMPORT_LOCK = threading.Lock()


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


@functools.lru_cache(maxsize=1)
def verify_vendor() -> None:
    """Verify every vendored byte before importing executable code."""
    for name, expected in _EXPECTED_VENDOR_SHA256.items():
        path = _VENDOR_MODULE_DIR / name
        if not path.is_file():
            raise CanonicalizationError(f"VENDOR_FILE_MISSING:{name}")
        actual = _sha256_bytes(path.read_bytes())
        if actual != expected:
            raise CanonicalizationError(
                f"VENDOR_DIGEST_MISMATCH:{name}:{expected}:{actual}"
            )


@functools.lru_cache(maxsize=1)
def _vendor_canonicalize():
    verify_vendor()
    with _VENDOR_IMPORT_LOCK:
        preserved = {
            name: module
            for name, module in tuple(sys.modules.items())
            if name == "org" or name.startswith("org.")
        }
        for name in preserved:
            del sys.modules[name]
        sys.path.insert(0, str(_VENDOR_SRC))
        try:
            module = importlib.import_module("org.webpki.json.Canonicalize")
            number_module = sys.modules.get("org.webpki.json.NumberToJson")
            module_path = Path(module.__file__).resolve()
            number_path = (
                Path(number_module.__file__).resolve()
                if number_module is not None and getattr(number_module, "__file__", None)
                else None
            )
            if module_path != (_VENDOR_MODULE_DIR / "Canonicalize.py").resolve():
                raise CanonicalizationError(f"VENDOR_IMPORT_REBOUND:{module_path}")
            if number_path != (_VENDOR_MODULE_DIR / "NumberToJson.py").resolve():
                raise CanonicalizationError(f"VENDOR_IMPORT_REBOUND:{number_path}")
            canonicalize = module.canonicalize
        finally:
            try:
                sys.path.remove(str(_VENDOR_SRC))
            except ValueError:
                pass
            for name in tuple(sys.modules):
                if name == "org" or name.startswith("org."):
                    del sys.modules[name]
            sys.modules.update(preserved)
    return canonicalize


def _reject_constant(value: str) -> None:
    raise CanonicalizationError(f"NON_FINITE_NUMBER:{value}")


def _object_pairs(pairs: Iterable[Any]) -> MutableMapping[str, Any]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise DuplicateKeyError(f"DUPLICATE_KEY:{key}")
        result[key] = value
    return result


def _validate_ijson(value: Any, location: str = "$") -> None:
    if value is None or isinstance(value, bool):
        return
    if isinstance(value, str):
        for char in value:
            if 0xD800 <= ord(char) <= 0xDFFF:
                raise CanonicalizationError(f"LONE_SURROGATE:{location}")
        return
    if isinstance(value, int):
        converted = float(value)
        if not math.isfinite(converted) or int(converted) != value:
            raise CanonicalizationError(f"NUMBER_NOT_IEEE754_EXACT:{location}")
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CanonicalizationError(f"NON_FINITE_NUMBER:{location}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_ijson(item, f"{location}[{index}]")
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(f"NON_STRING_KEY:{location}")
            _validate_ijson(key, f"{location}.<key>")
            _validate_ijson(item, f"{location}.{key}")
        return
    raise CanonicalizationError(f"NON_JSON_TYPE:{location}:{type(value).__name__}")


def parse_json_bytes(raw: bytes) -> Any:
    """Parse raw UTF-8 JSON without losing evidence needed for rejection."""
    if not isinstance(raw, bytes):
        raise TypeError("raw input must be bytes")
    if raw.startswith(b"\xef\xbb\xbf"):
        raise CanonicalizationError("UTF8_BOM_FORBIDDEN")
    try:
        text = raw.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        raise CanonicalizationError(f"INVALID_UTF8:{exc.start}") from exc
    try:
        value = json.loads(
            text,
            object_pairs_hook=_object_pairs,
            parse_constant=_reject_constant,
        )
    except DuplicateKeyError:
        raise
    except CanonicalizationError:
        raise
    except json.JSONDecodeError as exc:
        raise CanonicalizationError(
            f"INVALID_JSON:{exc.lineno}:{exc.colno}:{exc.msg}"
        ) from exc
    _validate_ijson(value)
    return value


def canonicalize_object(value: Any) -> bytes:
    _validate_ijson(value)
    try:
        result = _vendor_canonicalize()(value)
    except (TypeError, ValueError, UnicodeError) as exc:
        raise CanonicalizationError(f"JCS_SERIALIZATION_FAILED:{exc}") from exc
    if not isinstance(result, bytes):
        raise CanonicalizationError("JCS_NON_BYTES_OUTPUT")
    if result.startswith(b"\xef\xbb\xbf") or result.endswith(b"\n"):
        raise CanonicalizationError("JCS_OUTPUT_FRAMING_INVALID")
    return result


def canonicalize_bytes(raw: bytes) -> bytes:
    return canonicalize_object(parse_json_bytes(raw))


def _decode_pointer_token(token: str) -> str:
    output: List[str] = []
    index = 0
    while index < len(token):
        if token[index] != "~":
            output.append(token[index])
            index += 1
            continue
        if index + 1 >= len(token) or token[index + 1] not in "01":
            raise CanonicalizationError(f"INVALID_JSON_POINTER_ESCAPE:{token}")
        output.append("~" if token[index + 1] == "0" else "/")
        index += 2
    return "".join(output)


def without_json_pointer(value: Any, pointer: str) -> Any:
    """Deep-copy value and remove exactly one RFC 6901 pointer."""
    if not pointer or not pointer.startswith("/"):
        raise CanonicalizationError(f"INVALID_SELF_POINTER:{pointer}")
    tokens = [_decode_pointer_token(token) for token in pointer[1:].split("/")]
    cloned = copy.deepcopy(value)
    parent = cloned
    for token in tokens[:-1]:
        if isinstance(parent, dict) and token in parent:
            parent = parent[token]
        elif isinstance(parent, list) and token.isdigit() and int(token) < len(parent):
            parent = parent[int(token)]
        else:
            raise CanonicalizationError(f"SELF_POINTER_NOT_FOUND:{pointer}")
    final = tokens[-1]
    if isinstance(parent, dict) and final in parent:
        del parent[final]
    elif isinstance(parent, list) and final.isdigit() and int(final) < len(parent):
        del parent[int(final)]
    else:
        raise CanonicalizationError(f"SELF_POINTER_NOT_FOUND:{pointer}")
    return cloned


def canonical_digest(value: Any, self_pointer: Optional[str] = None) -> str:
    material = without_json_pointer(value, self_pointer) if self_pointer else value
    return _sha256_bytes(canonicalize_object(material))


def verify_self_digest(value: Any, pointer: str) -> bool:
    tokens = [_decode_pointer_token(token) for token in pointer[1:].split("/")]
    current = value
    for token in tokens:
        if isinstance(current, dict) and token in current:
            current = current[token]
        elif isinstance(current, list) and token.isdigit() and int(token) < len(current):
            current = current[int(token)]
        else:
            raise CanonicalizationError(f"SELF_POINTER_NOT_FOUND:{pointer}")
    if not isinstance(current, str):
        raise CanonicalizationError(f"SELF_DIGEST_NOT_STRING:{pointer}")
    return current == canonical_digest(value, pointer)


def _main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    for command in ("canonicalize", "digest"):
        child = subparsers.add_parser(command)
        child.add_argument("input", type=Path)
        if command == "digest":
            child.add_argument("--exclude-pointer")
    subparsers.add_parser("verify-vendor")
    args = parser.parse_args(argv)
    if args.command == "verify-vendor":
        verify_vendor()
        print("VENDOR_OK")
        return 0
    raw = args.input.read_bytes()
    if args.command == "canonicalize":
        sys.stdout.buffer.write(canonicalize_bytes(raw))
        return 0
    value = parse_json_bytes(raw)
    print(canonical_digest(value, args.exclude_pointer))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except CanonicalizationError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
