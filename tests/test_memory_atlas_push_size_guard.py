from __future__ import annotations

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
ATLASCTL = SCRIPTS / "atlasctl.py"
CONTRACT_PATH = ROOT / "config/data_sources/push_size_guard.json"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from memory_atlas_cli import push_size_guard as guard  # noqa: E402


def git(repo: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *arguments],
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(f"git {' '.join(arguments)} failed\nstdout={result.stdout}\nstderr={result.stderr}")
    return result.stdout.strip()


def write_contract(repo: Path) -> None:
    path = repo / "config/data_sources/push_size_guard.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(CONTRACT_PATH.read_bytes())


def init_repo(repo: Path, *, branch: str = "main") -> str:
    git(repo, "init", "-b", branch)
    git(repo, "config", "user.email", "codex@example.invalid")
    git(repo, "config", "user.name", "Codex Test")
    write_contract(repo)
    tracked = repo / "tracked.txt"
    tracked.write_text("base\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "base")
    base = git(repo, "rev-parse", "HEAD")
    git(repo, "update-ref", "refs/remotes/origin/main", base)
    return base


def run_json(command: list[str], *, cwd: Path = ROOT, expect_success: bool = True) -> dict:
    result = subprocess.run(command, cwd=cwd, text=True, capture_output=True, check=False)
    if expect_success and result.returncode != 0:
        raise AssertionError(f"command failed: {command}\nstdout={result.stdout}\nstderr={result.stderr}")
    if not expect_success and result.returncode == 0:
        raise AssertionError(f"command unexpectedly passed: {command}\nstdout={result.stdout}")
    lines = result.stdout.splitlines()
    starts = [index for index, line in enumerate(lines) if line == "{"]
    if not starts:
        raise AssertionError(f"command did not emit a JSON object: {command}\nstdout={result.stdout}")
    return json.loads("\n".join(lines[starts[-1] :]))


class MemoryAtlasPushSizeGuardTest(unittest.TestCase):
    def setUp(self) -> None:
        self.contract = guard.load_push_size_contract(ROOT)

    def test_canonical_contract_fixes_taskpack_limits_and_no_write_boundaries(self) -> None:
        self.assertEqual(self.contract["task_id"], "S06-P3-T2")
        self.assertEqual(self.contract["limits"]["recommended_chunk_bytes"], 45 * 1024 * 1024)
        self.assertEqual(self.contract["limits"]["split_required_above_bytes"], 50 * 1024 * 1024)
        self.assertEqual(
            self.contract["limits"]["ordinary_blob_hard_stop_at_or_above_bytes"],
            100 * 1024 * 1024,
        )
        self.assertEqual(self.contract["limits"]["max_single_push_target_bytes"], 1536 * 1024 * 1024)
        self.assertEqual(self.contract["limits"]["single_push_comparison"], "strictly_less_than")
        self.assertFalse(self.contract["direct_main"]["force"])
        self.assertFalse(self.contract["direct_main"]["git_lfs"])
        self.assertFalse(self.contract["direct_main"]["replace_refs"])
        self.assertFalse(self.contract["direct_main"]["lazy_fetch"])
        self.assertFalse(self.contract["direct_main"]["hooks"])
        self.assertFalse(self.contract["boundaries"]["remote_push"])
        self.assertEqual(self.contract["boundaries"]["raw_fixture_contract_task"], "S06-P3-T3")

    def test_contract_drift_fails_closed(self) -> None:
        payload = copy.deepcopy(self.contract)
        payload["limits"]["max_single_push_target_bytes"] += 1
        with self.assertRaisesRegex(guard.PushSizeGuardError, "drifted"):
            guard.validate_push_size_contract(payload)

    def test_blob_thresholds_are_exact_and_do_not_echo_content(self) -> None:
        entries = [
            {"path": "fifty.bin", "oid": "a" * 40},
            {"path": "split.bin", "oid": "b" * 40},
            {"path": "hard.bin", "oid": "c" * 40},
        ]
        object_info = {
            "a" * 40: {"type": "blob", "bytes": 50 * 1024 * 1024},
            "b" * 40: {"type": "blob", "bytes": 50 * 1024 * 1024 + 1},
            "c" * 40: {"type": "blob", "bytes": 100 * 1024 * 1024},
        }

        violations = guard.evaluate_staged_blob_limits(entries, object_info, self.contract["limits"])

        self.assertEqual(
            [(row["path"], row["reason"]) for row in violations],
            [
                ("split.bin", "split_required_above_50_mib"),
                ("hard.bin", "ordinary_blob_hard_stop"),
            ],
        )
        self.assertNotIn("content", json.dumps(violations))

    def test_staged_atomic_units_keep_archives_and_public_sources_together(self) -> None:
        entries = [
            {"path": "OpenAIDatabase/data/raw_archives/chatgpt/export-1/manifest.json", "oid": "a" * 40},
            {"path": "OpenAIDatabase/data/raw_archives/chatgpt/export-1/parts/part-1", "oid": "b" * 40},
            {"path": "OpenAIDatabase/data/public_raw/agents/reviewer/item.json", "oid": "c" * 40},
            {"path": "OpenAIDatabase/data/public_raw/agents/reviewer/other.json", "oid": "d" * 40},
            {"path": "OpenAIDatabase/docs/review.md", "oid": "e" * 40},
        ]
        object_info = {
            entry["oid"]: {"type": "blob", "bytes": 1}
            for entry in entries
        }

        plan = guard.plan_staged_batches(
            entries,
            object_info,
            database_prefix="OpenAIDatabase",
            contract=self.contract,
        )

        self.assertEqual(plan["batch_count"], 1)
        units = plan["batches"][0]["unit_ids"]
        self.assertEqual(
            units,
            [
                "OpenAIDatabase/data/public_raw/agents/reviewer",
                "OpenAIDatabase/data/raw_archives/chatgpt/export-1",
                "OpenAIDatabase/docs/review.md",
            ],
        )

    def test_staged_planner_splits_deterministically_below_strict_limit(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["limits"]["max_single_push_target_bytes"] = 100
        contract["estimation"]["protocol_reserve_bytes_per_batch"] = 10
        contract["estimation"]["protocol_reserve_bytes_per_object"] = 0
        entries = [
            {"path": f"file-{index}.bin", "oid": f"{index + 1:040x}"}
            for index in range(3)
        ]
        object_info = {
            entry["oid"]: {"type": "blob", "bytes": 40}
            for entry in entries
        }

        first = guard.plan_staged_batches(entries, object_info, database_prefix="", contract=contract)
        second = guard.plan_staged_batches(entries, object_info, database_prefix="", contract=contract)

        self.assertEqual(first, second)
        self.assertTrue(first["batch_required"])
        self.assertEqual(first["batch_count"], 2)
        self.assertTrue(all(row["estimated_push_upper_bound_bytes"] < 100 for row in first["batches"]))

    def test_staged_planner_rejects_unsplittable_atomic_recovery_unit(self) -> None:
        contract = copy.deepcopy(self.contract)
        contract["limits"]["max_single_push_target_bytes"] = 100
        contract["estimation"]["protocol_reserve_bytes_per_batch"] = 10
        contract["estimation"]["protocol_reserve_bytes_per_object"] = 0
        entries = [
            {"path": "data/raw_archives/chatgpt/export-1/manifest.json", "oid": "a" * 40},
            {"path": "data/raw_archives/chatgpt/export-1/parts/part-1", "oid": "b" * 40},
        ]
        object_info = {
            "a" * 40: {"type": "blob", "bytes": 50},
            "b" * 40: {"type": "blob", "bytes": 50},
        }

        plan = guard.plan_staged_batches(entries, object_info, database_prefix="", contract=contract)

        self.assertEqual(plan["batches"], [])
        self.assertEqual(plan["oversized_atomic_units"][0]["unit_id"], "data/raw_archives/chatgpt/export-1")

    def test_real_staged_index_is_sized_without_mutation(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            candidate = repo / "candidate.txt"
            candidate.write_text("candidate\n", encoding="utf-8")
            git(repo, "mv", "tracked.txt", "renamed.txt")
            git(repo, "add", "candidate.txt", "renamed.txt")
            before = git(repo, "diff", "--cached", "--name-only")

            report = guard.build_staged_push_report(repo)

            self.assertEqual(report["status"], "PASS")
            self.assertEqual(report["plan"]["entry_count"], 3)
            self.assertEqual(report["plan"]["batch_count"], 1)
            self.assertTrue(report["single_commit_ready"])
            self.assertFalse(report["staged_file_content_read"])
            self.assertFalse(report["index_mutation"])
            self.assertEqual(git(repo, "diff", "--cached", "--name-only"), before)

    def test_staged_guard_rejects_non_main_branch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo, branch="feature")
            (repo / "candidate.txt").write_text("candidate\n", encoding="utf-8")
            git(repo, "add", "candidate.txt")

            report = guard.build_staged_push_report(repo)

            self.assertEqual(report["status"], "FAIL")
            self.assertEqual(report["reason"], "branch_is_not_main")

    def test_pending_commit_batches_are_commit_bounded_and_resumable(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            base = init_repo(repo)
            for index in range(4):
                (repo / f"payload-{index}.bin").write_bytes(bytes([65 + index]) * 4096)
                git(repo, "add", f"payload-{index}.bin")
                git(repo, "commit", "-m", f"payload {index}")
            head = git(repo, "rev-parse", "HEAD")

            plan = guard.plan_pending_commit_batches(
                repo,
                base,
                head,
                max_bytes=7000,
                reserve_bytes=128,
            )

            self.assertGreater(plan["batch_count"], 1)
            self.assertFalse(plan["oversized_commits"])
            self.assertTrue(all(row["estimated_push_upper_bound_bytes"] < 7000 for row in plan["batches"]))
            self.assertTrue(all("--force" not in row["push_argv"] for row in plan["batches"]))
            first_tip = plan["batches"][0]["tip_commit"]
            git(repo, "update-ref", "refs/remotes/origin/main", first_tip)

            resumed = guard.plan_pending_commit_batches(
                repo,
                first_tip,
                head,
                max_bytes=7000,
                reserve_bytes=128,
            )

            self.assertLess(resumed["pending_commit_count"], plan["pending_commit_count"])
            self.assertEqual(resumed["remote_checkpoint_oid"], first_tip)
            self.assertNotEqual(resumed["plan_id"], plan["plan_id"])

    def test_pending_merge_batches_use_only_fast_forward_boundaries(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            base = init_repo(repo)
            git(repo, "switch", "-c", "side")
            (repo / "side.bin").write_bytes(b"s" * 4096)
            git(repo, "add", "side.bin")
            git(repo, "commit", "-m", "side")
            side_tip = git(repo, "rev-parse", "HEAD")
            git(repo, "switch", "main")
            (repo / "main.bin").write_bytes(b"m" * 4096)
            git(repo, "add", "main.bin")
            git(repo, "commit", "-m", "main")
            main_tip = git(repo, "rev-parse", "HEAD")
            git(repo, "merge", "--no-ff", "side", "-m", "merge side")
            head = git(repo, "rev-parse", "HEAD")

            plan = guard.plan_pending_commit_batches(
                repo,
                base,
                head,
                max_bytes=1024 * 1024,
                reserve_bytes=128,
            )

            self.assertEqual(plan["pending_commit_count"], 3)
            self.assertEqual(plan["pending_boundary_count"], 2)
            self.assertEqual(plan["batches"][0]["first_commit"], main_tip)
            self.assertEqual(plan["batches"][0]["tip_commit"], head)
            self.assertNotIn(side_tip, [row["tip_commit"] for row in plan["batches"]])
            previous = base
            for batch in plan["batches"]:
                self.assertEqual(git(repo, "merge-base", "--is-ancestor", previous, batch["tip_commit"]), "")
                previous = batch["tip_commit"]

            side_checkpoint_plan = guard.plan_pending_commit_batches(
                repo,
                side_tip,
                head,
                max_bytes=1024 * 1024,
                reserve_bytes=128,
            )
            self.assertEqual(side_checkpoint_plan["pending_boundary_count"], 1)
            self.assertEqual(side_checkpoint_plan["batches"][0]["tip_commit"], head)

    def test_pending_planner_rejects_one_oversized_commit(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            base = init_repo(repo)
            (repo / "payload.bin").write_bytes(b"x" * 4096)
            git(repo, "add", "payload.bin")
            git(repo, "commit", "-m", "payload")
            head = git(repo, "rev-parse", "HEAD")

            plan = guard.plan_pending_commit_batches(
                repo,
                base,
                head,
                max_bytes=100,
                reserve_bytes=10,
            )

            self.assertEqual(plan["batches"], [])
            self.assertEqual(plan["oversized_commits"][0]["commit_oid"], head)

    def test_pending_planner_rejects_blob_threshold_violations(self) -> None:
        commit_oid = "a" * 40
        blob_oid = "b" * 40
        units = [{"commit_oid": commit_oid, "object_ids": (blob_oid,)}]
        cases = [
            (50 * 1024 * 1024, None),
            (50 * 1024 * 1024 + 1, "split_required_above_50_mib"),
            (100 * 1024 * 1024, "ordinary_blob_hard_stop"),
        ]
        for blob_bytes, reason in cases:
            with self.subTest(blob_bytes=blob_bytes):
                with (
                    mock.patch.object(guard, "_pending_commit_units", return_value=units),
                    mock.patch.object(guard, "_rev_list_oids", return_value=[commit_oid]),
                    mock.patch.object(
                        guard,
                        "_object_info",
                        return_value={
                            blob_oid: {"oid": blob_oid, "type": "blob", "bytes": blob_bytes}
                        },
                    ),
                ):
                    plan = guard.plan_pending_commit_batches(
                        Path("/unused"),
                        "c" * 40,
                        commit_oid,
                        max_bytes=1536 * 1024 * 1024,
                        reserve_bytes=8 * 1024 * 1024,
                    )

                if reason is None:
                    self.assertEqual(plan["blob_violations"], [])
                    self.assertEqual(plan["batch_count"], 1)
                else:
                    self.assertEqual(plan["batches"], [])
                    self.assertEqual(plan["blob_violations"][0]["reason"], reason)

    def test_partial_clone_missing_object_fails_without_lazy_fetch(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            origin = root / "origin.git"
            clone = root / "clone"
            source.mkdir()
            origin.mkdir()
            base = init_repo(source)
            (source / "pending.bin").write_bytes(b"pending object\n")
            git(source, "add", "pending.bin")
            git(source, "commit", "-m", "pending")
            head = git(source, "rev-parse", "HEAD")
            git(origin, "init", "--bare")
            git(origin, "config", "uploadpack.allowFilter", "true")
            git(source, "remote", "add", "test-origin", origin.as_uri())
            git(source, "push", "test-origin", "main")
            git(origin, "symbolic-ref", "HEAD", "refs/heads/main")
            git(root, "clone", "--filter=blob:none", "--no-checkout", origin.as_uri(), str(clone))
            git(clone, "update-ref", "refs/remotes/origin/main", base)

            no_lazy_fetch_environment = os.environ.copy()
            no_lazy_fetch_environment["GIT_NO_LAZY_FETCH"] = "1"
            missing = subprocess.run(
                ["git", "--no-replace-objects", "-C", str(clone), "cat-file", "-e", f"{head}:pending.bin"],
                text=True,
                capture_output=True,
                env=no_lazy_fetch_environment,
                check=False,
            )
            self.assertNotEqual(missing.returncode, 0)

            trace_path = root / "guard-trace.jsonl"
            with mock.patch.dict(os.environ, {"GIT_TRACE2_EVENT": str(trace_path)}):
                with self.assertRaises(guard.PushSizeGuardError):
                    guard.plan_pending_commit_batches(
                        clone,
                        base,
                        head,
                        max_bytes=1536 * 1024 * 1024,
                        reserve_bytes=8 * 1024 * 1024,
                    )

            trace_events = [
                json.loads(line)
                for line in trace_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            child_argv = [
                event.get("argv", [])
                for event in trace_events
                if event.get("event") == "child_start"
            ]
            self.assertFalse(any("fetch" in argument for argv in child_argv for argument in argv))

    def test_pending_guard_fails_on_checkpoint_change_and_divergence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            (repo / "local.txt").write_text("local\n", encoding="utf-8")
            git(repo, "add", "local.txt")
            git(repo, "commit", "-m", "local")

            changed = guard.build_pending_push_report(repo, expected_remote_oid="0" * 40)
            self.assertEqual(changed["status"], "FAIL")
            self.assertEqual(changed["reason"], "remote_checkpoint_changed")

            tree = git(repo, "rev-parse", "HEAD^{tree}")
            unrelated = git(repo, "commit-tree", tree, "-m", "unrelated remote")
            git(repo, "update-ref", "refs/remotes/origin/main", unrelated)
            diverged = guard.build_pending_push_report(repo)
            self.assertEqual(diverged["status"], "FAIL")
            self.assertEqual(diverged["reason"], "remote_history_diverged")
            self.assertIsNone(diverged["plan"])
            self.assertFalse(diverged["remote_push"])

    def test_pending_audit_outputs_plan_without_fetch_or_push(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary)
            init_repo(repo)
            (repo / "local.txt").write_text("local\n", encoding="utf-8")
            git(repo, "add", "local.txt")
            git(repo, "commit", "-m", "local")

            result = guard.audit_push_size(repo, scope="pending")

            self.assertEqual(result["status"], "PASS")
            self.assertEqual(result["pending"]["remote_relation"], "ahead")
            self.assertEqual(result["pending"]["plan"]["pending_commit_count"], 1)
            self.assertFalse(result["pending"]["fetch_performed"])
            self.assertFalse(result["safety"]["remote_push"])
            self.assertFalse(result["safety"]["force_push"])

    def test_atlasctl_staged_audit_is_machine_readable_and_local_only(self) -> None:
        result = run_json([
            sys.executable,
            str(ATLASCTL),
            "audit",
            "--check",
            "push-size",
            "--push-scope",
            "staged",
        ])

        self.assertEqual(result["status"], "PASS")
        self.assertEqual(result["task_id"], "S06-P3-T2")
        self.assertEqual(result["scope"], "staged")
        self.assertFalse(result["safety"]["index_mutation"])
        self.assertFalse(result["safety"]["remote_fetch"])
        self.assertFalse(result["safety"]["remote_push"])


if __name__ == "__main__":
    unittest.main()
