#!/usr/bin/env bash
# v0.0.0.32 T10 — durability and recovery, executed rather than described.
#
#   durability_recovery_drill.sh <output-dir>
#
# Freezes the candidate, then does the four things the acceptance contract names
# and reads the world back after each one: restart the API and the container,
# blue-green rollback and roll-forward, and restore the snapshot store into an
# isolated directory. Each step records what it observed, so a receipt that says
# PASS can be checked against a digest rather than believed.
#
# It never deletes a history object or a fact. Rollback and roll-forward move
# symlinks the deploy already maintains; the restore step only reads.
set -euo pipefail
umask 077

OUT=${1:?用法: durability_recovery_drill.sh OUTPUT_DIR}
APP_ROOT=${MEMORY_ATLAS_APP_ROOT:-/srv/linze/apps/memory-atlas}
AGENT_ROOT=${MEMORY_ATLAS_AGENT_ROOT:-/srv/linze/apps/agentdatabase}
STORE="$APP_ROOT/shared/data/live-snapshot"
API=${MEMORY_ATLAS_INTERNAL_API:-http://127.0.0.1:8766}
mkdir -p "$OUT"

now() { date -u +%Y-%m-%dT%H:%M:%SZ; }
digest() { sudo sha256sum "$1" 2>/dev/null | cut -d' ' -f1; }

identity() {
  sudo python3 - "$STORE/current.json" <<'PY'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
except Exception as exc:
    print(json.dumps({"readable": False, "reason": f"{type(exc).__name__}: {exc}"}))
    raise SystemExit(0)
print(json.dumps({
    "readable": True,
    "schema_version": d.get("schema_version"),
    "run_id": d["run"]["run_id"], "trace_id": d["run"]["trace_id"],
    "source_completed_at": d["run"]["source_completed_at"],
    "release_id": d["release"].get("release_id"),
    "deployment_revision": d["release"].get("deployment_revision"),
    "artifact_digest": d["release"].get("artifact_digest"),
    "event_count": d["analysis"]["event_count"],
}, ensure_ascii=False))
PY
}

health() {
  # curl prints 000 and exits non-zero on failure, so a `|| echo 000` fallback
  # concatenates into "000000". The status line is the answer either way.
  printf '{"internal_api":"%s","internal_web":"%s"}' \
    "$(curl -s -o /dev/null -w '%{http_code}' --max-time 8 "$API/healthz" 2>/dev/null || true)" \
    "$(sudo docker exec memory-atlas-web sh -c 'wget -qO- http://127.0.0.1:8088/healthz >/dev/null && echo 200' 2>/dev/null || echo 000)"
}

frozen_release=$(basename "$(readlink -f "$APP_ROOT/current")")
frozen_agent=$(basename "$(readlink -f "$AGENT_ROOT/current")")
frozen_identity=$(identity)
frozen_current=$(digest "$STORE/current.json")
frozen_previous=$(digest "$STORE/previous.json")
frozen_history=$(sudo ls "$STORE/history" 2>/dev/null | wc -l | tr -d ' ')

cat > "$OUT/FROZEN_CANDIDATE.json" <<EOF
{
  "schema_version": "memory_atlas.frozen_candidate.v1",
  "frozen_at": "$(now)",
  "release_id": "$frozen_release",
  "agent_release_id": "$frozen_agent",
  "snapshot_identity": $frozen_identity,
  "store_digests": {
    "current_sha256": "$frozen_current",
    "previous_sha256": "$frozen_previous",
    "history_object_count": $frozen_history
  }
}
EOF

step() { printf '{"step":"%s","at":"%s","health":%s,"identity":%s,"current_sha256":"%s"}' \
  "$1" "$(now)" "$(health)" "$(identity)" "$(digest "$STORE/current.json")"; }

steps=()
steps+=("$(step baseline)")

# 1. Restart the API and the web container. Neither owns the snapshot; both must
#    come back reading the same one.
# Clearing the failed state first: the API shares a start-rate limit with the
# self-heal timer, and a drill that trips it would leave the service down.
sudo systemctl reset-failed memory-atlas-api.service 2>/dev/null || true
sudo systemctl restart memory-atlas-api.service
sudo docker restart memory-atlas-web >/dev/null
for _ in $(seq 1 30); do curl -sf -o /dev/null --max-time 3 "$API/healthz" && break; sleep 1; done
steps+=("$(step restart_api_and_container)")

# 2. Blue-green rollback to the previous release, then roll forward again. The
#    served snapshot must survive both moves unchanged.
# A failing rollback is a finding, not a reason for the drill to vanish.
rollback_rc=0
rollback_script="$AGENT_ROOT/current/ops/memory-atlas/rollback.sh"
rollback_output=$("$rollback_script" 2>&1 | tail -1) || rollback_rc=$?
steps+=("$(step rollback_to_previous)")
rolled_back_release=$(basename "$(readlink -f "$APP_ROOT/current")")

# After the rollback, `current` points at the older release, whose copy of this
# script is whatever shipped with it. Rolling forward is an operation on the
# candidate, so it runs the candidate's script — otherwise the drill measures
# the release it is leaving rather than the one it is certifying.
forward_rc=0
forward_script="$AGENT_ROOT/releases/$frozen_agent/ops/memory-atlas/rollback.sh"
[[ -x "$forward_script" ]] || forward_script="$AGENT_ROOT/current/ops/memory-atlas/rollback.sh"
forward_output=$("$forward_script" 2>&1 | tail -1) || forward_rc=$?
steps+=("$(step roll_forward_to_candidate)")
rolled_forward_release=$(basename "$(readlink -f "$APP_ROOT/current")")

# 3. Restore the snapshot store into an isolated directory and validate it there,
#    touching nothing in place.
restore_dir=$(mktemp -d "${TMPDIR:-/tmp}/memory-atlas-restore.XXXXXXXX")
sudo cp -a "$STORE/." "$restore_dir/"
sudo chmod -R u+rwX "$restore_dir"
restore=$(python3 - "$restore_dir" "$AGENT_ROOT/current/OpenAIDatabase/schema/memory_atlas.live_snapshot.v1.schema.json" <<'PY'
import hashlib, json, sys
from pathlib import Path
root, schema_path = Path(sys.argv[1]), Path(sys.argv[2])
out = {"state": "FAIL", "reason": None, "validated": []}
try:
    import jsonschema
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker())
    for name in ("current.json", "previous.json"):
        target = root / name
        if not target.is_file():
            continue
        value = json.loads(target.read_text(encoding="utf-8"))
        validator.validate(value)
        out["validated"].append({
            "file": name,
            "sha256": hashlib.sha256(target.read_bytes()).hexdigest(),
            "run_id": value["run"]["run_id"],
            "release_id": value["release"].get("release_id"),
        })
    history = sorted((root / "history").glob("*.json")) if (root / "history").is_dir() else []
    for target in history:
        validator.validate(json.loads(target.read_text(encoding="utf-8")))
    out["history_validated"] = len(history)
    out["state"] = "PASS" if out["validated"] else "FAIL"
    if not out["validated"]:
        out["reason"] = "no current or previous snapshot in the restored tree"
except Exception as exc:
    out["reason"] = f"{type(exc).__name__}: {exc}"[:300]
print(json.dumps(out, ensure_ascii=False))
PY
)
rm -rf "$restore_dir"
steps+=("$(step isolated_restore)")

joined=$(IFS=,; echo "${steps[*]}")
cat > "$OUT/DURABILITY_RECOVERY_REPORT.json" <<EOF
{
  "schema_version": "memory_atlas.durability_recovery.v1",
  "executed_at": "$(now)",
  "host": "$(hostname)",
  "frozen_release_id": "$frozen_release",
  "rolled_back_to": "$rolled_back_release",
  "rolled_forward_to": "$rolled_forward_release",
  "rollback_exit_code": $rollback_rc,
  "rollback_script": "$rollback_script",
  "roll_forward_exit_code": $forward_rc,
  "roll_forward_script": "$forward_script",
  "rollback_output": $(printf '%s' "$rollback_output" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'),
  "roll_forward_output": $(printf '%s' "$forward_output" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().strip()))'),
  "isolated_restore": $restore,
  "steps": [$joined]
}
EOF
echo "DURABILITY_DRILL_WROTE $OUT/DURABILITY_RECOVERY_REPORT.json"
