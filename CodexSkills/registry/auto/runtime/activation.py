"""Externally trusted two-stage activation handshake for SkillOps Auto."""

from __future__ import annotations

import importlib
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping, Tuple

from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
)

from .bootstrap import BootstrapContext, ControlTrustTuple
from .core import AutoRuntimeError


CONTROL_INTERFACE_PATH = (
    "CodexSkills/governance/activation/control-interface.json"
)
CONTROL_MODE = "DRAFT_NON_ACTIVE_CONTROL"
CONTROL_RUNTIME_PATHS = (
    "CodexSkills/governance/tools/build_activation_control.py",
    "CodexSkills/governance/tools/validate_activation.py",
)
GIT_OBJECT_RE = re.compile(
    r"^(?:(sha1):([0-9a-f]{40})|(sha256):([0-9a-f]{64}))$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
MAX_CONTROL_ARTIFACT_BYTES = 1024 * 1024


ActivationControlTrustTuple = ControlTrustTuple


@dataclass(frozen=True)
class VerifiedActivationIntent:
    payload: bytes
    repo_path: str
    expected_remote_head: str
    auto_transaction_uid: str
    notification_uid: str
    target_srv_revision: str
    created_at: str
    paths: Mapping[str, str]
    notification_metadata: Mapping[str, object]


@dataclass(frozen=True)
class VerifiedActivationSettlement:
    settlement_payload: bytes
    settlement_repo_path: str
    expected_remote_head: str
    auto_transaction_uid: str
    payloads: Mapping[str, bytes]
    artifact_paths: Tuple[str, ...]


def _run_git(repo_root: Path, *args: str) -> bytes:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AutoRuntimeError("ACTIVATION_CONTROL_GIT_UNAVAILABLE") from exc
    if result.returncode != 0:
        raise AutoRuntimeError("ACTIVATION_CONTROL_GIT_READ_FAILED")
    return result.stdout


def _git_blob(
    repo_root: Path,
    verified_git_object_id: str,
    relative_path: str,
) -> bytes:
    match = GIT_OBJECT_RE.fullmatch(verified_git_object_id)
    if not match:
        raise AutoRuntimeError("ACTIVATION_CONTROL_GIT_OBJECT_ID_INVALID")
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    observed_algorithm = _run_git(
        repo_root, "rev-parse", "--show-object-format"
    ).decode("ascii", errors="strict").strip()
    if observed_algorithm != algorithm:
        raise AutoRuntimeError("ACTIVATION_CONTROL_GIT_ALGORITHM_MISMATCH")
    _run_git(repo_root, "cat-file", "-e", f"{object_id}^{{commit}}")
    return _run_git(repo_root, "show", f"{object_id}:{relative_path}")


def _verify_control_runtime(
    repo_root: Path,
    trust: ActivationControlTrustTuple,
) -> None:
    if (
        trust.canonical_control_interface_path != CONTROL_INTERFACE_PATH
        or trust.mode != CONTROL_MODE
        or not SHA256_RE.fullmatch(
            trust.expected_control_interface_raw_sha256
        )
    ):
        raise AutoRuntimeError("ACTIVATION_CONTROL_TRUST_TUPLE_INVALID")
    for relative_path in CONTROL_RUNTIME_PATHS:
        local_path = repo_root.joinpath(*relative_path.split("/"))
        try:
            local = local_path.read_bytes()
        except OSError as exc:
            raise AutoRuntimeError(
                "ACTIVATION_CONTROL_RUNTIME_READ_FAILED"
            ) from exc
        if local != _git_blob(
            repo_root,
            trust.verified_git_object_id,
            relative_path,
        ):
            raise AutoRuntimeError("ACTIVATION_CONTROL_RUNTIME_LOCAL_DRIFT")


def _load_control_module(repo_root: Path):
    tools_path = (
        repo_root / "CodexSkills" / "governance" / "tools"
    ).resolve(strict=True)
    expected_path = (tools_path / "validate_activation.py").resolve(
        strict=True
    )
    expected_modules = {
        "build_activation_control": (
            tools_path / "build_activation_control.py"
        ).resolve(strict=True),
        "validate_activation": expected_path,
    }
    for name, expected in expected_modules.items():
        existing = sys.modules.get(name)
        if existing is None:
            continue
        observed = Path(str(getattr(existing, "__file__", ""))).resolve()
        if observed != expected:
            raise AutoRuntimeError(
                "ACTIVATION_CONTROL_MODULE_IDENTITY_CONFLICT"
            )
        del sys.modules[name]
    sys.path.insert(0, str(tools_path))
    try:
        module = importlib.import_module("validate_activation")
    except Exception as exc:
        raise AutoRuntimeError(
            "ACTIVATION_CONTROL_MODULE_IMPORT_FAILED"
        ) from exc
    finally:
        if sys.path and sys.path[0] == str(tools_path):
            sys.path.pop(0)
    observed = Path(str(getattr(module, "__file__", ""))).resolve()
    if observed != expected_path:
        raise AutoRuntimeError("ACTIVATION_CONTROL_MODULE_IDENTITY_CONFLICT")
    return module


def _canonical_mapping(payload: bytes, label: str) -> Mapping[str, Any]:
    if (
        not isinstance(payload, bytes)
        or not payload
        or len(payload) > MAX_CONTROL_ARTIFACT_BYTES
    ):
        raise AutoRuntimeError(f"{label}_BYTES_INVALID")
    try:
        value = parse_json_bytes(payload)
    except Exception as exc:
        raise AutoRuntimeError(f"{label}_JSON_INVALID") from exc
    if not isinstance(value, dict):
        raise AutoRuntimeError(f"{label}_ROOT_INVALID")
    if canonicalize_object(value) != payload:
        raise AutoRuntimeError(f"{label}_BYTES_NOT_CANONICAL")
    return value


class ActivationHandshake:
    """Validate activation control only through two external trust tuples."""

    def __init__(
        self,
        repo_root: Path,
        candidate_context: BootstrapContext,
        control_trust: ActivationControlTrustTuple,
    ) -> None:
        self.repo_root = repo_root.resolve(strict=True)
        self.candidate_context = candidate_context
        self.control_trust = control_trust
        if candidate_context.trust.mode != "CANDIDATE":
            raise AutoRuntimeError(
                "ACTIVATION_CANDIDATE_TRUST_MODE_REQUIRED"
            )
        if candidate_context.control_trust != control_trust:
            raise AutoRuntimeError(
                "ACTIVATION_CONTROL_CONTEXT_MISMATCH"
            )
        _verify_control_runtime(self.repo_root, control_trust)
        self.module = _load_control_module(self.repo_root)
        if (
            candidate_context.trust.verified_git_object_id
            != self.module.CANDIDATE_BUNDLE_GIT_OBJECT_ID
            or candidate_context.trust.expected_bundle_digest
            != self.module.CANDIDATE_BUNDLE_DIGEST
            or candidate_context.trust.canonical_manifest_path
            != self.module.CANDIDATE_MANIFEST_REPO_PATH
        ):
            raise AutoRuntimeError("ACTIVATION_CANDIDATE_TRUST_MISMATCH")
        try:
            module_trust = self.module.ActivationControlTrustTuple(
                control_trust.verified_git_object_id,
                control_trust.expected_control_interface_raw_sha256,
                control_trust.canonical_control_interface_path,
                control_trust.mode,
            )
            self.bundle = self.module.load_activation_bundle(module_trust)
        except self.module.ContractError as exc:
            raise AutoRuntimeError(
                f"ACTIVATION_CONTROL_TRUST_FAILED:{exc}"
            ) from exc
        if (
            len(self.bundle.schemas) != 33
            or len(self.bundle.policies) != 5
        ):
            raise AutoRuntimeError("ACTIVATION_CONTROL_CLOSURE_MISMATCH")

    def _read_artifact(self, root: Path, relative_path: str) -> bytes:
        try:
            payload = self.module._regular_file_under(root, relative_path)
        except self.module.ContractError as exc:
            raise AutoRuntimeError(
                f"ACTIVATION_ARTIFACT_READ_FAILED:{exc}"
            ) from exc
        if len(payload) > MAX_CONTROL_ARTIFACT_BYTES:
            raise AutoRuntimeError("ACTIVATION_ARTIFACT_SIZE_INVALID")
        return payload

    def _verify_intent(
        self,
        payload: bytes,
        repo_path: str,
        expected_remote_head: str,
    ) -> VerifiedActivationIntent:
        intent = _canonical_mapping(payload, "ACTIVATION_INTENT")
        try:
            paths = self.module.validate_intent(
                intent,
                expected_remote_head=expected_remote_head,
                bundle=self.bundle,
            )
            if repo_path != paths["intent"]:
                raise self.module.ContractError(
                    "ACTIVATION_INTENT_REPO_PATH_MISMATCH"
                )
            metadata = self.module.notification_metadata(intent)
            self.module.scan_public_value(metadata, self.bundle.policies)
        except self.module.ContractError as exc:
            raise AutoRuntimeError(
                f"ACTIVATION_INTENT_VALIDATION_FAILED:{exc}"
            ) from exc
        return VerifiedActivationIntent(
            payload=payload,
            repo_path=repo_path,
            expected_remote_head=str(intent["expected_remote_head"]),
            auto_transaction_uid=str(intent["auto_transaction_uid"]),
            notification_uid=str(intent["notification_uid"]),
            target_srv_revision=str(intent["target_srv_revision"]),
            created_at=str(intent["created_at"]),
            paths=MappingProxyType(dict(paths)),
            notification_metadata=MappingProxyType(dict(metadata)),
        )

    def verify_intent_root(
        self,
        artifact_root: Path,
        intent_repo_path: str,
        expected_remote_head: str,
    ) -> VerifiedActivationIntent:
        payload = self._read_artifact(artifact_root, intent_repo_path)
        return self._verify_intent(
            payload,
            intent_repo_path,
            expected_remote_head,
        )

    def verify_settlement_root(
        self,
        artifact_root: Path,
        settlement_repo_path: str,
        expected_remote_head: str,
    ) -> VerifiedActivationSettlement:
        settlement_payload = self._read_artifact(
            artifact_root, settlement_repo_path
        )
        settlement = _canonical_mapping(
            settlement_payload, "ACTIVATION_SETTLEMENT"
        )
        try:
            self.module.validate_instance(
                self.bundle,
                settlement,
                self.module.SETTLEMENT_ID,
                expected_bundle_digest=self.module.CANDIDATE_BUNDLE_DIGEST,
                public=True,
            )
            expected_settlement_path = self.module._activation_paths(
                settlement["activation_uid"]
            )["settlement"]
            if settlement_repo_path != expected_settlement_path:
                raise self.module.ContractError(
                    "ACTIVATION_SETTLEMENT_REPO_PATH_MISMATCH"
                )
            evidence = self.module._evidence_map(settlement)
            intent_path = evidence["ACTIVATION_INTENT"][
                "artifact_repo_path"
            ]
            receipt_path = evidence["NOTIFICATION_RECEIPT"][
                "artifact_repo_path"
            ]
            intent_payload = self._read_artifact(
                artifact_root, intent_path
            )
            receipt_payload = self._read_artifact(
                artifact_root, receipt_path
            )
            intent = _canonical_mapping(
                intent_payload, "ACTIVATION_INTENT"
            )
            receipt = _canonical_mapping(
                receipt_payload, "ACTIVATION_NOTIFICATION_RECEIPT"
            )
            payloads = {
                row["artifact_repo_path"]: self._read_artifact(
                    artifact_root, row["artifact_repo_path"]
                )
                for row in settlement["artifacts"]
            }
            result = self.module.validate_settlement(
                settlement,
                intent=intent,
                notification_receipt=receipt,
                artifact_payloads=payloads,
                expected_remote_head=expected_remote_head,
                bundle=self.bundle,
            )
            if result["settlement_repo_path"] != settlement_repo_path:
                raise self.module.ContractError(
                    "ACTIVATION_SETTLEMENT_REPO_PATH_MISMATCH"
                )
        except AutoRuntimeError:
            raise
        except self.module.ContractError as exc:
            raise AutoRuntimeError(
                f"ACTIVATION_SETTLEMENT_VALIDATION_FAILED:{exc}"
            ) from exc
        complete_payloads = dict(payloads)
        complete_payloads[settlement_repo_path] = settlement_payload
        artifact_paths = tuple(sorted(complete_payloads))
        return VerifiedActivationSettlement(
            settlement_payload=settlement_payload,
            settlement_repo_path=settlement_repo_path,
            expected_remote_head=str(settlement["expected_remote_head"]),
            auto_transaction_uid=str(
                settlement["auto_transaction_uid"]
            ),
            payloads=MappingProxyType(complete_payloads),
            artifact_paths=artifact_paths,
        )
