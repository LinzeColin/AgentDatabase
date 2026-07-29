from __future__ import annotations
from datetime import datetime,timezone
from typing import Any,Dict,Mapping
def _dt(v:str)->datetime:return datetime.fromisoformat(v.replace('Z','+00:00'))
def validate_lease(lease:Mapping[str,Any],identity:Mapping[str,str],now:str)->Dict[str,Any]:
    reasons=[]
    for key in ('candidate_hash','acceptance_hash','environment_hash','dataset_hash','toolchain_hash'):
        if key in lease and lease.get(key)!=identity.get(key): reasons.append(f'{key}_changed')
    if _dt(now)>_dt(str(lease['expires_at'])): reasons.append('expired')
    return {'valid':not reasons,'state':'FRESH' if not reasons else 'STALE','reasons':reasons}
