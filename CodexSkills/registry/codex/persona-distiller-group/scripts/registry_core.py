#!/usr/bin/env python3
from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import re
import shutil
import stat
import tempfile
import time
import unicodedata
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any, Iterator

REGISTRY_SCHEMA_VERSION = "3.0"
DELIVERY_SCHEMA_VERSION = "1.0"
DELIVERY_CONTRACT = "v0.0.0.5"
BUILDER_VERSION = "v0.0.0.5"
REGISTRY_INDEX_NAME = "team-index.json"
PRIVATE_ORIGINS = {"private", "self"}
SAFE_SLUG = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
PRODUCT_VERSION = re.compile(r"^0\.0\.0\.([1-9][0-9]{0,2})$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
TEXT_SUFFIXES = {
    ".csv",
    ".json",
    ".jsonl",
    ".md",
    ".py",
    ".rst",
    ".sh",
    ".toml",
    ".tsv",
    ".txt",
    ".yaml",
    ".yml",
}
SECRET_PATTERNS = {
    "private-key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
    "aws-access-key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "github-token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "openai-style-key": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "generic-secret-assignment": re.compile(
        r"(?i)\b(?:api[_-]?key|access[_-]?token|secret|password|passwd)\b"
        r"\s*[:=]\s*[\"']?([A-Za-z0-9_./+\-=]{12,})"
    ),
}

CATEGORIES: tuple[dict[str, str], ...] = (
    {"folder": "技术工程师", "identity_family_id": "technical-engineer", "identity_mode": "single"},
    {"folder": "创业经营家", "identity_family_id": "entrepreneur-operator", "identity_mode": "single"},
    {"folder": "投资资本家", "identity_family_id": "investor-capital-allocator", "identity_mode": "single"},
    {"folder": "开发设计家", "identity_family_id": "developer-designer", "identity_mode": "single"},
    {"folder": "思想教育家", "identity_family_id": "thinker-educator", "identity_mode": "single"},
    {"folder": "政治法律家", "identity_family_id": "political-legal", "identity_mode": "single"},
    {"folder": "多重身份", "identity_family_id": "multi-identity", "identity_mode": "multi"},
)
CATEGORY_BY_FOLDER = {item["folder"]: item for item in CATEGORIES}
CATEGORY_BY_IDENTITY = {item["identity_family_id"]: item for item in CATEGORIES}

REQUIRED_DELIVERY_FILES = {
    "README.md",
    "handoff.md",
    "install.py",
    "install.sh",
    "install.ps1",
    "delivery-manifest.json",
    "delivery-checksums.sha256",
    "registration.json",
    "team-card.json",
    "audit/verification.json",
    "audit/provenance.json",
    "audit/source-coverage.json",
    "audit/evaluation-summary.json",
    "audit/review-record.json",
}
TEAM_CARD_ARRAY_FIELDS = (
    "selection_reasons",
    "distillation_traits",
    "user_value",
    "application_scenarios",
    "key_capabilities",
    "hard_boundaries",
)


def default_registry_root() -> Path:
    return Path(__file__).resolve().parents[1]


def registry_index_path(registry_root: Path) -> Path:
    return registry_root / REGISTRY_INDEX_NAME


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=str(path.parent))
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
    finally:
        temp_path.unlink(missing_ok=True)


def canonical_key(name: str, subject_origin: str) -> str:
    normalized = unicodedata.normalize("NFKC", name).casefold()
    normalized = re.sub(r"[\s\-_·•.]+", "", normalized)
    if not normalized:
        raise ValueError("target name becomes empty after normalization")
    return f"{subject_origin}:{normalized}"


def subject_uid(name: str, subject_origin: str) -> str:
    digest = hashlib.sha256(canonical_key(name, subject_origin).encode("utf-8")).hexdigest()
    return f"person-{digest[:16]}"


def product_version_serial(value: str) -> int:
    match = PRODUCT_VERSION.fullmatch(value)
    if not match:
        raise ValueError("product version must be 0.0.0.1 through 0.0.0.999")
    serial = int(match.group(1))
    if serial > 999:
        raise ValueError("product version maximum is 0.0.0.999")
    return serial


def next_product_version(versions: list[dict[str, Any]]) -> str:
    serials = sorted(product_version_serial(str(item.get("product_version", ""))) for item in versions)
    if len(serials) != len(set(serials)):
        raise ValueError("duplicate product version in canonical person registration")
    if serials and serials != list(range(1, serials[-1] + 1)):
        raise ValueError(f"product versions must be contiguous from 0.0.0.1; found {serials}")
    last = serials[-1] if serials else 0
    if last >= 999:
        raise ValueError("product version range exhausted at 0.0.0.999")
    return f"0.0.0.{last + 1}"


@contextlib.contextmanager
def registry_lock(registry_root: Path, timeout: float = 30.0) -> Iterator[None]:
    identity = hashlib.sha256(str(registry_root.resolve()).encode("utf-8")).hexdigest()[:20]
    lock_path = Path(tempfile.gettempdir()) / f"persona-distiller-group-{identity}.lock"
    handle = lock_path.open("a+b")
    started = time.monotonic()
    try:
        try:
            import fcntl  # type: ignore
        except ImportError:
            fcntl = None  # type: ignore
        if fcntl is not None:
            while True:
                try:
                    fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    if time.monotonic() - started > timeout:
                        raise TimeoutError("persona registry lock timeout")
                    time.sleep(0.02)
            try:
                yield
            finally:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            return
        sentinel = lock_path.with_suffix(".exclusive")
        while True:
            try:
                fd = os.open(sentinel, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() - started > timeout:
                    raise TimeoutError(f"persona registry lock timeout; inspect {sentinel}")
                time.sleep(0.02)
        try:
            yield
        finally:
            sentinel.unlink(missing_ok=True)
    finally:
        handle.close()


def _safe_zip_members(archive: zipfile.ZipFile) -> tuple[str, dict[str, zipfile.ZipInfo]]:
    members: dict[str, zipfile.ZipInfo] = {}
    top_levels: set[str] = set()
    for info in archive.infolist():
        name = info.filename
        if name in members:
            raise ValueError(f"duplicate ZIP member: {name}")
        path = PurePosixPath(name)
        if path.is_absolute() or ".." in path.parts or "\\" in name or "\x00" in name:
            raise ValueError(f"unsafe ZIP member: {name}")
        if not path.parts:
            raise ValueError("empty ZIP member name")
        mode = (info.external_attr >> 16) & 0o170000
        if mode == stat.S_IFLNK:
            raise ValueError(f"ZIP symlink is forbidden: {name}")
        top_levels.add(path.parts[0])
        members[name] = info
    if len(top_levels) != 1:
        raise ValueError(f"ZIP must have exactly one top-level directory; found {sorted(top_levels)}")
    return next(iter(top_levels)), members


def _read_json_member(archive: zipfile.ZipFile, name: str) -> dict[str, Any]:
    try:
        value = json.loads(archive.read(name).decode("utf-8"))
    except (KeyError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"invalid JSON member {name}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON member must be an object: {name}")
    return value


def _checksum_records(
    archive: zipfile.ZipFile,
    top_level: str,
    members: dict[str, zipfile.ZipInfo],
    checksum_relative: str,
) -> dict[str, str]:
    checksum_member = f"{top_level}/{checksum_relative}"
    try:
        lines = archive.read(checksum_member).decode("utf-8").splitlines()
    except (KeyError, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid checksum member {checksum_relative}: {exc}") from exc
    records: dict[str, str] = {}
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        checksum, separator, relative = line.partition("  ")
        if not separator or not HEX_SHA256.fullmatch(checksum):
            raise ValueError(f"invalid checksum line {line_number}")
        relative_path = PurePosixPath(relative)
        if relative_path.is_absolute() or ".." in relative_path.parts or relative in records:
            raise ValueError(f"unsafe or duplicate checksum path: {relative}")
        member_name = f"{top_level}/{relative}"
        if member_name not in members or members[member_name].is_dir():
            raise ValueError(f"checksum references missing member: {relative}")
        if sha256_bytes(archive.read(member_name)) != checksum:
            raise ValueError(f"checksum mismatch: {relative}")
        records[relative] = checksum
    if not records:
        raise ValueError("checksum file contains no payload files")
    return records


def _scan_zip_secrets(
    archive: zipfile.ZipFile,
    top_level: str,
    members: dict[str, zipfile.ZipInfo],
) -> None:
    findings: list[str] = []
    for name, info in members.items():
        if info.is_dir() or info.file_size > 5 * 1024 * 1024:
            continue
        relative = PurePosixPath(name).relative_to(top_level)
        if relative.suffix.casefold() not in TEXT_SUFFIXES:
            continue
        try:
            text = archive.read(name).decode("utf-8")
        except UnicodeDecodeError:
            continue
        for pattern_name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                findings.append(f"{relative.as_posix()}:{pattern_name}")
    if findings:
        raise ValueError("secret-like content detected: " + ", ".join(findings[:10]))


def category_for_identity(selection: dict[str, Any]) -> dict[str, str]:
    mode = selection.get("mode")
    if mode == "multi":
        return CATEGORY_BY_IDENTITY["multi-identity"]
    if mode != "single":
        raise ValueError(f"unsupported identity mode: {mode!r}")
    primary = str(selection.get("primary"))
    category = CATEGORY_BY_IDENTITY.get(primary)
    if not category or category["identity_mode"] != "single":
        raise ValueError(f"unsupported primary identity: {primary!r}")
    return category


def _validate_team_card(
    team_card: dict[str, Any],
    *,
    name: str,
    slug: str,
    uid: str,
    identity_family_id: str,
    product_version: str,
) -> None:
    expected = {
        "schema_version": "1.0",
        "subject_uid": uid,
        "canonical_name": name,
        "subject_slug": slug,
        "identity_family_id": identity_family_id,
        "latest_product_version": product_version,
    }
    for key, value in expected.items():
        if team_card.get(key) != value:
            raise ValueError(f"team-card {key} mismatch")
    if team_card.get("readiness") not in {"ready", "provisional", "unavailable"}:
        raise ValueError("team-card readiness must be ready, provisional, or unavailable")
    if not isinstance(team_card.get("research_cutoff"), str) or not team_card["research_cutoff"].strip():
        raise ValueError("team-card research_cutoff is required")
    for field in TEAM_CARD_ARRAY_FIELDS:
        value = team_card.get(field)
        if (
            not isinstance(value, list)
            or not value
            or any(not isinstance(item, str) or not item.strip() for item in value)
            or len(value) != len(set(value))
        ):
            raise ValueError(f"team-card {field} must be a non-empty unique string array")


def inspect_runtime_bytes(data: bytes) -> dict[str, Any]:
    runtime_sha = sha256_bytes(data)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        top_level, members = _safe_zip_members(archive)
        required = {
            f"{top_level}/SKILL.md",
            f"{top_level}/meta.json",
            f"{top_level}/PACKAGE_MANIFEST.json",
            f"{top_level}/checksums.sha256",
        }
        missing = sorted(required - set(members))
        if missing:
            raise ValueError(f"runtime package missing required members: {missing}")
        forbidden_fragments = ("/raw/", "/references/holdout/", "/references/sources/")
        forbidden = sorted(
            name for name in members if any(fragment in f"/{name}" for fragment in forbidden_fragments)
        )
        if forbidden:
            raise ValueError(f"runtime contains private build material: {forbidden[:10]}")
        checksums = _checksum_records(archive, top_level, members, "checksums.sha256")
        manifest = _read_json_member(archive, f"{top_level}/PACKAGE_MANIFEST.json")
        meta = _read_json_member(archive, f"{top_level}/meta.json")
        manifest_files = manifest.get("files")
        if not isinstance(manifest_files, list):
            raise ValueError("runtime manifest files must be an array")
        manifest_records: dict[str, str] = {}
        for item in manifest_files:
            if not isinstance(item, dict):
                raise ValueError("runtime manifest file entries must be objects")
            path = item.get("path")
            checksum = item.get("sha256")
            if not isinstance(path, str) or not isinstance(checksum, str) or path in manifest_records:
                raise ValueError("runtime manifest contains invalid or duplicate file entry")
            manifest_records[path] = checksum
        if manifest_records != checksums:
            raise ValueError("runtime manifest and checksums disagree")
        privacy = manifest.get("privacy")
        expected_privacy = {
            "raw_included": False,
            "holdout_included": False,
            "private_source_bodies_included": False,
            "runtime_history_reset": True,
        }
        if not isinstance(privacy, dict) or any(privacy.get(k) != v for k, v in expected_privacy.items()):
            raise ValueError("runtime privacy contract is missing or unsafe")
        if manifest.get("builder") != "persona-distiller":
            raise ValueError("runtime builder must be persona-distiller")
        if manifest.get("top_level_count") != 1:
            raise ValueError("runtime manifest must declare one top-level directory")
        name = meta.get("name")
        slug = meta.get("slug")
        origin = meta.get("subject_origin")
        product_version = manifest.get("product_version")
        model_version = manifest.get("model_version")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("runtime target name is required")
        if not isinstance(slug, str) or not SAFE_SLUG.fullmatch(slug) or slug != top_level:
            raise ValueError("runtime slug must match its top-level directory")
        if not isinstance(origin, str) or not origin:
            raise ValueError("runtime subject_origin is required")
        if origin in PRIVATE_ORIGINS:
            raise ValueError("private/self products cannot be published in this public registry")
        if not isinstance(product_version, str):
            raise ValueError("runtime product_version is required")
        product_version_serial(product_version)
        if meta.get("product_version") != product_version:
            raise ValueError("runtime meta and manifest product versions disagree")
        if not isinstance(model_version, str) or not SAFE_COMPONENT.fullmatch(model_version):
            raise ValueError("invalid runtime model_version")
        if meta.get("model_version") != model_version:
            raise ValueError("runtime meta and manifest model versions disagree")
        if meta.get("runtime_invocation_versioning") is not False:
            raise ValueError("runtime must disable per-invocation versioning")
        selection = meta.get("identity_selection")
        if not isinstance(selection, dict):
            raise ValueError("runtime identity_selection must be an object")
        category = category_for_identity(selection)
        _scan_zip_secrets(archive, top_level, members)
    return {
        "sha256": runtime_sha,
        "size_bytes": len(data),
        "top_level": top_level,
        "canonical_name": name.strip(),
        "canonical_key": canonical_key(name, origin),
        "subject_uid": subject_uid(name, origin),
        "subject_slug": slug,
        "subject_origin": origin,
        "identity_family_id": category["identity_family_id"],
        "identity_mode": category["identity_mode"],
        "category": category["folder"],
        "product_version": product_version,
        "model_version": model_version,
        "builder_version": str(manifest.get("builder_version")),
        "artifact_created_at": str(manifest.get("created_at") or meta.get("updated_at") or ""),
        "research_cutoff": str(meta.get("research_cutoff") or "unknown"),
    }


def inspect_runtime_zip(zip_path: Path) -> dict[str, Any]:
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file() or zip_path.suffix.casefold() != ".zip":
        raise ValueError(f"runtime product must be a ZIP file: {zip_path}")
    result = inspect_runtime_bytes(zip_path.read_bytes())
    result["zip_path"] = zip_path
    return result


def inspect_delivery_zip(zip_path: Path) -> dict[str, Any]:
    zip_path = zip_path.expanduser().resolve()
    if not zip_path.is_file() or zip_path.suffix.casefold() != ".zip":
        raise ValueError(f"delivery must be a ZIP file: {zip_path}")
    with zipfile.ZipFile(zip_path) as archive:
        top_level, members = _safe_zip_members(archive)
        relative_files = {
            PurePosixPath(name).relative_to(top_level).as_posix()
            for name, info in members.items()
            if not info.is_dir()
        }
        missing = sorted(REQUIRED_DELIVERY_FILES - relative_files)
        if missing:
            raise ValueError(f"delivery missing required members: {missing}")
        runtime_members = sorted(
            relative
            for relative in relative_files
            if relative.startswith("runtime/") and relative.endswith(".zip")
        )
        if len(runtime_members) != 1:
            raise ValueError(f"delivery must contain exactly one runtime ZIP; found {runtime_members}")
        forbidden_fragments = ("/raw/", "/holdout/", "/private-sources/", "/runtime-history/")
        forbidden = sorted(
            relative
            for relative in relative_files
            if any(fragment in f"/{relative.casefold()}" for fragment in forbidden_fragments)
        )
        if forbidden:
            raise ValueError(f"delivery contains forbidden private/history paths: {forbidden[:10]}")
        checksum_records = _checksum_records(
            archive, top_level, members, "delivery-checksums.sha256"
        )
        expected_checksum_paths = relative_files - {"delivery-checksums.sha256"}
        if set(checksum_records) != expected_checksum_paths:
            missing_checksums = sorted(expected_checksum_paths - set(checksum_records))
            extra_checksums = sorted(set(checksum_records) - expected_checksum_paths)
            raise ValueError(
                f"delivery checksums must cover every file except themselves; "
                f"missing={missing_checksums}, extra={extra_checksums}"
            )
        manifest = _read_json_member(archive, f"{top_level}/delivery-manifest.json")
        if manifest.get("schema_version") != DELIVERY_SCHEMA_VERSION:
            raise ValueError("unsupported delivery manifest schema_version")
        if manifest.get("artifact_kind") != "persona-distillation-full-delivery":
            raise ValueError("unsupported delivery artifact_kind")
        if manifest.get("delivery_contract") != DELIVERY_CONTRACT:
            raise ValueError("delivery contract must be v0.0.0.5")
        if manifest.get("builder") != "persona-distiller":
            raise ValueError("delivery builder must be persona-distiller")
        if manifest.get("builder_version") != BUILDER_VERSION:
            raise ValueError(f"delivery builder_version must be {BUILDER_VERSION}")
        delivery_contract_status = manifest.get("delivery_contract_status")
        if delivery_contract_status not in {
            "native-v0.0.0.5",
            "legacy-normalized-v0.0.0.5",
        }:
            raise ValueError("unsupported delivery_contract_status")
        if manifest.get("single_archive_only") is not True or manifest.get("top_level_count") != 1:
            raise ValueError("delivery must declare a single archive and one top-level directory")
        manifest_files = manifest.get("files")
        if not isinstance(manifest_files, list):
            raise ValueError("delivery manifest files must be an array")
        manifest_records: dict[str, tuple[str, int]] = {}
        for item in manifest_files:
            if not isinstance(item, dict):
                raise ValueError("delivery manifest file entries must be objects")
            path = item.get("path")
            checksum = item.get("sha256")
            size = item.get("size_bytes")
            if (
                not isinstance(path, str)
                or not isinstance(checksum, str)
                or not isinstance(size, int)
                or path in manifest_records
            ):
                raise ValueError("delivery manifest has invalid or duplicate file entry")
            manifest_records[path] = (checksum, size)
        expected_manifest_paths = relative_files - {
            "delivery-manifest.json",
            "delivery-checksums.sha256",
        }
        if set(manifest_records) != expected_manifest_paths:
            raise ValueError("delivery manifest must enumerate every payload file exactly once")
        for relative, (checksum, size) in manifest_records.items():
            member = f"{top_level}/{relative}"
            if checksum_records.get(relative) != checksum or members[member].file_size != size:
                raise ValueError(f"delivery manifest metadata mismatch: {relative}")
        subject = manifest.get("subject")
        identity = manifest.get("identity")
        runtime = manifest.get("runtime")
        if not isinstance(subject, dict) or not isinstance(identity, dict) or not isinstance(runtime, dict):
            raise ValueError("delivery subject, identity, and runtime objects are required")
        name = subject.get("canonical_name")
        slug = subject.get("slug")
        origin = subject.get("origin")
        uid = subject.get("uid")
        product_version = manifest.get("product_version")
        model_version = manifest.get("model_version")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("delivery subject canonical_name is required")
        if not isinstance(slug, str) or not SAFE_SLUG.fullmatch(slug):
            raise ValueError("invalid delivery subject slug")
        if not isinstance(origin, str) or not origin:
            raise ValueError("delivery subject origin is required")
        if origin in PRIVATE_ORIGINS:
            raise ValueError("private/self products cannot be published in this public registry")
        expected_uid = subject_uid(name, origin)
        if uid != expected_uid:
            raise ValueError("delivery subject uid is not deterministic")
        if not isinstance(product_version, str):
            raise ValueError("delivery product_version is required")
        product_version_serial(product_version)
        if not isinstance(model_version, str) or not SAFE_COMPONENT.fullmatch(model_version):
            raise ValueError("invalid delivery model_version")
        expected_top = f"{slug}-persona-distillation-delivery-v{product_version}"
        if top_level != expected_top:
            raise ValueError(f"delivery top-level must be {expected_top!r}")
        category = CATEGORY_BY_FOLDER.get(str(identity.get("folder")))
        if not category:
            raise ValueError("delivery identity folder is not canonical")
        if (
            identity.get("family_id") != category["identity_family_id"]
            or identity.get("mode") != category["identity_mode"]
        ):
            raise ValueError("delivery identity metadata disagrees with folder")
        runtime_path = runtime_members[0]
        if runtime.get("path") != runtime_path:
            raise ValueError("delivery runtime path disagrees with the embedded runtime ZIP")
        expected_runtime_path = f"runtime/{slug}-persona-skill-v{product_version}.zip"
        if runtime_path != expected_runtime_path:
            raise ValueError(f"runtime artifact path must be {expected_runtime_path}")
        runtime_data = archive.read(f"{top_level}/{runtime_path}")
        runtime_info = inspect_runtime_bytes(runtime_data)
        if runtime.get("sha256") != runtime_info["sha256"] or runtime.get("size_bytes") != len(runtime_data):
            raise ValueError("delivery runtime hash or size mismatch")
        comparisons = {
            "canonical_name": name,
            "subject_uid": uid,
            "subject_slug": slug,
            "subject_origin": origin,
            "category": identity.get("folder"),
            "identity_family_id": identity.get("family_id"),
            "identity_mode": identity.get("mode"),
            "product_version": product_version,
            "model_version": model_version,
        }
        for key, expected in comparisons.items():
            if runtime_info.get(key) != expected:
                raise ValueError(f"embedded runtime {key} mismatch")
        if runtime.get("builder_version") != runtime_info["builder_version"]:
            raise ValueError("delivery runtime builder_version mismatch")
        if (
            delivery_contract_status == "native-v0.0.0.5"
            and runtime_info["builder_version"] != BUILDER_VERSION
        ):
            raise ValueError("native v0.0.0.5 delivery must contain a v0.0.0.5 runtime")
        team_card = _read_json_member(archive, f"{top_level}/team-card.json")
        _validate_team_card(
            team_card,
            name=name,
            slug=slug,
            uid=uid,
            identity_family_id=category["identity_family_id"],
            product_version=product_version,
        )
        portable_registration = _read_json_member(archive, f"{top_level}/registration.json")
        portable_expected = {
            "schema_version": "1.0",
            "subject_uid": uid,
            "canonical_name": name,
            "subject_slug": slug,
            "subject_origin": origin,
            "registration_category": category["folder"],
            "identity_family_id": category["identity_family_id"],
            "identity_mode": category["identity_mode"],
            "product_version": product_version,
            "runtime_sha256": runtime_info["sha256"],
            "outer_sha256_trust_anchor": "canonical-registry",
        }
        for key, expected in portable_expected.items():
            if portable_registration.get(key) != expected:
                raise ValueError(f"portable registration {key} mismatch")
        audit_statuses: dict[str, str] = {}
        for relative in (
            "audit/verification.json",
            "audit/provenance.json",
            "audit/source-coverage.json",
            "audit/evaluation-summary.json",
            "audit/review-record.json",
        ):
            audit = _read_json_member(archive, f"{top_level}/{relative}")
            if not isinstance(audit.get("status"), str) or not audit["status"].strip():
                raise ValueError(f"{relative} must declare a non-empty status")
            audit_statuses[relative] = audit["status"]
        if delivery_contract_status == "native-v0.0.0.5":
            nonpassing = {
                relative: status
                for relative, status in audit_statuses.items()
                if not status.startswith("passed")
            }
            if nonpassing:
                raise ValueError(
                    f"native delivery requires passing audit statuses; found {nonpassing}"
                )
        _scan_zip_secrets(archive, top_level, members)
    return {
        "zip_path": zip_path,
        "outer_sha256": sha256_file(zip_path),
        "size_bytes": zip_path.stat().st_size,
        "top_level": top_level,
        "canonical_name": name.strip(),
        "canonical_key": canonical_key(name, origin),
        "subject_uid": uid,
        "subject_slug": slug,
        "subject_origin": origin,
        "identity_family_id": category["identity_family_id"],
        "identity_mode": category["identity_mode"],
        "category": category["folder"],
        "product_version": product_version,
        "model_version": model_version,
        "builder_version": str(manifest.get("builder_version")),
        "artifact_created_at": str(manifest.get("created_at") or ""),
        "delivery_contract_status": str(delivery_contract_status),
        "runtime_artifact": runtime_path,
        "runtime_sha256": runtime_info["sha256"],
        "runtime_size_bytes": runtime_info["size_bytes"],
        "runtime_builder_version": runtime_info["builder_version"],
        "team_card": team_card,
    }


def inspect_target_zip(zip_path: Path) -> dict[str, Any]:
    """Compatibility alias: registration targets are full delivery ZIPs in v0.0.0.5."""
    return inspect_delivery_zip(zip_path)


def load_records(registry_root: Path) -> list[tuple[Path, dict[str, Any]]]:
    records: list[tuple[Path, dict[str, Any]]] = []
    if not registry_root.is_dir():
        return records
    for category in CATEGORIES:
        for path in sorted((registry_root / category["folder"]).glob("*/registration.json")):
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError(f"invalid registration JSON {path}: {exc}") from exc
            if not isinstance(value, dict):
                raise ValueError(f"registration must be a JSON object: {path}")
            records.append((path, value))
    return records


def next_product_version_for(
    name: str,
    subject_origin: str,
    registry_root: Path | None = None,
) -> str:
    registry_root = (registry_root or default_registry_root()).expanduser().resolve()
    key = canonical_key(name, subject_origin)
    uid = subject_uid(name, subject_origin)
    matches = [
        record
        for _, record in load_records(registry_root)
        if record.get("canonical_key") == key or record.get("subject_uid") == uid
    ]
    if len(matches) > 1:
        raise ValueError("canonical person is duplicated across registry folders")
    versions = list(matches[0].get("versions") or []) if matches else []
    return next_product_version(versions)


def build_index(
    registry_root: Path,
    records: list[tuple[Path, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    records = load_records(registry_root) if records is None else records
    products: list[dict[str, Any]] = []
    counts = {item["folder"]: 0 for item in CATEGORIES}
    for path, record in records:
        versions = record.get("versions") or []
        if not versions:
            continue
        latest = max(
            versions,
            key=lambda item: product_version_serial(str(item.get("product_version", ""))),
        )
        category = str(record.get("registration_category"))
        if category in counts:
            counts[category] += 1
        team_card_path = path.parent / "team-card.json"
        try:
            team_card = json.loads(team_card_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            team_card = {}
        products.append(
            {
                "subject_uid": record.get("subject_uid"),
                "canonical_name": record.get("canonical_name"),
                "subject_slug": record.get("subject_slug"),
                "subject_origin": record.get("subject_origin"),
                "registration_category": category,
                "identity_family_id": record.get("identity_family_id"),
                "registration": path.relative_to(registry_root).as_posix(),
                "team_card": team_card_path.relative_to(registry_root).as_posix(),
                "latest_product_version": latest.get("product_version"),
                "latest_model_snapshot": latest.get("model_version"),
                "latest_artifact": (
                    f"{path.parent.relative_to(registry_root).as_posix()}/{latest.get('artifact')}"
                ),
                "latest_outer_sha256": latest.get("outer_sha256"),
                "latest_runtime_sha256": latest.get("runtime_sha256"),
                "version_count": len(versions),
                "readiness": team_card.get("readiness"),
                "research_cutoff": team_card.get("research_cutoff"),
                "selection_reasons": team_card.get("selection_reasons", []),
                "distillation_traits": team_card.get("distillation_traits", []),
                "user_value": team_card.get("user_value", []),
                "application_scenarios": team_card.get("application_scenarios", []),
                "key_capabilities": team_card.get("key_capabilities", []),
                "hard_boundaries": team_card.get("hard_boundaries", []),
            }
        )
    products.sort(
        key=lambda item: (
            str(item["registration_category"]),
            str(item["canonical_name"]).casefold(),
            str(item["subject_uid"]),
        )
    )
    return {
        "schema_version": REGISTRY_SCHEMA_VERSION,
        "generated": True,
        "uniqueness_scope": "all-seven-categories",
        "category_counts": counts,
        "products": products,
    }


def write_index(
    registry_root: Path,
    records: list[tuple[Path, dict[str, Any]]] | None = None,
) -> dict[str, Any]:
    index = build_index(registry_root, records)
    atomic_write_json(registry_index_path(registry_root), index)
    return index


def _register_inspected_product(
    product: dict[str, Any],
    registry_root: Path,
) -> dict[str, Any]:
    category = CATEGORY_BY_FOLDER[product["category"]]
    category_root = registry_root / category["folder"]
    if not (category_root / "_category.json").is_file():
        raise ValueError(f"registry category is not initialized: {category_root}")
    records = load_records(registry_root)
    existing: tuple[Path, dict[str, Any]] | None = None
    for path, record in records:
        same_subject = (
            record.get("subject_uid") == product["subject_uid"]
            or record.get("canonical_key") == product["canonical_key"]
        )
        for version in record.get("versions") or []:
            if version.get("outer_sha256") == product["outer_sha256"] and not same_subject:
                raise ValueError(f"delivery hash is already registered to another subject: {path}")
        if same_subject:
            if existing and existing[0] != path:
                raise ValueError(
                    f"subject is duplicated across registry folders: {existing[0]} and {path}"
                )
            existing = (path, record)
    if existing:
        record_path, record = existing
        if record.get("registration_category") != product["category"]:
            raise ValueError(
                f"subject is already registered under {record.get('registration_category')}; "
                "reclassification must move the canonical record instead of copying it"
            )
        if record_path.parent.name != product["subject_slug"]:
            raise ValueError("subject slug differs from canonical registration")
    else:
        record_path = category_root / product["subject_slug"] / "registration.json"
        if record_path.parent.exists():
            existing_names = {path.name for path in record_path.parent.iterdir()}
            if existing_names - {"team-card.json"}:
                raise ValueError(
                    f"subject folder already exists without a matching canonical record: "
                    f"{record_path.parent}"
                )
        record = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "subject_uid": product["subject_uid"],
            "canonical_name": product["canonical_name"],
            "canonical_key": product["canonical_key"],
            "subject_slug": product["subject_slug"],
            "subject_origin": product["subject_origin"],
            "registration_category": product["category"],
            "identity_family_id": product["identity_family_id"],
            "identity_mode": product["identity_mode"],
            "versions": [],
        }
    versions = record.get("versions")
    if not isinstance(versions, list):
        raise ValueError(f"invalid versions array: {record_path}")
    for version in versions:
        if version.get("product_version") != product["product_version"]:
            continue
        if version.get("outer_sha256") != product["outer_sha256"]:
            raise ValueError(
                f"product version {product['product_version']} is already registered "
                "with a different full-delivery hash"
            )
        artifact = record_path.parent / str(version.get("artifact"))
        if artifact.is_file() and sha256_file(artifact) == product["outer_sha256"]:
            index = write_index(registry_root, records)
            return {
                "action": "already-registered",
                "registration": str(record_path),
                "artifact": str(artifact),
                "subject_uid": product["subject_uid"],
                "category": product["category"],
                "index_products": len(index["products"]),
            }
        break
    expected_version = next_product_version(versions)
    if product["product_version"] != expected_version:
        raise ValueError(
            f"next product version for this person is {expected_version}; "
            f"package declares {product['product_version']}"
        )
    artifact_name = (
        f"{product['subject_slug']}-persona-distillation-delivery-v"
        f"{product['product_version']}.zip"
    )
    artifact_relative = Path("versions") / product["product_version"] / artifact_name
    artifact = record_path.parent / artifact_relative
    artifact.parent.mkdir(parents=True, exist_ok=True)
    if artifact.exists() and sha256_file(artifact) != product["outer_sha256"]:
        raise ValueError(f"artifact destination exists with a different hash: {artifact}")
    shutil.copy2(product["zip_path"], artifact)
    version_record = {
        "product_version": product["product_version"],
        "model_version": product["model_version"],
        "artifact": artifact_relative.as_posix(),
        "outer_sha256": product["outer_sha256"],
        "size_bytes": product["size_bytes"],
        "runtime_artifact": product["runtime_artifact"],
        "runtime_sha256": product["runtime_sha256"],
        "runtime_size_bytes": product["runtime_size_bytes"],
        "builder_version": product["builder_version"],
        "artifact_created_at": product["artifact_created_at"],
        "delivery_contract_status": product["delivery_contract_status"],
    }
    replaced = False
    for index, version in enumerate(versions):
        if version.get("product_version") == product["product_version"]:
            versions[index] = version_record
            replaced = True
            break
    if not replaced:
        versions.append(version_record)
    versions.sort(key=lambda item: product_version_serial(str(item.get("product_version", ""))))
    team_card = dict(product["team_card"])
    team_card["latest_product_version"] = product["product_version"]
    atomic_write_json(record_path, record)
    atomic_write_json(record_path.parent / "team-card.json", team_card)
    records = [(path, value) for path, value in records if path != record_path]
    records.append((record_path, record))
    index = write_index(registry_root, records)
    return {
        "action": "registered",
        "registration": str(record_path),
        "artifact": str(artifact),
        "subject_uid": product["subject_uid"],
        "category": product["category"],
        "product_version": product["product_version"],
        "outer_sha256": product["outer_sha256"],
        "runtime_sha256": product["runtime_sha256"],
        "index_products": len(index["products"]),
    }


def register_product(
    zip_path: Path,
    registry_root: Path | None = None,
) -> dict[str, Any]:
    registry_root = (registry_root or default_registry_root()).expanduser().resolve()
    product = inspect_delivery_zip(zip_path)
    with registry_lock(registry_root):
        return _register_inspected_product(product, registry_root)


def validate_registry(registry_root: Path | None = None) -> dict[str, Any]:
    registry_root = (registry_root or default_registry_root()).expanduser().resolve()
    errors: list[str] = []
    expected_folders = set(CATEGORY_BY_FOLDER)
    actual_folders = (
        {path.name for path in registry_root.iterdir() if path.is_dir()}
        if registry_root.is_dir()
        else set()
    )
    missing_folders = expected_folders - actual_folders
    if missing_folders:
        errors.append(f"missing category folders: {sorted(missing_folders)}")
    for category in CATEGORIES:
        path = registry_root / category["folder"] / "_category.json"
        expected = {
            "schema_version": REGISTRY_SCHEMA_VERSION,
            "folder": category["folder"],
            "identity_family_id": category["identity_family_id"],
            "identity_mode": category["identity_mode"],
        }
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
            if value != expected:
                errors.append(f"category manifest mismatch: {path}")
        except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            errors.append(f"invalid category manifest {path}: {exc}")
    try:
        records = load_records(registry_root)
    except ValueError as exc:
        records = []
        errors.append(str(exc))
    seen_uids: dict[str, Path] = {}
    seen_keys: dict[str, Path] = {}
    seen_hashes: dict[str, Path] = {}
    for path, record in records:
        category = path.parents[1].name
        subject_dir = path.parent
        spec = CATEGORY_BY_FOLDER.get(category)
        required = {
            "schema_version",
            "subject_uid",
            "canonical_name",
            "canonical_key",
            "subject_slug",
            "subject_origin",
            "registration_category",
            "identity_family_id",
            "identity_mode",
            "versions",
        }
        missing = sorted(required - set(record))
        if missing:
            errors.append(f"{path}: missing fields {missing}")
            continue
        if record.get("schema_version") != REGISTRY_SCHEMA_VERSION:
            errors.append(f"{path}: unsupported schema_version")
        if not spec or record.get("registration_category") != category:
            errors.append(f"{path}: registration category does not match folder")
        elif (
            record.get("identity_family_id") != spec["identity_family_id"]
            or record.get("identity_mode") != spec["identity_mode"]
        ):
            errors.append(f"{path}: identity metadata does not match category")
        slug = str(record.get("subject_slug", ""))
        if slug != subject_dir.name or not SAFE_SLUG.fullmatch(slug):
            errors.append(f"{path}: subject slug does not match folder")
        if record.get("subject_origin") in PRIVATE_ORIGINS:
            errors.append(f"{path}: private/self products are forbidden in the public registry")
        try:
            expected_key = canonical_key(
                str(record.get("canonical_name", "")),
                str(record.get("subject_origin", "")),
            )
            expected_uid = subject_uid(
                str(record.get("canonical_name", "")),
                str(record.get("subject_origin", "")),
            )
            if record.get("canonical_key") != expected_key or record.get("subject_uid") != expected_uid:
                errors.append(f"{path}: canonical identity fields are not deterministic")
        except ValueError as exc:
            errors.append(f"{path}: {exc}")
        for field, seen in (("subject_uid", seen_uids), ("canonical_key", seen_keys)):
            value = str(record.get(field))
            if value in seen and seen[value] != path:
                errors.append(f"{field} duplicated across {seen[value]} and {path}")
            seen[value] = path
        versions = record.get("versions")
        if not isinstance(versions, list) or not versions:
            errors.append(f"{path}: versions must contain at least one release")
            continue
        team_card_path = subject_dir / "team-card.json"
        try:
            team_card = json.loads(team_card_path.read_text(encoding="utf-8"))
            latest_version = max(
                versions,
                key=lambda item: product_version_serial(str(item.get("product_version", ""))),
            )
            _validate_team_card(
                team_card,
                name=str(record.get("canonical_name")),
                slug=slug,
                uid=str(record.get("subject_uid")),
                identity_family_id=str(record.get("identity_family_id")),
                product_version=str(latest_version.get("product_version")),
            )
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
            errors.append(f"{team_card_path}: invalid team card: {exc}")
        seen_versions: set[str] = set()
        serials: list[int] = []
        for version in versions:
            if not isinstance(version, dict):
                errors.append(f"{path}: version entry must be an object")
                continue
            product_version = str(version.get("product_version", ""))
            try:
                serials.append(product_version_serial(product_version))
            except ValueError as exc:
                errors.append(f"{path}: {exc}")
            if product_version in seen_versions:
                errors.append(f"{path}: duplicate product version {product_version}")
            seen_versions.add(product_version)
            relative = Path(str(version.get("artifact", "")))
            if (
                relative.is_absolute()
                or ".." in relative.parts
                or len(relative.parts) != 3
                or relative.parts[0] != "versions"
                or relative.parts[1] != product_version
            ):
                errors.append(f"{path}: invalid artifact path {relative}")
                continue
            artifact = (subject_dir / relative).resolve()
            try:
                artifact.relative_to(subject_dir.resolve())
            except ValueError:
                errors.append(f"{path}: artifact escapes subject folder")
                continue
            checksum = str(version.get("outer_sha256", ""))
            if not artifact.is_file():
                errors.append(f"{path}: missing artifact {relative}")
                continue
            if not HEX_SHA256.fullmatch(checksum) or sha256_file(artifact) != checksum:
                errors.append(f"{path}: artifact checksum mismatch {relative}")
                continue
            if artifact.stat().st_size != version.get("size_bytes"):
                errors.append(f"{path}: artifact size mismatch {relative}")
            if checksum in seen_hashes and seen_hashes[checksum] != path:
                errors.append(f"artifact hash duplicated across {seen_hashes[checksum]} and {path}")
            seen_hashes[checksum] = path
            try:
                inspected = inspect_delivery_zip(artifact)
                comparisons = {
                    "subject_uid": record.get("subject_uid"),
                    "canonical_name": record.get("canonical_name"),
                    "subject_slug": record.get("subject_slug"),
                    "subject_origin": record.get("subject_origin"),
                    "category": record.get("registration_category"),
                    "identity_family_id": record.get("identity_family_id"),
                    "product_version": product_version,
                    "outer_sha256": checksum,
                    "runtime_sha256": version.get("runtime_sha256"),
                    "runtime_size_bytes": version.get("runtime_size_bytes"),
                    "delivery_contract_status": version.get("delivery_contract_status"),
                }
                for key, expected in comparisons.items():
                    if inspected.get(key) != expected:
                        errors.append(f"{path}: artifact {key} mismatch for {relative}")
            except (OSError, ValueError, zipfile.BadZipFile) as exc:
                errors.append(f"{path}: invalid artifact {relative}: {exc}")
        if serials and sorted(serials) != list(range(1, max(serials) + 1)):
            errors.append(f"{path}: product versions must be contiguous from 0.0.0.1")
    expected_index = build_index(registry_root, records)
    index_path = registry_index_path(registry_root)
    try:
        actual_index = json.loads(index_path.read_text(encoding="utf-8"))
        if actual_index != expected_index:
            errors.append(f"{index_path}: generated index is stale or inconsistent")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"invalid registry index {index_path}: {exc}")
    return {
        "passed": not errors,
        "registry_root": str(registry_root),
        "categories": len(CATEGORIES),
        "products": len(records),
        "artifacts": sum(len(record.get("versions") or []) for _, record in records),
        "errors": errors,
    }
