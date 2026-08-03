"""Regression assets for the generic Memory Atlas source runner (AC-013).

Codex automation is disabled and macOS launchd is forbidden, so the daily source
capture is bound through a bounded user crontab that wakes `run_due.py` every 30
minutes. These tests pin the three properties that binding depends on:

1. at most one *successful* capture per local calendar day;
2. a failed run stays retryable on the next wake-up of the same day;
3. an explicit `--force` rerun is still possible for owner or acceptance work.

The clock is injected with `--now`, so the suite is deterministic and never
depends on the wall clock of the machine running it. `TZ` is pinned per run as
well: "local calendar day" is resolved against the *runner's* timezone, so a
suite that only passes on a UTC CI box would give a false green on a developer
Mac in, for example, AEST. `test_local_calendar_day_is_local_not_utc` locks that
distinction in place.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
RUNNER = REPO_ROOT / "ops/memory-atlas/source-runner/run_due.py"


def execute(repo: Path, state: Path, entry: Path, when: str, *, force: bool = False, check: bool = True, tz: str = "UTC"):
    argv = [
        sys.executable,
        "-B",
        str(RUNNER),
        "--repo",
        str(repo),
        "--state-dir",
        str(state),
        "--entry",
        str(entry),
        "--now",
        when,
    ]
    if force:
        argv.append("--force")
    env = {**os.environ, "TZ": tz, "PYTHONDONTWRITEBYTECODE": "1"}
    completed = subprocess.run(argv, text=True, capture_output=True, env=env)
    if check and completed.returncode:
        raise AssertionError(f"stdout={completed.stdout}\nstderr={completed.stderr}")
    return completed


def make_entry(repo: Path, *, fail_first: bool = False) -> tuple[Path, Path]:
    counter = repo / "counter.txt"
    entry = repo / "capture.py"
    entry.write_text(
        """from pathlib import Path
counter=Path(__file__).with_name('counter.txt')
count=int(counter.read_text() if counter.exists() else '0')+1
counter.write_text(str(count))
FAIL_FIRST=__FAIL_FIRST__
raise SystemExit(9 if FAIL_FIRST and count == 1 else 0)
""".replace("__FAIL_FIRST__", "True" if fail_first else "False"),
        encoding="utf-8",
    )
    return entry, counter


def test_runner_exists_and_is_executable() -> None:
    assert RUNNER.is_file(), "generic one-shot source runner is missing; capture would be SOURCE_RUNNER_UNBOUND"


def test_success_runs_at_most_once_per_local_calendar_day(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    entry, counter = make_entry(repo)
    first = execute(repo, state, entry, "2026-08-03T01:00:00+00:00")
    assert json.loads(first.stdout)["state"] == "SUCCESS"
    second = execute(repo, state, entry, "2026-08-03T22:00:00+00:00")
    assert json.loads(second.stdout)["state"] == "SKIPPED_ALREADY_SUCCEEDED_TODAY"
    assert counter.read_text() == "1"
    third = execute(repo, state, entry, "2026-08-04T00:01:00+00:00")
    assert json.loads(third.stdout)["state"] == "SUCCESS"
    assert counter.read_text() == "2"


def test_failed_run_remains_retryable_same_day_then_success_suppresses_more_runs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    entry, counter = make_entry(repo, fail_first=True)
    failed = execute(repo, state, entry, "2026-08-03T01:00:00+00:00", check=False)
    assert failed.returncode == 9
    assert json.loads(failed.stdout)["state"] == "FAILED"
    success = execute(repo, state, entry, "2026-08-03T01:30:00+00:00")
    assert json.loads(success.stdout)["state"] == "SUCCESS"
    skipped = execute(repo, state, entry, "2026-08-03T02:00:00+00:00")
    assert json.loads(skipped.stdout)["state"] == "SKIPPED_ALREADY_SUCCEEDED_TODAY"
    assert counter.read_text() == "2"


def test_force_allows_explicit_owner_or_acceptance_rerun(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    entry, counter = make_entry(repo)
    execute(repo, state, entry, "2026-08-03T01:00:00+00:00")
    forced = execute(repo, state, entry, "2026-08-03T01:05:00+00:00", force=True)
    assert json.loads(forced.stdout)["state"] == "SUCCESS"
    assert counter.read_text() == "2"


def test_receipt_records_every_run_including_failures(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    repo.mkdir()
    state = tmp_path / "state"
    entry, _ = make_entry(repo, fail_first=True)
    execute(repo, state, entry, "2026-08-03T01:00:00+00:00", check=False)
    execute(repo, state, entry, "2026-08-03T01:30:00+00:00")
    receipts = sorted((state / "receipts").glob("*.json"))
    assert len(receipts) == 2
    states = [json.loads(path.read_text(encoding="utf-8"))["state"] for path in receipts]
    assert states == ["FAILED", "SUCCESS"]
    # A failure must never be recorded as the day's success.
    persisted = json.loads((state / "state.json").read_text(encoding="utf-8"))
    assert persisted["last_success_local_date"] == "2026-08-03"
    assert persisted["last_run_id"] == json.loads(receipts[1].read_text(encoding="utf-8"))["run_id"]


def test_local_calendar_day_is_local_not_utc(tmp_path: Path) -> None:
    """22:00 UTC is already the next day in Australia/Sydney, and the runner must
    follow the local calendar, not UTC. This is the exact case that made the
    upstream taskpack suite pass on a UTC CI runner and fail on the target Mac."""
    repo = tmp_path / "repo"
    repo.mkdir()
    utc_state = tmp_path / "state-utc"
    entry, counter = make_entry(repo)
    assert json.loads(execute(repo, utc_state, entry, "2026-08-03T01:00:00+00:00", tz="UTC").stdout)["state"] == "SUCCESS"
    assert json.loads(execute(repo, utc_state, entry, "2026-08-03T22:00:00+00:00", tz="UTC").stdout)["state"] == "SKIPPED_ALREADY_SUCCEEDED_TODAY"
    assert counter.read_text() == "1"

    sydney_state = tmp_path / "state-sydney"
    assert json.loads(execute(repo, sydney_state, entry, "2026-08-03T01:00:00+00:00", tz="Australia/Sydney").stdout)["state"] == "SUCCESS"
    # 2026-08-03T22:00Z is 2026-08-04 08:00 local, so it is a new local day.
    assert json.loads(execute(repo, sydney_state, entry, "2026-08-03T22:00:00+00:00", tz="Australia/Sydney").stdout)["state"] == "SUCCESS"
    assert counter.read_text() == "3"


def test_crontab_manager_reports_unbound_instead_of_guessing() -> None:
    manager = REPO_ROOT / "ops/memory-atlas/source-runner/manage_crontab.py"
    assert manager.is_file()
    text = manager.read_text(encoding="utf-8")
    assert "SOURCE_RUNNER_UNBOUND" in text, "missing binding must be reported, never assumed bound"
    assert "launchctl" not in text and "LaunchAgents" not in text, "launchd is forbidden on this machine"
    assert "*/30 * * * *" in text, "the 30-minute catch-up wake-up is the bounded schedule"
    assert "crontab-before-" in text, "the pre-install crontab backup is part of the binding evidence"
