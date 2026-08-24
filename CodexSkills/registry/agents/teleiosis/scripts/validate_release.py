#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
import tempfile
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from teleiosis_core.common import TeleiosisError, atomic_write_json, sha256_file  # noqa: E402
from teleiosis_core.packaging import build_deterministic_zip, safe_extract  # noqa: E402


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _run(label: str, command: list[str], output_dir: Path, cwd: Path = ROOT, timeout: int = 900) -> dict[str, Any]:
    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    started = time.monotonic()
    completed = subprocess.run(command, cwd=str(cwd), env=env, capture_output=True, text=True, timeout=timeout, check=False)
    elapsed = round(time.monotonic() - started, 3)
    stdout_path = output_dir / f"{label}.stdout.log"
    stderr_path = output_dir / f"{label}.stderr.log"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    result = {
        "label": label,
        "command": command,
        "returncode": completed.returncode,
        "seconds": elapsed,
        "stdout": stdout_path.name,
        "stdout_sha256": _sha(stdout_path),
        "stderr": stderr_path.name,
        "stderr_sha256": _sha(stderr_path),
    }
    if completed.returncode != 0:
        raise TeleiosisError("VALIDATION_COMMAND_FAILED", "验证命令失败。", result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Teleiosis v5 本地冻结候选验证")
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--runs", type=int, default=3)
    args = parser.parse_args()
    if args.runs < 3 or args.runs > 10:
        raise SystemExit("--runs 必须在 3—10。")
    output_dir = args.output_dir.expanduser().absolute()
    try:
        output_dir.relative_to(ROOT)
        raise SystemExit("验证输出目录必须位于包外。")
    except ValueError:
        pass
    if output_dir.exists() and any(output_dir.iterdir()):
        raise SystemExit("验证输出目录必须不存在或为空。")
    output_dir.mkdir(parents=True, exist_ok=True)

    records: list[dict[str, Any]] = []
    py = sys.executable
    for idx in range(1, args.runs + 1):
        records.append(_run(
            f"full-tests-{idx}",
            [py, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-v"],
            output_dir,
        ))
        records.append(_run(f"doctor-{idx}", [py, "scripts/teleiosis.py", "doctor"], output_dir))

    for label, command in [
        ("strict-check", [py, "scripts/teleiosis.py", "check"]),
        ("taskpack", [py, "scripts/teleiosis.py", "taskpack", "validate"]),
        ("fresh-builder", [py, "scripts/teleiosis.py", "taskpack", "fresh-builder"]),
        ("skill-audit", [py, "scripts/teleiosis.py", "skill-audit"]),
        ("review", [py, "scripts/teleiosis.py", "review"]),
        ("regression", [py, "scripts/teleiosis.py", "regression"]),
    ]:
        records.append(_run(label, command, output_dir))

    with tempfile.TemporaryDirectory() as tmp_text:
        tmp = Path(tmp_text)
        repo = tmp / "moving-main"
        repo.mkdir()
        (repo / "SKILL.md").write_text("semantic reconcile moving main FULL_NO_ROUTING\n", encoding="utf-8")
        semantic_report = output_dir / "semantic-reconcile-report.json"
        records.append(_run(
            "semantic-reconcile",
            [py, "scripts/teleiosis.py", "semantic-reconcile", "--repository", str(repo), "--spec", "templates/semantic-reconcile-spec.example.json", "--output", str(semantic_report)],
            output_dir,
        ))

        handoff = output_dir / "verifier-handoff.zip"
        records.append(_run("verifier-handoff-build", [py, "scripts/teleiosis.py", "verifier-handoff", "build", "--output", str(handoff)], output_dir))
        records.append(_run("verifier-handoff-validate", [py, "scripts/teleiosis.py", "verifier-handoff", "validate", "--zip", str(handoff)], output_dir))

        zip_a = output_dir / "candidate-a.zip"
        zip_b = output_dir / "candidate-b.zip"
        first = build_deterministic_zip(ROOT, zip_a)
        second = build_deterministic_zip(ROOT, zip_b)
        if zip_a.read_bytes() != zip_b.read_bytes():
            raise TeleiosisError("VALIDATION_ZIP_NOT_DETERMINISTIC", "两次冻结构建字节不一致。")
        package_result = {
            "zip_a": zip_a.name,
            "zip_b": zip_b.name,
            "sha256": sha256_file(zip_a),
            "bytes": zip_a.stat().st_size,
            "files": first["files"],
            "uncompressed_bytes": first["uncompressed_bytes"],
            "byte_identical": True,
        }
        atomic_write_json(output_dir / "deterministic-package.json", package_result)

        extracted = safe_extract(zip_a, tmp / "cold-extract")
        records.append(_run("cold-extract-check", [py, "scripts/teleiosis.py", "check"], output_dir, cwd=extracted))
        records.append(_run("cold-extract-tests", [py, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py", "-q"], output_dir, cwd=extracted))

        skills = tmp / "skills"
        records.append(_run("install-dry-run", [py, "START_HERE.py", "install", "--skills-root", str(skills), "--dry-run"], output_dir))
        records.append(_run("install-fresh", [py, "START_HERE.py", "install", "--skills-root", str(skills)], output_dir))
        records.append(_run("install-idempotent", [py, "START_HERE.py", "install", "--skills-root", str(skills)], output_dir))

        upgrade_root = tmp / "upgrade-skills"
        legacy = upgrade_root / "teleiosis"
        (legacy / "constitution").mkdir(parents=True)
        (legacy / "VERSION").write_text("v0.0.0.4\n", encoding="utf-8")
        shutil.copy2(ROOT / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md", legacy / "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md")
        (legacy / "owner-note.txt").write_text("preserve me\n", encoding="utf-8")
        upgrade_result_path = output_dir / "upgrade-result.json"
        completed = subprocess.run(
            [py, "START_HERE.py", "install", "--skills-root", str(upgrade_root)],
            cwd=str(ROOT), env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}, capture_output=True, text=True, timeout=900, check=False,
        )
        (output_dir / "install-upgrade.stdout.log").write_text(completed.stdout, encoding="utf-8")
        (output_dir / "install-upgrade.stderr.log").write_text(completed.stderr, encoding="utf-8")
        if completed.returncode != 0:
            raise TeleiosisError("VALIDATION_UPGRADE_FAILED", "v4→v5 升级失败。", {"stdout": completed.stdout[-1000:], "stderr": completed.stderr[-1000:]})
        payload = json.loads(completed.stdout)
        atomic_write_json(upgrade_result_path, payload)
        receipt = payload["result"]["receipt"]
        records.append({
            "label": "install-upgrade", "returncode": 0, "receipt": receipt,
            "stdout": "install-upgrade.stdout.log", "stdout_sha256": _sha(output_dir / "install-upgrade.stdout.log"),
            "stderr": "install-upgrade.stderr.log", "stderr_sha256": _sha(output_dir / "install-upgrade.stderr.log"),
        })
        records.append(_run("install-rollback", [py, "scripts/teleiosis.py", "rollback-install", "--receipt", receipt], output_dir))
        if (legacy / "VERSION").read_text(encoding="utf-8").strip() != "v0.0.0.4" or not (legacy / "owner-note.txt").is_file():
            raise TeleiosisError("VALIDATION_ROLLBACK_MISMATCH", "回滚后未精确恢复 v4。")

    summary = {
        "schema_version": "teleiosis.local_validation_run.v5",
        "status": "LOCAL_ENGINEERING_PASS",
        "version": "v0.0.0.5",
        "test_runs": args.runs,
        "records": records,
        "deterministic_package": package_result,
        "formal_pass": "NOT_ISSUED",
        "formal_pass_authority": "external independent verifier",
    }
    atomic_write_json(output_dir / "validation-summary.json", summary)
    print(json.dumps({"status": summary["status"], "records": len(records), "output": str(output_dir), "zip_sha256": package_result["sha256"]}, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except TeleiosisError as exc:
        print(json.dumps(exc.as_dict(), ensure_ascii=False, sort_keys=True))
        raise SystemExit(2)
