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
# The API is restarted three lines above and takes a second or two to bind, so
# a single immediate probe is a race: a rollback that actually succeeded would
# report failure, and this runs in exactly the situation where that matters
# most. Bounded retry, same total patience for each probe.
await_ok() {
  local what=$1; shift
  for _ in $(seq 1 20); do
    if "$@" >/dev/null 2>&1; then return 0; fi
    sleep 1
  done
  echo "rollback health probe never came up: $what" >&2
  return 1
}
await_ok api curl --fail --silent --max-time 8 http://127.0.0.1:8766/healthz
await_ok api-proxy curl --fail --silent --max-time 8 http://10.0.0.1:18766/healthz
await_ok web docker exec memory-atlas-web sh -c 'wget -qO- http://127.0.0.1:8088/healthz'
printf '{"schema_version":"memory_atlas.rollback.v1","state":"PASS","rolled_back_at":"%s","active_app":"%s","active_agent":"%s"}
' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$previous_app" "$previous_agent" > "$APP_ROOT/shared/rollback.json"
cat "$APP_ROOT/shared/rollback.json"
