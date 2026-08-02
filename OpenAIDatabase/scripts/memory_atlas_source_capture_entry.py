#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


def find_repo_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / "OpenAIDatabase" / "AGENTS.md").is_file() and (candidate / "MemoryAtlas").is_dir():
            return candidate
    raise RuntimeError("无法定位 AgentDatabase 仓库根目录")


def load_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> None:
    repo = find_repo_root(Path(__file__).resolve())
    env_path = Path(os.environ.get(
        "MEMORY_ATLAS_ENV_FILE",
        str(Path.home() / ".codex" / "memory-atlas" / "memory-atlas.env"),
    )).expanduser()
    if not env_path.is_file():
        print(json.dumps({
            "state": "BLOCKED",
            "message_zh": "缺少已验证的 Memory Atlas 受保护环境文件。先运行 bootstrap-protected-env。",
            "expected_path": str(env_path),
        }, ensure_ascii=False, indent=2))
        raise SystemExit(2)
    values = load_env_file(env_path)
    # The protected env contains OVH defaults, while the frozen last-mile command
    # exports Mac-local paths for source capture. Explicit process values are the
    # authoritative local binding; otherwise retain the entrypoint's safe local
    # defaults instead of accidentally using /srv paths on macOS.
    process_env = os.environ
    linked_protected_root = env_path.resolve().parent if env_path.is_symlink() else None
    default_runtime_dir = (
        linked_protected_root / "memory-atlas-runtime"
        if linked_protected_root
        else Path.home() / ".codex" / "memory-atlas" / "runtime"
    )
    default_work_dir = (
        linked_protected_root / "memory-atlas-work"
        if linked_protected_root
        else Path.home() / ".codex" / "memory-atlas" / "work"
    )
    default_web_data_dir = (
        linked_protected_root / "memory-atlas-preview"
        if linked_protected_root
        else repo / "MemoryAtlas" / "public"
    )
    values.update({
        "MEMORY_ATLAS_PRIVATE_DB_CLIENT": process_env.get(
            "MEMORY_ATLAS_PRIVATE_DB_CLIENT",
            str(repo / "OpenAIDatabase" / "scripts" / "private_db_client.py"),
        ),
        "MEMORY_ATLAS_SOURCE_REGISTRY": process_env.get(
            "MEMORY_ATLAS_SOURCE_REGISTRY",
            str(repo / "ops" / "memory-atlas" / "source-registry.json"),
        ),
        "MEMORY_ATLAS_RUNTIME_DIR": process_env.get(
            "MEMORY_ATLAS_RUNTIME_DIR",
            str(default_runtime_dir),
        ),
        "MEMORY_ATLAS_WORK_DIR": process_env.get(
            "MEMORY_ATLAS_WORK_DIR",
            str(default_work_dir),
        ),
        "MEMORY_ATLAS_WEB_DATA_DIR": process_env.get(
            "MEMORY_ATLAS_WEB_DATA_DIR",
            str(default_web_data_dir),
        ),
        "MEMORY_ATLAS_PUBLIC_SNAPSHOT": process_env.get(
            "MEMORY_ATLAS_PUBLIC_SNAPSHOT",
            str(repo / "MemoryAtlas" / "public" / "memory_atlas.json"),
        ),
        "MEMORY_ATLAS_EXTERNAL_ORIGIN": process_env.get(
            "MEMORY_ATLAS_EXTERNAL_ORIGIN",
            values.get("MEMORY_ATLAS_EXTERNAL_ORIGIN", "https://memoryatlas.linzezhang.com"),
        ),
        "MEMORY_ATLAS_SOURCE_HOST_ID": process_env.get(
            "MEMORY_ATLAS_SOURCE_HOST_ID",
            values.get("MEMORY_ATLAS_SOURCE_HOST_ID", "mac-codex-source"),
        ),
        "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS": process_env.get(
            "MEMORY_ATLAS_OPENAI_DATABASE_DATA_ROOTS",
            str(repo / "OpenAIDatabase" / "data"),
        ),
    })
    if linked_protected_root:
        values["MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS"] = process_env.get(
            "MEMORY_ATLAS_VERIFIED_EVIDENCE_ROOTS",
            str(linked_protected_root / "memory-atlas-evidence-adapters"),
        )
    env = values.copy()
    env.update(process_env)
    protected_python = env_path.resolve().parent / "memory-atlas-venv" / "bin" / "python"
    configured_python = process_env.get("MEMORY_ATLAS_SOURCE_PYTHON", "").strip()
    python_executable = configured_python or (str(protected_python) if protected_python.is_file() else sys.executable)
    command = [python_executable, "-B", "-m", "OpenAIDatabase.scripts.memory_atlas_private", "capture"]
    completed = subprocess.run(command, cwd=repo, env=env)
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
