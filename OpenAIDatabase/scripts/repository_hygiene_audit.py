#!/usr/bin/env python3
"""Audit the migrated AgentDatabase tree for bounded tracked artifacts."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path, PurePosixPath
from typing import Any, Mapping


DEFAULT_POLICY = Path("OpenAIDatabase/config/storage/repository_hygiene.json")
REGISTRY_PLANE_TOKEN = "{registry_plane}"
DECLARED_REGISTRY_PLANES = frozenset({"agents", "claude", "codex"})
PERSONA_DELIVERY_VERSION = re.compile(r"0\.0\.0\.(?:[1-9]\d{0,2})")
PERSONA_DELIVERY_SLUG = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*")


class RepositoryHygieneError(RuntimeError):
    """Stable repository audit error."""


def _git(root: Path, *args: str, binary: bool = False) -> subprocess.CompletedProcess[Any]:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        check=False,
        text=not binary,
    )


def load_policy(root: Path, relative: Path = DEFAULT_POLICY) -> dict[str, Any]:
    try:
        payload = json.loads((root / relative).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise RepositoryHygieneError("repository_hygiene_policy_invalid") from exc
    if not isinstance(payload, dict):
        raise RepositoryHygieneError("repository_hygiene_policy_invalid")
    return payload


def validate_policy(policy: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    if policy.get("schema_version") != "agent_database.repository_hygiene.v1":
        errors.append("policy_schema_invalid")
    maximum = policy.get("default_blob_max_bytes")
    if not isinstance(maximum, int) or not 0 < maximum <= 1_048_576:
        errors.append("default_blob_max_bytes_invalid")
    registry_planes = policy.get("registry_planes")
    if (
        not isinstance(registry_planes, list)
        or any(not isinstance(plane, str) for plane in registry_planes)
        or set(registry_planes) != DECLARED_REGISTRY_PLANES
        or len(registry_planes) != len(DECLARED_REGISTRY_PLANES)
    ):
        errors.append("registry_planes_invalid")
    persona_contract = policy.get("persona_delivery_archive_contract")
    if (
        not isinstance(persona_contract, dict)
        or not isinstance(persona_contract.get("root"), str)
        or not str(persona_contract["root"]).endswith("/")
        or not isinstance(persona_contract.get("identity_families"), list)
        or not persona_contract["identity_families"]
        or any(
            not isinstance(identity, str) or not identity
            for identity in persona_contract["identity_families"]
        )
    ):
        errors.append("persona_delivery_archive_contract_invalid")
    rules = policy.get("allowed_large_objects")
    if not isinstance(rules, list):
        errors.append("allowed_large_objects_invalid")
        rules = []
    for index, rule in enumerate(rules):
        prefix = rule.get("prefix") if isinstance(rule, dict) else None
        if (
            not isinstance(rule, dict)
            or not isinstance(prefix, str)
            or not prefix.endswith("/")
            or (
                REGISTRY_PLANE_TOKEN in prefix
                and prefix.count(REGISTRY_PLANE_TOKEN) != 1
            )
            or not isinstance(rule.get("max_bytes"), int)
            or int(rule["max_bytes"]) <= int(maximum or 0)
            or not isinstance(rule.get("reason"), str)
            or not str(rule["reason"]).strip()
        ):
            errors.append(f"allowed_large_objects_invalid:{index}")
    for key in (
        "allowed_archive_prefixes",
        "archive_suffixes",
        "forbidden_names",
        "forbidden_suffixes",
    ):
        if not isinstance(policy.get(key), list) or any(
            not isinstance(item, str) or not item for item in policy.get(key, [])
        ):
            errors.append(f"{key}_invalid")
    return errors


def allowed_large_object_rules(policy: Mapping[str, Any]) -> tuple[tuple[str, int], ...]:
    rules: list[tuple[str, int]] = []
    for rule in policy["allowed_large_objects"]:
        prefix = str(rule["prefix"])
        max_bytes = int(rule["max_bytes"])
        if REGISTRY_PLANE_TOKEN not in prefix:
            rules.append((prefix, max_bytes))
            continue
        rules.extend(
            (prefix.replace(REGISTRY_PLANE_TOKEN, str(plane)), max_bytes)
            for plane in policy["registry_planes"]
        )
    return tuple(rules)


def is_canonical_persona_delivery_archive(
    path: str, contract: Mapping[str, Any]
) -> bool:
    root = str(contract["root"])
    if not path.startswith(root):
        return False
    parts = PurePosixPath(path[len(root) :]).parts
    if len(parts) != 5:
        return False
    identity_family, slug, versions, version, filename = parts
    return (
        identity_family in contract["identity_families"]
        and versions == "versions"
        and PERSONA_DELIVERY_SLUG.fullmatch(slug) is not None
        and PERSONA_DELIVERY_VERSION.fullmatch(version) is not None
        and filename == f"{slug}-persona-distillation-delivery-v{version}.zip"
    )


def tree_inventory(root: Path, treeish: str) -> dict[str, int]:
    result = _git(root, "ls-tree", "-rlz", treeish, binary=True)
    if result.returncode != 0:
        raise RepositoryHygieneError("repository_tree_read_failed")
    inventory: dict[str, int] = {}
    for row in result.stdout.split(b"\0"):
        if not row:
            continue
        metadata, raw_path = row.split(b"\t", 1)
        _mode, kind, _oid, raw_size = metadata.split(b" ", 3)
        if kind == b"blob" and raw_size != b"-":
            inventory[raw_path.decode("utf-8", errors="surrogateescape")] = int(raw_size)
    return inventory


def worktree_inventory(root: Path) -> dict[str, int]:
    result = _git(root, "ls-files", "--cached", "--others", "--exclude-standard", "-z", binary=True)
    if result.returncode != 0:
        raise RepositoryHygieneError("repository_worktree_read_failed")
    inventory: dict[str, int] = {}
    for raw_path in result.stdout.split(b"\0"):
        if not raw_path:
            continue
        relative = raw_path.decode("utf-8", errors="surrogateescape")
        path = root / relative
        if path.is_file() and not path.is_symlink():
            inventory[relative] = path.stat().st_size
    return inventory


def evaluate_inventory(
    inventory: Mapping[str, int],
    policy: Mapping[str, Any],
) -> list[dict[str, Any]]:
    violations: list[dict[str, Any]] = []
    default_max = int(policy["default_blob_max_bytes"])
    archive_suffixes = tuple(str(value).casefold() for value in policy["archive_suffixes"])
    allowed_archives = tuple(str(value) for value in policy["allowed_archive_prefixes"])
    allowed_large_rules = allowed_large_object_rules(policy)
    persona_contract = policy["persona_delivery_archive_contract"]
    forbidden_names = {str(value).casefold() for value in policy["forbidden_names"]}
    forbidden_suffixes = tuple(str(value).casefold() for value in policy["forbidden_suffixes"])

    for path, size in sorted(inventory.items()):
        pure = PurePosixPath(path)
        lowered = path.casefold()
        if pure.name.casefold() in forbidden_names or lowered.endswith(forbidden_suffixes):
            violations.append({"path": path, "reason": "forbidden_credential_shape", "bytes": size})
            continue
        allowed_max = default_max
        for prefix, max_bytes in allowed_large_rules:
            if path.startswith(prefix):
                allowed_max = max(allowed_max, max_bytes)
        if size > allowed_max:
            violations.append(
                {
                    "path": path,
                    "reason": "tracked_blob_exceeds_bound",
                    "bytes": size,
                    "max_bytes": allowed_max,
                }
            )
        archive_allowed = any(
            path == rule or (rule.endswith("/") and path.startswith(rule))
            for rule in allowed_archives
        ) or is_canonical_persona_delivery_archive(path, persona_contract)
        if lowered.endswith(archive_suffixes) and not archive_allowed:
            violations.append({"path": path, "reason": "unapproved_tracked_archive", "bytes": size})
    return violations


def audit(root: Path, *, treeish: str | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve(strict=True)
    policy = load_policy(root)
    policy_errors = validate_policy(policy)
    if policy_errors:
        return {
            "schema_version": "agent_database.repository_hygiene_report.v1",
            "status": "FAIL",
            "mode": treeish or "worktree",
            "baseline_tree": "",
            "policy_errors": policy_errors,
            "violations": [],
        }
    if treeish:
        inventory = tree_inventory(root, treeish)
        tree = _git(root, "rev-parse", f"{treeish}^{{tree}}")
        if tree.returncode != 0:
            raise RepositoryHygieneError("repository_tree_read_failed")
        baseline_tree = tree.stdout.strip()
    else:
        inventory = worktree_inventory(root)
        tree = _git(root, "rev-parse", "HEAD^{tree}")
        if tree.returncode != 0:
            raise RepositoryHygieneError("repository_tree_read_failed")
        baseline_tree = tree.stdout.strip()
    violations = evaluate_inventory(inventory, policy)
    return {
        "schema_version": "agent_database.repository_hygiene_report.v1",
        "status": "PASS" if not violations else "FAIL",
        "mode": treeish or "worktree",
        "baseline_tree": baseline_tree,
        "policy_errors": [],
        "violations": violations,
        "inventory": {
            "tracked_file_count": len(inventory),
            "tracked_bytes": sum(inventory.values()),
            "large_object_count": sum(
                size > int(policy["default_blob_max_bytes"]) for size in inventory.values()
            ),
        },
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--tree-ish")
    args = parser.parse_args(argv)
    try:
        report = audit(args.root, treeish=args.tree_ish)
    except RepositoryHygieneError as exc:
        report = {
            "schema_version": "agent_database.repository_hygiene_report.v1",
            "status": "FAIL",
            "mode": args.tree_ish or "worktree",
            "baseline_tree": "",
            "policy_errors": [str(exc)],
            "violations": [],
        }
    print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    return 0 if report["status"] == "PASS" else 2


if __name__ == "__main__":
    raise SystemExit(main())
