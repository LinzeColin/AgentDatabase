"""S06-P1-T2 shallow public-raw layout and runtime-isolation audit."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

from .source_registry import REGISTRY_PATH, SourceRegistryError, load_source_registry, sync_source_map


LAYOUT_CONFIG_PATH = Path("config/data_sources/public_raw_layout.json")
LAYOUT_SCHEMA_VERSION = "memory_atlas.public_raw_layout.v1_2_1_s06_p1_t2"
TASK_ID = "S06-P1-T2"
RAW_ROOT = Path("data/public_raw")
CONTROL_FILES = ("data/public_raw/README.md",)
SOURCE_ROOTS = {
    "chatgpt": "data/public_raw/chatgpt",
    "codex": "data/public_raw/codex",
    "generic_agent_template": "data/public_raw/agents/{source_id}",
}
SHALLOW_LAYOUT = {
    "max_directory_depth_below_root": 2,
    "allowed_static_subdirectories": ["codex/sessions"],
    "registered_agent_directories_only": True,
    "symlinks_allowed": False,
}
RECOVERY_LAYOUT = {
    "partition_key": "source_id",
    "tracked_files_required": True,
    "layout_only": True,
    "restore_implementation_task": "S06-P2-T3",
}
ISOLATION = {
    "frontend_app": "apps/memory-atlas",
    "expected_vite_public_dir": "data/derived/visualization",
    "build_output": "apps/memory-atlas/dist",
    "default_codex_intent": "startup",
    "forbidden_default_context_prefixes": ["data/public_raw/"],
}
_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "source_registry_ref",
    "root",
    "control_files",
    "source_roots",
    "shallow_layout",
    "recovery_layout",
    "isolation",
}
_FRONTEND_SUFFIXES = {".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"}


class PublicRawLayoutError(ValueError):
    """Raised when the public-raw layout or isolation boundary is invalid."""


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise PublicRawLayoutError(f"{field} must be an object")
    return value


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise PublicRawLayoutError(f"{field} must be a canonical repository-relative path")
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or value.startswith("//")
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise PublicRawLayoutError(f"{field} must be a safe repository-relative path")
    return value


def validate_layout_contract(payload: Any) -> dict[str, Any]:
    contract = _mapping(payload, "public_raw_layout")
    if set(contract) != _CONTRACT_KEYS:
        raise PublicRawLayoutError("public_raw_layout keys do not match the canonical contract")
    if contract.get("schema_version") != LAYOUT_SCHEMA_VERSION or contract.get("task_id") != TASK_ID:
        raise PublicRawLayoutError("public_raw_layout identity is unsupported")
    if _safe_relative_path(contract.get("source_registry_ref"), "source_registry_ref") != REGISTRY_PATH.as_posix():
        raise PublicRawLayoutError("source_registry_ref must use the canonical source registry")
    if _safe_relative_path(contract.get("root"), "root") != RAW_ROOT.as_posix():
        raise PublicRawLayoutError("root must be data/public_raw")
    control_files = contract.get("control_files")
    if control_files != list(CONTROL_FILES):
        raise PublicRawLayoutError("control_files must contain only data/public_raw/README.md")
    for index, path in enumerate(control_files):
        _safe_relative_path(path, f"control_files[{index}]")
    if _mapping(contract.get("source_roots"), "source_roots") != SOURCE_ROOTS:
        raise PublicRawLayoutError("source_roots must match the TaskPack shallow source families")
    if _mapping(contract.get("shallow_layout"), "shallow_layout") != SHALLOW_LAYOUT:
        raise PublicRawLayoutError("shallow_layout drifted from the bounded two-level contract")
    if _mapping(contract.get("recovery_layout"), "recovery_layout") != RECOVERY_LAYOUT:
        raise PublicRawLayoutError("recovery_layout must remain tracked, source-partitioned and layout-only")
    if _mapping(contract.get("isolation"), "isolation") != ISOLATION:
        raise PublicRawLayoutError("isolation drifted from the frontend/default-Codex boundary")
    for field in ("frontend_app", "expected_vite_public_dir", "build_output"):
        _safe_relative_path(contract["isolation"][field], f"isolation.{field}")
    return contract


def load_layout_contract(database_dir: Path, path: Path | None = None) -> dict[str, Any]:
    target = path or database_dir.resolve() / LAYOUT_CONFIG_PATH
    try:
        payload = json.loads(target.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise PublicRawLayoutError(f"cannot read public-raw layout contract: {target}") from exc
    return validate_layout_contract(payload)


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _registered_agent_ids(registry: dict[str, Any]) -> set[str]:
    return {
        str(source["source_id"])
        for source in registry["sync_sources"]
        if source["source_type"] == "generic_agent" and source["source_id"] != "generic_agent_template"
    }


def classify_public_raw_path(relative_path: Path, registered_agent_ids: set[str]) -> str:
    parts = relative_path.parts
    if relative_path.as_posix() == "README.md":
        return "control"
    if len(parts) >= 2 and parts[0] in {"chatgpt", "codex"}:
        return parts[0]
    if len(parts) >= 3 and parts[0] == "agents" and parts[1] in registered_agent_ids:
        return parts[1]
    raise PublicRawLayoutError(f"public-raw file is outside a registered shallow source partition: {relative_path}")


def _tracked_public_raw_files(database_dir: Path) -> set[str]:
    result = subprocess.run(
        ["git", "ls-files", "--", RAW_ROOT.as_posix()],
        cwd=database_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PublicRawLayoutError("cannot verify Git tracking for data/public_raw")
    return {line.strip() for line in result.stdout.splitlines() if line.strip()}


def _audit_tree(
    database_dir: Path,
    contract: dict[str, Any],
    registry: dict[str, Any],
    *,
    enforce_git_tracking: bool,
) -> dict[str, Any]:
    raw_root = database_dir / contract["root"]
    if not raw_root.is_dir() or raw_root.is_symlink():
        raise PublicRawLayoutError("data/public_raw must be a real directory")

    sources = sync_source_map(registry)
    if sources["chatgpt"]["archive_path"] != SOURCE_ROOTS["chatgpt"]:
        raise PublicRawLayoutError("chatgpt registry archive_path drifted from the layout")
    if sources["codex"]["archive_path"] != SOURCE_ROOTS["codex"]:
        raise PublicRawLayoutError("codex registry archive_path drifted from the layout")
    if sources["generic_agent_template"]["archive_path"] != SOURCE_ROOTS["generic_agent_template"]:
        raise PublicRawLayoutError("generic-agent template archive_path drifted from the layout")

    registered_agents = _registered_agent_ids(registry)
    required_source_dirs = {"chatgpt", "codex"}
    active_source_ids = {"chatgpt", "codex"}
    allowed_dirs = {"chatgpt", "codex", "agents", *contract["shallow_layout"]["allowed_static_subdirectories"]}
    for source_id in registered_agents:
        source = sources[source_id]
        expected = f"data/public_raw/agents/{source_id}"
        if source["archive_path"] != expected:
            raise PublicRawLayoutError(f"registered agent archive_path is not source-partitioned: {source_id}")
        allowed_dirs.add(f"agents/{source_id}")
        if source["status"] == "active_manual":
            required_source_dirs.add(f"agents/{source_id}")
            active_source_ids.add(source_id)

    actual_dirs: set[str] = set()
    actual_files: set[str] = set()
    source_file_counts: dict[str, int] = {"chatgpt": 0, "codex": 0, **{item: 0 for item in registered_agents}}
    control_file_count = 0
    for current, dirnames, filenames in os.walk(raw_root, followlinks=False):
        current_path = Path(current)
        for name in dirnames + filenames:
            entry = current_path / name
            if entry.is_symlink():
                raise PublicRawLayoutError(f"symlink is forbidden in public raw: {entry.relative_to(database_dir)}")
        if current_path != raw_root:
            relative_dir = current_path.relative_to(raw_root).as_posix()
            actual_dirs.add(relative_dir)
            if len(PurePosixPath(relative_dir).parts) > contract["shallow_layout"]["max_directory_depth_below_root"]:
                raise PublicRawLayoutError(f"public-raw directory exceeds shallow depth: {relative_dir}")
            if relative_dir not in allowed_dirs:
                raise PublicRawLayoutError(f"public-raw directory is not registered: {relative_dir}")
        for name in filenames:
            file_path = current_path / name
            if not file_path.is_file():
                raise PublicRawLayoutError(f"public-raw entry is not a regular file: {file_path.relative_to(database_dir)}")
            relative = file_path.relative_to(raw_root)
            source_id = classify_public_raw_path(relative, registered_agents)
            repo_relative = file_path.relative_to(database_dir).as_posix()
            actual_files.add(repo_relative)
            if source_id == "control":
                control_file_count += 1
            else:
                source_file_counts[source_id] += 1

    missing_dirs = sorted(required_source_dirs - actual_dirs)
    if missing_dirs:
        raise PublicRawLayoutError(f"active source directories are missing: {missing_dirs}")
    if control_file_count != len(CONTROL_FILES):
        raise PublicRawLayoutError("public-raw control README is missing or duplicated")
    empty_active_sources = sorted(source_id for source_id in active_source_ids if source_file_counts[source_id] == 0)
    if empty_active_sources:
        raise PublicRawLayoutError(f"active source partitions are empty: {empty_active_sources}")

    tracked_file_count: int | None = None
    if enforce_git_tracking:
        tracked_files = _tracked_public_raw_files(database_dir)
        untracked = sorted(actual_files - tracked_files)
        missing = sorted(tracked_files - actual_files)
        if untracked or missing:
            raise PublicRawLayoutError(
                f"public-raw Git recovery mismatch: untracked={untracked[:5]}, missing={missing[:5]}"
            )
        tracked_file_count = len(tracked_files)

    return {
        "root": contract["root"],
        "directory_count": len(actual_dirs),
        "file_count": len(actual_files),
        "control_file_count": control_file_count,
        "raw_file_count": sum(source_file_counts.values()),
        "source_file_counts": dict(sorted(source_file_counts.items())),
        "tracked_file_count": tracked_file_count,
        "max_directory_depth_below_root": contract["shallow_layout"]["max_directory_depth_below_root"],
        "registered_agent_ids": sorted(registered_agents),
    }


def _resolve_vite_config(database_dir: Path, app_relative: str) -> dict[str, Any]:
    script = (
        'import { resolveConfig } from "vite"; '
        'const c=await resolveConfig({root:process.cwd()},"build"); '
        'console.log(JSON.stringify({root:c.root,publicDir:c.publicDir,outDir:c.build.outDir,allow:c.server.fs.allow}));'
    )
    result = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=database_dir / app_relative,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PublicRawLayoutError(f"cannot resolve Vite config: {result.stderr.strip()[-1000:]}")
    try:
        payload = json.loads(result.stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise PublicRawLayoutError("Vite resolved config did not return JSON") from exc
    return _mapping(payload, "vite_resolved_config")


def _audit_built_dist(out_dir: Path) -> int:
    if not out_dir.is_dir() or out_dir.is_symlink():
        raise PublicRawLayoutError("built dist is required for public-raw isolation audit")
    build_files: list[Path] = []
    for current, dirnames, filenames in os.walk(out_dir, followlinks=False):
        current_path = Path(current)
        for name in dirnames + filenames:
            entry = current_path / name
            if entry.is_symlink():
                raise PublicRawLayoutError(
                    f"symlink is forbidden in frontend build: {entry.relative_to(out_dir)}"
                )
        for name in filenames:
            path = current_path / name
            if not path.is_file():
                raise PublicRawLayoutError(
                    f"frontend build entry is not a regular file: {path.relative_to(out_dir)}"
                )
            build_files.append(path)
    leaked_paths = [
        path.relative_to(out_dir).as_posix()
        for path in build_files
        if "public_raw" in path.relative_to(out_dir).parts
    ]
    if leaked_paths:
        raise PublicRawLayoutError(f"frontend build contains public_raw paths: {leaked_paths[:5]}")
    return len(build_files)


def _audit_frontend_isolation(
    database_dir: Path,
    contract: dict[str, Any],
    *,
    require_built_dist: bool,
) -> dict[str, Any]:
    isolation = contract["isolation"]
    raw_root = (database_dir / contract["root"]).resolve()
    app_dir = (database_dir / isolation["frontend_app"]).resolve()
    expected_public_dir = (database_dir / isolation["expected_vite_public_dir"]).resolve()
    expected_build_output = (database_dir / isolation["build_output"]).resolve()
    resolved = _resolve_vite_config(database_dir, isolation["frontend_app"])
    public_dir = Path(str(resolved.get("publicDir") or "")).resolve()
    out_dir_value = Path(str(resolved.get("outDir") or ""))
    out_dir = (app_dir / out_dir_value).resolve() if not out_dir_value.is_absolute() else out_dir_value.resolve()
    allow_paths = [Path(str(path)).resolve() for path in resolved.get("allow") or []]

    for label, path in (
        ("frontend app", app_dir),
        ("Vite publicDir", public_dir),
        ("Vite build output", out_dir),
        *(("Vite server allow", path) for path in allow_paths),
    ):
        if not _is_within(path, database_dir):
            raise PublicRawLayoutError(f"{label} must stay within the database root")
    if public_dir != expected_public_dir:
        raise PublicRawLayoutError(f"Vite publicDir must resolve to {expected_public_dir}")
    if out_dir != expected_build_output:
        raise PublicRawLayoutError(f"Vite build.outDir must resolve to {expected_build_output}")
    if _is_within(raw_root, public_dir) or _is_within(public_dir, raw_root):
        raise PublicRawLayoutError("Vite publicDir overlaps data/public_raw")
    if _is_within(raw_root, out_dir) or _is_within(out_dir, raw_root):
        raise PublicRawLayoutError("Vite build output overlaps data/public_raw")
    if any(_is_within(raw_root, allowed) or _is_within(allowed, raw_root) for allowed in allow_paths):
        raise PublicRawLayoutError("Vite server.fs.allow exposes data/public_raw")

    frontend_raw_references: list[str] = []
    source_root = app_dir / "src"
    for path in sorted(source_root.rglob("*")):
        if path.is_file() and path.suffix in _FRONTEND_SUFFIXES:
            source = path.read_text(encoding="utf-8", errors="ignore")
            if "data/public_raw" in source or "/public_raw/" in source:
                frontend_raw_references.append(path.relative_to(app_dir).as_posix())
    if frontend_raw_references:
        raise PublicRawLayoutError(f"frontend source references public raw: {frontend_raw_references}")

    build_file_count: int | None = None
    if require_built_dist:
        build_file_count = _audit_built_dist(out_dir)

    return {
        "vite_public_dir": public_dir.relative_to(database_dir).as_posix(),
        "vite_server_allow": [path.relative_to(database_dir).as_posix() for path in allow_paths],
        "build_output": out_dir.relative_to(database_dir).as_posix(),
        "built_dist_required": require_built_dist,
        "build_file_count": build_file_count,
        "frontend_raw_reference_count": 0,
    }


def _route_sources(payload: dict[str, Any]) -> list[str]:
    sources = [str(value) for value in payload.get("read_order") or []]
    for row in payload.get("context_used") or []:
        if isinstance(row, dict) and row.get("source"):
            sources.append(str(row["source"]))
    for row in payload.get("conditional_context") or []:
        if isinstance(row, dict) and row.get("source"):
            sources.append(str(row["source"]))
    for row in payload.get("conditional_resources") or []:
        if isinstance(row, dict) and row.get("path"):
            sources.append(str(row["path"]))
    return sorted(set(sources))


def _audit_default_codex_route(database_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    intent = contract["isolation"]["default_codex_intent"]
    result = subprocess.run(
        [sys.executable, "scripts/route_agent_resources.py", "--database-dir", ".", "--intent", intent],
        cwd=database_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise PublicRawLayoutError(f"default Codex route failed: {result.stderr.strip()[-1000:]}")
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise PublicRawLayoutError("default Codex route did not return JSON") from exc
    if payload.get("status") != "PASS" or payload.get("intent") != intent:
        raise PublicRawLayoutError("default Codex route identity is invalid")
    route_sources = _route_sources(payload)
    forbidden = contract["isolation"]["forbidden_default_context_prefixes"]
    leaked = [
        source
        for source in route_sources
        if any(source == prefix.rstrip("/") or source.startswith(prefix) for prefix in forbidden)
    ]
    if leaked:
        raise PublicRawLayoutError(f"default Codex route reads public raw: {leaked}")
    return {
        "intent": intent,
        "route_sources": route_sources,
        "public_raw_source_count": 0,
    }


def audit_public_raw_layout(
    database_dir: Path,
    *,
    contract_path: Path | None = None,
    registry: dict[str, Any] | None = None,
    verify_runtime_isolation: bool = True,
    require_built_dist: bool = False,
    enforce_git_tracking: bool | None = None,
) -> dict[str, Any]:
    database_dir = database_dir.resolve()
    contract = load_layout_contract(database_dir, contract_path)
    registry = registry or load_source_registry(database_dir)
    if enforce_git_tracking is None:
        enforce_git_tracking = bool(contract["recovery_layout"]["tracked_files_required"])
    layout = _audit_tree(
        database_dir,
        contract,
        registry,
        enforce_git_tracking=enforce_git_tracking,
    )
    isolation: dict[str, Any] = {"verified": False}
    if verify_runtime_isolation:
        isolation = {
            "verified": True,
            "frontend": _audit_frontend_isolation(
                database_dir,
                contract,
                require_built_dist=require_built_dist,
            ),
            "default_codex_route": _audit_default_codex_route(database_dir, contract),
        }
    return {
        "status": "PASS",
        "command": "audit",
        "check": "public-raw-layout",
        "schema_version": LAYOUT_SCHEMA_VERSION,
        "task_id": TASK_ID,
        "layout": layout,
        "isolation": isolation,
        "raw_content_read": False,
        "raw_mutation": False,
        "remote_push": False,
    }


def run_public_raw_layout_audit(args: Any) -> int:
    try:
        result = audit_public_raw_layout(
            args.database_dir,
            verify_runtime_isolation=True,
            require_built_dist=bool(getattr(args, "require_built_dist", False)),
        )
    except (PublicRawLayoutError, SourceRegistryError) as exc:
        database_dir = Path(args.database_dir).resolve()
        if isinstance(exc, SourceRegistryError):
            reason = "canonical source registry is invalid for the public-raw layout"
        else:
            reason = str(exc).replace(str(database_dir), ".")
        result = {
            "status": "FAIL_CLOSED",
            "command": "audit",
            "check": "public-raw-layout",
            "schema_version": LAYOUT_SCHEMA_VERSION,
            "task_id": TASK_ID,
            "reason": reason,
            "dependency": REGISTRY_PATH.as_posix() if isinstance(exc, SourceRegistryError) else LAYOUT_CONFIG_PATH.as_posix(),
            "raw_content_read": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = (
    "CONTROL_FILES",
    "ISOLATION",
    "LAYOUT_CONFIG_PATH",
    "LAYOUT_SCHEMA_VERSION",
    "PublicRawLayoutError",
    "RAW_ROOT",
    "RECOVERY_LAYOUT",
    "SHALLOW_LAYOUT",
    "SOURCE_ROOTS",
    "TASK_ID",
    "audit_public_raw_layout",
    "classify_public_raw_path",
    "load_layout_contract",
    "run_public_raw_layout_audit",
    "validate_layout_contract",
)
