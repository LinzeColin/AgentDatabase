#!/usr/bin/env python3
"""Read MiniMax Design's own gateway log to tell whether it is still generating.

Watching the GUI with screenshots answers "is a spinner drawn", which is not the
same question as "is work happening" — the app draws a thinking state while it
reads files, and draws nothing while an image is in flight on the server. The
desktop app proxies every call through a local gateway at 127.0.0.1:8001 and
logs both sides to `~/Library/Logs/MiniMax Design/main-<MM-DD>.log`, so the
honest signals are already on disk:

    POST /api/generate/image/submit      one image handed to the server
    GET  /api/generate/tasks/<id>/query  that image still being polled
    POST /api/heartbeat                  the app itself is alive

Two thresholds, not one. `quiet` means no image traffic for a while — normal,
because the agent spends real minutes reading the pack and planning between
bursts (observed gaps: 36 and 69 minutes on 2026-08-19). `stalled` means quiet
for long enough that a nudge is warranted, and even then the caller should
confirm against the GUI before typing into it: interrupting a thinking agent
costs more than a late nudge.

Usage:
    python3 watch_mmx.py            # human report
    python3 watch_mmx.py --json     # {"verdict": …} for a watchdog loop
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path

LOGS = Path.home() / "Library/Logs/MiniMax Design"
STAMP = re.compile(r"^\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\.\d+\]")
SUBMIT = "POST /api/generate/image/submit"
POLL = re.compile(r"-> GET /api/generate/tasks/([A-Za-z0-9_-]+)/query")
HEARTBEAT = "POST /api/heartbeat"
# The agent reads the pack and plans between image bursts; that work shows up as
# session traffic, not generate traffic. Without this signal a watchdog reads a
# planning agent as a dead one and interrupts it — the 36- and 69-minute gaps on
# 2026-08-19 were both planning, not failure.
SESSION = re.compile(r"-> (?:GET|POST) /api/(?:internal/sessions|files|canvas|assets)")

QUIET_SECS = 600      # no image traffic this long → quiet
# 10 minutes of TOTAL silence. Measured on the night of 2026-08-19: while the
# agent was working, thinking-channel silence never exceeded 254s, and an image
# actually in flight keeps the image channel refreshed by its own polling — so
# neither a thinking agent nor a slow render can reach this. What does reach it
# is the real failure mode: the agent ends its turn ("下一步我会…") and waits for
# a human. At the old 25-minute threshold each of those cost 25-40 minutes of
# dead night.
STALL_SECS = 600
DEAD_SECS = 300       # no heartbeat this long → the app is gone


def newest_logs(count: int = 2) -> list[Path]:
    """The two newest logs, oldest first.

    The log rotates at local midnight into an empty file. Reading only the
    newest one meant that at 00:00:57 every timestamp was absent, absence read
    as "quiet forever", and the watchdog declared a healthy app stalled sixty
    seconds into the new day. Carrying yesterday's tail fixes that without
    special-casing the hour.
    """
    candidates = sorted(LOGS.glob("main-*.log"), key=lambda p: p.stat().st_mtime)
    return candidates[-count:]


def scan(paths: list[Path]) -> dict:
    """One pass. Only the leading bracket timestamp is parsed — the embedded
    JSON carries a UTC `timestamp` field, and mixing the two zones is how a
    watchdog convinces itself a live app has been dead for ten hours."""
    last: dict[str, float] = {}
    submits: list[float] = []
    tasks: set[str] = set()
    errors: list[str] = []
    lines = (line for path in paths
             for line in path.open(encoding="utf-8", errors="replace"))
    if True:
        for line in lines:
            stamp = STAMP.match(line)
            if not stamp:
                continue
            when = datetime.strptime(stamp.group(1), "%Y-%m-%d %H:%M:%S").timestamp()
            if SUBMIT in line:
                last["submit"] = when
                if "-> POST" in line:
                    submits.append(when)
            elif HEARTBEAT in line:
                last["heartbeat"] = when
            else:
                found = POLL.search(line)
                if found:
                    last["poll"] = when
                    tasks.add(found.group(1))
            if SESSION.search(line):
                last["session"] = when
            if '"level":"error"' in line or re.search(r'"status":[45]\d\d', line):
                errors.append(line.rstrip()[:200])
    return {"last": last, "submits": submits, "tasks": sorted(tasks), "errors": errors}


def rate(submits: list[float], window: float) -> int:
    now = time.time()
    return sum(1 for t in submits if now - t <= window)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--shell", action="store_true",
                        help="KEY=VALUE 行，供 shell eval —— 比在 shell 里嵌套引号解 JSON 稳")
    parser.add_argument("--quiet-secs", type=int, default=QUIET_SECS)
    parser.add_argument("--stall-secs", type=int, default=STALL_SECS)
    args = parser.parse_args()

    paths = newest_logs()
    if not paths:
        report = {"verdict": "no-log", "note": "找不到 MiniMax Design 日志"}
        print(json.dumps(report, ensure_ascii=False) if args.json else report["note"])
        return

    data = scan(paths)
    now = time.time()
    last = data["last"]
    age = lambda key: round(now - last[key], 1) if key in last else None
    image_age = min([a for a in (age("submit"), age("poll")) if a is not None], default=None)

    if age("heartbeat") is None or age("heartbeat") > DEAD_SECS:
        verdict = "dead"
    elif (image_age is not None and image_age > args.stall_secs
          and (age("session") is None or age("session") > args.stall_secs)):
        # Stalled means BOTH channels quiet: no image in flight and no thinking.
        # `image_age is None` deliberately does NOT qualify — a missing
        # timestamp means "nothing seen in the window read", which is what a
        # freshly rotated log looks like, not what a stalled app looks like.
        verdict = "stalled"
    elif image_age > args.quiet_secs:
        verdict = "quiet"
    else:
        verdict = "working"

    report = {
        "verdict": verdict,
        "log": paths[-1].name,
        "image_idle_secs": image_age,
        "heartbeat_age_secs": age("heartbeat"),
        "session_idle_secs": age("session"),
        "submits_total": len(data["submits"]),
        "submits_1h": rate(data["submits"], 3600),
        "submits_15m": rate(data["submits"], 900),
        "distinct_tasks": len(data["tasks"]),
        "errors": len(data["errors"]),
        "last_error": data["errors"][-1] if data["errors"] else None,
    }
    if args.shell:
        for key in ("verdict", "submits_total", "image_idle_secs",
                    "session_idle_secs", "heartbeat_age_secs", "errors"):
            value = report[key]
            print(f"{key.upper()}={-1 if value is None else value}")
        return
    if args.json:
        print(json.dumps(report, ensure_ascii=False))
        return
    print(f"判定   {verdict}")
    print(f"日志   {', '.join(p.name for p in paths)}")
    print(f"出图静默 {image_age} 秒 · 思考静默 {age('session')} 秒 · 心跳 {age('heartbeat')} 秒前")
    print(f"今日提交 {report['submits_total']} 次 · 近 1h {report['submits_1h']} · "
          f"近 15m {report['submits_15m']} · 不同任务 {report['distinct_tasks']}")
    if data["errors"]:
        print(f"错误 {len(data['errors'])} 条，最后一条：{data['errors'][-1][:160]}")


if __name__ == "__main__":
    main()
