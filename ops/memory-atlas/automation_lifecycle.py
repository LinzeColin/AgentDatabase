#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
import tempfile
try:  # 3.11+
    import tomllib
except ModuleNotFoundError:  # 3.9/3.10 — the Owner's system interpreter is 3.9.6
    try:
        import tomli as tomllib  # type: ignore[no-redef]
    except ModuleNotFoundError:  # pragma: no cover - exercised only without tomli
        import re as _re

        class tomllib:  # type: ignore[no-redef]
            """Minimal reader for the flat `key = "value"` automation.toml only.

            Not a TOML implementation: it exists so the repository's own gate is
            runnable on the interpreter the Owner actually has. Anything with a
            table header, an array or a multiline string raises rather than
            silently returning a wrong parse.
            """

            _PAIR = _re.compile(r'^([A-Za-z0-9_.-]+)\s*=\s*"([^"]*)"$')

            @staticmethod
            def load(handle: Any) -> dict[str, Any]:
                value: dict[str, Any] = {}
                for raw in handle.read().decode("utf-8").splitlines():
                    line = raw.strip()
                    if not line or line.startswith("#"):
                        continue
                    match = tomllib._PAIR.match(line)
                    if not match:
                        raise ValueError(f"unsupported TOML line for the fallback reader: {line!r}")
                    value[match.group(1)] = match.group(2)
                return value
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


NEW_ID = "memory-atlas-daily-source-capture"
OLD_DEFAULT_ID = "codex"
REQUIRED_RETIRE_GATES = {
    "new_automation_run_succeeded",
    "r2_full_readback_succeeded",
    "private_database_fact_committed",
    "memory_atlas_refresh_succeeded",
    "isolated_restore_succeeded",
}


class LifecycleError(RuntimeError):
    pass


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def safe_dir(root: Path, identifier: str) -> Path:
    if not identifier or any(char not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_" for char in identifier):
        raise LifecycleError(f"automation id 不安全：{identifier}")
    path = (root / identifier).resolve()
    path.relative_to(root.resolve())
    return path


def snapshot_tree(source: Path, destination: Path) -> dict[str, Any]:
    destination.mkdir(parents=True, exist_ok=False)
    records: list[dict[str, Any]] = []
    for path in sorted(source.rglob("*")):
        if path.is_symlink():
            raise LifecycleError(f"旧 Automation 含符号链接，拒绝迁移：{path}")
        if not path.is_file():
            continue
        relative = path.relative_to(source)
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, target)
        records.append({
            "path": relative.as_posix(),
            "size_bytes": target.stat().st_size,
            "sha256": sha256(target),
        })
    manifest = {
        "schema_version": "memory_atlas.automation_archive.v1",
        "source": str(source),
        "archived_at": utc_now(),
        "files": records,
    }
    manifest_path = destination / "ARCHIVE_MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    manifest["manifest_sha256"] = sha256(manifest_path)
    return manifest


def verify_archive(archive_dir: Path) -> dict[str, Any]:
    manifest_path = archive_dir / "ARCHIVE_MANIFEST.json"
    if not manifest_path.is_file():
        raise LifecycleError("旧 Automation 归档缺少 ARCHIVE_MANIFEST.json")
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    failures: list[str] = []
    for row in manifest.get("files", []):
        path = archive_dir / row["path"]
        if not path.is_file() or sha256(path) != row["sha256"]:
            failures.append(str(row["path"]))
    if failures:
        raise LifecycleError(f"旧 Automation 归档校验失败：{failures}")
    return {"state": "PASS", "file_count": len(manifest.get("files", [])), "archive": str(archive_dir)}


def pause_toml(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    changed = False
    output: list[str] = []
    for line in lines:
        if line.strip().startswith("status") and "=" in line:
            output.append('status = "PAUSED"')
            changed = True
        else:
            output.append(line)
    if not changed:
        output.append('status = "PAUSED"')
    temporary = path.with_suffix(".toml.partial")
    temporary.write_text("\n".join(output) + "\n", encoding="utf-8")
    with temporary.open("rb") as handle:
        tomllib.load(handle)
    temporary.replace(path)


def diagnose_old(root: Path, archive_root: Path, old_id: str) -> dict[str, Any]:
    old_dir = safe_dir(root, old_id)
    if not old_dir.is_dir():
        return {
            "schema_version": "memory_atlas.old_automation_diagnosis.v1",
            "state": "ALREADY_ABSENT",
            "old_id": old_id,
            "paused": True,
            "message_zh": "旧 Automation 目录不存在；保留无操作证据。",
        }
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    archive_dir = archive_root.resolve() / f"{old_id}-{timestamp}"
    manifest = snapshot_tree(old_dir, archive_dir)
    archive_check = verify_archive(archive_dir)
    config = old_dir / "automation.toml"
    if not config.is_file():
        raise LifecycleError("旧 Automation 缺少 automation.toml；归档已保留但不能宣称安全暂停")
    pause_toml(config)
    with config.open("rb") as handle:
        paused = tomllib.load(handle).get("status") == "PAUSED"
    if not paused:
        raise LifecycleError("旧 Automation 未能原子暂停")
    diagnosis = {
        "schema_version": "memory_atlas.old_automation_diagnosis.v1",
        "state": "ARCHIVED_VERIFIED_AND_PAUSED",
        "old_id": old_id,
        "archive_dir": str(archive_dir),
        "archive_manifest_sha256": manifest["manifest_sha256"],
        "archive_check": archive_check,
        "paused": True,
        "failure_migration": {
            "single_monolithic_stream": "replaced_by_content_addressed_incremental_objects",
            "no_checkpoint": "replaced_by_per_object_receipts_and_runtime_outbox",
            "keychain_single_host_recovery": "removed_from_primary_path",
            "no_remote_readback": "replaced_by_full_object_download_and_sha256",
            "no_restore_proof": "replaced_by_isolated_restore_drill",
        },
    }
    (archive_dir / "DIAGNOSIS.json").write_text(
        json.dumps(diagnosis, ensure_ascii=False, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    return diagnosis


def new_automation_toml(repo_root: Path) -> str:
    prompt = (
        "执行 Memory Atlas 每日源端采集。只运行任务包已落库的确定性命令："
        "python3 -B OpenAIDatabase/scripts/memory_atlas_source_capture_entry.py。"
        "不得研究、改代码、创建分支、等待人工或把排队状态写成成功。"
        "输出 run_id、状态、来源覆盖、R2 完整读回、Private-Database 事实提交、"
        "Memory Atlas 刷新和恢复门的证据摘要。失败必须生成 Incident 并保留可重试状态。"
    )
    escaped_prompt = prompt.replace("\\", "\\\\").replace('"', '\\"')
    escaped_cwd = str(repo_root.resolve()).replace("\\", "\\\\").replace('"', '\\"')
    return (
        'version = 1\n'
        f'id = "{NEW_ID}"\n'
        'name = "Memory Atlas 每日全量无损备份"\n'
        f'prompt = "{escaped_prompt}"\n'
        'status = "ACTIVE"\n'
        'rrule = "FREQ=DAILY;BYHOUR=3;BYMINUTE=0"\n'
        f'cwds = ["{escaped_cwd}"]\n'
    )


def install_new(root: Path, repo_root: Path) -> dict[str, Any]:
    target = safe_dir(root, NEW_ID)
    target.mkdir(parents=True, exist_ok=True)
    config = target / "automation.toml"
    payload = new_automation_toml(repo_root)
    temporary = config.with_suffix(".toml.partial")
    temporary.write_text(payload, encoding="utf-8")
    with temporary.open("rb") as handle:
        parsed = tomllib.load(handle)
    if parsed.get("id") != NEW_ID or parsed.get("status") != "ACTIVE":
        raise LifecycleError("新 Automation 配置无法通过本地契约")
    temporary.replace(config)
    memory = target / "memory.md"
    memory.write_text(
        "# Memory Atlas 每日源端采集\n\n"
        "本 Automation 只负责 Mac 本机独有来源的确定性采集。\n"
        "OVH 负责 7×24 对账、分析、刷新、自愈和状态投影。\n"
        "任何 WAITING_SOURCE、UNKNOWN、PARTIAL 或 FAILED 都不得改写为成功。\n",
        encoding="utf-8",
    )
    return verify_new(root)


def verify_new(root: Path) -> dict[str, Any]:
    target = safe_dir(root, NEW_ID)
    config = target / "automation.toml"
    memory = target / "memory.md"
    if not config.is_file() or not memory.is_file():
        raise LifecycleError("新 Automation 文件不完整")
    with config.open("rb") as handle:
        parsed = tomllib.load(handle)
    expected = {
        "version": 1,
        "id": NEW_ID,
        "status": "ACTIVE",
        "rrule": "FREQ=DAILY;BYHOUR=3;BYMINUTE=0",
    }
    mismatches = {key: {"expected": value, "actual": parsed.get(key)} for key, value in expected.items() if parsed.get(key) != value}
    if mismatches:
        raise LifecycleError(f"新 Automation 契约不匹配：{mismatches}")
    cwds = parsed.get("cwds")
    if not isinstance(cwds, list) or len(cwds) != 1 or not Path(str(cwds[0])).is_dir():
        raise LifecycleError("新 Automation cwd 不存在或不唯一")
    return {
        "schema_version": "memory_atlas.new_automation_verification.v1",
        "state": "PASS",
        "id": NEW_ID,
        "schedule": expected["rrule"],
        "cwd": str(cwds[0]),
        "config_sha256": sha256(config),
        "memory_sha256": sha256(memory),
    }


def retire_old(root: Path, old_id: str, evidence_path: Path) -> dict[str, Any]:
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    gates = evidence.get("gates")
    if not isinstance(gates, dict):
        raise LifecycleError("替代证据缺少 gates object")
    missing = sorted(key for key in REQUIRED_RETIRE_GATES if gates.get(key) is not True)
    if missing:
        raise LifecycleError(f"旧 Automation 删除门未满足：{missing}")
    new_check = verify_new(root)
    old_dir = safe_dir(root, old_id)
    if old_dir.is_dir():
        config = old_dir / "automation.toml"
        if config.is_file():
            with config.open("rb") as handle:
                if tomllib.load(handle).get("status") != "PAUSED":
                    raise LifecycleError("旧 Automation 未处于 PAUSED，拒绝删除")
        shutil.rmtree(old_dir)
    return {
        "schema_version": "memory_atlas.old_automation_retirement.v1",
        "state": "RETIRED",
        "old_id": old_id,
        "old_directory_absent": not old_dir.exists(),
        "replacement": new_check,
        "evidence_sha256": sha256(evidence_path),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Memory Atlas Codex Automation lifecycle")
    parser.add_argument("--automation-root", type=Path, default=Path.home() / ".codex" / "automations")
    sub = parser.add_subparsers(dest="command", required=True)
    diagnose = sub.add_parser("diagnose-old")
    diagnose.add_argument("--old-id", default=OLD_DEFAULT_ID)
    diagnose.add_argument("--archive-root", type=Path, required=True)
    install = sub.add_parser("install-new")
    install.add_argument("--repo-root", type=Path, required=True)
    sub.add_parser("verify-new")
    retire = sub.add_parser("retire-old")
    retire.add_argument("--old-id", default=OLD_DEFAULT_ID)
    retire.add_argument("--evidence", type=Path, required=True)
    args = parser.parse_args()
    root = args.automation_root.expanduser().resolve()
    root.mkdir(parents=True, exist_ok=True)
    try:
        if args.command == "diagnose-old":
            result = diagnose_old(root, args.archive_root.expanduser().resolve(), args.old_id)
        elif args.command == "install-new":
            result = install_new(root, args.repo_root.expanduser().resolve())
        elif args.command == "verify-new":
            result = verify_new(root)
        else:
            result = retire_old(root, args.old_id, args.evidence.expanduser().resolve())
    except LifecycleError as exc:
        print(json.dumps({"state": "BLOCKED", "message_zh": str(exc)}, ensure_ascii=False, indent=2))
        raise SystemExit(2) from exc
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == "__main__":
    main()
