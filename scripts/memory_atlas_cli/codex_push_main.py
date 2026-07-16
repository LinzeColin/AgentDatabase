"""Fail-closed Codex sync to one ordinary GitHub main push for S07-P3-T1."""

from __future__ import annotations

import argparse
import json
import os
import re
import stat
from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any

from github_backup import create_bound_commit, find_git_root, run_git, write_index_tree
from memory_atlas_validator_profiles import (
    load_validator_profile_config,
    run_validator_profile,
)

from .codex_atlas import publish_codex_atlas
from .codex_derived import build_codex_derived
from .codex_legacy_summary import migrate_codex_legacy_summary
from .codex_source_discovery import build_codex_source_discovery
from .codex_sync_state import sync_codex_public_raw_incremental
from .push_size_guard import build_staged_push_report


CONTRACT_PATH = Path("config/data_sources/codex_push_main.json")
SCHEMA_VERSION = "memory_atlas.codex_push_main_contract.v1_2_1_s07_p3_t1"
RESULT_SCHEMA_VERSION = "memory_atlas.codex_push_main_result.v1_2_1_s07_p3_t1"
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_push_main.v1_2_1_s07_p3_t1.json"
)
TASK_ID = "S07-P3-T1"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P3-T1"
REMOTE = "origin"
BRANCH = "main"
REMOTE_REF = "refs/heads/main"
VALIDATION_PROFILE = "sync"
MAX_CONTRACT_BYTES = 64 * 1024
MAX_COMMIT_MESSAGE_CHARS = 240
OID_PATTERN = re.compile(r"^[0-9a-f]{40}(?:[0-9a-f]{24})?$")
ARCHIVE_ID_PATTERN = re.compile(r"^[a-z0-9](?:[a-z0-9._-]{0,126}[a-z0-9])?$")

APPEND_ONLY_PREFIXES = (
    "data/raw_archives/codex/",
    "data/public_raw/codex/",
)
MUTABLE_PREFIXES = (
    "data/derived/codex/",
    "data/derived/weekly/",
    "data/processed/codex/",
)
MUTABLE_EXACT_PATHS = (
    "data/derived/agent_context/AGENT_CONTEXT.md",
    "data/derived/agent_context/agent_context_pack.json",
    "data/derived/visualization/memory_atlas.json",
    "data/sync_state/codex.json",
    "data/sync_state/codex_atlas.json",
    "data/sync_state/codex_legacy_summary.json",
)
RAW_LEDGER_PATH = "机器治理/证据与日志/raw_archive_manifests/raw_hash_ledger.jsonl"
RAW_MANIFEST_PREFIX = (
    "机器治理/证据与日志/raw_archive_manifests/"
    "raw_manifest.s07_p1_t3_"
)

EXPECTED_CONTRACT: dict[str, Any] = {
    "schema_version": SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "command": "sync codex --push-main",
    "pipeline": [
        "sync_incremental_raw",
        "build_codex_derived",
        "publish_codex_atlas",
        "migrate_legacy_summary_truth",
        "stage_exact_codex_outputs",
        "validate_sync_profile",
        "validate_push_size",
        "commit_audited_tree",
        "push_origin_main_once",
        "verify_remote_main",
    ],
    "git": {
        "required_branch": BRANCH,
        "remote": REMOTE,
        "remote_ref": REMOTE_REF,
        "require_clean_initial_worktree": True,
        "require_head_equals_tracking_main": True,
        "require_head_equals_remote_main": True,
        "remote_race_stop": True,
        "push_attempt_limit": 1,
        "force": False,
        "fetch": False,
        "branch_creation": False,
        "pull_request": False,
        "merge": False,
        "rebase": False,
        "history_rewrite": False,
    },
    "validation": {
        "profile": VALIDATION_PROFILE,
        "credential_scan_required": True,
        "push_size_guard_required": True,
        "source_hash_stat_equal_required": True,
        "index_tree_stable_required": True,
    },
    "write_scope": {
        "append_only_prefixes": list(APPEND_ONLY_PREFIXES),
        "mutable_prefixes": list(MUTABLE_PREFIXES),
        "mutable_exact_paths": list(MUTABLE_EXACT_PATHS),
        "raw_ledger_path": RAW_LEDGER_PATH,
        "raw_manifest_prefix": RAW_MANIFEST_PREFIX,
    },
    "failure_policy": {
        "stop_before_push": True,
        "preserve_append_only_raw": True,
        "preserve_failed_local_commit": True,
        "automatic_cleanup": False,
        "automatic_retry_push": False,
    },
    "phase_boundary": {
        "scheduler_not_implemented": True,
        "full_restore_proof_not_claimed": True,
        "next_task": "S07-P3-T2",
    },
}


class CodexPushMainError(RuntimeError):
    """A path-free failure code for one fail-closed pipeline gate."""

    def __init__(self, code: str, *, path: str | None = None):
        super().__init__(code)
        self.code = code
        self.path = path


PipelineRunner = Callable[[Path, str, Path | None], dict[str, Any]]
ValidationRunner = Callable[[Path, Path], dict[str, Any]]
SourceProbe = Callable[[Path, Path | None], dict[str, Any]]
PushGuard = Callable[[Path, Path], dict[str, Any]]


def _read_regular_json(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise CodexPushMainError("push_main_contract_unreadable") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > MAX_CONTRACT_BYTES:
            raise CodexPushMainError("push_main_contract_not_bounded_regular_file")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            payload = handle.read(MAX_CONTRACT_BYTES + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(payload) > MAX_CONTRACT_BYTES:
        raise CodexPushMainError("push_main_contract_too_large")
    try:
        value = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexPushMainError("push_main_contract_invalid_json") from exc
    if not isinstance(value, dict):
        raise CodexPushMainError("push_main_contract_not_object")
    return value


def validate_codex_push_main_contract(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise CodexPushMainError("push_main_contract_drift")
    return dict(payload)


def load_codex_push_main_contract(database_dir: Path) -> dict[str, Any]:
    return validate_codex_push_main_contract(
        _read_regular_json(database_dir.resolve() / CONTRACT_PATH)
    )


def _validate_oid(value: str, code: str) -> str:
    value = value.strip()
    if not OID_PATTERN.fullmatch(value):
        raise CodexPushMainError(code)
    return value


def _safe_repo_path(value: str) -> str:
    if not value or any(ord(character) < 32 for character in value):
        raise CodexPushMainError("git_path_invalid")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CodexPushMainError("git_path_invalid")
    return path.as_posix()


def _git(repo_root: Path, arguments: list[str], *, check: bool = True):
    try:
        return run_git(repo_root, arguments, check=check)
    except (OSError, RuntimeError) as exc:
        raise CodexPushMainError("git_command_failed") from exc


def _current_branch(repo_root: Path) -> str:
    result = _git(repo_root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    if result.returncode != 0:
        return "DETACHED"
    return result.stdout.strip()


def _ref_oid(repo_root: Path, ref: str, code: str) -> str:
    result = _git(repo_root, ["rev-parse", "--verify", ref], check=False)
    if result.returncode != 0:
        raise CodexPushMainError(code)
    return _validate_oid(result.stdout, code)


def _remote_push_url_count(repo_root: Path) -> int:
    result = _git(
        repo_root,
        ["remote", "get-url", "--all", "--push", REMOTE],
        check=False,
    )
    if result.returncode != 0:
        raise CodexPushMainError("origin_push_url_missing")
    return len([line for line in result.stdout.splitlines() if line.strip()])


def _remote_main_oid(repo_root: Path) -> str:
    result = _git(
        repo_root,
        ["ls-remote", "--exit-code", REMOTE, REMOTE_REF],
        check=False,
    )
    if result.returncode != 0:
        raise CodexPushMainError("remote_main_probe_failed")
    rows = [line.split("\t", 1) for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != 1 or len(rows[0]) != 2 or rows[0][1] != REMOTE_REF:
        raise CodexPushMainError("remote_main_probe_ambiguous")
    return _validate_oid(rows[0][0], "remote_main_oid_invalid")


def _status_entries(repo_root: Path) -> list[dict[str, str]]:
    result = _git(
        repo_root,
        ["status", "--porcelain=v1", "-z", "--untracked-files=all"],
    )
    tokens = result.stdout.split("\0")
    entries: list[dict[str, str]] = []
    index = 0
    while index < len(tokens):
        token = tokens[index]
        index += 1
        if not token:
            continue
        if len(token) < 4 or token[2] != " ":
            raise CodexPushMainError("git_status_invalid")
        status_code = token[:2]
        path = _safe_repo_path(token[3:])
        entry = {"status": status_code, "path": path}
        if "R" in status_code or "C" in status_code:
            if index >= len(tokens) or not tokens[index]:
                raise CodexPushMainError("git_status_rename_invalid")
            entry["original_path"] = _safe_repo_path(tokens[index])
            index += 1
        entries.append(entry)
    return entries


def _nul_paths(repo_root: Path, arguments: list[str]) -> list[str]:
    result = _git(repo_root, arguments)
    return sorted(_safe_repo_path(value) for value in result.stdout.split("\0") if value)


def _database_prefix(repo_root: Path, database_dir: Path) -> str:
    try:
        relative = database_dir.resolve().relative_to(repo_root.resolve()).as_posix()
    except ValueError as exc:
        raise CodexPushMainError("database_outside_worktree") from exc
    return "" if relative == "." else relative


def _database_relative_path(repo_path: str, database_prefix: str) -> str:
    if not database_prefix:
        return repo_path
    prefix = f"{database_prefix}/"
    if not repo_path.startswith(prefix):
        raise CodexPushMainError("change_outside_database", path=repo_path)
    return repo_path[len(prefix) :]


def _path_policy(database_relative: str) -> str | None:
    if any(database_relative.startswith(prefix) for prefix in APPEND_ONLY_PREFIXES):
        return "append_only"
    if database_relative.startswith(RAW_MANIFEST_PREFIX) and database_relative.endswith(".jsonl"):
        return "append_only"
    if database_relative == RAW_LEDGER_PATH:
        return "append_ledger"
    if any(database_relative.startswith(prefix) for prefix in MUTABLE_PREFIXES):
        return "mutable"
    if database_relative in MUTABLE_EXACT_PATHS:
        return "mutable"
    return None


def _validate_pipeline_changes(
    entries: list[dict[str, str]],
    database_prefix: str,
) -> list[str]:
    paths: list[str] = []
    for entry in entries:
        status_code = entry["status"]
        repo_path = entry["path"]
        if "R" in status_code or "C" in status_code or "U" in status_code:
            raise CodexPushMainError("unsupported_git_change", path=repo_path)
        if status_code[0] not in {" ", "?"}:
            raise CodexPushMainError("index_changed_during_pipeline", path=repo_path)
        relative = _database_relative_path(repo_path, database_prefix)
        policy = _path_policy(relative)
        if policy is None:
            raise CodexPushMainError("change_outside_codex_push_scope", path=repo_path)
        if policy == "append_only" and status_code != "??":
            raise CodexPushMainError("append_only_path_modified", path=repo_path)
        if policy == "append_ledger" and status_code not in {" M", "??"}:
            raise CodexPushMainError("raw_ledger_not_append_candidate", path=repo_path)
        if "D" in status_code and policy != "mutable":
            raise CodexPushMainError("immutable_path_deleted", path=repo_path)
        paths.append(repo_path)
    if len(paths) != len(set(paths)):
        raise CodexPushMainError("duplicate_git_change_path")
    return sorted(paths)


def _validate_staged_modes(repo_root: Path, paths: list[str]) -> None:
    result = _git(repo_root, ["ls-files", "--stage", "-z", "--", *paths])
    for record in (value for value in result.stdout.split("\0") if value):
        try:
            metadata, path = record.split("\t", 1)
            mode, oid, stage_number = metadata.split(" ")
        except ValueError as exc:
            raise CodexPushMainError("staged_entry_invalid") from exc
        _safe_repo_path(path)
        _validate_oid(oid, "staged_oid_invalid")
        if mode not in {"100644", "100755"} or stage_number != "0":
            raise CodexPushMainError("staged_entry_not_regular", path=path)


def _stage_exact_changes(repo_root: Path, paths: list[str]) -> str:
    _git(repo_root, ["add", "-A", "--", *paths])
    staged = _nul_paths(
        repo_root,
        [
            "diff",
            "--cached",
            "--name-only",
            "-z",
            "--no-ext-diff",
            "--no-textconv",
            "--no-renames",
        ],
    )
    if staged != paths:
        raise CodexPushMainError("staged_scope_mismatch")
    status = _status_entries(repo_root)
    if sorted(entry["path"] for entry in status) != paths:
        raise CodexPushMainError("worktree_scope_changed_while_staging")
    if any(entry["status"] == "??" or entry["status"][1] != " " for entry in status):
        raise CodexPushMainError("unstaged_changes_after_staging")
    _validate_staged_modes(repo_root, paths)
    try:
        return write_index_tree(repo_root)
    except (OSError, RuntimeError) as exc:
        raise CodexPushMainError("index_tree_unreadable") from exc


def _assert_staged_snapshot(repo_root: Path, paths: list[str], tree_oid: str) -> None:
    if write_index_tree(repo_root) != tree_oid:
        raise CodexPushMainError("index_changed_during_validation")
    status = _status_entries(repo_root)
    if sorted(entry["path"] for entry in status) != paths:
        raise CodexPushMainError("worktree_changed_during_validation")
    if any(entry["status"] == "??" or entry["status"][1] != " " for entry in status):
        raise CodexPushMainError("unstaged_change_during_validation")


def _source_probe(database_dir: Path, codex_home: Path | None) -> dict[str, Any]:
    result = build_codex_source_discovery(
        database_dir,
        operator_codex_home=codex_home,
    )
    return {
        "source_metadata_sha256": result["source_metadata_sha256"],
        "eligible_file_count": result["eligible_file_count"],
        "eligible_total_bytes": result["eligible_total_bytes"],
    }


def _run_pipeline(
    database_dir: Path,
    archive_id: str,
    codex_home: Path | None,
) -> dict[str, Any]:
    sync_result = sync_codex_public_raw_incremental(
        database_dir,
        archive_id,
        operator_codex_home=codex_home,
    )
    derived_result = build_codex_derived(database_dir)
    atlas_result = publish_codex_atlas(database_dir)
    legacy_result = migrate_codex_legacy_summary(database_dir)
    steps = {
        "sync_incremental_raw": sync_result,
        "build_codex_derived": derived_result,
        "publish_codex_atlas": atlas_result,
        "migrate_legacy_summary_truth": legacy_result,
    }
    for step_id, result in steps.items():
        if result.get("status") != "PASS":
            raise CodexPushMainError(f"{step_id}_failed")
        if result.get("source_mutation") is True or result.get("raw_mutation") is True:
            raise CodexPushMainError(f"{step_id}_mutation_detected")
        if result.get("remote_push") is not False:
            raise CodexPushMainError(f"{step_id}_unexpected_remote_push")
    if sync_result.get("archive_created") and sync_result.get("source_hash_stat_equal") is not True:
        raise CodexPushMainError("sync_source_hash_stat_not_equal")
    return {
        "status": "PASS",
        "writes_files": any(bool(result.get("writes_files")) for result in steps.values()),
        "steps": {
            step_id: {
                "status": result.get("status"),
                "outcome": result.get("outcome", "PASS"),
                "writes_files": bool(result.get("writes_files")),
            }
            for step_id, result in steps.items()
        },
    }


def _run_validation(database_dir: Path, repo_root: Path) -> dict[str, Any]:
    del repo_root
    config = load_validator_profile_config(database_dir)
    return run_validator_profile(config, VALIDATION_PROFILE, database_dir)


def _run_push_guard(database_dir: Path, repo_root: Path) -> dict[str, Any]:
    return build_staged_push_report(database_dir, repo_root=repo_root)


def _preflight(repo_root: Path) -> dict[str, str]:
    branch = _current_branch(repo_root)
    if branch != BRANCH:
        raise CodexPushMainError("branch_is_not_main")
    if _status_entries(repo_root):
        raise CodexPushMainError("initial_worktree_not_clean")
    head_oid = _ref_oid(repo_root, "HEAD", "head_oid_missing")
    tracking_oid = _ref_oid(
        repo_root,
        f"refs/remotes/{REMOTE}/{BRANCH}",
        "tracking_main_missing",
    )
    if tracking_oid != head_oid:
        raise CodexPushMainError("tracking_main_not_at_head")
    if _remote_push_url_count(repo_root) != 1:
        raise CodexPushMainError("origin_push_url_not_unique")
    remote_oid = _remote_main_oid(repo_root)
    if remote_oid != head_oid:
        raise CodexPushMainError("remote_main_not_at_head")
    return {
        "branch": branch,
        "head_oid": head_oid,
        "tracking_oid": tracking_oid,
        "remote_oid": remote_oid,
    }


def _assert_precommit_git_state(
    repo_root: Path,
    baseline_oid: str,
    paths: list[str],
    tree_oid: str,
) -> None:
    _assert_base_unchanged(repo_root, baseline_oid)
    _assert_staged_snapshot(repo_root, paths, tree_oid)


def _assert_base_unchanged(repo_root: Path, baseline_oid: str) -> None:
    if _current_branch(repo_root) != BRANCH:
        raise CodexPushMainError("branch_changed_during_run")
    if _ref_oid(repo_root, "HEAD", "head_oid_missing") != baseline_oid:
        raise CodexPushMainError("head_changed_during_run")
    if _ref_oid(
        repo_root,
        f"refs/remotes/{REMOTE}/{BRANCH}",
        "tracking_main_missing",
    ) != baseline_oid:
        raise CodexPushMainError("tracking_main_changed_during_run")
    if _remote_main_oid(repo_root) != baseline_oid:
        raise CodexPushMainError("remote_main_changed_during_run")


def _base_result(archive_id: str, dry_run: bool) -> dict[str, Any]:
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "command": "sync codex --push-main",
        "archive_id": archive_id,
        "status": "FAIL_CLOSED",
        "outcome": "NOT_STARTED",
        "dry_run": dry_run,
        "writes_files": False,
        "commit_created": False,
        "remote_push_attempted": False,
        "push_attempt_count": 0,
        "pushed": False,
        "remote_verified": False,
        "branch_created": False,
        "pull_request_created": False,
        "force_push": False,
        "fetch_executed": False,
        "merge_executed": False,
        "rebase_executed": False,
        "source_mutation": False,
        "raw_mutation": False,
        "next_task": "S07-P3-T2",
    }


def _failure(result: dict[str, Any], error: CodexPushMainError) -> dict[str, Any]:
    result.update(
        {
            "status": "FAIL_CLOSED",
            "outcome": "STOPPED",
            "reason": error.code,
            "recovery": (
                "Inspect the reported local Git state and preserve append-only raw. "
                "Do not retry push, force, merge, rebase, reset history, or delete raw evidence."
            ),
        }
    )
    if error.path is not None:
        result["rejected_path"] = error.path
    return result


def execute_codex_push_main(
    database_dir: Path,
    archive_id: str,
    *,
    codex_home: Path | None = None,
    message: str | None = None,
    dry_run: bool = False,
    pipeline_runner: PipelineRunner | None = None,
    validation_runner: ValidationRunner | None = None,
    source_probe: SourceProbe | None = None,
    push_guard: PushGuard | None = None,
) -> dict[str, Any]:
    result = _base_result(archive_id, dry_run)
    try:
        database_dir = database_dir.resolve()
        validate_codex_push_main_contract(load_codex_push_main_contract(database_dir))
        if not ARCHIVE_ID_PATTERN.fullmatch(archive_id):
            raise CodexPushMainError("archive_id_invalid")
        commit_message = message or f"chore(memory-atlas): sync Codex archive {archive_id}"
        if (
            not commit_message.strip()
            or len(commit_message) > MAX_COMMIT_MESSAGE_CHARS
            or any(ord(character) < 32 for character in commit_message)
        ):
            raise CodexPushMainError("commit_message_invalid")
        repo_root = find_git_root(database_dir)
        if repo_root is None:
            raise CodexPushMainError("not_git_worktree")
        database_prefix = _database_prefix(repo_root, database_dir)
        baseline = _preflight(repo_root)
        result.update(
            {
                "branch": baseline["branch"],
                "baseline_oid": baseline["head_oid"],
                "base_current": True,
                "initial_worktree_clean": True,
            }
        )
        probe = source_probe or _source_probe
        source_before = probe(database_dir, codex_home)
        result["source_before"] = source_before
        if dry_run:
            result.update(
                {
                    "status": "PASS",
                    "outcome": "DRY_RUN_READY",
                    "planned_pipeline": EXPECTED_CONTRACT["pipeline"],
                    "remote_verified": True,
                }
            )
            return result

        pipeline = pipeline_runner or _run_pipeline
        pipeline_result = pipeline(database_dir, archive_id, codex_home)
        if pipeline_result.get("status") != "PASS":
            raise CodexPushMainError("codex_sync_pipeline_failed")
        result["pipeline"] = pipeline_result
        result["writes_files"] = bool(pipeline_result.get("writes_files"))
        source_after_pipeline = probe(database_dir, codex_home)
        if source_after_pipeline != source_before:
            raise CodexPushMainError("codex_source_changed_during_pipeline")

        entries = _status_entries(repo_root)
        _assert_base_unchanged(repo_root, baseline["head_oid"])
        if not entries:
            result.update(
                {
                    "status": "PASS",
                    "outcome": "NO_CHANGES",
                    "writes_files": False,
                    "remote_verified": True,
                    "changed_paths": [],
                }
            )
            return result

        changed_paths = _validate_pipeline_changes(entries, database_prefix)
        result["changed_paths"] = changed_paths
        tree_oid = _stage_exact_changes(repo_root, changed_paths)
        result["audited_tree_oid"] = tree_oid
        validator = validation_runner or _run_validation
        validation = validator(database_dir, repo_root)
        result["validation"] = validation
        if (
            validation.get("status") != "PASS"
            or validation.get("failed_count") not in {None, 0}
            or validation.get("skipped_critical_count") not in {None, 0}
        ):
            raise CodexPushMainError("sync_validation_failed")
        _assert_staged_snapshot(repo_root, changed_paths, tree_oid)
        guard_runner = push_guard or _run_push_guard
        guard = guard_runner(database_dir, repo_root)
        result["push_size_guard"] = guard
        if guard.get("status") != "PASS" or guard.get("single_commit_ready") is not True:
            raise CodexPushMainError("push_size_guard_failed")
        _assert_staged_snapshot(repo_root, changed_paths, tree_oid)
        source_after_validation = probe(database_dir, codex_home)
        if source_after_validation != source_before:
            raise CodexPushMainError("codex_source_changed_during_validation")
        _assert_precommit_git_state(
            repo_root,
            baseline["head_oid"],
            changed_paths,
            tree_oid,
        )

        try:
            commit = create_bound_commit(
                repo_root,
                tree_oid=tree_oid,
                message=commit_message,
            )
        except (OSError, RuntimeError) as exc:
            raise CodexPushMainError("atomic_commit_failed") from exc
        result.update(
            {
                "commit_created": True,
                "commit_oid": commit["commit_oid"],
                "parent_oid": commit["parent_oid"],
                "commit_message": commit_message,
                "writes_files": True,
            }
        )
        if sorted(
            _nul_paths(
                repo_root,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", "-z", commit["commit_oid"]],
            )
        ) != changed_paths:
            raise CodexPushMainError("committed_scope_mismatch")
        if _status_entries(repo_root):
            raise CodexPushMainError("worktree_not_clean_after_commit")
        if _current_branch(repo_root) != BRANCH or _ref_oid(
            repo_root, "HEAD", "head_oid_missing"
        ) != commit["commit_oid"]:
            raise CodexPushMainError("head_not_at_created_commit")
        if probe(database_dir, codex_home) != source_before:
            raise CodexPushMainError("codex_source_changed_before_push")
        if _remote_main_oid(repo_root) != baseline["head_oid"]:
            raise CodexPushMainError("remote_main_changed_before_push")

        result["remote_push_attempted"] = True
        result["push_attempt_count"] = 1
        push = _git(
            repo_root,
            [
                "push",
                "--porcelain",
                REMOTE,
                f"{commit['commit_oid']}:{REMOTE_REF}",
            ],
            check=False,
        )
        try:
            remote_after = _remote_main_oid(repo_root)
        except CodexPushMainError:
            result["remote_state"] = "UNKNOWN"
            result["pushed"] = True if push.returncode == 0 else None
            raise CodexPushMainError("remote_verification_failed_after_push")
        result["remote_after_oid"] = remote_after
        if remote_after != commit["commit_oid"]:
            result["remote_state"] = (
                "UNCHANGED" if remote_after == baseline["head_oid"] else "COMPETING_CHANGE"
            )
            result["pushed"] = (
                False
                if remote_after == baseline["head_oid"]
                else (True if push.returncode == 0 else None)
            )
            reason = "push_rejected" if push.returncode != 0 else "remote_head_mismatch_after_push"
            raise CodexPushMainError(reason)
        result.update(
            {
                "status": "PASS",
                "outcome": "PUSHED_MAIN",
                "pushed": True,
                "remote_verified": True,
                "remote_state": "COMMIT_VERIFIED",
                "push_transport_returncode": push.returncode,
            }
        )
        return result
    except CodexPushMainError as exc:
        return _failure(result, exc)
    except Exception:
        return _failure(result, CodexPushMainError("unexpected_pipeline_failure"))


def generated_archive_id(clock: Callable[[], datetime] | None = None) -> str:
    now = (clock or (lambda: datetime.now(timezone.utc)))()
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return f"codex-incremental-{now.astimezone(timezone.utc).strftime('%Y%m%dt%H%M%Sz')}"


def run_codex_push_main(args: argparse.Namespace) -> int:
    archive_id = getattr(args, "archive_id", None) or generated_archive_id()
    incompatible = any(
        (
            getattr(args, "official_export", None),
            getattr(args, "input", None),
            getattr(args, "markdown_report", None),
            bool(getattr(args, "redact_for_public_backup", False)),
            bool(getattr(args, "public_transcripts", False)),
        )
    )
    if getattr(args, "source", None) != "codex" or incompatible:
        result = _failure(
            _base_result(archive_id, bool(getattr(args, "dry_run", False))),
            CodexPushMainError("push_main_requires_canonical_codex_source"),
        )
    else:
        result = execute_codex_push_main(
            Path(getattr(args, "database_dir", Path(__file__).resolve().parents[2])),
            archive_id,
            codex_home=getattr(args, "codex_home", None),
            message=getattr(args, "message", None),
            dry_run=bool(getattr(args, "dry_run", False)),
        )
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = (
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "EXPECTED_CONTRACT",
    "MODEL_PARAMETERS_PATH",
    "RESULT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "TASK_ID",
    "CodexPushMainError",
    "execute_codex_push_main",
    "generated_archive_id",
    "load_codex_push_main_contract",
    "run_codex_push_main",
    "validate_codex_push_main_contract",
)
