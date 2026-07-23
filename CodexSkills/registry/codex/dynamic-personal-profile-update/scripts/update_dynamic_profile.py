#!/usr/bin/env python3
"""Deterministically build one dynamic profile Markdown from redacted derived data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Any


SKILL_VERSION = "0.0.0.1"
SCHEMA_VERSION = "dynamic_personal_profile.v1"
DEFAULT_OUTPUT = Path("OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_OUTPUT_BYTES = 80 * 1024
MAX_ENTRIES = 18
MAX_RECORDS = 10_000

ALLOWLIST = (
    "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md",
    "OpenAIDatabase/data/derived/behavior_intelligence/low_value_loops.json",
    "OpenAIDatabase/data/derived/codex/codex_agent_recommendations.json",
)
FORBIDDEN_PARTS = {
    "raw",
    "public_raw",
    "private",
    "private_imports",
    "raw_archives",
    ".git",
    ".local_keys",
}
VOLATILE_KEYS = {
    "generated_at",
    "updated_at",
    "created_at",
    "timestamp",
    "run_at",
    "last_run",
    "source_snapshot_sha256",
    "semantic_snapshot_sha256",
}
ALLOWED_ENTRY_TYPES = {"profile_signal", "behavior_signal", "asset_candidate"}
ALLOWED_STATUSES = {"current", "emerging", "hypothesis"}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}
ALLOWED_ASSET_TYPES = {"prompt_template", "workflow", "skill", "schedule", "observation"}
ALLOWED_WINDOWS = {
    "recent_7d",
    "recent_30d",
    "long_baseline",
    "source timestamp unavailable",
}
WINDOW_ORDER = {
    "recent_7d": 0,
    "recent_30d": 1,
    "long_baseline": 2,
    "source timestamp unavailable": 3,
}
EXPECTED_TOP_LEVEL_KEYS = {
    "schema_version",
    "artifact",
    "artifact_status",
    "skill_version",
    "generated_at",
    "input_mode",
    "canonical_stable_profile_write",
    "source_snapshot_sha256",
    "semantic_snapshot_sha256",
    "source_files",
    "time_windows",
    "entry_count",
    "entries",
}
EXPECTED_SOURCE_KEYS = {"path", "sha256", "bytes"}
EXPECTED_ENTRY_KEYS = {
    "id",
    "type",
    "status",
    "statement",
    "evidence",
    "counterevidence",
    "confidence",
    "observed_window",
    "valid_until",
    "agent_action",
    "asset_candidate",
    "occurrences",
    "source_count",
}
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})(?:[T ][0-9:.+Z-]*)?\b")
HASH_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
ID_RE = re.compile(r"^dp-[0-9a-f]{12}$")
FORBIDDEN_CONTENT_PATTERNS = (
    re.compile(r"(?:^|[\"'`/])(?:OpenAIDatabase/)?data/(?:raw|public_raw|private|raw_archives)(?:/|[\"'`])", re.IGNORECASE),
    re.compile(r"(?:/Users/|/home/)"),
    re.compile(r"[A-Za-z]:\\"),
    re.compile(r"\bsk-(?:ant-)?[A-Za-z0-9_-]{20,}\b"),
    re.compile(r"\b(?:ghp|gho|ghu|ghs)_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"),
)


def clean_text(value: Any, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def normalize(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def parse_utc(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iso_now(value: str | None) -> str:
    parsed = parse_utc(value) if value else datetime.now(timezone.utc)
    return parsed.replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_forbidden(path: PurePosixPath | Path) -> bool:
    return any(part.casefold() in FORBIDDEN_PARTS for part in path.parts)


def is_allowlisted_relative(relative: str) -> bool:
    candidate = PurePosixPath(relative)
    if candidate.is_absolute() or ".." in candidate.parts or is_forbidden(candidate):
        return False
    return any(candidate.match(pattern) for pattern in ALLOWLIST)


def ensure_no_symlink_components(path: Path, database_dir: Path) -> None:
    try:
        relative = path.relative_to(database_dir)
    except ValueError as exc:
        raise ValueError("path escapes database directory") from exc
    current = database_dir
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            raise ValueError(f"symlink is forbidden: {relative.as_posix()}")


def resolve_output_path(database_dir: Path, requested: Path) -> Path:
    expected = Path(os.path.abspath(database_dir / DEFAULT_OUTPUT))
    candidate = requested if requested.is_absolute() else database_dir / requested
    candidate = Path(os.path.abspath(candidate)).resolve(strict=False)
    if candidate != expected:
        raise ValueError(f"output must be {DEFAULT_OUTPUT.as_posix()}")
    ensure_no_symlink_components(candidate, database_dir)
    return candidate


def source_paths(database_dir: Path, output: Path) -> list[Path]:
    matched: set[Path] = set()
    for relative in ALLOWLIST:
        candidate = database_dir / relative
        ensure_no_symlink_components(candidate, database_dir)
        if not candidate.is_file():
            raise ValueError(f"missing required derived source: {relative}")
        matched.add(candidate)

    result: list[Path] = []
    resolved_seen: set[Path] = set()
    total = 0
    for path in sorted(matched):
        try:
            relative_path = path.relative_to(database_dir)
        except ValueError as exc:
            raise ValueError("allowlisted source escapes database directory") from exc
        relative = relative_path.as_posix()
        if not is_allowlisted_relative(relative):
            raise ValueError(f"source is outside the explicit allowlist: {relative}")
        ensure_no_symlink_components(path, database_dir)
        if not path.is_file():
            raise ValueError(f"allowlisted source is not a regular file: {relative}")
        try:
            resolved = path.resolve(strict=True)
            resolved.relative_to(database_dir)
        except (OSError, ValueError) as exc:
            raise ValueError(f"source escapes database directory: {relative}") from exc
        if resolved in resolved_seen:
            raise ValueError(f"duplicate resolved source: {relative}")
        resolved_seen.add(resolved)
        if path == output:
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"source exceeds {MAX_FILE_BYTES} bytes: {relative}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError(f"allowlisted derived sources exceed {MAX_TOTAL_BYTES} bytes")
        result.append(path)
    return result


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_json_strict(text: str, label: str) -> Any:
    try:
        return json.loads(text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"invalid JSON source: {label}") from exc


def canonical_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: canonical_json(item)
            for key, item in sorted(value.items())
            if key not in VOLATILE_KEYS
        }
    if isinstance(value, list):
        return [canonical_json(item) for item in value]
    return value


def canonical_bytes(path: Path, database_dir: Path) -> bytes:
    relative = path.relative_to(database_dir).as_posix()
    raw = path.read_bytes()
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError(f"source is not valid UTF-8: {relative}") from exc
    if path.suffix.lower() == ".json":
        value = load_json_strict(text, relative)
        return json.dumps(
            canonical_json(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
    kept = [
        line
        for line in text.splitlines()
        if not re.match(
            r"^\s*-?\s*(generated_at|updated_at|created_at|timestamp|run_at|last_run):",
            line,
        )
    ]
    return "\n".join(kept).encode("utf-8")


def source_records(paths: list[Path], database_dir: Path) -> list[dict[str, Any]]:
    records = []
    for path in paths:
        data = canonical_bytes(path, database_dir)
        records.append(
            {
                "path": path.relative_to(database_dir).as_posix(),
                "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
                "bytes": len(data),
            }
        )
    return records


def source_snapshot_digest(records: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        records,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def date_window(text: str, now: datetime) -> str:
    dates = []
    for match in DATE_RE.finditer(text):
        try:
            dates.append(datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc))
        except ValueError:
            continue
    if not dates:
        return "source timestamp unavailable"
    latest = max(dates)
    age = now - latest
    if age < timedelta(0):
        return "source timestamp unavailable"
    if age <= timedelta(days=7):
        return "recent_7d"
    if age <= timedelta(days=30):
        return "recent_30d"
    return "long_baseline"


def append_record(records: list[dict[str, Any]], record: dict[str, Any]) -> None:
    if len(records) >= MAX_RECORDS:
        raise ValueError(f"derived records exceed {MAX_RECORDS}")
    records.append(record)


def collect_core_profile(
    text: str,
    source: str,
    records: list[dict[str, Any]],
) -> None:
    heading = "## High-weight Core Personalization"
    in_section = False
    pending: dict[str, Any] | None = None

    def flush() -> None:
        nonlocal pending
        if pending is not None:
            append_record(records, pending)
            pending = None

    for line in text.splitlines():
        if line == heading:
            in_section = True
            continue
        if in_section and line.startswith("## "):
            break
        if not in_section:
            continue
        if line.startswith("- "):
            flush()
            statement = clean_text(line[2:])
            if statement:
                pending = {
                    "text": statement,
                    "source": source,
                    "role": "profile_signal",
                    "window": "long_baseline",
                    "support_count": 1,
                    "confidence_hint": "high",
                    "counterevidence": (
                        "Stable curated baseline; this source does not provide a "
                        "recent observation timestamp."
                    ),
                    "asset_type": "observation",
                }
        elif pending is not None and "confidence:" in line:
            match = re.search(r"\bconfidence:\s*(high|medium|low)\b", line)
            if match:
                pending["confidence_hint"] = match.group(1)
    flush()
    if not in_section:
        raise ValueError(f"missing core personalization section: {source}")


def collect_codex_recommendations(
    value: Any,
    source: str,
    records: list[dict[str, Any]],
    now: datetime,
) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {source}")
    if value.get("schema_version") != "codex_agent_recommendations.v1":
        raise ValueError(f"unexpected schema_version: {source}")
    generated_at = value.get("generated_at")
    if not isinstance(generated_at, str):
        raise ValueError(f"missing generated_at: {source}")
    window = date_window(generated_at, now)
    for section_name in ("memory", "meta_data"):
        section = value.get(section_name)
        if not isinstance(section, dict) or not isinstance(section.get("current"), list):
            raise ValueError(f"missing {section_name}.current list: {source}")
        for index, item in enumerate(section["current"]):
            if not isinstance(item, dict):
                raise ValueError(f"invalid {section_name}.current[{index}]: {source}")
            statement = clean_text(item.get("statement"))
            confidence = item.get("confidence")
            support_count = item.get("evidence_count")
            if not statement:
                raise ValueError(f"missing statement in {section_name}.current[{index}]")
            if confidence not in ALLOWED_CONFIDENCE:
                raise ValueError(f"invalid confidence in {section_name}.current[{index}]")
            if (
                not isinstance(support_count, int)
                or isinstance(support_count, bool)
                or support_count < 1
            ):
                raise ValueError(f"invalid evidence_count in {section_name}.current[{index}]")
            append_record(
                records,
                {
                    "text": statement,
                    "source": source,
                    "role": "profile_signal",
                    "window": window,
                    "support_count": support_count,
                    "confidence_hint": confidence,
                    "counterevidence": (
                        "This redacted derived summary was not independently rechecked "
                        "against its underlying sessions in v0.0.0.1."
                    ),
                    "asset_type": "observation",
                },
            )


LOOP_ACTIONS = {
    "repeated_rework": (
        "派生行为数据在 {clusters} 个主题簇中检测到反复返工候选（累计 {events} 条事件）；"
        "下一次相关任务应先复用现有资产并设置一次复跑验收。"
    ),
    "discussion_without_landing": (
        "派生行为数据在 {clusters} 个主题簇中检测到多次讨论但缺少落地产物（累计 {events} 条事件）；"
        "下一次相关任务先收口为一个交付件、一个验收命令和一个停止条件。"
    ),
    "over_optimization": (
        "派生行为数据在 {clusters} 个主题簇中检测到高频细节迭代候选（累计 {events} 条事件）；"
        "下一次相关任务应先冻结质量上限，达到验收后停止扩张。"
    ),
    "scope_creep": (
        "派生行为数据在 {clusters} 个主题簇中检测到 scope creep 候选（累计 {events} 条事件）；"
        "下一次相关任务应先冻结 run contract、非目标和写入边界。"
    ),
}


def collect_low_value_loop_summary(
    value: Any,
    source: str,
    records: list[dict[str, Any]],
    now: datetime,
) -> None:
    if not isinstance(value, dict):
        raise ValueError(f"expected JSON object: {source}")
    if value.get("schema_version") != "memory_atlas_low_value_loops.v1":
        raise ValueError(f"unexpected schema_version: {source}")
    generated_at = value.get("generated_at")
    clusters = value.get("loop_clusters")
    if not isinstance(generated_at, str) or not isinstance(clusters, list):
        raise ValueError(f"missing generated_at or loop_clusters: {source}")
    totals = {
        loop_type: {"clusters": 0, "events": 0}
        for loop_type in LOOP_ACTIONS
    }
    for index, cluster in enumerate(clusters):
        if not isinstance(cluster, dict):
            raise ValueError(f"invalid loop_clusters[{index}]: {source}")
        loop_type = cluster.get("loop_type")
        if loop_type not in totals:
            continue
        event_count = cluster.get("event_count")
        if (
            not isinstance(event_count, int)
            or isinstance(event_count, bool)
            or event_count < 1
        ):
            raise ValueError(f"invalid event_count in loop_clusters[{index}]")
        totals[loop_type]["clusters"] += 1
        totals[loop_type]["events"] += event_count

    for loop_type, values in totals.items():
        if values["clusters"] == 0:
            continue
        append_record(
            records,
            {
                "text": LOOP_ACTIONS[loop_type].format(**values),
                "source": source,
                "role": "asset_candidate",
                "window": date_window(generated_at, now),
                "support_count": values["events"],
                "confidence_hint": "medium",
                "counterevidence": (
                    "The aggregation may reflect a temporary period of concentrated "
                    "development rather than a durable work pattern."
                ),
                "asset_type": "workflow",
            },
        )


def collect_records(
    paths: list[Path],
    database_dir: Path,
    now: datetime,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(database_dir).as_posix()
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError(f"source is not valid UTF-8: {relative}") from exc
        if relative == ALLOWLIST[0]:
            collect_core_profile(text, relative, records)
        elif relative == ALLOWLIST[1]:
            collect_low_value_loop_summary(
                load_json_strict(text, relative), relative, records, now
            )
        elif relative == ALLOWLIST[2]:
            collect_codex_recommendations(
                load_json_strict(text, relative), relative, records, now
            )
        else:
            raise ValueError(f"source collector is undefined: {relative}")
    return records


def aggregate(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "texts": [],
            "sources": set(),
            "roles": set(),
            "windows": set(),
            "support_count": 0,
            "confidence_hints": set(),
            "counterevidence": set(),
            "asset_types": set(),
        }
    )
    for record in records:
        key = normalize(record["text"])
        if len(key) < 12:
            continue
        item = grouped[key]
        item["texts"].append(record["text"])
        item["sources"].add(record["source"])
        item["roles"].add(record["role"])
        item["windows"].add(record["window"])
        item["support_count"] += record["support_count"]
        item["confidence_hints"].add(record["confidence_hint"])
        item["counterevidence"].add(record["counterevidence"])
        item["asset_types"].add(record["asset_type"])

    entries = []
    for key, item in grouped.items():
        occurrences = item["support_count"]
        source_count = len(item["sources"])
        if "high" in item["confidence_hints"]:
            confidence = "high"
        elif "medium" in item["confidence_hints"]:
            confidence = "medium"
        else:
            confidence = "low"

        if "asset_candidate" in item["roles"]:
            entry_type = "asset_candidate"
        elif "profile_signal" in item["roles"]:
            entry_type = "profile_signal"
        else:
            entry_type = "behavior_signal"
        if entry_type == "asset_candidate" and confidence != "low":
            status = "emerging"
        elif confidence == "high":
            status = "current"
        else:
            status = "hypothesis"

        statement = max(item["texts"], key=lambda value: (len(value), value))
        asset_type = (
            sorted(item["asset_types"])[0]
            if entry_type == "asset_candidate"
            else "observation"
        )
        entry_id = "dp-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        agent_action = clean_text(
            f"在下一次与“{statement}”直接相关的任务中试用一次；若没有可观察收益或出现反证，立即失效。",
            limit=420,
        )
        entries.append(
            {
                "id": entry_id,
                "type": entry_type,
                "status": status,
                "statement": statement,
                "evidence": sorted(item["sources"])[:6],
                "counterevidence": sorted(item["counterevidence"]),
                "confidence": confidence,
                "observed_window": ", ".join(
                    sorted(item["windows"], key=lambda value: WINDOW_ORDER[value])
                ),
                "valid_until": None,
                "agent_action": agent_action,
                "asset_candidate": asset_type,
                "occurrences": occurrences,
                "source_count": source_count,
            }
        )
    status_rank = {"current": 0, "emerging": 1, "hypothesis": 2}
    confidence_rank = {"high": 0, "medium": 1, "low": 2}
    entries.sort(
        key=lambda item: (
            status_rank[item["status"]],
            confidence_rank[item["confidence"]],
            -item["source_count"],
            -item["occurrences"],
            item["id"],
        )
    )
    return entries[:MAX_ENTRIES]


def semantic_hash(entries: list[dict[str, Any]]) -> str:
    payload = json.dumps(
        entries,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def records_used_by_entries(
    records: list[dict[str, Any]],
    entries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not entries:
        return records
    used = {path for entry in entries for path in entry["evidence"]}
    return [record for record in records if record["path"] in used]


def render_human(entries: list[dict[str, Any]]) -> str:
    lines = ["# Dynamic Personal Profile", "", "## 先看结论", ""]
    if not entries:
        lines.append("当前允许读取的派生数据没有形成可报告的重复信号；本文件保留为空变化视图。")
    else:
        for entry in entries[:8]:
            lines.append(
                f"- **{entry['status']} / {entry['confidence']}**：{entry['statement']}"
            )

    lines += ["", "## 变化条目", ""]
    if not entries:
        lines.append("无。")
    for entry in entries:
        evidence = ", ".join(f"`{path}`" for path in entry["evidence"])
        lines += [
            f"### {entry['id']}｜{entry['status']}",
            "",
            f"- 类型：`{entry['type']}`；资产候选：`{entry['asset_candidate']}`",
            f"- 观察：{entry['statement']}",
            f"- 证据：{evidence}",
            f"- 反证：{entry['counterevidence'][0]}",
            f"- 置信度：`{entry['confidence']}`；时间窗口：`{entry['observed_window']}`",
            f"- 临时 Agent 行为：{entry['agent_action']}",
            "",
        ]

    lines += ["## 可立即试用的 Agent 行为", ""]
    actionable = [
        entry for entry in entries if entry["status"] in {"current", "emerging"}
    ]
    if actionable:
        for entry in actionable:
            lines.append(f"- `{entry['id']}`：{entry['agent_action']}")
    else:
        lines.append("当前没有通过证据门的临时行为；`hypothesis` 不得用于改变 Agent 行为。")

    lines += ["", "## Recurring Asset 候选", ""]
    candidates = [
        entry
        for entry in entries
        if entry["type"] == "asset_candidate"
        and entry["status"] in {"current", "emerging"}
    ]
    if candidates:
        for entry in candidates:
            lines.append(
                f"- `{entry['id']}` / `{entry['asset_candidate']}`：一次真实任务验证前保持 `pending`。"
            )
    else:
        lines.append("当前没有达到一次真实任务验证门槛的资产候选。")

    lines += [
        "",
        "## 边界与不确定性",
        "",
        "- 本文件来自脱敏派生数据，不是原始记录，也不是稳定核心画像。",
        "- 没有源时间戳时不推断精确发生日期。",
        "- 当前脚本不调用 LLM，不做语义事实确认，不自动写回长期记忆。",
        "- `CORE_PROFILE.md`、Custom Instructions、AGENTS.md 和 Memory Atlas canonical records 不会被本次运行修改。",
        "",
    ]
    return "\n".join(lines)


def render_profile(
    entries: list[dict[str, Any]],
    generated_at: str,
    source_hash: str,
    sources: list[dict[str, Any]],
    semantic: str,
) -> str:
    machine = {
        "schema_version": SCHEMA_VERSION,
        "artifact": "dynamic_personal_profile",
        "artifact_status": "generated_derived_view",
        "skill_version": SKILL_VERSION,
        "generated_at": generated_at,
        "input_mode": "derived_only",
        "canonical_stable_profile_write": False,
        "source_snapshot_sha256": source_hash,
        "semantic_snapshot_sha256": semantic,
        "source_files": sources,
        "time_windows": ["recent_7d", "recent_30d", "long_baseline"],
        "entry_count": len(entries),
        "entries": entries,
    }
    machine_text = json.dumps(machine, ensure_ascii=False, indent=2)
    output = f"---\n{machine_text}\n---\n\n{render_human(entries)}"
    if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError(f"output exceeds {MAX_OUTPUT_BYTES} bytes")
    return output


def split_profile(content: str) -> tuple[dict[str, Any], str]:
    if not content.startswith("---\n"):
        raise ValueError("missing opening front matter boundary")
    machine_text, separator, human = content[4:].partition("\n---\n\n")
    if not separator:
        raise ValueError("missing closing front matter boundary")
    try:
        machine = json.loads(machine_text, object_pairs_hook=reject_duplicate_keys)
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError("machine plane is not JSON-compatible YAML") from exc
    if not isinstance(machine, dict):
        raise ValueError("machine plane must be an object")
    return machine, human


def validate_profile_content(content: str) -> list[str]:
    errors: list[str] = []
    if len(content.encode("utf-8")) > MAX_OUTPUT_BYTES:
        errors.append("profile exceeds 80 KiB")
    for pattern in FORBIDDEN_CONTENT_PATTERNS:
        if pattern.search(content):
            errors.append(f"forbidden content pattern: {pattern.pattern}")

    try:
        machine, human = split_profile(content)
    except ValueError as exc:
        return errors + [str(exc)]

    missing = sorted(EXPECTED_TOP_LEVEL_KEYS - set(machine))
    unexpected = sorted(set(machine) - EXPECTED_TOP_LEVEL_KEYS)
    if missing:
        errors.append(f"missing machine fields: {', '.join(missing)}")
    if unexpected:
        errors.append(f"unexpected machine fields: {', '.join(unexpected)}")
    if missing:
        return errors

    if machine["schema_version"] != SCHEMA_VERSION:
        errors.append("unexpected schema_version")
    if machine["artifact"] != "dynamic_personal_profile":
        errors.append("unexpected artifact")
    if machine["artifact_status"] != "generated_derived_view":
        errors.append("unexpected artifact_status")
    if machine["skill_version"] != SKILL_VERSION:
        errors.append("unexpected skill_version")
    if machine["input_mode"] != "derived_only":
        errors.append("input_mode must be derived_only")
    if machine["canonical_stable_profile_write"] is not False:
        errors.append("canonical_stable_profile_write must be false")
    try:
        generated_at = machine["generated_at"]
        if not isinstance(generated_at, str) or not generated_at.endswith("Z"):
            raise ValueError
        parse_utc(generated_at)
    except (TypeError, ValueError):
        errors.append("generated_at must be a UTC ISO timestamp")

    sources = machine["source_files"]
    source_path_set: set[str] = set()
    if not isinstance(sources, list) or not sources:
        errors.append("source_files must be a non-empty list")
        sources = []
    total_bytes = 0
    for index, record in enumerate(sources):
        if not isinstance(record, dict):
            errors.append(f"source_files[{index}] must be an object")
            continue
        if set(record) != EXPECTED_SOURCE_KEYS:
            errors.append(f"source_files[{index}] has invalid fields")
            continue
        path = record["path"]
        digest = record["sha256"]
        size = record["bytes"]
        if not isinstance(path, str) or not is_allowlisted_relative(path):
            errors.append(f"source_files[{index}] path is outside the allowlist")
        elif path in source_path_set:
            errors.append(f"duplicate source path: {path}")
        else:
            source_path_set.add(path)
        if not isinstance(digest, str) or not HASH_RE.fullmatch(digest):
            errors.append(f"source_files[{index}] has invalid sha256")
        if not isinstance(size, int) or isinstance(size, bool) or not 0 <= size <= MAX_FILE_BYTES:
            errors.append(f"source_files[{index}] has invalid byte count")
        else:
            total_bytes += size
    if total_bytes > MAX_TOTAL_BYTES:
        errors.append("source_files exceed the total byte limit")
    source_paths_in_order = [
        record.get("path") for record in sources if isinstance(record, dict)
    ]
    if source_paths_in_order != sorted(source_paths_in_order):
        errors.append("source_files must be sorted by path")
    if isinstance(machine["source_snapshot_sha256"], str) and HASH_RE.fullmatch(
        machine["source_snapshot_sha256"]
    ):
        if sources and machine["source_snapshot_sha256"] != source_snapshot_digest(sources):
            errors.append("source_snapshot_sha256 does not match source_files")
    else:
        errors.append("invalid source_snapshot_sha256")

    if machine["time_windows"] != ["recent_7d", "recent_30d", "long_baseline"]:
        errors.append("unexpected time_windows")

    entries = machine["entries"]
    if not isinstance(entries, list):
        errors.append("entries must be a list")
        entries = []
    if len(entries) > MAX_ENTRIES:
        errors.append(f"entries exceed {MAX_ENTRIES}")
    if machine["entry_count"] != len(entries):
        errors.append("entry_count does not match entries")

    seen_ids: set[str] = set()
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            errors.append(f"entries[{index}] must be an object")
            continue
        if set(entry) != EXPECTED_ENTRY_KEYS:
            errors.append(f"entries[{index}] has invalid fields")
            continue
        entry_id = entry["id"]
        statement = entry["statement"]
        if not isinstance(entry_id, str) or not ID_RE.fullmatch(entry_id):
            errors.append(f"entries[{index}] has invalid id")
        elif entry_id in seen_ids:
            errors.append(f"duplicate entry id: {entry_id}")
        else:
            seen_ids.add(entry_id)
        if not isinstance(statement, str) or not statement or len(statement) > 280:
            errors.append(f"entries[{index}] has invalid statement")
        elif isinstance(entry_id, str):
            expected_id = "dp-" + hashlib.sha256(
                normalize(statement).encode("utf-8")
            ).hexdigest()[:12]
            if entry_id != expected_id:
                errors.append(f"entries[{index}] id does not match statement")
        if entry["type"] not in ALLOWED_ENTRY_TYPES:
            errors.append(f"entries[{index}] has invalid type")
        if entry["status"] not in ALLOWED_STATUSES:
            errors.append(f"entries[{index}] has invalid status")
        if entry["confidence"] not in ALLOWED_CONFIDENCE:
            errors.append(f"entries[{index}] has invalid confidence")
        if entry["asset_candidate"] not in ALLOWED_ASSET_TYPES:
            errors.append(f"entries[{index}] has invalid asset_candidate")
        if entry["valid_until"] is not None:
            errors.append(f"entries[{index}] valid_until must be null in v0.0.0.1")

        evidence = entry["evidence"]
        if not isinstance(evidence, list) or not 1 <= len(evidence) <= 6:
            errors.append(f"entries[{index}] has invalid evidence")
            evidence = []
        elif evidence != sorted(set(evidence)):
            errors.append(f"entries[{index}] evidence must be sorted and unique")
        for path in evidence:
            if not isinstance(path, str) or not is_allowlisted_relative(path):
                errors.append(f"entries[{index}] evidence is outside the allowlist")
            elif path not in source_path_set:
                errors.append(f"entries[{index}] evidence is absent from source_files")

        counterevidence = entry["counterevidence"]
        if (
            not isinstance(counterevidence, list)
            or not counterevidence
            or not all(isinstance(value, str) and value for value in counterevidence)
        ):
            errors.append(f"entries[{index}] has invalid counterevidence")
        windows = (
            {value.strip() for value in entry["observed_window"].split(",")}
            if isinstance(entry["observed_window"], str)
            else set()
        )
        if not windows or not windows <= ALLOWED_WINDOWS:
            errors.append(f"entries[{index}] has invalid observed_window")
        if not isinstance(entry["agent_action"], str) or not entry["agent_action"]:
            errors.append(f"entries[{index}] has invalid agent_action")
        if (
            not isinstance(entry["occurrences"], int)
            or isinstance(entry["occurrences"], bool)
            or entry["occurrences"] < 1
        ):
            errors.append(f"entries[{index}] has invalid occurrences")
        if (
            not isinstance(entry["source_count"], int)
            or isinstance(entry["source_count"], bool)
            or entry["source_count"] < len(evidence)
        ):
            errors.append(f"entries[{index}] has invalid source_count")

    semantic = machine["semantic_snapshot_sha256"]
    if not isinstance(semantic, str) or not HASH_RE.fullmatch(semantic):
        errors.append("invalid semantic_snapshot_sha256")
    elif semantic != semantic_hash(entries):
        errors.append("semantic_snapshot_sha256 does not match entries")
    if human != render_human(entries):
        errors.append("human plane is not the deterministic projection of entries")
    return errors


def validate_profile_file(path: Path) -> list[str]:
    if path.is_symlink():
        return ["profile path must not be a symlink"]
    if not path.is_file():
        return [f"missing profile: {path}"]
    try:
        content = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ["profile is not valid UTF-8"]
    return validate_profile_content(content)


def previous_semantic_hash(output: Path) -> str | None:
    if not output.exists():
        return None
    errors = validate_profile_file(output)
    if errors:
        raise ValueError("existing output is invalid: " + "; ".join(errors[:3]))
    machine, _ = split_profile(output.read_text(encoding="utf-8"))
    return str(machine["semantic_snapshot_sha256"])


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            handle.write(content)
            handle.flush()
            if hasattr(os, "fchmod"):
                os.fchmod(handle.fileno(), 0o644)
            os.fsync(handle.fileno())
            temporary_path = Path(handle.name)
        os.replace(temporary_path, path)
        temporary_path = None
    finally:
        if temporary_path and temporary_path.exists():
            temporary_path.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--now", help="UTC ISO time for deterministic tests")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        database_dir = args.database_dir.resolve(strict=True)
        if not database_dir.is_dir():
            raise ValueError("database directory is not a directory")
        output = resolve_output_path(database_dir, args.output)
        generated_at = iso_now(args.now)
        now = parse_utc(generated_at)
        paths = source_paths(database_dir, output)
        if not paths:
            raise ValueError("no allowlisted derived source files found")

        all_source_records = source_records(paths, database_dir)
        entries = aggregate(collect_records(paths, database_dir, now))
        used_source_records = records_used_by_entries(all_source_records, entries)
        source_hash = source_snapshot_digest(used_source_records)
        semantic = semantic_hash(entries)
        if previous_semantic_hash(output) == semantic:
            print(
                json.dumps(
                    {
                        "status": "NO_CHANGE",
                        "semantic_snapshot_sha256": semantic,
                    },
                    ensure_ascii=False,
                )
            )
            return 0

        content = render_profile(
            entries,
            generated_at,
            source_hash,
            used_source_records,
            semantic,
        )
        validation_errors = validate_profile_content(content)
        if validation_errors:
            raise ValueError(
                "generated profile failed validation: "
                + "; ".join(validation_errors[:3])
            )
        if not args.check_only:
            atomic_write(output, content)
        print(
            json.dumps(
                {
                    "status": "CHANGED" if not args.check_only else "WOULD_CHANGE",
                    "output": output.relative_to(database_dir).as_posix(),
                    "entry_count": len(entries),
                    "input_source_count": len(paths),
                    "evidence_source_count": len(used_source_records),
                    "semantic_snapshot_sha256": semantic,
                },
                ensure_ascii=False,
            )
        )
        return 0
    except Exception as exc:
        print(
            json.dumps({"status": "STOP", "error": str(exc)}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
