from __future__ import annotations

import fnmatch
import json
import os
import re
import shutil
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from .hashing import sha256_file
from .models import InventoryRecord, SourceCoverage, SourceSpec, SourceState
from .sqlite_snapshot import create_consistent_snapshot


# Standalone credentials are configuration, not product memory. Embedded text inside an
# in-scope conversation is kept byte-for-byte and is not inspected or altered here.
DENY_STANDALONE = re.compile(
    r"(^|/)(\.env($|\.)|[^/]*(token|secret|credential|cookie|password)[^/]*|"
    r"id_(rsa|ed25519)|[^/]*\.(pem|key|p12|pfx))$",
    re.IGNORECASE,
)


class InventoryError(RuntimeError):
    pass


@dataclass(frozen=True)
class ResolvedSource:
    spec: SourceSpec
    roots: tuple[Path, ...]


def load_source_registry(path: Path, env: dict[str, str] | None = None) -> list[ResolvedSource]:
    values = dict(os.environ if env is None else env)
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema_version") != "memory_atlas.source_registry.v1":
        raise InventoryError("来源注册表 schema_version 不匹配")
    resolved: list[ResolvedSource] = []
    seen: set[str] = set()
    for raw in payload.get("sources", []):
        spec = SourceSpec(
            source_id=str(raw["source_id"]),
            label_zh=str(raw["label_zh"]),
            path_template=str(raw.get("path_template", "")),
            kind=str(raw["kind"]),
            required=bool(raw.get("required", False)),
            recursive=bool(raw.get("recursive", True)),
            env_var=raw.get("env_var"),
            include_globs=tuple(raw.get("include_globs", ["**/*"])),
            exclude_globs=tuple(raw.get("exclude_globs", [])),
        )
        if spec.source_id in seen:
            raise InventoryError(f"重复 source_id：{spec.source_id}")
        seen.add(spec.source_id)
        roots: list[Path] = []
        if spec.env_var:
            raw_value = values.get(spec.env_var, "").strip()
            if raw_value:
                roots.extend(Path(item).expanduser() for item in raw_value.split(os.pathsep) if item.strip())
        elif spec.path_template:
            expanded = os.path.expandvars(os.path.expanduser(spec.path_template))
            roots.append(Path(expanded))
        resolved.append(ResolvedSource(spec=spec, roots=tuple(root.resolve() for root in roots)))
    if not resolved:
        raise InventoryError("来源注册表没有任何来源")
    return resolved


def _matches(relative: str, includes: tuple[str, ...], excludes: tuple[str, ...]) -> bool:
    normalized = relative.replace(os.sep, "/")
    def matches(pattern: str) -> bool:
        # In source registries, **/ means zero or more directory levels. Python's
        # fnmatch treats the slash literally, so also test the zero-level form.
        return fnmatch.fnmatch(normalized, pattern) or (
            pattern.startswith("**/") and fnmatch.fnmatch(normalized, pattern[3:])
        )

    included = any(matches(pattern) for pattern in includes)
    excluded = any(matches(pattern) for pattern in excludes)
    return included and not excluded


def _safe_regular_files(root: Path, recursive: bool) -> Iterable[Path]:
    if root.is_file():
        yield root
        return
    if not root.is_dir():
        return
    iterator = root.rglob("*") if recursive else root.glob("*")
    root_real = root.resolve()
    for candidate in iterator:
        try:
            if candidate.is_symlink():
                continue
            resolved = candidate.resolve()
            resolved.relative_to(root_real)
            mode = resolved.stat().st_mode
            if stat.S_ISREG(mode):
                yield resolved
        except (OSError, ValueError):
            continue


def _materialize_record(
    source: ResolvedSource,
    root: Path,
    path: Path,
    snapshot_dir: Path,
) -> InventoryRecord:
    relative = path.name if root.is_file() else path.relative_to(root).as_posix()
    if DENY_STANDALONE.search(relative):
        raise InventoryError(f"来源注册表包含独立凭据文件，拒绝采集：{source.spec.source_id}/{relative}")
    stat_value = path.stat()
    materialized = path
    snapshot_created = False
    if source.spec.kind == "sqlite":
        original_sha = sha256_file(path)
        destination = snapshot_dir / source.spec.source_id / relative
        destination = destination.with_suffix(destination.suffix + ".snapshot.sqlite3")
        snapshot_sha, _ = create_consistent_snapshot(path, destination)
        materialized = destination
        digest = snapshot_sha
        snapshot_created = True
    else:
        # Codex JSONL/session files are live append-only sources. Materialize the
        # bytes observed during discovery into the run-scoped protected work area
        # so later upload, readback, and normalization all use one immutable copy.
        destination = snapshot_dir / source.spec.source_id / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_suffix(destination.suffix + ".partial")
        shutil.copyfile(path, temporary)
        temporary.replace(destination)
        materialized = destination
        digest = sha256_file(materialized)
        original_sha = digest
        snapshot_created = True
    return InventoryRecord(
        source_id=source.spec.source_id,
        source_root=str(root),
        relative_path=relative,
        materialized_path=str(materialized),
        kind=source.spec.kind,
        size_bytes=materialized.stat().st_size,
        mtime_ns=stat_value.st_mtime_ns,
        sha256=digest,
        original_sha256=original_sha,
        snapshot_created=snapshot_created,
    )


def discover_inventory(
    registry: list[ResolvedSource],
    snapshot_dir: Path,
) -> tuple[list[InventoryRecord], list[SourceCoverage]]:
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    records: list[InventoryRecord] = []
    coverages: list[SourceCoverage] = []
    for source in registry:
        source_records: list[InventoryRecord] = []
        if not source.roots:
            state = SourceState.MISSING_REQUIRED if source.spec.required else SourceState.MISSING_OPTIONAL
            coverages.append(SourceCoverage(
                source_id=source.spec.source_id,
                label_zh=source.spec.label_zh,
                required=source.spec.required,
                state=state,
                message_zh="没有配置来源路径",
            ))
            continue
        visible_root = False
        failures: list[str] = []
        for root in source.roots:
            if not root.exists():
                continue
            visible_root = True
            for path in _safe_regular_files(root, source.spec.recursive):
                relative = path.name if root.is_file() else path.relative_to(root).as_posix()
                if not _matches(relative, source.spec.include_globs, source.spec.exclude_globs):
                    continue
                try:
                    source_records.append(_materialize_record(source, root, path, snapshot_dir))
                except (OSError, InventoryError) as exc:
                    failures.append(str(exc))
        if failures:
            state = SourceState.UNREADABLE
            message = "；".join(failures[:3])
        elif not visible_root:
            state = SourceState.MISSING_REQUIRED if source.spec.required else SourceState.MISSING_OPTIONAL
            message = "路径不存在或当前不可见"
        elif not source_records:
            state = SourceState.EMPTY
            message = "来源可见，但没有匹配文件"
        else:
            state = SourceState.READY
            message = "已发现并计算内容哈希"
        coverages.append(SourceCoverage(
            source_id=source.spec.source_id,
            label_zh=source.spec.label_zh,
            required=source.spec.required,
            state=state,
            object_count=len(source_records),
            size_bytes=sum(item.size_bytes for item in source_records),
            message_zh=message,
        ))
        records.extend(source_records)
    records.sort(key=lambda item: (item.source_id, item.relative_path))
    return records, coverages


def cleanup_snapshots(snapshot_dir: Path) -> None:
    if snapshot_dir.exists():
        shutil.rmtree(snapshot_dir)
