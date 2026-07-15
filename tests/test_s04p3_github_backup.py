from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


REPO_ROOT = Path(__file__).resolve().parents[1]
GITHUB_BACKUP_SCRIPT = REPO_ROOT / "scripts" / "github_backup.py"
ATLASCTL_SCRIPT = REPO_ROOT / "scripts" / "atlasctl.py"
PUSH_SIZE_CONTRACT = REPO_ROOT / "config/data_sources/push_size_guard.json"
if str(REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "scripts"))

import github_backup as backup_module  # noqa: E402


def run_json(command: list[str], cwd: Path = REPO_ROOT, expect_success: bool = True) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if expect_success and result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {command}\nstdout={result.stdout}")
    start = result.stdout.find("{")
    if start < 0:
        raise AssertionError(f"command did not emit JSON: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    return json.loads(result.stdout[start:])


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", "-C", str(repo), *args], text=True).strip()


def create_backup_fixture(root: Path) -> None:
    files = {
        "data/public_raw/chatgpt/conversation_001.json": {"source_id": "chatgpt", "message_count": 1},
        "data/derived/visualization/memory_atlas.json": {"nodes": [], "edges": []},
        "data/derived/chat_reports/latest.json": {"status": "PASS"},
        "data/run_logs/sync_runs/2026-07-08.jsonl": '{"status":"PASS"}\n',
        "docs/reviews/sample_report.md": "# Sample report\n",
    }
    for relative_path, payload in files.items():
        path = root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(payload, str):
            path.write_text(payload, encoding="utf-8")
        else:
            path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    contract = root / "config/data_sources/push_size_guard.json"
    contract.parent.mkdir(parents=True, exist_ok=True)
    contract.write_bytes(PUSH_SIZE_CONTRACT.read_bytes())


class S04P3GithubBackupTest(unittest.TestCase):
    def test_atlasctl_push_dry_run_reports_backup_contract_without_writes(self) -> None:
        result = run_json([sys.executable, str(ATLASCTL_SCRIPT), "push", "--dry-run"])
        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["command"], "push")
        self.assertTrue(result["dry_run"])
        self.assertFalse(result["writes_files"])
        self.assertFalse(result["remote_push"])
        self.assertIn("data/public_raw", result["backup_targets"])
        self.assertIn("data/derived", result["backup_targets"])
        self.assertIn("data/run_logs", result["backup_targets"])
        self.assertIn("docs/reviews", result["backup_targets"])
        self.assertIn("git push origin HEAD:main", result["manual_push_command"])

    def test_backup_apply_commits_only_local_backup_scope_without_remote_push(self) -> None:
        self.assertTrue(GITHUB_BACKUP_SCRIPT.exists(), "github_backup.py should exist")
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")

            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
                "--message",
                "S04 P3 test backup",
            ])

            self.assertEqual(result["status"], "PASS")
            self.assertFalse(result["dry_run"])
            self.assertTrue(result["apply"])
            self.assertTrue(result["committed"])
            self.assertFalse(result["pushed"])
            self.assertFalse(result["remote_push"])
            self.assertEqual(result["push_size_guard"]["status"], "PASS")
            self.assertFalse(result["push_size_guard"]["staged_file_content_read"])
            self.assertEqual(git(root, "log", "-1", "--pretty=%s"), "S04 P3 test backup")
            self.assertEqual(git(root, "status", "--short"), "")
            self.assertIn("data/public_raw/chatgpt/conversation_001.json", result["committed_files"])
            self.assertIn("data/derived/visualization/memory_atlas.json", result["committed_files"])
            self.assertIn("data/run_logs/sync_runs/2026-07-08.jsonl", result["committed_files"])
            self.assertIn("docs/reviews/sample_report.md", result["committed_files"])

    def test_backup_apply_rejects_preexisting_staged_changes_without_commit(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            unrelated = root / "unrelated.txt"
            unrelated.write_text("keep staged\n", encoding="utf-8")
            git(root, "add", "unrelated.txt")

            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
            ], expect_success=False)

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "preexisting_staged_changes")
            self.assertFalse(result["committed"])
            self.assertFalse(result["remote_push"])
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "unrelated.txt")
            self.assertEqual(git(root, "rev-list", "--count", "--all"), "1")

    def test_backup_apply_rejects_non_main_before_staging_backup_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "feature")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")

            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
            ], expect_success=False)

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "push_size_guard_failed")
            self.assertEqual(result["push_size_guard"]["reason"], "branch_is_not_main")
            self.assertFalse(result["writes_files"])
            self.assertFalse(result["index_changed"])
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "")

    def test_backup_apply_does_not_commit_when_guard_requires_multiple_batches(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            pass_report = backup_module.build_staged_push_report(root, repo_root=root)
            batch_report = pass_report | {
                "single_commit_ready": False,
                "plan": pass_report["plan"] | {"batch_required": True, "batch_count": 2},
            }

            with mock.patch.object(
                backup_module,
                "build_staged_push_report",
                side_effect=[pass_report, batch_report],
            ):
                result = backup_module.apply_backup(root, root, "must not commit")

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "push_size_guard_failed")
            self.assertEqual(result["push_size_guard_reason"], "staged_batches_required")
            self.assertFalse(result["committed"])
            self.assertEqual(git(root, "rev-list", "--count", "--all"), "1")
            self.assertTrue(git(root, "diff", "--cached", "--name-only"))

    def test_backup_apply_binds_guard_to_index_tree_and_rejects_race(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            real_guard = backup_module.build_staged_push_report
            calls = 0

            def racing_guard(*args: object, **kwargs: object) -> dict[str, object]:
                nonlocal calls
                calls += 1
                if calls == 2:
                    (root / "race.txt").write_text("must not enter commit\n", encoding="utf-8")
                    git(root, "add", "race.txt")
                return real_guard(*args, **kwargs)

            with mock.patch.object(backup_module, "build_staged_push_report", side_effect=racing_guard):
                result = backup_module.apply_backup(root, root, "race must fail")

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "index_changed_during_push_size_guard")
            self.assertTrue(result["writes_files"])
            self.assertTrue(result["index_changed"])
            self.assertFalse(result["committed"])
            self.assertIn("race.txt", result["staged_files"])
            self.assertEqual(git(root, "rev-list", "--count", "--all"), "1")

    def test_backup_apply_does_not_execute_git_hooks(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            marker = root / ".git" / "pre-commit-ran"
            reference_marker = root / ".git" / "reference-transaction-ran"
            hook = root / ".git" / "hooks" / "pre-commit"
            hook.write_text(f"#!/bin/sh\ntouch '{marker}'\nexit 0\n", encoding="utf-8")
            hook.chmod(0o755)
            reference_hook = root / ".git" / "hooks" / "reference-transaction"
            reference_hook.write_text(
                f"#!/bin/sh\ntouch '{reference_marker}'\nexit 0\n",
                encoding="utf-8",
            )
            reference_hook.chmod(0o755)
            git(root, "config", "core.hooksPath", ".git/hooks")

            result = backup_module.apply_backup(root, root, "hook-free commit")

            self.assertEqual(result["status"], "PASS")
            self.assertTrue(result["committed"])
            self.assertEqual(result["commit_method"], "commit_tree_plus_update_ref_cas")
            self.assertFalse(result["hooks_executed"])
            self.assertFalse(marker.exists())
            self.assertFalse(reference_marker.exists())
            self.assertEqual(git(root, "rev-parse", "HEAD^{tree}"), result["audited_tree_oid"])

    def test_backup_apply_preserves_committed_truth_when_post_check_fails(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            real_run_git = backup_module.run_git

            def fail_post_commit_check(
                repo_root: Path,
                args: list[str],
                check: bool = True,
                input_text: str | None = None,
            ) -> subprocess.CompletedProcess[str]:
                if args and args[0] == "diff-tree":
                    raise RuntimeError("post-commit inspection failed")
                return real_run_git(repo_root, args, check=check, input_text=input_text)

            with mock.patch.object(backup_module, "run_git", side_effect=fail_post_commit_check):
                result = backup_module.apply_backup(root, root, "truthful committed state")

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "post_commit_inspection_failed")
            self.assertTrue(result["committed"])
            self.assertTrue(result["writes_files"])
            self.assertEqual(git(root, "rev-list", "--count", "--all"), "2")
            self.assertEqual(git(root, "rev-parse", "HEAD"), result["commit_oid"])
            self.assertIn("post-commit inspection failed", result["error"])

    def test_backup_apply_reports_post_stage_guard_exception_truthfully(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            preflight = backup_module.build_staged_push_report(root, repo_root=root)

            with mock.patch.object(
                backup_module,
                "build_staged_push_report",
                side_effect=[preflight, backup_module.PushSizeGuardError("guard interrupted")],
            ):
                result = backup_module.apply_backup(root, root, "must not commit")

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "git_backup_failed")
            self.assertTrue(result["writes_files"])
            self.assertTrue(result["index_changed"])
            self.assertTrue(result["staged_files"])
            self.assertIn("guard interrupted", result["error"])
            self.assertEqual(git(root, "rev-list", "--count", "--all"), "1")

    def test_backup_apply_rejects_symlink_target_before_staging(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            git(root, "init", "-b", "main")
            git(root, "config", "user.email", "codex@example.invalid")
            git(root, "config", "user.name", "Codex Test")
            create_backup_fixture(root)
            git(root, "add", "config/data_sources/push_size_guard.json")
            git(root, "commit", "-m", "fixture contract")
            shutil.rmtree(root / "data" / "derived")
            sensitive = root / "sensitive"
            sensitive.mkdir()
            (sensitive / "private.txt").write_text("must stay outside backup scope\n", encoding="utf-8")
            (root / "data" / "derived").symlink_to("../sensitive", target_is_directory=True)

            result = run_json(
                [
                    sys.executable,
                    str(GITHUB_BACKUP_SCRIPT),
                    "--database-dir",
                    str(root),
                    "--apply",
                ],
                expect_success=False,
            )

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "unsafe_backup_target")
            self.assertFalse(result["writes_files"])
            self.assertFalse(result["index_changed"])
            self.assertEqual(git(root, "diff", "--cached", "--name-only"), "")
            self.assertNotIn("sensitive/private.txt", git(root, "ls-files"))

    def test_backup_apply_fails_closed_outside_git_worktree_with_chinese_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            create_backup_fixture(root)
            result = run_json([
                sys.executable,
                str(GITHUB_BACKUP_SCRIPT),
                "--database-dir",
                str(root),
                "--apply",
            ], expect_success=False)

            self.assertEqual(result["status"], "FAIL")
            self.assertEqual(result["reason"], "not_git_worktree")
            self.assertFalse(result["writes_files"])
            self.assertFalse(result["remote_push"])
            self.assertIn("中文原因", result)
            self.assertIn("fallback建议", result)

    def test_installed_source_copy_supports_only_no_write_backup_scope_check(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            root = Path(tmpdir)
            create_backup_fixture(root)
            (root / "memory_atlas_source_workspace.json").write_text(
                json.dumps(
                    {
                        "schema_version": "memory_atlas_source_workspace.v1",
                        "original_repo_root": "/temporary/canonical/repo",
                        "installed_git_commit": "fixture",
                    }
                )
                + "\n",
                encoding="utf-8",
            )
            dry_run_result = run_json(
                [sys.executable, str(GITHUB_BACKUP_SCRIPT), "--database-dir", str(root), "--dry-run"]
            )
            self.assertEqual(dry_run_result["status"], "PASS")
            self.assertEqual(dry_run_result["backup_scope_check"], "installed_source_copy_no_git")
            self.assertTrue(dry_run_result["dry_run"])
            self.assertFalse(dry_run_result["writes_files"])
            self.assertFalse(dry_run_result["remote_push"])
            self.assertFalse(dry_run_result["github_main_upload"])
            self.assertEqual(dry_run_result["changed_files"], [])

            apply_result = run_json(
                [sys.executable, str(GITHUB_BACKUP_SCRIPT), "--database-dir", str(root), "--apply"],
                expect_success=False,
            )
            self.assertEqual(apply_result["status"], "FAIL")
            self.assertEqual(apply_result["reason"], "not_git_worktree")


if __name__ == "__main__":
    unittest.main()
