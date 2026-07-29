from __future__ import annotations

import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

from .common import ValidationError, object_sha256, strip_internal_fields

TOKEN_RE = re.compile(r"[\w\u4e00-\u9fff]+", re.UNICODE)
VISIBLE_PARTITIONS = {"development", "validation", "adversarial", "market_live", "incident_replay"}


def _tokens(text: str) -> List[str]:
    return [item.lower() for item in TOKEN_RE.findall(text)]


def _shingles(text: str, width: int = 3) -> set[str]:
    tokens = _tokens(text)
    if not tokens:
        return set()
    if len(tokens) < width:
        return {"\x1f".join(tokens)}
    return {"\x1f".join(tokens[index : index + width]) for index in range(len(tokens) - width + 1)}


def jaccard_similarity(left: str, right: str) -> float:
    a, b = _shingles(left), _shingles(right)
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def task_signature(task: Mapping[str, Any]) -> str:
    return object_sha256(
        {
            "prompt": " ".join(_tokens(str(task.get("prompt", "")))),
            "oracle": task.get("oracle"),
            "origin": task.get("origin"),
        }
    )


def contamination_audit(
    tasks: Iterable[Mapping[str, Any]],
    threshold: float = 0.82,
    max_candidates_per_holdout: int = 5000,
) -> Dict[str, Any]:
    """Detect exact and near duplicates without O(holdout*visible) full scanning.

    A shingle inverted index narrows candidate pairs. If a holdout task maps to more
    candidates than the explicit ceiling, the audit fails closed rather than silently
    skipping a potentially contaminated corpus.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValidationError("contamination threshold 必须在 0–1")
    if max_candidates_per_holdout < 1:
        raise ValidationError("max_candidates_per_holdout 必须 >= 1")
    rows = [strip_internal_fields(row) for row in tasks]
    exact: Dict[str, List[Mapping[str, Any]]] = defaultdict(list)
    for row in rows:
        exact[task_signature(row)].append(row)

    findings: List[Dict[str, Any]] = []
    for signature, group in exact.items():
        partitions = {str(item.get("partition")) for item in group}
        if "sealed_holdout" in partitions and partitions & VISIBLE_PARTITIONS:
            findings.append(
                {
                    "type": "exact_cross_partition_duplicate",
                    "signature": signature,
                    "task_ids": sorted(str(item.get("task_id")) for item in group),
                    "partitions": sorted(partitions),
                    "severity": "blocking",
                }
            )

    holdout = [row for row in rows if row.get("partition") == "sealed_holdout"]
    visible = [row for row in rows if row.get("partition") in VISIBLE_PARTITIONS]
    visible_shingles: List[set[str]] = []
    inverted: Dict[str, set[int]] = defaultdict(set)
    for index, row in enumerate(visible):
        shingles = _shingles(str(row.get("prompt", "")))
        visible_shingles.append(shingles)
        for shingle in shingles:
            inverted[shingle].add(index)

    checked_pairs = 0
    for secret in holdout:
        secret_shingles = _shingles(str(secret.get("prompt", "")))
        candidates: set[int] = set()
        for shingle in secret_shingles:
            candidates.update(inverted.get(shingle, set()))
        if len(candidates) > max_candidates_per_holdout:
            findings.append(
                {
                    "type": "candidate_set_overflow",
                    "holdout_task_id": secret.get("task_id"),
                    "candidate_count": len(candidates),
                    "ceiling": max_candidates_per_holdout,
                    "severity": "blocking",
                }
            )
            continue
        for index in sorted(candidates):
            public = visible[index]
            union = secret_shingles | visible_shingles[index]
            score = len(secret_shingles & visible_shingles[index]) / len(union) if union else 1.0
            checked_pairs += 1
            if score >= threshold:
                findings.append(
                    {
                        "type": "near_duplicate_cross_partition",
                        "holdout_task_id": secret.get("task_id"),
                        "visible_task_id": public.get("task_id"),
                        "similarity": round(score, 6),
                        "threshold": threshold,
                        "severity": "blocking",
                    }
                )

    result = {
        "valid": not findings,
        "status": "PASS" if not findings else "BLOCKED",
        "tasks": len(rows),
        "holdout_tasks": len(holdout),
        "visible_tasks": len(visible),
        "candidate_pairs_checked": checked_pairs,
        "threshold": threshold,
        "max_candidates_per_holdout": max_candidates_per_holdout,
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _inverse_normal(probability: float) -> float:
    if not 0.0 < probability < 1.0:
        raise ValidationError("inverse normal probability 必须在 0–1")
    low, high = -8.0, 8.0
    for _ in range(100):
        mid = (low + high) / 2.0
        if _normal_cdf(mid) < probability:
            low = mid
        else:
            high = mid
    return (low + high) / 2.0


def _chi_square_survival(statistic: float, degrees_of_freedom: int) -> float:
    if statistic < 0 or degrees_of_freedom < 1:
        raise ValidationError("chi-square 输入无效")
    if degrees_of_freedom == 1:
        return math.erfc(math.sqrt(statistic / 2.0))
    z = ((statistic / degrees_of_freedom) ** (1.0 / 3.0) - (1.0 - 2.0 / (9.0 * degrees_of_freedom))) / math.sqrt(
        2.0 / (9.0 * degrees_of_freedom)
    )
    return max(0.0, min(1.0, 1.0 - _normal_cdf(z)))


def _blind_mapping(blind_map: Mapping[str, Any] | None) -> Mapping[str, str]:
    if blind_map is None:
        return {}
    mapping = blind_map.get("mapping", blind_map)
    if not isinstance(mapping, Mapping):
        raise ValidationError("blind_map.mapping 必须是对象")
    return {str(key): str(value) for key, value in mapping.items()}


def resolve_assignment_arm(row: Mapping[str, Any], blind_map: Mapping[str, Any] | None = None) -> str | None:
    if row.get("arm_id") is not None:
        return str(row["arm_id"])
    code = row.get("condition_code")
    if code is None:
        return None
    mapping = _blind_mapping(blind_map)
    return mapping.get(str(code), str(code) if not mapping else None)


def sample_ratio_mismatch(
    assignments: Iterable[Mapping[str, Any]],
    expected_weights: Mapping[str, float],
    blind_map: Mapping[str, Any] | None = None,
    alpha: float = 0.001,
) -> Dict[str, Any]:
    if not 0 < alpha < 1:
        raise ValidationError("SRM alpha 必须在 0–1")
    if not expected_weights or any(isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0 for value in expected_weights.values()):
        raise ValidationError("expected_weights 必须为正数")
    observed: Counter[str] = Counter()
    unresolved = 0
    for row in assignments:
        arm = resolve_assignment_arm(row, blind_map)
        if arm is None:
            unresolved += 1
        else:
            observed[arm] += 1
    total = sum(observed.values())
    weight_sum = float(sum(expected_weights.values()))
    expected_counts: Dict[str, float] = {}
    statistic = 0.0
    for arm, weight in expected_weights.items():
        expected = total * float(weight) / weight_sum
        expected_counts[str(arm)] = expected
        if expected:
            statistic += (observed.get(str(arm), 0) - expected) ** 2 / expected
    unknown = sorted(set(observed) - set(expected_weights))
    if unknown or unresolved or total == 0:
        p_value = 0.0
    else:
        p_value = _chi_square_survival(statistic, max(1, len(expected_weights) - 1))
    valid = total > 0 and not unknown and unresolved == 0 and p_value >= alpha
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "total": total,
        "observed": dict(sorted(observed.items())),
        "expected": {key: round(value, 6) for key, value in sorted(expected_counts.items())},
        "statistic": round(statistic, 8),
        "p_value": round(p_value, 12),
        "alpha": alpha,
        "unknown_arms": unknown,
        "unresolved_assignments": unresolved,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def paired_assignment_integrity(
    assignments: Iterable[Mapping[str, Any]],
    expected_arms: Sequence[str],
    blind_map: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate full-factorial paired lab assignment, where multi-arm exposure is expected."""
    expected = set(map(str, expected_arms))
    groups: Dict[Tuple[str, int], List[str]] = defaultdict(list)
    missing = 0
    for row in assignments:
        task_id = row.get("task_id")
        repetition = row.get("repetition")
        arm = resolve_assignment_arm(row, blind_map)
        if task_id is None or not isinstance(repetition, int) or arm is None:
            missing += 1
            continue
        groups[(str(task_id), repetition)].append(arm)
    findings: List[Dict[str, Any]] = []
    for (task_id, repetition), arms in sorted(groups.items()):
        counts = Counter(arms)
        actual = set(counts)
        duplicates = sorted(arm for arm, count in counts.items() if count != 1)
        if actual != expected or duplicates:
            findings.append(
                {
                    "task_id": task_id,
                    "repetition": repetition,
                    "missing_arms": sorted(expected - actual),
                    "unknown_arms": sorted(actual - expected),
                    "duplicate_arms": duplicates,
                }
            )
    valid = missing == 0 and bool(groups) and not findings
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "design": "paired_full_factorial",
        "paired_units": len(groups),
        "missing_identity": missing,
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def exclusive_assignment_integrity(
    assignments: Iterable[Mapping[str, Any]],
    unit_key: str = "unit_id",
    blind_map: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    """Validate online/Canary assignment, where each real unit must see one arm only."""
    seen: Dict[str, set[str]] = defaultdict(set)
    missing = 0
    for row in assignments:
        unit = row.get(unit_key)
        arm = resolve_assignment_arm(row, blind_map)
        if unit is None or arm is None:
            missing += 1
            continue
        seen[str(unit)].add(arm)
    multiple = {unit: sorted(arms) for unit, arms in seen.items() if len(arms) > 1}
    valid = missing == 0 and bool(seen) and not multiple
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "design": "exclusive_online_assignment",
        "units": len(seen),
        "missing_identity": missing,
        "multiple_exposure_units": multiple,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def environment_fingerprint(record: Mapping[str, Any], required_fields: Sequence[str]) -> str:
    environment = record.get("environment") if isinstance(record.get("environment"), Mapping) else record
    selected = {field: environment.get(field) for field in required_fields}
    return object_sha256(selected)


def environment_parity(records: Iterable[Mapping[str, Any]], required_fields: Sequence[str]) -> Dict[str, Any]:
    if not required_fields:
        raise ValidationError("environment required_fields 不能为空")
    by_pair: Dict[Tuple[str, int], Dict[str, set[str]]] = defaultdict(lambda: defaultdict(set))
    incomplete: List[Dict[str, Any]] = []
    for row in records:
        environment = row.get("environment") if isinstance(row.get("environment"), Mapping) else row
        missing = [field for field in required_fields if environment.get(field) is None]
        if missing:
            incomplete.append({"run_id": row.get("run_id"), "missing_fields": missing})
        key = (str(row.get("task_id")), int(row.get("repetition", 0)))
        by_pair[key][str(row.get("arm_id"))].add(environment_fingerprint(row, required_fields))
    mismatches: List[Dict[str, Any]] = []
    for (task_id, repetition), arms in by_pair.items():
        union = set().union(*arms.values()) if arms else set()
        if len(union) > 1:
            mismatches.append(
                {
                    "task_id": task_id,
                    "repetition": repetition,
                    "arm_fingerprints": {arm: sorted(values) for arm, values in sorted(arms.items())},
                }
            )
    valid = bool(by_pair) and not incomplete and not mismatches
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "paired_units": len(by_pair),
        "required_fields": list(required_fields),
        "incomplete": incomplete,
        "mismatches": mismatches,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def required_sample_size_two_proportions(
    baseline_rate: float,
    minimum_detectable_effect: float,
    alpha: float = 0.05,
    power: float = 0.8,
) -> int:
    if not 0 < baseline_rate < 1:
        raise ValidationError("baseline_rate 必须在 0–1")
    if minimum_detectable_effect == 0 or not -baseline_rate < minimum_detectable_effect < 1 - baseline_rate:
        raise ValidationError("minimum_detectable_effect 超出可行范围")
    if not 0 < alpha < 1 or not 0 < power < 1:
        raise ValidationError("alpha/power 必须在 0–1")
    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    p_bar = (p1 + p2) / 2.0
    z_alpha = _inverse_normal(1.0 - alpha / 2.0)
    z_power = _inverse_normal(power)
    numerator = (
        z_alpha * math.sqrt(2.0 * p_bar * (1.0 - p_bar))
        + z_power * math.sqrt(p1 * (1.0 - p1) + p2 * (1.0 - p2))
    ) ** 2
    return int(math.ceil(numerator / ((p2 - p1) ** 2)))


def power_plan(spec: Mapping[str, Any]) -> Dict[str, Any]:
    plan = spec.get("analysis_plan") or {}
    mode = plan.get("mode")
    findings: List[str] = []
    required: int | None = None
    planned = plan.get("planned_sample_size_per_arm")
    if mode == "fixed_horizon":
        try:
            required = required_sample_size_two_proportions(
                float(plan["baseline_rate"]),
                float(plan["minimum_detectable_effect"]),
                float(plan["alpha"]),
                float(plan["power"]),
            )
        except (KeyError, TypeError, ValueError, ValidationError) as exc:
            findings.append(str(exc))
        if plan.get("allow_peeking") is not False:
            findings.append("fixed_horizon 必须 allow_peeking=false")
        if required is not None and (not isinstance(planned, int) or isinstance(planned, bool) or planned < required):
            findings.append(f"planned_sample_size_per_arm={planned} 小于 required={required}")
    elif mode == "sequential":
        if plan.get("allow_peeking") is not True or not plan.get("sequential_method"):
            findings.append("sequential 必须冻结 sequential_method 且 allow_peeking=true")
        if not isinstance(plan.get("max_sample_size_per_arm"), int) or plan.get("max_sample_size_per_arm", 0) < 1:
            findings.append("sequential 必须声明 max_sample_size_per_arm >= 1")
        if plan.get("stop_rules_predeclared") is not True:
            findings.append("sequential 必须 stop_rules_predeclared=true")
    else:
        findings.append("analysis_plan.mode 必须为 fixed_horizon 或 sequential")
    valid = not findings
    result = {
        "valid": valid,
        "status": "PASS" if valid else "REHEAT_REQUIRED",
        "mode": mode,
        "required_sample_size_per_arm": required,
        "planned_sample_size_per_arm": planned,
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def _cohen_kappa(left: Sequence[str], right: Sequence[str]) -> float:
    if len(left) != len(right) or not left:
        raise ValidationError("judge calibration 标签长度必须相同且非空")
    labels = sorted(set(left) | set(right))
    observed = sum(a == b for a, b in zip(left, right)) / len(left)
    left_counts, right_counts = Counter(left), Counter(right)
    expected = sum((left_counts[label] / len(left)) * (right_counts[label] / len(right)) for label in labels)
    if expected == 1.0:
        return 1.0 if observed == 1.0 else 0.0
    return (observed - expected) / (1.0 - expected)


def judge_calibration(rows: Iterable[Mapping[str, Any]], policy: Mapping[str, Any]) -> Dict[str, Any]:
    enabled = bool(policy.get("enabled", False))
    if not enabled:
        result = {"valid": True, "status": "NOT_APPLICABLE", "enabled": False, "cases": 0, "findings": []}
        result["audit_digest"] = object_sha256(result)
        return result
    records = [strip_internal_fields(row) for row in rows]
    gold: List[str] = []
    judge: List[str] = []
    missing = 0
    for row in records:
        if row.get("gold_label") is None or row.get("judge_label") is None:
            missing += 1
        else:
            gold.append(str(row["gold_label"]))
            judge.append(str(row["judge_label"]))
    agreement = sum(a == b for a, b in zip(gold, judge)) / len(gold) if gold else 0.0
    kappa = _cohen_kappa(gold, judge) if gold else 0.0
    findings: List[str] = []
    if missing:
        findings.append(f"{missing} 条校准记录缺少 gold_label/judge_label")
    min_cases = int(policy.get("minimum_calibration_cases", 20))
    min_agreement = float(policy.get("minimum_agreement", 0.8))
    min_kappa = float(policy.get("minimum_kappa", 0.6))
    if len(gold) < min_cases:
        findings.append(f"calibration cases {len(gold)} < {min_cases}")
    if agreement < min_agreement:
        findings.append(f"agreement {agreement:.4f} < {min_agreement:.4f}")
    if kappa < min_kappa:
        findings.append(f"cohens_kappa {kappa:.4f} < {min_kappa:.4f}")
    valid = not findings
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "enabled": True,
        "cases": len(gold),
        "agreement": round(agreement, 8),
        "cohens_kappa": round(kappa, 8),
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def _parse_timestamp(value: Any) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    text = value.strip().replace("Z", "+00:00")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def market_temporal_integrity(feedback: Iterable[Mapping[str, Any]], spec: Mapping[str, Any]) -> Dict[str, Any]:
    rows = [strip_internal_fields(row) for row in feedback]
    target = str(spec.get("evidence_target", "lab"))
    if not rows and target == "lab":
        result = {"valid": True, "status": "NOT_APPLICABLE", "events": 0, "findings": []}
        result["audit_digest"] = object_sha256(result)
        return result
    window = spec.get("market_window") or {}
    as_of = _parse_timestamp(window.get("as_of"))
    findings: List[str] = []
    if as_of is None:
        findings.append("market_window.as_of 无效")
        as_of = datetime.now(timezone.utc)
    max_age_days = float(window.get("max_age_days", 30))
    max_skew_hours = float(window.get("max_arm_skew_hours", 24))
    ids: Counter[str] = Counter()
    by_arm: Dict[str, List[datetime]] = defaultdict(list)
    invalid_timestamps = 0
    stale = 0
    future = 0
    for row in rows:
        ids[str(row.get("event_id"))] += 1
        timestamp = _parse_timestamp(row.get("timestamp"))
        if timestamp is None:
            invalid_timestamps += 1
            continue
        if timestamp > as_of:
            future += 1
        if (as_of - timestamp).total_seconds() > max_age_days * 86400:
            stale += 1
        by_arm[str(row.get("arm_id"))].append(timestamp)
    duplicates = sorted(key for key, count in ids.items() if count > 1)
    if duplicates:
        findings.append(f"duplicate event_id: {duplicates[:20]}")
    if invalid_timestamps:
        findings.append(f"invalid timestamps: {invalid_timestamps}")
    if stale:
        findings.append(f"stale market events: {stale}")
    if future:
        findings.append(f"future market events: {future}")
    medians: Dict[str, float] = {}
    for arm, values in by_arm.items():
        epochs = sorted(item.timestamp() for item in values)
        medians[arm] = epochs[len(epochs) // 2]
    if len(medians) >= 2 and (max(medians.values()) - min(medians.values())) / 3600 > max_skew_hours:
        findings.append("market arm median timestamp skew exceeds limit")
    valid = bool(rows) and not findings
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "events": len(rows),
        "invalid_timestamps": invalid_timestamps,
        "stale_events": stale,
        "future_events": future,
        "duplicate_event_ids": duplicates,
        "arm_median_skew_hours": round((max(medians.values()) - min(medians.values())) / 3600, 6) if len(medians) >= 2 else 0.0,
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def referential_integrity(
    tasks: Iterable[Mapping[str, Any]],
    results: Iterable[Mapping[str, Any]],
    feedback: Iterable[Mapping[str, Any]],
    spec: Mapping[str, Any],
) -> Dict[str, Any]:
    task_rows = [strip_internal_fields(row) for row in tasks]
    result_rows = [strip_internal_fields(row) for row in results]
    feedback_rows = [strip_internal_fields(row) for row in feedback]
    task_by_id = {str(row.get("task_id")): row for row in task_rows}
    arm_by_id = {str(arm["id"]): arm for arm in spec.get("arms", [])}
    run_by_id: Dict[str, Mapping[str, Any]] = {}
    findings: List[Dict[str, Any]] = []
    if len(task_by_id) != len(task_rows):
        findings.append({"code": "DUPLICATE_TASK_ID", "detail": "任务集中存在重复 task_id"})
    for row in result_rows:
        run_id = str(row.get("run_id"))
        task_id = str(row.get("task_id"))
        arm_id = str(row.get("arm_id"))
        if run_id in run_by_id:
            findings.append({"code": "DUPLICATE_RUN_ID", "run_id": run_id})
        run_by_id[run_id] = row
        if task_id not in task_by_id:
            findings.append({"code": "RESULT_ORPHAN_TASK", "run_id": run_id, "task_id": task_id})
        elif row.get("partition") != task_by_id[task_id].get("partition"):
            findings.append({"code": "RESULT_PARTITION_MISMATCH", "run_id": run_id, "task_id": task_id})
        arm = arm_by_id.get(arm_id)
        if arm is None:
            findings.append({"code": "RESULT_UNKNOWN_ARM", "run_id": run_id, "arm_id": arm_id})
        else:
            expected = None if arm.get("kind") == "no_skill" else arm.get("artifact_digest")
            if row.get("artifact_digest") != expected:
                findings.append({"code": "RESULT_ARTIFACT_MISMATCH", "run_id": run_id, "arm_id": arm_id})
        if row.get("experiment_id") != spec.get("experiment_id"):
            findings.append({"code": "RESULT_EXPERIMENT_MISMATCH", "run_id": run_id})
    event_ids: set[str] = set()
    for row in feedback_rows:
        event_id = str(row.get("event_id"))
        run_id = str(row.get("run_id"))
        if event_id in event_ids:
            findings.append({"code": "DUPLICATE_EVENT_ID", "event_id": event_id})
        event_ids.add(event_id)
        run = run_by_id.get(run_id)
        if run is None:
            findings.append({"code": "FEEDBACK_ORPHAN_RUN", "event_id": event_id, "run_id": run_id})
            continue
        for field in ("task_id", "arm_id", "artifact_digest", "experiment_id"):
            if row.get(field) != run.get(field):
                findings.append({"code": "FEEDBACK_RUN_MISMATCH", "event_id": event_id, "field": field})
    valid = not findings
    result = {
        "valid": valid,
        "status": "PASS" if valid else "BLOCKED",
        "tasks": len(task_rows),
        "results": len(result_rows),
        "feedback": len(feedback_rows),
        "findings": findings,
    }
    result["audit_digest"] = object_sha256(result)
    return result


def evidence_chain_digest(parts: Mapping[str, Any]) -> Dict[str, Any]:
    required = [
        "subject_digest",
        "spec_digest",
        "dataset_digest",
        "assignment_digest",
        "result_digest",
        "quality_audit_digest",
        "summary_digest",
        "gate_digest",
    ]
    missing = [key for key in required if not isinstance(parts.get(key), str) or not str(parts.get(key)).strip()]
    payload = {key: parts.get(key) for key in required}
    result = {
        "valid": not missing,
        "status": "PASS" if not missing else "BLOCKED",
        "missing": missing,
        "parts": payload,
    }
    result["evidence_chain_digest"] = object_sha256(payload) if not missing else None
    return result


def quality_audit(
    spec: Mapping[str, Any],
    tasks: Iterable[Mapping[str, Any]],
    assignments: Iterable[Mapping[str, Any]],
    results: Iterable[Mapping[str, Any]],
    feedback: Iterable[Mapping[str, Any]] = (),
    calibration: Iterable[Mapping[str, Any]] = (),
    blind_map: Mapping[str, Any] | None = None,
    assignment_mode: str = "paired",
) -> Dict[str, Any]:
    task_rows = [strip_internal_fields(row) for row in tasks]
    assignment_rows = [strip_internal_fields(row) for row in assignments]
    result_rows = [strip_internal_fields(row) for row in results]
    feedback_rows = [strip_internal_fields(row) for row in feedback]
    calibration_rows = [strip_internal_fields(row) for row in calibration]
    source_digests = {
        "tasks_digest": object_sha256(task_rows),
        "assignments_digest": object_sha256(assignment_rows),
        "results_digest": object_sha256(result_rows),
        "feedback_digest": object_sha256(feedback_rows),
        "calibration_digest": object_sha256(calibration_rows),
    }
    arm_ids = [str(arm["id"]) for arm in spec.get("arms", [])]
    assignment_guard = spec.get("assignment_guard") or {}
    if assignment_mode == "paired":
        assignment = paired_assignment_integrity(assignment_rows, arm_ids, blind_map)
    elif assignment_mode == "exclusive":
        assignment = exclusive_assignment_integrity(
            assignment_rows,
            unit_key=str(assignment_guard.get("unit_key", "unit_id")),
            blind_map=blind_map,
        )
    else:
        raise ValidationError("assignment_mode 必须是 paired 或 exclusive")
    reports = {
        "contamination": contamination_audit(
            task_rows,
            threshold=float((spec.get("contamination_policy") or {}).get("near_duplicate_threshold", 0.82)),
            max_candidates_per_holdout=int((spec.get("contamination_policy") or {}).get("max_candidates_per_holdout", 5000)),
        ),
        "assignment": assignment,
        "sample_ratio_mismatch": sample_ratio_mismatch(
            assignment_rows,
            expected_weights=assignment_guard.get("expected_weights") or {arm_id: 1.0 for arm_id in arm_ids},
            blind_map=blind_map,
            alpha=float(assignment_guard.get("srm_alpha", 0.001)),
        ),
        "environment_parity": environment_parity(
            result_rows,
            required_fields=(spec.get("environment_parity") or {}).get("required_fields")
            or ["model_snapshot", "runtime_version", "tools", "permissions", "budget", "system_digest", "dataset_digest"],
        ),
        "power_plan": power_plan(spec),
        "judge_calibration": judge_calibration(calibration_rows, spec.get("judge_policy") or {}),
        "market_temporal_integrity": market_temporal_integrity(feedback_rows, spec),
        "referential_integrity": referential_integrity(task_rows, result_rows, feedback_rows, spec),
    }
    blocking = [name for name, report in reports.items() if report.get("status") == "BLOCKED"]
    reheat = [name for name, report in reports.items() if report.get("status") == "REHEAT_REQUIRED"]
    valid = not blocking and not reheat
    result = {
        "schema_version": "2.0",
        "spec_digest": object_sha256(spec),
        "source_digests": source_digests,
        "valid": valid,
        "status": "PASS" if valid else ("BLOCKED" if blocking else "REHEAT_REQUIRED"),
        "assignment_mode": assignment_mode,
        "blocking_reports": blocking,
        "reheat_reports": reheat,
        "reports": reports,
        "quality_audit_digest": None,
    }
    result["quality_audit_digest"] = object_sha256({key: value for key, value in result.items() if key != "quality_audit_digest"})
    return result
