#!/usr/bin/env python3
"""文脉中枢 / Context Kernel v0.0.0.1.

A provider-neutral, file-based context control skill for long-running LLM work.
Only Python's standard library is used.
"""

from __future__ import annotations

import argparse
import base64
import contextlib
import datetime as dt
import hashlib
import json
import os
import re
import shutil
import socket
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Sequence, Tuple

VERSION = "0.0.0.1"
DISPLAY_NAME_ZH = "文脉中枢"
SKILL_NAME = "context-kernel"
RUNTIME_DIR_NAME = ".ramify"
KERNEL_FILE = "KERNEL.md"
DECISIONS_FILE = "DECISIONS.md"
HANDOFF_FILE = "HANDOFF.md"
RUNTIME_MANIFEST_FILE = "MANIFEST.json"
PACKAGE_MANIFEST_FILE = "MANIFEST.json"
TXN_FILE = ".txn.json"
LOCK_FILE = ".lock"

KERNEL_SCHEMA = "context-kernel/kernel-v1"
DECISIONS_SCHEMA = "context-kernel/decisions-v1"
HANDOFF_SCHEMA = "context-kernel/handoff-v1"
MANIFEST_SCHEMA = "context-kernel/manifest-v1"
PACKAGE_SCHEMA = "context-kernel/package-manifest-v1"
TXN_SCHEMA = "context-kernel/transaction-v1"

ACTIVE_MD_FILES = {KERNEL_FILE, DECISIONS_FILE, HANDOFF_FILE}
PERSISTENT_MD_FILES = {KERNEL_FILE, DECISIONS_FILE}
ALLOWED_TRANSACTION_TARGETS = {KERNEL_FILE, DECISIONS_FILE, HANDOFF_FILE, RUNTIME_MANIFEST_FILE}
ALLOWED_RUNTIME_ENTRIES = ALLOWED_TRANSACTION_TARGETS | {TXN_FILE, LOCK_FILE}
PACKAGE_CONTENT_FILES = {"SKILL.md", "scripts/context_kernel.py"}
MAX_TEXT_FILE_BYTES = 2 * 1024 * 1024
MAX_JSON_FILE_BYTES = 8 * 1024 * 1024
MAX_TRANSACTION_JOURNAL_BYTES = 24 * 1024 * 1024
MAX_SINGLE_LINE_CHARS = 500

LIFECYCLES = {"NOT_STARTED", "ACTIVE", "BLOCKED", "PAUSED", "COMPLETE"}
TRANSFER_STATES = {"NONE", "PREPARED", "CLOSED", "CANCELLED"}
DECISION_STATES = {"PROPOSED", "ACCEPTED", "SUPERSEDED", "REJECTED"}
EVIDENCE_STATES = {"VERIFIED", "UNVERIFIED"}

LIMITS = {
    "max_active_markdown_files": 3,
    "kernel_context_units": 4000,
    "decisions_context_units": 12000,
    "handoff_context_units": 2500,
    "max_completed": 12,
    "max_in_progress": 7,
    "max_blockers": 7,
    "max_unknowns": 7,
    "max_risks": 7,
    "max_decision_refs": 12,
    "max_next_actions": 5,
    "max_evidence": 20,
    "max_do_not_repeat": 7,
    "max_decision_units": 900,
}

KERNEL_SECTION_ORDER = [
    "目标",
    "范围与约束",
    "当前状态",
    "责任",
    "决策引用",
    "下一步",
    "证据",
    "不要重复",
]

SCOPE_SUBSECTIONS = ["范围内", "范围外", "硬约束", "软偏好"]
STATE_SUBSECTIONS = ["已完成", "进行中", "阻塞", "未知与待验证", "风险"]
TARGET_KEYS = ["项目", "北极星", "当前目标", "当前任务", "阶段 / Gate"]
RESPONSIBILITY_KEYS = ["最终责任人", "当前执行主体", "移交状态", "移交编号", "移交来源主体", "目标执行主体", "移交原因"]
DECISION_FIELDS = ["状态", "日期", "决策责任人", "决策", "理由", "证据", "影响", "替代", "复审触发"]
HANDOFF_SECTION_ORDER = [
    "一句话恢复", "当前控制状态", "当前任务", "必须继承的约束", "已完成", "进行中", "阻塞",
    "未知与待验证", "风险", "必须继承的决策", "下一步", "证据入口", "不要重复", "恢复规则",
]
RUNTIME_MANIFEST_KEYS = [
    "schema", "skill_name", "display_name_zh", "skill_version", "runtime_dir", "revision", "created_at",
    "updated_at", "files", "protected_digest", "responsibility_digest", "execution_digest", "decision_core_digests",
    "decision_statuses", "last_operation", "limits",
]

ID_PATTERNS = {
    "completed": re.compile(r"^C-\d{4}$"),
    "in_progress": re.compile(r"^P-\d{4}$"),
    "blockers": re.compile(r"^B-\d{4}$"),
    "unknowns": re.compile(r"^U-\d{4}$"),
    "risks": re.compile(r"^R-\d{4}$"),
    "decisions": re.compile(r"^D-\d{4}$"),
    "actions": re.compile(r"^A-\d{4}$"),
    "evidence": re.compile(r"^E-\d{4}$"),
    "do_not_repeat": re.compile(r"^N-\d{4}$"),
}

SECRET_PATTERNS = [
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:ghp|github_pat)_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    re.compile(r"(?i)\b(?:api[_ -]?key|access[_ -]?token|secret[_ -]?key)\b\s*[:=]\s*['\"]?[A-Za-z0-9_./+=-]{16,}"),
]

THOUGHT_PATTERNS = [
    re.compile(r"(?i)<\/?(?:thinking|analysis|chain_of_thought)>") ,
    re.compile(r"(?i)\bchain[- ]of[- ]thought\b"),
    re.compile(r"(?i)\bhidden reasoning\b"),
]


class KernelError(RuntimeError):
    """Expected operational or validation failure."""


class ValidationIssue:
    __slots__ = ("level", "code", "message", "path")

    def __init__(self, level: str, code: str, message: str, path: str = "") -> None:
        self.level = level
        self.code = code
        self.message = message
        self.path = path

    def as_dict(self) -> Dict[str, str]:
        return {"level": self.level, "code": self.code, "message": self.message, "path": self.path}

    def __str__(self) -> str:
        location = f" [{self.path}]" if self.path else ""
        return f"{self.level} {self.code}{location}: {self.message}"


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "\n".join(line.rstrip() for line in text.split("\n"))
    return text.rstrip() + "\n"


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    return sha256_bytes(normalize_text(text).encode("utf-8"))


def file_meta(path: Path) -> Dict[str, Any]:
    data = path.read_bytes()
    return {"sha256": sha256_bytes(data), "bytes": len(data)}


def context_units(text: str) -> int:
    """Model-neutral estimate: CJK chars + Latin-like tokens."""
    cjk = len(re.findall(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", text))
    scrubbed = re.sub(r"[\u3400-\u4dbf\u4e00-\u9fff\uf900-\ufaff]", " ", text)
    latin = len(re.findall(r"[A-Za-z0-9_./:@#%+\-=]+", scrubbed))
    return cjk + latin


def json_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    return json.dumps(str(value), ensure_ascii=False)


def parse_scalar(raw: str) -> Any:
    raw = raw.strip()
    if raw == "true":
        return True
    if raw == "false":
        return False
    if re.fullmatch(r"-?\d+", raw):
        return int(raw)
    if raw.startswith('"'):
        try:
            return json.loads(raw)
        except json.JSONDecodeError as exc:
            raise KernelError(f"Invalid JSON-quoted frontmatter value: {raw}") from exc
    return raw


def parse_frontmatter(text: str) -> Tuple[Dict[str, Any], str]:
    text = normalize_text(text)
    if not text.startswith("---\n"):
        raise KernelError("Missing YAML frontmatter opening delimiter")
    end = text.find("\n---\n", 4)
    if end < 0:
        raise KernelError("Missing YAML frontmatter closing delimiter")
    block = text[4:end]
    meta: Dict[str, Any] = {}
    for line in block.splitlines():
        if not line.strip():
            continue
        if ":" not in line:
            raise KernelError(f"Malformed frontmatter line: {line}")
        key, raw = line.split(":", 1)
        key = key.strip()
        if not re.fullmatch(r"[a-z_][a-z0-9_]*", key):
            raise KernelError(f"Invalid frontmatter key: {key}")
        if key in meta:
            raise KernelError(f"Duplicate frontmatter key: {key}")
        meta[key] = parse_scalar(raw)
    body = text[end + 5 :]
    return meta, body


def render_frontmatter(meta: Mapping[str, Any], order: Sequence[str], body: str) -> str:
    missing = [key for key in order if key not in meta]
    if missing:
        raise KernelError(f"Missing frontmatter keys: {', '.join(missing)}")
    lines = ["---"]
    for key in order:
        lines.append(f"{key}: {json_scalar(meta[key])}")
    for key in sorted(set(meta) - set(order)):
        lines.append(f"{key}: {json_scalar(meta[key])}")
    lines.extend(["---", "", body.strip(), ""])
    return normalize_text("\n".join(lines))


def split_h2_sections(body: str) -> Tuple[str, Dict[str, str], List[str]]:
    matches = list(re.finditer(r"(?m)^## ([^\n]+)\n", body))
    prefix = body[: matches[0].start()] if matches else body
    sections: Dict[str, str] = {}
    order: List[str] = []
    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        if name in sections:
            raise KernelError(f"Duplicate H2 section: {name}")
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(body)
        sections[name] = body[start:end].rstrip() + "\n"
        order.append(name)
    return prefix, sections, order


def split_h3_sections(section: str) -> Tuple[str, Dict[str, str], List[str]]:
    matches = list(re.finditer(r"(?m)^### ([^\n]+)\n", section))
    prefix = section[: matches[0].start()] if matches else section
    sections: Dict[str, str] = {}
    order: List[str] = []
    for idx, match in enumerate(matches):
        name = match.group(1).strip()
        if name in sections:
            raise KernelError(f"Duplicate H3 section: {name}")
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(section)
        sections[name] = section[start:end].rstrip() + "\n"
        order.append(name)
    return prefix, sections, order


def parse_key_bullets(section: str, expected_keys: Sequence[str]) -> Dict[str, str]:
    values: Dict[str, str] = {}
    for line in section.splitlines():
        if not line.strip() or line.startswith(">"):
            continue
        match = re.match(r"^- ([^：]+)：(.*)$", line)
        if not match:
            raise KernelError(f"Expected key bullet, got: {line}")
        key = match.group(1).strip()
        value = match.group(2).strip()
        if key in values:
            raise KernelError(f"Duplicate key bullet: {key}")
        values[key] = value
    if list(values.keys()) != list(expected_keys):
        raise KernelError(f"Expected keys in order {list(expected_keys)}, got {list(values.keys())}")
    return values


def parse_dash_items(section: str, allow_none: bool = True) -> List[str]:
    items: List[str] = []
    for line in section.splitlines():
        if not line.strip() or line.startswith(">"):
            continue
        if not line.startswith("- "):
            raise KernelError(f"Expected dash list item, got: {line}")
        items.append(line[2:].strip())
    if allow_none and items == ["无"]:
        return []
    if "无" in items:
        raise KernelError("'无' must be the only list item")
    return items


def parse_numbered_items(section: str) -> List[str]:
    items: List[str] = []
    expected = 1
    for line in section.splitlines():
        if not line.strip() or line.startswith(">"):
            continue
        if line.strip() == "- 无":
            if items:
                raise KernelError("'- 无' cannot be mixed with numbered actions")
            return []
        match = re.match(r"^(\d+)\. (.+)$", line)
        if not match:
            raise KernelError(f"Expected numbered item, got: {line}")
        number = int(match.group(1))
        if number != expected:
            raise KernelError(f"Next Actions must be consecutively numbered; expected {expected}, got {number}")
        items.append(match.group(2).strip())
        expected += 1
    return items


def parse_id_items(items: Sequence[str], pattern: re.Pattern[str], label: str) -> List[Dict[str, Any]]:
    parsed: List[Dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        parts = [part.strip() for part in item.split("|")]
        identifier = parts[0] if parts else ""
        if not pattern.fullmatch(identifier):
            raise KernelError(f"Invalid {label} ID in item: {item}")
        if identifier in seen:
            raise KernelError(f"Duplicate {label} ID: {identifier}")
        seen.add(identifier)
        parsed.append({"id": identifier, "parts": parts, "raw": item})
    return parsed


def clean_single_line(value: Any, field: str, *, allow_empty: bool = False, max_chars: int = MAX_SINGLE_LINE_CHARS) -> str:
    text = str(value).strip()
    if not text:
        if allow_empty:
            return ""
        raise KernelError(f"{field} must be non-empty")
    if any(ch in text for ch in ["\n", "\r", "\u2028", "\u2029"]):
        raise KernelError(f"{field} must be a single line")
    if any(ord(ch) < 32 or ord(ch) == 127 for ch in text):
        raise KernelError(f"{field} contains control characters")
    if len(text) > max_chars:
        raise KernelError(f"{field} exceeds {max_chars} characters")
    return text


def kernel_template(project: str, north_star: str, owner: str, executor: str) -> str:
    project = clean_single_line(project, "project")
    north_star = clean_single_line(north_star, "north-star")
    owner = clean_single_line(owner, "owner")
    executor = clean_single_line(executor or owner, "executor")
    now = utc_now()
    meta = {
        "ck_schema": KERNEL_SCHEMA,
        "skill_version": VERSION,
        "revision": 0,
        "updated_at": now,
        "lifecycle": "NOT_STARTED",
    }
    body = f"""# {DISPLAY_NAME_ZH}｜Context Kernel

> 当前项目的唯一状态事实源。只保留仍影响后续执行的有效信息；不保存聊天记录、长推理或原始工具输出。

## 目标
- 项目：{project}
- 北极星：{north_star}
- 当前目标：待确认
- 当前任务：核验初始化内容是否准确
- 阶段 / Gate：初始化 / Context Gate

## 范围与约束
### 范围内
- 待确认

### 范围外
- 待确认

### 硬约束
- 所有完成声明必须绑定 VERIFIED 证据；未核验内容必须明确标记 UNVERIFIED
- 不保存密钥、完整聊天、隐藏推理或原始工具输出
- 活跃 Markdown 文件最多三个

### 软偏好
- 优先使用最少上下文恢复任务

## 当前状态
### 已完成
- 无

### 进行中
- P-0001 | 核验项目目标、范围、责任和当前任务

### 阻塞
- 无

### 未知与待验证
- U-0001 | 初始化内容是否准确 | 验证：由最终责任人或权威项目证据核对

### 风险
- R-0001 | 未核验的初始化信息可能被误当作事实 | 缓解：Context Gate 通过前保持 NOT_STARTED

## 责任
- 最终责任人：{owner}
- 当前执行主体：{executor}
- 移交状态：NONE
- 移交编号：无
- 移交来源主体：无
- 目标执行主体：无
- 移交原因：无

## 决策引用
- 无

## 下一步
1. A-0001 | 核验并补全 KERNEL.md 中的待确认内容
2. A-0002 | 为确认后的事实补充证据 ID

## 证据
- 无

## 不要重复
- 无
"""
    return render_frontmatter(meta, ["ck_schema", "skill_version", "revision", "updated_at", "lifecycle"], body)


def decisions_template() -> str:
    meta = {"ck_schema": DECISIONS_SCHEMA, "skill_version": VERSION, "updated_at": utc_now()}
    body = f"""# {DISPLAY_NAME_ZH}｜决策账本

> 只记录会持续影响后续任务、架构、边界、责任或高返工成本的重要决策。普通讨论、临时想法和重复确认不进入本文件。

## 有效决策索引
- 无

## 决策记录

> 新决策使用 `D-0001` 起的四位编号。已接受决策不得静默改写；替代时新增决策并维护 Supersession 关系。
"""
    return render_frontmatter(meta, ["ck_schema", "skill_version", "updated_at"], body)


def runtime_dir(root: Path) -> Path:
    return root.resolve() / RUNTIME_DIR_NAME


def assert_safe_runtime_path(rt: Path) -> None:
    if rt.exists() and rt.is_symlink():
        raise KernelError(f"Runtime directory must not be a symlink: {rt}")
    if rt.exists() and not rt.is_dir():
        raise KernelError(f"Runtime path is not a directory: {rt}")


def safe_read_text(path: Path, *, max_bytes: int = MAX_TEXT_FILE_BYTES) -> str:
    if path.is_symlink():
        raise KernelError(f"Symlink is not allowed: {path}")
    if not path.exists() or not path.is_file():
        raise KernelError(f"Missing regular file: {path}")
    size = path.stat().st_size
    if size > max_bytes:
        raise KernelError(f"File exceeds {max_bytes} bytes: {path} ({size})")
    try:
        return normalize_text(path.read_text(encoding="utf-8"))
    except UnicodeDecodeError as exc:
        raise KernelError(f"File is not valid UTF-8: {path}") from exc


def parse_kernel(text: str) -> Dict[str, Any]:
    meta, body = parse_frontmatter(text)
    required_meta = ["ck_schema", "skill_version", "revision", "updated_at", "lifecycle"]
    if list(meta.keys()) != required_meta:
        raise KernelError(f"KERNEL frontmatter must contain exactly {required_meta}")
    if meta["ck_schema"] != KERNEL_SCHEMA:
        raise KernelError(f"Unsupported KERNEL schema: {meta['ck_schema']}")
    if meta["skill_version"] != VERSION:
        raise KernelError(f"KERNEL skill version must be {VERSION}")
    if not isinstance(meta["revision"], int) or isinstance(meta["revision"], bool) or meta["revision"] < 0:
        raise KernelError("KERNEL revision must be a non-negative integer")
    if meta["lifecycle"] not in LIFECYCLES:
        raise KernelError(f"Invalid lifecycle: {meta['lifecycle']}")
    clean_single_line(meta["updated_at"], "KERNEL updated_at", max_chars=80)

    prefix, sections, order = split_h2_sections(body)
    if prefix.strip() != f"# {DISPLAY_NAME_ZH}｜Context Kernel\n\n> 当前项目的唯一状态事实源。只保留仍影响后续执行的有效信息；不保存聊天记录、长推理或原始工具输出。":
        raise KernelError("KERNEL title or authority notice is missing or changed")
    if order != KERNEL_SECTION_ORDER:
        raise KernelError(f"KERNEL H2 sections must be exactly {KERNEL_SECTION_ORDER}; got {order}")

    target = parse_key_bullets(sections["目标"], TARGET_KEYS)
    for key, value in target.items():
        clean_single_line(value, f"目标/{key}")

    scope_prefix, scope_sections, scope_order = split_h3_sections(sections["范围与约束"])
    if scope_prefix.strip():
        raise KernelError("Unexpected content before scope subsections")
    if scope_order != SCOPE_SUBSECTIONS:
        raise KernelError(f"Scope subsections must be exactly {SCOPE_SUBSECTIONS}")
    scope = {name: parse_dash_items(scope_sections[name]) for name in SCOPE_SUBSECTIONS}

    state_prefix, state_sections, state_order = split_h3_sections(sections["当前状态"])
    if state_prefix.strip():
        raise KernelError("Unexpected content before state subsections")
    if state_order != STATE_SUBSECTIONS:
        raise KernelError(f"State subsections must be exactly {STATE_SUBSECTIONS}")

    completed = parse_id_items(parse_dash_items(state_sections["已完成"]), ID_PATTERNS["completed"], "completed")
    in_progress = parse_id_items(parse_dash_items(state_sections["进行中"]), ID_PATTERNS["in_progress"], "in-progress")
    blockers = parse_id_items(parse_dash_items(state_sections["阻塞"]), ID_PATTERNS["blockers"], "blocker")
    unknowns = parse_id_items(parse_dash_items(state_sections["未知与待验证"]), ID_PATTERNS["unknowns"], "unknown")
    risks = parse_id_items(parse_dash_items(state_sections["风险"]), ID_PATTERNS["risks"], "risk")

    responsibility = parse_key_bullets(sections["责任"], RESPONSIBILITY_KEYS)
    for key, value in responsibility.items():
        clean_single_line(value, f"责任/{key}")
    if responsibility["移交状态"] not in TRANSFER_STATES:
        raise KernelError(f"Invalid transfer state: {responsibility['移交状态']}")

    decision_refs = parse_id_items(parse_dash_items(sections["决策引用"]), ID_PATTERNS["decisions"], "decision reference")
    actions = parse_id_items(parse_numbered_items(sections["下一步"]), ID_PATTERNS["actions"], "action")

    evidence = parse_id_items(parse_dash_items(sections["证据"]), ID_PATTERNS["evidence"], "evidence")
    for item in evidence:
        if len(item["parts"]) < 4:
            raise KernelError(f"Evidence item requires ID | VERIFIED/UNVERIFIED | locator | claim: {item['raw']}")
        if item["parts"][1] not in EVIDENCE_STATES:
            raise KernelError(f"Invalid evidence state in: {item['raw']}")
        if not item["parts"][2] or not " | ".join(item["parts"][3:]).strip():
            raise KernelError(f"Evidence locator and claim must be non-empty: {item['raw']}")

    do_not_repeat = parse_id_items(parse_dash_items(sections["不要重复"]), ID_PATTERNS["do_not_repeat"], "do-not-repeat")

    all_ids: Dict[str, str] = {}
    for category, items in [
        ("completed", completed), ("in_progress", in_progress), ("blockers", blockers), ("unknowns", unknowns),
        ("risks", risks), ("decision_refs", decision_refs), ("actions", actions), ("evidence", evidence),
        ("do_not_repeat", do_not_repeat),
    ]:
        for item in items:
            identifier = item["id"]
            if identifier in all_ids:
                raise KernelError(f"ID reused across categories: {identifier} ({all_ids[identifier]} and {category})")
            all_ids[identifier] = category

    evidence_by_id = {item["id"]: item for item in evidence}
    for item in completed:
        referenced = set(re.findall(r"E-\d{4}", item["raw"]))
        explicitly_unverified = "UNVERIFIED" in item["raw"]
        if not referenced and not explicitly_unverified:
            raise KernelError(f"Completed item must reference VERIFIED evidence or contain UNVERIFIED: {item['raw']}")
        for evidence_id in referenced:
            if evidence_id not in evidence_by_id:
                raise KernelError(f"Completed item references missing evidence {evidence_id}: {item['raw']}")
        unverified_refs = [eid for eid in referenced if evidence_by_id[eid]["parts"][1] != "VERIFIED"]
        if unverified_refs and not explicitly_unverified:
            raise KernelError(f"Completed item relies on UNVERIFIED evidence {sorted(unverified_refs)} but is not marked UNVERIFIED")

    transfer_state = responsibility["移交状态"]
    transfer_id = responsibility["移交编号"]
    source = responsibility["移交来源主体"]
    target_executor = responsibility["目标执行主体"]
    transfer_reason = responsibility["移交原因"]
    current_executor = responsibility["当前执行主体"]
    audit_values = [transfer_id, source, target_executor, transfer_reason]
    if transfer_state == "NONE":
        if any(value not in {"", "无"} for value in audit_values):
            raise KernelError("NONE transfer must use '无' for ID, source, target and reason")
    else:
        if any(value in {"", "无"} for value in audit_values):
            raise KernelError(f"{transfer_state} transfer requires ID, source, target and reason")
        if not re.fullmatch(r"T-\d{14}-[A-F0-9]{6}", transfer_id):
            raise KernelError(f"Invalid transfer ID: {transfer_id}")
        if source == target_executor:
            raise KernelError("Transfer source and target must differ")
        if transfer_state == "PREPARED" and current_executor != source:
            raise KernelError("PREPARED transfer requires current executor to equal transfer source")
        if transfer_state == "CLOSED" and current_executor != target_executor:
            raise KernelError("CLOSED transfer requires current executor to equal transfer target")
        if transfer_state == "CANCELLED" and current_executor != source:
            raise KernelError("CANCELLED transfer requires current executor to remain the transfer source")

    if meta["lifecycle"] == "BLOCKED" and not blockers:
        raise KernelError("BLOCKED lifecycle requires at least one blocker")
    if meta["lifecycle"] != "COMPLETE" and not actions:
        raise KernelError(f"{meta['lifecycle']} lifecycle requires at least one next action")
    if meta["lifecycle"] == "COMPLETE":
        if in_progress or blockers or unknowns:
            raise KernelError("COMPLETE lifecycle cannot contain in-progress items, blockers or unknowns")
        if actions:
            raise KernelError("COMPLETE lifecycle cannot contain next actions")
        if any(item["parts"][1] != "VERIFIED" for item in evidence):
            raise KernelError("COMPLETE lifecycle cannot contain UNVERIFIED evidence")
        if any("UNVERIFIED" in item["raw"] for item in completed):
            raise KernelError("COMPLETE lifecycle cannot contain UNVERIFIED completion claims")

    return {
        "meta": meta, "body": body, "target": target, "scope": scope, "completed": completed,
        "in_progress": in_progress, "blockers": blockers, "unknowns": unknowns, "risks": risks,
        "responsibility": responsibility, "decision_refs": decision_refs, "actions": actions,
        "evidence": evidence, "do_not_repeat": do_not_repeat, "text": normalize_text(text),
    }


def parse_decisions(text: str) -> Dict[str, Any]:
    meta, body = parse_frontmatter(text)
    required_meta = ["ck_schema", "skill_version", "updated_at"]
    if list(meta.keys()) != required_meta:
        raise KernelError(f"DECISIONS frontmatter must contain exactly {required_meta}")
    if meta["ck_schema"] != DECISIONS_SCHEMA:
        raise KernelError(f"Unsupported DECISIONS schema: {meta['ck_schema']}")
    if meta["skill_version"] != VERSION:
        raise KernelError(f"DECISIONS skill version must be {VERSION}")
    clean_single_line(meta["updated_at"], "DECISIONS updated_at", max_chars=80)

    prefix, sections, order = split_h2_sections(body)
    expected_prefix = (
        f"# {DISPLAY_NAME_ZH}｜决策账本\n\n"
        "> 只记录会持续影响后续任务、架构、边界、责任或高返工成本的重要决策。普通讨论、临时想法和重复确认不进入本文件。"
    )
    if prefix.strip() != expected_prefix:
        raise KernelError("DECISIONS title or scope notice is missing or changed")
    if order != ["有效决策索引", "决策记录"]:
        raise KernelError("DECISIONS must contain exactly '有效决策索引' and '决策记录'")

    index_items = parse_dash_items(sections["有效决策索引"])
    index_entries: List[Tuple[str, str]] = []
    for item in index_items:
        parts = [part.strip() for part in item.split("|", 1)]
        if len(parts) != 2 or not ID_PATTERNS["decisions"].fullmatch(parts[0]) or not parts[1]:
            raise KernelError(f"Active decision index requires ID | title: {item}")
        if parts[0] in {entry[0] for entry in index_entries}:
            raise KernelError(f"Duplicate active decision index ID: {parts[0]}")
        index_entries.append((parts[0], parts[1]))

    record_section = sections["决策记录"]
    matches = list(re.finditer(r"(?m)^### (D-\d{4}) — ([^\n]+)\n", record_section))
    decisions: Dict[str, Dict[str, Any]] = {}
    leading = record_section[: matches[0].start()] if matches else record_section
    allowed_leading = [line for line in leading.splitlines() if line.strip() and not line.startswith(">")]
    if allowed_leading:
        raise KernelError(f"Unexpected content before first decision: {allowed_leading[0]}")

    numeric_ids: List[int] = []
    for idx, match in enumerate(matches):
        identifier, title = match.group(1), clean_single_line(match.group(2), f"decision {match.group(1)} title", max_chars=180)
        if identifier in decisions:
            raise KernelError(f"Duplicate decision ID: {identifier}")
        numeric_ids.append(int(identifier.split("-")[1]))
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(record_section)
        block = record_section[start:end]
        fields = parse_key_bullets(block, DECISION_FIELDS)
        if fields["状态"] not in DECISION_STATES:
            raise KernelError(f"Invalid decision state for {identifier}: {fields['状态']}")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", fields["日期"]):
            raise KernelError(f"Decision {identifier} date must be YYYY-MM-DD")
        for required_field in ["决策责任人", "决策", "理由", "证据", "影响", "复审触发"]:
            clean_single_line(fields[required_field], f"decision {identifier}/{required_field}", max_chars=MAX_SINGLE_LINE_CHARS)
        replaces = [] if fields["替代"] in {"", "无"} else [part.strip() for part in fields["替代"].split(",")]
        if len(replaces) != len(set(replaces)):
            raise KernelError(f"Decision {identifier} contains duplicate superseded IDs")
        for replaced in replaces:
            if not ID_PATTERNS["decisions"].fullmatch(replaced):
                raise KernelError(f"Invalid superseded ID in {identifier}: {replaced}")
            if replaced == identifier:
                raise KernelError(f"Decision {identifier} cannot supersede itself")
        block_text = record_section[match.start():end]
        if context_units(block_text) > LIMITS["max_decision_units"]:
            raise KernelError(f"Decision {identifier} exceeds {LIMITS['max_decision_units']} context units")
        decisions[identifier] = {"id": identifier, "title": title, "fields": fields, "replaces": replaces, "raw": block_text}

    if numeric_ids != sorted(numeric_ids) or len(numeric_ids) != len(set(numeric_ids)):
        raise KernelError("Decision records must be in strictly increasing numeric ID order")

    accepted_entries = [(identifier, decision["title"]) for identifier, decision in decisions.items() if decision["fields"]["状态"] == "ACCEPTED"]
    if index_entries != accepted_entries:
        raise KernelError(f"Active decision index must exactly match accepted decision IDs and titles in ledger order: {accepted_entries}")

    replaced_by: Dict[str, str] = {}
    for identifier, decision in decisions.items():
        for replaced in decision["replaces"]:
            if replaced not in decisions:
                raise KernelError(f"Decision {identifier} supersedes missing decision {replaced}")
            if replaced in replaced_by and replaced_by[replaced] != identifier:
                raise KernelError(f"Decision {replaced} is superseded by multiple decisions")
            replaced_by[replaced] = identifier
        if decision["fields"]["状态"] == "ACCEPTED":
            for replaced in decision["replaces"]:
                if decisions[replaced]["fields"]["状态"] != "SUPERSEDED":
                    raise KernelError(f"Decision {replaced} must be SUPERSEDED because {identifier} replaces it")

    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(identifier: str) -> None:
        if identifier in visiting:
            raise KernelError(f"Decision supersession cycle detected at {identifier}")
        if identifier in visited:
            return
        visiting.add(identifier)
        for replaced in decisions[identifier]["replaces"]:
            visit(replaced)
        visiting.remove(identifier)
        visited.add(identifier)
    for identifier in decisions:
        visit(identifier)

    return {
        "meta": meta, "body": body, "index_ids": [entry[0] for entry in index_entries],
        "index_entries": index_entries, "decisions": decisions, "text": normalize_text(text),
    }


def render_kernel_with_updates(parsed: Dict[str, Any], *, revision: int, updated_at: str, lifecycle: Optional[str] = None,
                               responsibility_updates: Optional[Mapping[str, str]] = None) -> str:
    text = parsed["text"]
    meta, body = parse_frontmatter(text)
    meta["revision"] = revision
    meta["updated_at"] = updated_at
    if lifecycle is not None:
        meta["lifecycle"] = lifecycle
    if responsibility_updates:
        _, sections, order = split_h2_sections(body)
        responsibility = parse_key_bullets(sections["责任"], RESPONSIBILITY_KEYS)
        responsibility.update(responsibility_updates)
        sections["责任"] = "\n".join(f"- {key}：{responsibility[key]}" for key in RESPONSIBILITY_KEYS) + "\n"
        prefix, _, _ = split_h2_sections(body)
        parts = [prefix.rstrip()]
        for name in order:
            parts.append(f"## {name}\n{sections[name].rstrip()}")
        body = "\n\n".join(parts) + "\n"
    return render_frontmatter(meta, ["ck_schema", "skill_version", "revision", "updated_at", "lifecycle"], body)


def protected_projection(kernel: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "project": kernel["target"]["项目"],
        "north_star": kernel["target"]["北极星"],
        "in_scope": kernel["scope"]["范围内"],
        "out_of_scope": kernel["scope"]["范围外"],
        "hard_constraints": kernel["scope"]["硬约束"],
        "accountable_owner": kernel["responsibility"]["最终责任人"],
    }


def responsibility_projection(kernel: Dict[str, Any]) -> Dict[str, str]:
    return dict(kernel["responsibility"])


def execution_projection(kernel: Dict[str, Any]) -> Dict[str, str]:
    return {key: value for key, value in kernel["responsibility"].items() if key != "最终责任人"}


def assert_external_draft(path: Path, rt: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    runtime_resolved = rt.resolve()
    try:
        resolved.relative_to(runtime_resolved)
    except ValueError:
        return resolved
    raise KernelError(f"{label} must be outside {RUNTIME_DIR_NAME}; use --adopt-current for audited manual edits")


def stable_digest(value: Any) -> str:
    return sha256_bytes(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"))


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def validate_timestamp(value: Any, field: str) -> None:
    if not isinstance(value, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
        raise KernelError(f"{field} must be UTC ISO-8601 seconds ending in Z")
    try:
        dt.datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
    except ValueError as exc:
        raise KernelError(f"{field} is not a valid timestamp: {value}") from exc


def validate_runtime_manifest_data(data: Any) -> Dict[str, Any]:
    if not isinstance(data, dict) or list(data.keys()) != sorted(RUNTIME_MANIFEST_KEYS):
        # JSON is rendered sort_keys=True, so canonical manifests must have sorted keys.
        expected = sorted(RUNTIME_MANIFEST_KEYS)
        actual = list(data.keys()) if isinstance(data, dict) else type(data).__name__
        raise KernelError(f"Manifest must contain exactly canonical keys {expected}; got {actual}")
    if data["schema"] != MANIFEST_SCHEMA or data["skill_name"] != SKILL_NAME or data["display_name_zh"] != DISPLAY_NAME_ZH:
        raise KernelError("Manifest identity mismatch")
    if data["skill_version"] != VERSION or data["runtime_dir"] != RUNTIME_DIR_NAME:
        raise KernelError("Manifest version/runtime mismatch")
    if not isinstance(data["revision"], int) or isinstance(data["revision"], bool) or data["revision"] < 0:
        raise KernelError("Manifest revision must be a non-negative integer")
    validate_timestamp(data["created_at"], "Manifest created_at")
    validate_timestamp(data["updated_at"], "Manifest updated_at")
    if data["created_at"] > data["updated_at"]:
        raise KernelError("Manifest created_at cannot be later than updated_at")
    files = data["files"]
    if not isinstance(files, dict) or set(files) != {KERNEL_FILE, DECISIONS_FILE, HANDOFF_FILE}:
        raise KernelError("Manifest files must contain exactly KERNEL.md, DECISIONS.md and HANDOFF.md")
    for filename, entry in files.items():
        if entry is None:
            if filename in PERSISTENT_MD_FILES:
                raise KernelError(f"Manifest cannot omit persistent file {filename}")
            continue
        if not isinstance(entry, dict) or set(entry) != {"bytes", "sha256"}:
            raise KernelError(f"Invalid file metadata for {filename}")
        if not isinstance(entry["bytes"], int) or isinstance(entry["bytes"], bool) or entry["bytes"] < 0:
            raise KernelError(f"Invalid byte count for {filename}")
        if not is_sha256(entry["sha256"]):
            raise KernelError(f"Invalid SHA-256 for {filename}")
    if not is_sha256(data["protected_digest"]) or not is_sha256(data["responsibility_digest"]) or not is_sha256(data["execution_digest"]):
        raise KernelError("Manifest control digests must be SHA-256")
    core = data["decision_core_digests"]
    statuses = data["decision_statuses"]
    if not isinstance(core, dict) or not isinstance(statuses, dict) or set(core) != set(statuses):
        raise KernelError("Manifest decision digest/status keys must match")
    for identifier, digest in core.items():
        if not ID_PATTERNS["decisions"].fullmatch(identifier) or not is_sha256(digest):
            raise KernelError(f"Invalid decision digest entry: {identifier}")
        if statuses[identifier] not in DECISION_STATES:
            raise KernelError(f"Invalid decision status in manifest: {identifier}")
    op = data["last_operation"]
    if not isinstance(op, dict) or set(op) != {"at", "result", "route"}:
        raise KernelError("Manifest last_operation must contain exactly at/result/route")
    if op["route"] not in {"init", "checkpoint", "handoff", "handover", "trim"}:
        raise KernelError(f"Invalid manifest route: {op['route']}")
    clean_single_line(op["result"], "Manifest operation result", max_chars=40)
    validate_timestamp(op["at"], "Manifest last_operation.at")
    if data["limits"] != LIMITS:
        raise KernelError("Manifest limits differ from this Skill version")
    return data


def decision_core(decision: Dict[str, Any]) -> Dict[str, Any]:
    fields = decision["fields"]
    return {
        "title": decision["title"],
        "date": fields["日期"],
        "owner": fields["决策责任人"],
        "decision": fields["决策"],
        "why": fields["理由"],
        "evidence": fields["证据"],
        "impact": fields["影响"],
        "replaces": fields["替代"],
        "revisit": fields["复审触发"],
    }


def file_meta_from_text(text: str) -> Dict[str, Any]:
    data = normalize_text(text).encode("utf-8")
    return {"sha256": sha256_bytes(data), "bytes": len(data)}


def read_manifest(rt: Path) -> Dict[str, Any]:
    path = rt / RUNTIME_MANIFEST_FILE
    if not path.exists():
        raise KernelError(f"Missing {RUNTIME_MANIFEST_FILE}: {path}")
    if path.is_symlink() or not path.is_file():
        raise KernelError(f"Manifest must be a regular file: {path}")
    if path.stat().st_size > MAX_JSON_FILE_BYTES:
        raise KernelError(f"Runtime manifest is too large: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise KernelError(f"Invalid runtime manifest: {path}") from exc
    return validate_runtime_manifest_data(data)


def render_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def atomic_write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(temp_path, path)
        try:
            dir_fd = os.open(str(path.parent), os.O_DIRECTORY)
        except (AttributeError, OSError):
            dir_fd = None
        if dir_fd is not None:
            try:
                os.fsync(dir_fd)
            finally:
                os.close(dir_fd)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def encode_optional(data: Optional[bytes]) -> Optional[str]:
    return None if data is None else base64.b64encode(data).decode("ascii")


def decode_optional(data: Optional[str]) -> Optional[bytes]:
    if data is None:
        return None
    if not isinstance(data, str):
        raise KernelError("Transaction payload must be base64 text or null")
    if len(data) > MAX_JSON_FILE_BYTES * 2:
        raise KernelError("Transaction payload is too large")
    try:
        decoded = base64.b64decode(data.encode("ascii"), validate=True)
    except Exception as exc:
        raise KernelError("Invalid base64 transaction payload") from exc
    if len(decoded) > MAX_JSON_FILE_BYTES:
        raise KernelError("Decoded transaction payload is too large")
    return decoded


def process_alive(pid: Any) -> bool:
    if not isinstance(pid, int) or isinstance(pid, bool) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def parse_transaction_journal(txn_path: Path) -> Dict[str, Any]:
    if txn_path.is_symlink() or not txn_path.is_file():
        raise KernelError(f"Transaction journal must be a regular file: {txn_path}")
    if txn_path.stat().st_size > MAX_TRANSACTION_JOURNAL_BYTES:
        raise KernelError(f"Transaction journal exceeds {MAX_TRANSACTION_JOURNAL_BYTES} bytes")
    try:
        txn = json.loads(txn_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise KernelError(f"Unreadable transaction journal: {txn_path}") from exc
    if not isinstance(txn, dict) or set(txn) != {"schema", "state", "created_at", "entries"}:
        raise KernelError("Transaction journal has unexpected fields")
    if txn["schema"] != TXN_SCHEMA or txn["state"] not in {"PREPARED", "APPLYING", "COMMITTED"}:
        raise KernelError("Transaction journal schema/state is invalid")
    validate_timestamp(txn["created_at"], "Transaction created_at")
    entries = txn["entries"]
    if not isinstance(entries, list) or not 1 <= len(entries) <= len(ALLOWED_TRANSACTION_TARGETS):
        raise KernelError("Transaction journal must contain 1-4 entries")
    seen: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict) or set(entry) != {"name", "before", "after", "before_sha256", "after_sha256"}:
            raise KernelError("Transaction entry has unexpected fields")
        name = entry["name"]
        if name not in ALLOWED_TRANSACTION_TARGETS or name in seen:
            raise KernelError(f"Unsafe or duplicate transaction target: {name}")
        seen.add(name)
        for side in ["before", "after"]:
            decoded = decode_optional(entry[side])
            expected = entry[f"{side}_sha256"]
            if decoded is None:
                if expected is not None:
                    raise KernelError(f"Transaction {side} hash must be null when payload is null")
            elif not is_sha256(expected) or sha256_bytes(decoded) != expected:
                raise KernelError(f"Transaction {side} payload hash mismatch for {name}")
    return txn


@contextlib.contextmanager
def runtime_lock(rt: Path, stale_seconds: int = 900) -> Iterator[None]:
    rt.mkdir(parents=True, exist_ok=True)
    lock_path = rt / LOCK_FILE
    lock_id = uuid.uuid4().hex
    host = socket.gethostname()
    payload = {"lock_id": lock_id, "pid": os.getpid(), "host": host, "created_at": utc_now(), "created_epoch": time.time()}
    for _ in range(2):
        try:
            fd = os.open(str(lock_path), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(payload, fh, ensure_ascii=False, sort_keys=True)
                fh.flush()
                os.fsync(fh.fileno())
            break
        except FileExistsError:
            if lock_path.is_symlink():
                raise KernelError(f"Lock path must not be a symlink: {lock_path}")
            try:
                before_stat = lock_path.stat()
            except FileNotFoundError:
                continue
            try:
                existing = json.loads(lock_path.read_text(encoding="utf-8"))
                created_epoch = existing.get("created_epoch")
                if isinstance(created_epoch, (int, float)) and not isinstance(created_epoch, bool):
                    age = max(0.0, time.time() - float(created_epoch))
                else:
                    age = max(0.0, time.time() - before_stat.st_mtime)
                same_host_live = existing.get("host") == host and process_alive(existing.get("pid"))
            except Exception:
                # A just-created lock can be temporarily empty or partial. Treat a
                # recent malformed lock as active; only reclaim it after its file
                # age crosses the stale threshold.
                age = max(0.0, time.time() - before_stat.st_mtime)
                same_host_live = False
            if same_host_live or age <= stale_seconds:
                raise KernelError(f"Context Kernel is locked by another operation: {lock_path}")
            try:
                current_stat = lock_path.stat()
            except FileNotFoundError:
                continue
            identity_before = (before_stat.st_dev, before_stat.st_ino, before_stat.st_mtime_ns, before_stat.st_size)
            identity_now = (current_stat.st_dev, current_stat.st_ino, current_stat.st_mtime_ns, current_stat.st_size)
            if identity_before != identity_now:
                continue
            lock_path.unlink(missing_ok=True)
    else:
        raise KernelError("Could not acquire Context Kernel lock")
    try:
        yield
    finally:
        if lock_path.exists():
            try:
                existing = json.loads(lock_path.read_text(encoding="utf-8"))
            except Exception:
                existing = {}
            if existing.get("lock_id") == lock_id:
                lock_path.unlink(missing_ok=True)
            else:
                raise KernelError("Lock ownership changed during operation; refusing to remove another lock")


def recover_transaction(rt: Path) -> Optional[str]:
    txn_path = rt / TXN_FILE
    if not txn_path.exists():
        return None
    txn = parse_transaction_journal(txn_path)
    entries = txn["entries"]
    if txn["state"] == "COMMITTED":
        for entry in entries:
            path = rt / entry["name"]
            after = decode_optional(entry["after"])
            if after is None:
                if path.exists():
                    raise KernelError(f"Committed transaction conflict: expected deletion of {entry['name']}")
            elif not path.exists() or path.is_symlink() or sha256_bytes(path.read_bytes()) != entry["after_sha256"]:
                raise KernelError(f"Committed transaction conflict: {entry['name']} does not match committed after-image")
        txn_path.unlink(missing_ok=True)
        return "FINALIZED_COMMITTED_TRANSACTION"

    for entry in entries:
        path = rt / entry["name"]
        before = decode_optional(entry["before"])
        if before is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, before)
    for entry in entries:
        path = rt / entry["name"]
        before = decode_optional(entry["before"])
        if before is None and path.exists():
            raise KernelError(f"Rollback failed to delete {entry['name']}")
        if before is not None and (not path.exists() or sha256_bytes(path.read_bytes()) != entry["before_sha256"]):
            raise KernelError(f"Rollback failed to restore {entry['name']}")
    txn_path.unlink(missing_ok=True)
    return "ROLLED_BACK_INCOMPLETE_TRANSACTION"


def commit_transaction(rt: Path, updates: Mapping[str, Optional[bytes]]) -> None:
    txn_path = rt / TXN_FILE
    if txn_path.exists():
        raise KernelError("Pending transaction exists; run validate --repair first")
    if not updates:
        raise KernelError("Empty transaction is not allowed")
    entries: List[Dict[str, Any]] = []
    for name in sorted(updates):
        if name not in ALLOWED_TRANSACTION_TARGETS:
            raise KernelError(f"Unsafe transaction target: {name}")
        path = rt / name
        if path.is_symlink():
            raise KernelError(f"Transaction target must not be a symlink: {name}")
        before = path.read_bytes() if path.exists() else None
        after = updates[name]
        if after is not None and not isinstance(after, bytes):
            raise KernelError(f"Transaction after-image must be bytes or null: {name}")
        for image, label in [(before, "before"), (after, "after")]:
            if image is not None and len(image) > MAX_JSON_FILE_BYTES:
                raise KernelError(f"Transaction {label}-image is too large: {name}")
        entries.append({
            "name": name,
            "before": encode_optional(before),
            "after": encode_optional(after),
            "before_sha256": sha256_bytes(before) if before is not None else None,
            "after_sha256": sha256_bytes(after) if after is not None else None,
        })
    txn = {"schema": TXN_SCHEMA, "state": "PREPARED", "created_at": utc_now(), "entries": entries}
    journal = render_json(txn).encode("utf-8")
    if len(journal) > MAX_TRANSACTION_JOURNAL_BYTES:
        raise KernelError("Transaction journal would exceed size limit")
    atomic_write(txn_path, journal)
    txn["state"] = "APPLYING"
    atomic_write(txn_path, render_json(txn).encode("utf-8"))
    for entry in entries:
        path = rt / entry["name"]
        after = decode_optional(entry["after"])
        if after is None:
            path.unlink(missing_ok=True)
        else:
            atomic_write(path, after)
    txn["state"] = "COMMITTED"
    atomic_write(txn_path, render_json(txn).encode("utf-8"))
    for entry in entries:
        path = rt / entry["name"]
        after = decode_optional(entry["after"])
        if after is None and path.exists():
            raise KernelError(f"Transaction deletion did not commit: {entry['name']}")
        if after is not None and (not path.exists() or sha256_bytes(path.read_bytes()) != entry["after_sha256"]):
            raise KernelError(f"Transaction write did not commit: {entry['name']}")
    txn_path.unlink(missing_ok=True)


def scan_security(text: str, filename: str) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for pattern in SECRET_PATTERNS:
        if pattern.search(text):
            issues.append(ValidationIssue("ERROR", "SECRET_LIKE_CONTENT", "Potential credential or private key detected", filename))
    for pattern in THOUGHT_PATTERNS:
        if pattern.search(text):
            issues.append(ValidationIssue("ERROR", "HIDDEN_REASONING_CONTENT", "Hidden reasoning / chain-of-thought content is not allowed", filename))
    return issues


def validate_limits(kernel: Dict[str, Any], decisions: Dict[str, Any], handoff_text: Optional[str] = None) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    counts = {
        "completed": len(kernel["completed"]),
        "in_progress": len(kernel["in_progress"]),
        "blockers": len(kernel["blockers"]),
        "unknowns": len(kernel["unknowns"]),
        "risks": len(kernel["risks"]),
        "decision_refs": len(kernel["decision_refs"]),
        "next_actions": len(kernel["actions"]),
        "evidence": len(kernel["evidence"]),
        "do_not_repeat": len(kernel["do_not_repeat"]),
    }
    key_to_limit = {
        "completed": "max_completed",
        "in_progress": "max_in_progress",
        "blockers": "max_blockers",
        "unknowns": "max_unknowns",
        "risks": "max_risks",
        "decision_refs": "max_decision_refs",
        "next_actions": "max_next_actions",
        "evidence": "max_evidence",
        "do_not_repeat": "max_do_not_repeat",
    }
    for key, count in counts.items():
        limit = LIMITS[key_to_limit[key]]
        if count > limit:
            issues.append(ValidationIssue("ERROR", "COUNT_LIMIT", f"{key} has {count} items; limit is {limit}", KERNEL_FILE))
    kernel_units = context_units(kernel["text"])
    if kernel_units > LIMITS["kernel_context_units"]:
        issues.append(ValidationIssue("ERROR", "KERNEL_BUDGET", f"KERNEL uses {kernel_units} context units; limit is {LIMITS['kernel_context_units']}", KERNEL_FILE))
    decisions_units = context_units(decisions["text"])
    if decisions_units > LIMITS["decisions_context_units"]:
        issues.append(ValidationIssue("ERROR", "DECISIONS_BUDGET", f"DECISIONS uses {decisions_units} context units; limit is {LIMITS['decisions_context_units']}", DECISIONS_FILE))
    if handoff_text is not None:
        handoff_units = context_units(handoff_text)
        if handoff_units > LIMITS["handoff_context_units"]:
            issues.append(ValidationIssue("ERROR", "HANDOFF_BUDGET", f"HANDOFF uses {handoff_units} context units; limit is {LIMITS['handoff_context_units']}", HANDOFF_FILE))
    return issues


def validate_decision_refs(kernel: Dict[str, Any], decisions: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    for ref in kernel["decision_refs"]:
        identifier = ref["id"]
        decision = decisions["decisions"].get(identifier)
        if decision is None:
            issues.append(ValidationIssue("ERROR", "MISSING_DECISION", f"Referenced decision {identifier} does not exist", KERNEL_FILE))
            continue
        if decision["fields"]["状态"] != "ACCEPTED":
            issues.append(ValidationIssue("ERROR", "INACTIVE_DECISION", f"Referenced decision {identifier} is not ACCEPTED", KERNEL_FILE))
        if len(ref["parts"]) != 2 or ref["parts"][1] != decision["title"]:
            issues.append(ValidationIssue("ERROR", "DECISION_TITLE_MISMATCH", f"Reference {identifier} must use exact title: {decision['title']}", KERNEL_FILE))
    return issues


def parse_handoff(text: str) -> Dict[str, Any]:
    meta, body = parse_frontmatter(text)
    required = [
        "ck_schema", "skill_version", "generated_at", "kind", "transfer_id", "bound_revision",
        "bound_kernel_sha256", "bound_decisions_sha256", "from_executor", "to_executor", "reason",
    ]
    if list(meta.keys()) != required:
        raise KernelError(f"HANDOFF frontmatter must contain exactly {required}")
    if meta["ck_schema"] != HANDOFF_SCHEMA or meta["skill_version"] != VERSION:
        raise KernelError("HANDOFF schema or version mismatch")
    validate_timestamp(meta["generated_at"], "HANDOFF generated_at")
    if meta["kind"] not in {"CONTEXT", "TRANSFER"}:
        raise KernelError("HANDOFF kind must be CONTEXT or TRANSFER")
    if meta["kind"] == "CONTEXT" and meta["transfer_id"] != "无":
        raise KernelError("CONTEXT handoff must use transfer_id '无'")
    if meta["kind"] == "TRANSFER" and not re.fullmatch(r"T-\d{14}-[A-F0-9]{6}", str(meta["transfer_id"])):
        raise KernelError("TRANSFER handoff requires a valid transfer_id")
    if not isinstance(meta["bound_revision"], int) or isinstance(meta["bound_revision"], bool) or meta["bound_revision"] < 0:
        raise KernelError("HANDOFF bound_revision must be a non-negative integer")
    if not is_sha256(meta["bound_kernel_sha256"]) or not is_sha256(meta["bound_decisions_sha256"]):
        raise KernelError("HANDOFF bound hashes must be SHA-256")
    for field in ["from_executor", "to_executor", "reason"]:
        clean_single_line(meta[field], f"HANDOFF {field}")

    prefix, sections, order = split_h2_sections(body)
    expected_prefix = (
        f"# {DISPLAY_NAME_ZH}｜交接快照\n\n"
        "> 这是绑定已提交 Kernel 的派生快照。发生 revision 或 hash 变化后即失效，不是第二事实源。"
    )
    if prefix.strip() != expected_prefix:
        raise KernelError("HANDOFF title or authority notice is missing or changed")
    if order != HANDOFF_SECTION_ORDER:
        raise KernelError(f"HANDOFF sections must be exactly {HANDOFF_SECTION_ORDER}; got {order}")
    return {"meta": meta, "body": body, "sections": sections, "text": normalize_text(text)}


def validate_handoff_relationship(handoff: Dict[str, Any], kernel: Dict[str, Any]) -> List[ValidationIssue]:
    issues: List[ValidationIssue] = []
    meta = handoff["meta"]
    resp = kernel["responsibility"]
    if meta["kind"] == "CONTEXT":
        if resp["移交状态"] == "PREPARED":
            issues.append(ValidationIssue("ERROR", "HANDOFF_KIND_MISMATCH", "PREPARED responsibility transfer requires a TRANSFER handoff", HANDOFF_FILE))
        if meta["from_executor"] != resp["当前执行主体"]:
            issues.append(ValidationIssue("ERROR", "HANDOFF_SOURCE_MISMATCH", "CONTEXT handoff source must equal current executor", HANDOFF_FILE))
    else:
        if resp["移交状态"] not in {"PREPARED", "CLOSED"}:
            issues.append(ValidationIssue("ERROR", "HANDOFF_KIND_MISMATCH", "TRANSFER handoff requires PREPARED or CLOSED transfer state", HANDOFF_FILE))
        if meta["transfer_id"] != resp["移交编号"]:
            issues.append(ValidationIssue("ERROR", "HANDOFF_TRANSFER_MISMATCH", "HANDOFF transfer ID differs from KERNEL", HANDOFF_FILE))
        if meta["from_executor"] != resp["移交来源主体"]:
            issues.append(ValidationIssue("ERROR", "HANDOFF_SOURCE_MISMATCH", "TRANSFER handoff source differs from KERNEL", HANDOFF_FILE))
        if meta["to_executor"] != resp["目标执行主体"]:
            issues.append(ValidationIssue("ERROR", "HANDOFF_TARGET_MISMATCH", "TRANSFER handoff target differs from KERNEL", HANDOFF_FILE))
    return issues


def validate_runtime(root: Path, *, strict: bool = False, verify_manifest_hashes: bool = True) -> Tuple[List[ValidationIssue], Optional[Dict[str, Any]], Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    rt = runtime_dir(root)
    issues: List[ValidationIssue] = []
    assert_safe_runtime_path(rt)
    if not rt.exists():
        return [ValidationIssue("ERROR", "MISSING_RUNTIME", f"Missing {RUNTIME_DIR_NAME} directory", str(rt))], None, None, None

    for path in rt.iterdir():
        if path.is_symlink():
            issues.append(ValidationIssue("ERROR", "SYMLINK", "Symlinks are not allowed in runtime directory", path.name))
            continue
        if path.name not in ALLOWED_RUNTIME_ENTRIES or not path.is_file():
            issues.append(ValidationIssue("ERROR", "EXTRA_RUNTIME_ENTRY", f"Unexpected runtime entry: {path.name}", path.name))
    if (rt / TXN_FILE).exists():
        issues.append(ValidationIssue("ERROR", "PENDING_TRANSACTION", "Incomplete transaction journal exists; run validate --repair", TXN_FILE))
    lock_path = rt / LOCK_FILE
    if lock_path.exists() and not lock_path.is_symlink():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            own_live_lock = lock_data.get("host") == socket.gethostname() and lock_data.get("pid") == os.getpid()
            if not own_live_lock:
                issues.append(ValidationIssue("WARNING", "ACTIVE_LOCK", "Another operation may be using this runtime", LOCK_FILE))
        except Exception:
            issues.append(ValidationIssue("WARNING", "LOCK_STATE_UNKNOWN", "Lock file is unreadable or malformed", LOCK_FILE))

    md_files = sorted(path.name for path in rt.glob("*.md") if path.is_file())
    unexpected_md = [name for name in md_files if name not in ACTIVE_MD_FILES]
    if unexpected_md:
        issues.append(ValidationIssue("ERROR", "EXTRA_MARKDOWN", f"Unexpected Markdown files: {unexpected_md}", RUNTIME_DIR_NAME))
    if len(md_files) > LIMITS["max_active_markdown_files"]:
        issues.append(ValidationIssue("ERROR", "MARKDOWN_LIMIT", f"Found {len(md_files)} Markdown files; limit is 3", RUNTIME_DIR_NAME))
    for required in sorted(PERSISTENT_MD_FILES):
        if not (rt / required).exists():
            issues.append(ValidationIssue("ERROR", "MISSING_PERSISTENT_FILE", f"Missing required file {required}", required))

    kernel = decisions = manifest = None
    handoff = None
    if not any(issue.code == "MISSING_PERSISTENT_FILE" for issue in issues):
        try:
            kernel_text = safe_read_text(rt / KERNEL_FILE)
            decisions_text = safe_read_text(rt / DECISIONS_FILE)
            kernel = parse_kernel(kernel_text)
            decisions = parse_decisions(decisions_text)
            issues.extend(scan_security(kernel_text, KERNEL_FILE))
            issues.extend(scan_security(decisions_text, DECISIONS_FILE))
            issues.extend(validate_decision_refs(kernel, decisions))
            handoff_text = None
            if (rt / HANDOFF_FILE).exists():
                handoff_text = safe_read_text(rt / HANDOFF_FILE)
                handoff = parse_handoff(handoff_text)
                issues.extend(scan_security(handoff_text, HANDOFF_FILE))
                fresh = True
                if handoff["meta"]["bound_revision"] != kernel["meta"]["revision"]:
                    fresh = False
                    issues.append(ValidationIssue("WARNING", "STALE_HANDOFF", "HANDOFF revision does not match current KERNEL revision", HANDOFF_FILE))
                if handoff["meta"]["bound_kernel_sha256"] != sha256_text(kernel_text):
                    fresh = False
                    issues.append(ValidationIssue("WARNING", "STALE_HANDOFF", "HANDOFF kernel hash does not match current KERNEL", HANDOFF_FILE))
                if handoff["meta"]["bound_decisions_sha256"] != sha256_text(decisions_text):
                    fresh = False
                    issues.append(ValidationIssue("WARNING", "STALE_HANDOFF", "HANDOFF decisions hash does not match current DECISIONS", HANDOFF_FILE))
                if fresh:
                    issues.extend(validate_handoff_relationship(handoff, kernel))
            issues.extend(validate_limits(kernel, decisions, handoff_text))
        except KernelError as exc:
            issues.append(ValidationIssue("ERROR", "SCHEMA", str(exc)))

    try:
        manifest = read_manifest(rt)
    except KernelError as exc:
        issues.append(ValidationIssue("ERROR", "MANIFEST", str(exc), RUNTIME_MANIFEST_FILE))

    if kernel is not None and manifest is not None:
        if manifest["revision"] != kernel["meta"]["revision"]:
            issues.append(ValidationIssue("ERROR", "REVISION_MISMATCH", "Manifest revision differs from KERNEL revision", RUNTIME_MANIFEST_FILE))
        if manifest["protected_digest"] != stable_digest(protected_projection(kernel)):
            issues.append(ValidationIssue("ERROR", "PROTECTED_DIGEST_MISMATCH", "Protected governance digest differs from KERNEL", RUNTIME_MANIFEST_FILE))
        if manifest["responsibility_digest"] != stable_digest(responsibility_projection(kernel)):
            issues.append(ValidationIssue("ERROR", "RESPONSIBILITY_DIGEST_MISMATCH", "Responsibility digest differs from KERNEL", RUNTIME_MANIFEST_FILE))
        if manifest["execution_digest"] != stable_digest(execution_projection(kernel)):
            issues.append(ValidationIssue("ERROR", "EXECUTION_DIGEST_MISMATCH", "Execution/transfer digest differs from KERNEL", RUNTIME_MANIFEST_FILE))
        if verify_manifest_hashes:
            for filename in [KERNEL_FILE, DECISIONS_FILE, HANDOFF_FILE]:
                expected = manifest["files"][filename]
                path = rt / filename
                if expected is None:
                    if path.exists():
                        issues.append(ValidationIssue("ERROR", "UNTRACKED_FILE", f"{filename} exists but manifest has no hash", filename))
                    continue
                if not path.exists():
                    issues.append(ValidationIssue("ERROR", "MISSING_TRACKED_FILE", f"Manifest tracks missing file {filename}", filename))
                else:
                    actual = file_meta(path)
                    if actual != expected:
                        issues.append(ValidationIssue("ERROR", "UNCOMMITTED_MANUAL_CHANGE", f"{filename} hash/size differs from manifest; use checkpoint drafts or audited adopt-current", filename))

    if decisions is not None and manifest is not None:
        current_digests = {identifier: stable_digest(decision_core(decision)) for identifier, decision in decisions["decisions"].items()}
        current_statuses = {identifier: decision["fields"]["状态"] for identifier, decision in decisions["decisions"].items()}
        if manifest["decision_core_digests"] != current_digests:
            issues.append(ValidationIssue("ERROR", "DECISION_DIGEST_MISMATCH", "Decision cores differ from manifest", RUNTIME_MANIFEST_FILE))
        if manifest["decision_statuses"] != current_statuses:
            issues.append(ValidationIssue("ERROR", "DECISION_STATUS_MISMATCH", "Decision statuses differ from manifest", RUNTIME_MANIFEST_FILE))

    if strict:
        for issue in issues:
            if issue.level == "WARNING":
                issue.level = "ERROR"
    return issues, kernel, decisions, manifest


def ensure_valid_or_raise(root: Path, *, allow_stale_handoff: bool = True) -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any], List[ValidationIssue]]:
    issues, kernel, decisions, manifest = validate_runtime(root, strict=False)
    errors = [issue for issue in issues if issue.level == "ERROR"]
    if not allow_stale_handoff:
        errors += [issue for issue in issues if issue.code == "STALE_HANDOFF"]
    if errors or kernel is None or decisions is None or manifest is None:
        raise KernelError("Runtime validation failed:\n" + "\n".join(str(issue) for issue in errors or issues))
    return kernel, decisions, manifest, issues


def compare_decision_immutability(old: Dict[str, Any], new: Dict[str, Any], *, trim_mode: bool = False) -> None:
    allowed_transitions = {
        "PROPOSED": {"PROPOSED", "ACCEPTED", "REJECTED"},
        "ACCEPTED": {"ACCEPTED", "SUPERSEDED"},
        "SUPERSEDED": {"SUPERSEDED"},
        "REJECTED": {"REJECTED"},
    }
    for identifier, old_decision in old["decisions"].items():
        if identifier not in new["decisions"]:
            raise KernelError(f"Existing decision {identifier} cannot be deleted")
        new_decision = new["decisions"][identifier]
        old_state = old_decision["fields"]["状态"]
        new_state = new_decision["fields"]["状态"]
        if trim_mode and new_state != old_state:
            raise KernelError(f"trim cannot change decision status {identifier}: {old_state} -> {new_state}")
        if new_state not in allowed_transitions[old_state]:
            raise KernelError(f"Invalid decision status transition {identifier}: {old_state} -> {new_state}")
        if stable_digest(decision_core(old_decision)) != stable_digest(decision_core(new_decision)):
            if not trim_mode or old_state not in {"SUPERSEDED", "REJECTED"}:
                raise KernelError(f"Existing decision core cannot be silently rewritten: {identifier}")
            old_core = decision_core(old_decision)
            new_core = decision_core(new_decision)
            for field in ["title", "date", "owner", "replaces"]:
                if old_core[field] != new_core[field]:
                    raise KernelError(f"Trim cannot change {field} of decision {identifier}")


def semantic_text_for_change(text: str) -> str:
    meta, body = parse_frontmatter(text)
    meta = dict(meta)
    meta.pop("revision", None)
    meta.pop("updated_at", None)
    return render_frontmatter(meta, list(meta.keys()), body)


def make_runtime_manifest(rt: Path, kernel_text: str, decisions_text: str, previous: Optional[Dict[str, Any]],
                          route: str, result: str, now: str, handoff_text: Optional[str] = None,
                          handoff_delete: bool = False) -> Dict[str, Any]:
    kernel = parse_kernel(kernel_text)
    decisions = parse_decisions(decisions_text)
    files: Dict[str, Any] = {
        KERNEL_FILE: file_meta_from_text(kernel_text),
        DECISIONS_FILE: file_meta_from_text(decisions_text),
        HANDOFF_FILE: None,
    }
    existing_handoff = rt / HANDOFF_FILE
    if handoff_delete:
        files[HANDOFF_FILE] = None
    elif handoff_text is not None:
        files[HANDOFF_FILE] = file_meta_from_text(handoff_text)
    elif existing_handoff.exists():
        files[HANDOFF_FILE] = file_meta(existing_handoff)
    return {
        "schema": MANIFEST_SCHEMA,
        "skill_name": SKILL_NAME,
        "display_name_zh": DISPLAY_NAME_ZH,
        "skill_version": VERSION,
        "runtime_dir": RUNTIME_DIR_NAME,
        "revision": kernel["meta"]["revision"],
        "created_at": previous.get("created_at", now) if previous else now,
        "updated_at": now,
        "files": files,
        "protected_digest": stable_digest(protected_projection(kernel)),
        "responsibility_digest": stable_digest(responsibility_projection(kernel)),
        "execution_digest": stable_digest(execution_projection(kernel)),
        "decision_core_digests": {
            identifier: stable_digest(decision_core(decision)) for identifier, decision in decisions["decisions"].items()
        },
        "decision_statuses": {
            identifier: decision["fields"]["状态"] for identifier, decision in decisions["decisions"].items()
        },
        "last_operation": {"route": route, "result": result, "at": now},
        "limits": LIMITS,
    }


def validate_candidate(kernel_text: str, decisions_text: str) -> Tuple[Dict[str, Any], Dict[str, Any], List[ValidationIssue]]:
    kernel = parse_kernel(kernel_text)
    decisions = parse_decisions(decisions_text)
    issues = []
    issues.extend(scan_security(kernel_text, KERNEL_FILE))
    issues.extend(scan_security(decisions_text, DECISIONS_FILE))
    issues.extend(validate_decision_refs(kernel, decisions))
    issues.extend(validate_limits(kernel, decisions))
    errors = [issue for issue in issues if issue.level == "ERROR"]
    if errors:
        raise KernelError("Candidate validation failed:\n" + "\n".join(str(issue) for issue in errors))
    return kernel, decisions, issues


def update_frontmatter_for_commit(kernel_text: str, decisions_text: str, revision: int, now: str) -> Tuple[str, str]:
    kmeta, kbody = parse_frontmatter(kernel_text)
    kmeta["revision"] = revision
    kmeta["updated_at"] = now
    kernel_text = render_frontmatter(kmeta, ["ck_schema", "skill_version", "revision", "updated_at", "lifecycle"], kbody)
    dmeta, dbody = parse_frontmatter(decisions_text)
    dmeta["updated_at"] = now
    decisions_text = render_frontmatter(dmeta, ["ck_schema", "skill_version", "updated_at"], dbody)
    return kernel_text, decisions_text


def apply_checkpoint(root: Path, kernel_draft: Path, decisions_draft: Optional[Path], expected_revision: int,
                     reason: str, allow_governance_change: bool, decision_id: Optional[str]) -> Dict[str, Any]:
    reason = clean_single_line(reason, "checkpoint reason")
    rt = runtime_dir(root)
    kernel_draft = assert_external_draft(kernel_draft, rt, "kernel draft")
    if decisions_draft is not None:
        decisions_draft = assert_external_draft(decisions_draft, rt, "decisions draft")
    with runtime_lock(rt):
        recover_transaction(rt)
        old_kernel, old_decisions, manifest, _ = ensure_valid_or_raise(root)
        if old_kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Stale checkpoint: expected revision {expected_revision}, current is {old_kernel['meta']['revision']}")
        if old_kernel["responsibility"]["移交状态"] == "PREPARED":
            raise KernelError("checkpoint is frozen while handover is PREPARED; accept or cancel first")
        kernel_text = safe_read_text(kernel_draft)
        decisions_text = safe_read_text(decisions_draft) if decisions_draft else old_decisions["text"]
        candidate_kernel, candidate_decisions, _ = validate_candidate(kernel_text, decisions_text)
        if candidate_kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Kernel draft revision must be {expected_revision}; got {candidate_kernel['meta']['revision']}")
        if execution_projection(candidate_kernel) != execution_projection(old_kernel):
            raise KernelError("checkpoint cannot change execution responsibility or transfer fields; use handover")
        governance_changed = protected_projection(candidate_kernel) != protected_projection(old_kernel)
        if governance_changed:
            if not allow_governance_change or not decision_id:
                raise KernelError("Governance fields changed without --allow-governance-change and --decision-id")
            decision = candidate_decisions["decisions"].get(decision_id)
            referenced = {ref["id"] for ref in candidate_kernel["decision_refs"]}
            if not decision or decision["fields"]["状态"] != "ACCEPTED" or decision_id not in referenced:
                raise KernelError(f"Governance change requires accepted and referenced decision {decision_id}")
        compare_decision_immutability(old_decisions, candidate_decisions)
        semantic_old = semantic_text_for_change(old_kernel["text"]) + semantic_text_for_change(old_decisions["text"])
        semantic_new = semantic_text_for_change(candidate_kernel["text"]) + semantic_text_for_change(candidate_decisions["text"])
        if semantic_old == semantic_new:
            return {"route": "checkpoint", "result": "NO_CHANGE", "revision": expected_revision, "files": [], "validation": "PASS", "reason": reason}
        now = utc_now()
        new_revision = expected_revision + 1
        kernel_text, decisions_text = update_frontmatter_for_commit(kernel_text, decisions_text, new_revision, now)
        validate_candidate(kernel_text, decisions_text)
        had_handoff = (rt / HANDOFF_FILE).exists()
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions_text, manifest, "checkpoint", "COMMITTED", now, handoff_delete=True)
        updates: Dict[str, Optional[bytes]] = {
            KERNEL_FILE: kernel_text.encode("utf-8"), DECISIONS_FILE: decisions_text.encode("utf-8"),
            HANDOFF_FILE: None, RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        }
        commit_transaction(rt, updates)
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-checkpoint validation failed:\n" + "\n".join(str(issue) for issue in errors))
        files = [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE] + ([HANDOFF_FILE] if had_handoff else [])
        return {"route": "checkpoint", "result": "COMMITTED", "revision": new_revision, "files": files, "validation": "PASS", "reason": reason}


def adopt_current(root: Path, expected_revision: int, reason: str, allow_governance_change: bool,
                  decision_id: Optional[str]) -> Dict[str, Any]:
    reason = clean_single_line(reason, "checkpoint reason")
    rt = runtime_dir(root)
    with runtime_lock(rt):
        recover_transaction(rt)
        manifest = read_manifest(rt)
        if manifest["revision"] != expected_revision:
            raise KernelError(f"Stale adopt-current: expected revision {expected_revision}, manifest is {manifest['revision']}")
        for path in rt.iterdir():
            if path.is_symlink() or path.name not in ALLOWED_RUNTIME_ENTRIES or not path.is_file():
                raise KernelError(f"Unsafe or unexpected runtime entry: {path.name}")
        kernel_text = safe_read_text(rt / KERNEL_FILE)
        decisions_text = safe_read_text(rt / DECISIONS_FILE)
        kernel, decisions, _ = validate_candidate(kernel_text, decisions_text)
        if kernel["meta"]["revision"] != expected_revision:
            raise KernelError("Manual draft must retain the current revision before adopt-current")
        k_changed = file_meta(rt / KERNEL_FILE) != manifest["files"][KERNEL_FILE]
        d_changed = file_meta(rt / DECISIONS_FILE) != manifest["files"][DECISIONS_FILE]
        if not k_changed and not d_changed:
            raise KernelError("No KERNEL.md or DECISIONS.md changes to adopt; regenerate or remove HANDOFF separately")
        current_protected = stable_digest(protected_projection(kernel))
        if current_protected != manifest["protected_digest"]:
            if not allow_governance_change or not decision_id:
                raise KernelError("Manual changes touched governance fields; explicit authorization and accepted decision required")
            decision = decisions["decisions"].get(decision_id)
            referenced = {ref["id"] for ref in kernel["decision_refs"]}
            if not decision or decision["fields"]["状态"] != "ACCEPTED" or decision_id not in referenced:
                raise KernelError(f"Governance change requires accepted and referenced decision {decision_id}")
        if stable_digest(execution_projection(kernel)) != manifest["execution_digest"]:
            raise KernelError("Manual changes touched execution responsibility or transfer fields; use handover")
        old_core = manifest["decision_core_digests"]
        old_statuses = manifest["decision_statuses"]
        allowed = {
            "PROPOSED": {"PROPOSED", "ACCEPTED", "REJECTED"},
            "ACCEPTED": {"ACCEPTED", "SUPERSEDED"},
            "SUPERSEDED": {"SUPERSEDED"}, "REJECTED": {"REJECTED"},
        }
        for identifier, digest in old_core.items():
            decision = decisions["decisions"].get(identifier)
            if decision is None:
                raise KernelError(f"Manual changes deleted decision {identifier}")
            if stable_digest(decision_core(decision)) != digest:
                raise KernelError(f"Manual changes rewrote existing decision {identifier}")
            if decision["fields"]["状态"] not in allowed[old_statuses[identifier]]:
                raise KernelError(f"Invalid manual decision status transition {identifier}: {old_statuses[identifier]} -> {decision['fields']['状态']}")
        now = utc_now()
        new_revision = expected_revision + 1
        kernel_text, decisions_text = update_frontmatter_for_commit(kernel_text, decisions_text, new_revision, now)
        validate_candidate(kernel_text, decisions_text)
        had_handoff = (rt / HANDOFF_FILE).exists()
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions_text, manifest, "checkpoint", "ADOPTED", now, handoff_delete=True)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"), DECISIONS_FILE: decisions_text.encode("utf-8"),
            HANDOFF_FILE: None, RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        })
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-adopt validation failed:\n" + "\n".join(str(issue) for issue in errors))
        files = [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE] + ([HANDOFF_FILE] if had_handoff else [])
        return {"route": "checkpoint", "result": "COMMITTED", "revision": new_revision, "files": files, "validation": "PASS", "reason": reason, "mode": "adopt-current"}


def bullet_lines(items: Sequence[Dict[str, Any]], max_items: Optional[int] = None) -> str:
    chosen = list(items[-max_items:] if max_items else items)
    if not chosen:
        return "- 无"
    return "\n".join(f"- {item['raw']}" for item in chosen)


def plain_bullet_lines(items: Sequence[str], max_items: Optional[int] = None) -> str:
    chosen = list(items[:max_items] if max_items else items)
    return "\n".join(f"- {item}" for item in chosen) if chosen else "- 无"


def decision_summary_lines(kernel: Dict[str, Any], decisions: Dict[str, Any]) -> str:
    lines: List[str] = []
    for ref in kernel["decision_refs"]:
        decision = decisions["decisions"].get(ref["id"])
        if decision:
            lines.append(f"- {ref['id']} | {decision['title']}")
    return "\n".join(lines) if lines else "- 无"


def handoff_text(kernel: Dict[str, Any], decisions: Dict[str, Any], to_executor: str, reason: str, now: str,
                 *, kind: str = "CONTEXT", transfer_id: str = "无", from_executor: Optional[str] = None) -> str:
    to_executor = clean_single_line(to_executor or "下一会话", "handoff recipient")
    reason = clean_single_line(reason or "上下文边界", "handoff reason")
    source = clean_single_line(from_executor or kernel["responsibility"]["当前执行主体"], "handoff source")
    if kind not in {"CONTEXT", "TRANSFER"}:
        raise KernelError("Invalid handoff kind")
    if kind == "CONTEXT":
        transfer_id = "无"
    elif not re.fullmatch(r"T-\d{14}-[A-F0-9]{6}", transfer_id):
        raise KernelError("TRANSFER handoff requires valid transfer ID")
    meta = {
        "ck_schema": HANDOFF_SCHEMA,
        "skill_version": VERSION,
        "generated_at": now,
        "kind": kind,
        "transfer_id": transfer_id,
        "bound_revision": kernel["meta"]["revision"],
        "bound_kernel_sha256": sha256_text(kernel["text"]),
        "bound_decisions_sha256": sha256_text(decisions["text"]),
        "from_executor": source,
        "to_executor": to_executor,
        "reason": reason,
    }
    body = f"""# {DISPLAY_NAME_ZH}｜交接快照

> 这是绑定已提交 Kernel 的派生快照。发生 revision 或 hash 变化后即失效，不是第二事实源。

## 一句话恢复
继续项目“{kernel['target']['项目']}”，当前目标是“{kernel['target']['当前目标']}”，首先执行 {kernel['actions'][0]['raw'] if kernel['actions'] else '核验当前状态'}。

## 当前控制状态
- 类型：{kind}
- Revision：{kernel['meta']['revision']}
- Lifecycle：{kernel['meta']['lifecycle']}
- 阶段 / Gate：{kernel['target']['阶段 / Gate']}
- 来源执行主体：{source}
- 接收方：{to_executor}
- 移交状态：{kernel['responsibility']['移交状态']}
- 移交编号：{transfer_id}

## 当前任务
- 北极星：{kernel['target']['北极星']}
- 当前目标：{kernel['target']['当前目标']}
- 当前任务：{kernel['target']['当前任务']}

## 必须继承的约束
{plain_bullet_lines(kernel['scope']['硬约束'])}

## 已完成
{bullet_lines(kernel['completed'], max_items=8)}

## 进行中
{bullet_lines(kernel['in_progress'])}

## 阻塞
{bullet_lines(kernel['blockers'])}

## 未知与待验证
{bullet_lines(kernel['unknowns'])}

## 风险
{bullet_lines(kernel['risks'])}

## 必须继承的决策
{decision_summary_lines(kernel, decisions)}

## 下一步
{chr(10).join(f'{idx}. {item["raw"]}' for idx, item in enumerate(kernel['actions'], 1)) if kernel['actions'] else '- 无'}

## 证据入口
{bullet_lines(kernel['evidence'], max_items=12)}

## 不要重复
{bullet_lines(kernel['do_not_repeat'])}

## 恢复规则
1. 先校验本文件绑定的 revision 与两个 SHA-256。
2. 读取 `KERNEL.md`，再只读取其中引用的 Decision。
3. 先输出最小 Context Check；发现冲突、陈旧状态或待接受移交时停止实质执行。
4. 不读取完整聊天，不重复已验证工作，不把本快照反向覆盖 Kernel。
"""
    return render_frontmatter(meta, [
        "ck_schema", "skill_version", "generated_at", "kind", "transfer_id", "bound_revision",
        "bound_kernel_sha256", "bound_decisions_sha256", "from_executor", "to_executor", "reason",
    ], body)


def apply_handoff(root: Path, to_executor: str, reason: str) -> Dict[str, Any]:
    to_executor = clean_single_line(to_executor or "下一会话", "handoff recipient")
    reason = clean_single_line(reason or "上下文边界", "handoff reason")
    rt = runtime_dir(root)
    with runtime_lock(rt):
        recover_transaction(rt)
        kernel, decisions, manifest, issues = ensure_valid_or_raise(root)
        if kernel["responsibility"]["移交状态"] == "PREPARED":
            raise KernelError("A responsibility transfer is PREPARED; use handover accept/cancel, not context handoff")
        existing = None
        if (rt / HANDOFF_FILE).exists() and not any(issue.code == "STALE_HANDOFF" for issue in issues):
            existing = parse_handoff(safe_read_text(rt / HANDOFF_FILE))
        if existing and existing["meta"]["kind"] == "CONTEXT" and existing["meta"]["to_executor"] == to_executor and existing["meta"]["reason"] == reason:
            return {"route": "handoff", "result": "NO_CHANGE", "revision": kernel["meta"]["revision"], "files": [], "validation": "PASS", "next": "在新上下文运行 resume"}
        now = utc_now()
        text = handoff_text(kernel, decisions, to_executor, reason, now, kind="CONTEXT")
        parse_handoff(text)
        limit_issues = validate_limits(kernel, decisions, text)
        if any(issue.level == "ERROR" for issue in limit_issues):
            raise KernelError("Generated handoff exceeds limits:\n" + "\n".join(str(issue) for issue in limit_issues))
        new_manifest = make_runtime_manifest(rt, kernel["text"], decisions["text"], manifest, "handoff", "COMMITTED", now, handoff_text=text)
        commit_transaction(rt, {HANDOFF_FILE: text.encode("utf-8"), RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8")})
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-handoff validation failed:\n" + "\n".join(str(issue) for issue in errors))
        return {"route": "handoff", "result": "COMMITTED", "revision": kernel["meta"]["revision"], "files": [HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "next": "在新上下文运行 resume"}


def modify_responsibility_text(kernel: Dict[str, Any], updates: Mapping[str, str], new_revision: int, now: str) -> str:
    return render_kernel_with_updates(kernel, revision=new_revision, updated_at=now, responsibility_updates=updates)


def handover_prepare(root: Path, to_executor: str, reason: str, expected_revision: int) -> Dict[str, Any]:
    to_executor = clean_single_line(to_executor, "handover target")
    reason = clean_single_line(reason, "handover reason")
    if to_executor == "无":
        raise KernelError("handover target must not be '无'")
    rt = runtime_dir(root)
    with runtime_lock(rt):
        recover_transaction(rt)
        kernel, decisions, manifest, _ = ensure_valid_or_raise(root)
        if kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Stale handover prepare: expected {expected_revision}, current {kernel['meta']['revision']}")
        if kernel["meta"]["lifecycle"] == "COMPLETE":
            raise KernelError("Completed work has no active execution responsibility to transfer; use handoff")
        if kernel["responsibility"]["移交状态"] == "PREPARED":
            raise KernelError("A handover is already PREPARED; accept or cancel it first")
        source = kernel["responsibility"]["当前执行主体"]
        if to_executor == source:
            raise KernelError("handover target is already the current executor; use handoff instead")
        now = utc_now()
        transfer_id = f"T-{dt.datetime.now(dt.timezone.utc).strftime('%Y%m%d%H%M%S')}-{uuid.uuid4().hex[:6].upper()}"
        new_revision = expected_revision + 1
        kernel_text = modify_responsibility_text(kernel, {
            "移交状态": "PREPARED", "移交编号": transfer_id, "移交来源主体": source,
            "目标执行主体": to_executor, "移交原因": reason,
        }, new_revision, now)
        new_kernel = parse_kernel(kernel_text)
        text = handoff_text(new_kernel, decisions, to_executor, reason, now, kind="TRANSFER", transfer_id=transfer_id, from_executor=source)
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions["text"], manifest, "handover", "PREPARED", now, handoff_text=text)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"), HANDOFF_FILE: text.encode("utf-8"),
            RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        })
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-prepare validation failed:\n" + "\n".join(str(issue) for issue in errors))
        return {"route": "handover", "result": "PREPARED", "revision": new_revision, "transfer_id": transfer_id, "files": [KERNEL_FILE, HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "next": "目标执行主体核验后运行 handover accept"}


def handover_accept(root: Path, as_executor: str, transfer_id: str, expected_revision: int) -> Dict[str, Any]:
    as_executor = clean_single_line(as_executor, "accepting executor")
    transfer_id = clean_single_line(transfer_id, "transfer ID", max_chars=40)
    rt = runtime_dir(root)
    with runtime_lock(rt):
        recover_transaction(rt)
        kernel, decisions, manifest, issues = ensure_valid_or_raise(root, allow_stale_handoff=False)
        if kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Stale handover accept: expected {expected_revision}, current {kernel['meta']['revision']}")
        resp = kernel["responsibility"]
        if resp["移交状态"] != "PREPARED":
            raise KernelError("No PREPARED handover exists")
        if transfer_id != resp["移交编号"]:
            raise KernelError("Transfer ID does not match the PREPARED handover")
        if as_executor != resp["目标执行主体"]:
            raise KernelError("Accepting executor does not match handover target")
        if any(issue.code == "STALE_HANDOFF" for issue in issues) or not (rt / HANDOFF_FILE).exists():
            raise KernelError("Cannot accept a missing or stale handoff")
        current_handoff = parse_handoff(safe_read_text(rt / HANDOFF_FILE))
        if current_handoff["meta"]["kind"] != "TRANSFER" or current_handoff["meta"]["transfer_id"] != transfer_id:
            raise KernelError("Cannot accept a non-matching transfer handoff")
        now = utc_now()
        new_revision = expected_revision + 1
        kernel_text = modify_responsibility_text(kernel, {"当前执行主体": as_executor, "移交状态": "CLOSED"}, new_revision, now)
        new_kernel = parse_kernel(kernel_text)
        text = handoff_text(
            new_kernel, decisions, as_executor, f"已接受移交 {transfer_id}", now,
            kind="TRANSFER", transfer_id=transfer_id, from_executor=resp["移交来源主体"],
        )
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions["text"], manifest, "handover", "CLOSED", now, handoff_text=text)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"), HANDOFF_FILE: text.encode("utf-8"),
            RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        })
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-accept validation failed:\n" + "\n".join(str(issue) for issue in errors))
        return {"route": "handover", "result": "CLOSED", "revision": new_revision, "transfer_id": transfer_id, "files": [KERNEL_FILE, HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "next": "新执行主体运行 resume"}


def handover_cancel(root: Path, transfer_id: str, expected_revision: int, reason: str) -> Dict[str, Any]:
    transfer_id = clean_single_line(transfer_id, "transfer ID", max_chars=40)
    reason = clean_single_line(reason or f"取消 {transfer_id}", "handover cancellation reason")
    rt = runtime_dir(root)
    with runtime_lock(rt):
        recover_transaction(rt)
        kernel, decisions, manifest, _ = ensure_valid_or_raise(root)
        if kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Stale handover cancel: expected {expected_revision}, current {kernel['meta']['revision']}")
        resp = kernel["responsibility"]
        if resp["移交状态"] != "PREPARED" or transfer_id != resp["移交编号"]:
            raise KernelError("No matching PREPARED handover exists")
        now = utc_now()
        new_revision = expected_revision + 1
        kernel_text = modify_responsibility_text(kernel, {"移交状态": "CANCELLED", "移交原因": reason}, new_revision, now)
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions["text"], manifest, "handover", "CANCELLED", now, handoff_delete=True)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"), HANDOFF_FILE: None,
            RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        })
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-cancel validation failed:\n" + "\n".join(str(issue) for issue in errors))
        return {"route": "handover", "result": "CANCELLED", "revision": new_revision, "transfer_id": transfer_id, "files": [KERNEL_FILE, HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "next": "由当前执行主体继续或重新 prepare"}


def normalize_markdown_safely(text: str) -> str:
    text = normalize_text(text)
    lines = text.splitlines()
    out: List[str] = []
    blank = False
    for line in lines:
        if not line.strip():
            if not blank:
                out.append("")
            blank = True
        else:
            out.append(line.rstrip())
            blank = False
    return normalize_text("\n".join(out))


def items_by_id(items: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    return {item["id"]: item for item in items}


def evidence_references(kernel: Dict[str, Any], decisions: Dict[str, Any]) -> set[str]:
    chunks: List[str] = []
    for category in ["completed", "in_progress", "blockers", "unknowns", "risks", "actions", "do_not_repeat"]:
        chunks.extend(item["raw"] for item in kernel[category])
    chunks.extend(decision["raw"] for decision in decisions["decisions"].values())
    return set(re.findall(r"E-\d{4}", "\n".join(chunks)))


def assert_trim_preserves_semantics(old_kernel: Dict[str, Any], new_kernel: Dict[str, Any],
                                    old_decisions: Dict[str, Any], new_decisions: Dict[str, Any]) -> None:
    if old_kernel["meta"]["lifecycle"] != new_kernel["meta"]["lifecycle"]:
        raise KernelError("trim cannot change lifecycle")
    if old_kernel["target"] != new_kernel["target"]:
        raise KernelError("trim cannot change project, objective, task or phase/Gate")
    if old_kernel["scope"] != new_kernel["scope"]:
        raise KernelError("trim cannot change scope, constraints or preferences")
    if responsibility_projection(old_kernel) != responsibility_projection(new_kernel):
        raise KernelError("trim cannot change responsibility or transfer state")

    for category in ["in_progress", "blockers", "unknowns", "risks", "decision_refs", "actions", "do_not_repeat"]:
        if [item["raw"] for item in old_kernel[category]] != [item["raw"] for item in new_kernel[category]]:
            raise KernelError(f"trim must preserve active {category} items exactly and in order")

    for category in ["completed", "evidence"]:
        old_items = items_by_id(old_kernel[category])
        new_items = items_by_id(new_kernel[category])
        if not set(new_items).issubset(old_items):
            raise KernelError(f"trim cannot add new {category} items")
        for identifier, item in new_items.items():
            if item["raw"] != old_items[identifier]["raw"]:
                raise KernelError(f"trim cannot rewrite retained {category} item {identifier}")
        expected_order = [item["id"] for item in old_kernel[category] if item["id"] in new_items]
        if [item["id"] for item in new_kernel[category]] != expected_order:
            raise KernelError(f"trim cannot reorder retained {category} items")

    required_evidence = evidence_references(new_kernel, new_decisions)
    available_evidence = {item["id"] for item in new_kernel["evidence"]}
    missing = required_evidence - available_evidence
    if missing:
        raise KernelError(f"trim cannot drop referenced evidence IDs: {sorted(missing)}")

    if list(old_decisions["decisions"]) != list(new_decisions["decisions"]):
        raise KernelError("trim cannot add, delete or reorder decision records")
    compare_decision_immutability(old_decisions, new_decisions, trim_mode=True)


def apply_trim(root: Path, expected_revision: int, *, auto: bool, kernel_draft: Optional[Path],
               decisions_draft: Optional[Path]) -> Dict[str, Any]:
    rt = runtime_dir(root)
    if not auto:
        if kernel_draft is None:
            raise KernelError("Semantic trim requires --kernel-draft")
        kernel_draft = assert_external_draft(kernel_draft, rt, "kernel draft")
        if decisions_draft is not None:
            decisions_draft = assert_external_draft(decisions_draft, rt, "decisions draft")
    with runtime_lock(rt):
        recover_transaction(rt)
        old_kernel, old_decisions, manifest, _ = ensure_valid_or_raise(root)
        if old_kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Stale trim: expected {expected_revision}, current {old_kernel['meta']['revision']}")
        if old_kernel["responsibility"]["移交状态"] == "PREPARED":
            raise KernelError("trim is frozen while handover is PREPARED; accept or cancel first")
        had_handoff = (rt / HANDOFF_FILE).exists()

        if auto:
            kernel_text = normalize_markdown_safely(old_kernel["text"])
            decisions_text = normalize_markdown_safely(old_decisions["text"])
            validate_candidate(kernel_text, decisions_text)
            changed_files: Dict[str, Optional[bytes]] = {}
            if kernel_text != old_kernel["text"]:
                changed_files[KERNEL_FILE] = kernel_text.encode("utf-8")
            if decisions_text != old_decisions["text"]:
                changed_files[DECISIONS_FILE] = decisions_text.encode("utf-8")
            if had_handoff:
                changed_files[HANDOFF_FILE] = None
            if not changed_files:
                return {"route": "trim", "result": "NO_CHANGE", "revision": expected_revision, "files": [], "validation": "PASS", "before_units": context_units(old_kernel["text"]) + context_units(old_decisions["text"]), "after_units": context_units(old_kernel["text"]) + context_units(old_decisions["text"])}
            now = utc_now()
            new_manifest = make_runtime_manifest(rt, kernel_text, decisions_text, manifest, "trim", "CLEANED", now, handoff_delete=True)
            changed_files[RUNTIME_MANIFEST_FILE] = render_json(new_manifest).encode("utf-8")
            commit_transaction(rt, changed_files)
            errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
            if errors:
                raise KernelError("Post-auto-trim validation failed:\n" + "\n".join(str(issue) for issue in errors))
            return {
                "route": "trim", "result": "COMMITTED", "revision": expected_revision,
                "files": list(changed_files), "validation": "PASS",
                "before_units": context_units(old_kernel["text"]) + context_units(old_decisions["text"]),
                "after_units": context_units(kernel_text) + context_units(decisions_text),
                "next": "运行 resume 验证恢复质量",
            }

        kernel_text = safe_read_text(kernel_draft)
        decisions_text = safe_read_text(decisions_draft) if decisions_draft else old_decisions["text"]
        new_kernel, new_decisions, _ = validate_candidate(kernel_text, decisions_text)
        if new_kernel["meta"]["revision"] != expected_revision:
            raise KernelError(f"Trim draft revision must be {expected_revision}; got {new_kernel['meta']['revision']}")
        assert_trim_preserves_semantics(old_kernel, new_kernel, old_decisions, new_decisions)
        old_units = context_units(old_kernel["text"]) + context_units(old_decisions["text"])
        new_units = context_units(new_kernel["text"]) + context_units(new_decisions["text"])
        semantic_old = semantic_text_for_change(old_kernel["text"]) + semantic_text_for_change(old_decisions["text"])
        semantic_new = semantic_text_for_change(new_kernel["text"]) + semantic_text_for_change(new_decisions["text"])
        if semantic_old == semantic_new:
            if not had_handoff:
                return {"route": "trim", "result": "NO_CHANGE", "revision": expected_revision, "files": [], "validation": "PASS", "before_units": old_units, "after_units": new_units}
            now = utc_now()
            new_manifest = make_runtime_manifest(rt, old_kernel["text"], old_decisions["text"], manifest, "trim", "CLEANED", now, handoff_delete=True)
            commit_transaction(rt, {HANDOFF_FILE: None, RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8")})
            return {"route": "trim", "result": "COMMITTED", "revision": expected_revision, "files": [HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "before_units": old_units, "after_units": old_units}
        if new_units >= old_units:
            raise KernelError(f"Semantic trim must reduce context units: before {old_units}, after {new_units}")
        now = utc_now()
        new_revision = expected_revision + 1
        kernel_text, decisions_text = update_frontmatter_for_commit(kernel_text, decisions_text, new_revision, now)
        validate_candidate(kernel_text, decisions_text)
        new_manifest = make_runtime_manifest(rt, kernel_text, decisions_text, manifest, "trim", "COMMITTED", now, handoff_delete=True)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"), DECISIONS_FILE: decisions_text.encode("utf-8"),
            HANDOFF_FILE: None, RUNTIME_MANIFEST_FILE: render_json(new_manifest).encode("utf-8"),
        })
        errors = [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"]
        if errors:
            raise KernelError("Post-trim validation failed:\n" + "\n".join(str(issue) for issue in errors))
        files = [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE] + ([HANDOFF_FILE] if had_handoff else [])
        return {"route": "trim", "result": "COMMITTED", "revision": new_revision, "files": files, "validation": "PASS", "before_units": old_units, "after_units": context_units(kernel_text) + context_units(decisions_text), "next": "运行 resume 验证恢复质量"}


def resume_summary(kernel: Dict[str, Any], decisions: Dict[str, Any], issues: Sequence[ValidationIssue],
                   handoff_present: bool = False) -> Dict[str, Any]:
    warnings = [issue.as_dict() for issue in issues if issue.level == "WARNING"]
    lifecycle = kernel["meta"]["lifecycle"]
    transfer_state = kernel["responsibility"]["移交状态"]
    if transfer_state == "PREPARED":
        permission = "STOP_HANDOVER_PENDING"
    elif lifecycle == "COMPLETE":
        permission = "NO_ACTIVE_TASK"
    elif lifecycle == "PAUSED":
        permission = "STOP_PAUSED"
    elif lifecycle == "NOT_STARTED":
        permission = "START_CONTEXT_GATE_ONLY"
    elif lifecycle == "BLOCKED" or kernel["blockers"]:
        permission = "EXECUTE_UNBLOCKING_ONLY"
    else:
        permission = "CONTINUE_ACTIVE_TASK"
    relevant_decisions = []
    for ref in kernel["decision_refs"]:
        decision = decisions["decisions"].get(ref["id"])
        if decision:
            relevant_decisions.append({"id": ref["id"], "title": decision["title"], "decision": decision["fields"]["决策"]})
    stale = any(issue.code == "STALE_HANDOFF" for issue in issues)
    return {
        "route": "resume", "result": "READ_ONLY", "revision": kernel["meta"]["revision"],
        "project": kernel["target"]["项目"], "north_star": kernel["target"]["北极星"],
        "lifecycle": lifecycle, "phase_gate": kernel["target"]["阶段 / Gate"],
        "current_objective": kernel["target"]["当前目标"], "active_task": kernel["target"]["当前任务"],
        "hard_constraints": kernel["scope"]["硬约束"],
        "accountable_owner": kernel["responsibility"]["最终责任人"],
        "responsible_executor": kernel["responsibility"]["当前执行主体"], "transfer_state": transfer_state,
        "blockers": [item["raw"] for item in kernel["blockers"]],
        "unknowns": [item["raw"] for item in kernel["unknowns"]],
        "risks": [item["raw"] for item in kernel["risks"]],
        "relevant_decisions": relevant_decisions,
        "next_action": kernel["actions"][0]["raw"] if kernel["actions"] else "无",
        "handoff_status": "STALE_IGNORED" if stale else ("FRESH" if handoff_present else "ABSENT"),
        "warnings": warnings, "validation": "PASS", "permission": permission,
    }


def render_resume_markdown(summary: Mapping[str, Any]) -> str:
    decision_ids = ", ".join(item["id"] for item in summary["relevant_decisions"]) or "无"
    blockers = "；".join(summary["blockers"]) or "无"
    unknowns = "；".join(summary["unknowns"]) or "无"
    risks = "；".join(summary["risks"]) or "无"
    constraints = "；".join(summary["hard_constraints"]) or "无"
    warnings = "；".join(item["code"] for item in summary["warnings"]) or "无"
    lines = [
        "# Context Check",
        f"- 项目 / Revision：{summary['project']} / {summary['revision']}",
        f"- 北极星：{summary['north_star']}",
        f"- 状态 / Gate：{summary['lifecycle']} / {summary['phase_gate']}",
        f"- 当前目标：{summary['current_objective']}",
        f"- 当前任务：{summary['active_task']}",
        f"- 硬约束：{constraints}",
        f"- 责任：{summary['accountable_owner']} / {summary['responsible_executor']} / {summary['transfer_state']}",
        f"- 阻塞：{blockers}",
        f"- 未知：{unknowns}",
        f"- 风险：{risks}",
        f"- 相关决策：{decision_ids}",
        f"- 首要下一步：{summary['next_action']}",
        f"- Handoff：{summary['handoff_status']}",
        f"- 校验 / 权限：{summary['validation']} / {summary['permission']}；警告：{warnings}",
    ]
    return "\n".join(lines) + "\n"


def do_init(root: Path, project: str, north_star: str, owner: str, executor: str) -> Dict[str, Any]:
    rt = runtime_dir(root)
    assert_safe_runtime_path(rt)
    if rt.exists() and any(rt.iterdir()):
        raise KernelError(f"Refusing to initialize non-empty runtime directory: {rt}")
    rt.mkdir(parents=True, exist_ok=True)
    with runtime_lock(rt):
        kernel_text = kernel_template(project, north_star, owner, executor)
        decisions_text = decisions_template()
        validate_candidate(kernel_text, decisions_text)
        now = utc_now()
        manifest = make_runtime_manifest(rt, kernel_text, decisions_text, None, "init", "COMMITTED", now, handoff_delete=True)
        commit_transaction(rt, {
            KERNEL_FILE: kernel_text.encode("utf-8"),
            DECISIONS_FILE: decisions_text.encode("utf-8"),
            RUNTIME_MANIFEST_FILE: render_json(manifest).encode("utf-8"),
        })
    return {"route": "init", "result": "COMMITTED", "revision": 0, "files": [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE], "validation": "PASS", "next": "核验初始化内容后执行 checkpoint"}


def package_root() -> Path:
    return Path(__file__).resolve().parent.parent


def validate_skill_md(path: Path) -> None:
    text = safe_read_text(path, max_bytes=64 * 1024)
    if len(text.splitlines()) > 500:
        raise KernelError("SKILL.md exceeds 500 lines")
    if not text.startswith("---\n") or "\n---\n" not in text[4:]:
        raise KernelError("SKILL.md YAML frontmatter is missing")
    end = text.find("\n---\n", 4)
    frontmatter = text[4:end]
    name_match = re.search(r"(?m)^name:\s*([^\n]+)$", frontmatter)
    desc_match = re.search(r"(?m)^description:\s*([^\n]+)$", frontmatter)
    version_match = re.search(r"(?m)^\s*version:\s*[\"']?([^\"'\n]+)", frontmatter)
    display_match = re.search(r"(?m)^\s*display_name_zh:\s*[\"']?([^\"'\n]+)", frontmatter)
    if not name_match or name_match.group(1).strip() != SKILL_NAME:
        raise KernelError("SKILL.md name must be context-kernel")
    if not desc_match or not (1 <= len(desc_match.group(1).strip()) <= 1024):
        raise KernelError("SKILL.md description must be 1-1024 characters on one line")
    if not version_match or version_match.group(1).strip() != VERSION:
        raise KernelError("SKILL.md metadata version mismatch")
    if not display_match or display_match.group(1).strip() != DISPLAY_NAME_ZH:
        raise KernelError("SKILL.md Chinese display name mismatch")
    for route in ["checkpoint", "handoff", "handover", "trim", "resume"]:
        if f"`{route}`" not in text:
            raise KernelError(f"SKILL.md is missing internal route {route}")
    if "活跃 Markdown 总数最多 3" not in text or "KERNEL.md" not in text or "DECISIONS.md" not in text or "HANDOFF.md" not in text:
        raise KernelError("SKILL.md is missing the three-Markdown runtime invariant")


def validate_package_manifest_data(manifest: Any) -> Dict[str, Any]:
    if not isinstance(manifest, dict) or set(manifest) != {"schema", "name", "display_name_zh", "version", "files"}:
        raise KernelError("Package manifest has unexpected fields")
    if manifest["schema"] != PACKAGE_SCHEMA or manifest["name"] != SKILL_NAME or manifest["display_name_zh"] != DISPLAY_NAME_ZH or manifest["version"] != VERSION:
        raise KernelError("Package manifest identity/version mismatch")
    files = manifest["files"]
    if not isinstance(files, list) or len(files) != len(PACKAGE_CONTENT_FILES):
        raise KernelError("Package manifest must list exactly the two payload files")
    seen: set[str] = set()
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != {"path", "sha256", "bytes"}:
            raise KernelError("Package file entry has unexpected fields")
        rel = entry["path"]
        if rel not in PACKAGE_CONTENT_FILES or rel in seen:
            raise KernelError(f"Unexpected or duplicate package path: {rel}")
        seen.add(rel)
        if not is_sha256(entry["sha256"]) or not isinstance(entry["bytes"], int) or isinstance(entry["bytes"], bool) or entry["bytes"] < 0:
            raise KernelError(f"Invalid package metadata for {rel}")
    if seen != PACKAGE_CONTENT_FILES:
        raise KernelError(f"Package manifest file set mismatch: {sorted(seen)}")
    return manifest


def verify_package(root: Optional[Path] = None) -> Dict[str, Any]:
    original = root or package_root()
    if original.is_symlink():
        raise KernelError(f"Skill package root must not be a symlink: {original}")
    root = original.resolve()
    if root.name != SKILL_NAME or not root.is_dir():
        raise KernelError(f"Skill package root directory must be named {SKILL_NAME}")
    allowed_paths = {"SKILL.md", "scripts", "scripts/context_kernel.py", PACKAGE_MANIFEST_FILE}
    actual_paths: set[str] = set()
    for path in root.rglob("*"):
        rel = str(path.relative_to(root)).replace(os.sep, "/")
        actual_paths.add(rel)
        if path.is_symlink():
            raise KernelError(f"Symlink is not allowed in Skill package: {rel}")
        if rel not in allowed_paths:
            raise KernelError(f"Unexpected package entry: {rel}")
        if rel == "scripts" and not path.is_dir():
            raise KernelError("scripts must be a directory")
        if rel != "scripts" and not path.is_file():
            raise KernelError(f"Package payload must be a regular file: {rel}")
    if actual_paths != allowed_paths:
        raise KernelError(f"Package layout mismatch; got {sorted(actual_paths)}")

    manifest_path = root / PACKAGE_MANIFEST_FILE
    if manifest_path.stat().st_size > MAX_JSON_FILE_BYTES:
        raise KernelError("Package manifest is too large")
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as exc:
        raise KernelError("Invalid package manifest") from exc
    validate_package_manifest_data(manifest)
    listed = set()
    for entry in manifest["files"]:
        rel = entry["path"]
        path = root / rel
        actual = file_meta(path)
        if actual != {"sha256": entry["sha256"], "bytes": entry["bytes"]}:
            raise KernelError(f"Package file integrity mismatch: {rel}")
        listed.add(rel)
    if listed != PACKAGE_CONTENT_FILES:
        raise KernelError("Package payload set differs from manifest")
    validate_skill_md(root / "SKILL.md")
    try:
        compile((root / "scripts" / "context_kernel.py").read_text(encoding="utf-8"), "context_kernel.py", "exec")
    except SyntaxError as exc:
        raise KernelError(f"Packaged Python script has syntax error: {exc}") from exc
    return {"result": "PASS", "version": VERSION, "files": len(listed) + 1, "markdown_files": 1, "layout": sorted(actual_paths)}


def install_skill(scope: Optional[str], target: Optional[Path], repo: Optional[Path], replace: bool) -> Dict[str, Any]:
    if target is not None and (scope is not None or repo is not None):
        raise KernelError("--target cannot be combined with --scope or --repo")
    if repo is not None and scope != "repo":
        raise KernelError("--repo is only valid with --scope repo")
    source = package_root()
    verify_package(source)
    home = Path.home()
    if target is not None:
        base = target.expanduser().resolve()
    elif scope == "user" or scope is None:
        base = (home / ".agents" / "skills").resolve()
    elif scope == "codex":
        base = (home / ".codex" / "skills").resolve()
    elif scope == "claude":
        base = (home / ".claude" / "skills").resolve()
    elif scope == "repo":
        if repo is None:
            raise KernelError("--scope repo requires --repo")
        base = (repo.expanduser().resolve() / ".agents" / "skills")
    else:
        raise KernelError(f"Unsupported install scope: {scope}")
    if base.exists() and (base.is_symlink() or not base.is_dir()):
        raise KernelError(f"Install base must be a real directory: {base}")
    base.mkdir(parents=True, exist_ok=True)
    destination = base / SKILL_NAME
    if destination.is_symlink() or (destination.exists() and not destination.is_dir()):
        raise KernelError(f"Destination must not be a symlink or non-directory: {destination}")
    if destination.exists() and not replace:
        raise KernelError(f"Destination exists; use --replace after review: {destination}")
    stage_parent = Path(tempfile.mkdtemp(prefix=f".{SKILL_NAME}.install-", dir=str(base)))
    stage = stage_parent / SKILL_NAME
    try:
        shutil.copytree(source, stage, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        verify_package(stage)
        old: Optional[Path] = None
        if destination.exists():
            old = base / f".{SKILL_NAME}.old-{uuid.uuid4().hex}"
            os.replace(destination, old)
        try:
            os.replace(stage, destination)
            verify_package(destination)
        except Exception:
            if destination.exists():
                shutil.rmtree(destination, ignore_errors=True)
            if old and old.exists():
                os.replace(old, destination)
            raise
        if old and old.exists():
            shutil.rmtree(old)
    finally:
        shutil.rmtree(stage_parent, ignore_errors=True)
    return {"route": "install", "result": "COMMITTED", "path": str(destination), "version": VERSION, "validation": "PASS", "next": "运行 self-test，然后在目标项目执行 init 或 resume"}


def print_result(data: Mapping[str, Any], output_format: str = "json") -> None:
    if output_format == "json":
        sys.stdout.write(render_json(data))
    else:
        for key in ["route", "result", "revision", "files", "validation", "next"]:
            if key in data:
                value = data[key]
                if isinstance(value, list):
                    value = ", ".join(str(x) for x in value) or "无"
                print(f"{key}: {value}")


def edit_kernel_text(text: str, *, target_updates: Optional[Mapping[str, str]] = None,
                     responsibility_updates: Optional[Mapping[str, str]] = None,
                     section_replacements: Optional[Mapping[Tuple[str, Optional[str]], str]] = None,
                     lifecycle: Optional[str] = None) -> str:
    meta, body = parse_frontmatter(text)
    prefix, sections, order = split_h2_sections(body)
    if target_updates:
        target = parse_key_bullets(sections["目标"], TARGET_KEYS)
        target.update(target_updates)
        sections["目标"] = "\n".join(f"- {key}：{target[key]}" for key in TARGET_KEYS) + "\n"
    if responsibility_updates:
        responsibility = parse_key_bullets(sections["责任"], RESPONSIBILITY_KEYS)
        responsibility.update(responsibility_updates)
        sections["责任"] = "\n".join(f"- {key}：{responsibility[key]}" for key in RESPONSIBILITY_KEYS) + "\n"
    if section_replacements:
        for (h2, h3), replacement in section_replacements.items():
            if h3 is None:
                sections[h2] = normalize_text(replacement)
            else:
                h3_prefix, h3_sections, h3_order = split_h3_sections(sections[h2])
                h3_sections[h3] = normalize_text(replacement)
                parts = [h3_prefix.rstrip()] if h3_prefix.rstrip() else []
                for name in h3_order:
                    parts.append(f"### {name}\n{h3_sections[name].rstrip()}")
                sections[h2] = "\n\n".join(parts) + "\n"
    parts = [prefix.rstrip()]
    for name in order:
        parts.append(f"## {name}\n{sections[name].rstrip()}")
    body = "\n\n".join(parts) + "\n"
    if lifecycle:
        meta["lifecycle"] = lifecycle
    return render_frontmatter(meta, ["ck_schema", "skill_version", "revision", "updated_at", "lifecycle"], body)


def append_decision_text(text: str, identifier: str, title: str, state: str = "ACCEPTED", replaces: str = "无") -> str:
    parsed = parse_decisions(text)
    if identifier in parsed["decisions"]:
        raise KernelError(f"Decision exists: {identifier}")
    meta, body = parse_frontmatter(text)
    _, sections, _ = split_h2_sections(body)
    index = parse_dash_items(sections["有效决策索引"])
    if state == "ACCEPTED":
        index.append(f"{identifier} | {title}")
    index_text = "\n".join(f"- {item}" for item in index) if index else "- 无"
    record = sections["决策记录"].rstrip()
    block = f"""

### {identifier} — {title}
- 状态：{state}
- 日期：{utc_now()[:10]}
- 决策责任人：Owner
- 决策：{title}
- 理由：测试或显式治理需要
- 证据：UNVERIFIED test fixture
- 影响：影响后续执行
- 替代：{replaces}
- 复审触发：前提发生变化
"""
    new_body = body
    new_body = re.sub(r"(?ms)^## 有效决策索引\n.*?(?=^## 决策记录\n)", f"## 有效决策索引\n{index_text}\n\n", new_body)
    new_body = new_body.rstrip() + block + "\n"
    return render_frontmatter(meta, ["ck_schema", "skill_version", "updated_at"], new_body)


def run_self_test() -> Dict[str, Any]:
    assertions = 0
    passed = 0
    details: List[str] = []

    def check(condition: bool, label: str) -> None:
        nonlocal assertions, passed
        assertions += 1
        if not condition:
            raise AssertionError(label)
        passed += 1
        details.append(label)

    def expect_error(fn: Any, text: str) -> None:
        nonlocal assertions, passed
        assertions += 1
        try:
            fn()
        except Exception as exc:
            if text not in str(exc):
                raise AssertionError(f"Expected error containing {text!r}, got {exc!r}") from exc
            passed += 1
            details.append(f"blocked:{text}")
            return
        raise AssertionError(f"Expected failure containing {text!r}")

    def txn_entry(name: str, before: Optional[bytes], after: Optional[bytes]) -> Dict[str, Any]:
        return {
            "name": name, "before": encode_optional(before), "after": encode_optional(after),
            "before_sha256": sha256_bytes(before) if before is not None else None,
            "after_sha256": sha256_bytes(after) if after is not None else None,
        }

    with tempfile.TemporaryDirectory(prefix="context-kernel-selftest-") as temp:
        base = Path(temp)
        root = base / "project"
        root.mkdir()
        result = do_init(root, "Self Test", "Maintain durable minimal context", "Owner", "LLM-A")
        rt = runtime_dir(root)
        check(result["revision"] == 0, "init revision 0")
        check(set(path.name for path in rt.iterdir()) == {KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE}, "init creates only two Markdown and manifest")
        check(len(list(rt.glob("*.md"))) == 2, "init active Markdown count is two")
        issues, kernel, decisions, manifest = validate_runtime(root, strict=True)
        check(not [issue for issue in issues if issue.level == "ERROR"], "strict validation after init")
        check(manifest is not None and manifest["revision"] == 0, "manifest revision matches init")
        check(resume_summary(kernel, decisions, issues)["permission"] == "START_CONTEXT_GATE_ONLY", "NOT_STARTED resume is gate-only")
        expect_error(lambda: do_init(root, "Again", "Goal", "Owner", "LLM-A"), "non-empty runtime")
        expect_error(lambda: kernel_template("bad\nproject", "Goal", "Owner", "LLM"), "single line")

        # First evidence-backed checkpoint and accepted decision.
        kernel_text = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            target_updates={"当前目标": "Complete self-test", "当前任务": "Exercise all five routes", "阶段 / Gate": "Test / G1"},
            section_replacements={
                ("当前状态", "已完成"): "- C-0001 | 初始化成功 | E-0001\n",
                ("当前状态", "进行中"): "- P-0001 | 执行路由测试\n",
                ("当前状态", "未知与待验证"): "- U-0001 | 故障恢复是否有效 | 验证：模拟未完成事务\n",
                ("当前状态", "风险"): "- R-0001 | 手工篡改可能污染状态 | 缓解：hash 与 digest 硬门\n",
                ("决策引用", None): "- D-0001 | 采用三文档上限\n",
                ("下一步", None): "1. A-0001 | 生成 handoff\n2. A-0002 | 测试 handover\n",
                ("证据", None): "- E-0001 | VERIFIED | .ramify/MANIFEST.json | 初始化文件与 hash 一致\n",
            },
            lifecycle="ACTIVE",
        )
        decisions_text = append_decision_text(safe_read_text(rt / DECISIONS_FILE), "D-0001", "采用三文档上限")
        kd = base / "KERNEL.draft.md"
        dd = base / "DECISIONS.draft.md"
        kd.write_text(kernel_text, encoding="utf-8")
        dd.write_text(decisions_text, encoding="utf-8")
        result = apply_checkpoint(root, kd, dd, 0, "self-test progress", False, None)
        check(result["revision"] == 1, "checkpoint increments revision")
        check(parse_kernel(safe_read_text(rt / KERNEL_FILE))["target"]["当前目标"] == "Complete self-test", "checkpoint updates objective")
        check(parse_decisions(safe_read_text(rt / DECISIONS_FILE))["index_ids"] == ["D-0001"], "accepted decision indexed")
        kd.write_text(safe_read_text(rt / KERNEL_FILE), encoding="utf-8")
        dd.write_text(safe_read_text(rt / DECISIONS_FILE), encoding="utf-8")
        check(apply_checkpoint(root, kd, dd, 1, "no change", False, None)["result"] == "NO_CHANGE", "no-change checkpoint creates no revision")
        expect_error(lambda: apply_checkpoint(root, rt / KERNEL_FILE, None, 1, "bad draft location", False, None), "outside .ramify")

        # Context handoff is derived, idempotent and does not transfer authority.
        result = apply_handoff(root, "Next Chat", "new chat")
        check(result["revision"] == 1 and result["result"] == "COMMITTED", "handoff commits without revision")
        check(len(list(rt.glob("*.md"))) == 3, "handoff raises active Markdown count to three")
        handoff = parse_handoff(safe_read_text(rt / HANDOFF_FILE))
        check(handoff["meta"]["kind"] == "CONTEXT" and handoff["meta"]["transfer_id"] == "无", "context handoff has explicit kind")
        check(handoff["meta"]["to_executor"] == "Next Chat", "handoff records recipient")
        check(parse_kernel(safe_read_text(rt / KERNEL_FILE))["responsibility"]["当前执行主体"] == "LLM-A", "handoff preserves executor")
        check(apply_handoff(root, "Next Chat", "new chat")["result"] == "NO_CHANGE", "identical handoff is idempotent")
        k, d, _, warnings = ensure_valid_or_raise(root)
        summary = resume_summary(k, d, warnings, True)
        check(summary["permission"] == "CONTINUE_ACTIVE_TASK", "ACTIVE resume grants task permission")
        check(summary["handoff_status"] == "FRESH", "resume recognizes fresh handoff")
        check(summary["hard_constraints"], "resume carries hard constraints")

        # Responsibility transfer: prepare freezes ordinary writes, accept changes executor.
        prepared = handover_prepare(root, "LLM-B", "responsibility transfer", 1)
        check(prepared["revision"] == 2 and prepared["result"] == "PREPARED", "handover prepare")
        current = parse_kernel(safe_read_text(rt / KERNEL_FILE))
        check(current["responsibility"]["当前执行主体"] == "LLM-A", "prepare preserves current executor")
        check(current["responsibility"]["移交来源主体"] == "LLM-A", "prepare records transfer source")
        check(current["responsibility"]["目标执行主体"] == "LLM-B", "prepare records transfer target")
        transfer_handoff = parse_handoff(safe_read_text(rt / HANDOFF_FILE))
        check(transfer_handoff["meta"]["kind"] == "TRANSFER" and transfer_handoff["meta"]["transfer_id"] == prepared["transfer_id"], "prepare creates bound transfer handoff")
        check(resume_summary(*ensure_valid_or_raise(root)[:2], ensure_valid_or_raise(root)[3])["permission"] == "STOP_HANDOVER_PENDING", "resume stops while handover pending")
        kd.write_text(safe_read_text(rt / KERNEL_FILE), encoding="utf-8")
        expect_error(lambda: apply_checkpoint(root, kd, None, 2, "frozen", False, None), "frozen while handover")
        expect_error(lambda: apply_trim(root, 2, auto=True, kernel_draft=None, decisions_draft=None), "frozen while handover")
        expect_error(lambda: apply_handoff(root, "Other", "wrong route"), "PREPARED")
        expect_error(lambda: handover_accept(root, "Wrong", prepared["transfer_id"], 2), "does not match handover target")
        accepted = handover_accept(root, "LLM-B", prepared["transfer_id"], 2)
        check(accepted["revision"] == 3 and accepted["result"] == "CLOSED", "handover accept closes transfer")
        current = parse_kernel(safe_read_text(rt / KERNEL_FILE))
        check(current["responsibility"]["当前执行主体"] == "LLM-B", "accept changes executor")
        check(current["responsibility"]["移交来源主体"] == "LLM-A", "closed transfer retains source")
        handoff = parse_handoff(safe_read_text(rt / HANDOFF_FILE))
        check(handoff["meta"]["from_executor"] == "LLM-A" and handoff["meta"]["to_executor"] == "LLM-B", "accepted handoff preserves transfer direction")

        # Checkpoint authority gates.
        bad_kernel = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            responsibility_updates={"当前执行主体": "Intruder", "目标执行主体": "Intruder"},
        )
        kd.write_text(bad_kernel, encoding="utf-8")
        expect_error(lambda: apply_checkpoint(root, kd, None, 3, "bad responsibility", False, None), "checkpoint cannot change")
        bad_kernel = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), target_updates={"北极星": "Changed without authority"})
        kd.write_text(bad_kernel, encoding="utf-8")
        expect_error(lambda: apply_checkpoint(root, kd, None, 3, "bad governance", False, None), "Governance fields changed")
        kd.write_text(safe_read_text(rt / KERNEL_FILE), encoding="utf-8")
        expect_error(lambda: apply_checkpoint(root, kd, None, 2, "stale", False, None), "Stale checkpoint")

        # Runtime cleanliness catches Markdown and non-Markdown pollution.
        extra_md = rt / "CHECKPOINT.md"
        extra_md.write_text("noise\n", encoding="utf-8")
        check(any(issue.code in {"EXTRA_MARKDOWN", "EXTRA_RUNTIME_ENTRY"} for issue in validate_runtime(root)[0]), "extra Markdown detected")
        extra_md.unlink()
        extra_txt = rt / "run.log"
        extra_txt.write_text("noise\n", encoding="utf-8")
        check(any(issue.code == "EXTRA_RUNTIME_ENTRY" for issue in validate_runtime(root)[0]), "extra non-Markdown detected")
        extra_txt.unlink()
        extra_dir = rt / "archive"
        extra_dir.mkdir()
        check(any(issue.code == "EXTRA_RUNTIME_ENTRY" for issue in validate_runtime(root)[0]), "nested runtime directory detected")
        extra_dir.rmdir()
        if hasattr(os, "symlink"):
            link = rt / "link"
            try:
                os.symlink(rt / KERNEL_FILE, link)
                check(any(issue.code == "SYMLINK" for issue in validate_runtime(root)[0]), "runtime symlink detected")
            finally:
                link.unlink(missing_ok=True)

        # Audited adoption accepts KERNEL/DECISIONS only and discards derived handoff.
        manual = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), target_updates={"当前任务": "Manual audited update"})
        (rt / KERNEL_FILE).write_text(manual, encoding="utf-8")
        check(any(issue.code == "UNCOMMITTED_MANUAL_CHANGE" for issue in validate_runtime(root)[0]), "manual edit detected")
        adopted = adopt_current(root, 3, "audited manual adoption", False, None)
        check(adopted["revision"] == 4, "adopt-current increments revision")
        check(not (rt / HANDOFF_FILE).exists(), "adopt-current deletes derived handoff")
        check(not [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"], "adopt-current restores strict integrity")
        expect_error(lambda: adopt_current(root, 4, "nothing", False, None), "No KERNEL.md or DECISIONS.md changes")

        # Any semantic checkpoint deletes an old handoff instead of retaining stale context.
        apply_handoff(root, "Next Chat", "refresh")
        current_text = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), target_updates={"当前任务": "Checkpoint after handoff"})
        kd.write_text(current_text, encoding="utf-8")
        applied = apply_checkpoint(root, kd, None, 4, "state changed", False, None)
        check(applied["revision"] == 5, "post-handoff checkpoint increments revision")
        check(not (rt / HANDOFF_FILE).exists(), "checkpoint removes invalidated handoff")
        check(not [issue for issue in validate_runtime(root, strict=True)[0] if issue.level == "ERROR"], "no stale handoff remains after checkpoint")

        # Auto trim is housekeeping: removes handoff without semantic revision.
        apply_handoff(root, "Next Chat", "cleanup test")
        trimmed = apply_trim(root, 5, auto=True, kernel_draft=None, decisions_draft=None)
        check(trimmed["result"] == "COMMITTED" and trimmed["revision"] == 5, "auto trim cleans without semantic revision")
        check(not (rt / HANDOFF_FILE).exists(), "auto trim removes handoff")
        check(apply_trim(root, 5, auto=True, kernel_draft=None, decisions_draft=None)["result"] == "NO_CHANGE", "clean auto trim is idempotent")

        # Manual trim may remove obsolete completion/evidence, but cannot rewrite active meaning.
        trim_kernel = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            section_replacements={("当前状态", "已完成"): "- 无\n", ("证据", None): "- 无\n"},
        )
        trim_draft = base / "KERNEL.trim.md"
        trim_draft.write_text(trim_kernel, encoding="utf-8")
        semantic_trim = apply_trim(root, 5, auto=False, kernel_draft=trim_draft, decisions_draft=None)
        check(semantic_trim["result"] == "COMMITTED" and semantic_trim["revision"] == 6, "semantic trim commits reduced context")
        rewritten_active = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            section_replacements={("当前状态", "进行中"): "- P-0001 | silently changed active meaning\n"},
        )
        trim_draft.write_text(rewritten_active, encoding="utf-8")
        expect_error(lambda: apply_trim(root, 6, auto=False, kernel_draft=trim_draft, decisions_draft=None), "preserve active in_progress")
        added_completed = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            section_replacements={("当前状态", "已完成"): "- C-0002 | UNVERIFIED historical claim\n"},
        )
        trim_draft.write_text(added_completed, encoding="utf-8")
        expect_error(lambda: apply_trim(root, 6, auto=False, kernel_draft=trim_draft, decisions_draft=None), "cannot add new completed")

        # Schema, evidence, budget and privacy gates.
        fake_credential = "api" + "_key = " + ("x" * 32)
        secret_kernel = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), section_replacements={("不要重复", None): f"- N-0001 | {fake_credential}\n"})
        expect_error(lambda: validate_candidate(secret_kernel, safe_read_text(rt / DECISIONS_FILE)), "SECRET_LIKE_CONTENT")
        thought_kernel = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), section_replacements={("不要重复", None): "- N-0001 | chain-of-thought transcript\n"})
        expect_error(lambda: validate_candidate(thought_kernel, safe_read_text(rt / DECISIONS_FILE)), "HIDDEN_REASONING_CONTENT")
        too_many = "\n".join(f"{index}. A-{index:04d} | step {index}" for index in range(1, 7)) + "\n"
        bad = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), section_replacements={("下一步", None): too_many})
        expect_error(lambda: validate_candidate(bad, safe_read_text(rt / DECISIONS_FILE)), "COUNT_LIMIT")
        bad = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), section_replacements={("当前状态", "已完成"): "- C-0002 | Unsupported completion\n"})
        expect_error(lambda: parse_kernel(bad), "must reference VERIFIED evidence")
        bad = edit_kernel_text(
            safe_read_text(rt / KERNEL_FILE),
            section_replacements={
                ("当前状态", "已完成"): "- C-0002 | Claimed complete | E-0002\n",
                ("证据", None): "- E-0002 | UNVERIFIED | pending | claim not checked\n",
            },
        )
        expect_error(lambda: parse_kernel(bad), "relies on UNVERIFIED evidence")
        complete_bad = edit_kernel_text(safe_read_text(rt / KERNEL_FILE), lifecycle="COMPLETE")
        expect_error(lambda: parse_kernel(complete_bad), "cannot contain in-progress")
        title_bad = safe_read_text(rt / KERNEL_FILE).replace("D-0001 | 采用三文档上限", "D-0001 | Wrong Title")
        expect_error(lambda: validate_candidate(title_bad, safe_read_text(rt / DECISIONS_FILE)), "DECISION_TITLE_MISMATCH")

        # Accepted decision core is append-only.
        decisions_bad = safe_read_text(rt / DECISIONS_FILE).replace("- 决策：采用三文档上限", "- 决策：静默改写")
        dd.write_text(decisions_bad, encoding="utf-8")
        kd.write_text(safe_read_text(rt / KERNEL_FILE), encoding="utf-8")
        expect_error(lambda: apply_checkpoint(root, kd, dd, 6, "rewrite decision", False, None), "cannot be silently rewritten")

        # Manifest tamper is detected, then restored.
        manifest_path = rt / RUNTIME_MANIFEST_FILE
        manifest_bytes = manifest_path.read_bytes()
        manifest_data = json.loads(manifest_bytes)
        manifest_data["limits"]["max_next_actions"] = 999
        manifest_path.write_text(render_json(manifest_data), encoding="utf-8")
        check(any(issue.code == "MANIFEST" for issue in validate_runtime(root)[0]), "manifest schema/control tamper detected")
        manifest_path.write_bytes(manifest_bytes)

        # Transaction recovery is safe and target-whitelisted.
        original = (rt / KERNEL_FILE).read_bytes()
        fake = b"broken"
        txn = {"schema": TXN_SCHEMA, "state": "PREPARED", "created_at": utc_now(), "entries": [txn_entry(KERNEL_FILE, original, fake)]}
        atomic_write(rt / TXN_FILE, render_json(txn).encode("utf-8"))
        atomic_write(rt / KERNEL_FILE, fake)
        check(recover_transaction(rt) == "ROLLED_BACK_INCOMPLETE_TRANSACTION", "PREPARED transaction rolls back")
        check((rt / KERNEL_FILE).read_bytes() == original, "rollback restores before-image")
        conflict = {"schema": TXN_SCHEMA, "state": "COMMITTED", "created_at": utc_now(), "entries": [txn_entry(KERNEL_FILE, original, fake)]}
        atomic_write(rt / TXN_FILE, render_json(conflict).encode("utf-8"))
        expect_error(lambda: recover_transaction(rt), "Committed transaction conflict")
        (rt / TXN_FILE).unlink()
        malicious = {"schema": TXN_SCHEMA, "state": "PREPARED", "created_at": utc_now(), "entries": [txn_entry("../../outside", None, b"x")]}
        atomic_write(rt / TXN_FILE, render_json(malicious).encode("utf-8"))
        expect_error(lambda: recover_transaction(rt), "Unsafe or duplicate transaction target")
        (rt / TXN_FILE).unlink()
        with runtime_lock(rt):
            expect_error(lambda: runtime_lock(rt).__enter__(), "locked by another operation")
        malformed_lock = rt / LOCK_FILE
        malformed_lock.write_text("{", encoding="utf-8")
        expect_error(lambda: runtime_lock(rt, stale_seconds=900).__enter__(), "locked by another operation")
        malformed_lock.unlink()
        malformed_lock.write_text("{", encoding="utf-8")
        old_time = time.time() - 10
        os.utime(malformed_lock, (old_time, old_time))
        with runtime_lock(rt, stale_seconds=1):
            check(True, "stale malformed lock is safely reclaimed")

        # Cancel path leaves audit fields but removes handoff.
        prep2 = handover_prepare(root, "Human-C", "test cancel", 6)
        cancel = handover_cancel(root, prep2["transfer_id"], prep2["revision"], "no longer needed")
        check(cancel["result"] == "CANCELLED" and cancel["revision"] == 8, "handover cancel")
        cancelled = parse_kernel(safe_read_text(rt / KERNEL_FILE))
        check(cancelled["responsibility"]["当前执行主体"] == "LLM-B", "cancel preserves source executor")
        check(cancelled["responsibility"]["移交来源主体"] == "LLM-B", "cancel retains audit source")
        check(not (rt / HANDOFF_FILE).exists(), "cancel removes handoff")

        issues, kernel, decisions, manifest = validate_runtime(root, strict=True)
        check(not [issue for issue in issues if issue.level == "ERROR"], "final strict validation")
        check(len(list(rt.glob("*.md"))) == 2, "final active Markdown count is two")
        check(set(path.name for path in rt.iterdir()) == {KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE}, "final runtime is clean")

    return {"result": "PASS", "version": VERSION, "assertions": assertions, "passed": passed, "details": details}


def command_validate(args: argparse.Namespace) -> Dict[str, Any]:
    root = Path(args.root)
    rt = runtime_dir(root)
    recovery = None
    if args.repair:
        assert_safe_runtime_path(rt)
        if rt.exists():
            with runtime_lock(rt):
                recovery = recover_transaction(rt)
    issues, kernel, decisions, manifest = validate_runtime(root, strict=args.strict)
    return {
        "route": "validate",
        "result": "PASS" if not [i for i in issues if i.level == "ERROR"] else "FAIL",
        "revision": kernel["meta"]["revision"] if kernel else None,
        "recovery": recovery,
        "issues": [i.as_dict() for i in issues],
        "markdown_files": sorted(path.name for path in rt.glob("*.md")) if rt.exists() else [],
    }


def command_status(args: argparse.Namespace) -> Dict[str, Any]:
    kernel, decisions, manifest, issues = ensure_valid_or_raise(Path(args.root))
    return {
        "route": "status",
        "result": "READ_ONLY",
        "revision": kernel["meta"]["revision"],
        "project": kernel["target"]["项目"],
        "lifecycle": kernel["meta"]["lifecycle"],
        "executor": kernel["responsibility"]["当前执行主体"],
        "transfer_state": kernel["responsibility"]["移交状态"],
        "active_markdown_files": [name for name in [KERNEL_FILE, DECISIONS_FILE, HANDOFF_FILE] if (runtime_dir(Path(args.root)) / name).exists()],
        "warnings": [i.as_dict() for i in issues if i.level == "WARNING"],
        "validation": "PASS",
    }


def command_resume(args: argparse.Namespace) -> None:
    root = Path(args.root)
    kernel, decisions, manifest, issues = ensure_valid_or_raise(root)
    summary = resume_summary(kernel, decisions, issues, (runtime_dir(root) / HANDOFF_FILE).exists())
    if args.format == "json":
        sys.stdout.write(render_json(summary))
    else:
        sys.stdout.write(render_resume_markdown(summary))


def command_guide(args: argparse.Namespace) -> Dict[str, Any]:
    specs = {
        "checkpoint": {"trigger": "material state changed", "writes": [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE], "forbidden": ["responsibility changes", "chat logging"]},
        "handoff": {"trigger": "context boundary without responsibility transfer", "writes": [HANDOFF_FILE, RUNTIME_MANIFEST_FILE], "forbidden": ["changing executor", "creating history files"]},
        "handover": {"trigger": "responsibility changes", "modes": ["prepare", "accept", "cancel"], "writes": [KERNEL_FILE, HANDOFF_FILE, RUNTIME_MANIFEST_FILE]},
        "trim": {"trigger": "context budget or stale/redundant content", "writes": [KERNEL_FILE, DECISIONS_FILE, RUNTIME_MANIFEST_FILE], "forbidden": ["dropping active IDs", "changing governance or responsibility"]},
        "resume": {"trigger": "continue in a new context", "writes": [], "reads": [KERNEL_FILE, "referenced decisions", "fresh HANDOFF if present"]},
    }
    return {"route": args.route, "spec": specs[args.route], "version": VERSION}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="context_kernel.py", description=f"{DISPLAY_NAME_ZH} / Context Kernel {VERSION}")
    parser.add_argument("--version", action="version", version=VERSION)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("install", help="Install this skill directory")
    p.add_argument("--scope", choices=["user", "codex", "claude", "repo"])
    p.add_argument("--target", type=Path)
    p.add_argument("--repo", type=Path)
    p.add_argument("--replace", action="store_true")

    p = sub.add_parser("init", help="Initialize two persistent Markdown files and manifest")
    p.add_argument("--root", required=True)
    p.add_argument("--project", required=True)
    p.add_argument("--north-star", required=True)
    p.add_argument("--owner", required=True)
    p.add_argument("--executor", default="")

    p = sub.add_parser("validate", help="Validate runtime invariants")
    p.add_argument("--root", required=True)
    p.add_argument("--strict", action="store_true")
    p.add_argument("--repair", action="store_true")

    p = sub.add_parser("status", help="Read-only status")
    p.add_argument("--root", required=True)

    p = sub.add_parser("checkpoint", help="Commit material state changes")
    p.add_argument("--root", required=True)
    p.add_argument("--kernel-draft", type=Path)
    p.add_argument("--decisions-draft", type=Path)
    p.add_argument("--expected-revision", type=int, required=True)
    p.add_argument("--reason", required=True)
    p.add_argument("--allow-governance-change", action="store_true")
    p.add_argument("--decision-id")
    p.add_argument("--adopt-current", action="store_true")

    p = sub.add_parser("handoff", help="Generate or replace derived handoff snapshot")
    p.add_argument("--root", required=True)
    p.add_argument("--to", default="下一会话")
    p.add_argument("--reason", default="上下文边界")

    p = sub.add_parser("handover", help="Transfer execution responsibility")
    hand_sub = p.add_subparsers(dest="handover_command", required=True)
    hp = hand_sub.add_parser("prepare")
    hp.add_argument("--root", required=True)
    hp.add_argument("--to", required=True)
    hp.add_argument("--reason", required=True)
    hp.add_argument("--expected-revision", type=int, required=True)
    hp = hand_sub.add_parser("accept")
    hp.add_argument("--root", required=True)
    hp.add_argument("--as", dest="as_executor", required=True)
    hp.add_argument("--transfer-id", required=True)
    hp.add_argument("--expected-revision", type=int, required=True)
    hp = hand_sub.add_parser("cancel")
    hp.add_argument("--root", required=True)
    hp.add_argument("--transfer-id", required=True)
    hp.add_argument("--expected-revision", type=int, required=True)
    hp.add_argument("--reason", default="取消责任移交")

    p = sub.add_parser("trim", help="Compact context without losing active semantics")
    p.add_argument("--root", required=True)
    p.add_argument("--expected-revision", type=int, required=True)
    mode = p.add_mutually_exclusive_group(required=True)
    mode.add_argument("--auto", action="store_true")
    mode.add_argument("--kernel-draft", type=Path)
    p.add_argument("--decisions-draft", type=Path)

    p = sub.add_parser("resume", help="Validate and print minimal Context Check")
    p.add_argument("--root", required=True)
    p.add_argument("--format", choices=["markdown", "json"], default="markdown")

    p = sub.add_parser("guide", help="Print one route contract without loading extra docs")
    p.add_argument("--route", choices=["checkpoint", "handoff", "handover", "trim", "resume"], required=True)

    sub.add_parser("verify-package", help="Verify installed skill package integrity")
    sub.add_parser("self-test", help="Run deterministic standard-library end-to-end tests")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "install":
            print_result(install_skill(args.scope, args.target, args.repo, args.replace))
        elif args.command == "init":
            print_result(do_init(Path(args.root), args.project, args.north_star, args.owner, args.executor))
        elif args.command == "validate":
            result = command_validate(args)
            print_result(result)
            return 0 if result["result"] == "PASS" else 2
        elif args.command == "status":
            print_result(command_status(args))
        elif args.command == "checkpoint":
            if args.adopt_current:
                result = adopt_current(Path(args.root), args.expected_revision, args.reason, args.allow_governance_change, args.decision_id)
            else:
                if args.kernel_draft is None:
                    raise KernelError("checkpoint requires --kernel-draft unless --adopt-current is used")
                result = apply_checkpoint(Path(args.root), args.kernel_draft, args.decisions_draft, args.expected_revision, args.reason, args.allow_governance_change, args.decision_id)
            print_result(result)
        elif args.command == "handoff":
            print_result(apply_handoff(Path(args.root), args.to, args.reason))
        elif args.command == "handover":
            if args.handover_command == "prepare":
                result = handover_prepare(Path(args.root), args.to, args.reason, args.expected_revision)
            elif args.handover_command == "accept":
                result = handover_accept(Path(args.root), args.as_executor, args.transfer_id, args.expected_revision)
            else:
                result = handover_cancel(Path(args.root), args.transfer_id, args.expected_revision, args.reason)
            print_result(result)
        elif args.command == "trim":
            print_result(apply_trim(Path(args.root), args.expected_revision, auto=args.auto, kernel_draft=args.kernel_draft, decisions_draft=args.decisions_draft))
        elif args.command == "resume":
            command_resume(args)
        elif args.command == "guide":
            print_result(command_guide(args))
        elif args.command == "verify-package":
            print_result(verify_package())
        elif args.command == "self-test":
            print_result(run_self_test())
        else:
            parser.error("Unknown command")
        return 0
    except (KernelError, OSError, ValueError, AssertionError) as exc:
        error = {"result": "FAIL", "error": str(exc), "command": getattr(args, "command", None)}
        sys.stderr.write(render_json(error))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
