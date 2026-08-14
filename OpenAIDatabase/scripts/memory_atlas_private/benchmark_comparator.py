from __future__ import annotations

"""Strict benchmark gate. It never emits a personal percentile."""

from typing import Any, Mapping

CONTRACT_FIELDS=("taxonomy_id","unit","window_definition","population_scope","inclusion_rule")


def compare(personal_metrics: Mapping[str, Mapping[str, Any]], registry: Mapping[str, Any]) -> dict[str, Any]:
    comparisons=[]
    for benchmark in registry.get("benchmarks", []):
        metric_key=str(benchmark.get("metric_key", ""))
        personal=personal_metrics.get(metric_key)
        if not isinstance(personal, Mapping) or not isinstance(personal.get("value"),(int,float)):
            comparisons.append(_row(benchmark,None,"INSUFFICIENT_DATA",None,"个人指标或样本不足。")); continue
        mismatches=[field for field in CONTRACT_FIELDS if personal.get(field)!=benchmark.get(field)]
        sample=int(personal.get("sample_size",0) or 0)
        minimum=int(benchmark.get("minimum_sample",0) or 0)
        if mismatches:
            comparisons.append(_row(benchmark,float(personal["value"]),"DIRECTION_ONLY",None,"口径不一致："+"、".join(mismatches)+"。")); continue
        if sample < minimum:
            comparisons.append(_row(benchmark,float(personal["value"]),"INSUFFICIENT_DATA",None,f"样本 {sample} 低于最低 {minimum}。")); continue
        value=float(personal["value"]); reference=float(benchmark["value"])
        comparisons.append(_row(benchmark,value,"DIRECTLY_COMPARABLE",round(value-reference,6),"全部口径字段和最低样本门一致；只显示直接差值，不生成百分位。"))
    states={row['comparability_state'] for row in comparisons}
    if not comparisons or states=={'INSUFFICIENT_DATA'}: state='INSUFFICIENT_DATA'
    elif states=={'DIRECTLY_COMPARABLE'}: state='DIRECTLY_COMPARABLE'
    elif 'DIRECTION_ONLY' in states or 'DIRECTLY_COMPARABLE' in states: state='DIRECTION_ONLY'
    else: state='NOT_COMPARABLE'
    return {'schema_version':'memory_atlas.benchmark_result.v1','state':state,'comparisons':comparisons,'limitations':['公开研究不是个人随机对照组。','不生成个人全球百分位、排名或优劣结论。']}


def _row(benchmark: Mapping[str,Any], personal_value: float|None, state: str, delta: float|None, reason: str) -> dict[str,Any]:
    return {'benchmark_id':benchmark.get('benchmark_id'),'label_zh':benchmark.get('label_zh'),'metric_key':benchmark.get('metric_key'),'personal_value':personal_value,'benchmark_value':benchmark.get('value'),'unit':benchmark.get('unit'),'comparability_state':state,'delta':delta,'percentile':None,'reason_zh':reason,'source':benchmark.get('source',{})}
