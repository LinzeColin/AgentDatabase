from __future__ import annotations

import datetime as dt
import difflib
import hashlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import stat
import time
import uuid
from typing import Any, Dict, Iterable, List, Optional, Tuple
try:
    from zoneinfo import ZoneInfo
except ImportError:  # pragma: no cover - Python 3.9+ has zoneinfo
    ZoneInfo = None  # type: ignore

from .genesis import verify_genesis
from .io import SKIP_DIRS, bind_files, canonical_json, copy_clean, ensure_external, iter_files, load_json, sha256_bytes, sha256_file, sha256_tree, utc_now, verify_file_bindings, write_json
from .ledger import append_event, read_events, verify_event_chain

DEFAULT_STRATEGIES = ("incremental", "architecture", "clean-slate")
STRATEGY_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")
VALID_DECISIONS = {"KEEP", "REVERT", "NO_CHANGE"}
CHANGE_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TERMINAL = {"SATURATED", "BLOCKED", "REHEAT_REQUIRED", "RETIRED", "RELEASED"}
ALLOWED_TRANSITIONS = {
    "INITIALIZED": {"RESEARCHING", "BLOCKED"},
    "RESEARCHING": {"ITERATING", "RETIRED", "BLOCKED"},
    "ITERATING": {"REVIEWING", "SATURATED", "BLOCKED", "REHEAT_REQUIRED"},
    "REVIEWING": {"VERIFYING", "ITERATING", "BLOCKED"},
    "VERIFYING": {"RELEASE_READY", "ITERATING", "BLOCKED", "REHEAT_REQUIRED"},
    "RELEASE_READY": {"RELEASED", "BLOCKED", "REHEAT_REQUIRED"},
}

DEFAULT_BUDGET = {
    "mandatory_review_rounds": 10,
    "max_total_rounds": 16,
    "max_candidates": 4,
    "max_architecture_resets": 3,
    "max_wall_seconds": 86400,
    "max_network_requests": 500,
    "max_projects": 40,
    "max_evaluations": 500,
    "max_model_calls": 1000,
    "max_tokens": 5000000,
    "max_cost": 0.0,
    "max_storage_bytes": 2147483648,
    "saturation_patience": 3,
}


def _walk_control_plane_files(optimizer_root: Path, *, max_files: int = 20000, max_dirs: int = 20000, max_bytes: int = 2147483648) -> List[Path]:
    """Enumerate one trusted optimizer tree with explicit resource bounds.

    Missing or malformed run fields must never fall back to the process current
    working directory. The walker also rejects linked/special files and stops
    before a hostile tree can turn an integrity check into an unbounded scan.
    """
    optimizer_root = optimizer_root.resolve()
    if not optimizer_root.is_dir() or optimizer_root.is_symlink():
        raise ValueError("optimizer root is missing, linked or not a directory")
    files: List[Path] = []
    directory_count = 0
    total_bytes = 0
    for current, directory_names, file_names in os.walk(str(optimizer_root), topdown=True, followlinks=False):
        directory_count += 1
        if directory_count > max_dirs:
            raise ValueError("optimizer control plane exceeds directory inspection budget")
        current_path = Path(current)
        kept_directories: List[str] = []
        for name in sorted(directory_names):
            child = current_path / name
            if name in SKIP_DIRS:
                continue
            if child.is_symlink():
                raise ValueError("optimizer control plane contains a linked directory: %s" % child.relative_to(optimizer_root).as_posix())
            kept_directories.append(name)
        directory_names[:] = kept_directories
        for name in sorted(file_names):
            path = current_path / name
            relative = path.relative_to(optimizer_root).as_posix()
            if relative == "MANIFEST.sha256":
                continue
            if path.is_symlink():
                raise ValueError("optimizer control plane contains a symlink: %s" % relative)
            try:
                metadata = path.stat()
            except OSError as exc:
                raise ValueError("cannot stat optimizer control-plane file %s: %s" % (relative, exc))
            if not stat.S_ISREG(metadata.st_mode):
                raise ValueError("optimizer control plane contains a special file: %s" % relative)
            files.append(path)
            total_bytes += metadata.st_size
            if len(files) > max_files:
                raise ValueError("optimizer control plane exceeds file inspection budget")
            if total_bytes > max_bytes:
                raise ValueError("optimizer control plane exceeds byte inspection budget")
    return files


def _tree_hash_from_entries(entries: List[Dict[str, Any]]) -> str:
    digest = hashlib.sha256()
    for entry in sorted(entries, key=lambda item: str(item["path"])):
        digest.update(str(entry["path"]).encode("utf-8") + b"\0")
        digest.update(bytes.fromhex(str(entry["sha256"])))
    return digest.hexdigest()


def _control_plane_manifest(optimizer_root: Path) -> Dict[str, Any]:
    optimizer_root = optimizer_root.resolve()
    entries: List[Dict[str, Any]] = []
    for path in _walk_control_plane_files(optimizer_root):
        relative = path.relative_to(optimizer_root).as_posix()
        entries.append({"path": relative, "sha256": sha256_file(path), "bytes": path.stat().st_size})
    payload: Dict[str, Any] = {
        "schema_version": "1.0",
        "optimizer_root": str(optimizer_root),
        "optimizer_tree_hash": _tree_hash_from_entries(entries),
        "entries": entries,
    }
    payload["manifest_sha256"] = sha256_bytes(canonical_json(payload))
    return payload


def _mapping(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _required_absolute_path(value: Any, label: str, errors: List[str]) -> Optional[Path]:
    if not isinstance(value, str) or not value.strip():
        errors.append("%s missing or not a non-empty string" % label)
        return None
    candidate = Path(value)
    if not candidate.is_absolute():
        errors.append("%s must be an absolute path" % label)
        return None
    try:
        return candidate.resolve()
    except OSError as exc:
        errors.append("%s cannot be resolved: %s" % (label, exc))
        return None


def _portable_component(value: Any, label: str, errors: List[str]) -> Optional[str]:
    if not isinstance(value, str) or not value or value in {".", ".."} or Path(value).name != value or "/" in value or "\\" in value:
        errors.append("%s missing or not a portable path component" % label)
        return None
    return value


def _verify_control_plane_entries(optimizer_root: Path, frozen: Dict[str, Any]) -> List[str]:
    errors: List[str] = []
    raw_entries = frozen.get("entries")
    if not isinstance(raw_entries, list):
        return ["control-plane manifest entries missing or not a list"]
    expected: Dict[str, Dict[str, Any]] = {}
    for index, entry in enumerate(raw_entries, 1):
        if not isinstance(entry, dict):
            errors.append("control-plane manifest entry %d is not an object" % index)
            continue
        relative = entry.get("path")
        if not isinstance(relative, str) or not relative or Path(relative).is_absolute() or ".." in Path(relative).parts or "\\" in relative:
            errors.append("unsafe control-plane manifest path at entry %d" % index)
            continue
        if relative in expected:
            errors.append("duplicate control-plane manifest path: %s" % relative)
            continue
        expected[relative] = entry
    if errors:
        return errors

    actual_entries: List[Dict[str, Any]] = []
    try:
        actual_files = _walk_control_plane_files(
            optimizer_root,
            max_files=max(20000, len(expected) + 1024),
            max_dirs=max(20000, len(expected) * 4 + 1024),
            max_bytes=max(2147483648, sum(int(item.get("bytes", 0)) for item in expected.values() if isinstance(item.get("bytes"), int)) + 268435456),
        )
    except Exception as exc:
        return ["cannot inspect stable control plane: %s" % exc]

    actual_paths = {path.relative_to(optimizer_root).as_posix(): path for path in actual_files}
    for relative in sorted(set(expected) - set(actual_paths)):
        errors.append("stable control-plane file missing: %s" % relative)
    for relative in sorted(set(actual_paths) - set(expected)):
        errors.append("stable control-plane file added after freeze: %s" % relative)
    for relative in sorted(set(expected) & set(actual_paths)):
        path = actual_paths[relative]
        entry = expected[relative]
        size = path.stat().st_size
        if isinstance(entry.get("bytes"), bool) or not isinstance(entry.get("bytes"), int) or entry.get("bytes") != size:
            errors.append("stable control-plane file size mismatch: %s" % relative)
        digest = sha256_file(path)
        if entry.get("sha256") != digest:
            errors.append("stable control-plane file hash mismatch: %s" % relative)
        actual_entries.append({"path": relative, "sha256": digest, "bytes": size})
    if not errors and _tree_hash_from_entries(actual_entries) != frozen.get("optimizer_tree_hash"):
        errors.append("stable optimizer tree hash differs from frozen manifest")
    return errors


def _run_immutable_projection(run: Dict[str, Any]) -> Dict[str, Any]:
    target = _mapping(run.get("target"))
    candidates = []
    raw_candidates = target.get("candidates") if isinstance(target.get("candidates"), list) else []
    for raw_item in raw_candidates:
        item = _mapping(raw_item)
        candidates.append({
            "candidate_id": item.get("candidate_id"),
            "strategy": item.get("strategy"),
            "path": item.get("path"),
            "initial_tree_hash": item.get("initial_tree_hash"),
        })
    return {
        "schema_version": run.get("schema_version"),
        "run_id": run.get("run_id"),
        "mode": run.get("mode"),
        "created_at": run.get("created_at"),
        "started_epoch": run.get("started_epoch"),
        "valid_as_of": run.get("valid_as_of"),
        "valid_as_of_source": run.get("valid_as_of_source"),
        "genesis": run.get("genesis"),
        "stable": run.get("stable"),
        "target": {
            "name": target.get("name"),
            "baseline_path": target.get("baseline_path"),
            "baseline_tree_hash": target.get("baseline_tree_hash"),
            "candidates": candidates,
        },
        "control_plane": run.get("control_plane"),
        "release_profile": run.get("release_profile"),
        "resolved_release_profile": run.get("resolved_release_profile"),
        "release_profile_contract": run.get("release_profile_contract"),
        "review_attestation_contract": run.get("review_attestation_contract"),
        "authority_contract": run.get("authority_contract"),
        "budget": run.get("budget"),
        "authority": run.get("authority"),
    }


def _write_run_seal(workspace: Path, run: Dict[str, Any]) -> Dict[str, Any]:
    projection = _run_immutable_projection(run)
    seal = {
        "schema_version": "1.0",
        "run_id": run["run_id"],
        "projection": projection,
        "projection_sha256": sha256_bytes(canonical_json(projection)),
        "created_at": utc_now(),
    }
    path = workspace / "control/contracts/run-seal.json"
    write_json(path, seal)
    try:
        path.chmod(0o444)
    except OSError:
        pass
    return seal


def verify_run_seal(workspace: Path, run: Optional[Dict[str, Any]] = None) -> List[str]:
    workspace = workspace.resolve()
    errors: List[str] = []
    if run is None:
        try:
            run = load_json(workspace / "run.json")
        except Exception as exc:
            return ["invalid run contract: %s" % exc]
    if not isinstance(run, dict):
        return ["run contract must be an object"]
    seal_path = workspace / "control/contracts/run-seal.json"
    if not seal_path.is_file() or seal_path.is_symlink():
        return ["run seal missing or linked"]
    try:
        seal = load_json(seal_path)
    except Exception as exc:
        return ["invalid run seal: %s" % exc]
    if not isinstance(seal, dict):
        return ["invalid run seal: expected an object"]
    projection = _run_immutable_projection(run)
    digest = sha256_bytes(canonical_json(projection))
    if seal.get("run_id") != run.get("run_id"):
        errors.append("run seal run_id mismatch")
    if seal.get("projection") != projection or seal.get("projection_sha256") != digest:
        errors.append("immutable run contract changed after initialization")

    target = run.get("target")
    if not isinstance(target, dict):
        errors.append("run target contract missing or not an object")
        target = {}
    target_name = _portable_component(target.get("name"), "target name", errors)
    baseline = _required_absolute_path(target.get("baseline_path"), "baseline path", errors)
    if target_name is not None and baseline is not None:
        expected_baseline = (workspace / "target/baseline" / target_name).resolve()
        if baseline != expected_baseline:
            errors.append("baseline path escaped its canonical workspace location")
    raw_candidates = target.get("candidates")
    if not isinstance(raw_candidates, list) or not raw_candidates:
        errors.append("candidate contract missing or not a non-empty list")
        raw_candidates = []
    seen_candidates = set()
    for index, raw_item in enumerate(raw_candidates, 1):
        if not isinstance(raw_item, dict):
            errors.append("candidate contract %d is not an object" % index)
            continue
        candidate_id = _portable_component(raw_item.get("candidate_id"), "candidate id", errors)
        candidate = _required_absolute_path(raw_item.get("path"), "candidate path", errors)
        if candidate_id is not None:
            if candidate_id in seen_candidates:
                errors.append("duplicate candidate id: %s" % candidate_id)
            seen_candidates.add(candidate_id)
        if target_name is not None and candidate_id is not None and candidate is not None:
            expected = (workspace / "target/candidates" / candidate_id / target_name).resolve()
            if candidate != expected:
                errors.append("candidate path escaped its canonical workspace location: %s" % candidate_id)

    def verify_binding(binding: Any, expected: Path, label: str, required: bool = False) -> None:
        if binding is None and not required:
            return
        if not isinstance(binding, dict):
            errors.append("%s binding missing or not an object" % label)
            return
        supplied = _required_absolute_path(binding.get("path"), "%s path" % label, errors)
        if supplied is None:
            return
        if supplied != expected.resolve():
            errors.append("%s path escaped canonical location" % label)
        elif not expected.is_file() or expected.is_symlink():
            errors.append("%s missing or linked" % label)
        elif binding.get("sha256") != sha256_file(expected):
            errors.append("%s changed after initialization" % label)

    verify_binding(run.get("release_profile_contract"), workspace / "control/contracts/release-profile-contract.json", "custom release profile contract")
    verify_binding(run.get("review_attestation_contract"), workspace / "control/contracts/review-attestation-contract.json", "review attestation contract")
    verify_binding(run.get("authority_contract"), workspace / "control/contracts/authority-contract.json", "authority contract", required=True)

    control = run.get("control_plane")
    if not isinstance(control, dict):
        errors.append("control-plane contract missing or not an object")
        control = {}
    optimizer_root = _required_absolute_path(control.get("optimizer_root"), "optimizer root", errors)
    if optimizer_root is not None and (workspace == optimizer_root or workspace in optimizer_root.parents or optimizer_root in workspace.parents):
        errors.append("optimizer root and workspace are not isolated")
    return errors


def verify_control_plane(workspace: Path, run: Optional[Dict[str, Any]] = None) -> List[str]:
    workspace = workspace.resolve()
    if run is None:
        try:
            run = load_json(workspace / "run.json")
        except Exception as exc:
            return ["invalid run contract: %s" % exc]
    if not isinstance(run, dict):
        return ["run contract must be an object"]
    errors: List[str] = []
    control = run.get("control_plane")
    if not isinstance(control, dict):
        return ["control-plane contract missing or not an object"]
    manifest_path = workspace / "control/contracts/control-plane-manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        return ["control-plane manifest missing or linked"]
    try:
        frozen = load_json(manifest_path)
    except Exception as exc:
        return ["invalid control-plane manifest: %s" % exc]
    if not isinstance(frozen, dict):
        return ["invalid control-plane manifest: expected an object"]
    supplied_digest = frozen.get("manifest_sha256")
    payload = dict(frozen)
    payload.pop("manifest_sha256", None)
    if supplied_digest != sha256_bytes(canonical_json(payload)):
        errors.append("control-plane manifest self-hash mismatch")
    expected_manifest_hash = control.get("manifest_file_sha256")
    if not isinstance(expected_manifest_hash, str) or expected_manifest_hash != sha256_file(manifest_path):
        errors.append("control-plane manifest file hash mismatch")

    optimizer_root = _required_absolute_path(control.get("optimizer_root"), "optimizer root", errors)
    frozen_root = _required_absolute_path(frozen.get("optimizer_root"), "frozen optimizer root", errors)
    if optimizer_root is None or frozen_root is None:
        return errors
    if optimizer_root != frozen_root:
        errors.append("optimizer root differs from frozen control-plane manifest")
        return errors
    if control.get("optimizer_tree_hash") != frozen.get("optimizer_tree_hash"):
        errors.append("control-plane contract tree hash differs from frozen manifest")
        return errors
    errors.extend(_verify_control_plane_entries(optimizer_root, frozen))
    return errors



def reconcile_state_with_ledger(workspace: Path, run: Optional[Dict[str, Any]] = None, state: Optional[Dict[str, Any]] = None) -> List[str]:
    """Rebuild mutable state from the append-only ledger and compare it.

    The hash chain alone only proves internal ordering. This reconciliation
    prevents an operator or Candidate from resetting counters, elapsed time,
    saturation state, or review/change counts by editing state.json directly.
    """
    workspace = workspace.resolve()
    errors: List[str] = []
    run = run or load_json(workspace / "run.json")
    state = state or load_json(workspace / "state.json")
    events, chain_errors = read_events(workspace / "events.jsonl")
    errors.extend(chain_errors)
    if not events:
        return errors
    first = events[0]
    if first.get("type") != "RUN_INITIALIZED" or first.get("run_id") != run.get("run_id"):
        errors.append("event ledger does not begin with this run's initialization")
    expected_candidates = [item.get("candidate_id") for item in run.get("target", {}).get("candidates", [])]
    if first.get("candidate_ids") != expected_candidates:
        errors.append("initial event candidate set differs from immutable run")
    if first.get("baseline_tree_hash") != run.get("target", {}).get("baseline_tree_hash"):
        errors.append("initial event baseline hash differs from immutable run")

    counters: Dict[str, Any] = {"network_requests": 0, "projects": 0, "evaluations": 0, "model_calls": 0, "tokens": 0, "cost": 0.0}
    rounds = 0
    changes = 0
    resets = 0
    consecutive_no_gain = 0
    status = "INITIALIZED"
    for event in events[1:]:
        kind = event.get("type")
        if kind == "CHANGE_RECORDED":
            changes += 1
            decision = event.get("decision")
            if decision not in VALID_DECISIONS:
                errors.append("change event has invalid decision")
            consecutive_no_gain = consecutive_no_gain + 1 if decision in {"REVERT", "NO_CHANGE"} else 0
            architecture_reset = event.get("architecture_reset", False)
            if not isinstance(architecture_reset, bool):
                errors.append("change event architecture_reset is not boolean")
            elif architecture_reset:
                resets += 1
            status = "ITERATING"
        elif kind == "ROUND_RECORDED":
            rounds += 1
            if event.get("round") != rounds:
                errors.append("round event sequence is not contiguous")
        elif kind == "BUDGET_CONSUMED":
            increments = event.get("increments")
            observed = event.get("counters")
            if not isinstance(increments, dict) or not isinstance(observed, dict):
                errors.append("budget event lacks increments/counters")
                continue
            if set(increments) - set(counters):
                errors.append("budget event contains unknown counter")
                continue
            for key, value in increments.items():
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)) or value < 0:
                    errors.append("budget event contains invalid increment: %s" % key)
                    continue
                counters[key] += value
            if observed != counters:
                errors.append("budget event cumulative counters are inconsistent")
        elif kind == "STATE_TRANSITION":
            if event.get("from") != status:
                errors.append("state transition source differs from event-derived state")
            destination = str(event.get("to", ""))
            if destination not in ALLOWED_TRANSITIONS.get(status, set()):
                errors.append("event ledger contains an invalid state transition")
            else:
                status = destination
        elif kind != "RUN_INITIALIZED":
            errors.append("unknown event type: %s" % kind)

    expected = {
        "rounds_completed": rounds,
        "changes_recorded": changes,
        "architecture_resets_used": resets,
        "consecutive_no_gain": consecutive_no_gain,
        "counters": counters,
        "status": status,
        "phase": status,
        "started_epoch": run.get("started_epoch"),
    }
    for key, value in expected.items():
        if state.get(key) != value:
            errors.append("state %s differs from the append-only event ledger" % key)
    return errors

def _chmod_read_only(root: Path) -> None:
    for path in sorted(root.rglob("*"), reverse=True):
        try:
            if path.is_dir():
                path.chmod(0o555)
            else:
                path.chmod(0o444)
        except OSError:
            pass
    try:
        root.chmod(0o555)
    except OSError:
        pass


def _workspace_size(root: Path) -> int:
    return sum(path.stat().st_size for path in iter_files(root) if not path.is_symlink())


def _load_budget(path: Optional[Path]) -> Dict[str, Any]:
    result: Dict[str, Any] = dict(DEFAULT_BUDGET)
    if path:
        supplied = load_json(path)
        if not isinstance(supplied, dict):
            raise ValueError("budget file must contain an object")
        unknown = set(supplied) - set(result)
        if unknown:
            raise ValueError("unknown budget keys: %s" % sorted(unknown))
        result.update(supplied)

    integer_keys = set(result) - {"max_cost"}
    normalized: Dict[str, Any] = {}
    for key, value in result.items():
        if isinstance(value, bool):
            raise ValueError("budget values cannot be booleans: %s" % key)
        if key in integer_keys:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError("budget must be an integer: %s" % key)
            if isinstance(value, str) and not value.strip().isdigit():
                raise ValueError("budget must be an integer: %s" % key)
            try:
                number = int(value)
            except (TypeError, ValueError):
                raise ValueError("budget must be an integer: %s" % key)
            if number < 0:
                raise ValueError("budget cannot be negative: %s" % key)
            normalized[key] = number
        else:
            try:
                number_f = float(value)
            except (TypeError, ValueError):
                raise ValueError("budget must be numeric: %s" % key)
            if not math.isfinite(number_f) or number_f < 0:
                raise ValueError("budget must be finite and non-negative: %s" % key)
            normalized[key] = number_f
    if normalized["mandatory_review_rounds"] != 10:
        raise ValueError("Genesis requires exactly ten mandatory system-review perspectives")
    if normalized["max_total_rounds"] < 10:
        raise ValueError("max_total_rounds cannot be below ten")
    return normalized


def _candidate_id(strategy: str, index: int) -> str:
    return "%02d-%s" % (index, strategy)


def _resolve_valid_as_of(value: Optional[str], timezone_name: str = "") -> Tuple[str, str]:
    if value:
        try:
            parsed = dt.date.fromisoformat(value)
        except ValueError:
            raise ValueError("valid_as_of must be YYYY-MM-DD")
        return parsed.isoformat(), "explicit"
    if timezone_name:
        if ZoneInfo is None:
            raise ValueError("timezone support unavailable; pass --valid-as-of explicitly")
        try:
            zone = ZoneInfo(timezone_name)
        except Exception as exc:
            raise ValueError("invalid timezone %s: %s" % (timezone_name, exc))
        return dt.datetime.now(zone).date().isoformat(), "timezone:%s" % timezone_name
    return dt.datetime.now().astimezone().date().isoformat(), "runtime-local-timezone"


def _validate_review_attestation_contract(
    contract_path: Path,
    *,
    workspace: Path,
    target: Path,
    optimizer_root: Path,
) -> Dict[str, Any]:
    """Validate a user/runtime supplied external trust adapter contract.

    Local JSON declarations cannot prove that twelve agents were independent.
    A formal promotion therefore requires a frozen adapter outside the target,
    optimizer, and run workspace. The adapter is still a trust boundary, but it
    is explicit, hash-bound, replaceable, and auditable instead of being
    silently inferred from self-authored IDs.
    """
    source = contract_path.resolve()
    if not source.is_file():
        raise ValueError("review attestation contract does not exist")
    contract = load_json(source)
    if not isinstance(contract, dict) or contract.get("status") != "FROZEN":
        raise ValueError("review attestation contract must be a FROZEN JSON object")
    if contract.get("schema_version") != "1.0" or not contract.get("provider"):
        raise ValueError("review attestation contract identity is incomplete")
    adapter = Path(str(contract.get("adapter_path", ""))).expanduser()
    receipt_root = Path(str(contract.get("receipt_root", ""))).expanduser()
    if not adapter.is_absolute() or not receipt_root.is_absolute():
        raise ValueError("review adapter and receipt root must be absolute paths")
    adapter, receipt_root = adapter.resolve(), receipt_root.resolve()
    protected = [workspace, target, optimizer_root]
    ensure_external(adapter, protected, "review attestation adapter")
    ensure_external(receipt_root, protected, "review receipt root")
    if not adapter.is_file():
        raise ValueError("review attestation adapter is missing")
    if sha256_file(adapter) != contract.get("adapter_sha256"):
        raise ValueError("review attestation adapter hash mismatch")
    if not receipt_root.is_dir():
        raise ValueError("review receipt root is missing")
    capabilities = contract.get("capabilities")
    if not isinstance(capabilities, list) or not {"independent-subagents", "read-only-verifier"}.issubset(set(capabilities)):
        raise ValueError("review attestation adapter lacks mandatory capabilities")
    timeout = contract.get("timeout_seconds", 15)
    if not isinstance(timeout, int) or timeout < 1 or timeout > 120:
        raise ValueError("review attestation timeout must be between 1 and 120 seconds")
    # Canonicalize external paths in the frozen copy so later comparison does
    # not depend on the caller's current working directory.
    contract = dict(contract)
    contract["adapter_path"] = str(adapter)
    contract["receipt_root"] = str(receipt_root)
    return contract


def init_run(target: Path, workspace: Path, optimizer_root: Path, strategies: Iterable[str], budget_path: Optional[Path] = None, self_evolve: bool = False, release_profile: str = "auto", valid_as_of: Optional[str] = None, timezone_name: str = "", release_profile_contract_path: Optional[Path] = None, review_attestation_contract_path: Optional[Path] = None) -> Dict[str, Any]:
    target, workspace, optimizer_root = target.resolve(), workspace.resolve(), optimizer_root.resolve()
    if os.environ.get("WBI_ACTIVE_RUN_ID"):
        raise ValueError("recursive WBI run detected; close or reheat the active run instead of nesting")
    if not target.is_dir():
        raise ValueError("target Skill does not exist: %s" % target)
    ensure_external(workspace, [target, optimizer_root], "workspace")
    if workspace.exists() and any(workspace.iterdir()):
        raise ValueError("workspace must be absent or empty")
    workspace.mkdir(parents=True, exist_ok=True)
    strategies_list = list(dict.fromkeys(str(item).strip() for item in strategies if str(item).strip())) or list(DEFAULT_STRATEGIES)
    invalid_strategies = [item for item in strategies_list if len(item) > 64 or not STRATEGY_RE.fullmatch(item)]
    if invalid_strategies:
        raise ValueError("invalid candidate strategy identifier(s): %s" % invalid_strategies)
    budget = _load_budget(budget_path)
    if len(strategies_list) > int(budget["max_candidates"]):
        raise ValueError("candidate strategies exceed max_candidates budget")

    release_profile = str(release_profile).strip()
    if len(release_profile) > 64 or (release_profile != "auto" and not STRATEGY_RE.fullmatch(release_profile)):
        raise ValueError("invalid release profile identifier")
    builtin_profiles = {"auto", "public", "internal", "infrastructure", "method"}
    custom_profile_contract: Optional[Dict[str, Any]] = None
    if release_profile not in builtin_profiles:
        if release_profile_contract_path is None:
            raise ValueError("custom release profile requires --release-profile-contract")
        custom_profile_contract = load_json(release_profile_contract_path.resolve())
        required = custom_profile_contract.get("required_profile_evidence") if isinstance(custom_profile_contract, dict) else None
        if (
            not isinstance(custom_profile_contract, dict)
            or custom_profile_contract.get("status") != "FROZEN"
            or custom_profile_contract.get("profile") != release_profile
            or not isinstance(required, list)
            or not required
            or any(not isinstance(item, str) or len(item) > 64 or not STRATEGY_RE.fullmatch(item) for item in required)
            or not custom_profile_contract.get("rationale")
        ):
            raise ValueError("invalid custom release profile contract")
    elif release_profile_contract_path is not None:
        raise ValueError("release profile contract is only valid for a custom profile")

    review_attestation_contract: Optional[Dict[str, Any]] = None
    if review_attestation_contract_path is not None:
        review_attestation_contract = _validate_review_attestation_contract(
            review_attestation_contract_path,
            workspace=workspace,
            target=target,
            optimizer_root=optimizer_root,
        )

    genesis = verify_genesis(optimizer_root)
    if genesis["status"] != "PASS":
        raise ValueError("optimizer Genesis verification failed: %s" % genesis["errors"])
    from .luban import resolve_release_profile
    resolved_release_profile = resolve_release_profile({"release_profile": release_profile}, target)
    resolved_valid_as_of, valid_as_of_source = _resolve_valid_as_of(valid_as_of, timezone_name)
    started_epoch = int(time.time())
    run_id = "wbi-%s-%s" % (time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(started_epoch)), uuid.uuid4().hex[:10])
    target_name = target.name
    baseline_root = workspace / "target" / "baseline" / target_name
    copy_clean(target, baseline_root)
    baseline_hash = sha256_tree(baseline_root, exclude={"MANIFEST.sha256"})
    _chmod_read_only(baseline_root)

    candidate_records = []
    for index, strategy in enumerate(strategies_list, 1):
        cid = _candidate_id(strategy, index)
        candidate_root = workspace / "target" / "candidates" / cid / target_name
        copy_clean(target, candidate_root)
        snapshot = workspace / "snapshots" / cid / "000-baseline" / target_name
        copy_clean(target, snapshot)
        _chmod_read_only(snapshot)
        candidate_records.append({
            "candidate_id": cid,
            "strategy": strategy,
            "path": str(candidate_root),
            "initial_tree_hash": sha256_tree(candidate_root, exclude={"MANIFEST.sha256"}),
            "current_tree_hash": sha256_tree(candidate_root, exclude={"MANIFEST.sha256"}),
            "change_count": 0,
            "architecture_resets": 0,
            "status": "ACTIVE",
            "rollback_pointer": str(snapshot),
        })

    control_manifest = _control_plane_manifest(optimizer_root)
    run = {
        "schema_version": "1.0",
        "run_id": run_id,
        "mode": "SELF_EVOLUTION" if self_evolve else "TARGET_EVOLUTION",
        "created_at": utc_now(),
        "started_epoch": started_epoch,
        "valid_as_of": resolved_valid_as_of,
        "valid_as_of_source": valid_as_of_source,
        "genesis": {"baseline_id": genesis["baseline_id"], "baseline_hash": genesis["locked_sha256"]},
        "stable": {"path": str(target), "version": (target / "VERSION").read_text(encoding="utf-8").strip() if (target / "VERSION").is_file() else "UNKNOWN", "tree_hash": sha256_tree(target, exclude={"MANIFEST.sha256"})},
        "target": {"name": target_name, "baseline_path": str(baseline_root), "baseline_tree_hash": baseline_hash, "candidates": candidate_records},
        "control_plane": {"optimizer_root": str(optimizer_root), "optimizer_tree_hash": control_manifest["optimizer_tree_hash"], "manifest_file_sha256": "PENDING", "candidate_may_modify": False},
        "release_profile": release_profile,
        "resolved_release_profile": resolved_release_profile,
        "release_profile_contract": None,
        "review_attestation_contract": None,
        "authority_contract": None,
        "budget": budget,
        "authority": {"reversible_candidate_actions": "AUTHORIZED", "remote_write_or_destructive_actions": "REQUIRES_EXPLICIT_AUTHORIZATION"},
    }
    state = {
        "schema_version": "1.0", "run_id": run_id, "status": "INITIALIZED", "phase": "INITIALIZED",
        "rounds_completed": 0, "changes_recorded": 0, "architecture_resets_used": 0, "consecutive_no_gain": 0,
        "counters": {"network_requests": 0, "projects": 0, "evaluations": 0, "model_calls": 0, "tokens": 0, "cost": 0.0},
        "started_epoch": started_epoch, "updated_at": utc_now(), "stop_reason": None,
    }
    for relative in [
        "control/contracts", "control/evals", "control/holdout", "evidence/research", "evidence/changes",
        "evidence/evals/raw", "evidence/evals/summary", "rounds", "reviews/panel-1", "reviews/panel-2", "verifier", "failed-candidates", "release",
    ]:
        (workspace / relative).mkdir(parents=True, exist_ok=True)
    if custom_profile_contract is not None:
        profile_contract_path = workspace / "control/contracts/release-profile-contract.json"
        write_json(profile_contract_path, custom_profile_contract)
        try:
            profile_contract_path.chmod(0o444)
        except OSError:
            pass
        run["release_profile_contract"] = {
            "path": str(profile_contract_path),
            "sha256": sha256_file(profile_contract_path),
            "profile": release_profile,
        }
    if review_attestation_contract is not None:
        attestation_contract_path = workspace / "control/contracts/review-attestation-contract.json"
        write_json(attestation_contract_path, review_attestation_contract)
        try:
            attestation_contract_path.chmod(0o444)
        except OSError:
            pass
        run["review_attestation_contract"] = {
            "path": str(attestation_contract_path),
            "sha256": sha256_file(attestation_contract_path),
            "provider": review_attestation_contract.get("provider"),
        }
    control_manifest_path = workspace / "control/contracts/control-plane-manifest.json"
    write_json(control_manifest_path, control_manifest)
    run["control_plane"]["manifest_file_sha256"] = sha256_file(control_manifest_path)
    write_json(workspace / "run.json", run)
    write_json(workspace / "state.json", state)
    (workspace / "control/holdout/README.md").write_text(
        "Sealed holdout content must live outside every candidate-readable installation. Store only dataset ID/hash and returned results here.\n",
        encoding="utf-8",
    )
    write_json(workspace / "control/contracts/run-contract.json", {
        "schema_version": "1.0", "run_id": run_id,
        "goal": "", "scope": [], "non_goals": [], "hard_requirements": [], "knowns": [], "unknowns": [],
        "dependencies": [], "risks": [], "acceptance_criteria": [], "user_constraints": [],
    })
    (workspace / "control/evals/README.md").write_text(
        "No active evaluation contract exists until `seal-eval` writes evaluation-contract.json and its immutable seal.\n",
        encoding="utf-8",
    )
    from .security import default_authority_contract
    authority_path = workspace / "control/contracts/authority-contract.json"
    write_json(authority_path, default_authority_contract(run))
    try:
        authority_path.chmod(0o444)
    except OSError:
        pass
    run["authority_contract"] = {"path": str(authority_path), "sha256": sha256_file(authority_path)}
    write_json(workspace / "run.json", run)
    seal = _write_run_seal(workspace, run)
    append_event(workspace / "events.jsonl", {"type": "RUN_INITIALIZED", "run_id": run_id, "baseline_tree_hash": baseline_hash, "candidate_ids": [item["candidate_id"] for item in candidate_records], "run_seal_sha256": seal["projection_sha256"], "control_plane_manifest_sha256": control_manifest["manifest_sha256"], "actor_id": "stable-optimizer"})
    return run


def _diff_trees(before: Path, after: Path) -> Tuple[str, List[str]]:
    before_map = {path.relative_to(before).as_posix(): path for path in iter_files(before) if not path.is_symlink()}
    after_map = {path.relative_to(after).as_posix(): path for path in iter_files(after) if not path.is_symlink()}
    changed: List[str] = []
    chunks: List[str] = []
    for relative in sorted(set(before_map) | set(after_map)):
        left, right = before_map.get(relative), after_map.get(relative)
        left_hash = sha256_file(left) if left else None
        right_hash = sha256_file(right) if right else None
        if left_hash == right_hash:
            continue
        changed.append(relative)
        if left and right and left.suffix.lower() in {".md", ".txt", ".json", ".jsonl", ".py", ".sh", ".yaml", ".yml", ".toml", ".html", ".css", ".js"} and left.stat().st_size < 2 * 1024 * 1024 and right.stat().st_size < 2 * 1024 * 1024:
            a = left.read_text(encoding="utf-8", errors="replace").splitlines()
            b = right.read_text(encoding="utf-8", errors="replace").splitlines()
            chunks.extend(difflib.unified_diff(a, b, fromfile="a/" + relative, tofile="b/" + relative, lineterm=""))
        else:
            chunks.append("BINARY_OR_LARGE %s %s -> %s" % (relative, left_hash or "ABSENT", right_hash or "ABSENT"))
    return "\n".join(chunks) + ("\n" if chunks else ""), changed


def _candidate(run: Dict[str, Any], candidate_id: str) -> Dict[str, Any]:
    for item in run["target"]["candidates"]:
        if item["candidate_id"] == candidate_id:
            return item
    raise ValueError("unknown candidate_id: %s" % candidate_id)


def record_change(workspace: Path, candidate_id: str, record_input: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    errors = verify_event_chain(workspace / "events.jsonl")
    errors.extend(verify_run_seal(workspace, run))
    errors.extend(verify_control_plane(workspace, run))
    errors.extend(reconcile_state_with_ledger(workspace, run, state))
    if errors:
        raise ValueError("run integrity failed verification: %s" % errors)
    candidate = _candidate(run, candidate_id)
    candidate_root = Path(candidate["path"])
    baseline_root = Path(run["target"]["baseline_path"])
    if sha256_tree(baseline_root, exclude={"MANIFEST.sha256"}) != run["target"]["baseline_tree_hash"]:
        raise ValueError("baseline changed during run")
    supplied = load_json(record_input)
    for key in ["hypothesis", "evidence_paths", "actor_id", "commands", "tools", "risk", "decision"]:
        if key not in supplied:
            raise ValueError("change record missing %s" % key)
    decision = str(supplied["decision"]).upper()
    if decision not in VALID_DECISIONS:
        raise ValueError("invalid decision")
    architecture_reset = supplied.get("architecture_reset", False)
    if not isinstance(architecture_reset, bool):
        raise ValueError("architecture_reset must be boolean")
    evidence_bindings = bind_files(workspace, supplied["evidence_paths"], label="change evidence")
    raw_result_paths = supplied.get("raw_result_paths", [])
    raw_result_bindings = bind_files(workspace, raw_result_paths, label="raw result") if raw_result_paths else []
    previous_snapshot = Path(candidate["rollback_pointer"]).resolve()
    snapshots_root = (workspace / "snapshots").resolve()
    if snapshots_root not in previous_snapshot.parents:
        raise ValueError("rollback pointer escaped the governed snapshot store")
    if not previous_snapshot.is_dir():
        raise ValueError("rollback snapshot missing")
    previous_hash = candidate["current_tree_hash"]
    snapshot_hash = sha256_tree(previous_snapshot, exclude={"MANIFEST.sha256"})
    if snapshot_hash != previous_hash:
        raise ValueError("rollback snapshot hash does not match candidate ledger")
    current_hash = sha256_tree(candidate_root, exclude={"MANIFEST.sha256"})
    diff, changed_files = _diff_trees(previous_snapshot, candidate_root)
    if decision in {"KEEP", "REVERT"} and current_hash == previous_hash:
        raise ValueError("%s requires an actual candidate change" % decision)
    if decision == "NO_CHANGE" and current_hash != previous_hash:
        raise ValueError("NO_CHANGE requires an unchanged candidate")
    change_number = int(candidate["change_count"]) + 1
    change_id = str(supplied.get("change_id") or "%s-change-%03d" % (candidate_id, change_number))
    if not CHANGE_ID_RE.fullmatch(change_id):
        raise ValueError("change_id must be a portable 1..128 character identifier")
    diff_path = workspace / "evidence/changes" / (change_id + ".diff")
    diff_path.write_text(diff, encoding="utf-8")
    diff_relative = diff_path.relative_to(workspace).as_posix()
    diff_binding = {"path": diff_relative, "sha256": sha256_file(diff_path), "bytes": diff_path.stat().st_size}
    if decision == "REVERT":
        failed_dir = workspace / "failed-candidates" / change_id / candidate_root.name
        copy_clean(candidate_root, failed_dir)
        copy_clean(previous_snapshot, candidate_root)
        final_hash = sha256_tree(candidate_root, exclude={"MANIFEST.sha256"})
        rollback_pointer = str(previous_snapshot)
    else:
        final_hash = current_hash
        snapshot = workspace / "snapshots" / candidate_id / ("%03d-%s" % (change_number, decision.lower())) / candidate_root.name
        copy_clean(candidate_root, snapshot)
        _chmod_read_only(snapshot)
        rollback_pointer = str(snapshot)
    record = {
        "schema_version": "1.0", "run_id": run["run_id"], "change_id": change_id, "candidate_id": candidate_id,
        "strategy": candidate["strategy"], "timestamp": utc_now(), "before_tree_hash": previous_hash,
        "observed_tree_hash": current_hash, "after_decision_tree_hash": final_hash, "decision": decision,
        "hypothesis": supplied["hypothesis"], "evidence_bindings": evidence_bindings, "changed_files": changed_files,
        "exact_diff_path": str(diff_path), "exact_diff_binding": diff_binding, "commands": supplied["commands"], "tools": supplied["tools"],
        "models": supplied.get("models", []), "agents": supplied.get("agents", []), "environment": supplied.get("environment", {}),
        "raw_result_bindings": raw_result_bindings, "risk": supplied["risk"], "unknowns": supplied.get("unknowns", []),
        "actor_id": supplied["actor_id"], "rollback_pointer": rollback_pointer,
        "architecture_reset": architecture_reset,
    }
    write_json(workspace / "evidence/changes" / (change_id + ".json"), record)
    candidate["change_count"] = change_number
    candidate["current_tree_hash"] = final_hash
    candidate["rollback_pointer"] = rollback_pointer
    if architecture_reset:
        candidate["architecture_resets"] = int(candidate["architecture_resets"]) + 1
        state["architecture_resets_used"] = int(state["architecture_resets_used"]) + 1
    write_json(workspace / "run.json", run)
    state["changes_recorded"] = int(state.get("changes_recorded", 0)) + 1
    state["phase"] = "ITERATING"
    state["status"] = "ITERATING"
    state["updated_at"] = utc_now()
    state["consecutive_no_gain"] = int(state.get("consecutive_no_gain", 0)) + 1 if decision in {"REVERT", "NO_CHANGE"} else 0
    write_json(workspace / "state.json", state)
    append_event(workspace / "events.jsonl", {"type": "CHANGE_RECORDED", "change_id": change_id, "candidate_id": candidate_id, "decision": decision, "before": previous_hash, "after": final_hash, "architecture_reset": architecture_reset, "actor_id": supplied["actor_id"]})
    return record


def record_round(workspace: Path, round_input: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    integrity = verify_event_chain(workspace / "events.jsonl") + verify_run_seal(workspace, run) + verify_control_plane(workspace, run) + reconcile_state_with_ledger(workspace, run, state)
    if integrity:
        raise ValueError("run integrity failed verification: %s" % integrity)
    supplied = load_json(round_input)
    supplied_number = supplied.get("round", 0)
    if isinstance(supplied_number, bool) or not isinstance(supplied_number, int):
        raise ValueError("round must be an integer")
    number = supplied_number
    expected = int(state.get("rounds_completed", 0)) + 1
    if number != expected:
        raise ValueError("round must be contiguous; expected %d" % expected)
    if number > int(run["budget"]["max_total_rounds"]):
        raise ValueError("round budget exhausted")
    for key in ["perspective", "evidence_paths", "candidate_comparison", "decision", "actor_id", "residual_risk"]:
        if key not in supplied:
            raise ValueError("round record missing %s" % key)
    if str(supplied["decision"]).upper() not in VALID_DECISIONS:
        raise ValueError("invalid round decision")
    if not isinstance(supplied.get("candidate_comparison"), dict) or not supplied["candidate_comparison"]:
        raise ValueError("round candidate_comparison must be a non-empty object")
    if not isinstance(supplied.get("actor_id"), str) or not supplied["actor_id"].strip():
        raise ValueError("round actor_id must be non-empty")
    supplied["decision"] = str(supplied["decision"]).upper()
    supplied["evidence_bindings"] = bind_files(workspace, supplied.pop("evidence_paths"), label="round evidence")
    supplied["schema_version"] = "1.0"
    supplied["run_id"] = run["run_id"]
    supplied["timestamp"] = utc_now()
    write_json(workspace / "rounds" / ("round-%02d.json" % number), supplied)
    state["rounds_completed"] = number
    state["updated_at"] = utc_now()
    write_json(workspace / "state.json", state)
    append_event(workspace / "events.jsonl", {"type": "ROUND_RECORDED", "round": number, "perspective": supplied["perspective"], "decision": supplied["decision"], "actor_id": supplied["actor_id"]})
    return supplied


def update_counters(workspace: Path, increments: Dict[str, Any]) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    integrity = verify_event_chain(workspace / "events.jsonl") + verify_run_seal(workspace, run) + verify_control_plane(workspace, run) + reconcile_state_with_ledger(workspace, run, state)
    if integrity:
        raise ValueError("run integrity failed verification: %s" % integrity)
    allowed = set(state["counters"])
    if not isinstance(increments, dict) or set(increments) - allowed:
        raise ValueError("unknown counters")
    normalized: Dict[str, Any] = {}
    for key, value in increments.items():
        if isinstance(value, bool):
            raise ValueError("counter increments cannot be booleans")
        if key == "cost":
            try:
                number = float(value)
            except (TypeError, ValueError):
                raise ValueError("cost increment must be numeric")
            if not math.isfinite(number) or number < 0:
                raise ValueError("counter increments must be finite and non-negative")
            normalized[key] = number
        else:
            if isinstance(value, float) and not value.is_integer():
                raise ValueError("count increments must be integers")
            try:
                number_i = int(value)
            except (TypeError, ValueError):
                raise ValueError("count increments must be integers")
            if number_i < 0:
                raise ValueError("counter increments must be non-negative")
            normalized[key] = number_i
    for key, value in normalized.items():
        state["counters"][key] = state["counters"].get(key, 0) + value
    state["updated_at"] = utc_now()
    write_json(workspace / "state.json", state)
    append_event(workspace / "events.jsonl", {
        "type": "BUDGET_CONSUMED",
        "increments": normalized,
        "counters": state["counters"],
        "actor_id": "stable-optimizer",
    })
    return loop_status(workspace)


def transition(workspace: Path, status: str, reason: str, actor_id: str) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    integrity = verify_event_chain(workspace / "events.jsonl") + verify_run_seal(workspace, run) + verify_control_plane(workspace, run) + reconcile_state_with_ledger(workspace, run, state)
    if integrity:
        raise ValueError("run integrity failed verification: %s" % integrity)
    current = state["status"]
    status = status.upper()
    if current in TERMINAL:
        raise ValueError("terminal run cannot transition; create a reheat run")
    if status not in ALLOWED_TRANSITIONS.get(current, set()):
        raise ValueError("invalid transition %s -> %s" % (current, status))
    state["status"] = status
    state["phase"] = status
    state["updated_at"] = utc_now()
    if status in TERMINAL:
        state["stop_reason"] = reason
    write_json(workspace / "state.json", state)
    append_event(workspace / "events.jsonl", {"type": "STATE_TRANSITION", "from": current, "to": status, "reason": reason, "actor_id": actor_id})
    return state


def audit_budget(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    budget = run["budget"]
    counters = state["counters"]
    stop_reasons: List[str] = []
    violations: List[str] = []
    mapping = {
        "network_requests": "max_network_requests", "projects": "max_projects", "evaluations": "max_evaluations",
        "model_calls": "max_model_calls", "tokens": "max_tokens", "cost": "max_cost",
    }
    for counter, budget_key in mapping.items():
        used = counters.get(counter, 0)
        limit = budget.get(budget_key, 0)
        if limit == 0:
            if used > 0:
                violations.append("ZERO_BUDGET_EXCEEDED:%s" % counter)
        elif used > limit:
            violations.append("BUDGET_EXCEEDED:%s" % counter)
        elif used >= limit:
            stop_reasons.append("BUDGET_EXHAUSTED:%s" % counter)
    elapsed = int(time.time()) - int(run["started_epoch"])
    wall_limit = int(budget["max_wall_seconds"])
    if elapsed > wall_limit:
        violations.append("BUDGET_EXCEEDED:wall_time")
    elif elapsed >= wall_limit:
        stop_reasons.append("BUDGET_EXHAUSTED:wall_time")
    storage = _workspace_size(workspace)
    storage_limit = int(budget["max_storage_bytes"])
    if storage > storage_limit:
        violations.append("BUDGET_EXCEEDED:storage")
    elif storage >= storage_limit:
        stop_reasons.append("BUDGET_EXHAUSTED:storage")
    rounds = int(state["rounds_completed"])
    round_limit = int(budget["max_total_rounds"])
    if rounds > round_limit:
        violations.append("ROUND_BUDGET_EXCEEDED")
    elif rounds >= round_limit:
        stop_reasons.append("ROUND_BUDGET_EXHAUSTED")
    resets = int(state.get("architecture_resets_used", 0))
    reset_limit = int(budget["max_architecture_resets"])
    if reset_limit == 0 and resets > 0:
        violations.append("ZERO_BUDGET_EXCEEDED:architecture_resets")
    elif resets > reset_limit:
        violations.append("ARCHITECTURE_RESET_BUDGET_EXCEEDED")
    elif reset_limit > 0 and resets >= reset_limit:
        stop_reasons.append("ARCHITECTURE_RESET_BUDGET_EXHAUSTED")
    return {
        "status": "VIOLATION" if violations else ("STOP" if stop_reasons else "CONTINUE"),
        "violations": violations,
        "stop_reasons": stop_reasons,
        "elapsed_seconds": elapsed,
        "storage_bytes": storage,
    }


def loop_status(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    integrity = verify_event_chain(workspace / "events.jsonl") + verify_run_seal(workspace, run) + verify_control_plane(workspace, run) + reconcile_state_with_ledger(workspace, run, state)
    if integrity:
        return {
            "status": "BLOCKED",
            "reasons": ["RUN_INTEGRITY:%s" % item for item in integrity],
            "budget_status": "UNKNOWN",
            "budget_violations": [],
            "mandatory_rounds_remaining": None,
            "rounds_remaining_in_run": None,
            "reheat_allowed": True,
            "state": state.get("status", "UNKNOWN"),
            "counters": state.get("counters", {}),
        }
    audit = audit_budget(workspace)
    reasons = list(audit["violations"]) + list(audit["stop_reasons"])
    patience = int(run["budget"]["saturation_patience"])
    if patience == 0:
        if int(state.get("consecutive_no_gain", 0)) > 0:
            reasons.append("ZERO_PATIENCE_NO_GAIN")
    elif int(state.get("consecutive_no_gain", 0)) >= patience:
        reasons.append("SATURATION_PATIENCE_REACHED")
    return {
        "status": "STOP" if reasons else "CONTINUE",
        "reasons": sorted(set(reasons)),
        "budget_status": audit["status"],
        "budget_violations": audit["violations"],
        "mandatory_rounds_remaining": max(0, 10 - int(state["rounds_completed"])),
        "rounds_remaining_in_run": max(0, int(run["budget"]["max_total_rounds"]) - int(state["rounds_completed"])),
        "reheat_allowed": True,
        "state": state["status"],
        "counters": state["counters"],
    }
