#!/usr/bin/env bash
set -euo pipefail
APP_ROOT=${MEMORY_ATLAS_APP_ROOT:-/srv/linze/apps/memory-atlas}
AGENT_ROOT=${MEMORY_ATLAS_AGENT_ROOT:-/srv/linze/apps/agentdatabase}
[[ -L "$APP_ROOT/previous" && -d "$(readlink -f "$APP_ROOT/previous")" ]] || { echo '没有可用前端 previous release'; exit 70; }
[[ -L "$AGENT_ROOT/previous" && -d "$(readlink -f "$AGENT_ROOT/previous")" ]] || { echo '没有可用 AgentDatabase previous release'; exit 70; }
current_app=$(readlink -f "$APP_ROOT/current"); current_agent=$(readlink -f "$AGENT_ROOT/current")
previous_app=$(readlink -f "$APP_ROOT/previous"); previous_agent=$(readlink -f "$AGENT_ROOT/previous")
ln -sfn "$previous_app" "$APP_ROOT/current"; ln -sfn "$previous_agent" "$AGENT_ROOT/current"
ln -sfn "$current_app" "$APP_ROOT/previous"; ln -sfn "$current_agent" "$AGENT_ROOT/previous"
sudo systemctl stop memory-atlas-api-proxy.socket memory-atlas-api-proxy.service
sudo systemctl restart memory-atlas-api.service
sudo systemctl start memory-atlas-api-proxy.socket
docker compose -f "$AGENT_ROOT/current/ops/memory-atlas/docker-compose.yml" up -d --remove-orphans
curl --fail --silent --max-time 8 http://127.0.0.1:8766/healthz >/dev/null
curl --fail --silent --max-time 8 http://10.0.0.1:18766/healthz >/dev/null
docker exec memory-atlas-web sh -c 'wget -qO- http://127.0.0.1:8088/healthz >/dev/null'
printf '{"schema_version":"memory_atlas.rollback.v1","state":"PASS","rolled_back_at":"%s","active_app":"%s","active_agent":"%s"}
' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$previous_app" "$previous_agent" > "$APP_ROOT/shared/rollback.json"
cat "$APP_ROOT/shared/rollback.json"
