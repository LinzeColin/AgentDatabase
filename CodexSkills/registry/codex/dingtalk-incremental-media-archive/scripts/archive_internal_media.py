#!/usr/bin/env python3
"""DWS internal-group media archive runner.

All runtime state is held in the two durable manifests. The process only creates
an operating-system temporary directory and removes it before exit.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Iterable
from zoneinfo import ZoneInfo


def _resolve_kmos_root() -> Path:
    """KMOS 根定位：KMOS_ROOT 环境变量优先；否则回退 __file__.parents[4]（worktree 内布局）。"""
    env = os.environ.get("KMOS_ROOT", "").strip()
    if env:
        p = Path(env).expanduser().resolve()
        if p.is_dir():
            return p
    return Path(__file__).resolve().parents[4]


ROOT = _resolve_kmos_root()
PRIVATE_DB_CLIENT = ROOT / "KMDatabase" / "machine" / "tools" / "private_db_client.py"
SMB_ROOT = Path("/Volumes/share/03_资料库/MetaData/IDS_MetaData/KMVideo")
GITHUB_AREA = "Private-KMDatabase"
GITHUB_PREFIX = "KMVideo"
GITHUB_MAX_BYTES = 95 * 1024 * 1024
DWS_TIMEOUT_SECONDS = 60
MANIFEST_NAME = ".manifest.jsonl"
TIMEZONE = ZoneInfo("Asia/Shanghai")
MEDIA_ID_RE = re.compile(r"mediaId=([^\s)\]]+)")
SMB_COPY_METHODS = ("dd", "rsync", "dd", "rsync")

# 单进程内并发下载时，records 字典与 manifest 追加仍保持单一写入者语义。
MANIFEST_LOCK = threading.Lock()


class ArchiveError(RuntimeError):
    pass


class PagingError(ArchiveError):
    pass


@dataclass(frozen=True)
class Group:
    title: str
    conversation_id: str
    group_type: str = "INTERNAL_GROUP"


# 用户显式授权纳入归档的非 INTERNAL_GROUP 会话（仍逐个 --allow-title 显式授权，
# 只读采集，SMB/GitHub 双目的地不变；名单外一律拒绝）。
AUTHORIZED_NON_INTERNAL_TITLES = {
    "新疆宜化2026",
    "项目设备工具类管理群",
}


@dataclass
class Counts:
    discovered: int = 0
    smb_saved: int = 0
    smb_repaired: int = 0
    smb_repaired_from_github: int = 0
    smb_repaired_from_dws: int = 0
    github_raw: int = 0
    github_index: int = 0
    skipped: int = 0
    failures: int = 0
    topic_replies: int = 0
    completed_windows: int = 0
    failures_by_reason: list[str] = field(default_factory=list)

    def merge(self, other: "Counts") -> None:
        self.discovered += other.discovered
        self.smb_saved += other.smb_saved
        self.smb_repaired += other.smb_repaired
        self.smb_repaired_from_github += other.smb_repaired_from_github
        self.smb_repaired_from_dws += other.smb_repaired_from_dws
        self.github_raw += other.github_raw
        self.github_index += other.github_index
        self.skipped += other.skipped
        self.failures += other.failures
        self.topic_replies += other.topic_replies
        self.completed_windows += other.completed_windows
        self.failures_by_reason.extend(other.failures_by_reason)


@dataclass
class GitHubMediaBudget:
    remaining: int | None

    def take(self) -> bool:
        if self.remaining is None:
            return True
        if self.remaining <= 0:
            return False
        self.remaining -= 1
        return True


def print_event(event: str, **fields: object) -> None:
    print(json.dumps({"event": event, **fields}, ensure_ascii=False, sort_keys=True), flush=True)


def run_process(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=ROOT,
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )


def dws_json(args: list[str]) -> dict:
    result = run_process(["dws", *args, "--timeout", str(DWS_TIMEOUT_SECONDS), "--format", "json"])
    if result.returncode != 0:
        raise ArchiveError(f"DWS command failed: {result.stderr.strip() or result.stdout.strip()}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise ArchiveError(f"DWS returned invalid JSON: {exc}") from exc
    if not payload.get("success"):
        raise ArchiveError(payload.get("errorMsg") or payload.get("errorCode") or "DWS request failed")
    return payload.get("result") or {}


def client(args: list[str]) -> subprocess.CompletedProcess[str]:
    return run_process(["python3", str(PRIVATE_DB_CLIENT), *args])


def is_not_found(result: subprocess.CompletedProcess[str]) -> bool:
    text = f"{result.stdout}\n{result.stderr}".lower()
    return "not found" in text or "404" in text or "不存在" in text


def parse_time(value: str) -> datetime:
    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S").replace(tzinfo=TIMEZONE)


def dws_time(value: datetime) -> str:
    return value.astimezone(TIMEZONE).strftime("%Y-%m-%d %H:%M:%S")


def read_manifest(path: Path) -> dict[str, dict]:
    if not path.exists():
        return {}
    result: dict[str, dict] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    for index, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            if index == len(lines) - 1:
                continue
            raise
        record_id = record.get("record_id")
        if record_id:
            result[record_id] = record
    return result


def status_rank(status: object, kind: str) -> int:
    value = str(status or "")
    if kind == "smb":
        return {"complete": 4, "pending": 2, "failed": 1}.get(value, 0)
    return {"complete": 4, "index_only": 3, "pending": 2, "failed": 1}.get(value, 0)


def merge_record(left: dict, right: dict) -> dict:
    merged = {**left, **right}
    for key, kind in (("smb_status", "smb"), ("github_media_status", "github")):
        chosen = left.get(key)
        if status_rank(right.get(key), kind) > status_rank(chosen, kind):
            chosen = right.get(key)
        if chosen:
            merged[key] = chosen
    if left.get("record_type") == "window" and right.get("record_type") == "window":
        if left.get("window_status") == "complete" or right.get("window_status") == "complete":
            merged["window_status"] = "complete"
    return merged


def merge_manifests(smb_records: dict[str, dict], github_records: dict[str, dict]) -> dict[str, dict]:
    merged = dict(github_records)
    for record_id, record in smb_records.items():
        merged[record_id] = merge_record(merged[record_id], record) if record_id in merged else record
    return merged


def manifest_text(records: dict[str, dict]) -> str:
    rows = [records[key] for key in sorted(records)]
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.partial-{uuid.uuid4().hex}")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def github_manifest_path(folder: str) -> str:
    return f"{GITHUB_PREFIX}/{folder}/{MANIFEST_NAME}"


def get_github_manifest(folder: str, temp_root: Path) -> tuple[dict[str, dict], str | None]:
    target = temp_root / f"github-manifest-{uuid.uuid4().hex}.jsonl"
    result = client(["get", GITHUB_AREA, github_manifest_path(folder), str(target)])
    if result.returncode == 0:
        try:
            return read_manifest(target), None
        finally:
            target.unlink(missing_ok=True)
    target.unlink(missing_ok=True)
    if is_not_found(result):
        return {}, None
    return {}, result.stderr.strip() or result.stdout.strip() or "GitHub manifest read failed"


def put_github_manifest(folder: str, text: str, temp_root: Path) -> str | None:
    target = temp_root / f"github-manifest-upload-{uuid.uuid4().hex}.jsonl"
    target.write_text(text, encoding="utf-8")
    try:
        result = client(["put", GITHUB_AREA, github_manifest_path(folder), str(target)])
    finally:
        target.unlink(missing_ok=True)
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "GitHub manifest write failed"


def persist_smb_manifest(folder: str, records: dict[str, dict]) -> dict[str, dict]:
    """Merge with the current SMB copy before replacing it.

    A group is intentionally single-writer in normal operation.  This merge is
    still needed to preserve an already-appended durable record if a prior run
    ended between the current process reading its manifest and this checkpoint.
    For the same record ID, this active writer is newer than its own prior
    checkpoint, so its in-memory state must win over an obsolete complete state.
    """
    path = SMB_ROOT / folder / MANIFEST_NAME
    current = read_manifest(path)
    merged = {**current, **records}
    atomic_write(path, manifest_text(merged))
    return merged


def append_smb_manifest_record(folder: str, record: dict) -> None:
    path = SMB_ROOT / folder / MANIFEST_NAME
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n")


def persist_manifests(folder: str, records: dict[str, dict], temp_root: Path) -> tuple[dict[str, dict], str | None]:
    merged = persist_smb_manifest(folder, records)
    return merged, put_github_manifest(folder, manifest_text(merged), temp_root)


def find_existing_folder(group: Group) -> str:
    direct = SMB_ROOT / group.title
    if direct.exists():
        return group.title
    for candidate in SMB_ROOT.iterdir():
        if not candidate.is_dir():
            continue
        manifest = candidate / MANIFEST_NAME
        try:
            records = read_manifest(manifest)
        except (OSError, json.JSONDecodeError):
            continue
        for record in records.values():
            if record.get("record_type") == "group" and record.get("conversation_id") == group.conversation_id:
                return candidate.name
    return group.title


def select_groups(allowed_titles: list[str]) -> list[Group]:
    result = dws_json(["chat", "list-all-conversations"])
    conversations = result.get("conversations") or []
    by_title: dict[str, list[dict]] = {}
    for conversation in conversations:
        by_title.setdefault(str(conversation.get("title") or ""), []).append(conversation)

    selected: list[Group] = []
    failures: list[str] = []
    for title in allowed_titles:
        matches = by_title.get(title, [])
        # 同名消歧：优先取非单聊会话（群名与某人的单聊同名时）。
        non_single = [c for c in matches if c.get("singleChat") is False]
        if len(non_single) == 1:
            matches = non_single
        if len(matches) != 1:
            failures.append(f"{title}: expected one live conversation, got {len(matches)}")
            continue
        conversation = matches[0]
        is_internal = (
            conversation.get("groupType") == "INTERNAL_GROUP"
            and conversation.get("singleChat") is False
        )
        is_authorized_extra = (
            title in AUTHORIZED_NON_INTERNAL_TITLES
            and conversation.get("singleChat") is False
        )
        if not (is_internal or is_authorized_extra):
            failures.append(f"{title}: refused non-internal or single-chat conversation")
            continue
        conversation_id = str(conversation.get("openConversationId") or "")
        if not conversation_id:
            failures.append(f"{title}: missing openConversationId")
            continue
        selected.append(Group(
            title=title,
            conversation_id=conversation_id,
            group_type=str(conversation.get("groupType") or "INTERNAL_GROUP"),
        ))
    if failures:
        raise ArchiveError("; ".join(failures))
    return selected


def message_page(group_id: str, boundary: datetime, topic_id: str | None, page_size: int) -> dict:
    if topic_id:
        args = [
            "chat", "message", "list-topic-replies",
            "--group", group_id,
            "--topic-id", topic_id,
        ]
    else:
        args = ["chat", "message", "list", "--group", group_id]
    args.extend(["--time", dws_time(boundary), "--direction", "older", "--limit", str(page_size)])
    return dws_json(args)


def walk_window_messages(
    group_id: str,
    start: datetime,
    end: datetime,
    topic_id: str | None,
    page_size: int,
) -> Iterable[dict]:
    boundary = end
    page_signatures: set[tuple[str, tuple[str, ...]]] = set()
    while True:
        result = message_page(group_id, boundary, topic_id, page_size)
        messages = result.get("messages") or []
        has_more = bool(result.get("hasMore"))
        if not messages:
            if has_more:
                raise PagingError("empty page with hasMore=true")
            return
        identifiers = tuple(str(message.get("openMessageId") or "") for message in messages)
        signature = (dws_time(boundary), identifiers)
        if signature in page_signatures:
            raise PagingError("DWS pagination repeated a page")
        page_signatures.add(signature)

        parsed: list[tuple[datetime, dict]] = []
        for message in messages:
            create_time = message.get("createTime")
            if not create_time:
                raise PagingError("message missing createTime")
            parsed.append((parse_time(str(create_time)), message))
        oldest = min(timestamp for timestamp, _ in parsed)
        if oldest >= boundary:
            raise PagingError("DWS pagination boundary did not move older")
        for timestamp, message in parsed:
            if start <= timestamp < end:
                yield message
        if oldest < start or not has_more:
            return
        boundary = oldest


def classify_media(message: dict) -> list[tuple[str, str]]:
    content = str(message.get("content") or "")
    resource_ids = MEDIA_ID_RE.findall(content)
    if not resource_ids:
        return []
    lowered = content.lower()
    if "视频" in content or "video" in lowered:
        media_type = "video"
    elif "图片" in content or "照片" in content or "image" in lowered:
        media_type = "photo"
    else:
        return []
    return [(resource_id, media_type) for resource_id in resource_ids]


def safe_filename(name: str, message_id: str) -> str:
    candidate = Path(name).name.replace("\x00", "_").replace("/", "_")
    if candidate in {"", ".", ".."}:
        candidate = f"media-{message_id.replace('/', '_')}"
    return candidate


def choose_relative_path(
    folder: str,
    media_type: str,
    filename: str,
    message_id: str,
    records: dict[str, dict],
    existing: dict | None,
) -> str:
    if existing and existing.get("relative_path"):
        return str(existing["relative_path"])
    directory = SMB_ROOT / folder / media_type
    candidate = safe_filename(filename, message_id)
    used_paths = {str(record.get("relative_path")) for record in records.values() if record.get("relative_path")}
    relative = f"{folder}/{media_type}/{candidate}"
    if not (directory / candidate).exists() and relative not in used_paths:
        return relative
    stem = Path(candidate).stem
    suffix = Path(candidate).suffix
    safe_message_id = message_id.replace("/", "_").replace("\x00", "_")
    candidate = f"{stem}__{safe_message_id}{suffix}"
    relative = f"{folder}/{media_type}/{candidate}"
    ordinal = 2
    while (directory / candidate).exists() or relative in used_paths:
        candidate = f"{stem}__{safe_message_id}_{ordinal}{suffix}"
        relative = f"{folder}/{media_type}/{candidate}"
        ordinal += 1
    return relative


def download_media(group: Group, message_id: str, resource_id: str, temp_root: Path) -> Path:
    destination = temp_root / f"download-{uuid.uuid4().hex}"
    destination.mkdir(parents=True)
    result = run_process([
        "dws", "chat", "message", "download-media",
        "--type", "mediaId",
        "--resource-id", resource_id,
        "--message-id", message_id,
        "--open-conversation-id", group.conversation_id,
        "--output", str(destination),
        "--timeout", str(DWS_TIMEOUT_SECONDS),
    ])
    if result.returncode != 0:
        shutil.rmtree(destination, ignore_errors=True)
        raise ArchiveError(result.stderr.strip() or result.stdout.strip() or "DWS media download failed")
    files = [path for path in destination.rglob("*") if path.is_file()]
    if len(files) != 1:
        shutil.rmtree(destination, ignore_errors=True)
        raise ArchiveError(f"DWS download created {len(files)} files instead of one")
    return files[0]


def write_smb_once(source: Path, target: Path, method: str) -> None:
    """Use one direct SMB writer, never the macOS fcopyfile path or a rename."""
    if method == "dd":
        command = [
            "/bin/dd",
            f"if={source}",
            f"of={target}",
            "bs=1048576",
            "conv=fsync",
        ]
    elif method == "rsync":
        command = ["rsync", "--inplace", "--whole-file", str(source), str(target)]
    else:
        raise ArchiveError(f"unsupported SMB copy method: {method}")
    result = run_process(command)
    if result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "SMB writer returned non-zero"
        raise ArchiveError(f"SMB {method} write failed: {detail}")


def verify_smb_copy(source: Path, target: Path) -> None:
    """Confirm size plus bounded head/tail bytes before a manifest can say complete."""
    last_reason = "SMB copy did not verify"
    source_size = 0
    target_size = 0
    for settle_attempt in range(2):
        source_size = source.stat().st_size
        target_size = target.stat().st_size
        if target_size == source_size:
            sample_size = min(source_size, 64 * 1024)
            with source.open("rb") as source_handle, target.open("rb") as target_handle:
                if source_handle.read(sample_size) != target_handle.read(sample_size):
                    last_reason = "SMB copy header differs from source"
                elif source_size > sample_size:
                    source_handle.seek(-sample_size, os.SEEK_END)
                    target_handle.seek(-sample_size, os.SEEK_END)
                    if source_handle.read(sample_size) != target_handle.read(sample_size):
                        last_reason = "SMB copy tail differs from source"
                    else:
                        return
                else:
                    return
        else:
            last_reason = "SMB copy size differs from source"
        if not settle_attempt:
            time.sleep(1)
    raise ArchiveError(f"{last_reason}: source_size={source_size}, target_size={target_size}")


def verify_media_openable(target: Path, media_type: str) -> None:
    """Require the final SMB original itself to be parsable before completion."""
    if media_type == "photo":
        result = run_process(["sips", "-g", "format", "-g", "pixelWidth", "-g", "pixelHeight", str(target)])
        if result.returncode != 0:
            detail = result.stderr.strip() or result.stdout.strip() or "ImageIO could not parse media"
            raise ArchiveError(f"SMB photo cannot be opened: {detail}")
        return
    if media_type == "video":
        probe = run_process([
            "ffprobe", "-v", "error", "-show_entries", "format=format_name",
            "-of", "default=nw=1:nk=1", str(target),
        ])
        if probe.returncode != 0:
            detail = probe.stderr.strip() or probe.stdout.strip() or "ffprobe could not parse media"
            raise ArchiveError(f"SMB video cannot be opened: {detail}")
        decode = run_process([
            "ffmpeg", "-v", "error", "-i", str(target), "-map", "0:v?", "-map", "0:a?", "-f", "null", "-",
        ])
        if decode.returncode != 0:
            detail = decode.stderr.strip() or decode.stdout.strip() or "ffmpeg could not decode media"
            raise ArchiveError(f"SMB video cannot be fully decoded: {detail}")
        return
    raise ArchiveError(f"unsupported media type for openability validation: {media_type}")


def smb_original_usable(record: dict | None) -> bool:
    if not record or record.get("smb_status") != "complete":
        return False
    relative_path = str(record.get("smb_relative_path") or record.get("relative_path") or "")
    if not relative_path:
        return False
    target = SMB_ROOT / relative_path
    if not target.is_file() or target.stat().st_size != record.get("size_bytes"):
        return False
    with target.open("rb") as handle:
        sample = handle.read(min(target.stat().st_size, 64))
    return bool(sample) and any(sample)


def copy_to_smb(source: Path, target: Path, media_type: str, *, replace_existing: bool = False) -> None:
    if not has_nonzero_header(source):
        raise ArchiveError("media source is empty or zero-filled")
    if target.exists() and not replace_existing:
        raise ArchiveError("SMB target path already exists without a completed manifest record")
    last_error: OSError | ArchiveError | None = None
    for attempt, method in enumerate(SMB_COPY_METHODS):
        target_existed_before_attempt = target.exists()
        target_removed_before_copy = False
        target_written = False
        try:
            # SMB can briefly report ENOENT for an otherwise-present directory.
            # Treat directory creation as part of the same bounded write attempt,
            # rather than abandoning the entire 30-day window before the retry.
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.is_dir():
                raise ArchiveError("SMB target directory is unavailable")
            if target_existed_before_attempt:
                if not replace_existing:
                    raise ArchiveError("SMB target appeared during direct write")
                target.unlink()
                target_removed_before_copy = True
            # `os.replace` on this SMB mount can acknowledge a rename while the
            # destination exposes a stale/truncated size.  Direct buffered
            # creation is the verified path; completion is still withheld until
            # the final path itself passes the source comparison.
            write_smb_once(source, target, method)
            target_written = True
            verify_smb_copy(source, target)
            verify_media_openable(target, media_type)
            return
        except (OSError, ArchiveError) as error:
            last_error = ArchiveError(f"{method}: {error}")
            if target_written or target_removed_before_copy or not target_existed_before_attempt:
                try:
                    target.unlink()
                except FileNotFoundError:
                    pass
            if attempt + 1 < len(SMB_COPY_METHODS):
                time.sleep(2 ** attempt)
    raise ArchiveError(
        f"SMB copy did not verify after {len(SMB_COPY_METHODS)} alternating attempts: {last_error}"
    )


def put_github_media(source: Path, relative_path: str, budget: GitHubMediaBudget) -> str | None:
    if source.stat().st_size > GITHUB_MAX_BYTES:
        return "raw_over_95_mib"
    if not budget.take():
        return "github_rate_budget_exhausted"
    result = client(["put", GITHUB_AREA, f"{GITHUB_PREFIX}/{relative_path}", str(source)])
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "GitHub raw-media write failed"


def has_nonzero_header(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as handle:
        return any(handle.read(min(path.stat().st_size, 64)))


def get_github_media_for_repair(record: dict, temp_root: Path) -> Path | None:
    if record.get("github_media_status") != "complete":
        return None
    relative_path = str(record.get("relative_path") or "")
    if not relative_path:
        return None
    target = temp_root / f"github-repair-{uuid.uuid4().hex}"
    result = client(["get", GITHUB_AREA, f"{GITHUB_PREFIX}/{relative_path}", str(target)])
    if result.returncode == 0 and has_nonzero_header(target):
        return target
    target.unlink(missing_ok=True)
    return None


def media_record_id(group: Group, message_id: str, resource_id: str) -> str:
    return f"media:{group.conversation_id}:{message_id}:{resource_id}"


def is_complete(record: dict | None) -> bool:
    if not record:
        return False
    return smb_original_usable(record) and record.get("github_media_status") in {"complete", "index_only"}


def archive_media(
    group: Group,
    folder: str,
    message: dict,
    resource_id: str,
    media_type: str,
    records: dict[str, dict],
    temp_root: Path,
    apply: bool,
    counts: Counts,
    github_budget: GitHubMediaBudget,
    smb_only: bool,
) -> None:
    message_id = str(message.get("openMessageId") or "")
    if not message_id:
        raise ArchiveError("media message missing openMessageId")
    key = media_record_id(group, message_id, resource_id)
    with MANIFEST_LOCK:
        existing = records.get(key)
        if existing and smb_original_usable(existing) and (smb_only or is_complete(existing)):
            counts.skipped += 1
            return
        counts.discovered += 1
    if not apply:
        return

    downloaded: Path | None = None
    try:
        downloaded = download_media(group, message_id, resource_id, temp_root)
        with MANIFEST_LOCK:
            relative_path = choose_relative_path(
                folder,
                media_type,
                downloaded.name,
                message_id,
                records,
                existing,
            )
        target = SMB_ROOT / relative_path
        record = dict(existing or {})
        record.update({
            "record_id": key,
            "record_type": "media",
            "conversation_id": group.conversation_id,
            "folder": folder,
            "message_id": message_id,
            "resource_id": resource_id,
            "media_type": media_type,
            "message_time": str(message.get("createTime") or ""),
            "relative_path": relative_path,
            "smb_relative_path": relative_path,
            "size_bytes": downloaded.stat().st_size,
        })

        if not smb_original_usable(record):
            try:
                copy_to_smb(
                    downloaded,
                    target,
                    media_type,
                    replace_existing=target.exists() and existing is not None,
                )
            except (ArchiveError, OSError) as exc:
                record["smb_status"] = "failed"
                record["smb_error"] = str(exc)
                with MANIFEST_LOCK:
                    records[key] = record
                    append_smb_manifest_record(folder, record)
                raise ArchiveError(
                    f"{exc}; failed_media_record={key}; relative_path={relative_path}; "
                    f"source_size={record['size_bytes']}"
                ) from exc
            record["smb_status"] = "complete"
            record.pop("smb_error", None)
            with MANIFEST_LOCK:
                counts.smb_saved += 1

        github_status = str(record.get("github_media_status") or "")
        if smb_only:
            record["github_media_status"] = "pending"
            record["github_index_reason"] = "deferred_while_github_writer_active"
        elif github_status not in {"complete", "index_only"}:
            github_error = put_github_media(downloaded, relative_path, github_budget)
            if github_error:
                record["github_media_status"] = "index_only"
                record["github_index_reason"] = github_error
                with MANIFEST_LOCK:
                    counts.github_index += 1
            else:
                record["github_media_status"] = "complete"
                record.pop("github_index_reason", None)
                with MANIFEST_LOCK:
                    counts.github_raw += 1

        with MANIFEST_LOCK:
            records[key] = record
            append_smb_manifest_record(folder, record)
    finally:
        if downloaded is not None:
            shutil.rmtree(downloaded.parent, ignore_errors=True)


def window_record_id(group: Group, start: datetime, end: datetime) -> str:
    return f"window:{group.conversation_id}:{dws_time(start)}:{dws_time(end)}"


def archive_group(
    group: Group,
    windows: list[tuple[datetime, datetime]],
    temp_root: Path,
    page_size: int,
    apply: bool,
    github_budget: GitHubMediaBudget,
    smb_only: bool,
    reconcile: bool,
    workers: int = 1,
) -> Counts:
    folder = find_existing_folder(group)
    local_records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    github_records, github_read_error = get_github_manifest(folder, temp_root)
    records = merge_manifests(local_records, github_records)
    counts = Counts()
    group_key = f"group:{group.conversation_id}"
    records[group_key] = {
        "record_id": group_key,
        "record_type": "group",
        "conversation_id": group.conversation_id,
        "folder": folder,
        "group_type": group.group_type,
    }
    if apply:
        append_smb_manifest_record(folder, records[group_key])

    if github_read_error:
        print_event("github_manifest_read_unavailable", group=group.title)

    known_topic_ids: set[str] = set()
    with ThreadPoolExecutor(max_workers=max(1, workers)) as pool:

        def run_tasks(tasks: list[tuple[dict, str, str]]) -> None:
            """按批提交并发处理；批内任一失败按顺序抛出，保留窗口停止语义。"""
            for offset in range(0, len(tasks), max(1, workers)):
                batch = tasks[offset:offset + max(1, workers)]
                futures = [
                    pool.submit(
                        archive_media,
                        group, folder, message, resource_id, media_type, records,
                        temp_root, apply, window_counts, github_budget, smb_only,
                    )
                    for message, resource_id, media_type in batch
                ]
                for future in futures:
                    future.result()

        for start, end in windows:
            boundary_key = window_record_id(group, start, end)
            if records.get(boundary_key, {}).get("window_status") == "complete" and not reconcile:
                print_event("window_skipped", group=group.title, start=dws_time(start), end=dws_time(end))
                continue
            window_counts = Counts()
            try:
                tasks: list[tuple[dict, str, str]] = []
                for message in walk_window_messages(group.conversation_id, start, end, None, page_size):
                    for resource_id, media_type in classify_media(message):
                        tasks.append((message, resource_id, media_type))
                    topic_id = str(message.get("openConvThreadId") or "")
                    if topic_id:
                        known_topic_ids.add(topic_id)
                run_tasks(tasks)
                reply_tasks: list[tuple[dict, str, str]] = []
                for topic_id in known_topic_ids:
                    for reply in walk_window_messages(group.conversation_id, start, end, topic_id, page_size):
                        window_counts.topic_replies += 1
                        for resource_id, media_type in classify_media(reply):
                            reply_tasks.append((reply, resource_id, media_type))
                run_tasks(reply_tasks)
                if apply:
                    records[boundary_key] = {
                        "record_id": boundary_key,
                        "record_type": "window",
                        "conversation_id": group.conversation_id,
                        "folder": folder,
                        "start": dws_time(start),
                        "end": dws_time(end),
                        "window_status": "smb_complete_pending_github_index" if smb_only else "complete",
                    }
                    if smb_only:
                        records = persist_smb_manifest(folder, records)
                    else:
                        records, github_manifest_error = persist_manifests(folder, records, temp_root)
                        if github_manifest_error:
                            raise ArchiveError(f"github_index_unavailable: {github_manifest_error}")
                window_counts.completed_windows += 1
                print_event(
                    "window_complete",
                    group=group.title,
                    start=dws_time(start),
                    end=dws_time(end),
                    discovered=window_counts.discovered,
                    smb_saved=window_counts.smb_saved,
                    github_raw=window_counts.github_raw,
                    github_index=window_counts.github_index,
                    skipped=window_counts.skipped,
                )
            except (ArchiveError, OSError) as exc:
                window_counts.failures += 1
                window_counts.failures_by_reason.append(str(exc))
                if apply:
                    records[boundary_key] = {
                        "record_id": boundary_key,
                        "record_type": "window",
                        "conversation_id": group.conversation_id,
                        "folder": folder,
                        "start": dws_time(start),
                        "end": dws_time(end),
                        "window_status": "stopped",
                        "reason": str(exc),
                    }
                    try:
                        records = persist_smb_manifest(folder, records)
                    except (OSError, json.JSONDecodeError) as persist_error:
                        print_event(
                            "window_stop_state_unavailable",
                            group=group.title,
                            start=dws_time(start),
                            end=dws_time(end),
                            reason=str(persist_error),
                        )
                print_event("window_stopped", group=group.title, start=dws_time(start), end=dws_time(end), reason=str(exc))
                counts.merge(window_counts)
                break
            counts.merge(window_counts)
    return counts


def repair_smb_group(group: Group, temp_root: Path, *, failed_only: bool = False) -> Counts:
    """Repair only manifest-known SMB media that is missing or zero-filled."""
    folder = find_existing_folder(group)
    records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    if not records:
        raise ArchiveError("SMB manifest is unavailable for repair")
    counts = Counts()
    for record_id in sorted(records):
        record = records[record_id]
        if record.get("record_type") != "media":
            continue
        if failed_only:
            if record.get("smb_status") != "failed":
                continue
        elif smb_original_usable(record):
            continue
        relative_path = str(record.get("relative_path") or "")
        message_id = str(record.get("message_id") or "")
        resource_id = str(record.get("resource_id") or "")
        media_type = str(record.get("media_type") or "")
        if not relative_path or not message_id or not resource_id or media_type not in {"photo", "video"}:
            counts.failures += 1
            counts.failures_by_reason.append("manifest media record lacks repair identity")
            continue
        downloaded: Path | None = None
        source_kind: str | None = None
        try:
            downloaded = get_github_media_for_repair(record, temp_root)
            if downloaded is not None:
                source_kind = "github"
            else:
                downloaded = download_media(group, message_id, resource_id, temp_root)
                source_kind = "dws"
            target = SMB_ROOT / relative_path
            copy_to_smb(downloaded, target, media_type, replace_existing=target.exists())
            record["size_bytes"] = downloaded.stat().st_size
            record["smb_status"] = "complete"
            record.pop("smb_error", None)
            records[record_id] = record
            append_smb_manifest_record(folder, record)
            counts.smb_repaired += 1
            if source_kind == "github":
                counts.smb_repaired_from_github += 1
            else:
                counts.smb_repaired_from_dws += 1
        except (ArchiveError, OSError) as exc:
            counts.failures += 1
            counts.failures_by_reason.append(str(exc))
            print_event("smb_repair_item_stopped", group=group.title, reason=str(exc))
        finally:
            if downloaded is not None:
                if source_kind == "github":
                    downloaded.unlink(missing_ok=True)
                else:
                    shutil.rmtree(downloaded.parent, ignore_errors=True)
    persist_smb_manifest(folder, records)
    return counts


def sync_github_index_group(group: Group, temp_root: Path) -> Counts:
    """Publish durable GitHub routes for SMB-complete media without re-downloading it.

    This mode deliberately never attempts a raw-media upload.  It is used only
    after an SMB-only historical pass, when the active raw-media GitHub writer
    has finished.  That keeps one GitHub manifest writer at a time.
    """
    folder = find_existing_folder(group)
    local_records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    if not local_records:
        raise ArchiveError("SMB manifest is unavailable for GitHub index synchronization")
    github_records, github_read_error = get_github_manifest(folder, temp_root)
    if github_read_error:
        raise ArchiveError(f"github_index_unavailable: {github_read_error}")
    records = merge_manifests(local_records, github_records)
    counts = Counts()
    for record in records.values():
        if record.get("record_type") != "media" or not smb_original_usable(record):
            continue
        github_status = str(record.get("github_media_status") or "")
        if github_status in {"complete", "index_only"}:
            continue
        record["github_media_status"] = "index_only"
        record["github_index_reason"] = "github_raw_deferred_for_serial_writer"
        counts.github_index += 1

    # Keep SMB explicitly pending until the corresponding GitHub index PUT has
    # succeeded.  A failed PUT therefore cannot be mistaken for a completed
    # dual-destination checkpoint.
    records = persist_smb_manifest(folder, records)
    completed_window_ids: list[str] = []
    for record_id, record in records.items():
        if record.get("record_type") == "window" and record.get("window_status") == "smb_complete_pending_github_index":
            record["window_status"] = "complete"
            completed_window_ids.append(record_id)
    github_manifest_error = put_github_manifest(folder, manifest_text(records), temp_root)
    if github_manifest_error:
        raise ArchiveError(f"github_index_unavailable: {github_manifest_error}")
    records = persist_smb_manifest(folder, records)
    counts.completed_windows = len(completed_window_ids)
    return counts


@dataclass
class AuditBucket:
    count: int = 0
    earliest: str | None = None
    latest: str | None = None
    reasons: dict[str, int] = field(default_factory=dict)

    def add(self, message_time: str, reason: str | None = None) -> None:
        self.count += 1
        if not self.earliest or message_time < self.earliest:
            self.earliest = message_time
        if not self.latest or message_time > self.latest:
            self.latest = message_time
        if reason:
            self.reasons[reason] = self.reasons.get(reason, 0) + 1

    def as_dict(self) -> dict[str, object]:
        result: dict[str, object] = {
            "count": self.count,
            "from": self.earliest,
            "to": self.latest,
        }
        if self.reasons:
            result["reasons"] = dict(sorted(self.reasons.items()))
        return result


def audit_media_status(record: dict | None) -> tuple[str, str | None]:
    if not record:
        return "unresolved", "manifest_record_missing"
    if not smb_original_usable(record):
        return "unresolved", "smb_original_missing_or_zero_filled"
    if record.get("github_media_status") not in {"complete", "index_only"}:
        return "unresolved", str(record.get("github_index_reason") or "github_index_pending")
    return "complete", None


def audit_group(
    group: Group,
    windows: list[tuple[datetime, datetime]],
    page_size: int,
) -> dict[str, dict[str, dict[str, object]]]:
    folder = find_existing_folder(group)
    records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    buckets = {
        media_type: {"complete": AuditBucket(), "unresolved": AuditBucket()}
        for media_type in ("photo", "video")
    }
    seen_media: set[str] = set()

    def inspect_message(message: dict) -> None:
        message_id = str(message.get("openMessageId") or "")
        message_time = str(message.get("createTime") or "")
        if not message_id or not message_time:
            raise PagingError("media message missing openMessageId or createTime")
        for resource_id, media_type in classify_media(message):
            record_id = media_record_id(group, message_id, resource_id)
            if record_id in seen_media:
                continue
            seen_media.add(record_id)
            status, reason = audit_media_status(records.get(record_id))
            buckets[media_type][status].add(message_time, reason)

    known_topic_ids: set[str] = set()
    for start, end in windows:
        for message in walk_window_messages(group.conversation_id, start, end, None, page_size):
            inspect_message(message)
            topic_id = str(message.get("openConvThreadId") or "")
            if topic_id:
                known_topic_ids.add(topic_id)
        for topic_id in known_topic_ids:
            for reply in walk_window_messages(group.conversation_id, start, end, topic_id, page_size):
                inspect_message(reply)
    return {
        media_type: {status: bucket.as_dict() for status, bucket in statuses.items()}
        for media_type, statuses in buckets.items()
    }


def make_windows(start: datetime, end: datetime, window_days: int) -> list[tuple[datetime, datetime]]:
    if start >= end:
        raise ArchiveError("start must be before end")
    if window_days < 1 or window_days > 30:
        raise ArchiveError("window-days must be between 1 and 30")
    windows: list[tuple[datetime, datetime]] = []
    cursor = start
    while cursor < end:
        next_cursor = min(cursor + timedelta(days=window_days), end)
        windows.append((cursor, next_cursor))
        cursor = next_cursor
    return windows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Archive DWS media from explicitly allowed internal groups.")
    parser.add_argument("--allow-title", action="append", required=True, help="Exact DWS group title; repeat for every authorized group.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--start", help="Inclusive start time in Asia/Shanghai, YYYY-MM-DD HH:MM:SS.")
    parser.add_argument("--window-days", type=int, default=30)
    parser.add_argument("--end", help="Frozen end time in Asia/Shanghai, YYYY-MM-DD HH:MM:SS.")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument(
        "--workers",
        type=int,
        default=1,
        help="Concurrent media pipeline workers (downloads in parallel; manifest writes stay serial).",
    )
    parser.add_argument(
        "--github-media-budget",
        type=int,
        help="Maximum raw-media uploads attempted through the current GitHub REST quota. Omit for no cap.",
    )
    parser.add_argument("--smb-only", action="store_true", help="Write SMB originals and durable SMB manifests only; defer GitHub media and index.")
    parser.add_argument(
        "--sync-github-index",
        action="store_true",
        help="For SMB-complete pending records, write GitHub route manifests only; requires --apply.",
    )
    parser.add_argument(
        "--audit",
        action="store_true",
        help="Read the specified DWS range and print per-group photo/video completion statistics; requires --dry-run.",
    )
    parser.add_argument(
        "--reconcile",
        action="store_true",
        help="Re-read completed windows and add only manifest-missing media; requires --apply.",
    )
    parser.add_argument(
        "--repair-smb",
        action="store_true",
        help="Re-download only manifest-known SMB files that are missing or zero-filled; requires --apply.",
    )
    parser.add_argument(
        "--failed-only",
        action="store_true",
        help="With --repair-smb, repair only manifest records explicitly marked smb_status=failed.",
    )
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.page_size < 1:
        raise ArchiveError("page-size must be positive")
    if args.workers < 1 or args.workers > 8:
        raise ArchiveError("workers must be between 1 and 8")
    if args.github_media_budget is not None and args.github_media_budget < 0:
        raise ArchiveError("github-media-budget must not be negative")
    if args.sync_github_index and args.audit:
        raise ArchiveError("--sync-github-index and --audit cannot be used together")
    if args.sync_github_index and not args.apply:
        raise ArchiveError("--sync-github-index requires --apply")
    if args.audit and not args.dry_run:
        raise ArchiveError("--audit requires --dry-run")
    if args.reconcile and not args.apply:
        raise ArchiveError("--reconcile requires --apply")
    if args.repair_smb and not args.apply:
        raise ArchiveError("--repair-smb requires --apply")
    if args.failed_only and not args.repair_smb:
        raise ArchiveError("--failed-only requires --repair-smb")
    if (args.sync_github_index or args.audit) and args.smb_only:
        raise ArchiveError("--smb-only only applies to an archive --apply run")
    if args.reconcile and (args.sync_github_index or args.audit):
        raise ArchiveError("--reconcile only applies to an archive --apply run")
    if args.repair_smb and (args.sync_github_index or args.audit or args.reconcile or args.smb_only):
        raise ArchiveError("--repair-smb cannot be combined with another operation")
    if not SMB_ROOT.is_dir():
        raise ArchiveError(f"SMB root is unavailable: {SMB_ROOT}")
    if not PRIVATE_DB_CLIENT.is_file():
        raise ArchiveError(f"Private-Database client is unavailable: {PRIVATE_DB_CLIENT}")
    end = parse_time(args.end) if args.end else datetime.now(TIMEZONE).replace(microsecond=0)
    if args.start:
        start = parse_time(args.start)
    else:
        if args.days < 1 or args.days > 90:
            raise ArchiveError("days must be between 1 and 90 unless --start is supplied")
        start = end - timedelta(days=args.days)
    windows = make_windows(start, end, args.window_days)
    groups = select_groups(args.allow_title)
    operation = "audit" if args.audit else "sync_github_index" if args.sync_github_index else "repair_smb" if args.repair_smb else "archive"
    print_event(
        "run_started",
        mode="apply" if args.apply else "dry_run",
        operation=operation,
        groups=len(groups),
        start=dws_time(start),
        end=dws_time(end),
        windows=len(windows),
    )
    total = Counts()
    github_budget = GitHubMediaBudget(args.github_media_budget)
    with tempfile.TemporaryDirectory(prefix="kmvideo-dws-") as temporary:
        temp_root = Path(temporary)
        for group in groups:
            try:
                if args.repair_smb:
                    group_counts = repair_smb_group(group, temp_root, failed_only=args.failed_only)
                    print_event(
                        "smb_repair_group",
                        group=group.title,
                        smb_repaired=group_counts.smb_repaired,
                        smb_repaired_from_github=group_counts.smb_repaired_from_github,
                        smb_repaired_from_dws=group_counts.smb_repaired_from_dws,
                        failures=group_counts.failures,
                    )
                elif args.sync_github_index:
                    group_counts = sync_github_index_group(group, temp_root)
                    print_event(
                        "github_index_synced",
                        group=group.title,
                        github_index=group_counts.github_index,
                        completed_windows=group_counts.completed_windows,
                    )
                elif args.audit:
                    report = audit_group(group, windows, args.page_size)
                    group_counts = Counts()
                    print_event("audit_group", group=group.title, **report)
                else:
                    group_counts = archive_group(
                        group, windows, temp_root, args.page_size, args.apply, github_budget, args.smb_only, args.reconcile,
                        workers=args.workers,
                    )
            except (ArchiveError, OSError) as exc:
                group_counts = Counts(failures=1, failures_by_reason=[str(exc)])
                print_event("audit_group_stopped" if args.audit else "group_stopped", group=group.title, reason=str(exc))
            total.merge(group_counts)
    print_event(
        "run_finished",
        mode="apply" if args.apply else "dry_run",
        operation=operation,
        groups=len(groups),
        discovered=total.discovered,
        smb_saved=total.smb_saved,
        smb_repaired=total.smb_repaired,
        smb_repaired_from_github=total.smb_repaired_from_github,
        smb_repaired_from_dws=total.smb_repaired_from_dws,
        github_raw=total.github_raw,
        github_index=total.github_index,
        skipped=total.skipped,
        failures=total.failures,
        completed_windows=total.completed_windows,
        github_media_budget_remaining=github_budget.remaining,
        temp_cleanup="complete",
    )
    return 1 if total.failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ArchiveError as exc:
        print_event("run_stopped", reason=str(exc), temp_cleanup="complete")
        raise SystemExit(1)
