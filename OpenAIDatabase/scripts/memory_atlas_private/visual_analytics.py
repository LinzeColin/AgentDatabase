from __future__ import annotations

"""Deterministic, model-free metrics and exactly three visual datasets."""

from collections import Counter, defaultdict
from datetime import datetime
from statistics import median
from typing import Any, Iterable, Mapping

VERIFIED_OUTCOMES = {
    "deployed_verified", "adopted_verified", "decision_impact_verified",
    "recovery_verified", "accepted_verified",
}


def _ratio(numerator: float, denominator: float) -> float | None:
    return round(numerator / denominator, 6) if denominator > 0 else None


def _metric(value: float | None, numerator: float | None, denominator: float | None, basis: str, label: str, *, proxy: bool = False) -> dict[str, Any]:
    return {"value": value, "numerator": numerator, "denominator": denominator, "denominator_basis": basis, "label_zh": label, "proxy": proxy}


def _parse(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"invalid {field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} requires timezone")
    return parsed


def build_visual_analytics(events: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    rows = [dict(row) for row in events]
    for index, row in enumerate(rows):
        for field in ("event_id", "occurred_at", "activity_type", "outcome_state", "model_tool"):
            if not isinstance(row.get(field), str) or not row[field].strip():
                raise ValueError(f"event[{index}].{field} is required")
        occurred = _parse(row["occurred_at"], f"event[{index}].occurred_at")
        verified_at = row.get("verified_at")
        if verified_at is not None:
            if not isinstance(verified_at, str) or not verified_at.strip():
                raise ValueError(f"event[{index}].verified_at must be an ISO timestamp or null")
            verified = _parse(verified_at, f"event[{index}].verified_at")
            if verified < occurred:
                raise ValueError(f"event[{index}].verified_at precedes occurred_at")

    event_count = len(rows)
    verified_count = sum(1 for row in rows if row["outcome_state"] in VERIFIED_OUTCOMES)
    evidence_count = sum(1 for row in rows if row.get("outcome_evidence") is True)
    known_effort = sum(float(row["work_time_minutes"]) for row in rows if isinstance(row.get("work_time_minutes"), (int, float)) and row["work_time_minutes"] >= 0)
    verified_effort = sum(float(row["work_time_minutes"]) for row in rows if row["outcome_state"] in VERIFIED_OUTCOMES and isinstance(row.get("work_time_minutes"), (int, float)) and row["work_time_minutes"] >= 0)
    known_effort_events = sum(1 for row in rows if isinstance(row.get("work_time_minutes"), (int, float)) and row["work_time_minutes"] >= 0)

    activity_counts = Counter(str(row["activity_type"]) for row in rows)
    outcome_counts = Counter(str(row["outcome_state"]) for row in rows)
    activity_verified = Counter(str(row["activity_type"]) for row in rows if row["outcome_state"] in VERIFIED_OUTCOMES)
    by_day: dict[str, dict[str, Any]] = defaultdict(lambda: {"event_count": 0, "verified_count": 0, "time_to_truth_hours": []})
    by_heat: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        day = row["occurred_at"][:10]
        by_day[day]["event_count"] += 1
        if row["outcome_state"] in VERIFIED_OUTCOMES:
            by_day[day]["verified_count"] += 1
            if isinstance(row.get("verified_at"), str):
                hours = (_parse(row["verified_at"], "verified_at") - _parse(row["occurred_at"], "occurred_at")).total_seconds() / 3600
                by_day[day]["time_to_truth_hours"].append(hours)
        by_heat[(str(row["activity_type"]), str(row["model_tool"]), str(row["outcome_state"]))] += 1

    contribution_rows = []
    for activity in sorted(activity_counts):
        count = activity_counts[activity]
        verified = activity_verified[activity]
        contribution_rows.append({"activity_type": activity, "event_count": count, "verified_count": verified, "quality_score": _ratio(verified, count)})

    trend_rows = []
    cumulative_events = 0
    cumulative_verified = 0
    for day in sorted(by_day):
        cumulative_events += by_day[day]["event_count"]
        cumulative_verified += by_day[day]["verified_count"]
        samples = by_day[day]["time_to_truth_hours"]
        trend_rows.append({
            "date": day,
            "event_count": by_day[day]["event_count"],
            "verified_count": by_day[day]["verified_count"],
            "verification_debt_proxy_event": _ratio(cumulative_events - cumulative_verified, cumulative_events),
            "time_to_truth_hours": round(float(median(samples)), 3) if samples else None,
            "time_to_truth_sample_count": len(samples),
        })

    heat_rows = [
        {"activity_type": activity, "model_tool": tool, "outcome_state": outcome, "count": count}
        for (activity, tool, outcome), count in sorted(by_heat.items())
    ]
    metrics = {
        "verified_outcome_rate_event": _metric(_ratio(verified_count, event_count), verified_count, event_count, "event_count", "事件口径已验证结果率"),
        "verified_outcome_rate_work_time": _metric(_ratio(verified_effort, known_effort), verified_effort if known_effort else None, known_effort if known_effort else None, "known_work_time_minutes", "工时加权已验证结果率"),
        "work_time_coverage_rate": _metric(_ratio(known_effort_events, event_count), known_effort_events, event_count, "events_with_known_work_time/event_count", "工时覆盖率"),
        "outcome_evidence_coverage_rate": _metric(_ratio(evidence_count, event_count), evidence_count, event_count, "events_with_outcome_evidence/event_count", "结果证据覆盖率"),
        "verification_debt_proxy_event": _metric(_ratio(event_count - verified_count, event_count), event_count - verified_count, event_count, "unverified_events/event_count", "事件验证债务代理", proxy=True),
    }
    return {
        "schema_version": "memory_atlas.visual_analytics.v1",
        "event_count": event_count,
        "event_window": {"start_at": min((row["occurred_at"] for row in rows), default=None), "end_at": max((row["occurred_at"] for row in rows), default=None)},
        "activity_distribution": {key: {"count": count, "share": _ratio(count, event_count)} for key, count in sorted(activity_counts.items())},
        "outcome_distribution": dict(sorted(outcome_counts.items())),
        "metrics": metrics,
        "visuals": [
            {"id": "quality_contribution_grid", "title_zh": "质量加权结果贡献网格", "kind": "GRID", "rows": contribution_rows},
            {"id": "verification_debt_trend", "title_zh": "验证债务与 Time-to-Truth 趋势", "kind": "TREND", "rows": trend_rows},
            {"id": "task_tool_outcome_heatmap", "title_zh": "任务 × 模型／工具 × 结果热力图", "kind": "HEATMAP", "rows": heat_rows},
        ],
    }
