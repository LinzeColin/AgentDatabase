#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP_ROOT = ROOT.parent / "persona-distiller-group"
TEMPLATE_ROOT = ROOT / "templates" / "bundle"
VERSION = "v0.0.0.5"
TOP_NAME = f"PersonaDistiller-Final-{VERSION}"
FIXED_ZIP_TIME = (2026, 7, 23, 0, 0, 0)
EXCLUDED_DIRS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    "_build",
    "build",
    "dist",
    "workspaces",
}
EXCLUDED_FILES = {".DS_Store"}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def included(source_root: Path, path: Path) -> bool:
    relative = path.relative_to(source_root)
    if any(part in EXCLUDED_DIRS for part in relative.parts):
        return False
    if path.name in EXCLUDED_FILES or path.suffix in {".pyc", ".pyo"}:
        return False
    if source_root == ROOT and path.suffix == ".zip":
        return False
    return path.is_file() and not path.is_symlink()


def copy_skill(source: Path, destination: Path) -> int:
    count = 0
    for path in sorted(source.rglob("*")):
        if not included(source, path):
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        count += 1
    return count


def deterministic_zip(staging: Path, output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(
        output,
        "w",
        compression=zipfile.ZIP_DEFLATED,
        compresslevel=9,
    ) as archive:
        for path in sorted(item for item in staging.rglob("*") if item.is_file()):
            relative = path.relative_to(staging.parent).as_posix()
            info = zipfile.ZipInfo(relative, date_time=FIXED_ZIP_TIME)
            info.compress_type = zipfile.ZIP_DEFLATED
            mode = 0o755 if path.suffix in {".py", ".sh"} else 0o644
            info.external_attr = (mode & 0xFFFF) << 16
            archive.writestr(info, path.read_bytes())


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build the one-file Persona Distiller v0.0.0.5 release bundle."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.home() / "Downloads" / f"{TOP_NAME}.zip",
    )
    args = parser.parse_args()
    output = args.output.expanduser().resolve()
    for source in (ROOT, GROUP_ROOT):
        if not (source / "SKILL.md").is_file():
            raise SystemExit(f"missing Skill root: {source}")
        if (source / "VERSION").read_text(encoding="utf-8").strip() != VERSION:
            raise SystemExit(f"version mismatch: {source}")
    with tempfile.TemporaryDirectory(prefix="persona-distiller-release-") as temporary:
        staging = Path(temporary) / TOP_NAME
        staging.mkdir()
        builder_count = copy_skill(ROOT, staging / "persona-distiller")
        group_count = copy_skill(GROUP_ROOT, staging / "persona-distiller-group")
        for name in ("README.md", "install.py", "install.sh", "install.ps1"):
            shutil.copy2(TEMPLATE_ROOT / name, staging / name)
        (staging / "VERSION").write_text(VERSION + "\n", encoding="utf-8")
        payload_files = sorted(
            path
            for path in staging.rglob("*")
            if path.is_file()
            and path.relative_to(staging).as_posix()
            not in {"PACKAGE_MANIFEST.json", "checksums.sha256"}
        )
        manifest = {
            "schema_version": "1.0",
            "artifact_kind": "persona-distiller-complete-release",
            "version": VERSION,
            "created_at": "2026-07-23T00:00:00Z",
            "single_archive_only": True,
            "top_level_count": 1,
            "default_install_root": "~/.codex/skills",
            "duplicate_install_root_forbidden": "~/.agents/skills",
            "skills": {
                "persona-distiller": {
                    "path": "persona-distiller",
                    "file_count": builder_count,
                },
                "persona-distiller-group": {
                    "path": "persona-distiller-group",
                    "file_count": group_count,
                    "canonical_registry": True,
                },
            },
            "installer": "install.py",
            "checksums": "checksums.sha256",
            "registered_persona_deliveries_included": True,
            "person_name_constraints": False,
        }
        (staging / "PACKAGE_MANIFEST.json").write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        checksummed = sorted(
            path
            for path in staging.rglob("*")
            if path.is_file() and path != staging / "checksums.sha256"
        )
        (staging / "checksums.sha256").write_text(
            "".join(
                f"{sha256_file(path)}  {path.relative_to(staging).as_posix()}\n"
                for path in checksummed
            ),
            encoding="utf-8",
        )
        deterministic_zip(staging, output)
    with zipfile.ZipFile(output) as archive:
        top_levels = {name.split("/", 1)[0] for name in archive.namelist() if name}
        if top_levels != {TOP_NAME}:
            output.unlink(missing_ok=True)
            raise SystemExit(f"invalid top-level roots: {sorted(top_levels)}")
        if any(name.endswith(".zip.sha256") for name in archive.namelist()):
            output.unlink(missing_ok=True)
            raise SystemExit("sidecar checksum files are forbidden")
    print(
        json.dumps(
            {
                "output": str(output),
                "sha256": sha256_file(output),
                "size_bytes": output.stat().st_size,
                "top_level": TOP_NAME,
                "single_archive_only": True,
            },
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
