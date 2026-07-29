from __future__ import annotations
import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any, Dict

class ProductRealityError(RuntimeError):
    pass

class ProductValidationError(ProductRealityError):
    pass

def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))

def object_sha256(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()

def is_sha256(value: Any) -> bool:
    if not isinstance(value, str) or len(value) != 64:
        return False
    try:
        int(value, 16)
        return value == value.lower()
    except ValueError:
        return False

def utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def read_json(path: Path) -> Dict[str, Any]:
    try:
        value=json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ProductRealityError(f"缺少 JSON: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ProductRealityError(f"JSON 无效: {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ProductRealityError(f"JSON 根节点必须为 object: {path}")
    return value

def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd,tmp=tempfile.mkstemp(prefix=f".{path.name}.",dir=str(path.parent))
    try:
        with os.fdopen(fd,"w",encoding="utf-8") as handle:
            json.dump(value,handle,ensure_ascii=False,indent=2,sort_keys=True)
            handle.write("\n"); handle.flush(); os.fsync(handle.fileno())
        os.replace(tmp,path)
    finally:
        try: os.unlink(tmp)
        except FileNotFoundError: pass
