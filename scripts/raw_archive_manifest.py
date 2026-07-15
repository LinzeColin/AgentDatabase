#!/usr/bin/env python3
"""Generate and audit Memory Atlas public raw manifest/hash ledgers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

from memory_atlas_cli.raw_ledger import (
    LEDGER_IMMUTABLE_FIELDS,
    LEDGER_PATH,
    RAW_LEDGER_CONTRACT_PATH,
    RAW_ROOT,
    RawLedgerError,
    append_jsonl_immutable,
    guarded_sha256_file,
    ledger_dedupe_key,
    load_raw_ledger_contract,
    raw_ledger_append_lock,
    validate_ledger_row,
)
from memory_atlas_cli.archive_chunking import (
    ArchiveChunkError,
    ArchiveChunkPartialWriteError,
    ArchiveChunkPostPublishError,
    chunk_archive_package,
)

PUBLIC_RAW_ROOT = RAW_ROOT
MANIFEST_ROOT = Path("机器治理/证据与日志/raw_archive_manifests")
HASH_LEDGER_FILE = LEDGER_PATH.name
IGNORED_RAW_NAMES = {".DS_Store", ".gitkeep", "README.md"}
RUN_ID_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]*\Z")
SHALLOW_IMPORT_RE = re.compile(
    r"(?P<source>[a-z0-9][a-z0-9-]{0,63})\.[a-f0-9]{12}\."
    r"(?:part-[0-9]{4}\.md|sidecar\.json)\Z"
)
MONTH_RE = re.compile(r"[0-9]{4}-(?:0[1-9]|1[0-2])\Z")


ManifestConflict = RawLedgerError


def load_database_raw_ledger_contract(database_dir: Path) -> dict[str, Any]:
    return load_raw_ledger_contract(
        database_dir,
        database_dir / RAW_LEDGER_CONTRACT_PATH,
    )


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def sha256_file(path: Path) -> str:
    return str(guarded_sha256_file(path)["sha256"])


def write_text_atomic(path: Path, payload: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        tmp_path.write_text(payload, encoding="utf-8")
        os.replace(tmp_path, path)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def write_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    payload = jsonl_payload(rows)
    write_text_atomic(path, payload)


def jsonl_payload(rows: Iterable[dict[str, Any]]) -> str:
    return "".join(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows)


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, 1):
            text = line.strip()
            if not text:
                continue
            try:
                row = json.loads(text)
            except json.JSONDecodeError as exc:
                raise ManifestConflict(
                    f"invalid JSONL in {path.name} at row {line_number}"
                ) from exc
            if not isinstance(row, dict):
                raise ManifestConflict(
                    f"invalid JSONL object in {path.name} at row {line_number}"
                )
            rows.append(row)
    return rows


def should_include_raw_file(path: Path, raw_root: Path) -> bool:
    if not path.is_file() or path.name in IGNORED_RAW_NAMES:
        return False
    try:
        relative = path.relative_to(raw_root)
    except ValueError:
        return False
    return not any(part.startswith(".") for part in relative.parts)


def iter_public_raw_files(database_dir: Path) -> list[Path]:
    raw_root = database_dir / PUBLIC_RAW_ROOT
    if not raw_root.exists():
        return []
    return sorted(path for path in raw_root.rglob("*") if should_include_raw_file(path, raw_root))


def source_id_for(relative_path: Path) -> str:
    parts = relative_path.parts
    if not parts:
        return "unknown"
    if parts[0] in {"chatgpt", "codex"}:
        return parts[0]
    if parts[0] == "agents" and len(parts) >= 2:
        return f"agent:{parts[1]}"
    if MONTH_RE.fullmatch(parts[0]) and len(parts) == 2:
        match = SHALLOW_IMPORT_RE.fullmatch(parts[1])
        if match:
            return match.group("source")
    return parts[0]


def build_manifest_rows(database_dir: Path, imported_at: str) -> list[dict[str, Any]]:
    raw_root = database_dir / PUBLIC_RAW_ROOT
    rows: list[dict[str, Any]] = []
    for file_path in iter_public_raw_files(database_dir):
        relative_path = file_path.relative_to(raw_root)
        fingerprint = guarded_sha256_file(file_path)
        rows.append(
            {
                "source_id": source_id_for(relative_path),
                "relative_path": relative_path.as_posix(),
                "sha256": fingerprint["sha256"],
                "imported_at": imported_at,
                "size_bytes": fingerprint["size_bytes"],
            }
        )
    return rows


def manifest_path_for(database_dir: Path, run_id: str) -> Path:
    safe_run_id = run_id.strip()
    if run_id != safe_run_id or not RUN_ID_RE.fullmatch(safe_run_id):
        raise ManifestConflict("run_id must use only letters, digits, dot, underscore or hyphen")
    return database_dir / MANIFEST_ROOT / f"raw_manifest.{safe_run_id}.jsonl"


def hash_ledger_path(database_dir: Path) -> Path:
    return database_dir / LEDGER_PATH


def _rows_by_path(rows: list[dict[str, Any]], label: str) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    dedupe_keys: set[str] = set()
    for row in rows:
        validated = validate_ledger_row(row, label)
        relative_path = str(validated["relative_path"])
        dedupe_key = ledger_dedupe_key(validated)
        if dedupe_key in dedupe_keys:
            raise ManifestConflict(f"{label} contains a duplicate dedupe key")
        dedupe_keys.add(dedupe_key)
        previous = result.get(relative_path)
        if previous is not None and previous != validated:
            raise ManifestConflict(f"{label} contains conflicting rows for {relative_path}")
        if previous is not None:
            raise ManifestConflict(f"{label} contains duplicate rows for {relative_path}")
        result[relative_path] = validated
    return result


def update_hash_ledger(
    existing: list[dict[str, Any]],
    current: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the append-only union after proving every historical raw still matches."""

    existing_by_path = _rows_by_path(existing, "hash ledger")
    current_by_path = _rows_by_path(current, "current raw inventory")

    deleted = sorted(set(existing_by_path) - set(current_by_path))
    if deleted:
        raise ManifestConflict(f"raw files recorded by the ledger were deleted: {', '.join(deleted)}")

    for relative_path, ledger_row in existing_by_path.items():
        current_row = current_by_path[relative_path]
        if any(
            ledger_row.get(field) != current_row.get(field)
            for field in LEDGER_IMMUTABLE_FIELDS
        ):
            raise ManifestConflict(f"raw file changed after ledger entry: {relative_path}")

    union = [dict(row) for row in existing]
    for relative_path in sorted(set(current_by_path) - set(existing_by_path)):
        union.append(dict(current_by_path[relative_path]))
    return union


def record_raw_ledger(
    database_dir: Path,
    imported_at: str | None = None,
) -> dict[str, Any]:
    """Record the current raw inventory by appending only previously unseen rows."""

    database_dir = database_dir.resolve()
    load_database_raw_ledger_contract(database_dir)
    imported_at = imported_at or now_utc()
    current_rows = build_manifest_rows(database_dir, imported_at)
    ledger_path = hash_ledger_path(database_dir)
    with raw_ledger_append_lock(ledger_path):
        existing_rows = read_jsonl(ledger_path)
        union_rows = update_hash_ledger(existing_rows, current_rows)
        appended_rows = union_rows[len(existing_rows):]
        appended_bytes = append_jsonl_immutable(ledger_path, appended_rows, lock_held=True)
    return {
        "status": "PASS",
        "schema_version": "memory_atlas_raw_ledger_record.v1_2_1_s06_p2_t1",
        "task_id": "S06-P2-T1",
        "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
        "raw_file_count": len(current_rows),
        "source_stat_verified_count": len(current_rows),
        "ledger_entry_count": len(union_rows),
        "ledger_appended_count": len(appended_rows),
        "ledger_deduplicated_count": len(current_rows) - len(appended_rows),
        "ledger_appended_bytes": appended_bytes,
        "idempotent": not appended_rows,
        "source_mutation": False,
        "existing_ledger_rewritten": False,
    }


def preflight_raw_ledger(database_dir: Path) -> dict[str, Any]:
    """Reject historical drift before an adapter starts appending public raw."""

    database_dir = database_dir.resolve()
    load_database_raw_ledger_contract(database_dir)
    ledger_path = hash_ledger_path(database_dir)
    current_rows = build_manifest_rows(database_dir, imported_at=now_utc())
    if not ledger_path.exists():
        if current_rows:
            raise ManifestConflict("existing public raw has no immutable ledger")
        return {
            "status": "PASS",
            "task_id": "S06-P2-T1",
            "ledger_initialized": False,
            "raw_file_count": 0,
        }
    with raw_ledger_append_lock(ledger_path):
        existing_rows = read_jsonl(ledger_path)
        union_rows = update_hash_ledger(existing_rows, current_rows)
        if len(union_rows) != len(existing_rows):
            raise ManifestConflict("existing public raw contains unledgered files")
    return {
        "status": "PASS",
        "task_id": "S06-P2-T1",
        "ledger_initialized": True,
        "raw_file_count": len(current_rows),
    }


def _require_source_families(rows: list[dict[str, Any]]) -> list[str]:
    source_families = sorted({str(row.get("source_id") or "") for row in rows})
    missing = [source for source in ("chatgpt", "codex") if source not in source_families]
    if not any(source.startswith("agent:") for source in source_families):
        missing.append("agent:*")
    if not rows:
        raise ManifestConflict("public raw inventory is empty")
    if missing:
        raise ManifestConflict(f"public raw source-family gate failed: missing {', '.join(missing)}")
    return source_families


def generate_raw_manifest(
    database_dir: Path,
    run_id: str,
    imported_at: str | None = None,
    require_non_empty: bool = False,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    load_database_raw_ledger_contract(database_dir)
    imported_at = imported_at or now_utc()
    rows = build_manifest_rows(database_dir, imported_at)
    source_families = sorted({str(row.get("source_id") or "") for row in rows})
    if require_non_empty:
        source_families = _require_source_families(rows)

    manifest_path = manifest_path_for(database_dir, run_id)
    ledger_path = hash_ledger_path(database_dir)
    manifest_payload = jsonl_payload(rows)
    manifest_exists = manifest_path.exists()
    if manifest_exists and manifest_path.read_text(encoding="utf-8") != manifest_payload:
        raise ManifestConflict(f"manifest run_id is immutable: {run_id}")

    # All conflict checks complete before either immutable artifact is written.
    with raw_ledger_append_lock(ledger_path):
        existing_ledger = read_jsonl(ledger_path)
        union_ledger = update_hash_ledger(existing_ledger, rows)
        appended_rows = union_ledger[len(existing_ledger):]
        appended_bytes = append_jsonl_immutable(ledger_path, appended_rows, lock_held=True)
    if not manifest_exists:
        write_text_atomic(manifest_path, manifest_payload)

    return {
        "status": "PASS",
        "schema_version": "memory_atlas_raw_manifest.v3_s06_p2_t1",
        "task_id": "S06-P2-T1",
        "run_id": run_id,
        "generated_at": now_utc(),
        "imported_at": imported_at,
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "manifest_path": manifest_path.relative_to(database_dir).as_posix(),
        "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
        "raw_file_count": len(rows),
        "ledger_entry_count": len(union_ledger),
        "ledger_appended_count": len(appended_rows),
        "ledger_deduplicated_count": len(rows) - len(appended_rows),
        "ledger_appended_bytes": appended_bytes,
        "source_stat_verified_count": len(rows),
        "existing_ledger_rewritten": False,
        "source_families": source_families,
        "manifest_sha256": hashlib.sha256(manifest_payload.encode("utf-8")).hexdigest(),
        "idempotent": manifest_exists and not appended_rows,
        "require_non_empty": require_non_empty,
    }


def audit_raw_append_only(database_dir: Path) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    load_database_raw_ledger_contract(database_dir)
    ledger_path = hash_ledger_path(database_dir)
    try:
        if not ledger_path.is_file():
            raise ManifestConflict("raw hash ledger is missing")
        ledger_rows = read_jsonl(ledger_path)
        current_rows = build_manifest_rows(database_dir, imported_at=now_utc())
        ledger_by_path = _rows_by_path(ledger_rows, "hash ledger")
        current_by_path = _rows_by_path(current_rows, "current raw inventory")
    except ManifestConflict as exc:
        return {
            "status": "FAIL",
            "schema_version": "memory_atlas_raw_append_only_audit.v3_s06_p2_t1",
            "task_id": "S06-P2-T1",
            "raw_root": PUBLIC_RAW_ROOT.as_posix(),
            "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
            "reason": str(exc),
        }

    deleted = sorted(path for path in ledger_by_path if path and path not in current_by_path)
    immutable_changed = sorted(
        path
        for path, row in ledger_by_path.items()
        if path in current_by_path
        and any(row.get(field) != current_by_path[path].get(field) for field in LEDGER_IMMUTABLE_FIELDS)
    )
    hash_changed = sorted(
        path
        for path, row in ledger_by_path.items()
        if path in current_by_path and row.get("sha256") != current_by_path[path].get("sha256")
    )
    added = sorted(path for path in current_by_path if path and path not in ledger_by_path)
    status = "PASS" if not deleted and not immutable_changed and not added else "FAIL"
    return {
        "status": status,
        "schema_version": "memory_atlas_raw_append_only_audit.v3_s06_p2_t1",
        "task_id": "S06-P2-T1",
        "raw_root": PUBLIC_RAW_ROOT.as_posix(),
        "hash_ledger_path": ledger_path.relative_to(database_dir).as_posix(),
        "ledger_entry_count": len(ledger_rows),
        "current_raw_file_count": len(current_rows),
        "source_stat_verified_count": len(current_rows),
        "new_raw_file_count": len(added),
        "unledgered_raw_file_count": len(added),
        "immutable_drift_count": len(immutable_changed),
        "hash_drift_count": len(hash_changed),
        "deleted_manifest_entry_count": len(deleted),
        "new_raw_files": added,
        "immutable_drift_files": immutable_changed,
        "hash_drift_files": hash_changed,
        "deleted_manifest_entries": deleted,
        "source_mutation": False,
        "existing_ledger_rewritten": False,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate = subparsers.add_parser("generate", help="generate raw manifest and hash ledger")
    generate.add_argument("--database-dir", default=".", help="OpenAIDatabase root")
    generate.add_argument("--run-id", required=True, help="manifest run id")
    generate.add_argument("--imported-at", default=None, help="stable imported_at timestamp")
    generate.add_argument(
        "--require-non-empty",
        action="store_true",
        help="require ChatGPT, Codex and at least one agent source family",
    )

    audit = subparsers.add_parser("audit", help="audit raw append-only/hash drift rules")
    audit.add_argument("--database-dir", default=".", help="OpenAIDatabase root")

    chunk = subparsers.add_parser("chunk", help="split a package into deterministic 45 MiB parts")
    chunk.add_argument("--database-dir", default=".", help="OpenAIDatabase root")
    chunk.add_argument("--package", required=True, help="package file to read without mutation")
    chunk.add_argument("--source-id", required=True, help="portable archive source id")
    chunk.add_argument("--archive-id", required=True, help="portable archive run id")

    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.command == "generate":
            result = generate_raw_manifest(
                Path(args.database_dir),
                args.run_id,
                args.imported_at,
                require_non_empty=args.require_non_empty,
            )
        elif args.command == "audit":
            result = audit_raw_append_only(Path(args.database_dir))
        elif args.command == "chunk":
            result = chunk_archive_package(
                Path(args.database_dir),
                Path(args.package),
                args.source_id,
                args.archive_id,
            )
        else:
            raise AssertionError(f"unhandled command: {args.command}")
    except ArchiveChunkPostPublishError as exc:
        result = {
            "status": "FAIL",
            "schema_version": "memory_atlas_archive_chunk_error.v1_2_1_s06_p2_t2",
            "task_id": "S06-P2-T2",
            "reason": str(exc),
            "published_archive_may_exist": True,
            "incomplete_archive_may_exist": False,
            "remote_push": False,
        }
    except ArchiveChunkPartialWriteError as exc:
        result = {
            "status": "FAIL",
            "schema_version": "memory_atlas_archive_chunk_error.v1_2_1_s06_p2_t2",
            "task_id": "S06-P2-T2",
            "reason": str(exc),
            "published_archive_may_exist": True,
            "incomplete_archive_may_exist": True,
            "remote_push": False,
        }
    except ArchiveChunkError as exc:
        result = {
            "status": "FAIL",
            "schema_version": "memory_atlas_archive_chunk_error.v1_2_1_s06_p2_t2",
            "task_id": "S06-P2-T2",
            "reason": str(exc),
            "published_archive_may_exist": False,
            "incomplete_archive_may_exist": False,
            "remote_push": False,
        }
    except ManifestConflict as exc:
        result = {
            "status": "FAIL",
            "schema_version": "memory_atlas_raw_manifest_error.v1",
            "reason": str(exc),
        }

    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
