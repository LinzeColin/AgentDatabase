"""S06-P3-T1 default search, routing, CI and frontend raw isolation."""

from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any


CONFIG_PATH = Path("config/data_sources/raw_isolation.json")
SCHEMA_VERSION = "memory_atlas.raw_isolation.v1_2_1_s06_p3_t1"
TASK_ID = "S06-P3-T1"
REPOSITORY_TOPOLOGIES = ("codexproject_monorepo", "standalone_openaidatabase")
FORBIDDEN_RAW_ROOTS = ("data/public_raw", "data/raw_archives")
SEARCH_CONTRACT = {
    "tool": "rg",
    "worktree_ignore_file": ".rgignore",
    "database_ignore_file": ".rgignore",
    "required_worktree_patterns": [
        "OpenAIDatabase/data/public_raw/**",
        "OpenAIDatabase/data/raw_archives/**",
    ],
    "required_database_patterns": ["data/public_raw/**", "data/raw_archives/**"],
    "explicit_override": ["rg", "--no-ignore"],
}
CODEX_ROUTING_CONTRACT = {
    "route_config": "config/context_sources/resource_routes.json",
    "route_script": "scripts/route_agent_resources.py",
    "contract_ref_field": "raw_isolation_contract_ref",
    "all_routes_default_excluded": True,
    "explicit_raw_route_ids": [],
}
CI_CONTRACT = {
    "environment_marker": "MEMORY_ATLAS_RAW_ISOLATED",
    "environment_value": "1",
    "root_workflow": ".github/workflows/openai-database-ci.yml",
    "project_workflow": ".github/workflows/ci.yml",
    "root_sparse_checkout_patterns": [
        "/*",
        "!/*/",
        "/.github/",
        "/governance/",
        "/scripts/",
        "/OpenAIDatabase/",
        "!/OpenAIDatabase/data/public_raw/",
        "!/OpenAIDatabase/data/raw_archives/",
    ],
    "project_sparse_checkout_patterns": [
        "/*",
        "!/data/public_raw/",
        "!/data/raw_archives/",
    ],
    "audit_command": "python3 scripts/atlasctl.py audit --check raw-isolation --ci-checkout",
}
FRONTEND_CONTRACT = {
    "app": "apps/memory-atlas",
    "vite_config": "apps/memory-atlas/vite.config.ts",
    "expected_public_dir": "data/derived/visualization",
    "build_output": "apps/memory-atlas/dist",
    "guard_plugin": "memory-atlas-raw-isolation",
    "server_fs_strict": True,
    "forbidden_dist_path_components": ["public_raw", "raw_archives"],
}
BOUNDARIES = {
    "raw_content_read_by_audit": False,
    "raw_mutation": False,
    "remote_push": False,
    "explicit_raw_tools_remain_available": True,
    "push_size_guard_task": "S06-P3-T2",
    "raw_fixture_contract_task": "S06-P3-T3",
}
_CONTRACT_KEYS = {
    "schema_version",
    "task_id",
    "repository_topologies",
    "forbidden_raw_roots",
    "search",
    "codex_routing",
    "ci",
    "frontend",
    "boundaries",
}
_MAX_CONFIG_BYTES = 64 * 1024
_MAX_WORKFLOW_BYTES = 256 * 1024
_MAX_DIST_FILE_BYTES = 64 * 1024 * 1024
_RAW_LEDGER_CONFIG = Path("config/data_sources/raw_ledger.json")


class RawIsolationError(ValueError):
    """Raised when default raw isolation is missing, unsafe or unverifiable."""


def _read_regular_bytes(path: Path, *, limit: int, label: str) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RawIsolationError(f"cannot read {label}") from exc
    try:
        metadata = os.fstat(descriptor)
        if not stat.S_ISREG(metadata.st_mode):
            raise RawIsolationError(f"{label} must be a regular file")
        if metadata.st_size > limit:
            raise RawIsolationError(f"{label} exceeds the size limit")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            descriptor = -1
            content = handle.read(limit + 1)
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    if len(content) > limit:
        raise RawIsolationError(f"{label} exceeds the size limit")
    return content


def _read_text(path: Path, *, limit: int, label: str) -> str:
    try:
        return _read_regular_bytes(path, limit=limit, label=label).decode("utf-8")
    except UnicodeDecodeError as exc:
        raise RawIsolationError(f"{label} must be UTF-8") from exc


def _read_json(path: Path, *, label: str) -> dict[str, Any]:
    try:
        payload = json.loads(_read_text(path, limit=_MAX_CONFIG_BYTES, label=label))
    except json.JSONDecodeError as exc:
        raise RawIsolationError(f"{label} must be valid JSON") from exc
    if not isinstance(payload, dict):
        raise RawIsolationError(f"{label} must be an object")
    return payload


def _safe_relative_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value or value != value.strip() or "\\" in value:
        raise RawIsolationError(f"{field} must be a canonical repository-relative path")
    posix_path = PurePosixPath(value)
    windows_path = PureWindowsPath(value)
    if (
        posix_path.is_absolute()
        or windows_path.is_absolute()
        or bool(windows_path.drive)
        or value.startswith("//")
        or any(part in {"", ".", ".."} for part in posix_path.parts)
    ):
        raise RawIsolationError(f"{field} must be a safe repository-relative path")
    return value


def validate_raw_isolation_contract(payload: Any) -> dict[str, Any]:
    if not isinstance(payload, dict) or set(payload) != _CONTRACT_KEYS:
        raise RawIsolationError("raw isolation keys do not match the canonical contract")
    if payload.get("schema_version") != SCHEMA_VERSION or payload.get("task_id") != TASK_ID:
        raise RawIsolationError("raw isolation identity is unsupported")
    if payload.get("repository_topologies") != list(REPOSITORY_TOPOLOGIES):
        raise RawIsolationError("repository topology contract drifted")
    if payload.get("forbidden_raw_roots") != list(FORBIDDEN_RAW_ROOTS):
        raise RawIsolationError("forbidden raw roots drifted")
    for index, root in enumerate(payload["forbidden_raw_roots"]):
        _safe_relative_path(root, f"forbidden_raw_roots[{index}]")
    if payload.get("search") != SEARCH_CONTRACT:
        raise RawIsolationError("search isolation contract drifted")
    if payload.get("codex_routing") != CODEX_ROUTING_CONTRACT:
        raise RawIsolationError("Codex routing isolation contract drifted")
    if payload.get("ci") != CI_CONTRACT:
        raise RawIsolationError("CI isolation contract drifted")
    if payload.get("frontend") != FRONTEND_CONTRACT:
        raise RawIsolationError("frontend isolation contract drifted")
    if payload.get("boundaries") != BOUNDARIES:
        raise RawIsolationError("raw isolation boundaries drifted")
    return payload


def load_raw_isolation_contract(database_dir: Path, path: Path | None = None) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    target = path or database_dir / CONFIG_PATH
    return validate_raw_isolation_contract(_read_json(target, label=CONFIG_PATH.as_posix()))


def _normalized_route_path(value: Any, field: str) -> str:
    path = _safe_relative_path(value, field)
    return path.rstrip("/")


def route_path_is_forbidden(path: str, contract: dict[str, Any]) -> bool:
    normalized = _normalized_route_path(path, "route path")
    return any(normalized == root or normalized.startswith(f"{root}/") for root in contract["forbidden_raw_roots"])


def validate_route_config_isolation(route_config: Any, contract: dict[str, Any]) -> tuple[str, ...]:
    if not isinstance(route_config, dict):
        raise RawIsolationError("resource route config must be an object")
    field = contract["codex_routing"]["contract_ref_field"]
    if route_config.get(field) != CONFIG_PATH.as_posix():
        raise RawIsolationError("resource routes do not reference the canonical raw isolation contract")
    routes = route_config.get("routes")
    if not isinstance(routes, list) or not routes:
        raise RawIsolationError("resource route config must contain routes")
    route_ids: list[str] = []
    for index, route in enumerate(routes):
        if not isinstance(route, dict):
            raise RawIsolationError(f"routes[{index}] must be an object")
        intent = route.get("intent")
        if not isinstance(intent, str) or not intent or intent in route_ids:
            raise RawIsolationError(f"routes[{index}].intent is invalid")
        route_ids.append(intent)
        paths: list[tuple[str, Any]] = []
        read_order = route.get("read_order")
        if not isinstance(read_order, list):
            raise RawIsolationError(f"route {intent} read_order must be a list")
        paths.extend((f"route {intent} read_order[{item_index}]", value) for item_index, value in enumerate(read_order))
        conditional = route.get("conditional_resources", [])
        if not isinstance(conditional, list):
            raise RawIsolationError(f"route {intent} conditional_resources must be a list")
        for item_index, row in enumerate(conditional):
            if not isinstance(row, dict) or "path" not in row:
                raise RawIsolationError(f"route {intent} conditional_resources[{item_index}] is invalid")
            paths.append((f"route {intent} conditional_resources[{item_index}].path", row["path"]))
        for path_field, value in paths:
            normalized = _normalized_route_path(value, path_field)
            if route_path_is_forbidden(normalized, contract):
                raise RawIsolationError(f"Codex route exposes a forbidden raw root: {intent}:{normalized}")
    return tuple(route_ids)


def _run(command: list[str], *, cwd: Path, label: str, timeout: int = 120) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise RawIsolationError(f"cannot run {label}") from exc
    if result.returncode != 0:
        detail = (result.stderr or result.stdout).strip()[-800:]
        raise RawIsolationError(f"{label} failed: {detail}")
    return result


def _forbidden_worktree_path(path: str) -> bool:
    normalized = path.removeprefix("./").rstrip("/")
    return any(
        normalized == f"OpenAIDatabase/{root}" or normalized.startswith(f"OpenAIDatabase/{root}/")
        for root in FORBIDDEN_RAW_ROOTS
    )


def _forbidden_database_path(path: str) -> bool:
    normalized = path.removeprefix("./").rstrip("/")
    return any(normalized == root or normalized.startswith(f"{root}/") for root in FORBIDDEN_RAW_ROOTS)


def _effective_ignore_patterns(path: Path, label: str) -> tuple[str, ...]:
    lines = _read_text(path, limit=_MAX_CONFIG_BYTES, label=label).splitlines()
    return tuple(line.strip() for line in lines if line.strip() and not line.lstrip().startswith("#"))


def _repository_topology(database_dir: Path) -> tuple[str, Path]:
    worktree = database_dir.parent
    if (
        database_dir.name == "OpenAIDatabase"
        and (worktree / CI_CONTRACT["root_workflow"]).is_file()
        and (worktree / SEARCH_CONTRACT["worktree_ignore_file"]).is_file()
    ):
        return "codexproject_monorepo", worktree
    if (
        (database_dir / CI_CONTRACT["project_workflow"]).is_file()
        and (database_dir / SEARCH_CONTRACT["database_ignore_file"]).is_file()
    ):
        return "standalone_openaidatabase", database_dir
    raise RawIsolationError("repository topology is neither canonical monorepo nor standalone OpenAIDatabase")


def _git_tracked_raw_paths(database_dir: Path) -> set[str]:
    result = _run(
        ["git", "ls-files", "--", *FORBIDDEN_RAW_ROOTS],
        cwd=database_dir,
        label="tracked raw path inventory",
    )
    paths = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    if not paths:
        raise RawIsolationError("tracked raw path inventory is empty")
    return paths


def _audit_search(database_dir: Path, contract: dict[str, Any], *, ci_checkout: bool) -> dict[str, Any]:
    topology, worktree = _repository_topology(database_dir)
    search = contract["search"]
    database_patterns = _effective_ignore_patterns(
        database_dir / search["database_ignore_file"], "OpenAIDatabase .rgignore"
    )
    if not set(search["required_database_patterns"]).issubset(database_patterns):
        raise RawIsolationError("OpenAIDatabase .rgignore does not exclude both raw roots")

    worktree_raw_path_count: int | None = None
    if topology == "codexproject_monorepo":
        worktree_patterns = _effective_ignore_patterns(
            worktree / search["worktree_ignore_file"], "worktree .rgignore"
        )
        if not set(search["required_worktree_patterns"]).issubset(worktree_patterns):
            raise RawIsolationError("worktree .rgignore does not exclude both raw roots")
        worktree_result = _run(
            ["rg", "--files", "OpenAIDatabase"], cwd=worktree, label="worktree default search"
        )
        worktree_leaks = [line for line in worktree_result.stdout.splitlines() if _forbidden_worktree_path(line)]
        if worktree_leaks:
            raise RawIsolationError("default worktree ripgrep search still enumerates raw paths")
        worktree_raw_path_count = 0
    database_result = _run(["rg", "--files", "."], cwd=database_dir, label="database default search")
    database_leaks = [line for line in database_result.stdout.splitlines() if _forbidden_database_path(line)]
    if database_leaks:
        raise RawIsolationError("default database ripgrep search still enumerates raw paths")

    tracked_paths = _git_tracked_raw_paths(database_dir)
    explicit_paths: set[str] = set()
    if ci_checkout:
        marker = contract["ci"]["environment_marker"]
        if os.environ.get(marker) != contract["ci"]["environment_value"]:
            raise RawIsolationError("CI raw-isolation environment marker is missing")
        present = [root for root in FORBIDDEN_RAW_ROOTS if os.path.lexists(database_dir / root)]
        if present:
            raise RawIsolationError(f"CI sparse checkout materialized raw roots: {present}")
    else:
        for root in FORBIDDEN_RAW_ROOTS:
            path = database_dir / root
            if not path.is_dir() or path.is_symlink():
                raise RawIsolationError(f"explicit raw root is unavailable: {root}")
        result = _run(
            [*search["explicit_override"], "--files", *FORBIDDEN_RAW_ROOTS],
            cwd=database_dir,
            label="explicit raw search",
        )
        explicit_paths = {line.strip() for line in result.stdout.splitlines() if line.strip()}
        if explicit_paths != tracked_paths:
            raise RawIsolationError("explicit raw search does not match the tracked raw inventory")

    return {
        "tool": search["tool"],
        "repository_topology": topology,
        "default_worktree_raw_path_count": worktree_raw_path_count,
        "default_database_raw_path_count": 0,
        "tracked_raw_path_count": len(tracked_paths),
        "explicit_raw_path_count": len(explicit_paths),
        "ci_checkout": ci_checkout,
        "explicit_override": " ".join(search["explicit_override"]),
    }


def _audit_codex_routing(database_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    routing = contract["codex_routing"]
    route_config = _read_json(database_dir / routing["route_config"], label="resource route config")
    route_ids = validate_route_config_isolation(route_config, contract)
    for route_id in route_ids:
        result = _run(
            [sys.executable, routing["route_script"], "--database-dir", ".", "--intent", route_id],
            cwd=database_dir,
            label=f"Codex route {route_id}",
        )
        try:
            payload = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            raise RawIsolationError(f"Codex route {route_id} did not return JSON") from exc
        isolation = payload.get("raw_isolation") if isinstance(payload, dict) else None
        if (
            payload.get("status") != "PASS"
            or not isinstance(isolation, dict)
            or isolation.get("enforced") is not True
            or isolation.get("contract_ref") != CONFIG_PATH.as_posix()
            or isolation.get("forbidden_prefixes") != list(FORBIDDEN_RAW_ROOTS)
        ):
            raise RawIsolationError(f"Codex route {route_id} did not enforce raw isolation")
    return {
        "route_count": len(route_ids),
        "route_ids": list(route_ids),
        "forbidden_route_path_count": 0,
        "runtime_enforced": True,
    }


def _extract_sparse_checkout_patterns(workflow: str, label: str) -> tuple[str, ...]:
    lines = workflow.splitlines()
    starts = [index for index, line in enumerate(lines) if line.strip() == "sparse-checkout: |"]
    if len(starts) != 1:
        raise RawIsolationError(f"{label} must contain one sparse-checkout block")
    start = starts[0]
    indentation = len(lines[start]) - len(lines[start].lstrip())
    patterns: list[str] = []
    for line in lines[start + 1 :]:
        if not line.strip():
            continue
        current = len(line) - len(line.lstrip())
        if current <= indentation:
            break
        patterns.append(line.strip())
    if not patterns:
        raise RawIsolationError(f"{label} sparse-checkout block is empty")
    return tuple(patterns)


def _audit_workflow(
    path: Path,
    *,
    display_path: str,
    patterns: list[str],
    contract: dict[str, Any],
    label: str,
) -> dict[str, Any]:
    workflow = _read_text(path, limit=_MAX_WORKFLOW_BYTES, label=label)
    if _extract_sparse_checkout_patterns(workflow, label) != tuple(patterns):
        raise RawIsolationError(f"{label} sparse-checkout patterns drifted")
    if "sparse-checkout-cone-mode: false" not in workflow:
        raise RawIsolationError(f"{label} must use non-cone sparse checkout")
    marker = contract["ci"]["environment_marker"]
    value = contract["ci"]["environment_value"]
    if f'{marker}: "{value}"' not in workflow:
        raise RawIsolationError(f"{label} does not set the raw-isolation environment marker")
    if contract["ci"]["audit_command"] not in workflow:
        raise RawIsolationError(f"{label} does not execute the raw-isolation audit")
    return {
        "path": display_path,
        "sparse_pattern_count": len(patterns),
        "non_cone": True,
        "runtime_audit": True,
    }


def _audit_ci(database_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    topology, worktree = _repository_topology(database_dir)
    ci = contract["ci"]
    root = None
    if topology == "codexproject_monorepo":
        root = _audit_workflow(
            worktree / ci["root_workflow"],
            display_path=ci["root_workflow"],
            patterns=ci["root_sparse_checkout_patterns"],
            contract=contract,
            label="root OpenAIDatabase CI workflow",
        )
    project = _audit_workflow(
        database_dir / ci["project_workflow"],
        display_path=ci["project_workflow"],
        patterns=ci["project_sparse_checkout_patterns"],
        contract=contract,
        label="project recovery CI workflow",
    )
    return {"repository_topology": topology, "root_workflow": root, "project_workflow": project}


def _is_within(path: Path, parent: Path) -> bool:
    return path == parent or parent in path.parents


def _resolve_frontend_config(database_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    frontend = contract["frontend"]
    app_dir = database_dir / frontend["app"]
    script = """
import { resolveConfig } from "vite";
const config = await resolveConfig({ root: process.cwd() }, "build");
const guard = config.plugins.find((plugin) => plugin.name === "memory-atlas-raw-isolation");
const probes = [];
for (const value of [
  "../../data/public_raw/probe.json",
  "../../data/raw_archives/probe.part",
  "src/main.tsx",
  "../../data/derived/visualization/memory_atlas.json",
]) {
  const absolute = new URL(value, import.meta.url).pathname;
  let blocked = false;
  try {
    guard?.api?.assertPath(absolute);
  } catch {
    blocked = true;
  }
  probes.push({ value, blocked });
}
console.log(JSON.stringify({
  publicDir: config.publicDir,
  outDir: config.build.outDir,
  allow: config.server.fs.allow,
  strict: config.server.fs.strict,
  pluginNames: config.plugins.map((plugin) => plugin.name),
  guardApi: Boolean(guard?.api?.assertPath),
  probes,
}));
"""
    result = _run(
        ["node", "--input-type=module", "-e", script],
        cwd=app_dir,
        label="resolved Vite raw-isolation config",
    )
    try:
        payload = json.loads(result.stdout.splitlines()[-1])
    except (IndexError, json.JSONDecodeError) as exc:
        raise RawIsolationError("resolved Vite raw-isolation config did not return JSON") from exc
    if not isinstance(payload, dict):
        raise RawIsolationError("resolved Vite raw-isolation config must be an object")
    return payload


def _load_raw_ledger_hashes(database_dir: Path) -> set[str]:
    config = _read_json(database_dir / _RAW_LEDGER_CONFIG, label="raw ledger config")
    ledger = config.get("ledger")
    if not isinstance(ledger, dict):
        raise RawIsolationError("raw ledger config is missing ledger")
    relative = _safe_relative_path(ledger.get("path"), "raw ledger path")
    lines = _read_text(database_dir / relative, limit=4 * 1024 * 1024, label="raw hash ledger").splitlines()
    hashes: set[str] = set()
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RawIsolationError(f"raw hash ledger line {line_number} is invalid") from exc
        value = row.get("sha256") if isinstance(row, dict) else None
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
            raise RawIsolationError(f"raw hash ledger line {line_number} has an invalid SHA-256")
        hashes.add(value)
    if not hashes:
        raise RawIsolationError("raw hash ledger is empty")
    return hashes


def _audit_dist(database_dir: Path, contract: dict[str, Any], out_dir: Path) -> dict[str, Any]:
    if not out_dir.is_dir() or out_dir.is_symlink():
        raise RawIsolationError("frontend dist is required for raw-isolation audit")
    forbidden_path_components = set(contract["frontend"]["forbidden_dist_path_components"])
    raw_hashes = _load_raw_ledger_hashes(database_dir)
    file_count = 0
    total_bytes = 0
    for current, dirnames, filenames in os.walk(out_dir, followlinks=False):
        current_path = Path(current)
        for name in dirnames + filenames:
            if (current_path / name).is_symlink():
                raise RawIsolationError("frontend dist contains a symlink")
        for name in filenames:
            path = current_path / name
            relative = path.relative_to(out_dir).as_posix()
            content = _read_regular_bytes(
                path,
                limit=_MAX_DIST_FILE_BYTES,
                label=f"frontend dist file {relative}",
            )
            if forbidden_path_components.intersection(Path(relative).parts):
                raise RawIsolationError(f"frontend dist contains a raw path component: {relative}")
            if hashlib.sha256(content).hexdigest() in raw_hashes:
                raise RawIsolationError(f"frontend dist contains a byte-identical public raw file: {relative}")
            file_count += 1
            total_bytes += len(content)
    if file_count == 0:
        raise RawIsolationError("frontend dist is empty")
    return {
        "file_count": file_count,
        "total_bytes": total_bytes,
        "raw_ledger_hash_count": len(raw_hashes),
        "raw_hash_collision_count": 0,
        "forbidden_path_component_count": 0,
    }


def _audit_frontend(
    database_dir: Path,
    contract: dict[str, Any],
    *,
    require_built_dist: bool,
) -> dict[str, Any]:
    frontend = contract["frontend"]
    app_dir = (database_dir / frontend["app"]).resolve()
    expected_public_dir = (database_dir / frontend["expected_public_dir"]).resolve()
    expected_out_dir = (database_dir / frontend["build_output"]).resolve()
    raw_roots = [(database_dir / root).resolve() for root in FORBIDDEN_RAW_ROOTS]
    resolved = _resolve_frontend_config(database_dir, contract)
    public_dir = Path(str(resolved.get("publicDir") or "")).resolve()
    out_value = Path(str(resolved.get("outDir") or ""))
    out_dir = (app_dir / out_value).resolve() if not out_value.is_absolute() else out_value.resolve()
    allow_paths = [Path(str(path)).resolve() for path in resolved.get("allow") or []]
    if public_dir != expected_public_dir or out_dir != expected_out_dir:
        raise RawIsolationError("resolved Vite publicDir or build output drifted")
    if resolved.get("strict") is not frontend["server_fs_strict"]:
        raise RawIsolationError("Vite server.fs.strict must remain enabled")
    if frontend["guard_plugin"] not in (resolved.get("pluginNames") or []) or resolved.get("guardApi") is not True:
        raise RawIsolationError("Vite raw-isolation guard plugin is unavailable")
    probes = resolved.get("probes")
    if not isinstance(probes, list) or [row.get("blocked") for row in probes if isinstance(row, dict)] != [True, True, False, False]:
        raise RawIsolationError("Vite raw-isolation guard probes failed")
    for label, path in (("publicDir", public_dir), ("build output", out_dir), *(("server allow", item) for item in allow_paths)):
        if not _is_within(path, database_dir):
            raise RawIsolationError(f"Vite {label} escapes the database root")
        if any(_is_within(path, root) or _is_within(root, path) for root in raw_roots):
            raise RawIsolationError(f"Vite {label} overlaps a raw root")

    source_references: list[str] = []
    forbidden_text = ("data/public_raw", "data/raw_archives", "/public_raw/", "/raw_archives/")
    for path in sorted((app_dir / "src").rglob("*")):
        if path.is_file() and path.suffix in {".cjs", ".js", ".jsx", ".mjs", ".ts", ".tsx"}:
            source = path.read_text(encoding="utf-8", errors="strict")
            if any(fragment in source for fragment in forbidden_text):
                source_references.append(path.relative_to(app_dir).as_posix())
    if source_references:
        raise RawIsolationError(f"frontend source references raw roots: {source_references}")

    dist = None
    if require_built_dist:
        dist = _audit_dist(database_dir, contract, out_dir)
    return {
        "guard_plugin": frontend["guard_plugin"],
        "guard_probe_count": 4,
        "blocked_raw_probe_count": 2,
        "safe_probe_count": 2,
        "vite_public_dir": public_dir.relative_to(database_dir).as_posix(),
        "vite_server_allow": [path.relative_to(database_dir).as_posix() for path in allow_paths],
        "frontend_raw_reference_count": 0,
        "built_dist_required": require_built_dist,
        "dist": dist,
    }


def audit_raw_isolation(
    database_dir: Path,
    *,
    ci_checkout: bool = False,
    require_built_dist: bool = False,
) -> dict[str, Any]:
    database_dir = Path(database_dir).resolve()
    contract = load_raw_isolation_contract(database_dir)
    return {
        "status": "PASS",
        "command": "audit",
        "check": "raw-isolation",
        "schema_version": SCHEMA_VERSION,
        "task_id": TASK_ID,
        "forbidden_raw_roots": list(FORBIDDEN_RAW_ROOTS),
        "search": _audit_search(database_dir, contract, ci_checkout=ci_checkout),
        "codex_routing": _audit_codex_routing(database_dir, contract),
        "ci": _audit_ci(database_dir, contract),
        "frontend": _audit_frontend(
            database_dir,
            contract,
            require_built_dist=require_built_dist,
        ),
        "raw_content_read": False,
        "raw_mutation": False,
        "remote_push": False,
    }


def run_raw_isolation_audit(args: Any) -> int:
    try:
        result = audit_raw_isolation(
            args.database_dir,
            ci_checkout=bool(getattr(args, "ci_checkout", False)),
            require_built_dist=bool(getattr(args, "require_built_dist", False)),
        )
    except RawIsolationError as exc:
        database_dir = Path(args.database_dir).resolve()
        result = {
            "status": "FAIL_CLOSED",
            "command": "audit",
            "check": "raw-isolation",
            "schema_version": SCHEMA_VERSION,
            "task_id": TASK_ID,
            "reason": str(exc).replace(str(database_dir.parent), ".").replace(str(database_dir), "OpenAIDatabase"),
            "raw_content_read": False,
            "raw_mutation": False,
            "remote_push": False,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


__all__ = (
    "CONFIG_PATH",
    "FORBIDDEN_RAW_ROOTS",
    "REPOSITORY_TOPOLOGIES",
    "RawIsolationError",
    "SCHEMA_VERSION",
    "TASK_ID",
    "audit_raw_isolation",
    "load_raw_isolation_contract",
    "route_path_is_forbidden",
    "run_raw_isolation_audit",
    "validate_raw_isolation_contract",
    "validate_route_config_isolation",
)
