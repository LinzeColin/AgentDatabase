#!/usr/bin/env bash
set -euo pipefail
systemctl start memory-atlas-api.service memory-atlas-api-proxy.socket memory-atlas-reconcile.timer memory-atlas-selfheal.timer memory-atlas-action-worker.timer
systemctl start memory-atlas-reconcile.service memory-atlas-action-worker.service
curl --fail --silent --max-time 8 http://127.0.0.1:8766/healthz >/dev/null
curl --fail --silent --max-time 8 http://10.0.0.1:18766/healthz >/dev/null
printf '%s
' 'MEMORY_ATLAS_STARTED'
