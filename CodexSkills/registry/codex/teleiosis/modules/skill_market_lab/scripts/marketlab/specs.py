from __future__ import annotations

import re
from typing import Any, Dict, List, Mapping, Sequence

from .common import ValidationError, as_number, require_keys

SCHEMA_VERSION = "1.0"
PARTITIONS = {
    "development",
    "validation",
    "sealed_holdout",
    "adversarial",
    "market_live",
    "incident_replay",
}
ARM_KINDS = {"no_skill", "baseline", "candidate", "competitor", "ablation"}
COMPETITOR_EVIDENCE_TYPES = {"real", "simulated", "proxy"}
EVIDENCE_TARGETS = {"lab", "market_partial", "market_validated"}
TASK_ORIGINS = {
    "synthetic",
    "historical_failure",
    "user_opt_in",
    "github_issue",
    "real_deliverable",
    "competitor_case",
    "red_team",
    "time_split",
    "negative_trigger",
    "production_incident",
}
RESULT_STATUSES = {"completed", "failed", "blocked", "not_run"}
EVIDENCE_KINDS = {
    "static",
    "offline",
    "simulation",
    "stress",
    "shadow",
    "canary",
    "external_acceptance",
    "economic",
    "retention",
    "incident",
}
FEEDBACK_SOURCES = {
    "opt_in_user",
    "blind_canary",
    "external_acceptor",
    "micro_bounty",
    "production_behavior",
    "retention_observation",
    "payment_observation",
    "incident_report",
}
COMPLETION_STATES = {"complete", "partial", "failed", "abandoned", "unknown"}
SEVERITIES = {"none", "low", "medium", "high", "critical"}
SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def _validate_id(value: Any, location: str, errors: List[str]) -> None:
    if not isinstance(value, str) or not SAFE_ID_PATTERN.fullmatch(value):
        errors.append(f"{location} 必须是 1–128 位安全标识符")


def validate_experiment_spec(spec: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(spec, dict):
        return ["实验规范必须是 JSON 对象"]

    errors.extend(
        require_keys(
            spec,
            [
                "schema_version",
                "experiment_id",
                "objective",
                "subject",
                "evidence_target",
                "arms",
                "repetitions",
                "seed",
                "budget",
                "gates",
                "privacy",
            ],
            "spec",
        )
    )
    if errors:
        return errors

    if spec.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"spec.schema_version 必须为 {SCHEMA_VERSION}")
    _validate_id(spec.get("experiment_id"), "spec.experiment_id", errors)
    if not isinstance(spec.get("objective"), str) or not spec["objective"].strip():
        errors.append("spec.objective 必须是非空字符串")
    if spec.get("evidence_target") not in EVIDENCE_TARGETS:
        errors.append(f"spec.evidence_target 必须属于 {sorted(EVIDENCE_TARGETS)}")

    subject = spec.get("subject")
    if not isinstance(subject, dict):
        errors.append("spec.subject 必须是对象")
    else:
        errors.extend(require_keys(subject, ["skill_name", "skill_version", "artifact_digest"], "spec.subject"))
        for key in ("skill_name", "skill_version", "artifact_digest"):
            if key in subject and (not isinstance(subject[key], str) or not subject[key].strip()):
                errors.append(f"spec.subject.{key} 必须是非空字符串")

    arms = spec.get("arms")
    if not isinstance(arms, list) or not arms:
        errors.append("spec.arms 必须是非空数组")
    else:
        seen_ids = set()
        seen_kinds: Dict[str, int] = {}
        for index, arm in enumerate(arms):
            location = f"spec.arms[{index}]"
            if not isinstance(arm, dict):
                errors.append(f"{location} 必须是对象")
                continue
            errors.extend(require_keys(arm, ["id", "kind", "label"], location))
            arm_id = arm.get("id")
            _validate_id(arm_id, f"{location}.id", errors)
            if arm_id in seen_ids:
                errors.append(f"{location}.id 重复: {arm_id}")
            seen_ids.add(arm_id)
            kind = arm.get("kind")
            if kind not in ARM_KINDS:
                errors.append(f"{location}.kind 必须属于 {sorted(ARM_KINDS)}")
            else:
                seen_kinds[kind] = seen_kinds.get(kind, 0) + 1
            if not isinstance(arm.get("label"), str) or not arm["label"].strip():
                errors.append(f"{location}.label 必须是非空字符串")
            if kind != "no_skill":
                digest = arm.get("artifact_digest")
                if not isinstance(digest, str) or not digest.strip():
                    errors.append(f"{location}.artifact_digest 必须绑定精确制品")
            if kind == "competitor":
                evidence_type = arm.get("competitor_evidence_type")
                if evidence_type not in COMPETITOR_EVIDENCE_TYPES:
                    errors.append(
                        f"{location}.competitor_evidence_type 必须属于 {sorted(COMPETITOR_EVIDENCE_TYPES)}"
                    )
                if evidence_type == "real" and not arm.get("source_reference"):
                    errors.append(f"{location}.source_reference 对真实竞品是必填项")
        if seen_kinds.get("no_skill", 0) != 1:
            errors.append("实验必须且只能包含一个 no_skill 永久对照臂")
        if seen_kinds.get("candidate", 0) != 1:
            errors.append("实验必须且只能包含一个 candidate 臂")
        if seen_kinds.get("baseline", 0) > 1:
            errors.append("实验最多包含一个 baseline 臂")

    repetitions = spec.get("repetitions")
    if isinstance(repetitions, bool) or not isinstance(repetitions, int) or repetitions < 1:
        errors.append("spec.repetitions 必须是 >= 1 的整数")
    seed = spec.get("seed")
    if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
        errors.append("spec.seed 必须是 >= 0 的整数")

    budget = spec.get("budget")
    if not isinstance(budget, dict):
        errors.append("spec.budget 必须是对象")
    else:
        for key in ("max_tasks", "max_tokens", "max_cost_usd", "max_wall_seconds"):
            if key not in budget:
                errors.append(f"spec.budget 缺少字段 {key}")
            else:
                as_number(budget[key], f"spec.budget.{key}", errors, 0)

    gates = spec.get("gates")
    if not isinstance(gates, dict):
        errors.append("spec.gates 必须是对象")
    else:
        numeric_gates = {
            "min_paired_tasks": 1,
            "min_success_delta": -1,
            "min_score_delta": -1,
            "max_protected_success_regression": 0,
            "max_cost_increase_ratio": 0,
            "max_latency_increase_ratio": 0,
            "min_market_events_per_arm": 0,
            "min_market_completion_delta": -1,
            "min_market_acceptance_delta": -1,
            "max_market_edit_increase_ratio": 0,
        }
        for key, minimum in numeric_gates.items():
            if key not in gates:
                errors.append(f"spec.gates 缺少字段 {key}")
            else:
                as_number(gates[key], f"spec.gates.{key}", errors, minimum)
        hard_failures = gates.get("blocking_failure_codes")
        if not isinstance(hard_failures, list) or not all(isinstance(item, str) and item for item in hard_failures):
            errors.append("spec.gates.blocking_failure_codes 必须是非空字符串数组")
        if not isinstance(gates.get("require_market_comparator"), bool):
            errors.append("spec.gates.require_market_comparator 必须是布尔值")
        if not isinstance(gates.get("require_positive_ci", False), bool):
            errors.append("spec.gates.require_positive_ci 必须是布尔值")

    privacy = spec.get("privacy")
    if not isinstance(privacy, dict):
        errors.append("spec.privacy 必须是对象")
    else:
        for key in ("raw_content_default", "require_consent_for_market", "retention_days"):
            if key not in privacy:
                errors.append(f"spec.privacy 缺少字段 {key}")
        if privacy.get("raw_content_default") not in {"deny", "allow_with_consent"}:
            errors.append("spec.privacy.raw_content_default 必须是 deny 或 allow_with_consent")
        if not isinstance(privacy.get("require_consent_for_market"), bool):
            errors.append("spec.privacy.require_consent_for_market 必须是布尔值")
        retention = privacy.get("retention_days")
        if isinstance(retention, bool) or not isinstance(retention, int) or retention < 0:
            errors.append("spec.privacy.retention_days 必须是 >= 0 的整数")

    return errors


def validate_task(task: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(task, dict):
        return ["任务必须是对象"]
    errors.extend(require_keys(task, ["task_id", "partition", "prompt", "origin", "oracle"], "task"))
    if errors:
        return errors
    _validate_id(task.get("task_id"), "task.task_id", errors)
    if task.get("partition") not in PARTITIONS:
        errors.append(f"task.partition 必须属于 {sorted(PARTITIONS)}")
    if not isinstance(task.get("prompt"), str) or not task["prompt"].strip():
        errors.append("task.prompt 必须是非空字符串")
    if task.get("origin") not in TASK_ORIGINS:
        errors.append(f"task.origin 必须属于 {sorted(TASK_ORIGINS)}")
    if not isinstance(task.get("oracle"), dict) or not task["oracle"].get("type"):
        errors.append("task.oracle 必须包含非空 type")
    if "protected" in task and not isinstance(task["protected"], bool):
        errors.append("task.protected 必须是布尔值")
    if task.get("origin") == "user_opt_in" and not task.get("consent_ref"):
        errors.append("user_opt_in 任务必须包含 consent_ref")
    if task.get("partition") == "market_live" and not task.get("consent_ref"):
        errors.append("market_live 任务必须包含 consent_ref")
    sensitivity = task.get("sensitivity", "public")
    if sensitivity not in {"public", "internal", "restricted"}:
        errors.append("task.sensitivity 必须是 public、internal 或 restricted")
    return errors


def validate_result(record: Any, arm_ids: Sequence[str] | None = None) -> List[str]:
    errors: List[str] = []
    if not isinstance(record, dict):
        return ["结果必须是对象"]
    errors.extend(
        require_keys(
            record,
            [
                "experiment_id",
                "run_id",
                "task_id",
                "partition",
                "arm_id",
                "repetition",
                "status",
                "outcome",
                "usage",
                "evidence_kind",
            ],
            "result",
        )
    )
    if errors:
        return errors
    for key in ("experiment_id", "run_id", "task_id", "arm_id"):
        _validate_id(record.get(key), f"result.{key}", errors)
    if arm_ids is not None and record.get("arm_id") not in arm_ids:
        errors.append(f"result.arm_id 未在实验臂中声明: {record.get('arm_id')}")
    if record.get("partition") not in PARTITIONS:
        errors.append(f"result.partition 必须属于 {sorted(PARTITIONS)}")
    repetition = record.get("repetition")
    if isinstance(repetition, bool) or not isinstance(repetition, int) or repetition < 1:
        errors.append("result.repetition 必须是 >= 1 的整数")
    if record.get("status") not in RESULT_STATUSES:
        errors.append(f"result.status 必须属于 {sorted(RESULT_STATUSES)}")
    if record.get("evidence_kind") not in EVIDENCE_KINDS:
        errors.append(f"result.evidence_kind 必须属于 {sorted(EVIDENCE_KINDS)}")

    outcome = record.get("outcome")
    if not isinstance(outcome, dict):
        errors.append("result.outcome 必须是对象")
    else:
        if not isinstance(outcome.get("success"), bool):
            errors.append("result.outcome.success 必须是布尔值")
        score = outcome.get("score")
        if isinstance(score, bool) or not isinstance(score, (int, float)) or not 0 <= float(score) <= 1:
            errors.append("result.outcome.score 必须在 0–1 之间")
        if "accepted" in outcome and outcome["accepted"] is not None and not isinstance(outcome["accepted"], bool):
            errors.append("result.outcome.accepted 必须是布尔值或 null")
        if record.get("status") != "completed":
            if outcome.get("success") is not False:
                errors.append("非 completed 结果必须 fail-closed：result.outcome.success=false")
            score = outcome.get("score")
            if isinstance(score, (int, float)) and not isinstance(score, bool) and float(score) != 0.0:
                errors.append("非 completed 结果必须 fail-closed：result.outcome.score=0")

    usage = record.get("usage")
    if not isinstance(usage, dict):
        errors.append("result.usage 必须是对象")
    else:
        for key in ("tokens", "cost_usd", "latency_ms", "tool_calls"):
            if key not in usage:
                errors.append(f"result.usage 缺少字段 {key}")
            elif usage[key] is not None:
                as_number(usage[key], f"result.usage.{key}", errors, 0)
    hard_failures = record.get("hard_failures", [])
    if not isinstance(hard_failures, list) or not all(isinstance(item, str) and item for item in hard_failures):
        errors.append("result.hard_failures 必须是字符串数组")
    if "protected" in record and not isinstance(record["protected"], bool):
        errors.append("result.protected 必须是布尔值")
    return errors


def validate_feedback(record: Any, arm_ids: Sequence[str] | None = None) -> List[str]:
    errors: List[str] = []
    if not isinstance(record, dict):
        return ["反馈必须是对象"]
    errors.extend(
        require_keys(
            record,
            [
                "event_id",
                "timestamp",
                "experiment_id",
                "source",
                "task_id",
                "arm_id",
                "artifact_digest",
                "completion",
                "consent_ref",
                "incident_severity",
            ],
            "feedback",
        )
    )
    if errors:
        return errors
    for key in ("event_id", "experiment_id", "task_id", "arm_id"):
        _validate_id(record.get(key), f"feedback.{key}", errors)
    if arm_ids is not None and record.get("arm_id") not in arm_ids:
        errors.append(f"feedback.arm_id 未在实验臂中声明: {record.get('arm_id')}")
    artifact_digest = record.get("artifact_digest")
    if artifact_digest is not None and (not isinstance(artifact_digest, str) or not artifact_digest.strip()):
        errors.append("feedback.artifact_digest 必须是非空字符串或 null")
    if not isinstance(record.get("timestamp"), str) or not record["timestamp"].strip():
        errors.append("feedback.timestamp 必须是非空字符串")
    if record.get("source") not in FEEDBACK_SOURCES:
        errors.append(f"feedback.source 必须属于 {sorted(FEEDBACK_SOURCES)}")
    if record.get("completion") not in COMPLETION_STATES:
        errors.append(f"feedback.completion 必须属于 {sorted(COMPLETION_STATES)}")
    if not isinstance(record.get("consent_ref"), str) or not record["consent_ref"].strip():
        errors.append("feedback.consent_ref 必须是非空字符串")
    if record.get("incident_severity") not in SEVERITIES:
        errors.append(f"feedback.incident_severity 必须属于 {sorted(SEVERITIES)}")
    for key in ("accepted", "would_reuse"):
        if key in record and record[key] is not None and not isinstance(record[key], bool):
            errors.append(f"feedback.{key} 必须是布尔值或 null")
    for key in ("human_edit_seconds", "time_saved_minutes", "paid_value_usd"):
        if key in record and record[key] is not None:
            as_number(record[key], f"feedback.{key}", errors, 0)
    if record.get("source") == "micro_bounty" and record.get("paid_value_usd") is None:
        errors.append("micro_bounty 反馈必须包含 paid_value_usd")
    if record.get("source") == "blind_canary":
        if not isinstance(record.get("assignment_id"), str) or not record["assignment_id"].strip():
            errors.append("blind_canary 反馈必须绑定 assignment_id")
        if record.get("randomized") is not True:
            errors.append("blind_canary 反馈必须声明 randomized=true")
    elif "randomized" in record and not isinstance(record.get("randomized"), bool):
        errors.append("feedback.randomized 必须是布尔值")
    if record.get("source") in {"external_acceptor", "micro_bounty"}:
        if not isinstance(record.get("acceptance_ref"), str) or not record["acceptance_ref"].strip():
            errors.append(f"{record.get('source')} 反馈必须包含 acceptance_ref")
    return errors


def validate_competitor_registry(registry: Any) -> List[str]:
    """Validate the frozen 5–12 peer registry used before experiment design."""
    errors: List[str] = []
    if not isinstance(registry, dict):
        return ["竞品登记必须是 JSON 对象"]
    errors.extend(require_keys(registry, ["schema_version", "registry_id", "entries"], "registry"))
    if errors:
        return errors
    if registry.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"registry.schema_version 必须为 {SCHEMA_VERSION}")
    _validate_id(registry.get("registry_id"), "registry.registry_id", errors)
    entries = registry.get("entries")
    if not isinstance(entries, list) or not 5 <= len(entries) <= 12:
        errors.append("registry.entries 必须包含 5–12 个当前同行或相似方案")
        return errors
    seen = set()
    for index, entry in enumerate(entries):
        location = f"registry.entries[{index}]"
        if not isinstance(entry, dict):
            errors.append(f"{location} 必须是对象")
            continue
        errors.extend(
            require_keys(
                entry,
                [
                    "id",
                    "name",
                    "evidence_type",
                    "role",
                    "source_reference",
                    "locked_identity",
                    "license_status",
                    "observable_artifact",
                    "adoption_decision",
                    "decision_reason",
                    "direct_performance_claim_allowed",
                ],
                location,
            )
        )
        entry_id = entry.get("id")
        _validate_id(entry_id, f"{location}.id", errors)
        if entry_id in seen:
            errors.append(f"{location}.id 重复: {entry_id}")
        seen.add(entry_id)
        if entry.get("evidence_type") not in COMPETITOR_EVIDENCE_TYPES:
            errors.append(
                f"{location}.evidence_type 必须属于 {sorted(COMPETITOR_EVIDENCE_TYPES)}"
            )
        for key in ("name", "role", "license_status", "observable_artifact", "adoption_decision", "decision_reason"):
            if not isinstance(entry.get(key), str) or not entry[key].strip():
                errors.append(f"{location}.{key} 必须是非空字符串")
        if entry.get("evidence_type") == "real":
            source = entry.get("source_reference")
            if not isinstance(source, str) or not source.startswith("https://"):
                errors.append(f"{location}.source_reference 对真实同行必须是 https URL")
            if not isinstance(entry.get("locked_identity"), str) or not entry["locked_identity"].strip():
                errors.append(f"{location}.locked_identity 对真实同行必填")
            if entry.get("direct_performance_claim_allowed") is not True:
                errors.append(f"{location} 真实同行应显式允许锁定版本的直接性能对比")
        else:
            if entry.get("direct_performance_claim_allowed") is not False:
                errors.append(f"{location} 模拟或代理证据不得允许直接性能市场声明")
        if not isinstance(entry.get("direct_performance_claim_allowed"), bool):
            errors.append(f"{location}.direct_performance_claim_allowed 必须是布尔值")
    return errors


def assert_valid(errors: Sequence[str], context: str) -> None:
    if errors:
        rendered = "\n".join(f"- {error}" for error in errors)
        raise ValidationError(f"{context} 验证失败:\n{rendered}")
