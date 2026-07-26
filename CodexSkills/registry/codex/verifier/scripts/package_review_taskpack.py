#!/usr/bin/env python3
"""Package one sealed verifier run as the sole builder-facing review ZIP."""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path
from typing import Any, Optional


ARCHIVE_SUFFIX = "_acceptance_review_taskpack.zip"
FIXED_ZIP_TIME = (2026, 1, 1, 0, 0, 0)
REQUIRED_SEALED_FILES = {
    "ACCEPTANCE_ATTESTATION.intoto.json",
    "DEFECT_REPORT.md",
    "EVIDENCE_INDEX.json",
    "FINAL_DECISION.json",
    "MODIFICATION_REPORT.md",
    "RUN_MANIFEST.yaml",
    "SHA256SUMS.txt",
    "TEST_MATRIX.md",
    "VERDICT.md",
}
CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}


class ReviewTaskpackError(Exception):
    """Raised when a safe, verified review taskpack cannot be produced."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _load_finalizer():
    path = Path(__file__).resolve().with_name("finalize_acceptance_run.py")
    spec = importlib.util.spec_from_file_location("verifier_review_pack_finalizer", path)
    if spec is None or spec.loader is None:
        raise ReviewTaskpackError(f"cannot load finalizer: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


FINALIZER = _load_finalizer()


def _safe_files(run_dir: Path) -> list[Path]:
    if not run_dir.is_dir() or run_dir.is_symlink():
        raise ReviewTaskpackError(f"run directory must be a real directory: {run_dir}")
    files: list[Path] = []
    seen_casefold: dict[str, str] = {}
    for path in run_dir.rglob("*"):
        relative = path.relative_to(run_dir)
        relative_text = relative.as_posix()
        if any(part in {"", ".", ".."} for part in relative.parts):
            raise ReviewTaskpackError(f"unsafe run path: {relative_text}")
        folded = relative_text.casefold()
        prior = seen_casefold.get(folded)
        if prior is not None and prior != relative_text:
            raise ReviewTaskpackError(
                f"case-insensitive path collision: {prior!r} vs {relative_text!r}"
            )
        seen_casefold[folded] = relative_text
        mode = path.lstat().st_mode
        if stat.S_ISLNK(mode):
            raise ReviewTaskpackError(f"symlink forbidden in sealed run: {relative_text}")
        if stat.S_ISDIR(mode):
            if path.name in CACHE_NAMES:
                raise ReviewTaskpackError(f"cache directory forbidden in sealed run: {relative_text}")
            continue
        if not stat.S_ISREG(mode):
            raise ReviewTaskpackError(f"non-regular run entry forbidden: {relative_text}")
        if path.suffix in {".pyc", ".pyo"}:
            raise ReviewTaskpackError(f"compiled cache file forbidden: {relative_text}")
        files.append(path)
    return sorted(files, key=lambda item: item.relative_to(run_dir).as_posix())


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, FIXED_ZIP_TIME)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.create_system = 3
    info.external_attr = (stat.S_IFREG | 0o644) << 16
    return info


def _entrypoint_text(run_name: str, evidence_root: str) -> str:
    return (
        "# 验收复审任务包 — 开发 Agent 先看这里\n\n"
        "这是 verifier 已封存并复验的只读验收结果。请不要修改本 ZIP 内证据，"
        "而是在目标产品自己的隔离 worktree 中完成开发。\n\n"
        "## 开发顺序\n\n"
        f"1. 先读 `{run_name}/VERDICT.md`，确认裁决范围与不可豁免门。\n"
        f"2. 按 `{run_name}/DEFECT_REPORT.md` 逐项最小复现。\n"
        f"3. 以 `{run_name}/MODIFICATION_REPORT.md` 作为修复任务与回归边界。\n"
        f"4. 用 `{run_name}/TEST_MATRIX.md` 和原始 Evidence 证明修复，不改写旧证据。\n"
        "5. 交付新的不可变 commit/build/artifact 后，交给 fresh verifier 独立复验。\n\n"
        "## 完整性\n\n"
        f"- Evidence root SHA-256: `{evidence_root}`\n"
        f"- 内部逐文件校验：`{run_name}/SHA256SUMS.txt`\n"
        f"- 机器裁决：`{run_name}/FINAL_DECISION.json`\n"
        f"- Test Result attestation: `{run_name}/ACCEPTANCE_ATTESTATION.intoto.json`\n\n"
        "本任务包是开发输入，不是修复后的通过证明。\n"
    )


def package_review_taskpack(
    run_dir: Path,
    output: Optional[Path] = None,
) -> dict[str, Any]:
    run_dir = Path(os.path.abspath(os.fspath(run_dir.expanduser())))
    try:
        verification = FINALIZER.verify(run_dir)
    except Exception as error:
        raise ReviewTaskpackError(f"sealed run verification failed: {error}") from error

    missing = sorted(name for name in REQUIRED_SEALED_FILES if not (run_dir / name).is_file())
    if missing:
        raise ReviewTaskpackError(f"sealed run missing builder-required files: {missing}")

    files = _safe_files(run_dir)
    output = output or run_dir.with_name(f"{run_dir.name}{ARCHIVE_SUFFIX}")
    output = Path(os.path.abspath(os.fspath(output.expanduser())))
    try:
        output.relative_to(run_dir)
    except ValueError:
        pass
    else:
        raise ReviewTaskpackError("review taskpack ZIP must be outside the sealed run directory")
    if output.suffix.lower() != ".zip":
        raise ReviewTaskpackError("review taskpack output must end with .zip")
    if output.exists() or output.is_symlink():
        raise ReviewTaskpackError(f"refusing to overwrite existing output: {output}")
    if not output.parent.is_dir() or output.parent.is_symlink():
        raise ReviewTaskpackError(f"output parent must be a real existing directory: {output.parent}")

    evidence_root = str(verification.get("evidence_root_sha256", ""))
    if len(evidence_root) != 64:
        raise ReviewTaskpackError("finalizer verification did not return an evidence root SHA-256")
    entrypoint = _entrypoint_text(run_dir.name, evidence_root).encode("utf-8")

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.", suffix=".tmp", dir=str(output.parent)
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary,
            mode="w",
            compression=zipfile.ZIP_DEFLATED,
            compresslevel=9,
            allowZip64=True,
        ) as archive:
            archive.writestr(_zip_info("README_FIRST.md"), entrypoint)
            for source in files:
                relative = source.relative_to(run_dir).as_posix()
                archive_name = f"{run_dir.name}/{relative}"
                with source.open("rb") as input_handle, archive.open(
                    _zip_info(archive_name), mode="w", force_zip64=True
                ) as output_handle:
                    shutil.copyfileobj(input_handle, output_handle, length=1024 * 1024)
        with temporary.open("rb") as handle:
            os.fsync(handle.fileno())
        os.replace(temporary, output)
    except Exception:
        temporary.unlink(missing_ok=True)
        output.unlink(missing_ok=True)
        raise

    return {
        "ok": True,
        "schema_version": "verifier-acceptance-review-taskpack-v1",
        "output": str(output),
        "sha256": sha256_file(output),
        "archive_file_count": len(files) + 1,
        "entrypoint": "README_FIRST.md",
        "sealed_run": run_dir.name,
        "evidence_root_sha256": evidence_root,
    }


def parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def main(argv: Optional[list[str]] = None) -> int:
    args = parse_args(argv)
    try:
        result = package_review_taskpack(args.run_dir, args.output)
    except (OSError, ReviewTaskpackError, zipfile.BadZipFile) as error:
        if args.json:
            print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2))
        else:
            print(f"error: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"created: {result['output']}")
        print(f"sha256: {result['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
