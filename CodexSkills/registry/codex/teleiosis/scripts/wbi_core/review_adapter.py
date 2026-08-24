from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from .io import canonical_json, ensure_external, load_json, sha256_file, utc_now, write_json

REQUIRED_CAPABILITIES = {"independent-subagents", "read-only-verifier", "provider-identifiable-runs"}
FORMAL_ISOLATION_MODES = {"REMOTE_PROVIDER", "SEPARATE_OS_PRINCIPAL", "HARDWARE_ATTESTED"}


def _is_hash(value: Any) -> bool:
    return isinstance(value, str) and len(value) == 64 and all(char in "0123456789abcdef" for char in value)


def _external_file(
    value: Any,
    digest: Any,
    *,
    protected: List[Path],
    label: str,
    errors: List[str],
    bundled_root: Optional[Path] = None,
) -> Optional[Path]:
    if not isinstance(value, str) or not Path(value).is_absolute():
        errors.append("%s path must be absolute" % label)
        return None
    path = Path(value).resolve()
    try:
        ensure_external(path, protected, label)
    except ValueError as exc:
        errors.append(str(exc))
    if not path.is_file() or path.is_symlink():
        errors.append("%s is missing, linked, or not a file" % label)
    elif not _is_hash(digest) or digest != sha256_file(path):
        errors.append("%s hash mismatch" % label)
    if bundled_root is not None:
        bundled = bundled_root.resolve()
        if path == bundled or bundled in path.parents:
            errors.append("bundled %s cannot be a formal trust root" % label)
    return path


def validate_review_adapter_contract(
    contract: Dict[str, Any],
    *,
    workspace: Path,
    target: Path,
    optimizer_root: Path,
    bundled_root: Optional[Path] = None,
) -> List[str]:
    errors: List[str] = []
    if not isinstance(contract, dict):
        return ["review adapter contract must be an object"]
    if contract.get("schema_version") != "1.0":
        errors.append("review adapter contract schema_version must be 1.0")
    if contract.get("status") != "FROZEN":
        errors.append("review adapter contract must be FROZEN")
    for key in ("provider", "adapter_version", "deployment_identity"):
        if not isinstance(contract.get(key), str) or not str(contract.get(key)).strip():
            errors.append("review adapter contract %s missing" % key)

    protected = [workspace.resolve(), target.resolve(), optimizer_root.resolve()]
    _external_file(
        contract.get("adapter_path"), contract.get("adapter_sha256"), protected=protected,
        label="review adapter", errors=errors, bundled_root=bundled_root,
    )

    receipt_value = contract.get("receipt_root")
    if not isinstance(receipt_value, str) or not Path(receipt_value).is_absolute():
        errors.append("receipt_root must be absolute")
        receipt_root = None
    else:
        receipt_root = Path(receipt_value).resolve()
        try:
            ensure_external(receipt_root, protected, "review receipt root")
        except ValueError as exc:
            errors.append(str(exc))
        if not receipt_root.is_dir() or receipt_root.is_symlink():
            errors.append("review receipt root is missing, linked, or not a directory")
        if bundled_root is not None:
            bundled = bundled_root.resolve()
            if receipt_root == bundled or bundled in receipt_root.parents:
                errors.append("bundled receipt root cannot satisfy formal review")

    capabilities = contract.get("capabilities")
    if not isinstance(capabilities, list) or not REQUIRED_CAPABILITIES.issubset(set(capabilities)):
        errors.append("review adapter lacks mandatory capabilities")
    if contract.get("candidate_can_write_receipts") is not False:
        errors.append("candidate_can_write_receipts must be false")
    if contract.get("candidate_can_access_signing_key") is not False:
        errors.append("candidate_can_access_signing_key must be false")
    if contract.get("shell_execution") is not False:
        errors.append("formal adapter protocol must not accept arbitrary shell execution")

    mode = contract.get("attestation_mode")
    if mode not in {"FORMAL_EXTERNAL", "DIAGNOSTIC_FIXTURE"}:
        errors.append("attestation_mode must be FORMAL_EXTERNAL or DIAGNOSTIC_FIXTURE")
    if mode == "DIAGNOSTIC_FIXTURE":
        if contract.get("formal_attestation") is not False:
            errors.append("diagnostic fixture contract cannot claim formal_attestation")
        return sorted(set(errors))

    if contract.get("formal_attestation") is not True:
        errors.append("FORMAL_EXTERNAL contract requires formal_attestation=true")
    if contract.get("trust_mode") != "ED25519_SIGNED_RECEIPTS":
        errors.append("formal review requires ED25519_SIGNED_RECEIPTS trust_mode")
    if contract.get("signature_algorithm") != "ed25519":
        errors.append("formal review signature_algorithm must be ed25519")
    if contract.get("trust_anchor_provisioning") != "PRE_EXISTING_EXTERNAL":
        errors.append("formal trust anchor must be provisioned before the run by an external authority")
    if contract.get("isolation_mode") not in FORMAL_ISOLATION_MODES:
        errors.append("formal isolation_mode must be REMOTE_PROVIDER, SEPARATE_OS_PRINCIPAL, or HARDWARE_ATTESTED")
    _external_file(
        contract.get("trust_anchor_path"), contract.get("trust_anchor_sha256"), protected=protected,
        label="review trust anchor", errors=errors, bundled_root=bundled_root,
    )
    return sorted(set(errors))


def _load_ed25519_public_key(path: Path, errors: List[str]):
    try:
        from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
        from cryptography.hazmat.primitives.serialization import load_pem_public_key
    except Exception as exc:  # pragma: no cover - depends on target runtime
        errors.append("ed25519 verification capability unavailable: %s" % exc)
        return None
    try:
        key = load_pem_public_key(path.read_bytes())
    except Exception as exc:
        errors.append("review trust anchor cannot be loaded: %s" % exc)
        return None
    if not isinstance(key, Ed25519PublicKey):
        errors.append("review trust anchor is not an Ed25519 public key")
        return None
    return key


def _verify_signature(public_key: Any, data: bytes, signature_path: Path, label: str, errors: List[str]) -> None:
    if public_key is None:
        return
    try:
        signature = signature_path.read_bytes()
        public_key.verify(signature, data)
    except Exception:
        errors.append("%s Ed25519 signature verification failed" % label)


def _receipt_file(
    item: Dict[str, Any],
    contract: Dict[str, Any],
    label: str,
    seen_paths: Set[str],
    errors: List[str],
    public_key: Any,
    *,
    packet_index_sha256: str,
    receipt_kind: str,
) -> None:
    receipt_root = Path(str(contract.get("receipt_root", ""))).resolve()
    path_value = item.get("provider_receipt_path")
    digest = item.get("provider_receipt_sha256")
    signature_value = item.get("provider_receipt_signature_path")
    signature_digest = item.get("provider_receipt_signature_sha256")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        errors.append("%s provider receipt path must be absolute" % label)
        return
    if not isinstance(signature_value, str) or not Path(signature_value).is_absolute():
        errors.append("%s provider receipt signature path must be absolute" % label)
        return
    path = Path(path_value).resolve()
    signature_path = Path(signature_value).resolve()
    for candidate, candidate_digest, candidate_label in (
        (path, digest, "provider receipt"),
        (signature_path, signature_digest, "provider receipt signature"),
    ):
        if receipt_root not in candidate.parents:
            errors.append("%s %s must be under the frozen external receipt root" % (label, candidate_label))
            continue
        if str(candidate) in seen_paths:
            errors.append("external review evidence path reused: %s" % candidate)
            continue
        seen_paths.add(str(candidate))
        if not candidate.is_file() or candidate.is_symlink():
            errors.append("%s %s is missing or linked" % (label, candidate_label))
        elif not _is_hash(candidate_digest) or candidate_digest != sha256_file(candidate):
            errors.append("%s %s hash mismatch" % (label, candidate_label))
    if not path.is_file() or path.is_symlink() or not signature_path.is_file() or signature_path.is_symlink():
        return
    _verify_signature(public_key, path.read_bytes(), signature_path, "%s provider receipt" % label, errors)
    try:
        receipt = load_json(path)
    except Exception as exc:
        errors.append("%s provider receipt is not valid JSON: %s" % (label, exc))
        return
    expected = {
        "schema_version": "1.0",
        "receipt_kind": receipt_kind,
        "provider": contract.get("provider"),
        "packet_index_sha256": packet_index_sha256,
        "actor_id": item.get("actor_id"),
        "context_id": item.get("context_id"),
        "provider_run_id": item.get("provider_run_id"),
        "verdict": item.get("verdict"),
    }
    for key, expected_value in expected.items():
        if receipt.get(key) != expected_value:
            errors.append("%s provider receipt %s binding mismatch" % (label, key))
    for key in ("provider_request_id", "runtime", "model", "started_at", "finished_at"):
        if not isinstance(receipt.get(key), str) or not str(receipt.get(key)).strip():
            errors.append("%s provider receipt %s missing" % (label, key))
    if receipt_kind == "review-seat":
        if receipt.get("review_round") != item.get("review_round") or receipt.get("seat_number") != item.get("seat_number"):
            errors.append("%s provider receipt round/seat binding mismatch" % label)
    else:
        if receipt.get("read_only") is not True:
            errors.append("final verifier provider receipt must prove read_only=true")


def _verify_attestation_signature(
    attestation: Dict[str, Any], contract: Dict[str, Any], public_key: Any, seen_paths: Set[str], errors: List[str]
) -> None:
    receipt_root = Path(str(contract.get("receipt_root", ""))).resolve()
    path_value = attestation.get("attestation_signature_path")
    digest = attestation.get("attestation_signature_sha256")
    if not isinstance(path_value, str) or not Path(path_value).is_absolute():
        errors.append("attestation signature path must be absolute")
        return
    path = Path(path_value).resolve()
    if receipt_root not in path.parents:
        errors.append("attestation signature must be under the frozen external receipt root")
        return
    if str(path) in seen_paths:
        errors.append("external review evidence path reused: %s" % path)
        return
    seen_paths.add(str(path))
    if not path.is_file() or path.is_symlink():
        errors.append("attestation signature is missing or linked")
        return
    if not _is_hash(digest) or digest != sha256_file(path):
        errors.append("attestation signature hash mismatch")
        return
    payload = {key: value for key, value in attestation.items() if key not in {"attestation_signature_path", "attestation_signature_sha256"}}
    _verify_signature(public_key, canonical_json(payload), path, "external attestation", errors)


def validate_attestation(
    attestation: Dict[str, Any],
    contract: Dict[str, Any],
    *,
    packet_index_sha256: str,
) -> List[str]:
    errors: List[str] = []
    if not isinstance(attestation, dict):
        return ["external attestation must be an object"]
    if contract.get("attestation_mode") != "FORMAL_EXTERNAL":
        return ["diagnostic fixture contract cannot satisfy formal attestation"]
    if attestation.get("schema_version") != "1.0":
        errors.append("external attestation schema_version must be 1.0")
    if attestation.get("attestation_mode") != "FORMAL_EXTERNAL":
        errors.append("external attestation mode mismatch")
    if attestation.get("adapter_sha256") != contract.get("adapter_sha256"):
        errors.append("external attestation adapter hash mismatch")
    if attestation.get("trust_anchor_sha256") != contract.get("trust_anchor_sha256"):
        errors.append("external attestation trust anchor hash mismatch")
    if attestation.get("provider") != contract.get("provider"):
        errors.append("external attestation provider mismatch")
    if attestation.get("deployment_identity") != contract.get("deployment_identity"):
        errors.append("external attestation deployment identity mismatch")
    if attestation.get("packet_index_sha256") != packet_index_sha256:
        errors.append("external attestation packet index hash mismatch")

    anchor_value = contract.get("trust_anchor_path")
    public_key = _load_ed25519_public_key(Path(str(anchor_value)).resolve(), errors) if isinstance(anchor_value, str) else None
    seats = attestation.get("review_seats")
    if not isinstance(seats, list) or len(seats) != 12:
        errors.append("external attestation requires exactly 12 review seats")
        seats = []
    actor_ids: Set[str] = set()
    context_ids: Set[str] = set()
    provider_run_ids: Set[str] = set()
    provider_request_ids: Set[str] = set()
    seen_paths: Set[str] = set()
    round_seats: Set[tuple] = set()
    for index, seat in enumerate(seats, 1):
        if not isinstance(seat, dict):
            errors.append("review seat %d must be an object" % index)
            continue
        review_round, seat_number = seat.get("review_round"), seat.get("seat_number")
        if review_round not in {1, 2} or not isinstance(seat_number, int) or isinstance(seat_number, bool) or seat_number not in range(1, 7):
            errors.append("review seat %d must bind review_round 1..2 and seat_number 1..6" % index)
        else:
            if (review_round, seat_number) in round_seats:
                errors.append("duplicate 2x6 review seat: round %s seat %s" % (review_round, seat_number))
            round_seats.add((review_round, seat_number))
        for key, collection in (("actor_id", actor_ids), ("context_id", context_ids), ("provider_run_id", provider_run_ids)):
            value = seat.get(key)
            if not isinstance(value, str) or not value:
                errors.append("review seat %d %s missing" % (index, key))
            elif value in collection:
                errors.append("review seat %s reused: %s" % (key, value))
            collection.add(value)
        if seat.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
            errors.append("review seat %d verdict invalid" % index)
        _receipt_file(
            seat, contract, "review seat %d" % index, seen_paths, errors, public_key,
            packet_index_sha256=packet_index_sha256, receipt_kind="review-seat",
        )
        receipt_path = seat.get("provider_receipt_path")
        if isinstance(receipt_path, str) and Path(receipt_path).is_file():
            try:
                request_id = load_json(Path(receipt_path)).get("provider_request_id")
            except Exception:
                request_id = None
            if isinstance(request_id, str):
                if request_id in provider_request_ids:
                    errors.append("provider_request_id reused across review seats: %s" % request_id)
                provider_request_ids.add(request_id)
    required_pairs = {(review_round, seat_number) for review_round in (1, 2) for seat_number in range(1, 7)}
    if round_seats != required_pairs:
        errors.append("review seats must cover exactly two rounds of six unique seats")

    verifier = attestation.get("final_verifier")
    if not isinstance(verifier, dict):
        errors.append("final verifier missing")
    else:
        if verifier.get("read_only") is not True:
            errors.append("final verifier must be read-only")
        for key, review_values in (("actor_id", actor_ids), ("context_id", context_ids), ("provider_run_id", provider_run_ids)):
            value = verifier.get(key)
            if not isinstance(value, str) or not value:
                errors.append("final verifier %s missing" % key)
            elif value in review_values:
                errors.append("final verifier %s reuses a reviewer identity" % key)
        if verifier.get("verdict") not in {"PASS", "FAIL", "BLOCKED"}:
            errors.append("final verifier verdict invalid")
        _receipt_file(
            verifier, contract, "final verifier", seen_paths, errors, public_key,
            packet_index_sha256=packet_index_sha256, receipt_kind="final-verifier",
        )
        receipt_path = verifier.get("provider_receipt_path")
        if isinstance(receipt_path, str) and Path(receipt_path).is_file():
            try:
                request_id = load_json(Path(receipt_path)).get("provider_request_id")
            except Exception:
                request_id = None
            if isinstance(request_id, str) and request_id in provider_request_ids:
                errors.append("final verifier provider_request_id reuses reviewer evidence")
    if attestation.get("candidate_authored") is not False:
        errors.append("candidate-authored attestation cannot satisfy formal review")
    if not isinstance(attestation.get("residual_trust"), list):
        errors.append("residual_trust must be a list")
    _verify_attestation_signature(attestation, contract, public_key, seen_paths, errors)
    return sorted(set(errors))


def inspect_review_adapter(
    contract_path: Path,
    *,
    workspace: Path,
    target: Path,
    optimizer_root: Path,
    bundled_root: Optional[Path] = None,
    attestation_path: Optional[Path] = None,
    packet_index_path: Optional[Path] = None,
    output: Optional[Path] = None,
) -> Dict[str, Any]:
    contract = load_json(contract_path.resolve())
    errors = validate_review_adapter_contract(
        contract, workspace=workspace, target=target, optimizer_root=optimizer_root, bundled_root=bundled_root
    )
    attestation_errors: List[str] = []
    if attestation_path is not None:
        resolved_attestation = attestation_path.resolve()
        receipt_root = Path(str(contract.get("receipt_root", ""))).resolve()
        if receipt_root not in resolved_attestation.parents or not resolved_attestation.is_file() or resolved_attestation.is_symlink():
            attestation_errors.append("external attestation must be an immutable file under the frozen receipt root")
        elif packet_index_path is None or not packet_index_path.resolve().is_file():
            attestation_errors.append("packet index required for external attestation validation")
        else:
            attestation = load_json(resolved_attestation)
            attestation_errors = validate_attestation(
                attestation, contract, packet_index_sha256=sha256_file(packet_index_path.resolve())
            )
    errors.extend(attestation_errors)
    mode = contract.get("attestation_mode")
    formal_available = not errors and attestation_path is not None and mode == "FORMAL_EXTERNAL"
    result = {
        "schema_version": "1.0",
        "checked_at": utc_now(),
        "adapter_contract_status": "PASS" if not errors else "FAIL",
        "cryptographic_receipt_status": "PASS" if formal_available else ("FAIL" if attestation_path is not None and errors else "NOT_CHECKED"),
        "formal_review_capability": "AVAILABLE" if formal_available else ("DIAGNOSTIC_ONLY" if mode == "DIAGNOSTIC_FIXTURE" and not errors else "UNAVAILABLE"),
        "errors": sorted(set(errors)),
        "contract_sha256": sha256_file(contract_path.resolve()),
        "residual_trust": [
            "Cryptographic integrity does not by itself prove organisational independence; the external provider or separate OS principal remains the trust root."
        ],
    }
    if output is not None:
        write_json(output.resolve(), result)
    return result
