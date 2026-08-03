#!/usr/bin/env python3
"""Run the Memory Atlas Mac source capture at most once per local calendar day.

The crontab wakes this due-check every 30 minutes so a sleeping/offline Mac catches
up after it wakes. A successful capture suppresses further runs for the same local
date. Failed runs remain retryable on the next wake-up. No launchd or agent session
is required.
"""
from __future__ import annotations

import argparse
import fcntl
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def current_time(override: str | None) -> datetime:
    parsed = parse_datetime(override)
    return parsed if parsed is not None else datetime.now().astimezone()


def write_json_atomic(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".partial")
    temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def successful_local_date(state: dict[str, Any], local_tz) -> str | None:
    explicit = state.get("last_success_local_date")
    if isinstance(explicit, str) and explicit:
        return explicit
    legacy = parse_datetime(state.get("last_success_at") if isinstance(state.get("last_success_at"), str) else None)
    return legacy.astimezone(local_tz).date().isoformat() if legacy else None


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Memory Atlas source capture once per local calendar day")
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--state-dir", type=Path, default=Path.home() / ".memory-atlas" / "source-runner")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--now", help="ISO-8601 clock override for deterministic acceptance tests")
    parser.add_argument("--entry", type=Path, help="Explicit capture entry for isolated acceptance tests")
    args = parser.parse_args()

    repo = args.repo.expanduser().resolve()
    entry = (args.entry.expanduser().resolve() if args.entry else repo / "OpenAIDatabase/scripts/memory_atlas_source_capture_entry.py")
    if not entry.is_file():
        raise SystemExit("Memory Atlas source capture entry 不存在")

    state_dir = args.state_dir.expanduser().resolve()
    state_dir.mkdir(parents=True, exist_ok=True)
    lock_path = state_dir / "run.lock"
    state_path = state_dir / "state.json"
    receipt_dir = state_dir / "receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)

    with lock_path.open("w") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            print(json.dumps({"state": "SKIPPED_LOCKED"}, ensure_ascii=False))
            return

        state: dict[str, Any] = {}
        if state_path.is_file():
            try:
                loaded = json.loads(state_path.read_text(encoding="utf-8"))
                if isinstance(loaded, dict):
                    state = loaded
            except (OSError, json.JSONDecodeError):
                state = {}

        current_local = current_time(args.now).astimezone()
        current_utc = current_local.astimezone(timezone.utc)
        today = current_local.date().isoformat()
        last_date = successful_local_date(state, current_local.tzinfo)
        if not args.force and last_date == today:
            print(json.dumps({
                "state": "SKIPPED_ALREADY_SUCCEEDED_TODAY",
                "local_date": today,
                "last_success_at": state.get("last_success_at"),
            }, ensure_ascii=False))
            return

        run_id = current_utc.strftime("source-%Y%m%dT%H%M%S%fZ")
        completed = subprocess.run(
            [sys.executable, "-B", str(entry)],
            cwd=repo,
            text=True,
            capture_output=True,
            env=os.environ.copy(),
        )
        finished_local = current_time(args.now).astimezone()
        receipt = {
            "schema_version": "memory_atlas.source_runner_receipt.v2",
            "run_id": run_id,
            "local_date": today,
            "started_at": current_local.isoformat(),
            "finished_at": finished_local.isoformat(),
            "exit_code": completed.returncode,
            "state": "SUCCESS" if completed.returncode == 0 else "FAILED",
            "stdout_tail": completed.stdout[-12000:],
            "stderr_tail": completed.stderr[-12000:],
        }
        receipt_path = receipt_dir / f"{run_id}.json"
        write_json_atomic(receipt_path, receipt)
        if completed.returncode == 0:
            new_state = {
                "schema_version": "memory_atlas.source_runner_state.v2",
                "last_success_at": receipt["finished_at"],
                "last_success_local_date": today,
                "last_run_id": run_id,
                "last_receipt": str(receipt_path),
            }
            write_json_atomic(state_path, new_state)
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
        raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
