#!/usr/bin/env python3
"""Local Git backup control for Memory Atlas S04 P3.

Dry-run reports the backup contract without writing. Apply stages and commits
the configured backup scope locally; it never pushes to a remote.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any

from memory_atlas_cli.push_size_guard import PushSizeGuardError, build_staged_push_report


BACKUP_TARGETS = [
    "data/public_raw",
    "data/derived",
    "data/run_logs",
    "docs/reviews",
    "reports",
]
DEFAULT_MESSAGE = "Memory Atlas GitHub backup snapshot"
MANUAL_PUSH_COMMAND = "git push origin HEAD:main"


class BackupScopeError(RuntimeError):
    """Raised when a configured backup target cannot be proven repository-local."""


def git_environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    return environment


def run_git(
    repo_root: Path,
    args: list[str],
    check: bool = True,
    input_text: str | None = None,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "--no-replace-objects",
            "-C",
            str(repo_root),
            *args,
        ],
        text=True,
        capture_output=True,
        input=input_text,
        env=git_environment(),
        check=False,
    )
    if check and result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result


def find_git_root(database_dir: Path) -> Path | None:
    result = subprocess.run(
        [
            "git",
            "-c",
            "core.hooksPath=/dev/null",
            "--no-replace-objects",
            "-C",
            str(database_dir),
            "rev-parse",
            "--show-toplevel",
        ],
        text=True,
        capture_output=True,
        env=git_environment(),
        check=False,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip()).resolve()


def relative_to_git(repo_root: Path, path: Path) -> str:
    lexical_root = Path(os.path.abspath(repo_root))
    lexical_path = Path(os.path.abspath(path))
    try:
        return lexical_path.relative_to(lexical_root).as_posix()
    except ValueError as exc:
        raise BackupScopeError("backup target is lexically outside the Git worktree") from exc


def validate_backup_target(database_dir: Path, target: str) -> Path:
    pure = PurePosixPath(target)
    if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise BackupScopeError(f"unsafe backup target path: {target}")
    current = database_dir
    for part in pure.parts:
        current = current / part
        if current.is_symlink():
            raise BackupScopeError(f"backup target traverses a symlink: {target}")
    return current


def target_exists_or_tracked(repo_root: Path, database_dir: Path, target: str) -> bool:
    absolute = validate_backup_target(database_dir, target)
    if absolute.exists():
        return True
    relative = relative_to_git(repo_root, absolute)
    result = run_git(repo_root, ["ls-files", "--error-unmatch", relative], check=False)
    return result.returncode == 0


def git_target_paths(repo_root: Path, database_dir: Path) -> list[str]:
    return [
        relative_to_git(repo_root, database_dir / target)
        for target in BACKUP_TARGETS
        if target_exists_or_tracked(repo_root, database_dir, target)
    ]


def status_files(repo_root: Path, targets: list[str]) -> list[str]:
    if not targets:
        return []
    result = run_git(repo_root, ["status", "--short", "--untracked-files=all", "--", *targets])
    files: list[str] = []
    for line in result.stdout.splitlines():
        if not line.strip():
            continue
        files.append(line[3:].strip())
    return sorted(files)


def staged_files(repo_root: Path) -> list[str]:
    result = run_git(repo_root, ["diff", "--cached", "--name-only"])
    return sorted(line for line in result.stdout.splitlines() if line.strip())


def index_signature(repo_root: Path) -> str:
    payload = run_git(repo_root, ["ls-files", "--stage", "-z"]).stdout.encode(
        "utf-8", errors="surrogateescape"
    )
    return hashlib.sha256(payload).hexdigest()


def write_index_tree(repo_root: Path) -> str:
    return run_git(repo_root, ["write-tree"]).stdout.strip()


def create_bound_commit(
    repo_root: Path,
    *,
    tree_oid: str,
    message: str,
) -> dict[str, str]:
    branch_ref = run_git(repo_root, ["symbolic-ref", "--quiet", "HEAD"]).stdout.strip()
    if branch_ref != "refs/heads/main":
        raise RuntimeError("HEAD changed away from canonical main before commit")
    parent_oid = run_git(repo_root, ["rev-parse", "--verify", "HEAD"]).stdout.strip()
    commit_message = message if message.endswith("\n") else f"{message}\n"
    commit_oid = run_git(
        repo_root,
        ["commit-tree", tree_oid, "-p", parent_oid, "-F", "-"],
        input_text=commit_message,
    ).stdout.strip()
    committed_tree_oid = run_git(repo_root, ["rev-parse", f"{commit_oid}^{{tree}}"]).stdout.strip()
    if committed_tree_oid != tree_oid:
        raise RuntimeError("commit-tree did not preserve the audited index tree")
    reflog_subject = " ".join(message.splitlines()).strip() or DEFAULT_MESSAGE
    run_git(
        repo_root,
        ["update-ref", "-m", f"commit: {reflog_subject}", branch_ref, commit_oid, parent_oid],
    )
    return {
        "branch_ref": branch_ref,
        "parent_oid": parent_oid,
        "commit_oid": commit_oid,
        "tree_oid": tree_oid,
    }


def base_contract(database_dir: Path, repo_root: Path | None, dry_run: bool, apply: bool) -> dict[str, Any]:
    return {
        "status": "PASS",
        "command": "push",
        "task_id": "MA-V12-S04P3",
        "acceptance_id": "ACC-MA-V12-S04P3",
        "database_dir": str(database_dir),
        "git_root": str(repo_root) if repo_root else "",
        "dry_run": dry_run,
        "apply": apply,
        "writes_files": apply,
        "backup_targets": BACKUP_TARGETS,
        "remote_push": False,
        "pushed": False,
        "manual_push_command": MANUAL_PUSH_COMMAND,
        "automation_mode": "local_commit_then_human_or_final_workflow_push",
        "中文原因": "GitHub 备份流程仅在本地记录可提交范围；本阶段不上传远端 main。",
        "fallback建议": "如 dry-run 显示无变更，先运行 sync/build-atlas；最终整体上传阶段再执行远端 push。",
    }


def fail_not_git(database_dir: Path, dry_run: bool, apply: bool) -> dict[str, Any]:
    return {
        "status": "FAIL",
        "reason": "not_git_worktree",
        "task_id": "MA-V12-S04P3",
        "acceptance_id": "ACC-MA-V12-S04P3",
        "database_dir": str(database_dir),
        "dry_run": dry_run,
        "apply": apply,
        "writes_files": False,
        "remote_push": False,
        "pushed": False,
        "中文原因": "当前 database-dir 不在 Git worktree 内，无法生成可恢复的 GitHub 备份提交。",
        "fallback建议": "切换到 LinzeColin/CodexProject/OpenAIDatabase 的规范 checkout 后重试；不要在临时目录伪造备份。",
    }


def installed_source_dry_run(database_dir: Path) -> dict[str, Any] | None:
    manifest_path = database_dir / "memory_atlas_source_workspace.json"
    if not manifest_path.is_file() or manifest_path.is_symlink() or (database_dir / ".git").exists():
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    original_repo_value = manifest.get("original_repo_root")
    if (
        manifest.get("schema_version") != "memory_atlas_source_workspace.v1"
        or not isinstance(original_repo_value, str)
        or not original_repo_value.strip()
        or Path(original_repo_value).expanduser().resolve() == database_dir.resolve()
    ):
        return None
    result = base_contract(database_dir, None, dry_run=True, apply=False)
    result.update(
        {
            "backup_scope_check": "installed_source_copy_no_git",
            "candidate_targets": [target for target in BACKUP_TARGETS if (database_dir / target).exists()],
            "changed_files": [],
            "writes_files": False,
            "remote_push": False,
            "github_main_upload": False,
            "中文原因": "已安装 source 副本不含 Git 元数据；本步骤只确认备份范围，最终 GitHub main 上传仍由 R8 整体交付执行。",
        }
    )
    return result


def dry_run(database_dir: Path, repo_root: Path) -> dict[str, Any]:
    targets = git_target_paths(repo_root, database_dir)
    result = base_contract(database_dir, repo_root, dry_run=True, apply=False)
    result.update({
        "writes_files": False,
        "candidate_targets": targets,
        "changed_files": status_files(repo_root, targets),
    })
    return result


def post_stage_failure(
    result: dict[str, Any],
    repo_root: Path,
    initial_index_signature: str,
    *,
    reason: str,
    error: str | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    try:
        current_signature = index_signature(repo_root)
        current_staged_files = staged_files(repo_root)
        index_changed = current_signature != initial_index_signature
    except RuntimeError:
        current_staged_files = []
        index_changed = True
    result.update({
        "status": "FAIL",
        "committed": False,
        "reason": reason,
        "writes_files": True,
        "index_changed": index_changed,
        "staged_files": current_staged_files,
        "remote_push": False,
        "pushed": False,
        "中文原因": "staged backup 候选在本地写阶段失败；已保留实际 index 状态供人工恢复。",
        "fallback建议": "先检查返回的 staged_files 与 git status；不要自动 unstage、执行 hook、push、force 或扩大提交范围。",
    })
    if error is not None:
        result["error"] = error
    if extra:
        result.update(extra)
    return result


def apply_backup(database_dir: Path, repo_root: Path, message: str) -> dict[str, Any]:
    targets = git_target_paths(repo_root, database_dir)
    result = base_contract(database_dir, repo_root, dry_run=False, apply=True)
    if not targets:
        result.update({
            "committed": False,
            "reason": "no_backup_targets",
            "writes_files": False,
            "中文原因": "没有找到 raw/derived/reports/run logs 备份目录。",
            "fallback建议": "先运行同步或构建命令生成可备份数据，再重新执行 backup apply。",
        })
        return result

    preexisting_staged = staged_files(repo_root)
    if preexisting_staged:
        result.update({
            "status": "FAIL",
            "committed": False,
            "reason": "preexisting_staged_changes",
            "writes_files": False,
            "preexisting_staged_files": preexisting_staged,
            "中文原因": "运行前已有 staged 变更，无法证明本地备份提交只包含当前 backup scope。",
            "fallback建议": "保留并人工处理现有 staged 变更；不要自动 unstage、扩大提交范围或继续 push。",
        })
        return result
    initial_index_signature = index_signature(repo_root)

    branch_preflight = build_staged_push_report(database_dir, repo_root=repo_root)
    if branch_preflight["status"] != "PASS":
        result.update({
            "status": "FAIL",
            "committed": False,
            "reason": "push_size_guard_failed",
            "writes_files": False,
            "index_changed": False,
            "push_size_guard": branch_preflight,
            "中文原因": "Git 分支或 push-size canonical contract 未通过 commit 前预检，index 保持不变。",
            "fallback建议": "切换到 canonical main 并修复合同；不要在其他分支提交、自动 merge/rebase 或绕过门禁。",
        })
        return result

    commit: dict[str, str] | None = None
    push_size_guard: dict[str, Any] | None = None
    try:
        run_git(repo_root, ["add", "--", *targets])
        files = staged_files(repo_root)
        if not files:
            result.update({
                "committed": False,
                "reason": "no_changes",
                "writes_files": False,
                "index_changed": False,
                "committed_files": [],
                "中文原因": "备份范围内没有新的 Git 变更。",
                "fallback建议": "如预期有新数据，先运行 sync/build-atlas 并确认输出目录位于 backup scope。",
            })
            return result

        tree_before_guard = write_index_tree(repo_root)
        push_size_guard = build_staged_push_report(database_dir, repo_root=repo_root)
        tree_after_guard = write_index_tree(repo_root)
        if tree_before_guard != tree_after_guard:
            return post_stage_failure(
                result,
                repo_root,
                initial_index_signature,
                reason="index_changed_during_push_size_guard",
                extra={
                    "tree_before_guard": tree_before_guard,
                    "tree_after_guard": tree_after_guard,
                    "push_size_guard": push_size_guard,
                },
            )
        push_size_guard["audited_tree_oid"] = tree_after_guard
        if push_size_guard["status"] != "PASS" or not push_size_guard["single_commit_ready"]:
            guard_reason = (
                push_size_guard["reason"]
                if push_size_guard["status"] != "PASS"
                else "staged_batches_required"
            )
            return post_stage_failure(
                result,
                repo_root,
                initial_index_signature,
                reason="push_size_guard_failed",
                extra={
                    "push_size_guard_reason": guard_reason,
                    "push_size_guard": push_size_guard,
                    "中文原因": "staged Git 对象未通过单次 push 体积、普通 blob 或 main 分支门禁，本地提交已停止。",
                    "fallback建议": "按 guard atomic units 拆成完整可恢复 commits；保留现场，不 force、不用 LFS 绕过。",
                },
            )

        commit = create_bound_commit(repo_root, tree_oid=tree_after_guard, message=message)
        committed_files = sorted(
            line
            for line in run_git(
                repo_root,
                ["diff-tree", "--no-commit-id", "--name-only", "-r", commit["commit_oid"]],
            ).stdout.splitlines()
            if line.strip()
        )
        remaining_staged_files = staged_files(repo_root)
        result.update({
            "committed": True,
            "commit_message": message,
            "committed_files": committed_files,
            "commit_oid": commit["commit_oid"],
            "parent_oid": commit["parent_oid"],
            "audited_tree_oid": commit["tree_oid"],
            "commit_method": "commit_tree_plus_update_ref_cas",
            "hooks_executed": False,
            "remaining_staged_files": remaining_staged_files,
            "push_size_guard": push_size_guard,
        })
        if remaining_staged_files:
            result.update({
                "status": "FAIL",
                "reason": "index_changed_after_audited_commit",
                "index_changed": True,
                "中文原因": "精确 audited tree 已提交，但随后 index 出现额外 staged 变更；额外变更未进入该 commit。",
                "fallback建议": "保留 commit 与 staged 现场，逐项核对 remaining_staged_files；不要自动 push 或 unstage。",
            })
        return result
    except (OSError, RuntimeError, PushSizeGuardError) as exc:
        if commit is not None:
            return post_stage_failure(
                result,
                repo_root,
                initial_index_signature,
                reason="post_commit_inspection_failed",
                error=str(exc),
                extra={
                    "committed": True,
                    "commit_message": message,
                    "commit_oid": commit["commit_oid"],
                    "parent_oid": commit["parent_oid"],
                    "audited_tree_oid": commit["tree_oid"],
                    "commit_method": "commit_tree_plus_update_ref_cas",
                    "hooks_executed": False,
                    "push_size_guard": push_size_guard,
                    "中文原因": "old-HEAD CAS 已成功提交精确 audited tree，但提交后的只读检查失败；commit 真实存在。",
                    "fallback建议": "先核对返回的 commit_oid 与当前 HEAD，再重跑只读检查；不要重复提交或自动 push。",
                },
            )
        return post_stage_failure(
            result,
            repo_root,
            initial_index_signature,
            reason="git_backup_failed",
            error=str(exc),
        )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Memory Atlas S04 P3 local GitHub backup control.")
    parser.add_argument("--database-dir", type=Path, default=Path("."))
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true")
    mode.add_argument("--apply", action="store_true")
    parser.add_argument("--message", default=DEFAULT_MESSAGE)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    database_dir = args.database_dir.resolve()
    repo_root = find_git_root(database_dir)
    if repo_root is None:
        installed_result = installed_source_dry_run(database_dir) if args.dry_run else None
        if installed_result is not None:
            print(json.dumps(installed_result, ensure_ascii=False, indent=2, sort_keys=True))
            return 0
        print(json.dumps(fail_not_git(database_dir, args.dry_run, args.apply), ensure_ascii=False, indent=2, sort_keys=True))
        return 2

    try:
        result = dry_run(database_dir, repo_root) if args.dry_run else apply_backup(database_dir, repo_root, args.message)
    except BackupScopeError as exc:
        result = {
            "status": "FAIL",
            "reason": "unsafe_backup_target",
            "task_id": "MA-V12-S04P3",
            "acceptance_id": "ACC-MA-V12-S04P3",
            "database_dir": str(database_dir),
            "writes_files": False,
            "index_changed": False,
            "remote_push": False,
            "pushed": False,
            "error": str(exc),
            "中文原因": "backup target 不是可证明的仓库内普通路径，已在 staging 前停止。",
            "fallback建议": "移除 target 路径中的 symlink 或越界组件并核对 Git scope；不要跟随链接扩大备份范围。",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3
    except (RuntimeError, PushSizeGuardError) as exc:
        result = {
            "status": "FAIL",
            "reason": "git_backup_failed",
            "task_id": "MA-V12-S04P3",
            "acceptance_id": "ACC-MA-V12-S04P3",
            "database_dir": str(database_dir),
            "writes_files": False,
            "remote_push": False,
            "pushed": False,
            "error": str(exc),
            "中文原因": "Git 本地备份命令失败。",
            "fallback建议": "检查 git status、权限和用户配置后重试；不要跳过失败继续伪造备份。",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 3

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
