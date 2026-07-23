#!/usr/bin/env python3
"""Validate two-stage SkillOps activation intent and settlement artifacts."""

from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import hashlib
import os
import re
import stat
import subprocess
import sys
from pathlib import Path, PurePosixPath
from typing import Any, Dict, Mapping, Optional, Sequence

from build_activation_control import (
    CANDIDATE_BUNDLE_DIGEST,
    CANDIDATE_BUNDLE_GIT_OBJECT_ID,
    CANDIDATE_MANIFEST_REPO_PATH,
    CONTROL_INTERFACE_PATH,
    CONTROL_INTERFACE_REPO_PATH,
    INTENT_ID,
    INTENT_SCHEMA_PATH,
    NOTIFICATION_AFFECTED_PATH_REFS,
    NOTIFICATION_RECEIPT_ID,
    PROTOCOL_REVISION,
    REPO_ROOT,
    SETTLEMENT_ID,
    SETTLEMENT_SCHEMA_PATH,
    TARGET_SRV_REVISION,
    control_interface,
    expected_outputs,
)
from canonical_json import canonical_digest, canonicalize_object, parse_json_bytes
from validate_mechanism import (
    ContractBundle,
    ContractError,
    TrustTuple,
    build_registry,
    is_repo_relative_posix_path,
    load_trusted_bundle,
    scan_public_value,
    strict_load,
    validate_instance,
)


VERSION_PATH = "CodexSkills/VERSION"
HANDOFF_PATH = "CodexSkills/governance/HANDOFF.md"
NOTIFICATION_POLICY_ID = (
    "urn:linzecolin:agentdatabase:skillops:policy:notification:v1"
)
UTC_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
CONTROL_MODE = "DRAFT_NON_ACTIVE_CONTROL"
GIT_OBJECT_RE = re.compile(
    r"^(?:(sha1):([0-9a-f]{40})|(sha256):([0-9a-f]{64}))$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
CONTROL_SCHEMA_REPO_PATHS = {
    INTENT_ID: (
        "CodexSkills/governance/activation/schemas/"
        "activation-intent.schema.json"
    ),
    SETTLEMENT_ID: (
        "CodexSkills/governance/activation/schemas/"
        "activation-settlement.schema.json"
    ),
}


@dataclasses.dataclass(frozen=True)
class ActivationControlTrustTuple:
    verified_git_object_id: str
    expected_control_interface_raw_sha256: str
    canonical_control_interface_path: str
    mode: str


def _activation_paths(activation_uid: str) -> Mapping[str, str]:
    prefix = (
        "CodexSkills/governance/activation-receipts/" + activation_uid
    )
    return {
        "intent": prefix + ".intent.json",
        "notification": prefix + ".notification-receipt.json",
        "settlement": prefix + ".settlement.json",
    }


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _utc(value: str) -> dt.datetime:
    try:
        return dt.datetime.strptime(value, UTC_FORMAT).replace(
            tzinfo=dt.timezone.utc
        )
    except (TypeError, ValueError) as exc:
        raise ContractError("ACTIVATION_TIMESTAMP_INVALID") from exc


def _sorted_unique(
    rows: Sequence[Mapping[str, Any]],
    field: str,
    code: str,
) -> None:
    values = [row.get(field) for row in rows]
    if values != sorted(values) or len(values) != len(set(values)):
        raise ContractError(code)


def _git_blob_for_control(
    repo_root: Path,
    verified_git_object_id: str,
    relative_path: str,
) -> bytes:
    match = GIT_OBJECT_RE.fullmatch(verified_git_object_id)
    if not match:
        raise ContractError("ACTIVATION_CONTROL_GIT_OBJECT_ID_INVALID")
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    commands = (
        ("rev-parse", "--show-object-format"),
        ("cat-file", "-e", f"{object_id}^{{commit}}"),
        ("show", f"{object_id}:{relative_path}"),
    )
    outputs = []
    for command in commands:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo_root), *command],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ContractError(
                "ACTIVATION_CONTROL_GIT_READ_UNAVAILABLE"
            ) from exc
        if result.returncode != 0:
            raise ContractError("ACTIVATION_CONTROL_GIT_READ_FAILED")
        outputs.append(result.stdout)
    observed_algorithm = outputs[0].decode("ascii").strip()
    if observed_algorithm != algorithm:
        raise ContractError("ACTIVATION_CONTROL_GIT_ALGORITHM_MISMATCH")
    return outputs[2]


def _candidate_bundle() -> ContractBundle:
    trusted = load_trusted_bundle(
        REPO_ROOT,
        TrustTuple(
            CANDIDATE_BUNDLE_GIT_OBJECT_ID,
            CANDIDATE_BUNDLE_DIGEST,
            CANDIDATE_MANIFEST_REPO_PATH,
            "CANDIDATE",
        ),
    )
    return trusted


def _combined_bundle(
    control: Mapping[str, Any],
    intent_schema: Mapping[str, Any],
    settlement_schema: Mapping[str, Any],
) -> ContractBundle:
    trusted = _candidate_bundle()
    expected_control = control_interface(
        {
            INTENT_ID: intent_schema,
            SETTLEMENT_ID: settlement_schema,
        }
    )
    if control != expected_control:
        raise ContractError("ACTIVATION_CONTROL_INTERFACE_SEMANTIC_MISMATCH")
    scan_public_value(control, trusted.policies)
    schemas = {
        **trusted.schemas,
        INTENT_ID: intent_schema,
        SETTLEMENT_ID: settlement_schema,
    }
    registry, checker = build_registry(schemas)
    pointers = {
        **trusted.self_digest_pointers,
        INTENT_ID: "/envelope_digest",
        SETTLEMENT_ID: "/envelope_digest",
    }
    return ContractBundle(
        schemas,
        registry,
        checker,
        pointers,
        trusted.policies,
        PROTOCOL_REVISION,
    )


def load_activation_bundle(
    control_trust: Optional[ActivationControlTrustTuple] = None,
    *,
    allow_current_draft: bool = False,
) -> ContractBundle:
    """Load control semantics from an external tuple or explicit lint-only draft."""

    if control_trust is None:
        if not allow_current_draft:
            raise ContractError(
                "ACTIVATION_CONTROL_EXTERNAL_TRUST_TUPLE_REQUIRED"
            )
        outputs = expected_outputs()
        for path, expected in outputs.items():
            if not path.is_file() or path.read_bytes() != expected:
                raise ContractError(
                    "ACTIVATION_CONTROL_GENERATED_DRIFT:"
                    + path.relative_to(REPO_ROOT).as_posix()
                )
        control = strict_load(CONTROL_INTERFACE_PATH)
        intent_schema = strict_load(INTENT_SCHEMA_PATH)
        settlement_schema = strict_load(SETTLEMENT_SCHEMA_PATH)
        return _combined_bundle(control, intent_schema, settlement_schema)

    if (
        control_trust.canonical_control_interface_path
        != CONTROL_INTERFACE_REPO_PATH
        or control_trust.mode != CONTROL_MODE
        or not SHA256_RE.fullmatch(
            control_trust.expected_control_interface_raw_sha256
        )
    ):
        raise ContractError("ACTIVATION_CONTROL_TRUST_TUPLE_INVALID")
    control_raw = _git_blob_for_control(
        REPO_ROOT,
        control_trust.verified_git_object_id,
        CONTROL_INTERFACE_REPO_PATH,
    )
    if (
        hashlib.sha256(control_raw).hexdigest()
        != control_trust.expected_control_interface_raw_sha256
    ):
        raise ContractError("ACTIVATION_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH")
    control = parse_json_bytes(control_raw)
    if not isinstance(control, dict):
        raise ContractError("ACTIVATION_CONTROL_INTERFACE_ROOT_INVALID")
    schema_documents: Dict[str, Mapping[str, Any]] = {}
    for schema_id, relative_path in CONTROL_SCHEMA_REPO_PATHS.items():
        document = parse_json_bytes(
            _git_blob_for_control(
                REPO_ROOT,
                control_trust.verified_git_object_id,
                relative_path,
            )
        )
        if not isinstance(document, dict) or document.get("$id") != schema_id:
            raise ContractError(
                "ACTIVATION_CONTROL_BOOTSTRAP_SCHEMA_BINDING_MISMATCH"
            )
        schema_documents[schema_id] = document
    return _combined_bundle(
        control,
        schema_documents[INTENT_ID],
        schema_documents[SETTLEMENT_ID],
    )


def validate_intent(
    instance: Mapping[str, Any],
    *,
    expected_remote_head: Optional[str] = None,
    bundle: Optional[ContractBundle] = None,
) -> Mapping[str, str]:
    contract = bundle or load_activation_bundle()
    validate_instance(
        contract,
        instance,
        INTENT_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        public=True,
    )
    if (
        instance["protocol_revision"] != PROTOCOL_REVISION
        or instance["bundle_digest"] != CANDIDATE_BUNDLE_DIGEST
        or instance["bundle_git_object_id"] != CANDIDATE_BUNDLE_GIT_OBJECT_ID
        or instance["candidate_manifest_path"] != CANDIDATE_MANIFEST_REPO_PATH
        or instance["target_srv_revision"] != TARGET_SRV_REVISION
        or instance["recipient_ref"] != "owner-primary"
        or instance["rollback_target_ref"] != instance["expected_remote_head"]
        or instance["notification_affected_path_refs"]
        != list(NOTIFICATION_AFFECTED_PATH_REFS)
    ):
        raise ContractError("ACTIVATION_INTENT_CONTEXT_MISMATCH")
    if (
        expected_remote_head is not None
        and instance["expected_remote_head"] != expected_remote_head
    ):
        raise ContractError("ACTIVATION_INTENT_EXPECTED_HEAD_MISMATCH")

    paths = _activation_paths(instance["activation_uid"])
    expected = {
        VERSION_PATH: (
            "ACTIVE_VERSION_MARKER",
            "BOUND_IN_INTENT",
            _sha256((TARGET_SRV_REVISION + "\n").encode("ascii")),
        ),
        HANDOFF_PATH: (
            "MECHANISM_HANDOFF",
            "DERIVED_AFTER_PROVIDER_SENT",
            None,
        ),
        paths["intent"]: (
            "ACTIVATION_INTENT",
            "SELF_DIGESTED_INTENT",
            None,
        ),
        paths["notification"]: (
            "NOTIFICATION_RECEIPT",
            "DERIVED_AFTER_PROVIDER_SENT",
            None,
        ),
        paths["settlement"]: (
            "ACTIVATION_SETTLEMENT",
            "DERIVED_AFTER_PROVIDER_SENT",
            None,
        ),
    }
    rows = instance["planned_artifacts"]
    _sorted_unique(
        rows,
        "artifact_repo_path",
        "ACTIVATION_INTENT_ARTIFACT_ORDER_INVALID",
    )
    observed: Dict[str, tuple] = {}
    for row in rows:
        path = row["artifact_repo_path"]
        observed[path] = (
            row["artifact_role"],
            row["digest_availability"],
            row.get("artifact_digest"),
        )
    if observed != expected:
        raise ContractError("ACTIVATION_INTENT_PLANNED_WRITE_SET_MISMATCH")
    if instance["envelope_digest"] != canonical_digest(
        instance, "/envelope_digest"
    ):
        raise ContractError("ACTIVATION_INTENT_SELF_DIGEST_MISMATCH")
    scan_public_value(instance, contract.policies)
    return paths


def _evidence_map(
    instance: Mapping[str, Any],
) -> Mapping[str, Mapping[str, Any]]:
    rows = instance["evidence_refs"]
    _sorted_unique(
        rows,
        "evidence_type",
        "ACTIVATION_SETTLEMENT_EVIDENCE_ORDER_INVALID",
    )
    output = {row["evidence_type"]: row for row in rows}
    if set(output) != {"ACTIVATION_INTENT", "NOTIFICATION_RECEIPT"}:
        raise ContractError("ACTIVATION_SETTLEMENT_EVIDENCE_SET_INVALID")
    return output


def notification_metadata(intent: Mapping[str, Any]) -> Mapping[str, Any]:
    """Return the only public-safe MAJOR metadata bound to an activation intent."""

    return {
        "impact": "MAJOR",
        "change_code": "ACTIVE_BUNDLE_CHANGE",
        "planned_action": "ACTIVATE",
        "affected_path_refs": list(intent["notification_affected_path_refs"]),
        "evidence_digests": sorted(
            [intent["bundle_digest"], intent["envelope_digest"]]
        ),
        "rollback_target_ref": intent["rollback_target_ref"],
    }


def notification_policy_digest(contract: ContractBundle) -> str:
    policy = contract.policies.get(NOTIFICATION_POLICY_ID)
    if not isinstance(policy, dict):
        raise ContractError("ACTIVATION_NOTIFICATION_POLICY_NOT_TRUSTED")
    return _sha256(canonicalize_object(policy))


def validate_settlement(
    settlement: Mapping[str, Any],
    *,
    intent: Mapping[str, Any],
    notification_receipt: Mapping[str, Any],
    artifact_payloads: Mapping[str, bytes],
    expected_remote_head: Optional[str] = None,
    bundle: Optional[ContractBundle] = None,
) -> Mapping[str, str]:
    contract = bundle or load_activation_bundle()
    declared_settlement_digest = settlement.get("envelope_digest")
    handoff_payload = artifact_payloads.get(HANDOFF_PATH)
    if (
        isinstance(declared_settlement_digest, str)
        and isinstance(handoff_payload, bytes)
        and declared_settlement_digest.encode("ascii", errors="ignore")
        in handoff_payload
    ):
        raise ContractError("ACTIVATION_HANDOFF_SETTLEMENT_DIGEST_CYCLE")
    paths = validate_intent(
        intent,
        expected_remote_head=expected_remote_head,
        bundle=contract,
    )
    validate_instance(
        contract,
        notification_receipt,
        NOTIFICATION_RECEIPT_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        public=True,
    )
    validate_instance(
        contract,
        settlement,
        SETTLEMENT_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        public=True,
    )
    if (
        settlement["activation_uid"] != intent["activation_uid"]
        or settlement["auto_transaction_uid"] != intent["auto_transaction_uid"]
        or settlement["expected_remote_head"] != intent["expected_remote_head"]
        or settlement["target_srv_revision"] != intent["target_srv_revision"]
        or settlement["recipient_ref"] != intent["recipient_ref"]
        or settlement["bundle_digest"] != intent["bundle_digest"]
    ):
        raise ContractError("ACTIVATION_SETTLEMENT_INTENT_CONTEXT_MISMATCH")
    if (
        notification_receipt["notification_uid"]
        != intent["notification_uid"]
        or notification_receipt["auto_transaction_uid"]
        != intent["auto_transaction_uid"]
        or notification_receipt["bundle_digest"] != intent["bundle_digest"]
        or notification_receipt["recipient_ref"] != intent["recipient_ref"]
        or notification_receipt["impact"] != "MAJOR"
        or notification_receipt["timing"] != "PRE_WRITE"
        or notification_receipt["provider_status"] != "SENT"
        or notification_receipt["notification_policy_id"]
        != NOTIFICATION_POLICY_ID
        or notification_receipt["approval_required"] is not False
        or notification_receipt["owner_reply_required"] is not False
    ):
        raise ContractError("ACTIVATION_NOTIFICATION_RECEIPT_NOT_RELEASE_GRADE")
    expected_metadata = notification_metadata(intent)
    scan_public_value(expected_metadata, contract.policies)
    if (
        notification_receipt["metadata_digest"]
        != _sha256(canonicalize_object(expected_metadata))
        or notification_receipt["policy_snapshot_digest"]
        != notification_policy_digest(contract)
    ):
        raise ContractError("ACTIVATION_NOTIFICATION_RECEIPT_DIGEST_BINDING_MISMATCH")
    if not (
        _utc(intent["created_at"])
        <= _utc(notification_receipt["sent_at"])
        <= _utc(settlement["created_at"])
    ):
        raise ContractError("ACTIVATION_SETTLEMENT_TIME_ORDER_INVALID")

    evidence = _evidence_map(settlement)
    expected_evidence = {
        "ACTIVATION_INTENT": {
            "evidence_type": "ACTIVATION_INTENT",
            "evidence_uid": intent["envelope_uid"],
            "evidence_digest": intent["envelope_digest"],
            "artifact_repo_path": paths["intent"],
        },
        "NOTIFICATION_RECEIPT": {
            "evidence_type": "NOTIFICATION_RECEIPT",
            "evidence_uid": notification_receipt["receipt_uid"],
            "evidence_digest": notification_receipt["receipt_digest"],
            "artifact_repo_path": paths["notification"],
        },
    }
    if evidence != expected_evidence:
        raise ContractError("ACTIVATION_SETTLEMENT_EVIDENCE_BINDING_MISMATCH")

    rows = settlement["artifacts"]
    _sorted_unique(
        rows,
        "artifact_repo_path",
        "ACTIVATION_SETTLEMENT_ARTIFACT_ORDER_INVALID",
    )
    expected_paths = {
        VERSION_PATH,
        HANDOFF_PATH,
        paths["intent"],
        paths["notification"],
    }
    if {row["artifact_repo_path"] for row in rows} != expected_paths:
        raise ContractError("ACTIVATION_SETTLEMENT_ARTIFACT_SET_MISMATCH")
    if set(artifact_payloads) != expected_paths:
        raise ContractError("ACTIVATION_SETTLEMENT_PAYLOAD_SET_MISMATCH")
    planned_roles = {
        row["artifact_repo_path"]: row["artifact_role"]
        for row in intent["planned_artifacts"]
    }
    for row in rows:
        path = row["artifact_repo_path"]
        if row["artifact_role"] != planned_roles[path]:
            raise ContractError("ACTIVATION_SETTLEMENT_ARTIFACT_ROLE_MISMATCH")
        if row["artifact_digest"] != _sha256(artifact_payloads[path]):
            raise ContractError("ACTIVATION_SETTLEMENT_PHYSICAL_DIGEST_MISMATCH")
        expected_schema_id = None
        expected_uid = None
        if path == paths["intent"]:
            expected_schema_id = INTENT_ID
            expected_uid = intent["envelope_uid"]
            if artifact_payloads[path] != canonicalize_object(intent):
                raise ContractError("ACTIVATION_SETTLEMENT_INTENT_BYTES_MISMATCH")
        elif path == paths["notification"]:
            expected_schema_id = NOTIFICATION_RECEIPT_ID
            expected_uid = notification_receipt["receipt_uid"]
            if artifact_payloads[path] != canonicalize_object(
                notification_receipt
            ):
                raise ContractError(
                    "ACTIVATION_SETTLEMENT_NOTIFICATION_BYTES_MISMATCH"
                )
        if row.get("artifact_schema_id") != expected_schema_id:
            raise ContractError("ACTIVATION_SETTLEMENT_ARTIFACT_SCHEMA_MISMATCH")
        if expected_uid is not None and row["artifact_uid"] != expected_uid:
            raise ContractError("ACTIVATION_SETTLEMENT_ARTIFACT_UID_MISMATCH")
    if artifact_payloads[VERSION_PATH] != (
        TARGET_SRV_REVISION + "\n"
    ).encode("ascii"):
        raise ContractError("ACTIVATION_VERSION_PAYLOAD_MISMATCH")
    if settlement["envelope_digest"] != canonical_digest(
        settlement, "/envelope_digest"
    ):
        raise ContractError("ACTIVATION_SETTLEMENT_SELF_DIGEST_MISMATCH")
    scan_public_value(notification_receipt, contract.policies)
    scan_public_value(settlement, contract.policies)
    return {
        "intent_envelope_digest": intent["envelope_digest"],
        "notification_receipt_digest": notification_receipt["receipt_digest"],
        "settlement_envelope_digest": settlement["envelope_digest"],
        "settlement_repo_path": paths["settlement"],
    }


def _regular_file_under(root: Path, relative_path: str) -> bytes:
    if not is_repo_relative_posix_path(relative_path):
        raise ContractError("ACTIVATION_ARTIFACT_PATH_INVALID")
    required_flags = ("O_DIRECTORY", "O_NOFOLLOW")
    if any(not hasattr(os, name) for name in required_flags):
        raise ContractError("ACTIVATION_NOFOLLOW_CAPABILITY_UNAVAILABLE")
    try:
        root_info = os.lstat(root)
    except OSError as exc:
        raise ContractError("ACTIVATION_ARTIFACT_ROOT_UNAVAILABLE") from exc
    if stat.S_ISLNK(root_info.st_mode) or not stat.S_ISDIR(root_info.st_mode):
        raise ContractError("ACTIVATION_ARTIFACT_ROOT_NOT_REAL_DIRECTORY")
    descriptors = []
    try:
        directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            directory_flags |= os.O_CLOEXEC
        current_fd = os.open(str(root), directory_flags)
        descriptors.append(current_fd)
        parts = PurePosixPath(relative_path).parts
        for part in parts[:-1]:
            current_fd = os.open(part, directory_flags, dir_fd=current_fd)
            descriptors.append(current_fd)
            if not stat.S_ISDIR(os.fstat(current_fd).st_mode):
                raise ContractError(
                    "ACTIVATION_ARTIFACT_PARENT_NOT_DIRECTORY"
                )
        file_flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            file_flags |= os.O_CLOEXEC
        file_fd = os.open(parts[-1], file_flags, dir_fd=current_fd)
        descriptors.append(file_fd)
        if not stat.S_ISREG(os.fstat(file_fd).st_mode):
            raise ContractError("ACTIVATION_ARTIFACT_NOT_REGULAR")
        chunks = []
        while True:
            chunk = os.read(file_fd, 1024 * 1024)
            if not chunk:
                return b"".join(chunks)
            chunks.append(chunk)
    except ContractError:
        raise
    except OSError as exc:
        raise ContractError(
            "ACTIVATION_ARTIFACT_SYMLINK_OR_UNAVAILABLE"
        ) from exc
    finally:
        for descriptor in reversed(descriptors):
            try:
                os.close(descriptor)
            except OSError:
                pass


def _main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("lint-control")

    def add_control_trust(command: argparse.ArgumentParser) -> None:
        command.add_argument(
            "--verified-control-git-object-id",
            required=True,
        )
        command.add_argument(
            "--expected-control-interface-raw-sha256",
            required=True,
        )
        command.add_argument(
            "--canonical-control-interface-path",
            required=True,
        )
        command.add_argument(
            "--control-mode",
            required=True,
            choices=(CONTROL_MODE,),
        )

    intent_cmd = commands.add_parser("validate-intent")
    add_control_trust(intent_cmd)
    intent_cmd.add_argument("--artifact-root", type=Path, required=True)
    intent_cmd.add_argument("--intent-repo-path", required=True)
    intent_cmd.add_argument("--expected-remote-head", required=True)
    settlement_cmd = commands.add_parser("validate-settlement")
    add_control_trust(settlement_cmd)
    settlement_cmd.add_argument("--artifact-root", type=Path, required=True)
    settlement_cmd.add_argument("--settlement-repo-path", required=True)
    settlement_cmd.add_argument("--expected-remote-head", required=True)
    args = parser.parse_args(argv)

    if args.command == "lint-control":
        bundle = load_activation_bundle(allow_current_draft=True)
        interface = strict_load(CONTROL_INTERFACE_PATH)
        if (
            interface.get("status") != "DRAFT_NON_ACTIVE"
            or interface.get("activation_forbidden") is not True
            or interface.get("bundle_digest") != CANDIDATE_BUNDLE_DIGEST
            or interface.get("bootstrap_schema_count") != 2
        ):
            raise ContractError("ACTIVATION_CONTROL_INTERFACE_MISMATCH")
        print(
            "ACTIVATION_CONTROL_VALID "
            f"schemas=2 bundle_digest={CANDIDATE_BUNDLE_DIGEST}"
        )
        return 0
    bundle = load_activation_bundle(
        ActivationControlTrustTuple(
            args.verified_control_git_object_id,
            args.expected_control_interface_raw_sha256,
            args.canonical_control_interface_path,
            args.control_mode,
        )
    )
    if args.command == "validate-intent":
        intent_raw = _regular_file_under(
            args.artifact_root, args.intent_repo_path
        )
        intent = parse_json_bytes(intent_raw)
        if (
            not isinstance(intent, dict)
            or intent_raw != canonicalize_object(intent)
        ):
            raise ContractError("ACTIVATION_INTENT_BYTES_NOT_CANONICAL")
        paths = validate_intent(
            intent,
            expected_remote_head=args.expected_remote_head,
            bundle=bundle,
        )
        if args.intent_repo_path != paths["intent"]:
            raise ContractError("ACTIVATION_INTENT_REPO_PATH_MISMATCH")
        print("ACTIVATION_INTENT_VALID")
        return 0

    settlement_raw = _regular_file_under(
        args.artifact_root, args.settlement_repo_path
    )
    settlement = parse_json_bytes(settlement_raw)
    if (
        not isinstance(settlement, dict)
        or settlement_raw != canonicalize_object(settlement)
    ):
        raise ContractError("ACTIVATION_SETTLEMENT_BYTES_NOT_CANONICAL")
    validate_instance(
        bundle,
        settlement,
        SETTLEMENT_ID,
        expected_bundle_digest=CANDIDATE_BUNDLE_DIGEST,
        public=True,
    )
    evidence = _evidence_map(settlement)
    expected_settlement_path = _activation_paths(
        settlement["activation_uid"]
    )["settlement"]
    if args.settlement_repo_path != expected_settlement_path:
        raise ContractError("ACTIVATION_SETTLEMENT_REPO_PATH_MISMATCH")
    intent_path = evidence["ACTIVATION_INTENT"]["artifact_repo_path"]
    receipt_path = evidence["NOTIFICATION_RECEIPT"]["artifact_repo_path"]
    intent = parse_json_bytes(_regular_file_under(args.artifact_root, intent_path))
    receipt = parse_json_bytes(_regular_file_under(args.artifact_root, receipt_path))
    if not isinstance(intent, dict) or not isinstance(receipt, dict):
        raise ContractError("ACTIVATION_EVIDENCE_ROOT_INVALID")
    payloads = {
        row["artifact_repo_path"]: _regular_file_under(
            args.artifact_root, row["artifact_repo_path"]
        )
        for row in settlement["artifacts"]
    }
    validate_settlement(
        settlement,
        intent=intent,
        notification_receipt=receipt,
        artifact_payloads=payloads,
        expected_remote_head=args.expected_remote_head,
        bundle=bundle,
    )
    print("ACTIVATION_SETTLEMENT_VALID")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(_main())
    except ContractError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2)
