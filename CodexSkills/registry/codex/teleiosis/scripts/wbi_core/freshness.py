from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List

from .io import canonical_json, sha256_bytes, sha256_file, utc_now, write_json

REQUIRED_CATEGORIES = {"models-runtimes", "methods-architectures", "evaluation", "standards-security", "competitors"}


def _parse_date(value: str) -> dt.datetime:
    text = value.strip().replace("Z", "+00:00")
    parsed = dt.datetime.fromisoformat(text)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def validate_source_record(record: Dict[str, Any], valid_as_of: dt.datetime) -> List[str]:
    errors: List[str] = []
    for key in ("source_id", "category", "title", "url", "source_type", "authority", "queried_at", "claim", "status"):
        if not record.get(key):
            errors.append("missing %s" % key)
    if record.get("category") not in REQUIRED_CATEGORIES:
        errors.append("invalid category")
    if record.get("source_type") not in {"official-doc", "source-repository", "research-paper", "standard", "product-artifact", "authoritative-release"}:
        errors.append("invalid source_type")
    if record.get("authority") not in {"primary", "official", "authoritative-secondary"}:
        errors.append("invalid authority")
    if record.get("status") not in {"VERIFIED", "PARTIAL", "BLOCKED", "UNKNOWN"}:
        errors.append("invalid status")
    try:
        queried = _parse_date(str(record.get("queried_at", "")))
        if queried > valid_as_of + dt.timedelta(days=1):
            errors.append("queried_at is after valid_as_of")
    except Exception:
        errors.append("invalid queried_at")
    if not str(record.get("url", "")).startswith("https://"):
        errors.append("source URL must be HTTPS")
    if record.get("status") != "VERIFIED" and not record.get("unknowns"):
        errors.append("non-verified source must state unknowns")
    return errors


def build_freshness_scan(records_path: Path, output_dir: Path, valid_as_of: str, validity_days: int = 30) -> Dict[str, Any]:
    valid_dt = _parse_date(valid_as_of)
    rows: List[Dict[str, Any]] = []
    errors: List[str] = []
    seen = set()
    for number, raw in enumerate(records_path.read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip():
            continue
        try:
            row = json.loads(raw)
        except Exception as exc:
            errors.append("line %d invalid JSON: %s" % (number, exc))
            continue
        identity = row.get("source_id")
        if identity in seen:
            errors.append("duplicate source_id: %s" % identity)
        seen.add(identity)
        row_errors = validate_source_record(row, valid_dt)
        if row_errors:
            errors.extend(["%s: %s" % (identity or "line-%d" % number, item) for item in row_errors])
        rows.append(row)
    categories = {row.get("category") for row in rows if row.get("status") in {"VERIFIED", "PARTIAL"}}
    missing = sorted(REQUIRED_CATEGORIES - categories)
    if missing:
        errors.append("missing freshness categories: %s" % missing)
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized = output_dir / "freshness-sources.jsonl"
    with normalized.open("w", encoding="utf-8", newline="\n") as handle:
        for row in sorted(rows, key=lambda item: str(item.get("source_id"))):
            handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")
    expires_at = valid_dt + dt.timedelta(days=validity_days)
    scan = {
        "schema_version": "1.0", "status": "PASS" if not errors else "BLOCKED", "valid_as_of": valid_dt.isoformat(),
        "validity_days": validity_days, "expires_at": expires_at.isoformat(), "source_count": len(rows),
        "categories_observed": sorted(category for category in categories if category), "required_categories": sorted(REQUIRED_CATEGORIES),
        "source_dataset": normalized.name, "source_dataset_sha256": sha256_file(normalized),
        "unknowns": [row.get("unknowns") for row in rows if row.get("unknowns")], "errors": errors,
        "reheat_triggers": [
            "validity window expired", "major model/runtime release", "standard or dependency deprecation",
            "new peer wins protected task", "real-task regression", "security advisory", "Genesis amendment",
        ],
        "generated_at": utc_now(),
    }
    scan["scan_sha256"] = sha256_bytes(canonical_json(scan))
    write_json(output_dir / "freshness-scan.json", scan)
    return scan


def reheat_status(scan_path: Path, now: str = "") -> Dict[str, Any]:
    scan = json.loads(scan_path.read_text(encoding="utf-8"))
    current = _parse_date(now) if now else dt.datetime.now(dt.timezone.utc)
    expiry = _parse_date(str(scan["expires_at"]))
    required = current > expiry or scan.get("status") != "PASS"
    return {
        "status": "REHEAT_REQUIRED" if required else "CURRENT",
        "checked_at": current.isoformat(), "valid_as_of": scan.get("valid_as_of"), "expires_at": scan.get("expires_at"),
        "reasons": (["freshness validity expired"] if current > expiry else []) + (["freshness scan did not pass"] if scan.get("status") != "PASS" else []),
    }
