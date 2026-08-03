#!/usr/bin/env bash
set -euo pipefail
printf '%s
' '=== services ==='
systemctl --no-pager --full status memory-atlas-api.service memory-atlas-api-proxy.socket memory-atlas-api-proxy.service memory-atlas-reconcile.timer memory-atlas-selfheal.timer memory-atlas-action-worker.timer || true
printf '%s
' '=== timers ==='
systemctl list-timers --all --no-pager | grep 'memory-atlas' || true
printf '%s
' '=== internal health ==='
curl --silent --show-error --max-time 8 http://127.0.0.1:8766/healthz || true
printf '\n%s\n' '=== Docker bridge proxy health ==='
curl --silent --show-error --max-time 8 http://10.0.0.1:18766/healthz || true
printf '
%s
' '=== latest reconcile ==='
journalctl -u memory-atlas-reconcile.service -n 80 --no-pager || true
printf '%s
' '=== latest action worker ==='
journalctl -u memory-atlas-action-worker.service -n 80 --no-pager || true
printf '%s
' '=== last promotion and probe ==='
for f in /srv/linze/apps/memory-atlas/shared/promotion.json /srv/linze/apps/memory-atlas/shared/post-promote-probe.json; do [[ -f "$f" ]] && cat "$f" || true; done
printf '%s
' '=== disk and memory ==='
df -h / /srv/linze 2>/dev/null || df -h /
free -h
