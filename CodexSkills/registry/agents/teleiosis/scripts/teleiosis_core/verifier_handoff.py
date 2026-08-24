from __future__ import annotations

import hashlib
import json
import os
import stat
import zipfile
from pathlib import Path
from typing import Any, Dict, List

from .common import PACKAGE_ROOT, TeleiosisError, canonical_json_hash, read_json, sha256_file, tree_digest
from .packaging import FIXED_ZIP_TIME

HANDOFF_FILES = [
    "VERSION", "ACCEPTANCE_CONTRACT.json", "TRACEABILITY_MATRIX.json", "CANONICAL_STATE.json",
    "metadata/release.json", "metadata/evidence-boundaries.json", "metadata/project-input.json",
    "evidence/validation/final-validation-summary.json", "evidence/validation/test-runs.json",
]


def subject_identity(root: Path = PACKAGE_ROOT) -> Dict[str, Any]:
    release = read_json(root / "metadata/release.json")
    acceptance_hash = sha256_file(root / "ACCEPTANCE_CONTRACT.json")
    manifest_hash = sha256_file(root / "MANIFEST.sha256") if (root / "MANIFEST.sha256").is_file() else None
    payload = {
        "schema_version": "teleiosis.verifier_subject_identity.v5",
        "name": release["name"],
        "version": release["version"],
        "candidate_tree_digest": tree_digest(root, include_manifest=False),
        "acceptance_sha256": acceptance_hash,
        "manifest_sha256": manifest_hash,
        "formal_pass": "NOT_ISSUED",
    }
    payload["subject_hash"] = canonical_json_hash(payload)
    return payload


def build_handoff(output: Path, root: Path = PACKAGE_ROOT) -> Dict[str, Any]:
    root = root.resolve()
    output = output.expanduser().absolute()
    try:
        output.relative_to(root)
        raise TeleiosisError("HANDOFF_INSIDE_PACKAGE", "Verifier handoff 输出必须位于包外。")
    except ValueError:
        pass
    if output.exists() and output.is_symlink():
        raise TeleiosisError("HANDOFF_SYMLINK", "Verifier handoff 输出不能是符号链接。")
    identity = subject_identity(root)
    entries: List[tuple[str, bytes]] = [("SUBJECT_IDENTITY.json", json.dumps(identity, ensure_ascii=False, sort_keys=True, indent=2).encode("utf-8") + b"\n")]
    for rel in HANDOFF_FILES:
        path = root / rel
        if not path.is_file() or path.is_symlink():
            raise TeleiosisError("HANDOFF_FILE_MISSING", "Verifier handoff 缺少冻结文件。", {"path": rel})
        entries.append((rel, path.read_bytes()))
    manifest_lines = []
    for name, data in entries:
        manifest_lines.append(f"{hashlib.sha256(data).hexdigest()}  {len(data)}  {name}")
    entries.append(("HANDOFF_MANIFEST.sha256", ("\n".join(manifest_lines) + "\n").encode("utf-8")))
    output.parent.mkdir(parents=True, exist_ok=True)
    tmp = output.with_name(output.name + ".tmp")
    if tmp.exists():
        tmp.unlink()
    with zipfile.ZipFile(tmp, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, data in sorted(entries):
            info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
            info.create_system = 3
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            info.flag_bits |= 0x800
            archive.writestr(info, data, compress_type=zipfile.ZIP_DEFLATED, compresslevel=9)
    os.replace(tmp, output)
    return {
        "schema_version": "teleiosis.verifier_handoff_result.v5",
        "status": "READY_FOR_EXTERNAL_VERIFIER",
        "subject_hash": identity["subject_hash"],
        "path": str(output),
        "sha256": sha256_file(output),
        "formal_pass": "NOT_ISSUED",
    }


def validate_handoff(path: Path) -> Dict[str, Any]:
    if not path.is_file() or path.is_symlink():
        raise TeleiosisError("HANDOFF_MISSING", "Verifier handoff ZIP 不存在或不安全。")
    with zipfile.ZipFile(path, "r") as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or "SUBJECT_IDENTITY.json" not in names or "HANDOFF_MANIFEST.sha256" not in names:
            raise TeleiosisError("HANDOFF_CONTENT", "Verifier handoff 内容不完整或重复。")
        identity = json.loads(archive.read("SUBJECT_IDENTITY.json").decode("utf-8"))
        if identity.get("formal_pass") != "NOT_ISSUED":
            raise TeleiosisError("HANDOFF_FORMAL_PASS", "内部 handoff 不得包含正式 PASS。")
        manifest = archive.read("HANDOFF_MANIFEST.sha256").decode("utf-8").splitlines()
        for line in manifest:
            digest, size_text, name = line.split("  ", 2)
            data = archive.read(name)
            if len(data) != int(size_text) or hashlib.sha256(data).hexdigest() != digest:
                raise TeleiosisError("HANDOFF_MANIFEST", "Verifier handoff manifest 不匹配。", {"path": name})
    return {"status": "PASS", "files": len(names), "subject_hash": identity["subject_hash"], "sha256": sha256_file(path)}
