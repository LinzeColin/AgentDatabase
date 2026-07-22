#!/usr/bin/env python3
"""Validate and seal a verifier v2.1 acceptance run using only stdlib.

The seal is tamper-evident after finalization. It is not an authenticity
signature; use trusted provenance/signatures when origin must be proven.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional


SCHEMA_VERSION = "2.1"
REQUIRED_FILES = {
    "VERDICT.md",
    "TEST_MATRIX.md",
    "DEFECT_REPORT.md",
    "RUN_MANIFEST.yaml",
    "RELEASE_ASSURANCE.md",
    "AI_EVAL_MATRIX.md",
    "TRACEABILITY_MATRIX.json",
}
REQUIRED_DIRS = {
    "logs",
    "traces",
    "screenshots",
    "metrics",
    "artifacts",
    "raw-results",
    "taskpack",
}
SEAL_FILES = {
    "EVIDENCE_INDEX.json",
    "FINAL_DECISION.json",
    "SHA256SUMS.txt",
    "ACCEPTANCE_ATTESTATION.intoto.json",
}
ALLOWED_STATUSES = {
    "PLANNED",
    "RUNNING",
    "PASS",
    "FAIL",
    "BLOCKED",
    "NOT_RUN",
    "NOT_APPLICABLE",
    "WAIVED",
}
FINAL_STATUSES = ALLOWED_STATUSES - {"PLANNED", "RUNNING"}
ALLOWED_VERDICTS = {"PASS", "PASS_WITH_RISKS", "FAIL", "BLOCKED", "UNSAFE"}
ACTION_BY_VERDICT = {
    "PASS": "NONE",
    "PASS_WITH_RISKS": "ACT",
    "FAIL": "ACT",
    "BLOCKED": "ESCALATE",
    "UNSAFE": "STOP",
}
ALLOWED_DECISION_SCOPES = {
    "developer_check",
    "release_candidate",
    "staged_release",
    "post_deploy",
}
ALLOWED_RISK_LEVELS = {"low", "medium", "high", "critical"}
ALLOWED_PROFILES = {"quick", "standard", "deep"}
ALLOWED_FINDING_TYPES = {
    "PRODUCT_DEFECT",
    "TEST_DEFECT",
    "ENVIRONMENT_DEFECT",
    "REQUIREMENT_GAP",
    "FLAKY_UNRESOLVED",
    "OBSERVATION",
}
ALLOWED_FINDING_SEVERITIES = {"L0", "L1", "L2"}
ALLOWED_FINDING_STATUSES = {"OPEN", "CONFIRMED", "WAIVED", "RETEST_PENDING", "CLOSED"}
NON_WAIVABLE_CATEGORIES = {
    "ARTIFACT_IDENTITY",
    "CORE_JOURNEY",
    "DATA_LOSS_OR_CORRUPTION",
    "AUTHZ_BYPASS",
    "SECRET_OR_PRIVACY_LEAK",
    "UNRECOVERABLE_MIGRATION",
    "UNBOUNDED_SIDE_EFFECT_OR_COST",
    "EVIDENCE_INTEGRITY",
    "CRITICAL_FLAKY",
    "NO_SAFE_RECOVERY",
    "TASKPACK_INTEGRITY",
    "ACCEPTANCE_ORACLE_DRIFT",
    "TRACEABILITY_GAP",
    "DELIVERY_CONTENT_MISMATCH",
}
BASE_GATES = {
    "subject_identity": {"PASS"},
    "build_start_health": {"PASS", "NOT_APPLICABLE"},
    "core_journey": {"PASS"},
    "data_or_output": {"PASS", "NOT_APPLICABLE"},
    "changed_scope_regression": {"PASS"},
}
HEX_RE = re.compile(r"^[0-9a-fA-F]+$")
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
IMAGE_DIGEST_RE = re.compile(r"^sha256:[0-9a-fA-F]{64}$")
PLACEHOLDER_RE = re.compile(r"<[^>\n]+>")
REQUIRED_TASKPACK_ROLES = {
    "manifest",
    "pursuing_goal",
    "prd",
    "technical_design",
    "roadmap",
    "task_graph",
    "acceptance_contract",
}
TASKPACK_GATE_STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}
TRACE_ROW_STATUSES = {"PASS", "FAIL", "BLOCKED", "WAIVED", "NOT_APPLICABLE"}
MAX_TASKPACK_FILES = 10_000
MAX_TASKPACK_BYTES = 512 * 1024 * 1024


class RunValidationError(Exception):
    """Raised for invalid acceptance runs."""


def _absolute_no_resolve(path: Path) -> Path:
    """Normalize an absolute path without hiding a final-path symlink."""
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise RunValidationError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def load_manifest(run_dir: Path) -> dict[str, Any]:
    path = run_dir / "RUN_MANIFEST.yaml"
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as error:
        raise RunValidationError(f"cannot read RUN_MANIFEST.yaml: {error}") from error
    try:
        value = json.loads(text, object_pairs_hook=_no_duplicate_keys)
    except (json.JSONDecodeError, RunValidationError) as error:
        raise RunValidationError(
            "RUN_MANIFEST.yaml must use strict JSON syntax (JSON is valid YAML): " + str(error)
        ) from error
    if not isinstance(value, dict):
        raise RunValidationError("RUN_MANIFEST.yaml root must be an object")
    return value


def _required_text(value: Any, label: str, errors: list[str]) -> str:
    if not isinstance(value, str) or not value.strip():
        errors.append(f"missing required text: {label}")
        return ""
    if PLACEHOLDER_RE.search(value) or value.strip().upper() in {"TODO", "TBD", "PENDING"}:
        errors.append(f"unresolved placeholder: {label}")
    return value.strip()


def _required_list(value: Any, label: str, errors: list[str], *, allow_empty: bool = False) -> list[Any]:
    if not isinstance(value, list):
        errors.append(f"{label} must be a list")
        return []
    if not allow_empty and not value:
        errors.append(f"{label} must not be empty")
    return value


def _get_object(parent: dict[str, Any], key: str, errors: list[str]) -> dict[str, Any]:
    value = parent.get(key)
    if not isinstance(value, dict):
        errors.append(f"{key} must be an object")
        return {}
    return value


def _safe_relative_file(run_dir: Path, raw: Any, label: str, errors: list[str]) -> Optional[Path]:
    if not isinstance(raw, str) or not raw.strip():
        errors.append(f"empty evidence path: {label}")
        return None
    relative = Path(raw)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"unsafe evidence path {label}: {raw}")
        return None
    candidate = run_dir / relative
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(run_dir.resolve())
    except (OSError, ValueError) as error:
        errors.append(f"missing or escaping evidence path {label}: {raw} ({error})")
        return None
    current = run_dir.resolve()
    for part in relative.parts:
        current = current / part
        if current.is_symlink():
            errors.append(f"symlink evidence path forbidden {label}: {raw}")
            return None
    if not resolved.is_file():
        errors.append(f"evidence path is not a regular file {label}: {raw}")
        return None
    return resolved


def _validate_evidence_path_list(
    run_dir: Path,
    value: Any,
    label: str,
    errors: list[str],
    *,
    allow_empty: bool = False,
) -> list[Any]:
    paths = _required_list(value, label, errors, allow_empty=allow_empty)
    for index, raw_path in enumerate(paths):
        _safe_relative_file(run_dir, raw_path, f"{label}[{index}]", errors)
    return paths


def _parse_timestamp(value: Any, label: str, errors: list[str]) -> Optional[datetime]:
    text = _required_text(value, label, errors)
    if not text:
        return None
    normalized = text[:-1] + "+00:00" if text.endswith("Z") else text
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        errors.append(f"invalid ISO-8601 timestamp: {label}")
        return None
    if parsed.tzinfo is None:
        errors.append(f"timestamp must include timezone: {label}")
        return None
    return parsed.astimezone(timezone.utc)


def _check_tree(run_dir: Path, errors: list[str]) -> None:
    if not run_dir.is_dir():
        errors.append(f"run directory not found: {run_dir}")
        return
    if run_dir.is_symlink():
        errors.append("run directory itself must not be a symlink")
        return
    for required in sorted(REQUIRED_FILES):
        path = run_dir / required
        if not path.is_file() or path.is_symlink():
            errors.append(f"missing regular required file: {required}")
    for required in sorted(REQUIRED_DIRS):
        path = run_dir / required
        if not path.is_dir() or path.is_symlink():
            errors.append(f"missing regular required directory: {required}/")
    for path in run_dir.rglob("*"):
        try:
            mode = path.lstat().st_mode
        except OSError as error:
            errors.append(f"cannot stat {path.relative_to(run_dir)}: {error}")
            continue
        relative = path.relative_to(run_dir)
        if stat.S_ISLNK(mode):
            errors.append(f"symlink forbidden in evidence bundle: {relative}")
        elif not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            errors.append(f"non-regular filesystem entry forbidden: {relative}")


def _iter_paths(value: Any) -> Iterable[str]:
    if isinstance(value, str):
        yield value
    elif isinstance(value, list):
        for item in value:
            yield from _iter_paths(item)



def _canonical_taskpack_digest(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: str(item.get("role", ""))):
        digest.update(
            f"{record.get('role', '')}\0{record.get('sha256', '')}\0{record.get('size', '')}\n".encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def _canonical_source_tree_digest(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: str(item.get("source_path", ""))):
        digest.update(
            f"{record.get('source_path', '')}\0{record.get('sha256', '')}\0{record.get('size', '')}\n".encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def _portable_source_path(raw: Any, label: str, errors: list[str]) -> str:
    if not isinstance(raw, str) or not raw:
        errors.append(f"missing required text: {label}")
        return ""
    if "\x00" in raw or "\\" in raw or raw.startswith(("/", "~")):
        errors.append(f"unsafe taskpack source path {label}: {raw!r}")
        return ""
    if re.match(r"^[A-Za-z]:", raw):
        errors.append(f"unsafe taskpack source path {label}: {raw!r}")
        return ""
    parts = raw.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        errors.append(f"unsafe taskpack source path {label}: {raw!r}")
        return ""
    return raw


def _load_json_object_file(
    run_dir: Path,
    raw_path: str,
    label: str,
    errors: list[str],
) -> dict[str, Any]:
    path = _safe_relative_file(run_dir, raw_path, label, errors)
    if path is None:
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys)
    except (OSError, json.JSONDecodeError, RunValidationError) as error:
        errors.append(f"cannot parse {label} as strict JSON: {error}")
        return {}
    if not isinstance(value, dict):
        errors.append(f"{label} root must be an object")
        return {}
    return value


def _validate_snapshot_zip(
    snapshot_path: Path,
    source_records: dict[str, dict[str, Any]],
    errors: list[str],
) -> None:
    try:
        archive = zipfile.ZipFile(snapshot_path)
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        errors.append(f"cannot open taskpack source snapshot ZIP: {error}")
        return
    seen_exact: set[str] = set()
    seen_casefold: dict[str, str] = {}
    total = 0
    try:
        with archive:
            for info in archive.infolist():
                name = _portable_source_path(
                    info.filename.rstrip("/"),
                    "taskpack source snapshot member",
                    errors,
                )
                if not name:
                    continue
                if info.is_dir():
                    errors.append(f"taskpack source snapshot must contain files only: {name}")
                    continue
                folded = name.casefold()
                if name in seen_exact or folded in seen_casefold:
                    errors.append(f"duplicate/case-colliding taskpack snapshot member: {name}")
                    continue
                seen_exact.add(name)
                seen_casefold[folded] = name
                if info.flag_bits & 0x1:
                    errors.append(f"encrypted taskpack snapshot member is forbidden: {name}")
                    continue
                unix_mode = (info.external_attr >> 16) & 0o170000
                if unix_mode == stat.S_IFLNK:
                    errors.append(f"symlink taskpack snapshot member is forbidden: {name}")
                    continue
                total += int(info.file_size)
                if len(seen_exact) > MAX_TASKPACK_FILES or total > MAX_TASKPACK_BYTES:
                    errors.append("taskpack source snapshot exceeds verifier safety limits")
                    return
                expected = source_records.get(name)
                if expected is None:
                    errors.append(f"taskpack snapshot contains unindexed file: {name}")
                    continue
                if info.file_size != expected["size"]:
                    errors.append(f"taskpack snapshot member size mismatch: {name}")
                digest = hashlib.sha256()
                actual_size = 0
                try:
                    with archive.open(info, "r") as handle:
                        while True:
                            block = handle.read(1024 * 1024)
                            if not block:
                                break
                            actual_size += len(block)
                            if actual_size > expected["size"] or actual_size > MAX_TASKPACK_BYTES:
                                errors.append(f"taskpack snapshot member expands beyond declared size: {name}")
                                break
                            digest.update(block)
                except (OSError, RuntimeError, zipfile.BadZipFile) as error:
                    errors.append(f"cannot read taskpack snapshot member {name}: {error}")
                    continue
                if actual_size != expected["size"]:
                    errors.append(f"taskpack snapshot member byte count mismatch: {name}")
                elif digest.hexdigest() != expected["sha256"]:
                    errors.append(f"taskpack snapshot member digest mismatch: {name}")
    except (OSError, RuntimeError, zipfile.BadZipFile) as error:
        errors.append(f"cannot validate taskpack source snapshot ZIP: {error}")
        return
    expected_paths = set(source_records)
    if seen_exact != expected_paths:
        errors.append(
            "taskpack source snapshot inventory mismatch; "
            f"missing={sorted(expected_paths - seen_exact)}, extra={sorted(seen_exact - expected_paths)}"
        )


def _validate_taskpack_source_lock(
    run_dir: Path,
    taskpack: dict[str, Any],
    errors: list[str],
) -> dict[str, Any]:
    lock = _load_json_object_file(
        run_dir,
        "raw-results/taskpack-lock.json",
        "raw-results/taskpack-lock.json",
        errors,
    )
    snapshot_raw_path = _required_text(
        taskpack.get("source_snapshot_path"), "taskpack.source_snapshot_path", errors
    )
    if snapshot_raw_path != "taskpack/TASKPACK_SOURCE_SNAPSHOT.zip":
        errors.append(
            "taskpack.source_snapshot_path must be taskpack/TASKPACK_SOURCE_SNAPSHOT.zip"
        )
    snapshot_path = (
        _safe_relative_file(
            run_dir,
            snapshot_raw_path,
            "taskpack.source_snapshot_path",
            errors,
        )
        if snapshot_raw_path
        else None
    )
    snapshot_digest = taskpack.get("source_snapshot_sha256", "")
    if not isinstance(snapshot_digest, str) or not SHA256_RE.fullmatch(snapshot_digest):
        errors.append("taskpack.source_snapshot_sha256 must be a 64-character SHA-256")
        snapshot_digest = ""
    snapshot_size = taskpack.get("source_snapshot_size")
    if not isinstance(snapshot_size, int) or snapshot_size < 0:
        errors.append("taskpack.source_snapshot_size must be a non-negative integer")
        snapshot_size = -1
    if snapshot_path is not None:
        actual_digest, actual_size = _sha256_file(snapshot_path)
        if snapshot_digest and actual_digest != snapshot_digest.lower():
            errors.append("taskpack source snapshot digest mismatch")
        if snapshot_size >= 0 and actual_size != snapshot_size:
            errors.append("taskpack source snapshot size mismatch")

    source_file_count = taskpack.get("source_file_count")
    if not isinstance(source_file_count, int) or source_file_count <= 0:
        errors.append("taskpack.source_file_count must be a positive integer")
        source_file_count = 0

    source_records_raw = lock.get("source_files") if isinstance(lock, dict) else None
    source_records_list = _required_list(
        source_records_raw,
        "taskpack-lock.source_files",
        errors,
    )
    source_records: dict[str, dict[str, Any]] = {}
    seen_casefold: dict[str, str] = {}
    total_size = 0
    for index, record in enumerate(source_records_list):
        label = f"taskpack-lock.source_files[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        source_path = _portable_source_path(record.get("source_path"), f"{label}.source_path", errors)
        if not source_path:
            continue
        folded = source_path.casefold()
        if source_path in source_records or folded in seen_casefold:
            errors.append(f"duplicate/case-colliding source file in taskpack lock: {source_path}")
            continue
        digest = record.get("sha256")
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            errors.append(f"{label}.sha256 must be a 64-character SHA-256")
            continue
        size = record.get("size")
        if not isinstance(size, int) or size < 0:
            errors.append(f"{label}.size must be a non-negative integer")
            continue
        total_size += size
        source_records[source_path] = {
            "source_path": source_path,
            "sha256": digest.lower(),
            "size": size,
        }
        seen_casefold[folded] = source_path
    if len(source_records) > MAX_TASKPACK_FILES or total_size > MAX_TASKPACK_BYTES:
        errors.append("taskpack lock source inventory exceeds verifier safety limits")
    if source_file_count and source_file_count != len(source_records):
        errors.append("taskpack.source_file_count does not match taskpack lock inventory")

    pack_digest = taskpack.get("pack_digest_sha256", "")
    if not isinstance(pack_digest, str) or not SHA256_RE.fullmatch(pack_digest):
        errors.append("taskpack.pack_digest_sha256 must be a 64-character SHA-256")
        pack_digest = ""
    elif source_records:
        computed = _canonical_source_tree_digest(list(source_records.values()))
        if computed != pack_digest.lower():
            errors.append("taskpack.pack_digest_sha256 does not match the full source inventory")

    if lock:
        exact_fields = (
            "source_kind",
            "source_reference",
            "source_archive_sha256",
            "source_snapshot_path",
            "source_snapshot_sha256",
            "source_snapshot_size",
            "source_file_count",
            "pack_digest_sha256",
            "contract_digest_sha256",
            "declared_version",
            "authoritative",
            "authorization_reference",
            "authorized_pack_digest_sha256",
            "files",
            "acceptance_ids",
            "task_ids",
        )
        for key in exact_fields:
            if lock.get(key) != taskpack.get(key):
                errors.append(f"taskpack lock does not match RUN_MANIFEST taskpack.{key}")
        if lock.get("schema_version") != SCHEMA_VERSION:
            errors.append(f"taskpack lock schema_version must be {SCHEMA_VERSION}")
        if lock.get("source_file_count") != len(source_records):
            errors.append("taskpack lock source_file_count does not match source_files")
        lock_pack_digest = lock.get("pack_digest_sha256")
        if source_records and isinstance(lock_pack_digest, str) and SHA256_RE.fullmatch(lock_pack_digest):
            if _canonical_source_tree_digest(list(source_records.values())) != lock_pack_digest.lower():
                errors.append("taskpack lock pack digest does not match source_files")

    if snapshot_path is not None and source_records:
        _validate_snapshot_zip(snapshot_path, source_records, errors)
    return {
        "lock": lock,
        "source_records": source_records,
        "pack_digest_sha256": pack_digest,
        "source_snapshot_sha256": snapshot_digest,
        "source_file_count": len(source_records),
    }

def _validate_taskpack(
    run_dir: Path,
    manifest: dict[str, Any],
    verdict: str,
    errors: list[str],
) -> dict[str, Any]:
    taskpack = _get_object(manifest, "taskpack", errors)
    mode = taskpack.get("mode")
    detected = taskpack.get("detected")
    authoritative = taskpack.get("authoritative")
    if not isinstance(detected, bool):
        errors.append("taskpack.detected must be boolean")
        detected = False
    if not isinstance(authoritative, bool):
        errors.append("taskpack.authoritative must be boolean")
        authoritative = False

    status_fields = ("integrity_status", "compatibility_status", "drift_status")
    for key in status_fields:
        value = taskpack.get(key)
        if value not in TASKPACK_GATE_STATUSES:
            errors.append(f"invalid taskpack.{key}: {value!r}")

    if not detected:
        if mode != "not-provided":
            errors.append('taskpack.mode must be "not-provided" when taskpack.detected=false')
        if authoritative:
            errors.append("absent taskpack cannot be authoritative")
        _required_text(taskpack.get("reason_if_absent"), "taskpack.reason_if_absent", errors)
        for key in status_fields:
            if taskpack.get(key) != "NOT_APPLICABLE":
                errors.append(f"absent taskpack requires taskpack.{key}=NOT_APPLICABLE")
        if taskpack.get("files") not in ([], None):
            errors.append("absent taskpack must not contain taskpack.files")
        manifest["_derived_taskpack"] = {
            "detected": False,
            "authoritative": False,
            "pack_digest_sha256": "",
            "contract_digest_sha256": "",
            "source_snapshot_sha256": "",
            "source_file_count": 0,
            "acceptance_ids": [],
            "task_ids": [],
        }
        return taskpack

    if mode != "product-design-taskpack":
        errors.append('detected taskpack requires mode="product-design-taskpack"')
    source_kind = taskpack.get("source_kind")
    if source_kind not in {"zip", "directory"}:
        errors.append("taskpack.source_kind must be zip or directory")
    _required_text(taskpack.get("source_reference"), "taskpack.source_reference", errors)
    _required_text(taskpack.get("declared_version"), "taskpack.declared_version", errors)
    _required_text(taskpack.get("pursuing_goal"), "taskpack.pursuing_goal", errors)
    if authoritative:
        _required_text(
            taskpack.get("authorization_reference"),
            "taskpack.authorization_reference",
            errors,
        )

    source_archive_digest = taskpack.get("source_archive_sha256", "")
    if source_archive_digest and (
        not isinstance(source_archive_digest, str)
        or not SHA256_RE.fullmatch(source_archive_digest)
    ):
        errors.append("taskpack.source_archive_sha256 must be a 64-character SHA-256")

    source_lock_info = _validate_taskpack_source_lock(run_dir, taskpack, errors)
    source_records = source_lock_info.get("source_records", {})
    pack_digest = source_lock_info.get("pack_digest_sha256", "")

    records_raw = taskpack.get("files")
    records = _required_list(records_raw, "taskpack.files", errors)
    normalized_records: list[dict[str, Any]] = []
    seen_roles: set[str] = set()
    seen_paths: set[str] = set()
    for index, record in enumerate(records):
        label = f"taskpack.files[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        role = _required_text(record.get("role"), f"{label}.role", errors)
        if role not in REQUIRED_TASKPACK_ROLES:
            errors.append(f"invalid {label}.role: {role!r}")
        if role in seen_roles:
            errors.append(f"duplicate taskpack role: {role}")
        seen_roles.add(role)
        source_path = _portable_source_path(
            record.get("source_path"), f"{label}.source_path", errors
        )
        raw_path = _required_text(record.get("path"), f"{label}.path", errors)
        if raw_path in seen_paths:
            errors.append(f"duplicate taskpack evidence path: {raw_path}")
        seen_paths.add(raw_path)
        relative = Path(raw_path) if raw_path else Path()
        if not relative.parts or relative.parts[0] != "taskpack":
            errors.append(f"{label}.path must be inside taskpack/: {raw_path!r}")
        resolved = _safe_relative_file(run_dir, raw_path, f"{label}.path", errors) if raw_path else None
        expected_digest = record.get("sha256")
        if not isinstance(expected_digest, str) or not SHA256_RE.fullmatch(expected_digest):
            errors.append(f"{label}.sha256 must be a 64-character SHA-256")
            expected_digest = ""
        expected_size = record.get("size")
        if not isinstance(expected_size, int) or expected_size < 0:
            errors.append(f"{label}.size must be a non-negative integer")
            expected_size = -1
        if resolved is not None:
            actual_digest, actual_size = _sha256_file(resolved)
            if expected_digest and actual_digest != expected_digest.lower():
                errors.append(f"taskpack file digest mismatch: {raw_path}")
            if expected_size >= 0 and actual_size != expected_size:
                errors.append(f"taskpack file size mismatch: {raw_path}")
        normalized_records.append(
            {
                "role": role,
                "source_path": source_path,
                "sha256": str(expected_digest).lower(),
                "size": expected_size,
            }
        )
        source_record = source_records.get(source_path) if source_path else None
        if source_path and source_record is None:
            errors.append(f"canonical taskpack role source is absent from full source inventory: {source_path}")
        elif source_record is not None:
            if source_record.get("sha256") != str(expected_digest).lower():
                errors.append(f"canonical taskpack role differs from source snapshot: {source_path}")
            if source_record.get("size") != expected_size:
                errors.append(f"canonical taskpack role size differs from source snapshot: {source_path}")
    if seen_roles != REQUIRED_TASKPACK_ROLES:
        errors.append(
            "taskpack seven-role set mismatch; "
            f"missing={sorted(REQUIRED_TASKPACK_ROLES - seen_roles)}, "
            f"extra={sorted(seen_roles - REQUIRED_TASKPACK_ROLES)}"
        )

    contract_digest = taskpack.get("contract_digest_sha256")
    if not isinstance(contract_digest, str) or not SHA256_RE.fullmatch(contract_digest):
        errors.append("taskpack.contract_digest_sha256 must be a 64-character SHA-256")
        contract_digest = ""
    elif len(normalized_records) == len(REQUIRED_TASKPACK_ROLES):
        computed = _canonical_taskpack_digest(normalized_records)
        if computed != contract_digest.lower():
            errors.append(
                "taskpack.contract_digest_sha256 does not match the locked seven semantic roles"
            )

    authorized_digest = taskpack.get("authorized_pack_digest_sha256", "")
    if authorized_digest and (
        not isinstance(authorized_digest, str) or not SHA256_RE.fullmatch(authorized_digest)
    ):
        errors.append("taskpack.authorized_pack_digest_sha256 must be a 64-character SHA-256")
    if authoritative and pack_digest and (
        not isinstance(authorized_digest, str) or authorized_digest.lower() != pack_digest.lower()
    ):
        errors.append("authoritative taskpack digest does not match the authorized pack digest (normalized full pack)")

    acceptance_ids_raw = taskpack.get("acceptance_ids")
    acceptance_ids_list = _required_list(
        acceptance_ids_raw,
        "taskpack.acceptance_ids",
        errors,
        allow_empty=verdict not in {"PASS", "PASS_WITH_RISKS", "FAIL"},
    )
    acceptance_ids: list[str] = []
    for index, value in enumerate(acceptance_ids_list):
        acceptance_id = _required_text(value, f"taskpack.acceptance_ids[{index}]", errors)
        if acceptance_id:
            acceptance_ids.append(acceptance_id)
    if len(acceptance_ids) != len(set(acceptance_ids)):
        errors.append("taskpack.acceptance_ids must be unique")

    task_ids_raw = taskpack.get("task_ids")
    task_ids_list = _required_list(
        task_ids_raw,
        "taskpack.task_ids",
        errors,
        allow_empty=verdict not in {"PASS", "PASS_WITH_RISKS", "FAIL"},
    )
    task_ids: list[str] = []
    for index, value in enumerate(task_ids_list):
        task_id = _required_text(value, f"taskpack.task_ids[{index}]", errors)
        if task_id:
            task_ids.append(task_id)
    if len(task_ids) != len(set(task_ids)):
        errors.append("taskpack.task_ids must be unique")

    drift_items = taskpack.get("drift_items")
    if not isinstance(drift_items, list):
        errors.append("taskpack.drift_items must be a list")
        drift_items = []
    for index, item in enumerate(drift_items):
        label = f"taskpack.drift_items[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in ("id", "type", "before", "after", "impact"):
            _required_text(item.get(key), f"{label}.{key}", errors)
        _validate_evidence_path_list(
            run_dir, item.get("evidence_paths"), f"{label}.evidence_paths", errors
        )
    _validate_evidence_path_list(
        run_dir,
        taskpack.get("authorization_evidence_paths", []),
        "taskpack.authorization_evidence_paths",
        errors,
        allow_empty=True,
    )
    _validate_evidence_path_list(
        run_dir,
        taskpack.get("integrity_evidence_paths"),
        "taskpack.integrity_evidence_paths",
        errors,
    )
    compatibility_paths = _validate_evidence_path_list(
        run_dir,
        taskpack.get("compatibility_evidence_paths", []),
        "taskpack.compatibility_evidence_paths",
        errors,
        allow_empty=taskpack.get("compatibility_status") not in {"PASS", "FAIL"},
    )
    drift_paths = _validate_evidence_path_list(
        run_dir,
        taskpack.get("drift_evidence_paths", []),
        "taskpack.drift_evidence_paths",
        errors,
        allow_empty=taskpack.get("drift_status") not in {"PASS", "FAIL"},
    )
    _validate_evidence_path_list(
        run_dir, taskpack.get("evidence_paths"), "taskpack.evidence_paths", errors
    )
    if taskpack.get("compatibility_status") != "PASS":
        _required_text(
            taskpack.get("compatibility_reason"),
            "taskpack.compatibility_reason when not PASS",
            errors,
        )
    if taskpack.get("drift_status") == "PASS" and drift_items:
        errors.append("taskpack.drift_status=PASS cannot contain drift_items")
    if taskpack.get("drift_status") == "FAIL" and not drift_items:
        errors.append("taskpack.drift_status=FAIL requires at least one drift_item")

    positive_or_fail = verdict in {"PASS", "PASS_WITH_RISKS", "FAIL"}
    if positive_or_fail and not authoritative:
        errors.append(
            "a deliberately ingested taskpack must be authoritative for PASS, PASS_WITH_RISKS, or FAIL; "
            "otherwise use a BLOCKED run or create a run without taskpack ingestion"
        )
    if positive_or_fail:
        if taskpack.get("integrity_status") != "PASS":
            errors.append(f"{verdict} requires taskpack.integrity_status=PASS")
        if taskpack.get("compatibility_status") != "PASS":
            errors.append(f"{verdict} requires taskpack.compatibility_status=PASS")
        if not compatibility_paths:
            errors.append(f"{verdict} requires semantic taskpack compatibility evidence")
        if not drift_paths:
            errors.append(f"{verdict} requires implementation-versus-contract drift evidence")
    if verdict in {"PASS", "PASS_WITH_RISKS"}:
        if taskpack.get("drift_status") != "PASS":
            errors.append("positive verdict requires taskpack.drift_status=PASS")
        if drift_items:
            errors.append("positive verdict cannot contain taskpack drift_items")

    manifest["_derived_taskpack"] = {
        "detected": True,
        "authoritative": authoritative,
        "pack_digest_sha256": pack_digest,
        "contract_digest_sha256": contract_digest,
        "source_snapshot_sha256": source_lock_info.get("source_snapshot_sha256", ""),
        "source_file_count": source_lock_info.get("source_file_count", 0),
        "acceptance_ids": acceptance_ids,
        "task_ids": task_ids,
    }
    return taskpack


def _trace_row_status(statuses: list[str]) -> str:
    if any(status == "FAIL" for status in statuses):
        return "FAIL"
    if any(status in {"BLOCKED", "NOT_RUN"} for status in statuses):
        return "BLOCKED"
    if any(status == "WAIVED" for status in statuses):
        return "WAIVED"
    if statuses and all(status == "NOT_APPLICABLE" for status in statuses):
        return "NOT_APPLICABLE"
    if statuses and all(status in {"PASS", "NOT_APPLICABLE"} for status in statuses):
        return "PASS"
    return "BLOCKED"


def _validate_traceability(
    run_dir: Path,
    manifest: dict[str, Any],
    taskpack: dict[str, Any],
    subject_identity: str,
    results: list[dict[str, Any]],
    verdict: str,
    errors: list[str],
) -> dict[str, Any]:
    trace = _get_object(manifest, "traceability", errors)
    status_value = trace.get("status")
    if status_value not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}:
        errors.append(f"invalid traceability.status: {status_value!r}")
    if status_value != "PASS":
        _required_text(trace.get("reason"), "traceability.reason when status is not PASS", errors)
    _validate_evidence_path_list(
        run_dir,
        trace.get("evidence_paths", []),
        "traceability.evidence_paths",
        errors,
        allow_empty=True,
    )
    matrix_raw = _required_text(trace.get("matrix_path"), "traceability.matrix_path", errors)
    matrix_path = _safe_relative_file(
        run_dir, matrix_raw, "traceability.matrix_path", errors
    ) if matrix_raw else None
    if matrix_path is None:
        summary = {
            "status": status_value,
            "row_count": 0,
            "declared_acceptance_count": len(taskpack.get("acceptance_ids", [])),
            "mapped_acceptance_count": 0,
            "blocking_acceptance_count": 0,
            "passing_acceptance_count": 0,
        }
        manifest["_derived_traceability"] = summary
        return summary
    try:
        matrix = json.loads(
            matrix_path.read_text(encoding="utf-8"), object_pairs_hook=_no_duplicate_keys
        )
    except (OSError, json.JSONDecodeError, RunValidationError) as error:
        errors.append(f"TRACEABILITY_MATRIX.json must be strict JSON: {error}")
        matrix = {}
    if not isinstance(matrix, dict):
        errors.append("TRACEABILITY_MATRIX.json root must be an object")
        matrix = {}
    if matrix.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"TRACEABILITY_MATRIX schema_version must be {SCHEMA_VERSION}")
    scope = _get_object(manifest, "scope", errors)
    if matrix.get("target_project_name") != scope.get("target_project_name"):
        errors.append("TRACEABILITY_MATRIX target_project_name does not match RUN_MANIFEST")
    matrix_subject = matrix.get("subject_identity", "")
    if verdict in {"PASS", "PASS_WITH_RISKS", "FAIL"}:
        if not isinstance(matrix_subject, str) or matrix_subject != subject_identity:
            errors.append("TRACEABILITY_MATRIX subject_identity does not match acceptance subject")
    taskpack_digest = taskpack.get("pack_digest_sha256", "") if taskpack.get("detected") else ""
    if matrix.get("taskpack_digest_sha256", "") != taskpack_digest:
        errors.append("TRACEABILITY_MATRIX taskpack_digest_sha256 does not match locked taskpack")

    result_by_id = {str(item.get("test_id")): item for item in results}
    rows_raw = matrix.get("rows")
    if not isinstance(rows_raw, list):
        errors.append("TRACEABILITY_MATRIX.rows must be a list")
        rows_raw = []
    mapped_ids: list[str] = []
    declared_task_ids = set(taskpack.get("task_ids", [])) if taskpack.get("detected") else set()
    blocking_count = 0
    passing_count = 0
    for index, row in enumerate(rows_raw):
        label = f"TRACEABILITY_MATRIX.rows[{index}]"
        if not isinstance(row, dict):
            errors.append(f"{label} must be an object")
            continue
        _required_text(row.get("requirement_id"), f"{label}.requirement_id", errors)
        acceptance_id = _required_text(row.get("acceptance_id"), f"{label}.acceptance_id", errors)
        _required_text(row.get("oracle_id"), f"{label}.oracle_id", errors)
        if acceptance_id:
            mapped_ids.append(acceptance_id)
        blocking = row.get("blocking")
        if not isinstance(blocking, bool):
            errors.append(f"{label}.blocking must be boolean")
        elif blocking:
            blocking_count += 1
        task_ids = _required_list(
            row.get("task_ids"),
            f"{label}.task_ids",
            errors,
            allow_empty=not taskpack.get("detected", False),
        )
        for task_index, task_id_raw in enumerate(task_ids):
            task_id = _required_text(task_id_raw, f"{label}.task_ids[{task_index}]", errors)
            if declared_task_ids and task_id not in declared_task_ids:
                errors.append(f"{label} references task_id absent from locked Task Graph: {task_id}")
        test_ids = _required_list(row.get("test_ids"), f"{label}.test_ids", errors)
        linked_statuses: list[str] = []
        for test_index, test_id_raw in enumerate(test_ids):
            test_id = _required_text(test_id_raw, f"{label}.test_ids[{test_index}]", errors)
            result = result_by_id.get(test_id)
            if result is None:
                errors.append(f"{label} references unknown test_id: {test_id}")
            else:
                linked_statuses.append(str(result.get("status", "")))
        row_status = row.get("status")
        if row_status not in TRACE_ROW_STATUSES:
            errors.append(f"invalid {label}.status: {row_status!r}")
        expected_status = _trace_row_status(linked_statuses)
        if linked_statuses and row_status != expected_status:
            errors.append(
                f"{label}.status={row_status!r} does not match linked test aggregate {expected_status!r}"
            )
        if row_status in {"PASS", "FAIL", "WAIVED"}:
            _validate_evidence_path_list(
                run_dir, row.get("evidence_paths"), f"{label}.evidence_paths", errors
            )
        else:
            _required_text(row.get("reason"), f"{label}.reason for {row_status}", errors)
            _validate_evidence_path_list(
                run_dir,
                row.get("evidence_paths", []),
                f"{label}.evidence_paths",
                errors,
                allow_empty=True,
            )
        if row_status == "PASS":
            passing_count += 1
        if verdict in {"PASS", "PASS_WITH_RISKS"} and blocking is True and row_status != "PASS":
            errors.append(f"positive verdict requires blocking acceptance row PASS: {acceptance_id}")

    if len(mapped_ids) != len(set(mapped_ids)):
        errors.append("TRACEABILITY_MATRIX acceptance_id values must be unique")
    declared_ids = taskpack.get("acceptance_ids", []) if taskpack.get("detected") else []
    declared_set = set(declared_ids)
    mapped_set = set(mapped_ids)
    complete_required = verdict in {"PASS", "PASS_WITH_RISKS", "FAIL"} or status_value == "PASS"
    if complete_required:
        if not rows_raw:
            errors.append("complete acceptance verdict requires at least one traceability row")
        if taskpack.get("detected") and mapped_set != declared_set:
            errors.append(
                "TRACEABILITY_MATRIX does not exactly cover authoritative acceptance IDs; "
                f"missing={sorted(declared_set - mapped_set)}, extra={sorted(mapped_set - declared_set)}"
            )
        if status_value != "PASS":
            errors.append("PASS, PASS_WITH_RISKS, or FAIL verdict requires traceability.status=PASS")

    change_impact = matrix.get("change_impact")
    if not isinstance(change_impact, list):
        errors.append("TRACEABILITY_MATRIX.change_impact must be a list")
        change_impact = []
    if complete_required and not change_impact:
        errors.append(
            "complete acceptance verdict requires at least one change_impact record; "
            "use an initial-delivery/current-subject record when no diff baseline exists"
        )
    seen_change_ids: set[str] = set()
    for index, item in enumerate(change_impact):
        label = f"TRACEABILITY_MATRIX.change_impact[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        change_id = _required_text(item.get("change_id"), f"{label}.change_id", errors)
        if change_id in seen_change_ids:
            errors.append(f"duplicate change_impact id: {change_id}")
        seen_change_ids.add(change_id)
        _required_list(item.get("changed_paths"), f"{label}.changed_paths", errors)
        impacted = item.get("impacted_acceptance_ids")
        if not isinstance(impacted, list):
            errors.append(f"{label}.impacted_acceptance_ids must be a list")
            impacted = []
        for impacted_id in impacted:
            if impacted_id not in mapped_set:
                errors.append(f"{label} references unmapped acceptance ID: {impacted_id}")
        non_impact_reason = item.get("non_impact_reason", "")
        if not impacted and (not isinstance(non_impact_reason, str) or not non_impact_reason.strip()):
            errors.append(f"{label} needs impacted_acceptance_ids or non_impact_reason")
        test_ids = item.get("test_ids", [])
        if not isinstance(test_ids, list):
            errors.append(f"{label}.test_ids must be a list")
        else:
            for test_id in test_ids:
                if test_id not in result_by_id:
                    errors.append(f"{label} references unknown test_id: {test_id}")
        _validate_evidence_path_list(
            run_dir,
            item.get("evidence_paths", []),
            f"{label}.evidence_paths",
            errors,
            allow_empty=not bool(impacted),
        )

    summary = {
        "status": status_value,
        "row_count": len(rows_raw),
        "declared_acceptance_count": len(declared_ids),
        "mapped_acceptance_count": len(mapped_set),
        "blocking_acceptance_count": blocking_count,
        "passing_acceptance_count": passing_count,
    }
    manifest["_derived_traceability"] = summary
    return summary


def _validate_result(
    run_dir: Path,
    item: Any,
    index: int,
    errors: list[str],
    seen_ids: set[str],
) -> Optional[dict[str, Any]]:
    label = f"results[{index}]"
    if not isinstance(item, dict):
        errors.append(f"{label} must be an object")
        return None
    test_id = _required_text(item.get("test_id"), f"{label}.test_id", errors)
    gate = _required_text(item.get("gate"), f"{label}.gate", errors)
    if test_id:
        if test_id in seen_ids:
            errors.append(f"duplicate test_id: {test_id}")
        seen_ids.add(test_id)
    status_value = item.get("status")
    if status_value not in ALLOWED_STATUSES:
        errors.append(f"invalid {label}.status: {status_value!r}")
        status_value = ""
    elif status_value not in FINAL_STATUSES:
        errors.append(f"non-final status in final run: {test_id}={status_value}")
    blocking = item.get("blocking")
    if not isinstance(blocking, bool):
        errors.append(f"{label}.blocking must be boolean")
    _required_text(item.get("expected"), f"{label}.expected", errors)
    if status_value in {"PASS", "FAIL"}:
        _required_text(item.get("actual"), f"{label}.actual", errors)
        paths = _required_list(item.get("evidence_paths"), f"{label}.evidence_paths", errors)
        for path_index, raw_path in enumerate(paths):
            _safe_relative_file(run_dir, raw_path, f"{label}.evidence_paths[{path_index}]", errors)
    else:
        _required_text(item.get("reason"), f"{label}.reason for {status_value}", errors)
        paths = item.get("evidence_paths", [])
        if not isinstance(paths, list):
            errors.append(f"{label}.evidence_paths must be a list")
        else:
            for path_index, raw_path in enumerate(paths):
                _safe_relative_file(run_dir, raw_path, f"{label}.evidence_paths[{path_index}]", errors)
    attempts = item.get("attempts")
    if not isinstance(attempts, int) or attempts < 0:
        errors.append(f"{label}.attempts must be a non-negative integer")
    elif status_value in {"PASS", "FAIL"} and attempts < 1:
        errors.append(f"{label}.attempts must be >= 1 for {status_value}")
    if status_value == "WAIVED":
        _required_text(item.get("finding_id"), f"{label}.finding_id for WAIVED", errors)
    return item if gate else None


def _open_finding(item: dict[str, Any]) -> bool:
    return item.get("status") in {"OPEN", "CONFIRMED", "WAIVED", "RETEST_PENDING"}


def _validate_findings(
    run_dir: Path, findings: Any, errors: list[str]
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    if not isinstance(findings, list):
        errors.append("findings must be a list")
        return [], {}
    valid: list[dict[str, Any]] = []
    by_id: dict[str, dict[str, Any]] = {}
    for index, item in enumerate(findings):
        label = f"findings[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        finding_id = _required_text(item.get("id"), f"{label}.id", errors)
        if finding_id in by_id:
            errors.append(f"duplicate finding id: {finding_id}")
        finding_type = item.get("type")
        severity = item.get("severity")
        status_value = item.get("status")
        category = _required_text(item.get("category"), f"{label}.category", errors)
        if finding_type not in ALLOWED_FINDING_TYPES:
            errors.append(f"invalid {label}.type: {finding_type!r}")
        if severity not in ALLOWED_FINDING_SEVERITIES:
            errors.append(f"invalid {label}.severity: {severity!r}")
        if status_value not in ALLOWED_FINDING_STATUSES:
            errors.append(f"invalid {label}.status: {status_value!r}")
        if severity == "L0" and item.get("non_waivable") is not True:
            errors.append(f"L0 finding must set non_waivable=true: {finding_id}")
        if category in NON_WAIVABLE_CATEGORIES and item.get("non_waivable") is not True:
            errors.append(f"non-waivable category must set non_waivable=true: {finding_id}")
        evidence_paths = item.get("evidence_paths", [])
        if not isinstance(evidence_paths, list):
            errors.append(f"{label}.evidence_paths must be a list")
        else:
            for path_index, raw_path in enumerate(evidence_paths):
                _safe_relative_file(run_dir, raw_path, f"{label}.evidence_paths[{path_index}]", errors)
        if finding_id:
            by_id[finding_id] = item
        valid.append(item)
    return valid, by_id


def _validate_waivers(
    waivers: Any,
    findings_by_id: dict[str, dict[str, Any]],
    subject_identity: str,
    run_ended_at: Optional[datetime],
    errors: list[str],
) -> list[dict[str, Any]]:
    if not isinstance(waivers, list):
        errors.append("waivers must be a list")
        return []
    valid: list[dict[str, Any]] = []
    seen: set[str] = set()
    required = (
        "id",
        "finding_id",
        "owner",
        "reason",
        "residual_risk",
        "applies_to_identity",
        "expires_at",
        "retest_plan",
    )
    for index, item in enumerate(waivers):
        label = f"waivers[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be an object")
            continue
        for key in required:
            _required_text(item.get(key), f"{label}.{key}", errors)
        waiver_id = str(item.get("id", ""))
        if waiver_id in seen:
            errors.append(f"duplicate waiver id: {waiver_id}")
        seen.add(waiver_id)
        controls = item.get("compensating_controls")
        _required_list(controls, f"{label}.compensating_controls", errors)
        finding_id = item.get("finding_id")
        finding = findings_by_id.get(finding_id)
        if finding is None:
            errors.append(f"waiver references unknown finding: {finding_id}")
        else:
            if finding.get("severity") == "L0" or finding.get("non_waivable") is True:
                errors.append(f"waiver attempts to waive non-waivable finding: {finding_id}")
            if finding.get("category") in NON_WAIVABLE_CATEGORIES:
                errors.append(f"waiver attempts to waive non-waivable category: {finding_id}")
            if finding.get("status") != "WAIVED":
                errors.append(f"waived finding must have status WAIVED: {finding_id}")
        if subject_identity and item.get("applies_to_identity") != subject_identity:
            errors.append(f"waiver identity does not match acceptance subject: {waiver_id}")
        expires_at = _parse_timestamp(item.get("expires_at"), f"{label}.expires_at", errors)
        if run_ended_at is not None and expires_at is not None and expires_at <= run_ended_at:
            errors.append(f"waiver was already expired at run end: {waiver_id}")
        valid.append(item)
    return valid


def _gate_statuses(results: list[dict[str, Any]]) -> dict[str, set[str]]:
    gates: dict[str, set[str]] = {}
    for item in results:
        gate = item.get("gate")
        status_value = item.get("status")
        if isinstance(gate, str) and isinstance(status_value, str):
            gates.setdefault(gate, set()).add(status_value)
    return gates


def _require_gate(
    gates: dict[str, set[str]], gate: str, allowed: set[str], errors: list[str]
) -> None:
    statuses = gates.get(gate)
    if not statuses:
        errors.append(f"missing required gate result: {gate}")
        return
    if not statuses.issubset(allowed) or not statuses.intersection(allowed):
        errors.append(f"gate {gate} has unacceptable status set: {sorted(statuses)}")


def _subject_identity(subject: dict[str, Any]) -> str:
    for key in ("image_digest", "artifact_sha256", "source_snapshot_sha256", "git_head", "deployment_identity", "package_version"):
        value = subject.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _validate_identity(
    run_dir: Path,
    manifest: dict[str, Any],
    verdict: str,
    decision_scope: str,
    errors: list[str],
) -> str:
    subject = _get_object(manifest, "subject", errors)
    _required_text(subject.get("repository"), "subject.repository", errors)
    identity = _subject_identity(subject)
    if verdict in {"PASS", "PASS_WITH_RISKS", "FAIL"} and not identity:
        errors.append("no immutable subject identity is recorded")
    git_head = subject.get("git_head", "")
    if git_head and (
        not isinstance(git_head, str)
        or not HEX_RE.fullmatch(git_head)
        or len(git_head) not in {7, 8, 9, 10, 11, 12, 40, 64}
    ):
        errors.append("subject.git_head must be a recognized hexadecimal revision length")
    artifact_sha = subject.get("artifact_sha256", "")
    if artifact_sha and (
        not isinstance(artifact_sha, str) or not SHA256_RE.fullmatch(artifact_sha)
    ):
        errors.append("subject.artifact_sha256 must be 64 hexadecimal characters")
    source_snapshot_sha = subject.get("source_snapshot_sha256", "")
    if source_snapshot_sha and (
        not isinstance(source_snapshot_sha, str) or not SHA256_RE.fullmatch(source_snapshot_sha)
    ):
        errors.append("subject.source_snapshot_sha256 must be 64 hexadecimal characters")
    if source_snapshot_sha:
        _validate_evidence_path_list(
            run_dir,
            subject.get("source_snapshot_evidence_paths"),
            "subject.source_snapshot_evidence_paths",
            errors,
        )
    image_digest = subject.get("image_digest", "")
    if image_digest and (
        not isinstance(image_digest, str) or not IMAGE_DIGEST_RE.fullmatch(image_digest)
    ):
        errors.append("subject.image_digest must be sha256:<64 hex>")

    positive = verdict in {"PASS", "PASS_WITH_RISKS"}
    digest_bound = bool(
        (isinstance(image_digest, str) and IMAGE_DIGEST_RE.fullmatch(image_digest))
        or (isinstance(artifact_sha, str) and SHA256_RE.fullmatch(artifact_sha))
        or (isinstance(source_snapshot_sha, str) and SHA256_RE.fullmatch(source_snapshot_sha))
        or (isinstance(git_head, str) and HEX_RE.fullmatch(git_head) and len(git_head) in {40, 64})
    )
    if positive and not digest_bound:
        errors.append(
            "positive verdict requires image digest, artifact SHA-256, source snapshot SHA-256, or full git commit"
        )
    if positive and subject.get("source_dirty") is True and not (
        (isinstance(source_snapshot_sha, str) and SHA256_RE.fullmatch(source_snapshot_sha))
        or (isinstance(artifact_sha, str) and SHA256_RE.fullmatch(artifact_sha))
        or (isinstance(image_digest, str) and IMAGE_DIGEST_RE.fullmatch(image_digest))
    ):
        errors.append("dirty source positive verdict requires a hashed source snapshot or built artifact/image")

    # Optional supply-chain evidence is still path-checked when present.
    for key in ("sbom_paths", "provenance_paths"):
        value = subject.get(key, [])
        _validate_evidence_path_list(
            run_dir, value, f"subject.{key}", errors, allow_empty=True
        )
    signature = _get_object(subject, "signature_verification", errors)
    signature_status = signature.get("status")
    if signature_status not in {"PASS", "FAIL", "BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}:
        errors.append(f"invalid subject.signature_verification.status: {signature_status!r}")
    if signature_status in {"PASS", "FAIL"}:
        _validate_evidence_path_list(
            run_dir,
            signature.get("evidence_paths"),
            "subject.signature_verification.evidence_paths",
            errors,
        )
        if signature_status == "FAIL":
            _required_text(
                signature.get("reason"),
                "subject.signature_verification.reason for FAIL",
                errors,
            )
    elif signature_status in {"BLOCKED", "NOT_RUN", "NOT_APPLICABLE"}:
        _required_text(
            signature.get("reason"),
            f"subject.signature_verification.reason for {signature_status}",
            errors,
        )

    if decision_scope != "developer_check" and verdict in {"PASS", "PASS_WITH_RISKS"}:
        if signature_status == "FAIL":
            errors.append("formal release acceptance cannot pass after signature verification FAIL")
        if subject.get("source_dirty") is not False:
            errors.append("formal release acceptance requires source_dirty=false")
        if not (
            SHA256_RE.fullmatch(str(artifact_sha))
            or IMAGE_DIGEST_RE.fullmatch(str(image_digest))
        ):
            errors.append("formal release acceptance requires artifact_sha256 or image_digest")
        _validate_evidence_path_list(
            run_dir,
            subject.get("source_to_artifact_mapping_evidence"),
            "subject.source_to_artifact_mapping_evidence",
            errors,
        )
    return identity

def _validate_release(
    run_dir: Path,
    manifest: dict[str, Any],
    verdict: str,
    gates: dict[str, set[str]],
    errors: list[str],
) -> str:
    release = _get_object(manifest, "release", errors)
    decision_scope = release.get("decision_scope")
    if decision_scope not in ALLOWED_DECISION_SCOPES:
        errors.append(f"invalid release.decision_scope: {decision_scope!r}")
        decision_scope = ""
    intent = release.get("intent")
    if intent not in {"none", "internal", "staged", "production"}:
        errors.append(f"invalid release.intent: {intent!r}")
    strategy = release.get("strategy")
    if strategy not in {"not-applicable", "canary", "ring", "blue-green", "rolling"}:
        errors.append(f"invalid release.strategy: {strategy!r}")

    positive = verdict in {"PASS", "PASS_WITH_RISKS"}
    if positive and decision_scope in {"release_candidate", "staged_release", "post_deploy"}:
        if intent == "none":
            errors.append("positive release-scope verdict requires release.intent other than none")
        _require_gate(gates, "operational_readiness", {"PASS"}, errors)
        _require_gate(gates, "rollback_or_rollforward", {"PASS"}, errors)
        _required_text(release.get("candidate_version"), "release.candidate_version", errors)
        candidate_identity = _required_text(
            release.get("candidate_identity"), "release.candidate_identity", errors
        )
        subject = _get_object(manifest, "subject", errors)
        # A release candidate must be bound to immutable bytes, not merely a
        # human-readable build ID or package version.
        accepted_identities = {
            str(value).strip()
            for value in (
                subject.get("image_digest"),
                subject.get("artifact_sha256"),
            )
            if isinstance(value, str) and value.strip()
        }
        if candidate_identity and candidate_identity not in accepted_identities:
            errors.append(
                "release.candidate_identity is not bound to the recorded build/artifact/image identity"
            )
        _required_list(release.get("health_signals"), "release.health_signals", errors)
        _required_list(release.get("business_invariants"), "release.business_invariants", errors)
        _required_list(release.get("abort_conditions"), "release.abort_conditions", errors)
        recovery = _get_object(release, "rollback_or_rollforward", errors)
        if recovery.get("tested") is not True or recovery.get("status") != "PASS":
            errors.append("release rollback_or_rollforward must be tested and PASS")
        _required_text(recovery.get("method"), "release.rollback_or_rollforward.method", errors)
        _validate_evidence_path_list(
            run_dir,
            recovery.get("evidence_paths"),
            "release.rollback_or_rollforward.evidence_paths",
            errors,
        )

        baseline = _get_object(manifest, "baseline", errors)
        baseline_reference = baseline.get("reference")
        baseline_pack_hash = baseline.get("acceptance_pack_hash", "")
        if baseline_pack_hash and (
            not isinstance(baseline_pack_hash, str)
            or not SHA256_RE.fullmatch(baseline_pack_hash)
        ):
            errors.append("baseline.acceptance_pack_hash must be a 64-character SHA-256")
        if isinstance(baseline_reference, str) and baseline_reference.strip():
            if not isinstance(baseline_pack_hash, str) or not SHA256_RE.fullmatch(baseline_pack_hash):
                errors.append("baseline reference requires acceptance_pack_hash")
            if baseline.get("comparison_status") != "PASS":
                errors.append("baseline comparison_status must be PASS when a baseline is supplied")
            _validate_evidence_path_list(
                run_dir,
                baseline.get("evidence_paths"),
                "baseline.evidence_paths",
                errors,
            )
        else:
            _required_text(baseline.get("reason_if_absent"), "baseline.reason_if_absent", errors)

        operations = _get_object(manifest, "operations", errors)
        _required_text(operations.get("owner_or_oncall"), "operations.owner_or_oncall", errors)
        _required_list(operations.get("runbook_paths"), "operations.runbook_paths", errors)
        _required_list(
            operations.get("dashboard_or_query_refs"),
            "operations.dashboard_or_query_refs",
            errors,
        )
        _required_list(operations.get("alert_tests"), "operations.alert_tests", errors)
        _required_list(
            operations.get("slo_or_health_objectives"),
            "operations.slo_or_health_objectives",
            errors,
        )
        _validate_evidence_path_list(
            run_dir,
            operations.get("capacity_evidence_paths"),
            "operations.capacity_evidence_paths",
            errors,
        )
        backup = _get_object(operations, "backup_restore", errors)
        if backup.get("status") not in {"PASS", "NOT_APPLICABLE"}:
            errors.append("operations.backup_restore.status must be PASS or NOT_APPLICABLE")
        if backup.get("status") == "NOT_APPLICABLE":
            _required_text(backup.get("reason"), "operations.backup_restore.reason", errors)
        else:
            _validate_evidence_path_list(
                run_dir,
                backup.get("evidence_paths"),
                "operations.backup_restore.evidence_paths",
                errors,
            )

        if intent == "production":
            if strategy == "not-applicable":
                errors.append("production release candidate requires a progressive deployment strategy")
            _required_list(release.get("rollout_groups"), "release.rollout_groups", errors)

    if positive and decision_scope in {"staged_release", "post_deploy"}:
        _require_gate(gates, "staged_release_observation", {"PASS"}, errors)
        if strategy == "not-applicable":
            errors.append("staged/post-deploy acceptance requires a progressive release strategy")
        _required_list(release.get("rollout_groups"), "release.rollout_groups", errors)
        subject = _get_object(manifest, "subject", errors)
        _required_text(subject.get("deployment_identity"), "subject.deployment_identity", errors)
        _validate_evidence_path_list(
            run_dir,
            subject.get("deployment_mapping_evidence_paths"),
            "subject.deployment_mapping_evidence_paths",
            errors,
        )
        bake = _get_object(release, "bake", errors)
        required_seconds = bake.get("required_seconds")
        observed_seconds = bake.get("observed_seconds")
        if not isinstance(required_seconds, int) or required_seconds <= 0:
            errors.append("release.bake.required_seconds must be a positive integer")
        if not isinstance(observed_seconds, int) or observed_seconds < 0:
            errors.append("release.bake.observed_seconds must be a non-negative integer")
        if (
            isinstance(required_seconds, int)
            and isinstance(observed_seconds, int)
            and observed_seconds < required_seconds
        ):
            errors.append("observed bake time is shorter than required bake time")
        if bake.get("status") != "PASS":
            errors.append("release.bake.status must be PASS for staged/post-deploy verdict")
        _validate_evidence_path_list(
            run_dir,
            bake.get("evidence_paths"),
            "release.bake.evidence_paths",
            errors,
        )

    if positive and decision_scope == "post_deploy":
        post = _get_object(release, "post_deploy", errors)
        if post.get("status") != "PASS":
            errors.append("release.post_deploy.status must be PASS")
        observation_start = _parse_timestamp(
            post.get("observation_start"), "release.post_deploy.observation_start", errors
        )
        observation_end = _parse_timestamp(
            post.get("observation_end"), "release.post_deploy.observation_end", errors
        )
        if (
            observation_start is not None
            and observation_end is not None
            and observation_end <= observation_start
        ):
            errors.append("post-deploy observation_end must be after observation_start")
        _validate_evidence_path_list(
            run_dir,
            post.get("evidence_paths"),
            "release.post_deploy.evidence_paths",
            errors,
        )
    return decision_scope

def _validate_ai(
    run_dir: Path,
    manifest: dict[str, Any],
    verdict: str,
    gates: dict[str, set[str]],
    errors: list[str],
) -> None:
    ai = _get_object(manifest, "ai_system", errors)
    applicable = ai.get("applicable")
    if not isinstance(applicable, bool):
        errors.append("ai_system.applicable must be boolean")
        return
    if not applicable:
        return
    positive = verdict in {"PASS", "PASS_WITH_RISKS"}
    if not positive:
        return

    _require_gate(gates, "ai_eval", {"PASS"}, errors)
    _required_text(ai.get("model_provider"), "ai_system.model_provider", errors)
    _required_text(ai.get("model_id"), "ai_system.model_id", errors)
    if not _required_text(ai.get("model_snapshot"), "ai_system.model_snapshot", []):
        _required_text(
            ai.get("model_snapshot_reason"),
            "ai_system.model_snapshot_reason when snapshot unavailable",
            errors,
        )
    for key in ("prompt_or_policy_hash", "toolset_or_harness_hash"):
        value = _required_text(ai.get(key), f"ai_system.{key}", errors)
        if value and not SHA256_RE.fullmatch(value):
            errors.append(f"ai_system.{key} must be a 64-character SHA-256")

    trial_count = ai.get("trial_count")
    if not isinstance(trial_count, int) or trial_count < 3:
        errors.append("positive AI verdict requires ai_system.trial_count >= 3")
    task_slices_raw = _required_list(ai.get("task_slices"), "ai_system.task_slices", errors)
    task_slices: list[str] = []
    for index, value in enumerate(task_slices_raw):
        task_slice = _required_text(value, f"ai_system.task_slices[{index}]", errors)
        if task_slice:
            task_slices.append(task_slice)
    if len(task_slices) != len(set(task_slices)):
        errors.append("ai_system.task_slices must be unique")

    trial_records = _required_list(ai.get("trial_records"), "ai_system.trial_records", errors)
    if isinstance(trial_count, int) and len(trial_records) != trial_count:
        errors.append("ai_system.trial_records count must equal trial_count")
    seen_trial_ids: set[str] = set()
    seen_context_ids: set[str] = set()
    represented_slices: set[str] = set()
    passed_trials = 0
    for index, record in enumerate(trial_records):
        label = f"ai_system.trial_records[{index}]"
        if not isinstance(record, dict):
            errors.append(f"{label} must be an object")
            continue
        trial_id = _required_text(record.get("trial_id"), f"{label}.trial_id", errors)
        if trial_id in seen_trial_ids:
            errors.append(f"duplicate AI trial_id: {trial_id}")
        seen_trial_ids.add(trial_id)
        context_id = _required_text(record.get("context_id"), f"{label}.context_id", errors)
        if context_id in seen_context_ids:
            errors.append(f"duplicate AI context_id: {context_id}")
        seen_context_ids.add(context_id)
        task_slice = _required_text(record.get("task_slice"), f"{label}.task_slice", errors)
        if task_slice:
            represented_slices.add(task_slice)
            if task_slices and task_slice not in task_slices:
                errors.append(f"{label}.task_slice is not declared in ai_system.task_slices")
        status_value = record.get("status")
        if status_value not in {"PASS", "FAIL"}:
            errors.append(f"{label}.status must be PASS or FAIL")
        elif status_value == "PASS":
            passed_trials += 1
        _required_text(record.get("outcome"), f"{label}.outcome", errors)
        for key in ("reset_evidence_path", "outcome_evidence_path", "trace_path"):
            _safe_relative_file(run_dir, record.get(key), f"{label}.{key}", errors)
        cost = record.get("cost")
        latency_ms = record.get("latency_ms")
        if not isinstance(cost, (int, float)) or isinstance(cost, bool) or cost < 0:
            errors.append(f"{label}.cost must be a non-negative number")
        if not isinstance(latency_ms, (int, float)) or isinstance(latency_ms, bool) or latency_ms < 0:
            errors.append(f"{label}.latency_ms must be a non-negative number")
    missing_slices = sorted(set(task_slices) - represented_slices)
    if missing_slices:
        errors.append(f"AI task slices without executed trials: {missing_slices}")

    success_threshold = ai.get("success_threshold")
    observed_pass_rate = ai.get("observed_pass_rate")
    if not isinstance(success_threshold, (int, float)) or isinstance(success_threshold, bool) or not 0 <= success_threshold <= 1:
        errors.append("ai_system.success_threshold must be a number from 0 to 1")
    if not isinstance(observed_pass_rate, (int, float)) or isinstance(observed_pass_rate, bool) or not 0 <= observed_pass_rate <= 1:
        errors.append("ai_system.observed_pass_rate must be a number from 0 to 1")
    computed_pass_rate = (passed_trials / len(trial_records)) if trial_records else 0.0
    if isinstance(observed_pass_rate, (int, float)) and not isinstance(observed_pass_rate, bool):
        if abs(float(observed_pass_rate) - computed_pass_rate) > 1e-9:
            errors.append("ai_system.observed_pass_rate does not match executed trial records")
    if (
        isinstance(success_threshold, (int, float))
        and not isinstance(success_threshold, bool)
        and computed_pass_rate < float(success_threshold)
    ):
        errors.append("AI observed pass rate is below success_threshold")

    # A healthy overall average must not conceal a failed critical task slice.
    # Every declared task slice is a blocking acceptance slice: it needs at
    # least three independent trials and must individually meet the same
    # predeclared threshold. Exploratory/non-blocking probes should not be
    # placed in task_slices; report them as additional results/findings.
    slice_trials: dict[str, list[str]] = {task_slice: [] for task_slice in task_slices}
    for record in trial_records:
        if not isinstance(record, dict):
            continue
        task_slice = record.get("task_slice")
        status_value = record.get("status")
        if isinstance(task_slice, str) and task_slice in slice_trials and status_value in {"PASS", "FAIL"}:
            slice_trials[task_slice].append(status_value)
    derived_slice_results: list[dict[str, Any]] = []
    valid_threshold = (
        float(success_threshold)
        if isinstance(success_threshold, (int, float))
        and not isinstance(success_threshold, bool)
        and 0 <= float(success_threshold) <= 1
        else None
    )
    for task_slice in task_slices:
        statuses = slice_trials.get(task_slice, [])
        if len(statuses) < 3:
            errors.append(
                f"AI task slice {task_slice!r} requires at least 3 independent trials; got {len(statuses)}"
            )
        slice_pass_rate = (
            sum(status == "PASS" for status in statuses) / len(statuses) if statuses else 0.0
        )
        if valid_threshold is not None and slice_pass_rate < valid_threshold:
            errors.append(
                f"AI task slice {task_slice!r} pass rate {slice_pass_rate:.6f} is below success_threshold {valid_threshold:.6f}"
            )
        derived_slice_results.append(
            {
                "task_slice": task_slice,
                "trial_count": len(statuses),
                "pass_count": sum(status == "PASS" for status in statuses),
                "observed_pass_rate": slice_pass_rate,
            }
        )
    manifest["_derived_ai"] = {
        "trial_count": len(trial_records),
        "observed_pass_rate": computed_pass_rate,
        "task_slice_results": derived_slice_results,
    }

    outcome_grader = _required_text(ai.get("outcome_grader"), "ai_system.outcome_grader", errors)
    if outcome_grader and "self-report" in outcome_grader.lower():
        errors.append("AI outcome grader cannot be self-report only")
    _required_text(ai.get("judge_calibration"), "ai_system.judge_calibration", errors)
    evaluator = _get_object(ai, "evaluator_independence", errors)
    grader_type = evaluator.get("primary_grader_type")
    if grader_type not in {"deterministic", "programmatic", "model", "human", "composite"}:
        errors.append("ai_system.evaluator_independence.primary_grader_type is invalid")
    if evaluator.get("generator_is_sole_judge") is not False:
        errors.append("positive AI verdict forbids the generator as the sole judge")
    evaluator_ids_raw = _required_list(
        evaluator.get("independent_evaluator_ids"),
        "ai_system.evaluator_independence.independent_evaluator_ids",
        errors,
    )
    evaluator_ids: list[str] = []
    for index, value in enumerate(evaluator_ids_raw):
        evaluator_id = _required_text(
            value, f"ai_system.evaluator_independence.independent_evaluator_ids[{index}]", errors
        )
        if evaluator_id:
            evaluator_ids.append(evaluator_id)
    if len(evaluator_ids) != len(set(evaluator_ids)):
        errors.append("AI independent_evaluator_ids must be unique")
    _required_text(
        evaluator.get("disagreement_policy"),
        "ai_system.evaluator_independence.disagreement_policy",
        errors,
    )
    _validate_evidence_path_list(
        run_dir,
        evaluator.get("evidence_paths"),
        "ai_system.evaluator_independence.evidence_paths",
        errors,
    )
    if grader_type in {"model", "composite"}:
        if evaluator.get("cross_model_review") is not True:
            errors.append("model/composite AI grading requires cross_model_review=true")
        if evaluator.get("blind_evaluation") is not True:
            errors.append("model/composite AI grading requires blind_evaluation=true")
        generator_model = str(ai.get("model_id", "")).strip()
        if generator_model and not any(value != generator_model for value in evaluator_ids):
            errors.append("model/composite grading requires an evaluator distinct from the generator model")
    else:
        for key in ("cross_model_review", "blind_evaluation"):
            if not isinstance(evaluator.get(key), bool):
                errors.append(f"ai_system.evaluator_independence.{key} must be boolean")
    baseline_reference = ai.get("baseline_reference")
    if not isinstance(baseline_reference, str) or not baseline_reference.strip():
        _required_text(
            ai.get("baseline_reason_if_absent"),
            "ai_system.baseline_reason_if_absent",
            errors,
        )
    _required_list(ai.get("safety_checks"), "ai_system.safety_checks", errors)
    if ai.get("safety_gate_status") != "PASS":
        errors.append("positive AI verdict requires ai_system.safety_gate_status=PASS")
    _validate_evidence_path_list(
        run_dir,
        ai.get("safety_evidence_paths"),
        "ai_system.safety_evidence_paths",
        errors,
    )
    _validate_evidence_path_list(
        run_dir,
        ai.get("cost_latency_evidence_paths"),
        "ai_system.cost_latency_evidence_paths",
        errors,
    )
    _validate_evidence_path_list(
        run_dir,
        ai.get("trace_paths", []),
        "ai_system.trace_paths",
        errors,
        allow_empty=True,
    )

def validate_run(run_dir: Path) -> tuple[dict[str, Any], list[str]]:
    run_dir = _absolute_no_resolve(run_dir)
    errors: list[str] = []
    _check_tree(run_dir, errors)
    if errors:
        return {}, errors
    try:
        manifest = load_manifest(run_dir)
    except RunValidationError as error:
        return {}, [str(error)]

    if manifest.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")

    run = _get_object(manifest, "run", errors)
    for key in ("id", "started_at", "ended_at", "timezone", "verifier_identity", "independence_evidence"):
        _required_text(run.get(key), f"run.{key}", errors)
    started_at = _parse_timestamp(run.get("started_at"), "run.started_at", errors)
    ended_at = _parse_timestamp(run.get("ended_at"), "run.ended_at", errors)
    if started_at is not None and ended_at is not None and ended_at < started_at:
        errors.append("run.ended_at must not be earlier than run.started_at")
    profile = run.get("profile")
    if profile not in ALLOWED_PROFILES:
        errors.append(f"run.profile must resolve to one of {sorted(ALLOWED_PROFILES)}, not {profile!r}")
    risk_level = run.get("risk_level")
    if risk_level not in ALLOWED_RISK_LEVELS:
        errors.append(f"invalid run.risk_level: {risk_level!r}")
    _required_list(run.get("risk_triggers"), "run.risk_triggers", errors)
    independent_passes = run.get("independent_passes")
    if not isinstance(independent_passes, int) or independent_passes < 1:
        errors.append("run.independent_passes must be >= 1")

    scope = _get_object(manifest, "scope", errors)
    if scope.get("mode") != "single-project":
        errors.append('scope.mode must be "single-project"')
    if scope.get("verdict_scope") != "target-project-only":
        errors.append('scope.verdict_scope must be "target-project-only"')
    _required_text(scope.get("target_project_name"), "scope.target_project_name", errors)
    _required_text(scope.get("target_project_path"), "scope.target_project_path", errors)
    _required_list(scope.get("acceptance_closure"), "scope.acceptance_closure", errors)
    _validate_evidence_path_list(
        run_dir, scope.get("closure_evidence"), "scope.closure_evidence", errors
    )
    _required_list(scope.get("included_paths"), "scope.included_paths", errors)
    if not isinstance(scope.get("excluded_projects"), list):
        errors.append("scope.excluded_projects must be a list")

    evidence = _get_object(manifest, "evidence", errors)
    if evidence.get("redaction_reviewed") is not True:
        errors.append("evidence.redaction_reviewed must be true before finalization")
    retention = evidence.get("retention_days")
    if not isinstance(retention, int) or retention < 0:
        errors.append("evidence.retention_days must be a non-negative integer")

    verdict_obj = _get_object(manifest, "verdict", errors)
    verdict = verdict_obj.get("value")
    if verdict not in ALLOWED_VERDICTS:
        errors.append(f"invalid verdict.value: {verdict!r}")
        verdict = ""
    action = verdict_obj.get("action")
    expected_action = ACTION_BY_VERDICT.get(verdict)
    if expected_action and action != expected_action:
        errors.append(f"verdict {verdict} requires action {expected_action}, got {action!r}")
    _required_text(verdict_obj.get("reason"), "verdict.reason", errors)
    _required_text(verdict_obj.get("owner_next_action"), "verdict.owner_next_action", errors)

    raw_results = manifest.get("results")
    results_list = _required_list(raw_results, "results", errors)
    results: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for index, item in enumerate(results_list):
        validated = _validate_result(run_dir, item, index, errors, seen_ids)
        if validated is not None:
            results.append(validated)
    gates = _gate_statuses(results)

    decision_scope = _validate_release(run_dir, manifest, verdict, gates, errors)
    subject_identity = _validate_identity(run_dir, manifest, verdict, decision_scope, errors)
    taskpack = _validate_taskpack(run_dir, manifest, verdict, errors)
    _validate_traceability(
        run_dir, manifest, taskpack, subject_identity, results, verdict, errors
    )
    findings, findings_by_id = _validate_findings(run_dir, manifest.get("findings"), errors)
    waivers = _validate_waivers(
        manifest.get("waivers"), findings_by_id, subject_identity, ended_at, errors
    )
    waivers_by_finding: dict[str, list[dict[str, Any]]] = {}
    for waiver in waivers:
        finding_id = waiver.get("finding_id")
        if isinstance(finding_id, str):
            waivers_by_finding.setdefault(finding_id, []).append(waiver)
    for finding in findings:
        if finding.get("status") == "WAIVED":
            matching = waivers_by_finding.get(str(finding.get("id")), [])
            if len(matching) != 1:
                errors.append(
                    f"WAIVED finding requires exactly one matching waiver: {finding.get('id')}"
                )
    for result in results:
        if result.get("status") == "WAIVED":
            finding_id = str(result.get("finding_id", ""))
            if len(waivers_by_finding.get(finding_id, [])) != 1:
                errors.append(
                    f"WAIVED result requires exactly one matching finding waiver: {result.get('test_id')}"
                )
    _validate_ai(run_dir, manifest, verdict, gates, errors)

    positive = verdict in {"PASS", "PASS_WITH_RISKS"}
    if positive:
        for gate, allowed in BASE_GATES.items():
            _require_gate(gates, gate, allowed, errors)
        if risk_level in {"high", "critical"}:
            _require_gate(gates, "safety_security", {"PASS"}, errors)
        else:
            _require_gate(gates, "safety_security", {"PASS", "NOT_APPLICABLE"}, errors)
        if risk_level == "critical":
            if not isinstance(independent_passes, int) or independent_passes < 2:
                errors.append("critical positive verdict requires two independent passes")
            records = _required_list(
                run.get("independent_pass_records"),
                "run.independent_pass_records",
                errors,
            )
            if isinstance(independent_passes, int) and len(records) != independent_passes:
                errors.append("independent_pass_records count must equal independent_passes")
            identities: set[str] = set()
            contexts: set[str] = set()
            for index, record in enumerate(records):
                label = f"run.independent_pass_records[{index}]"
                if not isinstance(record, dict):
                    errors.append(f"{label} must be an object")
                    continue
                identity_value = _required_text(
                    record.get("verifier_identity"), f"{label}.verifier_identity", errors
                )
                context_value = _required_text(
                    record.get("context_id"), f"{label}.context_id", errors
                )
                if identity_value in identities:
                    errors.append("critical independent passes require distinct verifier identities")
                if context_value in contexts:
                    errors.append("critical independent passes require distinct context IDs")
                identities.add(identity_value)
                contexts.add(context_value)
                pass_verdict = record.get("verdict")
                if pass_verdict not in {"PASS", "PASS_WITH_RISKS"}:
                    errors.append(f"{label}.verdict must be PASS or PASS_WITH_RISKS")
                if verdict == "PASS" and pass_verdict != "PASS":
                    errors.append("overall critical PASS requires every independent pass to be PASS")
                pass_subject_identity = _required_text(
                    record.get("subject_identity"), f"{label}.subject_identity", errors
                )
                if subject_identity and pass_subject_identity != subject_identity:
                    errors.append(f"{label}.subject_identity does not match acceptance subject")
                evidence_root = _required_text(
                    record.get("evidence_root_sha256"), f"{label}.evidence_root_sha256", errors
                )
                if evidence_root and not SHA256_RE.fullmatch(evidence_root):
                    errors.append(f"{label}.evidence_root_sha256 must be a 64-character SHA-256")
                _validate_evidence_path_list(
                    run_dir,
                    record.get("evidence_paths"),
                    f"{label}.evidence_paths",
                    errors,
                )
            if run.get("verifier_identity") not in identities:
                errors.append("primary run.verifier_identity is absent from independent_pass_records")

    blocking_bad = [
        item
        for item in results
        if item.get("blocking") is True and item.get("status") in {"FAIL", "BLOCKED", "NOT_RUN"}
    ]
    open_findings = [item for item in findings if _open_finding(item)]
    open_l0_l1 = [item for item in open_findings if item.get("severity") in {"L0", "L1"}]
    open_non_waivable = [
        item
        for item in open_findings
        if item.get("severity") == "L0"
        or item.get("non_waivable") is True
        or item.get("category") in NON_WAIVABLE_CATEGORIES
    ]

    if verdict == "PASS":
        if blocking_bad:
            errors.append("PASS cannot contain blocking FAIL/BLOCKED/NOT_RUN results")
        if waivers:
            errors.append("PASS cannot contain waivers; use PASS_WITH_RISKS")
        if any(item.get("status") == "WAIVED" for item in results):
            errors.append("PASS cannot contain WAIVED test results")
        if open_l0_l1:
            errors.append("PASS cannot contain open L0/L1 findings")
        risky_open = [
            item
            for item in open_findings
            if item.get("type") != "OBSERVATION" and item.get("status") != "CLOSED"
        ]
        if risky_open:
            errors.append("PASS cannot contain open defect/risk findings")
    elif verdict == "PASS_WITH_RISKS":
        if blocking_bad:
            errors.append("PASS_WITH_RISKS cannot contain blocking FAIL/BLOCKED/NOT_RUN")
        if open_non_waivable:
            errors.append("PASS_WITH_RISKS cannot contain non-waivable findings")
        if not waivers and not any(item.get("severity") == "L2" for item in open_findings):
            errors.append("PASS_WITH_RISKS requires a valid waiver or open L2 residual risk")
        for item in open_l0_l1:
            if item.get("status") != "WAIVED":
                errors.append(f"open L1 must be explicitly waived for PASS_WITH_RISKS: {item.get('id')}")
    elif verdict == "FAIL":
        if not blocking_bad and not open_l0_l1:
            errors.append("FAIL requires a blocking failed result or open L0/L1 finding")
    elif verdict == "BLOCKED":
        blocked = [
            item for item in results if item.get("status") in {"BLOCKED", "NOT_RUN"} and item.get("blocking") is True
        ]
        if not blocked:
            errors.append("BLOCKED requires at least one blocking BLOCKED/NOT_RUN result")
    elif verdict == "UNSAFE":
        incidents = manifest.get("abort_or_incidents")
        if not isinstance(incidents, list):
            errors.append("abort_or_incidents must be a list")
        elif not incidents and not open_non_waivable:
            errors.append("UNSAFE requires an abort/incident or non-waivable open finding")

    verdict_path = run_dir / "VERDICT.md"
    try:
        verdict_text = verdict_path.read_text(encoding="utf-8")
    except OSError as error:
        errors.append(f"cannot read VERDICT.md: {error}")
    else:
        first_line = verdict_text.splitlines()[0].strip() if verdict_text.splitlines() else ""
        if action and first_line != f"ACTION: {action}":
            errors.append(f"VERDICT.md first line must be ACTION: {action}")
        first_screen = verdict_text.split("\n---\n", 1)[0]
        if PLACEHOLDER_RE.search(first_screen):
            errors.append("VERDICT.md first screen contains unresolved <placeholder>")
        if verdict and verdict not in verdict_text:
            errors.append("VERDICT.md does not contain the machine verdict value")

    return manifest, errors


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        while True:
            block = handle.read(1024 * 1024)
            if not block:
                break
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _evidence_files(run_dir: Path) -> list[Path]:
    files: list[Path] = []
    for path in run_dir.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative = path.relative_to(run_dir).as_posix()
        if relative in SEAL_FILES:
            continue
        files.append(path)
    return sorted(files, key=lambda p: p.relative_to(run_dir).as_posix())


def _build_index(run_dir: Path) -> dict[str, Any]:
    entries: list[dict[str, Any]] = []
    root_hasher = hashlib.sha256()
    for path in _evidence_files(run_dir):
        relative = path.relative_to(run_dir).as_posix()
        sha256, size = _sha256_file(path)
        entries.append({"path": relative, "sha256": sha256, "size": size})
        root_hasher.update(f"{sha256} {size} {relative}\n".encode("utf-8"))
    return {
        "schema_version": SCHEMA_VERSION,
        "algorithm": "sha256",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "run_directory": run_dir.name,
        "file_count": len(entries),
        "files": entries,
        "evidence_root_sha256": root_hasher.hexdigest(),
        "excluded_seal_files": sorted(SEAL_FILES),
        "assurance_note": "Tamper-evident after finalization; not an authenticity signature.",
    }


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def _attestation_subject(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    subject = manifest["subject"]
    scope = manifest["scope"]
    name = str(subject.get("artifact_path") or scope.get("target_project_name") or "subject")
    image_digest = subject.get("image_digest", "")
    artifact_sha = subject.get("artifact_sha256", "")
    source_snapshot_sha = subject.get("source_snapshot_sha256", "")
    git_head = subject.get("git_head", "")
    if isinstance(image_digest, str) and IMAGE_DIGEST_RE.fullmatch(image_digest):
        return [{"name": name, "digest": {"sha256": image_digest.split(":", 1)[1].lower()}}]
    if isinstance(artifact_sha, str) and SHA256_RE.fullmatch(artifact_sha):
        return [{"name": name, "digest": {"sha256": artifact_sha.lower()}}]
    if isinstance(source_snapshot_sha, str) and SHA256_RE.fullmatch(source_snapshot_sha):
        return [{"name": name, "digest": {"sha256": source_snapshot_sha.lower()}}]
    if isinstance(git_head, str) and HEX_RE.fullmatch(git_head) and len(git_head) in {40, 64}:
        return [{"name": name, "digest": {"gitCommit": git_head.lower()}}]
    return []


def _expected_attestation(run_dir: Path, manifest: dict[str, Any]) -> dict[str, Any]:
    results = manifest.get("results", [])
    passed: list[str] = []
    warned: list[str] = []
    failed: list[str] = []
    for item in results if isinstance(results, list) else []:
        if not isinstance(item, dict):
            continue
        test_id = item.get("test_id")
        status_value = item.get("status")
        if not isinstance(test_id, str) or not test_id:
            continue
        if status_value == "PASS":
            passed.append(test_id)
        elif status_value == "WAIVED":
            warned.append(test_id)
        elif status_value in {"FAIL", "BLOCKED", "NOT_RUN"}:
            failed.append(test_id)

    configuration: list[dict[str, Any]] = []
    for relative in ("RUN_MANIFEST.yaml", "TRACEABILITY_MATRIX.json"):
        path = run_dir / relative
        digest, _ = _sha256_file(path)
        configuration.append({"name": relative, "digest": {"sha256": digest}})
    taskpack = manifest.get("taskpack", {})
    if isinstance(taskpack, dict) and taskpack.get("detected") is True:
        snapshot_digest = taskpack.get("source_snapshot_sha256")
        snapshot_path = taskpack.get("source_snapshot_path")
        if (
            isinstance(snapshot_digest, str)
            and SHA256_RE.fullmatch(snapshot_digest)
            and isinstance(snapshot_path, str)
            and snapshot_path
        ):
            configuration.append(
                {"name": snapshot_path, "digest": {"sha256": snapshot_digest.lower()}}
            )
        lock_path = run_dir / "raw-results/taskpack-lock.json"
        if lock_path.is_file() and not lock_path.is_symlink():
            lock_digest, _ = _sha256_file(lock_path)
            configuration.append(
                {"name": "raw-results/taskpack-lock.json", "digest": {"sha256": lock_digest}}
            )
        for record in sorted(taskpack.get("files", []), key=lambda item: str(item.get("role", ""))):
            if not isinstance(record, dict):
                continue
            digest = record.get("sha256")
            path = record.get("path")
            if isinstance(digest, str) and SHA256_RE.fullmatch(digest) and isinstance(path, str):
                configuration.append({"name": path, "digest": {"sha256": digest.lower()}})

    verdict_value = manifest["verdict"]["value"]
    predicate_result = {
        "PASS": "PASSED",
        "PASS_WITH_RISKS": "WARNED",
    }.get(verdict_value, "FAILED")
    return {
        "_type": "https://in-toto.io/Statement/v1",
        "subject": _attestation_subject(manifest),
        "predicateType": "https://in-toto.io/attestation/test-result/v0.1",
        "predicate": {
            "result": predicate_result,
            "configuration": configuration,
            "passedTests": sorted(passed),
            "warnedTests": sorted(warned),
            "failedTests": sorted(failed),
        },
    }


def _canonical_json_text(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _expected_decision(
    manifest: dict[str, Any],
    index: dict[str, Any],
    attestation_sha256: str,
) -> dict[str, Any]:
    release = manifest["release"]
    subject = manifest["subject"]
    scope = manifest["scope"]
    baseline = manifest["baseline"]
    evidence = manifest["evidence"]
    verdict = manifest["verdict"]
    taskpack = manifest.get("taskpack", {})
    traceability = manifest.get("_derived_traceability", {})
    ai_system = manifest.get("ai_system", {})
    derived_ai = manifest.get("_derived_ai", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "finalized_at": index["generated_at"],
        "target_project_name": scope["target_project_name"],
        "target_project_path": scope["target_project_path"],
        "decision_scope": release["decision_scope"],
        "candidate_identity": release.get("candidate_identity", ""),
        "subject_identity": _subject_identity(subject),
        "git_head": subject.get("git_head", ""),
        "artifact_sha256": subject.get("artifact_sha256", ""),
        "source_snapshot_sha256": subject.get("source_snapshot_sha256", ""),
        "image_digest": subject.get("image_digest", ""),
        "deployment_identity": subject.get("deployment_identity", ""),
        "taskpack_detected": bool(taskpack.get("detected", False)),
        "taskpack_declared_version": taskpack.get("declared_version", ""),
        "taskpack_digest_sha256": taskpack.get("pack_digest_sha256", ""),
        "taskpack_contract_digest_sha256": taskpack.get("contract_digest_sha256", ""),
        "taskpack_source_snapshot_sha256": taskpack.get("source_snapshot_sha256", ""),
        "taskpack_source_file_count": taskpack.get("source_file_count", 0),
        "traceability_status": traceability.get("status", ""),
        "traceability_row_count": traceability.get("row_count", 0),
        "traceability_declared_acceptance_count": traceability.get(
            "declared_acceptance_count", 0
        ),
        "taskpack_declared_task_count": len(taskpack.get("task_ids", []))
        if isinstance(taskpack, dict)
        else 0,
        "traceability_mapped_acceptance_count": traceability.get(
            "mapped_acceptance_count", 0
        ),
        "ai_applicable": bool(ai_system.get("applicable", False))
        if isinstance(ai_system, dict)
        else False,
        "ai_observed_pass_rate": derived_ai.get("observed_pass_rate", None)
        if isinstance(derived_ai, dict)
        else None,
        "ai_task_slice_results": derived_ai.get("task_slice_results", [])
        if isinstance(derived_ai, dict)
        else [],
        "baseline_reference": baseline.get("reference", ""),
        "baseline_acceptance_pack_hash": baseline.get("acceptance_pack_hash", ""),
        "external_signature_ref": evidence.get("external_signature_ref", ""),
        "verdict": verdict["value"],
        "action": verdict["action"],
        "reason": verdict["reason"],
        "owner_next_action": verdict["owner_next_action"],
        "evidence_root_sha256": index["evidence_root_sha256"],
        "evidence_index": "EVIDENCE_INDEX.json",
        "test_result_attestation": "ACCEPTANCE_ATTESTATION.intoto.json",
        "test_result_attestation_sha256": attestation_sha256,
        "attestation_predicate_type": "https://in-toto.io/attestation/test-result/v0.1",
        "assurance_note": (
            "Hash seal and unsigned in-toto statement provide internal consistency; "
            "authenticity requires a trusted external signature/provenance reference."
        ),
    }


def _canonical_sums(index: dict[str, Any]) -> str:
    return "".join(
        f"{entry['sha256']}  {entry['path']}\n"
        for entry in sorted(index["files"], key=lambda item: item["path"])
    )


def _write_seals_transactionally(run_dir: Path, contents: dict[str, str]) -> None:
    """Prepare all seal files, then publish; remove partial seals on failure."""
    temporary_paths: dict[str, Path] = {}
    published: list[Path] = []
    try:
        for name, text in contents.items():
            target = run_dir / name
            fd, temporary_name = tempfile.mkstemp(prefix=f".{name}.", dir=str(run_dir))
            temporary = Path(temporary_name)
            temporary_paths[name] = temporary
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
                handle.write(text)
                handle.flush()
                os.fsync(handle.fileno())
            if target.exists() or target.is_symlink():
                raise RunValidationError(f"seal path appeared during finalization: {name}")
        for name in sorted(contents):
            target = run_dir / name
            os.replace(temporary_paths[name], target)
            published.append(target)
            del temporary_paths[name]
    except Exception:
        for temporary in temporary_paths.values():
            try:
                temporary.unlink()
            except OSError:
                pass
        for target in published:
            try:
                target.unlink()
            except OSError:
                pass
        raise


def finalize(run_dir: Path) -> dict[str, Any]:
    run_dir = _absolute_no_resolve(run_dir)
    if run_dir.is_symlink():
        raise RunValidationError("run directory itself must not be a symlink")
    for name in SEAL_FILES:
        if (run_dir / name).exists() or (run_dir / name).is_symlink():
            raise RunValidationError(
                f"run is already sealed ({name} exists); verify it or create a new run instead of overwriting"
            )
    manifest, errors = validate_run(run_dir)
    if errors:
        raise RunValidationError("\n".join(f"- {error}" for error in errors))
    index = _build_index(run_dir)
    attestation = _expected_attestation(run_dir, manifest)
    attestation_text = _canonical_json_text(attestation)
    attestation_sha256 = hashlib.sha256(attestation_text.encode("utf-8")).hexdigest()
    decision = _expected_decision(manifest, index, attestation_sha256)
    contents = {
        "EVIDENCE_INDEX.json": _canonical_json_text(index),
        "FINAL_DECISION.json": _canonical_json_text(decision),
        "ACCEPTANCE_ATTESTATION.intoto.json": attestation_text,
        "SHA256SUMS.txt": _canonical_sums(index),
    }
    _write_seals_transactionally(run_dir, contents)
    try:
        verified = verify(run_dir)
    except Exception:
        for name in SEAL_FILES:
            try:
                (run_dir / name).unlink()
            except OSError:
                pass
        raise
    if verified != decision:
        for name in SEAL_FILES:
            try:
                (run_dir / name).unlink()
            except OSError:
                pass
        raise RunValidationError("post-publication seal verification mismatch")
    return verified


def _validate_seal_index(run_dir: Path, index: Any) -> list[dict[str, Any]]:
    if not isinstance(index, dict):
        raise RunValidationError("EVIDENCE_INDEX.json root must be an object")
    expected_keys = {
        "schema_version",
        "algorithm",
        "generated_at",
        "run_directory",
        "file_count",
        "files",
        "evidence_root_sha256",
        "excluded_seal_files",
        "assurance_note",
    }
    if set(index) != expected_keys:
        raise RunValidationError("EVIDENCE_INDEX has missing or unexpected top-level fields")
    if index.get("schema_version") != SCHEMA_VERSION:
        raise RunValidationError("EVIDENCE_INDEX schema_version mismatch")
    if index.get("algorithm") != "sha256":
        raise RunValidationError("EVIDENCE_INDEX algorithm must be sha256")
    timestamp_errors: list[str] = []
    _parse_timestamp(index.get("generated_at"), "EVIDENCE_INDEX.generated_at", timestamp_errors)
    if timestamp_errors:
        raise RunValidationError("; ".join(timestamp_errors))
    root_digest = index.get("evidence_root_sha256")
    if not isinstance(root_digest, str) or not SHA256_RE.fullmatch(root_digest):
        raise RunValidationError("EVIDENCE_INDEX evidence_root_sha256 invalid")
    if index.get("assurance_note") != (
        "Tamper-evident after finalization; not an authenticity signature."
    ):
        raise RunValidationError("EVIDENCE_INDEX assurance_note mismatch")
    if index.get("run_directory") != run_dir.name:
        raise RunValidationError("EVIDENCE_INDEX run_directory mismatch")
    if index.get("excluded_seal_files") != sorted(SEAL_FILES):
        raise RunValidationError("EVIDENCE_INDEX excluded seal set mismatch")
    entries = index.get("files")
    if not isinstance(entries, list):
        raise RunValidationError("EVIDENCE_INDEX files must be a list")
    if index.get("file_count") != len(entries):
        raise RunValidationError("EVIDENCE_INDEX file_count mismatch")
    normalized: list[dict[str, Any]] = []
    seen: set[str] = set()
    for position, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise RunValidationError(f"EVIDENCE_INDEX files[{position}] must be an object")
        if set(entry) != {"path", "sha256", "size"}:
            raise RunValidationError(f"EVIDENCE_INDEX files[{position}] has unexpected fields")
        relative = entry.get("path")
        digest = entry.get("sha256")
        size = entry.get("size")
        if not isinstance(relative, str) or not relative:
            raise RunValidationError(f"EVIDENCE_INDEX files[{position}].path invalid")
        safe = Path(relative)
        if safe.is_absolute() or ".." in safe.parts:
            raise RunValidationError(f"unsafe path in EVIDENCE_INDEX: {relative}")
        if relative in seen:
            raise RunValidationError(f"duplicate path in EVIDENCE_INDEX: {relative}")
        seen.add(relative)
        if not isinstance(digest, str) or not SHA256_RE.fullmatch(digest):
            raise RunValidationError(f"invalid digest in EVIDENCE_INDEX: {relative}")
        if not isinstance(size, int) or size < 0:
            raise RunValidationError(f"invalid size in EVIDENCE_INDEX: {relative}")
        normalized.append({"path": relative, "sha256": digest.lower(), "size": size})
    if [entry["path"] for entry in normalized] != sorted(entry["path"] for entry in normalized):
        raise RunValidationError("EVIDENCE_INDEX file entries are not in canonical order")
    return normalized


def verify(run_dir: Path) -> dict[str, Any]:
    run_dir = _absolute_no_resolve(run_dir)
    if run_dir.is_symlink():
        raise RunValidationError("run directory itself must not be a symlink")
    manifest, errors = validate_run(run_dir)
    if errors:
        raise RunValidationError(
            "semantic validation failed:\n" + "\n".join(f"- {error}" for error in errors)
        )
    try:
        index = json.loads(
            (run_dir / "EVIDENCE_INDEX.json").read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicate_keys,
        )
        decision = json.loads(
            (run_dir / "FINAL_DECISION.json").read_text(encoding="utf-8"),
            object_pairs_hook=_no_duplicate_keys,
        )
        attestation_text = (run_dir / "ACCEPTANCE_ATTESTATION.intoto.json").read_text(
            encoding="utf-8"
        )
        attestation = json.loads(
            attestation_text, object_pairs_hook=_no_duplicate_keys
        )
        sums_text = (run_dir / "SHA256SUMS.txt").read_text(encoding="utf-8")
    except (OSError, json.JSONDecodeError, RunValidationError) as error:
        raise RunValidationError(f"cannot read seal files: {error}") from error

    entries = _validate_seal_index(run_dir, index)
    actual_paths = {
        path.relative_to(run_dir).as_posix() for path in _evidence_files(run_dir)
    }
    expected_paths = {entry["path"] for entry in entries}
    if actual_paths != expected_paths:
        raise RunValidationError(
            "evidence file set changed; "
            f"missing={sorted(expected_paths - actual_paths)}, "
            f"added={sorted(actual_paths - expected_paths)}"
        )

    root_hasher = hashlib.sha256()
    for entry in entries:
        relative = entry["path"]
        path_errors: list[str] = []
        path = _safe_relative_file(run_dir, relative, f"sealed:{relative}", path_errors)
        if path_errors or path is None:
            raise RunValidationError("; ".join(path_errors))
        sha256, size = _sha256_file(path)
        if sha256 != entry["sha256"] or size != entry["size"]:
            raise RunValidationError(f"evidence changed: {relative}")
        root_hasher.update(f"{sha256} {size} {relative}\n".encode("utf-8"))
    root_hash = root_hasher.hexdigest()
    if root_hash != index.get("evidence_root_sha256"):
        raise RunValidationError("evidence root hash mismatch")
    if sums_text != _canonical_sums(index):
        raise RunValidationError("SHA256SUMS.txt does not match EVIDENCE_INDEX.json")

    if not isinstance(attestation, dict):
        raise RunValidationError("ACCEPTANCE_ATTESTATION.intoto.json root must be an object")
    expected_attestation = _expected_attestation(run_dir, manifest)
    if attestation != expected_attestation:
        raise RunValidationError(
            "ACCEPTANCE_ATTESTATION does not match manifest/results/taskpack configuration"
        )
    attestation_sha256 = hashlib.sha256(attestation_text.encode("utf-8")).hexdigest()

    if not isinstance(decision, dict):
        raise RunValidationError("FINAL_DECISION.json root must be an object")
    expected_decision = _expected_decision(manifest, index, attestation_sha256)
    if decision != expected_decision:
        differing = sorted(
            key
            for key in set(decision) | set(expected_decision)
            if decision.get(key) != expected_decision.get(key)
        )
        raise RunValidationError(
            "FINAL_DECISION does not match manifest/index; differing fields=" + str(differing)
        )
    return decision


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--verify", action="store_true", help="verify an existing seal")
    parser.add_argument("--json", action="store_true", help="emit machine-readable output")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = verify(args.run_dir) if args.verify else finalize(args.run_dir)
    except (RunValidationError, OSError) as error:
        payload = {"ok": False, "mode": "verify" if args.verify else "finalize", "error": str(error)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"INVALID: {error}", file=sys.stderr)
        return 2
    payload = {"ok": True, "mode": "verify" if args.verify else "finalize", "decision": result}
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(
            f"VALID: {result['verdict']} / ACTION {result['action']} / "
            f"evidence_root={result['evidence_root_sha256']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
