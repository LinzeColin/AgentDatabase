#!/usr/bin/env python3
"""Audit the current AgentDatabase workflow surface without legacy governance."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_POLICY = Path("OpenAIDatabase/config/workflow_security_policy.json")
FULL_SHA = re.compile(r"^[a-f0-9]{40}$")
USES = re.compile(r"^\s*(?:-\s*)?uses:\s*([^\s#]+)", re.MULTILINE)
WRITE_PERMISSION = re.compile(
    r"^\s*(actions|checks|contents|deployments|id-token|issues|packages|"
    r"pages|pull-requests|repository-projects|security-events|statuses):\s*write\s*$",
    re.MULTILINE,
)


class WorkflowAuditError(ValueError):
    """Stable fail-closed workflow policy error."""


def load_policy(root: Path, relative: Path = DEFAULT_POLICY) -> dict[str, Any]:
    path = relative if relative.is_absolute() else root / relative
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WorkflowAuditError("workflow_policy_invalid") from exc
    if not isinstance(value, dict) or value.get("schema_version") != (
        "agent_database.workflow_security_policy.v1"
    ):
        raise WorkflowAuditError("workflow_policy_identity_invalid")
    return value


def tracked_workflows(root: Path) -> tuple[list[str], list[str]]:
    canonical_dir = (root / ".github/workflows").resolve()
    canonical = sorted(
        path.relative_to(root).as_posix()
        for path in canonical_dir.glob("*")
        if path.is_file() and path.suffix.lower() in {".yml", ".yaml"}
    )
    nested: list[str] = []
    for path in root.rglob("*"):
        if (
            path.is_file()
            and path.suffix.lower() in {".yml", ".yaml"}
            and ".github" in path.parts
            and "workflows" in path.parts
            and path.parent.resolve() != canonical_dir
        ):
            nested.append(path.relative_to(root).as_posix())
    return canonical, sorted(nested)


def audit(root: Path, policy: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve(strict=True)
    workflows, nested = tracked_workflows(root)
    allowed = sorted(str(value) for value in policy.get("allowed_workflows") or [])
    allowed_nested = sorted(
        str(value) for value in policy.get("allowed_nested_workflows") or []
    )
    unowned = sorted(set(workflows) - set(allowed))
    missing = sorted(set(allowed) - set(workflows))
    invalid_nested = sorted(set(nested) - set(allowed_nested))
    missing_nested = sorted(set(allowed_nested) - set(nested))
    workflow_contracts = {
        str(row.get("path")): row
        for row in policy.get("workflows") or []
        if isinstance(row, dict) and isinstance(row.get("path"), str)
    }
    pins = {
        str(item.get("action")): str(item.get("commit_sha"))
        for item in policy.get("action_pins") or []
        if isinstance(item, dict)
    }
    if not pins or any(not FULL_SHA.fullmatch(value) for value in pins.values()):
        raise WorkflowAuditError("workflow_action_pin_policy_invalid")

    external_refs = 0
    unpinned = 0
    unapproved = 0
    forbidden_triggers = 0
    direct_context = 0
    high_privilege = 0
    missing_timeouts = 0
    missing_concurrency = 0
    overbroad_permissions = 0

    for relative in allowed:
        path = root / relative
        if not path.is_file() or path.is_symlink():
            continue
        text = path.read_text(encoding="utf-8")
        for reference in USES.findall(text):
            if reference.startswith("./"):
                continue
            external_refs += 1
            action, separator, sha = reference.partition("@")
            if not separator or not FULL_SHA.fullmatch(sha):
                unpinned += 1
            if pins.get(action) != sha:
                unapproved += 1
        forbidden_triggers += sum(
            len(re.findall(rf"^\s*{re.escape(str(event))}:\s*$", text, re.MULTILINE))
            for event in policy.get("forbidden_events") or []
        )
        direct_context += sum(
            text.count(fragment)
            for fragment in ("github.event.pull_request.", "github.event.issue.", "github.event.comment.")
        )
        contract = workflow_contracts.get(relative, {})
        required_permissions = contract.get("required_permissions")
        if not isinstance(required_permissions, dict):
            required_permissions = policy.get("required_permissions") or {}
        allowed_write_permissions = {
            str(value) for value in contract.get("allowed_write_permissions") or []
        }
        actual_write_permissions = set(WRITE_PERMISSION.findall(text))
        high_privilege += len(actual_write_permissions - allowed_write_permissions)
        missing_timeouts += int("timeout-minutes:" not in text)
        missing_concurrency += int(not re.search(r"^concurrency:\s*$", text, re.MULTILINE))
        overbroad_permissions += int(
            "permissions:" not in text
            or any(
                not re.search(
                    rf"^\s*{re.escape(str(key))}:\s*{re.escape(str(value))}\s*$",
                    text,
                    re.MULTILINE,
                )
                for key, value in required_permissions.items()
            )
            or any(
                required_permissions.get(key) != "write"
                for key in allowed_write_permissions
            )
            or (
                bool(allowed_write_permissions)
                and not contract.get("write_allowlist")
            )
        )

    metrics = {
        "unowned_workflow_count": len(unowned) + len(missing),
        "invalid_nested_workflow_count": len(invalid_nested) + len(missing_nested),
        "unpinned_actions": unpinned,
        "unapproved_actions": unapproved,
        "forbidden_triggers": forbidden_triggers,
        "direct_context_violations": direct_context,
        "high_privilege_violations": high_privilege,
        "missing_timeouts": missing_timeouts,
        "missing_concurrency": missing_concurrency,
        "overbroad_permissions": overbroad_permissions,
    }
    return {
        "schema_version": "agent_database.workflow_security_audit.v1",
        "status": "PASS" if all(value == 0 for value in metrics.values()) else "FAIL",
        "workflow_count": len(workflows),
        "external_action_refs": external_refs,
        "unowned_workflows": unowned,
        "missing_workflows": missing,
        "nested_workflows": nested,
        "invalid_nested_workflows": invalid_nested,
        "missing_nested_workflows": missing_nested,
        **metrics,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("audit",))
    parser.add_argument("--root", type=Path, default=REPO_ROOT)
    parser.add_argument("--policy", type=Path, default=DEFAULT_POLICY)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    try:
        root = args.root.expanduser().resolve(strict=True)
        result = audit(root, load_policy(root, args.policy))
    except (OSError, WorkflowAuditError) as exc:
        result = {
            "schema_version": "agent_database.workflow_security_audit.v1",
            "status": "FAIL_CLOSED",
            "reason": str(exc) or "workflow_audit_failed",
        }
    print(json.dumps(result, ensure_ascii=False, sort_keys=True, separators=(",", ":")))
    return 0 if result.get("status") == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
