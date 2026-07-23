#!/usr/bin/env bash
# Compatibility wrapper for the video-replica evidence engine.
set -euo pipefail

MODE="${1:?mode: doctor|all|exhaustive|key|burst}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
CORE="$SCRIPT_DIR/video_evidence.py"

case "$MODE" in
  doctor)
    exec "$PYTHON_BIN" "$CORE" doctor
    ;;
  all)
    VIDEO="${2:?video}"
    OUT="${3:?outdir}"
    exec "$PYTHON_BIN" "$CORE" extract "$VIDEO" "$OUT" --mode balanced
    ;;
  exhaustive)
    VIDEO="${2:?video}"
    OUT="${3:?outdir}"
    exec "$PYTHON_BIN" "$CORE" extract "$VIDEO" "$OUT" --mode exhaustive
    ;;
  key)
    VIDEO="${2:?video}"
    OUT="${3:?outdir}"
    TIMESTAMP="${4:?timestamp}"
    exec "$PYTHON_BIN" "$CORE" frame "$VIDEO" "$OUT" "$TIMESTAMP"
    ;;
  burst)
    VIDEO="${2:?video}"
    OUT="${3:?outdir}"
    START="${4:?timestamp}"
    END="$($PYTHON_BIN - "$START" "${BURST_DURATION:-0.5}" <<'PY'
import sys
print(float(sys.argv[1]) + float(sys.argv[2]))
PY
)"
    exec "$PYTHON_BIN" "$CORE" window "$VIDEO" "$OUT" "$START" "$END" --label "burst_${START}"
    ;;
  *)
    printf 'unknown mode: %s\n' "$MODE" >&2
    exit 2
    ;;
esac
