from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Any, Dict, Iterable, Iterator, Mapping, MutableMapping, Sequence, Tuple

from .common import ValidationError, strip_internal_fields, write_jsonl
from .specs import assert_valid, validate_feedback

SENSITIVE_KEYS = {
    "raw_prompt",
    "raw_output",
    "file_content",
    "attachment_content",
    "secret",
    "password",
    "api_key",
    "access_token",
    "refresh_token",
    "authorization",
    "credential",
    "private_key",
    "session_cookie",
}
HASHED_ID_KEYS = {"user_id", "account_id", "email", "device_id", "session_id", "external_user_id"}

EMAIL_PATTERN = re.compile(r"(?<![\w.+-])([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})(?![\w.-])")
SECRET_PATTERNS = (
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}\b"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{10,}=*"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----.*?-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----", re.DOTALL),
)
HOME_PATH_PATTERN = re.compile(r"(?:(?:/Users|/home)/[A-Za-z0-9._-]+|[A-Za-z]:\\Users\\[A-Za-z0-9._-]+)")


def _hash_identifier(value: str, salt: str) -> str:
    digest = hashlib.sha256(f"{salt}\x1f{value}".encode("utf-8")).hexdigest()
    return f"anon-{digest[:20]}"


def _redact_text(value: str, report: MutableMapping[str, int]) -> str:
    def replace_email(match: re.Match[str]) -> str:
        report["emails_redacted"] = report.get("emails_redacted", 0) + 1
        return "[REDACTED_EMAIL]"

    redacted = EMAIL_PATTERN.sub(replace_email, value)
    for pattern in SECRET_PATTERNS:
        redacted, count = pattern.subn("[REDACTED_SECRET]", redacted)
        report["secrets_redacted"] = report.get("secrets_redacted", 0) + count
    redacted, count = HOME_PATH_PATTERN.subn("[REDACTED_HOME]", redacted)
    report["paths_redacted"] = report.get("paths_redacted", 0) + count
    return redacted


def anonymize_value(value: Any, salt: str, report: MutableMapping[str, int], key: str | None = None) -> Any:
    normalized_key = (key or "").lower()
    if normalized_key in SENSITIVE_KEYS:
        report["sensitive_fields_removed"] = report.get("sensitive_fields_removed", 0) + 1
        return "[REDACTED_FIELD]"
    if normalized_key in HASHED_ID_KEYS and value is not None:
        report["identifiers_hashed"] = report.get("identifiers_hashed", 0) + 1
        return _hash_identifier(str(value), salt)
    if isinstance(value, str):
        return _redact_text(value, report)
    if isinstance(value, list):
        return [anonymize_value(item, salt, report) for item in value]
    if isinstance(value, dict):
        return {item_key: anonymize_value(item_value, salt, report, item_key) for item_key, item_value in value.items()}
    return value


def anonymize_feedback_rows(
    rows: Iterable[Mapping[str, Any]],
    salt: str,
    strict_validation: bool = True,
    arm_ids: Sequence[str] | None = None,
) -> Tuple[Iterator[Dict[str, Any]], Dict[str, int]]:
    if not salt or len(salt) < 16:
        raise ValidationError("匿名化 salt 至少需要 16 个字符，并应来自环境变量或受控文件")
    report: Dict[str, int] = {
        "rows_processed": 0,
        "sensitive_fields_removed": 0,
        "identifiers_hashed": 0,
        "emails_redacted": 0,
        "secrets_redacted": 0,
        "paths_redacted": 0,
    }

    def generator() -> Iterator[Dict[str, Any]]:
        for raw in rows:
            clean = strip_internal_fields(raw)
            if strict_validation:
                assert_valid(validate_feedback(clean, arm_ids), f"反馈 {clean.get('event_id', '<unknown>')}")
            anonymized = anonymize_value(clean, salt, report)
            report["rows_processed"] += 1
            yield anonymized

    return generator(), report


def anonymize_feedback_file(
    input_rows: Iterable[Mapping[str, Any]],
    output_path: Path,
    salt: str,
    arm_ids: Sequence[str] | None = None,
) -> Dict[str, int]:
    rows, report = anonymize_feedback_rows(input_rows, salt, arm_ids=arm_ids)
    write_jsonl(output_path, rows)
    return report
