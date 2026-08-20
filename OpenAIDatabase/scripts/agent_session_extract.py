#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""agent_session_extract.py —— 把本机各 agent 的会话抽成 canonical 事件

为什么必须抽取而不是整包上传（2026-08-19 实测一个 151MB 的 Claude Code 会话）：
    助手发言 44% ／ 工具输出 40% ／ attachment 12% ／ **用户发言 1%**
用户意图只占百分之一。整包上传等于把 99% 的噪音搬进备份链 ——
而备份链的合同写着单批次 90 分钟、每对象都要远端读回验证，
体积翻三倍就会顶穿上限（当前实测 1.77GB / 2808 对象 / 12 天 100% 成功）。

本仓 config/data_sources/source_registry.json 的隐私合同也早就定了同一件事：
    raw_payload_policy = never_commit_raw_platform_exports_or_full_messages_to_github
    privacy_level      = private_redacted_derived
所以这里只产出脱敏派生摘要，绝不产出原始逐字记录。

输出：每个会话一条 canonical 事件（字段见 source_registry 的 canonical_event_contract）。

用法:
  python3 agent_session_extract.py --source claude-code --out <目录>
  python3 agent_session_extract.py --source all --out <目录> --stats-only
退出码: 0=成功  1=来源不存在或抽取失败
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

HOME = Path.home()

# 各来源的本机位置与解析器名。体积是 2026-08-19 实测的「真实载荷」——
# 已剔除二进制与依赖：.workbuddy 的 binaries 707MB + plugins 189MB 是安装包，
# .kimi-code 的 shell 347MB + bin 178MB 是运行时，都不是会话数据。
SOURCES = {
    "claude-code": {"root": HOME / ".claude" / "projects", "parser": "jsonl_dir", "payload_mb": 3086},
    "codex":       {"root": HOME / ".codex" / "sessions",  "parser": "jsonl_dir", "payload_mb": 1144},
    "kimi-code":   {"root": HOME / ".kimi-code" / "sessions", "parser": "auto",   "payload_mb": 117},
    "workbuddy":   {"root": HOME / ".workbuddy" / "logs",  "parser": "auto",      "payload_mb": 136},
    "dws":         {"root": HOME / ".dws" / "audit",       "parser": "auto",      "payload_mb": 35},
    "openchatcut": {"root": HOME / ".openchatcut" / "project-store-v1", "parser": "auto", "payload_mb": 8},
    # 本仓已入库的历史导出。本机 ~/.claude 只到 2026-07-03，而这里的 chatgpt
    # 导出能回溯到 2025-11 —— 不接它，「全历史」和「180 天」切片就是假的。
    "chatgpt-archive": {"root": Path("OpenAIDatabase/data/public_raw/chatgpt"), "parser": "envelope", "payload_mb": 0},
    "codex-archive":   {"root": Path("OpenAIDatabase/data/public_raw/codex"),   "parser": "envelope", "payload_mb": 0},
}

# 查过但**没有可入库内容**的来源，登记在此以免下次又有人去挖：
#   dsh       ~/Library/Application Support/DSH Desktop —— 1.0GB 全是 Electron 缓存
#             （blob_storage / GPUCache / Session Storage / DawnGraphiteCache），
#             真实状态只有 profile-selection/state.json 与 updates/state.json，无对话。
#   workbuddy ~/.workbuddy —— 1.3GB 里 binaries 707MB + plugins 189MB 是应用安装包；
#             logs/ 是按日期分目录的运行日志（非对话），app/ 是程序自身。
#             真正的对话若存在，应在 WorkBuddy 云端而非本机。
#   mmx       ~/.mmx —— 只有 config.json 与 update-state.json，8KB。
NO_INGEST = {
    "dsh": "Electron 缓存，无对话数据；1.0GB 可直接释放",
    "workbuddy": "应用安装包 + 运行日志，非对话",
    "mmx": "仅配置文件 8KB",
}

# 脱敏：绝对路径 -> ~，以及明显的密钥形态。
# 不追求完美——它是最后一道，不是唯一一道：产出去向是 PRIVATE 仓。
REDACT = [
    (re.compile(re.escape(str(HOME))), "~"),
    (re.compile(r"\b(gh[pousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"), "<SECRET>"),
    (re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"), "<EMAIL>"),
]

# 主题词：从用户发言里认这些，用来做趋势分析。
# 刻意用中文+英文混合，因为实际对话就是混着说的。
TOPIC_WORDS = {
    "治理": ["治理", "governance", "AGENTS.md", "铁律", "复审", "审计"],
    "部署上线": ["部署", "上线", "deploy", "生产", "production", "发布"],
    "修bug": ["bug", "报错", "失败", "error", "修", "fix", "红了"],
    "重构简化": ["重构", "简化", "清理", "删除", "refactor", "simplif"],
    "测试验收": ["测试", "验收", "test", "负控", "变异"],
    "数据": ["数据", "database", "备份", "迁移", "data"],
    "赚钱": ["赚钱", "收入", "变现", "经济价值", "客户", "商业"],
    "前端界面": ["前端", "界面", "UI", "页面", "样式"],
    "自动化": ["自动", "automation", "cron", "定时", "CI"],
    "文档": ["文档", "README", "说明", "手册"],
}


def redact(text: str) -> str:
    for pat, rep in REDACT:
        text = pat.sub(rep, text)
    return text


def topics_of(text: str) -> list:
    low = text.lower()
    return sorted({name for name, kws in TOPIC_WORDS.items()
                   if any(k.lower() in low for k in kws)})


def _iter_json_lines(path: Path):
    try:
        with path.open(encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    yield json.loads(line)
                except ValueError:
                    continue
    except OSError:
        return


def _text_of(obj) -> str:
    """从各家不同的消息结构里捞出纯文本。各 agent 的 schema 不一样，
    所以按「能捞到什么算什么」处理，捞不到就返回空 —— 不猜结构。"""
    if isinstance(obj, str):
        return obj
    if isinstance(obj, list):
        return " ".join(_text_of(x) for x in obj)
    if isinstance(obj, dict):
        for k in ("text", "content", "message", "prompt", "input"):
            if k in obj:
                return _text_of(obj[k])
    return ""


def extract_jsonl_session(path: Path, source_id: str) -> dict | None:
    """一个 jsonl = 一个会话。只留信号：用户发言、助手结论首行、报错。"""
    user_texts, tool_calls, msg_count, errors = [], 0, 0, 0
    first_ts = last_ts = None
    for d in _iter_json_lines(path):
        if not isinstance(d, dict):
            # 有的来源整个文件是一个 list（openchatcut 的 project-store 就是）。
            # 不猜结构 —— 跳过，让它以 NO_EVENTS 暴露出来，而不是产出半真的事件。
            continue
        msg_count += 1
        blob = json.dumps(d, ensure_ascii=False)
        if '"tool_result"' in blob or '"toolUseResult"' in blob or '"tool_use"' in blob:
            tool_calls += 1
        role = d.get("type") or d.get("role")
        if role == "user":
            t = _text_of(d.get("message") or d)
            if t and len(t) < 4000:          # 超长的多半是粘贴的日志，不是意图
                user_texts.append(t)
        if re.search(r"\berror\b|失败|报错|Traceback", blob, re.I):
            errors += 1
        ts = d.get("timestamp") or d.get("created_at") or d.get("time")
        if isinstance(ts, str) and len(ts) >= 10:
            first_ts = first_ts or ts
            last_ts = ts
    if msg_count == 0:
        return None
    joined = redact(" ".join(user_texts))[:4000]
    st = path.stat()
    occurred = first_ts or datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat()
    rid = f"{source_id}-{path.stem[:40]}"
    return {
        "source_id": source_id,
        "record_id": rid,
        "occurred_at": occurred,
        "record_type": f"{source_id}_session_summary",
        "title": redact(user_texts[0][:120]) if user_texts else f"{source_id} 会话",
        "summary": joined[:1200],
        "topics": topics_of(joined),
        "sensitivity": "private_redacted_derived",
        "memory_tier": "一般",
        "importance": "高" if len(user_texts) >= 20 else ("中" if len(user_texts) >= 5 else "低"),
        "confidence": "高",
        "dedupe_key": hashlib.sha256(f"{source_id}:{path.stem}".encode()).hexdigest()[:32],
        "source_kind": "local_agent_session",
        "behavior_metrics": {
            "message_count": msg_count,
            "user_turn_count": len(user_texts),
            "tool_call_count": tool_calls,
            "error_mention_count": errors,
            "raw_bytes": st.st_size,
            "last_activity": last_ts or occurred,
        },
        "project_refs": [redact(str(path.parent.name))],
    }


def _load_state(out_dir: Path, source_id: str) -> dict:
    """增量状态：文件路径 -> (mtime, size)。这是「每日沉淀」的关键 ——
    没有它每天都要重扫 4.3GB，跑不进 codex 那 90 分钟批次。"""
    f = out_dir / f".{source_id}.state.json"
    if f.is_file():
        try:
            return json.loads(f.read_text(encoding="utf-8"))
        except ValueError:
            return {}
    return {}


def _save_state(out_dir: Path, source_id: str, state: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / f".{source_id}.state.json").write_text(
        json.dumps(state, ensure_ascii=False, sort_keys=True), encoding="utf-8")


def extract_envelope(path: Path, source_id: str) -> dict | None:
    """已入库导出的信封格式：整文件一个 dict，有 created_at 与 messages[]。
    和本机 jsonl 不同结构，所以单独一个解析器 —— 不去猜、不去合并。"""
    try:
        d = json.loads(path.read_text(encoding="utf-8", errors="ignore"))
    except (ValueError, OSError):
        return None
    if not isinstance(d, dict):
        return None
    msgs = d.get("messages") or []
    if not isinstance(msgs, list) or not msgs:
        return None
    users = [_text_of(m) for m in msgs
             if isinstance(m, dict) and m.get("role") == "user"]
    joined = redact(" ".join(u for u in users if u))[:4000]
    occurred = str(d.get("created_at") or d.get("occurred_at") or "")[:19] or None
    if not occurred:
        return None
    rid = f"{source_id}-{(d.get('conversation_id') or path.stem)[:40]}"
    return {
        "source_id": source_id, "record_id": rid, "occurred_at": occurred,
        "record_type": f"{source_id}_session_summary",
        "title": redact(users[0][:120]) if users else f"{source_id} 会话",
        "summary": joined[:1200], "topics": topics_of(joined),
        "sensitivity": "private_redacted_derived", "memory_tier": "一般",
        "importance": "中" if len(users) >= 5 else "低", "confidence": "高",
        "dedupe_key": hashlib.sha256(f"{source_id}:{rid}".encode()).hexdigest()[:32],
        "source_kind": "ingested_export",
        "behavior_metrics": {
            "message_count": d.get("message_count") or len(msgs),
            "user_turn_count": len(users), "tool_call_count": 0,
            "error_mention_count": 0, "raw_bytes": path.stat().st_size,
            "last_activity": occurred,
        },
        "project_refs": [],
    }


def extract_source(source_id: str, out_dir: Path, stats_only: bool = False,
                   incremental: bool = False) -> dict:
    cfg = SOURCES[source_id]
    root = Path(cfg["root"])
    if not root.exists():
        return {"source_id": source_id, "state": "MISSING_SOURCE", "root": str(root)}
    files = [p for p in root.rglob("*.jsonl")] or [p for p in root.rglob("*.json")]

    prev = _load_state(out_dir, source_id) if incremental else {}
    kept = {}
    if incremental:
        # 已有事件按 record_id 保留，只重算变化的文件。
        old_events = {}
        tgt = out_dir / f"{source_id}.events.jsonl"
        if tgt.is_file():
            for line in tgt.read_text(encoding="utf-8", errors="ignore").splitlines():
                if line.strip():
                    try:
                        e = json.loads(line)
                        old_events[e["record_id"]] = e
                    except (ValueError, KeyError):
                        continue
        kept = old_events

    events, raw_bytes, rescanned, new_state = [], 0, 0, {}
    for p in files:
        try:
            st = p.stat()
        except OSError:
            continue
        raw_bytes += st.st_size
        key = str(p)
        sig = [int(st.st_mtime), st.st_size]
        new_state[key] = sig
        if incremental and prev.get(key) == sig:
            continue                    # 没变，跳过重算
        rescanned += 1
        ev = (extract_envelope(p, source_id) if cfg.get("parser") == "envelope"
              else extract_jsonl_session(p, source_id))
        if ev:
            events.append(ev)

    if incremental:
        for e in events:
            kept[e["record_id"]] = e     # 新的覆盖旧的
        events = sorted(kept.values(), key=lambda e: e["occurred_at"])

    out_bytes = 0
    if events and not stats_only:
        out_dir.mkdir(parents=True, exist_ok=True)
        target = out_dir / f"{source_id}.events.jsonl"
        body = "\n".join(json.dumps(e, ensure_ascii=False, sort_keys=True) for e in events) + "\n"
        target.write_text(body, encoding="utf-8")
        out_bytes = len(body.encode("utf-8"))
        if incremental:
            _save_state(out_dir, source_id, new_state)
    elif events:
        out_bytes = sum(len(json.dumps(e, ensure_ascii=False).encode()) for e in events) + len(events)
    return {
        "source_id": source_id, "state": "READY" if events else "NO_EVENTS",
        "files_scanned": len(files), "events": len(events),
        "raw_mb": round(raw_bytes / 1048576, 1), "rescanned": rescanned,
        "out_mb": round(out_bytes / 1048576, 2),
        "reduction_pct": round(100 - out_bytes * 100 / raw_bytes, 2) if raw_bytes else 0,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--source", default="all", help="来源 id 或 all")
    ap.add_argument("--out", default="_out")
    ap.add_argument("--stats-only", action="store_true", help="只统计不落盘")
    ap.add_argument("--incremental", action="store_true",
                    help="只重算 mtime/size 变化的文件（每日跑必须开）")
    args = ap.parse_args()
    ids = list(SOURCES) if args.source == "all" else [args.source]
    bad = [i for i in ids if i not in SOURCES]
    if bad:
        print(f"FAIL: 未知来源 {bad}；可选 {list(SOURCES)}")
        return 1
    out = Path(args.out)
    rows = [extract_source(i, out, args.stats_only, args.incremental) for i in ids]
    tr = sum(r.get("raw_mb", 0) for r in rows)
    to = sum(r.get("out_mb", 0) for r in rows)
    print(f"{'来源':<14}{'状态':<16}{'文件':>7}{'事件':>8}{'重算':>7}{'原始MB':>10}{'产出MB':>9}{'压缩':>8}")
    for r in rows:
        print(f"{r['source_id']:<14}{r['state']:<16}{r.get('files_scanned',0):>7}"
              f"{r.get('events',0):>8}{r.get('rescanned',0):>7}{r.get('raw_mb',0):>10}{r.get('out_mb',0):>9}"
              f"{str(r.get('reduction_pct',0))+'%':>8}")
    print(f"{'合计':<14}{'':<16}{'':>7}{sum(r.get('events',0) for r in rows):>8}"
          f"{sum(r.get('rescanned',0) for r in rows):>7}"
          f"{round(tr,1):>10}{round(to,2):>9}"
          f"{(str(round(100-to*100/tr,2))+'%' if tr else '-'):>8}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
