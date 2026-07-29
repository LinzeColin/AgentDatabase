from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

from .genesis import discover_effective_paths, verify_genesis
from .io import (
    JUNK_NAMES,
    NAME_RE,
    SECRET_PATTERNS,
    TEXT_SUFFIXES,
    VERSION_RE,
    iter_files,
    load_json,
    read_frontmatter,
    verify_manifest,
)

GENERIC_REQUIRED = ["SKILL.md"]
OPTIMIZER_BASE_REQUIRED = [
    "SKILL.md", "README.md", "VERSION", "LICENSE", "CHANGELOG.md",
    "constitution/GENESIS_SOURCE.v0.0.0.1.zh-CN.md",
    "constitution/GENESIS_LOCKED.v0.0.0.1.zh-CN.md",
    "constitution/genesis-lock.json", "constitution/requirements.json",
    "metadata/release.json", "scripts/wbi.py",
]
V3_REQUIRED = [
    "constitution/amendments/WBI-GB-AMENDMENT-002-v0.0.0.3.zh-CN.md",
    "modules/raw_teleiosis/CAPABILITIES.json",
    "modules/skill_market_lab/CAPABILITIES.json",
    "modules/product_reality_lab/CAPABILITIES.json",
    "scripts/teleiosis_run.py",
    "scripts/wbi_run/core.py",
    "references/FULL_RUN_CONTRACT.md",
    "delivery/INSTALL_AND_GITHUB.md",
]
VALID_PROFILES = {"auto", "generic", "optimizer"}


def detect_profile(root: Path, requested: str = "auto") -> str:
    if requested not in VALID_PROFILES:
        raise ValueError("validation profile must be auto, generic or optimizer")
    if requested != "auto":
        return requested
    optimizer_markers = (
        root.name == "teleiosis",
        (root / "constitution/genesis-lock.json").is_file(),
        (root / "scripts/wbi.py").is_file() and (root / "metadata/release.json").is_file(),
    )
    return "optimizer" if any(optimizer_markers) else "generic"


def _scan_common_files(root: Path, errors: List[str]) -> None:
    for path in iter_files(root):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            errors.append("symlink rejected: %s" % relative)
            continue
        if path.name in JUNK_NAMES or any(part.startswith(".") and part not in {".github"} for part in path.relative_to(root).parts):
            errors.append("junk or hidden path rejected: %s" % relative)
        if path.stat().st_size > 50 * 1024 * 1024:
            errors.append("file exceeds 50 MiB: %s" % relative)
        if path.suffix.lower() in TEXT_SUFFIXES and path.stat().st_size <= 5 * 1024 * 1024:
            try:
                text = path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                errors.append("invalid UTF-8 text file: %s" % relative)
                continue
            for pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    errors.append("possible secret in %s" % relative)
                    break


def validate_skill(
    root: Path,
    strict: bool = False,
    check_manifest: bool = True,
    expected_genesis_hash: str = "",
    expected_effective_genesis_hash: str = "",
    profile: str = "auto",
) -> Dict[str, Any]:
    root = root.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    if not root.is_dir():
        return {"status": "FAIL", "profile": profile, "errors": ["Skill root is not a directory: %s" % root], "warnings": []}
    try:
        resolved_profile = detect_profile(root, profile)
    except ValueError as exc:
        return {"status": "FAIL", "profile": profile, "errors": [str(exc)], "warnings": []}

    required = list(OPTIMIZER_BASE_REQUIRED if resolved_profile == "optimizer" else GENERIC_REQUIRED)
    version = (root / "VERSION").read_text(encoding="utf-8").strip() if (root / "VERSION").is_file() else "UNKNOWN"
    if resolved_profile == "optimizer":
        lock_path, projection_path = discover_effective_paths(root)
        if lock_path and projection_path:
            required.extend([lock_path.relative_to(root).as_posix(), projection_path.relative_to(root).as_posix()])
        else:
            errors.append("missing effective Genesis lock/projection pair")
        if version == "v0.0.0.3":
            required.extend(V3_REQUIRED)
    for relative in required:
        if not (root / relative).is_file():
            errors.append("missing required file: %s" % relative)
    if not (root / "SKILL.md").is_file():
        return {"status": "FAIL", "profile": resolved_profile, "errors": sorted(set(errors)), "warnings": warnings}

    try:
        frontmatter, body = read_frontmatter(root / "SKILL.md")
    except Exception as exc:
        errors.append(str(exc))
        frontmatter, body = {}, ""
    name = str(frontmatter.get("name", ""))
    if not NAME_RE.fullmatch(name):
        errors.append("invalid frontmatter name: %s" % name)
    if root.name != name:
        errors.append("Skill directory name must match frontmatter name (%s != %s)" % (root.name, name))
    description = str(frontmatter.get("description", ""))
    if not description or len(description) > 1024:
        errors.append("description must be 1..1024 characters")
    line_count = len((root / "SKILL.md").read_text(encoding="utf-8").splitlines())
    if line_count > 500:
        message = "SKILL.md exceeds 500 lines; use progressive disclosure"
        if resolved_profile == "optimizer" or strict:
            errors.append(message)
        else:
            warnings.append(message)
    if not body.strip():
        errors.append("SKILL.md body is empty")

    genesis: Dict[str, Any] = {}
    if resolved_profile == "optimizer" and not any(item.startswith("missing required file") for item in errors):
        metadata = frontmatter.get("metadata")
        metadata_version = str(metadata.get("version", "")) if isinstance(metadata, dict) else ""
        try:
            release = load_json(root / "metadata/release.json")
        except Exception as exc:
            release = {}
            errors.append("invalid metadata/release.json: %s" % exc)
        if not VERSION_RE.fullmatch(version):
            errors.append("VERSION must use vN.N.N.N")
        if metadata_version != version or release.get("version") != version:
            errors.append("VERSION, frontmatter metadata.version and metadata/release.json must match")
        if release.get("display_name_zh") != "白箱迭代Skill":
            errors.append("Chinese display name must be 白箱迭代Skill")
        if release.get("english_brand") != "Teleiosis":
            errors.append("English brand must remain Teleiosis")
        if version == "v0.0.0.3":
            if release.get("candidate_semantics") != "C_IS_ITERATION_OBJECT_REVISION_NOT_SHA_CHECKPOINT":
                errors.append("v0.0.0.3 candidate semantics missing or regressed")
            if release.get("scope_mode") != "FULL_NO_ROUTING":
                errors.append("v0.0.0.3 must use FULL_NO_ROUTING")
        genesis = verify_genesis(root, expected_hash=expected_genesis_hash or None, expected_effective_hash=expected_effective_genesis_hash or None)
        errors.extend(genesis.get("errors", []))
        warnings.extend(genesis.get("warnings", []))
    elif resolved_profile == "generic" and expected_genesis_hash:
        warnings.append("expected Genesis hash ignored for a generic target Skill")

    _scan_common_files(root, errors)
    if check_manifest:
        manifest = root / "MANIFEST.sha256"
        if manifest.exists():
            errors.extend(verify_manifest(root))
        elif strict:
            errors.append("strict validation requires MANIFEST.sha256")
        else:
            warnings.append("MANIFEST.sha256 not present")

    return {
        "status": "PASS" if not errors else "FAIL",
        "profile": resolved_profile,
        "skill": name,
        "version": version,
        "genesis_sha256": genesis.get("locked_sha256") if genesis else None,
        "effective_genesis_sha256": genesis.get("effective_composite_sha256") if genesis else None,
        "effective_requirement_count": genesis.get("effective_requirement_count") if genesis else None,
        "anchor_mode": genesis.get("anchor_mode") if genesis else None,
        "errors": sorted(set(errors)),
        "warnings": sorted(set(warnings)),
    }
