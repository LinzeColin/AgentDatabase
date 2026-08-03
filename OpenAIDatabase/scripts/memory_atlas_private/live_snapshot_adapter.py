from __future__ import annotations

"""Thin, deterministic adapter from existing private analytics to LiveSnapshotV1."""

from datetime import datetime, timezone
from typing import Any, Mapping

TERMINAL_STATES={"SUCCEEDED","REBUILT_FROM_AUTHORITIES"}
FORBIDDEN_KEYS={"object_key","sha256","readback_sha256","source_root","relative_path","materialized_path","payload","objects","cookie","secret","token","raw_content","prompt"}
ACTIVITY_LABELS={"research_diagnosis":"研究与诊断","product_planning":"产品与规划","development_deployment":"开发与部署","verification_repair":"验证与修复","management_learning":"管理与学习","decision_execution":"决策与执行","unknown":"未分类"}

class LiveSnapshotError(ValueError): pass

def _dt(value: object, field: str) -> datetime:
    if not isinstance(value,str) or not value.strip(): raise LiveSnapshotError(f"{field} is required")
    try: parsed=datetime.fromisoformat(value.replace('Z','+00:00'))
    except ValueError as exc: raise LiveSnapshotError(f"invalid {field}") from exc
    if parsed.tzinfo is None: raise LiveSnapshotError(f"{field} requires timezone")
    return parsed.astimezone(timezone.utc)

def _state(value: object) -> str:
    raw=str(value or 'UNKNOWN')
    if raw=='READY': return 'READY'
    if raw in {'MISSING','MISSING_REQUIRED','MISSING_OPTIONAL','EMPTY'}: return 'MISSING'
    if raw in {'FAILED','UNREADABLE'}: return 'FAILED'
    if raw=='STALE': return 'STALE'
    return 'UNKNOWN'

def _counts(rows: list[dict[str,Any]]) -> dict[str,int]:
    out={'ready':0,'total':len(rows),'stale':0,'missing':0,'failed':0,'unknown':0}
    for row in rows: out[row['state'].lower()]+=1
    return out

def _scan(value: object, path: str='$') -> None:
    if isinstance(value,Mapping):
        for key,child in value.items():
            if str(key).lower() in FORBIDDEN_KEYS: raise LiveSnapshotError(f"private field leaked at {path}.{key}")
            _scan(child,f"{path}.{key}")
    elif isinstance(value,list):
        for index,child in enumerate(value): _scan(child,f"{path}[{index}]")

def _same_run_evidence(runtime: Mapping[str,Any], run_id: str, trace_id: str) -> dict[str,Any]:
    raw=runtime.get('same_run_evidence') if isinstance(runtime.get('same_run_evidence'),Mapping) else {}
    result={}
    for name in ('r2_readback','private_database_readback','ovh_reconcile','status_projection'):
        value=raw.get(name) if isinstance(raw.get(name),Mapping) else {}
        state=str(value.get('state','UNKNOWN'))
        evidence_run=value.get('run_id') if isinstance(value.get('run_id'),str) else None
        evidence_trace=value.get('trace_id') if isinstance(value.get('trace_id'),str) else None
        if state=='PASS' and (evidence_run!=run_id or evidence_trace!=trace_id): raise LiveSnapshotError(f"same-run mismatch for {name}")
        result[name]={'state':state if state in {'PASS','FAIL','NOT_RUN','UNKNOWN'} else 'UNKNOWN','run_id':evidence_run,'trace_id':evidence_trace,'ref':value.get('ref') if isinstance(value.get('ref'),str) else None}
    for required in ('r2_readback','private_database_readback','ovh_reconcile'):
        if result[required]['state']!='PASS': raise LiveSnapshotError(f"required authority evidence not PASS: {required}")
    return result

def build_live_snapshot(private_snapshot: Mapping[str,Any], visual_analytics: Mapping[str,Any], runtime_evidence: Mapping[str,Any], benchmark_result: Mapping[str,Any], *, evaluated_at: str, freshness_target_seconds: int=1800) -> dict[str,Any]:
    if private_snapshot.get('schema_version')!='memory_atlas.private_analytics.v1': raise LiveSnapshotError('private analytics schema mismatch')
    if visual_analytics.get('schema_version')!='memory_atlas.visual_analytics.v1': raise LiveSnapshotError('visual analytics schema mismatch')
    if benchmark_result.get('schema_version')!='memory_atlas.benchmark_result.v1': raise LiveSnapshotError('benchmark result schema mismatch')
    run=private_snapshot.get('run'); behavior=private_snapshot.get('behavior_economics'); failure=private_snapshot.get('failure_compound')
    if not all(isinstance(value,Mapping) for value in (run,behavior,failure)): raise LiveSnapshotError('private snapshot requires run, behavior_economics and failure_compound')
    run_id=str(run.get('run_id','')).strip(); trace_id=str(run.get('trace_id','')).strip(); source_state=str(run.get('state','UNKNOWN'))
    if not run_id or not trace_id: raise LiveSnapshotError('run_id and trace_id are required')
    if source_state not in TERMINAL_STATES: raise LiveSnapshotError(f"non-terminal source state refused: {source_state}")
    if runtime_evidence.get('run_id')!=run_id or runtime_evidence.get('trace_id')!=trace_id: raise LiveSnapshotError('runtime identity mismatch')
    completed_at=str(run.get('source_completed_at',run.get('completed_at',''))); completed_dt=_dt(completed_at,'source_completed_at'); evaluated_dt=_dt(evaluated_at,'evaluated_at')
    age=max(0,int((evaluated_dt-completed_dt).total_seconds()))

    release=runtime_evidence.get('release') if isinstance(runtime_evidence.get('release'),Mapping) else {}
    release_out={
        'identity_state':str(release.get('identity_state','UNVERIFIED')) if str(release.get('identity_state','UNVERIFIED')) in {'VERIFIED','OBSERVED','UNVERIFIED'} else 'UNVERIFIED',
        'repository_commit':release.get('repository_commit') if isinstance(release.get('repository_commit'),str) else None,
        'release_id':release.get('release_id') if isinstance(release.get('release_id'),str) else None,
        'artifact_digest':release.get('artifact_digest') if isinstance(release.get('artifact_digest'),str) else None,
        'deployment_revision':release.get('deployment_revision') if isinstance(release.get('deployment_revision'),str) else None,
    }

    tier_a=[]
    raw_a=runtime_evidence.get('cloud_native_sources')
    if not isinstance(raw_a,list) or not raw_a: raise LiveSnapshotError('cloud_native_sources must be non-empty')
    for item in raw_a:
        if not isinstance(item,Mapping): raise LiveSnapshotError('cloud source must be object')
        # required_for_product is read, not assumed: a cloud authority may be a
        # real gap when missing without being something the product cannot render
        # without (the GitHub full-history backup is exactly that).
        tier_a.append({'source_id':str(item.get('source_id','unknown')),'label_zh':str(item.get('label_zh',item.get('source_id','云端来源'))),'tier':'A_CLOUD_NATIVE','required_for_capture':bool(item.get('required_for_capture',True)),'required_for_product':bool(item.get('required_for_product',True)),'state':_state(item.get('state')),'object_count':int(item.get('object_count',0) or 0),'size_bytes':int(item.get('size_bytes',0) or 0),'last_observed_at':item.get('last_observed_at') if isinstance(item.get('last_observed_at'),str) else None})
    tier_b=[]
    for item in run.get('source_coverages',[]) if isinstance(run.get('source_coverages'),list) else []:
        if not isinstance(item,Mapping): continue
        tier=str(item.get('availability_tier','B_LOCAL_OPTIONAL'))
        tier_b.append({'source_id':str(item.get('source_id','unknown')),'label_zh':str(item.get('label_zh',item.get('source_id','本机来源'))),'tier':tier if tier in {'A_CLOUD_NATIVE','B_LOCAL_OPTIONAL'} else 'B_LOCAL_OPTIONAL','required_for_capture':bool(item.get('required',False)),'required_for_product':bool(item.get('required_for_product',False)),'state':_state(item.get('state')),'object_count':int(item.get('object_count',0) or 0),'size_bytes':int(item.get('size_bytes',0) or 0),'last_observed_at':completed_at})
    ac=_counts(tier_a); bc=_counts(tier_b)
    # Availability is decided by required_for_product, not by which tier a row
    # happens to sit in. Everything else is a coverage gap that degrades.
    required=[row for row in tier_a+tier_b if row['required_for_product']]
    optional=[row for row in tier_a+tier_b if not row['required_for_product']]
    required_failed=[row for row in required if row['state']=='FAILED']
    required_bad=[row for row in required if row['state']!='READY']
    optional_bad=[row for row in optional if row['state']!='READY']
    if required_bad:
        product_state='FAILED' if required_failed else 'DEGRADED'; fresh_state='DEGRADED'
        reason='至少一个产品必需的云端权威不可用：'+'、'.join(sorted(row['label_zh'] for row in required_bad))+'；系统不能宣称最新。'
    elif age>freshness_target_seconds:
        product_state='DEGRADED'; fresh_state='STALE'; reason=f'最近成功源运行已超过 {freshness_target_seconds} 秒新鲜度目标。'
    elif optional_bad:
        product_state='DEGRADED'; fresh_state='DEGRADED'
        reason='云端必需权威可用，但以下来源未更新：'+'、'.join(sorted(row['label_zh'] for row in optional_bad))+'；相关指标按陈旧处理。'
    else:
        product_state='PASS'; fresh_state='FRESH'; reason='云端权威和本批来源均在新鲜度目标内。'

    metrics=visual_analytics.get('metrics') if isinstance(visual_analytics.get('metrics'),Mapping) else {}
    for key in ('verified_outcome_rate_event','verified_outcome_rate_work_time','work_time_coverage_rate','outcome_evidence_coverage_rate','verification_debt_proxy_event'):
        if not isinstance(metrics.get(key),Mapping): raise LiveSnapshotError(f'missing metric {key}')
    event_count=int(visual_analytics.get('event_count',0) or 0)
    activity_raw=visual_analytics.get('activity_distribution') if isinstance(visual_analytics.get('activity_distribution'),Mapping) else {}
    activities=[{'key':str(key),'label_zh':ACTIVITY_LABELS.get(str(key),str(key)),'count':int(value.get('count',0) or 0),'share':value.get('share') if isinstance(value.get('share'),(int,float)) else None} for key,value in sorted(activity_raw.items()) if isinstance(value,Mapping)]
    outcomes=visual_analytics.get('outcome_distribution') if isinstance(visual_analytics.get('outcome_distribution'),Mapping) else {}
    top=activities[0] if activities else {'key':'unknown','label_zh':'暂无数据','count':0,'share':None}
    if activities: top=max(activities,key=lambda row:(row['count'],row['key']))
    verified_metric=metrics['verified_outcome_rate_event']; debt_metric=metrics['verification_debt_proxy_event']
    recommendations=behavior.get('recommendations') if isinstance(behavior.get('recommendations'),list) else []
    rec=recommendations[0] if recommendations and isinstance(recommendations[0],Mapping) else {}
    unknown_count=int(outcomes.get('unknown',0) or 0)
    low_title='结果状态不完整' if unknown_count else '当前未识别稳定低价值循环'
    low_detail=f'{unknown_count} 个事件缺少可验证结果状态。' if unknown_count else '现有证据未支持更强结论。'
    decision={
      'primary_use':{'title_zh':top['label_zh'],'detail_zh':f"{top['count']} 个事件，占当前样本 {round((top['share'] or 0)*100,1)}%。"},
      'verified_results':{'title_zh':f"{int(verified_metric.get('numerator') or 0)} 个已验证结果",'detail_zh':f"事件口径 {round((verified_metric.get('value') or 0)*100,1)}%，分母 {int(verified_metric.get('denominator') or 0)} 个事件。"},
      'low_value_loop':{'title_zh':low_title,'detail_zh':low_detail+f" 验证债务代理为 {round((debt_metric.get('value') or 0)*100,1)}%。"},
      'top_action':{'title_zh':str(rec.get('action','先补齐一条可读回的现实结果证据。')),'detail_zh':str(rec.get('success_metric','下一次运行至少新增一条已验证结果，并确认刷新后仍可读回。')),'recommendation_id':str(rec.get('recommendation_id','insufficient-data')),'confidence':rec.get('confidence') if isinstance(rec.get('confidence'),(int,float)) else None},
    }
    fmetrics=failure.get('metrics') if isinstance(failure.get('metrics'),Mapping) else {}
    evidence=_same_run_evidence(runtime_evidence,run_id,trace_id)
    output={
      'schema_version':'memory_atlas.live_snapshot.v1','generated_at':evaluated_at,
      'run':{'run_id':run_id,'trace_id':trace_id,'source_state':source_state,'source_started_at':run.get('source_started_at') if isinstance(run.get('source_started_at'),str) else None,'source_completed_at':completed_at,'reconciled_at':run.get('reconciled_at') if isinstance(run.get('reconciled_at'),str) else None},
      'release':release_out,
      'freshness':{'state':fresh_state,'evaluated_at':evaluated_at,'age_seconds':age,'target_seconds':freshness_target_seconds,'reason_zh':reason},
      'coverage':{'product_state':product_state,'tier_a_cloud_native':ac,'tier_b_local_optional':bc,'sources':tier_a+tier_b},
      'analysis':{'event_count':event_count,'event_window':visual_analytics.get('event_window',{'start_at':None,'end_at':None}),'activity_distribution':activities,'outcome_distribution':{str(k):int(v) for k,v in outcomes.items()},'verified_outcome_rate_event':dict(metrics['verified_outcome_rate_event']),'verified_outcome_rate_work_time':dict(metrics['verified_outcome_rate_work_time']),'work_time_coverage_rate':dict(metrics['work_time_coverage_rate']),'outcome_evidence_coverage_rate':dict(metrics['outcome_evidence_coverage_rate']),'verification_debt_proxy_event':dict(metrics['verification_debt_proxy_event']),'legacy_verified_outcome_rate':{'value':behavior.get('verified_outcome_rate') if isinstance(behavior.get('verified_outcome_rate'),(int,float)) else None,'denominator_basis':str(behavior.get('verified_outcome_rate_basis','legacy_unknown_or_mixed')),'compatibility_only':True},'failure_compound':{'compound_score':failure.get('compound_score') if isinstance(failure.get('compound_score'),(int,float)) else None,'incident_count':int(fmetrics.get('incident_count',0) or 0),'historical_recurrences':int(fmetrics.get('historical_recurrences',0) or 0),'blocked_recurrences':int(fmetrics.get('blocked_recurrences',0) or 0)}},
      'decision':decision,'visuals':visual_analytics.get('visuals',[]),
      'benchmarks':{'state':benchmark_result.get('state','NOT_COMPARABLE'),'comparisons':benchmark_result.get('comparisons',[]) if isinstance(benchmark_result.get('comparisons'),list) else [],'limitations':benchmark_result.get('limitations',[]) if isinstance(benchmark_result.get('limitations'),list) else []},
      'truth':{'metric_contract_version':'memory_atlas.metric_contract.v1','same_run_evidence':evidence,'historical_snapshot_role':'HISTORICAL_ATLAS_ONLY_NOT_LIVE_TRUTH','limitations':['验证债务是代理指标，不是错误率或个人正确率。','公开 Benchmark 只有完全同口径时才允许直接差值。','浏览器收到时间不等于数据生成时间。']},
      'privacy':{'raw_content_included':False,'secret_values_included':False,'private_paths_included':False,'object_keys_included':False},
    }
    if len(output['visuals'])!=3 or {row.get('id') for row in output['visuals']}!={'quality_contribution_grid','verification_debt_trend','task_tool_outcome_heatmap'}: raise LiveSnapshotError('exactly three canonical visuals are required')
    _scan(output)
    return output
