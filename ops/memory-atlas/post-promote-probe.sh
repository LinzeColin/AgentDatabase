#!/usr/bin/env bash
set -euo pipefail
release_id=${1:?release_id required}
origin=${MEMORY_ATLAS_EXTERNAL_ORIGIN:-https://memoryatlas.linzezhang.com}
tmp_dir=$(mktemp -d /tmp/memory-atlas-probe.XXXXXX)
trap 'rm -rf "$tmp_dir"' EXIT

container_http_status() {
  local url=${1:?url required}
  local stem=${2:?stem required}
  docker exec memory-atlas-web sh -c '
    url=$1; stem=$2
    body="/tmp/${stem}.body"; headers="/tmp/${stem}.headers"
    wget -S -O "$body" "$url" 2>"$headers" || true
    code=$(awk '\''$1 ~ /^HTTP\// {value=$2} END {print value}'\'' "$headers")
    rm -f "$body" "$headers"
    printf "%s" "${code:-000}"
  ' sh "$url" "$stem" 2>/dev/null || printf '000'
}

internal_api_health=$(curl --silent --show-error --max-time 8 --write-out '%{http_code}' --output "$tmp_dir/api-health" http://127.0.0.1:8766/healthz || true)
internal_api_private=$(curl --silent --show-error --max-time 8 --write-out '%{http_code}' --output "$tmp_dir/api-private" http://127.0.0.1:8766/api/v31/status || true)
internal_proxy_api_health=$(container_http_status http://host.docker.internal:18766/healthz ma-proxy-api-health)
internal_proxy_private=$(container_http_status http://127.0.0.1:8088/api/v31/status ma-proxy-private)
internal_web=$(container_http_status http://127.0.0.1:8088/healthz ma-web-health)
internal_static_private=$(container_http_status http://127.0.0.1:8088/data/memory_atlas_private_analytics.json ma-static-private)
public_health=$(curl --silent --show-error --max-time 12 --write-out '%{http_code}' --output "$tmp_dir/public-health" "$origin/healthz" || true)
public_private=$(curl --silent --show-error --max-time 12 --write-out '%{http_code}' --output "$tmp_dir/public-private" "$origin/api/v31/status" || true)

[[ "$internal_api_health" == "200" ]] || { echo "INTERNAL_API_HEALTH_FAIL:$internal_api_health"; exit 2; }
[[ "$internal_api_private" == "403" ]] || { echo "INTERNAL_PRIVATE_API_NOT_FAIL_CLOSED:$internal_api_private"; exit 2; }
[[ "$internal_proxy_api_health" == "200" ]] || { echo "INTERNAL_PROXY_API_HEALTH_FAIL:$internal_proxy_api_health"; exit 2; }
[[ "$internal_proxy_private" == "403" ]] || { echo "INTERNAL_PROXY_PRIVATE_API_NOT_FAIL_CLOSED:$internal_proxy_private"; exit 2; }
[[ "$internal_web" == "200" ]] || { echo "INTERNAL_WEB_FAIL:$internal_web"; exit 2; }
[[ "$internal_static_private" == "404" ]] || { echo "STATIC_PRIVATE_SNAPSHOT_EXPOSED:$internal_static_private"; exit 2; }
for pair in "health:$public_health" "private:$public_private"; do
  name=${pair%%:*}; code=${pair#*:}
  case "$code" in
    200) echo "UNAUTHENTICATED_PUBLIC_${name^^}_UNEXPECTEDLY_OPEN"; exit 3 ;;
    000) echo "PUBLIC_${name^^}_PATH_UNREACHABLE"; exit 3 ;;
    *) : ;;
  esac
done

state="DEPLOYED_INTERNAL_VERIFIED_OWNER_ACCESS_CONFIRMATION_PENDING"
auth_health="NOT_RUN"
auth_private="NOT_RUN"
if [[ -n "${CF_ACCESS_CLIENT_ID:-}" && -n "${CF_ACCESS_CLIENT_SECRET:-}" ]]; then
  auth_args=(-H "CF-Access-Client-Id: $CF_ACCESS_CLIENT_ID" -H "CF-Access-Client-Secret: $CF_ACCESS_CLIENT_SECRET")
  auth_health=$(curl --silent --show-error --max-time 12 --write-out '%{http_code}' --output "$tmp_dir/auth-health" "${auth_args[@]}" "$origin/healthz" || true)
  auth_private=$(curl --silent --show-error --max-time 12 --write-out '%{http_code}' --output "$tmp_dir/auth-private" "${auth_args[@]}" "$origin/api/v31/status" || true)
  if [[ "$auth_health" == "200" && "$auth_private" == "200" ]]; then
    state="POST_PROMOTION_AUTHENTICATED_PATH_VERIFIED"
  else
    echo "AUTHENTICATED_PATH_FAIL:health=$auth_health private=$auth_private"
    exit 4
  fi
fi
# v0.0.0.32 T08: the container must be serving the release that was just
# promoted, not the one it happened to start on. Compare the asset names on
# disk with the asset names the container answers with.
released_assets=$(ls "/srv/linze/apps/memory-atlas/current/dist/assets" 2>/dev/null | sort | tr '\n' ' ')
served_assets=$(docker exec memory-atlas-web ls /usr/share/nginx/html/assets 2>/dev/null | sort | tr '\n' ' ')
if [[ -z "$served_assets" || "$released_assets" != "$served_assets" ]]; then
  echo "SERVED_ARTIFACT_IS_NOT_THE_PROMOTED_RELEASE"
  echo "  released: $released_assets"
  echo "  served:   $served_assets"
  exit 7
fi

# v0.0.0.32 T07: the checks above prove the surface is up and fails closed. They
# say nothing about whether the numbers on the page came from this release. The
# live probe compares API headers against the API body, requires no-store, and
# pins the release and deployment identity. Without an Access service token it
# reports NOT_RUN, which is recorded rather than treated as a pass.
live_probe_state="NOT_RUN"
if [[ -n "${CF_ACCESS_CLIENT_ID:-}" && -n "${CF_ACCESS_CLIENT_SECRET:-}" ]]; then
  live_dir="/srv/linze/apps/memory-atlas/shared/post-promote-live"
  if "$(dirname "$0")/post-promote-live-probe.sh" "$origin" "$release_id" \
      "${MEMORY_ATLAS_DEPLOYMENT_REVISION:-UNVERIFIED}" "$live_dir" >/dev/null; then
    live_probe_state="PASS"
  else
    echo "LIVE_SNAPSHOT_PROBE_FAIL"
    exit 6
  fi
fi

printf '{"schema_version":"memory_atlas.post_promote_probe.v3","live_snapshot_probe":"'"$live_probe_state"'","release_id":"%s","state":"%s","internal_api_health":%s,"internal_api_private":%s,"internal_proxy_api_health":%s,"internal_proxy_private":%s,"internal_web":%s,"internal_static_private":%s,"unauthenticated_public_health":%s,"unauthenticated_public_private":%s,"authenticated_public_health":"%s","authenticated_public_private":"%s","checked_at":"%s"}\n' \
  "$release_id" "$state" "$internal_api_health" "$internal_api_private" "$internal_proxy_api_health" "$internal_proxy_private" "$internal_web" "$internal_static_private" "$public_health" "$public_private" "$auth_health" "$auth_private" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
  | tee /srv/linze/apps/memory-atlas/shared/post-promote-probe.json
[[ "$state" == "POST_PROMOTION_AUTHENTICATED_PATH_VERIFIED" ]] || exit 5
