#!/usr/bin/env python3
"""Read-only lock and ingest a Product-Design-Taskpack into a verifier run.

The source may be a directory or ZIP. The tool never modifies the source. It
rejects links, path traversal, duplicate archive members, ambiguous canonical
files, oversized archives, and partial overwrite. It creates a deterministic
read-only snapshot of every relevant taskpack file, separately locks the seven
canonical semantic roles, computes a normalized full-pack digest and a role-stable contract digest, conservatively
extracts explicit Acceptance/Task IDs, writes a lock record, and updates
RUN_MANIFEST.yaml transactionally.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional


SCHEMA_VERSION = "2.1"
MAX_ARCHIVE_FILES = 10_000
MAX_ARCHIVE_BYTES = 512 * 1024 * 1024
MAX_TEXT_SCAN_BYTES = 8 * 1024 * 1024
REQUIRED_ROLES = (
    "manifest",
    "pursuing_goal",
    "prd",
    "technical_design",
    "roadmap",
    "task_graph",
    "acceptance_contract",
)
ROLE_ALIASES: dict[str, tuple[str, ...]] = {
    "manifest": (
        "MANIFEST.yaml", "MANIFEST.yml", "MANIFEST.json",
        "TASKPACK_MANIFEST.yaml", "TASKPACK_MANIFEST.yml", "TASKPACK_MANIFEST.json",
    ),
    "pursuing_goal": (
        "PURSUE_GOAL.md", "PURSUING_GOAL.md", "PURSUING_GOAL_PROMPT.md", "GOAL.md",
    ),
    "prd": (
        "DECISION_PRD.md", "PRD.md", "PRODUCT_REQUIREMENTS.md", "PRODUCT_DESIGN.md",
    ),
    "technical_design": (
        "TECHNICAL_OPERATIONS_DESIGN.md", "TECHNICAL_DESIGN.md", "SYSTEM_DESIGN.md", "ARCHITECTURE.md",
    ),
    "roadmap": ("ROADMAP.md", "ROADMAP.yaml", "ROADMAP.yml", "ROADMAP.json"),
    "task_graph": (
        "TASK_GRAPH.yaml", "TASK_GRAPH.yml", "TASK_GRAPH.json", "TASK_DAG.yaml", "TASK_DAG.yml", "TASK_DAG.json",
    ),
    "acceptance_contract": (
        "ACCEPTANCE_CONTRACT.yaml", "ACCEPTANCE_CONTRACT.yml", "ACCEPTANCE_CONTRACT.json", "ACCEPTANCE_CONTRACT.md",
    ),
}
IGNORED_PARTS = {".git", "__MACOSX", "__pycache__", ".pytest_cache", "node_modules"}
VERSION_RE = re.compile(
    r"(?im)^\s*(?:pack_version|taskpack_version|version)\s*:\s*[\"']?([^\s#\"']+)"
)
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
ID_VALUE_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:/-]{0,127}$")
WINDOWS_DRIVE_RE = re.compile(r"^[A-Za-z]:/")


class TaskpackError(Exception):
    """Raised when a taskpack cannot be locked without ambiguity."""


def _absolute_no_resolve(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path.expanduser())))


def _sha256_file(path: Path) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _safe_archive_member(name: str) -> Path:
    normalized = name.replace("\\", "/")
    path = Path(normalized)
    if (
        not normalized
        or "\x00" in normalized
        or normalized.startswith("//")
        or WINDOWS_DRIVE_RE.match(normalized)
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise TaskpackError(f"unsafe ZIP member: {name!r}")
    return path


def _validate_source_tree(root: Path) -> None:
    if not root.is_dir() or root.is_symlink():
        raise TaskpackError(f"taskpack root must be a real directory: {root}")
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise TaskpackError(f"symlink forbidden in taskpack: {relative}")
        if not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
            raise TaskpackError(f"non-regular entry forbidden in taskpack: {relative}")


def _extract_zip(source: Path, destination: Path) -> str:
    if source.is_symlink():
        raise TaskpackError("taskpack ZIP source must not be a symlink")
    source_digest, _ = _sha256_file(source)
    count = 0
    total = 0
    seen_exact: set[str] = set()
    seen_casefold: set[str] = set()
    try:
        archive = zipfile.ZipFile(source)
    except (OSError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise TaskpackError(f"cannot open taskpack ZIP: {error}") from error
    with archive:
        members: list[tuple[zipfile.ZipInfo, Path]] = []
        for info in archive.infolist():
            member = _safe_archive_member(info.filename)
            normalized = member.as_posix().rstrip("/")
            if not normalized:
                continue
            folded = normalized.casefold()
            if normalized in seen_exact or folded in seen_casefold:
                raise TaskpackError(f"duplicate/case-colliding ZIP member: {normalized}")
            seen_exact.add(normalized)
            seen_casefold.add(folded)
            if info.flag_bits & 0x1:
                raise TaskpackError(f"encrypted ZIP member is not supported: {normalized}")
            count += 1
            total += int(info.file_size)
            if count > MAX_ARCHIVE_FILES:
                raise TaskpackError("taskpack ZIP exceeds file-count safety limit")
            if total > MAX_ARCHIVE_BYTES:
                raise TaskpackError("taskpack ZIP exceeds uncompressed-size safety limit")
            unix_mode = (info.external_attr >> 16) & 0o170000
            if unix_mode == stat.S_IFLNK:
                raise TaskpackError(f"symlink ZIP member forbidden: {member}")
            target = destination / member
            resolved_parent = target.parent.resolve()
            try:
                resolved_parent.relative_to(destination.resolve())
            except ValueError as error:
                raise TaskpackError(f"ZIP member escapes destination: {member}") from error
            members.append((info, member))
        try:
            for info, member in members:
                target = destination / member
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source_handle, target.open("xb") as target_handle:
                    shutil.copyfileobj(source_handle, target_handle, length=1024 * 1024)
        except (OSError, RuntimeError, zipfile.BadZipFile) as error:
            raise TaskpackError(f"cannot safely extract taskpack ZIP: {error}") from error
    _validate_source_tree(destination)
    return source_digest


def _meaningful_root(root: Path) -> Path:
    current = root
    while True:
        entries = [p for p in current.iterdir() if p.name not in {"__MACOSX", ".DS_Store"}]
        directories = [p for p in entries if p.is_dir()]
        files = [p for p in entries if p.is_file()]
        if not files and len(directories) == 1:
            current = directories[0]
            continue
        return current


def _candidate_files(root: Path) -> list[Path]:
    result: list[Path] = []
    total = 0
    seen_casefold: dict[str, str] = {}
    for path in root.rglob("*"):
        relative = path.relative_to(root)
        if any(part in IGNORED_PARTS for part in relative.parts):
            continue
        relative_text = relative.as_posix()
        if "\x00" in relative_text or "\\" in relative_text:
            raise TaskpackError(f"non-portable taskpack path: {relative_text!r}")
        folded = relative_text.casefold()
        if folded in seen_casefold:
            raise TaskpackError(
                "case-insensitive taskpack path collision: "
                f"{seen_casefold[folded]!r} vs {relative_text!r}"
            )
        seen_casefold[folded] = relative_text
        if path.is_file() and not path.is_symlink():
            result.append(path)
            try:
                total += path.stat().st_size
            except OSError as error:
                raise TaskpackError(f"cannot stat taskpack file {relative}: {error}") from error
            if len(result) > MAX_ARCHIVE_FILES:
                raise TaskpackError("taskpack directory exceeds file-count safety limit")
            if total > MAX_ARCHIVE_BYTES:
                raise TaskpackError("taskpack directory exceeds size safety limit")
    return result

def _discover_roles(root: Path) -> dict[str, Path]:
    files = _candidate_files(root)
    by_upper_name: dict[str, list[Path]] = {}
    for path in files:
        by_upper_name.setdefault(path.name.upper(), []).append(path)

    selected: dict[str, Path] = {}
    for role in REQUIRED_ROLES:
        # Rank all accepted aliases together. A canonical file at the taskpack
        # root must beat a preferred alias hidden deeper in an appendix, while
        # two different accepted names at the same shallowest depth are a real
        # semantic ambiguity and therefore fail closed.
        candidates: list[tuple[int, int, str, Path]] = []
        for alias_rank, alias in enumerate(ROLE_ALIASES[role]):
            for path in by_upper_name.get(alias.upper(), []):
                relative = path.relative_to(root)
                candidates.append(
                    (len(relative.parts), alias_rank, relative.as_posix(), path)
                )
        if not candidates:
            aliases = ", ".join(ROLE_ALIASES[role])
            raise TaskpackError(f"missing canonical taskpack role {role}; accepted names: {aliases}")
        shallowest_depth = min(item[0] for item in candidates)
        shallowest = sorted(
            (item for item in candidates if item[0] == shallowest_depth),
            key=lambda item: (item[1], item[2]),
        )
        distinct_paths = {item[3] for item in shallowest}
        if len(distinct_paths) != 1:
            names = sorted(path.relative_to(root).as_posix() for path in distinct_paths)
            raise TaskpackError(f"ambiguous {role} candidates across accepted aliases: {names}")
        selected[role] = shallowest[0][3]
    if len({path.resolve() for path in selected.values()}) != len(selected):
        raise TaskpackError("one source file cannot satisfy multiple canonical taskpack roles")
    return selected


def _pack_digest(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: item["role"]):
        digest.update(
            f"{record['role']}\0{record['sha256']}\0{record['size']}\n".encode("utf-8")
        )
    return digest.hexdigest()


def _source_tree_digest(records: list[dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for record in sorted(records, key=lambda item: item["source_path"]):
        digest.update(
            f"{record['source_path']}\0{record['sha256']}\0{record['size']}\n".encode(
                "utf-8"
            )
        )
    return digest.hexdigest()


def _copy_stable_source(source_root: Path, destination: Path) -> list[dict[str, Any]]:
    """Create the exact byte snapshot that all later discovery and hashing use."""
    candidates = _candidate_files(source_root)
    if not candidates:
        raise TaskpackError("taskpack does not contain any relevant regular files")
    destination.mkdir()
    records: list[dict[str, Any]] = []
    for source_path in sorted(candidates, key=lambda item: item.relative_to(source_root).as_posix()):
        relative = source_path.relative_to(source_root)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copyfile(source_path, target)
        except OSError as error:
            raise TaskpackError(f"cannot snapshot taskpack file {relative}: {error}") from error
        digest, size = _sha256_file(target)
        records.append(
            {
                "source_path": relative.as_posix(),
                "sha256": digest,
                "size": size,
            }
        )
    _validate_source_tree(destination)
    return records


def _write_snapshot_archive(
    snapshot_root: Path,
    records: list[dict[str, Any]],
    destination: Path,
) -> tuple[str, int]:
    """Write a deterministic ZIP containing the normalized full taskpack snapshot."""
    try:
        with zipfile.ZipFile(
            destination,
            mode="x",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            allowZip64=True,
        ) as archive:
            for record in sorted(records, key=lambda item: item["source_path"]):
                source_path = snapshot_root / Path(record["source_path"])
                info = zipfile.ZipInfo(record["source_path"], date_time=(1980, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                info.flag_bits |= 0x800
                with source_path.open("rb") as source_handle, archive.open(info, "w") as target_handle:
                    shutil.copyfileobj(source_handle, target_handle, length=1024 * 1024)
    except (OSError, RuntimeError, zipfile.BadZipFile, zipfile.LargeZipFile) as error:
        raise TaskpackError(f"cannot create deterministic taskpack snapshot: {error}") from error
    return _sha256_file(destination)


def _declared_version(manifest_path: Path, pack_digest: str) -> str:
    try:
        text = manifest_path.read_text(encoding="utf-8", errors="replace")[:128_000]
    except OSError:
        return f"sha256:{pack_digest[:16]}"
    match = VERSION_RE.search(text)
    return match.group(1).strip() if match else f"sha256:{pack_digest[:16]}"


def _goal_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    for raw in text.splitlines():
        line = raw.strip().lstrip("#>-* ").strip()
        if line and not line.startswith("```"):
            return line[:500]
    return ""


def _clean_id(value: Any) -> str:
    if not isinstance(value, str):
        return ""
    candidate = value.strip().strip("`\"'[](),")
    return candidate if ID_VALUE_RE.fullmatch(candidate) else ""


def _json_ids(value: Any, kind: str, contexts: tuple[str, ...] = ()) -> set[str]:
    result: set[str] = set()
    if isinstance(value, dict):
        for raw_key, child in value.items():
            key = str(raw_key)
            normalized = re.sub(r"[^a-z0-9]", "", key.lower())
            explicit_keys = {"acceptanceid"} if kind == "acceptance" else {"taskid"}
            if normalized in explicit_keys:
                candidate = _clean_id(child)
                if candidate:
                    result.add(candidate)
            context_tokens = tuple(re.sub(r"[^a-z0-9]", "", item.lower()) for item in contexts)
            relevant = (
                any(token in {"acceptance", "acceptances", "acceptancecriteria", "criteria"} for token in context_tokens)
                if kind == "acceptance"
                else any(token in {"task", "tasks", "taskgraph", "taskdag"} for token in context_tokens)
            )
            if normalized == "id" and relevant:
                candidate = _clean_id(child)
                if candidate:
                    result.add(candidate)
            result.update(_json_ids(child, kind, contexts + (key,)))
    elif isinstance(value, list):
        for child in value:
            result.update(_json_ids(child, kind, contexts))
    return result


def _line_ids(text: str, kind: str) -> set[str]:
    result: set[str] = set()
    if kind == "acceptance":
        direct = re.compile(
            r"(?im)^\s*(?:[-*]\s*)?(?:acceptance[ _-]?id|acceptanceid)\s*(?::|\|)\s*[`\"']?([A-Za-z0-9][A-Za-z0-9._:/-]{0,127})"
        )
        section = re.compile(r"^(?:acceptance|acceptances|acceptance[_ -]?criteria|criteria)\s*:\s*$", re.I)
    else:
        direct = re.compile(
            r"(?im)^\s*(?:[-*]\s*)?(?:task[ _-]?id|taskid)\s*(?::|\|)\s*[`\"']?([A-Za-z0-9][A-Za-z0-9._:/-]{0,127})"
        )
        section = re.compile(r"^(?:task|tasks|task[_ -]?graph|task[_ -]?dag)\s*:\s*$", re.I)
    for match in direct.finditer(text):
        candidate = _clean_id(match.group(1))
        if candidate:
            result.add(candidate)

    active_indent: Optional[int] = None
    id_line = re.compile(r"^(?:-\s*)?id\s*:\s*[`\"']?([A-Za-z0-9][A-Za-z0-9._:/-]{0,127})", re.I)
    for raw in text.splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        indent = len(raw) - len(raw.lstrip(" \t"))
        stripped = raw.strip()
        if section.fullmatch(stripped):
            active_indent = indent
            continue
        if active_indent is not None and indent <= active_indent:
            active_indent = None
        if active_indent is not None:
            match = id_line.match(stripped)
            if match:
                candidate = _clean_id(match.group(1))
                if candidate:
                    result.add(candidate)
    return result


def _extract_explicit_ids(path: Path, kind: str) -> tuple[list[str], str]:
    try:
        if path.stat().st_size > MAX_TEXT_SCAN_BYTES:
            return [], "skipped:file-too-large"
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as error:
        return [], f"skipped:read-error:{type(error).__name__}"
    if path.suffix.lower() == ".json":
        try:
            value = json.loads(raw)
        except json.JSONDecodeError:
            return sorted(_line_ids(raw, kind)), "line-scan:invalid-json"
        return sorted(_json_ids(value, kind)), "strict-json-recursive"
    return sorted(_line_ids(raw, kind)), "explicit-label-and-section-scan"


def _load_run_manifest(run_dir: Path) -> tuple[Path, dict[str, Any]]:
    path = run_dir / "RUN_MANIFEST.yaml"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise TaskpackError(f"RUN_MANIFEST.yaml must be strict JSON: {error}") from error
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        raise TaskpackError(f"RUN_MANIFEST must be verifier schema {SCHEMA_VERSION}")
    if not isinstance(value.get("taskpack"), dict):
        raise TaskpackError("RUN_MANIFEST.yaml lacks taskpack object; install aligned verifier v2.1 first")
    return path, value


def _atomic_json(path: Path, value: Any) -> None:
    fd, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary_name, path)
    except Exception:
        try:
            os.unlink(temporary_name)
        except OSError:
            pass
        raise


def ingest(
    source: Path,
    run_dir: Path,
    *,
    authoritative: bool,
    authorization_reference: str,
    declared_version: str = "",
    source_reference: str = "",
    authorized_pack_digest: str = "",
) -> dict[str, Any]:
    source = _absolute_no_resolve(source)
    run_dir = _absolute_no_resolve(run_dir)
    public_source_reference = source_reference.strip() or source.name
    normalized_authorized_digest = authorized_pack_digest.strip().lower()
    if normalized_authorized_digest and not SHA256_RE.fullmatch(normalized_authorized_digest):
        raise TaskpackError("--authorized-pack-digest must be a 64-character SHA-256")
    if not run_dir.is_dir() or run_dir.is_symlink():
        raise TaskpackError(f"run directory must be a real directory: {run_dir}")
    manifest_path, run_manifest = _load_run_manifest(run_dir)
    existing = run_manifest["taskpack"]
    if existing.get("detected") is True:
        raise TaskpackError("run already contains a locked taskpack; create a new run to change it")
    target_dir = run_dir / "taskpack"
    lock_path = run_dir / "raw-results/taskpack-lock.json"
    if target_dir.is_symlink() or lock_path.is_symlink():
        raise TaskpackError("taskpack destination must not be a symlink")
    if (target_dir.exists() and any(target_dir.iterdir())) or lock_path.exists():
        raise TaskpackError("taskpack destination is not empty; refusing partial overwrite")
    if authoritative and not authorization_reference.strip():
        raise TaskpackError("authoritative ingestion requires --authorization-reference")
    if normalized_authorized_digest and not authoritative:
        raise TaskpackError("--authorized-pack-digest requires --authoritative")

    with tempfile.TemporaryDirectory(prefix="verifier-taskpack-") as temporary_name:
        temporary = Path(temporary_name)
        source_kind: str
        source_archive_sha256 = ""
        if source.is_file() and source.suffix.lower() == ".zip":
            extracted = temporary / "extracted"
            extracted.mkdir()
            source_archive_sha256 = _extract_zip(source, extracted)
            initial_source_root = _meaningful_root(extracted)
            source_kind = "zip"
        elif source.is_dir():
            _validate_source_tree(source)
            initial_source_root = source
            source_kind = "directory"
        else:
            raise TaskpackError("taskpack source must be a directory or .zip file")

        # Freeze a stable all-file snapshot first. Role discovery, ID extraction and
        # all digests use only this copy, eliminating later source mutation ambiguity.
        stable_source = temporary / "stable-source"
        source_records = _copy_stable_source(initial_source_root, stable_source)
        selected = _discover_roles(stable_source)

        stage = temporary / "stage"
        stage.mkdir()
        source_snapshot_name = "TASKPACK_SOURCE_SNAPSHOT.zip"
        source_snapshot_path = stage / source_snapshot_name
        source_snapshot_sha256, source_snapshot_size = _write_snapshot_archive(
            stable_source, source_records, source_snapshot_path
        )
        pack_digest = _source_tree_digest(source_records)

        records: list[dict[str, Any]] = []
        for role in REQUIRED_ROLES:
            original = selected[role]
            suffix = "".join(original.suffixes) or ".bin"
            destination_name = f"{role}{suffix.lower()}"
            destination = stage / destination_name
            shutil.copyfile(original, destination)
            digest, size = _sha256_file(destination)
            records.append(
                {
                    "role": role,
                    "source_path": original.relative_to(stable_source).as_posix(),
                    "path": f"taskpack/{destination_name}",
                    "sha256": digest,
                    "size": size,
                }
            )
        contract_digest = _pack_digest(records)
        if normalized_authorized_digest and normalized_authorized_digest != pack_digest:
            raise TaskpackError(
                "computed normalized full-pack digest does not match --authorized-pack-digest; "
                "refusing authorization drift"
            )
        version = declared_version.strip() or _declared_version(selected["manifest"], pack_digest)
        goal = _goal_text(selected["pursuing_goal"])
        acceptance_ids, acceptance_method = _extract_explicit_ids(
            selected["acceptance_contract"], "acceptance"
        )
        task_ids, task_method = _extract_explicit_ids(selected["task_graph"], "task")
        snapshot_evidence_path = f"taskpack/{source_snapshot_name}"
        lock = {
            "schema_version": SCHEMA_VERSION,
            "source_kind": source_kind,
            "source_reference": public_source_reference,
            "source_archive_sha256": source_archive_sha256,
            "source_snapshot_path": snapshot_evidence_path,
            "source_snapshot_sha256": source_snapshot_sha256,
            "source_snapshot_size": source_snapshot_size,
            "source_file_count": len(source_records),
            "source_files": source_records,
            "pack_digest_sha256": pack_digest,
            "contract_digest_sha256": contract_digest,
            "declared_version": version,
            "authoritative": authoritative,
            "authorization_reference": authorization_reference.strip(),
            "authorized_pack_digest_sha256": (
                normalized_authorized_digest or (pack_digest if authoritative else "")
            ),
            "files": records,
            "acceptance_ids": acceptance_ids,
            "task_ids": task_ids,
            "id_extraction": {
                "acceptance_method": acceptance_method,
                "task_method": task_method,
                "assurance": (
                    "Conservative explicit-ID extraction only. Verifier must compare the inventory with the "
                    "locked Acceptance Contract and Task Graph before setting compatibility_status=PASS."
                ),
            },
            "assurance_note": (
                "Normalized full taskpack file inventory and deterministic source snapshot are byte-locked; "
                "the seven semantic roles have a separate contract digest. Semantic compatibility, ID "
                "completeness, acceptance coverage, and authorization remain independent verifier gates."
            ),
        }

        target_dir.mkdir(exist_ok=True)
        published: list[Path] = []
        try:
            for staged in sorted(stage.iterdir()):
                target = target_dir / staged.name
                if target.exists() or target.is_symlink():
                    raise TaskpackError(f"taskpack destination appeared during ingest: {target.name}")
                os.replace(staged, target)
                published.append(target)
            lock_path.parent.mkdir(exist_ok=True)
            _atomic_json(lock_path, lock)
            published.append(lock_path)

            taskpack_value = {
                "mode": "product-design-taskpack",
                "detected": True,
                "authoritative": authoritative,
                "authorization_reference": authorization_reference.strip(),
                "source_kind": source_kind,
                "source_reference": public_source_reference,
                "source_archive_sha256": source_archive_sha256,
                "source_snapshot_path": snapshot_evidence_path,
                "source_snapshot_sha256": source_snapshot_sha256,
                "source_snapshot_size": source_snapshot_size,
                "source_file_count": len(source_records),
                "declared_version": version,
                "pack_digest_sha256": pack_digest,
                "contract_digest_sha256": contract_digest,
                "authorized_pack_digest_sha256": (
                    normalized_authorized_digest or (pack_digest if authoritative else "")
                ),
                "pursuing_goal": goal,
                "files": records,
                "acceptance_ids": acceptance_ids,
                "task_ids": task_ids,
                "integrity_status": "PASS",
                "compatibility_status": "NOT_RUN",
                "compatibility_reason": "semantic compatibility and extracted-ID completeness have not yet been reviewed",
                "drift_status": "NOT_RUN",
                "drift_items": [],
                "authorization_evidence_paths": [],
                "integrity_evidence_paths": [
                    "raw-results/taskpack-lock.json",
                    snapshot_evidence_path,
                ],
                "compatibility_evidence_paths": [],
                "drift_evidence_paths": [],
                "evidence_paths": [
                    "raw-results/taskpack-lock.json",
                    snapshot_evidence_path,
                ],
                "reason_if_absent": "",
            }
            run_manifest["taskpack"] = taskpack_value
            _atomic_json(manifest_path, run_manifest)
        except Exception:
            for path in reversed(published):
                try:
                    path.unlink()
                except OSError:
                    pass
            try:
                target_dir.rmdir()
            except OSError:
                pass
            raise

    next_actions = [
        "verify extracted Acceptance/Task ID inventories against the locked source snapshot",
        "set taskpack.compatibility_status and attach compatibility evidence",
        "complete TRACEABILITY_MATRIX.json and change-impact mapping",
        "set taskpack.drift_status and attach implementation-versus-contract drift evidence",
    ]
    if not acceptance_ids:
        next_actions.insert(0, "extract all authoritative Acceptance IDs; none were found conservatively")
    if not task_ids:
        next_actions.insert(0, "extract all Task DAG IDs; none were found conservatively")
    return {
        "ok": True,
        "run_dir": str(run_dir),
        "pack_digest_sha256": pack_digest,
        "contract_digest_sha256": contract_digest,
        "source_snapshot_sha256": source_snapshot_sha256,
        "source_file_count": len(source_records),
        "declared_version": version,
        "authoritative": authoritative,
        "acceptance_ids": acceptance_ids,
        "task_ids": task_ids,
        "roles": {record["role"]: record["path"] for record in records},
        "next_required_actions": next_actions,
    }

def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--authoritative", action="store_true")
    parser.add_argument("--authorization-reference", default="")
    parser.add_argument("--authorized-pack-digest", default="")
    parser.add_argument("--declared-version", default="")
    parser.add_argument(
        "--source-reference",
        default="",
        help="non-sensitive label stored in evidence; defaults to the source basename",
    )
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = ingest(
            args.source,
            args.run_dir,
            authoritative=args.authoritative,
            authorization_reference=args.authorization_reference,
            declared_version=args.declared_version,
            source_reference=args.source_reference,
            authorized_pack_digest=args.authorized_pack_digest,
        )
    except (TaskpackError, OSError) as error:
        payload = {"ok": False, "error": str(error)}
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"ERROR: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
