"""Read-only capability and external-trust bootstrap for every run."""

from __future__ import annotations

import hashlib
import importlib.metadata
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Any, Mapping

from CodexSkills.registry.auto.tools.validate_auto import (
    AutoContract,
    ContractError,
    TrustTuple,
    capability_gate,
    load_trusted_auto_contract,
)
from CodexSkills.governance.tools.canonical_json import (
    canonicalize_object,
    parse_json_bytes,
    verify_vendor,
)
from .core import AutoRuntimeError, CANDIDATE_MANIFEST_PATH


SUPPORTED_DEPENDENCIES = {
    "jsonschema": ("4.25.1", "5"),
    "referencing": ("0.36.2", "1"),
    "PyYAML": ("6.0.3", "7"),
}
TRUSTED_MECHANISM_RUNTIME_PATHS = (
    "CodexSkills/governance/activation/control-interface.json",
    "CodexSkills/governance/tools/build_activation_control.py",
    "CodexSkills/governance/tools/canonical_json.py",
    "CodexSkills/governance/tools/validate_activation.py",
    "CodexSkills/governance/tools/validate_mechanism.py",
    "CodexSkills/governance/vendor/json_canonicalization/PROVENANCE.json",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/Canonicalize.py",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/NumberToJson.py",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/LICENSE",
    "CodexSkills/governance/vendor/json_canonicalization/python3/src/org/webpki/json/LICENSE.PSF",
)
CONTROL_INTERFACE_PATH = (
    "CodexSkills/governance/activation/control-interface.json"
)
CONTROL_MODE = "DRAFT_NON_ACTIVE_CONTROL"
GIT_OBJECT_RE = re.compile(
    r"^(?:(sha1):([0-9a-f]{40})|(sha256):([0-9a-f]{64}))$"
)
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class ControlTrustTuple:
    verified_git_object_id: str
    expected_control_interface_raw_sha256: str
    canonical_control_interface_path: str
    mode: str


@dataclass(frozen=True)
class BootstrapContext:
    trust: TrustTuple
    control_trust: ControlTrustTuple
    contract: AutoContract
    capabilities: Mapping[str, str]
    control_interface: Mapping[str, Any]


def _release(value: str) -> tuple:
    pieces = []
    for piece in value.split("."):
        digits = "".join(char for char in piece if char.isdigit())
        if not digits:
            break
        pieces.append(int(digits))
    if not pieces:
        raise AutoRuntimeError("CAPABILITY_VERSION_UNPARSEABLE")
    return tuple(pieces)


def _run_git(repo_root: Path, *args: str, check: bool = True) -> subprocess.CompletedProcess:
    try:
        result = subprocess.run(
            ["git", "-C", str(repo_root), *args],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AutoRuntimeError("BOOTSTRAP_GIT_UNAVAILABLE") from exc
    if check and result.returncode != 0:
        raise AutoRuntimeError("BOOTSTRAP_GIT_COMMAND_FAILED")
    return result


def _git_path_exists(repo_root: Path, object_id: str, relative_path: str) -> bool:
    result = _run_git(repo_root, "cat-file", "-e", f"{object_id}:{relative_path}", check=False)
    return result.returncode == 0


def _git_blob(repo_root: Path, object_id: str, relative_path: str) -> bytes:
    result = _run_git(repo_root, "show", f"{object_id}:{relative_path}")
    return result.stdout


def _split_git_object(repo_root: Path, tagged: str, code: str) -> str:
    match = GIT_OBJECT_RE.fullmatch(tagged)
    if not match:
        raise AutoRuntimeError(f"{code}_GIT_OBJECT_ID_INVALID")
    algorithm = match.group(1) or match.group(3)
    object_id = match.group(2) or match.group(4)
    observed = _run_git(
        repo_root, "rev-parse", "--show-object-format"
    ).stdout.decode("ascii", errors="strict").strip()
    if observed != algorithm:
        raise AutoRuntimeError(f"{code}_GIT_ALGORITHM_MISMATCH")
    _run_git(repo_root, "cat-file", "-e", f"{object_id}^{{commit}}")
    return object_id


def _verify_local_mechanism_runtime(
    repo_root: Path,
    control_object_id: str,
) -> None:
    for relative_path in TRUSTED_MECHANISM_RUNTIME_PATHS:
        try:
            local = repo_root.joinpath(*relative_path.split("/")).read_bytes()
        except OSError as exc:
            raise AutoRuntimeError("BOOTSTRAP_TRUSTED_RUNTIME_READ_FAILED") from exc
        if local != _git_blob(repo_root, control_object_id, relative_path):
            raise AutoRuntimeError("BOOTSTRAP_TRUSTED_RUNTIME_LOCAL_DRIFT")


def _verify_control_trust(
    repo_root: Path,
    candidate_trust: TrustTuple,
    control_trust: ControlTrustTuple,
) -> Mapping[str, Any]:
    if (
        control_trust.canonical_control_interface_path
        != CONTROL_INTERFACE_PATH
        or control_trust.mode != CONTROL_MODE
        or not SHA256_RE.fullmatch(
            control_trust.expected_control_interface_raw_sha256
        )
    ):
        raise AutoRuntimeError("BOOTSTRAP_CONTROL_TRUST_TUPLE_INVALID")
    control_object_id = _split_git_object(
        repo_root,
        control_trust.verified_git_object_id,
        "BOOTSTRAP_CONTROL",
    )
    raw = _git_blob(
        repo_root,
        control_object_id,
        control_trust.canonical_control_interface_path,
    )
    if (
        hashlib.sha256(raw).hexdigest()
        != control_trust.expected_control_interface_raw_sha256
    ):
        raise AutoRuntimeError(
            "BOOTSTRAP_CONTROL_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    try:
        local = repo_root.joinpath(
            *control_trust.canonical_control_interface_path.split("/")
        ).read_bytes()
    except OSError as exc:
        raise AutoRuntimeError(
            "BOOTSTRAP_CONTROL_INTERFACE_READ_FAILED"
        ) from exc
    if local != raw:
        raise AutoRuntimeError("BOOTSTRAP_CONTROL_INTERFACE_LOCAL_DRIFT")
    try:
        interface = parse_json_bytes(raw)
    except Exception as exc:
        raise AutoRuntimeError(
            "BOOTSTRAP_CONTROL_INTERFACE_JSON_INVALID"
        ) from exc
    if not isinstance(interface, dict):
        raise AutoRuntimeError(
            "BOOTSTRAP_CONTROL_INTERFACE_ROOT_INVALID"
        )
    expected_candidate = {
        "bundle_digest": candidate_trust.expected_bundle_digest,
        "candidate_bundle_git_object_id": (
            candidate_trust.verified_git_object_id
        ),
        "candidate_manifest_path": (
            candidate_trust.canonical_manifest_path
        ),
        "candidate_trust_mode": candidate_trust.mode,
    }
    if any(
        interface.get(key) != value
        for key, value in expected_candidate.items()
    ):
        raise AutoRuntimeError(
            "BOOTSTRAP_CONTROL_CANDIDATE_TRUST_MISMATCH"
        )
    consumer = interface.get("consumer_contract")
    transition = interface.get("transition_contract")
    control_contract = interface.get("control_trust_contract")
    transport = interface.get("transport_runtime_interface")
    if (
        interface.get("status") != "DRAFT_NON_ACTIVE"
        or interface.get("activation_forbidden") is not True
        or interface.get("protocol_revision")
        != "urn:linzecolin:agentdatabase:skillops:protocol:cross-pack:v1"
        or interface.get("candidate_schema_count") != 31
        or interface.get("candidate_policy_count") != 5
        or not isinstance(consumer, dict)
        or consumer.get("contract_revision") != "V2"
        or consumer.get("relative_path")
        != "OpenAIDatabase/config/evaluation/skill_run_consumer.json"
        or not isinstance(consumer.get("artifact_digest"), str)
        or not SHA256_RE.fullmatch(consumer["artifact_digest"])
        or not isinstance(consumer.get("verified_git_object_id"), str)
        or consumer.get("canonical_publication_permitted") is not False
        or consumer.get("repository_shards_permitted") is not False
        or not isinstance(transition, dict)
        or not isinstance(
            transition.get("auto_runtime_integration_complete"), bool
        )
        or not isinstance(transition.get("au_040_complete"), bool)
        or not isinstance(
            transition.get("canonical_publication_permitted"), bool
        )
        or not isinstance(transition.get("external_gmail_ready"), bool)
        or not isinstance(transition.get("m0c_b_permitted"), bool)
        or not isinstance(transition.get("repository_bound"), bool)
        or not isinstance(
            transition.get("schedule_authority_resolved"), bool
        )
        or not isinstance(transition.get("schedule_complete"), bool)
        or not isinstance(control_contract, dict)
        or control_contract.get("canonical_path")
        != CONTROL_INTERFACE_PATH
        or control_contract.get("expected_mode") != CONTROL_MODE
        or control_contract.get(
            "external_expected_raw_sha256_required"
        )
        is not True
        or control_contract.get("external_verified_git_object_required")
        is not True
        or control_contract.get(
            "repository_self_report_is_not_trust_root"
        )
        is not True
        or not isinstance(transport, dict)
        or transport.get("relative_path")
        != "CodexSkills/registry/auto/runtime-interface.json"
        or not isinstance(transport.get("artifact_digest"), str)
        or not SHA256_RE.fullmatch(transport["artifact_digest"])
        or not isinstance(transport.get("verified_git_object_id"), str)
    ):
        raise AutoRuntimeError("BOOTSTRAP_CONTROL_CONTRACT_MISMATCH")
    consumer_object_id = _split_git_object(
        repo_root,
        consumer["verified_git_object_id"],
        "BOOTSTRAP_CONSUMER",
    )
    consumer_raw = _git_blob(
        repo_root,
        consumer_object_id,
        consumer["relative_path"],
    )
    if (
        hashlib.sha256(consumer_raw).hexdigest()
        != consumer["artifact_digest"]
    ):
        raise AutoRuntimeError(
            "BOOTSTRAP_CONSUMER_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    try:
        local_consumer = repo_root.joinpath(
            *consumer["relative_path"].split("/")
        ).read_bytes()
    except OSError as exc:
        raise AutoRuntimeError(
            "BOOTSTRAP_CONSUMER_INTERFACE_READ_FAILED"
        ) from exc
    if local_consumer != consumer_raw:
        raise AutoRuntimeError(
            "BOOTSTRAP_CONSUMER_INTERFACE_LOCAL_DRIFT"
        )
    source_object_id = _split_git_object(
        repo_root,
        transport["verified_git_object_id"],
        "BOOTSTRAP_AUTO_RUNTIME",
    )
    source_raw = _git_blob(
        repo_root,
        source_object_id,
        transport["relative_path"],
    )
    if (
        hashlib.sha256(source_raw).hexdigest()
        != transport["artifact_digest"]
    ):
        raise AutoRuntimeError(
            "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_RAW_DIGEST_MISMATCH"
        )
    if transition["auto_runtime_integration_complete"]:
        try:
            local_source = repo_root.joinpath(
                *transport["relative_path"].split("/")
            ).read_bytes()
        except OSError as exc:
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_READ_FAILED"
            ) from exc
        if local_source != source_raw:
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_LOCAL_DRIFT"
            )
        try:
            source_interface = parse_json_bytes(source_raw)
        except Exception as exc:
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_JSON_INVALID"
            ) from exc
        if (
            not isinstance(source_interface, dict)
            or source_interface.get(
                "auto_exact_bundle_integration_complete"
            )
            is not True
            or source_interface.get("candidate_git_object_id")
            != candidate_trust.verified_git_object_id
            or source_interface.get("candidate_bundle_digest")
            != candidate_trust.expected_bundle_digest
            or source_interface.get("shared_bundle_schema_count") != 31
            or source_interface.get("shared_policy_count") != 5
            or source_interface.get("next_phase")
            != "MECHANISM_POST_AUTO_INTEGRATION_CONTROL_SYNC"
        ):
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_INTERFACE_CONTRACT_MISMATCH"
            )
        artifacts = source_interface.get("module_artifacts")
        if (
            not isinstance(artifacts, list)
            or source_interface.get("module_count") != len(artifacts)
            or not artifacts
        ):
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_MODULE_SET_INVALID"
            )
        observed_paths = []
        for entry in artifacts:
            if (
                not isinstance(entry, dict)
                or not isinstance(entry.get("relative_path"), str)
                or not entry["relative_path"].startswith(
                    "CodexSkills/registry/auto/"
                )
                or not isinstance(entry.get("artifact_digest"), str)
                or not SHA256_RE.fullmatch(entry["artifact_digest"])
            ):
                raise AutoRuntimeError(
                    "BOOTSTRAP_AUTO_RUNTIME_MODULE_ENTRY_INVALID"
                )
            observed_paths.append(entry["relative_path"])
            try:
                module_raw = repo_root.joinpath(
                    *entry["relative_path"].split("/")
                ).read_bytes()
            except OSError as exc:
                raise AutoRuntimeError(
                    "BOOTSTRAP_AUTO_RUNTIME_MODULE_READ_FAILED"
                ) from exc
            if (
                hashlib.sha256(module_raw).hexdigest()
                != entry["artifact_digest"]
            ):
                raise AutoRuntimeError(
                    "BOOTSTRAP_AUTO_RUNTIME_MODULE_LOCAL_DRIFT"
                )
        if (
            observed_paths != sorted(observed_paths)
            or len(observed_paths) != len(set(observed_paths))
        ):
            raise AutoRuntimeError(
                "BOOTSTRAP_AUTO_RUNTIME_MODULE_SET_INVALID"
            )
    _verify_local_mechanism_runtime(repo_root, control_object_id)
    return MappingProxyType(interface)


def _capability_smoke(repo_root: Path) -> Mapping[str, str]:
    try:
        base = dict(capability_gate())
        verify_vendor()
    except ContractError as exc:
        raise AutoRuntimeError(f"CAPABILITY_GATE_FAILED:{exc}") from exc
    if not ((3, 9) <= sys.version_info[:2] < (3, 14)):
        raise AutoRuntimeError("CAPABILITY_PYTHON_UNSUPPORTED")
    for package, (minimum, maximum_major) in SUPPORTED_DEPENDENCIES.items():
        try:
            observed = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError as exc:
            raise AutoRuntimeError(f"CAPABILITY_DEPENDENCY_MISSING:{package}") from exc
        if not (_release(minimum) <= _release(observed) < _release(maximum_major)):
            raise AutoRuntimeError(f"CAPABILITY_DEPENDENCY_UNSUPPORTED:{package}:{observed}")
        base[package.lower()] = observed

    smoke = parse_json_bytes(b'{"z":1,"a":"ok"}')
    if canonicalize_object(smoke) != b'{"a":"ok","z":1}':
        raise AutoRuntimeError("CAPABILITY_CANONICALIZER_SMOKE_FAILED")
    wrapper = repo_root / "CodexSkills" / "governance" / "tools" / "canonical_json.py"
    try:
        wrapper_digest = hashlib.sha256(wrapper.read_bytes()).hexdigest()
    except OSError as exc:
        raise AutoRuntimeError("CAPABILITY_CANONICALIZER_READ_FAILED") from exc
    base["canonicalizer_code_digest"] = wrapper_digest
    base["network_schema_resolution"] = "DISABLED"
    base["runtime_install"] = "FORBIDDEN"
    return base


def bootstrap_runtime(
    repo_root: Path,
    trust: TrustTuple,
    control_trust: ControlTrustTuple,
) -> BootstrapContext:
    """Validate all capabilities/trust before callers create runtime state."""

    root = repo_root.resolve()
    observed_root = _run_git(root, "rev-parse", "--show-toplevel").stdout.decode(
        "utf-8", errors="strict"
    ).strip()
    if Path(observed_root).resolve() != root:
        raise AutoRuntimeError("BOOTSTRAP_REPOSITORY_ROOT_MISMATCH")
    if trust.canonical_manifest_path != CANDIDATE_MANIFEST_PATH:
        raise AutoRuntimeError("BOOTSTRAP_MANIFEST_PATH_MISMATCH")
    object_id = _split_git_object(
        root,
        trust.verified_git_object_id,
        "BOOTSTRAP_CANDIDATE",
    )
    control_interface = _verify_control_trust(
        root,
        trust,
        control_trust,
    )
    capabilities = _capability_smoke(root)
    try:
        contract = load_trusted_auto_contract(root, trust)
    except ContractError as exc:
        raise AutoRuntimeError(f"BOOTSTRAP_TRUST_FAILED:{exc}") from exc
    if (
        len(contract.shared.schemas) != 31
        or len(contract.shared.policies) != 5
    ):
        raise AutoRuntimeError(
            "BOOTSTRAP_FINAL_BUNDLE_PROFILE_REQUIRED"
        )

    version_exists = _git_path_exists(root, object_id, "CodexSkills/VERSION")
    if trust.mode == "CANDIDATE" and version_exists:
        raise AutoRuntimeError("BOOTSTRAP_CANDIDATE_ACTIVE_VERSION_FORBIDDEN")
    if trust.mode == "ACTIVE" and not version_exists:
        raise AutoRuntimeError("BOOTSTRAP_ACTIVE_VERSION_REQUIRED")
    return BootstrapContext(
        trust,
        control_trust,
        contract,
        capabilities,
        control_interface,
    )


def require_control_synced_runtime(context: BootstrapContext) -> None:
    transition = context.control_interface.get("transition_contract")
    if (
        not isinstance(transition, dict)
        or transition.get("auto_runtime_integration_complete") is not True
    ):
        raise AutoRuntimeError(
            "RUNTIME_CONTROL_SYNC_REQUIRED_BEFORE_STATE_WRITE"
        )
