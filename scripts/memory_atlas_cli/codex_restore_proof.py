"""Empty-directory Codex archive restore and derived rebuild proof."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import stat
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any

from memory_atlas_cli.codex_derived import (
    EXPECTED_OUTPUTS,
    CodexDerivedError,
    build_codex_derived,
)
from memory_atlas_cli.codex_public_raw_archive import (
    CodexPublicRawArchiveError,
    verify_codex_public_raw_archive,
)
from memory_atlas_cli.raw_ledger import LEDGER_PATH


PACKAGE_ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = Path("config/data_sources/codex_restore_proof.json")
MODEL_PARAMETERS_PATH = Path(
    "机器治理/参数与公式/codex_restore_proof.v1_2_1_s07_p3_t3.json"
)
CODEX_DERIVED_CONTRACT_PATH = Path("config/data_sources/codex_derived.json")
CODEX_DERIVED_MODEL_PATH = Path(
    "机器治理/参数与公式/codex_derived.v1_2_1_s07_p2_t1.json"
)
RAW_LEDGER_CONTRACT_PATH = Path("config/data_sources/raw_ledger.json")
ARCHIVE_ROOT = Path("data/raw_archives/codex")
PUBLIC_RAW_ROOT = Path("data/public_raw")
SOURCE_MANIFEST_MEMBER = "codex/_memory_atlas/source_manifest.json"
BASELINE_INDEX_SCHEMA = "memory_atlas.codex_public_raw_archive_index.v1_2_1_s07_p1_t2"
BASELINE_MANIFEST_SCHEMA = (
    "memory_atlas.codex_public_raw_archive_manifest.v1_2_1_s07_p1_t2"
)
CONTRACT_SCHEMA_VERSION = (
    "memory_atlas.codex_restore_proof_contract.v1_2_1_s07_p3_t3"
)
MODEL_SCHEMA_VERSION = "memory_atlas.codex_restore_proof_model.v1_2_1_s07_p3_t3"
RESULT_SCHEMA_VERSION = "memory_atlas.codex_restore_proof.v1_2_1_s07_p3_t3"
TASK_ID = "S07-P3-T3"
ACCEPTANCE_ID = "ACC-MA-V121-S07-P3-T3"
MAX_CONTROL_BYTES = 32 * 1024 * 1024
READ_CHUNK_BYTES = 1024 * 1024

EXPECTED_PHASE_BOUNDARY = {
    "does_not_read_live_codex_home": True,
    "does_not_modify_raw_archive": True,
    "does_not_modify_canonical_derived": True,
    "does_not_fetch_or_push": True,
    "does_not_deploy": True,
    "does_not_start_s08": True,
    "next_task": "S08-P1-T1",
}

EXPECTED_CONTRACT = {
    "schema_version": CONTRACT_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "source_id": "codex",
    "archive": {
        "required_kind": "baseline",
        "archive_id_required": True,
        "verifier": "verify_codex_public_raw_archive",
        "restore_entrypoint": "restore.sh",
        "source_manifest_member": SOURCE_MANIFEST_MEMBER,
        "immutable_source_required": True,
        "materialization": "verified_byte_copy",
    },
    "workspace": {
        "absolute_path_required": True,
        "existing_empty_directory_required": True,
        "symlink_components_forbidden": True,
        "independent_rehearsals": 2,
        "sequential_cleanup": True,
        "retained_runtime_data": False,
    },
    "isolation": {
        "user_home_allowed": False,
        "user_codex_home_allowed": False,
        "network_required": False,
        "canonical_cache_allowed": False,
        "isolated_raw_registration": "canonical_index_and_exact_ledger_row",
        "subprocess_environment": "empty_allowlist_with_task_owned_home",
    },
    "rebuild": {
        "builder": "build_codex_derived",
        "input_archive_count": 1,
        "expected_initial_outcome": "BUILT_FROM_IMMUTABLE_RAW",
        "expected_replay_outcome": "NO_CHANGES",
        "output_hash_algorithm": "sha256",
        "output_hashes_must_match_between_runs": True,
        "event_provenance_must_match_restored_members": True,
    },
    "proof": {
        "machine_readable": True,
        "absolute_paths_forbidden": True,
        "restored_inventory_required": True,
        "full_event_provenance_coverage_required": True,
        "source_archive_before_after_verification_required": True,
        "workspace_empty_after_required": True,
    },
    "model_parameters_ref": MODEL_PARAMETERS_PATH.as_posix(),
    "phase_boundary": EXPECTED_PHASE_BOUNDARY,
}

EXPECTED_MODEL_PARAMETERS = {
    "schema_version": MODEL_SCHEMA_VERSION,
    "task_id": TASK_ID,
    "acceptance_id": ACCEPTANCE_ID,
    "model_id": "MOD-008",
    "formula_id": "FORM-008",
    "purpose": (
        "Prove that one immutable baseline Codex archive can restore and "
        "deterministically rebuild the derived snapshot without live Codex "
        "state or an online platform."
    ),
    "parameters": {
        "independent_rehearsal_count": 2,
        "minimum_free_space_bytes": 1_073_741_824,
        "free_space_safety_margin_bytes": 536_870_912,
        "archive_copy_multiplier": 2,
        "restore_timeout_seconds": 1800,
        "subprocess_output_max_bytes": 65_536,
        "provenance_coverage_required": 1,
        "hash_algorithm": "sha256",
    },
    "space_formula": (
        "required_free_bytes = max(minimum_free_space_bytes, source_total_bytes + "
        "package_bytes*archive_copy_multiplier + free_space_safety_margin_bytes)"
    ),
    "formula": (
        "pass = archive_verified AND empty_start[1..2] AND "
        "restore_verified[1..2] AND derived_rebuilt[1..2] AND "
        "provenance_coverage=1 AND output_hashes_run_1=output_hashes_run_2 "
        "AND replay_no_changes[1..2] AND source_unchanged AND "
        "no_live_or_remote_dependency"
    ),
    "parameter_rationale": {
        "independent_rehearsal_count": (
            "Two sequential empty-directory runs distinguish deterministic rebuild "
            "evidence from a single successful execution."
        ),
        "free_space_safety_margin_bytes": (
            "A 512 MiB margin covers derived outputs and filesystem overhead beyond "
            "the conservative source and package estimate."
        ),
        "archive_copy_multiplier": (
            "Two package-sized allocations cover the isolated archive copy and "
            "restore staging package without hardlinking canonical files."
        ),
        "restore_timeout_seconds": (
            "Thirty minutes bounds a large local archive restore while remaining "
            "independent of network availability."
        ),
    },
    "failure_semantics": (
        "Archive, workspace, space, subprocess, restore inventory, derived output, "
        "provenance, determinism, cleanup, source immutability, or isolation "
        "uncertainty fails closed and never performs a remote action."
    ),
    "calibration_boundary": (
        "This proof validates deterministic local recoverability for one registered "
        "baseline archive. It does not install a scheduler, sync live Codex state, "
        "fetch, push, deploy, or start S08."
    ),
}


class CodexRestoreProofError(ValueError):
    """Raised when local archive recoverability cannot be proven."""

    def __init__(self, code: str, message: str | None = None) -> None:
        super().__init__(message or code)
        self.code = code


def _same_file_identity(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
        left.st_ctime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
        right.st_ctime_ns,
    )


def _read_regular_bytes(path: Path, *, max_bytes: int, code: str) -> bytes:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CodexRestoreProofError(code) from exc
    if not stat.S_ISREG(metadata.st_mode) or metadata.st_size > max_bytes:
        raise CodexRestoreProofError(code)
    try:
        payload = path.read_bytes()
    except OSError as exc:
        raise CodexRestoreProofError(code) from exc
    try:
        after = path.lstat()
    except OSError as exc:
        raise CodexRestoreProofError(code) from exc
    if not _same_file_identity(metadata, after):
        raise CodexRestoreProofError(code)
    return payload


def _load_json(path: Path, code: str) -> dict[str, Any]:
    try:
        payload = json.loads(
            _read_regular_bytes(path, max_bytes=MAX_CONTROL_BYTES, code=code).decode(
                "utf-8"
            )
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CodexRestoreProofError(code) from exc
    if not isinstance(payload, dict):
        raise CodexRestoreProofError(code)
    return payload


def validate_codex_restore_proof_contract(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_CONTRACT:
        raise CodexRestoreProofError("codex_restore_proof_contract_invalid")
    return payload


def load_codex_restore_proof_contract(database_dir: Path) -> dict[str, Any]:
    return validate_codex_restore_proof_contract(
        _load_json(
            database_dir.resolve() / CONTRACT_PATH,
            "codex_restore_proof_contract_unreadable",
        )
    )


def validate_codex_restore_proof_model_parameters(payload: Any) -> dict[str, Any]:
    if payload != EXPECTED_MODEL_PARAMETERS:
        raise CodexRestoreProofError("codex_restore_proof_model_invalid")
    return payload


def load_codex_restore_proof_model_parameters(database_dir: Path) -> dict[str, Any]:
    return validate_codex_restore_proof_model_parameters(
        _load_json(
            database_dir.resolve() / MODEL_PARAMETERS_PATH,
            "codex_restore_proof_model_unreadable",
        )
    )


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    try:
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise CodexRestoreProofError("restore_proof_file_unsafe")
        with path.open("rb") as handle:
            while chunk := handle.read(READ_CHUNK_BYTES):
                digest.update(chunk)
                size += len(chunk)
        after = path.lstat()
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_file_unreadable") from exc
    if not _same_file_identity(before, after) or size != before.st_size:
        raise CodexRestoreProofError("restore_proof_file_changed")
    return digest.hexdigest(), size


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _safe_relative(value: Any, code: str, *, prefix: str | None = None) -> str:
    if not isinstance(value, str) or not value or "\\" in value or "\x00" in value:
        raise CodexRestoreProofError(code)
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise CodexRestoreProofError(code)
    if path.as_posix() != value or (prefix is not None and not value.startswith(prefix)):
        raise CodexRestoreProofError(code)
    return value


def _validate_workspace(database_dir: Path, workspace_root: Path) -> Path:
    if not workspace_root.is_absolute():
        raise CodexRestoreProofError("restore_proof_workspace_not_absolute")
    lexical = Path(os.path.abspath(os.fspath(workspace_root)))
    try:
        resolved = workspace_root.resolve(strict=True)
        metadata = workspace_root.lstat()
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_workspace_unsafe") from exc
    if lexical != resolved or not stat.S_ISDIR(metadata.st_mode):
        raise CodexRestoreProofError("restore_proof_workspace_unsafe")
    database = database_dir.resolve()
    if resolved == database or resolved in database.parents or database in resolved.parents:
        raise CodexRestoreProofError("restore_proof_workspace_overlaps_database")
    try:
        if any(resolved.iterdir()):
            raise CodexRestoreProofError("restore_proof_workspace_not_empty")
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_workspace_unsafe") from exc
    return resolved


def _copy_regular(source: Path, target: Path) -> None:
    try:
        metadata = source.lstat()
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_source_copy_failed") from exc
    if not stat.S_ISREG(metadata.st_mode):
        raise CodexRestoreProofError("restore_proof_source_copy_failed")
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with source.open("rb") as reader, target.open("xb") as writer:
            while chunk := reader.read(READ_CHUNK_BYTES):
                writer.write(chunk)
            writer.flush()
            os.fsync(writer.fileno())
        os.chmod(target, 0o600)
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_source_copy_failed") from exc
    source_hash, source_size = _sha256_file(source)
    target_hash, target_size = _sha256_file(target)
    if (source_hash, source_size) != (target_hash, target_size):
        raise CodexRestoreProofError("restore_proof_source_copy_mismatch")


def _copy_tree(source: Path, target: Path) -> int:
    try:
        if source.is_symlink() or not source.is_dir():
            raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
        target.mkdir(parents=True, mode=0o700)
        files = 0
        for current, directories, filenames in os.walk(source, followlinks=False):
            current_path = Path(current)
            if current_path.is_symlink():
                raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
            relative = current_path.relative_to(source)
            for name in directories:
                candidate = current_path / name
                if candidate.is_symlink():
                    raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
                (target / relative / name).mkdir(mode=0o700)
            for name in filenames:
                candidate = current_path / name
                if candidate.is_symlink():
                    raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
                _copy_regular(candidate, target / relative / name)
                files += 1
        return files
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_archive_source_unsafe") from exc


def _selected_ledger_line(
    database_dir: Path,
    verification: dict[str, Any],
) -> bytes:
    raw_manifest_path = database_dir / str(verification["raw_manifest_path"])
    public_index_path = database_dir / str(verification["public_index_path"])
    try:
        ledger_relative = public_index_path.relative_to(
            database_dir / PUBLIC_RAW_ROOT
        ).as_posix()
    except ValueError as exc:
        raise CodexRestoreProofError("restore_proof_public_index_path_invalid") from exc
    index_hash, index_size = _sha256_file(public_index_path)
    if index_hash != verification.get("public_index_sha256"):
        raise CodexRestoreProofError("restore_proof_public_index_hash_mismatch")
    payload = _read_regular_bytes(
        raw_manifest_path,
        max_bytes=MAX_CONTROL_BYTES,
        code="restore_proof_raw_manifest_unreadable",
    )
    matches: list[bytes] = []
    for line in payload.splitlines(keepends=True):
        if not line.strip():
            continue
        try:
            row = json.loads(line.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CodexRestoreProofError("restore_proof_raw_manifest_invalid") from exc
        if (
            isinstance(row, dict)
            and row.get("source_id") == "codex"
            and row.get("relative_path") == ledger_relative
            and row.get("sha256") == index_hash
            and row.get("size_bytes") == index_size
        ):
            matches.append(line if line.endswith(b"\n") else line + b"\n")
    if len(matches) != 1:
        raise CodexRestoreProofError("restore_proof_raw_registration_missing")
    return matches[0]


def _write_exclusive(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    try:
        with path.open("xb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(path, 0o600)
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_isolated_write_failed") from exc


def _prepare_isolated_database(
    database_dir: Path,
    archive_id: str,
    run_root: Path,
    verification: dict[str, Any],
) -> Path:
    isolated = run_root / "database"
    isolated.mkdir(mode=0o700)
    for relative in (
        CODEX_DERIVED_CONTRACT_PATH,
        RAW_LEDGER_CONTRACT_PATH,
        CODEX_DERIVED_MODEL_PATH,
    ):
        _copy_regular(database_dir / relative, isolated / relative)
    source_archive = database_dir / ARCHIVE_ROOT / archive_id
    copied_file_count = _copy_tree(
        source_archive,
        isolated / ARCHIVE_ROOT / archive_id,
    )
    if copied_file_count < 4:
        raise CodexRestoreProofError("restore_proof_archive_copy_incomplete")
    public_index_relative = Path(str(verification["public_index_path"]))
    _copy_regular(
        database_dir / public_index_relative,
        isolated / public_index_relative,
    )
    ledger_line = _selected_ledger_line(database_dir, verification)
    raw_manifest_relative = Path(str(verification["raw_manifest_path"]))
    _write_exclusive(isolated / raw_manifest_relative, ledger_line)
    _write_exclusive(isolated / LEDGER_PATH, ledger_line)
    try:
        isolated_verification = verify_codex_public_raw_archive(
            isolated,
            archive_id,
            require_public_registration=True,
        )
    except (CodexPublicRawArchiveError, OSError) as exc:
        raise CodexRestoreProofError("restore_proof_isolated_archive_invalid") from exc
    for key in ("manifest_sha256", "package_sha256", "package_bytes", "part_count"):
        if isolated_verification.get(key) != verification.get(key):
            raise CodexRestoreProofError("restore_proof_isolated_archive_mismatch")
    return isolated


def _restore_environment(run_root: Path) -> dict[str, str]:
    home = run_root / "isolated-home"
    codex_home = home / ".codex"
    tmp = run_root / "tmp"
    cache = run_root / "cache"
    config = run_root / "config"
    data = run_root / "data"
    for path in (home, codex_home, tmp, cache, config, data):
        path.mkdir(parents=True, mode=0o700, exist_ok=True)
    return {
        "HOME": str(home),
        "CODEX_HOME": str(codex_home),
        "TMPDIR": str(tmp),
        "XDG_CACHE_HOME": str(cache),
        "XDG_CONFIG_HOME": str(config),
        "XDG_DATA_HOME": str(data),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONNOUSERSITE": "1",
        "LANG": "C",
        "LC_ALL": "C",
    }


def _run_restore(
    isolated: Path,
    archive_id: str,
    run_root: Path,
    package_sha256: str,
    model: dict[str, Any],
) -> Path:
    archive = isolated / ARCHIVE_ROOT / archive_id
    script = archive / "restore.sh"
    output = run_root / "restored"
    try:
        process = subprocess.run(
            ["/bin/bash", str(script), str(output)],
            cwd=run_root,
            env=_restore_environment(run_root),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=int(model["parameters"]["restore_timeout_seconds"]),
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise CodexRestoreProofError("restore_proof_subprocess_failed") from exc
    output_limit = int(model["parameters"]["subprocess_output_max_bytes"])
    if len(process.stdout) > output_limit or len(process.stderr) > output_limit:
        raise CodexRestoreProofError("restore_proof_subprocess_output_unbounded")
    expected_stdout = f"PASS {package_sha256}\n".encode("ascii")
    if process.returncode != 0 or process.stdout != expected_stdout or process.stderr:
        raise CodexRestoreProofError("restore_proof_restore_failed")
    if output.is_symlink() or not output.is_dir():
        raise CodexRestoreProofError("restore_proof_output_missing")
    return output


def _verify_restored_tree(
    restored: Path,
    archive_id: str,
) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    manifest_path = restored / SOURCE_MANIFEST_MEMBER
    manifest = _load_json(manifest_path, "restore_proof_source_manifest_invalid")
    files = manifest.get("files")
    if (
        manifest.get("archive_id") != archive_id
        or manifest.get("source_id") != "codex"
        or not isinstance(files, list)
        or not files
    ):
        raise CodexRestoreProofError("restore_proof_source_manifest_invalid")
    by_source: dict[str, dict[str, Any]] = {}
    expected_inventory = {
        SOURCE_MANIFEST_MEMBER,
        "codex/_memory_atlas/README.md",
    }
    inventory_rows: list[tuple[str, int, str]] = []
    restored_total_bytes = 0
    for position, item in enumerate(files):
        if not isinstance(item, dict):
            raise CodexRestoreProofError("restore_proof_source_manifest_invalid")
        source_relative = _safe_relative(
            item.get("source_relative_path"),
            "restore_proof_source_manifest_invalid",
        )
        member = _safe_relative(
            item.get("archive_member"),
            "restore_proof_source_manifest_invalid",
            prefix="codex/",
        )
        if member != f"codex/{source_relative}" or source_relative in by_source:
            raise CodexRestoreProofError("restore_proof_source_manifest_invalid")
        expected_inventory.add(member)
        path = restored / member
        digest, size = _sha256_file(path)
        if digest != item.get("archive_sha256") or size != item.get("archive_size_bytes"):
            raise CodexRestoreProofError("restore_proof_restored_member_mismatch")
        source_sha256 = item.get("source_sha256")
        if not _is_sha256(source_sha256) or not _is_sha256(item.get("archive_sha256")):
            raise CodexRestoreProofError("restore_proof_source_manifest_invalid")
        by_source[source_relative] = item
        inventory_rows.append((member, size, digest))
        restored_total_bytes += size
    actual_inventory: set[str] = set()
    for current, directories, filenames in os.walk(restored, followlinks=False):
        current_path = Path(current)
        if current_path.is_symlink():
            raise CodexRestoreProofError("restore_proof_output_unsafe")
        for name in directories:
            if (current_path / name).is_symlink():
                raise CodexRestoreProofError("restore_proof_output_unsafe")
        for name in filenames:
            path = current_path / name
            if path.is_symlink() or not path.is_file():
                raise CodexRestoreProofError("restore_proof_output_unsafe")
            actual_inventory.add(path.relative_to(restored).as_posix())
    if actual_inventory != expected_inventory:
        raise CodexRestoreProofError("restore_proof_restored_inventory_mismatch")
    inventory_digest = hashlib.sha256()
    for member, size, digest in sorted(inventory_rows):
        inventory_digest.update(f"{member}\0{size}\0{digest}\n".encode("utf-8"))
    return by_source, {
        "restored_file_count": len(actual_inventory),
        "restored_data_file_count": len(files),
        "restored_total_bytes": restored_total_bytes,
        "restored_inventory_sha256": inventory_digest.hexdigest(),
    }


def _derived_output_hashes(isolated: Path) -> dict[str, dict[str, Any]]:
    output: dict[str, dict[str, Any]] = {}
    for relative in sorted(EXPECTED_OUTPUTS.values()):
        digest, size = _sha256_file(isolated / relative)
        output[relative] = {"sha256": digest, "byte_size": size}
    return output


def _verify_event_provenance(
    isolated: Path,
    source_files: dict[str, dict[str, Any]],
    archive_id: str,
    verification: dict[str, Any],
) -> int:
    events_path = isolated / EXPECTED_OUTPUTS["events"]
    payload = _read_regular_bytes(
        events_path,
        max_bytes=256 * 1024 * 1024,
        code="restore_proof_events_unreadable",
    )
    verified = 0
    seen: set[str] = set()
    for line_number, line in enumerate(payload.decode("utf-8").splitlines(), start=1):
        if not line:
            continue
        try:
            event = json.loads(line)
        except json.JSONDecodeError as exc:
            raise CodexRestoreProofError(
                "restore_proof_event_invalid", f"invalid event row {line_number}"
            ) from exc
        if not isinstance(event, dict):
            raise CodexRestoreProofError("restore_proof_event_invalid")
        source_relative = event.get("source_relative_path")
        provenance = event.get("provenance")
        item = source_files.get(str(source_relative))
        if (
            item is None
            or not isinstance(provenance, dict)
            or source_relative in seen
            or provenance.get("archive_id") != archive_id
            or provenance.get("archive_manifest_sha256")
            != verification.get("manifest_sha256")
            or provenance.get("archive_member") != item.get("archive_member")
            or provenance.get("archive_member_sha256") != item.get("archive_sha256")
            or provenance.get("source_relative_path") != source_relative
            or provenance.get("source_sha256") != item.get("source_sha256")
            or provenance.get("source_manifest_member") != SOURCE_MANIFEST_MEMBER
        ):
            raise CodexRestoreProofError("restore_proof_event_provenance_mismatch")
        seen.add(str(source_relative))
        verified += 1
    if verified == 0:
        raise CodexRestoreProofError("restore_proof_event_provenance_missing")
    return verified


def _run_rehearsal(
    database_dir: Path,
    archive_id: str,
    workspace: Path,
    run_number: int,
    verification: dict[str, Any],
    model: dict[str, Any],
) -> dict[str, Any]:
    run_root = workspace / f"run-{run_number}"
    empty_start = not any(run_root.iterdir())
    if not empty_start:
        raise CodexRestoreProofError("restore_proof_run_not_empty")
    isolated = _prepare_isolated_database(
        database_dir,
        archive_id,
        run_root,
        verification,
    )
    restored = _run_restore(
        isolated,
        archive_id,
        run_root,
        str(verification["package_sha256"]),
        model,
    )
    source_files, restore_evidence = _verify_restored_tree(restored, archive_id)
    try:
        build_result = build_codex_derived(isolated)
    except (CodexDerivedError, OSError) as exc:
        raise CodexRestoreProofError("restore_proof_derived_rebuild_failed") from exc
    if (
        build_result.get("status") != "PASS"
        or build_result.get("outcome") != "BUILT_FROM_IMMUTABLE_RAW"
        or build_result.get("input_archive_count") != 1
        or build_result.get("parsed_archive_count") != 1
        or build_result.get("writes_files") is not True
    ):
        raise CodexRestoreProofError("restore_proof_derived_rebuild_failed")
    output_hashes = _derived_output_hashes(isolated)
    verified_events = _verify_event_provenance(
        isolated,
        source_files,
        archive_id,
        verification,
    )
    if verified_events != build_result.get("event_count"):
        raise CodexRestoreProofError("restore_proof_provenance_coverage_incomplete")
    try:
        replay = build_codex_derived(isolated)
    except (CodexDerivedError, OSError) as exc:
        raise CodexRestoreProofError("restore_proof_replay_failed") from exc
    if (
        replay.get("status") != "PASS"
        or replay.get("outcome") != "NO_CHANGES"
        or replay.get("writes_files") is not False
        or replay.get("parsed_archive_count") != 0
        or _derived_output_hashes(isolated) != output_hashes
    ):
        raise CodexRestoreProofError("restore_proof_replay_not_idempotent")
    return {
        "run_number": run_number,
        "empty_start": empty_start,
        "archive_materialization": "verified_byte_copy",
        "restore_verified": True,
        **restore_evidence,
        "initial_outcome": str(build_result["outcome"]),
        "replay_outcome": str(replay["outcome"]),
        "event_count": int(build_result["event_count"]),
        "facet_count": int(build_result["facet_count"]),
        "verified_event_count": verified_events,
        "derived_output_hashes": output_hashes,
        "isolated_home": True,
        "network_required": False,
    }


def _directory_identity(path: Path) -> tuple[int, int]:
    try:
        metadata = path.lstat()
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_run_identity_unreadable") from exc
    if not stat.S_ISDIR(metadata.st_mode):
        raise CodexRestoreProofError("restore_proof_run_identity_unsafe")
    return int(metadata.st_dev), int(metadata.st_ino)


def _cleanup_owned_run(
    workspace: Path,
    run_root: Path,
    expected_identity: tuple[int, int],
) -> None:
    try:
        if (
            run_root.parent != workspace
            or run_root.is_symlink()
            or _directory_identity(run_root) != expected_identity
        ):
            raise CodexRestoreProofError("restore_proof_cleanup_unsafe")
        shutil.rmtree(run_root)
        if run_root.exists():
            raise CodexRestoreProofError("restore_proof_cleanup_failed")
    except CodexRestoreProofError:
        raise
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_cleanup_failed") from exc


def _run_signature(run: dict[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in run.items() if key != "run_number"}


def _archive_tree_identity(root: Path) -> dict[str, tuple[int, int, int, int, int, int]]:
    if root.is_symlink() or not root.is_dir():
        raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
    result: dict[str, tuple[int, int, int, int, int, int]] = {}
    try:
        for path in sorted(root.rglob("*")):
            metadata = path.lstat()
            if stat.S_ISLNK(metadata.st_mode):
                raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
            if stat.S_ISREG(metadata.st_mode):
                result[path.relative_to(root).as_posix()] = (
                    int(metadata.st_dev),
                    int(metadata.st_ino),
                    int(metadata.st_mode),
                    int(metadata.st_size),
                    int(metadata.st_mtime_ns),
                    int(metadata.st_ctime_ns),
                )
    except OSError as exc:
        raise CodexRestoreProofError("restore_proof_archive_source_unsafe") from exc
    if not result:
        raise CodexRestoreProofError("restore_proof_archive_source_unsafe")
    return result


def build_codex_restore_proof(
    database_dir: Path,
    archive_id: str,
    workspace_root: Path,
) -> dict[str, Any]:
    database = database_dir.resolve()
    contract = load_codex_restore_proof_contract(database)
    model = load_codex_restore_proof_model_parameters(database)
    workspace = _validate_workspace(database, workspace_root)
    archive_source = database / ARCHIVE_ROOT / archive_id
    source_identity_before = _archive_tree_identity(archive_source)
    try:
        verification_before = verify_codex_public_raw_archive(
            database,
            archive_id,
            require_public_registration=True,
        )
    except (CodexPublicRawArchiveError, OSError) as exc:
        raise CodexRestoreProofError("restore_proof_source_archive_invalid") from exc
    manifest = _load_json(
        database / ARCHIVE_ROOT / archive_id / "manifest.json",
        "restore_proof_archive_manifest_invalid",
    )
    public_index = _load_json(
        database / str(verification_before["public_index_path"]),
        "restore_proof_public_index_invalid",
    )
    if (
        manifest.get("schema_version") != BASELINE_MANIFEST_SCHEMA
        or public_index.get("schema_version") != BASELINE_INDEX_SCHEMA
        or public_index.get("archive_id") != archive_id
    ):
        raise CodexRestoreProofError("restore_proof_baseline_archive_required")
    parameters = model["parameters"]
    source_total_bytes = int(manifest["source_proof"]["source_total_bytes"])
    package_bytes = int(verification_before["package_bytes"])
    required_free_bytes = max(
        int(parameters["minimum_free_space_bytes"]),
        source_total_bytes
        + package_bytes * int(parameters["archive_copy_multiplier"])
        + int(parameters["free_space_safety_margin_bytes"]),
    )
    rehearsals: list[dict[str, Any]] = []
    rehearsal_count = int(parameters["independent_rehearsal_count"])
    for run_number in range(1, rehearsal_count + 1):
        try:
            free_bytes = shutil.disk_usage(workspace).free
        except OSError as exc:
            raise CodexRestoreProofError("restore_proof_space_check_failed") from exc
        if free_bytes < required_free_bytes:
            raise CodexRestoreProofError("restore_proof_insufficient_free_space")
        run_root = workspace / f"run-{run_number}"
        try:
            run_root.mkdir(mode=0o700)
        except OSError as exc:
            raise CodexRestoreProofError("restore_proof_run_create_failed") from exc
        run_identity = _directory_identity(run_root)
        try:
            result = _run_rehearsal(
                database,
                archive_id,
                workspace,
                run_number,
                verification_before,
                model,
            )
        finally:
            _cleanup_owned_run(workspace, run_root, run_identity)
        result["cleanup_verified"] = True
        rehearsals.append(result)
    if len(rehearsals) != rehearsal_count or any(workspace.iterdir()):
        raise CodexRestoreProofError("restore_proof_workspace_cleanup_incomplete")
    try:
        verification_after = verify_codex_public_raw_archive(
            database,
            archive_id,
            require_public_registration=True,
        )
    except (CodexPublicRawArchiveError, OSError) as exc:
        raise CodexRestoreProofError("restore_proof_source_archive_changed") from exc
    immutable_keys = ("manifest_sha256", "package_sha256", "package_bytes", "part_count")
    if any(
        verification_before.get(key) != verification_after.get(key)
        for key in immutable_keys
    ) or _archive_tree_identity(archive_source) != source_identity_before:
        raise CodexRestoreProofError("restore_proof_source_archive_changed")
    signatures = [_run_signature(run) for run in rehearsals]
    runs_equal = all(signature == signatures[0] for signature in signatures[1:])
    output_hashes_equal = all(
        run["derived_output_hashes"] == rehearsals[0]["derived_output_hashes"]
        for run in rehearsals[1:]
    )
    if not runs_equal or not output_hashes_equal:
        raise CodexRestoreProofError("restore_proof_not_deterministic")
    event_count = int(rehearsals[0]["event_count"])
    verified_event_count = int(rehearsals[0]["verified_event_count"])
    coverage = verified_event_count / event_count if event_count else 0
    if coverage != float(parameters["provenance_coverage_required"]):
        raise CodexRestoreProofError("restore_proof_provenance_coverage_incomplete")
    contract_hash, _contract_bytes = _sha256_file(database / CONTRACT_PATH)
    model_hash, _model_bytes = _sha256_file(database / MODEL_PARAMETERS_PATH)
    return {
        "schema_version": RESULT_SCHEMA_VERSION,
        "status": "PASS",
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "contract_sha256": contract_hash,
        "model_parameters_sha256": model_hash,
        "archive": {
            "source_id": "codex",
            "kind": "baseline",
            "archive_id": archive_id,
            "manifest_sha256": verification_before["manifest_sha256"],
            "package_sha256": verification_before["package_sha256"],
            "package_bytes": package_bytes,
            "part_count": int(verification_before["part_count"]),
            "source_unchanged": True,
        },
        "space": {
            "required_free_bytes": required_free_bytes,
            "source_total_bytes": source_total_bytes,
            "package_bytes": package_bytes,
            "sequential_rehearsals": True,
        },
        "rehearsal_count": rehearsal_count,
        "rehearsals": rehearsals,
        "derived": {
            "event_count": event_count,
            "facet_count": int(rehearsals[0]["facet_count"]),
            "output_hashes": rehearsals[0]["derived_output_hashes"],
        },
        "provenance": {
            "verified_event_count": verified_event_count,
            "coverage_ratio": coverage,
            "restored_member_binding": "PASS",
        },
        "determinism": {
            "proof_runs_equal": runs_equal,
            "output_hashes_equal": output_hashes_equal,
            "replay_no_changes": True,
        },
        "isolation": {
            "user_home_read": False,
            "user_codex_home_read": False,
            "canonical_cache_read": False,
            "network_required": False,
            "isolated_registration": "canonical_index_and_exact_ledger_row",
        },
        "cleanup": {
            "workspace_empty_after": True,
            "retained_runtime_data": False,
        },
        "effects": {
            "raw_mutation": False,
            "canonical_derived_mutation": False,
            "remote_push": False,
            "deployment": False,
        },
        "phase_boundary": EXPECTED_PHASE_BOUNDARY,
    }


def run_codex_restore_proof(args: argparse.Namespace) -> int:
    try:
        result = build_codex_restore_proof(
            Path(args.database_dir),
            str(args.archive_id),
            Path(args.workspace_root),
        )
        output = getattr(args, "output", None)
        payload = json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        if output is not None:
            output_path = Path(output)
            if output_path.exists() or output_path.is_symlink():
                raise CodexRestoreProofError("restore_proof_output_exists")
            try:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with output_path.open("x", encoding="utf-8") as handle:
                    handle.write(payload)
                    handle.flush()
                    os.fsync(handle.fileno())
            except OSError as exc:
                raise CodexRestoreProofError("restore_proof_output_write_failed") from exc
        print(payload, end="")
        return 0
    except CodexRestoreProofError as exc:
        print(
            json.dumps(
                {
                    "schema_version": RESULT_SCHEMA_VERSION,
                    "status": "FAIL",
                    "task_id": TASK_ID,
                    "acceptance_id": ACCEPTANCE_ID,
                    "error_code": exc.code,
                    "reason": str(exc),
                    "raw_mutation": False,
                    "remote_push": False,
                    "deployment": False,
                },
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
        )
        return 2


__all__ = (
    "ACCEPTANCE_ID",
    "CONTRACT_PATH",
    "EXPECTED_CONTRACT",
    "EXPECTED_MODEL_PARAMETERS",
    "EXPECTED_PHASE_BOUNDARY",
    "MODEL_PARAMETERS_PATH",
    "RESULT_SCHEMA_VERSION",
    "TASK_ID",
    "CodexRestoreProofError",
    "build_codex_restore_proof",
    "load_codex_restore_proof_contract",
    "load_codex_restore_proof_model_parameters",
    "run_codex_restore_proof",
    "validate_codex_restore_proof_contract",
    "validate_codex_restore_proof_model_parameters",
)
