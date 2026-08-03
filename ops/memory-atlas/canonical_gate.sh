#!/usr/bin/env bash
# v0.0.0.32 T07 — the single canonical gate.
#
#   canonical_gate.sh <repo> [quick|full] [output.json]
#
# One gate, two modes, one definition of "green". `quick` is what a git hook may
# call: it is fast and it is NOT authoritative. `full` is what CI and deployment
# call, and it is the only thing allowed to certify a release.
#
# Every check below already existed in this repository before v0.0.0.32. The
# taskpack's own scripts/canonical_gate.sh assumed the taskpack directory would
# be present at run time; it is not part of the repository, so the equivalent
# repo-resident gates are invoked instead — same guarantees, no phantom path.
set -euo pipefail
umask 077

repo=$(cd -- "${1:?repo path required}" && pwd)
mode=${2:-full}
output=${3:-}
case "$mode" in quick|full) ;; *) echo "mode must be quick or full" >&2; exit 64 ;; esac

started_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
results=()
failed=0

run_check() {
  local name=$1; shift
  local log
  log=$(mktemp "${TMPDIR:-/tmp}/memory-atlas-gate.XXXXXX")
  if "$@" >"$log" 2>&1; then
    results+=("{\"check\":\"$name\",\"pass\":true}")
  else
    results+=("{\"check\":\"$name\",\"pass\":false,\"tail\":$(tail -c 600 "$log" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read()))')}")
    failed=$((failed + 1))
  fi
  rm -f "$log"
}

# --- checks every mode runs -------------------------------------------------
run_check python_syntax python3 -B -m compileall -q \
  "$repo/OpenAIDatabase/scripts/memory_atlas_private" \
  "$repo/OpenAIDatabase/scripts/memory_atlas_acceptance" \
  "$repo/ops/memory-atlas"

run_check acceptance_oracles env PYTHONPATH="$repo" python3 -B -m unittest discover \
  -s "$repo/OpenAIDatabase/scripts/memory_atlas_acceptance" \
  -t "$repo/OpenAIDatabase/scripts/memory_atlas_acceptance"

run_check privacy_and_dependency python3 -B \
  "$repo/OpenAIDatabase/scripts/memory_atlas_acceptance/privacy_and_dependency_scan.py" \
  --snapshot "$repo/OpenAIDatabase/fixtures/live_snapshot.synthetic.json" \
  --snapshot "$repo/OpenAIDatabase/fixtures/private_analytics.synthetic.json" \
  --snapshot "$repo/OpenAIDatabase/fixtures/visual_analytics.synthetic.json" \
  --output "${TMPDIR:-/tmp}/memory-atlas-privacy-scan.json"

if [[ -d "$repo/MemoryAtlas/node_modules" ]]; then
  run_check frontend_typecheck npm --prefix "$repo/MemoryAtlas" run --silent lint
  run_check preservation_static npm --prefix "$repo/MemoryAtlas" run --silent validate:preservation
  run_check v31_typescript npm --prefix "$repo/MemoryAtlas" run --silent validate:v31:typescript
else
  results+=('{"check":"frontend_typecheck","pass":false,"tail":"MemoryAtlas/node_modules missing; run npm ci"}')
  failed=$((failed + 1))
fi

# --- full mode only ---------------------------------------------------------
if [[ "$mode" == "full" ]]; then
  run_check backend_suite env PYTHONPATH="$repo" python3 -B -m pytest -q \
    "$repo/OpenAIDatabase/tests/test_memory_atlas_private_v31.py" \
    "$repo/OpenAIDatabase/tests/test_memory_atlas_source_runner_v31.py" \
    "$repo/OpenAIDatabase/tests/test_memory_atlas_live_snapshot_api_v32.py" \
    "$repo/OpenAIDatabase/tests/test_memory_atlas_live_snapshot_publish_v32.py" \
    "$repo/OpenAIDatabase/tests/test_verification_policy.py" \
    "$repo/OpenAIDatabase/tests/test_directory_lifecycle.py"
  if [[ -d "$repo/MemoryAtlas/node_modules" ]]; then
    run_check frontend_build npm --prefix "$repo/MemoryAtlas" run --silent build
    run_check v31_static npm --prefix "$repo/MemoryAtlas" run --silent validate:v31
    run_check v31_incremental npm --prefix "$repo/MemoryAtlas" run --silent validate:v31:incremental
  fi
  run_check ci_workflow_present test -f "$repo/.github/workflows/memory-atlas-v31.yml"
fi

verdict=$([[ $failed -eq 0 ]] && echo PASS || echo FAIL)
report=$(printf '{"schema_version":"memory_atlas.canonical_gate.v1","mode":"%s","verdict":"%s","authoritative":%s,"started_at":"%s","finished_at":"%s","failed_count":%d,"checks":[%s]}' \
  "$mode" "$verdict" "$([[ "$mode" == "full" ]] && echo true || echo false)" \
  "$started_at" "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "$failed" \
  "$(IFS=,; echo "${results[*]}")")

if [[ -n "$output" ]]; then
  mkdir -p "$(dirname "$output")"
  printf '%s\n' "$report" >"$output"
fi
printf '%s\n' "$report"
printf 'MEMORY_ATLAS_CANONICAL_GATE_%s mode=%s failed=%d\n' "$verdict" "$mode" "$failed" >&2
[[ $failed -eq 0 ]]
