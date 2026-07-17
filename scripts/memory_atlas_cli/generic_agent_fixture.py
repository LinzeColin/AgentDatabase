"""Isolated end-to-end acceptance fixture for one standard generic Agent source."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import stat
from pathlib import Path, PurePosixPath
from typing import Any, Mapping

from memory_atlas_cli.archive_chunking import (
    CONTRACT_PATH as ARCHIVE_CHUNKING_CONTRACT_PATH,
    ArchiveChunkError,
    chunk_archive_package,
)
from memory_atlas_cli.archive_restore import (
    CONTRACT_PATH as ARCHIVE_RESTORE_CONTRACT_PATH,
    ArchiveRestoreError,
    restore_archive,
    verify_archive,
)
from memory_atlas_cli.raw_ledger import RAW_LEDGER_CONTRACT_PATH, RawLedgerError
from memory_atlas_cli.source_registry import (
    PUSH_DEFAULTS,
    SourceRegistryError,
    load_source_registry,
    sync_source_map,
    validate_source_registry,
)


SCHEMA_VERSION = "memory_atlas.generic_agent_fixture.v1_2_1_s09_p2_t2"
RESULT_SCHEMA_VERSION = "memory_atlas.generic_agent_fixture_result.v1_2_1_s09_p2_t2"
BUNDLE_SCHEMA_VERSION = "memory_atlas.generic_agent_fixture_bundle.v1_2_1_s09_p2_t2"
TASK_ID = "S09-P2-T2"
ACCEPTANCE_ID = "ACC-MA-V121-S09-P2-T2"
CONTRACT_PATH = Path("config/data_sources/generic_agent_fixture.json")
MODEL_PATH = Path("机器治理/参数与公式/generic_agent_fixture.v1_2_1_s09_p2_t2.json")
ENTRYPOINT_PATH = Path("scripts/verify_memory_atlas_generic_agent_fixture.py")
FIXTURE_INPUT_PATH = Path("tests/fixtures/memory_atlas/generic_agent_standard/events.jsonl")
PARSER_ENTRYPOINT = Path("scripts/sync_future_agent_data.py")
READ_ADAPTER_ENTRYPOINT = Path("scripts/inspect_memory_atlas_generic_agent_export.py")
READ_ADAPTER_CONTRACT_PATH = Path("config/data_sources/generic_agent_read_adapter.json")
RAW_MANIFEST_ENTRYPOINT = Path("scripts/raw_archive_manifest.py")
RAW_MANIFEST_ROOT = Path("机器治理/证据与日志/raw_archive_manifests")
PACKAGE_ROOT = Path(__file__).resolve().parents[2]
EXAMPLE_SOURCE_ID = "standard-agent-example"
FIXED_OBSERVED_AT = "2026-07-17T03:15:00Z"
FIXTURE_INPUT_SHA256 = "df6115c5adf5b37c4b9454266c9ad43b521e0f191d9528bcc7f4b6c6ebfe7f28"
MANIFEST_RUN_ID = "s09-p2-t2-fixture"
ARCHIVE_ID = "s09-p2-t2-fixture-v1"
WORKSPACE_MARKER = ".memory-atlas-s09-p2-t2-fixture-workspace.json"
BUNDLE_FILENAME = "fixture-recovery-bundle.json"
RESTORED_BUNDLE_FILENAME = "restored-fixture-recovery-bundle.json"
MAX_CONTROL_BYTES = 256 * 1024
MAX_BUNDLE_FILE_BYTES = 8 * 1024 * 1024

EXPECTED_PIPELINE = {
    "parser_entrypoint": PARSER_ENTRYPOINT.as_posix(),
    "read_adapter_entrypoint": READ_ADAPTER_ENTRYPOINT.as_posix(),
    "read_adapter_contract_ref": READ_ADAPTER_CONTRACT_PATH.as_posix(),
    "raw_root_template": "data/public_raw/agents/{source_id}",
    "raw_ledger_contract_ref": RAW_LEDGER_CONTRACT_PATH.as_posix(),
    "raw_manifest_entrypoint": RAW_MANIFEST_ENTRYPOINT.as_posix(),
    "raw_manifest_root": RAW_MANIFEST_ROOT.as_posix(),
    "derived_output_template": "data/derived/agents/{source_id}/agent_sync_summary.json",
    "archive_chunking_contract_ref": ARCHIVE_CHUNKING_CONTRACT_PATH.as_posix(),
    "archive_restore_contract_ref": ARCHIVE_RESTORE_CONTRACT_PATH.as_posix(),
    "archive_root_template": "data/raw_archives/{source_id}/{archive_id}",
    "bundle_schema_version": BUNDLE_SCHEMA_VERSION,
}
EXPECTED_FIXTURE = {
    "synthetic_only": True,
    "input_format": "jsonl",
    "input_sha256": FIXTURE_INPUT_SHA256,
    "expected_event_count": 2,
    "expected_message_count": 3,
    "manifest_run_id": MANIFEST_RUN_ID,
    "archive_id": ARCHIVE_ID,
    "force_archive": True,
    "bundle_file_count": 5,
    "repository_outputs_allowed": False,
}
EXPECTED_SAFETY = {
    "isolated_workspace_required": True,
    "empty_workspace_on_first_run_required": True,
    "owned_replay_only": True,
    "source_read_only": True,
    "package_root_mutation": False,
    "credential_exclusion_required": True,
    "network_access": False,
    "remote_push": False,
    "source_content_in_cli_output": False,
    "local_absolute_path_in_cli_output": False,
}
EXPECTED_PHASE_BOUNDARY = {
    "fixture_runtime_only": True,
    "production_source_data_created": False,
    "plugin_contract_implemented": False,
    "remote_push": False,
    "next_task": "S09-P2-T3",
}


class FixtureAcceptanceError(ValueError):
    """Fail-closed, path-free fixture acceptance error."""


def _read_regular_bytes(path: Path, *, max_bytes: int, code: str) -> bytes:
    descriptor: int | None = None
    try:
        descriptor = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
        before = os.fstat(descriptor)
        if not stat.S_ISREG(before.st_mode) or before.st_size > max_bytes:
            raise FixtureAcceptanceError(code)
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, min(1024 * 1024, max_bytes + 1 - total))
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise FixtureAcceptanceError(code)
            chunks.append(chunk)
        after = os.fstat(descriptor)
    except FixtureAcceptanceError:
        raise
    except OSError as exc:
        raise FixtureAcceptanceError(code) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    before_identity = (
        before.st_dev,
        before.st_ino,
        before.st_mode,
        before.st_size,
        before.st_mtime_ns,
        before.st_ctime_ns,
    )
    after_identity = (
        after.st_dev,
        after.st_ino,
        after.st_mode,
        after.st_size,
        after.st_mtime_ns,
        after.st_ctime_ns,
    )
    if before_identity != after_identity or total != after.st_size:
        raise FixtureAcceptanceError(code)
    return b"".join(chunks)


def _mapping(value: Any, code: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise FixtureAcceptanceError(code)
    return value


def validate_generic_agent_fixture_contract(payload: Any) -> dict[str, Any]:
    contract = _mapping(payload, "fixture_contract_not_object")
    if set(contract) != {
        "schema_version",
        "task_id",
        "acceptance_id",
        "entrypoint",
        "model_ref",
        "fixture_input",
        "example_source_id",
        "fixed_observed_at",
        "pipeline",
        "fixture",
        "main_push_contract",
        "safety",
        "phase_boundary",
    }:
        raise FixtureAcceptanceError("fixture_contract_keys_mismatch")
    identity = {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "entrypoint": ENTRYPOINT_PATH.as_posix(),
        "model_ref": MODEL_PATH.as_posix(),
        "fixture_input": FIXTURE_INPUT_PATH.as_posix(),
        "example_source_id": EXAMPLE_SOURCE_ID,
        "fixed_observed_at": FIXED_OBSERVED_AT,
    }
    if any(contract.get(key) != value for key, value in identity.items()):
        raise FixtureAcceptanceError("fixture_contract_identity_mismatch")
    expected_sections: tuple[tuple[str, Mapping[str, Any]], ...] = (
        ("pipeline", EXPECTED_PIPELINE),
        ("fixture", EXPECTED_FIXTURE),
        ("main_push_contract", PUSH_DEFAULTS),
        ("safety", EXPECTED_SAFETY),
        ("phase_boundary", EXPECTED_PHASE_BOUNDARY),
    )
    for field, expected in expected_sections:
        if contract.get(field) != expected:
            raise FixtureAcceptanceError(f"fixture_contract_{field}_mismatch")
    return contract


def load_generic_agent_fixture_contract(package_root: Path = PACKAGE_ROOT) -> dict[str, Any]:
    try:
        root = package_root.resolve(strict=True)
    except OSError as exc:
        raise FixtureAcceptanceError("package_root_unreadable") from exc
    if not root.is_dir():
        raise FixtureAcceptanceError("package_root_unreadable")
    try:
        payload = json.loads(
            _read_regular_bytes(
                root / CONTRACT_PATH,
                max_bytes=MAX_CONTROL_BYTES,
                code="fixture_contract_unreadable",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureAcceptanceError("fixture_contract_invalid_json") from exc
    contract = validate_generic_agent_fixture_contract(payload)
    for relative in (
        MODEL_PATH,
        ENTRYPOINT_PATH,
        FIXTURE_INPUT_PATH,
        PARSER_ENTRYPOINT,
        READ_ADAPTER_ENTRYPOINT,
        READ_ADAPTER_CONTRACT_PATH,
        RAW_LEDGER_CONTRACT_PATH,
        RAW_MANIFEST_ENTRYPOINT,
        ARCHIVE_CHUNKING_CONTRACT_PATH,
        ARCHIVE_RESTORE_CONTRACT_PATH,
    ):
        try:
            metadata = (root / relative).lstat()
        except OSError as exc:
            raise FixtureAcceptanceError("fixture_dependency_missing") from exc
        if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISREG(metadata.st_mode):
            raise FixtureAcceptanceError("fixture_dependency_not_regular")
    fixture_bytes = _read_regular_bytes(
        root / FIXTURE_INPUT_PATH,
        max_bytes=MAX_BUNDLE_FILE_BYTES,
        code="fixture_input_unreadable",
    )
    if hashlib.sha256(fixture_bytes).hexdigest() != FIXTURE_INPUT_SHA256:
        raise FixtureAcceptanceError("fixture_input_hash_mismatch")
    return contract


def validate_fixture_source(
    registry: Any,
    contract: Mapping[str, Any],
    package_root: Path = PACKAGE_ROOT,
) -> dict[str, Any]:
    if contract.get("main_push_contract") != PUSH_DEFAULTS:
        raise FixtureAcceptanceError("fixture_push_contract_drift")
    try:
        validated = validate_source_registry(registry, package_root.resolve(strict=True))
        source = sync_source_map(validated)[str(contract["example_source_id"])]
    except (KeyError, OSError, SourceRegistryError) as exc:
        raise FixtureAcceptanceError("fixture_source_registry_invalid") from exc
    expected = {
        "source_type": "generic_agent",
        "status": "fixture",
        "raw_paths": ["**/*.jsonl"],
        "state_path": f"data/sync_state/agents/{EXAMPLE_SOURCE_ID}.json",
        "archive_path": f"data/public_raw/agents/{EXAMPLE_SOURCE_ID}",
        "derived_outputs": [
            f"data/derived/agents/{EXAMPLE_SOURCE_ID}/agent_sync_summary.json"
        ],
        "push_policy": PUSH_DEFAULTS,
    }
    if any(source.get(field) != value for field, value in expected.items()):
        raise FixtureAcceptanceError("fixture_source_registry_invalid")
    parser = _mapping(source.get("parser"), "fixture_source_registry_invalid")
    if (
        parser.get("entrypoint") != PARSER_ENTRYPOINT.as_posix()
        or parser.get("read_adapter_entrypoint") != READ_ADAPTER_ENTRYPOINT.as_posix()
        or parser.get("read_adapter_contract_ref") != READ_ADAPTER_CONTRACT_PATH.as_posix()
        or parser.get("input_formats") != ["agent_event_jsonl"]
    ):
        raise FixtureAcceptanceError("fixture_source_registry_invalid")
    discovery = _mapping(source.get("discovery"), "fixture_source_registry_invalid")
    if discovery.get("candidates") != [
        {
            "kind": "environment_variable",
            "value": "MEMORY_ATLAS_STANDARD_AGENT_EXAMPLE_INPUT",
            "target_argument": "--input",
        },
        {"kind": "operator_argument", "value": "--input"},
    ]:
        raise FixtureAcceptanceError("fixture_source_registry_invalid")
    return source


def _canonical_workspace(package_root: Path, workspace_root: Path) -> tuple[Path, bool]:
    try:
        metadata = workspace_root.lstat()
        workspace = workspace_root.resolve(strict=True)
    except OSError as exc:
        raise FixtureAcceptanceError("fixture_workspace_unreadable") from exc
    if stat.S_ISLNK(metadata.st_mode) or not stat.S_ISDIR(metadata.st_mode):
        raise FixtureAcceptanceError("fixture_workspace_unreadable")
    if (
        workspace == package_root
        or package_root in workspace.parents
        or workspace in package_root.parents
    ):
        raise FixtureAcceptanceError("fixture_workspace_overlaps_package_root")
    entries = {path.name for path in workspace.iterdir()}
    if not entries:
        return workspace, False
    allowed = {
        WORKSPACE_MARKER,
        "database",
        BUNDLE_FILENAME,
        RESTORED_BUNDLE_FILENAME,
    }
    if not entries.issubset(allowed) or WORKSPACE_MARKER not in entries:
        raise FixtureAcceptanceError("fixture_workspace_not_owned")
    try:
        marker = json.loads(
            _read_regular_bytes(
                workspace / WORKSPACE_MARKER,
                max_bytes=MAX_CONTROL_BYTES,
                code="fixture_workspace_marker_invalid",
            ).decode("utf-8")
        )
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureAcceptanceError("fixture_workspace_marker_invalid") from exc
    if marker != {
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "source_id": EXAMPLE_SOURCE_ID,
    }:
        raise FixtureAcceptanceError("fixture_workspace_marker_invalid")
    return workspace, True


def _write_identical_or_new(path: Path, payload: bytes, *, mode: int = 0o600) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if os.path.lexists(path):
        existing = _read_regular_bytes(
            path,
            max_bytes=max(MAX_BUNDLE_FILE_BYTES, len(payload)),
            code="fixture_owned_output_conflict",
        )
        if existing != payload:
            raise FixtureAcceptanceError("fixture_owned_output_conflict")
        return False
    descriptor: int | None = None
    try:
        descriptor = os.open(
            path,
            os.O_CREAT | os.O_EXCL | os.O_WRONLY | getattr(os, "O_NOFOLLOW", 0),
            mode,
        )
        view = memoryview(payload)
        while view:
            written = os.write(descriptor, view)
            view = view[written:]
        os.fsync(descriptor)
    except OSError as exc:
        raise FixtureAcceptanceError("fixture_owned_output_write_failed") from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
    return True


def _assert_owned_tree(root: Path) -> None:
    stack = [root]
    while stack:
        directory = stack.pop()
        try:
            entries = list(os.scandir(directory))
        except OSError as exc:
            raise FixtureAcceptanceError("fixture_database_tree_invalid") from exc
        for entry in entries:
            try:
                metadata = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise FixtureAcceptanceError("fixture_database_tree_invalid") from exc
            if stat.S_ISLNK(metadata.st_mode):
                raise FixtureAcceptanceError("fixture_database_tree_invalid")
            if stat.S_ISDIR(metadata.st_mode):
                stack.append(Path(entry.path))
            elif not stat.S_ISREG(metadata.st_mode):
                raise FixtureAcceptanceError("fixture_database_tree_invalid")


def _install_workspace(package_root: Path, workspace: Path, replay: bool) -> Path:
    marker_payload = (
        json.dumps(
            {
                "schema_version": SCHEMA_VERSION,
                "task_id": TASK_ID,
                "source_id": EXAMPLE_SOURCE_ID,
            },
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n"
    ).encode("utf-8")
    _write_identical_or_new(workspace / WORKSPACE_MARKER, marker_payload)
    database = workspace / "database"
    if database.exists():
        if not replay or not database.is_dir() or database.is_symlink():
            raise FixtureAcceptanceError("fixture_database_workspace_invalid")
        _assert_owned_tree(database)
    else:
        database.mkdir(mode=0o700)
    for relative in (
        RAW_LEDGER_CONTRACT_PATH,
        ARCHIVE_CHUNKING_CONTRACT_PATH,
        ARCHIVE_RESTORE_CONTRACT_PATH,
    ):
        payload = _read_regular_bytes(
            package_root / relative,
            max_bytes=MAX_CONTROL_BYTES,
            code="fixture_runtime_contract_unreadable",
        )
        _write_identical_or_new(database / relative, payload)
    return database


def _safe_database_file(database: Path, relative_path: str) -> Path:
    if "\\" in relative_path:
        raise FixtureAcceptanceError("fixture_output_path_invalid")
    relative = PurePosixPath(relative_path)
    if relative.is_absolute() or ".." in relative.parts or "." in relative.parts:
        raise FixtureAcceptanceError("fixture_output_path_invalid")
    target = database.joinpath(*relative.parts)
    try:
        parent = target.parent.resolve(strict=True)
    except OSError as exc:
        raise FixtureAcceptanceError("fixture_output_path_invalid") from exc
    if database not in parent.parents and parent != database:
        raise FixtureAcceptanceError("fixture_output_path_invalid")
    return target


def _bundle_file(database: Path, relative_path: str) -> dict[str, Any]:
    path = _safe_database_file(database, relative_path)
    payload = _read_regular_bytes(
        path,
        max_bytes=MAX_BUNDLE_FILE_BYTES,
        code="fixture_bundle_input_unreadable",
    )
    return {
        "relative_path": relative_path,
        "byte_size": len(payload),
        "sha256": hashlib.sha256(payload).hexdigest(),
        "payload_base64": base64.b64encode(payload).decode("ascii"),
    }


def _bundle_payload(
    contract: Mapping[str, Any],
    source_sha256: str,
    files: list[dict[str, Any]],
) -> bytes:
    payload = {
        "schema_version": BUNDLE_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": EXAMPLE_SOURCE_ID,
        "observed_at": FIXED_OBSERVED_AT,
        "fixture_input_sha256": source_sha256,
        "parser_contract": {
            "entrypoint": contract["pipeline"]["parser_entrypoint"],
            "read_adapter_contract_ref": contract["pipeline"]["read_adapter_contract_ref"],
        },
        "main_push_contract": dict(PUSH_DEFAULTS),
        "files": files,
    }
    return (
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        + "\n"
    ).encode("utf-8")


def _verify_restored_bundle(database: Path, restored_path: Path) -> dict[str, Any]:
    payload = _read_regular_bytes(
        restored_path,
        max_bytes=MAX_BUNDLE_FILE_BYTES,
        code="fixture_restored_bundle_unreadable",
    )
    try:
        bundle = json.loads(payload.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise FixtureAcceptanceError("fixture_restored_bundle_invalid") from exc
    if (
        not isinstance(bundle, dict)
        or bundle.get("schema_version") != BUNDLE_SCHEMA_VERSION
        or bundle.get("source_id") != EXAMPLE_SOURCE_ID
        or bundle.get("main_push_contract") != PUSH_DEFAULTS
    ):
        raise FixtureAcceptanceError("fixture_restored_bundle_invalid")
    files = bundle.get("files")
    if not isinstance(files, list) or len(files) != EXPECTED_FIXTURE["bundle_file_count"]:
        raise FixtureAcceptanceError("fixture_restored_bundle_invalid")
    for item in files:
        if not isinstance(item, dict) or set(item) != {
            "relative_path",
            "byte_size",
            "sha256",
            "payload_base64",
        }:
            raise FixtureAcceptanceError("fixture_restored_bundle_invalid")
        try:
            decoded = base64.b64decode(item["payload_base64"], validate=True)
        except (TypeError, ValueError) as exc:
            raise FixtureAcceptanceError("fixture_restored_bundle_invalid") from exc
        current = _read_regular_bytes(
            _safe_database_file(database, str(item["relative_path"])),
            max_bytes=MAX_BUNDLE_FILE_BYTES,
            code="fixture_restored_file_unreadable",
        )
        if (
            decoded != current
            or len(decoded) != item["byte_size"]
            or hashlib.sha256(decoded).hexdigest() != item["sha256"]
        ):
            raise FixtureAcceptanceError("fixture_restored_file_mismatch")
    return {
        "file_count": len(files),
        "sha256": hashlib.sha256(payload).hexdigest(),
    }


def run_generic_agent_fixture(
    package_root: Path,
    workspace_root: Path,
) -> dict[str, Any]:
    try:
        root = package_root.resolve(strict=True)
    except OSError as exc:
        raise FixtureAcceptanceError("package_root_unreadable") from exc
    if root != PACKAGE_ROOT:
        raise FixtureAcceptanceError("package_root_identity_mismatch")
    contract = load_generic_agent_fixture_contract(root)
    registry = load_source_registry(root)
    source = validate_fixture_source(registry, contract, root)
    fixture_before = _read_regular_bytes(
        root / FIXTURE_INPUT_PATH,
        max_bytes=MAX_BUNDLE_FILE_BYTES,
        code="fixture_input_unreadable",
    )
    workspace, replay = _canonical_workspace(root, workspace_root)
    database = _install_workspace(root, workspace, replay)

    try:
        from raw_archive_manifest import generate_raw_manifest
        from sync_future_agent_data import sync_future_agent

        sync_result = sync_future_agent(
            database,
            EXAMPLE_SOURCE_ID,
            root / FIXTURE_INPUT_PATH,
            False,
            source_id=EXAMPLE_SOURCE_ID,
            generated_at=FIXED_OBSERVED_AT,
        )
        if (
            sync_result.get("event_count") != EXPECTED_FIXTURE["expected_event_count"]
            or sync_result.get("message_count") != EXPECTED_FIXTURE["expected_message_count"]
            or sync_result.get("adapter_source_formats") != ["jsonl"]
        ):
            raise FixtureAcceptanceError("fixture_parser_result_mismatch")
        manifest = generate_raw_manifest(
            database,
            MANIFEST_RUN_ID,
            imported_at=FIXED_OBSERVED_AT,
        )
        raw_paths = [str(value) for value in sync_result["raw_paths"]]
        artifact_paths = sorted(
            raw_paths
            + [
                str(sync_result["derived_summary"]),
                str(manifest["manifest_path"]),
                str(manifest["hash_ledger_path"]),
            ]
        )
        files = [_bundle_file(database, relative_path) for relative_path in artifact_paths]
        if len(files) != EXPECTED_FIXTURE["bundle_file_count"]:
            raise FixtureAcceptanceError("fixture_bundle_file_count_mismatch")
        bundle_payload = _bundle_payload(contract, str(sync_result["source_sha256"]), files)
        bundle_path = workspace / BUNDLE_FILENAME
        _write_identical_or_new(bundle_path, bundle_payload)
        chunk = chunk_archive_package(
            database,
            bundle_path,
            EXAMPLE_SOURCE_ID,
            ARCHIVE_ID,
            force_archive=True,
        )
        verified = verify_archive(database, EXAMPLE_SOURCE_ID, ARCHIVE_ID)
        restored_path = workspace / RESTORED_BUNDLE_FILENAME
        restored = restore_archive(
            database,
            EXAMPLE_SOURCE_ID,
            ARCHIVE_ID,
            restored_path,
        )
        restored_bundle = _verify_restored_bundle(database, restored_path)
    except FixtureAcceptanceError:
        raise
    except (
        ArchiveChunkError,
        ArchiveRestoreError,
        KeyError,
        OSError,
        RawLedgerError,
        SourceRegistryError,
        TypeError,
        ValueError,
    ) as exc:
        raise FixtureAcceptanceError("fixture_pipeline_failed") from exc

    fixture_after = _read_regular_bytes(
        root / FIXTURE_INPUT_PATH,
        max_bytes=MAX_BUNDLE_FILE_BYTES,
        code="fixture_input_unreadable",
    )
    if fixture_after != fixture_before:
        raise FixtureAcceptanceError("fixture_input_changed")
    if source["push_policy"] != contract["main_push_contract"]:
        raise FixtureAcceptanceError("fixture_push_contract_drift")
    bundle_sha256 = hashlib.sha256(bundle_payload).hexdigest()
    if restored_bundle["sha256"] != bundle_sha256:
        raise FixtureAcceptanceError("fixture_restore_hash_mismatch")

    raw_ledger = _mapping(sync_result.get("raw_ledger"), "fixture_raw_ledger_invalid")
    return {
        "status": "PASS",
        "schema_version": RESULT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "acceptance_id": ACCEPTANCE_ID,
        "source_id": EXAMPLE_SOURCE_ID,
        "workspace_persisted": True,
        "parser": {
            "adapter_source_formats": sync_result["adapter_source_formats"],
            "event_count": sync_result["event_count"],
            "message_count": sync_result["message_count"],
            "source_read_only": sync_result["source_read_only"],
        },
        "raw": {
            "file_count": len(raw_paths),
            "ledger_status": raw_ledger["status"],
            "ledger_appended_count": raw_ledger["ledger_appended_count"],
            "ledger_idempotent": raw_ledger["idempotent"],
        },
        "manifest": {
            "status": manifest["status"],
            "source_families": manifest["source_families"],
            "sha256": manifest["manifest_sha256"],
            "idempotent": manifest["idempotent"],
        },
        "derived": {
            "file_count": 1,
            "event_count": sync_result["event_count"],
        },
        "archive": {
            "chunk_status": chunk["status"],
            "verify_status": verified["status"],
            "restore_status": restored["status"],
            "part_count": chunk["part_count"],
            "manifest_sha256": chunk["manifest_sha256"],
            "bundle_sha256": bundle_sha256,
            "restored_sha256": restored_bundle["sha256"],
            "restored_file_count": restored_bundle["file_count"],
            "chunk_idempotent": chunk["idempotent"],
            "restore_idempotent": restored["idempotent"],
        },
        "main_push_contract": dict(PUSH_DEFAULTS),
        "push_executed": False,
        "remote_push": False,
        "plugin_contract_implemented": False,
        "production_database_mutation": False,
        "source_content_in_output": False,
        "local_absolute_path_in_output": False,
    }


__all__ = (
    "ACCEPTANCE_ID",
    "ARCHIVE_ID",
    "CONTRACT_PATH",
    "ENTRYPOINT_PATH",
    "EXAMPLE_SOURCE_ID",
    "FIXTURE_INPUT_PATH",
    "MODEL_PATH",
    "RESULT_SCHEMA_VERSION",
    "SCHEMA_VERSION",
    "TASK_ID",
    "FixtureAcceptanceError",
    "load_generic_agent_fixture_contract",
    "run_generic_agent_fixture",
    "validate_fixture_source",
    "validate_generic_agent_fixture_contract",
)
