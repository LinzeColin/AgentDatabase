from __future__ import annotations
import hashlib,json
from typing import Any
def canonical(v:Any)->str:return json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':'))
def digest(v:Any)->str:return hashlib.sha256(canonical(v).encode()).hexdigest()
