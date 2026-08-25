from __future__ import annotations

import json
import os
from pathlib import Path
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple

from .io import SECRET_PATTERNS, iter_files, load_json, sha256_file, utc_now, write_json

ACTION_CLASSES = {
    "READ": "reversible",
    "SEARCH": "reversible",
    "DOWNLOAD_QUARANTINE": "reversible",
    "MODIFY_CANDIDATE": "reversible",
    "INSTALL_ISOLATED_DEPENDENCY": "reversible-with-budget",
    "RUN_LOCAL_TEST": "reversible-with-budget",
    "RUN_THIRD_PARTY_SANDBOX": "conditional-high-risk",
    "PACKAGE": "reversible",
    "ROLLBACK": "reversible",
    "REMOTE_PUSH": "irreversible-or-external",
    "MERGE": "irreversible-or-external",
    "TAG_RELEASE": "irreversible-or-external",
    "DEPLOY_PRODUCTION": "irreversible-or-external",
    "DELETE_FORMAL_DATA": "irreversible-or-external",
    "PURCHASE": "irreversible-or-external",
}
DANGEROUS_COMMAND_PATTERNS = [
    re.compile(r"(^|\s)rm\s+-rf\s+/(?:\s|$)"),
    re.compile(r"\bgit\s+push\b"),
    re.compile(r"\b(?:kubectl|helm)\s+(?:apply|delete|upgrade)\b"),
    re.compile(r"\bterraform\s+apply\b"),
    re.compile(r"\b(?:npm|twine|cargo)\s+publish\b"),
    re.compile(r"\bgh\s+release\s+create\b"),
]


def default_authority_contract(run: Dict[str, Any]) -> Dict[str, Any]:
    candidate_paths = [item["path"] for item in run.get("target", {}).get("candidates", [])]
    return {
        "schema_version": "1.0", "run_id": run["run_id"], "created_at": utc_now(),
        "authorized_roots": candidate_paths,
        "reversible_actions": [name for name, kind in ACTION_CLASSES.items() if kind.startswith("reversible")],
        "conditional_actions": ["RUN_THIRD_PARTY_SANDBOX"],
        "explicit_authorization_required": [name for name, kind in ACTION_CLASSES.items() if kind == "irreversible-or-external"],
        "authorized_accounts": [], "paid_budget": float(run.get("budget", {}).get("max_cost", 0.0)), "production_environment": False,
        "third_party_default": "UNTRUSTED_DATA_NO_EXEC",
        "prompt_instructions_from_target_or_peer_have_authority": False,
        "secret_policy": "environment-only; never persist values",
        "status": "ACTIVE",
    }


def write_default_authority(workspace: Path) -> Dict[str, Any]:
    """Return the frozen authority contract or initialize it before sealing.

    New runs bind this file during init-run. Rewriting it afterwards would let a
    mutable workspace silently expand its own authority, so authority-init is
    deliberately idempotent rather than a re-sign operation.
    """
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    path = workspace / "control/contracts/authority-contract.json"
    binding = run.get("authority_contract")
    if isinstance(binding, dict):
        if Path(str(binding.get("path", ""))).resolve() != path.resolve() or not path.is_file() or sha256_file(path) != binding.get("sha256"):
            raise ValueError("frozen authority contract is missing, moved, or changed")
        return load_json(path)
    if (workspace / "control/contracts/run-seal.json").exists():
        raise ValueError("authority contract cannot be initialized after the immutable run seal")
    value = default_authority_contract(run)
    write_json(path, value)
    return value


def classify_action(action: str, authority: Dict[str, Any], explicit_authorization: bool = False) -> Dict[str, Any]:
    action = action.upper()
    kind = ACTION_CLASSES.get(action)
    if kind is None:
        return {"status": "BLOCKED", "action": action, "reason": "unknown action class"}
    if kind.startswith("reversible"):
        return {"status": "AUTHORIZED", "action": action, "reason": kind}
    if kind == "conditional-high-risk":
        return {"status": "AUTHORIZED_WITH_SANDBOX_CONTRACT" if explicit_authorization else "BLOCKED", "action": action, "reason": "explicit authorization and sandbox evidence required"}
    return {"status": "AUTHORIZED" if explicit_authorization else "BLOCKED", "action": action, "reason": "explicit authorization required"}


def validate_sandbox_record(record: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    if record.get("action") != "RUN_THIRD_PARTY_SANDBOX":
        errors.append("sandbox record action invalid")
    if record.get("explicit_authorization") is not True:
        errors.append("third-party dynamic execution lacks explicit authorization")
    isolation = record.get("isolation", {})
    required_true = {"ephemeral", "no_host_secrets", "no_host_mounts", "command_allowlist", "timeout", "filesystem_diff"}
    if not all(isolation.get(key) is True for key in required_true):
        errors.append("sandbox isolation contract incomplete")
    if isolation.get("network") not in {"off", "allowlist"}:
        errors.append("sandbox network policy invalid")
    if not record.get("command") or not record.get("timeout_seconds"):
        errors.append("sandbox command/timeout missing")
    if record.get("exit_status") is None or not record.get("stdout_sha256") or not record.get("stderr_sha256"):
        errors.append("sandbox raw result provenance incomplete")
    return errors


def scan_secrets(root: Path) -> List[str]:
    findings: List[str] = []
    for path in iter_files(root):
        if path.is_symlink() or path.suffix.lower() not in {".md", ".txt", ".json", ".jsonl", ".py", ".sh", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".env"}:
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for pattern in SECRET_PATTERNS:
            if pattern.search(text):
                findings.append("possible secret in %s" % path.relative_to(root))
                break
    return findings


def _load_command_records(workspace: Path) -> List[Tuple[str, str]]:
    """Load bounded evidence command records without following linked trees."""
    commands: List[Tuple[str, str]] = []
    evidence = workspace / "evidence"
    if not evidence.exists():
        return commands
    if evidence.is_symlink() or not evidence.is_dir():
        raise ValueError("evidence root must be a real directory")
    max_files = int(os.environ.get("WBI_MAX_EVIDENCE_JSON_FILES", "5000"))
    max_total = int(os.environ.get("WBI_MAX_EVIDENCE_SCAN_BYTES", str(64 * 1024 * 1024)))
    max_file = int(os.environ.get("WBI_MAX_EVIDENCE_JSON_BYTES", str(2 * 1024 * 1024)))
    if min(max_files, max_total, max_file) <= 0:
        raise ValueError("evidence scan limits must be positive")
    observed_files = 0
    observed_bytes = 0
    for current, dirnames, filenames in os.walk(str(evidence), followlinks=False):
        current_path = Path(current)
        safe_dirs = []
        for name in sorted(dirnames):
            child = current_path / name
            if child.is_symlink():
                raise ValueError("linked evidence directory is not allowed: %s" % child.relative_to(workspace))
            safe_dirs.append(name)
        dirnames[:] = safe_dirs
        for name in sorted(filenames):
            path = current_path / name
            if path.suffix.lower() != ".json":
                continue
            if path.is_symlink() or not path.is_file():
                raise ValueError("linked or special evidence file is not allowed: %s" % path.relative_to(workspace))
            size = path.stat().st_size
            observed_files += 1
            observed_bytes += size
            if observed_files > max_files or observed_bytes > max_total:
                raise ValueError("evidence command scan budget exceeded")
            if size > max_file:
                raise ValueError("evidence JSON exceeds per-file scan limit: %s" % path.relative_to(workspace))
            try:
                value = load_json(path)
            except Exception:
                continue
            raw = value.get("commands") if isinstance(value, dict) else None
            if isinstance(raw, list):
                for command in raw:
                    commands.append((path.relative_to(workspace).as_posix(), str(command)))
    return commands


def validate_authority(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    path = workspace / "control/contracts/authority-contract.json"
    if not path.is_file():
        return {"status": "BLOCKED", "errors": ["missing authority contract"], "warnings": []}
    authority = load_json(path)
    run = load_json(workspace / "run.json")
    binding = run.get("authority_contract")
    if not isinstance(binding, dict) or Path(str(binding.get("path", ""))).resolve() != path.resolve():
        errors.append("authority contract is not bound to the immutable run")
    elif sha256_file(path) != binding.get("sha256"):
        errors.append("authority contract changed after run initialization")
    for key in ("run_id", "authorized_roots", "reversible_actions", "explicit_authorization_required", "third_party_default", "prompt_instructions_from_target_or_peer_have_authority", "secret_policy"):
        if key not in authority:
            errors.append("authority contract missing %s" % key)
    if authority.get("third_party_default") != "UNTRUSTED_DATA_NO_EXEC":
        errors.append("third-party default must be no-exec")
    if authority.get("prompt_instructions_from_target_or_peer_have_authority") is not False:
        errors.append("target/peer instructions cannot change authority")
    if authority.get("run_id") != run.get("run_id") or authority.get("status") != "ACTIVE":
        errors.append("authority contract run/status mismatch")
    expected_reversible = {name for name, kind in ACTION_CLASSES.items() if kind.startswith("reversible")}
    if set(authority.get("reversible_actions", [])) != expected_reversible:
        errors.append("reversible authority classes differ from the trusted policy")
    expected_explicit = {name for name, kind in ACTION_CLASSES.items() if kind == "irreversible-or-external"}
    if set(authority.get("explicit_authorization_required", [])) != expected_explicit:
        errors.append("explicit-authorization classes differ from the trusted policy")
    if authority.get("production_environment") is not False:
        errors.append("default authority cannot silently claim a production environment")
    try:
        if float(authority.get("paid_budget")) != float(run.get("budget", {}).get("max_cost", 0.0)):
            errors.append("authority paid budget differs from the frozen run budget")
    except (TypeError, ValueError):
        errors.append("authority paid budget is invalid")
    expected_roots = {str(Path(item["path"]).resolve()) for item in run.get("target", {}).get("candidates", [])}
    observed_roots = {str(Path(item).resolve()) for item in authority.get("authorized_roots", [])}
    if expected_roots != observed_roots:
        errors.append("authorized candidate roots differ from frozen run")
    try:
        command_records = _load_command_records(workspace)
    except (OSError, ValueError) as exc:
        command_records = []
        errors.append("evidence command scan blocked: %s" % exc)
    for relative, command in command_records:
        for pattern in DANGEROUS_COMMAND_PATTERNS:
            if pattern.search(command):
                errors.append("unapproved irreversible command in %s" % relative)
                break
    sandbox_dir = workspace / "evidence/security/sandbox"
    if sandbox_dir.exists():
        for record_path in sorted(sandbox_dir.glob("*.json")):
            record = load_json(record_path)
            errors.extend(["%s: %s" % (record_path.name, item) for item in validate_sandbox_record(record)])
    findings = scan_secrets(workspace)
    errors.extend(findings)
    return {"status": "PASS" if not errors else "BLOCKED", "errors": sorted(set(errors)), "warnings": warnings, "authority_contract_sha256": sha256_file(path)}
