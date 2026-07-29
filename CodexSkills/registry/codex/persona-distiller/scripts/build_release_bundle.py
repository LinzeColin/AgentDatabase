#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GROUP_ROOT = ROOT.parent / "persona-distiller-group"
TEMPLATE_ROOT = ROOT / "templates" / "bundle"
# ★ 从 VERSION 文件读，不硬编码（原写死 v0.0.0.6，skill 升到 v0.0.0.7 后即失效）
def _read_version() -> str:
    p = Path(__file__).resolve().parent.parent / "VERSION"
    return p.read_text(encoding="utf-8").strip() if p.is_file() else "v0.0.0.0"


VERSION = _read_version()
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


def summarize_freshness() -> dict:
    """把 check_distillation_freshness 的结论如实塞进 bundle manifest。

    **复用检查器，不在这里另写一遍判据**——同一件事两把尺子，
    迟早会分叉，而分叉的那天没有人会发现。
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        from check_distillation_freshness import parse_version, survey
        report = survey(GROUP_ROOT, parse_version(VERSION))
    except Exception as exc:  # 读不到就如实说读不到，不填一个好看的默认值
        return {"available": False, "why": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "distiller_version": report["current"],
        "compatibility_floor": report["floor"],
        "floor_rule": report["floor_rule"],
        "at_or_above_floor": report["at_or_above_floor"],
        "below_floor": report["below_floor"],
        "unknown": report["unknown"],
        "upper_bound_only": report["upper_bound_only"],
        "policy": "低于下限不阻塞发行；统一重蒸安排在 600 人整体完成之后",
    }


def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"Build the one-file Persona Distiller {VERSION} release bundle."
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
        if not (source / "VERSION").is_file():
            raise SystemExit(f"missing VERSION: {source}")
    # ★ 原来这里要求两个 Skill 的 VERSION **完全相等**，意图是
    #   「人物蒸馏到 v0.0.0.8 了，专家团队就不该是 v0.0.0.6/7 蒸出来的」。
    #   意图对，判据测的不是那件事：它是包级的一个数字，不是每人一条记录，
    #   而且把 group 的 VERSION 改一下就能满足——一个人也没重蒸，门却变绿。
    #   实际后果是**自 v0.0.0.9 起本 bundle 一次也没能构建出来**，
    #   因为两个 Skill 的改动节奏本来就不同步。
    #   现在真正的判据是每人一条的 distilled_with + 滚动兼容下限
    #   （见 scripts/check_distillation_freshness.py）；这里只记录事实。
    group_version = (GROUP_ROOT / "VERSION").read_text(encoding="utf-8").strip()
    freshness = summarize_freshness()
    with tempfile.TemporaryDirectory(prefix="persona-distiller-release-") as temporary:
        staging = Path(temporary) / TOP_NAME
        staging.mkdir()
        builder_count = copy_skill(ROOT, staging / "persona-distiller")
        group_count = copy_skill(GROUP_ROOT, staging / "persona-distiller-group")
        for name in ("README.md", "install.py", "install.sh", "install.ps1"):
            shutil.copy2(TEMPLATE_ROOT / name, staging / name)
        # ★ 版本号在打包时**注入**安装器，不留在模板里硬编码。
        #   模板里原写死 BUNDLE_VERSION = "v0.0.0.6"，skill 升到 v0.0.0.7 之后
        #   安装器就一直在拿旧版本比对，`bundled Skill version mismatch` 从那时起必然发生。
        #   这是本次查出的**第五处**同名硬编码（另四处：self_check、build_release_bundle、
        #   build_manifest、test_release_bundle）——**版本号必须有单一真源。**
        installer = staging / "install.py"
        installer.write_text(
            installer.read_text(encoding="utf-8").replace(
                'BUNDLE_VERSION = "v0.0.0.6"', f'BUNDLE_VERSION = "{VERSION}"'),
            encoding="utf-8")
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
                    # 两个 Skill 各自编号，bundle 如实记录两者，不再要求相等。
                    "version": group_version,
                },
            },
            "installer": "install.py",
            "checksums": "checksums.sha256",
            "distillation_freshness": freshness,
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
