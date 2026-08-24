from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, List, Mapping, Sequence


class MarketLabError(RuntimeError):
    """Base error for deterministic, user-actionable failures."""


class ValidationError(MarketLabError):
    """Raised when a machine contract is invalid."""


JSONDict = Dict[str, Any]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def text_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def stable_int(*parts: object, modulo: int = 2**63 - 1) -> int:
    payload = "\x1f".join(str(part) for part in parts)
    return int(hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16], 16) % modulo


def stable_id(prefix: str, value: Any, length: int = 16) -> str:
    return f"{prefix}-{object_sha256(value)[:length]}"


def read_json(path: Path) -> Any:
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError as exc:
        raise ValidationError(f"文件不存在: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValidationError(f"JSON 无效: {path}: {exc}") from exc


def atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False, prefix=f".{path.name}."
    ) as handle:
        handle.write(text)
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)


def write_json(path: Path, value: Any) -> None:
    atomic_write_text(path, json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n")


def iter_jsonl(path: Path) -> Iterator[JSONDict]:
    try:
        with path.open("r", encoding="utf-8") as handle:
            for line_number, raw_line in enumerate(handle, 1):
                line = raw_line.strip()
                if not line:
                    continue
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValidationError(f"JSONL 无效: {path}:{line_number}: {exc}") from exc
                if not isinstance(item, dict):
                    raise ValidationError(f"JSONL 每行必须是对象: {path}:{line_number}")
                item["_source_line"] = line_number
                yield item
    except FileNotFoundError as exc:
        raise ValidationError(f"文件不存在: {path}") from exc


def write_jsonl(path: Path, rows: Iterable[Mapping[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with tempfile.NamedTemporaryFile(
        "w", encoding="utf-8", dir=str(path.parent), delete=False, prefix=f".{path.name}."
    ) as handle:
        for row in rows:
            clean_row = {key: value for key, value in row.items() if key != "_source_line"}
            handle.write(json.dumps(clean_row, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
        handle.flush()
        os.fsync(handle.fileno())
        temporary = Path(handle.name)
    temporary.replace(path)
    return count


def ensure_safe_relative_path(raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute() or ".." in candidate.parts:
        raise ValidationError(f"拒绝非安全相对路径: {raw_path}")
    if any(part in {"", "."} for part in candidate.parts):
        raise ValidationError(f"路径包含空段或当前目录段: {raw_path}")
    return candidate


def resolve_within(root: Path, raw_path: str) -> Path:
    relative = ensure_safe_relative_path(raw_path)
    root_resolved = root.resolve()
    target = (root_resolved / relative).resolve()
    if target != root_resolved and root_resolved not in target.parents:
        raise ValidationError(f"路径越界: {raw_path}")
    return target


def require_keys(value: Mapping[str, Any], keys: Sequence[str], location: str) -> List[str]:
    return [f"{location} 缺少字段 {key}" for key in keys if key not in value]


def ensure_type(value: Any, expected: type, location: str, errors: List[str]) -> None:
    if not isinstance(value, expected):
        errors.append(f"{location} 必须是 {expected.__name__}，实际为 {type(value).__name__}")


def as_number(value: Any, location: str, errors: List[str], minimum: float | None = None) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        errors.append(f"{location} 必须是数字")
        return None
    numeric = float(value)
    if minimum is not None and numeric < minimum:
        errors.append(f"{location} 必须 >= {minimum}")
    return numeric


def slugify(value: str, maximum: int = 64) -> str:
    normalized = re.sub(r"[^a-z0-9]+", "-", value.strip().lower()).strip("-")
    normalized = re.sub(r"-{2,}", "-", normalized)
    if not normalized:
        raise ValidationError("名称必须至少包含一个字母或数字")
    if len(normalized) > maximum:
        raise ValidationError(f"名称过长: {len(normalized)} > {maximum}")
    return normalized


def percentage_change(current: float | None, baseline: float | None) -> float | None:
    if current is None or baseline is None or baseline == 0:
        return None
    return (current - baseline) / abs(baseline)


def strip_internal_fields(value: Mapping[str, Any]) -> JSONDict:
    return {key: item for key, item in value.items() if not key.startswith("_")}
