"""v0.0.0.32 T10 — the verifier has to be able to fail us.

A verifier that only ever says PASS is decoration. Every test here plants one
defect in an otherwise healthy subject and asserts the verdict changes, plus the
cases where evidence is absent rather than wrong — those must be BLOCKED, since
the taskpack's rule is that the builder may not self-certify and absence is the
easiest way to accidentally do exactly that.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from OpenAIDatabase.scripts.memory_atlas_independent_verifier import main

REPO = Path(__file__).resolve().parents[2]
RUN = "marun_5bd5fa6104b034eaf65bdee3"
RELEASE = "20260804T111907Z-fa55d808fe90"
STEPS = ("baseline", "restart_api_and_container", "rollback_to_previous",
         "roll_forward_to_candidate", "isolated_restore")


def _snapshot() -> dict:
    return {
        "schema_version": "memory_atlas.live_snapshot.v1",
        "run": {"run_id": RUN, "trace_id": RUN, "source_completed_at": "2026-08-03T17:31:57+00:00"},
        "release": {"release_id": RELEASE, "deployment_revision": RELEASE,
                    "artifact_digest": "e9" * 32, "identity_state": "OBSERVED"},
        "analysis": {"event_count": 122080},
    }


def _identity() -> dict:
    snapshot = _snapshot()
    return {
        "readable": True, "run_id": RUN, "trace_id": RUN,
        "source_completed_at": snapshot["run"]["source_completed_at"],
        "release_id": RELEASE, "deployment_revision": RELEASE,
        "artifact_digest": snapshot["release"]["artifact_digest"], "event_count": 122080,
    }


def _subject(tmp_path: Path, **overrides) -> Path:
    """A healthy world; overrides plant exactly one defect at a time."""
    store = tmp_path / "live-snapshot"
    (store / "history").mkdir(parents=True)
    payload = json.dumps(overrides.get("snapshot", _snapshot()), ensure_ascii=False).encode("utf-8")
    (store / "current.json").write_bytes(payload)
    (store / "previous.json").write_bytes(payload)
    history_run = overrides.get("history_run", RUN)
    if overrides.get("history_present", True):
        stored = json.loads(payload)
        stored["run"]["run_id"] = history_run
        (store / "history" / f"{history_run}.json").write_text(
            json.dumps(stored, ensure_ascii=False), encoding="utf-8")

    frozen = {
        "schema_version": "memory_atlas.frozen_candidate.v1",
        "release_id": RELEASE, "agent_release_id": RELEASE,
        "snapshot_identity": overrides.get("frozen_identity", _identity()),
        "store_digests": {
            "current_sha256": overrides.get("frozen_current_digest", hashlib.sha256(payload).hexdigest()),
            "previous_sha256": hashlib.sha256(payload).hexdigest(),
            "history_object_count": 1,
        },
    }
    (tmp_path / "FROZEN_CANDIDATE.json").write_text(json.dumps(frozen, ensure_ascii=False), encoding="utf-8")

    step_identity = overrides.get("step_identity", {})
    steps = [
        {
            "step": name, "at": "2026-08-04T11:30:00Z",
            "health": overrides.get("health", {}).get(name, {"internal_api": "200", "internal_web": "200"}),
            "identity": step_identity.get(name, _identity()),
            "current_sha256": overrides.get("step_digest", {}).get(name, hashlib.sha256(payload).hexdigest()),
        }
        for name in overrides.get("steps", STEPS)
    ]
    durability = {
        "schema_version": "memory_atlas.durability_recovery.v1",
        "frozen_release_id": RELEASE,
        "rolled_back_to": "20260804T105352Z-2b7a59dc4227",
        "rolled_forward_to": overrides.get("rolled_forward_to", RELEASE),
        "rollback_exit_code": overrides.get("rollback_exit_code", 0),
        "roll_forward_exit_code": overrides.get("roll_forward_exit_code", 0),
        "isolated_restore": overrides.get("isolated_restore", {"state": "PASS", "validated": [{"file": "current.json"}]}),
        "steps": steps,
    }
    (tmp_path / "DURABILITY_RECOVERY_REPORT.json").write_text(
        json.dumps(durability, ensure_ascii=False), encoding="utf-8")

    receipts = []
    for name, body in (overrides.get("receipts") or _receipts()).items():
        target = tmp_path / name
        target.write_text(json.dumps(body, ensure_ascii=False), encoding="utf-8")
        receipts.append(str(target))
    if overrides.get("no_receipts"):
        receipts = [str(tmp_path / "absent.json")]

    injection = overrides.get("fault_injection", {
        "schema_version": "memory_atlas.fault_injection.v1", "exit_code": 0,
        "cases": [{"name": "test_time_regression_refused", "outcome": "passed"},
                  {"name": "test_invalid_schema_refused", "outcome": "passed"}],
    })
    injection_path = tmp_path / "FAULT_INJECTION.json"
    if injection is not None:
        injection_path.write_text(json.dumps(injection, ensure_ascii=False), encoding="utf-8")

    subject = {
        "schema_version": "memory_atlas.verifier_subject.v1",
        "fault_injection_report_path": None if injection is None else str(injection_path),
        "frozen_candidate_path": str(tmp_path / "FROZEN_CANDIDATE.json"),
        "durability_report_path": str(tmp_path / "DURABILITY_RECOVERY_REPORT.json"),
        "snapshot_store_root": str(store),
        "live_snapshot_schema_path": str(REPO / "OpenAIDatabase" / "schema" / "memory_atlas.live_snapshot.v1.schema.json"),
        "browser_receipt_paths": receipts,
    }
    (tmp_path / "VERIFIER_SUBJECT.json").write_text(json.dumps(subject, ensure_ascii=False), encoding="utf-8")
    return tmp_path


def _receipts() -> dict:
    identity = {"run_id": RUN, "source_completed_at": "2026-08-03T17:31:57+00:00", "release_id": RELEASE}
    return {
        "auto.json": {"verdict": "PASS", "identity": identity, "auto_revalidated": True},
        "refresh.json": {"verdict": "PASS", "identity": identity},
        "relogin.json": {"verdict": "PASS", "identity": identity},
    }


def _run(tmp_path: Path, capsys) -> dict:
    code = main([str(tmp_path), "--out", str(tmp_path / "report.json")])
    capsys.readouterr()
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert (code == 0) == (report["verdict"] == "PASS")
    return report


def _verdict(report: dict, ac_id: str) -> str:
    return next(row["verdict"] for row in report["checks"] if row["acceptance_id"] == ac_id)


def test_a_healthy_subject_passes(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path), capsys)
    assert report["verdict"] == "PASS", report
    assert {row["acceptance_id"] for row in report["checks"]} == {
        "MA-LIVE-AC-007", "MA-LIVE-AC-008", "MA-LIVE-AC-011", "MA-LIVE-AC-016"}


def test_the_report_states_what_independence_it_actually_has(tmp_path: Path, capsys) -> None:
    # The one thing a builder-written verifier must never do is imply it is a
    # second party.
    report = _run(_subject(tmp_path), capsys)
    assert report["independence"]["written_by"] == "the builder"
    assert report["independence"]["writes_performed"] == 0
    assert "不等于第二方独立验收" in report["independence"]["weaker_than_zh"]


def test_missing_browser_receipts_block_rather_than_pass(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, no_receipts=True), capsys)
    assert _verdict(report, "MA-LIVE-AC-007") == "BLOCKED"
    assert report["verdict"] == "BLOCKED"


def test_receipts_from_different_runs_are_a_time_regression(tmp_path: Path, capsys) -> None:
    receipts = _receipts()
    receipts["refresh.json"]["identity"] = {**receipts["refresh.json"]["identity"],
                                            "source_completed_at": "2026-07-16T00:00:00+00:00"}
    report = _run(_subject(tmp_path, receipts=receipts), capsys)
    assert _verdict(report, "MA-LIVE-AC-007") == "FAIL"


def test_a_failing_browser_receipt_fails(tmp_path: Path, capsys) -> None:
    receipts = _receipts()
    receipts["relogin.json"]["verdict"] = "FAIL"
    report = _run(_subject(tmp_path, receipts=receipts), capsys)
    assert _verdict(report, "MA-LIVE-AC-007") == "FAIL"


def test_current_moving_forward_with_last_good_preserved_passes(tmp_path: Path, capsys) -> None:
    """The reconcile republishing a newer reading of the same run is the system
    working. The first version of this check called it a failure and failed a
    healthy production run; "does not move on failure" is not "never moves"."""
    subject = _subject(tmp_path)
    store = tmp_path / "live-snapshot"
    newer = _snapshot()
    newer["run"]["reconciled_at"] = "2026-08-04T11:37:40+00:00"
    previous_digest = hashlib.sha256((store / "current.json").read_bytes()).hexdigest()
    (store / "current.json").write_text(json.dumps(newer, ensure_ascii=False), encoding="utf-8")
    frozen = json.loads((tmp_path / "FROZEN_CANDIDATE.json").read_text(encoding="utf-8"))
    frozen["store_digests"]["current_sha256"] = previous_digest
    (tmp_path / "FROZEN_CANDIDATE.json").write_text(json.dumps(frozen, ensure_ascii=False), encoding="utf-8")
    report = _run(subject, capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "PASS", report


def test_current_moving_backwards_fails(tmp_path: Path, capsys) -> None:
    subject = _subject(tmp_path)
    store = tmp_path / "live-snapshot"
    older = _snapshot()
    older["run"]["source_completed_at"] = "2026-07-16T00:00:00+00:00"
    previous_digest = hashlib.sha256((store / "current.json").read_bytes()).hexdigest()
    (store / "current.json").write_text(json.dumps(older, ensure_ascii=False), encoding="utf-8")
    frozen = json.loads((tmp_path / "FROZEN_CANDIDATE.json").read_text(encoding="utf-8"))
    frozen["store_digests"]["current_sha256"] = previous_digest
    (tmp_path / "FROZEN_CANDIDATE.json").write_text(json.dumps(frozen, ensure_ascii=False), encoding="utf-8")
    report = _run(subject, capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "FAIL"


def test_current_moving_without_preserving_last_good_fails(tmp_path: Path, capsys) -> None:
    subject = _subject(tmp_path)
    store = tmp_path / "live-snapshot"
    newer = _snapshot()
    newer["run"]["reconciled_at"] = "2026-08-04T11:37:40+00:00"
    (store / "current.json").write_text(json.dumps(newer, ensure_ascii=False), encoding="utf-8")
    (store / "previous.json").write_text(json.dumps({**newer, "analysis": {"event_count": 1}}, ensure_ascii=False), encoding="utf-8")
    frozen = json.loads((tmp_path / "FROZEN_CANDIDATE.json").read_text(encoding="utf-8"))
    frozen["store_digests"]["current_sha256"] = "a" * 64
    (tmp_path / "FROZEN_CANDIDATE.json").write_text(json.dumps(frozen, ensure_ascii=False), encoding="utf-8")
    report = _run(subject, capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "FAIL"


def test_missing_fault_injection_evidence_blocks(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, fault_injection=None), capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "BLOCKED"


def test_a_failing_fault_injection_case_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, fault_injection={
        "schema_version": "memory_atlas.fault_injection.v1", "exit_code": 1,
        "cases": [{"name": "test_time_regression_refused", "outcome": "failed"}]}), capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "FAIL"


def test_current_changing_mid_drill_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, step_digest={"rollback_to_previous": "b" * 64}), capsys)
    assert _verdict(report, "MA-LIVE-AC-008") == "FAIL"


def test_a_current_with_no_history_object_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, history_present=False), capsys)
    assert _verdict(report, "MA-LIVE-AC-011") == "FAIL"


def test_history_holding_a_different_run_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, history_run="marun_someone_else"), capsys)
    assert _verdict(report, "MA-LIVE-AC-011") == "FAIL"


@pytest.mark.parametrize("field", ["run_id", "trace_id", "release_id", "deployment_revision"])
def test_identity_drift_during_recovery_fails(tmp_path: Path, capsys, field: str) -> None:
    drifted = {**_identity(), field: "drifted"}
    report = _run(_subject(tmp_path, step_identity={"rollback_to_previous": drifted}), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_an_unreadable_snapshot_after_a_recovery_step_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, step_identity={"isolated_restore": {"readable": False, "reason": "gone"}}), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_an_unhealthy_recovery_step_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, health={"restart_api_and_container": {"internal_api": "000", "internal_web": "200"}}), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_a_missing_drill_step_blocks(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, steps=("baseline", "restart_api_and_container")), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "BLOCKED"


def test_a_failed_isolated_restore_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, isolated_restore={"state": "FAIL", "reason": "schema"}), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_a_non_zero_rollback_exit_code_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, roll_forward_exit_code=7), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_not_returning_to_the_frozen_candidate_fails(tmp_path: Path, capsys) -> None:
    report = _run(_subject(tmp_path, rolled_forward_to="20260804T105352Z-2b7a59dc4227"), capsys)
    assert _verdict(report, "MA-LIVE-AC-016") == "FAIL"


def test_no_subject_at_all_blocks(tmp_path: Path, capsys) -> None:
    code = main([str(tmp_path), "--out", str(tmp_path / "report.json")])
    capsys.readouterr()
    report = json.loads((tmp_path / "report.json").read_text(encoding="utf-8"))
    assert code == 2 and report["verdict"] == "BLOCKED"


def test_the_verifier_has_no_write_path_to_the_subject() -> None:
    """It may write only its own report, and only where told."""
    source = (REPO / "OpenAIDatabase" / "scripts" / "memory_atlas_independent_verifier.py").read_text(encoding="utf-8")
    for forbidden in ("shutil.", "os.remove", "os.unlink", "os.rename", "subprocess", "requests.post"):
        assert forbidden not in source, forbidden
    assert source.count("write_text") == 1  # the report, in emit()
