from __future__ import annotations

import argparse
import contextlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import codex_push_main as module  # noqa: E402
from memory_atlas_cli.parser import parse_args  # noqa: E402


def git(path: Path, *arguments: str, check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", "-C", str(path), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if check and result.returncode != 0:
        raise AssertionError(result.stderr or result.stdout)
    return result


class IsolatedRepository:
    def __init__(self, root: Path):
        self.root = root
        self.remote = root / "origin.git"
        self.checkout = root / "checkout"
        self.database = self.checkout / "OpenAIDatabase"
        git(root, "init", "--bare", "--initial-branch=main", str(self.remote))
        git(root, "init", "--initial-branch=main", str(self.checkout))
        git(self.checkout, "config", "user.name", "Memory Atlas Test")
        git(self.checkout, "config", "user.email", "memory-atlas@example.invalid")
        (self.database / module.CONTRACT_PATH.parent).mkdir(parents=True)
        (self.database / module.CONTRACT_PATH).write_text(
            json.dumps(module.EXPECTED_CONTRACT, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        state = self.database / "data/sync_state/codex.json"
        state.parent.mkdir(parents=True)
        state.write_text('{"revision": 1}\n', encoding="utf-8")
        git(self.checkout, "add", "--", "OpenAIDatabase")
        git(self.checkout, "commit", "-m", "seed")
        git(self.checkout, "remote", "add", "origin", str(self.remote))
        git(self.checkout, "push", "-u", "origin", "main")
        self.baseline_oid = git(self.checkout, "rev-parse", "HEAD").stdout.strip()

    def advance_remote(self, label: str = "competitor") -> str:
        competitor = self.root / label
        git(self.root, "clone", str(self.remote), str(competitor))
        git(competitor, "config", "user.name", "Competing Writer")
        git(competitor, "config", "user.email", "competitor@example.invalid")
        marker = competitor / f"{label}.txt"
        marker.write_text(f"{label}\n", encoding="utf-8")
        git(competitor, "add", "--", marker.name)
        git(competitor, "commit", "-m", label)
        git(competitor, "push", "origin", "main")
        return git(competitor, "rev-parse", "HEAD").stdout.strip()

    def remote_oid(self) -> str:
        return git(self.remote, "rev-parse", "refs/heads/main").stdout.strip()


def stable_source_probe(database_dir: Path, codex_home: Path | None) -> dict[str, object]:
    del database_dir, codex_home
    return {
        "source_metadata_sha256": "a" * 64,
        "eligible_file_count": 2,
        "eligible_total_bytes": 12,
    }


def passing_validation(database_dir: Path, repo_root: Path) -> dict[str, object]:
    del database_dir, repo_root
    return {
        "status": "PASS",
        "profile": "sync",
        "failed_count": 0,
        "skipped_critical_count": 0,
    }


def passing_guard(database_dir: Path, repo_root: Path) -> dict[str, object]:
    del database_dir, repo_root
    return {"status": "PASS", "single_commit_ready": True}


def state_pipeline(content: str = '{"revision": 2}\n'):
    def run(database_dir: Path, archive_id: str, codex_home: Path | None) -> dict[str, object]:
        del archive_id, codex_home
        (database_dir / "data/sync_state/codex.json").write_text(content, encoding="utf-8")
        return {"status": "PASS", "writes_files": True}

    return run


class CodexPushMainTests(unittest.TestCase):
    def execute(self, repository: IsolatedRepository, **overrides):
        arguments = {
            "pipeline_runner": state_pipeline(),
            "validation_runner": passing_validation,
            "source_probe": stable_source_probe,
            "push_guard": passing_guard,
        }
        arguments.update(overrides)
        return module.execute_codex_push_main(
            repository.database,
            "codex-incremental-20260716t120000z",
            **arguments,
        )

    def test_contract_and_exact_command_surface(self) -> None:
        loaded = module.load_codex_push_main_contract(ROOT)
        self.assertEqual(loaded, module.EXPECTED_CONTRACT)
        positional = parse_args(["sync", "codex", "--push-main"])
        historical = parse_args(["sync", "--source", "codex", "--push-main"])
        self.assertEqual(positional.source, "codex")
        self.assertEqual(historical.source, "codex")
        self.assertTrue(positional.push_main)
        with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
            parse_args(["sync", "codex", "--source", "chatgpt", "--push-main"])

    def test_success_commits_audited_scope_and_pushes_main_once(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            commands: list[list[str]] = []
            real_run_git = module.run_git

            def recording_run_git(repo_root, arguments, check=True, input_text=None):
                commands.append(list(arguments))
                return real_run_git(
                    repo_root,
                    arguments,
                    check=check,
                    input_text=input_text,
                )

            with mock.patch.object(module, "run_git", side_effect=recording_run_git):
                result = self.execute(repository)

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "PUSHED_MAIN")
            self.assertTrue(result["commit_created"])
            self.assertTrue(result["pushed"])
            self.assertTrue(result["remote_verified"])
            self.assertEqual(result["push_attempt_count"], 1)
            self.assertEqual(repository.remote_oid(), result["commit_oid"])
            self.assertEqual(git(repository.checkout, "status", "--porcelain").stdout, "")
            committed = git(
                repository.checkout,
                "diff-tree",
                "--no-commit-id",
                "--name-only",
                "-r",
                result["commit_oid"],
            ).stdout.splitlines()
            self.assertEqual(committed, ["OpenAIDatabase/data/sync_state/codex.json"])
            push_commands = [command for command in commands if command and command[0] == "push"]
            self.assertEqual(
                push_commands,
                [[
                    "push",
                    "--porcelain",
                    "origin",
                    f"{result['commit_oid']}:refs/heads/main",
                ]],
            )
            self.assertFalse(any(command and command[0] == "fetch" for command in commands))
            self.assertFalse(any("force" in argument for command in commands for argument in command))

    def test_idempotent_no_changes_does_not_commit_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))

            def no_changes(database_dir: Path, archive_id: str, codex_home: Path | None):
                del database_dir, archive_id, codex_home
                return {"status": "PASS", "writes_files": False}

            result = self.execute(repository, pipeline_runner=no_changes)
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "NO_CHANGES")
            self.assertFalse(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertEqual(repository.remote_oid(), repository.baseline_oid)

    def test_non_main_and_dirty_worktrees_fail_before_pipeline(self) -> None:
        for mode in ("branch", "dirty"):
            with self.subTest(mode=mode), tempfile.TemporaryDirectory() as temporary:
                repository = IsolatedRepository(Path(temporary))
                if mode == "branch":
                    git(repository.checkout, "switch", "-c", "feature")
                    expected = "branch_is_not_main"
                else:
                    (repository.checkout / "unrelated.txt").write_text("dirty\n", encoding="utf-8")
                    expected = "initial_worktree_not_clean"
                pipeline = mock.Mock(side_effect=AssertionError("pipeline must not run"))
                result = self.execute(repository, pipeline_runner=pipeline)
                self.assertEqual(result["status"], "FAIL_CLOSED")
                self.assertEqual(result["reason"], expected)
                self.assertFalse(pipeline.called)
                self.assertEqual(result["push_attempt_count"], 0)

    def test_stale_remote_base_fails_before_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            competing_oid = repository.advance_remote()
            pipeline = mock.Mock(side_effect=AssertionError("pipeline must not run"))
            result = self.execute(repository, pipeline_runner=pipeline)
            self.assertEqual(result["reason"], "remote_main_not_at_head")
            self.assertFalse(pipeline.called)
            self.assertEqual(repository.remote_oid(), competing_oid)
            self.assertEqual(result["push_attempt_count"], 0)

    def test_source_change_stops_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            probes = iter(
                [
                    {"source_metadata_sha256": "a" * 64},
                    {"source_metadata_sha256": "b" * 64},
                ]
            )

            def changing_probe(database_dir: Path, codex_home: Path | None):
                del database_dir, codex_home
                return next(probes)

            result = self.execute(repository, source_probe=changing_probe)
            self.assertEqual(result["reason"], "codex_source_changed_during_pipeline")
            self.assertFalse(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertEqual(repository.remote_oid(), repository.baseline_oid)

    def test_pipeline_cannot_hide_a_local_commit_behind_a_clean_status(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))

            def hidden_commit(database_dir: Path, archive_id: str, codex_home: Path | None):
                del archive_id, codex_home
                state = database_dir / "data/sync_state/codex.json"
                state.write_text('{"revision": 2}\n', encoding="utf-8")
                git(
                    repository.checkout,
                    "add",
                    "--",
                    str(state.relative_to(repository.checkout.resolve())),
                )
                git(repository.checkout, "commit", "-m", "unexpected pipeline commit")
                return {"status": "PASS", "writes_files": True}

            result = self.execute(repository, pipeline_runner=hidden_commit)
            self.assertEqual(result["reason"], "head_changed_during_run")
            self.assertFalse(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertEqual(repository.remote_oid(), repository.baseline_oid)

    def test_out_of_scope_and_append_only_modification_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))

            def outside(database_dir: Path, archive_id: str, codex_home: Path | None):
                del archive_id, codex_home
                (database_dir.parent / "outside.txt").write_text("outside\n", encoding="utf-8")
                return {"status": "PASS", "writes_files": True}

            result = self.execute(repository, pipeline_runner=outside)
            self.assertEqual(result["reason"], "change_outside_database")
            self.assertFalse(result["commit_created"])

        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            raw = repository.database / "data/raw_archives/codex/existing/manifest.json"
            raw.parent.mkdir(parents=True)
            raw.write_text("{}\n", encoding="utf-8")
            git(repository.checkout, "add", "--", str(raw.relative_to(repository.checkout)))
            git(repository.checkout, "commit", "-m", "seed raw")
            git(repository.checkout, "push", "origin", "main")
            repository.baseline_oid = git(repository.checkout, "rev-parse", "HEAD").stdout.strip()

            def modify_raw(database_dir: Path, archive_id: str, codex_home: Path | None):
                del archive_id, codex_home
                (database_dir / "data/raw_archives/codex/existing/manifest.json").write_text(
                    '{"changed": true}\n', encoding="utf-8"
                )
                return {"status": "PASS", "writes_files": True}

            result = self.execute(repository, pipeline_runner=modify_raw)
            self.assertEqual(result["reason"], "append_only_path_modified")
            self.assertFalse(result["commit_created"])

    def test_validation_and_push_size_failures_never_commit_or_push(self) -> None:
        failures = (
            (
                "validation",
                {"validation_runner": lambda database_dir, repo_root: {"status": "FAIL"}},
                "sync_validation_failed",
            ),
            (
                "push_size",
                {"push_guard": lambda database_dir, repo_root: {"status": "FAIL", "single_commit_ready": False}},
                "push_size_guard_failed",
            ),
        )
        for label, overrides, expected in failures:
            with self.subTest(label=label), tempfile.TemporaryDirectory() as temporary:
                repository = IsolatedRepository(Path(temporary))
                result = self.execute(repository, **overrides)
                self.assertEqual(result["reason"], expected)
                self.assertFalse(result["commit_created"])
                self.assertEqual(result["push_attempt_count"], 0)
                self.assertEqual(repository.remote_oid(), repository.baseline_oid)

    def test_validator_worktree_mutation_and_remote_race_stop_before_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))

            def mutate_worktree(database_dir: Path, repo_root: Path):
                del database_dir
                (repo_root / "validator-side-effect.txt").write_text("unexpected\n", encoding="utf-8")
                return {"status": "PASS"}

            result = self.execute(repository, validation_runner=mutate_worktree)
            self.assertEqual(result["reason"], "worktree_changed_during_validation")
            self.assertFalse(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 0)

        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))

            def race_remote(database_dir: Path, repo_root: Path):
                del database_dir, repo_root
                repository.advance_remote("race")
                return {"status": "PASS"}

            result = self.execute(repository, validation_runner=race_remote)
            self.assertEqual(result["reason"], "remote_main_changed_during_run")
            self.assertFalse(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 0)

    def test_rejected_push_preserves_one_local_commit_without_retry(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            real_run_git = module.run_git
            push_calls = 0

            def reject_push(repo_root, arguments, check=True, input_text=None):
                nonlocal push_calls
                if arguments and arguments[0] == "push":
                    push_calls += 1
                    return subprocess.CompletedProcess(arguments, 1, "", "rejected")
                return real_run_git(
                    repo_root,
                    arguments,
                    check=check,
                    input_text=input_text,
                )

            with mock.patch.object(module, "run_git", side_effect=reject_push):
                result = self.execute(repository)
            self.assertEqual(result["status"], "FAIL_CLOSED")
            self.assertEqual(result["reason"], "push_rejected")
            self.assertTrue(result["commit_created"])
            self.assertEqual(result["push_attempt_count"], 1)
            self.assertEqual(push_calls, 1)
            self.assertFalse(result["pushed"])
            self.assertEqual(repository.remote_oid(), repository.baseline_oid)
            self.assertEqual(git(repository.checkout, "rev-parse", "HEAD").stdout.strip(), result["commit_oid"])
            self.assertEqual(
                git(repository.checkout, "rev-list", "--count", f"{repository.baseline_oid}..HEAD").stdout.strip(),
                "1",
            )

    def test_dry_run_checks_base_without_pipeline_or_remote_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = IsolatedRepository(Path(temporary))
            pipeline = mock.Mock(side_effect=AssertionError("pipeline must not run"))
            result = module.execute_codex_push_main(
                repository.database,
                "codex-incremental-20260716t120000z",
                dry_run=True,
                pipeline_runner=pipeline,
                source_probe=stable_source_probe,
            )
            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["outcome"], "DRY_RUN_READY")
            self.assertFalse(pipeline.called)
            self.assertEqual(result["push_attempt_count"], 0)
            self.assertEqual(repository.remote_oid(), repository.baseline_oid)

    def test_non_codex_push_main_is_rejected_without_execution(self) -> None:
        args = argparse.Namespace(
            source="chatgpt",
            archive_id="codex-incremental-20260716t120000z",
            dry_run=False,
            official_export=None,
            input=None,
            markdown_report=None,
            redact_for_public_backup=False,
            public_transcripts=False,
            database_dir=ROOT,
            codex_home=None,
            message=None,
        )
        with mock.patch.object(module, "execute_codex_push_main") as execute, mock.patch(
            "builtins.print"
        ):
            return_code = module.run_codex_push_main(args)
        self.assertEqual(return_code, 2)
        execute.assert_not_called()


if __name__ == "__main__":
    unittest.main()
