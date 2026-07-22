#!/usr/bin/env python3
"""Deterministically build one dynamic profile Markdown from redacted derived data."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any


SKILL_VERSION = "0.0.0.1"
SCHEMA_VERSION = "dynamic_personal_profile.v1"
DEFAULT_OUTPUT = Path("OpenAIDatabase/data/derived/profile/DYNAMIC_PROFILE.md")
MAX_FILE_BYTES = 5 * 1024 * 1024
MAX_TOTAL_BYTES = 50 * 1024 * 1024
MAX_OUTPUT_BYTES = 80 * 1024
MAX_ENTRIES = 24

ALLOWLIST = (
    "OpenAIDatabase/data/derived/profile/CORE_PROFILE.md",
    "OpenAIDatabase/data/derived/personalization/*.md",
    "OpenAIDatabase/data/derived/behavior_intelligence/*.json",
    "OpenAIDatabase/data/derived/codex/*.json",
    "OpenAIDatabase/data/derived/timeline/*.md",
    "OpenAIDatabase/data/derived/weekly/*.md",
    "OpenAIDatabase/data/derived/monthly/*.md",
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
TEXT_KEYS = (
    "statement",
    "claim_zh",
    "summary_zh",
    "expected_change_zh",
    "rationale_zh",
    "description",
    "title",
    "label_zh",
    "decision_area_zh",
    "minimal_next_step_zh",
    "closure_rule_zh",
    "reason",
)
DATE_RE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})(?:[T ][0-9:.+Z-]*)?\b")


def clean_text(value: Any, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    if len(text) > limit:
        return text[: limit - 1].rstrip() + "…"
    return text


def normalize(text: str) -> str:
    return re.sub(r"[^\w\u4e00-\u9fff]+", "", text.lower())


def quote(value: Any) -> str:
    return json.dumps(str(value), ensure_ascii=False)


def iso_now(value: str | None) -> str:
    if value:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        return parsed.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def is_forbidden(path: Path) -> bool:
    return any(part in FORBIDDEN_PARTS for part in path.parts)


def source_paths(database_dir: Path, output: Path) -> list[Path]:
    paths: set[Path] = set()
    for pattern in ALLOWLIST:
        paths.update(database_dir.glob(pattern))
    output_resolved = output.resolve()
    result: list[Path] = []
    total = 0
    for path in sorted(paths):
        if not path.is_file() or is_forbidden(path.relative_to(database_dir)):
            continue
        if path.resolve() == output_resolved:
            continue
        size = path.stat().st_size
        if size > MAX_FILE_BYTES:
            raise ValueError(f"source exceeds {MAX_FILE_BYTES} bytes: {path}")
        total += size
        if total > MAX_TOTAL_BYTES:
            raise ValueError(f"allowlisted derived sources exceed {MAX_TOTAL_BYTES} bytes")
        result.append(path)
    return result


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


def canonical_bytes(path: Path) -> bytes:
    raw = path.read_bytes()
    if path.suffix.lower() == ".json":
        try:
            return json.dumps(canonical_json(json.loads(raw)), ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        except json.JSONDecodeError:
            pass
    text = raw.decode("utf-8", errors="replace")
    kept = [line for line in text.splitlines() if not re.match(r"^\s*-?\s*(generated_at|updated_at|timestamp|last_run):", line)]
    return "\n".join(kept).encode("utf-8")


def source_snapshot(paths: list[Path], database_dir: Path) -> tuple[str, list[dict[str, Any]]]:
    records = []
    for path in paths:
        data = canonical_bytes(path)
        relative = path.relative_to(database_dir).as_posix()
        records.append({
            "path": relative,
            "sha256": "sha256:" + hashlib.sha256(data).hexdigest(),
            "bytes": len(data),
        })
    payload = json.dumps(records, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest(), records


def date_window(text: str, now: datetime) -> str:
    dates = [datetime.fromisoformat(match.group(1)).replace(tzinfo=timezone.utc) for match in DATE_RE.finditer(text)]
    if not dates:
        return "source timestamp unavailable"
    latest = max(dates)
    age = now - latest
    if age <= timedelta(days=7):
        return "recent_7d"
    if age <= timedelta(days=30):
        return "recent_30d"
    return "long_baseline"


def role_for(path: str, key: str) -> str:
    lowered = f"{path} {key}".lower()
    if any(token in lowered for token in ("iteration", "recommend", "workflow", "skill", "prompt", "asset")):
        return "asset_candidate"
    if any(token in lowered for token in ("profile", "preference", "taste")):
        return "profile_signal"
    return "behavior_signal"


def collect_json(value: Any, path: str, records: list[dict[str, Any]], source: str, now: datetime) -> None:
    if isinstance(value, dict):
        picked = None
        picked_key = ""
        for key in TEXT_KEYS:
            if isinstance(value.get(key), str) and clean_text(value[key]):
                picked = value[key]
                picked_key = key
                break
        if picked:
            records.append({
                "text": clean_text(picked),
                "source": source,
                "field": picked_key,
                "role": role_for(source, picked_key),
                "window": date_window(json.dumps(value, ensure_ascii=False), now),
            })
        for key, child in value.items():
            if key in VOLATILE_KEYS:
                continue
            collect_json(child, f"{path}.{key}", records, source, now)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            collect_json(child, f"{path}[{index}]", records, source, now)


def collect_markdown(text: str, source: str, records: list[dict[str, Any]], now: datetime) -> None:
    in_code = False
    for line in text.splitlines():
        if line.strip().startswith("```"):
            in_code = not in_code
            continue
        if in_code:
            continue
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            candidate = clean_text(stripped[2:])
            if candidate and not candidate.startswith("http"):
                records.append({
                    "text": candidate,
                    "source": source,
                    "field": "bullet",
                    "role": role_for(source, "bullet"),
                    "window": date_window(candidate, now),
                })


def collect_records(paths: list[Path], database_dir: Path, now: datetime) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in paths:
        relative = path.relative_to(database_dir).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        if path.suffix.lower() == ".json":
            try:
                collect_json(json.loads(text), "$", records, relative, now)
            except json.JSONDecodeError:
                continue
        else:
            collect_markdown(text, relative, records, now)
    return records


def classify_asset(text: str) -> str:
    lowered = text.lower()
    if any(token in lowered for token in ("prompt", "提示", "template", "模板")):
        return "prompt_template"
    if any(token in lowered for token in ("workflow", "流程", "步骤", "先", "再")):
        return "workflow"
    if any(token in lowered for token in ("tool", "工具", "异常", "验证", "验收", "exception")):
        return "skill"
    return "observation"


def aggregate(records: list[dict[str, Any]], now: datetime) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = defaultdict(lambda: {"texts": [], "sources": set(), "roles": set(), "windows": set()})
    for record in records:
        key = normalize(record["text"])
        if len(key) < 12:
            continue
        item = grouped[key]
        item["texts"].append(record["text"])
        item["sources"].add(record["source"])
        item["roles"].add(record["role"])
        item["windows"].add(record["window"])

    entries = []
    for key, item in grouped.items():
        occurrences = len(item["texts"])
        source_count = len(item["sources"])
        confidence = "high" if source_count >= 2 and occurrences >= 2 else "medium" if occurrences >= 2 or source_count >= 2 else "low"
        role = "asset_candidate" if "asset_candidate" in item["roles"] else "profile_signal"
        status = "emerging" if role == "asset_candidate" and confidence != "low" else "current" if confidence == "high" else "hypothesis"
        statement = max(item["texts"], key=len)
        asset_type = classify_asset(statement) if role == "asset_candidate" else "observation"
        entry_id = "dp-" + hashlib.sha256(key.encode("utf-8")).hexdigest()[:12]
        entries.append({
            "id": entry_id,
            "type": "asset_candidate" if role == "asset_candidate" else "profile_signal",
            "status": status,
            "statement": statement,
            "evidence": sorted(item["sources"])[:6],
            "counterevidence": ["No independent counterevidence found in the allowlisted derived sources."],
            "confidence": confidence,
            "observed_window": ", ".join(sorted(item["windows"])),
            "valid_until": None,
            "agent_action": "Treat as a temporary task-scoped instruction; validate once before promotion.",
            "asset_candidate": asset_type,
            "occurrences": occurrences,
            "source_count": source_count,
        })
    entries.sort(key=lambda item: (-item["source_count"], -item["occurrences"], item["id"]))
    return entries[:MAX_ENTRIES]


def semantic_hash(source_snapshot_sha256: str, entries: list[dict[str, Any]]) -> str:
    payload = {"source_snapshot_sha256": source_snapshot_sha256, "entries": entries}
    return "sha256:" + hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def previous_semantic_hash(output: Path) -> str | None:
    if not output.exists():
        return None
    match = re.search(r"^semantic_snapshot_sha256:\s*['\"]?([^'\"\n]+)", output.read_text(encoding="utf-8", errors="ignore"), re.MULTILINE)
    return match.group(1).strip() if match else None


def yaml_scalar(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    return quote(value)


def render(entries: list[dict[str, Any]], generated_at: str, source_hash: str, source_records: list[dict[str, Any]], semantic: str) -> str:
    lines = [
        "---",
        f"schema_version: {yaml_scalar(SCHEMA_VERSION)}",
        "artifact: \"dynamic_personal_profile\"",
        "artifact_status: \"generated_derived_view\"",
        f"skill_version: {yaml_scalar(SKILL_VERSION)}",
        f"generated_at: {yaml_scalar(generated_at)}",
        "input_mode: \"derived_only\"",
        "canonical_stable_profile_write: false",
        f"source_snapshot_sha256: {yaml_scalar(source_hash)}",
        f"semantic_snapshot_sha256: {yaml_scalar(semantic)}",
        "source_files:",
    ]
    for record in source_records:
        lines.append(f"  - path: {yaml_scalar(record['path'])}")
        lines.append(f"    sha256: {yaml_scalar(record['sha256'])}")
        lines.append(f"    bytes: {record['bytes']}")
    lines += [
        "time_windows:",
        "  - recent_7d",
        "  - recent_30d",
        "  - long_baseline",
        f"entry_count: {len(entries)}",
        "entries:",
    ]
    for entry in entries:
        lines += [
            f"  - id: {yaml_scalar(entry['id'])}",
            f"    type: {yaml_scalar(entry['type'])}",
            f"    status: {yaml_scalar(entry['status'])}",
            f"    statement: {yaml_scalar(entry['statement'])}",
            "    evidence:",
        ]
        lines += [f"      - {yaml_scalar(path)}" for path in entry["evidence"]]
        lines += [
            "    counterevidence:",
            f"      - {yaml_scalar(entry['counterevidence'][0])}",
            f"    confidence: {yaml_scalar(entry['confidence'])}",
            f"    observed_window: {yaml_scalar(entry['observed_window'])}",
            "    valid_until: null",
            f"    agent_action: {yaml_scalar(entry['agent_action'])}",
            f"    asset_candidate: {yaml_scalar(entry['asset_candidate'])}",
            f"    occurrences: {entry['occurrences']}",
            f"    source_count: {entry['source_count']}",
        ]
    lines += ["---", "", "# Dynamic Personal Profile", "", "## 先看结论", ""]
    if not entries:
        lines.append("当前允许读取的派生数据没有形成可报告的重复信号；本文件保留为空变化视图。")
    else:
        for entry in entries[:8]:
            lines.append(f"- **{entry['status']} / {entry['confidence']}**：{entry['statement']}")
    lines += ["", "## 变化条目", ""]
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
    lines += [
        "## 可立即试用的 Agent 行为",
        "",
        "只把与当前任务直接相关且有证据的 `current`/`emerging` 条目转成临时行为；试用后再决定是否提炼为 Prompt Template、Workflow 或 Skill。",
        "",
        "## Recurring Asset 候选",
        "",
        "资产候选只表示“值得一次真实试用”，不表示已发布、已验证或已进入长期记忆。",
        "",
        "## 边界与不确定性",
        "",
        "- 本文件来自脱敏派生数据，不是原始记录，也不是稳定核心画像。",
        "- 没有源时间戳时不推断精确发生日期。",
        "- 当前脚本不调用 LLM，不做语义事实确认，不自动写回长期记忆。",
        "- `CORE_PROFILE.md`、Custom Instructions、AGENTS.md 和 Memory Atlas canonical records 不会被本次运行修改。",
        "",
    ]
    output = "\n".join(lines)
    if len(output.encode("utf-8")) > MAX_OUTPUT_BYTES:
        raise ValueError(f"output exceeds {MAX_OUTPUT_BYTES} bytes")
    return output


def atomic_write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--now", help="UTC ISO time for deterministic tests")
    parser.add_argument("--check-only", action="store_true")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.resolve()
    output = args.output if args.output.is_absolute() else database_dir / args.output
    try:
        now = iso_now(args.now)
        paths = source_paths(database_dir, output)
        if not paths:
            raise ValueError("no allowlisted derived source files found")
        source_hash, source_records = source_snapshot(paths, database_dir)
        now_dt = datetime.fromisoformat(now.replace("Z", "+00:00"))
        entries = aggregate(collect_records(paths, database_dir, now_dt), now_dt)
        semantic = semantic_hash(source_hash, entries)
        if previous_semantic_hash(output) == semantic:
            print(json.dumps({"status": "NO_CHANGE", "semantic_snapshot_sha256": semantic}, ensure_ascii=False))
            return 0
        content = render(entries, now, source_hash, source_records, semantic)
        if not args.check_only:
            atomic_write(output, content)
        print(json.dumps({
            "status": "CHANGED" if not args.check_only else "WOULD_CHANGE",
            "output": output.relative_to(database_dir).as_posix(),
            "entry_count": len(entries),
            "source_count": len(paths),
            "semantic_snapshot_sha256": semantic,
        }, ensure_ascii=False))
        return 0
    except Exception as exc:
        print(json.dumps({"status": "STOP", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
