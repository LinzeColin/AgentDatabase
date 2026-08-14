from __future__ import annotations

"""Framework-neutral response helper; caller must reuse the existing Access verifier."""

import hashlib, json
from pathlib import Path
from typing import Any
try:  # package import inside memory_atlas_private
    from .live_snapshot_store import LiveSnapshotStore
except ImportError:  # flat import when the module dir is the top level
    from live_snapshot_store import LiveSnapshotStore


def response(store_root: Path,schema_path: Path,*,authorized: bool) -> tuple[int,dict[str,str],bytes]:
    base={'Content-Type':'application/json; charset=utf-8','Cache-Control':'private, no-store, max-age=0','Pragma':'no-cache','Vary':'Cookie, Cf-Access-Jwt-Assertion'}
    if not authorized: return 403,base,json.dumps({'error':'forbidden'},ensure_ascii=False).encode()
    current=Path(store_root)/'current.json'
    if not current.exists(): return 404,base,json.dumps({'error':'live_snapshot_not_available'},ensure_ascii=False).encode()
    try:
        store=LiveSnapshotStore(store_root,schema_path); value=store.read_current()
        if value is None: raise ValueError('missing')
    except Exception:
        return 503,base,json.dumps({'error':'live_snapshot_invalid'},ensure_ascii=False).encode()
    body=(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'))+'\n').encode()
    headers=base|{'ETag':'"'+hashlib.sha256(body).hexdigest()+'"','X-Memory-Atlas-Run-Id':value['run']['run_id'],'X-Memory-Atlas-Trace-Id':value['run']['trace_id'],'X-Memory-Atlas-Release-Id':value['release']['release_id'] or 'UNVERIFIED','X-Memory-Atlas-Deployment-Revision':value['release']['deployment_revision'] or 'UNVERIFIED'}
    return 200,headers,body
