#!/usr/bin/env python3
"""Privacy guards for raw private import and redacted derived outputs."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from memory_atlas_cli.credential_exclusion import (
    BLOCKED_ACCOUNT_CONTROL_CATEGORIES,
    CREDENTIAL_SCHEMA_VERSION,
    CredentialExclusionError,
    POLICY_ID,
    TASK_ID,
    forbidden_public_raw_path_match,
    load_credential_exclusion_contract,
)


DERIVED_IMPORT_DIR = Path("data/derived/privacy_imports")
PRIVACY_AUDIT_LOG = Path("data/run_logs/privacy/privacy_imports.jsonl")
PRIVATE_ROOTS = (Path("data/raw"), Path("data/raw_encrypted"), Path("data/private_imports"))
REQUIRED_GITIGNORE_PATTERNS = ("*.zip", "data/raw/", "data/raw_encrypted/", "data/private_imports/")
CODEX_PUBLIC_RAW_ARCHIVE_MANIFEST_SCHEMA = (
    "memory_atlas.codex_public_raw_archive_manifest.v1_2_1_s07_p1_t2"
)
SECRET_PATTERNS = (
    ("openai_api_key", re.compile(r"\bsk-[A-Za-z0-9][A-Za-z0-9_-]{10,}\b")),
    ("github_token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("slack_token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b")),
    ("aws_access_key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
)
CREDENTIAL_PATTERNS = (
    ("api_keys", SECRET_PATTERNS[0][1]),
    ("api_keys", SECRET_PATTERNS[1][1]),
    ("api_keys", SECRET_PATTERNS[2][1]),
    ("api_keys", SECRET_PATTERNS[3][1]),
    (
        "api_keys",
        re.compile(r"\b(?:api[_-]?key|secret[_-]?key|client[_-]?secret)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:;-]{7,}", re.I),
    ),
    (
        "cookies",
        re.compile(
            r"\b(?:cookie|set-cookie)\b\s*[:=]\s*['\"]?"
            r"[A-Za-z0-9!#$%&'*+.^_`|~-]{1,128}=[^;,'\"\s][^,'\"\n]{6,}",
            re.I,
        ),
    ),
    (
        "session_tokens",
        re.compile(r"\b(?:session[_-]?token|sessionid|auth[_-]?token|csrf[_-]?token)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,}", re.I),
    ),
    (
        "passwords",
        re.compile(
            r"\b(?:password|passwd)\b\s*[:=]\s*"
            r"(?:\"[^\"\n]{8,}\"|'[^'\n]{8,}'|[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,})",
            re.I,
        ),
    ),
    (
        "passwords",
        re.compile(
            r"(?i:\bpwd\b)\s*[:=]\s*"
            r"(?:\"(?=[^\"\n]{8,}\")(?=[^\"\n]*[A-Z0-9])[^\"\n]+\"|"
            r"'(?=[^'\n]{8,}')(?=[^'\n]*[A-Z0-9])[^'\n]+'|"
            r"(?=[A-Za-z0-9._~+/=@:-]{8,}\b)(?=[A-Za-z0-9._~+/=@:-]*[A-Z0-9])"
            r"[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,})"
        ),
    ),
    (
        "passwords",
        re.compile(
            r"[\u4e00-\u9fff]{0,8}密码\s*[：:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{7,}",
            re.I,
        ),
    ),
    (
        "passwords",
        re.compile(
            r"\bsession\b.{0,80}密码\s*(?:是|为|[：:=])\s*['\"]?[0-9]{3}(?![0-9])",
            re.I,
        ),
    ),
    (
        "private_keys",
        re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----\s*[A-Za-z0-9+/=\r\n]{16,}\s*-----END [A-Z ]*PRIVATE KEY-----", re.S),
    ),
    (
        "oauth_tokens",
        re.compile(r"\b(?:access[_-]?token|refresh[_-]?token|oauth[_-]?token|id[_-]?token)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:;-]{7,}", re.I),
    ),
    ("oauth_tokens", re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]{16,}\b", re.I)),
    (
        "browser_credential_store",
        re.compile(r"\b(?:browser[_-]?credential[_-]?store|login[_-]?data|keychain)\b\s*[:=]\s*['\"]?[A-Za-z0-9][^'\"\n]{7,}", re.I),
    ),
    (
        "recovery_codes",
        re.compile(
            r"\b(?:recovery|backup)[_-]?(?:code|codes)\b\s*[:=]\s*['\"]?[A-Za-z0-9][A-Za-z0-9._~+/=@:-]{5,}",
            re.I,
        ),
    ),
)
_CREDENTIAL_TRIGGER_RE = re.compile(
    r"sk-|gh[pousr]_|xox[baprs]-|AKIA|"
    r"api[_-]?key|secret[_-]?key|client[_-]?secret|"
    r"set-cookie|\bcookie\b|session[_-]?token|sessionid|auth[_-]?token|csrf[_-]?token|"
    r"\bpassword\b|\bpasswd\b|\bpwd\b|-----BEGIN [A-Z ]*PRIVATE KEY-----|"
    r"access[_-]?token|refresh[_-]?token|oauth[_-]?token|id[_-]?token|\bBearer\s+|"
    r"browser[_-]?credential[_-]?store|login[_-]?data|\bkeychain\b",
    re.I,
)
_SAFE_CREDENTIAL_PLACEHOLDERS = {
    "example",
    "not-configured",
    "not configured",
    "not_configured",
    "null",
    "none",
    "redacted",
    "redacted_credential",
    "redacted_secret",
    "your-api-key",
    "your-token",
    "your_api_key",
    "your_token",
}
LOCAL_ABSOLUTE_PATH_RE = re.compile(r"(?:[A-Za-z]:[\\/][^\s\"']+|/(?:Users|home)/[^\s\"']+)")
_COOKIE_FIELD_VALUE_RE = re.compile(r"\A\s*[A-Za-z0-9!#$%&'*+.^_`|~-]{1,128}=")
_CREDENTIAL_FIELD_CATEGORIES = {
    "api_key": "api_keys",
    "api_keys": "api_keys",
    "apikey": "api_keys",
    "secret_key": "api_keys",
    "client_secret": "api_keys",
    "session_token": "session_tokens",
    "sessionid": "session_tokens",
    "auth_token": "session_tokens",
    "csrf_token": "session_tokens",
    "password": "passwords",
    "passwd": "passwords",
    "private_key": "private_keys",
    "privatekey": "private_keys",
    "rsa_private_key": "private_keys",
    "ec_private_key": "private_keys",
    "openssh_private_key": "private_keys",
    "access_token": "oauth_tokens",
    "refresh_token": "oauth_tokens",
    "oauth_token": "oauth_tokens",
    "id_token": "oauth_tokens",
    "browser_credential_store": "browser_credential_store",
    "login_data": "browser_credential_store",
    "keychain": "browser_credential_store",
}
REDACTION_PATTERNS = (
    ("email", re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    ("phone", re.compile(r"\+?\d[\d\s().-]{8,}\d"), "[REDACTED_PHONE]"),
    ("openai_api_key", SECRET_PATTERNS[0][1], "[REDACTED_SECRET]"),
    ("github_token", SECRET_PATTERNS[1][1], "[REDACTED_SECRET]"),
    ("slack_token", SECRET_PATTERNS[2][1], "[REDACTED_SECRET]"),
    ("aws_access_key", SECRET_PATTERNS[3][1], "[REDACTED_SECRET]"),
    (
        "local_absolute_path",
        LOCAL_ABSOLUTE_PATH_RE,
        "[REDACTED_LOCAL_PATH]",
    ),
)


class PrivacyViolation(ValueError):
    pass


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def is_relative_to(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def is_private_source_location(raw_path: Path, database_dir: Path) -> bool:
    resolved_raw = raw_path.resolve()
    resolved_db = database_dir.resolve()
    if not is_relative_to(resolved_raw, resolved_db):
        return True
    return any(is_relative_to(resolved_raw, resolved_db / root) for root in PRIVATE_ROOTS)


def redact_text(text: str) -> tuple[str, dict[str, int]]:
    redacted = text
    counts: dict[str, int] = {}
    for name, pattern, replacement in REDACTION_PATTERNS:
        redacted, count = pattern.subn(replacement, redacted)
        if count:
            counts[name] = counts.get(name, 0) + count
    redacted, credential_counts = redact_credentials_in_text(redacted)
    for name, count in credential_counts.items():
        counts[f"credential_{name}"] = counts.get(f"credential_{name}", 0) + count
    return redacted, counts


def redact_nonportable_paths_in_text(text: str) -> tuple[str, dict[str, int]]:
    """Apply the repository portability boundary without classifying it as credential handling."""

    if "/Users/" not in text and "/home/" not in text and ":\\" not in text and ":/" not in text:
        return text, {}
    redacted, count = LOCAL_ABSOLUTE_PATH_RE.subn("[REDACTED_LOCAL_PATH]", text)
    return redacted, {"local_absolute_path": count} if count else {}


def _credential_match_is_safe_placeholder(match_text: str) -> bool:
    separator = re.search(r"[:=]", match_text)
    if separator is None:
        return False
    return is_safe_credential_placeholder(match_text[separator.end() :])


def is_safe_credential_placeholder(value: str) -> bool:
    candidate = value.strip().strip("'\"").rstrip(";,")
    normalized = candidate.casefold()
    if len(normalized) > 2 and normalized[0] in "[<" and normalized[-1] in "]>":
        normalized = normalized[1:-1].strip()
    return normalized in _SAFE_CREDENTIAL_PLACEHOLDERS


def _normalized_credential_field(field_name: str) -> str:
    return re.sub(r"[\s-]+", "_", field_name.strip().casefold())


def _has_account_control_value(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value.strip()) and not is_safe_credential_placeholder(value)
    if isinstance(value, (list, dict)):
        return bool(value)
    return value is not None and value is not False


def credential_field_category(field_name: str, value: Any) -> str | None:
    """Classify structured credential fields without treating ordinary transcript keys as secrets."""

    normalized = _normalized_credential_field(field_name)
    if normalized in {"cookie", "cookies", "set_cookie"}:
        if isinstance(value, str):
            return "cookies" if _COOKIE_FIELD_VALUE_RE.search(value) else None
        return "cookies" if _has_account_control_value(value) else None
    if normalized == "pwd":
        if not isinstance(value, str) or is_safe_credential_placeholder(value):
            return None
        if "/" in value or "\\" in value:
            return None
        return "passwords" if any(character.isupper() or character.isdigit() for character in value) else None
    category = _CREDENTIAL_FIELD_CATEGORIES.get(normalized)
    return category if category and _has_account_control_value(value) else None


def credential_field_exclusion_hits(value: Any, source: str = "") -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            hits.extend(credential_field_exclusion_hits(item, source))
    elif isinstance(value, dict):
        for key, item in value.items():
            category = credential_field_category(str(key), item)
            if category:
                hits.append(
                    {
                        "category": category,
                        "source": source,
                        "policy": POLICY_ID,
                        "evidence": "[REDACTED_CREDENTIAL]",
                    }
                )
            else:
                hits.extend(credential_field_exclusion_hits(item, source))
    return hits


def credential_exclusion_hits(text: str, source: str = "") -> list[dict[str, Any]]:
    if not _CREDENTIAL_TRIGGER_RE.search(text):
        return []
    hits: list[dict[str, Any]] = []
    seen: set[tuple[str, int, int]] = set()
    for category, pattern in CREDENTIAL_PATTERNS:
        for match in pattern.finditer(text):
            if _credential_match_is_safe_placeholder(match.group(0)):
                continue
            key = (category, match.start(), match.end())
            if key in seen:
                continue
            seen.add(key)
            hits.append(
                {
                    "category": category,
                    "source": source,
                    "start": match.start(),
                    "end": match.end(),
                    "policy": POLICY_ID,
                    "evidence": "[REDACTED_CREDENTIAL]",
                }
            )
    return hits


def assert_no_credentials(text: str, source: str = "") -> None:
    hits = credential_exclusion_hits(text, source)
    if hits:
        categories = sorted({str(hit["category"]) for hit in hits})
        label = f" in {source}" if source else ""
        raise PrivacyViolation(f"credential content is not memory{label}: {', '.join(categories)}")


def redact_credentials_in_text(text: str) -> tuple[str, dict[str, int]]:
    hits = credential_exclusion_hits(text)
    if not hits:
        return text, {}

    counts: dict[str, int] = {}
    intervals: list[tuple[int, int]] = []
    for hit in sorted(hits, key=lambda item: (int(item["start"]), int(item["end"]))):
        category = str(hit["category"])
        counts[category] = counts.get(category, 0) + 1
        start = int(hit["start"])
        end = int(hit["end"])
        if intervals and start <= intervals[-1][1]:
            previous_start, previous_end = intervals[-1]
            intervals[-1] = (previous_start, max(previous_end, end))
        else:
            intervals.append((start, end))

    chunks: list[str] = []
    cursor = 0
    for start, end in intervals:
        chunks.extend((text[cursor:start], "[REDACTED_CREDENTIAL]"))
        cursor = end
    chunks.append(text[cursor:])
    redacted = "".join(chunks)
    return redacted, counts


def merge_counts(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    merged = dict(left)
    for key, value in right.items():
        merged[key] = merged.get(key, 0) + value
    return merged


def redact_payload(value: Any) -> tuple[Any, dict[str, int]]:
    if isinstance(value, str):
        return redact_text(value)
    if isinstance(value, list):
        counts: dict[str, int] = {}
        redacted_items = []
        for item in value:
            redacted_item, item_counts = redact_payload(item)
            redacted_items.append(redacted_item)
            counts = merge_counts(counts, item_counts)
        return redacted_items, counts
    if isinstance(value, dict):
        counts: dict[str, int] = {}
        redacted_dict: dict[str, Any] = {}
        for key, item in value.items():
            redacted_item, item_counts = redact_payload(item)
            redacted_dict[str(key)] = redacted_item
            counts = merge_counts(counts, item_counts)
        return redacted_dict, counts
    return value, {}


def read_private_payload(raw_path: Path) -> Any:
    text = raw_path.read_text(encoding="utf-8", errors="ignore")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"text": text}


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def append_jsonl(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def safe_output_name(name: str | None, raw_path: Path) -> str:
    candidate = name or f"{raw_path.stem}.redacted.json"
    if Path(candidate).name != candidate or not candidate.endswith(".json"):
        raise PrivacyViolation(f"output_name must be a simple .json filename: {candidate}")
    return candidate


def import_private_export(raw_path: Path, database_dir: Path, output_name: str | None = None) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    raw_path = raw_path.resolve()
    if not raw_path.is_file():
        raise PrivacyViolation(f"raw private source does not exist: {raw_path}")
    if not is_private_source_location(raw_path, database_dir):
        raise PrivacyViolation("raw private source must be outside the repo or under an ignored private input root")

    raw_bytes = raw_path.read_bytes()
    raw_payload = read_private_payload(raw_path)
    redacted_payload, redaction_counts = redact_payload(raw_payload)
    redacted_source_name, name_counts = redact_text(raw_path.name)
    redaction_counts = merge_counts(redaction_counts, name_counts)
    output_rel = DERIVED_IMPORT_DIR / safe_output_name(output_name, raw_path)
    output_path = database_dir / output_rel
    result = {
        "schema_version": "openaidatabase.redacted_private_import.v1",
        "generated_at": now_utc(),
        "raw_private_data_included": False,
        "plaintext_secrets_included": False,
        "local_absolute_paths_included": False,
        "raw_source_name": redacted_source_name,
        "raw_source_sha256": sha256_bytes(raw_bytes),
        "raw_source_size_bytes": len(raw_bytes),
        "redaction_counts": redaction_counts,
        "redacted_payload": redacted_payload,
    }
    write_json_atomic(output_path, result)
    append_jsonl(
        database_dir / PRIVACY_AUDIT_LOG,
        {
            "timestamp": result["generated_at"],
            "event_type": "redacted_private_import",
            "output_path": output_rel.as_posix(),
            "raw_private_data_included": False,
            "raw_source_name": redacted_source_name,
            "raw_source_sha256": result["raw_source_sha256"],
            "redaction_counts": redaction_counts,
        },
    )
    return {"status": "PASS", "output_path": output_rel.as_posix(), "redaction_counts": redaction_counts}


def git_ls_files(database_dir: Path, paths: list[str] | None = None) -> list[str]:
    command = ["git", "ls-files"]
    if paths:
        command.extend(["--", *paths])
    try:
        result = subprocess.run(
            command,
            cwd=database_dir,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
        )
    except OSError:
        return []
    if result.returncode != 0:
        return []
    return [line.strip().replace("\\", "/") for line in result.stdout.splitlines() if line.strip()]


def gitignore_declares_private_defaults(database_dir: Path) -> dict[str, Any]:
    text = (database_dir / ".gitignore").read_text(encoding="utf-8", errors="ignore") if (database_dir / ".gitignore").exists() else ""
    entries = {line.strip() for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")}
    missing = [pattern for pattern in REQUIRED_GITIGNORE_PATTERNS if pattern not in entries]
    return {"ok": not missing, "missing": missing, "required": list(REQUIRED_GITIGNORE_PATTERNS)}


def high_risk_secret_hits(database_dir: Path, tracked_files: list[str]) -> list[dict[str, str]]:
    hits: list[dict[str, str]] = []
    for rel in tracked_files:
        path = database_dir / rel
        is_public_raw = rel == "data/public_raw" or rel.startswith("data/public_raw/")
        if not path.is_file() or (not is_public_raw and path.stat().st_size > 1_000_000):
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        payloads = privacy_scan_payloads(path, text)
        if payloads is None:
            segments = [text]
        else:
            segments = [segment for payload in payloads for segment in iter_json_strings(payload)]
            for payload in payloads:
                for hit in credential_field_exclusion_hits(payload, rel):
                    hits.append({"path": rel, "pattern": str(hit["category"])})
        for segment in segments:
            for hit in credential_exclusion_hits(segment, rel):
                hits.append({"path": rel, "pattern": str(hit["category"])})
    return hits


def iter_json_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from iter_json_strings(item)
    elif isinstance(value, dict):
        for key, item in value.items():
            yield str(key)
            yield from iter_json_strings(item)


def privacy_scan_payloads(path: Path, text: str) -> list[Any] | None:
    if path.suffix not in {".json", ".jsonl"}:
        return None
    try:
        if path.suffix == ".json":
            payloads = [json.loads(text)]
        else:
            payloads = [json.loads(line) for line in text.splitlines() if line.strip()]
    except json.JSONDecodeError:
        return None
    return [_normalize_structured_scan_payload(payload) for payload in payloads]


def _normalize_structured_scan_payload(payload: Any) -> Any:
    """Treat validated archive redaction counters as metadata, never as credential values."""

    if not isinstance(payload, dict) or payload.get("schema_version") != (
        CODEX_PUBLIC_RAW_ARCHIVE_MANIFEST_SCHEMA
    ):
        return payload
    counts = payload.get("redaction_counts")
    if (
        not isinstance(counts, dict)
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, int)
            or isinstance(value, bool)
            or value < 0
            for key, value in counts.items()
        )
    ):
        return payload
    normalized = dict(payload)
    normalized["redaction_counts"] = {key: None for key in counts}
    return normalized


def privacy_scan_segments(path: Path, text: str) -> list[str]:
    payloads = privacy_scan_payloads(path, text)
    if payloads is None:
        return [text]
    return [segment for payload in payloads for segment in iter_json_strings(payload)]


def scan_repo_privacy(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    contract = load_credential_exclusion_contract(database_dir)
    configured_categories = {category for category, _ in CREDENTIAL_PATTERNS}
    if configured_categories != set(BLOCKED_ACCOUNT_CONTROL_CATEGORIES):
        raise CredentialExclusionError("credential detector categories drifted from the canonical contract")
    tracked_private = git_ls_files(database_dir, [root.as_posix() for root in PRIVATE_ROOTS])
    tracked_files = git_ls_files(database_dir)
    public_raw_files = [
        rel for rel in tracked_files if rel.startswith("data/public_raw/") and (database_dir / rel).is_file()
    ]
    credential_path_hits = []
    for rel in public_raw_files:
        public_relative = Path(rel).relative_to("data/public_raw")
        pattern = forbidden_public_raw_path_match(public_relative, contract)
        if pattern:
            credential_path_hits.append({"path": rel, "pattern": pattern})
    ignore_contract = gitignore_declares_private_defaults(database_dir)
    secret_hits = high_risk_secret_hits(database_dir, tracked_files)
    large_public_raw_file_count = sum(
        (database_dir / rel).stat().st_size > 1_000_000 for rel in public_raw_files
    )
    return {
        "status": (
            "PASS"
            if not tracked_private and not secret_hits and not credential_path_hits and ignore_contract["ok"]
            else "FAIL"
        ),
        "schema_version": CREDENTIAL_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "credential_policy": POLICY_ID,
        "credential_value_echo": False,
        "broad_privacy_redaction": False,
        "ordinary_transcript_blocked": False,
        "public_raw_file_count": len(public_raw_files),
        "large_public_raw_file_count": large_public_raw_file_count,
        "public_raw_large_files_skipped": False,
        "credential_like_path_hits": credential_path_hits,
        "credential_like_path_hit_count": len(credential_path_hits),
        "tracked_raw_private_files": tracked_private,
        "tracked_raw_private_file_count": len(tracked_private),
        "high_risk_secret_hits": secret_hits,
        "high_risk_secret_hit_count": len(secret_hits),
        "gitignore_contract": ignore_contract,
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAIDatabase privacy import and scan guard.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--scan-only", action="store_true")
    parser.add_argument("--import-private", type=Path)
    parser.add_argument("--output-name")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        if args.scan_only:
            result = scan_repo_privacy(args.database_dir)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0 if result["status"] == "PASS" else 1
        if args.import_private:
            result = import_private_export(args.import_private, args.database_dir, args.output_name)
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
    except CredentialExclusionError:
        print(
            json.dumps(
                {
                    "status": "FAIL_CLOSED",
                    "task_id": TASK_ID,
                    "credential_policy": POLICY_ID,
                    "error": "credential_exclusion_contract_invalid",
                    "credential_value_echo": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2
    raise SystemExit("Use --scan-only or --import-private")


if __name__ == "__main__":
    raise SystemExit(main())
