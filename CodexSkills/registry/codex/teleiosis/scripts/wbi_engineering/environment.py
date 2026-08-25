from __future__ import annotations
from typing import Any,Dict,Mapping,Sequence
DOMAINS=('model_runtime','tooling','network','sandbox','dataset','holdout','review_independence','verifier_independence')
def environment_strength(attestation:Mapping[str,Any])->Dict[str,Any]:
    missing=[x for x in DOMAINS if x not in attestation]; unproven=[x for x in DOMAINS if attestation.get(x) not in {'PROVEN','AVAILABLE','ISOLATED'}]
    return {'status':'PROVEN' if not missing and not unproven else 'NOT_PROVEN','missing':missing,'unproven':unproven,'domains':len(DOMAINS)}
def portability(rows:Sequence[Mapping[str,Any]])->Dict[str,Any]:
    failures=[dict(x) for x in rows if x.get('status') not in {'PASS','NOT_APPLICABLE_WITH_REASON'}]
    return {'status':'PASS' if not failures else 'NOT_PROVEN','matrix_rows':len(rows),'failures':failures}
