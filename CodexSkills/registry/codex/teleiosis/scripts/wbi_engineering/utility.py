from __future__ import annotations
from typing import Any,Dict,Mapping,Sequence
def utility_gate(metrics:Mapping[str,float],hard_failures:Sequence[str]=())->Dict[str,Any]:
    if hard_failures: return {'decision':'REVERT','hard_failures':list(hard_failures),'utility':None}
    benefit=float(metrics.get('outcome_gain',0))+float(metrics.get('risk_reduction',0))+float(metrics.get('maintainability_gain',0))
    cost=float(metrics.get('token_cost_delta',0))+float(metrics.get('latency_cost_delta',0))+float(metrics.get('maintenance_cost_delta',0))
    utility=benefit-cost
    return {'decision':'KEEP' if utility>0 else 'NO_CHANGE' if utility==0 else 'REVERT','utility':utility,'benefit':benefit,'cost':cost}
