from __future__ import annotations
from typing import Any,Dict,Mapping,Sequence
def independent_panel(reviews:Sequence[Mapping[str,Any]],verifier:Mapping[str,Any]|None)->Dict[str,Any]:
    actors=[str(x.get('actor_id','')) for x in reviews]; contexts=[str(x.get('context_id','')) for x in reviews]; providers=[str(x.get('provider_run_id','')) for x in reviews]
    reasons=[]
    if len(reviews)!=12: reasons.append('requires_12_reviews')
    if len(set(actors))!=len(actors) or '' in actors: reasons.append('review_actor_not_unique')
    if len(set(contexts))!=len(contexts) or '' in contexts: reasons.append('review_context_not_unique')
    if len(set(providers))!=len(providers) or '' in providers: reasons.append('provider_run_not_unique')
    if not verifier: reasons.append('verifier_missing')
    else:
        va=str(verifier.get('actor_id','')); vc=str(verifier.get('context_id',''))
        if va in set(actors) or not va: reasons.append('verifier_actor_not_independent')
        if vc in set(contexts) or not vc: reasons.append('verifier_context_not_independent')
        if verifier.get('mode')!='READ_ONLY': reasons.append('verifier_not_read_only')
    return {'status':'PASS' if not reasons else 'INDEPENDENT_REVIEW_UNAVAILABLE','reasons':reasons}
