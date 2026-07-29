from __future__ import annotations

import datetime as dt
from typing import Any, Dict, List, Mapping, Sequence

from .common import object_sha256, utc_now

REQUIRED_TRACE_FIELDS = {
    "run_id",
    "task_id",
    "arm_id",
    "subject_digest",
    "environment_digest",
    "tool_trace_digest",
    "artifact_digest",
    "handoff_digest",
}
ACTIVE_PROVIDER_STATES = {"active", "pinned"}


def _parse_date(value: Any) -> dt.date | None:
    if not isinstance(value, str):
        return None
    try:
        return dt.date.fromisoformat(value[:10])
    except ValueError:
        return None


def evaluate_assurance(record: Mapping[str, Any], as_of: str | None = None) -> Dict[str, Any]:
    failures: List[Dict[str, str]] = []
    warnings: List[Dict[str, str]] = []
    today = _parse_date(as_of) if as_of else dt.date.today()
    if today is None:
        today = dt.date.today()

    traces = record.get("traces")
    if not isinstance(traces, list) or not traces:
        failures.append({"code": "MISSING_TRACES", "detail": "至少需要一条可复核 trace。"})
    else:
        seen_run_ids = set()
        for index, trace in enumerate(traces):
            if not isinstance(trace, Mapping):
                failures.append({"code": "INVALID_TRACE", "detail": f"traces[{index}] 不是 object。"})
                continue
            missing = sorted(REQUIRED_TRACE_FIELDS - set(trace))
            if missing:
                failures.append(
                    {"code": "TRACE_FIELDS_MISSING", "detail": f"traces[{index}] 缺少 {missing}。"}
                )
            run_id = trace.get("run_id")
            if run_id in seen_run_ids:
                failures.append({"code": "DUPLICATE_RUN_ID", "detail": f"重复 run_id={run_id}。"})
            seen_run_ids.add(run_id)

    separation = record.get("evaluator_separation", {})
    generators = set(separation.get("generator_ids", [])) if isinstance(separation, Mapping) else set()
    evaluators = set(separation.get("evaluator_ids", [])) if isinstance(separation, Mapping) else set()
    if not generators or not evaluators:
        failures.append({"code": "EVALUATOR_SEPARATION_UNPROVEN", "detail": "缺少生成者/评估者身份集合。"})
    elif generators & evaluators:
        failures.append(
            {
                "code": "GENERATOR_EVALUATOR_OVERLAP",
                "detail": f"生成与评估身份重叠: {sorted(generators & evaluators)}。",
            }
        )

    calibration = record.get("judge_calibration", {})
    if not isinstance(calibration, Mapping):
        failures.append({"code": "MISSING_JUDGE_CALIBRATION", "detail": "缺少 judge calibration 或显式 NOT_APPLICABLE 合同。"})
    elif calibration.get("enabled") is False and calibration.get("status") == "NOT_APPLICABLE":
        pass
    else:
        sample = int(calibration.get("sample_size", 0) or 0)
        agreement = float(calibration.get("agreement", 0.0) or 0.0)
        kappa = float(calibration.get("cohens_kappa", 0.0) or 0.0)
        min_sample = int(calibration.get("min_sample_size", 20) or 20)
        min_agreement = float(calibration.get("min_agreement", 0.8) or 0.8)
        min_kappa = float(calibration.get("min_cohens_kappa", 0.6) or 0.6)
        if sample < min_sample:
            failures.append({"code": "CALIBRATION_SAMPLE_TOO_SMALL", "detail": f"{sample} < {min_sample}。"})
        if agreement < min_agreement:
            failures.append({"code": "JUDGE_AGREEMENT_TOO_LOW", "detail": f"{agreement} < {min_agreement}。"})
        if kappa < min_kappa:
            failures.append({"code": "JUDGE_KAPPA_TOO_LOW", "detail": f"{kappa} < {min_kappa}。"})

    providers = record.get("providers")
    if not isinstance(providers, list) or not providers:
        failures.append({"code": "MISSING_PROVIDER_LEDGER", "detail": "缺少 Adapter/Provider 生命周期台账。"})
    else:
        for index, provider in enumerate(providers):
            if not isinstance(provider, Mapping):
                failures.append({"code": "INVALID_PROVIDER", "detail": f"providers[{index}] 不是 object。"})
                continue
            required = {"id", "version", "status", "source_url", "valid_until"}
            missing = sorted(required - set(provider))
            if missing:
                failures.append({"code": "PROVIDER_FIELDS_MISSING", "detail": f"providers[{index}] 缺少 {missing}。"})
                continue
            if provider.get("status") not in ACTIVE_PROVIDER_STATES:
                failures.append(
                    {"code": "PROVIDER_NOT_ACTIVE", "detail": f"{provider.get('id')} 状态={provider.get('status')}。"}
                )
            valid_until = _parse_date(provider.get("valid_until"))
            if valid_until is None:
                failures.append({"code": "PROVIDER_VALIDITY_INVALID", "detail": f"{provider.get('id')} valid_until 无效。"})
            elif valid_until < today:
                failures.append(
                    {
                        "code": "PROVIDER_EVIDENCE_EXPIRED",
                        "detail": f"{provider.get('id')} 于 {valid_until.isoformat()} 失效。",
                    }
                )

    contamination = record.get("contamination", {})
    if not isinstance(contamination, Mapping):
        failures.append({"code": "MISSING_CONTAMINATION_AUDIT", "detail": "缺少污染审计。"})
    else:
        holdout_access = int(contamination.get("candidate_holdout_access_count", 0) or 0)
        overlap = float(contamination.get("max_overlap_ratio", 1.0) or 0.0)
        allowed = float(contamination.get("allowed_overlap_ratio", 0.0) or 0.0)
        if holdout_access > 0:
            failures.append({"code": "SEALED_HOLDOUT_ACCESSED", "detail": f"Candidate 访问 {holdout_access} 次。"})
        if overlap > allowed:
            failures.append({"code": "DATASET_OVERLAP_EXCEEDED", "detail": f"{overlap} > {allowed}。"})

    quality_reports = record.get("quality_reports")
    required_quality = {
        "contamination",
        "assignment",
        "sample_ratio_mismatch",
        "environment_parity",
        "power_plan",
        "referential_integrity",
    }
    if not isinstance(quality_reports, Mapping):
        failures.append({"code": "MISSING_QUALITY_REPORTS", "detail": "缺少 Schema 2.0 因果质量报告。"})
    else:
        for name in sorted(required_quality):
            report = quality_reports.get(name)
            if not isinstance(report, Mapping):
                failures.append({"code": "QUALITY_REPORT_MISSING", "detail": f"缺少 {name}。"})
                continue
            if report.get("status") != "PASS":
                failures.append({"code": "QUALITY_GATE_NOT_PASS", "detail": f"{name} status={report.get('status')}。"})
            if not isinstance(report.get("audit_digest"), str) or not report.get("audit_digest"):
                failures.append({"code": "QUALITY_DIGEST_MISSING", "detail": f"{name} 缺少 audit_digest。"})
        for optional in ("judge_calibration", "market_temporal_integrity"):
            report = quality_reports.get(optional)
            if report is not None and (not isinstance(report, Mapping) or report.get("status") not in {"PASS", "NOT_APPLICABLE"}):
                failures.append({"code": "OPTIONAL_QUALITY_GATE_INVALID", "detail": f"{optional} 未 PASS/NOT_APPLICABLE。"})

    evidence_chain = record.get("evidence_chain")
    if not isinstance(evidence_chain, Mapping) or evidence_chain.get("status") != "PASS" or not evidence_chain.get("evidence_chain_digest"):
        failures.append({"code": "EVIDENCE_CHAIN_UNPROVEN", "detail": "缺少完整且通过的证据链摘要。"})

    canary = record.get("canary", {})
    if not isinstance(canary, Mapping):
        failures.append({"code": "MISSING_CANARY_CONTRACT", "detail": "缺少 Canary 合同。"})
    else:
        if canary.get("stop_rules_predeclared") is not True:
            failures.append({"code": "CANARY_RULES_NOT_PREDECLARED", "detail": "停止规则未在运行前冻结。"})
        if int(canary.get("critical_incidents", 0) or 0) > 0:
            failures.append({"code": "CANARY_CRITICAL_INCIDENT", "detail": "出现严重事故。"})
        if canary.get("stop_triggered") is True and canary.get("candidate_stopped") is not True:
            failures.append({"code": "CANARY_STOP_NOT_ENFORCED", "detail": "触发停止条件但未停用 Candidate。"})

    freshness = record.get("freshness", {})
    if not isinstance(freshness, Mapping):
        failures.append({"code": "MISSING_FRESHNESS_CONTRACT", "detail": "缺少证据时效合同。"})
    else:
        checked_at = _parse_date(freshness.get("checked_at"))
        max_age = int(freshness.get("max_age_days", 30) or 30)
        if checked_at is None:
            failures.append({"code": "FRESHNESS_DATE_INVALID", "detail": "checked_at 无效。"})
        elif (today - checked_at).days > max_age:
            failures.append(
                {
                    "code": "EVIDENCE_STALE",
                    "detail": f"证据年龄 {(today - checked_at).days} 天，超过 {max_age} 天。",
                }
            )
        if freshness.get("reheat_triggered") and freshness.get("reheat_acknowledged") is not True:
            failures.append({"code": "REHEAT_TRIGGER_UNACKNOWLEDGED", "detail": "已触发回炉但未处理。"})

    result: Dict[str, Any] = {
        "schema_version": "2.0",
        "generated_at": utc_now(),
        "status": "PASS" if not failures else "BLOCKED",
        "final_authority": "teleiosis",
        "market_kernel_authority": "evidence_only",
        "failures": failures,
        "warnings": warnings,
        "record_digest": object_sha256(record),
        "assurance_digest": None,
    }
    result["assurance_digest"] = object_sha256({k: v for k, v in result.items() if k != "assurance_digest"})
    return result


def evaluate_sequential_canary(contract: Mapping[str, Any], observations: Sequence[Mapping[str, Any]]) -> Dict[str, Any]:
    if contract.get("predeclared") is not True:
        return {"decision": "BLOCKED", "stop": True, "reason": "RULES_NOT_PREDECLARED"}
    max_critical = int(contract.get("max_critical_incidents", 0) or 0)
    max_failure_rate = float(contract.get("max_failure_rate", 0.2) or 0.2)
    min_observations = int(contract.get("min_observations", 10) or 10)
    critical = sum(1 for row in observations if row.get("incident_severity") in {"critical", "high"})
    failures = sum(1 for row in observations if row.get("completed") is False)
    total = len(observations)
    failure_rate = failures / total if total else 0.0
    stop = critical > max_critical or (total >= min_observations and failure_rate > max_failure_rate)
    if critical > max_critical:
        reason = "CRITICAL_INCIDENT_THRESHOLD"
    elif total >= min_observations and failure_rate > max_failure_rate:
        reason = "FAILURE_RATE_THRESHOLD"
    else:
        reason = "CONTINUE"
    return {
        "decision": "STOP_CANDIDATE" if stop else "CONTINUE_CANARY",
        "stop": stop,
        "reason": reason,
        "observations": total,
        "critical_or_high_incidents": critical,
        "failure_rate": failure_rate,
        "contract_digest": object_sha256(contract),
        "observations_digest": object_sha256(list(observations)),
    }
