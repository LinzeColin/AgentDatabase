#!/usr/bin/env python3
"""DWS internal-group FILE archive runner (KMFile).

与 archive_internal_media.py 的同位体，只处理钉钉「文件」消息：

    [文件] 2026投标记录-武汉开明.xlsx fileId: R4GpnMqJzGynwDqYiqya5wYb8Ke0xjE3

传输层与媒体版完全不同：
  媒体  [图片消息](mediaId=...)  → dws chat message download-media --type mediaId
  文件  [文件] name fileId: xxx  → dws drive download --node <fileId>

服务端 `dws drive info --node <fileId>` 直接返回 md5（base64 of MD5 digest）与
fileSize，因此本脚本的完整性校验比媒体版更强：字节数 + 头尾抽样 + **服务端 md5 逐份复核**。

音视频扩展名的文件消息不归 KMFile：只登记进 `待转KMVideo.csv` 交接清单，
由 KMVideo 侧收（媒体版已打补丁认 `[文件]` 传输）。

All runtime state is held in the two durable manifests. The process only creates
an operating-system temporary directory and removes it before exit.
"""

from __future__ import annotations

import argparse
import base64
import csv
import hashlib
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
import zipfile
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


def _resolve_smb_root(sub: str) -> Path:
    """SMB 根动态解析：盘挂在哪都能跑。

    实测事故（260820）：盘从 `/Volumes/share` 换挂到 `~/mnt/share` 之后，写死路径的
    两个 skill 直接报 `SMB root is unavailable` 起不来 —— 定时任务会天天空转失败。
    顺序：`KM_SMB_ROOT` 环境变量 → /Volumes/share → ~/mnt/share → `mount` 输出里
    任何 smbfs 挂载点。都不命中时返回第一个候选，让后续检查报出可读的错。
    """
    candidates: list[Path] = []
    env = os.environ.get("KM_SMB_ROOT", "").strip()
    if env:
        candidates.append(Path(env).expanduser())
    candidates.append(Path("/Volumes/share"))
    candidates.append(Path.home() / "mnt" / "share")
    try:
        out = subprocess.run(["mount"], capture_output=True, text=True, timeout=10).stdout
        for line in out.splitlines():
            if "smbfs" in line and " on " in line:
                point = line.split(" on ", 1)[1].split(" (")[0].strip()
                if point:
                    candidates.append(Path(point))
    except (OSError, subprocess.SubprocessError):
        pass
    tail = Path("03_资料库") / "MetaData" / "IDS_MetaData" / sub
    seen: set[str] = set()
    for base in candidates:
        key = str(base)
        if key in seen:
            continue
        seen.add(key)
        target = base / tail
        if target.is_dir():
            return target
    return candidates[0] / tail

PRIVATE_DB_CLIENT = ROOT / "KMDatabase" / "machine" / "tools" / "private_db_client.py"
SMB_ROOT = _resolve_smb_root("KMFile")
GITHUB_AREA = "Private-KMDatabase"
GITHUB_PREFIX = "KMFile"
GITHUB_MAX_BYTES = 95 * 1024 * 1024
DWS_TIMEOUT_SECONDS = 60
MANIFEST_NAME = ".manifest.jsonl"
TIMEZONE = ZoneInfo("Asia/Shanghai")

# 钉钉文件消息体，实测格式（v0.0.0.1 冻结）：
#   [文件] <文件名> fileId: <dentryUuid> 注意：如需下载使用dws drive download命令下载
FILE_MSG_RE = re.compile(r"^\[文件\]\s+(.+?)\s+fileId:\s*(\S+)")
# 媒体版的 mediaId 正则，仅用于判定「这条消息属于 KMVideo 而不是 KMFile」
MEDIA_ID_RE = re.compile(r"mediaId=([^\s)\]]+)")

# 音视频一律不进 KMFile，交回 KMVideo（拍板方案 A）
AV_EXTENSIONS = {
    "mp4", "mov", "avi", "mkv", "wmv", "flv", "m4v", "3gp", "mpg", "mpeg", "webm",
    "mp3", "wav", "m4a", "aac", "amr", "flac", "wma", "ogg",
}
# OOXML / WPS 新版都是 zip 容器，可读性校验用 zipfile 判真
ZIP_CONTAINER_EXTENSIONS = {"xlsx", "docx", "pptx", "et", "wps", "dps", "zip", "apk", "jar"}
SMB_COPY_METHODS = ("dd", "rsync", "dd", "rsync")

# 单进程内并发下载时，records 字典与 manifest 追加仍保持单一写入者语义。
MANIFEST_LOCK = threading.Lock()

# 连续这么多个窗口失败就放弃该群本轮（防止对一个系统性坏掉的群空转整轮）
MAX_CONSECUTIVE_WINDOW_FAILURES = 3


class ArchiveError(RuntimeError):
    pass


class PagingError(ArchiveError):
    pass


class PermanentFileError(ArchiveError):
    """DWS 侧已删除/已过期/返回空文件 —— 重试多少次都不会好。

    窗口是从旧到新推进的，一个永久坏件按普通失败处理就会把该群后面所有窗口全堵死。
    实测武汉开明 ~9 个文件（drive resource.notFound / 返回空文件）正是如此。
    """


EMPTY_FILE_MD5_B64 = "1B2M2Y8AsgTpgAmY7PhCfg=="
PERMANENT_ERROR_MARKERS = (
    "resource.notfound", "notfound", "not found", "404",
    "已删除", "已过期", "已撤回", "不存在",
)


def is_permanent_failure(detail: str) -> bool:
    lowered = detail.lower()
    return any(marker in lowered for marker in PERMANENT_ERROR_MARKERS)


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
    "池州天赐20260415",
    "福建韩研2026.4.30",
    "阜阳电力齿轮修复2025.10.31",
    "新洋丰焊补2026.5.4",
    "山东日照检修群",
    "芜湖新兴铸管2026.3.31",
    "萍乡钢铁2026.6.3",
    "湘东区萍乡钢铁20260622",
    "湖南湘潭钢铁2026.3.6",
    "福建鼎信实业2026.6.4",
    "新都化工1500吨大颗粒项目",
    "新疆宜化技改2026",
    "内蒙古金鄂博氟化工2026.7.5",
    "赣锋锂业2026.7.27",
    "松滋葛洲坝小齿调整（原为调窑）2026.06.28",
    "盐湖海纳2026.1.22",
    "盐湖海纳大齿圈小齿更换2026.7.5",
    "汝州天瑞2#线3档托轮2次返修2026.1.16",
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
    unavailable: int = 0
    handoff_av: int = 0
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
        self.unavailable += other.unavailable
        self.handoff_av += other.handoff_av
        self.failures += other.failures
        self.topic_replies += other.topic_replies
        self.completed_windows += other.completed_windows
        self.failures_by_reason.extend(other.failures_by_reason)


@dataclass
class GitHubFileBudget:
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


def _resolve_binary(name: str) -> str:
    """cron 下 PATH 被精简，`dws` 在 ~/.local/bin 会找不到（实测浪费 50 分钟重试）。"""
    found = shutil.which(name)
    if found:
        return found
    for candidate in (
        Path.home() / ".local" / "bin" / name,
        Path("/opt/homebrew/bin") / name,
        Path("/usr/local/bin") / name,
    ):
        if candidate.is_file() and os.access(candidate, os.X_OK):
            return str(candidate)
    return name


DWS_BIN = _resolve_binary("dws")


def run_process(args: list[str]) -> subprocess.CompletedProcess[str]:
    if args and args[0] == "dws":
        args = [DWS_BIN, *args[1:]]
    return subprocess.run(
        args,
        cwd=ROOT if ROOT.is_dir() else Path.home(),
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


def md5_b64(path: Path) -> str:
    """服务端 md5 是 base64(MD5 digest)，本机按同一编码算，实测逐字节相等。"""
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return base64.b64encode(digest.digest()).decode()


def extension_of(name: str) -> str:
    suffix = Path(name).suffix
    return suffix[1:].lower() if suffix else ""


def read_manifest(path: Path) -> dict[str, dict]:
    if not path.exists() or path.stat().st_size == 0:
        backup = path.with_name(path.name + ".bak")
        if backup.is_file() and backup.stat().st_size > 0:
            print_event("manifest_recovered_from_backup", path=str(path))
            path = backup
        else:
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
    for key, kind in (("smb_status", "smb"), ("github_file_status", "github")):
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


MANIFEST_BACKUP_SUFFIX = ".bak"


def manifest_partial_residue(folder: str) -> list[str]:
    """`.partial-*` 残留 = 上一轮写 manifest 时被硬杀过，该群需要重跑核对。"""
    directory = SMB_ROOT / folder
    if not directory.is_dir():
        return []
    return sorted(p.name for p in directory.glob(f"*{MANIFEST_NAME}.partial-*"))


def atomic_write(path: Path, content: str) -> None:
    """SMB 上的 rename 实测会随机返回 EIO（KMVideo 目录同样复现），因此不走 os.replace。

    改为：写本机临时文件 → `rsync --inplace --whole-file` 落 SMB → 校验字节数。
    这条路径同时满足硬约束 7（禁 Python 直写与 shutil 快速路径），且不依赖 rename。
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    # 覆盖前先留一份 .bak：rsync --inplace 是直写目标，跑到一半被 SIGKILL 会留下截断文件。
    # 媒体版实测有过「7 个群 manifest 整个消失、只能逐群重建」的事故，这里不重蹈。
    if path.is_file() and path.stat().st_size > 0:
        backup = path.with_name(path.name + MANIFEST_BACKUP_SUFFIX)
        try:
            result = run_process(["rsync", "--inplace", "--whole-file", str(path), str(backup)])
            if result.returncode != 0:
                print_event("manifest_backup_unavailable", path=str(path), reason=result.stderr.strip()[:200])
        except OSError as exc:
            print_event("manifest_backup_unavailable", path=str(path), reason=str(exc))
    data = content.encode("utf-8")
    with tempfile.NamedTemporaryFile("wb", delete=False, suffix=".jsonl") as handle:
        handle.write(data)
        staged = Path(handle.name)
    try:
        last = ""
        for attempt in range(3):
            result = run_process(["rsync", "--inplace", "--whole-file", str(staged), str(path)])
            if result.returncode == 0 and path.is_file() and path.stat().st_size == len(data):
                return
            last = result.stderr.strip() or result.stdout.strip() or "size mismatch after rsync"
            time.sleep(2 ** attempt)
        raise ArchiveError(f"SMB manifest write did not verify: {path}: {last}")
    finally:
        staged.unlink(missing_ok=True)


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
    """
    path = SMB_ROOT / folder / MANIFEST_NAME
    current = read_manifest(path)
    merged = {**current, **records}
    atomic_write(path, manifest_text(merged))
    return merged


def append_smb_manifest_record(folder: str, record: dict) -> None:
    """追加式写入，SMB 上实测可用；瞬断重试 3 次后才认失败。"""
    path = SMB_ROOT / folder / MANIFEST_NAME
    line = json.dumps(record, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n"
    last: OSError | None = None
    for attempt in range(3):
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as handle:
                handle.write(line)
            return
        except OSError as error:
            last = error
            time.sleep(2 ** attempt)
    raise ArchiveError(f"SMB manifest append failed: {path}: {last}")


def persist_manifests(folder: str, records: dict[str, dict], temp_root: Path) -> tuple[dict[str, dict], str | None]:
    merged = persist_smb_manifest(folder, records)
    return merged, put_github_manifest(folder, manifest_text(merged), temp_root)


def find_existing_folder(group: Group) -> str:
    direct = SMB_ROOT / group.title
    if direct.exists():
        return group.title
    if not SMB_ROOT.is_dir():
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


def classify_files(message: dict) -> list[tuple[str, str]]:
    """返回 [(file_id, file_name)]。只认 `[文件]` 消息；mediaId 消息属于 KMVideo。"""
    content = str(message.get("content") or "")
    match = FILE_MSG_RE.match(content.strip())
    if not match:
        return []
    file_name = match.group(1).strip()
    file_id = match.group(2).strip()
    if not file_name or not file_id:
        return []
    return [(file_id, file_name)]


def safe_filename(name: str, message_id: str) -> str:
    candidate = Path(name).name.replace("\x00", "_").replace("/", "_")
    if candidate in {"", ".", ".."}:
        candidate = f"file-{message_id.replace('/', '_')}"
    return candidate


def choose_relative_path(
    folder: str,
    filename: str,
    message_id: str,
    records: dict[str, dict],
    existing: dict | None,
) -> str:
    if existing and existing.get("relative_path"):
        return str(existing["relative_path"])
    directory = SMB_ROOT / folder / "file"
    candidate = safe_filename(filename, message_id)
    used_paths = {str(record.get("relative_path")) for record in records.values() if record.get("relative_path")}
    relative = f"{folder}/file/{candidate}"
    if not (directory / candidate).exists() and relative not in used_paths:
        return relative
    stem = Path(candidate).stem
    suffix = Path(candidate).suffix
    safe_message_id = message_id.replace("/", "_").replace("\x00", "_")
    candidate = f"{stem}__{safe_message_id}{suffix}"
    relative = f"{folder}/file/{candidate}"
    ordinal = 2
    while (directory / candidate).exists() or relative in used_paths:
        candidate = f"{stem}__{safe_message_id}_{ordinal}{suffix}"
        relative = f"{folder}/file/{candidate}"
        ordinal += 1
    return relative


def drive_info(file_id: str) -> dict:
    """服务端元数据：name / extension / fileSize / md5 / spaceId / status。

    读一次 info 就能拿到 md5 与字节数，因此存在性与完整性判定**不需要整包下载**
    （云成本红线：禁止整包下载做存在性校验）。
    """
    return dws_json(["drive", "info", "--node", file_id])


def download_file(file_id: str, temp_root: Path) -> Path:
    destination = temp_root / f"download-{uuid.uuid4().hex}"
    destination.mkdir(parents=True)
    result = run_process([
        "dws", "drive", "download",
        "--node", file_id,
        "--output", str(destination) + os.sep,
        "--timeout", str(DWS_TIMEOUT_SECONDS),
    ])
    if result.returncode != 0:
        shutil.rmtree(destination, ignore_errors=True)
        detail = result.stderr.strip() or result.stdout.strip() or "DWS drive download failed"
        raise (PermanentFileError if is_permanent_failure(detail) else ArchiveError)(detail)
    files = [path for path in destination.rglob("*") if path.is_file()]
    if len(files) != 1:
        shutil.rmtree(destination, ignore_errors=True)
        raise ArchiveError(f"DWS download created {len(files)} files instead of one")
    if not has_nonzero_header(files[0]):
        shutil.rmtree(destination, ignore_errors=True)
        raise PermanentFileError("DWS returned an empty file (资源已在钉钉侧删除或过期)")
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
    for settle_attempt in range(4):
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
        # SMB 写后 stat 会短暂返回旧尺寸，实测「size differs」多数是延迟不是数据坏。
        # 沉降四次带退避，仍不符才认失败。
        time.sleep(2 ** settle_attempt)
    raise ArchiveError(f"{last_reason}: source_size={source_size}, target_size={target_size}")


def verify_server_md5(target: Path, expected_md5: str) -> None:
    """文件版独有：落地件必须与服务端 md5 逐字节等价，媒体版没有这一层。"""
    if not expected_md5:
        return
    actual = md5_b64(target)
    if actual != expected_md5:
        raise ArchiveError(f"SMB copy md5 differs from server: server={expected_md5}, local={actual}")


def verify_file_readable(target: Path, extension: str) -> None:
    """落地件本身必须能被解析，而不是只看字节数对得上。

    只用本机零依赖手段：zip 容器用 zipfile 判真，PDF 校头部魔数，其余校非零头部。
    """
    if target.stat().st_size == 0:
        raise ArchiveError("SMB file is empty")
    if extension in ZIP_CONTAINER_EXTENSIONS:
        if not zipfile.is_zipfile(target):
            # 旧版 .doc/.xls/.et 是二进制格式，不是 zip；只有明确的 OOXML 才强制。
            if extension in {"xlsx", "docx", "pptx"}:
                raise ArchiveError(f"SMB {extension} is not a readable zip container")
            return
        with zipfile.ZipFile(target) as archive:
            broken = archive.testzip()
            if broken is not None:
                raise ArchiveError(f"SMB {extension} zip member is corrupt: {broken}")
        return
    if extension == "pdf":
        with target.open("rb") as handle:
            if handle.read(5) != b"%PDF-":
                raise ArchiveError("SMB pdf lacks the %PDF- header")
        return
    if not has_nonzero_header(target):
        raise ArchiveError("SMB file header is zero-filled")


RENAME_MAP_CSV = SMB_ROOT / "原名新名映射.csv"
_RENAME_MAP: dict[tuple[str, str], str] | None = None
_RENAME_MAP_MTIME: float = -1.0


def rename_map() -> dict[tuple[str, str], str]:
    """(项目, 原文件名) → 现用文件名。按 mtime 缓存，改名后自动失效重载。

    `.manifest.jsonl` 永远记原名（硬约束 2 禁止改写），所以改名之后
    `SMB_ROOT/relative_path` 必然不存在。若不回查这张映射表，归档器会把
    「已经落地并改过名的文件」当成缺失，每轮重下一遍——纯浪费带宽和时间。
    """
    global _RENAME_MAP, _RENAME_MAP_MTIME
    try:
        mtime = RENAME_MAP_CSV.stat().st_mtime
    except OSError:
        _RENAME_MAP, _RENAME_MAP_MTIME = {}, -1.0
        return _RENAME_MAP
    if _RENAME_MAP is not None and mtime == _RENAME_MAP_MTIME:
        return _RENAME_MAP
    mapping: dict[tuple[str, str], str] = {}
    try:
        with RENAME_MAP_CSV.open(encoding="utf-8-sig", newline="") as handle:
            for row in csv.DictReader(handle):
                old = str(row.get("原文件名") or "").strip()
                new = str(row.get("新文件名") or "").strip()
                folder = str(row.get("项目") or "").strip()
                if folder and old and new and old != new:
                    mapping[(folder, old)] = new
    except (OSError, csv.Error):
        mapping = {}
    _RENAME_MAP, _RENAME_MAP_MTIME = mapping, mtime
    return mapping


def resolve_current_path(record: dict) -> Path | None:
    """返回该记录当前在磁盘上的真实路径（原名优先，其次查改名映射）。"""
    relative_path = str(record.get("smb_relative_path") or record.get("relative_path") or "")
    if not relative_path:
        return None
    target = SMB_ROOT / relative_path
    if target.is_file():
        return target
    folder = str(record.get("folder") or relative_path.split("/")[0])
    new_name = rename_map().get((folder, os.path.basename(relative_path)))
    if not new_name:
        return None
    renamed = SMB_ROOT / folder / "file" / new_name
    return renamed if renamed.is_file() else None


def smb_original_usable(record: dict | None) -> bool:
    if not record or record.get("smb_status") != "complete":
        return False
    target = resolve_current_path(record)
    if target is None or target.stat().st_size != record.get("size_bytes"):
        return False
    with target.open("rb") as handle:
        sample = handle.read(min(target.stat().st_size, 64))
    return bool(sample) and any(sample)


def copy_to_smb(
    source: Path,
    target: Path,
    extension: str,
    expected_md5: str,
    *,
    replace_existing: bool = False,
) -> None:
    if not has_nonzero_header(source):
        raise ArchiveError("file source is empty or zero-filled")
    if target.exists() and not replace_existing:
        raise ArchiveError("SMB target path already exists without a completed manifest record")
    last_error: OSError | ArchiveError | None = None
    for attempt, method in enumerate(SMB_COPY_METHODS):
        target_existed_before_attempt = target.exists()
        target_removed_before_copy = False
        target_written = False
        try:
            # SMB can briefly report ENOENT for an otherwise-present directory.
            target.parent.mkdir(parents=True, exist_ok=True)
            if not target.parent.is_dir():
                raise ArchiveError("SMB target directory is unavailable")
            if target_existed_before_attempt:
                if not replace_existing:
                    raise ArchiveError("SMB target appeared during direct write")
                target.unlink()
                target_removed_before_copy = True
            write_smb_once(source, target, method)
            target_written = True
            verify_smb_copy(source, target)
            verify_server_md5(target, expected_md5)
            verify_file_readable(target, extension)
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


def put_github_file(source: Path, relative_path: str, budget: GitHubFileBudget) -> str | None:
    if source.stat().st_size > GITHUB_MAX_BYTES:
        return "raw_over_95_mib"
    if not budget.take():
        return "github_rate_budget_exhausted"
    result = client(["put", GITHUB_AREA, f"{GITHUB_PREFIX}/{relative_path}", str(source)])
    if result.returncode == 0:
        return None
    return result.stderr.strip() or result.stdout.strip() or "GitHub raw-file write failed"


def has_nonzero_header(path: Path) -> bool:
    if not path.is_file() or path.stat().st_size == 0:
        return False
    with path.open("rb") as handle:
        return any(handle.read(min(path.stat().st_size, 64)))


def get_github_file_for_repair(record: dict, temp_root: Path) -> Path | None:
    if record.get("github_file_status") != "complete":
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


def file_record_id(group: Group, message_id: str, file_id: str) -> str:
    return f"file:{group.conversation_id}:{message_id}:{file_id}"


def handoff_record_id(group: Group, message_id: str, file_id: str) -> str:
    return f"handoff:{group.conversation_id}:{message_id}:{file_id}"


def is_complete(record: dict | None) -> bool:
    if not record:
        return False
    if record.get("smb_status") == "unavailable":
        return True  # 钉钉侧已删，永远拿不到；算已处置，进待办不进缺失
    return smb_original_usable(record) and record.get("github_file_status") in {"complete", "index_only"}


def record_av_handoff(
    group: Group,
    folder: str,
    message: dict,
    file_id: str,
    file_name: str,
    records: dict[str, dict],
    apply: bool,
    counts: Counts,
) -> None:
    """音视频不进 KMFile：登记为交接记录，由 KMVideo 侧收。"""
    message_id = str(message.get("openMessageId") or "")
    key = handoff_record_id(group, message_id, file_id)
    with MANIFEST_LOCK:
        if key in records:
            counts.skipped += 1
            return
        counts.handoff_av += 1
    if not apply:
        return
    record = {
        "record_id": key,
        "record_type": "handoff_av",
        "conversation_id": group.conversation_id,
        "folder": folder,
        "message_id": message_id,
        "file_id": file_id,
        "file_name": file_name,
        "extension": extension_of(file_name),
        "message_time": str(message.get("createTime") or ""),
        "sender": str(message.get("sender") or ""),
        "handoff_target": "KMVideo",
        "handoff_status": "pending",
    }
    with MANIFEST_LOCK:
        records[key] = record
        append_smb_manifest_record(folder, record)


def archive_file(
    group: Group,
    folder: str,
    message: dict,
    file_id: str,
    file_name: str,
    records: dict[str, dict],
    temp_root: Path,
    apply: bool,
    counts: Counts,
    github_budget: GitHubFileBudget,
    smb_only: bool,
) -> None:
    message_id = str(message.get("openMessageId") or "")
    if not message_id:
        raise ArchiveError("file message missing openMessageId")
    key = file_record_id(group, message_id, file_id)
    with MANIFEST_LOCK:
        existing = records.get(key)
        if existing and existing.get("smb_status") == "unavailable":
            counts.unavailable += 1
            return
        if existing and smb_original_usable(existing) and (smb_only or is_complete(existing)):
            counts.skipped += 1
            return
        counts.discovered += 1
    if not apply:
        return

    downloaded: Path | None = None
    try:
        try:
            info = drive_info(file_id)
        except ArchiveError:
            info = {}
        server_md5 = str(info.get("md5") or "")
        server_size = info.get("fileSize")
        extension = str(info.get("extension") or extension_of(file_name)).lower()

        try:
            downloaded = download_file(file_id, temp_root)
        except PermanentFileError as exc:
            record = dict(existing or {})
            record.update({
                "record_id": key, "record_type": "file",
                "conversation_id": group.conversation_id, "folder": folder,
                "message_id": message_id, "file_id": file_id, "file_name": file_name,
                "extension": extension_of(file_name),
                "message_time": str(message.get("createTime") or ""),
                "sender": str(message.get("sender") or ""),
                "smb_status": "unavailable", "smb_error": str(exc),
            })
            with MANIFEST_LOCK:
                records[key] = record
                append_smb_manifest_record(folder, record)
                counts.unavailable += 1
            print_event("file_unavailable", group=group.title, file_name=file_name,
                        file_id=file_id, reason=str(exc))
            return
        downloaded_size = downloaded.stat().st_size
        if isinstance(server_size, int) and server_size != downloaded_size:
            raise ArchiveError(
                f"download size differs from server: server={server_size}, local={downloaded_size}")
        if server_md5:
            local_md5 = md5_b64(downloaded)
            if local_md5 != server_md5:
                raise ArchiveError(f"download md5 differs from server: server={server_md5}, local={local_md5}")

        with MANIFEST_LOCK:
            relative_path = choose_relative_path(folder, file_name, message_id, records, existing)
        target = SMB_ROOT / relative_path
        record = dict(existing or {})
        record.update({
            "record_id": key,
            "record_type": "file",
            "conversation_id": group.conversation_id,
            "folder": folder,
            "message_id": message_id,
            "file_id": file_id,
            "file_name": file_name,
            "extension": extension,
            "message_time": str(message.get("createTime") or ""),
            "sender": str(message.get("sender") or ""),
            "relative_path": relative_path,
            "smb_relative_path": relative_path,
            "size_bytes": downloaded_size,
            "md5": server_md5 or md5_b64(downloaded),
        })

        if not smb_original_usable(record):
            try:
                copy_to_smb(
                    downloaded,
                    target,
                    extension,
                    record["md5"],
                    replace_existing=target.exists() and existing is not None,
                )
            except (ArchiveError, OSError) as exc:
                record["smb_status"] = "failed"
                record["smb_error"] = str(exc)
                with MANIFEST_LOCK:
                    records[key] = record
                    append_smb_manifest_record(folder, record)
                raise ArchiveError(
                    f"{exc}; failed_file_record={key}; relative_path={relative_path}; "
                    f"source_size={record['size_bytes']}"
                ) from exc
            record["smb_status"] = "complete"
            record.pop("smb_error", None)
            with MANIFEST_LOCK:
                counts.smb_saved += 1

        github_status = str(record.get("github_file_status") or "")
        if smb_only:
            record["github_file_status"] = "pending"
            record["github_index_reason"] = "deferred_while_github_writer_active"
        elif github_status not in {"complete", "index_only"}:
            github_error = put_github_file(downloaded, relative_path, github_budget)
            if github_error:
                record["github_file_status"] = "index_only"
                record["github_index_reason"] = github_error
                with MANIFEST_LOCK:
                    counts.github_index += 1
            else:
                record["github_file_status"] = "complete"
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
    github_budget: GitHubFileBudget,
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

        def collect(message: dict, tasks: list[tuple[dict, str, str]], window_counts: Counts) -> None:
            for file_id, file_name in classify_files(message):
                if extension_of(file_name) in AV_EXTENSIONS:
                    record_av_handoff(group, folder, message, file_id, file_name,
                                      records, apply, window_counts)
                    continue
                tasks.append((message, file_id, file_name))

        def run_tasks(tasks: list[tuple[dict, str, str]], window_counts: Counts) -> None:
            """按批提交并发处理；批内任一失败按顺序抛出，保留窗口停止语义。"""
            for offset in range(0, len(tasks), max(1, workers)):
                batch = tasks[offset:offset + max(1, workers)]
                futures = [
                    pool.submit(
                        archive_file,
                        group, folder, message, file_id, file_name, records,
                        temp_root, apply, window_counts, github_budget, smb_only,
                    )
                    for message, file_id, file_name in batch
                ]
                for future in futures:
                    future.result()

        consecutive_failures = 0
        for start, end in windows:
            boundary_key = window_record_id(group, start, end)
            if records.get(boundary_key, {}).get("window_status") == "complete" and not reconcile:
                print_event("window_skipped", group=group.title, start=dws_time(start), end=dws_time(end))
                continue
            window_counts = Counts()
            try:
                tasks: list[tuple[dict, str, str]] = []
                for message in walk_window_messages(group.conversation_id, start, end, None, page_size):
                    collect(message, tasks, window_counts)
                    topic_id = str(message.get("openConvThreadId") or "")
                    if topic_id:
                        known_topic_ids.add(topic_id)
                run_tasks(tasks, window_counts)
                reply_tasks: list[tuple[dict, str, str]] = []
                for topic_id in known_topic_ids:
                    for reply in walk_window_messages(group.conversation_id, start, end, topic_id, page_size):
                        window_counts.topic_replies += 1
                        collect(reply, reply_tasks, window_counts)
                run_tasks(reply_tasks, window_counts)
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
                    handoff_av=window_counts.handoff_av,
                    unavailable=window_counts.unavailable,
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
                consecutive_failures += 1
                # 一个坏件不该毁掉当轮剩下的所有窗口。窗口留 stopped 状态，下轮重试；
                # 「不得跳过未完成窗口」的保证由 manifest_window_bounds 的**连续前缀**
                # 来兜（增量起点只推进到第一个非 complete 窗口之前），不靠这里 break。
                if consecutive_failures >= MAX_CONSECUTIVE_WINDOW_FAILURES:
                    print_event("group_aborted_after_consecutive_failures",
                                group=group.title, failures=consecutive_failures)
                    break
                continue
            consecutive_failures = 0
            counts.merge(window_counts)
    return counts


def repair_smb_group(group: Group, temp_root: Path, *, failed_only: bool = False) -> Counts:
    """Repair only manifest-known SMB files that are missing or zero-filled."""
    folder = find_existing_folder(group)
    records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    if not records:
        raise ArchiveError("SMB manifest is unavailable for repair")
    counts = Counts()
    for record_id in sorted(records):
        record = records[record_id]
        if record.get("record_type") != "file":
            continue
        if failed_only:
            if record.get("smb_status") != "failed":
                continue
        elif smb_original_usable(record):
            continue
        relative_path = str(record.get("relative_path") or "")
        file_id = str(record.get("file_id") or "")
        extension = str(record.get("extension") or extension_of(relative_path))
        expected_md5 = str(record.get("md5") or "")
        if not relative_path or not file_id:
            counts.failures += 1
            counts.failures_by_reason.append("manifest file record lacks repair identity")
            continue
        downloaded: Path | None = None
        source_kind: str | None = None
        try:
            downloaded = get_github_file_for_repair(record, temp_root)
            if downloaded is not None:
                source_kind = "github"
            else:
                downloaded = download_file(file_id, temp_root)
                source_kind = "dws"
            target = SMB_ROOT / relative_path
            copy_to_smb(downloaded, target, extension, expected_md5, replace_existing=target.exists())
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
    """Publish durable GitHub routes for SMB-complete files without re-downloading them."""
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
        if record.get("record_type") != "file" or not smb_original_usable(record):
            continue
        github_status = str(record.get("github_file_status") or "")
        if github_status in {"complete", "index_only"}:
            continue
        record["github_file_status"] = "index_only"
        record["github_index_reason"] = "github_raw_deferred_for_serial_writer"
        counts.github_index += 1

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
        result: dict[str, object] = {"count": self.count, "from": self.earliest, "to": self.latest}
        if self.reasons:
            result["reasons"] = dict(sorted(self.reasons.items()))
        return result


def audit_file_status(record: dict | None) -> tuple[str, str | None]:
    if not record:
        return "unresolved", "manifest_record_missing"
    if record.get("smb_status") == "unavailable":
        return "unavailable", str(record.get("smb_error") or "dws_resource_gone")
    if not smb_original_usable(record):
        return "unresolved", "smb_original_missing_or_zero_filled"
    if record.get("github_file_status") not in {"complete", "index_only"}:
        return "unresolved", str(record.get("github_index_reason") or "github_index_pending")
    return "complete", None


def audit_group(group: Group, windows: list[tuple[datetime, datetime]], page_size: int) -> dict:
    folder = find_existing_folder(group)
    records = read_manifest(SMB_ROOT / folder / MANIFEST_NAME)
    buckets = {"file": {"complete": AuditBucket(), "unavailable": AuditBucket(), "unresolved": AuditBucket()},
               "handoff_av": {"complete": AuditBucket(), "unavailable": AuditBucket(), "unresolved": AuditBucket()}}
    seen: set[str] = set()

    def inspect_message(message: dict) -> None:
        message_id = str(message.get("openMessageId") or "")
        message_time = str(message.get("createTime") or "")
        if not message_id or not message_time:
            raise PagingError("file message missing openMessageId or createTime")
        for file_id, file_name in classify_files(message):
            if extension_of(file_name) in AV_EXTENSIONS:
                key = handoff_record_id(group, message_id, file_id)
                if key in seen:
                    continue
                seen.add(key)
                status = "complete" if key in records else "unresolved"
                buckets["handoff_av"][status].add(message_time, None if status == "complete" else "handoff_not_recorded")
                continue
            record_id = file_record_id(group, message_id, file_id)
            if record_id in seen:
                continue
            seen.add(record_id)
            status, reason = audit_file_status(records.get(record_id))
            buckets["file"][status].add(message_time, reason)

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
    return {kind: {status: bucket.as_dict() for status, bucket in statuses.items()}
            for kind, statuses in buckets.items()}


def export_handoff(groups: list[Group], destination: Path) -> int:
    """把 handoff_av 记录导出成 `待转KMVideo.csv`，交 KMVideo 侧收。"""
    rows = []
    for group in groups:
        folder = find_existing_folder(group)
        for record in read_manifest(SMB_ROOT / folder / MANIFEST_NAME).values():
            if record.get("record_type") != "handoff_av":
                continue
            rows.append({
                "项目": folder,
                "文件名": record.get("file_name", ""),
                "扩展名": record.get("extension", ""),
                "消息时间": record.get("message_time", ""),
                "发送人": record.get("sender", ""),
                "fileId": record.get("file_id", ""),
                "openMessageId": record.get("message_id", ""),
                "openConversationId": record.get("conversation_id", ""),
                "交接状态": record.get("handoff_status", "pending"),
            })
    rows.sort(key=lambda r: (r["项目"], r["消息时间"]))
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "项目", "文件名", "扩展名", "消息时间", "发送人",
            "fileId", "openMessageId", "openConversationId", "交接状态"])
        writer.writeheader()
        writer.writerows(rows)
    return len(rows)


def manifest_window_bounds(folder: str) -> tuple[datetime | None, datetime | None]:
    """(最早窗口起点, 最后一个 complete 窗口终点)。

    起点用于「窗口覆盖前移检查」：manifest 首窗口晚于本轮 --start 的群，
    说明更早的消息从来没扫过。终点用于增量起点 —— 直接读 manifest，
    不依赖外部预生成的 starts 文件（预生成会在 manifest 尚未落稳时取到旧值，
    导致整群按全量重扫）。
    """
    earliest: datetime | None = None
    latest_complete: datetime | None = None
    windows: list[tuple[datetime, datetime, object]] = []
    for record in read_manifest(SMB_ROOT / folder / MANIFEST_NAME).values():
        if record.get("record_type") != "window":
            continue
        try:
            start = parse_time(str(record.get("start") or ""))
            end = parse_time(str(record.get("end") or ""))
        except ValueError:
            continue
        if earliest is None or start < earliest:
            earliest = start
        windows.append((start, end, record.get("window_status")))
    # 增量起点只能推进到**第一个非 complete 窗口之前**。
    # 取 max(end) 会把中间那个 stopped 窗口永久跳过去，变成静默缺口。
    for start, end, status in sorted(windows):
        if status != "complete":
            break
        if latest_complete is None or end > latest_complete:
            latest_complete = end
    return earliest, latest_complete


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
    parser = argparse.ArgumentParser(description="Archive DWS files from explicitly allowed internal groups.")
    parser.add_argument("--allow-title", action="append", required=True, help="Exact DWS group title; repeat for every authorized group.")
    parser.add_argument("--days", type=int, default=90)
    parser.add_argument("--start", help="Inclusive start time in Asia/Shanghai, YYYY-MM-DD HH:MM:SS.")
    parser.add_argument("--window-days", type=int, default=30, help="时间切片天数，默认 30（拍板值）。")
    parser.add_argument("--end", help="Frozen end time in Asia/Shanghai, YYYY-MM-DD HH:MM:SS.")
    parser.add_argument("--page-size", type=int, default=100)
    parser.add_argument("--workers", type=int, default=1,
                        help="Concurrent file pipeline workers (downloads in parallel; manifest writes stay serial).")
    parser.add_argument("--github-file-budget", type=int,
                        help="Maximum raw-file uploads attempted through the current GitHub REST quota. Omit for no cap.")
    parser.add_argument("--smb-only", action="store_true", help="Write SMB originals and durable SMB manifests only; defer GitHub file and index.")
    parser.add_argument("--sync-github-index", action="store_true",
                        help="For SMB-complete pending records, write GitHub route manifests only; requires --apply.")
    parser.add_argument("--audit", action="store_true",
                        help="Read the specified DWS range and print per-group file completion statistics; requires --dry-run.")
    parser.add_argument("--since-manifest", action="store_true",
                        help="每群起点改为该群 manifest 里最后一个 complete 窗口的终点（增量提速；无记录则回退 --start）。")
    parser.add_argument("--reconcile", action="store_true",
                        help="Re-read completed windows and add only manifest-missing files; requires --apply.")
    parser.add_argument("--repair-smb", action="store_true",
                        help="Re-download only manifest-known SMB files that are missing or zero-filled; requires --apply.")
    parser.add_argument("--failed-only", action="store_true",
                        help="With --repair-smb, repair only manifest records explicitly marked smb_status=failed.")
    parser.add_argument("--export-handoff", help="导出 handoff_av 交接清单到该 CSV 路径后退出。")
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
    if args.github_file_budget is not None and args.github_file_budget < 0:
        raise ArchiveError("github-file-budget must not be negative")
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

    if args.export_handoff:
        groups = select_groups(args.allow_title)
        total = export_handoff(groups, Path(args.export_handoff).expanduser())
        print_event("handoff_exported", rows=total, path=args.export_handoff)
        return 0

    if not PRIVATE_DB_CLIENT.is_file():
        raise ArchiveError(f"Private-Database client is unavailable: {PRIVATE_DB_CLIENT}")
    end = parse_time(args.end) if args.end else datetime.now(TIMEZONE).replace(microsecond=0)
    if args.start:
        start = parse_time(args.start)
    else:
        if args.days < 1 or args.days > 90:
            raise ArchiveError("days must be between 1 and 90 unless --start is supplied")
        start = end - timedelta(days=args.days)
    base_windows = make_windows(start, end, args.window_days)
    groups = select_groups(args.allow_title)
    operation = "audit" if args.audit else "sync_github_index" if args.sync_github_index else "repair_smb" if args.repair_smb else "archive"
    print_event(
        "run_started",
        mode="apply" if args.apply else "dry_run",
        operation=operation,
        groups=len(groups),
        start=dws_time(start),
        end=dws_time(end),
        windows=len(base_windows),
        since_manifest=bool(args.since_manifest),
    )
    total = Counts()
    github_budget = GitHubFileBudget(args.github_file_budget)
    with tempfile.TemporaryDirectory(prefix="kmfile-dws-") as temporary:
        temp_root = Path(temporary)
        for group in groups:
            folder = find_existing_folder(group)
            residue = manifest_partial_residue(folder)
            if residue:
                print_event("manifest_partial_residue", group=group.title, files=residue[:5])
            earliest, latest_complete = manifest_window_bounds(folder)
            if earliest is not None and earliest > start:
                print_event("window_coverage_gap", group=group.title,
                            manifest_first_window=dws_time(earliest),
                            requested_start=dws_time(start),
                            note="该群比请求起点更早的消息从未扫过，需补全量")
            windows = base_windows
            if args.since_manifest and latest_complete is not None and latest_complete < end:
                windows = make_windows(latest_complete, end, args.window_days)
                print_event("incremental_start", group=group.title,
                            start=dws_time(latest_complete), windows=len(windows))
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
                        group, windows, temp_root, args.page_size, args.apply, github_budget,
                        args.smb_only, args.reconcile, workers=args.workers,
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
        unavailable=total.unavailable,
        handoff_av=total.handoff_av,
        skipped=total.skipped,
        failures=total.failures,
        completed_windows=total.completed_windows,
        github_file_budget_remaining=github_budget.remaining,
        temp_cleanup="complete",
    )
    return 1 if total.failures else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except ArchiveError as exc:
        print_event("run_stopped", reason=str(exc), temp_cleanup="complete")
        raise SystemExit(1)
