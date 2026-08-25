"""Fail-closed Registry namespace reservation and symlink-alias evidence.

This module owns only Auto sync/mirror mechanics.  It never creates or
validates Mechanism-owned source catalogs or Registry snapshots.
"""

from __future__ import annotations

import hashlib
import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Dict, Iterable, List, Mapping, Sequence, Tuple


SOURCE_NAMESPACES = ("agents", "claude", "codex", "codex-system")
SOURCE_CLASSES = {
    "agents": "AGENTS",
    "claude": "CLAUDE",
    "codex": "CODEX",
    "codex-system": "CODEX_SYSTEM",
}
SOURCE_CATALOG_COMPONENT = "_catalog"
GLOBAL_REGISTRY_NAMESPACE = "_global"
REGISTRY_DELIVERY_BACKUP_COMPONENT = "_delivery-backups"
HISTORICAL_SOURCE_MATERIAL_GIT_OBJECT = (
    "sha1:44a38890ec38ceb24ccae1ec6f5b1fc8e93aefa1"
)
HISTORICAL_SOURCE_SKILL_COUNTS = {
    "agents": 24,
    "claude": 3,
    "codex": 56,
    "codex-system": 6,
}
HISTORICAL_SOURCE_SKILL_COUNT = 89

POLICY_EXCLUDED_DIRECTORY_COMPONENTS = {
    ".git",
    ".hg",
    ".mypy_cache",
    ".pytest_cache",
    ".svn",
    ".venv",
    "__pycache__",
    "node_modules",
}
POLICY_EXCLUDED_FILES = {".DS_Store", "Thumbs.db"}
EXPLICIT_SOURCE_ROOT_NON_SKILL_ENTRIES = {
    "agents": {
        ".DS_Store": "OS_METADATA",
    },
    "claude": {},
    "codex": {
        ".DS_Store": "OS_METADATA",
        ".system": "SOURCE_OVERLAP",
        ".verifier-backups": "NON_SKILL_DOT_DIRECTORY_INCLUDED_IN_SOURCE_COVERAGE",
        ".wbi-install-transactions": (
            "NON_SKILL_OPERATIONAL_TRANSACTION_DIRECTORY_INCLUDED_IN_SOURCE_COVERAGE"
        ),
        ".wbi-install.lock": (
            "NON_SKILL_OPERATIONAL_LOCK_FILE_INCLUDED_IN_SOURCE_COVERAGE"
        ),
    },
    "codex-system": {
        ".codex-system-skills.marker": "SOURCE_MARKER",
    },
}


class CatalogReservationError(RuntimeError):
    """A public-safe fail-closed Registry reservation error."""

    def __init__(self, code: str, detail: str = "") -> None:
        self.code = code
        super().__init__(code if not detail else f"{code}:{detail}")


@dataclass(frozen=True)
class AliasSpec:
    source_namespace: str
    alias_path: str
    raw_target: str
    normalized_target_ref: str
    target_type: str

    def as_dict(self) -> Dict[str, str]:
        return {
            "alias_path": self.alias_path,
            "normalized_target_ref": self.normalized_target_ref,
            "raw_target": self.raw_target,
            "source_namespace": self.source_namespace,
            "target_type": self.target_type,
        }

    def metadata_digest(self) -> str:
        material = {
            "alias_path": self.alias_path,
            "normalized_target_ref": self.normalized_target_ref,
            "target_type": self.target_type,
        }
        return hashlib.sha256(_canonical_json(material)).hexdigest()


@dataclass(frozen=True)
class SourceRootInventory:
    skills: Mapping[Tuple[str, str], str]
    skill_counts: Mapping[str, int]
    explicit_non_skill_entries: Mapping[str, Tuple[Mapping[str, str], ...]]
    aliases: Tuple[AliasSpec, ...]

    @property
    def skill_count(self) -> int:
        return sum(self.skill_counts.values())

    @property
    def alias_count(self) -> int:
        return len(self.aliases)


def _canonical_json(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _alias_specs() -> Tuple[AliasSpec, ...]:
    # 2026-08-24：删除 beautiful-html-templates 的两条 alias —— 该 skill 已从三侧移除，
    # 留在合同里会让 walk 阶段恒报 SOURCE_ALIAS_TARGET_MISSING。
    rows = []
    for skill in (
        "gsap-core",
        "gsap-frameworks",
        "gsap-performance",
        "gsap-plugins",
        "gsap-react",
        "gsap-scrolltrigger",
        "gsap-skills",
        "gsap-timeline",
        "gsap-utils",
    ):
        # 2026-08-24：gsap 这组 alias 在 codex / claude / agents 三侧都真实存在，
        # 但合同此前只登记了 codex 一侧 —— 导致 SOURCE_ALIAS_SET_DRIFT 恒真，同步从未跑通。
        for source_namespace in ("agents", "claude", "codex"):
            for alias_name in ("CLAUDE.md", "GEMINI.md"):
                rows.append(
                    AliasSpec(
                        source_namespace,
                        f"{skill}/references/gsap-skills/{alias_name}",
                        "AGENTS.md",
                        f"{skill}/references/gsap-skills/AGENTS.md",
                        "REGULAR_FILE",
                    )
                )
    return tuple(
        sorted(
            rows,
            key=lambda item: (
                item.source_namespace.encode("utf-8"),
                item.alias_path.encode("utf-8"),
            ),
        )
    )


EXPECTED_SOURCE_ALIASES = _alias_specs()
EXPECTED_SOURCE_ALIAS_COUNT = 54


def alias_set_digest(aliases: Sequence[AliasSpec]) -> str:
    material = {
        "aliases": [item.as_dict() for item in aliases],
        "domain": "SKILLOPS_REGISTRY_ALIAS_SET_V1",
    }
    return hashlib.sha256(_canonical_json(material)).hexdigest()


EXPECTED_SOURCE_ALIAS_SET_DIGEST = alias_set_digest(EXPECTED_SOURCE_ALIASES)


def reserved_registry_paths() -> Tuple[str, ...]:
    rows = []
    for source in SOURCE_NAMESPACES:
        rows.append(
            f"CodexSkills/registry/{source}/{SOURCE_CATALOG_COMPONENT}/"
        )
        if source == "codex":
            rows.append(
                "CodexSkills/registry/codex/"
                f"{REGISTRY_DELIVERY_BACKUP_COMPONENT}/"
            )
    rows.append(f"CodexSkills/registry/{GLOBAL_REGISTRY_NAMESPACE}/")
    return tuple(rows)


def is_reserved_registry_relative_path(relative_path: str) -> bool:
    try:
        pure = PurePosixPath(relative_path)
    except (TypeError, ValueError):
        return False
    if (
        not relative_path
        or pure.is_absolute()
        or any(part in {"", ".", ".."} for part in pure.parts)
    ):
        return False
    parts = pure.parts
    if parts[0] == GLOBAL_REGISTRY_NAMESPACE:
        return True
    return (
        len(parts) >= 2
        and parts[0] in SOURCE_NAMESPACES
        and (
            parts[1] == SOURCE_CATALOG_COMPONENT
            or (
                parts[0] == "codex"
                and parts[1] == REGISTRY_DELIVERY_BACKUP_COMPONENT
            )
        )
    )


def is_reserved_source_child(source_namespace: str, child_name: str) -> bool:
    return (
        source_namespace in SOURCE_NAMESPACES
        and (
            child_name == SOURCE_CATALOG_COMPONENT
            or (
                source_namespace == "codex"
                and child_name == REGISTRY_DELIVERY_BACKUP_COMPONENT
            )
        )
    )


def _same_lstat(left: os.stat_result, right: os.stat_result) -> bool:
    return (
        left.st_dev,
        left.st_ino,
        left.st_mode,
        left.st_size,
        left.st_mtime_ns,
    ) == (
        right.st_dev,
        right.st_ino,
        right.st_mode,
        right.st_size,
        right.st_mtime_ns,
    )


def _within(root: Path, candidate: Path) -> bool:
    try:
        return os.path.commonpath((str(root), str(candidate))) == str(root)
    except ValueError:
        return False


def assert_real_directory(path: Path, code: str) -> Path:
    try:
        before = os.lstat(str(path))
    except OSError as exc:
        raise CatalogReservationError(code) from exc
    if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
        raise CatalogReservationError(code)
    try:
        resolved = path.resolve(strict=True)
        after = os.lstat(str(path))
    except OSError as exc:
        raise CatalogReservationError(code) from exc
    if not _same_lstat(before, after):
        raise CatalogReservationError(code)
    return resolved


def _assert_real_parent_chain(root: Path, relative_parent: PurePosixPath) -> None:
    current = root
    for component in relative_parent.parts:
        current = current / component
        try:
            info = os.lstat(str(current))
        except OSError as exc:
            raise CatalogReservationError("SOURCE_ALIAS_PARENT_UNSAFE") from exc
        if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
            raise CatalogReservationError("SOURCE_ALIAS_PARENT_UNSAFE")


def resolve_relative_alias(
    source_root: Path,
    alias_path: str,
    raw_target: str,
) -> Tuple[str, str]:
    root = assert_real_directory(source_root, "SOURCE_ROOT_NOT_REAL_DIRECTORY")
    alias = PurePosixPath(alias_path)
    if (
        alias.is_absolute()
        or not alias.parts
        or any(part in {"", ".", ".."} for part in alias.parts)
        or os.path.isabs(raw_target)
        or "\x00" in raw_target
    ):
        raise CatalogReservationError("SOURCE_ALIAS_PATH_UNSAFE")
    _assert_real_parent_chain(root, PurePosixPath(*alias.parts[:-1]))
    lexical_target = Path(
        os.path.normpath(str(root.joinpath(*alias.parts[:-1], raw_target)))
    )
    if not _within(root, lexical_target):
        raise CatalogReservationError("SOURCE_ALIAS_TARGET_ESCAPE")
    try:
        normalized = lexical_target.relative_to(root).as_posix()
    except ValueError as exc:
        raise CatalogReservationError("SOURCE_ALIAS_TARGET_ESCAPE") from exc

    current = root
    final = None
    target_parts = PurePosixPath(normalized).parts
    for index, component in enumerate(target_parts):
        current = current / component
        try:
            final = os.lstat(str(current))
        except OSError as exc:
            raise CatalogReservationError("SOURCE_ALIAS_TARGET_MISSING") from exc
        if stat.S_ISLNK(final.st_mode):
            raise CatalogReservationError("SOURCE_ALIAS_TARGET_CHAIN_UNSAFE")
        if index < len(target_parts) - 1 and not stat.S_ISDIR(final.st_mode):
            raise CatalogReservationError("SOURCE_ALIAS_TARGET_CHAIN_UNSAFE")
    if final is None or not (
        stat.S_ISDIR(final.st_mode) or stat.S_ISREG(final.st_mode)
    ):
        raise CatalogReservationError("SOURCE_ALIAS_TARGET_SPECIAL")
    target_type = "DIRECTORY" if stat.S_ISDIR(final.st_mode) else "REGULAR_FILE"
    return normalized, target_type


def observe_alias(source_root: Path, relative_path: str) -> AliasSpec:
    root = assert_real_directory(source_root, "SOURCE_ROOT_NOT_REAL_DIRECTORY")
    alias = root.joinpath(*PurePosixPath(relative_path).parts)
    try:
        before = os.lstat(str(alias))
    except OSError as exc:
        raise CatalogReservationError("SOURCE_ALIAS_LSTAT_FAILED") from exc
    if not stat.S_ISLNK(before.st_mode):
        raise CatalogReservationError("SOURCE_ALIAS_NOT_SYMLINK")
    try:
        raw_target = os.readlink(str(alias))
        after = os.lstat(str(alias))
    except OSError as exc:
        raise CatalogReservationError("SOURCE_ALIAS_READLINK_FAILED") from exc
    if not _same_lstat(before, after):
        raise CatalogReservationError("SOURCE_ALIAS_CHANGED_DURING_SCAN")
    normalized, target_type = resolve_relative_alias(
        root,
        relative_path,
        raw_target,
    )
    return AliasSpec("", relative_path, raw_target, normalized, target_type)


def _policy_exclusion_reason(
    source_namespace: str,
    relative: PurePosixPath,
    is_directory: bool,
) -> str:
    if any(part in POLICY_EXCLUDED_DIRECTORY_COMPONENTS for part in relative.parts):
        return "POLICY_EXCLUDED_DIRECTORY"
    if (
        source_namespace == "codex"
        and relative.parts
        and relative.parts[0] == ".system"
    ):
        return "SOURCE_OVERLAP"
    if (
        not is_directory
        and relative.parts
        and relative.parts[-1] in POLICY_EXCLUDED_FILES
    ):
        return "OS_METADATA"
    return ""


def observe_source_aliases(
    source_namespace: str,
    source_root: Path,
) -> Tuple[AliasSpec, ...]:
    root = assert_real_directory(source_root, "SOURCE_ROOT_NOT_REAL_DIRECTORY")
    aliases: List[AliasSpec] = []

    def walk(directory: Path, relative: PurePosixPath) -> None:
        try:
            before = os.lstat(str(directory))
            if stat.S_ISLNK(before.st_mode) or not stat.S_ISDIR(before.st_mode):
                raise CatalogReservationError("SOURCE_DIRECTORY_NOT_REAL")
            with os.scandir(str(directory)) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.encode("utf-8"))
        except CatalogReservationError:
            raise
        except (OSError, UnicodeError) as exc:
            raise CatalogReservationError("SOURCE_DIRECTORY_ENUMERATION_FAILED") from exc
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise CatalogReservationError("SOURCE_ENTRY_LSTAT_FAILED") from exc
            child_relative = (
                relative / entry.name
                if relative.parts
                else PurePosixPath(entry.name)
            )
            is_directory = stat.S_ISDIR(info.st_mode)
            if _policy_exclusion_reason(
                source_namespace,
                child_relative,
                is_directory,
            ):
                continue
            child = directory / entry.name
            if is_directory:
                walk(child, child_relative)
            elif stat.S_ISREG(info.st_mode):
                continue
            elif stat.S_ISLNK(info.st_mode):
                observed = observe_alias(root, child_relative.as_posix())
                aliases.append(
                    AliasSpec(
                        source_namespace,
                        observed.alias_path,
                        observed.raw_target,
                        observed.normalized_target_ref,
                        observed.target_type,
                    )
                )
            else:
                raise CatalogReservationError(
                    "SOURCE_SPECIAL_FILE",
                    child_relative.as_posix(),
                )
        try:
            after = os.lstat(str(directory))
        except OSError as exc:
            raise CatalogReservationError("SOURCE_DIRECTORY_RESTAT_FAILED") from exc
        if not _same_lstat(before, after):
            raise CatalogReservationError("SOURCE_CHANGED_DURING_SCAN")

    walk(root, PurePosixPath())
    return tuple(
        sorted(
            aliases,
            key=lambda item: (
                item.source_namespace.encode("utf-8"),
                item.alias_path.encode("utf-8"),
            ),
        )
    )


def _public_alias_rows(aliases: Iterable[AliasSpec]) -> List[Mapping[str, str]]:
    return [item.as_dict() for item in aliases]


def assert_exact_alias_set(
    source_roots: Mapping[str, Path],
) -> Tuple[AliasSpec, ...]:
    observed: List[AliasSpec] = []
    for namespace in SOURCE_NAMESPACES:
        if namespace not in source_roots:
            raise CatalogReservationError(
                "SOURCE_NAMESPACE_MISSING",
                namespace,
            )
        observed.extend(
            observe_source_aliases(namespace, Path(source_roots[namespace]))
        )
    ordered = tuple(
        sorted(
            observed,
            key=lambda item: (
                item.source_namespace.encode("utf-8"),
                item.alias_path.encode("utf-8"),
            ),
        )
    )
    if ordered != EXPECTED_SOURCE_ALIASES:
        detail = _canonical_json(
            {
                "expected": _public_alias_rows(EXPECTED_SOURCE_ALIASES),
                "observed": _public_alias_rows(ordered),
                "reason": "SOURCE_ALIAS_SET_DRIFT",
            }
        ).decode("utf-8")
        raise CatalogReservationError("SOURCE_ALIAS_SET_DRIFT", detail)
    return ordered


def inventory_source_roots(
    source_roots: Mapping[str, Path],
    *,
    enforce_exact_aliases: bool,
) -> SourceRootInventory:
    skills: Dict[Tuple[str, str], str] = {}
    counts: Dict[str, int] = {}
    non_skill: Dict[str, Tuple[Mapping[str, str], ...]] = {}
    for namespace in SOURCE_NAMESPACES:
        if namespace not in source_roots:
            raise CatalogReservationError("SOURCE_NAMESPACE_MISSING", namespace)
        root = assert_real_directory(
            Path(source_roots[namespace]),
            "SOURCE_ROOT_NOT_REAL_DIRECTORY",
        )
        try:
            root_before = os.lstat(str(root))
        except OSError as exc:
            raise CatalogReservationError(
                "SOURCE_ROOT_RESTAT_FAILED"
            ) from exc
        allowed_non_skill = EXPLICIT_SOURCE_ROOT_NON_SKILL_ENTRIES[namespace]
        observed_non_skill: List[Mapping[str, str]] = []
        try:
            with os.scandir(str(root)) as iterator:
                entries = sorted(iterator, key=lambda item: item.name.encode("utf-8"))
        except (OSError, UnicodeError) as exc:
            raise CatalogReservationError("SOURCE_ROOT_ENUMERATION_FAILED") from exc
        names: List[str] = []
        for entry in entries:
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise CatalogReservationError("SOURCE_ROOT_ENTRY_LSTAT_FAILED") from exc
            reason = allowed_non_skill.get(entry.name)
            if reason is not None:
                if entry.name in {
                    ".system",
                    ".verifier-backups",
                    ".wbi-install-transactions",
                }:
                    if stat.S_ISLNK(info.st_mode) or not stat.S_ISDIR(info.st_mode):
                        raise CatalogReservationError(
                            "SOURCE_ROOT_NON_SKILL_TYPE_DRIFT",
                            f"{namespace}/{entry.name}",
                        )
                    kind = "DIRECTORY"
                else:
                    if stat.S_ISLNK(info.st_mode) or not stat.S_ISREG(info.st_mode):
                        raise CatalogReservationError(
                            "SOURCE_ROOT_NON_SKILL_TYPE_DRIFT",
                            f"{namespace}/{entry.name}",
                        )
                    kind = "REGULAR_FILE"
                observed_non_skill.append(
                    {
                        "entry_name": entry.name,
                        "entry_type": kind,
                        "reason_code": reason,
                    }
                )
                continue
            if entry.name.startswith("."):
                raise CatalogReservationError(
                    "SOURCE_ROOT_UNCLASSIFIED_DOT_ENTRY",
                    f"{namespace}/{entry.name}",
                )
            if stat.S_ISLNK(info.st_mode):
                raise CatalogReservationError(
                    "SOURCE_SKILL_ROOT_SYMLINK_FORBIDDEN",
                    f"{namespace}/{entry.name}",
                )
            if not stat.S_ISDIR(info.st_mode):
                raise CatalogReservationError(
                    "SOURCE_ROOT_UNCLASSIFIED_NON_DIRECTORY",
                    f"{namespace}/{entry.name}",
                )
            names.append(entry.name)
            skills[(namespace, entry.name)] = str(root / entry.name)
        counts[namespace] = len(names)
        non_skill[namespace] = tuple(observed_non_skill)
        try:
            root_after = os.lstat(str(root))
        except OSError as exc:
            raise CatalogReservationError(
                "SOURCE_ROOT_RESTAT_FAILED"
            ) from exc
        if not _same_lstat(root_before, root_after):
            raise CatalogReservationError("SOURCE_ROOT_CHANGED_DURING_SCAN")
    aliases = (
        assert_exact_alias_set(source_roots)
        if enforce_exact_aliases
        else tuple()
    )
    return SourceRootInventory(
        skills=skills,
        skill_counts=counts,
        explicit_non_skill_entries=non_skill,
        aliases=aliases,
    )


def assert_safe_skill_removal_target(
    mirror_root: Path,
    source_namespace: str,
    slug: str,
) -> Path:
    root = assert_real_directory(mirror_root, "REGISTRY_ROOT_NOT_REAL_DIRECTORY")
    if (
        source_namespace not in SOURCE_NAMESPACES
        or not slug
        or "/" in slug
        or slug in {".", ".."}
        or is_reserved_source_child(source_namespace, slug)
    ):
        raise CatalogReservationError("REGISTRY_REMOVAL_RESERVED_OR_INVALID")
    source_root = root / source_namespace
    assert_real_directory(source_root, "REGISTRY_SOURCE_NOT_REAL_DIRECTORY")
    target = source_root / slug
    target_real = assert_real_directory(
        target,
        "REGISTRY_SKILL_REMOVAL_TARGET_NOT_REAL_DIRECTORY",
    )
    if not _within(source_root.resolve(strict=True), target_real):
        raise CatalogReservationError("REGISTRY_SKILL_REMOVAL_TARGET_ESCAPE")
    return target
