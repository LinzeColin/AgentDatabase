from __future__ import annotations
from math import sqrt
from typing import Any, Dict, List, Mapping, Set
from .common import object_sha256, utc_now
from .contracts import (
    COVERAGE_DIMENSIONS, COVERAGE_STATUSES, DEFECT_SEVERITIES, DEFECT_STATUSES,
    EVIDENCE_CLASSES, PROVENANCE_STATUSES, validate_product_reality_run,
)

def _ids(rows: List[Mapping[str, Any]], key: str) -> Set[str]:
    return {str(row.get(key)) for row in rows if isinstance(row,Mapping) and row.get(key)}

def _valid_waiver(row: Mapping[str, Any]) -> bool:
    return all(row.get(k) for k in ("waiver_owner","waiver_reason","waiver_expiry","compensating_control","evidence_refs"))

def evaluate_product_reality(value: Mapping[str, Any], require_field: bool = True) -> Dict[str, Any]:
    validation_errors=validate_product_reality_run(value)
    reasons: List[Dict[str,str]]=[]
    hard=False
    if validation_errors:
        hard=True
        reasons.extend({"code":"CONTRACT_INVALID","severity":"BLOCKING","detail":x} for x in validation_errors)

    provenance=value.get("provenance") if isinstance(value.get("provenance"),list) else []
    for row in provenance:
        if not isinstance(row,Mapping): continue
        status=row.get("status")
        if status not in PROVENANCE_STATUSES:
            hard=True; reasons.append({"code":"PROVENANCE_STATUS_INVALID","severity":"BLOCKING","detail":str(row.get("reuse_id"))})
        elif status == "PENDING":
            hard=True; reasons.append({"code":"PROVENANCE_PENDING","severity":"BLOCKING","detail":str(row.get("reuse_id"))})
        elif status == "APPROVED":
            required=("source_ref","commit_or_tag","license","copyright_notice","modified_files","use_basis","reviewer","reviewed_at","evidence_refs")
            missing=[k for k in required if not row.get(k)]
            if missing:
                hard=True; reasons.append({"code":"PROVENANCE_APPROVAL_INCOMPLETE","severity":"BLOCKING","detail":f"{row.get('reuse_id')}: {','.join(missing)}"})

    census=value.get("census") if isinstance(value.get("census"),Mapping) else {}
    source_ids=_ids(census.get("source_items",[]) if isinstance(census.get("source_items"),list) else [],"item_id")
    runtime_ids=_ids(census.get("runtime_items",[]) if isinstance(census.get("runtime_items"),list) else [],"item_id")
    source_only=sorted(source_ids-runtime_ids); runtime_only=sorted(runtime_ids-source_ids)
    if source_only or runtime_only:
        hard=True; reasons.append({"code":"CENSUS_RECONCILIATION_FAILED","severity":"BLOCKING","detail":f"source_only={source_only}; runtime_only={runtime_only}"})

    coverage=value.get("coverage") if isinstance(value.get("coverage"),list) else []
    coverage_ids=set(); dimensions=set(); coverage_counts={s:0 for s in COVERAGE_STATUSES}; coverage_errors=[]
    for row in coverage:
        if not isinstance(row,Mapping): continue
        cid=row.get("coverage_id")
        if cid in coverage_ids: coverage_errors.append(f"重复 coverage_id: {cid}")
        coverage_ids.add(cid)
        dimension=row.get("dimension"); status=row.get("status")
        if dimension in COVERAGE_DIMENSIONS: dimensions.add(dimension)
        else: coverage_errors.append(f"无效 dimension: {dimension}")
        if status not in COVERAGE_STATUSES: coverage_errors.append(f"无效 coverage status: {status}")
        else: coverage_counts[status]+=1
        if status == "COVERED" and (not row.get("oracle_ref") or not row.get("evidence_refs")): coverage_errors.append(f"{cid} COVERED 缺少 Oracle/Evidence")
        if status == "NOT_APPLICABLE_WITH_REASON" and not row.get("reason"): coverage_errors.append(f"{cid} N/A 缺少 reason")
        if status == "WAIVED" and not _valid_waiver(row): coverage_errors.append(f"{cid} waiver 不完整")
    missing_dims=sorted(set(COVERAGE_DIMENSIONS)-dimensions)
    if missing_dims: coverage_errors.append("八维覆盖缺失: "+", ".join(missing_dims))
    census_item_ids=source_ids | runtime_ids
    covered_surface_ids={str(row.get("item_id")) for row in coverage if isinstance(row,Mapping) and row.get("item_id")}
    missing_items=sorted(census_item_ids-covered_surface_ids)
    if missing_items: coverage_errors.append("Catalog 项未进入 coverage 分母: "+", ".join(missing_items))
    if coverage_errors:
        hard=True; reasons.extend({"code":"COVERAGE_LEDGER_INVALID","severity":"BLOCKING","detail":x} for x in coverage_errors)

    defects=value.get("defects") if isinstance(value.get("defects"),list) else []
    open_critical=[]; defect_ids=set()
    for row in defects:
        if not isinstance(row,Mapping): continue
        did=row.get("defect_id")
        if did in defect_ids: hard=True; reasons.append({"code":"DUPLICATE_DEFECT_ID","severity":"BLOCKING","detail":str(did)})
        defect_ids.add(did)
        severity=row.get("severity"); status=row.get("status")
        if severity not in DEFECT_SEVERITIES or status not in DEFECT_STATUSES:
            hard=True; reasons.append({"code":"DEFECT_CONTRACT_INVALID","severity":"BLOCKING","detail":str(did)})
        if severity in {"P0","P1"} and status not in {"FIXED","VERIFIED","DUPLICATE"}: open_critical.append(str(did))
        if status in {"FIXED","VERIFIED"}:
            missing=[k for k in ("minimal_reproduction","root_cause_cluster","regression_evidence_refs","neighborhood_regression_refs","residual_risk") if not row.get(k)]
            if missing: hard=True; reasons.append({"code":"DEFECT_CLOSURE_INCOMPLETE","severity":"BLOCKING","detail":f"{did}: {','.join(missing)}"})
    if open_critical:
        hard=True; reasons.append({"code":"OPEN_P0_P1","severity":"BLOCKING","detail":", ".join(open_critical)})

    negative=value.get("negative_controls") if isinstance(value.get("negative_controls"),list) else []
    critical_tests={str(row.get("critical_test_id")) for row in coverage if isinstance(row,Mapping) and row.get("critical_test_id")}
    valid_controls=set()
    for row in negative:
        if not isinstance(row,Mapping): continue
        if all(row.get(k) for k in ("test_id","mutation","expected_failure","evidence_ref")) and row.get("observed_failure") is True:
            valid_controls.add(str(row.get("test_id")))
    missing_controls=sorted(critical_tests-valid_controls)
    if missing_controls:
        hard=True; reasons.append({"code":"NEGATIVE_CONTROL_MISSING_OR_SURVIVED","severity":"BLOCKING","detail":", ".join(missing_controls)})

    field=value.get("field_experiments") if isinstance(value.get("field_experiments"),list) else []
    completed_field=[]; controlled=[]; synthetic=[]
    for row in field:
        if not isinstance(row,Mapping): continue
        klass=row.get("evidence_class")
        if klass not in EVIDENCE_CLASSES:
            hard=True; reasons.append({"code":"EVIDENCE_CLASS_INVALID","severity":"BLOCKING","detail":str(row.get("experiment_id"))}); continue
        if klass == "FIELD_OBSERVED":
            required=("consent_ref","real_user_or_acceptor_ref","real_task_ref","outcome_ref","cost_or_consequence_ref","evidence_refs")
            if row.get("status") == "COMPLETED" and all(row.get(k) for k in required): completed_field.append(str(row.get("experiment_id")))
        elif klass == "CONTROLLED_HUMAN": controlled.append(str(row.get("experiment_id")))
        else: synthetic.append(str(row.get("experiment_id")))

    lab_complete = (
        not hard
        and coverage_counts["NOT_RUN"] == 0
        and coverage_counts["BLOCKED"] == 0
        and len(dimensions) == len(COVERAGE_DIMENSIONS)
        and not missing_items
    )
    if hard:
        state="BLOCKED"
    elif not lab_complete:
        state="MORE_EVIDENCE_REQUIRED"
        reasons.append({"code":"LAB_INCOMPLETE","severity":"EVIDENCE","detail":"覆盖仍含 NOT_RUN/BLOCKED 或关键维度未闭合"})
    elif require_field and not completed_field:
        state="FIELD_VALIDATION_PENDING"
        reasons.append({"code":"FIELD_EVIDENCE_ABSENT","severity":"EVIDENCE","detail":"只有合成/受控证据，不能冒充 FIELD_OBSERVED"})
    else:
        state="READY_FOR_VERIFIER"
        reasons.append({"code":"PRODUCT_REALITY_EVIDENCE_CLOSED","severity":"INFO","detail":"产品试炼证据闭合；最终 PASS 仍归外部 Verifier"})

    # Optional capture-recapture is a residual-risk signal only.
    capture=value.get("capture_recapture") if isinstance(value.get("capture_recapture"),Mapping) else {}
    estimate=None
    try:
        a=float(capture.get("method_a_unique",0)); b=float(capture.get("method_b_unique",0)); overlap=float(capture.get("overlap",0))
        if a>0 and b>0 and overlap>0:
            estimate=((a+1)*(b+1)/(overlap+1))-1
    except (TypeError,ValueError,ZeroDivisionError): estimate=None

    result={
        "schema_version":"teleiosis.product_reality_gate.v1",
        "generated_at":utc_now(),
        "candidate_identity":value.get("candidate_identity"),
        "state":state,
        "authority":"PRODUCT_EVIDENCE_ONLY_NO_PASS",
        "require_field":require_field,
        "derived":{
            "source_census_items":len(source_ids),"runtime_census_items":len(runtime_ids),
            "source_only":source_only,"runtime_only":runtime_only,
            "coverage_total":len(coverage),"coverage_counts":coverage_counts,
            "dimensions_checked":sorted(dimensions),"open_p0_p1":open_critical,
            "valid_negative_controls":len(valid_controls),"completed_field_experiments":completed_field,
            "controlled_human_experiments":controlled,"synthetic_experiments":synthetic,
            "field_validation_complete":bool(completed_field),
            "capture_recapture_estimated_total_defects":estimate,
            "capture_recapture_use":"RESIDUAL_RISK_SIGNAL_ONLY",
        },
        "reasons":reasons,
    }
    result["gate_digest"]=object_sha256(result)
    return result
