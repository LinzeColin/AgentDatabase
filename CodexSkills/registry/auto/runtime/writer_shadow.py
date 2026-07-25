"""Development-only proof for an unbound AU-040 runtime candidate.

The result is deliberately not a production ``BootstrapContext``.  It proves
historical control closure and current byte self-consistency without touching
state, Gmail, notification, publication, or Git remote backends.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path

from CodexSkills.governance.tools.canonical_json import parse_json_bytes
from CodexSkills.governance.tools.validate_mechanism import TrustTuple
from CodexSkills.registry.auto.tools.validate_auto import (
    load_trusted_auto_contract,
)

from .bootstrap import (
    CONTROL_INTERFACE_PATH,
    CONTROL_MODE,
    ControlTrustTuple,
    _git_blob,
    _split_git_object,
)
from .core import AutoRuntimeError, CANDIDATE_MANIFEST_PATH


CANDIDATE_GIT_OBJECT = (
    "sha1:5ee37d7499c62ec19381dac7eb95cb12743ad2d5"
)
CANDIDATE_BUNDLE_DIGEST = (
    "36f0c66dd54d36365700a13f614a8c9bfa9619fb7c532af77566a858175b835e"
)
CONTROL_GIT_OBJECT = (
    "sha1:e6438db785c2f3f38da59be7ba9c1cd46651d7ea"
)
CONTROL_RAW_SHA256 = (
    "28a35148cc18362de4fc53b508754f263"
    "a015cf33e4cd187314cf48c767b6920"
)
BOUND_AUTO_GIT_OBJECT = (
    "sha1:85edc67df48d4e5bc783f89ed3f3371f25f288e1"
)
BOUND_AUTO_INTERFACE_RAW_SHA256 = (
    "ce3aae7a22419c3a01455e8e83cc67b2"
    "3eeb2ada3f3c17e57590a890c0fdef31"
)
BOUND_AUTO_MODULE_COUNT = 25
PUBLISHER_MATERIALIZATION_CONTROL_GIT_OBJECT = (
    "sha1:fb9b99c36cb870b04f34b5ed3bcb75aeae52c296"
)
RUNTIME_INTERFACE_PATH = (
    "CodexSkills/registry/auto/runtime-interface.json"
)


@dataclass(frozen=True)
class UnboundWriterCandidateEvidence:
    status: str
    schema_count: int
    policy_count: int
    historical_control_object: str
    historical_bound_auto_object: str
    historical_bound_module_count: int
    current_module_count: int
    current_runtime_interface_raw_sha256: str
    current_runtime_control_bound_at_materialization: bool
    runtime_state_write_permitted: bool
    runtime_shard_writer_integration_complete: bool
    publisher_v2_runtime_integration_complete: bool
    repository_binding_integration_complete: bool
    repository_bound: bool
    bound_reference_resolver_gate_satisfied: bool


def validate_unbound_writer_candidate(
    repo_root: Path,
    candidate_trust: TrustTuple,
    control_trust: ControlTrustTuple,
) -> UnboundWriterCandidateEvidence:
    """Prove historical and current offline closure without production trust."""

    if (
        candidate_trust.verified_git_object_id
        != CANDIDATE_GIT_OBJECT
        or candidate_trust.expected_bundle_digest
        != CANDIDATE_BUNDLE_DIGEST
        or candidate_trust.canonical_manifest_path
        != CANDIDATE_MANIFEST_PATH
        or candidate_trust.mode != "CANDIDATE"
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_CANDIDATE_TRUST_TUPLE_MISMATCH"
        )
    if (
        control_trust.verified_git_object_id != CONTROL_GIT_OBJECT
        or control_trust.expected_control_interface_raw_sha256
        != CONTROL_RAW_SHA256
        or control_trust.canonical_control_interface_path
        != CONTROL_INTERFACE_PATH
        or control_trust.mode != CONTROL_MODE
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_CONTROL_TRUST_TUPLE_MISMATCH"
        )

    root = repo_root.resolve()
    control_object_id = _split_git_object(
        root,
        CONTROL_GIT_OBJECT,
        "WRITER_SHADOW_CONTROL",
    )
    control_raw = _git_blob(
        root,
        control_object_id,
        CONTROL_INTERFACE_PATH,
    )
    if hashlib.sha256(control_raw).hexdigest() != CONTROL_RAW_SHA256:
        raise AutoRuntimeError(
            "WRITER_SHADOW_CONTROL_RAW_DIGEST_MISMATCH"
        )
    try:
        control = parse_json_bytes(control_raw)
    except Exception as exc:
        raise AutoRuntimeError(
            "WRITER_SHADOW_CONTROL_JSON_INVALID"
        ) from exc
    transport = (
        control.get("transport_runtime_interface")
        if isinstance(control, dict)
        else None
    )
    transition = (
        control.get("transition_contract")
        if isinstance(control, dict)
        else None
    )
    if (
        not isinstance(transport, dict)
        or not isinstance(transition, dict)
        or transport.get("verified_git_object_id")
        != BOUND_AUTO_GIT_OBJECT
        or transport.get("artifact_digest")
        != BOUND_AUTO_INTERFACE_RAW_SHA256
        or transport.get("module_count") != BOUND_AUTO_MODULE_COUNT
        or transition.get("auto_runtime_integration_complete")
        is not True
        or transition.get("runtime_state_write_permitted") is not True
        or transition.get("runtime_shard_writer_integration_complete")
        is not True
        or transition.get("publisher_v2_runtime_integration_complete")
        is not True
        or transition.get("repository_bound") is not False
        or control.get("next_phase")
        != "AUTO_AU040_REPOSITORY_BINDING"
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_HISTORICAL_CONTROL_CONTRACT_MISMATCH"
        )

    bound_object_id = _split_git_object(
        root,
        BOUND_AUTO_GIT_OBJECT,
        "WRITER_SHADOW_BOUND_AUTO",
    )
    bound_raw = _git_blob(
        root,
        bound_object_id,
        RUNTIME_INTERFACE_PATH,
    )
    if (
        hashlib.sha256(bound_raw).hexdigest()
        != BOUND_AUTO_INTERFACE_RAW_SHA256
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_BOUND_INTERFACE_DIGEST_MISMATCH"
        )
    try:
        bound = parse_json_bytes(bound_raw)
    except Exception as exc:
        raise AutoRuntimeError(
            "WRITER_SHADOW_BOUND_INTERFACE_JSON_INVALID"
        ) from exc
    artifacts = (
        bound.get("module_artifacts")
        if isinstance(bound, dict)
        else None
    )
    if (
        not isinstance(artifacts, list)
        or bound.get("module_count") != BOUND_AUTO_MODULE_COUNT
        or len(artifacts) != BOUND_AUTO_MODULE_COUNT
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_BOUND_MODULE_SET_INVALID"
        )
    paths = []
    for artifact in artifacts:
        if (
            not isinstance(artifact, dict)
            or not isinstance(artifact.get("relative_path"), str)
            or not isinstance(artifact.get("artifact_digest"), str)
        ):
            raise AutoRuntimeError(
                "WRITER_SHADOW_BOUND_MODULE_ENTRY_INVALID"
            )
        relative_path = artifact["relative_path"]
        paths.append(relative_path)
        raw = _git_blob(root, bound_object_id, relative_path)
        if hashlib.sha256(raw).hexdigest() != artifact[
            "artifact_digest"
        ]:
            raise AutoRuntimeError(
                "WRITER_SHADOW_BOUND_MODULE_DIGEST_MISMATCH"
            )
    if paths != sorted(paths) or len(paths) != len(set(paths)):
        raise AutoRuntimeError(
            "WRITER_SHADOW_BOUND_MODULE_SET_INVALID"
        )

    contract = load_trusted_auto_contract(root, candidate_trust)
    if (
        len(contract.shared.schemas) != 31
        or len(contract.shared.policies) != 5
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_FINAL_BUNDLE_PROFILE_REQUIRED"
        )

    from CodexSkills.registry.auto.tools import build_runtime_interface

    expected_current = build_runtime_interface.render(
        build_runtime_interface.build()
    )
    try:
        current_raw = root.joinpath(
            *RUNTIME_INTERFACE_PATH.split("/")
        ).read_bytes()
    except OSError as exc:
        raise AutoRuntimeError(
            "WRITER_SHADOW_CURRENT_INTERFACE_READ_FAILED"
        ) from exc
    if current_raw != expected_current:
        raise AutoRuntimeError(
            "WRITER_SHADOW_CURRENT_INTERFACE_NOT_BYTE_EQUIVALENT"
        )
    current = parse_json_bytes(current_raw)
    current_artifacts = current.get("module_artifacts")
    materialization = current.get(
        "runtime_interface_materialization_snapshot"
    )
    publisher_materialization = current.get(
        "publisher_v2_runtime_materialization_snapshot"
    )
    repository_materialization = current.get(
        "repository_binding_materialization_snapshot"
    )
    historical_control = current.get(
        "historical_control_observation"
    )
    if (
        not isinstance(current_artifacts, list)
        or current.get("module_count") != len(current_artifacts)
        or not isinstance(materialization, dict)
        or materialization.get("semantic_scope")
        != "INTERFACE_MATERIALIZATION_ONLY"
        or materialization.get("current_auto_runtime_control_bound")
        is not False
        or materialization.get("runtime_state_write_permitted")
        is not False
        or materialization.get(
            "control_sync_required_before_state_write"
        )
        is not True
        or not isinstance(publisher_materialization, dict)
        or publisher_materialization.get("semantic_scope")
        != "INTERFACE_MATERIALIZATION_ONLY"
        or publisher_materialization.get(
            "predecessor_control_git_object_id"
        )
        != PUBLISHER_MATERIALIZATION_CONTROL_GIT_OBJECT
        or publisher_materialization.get(
            "current_auto_runtime_control_bound"
        )
        is not False
        or publisher_materialization.get(
            "runtime_state_write_permitted"
        )
        is not False
        or publisher_materialization.get("repository_bound")
        is not False
        or publisher_materialization.get(
            "canonical_publication_permitted"
        )
        is not False
        or not isinstance(repository_materialization, dict)
        or repository_materialization.get("as_of_phase")
        != "AUTO_AU040_REPOSITORY_BINDING"
        or repository_materialization.get("semantic_scope")
        != "INTERFACE_MATERIALIZATION_ONLY"
        or repository_materialization.get(
            "predecessor_control_git_object_id"
        )
        != CONTROL_GIT_OBJECT
        or repository_materialization.get(
            "current_auto_runtime_control_bound"
        )
        is not False
        or repository_materialization.get(
            "repository_binding_integration_complete"
        )
        is not True
        or repository_materialization.get("repository_bound")
        is not False
        or repository_materialization.get(
            "bound_reference_resolver_gate_satisfied"
        )
        is not False
        or repository_materialization.get(
            "runtime_state_write_permitted"
        )
        is not False
        or repository_materialization.get(
            "canonical_publication_permitted"
        )
        is not False
        or not isinstance(historical_control, dict)
        or historical_control.get("verified_git_object_id")
        != CONTROL_GIT_OBJECT
        or historical_control.get("interface_raw_sha256")
        != CONTROL_RAW_SHA256
        or current.get("runtime_state_write_permitted") is not False
        or current.get("control_sync_required_before_state_write")
        is not True
        or current.get("runtime_shard_writer_integration_complete")
        is not True
        or current.get("publisher_v2_runtime_integration_complete")
        is not True
        or current.get("repository_binding_integration_complete")
        is not True
        or current.get("repository_bound") is not False
        or current.get("bound_reference_resolver_gate_satisfied")
        is not False
        or current.get("next_phase")
        != "MECHANISM_POST_AU040_REPOSITORY_BINDING_CONTROL_SYNC"
    ):
        raise AutoRuntimeError(
            "WRITER_SHADOW_CURRENT_INTERFACE_CONTRACT_MISMATCH"
        )
    for artifact in current_artifacts:
        relative_path = artifact["relative_path"]
        try:
            raw = root.joinpath(*relative_path.split("/")).read_bytes()
        except OSError as exc:
            raise AutoRuntimeError(
                "WRITER_SHADOW_CURRENT_MODULE_READ_FAILED"
            ) from exc
        if hashlib.sha256(raw).hexdigest() != artifact[
            "artifact_digest"
        ]:
            raise AutoRuntimeError(
                "WRITER_SHADOW_CURRENT_MODULE_DIGEST_MISMATCH"
            )
    return UnboundWriterCandidateEvidence(
        "UNBOUND_REPOSITORY_CONTROL_SYNC_PENDING",
        31,
        5,
        CONTROL_GIT_OBJECT,
        BOUND_AUTO_GIT_OBJECT,
        BOUND_AUTO_MODULE_COUNT,
        len(current_artifacts),
        hashlib.sha256(current_raw).hexdigest(),
        False,
        False,
        True,
        True,
        True,
        False,
        False,
    )


def validate_unbound_publisher_candidate(
    repo_root: Path,
    candidate_trust: TrustTuple,
    control_trust: ControlTrustTuple,
) -> UnboundWriterCandidateEvidence:
    """Explicit publisher-v2 name for the current unbound proof."""

    return validate_unbound_writer_candidate(
        repo_root,
        candidate_trust,
        control_trust,
    )


def validate_unbound_repository_binding_candidate(
    repo_root: Path,
    candidate_trust: TrustTuple,
    control_trust: ControlTrustTuple,
) -> UnboundWriterCandidateEvidence:
    """Explicit name for the current repository-binding shadow proof."""

    return validate_unbound_writer_candidate(
        repo_root,
        candidate_trust,
        control_trust,
    )
