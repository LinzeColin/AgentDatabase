from __future__ import annotations

import random
from collections import defaultdict
from statistics import mean
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import ValidationError, object_sha256, utc_now

REQUIRED_FIELDS = {"cluster_id", "task_id", "trial_id", "arm_id", "success", "score", "cost_usd", "latency_ms"}


def _avg(values: Sequence[float]) -> float | None:
    return mean(values) if values else None


def _cluster_arm_means(rows: Iterable[Mapping[str, Any]]) -> Dict[Tuple[str, str], Dict[str, float]]:
    bucket: Dict[Tuple[str, str], Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
    seen_trials = set()
    for index, row in enumerate(rows):
        missing = REQUIRED_FIELDS - set(row)
        if missing:
            raise ValidationError(f"cluster row[{index}] 缺少 {sorted(missing)}")
        identity = (str(row["cluster_id"]), str(row["task_id"]), str(row["trial_id"]), str(row["arm_id"]))
        if identity in seen_trials:
            raise ValidationError(f"重复 trial identity: {identity}")
        seen_trials.add(identity)
        key = (str(row["cluster_id"]), str(row["arm_id"]))
        bucket[key]["success"].append(1.0 if bool(row["success"]) else 0.0)
        bucket[key]["score"].append(float(row["score"]))
        bucket[key]["cost_usd"].append(float(row["cost_usd"]))
        bucket[key]["latency_ms"].append(float(row["latency_ms"]))
    return {
        key: {metric: mean(values) for metric, values in metrics.items()}
        for key, metrics in bucket.items()
    }


def _percentile(sorted_values: Sequence[float], percentile: float) -> float | None:
    if not sorted_values:
        return None
    position = (len(sorted_values) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def _cluster_bootstrap(deltas: Sequence[float], seed: int, samples: int) -> Dict[str, Any]:
    if not deltas:
        return {"n_clusters": 0, "mean": None, "low": None, "high": None}
    rng = random.Random(seed)
    simulated = []
    size = len(deltas)
    for _ in range(samples):
        simulated.append(mean(deltas[rng.randrange(size)] for _ in range(size)))
    simulated.sort()
    return {
        "n_clusters": size,
        "mean": mean(deltas),
        "low": _percentile(simulated, 0.025),
        "high": _percentile(simulated, 0.975),
    }


def aggregate_cluster_effects(
    rows: Iterable[Mapping[str, Any]],
    candidate_arm: str,
    comparator_arm: str,
    seed: int = 20260729,
    bootstrap_samples: int = 2000,
) -> Dict[str, Any]:
    values = _cluster_arm_means(rows)
    clusters = sorted({cluster for cluster, _arm in values})
    paired = [cluster for cluster in clusters if (cluster, candidate_arm) in values and (cluster, comparator_arm) in values]
    metrics: Dict[str, Any] = {}
    for offset, metric in enumerate(("success", "score", "cost_usd", "latency_ms")):
        deltas = [values[(cluster, candidate_arm)][metric] - values[(cluster, comparator_arm)][metric] for cluster in paired]
        metrics[f"{metric}_delta"] = _cluster_bootstrap(deltas, seed + offset, bootstrap_samples)
    utilities = []
    for cluster in paired:
        cand = values[(cluster, candidate_arm)]
        comp = values[(cluster, comparator_arm)]
        cand_utility = cand["score"] / max(cand["cost_usd"], 1e-9)
        comp_utility = comp["score"] / max(comp["cost_usd"], 1e-9)
        utilities.append(cand_utility - comp_utility)
    metrics["score_per_usd_delta"] = _cluster_bootstrap(utilities, seed + 10, bootstrap_samples)
    result: Dict[str, Any] = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "candidate_arm": candidate_arm,
        "comparator_arm": comparator_arm,
        "paired_clusters": len(paired),
        "unit_of_inference": "cluster",
        "repeated_trials_aggregated_before_inference": True,
        "metrics": metrics,
        "result_digest": None,
    }
    result["result_digest"] = object_sha256({k: v for k, v in result.items() if k != "result_digest"})
    return result
