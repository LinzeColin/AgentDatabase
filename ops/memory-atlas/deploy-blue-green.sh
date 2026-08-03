#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=${1:?用法: deploy-blue-green.sh REPO_ROOT}
APP_ROOT=${MEMORY_ATLAS_APP_ROOT:-/srv/linze/apps/memory-atlas}
AGENT_ROOT=${MEMORY_ATLAS_AGENT_ROOT:-/srv/linze/apps/agentdatabase}
ENV_FILE=${MEMORY_ATLAS_ENV_FILE:-/srv/linze/secrets/memory-atlas.env}
VENV=${MEMORY_ATLAS_VENV:-/srv/linze/venvs/memory-atlas}

remove_symlink_if_target() {
  local link_path=${1:?link path required}
  local expected_target=${2:?expected target required}
  local resolved=''
  if [[ -L "$link_path" ]]; then
    resolved=$(readlink -f "$link_path" 2>/dev/null || true)
    if [[ "$resolved" == "$expected_target" ]]; then
      unlink "$link_path"
    fi
  fi
}

rollback_first_deploy_to_absent() {
  local failed_probe_rc=${1:?probe rc required}
  local cleanup_rc=0
  set +e
  sudo systemctl disable --now \
    memory-atlas-api.service \
    memory-atlas-api-proxy.socket \
    memory-atlas-reconcile.timer \
    memory-atlas-selfheal.timer \
    memory-atlas-action-worker.timer || cleanup_rc=1
  sudo systemctl stop \
    memory-atlas-api-proxy.service \
    memory-atlas-reconcile.service \
    memory-atlas-selfheal.service \
    memory-atlas-action-worker.service || cleanup_rc=1
  docker compose -f "$agent_release/ops/memory-atlas/docker-compose.yml" down --remove-orphans || cleanup_rc=1
  remove_symlink_if_target "$APP_ROOT/current" "$release" || cleanup_rc=1
  remove_symlink_if_target "$AGENT_ROOT/current" "$agent_release" || cleanup_rc=1
  remove_symlink_if_target "$APP_ROOT/candidate" "$release" || cleanup_rc=1
  remove_symlink_if_target "$AGENT_ROOT/candidate" "$agent_release" || cleanup_rc=1
  if [[ -f "$APP_ROOT/shared/promotion.json" ]]; then
    mv "$APP_ROOT/shared/promotion.json" "$APP_ROOT/shared/failed-promotion-$release_id.json" || cleanup_rc=1
  fi
  if [[ -f "$APP_ROOT/shared/LAST_PROMOTED_RELEASE" ]]; then
    mv "$APP_ROOT/shared/LAST_PROMOTED_RELEASE" "$APP_ROOT/shared/LAST_FAILED_RELEASE" || cleanup_rc=1
  fi
  set -e
  if [[ "$cleanup_rc" -ne 0 ]]; then
    echo "FIRST_DEPLOY_ABSENCE_ROLLBACK_FAILED:$failed_probe_rc"
    return 1
  fi
  printf '{"schema_version":"memory_atlas.rollback.v1","state":"PASS","mode":"FIRST_DEPLOY_ABSENCE_RESTORED","failed_probe_rc":%s,"release_id":"%s","rolled_back_at":"%s"}\n' \
    "$failed_probe_rc" "$release_id" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$APP_ROOT/shared/rollback.json"
  cat "$APP_ROOT/shared/rollback.json"
  printf '%s\n' 'FIRST_DEPLOY_ABSENCE_RESTORED'
}

rollback_promoted_release() {
  local failed_rc=${1:?failure rc required}
  if [[ -n "$old_app" && -n "$old_agent" ]]; then
    "$agent_release/ops/memory-atlas/rollback.sh"
  else
    rollback_first_deploy_to_absent "$failed_rc"
  fi
}

post_promotion_error() {
  local failed_rc=$?
  local rollback_rc=0
  trap - ERR
  set +e
  rollback_promoted_release "$failed_rc" || rollback_rc=$?
  set -e
  if [[ "$rollback_rc" -ne 0 ]]; then
    echo "POST_PROMOTION_STEP_FAILED_ROLLBACK_FAILED:$failed_rc:$rollback_rc"
  else
    echo "POST_PROMOTION_STEP_FAILED_AND_ROLLED_BACK:$failed_rc"
  fi
  exit "$failed_rc"
}

[[ -f "$ENV_FILE" ]] || { echo "缺少受保护环境文件: $ENV_FILE"; exit 65; }
[[ -f "$REPO_ROOT/AGENTS.md" && -d "$REPO_ROOT/MemoryAtlas" ]] || { echo '目标不是 AgentDatabase 根目录'; exit 66; }
cd "$REPO_ROOT"
set -a
# shellcheck disable=SC1090
source "$ENV_FILE"
set +a
python3 -B OpenAIDatabase/scripts/lean_governance.py --database-dir OpenAIDatabase validate
sudo install -d -m 0750 -o "$(id -un)" -g "$(id -gn)" "$(dirname "$VENV")"
python3 -m venv "$VENV"
"$VENV/bin/python" -m pip install --disable-pip-version-check --requirement "$REPO_ROOT/OpenAIDatabase/scripts/memory_atlas_private/requirements-memory-atlas-private.txt"
PYTHONDONTWRITEBYTECODE=1 "$VENV/bin/python" -B -m pytest -q -p no:cacheprovider OpenAIDatabase/tests/test_memory_atlas_private_v31.py
npm --prefix MemoryAtlas ci
npm --prefix MemoryAtlas run lint
npm --prefix MemoryAtlas run validate:v31
# The retired CodexProject whole-project validator asserts the pre-split remote
# and layout. The frozen v0.0.0.31 validator plus focused backend suite above are
# the current AgentDatabase release Oracle.
npm --prefix MemoryAtlas run build
deploy_user=$(id -un)
deploy_group=$(id -gn)
sudo install -d -m 0750 -o "$deploy_user" -g "$deploy_group" \
  "$APP_ROOT" \
  "$APP_ROOT/releases" \
  "$APP_ROOT/shared" \
  "$APP_ROOT/shared/data" \
  "$APP_ROOT/shared/public-baseline" \
  "$AGENT_ROOT" \
  "$AGENT_ROOT/releases"
release_id="$(date -u +%Y%m%dT%H%M%SZ)-$(git rev-parse --short=12 HEAD)"
release="$APP_ROOT/releases/$release_id"
agent_release="$AGENT_ROOT/releases/$release_id"
mkdir -p "$release" "$APP_ROOT/shared/data" "$APP_ROOT/shared/public-baseline" "$agent_release"
cp -a MemoryAtlas/dist "$release/dist"
if [[ -f MemoryAtlas/public/memory_atlas.json ]]; then cp -f MemoryAtlas/public/memory_atlas.json "$APP_ROOT/shared/public-baseline/memory_atlas.json"; fi
rsync -a --delete --exclude '.git' --exclude 'node_modules' --exclude 'dist' --exclude '__pycache__' --exclude '.pytest_cache' --exclude '*.pyc' "$REPO_ROOT/" "$agent_release/"
ln -sfn "$agent_release" "$AGENT_ROOT/candidate"
ln -sfn "$release" "$APP_ROOT/candidate"
export PYTHONPATH="$agent_release"
export MEMORY_ATLAS_PRIVATE_DB_CLIENT="$agent_release/OpenAIDatabase/scripts/private_db_client.py"
export MEMORY_ATLAS_SOURCE_REGISTRY="$agent_release/ops/memory-atlas/source-registry.json"
export MEMORY_ATLAS_RUNTIME_DIR=${MEMORY_ATLAS_RUNTIME_DIR:-/srv/linze/state/memory-atlas}
export MEMORY_ATLAS_WORK_DIR=${MEMORY_ATLAS_WORK_DIR:-/srv/linze/work/memory-atlas}
export MEMORY_ATLAS_WEB_DATA_DIR=${MEMORY_ATLAS_WEB_DATA_DIR:-$APP_ROOT/shared/data}
export MEMORY_ATLAS_PUBLIC_SNAPSHOT=${MEMORY_ATLAS_PUBLIC_SNAPSHOT:-$APP_ROOT/shared/public-baseline/memory_atlas.json}
sudo "$agent_release/ops/memory-atlas/install-systemd.sh" "$agent_release"
/srv/linze/venvs/memory-atlas/bin/python -B -m OpenAIDatabase.scripts.memory_atlas_private doctor >/dev/null
/srv/linze/venvs/memory-atlas/bin/python -B -m OpenAIDatabase.scripts.memory_atlas_private preflight >/dev/null
old_app=''; old_agent=''
if [[ -L "$APP_ROOT/current" ]]; then old_app=$(readlink -f "$APP_ROOT/current"); ln -sfn "$old_app" "$APP_ROOT/previous"; fi
if [[ -L "$AGENT_ROOT/current" ]]; then old_agent=$(readlink -f "$AGENT_ROOT/current"); ln -sfn "$old_agent" "$AGENT_ROOT/previous"; fi
ln -sfn "$release" "$APP_ROOT/current"
ln -sfn "$agent_release" "$AGENT_ROOT/current"
trap post_promotion_error ERR
sudo systemctl restart memory-atlas-api.service
sudo systemctl enable --now memory-atlas-api-proxy.socket memory-atlas-reconcile.timer memory-atlas-selfheal.timer memory-atlas-action-worker.timer
docker compose -f "$AGENT_ROOT/current/ops/memory-atlas/docker-compose.yml" up -d --remove-orphans
sudo systemctl restart memory-atlas-reconcile.service memory-atlas-action-worker.service
printf '%s
' "$release_id" > "$APP_ROOT/shared/LAST_PROMOTED_RELEASE"
printf '{"schema_version":"memory_atlas.promotion.v1","release_id":"%s","git_commit":"%s","promoted_at":"%s"}
' "$release_id" "$(git rev-parse HEAD)" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" > "$APP_ROOT/shared/promotion.json"
trap - ERR
set +e
"$agent_release/ops/memory-atlas/post-promote-probe.sh" "$release_id"
probe_rc=$?
set -e
case "$probe_rc" in
  0) printf '%s
' 'MEMORY_ATLAS_DEPLOYED_AND_AUTHENTICATED_PATH_VERIFIED' ;;
  5) printf '%s
' 'MEMORY_ATLAS_DEPLOYED_INTERNAL_VERIFIED_OWNER_ACCESS_CONFIRMATION_PENDING'; exit 5 ;;
  *)
    rollback_promoted_release "$probe_rc" || true
    echo "POST_PROMOTE_BLOCKED_AND_ROLLED_BACK:$probe_rc"; exit "$probe_rc" ;;
esac
