#!/bin/bash
# Keep stepping the batch run until every unit is settled.
#
# Same shape as the GUI night watch and for the same reason: the polling is
# free, so it lives in shell, and the model is woken only when the script
# EXITS — which now means the run is finished or wedged, not that a batch is
# still baking. Batch turnaround is up to 24h per round, so a slow poll is
# plenty; anything faster just burns API calls to learn "still in_progress".
#
# Exit codes: 0 all settled · 3 no progress for too long · 4 step errored

TOOLS="$(cd "$(dirname "$0")" && pwd)"
STATE="$1"; shift
POLL=${POLL:-600}
LOG="$(dirname "$STATE")/batch-watch.log"
STALL_ROUNDS=${STALL_ROUNDS:-36}      # 36 × 10min = 6h with no change

say() { printf '%s  %s\n' "$(date '+%m-%d %H:%M:%S')" "$1" >> "$LOG"; }

done_count() {
  python3 -c "
import json,sys
s=json.load(open('$STATE'))
print(sum(1 for u in s['units'].values() if u['status']=='accepted'))"
}
open_count() {
  python3 -c "
import json,sys
s=json.load(open('$STATE'))
print(sum(1 for u in s['units'].values() if u['status'] in ('pending','retry','in_batch')))"
}

say "批次守护启动 · 每 ${POLL}s 一步"
LAST=-1; QUIET=0
while true; do
  if ! OUT=$(python3 "$TOOLS/batch_run.py" step --state "$STATE" 2>&1); then
    say "！step 失败：$(printf '%s' "$OUT" | tail -3 | tr '\n' ' ')"
    exit 4
  fi
  DONE=$(done_count); OPEN=$(open_count)
  # Per-request progress inside still-running batches, so the log shows movement
  # instead of a flat "0" for the hours before the first batch completes.
  INFLIGHT=$(python3 - "$STATE" <<'PYEOF'
import json, sys, urllib.request
state = json.load(open(sys.argv[1]))
token = open(state["key_file"]).read().strip()
done = total = 0
for b in state["batches"]:
    if b.get("harvested"): continue
    try:
        req = urllib.request.Request(f"https://api.openai.com/v1/batches/{b['id']}",
                                     headers={"Authorization": f"Bearer {token}"})
        with urllib.request.urlopen(req, timeout=60) as r:
            c = json.load(r).get("request_counts", {})
        done += c.get("completed", 0); total += c.get("total", 0)
    except Exception:
        pass
print(f"{done}/{total}")
PYEOF
)
  say "已落盘通过 ${DONE} · 批次内已出图 ${INFLIGHT} · 未结算 ${OPEN} · $(printf '%s' "$OUT" | tail -1)"
  if [ "$DONE" != "$LAST" ]; then LAST=$DONE; QUIET=0; else QUIET=$((QUIET+1)); fi
  if [ "$OPEN" -eq 0 ]; then
    say "全部结算完成 · 通过 ${DONE}"
    exit 0
  fi
  if [ "$QUIET" -ge "$STALL_ROUNDS" ]; then
    say "！${STALL_ROUNDS} 轮无进展（约 $((STALL_ROUNDS*POLL/3600)) 小时），叫醒 Claude"
    exit 3
  fi
  sleep "$POLL"
done
