#!/bin/bash
# Night watch for the MiniMax Design GUI run.
#
# The point of this script is that it costs nothing to run. Watching the app by
# waking a language model every twenty minutes burns a full context each time
# and, on a quiet night, learns nothing. So the polling lives here in shell --
# reading the app's own gateway log, which is free -- and the model is woken
# only by this script EXITING, which happens only when something needs an action
# shell cannot take: typing into the GUI. (osascript could, but has no
# assistive-access grant on this machine, so the nudge goes back to the model.)
#
# Exit codes are the wake reason:
#   0  reached the deadline, nothing wrong
#   2  the app is gone -- no heartbeat
#   3  stalled -- both the image channel and the thinking channel went quiet
#
# Usage: nightwatch.sh [--until HH:MM] [--poll SECS]

TOOLS="$(cd "$(dirname "$0")" && pwd)"
PROBE="$TOOLS/watch_mmx.py"
LOG="$HOME/Documents/Codex/GithubProject/_scratch/nightwatch.log"
POLL=60
UNTIL="09:00"

while [ $# -gt 0 ]; do
  case "$1" in
    --until) UNTIL="$2"; shift 2 ;;
    --poll)  POLL="$2";  shift 2 ;;
    *) shift ;;
  esac
done

NOW=$(date +%s)
DEADLINE=$(date -j -f "%Y-%m-%d %H:%M" "$(date -v+1d +%Y-%m-%d) $UNTIL" +%s)
TODAY=$(date -j -f "%Y-%m-%d %H:%M" "$(date +%Y-%m-%d) $UNTIL" +%s)
[ "$TODAY" -gt "$NOW" ] && DEADLINE=$TODAY

say() { printf '%s  %s\n' "$(date '+%m-%d %H:%M:%S')" "$1" >> "$LOG"; }

eval "$(python3 "$PROBE" --shell)"
BASE=$SUBMITS_TOTAL
say "守夜启动 · 每 ${POLL}s 一探 · 截止 $(date -r "$DEADLINE" '+%m-%d %H:%M') · 起始 ${BASE} 张"

LAST_REPORT=0
while [ "$(date +%s)" -lt "$DEADLINE" ]; do
  OUT=$(python3 "$PROBE" --shell 2>/dev/null)
  if [ -z "$OUT" ]; then sleep "$POLL"; continue; fi
  eval "$OUT"

  # A line every ten minutes, so the morning report is one `cat` and not a
  # reconstruction from the app's own log.
  if [ $(( $(date +%s) - LAST_REPORT )) -ge 600 ]; then
    say "${VERDICT} · 已提交 ${SUBMITS_TOTAL} 张（本夜 +$((SUBMITS_TOTAL - BASE))） · 出图静默 ${IMAGE_IDLE_SECS}s · 思考静默 ${SESSION_IDLE_SECS}s"
    LAST_REPORT=$(date +%s)
  fi

  case "$VERDICT" in
    dead)
      say "！心跳消失 ${HEARTBEAT_AGE_SECS}s —— MiniMax Design 已退出，需要人工重开"
      exit 2 ;;
    stalled)
      say "！停摆 —— 出图静默 ${IMAGE_IDLE_SECS}s、思考静默 ${SESSION_IDLE_SECS}s，叫醒 Claude 去 GUI 推一把"
      exit 3 ;;
  esac
  sleep "$POLL"
done

say "到点收工 · 共 ${SUBMITS_TOTAL} 张（本夜 +$((SUBMITS_TOTAL - BASE))）"
exit 0
