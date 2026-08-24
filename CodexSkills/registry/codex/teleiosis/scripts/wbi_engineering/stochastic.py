from __future__ import annotations
import random,statistics
from typing import Dict,Sequence
def paired_comparison(baseline:Sequence[float],candidate:Sequence[float],trials:int=2000,seed:int=0,alpha:float=.05)->Dict[str,object]:
    if len(baseline)!=len(candidate) or not baseline: raise ValueError('paired non-empty arrays required')
    diffs=[c-b for b,c in zip(baseline,candidate)]; rng=random.Random(seed); means=[]
    for _ in range(trials): means.append(statistics.fmean(rng.choice(diffs) for _ in diffs))
    means.sort(); lo=means[int((alpha/2)*trials)]; hi=means[min(trials-1,int((1-alpha/2)*trials))]; mean=statistics.fmean(diffs)
    decision='IMPROVED' if lo>0 else 'REGRESSED' if hi<0 else 'INCONCLUSIVE'
    return {'pairs':len(diffs),'mean_delta':mean,'ci':[lo,hi],'trials':trials,'seed':seed,'decision':decision}
