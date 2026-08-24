from __future__ import annotations
import re
from typing import Any,Dict,Iterable,List,Mapping,Sequence
from .common import digest
TOKEN=re.compile(r'[A-Za-z0-9_\-\u4e00-\u9fff]+')
def behavior_coverage(expected_ids:Sequence[str],records:Sequence[Mapping[str,Any]])->Dict[str,Any]:
    seen={}; errors=[]
    for row in records:
        rid=row.get('id'); status=row.get('status')
        if rid in seen: errors.append(f'duplicate:{rid}')
        seen[rid]=row
        if status not in {'PASS','FAIL','NOT_RUN','NOT_APPLICABLE_WITH_REASON'}: errors.append(f'invalid_status:{rid}')
        if status in {'NOT_RUN','NOT_APPLICABLE_WITH_REASON'} and not str(row.get('reason','')).strip(): errors.append(f'missing_reason:{rid}')
    missing=sorted(set(expected_ids)-set(seen)); extra=sorted(set(seen)-set(expected_ids)); errors += [f'missing:{x}' for x in missing]+[f'extra:{x}' for x in extra]
    return {'valid':not errors,'errors':errors,'total':len(expected_ids),'covered':sum(1 for x in expected_ids if seen.get(x,{}).get('status')=='PASS'),'failed':[x for x in expected_ids if seen.get(x,{}).get('status')=='FAIL'],'not_run':[x for x in expected_ids if seen.get(x,{}).get('status')=='NOT_RUN'],'digest':digest(records)}
def _tokens(text:str): return {x.lower() for x in TOKEN.findall(text) if len(x)>1}
def shadowing(skills:Sequence[Mapping[str,Any]],threshold:float=.72)->Dict[str,Any]:
    rows=[]
    for i,a in enumerate(skills):
        for b in skills[i+1:]:
            ta,tb=_tokens(str(a.get('description',''))),_tokens(str(b.get('description',''))); union=ta|tb; score=len(ta&tb)/len(union) if union else 0.0
            if score>=threshold: rows.append({'a':a.get('slug'),'b':b.get('slug'),'jaccard':round(score,4),'risk':'FALSE_ACTIVATION_OR_SHADOWING'})
    return {'threshold':threshold,'collisions':rows,'collision_count':len(rows),'digest':digest(rows)}
