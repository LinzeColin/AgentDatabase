from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
import uuid
from typing import Any, Dict, List, Tuple

from .io import bind_files, canonical_json, load_json, sha256_bytes, sha256_file, sha256_tree, utc_now, verify_file_bindings, write_json
from .process import run_bounded
from .workspace import verify_control_plane, verify_run_seal

PANEL_ROLES = {
    1: ["competitive-research", "skill-architecture", "evaluation-science", "safety-governance", "runtime-install", "efficiency-maintenance"],
    2: ["red-team", "ambiguity-triggering", "overfitting-negative-transfer", "recovery-rollback", "long-horizon-drift", "governance-boundary"],
}
HARD_DOMAINS = {"genesis", "safety", "truthfulness", "authority", "holdout-integrity", "install", "rollback"}
REVIEW_VERDICTS = {"PASS", "CONDITIONAL", "FAIL"}
ATTESTATION_TYPES = {"provider-signed-receipt", "runtime-tool-receipt"}


def _readonly(path: Path) -> None:
    try:
        path.chmod(0o444)
    except OSError:
        pass


def _evidence_bindings(workspace: Path, paths: Any) -> List[Dict[str, Any]]:
    return bind_files(workspace, paths, label="review evidence")


def _verify_evidence_bindings(workspace: Path, bindings: Any) -> List[str]:
    return verify_file_bindings(workspace, bindings, label="review evidence")


def _attestation_contract(workspace: Path) -> Tuple[Dict[str, Any], List[str]]:
    errors: List[str] = []
    try:
        run = load_json(workspace / "run.json")
    except Exception as exc:
        return {}, ["cannot load run for review trust anchor: %s" % exc]
    binding = run.get("review_attestation_contract")
    if not isinstance(binding, dict):
        return {}, ["no frozen external review attestation adapter is bound to this run"]
    path = workspace / "control/contracts/review-attestation-contract.json"
    if not path.is_file():
        return {}, ["frozen review attestation contract missing"]
    if sha256_file(path) != binding.get("sha256"):
        return {}, ["frozen review attestation contract hash mismatch"]
    try:
        contract = load_json(path)
    except Exception as exc:
        return {}, ["invalid review attestation contract: %s" % exc]
    adapter = Path(str(contract.get("adapter_path", "")))
    receipt_root = Path(str(contract.get("receipt_root", "")))
    if not adapter.is_absolute() or not adapter.is_file():
        errors.append("external review attestation adapter is unavailable")
    elif sha256_file(adapter) != contract.get("adapter_sha256"):
        errors.append("external review attestation adapter changed after run initialization")
    if not receipt_root.is_absolute() or not receipt_root.is_dir():
        errors.append("external review receipt root is unavailable")
    return contract if not errors else {}, errors


def _external_receipt(contract: Dict[str, Any], relative: str) -> Path:
    candidate = Path(str(relative))
    if candidate.is_absolute() or ".." in candidate.parts or not candidate.parts or "\\" in str(relative):
        raise ValueError("unsafe external receipt path: %s" % relative)
    root = Path(str(contract["receipt_root"])).resolve()
    resolved = (root / candidate).resolve()
    if root not in resolved.parents or not resolved.is_file():
        raise ValueError("external receipt missing or escaped trust root: %s" % relative)
    return resolved


def _adapter_environment() -> Dict[str, str]:
    allowed = ("PATH", "SYSTEMROOT", "WINDIR", "COMSPEC", "PATHEXT", "TMPDIR", "TEMP", "TMP")
    return {key: os.environ[key] for key in allowed if key in os.environ}


def _invoke_attestation_adapter(contract: Dict[str, Any], payload: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    adapter = Path(str(contract.get("adapter_path", ""))).resolve()
    errors: List[str] = []
    if not adapter.is_file() or sha256_file(adapter) != contract.get("adapter_sha256"):
        return {}, ["trusted review attestation adapter is missing or changed"]
    timeout = int(contract.get("timeout_seconds", 15))
    try:
        completed = run_bounded(
            [str(adapter)], input_text=json.dumps(payload, ensure_ascii=False, sort_keys=True),
            timeout_seconds=timeout, env=_adapter_environment(),
        )
    except (OSError, ValueError) as exc:
        return {}, ["review attestation adapter execution failed: %s" % exc]
    if completed["timed_out"]:
        return {}, ["review attestation adapter timed out after %s seconds" % timeout]
    if completed["returncode"] != 0:
        return {}, ["review attestation adapter rejected evidence (exit %d)" % completed["returncode"]]
    try:
        result = json.loads(completed["stdout"])
    except Exception as exc:
        return {}, ["review attestation adapter returned invalid JSON: %s" % exc]
    if not isinstance(result, dict) or result.get("status") != "VERIFIED":
        errors.append("review attestation adapter did not return VERIFIED")
    if result.get("provider") != contract.get("provider"):
        errors.append("review attestation provider mismatch")
    return result, errors


def _attestation_item(workspace: Path, record: Dict[str, Any], verifier: bool = False) -> Tuple[Dict[str, Any], List[str]]:
    """Bind one review/verifier record to an external immutable receipt.

    This performs only local structural and hash checks. Provider/runtime
    verification remains a single batch adapter call in the final review gate.
    """
    errors: List[str] = []
    contract, contract_errors = _attestation_contract(workspace)
    if contract_errors:
        return {}, contract_errors
    attestation = record.get("attestation")
    if not isinstance(attestation, dict):
        return {}, ["provider/runtime attestation missing"]
    if attestation.get("type") not in ATTESTATION_TYPES:
        errors.append("attestation type is not provider-verifiable")
    if attestation.get("verification_status") != "VERIFIED":
        errors.append("attestation was not verified")
    try:
        path = _external_receipt(contract, str(attestation.get("receipt_path", "")))
    except ValueError as exc:
        return {}, errors + [str(exc)]
    actual_hash = sha256_file(path)
    if actual_hash != attestation.get("receipt_sha256"):
        errors.append("attestation receipt hash mismatch")
        return {}, errors
    actor_key = "verifier_actor_id" if verifier else "actor_id"
    return {
        "kind": "verifier" if verifier else "review",
        "receipt_path": str(path),
        "receipt_sha256": actual_hash,
        "expected_identity": {
            actor_key: record.get(actor_key),
            "context_id": record.get("context_id"),
            "provider_run_id": record.get("provider_run_id"),
        },
        "expected_context_isolated": True,
        "expected_mode": record.get("mode"),
    }, errors


def _verify_attestation(workspace: Path, record: Dict[str, Any], verifier: bool = False) -> List[str]:
    """Perform cheap structural checks during collection.

    Provider verification is intentionally deferred to one batch adapter call
    at the final gate. This prevents O(review-count) process spawning while
    preserving exact receipt, identity, context and hash bindings.
    """
    _, errors = _attestation_item(workspace, record, verifier)
    return errors


def _verify_attestation_batch(workspace: Path, reviews: List[Dict[str, Any]], verdict: Dict[str, Any]) -> List[str]:
    contract, errors = _attestation_contract(workspace)
    if errors:
        return errors
    requested: List[Dict[str, Any]] = []
    for record in reviews:
        item, item_errors = _attestation_item(workspace, record, verifier=False)
        errors.extend(item_errors)
        if item:
            requested.append(item)
    if verdict:
        item, item_errors = _attestation_item(workspace, verdict, verifier=True)
        errors.extend(item_errors)
        if item:
            requested.append(item)
    if errors:
        return errors
    payload = {
        "action": "verify-receipt-batch",
        "run_id": load_json(workspace / "run.json").get("run_id"),
        "items": requested,
    }
    result, adapter_errors = _invoke_attestation_adapter(contract, payload)
    errors.extend(adapter_errors)
    verified_items = result.get("items") if isinstance(result, dict) else None
    if not isinstance(verified_items, list) or len(verified_items) != len(requested):
        return errors + ["review attestation adapter did not verify the exact receipt batch"]
    expected_by_hash = {item["receipt_sha256"]: item for item in requested}
    seen = set()
    for verified in verified_items:
        if not isinstance(verified, dict):
            errors.append("adapter returned a malformed receipt verification")
            continue
        digest = verified.get("receipt_sha256")
        expected = expected_by_hash.get(digest)
        if expected is None or digest in seen:
            errors.append("adapter returned an unknown or duplicate receipt verification")
            continue
        seen.add(digest)
        if verified.get("identity") != expected.get("expected_identity"):
            errors.append("adapter identity mismatch for receipt %s" % digest)
        if verified.get("context_isolated") is not True or verified.get("independent") is not True:
            errors.append("adapter did not verify independence and context isolation")
        if expected.get("kind") == "verifier" and verified.get("read_only") is not True:
            errors.append("adapter did not verify read-only final verifier execution")
    if seen != set(expected_by_hash):
        errors.append("adapter omitted one or more receipt verifications")
    return errors

def _runtime_capability(workspace: Path) -> Tuple[Dict[str, Any], List[str]]:
    contract, errors = _attestation_contract(workspace)
    if errors:
        return {}, errors
    payload = {
        "action": "capability",
        "run_id": load_json(workspace / "run.json").get("run_id"),
        "required": ["independent-subagents", "read-only-verifier", "provider-receipt-verification"],
    }
    result, adapter_errors = _invoke_attestation_adapter(contract, payload)
    errors.extend(adapter_errors)
    if result:
        if result.get("independent_subagents_available") is not True:
            errors.append("adapter cannot provide genuinely isolated SubAgents")
        if result.get("read_only_verifier_available") is not True:
            errors.append("adapter cannot provide an independent read-only verifier")
        if result.get("provider_receipt_verification") != "VERIFIED":
            errors.append("adapter cannot verify provider/runtime receipts")
    return result, errors


def _packet_integrity(workspace: Path) -> Tuple[Dict[str, Any], List[str]]:
    plan_path = workspace / "reviews/review-plan.json"
    if not plan_path.is_file():
        return {}, ["review plan missing"]
    try:
        plan = load_json(plan_path)
    except Exception as exc:
        return {}, ["invalid review plan: %s" % exc]
    errors: List[str] = []
    packet_hashes: Dict[str, str] = {}
    packets: List[Dict[str, Any]] = []
    for path in sorted((workspace / "reviews/packets").glob("*.json")):
        try:
            packet = load_json(path)
        except Exception as exc:
            errors.append("invalid packet %s: %s" % (path.name, exc))
            continue
        packet_hashes[path.stem] = sha256_file(path)
        packets.append(packet)
        errors.extend(["%s: %s" % (path.name, item) for item in _verify_evidence_bindings(workspace, packet.get("evidence_bindings"))])
    if len(packets) != 12:
        errors.append("review plan requires exactly twelve frozen packets")
    if packet_hashes != plan.get("packet_hashes"):
        errors.append("review packet hashes differ from frozen plan")
    digest_payload = [{"packet_id": key, "sha256": packet_hashes[key]} for key in sorted(packet_hashes)]
    if sha256_bytes(canonical_json(digest_payload)) != plan.get("packets_digest"):
        errors.append("review packet digest mismatch")
    return plan, errors


def _preflight_review_evidence(workspace: Path, evidence: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    """Validate every review evidence path before creating any immutable packet.

    Fail once with the complete missing/unsafe path set rather than discovering
    one stale reference per rerun.  This keeps the fail-closed boundary while
    reducing orchestration churn and token waste.
    """
    role_paths: Dict[str, List[str]] = {}
    errors: List[str] = []
    unique_paths = set()
    for roles in PANEL_ROLES.values():
        for role in roles:
            paths = evidence.get(role, evidence.get("default", []))
            if not isinstance(paths, list) or not paths or not all(isinstance(item, str) and item for item in paths):
                errors.append("%s: evidence paths must be a non-empty string list" % role)
                continue
            role_paths[role] = list(paths)
            unique_paths.update(paths)
    for relative in sorted(unique_paths):
        try:
            bind_files(workspace, [relative], label="review evidence")
        except (OSError, ValueError) as exc:
            errors.append("%s: %s" % (relative, exc))
    if errors:
        raise ValueError("review evidence preflight failed: " + " | ".join(errors))
    return {role: bind_files(workspace, paths, label="review evidence") for role, paths in role_paths.items()}


def generate_review_plan(workspace: Path, evidence_index: Path, actor_id: str = "stable-optimizer") -> Dict[str, Any]:
    workspace = workspace.resolve()
    run = load_json(workspace / "run.json")
    integrity = verify_run_seal(workspace, run) + verify_control_plane(workspace, run)
    if integrity:
        raise ValueError("cannot seal review plan over a mutated run: %s" % integrity)
    evidence = load_json(evidence_index)
    if not isinstance(evidence, dict):
        raise ValueError("evidence index must be an object")
    bindings_by_role = _preflight_review_evidence(workspace, evidence)
    candidate_hashes: Dict[str, str] = {}
    for item in run["target"]["candidates"]:
        actual = sha256_tree(Path(item["path"]), exclude={"MANIFEST.sha256"})
        if actual != item["current_tree_hash"]:
            raise ValueError("candidate ledger/tree mismatch before review: %s" % item["candidate_id"])
        candidate_hashes[item["candidate_id"]] = actual
    frozen = {
        "run_id": run["run_id"], "genesis_hash": run["genesis"]["baseline_hash"],
        "baseline_tree_hash": run["target"]["baseline_tree_hash"],
        "evidence_index_sha256": sha256_file(evidence_index),
        "candidate_tree_hashes": candidate_hashes,
        "run_seal_sha256": sha256_file(workspace / "control/contracts/run-seal.json"),
        "control_plane_manifest_sha256": sha256_file(workspace / "control/contracts/control-plane-manifest.json"),
    }
    plan_id = "review-plan-%s" % uuid.uuid4().hex[:12]
    packet_paths: List[Path] = []
    for panel, roles in PANEL_ROLES.items():
        for index, role in enumerate(roles, 1):
            packet_id = "p%d-r%02d-%s" % (panel, index, role)
            bindings = bindings_by_role[role]
            packet = {
                "schema_version": "2.0", "plan_id": plan_id, "packet_id": packet_id, "panel": panel, "role": role,
                "created_at": utc_now(), "created_by": actor_id, "frozen": frozen,
                "evidence_paths": [item["path"] for item in bindings], "evidence_bindings": bindings,
                "rubric": {
                    "hard_domains": sorted(HARD_DOMAINS),
                    "questions": [
                        "What evidence disproves the candidate's claimed improvement?",
                        "Which hard requirement is unverified or regressed?",
                        "What new failure mode, ambiguity or long-horizon risk remains?",
                        "Which result is raw evidence versus inference?",
                    ],
                    "allowed_verdicts": sorted(REVIEW_VERDICTS),
                },
                "independence_contract": {
                    "must_use_unique_actor_id": True, "must_use_unique_context_id": True,
                    "must_use_provider_run_id": True, "must_supply_provider_or_runtime_receipt": True,
                    "must_not_see_other_reviews_before_submission": True,
                    "must_not_receive_optimizer_preferred_verdict": True,
                },
            }
            path = workspace / "reviews/packets" / (packet_id + ".json")
            if path.exists():
                raise ValueError("review packets already exist; create a new run rather than overwrite")
            write_json(path, packet)
            _readonly(path)
            packet_paths.append(path)
    packet_hashes = {path.stem: sha256_file(path) for path in sorted(packet_paths)}
    digest_payload = [{"packet_id": key, "sha256": packet_hashes[key]} for key in sorted(packet_hashes)]
    plan = {
        "schema_version": "2.0", "plan_id": plan_id, "run_id": run["run_id"], "created_at": utc_now(),
        "packet_count": len(packet_paths), "panels": {str(key): value for key, value in PANEL_ROLES.items()},
        "frozen": frozen, "packet_hashes": packet_hashes,
        "packets_digest": sha256_bytes(canonical_json(digest_payload)),
    }
    plan_path = workspace / "reviews/review-plan.json"
    write_json(plan_path, plan)
    _readonly(plan_path)
    return plan


def validate_review_record(record: Dict[str, Any], packet: Dict[str, Any], workspace: Path = None) -> List[str]:
    errors: List[str] = []
    required = (
        "packet_id", "panel", "role", "actor_id", "context_id", "provider_run_id", "runtime", "model",
        "mode", "context_isolated", "saw_other_reviews_before_submission", "verdict", "confidence",
        "findings", "unknowns", "evidence_paths", "evidence_bindings", "attestation", "submitted_at",
    )
    for key in required:
        if key not in record:
            errors.append("review missing %s" % key)
    if record.get("packet_id") != packet.get("packet_id") or record.get("panel") != packet.get("panel") or record.get("role") != packet.get("role"):
        errors.append("review/packet identity mismatch")
    if record.get("mode") != "independent-subagent":
        errors.append("review mode is not a genuine independent SubAgent")
    if record.get("context_isolated") is not True or record.get("saw_other_reviews_before_submission") is not False:
        errors.append("review context was not isolated")
    if record.get("verdict") not in REVIEW_VERDICTS:
        errors.append("review verdict invalid")
    if not record.get("actor_id") or not record.get("context_id") or not record.get("provider_run_id"):
        errors.append("provider-verifiable identity evidence missing")
    if record.get("evidence_paths") != packet.get("evidence_paths") or record.get("evidence_bindings") != packet.get("evidence_bindings"):
        errors.append("review did not bind the exact frozen evidence set")
    try:
        confidence = float(record.get("confidence"))
        if confidence < 0 or confidence > 1:
            errors.append("review confidence must be 0..1")
    except (TypeError, ValueError):
        errors.append("review confidence must be numeric")
    try:
        dt.datetime.fromisoformat(str(record.get("submitted_at", "")).replace("Z", "+00:00"))
    except ValueError:
        errors.append("review submitted_at must be ISO-8601")
    findings = record.get("findings")
    if not isinstance(findings, list):
        errors.append("findings must be a list")
    else:
        for index, finding in enumerate(findings, 1):
            if not isinstance(finding, dict) or not all(key in finding for key in ("finding_id", "severity", "domain", "status", "evidence")):
                errors.append("finding %d incomplete" % index)
            elif finding.get("severity") not in {"INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL"}:
                errors.append("finding severity invalid")
            elif finding.get("status") not in {"OPEN", "RESOLVED", "NOT_AN_ISSUE"}:
                errors.append("finding status invalid")
            elif not isinstance(finding.get("evidence"), list) or not finding.get("evidence"):
                errors.append("finding evidence must be non-empty")
    if workspace is not None:
        errors.extend(_verify_evidence_bindings(workspace, record.get("evidence_bindings")))
        errors.extend(_verify_attestation(workspace, record, verifier=False))
    return errors


def collect_review(workspace: Path, record_path: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    plan, plan_errors = _packet_integrity(workspace)
    if plan_errors:
        return {"status": "BLOCKED", "errors": plan_errors}
    record = load_json(record_path)
    packet_path = workspace / "reviews/packets" / (str(record.get("packet_id")) + ".json")
    if not packet_path.is_file():
        return {"status": "BLOCKED", "errors": ["review packet not found"]}
    packet = load_json(packet_path)
    errors = validate_review_record(record, packet, workspace)
    if errors:
        return {"status": "BLOCKED", "errors": errors}
    destination = workspace / ("reviews/panel-%d" % int(record["panel"])) / (record["packet_id"] + ".json")
    if destination.exists():
        return {"status": "BLOCKED", "errors": ["review records are immutable; duplicate submission rejected"]}
    write_json(destination, record)
    _readonly(destination)
    return {"status": "RECORDED", "path": str(destination), "sha256": sha256_file(destination), "plan_id": plan.get("plan_id")}


def _load_reviews(workspace: Path) -> Tuple[List[Dict[str, Any]], List[str]]:
    reviews: List[Dict[str, Any]] = []
    errors: List[str] = []
    _, plan_errors = _packet_integrity(workspace)
    errors.extend(plan_errors)
    for panel in (1, 2):
        paths = sorted((workspace / ("reviews/panel-%d" % panel)).glob("*.json"))
        if len(paths) != 6:
            errors.append("panel %d requires exactly six submitted reviews; got %d" % (panel, len(paths)))
        for path in paths:
            try:
                record = load_json(path)
            except Exception as exc:
                errors.append("invalid review %s: %s" % (path.name, exc))
                continue
            packet_path = workspace / "reviews/packets" / (str(record.get("packet_id")) + ".json")
            if not packet_path.is_file():
                errors.append("review %s has no frozen packet" % path.name)
                continue
            errors.extend(["%s: %s" % (path.name, item) for item in validate_review_record(record, load_json(packet_path), workspace)])
            reviews.append(record)
    return reviews, errors


def validate_final_verifier(verdict: Dict[str, Any], run: Dict[str, Any], reviewer_ids: set, reviewer_contexts: set, reviewer_runs: set, workspace: Path) -> List[str]:
    errors: List[str] = []
    required = (
        "verifier_actor_id", "context_id", "provider_run_id", "mode", "read_only", "write_actions",
        "optimizer_actor_id", "reviewed_packet_ids", "reviewed_review_hashes", "finding_resolutions", "verdict",
        "evidence_paths", "evidence_bindings", "attestation", "submitted_at",
    )
    for key in required:
        if key not in verdict:
            errors.append("verifier record missing %s" % key)
    if verdict.get("mode") != "independent-read-only-verifier" or verdict.get("read_only") is not True or verdict.get("write_actions"):
        errors.append("final verifier must be independent, read-only and perform no writes")
    if verdict.get("verifier_actor_id") == verdict.get("optimizer_actor_id"):
        errors.append("optimizer cannot be final verifier")
    if verdict.get("verifier_actor_id") in reviewer_ids or verdict.get("context_id") in reviewer_contexts or verdict.get("provider_run_id") in reviewer_runs:
        errors.append("final verifier must be a distinct thirteenth actor/context/run")
    if verdict.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
        errors.append("final verifier verdict invalid")
    errors.extend(_verify_evidence_bindings(workspace, verdict.get("evidence_bindings")))
    errors.extend(_verify_attestation(workspace, verdict, verifier=True))
    return errors


def review_gate(workspace: Path) -> Dict[str, Any]:
    workspace = workspace.resolve()
    warnings: List[str] = []
    try:
        run = load_json(workspace / "run.json")
    except Exception as exc:
        return {"status": "BLOCKED", "errors": ["invalid run contract: %s" % exc], "warnings": []}
    integrity_errors = verify_run_seal(workspace, run) + verify_control_plane(workspace, run)
    if integrity_errors:
        return {"status": "BLOCKED", "errors": sorted(set(integrity_errors)), "warnings": []}
    capability, capability_errors = _runtime_capability(workspace)
    if capability_errors:
        return {
            "status": "INDEPENDENT_REVIEW_UNAVAILABLE", "errors": capability_errors,
            "warnings": capability.get("notes", []) if capability else [],
        }

    errors: List[str] = []
    reviews, review_errors = _load_reviews(workspace)
    errors.extend(review_errors)
    actors = [str(item.get("actor_id")) for item in reviews]
    contexts = [str(item.get("context_id")) for item in reviews]
    provider_runs = [str(item.get("provider_run_id")) for item in reviews]
    if len(actors) != len(set(actors)):
        errors.append("review actor IDs are not unique across both panels")
    if len(contexts) != len(set(contexts)):
        errors.append("review contexts are not unique across both panels")
    if len(provider_runs) != len(set(provider_runs)):
        errors.append("provider run IDs are not unique across both panels")
    unresolved_critical: List[Dict[str, Any]] = []
    unresolved_hard: List[Dict[str, Any]] = []
    soft_dissent: List[Dict[str, Any]] = []
    for review in reviews:
        if review.get("verdict") in {"CONDITIONAL", "FAIL"}:
            soft_dissent.append({"packet_id": review.get("packet_id"), "verdict": review.get("verdict")})
        for finding in review.get("findings", []):
            if finding.get("status") in {"RESOLVED", "NOT_AN_ISSUE"}:
                continue
            if finding.get("severity") == "CRITICAL":
                unresolved_critical.append(finding)
            if finding.get("domain") in HARD_DOMAINS and finding.get("severity") in {"HIGH", "CRITICAL"}:
                unresolved_hard.append(finding)
    verdict_path = workspace / "verifier/final-verdict.json"
    if not verdict_path.is_file():
        errors.append("missing independent final verifier record")
        verdict: Dict[str, Any] = {}
    else:
        verdict = load_json(verdict_path)
        run = load_json(workspace / "run.json")
        errors.extend(validate_final_verifier(verdict, run, set(actors), set(contexts), set(provider_runs), workspace))
    errors.extend(_verify_attestation_batch(workspace, reviews, verdict))
    expected_packets = {path.stem for path in (workspace / "reviews/packets").glob("*.json")}
    if verdict and set(verdict.get("reviewed_packet_ids", [])) != expected_packets:
        errors.append("final verifier did not review all twelve packet IDs")
    expected_review_hashes = {
        path.stem: sha256_file(path)
        for panel in (1, 2)
        for path in sorted((workspace / ("reviews/panel-%d" % panel)).glob("*.json"))
    }
    if verdict and verdict.get("reviewed_review_hashes") != expected_review_hashes:
        errors.append("final verifier did not bind the exact twelve review records")
    resolutions = {item.get("finding_id"): item for item in verdict.get("finding_resolutions", []) if isinstance(item, dict)} if verdict else {}
    for finding in unresolved_critical + unresolved_hard:
        resolution = resolutions.get(finding.get("finding_id"))
        if not resolution or resolution.get("status") != "RESOLVED" or not resolution.get("evidence"):
            errors.append("unresolved hard/critical finding: %s" % finding.get("finding_id"))
    if verdict and verdict.get("verdict") != "PASS":
        errors.append("final verifier did not PASS")
    return {
        "status": "PASS" if not errors else "BLOCKED", "errors": sorted(set(errors)), "warnings": warnings,
        "reviews": len(reviews), "soft_dissent": soft_dissent, "unresolved_critical": unresolved_critical,
        "policy": "12 provider-attested independent reviews are mandatory; soft dissent may be resolved by a distinct attested read-only verifier; hard/critical findings cannot remain unresolved",
    }
