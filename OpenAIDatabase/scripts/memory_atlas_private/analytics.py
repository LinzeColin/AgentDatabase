from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Iterable

from .models import NormalizedEvent


ACTIVITIES = (
    "research_diagnosis",
    "product_planning",
    "development_deployment",
    "verification_repair",
    "management_learning",
    "decision_execution",
    "unknown",
)

OUTCOME_VERIFIED = {"deployed_verified", "restore_verified", "adopted_verified", "decision_impact_verified"}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _ratio(numerator: float, denominator: float) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 4)


def build_behavior_analytics(events: Iterable[NormalizedEvent], generated_at: str | None = None) -> dict[str, Any]:
    activity_counts: Counter[str] = Counter()
    augmentation_counts: Counter[str] = Counter()
    outcome_counts: Counter[str] = Counter()
    by_project: dict[str, dict[str, float]] = defaultdict(
        lambda: {"events": 0.0, "verified_outcomes": 0.0, "effort_minutes": 0.0}
    )
    event_count = 0
    verified_event_count = 0
    effort_known_count = 0
    total_effort = 0.0
    verified_effort = 0.0
    for event in events:
        event_count += 1
        activity_counts[event.activity if event.activity in ACTIVITIES else "unknown"] += 1
        augmentation_counts[event.augmentation_mode or "unknown"] += 1
        outcome_counts[event.outcome_state or "unknown"] += 1
        verified = event.outcome_state in OUTCOME_VERIFIED
        if verified:
            verified_event_count += 1
        if event.effort_minutes is not None and event.effort_minutes >= 0:
            effort_known_count += 1
            effort = float(event.effort_minutes or 0)
            total_effort += effort
            if verified:
                verified_effort += effort
        project = event.project or "unknown"
        by_project[project]["events"] += 1
        if verified:
            by_project[project]["verified_outcomes"] += 1
        if event.effort_minutes is not None:
            by_project[project]["effort_minutes"] += float(event.effort_minutes)
    if effort_known_count:
        denominator_type = "effort_minutes"
        verified_outcome_rate = _ratio(verified_effort, total_effort)
        numerator = verified_effort
        denominator = total_effort
    else:
        denominator_type = "event_count"
        denominator = float(event_count)
        numerator = float(verified_event_count)
        verified_outcome_rate = _ratio(numerator, denominator)
    return {
        "schema_version": "memory_atlas.behavior_economics.v1",
        "generated_at": generated_at or utc_now(),
        "method": {
            "classification": "observed_usage_multi_label_deterministic",
            "model_calls": 0,
            "direct_global_percentile_allowed": False,
            "unknowns_are_not_pass": True,
        },
        "activity_distribution": {
            key: {"count": activity_counts.get(key, 0), "share": _ratio(activity_counts.get(key, 0), event_count)}
            for key in ACTIVITIES
        },
        "augmentation_distribution": {
            key: {"count": count, "share": _ratio(count, event_count)}
            for key, count in sorted(augmentation_counts.items())
        },
        "outcome_distribution": dict(sorted(outcome_counts.items())),
        "verified_outcome_rate": {
            "value": verified_outcome_rate,
            "numerator": round(numerator, 2),
            "denominator": round(denominator, 2),
            "denominator_type": denominator_type,
            "verified_states": sorted(OUTCOME_VERIFIED),
            "state": "MEASURED" if verified_outcome_rate is not None else "UNKNOWN",
        },
        "projects": [
            {"project": project, **{key: round(value, 2) for key, value in metrics.items()}}
            for project, metrics in sorted(by_project.items())
        ],
        "event_count": event_count,
    }


def compare_with_benchmark(
    personal: dict[str, Any],
    benchmark: dict[str, Any],
) -> dict[str, Any]:
    required_equal = ("taxonomy_version", "unit", "window_days", "population_scope")
    mismatches = [
        key for key in required_equal
        if personal.get("comparison_contract", {}).get(key) != benchmark.get("comparison_contract", {}).get(key)
    ]
    benchmark_sample = int(benchmark.get("comparison_contract", {}).get("sample_size", 0) or 0)
    comparable = not mismatches and benchmark_sample >= 30
    if not comparable:
        return {
            "schema_version": "memory_atlas.benchmark_comparison.v1",
            "state": "DIRECTION_ONLY",
            "percentile": None,
            "mismatches": mismatches,
            "sample_size": benchmark_sample,
            "message_zh": "口径、总体或样本不足；仅显示方向参考，不生成全球百分位。",
        }
    distribution = benchmark.get("distribution")
    value = personal.get("value")
    if not isinstance(distribution, list) or not distribution or not isinstance(value, (int, float)):
        return {
            "schema_version": "memory_atlas.benchmark_comparison.v1",
            "state": "DIRECTION_ONLY",
            "percentile": None,
            "mismatches": ["distribution_or_value_missing"],
            "sample_size": benchmark_sample,
            "message_zh": "缺少可验证分布或个人值；不生成百分位。",
        }
    numeric = sorted(float(item) for item in distribution if isinstance(item, (int, float)))
    if len(numeric) < 30:
        return {
            "schema_version": "memory_atlas.benchmark_comparison.v1",
            "state": "DIRECTION_ONLY",
            "percentile": None,
            "mismatches": ["usable_distribution_below_30"],
            "sample_size": len(numeric),
            "message_zh": "有效分布样本不足；不生成百分位。",
        }
    rank = sum(1 for item in numeric if item <= float(value))
    return {
        "schema_version": "memory_atlas.benchmark_comparison.v1",
        "state": "COMPARABLE",
        "percentile": round(100 * rank / len(numeric), 1),
        "mismatches": [],
        "sample_size": len(numeric),
        "message_zh": "同口径比较；百分位仅适用于该基准总体和时间窗。",
    }


def build_habit_recommendations(analytics: dict[str, Any], failure_snapshot: dict[str, Any]) -> list[dict[str, Any]]:
    recommendations: list[dict[str, Any]] = []
    distribution = analytics.get("activity_distribution", {})
    research_share = distribution.get("research_diagnosis", {}).get("share")
    verification_share = distribution.get("verification_repair", {}).get("share")
    vor = analytics.get("verified_outcome_rate", {}).get("value")
    if isinstance(research_share, (int, float)) and isinstance(vor, (int, float)) and research_share > 0.35 and vor < 0.4:
        recommendations.append({
            "recommendation_id": "habit-research-to-outcome-gate",
            "fact": "研究与诊断占比高，已验证成果率低于 40%。",
            "alternative_explanation": "项目可能处于必要的前期研究期。",
            "action": "为每个研究线程绑定一个可验证决策、测试或交付结果；无绑定则停止继续扩展。",
            "success_metric": "verified_outcome_rate",
            "observation_window_days": 14,
            "rollback": "若高风险决策质量下降，恢复研究预算并重新校准门槛。",
            "confidence": "medium",
        })
    if isinstance(verification_share, (int, float)) and verification_share < 0.12:
        recommendations.append({
            "recommendation_id": "habit-verification-coverage",
            "fact": "验证与修复活动占比偏低。",
            "alternative_explanation": "部分验证可能由 CI 自动完成，未被当前来源记录。",
            "action": "先完善 CI 与运行证据采集，再判断是否增加人工验证。",
            "success_metric": "evidence_bound_completion_rate",
            "observation_window_days": 14,
            "rollback": "若自动证据已覆盖，则不增加人工步骤。",
            "confidence": "low",
        })
    metrics = failure_snapshot.get("metrics", {})
    if int(metrics.get("historical_recurrences", 0)) > int(metrics.get("blocked_recurrences", 0)):
        recommendations.append({
            "recommendation_id": "habit-regression-asset-gap",
            "fact": "历史复发次数高于已阻止复发次数。",
            "alternative_explanation": "部分历史故障发生在回归引擎建立前。",
            "action": "优先把高频 P0/P1 Incident 转成最小 Fixture、Oracle 和故障注入。",
            "success_metric": "nonrecurrence_ratio",
            "observation_window_days": 30,
            "rollback": "若测试成本超过避免的返工成本，降低冷回放频率而不删除资产。",
            "confidence": "high",
        })
    return recommendations[:3]
