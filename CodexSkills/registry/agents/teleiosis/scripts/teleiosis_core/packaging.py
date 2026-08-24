from __future__ import annotations

import os
import shutil
import stat
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .common import TeleiosisError, atomic_write_text, iter_tree_files, sha256_file

FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MAX_ZIP_FILES = 100000
MAX_ZIP_UNCOMPRESSED = 4 * 1024 * 1024 * 1024


def generate_manifest(root: Path) -> Dict[str, Any]:
    lines: List[str] = []
    count = 0
    total = 0
    for rel, path in iter_tree_files(root, include_manifest=False):
        size = path.stat().st_size
        lines.append("%s  %d  %s" % (sha256_file(path), size, rel.as_posix()))
        count += 1
        total += size
    atomic_write_text(root / "MANIFEST.sha256", "\n".join(lines), mode=0o644)
    return {"files": count, "bytes": total, "manifest": str(root / "MANIFEST.sha256")}


def build_deterministic_zip(root: Path, output: Path, root_name: str = "teleiosis") -> Dict[str, Any]:
    if root.name != root_name:
        raise TeleiosisError("ZIP_ROOT_NAME", "封包根目录必须命名为 teleiosis。", {"actual": root.name})
    if output.exists() and output.is_symlink():
        raise TeleiosisError("ZIP_OUTPUT_SYMLINK", "ZIP 输出不能是符号链接。")
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(str(tmp), "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9, allowZip64=True) as archive:
        # Explicit root directory entry.
        root_info = zipfile.ZipInfo(root_name + "/", FIXED_ZIP_TIME)
        root_info.create_system = 3
        root_info.external_attr = (stat.S_IFDIR | 0o755) << 16
        root_info.compress_type = zipfile.ZIP_STORED
        archive.writestr(root_info, b"")
        directories: Set[str] = set()
        files = list(iter_tree_files(root, include_manifest=True))
        for rel, _ in files:
            parts = rel.parts[:-1]
            current = root_name
            for part in parts:
                current += "/" + part
                directories.add(current + "/")
        for directory in sorted(directories):
            info = zipfile.ZipInfo(directory, FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (stat.S_IFDIR | 0o755) << 16
            info.compress_type = zipfile.ZIP_STORED
            archive.writestr(info, b"")
        for rel, path in files:
            arcname = root_name + "/" + rel.as_posix()
            info = zipfile.ZipInfo(arcname, FIXED_ZIP_TIME)
            info.create_system = 3
            mode = path.stat().st_mode
            permission = 0o755 if mode & 0o111 else 0o644
            info.external_attr = (stat.S_IFREG | permission) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            info.flag_bits |= 0x800
            archive.writestr(info, path.read_bytes(), compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    os.replace(str(tmp), str(output))
    audit = audit_zip(output, expected_root=root_name)
    audit["sha256"] = sha256_file(output)
    audit["path"] = str(output)
    return audit


def audit_zip(path: Path, expected_root: str = "teleiosis") -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise TeleiosisError("ZIP_MISSING", "ZIP 不存在或不是普通文件。", {"path": str(path)})
    seen: Set[str] = set()
    roots: Set[str] = set()
    total = 0
    file_count = 0
    with zipfile.ZipFile(str(path), "r") as archive:
        if archive.testzip() is not None:
            raise TeleiosisError("ZIP_CRC", "ZIP CRC 校验失败。")
        for info in archive.infolist():
            name = info.filename
            if name in seen:
                raise TeleiosisError("ZIP_DUPLICATE", "ZIP 包含重复条目。", {"entry": name})
            seen.add(name)
            pure = Path(name)
            if pure.is_absolute() or any(part in {"", ".", ".."} for part in pure.parts):
                # Directory entries end with '/', which Path normalizes safely; blank trailing component is ignored.
                if not (name.endswith("/") and not pure.is_absolute() and all(part not in {".", ".."} for part in pure.parts)):
                    raise TeleiosisError("ZIP_PATH_TRAVERSAL", "ZIP 包含不安全路径。", {"entry": name})
            if pure.parts:
                roots.add(pure.parts[0])
            if info.flag_bits & 0x1:
                raise TeleiosisError("ZIP_ENCRYPTED", "ZIP 不得加密。", {"entry": name})
            unix_mode = (info.external_attr >> 16) & 0xFFFF
            file_type = stat.S_IFMT(unix_mode)
            if file_type == stat.S_IFLNK:
                raise TeleiosisError("ZIP_SYMLINK", "ZIP 不得包含符号链接。", {"entry": name})
            if not info.is_dir():
                file_count += 1
                total += info.file_size
                if file_count > MAX_ZIP_FILES or total > MAX_ZIP_UNCOMPRESSED:
                    raise TeleiosisError("ZIP_BOMB_LIMIT", "ZIP 超过安全解压上限。")
                if info.compress_size > 0 and info.file_size / info.compress_size > 10000:
                    raise TeleiosisError("ZIP_RATIO", "ZIP 条目压缩比异常。", {"entry": name})
    if roots != {expected_root}:
        raise TeleiosisError("ZIP_ROOT", "ZIP 必须只有一个 teleiosis 根目录。", {"roots": sorted(roots)})
    return {"status": "PASS", "root": expected_root, "files": file_count, "uncompressed_bytes": total, "zip_bytes": path.stat().st_size}


def safe_extract(path: Path, destination: Path, expected_root: str = "teleiosis") -> Path:
    audit_zip(path, expected_root=expected_root)
    if destination.exists() and any(destination.iterdir()):
        raise TeleiosisError("EXTRACT_DEST_NOT_EMPTY", "解压目标必须不存在或为空。")
    destination.mkdir(parents=True, exist_ok=True)
    root_resolved = destination.resolve()
    with zipfile.ZipFile(str(path), "r") as archive:
        for info in archive.infolist():
            target = (destination / info.filename).resolve()
            try:
                target.relative_to(root_resolved)
            except ValueError:
                raise TeleiosisError("ZIP_PATH_TRAVERSAL", "ZIP 解压目标越界。", {"entry": info.filename})
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info, "r") as source, target.open("wb") as sink:
                shutil.copyfileobj(source, sink)
            unix_mode = (info.external_attr >> 16) & 0o777
            os.chmod(target, unix_mode or 0o644)
    return destination / expected_root
