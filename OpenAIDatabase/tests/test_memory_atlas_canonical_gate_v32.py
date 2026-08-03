"""v0.0.0.32 T07 — one canonical gate, and the hook is never the authority.

The thing worth pinning is the *shape* of the code flow, not that a shell script
exits zero: a hook that could certify a release would be a second source of truth
on a machine nobody audits, and a parallel timer would be a second schedule
nobody reconciles.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
GATE = REPO / "ops" / "memory-atlas" / "canonical_gate.sh"
HOOK = REPO / ".githooks" / "pre-push"
WORKFLOW = REPO / ".github" / "workflows" / "memory-atlas-v31.yml"
LIVE_PROBE = REPO / "ops" / "memory-atlas" / "post-promote-live-probe.sh"
POST_PROMOTE = REPO / "ops" / "memory-atlas" / "post-promote-probe.sh"


def test_there_is_exactly_one_canonical_gate_script() -> None:
    found = sorted(p.relative_to(REPO).as_posix() for p in REPO.glob("**/canonical_gate.sh") if ".git/" not in str(p))
    assert found == ["ops/memory-atlas/canonical_gate.sh"], found


def test_the_hook_calls_only_the_quick_gate() -> None:
    text = HOOK.read_text(encoding="utf-8")
    invocations = [
        line.strip()
        for line in text.splitlines()
        if "canonical_gate.sh" in line and not line.lstrip().startswith("#")
    ]
    assert invocations, text
    for line in invocations:
        assert " quick" in line, line
        assert " full" not in line, "the hook must never invoke the authoritative gate"
    assert HOOK.stat().st_mode & 0o111, "hook must be executable"


def test_the_hook_is_skippable_and_reversible() -> None:
    text = HOOK.read_text(encoding="utf-8")
    assert "MEMORY_ATLAS_SKIP_GATE" in text
    assert "git config --unset core.hooksPath" in text


def test_quick_mode_declares_itself_non_authoritative(tmp_path: Path) -> None:
    output = tmp_path / "quick.json"
    subprocess.run([str(GATE), str(REPO), "quick", str(output)], check=True, capture_output=True)
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["mode"] == "quick"
    assert report["authoritative"] is False


def test_full_mode_is_the_authority_and_is_a_strict_superset(tmp_path: Path) -> None:
    quick = tmp_path / "quick.json"
    full = tmp_path / "full.json"
    subprocess.run([str(GATE), str(REPO), "quick", str(quick)], check=True, capture_output=True)
    subprocess.run([str(GATE), str(REPO), "full", str(full)], check=True, capture_output=True)
    quick_checks = {row["check"] for row in json.loads(quick.read_text(encoding="utf-8"))["checks"]}
    full_report = json.loads(full.read_text(encoding="utf-8"))
    full_checks = {row["check"] for row in full_report["checks"]}
    assert full_report["authoritative"] is True
    assert quick_checks < full_checks, "full must run strictly more than quick"
    assert {"backend_suite", "frontend_build", "ci_workflow_present"} <= full_checks


def test_an_invalid_mode_is_refused() -> None:
    result = subprocess.run([str(GATE), str(REPO), "sorta"], capture_output=True)
    assert result.returncode == 64


def test_ci_runs_the_full_gate_not_the_quick_one() -> None:
    text = WORKFLOW.read_text(encoding="utf-8")
    assert "canonical_gate.sh" in text
    assert "canonical_gate.sh . full" in text or 'canonical_gate.sh "$PWD" full' in text
    assert "canonical_gate.sh . quick" not in text


def test_no_parallel_timer_was_added() -> None:
    # The reconcile timer already compensates for missed events; a second
    # schedule would be a second answer to "when is the data current".
    units = sorted(p.name for p in (REPO / "ops" / "memory-atlas" / "systemd").glob("*.timer"))
    assert units == [
        "memory-atlas-action-worker.timer",
        "memory-atlas-reconcile.timer",
        "memory-atlas-selfheal.timer",
    ], units


def test_reconcile_compensation_window_is_at_most_fifteen_minutes() -> None:
    timer = (REPO / "ops" / "memory-atlas" / "systemd" / "memory-atlas-reconcile.timer").read_text(encoding="utf-8")
    interval = next(
        line.split("=", 1)[1].strip()
        for line in timer.splitlines()
        if line.startswith("OnUnitActiveSec=")
    )
    assert interval.endswith("min"), interval
    assert int(interval[:-3]) <= 15, interval


def test_post_promote_calls_the_live_probe_and_fails_on_it() -> None:
    text = POST_PROMOTE.read_text(encoding="utf-8")
    assert "post-promote-live-probe.sh" in text
    assert "LIVE_SNAPSHOT_PROBE_FAIL" in text
    assert "exit 6" in text


def test_live_probe_refuses_to_pass_without_an_access_token(tmp_path: Path) -> None:
    result = subprocess.run(
        [str(LIVE_PROBE), "https://example.invalid", "REL", "DEP", str(tmp_path)],
        capture_output=True,
        env={"PATH": "/usr/bin:/bin:/usr/local/bin"},
    )
    assert result.returncode == 3
    receipt = json.loads((tmp_path / "API_RECEIPT.json").read_text(encoding="utf-8"))
    assert receipt["state"] == "NOT_RUN"


@pytest.mark.parametrize(
    "needle",
    ["no-store", "header/body mismatch", "unexpected release_id", "unexpected deployment_revision", "privacy contract"],
)
def test_live_probe_checks_every_identity_and_contract_field(needle: str) -> None:
    assert needle in LIVE_PROBE.read_text(encoding="utf-8")
