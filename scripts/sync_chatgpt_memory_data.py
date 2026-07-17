#!/usr/bin/env python3
"""Sync ChatGPT official exports into the public raw archive.

S04 P1 intentionally keeps the browser connector as a read-only contract. It
never logs in, never captures browser credentials and never mutates ChatGPT
state. The executable path in this phase is the official export fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from memory_atlas_cli.chatgpt_canonical_events import (
    EVENTS_RELATIVE as CANONICAL_EVENTS_RELATIVE,
    ChatGPTCanonicalEventError,
    canonical_plan_result,
    commit_chatgpt_canonical_events,
    plan_chatgpt_canonical_events,
    stable_source_conversation_id,
)
from memory_atlas_cli.chatgpt_export_parser import (
    QUARANTINE_RELATIVE,
    parse_chatgpt_export,
)
from memory_atlas_cli.chatgpt_derived import (
    EXPECTED_OUTPUTS as CHATGPT_DERIVED_OUTPUTS,
    ChatGPTDerivedError,
    build_chatgpt_derived,
)
from memory_atlas_cli.raw_ledger import RawLedgerError, RawLedgerPostWriteError, source_stat_guard
from privacy_guard import PrivacyViolation, assert_no_credentials
from public_raw_sanitizer import (
    PublicRawLimitError,
    PublicRawSanitizationError,
    merge_counts,
    require_public_raw_file_size,
    sanitize_public_value,
)
from raw_archive_manifest import preflight_raw_ledger, record_raw_ledger


SOURCE_ID = "chatgpt"
RAW_ROOT = Path("data/public_raw/chatgpt")
PROCESSED_MANIFEST = Path("data/processed/conversations/conversation_manifest.jsonl")
DERIVED_SUMMARY = Path("data/derived/chatgpt/chatgpt_sync_summary.json")
SYNC_LOG_DIR = Path("data/run_logs/sync_runs")
FORBIDDEN_BROWSER_STATES = {"login_required", "password_required", "verification_required", "captcha_required"}
OFFICIAL_EXPORT_MODE = "official_export_fallback"


class AppendOnlyViolation(ValueError):
    pass


class ParsedConversationList(list[dict[str, Any]]):
    """List-compatible adapter carrying the loss-aware parser report."""

    def __init__(
        self,
        conversations: Iterable[dict[str, Any]],
        parse_report: dict[str, Any],
    ) -> None:
        super().__init__(conversations)
        self.parse_report = parse_report


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def iso_from_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(float(value), tz=timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    text = str(value).strip()
    if not text:
        return ""
    if text.endswith("Z"):
        return text
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return text
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def stable_hash(value: Any) -> str:
    payload = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def safe_filename(value: str) -> str:
    text = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    text = text.strip("._-")
    return text or stable_hash(value)[:16]


def write_if_changed(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        current = path.read_text(encoding="utf-8", errors="ignore")
        if current == payload:
            return
        raise AppendOnlyViolation(f"append-only raw target already exists with different content: {path}")
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def append_jsonl(path: Path, row: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def git_head(database_dir: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            cwd=database_dir,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except Exception:
        return "UNKNOWN_NO_GIT_HEAD"


def build_sync_log_row(
    database_dir: Path,
    generated_at: str,
    summary: dict[str, Any],
    export_sha256: str,
    redact_for_public_backup: bool,
) -> dict[str, Any]:
    head = git_head(database_dir)
    residual_risk = (
        "the authorized private export and omitted credentials remain outside GitHub"
    )
    return {
        "timestamp": generated_at,
        "category": "sync_runs",
        "task_id": "MA-V12-S04P1",
        "run_type": "sync_run",
        "status": "PASS",
        "task": "sync_chatgpt_memory_data",
        "source_id": SOURCE_ID,
        "mode": OFFICIAL_EXPORT_MODE,
        "dry_run": False,
        "conversation_count": summary["conversation_count"],
        "message_count": summary["message_count"],
        "export_sha256": export_sha256,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": summary["redaction_counts"],
        "updated_targets": ["history", "pattern"],
        "source_files": ["authorized ChatGPT official export snapshot"],
        "output_files": [
            RAW_ROOT.as_posix(),
            PROCESSED_MANIFEST.as_posix(),
            CANONICAL_EVENTS_RELATIVE.as_posix(),
            DERIVED_SUMMARY.as_posix(),
        ],
        "context_used": [
            {
                "source": "authorized ChatGPT official export snapshot",
                "reason": "read-only fallback input for sanitized public transcript recovery",
            }
        ],
        "tools_used": [
            {
                "tool": "python",
                "operation": "sync_chatgpt_memory_data",
                "result": "success",
            }
        ],
        "tests_run": [
            {
                "command": "connector runtime does not execute test suites",
                "result": "NOT_RUN",
                "not_run_reason": "tests are executed by the surrounding R7 validation run",
            }
        ],
        "failure_recovery": [],
        "base_commit": head,
        "result_commit": head,
        "residual_risks": [residual_risk],
    }


def write_current_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if not isinstance(content, dict):
        return ""
    parts = content.get("parts")
    if isinstance(parts, list):
        return "\n".join(str(part) for part in parts if isinstance(part, (str, int, float)))
    text = content.get("text") or content.get("value")
    return str(text) if text is not None else ""


def extract_attachments(content: Any) -> list[dict[str, Any]]:
    if not isinstance(content, dict):
        return []
    parts = content.get("parts")
    if not isinstance(parts, list):
        return []
    attachment_keys = {
        "asset_pointer",
        "attachment_id",
        "file_id",
        "file_name",
        "mime_type",
        "size_bytes",
    }
    attachments: list[dict[str, Any]] = []
    for part in parts:
        if not isinstance(part, dict):
            continue
        content_type = str(part.get("content_type") or "").lower()
        if attachment_keys.intersection(part) or any(
            marker in content_type
            for marker in ("asset", "image", "file", "audio", "video")
        ):
            attachments.append(part)
    return attachments


def extension_fields(
    payload: Any,
    known_fields: set[str],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        return {}
    return {key: value for key, value in payload.items() if key not in known_fields}


def normalized_message(
    message: dict[str, Any],
    *,
    fallback_id: str,
) -> dict[str, Any] | None:
    content = message.get("content")
    if content is None:
        content = message.get("text")
    text = extract_text(content)
    attachments = extract_attachments(content)
    if not text.strip() and not attachments:
        return None
    author = message.get("author")
    author_payload = author if isinstance(author, dict) else {}
    role = (
        author_payload.get("role")
        or message.get("role")
        or (author if isinstance(author, str) else None)
        or "unknown"
    )
    return {
        "message_id": str(message.get("id") or fallback_id),
        "role": str(role),
        "created_at": iso_from_value(
            message.get("created_at") or message.get("create_time")
        ),
        "text": text,
        "attachments": attachments,
        "source_extensions": extension_fields(
            message,
            {"id", "author", "role", "created_at", "create_time", "content", "text"},
        ),
        "author_extensions": extension_fields(author_payload, {"role"}),
        "content_extensions": extension_fields(
            content,
            {"parts", "text", "value"},
        ),
    }


def normalize_messages(conversation: dict[str, Any]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mapping = conversation.get("mapping")
    if isinstance(mapping, dict):
        for mapping_key, node in mapping.items():
            if not isinstance(node, dict):
                continue
            message = node.get("message")
            if not isinstance(message, dict):
                continue
            row = normalized_message(
                message,
                fallback_id=str(node.get("id") or mapping_key),
            )
            if row is not None:
                rows.append(row)
        return rows

    messages = conversation.get("messages")
    if isinstance(messages, list):
        for index, message in enumerate(messages):
            if not isinstance(message, dict):
                continue
            row = normalized_message(
                message,
                fallback_id=f"message_{index + 1}",
            )
            if row is not None:
                rows.append(row)
    return rows


def conversation_payload(conversation: dict[str, Any]) -> dict[str, Any]:
    conversation_id = stable_source_conversation_id(conversation)
    title = str(conversation.get("title") or "Untitled ChatGPT conversation")
    messages = normalize_messages(conversation)
    payload = {
        "schema_version": "memory_atlas_public_raw_chatgpt.v1",
        "source_id": SOURCE_ID,
        "conversation_id": conversation_id,
        "title": title,
        "created_at": iso_from_value(conversation.get("create_time") or conversation.get("created_at")),
        "updated_at": iso_from_value(conversation.get("update_time") or conversation.get("updated_at")),
        "message_count": len(messages),
        "messages": messages,
        "source_extensions": extension_fields(
            conversation,
            {
                "id",
                "conversation_id",
                "title",
                "create_time",
                "created_at",
                "update_time",
                "updated_at",
                "mapping",
                "messages",
                "_memory_atlas_parser",
            },
        ),
        "parser_provenance": conversation.get("_memory_atlas_parser") or {},
        "credential_boundary": "credentials_not_transcript",
        "sync_mode": OFFICIAL_EXPORT_MODE,
    }
    return payload


def assert_conversation_has_no_credentials(payload: dict[str, Any]) -> None:
    conversation_id = str(payload["conversation_id"])
    assert_no_credentials(
        json.dumps(payload, ensure_ascii=False, sort_keys=True),
        f"{SOURCE_ID}:{conversation_id}:normalized_payload",
    )


def normalize_conversation(conversation: dict[str, Any]) -> dict[str, Any]:
    payload = conversation_payload(conversation)
    assert_conversation_has_no_credentials(payload)
    return payload


def prepare_public_conversation(
    conversation: dict[str, Any],
    *,
    redact_for_public_backup: bool,
) -> tuple[dict[str, Any], dict[str, int]]:
    payload = conversation_payload(conversation)
    redaction_counts: dict[str, int] = {}
    if redact_for_public_backup:
        sanitized, redaction_counts = sanitize_public_value(payload)
        if not isinstance(sanitized, dict):
            raise PublicRawSanitizationError("sanitized ChatGPT conversation must remain an object")
        payload = sanitized
    else:
        assert_conversation_has_no_credentials(payload)
    payload["redact_for_public_backup"] = redact_for_public_backup
    payload["redaction_counts"] = redaction_counts
    payload["content_sha256"] = stable_hash(payload)
    return payload, redaction_counts


def coerce_conversation_list(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict):
        conversations = payload.get("conversations")
        if isinstance(conversations, list):
            return [item for item in conversations if isinstance(item, dict)]
        if payload.get("mapping") or payload.get("messages"):
            return [payload]
    return []


def load_official_export(path: Path) -> ParsedConversationList:
    report = parse_chatgpt_export(path)
    return ParsedConversationList(report["conversations"], report)


def official_export_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    if path.is_dir():
        candidates = sorted(path.glob("**/*.json"))
        for candidate in candidates:
            relative = candidate.relative_to(path).as_posix().encode("utf-8")
            digest.update(len(relative).to_bytes(8, "big"))
            digest.update(relative)
            with candidate.open("rb") as handle:
                for chunk in iter(lambda: handle.read(1024 * 1024), b""):
                    digest.update(chunk)
        return digest.hexdigest()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_summary(
    rows: list[dict[str, Any]],
    generated_at: str,
    *,
    export_sha256: str = "",
    redaction_counts: dict[str, int] | None = None,
    redact_for_public_backup: bool = False,
    canonical_events: dict[str, Any] | None = None,
    derived_inputs: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "schema_version": "memory_atlas_chatgpt_sync_summary.v1",
        "source_id": SOURCE_ID,
        "generated_at": generated_at,
        "conversation_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "conversation_ids": [row["conversation_id"] for row in rows],
        "mode": OFFICIAL_EXPORT_MODE,
        "credential_boundary": "credentials_not_transcript",
        "export_sha256": export_sha256,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": redaction_counts or {},
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
        "canonical_events": canonical_events
        or {
            "status": "NOT_RUN",
            "events_path": CANONICAL_EVENTS_RELATIVE.as_posix(),
            "appended_version_count": 0,
            "unchanged_version_count": 0,
            "event_count": 0,
            "writes_files": False,
            "append_only": True,
        },
        "derived_inputs": derived_inputs
        or {
            "status": "NOT_RUN",
            "reason": "canonical_events_not_committed",
            "output_paths": CHATGPT_DERIVED_OUTPUTS,
            "writes_files": False,
            "raw_mutation": False,
            "canonical_mutation": False,
        },
    }


def build_manifest_row(
    row: dict[str, Any],
    raw_path: Path,
    export_sha256: str,
    generated_at: str,
) -> dict[str, Any]:
    roles = [str(message.get("role") or "unknown") for message in row.get("messages") or []]
    return {
        "schema_version": "memory_atlas_conversation_manifest.v2",
        "conversation_id": row["conversation_id"],
        "title": row["title"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
        "message_count": row["message_count"],
        "user_message_count": roles.count("user"),
        "assistant_message_count": roles.count("assistant"),
        "content_sha256": row["content_sha256"],
        "export_sha256": export_sha256,
        "raw_ref": raw_path.as_posix(),
        "parsed_at": generated_at,
        "redaction_counts": row.get("redaction_counts") or {},
    }


def sync_official_export(
    database_dir: Path,
    export_path: Path,
    dry_run: bool,
    redact_for_public_backup: bool = False,
) -> dict[str, Any]:
    directory_globs = ("**/*.json",) if export_path.is_dir() else ()
    with source_stat_guard(export_path, directory_globs=directory_globs) as source_inventory:
        conversations = load_official_export(export_path)
        export_sha = official_export_sha256(export_path)
    parse_report = getattr(
        conversations,
        "parse_report",
        {
            "status": "PASS",
            "attachment_count": 0,
            "metadata_count": 0,
            "quarantine_count": 0,
            "quarantine": [],
        },
    )
    if not conversations:
        quarantine_rows = parse_report.get("quarantine") or []
        writes_files = False
        if not dry_run and quarantine_rows:
            with source_stat_guard(
                export_path,
                directory_globs=directory_globs,
                expected=source_inventory,
            ):
                write_current_jsonl(
                    database_dir / QUARANTINE_RELATIVE,
                    quarantine_rows,
                )
            writes_files = True
        return {
            "status": parse_report.get("status") or "NO_CONVERSATIONS",
            "source_id": SOURCE_ID,
            "mode": OFFICIAL_EXPORT_MODE,
            "dry_run": dry_run,
            "browser_connector": "readonly_contract",
            "fallback": "official_export",
            "conversation_count": 0,
            "message_count": 0,
            "attachment_count": int(parse_report.get("attachment_count") or 0),
            "metadata_count": int(parse_report.get("metadata_count") or 0),
            "quarantine_count": int(parse_report.get("quarantine_count") or 0),
            "quarantine_path": QUARANTINE_RELATIVE.as_posix(),
            "raw_paths": [],
            "export_sha256": export_sha,
            "redact_for_public_backup": redact_for_public_backup,
            "redaction_counts": {},
            "processed_manifest": PROCESSED_MANIFEST.as_posix(),
            "canonical_events": {
                "status": "NOT_RUN",
                "events_path": CANONICAL_EVENTS_RELATIVE.as_posix(),
                "appended_version_count": 0,
                "unchanged_version_count": 0,
                "event_count": 0,
                "writes_files": False,
                "append_only": True,
            },
            "derived_inputs": {
                "status": "NOT_RUN",
                "reason": "no_parseable_conversations",
                "output_paths": CHATGPT_DERIVED_OUTPUTS,
                "writes_files": False,
                "raw_mutation": False,
                "canonical_mutation": False,
            },
            "derived_summary": DERIVED_SUMMARY.as_posix(),
            "run_log_dir": SYNC_LOG_DIR.as_posix(),
            "writes_files": writes_files,
            "append_only": True,
            "no_browser_mutation": True,
            "source_stat_verified": True,
            "processed_outputs_preserved": True,
            "raw_ledger": {
                "status": "NOT_RUN",
                "reason": "no_parseable_conversations",
                "source_mutation": False,
            },
        }
    rows: list[dict[str, Any]] = []
    redaction_counts: dict[str, int] = {}
    for conversation in conversations:
        row, row_counts = prepare_public_conversation(
            conversation,
            redact_for_public_backup=redact_for_public_backup,
        )
        rows.append(row)
        redaction_counts = merge_counts(redaction_counts, row_counts)
    generated_at = now_utc()
    raw_paths = [
        RAW_ROOT / f"{safe_filename(row['conversation_id'])}.{row['content_sha256'][:12]}.json"
        for row in rows
    ]
    raw_payloads = [json.dumps(row, ensure_ascii=False, indent=2, sort_keys=True) + "\n" for row in rows]
    for relative_path, payload in zip(raw_paths, raw_payloads):
        require_public_raw_file_size(payload, relative_path.as_posix())
    manifest_rows = [
        build_manifest_row(row, relative_path, export_sha, generated_at)
        for row, relative_path in zip(rows, raw_paths)
    ]
    canonical_plan = plan_chatgpt_canonical_events(
        database_dir,
        rows,
        raw_paths,
        export_sha256=export_sha,
        observed_at=generated_at,
    )
    canonical_events = canonical_plan_result(canonical_plan, dry_run=dry_run)
    derived_inputs = {
        "status": "NOT_RUN",
        "reason": "dry_run",
        "output_paths": CHATGPT_DERIVED_OUTPUTS,
        "writes_files": False,
        "raw_mutation": False,
        "canonical_mutation": False,
    }

    raw_ledger = {
        "status": "NOT_RUN",
        "task_id": "S06-P2-T1",
        "reason": "dry_run",
        "source_mutation": False,
    }
    if not dry_run:
        raw_writes_started = False
        try:
            with source_stat_guard(
                export_path,
                directory_globs=directory_globs,
                expected=source_inventory,
            ):
                preflight_raw_ledger(database_dir)
                raw_writes_started = True
                for relative_path, payload in zip(raw_paths, raw_payloads):
                    write_if_changed(database_dir / relative_path, payload)
                raw_ledger = record_raw_ledger(database_dir, generated_at)
        except RawLedgerError as exc:
            if raw_writes_started:
                raise RawLedgerPostWriteError(
                    f"append-only raw or ledger bytes may exist after commit failure: {exc}"
                ) from exc
            raise
        try:
            canonical_events = commit_chatgpt_canonical_events(
                database_dir,
                canonical_plan,
            )
        except ChatGPTCanonicalEventError as exc:
            exc.writes_files = True
            raise
        derived_inputs = build_chatgpt_derived(database_dir)
        write_current_jsonl(database_dir / PROCESSED_MANIFEST, manifest_rows)
        write_current_jsonl(
            database_dir / QUARANTINE_RELATIVE,
            parse_report.get("quarantine") or [],
        )
        summary = build_summary(
            rows,
            generated_at,
            export_sha256=export_sha,
            redaction_counts=redaction_counts,
            redact_for_public_backup=redact_for_public_backup,
            canonical_events=canonical_events,
            derived_inputs=derived_inputs,
        )
        (database_dir / DERIVED_SUMMARY).parent.mkdir(parents=True, exist_ok=True)
        (database_dir / DERIVED_SUMMARY).write_text(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        append_jsonl(
            database_dir / SYNC_LOG_DIR / f"{generated_at[:10]}.jsonl",
            build_sync_log_row(
                database_dir,
                generated_at,
                summary,
                export_sha,
                redact_for_public_backup,
            ),
        )

    return {
        "status": parse_report.get("status") or "PASS",
        "source_id": SOURCE_ID,
        "mode": OFFICIAL_EXPORT_MODE,
        "dry_run": dry_run,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "conversation_count": len(rows),
        "message_count": sum(int(row.get("message_count") or 0) for row in rows),
        "attachment_count": int(parse_report.get("attachment_count") or 0),
        "metadata_count": int(parse_report.get("metadata_count") or 0),
        "quarantine_count": int(parse_report.get("quarantine_count") or 0),
        "quarantine_path": QUARANTINE_RELATIVE.as_posix(),
        "raw_paths": [path.as_posix() for path in raw_paths],
        "export_sha256": export_sha,
        "redact_for_public_backup": redact_for_public_backup,
        "redaction_counts": redaction_counts,
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
        "canonical_events": canonical_events,
        "derived_inputs": derived_inputs,
        "derived_summary": DERIVED_SUMMARY.as_posix(),
        "run_log_dir": SYNC_LOG_DIR.as_posix(),
        "writes_files": not dry_run,
        "append_only": True,
        "no_browser_mutation": True,
        "source_stat_verified": True,
        "raw_ledger": raw_ledger,
    }


def dry_run_contract(redact_for_public_backup: bool = False) -> dict[str, Any]:
    return {
        "status": "PASS",
        "source_id": SOURCE_ID,
        "mode": "browser_readonly_contract",
        "dry_run": True,
        "browser_connector": "readonly_contract",
        "fallback": "official_export",
        "conversation_count": 0,
        "message_count": 0,
        "writes_files": False,
        "append_only": True,
        "no_browser_mutation": True,
        "input_required_for_apply": True,
        "official_export_fallback": "official export ZIP/conversations.json fallback",
        "redact_for_public_backup": redact_for_public_backup,
        "processed_manifest": PROCESSED_MANIFEST.as_posix(),
        "canonical_events": {
            "status": "NOT_RUN",
            "events_path": CANONICAL_EVENTS_RELATIVE.as_posix(),
            "appended_version_count": 0,
            "unchanged_version_count": 0,
            "event_count": 0,
            "writes_files": False,
            "append_only": True,
        },
        "derived_inputs": {
            "status": "NOT_RUN",
            "reason": "dry_run_without_committed_canonical_events",
            "output_paths": CHATGPT_DERIVED_OUTPUTS,
            "writes_files": False,
            "raw_mutation": False,
            "canonical_mutation": False,
        },
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P1 ChatGPT read-only sync.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--official-export", type=Path)
    parser.add_argument("--browser-state", choices=["ready", "not_configured", "login_required", "password_required", "verification_required", "captcha_required"], default="not_configured")
    parser.add_argument("--redact-for-public-backup", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    if args.browser_state in FORBIDDEN_BROWSER_STATES:
        print(json.dumps({
            "status": "STOPPED",
            "source_id": SOURCE_ID,
            "reason": "browser_requires_human_authentication",
            "browser_state": args.browser_state,
            "dry_run": args.dry_run,
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    try:
        if args.official_export:
            result = sync_official_export(
                args.database_dir.resolve(),
                args.official_export.expanduser().absolute(),
                args.dry_run,
                redact_for_public_backup=args.redact_for_public_backup,
            )
        elif args.dry_run:
            result = dry_run_contract(args.redact_for_public_backup)
        else:
            result = {
                "status": "NEEDS_INPUT",
                "source_id": SOURCE_ID,
                "reason": "official_export_required_for_apply",
                "browser_connector": "readonly_contract",
                "fallback": "official_export",
                "no_browser_mutation": True,
            }
            print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
            return 2
    except PrivacyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "credential_is_not_memory",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 4
    except AppendOnlyViolation as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "append_only_violation",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 5
    except ChatGPTCanonicalEventError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": SOURCE_ID,
            "reason": "canonical_event_violation",
            "error": exc.code,
            "writes_files": exc.writes_files,
            "partial_append_only_raw_writes_possible": exc.writes_files,
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 8
    except ChatGPTDerivedError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": SOURCE_ID,
            "reason": "derived_input_violation",
            "error": exc.code,
            "writes_files": True,
            "partial_append_only_raw_writes_possible": True,
            "partial_append_only_canonical_writes_possible": True,
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 9
    except (PublicRawLimitError, PublicRawSanitizationError) as exc:
        print(json.dumps({
            "status": "FAIL",
            "source_id": SOURCE_ID,
            "reason": "public_raw_sanitization_failed",
            "error": str(exc),
            "no_browser_mutation": True,
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 6
    except RawLedgerError as exc:
        print(json.dumps({
            "status": "FAIL_CLOSED",
            "source_id": SOURCE_ID,
            "reason": "raw_ledger_violation",
            "error": str(exc),
            "writes_files": isinstance(exc, RawLedgerPostWriteError),
            "partial_append_only_raw_writes_possible": isinstance(exc, RawLedgerPostWriteError),
            "source_mutation": "source stat changed" in str(exc),
        }, ensure_ascii=False, indent=2, sort_keys=True))
        return 7

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
