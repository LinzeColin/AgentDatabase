from __future__ import annotations

import json
import math
import os
import random
import shutil
import signal
import statistics
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence, Set, Tuple

from .common import (
    TeleiosisError,
    atomic_write_json,
    atomic_write_text,
    canonical_json_hash,
    read_json,
    sha256_file,
)

LEVEL_ORDER = ["L1", "L2", "L3", "L4"]
HARD_DEFAULT = {"safety", "truthfulness", "permission", "data_integrity", "sealed_leakage"}
STATUS_DEVELOPMENT = {"IMPROVED", "DEGRADED", "REHEAT_REQUIRED", "INSUFFICIENT_EVIDENCE"}
STATUS_SEALED = {"ARENA_EVIDENCE_READY", "BLOCKED", "INVALID_RUN"}
OBSERVATION_KEYS = {"participant_id", "task_id", "split", "slice", "repetition", "metrics", "cost", "hard_failures"}
REQUIRED_DIMENSIONS = [
    "hidden_quality", "worst_slice", "hard_constraint_pass", "redteam_pass", "regression_retention", "cost_efficiency"
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _protocol_payload(spec: Dict[str, Any]) -> Dict[str, Any]:
    payload = dict(spec)
    payload.pop("freeze", None)
    return payload


def protocol_hash(spec: Dict[str, Any]) -> str:
    return canonical_json_hash(_protocol_payload(spec))


def validate_spec(spec: Dict[str, Any], require_frozen: bool = False) -> Dict[str, Any]:
    allowed = {"schema_version", "arena_id", "mode", "declared_evidence_level", "candidate_participant_id", "participants", "protocol", "freeze", "metadata"}
    unknown = sorted(set(spec) - allowed)
    if unknown:
        raise TeleiosisError("ARENA_SPEC_UNKNOWN_FIELDS", "ArenaSpec 包含未知字段。", {"unknown": unknown})
    if spec.get("schema_version") != "teleiosis.arena_spec.v1":
        raise TeleiosisError("ARENA_SPEC_SCHEMA", "ArenaSpec schema_version 错误。")
    if spec.get("mode") not in {"development", "sealed"}:
        raise TeleiosisError("ARENA_MODE", "Arena mode 必须是 development 或 sealed。")
    declared = spec.get("declared_evidence_level")
    if declared not in LEVEL_ORDER:
        raise TeleiosisError("ARENA_EVIDENCE_LEVEL", "declared_evidence_level 必须是 L1—L4。")
    participants = spec.get("participants")
    if not isinstance(participants, list) or len(participants) < 2:
        raise TeleiosisError("ARENA_PARTICIPANTS", "同场竞技至少需要两个参赛对象。")
    ids = []
    for participant in participants:
        if not isinstance(participant, dict):
            raise TeleiosisError("ARENA_PARTICIPANT_TYPE", "参赛对象必须是对象。")
        required = {"id", "role", "display_name", "version", "artifact_sha256", "adapter", "governance_capabilities"}
        if set(participant) != required:
            raise TeleiosisError("ARENA_PARTICIPANT_FIELDS", "参赛对象字段必须精确。", {"participant": participant.get("id"), "missing": sorted(required - set(participant)), "extra": sorted(set(participant) - required)})
        pid = participant.get("id")
        if not isinstance(pid, str) or not pid or len(pid) > 128:
            raise TeleiosisError("ARENA_PARTICIPANT_ID", "参赛对象 ID 不合法。")
        ids.append(pid)
        digest = participant.get("artifact_sha256")
        if not isinstance(digest, str) or len(digest) != 64 or any(ch not in "0123456789abcdef" for ch in digest):
            raise TeleiosisError("ARENA_ARTIFACT_HASH", "参赛制品必须有 64 位小写 SHA-256。", {"participant": pid})
        adapter = participant.get("adapter")
        if not isinstance(adapter, dict) or "kind" not in adapter or "native_execution" not in adapter or "official_implementation" not in adapter:
            raise TeleiosisError("ARENA_ADAPTER", "Adapter 必须声明 kind、native_execution 和 official_implementation。", {"participant": pid})
        if not isinstance(participant.get("governance_capabilities"), list):
            raise TeleiosisError("ARENA_GOVERNANCE_CAPABILITIES", "governance_capabilities 必须是数组。", {"participant": pid})
    if len(ids) != len(set(ids)):
        raise TeleiosisError("ARENA_PARTICIPANT_DUPLICATE", "参赛对象 ID 重复。")
    if spec.get("candidate_participant_id") not in ids:
        raise TeleiosisError("ARENA_CANDIDATE_MISSING", "candidate_participant_id 不在参赛对象中。")
    protocol = spec.get("protocol")
    if not isinstance(protocol, dict):
        raise TeleiosisError("ARENA_PROTOCOL", "Arena protocol 缺失。")
    required_protocol = {"required_splits", "repetitions", "seeds", "dimensions", "hard_gate_categories", "budget", "bootstrap_samples", "bootstrap_seed", "governance_requirements", "sealed_data_visibility"}
    if set(protocol) - (required_protocol | {"production_blind", "authorized_real_users"}):
        raise TeleiosisError("ARENA_PROTOCOL_UNKNOWN_FIELDS", "Arena protocol 包含未知字段。", {"unknown": sorted(set(protocol) - (required_protocol | {"production_blind", "authorized_real_users"}))})
    missing = sorted(required_protocol - set(protocol))
    if missing:
        raise TeleiosisError("ARENA_PROTOCOL_FIELDS", "Arena protocol 缺少字段。", {"missing": missing})
    splits = protocol.get("required_splits")
    if not isinstance(splits, list) or set(splits) != {"hidden_iid", "hidden_ood", "redteam", "regression"}:
        raise TeleiosisError("ARENA_SPLITS", "required_splits 必须精确覆盖 hidden_iid、hidden_ood、redteam、regression。")
    repetitions = protocol.get("repetitions")
    if not isinstance(repetitions, int) or repetitions < 1 or repetitions > 1000:
        raise TeleiosisError("ARENA_REPETITIONS", "repetitions 必须在 1—1000。")
    seeds = protocol.get("seeds")
    if not isinstance(seeds, list) or len(seeds) != repetitions or len(set(seeds)) != len(seeds) or any(not isinstance(seed, int) for seed in seeds):
        raise TeleiosisError("ARENA_SEEDS", "随机种子必须与 repetitions 等长、唯一且为整数。")
    dimensions = protocol.get("dimensions")
    if not isinstance(dimensions, list) or [item.get("id") for item in dimensions if isinstance(item, dict)] != REQUIRED_DIMENSIONS:
        raise TeleiosisError("ARENA_DIMENSIONS", "Arena 维度必须按固定顺序完整声明。")
    weights = [item.get("weight") for item in dimensions]
    if any(not isinstance(weight, (int, float)) or weight < 0 for weight in weights) or abs(sum(float(weight) for weight in weights) - 1.0) > 1e-9:
        raise TeleiosisError("ARENA_WEIGHTS", "Arena 权重必须非负且总和为 1。")
    hard = protocol.get("hard_gate_categories")
    if not isinstance(hard, list) or not HARD_DEFAULT.issubset(set(hard)):
        raise TeleiosisError("ARENA_HARD_GATES", "硬门必须至少包含安全、真实性、权限、数据完整性和密封泄漏。")
    budget = protocol.get("budget")
    if not isinstance(budget, dict) or set(budget) != {"metric", "ceiling_per_participant", "equal_budget", "relative_tolerance"}:
        raise TeleiosisError("ARENA_BUDGET_FIELDS", "预算合同字段不完整。")
    if budget.get("metric") not in {"candidate_evaluations", "input_tokens", "output_tokens", "usd", "wall_seconds"}:
        raise TeleiosisError("ARENA_BUDGET_METRIC", "预算 metric 不受支持。")
    if not isinstance(budget.get("ceiling_per_participant"), (int, float)) or budget["ceiling_per_participant"] <= 0:
        raise TeleiosisError("ARENA_BUDGET_CEILING", "预算上限必须大于 0。")
    if budget.get("equal_budget") is not True:
        raise TeleiosisError("ARENA_EQUAL_BUDGET_REQUIRED", "公平主榜必须启用 equal_budget。")
    tolerance = budget.get("relative_tolerance")
    if not isinstance(tolerance, (int, float)) or tolerance < 0 or tolerance > 0.1:
        raise TeleiosisError("ARENA_BUDGET_TOLERANCE", "预算相对容差必须在 0—0.1。")
    samples = protocol.get("bootstrap_samples")
    if not isinstance(samples, int) or samples < 100 or samples > 100000:
        raise TeleiosisError("ARENA_BOOTSTRAP", "bootstrap_samples 必须在 100—100000。")
    if not isinstance(protocol.get("bootstrap_seed"), int):
        raise TeleiosisError("ARENA_BOOTSTRAP_SEED", "bootstrap_seed 必须是整数。")
    if not isinstance(protocol.get("governance_requirements"), list) or not protocol["governance_requirements"]:
        raise TeleiosisError("ARENA_GOVERNANCE_REQUIREMENTS", "治理能力要求不能为空。")
    if protocol.get("sealed_data_visibility") != "verifier_only":
        raise TeleiosisError("ARENA_SEALED_VISIBILITY", "隐藏数据可见性必须是 verifier_only。")
    if spec["mode"] == "sealed" and not require_frozen and not spec.get("freeze"):
        # Validation may be used before freeze; score path passes require_frozen=True.
        pass
    if require_frozen:
        freeze = spec.get("freeze")
        if not isinstance(freeze, dict) or set(freeze) != {"protocol_hash", "frozen_at"}:
            raise TeleiosisError("ARENA_NOT_FROZEN", "评分前必须冻结 ArenaSpec。")
        actual = protocol_hash(spec)
        if freeze.get("protocol_hash") != actual:
            raise TeleiosisError("ARENA_PROTOCOL_TAMPERED", "冻结后的 ArenaSpec 已变化。", {"expected": freeze.get("protocol_hash"), "actual": actual})
    return {"participants": ids, "mode": spec["mode"], "declared_evidence_level": declared}


def freeze_spec(spec_path: Path, output: Path, frozen_at: Optional[str] = None) -> Dict[str, Any]:
    spec = read_json(spec_path)
    validate_spec(spec, require_frozen=False)
    spec = dict(spec)
    if spec.get("freeze"):
        validate_spec(spec, require_frozen=True)
    else:
        spec["freeze"] = {"protocol_hash": protocol_hash(spec), "frozen_at": frozen_at or _now_iso()}
    validate_spec(spec, require_frozen=True)
    atomic_write_json(output, spec)
    return {"status": "FROZEN", "output": str(output), "protocol_hash": spec["freeze"]["protocol_hash"], "arena_id": spec["arena_id"]}


def _load_observations(path: Path) -> List[Dict[str, Any]]:
    if not path.exists() or path.is_symlink() or not path.is_file():
        raise TeleiosisError("ARENA_OBSERVATIONS_FILE", "observations 必须是普通 JSONL 文件。", {"path": str(path)})
    if path.stat().st_size > 512 * 1024 * 1024:
        raise TeleiosisError("ARENA_OBSERVATIONS_TOO_LARGE", "observations 超过 512 MiB。")
    rows: List[Dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for number, line in enumerate(handle, 1):
            if not line.strip():
                continue
            if len(line.encode("utf-8")) > 2 * 1024 * 1024:
                raise TeleiosisError("ARENA_OBSERVATION_LINE_TOO_LARGE", "单行 observation 超过 2 MiB。", {"line": number})
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise TeleiosisError("ARENA_OBSERVATION_JSON", "observation 行无法解析。", {"line": number, "reason": str(exc)})
            if not isinstance(row, dict) or set(row) != OBSERVATION_KEYS:
                raise TeleiosisError("ARENA_OBSERVATION_FIELDS", "observation 字段必须精确。", {"line": number})
            rows.append(row)
            if len(rows) > 2_000_000:
                raise TeleiosisError("ARENA_OBSERVATION_COUNT", "observation 数量超过上限。")
    if not rows:
        raise TeleiosisError("ARENA_OBSERVATIONS_EMPTY", "observations 为空。")
    return rows


def _validate_observations(spec: Dict[str, Any], rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    participant_ids = [item["id"] for item in spec["participants"]]
    participants = set(participant_ids)
    repetitions = spec["protocol"]["repetitions"]
    required_splits = set(spec["protocol"]["required_splits"])
    keys_by_participant: Dict[str, Set[Tuple[str, str, str, int]]] = {pid: set() for pid in participant_ids}
    seen: Set[Tuple[str, str, str, str, int]] = set()
    split_by_participant: Dict[str, Set[str]] = {pid: set() for pid in participant_ids}
    for idx, row in enumerate(rows):
        pid = row.get("participant_id")
        if pid not in participants:
            raise TeleiosisError("ARENA_UNKNOWN_PARTICIPANT", "observation 引用了未知参赛对象。", {"row": idx, "participant": pid})
        for field in ("task_id", "split", "slice"):
            if not isinstance(row.get(field), str) or not row[field] or len(row[field]) > 256:
                raise TeleiosisError("ARENA_OBSERVATION_ID", "task/split/slice 必须是非空短字符串。", {"row": idx, "field": field})
        rep = row.get("repetition")
        if not isinstance(rep, int) or rep < 0 or rep >= repetitions:
            raise TeleiosisError("ARENA_OBSERVATION_REPETITION", "repetition 超出冻结范围。", {"row": idx})
        metrics = row.get("metrics")
        if not isinstance(metrics, dict) or not {"quality", "hard_constraint", "redteam", "regression"}.issubset(metrics):
            raise TeleiosisError("ARENA_OBSERVATION_METRICS", "metrics 缺少质量、硬约束、红队或回归。", {"row": idx})
        for key, value in metrics.items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0 or value > 1:
                raise TeleiosisError("ARENA_METRIC_RANGE", "metric 必须在 0—1。", {"row": idx, "metric": key, "value": value})
        cost = row.get("cost")
        required_costs = {"candidate_evaluations", "input_tokens", "output_tokens", "usd", "wall_seconds"}
        if not isinstance(cost, dict) or set(cost) != required_costs:
            raise TeleiosisError("ARENA_COST_FIELDS", "cost 字段必须精确。", {"row": idx})
        for key, value in cost.items():
            if not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
                raise TeleiosisError("ARENA_COST_RANGE", "cost 必须是非负有限数。", {"row": idx, "cost": key})
        failures = row.get("hard_failures")
        if not isinstance(failures, list) or any(not isinstance(item, str) for item in failures):
            raise TeleiosisError("ARENA_HARD_FAILURES", "hard_failures 必须是字符串数组。", {"row": idx})
        unknown_failures = set(failures) - set(spec["protocol"]["hard_gate_categories"])
        if unknown_failures:
            raise TeleiosisError("ARENA_HARD_FAILURE_CATEGORY", "hard failure 类别不在冻结协议中。", {"row": idx, "unknown": sorted(unknown_failures)})
        key = (row["task_id"], row["split"], row["slice"], rep)
        full_key = (pid,) + key
        if full_key in seen:
            raise TeleiosisError("ARENA_DUPLICATE_OBSERVATION", "同一参赛对象任务重复。", {"key": full_key})
        seen.add(full_key)
        keys_by_participant[pid].add(key)
        split_by_participant[pid].add(row["split"])
    reference = keys_by_participant[participant_ids[0]]
    for pid in participant_ids:
        if keys_by_participant[pid] != reference:
            raise TeleiosisError("ARENA_TASK_SET_MISMATCH", "所有参赛对象必须拥有完全相同的任务、切片和重复集合。", {"participant": pid, "missing": len(reference - keys_by_participant[pid]), "extra": len(keys_by_participant[pid] - reference)})
        if not required_splits.issubset(split_by_participant[pid]):
            raise TeleiosisError("ARENA_SPLIT_MISSING", "参赛对象缺少冻结数据分区。", {"participant": pid, "missing": sorted(required_splits - split_by_participant[pid])})
    budget_metric = spec["protocol"]["budget"]["metric"]
    ceiling = float(spec["protocol"]["budget"]["ceiling_per_participant"])
    tolerance = float(spec["protocol"]["budget"]["relative_tolerance"])
    totals: Dict[str, float] = {}
    for pid in participant_ids:
        totals[pid] = sum(float(row["cost"][budget_metric]) for row in rows if row["participant_id"] == pid)
        if totals[pid] > ceiling * (1 + 1e-12):
            raise TeleiosisError("ARENA_BUDGET_EXCEEDED", "参赛对象超过冻结预算。", {"participant": pid, "used": totals[pid], "ceiling": ceiling, "metric": budget_metric})
    reference_budget = totals[participant_ids[0]]
    for pid in participant_ids[1:]:
        denominator = max(reference_budget, totals[pid], 1.0)
        relative = abs(totals[pid] - reference_budget) / denominator
        if relative > tolerance + 1e-12:
            raise TeleiosisError("ARENA_BUDGET_MISMATCH", "公平主榜预算不相等。", {"reference": reference_budget, "participant": pid, "used": totals[pid], "relative_difference": relative, "tolerance": tolerance})
    return {"tasks_per_participant": len(reference), "budget_totals": totals, "budget_metric": budget_metric}


def _mean(values: Iterable[float]) -> float:
    data = list(values)
    if not data:
        return 0.0
    return sum(data) / len(data)


def _aggregate_participant(pid: str, rows: List[Dict[str, Any]], budget_metric: str) -> Dict[str, Any]:
    own = [row for row in rows if row["participant_id"] == pid]
    hidden = [row for row in own if row["split"] in {"hidden_iid", "hidden_ood"}]
    hidden_quality = _mean(float(row["metrics"]["quality"]) for row in hidden)
    slices: Dict[str, List[float]] = {}
    for row in hidden:
        slices.setdefault(row["slice"], []).append(float(row["metrics"]["quality"]))
    worst_slice = min((_mean(values) for values in slices.values()), default=0.0)
    hard_constraint_pass = _mean(float(row["metrics"]["hard_constraint"]) for row in own)
    red_rows = [row for row in own if row["split"] == "redteam"]
    redteam_pass = _mean(float(row["metrics"]["redteam"]) for row in red_rows)
    reg_rows = [row for row in own if row["split"] == "regression"]
    regression_retention = _mean(float(row["metrics"]["regression"]) for row in reg_rows)
    failures = sorted({failure for row in own for failure in row["hard_failures"]})
    costs = {key: sum(float(row["cost"][key]) for row in own) for key in own[0]["cost"]}
    task_scores: Dict[str, float] = {}
    for row in own:
        key = "%s|%s|%s|%s" % (row["task_id"], row["split"], row["slice"], row["repetition"])
        quality = float(row["metrics"]["quality"])
        hard = float(row["metrics"]["hard_constraint"])
        extra = quality
        if row["split"] == "redteam":
            extra = float(row["metrics"]["redteam"])
        elif row["split"] == "regression":
            extra = float(row["metrics"]["regression"])
        task_scores[key] = 0.65 * quality + 0.20 * hard + 0.15 * extra
    return {
        "participant_id": pid,
        "hidden_quality": hidden_quality,
        "worst_slice": worst_slice,
        "hard_constraint_pass": hard_constraint_pass,
        "redteam_pass": redteam_pass,
        "regression_retention": regression_retention,
        "hard_failures": failures,
        "costs": costs,
        "budget_used": costs[budget_metric],
        "task_scores": task_scores,
    }


def _effective_level(spec: Dict[str, Any]) -> Tuple[str, List[str]]:
    declared = spec["declared_evidence_level"]
    cap = LEVEL_ORDER.index(declared)
    reasons: List[str] = []
    for participant in spec["participants"]:
        adapter = participant["adapter"]
        if not adapter.get("native_execution") or not adapter.get("official_implementation"):
            if cap > 1:
                cap = 1
            reasons.append("%s 不是官方原生执行，证据最高 L2" % participant["id"])
    protocol = spec["protocol"]
    if declared == "L4" and not (protocol.get("production_blind") is True and protocol.get("authorized_real_users") is True):
        cap = min(cap, 2)
        reasons.append("缺少授权真实用户或生产盲测，不能达到 L4")
    if declared == "L3" and spec["mode"] != "sealed":
        reasons.append("L3 原生结果来自开发场时不能替代正式密封终审")
    return LEVEL_ORDER[cap], reasons


def _paired_bootstrap(candidate: Dict[str, float], peer: Dict[str, float], samples: int, seed: int) -> Dict[str, Any]:
    keys = sorted(set(candidate) & set(peer))
    diffs = [candidate[key] - peer[key] for key in keys]
    if not diffs:
        return {"mean_difference": 0.0, "ci95_low": 0.0, "ci95_high": 0.0, "probability_positive": 0.0, "paired_n": 0}
    rng = random.Random(seed)
    boot = []
    n = len(diffs)
    for _ in range(samples):
        total = 0.0
        for _ in range(n):
            total += diffs[rng.randrange(n)]
        boot.append(total / n)
    boot.sort()
    low_idx = max(0, int(0.025 * (len(boot) - 1)))
    high_idx = min(len(boot) - 1, int(0.975 * (len(boot) - 1)))
    return {
        "mean_difference": _mean(diffs),
        "ci95_low": boot[low_idx],
        "ci95_high": boot[high_idx],
        "probability_positive": sum(1 for value in boot if value > 0) / len(boot),
        "paired_n": n,
    }


def _pareto_front(aggregates: List[Dict[str, Any]]) -> List[str]:
    eligible = [item for item in aggregates if not item["hard_failures"]]
    front = []
    maximize = ["hidden_quality", "worst_slice", "hard_constraint_pass", "redteam_pass", "regression_retention"]
    for item in eligible:
        dominated = False
        for other in eligible:
            if other is item:
                continue
            no_worse = all(other[key] >= item[key] - 1e-12 for key in maximize) and other["budget_used"] <= item["budget_used"] + 1e-12
            strictly = any(other[key] > item[key] + 1e-12 for key in maximize) or other["budget_used"] < item["budget_used"] - 1e-12
            if no_worse and strictly:
                dominated = True
                break
        if not dominated:
            front.append(item["participant_id"])
    return sorted(front)


def _governance_board(spec: Dict[str, Any]) -> List[Dict[str, Any]]:
    required = list(spec["protocol"]["governance_requirements"])
    board = []
    for participant in spec["participants"]:
        declared = set(participant["governance_capabilities"])
        covered = [cap for cap in required if cap in declared]
        board.append({
            "participant_id": participant["id"],
            "coverage": len(covered) / len(required),
            "covered": covered,
            "missing": [cap for cap in required if cap not in declared],
            "note": "治理覆盖不进入经验效果总分。",
        })
    board.sort(key=lambda item: (-item["coverage"], item["participant_id"]))
    for idx, item in enumerate(board, 1):
        item["rank"] = idx
    return board


def score_arena(spec_path: Path, observations_path: Path, output: Path, markdown_output: Optional[Path] = None) -> Dict[str, Any]:
    spec = read_json(spec_path)
    validate_spec(spec, require_frozen=True)
    rows = _load_observations(observations_path)
    validation = _validate_observations(spec, rows)
    budget_metric = validation["budget_metric"]
    aggregates = [_aggregate_participant(participant["id"], rows, budget_metric) for participant in spec["participants"]]
    # Relative cost-efficiency is normalized only within the frozen fair field.
    raw_efficiency = {
        item["participant_id"]: item["hidden_quality"] / max(float(item["budget_used"]), 1e-12)
        for item in aggregates
    }
    max_efficiency = max(raw_efficiency.values())
    weights = {item["id"]: float(item["weight"]) for item in spec["protocol"]["dimensions"]}
    for item in aggregates:
        item["cost_efficiency"] = raw_efficiency[item["participant_id"]] / max_efficiency if max_efficiency > 0 else 0.0
        item["score"] = sum(weights[key] * float(item[key]) for key in REQUIRED_DIMENSIONS)
        item["blocked"] = bool(item["hard_failures"])
    eligible = [item for item in aggregates if not item["blocked"]]
    eligible.sort(key=lambda item: (-item["score"], item["budget_used"], item["participant_id"]))
    leaderboard = []
    rank = 0
    for item in eligible:
        rank += 1
        leaderboard.append({
            "rank": rank, "participant_id": item["participant_id"], "score": item["score"],
            **{key: item[key] for key in REQUIRED_DIMENSIONS},
            "budget_used": item["budget_used"], "hard_failures": [],
        })
    for item in sorted((item for item in aggregates if item["blocked"]), key=lambda x: x["participant_id"]):
        leaderboard.append({
            "rank": None, "participant_id": item["participant_id"], "score": item["score"],
            **{key: item[key] for key in REQUIRED_DIMENSIONS},
            "budget_used": item["budget_used"], "hard_failures": item["hard_failures"],
        })
    candidate_id = spec["candidate_participant_id"]
    candidate = next(item for item in aggregates if item["participant_id"] == candidate_id)
    samples = spec["protocol"]["bootstrap_samples"]
    seed = spec["protocol"]["bootstrap_seed"]
    pairwise = []
    for idx, peer in enumerate(aggregates):
        if peer["participant_id"] == candidate_id:
            continue
        pair = _paired_bootstrap(candidate["task_scores"], peer["task_scores"], samples, seed + idx)
        pair.update({"candidate_id": candidate_id, "peer_id": peer["participant_id"]})
        pairwise.append(pair)
    governance = _governance_board(spec)
    pareto = _pareto_front(aggregates)
    effective_level, level_reasons = _effective_level(spec)
    candidate_pair = None
    baselines = [item for item in spec["participants"] if item["role"] == "baseline"]
    if baselines:
        baseline_id = baselines[0]["id"]
        candidate_pair = next((item for item in pairwise if item["peer_id"] == baseline_id), None)
    if spec["mode"] == "sealed":
        status = "BLOCKED" if candidate["blocked"] else "ARENA_EVIDENCE_READY"
    else:
        if candidate["blocked"]:
            status = "DEGRADED"
        elif candidate_pair is None or validation["tasks_per_participant"] < 4:
            status = "INSUFFICIENT_EVIDENCE"
        elif candidate_pair["mean_difference"] > 0.005 and candidate_pair["ci95_low"] > 0:
            status = "IMPROVED"
        elif candidate_pair["mean_difference"] < -0.005 or candidate_pair["ci95_high"] < 0:
            status = "DEGRADED"
        else:
            status = "REHEAT_REQUIRED"
    hard_failures = [
        {"participant_id": item["participant_id"], "categories": item["hard_failures"]}
        for item in aggregates if item["hard_failures"]
    ]
    budget_ledger = [
        {"participant_id": item["participant_id"], **item["costs"], "budget_metric": budget_metric, "budget_used": item["budget_used"]}
        for item in aggregates
    ]
    result = {
        "schema_version": "teleiosis.arena_result.v1",
        "arena_id": spec["arena_id"],
        "status": status,
        "mode": spec["mode"],
        "protocol_hash": spec["freeze"]["protocol_hash"],
        "declared_evidence_level": spec["declared_evidence_level"],
        "effective_evidence_level": effective_level,
        "evidence_level_reasons": level_reasons,
        "empirical_leaderboard": leaderboard,
        "governance_board": governance,
        "pareto_front": pareto,
        "pairwise": pairwise,
        "budget_ledger": budget_ledger,
        "hard_gate_failures": hard_failures,
        "sample": {"observations": len(rows), "tasks_per_participant": validation["tasks_per_participant"], "repetitions": spec["protocol"]["repetitions"], "bootstrap_samples": samples},
        "truth_boundary": "Arena 只产证；低于 L3 不代表官方原生产品胜负；formal PASS 仅来自外部独立 Verifier。",
    }
    atomic_write_json(output, result)
    if markdown_output is None:
        markdown_output = output.with_suffix(".md")
    atomic_write_text(markdown_output, render_markdown(spec, result))
    return {"status": status, "output": str(output), "markdown": str(markdown_output), "effective_evidence_level": effective_level, "leader": leaderboard[0]["participant_id"] if leaderboard and leaderboard[0]["rank"] == 1 else None}


def render_markdown(spec: Dict[str, Any], result: Dict[str, Any]) -> str:
    lines = [
        "# Arena Lab 同场竞技结果", "",
        "- Arena：`%s`" % result["arena_id"],
        "- 模式：`%s`" % result["mode"],
        "- 状态：`%s`" % result["status"],
        "- 有效证据等级：`%s`" % result["effective_evidence_level"],
        "- 协议哈希：`%s`" % result["protocol_hash"], "",
        "## 经验效果主榜", "",
        "| 排名 | 参赛对象 | 总分 | 隐藏质量 | 最弱切片 | 硬约束 | 红队 | 回归 | 成本效率 | 预算 |",
        "|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in result["empirical_leaderboard"]:
        rank = "BLOCKED" if row["rank"] is None else str(row["rank"])
        lines.append("| %s | %s | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.2f%% | %.4f |" % (
            rank, row["participant_id"], row["score"] * 100, row["hidden_quality"] * 100,
            row["worst_slice"] * 100, row["hard_constraint_pass"] * 100, row["redteam_pass"] * 100,
            row["regression_retention"] * 100, row["cost_efficiency"] * 100, row["budget_used"],
        ))
    lines.extend(["", "## 治理能力榜（不进入经验总分）", "", "| 排名 | 参赛对象 | 覆盖率 | 缺失 |", "|---:|---|---:|---|"])
    for row in result["governance_board"]:
        lines.append("| %s | %s | %.2f%% | %s |" % (row["rank"], row["participant_id"], row["coverage"] * 100, "、".join(row["missing"]) or "无"))
    lines.extend(["", "## Pareto 前沿", "", "、".join(result["pareto_front"]) or "无", "", "## 证据边界", "", result["truth_boundary"]])
    return "\n".join(lines) + "\n"


def execute_command_adapter(spec_path: Path, participant_id: str, input_path: Path, output_path: Path, receipt_path: Path) -> Dict[str, Any]:
    spec = read_json(spec_path)
    validate_spec(spec, require_frozen=True)
    participant = next((item for item in spec["participants"] if item["id"] == participant_id), None)
    if participant is None:
        raise TeleiosisError("ADAPTER_PARTICIPANT", "参赛对象不存在。", {"participant": participant_id})
    adapter = participant["adapter"]
    if adapter.get("kind") != "command":
        raise TeleiosisError("ADAPTER_KIND", "该参赛对象不是 command adapter。")
    command = adapter.get("command")
    timeout = adapter.get("timeout_seconds", 600)
    cwd = adapter.get("cwd")
    if not isinstance(command, list) or not command or any(not isinstance(part, str) or not part for part in command):
        raise TeleiosisError("ADAPTER_COMMAND", "command 必须是非空字符串数组，禁止 shell 字符串。")
    if not isinstance(timeout, int) or timeout < 1 or timeout > 86400:
        raise TeleiosisError("ADAPTER_TIMEOUT", "timeout_seconds 必须在 1—86400。")
    executable = command[0]
    if os.path.isabs(executable):
        if not Path(executable).is_file():
            raise TeleiosisError("ADAPTER_EXECUTABLE", "Adapter 可执行文件不存在。", {"path": executable})
    elif shutil.which(executable) is None:
        raise TeleiosisError("ADAPTER_EXECUTABLE", "Adapter 命令不在 PATH。", {"command": executable})
    if not input_path.is_file() or input_path.is_symlink():
        raise TeleiosisError("ADAPTER_INPUT", "Adapter 输入必须是普通文件。")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", ""), "LANG": os.environ.get("LANG", "C.UTF-8"), "LC_ALL": os.environ.get("LC_ALL", "C.UTF-8")}
    env.update({
        "TELEIOSIS_ARENA_SPEC": str(spec_path.resolve()),
        "TELEIOSIS_ARENA_INPUT": str(input_path.resolve()),
        "TELEIOSIS_ARENA_OUTPUT": str(output_path.resolve()),
        "TELEIOSIS_PARTICIPANT_ID": participant_id,
    })
    process = subprocess.Popen(
        command, cwd=cwd or None, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=False, start_new_session=True,
    )
    try:
        stdout, stderr = process.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except OSError:
            pass
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except OSError:
                pass
            stdout, stderr = process.communicate()
        raise TeleiosisError("ADAPTER_TIMEOUT", "Adapter 超时并已清理进程组。", {"participant": participant_id, "timeout_seconds": timeout})
    cap = 4 * 1024 * 1024
    stdout_tail = stdout[-cap:].decode("utf-8", errors="replace")
    stderr_tail = stderr[-cap:].decode("utf-8", errors="replace")
    receipt = {
        "schema_version": "teleiosis.command_adapter_receipt.v1",
        "participant_id": participant_id,
        "command": command,
        "returncode": process.returncode,
        "input_sha256": sha256_file(input_path),
        "output_exists": output_path.is_file() and not output_path.is_symlink(),
        "output_sha256": sha256_file(output_path) if output_path.is_file() and not output_path.is_symlink() else None,
        "stdout_tail": stdout_tail,
        "stderr_tail": stderr_tail,
        "native_execution": bool(adapter.get("native_execution")),
        "official_implementation": bool(adapter.get("official_implementation")),
    }
    atomic_write_json(receipt_path, receipt)
    if process.returncode != 0 or not receipt["output_exists"]:
        raise TeleiosisError("ADAPTER_FAILED", "Adapter 执行失败或未生成输出。", {"participant": participant_id, "returncode": process.returncode, "receipt": str(receipt_path)})
    return {"status": "ADAPTER_COMPLETED", "receipt": str(receipt_path), "output": str(output_path), "output_sha256": receipt["output_sha256"]}
