#!/usr/bin/env python3
"""Shared primitives for the expert-team candidate runtime.

The module intentionally uses only Python's standard library so the registry remains
portable.  It performs lexical/structural routing; model-driven semantic routing can
augment it through the telemetry contract, but cannot silently replace it.
"""
from __future__ import annotations

import json
import math
import re
from pathlib import Path
from typing import Any, Iterable

WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9_+./-]*|[\u3400-\u9fff]{1,8}|\d+(?:\.\d+)?")
STOP = {
    "the", "a", "an", "and", "or", "to", "of", "for", "in", "on", "with", "by",
    "is", "are", "be", "this", "that", "it", "as", "from", "at", "please", "help",
    "使用", "帮我", "需要", "进行", "一个", "这个", "那个", "以及", "或者", "并且", "然后",
    "给我", "确保", "完成", "提供", "分析", "优化", "方案", "任务",
}


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def flatten_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return " ".join(flatten_text(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten_text(v) for v in value)
    return str(value)


def tokens(value: Any) -> set[str]:
    text = flatten_text(value).casefold()
    out: set[str] = set()
    for raw in WORD_RE.findall(text):
        token = raw.strip("-_/+. ")
        if len(token) < 2 or token in STOP:
            continue
        out.add(token)
        # Chinese chunks are also decomposed into bi-grams for partial matching.
        if re.fullmatch(r"[\u3400-\u9fff]{3,}", token):
            out.update(token[i:i + 2] for i in range(len(token) - 1))
    return out


def overlap_score(left: Any, right: Any) -> float:
    a, b = tokens(left), tokens(right)
    if not a or not b:
        return 0.0
    inter = len(a & b)
    # Asymmetric coverage is more useful for routing than plain Jaccard: a concise
    # work packet can be fully covered by a much larger expert profile.
    return 0.65 * (inter / len(a)) + 0.35 * (inter / math.sqrt(len(a) * len(b)))


def clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def normalized_count(text: str, patterns: Iterable[str], denominator: float) -> float:
    low = text.casefold()
    hits = sum(1 for pattern in patterns if pattern.casefold() in low)
    return clamp(hits / max(denominator, 1.0))


def iso_year(value: Any) -> int | None:
    if not value:
        return None
    match = re.match(r"(\d{4})", str(value))
    return int(match.group(1)) if match else None


def unique_preserving_order(items: Iterable[Any]) -> list[Any]:
    seen: set[Any] = set()
    out: list[Any] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        out.append(item)
    return out


def required_control_plane() -> list[dict[str, Any]]:
    """Mandatory quality controls. They are neutral functional roles, not personas.

    They do not count toward Single/Small/Deep/Swarm persona seat ranges.
    """
    return [
        {
            "role_id": "team-orchestrator",
            "role_type": "control",
            "purpose": "维护目标、依赖、权限、工作包、阶段门和失败返回路径。",
            "isolated_from": ["decision-judge"],
        },
        {
            "role_id": "hypothesis-framer",
            "role_type": "control",
            "purpose": "在求解前列出关键假设、可证伪预测、信息缺口和改判条件。",
            "isolated_from": ["persona-solver-*"],
        },
        {
            "role_id": "counterevidence-adversary",
            "role_type": "control",
            "purpose": "寻找反证、冲突来源、失败前提、相关性错误和替代解释。",
            "isolated_from": ["persona-solver-*", "independent-reviewer"],
        },
        {
            "role_id": "independent-reviewer",
            "role_type": "control",
            "purpose": "只读取密封候选产物和证据摘要，检查完整性、可执行性和事实风险。",
            "isolated_from": ["persona-solver-*", "counterevidence-adversary"],
        },
        {
            "role_id": "decision-judge",
            "role_type": "control",
            "purpose": "按预先冻结的判据裁决，不以多数票或折中替代证据。",
            "isolated_from": ["persona-solver-*", "team-orchestrator"],
        },
        {
            "role_id": "synthesis-lead",
            "role_type": "control",
            "purpose": "将裁决后的结论编译为单一、连贯、可直接使用的最终交付物。",
            "isolated_from": ["decision-judge"],
        },
    ]


MODE_LIMITS: dict[str, tuple[int, int | None]] = {
    "single_expert": (1, 1),
    "small_team": (5, 15),
    "deep_team": (10, 30),
    "swarm": (25, None),
}


def valid_mode_size(mode: str, size: int) -> bool:
    if mode not in MODE_LIMITS:
        return False
    low, high = MODE_LIMITS[mode]
    return size >= low and (high is None or size <= high)
