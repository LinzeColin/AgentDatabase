#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

SOURCE = Path(__file__).resolve().parent


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_delivery() -> dict[str, object]:
    checksum_path = SOURCE / "delivery-checksums.sha256"
    if not checksum_path.is_file():
        raise ValueError("missing delivery-checksums.sha256")
    expected_files = {
        path.relative_to(SOURCE).as_posix()
        for path in SOURCE.rglob("*")
        if path.is_file() and path != checksum_path
    }
    records: dict[str, str] = {}
    for line_number, line in enumerate(checksum_path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        checksum, separator, relative = line.partition("  ")
        if not separator or len(checksum) != 64 or any(character not in "0123456789abcdef" for character in checksum):
            raise ValueError(f"invalid checksum line {line_number}")
        path = PurePosixPath(relative)
        if path.is_absolute() or ".." in path.parts or relative in records:
            raise ValueError(f"unsafe or duplicate checksum path: {relative}")
        candidate = (SOURCE / relative).resolve()
        try:
            candidate.relative_to(SOURCE.resolve())
        except ValueError as exc:
            raise ValueError(f"checksum path escapes delivery: {relative}") from exc
        if not candidate.is_file():
            raise ValueError(f"missing delivery file: {relative}")
        if sha256_file(candidate) != checksum:
            raise ValueError(f"checksum mismatch: {relative}")
        records[relative] = checksum
    if set(records) != expected_files:
        raise ValueError(
            f"checksum coverage mismatch: missing={sorted(expected_files - set(records))}, "
            f"extra={sorted(set(records) - expected_files)}"
        )
    manifest = json.loads((SOURCE / "delivery-manifest.json").read_text(encoding="utf-8"))
    runtime = manifest.get("runtime", {})
    runtime_path = SOURCE / str(runtime.get("path", ""))
    if not runtime_path.is_file():
        raise ValueError("manifest runtime path is missing")
    if sha256_file(runtime_path) != runtime.get("sha256"):
        raise ValueError("embedded runtime checksum mismatch")
    if runtime_path.stat().st_size != runtime.get("size_bytes"):
        raise ValueError("embedded runtime size mismatch")
    return {
        "verified": True,
        "files": len(records),
        "runtime_sha256": runtime.get("sha256"),
        "product_version": manifest.get("product_version"),
    }


def safe_extract_runtime(runtime_path: Path, destination: Path) -> Path:
    top_levels: set[str] = set()
    with zipfile.ZipFile(runtime_path) as archive:
        for info in archive.infolist():
            name = info.filename
            path = PurePosixPath(name)
            if path.is_absolute() or ".." in path.parts or "\\" in name or "\x00" in name:
                raise ValueError(f"unsafe runtime ZIP member: {name}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise ValueError(f"runtime ZIP symlink is forbidden: {name}")
            top_levels.add(path.parts[0])
        if len(top_levels) != 1:
            raise ValueError("runtime ZIP must have one top-level directory")
        archive.extractall(destination)
    return destination / next(iter(top_levels))


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify this full delivery and install its embedded persona Skill.")
    parser.add_argument("--root", type=Path, default=Path.home() / ".codex" / "skills")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        verification = verify_delivery()
        manifest = json.loads((SOURCE / "delivery-manifest.json").read_text(encoding="utf-8"))
        runtime_path = SOURCE / manifest["runtime"]["path"]
        with tempfile.TemporaryDirectory(prefix="persona-delivery-install-") as temp:
            runtime_root = safe_extract_runtime(runtime_path, Path(temp))
            command = [
                sys.executable,
                str(runtime_root / "install.py"),
                "--root",
                str(args.root.expanduser().resolve()),
            ]
            if args.force:
                command.append("--force")
            completed = subprocess.run(
                command,
                cwd=runtime_root,
                text=True,
                capture_output=True,
            )
            if completed.returncode != 0:
                raise ValueError(
                    "embedded runtime installer failed: "
                    + (completed.stderr.strip() or completed.stdout.strip())
                )
            runtime_result = json.loads(completed.stdout)
    except (OSError, ValueError, zipfile.BadZipFile, json.JSONDecodeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "installed": True,
                "delivery_verification": verification,
                "runtime_install": runtime_result,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
