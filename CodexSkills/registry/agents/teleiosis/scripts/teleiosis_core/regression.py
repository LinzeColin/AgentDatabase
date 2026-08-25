from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict, Set

from .common import TeleiosisError, canonical_json_hash, require_regular_file

EXPECTED_COUNT = 8192
ENGINES = {"T", "S", "P", "A"}
SPLITS = {"development", "selection", "hidden_iid", "hidden_ood", "redteam", "regression"}
STATUSES = {"EXECUTED", "NOT_APPLICABLE_WITH_REASON", "NOT_RUN", "BLOCKED"}


def _record_checksum(record: Dict[str, Any]) -> str:
    payload = dict(record)
    payload.pop("checksum", None)
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def validate_corpus(path: Path, expected_count: int = EXPECTED_COUNT) -> Dict[str, Any]:
    require_regular_file(path)
    ids: Set[str] = set()
    counts_engine = {key: 0 for key in sorted(ENGINES)}
    counts_split = {key: 0 for key in sorted(SPLITS)}
    hard_gates = 0
    sha = hashlib.sha256()
    with path.open("rb") as raw:
        for line_number, line in enumerate(raw, 1):
            sha.update(line)
            try:
                record = json.loads(line.decode("utf-8"))
            except Exception as exc:
                raise TeleiosisError("REGRESSION_JSONL", "回归语料 JSONL 无法解析。", {"line": line_number, "reason": str(exc)})
            record_id = record.get("id")
            if not isinstance(record_id, str) or record_id in ids:
                raise TeleiosisError("REGRESSION_ID", "回归语料 ID 缺失或重复。", {"line": line_number, "id": record_id})
            ids.add(record_id)
            if record.get("engine") not in ENGINES or record.get("split") not in SPLITS or record.get("expected_status") not in STATUSES:
                raise TeleiosisError("REGRESSION_DOMAIN", "回归语料枚举值不合法。", {"line": line_number})
            if record.get("checksum") != _record_checksum(record):
                raise TeleiosisError("REGRESSION_CHECKSUM", "回归语料记录 checksum 不匹配。", {"line": line_number, "id": record_id})
            counts_engine[record["engine"]] += 1
            counts_split[record["split"]] += 1
            if record.get("hard_gate"):
                hard_gates += 1
    if len(ids) != expected_count:
        raise TeleiosisError("REGRESSION_COUNT", "回归语料数量不正确。", {"actual": len(ids), "expected": expected_count})
    if any(value == 0 for value in counts_engine.values()) or any(value == 0 for value in counts_split.values()):
        raise TeleiosisError("REGRESSION_COVERAGE", "回归语料未覆盖全部引擎或分区。")
    result = {
        "schema_version": "teleiosis.regression_corpus_validation.v5",
        "status": "PASS",
        "records": len(ids),
        "engines": counts_engine,
        "splits": counts_split,
        "hard_gate_cases": hard_gates,
        "sha256": sha.hexdigest(),
    }
    result["validation_hash"] = canonical_json_hash(result)
    return result
