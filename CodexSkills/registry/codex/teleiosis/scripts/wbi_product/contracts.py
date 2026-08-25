from __future__ import annotations
from typing import Any, Dict, List, Mapping, Sequence
from .common import is_sha256

COMPETITOR_CATEGORIES = ("direct", "adjacent", "substitute", "manual", "open_source")
COMPETITOR_DECISIONS = ("ADOPT", "ADAPT", "DIFFERENTIATE", "REJECT", "DEFER")
COVERAGE_DIMENSIONS = ("Surface", "State", "Transition", "Role", "Data", "Fault", "Oracle", "Evidence")
COVERAGE_STATUSES = ("COVERED", "NOT_APPLICABLE_WITH_REASON", "WAIVED", "NOT_RUN", "BLOCKED")
PROVENANCE_STATUSES = ("APPROVED", "PENDING", "REJECTED")
DEFECT_SEVERITIES = ("P0", "P1", "P2", "P3")
DEFECT_STATUSES = ("OPEN", "FIXED", "VERIFIED", "DEFERRED", "DUPLICATE")
EVIDENCE_CLASSES = ("SYNTHETIC", "CONTROLLED_HUMAN", "FIELD_OBSERVED")
TERMINAL_STATES = ("READY_FOR_VERIFIER", "MORE_EVIDENCE_REQUIRED", "FIELD_VALIDATION_PENDING", "BLOCKED")

REQUIRED_CAPABILITIES = {
    "competitor_and_open_source_analysis",
    "open_source_provenance_governance",
    "source_runtime_product_census",
    "eight_dimension_coverage",
    "frontend_experiment",
    "backend_api_experiment",
    "data_correctness",
    "performance_reliability",
    "poka_yoke_and_misoperation",
    "model_exploration_not_oracle",
    "field_evidence_ladder",
    "defect_convergence",
    "negative_control_and_mutation",
    "anti_cheat_derived_totals",
    "capture_recapture_residual_signal",
}


def _required(mapping: Mapping[str, Any], keys: Sequence[str], prefix: str, errors: List[str]) -> None:
    for key in keys:
        if mapping.get(key) in (None, "", []):
            errors.append(f"{prefix}.{key} 缺失")


def validate_candidate_identity(value: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(value, Mapping): return ["candidate_identity 必须为 object"]
    _required(value, ("subject_id", "baseline_hash", "candidate_hash", "acceptance_hash", "environment_hash"), "candidate_identity", errors)
    for key in ("baseline_hash", "candidate_hash", "acceptance_hash", "environment_hash"):
        if value.get(key) and not is_sha256(value[key]): errors.append(f"candidate_identity.{key} 必须为裸 64 位 SHA-256")
    return errors


def validate_capability_manifest(rows: Any) -> List[str]:
    errors: List[str] = []
    if not isinstance(rows, list): return ["capability_manifest 必须为 array"]
    seen=set()
    for index,row in enumerate(rows):
        if not isinstance(row,Mapping): errors.append(f"capability_manifest[{index}] 必须为 object"); continue
        capability=row.get("capability"); status=row.get("status")
        if capability in seen: errors.append(f"capability 重复: {capability}")
        seen.add(capability)
        if status not in {"EXECUTED","NOT_APPLICABLE_WITH_REASON","BLOCKED","NOT_RUN"}: errors.append(f"capability {capability} 状态无效")
        if status == "NOT_APPLICABLE_WITH_REASON" and not row.get("reason"): errors.append(f"capability {capability} N/A 缺少 reason")
        if status == "EXECUTED" and not row.get("evidence_refs"): errors.append(f"capability {capability} EXECUTED 缺少 evidence_refs")
    missing=sorted(REQUIRED_CAPABILITIES-seen)
    if missing: errors.append("capability_manifest 缺少全量能力: "+", ".join(missing))
    return errors


def validate_product_reality_run(value: Mapping[str, Any]) -> List[str]:
    errors: List[str] = []
    if value.get("schema_version") != "teleiosis.product_reality.v1": errors.append("schema_version 必须是 teleiosis.product_reality.v1")
    errors += validate_candidate_identity(value.get("candidate_identity"))
    errors += validate_capability_manifest(value.get("capability_manifest"))
    competitors=value.get("competitors")
    if not isinstance(competitors,list): errors.append("competitors 必须为 array")
    else:
        categories=set()
        for i,row in enumerate(competitors):
            if not isinstance(row,Mapping): errors.append(f"competitors[{i}] 必须为 object"); continue
            _required(row,("competitor_id","category","decision","source_ref","benchmark_task_ids"),f"competitors[{i}]",errors)
            if row.get("category") not in COMPETITOR_CATEGORIES: errors.append(f"competitors[{i}].category 无效")
            else: categories.add(row["category"])
            if row.get("decision") not in COMPETITOR_DECISIONS: errors.append(f"competitors[{i}].decision 无效")
        missing=sorted(set(COMPETITOR_CATEGORIES)-categories)
        if missing: errors.append("竞品五类覆盖缺失: "+", ".join(missing))
    for name in ("provenance","coverage","defects","negative_controls","field_experiments"):
        if not isinstance(value.get(name),list): errors.append(f"{name} 必须为 array")
    census=value.get("census")
    if not isinstance(census,Mapping): errors.append("census 必须为 object")
    else:
        if not isinstance(census.get("source_items"),list): errors.append("census.source_items 必须为 array")
        if not isinstance(census.get("runtime_items"),list): errors.append("census.runtime_items 必须为 array")
    return errors
