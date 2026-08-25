#!/usr/bin/env python3
"""Strict all-dimension champion logic for Prompt Compiler.

This module is deliberately standard-library-only.  It provides the evidence
contract that v0.0.0.4 uses to distinguish three states:

* CHAMPION_PASS: Prompt Compiler is statistically first on every frozen,
  mandatory dimension against every required peer that actually ran.
* CHAMPION_NOT_PROVEN: evidence is incomplete, tied, or uncertainty overlaps.
* CHAMPION_REJECTED: at least one peer is demonstrably better on a mandatory
  dimension.

The status is scoped to the exact sealed dataset, model identities, evaluator,
budget, repeat count, and competitor registry recorded in the evidence file.
It is never a universal claim.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import hashlib
import json
import math
from pathlib import Path
import random
import re
import statistics
from typing import Any, Iterable, Mapping, MutableMapping, Sequence

SCHEMA_VERSION = "1.0"
CHAMPION_STATUS_PASS = "CHAMPION_PASS"
CHAMPION_STATUS_NOT_PROVEN = "CHAMPION_NOT_PROVEN"
CHAMPION_STATUS_REJECTED = "CHAMPION_REJECTED"

# All values are normalized so that higher is better.
MANDATORY_DIMENSIONS: tuple[str, ...] = (
    "overall",
    "worst_case",
    "weakest_slice",
    "stability",
    "correctness",
    "coverage",
    "executability",
    "security",
    "efficiency",
    "oracle",
    "hard_safety",
    "regression",
    "redteam",
    "cost_efficiency",
    "latency_efficiency",
)

DIMENSION_LABELS_ZH: dict[str, str] = {
    "overall": "总体效果",
    "worst_case": "最差案例",
    "weakest_slice": "最弱任务切片",
    "stability": "稳定性",
    "correctness": "正确性",
    "coverage": "覆盖完整性",
    "executability": "可执行性",
    "security": "安全性",
    "efficiency": "提示词效率",
    "oracle": "业务预言机一致性",
    "hard_safety": "硬安全",
    "regression": "回归保持",
    "redteam": "红队韧性",
    "cost_efficiency": "成本效率代理",
    "latency_efficiency": "延迟效率代理",
}

# Capability priors do not decide the winner. They only allocate the search
# budget after every required arm receives a minimum probe.
CAPABILITY_PRIORS: dict[str, dict[str, float]] = {
    "gepa": {
        "overall": 1.15,
        "weakest_slice": 1.10,
        "correctness": 1.10,
        "coverage": 1.10,
        "executability": 1.05,
    },
    "autoresearch": {
        "overall": 1.12,
        "stability": 1.18,
        "cost_efficiency": 1.20,
        "latency_efficiency": 1.15,
        "regression": 1.12,
    },
    "meta_harness": {
        "coverage": 1.12,
        "executability": 1.18,
        "security": 1.08,
        "weakest_slice": 1.08,
    },
    "promptfoo": {
        "hard_safety": 1.20,
        "regression": 1.22,
        "redteam": 1.25,
        "security": 1.15,
        "oracle": 1.10,
    },
    "prompt_compiler": {dimension: 1.0 for dimension in MANDATORY_DIMENSIONS},
}


class ChampionContractError(RuntimeError):
    """Raised for malformed champion evidence or impossible budgets."""


@dataclass(frozen=True)
class DimensionSpec:
    name: str
    minimum_margin: float = 0.0
    confidence: float = 0.95
    required: bool = True
    higher_is_better: bool = True


@dataclass(frozen=True)
class PairwiseDimensionResult:
    peer: str
    dimension: str
    candidate_mean: float
    peer_mean: float
    observed_delta: float
    lower_bound: float
    upper_bound: float
    minimum_margin: float
    status: str
    sample_count: int

    def as_dict(self) -> dict[str, Any]:
        return {
            "peer": self.peer,
            "dimension": self.dimension,
            "dimension_zh": DIMENSION_LABELS_ZH.get(self.dimension, self.dimension),
            "candidate_mean": self.candidate_mean,
            "peer_mean": self.peer_mean,
            "observed_delta": self.observed_delta,
            "lower_bound": self.lower_bound,
            "upper_bound": self.upper_bound,
            "minimum_margin": self.minimum_margin,
            "status": self.status,
            "sample_count": self.sample_count,
        }


@dataclass
class EvaluationCache:
    """Small deterministic cache used to avoid duplicate model evaluations."""

    values: MutableMapping[str, Any] = field(default_factory=dict)
    hits: int = 0
    misses: int = 0

    @staticmethod
    def key(*, candidate: str, case: Mapping[str, Any], role_identity: str, repeat: int, phase: str) -> str:
        payload = {
            "candidate": candidate,
            "case": case,
            "role_identity": role_identity,
            "repeat": repeat,
            "phase": phase,
        }
        encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()

    def get(self, key: str) -> Any | None:
        if key in self.values:
            self.hits += 1
            return self.values[key]
        self.misses += 1
        return None

    def put(self, key: str, value: Any) -> None:
        self.values[key] = value

    def stats(self) -> dict[str, int]:
        return {"entries": len(self.values), "hits": self.hits, "misses": self.misses}


@dataclass(frozen=True)
class BudgetPlan:
    total_budget: int
    minimum_probe: int
    allocations: dict[str, int]
    rationale: dict[str, Any]

    def verify(self) -> None:
        if sum(self.allocations.values()) != self.total_budget:
            raise ChampionContractError("预算分配之和不等于冻结总预算")
        if any(value < self.minimum_probe for value in self.allocations.values()):
            raise ChampionContractError("至少一个必选执行器未获得最低探测预算")

    def as_dict(self) -> dict[str, Any]:
        self.verify()
        return {
            "total_budget": self.total_budget,
            "minimum_probe": self.minimum_probe,
            "allocations": dict(self.allocations),
            "rationale": self.rationale,
            "sum": sum(self.allocations.values()),
            "budget_conserved": True,
        }


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, float(value)))


def _mean(values: Sequence[float]) -> float:
    return statistics.fmean(values) if values else 0.0


def _weakest_slice(result: Mapping[str, Any]) -> float | None:
    per_task = result.get("per_task")
    if not isinstance(per_task, Mapping) or not per_task:
        return None
    values = [float(value) for value in per_task.values()]
    return min(values) if values else None


def _row_cost_efficiency(row: Mapping[str, Any]) -> float | None:
    # Prefer measured token usage when an adapter supplies it. Character counts
    # are a clearly-labelled provider-neutral proxy, not a monetary cost claim.
    usage = row.get("usage")
    if isinstance(usage, Mapping):
        tokens = usage.get("total_tokens")
        if tokens is not None:
            return 1.0 / (1.0 + max(0.0, float(tokens)) / 1000.0)
    chars = row.get("work_chars")
    if chars is None:
        candidate_chars = row.get("candidate_chars")
        output_chars = row.get("output_chars")
        if candidate_chars is None or output_chars is None:
            return None
        chars = float(candidate_chars) + float(output_chars)
    return 1.0 / (1.0 + max(0.0, float(chars)) / 4000.0)


def _row_latency_efficiency(row: Mapping[str, Any]) -> float | None:
    elapsed = row.get("elapsed_seconds")
    if elapsed is None:
        return None
    return 1.0 / (1.0 + max(0.0, float(elapsed)))


def dimension_samples(
    final_result: Mapping[str, Any],
    *,
    regression_result: Mapping[str, Any] | None = None,
    redteam_result: Mapping[str, Any] | None = None,
    dimensions: Sequence[str] | None = None,
) -> dict[str, list[float]]:
    """Extract aligned, higher-is-better samples for frozen dimensions.

    The built-in 15 dimensions are always understood.  Additional project
    dimensions are accepted when the evaluator emits a normalized value in each
    result row's ``dimensions`` object. Missing values fail closed later.
    """
    requested = list(dict.fromkeys(str(name) for name in (dimensions or MANDATORY_DIMENSIONS)))
    rows = [row for row in final_result.get("results", []) if isinstance(row, Mapping)]
    samples: dict[str, list[float]] = {name: [] for name in requested}
    case_scores: dict[str, list[float]] = {}
    task_scores: dict[str, list[float]] = {}
    for row in rows:
        score = _clamp(float(row.get("score", 0.0)))
        if "overall" in samples:
            samples["overall"].append(score)
        case_scores.setdefault(str(row.get("case_id", "unknown")), []).append(score)
        task_scores.setdefault(str(row.get("task_id", "default")), []).append(score)
        row_dimensions = row.get("dimensions") if isinstance(row.get("dimensions"), Mapping) else {}
        for name in requested:
            if name in row_dimensions:
                samples[name].append(_clamp(float(row_dimensions[name])))
        if "hard_safety" in samples:
            samples["hard_safety"].append(0.0 if bool(row.get("hard_fail")) else 1.0)
        if "cost_efficiency" in samples:
            cost_efficiency = _row_cost_efficiency(row)
            if cost_efficiency is not None:
                samples["cost_efficiency"].append(_clamp(cost_efficiency))
        if "latency_efficiency" in samples:
            latency_efficiency = _row_latency_efficiency(row)
            if latency_efficiency is not None:
                samples["latency_efficiency"].append(_clamp(latency_efficiency))

    # Worst-case and weakest-slice are represented as repeated group statistics,
    # giving bootstrap a real unit rather than a single pseudo-sample.
    if "worst_case" in samples:
        samples["worst_case"] = [min(values) for values in case_scores.values() if values]
    if "weakest_slice" in samples:
        samples["weakest_slice"] = [_mean(values) for values in task_scores.values() if values]
        if samples["weakest_slice"]:
            weakest = min(samples["weakest_slice"])
            samples["weakest_slice"] = [weakest for _ in samples["weakest_slice"]]

    if rows and "stability" in samples and "overall" in samples:
        score_mean = _mean(samples["overall"])
        samples["stability"] = [_clamp(1.0 - abs(score - score_mean)) for score in samples["overall"]]

    def suite_safety(result: Mapping[str, Any] | None) -> list[float]:
        if not result:
            return []
        suite_rows = [row for row in result.get("results", []) if isinstance(row, Mapping)]
        if suite_rows:
            return [0.0 if bool(row.get("hard_fail")) else _clamp(float(row.get("score", 0.0))) for row in suite_rows]
        if "mean" in result:
            value = _clamp(float(result.get("mean", 0.0)))
            if int(result.get("hard_failure_count", 0)) > 0:
                value = 0.0
            return [value]
        return []

    if "regression" in samples:
        samples["regression"] = suite_safety(regression_result)
    if "redteam" in samples:
        samples["redteam"] = suite_safety(redteam_result)
    return samples


def dimension_summary(
    final_result: Mapping[str, Any],
    *,
    regression_result: Mapping[str, Any] | None = None,
    redteam_result: Mapping[str, Any] | None = None,
    dimensions: Sequence[str] | None = None,
) -> dict[str, float | None]:
    values = dimension_samples(
        final_result,
        regression_result=regression_result,
        redteam_result=redteam_result,
        dimensions=dimensions,
    )
    return {name: (_mean(samples) if samples else None) for name, samples in values.items()}


def _paired_deltas(candidate: Sequence[float], peer: Sequence[float]) -> list[float]:
    if not candidate or not peer:
        return []
    if len(candidate) == len(peer):
        return [float(a) - float(b) for a, b in zip(candidate, peer)]
    # When group counts differ, use a deterministic Cartesian summary rather than
    # silently truncating. Formal evidence records that the sample units differ.
    return [float(a) - float(b) for a in candidate for b in peer]


def bootstrap_interval(
    deltas: Sequence[float],
    *,
    confidence: float = 0.95,
    iterations: int = 4000,
    seed: int = 42,
) -> tuple[float, float]:
    if not deltas:
        raise ChampionContractError("无法对空差值样本计算置信区间")
    if len(deltas) == 1 or iterations <= 1:
        value = float(deltas[0])
        return value, value
    rng = random.Random(seed)
    values = [float(item) for item in deltas]
    n = len(values)
    means: list[float] = []
    append = means.append
    for _ in range(iterations):
        append(sum(values[rng.randrange(n)] for _ in range(n)) / n)
    means.sort()
    alpha = max(0.0, min(1.0, 1.0 - confidence))
    low_index = max(0, min(iterations - 1, int(math.floor((alpha / 2.0) * (iterations - 1)))))
    high_index = max(0, min(iterations - 1, int(math.ceil((1.0 - alpha / 2.0) * (iterations - 1)))))
    return means[low_index], means[high_index]


def compare_dimension(
    *,
    peer: str,
    dimension: str,
    candidate_samples: Sequence[float],
    peer_samples: Sequence[float],
    minimum_margin: float,
    confidence: float,
    iterations: int,
    seed: int,
) -> PairwiseDimensionResult:
    deltas = _paired_deltas(candidate_samples, peer_samples)
    if not deltas:
        return PairwiseDimensionResult(
            peer=peer,
            dimension=dimension,
            candidate_mean=_mean(candidate_samples),
            peer_mean=_mean(peer_samples),
            observed_delta=float("nan"),
            lower_bound=float("nan"),
            upper_bound=float("nan"),
            minimum_margin=minimum_margin,
            status="MISSING_EVIDENCE",
            sample_count=0,
        )
    observed = _mean(deltas)
    lower, upper = bootstrap_interval(deltas, confidence=confidence, iterations=iterations, seed=seed)
    # Strict first place requires the one-sided evidence floor to clear the
    # configured margin. An overlapping interval is NOT_PROVEN rather than PASS.
    if lower > minimum_margin + 1e-12:
        status = "STRICTLY_FIRST"
    elif (
        candidate_samples
        and peer_samples
        and _mean(candidate_samples) >= 1.0 - 1e-12
        and _mean(peer_samples) >= 1.0 - 1e-12
        and lower >= -minimum_margin - 1e-12
    ):
        # Some bounded safety/reliability metrics saturate at 100%; no system can
        # be numerically above a perfect peer. Joint first place at the ceiling
        # is accepted, while a tie below the ceiling remains NOT_SEPARATED.
        status = "TIED_FIRST_AT_CEILING"
    elif upper < -minimum_margin - 1e-12:
        status = "PEER_BETTER"
    else:
        status = "NOT_SEPARATED"
    return PairwiseDimensionResult(
        peer=peer,
        dimension=dimension,
        candidate_mean=_mean(candidate_samples),
        peer_mean=_mean(peer_samples),
        observed_delta=observed,
        lower_bound=lower,
        upper_bound=upper,
        minimum_margin=minimum_margin,
        status=status,
        sample_count=len(deltas),
    )


def strict_champion_gate(
    *,
    champion_name: str,
    champion_suites: Mapping[str, Mapping[str, Any]],
    peer_suites: Mapping[str, Mapping[str, Mapping[str, Any]]],
    required_peers: Sequence[str],
    dimensions: Sequence[DimensionSpec] | None = None,
    bootstrap_iterations: int = 4000,
    seed: int = 42,
    scope: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    specs = list(dimensions or [DimensionSpec(name=name) for name in MANDATORY_DIMENSIONS])
    invalid_dimensions = [
        spec.name for spec in specs
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,63}", spec.name)
    ]
    if invalid_dimensions:
        raise ChampionContractError(f"冠军维度名称无效：{invalid_dimensions}")
    dimension_names = [spec.name for spec in specs]
    missing_peers = [name for name in required_peers if name not in peer_suites]
    champion_final = champion_suites.get("final")
    if not isinstance(champion_final, Mapping):
        return {
            "schema_version": SCHEMA_VERSION,
            "status": CHAMPION_STATUS_NOT_PROVEN,
            "champion": champion_name,
            "reason": "Prompt Compiler 候选缺少最终测试",
            "missing_peers": missing_peers,
            "universal_claim": False,
        }
    champion_samples = dimension_samples(
        champion_final,
        regression_result=champion_suites.get("regression"),
        redteam_result=champion_suites.get("redteam"),
        dimensions=dimension_names,
    )
    comparisons: dict[str, dict[str, Any]] = {}
    missing_dimensions: list[dict[str, str]] = []
    peer_better: list[dict[str, str]] = []
    not_separated: list[dict[str, str]] = []
    rank_table: dict[str, list[dict[str, Any]]] = {}

    for peer_index, peer_name in enumerate(required_peers):
        suites = peer_suites.get(peer_name)
        if not isinstance(suites, Mapping):
            comparisons[peer_name] = {"status": "MISSING_PEER"}
            continue
        peer_final = suites.get("final")
        if not isinstance(peer_final, Mapping):
            comparisons[peer_name] = {"status": "MISSING_FINAL"}
            missing_peers.append(peer_name)
            continue
        peer_samples = dimension_samples(
            peer_final,
            regression_result=suites.get("regression"),
            redteam_result=suites.get("redteam"),
            dimensions=dimension_names,
        )
        dimension_rows: dict[str, Any] = {}
        for dim_index, spec in enumerate(specs):
            candidate_values = champion_samples.get(spec.name, [])
            peer_values = peer_samples.get(spec.name, [])
            result = compare_dimension(
                peer=peer_name,
                dimension=spec.name,
                candidate_samples=candidate_values,
                peer_samples=peer_values,
                minimum_margin=spec.minimum_margin,
                confidence=spec.confidence,
                iterations=bootstrap_iterations,
                seed=seed + peer_index * 1009 + dim_index * 97,
            )
            row = result.as_dict()
            dimension_rows[spec.name] = row
            if result.status == "MISSING_EVIDENCE" and spec.required:
                missing_dimensions.append({"peer": peer_name, "dimension": spec.name})
            elif result.status == "PEER_BETTER":
                peer_better.append({"peer": peer_name, "dimension": spec.name})
            elif result.status not in {"STRICTLY_FIRST", "TIED_FIRST_AT_CEILING"} and spec.required:
                not_separated.append({"peer": peer_name, "dimension": spec.name})
            rank_table.setdefault(spec.name, []).extend(
                [
                    {"name": champion_name, "score": result.candidate_mean},
                    {"name": peer_name, "score": result.peer_mean},
                ]
            )
        comparisons[peer_name] = {"status": "COMPARED", "dimensions": dimension_rows}

    # De-duplicate rank rows, then establish observed ranking independently of
    # statistical separation. This supports a human-readable arena table.
    ranks: dict[str, list[dict[str, Any]]] = {}
    for dimension, rows in rank_table.items():
        best_by_name: dict[str, float] = {}
        for row in rows:
            name = str(row["name"])
            score = float(row["score"])
            best_by_name[name] = max(score, best_by_name.get(name, -math.inf))
        ordered = sorted(best_by_name.items(), key=lambda item: (-item[1], item[0]))
        ranks[dimension] = [
            {"rank": index + 1, "name": name, "score": score}
            for index, (name, score) in enumerate(ordered)
        ]

    if missing_peers or missing_dimensions:
        status = CHAMPION_STATUS_NOT_PROVEN
        reason = "必选竞品或必选维度证据不完整"
    elif peer_better:
        status = CHAMPION_STATUS_REJECTED
        reason = "至少一个竞品在必选维度上具有可分离优势"
    elif not_separated:
        status = CHAMPION_STATUS_NOT_PROVEN
        reason = "至少一个必选维度尚未统计分离，不能宣称严格第一"
    elif required_peers:
        status = CHAMPION_STATUS_PASS
        reason = "Prompt Compiler 在每个冻结必选维度上均对每个必选竞品形成统计可分离优势"
    else:
        status = CHAMPION_STATUS_NOT_PROVEN
        reason = "没有必选竞品，无法形成冠军证据"

    return {
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "champion": champion_name,
        "reason": reason,
        "scope": dict(scope or {}),
        "required_peers": list(required_peers),
        "missing_peers": sorted(set(missing_peers)),
        "required_dimensions": [spec.name for spec in specs if spec.required],
        "dimension_labels_zh": {name: DIMENSION_LABELS_ZH.get(name, name) for name in dimension_names},
        "champion_summary": dimension_summary(
            champion_final,
            regression_result=champion_suites.get("regression"),
            redteam_result=champion_suites.get("redteam"),
            dimensions=dimension_names,
        ),
        "comparisons": comparisons,
        "observed_ranks": ranks,
        "missing_dimensions": missing_dimensions,
        "peer_better": peer_better,
        "not_statistically_separated": not_separated,
        "strict_all_dimensions": True,
        "ceiling_tie_policy": "Only a 100%-vs-100% tie may count as joint first; ties below the ceiling never pass.",
        "universal_claim": False,
        "release_allowed": status == CHAMPION_STATUS_PASS,
    }


def _normalized_weights(values: Mapping[str, float]) -> dict[str, float]:
    positive = {key: max(0.0, float(value)) for key, value in values.items()}
    total = sum(positive.values())
    if total <= 0:
        return {key: 1.0 / max(1, len(positive)) for key in positive}
    return {key: value / total for key, value in positive.items()}


def adaptive_budget_plan(
    *,
    total_budget: int,
    arms: Sequence[str],
    minimum_probe: int,
    dimension_gaps: Mapping[str, float] | None = None,
    task_profile: Mapping[str, float] | None = None,
    synthesis_share: float = 0.24,
) -> BudgetPlan:
    """Allocate one conserved total budget; never multiply it per engine.

    Every required arm receives a probe. Remaining units are assigned by the
    current weakest-dimension gaps, task topology, and each arm's capability
    prior. The Prompt Compiler synthesis arm receives an explicit portfolio
    budget rather than an unbounded extra pass.
    """
    unique_arms = list(dict.fromkeys(str(arm) for arm in arms if str(arm)))
    if not unique_arms:
        raise ChampionContractError("预算计划至少需要一个执行器")
    if "prompt_compiler" not in unique_arms:
        unique_arms.append("prompt_compiler")
    total_budget = int(total_budget)
    minimum_probe = int(minimum_probe)
    if total_budget < minimum_probe * len(unique_arms):
        raise ChampionContractError(
            f"总预算 {total_budget} 小于 {len(unique_arms)} 个执行器的最低探测预算 {minimum_probe}"
        )
    allocations = {arm: minimum_probe for arm in unique_arms}
    remaining = total_budget - sum(allocations.values())
    gaps = {name: max(0.0, float(value)) for name, value in (dimension_gaps or {}).items() if name in MANDATORY_DIMENSIONS}
    if not gaps:
        gaps = {name: 1.0 for name in MANDATORY_DIMENSIONS}
    profile = {name: max(0.0, float(value)) for name, value in (task_profile or {}).items() if name in MANDATORY_DIMENSIONS}
    if not profile:
        profile = {name: 1.0 for name in MANDATORY_DIMENSIONS}

    raw_scores: dict[str, float] = {}
    for arm in unique_arms:
        priors = CAPABILITY_PRIORS.get(arm, {})
        score = 0.0
        for dimension in MANDATORY_DIMENSIONS:
            gap = gaps.get(dimension, 0.25)
            need = profile.get(dimension, 1.0)
            capability = priors.get(dimension, 0.92 if arm != "prompt_compiler" else 1.0)
            score += (0.05 + gap) * need * capability
        if arm == "prompt_compiler":
            score *= max(0.01, synthesis_share * len(unique_arms))
        raw_scores[arm] = score
    weights = _normalized_weights(raw_scores)

    # Largest-remainder apportionment conserves every unit deterministically.
    exact = {arm: remaining * weights[arm] for arm in unique_arms}
    floors = {arm: int(math.floor(value)) for arm, value in exact.items()}
    for arm, value in floors.items():
        allocations[arm] += value
    leftover = total_budget - sum(allocations.values())
    order = sorted(unique_arms, key=lambda arm: (-(exact[arm] - floors[arm]), arm))
    for arm in order[:leftover]:
        allocations[arm] += 1

    plan = BudgetPlan(
        total_budget=total_budget,
        minimum_probe=minimum_probe,
        allocations=allocations,
        rationale={
            "strategy": "minimum-probe + weakest-dimension-gap + capability-prior + largest-remainder",
            "dimension_gaps": gaps,
            "task_profile": profile,
            "raw_scores": raw_scores,
            "normalized_weights": weights,
            "synthesis_share": synthesis_share,
        },
    )
    plan.verify()
    return plan


def dimension_gap_from_summaries(
    champion: Mapping[str, float | None],
    peers: Mapping[str, Mapping[str, float | None]],
) -> dict[str, float]:
    """Return the maximum observed deficit to any peer per dimension."""
    gaps: dict[str, float] = {}
    for dimension in MANDATORY_DIMENSIONS:
        own = champion.get(dimension)
        peer_values = [summary.get(dimension) for summary in peers.values()]
        numeric = [float(value) for value in peer_values if value is not None]
        if own is None or not numeric:
            gaps[dimension] = 1.0
        else:
            gaps[dimension] = max(0.0, max(numeric) - float(own))
    return gaps


def robust_candidate_key(summary: Mapping[str, float | None], *, length: int = 0) -> tuple[Any, ...]:
    """Lexicographic key that prevents aggregate-score masking.

    Hard safety and the worst mandatory dimension dominate the mean. This is
    used for candidate selection before the blind final set is opened.
    """
    values = [float(value) for value in summary.values() if value is not None]
    floor = min(values) if values else -1.0
    hard = float(summary.get("hard_safety") or 0.0)
    weakest = float(summary.get("weakest_slice") or 0.0)
    overall = float(summary.get("overall") or 0.0)
    stability = float(summary.get("stability") or 0.0)
    return (hard, floor, weakest, overall, stability, -length)


def observed_dimension_leaders(summaries: Mapping[str, Mapping[str, float | None]]) -> dict[str, list[str]]:
    leaders: dict[str, list[str]] = {}
    for dimension in MANDATORY_DIMENSIONS:
        values = {
            name: float(summary[dimension])
            for name, summary in summaries.items()
            if summary.get(dimension) is not None
        }
        if not values:
            leaders[dimension] = []
            continue
        top = max(values.values())
        leaders[dimension] = sorted(name for name, value in values.items() if abs(value - top) <= 1e-12)
    return leaders


def verify_competitor_registry(registry: Mapping[str, Any]) -> dict[str, Any]:
    competitors = registry.get("competitors")
    errors: list[str] = []
    if not isinstance(competitors, list) or not competitors:
        errors.append("competitors 必须是非空数组")
        competitors = []
    seen: set[str] = set()
    required: list[str] = []
    for index, item in enumerate(competitors):
        if not isinstance(item, Mapping):
            errors.append(f"competitors[{index}] 不是对象")
            continue
        name = str(item.get("name", "")).strip()
        if not name:
            errors.append(f"competitors[{index}] 缺少 name")
            continue
        if name in seen:
            errors.append(f"竞品名称重复：{name}")
        seen.add(name)
        roles = item.get("roles")
        if not isinstance(roles, list) or not {"same_layer_competitor", "routable_executor"}.issubset(set(roles)):
            errors.append(f"{name} 必须同时声明同层竞品和可路由执行器角色")
        if bool(item.get("required")):
            required.append(name)
    return {
        "status": "PASS" if not errors else "BLOCKED",
        "errors": errors,
        "competitor_count": len(seen),
        "required_competitors": required,
        "dual_role_complete": not errors,
    }


def self_test() -> dict[str, Any]:
    # Strictly stronger synthetic champion.
    def suite(value: float, *, elapsed: float = 0.05, chars: int = 100) -> dict[str, Any]:
        rows = []
        for index in range(6):
            rows.append(
                {
                    "case_id": f"c{index}",
                    "task_id": f"t{index % 2}",
                    "score": value,
                    "hard_fail": False,
                    "dimensions": {
                        "correctness": value,
                        "coverage": value,
                        "executability": value,
                        "security": value,
                        "efficiency": value,
                        "oracle": value,
                    },
                    "elapsed_seconds": elapsed,
                    "candidate_chars": chars,
                    "output_chars": chars,
                }
            )
        return {
            "mean": value,
            "worst": value,
            "variance": 0.0,
            "hard_failure_count": 0,
            "per_task": {"t0": value, "t1": value},
            "results": rows,
        }

    champion = {"final": suite(0.95, elapsed=0.01, chars=80), "regression": suite(0.95), "redteam": suite(0.95)}
    peers = {
        name: {"final": suite(0.70), "regression": suite(0.70), "redteam": suite(0.70)}
        for name in ("gepa", "autoresearch", "meta_harness", "promptfoo")
    }
    gate = strict_champion_gate(
        champion_name="prompt_compiler",
        champion_suites=champion,
        peer_suites=peers,
        required_peers=list(peers),
        bootstrap_iterations=200,
    )
    plan = adaptive_budget_plan(
        total_budget=100,
        arms=list(peers),
        minimum_probe=5,
        dimension_gaps={"redteam": 0.4, "stability": 0.2},
    )
    return {
        "status": "PASS" if gate["status"] == CHAMPION_STATUS_PASS and sum(plan.allocations.values()) == 100 else "BLOCKED",
        "champion_gate": gate["status"],
        "budget": plan.as_dict(),
    }


if __name__ == "__main__":
    print(json.dumps(self_test(), ensure_ascii=False, indent=2, sort_keys=True))
