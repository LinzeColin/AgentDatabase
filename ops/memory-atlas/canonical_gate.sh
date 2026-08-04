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

# The gate now runs the suite that tests the gate, so a nested invocation would
# fork forever. A nested call reports itself and exits 0: the outer run is the
# one whose verdict counts.
if [[ "${MEMORY_ATLAS_GATE_RUNNING:-0}" == "1" ]]; then
  printf '{"schema_version":"memory_atlas.canonical_gate.v1","mode":"%s","verdict":"NESTED_SKIPPED","authoritative":false,"checks":[]}\n' "$mode"
  exit 0
fi
export MEMORY_ATLAS_GATE_RUNNING=1

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
  # Listing the files by hand drifted: two v0.0.0.32 suites existed for hours
  # without this gate ever running them, so the gate reported green while they
  # were red. The list comes from the ownership contract now.
  # `mapfile` is bash 4+; the Owner's machine ships bash 3.2, where it is a
  # command-not-found that set -e turns into a silent truncated run.
  owned=()
  while IFS= read -r line; do owned+=("$line"); done < <(python3 -c "
import json, sys
from pathlib import Path
policy = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
# This is the Memory Atlas gate, so it owns the Memory Atlas tests in the
# integration tier. Taking the list from the contract rather than by hand means
# a new suite is picked up automatically; running the whole tier would only
# duplicate CI and take ten minutes.
# Two suites assert against a live deployment and can only pass on CI. They are
# named here with the reason rather than silently dropped, and a test requires
# this list to stay exactly these two and CI to keep running them.
CI_ONLY = {
    'tests/test_memory_atlas_acceptance_audit.py',   # needs live Cloudflare evidence
    'tests/test_memory_atlas_goal_completion.py',    # needs live Cloudflare evidence
}
for name in sorted(policy['execution_tiers']['integration']['test_files']):
    if 'memory_atlas' not in name or name in CI_ONLY:
        continue
    path = Path(sys.argv[2]) / 'OpenAIDatabase' / name
    if path.is_file():
        print(path)
" "$repo/OpenAIDatabase/config/quality/verification_policy.json" "$repo")
  run_check backend_suite env PYTHONPATH="$repo" python3 -B -m pytest -q \
    "${owned[@]}" \
    "$repo/OpenAIDatabase/tests/test_verification_policy.py" \
    "$repo/OpenAIDatabase/tests/test_directory_lifecycle.py"
  if [[ -d "$repo/MemoryAtlas/node_modules" ]]; then
    run_check frontend_build npm --prefix "$repo/MemoryAtlas" run --silent build
    run_check v31_static npm --prefix "$repo/MemoryAtlas" run --silent validate:v31
    run_check v31_incremental npm --prefix "$repo/MemoryAtlas" run --silent validate:v31:incremental
    # validate:whole-project belongs here in principle — a privacy-scan failure
    # inside it reached main while this gate reported green. It is not run
    # locally because four of its tests (acceptance_audit, goal_completion)
    # require live deployment evidence and can only pass on CI, which would make
    # the local gate permanently red and therefore useless. The gap is closed by
    # asserting CI runs it (test_the_full_gate_covers_what_ci_runs), not by
    # pretending it is covered here.
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
