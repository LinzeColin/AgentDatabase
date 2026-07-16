from __future__ import annotations

import contextlib
import fcntl
import io
import json
import os
import stat
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import codex_scheduler as module  # noqa: E402
from memory_atlas_cli import sync as sync_module  # noqa: E402
from memory_atlas_cli.parser import parse_args  # noqa: E402


T0 = datetime(2026, 7, 17, 0, 0, tzinfo=timezone.utc)


def observation(digest: str = "a") -> dict[str, object]:
    return {
        "source_metadata_sha256": digest * 64,
        "eligible_file_count": 3,
        "eligible_total_bytes": 24,
    }


def source_probe(digest: str = "a"):
    def probe(database_dir: Path, codex_home: Path | None) -> dict[str, object]:
        del database_dir, codex_home
        return observation(digest)

    return probe


def push_result(
    *,
    status: str = "PASS",
    outcome: str = "PUSHED_MAIN",
    push_attempt_count: int = 1,
    commit_created: bool = True,
    remote_push_attempted: bool = True,
) -> dict[str, object]:
    return {
        "schema_version": "memory_atlas.codex_push_main_result.v1_2_1_s07_p3_t1",
        "task_id": "S07-P3-T1",
        "acceptance_id": "ACC-MA-V121-S07-P3-T1",
        "command": "sync codex --push-main",
        "status": status,
        "outcome": outcome,
        "push_attempt_count": push_attempt_count,
        "commit_created": commit_created,
        "remote_push_attempted": remote_push_attempted,
        "pushed": status == "PASS" and outcome == "PUSHED_MAIN",
        "remote_verified": status == "PASS",
        "force_push": False,
        "fetch_executed": False,
        "branch_created": False,
        "pull_request_created": False,
        "merge_executed": False,
        "rebase_executed": False,
    }


class SchedulerFixture:
    def __init__(self, root: Path):
        self.root = root
        self.database = root / "repo/OpenAIDatabase"
        self.state_dir = root / "runtime/codex-scheduler"
        profile_path = self.database / module.PROFILE_PATH
        profile_path.parent.mkdir(parents=True)
        profile_path.write_text(
            json.dumps(module.EXPECTED_PROFILE, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        model_path = self.database / module.MODEL_PARAMETERS_PATH
        model_path.parent.mkdir(parents=True)
        model_path.write_text(
            json.dumps(module.EXPECTED_MODEL_PARAMETERS, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    @property
    def state_path(self) -> Path:
        return self.state_dir / module.STATE_FILENAME

    def execute(self, **overrides):
        arguments = {
            "state_dir": self.state_dir,
            "owner_run_id": "owner-run-1",
            "now": T0,
            "source_probe": source_probe(),
            "push_main_runner": mock.Mock(return_value=push_result()),
        }
        arguments.update(overrides)
        return module.execute_codex_scheduler(self.database, **arguments)


class CodexSchedulerTests(unittest.TestCase):
    def test_contract_model_and_cli_surface_are_exact(self) -> None:
        self.assertEqual(module.load_codex_scheduler_profile(ROOT), module.EXPECTED_PROFILE)
        self.assertEqual(module.load_codex_scheduler_model(ROOT), module.EXPECTED_MODEL_PARAMETERS)

        args = parse_args(
            [
                "run",
                "--profile",
                "codex-scheduler",
                "--dry-run",
                "--owner-run-id",
                "owner-run-1",
                "--state-dir",
                "/tmp/memory-atlas-scheduler-test",
            ]
        )
        self.assertEqual(args.profile, "codex-scheduler")
        self.assertTrue(args.dry_run)
        self.assertEqual(args.owner_run_id, "owner-run-1")
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["run", "--profile", "unknown-scheduler"])

    def test_dry_run_checks_t1_without_state_write_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result(
                outcome="DRY_RUN_READY",
                push_attempt_count=0,
                commit_created=False,
                remote_push_attempted=False,
            ))

            result = fixture.execute(dry_run=True, push_main_runner=runner)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "DRY_RUN_READY")
            self.assertEqual(result["sync_invocation_count"], 0)
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertFalse(result["writes_state"])
            self.assertFalse(fixture.state_dir.exists())
            self.assertEqual(runner.call_count, 1)
            self.assertTrue(runner.call_args.kwargs["dry_run"])

    def test_dry_run_preserves_well_formed_t1_not_ready_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            child = push_result(
                status="FAIL_CLOSED",
                outcome="STOPPED",
                push_attempt_count=0,
                commit_created=False,
                remote_push_attempted=False,
            )
            child["reason"] = "canonical_worktree_not_clean"
            runner = mock.Mock(return_value=child)

            result = fixture.execute(dry_run=True, push_main_runner=runner)

            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "push_main_dry_run_not_ready")
            self.assertEqual(result["push_main_dry_run"], child)
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertFalse(result["writes_state"])
            self.assertFalse(fixture.state_dir.exists())

    def test_run_profile_dispatches_scheduler_once_and_rejects_owner_daily_step(self) -> None:
        args = parse_args(["run", "--profile", "codex-scheduler", "--dry-run"])
        with mock.patch.object(sync_module, "run_codex_scheduler", return_value=0) as runner:
            self.assertEqual(sync_module.run_profile(args), 0)
        runner.assert_called_once_with(args)

        bad = parse_args(
            ["run", "--profile", "codex-scheduler", "--dry-run", "--step", "sync"]
        )
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
            sync_module,
            "run_codex_scheduler",
            side_effect=AssertionError("scheduler must not run"),
        ):
            self.assertEqual(sync_module.run_profile(bad), 2)

    def test_owner_daily_rejects_scheduler_only_arguments(self) -> None:
        args = parse_args(
            [
                "run",
                "--profile",
                "owner-daily",
                "--dry-run",
                "--owner-run-id",
                "owner-run-1",
            ]
        )
        with contextlib.redirect_stdout(io.StringIO()), mock.patch.object(
            sync_module,
            "OwnerDailyRunner",
            side_effect=AssertionError("owner daily must not run"),
        ):
            self.assertEqual(sync_module.run_profile(args), 2)

    def test_first_observation_coalesces_and_second_stable_observation_runs_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result())

            first = fixture.execute(push_main_runner=runner)
            second = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                push_main_runner=runner,
            )

            self.assertEqual(first["outcome"], "COALESCING")
            self.assertEqual(first["same_metadata_observation_count"], 1)
            self.assertEqual(first["sync_invocation_count"], 0)
            self.assertEqual(second["status"], "PASS")
            self.assertEqual(second["outcome"], "SYNC_COMPLETED")
            self.assertEqual(second["child_outcome"], "PUSHED_MAIN")
            self.assertEqual(second["sync_invocation_count"], 1)
            self.assertEqual(second["push_attempt_count"], 1)
            self.assertEqual(runner.call_count, 1)
            state = json.loads(fixture.state_path.read_text(encoding="utf-8"))
            self.assertIsNone(state["pending"])
            self.assertEqual(state["last_completed"]["source_metadata_sha256"], "a" * 64)
            self.assertIsNone(state["active_attempt"])

    def test_ready_run_accepts_t1_no_changes_without_push_attempt(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result(
                outcome="NO_CHANGES",
                push_attempt_count=0,
                commit_created=False,
                remote_push_attempted=False,
            ))
            fixture.execute(push_main_runner=runner)

            result = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                push_main_runner=runner,
            )

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "SYNC_COMPLETED")
            self.assertEqual(result["child_outcome"], "NO_CHANGES")
            self.assertEqual(result["sync_invocation_count"], 1)
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertFalse(result["writes_repository"])

    def test_source_change_restarts_quiet_window_but_preserves_pending_deadline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result())
            fixture.execute(push_main_runner=runner)

            result = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                source_probe=source_probe("b"),
                push_main_runner=runner,
            )

            self.assertEqual(result["outcome"], "COALESCING")
            self.assertEqual(result["same_metadata_observation_count"], 1)
            self.assertEqual(runner.call_count, 0)
            state = json.loads(fixture.state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["pending"]["source_metadata_sha256"], "b" * 64)
            self.assertEqual(state["pending"]["first_observed_at"], module.isoformat_utc(T0))
            self.assertEqual(
                state["pending"]["last_changed_at"],
                module.isoformat_utc(T0 + timedelta(seconds=301)),
            )

    def test_minimum_success_interval_throttles_new_changes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result())
            fixture.execute(push_main_runner=runner)
            fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                push_main_runner=runner,
            )
            fixture.execute(
                owner_run_id="owner-run-3",
                now=T0 + timedelta(seconds=600),
                source_probe=source_probe("b"),
                push_main_runner=runner,
            )

            throttled = fixture.execute(
                owner_run_id="owner-run-4",
                now=T0 + timedelta(seconds=901),
                source_probe=source_probe("b"),
                push_main_runner=runner,
            )

            self.assertEqual(throttled["outcome"], "THROTTLED")
            self.assertGreater(throttled["throttle_remaining_seconds"], 0)
            self.assertEqual(runner.call_count, 1)

    def test_max_pending_window_bounds_continuous_source_churn(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result())
            fixture.execute(push_main_runner=runner)
            second = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=900),
                source_probe=source_probe("b"),
                push_main_runner=runner,
            )

            result = fixture.execute(
                owner_run_id="owner-run-3",
                now=T0 + timedelta(seconds=1801),
                source_probe=source_probe("c"),
                push_main_runner=runner,
            )

            self.assertEqual(second["outcome"], "COALESCING")
            self.assertEqual(result["outcome"], "SYNC_COMPLETED")
            self.assertTrue(result["max_pending_window_reached"])
            self.assertEqual(result["same_metadata_observation_count"], 1)
            self.assertEqual(runner.call_count, 1)

    def test_same_owner_run_id_never_invokes_t1_twice(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            runner = mock.Mock(return_value=push_result())
            fixture.execute(push_main_runner=runner)
            fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                push_main_runner=runner,
            )

            duplicate = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=3700),
                source_probe=source_probe("b"),
                push_main_runner=runner,
            )

            self.assertEqual(duplicate["outcome"], "OWNER_RUN_ALREADY_ATTEMPTED")
            self.assertEqual(duplicate["sync_invocation_count"], 0)
            self.assertEqual(runner.call_count, 1)

            state = json.loads(fixture.state_path.read_text(encoding="utf-8"))
            state["attempted_owner_run_ids"].append("owner-run-3")
            state["last_attempt"]["owner_run_id"] = "owner-run-3"
            fixture.state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )
            historical_duplicate = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=7300),
                source_probe=source_probe("c"),
                push_main_runner=runner,
            )
            self.assertEqual(historical_duplicate["outcome"], "OWNER_RUN_ALREADY_ATTEMPTED")
            self.assertEqual(runner.call_count, 1)

    def test_nonblocking_lock_stops_concurrent_owner_run(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            fixture.execute()
            lock_path = fixture.state_dir / module.LOCK_FILENAME
            with lock_path.open("a+b") as handle:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                result = fixture.execute(
                    owner_run_id="owner-run-2",
                    now=T0 + timedelta(seconds=301),
                )

            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "scheduler_run_locked")
            self.assertEqual(result["sync_invocation_count"], 0)

    def test_active_or_effectful_failed_attempt_requires_manual_intervention(self) -> None:
        cases = (
            (
                "active",
                None,
                "previous_scheduler_attempt_incomplete",
            ),
            (
                "failed_push",
                push_result(status="FAIL_CLOSED", outcome="STOPPED"),
                "push_main_child_failed_after_git_effect",
            ),
        )
        for label, child, expected in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = SchedulerFixture(Path(temporary))
                fixture.execute()
                if label == "active":
                    state = json.loads(fixture.state_path.read_text(encoding="utf-8"))
                    state["active_attempt"] = {
                        "owner_run_id": "crashed-owner-run",
                        "started_at": module.isoformat_utc(T0 + timedelta(seconds=1)),
                        "source_metadata_sha256": "a" * 64,
                    }
                    state["attempted_owner_run_ids"].append("crashed-owner-run")
                    fixture.state_path.write_text(
                        json.dumps(state, ensure_ascii=False, indent=2) + "\n",
                        encoding="utf-8",
                    )
                    result = fixture.execute(
                        owner_run_id="owner-run-2",
                        now=T0 + timedelta(seconds=301),
                    )
                else:
                    runner = mock.Mock(return_value=child)
                    result = fixture.execute(
                        owner_run_id="owner-run-2",
                        now=T0 + timedelta(seconds=301),
                        push_main_runner=runner,
                    )
                    state = json.loads(fixture.state_path.read_text(encoding="utf-8"))
                    self.assertTrue(state["manual_intervention_required"])

                self.assertEqual(result["status"], "FAIL_CLOSED")
                self.assertEqual(result["reason"], expected)
                self.assertLessEqual(result["sync_invocation_count"], 1)

    def test_child_contract_rejects_multiple_push_attempts(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            fixture.execute()
            runner = mock.Mock(return_value=push_result(push_attempt_count=2))

            result = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 + timedelta(seconds=301),
                push_main_runner=runner,
            )

            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "push_main_child_contract_invalid")
            self.assertEqual(result["sync_invocation_count"], 1)
            self.assertEqual(result["push_attempt_count"], 2)

    def test_child_contract_rejects_false_pass_semantics_and_wrong_schema(self) -> None:
        cases = (
            (
                "wrong_schema",
                {**push_result(), "schema_version": "wrong"},
            ),
            (
                "non_apply_outcome",
                push_result(
                    outcome="DRY_RUN_READY",
                    push_attempt_count=0,
                    commit_created=False,
                    remote_push_attempted=False,
                ),
            ),
            (
                "pushed_without_git_effect",
                push_result(
                    outcome="PUSHED_MAIN",
                    push_attempt_count=0,
                    commit_created=False,
                    remote_push_attempted=False,
                ),
            ),
        )
        for label, child in cases:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                fixture = SchedulerFixture(Path(temporary))
                fixture.execute()
                runner = mock.Mock(return_value=child)

                result = fixture.execute(
                    owner_run_id="owner-run-2",
                    now=T0 + timedelta(seconds=301),
                    push_main_runner=runner,
                )

                self.assertEqual(result["status"], "FAIL_CLOSED")
                self.assertEqual(result["reason"], "push_main_child_contract_invalid")
                self.assertEqual(result["sync_invocation_count"], 1)

    def test_state_finalize_failure_after_push_reports_possible_remote_effect(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            fixture.execute()
            runner = mock.Mock(return_value=push_result())
            real_write = module._write_state_atomic
            calls = 0

            def fail_second_write(state_dir: Path, payload: dict[str, object]) -> None:
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise module.CodexSchedulerError("injected_finalize_failure")
                real_write(state_dir, payload)

            with mock.patch.object(module, "_write_state_atomic", side_effect=fail_second_write):
                result = fixture.execute(
                    owner_run_id="owner-run-2",
                    now=T0 + timedelta(seconds=301),
                    push_main_runner=runner,
                )

            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "scheduler_state_finalize_failed_after_child")
            self.assertTrue(result["remote_effect_possible"])
            self.assertEqual(result["sync_invocation_count"], 1)
            self.assertEqual(runner.call_count, 1)

    def test_state_path_must_be_machine_local_outside_repo_source_and_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            codex_home = fixture.root / "codex-home"
            codex_home.mkdir()
            outside = fixture.root / "outside"
            outside.mkdir()
            symlink = fixture.root / "state-link"
            symlink.symlink_to(outside, target_is_directory=True)
            cases = (
                (fixture.database / "runtime", None, "scheduler_state_inside_database"),
                (codex_home / "runtime", codex_home, "scheduler_state_inside_codex_source"),
                (symlink, None, "scheduler_state_path_symlink"),
            )
            for state_dir, source_home, expected in cases:
                with self.subTest(expected=expected):
                    result = fixture.execute(state_dir=state_dir, codex_home=source_home)
                    self.assertEqual(result["reason"], expected)
                    self.assertFalse(result["writes_state"])

    def test_relative_codex_source_is_rejected_before_state_creation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))

            result = fixture.execute(codex_home=Path("relative-codex-home"))

            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "codex_source_path_not_absolute")
            self.assertFalse(result["writes_state"])
            self.assertFalse(fixture.state_dir.exists())

    def test_state_is_private_path_free_and_clock_regression_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            fixture.execute()
            state_text = fixture.state_path.read_text(encoding="utf-8")

            self.assertNotIn(str(fixture.root), state_text)
            mode = stat.S_IMODE(fixture.state_path.stat().st_mode)
            self.assertEqual(mode, 0o600)
            result = fixture.execute(
                owner_run_id="owner-run-2",
                now=T0 - timedelta(seconds=1),
            )
            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "scheduler_clock_regression")

    def test_profile_state_and_model_drift_fail_closed_before_source_probe(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            fixture = SchedulerFixture(Path(temporary))
            probe = mock.Mock(side_effect=AssertionError("source must not be read"))
            profile = dict(module.EXPECTED_PROFILE)
            profile["coalescing"] = dict(profile["coalescing"])
            profile["coalescing"]["quiet_period_seconds"] = 1
            (fixture.database / module.PROFILE_PATH).write_text(
                json.dumps(profile, ensure_ascii=False, indent=2) + "\n",
                encoding="utf-8",
            )

            result = fixture.execute(source_probe=probe)

            self.assertEqual(result["reason"], "scheduler_profile_drift")
            self.assertFalse(probe.called)


if __name__ == "__main__":
    unittest.main()
