from __future__ import annotations

import datetime as dt
import json
from pathlib import Path
import re
from typing import Any, Dict, List, Optional

from .competitors import select_peers
from .io import canonical_json, load_json, sha256_bytes, sha256_file, sha256_tree, utc_now, verify_file_bindings, write_json

PREMISE_DECISIONS = {"CONTINUE", "REPOSITION", "MERGE", "SPLIT", "RETIRE"}
QUESTION_IDS = {"real-problem", "unique-value", "install-reason", "observable-artifact"}
BUILTIN_RELEASE_PROFILES = {"public", "internal", "infrastructure", "method"}
PROFILE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$")


def _seal_paths(workspace: Path) -> List[Path]:
    roots = [workspace / "evidence" / "research", workspace / "competitors"]
    paths: List[Path] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.is_file() and path.name != "research-seal.json":
                paths.append(path)
    # Scope and authority are part of the pre-edit evidence contract. They may
    # be completed after init-run, but become immutable with the research seal.
    for relative in ("control/contracts/run-contract.json", "control/contracts/authority-contract.json"):
        path = workspace / relative
        if path.is_file():
            paths.append(path)
    unique = {path.resolve(): path for path in paths}
    return [unique[key] for key in sorted(unique, key=lambda item: item.as_posix())]


RUN_CONTRACT_LIST_FIELDS = (
    "scope", "non_goals", "hard_requirements", "knowns", "unknowns",
    "dependencies", "risks", "acceptance_criteria", "user_constraints",
)
RUN_CONTRACT_NONEMPTY_FIELDS = {
    "scope", "non_goals", "hard_requirements", "acceptance_criteria", "user_constraints",
}


def validate_run_contract(path: Path, expected_run_id: str = "") -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "run contract")
    if not value:
        return errors
    if value.get("schema_version") != "1.0":
        errors.append("run contract schema_version must be 1.0")
    if expected_run_id and value.get("run_id") != expected_run_id:
        errors.append("run contract is not bound to the active run")
    goal = value.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        errors.append("run contract goal is empty")
    for field in RUN_CONTRACT_LIST_FIELDS:
        items = value.get(field)
        if not isinstance(items, list):
            errors.append("run contract %s must be a list" % field)
            continue
        if field in RUN_CONTRACT_NONEMPTY_FIELDS and not items:
            errors.append("run contract %s must be explicit and non-empty" % field)
        if any(not isinstance(item, (str, dict)) or (isinstance(item, str) and not item.strip()) for item in items):
            errors.append("run contract %s contains an empty or invalid item" % field)
    return errors


def _chmod_read_only(path: Path) -> None:
    try:
        path.chmod(0o444)
    except OSError:
        pass


def seal_research(workspace: Path, actor_id: str) -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    state = load_json(workspace / "state.json")
    if int(state.get("changes_recorded", 0)) > 0:
        raise ValueError("research must be sealed before the first candidate change")
    contract_errors = validate_run_contract(workspace / "control/contracts/run-contract.json", str(run.get("run_id", "")))
    from .security import validate_authority
    authority = validate_authority(workspace)
    if authority.get("status") != "PASS":
        contract_errors.extend(["authority: %s" % item for item in authority.get("errors", [])])
    if contract_errors:
        return {"schema_version": "2.0", "run_id": run.get("run_id"), "status": "BLOCKED", "errors": sorted(set(contract_errors)), "files": []}
    research = workspace / "evidence" / "research"
    research.mkdir(parents=True, exist_ok=True)
    files: List[Dict[str, Any]] = []
    for path in _seal_paths(workspace):
        files.append({"path": path.relative_to(workspace).as_posix(), "sha256": sha256_file(path), "bytes": path.stat().st_size})
    files.sort(key=lambda item: item["path"])
    seal = {
        "schema_version": "2.0", "run_id": run["run_id"], "sealed_at": utc_now(), "actor_id": actor_id,
        "target_baseline_tree_hash": run["target"]["baseline_tree_hash"], "candidate_change_count_at_seal": 0,
        "files": files, "files_digest": sha256_bytes(canonical_json(files)), "status": "SEALED" if files else "BLOCKED",
        "errors": [] if files else ["no research evidence to seal"],
    }
    destination = research / "research-seal.json"
    write_json(destination, seal)
    for path in _seal_paths(workspace):
        _chmod_read_only(path)
    _chmod_read_only(destination)
    return seal

def _required(path: Path, errors: List[str], label: str) -> Optional[Dict[str, Any]]:
    if not path.is_file():
        errors.append("missing %s: %s" % (label, path))
        return None
    try:
        value = load_json(path)
    except Exception as exc:
        errors.append("invalid %s: %s" % (label, exc))
        return None
    if not isinstance(value, dict):
        errors.append("%s must be an object" % label)
        return None
    return value


def validate_premise(path: Path, expected_baseline_hash: str = "") -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "premise challenge")
    if not value:
        return errors
    questions = value.get("questions")
    if not isinstance(questions, list) or {item.get("id") for item in questions if isinstance(item, dict)} != QUESTION_IDS or len(questions) != 4:
        errors.append("premise challenge requires the four canonical questions exactly once")
    else:
        for item in questions:
            if not item.get("verdict") or not item.get("evidence"):
                errors.append("premise question %s lacks verdict/evidence" % item.get("id"))
    decision = value.get("decision")
    if decision not in PREMISE_DECISIONS:
        errors.append("invalid premise decision")
    if value.get("completed_before_first_change") is not True:
        errors.append("premise challenge was not completed before first change")
    if expected_baseline_hash and value.get("target_baseline_tree_hash") != expected_baseline_hash:
        errors.append("premise target hash does not match frozen baseline")
    if decision in {"REPOSITION", "MERGE", "SPLIT", "RETIRE"} and not value.get("architecture_or_exit_plan"):
        errors.append("non-CONTINUE decision requires architecture_or_exit_plan")
    if decision == "RETIRE" and value.get("mutation_allowed") is not False:
        errors.append("RETIRE must stop mutation; it does not delete or publish anything")
    return errors


def validate_research_seal(path: Path, expected_baseline_hash: str = "") -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "research seal")
    if not value:
        return errors
    if value.get("status") != "SEALED" or value.get("candidate_change_count_at_seal") != 0:
        errors.append("research was not sealed before candidate mutation")
    if expected_baseline_hash and value.get("target_baseline_tree_hash") != expected_baseline_hash:
        errors.append("research seal baseline mismatch")
    files = value.get("files")
    if not isinstance(files, list) or not files:
        errors.append("research seal lacks frozen evidence files")
        return errors
    if sha256_bytes(canonical_json(files)) != value.get("files_digest"):
        errors.append("research seal file-list digest mismatch")
    workspace = path.resolve().parents[2]
    listed = set()
    for item in files:
        if not isinstance(item, dict) or not all(key in item for key in ("path", "sha256", "bytes")):
            errors.append("research seal contains an incomplete file record")
            continue
        relative = Path(str(item["path"]))
        if relative.is_absolute() or ".." in relative.parts:
            errors.append("research seal contains unsafe path")
            continue
        listed.add(relative.as_posix())
        candidate = (workspace / relative).resolve()
        if workspace != candidate and workspace not in candidate.parents:
            errors.append("research seal path escapes workspace")
        elif not candidate.is_file():
            errors.append("sealed research file missing: %s" % relative.as_posix())
        elif sha256_file(candidate) != item.get("sha256") or candidate.stat().st_size != item.get("bytes"):
            errors.append("sealed research file changed: %s" % relative.as_posix())
    current_required = {item.relative_to(workspace).as_posix() for item in _seal_paths(workspace)}
    if not current_required.issubset(listed):
        errors.append("research files were added after sealing: %s" % sorted(current_required - listed))
    return errors


def validate_mechanism_adoption(path: Path) -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "mechanism adoption ledger")
    if not value:
        return errors
    if value.get("status") != "PASS":
        errors.append("mechanism adoption ledger did not PASS")
    records = value.get("records")
    if not isinstance(records, list):
        errors.append("mechanism adoption records must be a list")
        return errors
    if not records and not value.get("no_adoption_justification"):
        errors.append("mechanism adoption requires records or an evidence-backed no-adoption justification")
    identities = set()
    for index, record in enumerate(records, 1):
        if not isinstance(record, dict):
            errors.append("mechanism adoption record %d invalid" % index)
            continue
        for key in ("source_url", "source_type", "license_status", "mechanism", "adopted_abstraction", "copy_mode", "deliberately_not_adopted", "teleiosis_extension", "verification"):
            if not record.get(key):
                errors.append("mechanism adoption record %d missing %s" % (index, key))
        identity = (record.get("source_url"), record.get("mechanism"))
        if identity in identities:
            errors.append("duplicate mechanism adoption source/mechanism")
        identities.add(identity)
        if record.get("copy_mode") not in {"no-code-copied", "attributed-code-copy"}:
            errors.append("mechanism adoption copy_mode invalid")
        if record.get("copy_mode") == "attributed-code-copy" and not (record.get("license_compatible") is True and record.get("attribution_path")):
            errors.append("attributed code copy lacks verified license compatibility/attribution")
        if not isinstance(record.get("verification"), list) or not record.get("verification"):
            errors.append("mechanism adoption verification must be non-empty")
    return errors

def validate_ecosystem(path: Path) -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "ecosystem position")
    if not value:
        return errors
    vertical = value.get("vertical")
    horizontal = value.get("horizontal")
    strategy = value.get("strategy")
    if not isinstance(vertical, dict) or not all(vertical.get(key) for key in ("origin", "current_form", "next_horizon", "replacement_risks")):
        errors.append("vertical ecosystem analysis incomplete")
    required_horizontal = {"problem_fit", "distinctive_mechanism", "installability", "evidence", "safety", "portability", "efficiency", "maintainability"}
    if not isinstance(horizontal, dict) or not required_horizontal.issubset(horizontal):
        errors.append("horizontal ecosystem analysis lacks required dimensions")
    if not isinstance(strategy, dict) or not all(strategy.get(key) for key in ("avoid_niche", "target_niche", "falsifiable_advantage", "disconfirming_test")):
        errors.append("ecosystem strategy lacks falsifiable positioning")
    return errors


def _validate_observed_date(value: Any, label: str, errors: List[str]) -> None:
    if not isinstance(value, str):
        errors.append("%s observed_at missing" % label)
        return
    try:
        dt.date.fromisoformat(value[:10])
    except ValueError:
        errors.append("%s observed_at must start with an ISO date" % label)


def validate_live_artifacts(path: Path, workspace: Path) -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "live artifact check")
    if not value:
        return errors
    workspace = workspace.resolve()
    if value.get("status") != "PASS":
        errors.append("live artifact check did not PASS")
    if value.get("dry_run_only") is True or value.get("mock_only") is True:
        errors.append("dry-run/mock-only evidence cannot satisfy live artifact gate")
    targets = value.get("target_artifacts")
    peers = value.get("peer_artifacts")
    if not isinstance(targets, list) or not targets:
        errors.append("target live artifacts missing")
    if not isinstance(peers, list) or len(peers) < 2:
        errors.append("at least two peer live artifact observations required")
    identities = set()
    for label, items in (("target", targets or []), ("peer", peers or [])):
        for index, item in enumerate(items, 1):
            prefix = "%s artifact %d" % (label, index)
            if not isinstance(item, dict):
                errors.append("%s invalid" % prefix)
                continue
            artifact_id = item.get("artifact_id")
            if not isinstance(artifact_id, str) or not artifact_id.strip():
                errors.append("%s missing artifact_id" % prefix)
            elif (label, artifact_id) in identities:
                errors.append("duplicate %s artifact_id: %s" % (label, artifact_id))
            identities.add((label, artifact_id))
            for key in ("observation", "freshness"):
                if not isinstance(item.get(key), str) or not item.get(key).strip():
                    errors.append("%s missing %s" % (prefix, key))
            _validate_observed_date(item.get("observed_at"), prefix, errors)
            if item.get("freshness") not in {"current", "current-with-limitations"}:
                errors.append("%s is not current" % prefix)
            reproduction = item.get("reproduction")
            if not isinstance(reproduction, list) or not reproduction or any(not isinstance(step, str) or not step.strip() for step in reproduction):
                errors.append("%s reproduction must be a non-empty command/step list" % prefix)
            relative = item.get("local_path")
            digest = item.get("sha256")
            if not isinstance(relative, str) or not relative.strip():
                errors.append("%s lacks a locally captured artifact path" % prefix)
                continue
            candidate = (workspace / relative).resolve()
            if workspace != candidate and workspace not in candidate.parents:
                errors.append("artifact path escapes workspace")
            elif not candidate.is_file():
                errors.append("artifact file missing: %s" % relative)
            elif not re.fullmatch(r"[a-f0-9]{64}", str(digest or "")) or digest != sha256_file(candidate):
                errors.append("artifact hash mismatch: %s" % relative)
    return errors


def resolve_release_profile(run: Dict[str, Any], candidate_root: Path) -> str:
    profile = str(run.get("release_profile", "auto")).strip()
    if profile != "auto":
        if len(profile) > 64 or not PROFILE_RE.fullmatch(profile):
            raise ValueError("invalid resolved release profile")
        return profile
    if (candidate_root / "assets").exists() or (candidate_root / "showcase").exists():
        return "public"
    skill = (candidate_root / "SKILL.md").read_text(encoding="utf-8", errors="replace").lower()
    if any(token in skill for token in ("governance", "security", "infrastructure", "validator", "deployment")):
        return "infrastructure"
    return "method"


def _custom_release_contract(workspace: Path, profile: str, errors: List[str]) -> Optional[Dict[str, Any]]:
    path = workspace / "control/contracts/release-profile-contract.json"
    value = _required(path, errors, "custom release profile contract")
    if not value:
        return None
    if value.get("status") != "FROZEN" or value.get("profile") != profile:
        errors.append("custom release profile contract mismatch")
    required = value.get("required_profile_evidence")
    if not isinstance(required, list) or not required:
        errors.append("custom release profile contract requires evidence keys")
    elif any(not isinstance(item, str) or len(item) > 64 or not PROFILE_RE.fullmatch(item) for item in required):
        errors.append("custom release profile evidence key invalid")
    if not value.get("rationale"):
        errors.append("custom release profile contract lacks rationale")
    run_path = workspace / "run.json"
    if run_path.is_file():
        run = load_json(run_path)
        binding = run.get("release_profile_contract") or {}
        if binding.get("profile") != profile or binding.get("path") != str(path) or binding.get("sha256") != sha256_file(path):
            errors.append("custom release profile contract is not bound to immutable run contract")
    return value


def _paths_from_profile_value(value: Any) -> List[str]:
    if isinstance(value, str) and value.strip():
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str) and item.strip()]
    return []


def validate_release_readiness(path: Path, profile: str, workspace: Optional[Path] = None) -> List[str]:
    errors: List[str] = []
    value = _required(path, errors, "release readiness")
    if not value:
        return errors
    if len(profile) > 64 or not PROFILE_RE.fullmatch(profile):
        errors.append("invalid resolved release profile")
        return errors
    if value.get("status") != "PASS":
        errors.append("release readiness did not PASS")
    common = {
        "ten_second_value", "shortest_install", "first_invocation", "three_real_scenarios",
        "release_notes", "deterministic_package", "post_install_test", "rollback", "reheat_entry",
    }
    checks = value.get("checks")
    if not isinstance(checks, dict) or set(checks) != common or not all(checks.get(key) is True for key in common):
        errors.append("common release readiness checks must exactly PASS")
    resolved_workspace = workspace.resolve() if workspace else path.resolve().parents[2]
    bindings = value.get("evidence_bindings")
    binding_errors = verify_file_bindings(resolved_workspace, bindings, label="release evidence")
    errors.extend(binding_errors)
    bound_paths = {item.get("path") for item in bindings or [] if isinstance(item, dict)}
    check_evidence = value.get("check_evidence")
    if not isinstance(check_evidence, dict) or set(check_evidence) != common:
        errors.append("every common release check requires explicit evidence paths")
    else:
        for key in common:
            paths = _paths_from_profile_value(check_evidence.get(key))
            if not paths or any(item not in bound_paths for item in paths):
                errors.append("release check %s lacks hash-bound evidence" % key)
    evidence = value.get("profile_evidence")
    if not isinstance(evidence, dict) or evidence.get("profile") != profile:
        errors.append("release profile evidence mismatch")
        return errors
    required_profile_keys: List[str] = []
    if profile == "public":
        required_profile_keys = ["visual_showcase"]
    elif profile == "internal":
        required_profile_keys = ["operator_result_bundle"]
    elif profile == "infrastructure":
        required_profile_keys = ["healthcheck", "runbook", "verification_transcript"]
    elif profile == "method":
        required_profile_keys = ["worked_example", "comparison_result"]
    elif profile not in BUILTIN_RELEASE_PROFILES:
        contract = _custom_release_contract(resolved_workspace, profile, errors)
        required_profile_keys = contract.get("required_profile_evidence", []) if contract else []
    for key in required_profile_keys:
        paths = _paths_from_profile_value(evidence.get(key))
        if not paths or any(item not in bound_paths for item in paths):
            errors.append("%s profile requires hash-bound profile_evidence.%s" % (profile, key))
    return errors


def validate_luban_gates(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    errors: List[str] = []
    warnings: List[str] = []
    run_path = workspace / "run.json"
    if not run_path.is_file():
        return {"status": "BLOCKED", "errors": ["missing run.json"], "warnings": []}
    run = load_json(run_path)
    baseline_hash = run.get("target", {}).get("baseline_tree_hash", "")
    errors.extend(validate_run_contract(workspace / "control/contracts/run-contract.json", str(run.get("run_id", ""))))
    errors.extend(validate_premise(workspace / "evidence/research/premise-challenge.json", baseline_hash))
    errors.extend(validate_research_seal(workspace / "evidence/research/research-seal.json", baseline_hash))
    manifest = _required(workspace / "competitors/dataset-manifest.json", errors, "competitor dataset manifest")
    selection = _required(workspace / "competitors/peer-selection.json", errors, "peer selection")
    dataset = workspace / "competitors/competitor-dataset.jsonl"
    if manifest and selection:
        if not dataset.is_file() or sha256_file(dataset) != manifest.get("dataset_sha256"):
            errors.append("competitor dataset missing or hash mismatch")
        if selection.get("status") != "PASS" or manifest.get("selection_status") != "PASS":
            errors.append("at least five real peers with category/GitHub evidence have not passed")
    errors.extend(validate_mechanism_adoption(workspace / "evidence/research/mechanism-adoption-ledger.json"))
    errors.extend(validate_ecosystem(workspace / "evidence/research/ecosystem-position.json"))
    errors.extend(validate_live_artifacts(workspace / "evidence/validation/live-artifact-check.json", workspace))
    candidates = run.get("target", {}).get("candidates", [])
    candidate_root = Path(candidates[0]["path"]) if candidates else Path(run["target"]["baseline_path"])
    profile = str(run.get("resolved_release_profile") or resolve_release_profile(run, candidate_root))
    if profile != run.get("resolved_release_profile"):
        errors.append("resolved release profile is not frozen into the immutable run contract")
    errors.extend(validate_release_readiness(workspace / "evidence/validation/release-readiness.json", profile, workspace))
    reheat = _required(workspace / "evidence/validation/reheat-plan.json", errors, "reheat plan")
    if reheat and not all(reheat.get(key) for key in ("monitoring", "feedback", "triggers", "known_limits", "validity_policy")):
        errors.append("reheat plan incomplete")
    return {"status": "PASS" if not errors else "BLOCKED", "errors": sorted(set(errors)), "warnings": warnings, "release_profile": profile}
