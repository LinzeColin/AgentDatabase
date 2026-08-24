from __future__ import annotations

import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from .common import (
    PACKAGE_ROOT,
    VERSION,
    TeleiosisError,
    atomic_write_json,
    copy_tree_secure,
    ensure_not_nested,
    ensure_plain_directory,
    is_executable_like,
    iter_tree_files,
    parse_version,
    read_json,
    remove_tree,
    sha256_file,
)
from .integrity import GENESIS_SHA256, load_manifest, verify_manifest, verify_release
from .packaging import generate_manifest

KNOWN_UPGRADE_VERSIONS = {"v0.0.0.1", "v0.0.0.2", "v0.0.0.3", "v0.0.0.4", VERSION}


def default_skills_root(project: bool = False) -> Path:
    if project:
        return Path.cwd() / ".agents" / "skills"
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home).expanduser() / "skills"
    return Path.home() / ".codex" / "skills"


def _target_version(target: Path) -> Optional[str]:
    path = target / "VERSION"
    if not path.is_file() or path.is_symlink():
        return None
    return path.read_text(encoding="utf-8").strip()


def _verify_existing_genesis(target: Path) -> None:
    locked = target / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md"
    if locked.exists():
        if locked.is_symlink() or not locked.is_file() or sha256_file(locked) != GENESIS_SHA256:
            raise TeleiosisError("TARGET_GENESIS_MISMATCH", "目标安装的永久 Genesis 不匹配，拒绝写入。", {"target": str(target)})


def _declared_paths(root: Path) -> Set[str]:
    try:
        return set(load_manifest(root))
    except TeleiosisError:
        return set()


def _source_subset_matches(source: Path, target: Path) -> bool:
    try:
        source_manifest = load_manifest(source)
    except TeleiosisError:
        return False
    for rel, (digest, size) in source_manifest.items():
        path = target / rel
        if not path.is_file() or path.is_symlink() or path.stat().st_size != size or sha256_file(path) != digest:
            return False
    return True


def _plan_existing(source: Path, target: Path) -> Dict[str, Any]:
    version = _target_version(target)
    if version is None:
        raise TeleiosisError("TARGET_VERSION_UNKNOWN", "已有 teleiosis 缺少可识别 VERSION，拒绝覆盖。", {"target": str(target)})
    try:
        version_tuple = parse_version(version)
    except TeleiosisError:
        raise TeleiosisError("TARGET_VERSION_UNSUPPORTED", "已有版本不在安全升级集合。", {"version": version})
    if version_tuple > parse_version(VERSION):
        raise TeleiosisError("HIGHER_VERSION_REFUSED", "目标版本高于 v0.0.0.5，拒绝降级。", {"version": version})
    if version not in KNOWN_UPGRADE_VERSIONS:
        raise TeleiosisError("TARGET_VERSION_UNSUPPORTED", "已有版本不在安全升级集合。", {"version": version})
    _verify_existing_genesis(target)
    if version == VERSION and _source_subset_matches(source, target):
        return {"mode": "idempotent", "from_version": version, "unknown_files": [], "collisions": []}
    managed = _declared_paths(target)
    source_paths = {rel.as_posix() for rel, _ in iter_tree_files(source, include_manifest=True)}
    unknown_files: List[str] = []
    collisions: List[Dict[str, Any]] = []
    for rel, path in iter_tree_files(target, include_manifest=True):
        rel_text = rel.as_posix()
        if rel_text in managed or rel_text == "MANIFEST.sha256":
            continue
        unknown_files.append(rel_text)
        if rel_text in source_paths:
            source_path = source / rel
            if sha256_file(path) == sha256_file(source_path):
                continue
            kind = "conflict" if is_executable_like(rel) else "adapt"
            collisions.append({"path": rel_text, "state": kind, "reason": "unknown executable collision" if kind == "conflict" else "ordinary document collision preserved in external backup"})
    conflicts = [item for item in collisions if item["state"] == "conflict"]
    if conflicts:
        raise TeleiosisError("UNKNOWN_EXECUTABLE_COLLISION", "未知可执行文件与 v5 包冲突，拒绝写入。", {"conflicts": conflicts})
    return {"mode": "upgrade", "from_version": version, "unknown_files": sorted(unknown_files), "collisions": collisions}


def _merge_unknown_files(target: Path, staging: Path, plan: Dict[str, Any]) -> List[str]:
    preserved: List[str] = []
    collision_paths = {item["path"] for item in plan.get("collisions", [])}
    for rel_text in plan.get("unknown_files", []):
        if rel_text in collision_paths or rel_text == "MANIFEST.sha256":
            continue
        rel = Path(rel_text)
        source = target / rel
        destination = staging / rel
        if destination.exists():
            continue
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(str(source), str(destination), follow_symlinks=False)
        preserved.append(rel_text)
    return preserved


def install(
    skills_root: Optional[Path] = None,
    project: bool = False,
    dry_run: bool = False,
    source: Path = PACKAGE_ROOT,
) -> Dict[str, Any]:
    source = ensure_plain_directory(source)
    verify_release(source, strict=True)
    root = (skills_root or default_skills_root(project)).expanduser().absolute()
    target = root / "teleiosis"
    ensure_not_nested(source, target)
    root.mkdir(parents=True, exist_ok=True)
    if root.is_symlink():
        raise TeleiosisError("SKILLS_ROOT_SYMLINK", "Skills 根目录不能是符号链接。")
    if target.exists():
        if target.is_symlink() or not target.is_dir():
            raise TeleiosisError("TARGET_NOT_DIRECTORY", "目标 teleiosis 不是普通目录。")
        plan = _plan_existing(source, target)
    else:
        plan = {"mode": "fresh", "from_version": None, "unknown_files": [], "collisions": []}
    plan.update({"target": str(target), "version": VERSION})
    if plan["mode"] == "idempotent":
        return {"status": "ALREADY_INSTALLED", "plan": plan, "verified": True}
    if dry_run:
        return {"status": "DRY_RUN_READY", "plan": plan, "writes": False}
    staging = root / (".teleiosis-staging-" + uuid.uuid4().hex)
    backup_root = root.parent / ".teleiosis-backups"
    receipt_root = root.parent / ".teleiosis-receipts"
    backup = backup_root / ("teleiosis-" + uuid.uuid4().hex)
    receipt_path = receipt_root / ("install-" + uuid.uuid4().hex + ".json")
    backup_root.mkdir(parents=True, exist_ok=True)
    receipt_root.mkdir(parents=True, exist_ok=True)
    copy_tree_secure(source, staging)
    preserved: List[str] = []
    if target.exists():
        preserved = _merge_unknown_files(target, staging, plan)
    generate_manifest(staging)
    verify_release(staging, strict=True)
    swapped = False
    try:
        if target.exists():
            os.replace(str(target), str(backup))
            swapped = True
        os.replace(str(staging), str(target))
        try:
            verify_release(target, strict=True)
        except Exception:
            remove_tree(target)
            if swapped:
                os.replace(str(backup), str(target))
            raise
        receipt = {
            "schema_version": "teleiosis.install_receipt.v5",
            "status": "INSTALLED",
            "version": VERSION,
            "target": str(target),
            "plan": plan,
            "backup": str(backup) if swapped else None,
            "preserved_unknown_files": preserved,
            "rollback_available": swapped,
        }
        atomic_write_json(receipt_path, receipt)
        return {"status": "INSTALLED", "target": str(target), "version": VERSION, "backup": receipt["backup"], "receipt": str(receipt_path), "preserved_unknown_files": preserved}
    except Exception:
        if staging.exists():
            shutil.rmtree(str(staging), ignore_errors=True)
        raise


def rollback(receipt_path: Path) -> Dict[str, Any]:
    receipt = read_json(receipt_path)
    if receipt.get("schema_version") != "teleiosis.install_receipt.v5" or receipt.get("status") != "INSTALLED":
        raise TeleiosisError("ROLLBACK_RECEIPT_INVALID", "安装收据不支持回滚。")
    target = Path(receipt["target"])
    backup_value = receipt.get("backup")
    if not backup_value:
        raise TeleiosisError("ROLLBACK_NO_BACKUP", "全新安装没有前置版本备份。")
    backup = Path(backup_value)
    if not backup.is_dir() or backup.is_symlink():
        raise TeleiosisError("ROLLBACK_BACKUP_MISSING", "回滚备份不存在。", {"backup": str(backup)})
    failed = target.parent / (".teleiosis-failed-" + uuid.uuid4().hex)
    if target.exists():
        os.replace(str(target), str(failed))
    try:
        os.replace(str(backup), str(target))
    except Exception:
        if failed.exists():
            os.replace(str(failed), str(target))
        raise
    if failed.exists():
        shutil.rmtree(str(failed), ignore_errors=True)
    receipt["status"] = "ROLLED_BACK"
    atomic_write_json(receipt_path, receipt)
    return {"status": "ROLLED_BACK", "target": str(target)}
