"""S06-P3-T2 conservative Git object sizing and resumable batch planning."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Iterable


CONFIG_PATH = Path("config/data_sources/push_size_guard.json")
SCHEMA_VERSION = "memory_atlas.push_size_guard.v1_2_1_s06_p3_t2"
TASK_ID = "S06-P3-T2"
AUDIT_SCOPES = ("staged", "pending", "all")
ESTIMATION = {
    "model": "unique_git_object_uncompressed_bytes_plus_protocol_reserve",
    "staged_source": "git_index",
    "pending_source": "remote_ref_to_head_unique_objects",
    "unique_object_deduplication": True,
    "reads_worktree_file_bodies": False,
    "protocol_reserve_bytes_per_batch": 8 * 1024 * 1024,
    "protocol_reserve_bytes_per_object": 256,
}
LIMITS = {
    "recommended_chunk_bytes": 45 * 1024 * 1024,
    "split_required_above_bytes": 50 * 1024 * 1024,
    "ordinary_blob_hard_stop_at_or_above_bytes": 100 * 1024 * 1024,
    "max_single_push_target_bytes": 1536 * 1024 * 1024,
    "single_push_comparison": "strictly_less_than",
}
STAGED_BATCHING = {
    "atomic_unit_rules": [
        {"prefix": "data/raw_archives", "segments_after_prefix": 2},
        {"prefix": "data/public_raw/agents", "segments_after_prefix": 1},
        {"prefix": "data/public_raw", "segments_after_prefix": 1},
    ],
    "other_path_unit": "individual_path",
    "deterministic_order": "unit_id_then_repository_path",
    "index_mutation_by_audit": False,
}
PENDING_BATCHING = {
    "unit": "whole_commit",
    "split_between_commits_only": True,
    "deterministic_order": "oldest_first_parent_fast_forward_boundary_first",
    "oversized_commit_action": "fail_closed_recommit_required",
    "checkpoint_ref": "origin/main",
    "resume_strategy": "fetch_validate_checkpoint_and_recompute",
    "expected_remote_oid_supported": True,
}
DIRECT_MAIN = {
    "required_branch": "main",
    "remote": "origin",
    "destination_branch": "main",
    "fetch_before_each_batch": True,
    "require_fast_forward": True,
    "force": False,
    "git_lfs": False,
    "automatic_rebase": False,
    "automatic_merge": False,
    "replace_refs": False,
    "lazy_fetch": False,
    "hooks": False,
}
INTEGRATION = {
    "atlasctl_check": "push-size",
    "audit_scopes": list(AUDIT_SCOPES),
    "default_audit_scope": "staged",
    "local_backup_precommit_guard": True,
}
BOUNDARIES = {
    "remote_push": False,
    "staged_file_content_read": False,
    "raw_mutation": False,
    "history_rewrite": False,
    "force_push": False,
    "raw_fixture_contract_task": "S06-P3-T3",
    "direct_main_execution_task": "S07",
}
_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "estimation",
    "limits",
    "staged_batching",
    "pending_batching",
    "direct_main",
    "integration",
    "boundaries",
}
_MAX_CONFIG_BYTES = 64 * 1024
_OID_RE = re.compile(r"^[0-9a-f]{40,64}$")


class PushSizeGuardError(ValueError):
    """Raised when Git size evidence is invalid or cannot be proven safely."""


def _read_regular_json(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise PushSizeGuardError(f"cannot read push size contract: {CONFIG_PATH.as_posix()}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > _MAX_CONFIG_BYTES:
            raise PushSizeGuardError("push size contract must be a bounded regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(_MAX_CONFIG_BYTES + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > _MAX_CONFIG_BYTES:
        raise PushSizeGuardError("push size contract exceeds the size limit")
    try:
        payload = json.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise PushSizeGuardError("push size contract must be valid UTF-8 JSON") from exc
    if not isinstance(payload, dict):
        raise PushSizeGuardError("push size contract must be an object")
    return payload


def validate_push_size_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _CONTRACT_KEYS:
        raise PushSizeGuardError("push size contract keys do not match the canonical contract")
    expected = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "estimation": ESTIMATION,
        "limits": LIMITS,
        "staged_batching": STAGED_BATCHING,
        "pending_batching": PENDING_BATCHING,
        "direct_main": DIRECT_MAIN,
        "integration": INTEGRATION,
        "boundaries": BOUNDARIES,
    }
    if payload != expected:
        raise PushSizeGuardError("push size contract drifted from the reviewed S06-P3-T2 policy")
    if not (
        LIMITS["recommended_chunk_bytes"]
        < LIMITS["split_required_above_bytes"]
        < LIMITS["ordinary_blob_hard_stop_at_or_above_bytes"]
        < LIMITS["max_single_push_target_bytes"]
    ):
        raise PushSizeGuardError("push size limits are not strictly ordered")
    return payload


def load_push_size_contract(database_dir: Path, path: Path | None = None) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    return validate_push_size_contract(_read_regular_json(path or database_dir / CONFIG_PATH))


def _git_bytes(
    repo_root: Path,
    arguments: list[str],
    *,
    input_bytes: bytes | None = None,
    check: bool = True,
) -> subprocess.CompletedProcess[bytes]:
    environment = os.environ.copy()
    environment["GIT_NO_LAZY_FETCH"] = "1"
    environment["GIT_TERMINAL_PROMPT"] = "0"
    result = subprocess.run(
        ["git", "--no-replace-objects", "-C", str(repo_root), *arguments],
        input=input_bytes,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=environment,
        check=False,
    )
    if check and result.returncode != 0:
        detail = (result.stderr or result.stdout).decode("utf-8", errors="replace").strip()
        raise PushSizeGuardError(detail or f"git {' '.join(arguments)} failed")
    return result


def find_git_root(database_dir: Path) -> Path:
    result = _git_bytes(Path(database_dir), ["rev-parse", "--show-toplevel"], check=False)
    if result.returncode != 0:
        raise PushSizeGuardError("database-dir is not inside a Git worktree")
    try:
        root = Path(result.stdout.decode("utf-8").strip()).resolve()
        Path(database_dir).resolve().relative_to(root)
    except (UnicodeDecodeError, ValueError) as exc:
        raise PushSizeGuardError("database-dir is outside the resolved Git worktree") from exc
    return root


def _decode_git_path(value: bytes) -> str:
    try:
        path = value.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise PushSizeGuardError("Git path is not valid UTF-8") from exc
    pure = PurePosixPath(path)
    if not path or pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
        raise PushSizeGuardError("Git emitted an unsafe repository path")
    return pure.as_posix()


def _validate_oid(value: str, field: str) -> str:
    if not _OID_RE.fullmatch(value):
        raise PushSizeGuardError(f"{field} is not a canonical Git object id")
    return value


def _object_info(repo_root: Path, object_ids: Iterable[str]) -> dict[str, dict[str, Any]]:
    unique = sorted(set(object_ids))
    if not unique:
        return {}
    input_bytes = "".join(f"{oid}\n" for oid in unique).encode("ascii")
    result = _git_bytes(
        repo_root,
        ["cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)"],
        input_bytes=input_bytes,
    )
    rows: dict[str, dict[str, Any]] = {}
    for raw_line in result.stdout.splitlines():
        fields = raw_line.decode("ascii", errors="strict").split(" ")
        if len(fields) != 3:
            raise PushSizeGuardError("git cat-file returned incomplete object metadata")
        oid, object_type, size_text = fields
        _validate_oid(oid, "object id")
        try:
            size = int(size_text)
        except ValueError as exc:
            raise PushSizeGuardError("git cat-file returned an invalid object size") from exc
        if size < 0 or object_type not in {"blob", "commit", "tree", "tag"}:
            raise PushSizeGuardError("git cat-file returned unsupported object metadata")
        rows[oid] = {"oid": oid, "type": object_type, "bytes": size}
    if set(rows) != set(unique):
        raise PushSizeGuardError("Git object metadata is incomplete")
    return rows


def _database_prefix(repo_root: Path, database_dir: Path) -> str:
    relative = database_dir.resolve().relative_to(repo_root.resolve()).as_posix()
    return "" if relative == "." else relative


def _staged_entries(repo_root: Path) -> list[dict[str, Any]]:
    names_result = _git_bytes(
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
    names = sorted({_decode_git_path(value) for value in names_result.stdout.split(b"\0") if value})
    entries: list[dict[str, Any]] = []
    for path in names:
        stage_result = _git_bytes(repo_root, ["ls-files", "--stage", "-z", "--", path])
        rows = [value for value in stage_result.stdout.split(b"\0") if value]
        if not rows:
            entries.append({"path": path, "operation": "delete", "mode": None, "oid": None})
            continue
        if len(rows) != 1 or b"\t" not in rows[0]:
            raise PushSizeGuardError(f"staged index entry is ambiguous: {path}")
        metadata, encoded_path = rows[0].split(b"\t", 1)
        fields = metadata.decode("ascii", errors="strict").split(" ")
        if len(fields) != 3 or fields[2] != "0" or _decode_git_path(encoded_path) != path:
            raise PushSizeGuardError(f"staged index entry is unmerged or malformed: {path}")
        mode, oid, _stage = fields
        _validate_oid(oid, f"staged oid for {path}")
        entries.append({"path": path, "operation": "upsert", "mode": mode, "oid": oid})
    return entries


def _unit_id_for_path(path: str, database_prefix: str, contract: dict[str, Any]) -> str:
    database_relative = path
    if database_prefix:
        prefix = f"{database_prefix}/"
        if not path.startswith(prefix):
            return path
        database_relative = path[len(prefix) :]
    parts = PurePosixPath(database_relative).parts
    for rule in contract["staged_batching"]["atomic_unit_rules"]:
        prefix_parts = PurePosixPath(rule["prefix"]).parts
        depth = len(prefix_parts) + rule["segments_after_prefix"]
        if parts[: len(prefix_parts)] == prefix_parts and len(parts) >= depth:
            unit = PurePosixPath(*parts[:depth]).as_posix()
            return f"{database_prefix}/{unit}" if database_prefix else unit
    return path


def _manifest_hash(rows: Iterable[str]) -> str:
    payload = "".join(f"{row}\n" for row in sorted(rows))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _estimated_upper_bound(object_bytes: int, object_count: int, estimation: dict[str, Any]) -> int:
    return (
        object_bytes
        + estimation["protocol_reserve_bytes_per_batch"]
        + object_count * estimation["protocol_reserve_bytes_per_object"]
    )


def evaluate_staged_blob_limits(
    entries: list[dict[str, Any]],
    object_info: dict[str, dict[str, Any]],
    limits: dict[str, Any],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    for entry in entries:
        oid = entry.get("oid")
        if not oid or object_info[oid]["type"] != "blob":
            continue
        size = object_info[oid]["bytes"]
        if size >= limits["ordinary_blob_hard_stop_at_or_above_bytes"]:
            violations.append({"path": entry["path"], "bytes": size, "reason": "ordinary_blob_hard_stop"})
        elif size > limits["split_required_above_bytes"]:
            violations.append({"path": entry["path"], "bytes": size, "reason": "split_required_above_50_mib"})
    return violations


def plan_staged_batches(
    entries: list[dict[str, Any]],
    object_info: dict[str, dict[str, Any]],
    *,
    database_prefix: str,
    contract: dict[str, Any],
) -> dict[str, Any]:
    max_bytes = contract["limits"]["max_single_push_target_bytes"]
    estimation = contract["estimation"]
    units: dict[str, dict[str, Any]] = {}
    for entry in entries:
        unit_id = _unit_id_for_path(entry["path"], database_prefix, contract)
        unit = units.setdefault(unit_id, {"unit_id": unit_id, "paths": [], "oids": set()})
        unit["paths"].append(entry["path"])
        if entry.get("oid"):
            unit["oids"].add(entry["oid"])

    rows: list[dict[str, Any]] = []
    oversized_units: list[dict[str, Any]] = []
    for unit_id in sorted(units):
        unit = units[unit_id]
        object_bytes = sum(object_info[oid]["bytes"] for oid in unit["oids"])
        upper_bound = _estimated_upper_bound(object_bytes, len(unit["oids"]), estimation)
        row = {
            "unit_id": unit_id,
            "path_count": len(unit["paths"]),
            "path_manifest_sha256": _manifest_hash(unit["paths"]),
            "object_ids": tuple(sorted(unit["oids"])),
            "object_bytes": object_bytes,
            "estimated_push_upper_bound_bytes": upper_bound,
        }
        rows.append(row)
        if upper_bound >= max_bytes:
            oversized_units.append({
                "unit_id": unit_id,
                "object_bytes": object_bytes,
                "estimated_push_upper_bound_bytes": upper_bound,
                "reason": "atomic_recovery_unit_exceeds_single_push_target",
            })

    batches: list[dict[str, Any]] = []
    current_rows: list[dict[str, Any]] = []
    current_oids: set[str] = set()

    def finish_batch() -> None:
        if not current_rows:
            return
        object_bytes = sum(object_info[oid]["bytes"] for oid in current_oids)
        index = len(batches) + 1
        unit_ids = [row["unit_id"] for row in current_rows]
        batch_id = _manifest_hash([TASK_ID, "staged", str(index), *unit_ids, *sorted(current_oids)])
        batches.append({
            "batch_index": index,
            "batch_id": batch_id,
            "unit_ids": unit_ids,
            "unit_count": len(unit_ids),
            "path_count": sum(row["path_count"] for row in current_rows),
            "object_count": len(current_oids),
            "object_bytes": object_bytes,
            "estimated_push_upper_bound_bytes": _estimated_upper_bound(
                object_bytes, len(current_oids), estimation
            ),
        })

    if not oversized_units:
        for row in rows:
            candidate_oids = current_oids | set(row["object_ids"])
            candidate_bytes = _estimated_upper_bound(
                sum(object_info[oid]["bytes"] for oid in candidate_oids),
                len(candidate_oids),
                estimation,
            )
            if current_rows and candidate_bytes >= max_bytes:
                finish_batch()
                current_rows = []
                current_oids = set()
            current_rows.append(row)
            current_oids.update(row["object_ids"])
        finish_batch()

    unique_oids = {entry["oid"] for entry in entries if entry.get("oid")}
    object_bytes = sum(object_info[oid]["bytes"] for oid in unique_oids)
    plan_basis = [
        SCHEMA_VERSION,
        "staged",
        str(max_bytes),
        str(estimation["protocol_reserve_bytes_per_batch"]),
        str(estimation["protocol_reserve_bytes_per_object"]),
        *[f"{entry['path']}:{entry.get('oid') or 'DELETE'}" for entry in entries],
    ]
    return {
        "plan_id": _manifest_hash(plan_basis),
        "entry_count": len(entries),
        "unique_object_count": len(unique_oids),
        "unique_object_bytes": object_bytes,
        "estimated_unsplit_push_upper_bound_bytes": (
            _estimated_upper_bound(object_bytes, len(unique_oids), estimation) if entries else 0
        ),
        "batch_required": len(batches) > 1,
        "batch_count": len(batches),
        "batches": batches,
        "oversized_atomic_units": oversized_units,
    }


def build_staged_push_report(
    database_dir: Path,
    *,
    repo_root: Path | None = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    contract = validate_push_size_contract(contract) if contract is not None else load_push_size_contract(database_dir)
    repo_root = repo_root.resolve() if repo_root is not None else find_git_root(database_dir)
    prefix = _database_prefix(repo_root, database_dir)
    entries = _staged_entries(repo_root)
    object_info = _object_info(repo_root, [entry["oid"] for entry in entries if entry.get("oid")])
    violations = evaluate_staged_blob_limits(entries, object_info, contract["limits"])
    plan = plan_staged_batches(entries, object_info, database_prefix=prefix, contract=contract)
    branch = _current_branch(repo_root)
    errors = [row["reason"] for row in violations]
    errors.extend(row["reason"] for row in plan["oversized_atomic_units"])
    if branch != contract["direct_main"]["required_branch"]:
        errors.append("branch_is_not_main")
    single_commit_ready = not errors and not plan["batch_required"]
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason": None if not errors else errors[0],
        "branch": branch,
        "database_prefix": prefix or ".",
        "blob_violations": violations,
        "plan": plan,
        "single_commit_ready": single_commit_ready,
        "staged_file_content_read": False,
        "index_mutation": False,
    }


def _current_branch(repo_root: Path) -> str:
    result = _git_bytes(repo_root, ["symbolic-ref", "--quiet", "--short", "HEAD"], check=False)
    return result.stdout.decode("utf-8", errors="replace").strip() if result.returncode == 0 else "DETACHED"


def _ref_oid(repo_root: Path, ref: str) -> str:
    result = _git_bytes(repo_root, ["rev-parse", "--verify", ref], check=False)
    if result.returncode != 0:
        raise PushSizeGuardError(f"required Git ref is missing: {ref}")
    return _validate_oid(result.stdout.decode("ascii").strip(), ref)


def _is_ancestor(repo_root: Path, ancestor: str, descendant: str) -> bool:
    result = _git_bytes(repo_root, ["merge-base", "--is-ancestor", ancestor, descendant], check=False)
    if result.returncode not in {0, 1}:
        raise PushSizeGuardError("cannot determine Git ancestry")
    return result.returncode == 0


def _pending_relation(repo_root: Path, remote_oid: str, head_oid: str) -> str:
    if remote_oid == head_oid:
        return "up_to_date"
    if _is_ancestor(repo_root, remote_oid, head_oid):
        return "ahead"
    if _is_ancestor(repo_root, head_oid, remote_oid):
        return "behind"
    return "diverged"


def _rev_list_oids(repo_root: Path, arguments: list[str]) -> list[str]:
    result = _git_bytes(repo_root, arguments)
    rows: list[str] = []
    for line in result.stdout.splitlines():
        if not line:
            continue
        oid = line.split(b" ", 1)[0].decode("ascii", errors="strict")
        rows.append(_validate_oid(oid, "rev-list object id"))
    return rows


def _pending_commit_units(repo_root: Path, remote_oid: str, head_oid: str) -> list[dict[str, Any]]:
    commits = _rev_list_oids(
        repo_root,
        [
            "rev-list",
            "--reverse",
            "--first-parent",
            "--ancestry-path",
            f"{remote_oid}..{head_oid}",
        ],
    )
    if remote_oid != head_oid and (not commits or commits[-1] != head_oid):
        raise PushSizeGuardError("cannot derive complete fast-forward batch boundaries")

    previous_oid = remote_oid
    units: list[dict[str, Any]] = []
    for commit_oid in commits:
        if not _is_ancestor(repo_root, previous_oid, commit_oid):
            raise PushSizeGuardError("pending batch boundary is not a fast-forward")
        reachable = set(
            _rev_list_oids(repo_root, ["rev-list", "--objects", commit_oid, f"^{previous_oid}"])
        )
        units.append({"commit_oid": commit_oid, "object_ids": tuple(sorted(reachable))})
        previous_oid = commit_oid
    return units


def plan_pending_commit_batches(
    repo_root: Path,
    remote_oid: str,
    head_oid: str,
    *,
    max_bytes: int,
    reserve_bytes: int,
    per_object_reserve_bytes: int = 0,
    split_required_above_bytes: int = LIMITS["split_required_above_bytes"],
    ordinary_blob_hard_stop_at_or_above_bytes: int = LIMITS[
        "ordinary_blob_hard_stop_at_or_above_bytes"
    ],
    remote: str = "origin",
    destination_branch: str = "main",
) -> dict[str, Any]:
    units = _pending_commit_units(repo_root, remote_oid, head_oid)
    pending_commit_count = len(
        _rev_list_oids(repo_root, ["rev-list", "--topo-order", f"{remote_oid}..{head_oid}"])
    )
    object_info = _object_info(repo_root, [oid for unit in units for oid in unit["object_ids"]])
    hard_stop_blobs: list[dict[str, Any]] = []
    split_required_blobs: list[dict[str, Any]] = []
    for oid in sorted(object_info):
        metadata = object_info[oid]
        if metadata["type"] != "blob":
            continue
        if metadata["bytes"] >= ordinary_blob_hard_stop_at_or_above_bytes:
            hard_stop_blobs.append({
                "oid": oid,
                "bytes": metadata["bytes"],
                "reason": "ordinary_blob_hard_stop",
            })
        elif metadata["bytes"] > split_required_above_bytes:
            split_required_blobs.append({
                "oid": oid,
                "bytes": metadata["bytes"],
                "reason": "split_required_above_50_mib",
            })
    blob_violations = hard_stop_blobs + split_required_blobs
    oversized: list[dict[str, Any]] = []
    for unit in units:
        object_bytes = sum(object_info[oid]["bytes"] for oid in unit["object_ids"])
        unit["object_bytes"] = object_bytes
        upper_bound = object_bytes + reserve_bytes + len(unit["object_ids"]) * per_object_reserve_bytes
        if upper_bound >= max_bytes:
            oversized.append({
                "commit_oid": unit["commit_oid"],
                "object_bytes": object_bytes,
                "estimated_push_upper_bound_bytes": upper_bound,
                "reason": "whole_commit_exceeds_single_push_target",
            })

    batches: list[dict[str, Any]] = []
    current: list[dict[str, Any]] = []
    current_bytes = 0

    def finish_batch() -> None:
        nonlocal current, current_bytes
        if not current:
            return
        index = len(batches) + 1
        tip = current[-1]["commit_oid"]
        batch_id = _manifest_hash([TASK_ID, "pending", str(index), *[row["commit_oid"] for row in current]])
        batches.append({
            "batch_index": index,
            "batch_id": batch_id,
            "first_commit": current[0]["commit_oid"],
            "tip_commit": tip,
            "commit_count": len(current),
            "object_count": sum(len(row["object_ids"]) for row in current),
            "object_bytes": current_bytes,
            "estimated_push_upper_bound_bytes": (
                current_bytes
                + reserve_bytes
                + sum(len(row["object_ids"]) for row in current) * per_object_reserve_bytes
            ),
            "push_argv": ["git", "push", remote, f"{tip}:{destination_branch}"],
        })
        current = []
        current_bytes = 0

    if not oversized and not blob_violations:
        for unit in units:
            candidate = (
                current_bytes
                + unit["object_bytes"]
                + reserve_bytes
                + (sum(len(row["object_ids"]) for row in current) + len(unit["object_ids"]))
                * per_object_reserve_bytes
            )
            if current and candidate >= max_bytes:
                finish_batch()
            current.append(unit)
            current_bytes += unit["object_bytes"]
        finish_batch()

    unique_oids = {oid for unit in units for oid in unit["object_ids"]}
    plan_id = _manifest_hash([
        SCHEMA_VERSION,
        "pending",
        remote_oid,
        head_oid,
        str(max_bytes),
        str(reserve_bytes),
        str(per_object_reserve_bytes),
        *[unit["commit_oid"] for unit in units],
    ])
    return {
        "plan_id": plan_id,
        "remote_checkpoint_oid": remote_oid,
        "head_oid": head_oid,
        "pending_commit_count": pending_commit_count,
        "pending_boundary_count": len(units),
        "unique_object_count": len(unique_oids),
        "unique_object_bytes": sum(object_info[oid]["bytes"] for oid in unique_oids),
        "batch_required": len(batches) > 1,
        "batch_count": len(batches),
        "batches": batches,
        "blob_violations": blob_violations,
        "oversized_commits": oversized,
        "resume": {
            "strategy": PENDING_BATCHING["resume_strategy"],
            "checkpoint_ref": PENDING_BATCHING["checkpoint_ref"],
            "expected_remote_oid": remote_oid,
            "next_batch_index": 1 if batches else None,
            "requires_fetch_before_each_batch": True,
            "recompute_after_each_success": True,
        },
    }


def build_pending_push_report(
    database_dir: Path,
    *,
    repo_root: Path | None = None,
    contract: dict[str, Any] | None = None,
    expected_remote_oid: str | None = None,
) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    contract = validate_push_size_contract(contract) if contract is not None else load_push_size_contract(database_dir)
    repo_root = repo_root.resolve() if repo_root is not None else find_git_root(database_dir)
    branch = _current_branch(repo_root)
    remote_ref = contract["pending_batching"]["checkpoint_ref"]
    remote_oid = _ref_oid(repo_root, remote_ref)
    head_oid = _ref_oid(repo_root, "HEAD")
    relation = _pending_relation(repo_root, remote_oid, head_oid)
    errors: list[str] = []
    if branch != contract["direct_main"]["required_branch"]:
        errors.append("branch_is_not_main")
    if expected_remote_oid is not None:
        expected_remote_oid = _validate_oid(expected_remote_oid, "expected remote oid")
        if expected_remote_oid != remote_oid:
            errors.append("remote_checkpoint_changed")
    if relation not in {"ahead", "up_to_date"}:
        errors.append(f"remote_history_{relation}")

    plan = None
    if not errors:
        plan = plan_pending_commit_batches(
            repo_root,
            remote_oid,
            head_oid,
            max_bytes=contract["limits"]["max_single_push_target_bytes"],
            reserve_bytes=contract["estimation"]["protocol_reserve_bytes_per_batch"],
            per_object_reserve_bytes=contract["estimation"]["protocol_reserve_bytes_per_object"],
            split_required_above_bytes=contract["limits"]["split_required_above_bytes"],
            ordinary_blob_hard_stop_at_or_above_bytes=contract["limits"][
                "ordinary_blob_hard_stop_at_or_above_bytes"
            ],
            remote=contract["direct_main"]["remote"],
            destination_branch=contract["direct_main"]["destination_branch"],
        )
        if plan["blob_violations"]:
            errors.append(plan["blob_violations"][0]["reason"])
        elif plan["oversized_commits"]:
            errors.append("whole_commit_exceeds_single_push_target")
    return {
        "status": "PASS" if not errors else "FAIL",
        "reason": None if not errors else errors[0],
        "branch": branch,
        "remote_ref": remote_ref,
        "remote_checkpoint_oid": remote_oid,
        "head_oid": head_oid,
        "remote_relation": relation,
        "expected_remote_oid_checked": expected_remote_oid is not None,
        "fetch_performed": False,
        "fetch_required_before_execution": True,
        "plan": plan,
        "remote_push": False,
    }


def audit_push_size(
    database_dir: Path,
    *,
    scope: str = "staged",
    expected_remote_oid: str | None = None,
    contract: dict[str, Any] | None = None,
) -> dict[str, Any]:
    if scope not in AUDIT_SCOPES:
        raise PushSizeGuardError(f"unsupported push size audit scope: {scope}")
    database_dir = Path(database_dir).resolve()
    contract = validate_push_size_contract(contract) if contract is not None else load_push_size_contract(database_dir)
    repo_root = find_git_root(database_dir)
    if expected_remote_oid is not None and scope == "staged":
        raise PushSizeGuardError("expected remote oid requires pending or all scope")
    staged = build_staged_push_report(database_dir, repo_root=repo_root, contract=contract) if scope in {"staged", "all"} else None
    pending = (
        build_pending_push_report(
            database_dir,
            repo_root=repo_root,
            contract=contract,
            expected_remote_oid=expected_remote_oid,
        )
        if scope in {"pending", "all"}
        else None
    )
    failures = [row for row in (staged, pending) if row is not None and row["status"] != "PASS"]
    return {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "command": "audit",
        "check": "push-size",
        "scope": scope,
        "status": "PASS" if not failures else "FAIL",
        "reason": None if not failures else failures[0]["reason"],
        "estimation_model": contract["estimation"]["model"],
        "limits": contract["limits"],
        "staged": staged,
        "pending": pending,
        "safety": {
            "staged_file_content_read": False,
            "index_mutation": False,
            "raw_mutation": False,
            "remote_fetch": False,
            "remote_push": False,
            "force_push": False,
            "history_rewrite": False,
        },
        "next_task_boundary": contract["boundaries"]["raw_fixture_contract_task"],
    }


def run_push_size_audit(args: argparse.Namespace) -> int:
    try:
        result = audit_push_size(
            args.database_dir,
            scope=args.push_scope,
            expected_remote_oid=args.expected_remote_oid,
        )
    except (OSError, PushSizeGuardError, subprocess.SubprocessError) as exc:
        result = {
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "command": "audit",
            "check": "push-size",
            "scope": getattr(args, "push_scope", "staged"),
            "status": "FAIL",
            "reason": str(exc),
            "safety": {
                "staged_file_content_read": False,
                "index_mutation": False,
                "raw_mutation": False,
                "remote_fetch": False,
                "remote_push": False,
                "force_push": False,
                "history_rewrite": False,
            },
        }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 2


__all__ = (
    "AUDIT_SCOPES",
    "PushSizeGuardError",
    "audit_push_size",
    "build_pending_push_report",
    "build_staged_push_report",
    "evaluate_staged_blob_limits",
    "load_push_size_contract",
    "plan_pending_commit_batches",
    "plan_staged_batches",
    "run_push_size_audit",
    "validate_push_size_contract",
)
