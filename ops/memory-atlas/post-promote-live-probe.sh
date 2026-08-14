#!/usr/bin/env bash
# v0.0.0.32 T07 — live-snapshot identity probe for the existing post-promote step.
#
#   post-promote-live-probe.sh <origin> <expected-release-id> <expected-deployment-revision> <output-dir>
#
# Adapted from the taskpack's implementation/runtime/post_promote_live_probe.sh.
# Two changes, both because of how this deployment actually works:
#
#   1. The origin is reached through Cloudflare Access. Without a service-token
#      pair the probe cannot authenticate, so it reports NOT_RUN rather than
#      calling an unauthenticated 302 a pass.
#   2. `UNVERIFIED` is accepted for release/deployment identity only when the
#      caller passes `UNVERIFIED` as the expectation, so an unidentified release
#      can never satisfy an expectation of a real one.
set -euo pipefail
umask 077

if [[ $# -ne 4 ]]; then
  echo "usage: post-promote-live-probe.sh <origin> <expected-release-id> <expected-deployment-revision> <output-dir>" >&2
  exit 64
fi
origin="${1%/}"
expected_release="$2"
expected_deployment="$3"
output_dir="$4"
mkdir -p "$output_dir"
headers="$output_dir/live_snapshot.headers"
body="$output_dir/live_snapshot.json"
receipt="$output_dir/API_RECEIPT.json"

if [[ -z "${CF_ACCESS_CLIENT_ID:-}" || -z "${CF_ACCESS_CLIENT_SECRET:-}" ]]; then
  printf '{"schema_version":"memory_atlas.api_receipt.v1","state":"NOT_RUN","reason":"no Cloudflare Access service token; an unauthenticated probe proves nothing","origin":"%s","checked_at":"%s"}\n' \
    "$origin" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" >"$receipt"
  chmod 600 "$receipt"
  echo "LIVE_PROBE_NOT_RUN_NO_ACCESS_TOKEN" >&2
  exit 3
fi

curl --silent --show-error --fail-with-body --location --connect-timeout 10 --max-time 45 \
  -D "$headers" -o "$body" -H 'Accept: application/json' \
  -H "CF-Access-Client-Id: ${CF_ACCESS_CLIENT_ID}" \
  -H "CF-Access-Client-Secret: ${CF_ACCESS_CLIENT_SECRET}" \
  "$origin/api/v31/live-snapshot"

python3 - "$headers" "$body" "$receipt" "$expected_release" "$expected_deployment" <<'PYPROBE'
from __future__ import annotations
import json, sys
from datetime import datetime, timezone
from pathlib import Path

headers_path, body_path, output_path, expected_release, expected_deployment = sys.argv[1:6]
body = json.loads(Path(body_path).read_text(encoding="utf-8"))
headers = {}
for line in Path(headers_path).read_text(encoding="utf-8", errors="replace").splitlines():
    if ":" in line:
        key, value = line.split(":", 1)
        headers[key.strip().lower()] = value.strip()

identity = {
    "run_id": body["run"]["run_id"],
    "trace_id": body["run"]["trace_id"],
    "release_id": body["release"]["release_id"],
    "deployment_revision": body["release"]["deployment_revision"],
}
from_headers = {
    "run_id": headers.get("x-memory-atlas-run-id"),
    "trace_id": headers.get("x-memory-atlas-trace-id"),
    "release_id": headers.get("x-memory-atlas-release-id"),
    "deployment_revision": headers.get("x-memory-atlas-deployment-revision"),
}

errors = []
for key, value in identity.items():
    if from_headers[key] != (value if value is not None else "UNVERIFIED"):
        errors.append(f"header/body mismatch: {key}")
if (identity["release_id"] or "UNVERIFIED") != expected_release:
    errors.append(f"unexpected release_id: {identity['release_id']!r} != {expected_release!r}")
if (identity["deployment_revision"] or "UNVERIFIED") != expected_deployment:
    errors.append(f"unexpected deployment_revision: {identity['deployment_revision']!r} != {expected_deployment!r}")
if "no-store" not in headers.get("cache-control", "").lower():
    errors.append("cache-control missing no-store")
if body.get("privacy", {}) != {
    "raw_content_included": False, "secret_values_included": False,
    "private_paths_included": False, "object_keys_included": False,
}:
    errors.append("privacy contract not satisfied")
if len(body.get("visuals", [])) != 3:
    errors.append("visual contract not satisfied")

receipt = {
    "schema_version": "memory_atlas.api_receipt.v1",
    "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    "state": "PASS" if not errors else "FAIL",
    **identity,
    "cache_control": headers.get("cache-control"),
    "etag": headers.get("etag"),
    "freshness_state": body.get("freshness", {}).get("state"),
    "product_state": body.get("coverage", {}).get("product_state"),
    "errors": errors,
}
Path(output_path).write_text(json.dumps(receipt, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
if errors:
    raise SystemExit(2)
PYPROBE

chmod 600 "$headers" "$body" "$receipt"
printf '%s\n' "$receipt"
