#!/usr/bin/env bash
set -euo pipefail
systemctl stop memory-atlas-action-worker.timer memory-atlas-selfheal.timer memory-atlas-reconcile.timer memory-atlas-api-proxy.socket memory-atlas-api-proxy.service memory-atlas-api.service
printf '%s
' 'MEMORY_ATLAS_STOPPED'
