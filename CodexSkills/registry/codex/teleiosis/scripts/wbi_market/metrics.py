from __future__ import annotations

import json
import math
import random
import sqlite3
import statistics
import tempfile
from collections import Counter
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import ValidationError, object_sha256, percentage_change, strip_internal_fields, utc_now
from .specs import assert_valid, validate_experiment_spec, validate_feedback, validate_result

# 结果标签本身不能证明真实市场事件。只有绑定真实运行、用户同意与外部证据的
# feedback adapter 记录才能把证据提升到 L5–L7。
LEVEL_BY_RESULT_KIND = {
    "static": 0,
    "offline": 1,
    "simulation": 2,
    "stress": 3,
    "shadow": 4,
    "canary": 4,
    "external_acceptance": 4,
    "economic": 4,
    "retention": 4,
    "incident": 4,
}
LEVEL_BY_FEEDBACK_SOURCE = {
    "opt_in_user": 5,
    "blind_canary": 5,
    "external_acceptor": 6,
    "micro_bounty": 6,
    "production_behavior": 7,
    "retention_observation": 7,
    "payment_observation": 7,
    "incident_report": 7,
}
LEVEL_LABELS = {
    0: "L0_STATIC",
    1: "L1_OFFLINE_CONTROL",
    2: "L2_SIMULATION",
    3: "L3_STRESS",
    4: "L4_SHADOW_REPLAY",
    5: "L5_REAL_USER_CANARY",
    6: "L6_EXTERNAL_ECONOMIC_ACCEPTANCE",
    7: "L7_RETENTION_AND_REALIZED_VALUE",
}
TARGET_MIN_LEVEL = {"lab": 1, "market_partial": 5, "market_validated": 6}


def _mean(values: Sequence[float]) -> float | None:
    return statistics.fmean(values) if values else None


def _bootstrap_ci(
    values: Sequence[float],
    seed: int,
    confidence: float = 0.95,
    iterations: int = 400,
) -> Dict[str, Any]:
    if not values:
        return {
            "n": 0,
            "mean": None,
            "low": None,
            "high": None,
            "method": "paired-percentile-bootstrap",
        }
    sample = list(values)
    # 有界内存和计算：大规模数据通过确定性 reservoir 采样估计区间，均值仍用全量。
    if len(sample) > 5000:
        rng = random.Random(seed)
        reservoir = sample[:5000]
        for index, value in enumerate(sample[5000:], 5000):
            replacement = rng.randint(0, index)
            if replacement < 5000:
                reservoir[replacement] = value
        sample = reservoir
    rng = random.Random(seed)
    n = len(sample)
    means: List[float] = []
    for _ in range(iterations):
        total = 0.0
        for _index in range(n):
            total += sample[rng.randrange(n)]
        means.append(total / n)
    means.sort()
    alpha = (1.0 - confidence) / 2.0
    low_index = max(0, min(len(means) - 1, int(math.floor(alpha * len(means)))))
    high_index = max(0, min(len(means) - 1, int(math.ceil((1.0 - alpha) * len(means))) - 1))
    return {
        "n": len(values),
        "sampled_n": n,
        "mean": _mean(values),
        "low": means[low_index],
        "high": means[high_index],
        "confidence": confidence,
        "iterations": iterations,
        "method": "paired-percentile-bootstrap",
    }


def _normalize_nullable_number(value: Any) -> float | None:
    if value is None:
        return None
    return float(value)


def _arm_maps(spec: Mapping[str, Any]) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, str]]:
    by_id = {str(arm["id"]): dict(arm) for arm in spec["arms"]}
    by_kind = {
        str(arm["kind"]): str(arm["id"])
        for arm in spec["arms"]
        if arm["kind"] != "competitor"
    }
    return by_id, by_kind


def _create_db() -> Tuple[sqlite3.Connection, str]:
    temporary = tempfile.NamedTemporaryFile(prefix="teleiosis-market-", suffix=".sqlite3", delete=False)
    temporary.close()
    connection = sqlite3.connect(temporary.name)
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=NORMAL")
    connection.executescript(
        """
        CREATE TABLE results (
            run_id TEXT NOT NULL UNIQUE,
            task_id TEXT NOT NULL,
            partition_name TEXT NOT NULL,
            arm_id TEXT NOT NULL,
            repetition INTEGER NOT NULL,
            status TEXT NOT NULL,
            success INTEGER NOT NULL,
            score REAL NOT NULL,
            accepted INTEGER,
            cost_usd REAL,
            tokens REAL,
            latency_ms REAL,
            tool_calls REAL,
            human_edit_seconds REAL,
            evidence_kind TEXT NOT NULL,
            protected INTEGER NOT NULL,
            hard_failures TEXT NOT NULL,
            artifact_digest TEXT,
            trace_digest TEXT,
            stress_category TEXT,
            PRIMARY KEY (task_id, arm_id, repetition)
        );
        CREATE INDEX idx_results_arm ON results(arm_id);
        CREATE INDEX idx_results_pair ON results(task_id, repetition);
        CREATE INDEX idx_results_partition ON results(partition_name, arm_id);

        CREATE TABLE feedback (
            event_id TEXT PRIMARY KEY,
            run_id TEXT NOT NULL,
            task_id TEXT NOT NULL,
            arm_id TEXT NOT NULL,
            artifact_digest TEXT,
            source TEXT NOT NULL,
            evidence_level INTEGER NOT NULL,
            completion TEXT NOT NULL,
            accepted INTEGER,
            would_reuse INTEGER,
            human_edit_seconds REAL,
            time_saved_minutes REAL,
            paid_value_usd REAL,
            incident_severity TEXT NOT NULL,
            consent_ref TEXT NOT NULL,
            assignment_id TEXT,
            randomized INTEGER,
            acceptance_ref TEXT
        );
        CREATE INDEX idx_feedback_arm ON feedback(arm_id);
        CREATE INDEX idx_feedback_pair ON feedback(task_id, arm_id);
        CREATE INDEX idx_feedback_source ON feedback(source, arm_id);
        """
    )
    return connection, temporary.name


def _insert_results(
    connection: sqlite3.Connection,
    spec: Mapping[str, Any],
    rows: Iterable[Mapping[str, Any]],
) -> Dict[str, Any]:
    arm_by_id, _ = _arm_maps(spec)
    arm_ids = list(arm_by_id)
    counts: Counter[str] = Counter()
    hard_failures: Counter[str] = Counter()
    identity_mismatches = 0
    max_evidence_level = 0
    batch: List[Tuple[Any, ...]] = []

    for raw in rows:
        record = strip_internal_fields(raw)
        assert_valid(validate_result(record, arm_ids), f"结果 {record.get('run_id', '<unknown>')}")
        if record["experiment_id"] != spec["experiment_id"]:
            raise ValidationError(
                f"结果 experiment_id 不匹配: {record['experiment_id']} != {spec['experiment_id']}"
            )
        arm = arm_by_id[str(record["arm_id"])]
        expected_digest = arm.get("artifact_digest")
        actual_digest = record.get("artifact_digest")
        if arm["kind"] == "no_skill":
            digest_matches = actual_digest is None
        else:
            digest_matches = expected_digest == actual_digest
        if not digest_matches:
            identity_mismatches += 1
            record.setdefault("hard_failures", []).append("identity_mismatch")

        hard = list(dict.fromkeys(record.get("hard_failures", [])))
        hard_failures.update(hard)
        counts[str(record["status"])] += 1
        max_evidence_level = max(max_evidence_level, LEVEL_BY_RESULT_KIND[record["evidence_kind"]])

        metadata = record.get("metadata") or {}
        stress_category = None
        if isinstance(metadata, dict):
            stress = metadata.get("stress")
            if isinstance(stress, dict):
                stress_category = stress.get("category")
            if stress_category is None:
                stress_category = metadata.get("stress_category")

        outcome = record["outcome"]
        usage = record["usage"]
        batch.append(
            (
                record["run_id"],
                record["task_id"],
                record["partition"],
                record["arm_id"],
                int(record["repetition"]),
                record["status"],
                int(bool(outcome["success"])),
                float(outcome["score"]),
                None if outcome.get("accepted") is None else int(bool(outcome.get("accepted"))),
                _normalize_nullable_number(usage.get("cost_usd")),
                _normalize_nullable_number(usage.get("tokens")),
                _normalize_nullable_number(usage.get("latency_ms")),
                _normalize_nullable_number(usage.get("tool_calls")),
                _normalize_nullable_number(outcome.get("human_edit_seconds")),
                record["evidence_kind"],
                int(bool(record.get("protected", False))),
                json.dumps(hard, ensure_ascii=False, sort_keys=True),
                actual_digest,
                record.get("trace_digest"),
                stress_category,
            )
        )
        if len(batch) >= 1000:
            try:
                connection.executemany(
                    "INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    batch,
                )
            except sqlite3.IntegrityError as exc:
                raise ValidationError(f"结果存在重复 run_id 或 task_id/arm/repetition: {exc}") from exc
            batch.clear()

    if batch:
        try:
            connection.executemany(
                "INSERT INTO results VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                batch,
            )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"结果存在重复 run_id 或 task_id/arm/repetition: {exc}") from exc
    connection.commit()
    return {
        "result_status_counts": dict(counts),
        "hard_failure_counts": dict(hard_failures),
        "result_identity_mismatch_count": identity_mismatches,
        "max_result_evidence_level": max_evidence_level,
    }


def _insert_feedback(
    connection: sqlite3.Connection,
    spec: Mapping[str, Any],
    rows: Iterable[Mapping[str, Any]] | None,
) -> Dict[str, Any]:
    empty = {
        "event_count": 0,
        "source_counts": {},
        "source_counts_by_arm": {},
        "max_feedback_evidence_level": 0,
        "max_feedback_level_by_arm": {},
        "critical_or_high_incidents_total": 0,
        "critical_or_high_incidents_by_arm": {},
        "feedback_identity_mismatch_count": 0,
        "feedback_orphan_run_count": 0,
        "simulated_competitor_market_claim_count": 0,
        "hard_failure_counts": {},
    }
    if rows is None:
        return empty

    arm_by_id, _ = _arm_maps(spec)
    arm_ids = list(arm_by_id)
    source_counts: Counter[str] = Counter()
    source_counts_by_arm: Dict[str, Counter[str]] = {arm_id: Counter() for arm_id in arm_ids}
    max_level_by_arm: Dict[str, int] = {arm_id: 0 for arm_id in arm_ids}
    incidents_by_arm: Counter[str] = Counter()
    hard_failures: Counter[str] = Counter()
    identity_mismatches = 0
    orphan_runs = 0
    simulated_market_claims = 0
    batch: List[Tuple[Any, ...]] = []

    for raw in rows:
        record = strip_internal_fields(raw)
        assert_valid(validate_feedback(record, arm_ids), f"反馈 {record.get('event_id', '<unknown>')}")
        if record["experiment_id"] != spec["experiment_id"]:
            raise ValidationError(
                f"反馈 experiment_id 不匹配: {record['experiment_id']} != {spec['experiment_id']}"
            )

        arm_id = str(record["arm_id"])
        arm = arm_by_id[arm_id]
        expected_digest = arm.get("artifact_digest")
        actual_digest = record.get("artifact_digest")
        digest_matches = actual_digest is None if arm["kind"] == "no_skill" else actual_digest == expected_digest
        if not digest_matches:
            identity_mismatches += 1
            hard_failures["feedback_identity_mismatch"] += 1

        run_row = connection.execute(
            "SELECT artifact_digest FROM results WHERE run_id=? AND task_id=? AND arm_id=?",
            (record["run_id"], record["task_id"], arm_id),
        ).fetchone()
        if run_row is None:
            orphan_runs += 1
            hard_failures["feedback_orphan_run"] += 1
        elif run_row[0] != actual_digest:
            identity_mismatches += 1
            hard_failures["feedback_identity_mismatch"] += 1

        if arm["kind"] == "competitor" and arm.get("competitor_evidence_type") != "real":
            simulated_market_claims += 1
            hard_failures["simulated_competitor_market_claim"] += 1

        source = str(record["source"])
        level = LEVEL_BY_FEEDBACK_SOURCE[source]
        source_counts[source] += 1
        source_counts_by_arm[arm_id][source] += 1
        max_level_by_arm[arm_id] = max(max_level_by_arm[arm_id], level)
        severity = str(record["incident_severity"])
        if severity in {"high", "critical"}:
            incidents_by_arm[arm_id] += 1

        batch.append(
            (
                record["event_id"],
                record["run_id"],
                record["task_id"],
                arm_id,
                actual_digest,
                source,
                level,
                record["completion"],
                None if record.get("accepted") is None else int(bool(record.get("accepted"))),
                None if record.get("would_reuse") is None else int(bool(record.get("would_reuse"))),
                _normalize_nullable_number(record.get("human_edit_seconds")),
                _normalize_nullable_number(record.get("time_saved_minutes")),
                _normalize_nullable_number(record.get("paid_value_usd")),
                severity,
                record["consent_ref"],
                record.get("assignment_id"),
                None if record.get("randomized") is None else int(bool(record.get("randomized"))),
                record.get("acceptance_ref"),
            )
        )
        if len(batch) >= 1000:
            try:
                connection.executemany(
                    "INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                    batch,
                )
            except sqlite3.IntegrityError as exc:
                raise ValidationError(f"反馈 event_id 重复: {exc}") from exc
            batch.clear()

    if batch:
        try:
            connection.executemany(
                "INSERT INTO feedback VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                batch,
            )
        except sqlite3.IntegrityError as exc:
            raise ValidationError(f"反馈 event_id 重复: {exc}") from exc
    connection.commit()

    event_count = int(connection.execute("SELECT COUNT(*) FROM feedback").fetchone()[0])
    max_level = max(max_level_by_arm.values(), default=0)
    return {
        "event_count": event_count,
        "source_counts": dict(source_counts),
        "source_counts_by_arm": {
            arm_id: dict(counts) for arm_id, counts in source_counts_by_arm.items() if counts
        },
        "max_feedback_evidence_level": max_level,
        "max_feedback_level_by_arm": {
            arm_id: level for arm_id, level in max_level_by_arm.items() if level > 0
        },
        "critical_or_high_incidents_total": int(sum(incidents_by_arm.values())),
        "critical_or_high_incidents_by_arm": dict(incidents_by_arm),
        "feedback_identity_mismatch_count": identity_mismatches,
        "feedback_orphan_run_count": orphan_runs,
        "simulated_competitor_market_claim_count": simulated_market_claims,
        "hard_failure_counts": dict(hard_failures),
    }


def _arm_summary(connection: sqlite3.Connection, arm_id: str, arm: Mapping[str, Any]) -> Dict[str, Any]:
    row = connection.execute(
        """
        SELECT COUNT(*), SUM(success), AVG(score), AVG(accepted), AVG(cost_usd), AVG(tokens),
               AVG(latency_ms), AVG(tool_calls), AVG(human_edit_seconds),
               SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)
        FROM results WHERE arm_id=?
        """,
        (arm_id,),
    ).fetchone()
    return {
        "id": arm_id,
        "kind": arm["kind"],
        "label": arm["label"],
        "competitor_evidence_type": arm.get("competitor_evidence_type"),
        "records": int(row[0] or 0),
        "success_rate": None if not row[0] else float(row[1] or 0) / float(row[0]),
        "mean_score": row[2],
        "acceptance_rate": row[3],
        "mean_cost_usd": row[4],
        "mean_tokens": row[5],
        "mean_latency_ms": row[6],
        "mean_tool_calls": row[7],
        "mean_human_edit_seconds": row[8],
        "completed_records": int(row[9] or 0),
    }


def _pair_values(
    connection: sqlite3.Connection,
    candidate_id: str,
    comparator_id: str,
    protected_only: bool = False,
) -> Dict[str, List[float]]:
    clause = "AND c.protected=1 AND b.protected=1" if protected_only else ""
    query = f"""
        SELECT c.success-b.success,
               c.score-b.score,
               CASE WHEN c.accepted IS NULL OR b.accepted IS NULL THEN NULL ELSE c.accepted-b.accepted END,
               CASE WHEN c.cost_usd IS NULL OR b.cost_usd IS NULL THEN NULL ELSE c.cost_usd-b.cost_usd END,
               CASE WHEN c.latency_ms IS NULL OR b.latency_ms IS NULL THEN NULL ELSE c.latency_ms-b.latency_ms END,
               CASE WHEN c.tokens IS NULL OR b.tokens IS NULL THEN NULL ELSE c.tokens-b.tokens END
        FROM results c
        JOIN results b ON c.task_id=b.task_id AND c.repetition=b.repetition
        WHERE c.arm_id=? AND b.arm_id=? {clause}
    """
    values: Dict[str, List[float]] = {
        "success": [],
        "score": [],
        "acceptance": [],
        "cost": [],
        "latency": [],
        "tokens": [],
    }
    for row in connection.execute(query, (candidate_id, comparator_id)):
        values["success"].append(float(row[0]))
        values["score"].append(float(row[1]))
        if row[2] is not None:
            values["acceptance"].append(float(row[2]))
        if row[3] is not None:
            values["cost"].append(float(row[3]))
        if row[4] is not None:
            values["latency"].append(float(row[4]))
        if row[5] is not None:
            values["tokens"].append(float(row[5]))
    return values


def _pair_summary(
    connection: sqlite3.Connection,
    spec: Mapping[str, Any],
    candidate_id: str,
    comparator_id: str,
) -> Dict[str, Any]:
    values = _pair_values(connection, candidate_id, comparator_id)
    protected = _pair_values(connection, candidate_id, comparator_id, protected_only=True)
    seed = int(spec["seed"])
    candidate_arm = next(arm for arm in spec["arms"] if arm["id"] == candidate_id)
    comparator_arm = next(arm for arm in spec["arms"] if arm["id"] == comparator_id)
    candidate_summary = _arm_summary(connection, candidate_id, candidate_arm)
    comparator_summary = _arm_summary(connection, comparator_id, comparator_arm)
    return {
        "candidate_id": candidate_id,
        "comparator_id": comparator_id,
        "comparator_kind": comparator_arm["kind"],
        "paired_tasks": len(values["success"]),
        "success_delta": _bootstrap_ci(values["success"], seed + 11),
        "score_delta": _bootstrap_ci(values["score"], seed + 13),
        "acceptance_delta": _bootstrap_ci(values["acceptance"], seed + 17),
        "cost_delta_usd": _bootstrap_ci(values["cost"], seed + 19),
        "latency_delta_ms": _bootstrap_ci(values["latency"], seed + 23),
        "token_delta": _bootstrap_ci(values["tokens"], seed + 29),
        "protected_success_delta": _bootstrap_ci(protected["success"], seed + 31),
        "candidate_mean_cost_usd": candidate_summary["mean_cost_usd"],
        "comparator_mean_cost_usd": comparator_summary["mean_cost_usd"],
        "cost_increase_ratio": percentage_change(
            candidate_summary["mean_cost_usd"], comparator_summary["mean_cost_usd"]
        ),
        "candidate_mean_latency_ms": candidate_summary["mean_latency_ms"],
        "comparator_mean_latency_ms": comparator_summary["mean_latency_ms"],
        "latency_increase_ratio": percentage_change(
            candidate_summary["mean_latency_ms"], comparator_summary["mean_latency_ms"]
        ),
    }


def _slice_summaries(connection: sqlite3.Connection, candidate_id: str) -> Dict[str, List[Dict[str, Any]]]:
    result: Dict[str, List[Dict[str, Any]]] = {"partition": [], "stress_category": []}
    for field, key in (("partition_name", "partition"), ("stress_category", "stress_category")):
        rows = connection.execute(
            f"""
            SELECT {field}, COUNT(*), AVG(success), AVG(score), AVG(cost_usd), AVG(latency_ms)
            FROM results
            WHERE arm_id=? AND {field} IS NOT NULL
            GROUP BY {field}
            ORDER BY AVG(success) ASC, AVG(score) ASC
            """,
            (candidate_id,),
        ).fetchall()
        for row in rows:
            result[key].append(
                {
                    key: row[0],
                    "records": int(row[1]),
                    "success_rate": row[2],
                    "mean_score": row[3],
                    "mean_cost_usd": row[4],
                    "mean_latency_ms": row[5],
                }
            )
    return result


def _market_arm_summary(connection: sqlite3.Connection, arm_id: str) -> Dict[str, Any]:
    row = connection.execute(
        """
        SELECT COUNT(*),
               AVG(CASE WHEN completion='complete' THEN 1.0 ELSE 0.0 END),
               AVG(accepted), AVG(would_reuse), AVG(human_edit_seconds), AVG(time_saved_minutes),
               SUM(paid_value_usd), MAX(evidence_level),
               SUM(CASE WHEN incident_severity IN ('high','critical') THEN 1 ELSE 0 END)
        FROM feedback WHERE arm_id=?
        """,
        (arm_id,),
    ).fetchone()
    sources = {
        source: int(count)
        for source, count in connection.execute(
            "SELECT source, COUNT(*) FROM feedback WHERE arm_id=? GROUP BY source ORDER BY source",
            (arm_id,),
        )
    }
    level = int(row[7] or 0)
    return {
        "arm_id": arm_id,
        "event_count": int(row[0] or 0),
        "completion_rate": row[1],
        "acceptance_rate": row[2],
        "reuse_intent_rate": row[3],
        "mean_human_edit_seconds": row[4],
        "mean_time_saved_minutes": row[5],
        "total_paid_value_usd": float(row[6] or 0.0),
        "max_evidence_level": level,
        "max_evidence_label": LEVEL_LABELS[level],
        "critical_or_high_incidents": int(row[8] or 0),
        "source_counts": sources,
    }


def _market_pair_values(
    connection: sqlite3.Connection,
    candidate_id: str,
    comparator_id: str,
) -> Dict[str, List[float]]:
    # 先按 task 聚合，避免同一任务多次反馈伪装为独立样本。
    query = """
        WITH task_arm AS (
            SELECT task_id, arm_id,
                   AVG(CASE WHEN completion='complete' THEN 1.0 ELSE 0.0 END) AS completion_rate,
                   AVG(accepted) AS acceptance_rate,
                   AVG(would_reuse) AS reuse_rate,
                   AVG(human_edit_seconds) AS edit_seconds,
                   AVG(time_saved_minutes) AS time_saved
            FROM feedback
            GROUP BY task_id, arm_id
        )
        SELECT c.completion_rate-b.completion_rate,
               CASE WHEN c.acceptance_rate IS NULL OR b.acceptance_rate IS NULL THEN NULL
                    ELSE c.acceptance_rate-b.acceptance_rate END,
               CASE WHEN c.reuse_rate IS NULL OR b.reuse_rate IS NULL THEN NULL
                    ELSE c.reuse_rate-b.reuse_rate END,
               CASE WHEN c.edit_seconds IS NULL OR b.edit_seconds IS NULL THEN NULL
                    ELSE c.edit_seconds-b.edit_seconds END,
               CASE WHEN c.time_saved IS NULL OR b.time_saved IS NULL THEN NULL
                    ELSE c.time_saved-b.time_saved END
        FROM task_arm c
        JOIN task_arm b ON c.task_id=b.task_id
        WHERE c.arm_id=? AND b.arm_id=?
    """
    values: Dict[str, List[float]] = {
        "completion": [],
        "acceptance": [],
        "reuse": [],
        "edit": [],
        "time_saved": [],
    }
    for row in connection.execute(query, (candidate_id, comparator_id)):
        values["completion"].append(float(row[0]))
        if row[1] is not None:
            values["acceptance"].append(float(row[1]))
        if row[2] is not None:
            values["reuse"].append(float(row[2]))
        if row[3] is not None:
            values["edit"].append(float(row[3]))
        if row[4] is not None:
            values["time_saved"].append(float(row[4]))
    return values


def _market_comparison(
    connection: sqlite3.Connection,
    spec: Mapping[str, Any],
    candidate_id: str,
    comparator_id: str,
    arm_summaries: Mapping[str, Mapping[str, Any]],
) -> Dict[str, Any]:
    candidate = arm_summaries[candidate_id]
    comparator = arm_summaries[comparator_id]
    paired = _market_pair_values(connection, candidate_id, comparator_id)
    seed = int(spec["seed"])
    comparable_level = min(
        int(candidate["max_evidence_level"]),
        int(comparator["max_evidence_level"]),
    )

    def independent_delta(metric: str) -> float | None:
        left = candidate.get(metric)
        right = comparator.get(metric)
        if left is None or right is None:
            return None
        return float(left) - float(right)

    completion_ci = _bootstrap_ci(paired["completion"], seed + 101)
    acceptance_ci = _bootstrap_ci(paired["acceptance"], seed + 103)
    reuse_ci = _bootstrap_ci(paired["reuse"], seed + 107)
    edit_ci = _bootstrap_ci(paired["edit"], seed + 109)
    time_saved_ci = _bootstrap_ci(paired["time_saved"], seed + 113)

    return {
        "candidate_id": candidate_id,
        "comparator_id": comparator_id,
        "candidate_events": candidate["event_count"],
        "comparator_events": comparator["event_count"],
        "paired_market_tasks": len(paired["completion"]),
        "comparable_evidence_level": comparable_level,
        "comparable_evidence_label": LEVEL_LABELS[comparable_level],
        "completion_delta": completion_ci,
        "acceptance_delta": acceptance_ci,
        "reuse_delta": reuse_ci,
        "human_edit_seconds_delta": edit_ci,
        "time_saved_minutes_delta": time_saved_ci,
        "independent_completion_delta": independent_delta("completion_rate"),
        "independent_acceptance_delta": independent_delta("acceptance_rate"),
        "independent_reuse_delta": independent_delta("reuse_intent_rate"),
        "candidate_mean_human_edit_seconds": candidate["mean_human_edit_seconds"],
        "comparator_mean_human_edit_seconds": comparator["mean_human_edit_seconds"],
        "human_edit_increase_ratio": percentage_change(
            candidate["mean_human_edit_seconds"], comparator["mean_human_edit_seconds"]
        ),
        "candidate_incidents": candidate["critical_or_high_incidents"],
        "comparator_incidents": comparator["critical_or_high_incidents"],
    }


def _market_summary(
    connection: sqlite3.Connection,
    spec: Mapping[str, Any],
    feedback_meta: Mapping[str, Any],
    candidate_id: str,
    primary_comparator: str,
) -> Dict[str, Any]:
    by_arm = {
        str(arm["id"]): _market_arm_summary(connection, str(arm["id"]))
        for arm in spec["arms"]
    }
    comparison = _market_comparison(
        connection,
        spec,
        candidate_id,
        primary_comparator,
        by_arm,
    )
    return {
        **feedback_meta,
        "by_arm": by_arm,
        "primary_comparison": comparison,
    }


def aggregate_evidence(
    spec: Mapping[str, Any],
    result_rows: Iterable[Mapping[str, Any]],
    feedback_rows: Iterable[Mapping[str, Any]] | None = None,
) -> Dict[str, Any]:
    assert_valid(validate_experiment_spec(spec), "实验规范")
    connection, db_path = _create_db()
    try:
        result_meta = _insert_results(connection, spec, result_rows)
        feedback_meta = _insert_feedback(connection, spec, feedback_rows)
        arm_by_id, by_kind = _arm_maps(spec)
        candidate_id = by_kind["candidate"]
        baseline_id = by_kind.get("baseline")
        no_skill_id = by_kind["no_skill"]
        primary_comparator = baseline_id or no_skill_id

        arm_summaries = {
            arm_id: _arm_summary(connection, arm_id, arm)
            for arm_id, arm in arm_by_id.items()
        }
        pair_summaries = {
            comparator_id: _pair_summary(connection, spec, candidate_id, comparator_id)
            for comparator_id in arm_by_id
            if comparator_id != candidate_id
        }
        market = _market_summary(
            connection,
            spec,
            feedback_meta,
            candidate_id,
            primary_comparator,
        )
        comparable_market_level = int(
            market["primary_comparison"]["comparable_evidence_level"]
        )
        max_level = max(
            int(result_meta["max_result_evidence_level"]),
            comparable_market_level,
        )

        combined_hard = Counter(result_meta["hard_failure_counts"])
        combined_hard.update(feedback_meta["hard_failure_counts"])
        data_quality = {
            **result_meta,
            "feedback_identity_mismatch_count": feedback_meta["feedback_identity_mismatch_count"],
            "feedback_orphan_run_count": feedback_meta["feedback_orphan_run_count"],
            "simulated_competitor_market_claim_count": feedback_meta[
                "simulated_competitor_market_claim_count"
            ],
            "identity_mismatch_count": int(result_meta["result_identity_mismatch_count"])
            + int(feedback_meta["feedback_identity_mismatch_count"]),
            "hard_failure_counts": dict(combined_hard),
        }

        summary = {
            "schema_version": "1.0",
            "generated_at": utc_now(),
            "experiment_id": spec["experiment_id"],
            "spec_digest": object_sha256(spec),
            "subject": spec["subject"],
            "evidence_target": spec["evidence_target"],
            "evidence_level": max_level,
            "evidence_level_label": LEVEL_LABELS[max_level],
            "target_min_level": TARGET_MIN_LEVEL[spec["evidence_target"]],
            "primary_comparator": primary_comparator,
            "arms": arm_summaries,
            "candidate_pairs": pair_summaries,
            "slices": _slice_summaries(connection, candidate_id),
            "market": market,
            "data_quality": data_quality,
            "records_total": int(connection.execute("SELECT COUNT(*) FROM results").fetchone()[0]),
            "summary_digest": None,
        }
        summary["summary_digest"] = object_sha256(
            {key: value for key, value in summary.items() if key != "summary_digest"}
        )
        return summary
    finally:
        connection.close()
        for suffix in ("", "-wal", "-shm"):
            try:
                Path(f"{db_path}{suffix}").unlink(missing_ok=True)
            except OSError:
                pass


def _market_effective_delta(comparison: Mapping[str, Any], metric: str) -> float | None:
    paired = comparison.get(f"{metric}_delta", {})
    if int(paired.get("n", 0)) > 0:
        value = paired.get("mean")
        return None if value is None else float(value)
    value = comparison.get(f"independent_{metric}_delta")
    return None if value is None else float(value)


def decide_gate(
    spec: Mapping[str, Any],
    summary: Mapping[str, Any],
    quality_audit: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    assert_valid(validate_experiment_spec(spec), "实验规范")
    if summary.get("experiment_id") != spec["experiment_id"]:
        raise ValidationError("汇总结果与实验规范 experiment_id 不一致")
    expected_digest = object_sha256(spec)
    if summary.get("spec_digest") != expected_digest:
        raise ValidationError("汇总结果未绑定当前实验规范")

    candidate_id = next(arm["id"] for arm in spec["arms"] if arm["kind"] == "candidate")
    baseline_id = next((arm["id"] for arm in spec["arms"] if arm["kind"] == "baseline"), None)
    no_skill_id = next(arm["id"] for arm in spec["arms"] if arm["kind"] == "no_skill")
    primary_comparator = baseline_id or no_skill_id
    pair = summary.get("candidate_pairs", {}).get(primary_comparator)
    gates = spec["gates"]
    reasons: List[Dict[str, str]] = []

    blocking_codes = set(gates["blocking_failure_codes"])
    observed_failures = set(summary.get("data_quality", {}).get("hard_failure_counts", {}))
    # 内部生成的证据身份错误即使没有显式列入用户门，也必须 fail-closed。
    intrinsic_blockers = {
        "identity_mismatch",
        "feedback_identity_mismatch",
        "feedback_orphan_run",
        "simulated_competitor_market_claim",
    }
    blocking_observed = sorted((blocking_codes | intrinsic_blockers) & observed_failures)
    candidate_market_incidents = int(
        summary.get("market", {})
        .get("by_arm", {})
        .get(candidate_id, {})
        .get("critical_or_high_incidents", 0)
    )
    if candidate_market_incidents > 0:
        blocking_observed = sorted(set(blocking_observed) | {"severe_market_incident"})

    quality_required = any(bool(value) for value in (spec.get("quality_gates") or {}).values())
    quality_failure: str | None = None
    if quality_required:
        if not isinstance(quality_audit, Mapping):
            quality_failure = "冻结质量审计缺失"
        elif quality_audit.get("spec_digest") != expected_digest:
            quality_failure = "质量审计未绑定当前实验规范"
        elif quality_audit.get("status") != "PASS" or quality_audit.get("valid") is not True:
            quality_failure = (
                f"质量审计状态={quality_audit.get('status')}; "
                f"blocking={quality_audit.get('blocking_reports', [])}; "
                f"reheat={quality_audit.get('reheat_reports', [])}"
            )

    if quality_failure:
        reasons.append(
            {
                "code": "QUALITY_AUDIT_FAILED",
                "severity": "blocking",
                "detail": quality_failure,
            }
        )
        decision = "BLOCKED"
    elif blocking_observed:
        reasons.append(
            {
                "code": "HARD_GATE_FAILED",
                "severity": "blocking",
                "detail": ", ".join(blocking_observed),
            }
        )
        decision = "BLOCKED"
    elif not pair:
        reasons.append(
            {
                "code": "MISSING_PRIMARY_PAIR",
                "severity": "blocking",
                "detail": f"缺少 Candidate 与 {primary_comparator} 的配对结果",
            }
        )
        decision = "BLOCKED"
    else:
        decision = "EVIDENCE_READY_FOR_TELEIOSIS"
        if pair["paired_tasks"] < int(gates["min_paired_tasks"]):
            reasons.append(
                {
                    "code": "INSUFFICIENT_PAIRED_TASKS",
                    "severity": "evidence",
                    "detail": f"{pair['paired_tasks']} < {gates['min_paired_tasks']}",
                }
            )
            decision = "REHEAT_REQUIRED"

        success_mean = pair["success_delta"]["mean"]
        score_mean = pair["score_delta"]["mean"]
        if success_mean is not None and success_mean < -float(gates["max_protected_success_regression"]):
            reasons.append(
                {
                    "code": "CLEAR_SUCCESS_REGRESSION",
                    "severity": "blocking",
                    "detail": f"成功率配对差异 {success_mean:.4f}",
                }
            )
            decision = "REVERT"
        elif success_mean is None or success_mean < float(gates["min_success_delta"]):
            reasons.append(
                {
                    "code": "SUCCESS_DELTA_BELOW_TARGET",
                    "severity": "decision",
                    "detail": f"{success_mean} < {gates['min_success_delta']}",
                }
            )
            if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                decision = "KEEP_BASELINE"

        if score_mean is None or score_mean < float(gates["min_score_delta"]):
            reasons.append(
                {
                    "code": "SCORE_DELTA_BELOW_TARGET",
                    "severity": "decision",
                    "detail": f"{score_mean} < {gates['min_score_delta']}",
                }
            )
            if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                decision = "KEEP_BASELINE"

        protected_mean = pair["protected_success_delta"]["mean"]
        if protected_mean is not None and protected_mean < -float(gates["max_protected_success_regression"]):
            reasons.append(
                {
                    "code": "PROTECTED_TASK_REGRESSION",
                    "severity": "blocking",
                    "detail": f"保护任务成功率差异 {protected_mean:.4f}",
                }
            )
            decision = "REVERT"

        cost_ratio = pair.get("cost_increase_ratio")
        if cost_ratio is not None and cost_ratio > float(gates["max_cost_increase_ratio"]):
            reasons.append(
                {
                    "code": "COST_INCREASE_EXCEEDS_LIMIT",
                    "severity": "decision",
                    "detail": f"{cost_ratio:.4f} > {gates['max_cost_increase_ratio']}",
                }
            )
            if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                decision = "KEEP_BASELINE"

        latency_ratio = pair.get("latency_increase_ratio")
        if latency_ratio is not None and latency_ratio > float(gates["max_latency_increase_ratio"]):
            reasons.append(
                {
                    "code": "LATENCY_INCREASE_EXCEEDS_LIMIT",
                    "severity": "decision",
                    "detail": f"{latency_ratio:.4f} > {gates['max_latency_increase_ratio']}",
                }
            )
            if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                decision = "KEEP_BASELINE"

        if gates.get("require_positive_ci", False):
            success_low = pair["success_delta"]["low"]
            score_low = pair["score_delta"]["low"]
            if success_low is None or score_low is None or success_low <= 0 or score_low <= 0:
                reasons.append(
                    {
                        "code": "UNCERTAINTY_NOT_RESOLVED",
                        "severity": "evidence",
                        "detail": "配对 bootstrap 置信区间下界未同时大于 0",
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "REHEAT_REQUIRED"

        target_min_level = TARGET_MIN_LEVEL[spec["evidence_target"]]
        if int(summary.get("evidence_level", 0)) < target_min_level:
            reasons.append(
                {
                    "code": "EVIDENCE_LEVEL_BELOW_TARGET",
                    "severity": "evidence",
                    "detail": f"L{summary.get('evidence_level', 0)} < L{target_min_level}",
                }
            )
            if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                decision = "REHEAT_REQUIRED"

        if spec["evidence_target"] != "lab":
            market_comparison = summary.get("market", {}).get("primary_comparison", {})
            min_events = int(gates["min_market_events_per_arm"])
            candidate_events = int(market_comparison.get("candidate_events", 0))
            comparator_events = int(market_comparison.get("comparator_events", 0))
            if gates.get("require_market_comparator", True) and (
                candidate_events < min_events or comparator_events < min_events
            ):
                reasons.append(
                    {
                        "code": "INSUFFICIENT_COMPARABLE_MARKET_EVENTS",
                        "severity": "evidence",
                        "detail": (
                            f"candidate={candidate_events}, comparator={comparator_events}, "
                            f"required_per_arm={min_events}"
                        ),
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "REHEAT_REQUIRED"

            comparable_level = int(market_comparison.get("comparable_evidence_level", 0))
            if gates.get("require_market_comparator", True) and comparable_level < target_min_level:
                reasons.append(
                    {
                        "code": "MARKET_EVIDENCE_NOT_COMPARABLE",
                        "severity": "evidence",
                        "detail": f"Candidate 与 comparator 的共同证据仅 L{comparable_level}",
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "REHEAT_REQUIRED"

            completion_delta = _market_effective_delta(market_comparison, "completion")
            if completion_delta is None or completion_delta < float(gates["min_market_completion_delta"]):
                reasons.append(
                    {
                        "code": "MARKET_COMPLETION_DELTA_BELOW_TARGET",
                        "severity": "decision",
                        "detail": f"{completion_delta} < {gates['min_market_completion_delta']}",
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "KEEP_BASELINE"

            acceptance_delta = _market_effective_delta(market_comparison, "acceptance")
            if acceptance_delta is None or acceptance_delta < float(gates["min_market_acceptance_delta"]):
                reasons.append(
                    {
                        "code": "MARKET_ACCEPTANCE_DELTA_BELOW_TARGET",
                        "severity": "decision",
                        "detail": f"{acceptance_delta} < {gates['min_market_acceptance_delta']}",
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "KEEP_BASELINE"

            edit_ratio = market_comparison.get("human_edit_increase_ratio")
            if edit_ratio is not None and edit_ratio > float(gates["max_market_edit_increase_ratio"]):
                reasons.append(
                    {
                        "code": "MARKET_EDIT_BURDEN_EXCEEDS_LIMIT",
                        "severity": "decision",
                        "detail": f"{edit_ratio:.4f} > {gates['max_market_edit_increase_ratio']}",
                    }
                )
                if decision == "EVIDENCE_READY_FOR_TELEIOSIS":
                    decision = "KEEP_BASELINE"

    if decision == "EVIDENCE_READY_FOR_TELEIOSIS" and not reasons:
        reasons.append(
            {
                "code": "ALL_FROZEN_GATES_PASSED",
                "severity": "positive",
                "detail": "满足冻结的效果、保护任务、成本、时延、因果市场证据与身份硬门。",
            }
        )
    gate_result = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "experiment_id": spec["experiment_id"],
        "subject": spec["subject"],
        "decision": decision,
        "primary_comparator": primary_comparator,
        "evidence_level": summary.get("evidence_level"),
        "evidence_level_label": summary.get("evidence_level_label"),
        "reasons": reasons,
        "summary_digest": summary.get("summary_digest"),
        "quality_audit_digest": quality_audit.get("quality_audit_digest") if isinstance(quality_audit, Mapping) else None,
        "gate_contract_digest": object_sha256(gates),
        "gate_result_digest": None,
    }
    gate_result["gate_result_digest"] = object_sha256(
        {key: value for key, value in gate_result.items() if key != "gate_result_digest"}
    )
    return gate_result


def build_next_iteration_plan(
    spec: Mapping[str, Any],
    summary: Mapping[str, Any],
    gate_result: Mapping[str, Any],
) -> Dict[str, Any]:
    if gate_result.get("summary_digest") != summary.get("summary_digest"):
        raise ValidationError("Gate 与 Summary 未绑定同一份证据")
    actions: List[Dict[str, Any]] = []
    priority = 0

    def add(
        action_type: str,
        hypothesis: str,
        evidence: str,
        acceptance: str,
        rollback: str,
        blocking: bool = False,
    ) -> None:
        nonlocal priority
        priority += 1
        actions.append(
            {
                "priority": priority,
                "type": action_type,
                "hypothesis": hypothesis,
                "evidence": evidence,
                "acceptance": acceptance,
                "rollback": rollback,
                "blocking": blocking,
            }
        )

    reason_codes = {item["code"] for item in gate_result.get("reasons", [])}
    if "HARD_GATE_FAILED" in reason_codes:
        add(
            "hard-gate-remediation",
            "先修复身份、安全、隐私、sealed holdout、反馈孤儿运行或严重事故；平均收益不能抵消硬失败。",
            "gate_result.reasons[HARD_GATE_FAILED]",
            "阻断代码归零，原始失败轨迹保留，保护任务回归通过。",
            "回退到最近已接受 Baseline；禁止就地覆盖正式版。",
            True,
        )
    if "PROTECTED_TASK_REGRESSION" in reason_codes or "CLEAR_SUCCESS_REGRESSION" in reason_codes:
        add(
            "regression-isolation",
            "候选修改在保护任务或总体成功率上产生负迁移，需要消融定位。",
            "summary.candidate_pairs.*.protected_success_delta",
            "消融后保护任务差异不低于冻结阈值，且总体收益保留。",
            "REVERT 触发该回归的 change set。",
            True,
        )
    if "COST_INCREASE_EXCEEDS_LIMIT" in reason_codes or "LATENCY_INCREASE_EXCEEDS_LIMIT" in reason_codes:
        add(
            "efficiency-remediation",
            "候选可能通过增加上下文、工具调用或重复工作换取表面效果。",
            "summary.candidate_pairs.*.cost_increase_ratio / latency_increase_ratio",
            "成本与时延回到冻结上限内，且成功率和评分不退化。",
            "保留原 Baseline 与成本预算，超限自动熔断。",
        )
    if "SUCCESS_DELTA_BELOW_TARGET" in reason_codes or "SCORE_DELTA_BELOW_TARGET" in reason_codes:
        weakest: List[Mapping[str, Any]] = []
        weakest.extend(summary.get("slices", {}).get("partition", [])[:3])
        weakest.extend(summary.get("slices", {}).get("stress_category", [])[:3])
        add(
            "outcome-hypothesis",
            "从最低表现的任务切片提炼一个可证伪机制，不增加无证据的通用 Prompt。",
            json.dumps(weakest, ensure_ascii=False, sort_keys=True),
            "相同任务、预算和运行时下，配对成功率及评分达到冻结目标。",
            "若外部 holdout 无增益，REVERT 该机制。",
        )
    market_codes = {
        "EVIDENCE_LEVEL_BELOW_TARGET",
        "INSUFFICIENT_COMPARABLE_MARKET_EVENTS",
        "MARKET_EVIDENCE_NOT_COMPARABLE",
        "MARKET_COMPLETION_DELTA_BELOW_TARGET",
        "MARKET_ACCEPTANCE_DELTA_BELOW_TARGET",
        "MARKET_EDIT_BURDEN_EXCEEDS_LIMIT",
    }
    if reason_codes & market_codes:
        add(
            "market-evidence-collection",
            "实验室增益尚未形成 Candidate 与冻结 Comparator 的真实、同源、可比较市场证据。",
            "summary.market.primary_comparison",
            "通过双臂 opt-in Canary、外部盲验收或真实 Issue/PR/微赏金，分别达到每臂样本和市场差异门。",
            "任一严重事件立即终止 Canary 并回退 Baseline。",
            True,
        )
    if "INSUFFICIENT_PAIRED_TASKS" in reason_codes or "UNCERTAINTY_NOT_RESOLVED" in reason_codes:
        add(
            "evidence-expansion",
            "当前样本不足以区分随机波动与真实增益。",
            "gate_result.reasons",
            "按来源和失效机制扩展独立任务；达到最小配对数并缩窄区间。",
            "不修改 Candidate，只追加受控证据。",
        )
    if not actions:
        add(
            "controlled-promotion",
            "冻结证据已通过，可以受控晋级，但不得把实验结论扩大为未验证市场声明。",
            "gate_result.decision=EVIDENCE_READY_FOR_TELEIOSIS",
            "安装后重新绑定精确 tree hash，运行 release smoke 与最小 Canary。",
            "使用已封存 Baseline 和安装事务收据回滚。",
        )

    plan = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "experiment_id": spec["experiment_id"],
        "decision": gate_result["decision"],
        "actions": actions,
        "constraints": [
            "只读 Baseline；所有修改进入独立 Candidate。",
            "Candidate 不得读取 sealed_holdout、blind map 或修改 Gate。",
            "每个 change set 必须 KEEP、REVERT 或 NO_CHANGE。",
            "模拟竞品不能计为真实市场反馈。",
            "市场反馈必须绑定 task_id、run_id、arm_id 与 artifact_digest。",
        ],
        "plan_digest": None,
    }
    plan["plan_digest"] = object_sha256(
        {key: value for key, value in plan.items() if key != "plan_digest"}
    )
    return plan
